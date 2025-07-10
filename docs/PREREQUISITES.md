# Prerequisites

Before running the STL to GCode Converter, ensure that you have the following installed:

## System Requirements

### 🖥️ Hardware Requirements

#### Minimum
- **CPU**: Dual-core processor (2.0 GHz or faster)
- **RAM**: 4 GB
- **GPU**: Integrated graphics with OpenGL 2.0 support
- **Storage**: 500 MB free space
- **Display**: 1280x720 resolution

#### Recommended
- **CPU**: Quad-core processor (3.0 GHz or faster)
- **RAM**: 8 GB or more
- **GPU**: Dedicated graphics card with OpenGL 3.3+ support
- **Storage**: 1 GB free space (SSD recommended)
- **Display**: 1920x1080 resolution or higher

### 💻 Software Requirements

#### Operating Systems
- **Windows**: 10 or later (64-bit)
- **macOS**: 10.15 (Catalina) or later
- **Linux**: Ubuntu 20.04 LTS or later, Fedora 32+, or other modern distributions
  - Requires X11 or Wayland with OpenGL support
  - May require additional system packages (see below)

#### Python Requirements
- **Python**: 3.8 or later (3.10+ recommended)
- **pip**: Latest version

## Required Python Libraries

Install the required libraries using pip:

```bash
pip install -r requirements.txt
```

Or install the core dependencies manually:

```bash
pip install numpy-stl matplotlib numpy-stl trimesh pillow requests PyQt6
```

## Installation Instructions

### 1. Install System Dependencies

#### Windows
- Install the latest Windows updates
- Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

#### macOS
- Install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```
- Install Homebrew (if not already installed):
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv libgl1-mesa-glx
```

### 2. Set Up Python Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/stl_to_gcode.git
   cd stl_to_gcode
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Upgrade pip and setuptools:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Activate the virtual environment (if not already activated):
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. Run the application:
   ```bash
   python main_qt.py
   ```

## Troubleshooting

### Common Issues

#### PyQt6 Installation Issues
```bash
# If you encounter PyQt6 installation issues, try:
pip install --upgrade pip
pip install PyQt6 --no-cache-dir
```

#### Missing OpenGL Support
- On Linux, install the appropriate OpenGL libraries:
  ```bash
  # Ubuntu/Debian
  sudo apt install -y libgl1-mesa-glx libxcb-xinerama0
  
  # Fedora
  sudo dnf install -y mesa-libGL libxcb xcb-util
  ```

#### High DPI Display Issues
If the UI appears too small on high DPI displays, set the following environment variable before launching:
```bash
# Windows
set QT_SCALE_FACTOR=1.5

# macOS/Linux
export QT_SCALE_FACTOR=1.5

# Then run the application
python main_qt.py
```

## Additional Notes

- For development, install the development dependencies:
  ```bash
  pip install -r requirements-dev.txt
  ```

- To build a standalone executable, install PyInstaller:
  ```bash
  pip install pyinstaller
  pyinstaller --onefile --windowed --icon=assets/icon.ico main_qt.py
  ```

- For optimal performance with large STL files, ensure you have sufficient RAM and consider using an SSD.

- For issues with STL visualization, ensure that your `matplotlib` version is up to date (`>=3.7.0`).
- If you encounter any issues with the STL library, ensure you have the correct package installed:
  ```bash
  pip uninstall stl  # If installed
  pip install numpy-stl  # Install the correct package
  ```
- If the application fails to open, verify that you have installed all the required libraries.
