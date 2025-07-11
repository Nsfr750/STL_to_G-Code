"""
Main application class for the STL to GCode Converter using PyQt6.
"""
import sys
import os
import logging
from pathlib import Path
import datetime
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QTabWidget, 
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, 
    QProgressBar, QCheckBox, QDoubleSpinBox, QSplitter,
    QProgressDialog, QLineEdit, QDialog, QDialogButtonBox, QGroupBox, QStyle, QFrame, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer
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
from scripts.workers import GCodeGenerationWorker, STLLoadingWorker
from scripts.gcode_visualizer import GCodeVisualizer
from scripts.stl_processor import MemoryEfficientSTLProcessor, STLHeader, STLTriangle
from scripts.gcode_simulator import GCodeSimulator, PrinterState
from scripts.STL_load import open_stl_file, show_file_open_error  # Add this import
from scripts.gcode_load import open_gcode_file, show_file_open_error
from scripts.gcode_save import save_gcode_file, show_file_save_error
import numpy as np
from PyQt6.Qsci import QsciScintilla, QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
from scripts.gcode_editor import GCodeEditorWidget
from scripts.gcode_validator import PrinterLimits

# Try to import OpenGL components with better error handling
OPENGL_AVAILABLE = False
OPENGL_ERROR = ""
try:
    # Try importing from QtOpenGLWidgets first (PyQt6 >= 6.2.0)
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtOpenGL import QOpenGLContext, QOpenGLVersionProfile
    from scripts.opengl_visualizer import OpenGLGCodeVisualizer
    OPENGL_AVAILABLE = True
