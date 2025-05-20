import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import re
import json
from pathlib import Path
from datetime import datetime
import logging

class GCodeViewer:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("G-code Viewer")
        self.window.geometry("1000x800")
        
        # Configure style
        style = ttk.Style()
        style.configure("Custom.TFrame", background="#f0f0f0")
        style.configure("Custom.TButton", padding=6)
        style.configure("Custom.TLabel", padding=3)
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10", style="Custom.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create controls frame
        controls_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File controls
        ttk.Button(controls_frame, text="Open G-code File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Save As", command=self.save_file).pack(side=tk.LEFT, padx=5)
        
        # Search controls
        search_frame = ttk.Frame(controls_frame, style="Custom.TFrame")
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="Find", command=self.search_text).pack(side=tk.LEFT)
        
        # Line number display
        self.line_label = ttk.Label(controls_frame, text="Line: 1", style="Custom.TLabel")
        self.line_label.pack(side=tk.RIGHT, padx=5)
        
        # Create text widget with scrollbar
        self.text_widget = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.NONE,
            font=('Consolas', 14),
            bg='#2b2b2b',
            fg='white',
            insertbackground='white'
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure text widget
        self.text_widget.tag_configure('command', foreground='#007acc')
        self.text_widget.tag_configure('comment', foreground='#6a6a6a')
        self.text_widget.tag_configure('number', foreground='#70c070')
        self.text_widget.tag_configure('selected', background='#3c3f41')
        
        # Add line numbers
        self.add_line_numbers()
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, style="Custom.TLabel")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Bind events
        self.text_widget.bind('<Key>', lambda e: 'break')  # Disable editing
        self.text_widget.bind('<Button-1>', self.update_line_number)
        self.text_widget.bind('<Control-f>', lambda e: self.search_text())
        self.text_widget.bind('<Control-s>', lambda e: self.save_file())
        
        # Initialize logger
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging."""
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gcode_viewer.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def open_file(self):
        """Open a G-code file."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Open G-code File",
            filetypes=[
                ("G-code Files", "*.gcode *.g *.nc"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.display_gcode(file_path)
                self.logger.info(f"Opened G-code file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error opening file: {str(e)}")
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
                
    def save_file(self):
        """Save the current G-code content."""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="Save G-code File",
            defaultextension=".gcode",
            filetypes=[
                ("G-code Files", "*.gcode"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                content = self.text_widget.get('1.0', tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"Saved G-code file: {file_path}")
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                self.logger.error(f"Error saving file: {str(e)}")
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def search_text(self):
        """Search for text in the G-code."""
        search_text = self.search_var.get().strip()
        if not search_text:
            return
            
        # Clear previous search highlights
        self.text_widget.tag_remove('selected', '1.0', tk.END)
        
        # Find and highlight matches
        start = '1.0'
        while True:
            start = self.text_widget.search(search_text, start, stopindex=tk.END)
            if not start:
                break
                
            end = f"{start}+{len(search_text)}c"
            self.text_widget.tag_add('selected', start, end)
            start = end
            
    def display_gcode(self, file_path):
        """Display G-code content in the viewer."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Clear existing content
            self.text_widget.delete('1.0', tk.END)
            
            # Highlight syntax
            self.highlight_gcode(content)
            
            # Update window title
            self.window.title(f"G-code Viewer - {os.path.basename(file_path)}")
            
            # Update status
            line_count = len(content.split('\n'))
            self.status_var.set(f"{line_count} lines - {len(content)} characters")
            
        except Exception as e:
            self.logger.error(f"Error reading file: {str(e)}")
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")
            
    def highlight_gcode(self, content):
        """Highlight G-code syntax."""
        lines = content.split('\n')
        for line in lines:
            if not line.strip():
                self.text_widget.insert(tk.END, line + '\n')
                continue
                
            # Remove comments
            comment_pos = line.find('(')
            if comment_pos != -1:
                comment = line[comment_pos:]
                line = line[:comment_pos]
                self.text_widget.insert(tk.END, comment, 'comment')
                
            # Split into command and parameters
            parts = line.split(None, 1)
            if parts:
                command = parts[0]
                params = parts[1] if len(parts) > 1 else ''
                
                # Add command
                self.text_widget.insert(tk.END, command, 'command')
                
                # Add parameters
                if params:
                    # Highlight numbers
                    numbers = re.findall(r'\d+(\.\d+)?', params)
                    current_pos = 0
                    for num in numbers:
                        start = params.find(num, current_pos)
                        end = start + len(num)
                        before = params[current_pos:start]
                        self.text_widget.insert(tk.END, before)
                        self.text_widget.insert(tk.END, num, 'number')
                        current_pos = end
                    self.text_widget.insert(tk.END, params[current_pos:])
            
            self.text_widget.insert(tk.END, '\n')
            
    def update_line_number(self, event):
        """Update line number display."""
        line = self.text_widget.index(tk.CURRENT).split('.')[0]
        self.line_label.config(text=f"Line: {line}")
        
    def add_line_numbers(self):
        """Add line numbers to the text widget."""
        # Create a canvas for line numbers
        line_canvas = tk.Canvas(self.text_widget, width=40, bg='#2b2b2b', highlightthickness=0)
        line_canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        # Update line numbers when scrolling
        def update_line_numbers(event=None):
            line_count = int(self.text_widget.index('end-1c').split('.')[0])
            line_canvas.delete('all')
            
            for i in range(1, line_count + 1):
                line_canvas.create_text(
                    20,
                    i * 20,
                    text=str(i),
                    anchor='e',
                    fill='#808080'
                )
        
        self.text_widget.bind('<Configure>', update_line_numbers)
        self.text_widget.bind('<MouseWheel>', update_line_numbers)
        self.text_widget.bind('<Button-4>', update_line_numbers)
        self.text_widget.bind('<Button-5>', update_line_numbers)
