"""
UI styling and layout management for STL to GCode Converter.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Initialize CustomTkinter with dark theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class UI:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self._setup_styles()

    def _setup_styles(self):
        """Configure application styles."""
        # Configure main window
        self.root.configure(bg='#2b2b2b')
        
        # Configure buttons
        self.style.configure('TButton', 
                           padding=10,
                           relief='flat',
                           background='#424242',
                           foreground='white')
        
        # Configure labels
        self.style.configure('TLabel', 
                           padding=5,
                           background='#2b2b2b',
                           foreground='white')
        
        # Configure frames
        self.style.configure('TFrame', 
                           background='#2b2b2b')
        
        # Configure progress bar
        self.style.configure('Horizontal.TProgressbar', 
                           background='#007acc',
                           troughcolor='#333333')

    def create_progress_bar(self, parent):
        """Create a progress bar widget."""
        progress = ttk.Progressbar(parent, 
                                 mode='determinate',
                                 style='Horizontal.TProgressbar')
        return progress

    def create_status_bar(self, parent):
        """Create a status bar widget."""
        status = ttk.Label(parent, text="Ready", anchor='w')
        return status

    def create_file_list(self, parent):
        """Create a file list widget."""
        file_list = tk.Listbox(parent, 
                             bg='#333333',
                             fg='white',
                             selectbackground='#007acc')
        return file_list
