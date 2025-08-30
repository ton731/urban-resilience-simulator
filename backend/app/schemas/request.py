from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class WorldGenerationRequest(BaseModel):
    """Request schema for world generation API (WS-1.1 + WS-1.2)"""
    
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
                "config_override": {
                    "main_road_width": 12.0,
                    "secondary_road_width": 6.0
                }
            }
        }