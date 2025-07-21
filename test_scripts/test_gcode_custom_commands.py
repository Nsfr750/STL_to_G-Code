"""
Tests for custom start/end G-code functionality.
"""
import unittest
import numpy as np
from stl import 
from scripts.logger import get_loggermesh

try:
    from scripts.gcode_optimizer import GCodeOptimizer
except ImportError:
    # Fall back to relative import if running as a module
    from ..scripts.gcode_optimizer import GCodeOptimizer

class TestCustomGCode(unittest.TestCase):
    """Test cases for custom start/end G-code functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple cube STL for testing
        self.cube = mesh.Mesh(np.zeros(12, dtype=mesh.Mesh.dtype))
        
        # Define vertices of the cube
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ])
        
        # Define the 12 triangles that make up the cube
        faces = [
            [0, 3, 1], [1, 3, 2],  # Bottom
            [0, 4, 7], [0, 7, 3],  # Front
            [4, 5, 6], [4, 6, 7],  # Top
            [5, 1, 2], [5, 2, 6],  # Right
            [2, 3, 6], [3, 7, 6],  # Back
            [0, 1, 5], [0, 5, 4]   # Left
        ]
        
        for i, face in enumerate(faces):
            for j in range(3):
                self.cube.vectors[i][j] = vertices[face[j]]
        
        # Initialize the optimizer with test settings
        self.optimizer = GCodeOptimizer(
            layer_height=0.2,
            nozzle_diameter=0.4,
            filament_diameter=1.75,
            print_speed=60,
            travel_speed=120,
            infill_speed=60,
            first_layer_speed=30,
            retraction_length=5,
            retraction_speed=45,
            z_hop=0.2,
            infill_density=20,
            infill_pattern='lines',
            infill_angle=45,
            enable_arc_detection=False,
            arc_tolerance=0.05,
            min_arc_segments=5,
            enable_optimized_infill=False,
            infill_resolution=1.0
        )
    
    def test_start_gcode_injection(self):
        """Test that custom start G-code is correctly injected."""
        custom_start = "M140 S60\nM104 S200\nG28"
        
        gcode = list(self.optimizer.generate_gcode(
            self.cube,
            start_gcode=custom_start,
            end_gcode=""
        ))
        
        # Check that the start G-code is included
        self.assertIn("; --- Custom Start G-code ---", gcode[0])
        self.assertIn("M140 S60", gcode[0])
        self.assertIn("M104 S200", gcode[0])
        self.assertIn("G28", gcode[0])
    
    def test_end_gcode_injection(self):
        """Test that custom end G-code is correctly injected."""
        custom_end = "M104 S0\nM140 S0\nM84"
        
        gcode = list(self.optimizer.generate_gcode(
            self.cube,
            start_gcode="",
            end_gcode=custom_end
        ))
        
        # Check that the end G-code is included
        self.assertIn("; --- Custom End G-code ---", gcode[-1])
        self.assertIn("M104 S0", gcode[-1])
        self.assertIn("M140 S0", gcode[-1])
        self.assertIn("M84", gcode[-1])
    
    def test_variable_substitution(self):
        """Test that variables in custom G-code are correctly substituted."""
        custom_start = "M140 S{bed_temp}\nM104 S{extruder_temp}\n; Material: {material}"
        
        context = {
            'bed_temp': 60,
            'extruder_temp': 210,
            'material': 'PLA',
            'fan_speed': 0
        }
        
        gcode = list(self.optimizer.generate_gcode(
            self.cube,
            start_gcode=custom_start,
            end_gcode="",
            context=context
        ))
        
        # Check that variables were substituted
        self.assertIn("M140 S60", gcode[0])
        self.assertIn("M104 S210", gcode[0])
        self.assertIn("; Material: PLA", gcode[0])
    
    def test_invalid_gcode_detection(self):
        """Test that invalid G-code commands are detected."""
        # This command doesn't exist
        custom_start = "G0 X10 Y10\nINVALID_COMMAND X100"
        
        with self.assertRaises(ValueError) as context:
            list(self.optimizer.generate_gcode(
                self.cube,
                start_gcode=custom_start,
                end_gcode=""
            ))
        
        self.assertIn("Invalid G-code command", str(context.exception))

if __name__ == '__main__':
    unittest.main()
