# User Guide

## Interface Overview

The STL to GCode Converter features a modern, tabbed interface with the following main components:

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

## Basic Workflow

### 1. Opening an STL File

1. **Using the Menu**:
   - Click `File > Open STL`
   - Navigate to your STL file and click `Open`

2. **Drag and Drop**:
   - Simply drag an STL file from your file explorer and drop it onto the application window

3. **Recent Files**:
   - Click `File > Recent Files` to quickly access previously opened files

### 2. Viewing the 3D Model

- **Rotate**: Click and drag with the left mouse button
- **Pan**: Click and drag with the right mouse button
- **Zoom**: Use the mouse wheel or pinch gesture on touchpads
- **Reset View**: Click the `Home` button in the toolbar

### 3. Converting to G-code

1. Open an STL file
2. Click `Tools > Convert to GCode` or press `Ctrl+G`
3. Adjust conversion settings if needed
4. Click `Convert` to start the process
5. Monitor progress in the status bar

### 4. Viewing and Saving G-code

- The G-code viewer will automatically open after conversion
- Use the toolbar to navigate the G-code
- Click `File > Save GCode` to save the generated G-code
- Use `File > Save As...` to save with a different name or location

## Advanced Features

### Log Viewer

The log viewer at the bottom of the window shows detailed information about application operations:

- Use the filter dropdown to show only specific log levels
- Click the `Clear` button to clear the log
- Right-click on log entries for additional options

### Customizing the Interface

- **Dockable Panels**: Drag panels by their title bars to rearrange them
- **Themes**: Change between light and dark themes in `View > Theme`
- **Toolbars**: Show/hide toolbars via `View > Toolbars`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open STL file |
| `Ctrl+S` | Save G-code |
| `Ctrl+G` | Convert to G-code |
| `F1` | Show help |
| `F5` | Refresh 3D view |
| `Esc` | Cancel current operation |
| `Ctrl+Q` | Quit application |

## Troubleshooting

### Common Issues

#### 3D Model Not Displaying
- Ensure the file is a valid STL file
- Check the log viewer for any error messages
- Try zooming out (`Ctrl+-` or mouse wheel)

#### Conversion Fails
- Check that the model is manifold (watertight)
- Verify that the model is not too large or complex
- Check the log viewer for specific error messages

#### Performance Issues
- Close other applications to free up memory
- Reduce the model resolution if possible
- Update your graphics drivers

## Getting Help

For additional assistance:

1. Check the `Help > Documentation` menu
2. Visit the [GitHub Issues](https://github.com/Nsfr750/STL_to_G-Code/issues) page
3. Join our [Discord community](https://discord.gg/your-invite-link) for support

## Reporting Issues

When reporting issues, please include:

1. Steps to reproduce the issue
2. The STL file (if applicable)
3. Any error messages from the log viewer
4. Your system information (Help > About)

## Tips and Tricks

- Use `Ctrl+Mouse Wheel` to adjust the movement sensitivity
- Right-click on the 3D view for additional camera controls
- The status bar shows useful information about the current operation
- Press `F2` to rename the current file
