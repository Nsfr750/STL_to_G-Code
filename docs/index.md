# STL to GCode Converter

![STL to GCode Logo](https://raw.githubusercontent.com/Nsfr750/STL_to_G-Code/main/assets/icon.png)

A powerful, open-source application for converting STL files to G-code for 3D printing and CNC machining, featuring a modern PyQt6 interface.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![PyPI Version](https://img.shields.io/pypi/v/stl-to-gcode)](https://pypi.org/project/stl-to-gcode/)

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [User Guide](#-user-guide)
- [Development](#-development)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## ✨ Features

- **Modern PyQt6 Interface** - Clean, responsive UI with dark/light themes
- **Advanced 3D Visualization** - Interactive model manipulation and preview
- **Multi-language Support** - Built-in internationalization
- **G-code Optimization** - Advanced algorithms for efficient toolpaths
- **Plugin System** - Extend functionality with custom plugins
- **Cross-platform** - Works on Windows, macOS, and Linux
- **Logging & Debugging** - Built-in log viewer and debugging tools

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for development)

### Using pip (Recommended)

```bash
pip install stl-to-gcode
```

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🏃 Quick Start

1. Launch the application:
   ```bash
   python main.py
   ```

2. Open an STL file using `File > Open` or by dragging and dropping

3. Adjust settings as needed in the right panel

4. Click `Generate G-code` to convert your model

5. Save the G-code or send it directly to your 3D printer

## 📖 User Guide

For detailed usage instructions, see the [User Guide](usage.md).

## 🛠 Development

Interested in contributing? Check out our [Development Guide](development.md) for setup instructions and coding standards.

## 📚 API Reference

For developers looking to extend the application, see the [API Reference](api.md).

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, or suggest new features.

## 📄 License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- **Documentation**: [GitHub Wiki](https://github.com/Nsfr750/STL_to_G-Code/wiki)
- **Issues**: [GitHub Issues](https://github.com/Nsfr750/STL_to_G-Code/issues)
- **Discord**: [Join our community](https://discord.gg/BvvkUEP9)

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/Nsfr750">Nsfr750</a>
  <br>
  <a href="https://www.patreon.com/Nsfr750">Support on Patreon</a> | 
  <a href="https://paypal.me/3dmega">Donate via PayPal</a>
</div>
