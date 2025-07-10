# Prerequisites

Before running the STL to GCode Converter, ensure that you have the following installed:


## System Requirements


### 🖥️ Hardware Requirements


#### Minimum

- **CPU**: Dual-core processor (2.0 GHz or faster)
- **RAM**: 4 GB
- **GPU**: Integrated graphics with OpenGL 3.3+ support
- **Storage**: 1 GB free space
- **Display**: 1280x720 resolution


#### Recommended

- **CPU**: Quad-core processor (3.0 GHz or faster)
- **RAM**: 8 GB or more
- **GPU**: Dedicated graphics card with OpenGL 4.5+ support (NVIDIA/AMD)
- **Storage**: 2 GB free space (SSD recommended)
- **Display**: 1920x1080 resolution or higher with 100% scaling


### 💻 Software Requirements


#### Operating Systems

- **Windows**: 10 or later (64-bit)
- **macOS**: 11.0 (Big Sur) or later (Apple Silicon or Intel)
- **Linux**: Ubuntu 22.04 LTS or later, Fedora 36+, or other modern distributions
  - Requires X11 or Wayland with OpenGL 3.3+ support
  - May require additional system packages (see below)


#### Python Requirements

- **Python**: 3.8 or later (3.10+ recommended)
- **pip**: 22.0 or later
- **Git**: For development and version control


## Required Python Libraries


### Core Dependencies

```bash
pip install -r requirements.txt
```


### Main Dependencies

- **PyQt6**: Modern GUI framework
- **numpy**: Numerical computing
- **numpy-stl**: STL file processing
- **matplotlib**: 3D visualization
- **trimesh**: Advanced 3D mesh processing
- **Pillow**: Image processing
- **requests**: HTTP requests
- **QScintilla**: Advanced text editor component
- **PyOpenGL**: 3D rendering acceleration
- **pyqt6-tools**: Additional Qt tools (development only)


### Optional Dependencies

- **PyQt6-Qt6**: Qt6 runtime (for standalone packaging)
- **PyQt6-sip**: Required for some PyQt6 functionality
- **pyinstaller**: For creating standalone executables


## Linux-Specific Requirements


### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    build-essential \
    libgl1-mesa-glx \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libxkbcommon-x11-dev
```


### Fedora

```bash
sudo dnf install -y \
    python3-devel \
    python3-pip \
    @development-tools \
    mesa-libGL \
    libxcb \
    libxkbcommon-x11 \
    libxkbcommon-x11-devel
```


## Windows Specific Notes

- Ensure you have the latest graphics drivers installed
- On systems with both integrated and dedicated GPUs, ensure the application uses the dedicated GPU
- For best performance, add the application to your GPU's high-performance applications list


## macOS Specific Notes

- Requires Xcode Command Line Tools
- May require additional permissions for camera/microphone access
- For M1/M2 Macs, use native ARM64 Python for best performance


## Development Dependencies

```bash
pip install -r requirements-dev.txt
```


## Verifying Installation

After installation, verify all dependencies are correctly installed by running:

```bash
python -c "from PyQt6.QtCore import QT_VERSION_STR; print(f'Qt version: {QT_VERSION_STR}')"
python -c "import numpy as np; print(f'numpy version: {np.__version__}')"
python -c "import matplotlib; print(f'matplotlib version: {matplotlib.__version__}')"
```


## Troubleshooting


### Common Issues

1. **OpenGL Errors**: Ensure your GPU drivers are up to date
2. **Missing Dependencies**: Check error messages and install any missing system packages
3. **Performance Issues**: Try disabling GPU acceleration in settings if experiencing performance problems
4. **Display Issues**: If UI elements appear incorrectly, try running with the `-style=Fusion` flag


### Getting Help

If you encounter any issues, please:

1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Search the [GitHub Issues](https://github.com/yourusername/STL_to_G-Code/issues)
3. Open a new issue if your problem hasn't been reported
