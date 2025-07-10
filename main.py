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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
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
    # Try importing from QtOpenGLWidgets first (PyQt6 >= 6.2.0)
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtOpenGL import QOpenGLContext, QOpenGLVersionProfile
    from scripts.opengl_visualizer import OpenGLGCodeVisualizer
    OPENGL_AVAILABLE = True
except (ImportError, AttributeError) as e:
    try:
        # Fall back to QtOpenGL for older versions
        from PyQt6.QtOpenGL import QOpenGLWidget, QOpenGLContext, QOpenGLVersionProfile
        from scripts.opengl_visualizer import OpenGLGCodeVisualizer
        OPENGL_AVAILABLE = True
    except (ImportError, AttributeError) as e:
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
        
        # Set default printer limits (in mm) - must be before _setup_ui()
        self.printer_limits = {
            'x_min': 0,
            'x_max': 400,  # 400mm X-axis
            'y_min': 0,
            'y_max': 400,  # 400mm Y-axis
            'z_min': 0,
            'z_max': 400,  # 400mm Z-axis
            'feedrate': 3000,  # mm/min
            'travel_feedrate': 4800  # mm/min
        }
        
        # Initialize UI components
        self._setup_ui()
        
        # Show the window
        self.show()
        
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
        infill_group, inffill_layout = self.ui.create_frame(left_panel, "vertical")
        
        # Add a title label for the infill settings group
        infill_title = QLabel("<b>Infill Settings</b>")
        infill_title.setStyleSheet("color: #64B5F6; margin-bottom: 5px;")
        inffill_layout.addWidget(infill_title)
        
        # Enable optimized infill checkbox
        self.optimize_infill_checkbox = self.ui.create_checkbox(
            infill_group, 
            "Optimize Infill Paths",
            tooltip="Enable A* path planning for optimized infill patterns"
        )
        self.optimize_infill_checkbox.setChecked(True)
        inffill_layout.addWidget(self.optimize_infill_checkbox)
        
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
        inffill_layout.addLayout(res_layout)
        
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
                self, "Open STL File", "", "STL Files (*.stl);;All Files (*)")
        
        if not file_path:
            logging.debug("No file selected")
            return
            
        try:
            logging.info(f"Opening file: {file_path}")
            self._reset_loading_state()
            self.statusBar().showMessage(f"Loading {os.path.basename(file_path)}...")
            QApplication.processEvents()
        
            # Initialize the STL processor
            self.current_stl_processor = MemoryEfficientSTLProcessor(file_path, chunk_size=1000)
        
            # Store file info
            self.file_path = file_path
            self.current_file = os.path.basename(file_path)
            self.setWindowTitle(f"STL to GCode - {self.current_file}")
        
            # Add to recent files
            self.add_to_recent_files(file_path)
        
            # Start progressive loading
            logging.debug("Starting progressive loading")
            self._start_progressive_loading()
        
        except Exception as e:
            logging.error(f"Error opening file: {str(e)}", exc_info=True)
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
        
        # Only clear the visualization if it's been initialized
        if hasattr(self, 'ax') and hasattr(self, 'canvas'):
            try:
                self.ax.clear()
                self.canvas.draw()
            except Exception as e:
                logging.warning(f"Error resetting visualization: {str(e)}")
    
    def _start_progressive_loading(self):
        """Start the progressive loading process in a background thread."""
        if not self.current_stl_processor:
            logging.error("No STL processor available")
            return
        
        try:
            # Setup progress dialog
            self.progress_dialog = QProgressDialog("Loading STL file...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.canceled.connect(self._cancel_loading)
            
            # Configure chunk size (triangles per chunk)
            chunk_size = 1000  # Process 1000 triangles per chunk
            
            # Create and configure worker thread
            self.loading_thread = QThread()
            self.loading_worker = STLLoadingWorker(
                stl_processor=self.current_stl_processor,
                chunk_size=chunk_size
            )
            self.loading_worker.moveToThread(self.loading_thread)
            
            # Connect signals
            self.loading_worker.chunk_loaded.connect(self._on_chunk_loaded)
            self.loading_worker.loading_finished.connect(self._on_loading_finished)
            self.loading_worker.error_occurred.connect(self._on_loading_error)
            self.loading_worker.progress_updated.connect(self._update_loading_progress)
            
            # Clean up thread when done
            self.loading_worker.finished.connect(self.loading_thread.quit)
            self.loading_worker.finished.connect(self.loading_worker.deleteLater)
            self.loading_thread.finished.connect(self.loading_thread.deleteLater)
            
            # Start the thread and worker
            self.loading_thread.start()
            
            # Use a single-shot timer to start the worker in its thread
            QTimer.singleShot(0, self.loading_worker.start_loading)
            
            # Start the processing timer
            self.loading_timer.start(100)  # Process queue every 100ms
            self.is_loading = True
            
            logging.info("Started progressive loading thread")
            
        except Exception as e:
            logging.error(f"Error starting progressive loading: {str(e)}", exc_info=True)
            self._handle_loading_error(e, "Error starting loading process")
    
    def _process_loading_queue(self):
        """Process the loading queue to update the 3D view."""
        if not self.loading_queue:
            logging.debug("No chunks in queue to process")
            return
            
        logging.debug(f"Processing {len(self.loading_queue)} chunks from queue")
        try:
            # Process chunks in the queue
            while self.loading_queue:
                chunk = self.loading_queue.pop(0)
                self._process_chunk(chunk)
                
            # Update the 3D view
            logging.debug("Updating 3D view")
            self._update_visualization()
            
        except Exception as e:
            logging.error(f"Error processing loading queue: {str(e)}", exc_info=True)

    def _on_chunk_loaded(self, chunk_data):
        """Handle a new chunk of STL data."""
        try:
            logging.debug(f"Chunk received: {len(chunk_data.get('vertices', []))} vertices, "
                       f"{len(chunk_data.get('faces', []))} faces")
            self.loading_queue.append(chunk_data)
            logging.debug(f"Queue size: {len(self.loading_queue)}")
        except Exception as e:
            logging.error(f"Error handling chunk: {str(e)}", exc_info=True)

    def _process_chunk(self, chunk_data):
        """Process a single chunk of STL data."""
        if not chunk_data or 'vertices' not in chunk_data:
            logging.warning("Received empty or invalid chunk data")
            return
            
        try:
            # Update progress
            if 'progress' in chunk_data:
                self.loading_progress = chunk_data['progress']
                if hasattr(self, 'progress_dialog'):
                    self.progress_dialog.setValue(self.loading_progress)
            
            # Update mesh data
            if len(chunk_data['vertices']) > 0:
                logging.debug(f"Processing chunk with {len(chunk_data['vertices'])} vertices, "
                           f"{len(chunk_data['faces'])} faces")
                if len(self.current_vertices) == 0:
                    self.current_vertices = chunk_data['vertices']
                    self.current_faces = chunk_data['faces']
                    logging.debug("Initialized vertex and face arrays")
                else:
                    vertex_offset = len(self.current_vertices)
                    logging.debug(f"Appending to existing arrays. Current vertices: {vertex_offset}")
                    self.current_vertices = np.vstack((self.current_vertices, chunk_data['vertices']))
                    
                    # Update face indices with the correct offset
                    new_faces = chunk_data['faces'] + vertex_offset
                    self.current_faces = np.vstack((self.current_faces, new_faces))
                    logging.debug(f"Updated arrays. Total vertices: {len(self.current_vertices)}, "
                               f"Total faces: {len(self.current_faces)}")
        except Exception as e:
            logging.error(f"Error processing chunk: {str(e)}", exc_info=True)
            raise

    def _on_loading_finished(self):
        """Handle completion of the loading process."""
        logging.info("Loading finished")
        self.loading_timer.stop()
        self.is_loading = False
        
        try:
            # Process any remaining chunks
            logging.debug(f"Processing remaining {len(self.loading_queue)} chunks")
            while self.loading_queue:
                chunk = self.loading_queue.pop(0)
                self._process_chunk(chunk)
            
            # Final update
            logging.debug("Performing final 3D view update")
            self._update_visualization()
            
            # Close progress dialog
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
                
            self.statusBar().showMessage(f"Loaded {self.current_file}", 5000)
            logging.info(f"Successfully loaded {self.current_file}")
            
        except Exception as e:
            logging.error(f"Error finalizing loading: {str(e)}", exc_info=True)

    def _process_gcode_buffer(self):
        """Process the G-code buffer and update the editor."""
        if not self.gcode_buffer:
            return
            
        try:
            # Get the current cursor position
            cursor = self.gcode_editor.textCursor()
            position = cursor.position()
            
            # Append the buffered G-code to the editor
            self.gcode_editor.moveCursor(cursor.End)
            self.gcode_editor.insertPlainText(self.gcode_buffer)
            self.gcode_buffer = ""
            
            # Restore the cursor position
            cursor.setPosition(position)
            self.gcode_editor.setTextCursor(cursor)
            
        except Exception as e:
            logging.error(f"Error processing G-code buffer: {str(e)}", exc_info=True)
    
    def save_gcode(self):
        """Save the current G-code to a file."""
        try:
            if not hasattr(self, 'gcode_editor') or not self.gcode_editor.toPlainText():
                QMessageBox.warning(self, "No G-code", "No G-code to save.")
                return
                
            # Get the G-code from the editor
            gcode = self.gcode_editor.toPlainText()
            
            # Get the default filename based on the STL filename if available
            default_filename = ""
            if hasattr(self, 'current_file') and self.current_file:
                default_filename = os.path.splitext(self.current_file)[0] + ".gcode"
            
            # Open file dialog to select save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save G-code", 
                default_filename,
                "G-code Files (*.gcode *.nc);;All Files (*)"
            )
            
            if file_path:
                # Ensure the file has the correct extension
                if not file_path.lower().endswith(('.gcode', '.nc')):
                    file_path += ".gcode"
                
                # Write the G-code to the file
                with open(file_path, 'w') as f:
                    f.write(gcode)
                
                self.statusBar().showMessage(f"G-code saved to {os.path.basename(file_path)}", 5000)
                logging.info(f"G-code saved to {file_path}")
                
        except Exception as e:
            error_msg = f"Error saving G-code: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def show_settings(self):
        """Show the application settings dialog."""
        try:
            # Import the settings dialog here to avoid circular imports
            from scripts.settings_dialog import SettingsDialog
            from PyQt6.QtWidgets import QDialog  # Add this import
            
            # Initialize settings if not already set
            if not hasattr(self, 'settings') or not self.settings:
                self.settings = {}
            
            # Create and show the settings dialog with settings as first argument
            dialog = SettingsDialog(settings=self.settings, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:  # Use QDialog.DialogCode
                # Save the settings
                self.settings = dialog.get_settings()
                self.statusBar().showMessage("Settings saved", 3000)
                logging.info("Application settings updated")
                
                # Apply any settings that need immediate effect
                self._apply_settings()
                
        except ImportError as e:
            error_msg = "Settings dialog not available"
            logging.error(f"{error_msg}: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"{error_msg}. Please check the installation.")
        except Exception as e:
            error_msg = f"Error showing settings: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _apply_settings(self):
        """Apply the current settings to the application."""
        try:
            # Apply theme if specified in settings
            if 'theme' in self.settings:
                self._apply_theme(self.settings['theme'])
                
            # Apply editor settings if available
            if hasattr(self, 'gcode_editor') and 'editor' in self.settings:
                editor_settings = self.settings['editor']
                if 'font_size' in editor_settings:
                    font = self.gcode_editor.font()
                    font.setPointSize(editor_settings['font_size'])
                    self.gcode_editor.setFont(font)
                
            logging.debug("Applied application settings")
            
        except Exception as e:
            logging.error(f"Error applying settings: {str(e)}", exc_info=True)
    
    def _apply_theme(self, theme_name):
        """Apply the specified theme to the application.
        
        Args:
            theme_name: Name of the theme to apply (e.g., 'dark', 'light')
        """
        try:
            # This is a basic implementation - customize as needed
            if theme_name.lower() == 'dark':
                self.setStyleSheet("""
                    QMainWindow, QDialog {
                        background-color: #2b2b2b;
                        color: #e0e0e0;
                    }
                    QPushButton {
                        background-color: #3c3f41;
                        border: 1px solid #555555;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #4e5254;
                    }
                    QPushButton:pressed {
                        background-color: #2c2f30;
                    }
                """)
            else:  # Default light theme
                self.setStyleSheet("")
                
            logging.info(f"Applied theme: {theme_name}")
            
        except Exception as e:
            logging.error(f"Error applying theme '{theme_name}': {str(e)}", exc_info=True)
    
    def toggle_log_viewer(self):
        """Toggle the visibility of the log viewer."""
        try:
            if not hasattr(self, 'log_viewer') or not self.log_viewer:
                # Create and show the log viewer if it doesn't exist
                from scripts.log_viewer import LogViewer
                self.log_viewer = LogViewer()
                self.log_viewer.show()
                self.toggle_log_viewer_action.setText("Hide Log Viewer")
                logging.info("Log viewer opened")
            else:
                # Toggle visibility if it exists
                if self.log_viewer.isVisible():
                    self.log_viewer.hide()
                    self.toggle_log_viewer_action.setText("Show Log Viewer")
                    logging.debug("Log viewer hidden")
                else:
                    self.log_viewer.show()
                    self.toggle_log_viewer_action.setText("Hide Log Viewer")
                    logging.debug("Log viewer shown")
                    
        except ImportError as e:
            error_msg = "Log viewer module not available"
            logging.error(f"{error_msg}: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"{error_msg}. Please check the installation.")
        except Exception as e:
            error_msg = f"Error toggling log viewer: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)

    def generate_gcode(self):
        """Generate G-code from the current STL model."""
        try:
            if not hasattr(self, 'stl_mesh') or self.stl_mesh is None:
                QMessageBox.warning(self, "No Model", "Please load an STL file first.")
                return
                
            # Show progress dialog
            self.progress_dialog = QProgressDialog("Generating G-code...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            
            # Get current settings (you may want to get these from a settings dialog)
            settings = {
                'layer_height': 0.2,
                'extrusion_width': 0.4,
                'filament_diameter': 1.75,
                'print_speed': 60,
                'travel_speed': 120,
                'infill_speed': 60,
                'first_layer_speed': 30,
                'retraction_length': 5,
                'retraction_speed': 40,
                'z_hop': 0.2,
                'infill_density': 20,
                'infill_pattern': 'grid',
                'infill_angle': 45,
                'enable_arc_detection': True,
                'arc_tolerance': 0.05,
                'min_arc_segments': 5,
                'enable_optimized_infill': True,
                'infill_resolution': 1.0,
                'start_gcode': "; Custom start G-code\nG28 ; Home all axes\nG1 Z5 F5000 ; Lift nozzle\n",
                'end_gcode': "; Custom end G-code\nM104 S0 ; Turn off extruder\nM140 S0 ; Turn off bed\nG28 X0 Y0 ; Home X and Y axes\nM84 ; Disable motors\n",
                'bed_temp': 60,
                'extruder_temp': 200,
                'fan_speed': 100,
                'material': 'PLA'
            }
            
            # Create worker and thread for G-code generation
            self.gcode_thread = QThread()
            self.gcode_worker = GCodeGenerationWorker(self.stl_mesh, settings)
            self.gcode_worker.moveToThread(self.gcode_thread)
            
            # Connect signals
            self.gcode_worker.progress.connect(self._update_generation_progress)
            self.gcode_worker.gcode_chunk.connect(self._process_gcode_chunk)
            self.gcode_worker.preview_ready.connect(self._update_preview)
            self.gcode_worker.finished.connect(self._on_gcode_generation_finished)
            self.gcode_worker.error.connect(self._on_gcode_generation_error)
            
            # Start the thread and worker
            self.gcode_thread.started.connect(self.gcode_worker.generate)
            self.gcode_thread.start()
            
            # Enable cancel button
            self.progress_dialog.canceled.connect(self._cancel_gcode_generation)
            
            logging.info("Started G-code generation")
            
        except Exception as e:
            error_msg = f"Error starting G-code generation: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _update_generation_progress(self, current, total):
        """Update the progress dialog with the current generation progress."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(current)
            
            # Update status bar
            self.statusBar().showMessage(f"Generating G-code: {current}/{total} layers")
    
    def _process_gcode_chunk(self, chunk):
        """Process a chunk of generated G-code."""
        try:
            if not hasattr(self, 'gcode_buffer'):
                self.gcode_buffer = ""
                
            self.gcode_buffer += chunk
            
            # If buffer is large enough, update the editor
            if len(self.gcode_buffer) > self.gcode_buffer_size:
                self._process_gcode_buffer()
                
        except Exception as e:
            logging.error(f"Error processing G-code chunk: {str(e)}", exc_info=True)
    
    def _update_preview(self, preview_data):
        """Update the 3D preview with the generated G-code."""
        try:
            # This would be implemented to update the 3D preview
            # with the generated G-code paths
            logging.debug(f"Received preview data with {len(preview_data.get('paths', []))} paths")
            
        except Exception as e:
            logging.error(f"Error updating preview: {str(e)}", exc_info=True)
    
    def _on_gcode_generation_finished(self):
        """Handle completion of G-code generation."""
        try:
            # Process any remaining G-code in the buffer
            if hasattr(self, 'gcode_buffer') and self.gcode_buffer:
                self._process_gcode_buffer()
                
            # Clean up
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
                
            if hasattr(self, 'gcode_thread') and self.gcode_thread.isRunning():
                self.gcode_thread.quit()
                self.gcode_thread.wait()
                
            self.statusBar().showMessage("G-code generation completed", 5000)
            logging.info("G-code generation completed successfully")
            
        except Exception as e:
            logging.error(f"Error finalizing G-code generation: {str(e)}", exc_info=True)
    
    def _on_gcode_generation_error(self, error_msg):
        """Handle errors during G-code generation."""
        try:
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
                
            QMessageBox.critical(self, "G-code Generation Error", error_msg)
            self.statusBar().showMessage("G-code generation failed", 5000)
            logging.error(f"G-code generation error: {error_msg}")
            
        except Exception as e:
            logging.error(f"Error handling G-code generation error: {str(e)}", exc_info=True)
    
    def _cancel_gcode_generation(self):
        """Cancel the ongoing G-code generation."""
        try:
            if hasattr(self, 'gcode_worker') and self.gcode_worker:
                self.gcode_worker.cancel()
                
            if hasattr(self, 'gcode_thread') and self.gcode_thread.isRunning():
                self.gcode_thread.quit()
                self.gcode_thread.wait()
                
            self.statusBar().showMessage("G-code generation cancelled", 5000)
            logging.info("G-code generation cancelled by user")
            
        except Exception as e:
            logging.error(f"Error cancelling G-code generation: {str(e)}", exc_info=True)

    def show_documentation(self):
        """Open the application's documentation in the default web browser."""
        try:
            # Try to use the documentation URL from settings if available
            doc_url = getattr(self, 'documentation_url', 
                            "https://github.com/yourusername/STL_to_G-Code/wiki")
            
            # Open the URL in the default web browser
            import webbrowser
            webbrowser.open(doc_url)
            logging.info(f"Opened documentation: {doc_url}")
            
        except Exception as e:
            error_msg = f"Failed to open documentation: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(
                self, 
                "Documentation Error",
                f"Could not open documentation. Please visit the project's GitHub page for documentation.\n\nError: {str(e)}"
            )

    def show_about(self):
        """Show the About dialog with application information."""
        try:
            # Get application information
            app_name = "STL to G-Code Converter"
            version = "1.0.0"
            year = "2025"
            author = "Your Name"
            email = "your.email@example.com"
            github = "https://github.com/yourusername/STL_to_G-Code"
            
            # Create the about text with HTML formatting
            about_text = f"""
            <h3>{app_name} v{version}</h3>
            <p>Convert 3D STL models to G-code for 3D printing.</p>
            <p>Copyright {year} {author}<br>
            <a href="mailto:{email}">{email}</a><br>
            <a href="{github}">{github}</a></p>
            <p>This application is open source and released under the MIT License.</p>
            <p>Built with Python, PyQt6, and numpy-stl.</p>
            """
            
            # Create and show the about dialog
            about_dialog = QMessageBox(self)
            about_dialog.setWindowTitle(f"About {app_name}")
            about_dialog.setTextFormat(Qt.TextFormat.RichText)
            about_dialog.setText(about_text)
            
            # Set application icon if available
            if hasattr(self, 'windowIcon') and not self.windowIcon().isNull():
                about_dialog.setWindowIcon(self.windowIcon())
            
            # Add a button to close the dialog
            about_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Show the dialog
            about_dialog.exec()
            
            logging.info("About dialog shown")
            
        except Exception as e:
            error_msg = f"Error showing about dialog: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)


    def show_sponsor(self):
        """Show sponsor information and ways to support the project."""
        try:
            # Create sponsor dialog
            sponsor_dialog = QDialog(self)
            sponsor_dialog.setWindowTitle("Support the Project")
            sponsor_dialog.setMinimumSize(400, 300)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Add title
            title = QLabel("<h2>Support Our Work</h2>")
            title.setTextFormat(Qt.TextFormat.RichText)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            # Add message
            message = QLabel(
                "<p>If you find this application useful, please consider supporting its development.</p>"
                "<p>Your support helps cover development costs and encourages further improvements.</p>"
            )
            message.setWordWrap(True)
            message.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(message)
            
            # Add ways to support
            support_methods = QGroupBox("Ways to Support")
            methods_layout = QVBoxLayout()
            
            # GitHub Sponsors
            github_btn = QPushButton("Sponsor on GitHub")
            github_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            github_btn.clicked.connect(lambda: self._open_url("https://github.com/sponsors/yourusername"))
            methods_layout.addWidget(github_btn)
            
            # PayPal
            paypal_btn = QPushButton("Donate via PayPal")
            paypal_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
            paypal_btn.clicked.connect(lambda: self._open_url("https://paypal.me/yourusername"))
            methods_layout.addWidget(paypal_btn)
            
            # Patreon
            patreon_btn = QPushButton("Become a Patron")
            patreon_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
            patreon_btn.clicked.connect(lambda: self._open_url("https://patreon.com/yourusername"))
            methods_layout.addWidget(patreon_btn)
            
            # Add stretch to push buttons to the top
            methods_layout.addStretch()
            support_methods.setLayout(methods_layout)
            layout.addWidget(support_methods)
            
            # Add close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(sponsor_dialog.reject)
            layout.addWidget(button_box)
            
            # Set dialog layout
            sponsor_dialog.setLayout(layout)
            
            # Show dialog
            sponsor_dialog.exec()
            
            logging.info("Sponsor dialog shown")
            
        except Exception as e:
            error_msg = f"Error showing sponsor dialog: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _open_url(self, url):
        """Open a URL in the default web browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            logging.info(f"Opened URL: {url}")
        except Exception as e:
            error_msg = f"Failed to open URL: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)


    def check_updates(self):
        """Check for application updates."""
        try:
            # Get current version
            current_version = "1.0.0"  # This should match your version
            
            # Show checking message
            self.statusBar().showMessage("Checking for updates...")
            QApplication.processEvents()
            
            try:
                # In a real application, you would fetch this from your update server or GitHub releases
                # This is a placeholder implementation
                import requests
                import json
                
                # Simulate network request with timeout
                # In a real app, replace this with your actual update check URL
                response = requests.get(
                    "https://api.github.com/repos/yourusername/STL_to_G-Code/releases/latest",
                    timeout=5
                )
                response.raise_for_status()
                
                # Parse the response
                release_info = response.json()
                latest_version = release_info.get('tag_name', '').lstrip('v')
                
                if not latest_version:
                    raise ValueError("Invalid version format in response")
                
                # Compare versions (simple string comparison, might need more sophisticated logic)
                if latest_version > current_version:
                    # New version available
                    reply = QMessageBox.information(
                        self,
                        "Update Available",
                        f"Version {latest_version} is available!\n\n"
                        f"Current version: {current_version}\n\n"
                        f"Would you like to download the update?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        # Open the release page
                        self._open_url(release_info.get('html_url', 
                            "https://github.com/yourusername/STL_to_G-Code/releases/latest"))
                else:
                    QMessageBox.information(
                        self,
                        "No Updates",
                        f"You are using the latest version ({current_version}).",
                        QMessageBox.StandardButton.Ok
                    )
                
            except requests.RequestException as e:
                QMessageBox.warning(
                    self,
                    "Update Check Failed",
                    f"Could not check for updates: {str(e)}\n\n"
                    "Please check your internet connection and try again.",
                    QMessageBox.StandardButton.Ok
                )
                logging.error(f"Update check failed: {str(e)}", exc_info=True)
            
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Update Error",
                    f"An error occurred while checking for updates: {str(e)}",
                    QMessageBox.StandardButton.Ok
                )
                logging.error(f"Error in update check: {str(e)}", exc_info=True)
            
            finally:
                self.statusBar().showMessage("Ready", 3000)
                
        except Exception as e:
            error_msg = f"Error during update check: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)


    def view_gcode(self):
        """Display the generated G-code in a dedicated viewer."""
        try:
            # Check if there's any G-code to view
            if not hasattr(self, 'gcode_editor') or not self.gcode_editor.toPlainText().strip():
                QMessageBox.information(
                    self,
                    "No G-code Available",
                    "No G-code has been generated yet. Please generate G-code first.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # Create a new dialog to view the G-code
            dialog = QDialog(self)
            dialog.setWindowTitle("G-code Viewer")
            dialog.setMinimumSize(800, 600)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Create text editor for G-code
            gcode_viewer = QsciScintilla()
            gcode_viewer.setReadOnly(True)
            
            # Set up lexer for syntax highlighting
            lexer = QsciLexerPython()
            lexer.setDefaultFont(QFont("Consolas", 10))
            gcode_viewer.setLexer(lexer)
            
            # Set up line numbers
            gcode_viewer.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            gcode_viewer.setMarginWidth(0, "00000")
            gcode_viewer.setMarginsForegroundColor(QColor("#999999"))
            
            # Set the G-code content
            gcode_viewer.setText(self.gcode_editor.toPlainText())
            
            # Add search box
            search_box = QLineEdit()
            search_box.setPlaceholderText("Search in G-code...")
            search_box.textChanged.connect(
                lambda text: self._search_in_gcode(gcode_viewer, text)
            )
            
            # Add widgets to layout
            layout.addWidget(QLabel("Search:"))
            layout.addWidget(search_box)
            layout.addWidget(QLabel("G-code:"))
            layout.addWidget(gcode_viewer)
            
            # Add close button
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(dialog.reject)
            
            # Add copy button
            copy_button = QPushButton("Copy to Clipboard")
            copy_button.clicked.connect(
                lambda: self._copy_gcode_to_clipboard(gcode_viewer.text())
            )
            button_box.addButton(copy_button, QDialogButtonBox.ButtonRole.ActionRole)
            
            layout.addWidget(button_box)
            dialog.setLayout(layout)
            
            # Show the dialog
            dialog.exec()
            
            logging.info("G-code viewer opened")
            
        except Exception as e:
            error_msg = f"Error opening G-code viewer: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _search_in_gcode(self, editor, text):
        """Search for text in the G-code editor."""
        if not text:
            # Reset search if text is empty
            editor.setCursorPosition(0, 0)
            return
            
        # Search forward from current position
        editor.findFirst(text, False, False, False, True, True)
    
    def _copy_gcode_to_clipboard(self, text):
        """Copy G-code to the clipboard."""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.statusBar().showMessage("G-code copied to clipboard", 3000)
            logging.info("G-code copied to clipboard")
        except Exception as e:
            error_msg = f"Failed to copy G-code to clipboard: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _update_visualization(self):
        """Update the 3D visualization based on current settings."""
        try:
            # Check if we have the required matplotlib components
            if not hasattr(self, 'ax') or not hasattr(self, 'canvas') or not hasattr(self, 'figure'):
                logging.warning("Matplotlib components not initialized - skipping visualization update")
                return
            
            # Clear previous visualization
            self.ax.clear()
            
            # Check if we have vertices and faces to visualize
            if not hasattr(self, 'current_vertices') or len(self.current_vertices) == 0:
                logging.debug("No vertices to visualize")
                self.canvas.draw()
                return
            
            # Get vertices and faces
            vertices = self.current_vertices
            faces = self.current_faces if hasattr(self, 'current_faces') else []
            
            # Plot the mesh
            if len(faces) > 0:
                # Create a Poly3DCollection from the faces
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                
                # Convert vertices to the format expected by Poly3DCollection
                verts = vertices[faces]
                
                # Create the 3D polygon collection
                mesh = Poly3DCollection(verts, alpha=0.5, linewidths=0.5, edgecolor='k')
                mesh.set_facecolor([0.8, 0.8, 1.0])  # Light blue
                self.ax.add_collection3d(mesh)
                
                # Auto-scale the axes
                min_vals = vertices.min(axis=0)
                max_vals = vertices.max(axis=0)
                center = (min_vals + max_vals) / 2
                max_range = (max_vals - min_vals).max() / 2
                
                self.ax.set_xlim(center[0] - max_range, center[0] + max_range)
                self.ax.set_ylim(center[1] - max_range, center[1] + max_range)
                self.ax.set_zlim(center[2] - max_range, center[2] + max_range)
                
                # Set labels
                self.ax.set_xlabel('X')
                self.ax.set_ylabel('Y')
                self.ax.set_zlabel('Z')
                
                # Set title
                if hasattr(self, 'current_file'):
                    self.ax.set_title(f'STL: {self.current_file}')
                
                # Redraw the canvas
                self.canvas.draw()
                logging.info("STL visualization updated successfully")
                
        except Exception as e:
            error_msg = f"Error in _update_visualization: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Visualization Error", error_msg)


    def _reset_visualization_view(self):
        """Reset the 3D visualization view to default settings."""
        try:
            if not hasattr(self, 'ax') or not hasattr(self, 'canvas') or not hasattr(self, 'figure'):
                logging.warning("Matplotlib components not initialized - cannot reset")
                return
            
            # Reset camera to default position and orientation
            self.ax.clear()
            
            # Reset zoom level to fit the model
            self.ax.set_xlim(-100, 100)
            self.ax.set_ylim(-100, 100)
            self.ax.set_zlim(-100, 100)
            
            # Reset visualization settings to defaults
            if hasattr(self, 'show_wireframe_checkbox'):
                self.show_wireframe_checkbox.setChecked(False)
            if hasattr(self, 'show_normals_checkbox'):
                self.show_normals_checkbox.setChecked(False)
            if hasattr(self, 'show_travel_moves'):
                self.show_travel_moves.setChecked(True)
            
            # Update the visualization with new settings
            self._update_visualization()
            
            self.statusBar().showMessage("View reset to default", 3000)
            logging.info("Visualization view reset to default")
            
        except Exception as e:
            error_msg = f"Error resetting visualization view: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)


def main():
    """Main function to start the application."""
    app = QApplication(sys.argv)
    window = STLToGCodeApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
