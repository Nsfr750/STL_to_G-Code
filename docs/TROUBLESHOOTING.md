# Troubleshooting Guide

This document provides solutions to common issues you might encounter while using the STL to G-Code Converter.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Visualization Problems](#visualization-problems)
- [G-Code Generation Issues](#g-code-generation-issues)
- [Performance Problems](#performance-problems)
- [Common Error Messages](#common-error-messages)
- [Getting Help](#getting-help)

## Installation Issues

### Python Version Compatibility
- **Problem**: The application fails to start with Python version errors.
- **Solution**: Ensure you're using Python 3.8 or higher. Check your Python version:
  ```bash
  python --version
  ```
  If needed, download the latest version from [python.org](https://www.python.org/downloads/).

### Missing Dependencies
- **Problem**: Errors about missing Python packages during installation.
- **Solution**: Install all required dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### OpenGL Issues
- **Problem**: OpenGL visualization fails to initialize.
- **Solution**:
  1. Update your graphics drivers
  2. Install system OpenGL libraries:
     - **Windows**: Install the latest drivers from your GPU manufacturer
     - **Ubuntu/Debian**: `sudo apt-get install libgl1-mesa-glx`
     - **macOS**: Should be pre-installed
  3. The application will automatically fall back to matplotlib if OpenGL is not available

## Runtime Errors

### "Module Not Found" Errors
- **Problem**: Errors about missing modules when starting the application.
- **Solution**:
  ```bash
  # Activate your virtual environment if using one
  pip install -r requirements.txt
  ```

### "DLL Load Failed" on Windows
- **Problem**: Errors about DLL loading failures, often related to Qt or OpenGL.
- **Solution**:
  1. Install the latest Visual C++ Redistributable
  2. Update your graphics drivers
  3. Reinstall PyQt6:
     ```bash
     pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
     pip install PyQt6
     ```

## Visualization Problems

### Blank or Black Screen
- **Problem**: The 3D view shows a blank or black screen.
- **Solution**:
  1. Check if OpenGL is supported on your system
  2. Try using the software renderer:
     - Set the environment variable: `QT_QUICK_BACKEND=software`
  3. The application should automatically fall back to matplotlib if OpenGL fails

### Slow or Choppy Rendering
- **Problem**: The 3D view is slow or choppy.
- **Solution**:
  1. Reduce the STL resolution if possible
  2. Close other graphics-intensive applications
  3. Update your graphics drivers
  4. Try using the software renderer (see above)

## G-Code Generation Issues

### Empty G-Code Output
- **Problem**: The generated G-code file is empty.
- **Solution**:
  1. Check if the STL file is valid
  2. Verify that the STL contains valid 3D geometry
  3. Check the application logs for any error messages

### Incorrect Toolpaths
- **Problem**: The generated G-code doesn't match the expected toolpaths.
- **Solution**:
  1. Check your slicing parameters
  2. Verify the STL file is watertight and manifold
  3. Ensure the printer settings match your hardware

## Performance Problems

### Slow STL Loading
- **Problem**: Large STL files take too long to load.
- **Solution**:
  1. Use the progressive loading feature
  2. Reduce the STL resolution if possible
  3. Close other memory-intensive applications

### High CPU/Memory Usage
- **Problem**: The application uses too many system resources.
- **Solution**:
  1. Reduce the STL complexity
  2. Lower the visualization quality in settings
  3. Close other unnecessary applications

## Common Error Messages

### "Failed to initialize OpenGL"
- **Cause**: OpenGL is not properly installed or supported.
- **Solution**: The application will automatically fall back to matplotlib. For OpenGL support, update your graphics drivers.

### "STL file is not valid"
- **Cause**: The STL file is corrupted or in an unsupported format.
- **Solution**:
  1. Verify the STL file opens in other viewers
  2. Try exporting the STL again from your CAD software
  3. Check that the file is in binary STL format

### "Out of Memory"
- **Cause**: The STL file is too large for your system's memory.
- **Solution**:
  1. Use a smaller STL file
  2. Increase your system's virtual memory
  3. Close other memory-intensive applications

## Getting Help

If you encounter an issue not covered in this guide:

1. Check the [GitHub Issues](https://github.com/Nsfr750/STL_to_G-Code/issues) for similar problems
2. Search the project's documentation
3. If you can't find a solution, open a new issue with:
   - A clear description of the problem
   - Steps to reproduce the issue
   - Error messages (if any)
   - Your system information (OS, Python version, etc.)
   - Any relevant screenshots or files

## System Requirements

- **OS**: Windows 10/11, macOS 10.15+, or Linux with X11/Wayland
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB+ recommended for large models
- **Graphics**: OpenGL 3.3+ capable GPU recommended

## Known Issues

- On some Linux systems, you might need to install additional Qt platform plugins
- Very large STL files (>100MB) may cause performance issues on lower-end systems
- Some complex STL files with non-manifold edges might not render correctly

---
*Last updated: July 2025*
