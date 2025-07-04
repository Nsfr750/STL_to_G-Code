"""
Main application class for the STL to GCode Converter.

This class manages the main window, UI components, and application logic.
"""
# Set matplotlib backend before importing pyplot
import matplotlib
matplotlib.use('TkAgg')  # Set the backend to TkAgg

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import art3d  # Import art3d for 3D plotting
import threading
from version import get_version, __version__
from about import About
from sponsor import Sponsor
from help import show_help
from updates import check_for_updates
import logging
import os
import sys
import traceback

# Configure tkinter theme with modern styling
style = ttk.Style()
style.theme_use('clam')  # Use the clam theme for better visual appearance
style.configure('TButton', padding=10)  # Add padding to buttons
style.configure('TLabel', padding=5)    # Add padding to labels
style.configure('TFrame', padding=10)   # Add padding to frames
style.configure('TProgressbar', 
                thickness=10,           # Set progress bar thickness
                background='#4a90e2')   # Set progress bar color

class STLToGCodeApp:
    """
    Main application class for STL to GCode Converter.
    
    This class handles:
    - Main window creation and management
    - Menu system setup
    - File operations
    - 3D visualization
    - G-code conversion
    - Status updates
    """
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("STL to GCode Converter")
        self.root.geometry("800x600")
        
        # Setup logging
        self._setup_logging()
        
        # Configure root window
        self.root.configure(bg='SystemButtonFace')
        
        self.file_path = None
        self.progress = None
        self.status_bar = None
        
        # Menu Bar
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)
        
        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open STL File", command=self.open_file)
        self.file_menu.add_command(label="View G-code", command=self.show_gcode_viewer)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)

        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Help", command=lambda: show_help(root))
        self.help_menu.add_command(label="About", command=lambda: About.show_about(root))
        self.help_menu.add_command(label="Sponsor", command=lambda: Sponsor(root).show_sponsor())
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Create main frame with better layout
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # File list
        file_list = tk.Listbox(left_panel, 
                             bg='#333333',
                             fg='white',
                             selectbackground='#007acc')
        file_list.pack(fill=tk.Y, expand=True)
        
        # Buttons frame
        buttons_frame = ttk.Frame(left_panel, style='Buttons.TFrame')
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.open_button = ttk.Button(buttons_frame, text="Open STL File", command=self.open_file)
        self.open_button.pack(fill=tk.X, pady=5)
        
        self.convert_button = ttk.Button(buttons_frame, text="Convert to GCode", 
                                        command=self.convert_to_gcode, 
                                        state=tk.DISABLED)
        self.convert_button.pack(fill=tk.X, pady=5)
        
        # 3D Preview Panel
        preview_frame = ttk.LabelFrame(main_frame, text="3D Preview")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas for 3D preview
        self.figure = plt.figure(figsize=(5, 4))
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.figure, master=preview_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        progress = ttk.Progressbar(main_frame, 
                                 mode='determinate')
        progress.pack(fill=tk.X, pady=(10, 0))
        
        # Status bar
        status = ttk.Label(main_frame, text="Ready", anchor='w', style='Status.TLabel')
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def open_file(self):
        # Open file dialog to select STL file
        file_path = filedialog.askopenfilename(
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path = file_path
            self.load_stl(file_path)
            self.convert_button.config(state=tk.NORMAL)

    def load_stl(self, file_path):
        # Load the STL file and display it
        try:
            stl_mesh = mesh.Mesh.from_file(file_path)
            self.ax.clear()

            # Add STL data to the 3D plot
            self.ax.add_collection3d(
                art3d.Poly3DCollection(stl_mesh.vectors, alpha=0.5)
            )
            self.ax.auto_scale_xyz(stl_mesh.x.flatten(), stl_mesh.y.flatten(), stl_mesh.z.flatten())
            
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load STL file: {e}")

    def convert_to_gcode(self):
        if not self.file_path:
            messagebox.showwarning("No File", "Please load an STL file first.")
            return

        try:
            # Simple example: generate G-code for each triangle in the STL
            stl_mesh = mesh.Mesh.from_file(self.file_path)
            gcode = []

            gcode.append("G21 ; Set units to mm")
            gcode.append("G90 ; Absolute positioning")

            for i, triangle in enumerate(stl_mesh.vectors):
                gcode.append(f"; Triangle {i + 1}")
                for j, vertex in enumerate(triangle):
                    gcode.append(f"G1 X{vertex[0]:.2f} Y{vertex[1]:.2f} Z{vertex[2]:.2f}")
                gcode.append("")

            gcode.append("M30 ; End of program")

            # Save the G-code to a file
            save_path = filedialog.asksaveasfilename(
                defaultextension=".gcode",
                filetypes=[("GCode files", "*.gcode"), ("All files", "*.*")],
            )
            if save_path:
                with open(save_path, "w") as gcode_file:
                    gcode_file.write("\n".join(gcode))
                messagebox.showinfo("Success", "GCode file saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Could not convert to GCode: {e}")

    def show_help(self):
        # Display help information
        messagebox.showinfo("Help", "To use this app:\n1. Load an STL file.\n2. Visualize the 3D model.\n3. Convert to GCode.")

    def show_about(self):
        # Display about information
        About.show_about(self.root)

    def show_sponsor(self):
        Sponsor(self.root).show_sponsor()
        btn2 = tk.Button(dialog, text="Join Discord", pady=5)
        btn3 = tk.Button(dialog, text="Buy Me a Coffee", pady=5)
        btn4 = tk.Button(dialog, text="Join The Patreon", pady=5)
        
        btn_layout = tk.Frame(dialog)
        btn_layout.pack(pady=10)
        
        btn1.pack(side=tk.LEFT)
        btn2.pack(side=tk.LEFT)
        btn3.pack(side=tk.LEFT)
        btn4.pack(side=tk.LEFT)
        
        btn1.config(command=lambda: webbrowser.open("https://github.com/sponsors/Nsfr750"))
        btn2.config(command=lambda: webbrowser.open("https://discord.gg/BvvkUEP9"))
        btn3.config(command=lambda: webbrowser.open("https://paypal.me/3dmega"))
        btn4.config(command=lambda: webbrowser.open("https://www.patreon.com/Nsfr750"))

    def _setup_logging(self):
        """
        Configure application logging system.
        
        Sets up both file and console logging with appropriate format and level.
        """
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stl_to_gcode.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),  # Log to file
                logging.StreamHandler()         # Log to console
            ]
        )
        self.logger = logging.getLogger(__name__)

    def show_gcode_viewer(self):
        """
        Show the G-code viewer window.
        
        Creates a new G-code viewer if it doesn't exist, or brings the existing one to front.
        """
        if not hasattr(self, 'gcode_viewer') or not self.gcode_viewer.window.winfo_exists():
            from gcode_viewer import GCodeViewer
            self.gcode_viewer = GCodeViewer(self.root)
        else:
            self.gcode_viewer.window.lift()

    def check_for_updates(self, force_check: bool = False) -> None:
        """Check for application updates.
        
        Args:
            force_check: If True, skip the cache and force a check.
        """
        try:
            # Import here to avoid circular imports
            from updates import check_for_updates as check_updates
            # Run in a separate thread to avoid freezing the UI
            threading.Thread(
                target=check_updates,
                args=(self.root, __version__, force_check),
                daemon=True
            ).start()
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            messagebox.showerror(
                "Update Error",
                f"Failed to check for updates: {e}",
                parent=self.root
            )

def check_updates_in_background(root):
    """Check for updates in a background thread."""
    try:
        # Only check for updates if the root window is properly initialized
        if root and root.winfo_exists():
            # Check for updates but don't show any messages if no update is available
            update_available, _ = check_for_updates(
                parent=root, 
                current_version=__version__, 
                force_check=False, 
                silent_if_no_update=True
            )
            return update_available
        return False
    except Exception as e:
        # Don't show error messages for failed update checks
        logging.debug(f"Background update check failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    """
    Application entry point.
    
    Creates and runs the main application window.
    Handles keyboard interrupts and other exceptions gracefully.
    """
    try:
        root = tk.Tk()
        app = STLToGCodeApp(root)
        
        # Check for updates in a background thread after a short delay
        # to avoid slowing down the application startup
        root.after(2000, lambda: check_updates_in_background(root))
        
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
        print("\nTraceback:")
        import traceback
        traceback.print_exc()
        print(traceback.format_exc())