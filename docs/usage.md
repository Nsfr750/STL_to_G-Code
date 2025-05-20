# Usage Guide

## User Interface Overview

The application has a clean, modern interface with several main components:

### Main Window Layout

```
+------------------------+
|  Menu Bar             |
|-----------------------|
|  File List            |
|  +-----------------+  |
|  | Recent Files    |  |
|  +-----------------+  |
|  | Open File      |  |
|  | Convert        |  |
|  +-----------------+  |
|-----------------------|
|  3D Preview          |
|  +-----------------+  |
|  | 3D Model View  |  |
|  +-----------------+  |
|-----------------------|
|  Status Bar          |
+------------------------+
```

## Basic Operations

### Opening Files

1. Click "Open STL File" or use the File menu
2. Select your STL file
3. The model will appear in the 3D preview

### Converting to G-code

1. Open an STL file
2. Click "Convert to GCode"
3. Monitor progress in the status bar
4. Save the generated G-code file

## Navigation

### Menu Options

- **File**:
  - Open STL File
  - Exit

- **Help**:
  - Help (Documentation)
  - About
  - Sponsor

### Status Bar

The status bar shows:
- Current operation status
- Progress percentage
- Error messages

## Keyboard Shortcuts

- `Ctrl+O`: Open file
- `Ctrl+Q`: Quit application
- `F1`: Show help

## Troubleshooting

### Common Issues

1. **File Not Opening**
   - Check file permissions
   - Verify file format
   - Check error messages in status bar

2. **Conversion Fails**
   - Check model complexity
   - Verify STL file integrity
   - Check log file for details

3. **3D Preview Issues**
   - Ensure proper graphics drivers
   - Check system resources
   - Try different STL files

## Best Practices

1. **File Organization**
   - Keep STL files organized
   - Use descriptive filenames
   - Maintain a backup of original files

2. **Conversion Settings**
   - Adjust settings based on printer
   - Test with small files first
   - Save settings for reuse

3. **Error Handling**
   - Check status bar for messages
   - Review log files
   - Save work frequently
