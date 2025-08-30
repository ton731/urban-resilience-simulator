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
    graph: nx.Graph = field(default_factory=nx.Graph)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary": self.boundary.to_dict(),
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()},
            "node_count": len(self.nodes),
            "edge_count": len(self.edges)
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
        
    def generate_map(self) -> GeneratedMap:
        """
        Main method to generate a complete map with road network.
        
        Returns:
            GeneratedMap: Complete map data with boundaries, nodes, edges, and graph
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
        self._build_network_graph(generated_map)
        
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
                    road_edge = RoadEdge(
                        id=edge_id,
                        from_node=nodes_on_road[i],
                        to_node=nodes_on_road[i + 1],
                        width=self.secondary_road_width,
                        lanes=self.secondary_road_lanes,
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
                    road_edge = RoadEdge(
                        id=edge_id,
                        from_node=nodes_on_road[i],
                        to_node=nodes_on_road[i + 1],
                        width=self.secondary_road_width,
                        lanes=self.secondary_road_lanes,
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