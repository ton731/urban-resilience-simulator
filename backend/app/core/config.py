from pydantic_settings import BaseSettings
from typing import List, Dict


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Urban Resilience Simulator"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]  # In production, specify exact origins
    
    # World Generation Defaults
    DEFAULT_MAP_SIZE: List[int] = [2000, 2000]
    DEFAULT_ROAD_DENSITY: float = 0.6
    DEFAULT_TREE_COUNT: int = 8000
    DEFAULT_AMBULANCE_STATIONS: int = 5
    DEFAULT_SHELTERS: int = 10
    
    # Road generation defaults
    DEFAULT_MAIN_ROAD_COUNT: int = 6
    DEFAULT_SECONDARY_ROAD_DENSITY: float = 0.5
    DEFAULT_MAIN_ROAD_WIDTH: float = 12.0
    DEFAULT_SECONDARY_ROAD_WIDTH: float = 6.0
    DEFAULT_MAIN_ROAD_LANES: int = 4
    DEFAULT_SECONDARY_ROAD_LANES: int = 2
    DEFAULT_MAIN_ROAD_SPEED_LIMIT: float = 70.0
    DEFAULT_SECONDARY_ROAD_SPEED_LIMIT: float = 40.0
    
    # Tree generation defaults (WS-1.2)
    DEFAULT_INCLUDE_TREES: bool = True
    DEFAULT_TREE_SPACING: float = 40.0  # meters
    DEFAULT_TREE_MAX_OFFSET: float = 8.0  # meters
    DEFAULT_TREE_ROAD_BUFFER: float = 3.0  # meters
    
    # Tree physical properties
    DEFAULT_TREE_HEIGHT_RANGE: List[float] = [4.0, 25.0]  # meters
    DEFAULT_TREE_TRUNK_WIDTH_RANGE: List[float] = [0.2, 1.5]  # meters
    
    # Tree vulnerability distribution
    TREE_LEVEL_I_RATIO: float = 0.1  # High risk
    TREE_LEVEL_II_RATIO: float = 0.3  # Medium risk
    TREE_LEVEL_III_RATIO: float = 0.6  # Low risk
    
    # Facility generation defaults (WS-1.3)
    DEFAULT_INCLUDE_FACILITIES: bool = True
    DEFAULT_AMBULANCE_STATIONS_COUNT: int = 3
    DEFAULT_SHELTERS_COUNT: int = 8
    DEFAULT_SHELTER_CAPACITY_RANGE: List[int] = [100, 1000]
    
    # Building generation defaults (WS-1.5)
    DEFAULT_INCLUDE_BUILDINGS: bool = True
    DEFAULT_BUILDING_DENSITY: float = 0.3
    DEFAULT_MIN_BUILDING_DISTANCE: float = 25.0
    DEFAULT_ROAD_BUFFER_DISTANCE: float = 15.0
    DEFAULT_BUILDING_TYPE_WEIGHTS: Dict[str, float] = {
        "residential": 0.6,
        "commercial": 0.2,
        "mixed": 0.15,
        "industrial": 0.05
    }
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()