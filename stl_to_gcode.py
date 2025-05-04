import tkinter as tk
from tkinter import filedialog, messagebox
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import art3d  # Import art3d for 3D plotting
import webbrowser


class STLToGCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STL to GCode Converter")
        
        self.file_path = None

        # Menu Bar
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open STL File", command=self.open_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Help", command=self.show_help)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Sponsor", command=self.show_sponsor)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Buttons
        self.open_button = tk.Button(root, text="Open STL File", command=self.open_file)
        self.open_button.pack(pady=10)

        self.convert_button = tk.Button(root, text="Convert to GCode", command=self.convert_to_gcode, state=tk.DISABLED)
        self.convert_button.pack(pady=10)

        # Canvas for 3D preview
        self.figure = plt.figure(figsize=(5, 4))
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()

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
        messagebox.showinfo("About", "STL to GCode Converter v1.2\nDeveloped by Nsfr750")

    def show_sponsor(self):
        # Display sponsor information and open links
        sponsor_message = (
            "Support the project by sponsoring on various platforms:\n\n"
            "1. Patreon: Exclusive benefits for members.\n"
            "2. GitHub Sponsor: Support the development directly.\n"
            "3. Discord: Join the community!"
        )
        if messagebox.askyesno("Sponsor", sponsor_message + "\n\nWould you like to visit the sponsorship page?"):
            # Open the GitHub Sponsors page
            webbrowser.open("https://github.com/sponsors/Nsfr750")


if __name__ == "__main__":
    root = tk.Tk()
    app = STLToGCodeApp(root)
    root.mainloop()