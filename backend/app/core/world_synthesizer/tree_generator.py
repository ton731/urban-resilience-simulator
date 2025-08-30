import uuid
import random
import math
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
import numpy as np
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

from .map_generator import GeneratedMap, RoadEdge, MapNode


@dataclass
class Tree:
    """Represents a tree object in the simulation world"""
    id: str
    x: float
    y: float
    vulnerability_level: str  # "I" (high), "II" (medium), "III" (low)
    height: float  # in meters
    trunk_width: float  # in meters
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "vulnerability_level": self.vulnerability_level,
            "height": self.height,
            "trunk_width": self.trunk_width
        }


class TreeGenerator:
    """
    Implements WS-1.2: Tree Object Generation
    
    Generates trees along road edges with specified spacing, random offsets,
    and vulnerability level distribution according to configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Tree generation parameters
        self.tree_spacing = config.get("tree_spacing", 25.0)  # meters between trees
        self.max_offset = config.get("tree_max_offset", 8.0)  # max random offset from road
        self.road_buffer = config.get("tree_road_buffer", 3.0)  # minimum distance from road edge
        
        # Tree physical properties ranges
        self.height_range = config.get("tree_height_range", [4.0, 25.0])  # meters
        self.trunk_width_range = config.get("tree_trunk_width_range", [0.2, 1.5])  # meters
        
        # Vulnerability level distribution (must sum to 1.0)
        self.vulnerability_distribution = config.get("vulnerability_distribution", {
            "I": 0.1,   # High risk - 10%
            "II": 0.3,  # Medium risk - 30%
            "III": 0.6  # Low risk - 60%
        })
        
        # Validate vulnerability distribution
        total_prob = sum(self.vulnerability_distribution.values())
        if not math.isclose(total_prob, 1.0, rel_tol=1e-9):
            raise ValueError(f"Vulnerability distribution must sum to 1.0, got {total_prob}")
        
        # Create weighted list for random selection
        self._vulnerability_levels = []
        self._vulnerability_weights = []
        for level, weight in self.vulnerability_distribution.items():
            self._vulnerability_levels.append(level)
            self._vulnerability_weights.append(weight)
    
    def generate_trees_for_map(self, generated_map: GeneratedMap) -> Dict[str, Tree]:
        """
        Generate trees along all road edges in the map.
        
        Args:
            generated_map: GeneratedMap instance with road network
            
        Returns:
            Dict[str, Tree]: Dictionary of tree_id -> Tree objects
        """
        if not generated_map.edges:
            return {}
        
        trees = {}
        
        # Generate trees for each road edge
        for edge_id, edge in generated_map.edges.items():
            edge_trees = self._generate_trees_for_edge(edge, generated_map.nodes)
            trees.update(edge_trees)
        
        return trees
    
    def _generate_trees_for_edge(self, edge: RoadEdge, nodes: Dict[str, MapNode]) -> Dict[str, Tree]:
        """
        Generate trees along both sides of a road edge.
        
        Args:
            edge: RoadEdge to generate trees along
            nodes: Dictionary of all map nodes
            
        Returns:
            Dict[str, Tree]: Trees generated for this edge
        """
        from_node = nodes.get(edge.from_node)
        to_node = nodes.get(edge.to_node)
        
        if not from_node or not to_node:
            return {}
        
        # Calculate edge geometry
        edge_length = math.sqrt((to_node.x - from_node.x)**2 + (to_node.y - from_node.y)**2)
        
        # Skip very short edges
        if edge_length < self.tree_spacing:
            return {}
        
        # Calculate edge direction vector
        dx = (to_node.x - from_node.x) / edge_length
        dy = (to_node.y - from_node.y) / edge_length
        
        # Calculate perpendicular vector for offset
        perp_x = -dy  # Perpendicular to edge direction
        perp_y = dx
        
        trees = {}
        
        # Generate trees on both sides of the road
        for side in [-1, 1]:  # -1 for left side, 1 for right side
            side_trees = self._generate_trees_for_side(
                from_node, to_node, edge, 
                dx, dy, perp_x, perp_y, 
                side, edge_length
            )
            trees.update(side_trees)
        
        return trees
    
    def _generate_trees_for_side(self, from_node: MapNode, to_node: MapNode, 
                                 edge: RoadEdge, dx: float, dy: float, 
                                 perp_x: float, perp_y: float, side: int, 
                                 edge_length: float) -> Dict[str, Tree]:
        """
        Generate trees on one side of a road edge.
        """
        trees = {}
        
        # Calculate base distance from road center
        base_distance = (edge.width / 2) + self.road_buffer
        
        # Calculate number of trees along this side
        num_trees = int(edge_length / self.tree_spacing)
        
        for i in range(num_trees):
            # Position along the edge (with some randomization)
            t = (i + 0.5 + random.uniform(-0.3, 0.3)) / num_trees
            t = max(0.1, min(0.9, t))  # Keep within bounds
            
            # Base position along the edge
            base_x = from_node.x + t * (to_node.x - from_node.x)
            base_y = from_node.y + t * (to_node.y - from_node.y)
            
            # Offset from road edge
            offset_distance = base_distance + random.uniform(0, self.max_offset)
            offset_x = base_x + side * perp_x * offset_distance
            offset_y = base_y + side * perp_y * offset_distance
            
            # Generate tree properties
            tree_id = str(uuid.uuid4())
            vulnerability_level = random.choices(
                self._vulnerability_levels, 
                weights=self._vulnerability_weights
            )[0]
            
            # Generate physical properties based on vulnerability
            height, trunk_width = self._generate_tree_dimensions(vulnerability_level)
            
            tree = Tree(
                id=tree_id,
                x=offset_x,
                y=offset_y,
                vulnerability_level=vulnerability_level,
                height=height,
                trunk_width=trunk_width
            )
            
            trees[tree_id] = tree
        
        return trees
    
    def _generate_tree_dimensions(self, vulnerability_level: str) -> Tuple[float, float]:
        """
        Generate tree height and trunk width based on vulnerability level.
        
        Higher vulnerability trees tend to be older/larger but less healthy.
        Lower vulnerability trees tend to be younger/smaller but healthier.
        
        Args:
            vulnerability_level: "I", "II", or "III"
            
        Returns:
            Tuple[float, float]: (height, trunk_width)
        """
        min_height, max_height = self.height_range
        min_trunk, max_trunk = self.trunk_width_range
        
        if vulnerability_level == "I":  # High vulnerability - larger, older trees
            height_factor = random.uniform(0.7, 1.0)
            trunk_factor = random.uniform(0.8, 1.0)
        elif vulnerability_level == "II":  # Medium vulnerability - medium size
            height_factor = random.uniform(0.4, 0.8)
            trunk_factor = random.uniform(0.5, 0.8)
        else:  # Level III - Low vulnerability - smaller, healthier trees
            height_factor = random.uniform(0.2, 0.6)
            trunk_factor = random.uniform(0.2, 0.6)
        
        height = min_height + height_factor * (max_height - min_height)
        trunk_width = min_trunk + trunk_factor * (max_trunk - min_trunk)
        
        # Add some randomness
        height += random.gauss(0, height * 0.1)  # 10% variance
        trunk_width += random.gauss(0, trunk_width * 0.15)  # 15% variance
        
        # Ensure minimum values
        height = max(2.0, height)
        trunk_width = max(0.1, trunk_width)
        
        return round(height, 2), round(trunk_width, 2)
    
    def get_generation_stats(self, trees: Dict[str, Tree]) -> Dict[str, Any]:
        """
        Calculate statistics about generated trees.
        
        Args:
            trees: Dictionary of generated trees
            
        Returns:
            Dict with tree statistics
        """
        if not trees:
            return {
                "total_trees": 0,
                "vulnerability_distribution": {level: 0 for level in self._vulnerability_levels},
                "average_height": 0.0,
                "average_trunk_width": 0.0
            }
        
        # Count by vulnerability level
        level_counts = {level: 0 for level in self._vulnerability_levels}
        total_height = 0.0
        total_trunk_width = 0.0
        
        for tree in trees.values():
            level_counts[tree.vulnerability_level] += 1
            total_height += tree.height
            total_trunk_width += tree.trunk_width
        
        total_trees = len(trees)
        
        return {
            "total_trees": total_trees,
            "vulnerability_distribution": level_counts,
            "vulnerability_percentages": {
                level: round(count / total_trees * 100, 1) 
                for level, count in level_counts.items()
            },
            "average_height": round(total_height / total_trees, 2),
            "average_trunk_width": round(total_trunk_width / total_trees, 2),
            "height_range": [
                round(min(tree.height for tree in trees.values()), 2),
                round(max(tree.height for tree in trees.values()), 2)
            ],
            "trunk_width_range": [
                round(min(tree.trunk_width for tree in trees.values()), 2),
                round(max(tree.trunk_width for tree in trees.values()), 2)
            ]
        }