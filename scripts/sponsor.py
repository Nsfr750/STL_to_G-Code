"""
Sponsor dialog for the Image Deduplicator application.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QTextBrowser,
    QWidget,
    QSizePolicy,
    QApplication,
    QGridLayout,
    QInputDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QUrl, QSize, QBuffer, QTimer
from PyQt6.QtGui import QDesktopServices, QPixmap, QPalette, QColor, QIcon, QImage

from scripts.language_manager import LanguageManager
from typing import Optional

import webbrowser
import os
import io
import qrcode
from wand.image import Image as WandImage


class SponsorDialog(QDialog):
    def __init__(self, parent=None, language_manager: Optional[LanguageManager] = None):
        super().__init__(parent)

        # Initialize language manager
        self.lang_manager = language_manager or LanguageManager()

        # Connect language changed signal
        if self.lang_manager:
            self.lang_manager.language_changed.connect(self.on_language_changed)

        self.setMinimumSize(500, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Initialize UI
        self.setup_ui()

        # Set initial translations
        self.retranslate_ui()

    def translate(self, key: str, **kwargs) -> str:
        """Helper method to get translated text."""
        if hasattr(self, "lang_manager") and self.lang_manager:
            return self.lang_manager.translate(key, **kwargs)
        return key  # Fallback to key if no translation available

    def on_language_changed(self, lang_code: str) -> None:
        """Handle language change."""
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Retranslate the UI elements."""
        self.setWindowTitle(self.translate("support_title"))

        if hasattr(self, "title_label"):
            self.title_label.setText(self.translate("support_project_header"))

        if hasattr(self, "message_label"):
            self.message_label.setText(self.translate("support_project_description"))

        if hasattr(self, "github_btn"):
            self.github_btn.setText(self.translate("github_sponsors"))
            self.github_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(
                    QUrl("https://github.com/sponsors/Nsfr750")
                )
            )

        if hasattr(self, "monero_label"):
            self.monero_label.setText(f"{self.translate('monero')}:")

        if hasattr(self, "close_btn"):
            self.close_btn.setText(self.translate("close"))

        if hasattr(self, "donate_btn"):
            self.donate_btn.setText(self.translate("paypal_donation"))

        if hasattr(self, "copy_monero_btn"):
            self.copy_monero_btn.setText(self.translate("copy_address"))

    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Set window title
        self.setWindowTitle(self.translate("support_title"))

        # Header
        self.title_label = QLabel(self.translate("support_project_header"))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Description
        self.message_label = QLabel(self.translate("support_project_description"))
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # Add some spacing
        layout.addSpacing(20)

        # Ways to support
        support_label = QLabel(f"<b>{self.translate('ways_to_support')}</b>")
        layout.addWidget(support_label)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # GitHub Sponsors button
        self.github_btn = QPushButton(self.translate("github_sponsors"))
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/sponsors/Nsfr750")))
        buttons_layout.addWidget(self.github_btn)

        # PayPal Donation button
        self.donate_btn = QPushButton(self.translate("paypal_donation"))
        self.donate_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://paypal.me/3dmega")))
        buttons_layout.addWidget(self.donate_btn)

        layout.addLayout(buttons_layout)

        # Add some spacing
        layout.addSpacing(20)

        # Monero donation
        self.monero_label = QLabel(f"<b>{self.translate('monero')}</b>")
        layout.addWidget(self.monero_label)

        # Monero address
        monero_address = "47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF"
        address_label = QLabel(monero_address)
        address_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(address_label)

        # Copy address button
        self.copy_monero_btn = QPushButton(self.translate("copy_address"))
        self.copy_monero_btn.clicked.connect(lambda: self.copy_to_clipboard(monero_address))
        layout.addWidget(self.copy_monero_btn)

        # Add some spacing
        layout.addSpacing(20)

        # Other ways to help
        other_ways = QLabel(f"<b>{self.translate('other_ways_to_help')}</b>")
        layout.addWidget(other_ways)

        help_list = QLabel(
            f"• {self.translate('star_on_github')} GitHub\n"
            f"• {self.translate('report_bugs')}\n"
            f"• {self.translate('share_with_others')}"
        )
        help_list.setWordWrap(True)
        layout.addWidget(help_list)

        # Close button
        self.close_btn = QPushButton(self.translate("close"))
        self.close_btn.clicked.connect(self.accept)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Set layout
        self.setLayout(layout)

        # Apply dark theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply dark theme to the dialog."""
        # Set dark palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(74, 156, 255))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(74, 156, 255))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        self.setPalette(dark_palette)

        # Set style sheet
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #f0f0f0;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #f0f0f0;
                border: 1px solid #555;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QTextBrowser {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                color: #f0f0f0;
            }
            a {
                color: #4a9cff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """
        )

    def copy_to_clipboard(self, text):
        """Copy text to clipboard and show feedback."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # Show feedback
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(self.translate("address_copied"))
        msg.setInformativeText(self.translate("address_copied_to_clipboard"))
        msg.setWindowTitle("")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
