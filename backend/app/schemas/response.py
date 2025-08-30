from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
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


class WorldGenerationResponse(BaseModel):
    """Response schema for world generation API (WS-1.1 + WS-1.2 + WS-1.3)"""
    
    # Generation metadata
    generation_id: str = Field(description="Unique identifier for this world generation")
    generated_at: datetime = Field(description="Timestamp of generation")
    
    # Map data
    boundary: MapBoundaryResponse
    nodes: Dict[str, MapNodeResponse] = Field(description="Road network nodes indexed by ID")
    edges: Dict[str, RoadEdgeResponse] = Field(description="Road network edges indexed by ID")
    trees: Dict[str, TreeResponse] = Field(description="Trees indexed by ID (WS-1.2)")
    facilities: Dict[str, FacilityResponse] = Field(description="Facilities indexed by ID (WS-1.3)")
    
    # Summary statistics  
    node_count: int = Field(description="Total number of nodes in the road network")
    edge_count: int = Field(description="Total number of road segments")
    tree_count: int = Field(description="Total number of trees")
    facility_count: int = Field(description="Total number of facilities")
    main_road_count: int = Field(description="Number of main roads")
    secondary_road_count: int = Field(description="Number of secondary roads")
    
    # Tree statistics (WS-1.2)
    tree_stats: Optional[Dict[str, Any]] = Field(description="Tree generation statistics")
    
    # Facility statistics (WS-1.3)
    facility_stats: Optional[Dict[str, Any]] = Field(description="Facility generation statistics")
    
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
                "node_count": 45,
                "edge_count": 38,
                "tree_count": 156,
                "main_road_count": 4,
                "secondary_road_count": 34,
                "tree_stats": {
                    "total_trees": 156,
                    "vulnerability_distribution": {"I": 15, "II": 47, "III": 94},
                    "average_height": 10.8,
                    "average_trunk_width": 0.6
                },
                "generation_config": {
                    "map_size": [2000, 2000],
                    "road_density": 0.7,
                    "include_trees": True
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