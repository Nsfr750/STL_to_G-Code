"""
Tests for the G-code simulator and validator.
"""
import unittest
import 
from scripts.logger import get_loggernumpy as np

try:
    from scripts.gcode_simulator import GCodeSimulator, PrinterState, GCodeErrorType
except ImportError:
    # Fall back to relative import if running as a module
    from ..scripts.gcode_simulator import GCodeSimulator, PrinterState, GCodeErrorType

class TestGCodeSimulator(unittest.TestCase):
    """Test cases for G-code simulation and validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.simulator = GCodeSimulator()
    
    def test_basic_movement(self):
        """Test basic G0/G1 movement commands."""
        gcode = """
        G21 ; Set units to millimeters
        G90 ; Use absolute positioning
        G0 X10 Y20 Z5 ; Rapid move
        G1 X20 Y30 Z10 F3000 ; Linear move
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.simulator.state.position, [20.0, 30.0, 10.0, 0.0])
        self.assertAlmostEqual(self.simulator.state.feedrate, 3000/60)  # Convert to mm/s
    
    def test_relative_positioning(self):
        """Test relative positioning mode."""
        gcode = """
        G21
        G91 ; Relative positioning
        G1 X10 Y10 ; Move 10mm in X and Y
        G1 X10 Y10 ; Move another 10mm
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.simulator.state.position, [20.0, 20.0, 0.0, 0.0])
    
    def test_extrusion(self):
        """Test extrusion commands."""
        gcode = """
        G21
        G90
        G1 X10 E5 F1200 ; Move and extrude 5mm
        G1 X20 E10 ; Move and extrude 5mm more (absolute)
        G92 E0 ; Reset extruder position
        G1 X30 E5 ; Extrude 5mm from new zero
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.simulator.state.position[3], 5.0)  # E position
        self.assertAlmostEqual(self.simulator.filament_used, 10.0)  # Total filament used
    
    def test_temperature_control(self):
        """Test temperature control commands."""
        gcode = """
        M104 S200 ; Set hotend temperature
        M140 S60 ; Set bed temperature
        M109 S200 ; Wait for hotend
        M190 S60 ; Wait for bed
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.simulator.state.temperature.get(0, 0), 200.0)
        self.assertEqual(self.simulator.state.bed_temperature, 60.0)
    
    def test_fan_control(self):
        """Test fan control commands."""
        gcode = """
        M106 S255 ; Fan on full
        G4 P1000 ; Wait 1 second
        M106 S128 ; 50% power
        M107 ; Fan off
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.simulator.state.fan_speed, 0.0)
    
    def test_boundary_checks(self):
        """Test boundary checking."""
        gcode = """
        G21
        G90
        G1 X300 Y300 Z300 ; Move outside default bed size (200x200x200)
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertFalse(success)
        self.assertGreater(len(errors), 0)
        self.assertEqual(errors[0].error_type, GCodeErrorType.OUT_OF_BOUNDS)
    
    def test_feedrate_limits(self):
        """Test feedrate limit checking."""
        # Set up test with known feedrate limits
        self.simulator.state.max_feedrate = {'x': 300, 'y': 300, 'z': 5, 'e': 120}  # mm/s
        
        gcode = """
        G21
        G90
        G1 X100 F36000 ; 600mm/s - exceeds default limit
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)  # Should be a warning, not an error
        self.assertEqual(len(errors), 0)
        self.assertGreater(len(warnings), 0)
        
        # Check if any warning is about feedrate limit
        feedrate_warnings = [w for w in warnings if w.error_type == GCodeErrorType.MAX_FEEDRATE_EXCEEDED]
        self.assertGreater(len(feedrate_warnings), 0, "Expected a MAX_FEEDRATE_EXCEEDED warning")

    def test_layer_detection(self):
        """Test layer change detection."""
        gcode = """
        G21
        G90
        G1 Z0.2 ; First layer
        G1 X10 Y10
        G1 Z0.4 ; Second layer
        G1 X20 Y20
        G1 Z0.6 ; Third layer
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertEqual(len(self.simulator.layer_changes), 3)
        self.assertEqual(self.simulator.current_layer, 2)  # 0-based index
    
    def test_print_time_calculation(self):
        """Test print time calculation."""
        gcode = """
        G21
        G90
        G1 X100 F6000 ; 100mm at 100mm/s = 1s
        G1 Y100 F3000 ; 100mm at 50mm/s = 2s
        G1 Z10 F600   ; 10mm at 10mm/s = 1s
        """
        
        success, errors, warnings = self.simulator.simulate(gcode)
        self.assertTrue(success)
        self.assertAlmostEqual(self.simulator.print_time, 4.0, places=2)  # 1 + 2 + 1 seconds
    
    def test_filament_calculation(self):
        """Test filament usage calculation."""
        from scripts.gcode_simulator import PrinterState, GCodeSimulator, GCodeErrorType
        
        # Create a new printer state with the desired bed size
        printer_state = PrinterState()
        printer_state.bed_size = (400, 400, 400)  # X, Y, Z in mm
        
        print(f"Initial bed size: {printer_state.bed_size}")
        
        # Create a new simulator with the custom printer state
        self.simulator = GCodeSimulator(printer_state=printer_state)
        
        # Verify the bed size was set correctly in the simulator's state
        print(f"Simulator bed size after init: {self.simulator.state.bed_size}")
        self.assertEqual(self.simulator.state.bed_size, (400, 400, 400))
        
        gcode = """
        G21
        G90
        G1 X100 E50 F1200 ; 50mm filament
        G1 X200 E100 ; Another 50mm
        G92 E0 ; Reset extruder
        G1 X300 E50 ; 50mm more
        """
        
        # Print simulator state before simulation
        print(f"Simulator bed size before simulation: {self.simulator.state.bed_size}")
        
        success, errors, warnings = self.simulator.simulate(gcode)
        
        # Print all errors for debugging
        for error in errors:
            print(f"Error: {error}")
            if error.error_type == GCodeErrorType.OUT_OF_BOUNDS:
                print(f"Current bed size during error: {self.simulator.state.bed_size}")
        
        self.assertTrue(success, f"Simulation failed with errors: {errors}")
        self.assertAlmostEqual(self.simulator.filament_used, 150.0)  # 50 + 50 + 50
        self.assertAlmostEqual(self.simulator.extrusion_distance, 300.0)  # 100 + 100 + 100

if __name__ == '__main__':
    unittest.main()
