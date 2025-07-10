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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
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
from scripts.stl_processor import load_stl, MemoryEfficientSTLProcessor
from scripts.gcode_simulator import GCodeSimulator, PrinterState
import numpy as np
from PyQt6.Qsci import QsciScintilla, QsciLexerCustom
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer
from scripts.gcode_editor import GCodeEditorWidget
from scripts.gcode_validator import PrinterLimits

try:
    from scripts.opengl_visualizer import OpenGLGCodeVisualizer
    OPENGL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"OpenGL visualization not available: {e}")
    OPENGL_AVAILABLE = False

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
        
        # Initialize G-code simulator
        self.gcode_simulator = GCodeSimulator()
        self.simulation_worker = None
        self.simulation_thread = None
        self.simulation_running = False
        self.simulation_paused = False
        self.current_sim_line = 0
        self.total_sim_lines = 0
        
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
        
        # Add this to the __init__ method where other UI elements are created
        self.use_opengl = OPENGL_AVAILABLE  # Whether to use OpenGL for visualization
        self.opengl_visualizer = None
        
        # Add progressive loading attributes
        self.progressive_loading = True  # Enable progressive loading
        self.loading_progress = 0
        self.current_vertices = np.zeros((0, 3), dtype=np.float32)
        self.current_faces = np.zeros((0, 3), dtype=np.uint32)
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self._process_loading_queue)
        self.loading_queue = []
        self.is_loading = False
        self.current_stl_processor = None
        
        # G-code generation state
        self.gcode_worker = None
        self.gcode_thread = None
        self.gcode_chunks = []
        self.gcode_buffer = ""
        self.gcode_buffer_size = 1024 * 1024  # 1MB buffer
        self.gcode_update_timer = QTimer()
        self.gcode_update_timer.timeout.connect(self._process_gcode_buffer)
        
        # Initialize the UI
        self._init_ui()
        
        # Show the window
        self.show()
        
        # Add default printer limits
        self.printer_limits = PrinterLimits(
            max_x=200, max_y=200, max_z=200,
            max_feedrate=300, max_acceleration=3000,
            max_temperature=300, min_extrusion_temp=170,
            max_fan_speed=255
        )
        
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
        self.convert_button.clicked.connect(self.generate_gcode)
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
        
        # G-code Editor Tab
        self.editor_tab = QWidget()
        self.tab_widget.addTab(self.editor_tab, "G-code Editor")
        self._setup_editor_tab()
        
        # Add panels to main layout with stretch factors
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=3)
        
        # Add this after creating the visualization tab
        if self.use_opengl:
            try:
                self.opengl_visualizer = OpenGLGCodeVisualizer()
                self.visualization_tab.layout().addWidget(self.opengl_visualizer)
                logging.info("OpenGL visualization initialized")
            except Exception as e:
                logging.error(f"Failed to initialize OpenGL visualizer: {e}")
                self.use_opengl = False
    
    def _setup_editor_tab(self):
        """Set up the G-code editor tab."""
        if not hasattr(self, 'editor_widget'):
            self.editor_widget = GCodeEditorWidget()
            self.editor_widget.set_printer_limits(self.printer_limits)
            
            # Connect signals
            self.editor_widget.editor.textChanged.connect(self._on_editor_text_changed)
            
            # Add to tab widget
            self.tab_widget.addTab(self.editor_widget, "G-code Editor")
    
    def _on_editor_text_changed(self):
        """Handle text changes in the editor."""
        # Enable/disable save button based on modifications
        self.save_gcode_action.setEnabled(True)
    
    def validate_gcode(self):
        """Validate the G-code in the editor."""
        if hasattr(self, 'editor_widget'):
            # Validation happens automatically in the editor
            # Just ensure the issues panel is visible
            if self.editor_widget.issues_list.count() > 0:
                self.editor_widget.issues_panel.show()
    
    def open_gcode_in_editor(self):
        """Open a G-code file in the editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open G-code File", "", "G-code Files (*.gcode *.nc *.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                self.editor_widget.set_text(content)
                self.current_file = file_path
                self.setWindowTitle(f"STL to GCode Converter v{__version__} - {os.path.basename(file_path)}")
                self.statusBar().showMessage(f"Loaded {os.path.basename(file_path)}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
    
    def save_gcode_from_editor(self):
        """Save the current editor content to a file."""
        if not hasattr(self, 'current_file') or not self.current_file:
            self.save_gcode()
            return
        
        try:
            with open(self.current_file, 'w') as f:
                f.write(self.editor_widget.get_text())
            
            self.statusBar().showMessage(f"Saved {os.path.basename(self.current_file)}", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def simulate_from_editor(self):
        """Run a simulation from the editor content."""
        if not hasattr(self, 'editor_widget'):
            return
        
        gcode = self.editor_widget.get_text()
        if not gcode.strip():
            QMessageBox.warning(self, "Simulation", "No G-code to simulate")
            return
        
        # Switch to simulation tab
        self.tab_widget.setCurrentWidget(self.simulation_tab)
        
        # Run simulation
        self._start_simulation(gcode)
    
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
        convert_action.triggered.connect(self.generate_gcode)
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
    
    def open_file(self, file_path=None):
        """Open an STL file and load it into the viewer with progressive loading."""
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open STL File", "", "STL Files (*.stl);;All Files (*)"
            )
            
        if not file_path:
            return
            
        try:
            # Reset loading state
            self._reset_loading_state()
            self.statusBar().showMessage(f"Loading {os.path.basename(file_path)}...")
            QApplication.processEvents()
            
            # Initialize the STL processor
            self.current_stl_processor = load_stl(file_path)
            mesh_info = self.current_stl_processor.get_mesh_info()
            
            # Update UI with mesh info
            self.update_mesh_info(mesh_info)
            
            # Enable UI elements
            self.ui.convert_button.setEnabled(True)
            self.ui.export_button.setEnabled(False)
            
            # Store file info
            self.file_path = file_path
            self.current_file = os.path.basename(file_path)
            self.setWindowTitle(f"STL to GCode - {self.current_file}")
            
            # Add to recent files
            self.add_to_recent_files(file_path)
            
            # Start progressive loading
            self._start_progressive_loading()
            
        except Exception as e:
            self._handle_loading_error(e, file_path)
    
    def _reset_loading_state(self):
        """Reset the state for a new loading operation."""
        if self.current_stl_processor:
            try:
                self.current_stl_processor.close()
            except:
                pass
            self.current_stl_processor = None
            
        self.loading_progress = 0
        self.current_vertices = np.zeros((0, 3), dtype=np.float32)
        self.current_faces = np.zeros((0, 3), dtype=np.uint32)
        self.loading_queue = []
        self.is_loading = False
        self.loading_timer.stop()
        self.ax.clear()
        self.canvas.draw()
    
    def _start_progressive_loading(self):
        """Start the progressive loading process in a background thread."""
        if not self.current_stl_processor:
            return
            
        # Setup progress dialog
        self.progress_dialog = QProgressDialog("Loading STL file...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.canceled.connect(self._cancel_loading)
        
        # Start loading in a separate thread
        self.loading_thread = QThread()
        self.loading_worker = STLLoadingWorker(self.current_stl_processor)
        self.loading_worker.moveToThread(self.loading_thread)
        
        # Connect signals
        self.loading_worker.chunk_loaded.connect(self._on_chunk_loaded)
        self.loading_worker.loading_finished.connect(self._on_loading_finished)
        self.loading_worker.error_occurred.connect(self._on_loading_error)
        
        # Start the thread and worker
        self.loading_thread.started.connect(self.loading_worker.start_loading)
        self.loading_thread.start()
        
        # Start the processing timer
        self.loading_timer.start(100)  # Process queue every 100ms
        self.is_loading = True
    
    def _process_loading_queue(self):
        """Process the loading queue to update the 3D view."""
        if not self.loading_queue:
            return
            
        # Process chunks in the queue
        while self.loading_queue:
            chunk = self.loading_queue.pop(0)
            self._process_chunk(chunk)
            
        # Update the 3D view
        self._update_3d_view()
    
    def _process_chunk(self, chunk_data):
        """Process a single chunk of STL data."""
        if not chunk_data or 'vertices' not in chunk_data:
            return
            
        # Update progress
        if 'progress' in chunk_data:
            self.loading_progress = chunk_data['progress']
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.setValue(self.loading_progress)
        
        # Update mesh data
        if len(chunk_data['vertices']) > 0:
            if len(self.current_vertices) == 0:
                self.current_vertices = chunk_data['vertices']
                self.current_faces = chunk_data['faces']
            else:
                vertex_offset = len(self.current_vertices)
                self.current_vertices = np.vstack((self.current_vertices, chunk_data['vertices']))
                
                # Update face indices with the correct offset
                new_faces = chunk_data['faces'] + vertex_offset
                self.current_faces = np.vstack((self.current_faces, new_faces))
    
    def _update_3d_view(self):
        """Update the 3D view with the current mesh data."""
        if len(self.current_vertices) == 0:
            return
            
        try:
            self.ax.clear()
            
            # Only show a subset of triangles for better performance
            if len(self.current_faces) > 50000:
                # For large meshes, show a simplified version
                step = max(1, len(self.current_faces) // 10000)
                faces = self.current_faces[::step]
                self.ax.add_collection3d(art3d.Poly3DCollection(
                    self.current_vertices[faces],
                    alpha=0.5,
                    linewidths=0.1,
                    edgecolor='#666666'
                ))
            else:
                # For smaller meshes, show all triangles
                self.ax.add_collection3d(art3d.Poly3DCollection(
                    self.current_vertices[self.current_faces],
                    alpha=0.5,
                    linewidths=0.5,
                    edgecolor='#666666'
                ))
            
            # Auto-scale the plot
            scale = self.current_vertices.flatten()
            self.ax.auto_scale_xyz(scale, scale, scale)
            
            # Set labels and title
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')
            self.ax.set_title('3D View - ' + self.current_file)
            
            # Redraw the canvas
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error updating 3D view: {e}")
    
    def _on_chunk_loaded(self, chunk_data):
        """Handle a new chunk of STL data."""
        self.loading_queue.append(chunk_data)
    
    def _on_loading_finished(self):
        """Handle completion of the loading process."""
        self.loading_timer.stop()
        self.is_loading = False
        
        # Process any remaining chunks
        while self.loading_queue:
            chunk = self.loading_queue.pop(0)
            self._process_chunk(chunk)
        
        # Final update
        self._update_3d_view()
        
        # Close progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            
        self.statusBar().showMessage(f"Loaded {self.current_file}", 5000)
    
    def _on_loading_error(self, error_message):
        """Handle errors during loading."""
        self.loading_timer.stop()
        self.is_loading = False
        
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            
        QMessageBox.critical(self, "Loading Error", error_message)
        self.statusBar().showMessage("Error loading file", 5000)
    
    def _cancel_loading(self):
        """Cancel the current loading operation."""
        self.loading_timer.stop()
        self.is_loading = False
        
        if hasattr(self, 'loading_worker'):
            self.loading_worker.stop_loading()
            
        if hasattr(self, 'loading_thread'):
            self.loading_thread.quit()
            self.loading_thread.wait()
            
        self._reset_loading_state()
        self.statusBar().showMessage("Loading cancelled", 3000)
    
    def update_mesh_info(self, mesh_info):
        """Update the UI with mesh information."""
        # Update mesh info in the UI
        self.ui.mesh_info_widget.clear()
        self.ui.mesh_info_widget.addItem(f"Triangles: {mesh_info['num_triangles']:,}")
        
        bounds = mesh_info['bounds']
        self.ui.mesh_info_widget.addItem(f"Size: {bounds['size'][0]:.2f} x {bounds['size'][1]:.2f} x {bounds['size'][2]:.2f} mm")
        self.ui.mesh_info_widget.addItem(f"Bounding Box:")
        self.ui.mesh_info_widget.addItem(f"  Min: {bounds['min'][0]:.2f}, {bounds['min'][1]:.2f}, {bounds['min'][2]:.2f}")
        self.ui.mesh_info_widget.addItem(f"  Max: {bounds['max'][0]:.2f}, {bounds['max'][1]:.2f}, {bounds['max'][2]:.2f}")
        self.ui.mesh_info_widget.addItem(f"  Center: {bounds['center'][0]:.2f}, {bounds['center'][1]:.2f}, {bounds['center'][2]:.2f}")
    
    def update_3d_view(self, vertices, faces):
        """Update the 3D view with the given vertices and faces."""
        # Clear previous plot
        self.ax.clear()
        
        # Create a 3D plot of the mesh
        self.ax.add_collection3d(art3d.Poly3DCollection(vertices[faces], alpha=0.5, linewidths=0.5, edgecolor='#666666'))
        
        # Auto-scale the plot
        scale = vertices.flatten()
        self.ax.auto_scale_xyz(scale, scale, scale)
        
        # Set labels and title
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('3D View - ' + os.path.basename(self.file_path))
        
        # Redraw the canvas
        self.canvas.draw()
    
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

    def parse_gcode_for_visualization(self, gcode_text):
        """Parse G-code text into print and travel moves for OpenGL visualization."""
        print_moves = []
        travel_moves = []
        
        # Current position
        current_pos = [0.0, 0.0, 0.0]
        
        for line in gcode_text.split('\n'):
            line = line.split(';', 1)[0].strip()  # Remove comments
            if not line:
                continue
                
            # Handle G0/G1 commands (movement)
            if line.startswith('G0') or line.startswith('G1'):
                # Extract coordinates
                x = None
                y = None
                z = None
                e = None
                
                # Parse parameters
                for part in line.split():
                    if part.startswith('X'):
                        x = float(part[1:])
                    elif part.startswith('Y'):
                        y = float(part[1:])
                    elif part.startswith('Z'):
                        z = float(part[1:])
                    elif part.startswith('E'):
                        e = float(part[1:])
                
                # Update current position
                if x is not None:
                    current_pos[0] = x
                if y is not None:
                    current_pos[1] = y
                if z is not None:
                    current_pos[2] = z
                
                # Add to appropriate list
                if e is not None and e > 0:  # Print move (extrusion)
                    print_moves.append((current_pos[0], current_pos[1], current_pos[2]))
                else:  # Travel move (no extrusion)
                    travel_moves.append((current_pos[0], current_pos[1], current_pos[2]))
        
        return np.array(print_moves), np.array(travel_moves)

    def toggle_visualization_mode(self, use_opengl):
        """Toggle between OpenGL and Matplotlib visualization."""
        if not OPENGL_AVAILABLE and use_opengl:
            QMessageBox.warning(self, "OpenGL Not Available",
                              "OpenGL visualization is not available on this system. "
                              "Falling back to Matplotlib visualization.")
            self.use_opengl = False
            return
            
        self.use_opengl = use_opengl
        
        # Update the visualization if we have G-code loaded
        if hasattr(self, 'current_gcode') and self.current_gcode:
            self.update_visualization(self.current_gcode)

    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up OpenGL resources if they were used
        if hasattr(self, 'opengl_visualizer') and self.opengl_visualizer:
            self.opengl_visualizer.cleanup()
        
        # Call parent close event
        super().closeEvent(event)

    def generate_gcode(self):
        """Generate G-code from the loaded STL file."""
        if not hasattr(self, 'stl_vertices') or not hasattr(self, 'stl_faces'):
            QMessageBox.warning(self, 'Error', 'No STL file loaded')
            return
        
        # Get settings from UI
        settings = {
            'layer_height': float(self.layer_height_input.text()),
            'extrusion_width': float(self.extrusion_width_input.text()),
            'print_speed': float(self.print_speed_input.text()),
            'travel_speed': float(self.travel_speed_input.text()),
            'infill_density': float(self.infill_density_input.text()),
            'infill_pattern': self.infill_pattern_combo.currentText(),
            'enable_retraction': self.retraction_checkbox.isChecked(),
            'retraction_distance': float(self.retraction_distance_input.text()),
            'retraction_speed': float(self.retraction_speed_input.text()),
            'enable_wipe': self.wipe_checkbox.isChecked(),
            'wipe_distance': float(self.wipe_distance_input.text()),
            'enable_optimized_infill': self.optimized_infill_checkbox.isChecked(),
            'infill_resolution': float(self.infill_resolution_input.text())
        }
        
        # Update status
        self.statusBar().showMessage('Generating G-code...')
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        
        # Clear previous G-code
        self.gcode_chunks = []
        self.gcode_buffer = ""
        
        # Create and start the worker thread
        self.gcode_worker = GCodeGenerationWorker(
            self.stl_vertices,
            self.stl_faces,
            settings
        )
        
        self.gcode_thread = QThread()
        self.gcode_worker.moveToThread(self.gcode_thread)
        
        # Connect signals
        self.gcode_worker.progress_updated.connect(self._on_gcode_progress)
        self.gcode_worker.gcode_chunk_ready.connect(self._on_gcode_chunk)
        self.gcode_worker.finished.connect(self._on_gcode_finished)
        self.gcode_worker.error_occurred.connect(self._on_gcode_error)
        
        # Start the thread
        self.gcode_thread.started.connect(self.gcode_worker.run)
        self.gcode_thread.start()
        
        # Start the G-code processing timer
        self.gcode_update_timer.start(100)  # Process buffer every 100ms
    
    def _on_gcode_chunk(self, chunk: str):
        """Handle a new chunk of G-code from the worker thread."""
        # Add the chunk to our buffer
        self.gcode_buffer += chunk
        
        # Process the chunk with the simulator if simulation is enabled
        if hasattr(self, 'enable_simulation') and self.enable_simulation:
            try:
                # Process the chunk line by line
                for line in chunk.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(';'):  # Skip empty lines and comments
                        self.gcode_simulator.process_line(line)
                
                # Update simulation UI if needed
                self._update_simulation_ui()
                
            except Exception as e:
                logger.error(f"Error in G-code simulation: {e}", exc_info=True)
        
        # If buffer is large enough, process it
        if len(self.gcode_buffer) >= self.gcode_buffer_size:
            self._process_gcode_buffer()

    def _process_gcode_buffer(self):
        """Process the buffered G-code and update the visualization."""
        try:
            if not self.gcode_buffer:
                return
                
            # Process the buffer with the visualizer
            if hasattr(self, 'gcode_visualizer'):
                self.gcode_visualizer.append_gcode(self.gcode_buffer)
            
            # Update the G-code editor
            if hasattr(self, 'gcode_editor'):
                self.gcode_editor.moveCursor(QtGui.QTextCursor.End)
                self.gcode_editor.insertPlainText(self.gcode_buffer)
                
                # Auto-scroll to show the latest content
                scrollbar = self.gcode_editor.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            # Clear the buffer
            self.gcode_buffer = ""
            
        except Exception as e:
            logger.error(f"Error processing G-code buffer: {e}", exc_info=True)

    def _update_simulation_ui(self):
        """Update the UI with current simulation state."""
        if not hasattr(self, 'simulation_panel'):
            return
            
        # Update simulation status
        state = self.gcode_simulator.state
        stats = {
            'layer': self.gcode_simulator.current_layer,
            'total_layers': self.gcode_simulator.total_layers,
            'print_time': self.gcode_simulator.print_time,
            'filament_used': self.gcode_simulator.filament_used,
            'travel_distance': self.gcode_simulator.travel_distance,
            'extrusion_distance': self.gcode_simulator.extrusion_distance,
            'feedrate': state.feedrate if state else 0,
            'temperature': state.temperature if state else 0,
            'bed_temperature': state.bed_temperature if state else 0,
            'fan_speed': state.fan_speed if state else 0
        }
        
        # Update UI elements with simulation stats
        if hasattr(self, 'simulation_stats_label'):
            stats_text = (
                f"Layer: {stats['layer']}/{stats['total_layers']} | "
                f"Time: {stats['print_time']:.1f}s | "
                f"Filament: {stats['filament_used']:.1f}m | "
                f"Nozzle: {stats['temperature']}°C | "
                f"Bed: {stats['bed_temperature']}°C | "
                f"Fan: {stats['fan_speed']}%"
            )
            self.simulation_stats_label.setText(stats_text)
        
        # Update error/warning display
        if hasattr(self, 'simulation_errors_text'):
            errors = '\n'.join([f"Line {e.line}: {e.message}" for e in self.gcode_simulator.errors])
            warnings = '\n'.join([f"Line {w.line}: {w.message}" for w in self.gcode_simulator.warnings])
            
            self.simulation_errors_text.setPlainText(
                f"=== Errors ===\n{errors}\n\n"
                f"=== Warnings ===\n{warnings}"
            )
    
    def _on_gcode_progress(self, progress: int):
        """Update the progress bar."""
        self.progress_bar.setValue(progress)
    
    def _on_gcode_finished(self, gcode: str):
        """Handle completion of G-code generation."""
        try:
            # Process any remaining G-code in the buffer
            if self.gcode_buffer:
                self._process_gcode_buffer()
            
            # Stop the update timer
            self.gcode_update_timer.stop()
            
            # Clean up the worker and thread
            self.gcode_worker.deleteLater()
            self.gcode_thread.quit()
            self.gcode_thread.wait()
            self.gcode_thread.deleteLater()
            
            # Update UI
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.statusBar().showMessage('G-code generation completed')
            
            # Enable the save button
            self.save_gcode_button.setEnabled(True)
            
        except Exception as e:
            logger.error(f"Error in G-code generation completion: {e}", exc_info=True)
            self.statusBar().showMessage(f'Error: {str(e)}')
    
    def _on_gcode_error(self, error_msg: str):
        """Handle errors during G-code generation."""
        try:
            # Stop the update timer
            self.gcode_update_timer.stop()
            
            # Clean up the worker and thread
            if self.gcode_worker:
                self.gcode_worker.deleteLater()
            
            if self.gcode_thread:
                self.gcode_thread.quit()
                self.gcode_thread.wait()
                self.gcode_thread.deleteLater()
            
            # Update UI
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            
            # Show error message
            QMessageBox.critical(self, 'G-code Generation Error', error_msg)
            self.statusBar().showMessage('G-code generation failed')
            
        except Exception as e:
            logger.error(f"Error handling G-code generation error: {e}", exc_info=True)
            self.statusBar().showMessage(f'Error: {str(e)}')
    
    def cancel_operation(self):
        """Cancel the current operation (STL loading or G-code generation)."""
        try:
            # Stop any ongoing G-code generation
            if self.gcode_worker:
                self.gcode_worker.stop()
                self.gcode_worker = None
            
            # Stop any ongoing STL loading
            if hasattr(self, 'stl_worker') and self.stl_worker:
                self.stl_worker.stop()
                self.stl_worker = None
            
            # Stop the update timer
            if hasattr(self, 'gcode_update_timer') and self.gcode_update_timer.isActive():
                self.gcode_update_timer.stop()
            
            # Update UI
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.statusBar().showMessage('Operation cancelled')
            
        except Exception as e:
            logger.error(f"Error cancelling operation: {e}", exc_info=True)
            self.statusBar().showMessage(f'Error cancelling operation: {str(e)}')
    
    def toggle_visualization_mode(self):
        """Toggle between Matplotlib and OpenGL visualization."""
        try:
            # Toggle the flag
            self.use_opengl_visualizer = not getattr(self, 'use_opengl_visualizer', False)
            
            # Clear the current visualization
            if hasattr(self, 'visualization_layout') and self.visualization_layout.count() > 0:
                # Remove the current visualizer
                while self.visualization_layout.count() > 0:
                    item = self.visualization_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()
            
            # Create the appropriate visualizer
            if self.use_opengl_visualizer:
                try:
                    from scripts.opengl_visualizer import OpenGLGCodeVisualizer
                    self.opengl_visualizer = OpenGLGCodeVisualizer()
                    self.visualization_layout.addWidget(self.opengl_visualizer)
                    
                    # If we have G-code chunks, add them to the new visualizer
                    if hasattr(self, 'gcode_chunks') and self.gcode_chunks:
                        self.opengl_visualizer.append_gcode('\n'.join(self.gcode_chunks))
                    
                    self.statusBar().showMessage('Using OpenGL visualization')
                except ImportError as e:
                    logger.warning(f"OpenGL visualization not available: {e}")
                    QMessageBox.warning(
                        self,
                        'OpenGL Not Available',
                        'OpenGL visualization is not available on this system. Falling back to Matplotlib.'
                    )
                    self.use_opengl_visualizer = False
                    self._create_matplotlib_visualizer()
            else:
                self._create_matplotlib_visualizer()
            
            # Update the toggle button text
            self.toggle_visualization_button.setText(
                'Use OpenGL Visualization' if not self.use_opengl_visualizer 
                else 'Use Matplotlib Visualization'
            )
            
        except Exception as e:
            logger.error(f"Error toggling visualization mode: {e}", exc_info=True)
            self.statusBar().showMessage(f'Error: {str(e)}')
    
    def _create_matplotlib_visualizer(self):
        """Create and set up the Matplotlib visualizer."""
        try:
            from scripts.gcode_visualizer import GCodeVisualizer
            self.gcode_visualizer = GCodeVisualizer()
            self.visualization_layout.addWidget(self.gcode_visualizer)
            
            # If we have G-code chunks, add them to the new visualizer
            if hasattr(self, 'gcode_chunks') and self.gcode_chunks:
                self.gcode_visualizer.append_gcode('\n'.join(self.gcode_chunks))
            
            self.statusBar().showMessage('Using Matplotlib visualization')
            
        except ImportError as e:
            logger.error(f"Error creating Matplotlib visualizer: {e}", exc_info=True)
            self.statusBar().showMessage('Error: Could not create visualizer')

class STLLoadingWorker(QObject):
    """Worker class for loading STL files in the background."""
    chunk_loaded = pyqtSignal(dict)
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, stl_processor):
        super().__init__()
        self.stl_processor = stl_processor
        self._is_running = False
    
    def start_loading(self):
        """Start the loading process."""
        self._is_running = True
        
        try:
            # Process the STL file in chunks
            for chunk in self.stl_processor.iter_progressive_chunks(
                progress_callback=self._on_progress
            ):
                if not self._is_running:
                    break
                    
                # Emit the chunk for processing
                self.chunk_loaded.emit(chunk)
                
                # Allow the main thread to process events
                QThread.msleep(10)
                
            if self._is_running:
                self.loading_finished.emit()
                
        except Exception as e:
            if self._is_running:
                self.error_occurred.emit(str(e))
        finally:
            self._cleanup()
    
    def stop_loading(self):
        """Stop the loading process."""
        self._is_running = False
    
    def _on_progress(self, progress, total):
        """Handle progress updates."""
        if not self._is_running:
            return
            
        self.chunk_loaded.emit({
            'progress': progress,
            'total_triangles': total
        })
    
    def _cleanup(self):
        """Clean up resources."""
        if self.stl_processor:
            try:
                self.stl_processor.close()
            except:
                pass
            self.stl_processor = None

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
