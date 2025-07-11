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

def setup_logging():
    """
    Set up logging configuration for the application.
    
    Returns:
        Path: Path to the log file that was created
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a timestamped log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"stl_to_gcode_{timestamp}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Set up specific loggers
    loggers = [
        logging.getLogger('matplotlib'),
        logging.getLogger('PyQt6'),
        logging.getLogger('OpenGL')
    ]
    
    for logger in loggers:
        logger.setLevel(logging.WARNING)  # Reduce verbosity for these loggers
    
    # Log startup information
    root_logger = logging.getLogger()
    root_logger.info("=" * 80)
    root_logger.info(f"STL to GCode Converter - Logging initialized")
    root_logger.info(f"Log file: {log_file.absolute()}")
    root_logger.info("=" * 80)
    
    return log_file

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (usually __name__ of the module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

# Initialize logging when this module is imported
log_file = setup_logging()
