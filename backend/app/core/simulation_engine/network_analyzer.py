"""
Network Analyzer Implementation (SE-2.2)
Handles road network analysis and pathfinding with obstruction awareness.
"""

import heapq
import math
import uuid
from typing import Dict, List, Set, Tuple, Optional, Any
import networkx as nx
from shapely.geometry import Point, Polygon, LineString

from .models import (
    PathfindingRequest,
    PathfindingResult,
    RoadObstruction,
    VehicleType,
    VehicleConfig,
    DEFAULT_VEHICLE_CONFIGS
)


class NetworkAnalyzer:
    """
    Implements SE-2.2: Road Network Analysis
    
    Provides pathfinding capabilities with awareness of road obstructions
    and vehicle-specific requirements (width, turning radius, etc.)
    """
    
    def __init__(self):
        """Initialize the network analyzer."""
        self.road_graph: Optional[nx.Graph] = None
        self.road_obstructions: Dict[str, RoadObstruction] = {}
        self.vehicle_configs = DEFAULT_VEHICLE_CONFIGS
    
    def initialize_road_network(
        self,
        nodes_data: Dict[str, Any],
        edges_data: Dict[str, Any]
    ):
        """
        Initialize the road network graph from world synthesizer data.
        
        Args:
            nodes_data: Dictionary of road network nodes
            edges_data: Dictionary of road network edges
        """
        self.road_graph = nx.Graph()
        
        # Add nodes to the graph
        for node_id, node_data in nodes_data.items():
            self.road_graph.add_node(
                node_id,
                x=node_data['x'],
                y=node_data['y'],
                type=node_data.get('type', 'intersection')
            )
        
        # Add edges to the graph
        for edge_id, edge_data in edges_data.items():
            from_node = edge_data['from_node']
            to_node = edge_data['to_node']
            
            # Calculate edge length (Euclidean distance)
            from_coords = (nodes_data[from_node]['x'], nodes_data[from_node]['y'])
            to_coords = (nodes_data[to_node]['x'], nodes_data[to_node]['y'])
            distance = self._calculate_distance(from_coords, to_coords)
            
            self.road_graph.add_edge(
                from_node,
                to_node,
                edge_id=edge_id,
                distance=distance,
                width=edge_data.get('width', 6.0),
                lanes=edge_data.get('lanes', 2),
                is_bidirectional=edge_data.get('is_bidirectional', True),
                road_type=edge_data.get('road_type', 'secondary'),
                speed_limit=edge_data.get('speed_limit', 40.0),
                original_width=edge_data.get('width', 6.0)  # Store original width
            )
    
    def update_obstructions(self, obstructions: List[RoadObstruction]):
        """
        Update road obstructions and modify graph edge weights accordingly.
        
        Args:
            obstructions: List of RoadObstruction objects
        """
        # Clear previous obstructions
        self.road_obstructions = {}
        
        # Reset all edges to original width
        for u, v, data in self.road_graph.edges(data=True):
            data['width'] = data['original_width']
        
        # Apply new obstructions
        for obstruction in obstructions:
            self.road_obstructions[obstruction.obstruction_id] = obstruction
            
            # Find the edge corresponding to this road
            edge = self._find_edge_by_id(obstruction.road_edge_id)
            if edge:
                u, v = edge
                # Update the effective width for this edge
                self.road_graph[u][v]['width'] = obstruction.remaining_width
    
    def find_path(
        self,
        request: PathfindingRequest
    ) -> PathfindingResult:
        """
        Find the optimal path between two points for a specific vehicle type.
        
        Implements A* pathfinding with obstruction awareness and vehicle constraints.
        
        Args:
            request: PathfindingRequest with start/end points and vehicle type
            
        Returns:
            PathfindingResult with path details or failure indication
        """
        if not self.road_graph:
            return PathfindingResult(
                success=False,
                path_coordinates=[],
                path_node_ids=[],
                total_distance=0.0,
                estimated_travel_time=0.0,
                vehicle_type=request.vehicle_type,
                blocked_roads=[]
            )
        
        # Find nearest nodes to start and end points
        start_node = self._find_nearest_node(request.start_point)
        end_node = self._find_nearest_node(request.end_point)
        
        if not start_node or not end_node:
            return PathfindingResult(
                success=False,
                path_coordinates=[],
                path_node_ids=[],
                total_distance=0.0,
                estimated_travel_time=0.0,
                vehicle_type=request.vehicle_type,
                blocked_roads=[]
            )
        
        # Get vehicle configuration
        vehicle_config = self.vehicle_configs.get(
            request.vehicle_type,
            DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )
        
        # Perform A* pathfinding with vehicle constraints
        try:
            path_nodes = self._astar_pathfinding(
                start_node, end_node, vehicle_config, request.max_travel_time
            )
            
            if not path_nodes:
                return PathfindingResult(
                    success=False,
                    path_coordinates=[],
                    path_node_ids=[],
                    total_distance=0.0,
                    estimated_travel_time=0.0,
                    vehicle_type=request.vehicle_type,
                    blocked_roads=[]
                )
            
            # Convert path to coordinates and calculate metrics
            path_coordinates = self._nodes_to_coordinates(path_nodes)
            total_distance = self._calculate_path_distance(path_nodes)
            travel_time = self._estimate_travel_time(path_nodes, vehicle_config)
            blocked_roads = self._identify_blocked_roads_in_path(path_nodes)
            
            # Add actual start and end points to path coordinates
            if path_coordinates:
                path_coordinates[0] = request.start_point
                path_coordinates[-1] = request.end_point
            
            return PathfindingResult(
                success=True,
                path_coordinates=path_coordinates,
                path_node_ids=path_nodes,
                total_distance=total_distance,
                estimated_travel_time=travel_time,
                vehicle_type=request.vehicle_type,
                blocked_roads=blocked_roads
            )
            
        except Exception as e:
            return PathfindingResult(
                success=False,
                path_coordinates=[],
                path_node_ids=[],
                total_distance=0.0,
                estimated_travel_time=0.0,
                vehicle_type=request.vehicle_type,
                blocked_roads=[],
            )
    
    def _find_nearest_node(self, point: Tuple[float, float]) -> Optional[str]:
        """
        Find the nearest road network node to a given point.
        
        Args:
            point: Coordinates (x, y)
            
        Returns:
            Node ID of the nearest node, or None if no nodes available
        """
        if not self.road_graph.nodes():
            return None
        
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, node_data in self.road_graph.nodes(data=True):
            node_point = (node_data['x'], node_data['y'])
            distance = self._calculate_distance(point, node_point)
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node
    
    def _astar_pathfinding(
        self,
        start_node: str,
        end_node: str,
        vehicle_config: VehicleConfig,
        max_travel_time: Optional[float] = None
    ) -> List[str]:
        """
        A* pathfinding algorithm with vehicle constraints and obstruction awareness.
        
        Implements SE-2.2 requirements:
        - Cost based on road_length / speed_limit
        - Dynamic checking of vehicle width vs remaining road width
        - Infinite cost for impassable roads
        
        Args:
            start_node: Starting node ID
            end_node: Destination node ID
            vehicle_config: Vehicle configuration for constraints
            max_travel_time: Maximum allowed travel time in seconds
            
        Returns:
            List of node IDs forming the optimal path, empty if no path found
        """
        if start_node == end_node:
            return [start_node]
        
        # Priority queue: (f_score, g_score, current_node, path)
        open_set = [(0, 0, start_node, [start_node])]
        closed_set: Set[str] = set()
        
        # Best g_score for each node
        g_scores = {start_node: 0}
        
        end_coords = (
            self.road_graph.nodes[end_node]['x'],
            self.road_graph.nodes[end_node]['y']
        )
        
        while open_set:
            f_score, g_score, current_node, path = heapq.heappop(open_set)
            
            if current_node in closed_set:
                continue
            
            closed_set.add(current_node)
            
            if current_node == end_node:
                return path
            
            # Check time constraint
            if max_travel_time and g_score > max_travel_time:
                continue
            
            # Explore neighbors
            for neighbor in self.road_graph.neighbors(current_node):
                if neighbor in closed_set:
                    continue
                
                edge_data = self.road_graph[current_node][neighbor]
                
                # Check if vehicle can use this edge
                if not self._can_vehicle_use_edge(vehicle_config, edge_data):
                    continue
                
                # Calculate cost to move to neighbor
                move_cost = self._calculate_edge_cost(
                    current_node, neighbor, vehicle_config
                )
                
                tentative_g_score = g_score + move_cost
                
                if (neighbor not in g_scores or 
                    tentative_g_score < g_scores[neighbor]):
                    
                    g_scores[neighbor] = tentative_g_score
                    
                    # Calculate heuristic (Euclidean distance)
                    neighbor_coords = (
                        self.road_graph.nodes[neighbor]['x'],
                        self.road_graph.nodes[neighbor]['y']
                    )
                    h_score = self._calculate_distance(neighbor_coords, end_coords)
                    
                    f_score = tentative_g_score + h_score
                    
                    new_path = path + [neighbor]
                    heapq.heappush(open_set, (f_score, tentative_g_score, neighbor, new_path))
        
        # No path found
        return []
    
    def _can_vehicle_use_edge(
        self,
        vehicle_config: VehicleConfig,
        edge_data: Dict[str, Any]
    ) -> bool:
        """
        Check if a vehicle can use a road edge given current obstructions.
        
        Implements comprehensive vehicle constraint checking:
        - Road width vs vehicle width
        - Road type compatibility
        - Physical vehicle limitations
        
        Args:
            vehicle_config: Vehicle configuration
            edge_data: Road edge data
            
        Returns:
            True if vehicle can pass, False otherwise
        """
        current_width = edge_data.get('width', 6.0)
        min_required_width = vehicle_config.minimum_road_width
        road_type = edge_data.get('road_type', 'secondary')
        
        # Basic width check
        if current_width < min_required_width:
            return False
        
        # Road type compatibility check
        if hasattr(vehicle_config, 'prohibited_road_types'):
            if road_type in vehicle_config.prohibited_road_types:
                return False
        
        # Emergency vehicle special access (if implemented)
        if (hasattr(vehicle_config, 'emergency_vehicle') and 
            vehicle_config.emergency_vehicle and
            current_width >= min_required_width * 0.8):  # 20% tolerance for emergency vehicles
            return True
        
        # Tight passage warning threshold (for future enhancements)
        if current_width < min_required_width * 1.1:
            # Vehicle can pass but with difficulty - add penalty in cost calculation
            pass
        
        return True
    
    def _calculate_edge_cost(
        self,
        from_node: str,
        to_node: str,
        vehicle_config: VehicleConfig
    ) -> float:
        """
        Calculate the cost of traversing an edge for a specific vehicle.
        
        Implements SE-2.2 requirement: cost based on road_length / speed_limit
        with vehicle-specific constraints and obstruction penalties.
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            vehicle_config: Vehicle configuration
            
        Returns:
            Edge traversal cost (travel time in seconds), or float('inf') if impassable
        """
        edge_data = self.road_graph[from_node][to_node]
        
        distance = edge_data['distance']
        speed_limit = edge_data.get('speed_limit', 40.0)  # km/h
        vehicle_max_speed = vehicle_config.max_speed
        current_width = edge_data.get('width', 6.0)
        min_required_width = vehicle_config.minimum_road_width
        
        # SE-2.2: Check if vehicle can physically pass through
        if current_width < min_required_width:
            return float('inf')  # Impassable - infinite cost
        
        # Calculate base travel time using SE-2.2 formula: distance / speed
        effective_speed = min(speed_limit, vehicle_max_speed)
        
        # Convert km/h to m/s
        speed_ms = effective_speed * 1000 / 3600
        base_travel_time = distance / speed_ms
        
        # Apply penalties for narrow passages and obstructions
        width_ratio = current_width / edge_data.get('original_width', current_width)
        
        if width_ratio < 0.5:
            # Severely obstructed - high time penalty
            base_travel_time *= 3.0
        elif width_ratio < 0.7:
            # Moderately obstructed - moderate penalty
            base_travel_time *= 2.0
        elif current_width < min_required_width * 1.2:
            # Tight fit - small penalty
            base_travel_time *= 1.3
        
        return base_travel_time
    
    def _calculate_distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two points."""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _nodes_to_coordinates(self, path_nodes: List[str]) -> List[Tuple[float, float]]:
        """Convert a list of node IDs to coordinate tuples."""
        coordinates = []
        for node_id in path_nodes:
            node_data = self.road_graph.nodes[node_id]
            coordinates.append((node_data['x'], node_data['y']))
        return coordinates
    
    def _calculate_path_distance(self, path_nodes: List[str]) -> float:
        """Calculate total distance of a path."""
        total_distance = 0.0
        
        for i in range(len(path_nodes) - 1):
            from_node = path_nodes[i]
            to_node = path_nodes[i + 1]
            edge_data = self.road_graph[from_node][to_node]
            total_distance += edge_data['distance']
        
        return total_distance
    
    def _estimate_travel_time(
        self,
        path_nodes: List[str],
        vehicle_config: VehicleConfig
    ) -> float:
        """Estimate total travel time for a path."""
        total_time = 0.0
        
        for i in range(len(path_nodes) - 1):
            from_node = path_nodes[i]
            to_node = path_nodes[i + 1]
            edge_cost = self._calculate_edge_cost(from_node, to_node, vehicle_config)
            total_time += edge_cost
        
        return total_time
    
    def _identify_blocked_roads_in_path(self, path_nodes: List[str]) -> List[str]:
        """Identify which roads in the path have obstructions."""
        blocked_roads = []
        
        for i in range(len(path_nodes) - 1):
            from_node = path_nodes[i]
            to_node = path_nodes[i + 1]
            
            edge_data = self.road_graph[from_node][to_node]
            edge_id = edge_data.get('edge_id')
            
            # Check if this edge has any obstructions
            for obstruction in self.road_obstructions.values():
                if obstruction.road_edge_id == edge_id:
                    blocked_roads.append(edge_id)
                    break
        
        return blocked_roads
    
    def _find_edge_by_id(self, edge_id: str) -> Optional[Tuple[str, str]]:
        """Find an edge in the graph by its ID."""
        for u, v, data in self.road_graph.edges(data=True):
            if data.get('edge_id') == edge_id:
                return (u, v)
        return None
    
    def calculate_service_area(
        self,
        center_point: Tuple[float, float],
        vehicle_type: VehicleType,
        max_travel_time: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate service area (isochrone) from a center point.
        
        Implements SE-2.2 isochrone generation using Dijkstra's algorithm
        to find all points reachable within specified travel time.
        
        Args:
            center_point: Center coordinates (x, y)
            vehicle_type: Type of vehicle for constraints
            max_travel_time: Maximum travel time in seconds
            
        Returns:
            List of coordinates forming the boundary of the service area
        """
        if not self.road_graph:
            return []
        
        center_node = self._find_nearest_node(center_point)
        if not center_node:
            return []
        
        vehicle_config = self.vehicle_configs.get(
            vehicle_type,
            DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )
        
        # Use Dijkstra's algorithm to find all reachable nodes within time limit
        reachable_points = []
        distances = {center_node: 0.0}
        visited = set()
        queue = [(0.0, center_node)]  # (cumulative_time, node_id)
        
        while queue:
            cumulative_time, current_node = heapq.heappop(queue)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Add this node to reachable points
            node_data = self.road_graph.nodes[current_node]
            reachable_points.append((node_data['x'], node_data['y']))
            
            # Explore neighbors
            for neighbor in self.road_graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                
                edge_data = self.road_graph[current_node][neighbor]
                
                # Check vehicle compatibility
                if not self._can_vehicle_use_edge(vehicle_config, edge_data):
                    continue
                
                # Calculate edge travel time
                travel_time = self._calculate_edge_cost(
                    current_node, neighbor, vehicle_config
                )
                
                # Skip if infinite cost (impassable)
                if travel_time == float('inf'):
                    continue
                
                total_time = cumulative_time + travel_time
                
                # Only process if within time limit and better than known distance
                if (total_time <= max_travel_time and 
                    (neighbor not in distances or total_time < distances[neighbor])):
                    distances[neighbor] = total_time
                    heapq.heappush(queue, (total_time, neighbor))
        
        # Generate service area boundary
        if len(reachable_points) < 3:
            return reachable_points
        
        # Create convex hull for service area boundary
        try:
            from shapely.geometry import MultiPoint
            points = MultiPoint(reachable_points)
            convex_hull = points.convex_hull
            
            if hasattr(convex_hull, 'exterior'):
                return list(convex_hull.exterior.coords)
            else:
                return reachable_points
                
        except Exception:
            # Fallback to original points if convex hull fails
            return reachable_points
    
    def calculate_multiple_isochrones(
        self,
        center_point: Tuple[float, float],
        vehicle_type: VehicleType,
        time_intervals: List[float]
    ) -> Dict[float, List[Tuple[float, float]]]:
        """
        Calculate multiple isochrones for different time intervals.
        
        More efficient than calling calculate_service_area multiple times
        as it reuses the Dijkstra computation.
        
        Args:
            center_point: Center coordinates (x, y)
            vehicle_type: Type of vehicle for constraints
            time_intervals: List of time intervals in seconds
            
        Returns:
            Dictionary mapping time intervals to service area coordinates
        """
        if not self.road_graph or not time_intervals:
            return {}
        
        center_node = self._find_nearest_node(center_point)
        if not center_node:
            return {}
        
        vehicle_config = self.vehicle_configs.get(
            vehicle_type,
            DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )
        
        # Sort time intervals for efficient processing
        sorted_intervals = sorted(time_intervals)
        max_time = max(sorted_intervals)
        
        # Run single Dijkstra to find all reachable nodes
        distances = {center_node: 0.0}
        visited = set()
        queue = [(0.0, center_node)]
        node_times = {}  # node_id -> travel_time
        
        while queue:
            cumulative_time, current_node = heapq.heappop(queue)
            
            if current_node in visited or cumulative_time > max_time:
                continue
            
            visited.add(current_node)
            node_times[current_node] = cumulative_time
            
            # Explore neighbors
            for neighbor in self.road_graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                
                edge_data = self.road_graph[current_node][neighbor]
                
                if not self._can_vehicle_use_edge(vehicle_config, edge_data):
                    continue
                
                travel_time = self._calculate_edge_cost(
                    current_node, neighbor, vehicle_config
                )
                
                if travel_time == float('inf'):
                    continue
                
                total_time = cumulative_time + travel_time
                
                if (total_time <= max_time and 
                    (neighbor not in distances or total_time < distances[neighbor])):
                    distances[neighbor] = total_time
                    heapq.heappush(queue, (total_time, neighbor))
        
        # Generate isochrones for each time interval
        isochrones = {}
        
        for time_limit in sorted_intervals:
            reachable_points = []
            
            for node_id, travel_time in node_times.items():
                if travel_time <= time_limit:
                    node_data = self.road_graph.nodes[node_id]
                    reachable_points.append((node_data['x'], node_data['y']))
            
            # Generate boundary for this time interval
            if len(reachable_points) >= 3:
                try:
                    from shapely.geometry import MultiPoint
                    points = MultiPoint(reachable_points)
                    convex_hull = points.convex_hull
                    
                    if hasattr(convex_hull, 'exterior'):
                        isochrones[time_limit] = list(convex_hull.exterior.coords)
                    else:
                        isochrones[time_limit] = reachable_points
                except Exception:
                    isochrones[time_limit] = reachable_points
            else:
                isochrones[time_limit] = reachable_points
        
        return isochrones
    
    def analyze_road_network_connectivity(
        self,
        vehicle_type: VehicleType
    ) -> Dict[str, Any]:
        """
        Analyze road network connectivity for a specific vehicle type.
        
        Useful for understanding how obstructions affect overall network accessibility.
        
        Args:
            vehicle_type: Type of vehicle for analysis
            
        Returns:
            Dictionary with connectivity statistics
        """
        if not self.road_graph:
            return {}
        
        vehicle_config = self.vehicle_configs.get(
            vehicle_type,
            DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )
        
        total_edges = 0
        passable_edges = 0
        blocked_edges = 0
        severely_obstructed_edges = 0
        
        total_road_length = 0.0
        passable_road_length = 0.0
        
        for u, v, edge_data in self.road_graph.edges(data=True):
            total_edges += 1
            distance = edge_data.get('distance', 0.0)
            total_road_length += distance
            
            current_width = edge_data.get('width', 6.0)
            original_width = edge_data.get('original_width', current_width)
            min_required_width = vehicle_config.minimum_road_width
            
            if current_width >= min_required_width:
                passable_edges += 1
                passable_road_length += distance
                
                # Check obstruction level
                width_ratio = current_width / original_width
                if width_ratio < 0.5:
                    severely_obstructed_edges += 1
            else:
                blocked_edges += 1
        
        # Calculate connected components for passable roads
        passable_graph = self.road_graph.copy()
        edges_to_remove = []
        
        for u, v, edge_data in passable_graph.edges(data=True):
            current_width = edge_data.get('width', 6.0)
            if current_width < vehicle_config.minimum_road_width:
                edges_to_remove.append((u, v))
        
        passable_graph.remove_edges_from(edges_to_remove)
        
        import networkx as nx
        connected_components = list(nx.connected_components(passable_graph))
        
        return {
            'vehicle_type': vehicle_type.value,
            'total_edges': total_edges,
            'passable_edges': passable_edges,
            'blocked_edges': blocked_edges,
            'severely_obstructed_edges': severely_obstructed_edges,
            'passability_percentage': (passable_edges / total_edges * 100) if total_edges > 0 else 0,
            'total_road_length_km': total_road_length / 1000,
            'passable_road_length_km': passable_road_length / 1000,
            'connected_components': len(connected_components),
            'largest_component_size': max(len(comp) for comp in connected_components) if connected_components else 0,
            'network_fragmentation': len(connected_components) > 1
        }
    
    def find_alternative_paths(
        self,
        request: PathfindingRequest,
        max_alternatives: int = 3,
        diversity_factor: float = 1.5
    ) -> List[PathfindingResult]:
        """
        Find multiple alternative paths between two points.
        
        Useful for emergency response planning and route redundancy analysis.
        Uses a modified A* with edge penalty increases to find diverse routes.
        
        Args:
            request: PathfindingRequest with start/end points and vehicle type
            max_alternatives: Maximum number of alternative paths to find
            diversity_factor: Factor to increase cost of previously used edges
            
        Returns:
            List of PathfindingResult objects, ordered by cost
        """
        if not self.road_graph:
            return []
        
        vehicle_config = self.vehicle_configs.get(
            request.vehicle_type,
            DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )
        
        alternatives = []
        edge_usage_count = {}  # Track how many times each edge has been used
        
        # Find nearest nodes
        start_node = self._find_nearest_node(request.start_point)
        end_node = self._find_nearest_node(request.end_point)
        
        if not start_node or not end_node:
            return []
        
        for attempt in range(max_alternatives):
            # Create modified cost function with edge penalties
            def get_modified_edge_cost(from_node: str, to_node: str) -> float:
                base_cost = self._calculate_edge_cost(from_node, to_node, vehicle_config)
                
                if base_cost == float('inf'):
                    return base_cost
                
                # Add penalty for previously used edges
                edge_key = (from_node, to_node)
                reverse_key = (to_node, from_node)
                usage = edge_usage_count.get(edge_key, 0) + edge_usage_count.get(reverse_key, 0)
                
                if usage > 0:
                    penalty = base_cost * (diversity_factor - 1.0) * usage
                    return base_cost + penalty
                
                return base_cost
            
            # Find path with modified costs
            path_nodes = self._astar_pathfinding_with_custom_cost(
                start_node, end_node, vehicle_config, 
                request.max_travel_time, get_modified_edge_cost
            )
            
            if not path_nodes:
                break  # No more paths found
            
            # Check if this path is significantly different
            if self._is_path_sufficiently_different(path_nodes, alternatives):
                # Convert to PathfindingResult
                path_coordinates = self._nodes_to_coordinates(path_nodes)
                total_distance = self._calculate_path_distance(path_nodes)
                travel_time = self._estimate_travel_time(path_nodes, vehicle_config)
                blocked_roads = self._identify_blocked_roads_in_path(path_nodes)
                
                # Add actual start and end points
                if path_coordinates:
                    path_coordinates[0] = request.start_point
                    path_coordinates[-1] = request.end_point
                
                alternative = PathfindingResult(
                    success=True,
                    path_coordinates=path_coordinates,
                    path_node_ids=path_nodes,
                    total_distance=total_distance,
                    estimated_travel_time=travel_time,
                    vehicle_type=request.vehicle_type,
                    blocked_roads=blocked_roads
                )
                
                alternatives.append(alternative)
                
                # Update edge usage count
                for i in range(len(path_nodes) - 1):
                    edge_key = (path_nodes[i], path_nodes[i + 1])
                    edge_usage_count[edge_key] = edge_usage_count.get(edge_key, 0) + 1
            
            else:
                # Path too similar, stop searching
                break
        
        return alternatives
    
    def _astar_pathfinding_with_custom_cost(
        self,
        start_node: str,
        end_node: str,
        vehicle_config: VehicleConfig,
        max_travel_time: Optional[float],
        cost_function
    ) -> List[str]:
        """
        A* pathfinding with custom cost function for alternative path finding.
        
        Args:
            start_node: Starting node ID
            end_node: Destination node ID
            vehicle_config: Vehicle configuration
            max_travel_time: Maximum allowed travel time
            cost_function: Custom function to calculate edge costs
            
        Returns:
            List of node IDs forming the path
        """
        if start_node == end_node:
            return [start_node]
        
        # Priority queue: (f_score, g_score, current_node, path)
        open_set = [(0, 0, start_node, [start_node])]
        closed_set: Set[str] = set()
        g_scores = {start_node: 0}
        
        end_coords = (
            self.road_graph.nodes[end_node]['x'],
            self.road_graph.nodes[end_node]['y']
        )
        
        while open_set:
            f_score, g_score, current_node, path = heapq.heappop(open_set)
            
            if current_node in closed_set:
                continue
            
            closed_set.add(current_node)
            
            if current_node == end_node:
                return path
            
            if max_travel_time and g_score > max_travel_time:
                continue
            
            for neighbor in self.road_graph.neighbors(current_node):
                if neighbor in closed_set:
                    continue
                
                edge_data = self.road_graph[current_node][neighbor]
                
                if not self._can_vehicle_use_edge(vehicle_config, edge_data):
                    continue
                
                # Use custom cost function
                move_cost = cost_function(current_node, neighbor)
                
                if move_cost == float('inf'):
                    continue
                
                tentative_g_score = g_score + move_cost
                
                if (neighbor not in g_scores or 
                    tentative_g_score < g_scores[neighbor]):
                    
                    g_scores[neighbor] = tentative_g_score
                    
                    neighbor_coords = (
                        self.road_graph.nodes[neighbor]['x'],
                        self.road_graph.nodes[neighbor]['y']
                    )
                    h_score = self._calculate_distance(neighbor_coords, end_coords)
                    
                    f_score = tentative_g_score + h_score
                    new_path = path + [neighbor]
                    heapq.heappush(open_set, (f_score, tentative_g_score, neighbor, new_path))
        
        return []
    
    def _is_path_sufficiently_different(
        self,
        new_path: List[str],
        existing_paths: List[PathfindingResult],
        min_difference_ratio: float = 0.3
    ) -> bool:
        """
        Check if a new path is sufficiently different from existing paths.
        
        Args:
            new_path: New path as list of node IDs
            existing_paths: List of existing PathfindingResult objects
            min_difference_ratio: Minimum ratio of different edges required
            
        Returns:
            True if path is sufficiently different
        """
        if not existing_paths:
            return True
        
        new_path_edges = set()
        for i in range(len(new_path) - 1):
            edge = (new_path[i], new_path[i + 1])
            new_path_edges.add(edge)
            new_path_edges.add((edge[1], edge[0]))  # Add reverse edge
        
        for existing in existing_paths:
            existing_edges = set()
            existing_path = existing.path_node_ids
            
            for i in range(len(existing_path) - 1):
                edge = (existing_path[i], existing_path[i + 1])
                existing_edges.add(edge)
                existing_edges.add((edge[1], edge[0]))  # Add reverse edge
            
            # Calculate overlap ratio
            common_edges = new_path_edges.intersection(existing_edges)
            if len(new_path_edges) > 0:
                difference_ratio = 1.0 - (len(common_edges) / len(new_path_edges))
                
                if difference_ratio < min_difference_ratio:
                    return False  # Too similar to existing path
        
        return True