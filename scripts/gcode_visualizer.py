import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QPushButton, QComboBox, QLabel, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import collections as mcoll
import matplotlib.pyplot as plt
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import time

logger = logging.getLogger(__name__)

class GCodeVisualizer(QWidget):
    """Widget for 3D visualization of G-code toolpaths with performance optimizations."""
    
    def __init__(self, parent=None):
        """Initialize the G-code visualizer with performance optimizations."""
        super().__init__(parent)
        
        # Performance settings
        self._decimation_factor = 1  # Start with no decimation
        self._show_travel_moves = True
        self._last_render_time = 0
        self._min_render_interval = 0.1  # Minimum time between renders (seconds)
        self._last_render_data = None
        
        # Set up the matplotlib figure and axes with optimized settings
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.set_facecolor('none')  # Transparent background
        
        # Use a more efficient backend if available
        try:
            import matplotlib
            matplotlib.use('Qt5Agg', force=True)
        except ImportError:
            pass
        
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111, projection='3d')
        
        # Configure the axes for better performance
        self.axes.set_axis_off()  # Turn off axis for better performance
        self.axes.grid(False)
        
        # Set up the layout
        layout = QVBoxLayout()
        
        # Add controls layout
        controls_layout = QHBoxLayout()
        
        # Add performance controls
        self.performance_label = QLabel("Detail:")
        controls_layout.addWidget(self.performance_label)
        
        self.detail_combo = QComboBox()
        self.detail_combo.addItems(["Low", "Medium", "High"])
        self.detail_combo.setCurrentIndex(1)  # Default to Medium
        self.detail_combo.currentIndexChanged.connect(self._on_detail_changed)
        controls_layout.addWidget(self.detail_combo)
        
        # Add travel moves toggle
        self.travel_moves_check = QCheckBox("Show Travel Moves")
        self.travel_moves_check.setChecked(True)
        self.travel_moves_check.stateChanged.connect(self._on_travel_moves_changed)
        controls_layout.addWidget(self.travel_moves_check)
        
        # Add reset view button
        self.reset_view_btn = QPushButton("Reset View")
        self.reset_view_btn.clicked.connect(self.reset_view)
        controls_layout.addWidget(self.reset_view_btn)
        
        controls_layout.addStretch()
        
        # Add status label
        self.status_label = QLabel("")
        controls_layout.addWidget(self.status_label)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Initialize visualization state
        self.reset_view()
    
    def _on_detail_changed(self, index):
        """Handle changes to the detail level."""
        detail_levels = {
            0: 4,  # Low detail - more aggressive decimation
            1: 2,  # Medium detail - moderate decimation
            2: 1   # High detail - no decimation
        }
        self._decimation_factor = detail_levels.get(index, 1)
        self._update_visualization()
    
    def _on_travel_moves_changed(self, state):
        """Handle changes to the travel moves visibility."""
        self._show_travel_moves = (state == 2)  # 2 is checked state
        self._update_visualization()
    
    def _decimate_points(self, points, factor):
        """Decimate points to improve rendering performance."""
        if factor <= 1 or len(points) < 10:
            return points
        return points[::factor]
    
    def reset_view(self):
        """Reset the 3D view to default settings with performance optimizations."""
        try:
            # Clear the axes more efficiently
            for artist in self.axes.lines + self.axes.collections:
                artist.remove()
            
            # Set labels and title
            self.axes.set_xlabel('X (mm)', fontsize=8)
            self.axes.set_ylabel('Y (mm)', fontsize=8)
            self.axes.set_zlabel('Z (mm)', fontsize=8)
            self.axes.set_title('G-code Toolpath Visualization', fontsize=10)
            
            # Set grid with reduced alpha for better performance
            self.axes.grid(True, alpha=0.3)
            
            # Set equal aspect ratio
            self.axes.set_box_aspect([1, 1, 1])
            
            # Set initial view angle
            self.axes.view_init(elev=30, azim=45)
            
            # Set initial limits
            self.axes.set_xlim(0, 200)
            self.axes.set_ylim(0, 200)
            self.axes.set_zlim(0, 200)
            
            # Optimize rendering
            self.figure.tight_layout()
            self.canvas.draw_idle()
            
        except Exception as e:
            logger.error(f"Error resetting view: {e}", exc_info=True)
    
    def visualize_gcode(self, gcode: str, show_travel_moves: bool = True):
        """Visualize G-code with performance optimizations.
        
        Args:
            gcode: The G-code string to visualize
            show_travel_moves: Whether to show travel moves (G0)
        """
        current_time = time.time()
        if current_time - self._last_render_time < self._min_render_interval:
            return  # Skip render if we're rendering too frequently
            
        self._last_render_time = current_time
        self._show_travel_moves = show_travel_moves
        
        try:
            # Parse the G-code
            commands = self._parse_gcode(gcode)
            if not commands:
                self.status_label.setText("No valid G-code commands to visualize")
                return
            
            # Extract coordinates for different move types
            print_segments = []
            travel_segments = []
            
            for cmd in commands:
                segment = (cmd['x'], cmd['y'], cmd['z'])
                if cmd['type'] == 'print':
                    print_segments.append(segment)
                elif cmd['type'] == 'move' and self._show_travel_moves:
                    travel_segments.append(segment)
            
            # Convert to numpy arrays for plotting
            print_segments = np.array(print_segments) if print_segments else None
            travel_segments = np.array(travel_segments) if travel_segments else None
            
            # Skip if no data to plot
            if print_segments is None and travel_segments is None:
                return
            
            # Clear previous plots more efficiently
            for artist in self.axes.lines + self.axes.collections:
                artist.remove()
            
            # Plot print moves with line collection for better performance
            if print_segments is not None and len(print_segments) > 1:
                # Apply decimation
                if self._decimation_factor > 1 and len(print_segments) > 1000:
                    print_segments = print_segments[::self._decimation_factor]
                
                # Use line collection for better performance with many lines
                lines = []
                for i in range(len(print_segments) - 1):
                    lines.append([print_segments[i], print_segments[i+1]])
                
                if lines:
                    lc = mcoll.LineCollection(
                        lines, 
                        colors='b', 
                        linewidths=0.5, 
                        alpha=0.8,
                        linestyles='solid'
                    )
                    self.axes.add_collection3d(lc)
            
            # Plot travel moves with line collection
            if travel_segments is not None and len(travel_segments) > 1 and self._show_travel_moves:
                # Apply more aggressive decimation to travel moves
                decimation = max(1, self._decimation_factor * 2)
                if decimation > 1 and len(travel_segments) > 100:
                    travel_segments = travel_segments[::decimation]
                
                # Use line collection for travel moves
                lines = []
                for i in range(len(travel_segments) - 1):
                    lines.append([travel_segments[i], travel_segments[i+1]])
                
                if lines:
                    lc = mcoll.LineCollection(
                        lines,
                        colors='r',
                        linewidths=0.3,
                        alpha=0.3,
                        linestyles='dashed'
                    )
                    self.axes.add_collection3d(lc)
            
            # Auto-scale the view if this is a new visualization
            if self._last_render_data is None:
                self._auto_scale_view(print_segments, travel_segments)
            
            # Update status
            point_count = (0 if print_segments is None else len(print_segments)) + \
                         (0 if travel_segments is None or not self._show_travel_moves else len(travel_segments))
            self.status_label.setText(f"Points: {point_count:,} | "
                                   f"Detail: {self.detail_combo.currentText()}")
            
            # Store the last render data for incremental updates
            self._last_render_data = (print_segments, travel_segments)
            
            # Use draw_idle instead of draw for better performance
            self.canvas.draw_idle()
            
        except Exception as e:
            logger.error(f"Error in visualize_gcode: {e}", exc_info=True)
            self.status_label.setText(f"Error: {str(e)}")
    
    def _auto_scale_view(self, print_segments, travel_segments):
        """Auto-scale the view to fit all points."""
        all_points = []
        
        if print_segments is not None and len(print_segments) > 0:
            all_points.append(print_segments)
        
        if travel_segments is not None and len(travel_segments) > 0 and self._show_travel_moves:
            all_points.append(travel_segments)
        
        if not all_points:
            return
        
        all_points = np.vstack(all_points)
        min_vals = np.min(all_points, axis=0)
        max_vals = np.max(all_points, axis=0)
        ranges = max_vals - min_vals
        
        # Add 10% padding, but at least 1mm
        padding = np.maximum(ranges * 0.1, [1, 1, 1])
        
        self.axes.set_xlim(min_vals[0] - padding[0], max_vals[0] + padding[0])
        self.axes.set_ylim(min_vals[1] - padding[1], max_vals[1] + padding[1])
        self.axes.set_zlim(max(0, min_vals[2] - padding[2]), max_vals[2] + padding[2])
    
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
                
                # Handle different G-codes
                if gcode_num in (0, 1):  # G0/G1 - Linear move
                    # Extract coordinates
                    x = re.search(r'X([-\d.]+)', line)
                    y = re.search(r'Y([-\d.]+)', line)
                    z = re.search(r'Z([-\d.]+)', line)
                    e = re.search(r'E([-\d.]+)', line)
                    f = re.search(r'F(\d+)', line)
                    
                    # Update current position
                    if x: current_pos['X'] = float(x.group(1))
                    if y: current_pos['Y'] = float(y.group(1))
                    if z: current_pos['Z'] = float(z.group(1))
                    if e: current_pos['E'] = float(e.group(1))
                    if f: current_pos['F'] = float(f.group(1))
                    
                    # Add command
                    commands.append({
                        'type': 'move' if gcode_num == 0 else 'print',
                        'x': current_pos['X'],
                        'y': current_pos['Y'],
                        'z': current_pos['Z'],
                        'e': current_pos['E'],
                        'f': current_pos['F']
                    })
                
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
    
    def _update_visualization(self):
        """Update the visualization with current settings."""
        if hasattr(self, '_last_render_data'):
            self.visualize_gcode(self._last_render_data[0], self._show_travel_moves)
