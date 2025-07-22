"""
Sponsor dialog for the Image Deduplicator application.

This module provides the SponsorDialog class which displays options for supporting
the development of the application through donations and sponsorships.
"""

import logging
import os
import sys
import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt, QUrl, QSize, QBuffer, QTimer
from PyQt6.QtGui import (QDesktopServices, QPixmap, QPalette, QColor, QIcon, 
                         QImage, QGuiApplication)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, 
    QTextBrowser, QWidget, QSizePolicy, QApplication, QGridLayout,
    QMessageBox, QScrollArea, QFrame
)

# Import translation utilities
try:
    from .language_manager import LanguageManager
except ImportError:
    # Fallback for direct script execution
    LanguageManager = type('LanguageManager', (), {'language_changed': None})

# Configure logging
logger = logging.getLogger(__name__)

# Constants for donation addresses
MONERO_ADDRESS = "47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF"
BITCOIN_ADDRESS = "bc1q8x7v0j8x3q3q3q3q3q3q3q3q3q3q3q3q3q3q3"

class SponsorDialog(QDialog):
    """
    A dialog that displays options for supporting the application's development.
    
    This includes links to GitHub Sponsors, PayPal donations, and cryptocurrency
    donation addresses with QR codes for easy scanning.
    """
    
    def __init__(self, parent=None, language_manager: Optional[LanguageManager] = None):
        """
        Initialize the sponsor dialog.
        
        Args:
            parent: Parent widget
            language_manager: LanguageManager instance for translations
        """
        super().__init__(parent)
        self.setWindowTitle(self.translate("support_title"))
        self.setMinimumSize(600, 700)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Initialize language manager
        self.lang_manager = language_manager or LanguageManager()
        
        # Connect language changed signal
        if hasattr(self.lang_manager, 'language_changed'):
            self.lang_manager.language_changed.connect(self.retranslate_ui)
        
        # Store QR code images
        self.qr_images = {}
        
        # Set up the UI
        self.setup_ui()
        
        # Apply initial translations
        self.retranslate_ui()
        
        # Set window icon if available
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Get a translated string for the given key.
        
        Args:
            key: Translation key
            **kwargs: Format arguments for the translation string
            
        Returns:
            str: Translated string or the key if not found
        """
        if hasattr(self, "lang_manager") and self.lang_manager:
            return self.lang_manager.translate(key, **kwargs)
        return key
    
    def retranslate_ui(self) -> None:
        """Update all UI elements with translated text."""
        # Window title
        self.setWindowTitle(self.translate("support_title"))
        
        # Main title
        if hasattr(self, "title_label"):
            self.title_label.setText(self.translate("support_project_header"))
        
        # Description
        if hasattr(self, "description_label"):
            self.description_label.setText(
                self.translate("support_project_description")
            )
        
        # Section headers
        if hasattr(self, "github_section_label"):
            self.github_section_label.setText(
                f"<h3>{self.translate('ways_to_support')}</h3>"
            )
        
        if hasattr(self, "crypto_section_label"):
            self.crypto_section_label.setText(
                f"<h3>{self.translate('monero')}</h3>"
            )
        
        # Buttons
        if hasattr(self, "github_btn"):
            self.github_btn.setText(self.translate("github_sponsors"))
        
        if hasattr(self, "paypal_btn"):
            self.paypal_btn.setText(self.translate("paypal_donation"))
        
        if hasattr(self, "close_btn"):
            self.close_btn.setText(self.translate("close"))
        
        # Crypto addresses
        if hasattr(self, "monero_label"):
            self.monero_label.setText(
                f"<b>{self.translate('monero')}:</b>"
            )
        
        if hasattr(self, "bitcoin_label"):
            self.bitcoin_label.setText(
                f"<b>{self.translate('bitcoin')}:</b>"
            )
        
        # Copy buttons
        if hasattr(self, "copy_monero_btn"):
            self.copy_monero_btn.setText(self.translate("copy_address"))
        
        if hasattr(self, "copy_bitcoin_btn"):
            self.copy_bitcoin_btn.setText(self.translate("copy_address"))
    
    def setup_ui(self):
        """Initialize the user interface components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Scroll area to handle small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget for scroll area
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(5, 5, 15, 5)  # Right margin for scrollbar
        
        # Title
        self.title_label = QLabel(self.translate("support_project_header"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Description
        self.description_label = QLabel(self.translate("support_project_description"))
        self.description_label.setWordWrap(True)
        self.description_label.setOpenExternalLinks(True)
        self.description_label.setTextFormat(Qt.TextFormat.RichText)
        self.description_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        layout.addWidget(self.description_label)
        
        # GitHub Sponsors section
        self.github_section_label = QLabel(
            f"<h3>{self.translate('ways_to_support')}</h3>"
        )
        layout.addWidget(self.github_section_label)
        
        github_layout = QHBoxLayout()
        
        # GitHub Sponsors button
        self.github_btn = QPushButton(self.translate("github_sponsors"))
        self.github_btn.setIcon(QIcon.fromTheme("github"))
        self.github_btn.setIconSize(QSize(24, 24))
        self.github_btn.setMinimumHeight(40)
        self.github_btn.clicked.connect(self.open_github_sponsors)
        github_layout.addWidget(self.github_btn)
        
        # PayPal button
        self.paypal_btn = QPushButton(self.translate("paypal_donation"))
        self.paypal_btn.setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), "..", "assets", "paypal.png"
        )))
        self.paypal_btn.setIconSize(QSize(24, 24))
        self.paypal_btn.setMinimumHeight(40)
        self.paypal_btn.clicked.connect(self.open_paypal)
        github_layout.addWidget(self.paypal_btn)
        
        layout.addLayout(github_layout)
        
        # Cryptocurrency section
        self.crypto_section_label = QLabel(
            f"<h3>{self.translate('monero')}</h3>"
        )
        layout.addWidget(self.crypto_section_label)
        
        # Cryptocurrency grid
        crypto_grid = QGridLayout()
        crypto_grid.setSpacing(15)
        
        # Monero
        row = 0
        self.monero_label = QLabel(f"<b>{self.translate('monero')}:</b>")
        crypto_grid.addWidget(self.monero_label, row, 0, 1, 2)
        
        # Monero address with copy button
        monero_address = QLabel(MONERO_ADDRESS)
        monero_address.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        monero_address.setStyleSheet(
            "font-family: monospace; background-color: #f0f0f0; "
            "padding: 5px; border-radius: 4px;"
        )
        crypto_grid.addWidget(monero_address, row, 2)
        
        self.copy_monero_btn = QPushButton(self.translate("copy_address"))
        self.copy_monero_btn.clicked.connect(
            lambda: self.copy_to_clipboard(MONERO_ADDRESS)
        )
        crypto_grid.addWidget(self.copy_monero_btn, row, 3)
        
        # Monero QR code
        row += 1
        monero_qr = self.generate_qr_code(MONERO_ADDRESS, "monero")
        if monero_qr:
            crypto_grid.addWidget(monero_qr, row, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        # Bitcoin
        row += 1
        self.bitcoin_label = QLabel(f"<b>{self.translate('bitcoin')}:</b>")
        crypto_grid.addWidget(self.bitcoin_label, row, 0, 1, 2)
        
        # Bitcoin address with copy button
        bitcoin_address = QLabel(BITCOIN_ADDRESS)
        bitcoin_address.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        bitcoin_address.setStyleSheet(
            "font-family: monospace; background-color: #f0f0f0; "
            "padding: 5px; border-radius: 4px;"
        )
        crypto_grid.addWidget(bitcoin_address, row, 2)
        
        self.copy_bitcoin_btn = QPushButton(self.translate("copy_address"))
        self.copy_bitcoin_btn.clicked.connect(
            lambda: self.copy_to_clipboard(BITCOIN_ADDRESS)
        )
        crypto_grid.addWidget(self.copy_bitcoin_btn, row, 3)
        
        # Bitcoin QR code
        row += 1
        bitcoin_qr = self.generate_qr_code(BITCOIN_ADDRESS, "bitcoin")
        if bitcoin_qr:
            crypto_grid.addWidget(bitcoin_qr, row, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(crypto_grid)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton(self.translate("close"))
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Set up scroll area
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def generate_qr_code(self, data: str, name: str) -> Optional[QLabel]:
        """
        Generate a QR code for the given data.
        
        Args:
            data: Data to encode in the QR code
            name: Name for the QR code (used for caching)
            
        Returns:
            QLabel containing the QR code image, or None on error
        """
        try:
            # Check if we already generated this QR code
            if name in self.qr_images:
                return self.qr_images[name]
                
            import qrcode
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to QPixmap
            buffer = QBuffer()
            qr_img.save(buffer, format="PNG")
            qpixmap = QPixmap()
            qpixmap.loadFromData(buffer.data(), "PNG")
            
            # Create label with QR code
            qr_label = QLabel()
            qr_label.setPixmap(qpixmap)
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_label.setStyleSheet("background-color: white; padding: 10px;")
            
            # Cache the QR code
            self.qr_images[name] = qr_label
            return qr_label
            
        except ImportError:
            logger.warning("qrcode module not available, QR codes will not be displayed")
            return None
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def copy_to_clipboard(self, text: str) -> None:
        """
        Copy text to clipboard and show a confirmation message.
        
        Args:
            text: Text to copy to clipboard
        """
        try:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            
            # Show tooltip at cursor position
            QToolTip.showText(
                QCursor.pos(), 
                self.translate("address_copied"),
                msecShowTime=2000
            )
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
    
    def open_github_sponsors(self) -> None:
        """Open GitHub Sponsors page in the default web browser."""
        try:
            QDesktopServices.openUrl(QUrl("https://github.com/sponsors/Nsfr750"))
        except Exception as e:
            logger.error(f"Error opening GitHub Sponsors: {e}")
            QMessageBox.critical(
                self,
                self.translate("error_title"),
                self.translate("browser_error", url="GitHub Sponsors")
            )
    
    def open_paypal(self) -> None:
        """Open PayPal donation page in the default web browser."""
        try:
            QDesktopServices.openUrl(QUrl("https://paypal.me/3dmega"))
        except Exception as e:
            logger.error(f"Error opening PayPal: {e}")
            QMessageBox.critical(
                self,
                self.translate("error_title"),
                self.translate("browser_error", url="PayPal")
            )


if __name__ == "__main__":
    # For testing the dialog standalone
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Set up basic logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show the dialog
    dialog = SponsorDialog()
    dialog.show()
    
    # Run the event loop
    sys.exit(app.exec())
