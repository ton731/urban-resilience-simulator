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
        return {"id": self.id, "x": self.x, "y": self.y, "type": self.node_type}


@dataclass
class LaneInfo:
    """Represents individual lane information within a road"""
    
    lane_id: int  # 0, 1, 2, etc.
    direction: str  # "forward", "backward" for bidirectional roads
    side: str  # "left", "right" for Taiwan right-hand traffic
    width: float  # individual lane width in meters
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "direction": self.direction,
            "side": self.side,
            "width": self.width,
        }


@dataclass
class RoadEdge:
    """Represents a road segment between two nodes"""

    id: str
    from_node: str
    to_node: str
    width: float  # total road width in meters
    lanes: int  # total number of lanes
    is_bidirectional: bool = True
    road_type: str = "secondary"  # "main", "secondary"
    speed_limit: float = 50.0  # km/h
    
    # New directional information
    primary_direction: str = "north"  # "north", "south", "east", "west" for single direction roads
    lane_info: List[LaneInfo] = field(default_factory=list)  # detailed lane information
    has_center_divider: bool = True  # whether bidirectional roads have a center line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "width": self.width,
            "lanes": self.lanes,
            "is_bidirectional": self.is_bidirectional,
            "road_type": self.road_type,
            "speed_limit": self.speed_limit,
            "primary_direction": self.primary_direction,
            "lane_info": [lane.to_dict() for lane in self.lane_info],
            "has_center_divider": self.has_center_divider,
        }
    
    def get_lanes_by_direction(self, direction: str) -> List[LaneInfo]:
        """Get all lanes going in a specific direction"""
        return [lane for lane in self.lane_info if lane.direction == direction]
    
    def get_remaining_width_by_direction(self, direction: str, blocked_width: float) -> float:
        """Calculate remaining width for a specific direction after blockage"""
        direction_lanes = self.get_lanes_by_direction(direction)
        total_direction_width = sum(lane.width for lane in direction_lanes)
        return max(0.0, total_direction_width - blocked_width)


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
            "height": self.height,
        }


