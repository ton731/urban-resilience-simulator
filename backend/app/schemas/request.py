from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple


class WorldGenerationRequest(BaseModel):
    """Request schema for world generation API (WS-1.1 + WS-1.2 + WS-1.3 + WS-1.5)"""
    
    # Map configuration
    map_size: List[int] = Field(
        default=[2000, 2000],
        description="Map dimensions in meters [width, height]",
        min_items=2,
        max_items=2
    )
    
    road_density: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Road network density factor (0.1-1.0)"
    )
    
    main_road_count: int = Field(
        default=4,
        ge=2,
        le=10,
        description="Number of main roads (major arteries)"
    )
    
    secondary_road_density: float = Field(
        default=0.5,
        ge=0.1,
        le=1.0,
        description="Secondary road generation probability (0.1-1.0)"
    )
    
    # Tree generation configuration (WS-1.2)
    include_trees: bool = Field(
        default=True,
        description="Whether to generate trees along roads (WS-1.2)"
    )
    
    tree_spacing: float = Field(
        default=25.0,
        ge=10.0,
        le=100.0,
        description="Average spacing between trees in meters"
    )
    
    tree_max_offset: float = Field(
        default=8.0,
        ge=2.0,
        le=20.0,
        description="Maximum random offset from road edge in meters"
    )
    
    vulnerability_distribution: Optional[Dict[str, float]] = Field(
        default=None,
        description="Tree vulnerability level distribution (I/II/III)"
    )
    
    # Facility generation configuration (WS-1.3)
    include_facilities: Optional[bool] = Field(
        default=True,
        description="Whether to generate facilities (ambulance stations, shelters)"
    )
    
    # Building generation configuration (WS-1.5)
    include_buildings: Optional[bool] = Field(
        default=True,
        description="Whether to generate buildings and population (WS-1.5)"
    )
    
    building_density: Optional[float] = Field(
        default=0.3,
        ge=0.1,
        le=1.0,
        description="Building density factor (buildings per 100m²)"
    )
    
    # Additional configuration options
    config_override: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional configuration parameters to override defaults"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_size": [2000, 2000],
                "road_density": 0.7,
                "main_road_count": 4,
                "secondary_road_density": 0.5,
                "include_trees": True,
                "tree_spacing": 25.0,
                "tree_max_offset": 8.0,
                "vulnerability_distribution": {
                    "I": 0.1,
                    "II": 0.3,
                    "III": 0.6
                },
                "include_facilities": True,
                "include_buildings": True,
                "building_density": 0.3,
                "config_override": {
                    "main_road_width": 12.0,
                    "secondary_road_width": 6.0
                }
            }
        }


class DisasterSimulationRequest(BaseModel):
    """Request schema for disaster simulation API (SE-2.1)"""
    
    # World state input (from World Synthesizer)
    world_generation_id: str = Field(
        description="ID of the generated world to simulate disasters on"
    )
    
    # Disaster configuration
    disaster_intensity: float = Field(
        ge=1.0, 
        le=10.0,
        description="Overall disaster intensity parameter (1-10 scale)"
    )
    
    # Optional custom vulnerability collapse rates
    vulnerability_collapse_rates: Optional[Dict[str, float]] = Field(
        default=None,
        description="Custom collapse probability by vulnerability level (I/II/III)"
    )
    
    # Simulation settings
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible simulations"
    )
    
    include_minor_debris: bool = Field(
        default=False,
        description="Whether to simulate minor debris effects"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "world_generation_id": "gen_123456789",
                "disaster_intensity": 7.5,
                "vulnerability_collapse_rates": {
                    "I": 0.8,
                    "II": 0.5, 
                    "III": 0.1
                },
                "random_seed": 42,
                "include_minor_debris": False
            }
        }


class PathfindingRequest(BaseModel):
    """Request schema for pathfinding API (SE-2.2)"""
    
    # World and simulation context
    world_generation_id: str = Field(
        description="ID of the generated world"
    )
    
    simulation_id: Optional[str] = Field(
        default=None,
        description="Optional simulation ID for post-disaster pathfinding"
    )
    
    # Path parameters
    start_point: Tuple[float, float] = Field(
        description="Starting coordinates [x, y]"
    )
    
    end_point: Tuple[float, float] = Field(
        description="Destination coordinates [x, y]"
    )
    
    # Vehicle configuration
    vehicle_type: str = Field(
        default="car",
        description="Vehicle type: pedestrian, motorcycle, car, ambulance, fire_truck"
    )
    
    # Optional constraints
    max_travel_time: Optional[float] = Field(
        default=None,
        description="Maximum travel time in seconds (None for no limit)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "world_generation_id": "gen_123456789",
                "simulation_id": "sim_987654321",
                "start_point": [500.0, 500.0],
                "end_point": [1500.0, 1200.0],
                "vehicle_type": "ambulance",
                "max_travel_time": 900.0
            }
        }


class ServiceAreaRequest(BaseModel):
    """Request schema for service area calculation API"""
    
    # World and simulation context  
    world_generation_id: str = Field(
        description="ID of the generated world"
    )
    
    simulation_id: Optional[str] = Field(
        default=None,
        description="Optional simulation ID for post-disaster analysis"
    )
    
    # Service area parameters
    center_point: Tuple[float, float] = Field(
        description="Center coordinates for service area [x, y]"
    )
    
    vehicle_type: str = Field(
        default="ambulance",
        description="Vehicle type for service area calculation"
    )
    
    max_travel_time: float = Field(
        gt=0.0,
        description="Maximum travel time in seconds"
    )
    
    time_intervals: Optional[List[float]] = Field(
        default=None,
        description="Time intervals for multiple isochrones (e.g., [300, 600, 900] for 5, 10, 15 minutes)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "world_generation_id": "gen_123456789", 
                "simulation_id": "sim_987654321",
                "center_point": [1000.0, 1000.0],
                "vehicle_type": "ambulance",
                "max_travel_time": 900.0,
                "time_intervals": [300.0, 600.0, 900.0]
            }
        }