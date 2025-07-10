# STL to GCode Converter Documentation

Welcome to the documentation for the STL to GCode Converter application, now powered by PyQt6!

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Features](#features)
- [User Interface](#user-interface)
- [Usage](#usage)
- [Development](#development)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The STL to GCode Converter is a modern Python application that converts STL (STereoLithography) files into G-code for 3D printing and CNC machining. The application features a responsive PyQt6-based graphical user interface with advanced visualization and debugging tools.

### What's New in PyQt6 Version

- **Modern UI**: Completely redesigned interface with PyQt6
- **Dark Theme**: Built-in dark theme with customizable styles
- **Dockable Panels**: Flexible workspace with resizable panels
- **Enhanced Logging**: Built-in log viewer with filtering
- **Improved Performance**: Faster rendering and processing
- **High DPI Support**: Better display on high-resolution screens

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PyQt6 and other dependencies (see [PREREQUISITES.md](../PREREQUISITES.md))

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   # source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main_qt.py
   ```

## Features

### Core Features
- Open and visualize STL files in 3D
- Convert STL models to G-code
- Interactive 3D preview with rotation and zoom
- Recent files history
- Automatic update checking

### Advanced Features
- Built-in G-code viewer with syntax highlighting
- Log viewer with filtering by log level
- Support for multiple 3D file formats
- Customizable interface with dockable panels
- High DPI display support

## User Interface

The application features a modern, tabbed interface with the following main components:

1. **Menu Bar**: Access to all application functions
2. **Toolbar**: Quick access to common actions
3. **File Browser**: Navigate and select STL files
4. **3D Preview**: Interactive 3D model visualization
5. **Log Viewer**: View and filter application logs
6. **Status Bar**: Displays current status and progress

## Usage

For detailed usage instructions, see the [Usage Guide](usage.md).

## Development

For information on setting up a development environment, running tests, and contributing to the project, see the [Development Guide](development.md).

## API Reference

For detailed API documentation, see the [API Reference](api.md).

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](../CONTRIBUTING.md) for details on how to contribute to this project.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For the full license text, see the [LICENSE](../LICENSE) file.
