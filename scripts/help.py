"""
Help documentation and user guide for STL to GCode Converter.

This module provides comprehensive help documentation and a user guide
for the STL to GCode Converter application.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                            QHBoxLayout, QApplication, QWidget, QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
import webbrowser
import os
from scripts.logger import get_logger
from scripts.language_manager import LanguageManager

# Import the markdown viewer
from .markdown_viewer import show_documentation

# Create a logger
logger = get_logger(__name__)

def get_help_content(language_manager):
    """Generate help content with translated strings.
    
    Args:
        language_manager: The LanguageManager instance to use for translations
    """
    try:
        return f"""
        <h1>{language_manager.translate('help.title')}</h1>

        <h2>{language_manager.translate('help.overview.title')}</h2>
        <p>{language_manager.translate('help.overview.description')}</p>

        <h2>{language_manager.translate('help.getting_started.title')}</h2>
        <ol>
            <li>{language_manager.translate('help.getting_started.step1')}</li>
            <li>{language_manager.translate('help.getting_started.step2')}</li>
            <li>{language_manager.translate('help.getting_started.step3')}</li>
            <li>{language_manager.translate('help.getting_started.step4')}</li>
            <li>{language_manager.translate('help.getting_started.step5')}</li>
        </ol>

        <h2>{language_manager.translate('help.features.title')}</h2>

        <h3>{language_manager.translate('help.features.file_management.title')}</h3>
        <ul>
            <li>{language_manager.translate('help.features.file_management.item1')}</li>
            <li>{language_manager.translate('help.features.file_management.item2')}</li>
            <li>{language_manager.translate('help.features.file_management.item3')}</li>
            <li>{language_manager.translate('help.features.file_management.item4')}</li>
            <li>{language_manager.translate('help.features.file_management.item5')}</li>
        </ul>

        <h3>{language_manager.translate('help.features.visualization.title')}</h3>
        <ul>
            <li>{language_manager.translate('help.features.visualization.item1')}</li>
            <li>{language_manager.translate('help.features.visualization.item2')}</li>
            <li>{language_manager.translate('help.features.visualization.item3')}</li>
            <li>{language_manager.translate('help.features.visualization.item4')}</li>
            <li>{language_manager.translate('help.features.visualization.item5')}</li>
        </ul>

        <h3>{language_manager.translate('help.features.gcode_tools.title')}</h3>
        <ul>
            <li>{language_manager.translate('help.features.gcode_tools.item1')}</li>
            <li>{language_manager.translate('help.features.gcode_tools.item2')}</li>
            <li>{language_manager.translate('help.features.gcode_tools.item3')}</li>
            <li>{language_manager.translate('help.features.gcode_tools.item4')}</li>
            <li>{language_manager.translate('help.features.gcode_tools.item5')}</li>
        </ul>

        <h3>{language_manager.translate('help.features.documentation.title')}</h3>
        <ul>
            <li>{language_manager.translate('help.features.documentation.item1')}</li>
            <li>{language_manager.translate('help.features.documentation.item2')}</li>
            <li>{language_manager.translate('help.features.documentation.item3')}</li>
            <li>{language_manager.translate('help.features.documentation.item4')}</li>
        </ul>

        <h3>{language_manager.translate('help.features.advanced.title')}</h3>
        <ul>
            <li>{language_manager.translate('help.features.advanced.item1')}</li>
            <li>{language_manager.translate('help.features.advanced.item2')}</li>
            <li>{language_manager.translate('help.features.advanced.item3')}</li>
            <li>{language_manager.translate('help.features.advanced.item4')}</li>
            <li>{language_manager.translate('help.features.advanced.item5')}</li>
        </ul>

        <h2>{language_manager.translate('help.shortcuts.title')}</h2>
        <ul>
            <li><b>{language_manager.translate('help.shortcuts.ctrl_o')}</b>: {language_manager.translate('help.shortcuts.ctrl_o_desc')}</li>
            <li><b>{language_manager.translate('help.shortcuts.ctrl_s')}</b>: {language_manager.translate('help.shortcuts.ctrl_s_desc')}</li>
            <li><b>{language_manager.translate('help.shortcuts.f1')}</b>: {language_manager.translate('help.shortcuts.f1_desc')}</li>
            <li><b>{language_manager.translate('help.shortcuts.ctrl_q')}</b>: {language_manager.translate('help.shortcuts.ctrl_q_desc')}</li>
            <li><b>{language_manager.translate('help.shortcuts.ctrl_l')}</b>: {language_manager.translate('help.shortcuts.ctrl_l_desc')}</li>
            <li><b>{language_manager.translate('help.shortcuts.ctrl_g')}</b>: {language_manager.translate('help.shortcuts.ctrl_g_desc')}</li>
        </ul>

        <h2>{language_manager.translate('help.support.title')}</h2>
        <p>{language_manager.translate('help.support.description')}</p>
        """
    except Exception as e:
        logger.error(f"Error generating help content: {e}")
        # Fallback to English if there's an error
        return """
        <h1>Help - STL to G-Code</h1>
        <p>An error occurred while loading the help content. Please check the logs for more details.</p>
        """

class HelpDialog(QDialog):
    """A dialog displaying help information for the application."""
    
    def __init__(self, parent=None, language_manager=None):
        """Initialize the help dialog.
        
        Args:
            parent: The parent widget
            language_manager: The LanguageManager instance to use for translations
        """
        super().__init__(parent)
        self.language_manager = language_manager or LanguageManager()
        self.setWindowTitle(self.language_manager.translate("help.dialog.title"))
        self.setMinimumSize(800, 600)
        
        # Set window modality to make it modal
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Set window flags to make it a proper dialog
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Create text edit for help content
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(get_help_content(self.language_manager))
        
        # Set document to be scrollable with proper margins
        self.text_edit.document().setDocumentMargin(20)
        
        # Add text edit to layout
        layout.addWidget(self.text_edit)
        
        # Create button box
        button_box = QHBoxLayout()
        
        # Add full documentation button
        self.full_docs_button = QPushButton(
            self.language_manager.translate("help.buttons.full_documentation")
        )
        self.full_docs_button.setToolTip(
            self.language_manager.translate("help.tooltips.full_documentation")
        )
        self.full_docs_button.clicked.connect(self.open_documentation)
        
        # Add close button
        self.close_button = QPushButton(
            self.language_manager.translate("common.buttons.close")
        )
        self.close_button.clicked.connect(self.accept)
        
        # Add buttons to button box
        button_box.addWidget(self.full_docs_button)
        button_box.addStretch()
        button_box.addWidget(self.close_button)
        
        # Add button box to main layout
        layout.addLayout(button_box)
        
        # Set the layout
        self.setLayout(layout)
    
    def open_documentation(self):
        """Open the full documentation in the default web browser."""
        try:
            # Get the base directory of the application
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            docs_path = os.path.join(base_dir, 'docs', 'index.html')
            
            # Check if the documentation exists
            if os.path.exists(docs_path):
                # Open the local documentation
                QDesktopServices.openUrl(QUrl.fromLocalFile(docs_path))
            else:
                # Fallback to online documentation
                QDesktopServices.openUrl(QUrl("https://github.com/Nsfr750/STL_to_G-Code/wiki"))
        except Exception as e:
            logger.error(f"Error opening documentation: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open documentation: {str(e)}"
            )

def show_help(parent=None, language_manager=None):
    """
    Show the help dialog.
    
    Args:
        parent: The parent QWidget window
        language_manager: The LanguageManager instance to use for translations
    """
    try:
        dialog = HelpDialog(parent, language_manager)
        dialog.exec()
    except Exception as e:
        logger.error(f"Error showing help dialog: {e}")
        QMessageBox.critical(
            parent,
            "Error",
            f"Could not display help: {str(e)}"
        )

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Set up logging
    from scripts.logger import setup_logging
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Show the help dialog
    show_help()
    
    sys.exit(app.exec())