except (ImportError, AttributeError) as e1:
    try:
        # Fall back to QtOpenGL for older versions
        from PyQt6.QtOpenGL import QOpenGLWidget, QOpenGLContext, QOpenGLVersionProfile
        from scripts.opengl_visualizer import OpenGLGCodeVisualizer
        OPENGL_AVAILABLE = True
    except (ImportError, AttributeError) as e2:
        OPENGL_ERROR = str(e2)
        if not OPENGL_ERROR:
            OPENGL_ERROR = "OpenGL components not found"
        logging.info(f"Using matplotlib 3D renderer: {OPENGL_ERROR}")

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
        
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logging.info(f"Application icon set from: {icon_path}")
            else:
                logging.warning(f"Icon file not found at: {icon_path}")
        except Exception as e:
            logging.error(f"Error setting application icon: {str(e)}")
        
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
        
        # Set window properties
        self.setWindowTitle(f"STL to GCode Converter v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Log application start
        logging.info("Application started")
        
        # Add this to the __init__ method where other UI elements are created
        self.use_opengl = OPENGL_AVAILABLE  # Whether to use OpenGL for visualization
        self.opengl_visualizer = None
        
        # Log OpenGL status
        if not OPENGL_AVAILABLE:
            logging.info(f"OpenGL visualization not available: {OPENGL_ERROR}")
        
        # Add progressive loading attributes
        self.progressive_loading = True  # Enable progressive loading
        self.loading_progress = 0
        self.current_vertices = np.zeros((0, 3), dtype=np.float32)
        self.current_faces = np.zeros((0, 3), dtype=np.uint32)
        self.loading_queue = []
        self.is_loading = False
        self.loading_timer = QTimer(self)
        self.loading_timer.setSingleShot(False)  # Make it a repeating timer
        self.loading_timer.setInterval(100)  # 100ms interval for processing queue
        self.loading_timer.timeout.connect(self._process_loading_queue)
        
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
        
        # Initialize STL processor
        self.current_stl_processor = None
        
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
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create main toolbar
        toolbar, toolbar_layout = self.ui.create_toolbar(central_widget)
        
        # Add file operations to toolbar
        self.open_button = self.ui.create_button(
            toolbar, 
            "Open STL",
            self.open_file,
            "Open an STL file (Ctrl+O)",
            'primary',
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogOpenButton'))
        )
        toolbar_layout.addWidget(self.open_button)
        
        # Add convert button
        self.convert_button = self.ui.create_button(
            toolbar,
            "Convert to G-code",
            self.generate_gcode,
            "Convert the loaded STL to G-code",
            'success',
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPlay'))
        )
        self.convert_button.setEnabled(False)
        toolbar_layout.addWidget(self.convert_button)
        
        # Add view buttons
        self.view_gcode_button = self.ui.create_button(
            toolbar,
            "View G-code",
            self.view_gcode,
            "View and edit the generated G-code",
            'default',
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_FileDialogDetailedView'))
        )
        self.view_gcode_button.setEnabled(False)
        toolbar_layout.addWidget(self.view_gcode_button)
        
        # Add separator
        toolbar_layout.addWidget(self._create_separator())
        
        # Add simulation controls
        self.simulate_button = self.ui.create_button(
            toolbar,
            "Simulate",
            self.simulate_from_editor,
            "Simulate the G-code (Ctrl+R)",
            'default',
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPlay'))
        )
        self.simulate_button.setEnabled(False)
        toolbar_layout.addWidget(self.simulate_button)
        
        # Add stretch to push help button to the right
        toolbar_layout.addStretch()
        
        # Add help button
        help_button = self.ui.create_button(
            toolbar,
            "Help",
            self.show_documentation,
            "Show help documentation",
            'default',
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogHelpButton'))
        )
        toolbar_layout.addWidget(help_button)
        
        main_layout.addWidget(toolbar)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        
        # Left panel for controls
        left_panel, left_layout = self.ui.create_frame(content_widget, "vertical")
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # File list with label
        left_layout.addWidget(QLabel("<b>Loaded Files</b>"))
        self.file_list = self.ui.create_file_list(left_panel)
        left_layout.addWidget(self.file_list)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Infill optimization
        infill_layout = QVBoxLayout()
        infill_layout.addWidget(QLabel("<b>Infill Settings</b>"))
        
        self.optimize_infill_checkbox = self.ui.create_checkbox(
            settings_group,
            "Optimize Infill Paths",
            tooltip="Enable A* path planning for optimized infill patterns"
        )
        self.optimize_infill_checkbox.setChecked(True)
        infill_layout.addWidget(self.optimize_infill_checkbox)
        
        # Infill resolution
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Resolution (mm):"))
        self.infill_resolution_spin = self.ui.create_double_spinbox(
            settings_group,
            minimum=0.1,
            maximum=5.0,
            value=1.0,
            step=0.1,
            decimals=1,
            tooltip="Grid resolution for infill path optimization (smaller = more precise but slower)"
        )
        res_layout.addWidget(self.infill_resolution_spin)
        infill_layout.addLayout(res_layout)
        
        settings_layout.addLayout(infill_layout)
        left_layout.addWidget(settings_group)
        
        # Add stretch to push content to top
        left_layout.addStretch()
        
        # Add left panel to content
        content_layout.addWidget(left_panel, stretch=1)
        
        # Right panel for main content
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # Better look on some platforms
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        
        # Add tabs
        self.stl_view_tab = QWidget()
        self.gcode_view_tab = QWidget()
        self.visualization_tab = QWidget()
        
        # Add tabs with proper names
        self.tab_widget.addTab(self.stl_view_tab, "3D View")
        self.tab_widget.addTab(self.gcode_view_tab, "G-code Editor")
        self.tab_widget.addTab(self.visualization_tab, "G-code Visualization")
        
        # Set up each tab's content
        self._setup_stl_view()
        self._setup_gcode_view()
        self._setup_visualization_view()
        
        # Add tab widget to right layout
        right_layout.addWidget(self.tab_widget)
        
        # Add right panel to content
        content_layout.addWidget(right_panel, stretch=4)
        
        # Add content to main layout
        main_layout.addWidget(content_widget, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar for long operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set up the editor tab
        self._setup_editor_tab()
        
        # Set initial tab
        self.tab_widget.setCurrentIndex(0)  # Show 3D View by default
    
    def _create_separator(self):
        """Create a vertical separator for toolbars."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #555;")
        line.setFixedWidth(1)
        return line
    
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
        
        # Create matplotlib Figure and Canvas for 3D visualization
        self.figure = Figure(figsize=(5, 4), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Set up the 3D axes
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Add navigation toolbar with custom styling
        self.toolbar = NavigationToolbar(self.canvas, self.visualization_tab)
        self._style_matplotlib_toolbar()
        
        # Add widgets to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Initialize with empty plot
        self._update_visualization()
    
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
        
        open_action = QAction("&Open STL File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an STL file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Add Open G-code action
        open_gcode_action = QAction("Open &G-code File...", self)
        open_gcode_action.setShortcut("Ctrl+G")
        open_gcode_action.setStatusTip("Open a G-code file")
        open_gcode_action.triggered.connect(self.open_gcode_in_editor)
        file_menu.addAction(open_gcode_action)
        
        # Save GCode action
        self.save_gcode_action = QAction("&Save GCode As...", self)
        self.save_gcode_action.setShortcut("Ctrl+Shift+S")
        self.save_gcode_action.setStatusTip("Save the generated GCode to a file")
        self.save_gcode_action.triggered.connect(self.save_gcode)
        self.save_gcode_action.setEnabled(False)  # Will be enabled when GCode is generated
        file_menu.addAction(self.save_gcode_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.show_settings)
        settings_action.setShortcut("Ctrl+,")
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Toggle Log Viewer action
        self.toggle_log_viewer_action = QAction("Show &Log", self)
        self.toggle_log_viewer_action.setCheckable(True)
        self.toggle_log_viewer_action.setChecked(False)
        self.toggle_log_viewer_action.setStatusTip("Show or hide the log viewer")
        self.toggle_log_viewer_action.triggered.connect(self.toggle_log_viewer)
        view_menu.addAction(self.toggle_log_viewer_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show the application's About box")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Help action
        help_action = QAction("&Help", self)
        help_action.setShortcut("F1")
        help_action.setStatusTip("Show help documentation")
        help_action.triggered.connect(lambda: show_help(self))
        help_menu.addAction(help_action)
        
        # Documentation action
        docs_action = QAction("&Documentation", self)
        docs_action.setStatusTip("Open the application documentation")
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        # Sponsor action
        sponsor_action = QAction("&Sponsor", self)
        sponsor_action.setStatusTip("Support the project")
        sponsor_action.triggered.connect(self.show_sponsor)
        help_menu.addAction(sponsor_action)
        
        help_menu.addSeparator()
               
        # Check for updates action
        update_action = QAction("Check for &Updates...", self)
        update_action.setStatusTip("Check for application updates")
        update_action.triggered.connect(self.check_updates)
        help_menu.addAction(update_action)
        
        # Store actions for later reference
        self.open_action = open_action
    
    def open_file(self, file_path=None):
        """Open an STL file and load it into the viewer with progressive loading."""
        # Reset any existing loading state
        self._reset_loading_state()
        
        try:
            # Use the new STL loading function
            file_path, file_name, success, error_msg = open_stl_file(self, file_path)
            
            if not success:
                if error_msg:
                    show_file_open_error(self, error_msg)
                return
                
            # Store file info
            self.file_path = file_path
            self.current_file = file_name
            self.setWindowTitle(f"STL to GCode - {self.current_file}")
            
            # Add to recent files
            self.add_to_recent_files(self.file_path)
            
            # Initialize STL processor
            try:
                from scripts.stl_processor import MemoryEfficientSTLProcessor
                self.current_stl_processor = MemoryEfficientSTLProcessor(file_path)
                self.current_stl_processor.open()
                
                # Start progressive loading
                logging.debug("Starting progressive loading")
                self._start_progressive_loading()
                
            except Exception as e:
                error_msg = f"Failed to initialize STL processor: {str(e)}"
                logging.error(error_msg, exc_info=True)
                show_file_open_error(self, error_msg)
                return
            
        except Exception as e:
            error_msg = f"Error in open_file: {str(e)}"
            logging.error(error_msg, exc_info=True)
            show_file_open_error(self, error_msg)
    
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
        logging.debug("Starting progressive loading process...")
        
        if not self.current_stl_processor:
            error_msg = "No STL processor available"
            logging.error(error_msg)
            self._handle_loading_error(error_msg, "Loading Error")
            return
        
        try:
            logging.debug("Creating progress dialog...")
            # Setup progress dialog
            self.progress_dialog = QProgressDialog("Loading STL file...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.canceled.connect(self._cancel_loading)
            
            # Get total number of triangles for progress tracking
            total_triangles = self.current_stl_processor._header.num_triangles
            if total_triangles <= 0:
                error_msg = f"Invalid number of triangles in STL file: {total_triangles}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            logging.info(f"Starting progressive loading of {total_triangles} triangles")
            
            # Initialize loading state
            self.is_loading = True
            self.loaded_triangles = 0
            self.total_triangles = total_triangles
            
            # Create and configure worker thread
            logging.debug("Creating worker thread...")
            self.loading_thread = QThread()
            self.loading_worker = STLLoadingWorker(
                stl_processor=self.current_stl_processor,
                chunk_size=1000  # Process 1000 triangles at a time
            )
            
            # Move worker to thread
            logging.debug("Moving worker to thread...")
            self.loading_worker.moveToThread(self.loading_thread)
            
            # Connect signals
            logging.debug("Connecting signals...")
            self.loading_worker.chunk_loaded.connect(self._on_chunk_loaded)
            self.loading_worker.loading_finished.connect(self._on_loading_finished)
            self.loading_worker.error_occurred.connect(self._handle_loading_error)
            self.loading_worker.progress_updated.connect(self._update_loading_progress)
            
            # Clean up thread when done
            self.loading_worker.loading_finished.connect(self.loading_thread.quit)
            self.loading_worker.loading_finished.connect(self.loading_worker.deleteLater)
            self.loading_thread.finished.connect(self.loading_thread.deleteLater)
            
            # Start the thread
            logging.debug("Starting worker thread...")
            self.loading_thread.start()
            
            # Start the loading process using a single-shot timer
            logging.debug("Starting loading process...")
            QTimer.singleShot(0, self.loading_worker.start_loading)
            
            # Start the processing timer
            logging.debug("Starting processing timer...")
            self.loading_timer.start(100)  # Process queue every 100ms
            
            logging.info("Progressive loading started successfully")
            
        except Exception as e:
            error_msg = f"Error starting progressive loading: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self._handle_loading_error(error_msg, "Error starting loading process")
    
    def _process_loading_queue(self):
        """Process chunks from the loading queue."""
        try:
            if not hasattr(self, 'loading_queue') or not self.loading_queue:
                return
            
            # Process up to 5 chunks per timer tick to keep UI responsive
            chunks_processed = 0
            max_chunks_per_tick = 5
            
            while self.loading_queue and chunks_processed < max_chunks_per_tick:
                chunk_data = self.loading_queue.pop(0)
                chunks_processed += 1
                
                try:
                    # Process the chunk
                    self._process_chunk(chunk_data)
                    
                    # Update progress
                    progress = chunk_data.get('progress', 0)
                    self.statusBar().showMessage(f"Loading STL: {progress}%")
                    
                    # Update visualization periodically or on last chunk
                    if progress % 10 == 0 or progress >= 100 or not self.loading_queue:
                        self._update_visualization()
                        QApplication.processEvents()
                    
                except Exception as e:
                    error_msg = f"Error processing chunk: {str(e)}"
                    logging.error(error_msg, exc_info=True)
                    QMessageBox.critical(self, "Processing Error", error_msg)
                    continue
            
            # If there are more chunks to process, schedule the next batch
            if self.loading_queue:
                QTimer.singleShot(10, self._process_loading_queue)
            else:
                # Final update when done
                self._update_visualization()
                self.statusBar().showMessage("STL loading completed", 3000)
                
        except Exception as e:
            error_msg = f"Error in _process_loading_queue: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            QApplication.processEvents()
    
    def _process_chunk(self, chunk_data):
        """Process a single chunk of STL data."""
        if not chunk_data or 'vertices' not in chunk_data:
            logging.warning("Received empty or invalid chunk data")
            return
            
        try:
            # Update progress
            if 'progress' in chunk_data:
                self.loading_progress = chunk_data['progress']
                if hasattr(self, 'progress_dialog') and self.progress_dialog:
                    self.progress_dialog.setValue(self.loading_progress)
            
            # Get vertices and faces from chunk
            new_vertices = np.array(chunk_data['vertices'], dtype=np.float32)
            new_faces = np.array(chunk_data.get('faces', []), dtype=np.uint32)
            
            if len(new_vertices) == 0:
                logging.warning("Received chunk with no vertices")
                return
            
            # Initialize arrays if they don't exist
            if not hasattr(self, 'current_vertices') or self.current_vertices is None:
                self.current_vertices = np.zeros((0, 3), dtype=np.float32)
            if not hasattr(self, 'current_faces') or self.current_faces is None:
                self.current_faces = np.zeros((0, 3), dtype=np.uint32)
            
            # Calculate the offset for face indices
            vertex_offset = len(self.current_vertices)
            
            # Add the new vertices
            self.current_vertices = np.vstack((self.current_vertices, new_vertices))
            
            # If we have faces, add them with the correct offset
            if len(new_faces) > 0:
                new_faces_offset = new_faces + vertex_offset
                self.current_faces = np.vstack((self.current_faces, new_faces_offset))
            
            logging.debug(f"Processed chunk. Total vertices: {len(self.current_vertices)}, "
                       f"Total faces: {len(self.current_faces)}")
            
        except Exception as e:
            logging.error(f"Error in _process_chunk: {str(e)}", exc_info=True)
            raise
    
    def _on_chunk_loaded(self, chunk_data):
        """Handle a chunk of STL data that has been loaded.
        
        Args:
            chunk_data: Dictionary containing 'vertices', 'faces', and 'progress' keys
        """
        try:
            if not self.is_loading:
                logging.warning("Received chunk but loading is not in progress")
                return
                
            logging.debug(f"Received chunk with {len(chunk_data.get('vertices', []))} vertices")
            
            # Add the chunk to the processing queue
            if not hasattr(self, 'loading_queue'):
                self.loading_queue = []
                
            self.loading_queue.append(chunk_data)
            
            # If this is the first chunk, start the processing timer
            if not hasattr(self, 'loading_timer') or not self.loading_timer.isActive():
                logging.debug("Starting loading timer")
                self.loading_timer = QTimer()
                self.loading_timer.timeout.connect(self._process_loading_queue)
                self.loading_timer.start(50)  # Process queue every 50ms for smoother updates
            
            # Update progress
            if 'progress' in chunk_data:
                progress = int(chunk_data['progress'])
                if hasattr(self, 'progress_dialog'):
                    self.progress_dialog.setValue(progress)
                    
                    # Close the progress dialog when loading is complete
                    if progress >= 100:
                        self.progress_dialog.close()
                        self.is_loading = False
                        self._on_loading_finished()
                
                # Update status bar
                self.statusBar().showMessage(f"Loading STL: {progress}%")
                
                # Force UI update
                QApplication.processEvents()
            
        except Exception as e:
            error_msg = f"Error in _on_chunk_loaded: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self._handle_loading_error(error_msg, "Error processing STL data")
    
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
    
    def save_gcode(self, file_path=None):
        """
        Save the current G-code to a file.
        
        Args:
            file_path (str, optional): Path to save the file. If None, a save dialog will be shown.
        """
        if not hasattr(self, 'editor_widget') or not self.editor_widget:
            QMessageBox.warning(self, "Error", "No G-code editor is available.")
            return
        
        content = self.editor_widget.text()
        
        # If file_path is provided, use it as the default filename
        default_filename = file_path if file_path else self.gcode_file_path
        
        # Use the gcode_save module to handle file saving
        result = save_gcode_file(
            parent=self,
            content=content,
            default_filename=default_filename
        )
        
        if result['success']:
            # Update the current file path and window title
            self.gcode_file_path = result['file_path']
            self.setWindowTitle(f"STL to GCode - {result['file_name']}")
            
            # Add to recent files
            self.add_to_recent_files(self.gcode_file_path)
            
            # Update status bar
            self.statusBar().showMessage(f"G-code saved to {result['file_name']}", 3000)
        else:
            # Show error message if save failed
            show_file_save_error(self, result)
        
        return result['success']
    
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
                        border: 1px solid #555;
                        border-radius: 3px;
                        padding: 5px;
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

    def show_documentation(self):
        """Open the application's documentation in the markdown viewer."""
        try:
            from scripts.markdown_viewer import show_documentation as show_markdown_docs
            show_markdown_docs(self)  # Pass self as parent
            logging.info("Opened documentation in markdown viewer")
        except Exception as e:
            error_msg = f"Failed to open documentation: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(
                self, 
                "Documentation Error",
                f"Could not open documentation. Please check the 'docs' directory.\n\nError: {str(e)}"
            )

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

    def show_about(self):
        """Show the About dialog using the About class from scripts.about."""
        try:
            About.show_about(self)  # This will use the static method from the About class
        except Exception as e:
            logging.error(f"Error showing about dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show about dialog: {str(e)}")
    
    def show_sponsor(self):
        """Show the sponsor dialog using the Sponsor class from scripts.sponsor."""
        try:
            sponsor_dialog = Sponsor(self)
            sponsor_dialog.show_sponsor()
        except Exception as e:
            logging.error(f"Error showing sponsor dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show sponsor dialog: {str(e)}")
    
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

    def check_updates(self, force_check: bool = False):
        """Check for application updates using the updates module.
        
        Args:
            force_check: If True, skip the cache and force a check.
        """
        try:
            # Show checking message
            self.statusBar().showMessage("Checking for updates...")
            QApplication.processEvents()
            
            # Import the update function
            from scripts.updates import check_for_updates
            
            # Check for updates
            update_available, update_info = check_for_updates(
                parent=self,
                current_version=__version__,
                force_check=force_check,
                silent_if_no_update=not force_check
            )
            
            # Show appropriate message if no update is available and this was a forced check
            if force_check and not update_available:
                QMessageBox.information(
                    self,
                    "No Updates",
                    f"You are using the latest version ({__version__}).",
                    QMessageBox.StandardButton.Ok
                )
                
            # Update status bar
            self.statusBar().showMessage("Ready", 3000)
            
        except ImportError as e:
            error_msg = "Failed to import updates module. Update check disabled."
            logging.error(f"{error_msg} Error: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
            
        except Exception as e:
            error_msg = f"Error during update check: {str(e)}"
            logging.error(error_msg, exc_info=True)
            
            # Only show error if this was a forced check
            if force_check:
                QMessageBox.critical(
                    self,
                    "Update Error",
                    f"An error occurred while checking for updates:\n{str(e)}",
                    QMessageBox.StandardButton.Ok
                )
            
            self.statusBar().showMessage("Update check failed", 3000)

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
        """Update the 3D visualization with the current STL data."""
        try:
            # Check if we have vertices to visualize
            if not hasattr(self, 'current_vertices') or len(self.current_vertices) == 0:
                logging.warning("No vertices to visualize")
                return

            # Ensure we have a valid figure and canvas
            if not hasattr(self, 'figure') or not hasattr(self, 'ax'):
                try:
                    # Create a new figure with 3D projection if OpenGL is available
                    self.figure = Figure(figsize=(8, 6), dpi=100)
                    try:
                        self.ax = self.figure.add_subplot(111, projection='3d')
                    except Exception as e:
                        logging.warning(f"3D projection not available, falling back to 2D: {str(e)}")
                        self.ax = self.figure.add_subplot(111)
                    
                    # Create the canvas and toolbar
                    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
                    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
                    
                    # Create a new widget for the visualization
                    self.visualization_widget = QWidget()
                    layout = QVBoxLayout(self.visualization_widget)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Create the canvas and toolbar
                    self.canvas = FigureCanvas(self.figure)
                    self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    
                    # Add widgets to layout
                    self.toolbar = NavigationToolbar(self.canvas, self.visualization_widget)
                    layout.addWidget(self.toolbar)
                    layout.addWidget(self.canvas)
                    
                    # Set the visualization widget in the tab
                    if hasattr(self, 'stl_view_tab'):
                        # Clear existing layout if it exists
                        if self.stl_view_tab.layout():
                            QWidget().setLayout(self.stl_view_tab.layout())
                        self.stl_view_tab.setLayout(layout)
                    
                    # Connect mouse events for better interaction
                    self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
                    self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
                    self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
                    
                except Exception as e:
                    error_msg = f"Failed to initialize visualization: {str(e)}"
                    logging.error(error_msg, exc_info=True)
                    self.statusBar().showMessage("Failed to initialize visualization", 5000)
                    return

            # Clear the current plot
            self.ax.clear()
            
            try:
                # Plot the mesh if we have faces, otherwise plot points
                if hasattr(self, 'current_faces') and len(self.current_faces) > 0:
                    try:
                        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                        
                        # Create a Poly3DCollection from the vertices and faces
                        verts = self.current_vertices[self.current_faces]
                        mesh = Poly3DCollection(
                            verts,
                            alpha=0.8,
                            linewidths=0.5,
                            edgecolor='#555555'
                        )
                        mesh.set_facecolor([0.8, 0.8, 1.0])  # Light blue
                        self.ax.add_collection3d(mesh)
                        
                        # Auto-scale the plot
                        if len(self.current_vertices) > 0:
                            self.ax.set_xlim([self.current_vertices[:, 0].min(), self.current_vertices[:, 0].max()])
                            self.ax.set_ylim([self.current_vertices[:, 1].min(), self.current_vertices[:, 1].max()])
                            self.ax.set_zlim([self.current_vertices[:, 2].min(), self.current_vertices[:, 2].max()])
                            
                    except Exception as e:
                        logging.warning(f"Failed to create 3D mesh, falling back to point cloud: {str(e)}")
                        # Fall back to point cloud if mesh creation fails
                        self.ax.scatter(
                            self.current_vertices[:, 0],
                            self.current_vertices[:, 1],
                            self.current_vertices[:, 2],
                            c='b', marker='.', alpha=0.5, s=1
                        )
                else:
                    # Just plot the vertices as points
                    self.ax.scatter(
                        self.current_vertices[:, 0],
                        self.current_vertices[:, 1],
                        self.current_vertices[:, 2],
                        c='b', marker='.', alpha=0.5, s=1
                    )
                
                # Set labels and title
                self.ax.set_xlabel('X (mm)')
                self.ax.set_ylabel('Y (mm)')
                if hasattr(self.ax, 'set_zlabel'):  # Only for 3D plots
                    self.ax.set_zlabel('Z (mm)')
                self.ax.set_title('STL Model')
                
                # Use draw_idle instead of draw for better performance
                self.canvas.draw_idle()
                
            except Exception as e:
                error_msg = f"Error during visualization update: {str(e)}"
                logging.error(error_msg, exc_info=True)
                self.statusBar().showMessage("Error updating visualization", 5000)
                
        except Exception as e:
            error_msg = f"Unexpected error in visualization: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.statusBar().showMessage("Unexpected error in visualization", 5000)
    
    def on_mouse_press(self, event):
        """Handle mouse press events for the visualization."""
        if hasattr(self, 'canvas') and hasattr(self, 'toolbar'):
            self.toolbar.press_pan(event) if event.button == 1 else self.toolbar.press_zoom(event)
    
    def on_mouse_release(self, event):
        """Handle mouse release events for the visualization."""
        if hasattr(self, 'canvas') and hasattr(self, 'toolbar'):
            self.toolbar.release_pan(event) if event.button == 1 else self.toolbar.release_zoom(event)
    
    def on_mouse_move(self, event):
        """Handle mouse move events for the visualization."""
        if hasattr(self, 'canvas') and hasattr(self, 'toolbar'):
            self.toolbar.mouse_move(event)
    
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

    def _reset_loading_state(self):
        """Reset the loading state and clean up any existing resources."""
        self.is_loading = False
        self.loaded_triangles = 0
        self.total_triangles = 0
        
        # Clean up any existing loading thread
        if hasattr(self, 'loading_thread') and self.loading_thread is not None:
            if self.loading_thread.isRunning():
                self.loading_thread.quit()
                self.loading_thread.wait()
            self.loading_thread = None
            
        # Clean up any existing STL processor
        if hasattr(self, 'current_stl_processor') and self.current_stl_processor is not None:
            self.current_stl_processor.close()
            self.current_stl_processor = None
            
        # Reset the 3D view
        if hasattr(self, 'view'):
            self.view.clear()

    def _start_progressive_loading(self):
        """Start the progressive loading of the STL file in a background thread."""
        logging.debug("Starting progressive loading process...")
        
        if not hasattr(self, 'current_stl_processor') or self.current_stl_processor is None:
            logging.error("No STL processor available")
            return
            
        try:
            logging.debug("Creating progress dialog...")
            # Initialize progress dialog
            self.progress_dialog = QProgressDialog("Loading STL file...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.canceled.connect(self._cancel_loading)
            
            # Get total number of triangles for progress tracking
            total_triangles = self.current_stl_processor._header.num_triangles
            if total_triangles <= 0:
                error_msg = f"Invalid number of triangles in STL file: {total_triangles}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            logging.info(f"Starting progressive loading of {total_triangles} triangles")
            
            # Initialize loading state
            self.is_loading = True
            self.loaded_triangles = 0
            self.total_triangles = total_triangles
            
            # Create and configure worker thread
            logging.debug("Creating worker thread...")
            self.loading_thread = QThread()
            self.loading_worker = STLLoadingWorker(
                stl_processor=self.current_stl_processor,
                chunk_size=1000  # Process 1000 triangles at a time
            )
            
            # Move worker to thread
            logging.debug("Moving worker to thread...")
            self.loading_worker.moveToThread(self.loading_thread)
            
            # Connect signals
            logging.debug("Connecting signals...")
            self.loading_worker.chunk_loaded.connect(self._on_chunk_loaded)
            self.loading_worker.loading_finished.connect(self._on_loading_finished)
            self.loading_worker.error_occurred.connect(self._handle_loading_error)
            self.loading_worker.progress_updated.connect(self._update_loading_progress)
            
            # Clean up thread when done
            self.loading_worker.loading_finished.connect(self.loading_thread.quit)
            self.loading_worker.loading_finished.connect(self.loading_worker.deleteLater)
            self.loading_thread.finished.connect(self.loading_thread.deleteLater)
            
            # Start the thread
            logging.debug("Starting worker thread...")
            self.loading_thread.start()
            
            # Start the loading process using a single-shot timer
            logging.debug("Starting loading process...")
            QTimer.singleShot(0, self.loading_worker.start_loading)
            
            # Start the processing timer
            logging.debug("Starting processing timer...")
            self.loading_timer.start(100)  # Process queue every 100ms
            self.is_loading = True
            
            logging.info("Started progressive loading thread")
            
        except Exception as e:
            logging.error(f"Error starting progressive loading: {str(e)}", exc_info=True)
            self._handle_loading_error(e, "Error starting loading process")

    @pyqtSlot(dict)
    def _on_chunk_loaded(self, chunk_data):
        """Handle a chunk of STL data that has been loaded."""
        try:
            # Update the 3D view with the new chunk
            if hasattr(self, 'view'):
                self.view.add_mesh(
                    vertices=chunk_data['vertices'],
                    faces=chunk_data['faces'],
                    color=(0.8, 0.8, 0.8, 0.5)
                )
                
            # Update progress
            progress = int(chunk_data['progress'])
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.setValue(progress)
                
            # Process events to keep the UI responsive
            QApplication.processEvents()
            
        except Exception as e:
            logging.error(f"Error processing chunk: {str(e)}", exc_info=True)

    @pyqtSlot()
    def _on_loading_finished(self):
        """Handle completion of STL loading."""
        try:
            logging.info("STL loading completed successfully")
            self.is_loading = False
            
            # Close progress dialog if it exists
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
                self.progress_dialog = None
                
            # Update status bar
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("STL file loaded successfully", 5000)
                
            # Fit the view to the model
            if hasattr(self, 'view'):
                self.view.fit_view()
                
        except Exception as e:
            logging.error(f"Error finalizing STL loading: {str(e)}", exc_info=True)

    @pyqtSlot(str)
    def _handle_loading_error(self, error_msg, context=""):
        """Handle errors during STL loading."""
        try:
            logging.error(f"STL loading error: {error_msg}")
            self.is_loading = False
            
            # Close progress dialog if it exists
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
                self.progress_dialog = None
                
            # Show error message
            full_msg = f"Error loading STL file"
            if context:
                full_msg += f" ({context}): {error_msg}"
            else:
                full_msg += f": {error_msg}"
                
            QMessageBox.critical(self, "Loading Error", full_msg)
            
            # Update status bar
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("Error loading STL file", 5000)
                
        except Exception as e:
            logging.error(f"Error handling loading error: {str(e)}", exc_info=True)

    @pyqtSlot(int, int)
    def _update_loading_progress(self, current, total):
        """Update the loading progress."""
        try:
            self.loaded_triangles = current
            self.total_triangles = total
            
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(
                    f"Loading STL: {current:,} / {total:,} triangles "
                    f"({current/max(1, total)*100:.1f}%)"
                )
                
        except Exception as e:
            logging.error(f"Error updating progress: {str(e)}", exc_info=True)

    def _cancel_loading(self):
        """Cancel the current loading operation."""
        try:
            logging.info("Cancelling STL loading...")
            
            if hasattr(self, 'loading_worker'):
                self.loading_worker.cancel()
                
            self._reset_loading_state()
            
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("Loading cancelled", 3000)
                
        except Exception as e:
            logging.error(f"Error cancelling loading: {str(e)}", exc_info=True)
            self._handle_loading_error(e, "Error cancelling loading")

    def add_to_recent_files(self, file_path):
        """
        Add a file to the list of recently opened files.
        
        Args:
            file_path: Path to the file to add to recent files
        """
        try:
            # Get current recent files list or create a new one
            recent_files = self.settings.get('recent_files', [])
            
            # Convert to Path objects for consistent comparison
            file_path = Path(file_path).resolve()
            
            # Remove the file if it already exists in the list
            recent_files = [str(f) for f in recent_files]
            if str(file_path) in recent_files:
                recent_files.remove(str(file_path))
                
            # Add the file to the beginning of the list
            recent_files.insert(0, str(file_path))
            
            # Limit the number of recent files (e.g., keep last 10)
            max_recent = 10
            recent_files = recent_files[:max_recent]
            
            # Save the updated list to settings
            self.settings['recent_files'] = recent_files
            
            # Update the recent files menu if it exists
            if hasattr(self, 'recent_files_menu'):
                self._update_recent_files_menu()
                
            logging.debug(f"Added to recent files: {file_path}")
            
        except Exception as e:
            logging.error(f"Error adding to recent files: {str(e)}", exc_info=True)
    
    def _update_recent_files_menu(self):
        """Update the recent files menu with the current list of files."""
        if not hasattr(self, 'recent_files_menu'):
            return
            
        # Clear existing actions
        self.recent_files_menu.clear()
        
        # Get recent files from settings
        recent_files = self.settings.get('recent_files', [])
        
        if not recent_files:
            action = self.recent_files_menu.addAction("No recent files")
            action.setEnabled(False)
            return
            
        # Add each recent file as a menu item
        for i, file_path in enumerate(recent_files, 1):
            # Show a shortened path if it's too long
            display_path = str(file_path)
            if len(display_path) > 50:
                display_path = f"...{display_path[-47:]}"
                
            # Create the action with a keyboard shortcut (Ctrl+1, Ctrl+2, etc.)
            shortcut = f"Ctrl+{i}" if i <= 9 else ""
            action = self.recent_files_menu.addAction(
                f"&{i} {display_path}",
                lambda checked, path=file_path: self.open_file(path)
            )
            
            if i <= 9:
                action.setShortcut(f"Ctrl+{i}")
                
        # Add a separator and clear action
        self.recent_files_menu.addSeparator()
        self.recent_files_menu.addAction("Clear Recent Files", self._clear_recent_files)
    
    def _clear_recent_files(self):
        """Clear the list of recently opened files."""
        try:
            self.settings['recent_files'] = []
            if hasattr(self, 'recent_files_menu'):
                self._update_recent_files_menu()
            logging.debug("Cleared recent files list")
        except Exception as e:
            logging.error(f"Error clearing recent files: {str(e)}", exc_info=True)

    def _setup_editor_tab(self):
        """Set up the G-code editor tab."""
        if not hasattr(self, 'editor_widget'):
            self.editor_widget = GCodeEditorWidget()
            self.editor_widget.set_printer_limits(self.printer_limits)
            
            # Connect signals
            self.editor_widget.editor.textChanged.connect(self._on_editor_text_changed)
            
            # Add to tab widget
            self.gcode_view_tab.layout().addWidget(self.editor_widget)
    
    def _on_editor_text_changed(self):
        """Handle text changes in the editor."""
        # Enable/disable save button based on modifications
        if hasattr(self, 'save_gcode_action'):
            self.save_gcode_action.setEnabled(True)
    
    def open_gcode_in_editor(self):
        """Open a G-code file in the editor using the gcode_load module."""
        try:
            # Use the gcode_load module to handle file opening
            gcode_content, result = open_gcode_file(parent=self)
            
            if not result['success']:
                if result.get('error_details'):
                    show_gcode_open_error(self, result['error_details'])
                return
                
            # Set the editor content
            self.editor_widget.set_text(gcode_content) 
            self.current_file = result['file_path']
            
            # Update window title and status bar
            self.setWindowTitle(f"STL to GCode Converter v{__version__} - {result['file_name']}")
            self.statusBar().showMessage(f"Loaded {result['file_name']}", 3000)
            
            # Add to recent files
            self.add_to_recent_files(self.current_file)
            
        except Exception as e:
            error_msg = f"Failed to open file: {str(e)}"
            logging.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
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
        
        # Switch to visualization tab
        self.tab_widget.setCurrentWidget(self.visualization_tab)
        
        # Run simulation
        self._start_simulation(gcode)

def main():
    """Main function to start the application."""
    # Set up logging configuration
    log_file = Path(__file__).parent / 'stl_to_gcode.log'
    
    # Ensure the log file exists and is writable
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.touch()
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")
        log_file = None
    
    # Configure logging
    log_handlers = [logging.StreamHandler()]  # Always log to console
    if log_file and os.access(log_file, os.W_OK):
        file_handler = logging.FileHandler(log_file, mode='a')  # Append to log file
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        log_handlers.append(file_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=log_handlers
    )
    
    # Log application start
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"Starting STL to GCode Converter v{__version__}")
    logger.info(f"Log file: {log_file.absolute() if log_file else 'Console only'}")
    logger.info("=" * 80)
    
    # Initialize and run the application
    try:
        app = QApplication(sys.argv)
        window = STLToGCodeApp()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
