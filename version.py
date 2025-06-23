"""
Version management module for STL to GCode Converter.

This module implements version tracking and management according to
Semantic Versioning 2.0.0 (https://semver.org/). It provides:
- Version number components (major, minor, patch)
- Version qualifier support (alpha, beta, rc)
- Version string generation
- Version compatibility checking
- Version information dictionary
"""

# Version components following Semantic Versioning 2.0.0
# MAJOR version when you make incompatible API changes
# MINOR version when you add functionality in a backwards compatible manner
# PATCH version when you make backwards compatible bug fixes
VERSION_MAJOR = 1
VERSION_MINOR = 2
VERSION_PATCH = 0

# Version qualifier (pre-release identifier)
# Can be 'alpha', 'beta', 'rc' (release candidate), or empty string for final release
VERSION_QUALIFIER = ''

def get_version():
    """
    Generate the full version string in semantic versioning format.
    
    Returns:
        str: Formatted version string (e.g., "1.1.0-beta")
    """
    version_parts = [str(VERSION_MAJOR), str(VERSION_MINOR), str(VERSION_PATCH)]
    version_str = '.'.join(version_parts)
    
    if VERSION_QUALIFIER:
        version_str += f'-{VERSION_QUALIFIER}'
    
    return version_str

def get_version_info():
    """
    Get detailed version information as a dictionary.
    
    Returns:
        dict: Dictionary containing:
            - major: Major version number
            - minor: Minor version number
            - patch: Patch version number
            - qualifier: Version qualifier (alpha/beta/rc)
            - full_version: Complete version string
    """
    return {
        'major': VERSION_MAJOR,
        'minor': VERSION_MINOR,
        'patch': VERSION_PATCH,
        'qualifier': VERSION_QUALIFIER,
        'full_version': get_version()
    }

def check_version_compatibility(min_version):
    """
    Check if the current version is compatible with a minimum required version.
    
    Args:
        min_version (str): Minimum version requirement (e.g., "1.0.0")
    
    Returns:
        bool: True if the current version meets or exceeds the minimum version,
              False if it's lower than the minimum version
    """
    current_parts = [VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH]
    min_parts = [int(part) for part in min_version.split('.')]
    
    # Compare each version component
    for current, minimum in zip(current_parts, min_parts):
        if current > minimum:
            return True
        elif current < minimum:
            return False
    
    return True

# Expose version as a module-level attribute for easy access
# This allows other modules to import version directly: from version import __version__
__version__ = get_version()
