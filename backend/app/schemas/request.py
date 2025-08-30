from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class WorldGenerationRequest(BaseModel):
    """Request schema for world generation API (WS-1.1)"""
    
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
                "config_override": {
                    "main_road_width": 12.0,
                    "secondary_road_width": 6.0
                }
            }
        }