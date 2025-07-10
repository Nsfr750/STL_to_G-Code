"""
Update checking functionality for the STL to G-Code application.
"""
import logging
from typing import Optional, Tuple, Dict, Any
import requests
import json
from pathlib import Path
import os
import time
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal

# Get the application directory
APP_DIR = Path(__file__).parent.parent  # Now points to the project root
UPDATES_FILE = APP_DIR / 'updates.json'  # Keep updates.json in the project root

# Configure logger
logger = logging.getLogger(__name__)

class UpdateChecker(QObject):
    """Handles checking for application updates."""
    
    update_available = pyqtSignal(dict)
    no_update_available = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version: str, config_path: Optional[Path] = None):
        """Initialize the update checker.
        
        Args:
            current_version: The current application version.
            config_path: Optional path to the configuration directory.
        """
        super().__init__()
        self.current_version = current_version
        self.config_path = config_path or APP_DIR
        
        # Create updates directory if it doesn't exist
        self.updates_dir = self.config_path / 'updates'
        self.updates_dir.mkdir(exist_ok=True)
        
        # Path to store last update check time
        self.last_check_file = self.updates_dir / 'last_check.json'
    
    def check_for_updates(self, force: bool = False) -> None:
        """Check for updates.
        
        Args:
            force: If True, skip cache and force a check.
        """
        try:
            # Check if we should skip the check
            if not force and not self._should_check():
                logger.debug("Skipping update check (too soon since last check)")
                self.no_update_available.emit()
                return
            
            # Make the request to check for updates
            response = requests.get(
                "https://api.github.com/repos/Nsfr750/STL_to_G-Code/releases/latest",
                timeout=10
            )
            response.raise_for_status()
            
            # Parse the response
            latest_release = response.json()
            self._handle_update_response(latest_release)
            
        except requests.RequestException as e:
            error_msg = f"Error checking for updates: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error checking for updates: {str(e)}"
            logger.exception(error_msg)
            self.error_occurred.emit(error_msg)
    
    def _should_check(self) -> bool:
        """Determine if we should check for updates based on the last check time."""
        if not self.last_check_file.exists():
            return True
            
        try:
            with open(self.last_check_file, 'r') as f:
                data = json.load(f)
                last_check = data.get('last_check', 0)
                # Check at most once per day
                return (time.time() - last_check) > 86400
        except Exception as e:
            logger.warning(f"Error reading last check time: {e}")
            return True
    
    def _handle_update_response(self, release_data: Dict[str, Any]) -> None:
        """Handle the response from the update check."""
        try:
            # Save the last check time
            with open(self.last_check_file, 'w') as f:
                json.dump({'last_check': time.time()}, f)
            
            latest_version = release_data.get('tag_name', '').lstrip('v')
            if self._is_newer_version(latest_version, self.current_version):
                update_info = {
                    'version': latest_version,
                    'url': release_data.get('html_url', ''),
                    'body': release_data.get('body', ''),
                    'published_at': release_data.get('published_at', '')
                }
                self.update_available.emit(update_info)
            else:
                self.no_update_available.emit()
                
        except Exception as e:
            error_msg = f"Error processing update response: {str(e)}"
            logger.exception(error_msg)
            self.error_occurred.emit(error_msg)
    
    @staticmethod
    def _is_newer_version(latest: str, current: str) -> bool:
        """Check if the latest version is newer than the current version."""
        from packaging import version
        try:
            return version.parse(latest) > version.parse(current)
        except Exception:
            return False

def check_for_updates(parent: Optional[QWidget] = None, 
                    current_version: str = "0.0.0", 
                    force_check: bool = False,
                    silent_if_no_update: bool = False) -> Tuple[bool, Optional[Dict]]:
    """Check for application updates and show a dialog if an update is available.
    
    Args:
        parent: Parent widget for dialogs.
        current_version: Current application version.
        force_check: If True, skip the cache and force a check.
        silent_if_no_update: If True, don't show any UI if no update is available.
        
    Returns:
        Tuple of (update_available, update_info)
    """
    checker = UpdateChecker(current_version)
    update_available = False
    update_info = None
    
    def on_update_available(info):
        nonlocal update_available, update_info
        update_available = True
        update_info = info
        
        # Show update dialog
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Update Available")
        msg.setText(f"Version {info['version']} is available!")
        msg.setInformativeText("Would you like to download the latest version?")
        
        download_btn = msg.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == download_btn:
            import webbrowser
            webbrowser.open(info['url'])
    
    def on_no_update():
        if not silent_if_no_update:
            QMessageBox.information(
                parent,
                "No Updates",
                "You are running the latest version.",
                QMessageBox.StandardButton.Ok
            )
    
    def on_error(message):
        QMessageBox.warning(
            parent,
            "Update Error",
            f"Could not check for updates: {message}",
            QMessageBox.StandardButton.Ok
        )
    
    # Connect signals
    checker.update_available.connect(on_update_available)
    checker.no_update_available.connect(on_no_update)
    checker.error_occurred.connect(on_error)
    
    # Start the check
    checker.check_for_updates(force=force_check)
    
    return update_available, update_info

# For testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    def show_update_info(update_info):
        print(f"Update available: {update_info}")
    
    app = QApplication(sys.argv)
    checker = UpdateChecker("1.0.0")
    checker.update_available.connect(show_update_info)
    checker.check_for_updates()
    
    sys.exit(app.exec())
