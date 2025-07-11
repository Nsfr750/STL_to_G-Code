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
    QProgressDialog, QLineEdit, QDialog, QDialogButtonBox, QGroupBox, 
    QStyle, QFrame, QStatusBar, QToolBar, QPlainTextEdit
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
from scripts.view_settings import view_settings  # Add this import
from scripts.logger import setup_logging, get_logger
from PyQt6.QtCore import QSettings

# Get logger for this module
logger = get_logger(__name__)

# Check for OpenGL availability at module level
OPENGL_AVAILABLE = False
OPENGL_ERROR = "OpenGL not available"

try:
    from PyQt6.QtOpenGL import QOpenGLWidget, QOpenGLContext
    from OpenGL import GL
    OPENGL_AVAILABLE = True
except ImportError as e:
    OPENGL_ERROR = str(e)
    logger.warning(f"OpenGL not available: {OPENGL_ERROR}")

# Import view settings after OPENGL_AVAILABLE is set
from scripts.view_settings import view_settings

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
        
        # Initialize OpenGL setting
        self.use_opengl = view_settings.use_opengl and OPENGL_AVAILABLE
        if not OPENGL_AVAILABLE:
            logger.warning(f"OpenGL visualization disabled: {OPENGL_ERROR}")
            if view_settings.use_opengl:
                # If OpenGL was enabled in settings but not available, update settings
                view_settings.toggle_opengl()
        
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logger.info(f"Application icon set from: {icon_path}")
            else:
                logger.warning(f"Icon file not found at: {icon_path}")
        except Exception as e:
            logger.error(f"Error setting application icon: {str(e)}")
        
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
        logger.info("Application started")
        
        # Add this to the __init__ method where other UI elements are created
        self.opengl_visualizer = None
        
        # Log OpenGL status
        if not OPENGL_AVAILABLE:
            logger.info(f"OpenGL visualization not available: {OPENGL_ERROR}")
        
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
        
        # Load recent files
        self._load_recent_files()
        
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
        self.file_menu = menubar.addMenu("&File")
        
        open_stl_action = QAction("&Open STL...", self)
        open_stl_action.setShortcut("Ctrl+O")
        open_stl_action.triggered.connect(self.open_file)
        self.file_menu.addAction(open_stl_action)
        
        # Add Open G-code action
        open_gcode_action = QAction("Open &G-code File...", self)
        open_gcode_action.setShortcut("Ctrl+G")
        open_gcode_action.setStatusTip("Open a G-code file")
        open_gcode_action.triggered.connect(self.open_gcode_in_editor)
        self.file_menu.addAction(open_gcode_action)
        
        # Save GCode action
        self.save_gcode_action = QAction("&Save GCode As...", self)
        self.save_gcode_action.setShortcut("Ctrl+Shift+S")
        self.save_gcode_action.setStatusTip("Save the generated GCode to a file")
        self.save_gcode_action.triggered.connect(self.save_gcode)
        self.save_gcode_action.setEnabled(False)  # Will be enabled when GCode is generated
        self.file_menu.addAction(self.save_gcode_action)
        
        self.file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
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
        
        # Add OpenGL toggle action if OpenGL is available
        if OPENGL_AVAILABLE:
            self.opengl_action = QAction("Use OpenGL Rendering", self)
            self.opengl_action.setCheckable(True)
            self.opengl_action.setChecked(self.use_opengl)
            self.opengl_action.triggered.connect(self.toggle_opengl)
            view_menu.addAction(self.opengl_action)
        else:
            # Add a disabled menu item to inform the user why OpenGL is not available
            opengl_info = QAction("OpenGL Not Available", self)
            opengl_info.setStatusTip(f"OpenGL is not available: {OPENGL_ERROR}")
            opengl_info.setEnabled(False)
            view_menu.addAction(opengl_info)
        
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
        self.open_action = open_stl_action
    
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
                logger.debug("Starting progressive loading")
                self._start_progressive_loading()
                
            except Exception as e:
                error_msg = f"Failed to initialize STL processor: {str(e)}"
                logger.error(error_msg, exc_info=True)
                show_file_open_error(self, error_msg)
                return
            
        except Exception as e:
            error_msg = f"Error in open_file: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
                logger.warning(f"Error resetting visualization: {str(e)}")
    
    def _start_progressive_loading(self):
        """Start the progressive loading process in a background thread."""
        logger.debug("Starting progressive loading process...")
        
        if not self.current_stl_processor:
            error_msg = "No STL processor available"
            logger.error(error_msg)
            self._handle_loading_error(error_msg, "Loading Error")
            return
        
        try:
            logger.debug("Creating progress dialog...")
            # Setup progress dialog
            self.progress_dialog = QProgressDialog("Loading STL file...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.canceled.connect(self._cancel_loading)
            
            # Get total number of triangles for progress tracking
            total_triangles = self.current_stl_processor._header.num_triangles
            if total_triangles <= 0:
                error_msg = f"Invalid number of triangles in STL file: {total_triangles}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Starting progressive loading of {total_triangles} triangles")
            
            # Initialize loading state
            self.is_loading = True
            self.loaded_triangles = 0
            self.total_triangles = total_triangles
            
            # Create and configure worker thread
            logger.debug("Creating worker thread...")
            self.loading_thread = QThread()
            self.loading_worker = STLLoadingWorker(
                stl_processor=self.current_stl_processor,
                chunk_size=1000  # Process 1000 triangles at a time
            )
            
            # Move worker to thread
            logger.debug("Moving worker to thread...")
            self.loading_worker.moveToThread(self.loading_thread)
            
            # Connect signals
            logger.debug("Connecting signals...")
            self.loading_worker.chunk_loaded.connect(self._on_chunk_loaded)
            self.loading_worker.loading_finished.connect(self._on_loading_finished)
            self.loading_worker.error_occurred.connect(self._handle_loading_error)
            self.loading_worker.progress_updated.connect(self._update_loading_progress)
            
            # Clean up thread when done
            self.loading_worker.loading_finished.connect(self.loading_thread.quit)
            self.loading_worker.loading_finished.connect(self.loading_worker.deleteLater)
            self.loading_thread.finished.connect(self.loading_thread.deleteLater)
            
            # Start the thread
            logger.debug("Starting worker thread...")
            self.loading_thread.start()
            
            # Start the loading process using a single-shot timer
            logger.debug("Starting loading process...")
            QTimer.singleShot(0, self.loading_worker.start_loading)
            
            # Start the processing timer
            logger.debug("Starting processing timer...")
            self.loading_timer.start(100)  # Process queue every 100ms
            
            logger.info("Progressive loading started successfully")
            
        except Exception as e:
            error_msg = f"Error starting progressive loading: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
                    logger.error(error_msg, exc_info=True)
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
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            QApplication.processEvents()
    
    def _process_chunk(self, chunk_data):
        """Process a single chunk of STL data."""
        if not chunk_data or 'vertices' not in chunk_data:
            logger.warning("Received empty or invalid chunk data")
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
                logger.warning("Received chunk with no vertices")
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
            
            logger.debug(f"Processed chunk. Total vertices: {len(self.current_vertices)}, "
                       f"Total faces: {len(self.current_faces)}")
            
        except Exception as e:
            logger.error(f"Error in _process_chunk: {str(e)}", exc_info=True)
            raise
    
    def _on_chunk_loaded(self, chunk_data):
        """Handle a chunk of STL data that has been loaded.
        
        Args:
            chunk_data: Dictionary containing 'vertices', 'faces', and 'progress' keys
        """
        try:
            if not self.is_loading:
                logger.warning("Received chunk but loading is not in progress")
                return
                
            logger.debug(f"Received chunk with {len(chunk_data.get('vertices', []))} vertices")
            
            # Add the chunk to the processing queue
            if not hasattr(self, 'loading_queue'):
                self.loading_queue = []
                
            self.loading_queue.append(chunk_data)
            
            # If this is the first chunk, start the processing timer
            if not hasattr(self, 'loading_timer') or not self.loading_timer.isActive():
                logger.debug("Starting loading timer")
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
            logger.error(error_msg, exc_info=True)
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
            logger.error(f"Error processing G-code buffer: {str(e)}", exc_info=True)
    
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
                logger.info("Application settings updated")
                
                # Apply any settings that need immediate effect
                self._apply_settings()
                
        except ImportError as e:
            error_msg = "Settings dialog not available"
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"{error_msg}. Please check the installation.")
        except Exception as e:
            error_msg = f"Error showing settings: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
                
            logger.debug("Applied application settings")
            
        except Exception as e:
            logger.error(f"Error applying settings: {str(e)}", exc_info=True)
    
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
                
            logger.info(f"Applied theme: {theme_name}")
            
        except Exception as e:
            logger.error(f"Error applying theme '{theme_name}': {str(e)}", exc_info=True)
    
    def toggle_log_viewer(self):
        """Toggle the visibility of the log viewer."""
        try:
            if not hasattr(self, 'log_viewer') or not self.log_viewer:
                # Create and show the log viewer if it doesn't exist
                from scripts.log_viewer import LogViewer
                self.log_viewer = LogViewer()
                self.log_viewer.show()
                self.toggle_log_viewer_action.setText("Hide Log Viewer")
                logger.info("Log viewer opened")
            else:
                # Toggle visibility if it exists
                if self.log_viewer.isVisible():
                    self.log_viewer.hide()
                    self.toggle_log_viewer_action.setText("Show Log Viewer")
                    logger.debug("Log viewer hidden")
                else:
                    self.log_viewer.show()
                    self.toggle_log_viewer_action.setText("Hide Log Viewer")
                    logger.debug("Log viewer shown")
                    
        except ImportError as e:
            error_msg = "Log viewer module not available"
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"{error_msg}. Please check the installation.")
        except Exception as e:
            error_msg = f"Error toggling log viewer: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)

    def show_documentation(self):
        """Open the application's documentation in the markdown viewer."""
        try:
            from scripts.markdown_viewer import show_documentation as show_markdown_docs
            show_markdown_docs(self)  # Pass self as parent
            logger.info("Opened documentation in markdown viewer")
        except Exception as e:
            error_msg = f"Failed to open documentation: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
            
            logger.info("Started G-code generation")
            
        except Exception as e:
            error_msg = f"Error starting G-code generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
            logger.error(f"Error processing G-code chunk: {str(e)}", exc_info=True)
    
    def _update_preview(self, preview_data):
        """Update the 3D preview with the generated G-code."""
        try:
            # This would be implemented to update the 3D preview
            # with the generated G-code paths
            logger.debug(f"Received preview data with {len(preview_data.get('paths', []))} paths")
            
        except Exception as e:
            logger.error(f"Error updating preview: {str(e)}", exc_info=True)
    
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
            logger.info("G-code generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error finalizing G-code generation: {str(e)}", exc_info=True)
    
    def _on_gcode_generation_error(self, error_msg):
        """Handle errors during G-code generation."""
        try:
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
                
            QMessageBox.critical(self, "G-code Generation Error", error_msg)
            self.statusBar().showMessage("G-code generation failed", 5000)
            logger.error(f"G-code generation error: {error_msg}")
            
        except Exception as e:
            logger.error(f"Error handling G-code generation error: {str(e)}", exc_info=True)
    
    def _cancel_gcode_generation(self):
        """Cancel the ongoing G-code generation."""
        try:
            if hasattr(self, 'gcode_worker') and self.gcode_worker:
                self.gcode_worker.cancel()
                
            if hasattr(self, 'gcode_thread') and self.gcode_thread.isRunning():
                self.gcode_thread.quit()
                self.gcode_thread.wait()
                
            self.statusBar().showMessage("G-code generation cancelled", 5000)
            logger.info("G-code generation cancelled by user")
            
        except Exception as e:
            logger.error(f"Error cancelling G-code generation: {str(e)}", exc_info=True)

    def show_about(self):
        """Show the About dialog using the About class from scripts.about."""
        try:
            About.show_about(self)  # This will use the static method from the About class
        except Exception as e:
            logger.error(f"Error showing about dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show about dialog: {str(e)}")
    
    def show_sponsor(self):
        """Show the sponsor dialog using the Sponsor class from scripts.sponsor."""
        try:
            sponsor_dialog = Sponsor(self)
            sponsor_dialog.show_sponsor()
        except Exception as e:
            logger.error(f"Error showing sponsor dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show sponsor dialog: {str(e)}")
    
    def _open_url(self, url):
        """Open a URL in the default web browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
        except Exception as e:
            error_msg = f"Failed to open URL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)

    def check_updates(self, force_check: bool = False):
        """Check for application updates.
        
        Args:
            force_check: If True, force a check even if recently checked.
        """
        try:
            self.statusBar().showMessage("Checking for updates...")
            QApplication.processEvents()  # Update the UI
            
            from scripts.updates import check_for_updates
            
            # Store the current status bar message to restore it later
            current_message = self.statusBar().currentMessage()
            
            def on_update_available(update_info):
                # Update will be shown by the check_for_updates function
                self.statusBar().showMessage("Update check complete", 3000)
                
            def on_no_update():
                if force_check:  # Only show message if user explicitly checked
                    QMessageBox.information(
                        self,
                        "No Updates",
                        "You are running the latest version.",
                        QMessageBox.StandardButton.Ok
                    )
                self.statusBar().showMessage("You are running the latest version", 3000)
                
            def on_error(error_msg):
                logger.error(f"Update check failed: {error_msg}")
                self.statusBar().showMessage("Update check failed", 3000)
                if force_check:  # Only show error if user explicitly checked
                    QMessageBox.warning(
                        self,
                        "Update Check Failed",
                        f"Could not check for updates: {error_msg}",
                        QMessageBox.StandardButton.Ok
                    )
            
            # Start the update check
            update_available, update_info = check_for_updates(
                parent=self,
                current_version=__version__,
                force_check=force_check,
                silent_if_no_update=not force_check
            )
            
            # The check_for_updates function will show UI dialogs as needed
            # We don't need to do anything with the return values here
            
        except ImportError as e:
            error_msg = f"Failed to import update module: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.statusBar().showMessage("Update check failed: Missing module", 5000)
            if force_check:
                QMessageBox.critical(
                    self,
                    "Update Error",
                    f"Could not check for updates: {error_msg}",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            error_msg = f"Unexpected error during update check: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.statusBar().showMessage("Update check failed", 5000)
            if force_check:
                QMessageBox.critical(
                    self,
                    "Update Error",
                    "An unexpected error occurred while checking for updates.",
                    QMessageBox.StandardButton.Ok
                )

    def open_gcode_in_editor(self):
        """
        Open a G-code file and display it in the editor.
        """
        try:
            # Get the file path from the file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open G-code File",
                "",
                "G-code Files (*.gcode *.nc *.tap);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled the dialog
                
            logger.info(f"Opening G-code file: {file_path}")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                gcode_content = f.read()
            
            # Update the G-code editor
            self.gcode_editor.setPlainText(gcode_content)
            
            # Switch to the G-code tab
            self.tab_widget.setCurrentIndex(1)  # Assuming G-code tab is at index 1
            
            # Update status bar
            self.statusBar().showMessage(f"Loaded G-code from {os.path.basename(file_path)}", 5000)
            
            # Store the current file path
            self.current_file = file_path
            
        except Exception as e:
            error_msg = f"Error opening G-code file: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def view_gcode(self):
        """
        Switch to the G-code editor tab and ensure it's up to date.
        """
        try:
            # Check if we have a tab widget
            if not hasattr(self, 'tab_widget') or not self.tab_widget:
                logger.warning("Tab widget not initialized")
                return
                
            # Switch to the G-code Editor tab (index 1)
            self.tab_widget.setCurrentIndex(1)
            
            # Set focus to the G-code editor if it exists
            if hasattr(self, 'gcode_editor'):
                self.gcode_editor.setFocus()
                
                # If there's G-code content, ensure it's visible
                if hasattr(self, 'gcode') and self.gcode:
                    cursor = self.gcode_editor.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.Start)
                    self.gcode_editor.setTextCursor(cursor)
                    
            # Update status bar with a temporary message
            self.statusBar().showMessage("Viewing G-code Editor", 3000)
            
        except Exception as e:
            error_msg = f"Error viewing G-code: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def simulate_from_editor(self):
        """
        Start G-code simulation using the content from the editor.
        """
        try:
            # Check if we have a G-code editor
            if not hasattr(self, 'gcode_editor') or not self.gcode_editor:
                logger.warning("G-code editor not available for simulation")
                QMessageBox.warning(
                    self,
                    "Simulation Error",
                    "G-code editor is not available.",
                    QMessageBox.StandardButton.Ok
                )
                return
                
            # Get G-code from the editor
            gcode = self.gcode_editor.toPlainText().strip()
            if not gcode:
                QMessageBox.warning(
                    self,
                    "Simulation Error",
                    "No G-code to simulate. Please load or generate G-code first.",
                    QMessageBox.StandardButton.Ok
                )
                return
                
            # Update status
            self.statusBar().showMessage("Starting G-code simulation...")
            
            # Switch to the visualization tab
            if hasattr(self, 'tab_widget') and self.tab_widget:
                self.tab_widget.setCurrentIndex(2)  # Assuming index 2 is the visualization tab
                
            # TODO: Add actual simulation logic here
            # For now, just show a message
            QMessageBox.information(
                self,
                "Simulation Started",
                "G-code simulation started. This is a placeholder for actual simulation.",
                QMessageBox.StandardButton.Ok
            )
            
            # Update status
            self.statusBar().showMessage("G-code simulation ready", 3000)
            
        except Exception as e:
            error_msg = f"Error during G-code simulation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(
                self,
                "Simulation Error",
                f"An error occurred during simulation:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def _update_visualization(self, state=None):
        """
        Update the 3D visualization based on current settings.
        
        Args:
            state: The state of the checkbox that triggered the update (if any)
        """
        try:
            # Clear the current plot
            self.ax.clear()
            
            # Set up the 3D axes
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')
            
            # Get the current visualization settings
            show_travel = self.show_travel_moves.isChecked() if hasattr(self, 'show_travel_moves') else True
            
            # TODO: Add actual G-code visualization logic here
            # For now, just show an empty plot with axes
            
            # Set equal aspect ratio for all axes
            self.ax.set_box_aspect([1, 1, 1])
            
            # Redraw the canvas
            self.canvas.draw()
            
            # Update status bar
            self.statusBar().showMessage("Visualization updated", 2000)
            
        except Exception as e:
            error_msg = f"Error updating visualization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.statusBar().showMessage(error_msg, 5000)
    
    def _reset_visualization_view(self):
        """Reset the 3D visualization view to default."""
        try:
            if hasattr(self, 'ax') and self.ax:
                # Reset the view to default
                self.ax.set_xlim(0, self.printer_limits['x_max'])
                self.ax.set_ylim(0, self.printer_limits['y_max'])
                self.ax.set_zlim(0, self.printer_limits['z_max'])
                
                # Redraw the canvas
                self.canvas.draw()
                
                # Update status bar
                self.statusBar().showMessage("View reset", 2000)
                
        except Exception as e:
            error_msg = f"Error resetting view: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.statusBar().showMessage(error_msg, 5000)
    
    def _setup_editor_tab(self):
        """Set up the G-code editor tab."""
        try:
            # Create a new tab for the G-code editor
            self.editor_tab = QWidget()
            self.tab_widget.addTab(self.editor_tab, "G-code Editor")
            
            # Create layout for the editor tab
            layout = QVBoxLayout(self.editor_tab)
            
            # Create toolbar for editor actions
            editor_toolbar = QToolBar("Editor Tools")
            
            # Add action to open G-code file
            open_action = QAction(QIcon.fromTheme("document-open"), "Open G-code", self)
            open_action.triggered.connect(self.open_gcode_in_editor)
            open_action.setStatusTip("Open a G-code file in the editor")
            editor_toolbar.addAction(open_action)
            
            # Add action to save G-code
            save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
            save_action.triggered.connect(lambda: self.save_gcode())
            save_action.setShortcut("Ctrl+S")
            save_action.setStatusTip("Save the current G-code")
            editor_toolbar.addAction(save_action)
            
            # Add separator
            editor_toolbar.addSeparator()
            
            # Add action to simulate G-code
            simulate_action = QAction(QIcon.fromTheme("media-playback-start"), "Simulate", self)
            simulate_action.triggered.connect(self.simulate_from_editor)
            simulate_action.setStatusTip("Simulate the current G-code")
            editor_toolbar.addAction(simulate_action)
            
            # Add the toolbar to the layout
            layout.addWidget(editor_toolbar)
            
            # Create the G-code text editor
            self.gcode_editor = QPlainTextEdit()
            self.gcode_editor.setStyleSheet("""
                QPlainTextEdit {
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                    background-color: #2b2b2b;
                    color: #f8f8f2;
                    selection-background-color: #49483e;
                }
                QScrollBar:vertical {
                    border: none;
                    background: #2b2b2b;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #3e3d32;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)
            
            # Set up line numbers
            self.gcode_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            
            # Add the editor to the layout
            layout.addWidget(self.gcode_editor)
            
            # Status bar for editor information
            self.editor_status = QStatusBar()
            self.editor_status.setSizeGripEnabled(False)
            layout.addWidget(self.editor_status)
            
            # Update status when cursor position changes
            self.gcode_editor.cursorPositionChanged.connect(self._update_editor_status)
            
            logger.info("G-code editor tab initialized")
            
        except Exception as e:
            error_msg = f"Error setting up editor tab: {str(e)}"
            logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _update_editor_status(self):
        """Update the editor status bar with cursor position and document info."""
        try:
            cursor = self.gcode_editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            char_count = len(self.gcode_editor.toPlainText())
            line_count = self.gcode_editor.document().blockCount()
            
            self.editor_status.showMessage(
                f"Line: {line}, Col: {col} | "
                f"Length: {char_count} chars | "
                f"Lines: {line_count}"
            )
        except Exception as e:
            logger.error(f"Error updating editor status: {str(e)}", exc_info=True)
    
    def add_to_recent_files(self, file_path):
        """
        Add a file to the list of recently opened files.
        
        Args:
            file_path: Path to the file to add to recent files
        """
        try:
            # Initialize recent files list if it doesn't exist
            if not hasattr(self, 'recent_files'):
                self.recent_files = []
            
            # Remove the file if it already exists in the list
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            
            # Add the file to the beginning of the list
            self.recent_files.insert(0, file_path)
            
            # Keep only the most recent 10 files
            max_recent = 10
            self.recent_files = self.recent_files[:max_recent]
            
            # Update the recent files menu
            self._update_recent_files_menu()
            
            # Save the recent files to settings
            self._save_recent_files()
            
        except Exception as e:
            logger.error(f"Error adding to recent files: {str(e)}", exc_info=True)
    
    def _update_recent_files_menu(self):
        """Update the recent files menu with the current list of files."""
        try:
            if not hasattr(self, 'recent_files_menu'):
                # Find the recent files menu in the file menu
                for action in self.file_menu.actions():
                    if action.text() == 'Recent Files' and hasattr(action, 'menu'):
                        self.recent_files_menu = action.menu()
                        self.recent_files_menu.aboutToShow.connect(self._update_recent_files_menu)
                        break
                else:
                    logger.warning("Recent files menu not found")
                    return
            
            # Clear the current actions
            self.recent_files_menu.clear()
            
            if not hasattr(self, 'recent_files') or not self.recent_files:
                no_files = self.recent_files_menu.addAction("No recent files")
                no_files.setEnabled(False)
                return
            
            # Add each recent file as an action
            for i, file_path in enumerate(self.recent_files[:10]):  # Show max 10 recent files
                display_text = f"&{i + 1} {os.path.basename(file_path)}"
                action = self.recent_files_menu.addAction(display_text, 
                                                         lambda checked, path=file_path: self.open_file(path))
                action.setStatusTip(file_path)
            
            # Add a separator and clear action
            self.recent_files_menu.addSeparator()
            clear_action = self.recent_files_menu.addAction("Clear Recent Files", self._clear_recent_files)
            clear_action.setStatusTip("Clear the list of recent files")
            
        except Exception as e:
            logger.error(f"Error updating recent files menu: {str(e)}", exc_info=True)
    
    def _save_recent_files(self):
        """Save the recent files list to application settings."""
        try:
            if hasattr(self, 'recent_files'):
                settings = QSettings("STLtoGCode", "RecentFiles")
                settings.setValue("recentFiles", self.recent_files)
        except Exception as e:
            logger.error(f"Error saving recent files: {str(e)}", exc_info=True)
    
    def _load_recent_files(self):
        """Load the recent files list from application settings."""
        try:
            settings = QSettings("STLtoGCode", "RecentFiles")
            self.recent_files = settings.value("recentFiles", [])
            if not isinstance(self.recent_files, list):
                self.recent_files = []
            
            # Filter out files that no longer exist
            self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
            
            # Save the filtered list back
            if len(self.recent_files) != settings.value("recentFiles", [], type=list):
                self._save_recent_files()
                
        except Exception as e:
            logger.error(f"Error loading recent files: {str(e)}", exc_info=True)
            self.recent_files = []
    
    def _clear_recent_files(self):
        """Clear the list of recent files."""
        try:
            if hasattr(self, 'recent_files'):
                self.recent_files = []
                self._save_recent_files()
                self._update_recent_files_menu()
        except Exception as e:
            logger.error(f"Error clearing recent files: {str(e)}", exc_info=True)
    
    def _cancel_loading(self):
        """Cancel the current loading operation."""
        if hasattr(self, 'loading_worker') and self.loading_worker:
            self.loading_worker.cancel()
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        self.is_loading = False
        self.loading_queue = []
        self.loading_timer.stop()
        
    def _handle_loading_error(self, error_msg, title="Loading Error"):
        """Display an error message for loading failures."""
        logger.error(f"{title}: {error_msg}")
        QMessageBox.critical(self, title, str(error_msg))
        self._cancel_loading()

def main():
    """Main entry point for the application."""
    # Set up logging first
    try:
        log_file = setup_logging()
        logger.info("=" * 80)
        logger.info(f"Starting STL to GCode Converter v{__version__}")
        logger.info(f"Log file: {log_file.absolute()}")
        logger.info("=" * 80)
    except Exception as e:
        print(f"Failed to set up logging: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = STLToGCodeApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
