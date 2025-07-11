"""
Logging configuration for the STL to GCode Converter application.

This module provides a centralized way to configure logging for the application,
including file and console handlers with appropriate formatting.
"""
import logging
import os
import sys
from pathlib import Path
import datetime

# Flag to track if logging has been configured
_logging_configured = False

def setup_logging():
    """
    Set up logging configuration for the application.
    
    Returns:
        Path: Path to the log file that was created
    """
    global _logging_configured
    
    # Only configure logging once
    if _logging_configured:
        return logging.getLogger().handlers[0].baseFilename
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a timestamped log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"stl_to_gcode_{timestamp}.log"
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log the absolute path of the log file
    log_file_path = Path(log_file).absolute()
    
    # Set up specific loggers with higher levels
    loggers = [
        logging.getLogger('matplotlib'),
        logging.getLogger('PyQt6'),
        logging.getLogger('OpenGL'),
        logging.getLogger('PIL')
    ]
    
    for logger in loggers:
        logger.setLevel(logging.WARNING)  # Reduce verbosity for these loggers
    
    # Log startup information
    root_logger.info("=" * 80)
    root_logger.info(f"STL to GCode Converter - Logging initialized")
    root_logger.info(f"Log file: {log_file_path}")
    root_logger.info("=" * 80)
    
    _logging_configured = True
    return log_file

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (usually __name__ of the module)
        
    Returns:
        Configured logger instance
    """
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()
    return logging.getLogger(name)

# Initialize logging when this module is imported
# This ensures that if someone imports this module directly, logging is still configured
if not _logging_configured:
    setup_logging()
