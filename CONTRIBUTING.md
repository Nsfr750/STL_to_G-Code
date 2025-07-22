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
- pip 23.0 or later
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
   
   # On Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number-description
   ```

2. Make your changes following the code style guidelines below

3. Run tests to ensure nothing is broken:
   ```bash
   pytest
   ```

4. Format your code:
   ```bash
   black .
   ```

5. Check for linting errors:
   ```bash
   flake8 .
   ```

6. Commit your changes with a descriptive message:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # or
   git commit -m "fix: resolve issue with gcode generation"
   ```

## Pull Request Process

1. Push your changes to your fork:
   ```bash
   git push origin your-branch-name
   ```

2. Open a pull request against the `main` branch
3. Fill out the pull request template with all relevant information
4. Ensure all CI checks pass
5. Request a review from one of the maintainers
6. Address any review feedback
7. Once approved, your PR will be merged by a maintainer

## Reporting Issues

When reporting issues, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Screenshots if applicable
- Your operating system and Python version
- Any error messages or logs from `stl_to_gcode.log`

## Feature Requests

We welcome feature requests! Please:
1. Check if a similar feature already exists
2. Explain why this feature would be valuable
3. Provide as much detail as possible about the implementation

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Use [Google style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Keep lines under 88 characters (Black's default)
- Type hints are encouraged for all new code
- Use f-strings for string formatting (Python 3.6+)

## Testing

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a PR
- Use descriptive test function names (e.g., `test_function_name_expected_behavior`)
- Add integration tests for critical paths
- Update tests when changing functionality

## Documentation

- Update relevant documentation when adding new features
- Add docstrings to all public functions and classes
- Keep the README up to date
- Document any breaking changes in CHANGELOG.md

## License

By contributing, you agree that your contributions will be licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for details.
