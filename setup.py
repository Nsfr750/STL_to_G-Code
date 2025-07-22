"""
Setup script for STL to GCode Converter.
"""

import os
import sys
from setuptools import setup, find_packages
from scripts import version
from pathlib import Path

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

def get_requirements():
    """Load requirements from requirements.txt."""
    requirements_path = this_directory / 'requirements.txt'
    with open(requirements_path, 'r', encoding='utf-8') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith(("#", "--"))
        ]

# Package data files
package_data = {
    '': ['*.ui', '*.qss', '*.css', '*.png', '*.ico', '*.icns', '*.md'],
    'scripts.assets': ['assets/*.png', 'assets/*.ico', 'assets/*.icns'],
    '': ['LICENSE', 'CHANGELOG.md', 'PREREQUISITES.md', 'CONTRIBUTING.md'],
}

# Platform-specific options
options = {
    'py2exe': {
        'includes': [
            'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
            'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore',
            'PyQt6.QtPrintSupport', 'PyQt6.Qsci'
        ],
        'packages': [
            'numpy', 'matplotlib', 'numpy_stl', 'scipy', 'Pillow',
            'markdown', 'pygments', 'requests', 'packaging', 'python_dateutil',
            'six', 'scikit_image', 'opencv_python_headless'
        ],
        'excludes': ['tkinter'],
        'bundle_files': 1,
        'compressed': True,
        'optimize': 2,
        'dll_excludes': ['w9xpopen.exe'],
        'includes': ['sip'],
        'include_files': [
            ('scripts/assets/icon.png', 'scripts/assets/icon.png'),
            'LICENSE', 'CHANGELOG.md', 'PREREQUISITES.md', 'CONTRIBUTING.md'
        ]
    },
    'py2app': {
        'argv_emulation': True,
        'iconfile': 'scripts/assets/icon.icns',
        'packages': [
            'PyQt6', 'numpy', 'matplotlib', 'numpy_stl', 'scipy', 'Pillow',
            'markdown', 'pygments', 'requests', 'packaging', 'python_dateutil',
            'six', 'scikit_image', 'opencv_python_headless', 'scripts'
        ],
        'plist': {
            'CFBundleName': 'STL to GCode',
            'CFBundleDisplayName': 'STL to GCode Converter',
            'CFBundleVersion': version.__version__,
            'CFBundleShortVersionString': version.__version__,
            'NSHumanReadableCopyright': 'Copyright 2024 Nsfr750. All rights reserved.',
            'NSMicrophoneUsageDescription': 'Not used',
            'NSCameraUsageDescription': 'Not used',
            'NSDocumentsFolderUsageDescription': 'Used to open and save files',
            'NSDownloadsFolderUsageDescription': 'Used to download files',
            'NSDesktopFolderUsageDescription': 'Used to access the desktop',
        },
        'resources': [
            'scripts/assets/icon.png',
            'LICENSE', 'CHANGELOG.md', 'PREREQUISITES.md', 'CONTRIBUTING.md'
        ],
    }
}

# Development requirements
extras_require = {
    'dev': [
        'black>=23.11.0',
        'flake8>=6.1.0',
        'pytest>=7.4.3',
        'pytest-qt>=4.2.0',
        'mypy>=1.7.0',
        'sphinx>=7.2.0',
        'sphinx-rtd-theme>=1.3.0',
    ],
    'test': [
        'pytest>=7.4.3',
        'pytest-qt>=4.2.0',
        'pytest-cov>=4.1.0',
    ],
    'docs': [
        'sphinx>=7.2.0',
        'sphinx-rtd-theme>=1.3.0',
        'sphinx-copybutton>=0.5.2',
        'myst-parser>=2.0.0',
    ]
}

setup(
    name="stl-to-gcode",
    version=version.__version__,
    author="Nsfr750",
    author_email="nsfr750@yandex.com",
    description="Convert STL files to G-code for 3D printing and CNC machining",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nsfr750/STL_to_G-Code",
    project_urls={
        'Bug Reports': 'https://github.com/Nsfr750/STL_to_G-Code/issues',
        'Source': 'https://github.com/Nsfr750/STL_to_G-Code',
        'Documentation': 'https://github.com/Nsfr750/STL_to_G-Code#readme',
    },
    packages=find_packages(include=['scripts', 'scripts.*']),
    package_dir={'': '.'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: User Interfaces',
    ],
    python_requires='>=3.8',
    package_data=package_data,
    include_package_data=True,
    install_requires=get_requirements(),
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'stl-to-gcode=scripts.main:main',
        ],
        'gui_scripts': [
            'stl-to-gcode-gui=scripts.main:main',
        ],
    },
    options=options,
    zip_safe=False,
    license='GPLv3',
    keywords='stl gcode 3d-printing cnc converter',
    platforms=['Windows', 'macOS', 'Linux'],
)
