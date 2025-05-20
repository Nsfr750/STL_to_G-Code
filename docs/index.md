# STL to GCode Converter Documentation

Welcome to the documentation for the STL to GCode Converter application.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Features](#features)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The STL to GCode Converter is a Python application that converts STL (STereoLithography) files into G-code for 3D printing and CNC machining. It provides a graphical user interface (GUI) for easy file manipulation and conversion.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required dependencies (see [requirements.txt](../../requirements.txt))

### Installation

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

## Features

- Open and visualize STL files
- Convert STL files to G-code
- Recent files menu
- File history tracking
- Progress tracking during conversions
- Modern UI with ttk widgets
- Error handling and logging
- Sponsorship options

## Usage

### Opening Files

1. Click "Open STL File" or use the File menu
2. Select your STL file from the file dialog
3. The model will appear in the 3D preview area

### Converting to G-code

1. Open an STL file
2. Click "Convert to GCode"
3. Monitor progress in the status bar
4. Save the generated G-code file

## Configuration

The application maintains configuration settings in `~/.stl_to_gcode/config.json`:

- Last opened directory
- Recent files list
- G-code conversion settings
- Window size and position

## Development

### Project Structure

```
STL_to_G-Code/
├── main.py              # Main application
├── config.py           # Configuration management
├── help.py             # Help documentation
├── about.py            # About dialog
├── sponsor.py          # Sponsor dialog
├── version.py          # Version management
├── requirements.txt    # Dependencies
├── setup.py           # Package setup
└── docs/              # Documentation
```

### Running Tests

To run tests:
```bash
python -m pytest tests/
```

## API Reference

### Main Application

```python
from main import STLToGCodeApp

app = STLToGCodeApp(root)
```

### Configuration

```python
from config import config

# Get configuration value
value = config.get('key')

# Set configuration value
config.set('key', value)
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
