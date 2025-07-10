"""
G-code Viewer using PyQt6

This module provides a G-code viewer with syntax highlighting, line numbers,
and search functionality.
"""
import os
import re
import logging
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
    """Custom text editor with line numbers and syntax highlighting."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 10))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: none;
            }
        """)
        
        # Line number area
        self.lineNumberArea = LineNumberArea(self)
        
        # Update the line number area when the text changes
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        
        # Set the viewport margins to make room for the line number area
        self.updateLineNumberAreaWidth(0)
    
    def lineNumberAreaWidth(self):
        """Calculate the width of the line number area."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1
        
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def updateLineNumberAreaWidth(self, newBlockCount=0):
        """Update the viewport margins to make room for the line number area."""
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    
    def updateLineNumberArea(self, rect=None, dy=0):
        """Update the line number area."""
        if rect is not None and dy != 0:
            self.lineNumberArea.scroll(0, dy)
        elif rect is not None and hasattr(rect, 'y'):
            # Only call rect.y() if rect is a QRectF/QRegion object
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        elif rect is not None and isinstance(rect, int):
            # If rect is an integer (like when called from QPlainTextEdit.updateRequest)
            self.lineNumberArea.update(0, rect, self.lineNumberArea.width(), self.viewport().height())
        else:
            # If rect is None or doesn't have y() method, update the entire line number area
            self.lineNumberArea.update()
        
        if rect is not None and hasattr(rect, 'contains') and rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()
    
    def resizeEvent(self, event):
        """Handle the resize event."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
    
    def lineNumberAreaPaintEvent(self, event):
        """Paint the line numbers in the line number area."""
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#2b2b2b"))
        
        # Set up the text format
        text_format = QTextCharFormat()
        text_format.setForeground(QColor("#808080"))
        
        # Get the first visible block
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        
        # Get the top position of the first visible block
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        # Draw the line numbers
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#808080"))
                painter.drawText(
                    0, int(top),
                    self.lineNumberArea.width() - 5, int(self.fontMetrics().height()),
                    int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                    number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

class GCodeViewer(QDialog):
    """G-code viewer dialog with syntax highlighting and search functionality."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("G-code Viewer")
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
        self.open_btn = QPushButton("Open G-code")
        self.open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(self.open_btn)
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)
        
        # Search
        toolbar.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in G-code...")
        self.search_edit.returnPressed.connect(self.search_text)
        toolbar.addWidget(self.search_edit)
        
        # Line number
        self.line_number_label = QLabel("Line: 0")
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
        self.logger = logging.getLogger("GCodeViewer")
    
    def open_file(self):
        """Open a G-code file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open G-code File",
            "",
            "G-code Files (*.gcode *.nc *.txt);;All Files (*)"
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
            QMessageBox.information(self, "Success", "File saved successfully.")
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
    
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
            QMessageBox.information(self, "Not Found", f"'{search_text}' not found.")
    
    def display_gcode(self, file_path):
        """Display G-code content in the viewer."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            self.current_file = file_path
            self.setWindowTitle(f"G-code Viewer - {os.path.basename(file_path)}")
            self.highlight_gcode(content)
            self.save_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error loading file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
    
    def highlight_gcode(self, content):
        """Apply syntax highlighting to the G-code content."""
        # Clear existing content
        self.editor.clear()
        
        # Set the content
        self.editor.setPlainText(content)
        
        # Define text formats
        gcode_format = QTextCharFormat()
        gcode_format.setForeground(QColor("#4FC1FF"))  # Light blue for G-codes
        
        mcode_format = QTextCharFormat()
        mcode_format.setForeground(QColor("#FF79C6"))  # Pink for M-codes
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green for comments
        comment_format.setFontItalic(True)
        
        # Apply highlighting
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Highlight G-codes (G followed by numbers)
        self._highlight_pattern(r'\bG\d+\b', gcode_format, cursor)
        
        # Highlight M-codes (M followed by numbers)
        self._highlight_pattern(r'\bM\d+\b', mcode_format, cursor)
        
        # Highlight comments (semicolon to end of line or parentheses)
        self._highlight_pattern(r';\([^)]*\)|;.*$', comment_format, cursor, True)
    
    def _highlight_pattern(self, pattern, format, cursor, is_regex=False):
        """Helper method to highlight text matching a pattern."""
        cursor.beginEditBlock()
        
        if is_regex:
            regex = re.compile(pattern, re.MULTILINE)
            text = self.editor.toPlainText()
            
            for match in regex.finditer(text):
                start = match.start()
                length = match.end() - start
                
                cursor.setPosition(start)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor,
                    length
                )
                cursor.mergeCharFormat(format)
        else:
            # Simple text search
            cursor.setPosition(0)
            while True:
                cursor = self.editor.document().find(pattern, cursor)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(format)
        
        cursor.endEditBlock()
    
    def update_line_number(self):
        """Update the current line number display."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        self.line_number_label.setText(f"Line: {line}")

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
