"""
Help system for STL to G-Code Converter.

This module provides a help system that supports multiple languages.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QPushButton, 
                           QHBoxLayout, QTabWidget, QWidget, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon
import os
from pathlib import Path
from scripts.logger import get_logger
from scripts.language_manager import LanguageManager
from scripts.help_translations import HELP_TRANSLATIONS

logger = get_logger(__name__)

class HelpDialog(QDialog):
    """A dialog displaying help information for the application."""
    
    def __init__(self, language_manager: LanguageManager = None, parent=None):
        """Initialize the help dialog."""
        super().__init__(parent)
        
        # Initialize language manager
        self.lang_manager = language_manager or LanguageManager()
        self.translate = self._translate
        
        # Connect language change signal
        if hasattr(self.lang_manager, 'language_changed'):
            self.lang_manager.language_changed.connect(self.retranslate_ui)
        
        self.setWindowTitle(self.translate("help.window_title"))
        self.setMinimumSize(900, 700)
        
        # Set window properties
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # Set application icon if available
        icon_path = Path("assets/icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.tabs = {}
        tab_ids = ['welcome', 'getting_started', 'features', 'shortcuts', 'support']
        for tab_id in tab_ids:
            self._add_tab(tab_id)
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget, 1)
        
        # Add close button
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        # Add documentation button
        self.docs_button = QPushButton()
        self.docs_button.clicked.connect(self._open_documentation)
        button_box.addWidget(self.docs_button)
        
        # Add close button
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        button_box.addWidget(self.close_button)
        
        main_layout.addLayout(button_box)
        self.setLayout(main_layout)
        
        # Set initial translations
        self.retranslate_ui()
    
    def _translate(self, key: str, **kwargs) -> str:
        """Translate a key using the language manager."""
        # First try to get from help translations
        lang = self.lang_manager.current_language
        if lang in HELP_TRANSLATIONS and key in HELP_TRANSLATIONS[lang]:
            text = HELP_TRANSLATIONS[lang][key]
            if isinstance(text, str) and kwargs:
                return text.format(**kwargs)
            return text
        
        # Fall back to main translations
        return self.lang_manager.translate(key, **kwargs)
    
    def _add_tab(self, tab_id: str):
        """Add a tab with the given ID to the tab widget."""
        content = QTextBrowser()
        content.setOpenExternalLinks(True)
        content.setStyleSheet("""
            QTextBrowser {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            h1, h2, h3, h4, h5, h6 { color: #333; }
            .note {
                background-color: #e7f4ff;
                border-left: 4px solid #0066cc;
                padding: 10px;
                margin: 10px 0;
                border-radius: 0 4px 4px 0;
            }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }
        """)
        
        self.tabs[tab_id] = content
        self.tab_widget.addTab(content, self.translate(f"help.{tab_id}.tab_title"))
        self._update_tab_content(tab_id)
    
    def _update_tab_content(self, tab_id: str):
        """Update the content of a tab based on the current language."""
        if tab_id not in self.tabs:
            return
            
        content = self.tabs[tab_id]
        html = self.translate(f"help.{tab_id}.content")
        
        # Add basic HTML structure if not present
        if not html.strip().lower().startswith(('<!doctype', '<html>')):
            # Use double curly braces to escape them in the format string
            html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            line-height: 1.6; 
            color: #333;
            margin: 0;
            padding: 0;
        }}
        h1, h2, h3, h4, h5, h6 {{ 
            color: #2c3e50; 
            margin-top: 1.5em;
        }}
        h1 {{ font-size: 1.8em; }}
        h2 {{ font-size: 1.5em; }}
        h3 {{ font-size: 1.3em; }}
        code {{ 
            background-color: #f5f5f5; 
            padding: 2px 5px; 
            border-radius: 3px; 
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
        }}
        .note {{
            background-color: #e7f4ff;
            border-left: 4px solid #0066cc;
            padding: 10px 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }}
        .warning {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 10px 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }}
        .tip {{
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 10px 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""
            # Format the template with the content
            html = html_template.format(content=html)
        
        content.setHtml(html)
    
    def _open_documentation(self):
        """Open the online documentation in the default web browser."""
        docs_url = "https://github.com/Nsfr750/STL_to_G-Code/wiki"
        QDesktopServices.openUrl(QUrl(docs_url))
    
    def retranslate_ui(self):
        """Update the UI with the current language."""
        self.setWindowTitle(self.translate("help.window_title"))
        self.docs_button.setText(self.translate("help.buttons.documentation"))
        self.close_button.setText(self.translate("common.buttons.close"))
        
        # Update tab titles and content
        for tab_id, content in self.tabs.items():
            tab_index = self.tab_widget.indexOf(content)
            if tab_index >= 0:
                self.tab_widget.setTabText(tab_index, self.translate(f"help.{tab_id}.tab_title"))
            self._update_tab_content(tab_id)

def show_help(parent=None, language_manager=None):
    """
    Show the help dialog.
    
    Args:
        parent: The parent widget
        language_manager: Optional LanguageManager instance
    """
    try:
        dialog = HelpDialog(language_manager=language_manager, parent=parent)
        dialog.exec()
    except Exception as e:
        logger.error(f"Error showing help dialog: {e}", exc_info=True)
        QMessageBox.critical(
            parent,
            "Error",
            f"Failed to display help: {str(e)}\n\nPlease check the logs for more details."
        )

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Initialize language manager with test language
    from scripts.language_manager import LanguageManager
    lang_manager = LanguageManager()
    
    # Show the help dialog
    show_help(language_manager=lang_manager)
    
    sys.exit(app.exec())
