# Contributing to STL to GCode Converter

Thank you for your interest in contributing to the STL to GCode Converter! We welcome contributions from everyone, whether you're a developer, designer, tester, or just someone with ideas.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Workflow](#-development-workflow)
- [Code Style](#-code-style)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Submitting Changes](#-submitting-changes)
- [Reporting Issues](#-reporting-issues)
- [Feature Requests](#-feature-requests)
- [Community](#-community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report any unacceptable behavior to the project maintainers.

## 🚀 Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
   ```bash
   git clone https://github.com/Nsfr750/STL_to_G-Code.git
   cd STL_to_G-Code
   ```
3. **Set up** the development environment (see [PREREQUISITES.md](PREREQUISITES.md))
4. **Create a branch** for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🔄 Development Workflow

1. **Sync** your fork with the main repository
   ```bash
   git remote add upstream https://github.com/Nsfr750/STL_to_G-Code.git
   git fetch upstream
   git merge upstream/main
   ```

2. **Make your changes** following the code style guidelines

3. **Run tests** to ensure everything works
   ```bash
   pytest tests/
   ```

4. **Commit your changes** with a descriptive message
   ```bash
   git commit -m "Add your detailed description here"
   ```

5. **Push** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** against the `main` branch

## 🎨 Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
  ```bash
  black .
  ```
  
- **Flake8** for linting
  ```bash
  flake8 .
  ```
  
- **mypy** for type checking
  ```bash
  mypy .
  ```

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public functions, classes, and modules following [Google style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
- Keep lines under 100 characters

## 🧪 Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting a PR
- Use descriptive test function names (e.g., `test_function_name_does_what`)
- Group related tests in classes when appropriate

## 📝 Documentation

- Update documentation when adding new features or changing behavior
- Keep docstrings up to date
- Add examples for complex functionality
- Document any breaking changes in the [CHANGELOG.md](CHANGELOG.md)

## 🔄 Submitting Changes

1. Ensure your branch is up to date with the latest changes from `main`
2. Run all tests and ensure they pass
3. Update documentation if needed
4. Push your changes to your fork
5. Open a Pull Request with a clear title and description
   - Reference any related issues
   - Describe your changes and the reasoning behind them
   - Include screenshots or screen recordings for UI changes

## 🐛 Reporting Issues

When reporting bugs, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Screenshots or screen recordings if applicable
5. Your operating system and Python version
6. Any error messages or logs

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if a similar feature request already exists
2. Describe the feature and why it would be useful
3. Provide examples of how it would work
4. Consider contributing the feature yourself if possible

## 🌍 Community

Join our community to get help, discuss features, and contribute:

- [Discord Server](https://discord.gg/BvvkUEP9)
- [GitHub Discussions](https://github.com/Nsfr750/STL_to_G-Code/discussions)
- [GitHub Issues](https://github.com/Nsfr750/STL_to_G-Code/issues)

## 🙏 Thank You!

Your contributions help make this project better for everyone. Thank you for taking the time to contribute!
