import logging
from scripts.logger import get_logger
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from typing import Dict, Any, Optional, Tuple
import numpy as np
from stl import mesh
from .language_manager import LanguageManager

logger = get_logger(__name__)

class GCodeGenerationWorker(QObject):
    """Worker class for generating G-code in a background thread."""
    
    # Signals
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total
    gcode_chunk = pyqtSignal(str)    # Emit chunks of G-code
    preview_ready = pyqtSignal(dict)  # Emit preview data
    
    def __init__(self, stl_mesh: mesh.Mesh, settings: Dict[str, Any], 
                 language_manager: Optional[LanguageManager] = None):
        """Initialize the worker with STL mesh and settings.
        
        Args:
            stl_mesh: The STL mesh to process
            settings: Dictionary containing all generation settings
            language_manager: Optional LanguageManager instance for localization
        """
        super().__init__()
        self.stl_mesh = stl_mesh
        self.settings = settings
        self._is_cancelled = False
        self.language_manager = language_manager or LanguageManager()
        
        # Log initialization
        logger.debug("GCodeGenerationWorker initialized with language: %s", 
                    self.language_manager.current_language)
    
    @pyqtSlot()
    def cancel(self):
        """Request cancellation of the current operation."""
        self._is_cancelled = True
        logger.debug("G-code generation cancellation requested")
    
    @pyqtSlot()
    def generate(self):
        """Generate G-code from the STL mesh."""
        try:
            # Extract Z coordinates for layer calculation
            if hasattr(self.stl_mesh, 'vertices'):
                # Handle trimesh object
                z_coords = self.stl_mesh.vertices[:, 2]
            elif isinstance(self.stl_mesh, dict) and 'vertices' in self.stl_mesh:
                # Handle dictionary mesh
                z_coords = self.stl_mesh['vertices'][:, 2]
            else:
                error_msg = self.language_manager.translate(
                    "worker.error.unsupported_mesh_format",
                    default="Unsupported mesh format. Expected trimesh object or dictionary with 'vertices' key."
                )
                logger.error(error_msg)
                self.error.emit(error_msg)
                return

            # Calculate total layers
            z_min, z_max = np.min(z_coords), np.max(z_coords)
            total_layers = int((z_max - z_min) / self.settings['layer_height']) + 1
            
            logger.info(
                self.language_manager.translate(
                    "worker.info.calculated_layers",
                    default="Calculated {layers} layers (z: {z_min:.2f}mm to {z_max:.2f}mm, height: {height:.2f}mm)",
                    layers=total_layers,
                    z_min=z_min,
                    z_max=z_max,
                    height=z_max-z_min
                )
            )
            
            # Initialize progress
            self.progress.emit(0, total_layers)
            
            # Create G-code generator
            gcode_generator = self._generate_gcode()
            
            # Process G-code in chunks
            for i, chunk in enumerate(gcode_generator):
                if self._is_cancelled:
                    logger.info(
                        self.language_manager.translate(
                            "worker.info.generation_cancelled",
                            default="G-code generation cancelled by user"
                        )
                    )
                    break
                    
                # Emit progress
                progress = min(int((i / total_layers) * 100), 100)
                self.progress.emit(progress, total_layers)
                
                # Emit G-code chunk
                self.gcode_chunk.emit(chunk)
                
                # Allow other events to be processed
                QThread.yieldCurrentThread()
            
            logger.info(
                self.language_manager.translate(
                    "worker.info.generation_complete",
                    default="G-code generation completed successfully"
                )
            )
            
        except Exception as e:
            error_msg = self.language_manager.translate(
                "worker.error.generation_failed",
                default="Error in G-code generation: {error}",
                error=str(e)
            )
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
        finally:
            self.finished.emit()


