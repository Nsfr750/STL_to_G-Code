# Development Guide

## Setting Up Development Environment

### Prerequisites

- Python 3.8 or higher
- Git
- Qt development tools (for building PyQt6 from source if needed)

### 1. Clone the Repository

```bash
git clone https://github.com/Nsfr750/STL_to_G-Code.git
cd STL_to_G-Code
```

### 2. Create and Activate Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

## Code Style and Formatting

We use several tools to maintain code quality:

### Black (Code Formatter)
```bash
black .
```

### Flake8 (Linter)
```bash
flake8 .
```

### isort (Import Sorter)
```bash
isort .
```

### Pre-commit Hooks

We use pre-commit to automatically run code quality checks before each commit. Install it with:

```bash
pre-commit install
```

## Running Tests

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Test Coverage
```bash
pytest --cov=stl_to_gcode tests/
coverage html  # Generates HTML coverage report
```

## PyQt6 Development

### UI Development
- The application uses PyQt6 for the user interface
- UI files are in the `ui/` directory
- To edit UI files, use Qt Designer (included with PyQt6)

### Creating New Dialogs
1. Design the UI in Qt Designer
2. Save as `.ui` file in the `ui/` directory
3. Convert to Python code:
   ```bash
   pyuic6 ui/your_dialog.ui -o ui/your_dialog.py
   ```
4. Import and use in your code

### Signals and Slots

Example of connecting signals to slots:

```python
self.ui.pushButton.clicked.connect(self.on_button_clicked)

def on_button_clicked(self):
    # Handle button click
    pass
```

## Debugging

### Using the Log Viewer
- The application includes a built-in log viewer
- Use the `logging` module to add debug information
- Different log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Example logging:
```python
import logging

logging.debug("Detailed debug information")
logging.info("Informational message")
logging.warning("Warning message")
logging.error("Error message")
logging.critical("Critical error")
```

### Debugging with VSCode

1. Install the Python extension
2. Create a `.vscode/launch.json` file:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: STL to GCode",
            "type": "python",
            "request": "launch",
            "program": "main_qt.py",
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

## Building the Application

### Creating a Standalone Executable

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the application:
   ```bash
   pyinstaller --onefile --windowed --icon=assets/icon.ico main_qt.py
   ```

### Creating Installers

#### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico --name="STL to GCode" main_qt.py
```

#### macOS
```bash
pyinstaller --onefile --windowed --icon=assets/icon.icns --name="STL to GCode" main_qt.py
```

#### Linux
```bash
pyinstaller --onefile --windowed --icon=assets/icon.png --name="stl-to-gcode" main_qt.py
```

## Contributing

### Welcome to the STL to G-Code development guide!

This document will help you set up your development environment, understand the codebase structure, and contribute effectively.

### Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. Set up the development environment (see below)
4. Create a feature branch
5. Make your changes and test them
6. Submit a pull request

### Development Environment Setup

#### Prerequisites

- Python 3.8+
- Git
- pip (Python package manager)
- Virtual environment (recommended)

#### 1. Clone the Repository

```bash
git clone https://github.com/Nsfr750/STL_to_G-Code.git
cd STL_to_G-Code
```

#### 2. Set Up Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### Project Structure

```
STL_to_G-Code/
├── assets/             # Static assets (images, icons, etc.)
├── docs/               # Documentation files
├── scripts/            # Python modules
│   ├── __init__.py
│   ├── main.py         # Main application entry point
│   ├── config.py       # Configuration management
│   ├── language_manager.py  # Internationalization
│   └── ...
├── tests/              # Test files
├── .github/            # GitHub configuration
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt    # Production dependencies
```

### Testing

We use `pytest` for testing. To run the test suite:

```bash
pytest
```

Run tests with coverage report:

```bash
pytest --cov=scripts tests/
```

### Code Style

We enforce consistent code style using several tools:

#### Black (Code Formatter)
```bash
black .
```

#### Flake8 (Linter)
```bash
flake8 .
```

#### isort (Import Sorter)
```bash
isort .
```

#### Pre-commit Hooks

We use pre-commit to automatically run code quality checks before each commit. Install it with:

```bash
pre-commit install
```

The following checks will run automatically:
- Black code formatting
- Flake8 linting
- isort import sorting
- MyPy type checking

### Pull Request Guidelines

1. **Branch Naming**: Use descriptive branch names (e.g., `feature/add-logging` or `bugfix/fix-imports`)
2. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
3. **Code Review**: All PRs require at least one review
4. **Tests**: New features should include tests
5. **Documentation**: Update relevant documentation

### Internationalization (i18n)

#### Adding New Translations

1. Add new strings to `scripts/translations.py`
2. Update all language dictionaries
3. Use the translation system in your code:
   ```python
   from scripts.language_manager import get_language_manager
   _ = get_language_manager().translate
   
   # Usage
   message = _("your.translation.key")
   ```

#### Testing Translations

To test a specific language:

```python
from scripts.language_manager import get_language_manager
language_manager = get_language_manager()
language_manager.set_language("it")  # Test Italian
```

### Debugging

#### Logging

The application uses Python's built-in `logging` module. To enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### VS Code Debugging

A `.vscode/launch.json` configuration is provided for debugging in VS Code.

### Packaging and Distribution

#### Building the Package

```bash
python setup.py sdist bdist_wheel
```

#### Publishing to PyPI

1. Install build tools:
   ```bash
   pip install --upgrade build twine
   ```

2. Build the package:
   ```bash
   python -m build
   ```

3. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```

### Security

- Never commit sensitive information
- Validate all user inputs
- Use environment variables for secrets
- Keep dependencies up to date
- Follow security best practices for file operations

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

### License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

### Acknowledgments

- Thanks to all contributors
- Built with ❤️ using Python and PyQt6
- Inspired by the open-source 3D printing community

## Code Review Process

1. All pull requests require at least one approval
2. Code must pass all tests
3. Code must be formatted with Black and pass Flake8
4. New features should include tests
5. Update documentation as needed

## Release Process

1. Update `version.py` with the new version number
2. Update `CHANGELOG.md` with the changes
3. Create a new release on GitHub
4. Create a new tag with the version number
5. Build and upload the installers
6. Update the documentation

## Getting Help

- Check the [GitHub Issues](https://github.com/Nsfr750/STL_to_G-Code/issues)
- Join our [Discord community](https://discord.gg/your-invite-link)
- Read the [PyQt6 documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)

## Versioning

The project uses Semantic Versioning (SemVer). Version numbers follow the format:

- MAJOR.MINOR.PATCH
- Breaking changes: increment MAJOR
- New features: increment MINOR
- Bug fixes: increment PATCH

## Security

### Reporting Security Issues

Please report security issues privately to the maintainers.

### Security Checklist

- Input validation
- Error handling
- File permissions
- Dependency security
- Logging security
