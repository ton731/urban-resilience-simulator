from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class MapBoundaryResponse(BaseModel):
    """Map boundary information"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    width: float
    height: float


class MapNodeResponse(BaseModel):
    """Road network node information"""
    id: str
    x: float
    y: float
    type: str = Field(description="Node type: intersection, facility")


class RoadEdgeResponse(BaseModel):
    """Road network edge information"""
    id: str
    from_node: str
    to_node: str
    width: float = Field(description="Road width in meters")
    lanes: int
    is_bidirectional: bool
    road_type: str = Field(description="Road type: main, secondary")
    speed_limit: float = Field(description="Speed limit in km/h")


class TreeResponse(BaseModel):
    """Tree object information (WS-1.2)"""
    id: str
    x: float
    y: float
    vulnerability_level: str = Field(description="Vulnerability level: I (high), II (medium), III (low)")
    height: float = Field(description="Tree height in meters")
    trunk_width: float = Field(description="Tree trunk width in meters")


class FacilityResponse(BaseModel):
    """Facility object information (WS-1.3)"""
    id: str
    x: float
    y: float
    facility_type: str = Field(description="Facility type: ambulance_station, shelter")
    node_id: str = Field(description="ID of the road network node where facility is located")
    capacity: Optional[int] = Field(default=None, description="Capacity for shelters")
    name: Optional[str] = Field(default=None, description="Facility name")


class BuildingResponse(BaseModel):
    """Building object information (WS-1.5)"""
    id: str
    x: float
    y: float
    height: float = Field(description="Building height in meters")
    floors: int = Field(description="Number of floors")
    building_type: str = Field(description="Building type: residential, commercial, mixed, industrial")
    population: int = Field(description="Current population in the building")
    capacity: int = Field(description="Maximum population capacity")
    footprint_area: float = Field(description="Building footprint area in square meters")


class WorldGenerationResponse(BaseModel):
    """Response schema for world generation API (WS-1.1 + WS-1.2 + WS-1.3 + WS-1.5)"""
    
    # Generation metadata
    generation_id: str = Field(description="Unique identifier for this world generation")
    generated_at: datetime = Field(description="Timestamp of generation")
    
    # Map data
    boundary: MapBoundaryResponse
    nodes: Dict[str, MapNodeResponse] = Field(description="Road network nodes indexed by ID")
    edges: Dict[str, RoadEdgeResponse] = Field(description="Road network edges indexed by ID")
    trees: Dict[str, TreeResponse] = Field(description="Trees indexed by ID (WS-1.2)")
    facilities: Dict[str, FacilityResponse] = Field(description="Facilities indexed by ID (WS-1.3)")
    buildings: Dict[str, BuildingResponse] = Field(description="Buildings indexed by ID (WS-1.5)")
    
    # Summary statistics  
    node_count: int = Field(description="Total number of nodes in the road network")
    edge_count: int = Field(description="Total number of road segments")
    tree_count: int = Field(description="Total number of trees")
    facility_count: int = Field(description="Total number of facilities")
    building_count: int = Field(description="Total number of buildings")
    main_road_count: int = Field(description="Number of main roads")
    secondary_road_count: int = Field(description="Number of secondary roads")
    
    # Tree statistics (WS-1.2)
    tree_stats: Optional[Dict[str, Any]] = Field(description="Tree generation statistics")
    
    # Facility statistics (WS-1.3)
    facility_stats: Optional[Dict[str, Any]] = Field(description="Facility generation statistics")
    
    # Population and building statistics (WS-1.5)
    population_stats: Optional[Dict[str, Any]] = Field(description="Population and building statistics")
    
    # Generation parameters used
    generation_config: Dict[str, Any] = Field(description="Configuration parameters used for generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "generation_id": "gen_123456789",
                "generated_at": "2024-08-22T10:30:00Z",
                "boundary": {
                    "min_x": 0.0,
                    "min_y": 0.0,
                    "max_x": 2000.0,
                    "max_y": 2000.0,
                    "width": 2000.0,
                    "height": 2000.0
                },
                "nodes": {
                    "node_001": {
                        "id": "node_001",
                        "x": 500.0,
                        "y": 500.0,
                        "type": "intersection"
                    }
                },
                "edges": {
                    "edge_001": {
                        "id": "edge_001",
                        "from_node": "node_001",
                        "to_node": "node_002",
                        "width": 6.0,
                        "lanes": 2,
                        "is_bidirectional": True,
                        "road_type": "secondary",
                        "speed_limit": 40.0
                    }
                },
                "trees": {
                    "tree_001": {
                        "id": "tree_001",
                        "x": 520.5,
                        "y": 485.2,
                        "vulnerability_level": "II",
                        "height": 12.5,
                        "trunk_width": 0.8
                    }
                },
                "buildings": {
                    "building_001": {
                        "id": "building_001",
                        "x": 800.0,
                        "y": 600.0,
                        "height": 18.0,
                        "floors": 6,
                        "building_type": "residential",
                        "population": 24,
                        "capacity": 30,
                        "footprint_area": 250.0
                    }
                },
                "node_count": 45,
                "edge_count": 38,
                "tree_count": 156,
                "building_count": 89,
                "main_road_count": 4,
                "secondary_road_count": 34,
                "tree_stats": {
                    "total_trees": 156,
                    "vulnerability_distribution": {"I": 15, "II": 47, "III": 94},
                    "average_height": 10.8,
                    "average_trunk_width": 0.6
                },
                "population_stats": {
                    "total_population": 2340,
                    "total_buildings": 89,
                    "total_capacity": 3120,
                    "average_population_per_building": 26.3,
                    "population_by_type": {
                        "residential": 1890,
                        "commercial": 156,
                        "mixed": 246,
                        "industrial": 48
                    },
                    "population_density_per_sqkm": 585.0,
                    "occupancy_rate": 75.0
                },
                "generation_config": {
                    "map_size": [2000, 2000],
                    "road_density": 0.7,
                    "include_trees": True,
                    "include_buildings": True,
                    "building_density": 0.3
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    code: Optional[str] = Field(default=None, description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid map size",
                "detail": "Map size must be between 500 and 10000 meters",
                "code": "INVALID_MAP_SIZE"
            }
        }


class TreeCollapseEventResponse(BaseModel):
    """Response model for tree collapse events (SE-2.1)"""
    event_id: str = Field(description="Unique identifier for the disaster event")
    tree_id: str = Field(description="ID of the collapsed tree")
    location: Tuple[float, float] = Field(description="Geographic coordinates [x, y]")
    vulnerability_level: str = Field(description="Tree vulnerability level (I/II/III)")
    collapse_angle: float = Field(description="Collapse direction in degrees (0-359)")
    tree_height: float = Field(description="Tree height in meters")
    trunk_width: float = Field(description="Tree trunk width in meters")
    blockage_polygon: List[Tuple[float, float]] = Field(description="Polygon coordinates representing blocked area")
    severity: float = Field(description="Event severity (0.0-1.0)")
    timestamp: datetime = Field(description="When the event occurred in simulation")


class RoadObstructionResponse(BaseModel):
    """Response model for road obstructions"""
    obstruction_id: str = Field(description="Unique identifier for the obstruction")
    road_edge_id: str = Field(description="ID of the affected road edge")
    obstruction_polygon: List[Tuple[float, float]] = Field(description="Polygon coordinates of the obstruction")
    remaining_width: float = Field(description="Remaining passable width in meters")
    blocked_percentage: float = Field(description="Percentage of road blocked (0-100)")
    caused_by_event: str = Field(description="ID of the disaster event that caused this obstruction")


class DisasterSimulationResponse(BaseModel):
    """Response schema for disaster simulation API (SE-2.1)"""
    
    # Simulation metadata
    simulation_id: str = Field(description="Unique identifier for this simulation run")
    world_generation_id: str = Field(description="ID of the world that was simulated")
    simulated_at: datetime = Field(description="Timestamp when simulation was performed")
    
    # Disaster events and effects
    disaster_events: List[TreeCollapseEventResponse] = Field(description="List of all disaster events")
    road_obstructions: List[RoadObstructionResponse] = Field(description="List of road obstructions")
    
    # Summary statistics
    total_trees_affected: int = Field(description="Total number of trees that collapsed")
    total_roads_affected: int = Field(description="Total number of road segments affected")
    total_blocked_road_length: float = Field(description="Total length of blocked roads in meters")
    
    trees_affected_by_level: Dict[str, int] = Field(
        description="Number of affected trees by vulnerability level"
    )
    
    average_road_blockage_percentage: float = Field(
        description="Average percentage of road blockage across affected roads"
    )
    
    # Configuration used for simulation
    simulation_config: Dict[str, Any] = Field(description="Configuration used for this simulation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_abc123def456",
                "world_generation_id": "gen_123456789",
                "simulated_at": "2024-08-22T14:30:00Z",
                "disaster_events": [
                    {
                        "event_id": "collapse_xy123",
                        "tree_id": "tree_001",
                        "location": [520.5, 485.2],
                        "vulnerability_level": "II",
                        "collapse_angle": 45.0,
                        "tree_height": 12.5,
                        "trunk_width": 0.8,
                        "blockage_polygon": [[520.5, 485.2], [530.0, 495.0], [525.0, 500.0], [515.5, 490.2]],
                        "severity": 0.6,
                        "timestamp": "2024-08-22T14:30:05Z"
                    }
                ],
                "road_obstructions": [
                    {
                        "obstruction_id": "obs_def789",
                        "road_edge_id": "edge_001",
                        "obstruction_polygon": [[520.0, 485.0], [525.0, 490.0], [522.0, 492.0], [517.0, 487.0]],
                        "remaining_width": 3.2,
                        "blocked_percentage": 46.7,
                        "caused_by_event": "collapse_xy123"
                    }
                ],
                "total_trees_affected": 23,
                "total_roads_affected": 8,
                "total_blocked_road_length": 450.5,
                "trees_affected_by_level": {"I": 8, "II": 12, "III": 3},
                "average_road_blockage_percentage": 35.2,
                "simulation_config": {
                    "disaster_intensity": 7.5,
                    "vulnerability_collapse_rates": {"I": 0.8, "II": 0.5, "III": 0.1},
                    "random_seed": 42
                }
            }
        }


class PathfindingResponse(BaseModel):
    """Response schema for pathfinding API (SE-2.2)"""
    
    # Path result
    success: bool = Field(description="Whether a valid path was found")
    path_coordinates: List[Tuple[float, float]] = Field(description="List of coordinates forming the path")
    path_node_ids: List[str] = Field(description="List of node IDs in the path")
    is_partial_path: bool = Field(default=False, description="True if this is a partial path (destination not reachable)")
    partial_path_reason: Optional[str] = Field(default=None, description="Reason why only partial path was found")
    
    # Path metrics
    total_distance: float = Field(description="Total path distance in meters")
    estimated_travel_time: float = Field(description="Estimated travel time in seconds")
    
    # Context information
    vehicle_type: str = Field(description="Vehicle type used for calculation")
    world_generation_id: str = Field(description="ID of the world used")
    simulation_id: Optional[str] = Field(default=None, description="ID of the simulation used (if post-disaster)")
    
    # Path analysis
    blocked_roads: List[str] = Field(description="List of road edge IDs that were blocked and avoided")
    alternative_routes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of alternative routes with their details"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "path_coordinates": [[500.0, 500.0], [600.0, 650.0], [1200.0, 1100.0], [1500.0, 1200.0]],
                "path_node_ids": ["node_001", "node_015", "node_087", "node_134"],
                "total_distance": 1247.8,
                "estimated_travel_time": 156.2,
                "vehicle_type": "ambulance",
                "world_generation_id": "gen_123456789",
                "simulation_id": "sim_987654321",
                "blocked_roads": ["edge_023", "edge_045"],
                "alternative_routes": 2
            }
        }


class ServiceAreaResponse(BaseModel):
    """Response schema for service area calculation API"""
    
    # Service area data
    service_area_coordinates: List[Tuple[float, float]] = Field(
        description="Coordinates forming the boundary of the service area"
    )
    
    reachable_nodes: List[str] = Field(
        description="List of node IDs within the service area"
    )
    
    # Multiple isochrones if requested
    isochrones: Optional[Dict[str, List[Tuple[float, float]]]] = Field(
        default=None,
        description="Multiple service areas by time interval"
    )
    
    # Area metrics
    area_coverage_sqm: float = Field(description="Service area coverage in square meters")
    max_travel_time_used: float = Field(description="Maximum travel time used for calculation")
    
    # Context information
    center_point: Tuple[float, float] = Field(description="Center point used for calculation")
    vehicle_type: str = Field(description="Vehicle type used for calculation")
    world_generation_id: str = Field(description="ID of the world used")
    simulation_id: Optional[str] = Field(default=None, description="ID of the simulation used (if post-disaster)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_area_coordinates": [[950.0, 950.0], [1050.0, 950.0], [1050.0, 1050.0], [950.0, 1050.0]],
                "reachable_nodes": ["node_001", "node_002", "node_015", "node_087"],
                "isochrones": {
                    "300": [[980.0, 980.0], [1020.0, 980.0], [1020.0, 1020.0], [980.0, 1020.0]],
                    "600": [[960.0, 960.0], [1040.0, 960.0], [1040.0, 1040.0], [960.0, 1040.0]],
                    "900": [[950.0, 950.0], [1050.0, 950.0], [1050.0, 1050.0], [950.0, 1050.0]]
                },
                "area_coverage_sqm": 10000.0,
                "max_travel_time_used": 900.0,
                "center_point": [1000.0, 1000.0],
                "vehicle_type": "ambulance",
                "world_generation_id": "gen_123456789",
                "simulation_id": "sim_987654321"
            }
        }