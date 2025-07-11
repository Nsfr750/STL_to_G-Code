"""
View settings and configuration for the STL to GCode Converter.
Handles OpenGL and other view-related settings.
"""
import os
import json
from pathlib import Path

# Default settings
DEFAULT_SETTINGS = {
    'use_opengl': True,  # Whether to use OpenGL for rendering
}

class ViewSettings:
    _instance = None
    _settings_file = Path.home() / '.stl_to_gcode' / 'view_settings.json'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ViewSettings, cls).__new__(cls)
            cls._instance._settings = DEFAULT_SETTINGS.copy()
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        """Load settings from file if it exists."""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self._settings.update(loaded_settings)
        except Exception as e:
            print(f"Warning: Could not load view settings: {e}")
    
    def _save_settings(self):
        """Save current settings to file."""
        try:
            os.makedirs(self._settings_file.parent, exist_ok=True)
            with open(self._settings_file, 'w') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save view settings: {e}")
    
    def get_setting(self, key, default=None):
        """Get a setting value by key."""
        return self._settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set a setting value and save to file."""
        if key in self._settings and self._settings[key] != value:
            self._settings[key] = value
            self._save_settings()
            return True
        return False
    
    def toggle_opengl(self):
        """Toggle OpenGL usage and return the new state."""
        new_state = not self._settings['use_opengl']
        self.set_setting('use_opengl', new_state)
        return new_state
    
    @property
    def use_opengl(self):
        """Get the current OpenGL usage setting."""
        return self._settings['use_opengl']

# Create a singleton instance
view_settings = ViewSettings()
