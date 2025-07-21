"""
View Settings Module

Handles view-related settings.
"""
from dataclasses import dataclass
from typing import Dict, Any
from scripts.logger import get_logger

@dataclass
class ViewSettings:
    """Class to manage view settings."""
    # Default view settings
    _settings: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default settings."""
        self._settings = {
            'show_axis': True,  # Whether to show axis in the 3D view
            'show_grid': True,  # Whether to show grid in the 3D view
            'background_color': (0.2, 0.2, 0.2, 1.0),  # Background color (R,G,B,A)
            'mesh_color': (0.8, 0.8, 1.0, 0.8),  # Mesh color (R,G,B,A)
            'edge_color': (0.3, 0.3, 0.3, 1.0),  # Edge color (R,G,B,A)
            'point_size': 2.0,  # Size of points in the point cloud
            'line_width': 1.0,  # Width of lines in the wireframe
            'antialiasing': True,  # Whether to enable antialiasing
            'lighting': True,  # Whether to enable lighting
            'light_color': (1.0, 1.0, 1.0, 1.0),  # Light color (R,G,B,A)
            'light_position': (1.0, 1.0, 1.0),  # Light position (X,Y,Z)
            'ambient_light': 0.2,  # Ambient light intensity (0.0 to 1.0)
            'diffuse_light': 0.8,  # Diffuse light intensity (0.0 to 1.0)
            'specular_light': 0.5,  # Specular light intensity (0.0 to 1.0)
            'specular_power': 20.0,  # Specular power (shininess)
            'auto_rotate': False,  # Whether to auto-rotate the view
            'rotation_speed': 1.0,  # Auto-rotation speed (degrees per frame)
            'show_normals': False,  # Whether to show surface normals
            'normal_length': 0.1,  # Length of normal vectors
            'show_wireframe': False,  # Whether to show wireframe overlay
            'show_points': False,  # Whether to show points
            'point_size': 2.0,  # Size of points in point cloud
            'point_color': (1.0, 1.0, 1.0, 1.0),  # Point color (R,G,B,A)
        }
    
    def get(self, key: str, default=None) -> Any:
        """Get a setting value by key.
        
        Args:
            key: The setting key
            default: Default value if key doesn't exist
            
        Returns:
            The setting value or default if not found
        """
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: The setting key
            value: The value to set
        """
        if key in self._settings:
            self._settings[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary.
        
        Returns:
            Dictionary containing all settings
        """
        return self._settings.copy()
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update multiple settings at once.
        
        Args:
            settings: Dictionary of settings to update
        """
        for key, value in settings.items():
            if key in self._settings:
                self._settings[key] = value

# Create a singleton instance
view_settings = ViewSettings()
