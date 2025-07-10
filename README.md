# STL to GCode Converter

A powerful Python application for converting STL files to G-code, designed for 3D printing and CNC machining. The application features a modern GUI built with **PyQt6**, numpy-stl for STL file processing, and matplotlib for high-quality 3D visualization.

![Screenshot of the Application](assets/screenshot.png)


## 🚀 Key Features


### 🖥️ Modern User Interface

- Built with PyQt6 for a native look and feel
- Dark theme with customizable styles
- Dockable panels for flexible workspace
- Responsive design that works on different screen sizes
- High DPI display support
- Comprehensive keyboard shortcuts


### 📚 Documentation

- Built-in markdown documentation viewer
- Accessible via Help menu or F1 key
- Support for multiple documentation files
- Syntax highlighting for code examples
- Table of contents navigation


### 📂 File Management

- Open and manage STL files
- Recent files menu for quick access
- File list display with status
- Support for multiple file formats
- Drag and drop support
- Auto-save functionality


### 🔍 3D Visualization & Simulation

- Interactive 3D preview with rotation and zoom
- G-code simulation with toolpath visualization
- Real-time simulation controls (play/pause/stop)
- Layer-by-layer simulation
- Simulation speed control
- Auto-scaling to fit models
- High-quality rendering with shading
- Multiple view angles
- Matplotlib integration with custom toolbar


### 📝 G-code Tools

- Built-in G-code viewer with syntax highlighting
- Line numbers and current line indicator
- Search functionality
- Advanced G-code validation with real-time feedback
- G-code simulation with 3D visualization
- Export G-code to file
- Support for custom start/end G-code


### 🛠️ G-code Validation

- Real-time syntax checking
- Printer compatibility validation
- Safety checks (temperature, feedrate, etc.)
- Visual error highlighting in editor
- Detailed error messages with suggestions
- Warning system for potential issues
- Customizable validation rules


### 📊 Advanced Features

- Comprehensive logging system with real-time updates
- Log viewer with filtering by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Automatic update checking
- Plugin system for extending functionality
- Customizable keyboard shortcuts
- Multi-language support


### 🚀 Performance Features

- Background processing for large files
- Incremental loading of large STL and G-code files
- Memory-efficient processing
- GPU-accelerated rendering (OpenGL)
- Progressive loading for better responsiveness


## 📦 Installation


### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for development)


### Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Linux/Mac
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:

   ```bash
   python main.py
   ```


## 🛠 Usage

1. **Open an STL file** using File > Open or drag and drop
2. **Adjust settings** in the right panel
3. **Preview** the 3D model
4. **Generate G-code** using the toolbar button
5. **Save** or **export** the G-code


## 📖 Documentation

Comprehensive documentation is available within the application. Press F1 or go to Help > Documentation to access it.


## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started.


## 📄 License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.


## 📬 Contact

For questions or feedback, please open an issue on GitHub or contact the maintainers.


## 🙏 Acknowledgments

- Thanks to all contributors who have helped improve this project
- Built with ❤️ using Python, PyQt6, and other amazing open-source libraries
