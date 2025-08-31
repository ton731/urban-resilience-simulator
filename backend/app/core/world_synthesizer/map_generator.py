import uuid
import random
import math
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, field
import networkx as nx
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union


@dataclass
class MapNode:
    """Represents a node (intersection) in the road network"""
    id: str
    x: float
    y: float
    node_type: str = "intersection"  # "intersection", "facility"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "type": self.node_type
        }


@dataclass 
class RoadEdge:
    """Represents a road segment between two nodes"""
    id: str
    from_node: str
    to_node: str
    width: float  # in meters
    lanes: int
    is_bidirectional: bool = True
    road_type: str = "secondary"  # "main", "secondary"
    speed_limit: float = 50.0  # km/h
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "width": self.width,
            "lanes": self.lanes,
            "is_bidirectional": self.is_bidirectional,
            "road_type": self.road_type,
            "speed_limit": self.speed_limit
        }


@dataclass
class MapBoundary:
    """Defines the geographical boundaries of the map"""
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 2000.0
    max_y: float = 2000.0
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property 
    def height(self) -> float:
        return self.max_y - self.min_y
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "width": self.width,
            "height": self.height
        }


@dataclass
class GeneratedMap:
    """Container for all generated map data"""
    boundary: MapBoundary
    nodes: Dict[str, MapNode] = field(default_factory=dict)
    edges: Dict[str, RoadEdge] = field(default_factory=dict)
    trees: Dict[str, Any] = field(default_factory=dict)  # Will contain Tree objects
    facilities: Dict[str, Any] = field(default_factory=dict)  # Will contain Facility objects
    buildings: Dict[str, Any] = field(default_factory=dict)  # Will contain Building objects
    graph: nx.Graph = field(default_factory=nx.Graph)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary": self.boundary.to_dict(),
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()},
            "trees": {tree_id: tree.to_dict() for tree_id, tree in self.trees.items()},
            "facilities": {facility_id: facility.to_dict() for facility_id, facility in self.facilities.items()},
            "buildings": {building_id: building.to_dict() for building_id, building in self.buildings.items()},
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "tree_count": len(self.trees),
            "facility_count": len(self.facilities),
            "building_count": len(self.buildings)
        }


