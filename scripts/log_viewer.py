"""
Log viewer module for the STL to GCode Converter.

This module provides a dockable log viewer with filtering capabilities.
"""
import logging
from scripts.logger import get_logger
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
        
        # Top bar with controls
        self.top_bar = QHBoxLayout()
        
        # Log file selector
        self.log_file_label = QLabel("Log File:")
        self.log_file_combo = QComboBox()
        self.log_file_combo.setMinimumWidth(300)
        self.log_file_combo.currentTextChanged.connect(self.change_log_file)
        
        # Log level filter
        self.filter_label = QLabel("Log Level:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.filter_combo.setCurrentText("INFO")
        self.filter_combo.currentTextChanged.connect(self.filter_logs)
        
        # Clear button
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        
        # Add widgets to top bar
        self.top_bar.addWidget(self.log_file_label)
        self.top_bar.addWidget(self.log_file_combo)
        self.top_bar.addWidget(self.filter_label)
        self.top_bar.addWidget(self.filter_combo)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.clear_button)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Add widgets to main layout
        self.layout.addLayout(self.top_bar)
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
        self.logs_dir = Path(__file__).parent.parent / 'logs'
        self.log_file = None
        self.last_position = 0
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log_display)
        self.log_timer.start(1000)  # Update every second
        
        # Initialize log files list and select the most recent one
        self.init_log_files()
    
    def init_log_files(self):
        """Initialize the list of log files and select the most recent one."""
        try:
            # Create logs directory if it doesn't exist
            self.logs_dir.mkdir(exist_ok=True)
            
            # Get all log files
            log_files = list(self.logs_dir.glob('stl_to_gcode_*.log'))
            
            # Sort by modification time (newest first)
            log_files.sort(key=os.path.getmtime, reverse=True)
            
            # Add to combo box
            self.log_file_combo.clear()
            for log_file in log_files:
                self.log_file_combo.addItem(log_file.name, str(log_file))
            
            # Select the most recent log file
            if log_files:
                self.change_log_file(log_files[0].name)
            
        except Exception as e:
            print(f"Error initializing log files: {e}")
    
    def change_log_file(self, file_name):
        """Change the currently displayed log file."""
        if not file_name:
            return
            
        try:
            file_path = self.logs_dir / file_name
            if file_path.exists():
                self.log_file = file_path
                self.last_position = 0
                self.log_display.clear()
                self.update_log_display()
        except Exception as e:
            print(f"Error changing log file: {e}")
    
    def update_log_display(self):
        """Update the log display with new log entries."""
        if not self.log_file or not self.log_file.exists():
            return
            
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
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
        if not self.log_file:
            return
            
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
        """Clear the current log file."""
        if not self.log_file:
            return
            
        reply = QMessageBox.question(
            self, 
            'Clear Logs',
            f'Are you sure you want to clear {self.log_file.name}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write('')
                self.log_display.clear()
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


# For testing
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # Create and show the log viewer
    log_viewer = LogViewer()
    log_viewer.show()
    
    # Add some test log messages
    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(LogHandler(log_viewer))
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    sys.exit(app.exec())
