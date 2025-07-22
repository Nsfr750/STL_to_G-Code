"""
Menu module for STL to GCode Converter.

This module handles the creation and management of the application's menu bar.
"""
from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from scripts.logger import get_logger

logger = get_logger(__name__)

class MenuManager:
    """Manages the application's menu bar and actions."""
    
    def __init__(self, parent):
        """Initialize the menu manager with a parent widget."""
        self.parent = parent
        self.menubar = parent.menuBar()
        self.setup_menus()
    
    def setup_menus(self):
        """Set up the menu bar and all menus."""
        # File menu
        file_menu = self.menubar.addMenu("&File")
        
        # Open STL action
        open_stl_action = QAction("&Open STL...", self.parent)
        open_stl_action.setShortcut("Ctrl+O")
        open_stl_action.triggered.connect(self.parent.open_file)
        file_menu.addAction(open_stl_action)
        
        # Open G-code action
        open_gcode_action = QAction("Open &G-code...", self.parent)
        open_gcode_action.setShortcut("Ctrl+G")
        open_gcode_action.triggered.connect(self.parent.open_gcode_in_editor)
        file_menu.addAction(open_gcode_action)
        
        # Save G-code action
        save_gcode_action = QAction("&Save G-code...", self.parent)
        save_gcode_action.setShortcut("Ctrl+S")
        save_gcode_action.triggered.connect(lambda: self.parent.save_gcode())
        file_menu.addAction(save_gcode_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_files_menu = file_menu.addMenu("Recent Files")
        self.parent._update_recent_files_menu()
        
        # Separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self.parent)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.parent.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menubar.addMenu("&Edit")
        
        # Settings action
        settings_action = QAction("&Settings...", self.parent)
        settings_action.triggered.connect(self.parent.show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = self.menubar.addMenu("&View")
        
        # Toggle log viewer action
        toggle_log_action = QAction("Show &Log", self.parent, checkable=True)
        toggle_log_action.setShortcut("Ctrl+L")
        toggle_log_action.toggled.connect(self.parent.toggle_log_viewer)
        view_menu.addAction(toggle_log_action)
        
        # Help menu
        help_menu = self.menubar.addMenu("&Help")
        
        # Documentation action
        docs_action = QAction("&Documentation...", self.parent)
        docs_action.triggered.connect(self.parent.show_documentation)
        help_menu.addAction(docs_action)
        
        # Help action
        help_action = QAction("&Help", self.parent)
        help_action.setShortcut("F1")
        help_action.triggered.connect(lambda: self.parent.show_help())
        help_menu.addAction(help_action)
        
        # Check for updates action
        update_action = QAction("Check for &Updates...", self.parent)
        update_action.triggered.connect(lambda: self.parent.check_updates(True))
        help_menu.addAction(update_action)
        
        # Separator
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About...", self.parent)
        about_action.triggered.connect(self.parent.show_about)
        help_menu.addAction(about_action)
        
        # Sponsor action
        sponsor_action = QAction("&Sponsor...", self.parent)
        sponsor_action.triggered.connect(self.parent.show_sponsor)
        help_menu.addAction(sponsor_action)
        
        logger.info("Menu bar initialized")
