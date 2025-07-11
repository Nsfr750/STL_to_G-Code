# Test Scripts

## Running Tests

### Test STL Loading
```python -m test_scripts.test_stl_loading.py "STL/tappo_usb-c.stl"```

### Test Update Check
```python -m test_scripts.test_update_check.py --version 1.0.0 --force```

```python -m test_scripts.test_update_check.py --version 99.99.99 --force```

### Test G-Code Custom Commands
```python -m test_scripts.test_gcode_cusom_commands.py```

### Test G-Code Simulator
```python -m test_scripts.test_gcode_simulator.py```

## Run All Tests
```python -m unittest discover -s test_scripts -p "test_*.py"```

## Test G-Code Simulator with Pytest
```python -m pytest test_scripts/test_gcode_custom_commands.py test_scripts/test_gcode_simulator.py -v```

## Test G-Code Optimizer
```python -m pytest test_scripts/test_gcode_optimizer.py -v```
