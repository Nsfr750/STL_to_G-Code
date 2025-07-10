import numpy as np
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QSurfaceFormat, QOpenGLShaderProgram, QOpenGLShader, QOpenGLBuffer, QOpenGLVertexArrayObject, QVector3D, QMatrix4x4, QVector4D, QOpenGLVersionProfile, QOpenGLContext
from PyQt6.QtCore import Qt, QSize, QTimer
from OpenGL import GL as gl
import ctypes
import logging
from typing import List, Tuple, Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class OpenGLGCodeVisualizer(QOpenGLWidget):
    """OpenGL-based G-code visualizer with GPU acceleration."""
    
    def __init__(self, parent=None):
        """Initialize the OpenGL visualizer."""
        # Request OpenGL 3.3 Core Profile
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)  # Enable MSAA
        fmt.setSwapInterval(1)  # Enable VSync
        super().__init__(parent)
        self.setFormat(fmt)
        
        # Visualization settings
        self.decimation_factor = 1
        self.show_travel_moves = True
        self.point_size = 1.5
        self.line_width = 1.0
        self.background_color = (0.1, 0.1, 0.1, 1.0)
        self.print_color = (0.2, 0.6, 1.0, 1.0)  # Blue for print moves
        self.travel_color = (1.0, 0.2, 0.2, 0.3)  # Red for travel moves with transparency
        
        # Camera settings
        self.camera_distance = 300.0
        self.camera_yaw = 45.0
        self.camera_pitch = 30.0
        self.camera_target = QVector3D(0, 0, 0)
        
        # Mouse interaction
        self.last_pos = None
        self.rotation_speed = 0.5
        self.zoom_speed = 0.01
        self.pan_speed = 0.01
        
        # Data buffers
        self.print_vao = None
        self.print_vbo = None
        self.travel_vao = None
        self.travel_vbo = None
        self.num_print_points = 0
        self.num_travel_points = 0
        
        # Shader programs
        self.shader_program = None
        self.mvp_matrix_location = None
        
        # View matrices
        self.model_matrix = QMatrix4x4()
        self.view_matrix = QMatrix4x4()
        self.projection_matrix = QMatrix4x4()
        self.mvp_matrix = QMatrix4x4()
        
        # Animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(16)  # ~60 FPS
    
    def minimumSizeHint(self):
        return QSize(400, 300)
    
    def sizeHint(self):
        return QSize(800, 600)
    
    def initializeGL(self):
        """Initialize OpenGL resources."""
        try:
            # Initialize OpenGL functions
            self.gl = self.context().versionFunctions()
            if self.gl is None:
                raise RuntimeError("Could not obtain OpenGL functions")
                
            self.gl.initializeOpenGLFunctions()
            
            # Set up OpenGL state
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_MULTISAMPLE)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glClearColor(*self.background_color)
            
            # Initialize shaders
            self.init_shaders()
            
            # Set up initial view
            self.update_view()
            
        except Exception as e:
            logger.error(f"Error initializing OpenGL: {e}", exc_info=True)
    
    def init_shaders(self):
        """Initialize the shader program."""
        try:
            # Create shader program
            self.shader_program = QOpenGLShaderProgram()
            
            # Add vertex shader
            if not self.shader_program.addShaderFromSourceCode(
                QOpenGLShader.Vertex,
                """
                #version 330 core
                layout(location = 0) in vec3 position;
                uniform mat4 mvp_matrix;
                uniform vec4 color;
                out vec4 frag_color;
                void main() {
                    gl_Position = mvp_matrix * vec4(position, 1.0);
                    frag_color = color;
                }
                """
            ):
                raise RuntimeError("Vertex shader compilation failed: " + 
                                self.shader_program.log())
            
            # Add fragment shader
            if not self.shader_program.addShaderFromSourceCode(
                QOpenGLShader.Fragment,
                """
                #version 330 core
                in vec4 frag_color;
                out vec4 final_color;
                void main() {
                    final_color = frag_color;
                }
                """
            ):
                raise RuntimeError("Fragment shader compilation failed: " + 
                                self.shader_program.log())
            
            # Link shader program
            if not self.shader_program.link():
                raise RuntimeError("Shader program linking failed: " + 
                                self.shader_program.log())
            
            # Get uniform locations
            self.mvp_matrix_location = self.shader_program.uniformLocation("mvp_matrix")
            self.color_location = self.shader_program.uniformLocation("color")
            
        except Exception as e:
            logger.error(f"Error initializing shaders: {e}", exc_info=True)
            raise
    
    def resizeGL(self, w, h):
        """Handle window resize events."""
        try:
            # Update viewport
            gl.glViewport(0, 0, w, h)
            
            # Update projection matrix
            self.projection_matrix.setToIdentity()
            aspect = w / h if h > 0 else 1.0
            self.projection_matrix.perspective(45.0, aspect, 1.0, 10000.0)
            
            self.update_view()
            
        except Exception as e:
            logger.error(f"Error in resizeGL: {e}", exc_info=True)
    
    def paintGL(self):
        """Render the scene."""
        try:
            # Clear the screen and depth buffer
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
            # If no shader program, nothing to render
            if not self.shader_program or not self.shader_program.isLinked():
                return
            
            # Bind shader program
            self.shader_program.bind()
            
            # Update model-view-projection matrix
            self.shader_program.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
            
            # Render print moves
            if self.print_vao and self.num_print_points > 0:
                self.shader_program.setUniformValue(self.color_location, 
                                                  QVector4D(*self.print_color))
                self.print_vao.bind()
                gl.glDrawArrays(gl.GL_LINE_STRIP, 0, self.num_print_points)
                self.print_vao.release()
            
            # Render travel moves if enabled
            if self.show_travel_moves and self.travel_vao and self.num_travel_points > 0:
                self.shader_program.setUniformValue(self.color_location,
                                                  QVector4D(*self.travel_color))
                self.travel_vao.bind()
                gl.glDrawArrays(gl.GL_LINE_STRIP, 0, self.num_travel_points)
                self.travel_vao.release()
            
            # Release shader program
            self.shader_program.release()
            
        except Exception as e:
            logger.error(f"Error in paintGL: {e}", exc_info=True)
    
    def update_view(self):
        """Update the view and projection matrices."""
        try:
            # Reset view matrix
            self.view_matrix.setToIdentity()
            
            # Calculate camera position
            rad_yaw = np.radians(self.camera_yaw)
            rad_pitch = np.radians(self.camera_pitch)
            
            # Calculate camera position in spherical coordinates
            x = (self.camera_distance * np.cos(rad_pitch) * 
                 np.cos(rad_yaw))
            y = (self.camera_distance * np.cos(rad_pitch) * 
                 np.sin(rad_yaw))
            z = self.camera_distance * np.sin(rad_pitch)
            
            # Apply camera position and target
            eye = QVector3D(x, y, z) + self.camera_target
            up = QVector3D(0, 0, 1)  # Z is up in our coordinate system
            
            # Set up the view matrix
            self.view_matrix.lookAt(eye, self.camera_target, up)
            
            # Update MVP matrix
            self.mvp_matrix = self.projection_matrix * self.view_matrix * self.model_matrix
            
        except Exception as e:
            logger.error(f"Error updating view: {e}", exc_info=True)
    
    def set_gcode_data(self, print_points, travel_points):
        """Set the G-code data to be rendered.
        
        Args:
            print_points: List of (x, y, z) tuples for print moves
            travel_points: List of (x, y, z) tuples for travel moves
        """
        try:
            # Ensure we have a valid OpenGL context
            self.makeCurrent()
            
            # Convert points to numpy arrays if they aren't already
            if print_points is not None:
                print_points = np.array(print_points, dtype=np.float32)
                if len(print_points.shape) == 1:
                    print_points = print_points.reshape(-1, 3)
            
            if travel_points is not None:
                travel_points = np.array(travel_points, dtype=np.float32)
                if len(travel_points.shape) == 1:
                    travel_points = travel_points.reshape(-1, 3)
            
            # Process print points
            if print_points is not None and len(print_points) > 0:
                # Apply decimation if needed
                if self.decimation_factor > 1 and len(print_points) > 1000:
                    print_points = print_points[::self.decimation_factor]
                
                self.num_print_points = len(print_points)
                
                # Create or update VBO for print moves
                if self.print_vbo is None:
                    self.print_vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                    self.print_vbo.create()
                
                self.print_vbo.bind()
                self.print_vbo.allocate(print_points.tobytes(), 
                                      print_points.nbytes)
                
                # Create or update VAO for print moves
                if self.print_vao is None:
                    self.print_vao = QOpenGLVertexArrayObject()
                    self.print_vao.create()
                
                self.print_vao.bind()
                
                # Configure vertex attributes
                gl.glEnableVertexAttribArray(0)
                gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 
                                      3 * 4, None)  # 3 floats, 4 bytes each
                
                self.print_vao.release()
                self.print_vbo.release()
                
                # Update camera to fit the model
                self.fit_view_to_model(print_points, travel_points if travel_points is not None else [])
            else:
                self.num_print_points = 0
            
            # Process travel points
            if travel_points is not None and len(travel_points) > 0:
                # Apply more aggressive decimation to travel moves
                decimation = max(1, self.decimation_factor * 2)
                if decimation > 1 and len(travel_points) > 100:
                    travel_points = travel_points[::decimation]
                
                self.num_travel_points = len(travel_points)
                
                # Create or update VBO for travel moves
                if self.travel_vbo is None:
                    self.travel_vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                    self.travel_vbo.create()
                
                self.travel_vbo.bind()
                self.travel_vbo.allocate(travel_points.tobytes(),
                                       travel_points.nbytes)
                
                # Create or update VAO for travel moves
                if self.travel_vao is None:
                    self.travel_vao = QOpenGLVertexArrayObject()
                    self.travel_vao.create()
                
                self.travel_vao.bind()
                
                # Configure vertex attributes
                gl.glEnableVertexAttribArray(0)
                gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE,
                                      3 * 4, None)  # 3 floats, 4 bytes each
                
                self.travel_vao.release()
                self.travel_vbo.release()
                
                # Update camera to fit the model if we don't have print points
                if self.num_print_points == 0:
                    self.fit_view_to_model(travel_points, [])
            else:
                self.num_travel_points = 0
            
            # Request a redraw
            self.update()
            
        except Exception as e:
            logger.error(f"Error setting G-code data: {e}", exc_info=True)
    
    def fit_view_to_model(self, points1, points2=None):
        """Adjust the camera to fit the model in the view."""
        try:
            if len(points1) == 0 and (points2 is None or len(points2) == 0):
                return
            
            # Combine points from both arrays
            if points2 is not None and len(points2) > 0:
                all_points = np.vstack((points1, points2))
            else:
                all_points = points1
            
            # Calculate bounding box
            min_vals = np.min(all_points, axis=0)
            max_vals = np.max(all_points, axis=0)
            
            # Calculate center of the model
            center = (min_vals + max_vals) * 0.5
            
            # Calculate the size of the model
            size = max(max_vals - min_vals)
            
            # Update camera target to center of the model
            self.camera_target = QVector3D(center[0], center[1], center[2])
            
            # Adjust camera distance to fit the model
            if size > 0:
                self.camera_distance = size * 1.5  # Add some padding
            
            # Reset rotation
            self.camera_yaw = 45.0
            self.camera_pitch = 30.0
            
            # Update the view
            self.update_view()
            
        except Exception as e:
            logger.error(f"Error fitting view to model: {e}", exc_info=True)
    
    def set_decimation_factor(self, factor):
        """Set the decimation factor for reducing the number of points."""
        self.decimation_factor = max(1, int(factor))
    
    def set_show_travel_moves(self, show):
        """Set whether to show travel moves."""
        self.show_travel_moves = show
        self.update()
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        try:
            # Get the wheel delta (scaled by zoom speed)
            delta = event.angleDelta().y() * self.zoom_speed
            
            # Adjust camera distance (inverse because we're moving the camera)
            self.camera_distance = max(1.0, self.camera_distance - delta)
            
            # Update the view
            self.update_view()
            self.update()
            
        except Exception as e:
            logger.error(f"Error in wheelEvent: {e}", exc_info=True)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for rotation and panning."""
        try:
            self.last_pos = event.pos()
            
        except Exception as e:
            logger.error(f"Error in mousePressEvent: {e}", exc_info=True)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for rotation and panning."""
        try:
            if self.last_pos is None:
                return
            
            # Calculate mouse movement delta
            dx = event.pos().x() - self.last_pos.x()
            dy = event.pos().y() - self.last_pos.y()
            
            # Rotate on left button drag
            if event.buttons() & Qt.LeftButton:
                self.camera_yaw += dx * self.rotation_speed
                self.camera_pitch += dy * self.rotation_speed
                self.camera_pitch = max(-89.9, min(89.9, self.camera_pitch))  # Clamp pitch
            
            # Pan on right button drag
            elif event.buttons() & Qt.RightButton:
                # Calculate right and up vectors
                yaw_rad = np.radians(self.camera_yaw)
                right = QVector3D(np.cos(yaw_rad), np.sin(yaw_rad), 0.0)
                up = QVector3D(0.0, 0.0, 1.0)
                
                # Calculate pan amount (scaled by distance)
                pan_speed = self.camera_distance * self.pan_speed
                pan_dx = -dx * pan_speed
                pan_dy = dy * pan_speed
                
                # Update camera target
                self.camera_target += right * pan_dx + up * pan_dy
            
            # Update last position
            self.last_pos = event.pos()
            
            # Update the view
            self.update_view()
            self.update()
            
        except Exception as e:
            logger.error(f"Error in mouseMoveEvent: {e}", exc_info=True)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        try:
            self.last_pos = None
            
        except Exception as e:
            logger.error(f"Error in mouseReleaseEvent: {e}", exc_info=True)
    
    def cleanup(self):
        """Clean up OpenGL resources."""
        try:
            self.makeCurrent()
            
            # Delete VAOs and VBOs
            if self.print_vao is not None:
                self.print_vao.destroy()
                self.print_vao = None
            
            if self.print_vbo is not None:
                self.print_vbo.destroy()
                self.print_vbo = None
            
            if self.travel_vao is not None:
                self.travel_vao.destroy()
                self.travel_vao = None
            
            if self.travel_vbo is not None:
                self.travel_vbo.destroy()
                self.travel_vbo = None
            
            # Delete shader program
            if self.shader_program is not None:
                self.shader_program.removeAllShaders()
                self.shader_program = None
            
            self.doneCurrent()
            
        except Exception as e:
            logger.error(f"Error cleaning up OpenGL resources: {e}", exc_info=True)
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.cleanup()
        event.accept()
