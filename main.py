"""
Main application class for the STL to GCode Converter using PyQt6.
"""
import sys
import os
import time  # Added for time-based progress tracking
import logging
from scripts.logger import get_logger
from pathlib import Path
import datetime
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QTabWidget, 
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, 
    QProgressBar, QCheckBox, QDoubleSpinBox, QSplitter,
    QProgressDialog, QLineEdit, QDialog, QDialogButtonBox, QGroupBox, 
    QStyle, QFrame, QStatusBar, QToolBar, QPlainTextEdit, QSizePolicy, QTextEdit
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
from scripts.stl_processor import MemoryEfficientSTLProcessor, STLHeader, STLTriangle
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
from scripts.progress import ProgressReporter  # Add import at the top of the file with other imports
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

class STLToGCodeApp(QMainWindow):
    """
    Main application window for the STL to GCode Converter.
    """
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("STLtoGCode", "STLtoGCode")
        self.recent_files = []
        
        # Initialize UI helper
        from scripts.ui_qt import UI
        self.ui = UI(self)  # Pass self as parent
        
        # Set up the UI
        self._setup_ui()
        
        # Load recent files
        self._load_recent_files()
        
        # Initialize other attributes
        self.current_file = None
        self.stl_mesh = None
        self.gcode = []
        self.file_path = None
        self.worker_thread = None
        self.worker = None
        
        # Set up the logger
        self.logger = get_logger(__name__)
        self.logger.info("Starting STL to GCode Converter")
        
        # Set window properties
        self.setWindowTitle("STL to GCode Converter")
        
        # Set application icon
        icon_path = Path("assets/icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            self.logger.info(f"Loaded application icon from {icon_path}")
        else:
            self.logger.warning(f"Icon not found at {icon_path}")
        
        # Initialize the UI manager
        # self.ui = UI()
        
        # Initialize the log viewer
        self.log_viewer = None
        
        # Set window properties
        self.setWindowTitle(f"STL to GCode Converter v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Log application start
        logger.info("Application started")
        
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
        
        # Add progress reporter
        self.progress_reporter = ProgressReporter()
        
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
        
        # Add tabs with proper names
        self.tab_widget.addTab(self.stl_view_tab, "3D View")
        self.tab_widget.addTab(self.gcode_view_tab, "G-code Editor")
        
        # Set up each tab's content
        self._setup_stl_view()
        self._setup_gcode_view()
        self._setup_editor_tab()
        
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
        
        # Set initial tab
        self.tab_widget.setCurrentIndex(0)  # Show 3D View by default
    
    def _setup_stl_view(self):
        """Set up the STL view tab."""
        layout = QVBoxLayout(self.stl_view_tab)
        
        # Add controls
        controls_layout = QHBoxLayout()
        
        # Add a reset view button
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.clicked.connect(self._reset_stl_view)
        controls_layout.addWidget(reset_view_btn)
        
        # Add stretch to push controls to the left
        controls_layout.addStretch()
        
        # Add controls to layout
        layout.addLayout(controls_layout)
        
        # Create matplotlib figure and canvas
        self.stl_figure = Figure(figsize=(5, 4), dpi=100)
        self.stl_canvas = FigureCanvas(self.stl_figure)
        self.stl_ax = self.stl_figure.add_subplot(111, projection='3d')
        
        # Initialize STL visualizer for the STL view tab
        self.stl_visualizer = STLVisualizer(self.stl_ax, self.stl_canvas)
        
        # Set up the 3D axes
        self.stl_ax.set_xlabel('X')
        self.stl_ax.set_ylabel('Y')
        self.stl_ax.set_zlabel('Z')
        
        # Add navigation toolbar with custom styling
        self.stl_toolbar = NavigationToolbar(self.stl_canvas, self.stl_view_tab)
        self._style_matplotlib_toolbar(self.stl_toolbar)
        
        # Add widgets to layout
        layout.addWidget(self.stl_toolbar)
        layout.addWidget(self.stl_canvas)
        
        # Initialize with empty plot
        self.stl_visualizer.clear()
    
    def _setup_gcode_view(self):
        """Set up the G-code view tab."""
        layout = QVBoxLayout(self.gcode_view_tab)
        
        # G-code text editor
        self.gcode_editor = self.ui.create_text_editor(self.gcode_view_tab)
        layout.addWidget(self.gcode_editor)
    
    def _style_matplotlib_toolbar(self, toolbar=None):
        """Apply custom styling to the matplotlib toolbar.
        
        Args:
            toolbar: The toolbar to style. If None, styles all toolbars.
        """
        try:
            # Get the toolbar(s) to style
            toolbars = []
            if toolbar is not None:
                toolbars.append(toolbar)
            else:
                # Add all toolbars if none specified
                if hasattr(self, 'stl_toolbar') and self.stl_toolbar is not None:
                    toolbars.append(self.stl_toolbar)
                if hasattr(self, 'vis_toolbar') and self.vis_toolbar is not None:
                    toolbars.append(self.vis_toolbar)
            
            # Style each toolbar
            for tb in toolbars:
                tb.setStyleSheet("""
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
                
        except Exception as e:
            logger.error(f"Error styling matplotlib toolbar: {str(e)}", exc_info=True)
    
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
            self._add_to_recent_files(self.file_path)
            
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
        """Process chunks from the loading queue in a thread-safe manner."""
        # Skip if we're not loading or if the queue is empty
        if not hasattr(self, 'is_loading') or not self.is_loading or not hasattr(self, 'loading_queue'):
            return
        
        # Create a mutex if it doesn't exist
        if not hasattr(self, '_queue_mutex'):
            from PyQt6.QtCore import QMutex
            self._queue_mutex = QMutex()
        
        chunks_to_process = []
        
        try:
            # Lock the mutex while accessing the shared queue
            self._queue_mutex.lock()
            
            # Get up to 5 chunks to process in this batch
            max_chunks_per_tick = 5
            while self.loading_queue and len(chunks_to_process) < max_chunks_per_tick:
                chunks_to_process.append(self.loading_queue.pop(0))
        except Exception as e:
            logger.error(f"Error accessing loading queue: {e}", exc_info=True)
            return
        finally:
            # Always unlock the mutex, even if an exception occurs
            if hasattr(self, '_queue_mutex') and self._queue_mutex.tryLock():
                self._queue_mutex.unlock()
        
        # Process the chunks we've taken from the queue
        for chunk_data in chunks_to_process:
            try:
                if not hasattr(self, 'is_loading') or not self.is_loading:
                    break
                    
                # Process the chunk
                self._process_chunk(chunk_data)
                
                # Update progress if available
                if 'progress' in chunk_data:
                    status = chunk_data.get('status', '')
                    self._update_loading_progress(chunk_data['progress'], status)
                    
            except Exception as e:
                logger.error(f"Error processing chunk: {e}", exc_info=True)
                
                # If we encounter an error, try to continue with the next chunk
                continue
    
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
        try:
            # Make sure we're still in a loading state
            if not hasattr(self, 'is_loading') or not self.is_loading:
                logger.debug("Ignoring chunk - loading already completed or cancelled")
                return
                
            # Update progress if available
            if 'progress' in chunk_data:
                self.loading_progress = chunk_data['progress']
                if hasattr(self, 'progress_dialog') and self.progress_dialog:
                    self.progress_dialog.setValue(int(self.loading_progress))
            
            # Get vertices and faces from chunk
            if 'vertices' not in chunk_data or len(chunk_data['vertices']) == 0:
                logger.warning("Received chunk with no vertices")
                return
                
            new_vertices = np.array(chunk_data['vertices'], dtype=np.float32)
            new_faces = np.array(chunk_data.get('faces', []), dtype=np.uint32)
            
            # Initialize arrays if they don't exist
            if not hasattr(self, 'current_vertices') or self.current_vertices is None:
                self.current_vertices = np.zeros((0, 3), dtype=np.float32)
            if not hasattr(self, 'current_faces') or self.current_faces is None:
                self.current_faces = np.zeros((0, 3), dtype=np.uint32)
            
            # Store the current vertex count for face index offset
            vertex_offset = len(self.current_vertices)
            
            try:
                # Add the new vertices
                self.current_vertices = np.vstack((self.current_vertices, new_vertices))
                
                # If we have faces, add them with the correct offset
                if len(new_faces) > 0:
                    new_faces_offset = new_faces + vertex_offset
                    self.current_faces = np.vstack((self.current_faces, new_faces_offset))
                
                logger.debug(f"Processed chunk. Total vertices: {len(self.current_vertices)}, "
                           f"Total faces: {len(self.current_faces)}")
                
                # If this is the final chunk, update visualization
                if chunk_data.get('is_final', False):
                    logger.info(f"Final chunk received. Total vertices: {len(self.current_vertices)}, "
                               f"Total faces: {len(self.current_faces)}")
                    self._on_loading_finished(success=True)
                    
            except Exception as e:
                logger.error(f"Error processing chunk: {str(e)}", exc_info=True)
                self._on_loading_finished(success=False, error_msg=f"Error processing mesh data: {str(e)}")
                
        except Exception as e:
            logger.error(f"Unexpected error in _on_chunk_loaded: {str(e)}", exc_info=True)
            self._on_loading_finished(success=False, error_msg=f"Unexpected error: {str(e)}")
    
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
            self._add_to_recent_files(self.gcode_file_path)
            
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
                    # Clean up the update checker
                    if hasattr(self, 'update_checker'):
                        self.update_checker.deleteLater()
                        del self.update_checker
            
            def on_no_update():
                if force_check:  # Only show message if user explicitly checked
                    QMessageBox.information(
                        self,
                        "No Updates",
                        f"You are running the latest version ({__version__}).",
                        QMessageBox.StandardButton.Ok
                    )
                self.statusBar().showMessage("You are running the latest version", 3000)
                # Clean up the update checker
                if hasattr(self, 'update_checker'):
                    self.update_checker.deleteLater()
                    del self.update_checker
            
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
                # Clean up the update checker
                if hasattr(self, 'update_checker'):
                    self.update_checker.deleteLater()
                    del self.update_checker
            
            # Create the update checker as an instance variable to maintain signal connections
            self.update_checker = UpdateChecker(current_version=__version__)
            
            # Connect signals after defining the handlers
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
            # Clean up the update checker if it was created
            if hasattr(self, 'update_checker'):
                self.update_checker.deleteLater()
                del self.update_checker
    
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
    
    def _update_visualization(self):
        """Update the 3D visualization with the current mesh data."""
        try:
            # Check if we have valid mesh data
            if not hasattr(self, 'current_vertices') or len(self.current_vertices) == 0:
                logger.warning("No mesh data available to display")
                return
                
            logger.debug(f"Updating visualization with {len(self.current_vertices)} vertices and "
                       f"{len(self.current_faces) if hasattr(self, 'current_faces') else 0} faces")
            
            # Ensure we have the STL visualizer
            if not hasattr(self, 'stl_visualizer') or self.stl_visualizer is None:
                logger.error("STL visualizer not initialized")
                # Try to initialize the visualizer if it's not available
                if hasattr(self, '_setup_stl_view'):
                    logger.debug("Initializing STL visualizer...")
                    self._setup_stl_view()
                    if not hasattr(self, 'stl_visualizer') or self.stl_visualizer is None:
                        logger.error("Failed to initialize STL visualizer")
                        return
                else:
                    logger.error("Cannot initialize STL visualizer - _setup_stl_view method not found")
                    return
            
            # Convert vertices to numpy array if needed
            vertices = np.asarray(self.current_vertices, dtype=np.float32)
            
            # Generate faces if they don't exist (triangle soup)
            if not hasattr(self, 'current_faces') or self.current_faces is None or len(self.current_faces) == 0:
                logger.debug("Generating faces for triangle soup")
                num_vertices = len(vertices)
                if num_vertices % 3 != 0:
                    logger.error(f"Number of vertices ({num_vertices}) is not divisible by 3")
                    return
                faces = np.arange(num_vertices, dtype=np.uint32).reshape(-1, 3)
            else:
                faces = np.asarray(self.current_faces, dtype=np.uint32)
            
            # Ensure we have valid data
            if len(vertices) == 0:
                logger.warning("No vertices to display")
                return
                
            if len(faces) == 0:
                logger.warning("No faces to display")
                return
            
            # Log some debug info
            logger.debug(f"Vertices shape: {vertices.shape}, dtype: {vertices.dtype}")
            logger.debug(f"Faces shape: {faces.shape}, dtype: {faces.dtype}")
            logger.debug(f"First few vertices: {vertices[:2]}")
            logger.debug(f"First few faces: {faces[:2]}")
            
            try:
                # Update the mesh in the visualizer
                logger.debug("Updating mesh in visualizer...")
                self.stl_visualizer.update_mesh(vertices, faces)
                
                # Force a redraw of the canvas
                if hasattr(self, 'stl_canvas'):
                    logger.debug("Forcing canvas redraw...")
                    self.stl_canvas.draw_idle()
                
                # Update the window title with the current file name
                if hasattr(self, 'current_stl_file'):
                    self.setWindowTitle(f"STL to G-Code - {os.path.basename(self.current_stl_file)}")
                
                logger.info("Visualization updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating visualization: {e}", exc_info=True)
                self._handle_loading_error(
                    f"Error updating 3D view: {str(e)}",
                    "Visualization Error"
                )
                
        except Exception as e:
            logger.error(f"Error in _update_visualization: {e}", exc_info=True)
            self._handle_loading_error(
                f"Error updating 3D view: {str(e)}",
                "Visualization Error"
            )
    
    def _reset_stl_view(self):
        """Reset the STL view to its default state."""
        try:
            if hasattr(self, 'stl_visualizer') and self.stl_visualizer is not None:
                # Clear the current visualization
                self.stl_visualizer.clear()
                
                # Reset the view to show all content
                if hasattr(self, 'current_vertices') and len(self.current_vertices) > 0:
                    # If we have mesh data, update the visualizer with it
                    self.stl_visualizer.update_mesh(
                        vertices=self.current_vertices,
                        faces=self.current_faces,
                        file_path=self.file_path
                    )
                
                # Update the canvas
                self.stl_canvas.draw_idle()
                
        except Exception as e:
            error_msg = f"Error resetting STL view: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._handle_loading_error(error_msg)

    def _setup_editor_tab(self):
        """Set up the G-code editor tab."""
        # Create a new tab for the G-code editor
        self.editor_tab = QWidget()
        self.tab_widget.addTab(self.editor_tab, "G-code Editor")
        
        # Create layout for the editor tab
        layout = QVBoxLayout(self.editor_tab)
        
        # Add a toolbar for editor actions
        editor_toolbar = QToolBar("Editor")
        layout.addWidget(editor_toolbar)
        
        # Add actions to the toolbar
        save_action = QAction("Save", self)
        save_action.triggered.connect(lambda: self.save_gcode())
        editor_toolbar.addAction(save_action)
        
        # Add the G-code editor
        self.gcode_editor = QTextEdit()
        self.gcode_editor.setFont(QFont("Courier", 10))
        self.gcode_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.gcode_editor)
        
        # Add status bar for editor information
        editor_status = QStatusBar()
        self.editor_status_label = QLabel("Ready")
        editor_status.addWidget(self.editor_status_label)
        layout.addWidget(editor_status)
        
        # Connect text changed signal
        self.gcode_editor.textChanged.connect(self._on_editor_text_changed)
    
    def _on_editor_text_changed(self):
        """Handle text changes in the G-code editor."""
        # Update status with line count
        line_count = self.gcode_editor.document().lineCount()
        self.editor_status_label.setText(f"Lines: {line_count}")

    def _load_recent_files(self):
        """Load the list of recently opened files from settings."""
        # Get recent files from settings, defaulting to an empty list
        recent_files = self.settings.value('recent_files')
        
        # Handle different possible return types from QSettings
        if recent_files is None:
            self.recent_files = []
        elif isinstance(recent_files, str):
            # If it's a single string, convert to a list
            self.recent_files = [recent_files] if recent_files else []
        elif isinstance(recent_files, list):
            # If it's already a list, use it directly
            self.recent_files = recent_files
        else:
            # For any other type, convert to string and wrap in a list
            self.recent_files = [str(recent_files)]
            
        # Ensure all paths are strings and exist
        self.recent_files = [str(path) for path in self.recent_files if path and os.path.exists(str(path))]
        
        # Update the menu
        self._update_recent_files_menu()
    
    def _update_recent_files_menu(self):
        """Update the recent files menu with the current list of recent files."""
        if not hasattr(self, 'recent_menu'):
            return
            
        # Clear the current menu
        self.recent_menu.clear()
        
        # Add recent files
        for i, file_path in enumerate(self.recent_files[:10]):  # Show max 10 recent files
            action = self.recent_menu.addAction(f'&{i+1} {os.path.basename(file_path)}',
                                             lambda checked, path=file_path: self._open_recent_file(path))
            action.setToolTip(file_path)
        
        # Add a separator and clear action if there are recent files
        if self.recent_files:
            self.recent_menu.addSeparator()
            clear_action = self.recent_menu.addAction('Clear Recent Files', self._clear_recent_files)
            clear_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        
        # Disable the menu if no recent files
        self.recent_menu.setEnabled(bool(self.recent_files))

    def _open_recent_file(self, file_path):
        """Open a file from the recent files list."""
        if os.path.exists(file_path):
            self.load_stl_file(file_path)
        else:
            # Remove non-existent file from recent files
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
                self.settings.setValue('recent_files', self.recent_files)
                self._update_recent_files_menu()
            QMessageBox.warning(self, 'File Not Found',
                             f'The file was not found:\n{file_path}')

    def _clear_recent_files(self):
        """Clear the list of recent files."""
        reply = QMessageBox.question(
            self, 'Clear Recent Files',
            'Are you sure you want to clear the list of recently opened files?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.recent_files = []
            self.settings.setValue('recent_files', self.recent_files)
            self._update_recent_files_menu()
            
    def _add_to_recent_files(self, file_path):
        """Add a file to the recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        # Keep only unique paths and limit the number of recent files
        self.recent_files = list(dict.fromkeys(self.recent_files))[:10]
        self.settings.setValue('recent_files', self.recent_files)
        self._update_recent_files_menu()

    def _cancel_loading(self):
        """Cancel the ongoing STL loading process."""
        try:
            # Prevent multiple cancellation attempts
            if not hasattr(self, 'is_loading') or not self.is_loading:
                logger.debug("No loading in progress to cancel")
                return
                
            logger.info("Cancelling STL loading...")
            
            # Mark loading as cancelled
            self.is_loading = False
            
            # Stop the loading timer if it's running
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
            
            # Cancel the worker if it exists
            if hasattr(self, 'loading_worker'):
                try:
                    if not sip.isdeleted(self.loading_worker):
                        self.loading_worker.cancel()
                except Exception as e:
                    logger.warning(f"Error cancelling worker: {e}")
            
            # Clean up the worker thread
            if hasattr(self, 'loading_thread'):
                try:
                    # Disconnect all signals first to prevent any callbacks
                    if hasattr(self, 'loading_worker') and self.loading_worker is not None:
                        try:
                            self.loading_worker.chunk_loaded.disconnect()
                            self.loading_worker.loading_finished.disconnect()
                            self.loading_worker.error_occurred.disconnect()
                        except (RuntimeError, TypeError):
                            # Disconnect might fail if signals were already disconnected
                            pass
                    
                    # Stop the thread
                    if not sip.isdeleted(self.loading_thread):
                        if self.loading_thread.isRunning():
                            self.loading_thread.quit()
                            if not self.loading_thread.wait(1000):  # Wait up to 1 second
                                logger.warning("Thread did not stop gracefully, terminating...")
                                self.loading_thread.terminate()
                                self.loading_thread.wait()
                        self.loading_thread.deleteLater()
                except Exception as e:
                    logger.error(f"Error stopping loading thread: {e}", exc_info=True)
                finally:
                    # Clean up references
                    if hasattr(self, 'loading_worker'):
                        del self.loading_worker
                    del self.loading_thread
            
            # Clean up progress dialog if it exists
            if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
                try:
                    if not sip.isdeleted(self.progress_dialog):
                        self.progress_dialog.cancel()
                        self.progress_dialog.close()
                        self.progress_dialog.deleteLater()
                except Exception as e:
                    logger.warning(f"Error closing progress dialog: {e}")
                finally:
                    del self.progress_dialog
            
            # Reset loading state
            self._reset_loading_state()
            
            logger.info("STL loading cancelled")
            
        except Exception as e:
            logger.error(f"Error in _cancel_loading: {e}", exc_info=True)
            self._handle_loading_error(
                f"An error occurred while cancelling the loading process: {str(e)}",
                "Cancellation Error"
            )
    
    def _handle_loading_error(self, error_message, title="Loading Error"):
        """
        Handle errors that occur during STL loading.
        
        Args:
            error_message (str): The error message to display
            title (str): The title for the error dialog
        """
        logger.error(f"{title}: {error_message}", exc_info=True)
        
        # Ensure we're in the main thread for UI operations
        if not sip.isdeleted(self):
            # Show error message to user
            QMessageBox.critical(
                self,
                title,
                f"An error occurred while loading the STL file:\n\n{error_message}\n\nPlease check the logs for more details.",
                QMessageBox.StandardButton.Ok
            )
            
            # Reset loading state
            self._reset_loading_state()
            
            # Close progress dialog if it exists
            if hasattr(self, 'progress_dialog'):
                try:
                    self.progress_dialog.close()
                    del self.progress_dialog
                except Exception as e:
                    logger.warning(f"Error closing progress dialog: {e}")
        
        # Log the error
        logger.error(f"STL loading failed: {error_message}")

    def _on_loading_finished(self, success=True, error_msg=None):
        """
        Handle the completion of the STL loading process.
        
        Args:
            success: Whether loading was successful
            error_msg: Error message if loading failed
        """
        # Prevent multiple calls to this method
        if not hasattr(self, 'is_loading') or not self.is_loading:
            logger.debug("Ignoring duplicate loading finished signal")
            return
            
        logger.debug(f"Loading finished. Success: {success}, Error: {error_msg}")
        
        # Mark loading as complete
        self.is_loading = False
        
        try:
            # Stop the loading timer if it exists
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
            
            # Clean up the worker thread if it exists
            if hasattr(self, 'loading_thread'):
                try:
                    # Disconnect all signals first
                    if hasattr(self, 'loading_worker') and self.loading_worker is not None:
                        try:
                            self.loading_worker.chunk_loaded.disconnect()
                            self.loading_worker.loading_finished.disconnect()
                            self.loading_worker.error_occurred.disconnect()
                        except (RuntimeError, TypeError) as e:
                            logger.debug(f"Error disconnecting signals: {e}")
                    
                    # Stop the thread
                    if not sip.isdeleted(self.loading_thread):
                        if self.loading_thread.isRunning():
                            self.loading_thread.quit()
                            if not self.loading_thread.wait(1000):
                                logger.warning("Thread did not stop gracefully, terminating...")
                                self.loading_thread.terminate()
                                self.loading_thread.wait()
                        self.loading_thread.deleteLater()
                except Exception as e:
                    logger.error(f"Error stopping loading thread: {e}", exc_info=True)
                finally:
                    # Clean up references
                    if hasattr(self, 'loading_worker'):
                        del self.loading_worker
                    del self.loading_thread
            
            # Close progress dialog if it exists
            if hasattr(self, 'progress_dialog') and self.progress_dialog is not None:
                try:
                    if not sip.isdeleted(self.progress_dialog):
                        self.progress_dialog.setValue(100)
                        self.progress_dialog.close()
                        self.progress_dialog.deleteLater()
                except Exception as e:
                    logger.warning(f"Error closing progress dialog: {e}")
                finally:
                    del self.progress_dialog
            
            # Handle success/failure
            if success:
                # Only update visualization if we have valid mesh data
                if hasattr(self, 'current_vertices') and len(self.current_vertices) > 0:
                    logger.debug(f"Updating visualization with {len(self.current_vertices)} vertices and {len(self.current_faces) if hasattr(self, 'current_faces') else 0} faces")
                    self._update_visualization()
                    logger.debug("Visualization update complete")
                else:
                    logger.warning("No mesh data available to display")
                    
                # Update status bar
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage("STL file loaded successfully", 5000)
            else:
                # Show error message
                if error_msg:
                    logger.error(f"STL loading failed: {error_msg}")
                    self._handle_loading_error(error_msg, "STL Loading Error")
                
        except Exception as e:
            logger.error(f"Error in _on_loading_finished: {e}", exc_info=True)
            self._handle_loading_error(
                f"An error occurred while finalizing the loading process: {str(e)}",
                "Loading Completion Error"
            )
    
    def _update_loading_progress(self, progress, message=None):
        """
        Update the progress dialog with the current loading status.
        
        Args:
            progress (int/float): Progress percentage (0-100)
            message (str, optional): Optional status message
        """
        # Initialize progress reporter if needed
        if not hasattr(self, 'progress_reporter'):
            self.progress_reporter = ProgressReporter()
            
        # Set the current progress dialog if not set
        if not hasattr(self.progress_reporter, 'progress_dialog') or self.progress_reporter.progress_dialog is None:
            self.progress_reporter.progress_dialog = getattr(self, 'progress_dialog', None)
            
        # Set loading state
        self.progress_reporter.is_loading = getattr(self, 'is_loading', False)
        
        # Update progress
        self.progress_reporter.update_progress(progress, message)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = STLToGCodeApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())
