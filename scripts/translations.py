"""
Translation strings for STL to G-Code v{version}.
"""

# List of available language codes
LANGUAGES = ["en", "it"]

# Translation strings organized by language
TRANSLATIONS = {
    "en": {
        # Application
        "app_title": "STL to G-Code v{version}",
        
        # Menu items
        "file_menu": {
            "title": "&File",
            "open_stl": "&Open STL...",
            "open_gcode": "Open &G-code...",
            "save_gcode": "&Save G-code...",
            "recent_files": "Recent Files",
            "exit": "E&xit"
        },
        "edit_menu": {
            "title": "&Edit",
            "settings": "&Settings..."
        },
        "view_menu": {
            "title": "&View",
            "show_log": "Show &Log",
            "language": "&Language"
        },
        "help_menu": {
            "title": "&Help",
            "documentation": "&Documentation...",
            "help": "&Help",
            "check_updates": "Check for &Updates...",
            "about": "&About...",
            "sponsor": "&Sponsor..."
        },
        
        # About text
        "about_title": "About",
        "app_name": "STL to G-Code",
        "version": "Version {version}",
        "github": "GitHub",
        "system_information": "System Information",
        "operating_system": "Operating System",
        "error_loading_system_info": "Error loading system information",
        "about_description": "This application is developed and maintained by a single developer.\nYour support helps keep the project alive and allows for new features and improvements.",
        "copyright": "(c) 2025 Nsfr750",
        "license": "Licensed under the GPLv3 License",

        # Sponsor dialog
        "support_title": "Support STL to G-Code",
        "support_project": "Support the Project",
        "support_project_header": "Support STL to G-Code",
        "support_project_description": "This application is developed and maintained by a single developer.\nYour support helps keep the project alive and allows for new features and improvements.",
        "support_on_patreon": "Support on Patreon",
        "donate_via_paypal": "Donate with PayPal",
        "copy_address": "Copy Address",
        "address_copied": "Address Copied",
        "address_copied_to_clipboard": "address copied to clipboard",
        "support_development": "Support Development",
        "support_app_name": "Support STL to G-Code",
        "support_message": "If you find this application useful, we invite you to support its development.\n\nYour support helps cover hosting costs and encourages further development.",
        "github_sponsors": "GitHub Sponsors",
        "paypal_donation": "PayPal Donation",
        "monero": "Monero",
        "scan_to_donate_xmr": "Scan to donate XMR",
        "qr_generation_failed": "QR code generation failed",
        "ways_to_support": "Ways to Support",
        "other_ways_to_help": "Other Ways to Help",
        "star_on_github": "Star the project on",
        "report_bugs": "Report bugs and suggest features",
        "share_with_others": "Share with others who might find it useful",
        "copied": "Copied!",
        "close": "Close",
        "donate_with_paypal": "Donate with PayPal",
        "copy_monero_address": "Copy Monero Address",

        # Log viewer
        "log_viewer": "Log Viewer",
        "filter_logs": "Filter Logs",
        "no_log_file": "No log file available.",
        "error_reading_log": "Error reading log file: {error}",
        "clear_logs": "Clear Logs",
        "confirm_clear_logs": "Are you sure you want to clear all logs? This action cannot be undone.",
        "save_logs": "Save Logs",
        "save_log_file": "Save Log File",
        "log_files": "Log Files (*.log);;All Files (*)",
        "logs_saved": "Logs successfully saved to: {path}",
        "failed_save_logs": "Failed to save log file: {error}",
        "log_level": "Log Level",
        "all_levels": "All Levels",
        "refresh": "Refresh",
        "select_log_file": "Select Log File",
        "no_logs_found": "No Logs Found",
        "log_level_filters": "Log Level Filters",
        "clear_log": "Clear Log",
        "save_as": "Save As",
        "no_logs_available": "No Logs Available",
        
        # Log Viewer Translations
        "log_viewer.title": "Log Viewer",
        "log_viewer.labels.log_file": "Log File:",
        "log_viewer.labels.log_level": "Log Level:",
        "log_viewer.buttons.clear": "Clear Logs",
        
        # Log Level Options
        "log_viewer.levels.all": "ALL",
        "log_viewer.levels.debug": "DEBUG",
        "log_viewer.levels.info": "INFO",
        "log_viewer.levels.warning": "WARNING",
        "log_viewer.levels.error": "ERROR",
        "log_viewer.levels.critical": "CRITICAL",
        
        # Messages
        "log_viewer.messages.no_logs": "No log files found",
        "log_viewer.messages.logs_cleared": "Logs cleared",
        "log_viewer.errors.init_failed": "Error initializing log files: {error}",
        "log_viewer.errors.change_failed": "Error changing log file: {error}",
        
        # G-code Editor
        "gcode_editor": {
            "no_issues": "No issues",
            "no_issues_found": "No issues found",
            "error_count": "{count} error" if "{count}" == "1" else "{count} errors",
            "warning_count": "{count} warning" if "{count}" == "1" else "{count} warnings",
            "info_count": "{count} info" if "{count}" == "1" else "{count} info",
            "issue_line": "{icon} Line {line}: {message}",
            "validation_error": "Validation Error",
            "validation_warning": "Validation Warning",
            "validation_info": "Information",
            "save_changes": "Save Changes",
            "discard_changes": "Discard Changes",
            "unsaved_changes": "You have unsaved changes. Would you like to save them?"
        },

        # G-code Validator Translations
        "validation.severity.info": "Info",
        "validation.severity.warning": "Warning",
        "validation.severity.error": "Error",
        "validation.severity.critical": "Critical",
        
        "validation.error.invalid_syntax": "Invalid G-code syntax",
        "validation.error.invalid_parameter": "Invalid parameter value: {param}",
        "validation.error.processing_command": "Error processing command {command}: {error}",
        "validation.error.invalid_tool": "Invalid tool number: T{tool}",
        "validation.error.invalid_tool_selection": "Invalid tool selection: {command}",
        "validation.error.negative_feedrate": "Feedrate cannot be negative",
        "validation.error.axis_out_of_bounds": "{axis} position {value} is out of bounds (0-{max_pos})",
        "validation.error.invalid_fan_speed": "Fan speed {speed} is outside valid range (0-255)",
        
        "validation.warning.feedrate_exceeds_max": "Feedrate {feedrate} exceeds maximum of {max_feedrate}",
        "validation.warning.temp_out_of_range": "Extruder temperature {temp}°C is outside safe range ({min_temp}-{max_temp}°C)",
        "validation.warning.no_heated_bed": "Printer does not have a heated bed",
        "validation.warning.bed_temp_out_of_range": "Bed temperature {temp}°C is outside safe range ({min_temp}-{max_temp}°C)",
        "validation.warning.no_controllable_fan": "Printer does not have a controllable fan",
        "validation.warning.hotend_hot_fan_off": "Hotend is hot but part cooling fan is off",
        "validation.warning.hotend_hot_away_from_bed": "Hotend is hot but appears to be away from the print area",
        
        # Update checker
        "update_available": "Update Available",
        "new_version_available": "A new version of STL to G-Code is available!",
        "current_version": "Your version: {current_version}",
        "latest_version": "Latest version: {latest_version}",
        "download_update": "Download Update",
        "remind_me_later": "Remind Me Later",
        "skip_this_version": "Skip This Version",
        "checking_for_updates": "Checking for updates...",
        "up_to_date": "You are using the latest version of STL to G-Code.",
        "update_error": "Error checking for updates",
        "update_check_failed": "Failed to check for updates: {error}",
        "release_notes": "Release Notes",
        "download": "Download",
        "view_changes": "View Changes",
        "update_available_title": "Update Available",
        
        # Update Checker
        "updates.checking": "Checking for updates...",
        "updates.error.check_failed": "Failed to check for updates: {error}",
        "updates.error.connection": "Could not connect to the update server. Please check your internet connection.",
        "updates.error.invalid_response": "Received an invalid response from the update server.",
        "updates.available.title": "Update Available",
        "updates.available.message": "A new version {version} is available.\n\nWould you like to download it now?\n\nChanges in this version:\n{changelog}",
        "updates.available.download": "Download Update",
        "updates.available.later": "Remind Me Later",
        "updates.available.skip": "Skip This Version",
        "updates.latest.title": "Up to Date",
        "updates.latest.message": "You are using the latest version ({version}).",
        "updates.downloading": "Downloading update...",
        "updates.download.complete": "Download complete. The update will be installed when you restart the application.",
        "updates.download.failed": "Failed to download update: {error}",
        "updates.check.complete": "Update check complete.",
        "updates.check.force": "Force checking for updates...",
        "updates.check.offline": "Skipping update check (offline mode)",
        "updates.check.frequency": "Checking for updates every {hours} hours",
        "updates.check.last_checked": "Last checked: {time}",
        "updates.check.next_check": "Next check: {time}",
        "updates.check.manual": "Manual update check requested",
        
        # Worker-related translations
        "worker.error.unsupported_mesh_format": "Unsupported mesh format. Expected trimesh object or dictionary with 'vertices' key.",
        "worker.info.calculated_layers": "Calculated {layers} layers (z: {z_min:.2f}mm to {z_max:.2f}mm, height: {height:.2f}mm)",
        "worker.info.generation_cancelled": "G-code generation cancelled by user",
        "worker.info.generation_complete": "G-code generation completed successfully",
        "worker.error.generation_failed": "Error in G-code generation: {error}",
        
        "worker.error.missing_header_info": "STL processor is missing required header information",
        "worker.error.invalid_triangle_count": "Invalid number of triangles in STL file: {count}",
        "worker.error.loading_failed": "Error in STL loading worker: {error}",
        "worker.error.cleanup_failed": "Error closing STL processor: {error}",
        "worker.info.stl_loading_started": "STL loading worker started",
        "worker.info.total_triangles": "Total triangles to process: {count}",
        "worker.info.loading_cancelled": "Loading cancelled by user",
        "worker.info.loading_complete": "STL loading completed successfully",
        "worker.status.loading_stl": "Loading STL... {progress:.1f}%",
        
        "worker.debug.stl_header": "STL header: {header}",
        "worker.debug.starting_triangle_iteration": "Starting triangle iteration...",
        "worker.debug.emitting_chunk": "Emitting chunk with {triangles} triangles, progress: {progress:.1f}%",
        "worker.debug.loading_cancellation_requested": "STL loading cancellation requested",
        "worker.warning.no_stl_header": "STL processor has no _header attribute",
        
        # STL Processor
        "stl_processor": {
            "file_opened": "Opened STL file: {filename} ({num_triangles} triangles)",
            
            "detection": {
                "binary_detected": "Binary STL detected (null byte found in first 100 bytes)",
                "ascii_detected": "ASCII STL detected (starts with 'solid' and no null bytes)",
                "default_to_binary": "Could not determine STL format, defaulting to binary"
            },
            
            "ascii_header": {
                "first_line": "ASCII STL header - First line: {line}",
                "decode_error": "ASCII STL header - Could not decode first line: {error}",
                "triangle_count": "ASCII STL header - Number of triangles: {count}",
                "processing_complete": "Processed {count} triangles from ASCII STL file"
            },
            
            "binary_header": {
                "comment": "Binary STL header - Comment: {comment}",
                "decode_error": "Binary STL header - Could not decode comment: {error}",
                "triangle_count": "Binary STL header - Number of triangles: {count}",
                "size_mismatch": "STL file size doesn't match header. Expected {expected} bytes, got {actual}.",
                "processing_complete": "Processed {count} triangles from binary STL file"
            },
            
            "error": {
                "invalid_ascii_stl": "Not a valid ASCII STL file",
                "expected_vertex": "Expected 'vertex' in STL file"
            },
            
            "warning": {
                "triangle_parse_error": "Error parsing triangle at position {position}: {error}",
                "incomplete_triangle": "Incomplete triangle data, expected {expected} bytes, got {actual}"
            },
            
            "debug": {
                "triangle_info": "Triangle {index}:\n  Normal: {normal}\n  Vertex 1: {vertex1}\n  Vertex 2: {vertex2}\n  Vertex 3: {vertex3}\n  Attributes: {attributes}"
            }
        },
        
        # Progress module
        "progress": {
            "ui": {
                "loading": "Loading...",
                "loading_progress": "Loading: {progress}%"
            },
            "log": {
                "progress": "Loading progress: {progress}%"
            },
            "errors": {
                "invalid_progress_value": "Invalid progress value: {progress} - {error}",
                "update_error": "Error updating progress dialog: {error}",
                "reset_error": "Error resetting progress dialog: {error}"
            }
        },
        
        # Settings Dialog Translations
        "settings_dialog.title": "Settings",
        
        # Tab names
        "settings_dialog.tabs.general": "General",
        "settings_dialog.tabs.path_optimization": "Path Optimization",
        "settings_dialog.tabs.infill": "Infill",
        "settings_dialog.tabs.advanced": "Advanced",
        
        # Group box titles
        "settings_dialog.general.title": "General Settings",
        "settings_dialog.path_optimization.title": "Path Optimization Settings",
        "settings_dialog.infill.title": "Infill Settings",
        "settings_dialog.advanced.title": "Advanced Settings",
        "settings_dialog.gcode.title": "G-code",
        
        # General settings
        "settings_dialog.general.layer_height": "Layer Height (mm):",
        "settings_dialog.general.print_speed": "Print Speed (mm/s):",
        "settings_dialog.general.travel_speed": "Travel Speed (mm/s):",
        "settings_dialog.general.retraction_length": "Retraction Length (mm):",
        
        # Path optimization settings
        "settings_dialog.path_optimization.enable": "Enable Path Optimization:",
        "settings_dialog.path_optimization.enable_arcs": "Enable Arc Detection:",
        "settings_dialog.path_optimization.arc_tolerance": "Arc Tolerance (mm):",
        "settings_dialog.path_optimization.min_arc_segments": "Min Arc Segments:",
        "settings_dialog.path_optimization.remove_redundant": "Remove Redundant Moves:",
        "settings_dialog.path_optimization.combine_coincident": "Combine Coincident Moves:",
        "settings_dialog.path_optimization.optimize_travel": "Optimize Travel Moves:",
        
        # Infill settings
        "settings_dialog.infill.density": "Density (%):",
        "settings_dialog.infill.pattern": "Pattern:",
        "settings_dialog.infill.patterns.grid": "Grid",
        "settings_dialog.infill.patterns.lines": "Lines",
        "settings_dialog.infill.patterns.triangles": "Triangles",
        "settings_dialog.infill.patterns.trihexagon": "Tri-Hexagon",
        "settings_dialog.infill.patterns.cubic": "Cubic",
        "settings_dialog.infill.angle": "Angle (degrees):",
        "settings_dialog.infill.enable_optimized": "Enable Optimized Infill:",
        "settings_dialog.infill.resolution": "Resolution (mm):",
        
        # Advanced settings
        "settings_dialog.advanced.extrusion_width": "Extrusion Width (mm):",
        "settings_dialog.advanced.filament_diameter": "Filament Diameter (mm):",
        "settings_dialog.advanced.first_layer_height": "First Layer Height (mm):",
        "settings_dialog.advanced.first_layer_speed": "First Layer Speed (mm/s):",
        "settings_dialog.advanced.z_hop": "Z Hop (mm):",
        "settings_dialog.advanced.skirt_line_count": "Skirt Line Count:",
        "settings_dialog.advanced.skirt_distance": "Skirt Distance (mm):",
        "settings_dialog.advanced.temperature": "Nozzle Temperature (°C):",
        "settings_dialog.advanced.bed_temperature": "Bed Temperature (°C):",
        "settings_dialog.advanced.fan_speed": "Fan Speed (%):",
        "settings_dialog.advanced.fan_layer": "Fan Start Layer:",
        
        # G-code settings
        "settings_dialog.gcode.start": "Start G-code:",
        "settings_dialog.gcode.end": "End G-code:",
        "settings_dialog.gcode.start_placeholder": "; Start G-code (inserted at the beginning of the file)\nG28 ; Home all axes\nG1 Z5 F5000 ; Lift nozzle\nM104 S{material_print_temperature} ; Set nozzle temperature\nM190 S{material_bed_temperature} ; Wait for bed temperature\nM109 S{material_print_temperature} ; Wait for nozzle temperature\nG92 E0 ; Reset extruder\nG1 E-1 F300 ; Retract a little\nG1 Z0.4 F3000 ; Move nozzle up\nG1 X3.2 F5000 ; Move to start position\nG1 Y100.0 Z0.3 F1500.0 E15 ; Draw first line\nG1 X3.2 Y20.2 Z0.3 F1500.0 E30 ; Draw second line\nG92 E0 ; Reset extruder\nG1 Z2.0 F3000 ; Move Z up a bit",
        "settings_dialog.gcode.end_placeholder": "; End G-code\nM104 S0 ; Turn off hotend\nM140 S0 ; Turn off bed\nG91 ; Use relative positioning\nG1 E-1 F300 ; Retract filament\nG1 Z+5 E-5 F3000 ; Lift and retract\nG90 ; Use absolute positioning\nG28 X0 ; Home X axis\nM84 ; Disable steppers",
        
        # Reset confirmation
        "settings_dialog.reset_title": "Reset to Defaults",
        "settings_dialog.reset_confirm": "Are you sure you want to reset all settings to their default values?",

        # Configuration
        "config.error_loading": "Error loading configuration: {error}",
        "config.error_saving": "Error saving configuration: {error}",
        
        # Markdown Viewer Translations
        "markdown_viewer.title": "Documentation",
        "markdown_viewer.label.document": "Document:",
        "markdown_viewer.button.close": "Close",
        "markdown_viewer.error.file_not_found": "File not found: {filename}",
        "markdown_viewer.error.load_error": "Error loading {filename}: {error}",
        "markdown_viewer.message.no_docs_title": "No Documentation Found",
        "markdown_viewer.message.no_docs_text": "No markdown documentation files (*.md) were found in the 'docs' directory.",
        
        # G-code Viewer Translations
        "gcode_viewer.title": "G-code Viewer",
        "gcode_viewer.title_with_file": "G-code Viewer - {filename}",
        
        "gcode_viewer.buttons.open": "Open G-code",
        "gcode_viewer.buttons.save": "Save",
        
        "gcode_viewer.search.placeholder": "Search in G-code...",
        "gcode_viewer.search.not_found": "'{text}' not found.",
        "gcode_viewer.search.not_found_title": "Not Found",
        
        "gcode_viewer.line_number": "Line: {number}",
        
        "gcode_viewer.file_dialog.open_title": "Open G-code File",
        "gcode_viewer.file_dialog.filter": "G-code Files (*.gcode *.nc *.txt);;All Files (*)",
        
        "gcode_viewer.messages.success": "Success",
        "gcode_viewer.messages.file_saved": "File saved successfully.",
        "gcode_viewer.messages.error": "Error",
        "gcode_viewer.messages.save_error": "Failed to save file: {error}",
        "gcode_viewer.messages.load_error": "Failed to load file: {error}",
        
        # Help Dialog Translations
        "help_dialog.title": "STL to GCode Converter - Help",
        "help_dialog.buttons.close": "Close",
        "help_dialog.buttons.documentation": "Open Full Documentation",
        
        "help.content.overview": """
        <h1>STL to GCode Converter - User Guide</h1>
        
        <h2>Overview</h2>
        <p>This application converts STL (STereoLithography) files to G-code for 3D printing and CNC machining, featuring a modern PyQt6-based interface with advanced visualization and customization options.</p>
        
        <h2>Getting Started</h2>
        <ol>
            <li>Open an STL file using File > Open or drag and drop</li>
            <li>Adjust settings in the right panel as needed</li>
            <li>Preview the 3D model using the view controls</li>
            <li>Generate G-code using the toolbar button</li>
            <li>Save or export your G-code</li>
        </ol>
        
        <h2>Features</h2>
        
        <h3>File Management</h3>
        <ul>
            <li>Open STL files from your system</li>
            <li>Recent files menu for quick access</li>
            <li>Save G-code output to your preferred location</li>
            <li>Export/import settings profiles</li>
            <li>Drag and drop support</li>
        </ul>
        
        <h3>3D View Controls</h3>
        <ul>
            <li>Rotate: Left-click and drag</li>
            <li>Pan: Right-click and drag</li>
            <li>Zoom: Mouse wheel or pinch gesture</li>
            <li>Reset view: Double-click or toolbar button</li>
        </ul>
        
        <h3>G-code Generation</h3>
        <ul>
            <li>Customizable layer height and print speed</li>
            <li>Support structure generation</li>
            <li>Infill patterns and density control</li>
            <li>Multiple quality presets</li>
        </ul>
        
        <h2>Support</h2>
        <p>For additional help, please visit our <a href="https://github.com/yourusername/stl-to-gcode/wiki">documentation</a> or contact support.</p>
        """,
        
        # About Dialog Translations
        "about.title": "About STL to G-Code Converter",
        "about.app_name": "STL to G-Code Converter",
        "about.version": "Version: {version}",
        "about.copyright": " 2025 Nsfr750",
        "about.description": (
            "A powerful application for converting STL files to G-code for 3D printing.\n\n"
            "This tool provides advanced features for 3D model preparation and G-code optimization "
            "to ensure high-quality 3D prints."
        ),
        "about.system_info": "System Information",
        "about.os": "Operating System: {os_name} {os_version}",
        "about.python": "Python: {python_version}",
        "about.qt": "Qt: {qt_version}",
        "about.pyqt": "PyQt: {pyqt_version}",
        "about.cpu": "CPU: {cpu_info}",
        "about.memory": "Memory: {memory:.2f} GB",
        "about.gpu": "GPU: {gpu_info}",
        "about.buttons.github": "GitHub",
        "about.buttons.documentation": "Documentation",
        "about.buttons.license": "License",
        "about.buttons.close": "Close",
        "about.buttons.check_updates": "Check for Updates",
        "about.links.website": "Website",
        "about.links.issues": "Report Issues",
        "about.links.donate": "Donate",
        "about.credits.title": "Credits",
        "about.credits.developer": "Developer: {author}",
        "about.credits.contributors": "Contributors",
        "about.credits.libraries": "Libraries Used",
        "about.credits.licenses": "Open Source Licenses",
        
        # About Dialog - Additional Keys
        "about.urls.github": "https://github.com/Nsfr750/STL_to_G-Code",
        "about.urls.documentation": "https://github.com/Nsfr750/STL_to_G-Code/wiki",
        
        "about.license_title": "License Information",
        "about.license": "GNU General Public License v3.0",
        "about.license_text": (
            "This program is free software: you can redistribute it and/or modify\n"
            "it under the terms of the GNU General Public License as published by\n"
            "the Free Software Foundation, either version 3 of the License, or\n"
            "(at your option) any later version.\n\n"
            "This program is distributed in the hope that it will be useful,\n"
            "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
            "GNU General Public License for more details.\n\n"
            "You should have received a copy of the GNU General Public License\n"
            "along with this program.  If not, see <https://www.gnu.org/licenses/>."
        ),
        
        "about.update_error_title": "Update Error",
        "about.update_error_message": "An error occurred while checking for updates: {error}",
        
        "about.cores": "CPU Cores",
        "about.available": "available",
        "about.error_loading_system_info": "Error loading system information",
        
        # STL Loading
        "stl.loading.open_dialog_title": "Open STL File",
        "stl.loading.file_filter": "STL Files (*.stl)",
        "stl.loading.no_file_selected": "No file selected",
        "stl.loading.file_not_found": "File not found: {file_path}",
        "stl.loading.operation_cancelled": "Operation cancelled by user",
        "stl.loading.error_opening": "Error opening STL file: {error}",
        "stl.loading.failed_to_open": "Failed to open file: {file_path}\n\nError: {error_msg}",
        "stl.loading.error_metadata": "Error getting STL metadata: {error}",
        "stl.loading.large_file_title": "Large File Warning",
        "stl.loading.large_file_message": "The selected file is large ({size_mb:.1f} MB). This may take a while to process. Continue?",
        "stl.loading.error_title": "Error Opening File",
        
        # Error Handling
        "error_handling.no_error_message": "No error message available",
        "error_handling.error_dialog_title": "Error - {error_type}",
        "error_handling.permission_denied": "Permission denied when trying to {operation} '{file_name}'",
        "error_handling.file_not_found": "File not found: {file_name}",
        "error_handling.expected_file_found_dir": "Expected a file but found a directory: {file_name}",
        "error_handling.file_in_use": "Cannot {operation} '{file_name}': The file is in use by another process",
        "error_handling.file_operation_error": "Error {operation}ing file '{file_name}': {error}",
        "error_handling.default_warning_title": "Warning",
        "error_handling.default_info_title": "Information",
        "error_handling.default_confirm_title": "Confirm",
        
        # G-code Loading
        "gcode.loading.open_dialog_title": "Open G-code File",
        "gcode.loading.file_filter": "G-code Files (*.gcode *.nc *.tap);;All Files (*)",
        "gcode.loading.file_not_found": "File not found: {file_path}",
        "gcode.loading.large_file_detected": "Large G-code file detected: {size_mb:.2f}MB",
        "gcode.loading.large_file_title": "Large File Warning",
        "gcode.loading.large_file_message": "This G-code file is {size_mb:.2f}MB. Loading large files may take time and consume significant memory.\n\nDo you want to continue?",
        "gcode.loading.operation_canceled": "Operation canceled",
        "gcode.loading.no_file_selected": "No file selected",
        "gcode.loading.user_canceled": "User canceled loading large file",
        "gcode.loading.loading_file": "Loading G-code file: {file_path}",
        "gcode.loading.success": "Successfully loaded G-code file: {file_name} ({file_size} bytes, {line_count} lines)",
        "gcode.loading.permission_denied": "Permission denied when accessing file: {file_path}",
        "gcode.loading.io_error": "Error reading file: {file_path}",
        "gcode.loading.unexpected_error": "Unexpected error loading file: {file_path}",
        
        # G-code Optimizer
        "gcode_optimizer.error.optimized_infill": "Error in generate_optimized_infill: {error}",
        "gcode_optimizer.error.invalid_command": "Invalid G-code command: {command} at line {line_num}",
        "gcode_optimizer.error.missing_variable_start": "Missing variable in start G-code: {error}",
        "gcode_optimizer.error.invalid_start_gcode": "Error in start G-code: {error}",
        "gcode_optimizer.error.unsupported_mesh_format": "Unsupported mesh format. Expected trimesh object or dictionary with 'vertices' key.",
        "gcode_optimizer.error.generating_gcode": "Error generating G-code: {error}",
        "gcode_optimizer.error.missing_variable_end": "Missing variable in end G-code: {error}",
        "gcode_optimizer.error.invalid_end_gcode": "Error in end G-code: {error}",
        "gcode_optimizer.error.unsupported_mesh_with_faces": "Unsupported mesh format. Expected trimesh object or dictionary with 'vertices' and 'faces' keys.",
        "gcode_optimizer.error.no_face_info": "Could not determine face information from mesh",
        
        # G-code Comments
        "gcode_optimizer.comment.custom_start_code": "--- Custom Start G-code ---",
        "gcode_optimizer.comment.end_start_code": "--- End of Custom Start G-code ---",
        "gcode_optimizer.comment.custom_end_code": "--- Custom End G-code ---",
        "gcode_optimizer.comment.end_end_code": "--- End of Custom End G-code ---",
        "gcode_optimizer.comment.layer_z": "--- Layer at Z={z} ---",
        "gcode_optimizer.comment.move_to_layer": "Move to layer height",
        "gcode_optimizer.comment.infill_section": "--- Infill ---",
        "gcode_optimizer.comment.set_infill_speed": "Set infill speed",
        "gcode_optimizer.comment.move_to_start": "Move to start",
        "gcode_optimizer.comment.draw_infill_line": "Draw infill line",
        
        # Retraction Comments
        "gcode_optimizer.retract.retract": "retract",
        "gcode_optimizer.retract.unretract": "unretract",
        
        # STL Processor module
        "stl_processor": {
            "file_opened": "Opened STL file: {filename} ({num_triangles} triangles)",
            "detection": {
                "binary_detected": "Binary STL detected (null byte found in first 100 bytes)",
                "ascii_detected": "ASCII STL detected (starts with 'solid' and no null bytes)",
                "default_binary": "Could not determine STL format, defaulting to binary"
            },
            "ascii_header": {
                "first_line": "ASCII STL header - First line: {line}",
                "first_line_error": "ASCII STL header - Could not decode first line: {error}",
                "triangle_count": "ASCII STL header - Number of triangles: {count}"
            },
            "errors": {
                "file_not_found": "STL file not found: {path}",
                "invalid_file": "Invalid or corrupted STL file: {path}",
                "read_error": "Error reading STL file: {error}",
                "invalid_format": "Invalid STL format",
                "empty_file": "STL file is empty",
                "header_error": "Error reading STL header: {error}",
                "triangle_error": "Error reading triangle data: {error}"
            }
        },
        
        # STL View
        "stl_view": {
            "axes": {
                "x_label": "X",
                "y_label": "Y",
                "z_label": "Z"
            },
            "loading": "Loading STL file...",
            "error_loading": "Error loading STL file"
        },
        
        # STL Loading
        "stl": {
            "loading": {
                "open_dialog_title": "Open STL File",
                "file_filter": "STL Files (*.stl)",
                "no_file_selected": "No file selected"
            }
        },
        
        # Error Handling
        "error_handling": {
            "error_dialog_title": "Error"
        },
        
        # Logging
        "logging": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "config_success": "Logging configured successfully",
            "file_creation_failed": "Failed to create log file: {error}. Logging to console only.",
            "log_viewer": {
                "title": "Log Viewer",
                "filter_placeholder": "Filter logs...",
                "clear_confirm": "Are you sure you want to clear all log messages?",
                "clear_button": "Clear Log",
                "save_button": "Save Log",
                "save_title": "Save Log File",
                "save_success": "Log saved successfully to {path}",
                "save_failed": "Failed to save log file: {error}",
                "level_debug": "Debug",
                "level_info": "Info",
                "level_warning": "Warning",
                "level_error": "Error",
                "level_critical": "Critical"
            }
        },
        
        # UI Elements
        "ui": {
            # Buttons
            "buttons": {
                "open": "Open",
                "save": "Save",
                "save_as": "Save As",
                "run": "Run",
                "stop": "Stop",
                "settings": "Settings",
                "about": "About",
                "exit": "Exit",
                "browse": "Browse...",
                "add": "Add",
                "remove": "Remove",
                "clear": "Clear",
                "apply": "Apply",
                "cancel": "Cancel",
                "ok": "OK",
                "reset": "Reset",
                "help": "Help"
            },
            
            # Labels
            "labels": {
                "input_file": "Input File:",
                "output_file": "Output File:",
                "no_file_selected": "No file selected",
                "status": "Status:",
                "progress": "Progress:",
                "ready": "Ready",
                "processing": "Processing...",
                "complete": "Complete",
                "error": "Error",
                "warning": "Warning",
                "info": "Information"
            },
            
            # Tooltips
            "tooltips": {
                "open_file": "Open an STL file for processing",
                "save_file": "Save the generated G-code to a file",
                "run_conversion": "Start the conversion process",
                "stop_conversion": "Stop the current operation"
            },
            
            # Messages
            "messages": {
                "file_opened": "File opened: {filename}",
                "file_saved": "File saved: {filename}",
                "conversion_complete": "Conversion completed successfully",
                "conversion_failed": "Conversion failed: {error}",
                "no_file_selected": "Please select an input file first",
                "invalid_file": "Invalid file format. Please select an STL file.",
                "processing_file": "Processing file: {filename}",
                "saving_file": "Saving to: {filename}"
            },
            
            # Settings
            "settings": {
                "title": "Settings",
                "general": "General",
                "appearance": "Appearance",
                "language": "Language:",
                "theme": "Theme:",
                "dark": "Dark",
                "light": "Light",
                "system": "System",
                "units": "Units:",
                "millimeters": "Millimeters (mm)",
                "inches": "Inches (in)",
                "precision": "Precision:",
                "decimal_places": "{n} decimal places"
            },
            
            # Menu items
            "menu": {
                "file": "&File",
                "edit": "&Edit",
                "view": "&View",
                "tools": "&Tools",
                "help": "&Help"
            },
            
            # File menu
            "file_menu": {
                "new": "&New",
                "open": "&Open...",
                "save": "&Save",
                "save_as": "Save &As...",
                "recent_files": "Recent Files",
                "exit": "E&xit"
            },
            
            # Edit menu
            "edit_menu": {
                "undo": "&Undo",
                "redo": "&Redo",
                "cut": "Cu&t",
                "copy": "&Copy",
                "paste": "&Paste",
                "delete": "&Delete",
                "select_all": "Select &All"
            },
            
            # View menu
            "view_menu": {
                "toolbar": "&Toolbar",
                "statusbar": "Status &Bar",
                "fullscreen": "&Full Screen",
                "zoom_in": "Zoom &In",
                "zoom_out": "Zoom &Out",
                "reset_zoom": "&Reset Zoom"
            },
            
            # Help menu
            "help_menu": {
                "documentation": "&Documentation",
                "check_updates": "Check for &Updates",
                "about": "&About"
            },
            
            # About dialog
            "about": {
                "title": "About STL to G-Code Converter",
                "version": "Version {version}",
                "description": "A tool for converting STL 3D models to G-code for CNC machines.",
                "copyright": " 2025 Nsfr750",
                "license": "Licensed under the GPLv3 License."
            }
        },
        
        # Help Dialog
        "help.dialog.title": "Help - STL to G-Code",
        "help.buttons.full_documentation": "Full Documentation",
        "help.tooltips.full_documentation": "Open the full documentation in your web browser",
        "common.buttons.close": "Close",
        
        # Help Content
        "help.title": "STL to G-Code Help",
        
        # Overview Section
        "help.overview.title": "Overview",
        "help.overview.description": "STL to G-Code is a powerful tool for converting 3D models (STL files) into G-code for 3D printing.",
        
        # Getting Started Section
        "help.getting_started.title": "Getting Started",
        "help.getting_started.step1": "1. Open an STL file using File > Open STL or drag and drop a file",
        "help.getting_started.step2": "2. Adjust the print settings as needed",
        "help.getting_started.step3": "3. Click 'Convert to G-code' to generate the G-code",
        "help.getting_started.step4": "4. Preview the generated G-code and make adjustments if needed",
        "help.getting_started.step5": "5. Save the G-code to a file or send it directly to your 3D printer",
        
        # Features Section
        "help.features.title": "Features",
        
        # File Management Features
        "help.features.file_management.title": "File Management",
        "help.features.file_management.item1": "• Open and view STL files",
        "help.features.file_management.item2": "• Save and export G-code",
        "help.features.file_management.item3": "• Recent files list",
        "help.features.file_management.item4": "• Import/export settings profiles",
        "help.features.file_management.item5": "• Drag and drop support",
        
        # Visualization Features
        "help.features.visualization.title": "3D Visualization",
        "help.features.visualization.item1": "• Interactive 3D model preview",
        "help.features.visualization.item2": "• Layer-by-layer visualization",
        "help.features.visualization.item3": "• Multiple view modes (solid, wireframe, etc.)",
        "help.features.visualization.item4": "• Zoom, pan, and rotate controls",
        "help.features.visualization.item5": "• Measurement tools",
        
        # G-code Tools
        "help.features.gcode_tools.title": "G-code Tools",
        "help.features.gcode_tools.item1": "• G-code editor with syntax highlighting",
        "help.features.gcode_tools.item2": "• G-code validation and analysis",
        "help.features.gcode_tools.item3": "• Optimize G-code for better print quality",
        "help.features.gcode_tools.item4": "• Preview G-code execution",
        "help.features.gcode_tools.item5": "• Custom start/end G-code scripts",
        
        # Documentation
        "help.features.documentation.title": "Documentation",
        "help.features.documentation.item1": "• Built-in help system",
        "help.features.documentation.item2": "• Tooltips and hints throughout the UI",
        "help.features.documentation.item3": "• Online documentation and tutorials",
        "help.features.documentation.item4": "• Keyboard shortcuts reference",
        
        # Advanced Features
        "help.features.advanced.title": "Advanced Features",
        "help.features.advanced.item1": "• Customizable print profiles",
        "help.features.advanced.item2": "• Support for multiple extruders",
        "help.features.advanced.item3": "• Advanced infill patterns",
        "help.features.advanced.item4": "• Support for custom post-processing scripts",
        "help.features.advanced.item5": "• Plugin system for extending functionality",
        
        # Keyboard Shortcuts
        "help.shortcuts.title": "Keyboard Shortcuts",
        "help.shortcuts.ctrl_o": "Ctrl+O",
        "help.shortcuts.ctrl_o_desc": "Open STL file",
        "help.shortcuts.ctrl_s": "Ctrl+S",
        "help.shortcuts.ctrl_s_desc": "Save G-code",
        "help.shortcuts.f1": "F1",
        "help.shortcuts.f1_desc": "Show this help dialog",
        "help.shortcuts.ctrl_q": "Ctrl+Q",
        "help.shortcuts.ctrl_q_desc": "Quit application",
        "help.shortcuts.ctrl_l": "Ctrl+L",
        "help.shortcuts.ctrl_l_desc": "Show log viewer",
        "help.shortcuts.ctrl_g": "Ctrl+G",
        "help.shortcuts.ctrl_g_desc": "View G-code editor",
        
        # Support Section
        "help.support.title": "Support",
        "help.support.description": "For more help, please visit our documentation or contact support.",
        
    },
    "it": {
        # Application
        "app_title": "STL a G-Code v{version}",
        
        # Menu items
        "file_menu": {
            "title": "&File",
            "open_stl": "&Apri STL...",
            "open_gcode": "Apri &G-code...",
            "save_gcode": "&Salva G-code...",
            "recent_files": "File recenti",
            "exit": "E&sci"
        },
        "edit_menu": {
            "title": "&Modifica",
            "settings": "Impo&stazioni..."
        },
        "view_menu": {
            "title": "&Visualizza",
            "show_log": "Mostra &Log",
            "language": "&Lingua"
        },
        "help_menu": {
            "title": "&Aiuto",
            "documentation": "&Documentazione...",
            "help": "&Aiuto",
            "check_updates": "Controlla &Aggiornamenti...",
            "about": "&Informazioni...",
            "sponsor": "&Supporta il Progetto..."
        },
        
        # About dialog
        "about_title": "Informazioni",
        "app_name": "STL a G-Code",
        "version": "Versione {version}",
        "github": "GitHub",
        "system_information": "Informazioni di Sistema",
        "operating_system": "Sistema Operativo",
        "error_loading_system_info": "Errore nel caricamento delle informazioni di sistema",
        "about_description": "Questa applicazione è sviluppata e mantenuta da un singolo sviluppatore.\nIl tuo supporto aiuta a mantenere in vita il progetto e a sviluppare nuove funzionalità e miglioramenti.",
        "copyright": " 2025 Nsfr750",
        "license": "Distribuito con licenza GPLv3",
        
        # Sponsor dialog
        "support_title": "Supporta STL a G-Code",
        "support_project": "Supporta il Progetto",
        "support_project_header": "Supporta STL a G-Code",
        "support_project_description": "Questa applicazione è sviluppata e mantenuta da un singolo sviluppatore.\nIl tuo supporto aiuta a mantenere in vita il progetto e a sviluppare nuove funzionalità e miglioramenti.",
        "support_on_patreon": "Supporta su Patreon",
        "donate_via_paypal": "Dona con PayPal",
        "copy_address": "Copia Indirizzo",
        "address_copied": "Indirizzo Copiato",
        "address_copied_to_clipboard": "indirizzo copiato negli appunti",
        "support_development": "Supporta lo Sviluppo",
        "support_app_name": "Supporta STL a G-Code",
        "support_message": "Se trovi utile questa applicazione, ti invitiamo a supportarne lo sviluppo.\n\nIl tuo supporto aiuta a coprire i costi di hosting e incoraggia ulteriori sviluppi.",
        "github_sponsors": "GitHub Sponsors",
        "paypal_donation": "Donazione PayPal",
        "monero": "Monero",
        "scan_to_donate_xmr": "Scansiona per donare XMR",
        "qr_generation_failed": "Generazione codice QR fallita",
        "ways_to_support": "Modi per Supportare",
        "other_ways_to_help": "Altri Modi per Aiutare",
        "star_on_github": "Metti una stella al progetto su",
        "report_bugs": "Segnala bug e suggerisci funzionalità",
        "share_with_others": "Condividi con altri che potrebbero trovarlo utile",
        "copied": "Copiato!",
        "close": "Chiudi",
        "donate_with_paypal": "Dona con PayPal",
        "copy_monero_address": "Copia Indirizzo Monero",

        # Log viewer
        "log_viewer": "Visualizzatore Log",
        "filter_logs": "Filtra Log",
        "no_log_file": "Nessun file di log disponibile.",
        "error_reading_log": "Errore durante la lettura del file di log: {error}",
        "clear_logs": "Pulisci Log",
        "confirm_clear_logs": "Sei sicuro di voler cancellare tutti i log? Questa azione non può essere annullata.",
        "save_logs": "Salva Log",
        "save_log_file": "Salva File di Log",
        "log_files": "File di Log (*.log);;Tutti i File (*)",
        "logs_saved": "Log salvati con successo in: {path}",
        "failed_save_logs": "Impossibile salvare il file di log: {error}",
        "log_level": "Livello di Log",
        "all_levels": "Tutti i Livelli",
        "refresh": "Aggiorna",
        "select_log_file": "Seleziona File di Log",
        "no_logs_found": "Nessun Log Trovato",
        "log_level_filters": "Filtri Livello Log",
        "clear_log": "Pulisci Log",
        "save_as": "Salva come",
        "no_logs_available": "Nessun Log Disponibile",
        
        # Log Viewer Translations
        "log_viewer.title": "Visualizzatore Log",
        "log_viewer.labels.log_file": "File di log:",
        "log_viewer.labels.log_level": "Livello:",
        "log_viewer.buttons.clear": "Pulisci Log",
        
        # Log Level Options
        "log_viewer.levels.all": "TUTTI",
        "log_viewer.levels.debug": "DEBUG",
        "log_viewer.levels.info": "INFO",
        "log_viewer.levels.warning": "ATTENZIONE",
        "log_viewer.levels.error": "ERRORE",
        "log_viewer.levels.critical": "CRITICO",
        
        # Messages
        "log_viewer.messages.no_logs": "Nessun file di log trovato",
        "log_viewer.messages.logs_cleared": "Log cancellati",
        "log_viewer.errors.init_failed": "Errore durante l'inizializzazione dei file di log: {error}",
        "log_viewer.errors.change_failed": "Errore durante il cambio del file di log: {error}",
        
        # G-code Editor
        "gcode_editor": {
            "no_issues": "Nessun problema",
            "no_issues_found": "Nessun problema trovato",
            "error_count": "{count} errore" if "{count}" == "1" else "{count} errori",
            "warning_count": "{count} avviso" if "{count}" == "1" else "{count} avvisi",
            "info_count": "{count} informazione" if "{count}" == "1" else "{count} informazioni",
            "issue_line": "{icon} Riga {line}: {message}",
            "validation_error": "Errore di convalida",
            "validation_warning": "Avviso di convalida",
            "validation_info": "Informazione",
            "save_changes": "Salva modifiche",
            "discard_changes": "Annulla modifiche",
            "unsaved_changes": "Hai delle modifiche non salvate. Vuoi salvarle?"
        },

        # G-code Validator Translations
        "validation.severity.info": "Informazione",
        "validation.severity.warning": "Avviso",
        "validation.severity.error": "Errore",
        "validation.severity.critical": "Critico",
        
        "validation.error.invalid_syntax": "Sintassi G-code non valida",
        "validation.error.invalid_parameter": "Valore parametro non valido: {param}",
        "validation.error.processing_command": "Errore durante l'elaborazione del comando {command}: {error}",
        "validation.error.invalid_tool": "Numero utensile non valido: T{tool}",
        "validation.error.invalid_tool_selection": "Selezione utensile non valida: {command}",
        "validation.error.negative_feedrate": "La velocità di avanzamento non può essere negativa",
        "validation.error.axis_out_of_bounds": "{axis} position {value} è fuori dai limiti (0-{max_pos})",
        "validation.error.invalid_fan_speed": "La velocità della ventola {speed} è al di fuori dell'intervallo valido (0-255)",
        
        "validation.warning.feedrate_exceeds_max": "La velocità di avanzamento {feedrate} supera il massimo di {max_feedrate}",
        "validation.warning.temp_out_of_range": "Extruder temperature {temp}°C is outside safe range ({min_temp}-{max_temp}°C)",
        "validation.warning.no_heated_bed": "La stampante non ha un piano riscaldato",
        "validation.warning.bed_temp_out_of_range": "Bed temperature {temp}°C is outside safe range ({min_temp}-{max_temp}°C)",
        "validation.warning.no_controllable_fan": "La stampante non ha una ventola controllabile",
        "validation.warning.hotend_hot_fan_off": "L'hotend è caldo ma la ventola di raffreddamento è spenta",
        "validation.warning.hotend_hot_away_from_bed": "L'hotend è caldo ma sembra essere lontano dall'area di stampa",
        
        # Update checker
        "update_available": "Aggiornamento Disponibile",
        "new_version_available": "È disponibile una nuova versione di STL a G-Code!",
        "current_version": "La tua versione: {current_version}",
        "latest_version": "Ultima versione: {latest_version}",
        "download_update": "Scarica Aggiornamento",
        "remind_me_later": "Ricordamelo più tardi",
        "skip_this_version": "Salta questa versione",
        "checking_for_updates": "Controllo aggiornamenti in corso...",
        "up_to_date": "Stai utilizzando l'ultima versione di STL a G-Code.",
        "update_error": "Errore durante il controllo degli aggiornamenti",
        "update_check_failed": "Impossibile controllare gli aggiornamenti: {error}",
        "release_notes": "Note di Rilascio",
        "download": "Scarica",
        "view_changes": "Visualizza Modifiche",
        "update_available_title": "Aggiornamento Disponibile",
        
        # Update Checker
        "updates.checking": "Controllo aggiornamenti in corso...",
        "updates.error.check_failed": "Impossibile controllare gli aggiornamenti: {error}",
        "updates.error.connection": "Impossibile connettersi al server di aggiornamento. Controlla la tua connessione internet.",
        "updates.error.invalid_response": "Risposta non valida ricevuta dal server di aggiornamento.",
        "updates.available.title": "Aggiornamento Disponibile",
        "updates.available.message": "È disponibile una nuova versione {version}.\n\nVuoi scaricarla ora?\n\nNovità di questa versione:\n{changelog}",
        "updates.available.download": "Scarica Aggiornamento",
        "updates.available.later": "Ricordamelo più tardi",
        "updates.available.skip": "Salta questa versione",
        "updates.latest.title": "Aggiornato",
        "updates.latest.message": "Stai utilizzando l'ultima versione disponibile ({version}).",
        "updates.downloading": "Download dell'aggiornamento in corso...",
        "updates.download.complete": "Download completato. L'aggiornamento verrà installato al riavvio dell'applicazione.",
        "updates.download.failed": "Impossibile scaricare l'aggiornamento: {error}",
        "updates.check.complete": "Controllo aggiornamenti completato.",
        "updates.check.force": "Forzo il controllo degli aggiornamenti...",
        "updates.check.offline": "Controllo aggiornamenti saltato (modalità offline)",
        "updates.check.frequency": "Controllo aggiornamenti ogni {hours} ore",
        "updates.check.last_checked": "Ultimo controllo: {time}",
        "updates.check.next_check": "Prossimo controllo: {time}",
        "updates.check.manual": "Controllo aggiornamenti manuale richiesto",
        
        # Worker-related translations
        "worker.error.unsupported_mesh_format": "Formato mesh non supportato. Atteso oggetto trimesh o dizionario con chiave 'vertices'.",
        "worker.info.calculated_layers": "Calcolati {layers} layer (z: da {z_min:.2f}mm a {z_max:.2f}mm, altezza: {height:.2f}mm)",
        "worker.info.generation_cancelled": "Generazione G-code annullata dall'utente",
        "worker.info.generation_complete": "Generazione G-code completata con successo",
        "worker.error.generation_failed": "Errore nella generazione del G-code: {error}",
        
        "worker.error.missing_header_info": "Mancano le informazioni di intestazione richieste nel processore STL",
        "worker.error.invalid_triangle_count": "Numero di triangoli non valido nel file STL: {count}",
        "worker.error.loading_failed": "Errore nel worker di caricamento STL: {error}",
        "worker.error.cleanup_failed": "Errore durante la chiusura del processore STL: {error}",
        "worker.info.stl_loading_started": "Avvio del worker di caricamento STL",
        "worker.info.total_triangles": "Triangoli totali da elaborare: {count}",
        "worker.info.loading_cancelled": "Caricamento annullato dall'utente",
        "worker.info.loading_complete": "Caricamento STL completato con successo",
        "worker.status.loading_stl": "Caricamento STL... {progress:.1f}%",
        
        "worker.debug.stl_header": "Intestazione STL: {header}",
        "worker.debug.starting_triangle_iteration": "Avvio iterazione triangoli...",
        "worker.debug.emitting_chunk": "Invio blocco con {triangles} triangoli, avanzamento: {progress:.1f}%",
        "worker.debug.loading_cancellation_requested": "Annullamento del caricamento STL richiesto",
        "worker.warning.no_stl_header": "Il processore STL non ha l'attributo _header",
        
        # Progress module
        "progress": {
            "ui": {
                "loading": "Loading...",
                "loading_progress": "Loading: {progress}%"
            },
            "log": {
                "progress": "Loading progress: {progress}%"
            },
            "errors": {
                "invalid_progress_value": "Invalid progress value: {progress} - {error}",
                "update_error": "Error updating progress dialog: {error}",
                "reset_error": "Error resetting progress dialog: {error}"
            }
        },
        
        # Settings Dialog Translations
        "settings_dialog.title": "Impostazioni",
        
        # Tab names
        "settings_dialog.tabs.general": "Generale",
        "settings_dialog.tabs.path_optimization": "Ottimizzazione Percorso",
        "settings_dialog.tabs.infill": "Riempimento",
        "settings_dialog.tabs.advanced": "Avanzate",
        
        # Group box titles
        "settings_dialog.general.title": "Impostazioni Generali",
        "settings_dialog.path_optimization.title": "Impostazioni Ottimizzazione Percorso",
        "settings_dialog.infill.title": "Impostazioni Riempimento",
        "settings_dialog.advanced.title": "Impostazioni Avanzate",
        "settings_dialog.gcode.title": "G-code",
        
        # General settings
        "settings_dialog.general.layer_height": "Altezza Strato (mm):",
        "settings_dialog.general.print_speed": "Velocità Stampa (mm/s):",
        "settings_dialog.general.travel_speed": "Velocità Spostamento (mm/s):",
        "settings_dialog.general.retraction_length": "Lunghezza Ritrazione (mm):",
        
        # Path optimization settings
        "settings_dialog.path_optimization.enable": "Abilita Ottimizzazione Percorso:",
        "settings_dialog.path_optimization.enable_arcs": "Rilevamento Archi:",
        "settings_dialog.path_optimization.arc_tolerance": "Tolleranza Archi (mm):",
        "settings_dialog.path_optimization.min_arc_segments": "Segmenti Minimi Arco:",
        "settings_dialog.path_optimization.remove_redundant": "Rimuovi Movimenti Ridondanti:",
        "settings_dialog.path_optimization.combine_coincident": "Combina Movimenti Sovrapposti:",
        "settings_dialog.path_optimization.optimize_travel": "Ottimizza Spostamenti a Vuoto:",
        
        # Infill settings
        "settings_dialog.infill.density": "Densità (%):",
        "settings_dialog.infill.pattern": "Modello:",
        "settings_dialog.infill.patterns.grid": "Griglia",
        "settings_dialog.infill.patterns.lines": "Linee",
        "settings_dialog.infill.patterns.triangles": "Triangoli",
        "settings_dialog.infill.patterns.trihexagon": "Tri-esagonale",
        "settings_dialog.infill.patterns.cubic": "Cubico",
        "settings_dialog.infill.angle": "Angolo (gradi):",
        "settings_dialog.infill.enable_optimized": "Abilita Riempimento Ottimizzato:",
        "settings_dialog.infill.resolution": "Risoluzione (mm):",
        
        # Advanced settings
        "settings_dialog.advanced.extrusion_width": "Larghezza Estrusione (mm):",
        "settings_dialog.advanced.filament_diameter": "Diametro Filamento (mm):",
        "settings_dialog.advanced.first_layer_height": "Altezza Primo Strato (mm):",
        "settings_dialog.advanced.first_layer_speed": "Velocità Primo Strato (mm/s):",
        "settings_dialog.advanced.z_hop": "Sollevamento Z (mm):",
        "settings_dialog.advanced.skirt_line_count": "Numero Linee Gonna:",
        "settings_dialog.advanced.skirt_distance": "Distanza Gonna (mm):",
        "settings_dialog.advanced.temperature": "Nozzle Temperature (°C):",
        "settings_dialog.advanced.bed_temperature": "Bed Temperature (°C):",
        "settings_dialog.advanced.fan_speed": "Fan Speed (%):",
        "settings_dialog.advanced.fan_layer": "Fan Start Layer:",
        
        # G-code settings
        "settings_dialog.gcode.start": "G-code Iniziale:",
        "settings_dialog.gcode.end": "G-code Finale:",
        "settings_dialog.gcode.start_placeholder": "; G-code iniziale (inserito all'inizio del file)\nG28 ; Home assi\nG1 Z5 F5000 ; Solleva ugello\nM104 S{material_print_temperature} ; Imposta temperatura ugello\nM190 S{material_bed_temperature} ; Attendi temperatura piatto\nM109 S{material_print_temperature} ; Attendi temperatura ugello\nG92 E0 ; Azzera estrusore\nG1 E-1 F300 ; Ritrai leggermente\nG1 Z0.4 F3000 ; Solleva ugello\nG1 X3.2 F5000 ; Posizione iniziale\nG1 Y100.0 Z0.3 F1500.0 E15 ; Primo movimento\nG1 X3.2 Y20.2 Z0.3 F1500.0 E30 ; Secondo movimento\nG92 E0 ; Azzera estrusore\nG1 Z2.0 F3000 ; Solleva Z",
        "settings_dialog.gcode.end_placeholder": "; G-code finale\nM104 S0 ; Spegni ugello\nM140 S0 ; Spegni piatto\nG91 ; Posizionamento relativo\nG1 E-1 F300 ; Ritrai filamento\nG1 Z+5 E-5 F3000 ; Solleva e ritrai\nG90 ; Posizionamento assoluto\nG28 X0 ; Home asse X\nM84 ; Disabilita motori",
        
        # Reset confirmation
        "settings_dialog.reset_title": "Ripristina Impostazioni",
        "settings_dialog.reset_confirm": "Sei sicuro di voler ripristinare tutte le impostazioni ai valori predefiniti?",
        
        # Configuration
        "config.error_loading": "Errore durante il caricamento della configurazione: {error}",
        "config.error_saving": "Errore durante il salvataggio della configurazione: {error}",
        
        # About Dialog Translations
        "about.title": "Informazioni su STL to G-Code Converter",
        "about.app_name": "Convertitore STL in G-Code",
        "about.version": "Versione: {version}",
        "about.copyright": " 2025 Nsfr750",
        "about.description": (
            "Un'applicazione avanzata per convertire file STL in G-code per la stampa 3D.\n\n"
            "Questo strumento offre funzionalità avanzate per la preparazione di modelli 3D e "
            "l'ottimizzazione del G-code per garantire stampe 3D di alta qualità."
        ),
        "about.system_info": "Informazioni di Sistema",
        "about.os": "Sistema Operativo: {os_name} {os_version}",
        "about.python": "Python: {python_version}",
        "about.qt": "Qt: {qt_version}",
        "about.pyqt": "PyQt: {pyqt_version}",
        "about.cpu": "CPU: {cpu_info}",
        "about.memory": "Memoria: {memory:.2f} GB",
        "about.gpu": "GPU: {gpu_info}",
        "about.buttons.github": "GitHub",
        "about.buttons.documentation": "Documentazione",
        "about.buttons.license": "Licenza",
        "about.buttons.close": "Chiudi",
        "about.buttons.check_updates": "Cerca Aggiornamenti",
        "about.links.website": "Sito Web",
        "about.links.issues": "Segnala Problemi",
        "about.links.donate": "Dona",
        "about.credits.title": "Crediti",
        "about.credits.developer": "Sviluppatore: {author}",
        "about.credits.contributors": "Collaboratori",
        "about.credits.libraries": "Librerie Utilizzate",
        "about.credits.licenses": "Open Source Licenses",
        
        # About Dialog - Additional Keys
        "about.urls.github": "https://github.com/Nsfr750/STL_to_G-Code",
        "about.urls.documentation": "https://github.com/Nsfr750/STL_to_G-Code/wiki",
        
        "about.license_title": "Informazioni sulla Licenza",
        "about.license": "Licenza Pubblica Generica GNU v3.0",
        "about.license_text": (
            "Questo programma è un software libero: puoi ridistribuirlo e/o modificarlo\n"
            "secondo i termini della GNU General Public License così come pubblicata dalla\n"
            "Free Software Foundation, sia la versione 3 della Licenza, o (a tua scelta)\n"
            "qualsiasi versione successiva.\n\n"
            "Questo programma è distribuito nella speranza che possa essere utile,\n"
            "ma SENZA ALCUNA GARANZIA; senza nemmeno la garanzia implicita di\n"
            "COMMERCIABILITÀ o IDONEITÀ PER UN PARTICOLARE SCOPO. Vedere la\n"
            "GNU General Public License per maggiori dettagli.\n\n"
            "Dovresti aver ricevuto una copia della GNU General Public License\n"
            "insieme a questo programma. In caso contrario, vedi <https://www.gnu.org/licenses/>."
        ),
        
        "about.update_error_title": "Errore Aggiornamento",
        "about.update_error_message": "Si è verificato un errore durante il controllo degli aggiornamenti: {error}",
        
        "about.cores": "Core CPU",
        "about.available": "disponibile",
        "about.error_loading_system_info": "Errore nel caricamento delle informazioni di sistema",
        
        # STL Loading
        "stl.loading.open_dialog_title": "Apri file STL",
        "stl.loading.file_filter": "File STL (*.stl)",
        "stl.loading.no_file_selected": "Nessun file selezionato",
        "stl.loading.file_not_found": "File non trovato: {file_path}",
        "stl.loading.operation_cancelled": "Operazione annullata dall'utente",
        "stl.loading.error_opening": "Errore durante l'apertura del file STL: {error}",
        "stl.loading.failed_to_open": "Impossibile aprire il file: {file_path}\n\nErrore: {error_msg}",
        "stl.loading.error_metadata": "Errore durante il recupero dei metadati STL: {error}",
        "stl.loading.large_file_title": "Avviso file di grandi dimensioni",
        "stl.loading.large_file_message": "Il file selezionato è di grandi dimensioni ({size_mb:.1f} MB). L'elaborazione potrebbe richiedere del tempo. Continuare?",
        "stl.loading.error_title": "Errore durante l'apertura del file",
        
        # Error Handling
        "error_handling.no_error_message": "Nessun messaggio di errore disponibile",
        "error_handling.error_dialog_title": "Errore",
        "error_handling.permission_denied": "Permesso negato durante il tentativo di {operation} '{file_name}'",
        "error_handling.file_not_found": "File non trovato: {file_name}",
        "error_handling.expected_file_found_dir": "Atteso un file ma trovata una cartella: {file_name}",
        "error_handling.file_in_use": "Impossibile {operation} '{file_name}': Il file è in uso da un altro processo",
        "error_handling.file_operation_error": "Errore durante {operation} del file '{file_name}': {error}",
        "error_handling.default_warning_title": "Avviso",
        "error_handling.default_info_title": "Informazione",
        "error_handling.default_confirm_title": "Conferma",
        
        # G-code Loading
        "gcode.loading.open_dialog_title": "Apri file G-code",
        "gcode.loading.file_filter": "File G-code (*.gcode *.nc *.tap);;Tutti i file (*)",
        "gcode.loading.file_not_found": "File non trovato: {file_path}",
        "gcode.loading.large_file_detected": "Rilevato file G-code di grandi dimensioni: {size_mb:.2f}MB",
        "gcode.loading.large_file_title": "Avviso file di grandi dimensioni",
        "gcode.loading.large_file_message": "Questo file G-code è di {size_mb:.2f}MB. Il caricamento di file di grandi dimensioni potrebbe richiedere tempo e consumare molta memoria.\n\nVuoi continuare?",
        "gcode.loading.operation_canceled": "Operazione annullata",
        "gcode.loading.no_file_selected": "Nessun file selezionato",
        "gcode.loading.user_canceled": "L'utente ha annullato il caricamento del file di grandi dimensioni",
        "gcode.loading.loading_file": "Caricamento file G-code: {file_path}",
        "gcode.loading.success": "File G-code caricato con successo: {file_name} ({file_size} byte, {line_count} righe)",
        "gcode.loading.permission_denied": "Permesso negato durante l'accesso al file: {file_path}",
        "gcode.loading.io_error": "Errore durante la lettura del file: {file_path}",
        "gcode.loading.unexpected_error": "Errore imprevisto durante il caricamento del file: {file_path}",
        
        # G-code Optimizer
        "gcode_optimizer.error.optimized_infill": "Errore in generate_optimized_infill: {error}",
        "gcode_optimizer.error.invalid_command": "Comando G-code non valido: {command} alla riga {line_num}",
        "gcode_optimizer.error.missing_variable_start": "Variabile mancante nel G-code di inizio: {error}",
        "gcode_optimizer.error.invalid_start_gcode": "Errore nel G-code di inizio: {error}",
        "gcode_optimizer.error.unsupported_mesh_format": "Formato mesh non supportato. Previsto trimesh object o dictionary con chiave 'vertices'.",
        "gcode_optimizer.error.generating_gcode": "Errore durante la generazione del G-code: {error}",
        "gcode_optimizer.error.missing_variable_end": "Variabile mancante nel G-code di fine: {error}",
        "gcode_optimizer.error.invalid_end_gcode": "Errore nel G-code di fine: {error}",
        "gcode_optimizer.error.unsupported_mesh_with_faces": "Formato mesh non supportato. Previsto trimesh object o dictionary con chiavi 'vertices' e 'faces'.",
        "gcode_optimizer.error.no_face_info": "Impossibile determinare le informazioni sulle facce dalla mesh",
        
        # G-code Comments
        "gcode_optimizer.comment.custom_start_code": "--- G-code personalizzato di inizio ---",
        "gcode_optimizer.comment.end_start_code": "--- Fine del G-code personalizzato di inizio ---",
        "gcode_optimizer.comment.custom_end_code": "--- G-code personalizzato di fine ---",
        "gcode_optimizer.comment.end_end_code": "--- Fine del G-code personalizzato di fine ---",
        "gcode_optimizer.comment.layer_z": "--- Strato a Z={z} ---",
        "gcode_optimizer.comment.move_to_layer": "Sposta all'altezza dello strato",
        "gcode_optimizer.comment.infill_section": "--- Riempimento ---",
        "gcode_optimizer.comment.set_infill_speed": "Imposta velocità di riempimento",
        "gcode_optimizer.comment.move_to_start": "Sposta all'inizio",
        "gcode_optimizer.comment.draw_infill_line": "Disegna linea di riempimento",
        
        # Retraction Comments
        "gcode_optimizer.retract.retract": "ritrazione",
        "gcode_optimizer.retract.unretract": "estrusione",
        
        # Logging
        "logging": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "config_success": "Configurazione del logging completata con successo",
            "file_creation_failed": "Impossibile creare il file di log: {error}. Verranno mostrati solo i messaggi nella console.",
            "log_viewer": {
                "title": "Visualizzatore Log",
                "filter_placeholder": "Filtra log...",
                "clear_confirm": "Sei sicuro di voler cancellare tutti i messaggi di log?",
                "clear_button": "Pulisci Log",
                "save_button": "Salva Log",
                "save_title": "Salva File di Log",
                "save_success": "Log salvato con successo in {path}",
                "save_failed": "Impossibile salvare il file di log: {error}",
                "level_debug": "Debug",
                "level_info": "Informazioni",
                "level_warning": "Avviso",
                "level_error": "Errore",
                "level_critical": "Critico"
            }
        },
        
        # UI Elements
        "ui": {
            # Buttons
            "buttons": {
                "open": "Apri",
                "save": "Salva",
                "save_as": "Salva con nome",
                "run": "Esegui",
                "stop": "Ferma",
                "settings": "Impostazioni",
                "about": "Informazioni",
                "exit": "Esci",
                "browse": "Sfoglia...",
                "add": "Aggiungi",
                "remove": "Rimuovi",
                "clear": "Pulisci",
                "apply": "Applica",
                "cancel": "Annulla",
                "ok": "OK",
                "reset": "Reimposta",
                "help": "Aiuto"
            },
            
            # Labels
            "labels": {
                "input_file": "File di input:",
                "output_file": "File di output:",
                "no_file_selected": "Nessun file selezionato",
                "status": "Stato:",
                "progress": "Avanzamento:",
                "ready": "Pronto",
                "processing": "Elaborazione in corso...",
                "complete": "Completato",
                "error": "Errore",
                "warning": "Attenzione",
                "info": "Informazione"
            },
            
            # Tooltips
            "tooltips": {
                "open_file": "Apri un file STL da elaborare",
                "save_file": "Salva il G-code generato in un file",
                "run_conversion": "Avvia il processo di conversione",
                "stop_conversion": "Interrompi l'operazione corrente"
            },
            
            # Messages
            "messages": {
                "file_opened": "File aperto: {filename}",
                "file_saved": "File salvato: {filename}",
                "conversion_complete": "Conversione completata con successo",
                "conversion_failed": "Conversione fallita: {error}",
                "no_file_selected": "Selezionare prima un file di input",
                "invalid_file": "Formato file non valido. Selezionare un file STL.",
                "processing_file": "Elaborazione file: {filename}",
                "saving_file": "Salvataggio in: {filename}"
            },
            
            # Settings
            "settings": {
                "title": "Impostazioni",
                "general": "Generale",
                "appearance": "Aspetto",
                "language": "Lingua:",
                "theme": "Tema:",
                "dark": "Scuro",
                "light": "Chiaro",
                "system": "Sistema",
                "units": "Unità di misura:",
                "millimeters": "Millimetri (mm)",
                "inches": "Pollici (in)",
                "precision": "Precisione:",
                "decimal_places": "{n} cifre decimali"
            },
            
            # Menu items
            "menu": {
                "file": "&File",
                "edit": "&Modifica",
                "view": "&Visualizza",
                "tools": "&Strumenti",
                "help": "&Aiuto"
            },
            
            # File menu
            "file_menu": {
                "new": "&Nuovo",
                "open": "&Apri...",
                "save": "&Salva",
                "save_as": "Salva &con nome...",
                "recent_files": "File recenti",
                "exit": "&Esci"
            },
            
            # Edit menu
            "edit_menu": {
                "undo": "&Annulla",
                "redo": "&Ripeti",
                "cut": "Ta&glia",
                "copy": "&Copia",
                "paste": "I&ncolla",
                "delete": "&Elimina",
                "select_all": "Seleziona &tutto"
            },
            
            # View menu
            "view_menu": {
                "toolbar": "Barra &strumenti",
                "statusbar": "Barra di &stato",
                "fullscreen": "&Schermo intero",
                "zoom_in": "Ingrandisci",
                "zoom_out": "Riduci",
                "reset_zoom": "&Ripristina zoom"
            },
            
            # Help menu
            "help_menu": {
                "documentation": "&Documentazione",
                "check_updates": "Verifica a&ggiornamenti",
                "about": "&Informazioni"
            },
            
            # About dialog
            "about": {
                "title": "Informazioni su STL a G-Code",
                "version": "Versione {version}",
                "description": "Uno strumento per convertire modelli 3D STL in G-code per macchine CNC.",
                "copyright": " 2025 Nsfr750",
                "license": "Distribuito con licenza GPLv3."
            }
        },
        
        # Help Dialog
        "help.dialog.title": "Aiuto - STL a G-Code",
        "help.buttons.full_documentation": "Documentazione Completa",
        "help.tooltips.full_documentation": "Apri la documentazione completa nel browser web",
        "common.buttons.close": "Chiudi",
        
        # Help Content
        "help.title": "Aiuto per STL a G-Code",
        
        # Overview Section
        "help.overview.title": "Panoramica",
        "help.overview.description": "STL a G-Code è un potente strumento per convertire modelli 3D (file STL) in G-code per la stampa 3D.",
        
        # Getting Started Section
        "help.getting_started.title": "Per Iniziare",
        "help.getting_started.step1": "1. Apri un file STL utilizzando File > Apri STL o trascina e rilascia un file",
        "help.getting_started.step2": "2. Regola le impostazioni di stampa secondo necessità",
        "help.getting_started.step3": "3. Fai clic su 'Converti in G-code' per generare il G-code",
        "help.getting_started.step4": "4. Anteprima del G-code generato e apporta modifiche se necessario",
        "help.getting_started.step5": "5. Salva il G-code in un file o invialo direttamente alla tua stampante 3D",
        
        # Features Section
        "help.features.title": "Caratteristiche",
        
        # File Management Features
        "help.features.file_management.title": "Gestione File",
        "help.features.file_management.item1": "• Apri e visualizza file STL",
        "help.features.file_management.item2": "• Salva ed esporta G-code",
        "help.features.file_management.item3": "• Elenco file recenti",
        "help.features.file_management.item4": "• Importa/esporta profili di impostazioni",
        "help.features.file_management.item5": "• Supporto per trascinamento",
        
        # Visualization Features
        "help.features.visualization.title": "Visualizzazione 3D",
        "help.features.visualization.item1": "• Anteprima interattiva del modello 3D",
        "help.features.visualization.item2": "• Visualizzazione strato per strato",
        "help.features.visualization.item3": "• Modalità di visualizzazione multiple (solido, wireframe, ecc.)",
        "help.features.visualization.item4": "• Controlli per zoom, panoramica e rotazione",
        "help.features.visualization.item5": "• Strumenti di misurazione",
        
        # G-code Tools
        "help.features.gcode_tools.title": "Strumenti G-code",
        "help.features.gcode_tools.item1": "• Editor G-code con evidenziazione della sintassi",
        "help.features.gcode_tools.item2": "• Validazione e analisi G-code",
        "help.features.gcode_tools.item3": "• Ottimizza il G-code per una migliore qualità di stampa",
        "help.features.gcode_tools.item4": "• Anteprima dell'esecuzione del G-code",
        "help.features.gcode_tools.item5": "• Script G-code personalizzati per inizio/fine",
        
        # Documentation
        "help.features.documentation.title": "Documentazione",
        "help.features.documentation.item1": "• Sistema di aiuto integrato",
        "help.features.documentation.item2": "• Suggerimenti e descrizioni nell'interfaccia",
        "help.features.documentation.item3": "• Documentazione e tutorial online",
        "help.features.documentation.item4": "• Riferimento alle scorciatoie da tastiera",
        
        # Advanced Features
        "help.features.advanced.title": "Funzionalità Avanzate",
        "help.features.advanced.item1": "• Profili di stampa personalizzabili",
        "help.features.advanced.item2": "• Supporto per più estrusori",
        "help.features.advanced.item3": "• Modelli di riempimento avanzati",
        "help.features.advanced.item4": "• Supporto per script di post-elaborazione personalizzati",
        "help.features.advanced.item5": "• Sistema di plugin per estendere le funzionalità",
        
        # Keyboard Shortcuts
        "help.shortcuts.title": "Scorciatoie da Tastiera",
        "help.shortcuts.ctrl_o": "Ctrl+O",
        "help.shortcuts.ctrl_o_desc": "Apri file STL",
        "help.shortcuts.ctrl_s": "Ctrl+S",
        "help.shortcuts.ctrl_s_desc": "Salva G-code",
        "help.shortcuts.f1": "F1",
        "help.shortcuts.f1_desc": "Mostra questa finestra di aiuto",
        "help.shortcuts.ctrl_q": "Ctrl+Q",
        "help.shortcuts.ctrl_q_desc": "Esci dall'applicazione",
        "help.shortcuts.ctrl_l": "Ctrl+L",
        "help.shortcuts.ctrl_l_desc": "Mostra il visualizzatore di log",
        "help.shortcuts.ctrl_g": "Ctrl+G",
        "help.shortcuts.ctrl_g_desc": "Visualizza l'editor G-code",
        
        # Italian translations for G-code Optimizer
        "gcode_optimizer.error.optimized_infill": "Errore in generate_optimized_infill: {error}",
        "gcode_optimizer.error.invalid_command": "Comando G-code non valido: {command} alla riga {line_num}",
        "gcode_optimizer.error.missing_variable_start": "Variabile mancante nel G-code di inizio: {error}",
        "gcode_optimizer.error.invalid_start_gcode": "Errore nel G-code di inizio: {error}",
        "gcode_optimizer.error.unsupported_mesh_format": "Formato mesh non supportato. Previsto trimesh object o dictionary con chiave 'vertices'.",
        "gcode_optimizer.error.generating_gcode": "Errore durante la generazione del G-code: {error}",
        "gcode_optimizer.error.missing_variable_end": "Variabile mancante nel G-code di fine: {error}",
        "gcode_optimizer.error.invalid_end_gcode": "Errore nel G-code di fine: {error}",
        "gcode_optimizer.error.unsupported_mesh_with_faces": "Formato mesh non supportato. Previsto trimesh object o dictionary con chiavi 'vertices' e 'faces'.",
        "gcode_optimizer.error.no_face_info": "Impossibile determinare le informazioni sulle facce dalla mesh",
        
        # Italian translations for G-code Comments
        "gcode_optimizer.comment.custom_start_code": "--- G-code personalizzato di inizio ---",
        "gcode_optimizer.comment.end_start_code": "--- Fine del G-code personalizzato di inizio ---",
        "gcode_optimizer.comment.custom_end_code": "--- G-code personalizzato di fine ---",
        "gcode_optimizer.comment.end_end_code": "--- Fine del G-code personalizzato di fine ---",
        "gcode_optimizer.comment.layer_z": "--- Strato a Z={z} ---",
        "gcode_optimizer.comment.move_to_layer": "Sposta all'altezza dello strato",
        "gcode_optimizer.comment.infill_section": "--- Riempimento ---",
        "gcode_optimizer.comment.set_infill_speed": "Imposta velocità di riempimento",
        "gcode_optimizer.comment.move_to_start": "Sposta all'inizio",
        "gcode_optimizer.comment.draw_infill_line": "Disegna linea di riempimento",
        
        # Italian translations for Retraction Comments
        "gcode_optimizer.retract.retract": "ritrazione",
        "gcode_optimizer.retract.unretract": "estrusione",
                
        # Support Section
        "help.support.title": "Supporto",
        "help.support.description": "Per ulteriore assistenza, visita la nostra documentazione o contatta il supporto.",
    },
}


# Backward compatibility function
def t(key: str, lang_code: str = "en", **kwargs) -> str:
    """
    Get a translated string for the given key and language.

    Note: This is kept for backward compatibility. New code should use LanguageManager.

    Args:
        key: The translation key
        lang_code: Language code (default: 'en')
        **kwargs: Format arguments for the translation string

    Returns:
        str: The translated string or the key if not found
    """
    try:
        translation = TRANSLATIONS.get(lang_code, {}).get(
            key, TRANSLATIONS.get("en", {}).get(key, key)
        )
        if isinstance(translation, str) and kwargs:
            return translation.format(**kwargs)
        return translation
    except Exception as e:
        print(f"Translation error for key '{key}': {e}")
        return key
