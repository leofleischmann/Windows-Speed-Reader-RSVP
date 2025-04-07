# -*- coding: utf-8 -*-

import json
import os

# --- Standardeinstellungen ---
DEFAULT_SETTINGS = {
    "wpm": 300,
    "pause_punctuation": 0.5, # Sekunden
    "pause_comma": 0.2,       # Sekunden
    "pause_paragraph": 0.8,   # Sekunden
    "font_family": "Arial",
    "font_size": 48,
    "font_color": "#000000",
    "highlight_color": "#FF0000",
    "background_color": "#F0F0F0",
    "hotkey": "<ctrl>+<alt>+r",
    "enable_orp": True,
    "orp_position": 0.3,      # 0.0 - 1.0
    "reader_borderless": False,
    "reader_always_on_top": True,
    "hide_main_window": True,
    "dark_mode": False,
    "chunk_size": 1,
    "show_context": False,
    "context_layout": "vertical" # NEU: 'vertical' or 'horizontal'
}
SETTINGS_FILE = "speed_reader_settings.json"

# --- Konfigurationsmanager ---
class ConfigManager:
    """Manages loading and saving application settings."""
    def __init__(self, filename=SETTINGS_FILE, defaults=DEFAULT_SETTINGS):
        self.filename = filename
        self.defaults = defaults
        self.settings = self.load_settings()

    def load_settings(self):
        """Loads settings from the JSON file or returns defaults."""
        settings = self.defaults.copy()
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    settings.update(loaded_settings)

            # Ensure correct types
            for key in ['wpm', 'font_size', 'chunk_size']:
                if key in settings: settings[key] = int(settings[key])
            for key in ['pause_punctuation', 'pause_comma', 'pause_paragraph', 'orp_position']:
                 if key in settings: settings[key] = float(settings[key])
            for key in ['enable_orp', 'reader_borderless', 'reader_always_on_top', 'hide_main_window', 'dark_mode', 'show_context']:
                 if key in settings: settings[key] = bool(settings[key])
            # Ensure context_layout is valid string
            if settings.get("context_layout") not in ["vertical", "horizontal"]:
                 settings["context_layout"] = self.defaults["context_layout"]

        except (json.JSONDecodeError, IOError, TypeError, ValueError) as e:
            print(f"Error loading settings from {self.filename}: {e}. Using default settings.")
            settings = self.defaults.copy()

        if settings.get("chunk_size", 1) < 1: settings["chunk_size"] = 1
        return settings

    def save_settings(self):
        """Saves the current settings to the JSON file."""
        try:
            if self.settings.get("chunk_size", 1) < 1: self.settings["chunk_size"] = 1
            if self.settings.get("context_layout") not in ["vertical", "horizontal"]:
                 self.settings["context_layout"] = self.defaults["context_layout"]
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e: print(f"Error saving settings to {self.filename}: {e}")
        except Exception as e: print(f"Unexpected error saving settings: {e}")

    def get(self, key): return self.settings.get(key, self.defaults.get(key))
    def set(self, key, value): self.settings[key] = value
