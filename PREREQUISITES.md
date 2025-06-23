# Prerequisites

Before running the STL to GCode Converter, ensure that you have the following installed:

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python Version**: Python 3.8 or later (3.12 recommended)

## Required Python Libraries

Install the required libraries using pip:

```bash
pip install -r requirements.txt
```

Or install the core dependencies manually:

```bash
pip install numpy-stl matplotlib numpy-stl trimesh pillow requests
```

## Installation Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/stl_to_gcode.git
   cd python-stl-to-gcode
   ```

2. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   # source venv/bin/activate
   ```

3. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Additional Notes

- For issues with STL visualization, ensure that your `matplotlib` version is up to date (`>=3.7.0`).
- If you encounter any issues with the STL library, ensure you have the correct package installed:
  ```bash
  pip uninstall stl  # If installed
  pip install numpy-stl  # Install the correct package
  ```
- If the application fails to open, verify that you have installed all the required libraries.
