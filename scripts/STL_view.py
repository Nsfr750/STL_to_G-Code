"""
STL visualization module for the STL to GCode Converter.

This module provides functionality for visualizing STL files and infill patterns using matplotlib.
"""
import numpy as np
import os
import logging
from scripts.logger import get_logger
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

# Set up logging
logger = get_logger(__name__)

class STLVisualizer:
    """
    A class to handle visualization of STL files and infill patterns using matplotlib.
    """
    
    def __init__(self, ax, canvas):
        """
        Initialize the STL visualizer.
        
        Args:
            ax: Matplotlib 3D axis object
            canvas: Matplotlib canvas for redrawing
        """
        self.ax = ax
        self.canvas = canvas
        self.vertices = np.zeros((0, 3), dtype=np.float32)
        self.faces = np.zeros((0, 3), dtype=np.uint32)
        self.mesh = None
        self.file_path = None
        self.infill_lines = []  # Store infill line segments
        self.infill_collection = None  # Store the infill Line3DCollection
        self.show_infill = True  # Whether to show infill
        
        # Set up the 3D axes with better default settings
        self._setup_axes()
        
        # Set default visual style
        self.face_color = [0.8, 0.8, 1.0]  # Light blue
        self.edge_color = 'k'  # Black edges
        self.alpha = 0.8  # Slightly transparent
        self.line_width = 0.5
        self.infill_color = [1.0, 0.0, 0.0, 0.6]  # Red with transparency
        self.infill_width = 0.5  # Line width for infill

    def _setup_axes(self):
        """Set up the 3D axes with proper labels and grid."""
        self.ax.clear()
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_zlabel('Z (mm)')
        self.ax.grid(True, alpha=0.5)
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor('w')
        self.ax.yaxis.pane.set_edgecolor('w')
        self.ax.zaxis.pane.set_edgecolor('w')
    
    def update_mesh(self, vertices, faces, file_path=None, is_chunk=False):
        """
        Update the mesh data to be visualized.
        
        Args:
            vertices: Numpy array of vertices (Nx3)
            faces: Numpy array of face indices (Mx3)
            file_path: Optional path to the STL file
            is_chunk: If True, append to existing mesh data
        
        Returns:
            bool: True if the mesh was updated successfully, False otherwise
        """
        try:
            # Convert inputs to numpy arrays if they aren't already
            new_vertices = np.asarray(vertices, dtype=np.float32)
            new_faces = np.asarray(faces, dtype=np.uint32)
            
            if is_chunk and len(self.vertices) > 0:
                # For chunks, append to existing vertices and update face indices
                vertex_offset = len(self.vertices)
                self.vertices = np.vstack([self.vertices, new_vertices])
                self.faces = np.vstack([self.faces, new_faces + vertex_offset])
            else:
                # For new meshes, replace existing data
                self.vertices = new_vertices
                self.faces = new_faces
            
            if file_path:
                self.file_path = str(file_path)
            
            # Update the visualization
            return self._render()
            
        except Exception as e:
            logger.error(f"Error updating mesh: {str(e)}", exc_info=True)
            self._show_error(f"Error updating mesh: {str(e)}")
            return False
    
    def update_infill(self, infill_lines):
        """
        Update the infill lines to be visualized.
        
        Args:
            infill_lines: List of (x1, y1, z1, x2, y2, z2) line segments
        """
        try:
            self.infill_lines = np.array(infill_lines, dtype=np.float32)
            self._render_infill()
            return True
        except Exception as e:
            logger.error(f"Error updating infill: {str(e)}", exc_info=True)
            return False

    def _render_infill(self):
        """Render the infill lines."""
        if not self.show_infill or len(self.infill_lines) == 0:
            if self.infill_collection is not None:
                self.infill_collection.remove()
                self.infill_collection = None
            return
        
        # Create line segments in the correct format for Line3DCollection
        segments = self.infill_lines.reshape(-1, 2, 3)
        
        # Remove existing infill collection if it exists
        if self.infill_collection is not None:
            self.infill_collection.remove()
        
        # Create new line collection
        self.infill_collection = Line3DCollection(
            segments,
            colors=self.infill_color,
            linewidths=self.infill_width,
            linestyles='-',
            alpha=self.infill_color[3] if len(self.infill_color) > 3 else 0.6
        )
        
        # Add to the axes
        self.ax.add_collection3d(self.infill_collection)
        self.canvas.draw_idle()

    def toggle_infill(self, visible=None):
        """
        Toggle infill visibility.
        
        Args:
            visible: If provided, set visibility to this value. Otherwise, toggle.
        """
        if visible is None:
            self.show_infill = not self.show_infill
        else:
            self.show_infill = bool(visible)
        
        self._render_infill()
        return self.show_infill

    def set_infill_style(self, color=None, width=None, alpha=None):
        """
        Set the visual style of the infill.
        
        Args:
            color: RGB or RGBA color tuple/list
            width: Line width
            alpha: Opacity (0-1)
        """
        if color is not None:
            self.infill_color = list(color)
        if width is not None:
            self.infill_width = float(width)
        if alpha is not None and len(self.infill_color) > 3:
            self.infill_color[3] = float(alpha)
        
        self._render_infill()

    def _render(self):
        """Render the current mesh data."""
        try:
            # Clear the previous mesh and set up axes
            self._setup_axes()
            
            # Check if we have valid data
            if len(self.vertices) == 0 or len(self.faces) == 0:
                self._show_message("No mesh data to display")
                return False
                
            # Verify face indices
            if np.any(self.faces >= len(self.vertices)):
                error_msg = f"Invalid face indices: some indices exceed vertex count (max index: {np.max(self.faces)}, num vertices: {len(self.vertices)})"
                logger.error(error_msg)
                self._show_error(error_msg)
                return False
            
            # Create the mesh with improved visual settings
            triangles = self.vertices[self.faces]
            self.mesh = Poly3DCollection(
                triangles,
                alpha=self.alpha,
                linewidths=self.line_width,
                edgecolor=self.edge_color,
                facecolor=self.face_color
            )
            
            # Add the collection to the plot
            self.ax.add_collection3d(self.mesh)
            
            # Auto-scale the view with better margins
            self._auto_scale()
            
            # Set title if we have a file path
            if self.file_path:
                self.ax.set_title(f'STL: {os.path.basename(self.file_path)}')
            
            # Update the display
            self.canvas.draw_idle()
            
            # Re-render infill if needed
            if len(self.infill_lines) > 0:
                self._render_infill()
                
            return True
            
        except Exception as e:
            error_msg = f"Error rendering mesh: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._show_error(error_msg)
            return False

    def _auto_scale(self):
        """Auto-scale the view to fit the mesh with proper aspect ratio."""
        if len(self.vertices) == 0:
            return
            
        min_vals = np.min(self.vertices, axis=0)
        max_vals = np.max(self.vertices, axis=0)
        
        # Calculate the bounding box size
        size = max_vals - min_vals
        
        # Add a 10% margin, but ensure it's at least 1.0
        margin = np.max(size) * 0.1
        margin = max(margin, 1.0)
        
        # Calculate center point
        center = (min_vals + max_vals) / 2
        
        # Calculate new bounds
        half_size = np.max(size) / 2 + margin
        new_min = center - half_size
        new_max = center + half_size
        
        # Apply new bounds with equal aspect ratio
        self.ax.set_xlim(new_min[0], new_max[0])
        self.ax.set_ylim(new_min[1], new_max[1])
        self.ax.set_zlim(new_min[2], new_max[2])
        
        # Set equal aspect ratio
        self.ax.set_box_aspect([1, 1, 1])
    
    def clear(self):
        """Clear the visualization."""
        self.vertices = np.zeros((0, 3), dtype=np.float32)
        self.faces = np.zeros((0, 3), dtype=np.uint32)
        self.mesh = None
        self.file_path = None
        self.infill_lines = []
        self.infill_collection = None
        
        self._setup_axes()
        
        try:
            self.canvas.draw_idle()
        except Exception as e:
            logger.warning(f"Error updating canvas: {str(e)}")
    
    def toggle_wireframe(self, show):
        """
        Toggle wireframe visibility.
        
        Args:
            show: If True, show wireframe; if False, hide it
        """
        if self.mesh is not None:
            self.mesh.set_edgecolor(self.edge_color if show else 'none')
            try:
                self.canvas.draw_idle()
            except Exception as e:
                logger.warning(f"Error updating wireframe: {str(e)}")
    
    def _show_error(self, message):
        """Display an error message in the plot area."""
        self._show_message(message, 'red')
    
    def _show_message(self, message, color='black'):
        """
        Display a message in the plot area.
        
        Args:
            message: The message to display
            color: The color of the message text
        """
        try:
            self.ax.clear()
            self.ax.set_axis_off()
            
            # Use text2D for proper positioning in 3D axes
            self.ax.text2D(
                0.5, 0.5, message,
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.ax.transAxes,
                color=color,
                fontsize=12
            )
            self.canvas.draw_idle()
        except Exception as e:
            logger.error(f"Error displaying message: {str(e)}", exc_info=True)
