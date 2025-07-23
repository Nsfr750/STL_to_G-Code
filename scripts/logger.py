"""
Logging configuration for the STL to GCode Converter application.

This module provides a centralized way to configure logging for the application,
including file and console handlers with appropriate formatting and daily log rotation.
All log files are stored in the logs directory at the project root.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

# Import the language manager
from .language_manager import LanguageManager

# Flag to track if logging has been configured
_logging_configured = False

# Define log directory name (relative to the project root)
LOG_DIR = Path("logs")

class DailyRotatingFileHandler(TimedRotatingFileHandler):
    """Custom handler that creates a new log file each day with the date in the filename."""
    def __init__(self, filename: str, **kwargs):
        # Ensure the logs directory exists
        LOG_DIR.mkdir(exist_ok=True, parents=True)
        
        # Get current date in YYYY-MM-DD format
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Create the log file with date in the name
        log_file = LOG_DIR / f"{filename}-{date_str}.log"
        
        # Initialize the parent class with daily rotation at midnight
        # Set backupCount to 0 since we're handling the date in the filename
        super().__init__(
            filename=str(log_file.absolute()),
            when='midnight',
            interval=1,
            backupCount=0,  # We don't need backup files since we have date in the filename
            encoding='utf-8',
            **kwargs
        )
        
        # Set the current log file name
        self.baseFilename = str(log_file.absolute())
    
    def doRollover(self):
        """Override to create a new log file with the current date."""
        # Close the old file
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Get current date in YYYY-MM-DD format
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Create new log file with current date
        log_file = LOG_DIR / f"{self.baseFilename.rsplit('-', 1)[0].rsplit(os.sep, 1)[-1]}-{date_str}.log"
        self.baseFilename = str(log_file.absolute())
        
        # Open the new log file
        if not self.delay:
            self.stream = self._open()
        
        # Update the modification time for the next rollover check
        self.rolloverAt = self.rolloverAt + self.interval

def setup_logging(language_manager: Optional[LanguageManager] = None) -> Optional[str]:
    """
    Set up logging configuration for the application with daily rotation.
    
    Args:
        language_manager: Optional LanguageManager instance for localized log messages
        
    Returns:
        str: Absolute path to the current log file or None if not applicable
    """
    global _logging_configured
    
    # Only configure logging once
    if _logging_configured:
        for handler in get_logger().handlers:
            if hasattr(handler, 'baseFilename'):
                return handler.baseFilename
        return None
    
    # Create a logger with the application name
    logger = logging.getLogger("STLtoGCode")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Get log format from language system or use default
    log_format = (
        language_manager.get_translation("logging.format") 
        if language_manager else 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    date_format = (
        language_manager.get_translation("logging.date_format") 
        if language_manager else 
        "%Y-%m-%d %H:%M:%S"
    )
    
    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler with daily rotation
    try:
        file_handler = DailyRotatingFileHandler("stl_to_gcode")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        log_file = file_handler.baseFilename
    except Exception as e:
        logger.warning(
            "Failed to create log file: %s. Logging to console only.",
            str(e),
            exc_info=True
        )
        log_file = None
    
    _logging_configured = True
    logger.debug("Logging configured successfully")
    
    return log_file

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (usually __name__ of the module).
              If None, returns the root logger.
              
    Returns:
        Configured logger instance with the specified name
    """
    # If logging hasn't been configured yet, set it up with defaults
    if not _logging_configured:
        setup_logging()
    
    # Get the logger with the specified name
    logger = logging.getLogger("STLtoGCode" + (f".{name}" if name else ""))
    
    # Ensure the logger has at least one handler
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    
    return logger

# Initialize logging when this module is imported
if not _logging_configured:
    setup_logging()
