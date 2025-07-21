import logging
from scripts.logger import get_logger
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from typing import Dict, Any, Optional, Tuple
import numpy as np
from stl import mesh

logger = get_logger(__name__)

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
        logging.debug(f"Initializing STLLoadingWorker with chunk_size={chunk_size}")
        self.stl_processor = stl_processor
        self.chunk_size = chunk_size
        self._is_cancelled = False
        
        # Log STL processor info
        if hasattr(stl_processor, '_header'):
            logging.debug(f"STL header: {stl_processor._header}")
        else:
            logging.warning("STL processor has no _header attribute")
    
    @pyqtSlot()
    def start_loading(self):
        """Start the loading process in the background thread."""
        logging.info("STL loading worker started")
        
        try:
            # Get total number of triangles for progress reporting
            if not hasattr(self.stl_processor, '_header') or not hasattr(self.stl_processor._header, 'num_triangles'):
                error_msg = "STL processor is missing required header information"
                logging.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
                
            total_triangles = self.stl_processor._header.num_triangles
            logging.info(f"Total triangles to process: {total_triangles}")
            
            if total_triangles <= 0:
                error_msg = f"Invalid number of triangles in STL file: {total_triangles}"
                logging.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # Initialize chunk buffers
            chunk_vertices = []
            chunk_faces = []
            processed_triangles = 0
            
            logging.debug("Starting triangle iteration...")
            
            # Process STL in chunks
            for i, triangle in enumerate(self.stl_processor.iter_triangles()):
                if self._is_cancelled:
                    logging.info("Loading cancelled by user")
                    break
                
                # Add triangle vertices and face indices
                vertex_offset = len(chunk_vertices)
                chunk_vertices.extend(triangle.vertices)
                
                # Add face indices relative to the current chunk
                chunk_faces.append([vertex_offset, vertex_offset + 1, vertex_offset + 2])
                processed_triangles += 1
                
                # Emit progress update every 100 triangles
                if processed_triangles % 100 == 0:
                    self.progress_updated.emit(processed_triangles, total_triangles)
                
                # Process chunk if we've reached the chunk size
                if len(chunk_vertices) >= self.chunk_size * 3:  # 3 vertices per triangle
                    self._emit_chunk(chunk_vertices, chunk_faces, processed_triangles, total_triangles)
                    chunk_vertices = []
                    chunk_faces = []
            
            # Process any remaining triangles in the last chunk
            if chunk_vertices and not self._is_cancelled:
                self._emit_chunk(chunk_vertices, chunk_faces, processed_triangles, total_triangles, is_final=True)
            
            if not self._is_cancelled:
                logging.info("STL loading completed successfully")
                self.loading_finished.emit()
                
        except Exception as e:
            error_msg = f"Error in STL loading worker: {str(e)}"
            logging.error(error_msg, exc_info=True) 
            self.error_occurred.emit(error_msg)
        finally:
            # Clean up
            try:
                if hasattr(self.stl_processor, 'close'):
                    self.stl_processor.close()
            except Exception as e:
                logging.error(f"Error closing STL processor: {str(e)}", exc_info=True)
    
    def _emit_chunk(self, vertices, faces, processed_triangles, total_triangles, is_final=False):
        """Emit a chunk of STL data with proper progress information."""
        progress = 100.0 if is_final else (processed_triangles / total_triangles) * 100
        
        # Only log progress at certain intervals or for significant changes
        if is_final or processed_triangles % 100 == 0 or not hasattr(self, '_last_progress') or \
           abs(progress - getattr(self, '_last_progress', 0)) >= 1.0:  # At least 1% change
            
            logging.debug(f"Emitting chunk with {len(vertices)//3} triangles, progress: {progress:.1f}%")
            
            self.chunk_loaded.emit({
                'vertices': np.array(vertices, dtype=np.float32),
                'faces': np.array(faces, dtype=np.int32),
                'progress': progress,
                'status': f"Loading STL... {progress:.1f}%"
            })
            
            # Update the last progress value
            self._last_progress = progress
    
    def cancel(self):
        """Cancel the loading process."""
        self._is_cancelled = True
