"""
About dialog module for the STL to GCode Converter application.

This module provides the About dialog window that displays application information,
version details, and copyright notice.
"""
import tkinter as tk
from tkinter import ttk
from version import get_version

class About:
    """
    Static class for managing the About dialog window.
    
    Provides a method to display the About dialog with application information.
    """
    @staticmethod
    def show_about(root):
        """
        Display the About dialog window.
        
        Args:
            root: The parent Tkinter window
            
        Creates a modal dialog window containing:
        - Application title
        - Version information
        - Description
        - Copyright notice
        - Close button
        """
        about_dialog = tk.Toplevel(root)
        about_dialog.title('About STL to GCode Converter')
        about_dialog.geometry('400x300')
        about_dialog.transient(root)  # Makes dialog modal
        about_dialog.grab_set()      # Focuses the dialog

        # Application title with larger font
        title = ttk.Label(about_dialog, 
                         text='STL to GCode Converter', 
                         font=('Helvetica', 16, 'bold'))
        title.pack(pady=20)  # Add padding around the title

        # Version label using version from version.py
        version = ttk.Label(about_dialog, text=f'Version {get_version()}')
        version.pack()

        # Description label
        description = ttk.Label(about_dialog, 
                              text='A simple STL to GCode Converter.', 
                              justify=tk.CENTER)
        description.pack(pady=20)

        # Copyright notice
        copyright = ttk.Label(about_dialog, text=' 2025 Nsfr750')
        copyright.pack(pady=10)

        # Close button to dismiss the dialog
        ttk.Button(about_dialog, 
                  text='Close', 
                  command=about_dialog.destroy).pack(pady=20)
