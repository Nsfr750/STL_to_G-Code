"""
Progress reporting functionality for STL to GCode Converter.

This module provides a ProgressReporter class that handles progress updates,
including throttling, duplicate detection, and UI updates.
"""
import time
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip

logger = logging.getLogger("STLtoGCode")

class ProgressReporter:
    """
    Handles progress reporting with throttling and UI updates.
    
    This class can be used to report progress with the following features:
    - Throttling of progress updates
    - Duplicate detection
    - Minimum progress increment threshold
    - UI and logging integration
    """
    
    def __init__(self, progress_dialog=None, is_loading=True):
        """
        Initialize the progress reporter.
        
        Args:
            progress_dialog: Optional QProgressDialog for UI updates
            is_loading: Initial loading state
        """
        self.progress_dialog = progress_dialog
        self.is_loading = is_loading
        self._last_progress = -1
        self._last_progress_time = 0
        self._last_message = None
        self._logged_100_percent = False
    
    def update_progress(self, progress, message=None):
        """
        Update the progress with the current status.
        
        Args:
            progress (int/float): Progress percentage (0-100)
            message (str, optional): Optional status message
            
        Returns:
            bool: True if the progress was updated, False otherwise
        """
        # Don't process if we're not in loading state
        if not self.is_loading:
            return False
            
        try:
            # Convert progress to float and ensure it's within bounds
            progress_float = float(progress)
            progress_float = max(0.0, min(100.0, progress_float))
            progress_int = int(progress_float)
            
            # Get current time for throttling
            current_time = time.time()
            
            # Check if this is a significant update (1% change or more, or 1 second has passed)
            progress_changed = (progress_int != self._last_progress)
            time_elapsed = (current_time - self._last_progress_time) >= 1.0
            message_changed = (message != self._last_message)
            
            if progress_changed or time_elapsed or message_changed:
                # Update the UI if we have a dialog
                self._update_ui(progress_int, message)
                
                # Log progress at key intervals or when message changes
                self._log_progress(progress_float, message)
                
                # Update last values
                self._last_progress = progress_int
                self._last_progress_time = current_time
                self._last_message = message
                
                return True
                
            return False
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid progress value: {progress} - {e}")
            return False
    
    def _update_ui(self, progress_int, message):
        """Update the UI with the current progress."""
        if not hasattr(self, 'progress_dialog') or self.progress_dialog is None:
            return
            
        # Check if we can safely check if the dialog is deleted
        try:
            if hasattr(sip, 'isdeleted') and callable(sip.isdeleted):
                if sip.isdeleted(self.progress_dialog):
                    return
        except (ImportError, RuntimeError, AttributeError):
            # If sip is not available or there's an error, we'll just try to update the dialog
            pass
            
        try:
            progress_text = f"Loading: {progress_int}%"
            if message:
                progress_text = f"{progress_text} - {message}"
                
            self.progress_dialog.setLabelText(progress_text)
            self.progress_dialog.setValue(progress_int)
            QApplication.processEvents()
        except Exception as e:
            logger.warning(f"Error updating progress dialog: {e}")
    
    def _log_progress(self, progress, message):
        """Log the progress at appropriate intervals."""
        # Only log if:
        # 1. We're at a 10% interval (0%, 10%, 20%, etc.)
        # 2. We're at 100% completion (but only once)
        # 3. The message has changed
        should_log = False
        
        # Check for 10% intervals (but not 100% yet)
        if progress < 100 and progress % 10 < 0.1:
            should_log = True
        # Check for 100% completion (only log once)
        elif progress >= 100 and (not hasattr(self, '_logged_100_percent') or not self._logged_100_percent):
            should_log = True
            self._logged_100_percent = True
        # Check if message has changed
        elif hasattr(self, '_last_message') and message != self._last_message:
            should_log = True
        
        if should_log:
            log_msg = f"Loading progress: {min(100.0, progress):.1f}%"
            if message:
                log_msg = f"{log_msg} - {message}"
            logger.debug(log_msg)
    
    def reset(self):
        """Reset the progress reporter to its initial state."""
        self._last_progress = -1
        self._last_progress_time = 0
        self._last_message = None
        self._logged_100_percent = False  # Reset the 100% flag
        
        # Reset the progress dialog if it exists
        if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
            try:
                self.progress_dialog.setValue(0)
                self.progress_dialog.setLabelText("Loading...")
            except Exception as e:
                logger.warning(f"Error resetting progress dialog: {e}")
