"""
Settings dialog for STL to GCode Converter.

This module provides a settings dialog for configuring optimization parameters.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from scripts.logger import get_logger
from scripts.language_manager import LanguageManager
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
            self.logger.info("No settings file found, using defaults")
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.logger.info("Settings loaded successfully")
                return settings
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
                json.dump(settings, f, indent=4)
            self.logger.info("Settings saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False


class SettingsDialog(QDialog):
    """Dialog for configuring optimization settings."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None, parent=None, language_manager: Optional[LanguageManager] = None):
        """Initialize the settings dialog.
        
        Args:
            settings: Optional initial settings (dict or QSettings)
            parent: Parent widget
            language_manager: Language manager for translations
        """
        super().__init__(parent)
        
        # Initialize language manager
        self.lang_manager = language_manager or LanguageManager()
        
        # Connect language changed signal
        if self.lang_manager:
            self.lang_manager.language_changed.connect(self.retranslate_ui)
        
        self.setMinimumWidth(600)
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Default settings
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
        self.retranslate_ui()
    
    def translate(self, key, **kwargs):
        """Helper method to get translated text."""
        if hasattr(self, "lang_manager") and self.lang_manager:
            return self.lang_manager.translate(key, **kwargs)
        return key  # Fallback to key if no translation available
    
    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.setWindowTitle(self.translate("settings_dialog.title"))
        
        # Tab names
        self.tab_widget.setTabText(0, self.translate("settings_dialog.tabs.general"))
        self.tab_widget.setTabText(1, self.translate("settings_dialog.tabs.path_optimization"))
        self.tab_widget.setTabText(2, self.translate("settings_dialog.tabs.infill"))
        self.tab_widget.setTabText(3, self.translate("settings_dialog.tabs.advanced"))
        
        # Group box titles
        self.general_group.setTitle(self.translate("settings_dialog.general.title"))
        self.path_optimization_group.setTitle(self.translate("settings_dialog.path_optimization.title"))
        self.infill_group.setTitle(self.translate("settings_dialog.infill.title"))
        self.advanced_group.setTitle(self.translate("settings_dialog.advanced.title"))
        self.gcode_group.setTitle(self.translate("settings_dialog.gcode.title"))
        
        # Button box
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.translate("common.buttons.ok"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.translate("common.buttons.cancel"))
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).setText(self.translate("common.buttons.apply"))
        self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).setText(
            self.translate("common.buttons.restore_defaults"))
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self._create_general_tab()
        self._create_path_optimization_tab()
        self._create_infill_tab()
        self._create_advanced_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        
        # Connect signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.reset_to_defaults)
    
    def _create_general_tab(self):
        """Create the General tab."""
        self.general_tab = QWidget()
        layout = QVBoxLayout(self.general_tab)
        
        # General settings group
        self.general_group = QGroupBox()
        form_layout = QFormLayout()
        
        # Layer height
        self.layer_height_spin = QDoubleSpinBox()
        self.layer_height_spin.setRange(0.05, 1.0)
        self.layer_height_spin.setSingleStep(0.05)
        self.layer_height_spin.setDecimals(2)
        form_layout.addRow(QLabel(self.translate("settings_dialog.general.layer_height")), self.layer_height_spin)
        
        # Print speed
        self.print_speed_spin = QSpinBox()
        self.print_speed_spin.setRange(1, 300)
        form_layout.addRow(QLabel(self.translate("settings_dialog.general.print_speed")), self.print_speed_spin)
        
        # Travel speed
        self.travel_speed_spin = QSpinBox()
        self.travel_speed_spin.setRange(1, 500)
        form_layout.addRow(QLabel(self.translate("settings_dialog.general.travel_speed")), self.travel_speed_spin)
        
        # Retraction length
        self.retraction_length_spin = QDoubleSpinBox()
        self.retraction_length_spin.setRange(0, 20)
        self.retraction_length_spin.setSingleStep(0.5)
        self.retraction_length_spin.setDecimals(1)
        form_layout.addRow(QLabel(self.translate("settings_dialog.general.retraction_length")), self.retraction_length_spin)
        
        self.general_group.setLayout(form_layout)
        layout.addWidget(self.general_group)
        layout.addStretch()
        
        self.tab_widget.addTab(self.general_tab, "")
    
    def _create_path_optimization_tab(self):
        """Create the Path Optimization tab."""
        self.path_optimization_tab = QWidget()
        layout = QVBoxLayout(self.path_optimization_tab)
        
        # Path optimization group
        self.path_optimization_group = QGroupBox()
        form_layout = QFormLayout()
        
        # Enable path optimization
        self.enable_path_optimization_cb = QCheckBox()
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.enable")), self.enable_path_optimization_cb)
        
        # Enable arc detection
        self.enable_arc_detection_cb = QCheckBox()
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.enable_arcs")), self.enable_arc_detection_cb)
        
        # Arc tolerance
        self.arc_tolerance_spin = QDoubleSpinBox()
        self.arc_tolerance_spin.setRange(0.01, 1.0)
        self.arc_tolerance_spin.setSingleStep(0.01)
        self.arc_tolerance_spin.setDecimals(2)
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.arc_tolerance")), self.arc_tolerance_spin)
        
        # Min arc segments
        self.min_arc_segments_spin = QSpinBox()
        self.min_arc_segments_spin.setRange(3, 100)
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.min_arc_segments")), self.min_arc_segments_spin)
        
        # Remove redundant moves
        self.remove_redundant_moves_cb = QCheckBox()
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.remove_redundant")), self.remove_redundant_moves_cb)
        
        # Combine coincident moves
        self.combine_coincident_moves_cb = QCheckBox()
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.combine_coincident")), self.combine_coincident_moves_cb)
        
        # Optimize travel moves
        self.optimize_travel_moves_cb = QCheckBox()
        form_layout.addRow(QLabel(self.translate("settings_dialog.path_optimization.optimize_travel")), self.optimize_travel_moves_cb)
        
        self.path_optimization_group.setLayout(form_layout)
        layout.addWidget(self.path_optimization_group)
        layout.addStretch()
        
        self.tab_widget.addTab(self.path_optimization_tab, "")
    
    def _create_infill_tab(self):
        """Create the Infill tab."""
        self.infill_tab = QWidget()
        layout = QVBoxLayout(self.infill_tab)
        
        # Infill settings group
        self.infill_group = QGroupBox()
        form_layout = QFormLayout()
        
        # Infill density
        self.infill_density_spin = QDoubleSpinBox()
        self.infill_density_spin.setRange(0, 1)
        self.infill_density_spin.setSingleStep(0.05)
        self.infill_density_spin.setDecimals(2)
        form_layout.addRow(QLabel(self.translate("settings_dialog.infill.density")), self.infill_density_spin)
        
        # Infill pattern
        self.infill_pattern_combo = QComboBox()
        self.infill_pattern_combo.addItems([
            self.translate("settings_dialog.infill.patterns.grid"),
            self.translate("settings_dialog.infill.patterns.lines"),
            self.translate("settings_dialog.infill.patterns.triangles"),
            self.translate("settings_dialog.infill.patterns.trihexagon"),
            self.translate("settings_dialog.infill.patterns.cubic")
        ])
        form_layout.addRow(QLabel(self.translate("settings_dialog.infill.pattern")), self.infill_pattern_combo)
        
        # Infill angle
        self.infill_angle_spin = QSpinBox()
        self.infill_angle_spin.setRange(0, 359)
        form_layout.addRow(QLabel(self.translate("settings_dialog.infill.angle")), self.infill_angle_spin)
        
        # Enable optimized infill
        self.enable_optimized_infill_cb = QCheckBox()
        form_layout.addRow(QLabel(self.translate("settings_dialog.infill.enable_optimized")), self.enable_optimized_infill_cb)
        
        # Infill resolution
        self.infill_resolution_spin = QDoubleSpinBox()
        self.infill_resolution_spin.setRange(0.1, 5.0)
        self.infill_resolution_spin.setSingleStep(0.1)
        self.infill_resolution_spin.setDecimals(1)
        form_layout.addRow(QLabel(self.translate("settings_dialog.infill.resolution")), self.infill_resolution_spin)
        
        self.infill_group.setLayout(form_layout)
        layout.addWidget(self.infill_group)
        layout.addStretch()
        
        self.tab_widget.addTab(self.infill_tab, "")
    
    def _create_advanced_tab(self):
        """Create the Advanced tab."""
        self.advanced_tab = QWidget()
        layout = QVBoxLayout(self.advanced_tab)
        
        # Advanced settings group
        self.advanced_group = QGroupBox()
        form_layout = QFormLayout()
        
        # Extrusion width
        self.extrusion_width_spin = QDoubleSpinBox()
        self.extrusion_width_spin.setRange(0.1, 2.0)
        self.extrusion_width_spin.setSingleStep(0.05)
        self.extrusion_width_spin.setDecimals(2)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.extrusion_width")), self.extrusion_width_spin)
        
        # Filament diameter
        self.filament_diameter_spin = QDoubleSpinBox()
        self.filament_diameter_spin.setRange(1.0, 3.0)
        self.filament_diameter_spin.setSingleStep(0.05)
        self.filament_diameter_spin.setDecimals(2)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.filament_diameter")), self.filament_diameter_spin)
        
        # First layer height
        self.first_layer_height_spin = QDoubleSpinBox()
        self.first_layer_height_spin.setRange(0.05, 1.0)
        self.first_layer_height_spin.setSingleStep(0.05)
        self.first_layer_height_spin.setDecimals(2)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.first_layer_height")), self.first_layer_height_spin)
        
        # First layer speed
        self.first_layer_speed_spin = QSpinBox()
        self.first_layer_speed_spin.setRange(1, 300)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.first_layer_speed")), self.first_layer_speed_spin)
        
        # Z-hop
        self.z_hop_spin = QDoubleSpinBox()
        self.z_hop_spin.setRange(0, 10.0)
        self.z_hop_spin.setSingleStep(0.1)
        self.z_hop_spin.setDecimals(1)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.z_hop")), self.z_hop_spin)
        
        # Skirt line count
        self.skirt_line_count_spin = QSpinBox()
        self.skirt_line_count_spin.setRange(0, 10)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.skirt_line_count")), self.skirt_line_count_spin)
        
        # Skirt distance
        self.skirt_distance_spin = QDoubleSpinBox()
        self.skirt_distance_spin.setRange(0, 20.0)
        self.skirt_distance_spin.setSingleStep(0.5)
        self.skirt_distance_spin.setDecimals(1)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.skirt_distance")), self.skirt_distance_spin)
        
        # Temperature
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 400)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.temperature")), self.temperature_spin)
        
        # Bed temperature
        self.bed_temperature_spin = QSpinBox()
        self.bed_temperature_spin.setRange(0, 200)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.bed_temperature")), self.bed_temperature_spin)
        
        # Fan speed
        self.fan_speed_spin = QSpinBox()
        self.fan_speed_spin.setRange(0, 100)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.fan_speed")), self.fan_speed_spin)
        
        # Fan layer
        self.fan_layer_spin = QSpinBox()
        self.fan_layer_spin.setRange(0, 20)
        form_layout.addRow(QLabel(self.translate("settings_dialog.advanced.fan_layer")), self.fan_layer_spin)
        
        self.advanced_group.setLayout(form_layout)
        
        # G-code group
        self.gcode_group = QGroupBox()
        gcode_layout = QVBoxLayout()
        
        # Start G-code
        self.start_gcode_edit = QPlainTextEdit()
        self.start_gcode_edit.setPlaceholderText(self.translate("settings_dialog.gcode.start_placeholder"))
        gcode_layout.addWidget(QLabel(self.translate("settings_dialog.gcode.start")))
        gcode_layout.addWidget(self.start_gcode_edit)
        
        # End G-code
        self.end_gcode_edit = QPlainTextEdit()
        self.end_gcode_edit.setPlaceholderText(self.translate("settings_dialog.gcode.end_placeholder"))
        gcode_layout.addWidget(QLabel(self.translate("settings_dialog.gcode.end")))
        gcode_layout.addWidget(self.end_gcode_edit)
        
        self.gcode_group.setLayout(gcode_layout)
        
        layout.addWidget(self.advanced_group)
        layout.addWidget(self.gcode_group)
        layout.addStretch()
        
        self.tab_widget.addTab(self.advanced_tab, "")
    
    def _setup_layout(self):
        """Set up the dialog layout."""
        layout = QVBoxLayout(self)
        layout.addWidget(self.tab_widget)
        layout.addWidget(self.button_box)
    
    def _load_settings(self):
        """Load settings into the UI."""
        # General settings
        self.layer_height_spin.setValue(self.settings.get('layer_height', 0.2))
        self.print_speed_spin.setValue(self.settings.get('print_speed', 60))
        self.travel_speed_spin.setValue(self.settings.get('travel_speed', 120))
        self.retraction_length_spin.setValue(self.settings.get('retraction_length', 5.0))
        
        # Path optimization settings
        self.enable_path_optimization_cb.setChecked(self.settings.get('enable_path_optimization', True))
        self.enable_arc_detection_cb.setChecked(self.settings.get('enable_arc_detection', True))
        self.arc_tolerance_spin.setValue(self.settings.get('arc_tolerance', 0.05))
        self.min_arc_segments_spin.setValue(self.settings.get('min_arc_segments', 8))
        self.remove_redundant_moves_cb.setChecked(self.settings.get('remove_redundant_moves', True))
        self.combine_coincident_moves_cb.setChecked(self.settings.get('combine_coincident_moves', True))
        self.optimize_travel_moves_cb.setChecked(self.settings.get('optimize_travel_moves', True))
        
        # Infill settings
        self.infill_density_spin.setValue(self.settings.get('infill_density', 0.2))
        
        infill_pattern = self.settings.get('infill_pattern', 'grid')
        pattern_index = {
            'grid': 0,
            'lines': 1,
            'triangles': 2,
            'trihexagon': 3,
            'cubic': 4
        }.get(infill_pattern, 0)
        self.infill_pattern_combo.setCurrentIndex(pattern_index)
        
        self.infill_angle_spin.setValue(self.settings.get('infill_angle', 45))
        self.enable_optimized_infill_cb.setChecked(self.settings.get('enable_optimized_infill', True))
        self.infill_resolution_spin.setValue(self.settings.get('infill_resolution', 1.0))
        
        # Advanced settings
        self.extrusion_width_spin.setValue(self.settings.get('extrusion_width', 0.48))
        self.filament_diameter_spin.setValue(self.settings.get('filament_diameter', 1.75))
        self.first_layer_height_spin.setValue(self.settings.get('first_layer_height', 0.3))
        self.first_layer_speed_spin.setValue(self.settings.get('first_layer_speed', 30))
        self.z_hop_spin.setValue(self.settings.get('z_hop', 0.4))
        self.skirt_line_count_spin.setValue(self.settings.get('skirt_line_count', 1))
        self.skirt_distance_spin.setValue(self.settings.get('skirt_distance', 5.0))
        self.temperature_spin.setValue(self.settings.get('temperature', 200))
        self.bed_temperature_spin.setValue(self.settings.get('bed_temperature', 60))
        self.fan_speed_spin.setValue(self.settings.get('fan_speed', 100))
        self.fan_layer_spin.setValue(self.settings.get('fan_layer', 2))
        
        # G-code
        self.start_gcode_edit.setPlainText(self.settings.get('start_gcode', ''))
        self.end_gcode_edit.setPlainText(self.settings.get('end_gcode', ''))
    
    def get_settings(self):
        """Get the current settings from the UI."""
        settings = {
            # General settings
            'layer_height': self.layer_height_spin.value(),
            'print_speed': self.print_speed_spin.value(),
            'travel_speed': self.travel_speed_spin.value(),
            'retraction_length': self.retraction_length_spin.value(),
            
            # Path optimization settings
            'enable_path_optimization': self.enable_path_optimization_cb.isChecked(),
            'enable_arc_detection': self.enable_arc_detection_cb.isChecked(),
            'arc_tolerance': self.arc_tolerance_spin.value(),
            'min_arc_segments': self.min_arc_segments_spin.value(),
            'remove_redundant_moves': self.remove_redundant_moves_cb.isChecked(),
            'combine_coincident_moves': self.combine_coincident_moves_cb.isChecked(),
            'optimize_travel_moves': self.optimize_travel_moves_cb.isChecked(),
            
            # Infill settings
            'infill_density': self.infill_density_spin.value(),
            'infill_pattern': ['grid', 'lines', 'triangles', 'trihexagon', 'cubic'][self.infill_pattern_combo.currentIndex()],
            'infill_angle': self.infill_angle_spin.value(),
            'enable_optimized_infill': self.enable_optimized_infill_cb.isChecked(),
            'infill_resolution': self.infill_resolution_spin.value(),
            
            # Advanced settings
            'extrusion_width': self.extrusion_width_spin.value(),
            'filament_diameter': self.filament_diameter_spin.value(),
            'first_layer_height': self.first_layer_height_spin.value(),
            'first_layer_speed': self.first_layer_speed_spin.value(),
            'z_hop': self.z_hop_spin.value(),
            'skirt_line_count': self.skirt_line_count_spin.value(),
            'skirt_distance': self.skirt_distance_spin.value(),
            'temperature': self.temperature_spin.value(),
            'bed_temperature': self.bed_temperature_spin.value(),
            'fan_speed': self.fan_speed_spin.value(),
            'fan_layer': self.fan_layer_spin.value(),
            
            # G-code
            'start_gcode': self.start_gcode_edit.toPlainText(),
            'end_gcode': self.end_gcode_edit.toPlainText()
        }
        
        return settings
    
    def accept(self):
        """Handle dialog accept."""
        if self._save_settings():
            super().accept()
    
    def apply(self):
        """Apply the current settings."""
        settings = self.get_settings()
        if self._save_settings():
            self.settings_changed.emit(settings)
    
    def reset_to_defaults(self):
        """Reset settings to default values."""
        reply = QMessageBox.question(
            self,
            self.translate("settings_dialog.reset_title"),
            self.translate("settings_dialog.reset_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = self.default_settings.copy()
            self._load_settings()
            self._save_settings()
            self.settings_changed.emit(self.settings)
    
    def _save_settings(self):
        """Save current settings to the config file.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        self.settings = self.get_settings()
        return self.settings_manager.save_settings(self.settings)


if __name__ == "__main__":
    # Test the settings dialog
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Initialize language manager
    from scripts.language_manager import LanguageManager
    lang_manager = LanguageManager()
    
    # Create and show the dialog
    dialog = SettingsDialog(language_manager=lang_manager)
    dialog.show()
    
    sys.exit(app.exec())
