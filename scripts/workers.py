import logging
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
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
                enable_arc_detection=self.settings['enable_arc_detection'],
                arc_tolerance=self.settings['arc_tolerance'],
                min_arc_segments=self.settings['min_arc_segments'],
                enable_optimized_infill=self.settings['enable_optimized_infill'],
                infill_resolution=self.settings['infill_resolution']
            )
            
            # Generate G-code in chunks to keep the UI responsive
            gcode_generator = optimizer.generate_gcode(self.stl_mesh)
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
