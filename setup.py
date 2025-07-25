from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stl-to-gcode",
    version="2.1.0",
    author="Nsfr750",
    author_email="nsfr750@yandex.com",
    description="A powerful Python application for converting STL files to G-code for 3D printing and CNC machining",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nsfr750/STL_to_G-Code",
    packages=find_packages(include=['scripts*']),
    package_dir={"": "."},
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.6.0",
        "PyQt6-WebEngine>=6.6.0",
        "numpy>=1.26.0",
        "numpy-stl>=3.1.0",
        "scipy>=1.12.0",
        "scikit-image>=0.22.0",
        "matplotlib>=3.8.0",
        "wand>=0.6.13",
        "markdown>=3.5.0",
        "pygments>=2.16.0",
        "pymdown-extensions>=10.0.0",
        "requests>=2.31.0",
        "packaging>=23.2",
        "urllib3>=2.0.7",
        "python-dateutil>=2.8.2",
        "six>=1.16.0",
    ],
    entry_points={
        'console_scripts': [
            'stl-to-gcode=scripts.main:main',
        ],
        'gui_scripts': [
            'stl-to-gcode-gui=scripts.main:main',
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Topic :: Scientific/Engineering",
    ],
    python_requires='>=3.8,<3.14',
    project_urls={
        "Homepage": "https://github.com/Nsfr750/STL_to_G-Code",
        "Documentation": "https://github.com/Nsfr750/STL_to_G-Code#readme",
        "Issues": "https://github.com/Nsfr750/STL_to_G-Code/issues",
        "Source": "https://github.com/Nsfr750/STL_to_G-Code",
        "Sponsor": "https://www.patreon.com/Nsfr750",
        "Donate": "https://paypal.me/3dmega",
        "Discord": "https://discord.gg/BvvkUEP9",
    },
    extras_require={
        'dev': [
            'black>=23.11.0',
            'flake8>=6.1.0',
            'pytest>=7.4.3',
            'mypy>=1.7.0',
            'sphinx>=7.2.0',
            'sphinx-rtd-theme>=1.3.0',
        ],
    },
)
