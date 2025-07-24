# 📖 User Guide

## Table of Contents
- [Interface Overview](#-interface-overview)
- [Basic Workflow](#-basic-workflow)
- [Advanced Features](#-advanced-features)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-frequently-asked-questions)

## 🖥️ Interface Overview

The STL to GCode Converter features a modern, dockable interface that can be customized to your workflow:

```
+---------------------------------------------------+
|  Menu Bar                                        |
|--------------------------------------------------|
|  +-------------------+  +---------------------+  |
|  |                   |  |                     |  |
|  |   3D Preview      |  |    G-code Viewer    |  |
|  |                   |  |                     |  |
|  |                   |  |                     |  |
|  +-------------------+  +---------------------+  |
|  |                                                 |
|  |                  Log Viewer                    |
|  |                                                 |
|  +-------------------------------------------------+
|  | Status Bar | Progress | Memory Usage | FPS      |
+---------------------------------------------------+
```

### Main Components

1. **Menu Bar**
   - Access all application functions
   - Configure settings and preferences
   - Access help and documentation

2. **Toolbar**
   - Quick access to frequently used functions
   - Model manipulation tools
   - View controls

3. **3D Preview**
   - Interactive 3D model visualization
   - Real-time rendering with OpenGL
   - Multiple view modes (solid, wireframe, etc.)

4. **G-code Viewer**
   - Syntax-highlighted G-code display
   - Line-by-line execution preview
   - Error highlighting and validation

5. **Log Viewer**
   - Real-time application logging
   - Filter by log level (Debug, Info, Warning, Error)
   - Search and highlight functionality

## 🚀 Basic Workflow

### 1. Opening an STL File

#### Methods:
- **Menu**: `File > Open STL`
- **Toolbar**: Click the 'Open' icon
- **Drag & Drop**: Drag an STL file into the application window
- **Recent Files**: `File > Recent Files`

#### Supported Formats:
- STL (.stl)
- OBJ (.obj) - Basic support
- 3MF (.3mf) - Experimental

### 2. Viewing and Manipulating the 3D Model

#### Navigation:
- **Rotate**: Left-click + drag
- **Pan**: Right-click + drag or Middle-click + drag
- **Zoom**: Scroll wheel or pinch gesture
- **Reset View**: Click the 'Home' button or press `Home` key

#### View Modes:
- **Solid**: Filled polygons (default)
- **Wireframe**: Show model edges only
- **Point Cloud**: Show vertices only
- **X-Ray**: Semi-transparent view

### 3. Converting to G-code

1. **Set Up Print Parameters**
   - Layer height
   - Print speed
   - Infill density
   - Support structures

2. **Generate G-code**
   - Click `Tools > Generate G-code` or press `Ctrl+G`
   - Monitor progress in the status bar
   - Preview the generated toolpaths

3. **Save or Export**
   - Save G-code to file (`File > Save G-code`)
   - Export settings as profile
   - Send directly to printer (if configured)

## ⚙️ Advanced Features

### Custom Profiles
- Save and load printer profiles
- Import/export settings
- Create material-specific configurations

### G-code Optimization
- Travel optimization
- Retraction settings
- Cooling strategies

### Scripting
- Custom start/end G-code
- Post-processing scripts
- Automation support

## ⌨️ Keyboard Shortcuts

### Navigation
| Shortcut | Action |
|----------|--------|
| `R` | Reset view |
| `F` | Fit model to view |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |

### File Operations
| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open STL file |
| `Ctrl+S` | Save G-code |
| `Ctrl+Shift+S` | Save As... |
| `Ctrl+Q` | Quit application |

### View Controls
| Shortcut | Action |
|----------|--------|
| `1` | Front view |
| `3` | Side view |
| `7` | Top view |
| `5` | Toggle perspective/orthographic |
| `Space` | Toggle rotation |

## 🛠 Troubleshooting

### Common Issues

#### Model Won't Load
- Verify the file is not corrupted
- Check that the file format is supported
- Try simplifying the model in a 3D modeling program

#### G-code Generation Fails
- Check log for specific error messages
- Verify print settings are valid
- Ensure the model is manifold (watertight)

#### Performance Issues
- Reduce model complexity
- Lower preview quality in settings
- Close other resource-intensive applications

## ❓ Frequently Asked Questions

### How do I update the application?
Check for updates in `Help > Check for Updates` or visit the [GitHub repository](https://github.com/Nsfr750/STL_to_G-Code).

### Can I use custom post-processing scripts?
Yes! Place your Python scripts in the `scripts/post_processing` directory and they'll appear in the post-processing menu.

### How do I report a bug?
Please open an issue on [GitHub](https://github.com/Nsfr750/STL_to_G-Code/issues) with detailed steps to reproduce the problem.

### Is there a command-line interface?
Yes! Run `python main.py --help` to see available command-line options.

---

For additional help, please visit our [GitHub Discussions](https://github.com/Nsfr750/STL_to_G-Code/discussions) or join our [Discord community](https://discord.gg/BvvkUEP9).
