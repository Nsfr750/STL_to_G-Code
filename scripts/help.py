"""
Help documentation and user guide for STL to GCode Converter.

This module provides comprehensive help documentation and a user guide
for the STL to GCode Converter application.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                            QHBoxLayout, QApplication, QWidget, QLabel, QFrame)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
import webbrowser
import os
from scripts.logger import get_logger
from scripts.language_manager import get_language_manager

# Import the markdown viewer
from .markdown_viewer import show_documentation

# Initialize language manager
language_manager = get_language_manager()

def get_help_content():
    """Generate help content with translated strings."""
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

class HelpDialog(QDialog):
    """
    Dialog window for displaying help documentation using PyQt6.
    """
    def __init__(self, parent=None):
        """
        Initialize the help dialog window.
        
        Args:
            parent: The parent QWidget window
        """
        super().__init__(parent)
        self.parent = parent
        self.language_manager = get_language_manager()
        self.translate = self.language_manager.translate
        
        self.setWindowTitle(self.translate('help.dialog.title'))
        self.resize(900, 700)
        
        # Set window modality
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Documentation button
        doc_btn = QPushButton(self.translate('help.buttons.full_documentation'))
        doc_btn.setToolTip(self.translate('help.tooltips.full_documentation'))
        doc_btn.clicked.connect(self.open_documentation)
        toolbar.addWidget(doc_btn)
        
        # Add some stretch
        toolbar.addStretch()
        
        # Close button
        close_btn = QPushButton(self.translate('common.buttons.close'))
        close_btn.clicked.connect(self.accept)
        toolbar.addWidget(close_btn)
        
        layout.addLayout(toolbar)
        
        # Add a line separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Create text edit for help content
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(get_help_content())
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: Arial, sans-serif;
                font-size: 12px;
                border: 1px solid #444;
                border-radius: 4px;
            }
            h1, h2, h3 {
                color: #4da6ff;
                margin-top: 1em;
                margin-bottom: 0.5em;
            }
            ul, ol {
                margin-top: 0.5em;
                margin-bottom: 0.5em;
            }
            li {
                margin-bottom: 0.25em;
            }
        """)
        layout.addWidget(self.text_edit)
        
        # Add some padding
        self.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
    
    def open_documentation(self):
        """Open the full documentation in the markdown viewer."""
        self.close()  # Close the help dialog
        show_documentation()

def show_help(parent=None):
    """
    Show the help dialog.
    
    Args:
        parent: The parent QWidget window
    """
    dialog = HelpDialog(parent)
    dialog.exec()

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = HelpDialog()
    dialog.show()
    sys.exit(app.exec())
