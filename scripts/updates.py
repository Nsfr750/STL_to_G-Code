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
import sys
import ssl
from urllib.parse import urljoin
from PyQt6.QtWidgets import QMessageBox, QWidget, QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot

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
        self.updates_dir.mkdir(exist_ok=True, parents=True)  # Add parents=True to create parent dirs
        
        # Path to store last update check time
        self.last_check_file = self.updates_dir / 'last_check.json'
        
        # Configure requests session with timeout and retry
        self.session = requests.Session()
        self.session.timeout = 15  # 15 seconds timeout
        
        # Add retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
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
            
            # Create a thread to perform the check
            self.thread = QThread()
            self.worker = UpdateWorker(self.current_version)
            self.worker.moveToThread(self.thread)
            
            # Connect signals
            self.thread.started.connect(self.worker.check)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.update_available.connect(self._handle_update_response)
            self.worker.no_update_available.connect(self.no_update_available)
            self.worker.error_occurred.connect(self.error_occurred)
            
            # Start the thread
            self.thread.start()
            
        except Exception as e:
            error_msg = f"Error starting update check: {str(e)}"
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
                # Check at most once per day (24 hours)
                return (time.time() - last_check) > 86400
        except Exception as e:
            logger.warning(f"Error reading last check time: {e}")
            return True
    
    def _handle_update_response(self, release_data: Dict[str, Any]) -> None:
        """Handle the response from the update check."""
        try:
            # Save the last check time
            self.updates_dir.mkdir(parents=True, exist_ok=True)
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
        try:
            # Try to use packaging if available
            try:
                from packaging import version
                return version.parse(latest) > version.parse(current)
            except ImportError:
                # Fallback to simple string comparison
                return latest > current
        except Exception as e:
            logger.warning(f"Error comparing versions: {e}")
            return False


class UpdateWorker(QObject):
    """Worker class for performing update checks in a background thread."""
    
    update_available = pyqtSignal(dict)
    no_update_available = pyqtSignal()
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.session = requests.Session()
        self.session.timeout = 15
    
    def check(self):
        """Perform the update check."""
        try:
            # Add a user agent to identify our requests
            headers = {
                'User-Agent': f'STL-to-GCode-Updater/{self.current_version}'
            }
            
            # Make the request to check for updates
            response = self.session.get(
                "https://api.github.com/repos/Nsfr750/STL_to_G-Code/releases/latest",
                headers=headers,
                timeout=15,
                verify=True  # Enable SSL verification
            )
            
            # Check for rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                if int(response.headers['X-RateLimit-Remaining']) <= 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
                    wait_time = reset_time - int(time.time())
                    if wait_time > 0:
                        error_msg = f"GitHub API rate limit exceeded. Please try again in {wait_time//60} minutes."
                        self.error_occurred.emit(error_msg)
                        return
            
            response.raise_for_status()
            
            # Parse the response
            latest_release = response.json()
            self.update_available.emit(latest_release)
            
        except requests.exceptions.SSLError as e:
            error_msg = "SSL certificate verification failed. Please check your system's date and time settings."
            self.error_occurred.emit(error_msg)
        except requests.exceptions.Timeout:
            self.error_occurred.emit("The update check timed out. Please check your internet connection.")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Could not connect to the update server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Error checking for updates: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
        finally:
            self.finished.emit()


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
    # Create QApplication instance if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
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
        if not silent_if_no_update and parent is not None:
            QMessageBox.information(
                parent,
                "No Updates",
                f"You are running the latest version ({current_version}).",
                QMessageBox.StandardButton.Ok
            )
    
    def on_error(message):
        if parent is not None:  # Only show error if we have a parent widget
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
    
    # Test with the current version as 0.0.1 to force an update check
    check_for_updates(current_version="0.0.1", force_check=True)
    
    sys.exit(app.exec())
