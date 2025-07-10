"""
Main application class for the STL to GCode Converter using PyQt6.
"""
import sys
import os
import logging
from pathlib import Path
import datetime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QProgressBar, QCheckBox, QDoubleSpinBox, QSplitter
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import art3d
from stl import mesh
from scripts.version import __version__
from scripts.about import About
from scripts.sponsor import Sponsor
from scripts.help import show_help
from scripts.updates import check_for_updates
from scripts.ui_qt import UI  # Import the new UI module
from scripts.log_viewer import LogViewer  # Import the LogViewer
from scripts.gcode_optimizer import GCodeOptimizer
from scripts.workers import GCodeGenerationWorker
from scripts.gcode_visualizer import GCodeVisualizer

class STLToGCodeApp(QMainWindow):
    """
    Main application window for STL to GCode Converter.
    """
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.stl_mesh = None
        self.gcode = ""
        self.current_file = ""
        self.settings = {}
        self.worker_thread = None
        self.worker = None
        
        # Initialize the UI manager
        self.ui = UI()
        
        # Initialize the log viewer
        self.log_viewer = None
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Set up the UI
        self._setup_ui()
        
        # Set up logging
        self._setup_logging()
        
        # Set window properties
        self.setWindowTitle(f"STL to GCode Converter v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Log application start
        logging.info("Application started")
        
    def _setup_ui(self):
        """Set up the main UI components using the UI module."""
        # Set up the menu bar
        self._setup_menus()
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel for controls
        left_panel, left_layout = self.ui.create_frame(central_widget, "vertical")
        
        # File list with label
        left_layout.addWidget(QLabel("Loaded Files:"))
        self.file_list = self.ui.create_file_list(left_panel)
        left_layout.addWidget(self.file_list)
        
        # Buttons with consistent styling
        self.open_button = self.ui.create_button(left_panel, "Open STL File")
        self.open_button.clicked.connect(self.open_file)
        left_layout.addWidget(self.open_button)
        
        # Add infill optimization controls
        infill_group, infill_layout = self.ui.create_frame(left_panel, "vertical")
        
        # Add a title label for the infill settings group
        infill_title = QLabel("<b>Infill Settings</b>")
        infill_title.setStyleSheet("color: #64B5F6; margin-bottom: 5px;")
        infill_layout.addWidget(infill_title)
        
        # Enable optimized infill checkbox
        self.optimize_infill_checkbox = self.ui.create_checkbox(
            infill_group, 
            "Optimize Infill Paths",
            tooltip="Enable A* path planning for optimized infill patterns"
        )
        self.optimize_infill_checkbox.setChecked(True)
        infill_layout.addWidget(self.optimize_infill_checkbox)
        
        # Infill resolution spinbox
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Resolution (mm):"))
        self.infill_resolution_spin = self.ui.create_double_spinbox(
            infill_group,
            minimum=0.1,
            maximum=5.0,
            value=1.0,
            step=0.1,
            decimals=1,
            tooltip="Grid resolution for infill path optimization (smaller = more precise but slower)"
        )
        res_layout.addWidget(self.infill_resolution_spin)
        infill_layout.addLayout(res_layout)
        
        left_layout.addWidget(infill_group)
        
        self.convert_button = self.ui.create_button(left_panel, "Convert to GCode")
        self.convert_button.clicked.connect(self.convert_to_gcode)
        self.convert_button.setEnabled(False)
        left_layout.addWidget(self.convert_button)
        
        # Add G-code viewer button
        self.view_gcode_button = self.ui.create_button(left_panel, "View G-code")
        self.view_gcode_button.clicked.connect(self.view_gcode)
        self.view_gcode_button.setEnabled(False)
        left_layout.addWidget(self.view_gcode_button)
        
        # Add stretch to push buttons to top
        left_layout.addStretch()
        
        # Right panel for 3D preview
        right_panel, right_layout = self.ui.create_frame(central_widget, "vertical")
        
        # Tab widget
        self.tab_widget = QTabWidget()
        right_layout.addWidget(self.tab_widget)
        
        # STL View Tab
        self.stl_view_tab = QWidget()
        self.tab_widget.addTab(self.stl_view_tab, "STL View")
        self._setup_stl_view()
        
        # G-code View Tab
        self.gcode_view_tab = QWidget()
        self.tab_widget.addTab(self.gcode_view_tab, "G-code View")
        self._setup_gcode_view()
        
        # G-code Visualization Tab
        self.visualization_tab = QWidget()
        self.tab_widget.addTab(self.visualization_tab, "3D Toolpath")
        self._setup_visualization_view()
        
        # Add panels to main layout with stretch factors
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=3)
    
    def _setup_stl_view(self):
        """Set up the STL view tab."""
        layout = QVBoxLayout(self.stl_view_tab)
        
        # Matplotlib Figure
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Add navigation toolbar with custom styling
        self.toolbar = NavigationToolbar(self.canvas, self)
        self._style_matplotlib_toolbar()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
    
    def _setup_gcode_view(self):
        """Set up the G-code view tab."""
        layout = QVBoxLayout(self.gcode_view_tab)
        
        # G-code text editor
        self.gcode_editor = self.ui.create_text_editor(self.gcode_view_tab)
        layout.addWidget(self.gcode_editor)
    
    def _setup_visualization_view(self):
        """Set up the G-code visualization tab."""
        layout = QVBoxLayout(self.visualization_tab)
        
        # Create visualization controls
        controls_layout = QHBoxLayout()
        
        self.show_travel_moves = QCheckBox("Show Travel Moves")
        self.show_travel_moves.setChecked(True)
        self.show_travel_moves.stateChanged.connect(self._update_visualization)
        controls_layout.addWidget(self.show_travel_moves)
        
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.clicked.connect(self._reset_visualization_view)
        controls_layout.addWidget(reset_view_btn)
        
        controls_layout.addStretch()
        
        # Add controls to layout
        layout.addLayout(controls_layout)
        
        # Create G-code visualizer
        self.gcode_visualizer = GCodeVisualizer()
        layout.addWidget(self.gcode_visualizer)
    
    def _style_matplotlib_toolbar(self):
        """Apply custom styling to the matplotlib toolbar."""
        # Style the matplotlib toolbar to match our dark theme
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                spacing: 2px;
                padding: 2px;
            }
            QToolButton {
                background-color: #424242;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px;
            }
            QToolButton:hover {
                background-color: #555;
            }
            QToolButton:pressed {
                background-color: #666;
            }
        """)
    
    def _setup_menus(self):
        """Set up the menu bar and menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = file_menu.addAction("&Open STL...")
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut("Ctrl+O")
        
        save_action = file_menu.addAction("&Save GCode As...")
        save_action.triggered.connect(self.save_gcode)
        save_action.setShortcut("Ctrl+Shift+S")
        save_action.setEnabled(False)
        
        file_menu.addSeparator()
        
        # Add Settings action
        settings_action = file_menu.addAction("&Settings...")
        settings_action.triggered.connect(self.show_settings)
        settings_action.setShortcut("Ctrl+,")
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Alt+F4")
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Add toggle for log viewer
        self.toggle_log_viewer_action = view_menu.addAction("Show &Log Viewer")
        self.toggle_log_viewer_action.setCheckable(True)
        self.toggle_log_viewer_action.setChecked(False)
        self.toggle_log_viewer_action.triggered.connect(self.toggle_log_viewer)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        convert_action = tools_menu.addAction("&Convert to GCode")
        convert_action.triggered.connect(self.convert_to_gcode)
        convert_action.setEnabled(False)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # Add Documentation action
        doc_action = help_menu.addAction("&Documentation")
        doc_action.triggered.connect(self.show_documentation)
        doc_action.setShortcut("F1")
        
        help_menu.addSeparator()
        
        help_action = help_menu.addAction("&Help")
        help_action.triggered.connect(lambda: show_help(self))
        
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about)
        
        sponsor_action = help_menu.addAction("&Sponsor")
        sponsor_action.triggered.connect(self.show_sponsor)
        
        check_updates_action = help_menu.addAction("Check for &Updates")
        check_updates_action.triggered.connect(self.check_updates)
        
        # Store actions for later reference
        self.save_action = save_action
        self.convert_action = convert_action
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        logging.captureWarnings(True)
        
        # Log application version
        logging.info(f"STL to GCode Converter v{__version__} starting up...")
    
    def _setup_status_bar(self):
        """Set up the status bar with the UI module."""
        self.status_bar = self.ui.create_status_bar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def open_file(self):
        """Open an STL file and display it in the 3D viewer."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open STL File",
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            try:
                self.file_path = file_path
                self._load_stl(file_path)
                self.convert_button.setEnabled(True)
                # Enable save button if it exists
                if hasattr(self, 'save_button'):
                    self.save_button.setEnabled(True)
                self.statusBar().showMessage(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load STL file: {str(e)}")
                self.statusBar().showMessage("Error loading file")
    
    def _load_stl(self, file_path):
        """Load and display an STL file in the 3D viewer with infill preview."""
        # Clear previous plot
        self.ax.clear()
        
        # Load the STL file
        stl_mesh = mesh.Mesh.from_file(file_path) 
        
        # Create a 3D plot of the mesh
        self.ax.add_collection3d(art3d.Poly3DCollection(stl_mesh.vectors, alpha=0.5, linewidths=0.5, edgecolor='#666666'))
        
        # Auto-scale the plot
        scale = stl_mesh.points.flatten()
        self.ax.auto_scale_xyz(scale, scale, scale)
        
        # Get the current settings for infill
        settings = self.get_current_settings()
        
        # If infill is enabled, show a preview of the infill pattern
        if settings['infill_density'] > 0 and self.optimize_infill_checkbox.isChecked():
            try:
                # Get bounding box of the model
                min_x, max_x = stl_mesh.vectors[:,:,0].min(), stl_mesh.vectors[:,:,0].max()
                min_y, max_y = stl_mesh.vectors[:,:,1].min(), stl_mesh.vectors[:,:,1].max()
                
                # Get the middle layer for preview
                mid_z = (stl_mesh.vectors[:,:,2].min() + stl_mesh.vectors[:,:,2].max()) / 2
                
                # Generate the infill pattern
                infill_lines = GCodeOptimizer.generate_optimized_infill(
                    bounds=(min_x, min_y, max_x, max_y),
                    angle=settings['infill_angle'],
                    spacing=settings['extrusion_width'] / settings['infill_density'],
                    resolution=self.infill_resolution_spin.value()
                )
                
                # Debug: Log the structure of infill_lines
                logging.info(f"Infill lines type: {type(infill_lines)}")
                if hasattr(infill_lines, '__len__'):
                    logging.info(f"Number of infill lines: {len(infill_lines)}")
                    if len(infill_lines) > 0:
                        logging.info(f"First line type: {type(infill_lines[0])}")
                        logging.info(f"First line: {infill_lines[0]}")
                
                # Plot the infill lines at the middle Z height
                for i, line in enumerate(infill_lines):
                    try:
                        # Debug: Log the current line being processed
                        logging.debug(f"Processing line {i}: {line}")
                        # Ensure we have exactly 4 values (x1, y1, x2, y2)
                        if len(line) == 4:
                            x1, y1, x2, y2 = line
                            self.ax.plot([x1, x2], [y1, y2], [mid_z, mid_z], 'b-', linewidth=1, alpha=0.6)
                        else:
                            logging.warning(f"Skipping invalid infill line (length {len(line)}): {line}")
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Error processing infill line {i}: {e} - Line: {line}")
                    except Exception as e:
                        logging.error(f"Unexpected error processing line {i}: {e} - Line: {line}")
                        raise
            except Exception as e:
                logging.warning(f"Could not generate infill preview: {str(e)}")
        
        # Set labels and title
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('3D View - ' + os.path.basename(file_path))
        
        # Redraw the canvas
        self.canvas.draw()
    
    def _update_visualization(self):
        """Update the G-code visualization."""
        if not self.gcode:
            return
            
        try:
            show_travel = self.show_travel_moves.isChecked()
            self.gcode_visualizer.visualize_gcode(self.gcode, show_travel)
        except Exception as e:
            logging.error(f"Error updating visualization: {e}", exc_info=True)
            QMessageBox.critical(self, "Visualization Error", 
                               f"Error updating visualization: {str(e)}")
    
    def _reset_visualization_view(self):
        """Reset the G-code visualization view."""
        self.gcode_visualizer.reset_view()
    
    def convert_to_gcode(self):
        """Convert the loaded STL to GCode with proper slicing and path planning."""
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please open an STL file first.")
            return
        
        # Show progress
        self.statusBar().showMessage("Converting to GCode...")
        QApplication.processEvents()  # Update the UI
        
        try:
            # Load the STL file
            stl_mesh = mesh.Mesh.from_file(self.file_path)
            
            # Get the STL bounds for slicing
            min_z = stl_mesh.vectors[:,:,2].min()
            max_z = stl_mesh.vectors[:,:,2].max()
            
            # Get current settings
            settings = self.get_current_settings()
            
            # Calculate number of layers
            num_layers = int((max_z - min_z) / settings['layer_height']) + 1
            
            # Initialize G-code content
            self.gcode_content = f"; GCode generated by STL to GCode Converter v{__version__}\n"
            self.gcode_content += f"; Source: {os.path.basename(self.file_path)}\n"
            self.gcode_content += f"; Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            self.gcode_content += f"; Optimizations: Arc Detection, Redundant Move Removal, Extrusion Smoothing\n\n"
            
            # Initial setup
            self.gcode_content += "G21 ; Set units to millimeters\n"
            self.gcode_content += "G90 ; Use absolute positioning\n"
            self.gcode_content += "M82 ; Set extruder to absolute mode\n"
            self.gcode_content += "M107 ; Start with the fan off\n"
            
            # Home all axes
            self.gcode_content += "G28 ; Home all axes\n"
            
            # Wait for temperatures
            self.gcode_content += f"M140 S{settings['bed_temperature']} ; Set bed temperature\n"
            self.gcode_content += f"M190 S{settings['bed_temperature']} ; Wait for bed temperature\n"
            self.gcode_content += f"M104 S{settings['temperature']} ; Set extruder temperature\n"
            self.gcode_content += f"M109 S{settings['temperature']} ; Wait for extruder temperature\n\n"
            
            # Start printing
            self.gcode_content += "; Start printing\n"
            self.gcode_content += "G92 E0 ; Reset extruder position\n"
            self.gcode_content += "G1 F1500 E-6 ; Retract filament slightly\n"
            
            # Initialize variables for optimization
            last_pos = {'X': 0, 'Y': 0, 'Z': 0, 'E': 0, 'F': 0}
            gcode_commands = []
            
            # Generate G-code for each layer
            for layer_num in range(num_layers):
                current_z = min_z + (layer_num * settings['layer_height'])
                is_first_layer = (layer_num == 0)
                
                # Layer header
                layer_comment = f"\n; Layer {layer_num} (Z={current_z:.3f}mm)"
                if is_first_layer:
                    layer_comment += " (first layer)"
                gcode_commands.append(layer_comment)
                
                # Move to layer height
                move_cmd = {
                    'Z': current_z,
                    'F': settings['first_layer_speed'] * 60 if is_first_layer else settings['print_speed'] * 60
                }
                gcode_commands.append(self._format_g1_command(move_cmd, last_pos))
                last_pos.update(move_cmd)
                
                # Get contours for this layer
                contours = self._get_layer_contours(stl_mesh, current_z)
                
                if contours:
                    # Optimize contour order
                    optimized_contours = GCodeOptimizer.optimize_contour_order(contours, (last_pos['X'], last_pos['Y']))
                    
                    # Generate G-code for contours
                    for contour in optimized_contours:
                        # Add travel move to start of contour
                        if len(contour) > 0:
                            first_point = contour[0]
                            move_cmd = {
                                'X': first_point[0],
                                'Y': first_point[1],
                                'F': settings['travel_speed'] * 60
                            }
                            gcode_commands.append(self._format_g1_command(move_cmd, last_pos, is_travel=True))
                            last_pos.update(move_cmd)
                        
                        # Add contour with arc detection
                        gcode_commands.extend(
                            self._generate_contour_gcode(
                                contour, 
                                settings,
                                last_pos,
                                is_outer=contour == optimized_contours[0],  # First contour is outer wall
                                is_first_layer=is_first_layer
                            )
                        )
                
                # Add infill if needed
                if settings['infill_density'] > 0 and not is_first_layer:
                    infill_lines = self._generate_infill(stl_mesh, current_z, settings)
                    if infill_lines:
                        gcode_commands.append("\n; Infill")
                        gcode_commands.extend(
                            self._generate_infill_gcode(infill_lines, settings, last_pos)
                        )
            
            # Apply post-processing optimizations
            gcode_commands = GCodeOptimizer.optimize_gcode(gcode_commands)
            
            # Add footer
            gcode_commands.extend([
                "\n; End of G-code",
                "M104 S0 ; Turn off extruder",
                "M140 S0 ; Turn off bed",
                "M107 ; Turn off fan",
                "G1 X0 Y0 F5000 ; Move to origin",
                "M84 ; Disable steppers"
            ])
            
            # Combine all commands
            self.gcode_content = '\n'.join(gcode_commands)
            
            # Enable save button
            self.save_action.setEnabled(True)
            self.statusBar().showMessage("G-code generation complete")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate G-code: {str(e)}")
            self.statusBar().showMessage("Error generating G-code")
            logging.error(f"Error in convert_to_gcode: {str(e)}", exc_info=True)

    # Helper methods for G-code generation
    def _format_g1_command(self, params, last_pos, is_travel=False):
        """Format a G1 command with only changed parameters."""
        cmd = ["G1"]
        for axis in ['X', 'Y', 'Z', 'E', 'F']:
            if axis in params and (axis not in last_pos or abs(params[axis] - last_pos[axis]) > 0.0001):
                cmd.append(f"{axis}{params[axis]:.3f}")
        
        # Add comment for travel moves
        comment = "; Travel" if is_travel else ""
        return ' '.join(cmd) + comment

    def _generate_contour_gcode(self, contour, settings, last_pos, is_outer=True, is_first_layer=False):
        """Generate G-code for a contour with arc detection."""
        commands = []
        current_pos = dict(last_pos)
        
        # Add contour start comment
        contour_type = "Outer wall" if is_outer else "Inner wall"
        commands.append(f"; {contour_type} - {len(contour)} points")
        
        # Detect arcs and generate G2/G3 commands
        points = contour + [contour[0]]  # Close the loop
        i = 0
        
        while i < len(points) - 1:
            # Try to detect an arc starting at this point
            arc = GCodeOptimizer.detect_arc(points[i:i+5])
            
            if arc and len(arc['points']) > 2:
                # Generate arc command
                cmd = {
                    'X': points[i + len(arc['points']) - 1][0],
                    'Y': points[i + len(arc['points']) - 1][1],
                    'I': arc['center'][0] - current_pos['X'],
                    'J': arc['center'][1] - current_pos['Y'],
                    'F': settings['first_layer_speed'] * 60 if is_first_layer else settings['print_speed'] * 60
                }
                
                # Add extrusion
                if not is_travel:
                    distance = math.sqrt(
                        (cmd['X'] - current_pos['X'])**2 + 
                        (cmd['Y'] - current_pos['Y'])**2
                    )
                    extrusion = distance * settings['extrusion_width'] * settings['layer_height'] / (math.pi * (settings['filament_diameter']/2)**2)
                    cmd['E'] = current_pos['E'] + extrusion
                
                # Add arc command (G2 for CW, G3 for CCW)
                arc_cmd = "G3" if arc['direction'] == 'ccw' else "G2"
                cmd_str = [arc_cmd]
                for axis in ['X', 'Y', 'I', 'J', 'E', 'F']:
                    if axis in cmd:
                        cmd_str.append(f"{axis}{cmd[axis]:.3f}")
                
                commands.append(' '.join(cmd_str))
                current_pos.update(cmd)
                i += len(arc['points']) - 1
            else:
                # No arc detected, use linear move
                cmd = {
                    'X': points[i+1][0],
                    'Y': points[i+1][1],
                    'F': settings['first_layer_speed'] * 60 if is_first_layer else settings['print_speed'] * 60
                }
                
                # Add extrusion for non-travel moves
                if not is_travel:
                    distance = math.sqrt(
                        (cmd['X'] - current_pos['X'])**2 + 
                        (cmd['Y'] - current_pos['Y'])**2
                    )
                    extrusion = distance * settings['extrusion_width'] * settings['layer_height'] / (math.pi * (settings['filament_diameter']/2)**2)
                    cmd['E'] = current_pos['E'] + extrusion
                
                commands.append(self._format_g1_command(cmd, current_pos, is_travel=is_travel))
                current_pos.update(cmd)
                i += 1
        
        return commands

    def _generate_infill(self, stl_mesh, z, settings):
        """Generate infill lines for the current layer."""
        # Get bounds of the model
        min_x, min_y = stl_mesh.vectors[:,:,0].min(), stl_mesh.vectors[:,:,1].min()
        max_x, max_y = stl_mesh.vectors[:,:,0].max(), stl_mesh.vectors[:,:,1].max()
        bounds = (min_x, min_y, max_x, max_y)
        
        # Generate infill pattern
        if settings.get('infill_optimization', True):
            try:
                return GCodeOptimizer.generate_optimized_infill(
                    bounds=bounds,
                    angle=settings['infill_angle'],
                    spacing=settings['extrusion_width'] / settings['infill_density'],
                    resolution=settings.get('infill_resolution', 1.0)
                )
            except Exception as e:
                logging.warning(f"Optimized infill failed, falling back to basic infill: {e}")
        
        # Fall back to basic infill
        return GCodeOptimizer.generate_infill_pattern(
            bounds=bounds,
            angle=settings['infill_angle'],
            spacing=settings['extrusion_width'] / settings['infill_density']
        )

    def _generate_infill_gcode(self, infill_lines, settings, last_pos):
        """Generate G-code for infill lines."""
        commands = []
        current_pos = dict(last_pos)
        
        for i, line in enumerate(infill_lines):
            if len(line) == 4:  # Should be (x1, y1, x2, y2)
                x1, y1, x2, y2 = line
                
                # Travel to start of line
                move_cmd = {
                    'X': x1,
                    'Y': y1,
                    'F': settings['travel_speed'] * 60
                }
                commands.append(self._format_g1_command(move_cmd, current_pos, is_travel=True))
                current_pos.update(move_cmd)
                
                # Extrude to end of line
                move_cmd = {
                    'X': x2,
                    'Y': y2,
                    'F': settings['infill_speed'] * 60
                }
                
                # Calculate extrusion
                distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                extrusion = distance * settings['extrusion_width'] * settings['layer_height'] / (math.pi * (settings['filament_diameter']/2)**2)
                move_cmd['E'] = current_pos['E'] + extrusion
                
                commands.append(self._format_g1_command(move_cmd, current_pos))
                current_pos.update(move_cmd)
        
        return commands
    
    def view_gcode(self):
        """Open the G-code viewer with the current G-code."""
        if hasattr(self, 'gcode_content') and self.gcode_content:
            # Create a temporary file to store the G-code
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False, mode='w') as f:
                f.write(self.gcode_content)
                temp_path = f.name
            
            # Open the G-code viewer
            from scripts.gcode_viewer_qt import GCodeViewer
            viewer = GCodeViewer(self)
            viewer.display_gcode(temp_path)
            viewer.exec()
            
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logging.warning(f"Failed to delete temporary G-code file: {e}")
        else:
            QMessageBox.information(self, "No G-code", "No G-code has been generated yet.")
    
    def save_gcode(self):
        """Save the generated GCode to a file."""
        if not self.file_path:
            QMessageBox.warning(self, "No File", "No file to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GCode",
            f"{os.path.splitext(self.file_path)[0]}.gcode",
            "GCode Files (*.gcode);;All Files (*)"
        )
        
        if file_path:
            try:
                # In a real application, this would save the actual GCode
                with open(file_path, 'w') as f:
                    f.write("; GCode generated by STL to GCode Converter\n")
                    f.write(f"; Source: {os.path.basename(self.file_path)}\n\n")
                    # Add sample GCode commands
                    f.write("G28 ; Home all axes\n")
                    f.write("G1 Z10 F5000 ; Move up\n")
                    # ... more GCode commands would go here
                
                self.statusBar().showMessage(f"Saved GCode to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save GCode: {str(e)}")
                self.statusBar().showMessage("Error saving file")
    
    def show_about(self):
        """Show the About dialog."""
        About.show_about(self)  # Call the static method with self as parent
    
    def show_sponsor(self):
        """Show the Sponsor dialog."""
        sponsor = Sponsor(self)
        sponsor.show_sponsor()  # Call the show_sponsor method instead of exec()
    
    def check_updates(self):
        """Check for application updates."""
        check_for_updates(self, __version__)

    def toggle_log_viewer(self, checked):
        """Toggle the visibility of the log viewer."""
        if checked:
            if not self.log_viewer:
                self.log_viewer = LogViewer(self)
                self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_viewer)
            self.log_viewer.show()
        else:
            if self.log_viewer:
                self.log_viewer.hide()
        
        # Update the menu action text
        self.toggle_log_viewer_action.setText(
            "Hide &Log Viewer" if checked else "Show &Log Viewer"
        )

    def show_documentation(self):
        """Show the documentation viewer."""
        from scripts.markdown_viewer import show_documentation
        show_documentation(self)

    def show_settings(self):
        """Show the settings dialog."""
        from scripts.settings_dialog import SettingsDialog
        
        # Get current settings
        current_settings = self.get_current_settings()
        
        # Create and show the settings dialog
        dialog = SettingsDialog(current_settings, self)
        
        # Connect the settings_changed signal
        dialog.settings_changed.connect(self._on_settings_changed)
        
        # Show the dialog
        dialog.exec()
    
    def _on_settings_changed(self, settings):
        """Handle settings changes."""
        # Update the settings in the application
        self.settings = settings
        
        # Update the UI to reflect the new settings
        self._update_ui_from_settings()
        
        # Save settings to disk if needed
        self._save_settings()
    
    def _update_ui_from_settings(self):
        """Update the UI to reflect the current settings."""
        # Update any UI elements that depend on settings
        if hasattr(self, 'infill_density_slider'):
            self.infill_density_slider.setValue(int(self.settings.get('infill_density', 0.2) * 100))
        
        if hasattr(self, 'layer_height_spin'):
            self.layer_height_spin.setValue(self.settings.get('layer_height', 0.2))
        
        # Update other UI elements as needed...
    
    def _save_settings(self):
        """Save settings to disk."""
        # In a real application, you would save these to a config file
        # For now, we'll just store them in memory
        pass

    def _start_gcode_generation(self):
        """Start G-code generation in a background thread."""
        if self.stl_mesh is None:
            return
        
        # Clear previous G-code
        self.gcode = ""
        
        # Create worker and thread
        self.worker = GCodeGenerationWorker(self.stl_mesh, self.get_current_settings())
        self.worker_thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.progress.connect(self._on_generation_progress)
        self.worker.gcode_chunk.connect(self._on_gcode_chunk)
        self.worker.preview_ready.connect(self._on_preview_ready)
        
        # Start the thread
        self.worker_thread.started.connect(self.worker.generate)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        # Update UI
        self._update_ui_state()
        self.ui.statusBar().showMessage("Generating G-code...")
        
        # Start the thread
        self.worker_thread.start()
    
    def _on_generation_finished(self):
        """Handle successful completion of G-code generation."""
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker = None
        self.worker_thread = None
        
        # Update UI
        self._update_ui_state()
        self.ui.statusBar().showMessage("G-code generation completed", 5000)
        
        # Enable save and view buttons
        self.ui.save_button.setEnabled(True)
        self.ui.view_button.setEnabled(True)
    
    def _on_generation_error(self, error_msg):
        """Handle errors during G-code generation."""
        if self.worker_thread is not None:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker = None
            self.worker_thread = None
        
        # Show error message
        QMessageBox.critical(self, "G-code Generation Error", 
                            f"An error occurred during G-code generation:\n\n{error_msg}")
        
        # Update UI
        self._update_ui_state()
        self.ui.statusBar().showMessage("G-code generation failed", 5000)
    
    def _on_generation_progress(self, current, total):
        """Update progress during G-code generation."""
        self.ui.progress_bar.setMaximum(total)
        self.ui.progress_bar.setValue(current)
        self.ui.statusBar().showMessage(
            f"Generating G-code... Layer {current} of {total}")
    
    def _on_gcode_chunk(self, chunk):
        """Append a chunk of generated G-code to the output."""
        self.gcode += chunk
    
    def _on_preview_ready(self, preview_data):
        """Update the 3D preview with the generated paths."""
        # This would be implemented to update the 3D view with the preview data
        pass
    
    def _update_ui_state(self):
        """Update the UI state based on current application state."""
        # Enable/disable buttons based on state
        has_stl = self.stl_mesh is not None
        has_gcode = bool(self.gcode)
        is_processing = self.worker_thread is not None
        
        self.ui.action_convert.setEnabled(has_stl and not is_processing)
        self.ui.convert_button.setEnabled(has_stl and not is_processing)
        self.ui.action_save.setEnabled(has_gcode and not is_processing)
        self.ui.save_button.setEnabled(has_gcode and not is_processing)
        self.ui.action_view_gcode.setEnabled(has_gcode)
        self.ui.view_button.setEnabled(has_gcode)
        self.ui.cancel_button.setEnabled(is_processing)
        
        # Update progress bar visibility
        self.ui.progress_bar.setVisible(is_processing)
        
        # Disable settings during processing
        self.ui.settings_group.setEnabled(not is_processing)

def main():
    """Application entry point."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('stl_to_gcode.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create and run the application
    app = QApplication(sys.argv)
    
    # Set application style and palette
    app.setStyle('Fusion')
    
    # Set application metadata
    app.setApplicationName("STL to GCode Converter")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("STLtoGCode")
    
    # Set application icon for taskbar/dock
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = STLToGCodeApp()
    window.show()
    
    # Handle command line arguments
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        window.open_file(sys.argv[1])
    
    sys.exit(app.exec())

if __name__ == "__main__":
    # Enable sharing of OpenGL contexts for WebEngine
    from PyQt6.QtCore import Qt, QCoreApplication
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    
    main()
