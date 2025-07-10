import numpy as np
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtOpenGL import (
    QOpenGLShaderProgram, QOpenGLShader, QOpenGLBuffer, 
    QOpenGLVertexArrayObject, QOpenGLVersionProfile, QOpenGLContext,
    QOpenGLFunctions_3_3_Core
)
from PyQt6.QtGui import QSurfaceFormat, QVector3D, QMatrix4x4, QVector4D
from PyQt6.QtCore import Qt, QSize, QTimer, QObject, pyqtSignal
from OpenGL import GL as gl
import ctypes
import logging
import re
from typing import List, Tuple, Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class OpenGLGCodeVisualizer(QOpenGLWidget, QOpenGLFunctions_3_3_Core):
    """OpenGL-based G-code visualizer with GPU acceleration and incremental loading support."""
    
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
        
        # Initialize OpenGL functions
        self.gl = None
        
        # Visualization settings
        self.decimation_factor = 1
        self.show_travel_moves = True
        self.point_size = 1.5
        self.line_width = 1.0
        self.background_color = (0.1, 0.1, 0.1, 1.0)
        
        # Camera settings
        self.camera_distance = 100.0
        self.camera_yaw = 45.0
        self.camera_pitch = 30.0
        self.camera_target = QVector3D(0, 0, 0)
        
        # Shader program and buffers
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.ibo = None
        
        # View matrices
        self.model_matrix = QMatrix4x4()
        self.view_matrix = QMatrix4x4()
        self.projection_matrix = QMatrix4x4()
        self.mvp_matrix = QMatrix4x4()
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(16)  # ~60 FPS

    def initializeGL(self):
        """Initialize OpenGL context."""
        try:
            # Initialize OpenGL functions
            self.gl = self.context().versionFunctions()
            if self.gl is None:
                raise RuntimeError("Could not obtain OpenGL functions")
                
            self.gl.initializeOpenGLFunctions()
            
            # Set up OpenGL state
            self.gl.glEnable(gl.GL_DEPTH_TEST)
            self.gl.glEnable(gl.GL_MULTISAMPLE)
            self.gl.glEnable(gl.GL_BLEND)
            self.gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            self.gl.glClearColor(*self.background_color)
            
            # Initialize shaders
            self._init_shaders()
            
            # Set up initial view
            self.resizeGL(self.width(), self.height())
            self.update_view()
            
        except Exception as e:
            logger.error(f"Error initializing OpenGL: {e}", exc_info=True)
            raise

    def _init_shaders(self):
        """Initialize shader programs."""
        try:
            # Create shader program
            self.shader_program = QOpenGLShaderProgram()
            
            # Add vertex shader
            if not self.shader_program.addShaderFromSourceCode(
                QOpenGLShader.Vertex,
                """
                #version 330 core
                layout(location = 0) in vec3 position;
                layout(location = 1) in vec3 color;
                
                uniform mat4 mvp_matrix;
                
                out vec3 frag_color;
                
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
                in vec3 frag_color;
                out vec4 final_color;
                
                void main() {
                    final_color = vec4(frag_color, 1.0);
                }
                """
            ):
                raise RuntimeError("Fragment shader compilation failed: " + 
                                self.shader_program.log())
            
            # Link shader program
            if not self.shader_program.link():
                raise RuntimeError("Shader program linking failed: " + 
                                self.shader_program.log())
            
        except Exception as e:
            logger.error(f"Error initializing shaders: {e}", exc_info=True)
            raise

    def resizeGL(self, w, h):
        """Handle window resize events."""
        try:
            if h == 0:
                h = 1
                
            # Update viewport
            self.gl.glViewport(0, 0, w, h)
            
            # Update projection matrix
            self.projection_matrix.setToIdentity()
            aspect_ratio = w / h
            self.projection_matrix.perspective(45.0, aspect_ratio, 0.1, 1000.0)
            
        except Exception as e:
            logger.error(f"Error in resizeGL: {e}", exc_info=True)

    def paintGL(self):
        """Render the scene."""
        try:
            # Clear the screen and depth buffer
            self.gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
            # Bind shader program
            if not self.shader_program or not self.shader_program.bind():
                logger.warning("Failed to bind shader program")
                return
            
            # Update MVP matrix
            self.update_view()
            self.shader_program.setUniformValue("mvp_matrix", self.mvp_matrix)
            
            # Draw your scene here
            # Example: self._draw_axis()
            
            # Release shader program
            self.shader_program.release()
            
        except Exception as e:
            logger.error(f"Error in paintGL: {e}", exc_info=True)

    def update_view(self):
        """Update the view matrices."""
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

    def clear_scene(self):
        """Clear the current scene."""
        try:
            # Clear any existing geometry
            self.makeCurrent()
            
            # Delete any existing buffers
            if hasattr(self, 'vbo') and self.vbo:
                self.vbo.destroy()
                self.vbo = None
                
            if hasattr(self, 'ibo') and self.ibo:
                self.ibo.destroy()
                self.ibo = None
                
            if hasattr(self, 'vao') and self.vao:
                self.vao.destroy()
                self.vao = None
                
            self.update()
            
        except Exception as e:
            logger.error(f"Error clearing scene: {e}", exc_info=True)

    def fit_to_view(self):
        """Fit the view to the current geometry."""
        # Reset camera position and orientation
        self.camera_distance = 100.0
        self.camera_yaw = 45.0
        self.camera_pitch = 30.0
        self.camera_target = QVector3D(0, 0, 0)
        
        # Update the view
        self.update_view()
        self.update()

    def minimumSizeHint(self):
        return QSize(400, 300)
    
    def sizeHint(self):
        return QSize(800, 600)

    def clear(self):
        """Clear all loaded G-code data."""
        self.print_points = []
        self.travel_points = []
        self._bounds = None
        self.update_gpu_buffers()
        self.update()
    
    def append_gcode(self, gcode_chunk: str):
        """Append a chunk of G-code to the visualization.
        
        Args:
            gcode_chunk: A string containing G-code to be parsed and added to the visualization
        """
        if not gcode_chunk.strip():
            return
            
        try:
            # Parse the G-code chunk
            commands = self._parse_gcode(gcode_chunk)
            
            # Process commands and update internal state
            current_pos = {'X': 0, 'Y': 0, 'Z': 0, 'E': 0, 'F': 0}
            is_absolute = True
            
            for cmd in commands:
                # Update current position based on command
                if 'X' in cmd or 'Y' in cmd or 'Z' in cmd:
                    # Handle movement command
                    is_extruding = 'E' in cmd and cmd['E'] > 0
                    
                    # Get target position
                    target_pos = dict(current_pos)
                    for axis in ['X', 'Y', 'Z', 'E', 'F']:
                        if axis in cmd:
                            if is_absolute or axis == 'F':
                                target_pos[axis] = cmd[axis]
                            else:
                                target_pos[axis] += cmd[axis]
                    
                    # Add to appropriate move list
                    if is_extruding:
                        self._add_print_move(current_pos, target_pos)
                    else:
                        self._add_travel_move(current_pos, target_pos)
                    
                    current_pos.update(target_pos)
                
                # Handle G90/G91 (absolute/relative positioning)
                elif cmd.get('G') == 90:
                    is_absolute = True
                elif cmd.get('G') == 91:
                    is_absolute = False
            
            # Update GPU buffers if we have an OpenGL context
            if self.isValid():
                self.makeCurrent()
                self.update_gpu_buffers()
                self.update()
                self.doneCurrent()
            
        except Exception as e:
            logger.error(f"Error processing G-code chunk: {e}", exc_info=True)
    
    def _add_print_move(self, start_pos, end_pos):
        """Add a print move to the visualization."""
        # Add line segment
        self.print_points.extend([
            start_pos['X'], start_pos['Y'], start_pos['Z'],
            end_pos['X'], end_pos['Y'], end_pos['Z']
        ])
        
        # Update bounds
        self._update_bounds([
            [start_pos['X'], start_pos['Y'], start_pos['Z']],
            [end_pos['X'], end_pos['Y'], end_pos['Z']]
        ])
    
    def _add_travel_move(self, start_pos, end_pos):
        """Add a travel move to the visualization."""
        # Add line segment
        self.travel_points.extend([
            start_pos['X'], start_pos['Y'], start_pos['Z'],
            end_pos['X'], end_pos['Y'], end_pos['Z']
        ])
        
        # Update bounds
        self._update_bounds([
            [start_pos['X'], start_pos['Y'], start_pos['Z']],
            [end_pos['X'], end_pos['Y'], end_pos['Z']]
        ])
    
    def _update_bounds(self, points):
        """Update the bounding box to include the given points."""
        points = np.array(points)
        if len(points) == 0:
            return
            
        min_vals = np.min(points, axis=0)
        max_vals = np.max(points, axis=0)
        
        if self._bounds is None:
            self._bounds = np.column_stack((min_vals, max_vals)).flatten()
        else:
            min_vals = np.minimum(self._bounds[::2], min_vals)
            max_vals = np.maximum(self._bounds[1::2], max_vals)
            self._bounds = np.column_stack((min_vals, max_vals)).flatten()
        
        # Update camera target if we have valid bounds
        if self._bounds is not None:
            center = (self._bounds[1::2] + self._bounds[::2]) / 2
            self.camera_target = QVector3D(center[0], center[1], center[2])
            
            # Adjust camera distance to fit the model
            size = max(self._bounds[1::2] - self._bounds[::2])
            if size > 0:
                self.camera_distance = size * 1.5  # Add some padding
    
    def update_gpu_buffers(self):
        """Update the GPU buffers with the current data."""
        if not self.isValid():
            return
            
        self.makeCurrent()
        
        # Update print moves buffer
        if self.print_points:
            print_data = np.array(self.print_points, dtype=np.float32)
            self.num_print_points = len(print_data) // 3
            
            if self.print_vbo is None:
                self.print_vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                self.print_vbo.create()
            
            self.print_vbo.bind()
            self.print_vbo.allocate(print_data.tobytes(), print_data.nbytes)
            
            if self.print_vao is None:
                self.print_vao = QOpenGLVertexArrayObject()
                self.print_vao.create()
            
            self.print_vao.bind()
            self.shader_program.enableAttributeArray(0)
            self.shader_program.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3, 0)
            self.print_vao.release()
            self.print_vbo.release()
        
        # Update travel moves buffer
        if self.travel_points:
            travel_data = np.array(self.travel_points, dtype=np.float32)
            self.num_travel_points = len(travel_data) // 3
            
            if self.travel_vbo is None:
                self.travel_vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                self.travel_vbo.create()
            
            self.travel_vbo.bind()
            self.travel_vbo.allocate(travel_data.tobytes(), travel_data.nbytes)
            
            if self.travel_vao is None:
                self.travel_vao = QOpenGLVertexArrayObject()
                self.travel_vao.create()
            
            self.travel_vao.bind()
            self.shader_program.enableAttributeArray(0)
            self.shader_program.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3, 0)
            self.travel_vao.release()
            self.travel_vbo.release()
        
        self.doneCurrent()
    
    def _parse_gcode(self, gcode: str) -> List[Dict[str, Any]]:
        """Parse G-code into a list of commands with coordinates."""
        commands = []
        lines = gcode.strip().split('\n')
        
        # Current position (absolute coordinates)
        current_pos = {'X': 0, 'Y': 0, 'Z': 0, 'E': 0, 'F': 0}
        is_absolute = True  # Default to absolute positioning (G90)
        
        for line in lines:
            line = line.split(';', 1)[0].strip()  # Remove comments
            if not line:
                continue
                
            # Parse G-code commands
            g_match = re.match(r'^G(\d+)', line)
            if g_match:
                gcode_num = int(g_match.group(1))
                
                # Handle movement commands (G0, G1, G2, G3)
                if gcode_num in [0, 1, 2, 3]:
                    # Parse coordinates
                    coords = {}
                    for m in re.finditer(r'([XYZEF])([\d\.\-]+)', line):
                        coords[m.group(1)] = float(m.group(2))
                    
                    commands.append({
                        'G': gcode_num,
                        **coords
                    })
                
                # Handle absolute/relative positioning
                elif gcode_num == 90:  # G90 - Absolute positioning
                    is_absolute = True
                elif gcode_num == 91:  # G91 - Relative positioning
                    is_absolute = False
            
            # Handle M-codes if needed
            m_match = re.match(r'^M(\d+)', line)
            if m_match:
                mcode = int(m_match.group(1))
                # Handle M-codes like M82/M83 (extruder mode)
                # Add handlers as needed
                pass
        
        return commands
    
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
            self.last_mouse_pos = event.pos()
            
        except Exception as e:
            logger.error(f"Error in mousePressEvent: {e}", exc_info=True)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for rotation and panning."""
        try:
            if self.last_mouse_pos is None:
                return
            
            # Calculate mouse movement delta
            dx = event.pos().x() - self.last_mouse_pos.x()
            dy = event.pos().y() - self.last_mouse_pos.y()
            
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
            self.last_mouse_pos = event.pos()
            
            # Update the view
            self.update_view()
            self.update()
            
        except Exception as e:
            logger.error(f"Error in mouseMoveEvent: {e}", exc_info=True)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        try:
            self.last_mouse_pos = None
            
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
