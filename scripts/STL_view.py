"""
STL visualization module for the STL to GCode Converter.

This module provides functionality for visualizing STL files using matplotlib.
"""
import numpy as np
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Check for OpenGL availability
def is_opengl_available():
    """Check if OpenGL is available in the current environment."""
    try:
        from PyQt6.QtOpenGL import QOpenGLContext
        from PyQt6.QtGui import QSurfaceFormat
        return True
    except (ImportError, AttributeError):
        return False

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
        self.use_opengl = is_opengl_available()
        
        if not self.use_opengl:
            logger.warning("OpenGL not available. Using software rendering.")
    
    def _create_opengl_widget(self):
        """Create an OpenGL widget if available, return None otherwise."""
        if not self.use_opengl:
            return None
            
        try:
            from PyQt6.QtOpenGL import QOpenGLWidget
            from PyQt6.QtGui import QSurfaceFormat
            
            format = QSurfaceFormat()
            format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
            format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            format.setVersion(3, 3)
            
            widget = QOpenGLWidget()
            widget.setFormat(format)
            return widget
        except Exception as e:
            logger.warning(f"Failed to create OpenGL widget: {str(e)}")
            self.use_opengl = False
            return None

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
                faces = np.asarray(faces, dtype=np.int32)
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting input data: {str(e)}")
                self._show_error_message("Invalid mesh data format")
                return False
            
            # Validate input data types and shapes
            if len(vertices) == 0 or len(faces) == 0:
                error_msg = "No vertex or face data provided"
                logger.error(error_msg)
                self._show_error_message(error_msg)
                return False
                
            if len(vertices.shape) != 2 or vertices.shape[1] != 3:
                error_msg = f"Invalid vertices shape: expected (N,3), got {vertices.shape}"
                logger.error(error_msg)
                self._show_error_message(error_msg)
                return False
                
            if len(faces.shape) != 2 or faces.shape[1] != 3:
                error_msg = f"Invalid faces shape: expected (M,3), got {faces.shape}"
                logger.error(error_msg)
                self._show_error_message(error_msg)
                return False
            
            # Create a copy of faces to avoid modifying the input
            faces = faces.copy()
            num_vertices = len(vertices)
            
            # Check for invalid face indices (negative or >= num_vertices)
            # Convert to int64 to handle potential large indices
            faces = faces.astype(np.int64)
            valid_faces_mask = (faces >= 0) & (faces < num_vertices)
            valid_faces = np.all(valid_faces_mask, axis=1)
            
            if not np.any(valid_faces):
                error_msg = "No valid faces found in the mesh"
                logger.error(error_msg)
                self._show_error_message(error_msg)
                return False
                
            if not np.all(valid_faces):
                invalid_count = len(faces) - np.sum(valid_faces)
                logger.warning(f"Found {invalid_count} faces with invalid vertex indices. Filtering out invalid faces...")
                
                # Keep only valid faces
                faces = faces[valid_faces]
                logger.info(f"Kept {len(faces)} valid faces out of {len(valid_faces) + invalid_count}")
                
                if len(faces) == 0:
                    error_msg = "No valid faces remaining after filtering"
                    logger.error(error_msg)
                    self._show_error_message(error_msg)
                    return False
            
            # Get all unique vertex indices used in faces
            used_vertex_indices = np.unique(faces)
            
            # Create a mapping from old indices to new contiguous indices
            max_vertex_idx = np.max(used_vertex_indices) + 1 if len(used_vertex_indices) > 0 else 0
            index_map = np.full(max_vertex_idx, -1, dtype=np.int32)
            index_map[used_vertex_indices] = np.arange(len(used_vertex_indices), dtype=np.int32)
            
            # Remap face indices
            try:
                remapped_faces = index_map[faces]
                
                # Verify the remapping was successful
                if np.any(remapped_faces < 0):
                    error_msg = "Error in face index remapping: invalid indices detected"
                    logger.error(error_msg)
                    self._show_error_message(error_msg)
                    return False
                
                # Extract only the used vertices
                used_vertices = vertices[used_vertex_indices]
                
                # Update the mesh data
                self.current_vertices = used_vertices.astype(np.float32)
                self.current_faces = remapped_faces.astype(np.uint32)
                
                if file_path:
                    self.file_path = str(file_path)
                    
                logger.info(f"Updated mesh with {len(self.current_vertices)} vertices and {len(self.current_faces)} faces")
                return True
                
            except IndexError as e:
                error_msg = f"Error remapping face indices: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._show_error_message("Error processing mesh indices")
                return False
                
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
                msg = f"Invalid face indices: Max index {max_vertex_idx} exceeds vertex count {len(self.current_vertices)}"
                logger.error(msg)
                self._show_error_message("Invalid mesh data: face indices out of range")
                return False
                
            try:
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                
                # Create a Poly3DCollection with the valid faces
                try:
                    verts = self.current_vertices[self.current_faces]
                    
                    # Use software rendering (more reliable)
                    mesh = Poly3DCollection(verts, alpha=0.5, linewidths=0.5, edgecolor='k')
                    mesh.set_facecolor([0.7, 0.7, 1.0])  # Light blue color
                    self.ax.add_collection3d(mesh)
                    
                    # Auto-scale the plot to fit the mesh
                    min_vals = np.min(self.current_vertices, axis=0)
                    max_vals = np.max(self.current_vertices, axis=0)
                    
                    # Add a small margin
                    bounds = max_vals - min_vals
                    margin = np.max(bounds) * 0.1 if np.any(bounds > 0) else 1.0
                    
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
                    logger.error(f"Error creating 3D visualization: {str(e)}", exc_info=True)
                    self._show_error_message("Error creating 3D visualization")
                    return False
                
            except ImportError:
                error_msg = "Required 3D visualization libraries not available"
                logger.error(error_msg, exc_info=True)
                self._show_error_message(error_msg)
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error in render: {str(e)}", exc_info=True)
            self._show_error_message(f"Rendering error: {str(e)}")
            return False
    
    def _show_error_message(self, message):
        """Display an error message in the plot area."""
        try:
            self.ax.clear()
            self.ax.set_axis_off()
            
            # Use text2D for 3D axes
            self.ax.text2D(0.5, 0.5, message,
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        bbox=dict(facecolor='red', alpha=0.7, boxstyle='round,pad=0.5'),
                        wrap=True)
            
            # Set the 3D view to be orthogonal and zoomed out for better text visibility
            self.ax.set_xlim(-1, 1)
            self.ax.set_ylim(-1, 1)
            self.ax.set_zlim(-1, 1)
            
            # Force a draw to update the display
            self.canvas.draw_idle()
        except Exception as e:
            # If we can't show the error in the plot, log it to the console
            logger.error(f"Error displaying error message: {str(e)}", exc_info=True)
            try:
                # Try a simpler approach as fallback
                print(f"Error: {message}")
            except:
                pass  # If even basic printing fails, give up
