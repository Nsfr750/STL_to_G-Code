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
    """Worker class for simulating G-code execution in a background thread."""
    # Signals
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current_line, total_lines
    state_updated = pyqtSignal(object)  # Emits PrinterState
    
    def __init__(self, gcode: str, simulator):
        """Initialize the simulation worker.
        
        Args:
            gcode: The G-code to simulate
            simulator: Instance of GCodeSimulator to use for simulation
        """
        super().__init__()
        self.gcode = gcode
        self.simulator = simulator
        self._is_running = False
        self._should_pause = False
        self._step = False
        self._speed = 1.0  # 1x speed by default
        self._delay_ms = 50  # Base delay between commands in ms
        
    def run(self):
        """Run the simulation."""
        try:
            self._is_running = True
            self._should_pause = False
            
            # Reset the simulator
            self.simulator.reset()
            
            # Split G-code into lines and filter out comments/empty lines
            lines = [line.strip() for line in self.gcode.split('\n') if line.strip() and not line.strip().startswith(';')]
            total_lines = len(lines)
            
            # Emit initial state
            self.state_updated.emit(self.simulator.state)
            
            # Process each line
            for i, line in enumerate(lines, 1):
                if not self._is_running:
                    break
                    
                # Skip comments and empty lines
                if not line or line.startswith(';'):
                    self.progress.emit(i, total_lines)
                    continue
                
                # Process the line
                success, errors, warnings = self.simulator.simulate(line)
                
                # Handle errors and warnings
                for err in errors:
                    self.error.emit(f"Line {i}: {err.message}")
                
                for warn in warnings:
                    self.error.emit(f"Line {i} [WARNING]: {warn.message}")
                
                # Update progress
                self.progress.emit(i, total_lines)
                
                # Emit state update
                self.state_updated.emit(self.simulator.state)
                
                # Handle pausing
                if self._should_pause and not self._step:
                    while self._should_pause and self._is_running:
                        QThread.msleep(100)
                
                # Reset step flag if it was set
                if self._step:
                    self._step = False
                    self._should_pause = True
                
                # Add delay based on speed
                if self._speed > 0:
                    delay = int(self._delay_ms / self._speed)
                    QThread.msleep(max(1, delay))
            
            if self._is_running:
                self.finished.emit()
                
        except Exception as e:
            import traceback
            error_msg = f"Simulation error: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)
        finally:
            self._is_running = False
    
    def stop(self):
        """Stop the simulation."""
        self._is_running = False
        self._should_pause = False
    
    def pause(self):
        """Pause the simulation."""
        self._should_pause = True
    
    def resume(self):
        """Resume the simulation."""
        self._should_pause = False
    
    def step(self):
        """Step through the simulation one command at a time."""
        self._step = True
        self._should_pause = False
    
    def set_speed(self, speed: float):
        """Set the simulation speed multiplier.
        
        Args:
            speed: Speed multiplier (e.g., 0.5 for half speed, 2.0 for double speed)
        """
        self._speed = max(0.1, min(10.0, speed))  # Clamp between 0.1x and 10x


class STLLoadingWorker(QObject):
    """Worker class for loading STL files in chunks in a background thread."""
    
    # Signals
    chunk_loaded = pyqtSignal(dict)  # Emitted when a chunk of STL data is loaded
    loading_finished = pyqtSignal()  # Emitted when loading is complete
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self, stl_processor, chunk_size=1000):
        """Initialize the STL loading worker.
        
        Args:
            stl_processor: Instance of MemoryEfficientSTLProcessor
            chunk_size: Number of triangles to process in each chunk
        """
        super().__init__()
        self.stl_processor = stl_processor
        self.chunk_size = chunk_size
        self._is_cancelled = False
    
    @pyqtSlot()
    def cancel(self):
        """Request cancellation of the loading process."""
        self._is_cancelled = True
    
    @pyqtSlot()
    def start_loading(self):
        """Start the loading process in the background thread."""
        try:
            logging.info("Starting STL loading worker")
            
            # Get total number of triangles for progress reporting
            total_triangles = self.stl_processor._header.num_triangles
            processed_triangles = 0
            
            # Process STL in chunks
            chunk_vertices = []
            chunk_faces = []
            face_offset = 0
            
            for i, triangle in enumerate(self.stl_processor.iter_triangles()):
                if self._is_cancelled:
                    logging.info("STL loading cancelled by user")
                    break
                
                # Add triangle vertices to current chunk
                chunk_vertices.extend(triangle.vertices)
                
                # Add triangle faces with offset
                chunk_faces.append([
                    face_offset,
                    face_offset + 1,
                    face_offset + 2
                ])
                face_offset += 3
                
                # Emit chunk if we've reached chunk size or end of file
                if (i + 1) % self.chunk_size == 0 or (i + 1) == total_triangles:
                    if chunk_vertices and chunk_faces:
                        # Convert to numpy arrays
                        vertices = np.array(chunk_vertices, dtype=np.float32)
                        faces = np.array(chunk_faces, dtype=np.uint32)
                        
                        # Emit chunk
                        chunk_data = {
                            'vertices': vertices,
                            'faces': faces,
                            'progress': (i + 1) / total_triangles * 100
                        }
                        self.chunk_loaded.emit(chunk_data)
                        self.progress_updated.emit(i + 1, total_triangles)
                        
                        # Reset chunk buffers
                        chunk_vertices = []
                        chunk_faces = []
            
            if not self._is_cancelled:
                logging.info("STL loading completed successfully")
                self.loading_finished.emit()
                
        except Exception as e:
            error_msg = f"Error loading STL: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
        finally:
            # Clean up
            self.stl_processor.close()
