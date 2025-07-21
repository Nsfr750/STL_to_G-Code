"""
Settings dialog for STL to GCode Converter.

This module provides a settings dialog for configuring optimization parameters.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from scripts.logger import get_logger
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QDoubleSpinBox, QCheckBox, QDialogButtonBox,
                           QTabWidget, QGroupBox, QFormLayout, QPlainTextEdit, QWidget, QComboBox,
                           QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QStandardPaths
from PyQt6.QtCore import QSettings


class SettingsManager:
    """Manages loading and saving of application settings."""
    
    def __init__(self, config_dir: str = "config", filename: str = "settings.json"):
        """Initialize the settings manager.
        
        Args:
            config_dir: Directory to store the settings file
            filename: Name of the settings file
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / filename
        self.logger = get_logger(__name__)
        self.settings = {}
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create config directory: {e}")
            raise
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from the config file.
        
        Returns:
            dict: Loaded settings or empty dict if file doesn't exist or is invalid
        """
        if not self.config_file.exists():
            self.logger.info("No settings file found, using default settings")
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
                self.logger.info("Settings loaded successfully")
                return self.settings
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing settings file: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            return {}
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to the config file.
        
        Args:
            settings: Dictionary of settings to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, sort_keys=True)
            self.logger.info("Settings saved successfully")
            self.settings = settings.copy()
            return True
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key.
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
            
        Returns:
            The setting value or default if not found
        """
        return self.settings.get(key, default)


