# STL to GCode Converter

A powerful Python application for converting STL files to G-code, designed for 3D printing and CNC machining. The application features a modern GUI built with Tkinter, numpy-stl for STL file processing, and matplotlib for high-quality 3D visualization.

## Key Features

### File Management
- Open and manage STL files
- Recent files menu for quick access
- Persistent file history tracking
- File list display with status
- Support for multiple file formats

### 3D Visualization
- Interactive 3D preview with rotation and zoom
- Auto-scaling to fit models
- High-quality rendering with shading
- Real-time model updates
- Multiple view angles

### G-code Viewer
- Syntax-highlighted G-code viewing
- Line numbers and current line indicator
- Search functionality
- Read-only view with scroll support
- Status bar showing line and character counts

### G-code Conversion
- Efficient STL to G-code conversion
- Progress tracking with visual feedback
- Real-time status updates
- Configurable conversion settings
- Error handling and validation

### User Interface
- Modern, clean ttk-themed interface
- Organized layout with left panel controls
- Progress bar for operations
- Status bar with operation status
- Responsive design

### Menu System
- File menu with Open, View G-code, and Exit options
- Help menu with comprehensive documentation
- About dialog with version info
- Sponsor options for project support
- Recent files menu

## Installation

### Requirements
- Python 3.8 or higher
- Required Python packages:
  - numpy (>=1.24.0)
  - stl (>=0.1.0)
  - trimesh (>=3.22.0)
  - matplotlib (>=3.7.0)
  - pillow (>=10.0.0)

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage Guide

### Basic Workflow
1. Launch the application
2. Use the "Open STL File" button or File menu to select an STL file
3. The model will appear in the 3D preview area
4. The "Convert to GCode" button will become enabled
5. Click "Convert to GCode" to start the conversion process
6. Monitor progress in the status bar and progress bar
7. Once complete, save the G-code file
8. Use the G-code viewer to inspect the generated code

### File Operations
- Access recent files through the "Recent Files" menu
- View file history in the left panel
- Save G-code files with custom naming
- Open multiple files for comparison

### Configuration
The application maintains persistent settings:
- Last opened directory
- Recent files list
- G-code conversion settings
- Window size and position
- Theme preferences

## Error Handling & Logging

The application includes comprehensive error handling:
- Detailed error messages
- Operation status tracking
- Automatic logging to `stl_to_gcode.log`
- Error recovery mechanisms
- User-friendly error notifications

## Support & Community

### Getting Help
- Check the [Changelog](./CHANGELOG.md) for recent updates
- View the [License](./LICENSE) for usage rights
- Report issues on the [GitHub repository](https://github.com/Nsfr750/STL_to_G-Code)
- Join our Discord for support

### Sponsorship Options
- [GitHub Sponsors](https://github.com/sponsors/Nsfr750)
- [Patreon](https://www.patreon.com/Nsfr750)
- [Discord](https://discord.gg/BvvkUEP9)
- [PayPal](https://paypal.me/3dmega)

### Community
Join our active community:
- [Discord](https://discord.gg/BvvkUEP9)
- [GitHub Discussions](https://github.com/Nsfr750/STL_to_G-Code/discussions)
- Feature requests and bug reports
- User feedback and suggestions

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

- Thanks to the Python community for open-source libraries
- Special thanks to contributors and users
- Inspired by open-source 3D printing and CNC projects

To run the application, execute:

```bash
python main.py
```

This will launch the STL to GCode Converter GUI.
