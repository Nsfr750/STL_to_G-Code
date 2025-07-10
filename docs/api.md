# API Reference

## Core Application

### Class: `STLToGCodeApp`

Main application class that initializes and runs the STL to GCode Converter.

```python
class STLToGCodeApp(QMainWindow):
    def __init__(self, parent=None):
        """Initialize the main application window."""
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        self.setup_logging()
    
    def open_file(self, file_path=None):
        """Open and load an STL file."""
        pass
    
    def convert_to_gcode(self):
        """Convert the loaded STL to G-code."""
        pass
    
    def save_gcode(self, file_path=None):
        """Save the generated G-code to a file."""
        pass
    
    def show_gcode_viewer(self):
        """Display the G-code viewer with the current G-code."""
        pass
    
    def show_log_viewer(self, show=True):
        """Show or hide the log viewer panel."""
        pass
    
    def setup_ui(self):
        """Initialize the user interface components."""
        pass
    
    def setup_connections(self):
        """Set up signal-slot connections."""
        pass
    
    def setup_logging(self):
        """Configure the logging system."""
        pass
```

## UI Components

### Class: `GCodeViewer`

Interactive G-code viewer with syntax highlighting.

```python
class GCodeViewer(QDockWidget):
    def __init__(self, parent=None):
        """Initialize the G-code viewer."""
        super().__init__("G-code Viewer", parent)
        self.setup_ui()
    
    def set_gcode(self, gcode):
        """Set the G-code to display."""
        pass
    
    def highlight_line(self, line_number):
        """Highlight a specific line in the G-code."""
        pass
    
    def find_text(self, text):
        """Find and highlight text in the G-code."""
        pass
```

### Class: `LogViewer`

Interactive log viewer with filtering capabilities.

```python
class LogViewer(QDockWidget):
    def __init__(self, parent=None):
        """Initialize the log viewer."""
        super().__init__("Log Viewer", parent)
        self.setup_ui()
    
    def add_log_entry(self, level, message):
        """Add a new log entry."""
        pass
    
    def set_log_level(self, level):
        """Set the minimum log level to display."""
        pass
    
    def clear_logs(self):
        """Clear all log entries."""
        pass
```

## Utility Classes

### Class: `STLProcessor`

Handles STL file processing and G-code generation.

```python
class STLProcessor(QObject):
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the STL processor."""
        super().__init__(parent)
    
    def load_stl(self, file_path):
        """Load an STL file for processing."""
        pass
    
    def generate_gcode(self, parameters):
        """Generate G-code from the loaded STL."""
        pass
    
    def cancel_processing(self):
        """Cancel the current processing operation."""
        pass
```

### Class: `SettingsManager`

Manages application settings and preferences.

```python
class SettingsManager(QObject):
    def __init__(self, parent=None):
        """Initialize the settings manager."""
        super().__init__(parent)
        self.settings = QSettings("STLToGCode", "STL to GCode Converter")
    
    def get_setting(self, key, default=None):
        """Get a setting value."""
        return self.settings.value(key, default)
    
    def set_setting(self, key, value):
        """Set a setting value."""
        self.settings.setValue(key, value)
    
    def get_recent_files(self):
        """Get the list of recently opened files."""
        return self.get_setting("recentFiles", [])
    
    def add_recent_file(self, file_path):
        """Add a file to the recent files list."""
        recent = self.get_recent_files()
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        recent = recent[:10]  # Keep only the 10 most recent files
        self.set_setting("recentFiles", recent)
```

## Enumerations

### `LogLevel`

```python
class LogLevel(IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
```

### `ViewMode`

```python
class ViewMode(Enum):
    SOLID = "Solid"
    WIREFRAME = "Wireframe"
    POINTS = "Points"
    X_RAY = "X-Ray"
```

## Signals

### `ProcessingSignals`

```python
class ProcessingSignals(QObject):
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    status = pyqtSignal(str)    # Status message
    finished = pyqtSignal()     # Processing finished
    error = pyqtSignal(str)     # Error message
```

## Constants

```python
# Default G-code parameters
DEFAULT_PARAMETERS = {
    'layer_height': 0.2,
    'print_speed': 60,
    'nozzle_temp': 200,
    'bed_temp': 60,
    'infill_density': 20,
    'shells': 2,
    'retraction': True,
    'retraction_distance': 5.0,
    'retraction_speed': 45.0
}

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.stl', '.STL', '.gcode', '.gco', '.g']

# Logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

## Example Usage

```python
# Create and show the main application window
app = QApplication(sys.argv)
window = STLToGCodeApp()
window.show()
sys.exit(app.exec())
```

## Dependencies

- PyQt6 >= 6.4.0
- numpy-stl >= 2.17.1
- matplotlib >= 3.5.0
- numpy >= 1.21.0
- packaging >= 21.0

## Versioning

This API follows [Semantic Versioning](https://semver.org/). The current API version is 2.0.0.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For the full license text, see the [LICENSE](../LICENSE) file.
