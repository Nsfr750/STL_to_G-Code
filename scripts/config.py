"""
Configuration management for STL to GCode Converter.
"""

import json
import os
from pathlib import 
from scripts.logger import get_loggerPath

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
        # Store config in user's home directory under .stl_to_gcode
        self.config_dir = Path.home() / '.stl_to_gcode'
        self.config_file = self.config_dir / 'config.json'
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file or create default if not exists."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_dicts(DEFAULT_CONFIG, config)
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
                return DEFAULT_CONFIG.copy()
                
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    
    def _merge_dicts(self, default, custom):
        """Recursively merge two dictionaries."""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a configuration value by dot notation key."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Set a configuration value by dot notation key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        self.save()

# Singleton instance
config = Config()

# For testing
if __name__ == "__main__":
    # Test config
    print("Current config:", config.config)
    
    # Test getting/setting values
    print("Layer height:", config.get('gcode_settings.layer_height'))
    config.set('gcode_settings.layer_height', 0.25)
    print("New layer height:", config.get('gcode_settings.layer_height'))
    
    # Save changes
    config.save()
