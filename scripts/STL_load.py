"""
STL file loading functionality for the STL to GCode Converter.

This module provides functions to open and handle STL files with proper error handling
and logging. It's designed to work with the main application's UI and logging system.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from .stl_processor import load_stl, MemoryEfficientSTLProcessor

logger = logging.getLogger(__name__)

def open_stl_file(parent: Optional[QWidget] = None, file_path: Optional[str] = None) -> Tuple[Optional[MemoryEfficientSTLProcessor], Dict[str, Any]]:
    """
    Open an STL file with progress tracking and error handling.
    
    Args:
        parent: Parent widget for dialogs
        file_path: Optional path to the STL file. If None, a file dialog will be shown.
        
    Returns:
        A tuple containing:
        - The STL processor instance if successful, None otherwise
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
                "Open STL File",
                "",
                "STL Files (*.stl);;All Files (*)"
            )
            
            if not file_path:
                logger.debug("No file selected")
                return None, result
        
        logger.info(f"Opening STL file: {file_path}")
        
        # Validate file exists and is readable
        if not os.path.isfile(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            result.update({
                'error': "File not found",
                'error_details': error_msg
            })
            return None, result
            
        # Try to load the STL file
        try:
            stl_processor = load_stl(file_path)
            stl_processor.open()
            
            # Get basic file info
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            logger.info(f"Successfully opened STL file: {file_name} ({file_size:.2f} MB)")
            
            # Update result with success info
            result.update({
                'success': True,
                'file_path': file_path,
                'file_name': file_name,
                'file_size_mb': file_size,
                'num_triangles': stl_processor._header.num_triangles if hasattr(stl_processor, '_header') else 0
            })
            
            return stl_processor, result
            
        except Exception as e:
            error_msg = f"Error loading STL file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.update({
                'error': "Failed to load STL file",
                'error_details': str(e)
            })
            return None, result
            
    except Exception as e:
        error_msg = f"Unexpected error while opening file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result.update({
            'error': "Unexpected error",
            'error_details': str(e)
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
        "Error Opening File",
        f"Failed to open STL file.\n\nDetails: {error_details}"
    )
