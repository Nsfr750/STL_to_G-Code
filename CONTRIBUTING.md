# Contributing to STL to G-Code Converter

Thank you for your interest in contributing to the STL to G-Code Converter! We welcome contributions from everyone, whether you're a developer, designer, tester, or documentation writer.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [License](#license)

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report any unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a new branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Environment Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git
- (Optional) A Python virtual environment (recommended)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number-short-description
   ```

2. Make your changes following the code style guidelines
3. Add tests for your changes
4. Update documentation as needed
5. Run tests to ensure everything works

## Pull Request Process

1. Ensure all tests pass
2. Update the README.md with details of changes if needed
3. Increment the version number in any files that need it
4. Submit the pull request with a clear title and description
5. Reference any related issues in your PR description
6. Wait for code review and address any feedback

## Reporting Issues

When reporting issues, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Any error messages or logs
- Screenshots if applicable

## Feature Requests

For feature requests, please:
1. Check if a similar feature request already exists
2. Describe the feature and why it would be useful
3. Include any relevant use cases

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for all function parameters and return values
- Keep lines under 100 characters when possible
- Use docstrings for all public modules, classes, and functions
- Write clear, concise commit messages

## Testing

- Write unit tests for new features and bug fixes
- Run all tests before submitting a PR:
  ```bash
  pytest
  ```
- Ensure test coverage doesn't decrease
- Add integration tests for complex features

## Documentation

- Update the README.md with any changes to the setup or usage
- Add docstrings to all new functions and classes
- Update any relevant documentation in the `docs/` directory
- Keep comments clear and up-to-date

## License

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file.
