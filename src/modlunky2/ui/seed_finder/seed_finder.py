import logging

logger = logging.getLogger("modlunky2")
from .prng import Seed
from .generate_level import generate_level
from .themes import THEME


class SeedFinderConfig:
    def __init__(
        self,
    ):
        self.test = 1


class SeedFinderState:
    def set_seed(self, seed):
        self.seed = seed
        self.ushabti = -1
        # self.dark_level_spawned = False
        # self.vault_spawned = False
        self.quest_flags = 0x00000040
        self.level_flags = 0x00000000
        self.presence_flags = 0x00000000

        self.locust_levels = 0
        self.dark_levels = 0
        self.echo_levels = 0
        self.echo_level_themes = []

    def __init__(
        self,
        seed,
    ):
        self.set_seed(seed)


class LevelChances:
    def reset(self):
        self.altar_chance = 0
        self.max_liquid_particles = 2000
        self.flagged_liquid_rooms = 0

    def __init__(self):
        self.reset()


class RoomMeta:
    def reset(self):
        self.flipped = False
        self.meta_27 = 0
        self.setroom_f = False
        self.setroom_b = False
        self.has_backlayer = False
        self.machineroom_origin = False
        self.flagged_liquid = False
        self.meta_33 = 0
        self.meta_34 = 0

    def __init__(self):
        self.reset()


class LevelState:
    def update(
        self,
        prng,
        run_state,
        world,
        level,
        theme,
    ):
        self.prng = prng
        self.run_state = run_state
        self.world = world
        self.level = level
        self.theme = theme
        # These ones are the wrong way, oops 0x138-0x139-0x13a
        self.level_gen_flags = 0xFFFFFF
        self.unknown46 = 1
        self.level_chances.reset()

        self.is_dark_level = False
        self.is_echo_level = False
        self.level_width = 4
        self.level_height = 4
        self.spawn_room_x = -1
        self.spawn_room_y = -1
        self.shop_type = -1
        self.backlayer_shop_type = 9
        self.locust_plague = False
        for x in range(8):
            for y in range(15):
                self.rooms_f[y][x] = 0
                self.rooms_b[y][x] = 9
                self.rooms_meta[y][x].reset()

    def __init__(
        self,
        prng,
        run_state,
        world,
        level,
        theme,
    ):
        self.level_chances = LevelChances()
        self.rooms_f = [[0 for _ in range(8)] for _ in range(15)]
        self.rooms_b = [[9 for _ in range(8)] for _ in range(15)]
        self.rooms_meta = [[RoomMeta() for _ in range(8)] for _ in range(15)]
        self.update(prng, run_state, world, level, theme)


def levels_in_world(world):
    if world == 1 or world == 2 or world == 4 or world == 6 or world == 7:
        return 4
    if world == 8:
        return 94
    return 1


def level_number(world, level):
    level_num = level
    for w in range(1, world):
        level_num += levels_in_world(w)
    return level_num


def theme_for_world(world):
    if world == 1:
        return THEME.DWELLING
    if world == 2:
        return THEME.VOLCANA
    if world == 3:
        return THEME.OLMEC
    if world == 4:
        return THEME.TEMPLE
    if world == 5:
        return THEME.ICE_CAVES
    if world == 6:
        return THEME.NEO_BABYLON
    if world == 7:
        return THEME.SUNKEN_CITY
    if world == 8:
        return THEME.COSMIC_OCEAN


def apply_level_findings(level_state):
    run_state = level_state.run_state
    if level_state.locust_plague:
        run_state.locust_levels += 1


class SeedFinder:
    def __init__(
        self,
        seed,
    ):
        self.seed = seed
        self.state = SeedFinderState(self.seed)

    def set_seed(self, seed):
        self.state.set_seed(seed)
        self.seed = seed

    def check_level(self, check_level_index):
        prngseed = Seed(self.seed)
        level_state = None
        level_count = 0
        for world in range(1, 7 + 1):
            for level in range(1, levels_in_world(world) + 1):
                print("level: ", level)
                level_count += 1
                prngseed.next_level_prng()

                # for theme in themes_in_world(world):
                if not level_state:
                    level_state = LevelState(
                        prngseed.current_level_prng(),
                        self.state,
                        world,
                        level,
                        theme_for_world(world),
                    )
                else:
                    level_state.update(
                        prngseed.current_level_prng(),
                        self.state,
                        world,
                        level,
                        theme_for_world(world),
                    )

                generate_level(level_state)
                apply_level_findings(level_state)
                if level_count == check_level_index:
                    return level_state

    def generate(self):
        # self.state = SeedFinderState(self.seed)
        prngseed = Seed(self.seed)
        level_state = None
        for world in range(1, 7 + 1):
            for level in range(1, levels_in_world(world) + 1):
                prngseed.next_level_prng()
                if world != 4:
                    continue

                # for theme in themes_in_world(world):
                if not level_state:
                    level_state = LevelState(
                        prngseed.current_level_prng(),
                        self.state,
                        world,
                        level,
                        theme_for_world(world),
                    )
                else:
                    level_state.update(
                        prngseed.current_level_prng(),
                        self.state,
                        world,
                        level,
                        theme_for_world(world),
                    )

                generate_level(level_state)
                apply_level_findings(level_state)

        # print(self.state.locust_levels)
        return self.state
