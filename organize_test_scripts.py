"""
Script to organize test scripts into a test_scripts directory and update their imports.
Run this script from the root directory of the project.
"""
import os
import shutil
from pathlib import 
from scripts.logger import get_loggerPath

def create_directory(directory):
    """Create a directory if it doesn't exist."""
    try:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False

def move_file(src, dest_dir):
    """Move a file to the destination directory."""
    try:
        dest = os.path.join(dest_dir, os.path.basename(src))
        shutil.move(src, dest)
        print(f"Moved: {src} -> {dest}")
        return dest
    except Exception as e:
        print(f"Error moving {src}: {e}")
        return None

def update_imports(file_path):
    """Update imports in the test script to work from the new location."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update imports that point to scripts directory
        updated_content = content.replace(
            'from scripts.', 'from ..scripts.'
        )
        
        # Write back the updated content
        if content != updated_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated imports in: {file_path}")
        return True
    except Exception as e:
        print(f"Error updating imports in {file_path}: {e}")
        return False

def main():
    """Main function to organize test scripts."""
    # Define paths
    root_dir = os.path.dirname(os.path.abspath(__file__))
    test_scripts_dir = os.path.join(root_dir, 'test_scripts')
    scripts_dir = os.path.join(root_dir, 'scripts')
    
    # Test files to move
    test_files = [
        os.path.join(root_dir, 'test_stl_loading.py'),
        os.path.join(root_dir, 'test_update_check.py'),
        os.path.join(scripts_dir, 'test_gcode_custom_commands.py'),
        os.path.join(scripts_dir, 'test_gcode_simulator.py')
    ]
    
    # Create test_scripts directory
    if not create_directory(test_scripts_dir):
        return
    
    # Process each test file
    for test_file in test_files:
        if os.path.exists(test_file):
            # Move the file
            dest_file = move_file(test_file, test_scripts_dir)
            if dest_file:
                # Update imports in the moved file
                update_imports(dest_file)
    
    print("\nTest scripts have been organized into the test_scripts directory.")
    print("You can now run them using: python -m test_scripts.test_script_name")

if __name__ == "__main__":
    main()
