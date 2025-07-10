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
VERSION_MAJOR = 2
VERSION_MINOR = 0
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
    version = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
    if VERSION_QUALIFIER:
        version += f"-{VERSION_QUALIFIER}"
    return version

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
    def parse_version(version_str):
        # Remove any pre-release identifiers for comparison
        base_version = version_str.split('-')[0]
        return tuple(map(int, base_version.split('.')))
    
    try:
        current = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
        required = parse_version(min_version)
        return current >= required
    except (ValueError, IndexError, AttributeError):
        return False

# Expose version as a module-level attribute for easy access
# This allows other modules to import version directly: from scripts.version import __version__
__version__ = get_version()

# For testing
if __name__ == "__main__":
    print(f"Version: {get_version()}")
    print(f"Version info: {get_version_info()}")
    print(f"Compatible with 1.0.0: {check_version_compatibility('1.0.0')}")
    print(f"Compatible with 2.0.0: {check_version_compatibility('2.0.0')}")
