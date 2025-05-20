# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0-beta] - 2025-05-20

### Added
- G-code viewer with syntax highlighting and line numbers
- View G-code option in File menu
- Read-only view with scroll support
- Current line indicator
- File history tracking and recent files menu
- Progress bar for file operations
- Status bar for operation status
- Improved error handling and logging
- Configuration system for persistent settings
- Better UI layout with left panel for controls
- File list to track opened files
- Renamed main application file to `main.py` for better clarity

### Changed
- Modernized UI with ttk themed widgets
- Improved menu structure and organization
- Enhanced 3D preview area layout
- Better button styling and spacing
- Removed customtkinter dependency for better compatibility

### Fixed
- Removed duplicated menu definitions
- Fixed ttk import issues
- Improved error handling for file operations
- Better progress tracking during conversions

## [1.0.1-beta] - 2025-05-20

### Added
- Initial version with core functionality
- Basic STL file opening and visualization
- G-code conversion capabilities
- Menu system with Help, About, and Sponsor options
- Basic UI with file open and convert buttons

### Known Issues
- No file history tracking
- No progress indication during conversions
- Basic error handling only
- No persistent configuration

## [1.0.0-beta] - 2025-05-20

### Added
- Initial project setup
- Basic STL file handling
- 3D visualization using matplotlib
- Basic GUI structure with Tkinter
- Version tracking system

[1.0.2-beta]: https://github.com/Nsfr750/STL_to_G-Code/compare/v1.0.1-beta...v1.0.2-beta
[1.0.1-beta]: https://github.com/Nsfr750/STL_to_G-Code/compare/v1.0.0-beta...v1.0.1-beta
[1.0.0-beta]: https://github.com/Nsfr750/STL_to_G-Code/releases/tag/v1.0.0-beta
