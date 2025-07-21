"""
Error handling utilities for the STL to GCode Converter.

This module provides consistent error handling and user feedback.
"""
import os
import sys
import traceback
from typing import Optional, Callable, TypeVar, Type, Any
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt
import logging
from scripts.logger import get_logger

# Set up logging
logger = get_logger(__name__)

T = TypeVar('T')

def handle_error(
    error: Exception,
    context: str = "",
    parent=None,
    show_dialog: bool = True
) -> None:
    """
    Handle an error consistently across the application.
    
    Args:
        error: The exception that was raised
        context: Additional context about where the error occurred
        parent: Parent widget for dialogs
        show_dialog: Whether to show an error dialog to the user
    """
    # Format the error message
    error_type = type(error).__name__
    error_msg = str(error) or "No error message available"
    
    if context:
        error_msg = f"{context}: {error_msg}"
    
    # Log the error
    logger.error(error_msg, exc_info=True)
    
    if show_dialog and QApplication.instance() is not None:
        # Show error dialog in a non-blocking way
        QMessageBox.critical(
            parent,
            f"Error - {error_type}",
            error_msg,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

def handle_file_error(
    file_path: str,
    error: Exception,
    operation: str = "access",
    parent=None
) -> None:
    """
    Handle file-related errors with user-friendly messages.
    
    Args:
        file_path: Path to the file that caused the error
        error: The exception that was raised
        operation: The operation being performed (e.g., 'read', 'write', 'access')
        parent: Parent widget for dialogs
    """
    file_name = os.path.basename(file_path)
    
    if isinstance(error, PermissionError):
        msg = f"Permission denied when trying to {operation} '{file_name}'"
    elif isinstance(error, FileNotFoundError):
        msg = f"File not found: {file_name}"
    elif isinstance(error, IsADirectoryError):
        msg = f"Expected a file but found a directory: {file_name}"
    elif isinstance(error, OSError) and hasattr(error, 'winerror'):
        # Windows-specific error handling
        if error.winerror == 32:  # File in use
            msg = f"Cannot {operation} '{file_name}': The file is in use by another process"
        else:
            msg = f"Error {operation}ing file '{file_name}': {str(error)}"
    else:
        msg = f"Error {operation}ing file '{file_name}': {str(error)}"
    
    handle_error(error, msg, parent)

def with_error_handling(
    func: Callable[..., T],
    context: str = "",
    parent=None,
    show_dialog: bool = True,
    default: Any = None
) -> Callable[..., T]:
    """
    Decorator to wrap a function with error handling.
    
    Args:
        func: The function to wrap
        context: Context for error messages
        parent: Parent widget for dialogs
        show_dialog: Whether to show error dialogs
        default: Default value to return on error
        
    Returns:
        The wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e, context, parent, show_dialog)
            return default
    return wrapper

def check_file_path(
    file_path: str,
    check_exists: bool = True,
    check_readable: bool = False,
    check_writable: bool = False,
    parent=None
) -> tuple[bool, str]:
    """
    Check if a file path is valid and accessible.
    
    Args:
        file_path: Path to check
        check_exists: Whether to check if the file exists
        check_readable: Whether to check if the file is readable
        check_writable: Whether to check if the file is writable
        parent: Parent widget for dialogs
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path or not isinstance(file_path, str) or not file_path.strip():
        return False, "No file path provided"
    
    if check_exists and not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    if os.path.isdir(file_path):
        return False, f"Path is a directory, not a file: {file_path}"
    
    if check_exists and check_readable and not os.access(file_path, os.R_OK):
        return False, f"File is not readable: {file_path}"
    
    if check_writable:
        if os.path.exists(file_path):
            if not os.access(file_path, os.W_OK):
                return False, f"File is not writable: {file_path}"
        else:
            # Check if the directory is writable
            dir_path = os.path.dirname(file_path) or '.'
            if not os.access(dir_path, os.W_OK):
                return False, f"Cannot create file in read-only directory: {dir_path}"
    
    return True, ""

def show_warning(message: str, title: str = "Warning", parent=None) -> None:
    """Show a warning message to the user."""
    if QApplication.instance() is not None:
        QMessageBox.warning(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

def show_info(message: str, title: str = "Information", parent=None) -> None:
    """Show an information message to the user."""
    if QApplication.instance() is not None:
        QMessageBox.information(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

def confirm(
    message: str,
    title: str = "Confirm",
    parent=None,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes
) -> bool:
    """
    Show a confirmation dialog.
    
    Args:
        message: The message to display
        title: Dialog title
        parent: Parent widget
        default_button: Default button to highlight
        
    Returns:
        True if the user clicked Yes, False otherwise
    """
    if QApplication.instance() is None:
        return False
        
    return QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button
    ) == QMessageBox.StandardButton.Yes
