"""
Setup script for STL to GCode Converter.
"""

from setuptools import setup, find_packages
import version

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stl-to-gcode",
    version=version.__version__,
    author="Nsfr750",
    author_email="",
    description="Convert STL files to G-code for 3D printing and CNC machining",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nsfr750/STL_to_G-Code",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'stl-to-gcode=main:main',
        ],
    },
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
)
