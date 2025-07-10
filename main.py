"""
Main application class for the STL to GCode Converter using PyQt6.
"""
import sys
import os
import logging
from pathlib import Path
import datetime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

# Set matplotlib backend to Qt5Agg before importing pyplot
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5Agg backend

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QMessageBox, QListWidget,
                            QProgressBar, QStatusBar, QMenuBar, QMenu, QDockWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import art3d
from stl import mesh

# Import other modules from scripts directory
from scripts.version import __version__
from scripts.about import About
from scripts.sponsor import Sponsor
from scripts.help import show_help
from scripts.updates import check_for_updates
from scripts.ui_qt import UI  # Import the new UI module
from scripts.log_viewer import LogViewer  # Import the LogViewer
from scripts.gcode_optimizer import GCodeOptimizer

class STLToGCodeApp(QMainWindow):
    """
    Main application window for STL to GCode Converter.
    """
    def __init__(self):
        super().__init__()
        self.file_path = None
        
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
        
        # Matplotlib Figure
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Add navigation toolbar with custom styling
        self.toolbar = NavigationToolbar(self.canvas, self)
        self._style_matplotlib_toolbar()
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        # Add panels to main layout with stretch factors
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=3)
    
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
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        
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
                
                # Plot the infill lines at the middle Z height
                for line in infill_lines:
                    x1, y1, x2, y2 = line
                    self.ax.plot([x1, x2], [y1, y2], [mid_z, mid_z], 'b-', linewidth=1, alpha=0.6)
                
            except Exception as e:
                logging.warning(f"Could not generate infill preview: {str(e)}")
        
        # Set labels and title
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('3D View - ' + os.path.basename(file_path))
        
        # Redraw the canvas
        self.canvas.draw()
    
    def _setup_status_bar(self):
        """Set up the status bar with the UI module."""
        self.status_bar = self.ui.create_status_bar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def get_current_settings(self):
        """Get the current settings from the UI."""
        # Default settings - these would typically come from a config file or UI
        settings = {
            'layer_height': 0.2,  # mm
            'nozzle_diameter': 0.4,  # mm
            'extrusion_width': 0.48,  # 120% of nozzle diameter
            'filament_diameter': 1.75,  # mm
            'extrusion_multiplier': 1.0,
            'print_speed': 60,  # mm/s
            'travel_speed': 120,  # mm/s
            'infill_speed': 80,  # mm/s
            'first_layer_speed': 30,  # mm/s
            'retraction_length': 5.0,  # mm
            'retraction_speed': 45,  # mm/s
            'infill_density': 0.2,  # 20%
            'infill_pattern': 'grid',  # grid, lines, triangles, etc.
            'infill_angle': 45,  # degrees
            'infill_optimization': True,  # Enable A* optimized infill
            'infill_resolution': 1.0,  # mm per grid cell for optimized infill
            'brim_width': 0,  # mm
            'skirt_distance': 5.0,  # mm
            'skirt_line_count': 1,
            'support_enabled': False,
            'support_angle': 60,  # degrees
            'support_density': 0.15,
            'support_gap': 0.2,  # mm
            'z_hop': 0.4,  # mm
            'temperature': 200,  # °C
            'bed_temperature': 60,  # °C
            'fan_speed': 100,  # %
            'fan_layer': 2,  # Layer to turn on fan
        }
        
        # Update settings from UI
        settings['infill_density'] = 0.2 if self.optimize_infill_checkbox.isChecked() else 0.0
        settings['infill_resolution'] = self.infill_resolution_spin.value()
        
        return settings
    
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
            
            # Default settings - these would typically come from a config file or UI
            settings = {
                'layer_height': 0.2,  # mm
                'nozzle_diameter': 0.4,  # mm
                'extrusion_width': 0.48,  # 120% of nozzle diameter
                'filament_diameter': 1.75,  # mm
                'extrusion_multiplier': 1.0,
                'print_speed': 60,  # mm/s
                'travel_speed': 120,  # mm/s
                'infill_speed': 80,  # mm/s
                'first_layer_speed': 30,  # mm/s
                'retraction_length': 5.0,  # mm
                'retraction_speed': 45,  # mm/s
                'infill_density': 0.2,  # 20%
                'infill_pattern': 'grid',  # grid, lines, triangles, etc.
                'infill_angle': 45,  # degrees
                'infill_optimization': True,  # Enable A* optimized infill
                'infill_resolution': 1.0,  # mm per grid cell for optimized infill
                'brim_width': 0,  # mm
                'skirt_distance': 5.0,  # mm
                'skirt_line_count': 1,
                'support_enabled': False,
                'support_angle': 60,  # degrees
                'support_density': 0.15,
                'support_gap': 0.2,  # mm
                'z_hop': 0.4,  # mm
                'temperature': 200,  # °C
                'bed_temperature': 60,  # °C
                'fan_speed': 100,  # %
                'fan_layer': 2,  # Layer to turn on fan
            }
            
            # Calculate number of layers
            num_layers = int((max_z - min_z) / settings['layer_height']) + 1
            
            # Start G-code generation
            self.gcode_content = f"; GCode generated by STL to GCode Converter v{__version__}\n"
            self.gcode_content += f"; Source: {os.path.basename(self.file_path)}\n"
            self.gcode_content += f"; Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
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
            
            # Generate G-code for each layer
            for layer_num in range(num_layers):
                current_z = min_z + (layer_num * settings['layer_height'])
                is_first_layer = (layer_num == 0)
                
                # Move to layer height
                if is_first_layer:
                    self.gcode_content += f"\n; Layer 0 (first layer)\n"
                    self.gcode_content += f"G1 Z{settings['layer_height']} F{settings['first_layer_speed']*60} ; Move to first layer height\n"
                    current_speed = settings['first_layer_speed']
                    current_height = settings['layer_height']
                else:
                    self.gcode_content += f"\n; Layer {layer_num}\n"
                    self.gcode_content += f"G1 Z{current_z:.3f} F{settings['print_speed']*60} ; Move to layer height\n"
                    current_speed = settings['print_speed']
                    current_height = current_z
                
                # Get contours for this layer
                contours = self._get_layer_contours(stl_mesh, current_height)
                
                # Optimize travel path using nearest-neighbor algorithm
                if contours:
                    # Flatten contours to points for optimization
                    points = [point for contour in contours for point in contour]
                    current_pos = (0, 0, current_height)  # Assume starting at origin
                    optimized_points = GCodeOptimizer.optimize_travel_path(points, current_pos)
                    
                    # Generate G-code for optimized path
                    for point in optimized_points:
                        x, y, z = point
                        self.gcode_content += f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} E0.1 ; Extrude contour\n"
                
                # Add infill if needed
                if settings['infill_density'] > 0 and not is_first_layer:
                    # Get bounding box of the model
                    min_x = stl_mesh.vectors[:,:,0].min()
                    max_x = stl_mesh.vectors[:,:,0].max()
                    min_y = stl_mesh.vectors[:,:,1].min()
                    max_y = stl_mesh.vectors[:,:,1].max()
                    
                    # Generate optimized infill pattern using A* path planning
                    try:
                        infill_lines = GCodeOptimizer.generate_optimized_infill(
                            bounds=(min_x, min_y, max_x, max_y),
                            angle=settings['infill_angle'],
                            spacing=settings['extrusion_width'] / settings['infill_density'],
                            resolution=settings.get('infill_resolution', 1.0)  # Default 1mm resolution
                        )
                        
                        # Add infill to G-code with optimized path
                        self.gcode_content += "; Optimized infill with A* path planning\n"
                        last_x, last_y = None, None
                        
                        for line in infill_lines:
                            x1, y1, x2, y2 = line
                            
                            # Add travel move to start of line if needed
                            if last_x is not None and (abs(last_x - x1) > 0.01 or abs(last_y - y1) > 0.01):
                                self.gcode_content += f"G0 X{x1:.3f} Y{y1:.3f} F{settings['travel_speed']*60}\n"
                            
                            # Add the infill line
                            self.gcode_content += f"G1 X{x2:.3f} Y{y2:.3f} E0.1 F{settings['infill_speed']*60}\n"
                            
                            last_x, last_y = x2, y2
                            
                    except ImportError as e:
                        # Fall back to basic infill if scikit-image is not available
                        logging.warning("scikit-image not available, using basic infill pattern")
                        infill_lines = GCodeOptimizer.generate_infill_pattern(
                            bounds=(min_x, min_y, max_x, max_y),
                            angle=settings['infill_angle'],
                            spacing=settings['extrusion_width'] / settings['infill_density']
                        )
                        
                        # Add basic infill to G-code
                        self.gcode_content += "; Basic infill (fallback)\n"
                        for line in infill_lines:
                            x1, y1, x2, y2 = line
                            self.gcode_content += f"G1 X{x1:.3f} Y{y1:.3f} F{settings['travel_speed']*60}\n"
                            self.gcode_content += f"G1 X{x2:.3f} Y{y2:.3f} E0.1 F{settings['infill_speed']*60}\n"
                
                # Update progress
                progress = int((layer_num + 1) / num_layers * 100)
                self.statusBar().showMessage(f"Generating G-code... {progress}%")
                QApplication.processEvents()
            
            # End of print
            self.gcode_content += "\n; End of print\n"
            self.gcode_content += "M104 S0 ; Turn off extruder\n"
            self.gcode_content += "M140 S0 ; Turn off bed\n"
            self.gcode_content += "G91 ; Relative positioning\n"
            self.gcode_content += "G1 E-1 F300 ; Retract filament\n"
            self.gcode_content += f"G1 Z{settings['layer_height']+5} E-5 F9000 ; Lift and retract\n"
            self.gcode_content += "G90 ; Absolute positioning\n"
            self.gcode_content += "G28 X0 Y0 ; Home X and Y axes\n"
            self.gcode_content += "M84 ; Disable stepper motors\n"
            self.gcode_content += "M107 ; Turn off fan\n"
            # Enable the view G-code button
            self.view_gcode_button.setEnabled(True)
            
            # Show completion message
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted {os.path.basename(self.file_path)} to GCode.\n"
                f"Layers: {num_layers}\n"
                f"Layer height: {settings['layer_height']}mm\n"
                f"Total height: {max_z-min_z:.2f}mm"
            )
            
            self.statusBar().showMessage("Ready")
            
        except Exception as e:
            self.statusBar().showMessage("Error during conversion")
            QMessageBox.critical(self, "Error", f"Failed to convert to GCode: {str(e)}")
            logging.error(f"Error converting to GCode: {str(e)}")
    
    def _get_layer_contours(self, stl_mesh, z_height):
        """
        Get the contours for a specific layer height from the STL mesh.
        This is a simplified version - a real implementation would use a proper slicing algorithm.
        
        Args:
            stl_mesh: The STL mesh object
            z_height: The Z height to slice at
            
        Returns:
            List of contours, where each contour is a list of (x, y, z) points
        """
        contours = []
        
        # This is a simplified approach - in a real implementation, you would:
        # 1. Find all triangles that intersect with the current Z plane
        # 2. Calculate the intersection lines
        # 3. Connect the lines into closed contours
        # 4. Sort the contours (outer first, then holes)
        
        # For demonstration, we'll just return a simple square contour
        # In a real implementation, this would be replaced with actual contour extraction
        if z_height <= 10:  # Only add contours for the first 10mm
            # Outer contour (square)
            size = 20
            offset = 50
            outer = [
                (offset, offset, z_height),
                (offset + size, offset, z_height),
                (offset + size, offset + size, z_height),
                (offset, offset + size, z_height)
            ]
            contours.append(outer)
            
            # Inner contour (smaller square inside)
            if z_height > 2:  # Only add inner contour after a few layers
                inner_size = 10
                inner_offset = offset + (size - inner_size) / 2
                inner = [
                    (inner_offset, inner_offset, z_height),
                    (inner_offset + inner_size, inner_offset, z_height),
                    (inner_offset + inner_size, inner_offset + inner_size, z_height),
                    (inner_offset, inner_offset + inner_size, z_height)
                ]
                contours.append(inner)
        
        return contours
    
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
