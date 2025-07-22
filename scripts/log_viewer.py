"""
Log viewer module for the STL to GCode Converter.

This module provides a dockable log viewer with filtering capabilities.
"""
import logging
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QDockWidget, QTextEdit, QComboBox, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QPushButton, QApplication, QTextBrowser, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont, QPalette

from scripts.logger import get_logger
from scripts.translations import get_language_manager

class LogViewer(QDockWidget):
    """
    A dockable log viewer widget that displays log messages with filtering by log level.
    """
    def __init__(self, parent=None):
        """Initialize the log viewer."""
        self.language_manager = get_language_manager()
        self.translate = self.language_manager.translate
        
        super().__init__(self.translate("log_viewer.title"), parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setObjectName("LogViewer")
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Apply dark theme
        self.setStyleSheet("""
            QDockWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                titlebar-close-icon: url(close-light.png);
                titlebar-normal-icon: url(undock-light.png);
            }
            QDockWidget::title {
                text-align: left;
                padding: 3px;
                background-color: #2b2b2b;
            }
            QTextEdit, QTextBrowser {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
            QComboBox, QPushButton, QLabel {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 3px;
                min-width: 80px;
            }
            QComboBox:on, QPushButton:pressed {
                background-color: #4a4a4a;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #e0e0e0;
                selection-background-color: #4a4a4a;
            }
        """)
        
        # Main widget and layout
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0;")
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Set initial size
        geometry = self.geometry()
        geometry.setWidth(800)
        geometry.setHeight(400)
        self.setGeometry(geometry)
        
        # Top bar with controls
        self.top_bar = QHBoxLayout()
        self.top_bar.setSpacing(5)
        
        # Log file selector
        self.log_file_label = QLabel(self.translate("log_viewer.log_file_label"))
        self.log_file_combo = QComboBox()
        self.log_file_combo.setMinimumWidth(400)
        self.log_file_combo.currentTextChanged.connect(self.change_log_file)
        
        # Log level filter
        self.filter_label = QLabel(self.translate("log_viewer.labels.log_level"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            self.translate("log_viewer.levels.all"),
            self.translate("log_viewer.levels.debug"),
            self.translate("log_viewer.levels.info"),
            self.translate("log_viewer.levels.warning"),
            self.translate("log_viewer.levels.error"),
            self.translate("log_viewer.levels.critical")
        ])
        self.filter_combo.setCurrentText(self.translate("log_viewer.levels.info"))
        self.filter_combo.currentTextChanged.connect(self.filter_logs)
        
        # Clear button
        self.clear_button = QPushButton(self.translate("log_viewer.clear_button"))
        self.clear_button.clicked.connect(self.clear_logs)
        
        # Add widgets to top bar
        self.top_bar.addWidget(self.log_file_label)
        self.top_bar.addWidget(self.log_file_combo, 1)  # Add stretch factor
        self.top_bar.addWidget(self.filter_label)
        self.top_bar.addWidget(self.filter_combo)
        self.top_bar.addWidget(self.clear_button)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                padding: 5px;
            }
        """)
        
        # Add widgets to main layout
        self.layout.addLayout(self.top_bar)
        self.layout.addWidget(self.log_display)
        
        self.setWidget(self.main_widget)
        
        # Set up log level colors (brighter for dark theme)
        self.log_colors = {
            'DEBUG': QColor('#888888'),
            'INFO': QColor('#e0e0e0'),
            'WARNING': QColor('#ffcc66'),
            'ERROR': QColor('#ff6b6b'),
            'CRITICAL': QColor('#ff4444')
        }
        
        # Set up log file monitoring
        self.logs_dir = Path.cwd() / 'logs'
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
            
            # Get all log files (including rotated ones)
            log_files = list(self.logs_dir.glob('STL_To_GCode-*.log*'))
            
            # If no log files found, try the old pattern for backward compatibility
            if not log_files:
                log_files = list(self.logs_dir.glob('stl_to_gcode_*.log*'))
            
            # Sort by modification time (newest first)
            log_files.sort(key=os.path.getmtime, reverse=True)
            
            # Add to combo box
            self.log_file_combo.clear()
            for log_file in log_files:
                self.log_file_combo.addItem(log_file.name, str(log_file))
            
            # Select the most recent log file if available
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
        line_upper = line.upper()
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            if f" - {level} - " in line_upper:
                return level
        return 'INFO'  # Default to INFO if no level detected
    
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
            format.setForeground(self.log_colors.get(log_level, QColor('#e0e0e0')))
            
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
        scroll_bar = self.log_display.verticalScrollBar()
        was_at_bottom = scroll_bar.value() >= scroll_bar.maximum() - 10
        
        # Get all log content
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # Clear and re-add filtered content
            self.log_display.clear()
            for line in content.splitlines():
                log_level = self._detect_log_level(line)
                if log_level and log_level in self.log_colors:
                    self._append_log_line(line, log_level)
            
            # Restore scroll position
            if was_at_bottom:
                scroll_bar.setValue(scroll_bar.maximum())
        except Exception as e:
            print(f"Error filtering logs: {e}")
    
    def clear_logs(self):
        """Clear the current log display."""
        self.log_display.clear()
        
        # Reset file position to show only new logs
        if self.log_file and self.log_file.exists():
            self.last_position = self.log_file.stat().st_size


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
