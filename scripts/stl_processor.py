"""
Memory-efficient STL file processor with chunked loading and processing.

This module provides functionality to load and process large STL files while
minimizing memory usage through chunked processing and memory mapping.
"""
import numpy as np
import numpy.typing as npt
from typing import Tuple, Iterator, Optional, Union, Dict, Any, List
import os
import mmap
import struct
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class STLHeader:
    """STL file header information."""
    comment: bytes
    num_triangles: int

@dataclass
class STLTriangle:
    """A single triangle from an STL file."""
    normal: npt.NDArray[np.float32]  # 3D normal vector
    vertices: npt.NDArray[np.float32]  # 3x3 array of vertex coordinates
    attributes: int  # Attribute byte count (usually 0)

class MemoryEfficientSTLProcessor:
    """
    Processes STL files in a memory-efficient manner using chunked loading.
    
    This class provides methods to load and process STL files while keeping
    memory usage low, making it suitable for very large STL files.
    """
    
    def __init__(self, file_path: Union[str, os.PathLike], chunk_size: int = 10000):
        """
        Initialize the STL processor.
        
        Args:
            file_path: Path to the STL file
            chunk_size: Number of triangles to process at once (default: 10,000)
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self._file = None
        self._mmap = None
        self._header = None
        self._is_binary = None
        self._current_position = 0
        self._progressive_chunk_size = max(1000, chunk_size // 10)  # Smaller chunks for progressive loading
        
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def open(self) -> None:
        """Open the STL file and read its header."""
        if self._file is not None:
            return
            
        self._file = open(self.file_path, 'rb')
        self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        self._is_binary = self._detect_binary()
        
        if self._is_binary:
            self._header = self._read_binary_header()
        else:
            self._header = self._read_ascii_header()
            
        logger.info(f"Opened STL file: {self.file_path.name} ({self._header.num_triangles} triangles)")
    
    def close(self) -> None:
        """Close the STL file and clean up resources."""
        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None
            
        if self._file is not None:
            self._file.close()
            self._file = None
            
        self._header = None
    
    def _detect_binary(self) -> bool:
        """Detect if the STL file is in binary format."""
        # Check if the file starts with 'solid ' and has no null bytes in the first 100 bytes
        start = self._mmap[:100]
        
        # If we find a null byte in the first 100 bytes, it's likely binary
        if b'\x00' in start:
            return True
            
        # If it starts with 'solid ' and has no null bytes, it's likely ASCII
        if start.startswith(b'solid '):
            return False
            
        # Default to binary if we can't determine
        return True
    
    def _read_binary_header(self) -> STLHeader:
        """Read the header of a binary STL file."""
        # Binary STL format:
        # 80 bytes: header/comment
        # 4 bytes: number of triangles (uint32, little-endian)
        self._mmap.seek(0)
        comment = self._mmap.read(80)
        num_triangles = struct.unpack('<I', self._mmap.read(4))[0]
        
        # Verify the file size matches the header
        expected_size = 84 + num_triangles * 50  # 50 bytes per triangle
        if len(self._mmap) != expected_size:
            logger.warning(f"STL file size doesn't match header. Expected {expected_size} bytes, got {len(self._mmap)}.")
            
        return STLHeader(comment=comment, num_triangles=num_triangles)
    
    def _read_ascii_header(self) -> STLHeader:
        """Read the header of an ASCII STL file."""
        self._mmap.seek(0)
        first_line = self._mmap.readline().strip()
        
        # Count the number of triangles by counting 'facet' lines
        # This is inefficient but necessary for accurate counting
        self._mmap.seek(0)
        num_triangles = self._mmap.read().count(b'facet')
        
        return STLHeader(comment=first_line, num_triangles=num_triangles)
    
    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get the bounding box of the STL model.
        
        Returns:
            Tuple of (min_bounds, max_bounds) as 3D numpy arrays
        """
        min_bounds = np.array([np.inf, np.inf, np.inf], dtype=np.float32)
        max_bounds = np.array([-np.inf, -np.inf, -np.inf], dtype=np.float32)
        
        for triangle in self.iter_triangles():
            min_bounds = np.minimum(min_bounds, np.min(triangle.vertices, axis=0))
            max_bounds = np.maximum(max_bounds, np.max(triangle.vertices, axis=0))
            
        return min_bounds, max_bounds
    
    def get_center(self) -> np.ndarray:
        """
        Get the center point of the STL model's bounding box.
        
        Returns:
            3D numpy array with the center coordinates
        """
        min_bounds, max_bounds = self.get_bounds()
        return (min_bounds + max_bounds) / 2.0
    
    def get_size(self) -> np.ndarray:
        """
        Get the size of the STL model's bounding box.
        
        Returns:
            3D numpy array with the size in each dimension
        """
        min_bounds, max_bounds = self.get_bounds()
        return max_bounds - min_bounds
    
    def iter_triangles(self) -> Iterator[STLTriangle]:
        """
        Iterate over all triangles in the STL file.
        
        Yields:
            STLTriangle objects one at a time
        """
        if self._is_binary:
            yield from self._iter_binary_triangles()
        else:
            yield from self._iter_ascii_triangles()
    
    def _iter_binary_triangles(self) -> Iterator[STLTriangle]:
        """Iterate over triangles in a binary STL file."""
        if self._header is None:
            self.open()
            
        # Skip header (80 bytes) and triangle count (4 bytes)
        self._mmap.seek(84)
        
        # Each triangle is 50 bytes:
        # 12 bytes normal (3x float32)
        # 36 bytes vertices (3x 3x float32)
        # 2 bytes attribute count (uint16, usually 0)
        triangle_size = 50
        
        for _ in range(self._header.num_triangles):
            data = self._mmap.read(triangle_size)
            if len(data) < triangle_size:
                break
                
            normal = np.frombuffer(data[0:12], dtype=np.float32).astype(np.float32)
            vertices = np.frombuffer(data[12:48], dtype=np.float32).reshape(3, 3).astype(np.float32)
            attributes = struct.unpack('<H', data[48:50])[0]
            
            yield STLTriangle(normal=normal, vertices=vertices, attributes=attributes)
    
    def _iter_ascii_triangles(self) -> Iterator[STLTriangle]:
        """Iterate over triangles in an ASCII STL file."""
        if self._header is None:
            self.open()
            
        self._mmap.seek(0)
        
        # Skip the 'solid' line
        line = self._mmap.readline()
        if not line.startswith(b'solid'):
            raise ValueError("Not a valid ASCII STL file")
        
        while True:
            # Find the next 'facet' line
            pos = self._mmap.find(b'facet')
            if pos == -1:
                break
                
            self._mmap.seek(pos)
            
            # Read the facet definition
            # Format:
            # facet normal ni nj nk
            #   outer loop
            #     vertex v1x v1y v1z
            #     vertex v2x v2y v2z
            #     vertex v3x v3y v3z
            #   endloop
            # endfacet
            try:
                # Read normal
                normal_line = self._mmap.readline().strip().split()
                if len(normal_line) < 5 or normal_line[0] != b'facet' or normal_line[1] != b'normal':
                    continue
                    
                normal = np.array([
                    float(normal_line[2]),
                    float(normal_line[3]),
                    float(normal_line[4])
                ], dtype=np.float32)
                
                # Skip 'outer loop'
                self._mmap.readline()
                
                # Read vertices
                vertices = []
                for _ in range(3):
                    vertex_line = self._mmap.readline().strip().split()
                    if len(vertex_line) < 4 or vertex_line[0] != b'vertex':
                        raise ValueError("Invalid vertex format in STL file")
                        
                    vertex = np.array([
                        float(vertex_line[1]),
                        float(vertex_line[2]),
                        float(vertex_line[3])
                    ], dtype=np.float32)
                    vertices.append(vertex)
                
                # Skip 'endloop' and 'endfacet'
                self._mmap.readline()  # endloop
                self._mmap.readline()  # endfacet
                
                yield STLTriangle(
                    normal=normal,
                    vertices=np.array(vertices, dtype=np.float32),
                    attributes=0
                )
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing triangle at position {pos}: {e}")
                # Try to recover by finding the next 'facet' or 'endsolid'
                self._mmap.seek(pos + 5)  # Skip past the current 'facet'
    
    def iter_chunks(self, chunk_size: Optional[int] = None) -> Iterator[List[STLTriangle]]:
        """
        Iterate over triangles in chunks to reduce memory usage.
        
        Args:
            chunk_size: Number of triangles per chunk (default: self.chunk_size)
            
        Yields:
            Lists of STLTriangle objects, each list containing up to chunk_size triangles
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
            
        chunk = []
        for triangle in self.iter_triangles():
            chunk.append(triangle)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
                
        if chunk:
            yield chunk
    
    def iter_progressive_chunks(self, chunk_size: Optional[int] = None, 
                             progress_callback: Optional[callable] = None) -> Iterator[Dict[str, Any]]:
        """
        Iterate over the STL file in chunks, yielding partial results for progressive loading.
        
        Args:
            chunk_size: Number of triangles per chunk (default: self._progressive_chunk_size)
            progress_callback: Optional callback function that receives progress (0-100)
            
        Yields:
            Dictionary containing:
            - 'vertices': Numpy array of vertex positions
            - 'faces': Numpy array of face indices
            - 'progress': Current loading progress (0-100)
            - 'total_triangles': Total number of triangles in the file
        """
        if chunk_size is None:
            chunk_size = self._progressive_chunk_size
            
        if self._header is None:
            self.open()
            
        total_triangles = self._header.num_triangles
        processed_triangles = 0
        
        # First yield an empty result with just the total count
        if progress_callback:
            progress_callback(0, total_triangles)
            
        yield {
            'vertices': np.zeros((0, 3), dtype=np.float32),
            'faces': np.zeros((0, 3), dtype=np.uint32),
            'progress': 0,
            'total_triangles': total_triangles
        }
        
        # Process the file in chunks
        chunk_vertices = []
        chunk_faces = []
        vertex_offset = 0
        
        for chunk in self.iter_chunks(chunk_size):
            for triangle in chunk:
                # Add vertices for this triangle
                chunk_vertices.append(triangle.vertices[0])
                chunk_vertices.append(triangle.vertices[1])
                chunk_vertices.append(triangle.vertices[2])
                
                # Add face indices (relative to current vertex offset)
                chunk_faces.append([vertex_offset, vertex_offset+1, vertex_offset+2])
                vertex_offset += 3
                
                processed_triangles += 1
                
                # If we've collected enough triangles, yield them
                if len(chunk_vertices) >= chunk_size * 3:
                    yield self._create_chunk_result(chunk_vertices, chunk_faces, 
                                                  processed_triangles, total_triangles)
                    chunk_vertices = []
                    chunk_faces = []
                    
                    if progress_callback:
                        progress = int((processed_triangles / total_triangles) * 100)
                        progress_callback(progress, total_triangles)
        
        # Yield any remaining triangles
        if chunk_vertices:
            yield self._create_chunk_result(chunk_vertices, chunk_faces, 
                                          processed_triangles, total_triangles)
            
            if progress_callback:
                progress_callback(100, total_triangles)
    
    def _create_chunk_result(self, vertices: list, faces: list, 
                           processed: int, total: int) -> Dict[str, Any]:
        """Helper method to create a chunk result dictionary."""
        return {
            'vertices': np.array(vertices, dtype=np.float32),
            'faces': np.array(faces, dtype=np.uint32),
            'progress': int((processed / total) * 100) if total > 0 else 0,
            'total_triangles': total
        }

    def get_mesh_info(self) -> Dict[str, Any]:
        """
        Get basic information about the STL mesh.
        
        Returns:
            Dictionary containing mesh information
        """
        min_bounds, max_bounds = self.get_bounds()
        size = max_bounds - min_bounds
        
        return {
            'num_triangles': self._header.num_triangles if self._header else 0,
            'bounds': {
                'min': min_bounds.tolist(),
                'max': max_bounds.tolist(),
                'size': size.tolist(),
                'center': ((min_bounds + max_bounds) / 2.0).tolist()
            },
            'is_binary': self._is_binary,
            'file_size': os.path.getsize(self.file_path) if self.file_path.exists() else 0
        }


def load_stl(file_path: Union[str, os.PathLike], chunk_size: int = 10000) -> MemoryEfficientSTLProcessor:
    """
    Convenience function to create and open an STL processor.
    
    Args:
        file_path: Path to the STL file
        chunk_size: Number of triangles to process at once (default: 10,000)
        
    Returns:
        An initialized and opened MemoryEfficientSTLProcessor
    """
    processor = MemoryEfficientSTLProcessor(file_path, chunk_size)
    processor.open()
    return processor
