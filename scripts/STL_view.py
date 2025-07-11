"""
STL visualization module for the STL to GCode Converter.

This module provides functionality for visualizing STL files using matplotlib.
"""
import numpy as np
import os
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Set up logging
import logging
logger = logging.getLogger(__name__)

class STLVisualizer:
    """
    A class to handle visualization of STL files using matplotlib.
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
        self.current_vertices = np.zeros((0, 3), dtype=np.float32)
        self.current_faces = np.zeros((0, 3), dtype=np.uint32)
        self.file_path = None
        
    def update_mesh(self, vertices, faces, file_path=None):
        """
        Update the mesh data to be visualized.
        
        Args:
            vertices: Numpy array of vertices (Nx3)
            faces: Numpy array of face indices (Mx3)
            file_path: Optional path to the STL file
            
        Returns:
            bool: True if the mesh was updated successfully, False otherwise
        """
        try:
            # Convert inputs to numpy arrays if they aren't already
            try:
                vertices = np.asarray(vertices, dtype=np.float32)
                faces = np.asarray(faces, dtype=np.uint32)
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting input data: {str(e)}")
                self._show_error_message("Invalid mesh data format")
                return False
            
            # Validate input data types and shapes
            if len(vertices) == 0:
                logger.error("No vertices provided")
                self._show_error_message("No vertex data found in the file")
                return False
                
            if len(vertices.shape) != 2 or vertices.shape[1] != 3:
                logger.error(f"Invalid vertices shape: expected (N,3), got {vertices.shape}")
                self._show_error_message(f"Invalid vertex data format: expected (N,3), got {vertices.shape}")
                return False
                
            if len(faces) == 0:
                logger.error("No faces provided")
                self._show_error_message("No face data found in the file")
                return False
                
            if len(faces.shape) != 2 or faces.shape[1] != 3:
                logger.error(f"Invalid faces shape: expected (M,3), got {faces.shape}")
                self._show_error_message(f"Invalid face data format: expected (M,3), got {faces.shape}")
                return False
            
            # Create a copy of faces to avoid modifying the input
            faces = faces.copy()
            num_vertices = len(vertices)
            
            # Check for invalid face indices
            max_vertex_idx = np.max(faces) if len(faces) > 0 else -1
            min_vertex_idx = np.min(faces) if len(faces) > 0 else 0
            
            if max_vertex_idx >= num_vertices or min_vertex_idx < 0:
                logger.warning(f"Found face indices out of bounds. Vertex count: {num_vertices}, "
                             f"Face index range: [{min_vertex_idx}, {max_vertex_idx}]")
                
                # Create a mapping of old vertex indices to new ones
                used_vertices = np.unique(faces)
                valid_vertices = (used_vertices >= 0) & (used_vertices < num_vertices)
                used_vertices = used_vertices[valid_vertices]
                
                if len(used_vertices) == 0:
                    logger.error("No valid vertex indices found in face data")
                    self._show_error_message("No valid vertex indices found in face data")
                    return False
                
                # Create new vertex array with only used vertices
                new_vertices = vertices[used_vertices]
                
                # Create mapping from old indices to new indices
                index_map = {old_idx: new_idx for new_idx, old_idx in enumerate(used_vertices)}
                
                # Create new face array with remapped indices
                valid_faces = []
                for face in faces:
                    if np.all((face >= 0) & (face < num_vertices)):
                        valid_faces.append([index_map[idx] for idx in face])
                
                if not valid_faces:
                    logger.error("No valid faces after remapping vertex indices")
                    self._show_error_message("No valid faces after processing vertex indices")
                    return False
                
                # Update vertices and faces with the remapped data
                self.current_vertices = np.array(new_vertices, dtype=np.float32)
                self.current_faces = np.array(valid_faces, dtype=np.uint32)
                
                logger.info(f"Remapped vertex indices. New mesh has {len(self.current_vertices)} "
                           f"vertices and {len(self.current_faces)} faces")
            else:
                # All indices are valid, use the data as-is
                self.current_vertices = vertices
                self.current_faces = faces
            
            if file_path:
                self.file_path = str(file_path)
                
            logger.info(f"Updated mesh with {len(self.current_vertices)} vertices and {len(self.current_faces)} faces")
            return True
            
        except Exception as e:
            error_msg = f"Error updating mesh: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._show_error_message(f"Error processing mesh: {str(e)}")
            return False

    def clear(self):
        """Clear the current visualization."""
        self.current_vertices = np.zeros((0, 3), dtype=np.float32)
        self.current_faces = np.zeros((0, 3), dtype=np.uint32)
        self.file_path = None
    
    def render(self):
        """
        Render the STL visualization.
        
        Returns:
            bool: True if rendering was successful, False otherwise
        """
        try:
            # Clear the current plot
            self.ax.clear()
            
            # Set up the 3D axes with default labels
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')
            
            # Check if we have valid data to visualize
            if len(self.current_vertices) == 0 or len(self.current_faces) == 0:
                msg = "No valid mesh data to render"
                logger.warning(msg)
                self._show_error_message(msg)
                return False
            
            # Verify all face indices are valid before rendering
            max_vertex_idx = np.max(self.current_faces) if len(self.current_faces) > 0 else -1
            if max_vertex_idx >= len(self.current_vertices):
                msg = f"Invalid STL file: Face indices reference non-existent vertices\n" \
                      f"Max vertex index: {max_vertex_idx}, Number of vertices: {len(self.current_vertices)}"
                logger.error(msg)
                self._show_error_message(msg)
                return False
                
            try:
                # Create a Poly3DCollection with the valid faces
                verts = self.current_vertices[self.current_faces]
                mesh = Poly3DCollection(verts, alpha=0.5, linewidths=0.5, edgecolor='k')
                mesh.set_facecolor([0.7, 0.7, 1.0])  # Light blue color
                self.ax.add_collection3d(mesh)
                
                # Auto-scale the plot to fit the mesh
                min_vals = np.min(self.current_vertices, axis=0)
                max_vals = np.max(self.current_vertices, axis=0)
                
                # Add a small margin
                margin = np.max((max_vals - min_vals)) * 0.1 if len(self.current_vertices) > 0 else 1.0
                self.ax.set_xlim([min_vals[0] - margin, max_vals[0] + margin])
                self.ax.set_ylim([min_vals[1] - margin, max_vals[1] + margin])
                self.ax.set_zlim([min_vals[2] - margin, max_vals[2] + margin])
                
                # Set a title if we have a file path
                if self.file_path:
                    self.ax.set_title(f'STL: {os.path.basename(self.file_path)}')
                
                # Redraw the canvas
                self.canvas.draw()
                return True
                
            except Exception as e:
                msg = f"Error rendering STL: {str(e)}"
                logger.error(msg, exc_info=True)
                self._show_error_message(msg)
                return False
                
        except Exception as e:
            msg = f"Unexpected error in render: {str(e)}"
            logger.error(msg, exc_info=True)
            self._show_error_message(msg)
            return False
            
    def _show_error_message(self, message):
        """Helper method to display an error message in the plot."""
        try:
            self.ax.clear()
            self.ax.set_axis_off()
            
            # Add text in the center of the plot
            self.ax.text(0.5, 0.5, message,
                       horizontalalignment='center',
                       verticalalignment='center',
                       transform=self.ax.transAxes,
                       bbox=dict(facecolor='red', alpha=0.5, boxstyle='round,pad=0.5'))
            
            # Adjust the plot to make sure text is visible
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Error displaying error message: {str(e)}", exc_info=True)
