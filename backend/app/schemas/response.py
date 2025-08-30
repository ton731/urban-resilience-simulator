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


class WorldGenerationResponse(BaseModel):
    """Response schema for world generation API (WS-1.1)"""
    
    # Generation metadata
    generation_id: str = Field(description="Unique identifier for this world generation")
    generated_at: datetime = Field(description="Timestamp of generation")
    
    # Map data
    boundary: MapBoundaryResponse
    nodes: Dict[str, MapNodeResponse] = Field(description="Road network nodes indexed by ID")
    edges: Dict[str, RoadEdgeResponse] = Field(description="Road network edges indexed by ID")
    
    # Summary statistics  
    node_count: int = Field(description="Total number of nodes in the road network")
    edge_count: int = Field(description="Total number of road segments")
    main_road_count: int = Field(description="Number of main roads")
    secondary_road_count: int = Field(description="Number of secondary roads")
    
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
                "node_count": 45,
                "edge_count": 38,
                "main_road_count": 4,
                "secondary_road_count": 34,
                "generation_config": {
                    "map_size": [2000, 2000],
                    "road_density": 0.7
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