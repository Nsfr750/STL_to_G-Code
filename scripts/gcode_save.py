"""
G-code file saving functionality for the STL to GCode Converter.

This module provides functions to save G-code files with proper error handling
and user feedback. It's designed to work with the main application's UI and logging system.
"""
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtCore import QFileInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_gcode_file(parent: QWidget = None, content: str = "", 
                   default_filename: str = "") -> dict:
    """
    Save G-code content to a file with a file dialog.
    
    Args:
        parent: Parent widget for dialogs
        content: The G-code content to save
        default_filename: Optional default filename to suggest
        
    Returns:
        dict: Dictionary containing operation status and file info
    """
    try:
        if not content.strip():
            return {
                'success': False,
                'error': 'No content to save',
                'error_details': 'The G-code content is empty.'
            }
        
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save G-code File",
            default_filename or "",
            "G-code Files (*.gcode *.nc);;All Files (*)"
        )
        
        if not file_path:
            return {
                'success': False,
                'error': 'No file selected',
                'error_details': 'No file path was provided.'
            }
        
        # Ensure file has .gcode or .nc extension
        if not file_path.lower().endswith(('.gcode', '.nc')):
            file_path += '.gcode'
        
        # Check if file exists and prompt for overwrite
        if os.path.exists(file_path):
            reply = QMessageBox.question(
                parent,
                "File Exists",
                f"The file {os.path.basename(file_path)} already exists.\nDo you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return {
                    'success': False,
                    'error': 'Operation cancelled',
                    'error_details': 'User chose not to overwrite existing file.'
                }
        
        # Save the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file info for the result
        file_info = QFileInfo(file_path)
        
        logger.info(f"Successfully saved G-code to {file_path}")
        
        return {
            'success': True,
            'file_path': file_path,
            'file_name': file_info.fileName(),
            'file_size': file_info.size()
        }
        
    except PermissionError as e:
        error_msg = "Permission denied when trying to save the file."
        logger.error(f"{error_msg} {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': 'Permission denied',
            'error_details': error_msg
        }
        
    except Exception as e:
        error_msg = f"Error saving G-code file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': 'File save failed',
            'error_details': error_msg
        }

def show_file_save_error(parent: QWidget, error_details: dict):
    """
    Show an error message for file save failures.
    
    Args:
        parent: Parent widget for the message box
        error_details: Dictionary containing error details
    """
    error_msg = error_details.get('error', 'Unknown error')
    details = error_details.get('error_details', 'No additional details available.')
    
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Error Saving File")
    msg.setText(f"Failed to save G-code file: {error_msg}")
    msg.setDetailedText(details)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()
    
    logger.error(f"File save error: {error_msg} - {details}")
