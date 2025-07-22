# Prerequisites

Before running the STL to GCode Converter, ensure that you have the following installed:


## System Requirements


### 🖥️ Hardware Requirements


#### Minimum

- **CPU**: Dual-core processor (2.0 GHz or faster)
- **RAM**: 4 GB
- **Storage**: 1 GB free space
- **Display**: 1366x768 resolution


#### Recommended

- **CPU**: Quad-core processor (3.0 GHz or faster)
- **RAM**: 8 GB or more
- **Storage**: 2 GB free space (SSD recommended)
- **Display**: 1920x1080 resolution or higher with 100% scaling
- **GPU**: Discrete GPU with OpenGL 3.3+ support for better 3D rendering


### 💻 Software Requirements


#### Operating Systems

- **Windows**: 10 or later (64-bit)
- **macOS**: 12.0 (Monterey) or later (Apple Silicon or Intel)
- **Linux**: Ubuntu 22.04 LTS or later, Fedora 36+, or other modern distributions
  - May require additional system packages (see below)


#### Python Requirements

- **Python**: 3.8 or later (3.10+ recommended)
- **pip**: 23.0 or later
- **Git**: For development and version control


## Required Python Libraries


### Core Dependencies

- **PyQt6**: Modern GUI framework (>= 6.6.0)
- **PyQt6-WebEngine**: Qt WebEngine for PyQt6 (>= 6.6.0)
- **QScintilla**: Advanced text editor component (>= 2.15.1)
- **numpy**: Numerical computing (>= 1.26.0)
- **numpy-stl**: STL file processing (>= 3.1.0)
- **scipy**: Scientific computing (>= 1.12.0)
- **scikit-image**: Image processing (>= 0.22.0)
- **matplotlib**: 3D visualization (>= 3.8.0)
- **Pillow**: Image processing (>= 10.1.0)
- **markdown**: Markdown rendering (>= 3.5.0)
- **pygments**: Syntax highlighting (>= 2.16.0)


### Development Dependencies

- **black**: Code formatting (>= 23.11.0)
- **flake8**: Code linting (>= 6.1.0)
- **pytest**: Unit testing (>= 7.4.3)
- **pytest-qt**: Qt testing (>= 4.2.0)
- **mypy**: Type checking (>= 1.7.0)
- **sphinx**: Documentation generation (>= 7.2.0)
- **sphinx-rtd-theme**: Read the Docs theme (>= 1.3.0)


### Optional Dependencies

- **opencv-python-headless**: Advanced image processing (>= 4.8.0)


## Installation


### Windows

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. Install required system dependencies:
   ```powershell
   winget install Git.Git
   ```
3. Clone the repository and install Python dependencies:
   ```powershell
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   pip install -r requirements.txt
   ```


### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3-pip python3-venv git
# For PyQt6
sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtsvg
# For QScintilla
sudo apt install pyqt6-dev-tools qttools6-dev-tools

# Clone and install
pip install -r requirements.txt
```


### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 git
brew install pyqt@6 qscintilla2

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```


## Logging

Logs are stored in `stl_to_gcode.log` in the application's root directory. For debugging purposes, you can view the log file using any text editor or the built-in log viewer.
