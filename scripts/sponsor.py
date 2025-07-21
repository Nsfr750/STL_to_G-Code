"""
Sponsor dialog module for the STL to GCode Converter.

This module provides a dialog window with sponsorship options,
allowing users to support the project through various platforms using PyQt6.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
import webbrowser
import os
from pathlib import Path
from scripts.logger import get_logger

class Sponsor:
    """
    Sponsor dialog class for displaying sponsorship options.
    
    Provides a modal dialog window with buttons linking to various
    sponsorship platforms (GitHub Sponsors, Discord, Patreon, etc.).
    """
    def __init__(self, parent=None):
        """
        Initialize the sponsor dialog.
        
        Args:
            parent: The parent QWidget window
        """
        self.parent = parent

    def show_sponsor(self):
        """Show the sponsor dialog."""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Support the Project")
        dialog.setMinimumWidth(400)
        
        # Set window modality
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Create main layout
        layout = QVBoxLayout(dialog)
        
        # Add title
        title = QLabel("Support STL to GCode Converter")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        
        # Add description
        description = QLabel(
            "This project is developed and maintained in my free time. "
            "If you find it useful, please consider supporting its development "
            "through one of the following platforms:"
        )
        description.setWordWrap(True)
        
        # Add sponsor buttons
        buttons_layout = QVBoxLayout()
        
        # GitHub Sponsors button
        github_btn = QPushButton("GitHub Sponsors")
        github_btn.setIcon(QIcon.fromTheme("github"))
        github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/sponsors/Nsfr750")
        )
        
        # Patreon button
        patreon_btn = QPushButton("Patreon")
        patreon_btn.setIcon(QIcon.fromTheme("patreon"))
        patreon_btn.clicked.connect(
            lambda: webbrowser.open("https://www.patreon.com/nsfr750")
        )
        
        # PayPal button
        paypal_btn = QPushButton("PayPal")
        paypal_btn.setIcon(QIcon.fromTheme("paypal"))
        paypal_btn.clicked.connect(
            lambda: webbrowser.open("https://paypal.me/3dmega")
        )
        
        # Add buttons to layout
        buttons_layout.addWidget(github_btn)
        buttons_layout.addWidget(patreon_btn)
        buttons_layout.addWidget(paypal_btn)
        
        # Add thank you message
        thanks = QLabel("Thank you for your support! ❤️")
        thanks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thanks_font = thanks.font()
        thanks_font.setItalic(True)
        thanks.setFont(thanks_font)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        
        # Add all widgets to main layout
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(description)
        layout.addSpacing(15)
        layout.addLayout(buttons_layout)
        layout.addSpacing(15)
        layout.addWidget(thanks)
        layout.addStretch()
        
        # Button container for close button
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_container)
        
        # Set dialog properties
        dialog.setLayout(layout)
        dialog.exec()

# For testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    sponsor = Sponsor()
    sponsor.show_sponsor()
    sys.exit(app.exec())
