"""
Configuration management for STL to GCode Converter.
"""

import json
import os
from pathlib import Path

# Default configuration values
DEFAULT_CONFIG = {
    'last_open_dir': '',
    'recent_files': [],
    'max_recent_files': 5,
    'gcode_settings': {
        'feed_rate': 1000,
        'travel_speed': 2000,
        'z_hop': 1.0,
        'layer_height': 0.2,
        'infill_density': 20
    }
}

class Config:
    def __init__(self):
        self.config_file = Path.home() / '.stl_to_gcode' / 'config.json'
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file or create default if not exists."""
        try:
            if not self.config_file.parent.exists():
                self.config_file.parent.mkdir(parents=True)
            
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG

    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Get configuration value with optional default."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value."""
        self.config[key] = value
        self.save()

    def add_recent_file(self, file_path):
        """Add file to recent files list."""
        if file_path not in self.config['recent_files']:
            self.config['recent_files'].insert(0, file_path)
            if len(self.config['recent_files']) > self.config['max_recent_files']:
                self.config['recent_files'].pop()
            self.save()

# Singleton instance
config = Config()
