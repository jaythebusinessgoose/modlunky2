use std::io::{Cursor, Write};
use std::{
    collections::HashMap,
    fs::{create_dir_all, File},
    io::{Read, Seek, SeekFrom},
    path::Path,
};

use byteorder::{ReadBytesExt, LE};

use image::{ImageOutputFormat, Rgba, RgbaImage};
use ml2_chacha::{NasamGenerator, Spel2ChaCha, Spel2ChaChaVersion2};
use zstd::decode_all;

use crate::files::get_filepath_registry;

const BUNDLE_OFFSET: u64 = 0x400;

#[derive(Debug)]
pub struct AssetMeta {
    /// Position in the .exe where asset meta is located.
    pub offset: u64,

    /// Length of the filepath
    pub filepath_len: u32,

    /// The hash of the filepath
    pub filepath_hash: Vec<u8>,

    /// Whether the asset is encrypted and compressed
    pub is_encrypted: bool,

    /// Position into the .exe where the data itself is located
    pub asset_offset: u64,

    /// The size of the asset itself.
    pub asset_len: u32,
}

impl AssetMeta {
    pub fn total_size(&self) -> u64 {
        8 // 8 bytes for header (asset_len, filepath_len)
        + self.filepath_len as u64  // The size of the filepath
        + 1  // The byte for whether the asset is encrypted
        + self.asset_len as u64 // The size of the asset
    }

    fn from_handle<T: Seek + Read>(handle: &mut T) -> Option<Self> {
        let offset = handle.stream_position().unwrap();

        let data_len = handle.read_u32::<LE>().unwrap();
        let filepath_len = handle.read_u32::<LE>().unwrap();

        if (data_len, filepath_len) == (0, 0) {
            return None;
        }

        let asset_len = data_len - 1;
        let mut filepath_hash = vec![0; filepath_len as usize];
        handle.read_exact(&mut filepath_hash).unwrap();

        let is_encrypted = handle.read_u8().unwrap() == 1;
        let asset_offset = handle.stream_position().unwrap();

        handle
            .seek(std::io::SeekFrom::Current(asset_len as i64))
            .unwrap();

        Some(Self {
            offset,
            filepath_len,
            filepath_hash,
            is_encrypted,
            asset_offset,
            asset_len,
        })
    }
}

#[derive(Debug)]
pub struct Asset {
    pub meta: AssetMeta,
    pub filepath: Option<Vec<u8>>,
    pub data: Option<Vec<u8>>,
}

fn get_idx_from_mask(idx: Option<u32>) -> usize {
    match idx {
        Some(0xFF) => 0,
        Some(0xFF00) => 1,
        Some(0xFF0000) => 2,
        Some(0xFF000000) => 3,
        _ => 0,
    }
}

impl Asset {
    fn extract<T: Spel2ChaCha>(&self, extract_dir: &Path, chacha: &T) {
        let filepath = match &self.filepath {
            Some(filepath) => filepath,
            None => return,
        };

        let mut data = match &self.data {
            Some(data) => data.to_vec(),
            None => return,
        };

        let filepath_str: String = String::from_utf8_lossy(filepath).into();
        let mut fullpath = extract_dir.join(filepath_str);

        if let Some(parent) = fullpath.parent() {
            create_dir_all(parent).unwrap();
        }

        if self.meta.is_encrypted {
            data = chacha.decrypt(filepath, &data);
            data = decode_all(&data[..]).unwrap();
        }

        if let Some(ext) = fullpath.extension() {
            if ext == "DDS" {
                let dds = ddsfile::Dds::read(Cursor::new(&data)).unwrap();

                let width = dds.get_width();
                let height = dds.get_height();
                let max_size = width * height;
                let mut img = RgbaImage::new(width, height);

                for (idx, chunk) in dds.get_data(0).unwrap().chunks(4).enumerate() {
                    let idx = idx as u32;
                    if idx >= max_size {
                        break;
                    }
                    let x = idx % width;
                    let y = idx / width;

                    let r = chunk[get_idx_from_mask(dds.header.spf.r_bit_mask)];
                    let g = chunk[get_idx_from_mask(dds.header.spf.g_bit_mask)];
                    let b = chunk[get_idx_from_mask(dds.header.spf.b_bit_mask)];
                    let a = chunk[get_idx_from_mask(dds.header.spf.a_bit_mask)];

                    img.put_pixel(x, y, Rgba([r, g, b, a]));
                }

                fullpath.set_extension("png");
                data = Vec::new();
                img.write_to(&mut Cursor::new(&mut data), ImageOutputFormat::Png)
                    .unwrap();
            }
        }

        let mut file = File::create(fullpath).unwrap();
        file.write_all(&data).unwrap();
    }

    fn load_data<T: Seek + Read>(&mut self, handle: &mut T) {
        handle
            .seek(SeekFrom::Start(self.meta.asset_offset))
            .unwrap();
        let mut data = vec![0; self.meta.asset_len as usize];
        handle.read_exact(&mut data).unwrap();
        self.data = Some(data);
    }
}

#[derive(Debug)]
pub struct AssetStore<T: Seek + Read> {
    pub assets: Vec<Asset>,
    handle: T,
    chacha: Spel2ChaChaVersion2,
    registry: HashMap<Vec<u8>, &'static [u8]>,
}

impl<T: Seek + Read> AssetStore<T> {
    pub fn from_handle(mut handle: T) -> Self {
        let mut assets = Vec::new();
        let mut keygen = NasamGenerator::default();

        handle
            .seek(std::io::SeekFrom::Start(BUNDLE_OFFSET))
            .unwrap();

        while let Some(meta) = AssetMeta::from_handle(&mut handle) {
            keygen.update(meta.asset_len as u64 + 1);
            assets.push(Asset {
                meta,
                filepath: None,
                data: None,
            });
        }

        let chacha = Spel2ChaChaVersion2::new(keygen.key);
        let registry = get_filepath_registry(&chacha);

        let mut inst = Self {
            assets,
            handle,
            chacha,
            registry,
        };

        inst.populate_filepaths();
        inst
    }

    fn populate_filepaths(&mut self) {
        for asset in self.assets.iter_mut() {
            // Try full hash first
            if let Some(filepath) = self.registry.get(&asset.meta.filepath_hash) {
                asset.filepath = Some(filepath.to_vec());
                continue;
            }

            let end = &asset.meta.filepath_hash.iter().rposition(|elem| *elem != 0);
            if let Some(end) = end {
                let key = &asset.meta.filepath_hash[..*end + 1];
                if let Some(filepath) = self.registry.get(key) {
                    asset.filepath = Some(filepath.to_vec());
                }
            }
        }
    }

    pub fn extract(&mut self, extract_dir: &Path) {
        for asset in self.assets.iter_mut() {
            if asset.filepath.is_none() {
                continue;
            }
            asset.load_data(&mut self.handle);
            asset.extract(extract_dir, &self.chacha);
        }
    }
}