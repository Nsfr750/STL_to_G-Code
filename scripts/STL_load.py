"""
STL file loading and handling utilities.
"""
import os
import logging
from scripts.logger import get_logger
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QFileInfo
from scripts.language_manager import LanguageManager

# Configure logging
logger = get_logger(__name__)

# Initialize language manager
language_manager = LanguageManager()

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
        # Show file dialog if no path provided
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent=parent,
                caption=language_manager.translate("stl.loading.open_dialog_title"),
                filter=language_manager.translate("stl.loading.file_filter")
            )
            if not file_path:
                return None, None, False, language_manager.translate("stl.loading.no_file_selected")
        
        file_info = QFileInfo(file_path)
        
        # Basic file validation
        if not file_info.exists():
            return None, None, False, language_manager.translate(
                "stl.loading.file_not_found", 
                file_path=file_path
            )
            
        # Warn for large files (>100MB)
        if file_info.size() > 100 * 1024 * 1024:  # 100MB
            if not confirm_large_file(parent, file_info.size()):
                return None, None, False, language_manager.translate("stl.loading.operation_cancelled")
        
        logger.info("Opening STL file: %s", file_path)
        return file_path, file_info.fileName(), True, ""
        
    except Exception as e:
        error_msg = language_manager.translate("stl.loading.error_opening", error=str(e))
        logger.exception(error_msg)
        return None, None, False, error_msg

def confirm_large_file(parent, file_size):
    """Show confirmation dialog for large files."""
    size_mb = file_size / (1024 * 1024)
    reply = QMessageBox.question(
        parent,
        language_manager.translate("stl.loading.large_file_title"),
        language_manager.translate("stl.loading.large_file_message", size_mb=size_mb),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes

def show_file_open_error(parent, error_details):
    """Show an error message for file open failures."""
    error_msg = error_details.get('error', language_manager.translate('stl.loading.operation_cancelled'))
    file_path = error_details.get('file_path', language_manager.translate('stl.loading.no_file_selected'))
    
    QMessageBox.critical(
        parent,
        language_manager.translate("stl.loading.error_title"),
        language_manager.translate(
            "stl.loading.failed_to_open",
            file_path=file_path,
            error_msg=error_msg
        )
    )
    
    logger.error("Failed to open file %s: %s", file_path, error_msg)

def get_stl_metadata(file_path):
    """
    Read basic metadata from an STL file.
    
    Args:
        file_path: Path to the STL file
        
    Returns:
        dict: Dictionary containing file metadata or error information
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
        error_msg = language_manager.translate("stl.loading.error_metadata", error=str(e))
        logger.exception(error_msg)
        return {'error': error_msg}
