"""
G-code simulation and validation module.

This module provides functionality to simulate and validate G-code commands,
checking for errors, estimating print time, and simulating printer state.
"""
import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, NamedTuple
from enum import Enum, auto
import numpy as np

class GCodeErrorType(Enum):
    """Types of G-code errors that can be detected."""
    SYNTAX_ERROR = auto()
    UNSUPPORTED_COMMAND = auto()
    INVALID_PARAMETER = auto()
    MISSING_PARAMETER = auto()
    OUT_OF_BOUNDS = auto()
    EXTRUSION_UNDERFLOW = auto()
    EXTRUSION_OVERFLOW = auto()
    BED_COLLISION = auto()
    MAX_FEEDRATE_EXCEEDED = auto()
    MAX_ACCELERATION_EXCEEDED = auto()
    MAX_JERK_EXCEEDED = auto()
    HEATER_ERROR = auto()
    FAN_ERROR = auto()

@dataclass
class GCodeError:
    """Represents a G-code error or warning."""
    line_number: int
    error_type: GCodeErrorType
    message: str
    command: str
    severity: str  # 'error' or 'warning'

@dataclass
class PrinterState:
    """Represents the current state of the 3D printer."""
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])  # X, Y, Z, E (extruder)
    absolute_positioning: bool = True
    absolute_extrusion: bool = True
    feedrate: float = 0.0  # mm/s
    temperature: Dict[int, float] = field(default_factory=dict)  # Extruder temperatures by index
    bed_temperature: float = 0.0
    fan_speed: float = 0.0  # 0-100%
    relative_mode: bool = False
    units_mm: bool = True  # True for mm, False for inches
    extruder_active: List[bool] = field(default_factory=lambda: [False])  # Per-extruder
    retracted: List[bool] = field(default_factory=lambda: [False])  # Per-extruder
    retract_length: float = 1.0  # mm
    retract_speed: float = 45.0  # mm/s
    layer_height: float = 0.2  # mm
    bed_size: Tuple[float, float, float] = (200, 200, 200)  # X, Y, Z in mm
    max_feedrate: Dict[str, float] = field(default_factory=lambda: {
        'x': 300, 'y': 300, 'z': 5, 'e': 120
    })  # mm/s
    max_acceleration: Dict[str, float] = field(default_factory=lambda: {
        'x': 3000, 'y': 3000, 'z': 100, 'e': 10000
    })  # mm/s²
    max_jerk: Dict[str, float] = field(default_factory=lambda: {
        'x': 20, 'y': 20, 'z': 0.4, 'e': 5.0
    })  # mm/s

