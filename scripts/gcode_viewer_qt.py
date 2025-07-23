"""
G-code Viewer using PyQt6

This module provides a G-code viewer with syntax highlighting, line numbers,
and search functionality.
"""
import os
import re
import logging
from scripts.logger import get_logger
from scripts.translations import get_language_manager
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QPlainTextEdit, QPushButton, QLabel, QFileDialog, QMessageBox, 
    QLineEdit, QFrame, QScrollArea, QDialog, QApplication, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor, QFont, QTextFormat, QPainter

class LineNumberArea(QFrame):
    """Widget to display line numbers for the text editor."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(40)
        self.setStyleSheet("background-color: #2b2b2b; color: #808080;")
        
    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)
    
    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    """Custom text editor with syntax highlighting for G-code."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_manager = get_language_manager()
        self.translate = self.language_manager.translate
        
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 10))
        
        # Imposta lo stile con sfondo scuro e testo chiaro
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #252526;
                width: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Imposta i margini
        self.setViewportMargins(10, 5, 5, 5)
        
        # Abilita il wrapping del testo
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Nascondi la barra di scorrimento orizzontale
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Imposta il colore di selezione
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#264F78"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        # Rimuovi il numero di riga
        self.line_number_area = None
        
    def setPlainText(self, text):
        """Override per assicurarsi che il testo venga formattato correttamente."""
        super().setPlainText(text)
        
        # Opzionale: evidenzia la sintassi G-code
        self.highlight_gcode()
    
    def highlight_gcode(self):
        """Evidenzia la sintassi G-code."""
        cursor = self.textCursor()
        format_normal = QTextCharFormat()
        format_normal.setForeground(QColor("#e0e0e0"))
        
        # Applica la formattazione a tutto il testo
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(format_normal)
        
        # Opzionale: aggiungi qui la logica per evidenziare comandi G-code specifici
        # es. G0, G1, M104, ecc.
        
        self.setTextCursor(cursor)
        
    def resizeEvent(self, event):
        """Override del resize event per gestire il ridimensionamento."""
        super().resizeEvent(event)
        # Aggiorna l'area del numero di riga se necessario
        if self.line_number_area is not None:
            self.line_number_area.setGeometry(0, 0, 0, 0)

class GCodeViewer(QDialog):
    """G-code viewer dialog with syntax highlighting and search functionality."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_manager = get_language_manager()
        self.translate = self.language_manager.translate
        
        self.setWindowTitle(self.translate("gcode_viewer.title"))
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QPushButton {
                background-color: #424242;
                color: white;
                padding: 5px 10px;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #555;
                background-color: #333;
                color: white;
            }
            QLabel {
                color: white;
                padding: 5px;
            }
        """)
        
        self.current_file = None
        self.setup_ui()
        self.setup_logging()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Open button
        self.open_btn = QPushButton(self.translate("gcode_viewer.buttons.open"))
        self.open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(self.open_btn)
        
        # Save button
        self.save_btn = QPushButton(self.translate("gcode_viewer.buttons.save"))
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)
        
        # Search
        toolbar.addWidget(QLabel(self.translate("gcode_viewer.search.placeholder").replace("...", "")))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.translate("gcode_viewer.search.placeholder"))
        self.search_edit.returnPressed.connect(self.search_text)
        toolbar.addWidget(self.search_edit)
        
        # Line number
        self.line_number_label = QLabel(self.translate("gcode_viewer.line_number", number=0))
        toolbar.addWidget(self.line_number_label)
        
        # Add stretch to push elements to the left
        toolbar.addStretch()
        
        main_layout.addLayout(toolbar)
        
        # Editor
        self.editor = CodeEditor()
        self.editor.cursorPositionChanged.connect(self.update_line_number)
        main_layout.addWidget(self.editor)
    
    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = get_logger("GCodeViewer")
    
    def open_file(self):
        """Open a G-code file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.translate("gcode_viewer.file_dialog.open_title"),
            "",
            self.translate("gcode_viewer.file_dialog.filter")
        )
        
        if file_name:
            self.display_gcode(file_name)
    
    def save_file(self):
        """Save the current G-code content."""
        if not self.current_file:
            return
            
        try:
            with open(self.current_file, 'w') as f:
                f.write(self.editor.toPlainText())
            QMessageBox.information(
                self, 
                self.translate("gcode_viewer.messages.success"),
                self.translate("gcode_viewer.messages.file_saved")
            )
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            QMessageBox.critical(
                self, 
                self.translate("gcode_viewer.messages.error"),
                self.translate("gcode_viewer.messages.save_error", error=str(e))
            )
    
    def search_text(self):
        """Search for text in the G-code."""
        search_text = self.search_edit.text()
        if not search_text:
            return
        
        # Clear previous highlights
        cursor = self.editor.textCursor()
        cursor.setPosition(0)
        
        # Search forward from current position
        flags = QTextDocument.FindFlag(0)
        found = self.editor.find(search_text, flags)
        
        if not found:
            QMessageBox.information(
                self, 
                self.translate("gcode_viewer.search.not_found_title"),
                self.translate("gcode_viewer.search.not_found", text=search_text)
            )
    
    def display_gcode(self, file_path):
        """Display G-code content in the viewer."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            self.current_file = file_path
            self.setWindowTitle(self.translate("gcode_viewer.title_with_file", filename=os.path.basename(file_path)))
            self.editor.setPlainText(content)
            self.save_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error loading file: {e}")
            QMessageBox.critical(
                self, 
                self.translate("gcode_viewer.messages.error"),
                self.translate("gcode_viewer.messages.load_error", error=str(e))
            )
    
    def update_line_number(self):
        """Update the current line number display."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        self.line_number_label.setText(self.translate("gcode_viewer.line_number", number=line))

# For testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle("Fusion")
    
    viewer = GCodeViewer()
    viewer.show()
    
    # If a file was provided as a command-line argument, open it
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        viewer.display_gcode(sys.argv[1])
    
    sys.exit(app.exec())
