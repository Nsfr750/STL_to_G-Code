# Changelog

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2025-07-10

### ⚠️ BREAKING CHANGES
- **Complete UI Rewrite**: Migrated from Tkinter to PyQt6
  - Requires Python 3.8 or higher
  - New dependency on PyQt6 and PyQt6-WebEngine
  - Updated all UI components to use Qt widgets
  - Removed Tkinter dependencies

### Added

- **New UI Framework**
  - Modern, native-looking interface with PyQt6
  - Dark theme support
  - Dockable panels for flexible workspace
  - High DPI display support
  - Improved keyboard shortcuts

- **Documentation**
  - Integrated markdown documentation viewer
  - Help menu with access to documentation
  - In-app documentation browser
  - Support for multiple documentation files

- **Log Viewer**
  - Real-time log monitoring
  - Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Color-coded log messages
  - Clear logs button
  - Auto-scrolling with pause option
  - Log file monitoring in root directory

- **Update System**
  - Automatic update checking
  - Manual update check option
  - Version comparison
  - Update notifications

- **Enhanced G-code Generation**
  - More realistic 3D printing G-code output
  - Improved toolpath generation
  - Better support for different printer firmwares
  - Added G-code validation

### Changed

- **UI/UX Improvements**
  - Redesigned main window layout
  - Modern icons and styling
  - Better error messages and user feedback
  - Improved file dialogs
  - More responsive interface
  - Enhanced menu structure

- **Code Quality**
  - Refactored codebase for better maintainability
  - Added type hints
  - Improved error handling
  - Better separation of concerns
  - Modular architecture with scripts directory

### Fixed
- Fixed log viewer file path issues
- Resolved update checker time import error
- Fixed menu bar visibility issues
- Addressed various UI layout problems
- Fixed G-code viewer line number rendering
- Resolved OpenGL context issues with WebEngine

### Dependencies

- Added: PyQt6 (>=6.4.0), PyQt6-WebEngine
- Updated: numpy, numpy-stl, matplotlib
- Removed: All Tkinter dependencies

---

## [1.2.0] - 2025-06-23

### Added

- **Update System**
  - Automatic update checking on startup
  - Manual update check from Help menu
  - Version comparison functionality
  - User notifications for available updates
  - GitHub release integration for update checking

### Changed

- Updated to stable release (removed beta status)
- Improved error handling for update checks
- Enhanced version management system

### Fixed

- Fixed STL import issue by switching from `stl` to `numpy-stl` package
- Improved compatibility with Python 3.12
- Fixed various UI responsiveness issues

### Dependencies

- Replaced `stl` with `numpy-stl` for better compatibility
- Updated minimum required versions for several dependencies
- Removed redundant dependencies

---

## [1.1.0-beta] - 2025-05-20

### Added

- **G-code Viewer**
  - Syntax-highlighted G-code viewing with color-coded commands
  - Line numbers with current line indicator
  - Search functionality with highlighting
  - Read-only view with scroll support
  - Status bar showing line and character counts
  - Support for multiple file formats (G-code, NC)
  - Save As functionality for modified G-code

- **UI Improvements**
  - Modern ttk-themed interface with improved styling
  - Left panel controls for better organization
  - Status bar with operation status
  - Progress bar for file operations
  - File history tracking and recent files menu
  - Persistent configuration system
  - Improved menu structure and organization

- **Features**
  - File list with status indicators
  - Enhanced 3D preview with rotation controls
  - Auto-scaling for better visualization
  - Improved error handling and logging
  - Configuration system for persistent settings

### Changed
- **UI/UX**
  - Modernized UI with ttk themed widgets
  - Improved button styling and spacing
  - Enhanced menu organization
  - Better layout for 3D preview area
  - Removed customtkinter dependency for better compatibility

- **Code**
  - Restructured main application file for better clarity
  - Improved error handling patterns
  - Enhanced logging system
  - Better code organization

### Fixed
- **Bugs**
  - Removed duplicated menu definitions
  - Fixed ttk import issues
  - Enhanced error handling for file operations
  - Improved progress tracking during conversions
  - Fixed window resizing issues
  - Enhanced file dialog handling

### Removed
- Customtkinter dependency for better compatibility

## [1.0.1-beta] - 2025-05-20

### Added
- **Core Functionality**
  - STL file opening and visualization
  - Basic G-code conversion
  - Menu system with Help, About, and Sponsor options
  - Basic UI with file open and convert buttons
  - Version tracking system
  - Basic error handling

### Known Issues
- No file history tracking
- No progress indication during conversions
- Basic error handling only
- No persistent configuration
- Limited file format support

## [1.0.0-beta] - 2025-05-20

### Added
- Initial project setup
- Basic STL file handling
- 3D visualization using matplotlib
- Basic GUI structure with Tkinter
- Version tracking system
- Initial error handling
- Basic logging capabilities

### Known Issues
- Basic UI implementation
- Limited error handling
- No configuration persistence
- Basic file operations only

[1.1.0-beta]: https://github.com/Nsfr750/STL_to_G-Code/releases/tag/v1.1.0-beta
[1.0.1-beta]: https://github.com/Nsfr750/STL_to_G-Code/releases/tag/v1.0.1-beta
[1.0.0-beta]: https://github.com/Nsfr750/STL_to_G-Code/releases/tag/v1.0.0-beta
