# STL to GCode Converter

This is a Python application with a graphical user interface (GUI) for opening STL files, visualizing them, and converting them to G-code. The application leverages `Tkinter` for the GUI, `numpy-stl` for handling STL files, and `matplotlib` for 3D visualization.

## Features

- **File Management**:
  - Open STL files from your system
  - Recent files menu for quick access
  - File history tracking
  - File list display

- **3D Visualization**:
  - Interactive 3D preview of STL models
  - Auto-scaling to fit the model
  - Improved 3D rendering quality

- **G-code Viewer**:
  - View generated G-code files
  - Syntax highlighting for G-code commands
  - Line numbers and current line indicator
  - Read-only view with scroll support

- **G-code Conversion**:
  - Convert STL files to G-code
  - Progress tracking during conversion
  - Status updates in real-time

- **UI Improvements**:
  - Modern, clean interface using ttk widgets
  - Organized layout with left panel controls
  - Progress bar for operations
  - Status bar for operation status

- **Menu Options**:
  - File menu with Open, View G-code, and Exit options
  - Help menu with documentation
  - About dialog with version info
  - Sponsor options for project support

## Screenshots

*Coming soon...*

## How to Use

1. Launch the application
2. Use the "Open STL File" button or File menu to select an STL file
3. The model will appear in the 3D preview area
4. The "Convert to GCode" button will become enabled
5. Click "Convert to GCode" to start the conversion process
6. Monitor progress in the status bar and progress bar
7. Once complete, save the G-code file

## Recent Files
Access your recently opened files through the "Recent Files" menu

## Configuration
The application maintains persistent settings including:
- Last opened directory
- Recent files list
- G-code conversion settings
- Window size and position

## Error Handling
The application includes improved error handling with:
- Detailed error messages
- Operation status tracking
- Automatic logging to `stl_to_gcode.log`

## License

This project is licensed under the [MIT License](./LICENSE).

## Support

### Getting Help
- Check the [Changelog](./CHANGELOG.md) for recent updates
- View the [License](./LICENSE) for usage rights
- Report issues on the [GitHub repository](https://github.com/Nsfr750/STL_to_G-Code)

### Sponsorship Options
- [GitHub Sponsors](https://github.com/sponsors/Nsfr750)
- [Patreon](https://www.patreon.com/Nsfr750)
- [Discord](https://discord.gg/BvvkUEP9)
- [PayPal](https://paypal.me/3dmega)

### Community
Join our community on:
- [Discord](https://discord.gg/BvvkUEP9)
- [GitHub Discussions](https://github.com/Nsfr750/STL_to_G-Code/discussions)

## Social Links

- [GitHub](https://github.com/sponsors/Nsfr750)
- [Patreon](https://www.patreon.com/Nsfr750)
- [Discord](https://discord.gg/BvvkUEP9)
- [Paypal](https://paypal.me/3dmega)

## Running the Application

To run the application, execute:

```bash
python main.py
```

This will launch the STL to GCode Converter GUI.
