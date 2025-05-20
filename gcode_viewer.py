import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import re

class GCodeViewer:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("G-code Viewer")
        self.window.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Open button
        ttk.Button(controls_frame, text="Open G-code File", command=self.open_file).pack(side=tk.LEFT)
        
        # Line number display
        self.line_label = ttk.Label(controls_frame, text="Line: 1")
        self.line_label.pack(side=tk.RIGHT)
        
        # Create text widget with scrollbar
        self.text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.NONE)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure text widget
        self.text_widget.configure(font=('Consolas', 10))
        self.text_widget.tag_configure('command', foreground='blue')
        self.text_widget.tag_configure('comment', foreground='gray')
        self.text_widget.tag_configure('number', foreground='green')
        
        # Bind events
        self.text_widget.bind('<Key>', lambda e: 'break')  # Disable editing
        self.text_widget.bind('<Button-1>', self.update_line_number)
        
        # Add line numbers
        self.add_line_numbers()
        
    def open_file(self):
        """Open a G-code file."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Open G-code File",
            filetypes=[("G-code Files", "*.gcode *.g *.nc"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.display_gcode(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
                
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
            
        except Exception as e:
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
                    self.text_widget.insert(tk.END, ' ' + params)
            
            self.text_widget.insert(tk.END, '\n')
            
    def update_line_number(self, event):
        """Update line number display."""
        line = self.text_widget.index(tk.CURRENT).split('.')[0]
        self.line_label.config(text=f"Line: {line}")
        
    def add_line_numbers(self):
        """Add line numbers to the text widget."""
        # Create a frame for line numbers
        line_frame = ttk.Frame(self.text_widget, width=40)
        line_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create a canvas for line numbers
        line_canvas = tk.Canvas(line_frame, width=40, bg='white')
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
                    fill='gray'
                )
        
        self.text_widget.bind('<Configure>', update_line_numbers)
        self.text_widget.bind('<MouseWheel>', update_line_numbers)
        self.text_widget.bind('<Button-4>', update_line_numbers)
        self.text_widget.bind('<Button-5>', update_line_numbers)
