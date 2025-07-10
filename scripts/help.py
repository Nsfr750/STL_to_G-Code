"""
Help documentation and user guide for STL to GCode Converter.

This module provides comprehensive help documentation and a user guide
for the STL to GCode Converter application. It includes:
- Application overview
- Feature descriptions
- Usage instructions
- Configuration details
- Support information
- Community links
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                            QHBoxLayout, QApplication, QWidget)
from PyQt6.QtCore import Qt
import webbrowser

HELP_CONTENT = """
<h1>STL to GCode Converter - User Guide</h1>

<h2>Overview</h2>
<p>This application converts STL (STereoLithography) files to G-code for 3D printing and CNC machining, featuring a modern PyQt6-based interface with advanced visualization and customization options.</p>

<h2>Getting Started</h2>
<ol>
    <li>Open an STL file using File > Open or drag and drop</li>
    <li>Adjust settings in the right panel as needed</li>
    <li>Preview the 3D model using the view controls</li>
    <li>Generate G-code using the toolbar button</li>
    <li>Save or export your G-code</li>
</ol>

<h2>Features</h2>

<h3>File Management</h3>
<ul>
    <li>Open STL files from your system</li>
    <li>Recent files menu for quick access</li>
    <li>Save G-code output to your preferred location</li>
    <li>Export/import settings profiles</li>
    <li>Drag and drop support</li>
</ul>

<h3>3D Visualization</h3>
<ul>
    <li>Interactive 3D model viewing with rotation, pan, and zoom</li>
    <li>Multiple view angles and perspective options</li>
    <li>Toggle between solid and wireframe views</li>
    <li>Measure distances between points</li>
    <li>High DPI display support</li>
</ul>

<h3>G-code Tools</h3>
<ul>
    <li>Built-in G-code viewer with syntax highlighting</li>
    <li>Line numbers and current line indicator</li>
    <li>Search functionality within G-code</li>
    <li>G-code validation and simulation</li>
    <li>Support for different printer firmwares</li>
</ul>

<h3>Documentation & Help</h3>
<ul>
    <li>Press F1 or go to Help > Documentation for detailed guides</li>
    <li>Built-in markdown documentation viewer</li>
    <li>Context-sensitive help</li>
    <li>Automatic update checking</li>
</ul>

<h3>Advanced Features</h3>
<ul>
    <li>Comprehensive logging system</li>
    <li>Log viewer with filtering by log level</li>
    <li>Customizable keyboard shortcuts</li>
    <li>Plugin system for extending functionality</li>
    <li>Multi-language support</li>
</ul>

<h2>Keyboard Shortcuts</h2>
<ul>
    <li><b>Ctrl+O</b>: Open STL file</li>
    <li><b>Ctrl+S</b>: Save G-code</li>
    <li><b>F1</b>: Show help/documentation</li>
    <li><b>Ctrl+Q</b>: Quit application</li>
    <li><b>Ctrl+L</b>: Toggle log viewer</li>
    <li><b>Ctrl+G</b>: Show G-code viewer</li>
</ul>

<h2>Support</h2>
<p>For help and support, please visit our GitHub repository or join our Discord community.</p>
"""

class HelpDialog(QDialog):
    """
    Dialog window for displaying help documentation using PyQt6.
    
    Creates a modal dialog window that shows the application's help content
    in a scrollable text widget with proper formatting.
    """
    def __init__(self, parent=None):
        """
        Initialize the help dialog window.
        
        Args:
            parent: The parent QWidget window
        """
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("STL to GCode Converter - Help")
        self.resize(900, 700)
        
        # Set window modality
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Create text edit for help content
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(HELP_CONTENT)
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
        
        # Create buttons layout
        buttons_layout = QHBoxLayout()
        
        # Documentation button
        docs_btn = QPushButton("Open Documentation")
        docs_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/Nsfr750/STL_to_G-Code/tree/main/docs")
        )
        buttons_layout.addWidget(docs_btn)
        
        # Discord button
        discord_btn = QPushButton("Join Discord")
        discord_btn.clicked.connect(
            lambda: webbrowser.open("https://discord.gg/BvvkUEP9")
        )
        buttons_layout.addWidget(discord_btn)
        
        # GitHub button
        github_btn = QPushButton("View on GitHub")
        github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/Nsfr750/STL_to_G-Code")
        )
        buttons_layout.addWidget(github_btn)
        
        # Add stretch to push buttons to the right
        buttons_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        # Add buttons layout to main layout
        layout.addLayout(buttons_layout)


def show_help(parent=None):
    """
    Show the help dialog.
    
    Args:
        parent: The parent QWidget window
    """
    dialog = HelpDialog(parent)
    dialog.exec()


# For testing
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    show_help()
    sys.exit(app.exec())
