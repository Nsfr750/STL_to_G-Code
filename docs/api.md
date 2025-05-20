# API Documentation

## Main Application

### Class: STLToGCodeApp

```python
class STLToGCodeApp:
    def __init__(self, root)
    def open_file(self)
    def convert_to_gcode(self)
    def show_help(self)
    def show_about(self)
    def show_sponsor(self)
    def _setup_logging(self)
```

### Configuration

```python
class Config:
    def __init__(self)
    def get(self, key, default=None)
    def set(self, key, value)
    def add_recent_file(self, file_path)
    def _load_config(self)
    def save(self)
```

## UI Components

### Help Dialog

```python
class HelpDialog:
    def __init__(self, parent)
    def show_help(self)
```

### About Dialog

```python
class About:
    @staticmethod
    def show_about(root)
```

### Sponsor Dialog

```python
class Sponsor:
    def __init__(self, root)
    def show_sponsor(self)
```

## Version Management

```python
def get_version()
def get_version_info()
def check_version_compatibility(min_version)
```

## Error Handling

```python
def _handle_error(message)
```

## File Operations

```python
def open_file()
def save_file()
def load_config()
def save_config()
```

## UI Styling

```python
def setup_styles()
def configure_theme()
def create_widgets()
```

## Progress Tracking

```python
def update_progress(value)
def show_status(message)
def clear_status()
```

## Logging

```python
def setup_logging()
def log_message(level, message)
def get_logger()
```

## Example Usage

```python
# Create application
root = tk.Tk()
app = STLToGCodeApp(root)

# Open file
app.open_file()

# Convert to GCode
app.convert_to_gcode()

# Show help
app.show_help()

# Show about dialog
app.show_about()

# Show sponsor options
app.show_sponsor()
```
