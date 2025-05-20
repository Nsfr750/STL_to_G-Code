"""
Sponsor dialog module for the STL to GCode Converter.

This module provides a dialog window with sponsorship options,
allowing users to support the project through various platforms.
"""

import tkinter as tk
import webbrowser

class Sponsor:
    """
    Sponsor dialog class for displaying sponsorship options.
    
    Provides a modal dialog window with buttons linking to various
    sponsorship platforms (GitHub Sponsors, Discord, Patreon, etc.).
    """
    def __init__(self, root):
        """
        Initialize the sponsor dialog.
        
        Args:
            root: The parent Tkinter window
        """
        self.root = root

    def show_sponsor(self):
        """
        Display the sponsor dialog window.
        
        Creates a modal dialog with:
        - Title: "Sponsor the Project"
        - Size: 500x150 pixels
        - Buttons for different sponsorship platforms:
          * GitHub Sponsors
          * Discord
          * PayPal (Buy Me a Coffee)
          * Patreon
        - Close button
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Sponsor the Project")
        dialog.geometry('500x150')
        dialog.transient(self.root)  # Makes dialog modal
        dialog.grab_set()           # Focuses the dialog
        
        # Create frame for sponsor buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        # List of sponsorship options with URLs
        buttons = [
            ("Sponsor on GitHub", "https://github.com/sponsors/Nsfr750"),
            ("Join Discord", "https://discord.gg/BvvkUEP9"),
            ("Buy Me a Coffee", "https://paypal.me/3dmega"),
            ("Join The Patreon", "https://www.patreon.com/Nsfr750")
        ]
        
        # Create buttons for each sponsorship option
        for text, url in buttons:
            btn = tk.Button(btn_frame, 
                          text=text, 
                          pady=5,
                          command=lambda u=url: webbrowser.open(u))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Add close button
        tk.Button(dialog, 
                 text="Close", 
                 command=dialog.destroy).pack(pady=10)

