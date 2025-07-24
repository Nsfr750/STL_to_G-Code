"""
Update checking functionality for the STL to G-Code application.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from scripts.language_manager import LanguageManager
from scripts.logger import get_logger
from scripts.version import __version__

# Configure logging
logger = get_logger(__name__)

# Constants
UPDATES_FILE = Path("updates.json")

class UpdateChecker(QObject):
    """Handles checking for application updates."""
    
    update_available = pyqtSignal(dict)
    no_update_available = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version: str = None, config_path: Optional[Path] = None, parent=None):
        """
        Initialize the update checker.
        
        Args:
            current_version: Current application version string (e.g., '1.0.0')
                           If None, will be read from version.py
            config_path: Optional path to configuration file
            parent: Parent QObject
        """
        super().__init__(parent)
        self.current_version = current_version or __version__
        self.config_path = config_path or UPDATES_FILE
        
        # Initialize language manager
        self.language_manager = LanguageManager()
        self.translate = self.language_manager.translate
        
        # Load update configuration
        self.config = self._load_config()
        self.last_check = self.config.get('last_check', 0)
        self.last_version = self.config.get('last_version', '')
        
        # Set up the worker thread
        self.worker = None
        self.thread = None
        
        logger.debug(f"Update checker initialized for version {self.current_version}")
    
    def _setup_directories(self):
        """Create necessary directories and files."""
        self.updates_dir = self.config_path / 'config'
        self.updates_dir.mkdir(exist_ok=True, parents=True)
        self.last_check_file = self.updates_dir / 'last_check.json'
    
    def _setup_session(self):
        """Configure the requests session with retry strategy."""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        self.session.timeout = 15
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _on_language_changed(self, language: str):
        """Update translation function when language changes."""
        logger.debug(f"Update checker language changed to: {language}")
        self.translate = self.language_manager.translate
    
    def check_for_updates(self, force: bool = False) -> None:
        """Initiate update check in a background thread."""
        try:
            if not force and not self._should_check():
                logger.debug("Skipping update check (too soon since last check)")
                self.no_update_available.emit()
                return
            
            logger.info(self.translate("updates.checking"))
            
            self.thread = QThread()
            self.worker = UpdateWorker(self.current_version, self.translate)
            self.worker.moveToThread(self.thread)
            
            self.thread.started.connect(self.worker.check)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.update_available.connect(self._handle_update_response)
            self.worker.no_update_available.connect(self.no_update_available)
            self.worker.error_occurred.connect(self.error_occurred)
            
            self.thread.start()
            
        except Exception as e:
            error_msg = self.translate("updates.error.check_failed", error=str(e))
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def _handle_update_response(self, update_info: Dict[str, Any]) -> None:
        """Process update information from the worker thread."""
        try:
            self._save_last_check(self.current_version)
            self.update_available.emit(update_info)
        except Exception as e:
            error_msg = self.translate("updates.error.check_failed", error=str(e))
            logger.error(f"Error handling update response: {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def _should_check(self) -> bool:
        """Determine if an update check should be performed."""
        try:
            if not self.last_check_file.exists():
                return True
                
            with open(self.last_check_file, 'r') as f:
                data = json.load(f)
                last_check = data.get('last_check', 0)
                check_interval = data.get('check_interval', 86400)  # 24 hours
                return (time.time() - last_check) >= check_interval
                
        except Exception as e:
            logger.error(f"Error checking last update time: {e}")
            return True
    
    def _save_last_check(self, version: str) -> None:
        """
        Save the last update check time and version to the config file.
        
        Args:
            version: The version that was checked
        """
        try:
            self.config['last_check'] = int(time.time())
            self.config['last_version'] = version
            self._save_config(self.config)
            
        except Exception as e:
            logger.error(f"Error saving last update check time: {e}")
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save the update configuration to file in the config/ directory.
        
        Args:
            config: The configuration to save
        """
        try:
            # Ensure the config directory exists
            config_dir = self.config_path.parent / 'config'
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Update the config path to include the config directory
            config_file = config_dir / 'updates.json'
            
            # Save the configuration
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            logger.debug(f"Configuration saved to {config_file}")
                
        except Exception as e:
            logger.error(f"Error saving update config: {e}")
            raise
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the update configuration from file in the config/ directory.
        
        Returns:
            dict: The loaded configuration or default values if file doesn't exist
        """
        default_config = {
            'last_check': 0,
            'last_version': '',
            'update_url': 'https://api.github.com/repos/Nsfr750/STL_to_G-Code/releases/latest',
            'check_interval': 86400  # 24 hours in seconds
        }
        
        try:
            # Check for config file in the config/ directory
            config_dir = self.config_path.parent / 'config'
            config_file = config_dir / 'updates.json'
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Ensure all required keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
                    
            logger.debug(f"No config file found at {config_file}, using default configuration")
                    
        except Exception as e:
            logger.warning(f"Error loading update config: {str(e)}")
            
        return default_config


class UpdateWorker(QObject):
    """Worker class for performing update checks in a background thread."""
    
    update_available = pyqtSignal(dict)
    no_update_available = pyqtSignal()
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, current_version: str, translate_func):
        super().__init__()
        self.current_version = current_version
        self.translate = translate_func
        self.session = requests.Session()
        self.session.timeout = 15
    
    def check(self) -> None:
        """Perform the update check in the background thread."""
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
                        error_msg = self.translate("updates.error.rate_limit_exceeded", wait_time=wait_time//60)
                        self.error_occurred.emit(error_msg)
                        return
            
            response.raise_for_status()
            
            # Parse the response
            latest_release = response.json()
            self.update_available.emit(latest_release)
            
        except requests.exceptions.RequestException as e:
            error_msg = self.translate("updates.error.connection")
            self.error_occurred.emit(error_msg)
            logger.error(f"Network error during update check: {e}")
        except json.JSONDecodeError as e:
            error_msg = self.translate("updates.error.invalid_response")
            self.error_occurred.emit(error_msg)
            logger.error(f"Invalid JSON response during update check: {e}")
        except Exception as e:
            error_msg = self.translate("updates.error.check_failed", error=str(e))
            self.error_occurred.emit(error_msg)
            logger.error(f"Error during update check: {e}")
        finally:
            self.finished.emit()


def check_for_updates(parent=None, current_version: str = "0.0.0", 
                    force_check: bool = False, silent_if_no_update: bool = False) -> None:
    """
    Check for application updates and show a dialog if an update is available.
    
    Args:
        parent: Parent widget for dialogs
        current_version: Current application version
        force_check: If True, skip cache and force a check
        silent_if_no_update: If True, don't show any UI if no update is available
    """
    from PyQt6.QtWidgets import QMessageBox
    
    # Get language manager for translations
    from scripts.language_manager import LanguageManager
    language_manager = LanguageManager()
    translate = language_manager.translate
    
    def on_update_available(update_info: dict) -> None:
        """Handle update available event."""
        try:
            # Format the changelog with bullet points
            changelog = update_info.get('changelog', translate("updates.no_changelog"))
            formatted_changelog = '\n'.join(f'• {line.strip()}' for line in changelog.split('\n') if line.strip())
            
            # Show update dialog
            msg = QMessageBox(parent)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(translate("updates.available.title"))
            msg.setText(translate("updates.available.message").format(
                version=update_info.get('version', '?'),
                changelog=formatted_changelog
            ))
            
            # Add buttons
            download_btn = msg.addButton(
                translate("updates.available.download"), 
                QMessageBox.ButtonRole.AcceptRole
            )
            later_btn = msg.addButton(
                translate("updates.available.later"), 
                QMessageBox.ButtonRole.RejectRole
            )
            skip_btn = msg.addButton(
                translate("updates.available.skip"),
                QMessageBox.ButtonRole.DestructiveRole
            )
            
            msg.exec()
            
            # Handle button clicks
            if msg.clickedButton() == download_btn:
                # Handle download
                QMessageBox.information(
                    parent,
                    translate("updates.download.starting"),
                    translate("updates.download.starting_message")
                )
                # TODO: Implement download logic
                
            elif msg.clickedButton() == skip_btn:
                # TODO: Store skipped version to not notify again
                pass
                
        except Exception as e:
            logger.error(f"Error showing update dialog: {e}")
    
    def on_no_update() -> None:
        """Handle no update available event."""
        if not silent_if_no_update:
            QMessageBox.information(
                parent,
                translate("updates.latest.title"),
                translate("updates.latest.message").format(version=current_version)
            )
    
    def on_error(error_msg: str) -> None:
        """Handle error during update check."""
        if not silent_if_no_update:
            QMessageBox.warning(
                parent,
                translate("updates.error.title"),
                error_msg
            )
    
    # Create and configure the update checker
    checker = UpdateChecker(current_version=current_version)
    checker.update_available.connect(on_update_available)
    checker.no_update_available.connect(on_no_update)
    checker.error_occurred.connect(on_error)
    
    # Start the update check
    checker.check_for_updates(force=force_check)


if __name__ == "__main__":
    """Test the update checker."""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Initialize the application
    app = QApplication(sys.argv)
    
    # Initialize language manager
    from scripts.language_manager import LanguageManager
    language_manager = LanguageManager()
    language_manager.set_language('en')  # or 'it' for Italian
    
    # Test with the current version as 0.0.1 to force an update check
    check_for_updates(current_version="0.0.1", force_check=True)
    
    # Start the event loop
    sys.exit(app.exec())
