"""
Log viewer module for the STL to GCode Converter.

This module provides a dockable log viewer with filtering capabilities.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QDockWidget, QTextEdit, QComboBox, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QPushButton, QApplication, QTextBrowser, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont

class LogViewer(QDockWidget):
    """
    A dockable log viewer widget that displays log messages with filtering by log level.
    """
    def __init__(self, parent=None):
        """Initialize the log viewer."""
        super().__init__("Log Viewer", parent)
        self.setObjectName("LogViewer")
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | 
                           Qt.DockWidgetArea.LeftDockWidgetArea |
                           Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Main widget and layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(2, 2, 2, 2)
        geometry = self.geometry()
        geometry.setWidth(500)
        geometry.setHeight(400)
        self.setGeometry(geometry)
        
        # Log level filter
        self.filter_layout = QHBoxLayout()
        self.filter_label = QLabel("Log Level:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.filter_combo.setCurrentText("INFO")
        self.filter_combo.currentTextChanged.connect(self.filter_logs)
        
        # Clear button
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        
        # Add widgets to filter layout
        self.filter_layout.addWidget(self.filter_label)
        self.filter_layout.addWidget(self.filter_combo)
        self.filter_layout.addStretch()
        self.filter_layout.addWidget(self.clear_button)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Add widgets to main layout
        self.layout.addLayout(self.filter_layout)
        self.layout.addWidget(self.log_display)
        
        self.setWidget(self.main_widget)
        
        # Set up log level colors
        self.log_colors = {
            'DEBUG': QColor('#888888'),
            'INFO': QColor('#ffffff'),
            'WARNING': QColor('#ffcc00'),
            'ERROR': QColor('#ff6b6b'),
            'CRITICAL': QColor('#ff0000')
        }
        
        # Set up log file monitoring
        self.log_file = Path(__file__).parent.parent / 'stl_to_gcode.log'
        self.last_position = 0
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log_display)
        self.log_timer.start(1000)  # Update every second
        
        # Load existing log content
        self.update_log_display()
    
    def update_log_display(self):
        """Update the log display with new log entries."""
        try:
            if not self.log_file.exists():
                return
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()
                
                if new_content:
                    cursor = self.log_display.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    
                    # Process each line to apply formatting
                    for line in new_content.splitlines():
                        log_level = self._detect_log_level(line)
                        if log_level and log_level in self.log_colors:
                            self._append_log_line(line, log_level)
                    
                    # Auto-scroll to bottom
                    self.log_display.verticalScrollBar().setValue(
                        self.log_display.verticalScrollBar().maximum()
                    )
        except Exception as e:
            print(f"Error updating log display: {e}")
    
    def _detect_log_level(self, line):
        """Detect the log level from a log line."""
        line = line.upper()
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            if f" - {level} - " in line:
                return level
        return 'INFO'
    
    def _append_log_line(self, line, log_level):
        """Append a log line with appropriate formatting."""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Get the selected filter level
        selected_level = self.filter_combo.currentText().upper()
        level_order = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Show all logs if ALL is selected, otherwise filter by level
        if selected_level == 'ALL' or level_order.index(log_level) >= level_order.index(selected_level):
            # Apply color based on log level
            format = QTextCharFormat()
            format.setForeground(self.log_colors.get(log_level, QColor('#ffffff')))
            
            # Make critical errors bold
            if log_level == 'CRITICAL':
                font = format.font()
                font.setBold(True)
                format.setFont(font)
            
            cursor.insertText(f"{line}\n", format)
    
    def filter_logs(self):
        """Filter the log display based on the selected log level."""
        # Save current scroll position
        scrollbar = self.log_display.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()
        
        # Get the current content
        current_text = self.log_display.toPlainText()
        self.log_display.clear()
        
        # Get the selected filter level
        selected_level = self.filter_combo.currentText().upper()
        level_order = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Process each line
        cursor = self.log_display.textCursor()
        for line in current_text.splitlines():
            log_level = self._detect_log_level(line)
            if log_level and (selected_level == 'ALL' or level_order.index(log_level) >= level_order.index(selected_level)):
                self._append_log_line(line, log_level)
        
        # Restore scroll position
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(min(scrollbar.value(), scrollbar.maximum()))
    
    def clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
        self.last_position = 0
        
        # Clear the log file
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('')
            self.last_position = 0
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not clear log file: {e}")


class LogHandler(logging.Handler):
    """Custom logging handler that forwards log messages to the log viewer."""
    def __init__(self, log_viewer):
        super().__init__()
        self.log_viewer = log_viewer
    
    def emit(self, record):
        """Emit a log record to the log viewer."""
        try:
            msg = self.format(record)
            self.log_viewer._append_log_line(msg, record.levelname)
        except Exception:
            self.handleError(record)


def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


# For testing
if __name__ == "__main__":
    import sys
    
    # Set up logging
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show log viewer
    log_viewer = LogViewer()
    log_viewer.show()
    
    # Add a custom handler to forward logs to the viewer
    logger = logging.getLogger()
    handler = LogHandler(log_viewer)
    handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    logger.addHandler(handler)
    
    # Log some test messages
    logging.debug("This is a debug message")
    logging.info("This is an info message")
    logging.warning("This is a warning message")
    logging.error("This is an error message")
    logging.critical("This is a critical message")
    
    sys.exit(app.exec())
