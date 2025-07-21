"""
About dialog module for the STL to GCode Converter application.

This module provides the About dialog window that displays application information,
version details, and copyright notice using PyQt6.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QTextBrowser, QApplication)
from PyQt6.QtCore import Qt, QSize, QUrl, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt6.QtGui import QPixmap, QIcon, QDesktopServices, QFont
import os
import sys
import platform
from pathlib import Path
from .version import get_version  # Updated import to use relative import
import logging
from scripts.logger import get_logger
logger = get_logger(__name__)

# Check if OpenGL is available
OPENGL_AVAILABLE = False
try:
    from PyQt6.QtOpenGL import QOpenGLWidget  # noqa: F401
    OPENGL_AVAILABLE = True
except ImportError:
    pass

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
        
        # PyQt6 version information
        pyqt_version = f"PyQt6 version: {PYQT_VERSION_STR}"
        pyqt_label = QLabel(pyqt_version)
        pyqt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Qt version information
        qt_version = f"Qt version: {QT_VERSION_STR}"
        qt_label = QLabel(qt_version)
        qt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # System info
        sys_info = QTextBrowser()
        sys_info.setOpenLinks(True)
        sys_info.setHtml(About.get_system_info())
        sys_info.setMaximumHeight(250)
        layout.addWidget(QLabel("<b>System Information:</b>"))
        layout.addWidget(sys_info)
                
        # GitHub button
        github_btn = QPushButton("GitHub")
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b579a;  /* Blue color */
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1e4b8b;  /* Darker blue on hover */
            }
            QPushButton:pressed {
                background-color: #173f75;  /* Even darker when pressed */
            }
        """)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/Nsfr750/STL_to_G-Code")))

        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addSpacing(10)
        layout.addWidget(description)
        layout.addSpacing(10)
        layout.addWidget(copyright)
        
        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        
        # Add GitHub button with stretch on the left
        button_layout.addStretch()
        button_layout.addWidget(github_btn)
        
        # Add OK button with some spacing
        button_layout.addSpacing(10)  # Add some space between buttons
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        button_layout.addStretch()  # Add stretch on the right
        
        # Add the button layout to the main layout
        layout.addSpacing(10)
        layout.addLayout(button_layout)
        
        # Set dialog properties
        dialog.setLayout(layout)
        dialog.setWindowTitle("About STL to GCode Converter")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.exec()

    @staticmethod
    def get_system_info():
        """Get system information for the about dialog."""
        try:
            # Get PyQt version
            python_version = sys.version.split(' ')[0]
            
            # Get operating system information
            os_info = f"{platform.system()} {platform.release()} {platform.version()}"
            
            # Get screen resolution
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            resolution = f"{screen_geometry.width()}x{screen_geometry.height()}"

            # Get CPU information
            cpu_info = ""
            try:
                if hasattr(platform, 'processor'):
                    cpu_info = platform.processor() or "Not available"
                else:
                    cpu_info = "Not available"
                
                # Get CPU cores using os.cpu_count() which is more reliable
                cpu_cores = os.cpu_count() or "Not available"
            except Exception as e:
                logger.warning(f"Error getting CPU info: {e}")
                cpu_info = "Error getting CPU info"
                cpu_cores = "Error"
            
            # Get memory information
            memory_info = ""
            try:
                import psutil
                memory = psutil.virtual_memory()
                total_memory = memory.total / (1024 ** 3)  # Convert to GB
                available_memory = memory.available / (1024 ** 3)
                memory_info = f"{available_memory:.1f} GB available of {total_memory:.1f} GB"
            except ImportError:
                memory_info = "psutil not available"
            except Exception as e:
                logger.warning(f"Error getting memory info: {e}")
                memory_info = "Error getting memory info"
            
            # Format the information as HTML
            info = f"""
            <html>
            <body>
            <table>
            <tr><td><b>Operating System:</b></td><td>{os_info}</td></tr>
            <tr><td><b>Python Version:</b></td><td>{python_version}</td></tr>
            <tr><td><b>Qt Version:</b></td><td>{QT_VERSION_STR}</td></tr>
            <tr><td><b>PyQt Version:</b></td><td>{PYQT_VERSION_STR}</td></tr>
            <tr><td><b>Screen Resolution:</b></td><td>{resolution}</td></tr>
            <tr><td><b>CPU:</b></td><td>{cpu_info}</td></tr>
            <tr><td><b>CPU Cores:</b></td><td>{cpu_cores}</td></tr>
            <tr><td><b>Memory:</b></td><td>{memory_info}</td></tr>
            </table>
            </body>
            </html>
            """
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return f"<p>Error getting system information: {str(e)}</p>"