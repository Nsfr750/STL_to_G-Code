# Test Scripts

## Running Tests

### Test STL Loading
```python -m test_scripts.test_stl_loading "STL/tappo_usb-c.stl"```

### Test Update Check
```python -m test_scripts.test_update_check.py --version 1.0.0 --force```

```python -m test_scripts.test_update_check.py --version 99.99.99 --force```

### Test Progress Reporting
```python -m test_scripts.test_progress_reporting```
## Run All Tests
```python -m unittest discover -s test_scripts -p "test_*.py"```
