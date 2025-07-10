"""
G-code optimization algorithms for the STL to GCode Converter.

This module provides various optimization techniques for G-code generation,
including path optimization, infill patterns, and print parameter tuning.
"""
import math
from typing import List, Tuple, Dict, Optional
import numpy as np
from scipy.spatial import distance
import logging

class GCodeOptimizer:
    """
    A class containing various G-code optimization algorithms.
    """
    
    @staticmethod
    def optimize_travel_path(points: List[Tuple[float, float, float]], 
                           current_pos: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
        """
        Optimize the travel path using nearest-neighbor algorithm.
        
        Args:
            points: List of (x, y, z) points to visit
            current_pos: Current (x, y, z) position of the print head
            
        Returns:
            List of points in optimized order
        """
        if not points:
            return []
            
        points = points.copy()
        optimized_path = []
        current = np.array(current_pos)
        
        while points:
            # Find the nearest point to current position
            distances = [np.linalg.norm(current - np.array(p)) for p in points]
            nearest_idx = np.argmin(distances)
            nearest_point = points.pop(nearest_idx)
            
            # Add to optimized path and update current position
            optimized_path.append(nearest_point)
            current = np.array(nearest_point)
            
        return optimized_path
    
    @staticmethod
    def generate_infill_pattern(bounds: Tuple[float, float, float, float], 
                              angle: float = 45, 
                              spacing: float = 5.0) -> List[Tuple[float, float, float, float]]:
        """
        Generate an infill pattern with the specified angle and spacing.
        
        Args:
            bounds: (x_min, y_min, x_max, y_max) bounding box for infill
            angle: Angle of infill lines in degrees (0-180)
            spacing: Distance between infill lines
            
        Returns:
            List of (x1, y1, x2, y2) line segments
        """
        x_min, y_min, x_max, y_max = bounds
        width = x_max - x_min
        height = y_max - y_min
        
        # Convert angle to radians
        angle_rad = math.radians(angle)
        
        # Calculate the maximum distance we need to cover
        max_dim = math.sqrt(width**2 + height**2)
        
        # Generate lines perpendicular to the angle
        lines = []
        d = 0
        
        while d <= max_dim:
            # Calculate line endpoints
            if angle < 45 or angle > 135:
                # More horizontal lines
                x1 = x_min - height / math.tan(angle_rad)
                y1 = y_min
                x2 = x_min + height / math.tan(angle_rad)
                y2 = y_max
                
                # Offset the line
                x1 += d * math.cos(angle_rad)
                y1 += d * math.sin(angle_rad)
                x2 += d * math.cos(angle_rad)
                y2 += d * math.sin(angle_rad)
            else:
                # More vertical lines
                x1 = x_min
                y1 = y_min - width * math.tan(angle_rad)
                x2 = x_max
                y2 = y_min + width * math.tan(angle_rad)
                
                # Offset the line
                x1 += d * math.cos(angle_rad)
                y1 += d * math.sin(angle_rad)
                x2 += d * math.cos(angle_rad)
                y2 += d * math.sin(angle_rad)
            
            # Add line if it intersects the bounding box
            lines.append((x1, y1, x2, y2))
            d += spacing
            
        return lines
    
    @staticmethod
    def optimize_retraction(moves: List[Dict], 
                          retract_dist: float = 5.0,
                          retract_speed: float = 40.0,
                          min_travel: float = 1.0) -> List[Dict]:
        """
        Add retraction commands to the G-code moves where needed.
        
        Args:
            moves: List of move dictionaries with 'x', 'y', 'z', 'e', 'f' keys
            retract_dist: Distance to retract in mm
            retract_speed: Retraction speed in mm/s
            min_travel: Minimum travel distance to trigger retraction (mm)
            
        Returns:
            List of optimized moves with retractions
        """
        if not moves:
            return []
            
        optimized_moves = []
        extruded = False
        
        for i, move in enumerate(moves):
            # Check if this is a travel move (no extrusion)
            is_travel = 'e' not in move or move.get('e', 0) <= 0
            
            if is_travel:
                # Calculate travel distance
                prev_move = moves[i-1] if i > 0 else {'x': 0, 'y': 0, 'z': 0}
                dx = move.get('x', prev_move.get('x', 0)) - prev_move.get('x', 0)
                dy = move.get('y', prev_move.get('y', 0)) - prev_move.get('y', 0)
                travel_dist = math.sqrt(dx**2 + dy**2)
                
                # Add retraction if needed
                if travel_dist >= min_travel and extruded:
                    optimized_moves.append({
                        'command': 'G1',
                        'e': -retract_dist,
                        'f': retract_speed * 60,  # Convert to mm/min
                        'comment': 'retract'
                    })
                    extruded = False
            else:
                # Add unretract if needed
                if not extruded:
                    optimized_moves.append({
                        'command': 'G1',
                        'e': retract_dist,
                        'f': retract_speed * 60,  # Convert to mm/min
                        'comment': 'unretract'
                    })
                    extruded = True
            
            # Add the original move
            optimized_moves.append(move)
            
        return optimized_moves

    @staticmethod
    def calculate_optimal_speed(distance: float, 
                              max_speed: float, 
                              acceleration: float,
                              corner_angle: Optional[float] = None) -> float:
        """
        Calculate the optimal speed for a move based on distance and cornering.
        
        Args:
            distance: Distance of the move in mm
            max_speed: Maximum speed in mm/s
            acceleration: Printer acceleration in mm/s²
            corner_angle: Angle between current and next move in degrees (optional)
            
        Returns:
            Optimal speed in mm/s
        """
        if distance <= 0:
            return 0
            
        # Calculate maximum speed based on acceleration and distance
        # v = sqrt(2 * a * d)
        max_possible_speed = math.sqrt(2 * acceleration * distance)
        
        # Reduce speed for sharp corners
        if corner_angle is not None:
            # Convert to radians and calculate speed factor (1.0 for 180°, 0.5 for 90°)
            angle_rad = math.radians(corner_angle)
            corner_factor = 0.5 * (1.0 + math.cos(angle_rad))
            max_possible_speed *= corner_factor
        
        # Don't exceed maximum speed
        return min(max_possible_speed, max_speed)

    @staticmethod
    def detect_arcs(points, tolerance=0.1, min_points=5):
        """
        Detect arcs in a sequence of 2D points and convert them to circular arcs.
        
        Args:
            points: List of (x, y) points
            tolerance: Maximum distance between original points and fitted arc
            min_points: Minimum number of points to consider for arc detection
            
        Returns:
            List of segments where each segment is either a line or an arc
            Each segment is a dict with keys: type, points, center, radius, start_angle, end_angle
        """
        if len(points) < 3:
            return [{'type': 'line', 'points': points}]
            
        segments = []
        segment_start = 0
        
        while segment_start < len(points) - 2:
            best_fit = None
            best_error = float('inf')
            best_end = segment_start + 2
            
            # Try to find the longest possible arc starting at segment_start
            for end in range(segment_start + min_points, min(segment_start + 100, len(points))):
                arc_points = points[segment_start:end+1]
                
                # Skip colinear points
                if GCodeOptimizer._are_colinear(arc_points):
                    continue
                    
                # Fit circle to points
                center, radius, error = GCodeOptimizer._fit_circle(arc_points)
                
                # Check if this is a better fit
                if error < tolerance and error < best_error:
                    best_fit = {
                        'center': center,
                        'radius': radius,
                        'points': arc_points
                    }
                    best_error = error
                    best_end = end
            
            if best_fit:
                # Calculate start and end angles
                start_vec = np.array(best_fit['points'][0]) - best_fit['center']
                end_vec = np.array(best_fit['points'][-1]) - best_fit['center']
                
                start_angle = np.arctan2(start_vec[1], start_vec[0])
                end_angle = np.arctan2(end_vec[1], end_vec[0])
                
                # Ensure angles are in the correct order
                if np.abs(end_angle - start_angle) > np.pi:
                    if end_angle > start_angle:
                        start_angle += 2 * np.pi
                    else:
                        end_angle += 2 * np.pi
                
                segments.append({
                    'type': 'arc',
                    'center': best_fit['center'],
                    'radius': best_fit['radius'],
                    'start_angle': start_angle,
                    'end_angle': end_angle,
                    'points': best_fit['points']
                })
                segment_start = best_end + 1
            else:
                # No good arc found, add as line segment
                end = min(segment_start + 10, len(points))
                segments.append({
                    'type': 'line',
                    'points': points[segment_start:end]
                })
                segment_start = end
        
        return segments
    
    @staticmethod
    def _fit_circle(points):
        """Fit a circle to a set of 2D points using least squares."""
        points = np.array(points)
        x = points[:, 0]
        y = points[:, 1]
        
        # Formulate and solve the least squares problem
        A = np.column_stack((2*x, 2*y, np.ones_like(x)))
        b = x**2 + y**2
        c = np.linalg.lstsq(A, b, rcond=None)[0]
        
        # Extract circle parameters
        xc = c[0]
        yc = c[1]
        r = np.sqrt(c[2] + xc**2 + yc**2)
        
        # Calculate fitting error
        distances = np.sqrt((x - xc)**2 + (y - yc)**2)
        error = np.mean((distances - r)**2)
        
        return (xc, yc), r, error
    
    @staticmethod
    def _are_colinear(points, tolerance=1e-6):
        """Check if points are colinear within a given tolerance."""
        if len(points) < 3:
            return True
            
        x = np.array(points)[:, 0]
        y = np.array(points)[:, 1]
        
        # Fit a line to the points
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
        
        # Calculate distances from points to the line
        distances = np.abs(m * x - y + c) / np.sqrt(m**2 + 1)
        
        return np.max(distances) < tolerance

    @staticmethod
    def convert_arcs_to_gcode(segments, feedrate=1000, z_height=None):
        """
        Convert a list of segments (lines and arcs) to G-code.
        
        Args:
            segments: List of segments from detect_arcs()
            feedrate: Feedrate for G1 moves
            z_height: Optional Z height for 3D moves
            
        Returns:
            List of G-code commands as strings
        """
        gcode = []
        current_pos = None
        
        for segment in segments:
            if segment['type'] == 'line':
                for point in segment['points']:
                    x, y = point
                    cmd = f"G1 X{x:.3f} Y{y:.3f}"
                    if z_height is not None:
                        cmd += f" Z{z_height:.3f}"
                    cmd += f" F{feedrate}"
                    gcode.append(cmd)
                    current_pos = (x, y, z_height) if z_height is not None else (x, y)
            
            elif segment['type'] == 'arc':
                # Convert arc to G2/G3 command
                x_start, y_start = segment['points'][0]
                x_end, y_end = segment['points'][-1]
                cx, cy = segment['center']
                
                # Determine direction (G2 = CW, G3 = CCW)
                cross = (x_start - cx) * (y_end - cy) - (y_start - cy) * (x_end - cx)
                cmd = "G2" if cross < 0 else "G3"
                
                # Calculate I and J offsets
                i = cx - x_start
                j = cy - y_start
                
                # Format G-code command
                gcode_cmd = f"{cmd} X{x_end:.3f} Y{y_end:.3f} I{i:.3f} J{j:.3f} F{feedrate}"
                if z_height is not None:
                    gcode_cmd = f"G1 Z{z_height:.3f} F{feedrate/2}\n" + gcode_cmd
                
                gcode.append(gcode_cmd)
                current_pos = (x_end, y_end, z_height) if z_height is not None else (x_end, y_end)
        
        return gcode

    @staticmethod
    def remove_redundant_moves(gcode_commands, tolerance=0.001):
        """
        Remove redundant G-code moves that don't change the tool position.
        
        Args:
            gcode_commands: List of G-code command strings
            tolerance: Minimum distance to consider a move non-redundant
            
        Returns:
            List of optimized G-code commands
        """
        if not gcode_commands:
            return []
            
        optimized = []
        last_pos = {'X': 0, 'Y': 0, 'Z': 0, 'E': 0, 'F': 0}
        
        for cmd in gcode_commands:
            # Skip comments and empty lines
            cmd = cmd.strip()
            if not cmd or cmd.startswith(';'):
                optimized.append(cmd)
                continue
                
            # Parse the command
            parts = cmd.split(';')[0].split()  # Remove comments and split
            if not parts:
                continue
                
            cmd_type = parts[0]
            
            # Only process G1 (linear move) and G0 (rapid move) commands
            if cmd_type not in ('G0', 'G1'):
                optimized.append(cmd)
                continue
                
            # Parse coordinates and parameters
            current_pos = last_pos.copy()
            has_movement = False
            
            for part in parts[1:]:
                if not part:
                    continue
                axis = part[0].upper()
                if axis in current_pos:
                    try:
                        value = float(part[1:])
                        current_pos[axis] = value
                        has_movement = True
                    except (ValueError, IndexError):
                        pass
            
            # Check if the move is redundant
            if has_movement:
                # Calculate movement distance
                distance_sq = 0
                for axis in 'XYZE':
                    if axis in current_pos and axis in last_pos:
                        delta = current_pos[axis] - last_pos[axis]
                        distance_sq += delta * delta
                
                if distance_sq >= tolerance * tolerance:
                    # Non-redundant move, keep it
                    optimized.append(cmd)
                    last_pos = current_pos
            else:
                # No movement, but might have other parameters (like feedrate)
                if 'F' in current_pos and current_pos['F'] != last_pos['F']:
                    optimized.append(f"G1 F{current_pos['F']:.1f}")
                    last_pos['F'] = current_pos['F']
        
        return optimized
    
    @staticmethod
    def smooth_extrusion(gcode_commands, window_size=5, max_deviation=0.05):
        """
        Smooth extrusion values to reduce sudden changes in flow rate.
        
        Args:
            gcode_commands: List of G-code command strings
            window_size: Number of points to consider for smoothing
            max_deviation: Maximum allowed deviation from original extrusion
            
        Returns:
            List of G-code commands with smoothed extrusion
        """
        if not gcode_commands:
            return []
            
        # First pass: extract all extrusion values and their positions
        extrusions = []
        for i, cmd in enumerate(gcode_commands):
            cmd = cmd.strip()
            if not cmd or cmd.startswith(';'):
                continue
                
            parts = cmd.split(';')[0].split()
            if not parts or parts[0] not in ('G0', 'G1'):
                continue
                
            for part in parts[1:]:
                if part.upper().startswith('E'):
                    try:
                        e_value = float(part[1:])
                        extrusions.append((i, e_value))
                    except (ValueError, IndexError):
                        pass
                    break
        
        if len(extrusions) < 3:  # Not enough points to smooth
            return gcode_commands
            
        # Apply moving average smoothing to extrusion values
        smoothed_extrusions = extrusions.copy()
        half_window = window_size // 2
        
        for i in range(len(extrusions)):
            start = max(0, i - half_window)
            end = min(len(extrusions), i + half_window + 1)
            window = extrusions[start:end]
            
            # Calculate average of the window
            avg = sum(e for _, e in window) / len(window)
            
            # Limit the change to max_deviation
            original_e = extrusions[i][1]
            if abs(avg - original_e) > max_deviation:
                if avg > original_e:
                    smoothed_e = original_e + max_deviation
                else:
                    smoothed_e = original_e - max_deviation
            else:
                smoothed_e = avg
                
            smoothed_extrusions[i] = (extrusions[i][0], smoothed_e)
        
        # Second pass: update the G-code with smoothed extrusion values
        result = gcode_commands.copy()
        for idx, e_value in smoothed_extrusions:
            cmd = result[idx].strip()
            if not cmd or cmd.startswith(';'):
                continue
                
            # Replace the extrusion value
            parts = cmd.split(';')
            gcode_parts = parts[0].split()
            
            # Find and update the E parameter
            for i, part in enumerate(gcode_parts[1:], 1):
                if part.upper().startswith('E'):
                    gcode_parts[i] = f"E{e_value:.5f}".rstrip('0').rstrip('.')
                    break
            
            # Reconstruct the command
            result[idx] = ' '.join(gcode_parts)
            if len(parts) > 1:  # Add back the comment if it existed
                result[idx] += ' ;' + ';'.join(parts[1:])
        
        return result
    
    @staticmethod
    def optimize_gcode(gcode_commands, optimize_level=2):
        """
        Apply multiple optimization passes to G-code.
        
        Args:
            gcode_commands: List of G-code command strings
            optimize_level: Optimization level (0=none, 1=basic, 2=aggressive)
            
        Returns:
            Optimized list of G-code commands
        """
        if not gcode_commands:
            return []
            
        optimized = gcode_commands
        
        # Always apply basic optimizations
        optimized = GCodeOptimizer.remove_redundant_moves(optimized)
        
        if optimize_level >= 1:
            # Apply medium-level optimizations
            optimized = GCodeOptimizer.smooth_extrusion(optimized)
            
            # Remove empty lines and trailing whitespace
            optimized = [line.rstrip() for line in optimized if line.strip()]
            
        if optimize_level >= 2:
            # Apply aggressive optimizations
            # Note: Arc detection would go here, but it requires more context
            # about the toolpath geometry
            pass
        
        return optimized

    @staticmethod
    def _heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate the Manhattan distance between two points."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def _get_neighbors(grid: List[List[int]], pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighbors for a position in the grid."""
        rows, cols = len(grid), len(grid[0])
        x, y = pos
        neighbors = [(x+dx, y+dy) for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]
                    if 0 <= x+dx < rows and 0 <= y+dy < cols and grid[x+dx][y+dy] == 0]
        return neighbors

    @staticmethod
    def astar_path(grid: List[List[int]], start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        A* pathfinding algorithm to find the shortest path in a grid.
        
        Args:
            grid: 2D grid where 0 is walkable and 1 is an obstacle
            start: Starting position (row, col)
            end: Target position (row, col)
            
        Returns:
            List of positions from start to end (inclusive)
        """
        import heapq
        
        # Priority queue: (f_score, count, position, path)
        count = 0
        open_set = [(0, count, start, [start])]
        heapq.heapify(open_set)
        
        # Track visited nodes and their g_scores
        g_scores = {start: 0}
        f_scores = {start: GCodeOptimizer._heuristic(start, end)}
        
        open_set_hash = {start}
        
        while open_set:
            _, _, current, path = heapq.heappop(open_set)
            open_set_hash.remove(current)
            
            if current == end:
                return path
                
            for neighbor in GCodeOptimizer._get_neighbors(grid, current):
                # Tentative g_score
                tentative_g_score = g_scores[current] + 1
                
                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g_score
                    f_score = tentative_g_score + GCodeOptimizer._heuristic(neighbor, end)
                    
                    if neighbor not in open_set_hash:
                        count += 1
                        new_path = path + [neighbor]
                        heapq.heappush(open_set, (f_score, count, neighbor, new_path))
                        open_set_hash.add(neighbor)
                        f_scores[neighbor] = f_score
        
        return []  # No path found

    @staticmethod
    def _raster_to_world(grid_pos: Tuple[int, int], cell_size: float, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates."""
        x_min, y_min, _, _ = bounds
        return (x_min + grid_pos[1] * cell_size, y_min + grid_pos[0] * cell_size)

    @staticmethod
    def generate_optimized_infill(bounds: Tuple[float, float, float, float], 
                                angle: float = 45,
                                spacing: float = 5.0,
                                resolution: float = 1.0) -> List[Tuple[float, float, float, float]]:
        """
        Generate optimized infill pattern using A* path planning.
        
        Args:
            bounds: (x_min, y_min, x_max, y_max) bounding box for infill
            angle: Angle of infill lines in degrees (0-180)
            spacing: Distance between infill lines
            resolution: Grid resolution in mm
            
        Returns:
            List of (x1, y1, x2, y2) line segments
        """
        try:
            # Convert angle to radians
            angle_rad = math.radians(angle)
            
            # Generate grid points based on resolution
            x_min, y_min, x_max, y_max = bounds
            width = x_max - x_min
            height = y_max - y_min
            diagonal = math.sqrt(width**2 + height**2)
            
            # Generate infill lines
            lines = []
            d = 0
            
            while d < diagonal:
                # Calculate line endpoints
                if angle_rad <= math.pi/4 or angle_rad >= 3*math.pi/4:
                    # More horizontal lines
                    x1 = x_min - height / math.tan(angle_rad)
                    y1 = y_min
                    x2 = x_min + height / math.tan(angle_rad)
                    y2 = y_max
                    
                    # Offset the line
                    x1 += d * math.cos(angle_rad)
                    y1 += d * math.sin(angle_rad)
                    x2 += d * math.cos(angle_rad)
                    y2 += d * math.sin(angle_rad)
                else:
                    # More vertical lines
                    x1 = x_min
                    y1 = y_min - width * math.tan(angle_rad)
                    x2 = x_max
                    y2 = y_min + width * math.tan(angle_rad)
                    
                    # Offset the line
                    x1 += d * math.cos(angle_rad)
                    y1 += d * math.sin(angle_rad)
                    x2 += d * math.cos(angle_rad)
                    y2 += d * math.sin(angle_rad)
                
                # Clip line to bounds
                line = GCodeOptimizer._clip_line_to_bounds((x1, y1, x2, y2), bounds)
                if line:
                    lines.append(line)
                
                d += spacing
            
            if not lines:
                return []
            
            # Optimize path using nearest neighbor
            optimized = []
            remaining = lines.copy()
            
            # Start with the first line
            current = remaining.pop(0)
            optimized.append(current)
            
            while remaining:
                # Find the closest line to the current end point
                last_x2, last_y2 = current[2], current[3]
                
                # Find closest line (start or end point)
                closest = min(remaining, 
                             key=lambda s: min(
                                 (s[0] - last_x2)**2 + (s[1] - last_y2)**2,  # Start to last end
                                 (s[2] - last_x2)**2 + (s[3] - last_y2)**2   # End to last end
                             ))
                remaining.remove(closest)
                
                # Add the closest segment in the optimal direction
                start_dist = (closest[0] - last_x2)**2 + (closest[1] - last_y2)**2
                end_dist = (closest[2] - last_x2)**2 + (closest[3] - last_y2)**2
                
                if start_dist <= end_dist:
                    optimized.append(closest)
                else:
                    # Reverse the segment
                    optimized.append((closest[2], closest[3], closest[0], closest[1]))
                
                current = optimized[-1]
            
            # Ensure all lines are tuples of 4 floats
            return [tuple(float(x) for x in line) for line in optimized]
            
        except Exception as e:
            logging.error(f"Error in generate_optimized_infill: {e}")
            # Fall back to basic infill pattern if optimization fails
            return GCodeOptimizer.generate_infill_pattern(bounds, angle, spacing)

    @staticmethod
    def _clip_line_to_bounds(line: Tuple[float, float, float, float], 
                           bounds: Tuple[float, float, float, float]) -> Optional[Tuple[float, float, float, float]]:
        """Clip a line segment to the given bounds using Liang-Barsky algorithm."""
        x1, y1, x2, y2 = line
        x_min, y_min, x_max, y_max = bounds
        
        # Check if line is completely outside bounds
        if (x1 < x_min and x2 < x_min) or (x1 > x_max and x2 > x_max) or \
           (y1 < y_min and y2 < y_min) or (y1 > y_max and y2 > y_max):
            return None
        
        # Check if line is completely inside bounds
        if (x_min <= x1 <= x_max and x_min <= x2 <= x_max and
            y_min <= y1 <= y_max and y_min <= y2 <= y_max):
            return (x1, y1, x2, y2)
        
        # Use Liang-Barsky algorithm to clip the line
        dx = x2 - x1
        dy = y2 - y1
        p = [-dx, dx, -dy, dy]
        q = [x1 - x_min, x_max - x1, y1 - y_min, y_max - y1]
        
        u1 = 0.0
        u2 = 1.0
        
        for i in range(4):
            if p[i] == 0:
                if q[i] < 0:
                    return None  # Line is parallel and outside the boundary
            else:
                t = q[i] / p[i]
                if p[i] < 0:
                    u1 = max(u1, t)
                else:
                    u2 = min(u2, t)
                    
                if u1 > u2:
                    return None  # Line is outside the boundary
        
        # Calculate new endpoints
        nx1 = x1 + u1 * dx
        ny1 = y1 + u1 * dy
        nx2 = x1 + u2 * dx
        ny2 = y1 + u2 * dy
        
        return (nx1, ny1, nx2, ny2)
