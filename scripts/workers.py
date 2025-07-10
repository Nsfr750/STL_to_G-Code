import logging
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from typing import Dict, Any, Optional, Tuple
import numpy as np
from stl import mesh

logger = logging.getLogger(__name__)

class GCodeGenerationWorker(QObject):
    """Worker class for generating G-code in a background thread."""
    
    # Signals
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total
    gcode_chunk = pyqtSignal(str)    # Emit chunks of G-code
    preview_ready = pyqtSignal(dict)  # Emit preview data
    
    def __init__(self, stl_mesh: mesh.Mesh, settings: Dict[str, Any]):
        """Initialize the worker with STL mesh and settings.
        
        Args:
            stl_mesh: The STL mesh to process
            settings: Dictionary containing all generation settings
        """
        super().__init__()
        self.stl_mesh = stl_mesh
        self.settings = settings
        self._is_cancelled = False
    
    @pyqtSlot()
    def cancel(self):
        """Request cancellation of the current operation."""
        self._is_cancelled = True
    
    @pyqtSlot()
    def generate(self):
        """Perform the G-code generation in the background."""
        try:
            # Import here to avoid circular imports
            from scripts.gcode_optimizer import GCodeOptimizer
            
            # Initialize the optimizer with settings
            optimizer = GCodeOptimizer(
                layer_height=self.settings['layer_height'],
                nozzle_diameter=self.settings['extrusion_width'],
                filament_diameter=self.settings['filament_diameter'],
                print_speed=self.settings['print_speed'],
                travel_speed=self.settings['travel_speed'],
                infill_speed=self.settings['infill_speed'],
                first_layer_speed=self.settings['first_layer_speed'],
                retraction_length=self.settings['retraction_length'],
                retraction_speed=self.settings['retraction_speed'],
                z_hop=self.settings['z_hop'],
                infill_density=self.settings['infill_density'],
                infill_pattern=self.settings['infill_pattern'],
                infill_angle=self.settings['infill_angle'],
                enable_arc_detection=self.settings.get('enable_arc_detection', False),
                arc_tolerance=self.settings.get('arc_tolerance', 0.05),
                min_arc_segments=self.settings.get('min_arc_segments', 5),
                enable_optimized_infill=self.settings.get('enable_optimized_infill', False),
                infill_resolution=self.settings.get('infill_resolution', 1.0)
            )
            
            # Get custom start/end G-code from settings
            start_gcode = self.settings.get('start_gcode', '')
            end_gcode = self.settings.get('end_gcode', '')
            
            # Prepare context for variable substitution
            context = {
                'bed_temp': self.settings.get('bed_temp', 60),
                'extruder_temp': self.settings.get('extruder_temp', 200),
                'fan_speed': self.settings.get('fan_speed', 0),
                'material': self.settings.get('material', 'PLA'),
                'layer_height': self.settings['layer_height'],
                'filament_diameter': self.settings['filament_diameter'],
                'nozzle_diameter': self.settings['extrusion_width']
            }
            
            # Generate G-code in chunks to keep the UI responsive
            gcode_generator = optimizer.generate_gcode(
                self.stl_mesh,
                start_gcode=start_gcode,
                end_gcode=end_gcode,
                context=context
            )
            
            total_layers = int((self.stl_mesh.z.max() - self.stl_mesh.z.min()) / self.settings['layer_height']) + 1
            
            for i, chunk in enumerate(gcode_generator):
                if self._is_cancelled:
                    logger.info("G-code generation cancelled by user")
                    break
                    
                # Emit progress (layer number, total layers)
                self.progress.emit(i + 1, total_layers)
                
                # Emit the G-code chunk
                if chunk:
                    self.gcode_chunk.emit(chunk)
            
            # Emit preview data if available
            if hasattr(optimizer, 'last_preview_data'):
                self.preview_ready.emit(optimizer.last_preview_data)
            
            if not self._is_cancelled:
                self.finished.emit()
                
        except Exception as e:
            logger.exception("Error in G-code generation")
            self.error.emit(str(e))
        finally:
            # Clean up
            self._is_cancelled = True


class SimulationWorker(QObject):
    """
    Worker class for simulating G-code execution in a background thread.
    
    This class processes G-code line by line, updates the printer state,
    and emits progress updates and simulation results.
    """
    update_progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, gcode: str, simulator):
        """
        Initialize the simulation worker.
        
        Args:
            gcode: The G-code to simulate
            simulator: An instance of GCodeSimulator to use for simulation
        """
        super().__init__()
        self.gcode = gcode
        self.simulator = simulator
        self._is_running = True
    
    def run(self):
        """Run the G-code simulation."""
        try:
            # Split G-code into lines and filter out comments and empty lines
            lines = [line.strip() for line in self.gcode.split('\n') if line.strip() and not line.strip().startswith(';')]
            total_lines = len(lines)
            
            # Process each line
            for i, line in enumerate(lines):
                if not self._is_running:
                    break
                    
                try:
                    # Process the line with the simulator
                    self.simulator.process_line(line)
                    
                    # Update progress
                    self.update_progress.emit(i + 1, total_lines)
                    
                    # Small delay to keep the UI responsive
                    QThread.msleep(10)
                    
                except Exception as e:
                    logger.warning(f"Error processing line {i+1}: {e}")
                    continue
            
            # Emit finished signal
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"Simulation error: {e}", exc_info=True)
            self.error.emit(f"Simulation error: {str(e)}")
        finally:
            self.finished.emit()
    
    def stop(self):
        """Stop the simulation."""
        self._is_running = False
