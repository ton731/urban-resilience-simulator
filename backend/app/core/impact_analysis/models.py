"""
Data models for Impact Analysis Module (IA-3.1: Ambulance Service Analysis)

Defines request/response schemas and core data structures for ambulance service
range analysis functionality.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from enum import Enum


class AnalysisMode(str, Enum):
    """Analysis modes for ambulance service analysis"""
    PRE_DISASTER = "pre_disaster"    # 災前分析
    POST_DISASTER = "post_disaster"  # 災後分析
    COMPARISON = "comparison"        # 災前災後對比


class ServiceGridCell(BaseModel):
    """Individual grid cell in the service accessibility map"""
    grid_id: str = Field(description="Unique identifier for this grid cell")
    center_x: float = Field(description="X coordinate of grid cell center")
    center_y: float = Field(description="Y coordinate of grid cell center")
    
    # Service time data
    service_time_seconds: Optional[float] = Field(
        default=None, 
        description="Time to reach nearest ambulance station (seconds). None if unreachable."
    )
    nearest_ambulance_station_id: Optional[str] = Field(
        default=None,
        description="ID of the nearest ambulance station"
    )
    
    # Grid properties
    grid_size_meters: float = Field(description="Size of grid cell in meters")
    
    # Color coding for visualization
    color_code: str = Field(description="Hex color code for visualization (#RRGGBB)")
    accessibility_level: str = Field(
        description="Accessibility level: excellent, good, fair, poor, unreachable"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "grid_25_30",
                "center_x": 1250.0,
                "center_y": 1500.0,
                "service_time_seconds": 420.0,
                "nearest_ambulance_station_id": "ambulance_001",
                "grid_size_meters": 50.0,
                "color_code": "#FFA500",
                "accessibility_level": "fair"
            }
        }


class AmbulanceServiceMetrics(BaseModel):
    """Key performance indicators for ambulance service analysis"""
    
    # Coverage metrics
    total_grid_cells: int = Field(description="Total number of grid cells analyzed")
    reachable_cells: int = Field(description="Number of cells reachable by ambulances")
    unreachable_cells: int = Field(description="Number of cells unreachable by ambulances")
    coverage_percentage: float = Field(description="Percentage of area covered by ambulance service")
    
    # Time metrics
    average_response_time_seconds: float = Field(description="Average response time across all reachable cells")
    median_response_time_seconds: float = Field(description="Median response time across all reachable cells")
    max_response_time_seconds: Optional[float] = Field(
        default=None, 
        description="Maximum response time found"
    )
    
    # Service level distribution
    excellent_service_cells: int = Field(description="Cells with service time ≤ 5 minutes")
    good_service_cells: int = Field(description="Cells with service time 5-10 minutes")
    fair_service_cells: int = Field(description="Cells with service time 10-15 minutes") 
    poor_service_cells: int = Field(description="Cells with service time > 15 minutes")
    
    # Geographic metrics
    service_blind_area_sqm: float = Field(description="Total area of service blind spots in square meters")
    total_analyzed_area_sqm: float = Field(description="Total analyzed area in square meters")
    
    # Ambulance station utilization
    ambulance_stations_analyzed: int = Field(description="Number of ambulance stations included in analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_grid_cells": 1600,
                "reachable_cells": 1450,
                "unreachable_cells": 150,
                "coverage_percentage": 90.625,
                "average_response_time_seconds": 485.7,
                "median_response_time_seconds": 420.0,
                "max_response_time_seconds": 1200.0,
                "excellent_service_cells": 320,
                "good_service_cells": 580,
                "fair_service_cells": 450,
                "poor_service_cells": 100,
                "service_blind_area_sqm": 375000.0,
                "total_analyzed_area_sqm": 2500000.0,
                "ambulance_stations_analyzed": 5
            }
        }


class ComparisonMetrics(BaseModel):
    """Metrics comparing pre-disaster and post-disaster analysis"""
    
    # Coverage changes
    coverage_change_percentage: float = Field(description="Change in coverage percentage")
    newly_unreachable_cells: int = Field(description="Cells that became unreachable post-disaster")
    
    # Time changes  
    average_time_increase_seconds: float = Field(description="Average increase in response time")
    median_time_increase_seconds: float = Field(description="Median increase in response time")
    
    # Service level changes
    service_degradation_cells: int = Field(description="Cells that experienced service level degradation")
    cells_improved: int = Field(description="Cells with improved service (rare but possible)")
    
    # Impact severity
    severely_impacted_cells: int = Field(description="Cells with >50% response time increase")
    moderately_impacted_cells: int = Field(description="Cells with 20-50% response time increase")
    lightly_impacted_cells: int = Field(description="Cells with <20% response time increase")
    
    class Config:
        json_schema_extra = {
            "example": {
                "coverage_change_percentage": -12.5,
                "newly_unreachable_cells": 200,
                "average_time_increase_seconds": 127.3,
                "median_time_increase_seconds": 95.0,
                "service_degradation_cells": 450,
                "cells_improved": 5,
                "severely_impacted_cells": 120,
                "moderately_impacted_cells": 180,
                "lightly_impacted_cells": 150
            }
        }


class AmbulanceServiceAnalysisRequest(BaseModel):
    """Request schema for ambulance service analysis API"""
    
    # Required parameters
    world_generation_id: str = Field(description="ID of the world generation to analyze")
    analysis_mode: AnalysisMode = Field(description="Analysis mode: pre_disaster, post_disaster, or comparison")
    
    # Grid configuration
    grid_size_meters: float = Field(
        default=50.0,
        description="Size of each grid cell in meters",
        ge=10.0,
        le=200.0
    )
    
    # Analysis parameters
    max_response_time_seconds: float = Field(
        default=1800.0,  # 30 minutes
        description="Maximum response time to consider (beyond this is unreachable)",
        gt=0
    )
    
    # Post-disaster analysis parameters
    simulation_id: Optional[str] = Field(
        default=None,
        description="Required for post_disaster and comparison modes: ID of disaster simulation"
    )
    
    # Vehicle configuration
    vehicle_type: str = Field(
        default="ambulance",
        description="Type of emergency vehicle for analysis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "world_generation_id": "gen_123456789",
                "analysis_mode": "comparison", 
                "grid_size_meters": 50.0,
                "max_response_time_seconds": 1800.0,
                "simulation_id": "sim_abc123def456",
                "vehicle_type": "ambulance"
            }
        }


class AmbulanceServiceAnalysisResponse(BaseModel):
    """Response schema for ambulance service analysis API"""
    
    # Analysis metadata
    analysis_id: str = Field(description="Unique identifier for this analysis")
    world_generation_id: str = Field(description="ID of the world generation analyzed")
    analysis_mode: AnalysisMode = Field(description="Analysis mode used")
    analyzed_at: datetime = Field(description="Timestamp when analysis was performed")
    
    # Grid data
    grid_cells: List[ServiceGridCell] = Field(description="List of all grid cells with their service data")
    
    # Pre-disaster analysis results
    pre_disaster_metrics: Optional[AmbulanceServiceMetrics] = Field(
        default=None,
        description="Metrics for pre-disaster analysis"
    )
    
    # Post-disaster analysis results (if applicable)
    post_disaster_metrics: Optional[AmbulanceServiceMetrics] = Field(
        default=None,
        description="Metrics for post-disaster analysis"
    )
    
    # Comparison results (if applicable)
    comparison_metrics: Optional[ComparisonMetrics] = Field(
        default=None,
        description="Comparison metrics between pre and post disaster"
    )
    
    # Analysis configuration
    analysis_config: Dict[str, Any] = Field(description="Configuration parameters used for this analysis")
    
    # Visualization data
    color_legend: Dict[str, str] = Field(
        description="Color coding legend for visualization",
        default={
            "excellent": "#00FF00",  # Green: ≤ 5 minutes
            "good": "#FFFF00",       # Yellow: 5-10 minutes  
            "fair": "#FFA500",       # Orange: 10-15 minutes
            "poor": "#FF0000",       # Red: > 15 minutes
            "unreachable": "#808080" # Gray: Unreachable
        }
    )
    
    # Map boundary for visualization
    map_boundary: Dict[str, float] = Field(description="Map boundary coordinates for visualization")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "analysis_xyz789abc123",
                "world_generation_id": "gen_123456789",
                "analysis_mode": "comparison",
                "analyzed_at": "2024-08-22T16:45:00Z",
                "grid_cells": [
                    {
                        "grid_id": "grid_25_30",
                        "center_x": 1250.0,
                        "center_y": 1500.0,
                        "service_time_seconds": 420.0,
                        "nearest_ambulance_station_id": "ambulance_001",
                        "grid_size_meters": 50.0,
                        "color_code": "#FFA500",
                        "accessibility_level": "fair"
                    }
                ],
                "pre_disaster_metrics": {
                    "total_grid_cells": 1600,
                    "reachable_cells": 1450,
                    "unreachable_cells": 150,
                    "coverage_percentage": 90.625,
                    "average_response_time_seconds": 485.7
                },
                "analysis_config": {
                    "grid_size_meters": 50.0,
                    "max_response_time_seconds": 1800.0,
                    "vehicle_type": "ambulance"
                }
            }
        }