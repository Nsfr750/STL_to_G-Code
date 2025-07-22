"""
G-code file loading functionality for the STL to GCode Converter.

This module provides functions to open and handle G-code files with proper error handling
and logging. It's designed to work with the main application's UI and logging system.
"""
import os
import logging
from scripts.logger import get_logger
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from scripts.language_manager import LanguageManager

# Initialize language manager
language_manager = LanguageManager()

logger = get_logger(__name__)

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
                language_manager.translate("gcode.loading.open_dialog_title"),
                "",
                language_manager.translate("gcode.loading.file_filter")
            )
            
            if not file_path:
                logger.debug(language_manager.translate("gcode.loading.no_file_selected"))
                return None, result
        
        # Validate file path
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            error_msg = language_manager.translate(
                "gcode.loading.file_not_found", 
                file_path=file_path
            )
            logger.error(error_msg)
            result['error'] = language_manager.translate("error_handling.file_not_found", file_path=file_path)
            result['error_details'] = error_msg
            return None, result
            
        # Check file size (warn for large files)
        file_size = path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            logger.warning(language_manager.translate(
                "gcode.loading.large_file_detected",
                size_mb=size_mb
            ))
            
            if parent is not None:
                reply = QMessageBox.question(
                    parent,
                    language_manager.translate("gcode.loading.large_file_title"),
                    language_manager.translate(
                        "gcode.loading.large_file_message",
                        size_mb=size_mb
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    logger.info(language_manager.translate("gcode.loading.user_canceled"))
                    result['error'] = language_manager.translate("gcode.loading.operation_canceled")
                    result['error_details'] = language_manager.translate("gcode.loading.user_canceled")
                    return None, result
        
        # Read the G-code file
        logger.info(language_manager.translate(
            "gcode.loading.loading_file",
            file_path=file_path
        ))
        
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
        
        logger.info(language_manager.translate(
            "gcode.loading.success",
            file_name=path.name,
            file_size=file_size,
            line_count=result['line_count']
        ))
        
        return gcode_content, result
        
    except PermissionError as e:
        error_msg = language_manager.translate(
            "gcode.loading.permission_denied",
            file_path=file_path
        )
        logger.error(error_msg)
        result['error'] = error_msg
        result['error_details'] = str(e)
        return None, result
        
    except IOError as e:
        error_msg = language_manager.translate(
            "gcode.loading.io_error",
            file_path=file_path
        )
        logger.error(error_msg, exc_info=True)
        result['error'] = error_msg
        result['error_details'] = str(e)
        return None, result
        
    except Exception as e:
        error_msg = language_manager.translate(
            "gcode.loading.unexpected_error",
            file_path=file_path
        )
        logger.error(error_msg, exc_info=True)
        result['error'] = error_msg
        result['error_details'] = str(e)
        return None, result

def show_file_open_error(parent: QWidget, error_details: str) -> None:
    """
    Show an error message for file opening failures.
    
    Args:
        parent: Parent widget for the message box
        error_details: Detailed error message to display
    """
    QMessageBox.critical(
        parent,
        language_manager.translate("error_handling.error_dialog_title", error_type="File Open Error"),
        error_details,
        QMessageBox.StandardButton.Ok
    )
