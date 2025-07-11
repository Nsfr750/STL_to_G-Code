"""
Test script for verifying update check functionality.
Run this script to test different update scenarios.
"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

try:
    from scripts.updates import UpdateChecker
    from scripts.version import __version__
except ImportError:
    # Fall back to relative import if running as a module
    from ..scripts.updates import UpdateChecker
    from ..scripts.version import __version__

def test_update_check(current_version, force_check=True):
    """Test the update check with a specific version."""
    app = QApplication(sys.argv)
    
    print(f"Testing update check with version: {current_version}")
    
    def on_update_available(update_info):
        print(f"\n=== UPDATE AVAILABLE ===")
        print(f"New version: {update_info['version']}")
        print(f"URL: {update_info['url']}")
        print(f"Published at: {update_info['published_at']}")
        print("\n")
        
        # Show dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Update Available")
        msg.setText(f"Version {update_info['version']} is available!")
        msg.setInformativeText("Would you like to download the latest version?")
        
        download_btn = msg.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
        later_btn = msg.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == download_btn:
            print("User clicked Download")
            # In the real app, this would open the URL in a browser
            print(f"Would open URL: {update_info['url']}")
        else:
            print("User clicked Later")
        
        app.quit()
    
    def on_no_update():
        print("\n=== NO UPDATE AVAILABLE ===")
        print(f"You are running the latest version ({current_version})")
        QMessageBox.information(
            None,
            "No Updates",
            f"You are running the latest version ({current_version}).",
            QMessageBox.StandardButton.Ok
        )
        app.quit()
    
    def on_error(error_msg):
        print(f"\n=== ERROR ===")
        print(f"Update check failed: {error_msg}")
        QMessageBox.warning(
            None,
            "Update Check Failed",
            f"Could not check for updates: {error_msg}",
            QMessageBox.StandardButton.Ok
        )
        app.quit()
    
    # Create and configure the update checker
    checker = UpdateChecker(current_version=current_version)
    checker.update_available.connect(on_update_available)
    checker.no_update_available.connect(on_no_update)
    checker.error_occurred.connect(on_error)
    
    # Start the update check
    print("Starting update check...")
    checker.check_for_updates(force=force_check)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test update check functionality')
    parser.add_argument('--version', type=str, default=__version__,
                       help='Version to test with (default: current version)')
    parser.add_argument('--force', action='store_true',
                       help='Force update check even if recently checked')
    
    args = parser.parse_args()
    
    test_update_check(args.version, args.force)
