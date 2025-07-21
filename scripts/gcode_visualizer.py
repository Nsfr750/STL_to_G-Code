import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QPushButton, QComboBox, QLabel, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import collections as mcoll
import matplotlib.pyplot as plt
import re
import logging
from scripts.logger import get_logger
from typing import List, Dict, Any, Tuple, Optional
import time

logger = get_logger(__name__)

class GCodeVisualizer(QWidget):
    """Widget for 3D visualization of G-code toolpaths with performance optimizations and incremental loading support."""
    
    def __init__(self, parent=None):
        """Initialize the G-code visualizer with performance optimizations."""
        super().__init__(parent)
        
        # Performance settings
        self._decimation_factor = 1  # Start with no decimation
        self._show_travel_moves = True
        self._last_render_time = 0
        self._min_render_interval = 0.1  # Minimum time between renders (seconds)
        self._last_render_data = None
        
        # Store print and travel moves incrementally
        self._print_moves = []
        self._travel_moves = []
        self._bounds = None  # Will store (min_x, max_x, min_y, max_y, min_z, max_z)
        
        # Set up the matplotlib figure and axes with optimized settings
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.set_facecolor('none')  # Transparent background
        
        # Use constrained layout to prevent label cutoff
        self.figure.set_layout_engine('constrained')
        
        # Create 3D axes with optimized settings
        self.axes = self.figure.add_subplot(111, projection='3d')
        
        # Optimize rendering performance
        self.figure.set_tight_layout(True)
        
        # Create canvas and add to layout
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        # Set up the UI
        self._setup_ui()
        
        # Initialize visualization state
        self.reset_view()
    
    def clear(self):
        """Clear all loaded G-code data."""
        self._print_moves = []
        self._travel_moves = []
        self._bounds = None
        self._last_render_data = None
        self.axes.clear()
        self.canvas.draw_idle()
    
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
            
            # Update visualization
            self._update_visualization()
            
        except Exception as e:
            logger.error(f"Error processing G-code chunk: {e}", exc_info=True)
    
    def _add_print_move(self, start_pos, end_pos):
        """Add a print move to the visualization."""
        if not self._print_moves:
            self._print_moves = []
            
        # Add line segment
        segment = np.array([
            [start_pos['X'], start_pos['Y'], start_pos['Z']],
            [end_pos['X'], end_pos['Y'], end_pos['Z']]
        ])
        self._print_moves.append(segment)
        
        # Update bounds
        self._update_bounds(segment)
    
    def _add_travel_move(self, start_pos, end_pos):
        """Add a travel move to the visualization."""
        if not self._travel_moves:
            self._travel_moves = []
            
        # Add line segment
        segment = np.array([
            [start_pos['X'], start_pos['Y'], start_pos['Z']],
            [end_pos['X'], end_pos['Y'], end_pos['Z']]
        ])
        self._travel_moves.append(segment)
        
        # Update bounds
        self._update_bounds(segment)
    
    def _update_bounds(self, points):
        """Update the bounding box to include the given points."""
        if self._bounds is None:
            min_vals = np.min(points, axis=0)
            max_vals = np.max(points, axis=0)
            self._bounds = np.column_stack((min_vals, max_vals)).flatten()
        else:
            min_vals = np.minimum(self._bounds[::2], np.min(points, axis=0))
            max_vals = np.maximum(self._bounds[1::2], np.max(points, axis=0))
            self._bounds = np.column_stack((min_vals, max_vals)).flatten()
    
    def _update_visualization(self):
        """Update the visualization with the current data."""
        current_time = time.time()
        if current_time - self._last_render_time < self._min_render_interval:
            return  # Skip render if we're rendering too frequently
            
        self._last_render_time = current_time
        
        try:
            self.axes.clear()
            
            # Plot print moves (extrusion)
            if self._print_moves:
                print_segments = np.vstack(self._print_moves)
                print_lines = self.axes.plot(
                    print_segments[:, 0], 
                    print_segments[:, 1], 
                    print_segments[:, 2],
                    'b-',  # Blue lines for print moves
                    linewidth=1.0,
                    alpha=0.7
                )
            
            # Plot travel moves (non-extrusion)
            if self._show_travel_moves and self._travel_moves:
                travel_segments = np.vstack(self._travel_moves)
                travel_lines = self.axes.plot(
                    travel_segments[:, 0],
                    travel_segments[:, 1],
                    travel_segments[:, 2],
                    'r--',  # Red dashed lines for travel moves
                    linewidth=0.5,
                    alpha=0.5
                )
            
            # Auto-scale the view if we have bounds
            if self._bounds is not None:
                padding = 10  # mm padding
                min_x, max_x, min_y, max_y, min_z, max_z = self._bounds
                
                # Add padding
                min_x -= padding
                max_x += padding
                min_y -= padding
                max_y += padding
                min_z = max(0, min_z - padding)  # Don't go below z=0
                max_z += padding
                
                # Set axis limits
                self.axes.set_xlim(min_x, max_x)
                self.axes.set_ylim(min_y, max_y)
                self.axes.set_zlim(min_z, max_z)
            
            # Set labels and title
            self.axes.set_xlabel('X (mm)')
            self.axes.set_ylabel('Y (mm)')
            self.axes.set_zlabel('Z (mm)')
            self.axes.set_title('G-code Toolpath Visualization')
            
            # Update status
            point_count = len(self._print_moves) * 2 + len(self._travel_moves) * 2
            self.status_label.setText(
                f"Points: {point_count:,} | "
                f"Detail: {self.detail_combo.currentText()}"
            )
            
            # Use draw_idle instead of draw for better performance
            self.canvas.draw_idle()
            
        except Exception as e:
            logger.error(f"Error updating visualization: {e}", exc_info=True)
    
    def _setup_ui(self):
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
    
    def reset_view(self):
        """Reset the 3D view to default settings with performance optimizations."""
        try:
            # Clear the axes more efficiently
            for artist in self.axes.lines + self.axes.collections:
                artist.remove()
            
            # Set labels and title
            self.axes.set_xlabel('X (mm)')
            self.axes.set_ylabel('Y (mm)')
            self.axes.set_zlabel('Z (mm)')
            self.axes.set_title('G-code Toolpath Visualization')
            
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
