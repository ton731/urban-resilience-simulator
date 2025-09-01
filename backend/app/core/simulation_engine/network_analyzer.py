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
    DEFAULT_VEHICLE_CONFIGS,
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
        self, nodes_data: Dict[str, Any], edges_data: Dict[str, Any]
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
                x=node_data["x"],
                y=node_data["y"],
                type=node_data.get("type", "intersection"),
            )

        # Add edges to the graph
        for edge_id, edge_data in edges_data.items():
            from_node = edge_data["from_node"]
            to_node = edge_data["to_node"]

            # Calculate edge length (Euclidean distance)
            from_coords = (nodes_data[from_node]["x"], nodes_data[from_node]["y"])
            to_coords = (nodes_data[to_node]["x"], nodes_data[to_node]["y"])
            distance = self._calculate_distance(from_coords, to_coords)

            self.road_graph.add_edge(
                from_node,
                to_node,
                edge_id=edge_id,
                distance=distance,
                width=edge_data.get("width", 6.0),
                lanes=edge_data.get("lanes", 2),
                is_bidirectional=edge_data.get("is_bidirectional", True),
                road_type=edge_data.get("road_type", "secondary"),
                speed_limit=edge_data.get("speed_limit", 40.0),
                original_width=edge_data.get("width", 6.0),  # Store original width
            )

    def update_obstructions(self, obstructions: List[RoadObstruction]):
        """
        Update road obstructions and modify graph edge weights accordingly.

        Args:
            obstructions: List of RoadObstruction objects
        """
        print(f"\n🚧 更新道路阻塞信息 - 共 {len(obstructions)} 個阻塞點")
        print("=" * 80)
        
        # Clear previous obstructions
        self.road_obstructions = {}

        # Reset all edges to original width
        for u, v, data in self.road_graph.edges(data=True):
            data["width"] = data["original_width"]

        # Apply new obstructions
        for i, obstruction in enumerate(obstructions, 1):
            self.road_obstructions[obstruction.obstruction_id] = obstruction

            # Find the edge corresponding to this road
            edge = self._find_edge_by_id(obstruction.road_edge_id)
            if edge:
                u, v = edge
                original_width = self.road_graph[u][v]["original_width"]
                
                print(f"阻塞點 {i}:")
                print(f"  📍 道路 ID: {obstruction.road_edge_id}")
                print(f"  🌳 造成事件: {obstruction.caused_by_event}")
                print(f"  📏 原始寬度: {original_width:.1f}m")
                print(f"  📉 剩餘寬度: {obstruction.remaining_width:.1f}m") 
                print(f"  🚫 阻塞程度: {obstruction.blocked_percentage:.1f}%")
                print(f"  📊 寬度減少: {original_width - obstruction.remaining_width:.1f}m")
                print(f"  ⚠️  影響程度: {'嚴重' if obstruction.blocked_percentage > 70 else '中等' if obstruction.blocked_percentage > 30 else '輕微'}")
                print()
                
                # Update the effective width for this edge
                self.road_graph[u][v]["width"] = obstruction.remaining_width
            else:
                print(f"⚠️  警告: 找不到道路 ID {obstruction.road_edge_id} 對應的邊")
        
        print("=" * 80)

    def find_path(self, request: PathfindingRequest) -> PathfindingResult:
        """
        Find the optimal path between two points for a specific vehicle type.

        Implements A* pathfinding with obstruction awareness and vehicle constraints.

        Args:
            request: PathfindingRequest with start/end points and vehicle type

        Returns:
            PathfindingResult with path details or failure indication
        """
        print(f"\n🚗 開始路徑規劃")
        print(f"起點: ({request.start_point[0]:.1f}, {request.start_point[1]:.1f})")
        print(f"終點: ({request.end_point[0]:.1f}, {request.end_point[1]:.1f})")
        print(f"車輛類型: {request.vehicle_type.value}")
        
        if not self.road_graph:
            return PathfindingResult(
                success=False,
                path_coordinates=[],
                path_node_ids=[],
                total_distance=0.0,
                estimated_travel_time=0.0,
                vehicle_type=request.vehicle_type,
                blocked_roads=[],
            )

        # Try road-based pathfinding first
        start_node, end_node = self._prepare_pathfinding_nodes(
            request.start_point, request.end_point
        )

        # Get vehicle configuration
        vehicle_config = self.vehicle_configs.get(
            request.vehicle_type, DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )
        
        print(f"車輛配置:")
        print(f"  寬度: {vehicle_config.width:.1f}m")
        print(f"  長度: {vehicle_config.length:.1f}m") 
        print(f"  最高速度: {vehicle_config.max_speed:.1f} km/h")
        print(f"  最小道路寬度需求: {vehicle_config.minimum_road_width:.1f}m")
        print()

        # Perform A* pathfinding with vehicle constraints
        try:
            path_nodes = self._astar_pathfinding(
                start_node, end_node, vehicle_config, request.max_travel_time
            )

            if not path_nodes:
                # If complete path not found, try to find partial path
                partial_path_result = self._find_partial_path(
                    start_node, end_node, vehicle_config, request.max_travel_time
                )
                
                if partial_path_result["path_nodes"]:
                    # Convert partial path to coordinates and metrics
                    partial_coordinates = self._nodes_to_coordinates(partial_path_result["path_nodes"])
                    partial_distance = self._calculate_path_distance(partial_path_result["path_nodes"])
                    partial_time = self._estimate_travel_time(partial_path_result["path_nodes"], vehicle_config)
                    blocked_roads = self._identify_blocked_roads_in_path(partial_path_result["path_nodes"])
                    
                    # Add start point if not already exact
                    if partial_coordinates and partial_coordinates[0] != request.start_point:
                        start_distance = self._calculate_distance(request.start_point, partial_coordinates[0])
                        if start_distance > 1.0:
                            partial_coordinates.insert(0, request.start_point)
                        else:
                            partial_coordinates[0] = request.start_point
                    
                    # Clean up virtual nodes
                    virtual_nodes_to_cleanup = []
                    if self.road_graph.has_node(start_node) and self.road_graph.nodes[start_node].get("is_virtual", False):
                        virtual_nodes_to_cleanup.append(start_node)
                    if self.road_graph.has_node(end_node) and self.road_graph.nodes[end_node].get("is_virtual", False):
                        virtual_nodes_to_cleanup.append(end_node)
                    
                    result = PathfindingResult(
                        success=False,  # Still false since complete path not found
                        path_coordinates=partial_coordinates,
                        path_node_ids=partial_path_result["path_nodes"],
                        total_distance=partial_distance,
                        estimated_travel_time=partial_time,
                        vehicle_type=request.vehicle_type,
                        blocked_roads=blocked_roads,
                    )
                    
                    # Print partial path summary
                    print(f"\n⚠️  部分路徑規劃")
                    print(f"原因: {partial_path_result['reason']}")
                    print(f"可達距離: {partial_distance:.1f}m")
                    print(f"預計時間: {partial_time:.1f}秒 ({partial_time/60:.1f}分鐘)")
                    print(f"路徑節點: {len(partial_path_result['path_nodes'])}個")
                    if "distance_to_destination" in partial_path_result:
                        print(f"距離目標還有: {partial_path_result['distance_to_destination']:.1f}m")
                    if blocked_roads:
                        print(f"遇到阻塞道路: {len(blocked_roads)}條")
                        for road_id in blocked_roads:
                            print(f"  - {road_id}")
                    print("=" * 50)
                    
                    if virtual_nodes_to_cleanup:
                        self._cleanup_virtual_nodes(virtual_nodes_to_cleanup)
                    
                    return result
                else:
                    # No partial path found either
                    return PathfindingResult(
                        success=False,
                        path_coordinates=[],
                        path_node_ids=[],
                        total_distance=0.0,
                        estimated_travel_time=0.0,
                        vehicle_type=request.vehicle_type,
                        blocked_roads=[],
                    )

            # Convert path to coordinates and calculate metrics
            path_coordinates = self._nodes_to_coordinates(path_nodes)
            total_distance = self._calculate_path_distance(path_nodes)
            travel_time = self._estimate_travel_time(path_nodes, vehicle_config)
            blocked_roads = self._identify_blocked_roads_in_path(path_nodes)

            # Handle coordinates properly - ensure start and end points are correct
            if path_coordinates:
                # Always ensure the first coordinate matches the requested start point
                if path_coordinates[0] != request.start_point:
                    # Check if start point is reasonably close to first coordinate
                    first_coord = path_coordinates[0]
                    start_distance = self._calculate_distance(
                        request.start_point, first_coord
                    )
                    if start_distance > 1.0:  # If more than 1 meter difference
                        path_coordinates.insert(0, request.start_point)
                    else:
                        path_coordinates[0] = (
                            request.start_point
                        )  # Just replace if very close

                # Always ensure the last coordinate matches the requested end point
                if path_coordinates[-1] != request.end_point:
                    # Check if end point is reasonably close to last coordinate
                    last_coord = path_coordinates[-1]
                    end_distance = self._calculate_distance(
                        request.end_point, last_coord
                    )
                    if end_distance > 1.0:  # If more than 1 meter difference
                        path_coordinates.append(request.end_point)
                    else:
                        path_coordinates[-1] = (
                            request.end_point
                        )  # Just replace if very close

            # Clean up virtual nodes after successful pathfinding
            virtual_nodes_to_cleanup = []
            # Always try to cleanup start node if it's virtual
            if self.road_graph.has_node(start_node):
                start_node_data = self.road_graph.nodes[start_node]
                if start_node_data.get("is_virtual", False):
                    virtual_nodes_to_cleanup.append(start_node)

            # Always try to cleanup end node if it's virtual
            if self.road_graph.has_node(end_node):
                end_node_data = self.road_graph.nodes[end_node]
                if end_node_data.get("is_virtual", False):
                    virtual_nodes_to_cleanup.append(end_node)

            # Create result before cleanup
            result = PathfindingResult(
                success=True,
                path_coordinates=path_coordinates,
                path_node_ids=path_nodes,
                total_distance=total_distance,
                estimated_travel_time=travel_time,
                vehicle_type=request.vehicle_type,
                blocked_roads=blocked_roads,
            )
            
            # Print path summary
            print(f"\n🎉 路徑規劃成功!")
            print(f"總距離: {total_distance:.1f}m")
            print(f"預計時間: {travel_time:.1f}秒 ({travel_time/60:.1f}分鐘)")
            print(f"路徑節點: {len(path_nodes)}個")
            if blocked_roads:
                print(f"遇到阻塞道路: {len(blocked_roads)}條")
                for road_id in blocked_roads:
                    print(f"  - {road_id}")
            else:
                print("路徑暢通，無阻塞道路")
            print("=" * 50)

            # Clean up virtual nodes to restore original graph
            if virtual_nodes_to_cleanup:
                self._cleanup_virtual_nodes(virtual_nodes_to_cleanup)

            return result

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

        min_distance = float("inf")
        nearest_node = None

        for node_id, node_data in self.road_graph.nodes(data=True):
            node_point = (node_data["x"], node_data["y"])
            distance = self._calculate_distance(point, node_point)

            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id

        return nearest_node

    def _find_closest_road_point(
        self, point: Tuple[float, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the closest point on any road edge to a given point.
        This enables road-based pathfinding instead of node-to-node pathfinding.

        Args:
            point: Coordinates (x, y)

        Returns:
            Dictionary with closest road information or None if no roads available
            {
                'edge_id': str,
                'from_node': str,
                'to_node': str,
                'closest_point': Tuple[float, float],
                'distance_to_road': float,
                'position_on_edge': float  # 0.0 = at from_node, 1.0 = at to_node
            }
        """
        if not self.road_graph.edges():
            return None

        min_distance = float("inf")
        closest_road_info = None

        for from_node, to_node, edge_data in self.road_graph.edges(data=True):
            from_coords = (
                self.road_graph.nodes[from_node]["x"],
                self.road_graph.nodes[from_node]["y"],
            )
            to_coords = (
                self.road_graph.nodes[to_node]["x"],
                self.road_graph.nodes[to_node]["y"],
            )

            # Create line segment for this road edge
            road_line = LineString([from_coords, to_coords])

            # Find closest point on this road segment
            point_geom = Point(point)
            closest_point_on_road = road_line.interpolate(road_line.project(point_geom))

            distance = point_geom.distance(closest_point_on_road)

            if distance < min_distance:
                min_distance = distance

                # Calculate position along the edge (0.0 to 1.0)
                total_length = road_line.length
                if total_length > 0:
                    position_ratio = (
                        road_line.project(closest_point_on_road) / total_length
                    )
                else:
                    position_ratio = 0.0

                closest_road_info = {
                    "edge_id": edge_data.get("edge_id", f"{from_node}-{to_node}"),
                    "from_node": from_node,
                    "to_node": to_node,
                    "closest_point": (closest_point_on_road.x, closest_point_on_road.y),
                    "distance_to_road": distance,
                    "position_on_edge": position_ratio,
                    "edge_data": edge_data,
                }

        return closest_road_info

    def _create_virtual_node_on_road(
        self,
        point: Tuple[float, float],
        road_info: Dict[str, Any],
        node_id_prefix: str = "virtual",
    ) -> str:
        """
        Create a virtual node on a road edge at the closest point to the given point.
        This allows pathfinding to connect to roads at any point, not just existing nodes.

        Args:
            point: Original point coordinates
            road_info: Road information from _find_closest_road_point
            node_id_prefix: Prefix for the virtual node ID

        Returns:
            ID of the created virtual node
        """
        virtual_node_id = f"{node_id_prefix}_{uuid.uuid4()}"
        closest_point = road_info["closest_point"]

        # Add virtual node to the graph
        self.road_graph.add_node(
            virtual_node_id,
            x=closest_point[0],
            y=closest_point[1],
            type="virtual",
            original_point=point,
            is_virtual=True,
        )

        # Split the original edge and connect to virtual node
        from_node = road_info["from_node"]
        to_node = road_info["to_node"]
        edge_data = road_info["edge_data"]
        position_ratio = road_info["position_on_edge"]

        # Only split the edge if the virtual node is not too close to existing nodes
        tolerance = 10.0  # meters
        from_coords = (
            self.road_graph.nodes[from_node]["x"],
            self.road_graph.nodes[from_node]["y"],
        )
        to_coords = (
            self.road_graph.nodes[to_node]["x"],
            self.road_graph.nodes[to_node]["y"],
        )

        dist_to_from = self._calculate_distance(closest_point, from_coords)
        dist_to_to = self._calculate_distance(closest_point, to_coords)

        if dist_to_from < tolerance:
            # Virtual node is too close to from_node, just use from_node
            return from_node
        elif dist_to_to < tolerance:
            # Virtual node is too close to to_node, just use to_node
            return to_node
        else:
            # Split the edge: create edges from_node->virtual and virtual->to_node
            original_distance = edge_data["distance"]

            # Calculate distances for new edge segments
            distance_to_virtual = original_distance * position_ratio
            distance_from_virtual = original_distance * (1.0 - position_ratio)

            # Remove the original edge
            if self.road_graph.has_edge(from_node, to_node):
                self.road_graph.remove_edge(from_node, to_node)

            # Add new edges through virtual node
            self.road_graph.add_edge(
                from_node,
                virtual_node_id,
                edge_id=f"{edge_data.get('edge_id', '')}_part1",
                distance=distance_to_virtual,
                width=edge_data.get("width", 6.0),
                lanes=edge_data.get("lanes", 2),
                road_type=edge_data.get("road_type", "secondary"),
                speed_limit=edge_data.get("speed_limit", 40.0),
                travel_time=distance_to_virtual
                / 1000
                / (edge_data.get("speed_limit", 40.0) / 3600),
                weight=distance_to_virtual
                / 1000
                / (edge_data.get("speed_limit", 40.0) / 3600),
                original_width=edge_data.get(
                    "original_width", edge_data.get("width", 6.0)
                ),
            )

            self.road_graph.add_edge(
                virtual_node_id,
                to_node,
                edge_id=f"{edge_data.get('edge_id', '')}_part2",
                distance=distance_from_virtual,
                width=edge_data.get("width", 6.0),
                lanes=edge_data.get("lanes", 2),
                road_type=edge_data.get("road_type", "secondary"),
                speed_limit=edge_data.get("speed_limit", 40.0),
                travel_time=distance_from_virtual
                / 1000
                / (edge_data.get("speed_limit", 40.0) / 3600),
                weight=distance_from_virtual
                / 1000
                / (edge_data.get("speed_limit", 40.0) / 3600),
                original_width=edge_data.get(
                    "original_width", edge_data.get("width", 6.0)
                ),
            )

            # Add perpendicular connection from original point to virtual node
            perpendicular_distance = road_info["distance_to_road"]
            if perpendicular_distance > 0.1:  # Only add if there's meaningful distance
                access_node_id = f"access_{uuid.uuid4()}"

                # Add access node at original point
                self.road_graph.add_node(
                    access_node_id,
                    x=point[0],
                    y=point[1],
                    type="access",
                    is_virtual=True,
                )

                # Add access edge (straight line connection to road)
                # Use walking speed for access segments
                access_speed = 5.0  # km/h (walking speed)
                access_time = perpendicular_distance / 1000 / (access_speed / 3600)

                self.road_graph.add_edge(
                    access_node_id,
                    virtual_node_id,
                    edge_id=f"access_{uuid.uuid4()}",
                    distance=perpendicular_distance,
                    width=10.0,  # Wide enough for any vehicle
                    lanes=1,
                    road_type="access",
                    speed_limit=access_speed,
                    travel_time=access_time,
                    weight=access_time,
                    original_width=10.0,
                    is_access_road=True,
                )

                return access_node_id

            return virtual_node_id

    def _prepare_pathfinding_nodes(
        self, start_point: Tuple[float, float], end_point: Tuple[float, float]
    ) -> Tuple[str, str]:
        """
        Prepare start and end nodes for pathfinding with smart fallback strategies.

        For START: Try normal road connection, fallback to nearest node
        For END: Try normal road connection, if failed, FORCE connection to ensure path exists

        This ensures we ALWAYS find a path: start -> roads -> closest_road_node -> end

        Args:
            start_point: Starting coordinates
            end_point: Ending coordinates

        Returns:
            Tuple of (start_node_id, end_node_id)
        """
        # === START POINT HANDLING ===
        start_node = None

        # Try road-based connection for start point
        try:
            start_road_info = self._find_closest_road_point(start_point)

            if (
                start_road_info and start_road_info["distance_to_road"] <= 200.0
            ):  # Reasonable distance
                # If the start point is very close to an existing node, just use that node
                if start_road_info["distance_to_road"] < 10.0:
                    # Check if we're close to either endpoint of the edge
                    from_node_pos = (
                        self.road_graph.nodes[start_road_info["from_node"]]["x"],
                        self.road_graph.nodes[start_road_info["from_node"]]["y"],
                    )
                    to_node_pos = (
                        self.road_graph.nodes[start_road_info["to_node"]]["x"],
                        self.road_graph.nodes[start_road_info["to_node"]]["y"],
                    )

                    dist_to_from = self._calculate_distance(start_point, from_node_pos)
                    dist_to_to = self._calculate_distance(start_point, to_node_pos)

                    if dist_to_from < 15.0:
                        start_node = start_road_info["from_node"]
                    elif dist_to_to < 15.0:
                        start_node = start_road_info["to_node"]
                    else:
                        start_node = self._create_virtual_node_on_road(
                            start_point, start_road_info, "start"
                        )
                else:
                    start_node = self._create_virtual_node_on_road(
                        start_point, start_road_info, "start"
                    )
        except Exception as e:
            print(f"Road-based start node creation failed: {e}")
            start_node = None

        # Fallback to nearest node for start if road connection failed
        if not start_node:
            start_node = self._find_nearest_node(start_point)

        # === END POINT HANDLING ===
        end_node = None

        # Try road-based connection for end point first
        try:
            end_road_info = self._find_closest_road_point(end_point)

            if (
                end_road_info and end_road_info["distance_to_road"] <= 200.0
            ):  # Reasonable distance
                # If the end point is very close to an existing node, just use that node
                if end_road_info["distance_to_road"] < 10.0:
                    # Check if we're close to either endpoint of the edge
                    from_node_pos = (
                        self.road_graph.nodes[end_road_info["from_node"]]["x"],
                        self.road_graph.nodes[end_road_info["from_node"]]["y"],
                    )
                    to_node_pos = (
                        self.road_graph.nodes[end_road_info["to_node"]]["x"],
                        self.road_graph.nodes[end_road_info["to_node"]]["y"],
                    )

                    dist_to_from = self._calculate_distance(end_point, from_node_pos)
                    dist_to_to = self._calculate_distance(end_point, to_node_pos)

                    if dist_to_from < 15.0:
                        end_node = end_road_info["from_node"]
                    elif dist_to_to < 15.0:
                        end_node = end_road_info["to_node"]
                    else:
                        end_node = self._create_virtual_node_on_road(
                            end_point, end_road_info, "end"
                        )
                else:
                    end_node = self._create_virtual_node_on_road(
                        end_point, end_road_info, "end"
                    )
        except Exception as e:
            print(f"Road-based end node creation failed: {e}")
            end_node = None

        # If road-based connection failed for end point, FORCE connection
        # This ensures we can ALWAYS reach the destination
        if not end_node:
            end_node = self._create_forced_connection_to_end(end_point)

        return start_node, end_node

    def _create_forced_connection_to_end(self, end_point: Tuple[float, float]) -> str:
        """
        Create a forced connection to the end point by connecting it to the closest road node.
        This ensures we can ALWAYS reach the destination, no matter how far it is from roads.

        The strategy: find closest road node -> create direct connection (unlimited distance)

        Args:
            end_point: End point coordinates

        Returns:
            ID of the created end node
        """
        # Find the closest road node (not virtual nodes)
        closest_road_node = None
        min_distance = float("inf")

        for node_id, node_data in self.road_graph.nodes(data=True):
            # Skip virtual/temporary nodes - we want real road nodes
            if node_data.get("is_virtual", False):
                continue
            # Also skip other temporary nodes
            if node_data.get("type") in ["forced_access", "forced_standalone"]:
                continue

            node_coords = (node_data["x"], node_data["y"])
            distance = self._calculate_distance(end_point, node_coords)

            if distance < min_distance:
                min_distance = distance
                closest_road_node = node_id

        if not closest_road_node:
            # Emergency fallback: create standalone end node
            print(f"Warning: No road nodes found, creating standalone end node")
            end_node_id = f"end_standalone_{uuid.uuid4()}"
            self.road_graph.add_node(
                end_node_id,
                x=end_point[0],
                y=end_point[1],
                type="end_standalone",
                is_virtual=True,
            )
            return end_node_id

        # Create end node at the exact end point location
        end_node_id = f"end_forced_{uuid.uuid4()}"
        self.road_graph.add_node(
            end_node_id,
            x=end_point[0],
            y=end_point[1],
            type="end_forced",
            is_virtual=True,
            connected_from=closest_road_node,
            original_point=end_point,
        )

        # Create forced connection from closest road node to end point
        # Use walking speed for the final connection segment
        connection_speed = 5.0  # km/h (walking speed)
        connection_time = (
            min_distance / 1000 / (connection_speed / 3600) if min_distance > 0 else 0.1
        )

        self.road_graph.add_edge(
            closest_road_node,
            end_node_id,
            edge_id=f"to_end_{uuid.uuid4()}",
            distance=min_distance,
            width=10.0,  # Wide enough for any vehicle
            lanes=1,
            road_type="end_access",
            speed_limit=connection_speed,
            travel_time=connection_time,
            weight=connection_time,
            original_width=10.0,
            is_access_road=True,
            is_forced_end_connection=True,
        )

        return end_node_id

    def _create_forced_connection(
        self, point: Tuple[float, float], node_type: str = "forced"
    ) -> str:
        """
        Force create a connection to the road network by finding the closest road node
        and creating a direct connection, regardless of distance.

        This ensures we ALWAYS have a path, even if the point is very far from roads.

        Args:
            point: Coordinates to connect
            node_type: Type prefix for the node ID

        Returns:
            ID of the connected node
        """
        # Find the closest existing road node (not just any node)
        closest_road_node = None
        min_distance = float("inf")

        for node_id, node_data in self.road_graph.nodes(data=True):
            # Skip virtual nodes to avoid connecting to temporary nodes
            if node_data.get("is_virtual", False):
                continue

            node_coords = (node_data["x"], node_data["y"])
            distance = self._calculate_distance(point, node_coords)

            if distance < min_distance:
                min_distance = distance
                closest_road_node = node_id

        if not closest_road_node:
            # If somehow no road nodes exist, create a standalone node
            forced_node_id = f"{node_type}_standalone_{uuid.uuid4()}"
            self.road_graph.add_node(
                forced_node_id,
                x=point[0],
                y=point[1],
                type="forced_standalone",
                is_virtual=True,
            )
            return forced_node_id

        # Create access node at the original point
        access_node_id = f"{node_type}_forced_{uuid.uuid4()}"
        self.road_graph.add_node(
            access_node_id,
            x=point[0],
            y=point[1],
            type="forced_access",
            is_virtual=True,
            connected_to=closest_road_node,
        )

        # Create direct connection to closest road node, regardless of distance
        connection_distance = min_distance

        # Use slow speed for very long connections (walking speed)
        connection_speed = 5.0  # km/h (walking speed)
        connection_time = connection_distance / 1000 / (connection_speed / 3600)

        # Add bidirectional connection
        self.road_graph.add_edge(
            access_node_id,
            closest_road_node,
            edge_id=f"forced_access_{uuid.uuid4()}",
            distance=connection_distance,
            width=10.0,  # Wide enough for any vehicle
            lanes=1,
            road_type="access",
            speed_limit=connection_speed,
            travel_time=connection_time,
            weight=connection_time,
            original_width=10.0,
            is_access_road=True,
            is_forced_connection=True,
        )

        return access_node_id

    def _cleanup_virtual_nodes(self, virtual_nodes: List[str]) -> None:
        """
        Clean up virtual nodes and restore original graph structure.
        This prevents accumulation of temporary nodes in the graph.

        Args:
            virtual_nodes: List of virtual node IDs to remove
        """
        for node_id in virtual_nodes:
            if self.road_graph.has_node(node_id):
                node_data = self.road_graph.nodes[node_id]

                # If this is a virtual node that split an edge, restore the original edge
                if node_data.get("type") in ["virtual", "access"]:
                    neighbors = list(self.road_graph.neighbors(node_id))

                    # For virtual nodes that split roads, reconnect the original nodes
                    if len(neighbors) == 2 and node_data.get("type") == "virtual":
                        node1, node2 = neighbors

                        # Get edge data from one of the split edges
                        edge1_data = self.road_graph[node_id][node1]
                        edge2_data = self.road_graph[node_id][node2]

                        # Only restore if both edges are road segments (not access roads)
                        if not edge1_data.get(
                            "is_access_road", False
                        ) and not edge2_data.get("is_access_road", False):

                            # Remove split edges
                            self.road_graph.remove_edge(node_id, node1)
                            self.road_graph.remove_edge(node_id, node2)

                            # Restore original edge
                            combined_distance = (
                                edge1_data["distance"] + edge2_data["distance"]
                            )
                            combined_time = (
                                edge1_data["travel_time"] + edge2_data["travel_time"]
                            )

                            self.road_graph.add_edge(
                                node1,
                                node2,
                                edge_id=edge1_data.get("edge_id", "")
                                .replace("_part1", "")
                                .replace("_part2", ""),
                                distance=combined_distance,
                                width=edge1_data.get("width", 6.0),
                                lanes=edge1_data.get("lanes", 2),
                                road_type=edge1_data.get("road_type", "secondary"),
                                speed_limit=edge1_data.get("speed_limit", 40.0),
                                travel_time=combined_time,
                                weight=combined_time,
                                original_width=edge1_data.get(
                                    "original_width", edge1_data.get("width", 6.0)
                                ),
                            )

                    # Remove the virtual node
                    self.road_graph.remove_node(node_id)

    def _astar_pathfinding(
        self,
        start_node: str,
        end_node: str,
        vehicle_config: VehicleConfig,
        max_travel_time: Optional[float] = None,
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
            self.road_graph.nodes[end_node]["x"],
            self.road_graph.nodes[end_node]["y"],
        )

        iterations = 0
        while open_set:
            iterations += 1
            if iterations > 1000:  # Prevent infinite loops
                break
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

                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:

                    g_scores[neighbor] = tentative_g_score

                    # Calculate heuristic (Euclidean distance)
                    neighbor_coords = (
                        self.road_graph.nodes[neighbor]["x"],
                        self.road_graph.nodes[neighbor]["y"],
                    )
                    h_score = self._calculate_distance(neighbor_coords, end_coords)

                    f_score = tentative_g_score + h_score

                    new_path = path + [neighbor]
                    heapq.heappush(
                        open_set, (f_score, tentative_g_score, neighbor, new_path)
                    )

        return []

    def _can_vehicle_use_edge(
        self, vehicle_config: VehicleConfig, edge_data: Dict[str, Any]
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
        current_width = edge_data.get("width", 6.0)
        original_width = edge_data.get("original_width", current_width)
        min_required_width = vehicle_config.minimum_road_width
        road_type = edge_data.get("road_type", "secondary")
        edge_id = edge_data.get("edge_id", "unknown")

        # Show detailed road analysis
        width_reduction = original_width - current_width
        can_pass = current_width >= min_required_width
        
        if width_reduction > 0.1:  # Only show if there's meaningful obstruction
            status = "✅ 可通行" if can_pass else "❌ 不可通行"
            difficulty = ""
            if can_pass:
                if current_width < min_required_width * 1.2:
                    difficulty = " (緊迫)"
                elif current_width < min_required_width * 1.5:
                    difficulty = " (困難)"
                else:
                    difficulty = " (正常)"
            
            print(f"🛣️  道路檢查 {edge_id[:8]}...")
            print(f"  原始寬度: {original_width:.1f}m → 目前寬度: {current_width:.1f}m")
            print(f"  寬度減少: {width_reduction:.1f}m ({(width_reduction/original_width*100):.1f}%)")
            print(f"  需求寬度: {min_required_width:.1f}m")
            print(f"  通行狀態: {status}{difficulty}")

        # Basic width check
        if current_width < min_required_width:
            return False

        # Road type compatibility check
        if hasattr(vehicle_config, "prohibited_road_types"):
            if road_type in vehicle_config.prohibited_road_types:
                return False

        # Emergency vehicle special access (if implemented)
        if (
            hasattr(vehicle_config, "emergency_vehicle")
            and vehicle_config.emergency_vehicle
            and current_width >= min_required_width * 0.8
        ):  # 20% tolerance for emergency vehicles
            return True

        # Tight passage warning threshold (for future enhancements)
        if current_width < min_required_width * 1.1:
            # Vehicle can pass but with difficulty - add penalty in cost calculation
            pass

        return True

    def _calculate_edge_cost(
        self, from_node: str, to_node: str, vehicle_config: VehicleConfig
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

        distance = edge_data["distance"]
        speed_limit = edge_data.get("speed_limit", 40.0)  # km/h
        vehicle_max_speed = vehicle_config.max_speed
        current_width = edge_data.get("width", 6.0)
        original_width = edge_data.get("original_width", current_width)
        min_required_width = vehicle_config.minimum_road_width
        edge_id = edge_data.get("edge_id", "unknown")

        # SE-2.2: Check if vehicle can physically pass through
        if current_width < min_required_width:
            print(f"❌ 道路 {edge_id[:8]} 不可通行: 寬度 {current_width:.1f}m < 需求 {min_required_width:.1f}m")
            return float("inf")  # Impassable - infinite cost

        # Calculate base travel time using SE-2.2 formula: distance / speed
        effective_speed = min(speed_limit, vehicle_max_speed)

        # Convert km/h to m/s
        speed_ms = effective_speed * 1000 / 3600
        base_travel_time = distance / speed_ms

        # Apply penalties for narrow passages and obstructions
        width_ratio = current_width / original_width
        penalty_multiplier = 1.0

        if width_ratio < 0.5:
            # Severely obstructed - high time penalty
            penalty_multiplier = 3.0
            penalty_reason = "嚴重阻塞"
        elif width_ratio < 0.7:
            # Moderately obstructed - moderate penalty
            penalty_multiplier = 2.0
            penalty_reason = "中度阻塞"
        elif current_width < min_required_width * 1.2:
            # Tight fit - small penalty
            penalty_multiplier = 1.3
            penalty_reason = "通行困難"
        else:
            penalty_reason = "正常通行"

        final_travel_time = base_travel_time * penalty_multiplier
        
        # Show cost calculation details for obstructed roads
        if penalty_multiplier > 1.1 or width_ratio < 0.9:
            print(f"⏱️  道路成本計算 {edge_id[:8]}:")
            print(f"  距離: {distance:.0f}m, 速度: {effective_speed:.0f}km/h")
            print(f"  基礎時間: {base_travel_time:.1f}秒")
            print(f"  寬度比例: {width_ratio:.2f} ({original_width:.1f}m→{current_width:.1f}m)")
            print(f"  懲罰倍數: {penalty_multiplier:.1f}x ({penalty_reason})")
            print(f"  最終時間: {final_travel_time:.1f}秒")

        return final_travel_time

    def _calculate_distance(
        self, point1: Tuple[float, float], point2: Tuple[float, float]
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
            coordinates.append((node_data["x"], node_data["y"]))
        return coordinates

    def _calculate_path_distance(self, path_nodes: List[str]) -> float:
        """Calculate total distance of a path."""
        total_distance = 0.0

        for i in range(len(path_nodes) - 1):
            from_node = path_nodes[i]
            to_node = path_nodes[i + 1]
            edge_data = self.road_graph[from_node][to_node]
            total_distance += edge_data["distance"]

        return total_distance

    def _estimate_travel_time(
        self, path_nodes: List[str], vehicle_config: VehicleConfig
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
            edge_id = edge_data.get("edge_id")

            # Check if this edge has any obstructions
            for obstruction in self.road_obstructions.values():
                if obstruction.road_edge_id == edge_id:
                    blocked_roads.append(edge_id)
                    break

        return blocked_roads

    def _find_edge_by_id(self, edge_id: str) -> Optional[Tuple[str, str]]:
        """Find an edge in the graph by its ID."""
        for u, v, data in self.road_graph.edges(data=True):
            if data.get("edge_id") == edge_id:
                return (u, v)
        return None

    def calculate_service_area(
        self,
        center_point: Tuple[float, float],
        vehicle_type: VehicleType,
        max_travel_time: float,
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
            vehicle_type, DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
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
            reachable_points.append((node_data["x"], node_data["y"]))

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
                if travel_time == float("inf"):
                    continue

                total_time = cumulative_time + travel_time

                # Only process if within time limit and better than known distance
                if total_time <= max_travel_time and (
                    neighbor not in distances or total_time < distances[neighbor]
                ):
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

            if hasattr(convex_hull, "exterior"):
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
        time_intervals: List[float],
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
            vehicle_type, DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
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

                if travel_time == float("inf"):
                    continue

                total_time = cumulative_time + travel_time

                if total_time <= max_time and (
                    neighbor not in distances or total_time < distances[neighbor]
                ):
                    distances[neighbor] = total_time
                    heapq.heappush(queue, (total_time, neighbor))

        # Generate isochrones for each time interval
        isochrones = {}

        for time_limit in sorted_intervals:
            reachable_points = []

            for node_id, travel_time in node_times.items():
                if travel_time <= time_limit:
                    node_data = self.road_graph.nodes[node_id]
                    reachable_points.append((node_data["x"], node_data["y"]))

            # Generate boundary for this time interval
            if len(reachable_points) >= 3:
                try:
                    from shapely.geometry import MultiPoint

                    points = MultiPoint(reachable_points)
                    convex_hull = points.convex_hull

                    if hasattr(convex_hull, "exterior"):
                        isochrones[time_limit] = list(convex_hull.exterior.coords)
                    else:
                        isochrones[time_limit] = reachable_points
                except Exception:
                    isochrones[time_limit] = reachable_points
            else:
                isochrones[time_limit] = reachable_points

        return isochrones

    def analyze_road_network_connectivity(
        self, vehicle_type: VehicleType
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
            vehicle_type, DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
        )

        total_edges = 0
        passable_edges = 0
        blocked_edges = 0
        severely_obstructed_edges = 0

        total_road_length = 0.0
        passable_road_length = 0.0

        for u, v, edge_data in self.road_graph.edges(data=True):
            total_edges += 1
            distance = edge_data.get("distance", 0.0)
            total_road_length += distance

            current_width = edge_data.get("width", 6.0)
            original_width = edge_data.get("original_width", current_width)
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
            current_width = edge_data.get("width", 6.0)
            if current_width < vehicle_config.minimum_road_width:
                edges_to_remove.append((u, v))

        passable_graph.remove_edges_from(edges_to_remove)

        import networkx as nx

        connected_components = list(nx.connected_components(passable_graph))

        return {
            "vehicle_type": vehicle_type.value,
            "total_edges": total_edges,
            "passable_edges": passable_edges,
            "blocked_edges": blocked_edges,
            "severely_obstructed_edges": severely_obstructed_edges,
            "passability_percentage": (
                (passable_edges / total_edges * 100) if total_edges > 0 else 0
            ),
            "total_road_length_km": total_road_length / 1000,
            "passable_road_length_km": passable_road_length / 1000,
            "connected_components": len(connected_components),
            "largest_component_size": (
                max(len(comp) for comp in connected_components)
                if connected_components
                else 0
            ),
            "network_fragmentation": len(connected_components) > 1,
        }

    def find_alternative_paths(
        self,
        request: PathfindingRequest,
        max_alternatives: int = 3,
        diversity_factor: float = 1.5,
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
            request.vehicle_type, DEFAULT_VEHICLE_CONFIGS[VehicleType.CAR]
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
                base_cost = self._calculate_edge_cost(
                    from_node, to_node, vehicle_config
                )

                if base_cost == float("inf"):
                    return base_cost

                # Add penalty for previously used edges
                edge_key = (from_node, to_node)
                reverse_key = (to_node, from_node)
                usage = edge_usage_count.get(edge_key, 0) + edge_usage_count.get(
                    reverse_key, 0
                )

                if usage > 0:
                    penalty = base_cost * (diversity_factor - 1.0) * usage
                    return base_cost + penalty

                return base_cost

            # Find path with modified costs
            path_nodes = self._astar_pathfinding_with_custom_cost(
                start_node,
                end_node,
                vehicle_config,
                request.max_travel_time,
                get_modified_edge_cost,
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
                    blocked_roads=blocked_roads,
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
        cost_function,
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
            self.road_graph.nodes[end_node]["x"],
            self.road_graph.nodes[end_node]["y"],
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

                if move_cost == float("inf"):
                    continue

                tentative_g_score = g_score + move_cost

                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:

                    g_scores[neighbor] = tentative_g_score

                    neighbor_coords = (
                        self.road_graph.nodes[neighbor]["x"],
                        self.road_graph.nodes[neighbor]["y"],
                    )
                    h_score = self._calculate_distance(neighbor_coords, end_coords)

                    f_score = tentative_g_score + h_score
                    new_path = path + [neighbor]
                    heapq.heappush(
                        open_set, (f_score, tentative_g_score, neighbor, new_path)
                    )

        return []

    def _find_partial_path(
        self,
        start_node: str,
        end_node: str,
        vehicle_config: VehicleConfig,
        max_travel_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Find the farthest reachable point from start node when complete path is not possible.
        
        This method uses Dijkstra's algorithm to explore all reachable nodes from the start
        and returns the path to the node that is closest to the destination among all reachable nodes.
        
        Args:
            start_node: Starting node ID
            end_node: Destination node ID (used as target for direction)
            vehicle_config: Vehicle configuration for constraints
            max_travel_time: Maximum allowed travel time in seconds
            
        Returns:
            Dictionary with 'path_nodes' and 'reason' keys
        """
        import heapq
        
        if start_node == end_node:
            return {"path_nodes": [start_node], "reason": "start_is_destination"}
        
        # Get destination coordinates for distance calculation
        end_coords = (
            self.road_graph.nodes[end_node]["x"],
            self.road_graph.nodes[end_node]["y"],
        )
        
        # Dijkstra exploration from start node
        distances = {start_node: 0.0}
        previous = {start_node: None}
        visited = set()
        queue = [(0.0, start_node)]  # (cumulative_cost, node_id)
        
        # Track the closest node to destination found so far
        closest_to_destination = start_node
        min_distance_to_destination = float('inf')
        
        # Calculate initial distance to destination
        start_coords = (
            self.road_graph.nodes[start_node]["x"],
            self.road_graph.nodes[start_node]["y"],
        )
        initial_distance = self._calculate_distance(start_coords, end_coords)
        min_distance_to_destination = initial_distance
        
        max_iterations = 500  # Prevent infinite loops
        iterations = 0
        
        while queue and iterations < max_iterations:
            iterations += 1
            cumulative_cost, current_node = heapq.heappop(queue)
            
            if current_node in visited:
                continue
                
            visited.add(current_node)
            
            # Check if this node is closer to destination
            current_coords = (
                self.road_graph.nodes[current_node]["x"],
                self.road_graph.nodes[current_node]["y"],
            )
            distance_to_destination = self._calculate_distance(current_coords, end_coords)
            
            if distance_to_destination < min_distance_to_destination:
                min_distance_to_destination = distance_to_destination
                closest_to_destination = current_node
            
            # If we reached the destination somehow, return complete path
            if current_node == end_node:
                path = self._reconstruct_path(previous, end_node)
                return {"path_nodes": path, "reason": "complete_path_found"}
            
            # Explore neighbors
            for neighbor in self.road_graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                    
                edge_data = self.road_graph[current_node][neighbor]
                
                # Check if vehicle can use this edge
                if not self._can_vehicle_use_edge(vehicle_config, edge_data):
                    continue
                
                # Calculate cost to reach neighbor
                edge_cost = self._calculate_edge_cost(current_node, neighbor, vehicle_config)
                
                # Skip if edge is impassable
                if edge_cost == float("inf"):
                    continue
                
                tentative_cost = cumulative_cost + edge_cost
                
                # Check time constraint
                if max_travel_time and tentative_cost > max_travel_time:
                    continue
                
                # Update if we found a better path to this neighbor
                if neighbor not in distances or tentative_cost < distances[neighbor]:
                    distances[neighbor] = tentative_cost
                    previous[neighbor] = current_node
                    heapq.heappush(queue, (tentative_cost, neighbor))
        
        # Reconstruct path to closest reachable node
        if closest_to_destination != start_node:
            path = self._reconstruct_path(previous, closest_to_destination)
            return {
                "path_nodes": path, 
                "reason": f"partial_path_to_closest_reachable_point",
                "distance_to_destination": min_distance_to_destination
            }
        else:
            # Could not find any reachable nodes beyond start
            return {
                "path_nodes": [start_node], 
                "reason": "no_reachable_nodes",
                "distance_to_destination": initial_distance
            }
    
    def _reconstruct_path(self, previous: Dict[str, Optional[str]], end_node: str) -> List[str]:
        """
        Reconstruct path from previous node tracking.
        
        Args:
            previous: Dictionary mapping node_id -> previous_node_id
            end_node: Final node in the path
            
        Returns:
            List of node IDs forming the path from start to end
        """
        path = []
        current = end_node
        
        while current is not None:
            path.insert(0, current)
            current = previous.get(current)
            
        return path

    def _is_path_sufficiently_different(
        self,
        new_path: List[str],
        existing_paths: List[PathfindingResult],
        min_difference_ratio: float = 0.3,
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
