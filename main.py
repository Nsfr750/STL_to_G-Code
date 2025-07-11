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
    QStyle, QFrame, QStatusBar, QToolBar, QPlainTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QSettings, QSize, QObject
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import art3d
from stl import mesh
from scripts.version import __version__
from scripts.about import About
from scripts.sponsor import Sponsor
from scripts.help import show_help
from scripts.updates import UpdateChecker  # Import the new UpdateChecker class
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
from scripts.STL_view import STLVisualizer  # Add STLVisualizer import
import numpy as np
from PyQt6.Qsci import QsciScintilla, QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
from scripts.gcode_editor import GCodeEditorWidget
from scripts.gcode_validator import PrinterLimits
from scripts.view_settings import view_settings  # Add this import
from scripts.logger import setup_logging, get_logger
from PyQt6.QtCore import QSettings
try:
    from PyQt6 import sip
except ImportError:
    # Fallback for older PyQt6 versions or PySide6
    try:
        import PySide6.sip as sip
    except ImportError:
        # Fallback to regular sip if available
        try:
            import sip
        except ImportError:
            # If sip is not available, use a dummy implementation
            class SipWrapper:
                @staticmethod
                def isdeleted(obj):
                    return False
            sip = SipWrapper()

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

class SimulationWorker(QObject):
    """Worker for running G-code simulation in a separate thread."""
    
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(bool, str)  # success, message
    error = pyqtSignal(str)  # error message
    
    def __init__(self, gcode):
        super().__init__()
        self.gcode = gcode
        self._is_running = True
        
    def run(self):
        """Run the simulation."""
        try:
            # TODO: Implement actual simulation logic
            # For now, just parse the G-code and emit progress
            lines = [line.strip() for line in self.gcode.split('\n') if line.strip()]
            total_lines = len(lines)
            
            for i, line in enumerate(lines, 1):
                if not self._is_running:
                    break
                    
                # Process line here
                # ...
                
                # Update progress
                progress = int((i / total_lines) * 100) if total_lines > 0 else 100
                self.progress.emit(progress, f"Simulating line {i}/{total_lines}")
                
            self.finished.emit(True, "Simulation completed successfully")
            
        except Exception as e:
            self.error.emit(f"Simulation error: {str(e)}")
            
    def stop(self):
        """Stop the simulation."""
        self._is_running = False

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
        
        # Create main toolbar with improved organization
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        # File Operations Group
        open_action = QAction(
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogOpenButton')),
            "Open STL",
            self
        )
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        # Add separator after file operations
        toolbar.addSeparator()
        
        # Conversion Group
        convert_action = QAction(
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPlay')),
            "Convert to G-code",
            self
        )
        convert_action.setShortcut("F5")
        convert_action.setStatusTip("Convert the loaded STL to G-code")
        convert_action.triggered.connect(self.generate_gcode)
        self.convert_action = convert_action  # Save reference for enabling/disabling
        self.convert_action.setEnabled(False)
        toolbar.addAction(convert_action)
        
        # View Group
        view_gcode_action = QAction(
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_FileDialogDetailedView')),
            "View G-code",
            self
        )
        view_gcode_action.setShortcut("Ctrl+G")
        view_gcode_action.setStatusTip("View and edit the generated G-code")
        view_gcode_action.triggered.connect(self.view_gcode)
        self.view_gcode_action = view_gcode_action  # Save reference for enabling/disabling
        self.view_gcode_action.setEnabled(False)
        toolbar.addAction(view_gcode_action)
        
        # Add separator before simulation controls
        toolbar.addSeparator()
        
        # Simulation Group
        simulate_action = QAction(
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_MediaPlay')),
            "Simulate",
            self
        )
        simulate_action.setShortcut("Ctrl+R")
        simulate_action.setStatusTip("Simulate the G-code")
        simulate_action.triggered.connect(self.simulate_from_editor)
        self.simulate_action = simulate_action  # Save reference for enabling/disabling
        self.simulate_action.setEnabled(False)
        toolbar.addAction(simulate_action)
        
        # Add stretch to push help button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Help Group
        help_action = QAction(
            self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_DialogHelpButton')),
            "Help",
            self
        )
        help_action.setShortcut("F1")
        help_action.setStatusTip("Show help documentation")
        help_action.triggered.connect(self.show_documentation)
        toolbar.addAction(help_action)
        
        # Set up keyboard shortcuts
        self.shortcuts = {
            Qt.Key.Key_F1: self.show_documentation,
            Qt.Key.Key_F5: self.generate_gcode,
            Qt.Key.Key_F12: self.toggle_log_viewer
        }
        
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
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Initialize STL visualizer
        self.stl_visualizer = STLVisualizer(self.ax, self.canvas)
        
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
        """
        Handle a chunk of STL data that has been loaded.
        
        Args:
            chunk_data: Dictionary containing 'vertices', 'faces', and 'progress' keys
        """
        if not chunk_data or 'progress' not in chunk_data:
            return
            
        try:
            # Update the progress bar
            progress = int(chunk_data['progress'])
            self.loading_progress = progress
            
            # Update the mesh data if vertices are provided
            if 'vertices' in chunk_data and 'faces' in chunk_data:
                # Update the STL visualizer with the new mesh data
                if hasattr(self, 'stl_visualizer') and self.stl_visualizer:
                    self.stl_visualizer.update_mesh(
                        chunk_data['vertices'],
                        chunk_data['faces'],
                        self.file_path
                    )
                
                # Also update the local references (for backward compatibility)
                self.current_vertices = chunk_data['vertices']
                self.current_faces = chunk_data['faces']
                
                # Update the visualization
                self._update_visualization()
            
            # Update the progress dialog
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.setValue(progress)
                
                # Update the progress message
                if 'status' in chunk_data:
                    self.progress_dialog.setLabelText(chunk_data['status'])
                
                # Process events to keep the UI responsive
                QApplication.processEvents()
                
        except Exception as e:
            error_msg = f"Error processing chunk: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._handle_loading_error(error_msg)
    
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
                        background-color: #555;
                    }
                    QPushButton:pressed {
                        background-color: #666;
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
            
            from scripts.updates import UpdateChecker
            
            # Store the current status bar message to restore it later
            current_message = self.statusBar().currentMessage()
            
            def on_update_available(update_info):
                try:
                    # Show update dialog
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setWindowTitle("Update Available")
                    msg.setText(f"Version {update_info['version']} is available!")
                    msg.setInformativeText("Would you like to download the latest version?")
                    
                    download_btn = msg.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
                    msg.addButton("Later", QMessageBox.ButtonRole.RejectRole)
                    
                    msg.exec()
                    
                    if msg.clickedButton() == download_btn:
                        import webbrowser
                        webbrowser.open(update_info['url'])
                except Exception as e:
                    logger.error(f"Error showing update dialog: {str(e)}", exc_info=True)
                    QMessageBox.warning(
                        self,
                        "Update Error",
                        "An error occurred while showing update information.",
                        QMessageBox.StandardButton.Ok
                    )
                finally:
                    self.statusBar().showMessage("Update check complete", 3000)
            
            def on_no_update():
                if force_check:  # Only show message if user explicitly checked
                    QMessageBox.information(
                        self,
                        "No Updates",
                        f"You are running the latest version ({__version__}).",
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
            
            # Create and configure the update checker
            self.update_checker = UpdateChecker(current_version=__version__)
            self.update_checker.update_available.connect(on_update_available)
            self.update_checker.no_update_available.connect(on_no_update)
            self.update_checker.error_occurred.connect(on_error)
            
            # Start the update check in a background thread
            self.update_checker.check_for_updates(force=force_check)
            
        except ImportError as e:
            error_msg = f"Failed to import update module: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.statusBar().showMessage("Update check failed: Missing module", 5000)
            if force_check:
                QMessageBox.critical(
                    self,
                    "Update Error",
                    f"Could not check for updates: {error_msg}\n\nPlease make sure all dependencies are installed.",
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
            # Initialize visualizer if it doesn't exist
            if not hasattr(self, 'stl_visualizer') or not self.stl_visualizer:
                if not hasattr(self, 'ax') or not self.ax:
                    logger.error("Cannot update visualization: Matplotlib axes not initialized")
                    return False
                self.stl_visualizer = STLVisualizer(self.ax, self.canvas)
                
            # Update the visualization using the STL visualizer
            success = self.stl_visualizer.render()
            
            if not success:
                error_msg = "Failed to update visualization"
                logger.warning(error_msg)
                self.statusBar().showMessage(error_msg, 5000)
            else:
                self.statusBar().showMessage("Visualization updated", 2000)
                
            return success
                
        except Exception as e:
            error_msg = f"Error updating visualization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.statusBar().showMessage(error_msg, 5000)
            return False
    
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
            self.simulate_action = QAction(QIcon.fromTheme("media-playback-start"), "Simulate", self)
            self.simulate_action.triggered.connect(self.simulate_from_editor)
            self.simulate_action.setStatusTip("Simulate the current G-code")
            self.simulate_action.setEnabled(False)  # Disable by default
            editor_toolbar.addAction(self.simulate_action)
            
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
            
            # Connect textChanged signal to update button state
            self.gcode_editor.textChanged.connect(self._update_simulate_button_state)
            
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
    
    def _update_simulate_button_state(self):
        """Update the simulate button state based on editor content."""
        has_content = bool(self.gcode_editor.toPlainText().strip())
        self.simulate_action.setEnabled(has_content)
    
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
            self._setup_recent_files_menu()
            
            # Save the recent files to settings
            self._save_recent_files()
            
        except Exception as e:
            logger.error(f"Error adding to recent files: {str(e)}", exc_info=True)
    
    def _setup_recent_files_menu(self):
        """Set up the recent files menu."""
        try:
            # Create recent files menu if it doesn't exist
            if not hasattr(self, 'recent_files_menu'):
                if not hasattr(self, 'file_menu'):
                    logger.warning("File menu not found, cannot create recent files menu")
                    return
                self.recent_files_menu = self.file_menu.addMenu("Recent Files")
            
            # Clear existing items
            self.recent_files_menu.clear()
            
            # Get recent files from settings
            settings = QSettings("STLtoGCode", "RecentFiles")
            recent_files = settings.value("recentFiles", [], type=list)
            
            if not recent_files:
                no_files = self.recent_files_menu.addAction("No recent files")
                no_files.setEnabled(False)
                return
                
            # Add recent files to menu
            for i, file_path in enumerate(recent_files[:10]):  # Show max 10 recent files
                if os.path.exists(file_path):
                    action = self.recent_files_menu.addAction(
                        f"&{i+1} {os.path.basename(file_path)}",
                        lambda checked, path=file_path: self._open_recent_file(path)
                    )
                    action.setToolTip(file_path)
            
            # Add a separator and clear action if there are recent files
            self.recent_files_menu.addSeparator()
            clear_action = self.recent_files_menu.addAction("Clear Recent Files")
            clear_action.triggered.connect(self._clear_recent_files)
            
        except Exception as e:
            logger.error(f"Error setting up recent files menu: {str(e)}")
    
    def _open_recent_file(self, file_path):
        """Open a file from the recent files menu."""
        try:
            if os.path.exists(file_path):
                self.open_file(file_path)
            else:
                # Remove non-existent file from recent files
                self._remove_recent_file(file_path)
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"The file was not found:\n{file_path}"
                )
        except Exception as e:
            logger.error(f"Error opening recent file: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open file:\n{file_path}\n\nError: {str(e)}"
            )
    
    def _clear_recent_files(self):
        """Clear the list of recent files."""
        try:
            settings = QSettings("STLtoGCode", "RecentFiles")
            settings.setValue("recentFiles", [])
            self._setup_recent_files_menu()
        except Exception as e:
            logger.error(f"Error clearing recent files: {str(e)}")
    
    def _remove_recent_file(self, file_path):
        """Remove a file from the recent files list."""
        try:
            settings = QSettings("STLtoGCode", "RecentFiles")
            recent_files = settings.value("recentFiles", [], type=list)
            if file_path in recent_files:
                recent_files.remove(file_path)
                settings.setValue("recentFiles", recent_files)
                self._setup_recent_files_menu()
        except Exception as e:
            logger.error(f"Error removing recent file: {str(e)}")
    
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

    def _on_loading_finished(self, success=True, error_msg=None):
        """Handle completion of the STL file loading process.
        
        Args:
            success (bool): Whether the loading was successful
            error_msg (str, optional): Error message if loading failed
        """
        logger.debug(f"Loading finished. Success: {success}, Error: {error_msg}")
        
        # Make local copies of resources we need to clean up
        worker = getattr(self, 'loading_worker', None)
        thread = getattr(self, 'loading_thread', None)
        progress_dialog = getattr(self, 'progress_dialog', None)
        
        # Clear references first to prevent re-entry
        self.loading_worker = None
        self.loading_thread = None
        self.loading_timer.stop()
        
        try:
            # Close the progress dialog if it exists
            if progress_dialog is not None:
                try:
                    progress_dialog.close()
                    progress_dialog.deleteLater()
                except Exception as e:
                    logger.error(f"Error closing progress dialog: {str(e)}")
                finally:
                    if hasattr(self, 'progress_dialog'):
                        self.progress_dialog = None
            
            # Handle error case
            if not success or error_msg:
                logger.error(f"STL loading failed: {error_msg}")
                self._handle_loading_error(error_msg or "Unknown error occurred during STL loading")
                return
                
            # Update UI state
            logger.debug("Updating UI after successful load")
            self._update_ui_after_loading()
            
            # Update status bar
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("STL file loaded successfully", 5000)
                
        except Exception as e:
            logger.error(f"Error in _on_loading_finished: {str(e)}", exc_info=True)
            self._handle_loading_error(f"Error finalizing load: {str(e)}")
        finally:
            # Clean up worker and thread in the correct order
            if worker is not None:
                try:
                    # Disconnect signals safely
                    signals = [
                        ('chunk_loaded', self._on_chunk_loaded),
                        ('loading_finished', self._on_loading_finished),
                        ('error_occurred', self._handle_loading_error),
                        ('progress_updated', self._update_loading_progress)
                    ]
                    
                    for signal, slot in signals:
                        try:
                            getattr(worker, signal).disconnect(slot)
                        except (TypeError, RuntimeError):
                            # Signal was not connected or already disconnected
                            pass
                    
                    # Schedule the worker for deletion
                    worker.deleteLater()
                except Exception as e:
                    if 'wrapped C/C++ object' not in str(e):
                        logger.error(f"Error during worker cleanup: {str(e)}")
            
            # Clean up thread
            if thread is not None:
                try:
                    if thread.isRunning():
                        thread.quit()
                        if not thread.wait(1000):  # Wait up to 1 second
                            logger.warning("Thread didn't stop gracefully, terminating")
                            thread.terminate()
                            thread.wait(500)  # Give it a moment to terminate
                    
                    thread.deleteLater()
                except Exception as e:
                    logger.error(f"Error during thread cleanup: {str(e)}")
            
            # Reset loading state
            self.is_loading = False
            
            # Force UI update
            QApplication.processEvents()
    
    def _cleanup_loading_resources(self):
        """Safely clean up loading resources."""
        try:
            # Clean up worker if it exists
            if hasattr(self, 'loading_worker') and self.loading_worker is not None:
                try:
                    # Check if the worker still exists before trying to disconnect
                    if not sip.isdeleted(self.loading_worker) if hasattr(sip, 'isdeleted') else True:
                        try:
                            # Disconnect signals safely
                            signals = [
                                ('chunk_loaded', self._on_chunk_loaded),
                                ('loading_finished', self._on_loading_finished),
                                ('error_occurred', self._handle_loading_error),
                                ('progress_updated', self._update_loading_progress)
                            ]
                            
                            for signal, slot in signals:
                                try:
                                    getattr(self.loading_worker, signal).disconnect(slot)
                                except (TypeError, RuntimeError):
                                    # Signal was not connected or already disconnected
                                    pass
                            
                            # Schedule the worker for deletion
                            self.loading_worker.deleteLater()
                        except RuntimeError as e:
                            if "wrapped C/C++ object" not in str(e):
                                logger.error(f"Error disconnecting worker signals: {str(e)}")
                except Exception as e:
                    logger.error(f"Error during worker cleanup: {str(e)}")
                finally:
                    self.loading_worker = None
            
            # Clean up thread
            if hasattr(self, 'loading_thread') and self.loading_thread is not None:
                try:
                    if self.loading_thread.isRunning():
                        self.loading_thread.quit()
                        if not self.loading_thread.wait(1000):  # Wait up to 1 second
                            logger.warning("Thread didn't stop gracefully, terminating")
                            self.loading_thread.terminate()
                            self.loading_thread.wait(500)  # Give it a moment to terminate
                    
                    self.loading_thread.deleteLater()
                except Exception as e:
                    logger.error(f"Error during thread cleanup: {str(e)}")
                finally:
                    self.loading_thread = None
            
            # Clean up progress dialog if it exists
            if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
                try:
                    self.progress_dialog.close()
                    self.progress_dialog.deleteLater()
                except Exception as e:
                    logger.error(f"Error during progress dialog cleanup: {str(e)}")
                finally:
                    self.progress_dialog = None
                    
        except Exception as e:
            logger.error(f"Unexpected error during resource cleanup: {str(e)}", exc_info=True)
    
    def _update_loading_progress(self, progress_value, status_message):
        """Update the loading progress dialog with current progress.
        
        Args:
            progress_value (int): Current progress value (0-100)
            status_message (str or int): Status message to display
        """
        try:
            # Ensure we're in the main thread and the application is still running
            if not QApplication.instance() or not hasattr(self, 'progress_dialog'):
                return
                
            # Get a local reference to the dialog to prevent race conditions
            progress_dialog = self.progress_dialog
            if progress_dialog is None:
                return
                
            # Ensure status_message is a string
            status_str = str(status_message) if status_message is not None else ""
            
            # Update progress dialog if it still exists
            try:
                # Check if the dialog was deleted
                if sip and hasattr(sip, 'isdeleted') and sip.isdeleted(progress_dialog):
                    return
                    
                # Update the dialog
                progress_dialog.setValue(progress_value)
                progress_dialog.setLabelText(status_str)
                
                # Process events to keep the UI responsive
                QApplication.processEvents()
                
            except RuntimeError as e:
                # Dialog was likely deleted
                if 'wrapped C/C++ object' in str(e):
                    self.progress_dialog = None
                return
                
            # Update status bar if available
            try:
                status_bar = self.statusBar()
                if status_bar:
                    status_bar.showMessage(status_str, 3000)  # Show for 3 seconds
            except RuntimeError:
                pass  # Status bar might be destroyed
                
        except Exception as e:
            # Use logger if available, otherwise fall back to stderr
            try:
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating loading progress: {str(e)}", exc_info=True)
            except:
                import traceback
                print(f"Error updating loading progress: {str(e)}\n{traceback.format_exc()}")
                
        finally:
            # Ensure we don't hold references to deleted objects
            if 'progress_dialog' in locals():
                del progress_dialog
                
    def _update_ui_after_loading(self):
        """Update the UI after an STL file has been successfully loaded."""
        # Enable/disable toolbar actions based on loaded state
        if hasattr(self, 'convert_action'):
            self.convert_action.setEnabled(True)
        if hasattr(self, 'view_gcode_action'):
            self.view_gcode_action.setEnabled(False)  # Disable until G-code is generated
            
        # Update window title with the current file
        if self.current_file:
            self.setWindowTitle(f"STL to GCode Converter v{__version__} - {os.path.basename(self.current_file)}")
        
        # Update the status bar
        self.statusBar().showMessage(f"Loaded {os.path.basename(self.current_file)}", 3000)
        
        # Update the recent files list in the menu
        self._update_recent_files_menu()
        
    def _update_file_list(self):
        """Update the recent files list in the UI."""
        # This method is kept for backward compatibility
        # The actual implementation is in _update_recent_files_menu
        self._update_recent_files_menu()
        
    def _update_recent_files_menu(self):
        """Update the recent files list in the File menu."""
        try:
            # Clear the recent files menu
            if hasattr(self, 'recent_files_menu'):
                self.recent_files_menu.clear()
            else:
                # Create the recent files menu if it doesn't exist
                self.recent_files_menu = self.file_menu.addMenu("Recent Files")
            
            # Add recent files to the menu
            if hasattr(self, 'recent_files') and self.recent_files:
                for i, file_path in enumerate(self.recent_files[:10]):  # Show max 10 recent files
                    if os.path.exists(file_path):
                        action = QAction(f"{i+1}. {os.path.basename(file_path)}", self)
                        action.setData(file_path)
                        action.triggered.connect(lambda checked, path=file_path: self._open_recent_file(path))
                        self.recent_files_menu.addAction(action)
                
                # Add a separator and clear action if there are recent files
                self.recent_files_menu.addSeparator()
                clear_action = QAction("Clear Recent Files", self)
                clear_action.triggered.connect(self._clear_recent_files)
                self.recent_files_menu.addAction(clear_action)
            else:
                # Add a disabled action if no recent files
                no_files = QAction("No recent files", self)
                no_files.setEnabled(False)
                self.recent_files_menu.addAction(no_files)
                
        except Exception as e:
            logger.error(f"Error updating recent files menu: {str(e)}", exc_info=True)
    
def main():
    """Main entry point for the application."""
    # Set up logging first
    try:
        log_file = setup_logging()
        logger = get_logger(__name__)
        logger.info("=" * 80)
        logger.info(f"Starting STL to GCode Converter v{__version__}")
        logger.info(f"Log file: {log_file}")
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
