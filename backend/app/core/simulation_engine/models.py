"""
Data models for the Simulation Engine module
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime


class VulnerabilityLevel(str, Enum):
    """Tree vulnerability levels as defined in PRD"""
    HIGH = "I"      # 80% collapse probability
    MEDIUM = "II"   # 50% collapse probability
    LOW = "III"     # 10% collapse probability


class VehicleType(str, Enum):
    """Vehicle types for pathfinding"""
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    PEDESTRIAN = "pedestrian"


class DisasterEvent(BaseModel):
    """Base class for disaster events"""
    event_id: str = Field(description="Unique identifier for the disaster event")
    event_type: str = Field(description="Type of disaster event")
    timestamp: datetime = Field(description="When the event occurred in simulation")
    location: Tuple[float, float] = Field(description="Geographic coordinates [x, y]")
    severity: float = Field(ge=0.0, le=1.0, description="Event severity (0.0 - 1.0)")


class TreeCollapseEvent(DisasterEvent):
    """Represents a tree collapse disaster event (SE-2.1)"""
    tree_id: str = Field(description="ID of the collapsed tree")
    vulnerability_level: VulnerabilityLevel = Field(description="Tree vulnerability level")
    collapse_angle: float = Field(ge=0.0, lt=360.0, description="Collapse direction in degrees (0-359)")
    tree_height: float = Field(gt=0.0, description="Tree height in meters")
    trunk_width: float = Field(gt=0.0, description="Tree trunk width in meters")
    blockage_polygon: List[Tuple[float, float]] = Field(
        description="Polygon coordinates representing blocked area"
    )
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = 'tree_collapse'
        super().__init__(**data)


class RoadObstruction(BaseModel):
    """Represents road obstruction caused by disaster events"""
    obstruction_id: str = Field(description="Unique identifier for the obstruction")
    road_edge_id: str = Field(description="ID of the affected road edge")
    obstruction_polygon: List[Tuple[float, float]] = Field(
        description="Polygon coordinates of the obstruction"
    )
    remaining_width: float = Field(ge=0.0, description="Remaining passable width in meters")
    blocked_percentage: float = Field(ge=0.0, le=100.0, description="Percentage of road blocked")
    caused_by_event: str = Field(description="ID of the disaster event that caused this obstruction")


class PathfindingRequest(BaseModel):
    """Request for pathfinding between two points"""
    start_point: Tuple[float, float] = Field(description="Starting coordinates [x, y]")
    end_point: Tuple[float, float] = Field(description="Destination coordinates [x, y]")
    vehicle_type: VehicleType = Field(description="Type of vehicle for path calculation")
    max_travel_time: Optional[float] = Field(
        default=None, 
        description="Maximum travel time in seconds (None for no limit)"
    )


class PathfindingResult(BaseModel):
    """Result of pathfinding calculation"""
    success: bool = Field(description="Whether a valid path was found")
    path_coordinates: List[Tuple[float, float]] = Field(
        description="List of coordinates forming the path"
    )
    path_node_ids: List[str] = Field(description="List of node IDs in the path")
    total_distance: float = Field(description="Total path distance in meters")
    estimated_travel_time: float = Field(description="Estimated travel time in seconds")
    vehicle_type: VehicleType = Field(description="Vehicle type used for calculation")
    blocked_roads: List[str] = Field(
        default=[], 
        description="List of road edge IDs that were blocked and avoided"
    )
    alternative_routes: Optional[int] = Field(
        default=None,
        description="Number of alternative routes found (if applicable)"
    )


class DisasterSimulationConfig(BaseModel):
    """Configuration for disaster simulation"""
    disaster_intensity: float = Field(
        ge=1.0, le=10.0,
        description="Overall disaster intensity parameter (1-10 scale)"
    )
    
    # Tree collapse probabilities by vulnerability level
    vulnerability_collapse_rates: Dict[str, float] = Field(
        default={
            "I": 0.8,    # High risk: 80% collapse probability
            "II": 0.5,   # Medium risk: 50% collapse probability  
            "III": 0.1   # Low risk: 10% collapse probability
        },
        description="Collapse probability by vulnerability level"
    )
    
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible simulations"
    )
    
    include_minor_debris: bool = Field(
        default=False,
        description="Whether to simulate minor debris (branches, etc.)"
    )


class DisasterSimulationResult(BaseModel):
    """Result of disaster simulation"""
    simulation_id: str = Field(description="Unique identifier for this simulation run")
    simulated_at: datetime = Field(description="Timestamp when simulation was performed")
    disaster_events: List[TreeCollapseEvent] = Field(description="List of all disaster events")
    road_obstructions: List[RoadObstruction] = Field(description="List of road obstructions")
    
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
    
    simulation_config: DisasterSimulationConfig = Field(
        description="Configuration used for this simulation"
    )


class VehicleConfig(BaseModel):
    """Configuration for different vehicle types"""
    vehicle_type: VehicleType
    width: float = Field(gt=0.0, description="Vehicle width in meters")
    length: float = Field(gt=0.0, description="Vehicle length in meters")
    max_speed: float = Field(gt=0.0, description="Maximum speed in km/h")
    can_use_sidewalk: bool = Field(default=False, description="Whether vehicle can use sidewalks")
    minimum_road_width: float = Field(gt=0.0, description="Minimum road width required in meters")


# Default vehicle configurations
DEFAULT_VEHICLE_CONFIGS = {
    VehicleType.PEDESTRIAN: VehicleConfig(
        vehicle_type=VehicleType.PEDESTRIAN,
        width=0.6,
        length=0.6,
        max_speed=5.0,  # km/h
        can_use_sidewalk=True,
        minimum_road_width=0.8
    ),
    VehicleType.MOTORCYCLE: VehicleConfig(
        vehicle_type=VehicleType.MOTORCYCLE,
        width=0.8,
        length=2.0,
        max_speed=60.0,
        can_use_sidewalk=False,
        minimum_road_width=1.2
    ),
    VehicleType.CAR: VehicleConfig(
        vehicle_type=VehicleType.CAR,
        width=1.8,
        length=4.5,
        max_speed=50.0,
        can_use_sidewalk=False,
        minimum_road_width=2.2
    ),
    VehicleType.AMBULANCE: VehicleConfig(
        vehicle_type=VehicleType.AMBULANCE,
        width=2.5,
        length=7.0,
        max_speed=80.0,
        can_use_sidewalk=False,
        minimum_road_width=3.0
    ),
    VehicleType.FIRE_TRUCK: VehicleConfig(
        vehicle_type=VehicleType.FIRE_TRUCK,
        width=3.0,
        length=12.0,
        max_speed=60.0,
        can_use_sidewalk=False,
        minimum_road_width=3.5
    )
}