class SettingsDialog(QDialog):
    """Dialog for configuring optimization settings."""
    
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings are saved
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None, parent=None):
        """Initialize the settings dialog.
        
        Args:
            settings: Optional initial settings (dict or QSettings)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Optimization Settings")
        self.setMinimumWidth(600)
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Load settings or use provided defaults
        self.default_settings = {
            'layer_height': 0.2,
            'print_speed': 60,
            'travel_speed': 120,
            'retraction_length': 5.0,
            'enable_path_optimization': True,
            'enable_arc_detection': True,
            'arc_tolerance': 0.05,
            'min_arc_segments': 8,
            'remove_redundant_moves': True,
            'combine_coincident_moves': True,
            'optimize_travel_moves': True,
            'infill_density': 0.2,
            'infill_pattern': 'grid',
            'infill_angle': 45,
            'enable_optimized_infill': True,
            'infill_resolution': 1.0,
            'extrusion_width': 0.48,
            'filament_diameter': 1.75,
            'first_layer_height': 0.3,
            'first_layer_speed': 30,
            'z_hop': 0.4,
            'skirt_line_count': 1,
            'skirt_distance': 5.0,
            'temperature': 200,
            'bed_temperature': 60,
            'fan_speed': 100,
            'fan_layer': 2,
            'start_gcode': '',
            'end_gcode': ''
        }
        
        # Load saved settings
        saved_settings = self.settings_manager.load_settings()
        self.settings = self.default_settings.copy()
        
        # Update with saved settings if any
        if saved_settings:
            self.settings.update(saved_settings)
        
        # If QSettings or other settings were provided, update with them
        if settings is not None:
            if hasattr(settings, 'allKeys'):  # QSettings object
                # Convert QSettings to dict
                settings_dict = {}
                for key in settings.allKeys():
                    settings_dict[key] = settings.value(key)
                self.settings.update(settings_dict)
            elif isinstance(settings, dict):  # Regular dict
                self.settings.update(settings)
        
        self._create_widgets()
        self._setup_layout()
        self._load_settings()
    
    def _set_checkbox_style(self):
        """Set the style for checkboxes to use a checkmark."""
        style = """
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #999999;
            background: #ffffff;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #0078d7;
            background: #ffffff;
            border-radius: 3px;
            image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="%230078d7" d="M13.5 3.5L6 11 2.5 7.5l-1 1L6 13l8.5-8.5z"/></svg>');
        }
        QCheckBox::indicator:indeterminate {
            border: 1px solid #999999;
            background: #ffffff;
            border-radius: 3px;
            image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="3" y="7" width="10" height="2" fill="%23999999"/></svg>');
        }
        """
        
        # Apply the style to all QCheckBox widgets
        self.setStyleSheet(style)
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Set checkbox style first
        self._set_checkbox_style()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # General tab
        self.general_tab = QWidget()
        self._create_general_tab()
        
        # Path Optimization tab
        self.path_opt_tab = QWidget()
        self._create_path_optimization_tab()
        
        # Infill tab
        self.infill_tab = QWidget()
        self._create_infill_tab()
        
        # Advanced tab
        self.advanced_tab = QWidget()
        self._create_advanced_tab()
        
        # Add tabs
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.path_opt_tab, "Path Optimization")
        self.tab_widget.addTab(self.infill_tab, "Infill")
        self.tab_widget.addTab(self.advanced_tab, "Advanced")
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Reset
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset_to_defaults)
    
    def _create_general_tab(self):
        """Create the General tab."""
        layout = QVBoxLayout(self.general_tab)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        form_layout = QFormLayout()
        
        # Layer height
        self.layer_height = QDoubleSpinBox()
        self.layer_height.setRange(0.05, 0.5)
        self.layer_height.setSingleStep(0.05)
        self.layer_height.setSuffix(" mm")
        form_layout.addRow("Layer Height:", self.layer_height)
        
        # Print speed
        self.print_speed = QSpinBox()
        self.print_speed.setRange(1, 300)
        self.print_speed.setSuffix(" mm/s")
        form_layout.addRow("Print Speed:", self.print_speed)
        
        # Travel speed
        self.travel_speed = QSpinBox()
        self.travel_speed.setRange(1, 300)
        self.travel_speed.setSuffix(" mm/s")
        form_layout.addRow("Travel Speed:", self.travel_speed)
        
        # Retraction
        self.retraction_length = QDoubleSpinBox()
        self.retraction_length.setRange(0, 10)
        self.retraction_length.setSingleStep(0.5)
        self.retraction_length.setSuffix(" mm")
        form_layout.addRow("Retraction Length:", self.retraction_length)
        
        general_group.setLayout(form_layout)
        layout.addWidget(general_group)
        layout.addStretch()
    
    def _create_path_optimization_tab(self):
        """Create the Path Optimization tab."""
        layout = QVBoxLayout(self.path_opt_tab)
        
        # Path optimization group
        path_group = QGroupBox("Path Optimization")
        form_layout = QFormLayout()
        
        # Enable path optimization
        self.enable_path_optimization = QCheckBox("Enable path optimization")
        form_layout.addRow(self.enable_path_optimization)
        
        # Arc detection
        self.enable_arc_detection = QCheckBox("Enable arc detection (G2/G3)")
        form_layout.addRow(self.enable_arc_detection)
        
        # Arc tolerance
        self.arc_tolerance = QDoubleSpinBox()
        self.arc_tolerance.setRange(0.001, 1.0)
        self.arc_tolerance.setSingleStep(0.01)
        self.arc_tolerance.setSuffix(" mm")
        form_layout.addRow("Arc Detection Tolerance:", self.arc_tolerance)
        
        # Minimum arc segments
        self.min_arc_segments = QSpinBox()
        self.min_arc_segments.setRange(3, 20)
        form_layout.addRow("Minimum Arc Segments:", self.min_arc_segments)
        
        path_group.setLayout(form_layout)
        layout.addWidget(path_group)
        
        # Redundant move removal group
        move_group = QGroupBox("Move Optimization")
        move_layout = QVBoxLayout()
        
        self.remove_redundant_moves = QCheckBox("Remove redundant moves")
        self.remove_redundant_moves.setToolTip("Remove consecutive moves to the same position")
        move_layout.addWidget(self.remove_redundant_moves)
        
        self.combine_coincident_moves = QCheckBox("Combine coincident moves")
        self.combine_coincident_moves.setToolTip("Combine moves that are in the same direction")
        move_layout.addWidget(self.combine_coincident_moves)
        
        self.optimize_travel_moves = QCheckBox("Optimize travel moves")
        self.optimize_travel_moves.setToolTip("Use nearest-neighbor algorithm to optimize travel moves")
        move_layout.addWidget(self.optimize_travel_moves)
        
        move_group.setLayout(move_layout)
        layout.addWidget(move_group)
        
        layout.addStretch()
    
    def _create_infill_tab(self):
        """Create the Infill tab."""
        layout = QVBoxLayout(self.infill_tab)
        
        # Infill settings group
        infill_group = QGroupBox("Infill Settings")
        form_layout = QFormLayout()
        
        # Infill density
        self.infill_density = QSpinBox()
        self.infill_density.setRange(0, 100)
        self.infill_density.setSuffix("%")
        form_layout.addRow("Infill Density:", self.infill_density)
        
        # Infill pattern
        self.infill_pattern = QComboBox()
        self.infill_pattern.addItems(["grid", "lines", "triangles", "cubic", "gyroid"])
        form_layout.addRow("Infill Pattern:", self.infill_pattern)
        
        # Infill angle
        self.infill_angle = QSpinBox()
        self.infill_angle.setRange(0, 180)
        self.infill_angle.setSuffix("°")
        form_layout.addRow("Infill Angle:", self.infill_angle)
        
        # Optimized infill
        self.enable_optimized_infill = QCheckBox("Enable optimized infill (A* path planning)")
        form_layout.addRow(self.enable_optimized_infill)
        
        # Infill resolution
        self.infill_resolution = QDoubleSpinBox()
        self.infill_resolution.setRange(0.1, 5.0)
        self.infill_resolution.setSingleStep(0.1)
        self.infill_resolution.setSuffix(" mm")
        self.infill_resolution.setToolTip("Resolution for optimized infill path planning")
        form_layout.addRow("Infill Resolution:", self.infill_resolution)
        
        infill_group.setLayout(form_layout)
        layout.addWidget(infill_group)
        
        # Connect signals
        self.enable_optimized_infill.toggled.connect(self.infill_resolution.setEnabled)
        
        layout.addStretch()
    
    def _create_advanced_tab(self):
        """Create the Advanced tab."""
        layout = QVBoxLayout(self.advanced_tab)
        
        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        form_layout = QFormLayout()
        
        # Extrusion width
        self.extrusion_width = QDoubleSpinBox()
        self.extrusion_width.setRange(0.1, 1.0)
        self.extrusion_width.setSingleStep(0.05)
        self.extrusion_width.setSuffix(" mm")
        form_layout.addRow("Extrusion Width:", self.extrusion_width)
        
        # Filament diameter
        self.filament_diameter = QDoubleSpinBox()
        self.filament_diameter.setRange(1.0, 3.0)
        self.filament_diameter.setSingleStep(0.05)
        self.filament_diameter.setSuffix(" mm")
        form_layout.addRow("Filament Diameter:", self.filament_diameter)
        
        # First layer settings
        self.first_layer_height = QDoubleSpinBox()
        self.first_layer_height.setRange(0.1, 1.0)
        self.first_layer_height.setSingleStep(0.05)
        self.first_layer_height.setSuffix(" mm")
        form_layout.addRow("First Layer Height:", self.first_layer_height)
        
        self.first_layer_speed = QSpinBox()
        self.first_layer_speed.setRange(1, 100)
        self.first_layer_speed.setSuffix(" %")
        form_layout.addRow("First Layer Speed:", self.first_layer_speed)
        
        # Z-hop
        self.z_hop = QDoubleSpinBox()
        self.z_hop.setRange(0, 1.0)
        self.z_hop.setSingleStep(0.05)
        self.z_hop.setSuffix(" mm")
        form_layout.addRow("Z-hop Height:", self.z_hop)
        
        # Skirt/Brim
        self.skirt_line_count = QSpinBox()
        self.skirt_line_count.setRange(0, 10)
        form_layout.addRow("Skirt Line Count:", self.skirt_line_count)
        
        self.skirt_distance = QDoubleSpinBox()
        self.skirt_distance.setRange(0, 20)
        self.skirt_distance.setSingleStep(0.5)
        self.skirt_distance.setSuffix(" mm")
        form_layout.addRow("Skirt Distance:", self.skirt_distance)
        
        advanced_group.setLayout(form_layout)
        layout.addWidget(advanced_group)
        
        # Temperature settings group
        temp_group = QGroupBox("Temperature Settings")
        temp_layout = QFormLayout()
        
        # Extruder temperature
        self.temperature = QSpinBox()
        self.temperature.setRange(150, 300)
        self.temperature.setSuffix(" °C")
        temp_layout.addRow("Extruder Temperature:", self.temperature)
        
        # Bed temperature
        self.bed_temperature = QSpinBox()
        self.bed_temperature.setRange(0, 120)
        self.bed_temperature.setSuffix(" °C")
        temp_layout.addRow("Bed Temperature:", self.bed_temperature)
        
        # Fan settings
        self.fan_speed = QSpinBox()
        self.fan_speed.setRange(0, 100)
        self.fan_speed.setSuffix(" %")
        temp_layout.addRow("Fan Speed:", self.fan_speed)
        
        self.fan_layer = QSpinBox()
        self.fan_layer.setRange(0, 20)
        self.fan_layer.setToolTip("Layer to turn on the fan (0 = first layer)")
        temp_layout.addRow("Fan Start Layer:", self.fan_layer)
        
        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)
        
        # Custom G-code group
        gcode_group = QGroupBox("Custom G-code")
        gcode_layout = QVBoxLayout()
        
        # Start G-code tab widget
        gcode_tabs = QTabWidget()
        
        # Start G-code tab
        start_tab = QWidget()
        start_layout = QVBoxLayout()
        
        self.start_gcode = QPlainTextEdit()
        self.start_gcode.setPlaceholderText(
            "; Add custom start G-code here\n"
            "; Available placeholders:\n"
            "; {bed_temp} - Bed temperature\n"
            "; {extruder_temp} - Extruder temperature\n"
            "; {fan_speed} - Fan speed (0-255)\n"
            "; {material} - Filament material"
        )
        self.start_gcode.setMinimumHeight(200)
        start_layout.addWidget(QLabel("Start G-code:"))
        start_layout.addWidget(self.start_gcode)
        
        start_tab.setLayout(start_layout)
        
        # End G-code tab
        end_tab = QWidget()
        end_layout = QVBoxLayout()
        
        self.end_gcode = QPlainTextEdit()
        self.end_gcode.setPlaceholderText(
            "; Add custom end G-code here\n"
            "; Available placeholders same as start G-code"
        )
        self.end_gcode.setMinimumHeight(200)
        end_layout.addWidget(QLabel("End G-code:"))
        end_layout.addWidget(self.end_gcode)
        
        end_tab.setLayout(end_layout)
        
        # Add tabs
        gcode_tabs.addTab(start_tab, "Start G-code")
        gcode_tabs.addTab(end_tab, "End G-code")
        
        gcode_layout.addWidget(gcode_tabs)
        gcode_group.setLayout(gcode_layout)
        layout.addWidget(gcode_group)
        
        layout.addStretch()
    
    def _setup_layout(self):
        """Set up the dialog layout."""
        layout = QVBoxLayout(self)
        layout.addWidget(self.tab_widget)
        layout.addWidget(self.button_box)
    
    def _load_settings(self):
        """Load settings into the UI."""
        # General settings
        self.layer_height.setValue(self.settings.get('layer_height', 0.2))
        self.print_speed.setValue(self.settings.get('print_speed', 60))
        self.travel_speed.setValue(self.settings.get('travel_speed', 120))
        self.retraction_length.setValue(self.settings.get('retraction_length', 5.0))
        
        # Path optimization
        self.enable_path_optimization.setChecked(self.settings.get('enable_path_optimization', True))
        self.enable_arc_detection.setChecked(self.settings.get('enable_arc_detection', True))
        self.arc_tolerance.setValue(self.settings.get('arc_tolerance', 0.05))
        self.min_arc_segments.setValue(self.settings.get('min_arc_segments', 8))
        self.remove_redundant_moves.setChecked(self.settings.get('remove_redundant_moves', True))
        self.combine_coincident_moves.setChecked(self.settings.get('combine_coincident_moves', True))
        self.optimize_travel_moves.setChecked(self.settings.get('optimize_travel_moves', True))
        
        # Infill settings
        self.infill_density.setValue(int(self.settings.get('infill_density', 0.2) * 100))
        self.infill_pattern.setCurrentText(self.settings.get('infill_pattern', 'grid'))
        self.infill_angle.setValue(self.settings.get('infill_angle', 45))
        self.enable_optimized_infill.setChecked(self.settings.get('enable_optimized_infill', True))
        self.infill_resolution.setValue(self.settings.get('infill_resolution', 1.0))
        
        # Advanced settings
        self.extrusion_width.setValue(self.settings.get('extrusion_width', 0.48))
        self.filament_diameter.setValue(self.settings.get('filament_diameter', 1.75))
        self.first_layer_height.setValue(self.settings.get('first_layer_height', 0.3))
        self.first_layer_speed.setValue(int(self.settings.get('first_layer_speed', 30) / 60 * 100))  # Convert from mm/s to %
        self.z_hop.setValue(self.settings.get('z_hop', 0.4))
        self.skirt_line_count.setValue(self.settings.get('skirt_line_count', 1))
        self.skirt_distance.setValue(self.settings.get('skirt_distance', 5.0))
        
        # Temperature settings
        self.temperature.setValue(self.settings.get('temperature', 200))
        self.bed_temperature.setValue(self.settings.get('bed_temperature', 60))
        self.fan_speed.setValue(self.settings.get('fan_speed', 100))
        self.fan_layer.setValue(self.settings.get('fan_layer', 2))
        
        # Custom G-code
        self.start_gcode.setPlainText(self.settings.get('start_gcode', ''))
        self.end_gcode.setPlainText(self.settings.get('end_gcode', ''))
    
    def get_settings(self):
        """Get the current settings from the UI."""
        settings = {}
        
        # General settings
        settings['layer_height'] = self.layer_height.value()
        settings['print_speed'] = self.print_speed.value()
        settings['travel_speed'] = self.travel_speed.value()
        settings['retraction_length'] = self.retraction_length.value()
        
        # Path optimization
        settings['enable_path_optimization'] = self.enable_path_optimization.isChecked()
        settings['enable_arc_detection'] = self.enable_arc_detection.isChecked()
        settings['arc_tolerance'] = self.arc_tolerance.value()
        settings['min_arc_segments'] = self.min_arc_segments.value()
        settings['remove_redundant_moves'] = self.remove_redundant_moves.isChecked()
        settings['combine_coincident_moves'] = self.combine_coincident_moves.isChecked()
        settings['optimize_travel_moves'] = self.optimize_travel_moves.isChecked()
        
        # Infill settings
        settings['infill_density'] = self.infill_density.value() / 100.0  # Convert % to decimal
        settings['infill_pattern'] = self.infill_pattern.currentText()
        settings['infill_angle'] = self.infill_angle.value()
        settings['enable_optimized_infill'] = self.enable_optimized_infill.isChecked()
        settings['infill_resolution'] = self.infill_resolution.value()
        
        # Advanced settings
        settings['extrusion_width'] = self.extrusion_width.value()
        settings['filament_diameter'] = self.filament_diameter.value()
        settings['first_layer_height'] = self.first_layer_height.value()
        settings['first_layer_speed'] = int(self.first_layer_speed.value() * 0.6)  # Convert % to mm/s (assuming 100% = 60mm/s)
        settings['z_hop'] = self.z_hop.value()
        settings['skirt_line_count'] = self.skirt_line_count.value()
        settings['skirt_distance'] = self.skirt_distance.value()
        
        # Temperature settings
        settings['temperature'] = self.temperature.value()
        settings['bed_temperature'] = self.bed_temperature.value()
        settings['fan_speed'] = self.fan_speed.value()
        settings['fan_layer'] = self.fan_layer.value()
        
        # Custom G-code
        settings['start_gcode'] = self.start_gcode.toPlainText()
        settings['end_gcode'] = self.end_gcode.toPlainText()
        
        return settings
    
    def accept(self):
        """Handle dialog accept."""
        if self._save_settings():
            super().accept()
    
    def apply(self):
        """Apply the current settings."""
        if self._save_settings():
            self.settings_changed.emit(self.settings)
    
    def reset_to_defaults(self):
        """Reset settings to default values."""
        # Default settings
        default_settings = {
            'layer_height': 0.2,
            'print_speed': 60,
            'travel_speed': 120,
            'retraction_length': 5.0,
            'enable_path_optimization': True,
            'enable_arc_detection': True,
            'arc_tolerance': 0.05,
            'min_arc_segments': 8,
            'remove_redundant_moves': True,
            'combine_coincident_moves': True,
            'optimize_travel_moves': True,
            'infill_density': 0.2,
            'infill_pattern': 'grid',
            'infill_angle': 45,
            'enable_optimized_infill': True,
            'infill_resolution': 1.0,
            'extrusion_width': 0.48,
            'filament_diameter': 1.75,
            'first_layer_height': 0.3,
            'first_layer_speed': 30,
            'z_hop': 0.4,
            'skirt_line_count': 1,
            'skirt_distance': 5.0,
            'temperature': 200,
            'bed_temperature': 60,
            'fan_speed': 100,
            'fan_layer': 2,
            'start_gcode': '',
            'end_gcode': ''
        }
        
        # Update UI with default values
        self.settings.update(default_settings)
        self._load_settings()
        
        # Emit settings changed signal
        self.settings_changed.emit(self.settings)
    
    def _save_settings(self):
        """Save current settings to the config file.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Update settings from UI elements
            self.settings = self.get_settings()
            
            # Save to file
            if self.settings_manager.save_settings(self.settings):
                return True
            return False
                
        except Exception as e:
            get_logger(__name__).error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
            return False


if __name__ == "__main__":
    # Test the settings dialog
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Default settings
    settings = {
        'layer_height': 0.2,
        'print_speed': 60,
        'travel_speed': 120,
        'retraction_length': 5.0,
        'enable_path_optimization': True,
        'enable_arc_detection': True,
        'infill_density': 0.2,
        'infill_pattern': 'grid',
        'temperature': 200,
        'bed_temperature': 60
    }
    
    dialog = SettingsDialog(settings)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Settings saved:", dialog.get_settings())
    
    sys.exit()