class STLLoadingWorker(QObject):
    """Worker class for loading STL files in chunks in a background thread."""
    
    # Signals
    chunk_loaded = pyqtSignal(dict)  # Emitted when a chunk of STL data is loaded
    loading_finished = pyqtSignal()  # Emitted when loading is complete
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self, stl_processor, chunk_size=1000, language_manager: Optional[LanguageManager] = None):
        """Initialize the STL loading worker.
        
        Args:
            stl_processor: Instance of MemoryEfficientSTLProcessor
            chunk_size: Number of triangles to process in each chunk
            language_manager: Optional LanguageManager instance for localization
        """
        super().__init__()
        self.language_manager = language_manager or LanguageManager()
        self.stl_processor = stl_processor
        self.chunk_size = chunk_size
        self._is_cancelled = False
        
        # Log STL processor info
        if hasattr(stl_processor, '_header'):
            logger.debug(
                self.language_manager.translate(
                    "worker.debug.stl_header",
                    header=str(stl_processor._header)
                )
            )
        else:
            logger.warning(
                self.language_manager.translate(
                    "worker.warning.no_stl_header"
                )
            )
    
    @pyqtSlot()
    def start_loading(self):
        """Start the loading process in the background thread."""
        logger.info(
            self.language_manager.translate(
                "worker.info.stl_loading_started",
                default="STL loading worker started"
            )
        )
        
        try:
            # Get total number of triangles for progress reporting
            if not hasattr(self.stl_processor, '_header') or not hasattr(self.stl_processor._header, 'num_triangles'):
                error_msg = self.language_manager.translate(
                    "worker.error.missing_header_info",
                    default="STL processor is missing required header information"
                )
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
                
            total_triangles = self.stl_processor._header.num_triangles
            logger.info(
                self.language_manager.translate(
                    "worker.info.total_triangles",
                    default="Total triangles to process: {count}",
                    count=total_triangles
                )
            )
            
            if total_triangles <= 0:
                error_msg = self.language_manager.translate(
                    "worker.error.invalid_triangle_count",
                    default="Invalid number of triangles in STL file: {count}",
                    count=total_triangles
                )
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # Initialize triangle collection
            vertices = []
            faces = []
            processed_triangles = 0
            
            logger.debug(
                self.language_manager.translate(
                    "worker.debug.starting_triangle_iteration",
                    default="Starting triangle iteration..."
                )
            )
            
            # Process triangles in chunks
            for i, triangle in enumerate(self.stl_processor.iter_triangles()):
                if self._is_cancelled:
                    logger.info(
                        self.language_manager.translate(
                            "worker.info.loading_cancelled",
                            default="Loading cancelled by user"
                        )
                    )
                    break
                    
                # Add triangle to current chunk
                base_idx = len(vertices) // 3
                vertices.extend([
                    triangle[0][0], triangle[0][1], triangle[0][2],
                    triangle[1][0], triangle[1][1], triangle[1][2],
                    triangle[2][0], triangle[2][1], triangle[2][2]
                ])
                faces.append([base_idx, base_idx+1, base_idx+2])
                processed_triangles += 1
                
                # Emit chunk if we've reached chunk size or end of file
                if len(vertices) >= self.chunk_size * 9:  # 3 vertices * 3 coordinates per triangle
                    self._emit_chunk(vertices, faces, processed_triangles, total_triangles)
                    vertices = []
                    faces = []
                    
                # Allow other events to be processed
                QThread.yieldCurrentThread()
            
            # Emit any remaining triangles
            if vertices and not self._is_cancelled:
                self._emit_chunk(vertices, faces, processed_triangles, total_triangles, is_final=True)
            
            if not self._is_cancelled:
                logger.info(
                    self.language_manager.translate(
                        "worker.info.loading_complete",
                        default="STL loading completed successfully"
                    )
                )
                self.loading_finished.emit()
                
        except Exception as e:
            error_msg = self.language_manager.translate(
                "worker.error.loading_failed",
                default="Error in STL loading worker: {error}",
                error=str(e)
            )
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
        finally:
            # Clean up resources
            try:
                if hasattr(self.stl_processor, 'close'):
                    self.stl_processor.close()
            except Exception as e:
                logger.error(
                    self.language_manager.translate(
                        "worker.error.cleanup_failed",
                        default="Error closing STL processor: {error}",
                        error=str(e)
                    )
                )
    
    def _emit_chunk(self, vertices, faces, processed_triangles, total_triangles, is_final=False):
        """Emit a chunk of STL data with proper progress information."""
        progress = (processed_triangles / total_triangles) * 100.0
        
        # Only emit progress if it's the final chunk or if progress has changed significantly
        if is_final or processed_triangles % 100 == 0 or not hasattr(self, '_last_progress') or \
           abs(progress - getattr(self, '_last_progress', 0)) >= 1.0:  # At least 1% change
            
            status_msg = self.language_manager.translate(
                "worker.status.loading_stl",
                default="Loading STL... {progress:.1f}%",
                progress=progress
            )
            
            logger.debug(
                self.language_manager.translate(
                    "worker.debug.emitting_chunk",
                    default="Emitting chunk with {triangles} triangles, progress: {progress:.1f}%",
                    triangles=len(vertices)//3,
                    progress=progress
                )
            )
            
            # Emit progress update
            self.progress_updated.emit(int(progress), 100)
            
            # Update last progress
            self._last_progress = progress
        
        # Emit the chunk data
        self.chunk_loaded.emit({
            'vertices': vertices,
            'faces': faces,
            'progress': progress,
            'is_final': is_final
        })
    
    def cancel(self):
        """Cancel the loading process."""
        self._is_cancelled = True
        logger.debug(
            self.language_manager.translate(
                "worker.debug.loading_cancellation_requested",
                default="STL loading cancellation requested"
            )
        )
