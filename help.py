"""
Help documentation and user guide for STL to GCode Converter.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import webbrowser
import os

HELP_CONTENT = """
# STL to GCode Converter - User Guide

## Overview
This application converts STL (STereoLithography) files to G-code for 3D printing and CNC machining.

## Features

### File Management
- Open STL files from your system
- Recent files menu for quick access
- File history tracking
- File list display

### 3D Visualization
- Interactive 3D preview of STL models
- Auto-scaling to fit the model
- Improved 3D rendering quality

### G-code Conversion
- Convert STL files to G-code
- Progress tracking during conversion
- Status updates in real-time

## Getting Started

1. Launch the application
2. Use the "Open STL File" button or File menu to select an STL file
3. The model will appear in the 3D preview area
4. The "Convert to GCode" button will become enabled
5. Click "Convert to GCode" to start the conversion process
6. Monitor progress in the status bar and progress bar
7. Once complete, save the G-code file

## Recent Files
Access your recently opened files through the "Recent Files" menu

## Configuration
The application maintains persistent settings including:
- Last opened directory
- Recent files list
- G-code conversion settings
- Window size and position

## Error Handling
The application includes improved error handling with:
- Detailed error messages
- Operation status tracking
- Automatic logging to `stl_to_gcode.log`

## Support

### Getting Help
- Check the [Changelog](./CHANGELOG.md) for recent updates
- View the [License](./LICENSE) for usage rights
- Report issues on the [GitHub repository](https://github.com/Nsfr750/STL_to_G-Code)

### Sponsorship Options
- [GitHub Sponsors](https://github.com/sponsors/Nsfr750)
- [Patreon](https://www.patreon.com/Nsfr750)
- [Discord](https://discord.gg/BvvkUEP9)
- [PayPal](https://paypal.me/3dmega)

### Community
Join our community on:
- [Discord](https://discord.gg/BvvkUEP9)
- [GitHub Discussions](https://github.com/Nsfr750/STL_to_G-Code/discussions)
"""

class HelpDialog:
    def __init__(self, parent):
        """Create a help dialog window."""
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("STL to GCode Converter - Help")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create help text widget
        self.text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=('Helvetica', 10),
            bg='#333333',
            fg='white',
            insertbackground='white'
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # Insert help content
        self.text.insert(tk.END, HELP_CONTENT)
        self.text.configure(state='disabled')  # Make text read-only
        
        # Create buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Close button
        close_btn = ttk.Button(
            buttons_frame,
            text="Close",
            command=self.dialog.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Open GitHub button
        github_btn = ttk.Button(
            buttons_frame,
            text="View on GitHub",
            command=lambda: webbrowser.open("https://github.com/Nsfr750/STL_to_G-Code")
        )
        github_btn.pack(side=tk.RIGHT, padx=5)
        
        # Open Discord button
        discord_btn = ttk.Button(
            buttons_frame,
            text="Join Discord",
            command=lambda: webbrowser.open("https://discord.gg/BvvkUEP9")
        )
        discord_btn.pack(side=tk.RIGHT, padx=5)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)

    def show_help(self):
        """Show the help dialog."""
        self.dialog.deiconify()
        self.dialog.lift()

# Create singleton instance
def show_help(parent):
    """Show the help dialog."""
    HelpDialog(parent).show_help()
