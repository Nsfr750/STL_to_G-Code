"""
About dialog module for the STL to GCode Converter application.

This module provides the About dialog window that displays application information,
version details, and copyright notice using PyQt6.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                            QHBoxLayout, QApplication, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .version import get_version  # Updated import to use relative import

class About:
    """
    Static class for managing the About dialog window.
    
    Provides a method to display the About dialog with application information.
    """
    @staticmethod
    def show_about(parent=None):
        """
        Display the About dialog.
        
        Args:
            parent: The parent widget for the dialog.
        """
        dialog = QDialog(parent)
        dialog.setWindowTitle("About STL to GCode Converter")
        dialog.setMinimumWidth(400)
        
        # Create main layout
        layout = QVBoxLayout(dialog)
        
        # Application title
        title = QLabel("STL to GCode Converter")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Version information
        version = QLabel(f"Version: {get_version()}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Copyright information
        copyright = QLabel("© 2025 Nsfr750. All rights reserved.")
        copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Description
        description = QLabel(
            "A tool to convert STL 3D model files to GCode for 3D printing."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addSpacing(10)
        layout.addWidget(description)
        layout.addSpacing(10)
        layout.addWidget(copyright)
        
        # Add OK button
        button_box = QHBoxLayout()
        button_box.addStretch()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_box.addWidget(ok_button)
        button_box.addStretch()
        
        layout.addLayout(button_box)
        
        # Set dialog properties
        dialog.setLayout(layout)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.exec()
