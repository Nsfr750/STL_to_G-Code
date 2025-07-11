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
        # First try importing PyQt6's OpenGL module
        from PyQt6.QtOpenGL import QOpenGLWidget
        from PyQt6.QtGui import QSurfaceFormat
        
        # Then try importing PyOpenGL
        try:
            from OpenGL import GL
            import OpenGL.error
            
            # Test creating a simple OpenGL context
            format = QSurfaceFormat()
            format.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
            format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            format.setVersion(3, 3)
            
            # Test creating a widget (but don't show it)
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            widget = QOpenGLWidget()
            widget.setFormat(format)
            widget.makeCurrent()
            
            # Test a simple OpenGL call
            GL.glClearColor(0, 0, 0, 1)
            
            return True
            
        except Exception as e:
            logger.warning(f"OpenGL test failed: {str(e)}")
            return False
            
    except (ImportError, AttributeError) as e:
        logger.warning(f"OpenGL not available: {str(e)}")
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
        self.all_vertices = np.zeros((0, 3), dtype=np.float32)
        self.all_faces = np.zeros((0, 3), dtype=np.uint32)
        self.file_path = None
        self.use_opengl = is_opengl_available()
        self.mesh_plot = None  # Store reference to the mesh plot
        
        if not self.use_opengl:
            logger.warning("OpenGL not available. Using software rendering.")
        else:
            logger.info("OpenGL acceleration is available")
    
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
            logger.info(f"Updating mesh with {len(vertices) if vertices is not None else 'None'} vertices and {len(faces) if faces is not None else 'None'} faces")
            
            # Convert inputs to numpy arrays if they aren't already
            try:
                vertices = np.asarray(vertices, dtype=np.float32)
                faces = np.asarray(faces, dtype=np.uint32)
                logger.debug(f"Converted vertices shape: {vertices.shape}, faces shape: {faces.shape}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting input data: {str(e)}")
                self._show_error_message("Invalid mesh data format")
                return False
            
            # For the first chunk, just store the vertices and faces directly
            if len(self.all_vertices) == 0:
                self.all_vertices = vertices
                self.all_faces = faces
            else:
                # For subsequent chunks, append vertices and update face indices
                vertex_offset = len(self.all_vertices)
                self.all_vertices = np.vstack((self.all_vertices, vertices))
                self.all_faces = np.vstack((self.all_faces, faces + vertex_offset))
            
            # Update the file path if provided
            if file_path:
                self.file_path = str(file_path)
            
            # Update the visualization with the accumulated mesh
            return self._update_visualization()
            
        except Exception as e:
            error_msg = f"Error updating mesh: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._show_error_message(f"Error processing mesh: {str(e)}")
            return False
    
    def _update_visualization(self):
        """
        Internal method to update the visualization with the current mesh data.
        """
        try:
            # Clear the current plot and reset mesh_plot reference
            self.ax.clear()
            self.mesh_plot = None
            
            # Set up the 3D axes with default labels
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')
            
            # Check if we have valid data to visualize
            if len(self.all_vertices) == 0 or len(self.all_faces) == 0:
                msg = "No valid mesh data to render"
                logger.warning(msg)
                self._show_error_message(msg)
                return False
            
            # Verify all face indices are valid before rendering
            max_vertex_idx = np.max(self.all_faces) if len(self.all_faces) > 0 else -1
            if max_vertex_idx >= len(self.all_vertices):
                msg = f"Invalid face indices: Max index {max_vertex_idx} exceeds vertex count {len(self.all_vertices)}"
                logger.error(msg)
                self._show_error_message("Invalid mesh data: face indices out of range")
                return False
            
            try:
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                
                # Create triangles array with the correct vertex indices
                triangles = self.all_vertices[self.all_faces]
                
                # Create the mesh plot and store the reference
                self.mesh_plot = Poly3DCollection(triangles, alpha=0.5, linewidths=0.5, edgecolor='k')
                self.mesh_plot.set_facecolor([0.7, 0.7, 1.0])  # Light blue color
                self.ax.add_collection3d(self.mesh_plot)
                
                # Auto-scale the plot to fit the mesh
                min_vals = np.min(self.all_vertices, axis=0)
                max_vals = np.max(self.all_vertices, axis=0)
                
                # Add a small margin
                bounds = max_vals - min_vals
                margin = np.max(bounds) * 0.1 if np.any(bounds > 0) else 1.0
                
                self.ax.set_xlim([min_vals[0] - margin, max_vals[0] + margin])
                self.ax.set_ylim([min_vals[1] - margin, max_vals[1] + margin])
                self.ax.set_zlim([min_vals[2] - margin, max_vals[2] + margin])
                
                # Set a title if we have a file path
                if hasattr(self, 'file_path') and self.file_path:
                    self.ax.set_title(f'STL: {os.path.basename(self.file_path)}')
                
                # Redraw the canvas
                self.canvas.draw()
                logger.info(f"Successfully rendered mesh with {len(self.all_vertices)} vertices and {len(self.all_faces)} faces")
                return True
                
            except Exception as e:
                logger.error(f"Error creating 3D visualization: {str(e)}", exc_info=True)
                self._show_error_message("Error creating 3D visualization")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error in visualization: {str(e)}", exc_info=True)
            self._show_error_message(f"Visualization error: {str(e)}")
            return False
    
    def clear(self):
        """Clear the current visualization."""
        if hasattr(self, 'all_vertices'):
            del self.all_vertices
        if hasattr(self, 'all_faces'):
            del self.all_faces
        self.file_path = None
        self.ax.clear()
        self.canvas.draw()
    
    def render(self):
        """
        Render the STL visualization.
        
        Returns:
            bool: True if rendering was successful, False otherwise
        """
        try:
            # Clear the current plot and reset mesh_plot reference
            self.ax.clear()
            self.mesh_plot = None
            
            # Set up the 3D axes with default labels
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')
            
            # Check if we have valid data to visualize
            if len(self.all_vertices) == 0 or len(self.all_faces) == 0:
                msg = "No valid mesh data to render"
                logger.warning(msg)
                self._show_error_message(msg)
                return False
            
            # Verify all face indices are valid before rendering
            max_vertex_idx = np.max(self.all_faces) if len(self.all_faces) > 0 else -1
            if max_vertex_idx >= len(self.all_vertices):
                msg = f"Invalid face indices: Max index {max_vertex_idx} exceeds vertex count {len(self.all_vertices)}"
                logger.error(msg)
                self._show_error_message("Invalid mesh data: face indices out of range")
                return False
                
            try:
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                
                # Create triangles array with the correct vertex indices
                triangles = self.all_vertices[self.all_faces]
                
                # Create the mesh plot and store the reference
                self.mesh_plot = Poly3DCollection(triangles, alpha=0.5, linewidths=0.5, edgecolor='k')
                self.mesh_plot.set_facecolor([0.7, 0.7, 1.0])  # Light blue color
                self.ax.add_collection3d(self.mesh_plot)
                
                # Auto-scale the plot to fit the mesh
                min_vals = np.min(self.all_vertices, axis=0)
                max_vals = np.max(self.all_vertices, axis=0)
                
                # Add a small margin
                bounds = max_vals - min_vals
                margin = np.max(bounds) * 0.1 if np.any(bounds > 0) else 1.0
                
                self.ax.set_xlim([min_vals[0] - margin, max_vals[0] + margin])
                self.ax.set_ylim([min_vals[1] - margin, max_vals[1] + margin])
                self.ax.set_zlim([min_vals[2] - margin, max_vals[2] + margin])
                
                # Set a title if we have a file path
                if hasattr(self, 'file_path') and self.file_path:
                    self.ax.set_title(f'STL: {os.path.basename(self.file_path)}')
                
                # Redraw the canvas
                self.canvas.draw()
                logger.info(f"Successfully rendered mesh with {len(self.all_vertices)} vertices and {len(self.all_faces)} faces")
                return True
                
            except Exception as e:
                logger.error(f"Error creating 3D visualization: {str(e)}", exc_info=True)
                self._show_error_message("Error creating 3D visualization")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error in render: {str(e)}", exc_info=True)
            self._show_error_message(f"Rendering error: {str(e)}")
            return False
    
    def toggle_wireframe(self, show):
        """
        Toggle wireframe visibility.
        
        Args:
            show: If True, show wireframe; if False, hide it
            
        Returns:
            bool: True if toggled successfully, False otherwise
        """
        try:
            if self.mesh_plot is not None:
                self.mesh_plot.set_edgecolor('k' if show else 'none')
                self.canvas.draw()
                return True
            return False
        except Exception as e:
            logger.error(f"Error toggling wireframe: {str(e)}", exc_info=True)
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
