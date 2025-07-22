"""
Menu module for STL to GCode Converter.

This module handles the creation and management of the application's menu bar.
"""
from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtCore import Qt
from scripts.logger import get_logger
from scripts.language_manager import LanguageManager

logger = get_logger(__name__)

class MenuManager:
    """Manages the application's menu bar and actions."""
    
    def __init__(self, parent, language_manager=None):
        """Initialize the menu manager with a parent widget and language manager."""
        self.parent = parent
        self.language_manager = language_manager or LanguageManager()
        self.menubar = parent.menuBar()
        self.setup_menus()
        
        # Connect language change signal
        if self.language_manager:
            self.language_manager.language_changed.connect(self.retranslate_ui)
    
    def retranslate_ui(self):
        """Retranslate all menu items when language changes."""
        # File menu
        self.file_menu.setTitle(self._tr("file_menu.title"))
        self.open_stl_action.setText(self._tr("file_menu.open_stl"))
        self.open_gcode_action.setText(self._tr("file_menu.open_gcode"))
        self.save_gcode_action.setText(self._tr("file_menu.save_gcode"))
        self.recent_files_menu.setTitle(self._tr("file_menu.recent_files"))
        
        # View menu
        self.view_menu.setTitle(self._tr("view_menu.title"))
        
        # Help menu
        self.help_menu.setTitle(self._tr("help_menu.title"))
        self.about_action.setText(self._tr("help_menu.about"))
        self.help_action.setText(self._tr("help_menu.help"))
        self.sponsor_action.setText(self._tr("help_menu.sponsor"))
    
    def _tr(self, key, **kwargs):
        """Helper method to translate text using the language manager."""
        if self.language_manager:
            return self.language_manager.translate(key, **kwargs)
        return key
    
    def setup_menus(self):
        """Set up the menu bar and all menus."""
        # File menu
        self.file_menu = self.menubar.addMenu(self._tr("file_menu.title"))
        
        # Open STL action
        self.open_stl_action = QAction(self._tr("file_menu.open_stl"), self.parent)
        self.open_stl_action.setShortcut("Ctrl+O")
        self.open_stl_action.triggered.connect(self.parent.open_file)
        self.file_menu.addAction(self.open_stl_action)
        
        # Open G-code action
        self.open_gcode_action = QAction(self._tr("file_menu.open_gcode"), self.parent)
        self.open_gcode_action.setShortcut("Ctrl+G")
        self.open_gcode_action.triggered.connect(self.parent.open_gcode_in_editor)
        self.file_menu.addAction(self.open_gcode_action)
        
        # Save G-code action
        self.save_gcode_action = QAction(self._tr("file_menu.save_gcode"), self.parent)
        self.save_gcode_action.setShortcut("Ctrl+S")
        self.save_gcode_action.triggered.connect(lambda: self.parent.save_gcode())
        self.file_menu.addAction(self.save_gcode_action)
        
        # Separator
        self.file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_files_menu = self.file_menu.addMenu(self._tr("file_menu.recent_files"))
        self.parent._update_recent_files_menu()
        
        # Separator
        self.file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction(self._tr("file_menu.exit"), self.parent)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.parent.close)
        self.file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menubar.addMenu(self._tr("edit_menu.title"))
        
        # Settings action
        settings_action = QAction(self._tr("edit_menu.settings"), self.parent)
        settings_action.triggered.connect(self.parent.show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        self.view_menu = self.menubar.addMenu(self._tr("view_menu.title"))
        
        # Toggle log viewer action
        toggle_log_action = QAction(self._tr("view_menu.show_log"), self.parent, checkable=True)
        toggle_log_action.setShortcut("Ctrl+L")
        toggle_log_action.toggled.connect(self.parent.toggle_log_viewer)
        self.view_menu.addAction(toggle_log_action)
        
        # Language submenu
        language_menu = self.view_menu.addMenu(self._tr("view_menu.language"))
        language_group = QActionGroup(self.parent)
        
        # Add available languages
        if self.language_manager:
            for lang_code, lang_name in self.language_manager.available_languages.items():
                action = QAction(lang_name, self.parent, checkable=True)
                action.setData(lang_code)
                action.setChecked(lang_code == self.language_manager.current_language)
                action.triggered.connect(self.change_language)
                language_group.addAction(action)
                language_menu.addAction(action)
        
        # Help menu
        self.help_menu = self.menubar.addMenu(self._tr("help_menu.title"))
        
        # Documentation action
        docs_action = QAction(self._tr("help_menu.documentation"), self.parent)
        docs_action.triggered.connect(self.parent.show_documentation)
        self.help_menu.addAction(docs_action)
        
        # About action
        self.about_action = QAction(self._tr("help_menu.about"), self.parent)
        self.about_action.triggered.connect(lambda: self.parent.show_about())
        self.help_menu.addAction(self.about_action)
        
        # Help action
        self.help_action = QAction(self._tr("help_menu.help"), self.parent)
        self.help_action.setShortcut("F1")
        self.help_action.triggered.connect(lambda: self.parent.show_help())
        self.help_menu.addAction(self.help_action)
        
        # Sponsor action
        self.sponsor_action = QAction(self._tr("help_menu.sponsor"), self.parent)
        self.sponsor_action.triggered.connect(lambda: self.parent.show_sponsor())
        self.help_menu.addAction(self.sponsor_action)
        
        # Check for updates action
        update_action = QAction(self._tr("help_menu.check_updates"), self.parent)
        update_action.triggered.connect(lambda: self.parent.check_updates(True))
        self.help_menu.addAction(update_action)
        
        # Separator
        self.help_menu.addSeparator()
        
        logger.info("Menu bar initialized")
    
    def change_language(self):
        """Handle language change from the menu."""
        action = self.parent.sender()
        if action and hasattr(action, 'data') and self.language_manager:
            lang_code = action.data()
            self.language_manager.set_language(lang_code)