@dataclass
class GeneratedMap:
    """Container for all generated map data"""

    boundary: MapBoundary
    nodes: Dict[str, MapNode] = field(default_factory=dict)
    edges: Dict[str, RoadEdge] = field(default_factory=dict)
    trees: Dict[str, Any] = field(default_factory=dict)  # Will contain Tree objects
    facilities: Dict[str, Any] = field(
        default_factory=dict
    )  # Will contain Facility objects
    buildings: Dict[str, Any] = field(
        default_factory=dict
    )  # Will contain Building objects
    graph: nx.Graph = field(default_factory=nx.Graph)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary": self.boundary.to_dict(),
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()},
            "trees": {tree_id: tree.to_dict() for tree_id, tree in self.trees.items()},
            "facilities": {
                facility_id: facility.to_dict()
                for facility_id, facility in self.facilities.items()
            },
            "buildings": {
                building_id: building.to_dict()
                for building_id, building in self.buildings.items()
            },
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "tree_count": len(self.trees),
            "facility_count": len(self.facilities),
            "building_count": len(self.buildings),
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

    def _create_lane_info(self, 
                         total_lanes: int, 
                         is_bidirectional: bool, 
                         total_width: float,
                         road_direction: str = "north") -> List[LaneInfo]:
        """
        Create detailed lane information for a road segment.
        
        Args:
            total_lanes: Total number of lanes
            is_bidirectional: Whether the road is bidirectional
            total_width: Total road width in meters
            road_direction: Primary direction for unidirectional roads
            
        Returns:
            List of LaneInfo objects with detailed lane configuration
        """
        lane_info = []
        
        if is_bidirectional:
            # For bidirectional roads, split lanes evenly
            lanes_per_direction = total_lanes // 2
            lane_width = total_width / total_lanes
            
            # Create forward direction lanes (right side in Taiwan)
            for i in range(lanes_per_direction):
                lane_info.append(LaneInfo(
                    lane_id=i,
                    direction="forward",
                    side="right",
                    width=lane_width
                ))
            
            # Create backward direction lanes (left side in Taiwan)  
            for i in range(lanes_per_direction):
                lane_info.append(LaneInfo(
                    lane_id=i + lanes_per_direction,
                    direction="backward", 
                    side="left",
                    width=lane_width
                ))
        else:
            # For unidirectional roads, all lanes go in the same direction
            lane_width = total_width / total_lanes
            side = "right"  # Default to right side
            
            for i in range(total_lanes):
                lane_info.append(LaneInfo(
                    lane_id=i,
                    direction="forward",
                    side=side,
                    width=lane_width
                ))
                
        return lane_info
    
    def _determine_road_direction(self, from_x: float, from_y: float, to_x: float, to_y: float) -> str:
        """
        Determine the primary direction of a road based on from/to coordinates.
        
        Returns: "north", "south", "east", "west"
        """
        dx = to_x - from_x
        dy = to_y - from_y
        
        if abs(dx) > abs(dy):
            return "east" if dx > 0 else "west"
        else:
            return "north" if dy > 0 else "south"

    def generate_map(
        self,
        include_trees: bool = True,
        include_facilities: bool = True,
        include_buildings: bool = True,
    ) -> GeneratedMap:
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
            max_y=float(self.map_size[1]),
        )

        # Initialize map container
        generated_map = GeneratedMap(boundary=boundary)

        # Generate road network
        self._generate_main_roads(generated_map)

        self._generate_secondary_roads(generated_map)

        # Generate 1-2 diagonal main roads (after basic road network is complete)
        self._generate_diagonal_main_roads(generated_map)

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
            x = boundary.min_x + (i + 1) * boundary.width / (
                self.main_road_count // 2 + 1
            )

            # Create nodes at top and bottom
            top_node_id = str(uuid.uuid4())
            bottom_node_id = str(uuid.uuid4())

            top_node = MapNode(
                id=top_node_id,
                x=x,
                y=boundary.max_y - 50,  # Slight offset from edge
                node_type="intersection",
            )

            bottom_node = MapNode(
                id=bottom_node_id, x=x, y=boundary.min_y + 50, node_type="intersection"
            )

            map_data.nodes[top_node_id] = top_node
            map_data.nodes[bottom_node_id] = bottom_node

            # Determine road direction and create lane info
            road_direction = self._determine_road_direction(
                bottom_node.x, bottom_node.y, top_node.x, top_node.y
            )
            lane_info = self._create_lane_info(
                self.main_road_lanes, True, self.main_road_width, road_direction
            )
            
            # Create road edge with directional information
            edge_id = str(uuid.uuid4())
            road_edge = RoadEdge(
                id=edge_id,
                from_node=bottom_node_id,
                to_node=top_node_id,
                width=self.main_road_width,
                lanes=self.main_road_lanes,
                is_bidirectional=True,
                road_type="main",
                speed_limit=70.0,
                primary_direction=road_direction,
                lane_info=lane_info,
                has_center_divider=True,
            )

            map_data.edges[edge_id] = road_edge

        # Generate horizontal main roads
        for i in range(self.main_road_count // 2):
            y = boundary.min_y + (i + 1) * boundary.height / (
                self.main_road_count // 2 + 1
            )

            # Create nodes at left and right
            left_node_id = str(uuid.uuid4())
            right_node_id = str(uuid.uuid4())

            left_node = MapNode(
                id=left_node_id, x=boundary.min_x + 50, y=y, node_type="intersection"
            )

            right_node = MapNode(
                id=right_node_id, x=boundary.max_x - 50, y=y, node_type="intersection"
            )

            map_data.nodes[left_node_id] = left_node
            map_data.nodes[right_node_id] = right_node

            # Determine road direction and create lane info
            road_direction = self._determine_road_direction(
                left_node.x, left_node.y, right_node.x, right_node.y
            )
            lane_info = self._create_lane_info(
                self.main_road_lanes, True, self.main_road_width, road_direction
            )
            
            # Create road edge with directional information
            edge_id = str(uuid.uuid4())
            road_edge = RoadEdge(
                id=edge_id,
                from_node=left_node_id,
                to_node=right_node_id,
                width=self.main_road_width,
                lanes=self.main_road_lanes,
                is_bidirectional=True,
                road_type="main",
                speed_limit=70.0,
                primary_direction=road_direction,
                lane_info=lane_info,
                has_center_divider=True,
            )

            map_data.edges[edge_id] = road_edge
    
    def _generate_diagonal_main_roads(self, map_data: GeneratedMap) -> None:
        """
        Generate 1-2 diagonal main roads across the map.
        Angles are between 20-45 degrees to avoid being too close to horizontal/vertical.
        """
        boundary = map_data.boundary
        
        # Generate 1-2 diagonal roads
        num_diagonal_roads = random.randint(1, 2)
        
        for _ in range(num_diagonal_roads):
            # Random angle between 20-45 degrees (choose from 4 quadrants)
            base_angles = [30, 150, 210, 330]  # 30°, 150°, 210°, 330°
            angle_degrees = random.choice(base_angles) + random.uniform(-10, 10)  # ±10° variation
            angle_radians = math.radians(angle_degrees)
            
            # Calculate direction vector
            dx = math.cos(angle_radians)
            dy = math.sin(angle_radians)
            
            # Start from one corner of the map and extend across
            if angle_degrees < 90 or angle_degrees > 270:  # Going right
                start_x = boundary.min_x
                start_y = boundary.min_y + random.uniform(0.3, 0.7) * boundary.height
            else:  # Going left
                start_x = boundary.max_x
                start_y = boundary.min_y + random.uniform(0.3, 0.7) * boundary.height
            
            # Calculate road length that crosses the map
            if abs(dx) > abs(dy):  # More horizontal
                road_length = boundary.width / abs(dx)
            else:  # More vertical
                road_length = boundary.height / abs(dy)
            
            # Extend slightly beyond map boundaries
            road_length *= 1.2
            
            end_x = start_x + dx * road_length
            end_y = start_y + dy * road_length
            
            # Create start and end nodes
            start_node_id = str(uuid.uuid4())
            end_node_id = str(uuid.uuid4())
            
            start_node = MapNode(
                id=start_node_id,
                x=start_x,
                y=start_y,
                node_type="intersection"
            )
            
            end_node = MapNode(
                id=end_node_id,
                x=end_x,
                y=end_y,
                node_type="intersection"
            )
            
            map_data.nodes[start_node_id] = start_node
            map_data.nodes[end_node_id] = end_node
            
            # Create road edge
            edge_id = str(uuid.uuid4())
            road_edge = RoadEdge(
                id=edge_id,
                from_node=start_node_id,
                to_node=end_node_id,
                width=self.main_road_width,
                lanes=self.main_road_lanes,
                road_type="main",
                speed_limit=70.0,
            )
            
            map_data.edges[edge_id] = road_edge

    def _generate_secondary_roads(self, map_data: GeneratedMap) -> None:
        """
        Generate secondary roads (alleys) within blocks formed by main roads.
        50% of alleys are partial length (extending from main roads into blocks).
        50% of alleys are full length (spanning across entire blocks).
        Each alley maintains consistent directionality (all bidirectional or all unidirectional).
        """
        boundary = map_data.boundary
        
        # Find only straight main roads (exclude diagonal ones for block calculation)
        straight_main_road_x_positions = []
        straight_main_road_y_positions = []
        
        for edge in map_data.edges.values():
            if edge.road_type == "main":
                from_node = map_data.nodes[edge.from_node]
                to_node = map_data.nodes[edge.to_node]
                
                # Check if this is a straight vertical road
                if abs(from_node.x - to_node.x) < 50:  # Almost vertical
                    x_pos = (from_node.x + to_node.x) / 2
                    if x_pos not in straight_main_road_x_positions:
                        straight_main_road_x_positions.append(x_pos)
                
                # Check if this is a straight horizontal road
                if abs(from_node.y - to_node.y) < 50:  # Almost horizontal
                    y_pos = (from_node.y + to_node.y) / 2
                    if y_pos not in straight_main_road_y_positions:
                        straight_main_road_y_positions.append(y_pos)
        
        straight_main_road_x_positions.sort()
        straight_main_road_y_positions.sort()
        
        # Generate alleys within blocks formed by straight main roads only
        self._generate_alleys_in_blocks(map_data, straight_main_road_x_positions, straight_main_road_y_positions)

    def _generate_alleys_in_blocks(self, map_data: GeneratedMap, x_positions: List[float], y_positions: List[float]) -> None:
        """
        Generate alleys within blocks defined by main road positions.
        """
        # For each block (rectangle between adjacent main roads)
        for i in range(len(x_positions) - 1):
            for j in range(len(y_positions) - 1):
                block_left = x_positions[i]
                block_right = x_positions[i + 1]
                block_bottom = y_positions[j]
                block_top = y_positions[j + 1]
                
                block_width = block_right - block_left
                block_height = block_top - block_bottom
                
                # Generate random number of alleys in this block (1-4 alleys per block)
                num_alleys = random.randint(1, 4)
                
                for _ in range(num_alleys):
                    # 50% chance for full-length alley, 50% for partial
                    is_full_length = random.random() < 0.5
                    
                    # 50% chance for horizontal alley, 50% for vertical
                    is_horizontal = random.random() < 0.5
                    
                    if is_horizontal:
                        self._create_horizontal_alley(map_data, block_left, block_right, 
                                                    block_bottom, block_top, is_full_length)
                    else:
                        self._create_vertical_alley(map_data, block_left, block_right, 
                                                  block_bottom, block_top, is_full_length)
    
    def _create_horizontal_alley(self, map_data: GeneratedMap, block_left: float, block_right: float, 
                               block_bottom: float, block_top: float, is_full_length: bool) -> None:
        """Create a horizontal alley within a block."""
        # Random Y position within the block
        alley_y = block_bottom + random.uniform(0.2, 0.8) * (block_top - block_bottom)
        
        # Decide directionality for this entire alley (consistent throughout)
        is_bidirectional = random.random() > 0.3  # 70% chance bidirectional
        
        # Start with straight horizontal alley
        if is_full_length:
            # Full-length alley: spans from left to right boundary
            start_x, end_x = block_left, block_right
            start_y = end_y = alley_y
        else:
            # Partial-length alley: extends from one side into the block
            if random.random() < 0.5:
                # Extend from left boundary
                start_x = block_left
                end_x = block_left + random.uniform(0.3, 0.8) * (block_right - block_left)
            else:
                # Extend from right boundary
                end_x = block_right
                start_x = block_right - random.uniform(0.3, 0.8) * (block_right - block_left)
            
            start_y = end_y = alley_y
        
        # 30% chance to add slight tilt (up to 20 degrees) - only for partial alleys
        if random.random() < 0.3 and not is_full_length:  # 30% chance for tilt
            max_tilt_angle = math.radians(20)  # 20 degrees maximum
            tilt_angle = random.uniform(-max_tilt_angle, max_tilt_angle)
            
            # Calculate Y offset based on X distance and tilt angle
            x_distance = end_x - start_x
            y_offset = x_distance * math.tan(tilt_angle)
            
            # Ensure tilted alley stays within block boundaries
            if alley_y + y_offset > block_top - 10:
                y_offset = block_top - alley_y - 10  # Small buffer
            elif alley_y + y_offset < block_bottom + 10:
                y_offset = block_bottom - alley_y + 10  # Small buffer
            
            end_y = alley_y + y_offset
        
        # Check if road would have zero length (avoid NaN in frontend)
        road_length = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
        if road_length < 5:  # Minimum 5 meters
            return  # Skip this alley
        
        # Create nodes at block boundaries for better connectivity
        start_node_id = str(uuid.uuid4())
        end_node_id = str(uuid.uuid4())
        
        start_node = MapNode(id=start_node_id, x=start_x, y=start_y, node_type="intersection")
        end_node = MapNode(id=end_node_id, x=end_x, y=end_y, node_type="intersection")
        
        map_data.nodes[start_node_id] = start_node
        map_data.nodes[end_node_id] = end_node
        
        # Determine road direction and create lane info for horizontal alley
        road_direction = self._determine_road_direction(start_x, start_y, end_x, end_y)
        lane_info = self._create_lane_info(
            self.secondary_road_lanes, is_bidirectional, self.secondary_road_width, road_direction
        )
        
        # Create the road edge with directional information
        edge_id = str(uuid.uuid4())
        road_edge = RoadEdge(
            id=edge_id,
            from_node=start_node_id,
            to_node=end_node_id,
            width=self.secondary_road_width,
            lanes=self.secondary_road_lanes,
            is_bidirectional=is_bidirectional,
            road_type="secondary",
            speed_limit=30.0,
            primary_direction=road_direction,
            lane_info=lane_info,
            has_center_divider=is_bidirectional,  # Only bidirectional roads have center dividers
        )
        
        map_data.edges[edge_id] = road_edge
    
    def _create_vertical_alley(self, map_data: GeneratedMap, block_left: float, block_right: float, 
                             block_bottom: float, block_top: float, is_full_length: bool) -> None:
        """Create a vertical alley within a block."""
        # Random X position within the block
        alley_x = block_left + random.uniform(0.2, 0.8) * (block_right - block_left)
        
        # Decide directionality for this entire alley (consistent throughout)
        is_bidirectional = random.random() > 0.3  # 70% chance bidirectional
        
        # Start with straight vertical alley
        if is_full_length:
            # Full-length alley: spans from bottom to top boundary
            start_x = end_x = alley_x
            start_y, end_y = block_bottom, block_top
        else:
            # Partial-length alley: extends from one side into the block
            if random.random() < 0.5:
                # Extend from bottom boundary
                start_y = block_bottom
                end_y = block_bottom + random.uniform(0.3, 0.8) * (block_top - block_bottom)
            else:
                # Extend from top boundary
                end_y = block_top
                start_y = block_top - random.uniform(0.3, 0.8) * (block_top - block_bottom)
            
            start_x = end_x = alley_x
        
        # 30% chance to add slight tilt (up to 20 degrees) - only for partial alleys
        if random.random() < 0.3 and not is_full_length:  # 30% chance for tilt
            max_tilt_angle = math.radians(20)  # 20 degrees maximum
            tilt_angle = random.uniform(-max_tilt_angle, max_tilt_angle)
            
            # Calculate X offset based on Y distance and tilt angle
            y_distance = end_y - start_y
            x_offset = y_distance * math.tan(tilt_angle)
            
            # Ensure tilted alley stays within block boundaries
            if alley_x + x_offset > block_right - 10:
                x_offset = block_right - alley_x - 10  # Small buffer
            elif alley_x + x_offset < block_left + 10:
                x_offset = block_left - alley_x + 10  # Small buffer
            
            end_x = alley_x + x_offset
        
        # Check if road would have zero length (avoid NaN in frontend)
        road_length = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
        if road_length < 5:  # Minimum 5 meters
            return  # Skip this alley
        
        # Create nodes at block boundaries for better connectivity
        start_node_id = str(uuid.uuid4())
        end_node_id = str(uuid.uuid4())
        
        start_node = MapNode(id=start_node_id, x=start_x, y=start_y, node_type="intersection")
        end_node = MapNode(id=end_node_id, x=end_x, y=end_y, node_type="intersection")
        
        map_data.nodes[start_node_id] = start_node
        map_data.nodes[end_node_id] = end_node
        
        # Determine road direction and create lane info for vertical alley
        road_direction = self._determine_road_direction(start_x, start_y, end_x, end_y)
        lane_info = self._create_lane_info(
            self.secondary_road_lanes, is_bidirectional, self.secondary_road_width, road_direction
        )
        
        # Create the road edge with directional information
        edge_id = str(uuid.uuid4())
        road_edge = RoadEdge(
            id=edge_id,
            from_node=start_node_id,
            to_node=end_node_id,
            width=self.secondary_road_width,
            lanes=self.secondary_road_lanes,
            is_bidirectional=is_bidirectional,
            road_type="secondary",
            speed_limit=30.0,
            primary_direction=road_direction,
            lane_info=lane_info,
            has_center_divider=is_bidirectional,  # Only bidirectional roads have center dividers
        )
        
        map_data.edges[edge_id] = road_edge
    
    def _find_closest_main_road_node(self, map_data: GeneratedMap, x: float, y: float) -> MapNode:
        """Find the closest node that belongs to a main road."""
        closest_node = None
        min_distance = float('inf')
        
        for node in map_data.nodes.values():
            # Check if this node is connected to any main road
            is_main_road_node = False
            for edge in map_data.edges.values():
                if (edge.road_type == "main" and 
                    (edge.from_node == node.id or edge.to_node == node.id)):
                    is_main_road_node = True
                    break
            
            if is_main_road_node:
                distance = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_node = node
        
        return closest_node

    def _find_nearby_node(
        self, map_data: GeneratedMap, x: float, y: float, threshold: float = 50.0
    ) -> MapNode:
        """Find existing node within threshold distance"""
        for node in map_data.nodes.values():
            distance = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)
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
            graph.add_node(node_id, x=node.x, y=node.y, type=node.node_type)

        # Add edges with weights based on length and road type
        for edge_id, edge in map_data.edges.items():
            if edge.from_node in map_data.nodes and edge.to_node in map_data.nodes:
                from_node = map_data.nodes[edge.from_node]
                to_node = map_data.nodes[edge.to_node]

                # Calculate edge length
                length = math.sqrt(
                    (to_node.x - from_node.x) ** 2 + (to_node.y - from_node.y) ** 2
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
                    weight=travel_time,  # Default weight for shortest path
                )

        map_data.graph = graph

    def _create_intersection_nodes(self, map_data: GeneratedMap) -> None:
        """
        Detect road intersections and create nodes at intersection points.
        This uses a completely rewritten approach that ensures proper connectivity.
        """

        # Store original edges before any modifications
        original_edges = dict(map_data.edges)

        # Get all road edges as LineString geometries
        road_lines = {}  # edge_id -> (LineString, edge_data)

        for edge_id, edge in original_edges.items():
            from_node = map_data.nodes[edge.from_node]
            to_node = map_data.nodes[edge.to_node]

            line = LineString([(from_node.x, from_node.y), (to_node.x, to_node.y)])
            road_lines[edge_id] = (line, edge)

        # Find all intersection points
        intersection_points = {}  # (x, y) -> list of edge_ids that intersect here
        edge_intersections = (
            {}
        )  # edge_id -> list of (x, y) intersection points on this edge

        for edge_id1, (line1, edge1) in road_lines.items():
            edge_intersections[edge_id1] = []

            for edge_id2, (line2, edge2) in road_lines.items():
                if edge_id1 >= edge_id2:  # Avoid duplicate comparisons
                    continue

                # Skip if they share a node (already connected)
                if edge1.from_node in [
                    edge2.from_node,
                    edge2.to_node,
                ] or edge1.to_node in [edge2.from_node, edge2.to_node]:
                    continue

                # Check for intersection
                if line1.intersects(line2):
                    intersection = line1.intersection(line2)

                    # Only handle point intersections (not overlapping segments)
                    if intersection.geom_type == "Point":
                        x, y = intersection.x, intersection.y

                        # Round to avoid floating point precision issues
                        point_key = (round(x, 2), round(y, 2))

                        # Store intersection for both edges
                        edge_intersections[edge_id1].append(point_key)
                        if edge_id2 not in edge_intersections:
                            edge_intersections[edge_id2] = []
                        edge_intersections[edge_id2].append(point_key)

                        if point_key not in intersection_points:
                            intersection_points[point_key] = []

                        intersection_points[point_key].extend([edge_id1, edge_id2])

        # Create intersection nodes first
        intersection_nodes = {}  # (x, y) -> node_id
        for x, y in intersection_points.keys():
            intersection_node_id = str(uuid.uuid4())
            intersection_node = MapNode(
                id=intersection_node_id,
                x=float(x),
                y=float(y),
                node_type="intersection",
            )
            map_data.nodes[intersection_node_id] = intersection_node
            intersection_nodes[(x, y)] = intersection_node_id

        # Now process each edge that has intersections
        for edge_id, intersections in edge_intersections.items():
            if not intersections or edge_id not in original_edges:
                continue

            original_edge = original_edges[edge_id]
            from_node = map_data.nodes[original_edge.from_node]
            to_node = map_data.nodes[original_edge.to_node]

            # Sort intersections by distance along the edge
            edge_line = LineString([(from_node.x, from_node.y), (to_node.x, to_node.y)])
            intersections_with_distance = []

            for x, y in intersections:
                point_on_line = Point(x, y)
                distance = edge_line.project(point_on_line)
                intersections_with_distance.append((distance, (x, y)))

            intersections_with_distance.sort()  # Sort by distance along edge

            # Create segments: from_node -> intersection1 -> intersection2 -> ... -> to_node
            segments = []
            current_from = original_edge.from_node

            for distance, (x, y) in intersections_with_distance:
                intersection_node_id = intersection_nodes[(x, y)]
                segments.append((current_from, intersection_node_id))
                current_from = intersection_node_id

            # Final segment to end node
            segments.append((current_from, original_edge.to_node))

            # Remove original edge
            if edge_id in map_data.edges:
                del map_data.edges[edge_id]

            # Create new edges for each segment
            for i, (segment_from, segment_to) in enumerate(segments):
                # Skip zero-length segments
                if segment_from == segment_to:
                    continue
                    
                # Check if nodes have same coordinates
                from_node_obj = map_data.nodes[segment_from]
                to_node_obj = map_data.nodes[segment_to]
                segment_length = math.sqrt(
                    (to_node_obj.x - from_node_obj.x) ** 2 + 
                    (to_node_obj.y - from_node_obj.y) ** 2
                )
                
                if segment_length < 5:  # Skip very short segments
                    continue
                
                new_edge_id = str(uuid.uuid4())
                new_edge = RoadEdge(
                    id=new_edge_id,
                    from_node=segment_from,
                    to_node=segment_to,
                    width=original_edge.width,
                    lanes=original_edge.lanes,
                    is_bidirectional=original_edge.is_bidirectional,
                    road_type=original_edge.road_type,
                    speed_limit=original_edge.speed_limit,
                )

                map_data.edges[new_edge_id] = new_edge

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
