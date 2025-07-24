# Prerequisites

This document outlines the system requirements and setup instructions for the STL to GCode Converter.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **CPU**: Dual-core processor, 2.0 GHz or faster
- **RAM**: 4 GB minimum (8 GB recommended for large models)
- **GPU**: OpenGL 3.3 compatible graphics card (discrete GPU recommended for better 3D rendering)
- **Disk Space**: 500 MB free space
- **Display**: 1366x768 resolution minimum (1920x1080 recommended)

### Development Requirements
- **Python**: 3.8 or higher
- **pip**: Latest version
- **Git**: For version control
- **C++ Build Tools**: Required for some Python packages
  - Windows: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  - macOS: Xcode Command Line Tools (`xcode-select --install`)
  - Linux: `build-essential` package

## Python Environment Setup

We recommend using a virtual environment to manage dependencies. Here's how to set it up:

### Windows
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### macOS/Linux
```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Development Tools

### Recommended IDEs
- [Visual Studio Code](https://code.visualstudio.com/) with Python extension
- [PyCharm](https://www.jetbrains.com/pycharm/)
- [Spyder](https://www.spyder-ide.org/)

### Useful Extensions
- Python (Microsoft)
- Pylance
- Python Docstring Generator
- GitLens
- Python Test Explorer

## Building from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Set up the development environment (see above)

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Troubleshooting

### Common Issues

#### Missing Dependencies
If you encounter errors about missing dependencies, try:
```bash
pip install -r requirements.txt --force-reinstall
```

#### PyQt6 Installation Issues
On some Linux distributions, you might need to install additional system packages:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt6 python3-pyqt6.qtwebengine

# Fedora
sudo dnf install python3-qt6 python3-qt6-qtwebengine
```

#### OpenGL Issues
If you experience issues with 3D rendering:
- Update your graphics drivers
- Try running with software rendering:
  ```bash
  python main.py --disable-gpu
  ```

## Getting Help

If you encounter any issues during setup, please:
1. Check the [Troubleshooting](#troubleshooting) section
2. Search the [GitHub Issues](https://github.com/Nsfr750/STL_to_G-Code/issues)
3. If your issue isn't listed, open a new issue with details about your problem