class GCodeSimulator:
    """Simulates G-code execution and validates commands."""
    
    def __init__(self, printer_state: Optional[PrinterState] = None):
        """Initialize the G-code simulator.
        
        Args:
            printer_state: Initial printer state. If None, uses default values.
        """
        self.state = printer_state if printer_state is not None else PrinterState()
        self.errors: List[GCodeError] = []
        self.warnings: List[GCodeError] = []
        self.layer_changes: List[int] = []  # Line numbers where layers change
        self.current_layer: int = 0
        self.total_layers: int = 0
        self.print_time: float = 0.0  # seconds
        self.filament_used: float = 0.0  # mm
        self.travel_distance: float = 0.0  # mm
        self.extrusion_distance: float = 0.0  # mm
        self.max_feedrate: float = 0.0
        self.min_feedrate: float = float('inf')
        self._previous_position = None
        self._previous_feedrate = 0.0
        self._previous_command = ""
        
        # Regular expressions for parsing G-code
        self.command_regex = re.compile(r'^([GM][0-9]+)(?:\s+([A-Z][-+]?[0-9]*\.?[0-9]*))*')
        self.param_regex = re.compile(r'([A-Z])([-+]?[0-9]*\.?[0-9]*)')
    
    def reset(self):
        """Reset the simulator to its initial state."""
        self.__init__(self.state)
    
    def simulate(self, gcode: str) -> Tuple[bool, List[GCodeError], List[GCodeError]]:
        """Simulate G-code execution.
        
        Args:
            gcode: The G-code to simulate
            
        Returns:
            Tuple of (success, errors, warnings)
        """
        self.reset()
        
        # Split into lines and process each line
        lines = gcode.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            self._process_line(line, line_num)
            
            # Check for cancellation
            if hasattr(self, '_is_cancelled') and self._is_cancelled:
                return False, self.errors, self.warnings
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _process_line(self, line: str, line_num: int):
        """Process a single line of G-code."""
        # Skip empty lines and comments
        line = line.strip()
        if not line or line.startswith(';'):
            return
            
        # Remove inline comments
        if ';' in line:
            line = line.split(';', 1)[0].strip()
        
        # Parse the command and parameters
        match = self.command_regex.match(line)
        if not match:
            self._add_error(line_num, GCodeErrorType.SYNTAX_ERROR, 
                          f"Invalid G-code syntax: {line}", line)
            return
            
        command = match.group(1).upper()
        params = {}
        
        # Extract parameters
        for param_match in self.param_regex.finditer(line[match.end(1):]):
            param = param_match.group(1).upper()
            try:
                value = float(param_match.group(2))
                params[param] = value
            except ValueError:
                self._add_error(line_num, GCodeErrorType.INVALID_PARAMETER,
                              f"Invalid parameter value: {param_match.group(0)}", line)
        
        # Process the command
        self._process_command(command, params, line, line_num)
        
        # Store the previous command for context
        self._previous_command = command
    
    def _process_command(self, command: str, params: Dict[str, float], 
                        original_line: str, line_num: int):
        """Process a single G-code command."""
        # Store previous position for distance calculations
        prev_pos = self.state.position.copy()
        
        try:
            # Handle movement commands
            if command in ('G0', 'G1', 'G2', 'G3'):
                self._process_movement(command, params, line_num)
            
            # Handle absolute/relative positioning
            elif command == 'G90':
                self.state.absolute_positioning = True
            elif command == 'G91':
                self.state.absolute_positioning = False
            
            # Handle absolute/relative extrusion
            elif command == 'M82':
                self.state.absolute_extrusion = True
            elif command == 'M83':
                self.state.absolute_extrusion = False
            
            # Handle temperature commands
            elif command == 'M104':  # Set extruder temperature
                self._process_set_temperature(params, line_num, wait=False)
            elif command == 'M109':  # Set extruder temperature and wait
                self._process_set_temperature(params, line_num, wait=True)
            elif command == 'M140':  # Set bed temperature (don't wait)
                self._process_set_bed_temperature(params, line_num, wait=False)
            elif command == 'M190':  # Set bed temperature and wait
                self._process_set_bed_temperature(params, line_num, wait=True)
            
            # Handle fan commands
            elif command == 'M106':  # Fan on
                self._process_fan_on(params, line_num)
            elif command == 'M107':  # Fan off
                self._process_fan_off(params, line_num)
            
            # Handle G92 (Set Position)
            elif command == 'G92':
                self._process_set_position(params, line_num)
            
            # Handle M82/M83 (E Absolute/Relative)
            elif command in ('M82', 'M83'):
                self.state.absolute_extrusion = (command == 'M82')
            
            # Handle G28 (Auto Home)
            elif command == 'G28':
                self._process_auto_home(params, line_num)
            
            # Handle G29 (Bed Leveling)
            elif command == 'G29':
                self._process_bed_leveling(params, line_num)
            
            # Handle M204 (Set starting acceleration)
            elif command == 'M204':
                self._process_set_acceleration(params, line_num)
            
            # Handle M205 (Advanced settings)
            elif command == 'M205':
                self._process_advanced_settings(params, line_num)
            
            # Handle M220 (Set feedrate percentage)
            elif command == 'M220':
                self._process_set_feedrate_percentage(params, line_num)
            
            # Handle M221 (Set flow percentage)
            elif command == 'M221':
                self._process_set_flow_percentage(params, line_num)
            
            # Unsupported but non-critical commands
            elif command in ('M105', 'M114', 'M115', 'M117', 'M118', 'M119'):
                pass  # These are query/status commands
                
            # Unsupported commands
            else:
                self._add_warning(line_num, GCodeErrorType.UNSUPPORTED_COMMAND,
                                f"Unsupported command: {command}", original_line)
            
            # Update print time based on movement
            if command in ('G0', 'G1', 'G2', 'G3'):
                self._update_print_time(prev_pos, self.state.position, self.state.feedrate)
            
            # Check for layer changes
            if 'Z' in params and command in ('G0', 'G1'):
                self._check_layer_change(params['Z'], line_num)
                
        except Exception as e:
            self._add_error(line_num, GCodeErrorType.SYNTAX_ERROR,
                          f"Error processing command: {str(e)}", original_line)
    
    def _process_movement(self, command: str, params: Dict[str, float], line_num: int):
        """Process G0/G1 (linear move) or G2/G3 (arc move) commands."""
        # Update position based on parameters
        new_pos = self.state.position.copy()
        
        # Handle X, Y, Z parameters
        for axis in ['X', 'Y', 'Z']:
            if axis in params:
                if self.state.absolute_positioning:
                    new_pos[['X', 'Y', 'Z'].index(axis)] = params[axis]
                else:
                    new_pos[['X', 'Y', 'Z'].index(axis)] += params[axis]
        
        # Handle E (extrusion) parameter
        if 'E' in params:
            e_value = params['E']
            if self.state.absolute_extrusion:
                new_pos[3] = e_value  # E is at index 3
            else:
                new_pos[3] += e_value
            
            # Track filament usage
            if e_value > 0:
                self.filament_used += abs(e_value)
                self.extrusion_distance += math.sqrt(
                    sum((new_pos[i] - self.state.position[i])**2 for i in range(3)))
        
        # Update feedrate if specified
        if 'F' in params:
            self.state.feedrate = params['F'] / 60.0  # Convert mm/min to mm/s
            self.max_feedrate = max(self.max_feedrate, self.state.feedrate)
            self.min_feedrate = min(self.min_feedrate, self.state.feedrate)
        
        # Check for out-of-bounds movement
        if not self._check_bounds(new_pos, line_num):
            return
        
        # Check for maximum feedrate exceeded
        self._check_feedrate_limits(line_num)
        
        # Update position
        self._previous_position = self.state.position.copy()
        self.state.position = new_pos
        
        # Update travel distance (for non-extrusion moves)
        if 'E' not in params or params['E'] == 0:
            self.travel_distance += math.sqrt(
                sum((new_pos[i] - self._previous_position[i])**2 for i in range(3)))
    
    def _process_set_temperature(self, params: Dict[str, float], line_num: int, wait: bool):
        """Process M104/M109 (Set Extruder Temperature)."""
        if 'S' not in params:
            self._add_error(line_num, GCodeErrorType.MISSING_PARAMETER,
                          "Missing temperature parameter (S)", "M104/M109")
            return
        
        temp = params['S']
        extruder = int(params.get('T', 0))  # Default to extruder 0
        
        # Validate temperature range
        if temp < 0 or temp > 300:  # Reasonable range for most printers
            self._add_warning(line_num, GCodeErrorType.HEATER_ERROR,
                            f"Temperature {temp}°C is outside recommended range", 
                            f"M109 S{temp}")
        
        # Update temperature
        self.state.temperature[extruder] = temp
    
    def _process_set_bed_temperature(self, params: Dict[str, float], line_num: int, wait: bool):
        """Process M140/M190 (Set Bed Temperature)."""
        if 'S' not in params:
            self._add_error(line_num, GCodeErrorType.MISSING_PARAMETER,
                          "Missing temperature parameter (S)", "M140/M190")
            return
        
        temp = params['S']
        
        # Validate temperature range
        if temp < 0 or temp > 120:  # Reasonable range for most heated beds
            self._add_warning(line_num, GCodeErrorType.HEATER_ERROR,
                            f"Bed temperature {temp}°C is outside recommended range", 
                            f"M190 S{temp}")
        
        # Update bed temperature
        self.state.bed_temperature = temp
    
    def _process_fan_on(self, params: Dict[str, float], line_num: int):
        """Process M106 (Fan On)."""
        # Default to full speed if not specified
        speed = params.get('S', 255) / 255.0 * 100.0  # Convert 0-255 to 0-100%
        self.state.fan_speed = min(max(0, speed), 100)  # Clamp to 0-100%
    
    def _process_fan_off(self, params: Dict[str, float], line_num: int):
        """Process M107 (Fan Off)."""
        self.state.fan_speed = 0.0
    
    def _process_set_position(self, params: Dict[str, float], line_num: int):
        """Process G92 (Set Position)."""
        # Update axis positions
        for i, axis in enumerate(['X', 'Y', 'Z', 'E']):
            if axis in params:
                self.state.position[i] = params[axis]
    
    def _process_auto_home(self, params: Dict[str, float], line_num: int):
        """Process G28 (Auto Home)."""
        # If no axes specified, home all
        if not any(axis in params for axis in ['X', 'Y', 'Z']):
            self.state.position = [0.0, 0.0, 0.0, self.state.position[3]]
        else:
            # Home only specified axes
            for i, axis in enumerate(['X', 'Y', 'Z']):
                if axis in params:
                    self.state.position[i] = 0.0
    
    def _process_bed_leveling(self, params: Dict[str, float], line_num: int):
        """Process G29 (Bed Leveling)."""
        # This is a no-op in simulation, but we'll log it
        self._add_warning(line_num, GCodeErrorType.UNSUPPORTED_COMMAND,
                         "Bed leveling (G29) not simulated", "G29")
    
    def _process_set_acceleration(self, params: Dict[str, float], line_num: int):
        """Process M204 (Set Acceleration)."""
        # Update acceleration for specified axes
        for axis in ['X', 'Y', 'Z', 'E']:
            if axis in params:
                self.state.max_acceleration[axis.lower()] = params[axis]
    
    def _process_advanced_settings(self, params: Dict[str, float], line_num: int):
        """Process M205 (Advanced Settings)."""
        # Update jerk settings
        for axis in ['X', 'Y', 'Z', 'E']:
            if axis in params:
                self.state.max_jerk[axis.lower()] = params[axis]
    
    def _process_set_feedrate_percentage(self, params: Dict[str, float], line_num: int):
        """Process M220 (Set Feedrate Percentage)."""
        if 'S' in params:
            # Apply feedrate percentage to current feedrate
            percentage = params['S'] / 100.0
            self.state.feedrate *= percentage
    
    def _process_set_flow_percentage(self, params: Dict[str, float], line_num: int):
        """Process M221 (Set Flow Percentage)."""
        # This would affect extrusion calculations, but we'll just log it for now
        if 'S' in params:
            self._add_warning(line_num, GCodeErrorType.UNSUPPORTED_COMMAND,
                            f"Flow rate set to {params['S']}% (not simulated)", 
                            f"M221 S{params['S']}")
    
    def _check_bounds(self, position: List[float], line_num: int) -> bool:
        """Check if a position is within printer bounds."""
        in_bounds = True
        
        for i, axis in enumerate(['X', 'Y', 'Z']):
            if position[i] < 0 or position[i] > self.state.bed_size[i]:
                self._add_error(line_num, GCodeErrorType.OUT_OF_BOUNDS,
                              f"{axis}={position[i]:.2f}mm is outside print volume (0-{self.state.bed_size[i]}mm)",
                              f"{axis}{position[i]:.2f}")
                in_bounds = False
        
        return in_bounds
    
    def _check_feedrate_limits(self, line_num: int):
        """Check if the current feedrate exceeds any limits."""
        if self.state.feedrate > self.state.max_feedrate['x']:
            self._add_warning(line_num, GCodeErrorType.MAX_FEEDRATE_EXCEEDED,
                            f"Feedrate {self.state.feedrate:.1f} mm/s exceeds X/Y max feedrate of {self.state.max_feedrate['x']} mm/s",
                            f"F{self.state.feedrate*60:.0f}")
    
    def _check_layer_change(self, z_pos: float, line_num: int):
        """Check for layer changes and update layer count."""
        if not hasattr(self, '_last_z'):
            self._last_z = z_pos
            self.current_layer = 0
            self.layer_changes.append(line_num)
            return
        
        if abs(z_pos - self._last_z) > self.state.layer_height * 0.1:  # 10% threshold
            self.current_layer += 1
            self.layer_changes.append(line_num)
            
        self._last_z = z_pos
    
    def _update_print_time(self, start_pos: List[float], end_pos: List[float], feedrate: float):
        """Update the total print time based on movement."""
        if feedrate <= 0:
            return
            
        # Calculate Euclidean distance in mm
        distance = math.sqrt(sum((end_pos[i] - start_pos[i])**2 for i in range(3)))
        
        # Time = distance / speed (convert feedrate from mm/s to mm/min if needed)
        time_seconds = distance / feedrate
        self.print_time += time_seconds
    
    def _add_error(self, line_num: int, error_type: GCodeErrorType, 
                  message: str, command: str):
        """Add an error to the error list."""
        self.errors.append(GCodeError(
            line_number=line_num,
            error_type=error_type,
            message=message,
            command=command,
            severity='error'
        ))
    
    def _add_warning(self, line_num: int, error_type: GCodeErrorType, 
                    message: str, command: str):
        """Add a warning to the warning list."""
        self.warnings.append(GCodeError(
            line_number=line_num,
            error_type=error_type,
            message=message,
            command=command,
            severity='warning'
        ))
    
    def get_summary(self) -> Dict:
        """Get a summary of the simulation results."""
        return {
            'success': len(self.errors) == 0,
            'print_time': self.print_time,
            'filament_used': self.filament_used,
            'travel_distance': self.travel_distance,
            'extrusion_distance': self.extrusion_distance,
            'max_feedrate': self.max_feedrate,
            'min_feedrate': self.min_feedrate if self.min_feedrate != float('inf') else 0,
            'layer_count': len(self.layer_changes),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }
