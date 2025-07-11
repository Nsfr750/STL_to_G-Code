### TEST Script

python -m test_scripts.test_stl_loading.py "STL/tappo_usb-c.stl"
python -m test_scripts.test_update_check.py --version 1.0.0 --force
python -m test_scripts.test_update_check.py --version 99.99.99 --force
python -m test_scripts.test_gcode_cusom_commands.py
python -m test_scripts.test_gcode_simulator.py

## Test all
python -m unittest discover -s test_scripts -p "test_*.py"

## Test G-Code Simulator
python -m pytest test_scripts/test_gcode_custom_commands.py test_scripts/test_gcode_simulator.py -v
