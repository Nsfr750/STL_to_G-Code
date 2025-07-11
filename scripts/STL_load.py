"""
STL file loading and handling utilities.
"""
import os
import logging
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QFileInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def open_stl_file(parent=None, file_path=None):
    """
    Open an STL file with a file dialog if no path is provided.
    
    Args:
        parent: Parent widget for the file dialog
        file_path: Optional path to the STL file to open directly
        
    Returns:
        tuple: (file_path, file_name, success, error_message)
    """
    try:
        # If no file path provided, show file dialog
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Open STL File",
                "",
                "STL Files (*.stl);;All Files (*)"
            )
            
            if not file_path:
                return None, None, False, "No file selected"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return None, None, False, f"File not found: {file_path}"
            
        # Check file size
        file_info = QFileInfo(file_path)
        file_size = file_info.size()
        file_name = file_info.fileName()
        
        # Warn for large files (>100MB)
        if file_size > 100 * 1024 * 1024:  # 100MB
            reply = QMessageBox.question(
                parent,
                "Large File Warning",
                f"The selected file is large ({file_size/1024/1024:.1f} MB). "
                "This may take a while to process. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return None, None, False, "Operation cancelled by user"
        
        logger.info(f"Opening STL file: {file_path}")
        return file_path, file_name, True, ""
        
    except Exception as e:
        error_msg = f"Error opening STL file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, None, False, error_msg

def show_file_open_error(parent, error_details):
    """
    Show an error message for file open failures.
    
    Args:
        parent: Parent widget for the error dialog
        error_details: Dictionary containing error details
    """
    error_msg = error_details.get('error', 'Unknown error')
    file_path = error_details.get('file_path', 'Unknown file')
    
    QMessageBox.critical(
        parent,
        "Error Opening File",
        f"Failed to open file: {file_path}\n\nError: {error_msg}"
    )
    
    logger.error(f"Failed to open file {file_path}: {error_msg}")

def get_stl_metadata(file_path):
    """
    Read basic metadata from an STL file.
    
    Args:
        file_path: Path to the STL file
        
    Returns:
        dict: Dictionary containing file metadata
    """
    try:
        file_info = QFileInfo(file_path)
        return {
            'file_name': file_info.fileName(),
            'file_path': file_path,
            'file_size': file_info.size(),
            'last_modified': file_info.lastModified().toString(),
            'exists': file_info.exists(),
            'is_file': file_info.isFile()
        }
    except Exception as e:
        logger.error(f"Error getting STL metadata: {str(e)}", exc_info=True)
        return {'error': str(e)}
