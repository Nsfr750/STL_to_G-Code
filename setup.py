"""
Setup script for STL to GCode Converter.
"""

from setuptools import setup, find_packages
from scripts import version
import sys
import 
from scripts.logger import get_loggeros

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith(("#", "--"))
    ]

# Get package data files
def get_package_data(package, data_dir):
    package_path = os.path.join(package, data_dir)
    walk = [(dir_path.replace(package_path, data_dir).lstrip(os.sep), filenames)
            for dir_path, _, filenames in os.walk(package_path)
            if filenames]
    file_dict = {}
    for dir_path, filenames in walk:
        if dir_path not in file_dict:
            file_dict[dir_path] = []
        for filename in filenames:
            file_dict[dir_path].append(os.path.join(dir_path, filename))
    return file_dict

package_data = {
    '': ['*.ui', '*.qss', '*.css', '*.png', '*.ico', '*.icns'],
    'scripts.assets': ['assets/*.png', 'assets/*.ico', 'assets/*.icns'],
}

# Platform-specific options
options = {
    'py2exe': {
        'includes': ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
        'packages': ['numpy', 'matplotlib', 'numpy-stl', 'scripts'],
        'excludes': ['tkinter'],
        'bundle_files': 1,
        'compressed': True,
        'optimize': 2,
        'dll_excludes': ['w9xpopen.exe'],
        'includes': ['sip'],
        'include_files': [
            ('scripts/assets/icon.png', 'scripts/assets/icon.png')
        ]
    },
    'py2app': {
        'argv_emulation': True,
        'iconfile': 'scripts/assets/icon.icns',
        'packages': ['PyQt6', 'numpy', 'matplotlib', 'numpy-stl', 'scripts'],
        'plist': {
            'CFBundleName': 'STL to GCode',
            'CFBundleDisplayName': 'STL to GCode Converter',
            'CFBundleVersion': version.__version__,
            'CFBundleShortVersionString': version.__version__,
            'NSHumanReadableCopyright': 'Copyright 2024 Nsfr750. All rights reserved.',
        },
        'resources': ['scripts/assets/icon.png'],
    }
}

setup(
    name="stl-to-gcode",
    version=version.__version__,
    author="Nsfr750",
    author_email="",
    description="Convert STL files to G-code for 3D printing and CNC machining",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nsfr750/STL_to_G-Code",
    packages=find_packages(include=['scripts', 'scripts.*']),
    package_dir={'': '.'},  # look for packages in the root
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Topic :: Scientific/Engineering",
    ],
    python_requires='>=3.8',
    package_data=package_data,
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'stl-to-gcode=main_qt:main',
        ],
    },
    options=options,
    data_files=[
        ('scripts/assets', ['scripts/assets/icon.png']),
    ],
    app=['main_qt.py'],
    setup_requires=['py2app'] if sys.platform == 'darwin' else [],
    project_urls={
        'Bug Reports': 'https://github.com/Nsfr750/STL_to_G-Code/issues',
        'Source': 'https://github.com/Nsfr750/STL_to_G-Code',
    },
    keywords=[
        '3D printing', 'CNC', 'G-code', 'STL', '3D modeling',
        'manufacturing', 'slicer', '3D printer', 'CAD/CAM'
    ],
)
