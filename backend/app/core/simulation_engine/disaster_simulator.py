"""
Disaster Simulator Implementation (SE-2.1)
Handles tree collapse simulation based on vulnerability levels and disaster intensity.
"""

import math
import random
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple
from shapely.geometry import Polygon, Point
from shapely.ops import transform
import numpy as np

from .models import (
    DisasterSimulationConfig,
    DisasterSimulationResult,
    TreeCollapseEvent,
    RoadObstruction,
    VulnerabilityLevel
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
        roads_data: Dict[str, Any]
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
            collapse_events, roads_data
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
            **stats
        )
    
    def _simulate_tree_collapses(self, trees_data: Dict[str, Any]) -> List[TreeCollapseEvent]:
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
            vulnerability_level = tree_data['vulnerability_level']
            
            # Get collapse probability for this vulnerability level
            base_probability = self.config.vulnerability_collapse_rates.get(
                vulnerability_level, 0.0
            )
            
            # Apply disaster intensity multiplier (1.0-10.0 scale)
            # Higher intensity increases collapse probability
            intensity_multiplier = min(1.0, self.config.disaster_intensity / 10.0)
            final_probability = min(1.0, base_probability * (0.5 + 0.5 * intensity_multiplier))
            
            # Random collapse decision
            if random.random() <= final_probability:
                # Tree collapses - generate collapse event
                collapse_angle = random.uniform(0.0, 360.0)
                
                collapse_event = self._create_tree_collapse_event(
                    tree_id=tree_id,
                    tree_data=tree_data,
                    collapse_angle=collapse_angle
                )
                collapse_events.append(collapse_event)
        
        return collapse_events
    
    def _create_tree_collapse_event(
        self,
        tree_id: str,
        tree_data: Dict[str, Any],
        collapse_angle: float
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
        tree_x = tree_data['x']
        tree_y = tree_data['y']
        tree_height = tree_data['height']
        trunk_width = tree_data['trunk_width']
        
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
            vulnerability_level=VulnerabilityLevel(tree_data['vulnerability_level']),
            collapse_angle=collapse_angle,
            tree_height=tree_height,
            trunk_width=trunk_width,
            blockage_polygon=blockage_polygon
        )
    
    def _calculate_tree_blockage_polygon(
        self,
        tree_x: float,
        tree_y: float,
        tree_height: float,
        trunk_width: float,
        collapse_angle: float
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
            (end_x - width_offset_x, end_y - width_offset_y),    # Crown right
            (end_x + width_offset_x, end_y + width_offset_y),    # Crown left
        ]
        
        return polygon_points
    
    def _calculate_road_obstructions(
        self,
        collapse_events: List[TreeCollapseEvent],
        roads_data: Dict[str, Any]
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
                obstruction = self._calculate_road_intersection(
                    event, tree_polygon, road_id, road_data
                )
                if obstruction:
                    road_obstructions.append(obstruction)
        
        return road_obstructions
    
    def _calculate_road_intersection(
        self,
        collapse_event: TreeCollapseEvent,
        tree_polygon: Polygon,
        road_id: str,
        road_data: Dict[str, Any]
    ) -> RoadObstruction:
        """
        Calculate the intersection between a fallen tree and a road segment.
        
        Args:
            collapse_event: The tree collapse event
            tree_polygon: Shapely polygon of the fallen tree
            road_id: ID of the road segment  
            road_data: Road segment data
            
        Returns:
            RoadObstruction object if intersection exists, None otherwise
        """
        # For this implementation, we'll approximate roads as rectangular polygons
        # In a more sophisticated version, roads would have proper geometry
        
        # Extract road geometry (simplified as line with width)
        from_node = road_data.get('from_node')
        to_node = road_data.get('to_node') 
        road_width = road_data.get('width', 6.0)
        
        # This is a simplified implementation - in practice you'd need actual
        # road geometry coordinates from the road network data
        # For now, we'll create a rough approximation
        
        # Create a simple road polygon (this would be more sophisticated in practice)
        road_polygon = self._create_road_polygon_approximation(road_data)
        
        if road_polygon and tree_polygon.intersects(road_polygon):
            # Calculate intersection area and remaining width
            intersection = tree_polygon.intersection(road_polygon)
            intersection_area = intersection.area
            road_area = road_polygon.area
            
            blocked_percentage = min(100.0, (intersection_area / road_area) * 100)
            remaining_width = road_width * (1.0 - blocked_percentage / 100.0)
            
            # Get intersection polygon coordinates
            if hasattr(intersection, 'exterior'):
                obstruction_coords = list(intersection.exterior.coords)
            else:
                # Handle MultiPolygon case
                obstruction_coords = []
                for geom in intersection.geoms:
                    if hasattr(geom, 'exterior'):
                        obstruction_coords.extend(list(geom.exterior.coords))
            
            return RoadObstruction(
                obstruction_id=f"obstruction_{uuid.uuid4().hex[:8]}",
                road_edge_id=road_id,
                obstruction_polygon=obstruction_coords,
                remaining_width=remaining_width,
                blocked_percentage=blocked_percentage,
                caused_by_event=collapse_event.event_id
            )
        
        return None
    
    def _create_road_polygon_approximation(self, road_data: Dict[str, Any]) -> Polygon:
        """
        Create a rough polygon approximation for a road segment.
        
        This is a simplified implementation. In practice, the road network
        would provide actual geometric data for road segments.
        
        Args:
            road_data: Road segment data
            
        Returns:
            Shapely Polygon representing the road segment
        """
        # This is a placeholder - in a real implementation, you'd use
        # actual road geometry from the road network graph
        # For now, return None to indicate no geometry available
        return None
    
    def _calculate_event_severity(self, tree_data: Dict[str, Any]) -> float:
        """
        Calculate the severity of a tree collapse event.
        
        Severity is based on tree size and vulnerability level.
        
        Args:
            tree_data: Tree object data
            
        Returns:
            Severity value between 0.0 and 1.0
        """
        height = tree_data.get('height', 10.0)
        width = tree_data.get('trunk_width', 0.5)
        vulnerability = tree_data.get('vulnerability_level', 'III')
        
        # Base severity from tree size (normalized to typical ranges)
        size_factor = min(1.0, (height * width) / (20.0 * 1.0))  # Max at 20m height, 1m width
        
        # Vulnerability multiplier
        vulnerability_multipliers = {'I': 1.0, 'II': 0.7, 'III': 0.4}
        vulnerability_factor = vulnerability_multipliers.get(vulnerability, 0.5)
        
        return min(1.0, size_factor * vulnerability_factor)
    
    def _generate_simulation_statistics(
        self,
        collapse_events: List[TreeCollapseEvent],
        road_obstructions: List[RoadObstruction],
        trees_data: Dict[str, Any],
        roads_data: Dict[str, Any]
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
        trees_by_level = {'I': 0, 'II': 0, 'III': 0}
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
            estimated_length = 100.0  # Placeholder - would calculate from actual geometry
            total_blocked_length += estimated_length * (obstruction.blocked_percentage / 100.0)
            total_blockage_percentage += obstruction.blocked_percentage
        
        avg_blockage_percentage = (
            total_blockage_percentage / len(road_obstructions) 
            if road_obstructions else 0.0
        )
        
        return {
            'total_trees_affected': len(collapse_events),
            'total_roads_affected': len(affected_roads),
            'total_blocked_road_length': total_blocked_length,
            'trees_affected_by_level': trees_by_level,
            'average_road_blockage_percentage': avg_blockage_percentage
        }