import uuid
import random
import math
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


@dataclass
class Building:
    """Represents a building with population data"""
    id: str
    x: float
    y: float
    height: float  # in meters
    floors: int
    building_type: str  # "residential", "commercial", "industrial", "mixed"
    population: int
    capacity: int  # max population capacity
    footprint_area: float  # in square meters
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "height": self.height,
            "floors": self.floors,
            "building_type": self.building_type,
            "population": self.population,
            "capacity": self.capacity,
            "footprint_area": self.footprint_area
        }


class BuildingGenerator:
    """
    Implements WS-1.5: Building and Population Generation
    
    Generates buildings in non-road areas with procedural placement.
    Each building has properties like coordinates, height, population, and type.
    Population density tends to be higher in areas with denser road networks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Building generation parameters
        self.building_density = config.get("building_density", 0.3)  # buildings per 100m²
        self.min_building_distance = config.get("min_building_distance", 25.0)  # meters
        self.road_buffer_distance = config.get("road_buffer_distance", 15.0)  # meters from roads
        
        # Building type distribution (probabilities)
        self.building_type_weights = config.get("building_type_weights", {
            "residential": 0.6,
            "commercial": 0.2,
            "mixed": 0.15,
            "industrial": 0.05
        })
        
        # Building specifications by type
        self.building_specs = {
            "residential": {
                "min_height": 8.0,
                "max_height": 45.0,
                "min_floors": 2,
                "max_floors": 15,
                "population_per_floor": (2, 8),
                "footprint_range": (100, 400)
            },
            "commercial": {
                "min_height": 6.0,
                "max_height": 25.0,
                "min_floors": 1,
                "max_floors": 8,
                "population_per_floor": (0, 3),  # Commercial has fewer residents
                "footprint_range": (200, 800)
            },
            "mixed": {
                "min_height": 10.0,
                "max_height": 35.0,
                "min_floors": 3,
                "max_floors": 12,
                "population_per_floor": (1, 5),
                "footprint_range": (150, 600)
            },
            "industrial": {
                "min_height": 5.0,
                "max_height": 15.0,
                "min_floors": 1,
                "max_floors": 4,
                "population_per_floor": (0, 2),  # Very few residents
                "footprint_range": (300, 1200)
            }
        }
    
    def generate_buildings_for_map(self, map_data) -> Dict[str, Building]:
        """
        Generate buildings for the entire map, avoiding road areas.
        
        Args:
            map_data: GeneratedMap object containing boundary, nodes, and edges
            
        Returns:
            Dict[str, Building]: Dictionary of building_id -> Building objects
        """        
        # Create exclusion zones for roads and existing facilities
        exclusion_zones = self._create_exclusion_zones(map_data)
        
        # Generate candidate building positions
        candidate_positions = self._generate_candidate_positions(map_data, exclusion_zones)
        
        # Calculate road density map for population distribution
        road_density_map = self._calculate_road_density_map(map_data)
        
        # Generate buildings at candidate positions
        buildings = {}
        total_population = 0
        
        for position in candidate_positions:
            x, y = position
            
            # Calculate local road density to influence building type and population
            density_factor = self._get_density_factor(x, y, road_density_map, map_data.boundary)
            
            # Generate building
            building = self._generate_building(x, y, density_factor)
            buildings[building.id] = building
            total_population += building.population
        
        return buildings
    
    def _create_exclusion_zones(self, map_data) -> List[Polygon]:
        """
        Create polygons representing areas where buildings cannot be placed.
        This includes road buffers and facility areas.
        """
        exclusion_zones = []
        
        # Create buffers around all road edges
        for edge in map_data.edges.values():
            from_node = map_data.nodes[edge.from_node]
            to_node = map_data.nodes[edge.to_node]
            
            # Create line from road edge
            from_point = Point(from_node.x, from_node.y)
            to_point = Point(to_node.x, to_node.y)
            
            # Buffer the road line by road width + additional buffer
            total_buffer = (edge.width / 2) + self.road_buffer_distance
            road_polygon = Point(from_node.x, from_node.y).buffer(total_buffer).union(
                Point(to_node.x, to_node.y).buffer(total_buffer)
            )
            
            exclusion_zones.append(road_polygon)
        
        # Create buffers around facilities
        for facility in map_data.facilities.values():
            facility_buffer = Point(facility.x, facility.y).buffer(30.0)  # 30m buffer
            exclusion_zones.append(facility_buffer)
        
        return exclusion_zones
    
    def _generate_candidate_positions(self, map_data, exclusion_zones) -> List[Tuple[float, float]]:
        """
        Generate candidate positions for buildings using Poisson disk sampling
        to ensure good distribution with minimum distances.
        """
        boundary = map_data.boundary
        positions = []
        
        # Merge all exclusion zones for efficient checking
        merged_exclusions = unary_union(exclusion_zones) if exclusion_zones else None
        
        # Grid-based sampling with randomization
        grid_size = 50  # 50m grid for sampling
        attempts_per_cell = 3
        
        for x in np.arange(boundary.min_x, boundary.max_x, grid_size):
            for y in np.arange(boundary.min_y, boundary.max_y, grid_size):
                
                for _ in range(attempts_per_cell):
                    # Add randomness within grid cell
                    candidate_x = x + random.uniform(0, grid_size)
                    candidate_y = y + random.uniform(0, grid_size)
                    
                    # Check if position is valid
                    if self._is_valid_building_position(
                        candidate_x, candidate_y, positions, merged_exclusions
                    ):
                        positions.append((candidate_x, candidate_y))
                        break  # Found valid position for this cell
        
        # Apply density-based filtering
        final_positions = []
        for pos in positions:
            if random.random() < self.building_density:
                final_positions.append(pos)
        
        return final_positions
    
    def _is_valid_building_position(self, x: float, y: float, 
                                  existing_positions: List[Tuple[float, float]], 
                                  exclusion_zones) -> bool:
        """
        Check if a position is valid for building placement.
        """
        candidate_point = Point(x, y)
        
        # Check exclusion zones
        if exclusion_zones and exclusion_zones.contains(candidate_point):
            return False
        
        # Check minimum distance to existing buildings
        for ex_x, ex_y in existing_positions:
            distance = math.sqrt((x - ex_x)**2 + (y - ex_y)**2)
            if distance < self.min_building_distance:
                return False
        
        return True
    
    def _calculate_road_density_map(self, map_data) -> Dict[str, float]:
        """
        Calculate road density in different areas to influence population distribution.
        Higher road density areas will have higher population density.
        """
        boundary = map_data.boundary
        density_map = {}
        
        # Create grid for density calculation
        grid_size = 100  # 100m grid cells
        
        for x in np.arange(boundary.min_x, boundary.max_x, grid_size):
            for y in np.arange(boundary.min_y, boundary.max_y, grid_size):
                center_x = x + grid_size / 2
                center_y = y + grid_size / 2
                
                # Count roads within influence radius
                influence_radius = 200.0  # 200m influence radius
                road_count = 0
                total_road_length = 0
                
                for edge in map_data.edges.values():
                    from_node = map_data.nodes[edge.from_node]
                    to_node = map_data.nodes[edge.to_node]
                    
                    # Calculate distance from grid center to road
                    road_center_x = (from_node.x + to_node.x) / 2
                    road_center_y = (from_node.y + to_node.y) / 2
                    
                    distance = math.sqrt(
                        (center_x - road_center_x)**2 + (center_y - road_center_y)**2
                    )
                    
                    if distance < influence_radius:
                        road_count += 1
                        road_length = math.sqrt(
                            (to_node.x - from_node.x)**2 + (to_node.y - from_node.y)**2
                        )
                        total_road_length += road_length
                
                # Calculate density factor (0.0 to 1.0)
                density_factor = min(1.0, (road_count * 0.1) + (total_road_length / 10000))
                density_map[f"{center_x},{center_y}"] = density_factor
        
        return density_map
    
    def _get_density_factor(self, x: float, y: float, road_density_map: Dict[str, float], 
                          boundary) -> float:
        """
        Get density factor for a specific position by interpolating from density map.
        """
        grid_size = 100
        grid_x = int((x - boundary.min_x) // grid_size) * grid_size + boundary.min_x + 50
        grid_y = int((y - boundary.min_y) // grid_size) * grid_size + boundary.min_y + 50
        
        key = f"{grid_x},{grid_y}"
        return road_density_map.get(key, 0.2)  # Default low density
    
    def _generate_building(self, x: float, y: float, density_factor: float) -> Building:
        """
        Generate a single building at the specified position.
        """
        # Select building type based on weights and density
        building_type = self._select_building_type(density_factor)
        
        # Get building specifications
        specs = self.building_specs[building_type]
        
        # Generate building physical properties
        floors = random.randint(specs["min_floors"], specs["max_floors"])
        floor_height = 3.0  # Average 3m per floor
        height = floors * floor_height
        
        # Adjust height based on type specifications
        height = max(specs["min_height"], min(specs["max_height"], height))
        
        # Generate footprint area
        footprint_area = random.uniform(
            specs["footprint_range"][0], 
            specs["footprint_range"][1]
        )
        
        # Calculate population based on building type and density
        population = self._calculate_building_population(
            building_type, floors, density_factor, specs
        )
        
        # Calculate capacity (usually 1.2-1.5x current population)
        capacity = int(population * random.uniform(1.2, 1.5))
        
        building = Building(
            id=str(uuid.uuid4()),
            x=x,
            y=y,
            height=height,
            floors=floors,
            building_type=building_type,
            population=population,
            capacity=capacity,
            footprint_area=footprint_area
        )
        
        return building
    
    def _select_building_type(self, density_factor: float) -> str:
        """
        Select building type based on density factor and configured weights.
        Higher density areas favor commercial/mixed buildings.
        """
        weights = self.building_type_weights.copy()
        
        # Adjust weights based on density
        if density_factor > 0.7:  # High density area
            weights["commercial"] *= 1.5
            weights["mixed"] *= 1.3
            weights["residential"] *= 0.8
        elif density_factor < 0.3:  # Low density area
            weights["residential"] *= 1.4
            weights["industrial"] *= 1.2
            weights["commercial"] *= 0.6
        
        # Weighted random selection
        choices = list(weights.keys())
        weights_list = list(weights.values())
        
        return random.choices(choices, weights=weights_list)[0]
    
    def _calculate_building_population(self, building_type: str, floors: int, 
                                     density_factor: float, specs: Dict) -> int:
        """
        Calculate population for a building based on its properties.
        """
        pop_min, pop_max = specs["population_per_floor"]
        
        # Base population per floor
        base_pop_per_floor = random.uniform(pop_min, pop_max)
        
        # Apply density factor
        density_multiplier = 0.5 + (density_factor * 1.0)  # 0.5 to 1.5 multiplier
        
        # Calculate total population
        total_population = int(floors * base_pop_per_floor * density_multiplier)
        
        # Apply building type specific adjustments
        if building_type == "residential":
            total_population = max(1, total_population)  # At least 1 person
        elif building_type == "commercial":
            total_population = int(total_population * 0.3)  # Much lower resident population
        elif building_type == "industrial":
            total_population = int(total_population * 0.2)  # Very low resident population
        
        return max(0, total_population)
    
    def calculate_population_statistics(self, buildings: Dict[str, Building]) -> Dict[str, Any]:
        """
        Calculate population statistics for the generated buildings.
        """
        if not buildings:
            return {
                "total_population": 0,
                "total_buildings": 0,
                "total_capacity": 0,
                "average_population_per_building": 0,
                "population_by_type": {},
                "population_density_per_sqkm": 0
            }
        
        total_population = sum(b.population for b in buildings.values())
        total_capacity = sum(b.capacity for b in buildings.values())
        
        # Population by building type
        pop_by_type = {}
        for building in buildings.values():
            if building.building_type not in pop_by_type:
                pop_by_type[building.building_type] = 0
            pop_by_type[building.building_type] += building.population
        
        # Calculate area coverage (assuming 2km x 2km map)
        map_area_sqkm = 4.0  # 2km x 2km = 4 sq km
        population_density = total_population / map_area_sqkm
        
        return {
            "total_population": total_population,
            "total_buildings": len(buildings),
            "total_capacity": total_capacity,
            "average_population_per_building": total_population / len(buildings),
            "population_by_type": pop_by_type,
            "population_density_per_sqkm": population_density,
            "occupancy_rate": (total_population / total_capacity) * 100 if total_capacity > 0 else 0
        }