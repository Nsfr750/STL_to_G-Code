"""
G-code file loading functionality for the STL to GCode Converter.

This module provides functions to open and handle G-code files with proper error handling
and logging. It's designed to work with the main application's UI and logging system.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

logger = logging.getLogger(__name__)

def open_gcode_file(parent: Optional[QWidget] = None, file_path: Optional[str] = None) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Open a G-code file with progress tracking and error handling.
    
    Args:
        parent: Parent widget for dialogs
        file_path: Optional path to the G-code file. If None, a file dialog will be shown.
        
    Returns:
        A tuple containing:
        - The G-code content as a string if successful, None otherwise
        - A dictionary with file information or error details
    """
    result = {
        'success': False,
        'file_path': None,
        'file_name': None,
        'error': None,
        'error_details': None
    }
    
    try:
        # If no file path provided, show file dialog
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Open G-code File",
                "",
                "G-code Files (*.gcode *.nc *.tap);;All Files (*)"
            )
            
            if not file_path:
                logger.debug("No file selected")
                return None, result
        
        # Validate file path
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            result['error'] = "File not found"
            result['error_details'] = error_msg
            return None, result
            
        # Check file size (warn for large files)
        file_size = path.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB
            logger.warning(f"Large G-code file detected: {file_size/1024/1024:.2f}MB")
            
            if parent is not None:
                reply = QMessageBox.question(
                    parent,
                    "Large File Warning",
                    f"This G-code file is {file_size/1024/1024:.2f}MB. "
                    "Loading large files may take time and consume significant memory.\n\n"
                    "Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    logger.info("User canceled loading large file")
                    result['error'] = "Operation canceled"
                    result['error_details'] = "User canceled loading large file"
                    return None, result
        
        # Read the G-code file
        logger.info(f"Loading G-code file: {file_path}")
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            gcode_content = f.read()
        
        # Update result with success information
        result.update({
            'success': True,
            'file_path': str(path.absolute()),
            'file_name': path.name,
            'file_size': file_size,
            'line_count': len(gcode_content.splitlines())
        })
        
        logger.info(f"Successfully loaded G-code file: {path.name} ({file_size} bytes, {result['line_count']} lines)")
        return gcode_content, result
        
    except PermissionError as e:
        error_msg = f"Permission denied when accessing file: {file_path}"
        logger.error(error_msg, exc_info=True)
        result.update({
            'error': "Permission denied",
            'error_details': error_msg
        })
        return None, result
        
    except UnicodeDecodeError as e:
        error_msg = f"Failed to decode G-code file (not valid UTF-8): {file_path}"
        logger.error(error_msg, exc_info=True)
        result.update({
            'error': "Invalid file encoding",
            'error_details': error_msg
        })
        return None, result
        
    except Exception as e:
        error_msg = f"Error loading G-code file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result.update({
            'error': "Error loading file",
            'error_details': error_msg
        })
        return None, result

def show_file_open_error(parent: QWidget, error_details: str):
    """
    Show an error message for file opening failures.
    
    Args:
        parent: Parent widget for the message box
        error_details: Detailed error message to display
    """
    QMessageBox.critical(
        parent,
        "Error Loading G-code",
        f"Failed to load G-code file.\n\n"
        f"Details: {error_details}\n\n"
        "Please ensure the file exists and you have permission to access it.",
        QMessageBox.StandardButton.Ok
    )
