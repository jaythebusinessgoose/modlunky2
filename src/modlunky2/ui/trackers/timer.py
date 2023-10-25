import logging
import tkinter as tk
from tkinter import ttk
import datetime

from PIL import Image, ImageTk

from modlunky2.config import Config, TimerTrackerConfig
from modlunky2.constants import BASE_DIR
from modlunky2.mem import Spel2Process

from modlunky2.ui.trackers.common import (
    Tracker,
    TrackerWindow,
    WindowData,
)

logger = logging.getLogger(__name__)

ICON_PATH = BASE_DIR / "static/images"


class TimerModifiers(ttk.LabelFrame):
    def __init__(
        self, parent, timer_tracker_config: TimerTrackerConfig, *args, **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.timer_tracker_config = timer_tracker_config

        self.show_total = tk.BooleanVar()
        self.show_total.set(self.timer_tracker_config.show_total)
        self.show_total_checkbox = ttk.Checkbutton(
            self,
            text="Total",
            variable=self.show_total,
            onvalue=True,
            offvalue=False,
            command=self.toggle_show_total,
        )
        self.show_total_checkbox.grid(row=0, column=1, pady=5, padx=5, sticky="w")

        self.show_level = tk.BooleanVar()
        self.show_level.set(self.timer_tracker_config.show_level)
        self.show_level_checkbox = ttk.Checkbutton(
            self,
            text="Level",
            variable=self.show_level,
            onvalue=True,
            offvalue=False,
            command=self.toggle_show_level,
        )
        self.show_level_checkbox.grid(row=0, column=2, pady=5, padx=5, sticky="w")

        self.show_last_level = tk.BooleanVar()
        self.show_last_level.set(self.timer_tracker_config.show_last_level)
        self.show_last_level_checkbox = ttk.Checkbutton(
            self,
            text="Last Level",
            variable=self.show_last_level,
            onvalue=True,
            offvalue=False,
            command=self.toggle_show_last_level,
        )
        self.show_last_level_checkbox.grid(row=0, column=3, pady=5, padx=5, sticky="w")

        self.show_tutorial = tk.BooleanVar()
        self.show_tutorial.set(self.timer_tracker_config.show_tutorial)
        self.show_tutorial_checkbox = ttk.Checkbutton(
            self,
            text="Tutorial",
            variable=self.show_tutorial,
            onvalue=True,
            offvalue=False,
            command=self.toggle_show_tutorial,
        )
        self.show_tutorial_checkbox.grid(row=0, column=4, pady=5, padx=5, sticky="w")

        self.show_startup = tk.BooleanVar()
        self.show_startup.set(self.timer_tracker_config.show_startup)
        self.show_startup_checkbox = ttk.Checkbutton(
            self,
            text="Session",
            variable=self.show_startup,
            onvalue=True,
            offvalue=False,
            command=self.toggle_show_startup,
        )
        self.show_startup_checkbox.grid(row=0, column=5, pady=5, padx=5, sticky="w")

    def toggle_show_total(self):
        self.timer_tracker_config.show_total = self.show_total.get()
        self.parent.config_update_callback()

    def toggle_show_level(self):
        self.timer_tracker_config.show_level = self.show_level.get()
        self.parent.config_update_callback()

    def toggle_show_last_level(self):
        self.timer_tracker_config.show_last_level = self.show_last_level.get()
        self.parent.config_update_callback()

    def toggle_show_tutorial(self):
        self.timer_tracker_config.show_tutorial = self.show_tutorial.get()
        self.parent.config_update_callback()

    def toggle_show_startup(self):
        self.timer_tracker_config.show_startup = self.show_startup.get()
        self.parent.config_update_callback()


class TimerButtons(ttk.Frame):
    def __init__(self, parent, modlunky_config: Config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.modlunky_config = modlunky_config
        self.columnconfigure(0, weight=1, minsize=200)
        self.columnconfigure(1, weight=10000)
        self.rowconfigure(0, minsize=60)
        self.window = None

        self.timer_icon = ImageTk.PhotoImage(
            Image.open(ICON_PATH / "timer.png").resize(
                (24, 24), Image.Resampling.LANCZOS
            )
        )

        self.timer_button = ttk.Button(
            self,
            image=self.timer_icon,
            text="Timer",
            compound="left",
            command=self.launch,
            width=1,
        )
        self.timer_button.grid(row=0, column=0, pady=5, padx=5, sticky="nswe")

        self.modifiers = TimerModifiers(
            self, self.modlunky_config.trackers.timer, text="Timers shown"
        )
        self.modifiers.grid(row=0, column=1, pady=5, padx=5, sticky="nswe")

    def launch(self):
        color_key = self.modlunky_config.tracker_color_key
        self.disable_button()
        self.window = TrackerWindow(
            title="Timer Tracker",
            color_key=color_key,
            on_close=self.window_closed,
            file_name="",
            tracker=TimerTracker(),
            config=self.modlunky_config.trackers.timer,
        )

    def config_update_callback(self):
        self.modlunky_config.save()
        if self.window:
            self.window.update_config(self.modlunky_config.trackers.timer)

    def window_closed(self):
        self.window = None
        # If we're in the midst of destroy() the button might not exist
        if self.timer_button.winfo_exists():
            self.timer_button["state"] = tk.NORMAL

    def disable_button(self):
        self.timer_button["state"] = tk.DISABLED


class TimerTracker(Tracker[TimerTrackerConfig, WindowData]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_total = 0
        self.time_level = 0
        self.time_last_level = 0
        self.time_tutorial = 0
        self.time_startup = 0

    def initialize(self):
        self.time_total = 0
        self.time_level = 0
        self.time_last_level = 0
        self.time_tutorial = 0
        self.time_startup = 0

    def poll(self, proc: Spel2Process, config: TimerTrackerConfig) -> WindowData:
        game_state = proc.get_state()
        if game_state is None:
            return None

        self.time_total = game_state.time_total
        self.time_level = game_state.time_level
        self.time_last_level = game_state.time_last_level
        self.time_tutorial = game_state.time_tutorial
        self.time_startup = game_state.time_startup

        label = self.get_text(config)
        return WindowData(label)

    def format(self, frames):
        return datetime.datetime.utcfromtimestamp(frames / 60).strftime("%H:%M:%S.%f")[
            :-3
        ]

    def get_text(
        self,
        config: TimerTrackerConfig,
    ):
        out = []
        if config.show_total:
            out.append(f"Total: {self.format(self.time_total)}")
        if config.show_level:
            out.append(f"Level: {self.format(self.time_level)}")
        if config.show_last_level:
            out.append(f"Last Level: {self.format(self.time_last_level)}")
        if config.show_tutorial:
            out.append(f"Tutorial: {self.format(self.time_tutorial)}")
        if config.show_startup:
            out.append(f"Session: {self.format(self.time_startup)}")

        return "\n".join(out)