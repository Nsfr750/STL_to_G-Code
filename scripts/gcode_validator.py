"""
G-code Validator Module

This module provides functionality to validate G-code for syntax correctness,
safety, and printer compatibility.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Set, Pattern
import math

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

@dataclass
class ValidationIssue:
    """Represents a validation issue found in G-code."""
    line_number: int
    message: str
    severity: ValidationSeverity
    code: str = ""
    suggestion: str = ""
    command: str = ""

@dataclass
class PrinterLimits:
    """Represents the physical and firmware limits of a 3D printer."""
    max_feedrate: Dict[str, float] = field(default_factory=lambda: {
        'x': 300, 'y': 300, 'z': 5, 'e': 120
    })
    max_acceleration: Dict[str, float] = field(default_factory=lambda: {
        'x': 3000, 'y': 3000, 'z': 100, 'e': 10000
    })
    max_jerk: Dict[str, float] = field(default_factory=lambda: {
        'x': 20, 'y': 20, 'z': 0.4, 'e': 5.0
    })
    bed_size: Tuple[float, float, float] = (200, 200, 200)  # X, Y, Z in mm
    min_temp: float = 0.0
    max_temp: float = 300.0
    min_bed_temp: float = 0.0
    max_bed_temp: float = 120.0
    firmware: str = "Marlin"  # Marlin, RepRap, etc.
    extruder_count: int = 1
    has_heated_bed: bool = True
    has_fan: bool = True

class GCodeValidator:
    """Validates G-code for syntax, safety, and printer compatibility."""
    
    def __init__(self, printer_limits: Optional[PrinterLimits] = None):
        """Initialize the validator with optional printer limits."""
        self.printer_limits = printer_limits if printer_limits else PrinterLimits()
        self.issues: List[ValidationIssue] = []
        self._current_line = 0
        self._current_command = ""
        self._state = {
            'position': {'x': 0, 'y': 0, 'z': 0, 'e': 0},
            'feedrate': 0,
            'extruder_temp': 0,
            'bed_temp': 0,
            'fan_speed': 0,
            'absolute_positioning': True,
            'absolute_extrusion': True,
            'relative_mode': False,
            'units_mm': True,
            'current_tool': 0
        }
        
        # Command patterns
        self._gcode_pattern = re.compile(
            r'^\s*(?P<command>[GM][0-9]+\.?[0-9]*)\s*'  # G or M command
            r'(?P<params>([A-Za-z][-+]?[0-9]*\.?[0-9]*\s*)*)'  # Parameters
            r'(?:;.*)?$'  # Optional comment
        )
        self._param_pattern = re.compile(
            r'([A-Za-z])([-+]?[0-9]*\.?[0-9]*)',
            re.IGNORECASE
        )
    
    def validate(self, gcode: str) -> List[ValidationIssue]:
        """
        Validate G-code and return a list of issues.
        
        Args:
            gcode: The G-code to validate
            
        Returns:
            List of validation issues found
        """
        self.issues = []
        lines = gcode.split('\n')
        
        for i, line in enumerate(lines, 1):
            self._current_line = i
            self._process_line(line.strip())
        
        self._check_final_state()
        return self.issues
    
    def _process_line(self, line: str):
        """Process a single line of G-code."""
        if not line or line.startswith(';'):
            return
            
        # Check for line numbers and remove them
        if line[0] == 'N' and line[1].isdigit():
            line = line[line.find(' ') + 1:] if ' ' in line else ""
            if not line:
                return
        
        # Match G/M command with parameters
        match = self._gcode_pattern.match(line)
        if not match:
            self._add_issue("Invalid G-code syntax", ValidationSeverity.ERROR, line)
            return
            
        command = match.group('command').upper()
        self._current_command = command
        params_str = match.group('params')
        
        # Parse parameters
        params = {}
        for param_match in self._param_pattern.finditer(params_str):
            param = param_match.group(1).upper()
            try:
                value = float(param_match.group(2))
                params[param] = value
            except (ValueError, IndexError):
                self._add_issue(
                    f"Invalid parameter value: {param_match.group(0)}",
                    ValidationSeverity.ERROR,
                    line
                )
        
        # Process the command
        try:
            self._process_command(command, params, line)
        except Exception as e:
            self._add_issue(
                f"Error processing command: {str(e)}",
                ValidationSeverity.ERROR,
                line
            )
    
    def _process_command(self, command: str, params: Dict[str, float], original_line: str):
        """Process a G/M command with its parameters."""
        # Movement commands
        if command in ('G0', 'G1'):
            self._process_movement(command, params, original_line)
        # Set Positioning Mode
        elif command in ('G90', 'G91'):
            self._state['absolute_positioning'] = (command == 'G90')
            if 'E' in params and command == 'G91':
                self._state['absolute_extrusion'] = False
            elif 'E' in params and command == 'G90':
                self._state['absolute_extrusion'] = True
        # Set Units
        elif command in ('G20', 'G21'):
            self._state['units_mm'] = (command == 'G21')
        # Set Position
        elif command == 'G92':
            self._process_set_position(params)
        # Home
        elif command == 'G28':
            self._process_homing(params)
        # Set Temperature
        elif command in ('M104', 'M109'):
            self._process_set_temperature(params, wait=(command == 'M109'))
        # Set Bed Temperature
        elif command in ('M140', 'M190'):
            self._process_set_bed_temperature(params, wait=(command == 'M190'))
        # Set Fan Speed
        elif command == 'M106':
            self._process_set_fan_speed(params)
        # Disable Fan
        elif command == 'M107':
            self._state['fan_speed'] = 0
        # Set Absolute/Relative Extrusion
        elif command in ('M82', 'M83'):
            self._state['absolute_extrusion'] = (command == 'M82')
        # Set Extruder
        elif command.startswith('T'):
            try:
                tool = int(command[1:])
                if tool < 0 or tool >= self.printer_limits.extruder_count:
                    self._add_issue(
                        f"Invalid tool number: T{tool}",
                        ValidationSeverity.ERROR,
                        original_line
                    )
                else:
                    self._state['current_tool'] = tool
            except (ValueError, IndexError):
                self._add_issue(
                    f"Invalid tool selection: {command}",
                    ValidationSeverity.ERROR,
                    original_line
                )
    
    def _process_movement(self, command: str, params: Dict[str, float], original_line: str):
        """Process G0/G1 movement commands."""
        # Check feedrate
        if 'F' in params:
            feedrate = params['F']
            if feedrate < 0:
                self._add_issue(
                    "Feedrate cannot be negative",
                    ValidationSeverity.ERROR,
                    original_line
                )
            elif feedrate > self.printer_limits.max_feedrate['x']:
                self._add_issue(
                    f"Feedrate {feedrate} exceeds maximum of {self.printer_limits.max_feedrate['x']}",
                    ValidationSeverity.WARNING,
                    original_line
                )
            self._state['feedrate'] = feedrate
        
        # Check movement parameters
        for axis in ['X', 'Y', 'Z', 'E']:
            if axis in params:
                value = params[axis]
                
                # Check axis limits
                if axis in ['X', 'Y', 'Z']:
                    axis_idx = ['X', 'Y', 'Z'].index(axis)
                    max_pos = self.printer_limits.bed_size[axis_idx]
                    if value < 0 or value > max_pos:
                        self._add_issue(
                            f"{axis} position {value} is out of bounds (0-{max_pos})",
                            ValidationSeverity.WARNING if command == 'G0' else ValidationSeverity.ERROR,
                            original_line
                        )
                
                # Update position
                if self._state['absolute_positioning'] or axis == 'E' and self._state['absolute_extrusion']:
                    self._state['position'][axis.lower()] = value
                else:
                    self._state['position'][axis.lower()] += value
    
    def _process_set_position(self, params: Dict[str, float]):
        """Process G92 (Set Position) command."""
        for axis in params:
            if axis.upper() in ['X', 'Y', 'Z', 'E']:
                self._state['position'][axis.lower()] = params[axis]
    
    def _process_homing(self, params: Dict[str, float]):
        """Process G28 (Auto Home) command."""
        if not params:  # Home all axes if none specified
            for axis in ['x', 'y', 'z']:
                self._state['position'][axis] = 0
        else:
            for axis in params:
                if axis.upper() in ['X', 'Y', 'Z']:
                    self._state['position'][axis.lower()] = 0
    
    def _process_set_temperature(self, params: Dict[str, float], wait: bool = False):
        """Process M104/M109 (Set/Set and Wait for Temperature) command."""
        if 'S' in params:
            temp = params['S']
            if temp < self.printer_limits.min_temp or temp > self.printer_limits.max_temp:
                self._add_issue(
                    f"Extruder temperature {temp}°C is outside safe range "
                    f"({self.printer_limits.min_temp}-{self.printer_limits.max_temp}°C)",
                    ValidationSeverity.WARNING if wait else ValidationSeverity.ERROR,
                    self._current_command
                )
            self._state['extruder_temp'] = temp
    
    def _process_set_bed_temperature(self, params: Dict[str, float], wait: bool = False):
        """Process M140/M190 (Set/Set and Wait for Bed Temperature) command."""
        if not self.printer_limits.has_heated_bed:
            self._add_issue(
                "Printer does not have a heated bed",
                ValidationSeverity.WARNING,
                self._current_command
            )
            return
            
        if 'S' in params:
            temp = params['S']
            if temp < self.printer_limits.min_bed_temp or temp > self.printer_limits.max_bed_temp:
                self._add_issue(
                    f"Bed temperature {temp}°C is outside safe range "
                    f"({self.printer_limits.min_bed_temp}-{self.printer_limits.max_bed_temp}°C)",
                    ValidationSeverity.WARNING if wait else ValidationSeverity.ERROR,
                    self._current_command
                )
            self._state['bed_temp'] = temp
    
    def _process_set_fan_speed(self, params: Dict[str, float]):
        """Process M106 (Set Fan Speed) command."""
        if not self.printer_limits.has_fan:
            self._add_issue(
                "Printer does not have a controllable fan",
                ValidationSeverity.WARNING,
                self._current_command
            )
            return
            
        if 'S' in params:
            speed = params['S']
            if speed < 0 or speed > 255:
                self._add_issue(
                    f"Fan speed {speed} is outside valid range (0-255)",
                    ValidationSeverity.ERROR,
                    self._current_command
                )
            self._state['fan_speed'] = speed
    
    def _check_final_state(self):
        """Perform final validation checks after processing all commands."""
        # Check if hotend is hot but no part cooling fan is on
        if (self._state['extruder_temp'] > 50 and 
            self._state['fan_speed'] == 0 and 
            self.printer_limits.has_fan):
            self._add_issue(
                "Hotend is hot but part cooling fan is off",
                ValidationSeverity.WARNING,
                line_number=self._current_line
            )
        
        # Check if hotend is hot but no print is present
        if (self._state['extruder_temp'] > 50 and 
            self._state['position']['z'] > 10):
            self._add_issue(
                "Hotend is hot but appears to be away from the print area",
                ValidationSeverity.WARNING,
                line_number=self._current_line
            )
    
    def _add_issue(self, message: str, severity: ValidationSeverity, 
                  code: str = "", suggestion: str = "", line_number: int = None):
        """Add a validation issue to the list."""
        if line_number is None:
            line_number = self._current_line
            
        self.issues.append(ValidationIssue(
            line_number=line_number,
            message=message,
            severity=severity,
            code=code or self._current_command,
            suggestion=suggestion,
            command=self._current_command
        ))

def validate_gcode(gcode: str, printer_limits: Optional[PrinterLimits] = None) -> List[ValidationIssue]:
    """
    Validate G-code and return a list of issues.

    This is a convenience function that creates a GCodeValidator instance
    and calls validate() on it.

    Args:
        gcode: The G-code to validate
        printer_limits: Optional PrinterLimits instance. If None, default limits will be used.

    Returns:
        List of validation issues found
    """
    validator = GCodeValidator(printer_limits)
    return validator.validate(gcode)
