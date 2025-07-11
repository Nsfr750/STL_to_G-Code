"""
Test script for STL file loading and OpenGL fallback functionality.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                           QPushButton, QFileDialog, QMessageBox, QLabel, QHBoxLayout,
                           QStatusBar, QToolBar, QSizePolicy, QStyle, QProgressBar,
                           QDockWidget, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeySequence
import logging
from pathlib import Path

# Import the error handling utilities
try:
    from scripts.error_handling import (
        handle_error, handle_file_error, check_file_path,
        show_warning, show_info, confirm
    )
except ImportError:
    # Fall back to relative import if running as a module
    from ..scripts.error_handling import (
        handle_error, handle_file_error, check_file_path,
        show_warning, show_info, confirm
    )

# Set up logging
log_file = 'stl_to_gcode.log'
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='w'  # Overwrite previous log
    )
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {os.path.abspath(log_file)}")
    
except Exception as e:
    print(f"Failed to initialize logging: {e}")
    raise

# Import matplotlib with Qt5 backend
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import the STL visualizer
try:
    from scripts.STL_view import STLVisualizer
except ImportError:
    # Fall back to relative import if running as a module
    from ..scripts.STL_view import STLVisualizer

class MeshInfoPanel(QDockWidget):
    """Panel to display mesh information and controls."""
    
    def __init__(self, parent=None):
        super().__init__("Mesh Information", parent)
        self.setObjectName("MeshInfoPanel")
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                        QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        # Create main widget and layout
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        
        # Mesh info group
        self.info_group = QGroupBox("Mesh Statistics")
        self.info_layout = QFormLayout()
        
        # Info labels
        self.vertex_count = QLabel("0")
        self.face_count = QLabel("0")
        self.file_name = QLabel("No file loaded")
        self.file_size = QLabel("0 KB")
        
        # Add to layout
        self.info_layout.addRow("File:", self.file_name)
        self.info_layout.addRow("Vertices:", self.vertex_count)
        self.info_layout.addRow("Faces:", self.face_count)
        self.info_layout.addRow("File size:", self.file_size)
        
        self.info_group.setLayout(self.info_layout)
        
        # View controls group
        self.view_group = QGroupBox("View Controls")
        self.view_layout = QVBoxLayout()
        
        # View angle controls
        self.azimuth = QSpinBox()
        self.azimuth.setRange(-180, 180)
        self.azimuth.setValue(45)
        self.azimuth.setSuffix("°")
        
        self.elevation = QSpinBox()
        self.elevation.setRange(-90, 90)
        self.elevation.setValue(30)
        self.elevation.setSuffix("°")
        
        # Add to layout
        view_form = QFormLayout()
        view_form.addRow("Azimuth:", self.azimuth)
        view_form.addRow("Elevation:", self.elevation)
        
        # Toggle wireframe
        self.wireframe = QCheckBox("Show wireframe")
        self.wireframe.setChecked(True)
        
        self.view_layout.addLayout(view_form)
        self.view_layout.addWidget(self.wireframe)
        self.view_group.setLayout(self.view_layout)
        
        # Add groups to main layout
        self.layout.addWidget(self.info_group)
        self.layout.addWidget(self.view_group)
        self.layout.addStretch()
        
        self.setWidget(self.widget)
    
    def update_mesh_info(self, vertices, faces, file_path):
        """Update the mesh information display."""
        self.vertex_count.setText(f"{len(vertices):,}")
        self.face_count.setText(f"{len(faces):,}")
        
        if file_path and os.path.isfile(file_path):
            self.file_name.setText(os.path.basename(file_path))
            size = os.path.getsize(file_path)
            self.file_size.setText(f"{size/1024:.1f} KB")
        else:
            self.file_name.setText("No file loaded")
            self.file_size.setText("0 KB")

class STLLoadingTest(QMainWindow):
    """Main window for testing STL loading and OpenGL fallback."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        self.show()
    
    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("STL to G-Code - Test Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)  # Set spacing on the layout, not the widget
        self.main_widget.setLayout(self.layout)
        
        # Create UI components
        self.create_toolbar()
        self.create_status_bar()
        self.create_viewer()
        self.create_dock_widgets()
        
        # Add some padding
        self.layout.setContentsMargins(10, 10, 10, 10)
    
    def setup_connections(self):
        """Set up signal-slot connections."""
        self.open_action.triggered.connect(self.load_stl)
        self.opengl_action.toggled.connect(self.toggle_opengl)
    
    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Open STL action
        self.open_action = QAction(
            QIcon.fromTheme("document-open"),
            "&Open STL",
            self,
            shortcut=QKeySequence.StandardKey.Open,
            statusTip="Open an STL file (Ctrl+O)",
            toolTip="Open STL File\nCtrl+O"
        )
        toolbar.addAction(self.open_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # OpenGL toggle
        self.opengl_action = QAction(
            QIcon.fromTheme("video-display"),
            "OpenGL",
            self,
            checkable=True,
            statusTip="Toggle OpenGL rendering (Ctrl+G)",
            toolTip="Toggle OpenGL Rendering\nCtrl+G"
        )
        self.opengl_action.setChecked(True)
        self.opengl_action.setShortcut(QKeySequence("Ctrl+G"))
        toolbar.addAction(self.opengl_action)
    
    def create_status_bar(self):
        """Create and configure the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.statusBar.addPermanentWidget(self.status_label, 1)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(200)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.hide()
        self.statusBar.addPermanentWidget(self.progress)
    
    def create_viewer(self):
        """Set up the 3D viewer."""
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Initialize STL visualizer
        self.visualizer = STLVisualizer(self.ax, self.canvas)
        
        # Add to layout
        self.layout.addWidget(self.canvas)
    
    def create_dock_widgets(self):
        """Create dockable widgets."""
        # Create and add mesh info panel
        self.mesh_panel = MeshInfoPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.mesh_panel)
        
        # Connect signals
        self.mesh_panel.azimuth.valueChanged.connect(self.update_view_angle)
        self.mesh_panel.elevation.valueChanged.connect(self.update_view_angle)
        self.mesh_panel.wireframe.toggled.connect(self.toggle_wireframe)
    
    def show_progress(self, message, value=None, maximum=None):
        """Show progress in the status bar."""
        if value is not None:
            self.progress.setValue(value)
        if maximum is not None:
            self.progress.setMaximum(maximum)
        if message:
            self.status_label.setText(message)
        self.progress.setVisible(value is not None)
        QApplication.processEvents()
    
    def toggle_opengl(self, enabled):
        """Toggle OpenGL rendering."""
        try:
            self.visualizer.use_opengl = enabled
            render_success = self.visualizer.render()
            if render_success:
                self.canvas.draw()
            status = "enabled" if enabled else "disabled"
            self.statusBar.showMessage(f"OpenGL {status}", 3000)
        except Exception as e:
            handle_error(e, "Error toggling OpenGL", self)
            self.opengl_action.setChecked(not enabled)
    
    def load_stl(self, file_path=None):
        """Open a file dialog to select and load an STL file."""
        try:
            # If file_path is None, False, or not a string, show file dialog
            if not isinstance(file_path, str):
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open STL File",
                    os.path.expanduser("~"),
                    "STL Files (*.stl *.STL);;All Files (*)"
                )
                
                if not file_path:  # User cancelled
                    self.statusBar.showMessage("File selection cancelled", 3000)
                    return
            
            # Convert to absolute path and normalize
            file_path = os.path.abspath(file_path)
            
            # Validate file
            if not os.path.isfile(file_path):
                show_warning(f"File not found: {file_path}", "File Error", self)
                return
                
            if not os.access(file_path, os.R_OK):
                show_warning(f"Cannot read file (permission denied): {file_path}", 
                           "File Error", self)
                return
            
            # Disable UI during loading
            self.setEnabled(False)
            self.show_progress("Loading STL file...", 0, 100)
            
            # Use a timer to ensure UI updates
            QTimer.singleShot(100, lambda: self._load_stl_async(file_path))
            
        except Exception as e:
            handle_error(e, "Error in file selection", self)
            self.setEnabled(True)
    
    def _load_stl_async(self, file_path):
        """Load STL file asynchronously."""
        try:
            # Show loading progress
            self.show_progress("Reading STL data...", 30)
            
            # Import required modules
            try:
                from stl import mesh as stl_mesh
                import numpy as np
            except ImportError:
                show_warning(
                    "numpy-stl package is required to load STL files\n"
                    "Install it with: pip install numpy-stl",
                    "Dependency Error",
                    self
                )
                return
            
            # Read the STL file
            self.show_progress("Processing mesh...", 60)
            stl_data = stl_mesh.Mesh.from_file(file_path)
            
            # Process vertices and faces
            vertices = stl_data.vectors.reshape(-1, 3)
            num_triangles = len(stl_data.vectors)
            faces = np.arange(num_triangles * 3, dtype=np.int32).reshape(-1, 3)
            
            # Update the mesh
            self.show_progress("Updating visualization...", 90)
            success = self.visualizer.update_mesh(vertices, faces, file_path)
            
            if success:
                # Store the mesh plot for later reference
                self.mesh_plot = self.visualizer.mesh_plot
                
                # Update mesh info panel
                self.mesh_panel.update_mesh_info(vertices, faces, file_path)
                
                # Set initial view angles
                self.mesh_panel.azimuth.setValue(45)
                self.mesh_panel.elevation.setValue(30)
                
                render_success = self.visualizer.render()
                if render_success:
                    self.canvas.draw()
                
                # Show success message
                self.statusBar.showMessage(
                    f"Loaded {os.path.basename(file_path)} - "
                    f"Vertices: {len(vertices):,}, Faces: {len(faces):,}",
                    5000
                )
            else:
                show_warning(
                    "Failed to update mesh. The file may be corrupted or in an unsupported format.",
                    "Load Error",
                    self
                )
            
        except Exception as e:
            handle_error(e, f"Error loading STL file: {file_path}", self)
        
        finally:
            # Clean up
            self.show_progress("", 100)
            self.setEnabled(True)
            QTimer.singleShot(1000, self.progress.hide)
    
    def update_view_angle(self):
        """Update the 3D view angle."""
        try:
            self.ax.view_init(
                elev=self.mesh_panel.elevation.value(),
                azim=self.mesh_panel.azimuth.value()
            )
            self.canvas.draw()
        except Exception as e:
            handle_error(e, "Error updating view angle", self)
    
    def toggle_wireframe(self, show):
        """Toggle wireframe display."""
        try:
            if hasattr(self, 'visualizer') and self.visualizer is not None:
                success = self.visualizer.toggle_wireframe(show)
                if success:
                    self.canvas.draw()
                else:
                    logger.warning("Failed to toggle wireframe: visualizer returned False")
        except Exception as e:
            handle_error(e, "Error toggling wireframe", self)

def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting STL to G-Code Test Viewer")
        
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle('Fusion')
        
        # Set application metadata
        app.setApplicationName("STL to G-Code")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("YourOrganization")
        
        # Create and show the main window
        try:
            logger.info("Creating main window")
            window = STLLoadingTest()
            
            # Load file from command line if provided
            if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
                logger.info(f"Loading file from command line: {sys.argv[1]}")
                window.load_stl(sys.argv[1])
            
            logger.info("Application started successfully")
            return app.exec()
            
        except Exception as e:
            logger.critical("Failed to create main window", exc_info=True)
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"Failed to start application: {str(e)}\n\n"
                "Check the log file for more details.\n"
                f"Log file: {os.path.abspath(log_file)}"
            )
            return 1
            
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
