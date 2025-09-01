"""
Disaster Simulator Implementation (SE-2.1)
Handles tree collapse simulation based on vulnerability levels and disaster intensity.
"""

import math
import random
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import transform
import numpy as np

from .models import (
    DisasterSimulationConfig,
    DisasterSimulationResult,
    TreeCollapseEvent,
    RoadObstruction,
    VulnerabilityLevel,
)


class DisasterSimulator:
    """
    Implements SE-2.1: Disaster Simulation

    This class handles the core disaster simulation logic, specifically tree collapse
    events based on vulnerability levels and disaster intensity parameters.
    """

    def __init__(self, config: DisasterSimulationConfig):
        """
        Initialize the disaster simulator with configuration.

        Args:
            config: DisasterSimulationConfig object with simulation parameters
        """
        self.config = config
        if config.random_seed is not None:
            random.seed(config.random_seed)
            np.random.seed(config.random_seed)

    def simulate_tree_collapse(
        self,
        trees_data: Dict[str, Any],
        roads_data: Dict[str, Any],
        nodes_data: Dict[str, Any] = None,
    ) -> DisasterSimulationResult:
        """
        Main simulation method implementing SE-2.1 tree collapse logic.

        Args:
            trees_data: Dictionary of trees from world synthesizer
            roads_data: Dictionary of road network data

        Returns:
            DisasterSimulationResult with all collapse events and obstructions
        """
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        simulated_at = datetime.now()

        # Step 1: Simulate tree collapses based on vulnerability
        collapse_events = self._simulate_tree_collapses(trees_data)

        # Step 2: Calculate road obstructions from collapsed trees
        road_obstructions = self._calculate_road_obstructions(
            collapse_events, roads_data, nodes_data
        )

        # Step 3: Generate summary statistics
        stats = self._generate_simulation_statistics(
            collapse_events, road_obstructions, trees_data, roads_data
        )

        return DisasterSimulationResult(
            simulation_id=simulation_id,
            simulated_at=simulated_at,
            disaster_events=collapse_events,
            road_obstructions=road_obstructions,
            simulation_config=self.config,
            **stats,
        )

    def _simulate_tree_collapses(
        self, trees_data: Dict[str, Any]
    ) -> List[TreeCollapseEvent]:
        """
        Simulate tree collapses based on vulnerability levels and disaster intensity.

        Implementation of SE-2.1 core logic:
        - Level I (High risk): 80% collapse probability
        - Level II (Medium risk): 50% collapse probability
        - Level III (Low risk): 10% collapse probability

        Args:
            trees_data: Dictionary of tree objects from world synthesizer

        Returns:
            List of TreeCollapseEvent objects for collapsed trees
        """
        collapse_events = []

        for tree_id, tree_data in trees_data.items():
            vulnerability_level = tree_data["vulnerability_level"]

            # Get collapse probability for this vulnerability level
            base_probability = self.config.vulnerability_collapse_rates.get(
                vulnerability_level, 0.0
            )

            # Apply disaster intensity multiplier (1.0-10.0 scale)
            # Higher intensity increases collapse probability
            intensity_multiplier = min(1.0, self.config.disaster_intensity / 10.0)
            final_probability = min(
                1.0, base_probability * (0.5 + 0.5 * intensity_multiplier)
            )

            # Random collapse decision
            if random.random() <= final_probability:
                # Tree collapses - generate collapse event
                collapse_angle = random.uniform(0.0, 360.0)

                collapse_event = self._create_tree_collapse_event(
                    tree_id=tree_id, tree_data=tree_data, collapse_angle=collapse_angle
                )
                collapse_events.append(collapse_event)

        return collapse_events

    def _create_tree_collapse_event(
        self, tree_id: str, tree_data: Dict[str, Any], collapse_angle: float
    ) -> TreeCollapseEvent:
        """
        Create a TreeCollapseEvent with blockage polygon calculation.

        Args:
            tree_id: Unique identifier for the tree
            tree_data: Tree object data from world synthesizer
            collapse_angle: Collapse direction in degrees (0-359)

        Returns:
            TreeCollapseEvent with calculated blockage polygon
        """
        tree_x = tree_data["x"]
        tree_y = tree_data["y"]
        tree_height = tree_data["height"]
        trunk_width = tree_data["trunk_width"]

        # Calculate blockage polygon based on collapse direction and tree dimensions
        blockage_polygon = self._calculate_tree_blockage_polygon(
            tree_x, tree_y, tree_height, trunk_width, collapse_angle
        )

        return TreeCollapseEvent(
            event_id=f"collapse_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
            location=(tree_x, tree_y),
            severity=self._calculate_event_severity(tree_data),
            tree_id=tree_id,
            vulnerability_level=VulnerabilityLevel(tree_data["vulnerability_level"]),
            collapse_angle=collapse_angle,
            tree_height=tree_height,
            trunk_width=trunk_width,
            blockage_polygon=blockage_polygon,
        )

    def _calculate_tree_blockage_polygon(
        self,
        tree_x: float,
        tree_y: float,
        tree_height: float,
        trunk_width: float,
        collapse_angle: float,
    ) -> List[Tuple[float, float]]:
        """
        Calculate the blockage polygon created by a collapsed tree.

        The polygon represents the area blocked by the fallen tree trunk and canopy.
        Approximates the tree as a rectangle falling in the collapse direction.

        Args:
            tree_x: Tree center X coordinate
            tree_y: Tree center Y coordinate
            tree_height: Height of the tree (becomes length when fallen)
            trunk_width: Width of tree trunk (becomes width when fallen)
            collapse_angle: Collapse direction in degrees

        Returns:
            List of (x, y) coordinate tuples forming the blockage polygon
        """
        # Convert angle to radians
        angle_rad = math.radians(collapse_angle)

        # Calculate the end point where tree crown lands
        end_x = tree_x + tree_height * math.cos(angle_rad)
        end_y = tree_y + tree_height * math.sin(angle_rad)

        # Calculate perpendicular offset for tree width
        perpendicular_angle = angle_rad + math.pi / 2
        width_offset_x = (trunk_width / 2) * math.cos(perpendicular_angle)
        width_offset_y = (trunk_width / 2) * math.sin(perpendicular_angle)

        # Create rectangle polygon representing fallen tree
        # Four corners of the fallen tree rectangle
        polygon_points = [
            (tree_x + width_offset_x, tree_y + width_offset_y),  # Base left
            (tree_x - width_offset_x, tree_y - width_offset_y),  # Base right
            (end_x - width_offset_x, end_y - width_offset_y),  # Crown right
            (end_x + width_offset_x, end_y + width_offset_y),  # Crown left
        ]

        return polygon_points

    def _calculate_road_obstructions(
        self,
        collapse_events: List[TreeCollapseEvent],
        roads_data: Dict[str, Any],
        nodes_data: Dict[str, Any] = None,
    ) -> List[RoadObstruction]:
        """
        Calculate road obstructions caused by tree collapse events.

        For each collapsed tree, determine which road segments are affected
        and calculate the remaining passable width.

        Args:
            collapse_events: List of tree collapse events
            roads_data: Dictionary of road network data

        Returns:
            List of RoadObstruction objects
        """
        road_obstructions = []

        for event in collapse_events:
            # Create Shapely polygon for the tree blockage
            tree_polygon = Polygon(event.blockage_polygon)

            # Check intersection with all road edges
            for road_id, road_data in roads_data.items():
                if nodes_data:
                    # Use precise geometric intersection with node data
                    obstruction = self._calculate_road_intersection(
                        event, tree_polygon, road_id, road_data, nodes_data
                    )
                    if obstruction:
                        road_obstructions.append(obstruction)
                else:
                    # Fallback method without precise geometry
                    obstruction = self._calculate_approximate_road_intersection(
                        event, tree_polygon, road_id, road_data
                    )
                    if obstruction:
                        road_obstructions.append(obstruction)

        return road_obstructions

    def _calculate_tree_road_blockage_simple(
        self,
        collapse_event: TreeCollapseEvent,
        road_data: Dict[str, Any],
        nodes_data: Dict[str, Any],
    ) -> Tuple[float, float]:
        """
        使用簡化三角學方法計算樹木佔用的道路寬度。

        Args:
            collapse_event: 樹木倒塌事件
            road_data: 道路資料
            nodes_data: 節點資料

        Returns:
            (佔用的道路寬度, 阻塞率%)
        """
        # 獲取樹木和道路資訊
        tree_x, tree_y = collapse_event.location
        tree_height = collapse_event.tree_height
        tree_angle = math.radians(collapse_event.collapse_angle)
        road_width = road_data.get("width", 6.0)

        # 獲取道路節點座標
        from_node_id = road_data.get("from_node")
        to_node_id = road_data.get("to_node")

        if not from_node_id or not to_node_id:
            return 0.0, 0.0

        from_node = nodes_data.get(from_node_id)
        to_node = nodes_data.get(to_node_id)

        if not from_node or not to_node:
            return 0.0, 0.0

        # 計算道路方向角度
        road_dx = to_node["x"] - from_node["x"]
        road_dy = to_node["y"] - from_node["y"]
        road_angle = math.atan2(road_dy, road_dx)

        # 檢查樹是否與道路相交
        tree_end_x = tree_x + tree_height * math.cos(tree_angle)
        tree_end_y = tree_y + tree_height * math.sin(tree_angle)

        # 預先檢查：計算樹到道路的距離，判斷是否可能相交
        tree_to_road_distance = self._calculate_point_to_line_distance(
            tree_x, tree_y, from_node, to_node
        )

        # 如果樹距離道路太遠，樹倒下後也無法觸及道路
        road_half_width = road_width / 2
        if tree_to_road_distance > (tree_height + road_half_width):
            return 0.0, 0.0

        # 更精確的相交檢查
        if not self._line_intersects_road(
            tree_x, tree_y, tree_end_x, tree_end_y, from_node, to_node, road_width
        ):
            return 0.0, 0.0

        # 計算樹線與道路垂直方向的夾角
        angle_diff = abs(tree_angle - road_angle)
        # 確保角度在 0-π/2 範圍內
        if angle_diff > math.pi / 2:
            angle_diff = math.pi - angle_diff
        if angle_diff > math.pi / 2:
            angle_diff = math.pi / 2 - (angle_diff - math.pi / 2)

        # 計算樹總長度在道路垂直方向的投影
        perpendicular_road_angle = road_angle + math.pi / 2  # 道路垂直方向
        tree_to_perpendicular_angle = abs(tree_angle - perpendicular_road_angle)

        # 標準化角度到 [0, π/2]
        while tree_to_perpendicular_angle > math.pi:
            tree_to_perpendicular_angle -= math.pi
        if tree_to_perpendicular_angle > math.pi / 2:
            tree_to_perpendicular_angle = math.pi - tree_to_perpendicular_angle

        # 樹總長度在道路垂直方向的投影
        tree_projection_length = tree_height * abs(
            math.cos(tree_to_perpendicular_angle)
        )

        # 計算樹到道路邊緣的距離
        # 如果樹在道路外側，需要減去樹到道路邊緣的距離
        road_half_width = road_width / 2
        distance_to_road_edge = max(0, tree_to_road_distance - road_half_width)

        # 計算實際佔用的道路寬度
        # 樹投影長度 - 樹到道路邊緣距離 = 實際佔用寬度
        occupied_width = max(0, tree_projection_length - distance_to_road_edge)

        # 確保不超過道路寬度（物理限制）
        occupied_width = min(occupied_width, road_width)

        # 計算阻塞率
        blockage_percentage = (
            min(100.0, (occupied_width / road_width) * 100) if road_width > 0 else 100.0
        )

        return occupied_width, blockage_percentage

    def _line_intersects_road(
        self,
        line_x1: float,
        line_y1: float,
        line_x2: float,
        line_y2: float,
        from_node: Dict[str, Any],
        to_node: Dict[str, Any],
        road_width: float,
    ) -> bool:
        """
        檢查線段是否與道路矩形相交
        """
        # 創建道路矩形的四個頂點
        road_dx = to_node["x"] - from_node["x"]
        road_dy = to_node["y"] - from_node["y"]
        road_length = math.sqrt(road_dx * road_dx + road_dy * road_dy)

        if road_length == 0:
            return False

        # 標準化道路方向向量
        road_dx_norm = road_dx / road_length
        road_dy_norm = road_dy / road_length

        # 垂直向量
        perp_x = -road_dy_norm * (road_width / 2)
        perp_y = road_dx_norm * (road_width / 2)

        # 道路矩形的四個頂點
        road_corners = [
            (from_node["x"] + perp_x, from_node["y"] + perp_y),
            (from_node["x"] - perp_x, from_node["y"] - perp_y),
            (to_node["x"] - perp_x, to_node["y"] - perp_y),
            (to_node["x"] + perp_x, to_node["y"] + perp_y),
        ]

        # 簡化檢查：看樹線的起點或終點是否在道路矩形內，或者線段是否穿過道路
        from shapely.geometry import LineString, Polygon

        tree_line = LineString([(line_x1, line_y1), (line_x2, line_y2)])
        road_polygon = Polygon(road_corners)

        return tree_line.intersects(road_polygon)

    def _calculate_point_to_line_distance(
        self,
        point_x: float,
        point_y: float,
        from_node: Dict[str, Any],
        to_node: Dict[str, Any],
    ) -> float:
        """
        計算點到線段的垂直距離（點到直線的最短距離）

        Args:
            point_x: 點的 X 座標
            point_y: 點的 Y 座標
            from_node: 線段起點
            to_node: 線段終點

        Returns:
            點到線段的垂直距離（米）
        """
        # 線段的起點和終點
        x1, y1 = from_node["x"], from_node["y"]
        x2, y2 = to_node["x"], to_node["y"]

        # 計算線段的長度
        line_length_squared = (x2 - x1) ** 2 + (y2 - y1) ** 2

        if line_length_squared == 0:
            # 線段長度為0（起點和終點相同）
            return math.sqrt((point_x - x1) ** 2 + (point_y - y1) ** 2)

        # 使用點到直線距離公式：|ax + by + c| / sqrt(a² + b²)
        # 直線方程：(y2-y1)x - (x2-x1)y + (x2-x1)y1 - (y2-y1)x1 = 0
        # 即：ax + by + c = 0，其中：
        a = y2 - y1
        b = x1 - x2
        c = (x2 - x1) * y1 - (y2 - y1) * x1

        # 點到直線的垂直距離
        distance = abs(a * point_x + b * point_y + c) / math.sqrt(a * a + b * b)

        return distance

    def _calculate_road_intersection(
        self,
        collapse_event: TreeCollapseEvent,
        tree_polygon: Polygon,
        road_id: str,
        road_data: Dict[str, Any],
        nodes_data: Dict[str, Any],
    ) -> RoadObstruction:
        """
        Calculate the intersection between a fallen tree and a road segment.
        使用簡化的三角學方法計算阻塞率。

        Args:
            collapse_event: The tree collapse event
            tree_polygon: Shapely polygon of the fallen tree (unused in new method)
            road_id: ID of the road segment
            road_data: Road segment data
            nodes_data: Node coordinates for road geometry

        Returns:
            RoadObstruction object if intersection exists, None otherwise
        """
        # 使用新的三角學方法計算佔用寬度和阻塞率
        occupied_width, blocked_percentage = self._calculate_tree_road_blockage_simple(
            collapse_event, road_data, nodes_data
        )

        # 如果沒有阻塞，返回 None
        if occupied_width <= 0 or blocked_percentage <= 0:
            return None

        road_width = road_data.get("width", 6.0)
        remaining_width = max(0.0, road_width - occupied_width)

        # 簡化的方向性阻塞計算
        # 假設阻塞影響所有方向
        directional_blockage = {
            "forward": remaining_width / 2,  # 前進方向剩餘寬度
            "backward": remaining_width / 2,  # 後退方向剩餘寬度
        }

        # 確定受影響的方向
        min_width_threshold = 2.0
        affected_directions = [
            direction
            for direction, width in directional_blockage.items()
            if width < min_width_threshold
        ]

        # 簡化的阻塞多邊形（使用樹的阻塞多邊形）
        obstruction_coords = collapse_event.blockage_polygon

        return RoadObstruction(
            obstruction_id=f"obstruction_{uuid.uuid4().hex[:8]}",
            road_edge_id=road_id,
            obstruction_polygon=obstruction_coords,
            remaining_width=remaining_width,
            blocked_percentage=blocked_percentage,
            caused_by_event=collapse_event.event_id,
            directional_blockage=directional_blockage,
            affected_directions=affected_directions,
        )

    def _create_road_polygon(
        self,
        from_node_data: Dict[str, Any],
        to_node_data: Dict[str, Any],
        road_width: float,
    ) -> Polygon:
        """
        Create an accurate road polygon from node coordinates and width.

        Implements SE-2.2 requirement for precise road geometry calculation.

        Args:
            from_node_data: Starting node coordinates
            to_node_data: Ending node coordinates
            road_width: Road width in meters

        Returns:
            Shapely Polygon representing the road segment
        """
        from_x, from_y = from_node_data["x"], from_node_data["y"]
        to_x, to_y = to_node_data["x"], to_node_data["y"]

        # Calculate road direction vector
        dx = to_x - from_x
        dy = to_y - from_y
        road_length = math.sqrt(dx * dx + dy * dy)

        if road_length == 0:
            return None

        # Normalize direction vector
        dx_norm = dx / road_length
        dy_norm = dy / road_length

        # Calculate perpendicular vector for road width
        perp_x = -dy_norm * (road_width / 2)
        perp_y = dx_norm * (road_width / 2)

        # Create road polygon (rectangle)
        road_corners = [
            (from_x + perp_x, from_y + perp_y),  # From left
            (from_x - perp_x, from_y - perp_y),  # From right
            (to_x - perp_x, to_y - perp_y),  # To right
            (to_x + perp_x, to_y + perp_y),  # To left
        ]

        return Polygon(road_corners)

    def _calculate_remaining_road_width(
        self, road_polygon: Polygon, intersection: Polygon, original_width: float
    ) -> float:
        """
        Calculate remaining passable road width after obstruction.

        Key insight: Blockage is a CROSS-SECTIONAL concept, not area-based.
        We need to find the narrowest passable width at the intersection point.

        Args:
            road_polygon: Full road polygon
            intersection: Intersection with obstruction
            original_width: Original road width

        Returns:
            Remaining passable width in meters at the narrowest point
        """
        try:
            # Get road centerline and direction
            road_bounds = road_polygon.bounds  # (minx, miny, maxx, maxy)
            road_length = max(
                road_bounds[2] - road_bounds[0], road_bounds[3] - road_bounds[1]
            )

            # Calculate cross-sectional blockage at the intersection
            min_remaining_width = self._calculate_cross_sectional_width(
                road_polygon, intersection, original_width
            )
            return max(0.0, min_remaining_width)

        except Exception as e:
            # Emergency fallback: if there's any intersection, assume significant blockage
            return original_width * 0.2

    def _calculate_cross_sectional_width(
        self, road_polygon: Polygon, intersection: Polygon, original_width: float
    ) -> float:
        """
        Calculate the minimum cross-sectional remaining width.

        This method samples multiple cross-sections through the intersection
        to find the narrowest passable point.
        """

        # Get road geometry
        road_bounds = road_polygon.bounds
        intersection_bounds = intersection.bounds

        # Determine road direction (longer dimension)
        road_dx = road_bounds[2] - road_bounds[0]  # width in x direction
        road_dy = road_bounds[3] - road_bounds[1]  # width in y direction

        if road_dx > road_dy:
            # Road runs primarily in X direction
            is_horizontal = True
            road_start = road_bounds[0]
            road_end = road_bounds[2]
            road_width_dim = road_dy
        else:
            # Road runs primarily in Y direction
            is_horizontal = False
            road_start = road_bounds[1]
            road_end = road_bounds[3]
            road_width_dim = road_dx

        # Sample cross-sections through the intersection area
        intersection_start = intersection_bounds[0 if is_horizontal else 1]
        intersection_end = intersection_bounds[2 if is_horizontal else 3]

        # Create multiple cross-sectional lines through the intersection
        num_samples = 10
        min_remaining_width = original_width  # Start with full width

        for i in range(num_samples):
            # Position along the road where we check the cross-section
            if intersection_start == intersection_end:
                position = intersection_start
            else:
                position = intersection_start + (
                    intersection_end - intersection_start
                ) * i / (num_samples - 1)

            # Create cross-sectional line perpendicular to road direction
            if is_horizontal:
                # Road is horizontal, so cross-section is vertical
                cross_line = LineString(
                    [
                        (position, road_bounds[1] - 1),  # Extend beyond road
                        (position, road_bounds[3] + 1),
                    ]
                )
            else:
                # Road is vertical, so cross-section is horizontal
                cross_line = LineString(
                    [
                        (road_bounds[0] - 1, position),  # Extend beyond road
                        (road_bounds[2] + 1, position),
                    ]
                )

            # Calculate remaining width at this cross-section
            remaining_width = self._calculate_width_at_cross_section(
                cross_line, road_polygon, intersection, original_width
            )

            min_remaining_width = min(min_remaining_width, remaining_width)

        return min_remaining_width

    def _calculate_width_at_cross_section(
        self,
        cross_line: LineString,
        road_polygon: Polygon,
        intersection: Polygon,
        original_width: float,
    ) -> float:
        """
        Calculate remaining width at a specific cross-section line.
        """
        try:
            # Get intersection of cross-line with road polygon
            road_intersection = cross_line.intersection(road_polygon)
            if road_intersection.is_empty:
                return original_width  # No intersection means full width available

            # Get intersection of cross-line with obstruction
            obstruction_intersection = cross_line.intersection(intersection)
            if obstruction_intersection.is_empty:
                return original_width  # No obstruction at this cross-section

            # Calculate blocked length along this cross-section
            if hasattr(obstruction_intersection, "length"):
                blocked_length = obstruction_intersection.length
            elif hasattr(obstruction_intersection, "coords"):
                # Point intersection
                blocked_length = 0.0
            else:
                blocked_length = 0.0

            # Calculate total road width at this cross-section
            if hasattr(road_intersection, "length"):
                total_road_width = road_intersection.length
            else:
                total_road_width = original_width

            # Remaining width is total width minus blocked width
            remaining_width = total_road_width - blocked_length

            return max(0.0, remaining_width)

        except Exception as e:
            return original_width * 0.5  # Conservative fallback

    def _calculate_directional_blockage(
        self,
        road_polygon: Polygon,
        intersection: Polygon,
        road_data: Dict[str, Any],
        original_width: float,
    ) -> Dict[str, float]:
        """
        Calculate remaining width for each direction separately for bidirectional roads.

        For Taiwan's right-hand traffic:
        - Forward direction uses right side of road
        - Backward direction uses left side of road

        Returns:
            Dict with 'forward' and 'backward' remaining widths
        """
        # Get road lane information if available
        lane_info = road_data.get("lane_info", [])
        is_bidirectional = road_data.get("is_bidirectional", True)

        if not is_bidirectional or not lane_info:
            # For unidirectional roads, use simple calculation
            remaining_width = self._calculate_cross_sectional_width(
                road_polygon, intersection, original_width
            )
            direction = "forward"  # Default direction
            return {direction: remaining_width, "backward": 0.0}

        # For bidirectional roads, calculate each direction separately
        forward_lanes = [lane for lane in lane_info if lane["direction"] == "forward"]
        backward_lanes = [lane for lane in lane_info if lane["direction"] == "backward"]

        forward_width = sum(lane["width"] for lane in forward_lanes)
        backward_width = sum(lane["width"] for lane in backward_lanes)

        # Calculate which side of the road is more blocked
        remaining_widths = self._calculate_side_specific_blockage(
            road_polygon, intersection, forward_width, backward_width
        )

        return remaining_widths

    def _calculate_side_specific_blockage(
        self,
        road_polygon: Polygon,
        intersection: Polygon,
        forward_width: float,
        backward_width: float,
    ) -> Dict[str, float]:
        """
        Calculate blockage for left and right sides of the road separately.

        Taiwan traffic:
        - Right side = Forward direction
        - Left side = Backward direction
        """
        from shapely.geometry import LineString

        # Get road centerline and direction
        road_bounds = road_polygon.bounds
        road_dx = road_bounds[2] - road_bounds[0]
        road_dy = road_bounds[3] - road_bounds[1]

        is_horizontal = road_dx > road_dy

        # Sample multiple cross-sections to find worst-case blockage
        num_samples = 5
        min_forward_width = forward_width
        min_backward_width = backward_width

        if is_horizontal:
            # Road runs horizontally
            start_x = road_bounds[0]
            end_x = road_bounds[2]
            center_y = (road_bounds[1] + road_bounds[3]) / 2

            for i in range(num_samples):
                sample_x = start_x + (end_x - start_x) * i / (num_samples - 1)

                # Create cross-sectional line
                cross_line = LineString(
                    [(sample_x, road_bounds[1] - 1), (sample_x, road_bounds[3] + 1)]
                )

                # Calculate blockage at this cross-section
                forward_remain, backward_remain = (
                    self._calculate_cross_section_directional_blockage(
                        cross_line,
                        road_polygon,
                        intersection,
                        forward_width,
                        backward_width,
                        center_y,
                        True,
                    )
                )

                min_forward_width = min(min_forward_width, forward_remain)
                min_backward_width = min(min_backward_width, backward_remain)

        else:
            # Road runs vertically
            start_y = road_bounds[1]
            end_y = road_bounds[3]
            center_x = (road_bounds[0] + road_bounds[2]) / 2

            for i in range(num_samples):
                sample_y = start_y + (end_y - start_y) * i / (num_samples - 1)

                # Create cross-sectional line
                cross_line = LineString(
                    [(road_bounds[0] - 1, sample_y), (road_bounds[2] + 1, sample_y)]
                )

                # Calculate blockage at this cross-section
                forward_remain, backward_remain = (
                    self._calculate_cross_section_directional_blockage(
                        cross_line,
                        road_polygon,
                        intersection,
                        forward_width,
                        backward_width,
                        center_x,
                        False,
                    )
                )

                min_forward_width = min(min_forward_width, forward_remain)
                min_backward_width = min(min_backward_width, backward_remain)

        return {
            "forward": max(0.0, min_forward_width),
            "backward": max(0.0, min_backward_width),
        }

    def _calculate_cross_section_directional_blockage(
        self,
        cross_line: LineString,
        road_polygon: Polygon,
        intersection: Polygon,
        forward_width: float,
        backward_width: float,
        center_coord: float,  # center Y for horizontal roads, center X for vertical roads
        is_horizontal: bool,
    ) -> Tuple[float, float]:
        """
        Calculate directional blockage at a specific cross-section.

        Returns: (forward_remaining_width, backward_remaining_width)
        """
        try:
            # Get road cross-section
            road_cross = cross_line.intersection(road_polygon)
            if road_cross.is_empty:
                return forward_width, backward_width

            # Get obstruction cross-section
            obstruction_cross = cross_line.intersection(intersection)
            if obstruction_cross.is_empty:
                return forward_width, backward_width

            # Determine which side of the center line is blocked
            if hasattr(obstruction_cross, "coords"):
                obstruction_coords = list(obstruction_cross.coords)
            elif hasattr(obstruction_cross, "geoms"):
                # Handle MultiPoint or MultiLineString
                obstruction_coords = []
                for geom in obstruction_cross.geoms:
                    if hasattr(geom, "coords"):
                        obstruction_coords.extend(geom.coords)
            else:
                obstruction_coords = []

            if not obstruction_coords:
                return forward_width, backward_width

            # Calculate blockage on each side of center line
            forward_blockage = 0.0  # Right side for Taiwan traffic
            backward_blockage = 0.0  # Left side for Taiwan traffic

            for coord in obstruction_coords:
                if is_horizontal:
                    # For horizontal roads, compare Y coordinates
                    if coord[1] > center_coord:  # Above center line (left side)
                        backward_blockage += 0.5  # Approximate blockage
                    else:  # Below center line (right side)
                        forward_blockage += 0.5
                else:
                    # For vertical roads, compare X coordinates
                    if coord[0] > center_coord:  # Right of center line
                        forward_blockage += 0.5
                    else:  # Left of center line
                        backward_blockage += 0.5

            # Calculate remaining widths
            forward_remaining = max(0.0, forward_width - forward_blockage)
            backward_remaining = max(0.0, backward_width - backward_blockage)

            return forward_remaining, backward_remaining

        except Exception as e:
            return forward_width * 0.5, backward_width * 0.5

    def _estimate_road_length_from_polygon(self, road_polygon: Polygon) -> float:
        """
        Estimate road length from its polygon representation.

        Args:
            road_polygon: Road polygon

        Returns:
            Estimated road length in meters
        """
        try:
            # Get the centroid and approximate length from polygon bounds
            minx, miny, maxx, maxy = road_polygon.bounds
            return max(maxx - minx, maxy - miny)
        except Exception:
            return 100.0  # Default fallback length

    def _extract_polygon_coordinates(self, geom) -> List[Tuple[float, float]]:
        """
        Extract coordinate list from Shapely geometry.

        Args:
            geom: Shapely geometry object

        Returns:
            List of coordinate tuples
        """
        coords = []

        try:
            if hasattr(geom, "exterior"):
                # Single Polygon
                coords.extend(list(geom.exterior.coords))
            elif hasattr(geom, "geoms"):
                # MultiPolygon or GeometryCollection
                for sub_geom in geom.geoms:
                    if hasattr(sub_geom, "exterior"):
                        coords.extend(list(sub_geom.exterior.coords))
            else:
                # Other geometry types - convert to coordinate list
                coords = list(geom.coords) if hasattr(geom, "coords") else []

        except Exception:
            # Fallback empty coordinates
            coords = []

        return coords

    def _calculate_approximate_road_intersection(
        self,
        collapse_event: TreeCollapseEvent,
        tree_polygon: Polygon,
        road_id: str,
        road_data: Dict[str, Any],
    ) -> RoadObstruction:
        """
        Calculate approximate road intersection without precise node geometry.

        Fallback method for when node coordinates are not available.

        Args:
            collapse_event: The tree collapse event
            tree_polygon: Shapely polygon of the fallen tree
            road_id: ID of the road segment
            road_data: Road segment data

        Returns:
            RoadObstruction object if intersection likely, None otherwise
        """
        road_width = road_data.get("width", 6.0)

        # Use a simple distance-based approach
        # Check if tree position is close enough to potentially affect road
        tree_location = collapse_event.location
        tree_height = collapse_event.tree_height

        # Create approximate circular area of influence
        influence_radius = tree_height + road_width

        # Simplified obstruction for roads that might be affected
        # In practice this would need more sophisticated spatial analysis
        return RoadObstruction(
            obstruction_id=f"obstruction_{uuid.uuid4().hex[:8]}",
            road_edge_id=road_id,
            obstruction_polygon=list(tree_polygon.exterior.coords),
            remaining_width=max(0.0, road_width * 0.3),  # Assume significant blockage
            blocked_percentage=70.0,  # Conservative estimate
            caused_by_event=collapse_event.event_id,
        )

    def _calculate_event_severity(self, tree_data: Dict[str, Any]) -> float:
        """
        Calculate the severity of a tree collapse event.

        Severity is based on tree size and vulnerability level.

        Args:
            tree_data: Tree object data

        Returns:
            Severity value between 0.0 and 1.0
        """
        height = tree_data.get("height", 10.0)
        width = tree_data.get("trunk_width", 0.5)
        vulnerability = tree_data.get("vulnerability_level", "III")

        # Base severity from tree size (normalized to typical ranges)
        size_factor = min(
            1.0, (height * width) / (20.0 * 1.0)
        )  # Max at 20m height, 1m width

        # Vulnerability multiplier
        vulnerability_multipliers = {"I": 1.0, "II": 0.7, "III": 0.4}
        vulnerability_factor = vulnerability_multipliers.get(vulnerability, 0.5)

        return min(1.0, size_factor * vulnerability_factor)

    def _generate_simulation_statistics(
        self,
        collapse_events: List[TreeCollapseEvent],
        road_obstructions: List[RoadObstruction],
        trees_data: Dict[str, Any],
        roads_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for the simulation result.

        Args:
            collapse_events: List of tree collapse events
            road_obstructions: List of road obstructions
            trees_data: Original tree data
            roads_data: Original road data

        Returns:
            Dictionary of statistical summaries
        """
        # Count trees affected by vulnerability level
        trees_by_level = {"I": 0, "II": 0, "III": 0}
        for event in collapse_events:
            level = event.vulnerability_level.value
            trees_by_level[level] += 1

        # Calculate blocked road statistics
        affected_roads = set(obs.road_edge_id for obs in road_obstructions)
        total_blocked_length = 0.0
        total_blockage_percentage = 0.0

        for obstruction in road_obstructions:
            # Approximate road length (simplified)
            road_data = roads_data.get(obstruction.road_edge_id, {})
            estimated_length = (
                100.0  # Placeholder - would calculate from actual geometry
            )
            total_blocked_length += estimated_length * (
                obstruction.blocked_percentage / 100.0
            )
            total_blockage_percentage += obstruction.blocked_percentage

        avg_blockage_percentage = (
            total_blockage_percentage / len(road_obstructions)
            if road_obstructions
            else 0.0
        )

        return {
            "total_trees_affected": len(collapse_events),
            "total_roads_affected": len(affected_roads),
            "total_blocked_road_length": total_blocked_length,
            "trees_affected_by_level": trees_by_level,
            "average_road_blockage_percentage": avg_blockage_percentage,
        }