class MapGenerator:
    """
    Implements WS-1.1: Procedural Map Generation
    
    Generates a 2D grid map with geographical boundaries and creates
    random but logical road networks with main roads and secondary roads.
    Roads are stored as graph data structure with nodes and edges.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.map_size = config.get("map_size", [2000, 2000])
        self.road_density = config.get("road_density", 0.7)
        self.main_road_count = config.get("main_road_count", 4)
        self.secondary_road_density = config.get("secondary_road_density", 0.5)
        
        # Road specifications
        self.main_road_width = 12.0  # meters
        self.secondary_road_width = 6.0  # meters
        self.main_road_lanes = 4
        self.secondary_road_lanes = 2
        
        # Facility specifications (WS-1.3)
        self.ambulance_stations = config.get("ambulance_stations", 3)
        self.shelters = config.get("shelters", 8)
        
    def generate_map(self, include_trees: bool = True, include_facilities: bool = True, include_buildings: bool = True) -> GeneratedMap:
        """
        Main method to generate a complete map with road network, trees, facilities, and buildings.
        
        Args:
            include_trees: Whether to generate trees (WS-1.2)
            include_facilities: Whether to generate facilities (WS-1.3)
            include_buildings: Whether to generate buildings (WS-1.5)
        
        Returns:
            GeneratedMap: Complete map data with boundaries, nodes, edges, trees, facilities, buildings, and graph
        """
        # Create map boundary
        boundary = MapBoundary(
            min_x=0.0,
            min_y=0.0, 
            max_x=float(self.map_size[0]),
            max_y=float(self.map_size[1])
        )
        
        # Initialize map container
        generated_map = GeneratedMap(boundary=boundary)
        
        # Generate road network
        self._generate_main_roads(generated_map)
        self._generate_secondary_roads(generated_map)
        self._create_intersection_nodes(generated_map)
        self._build_network_graph(generated_map)
        
        # Generate trees along roads (WS-1.2)
        if include_trees:
            self._generate_trees(generated_map)
        
        # Generate facilities on road nodes (WS-1.3)
        if include_facilities:
            self._generate_facilities(generated_map)
        
        # Generate buildings and population in non-road areas (WS-1.5)
        if include_buildings:
            self._generate_buildings(generated_map)
        
        return generated_map
    
    def _generate_main_roads(self, map_data: GeneratedMap) -> None:
        """
        Generate main roads (major arteries) that span the map.
        These are wider roads with higher speed limits.
        """
        boundary = map_data.boundary
        
        # Generate vertical main roads
        for i in range(self.main_road_count // 2):
            x = boundary.min_x + (i + 1) * boundary.width / (self.main_road_count // 2 + 1)
            
            # Create nodes at top and bottom
            top_node_id = str(uuid.uuid4())
            bottom_node_id = str(uuid.uuid4())
            
            top_node = MapNode(
                id=top_node_id,
                x=x,
                y=boundary.max_y - 50,  # Slight offset from edge
                node_type="intersection"
            )
            
            bottom_node = MapNode(
                id=bottom_node_id,
                x=x,
                y=boundary.min_y + 50,
                node_type="intersection"
            )
            
            map_data.nodes[top_node_id] = top_node
            map_data.nodes[bottom_node_id] = bottom_node
            
            # Create road edge
            edge_id = str(uuid.uuid4())
            road_edge = RoadEdge(
                id=edge_id,
                from_node=bottom_node_id,
                to_node=top_node_id,
                width=self.main_road_width,
                lanes=self.main_road_lanes,
                road_type="main",
                speed_limit=70.0
            )
            
            map_data.edges[edge_id] = road_edge
        
        # Generate horizontal main roads
        for i in range(self.main_road_count // 2):
            y = boundary.min_y + (i + 1) * boundary.height / (self.main_road_count // 2 + 1)
            
            # Create nodes at left and right
            left_node_id = str(uuid.uuid4())
            right_node_id = str(uuid.uuid4())
            
            left_node = MapNode(
                id=left_node_id,
                x=boundary.min_x + 50,
                y=y,
                node_type="intersection"
            )
            
            right_node = MapNode(
                id=right_node_id,
                x=boundary.max_x - 50,
                y=y,
                node_type="intersection"
            )
            
            map_data.nodes[left_node_id] = left_node
            map_data.nodes[right_node_id] = right_node
            
            # Create road edge
            edge_id = str(uuid.uuid4())
            road_edge = RoadEdge(
                id=edge_id,
                from_node=left_node_id,
                to_node=right_node_id,
                width=self.main_road_width,
                lanes=self.main_road_lanes,
                road_type="main",
                speed_limit=70.0
            )
            
            map_data.edges[edge_id] = road_edge
    
    def _generate_secondary_roads(self, map_data: GeneratedMap) -> None:
        """
        Generate secondary roads that connect to main roads and form a network.
        These create natural intersections and provide local connectivity.
        """
        boundary = map_data.boundary
        
        # Calculate grid for secondary roads
        grid_spacing = 200  # meters between secondary roads
        x_positions = np.arange(boundary.min_x + grid_spacing, 
                               boundary.max_x, 
                               grid_spacing)
        y_positions = np.arange(boundary.min_y + grid_spacing,
                               boundary.max_y,
                               grid_spacing)
        
        # Generate vertical secondary roads
        for x in x_positions:
            if random.random() < self.secondary_road_density:
                # Add some randomness to position
                x_actual = x + random.uniform(-50, 50)
                
                # Create nodes at intersections with horizontal roads
                nodes_on_road = []
                
                for y in y_positions:
                    if random.random() < 0.8:  # 80% chance of intersection
                        y_actual = y + random.uniform(-30, 30)
                        
                        node_id = str(uuid.uuid4())
                        node = MapNode(
                            id=node_id,
                            x=x_actual,
                            y=y_actual,
                            node_type="intersection"
                        )
                        
                        map_data.nodes[node_id] = node
                        nodes_on_road.append(node_id)
                
                # Connect consecutive nodes with road edges
                for i in range(len(nodes_on_road) - 1):
                    edge_id = str(uuid.uuid4())
                    # Some secondary roads are one-way (30% chance)
                    is_bidirectional = random.random() > 0.3
                    road_edge = RoadEdge(
                        id=edge_id,
                        from_node=nodes_on_road[i],
                        to_node=nodes_on_road[i + 1],
                        width=self.secondary_road_width,
                        lanes=self.secondary_road_lanes,
                        is_bidirectional=is_bidirectional,
                        road_type="secondary",
                        speed_limit=40.0
                    )
                    
                    map_data.edges[edge_id] = road_edge
        
        # Generate horizontal secondary roads
        for y in y_positions:
            if random.random() < self.secondary_road_density:
                y_actual = y + random.uniform(-50, 50)
                
                nodes_on_road = []
                
                for x in x_positions:
                    if random.random() < 0.8:
                        x_actual = x + random.uniform(-30, 30)
                        
                        # Check if we already have a node near this position
                        existing_node = self._find_nearby_node(
                            map_data, x_actual, y_actual, threshold=80.0
                        )
                        
                        if existing_node:
                            nodes_on_road.append(existing_node.id)
                        else:
                            node_id = str(uuid.uuid4())
                            node = MapNode(
                                id=node_id,
                                x=x_actual,
                                y=y_actual,
                                node_type="intersection"
                            )
                            
                            map_data.nodes[node_id] = node
                            nodes_on_road.append(node_id)
                
                # Connect consecutive nodes
                for i in range(len(nodes_on_road) - 1):
                    edge_id = str(uuid.uuid4())
                    # Some secondary roads are one-way (30% chance)
                    is_bidirectional = random.random() > 0.3
                    road_edge = RoadEdge(
                        id=edge_id,
                        from_node=nodes_on_road[i],
                        to_node=nodes_on_road[i + 1],
                        width=self.secondary_road_width,
                        lanes=self.secondary_road_lanes,
                        is_bidirectional=is_bidirectional,
                        road_type="secondary",
                        speed_limit=40.0
                    )
                    
                    map_data.edges[edge_id] = road_edge
    
    def _find_nearby_node(self, map_data: GeneratedMap, x: float, y: float, 
                          threshold: float = 50.0) -> MapNode:
        """Find existing node within threshold distance"""
        for node in map_data.nodes.values():
            distance = math.sqrt((node.x - x)**2 + (node.y - y)**2)
            if distance < threshold:
                return node
        return None
    
    def _build_network_graph(self, map_data: GeneratedMap) -> None:
        """
        Build NetworkX graph from nodes and edges for efficient path finding.
        """
        graph = nx.Graph()
        
        # Add nodes
        for node_id, node in map_data.nodes.items():
            graph.add_node(
                node_id,
                x=node.x,
                y=node.y,
                type=node.node_type
            )
        
        # Add edges with weights based on length and road type
        for edge_id, edge in map_data.edges.items():
            if edge.from_node in map_data.nodes and edge.to_node in map_data.nodes:
                from_node = map_data.nodes[edge.from_node]
                to_node = map_data.nodes[edge.to_node]
                
                # Calculate edge length
                length = math.sqrt(
                    (to_node.x - from_node.x)**2 + (to_node.y - from_node.y)**2
                )
                
                # Calculate travel time based on speed limit
                travel_time = (length / 1000) / (edge.speed_limit / 3600)  # seconds
                
                graph.add_edge(
                    edge.from_node,
                    edge.to_node,
                    edge_id=edge_id,
                    length=length,
                    width=edge.width,
                    lanes=edge.lanes,
                    road_type=edge.road_type,
                    speed_limit=edge.speed_limit,
                    travel_time=travel_time,
                    weight=travel_time  # Default weight for shortest path
                )
        
        map_data.graph = graph
    
    def _create_intersection_nodes(self, map_data: GeneratedMap) -> None:
        """
        Detect road intersections and create nodes at intersection points.
        This solves the problem where main roads and secondary roads cross
        but have no node at the intersection for turning.
        """
        # Get all road edges as LineString geometries
        road_lines = {}  # edge_id -> (LineString, edge_data)
        
        for edge_id, edge in map_data.edges.items():
            from_node = map_data.nodes[edge.from_node]
            to_node = map_data.nodes[edge.to_node]
            
            line = LineString([(from_node.x, from_node.y), (to_node.x, to_node.y)])
            road_lines[edge_id] = (line, edge)
        
        # Find all intersection points
        intersection_points = {}  # (x, y) -> list of edge_ids that intersect here
        processed_pairs = set()
        
        for edge_id1, (line1, edge1) in road_lines.items():
            for edge_id2, (line2, edge2) in road_lines.items():
                if edge_id1 >= edge_id2:  # Avoid duplicate comparisons
                    continue
                
                pair_key = (min(edge_id1, edge_id2), max(edge_id1, edge_id2))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # Skip if they share a node (already connected)
                if (edge1.from_node in [edge2.from_node, edge2.to_node] or 
                    edge1.to_node in [edge2.from_node, edge2.to_node]):
                    continue
                
                # Check for intersection
                if line1.intersects(line2):
                    intersection = line1.intersection(line2)
                    
                    # Only handle point intersections (not overlapping segments)
                    if intersection.geom_type == 'Point':
                        x, y = intersection.x, intersection.y
                        
                        # Round to avoid floating point precision issues
                        point_key = (round(x, 2), round(y, 2))
                        
                        if point_key not in intersection_points:
                            intersection_points[point_key] = []
                        
                        intersection_points[point_key].extend([edge_id1, edge_id2])
        
        # Create nodes at intersection points and split edges
        for (x, y), intersecting_edges in intersection_points.items():
            # Remove duplicates
            intersecting_edges = list(set(intersecting_edges))
            
            if len(intersecting_edges) < 2:
                continue
            
            # Create intersection node
            intersection_node_id = str(uuid.uuid4())
            intersection_node = MapNode(
                id=intersection_node_id,
                x=float(x),
                y=float(y),
                node_type="intersection"
            )
            
            map_data.nodes[intersection_node_id] = intersection_node
            
            # Split each intersecting edge at the intersection point
            edges_to_remove = []
            new_edges = []
            
            for edge_id in intersecting_edges:
                if edge_id not in map_data.edges:
                    continue  # Edge might have been processed already
                    
                original_edge = map_data.edges[edge_id]
                from_node = map_data.nodes[original_edge.from_node]
                to_node = map_data.nodes[original_edge.to_node]
                
                # Calculate distances to determine if intersection is actually on the edge
                from_dist = math.sqrt((x - from_node.x)**2 + (y - from_node.y)**2)
                to_dist = math.sqrt((x - to_node.x)**2 + (y - to_node.y)**2)
                total_dist = math.sqrt((to_node.x - from_node.x)**2 + (to_node.y - from_node.y)**2)
                
                # Only split if intersection is actually between the nodes (not at endpoints)
                tolerance = 5.0  # meters
                if (from_dist > tolerance and to_dist > tolerance and 
                    abs(from_dist + to_dist - total_dist) < tolerance):
                    
                    # Create two new edges: from_node -> intersection and intersection -> to_node
                    edge1_id = str(uuid.uuid4())
                    edge2_id = str(uuid.uuid4())
                    
                    edge1 = RoadEdge(
                        id=edge1_id,
                        from_node=original_edge.from_node,
                        to_node=intersection_node_id,
                        width=original_edge.width,
                        lanes=original_edge.lanes,
                        is_bidirectional=original_edge.is_bidirectional,
                        road_type=original_edge.road_type,
                        speed_limit=original_edge.speed_limit
                    )
                    
                    edge2 = RoadEdge(
                        id=edge2_id,
                        from_node=intersection_node_id,
                        to_node=original_edge.to_node,
                        width=original_edge.width,
                        lanes=original_edge.lanes,
                        is_bidirectional=original_edge.is_bidirectional,
                        road_type=original_edge.road_type,
                        speed_limit=original_edge.speed_limit
                    )
                    
                    new_edges.extend([edge1, edge2])
                    edges_to_remove.append(edge_id)
            
            # Apply edge modifications
            for edge_id in edges_to_remove:
                del map_data.edges[edge_id]
            
            for edge in new_edges:
                map_data.edges[edge.id] = edge
    
    def _generate_trees(self, map_data: GeneratedMap) -> None:
        """
        Generate trees along road edges using TreeGenerator (WS-1.2).
        """
        from .tree_generator import TreeGenerator
        
        # Create tree generator with configuration
        tree_generator = TreeGenerator(self.config)
        
        # Generate trees for all road edges
        trees = tree_generator.generate_trees_for_map(map_data)
        
        # Add trees to map data
        map_data.trees = trees
    
    def _generate_facilities(self, map_data: GeneratedMap) -> None:
        """
        Generate facilities on road network nodes (WS-1.3).
        """
        from .facility_generator import FacilityGenerator
        
        # Create facility generator with configuration
        facility_generator = FacilityGenerator(self.config)
        
        # Generate facilities for the map
        facilities = facility_generator.generate_facilities_for_map(map_data)
        
        # Add facilities to map data
        map_data.facilities = facilities
    
    def _generate_buildings(self, map_data: GeneratedMap) -> None:
        """
        Generate buildings and population in non-road areas (WS-1.5).
        """
        from .building_generator import BuildingGenerator
        
        # Create building generator with configuration
        building_generator = BuildingGenerator(self.config)
        
        # Generate buildings for the map
        buildings = building_generator.generate_buildings_for_map(map_data)
        
        # Add buildings to map data
        map_data.buildings = buildings