# Development Guide

## Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development tools:
   ```bash
   pip install pytest pytest-cov black flake8
   ```

## Code Style and Formatting

- Use black for code formatting
- Follow PEP 8 style guidelines
- Use type hints where possible
- Write docstrings for all public methods

## Testing

### Running Tests

```bash
python -m pytest tests/ --cov=stl_to_gcode
```

### Test Coverage

```bash
coverage run -m pytest
coverage report
coverage html  # Generates HTML coverage report
```

## Building the Application

```bash
python setup.py sdist bdist_wheel
```

## Versioning

The project uses Semantic Versioning (SemVer). Version numbers follow the format:

- MAJOR.MINOR.PATCH
- Breaking changes: increment MAJOR
- New features: increment MINOR
- Bug fixes: increment PATCH

## Release Process

1. Update version number in `version.py`
2. Update CHANGELOG.md
3. Create a git tag:
   ```bash
   git tag v1.0.0
   git push --tags
   ```
4. Create a release on GitHub

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Update documentation
6. Submit a Pull Request

## Code Review Process

1. All changes require at least one approval
2. Tests must pass
3. Code must be formatted
4. Documentation must be updated
5. Changes must be backward compatible

## Security

### Reporting Security Issues

Please report security issues privately to the maintainers.

### Security Checklist

- Input validation
- Error handling
- File permissions
- Dependency security
- Logging security
