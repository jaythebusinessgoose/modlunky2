import logging
from tkinter import ttk
import asyncio

from modlunky2.config import Config
from modlunky2.ui.trackers.category import CategoryButtons
from modlunky2.ui.widgets import Tab
from .seed_finder import SeedFinder

# from .options import OptionsFrame
# from .pacifist import PacifistButtons

logger = logging.getLogger("modlunky2")


class SeedFinderFrame(ttk.LabelFrame):
    def __init__(self, parent, ml_config: Config, *args, **kwargs):
        super().__init__(parent, text="Trackers", *args, **kwargs)
        self.ml_config = ml_config
        self.button_index = 0

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        seedbox_frame = ttk.Frame(self)
        seed_frame = ttk.Frame(seedbox_frame)
        seed_label = ttk.Label(seed_frame, text="Start Seed: ")
        seed_entry = ttk.Entry(seed_frame)
        seed_frame2 = ttk.Frame(seedbox_frame)
        seed_label2 = ttk.Label(seed_frame2, text="End Seed: ")
        seed_entry2 = ttk.Entry(seed_frame2)
        seed_decimal = ttk.Label(seedbox_frame, text="")
        seed_button = None

        calculating = False
        canceled = False

        def update_decimal():
            nonlocal calculating
            nonlocal canceled
            if calculating:
                canceled = True
                return
            canceled = False
            calculating = True
            start_seed = int(seed_entry.get(), 16)
            end_seed = int(seed_entry2.get(), 16)
            seed_finder = SeedFinder(start_seed)
            # loop = asyncio.get_event_loop()

            # async def find_seed():
            # seed_decimal["text"] = str(seed)

            def check_seed(seed):
                nonlocal calculating
                nonlocal canceled
                seed_finder.set_seed(seed)
                seed_decimal["text"] = hex(seed)
                seed_button["text"] = "Cancel"
                seed_info = seed_finder.generate()
                if seed_info.locust_levels > 1:
                    print(hex(seed), seed_info.locust_levels)
                if seed == end_seed or canceled:
                    calculating = False
                    canceled = False
                    seed_button["text"] = "Compute"
                else:
                    if seed & 0xF == 0:
                        seed_frame.after(1, lambda: check_seed(seed + 1))
                    else:
                        check_seed(seed + 1)

            check_seed(start_seed)
            # for seed in range(start_seed, end_seed + 1):
            #     seed_frame.after(1, check_seed(seed))
            # async def find_seed_async():
            #     return await find_seed()

            # task = asyncio.create_task(find_seed_async())
            # asyncio.run(find_seed_async())

            # loop = asyncio.get_event_loop()
            # asyncio.ensure_future(find_seed_async())

            # loop.run(find_seed_async())

        seed_button = ttk.Button(seedbox_frame, text="Compute", command=update_decimal)

        seedbox_frame.grid(row=0, column=0)
        seed_frame.grid(row=0, column=0)
        seed_frame2.grid(row=1, column=0)
        seed_label.grid(row=0, column=0)
        seed_entry.grid(row=0, column=1)
        seed_label2.grid(row=0, column=0)
        seed_entry2.grid(row=0, column=1)
        seed_button.grid(row=2, column=0)
        seed_decimal.grid(row=3, column=0)

        seedbox_frame2 = ttk.Frame(self)
        seed_frame3 = ttk.Frame(seedbox_frame2)
        seed_label3 = ttk.Label(seed_frame3, text="Seed: ")
        seed_entry3 = ttk.Entry(seed_frame3)
        level_frame = ttk.Frame(seedbox_frame2)
        level_label = ttk.Label(level_frame, text="Level: ")
        level_entry = ttk.Entry(level_frame)
        output = ttk.Label(seedbox_frame2, text="")
        start_button = None

        def examine_seed():
            seed_finder = SeedFinder(int(seed_entry3.get(), 16))
            level_state = seed_finder.check_level(int(level_entry.get()))

            levels = []
            for row in level_state.rooms_f:
                levels.append(", ".join(str(x) for x in row))
            levels.append("")
            for row in level_state.rooms_b:
                levels.append(", ".join(str(x) for x in row))
            output["text"] = "\n".join(levels)

        start_button = ttk.Button(
            seedbox_frame2, text="Examine Seed", command=examine_seed
        )

        seedbox_frame2.grid(row=0, column=1)
        seed_frame3.grid(row=0, column=0)
        level_frame.grid(row=1, column=0)
        seed_label3.grid(row=0, column=0)
        seed_entry3.grid(row=0, column=1)
        level_label.grid(row=0, column=0)
        level_entry.grid(row=0, column=1)
        start_button.grid(row=2, column=0)
        output.grid(row=3, column=0)

        self.button_index += 1

        self.rowconfigure(self.button_index, weight=1)

    # def add_button(self, button):
    #     if self.button_index > 0:
    #         ttk.Separator(self).grid(column=0, row=self.button_index, sticky="nsew")
    #         self.button_index += 1
    #     button.grid(column=0, row=self.button_index, sticky="nsew")
    #     self.button_index += 1


class SeedFinderTab(Tab):
    def __init__(self, tab_control, ml_config: Config, *args, **kwargs):
        super().__init__(tab_control, *args, **kwargs)
        self.ml_config = ml_config

        self.rowconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.trackers_frame = SeedFinderFrame(self, ml_config)
        self.trackers_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # self.columnconfigure(1, minsize=300)
        # self.options_frame = OptionsFrame(self, ml_config)
        # self.options_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    # def on_load(self):
    #     self.options_frame.render()
