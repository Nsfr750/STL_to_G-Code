#!/usr/bin/env python3
"""
Test script for loading and visualizing STL files using matplotlib.

Usage:
    python -m test_scripts.test_stl_loading [path_to_stl_file]
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import Button, Slider
import logging
from scripts.logger import get_logger
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

class STLViewer:
    """Simple STL file viewer using matplotlib."""
    
    def __init__(self, stl_file=None):
        """Initialize the STL viewer."""
        self.stl_file = stl_file
        self.vertices = None
        self.faces = None
        self.mesh = None
        
        # Set up the figure and 3D axis
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Add some space for controls
        plt.subplots_adjust(bottom=0.2)
        
        # Initialize the viewer
        self._init_ui()
        
        # Load the STL file if provided
        if self.stl_file and os.path.exists(self.stl_file):
            self.load_stl(self.stl_file)
    
    def _init_ui(self):
        """Initialize the user interface controls."""
        # Add buttons
        ax_load = plt.axes([0.1, 0.05, 0.15, 0.075])
        btn_load = Button(ax_load, 'Load STL')
        btn_load.on_clicked(self._on_load_clicked)
        
        # Add rotation sliders
        ax_rot_x = plt.axes([0.3, 0.1, 0.5, 0.03])
        ax_rot_y = plt.axes([0.3, 0.06, 0.5, 0.03])
        ax_rot_z = plt.axes([0.3, 0.02, 0.5, 0.03])
        
        self.slider_rot_x = Slider(ax_rot_x, 'Rot X', -180, 180, valinit=0)
        self.slider_rot_y = Slider(ax_rot_y, 'Rot Y', -180, 180, valinit=0)
        self.slider_rot_z = Slider(ax_rot_z, 'Rot Z', -180, 180, valinit=0)
        
        # Connect sliders to update function
        self.slider_rot_x.on_changed(self._update_rotation)
        self.slider_rot_y.on_changed(self._update_rotation)
        self.slider_rot_z.on_changed(self._update_rotation)
        
        # Set up the 3D axes
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_zlabel('Z (mm)')
        self.ax.grid(True)
    
    def _on_load_clicked(self, event):
        """Handle load button click."""
        from tkinter import Tk, filedialog
        
        # Create a root window and hide it
        root = Tk()
        root.withdraw()
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select STL file",
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_stl(file_path)
    
    def load_stl(self, file_path):
        """Load an STL file and update the visualization."""
        try:
            logger.info(f"Loading STL file: {file_path}")
            
            # Try to use numpy-stl if available
            try:
                from stl import mesh as stl_mesh
                stl_mesh = stl_mesh.Mesh.from_file(file_path)
                self.vertices = stl_mesh.vectors.reshape(-1, 3)
                self.faces = np.arange(len(self.vertices)).reshape(-1, 3)
                logger.info(f"Loaded {len(self.faces)} faces using numpy-stl")
            except ImportError:
                logger.warning("numpy-stl not found, using simple STL parser")
                self.vertices, self.faces = self._parse_stl_ascii(file_path)
            
            self._update_plot()
            
        except Exception as e:
            logger.error(f"Error loading STL file: {e}")
            self._show_error(f"Error loading STL file: {e}")
    
    def _parse_stl_ascii(self, file_path):
        """Simple ASCII STL parser as a fallback."""
        vertices = []
        faces = []
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('vertex'):
                # Read 3 vertices to form a triangle face
                v1 = list(map(float, line.split()[1:4]))
                v2 = list(map(float, lines[i+1].strip().split()[1:4]))
                v3 = list(map(float, lines[i+2].strip().split()[1:4]))
                
                # Add vertices and face
                start_idx = len(vertices)
                vertices.extend([v1, v2, v3])
                faces.append([start_idx, start_idx+1, start_idx+2])
                i += 3
            else:
                i += 1
        
        return np.array(vertices, dtype=np.float32), np.array(faces, dtype=np.uint32)
    
    def _update_plot(self):
        """Update the 3D plot with the current mesh."""
        if self.vertices is None or self.faces is None:
            return
        
        # Clear previous plot
        self.ax.clear()
        
        # Create a collection of polygons from the faces
        verts = self.vertices[self.faces]
        
        # Create the 3D polygon collection
        self.mesh = Poly3DCollection(
            verts,
            alpha=0.8,
            linewidths=0.5,
            edgecolor='k',
            facecolor='lightblue'
        )
        
        # Add the collection to the plot
        self.ax.add_collection3d(self.mesh)
        
        # Auto-scale the plot
        self.ax.auto_scale_xyz(
            [self.vertices[:, 0].min(), self.vertices[:, 0].max()],
            [self.vertices[:, 1].min(), self.vertices[:, 1].max()],
            [self.vertices[:, 2].min(), self.vertices[:, 2].max()]
        )
        
        # Update the plot
        self.fig.canvas.draw_idle()
    
    def _update_rotation(self, val):
        """Update the mesh rotation based on slider values."""
        if self.vertices is None:
            return
        
        # Get rotation angles in radians
        rx = np.radians(self.slider_rot_x.val)
        ry = np.radians(self.slider_rot_y.val)
        rz = np.radians(self.slider_rot_z.val)
        
        # Create rotation matrices
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx), np.cos(rx)]
        ])
        
        Ry = np.array([
            [np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)]
        ])
        
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz), np.cos(rz), 0],
            [0, 0, 1]
        ])
        
        # Combine rotations
        R = Rz @ Ry @ Rx
        
        # Rotate vertices
        rotated_vertices = (R @ self.vertices.T).T
        
        # Update the plot
        self.mesh.set_verts(rotated_vertices[self.faces])
        self.fig.canvas.draw_idle()
    
    def _show_error(self, message):
        """Display an error message on the plot."""
        self.ax.clear()
        self.ax.text(
            0.5, 0.5, message,
            horizontalalignment='center',
            verticalalignment='center',
            transform=self.ax.transAxes,
            color='red',
            fontsize=12
        )
        self.fig.canvas.draw_idle()
    
    def show(self):
        """Show the plot."""
        plt.show()

def main():
    """Main function to run the STL viewer."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='STL File Viewer with Matplotlib')
    parser.add_argument('stl_file', nargs='?', help='Path to STL file (optional)')
    args = parser.parse_args()
    
    # Create and show the viewer
    viewer = STLViewer(args.stl_file)
    viewer.show()

if __name__ == "__main__":
    main()
