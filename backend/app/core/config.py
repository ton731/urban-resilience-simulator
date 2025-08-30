from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Urban Resilience Simulator"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]  # In production, specify exact origins
    
    # World Generation Defaults
    DEFAULT_MAP_SIZE: List[int] = [2000, 2000]
    DEFAULT_ROAD_DENSITY: float = 0.7
    DEFAULT_TREE_COUNT: int = 8000
    DEFAULT_AMBULANCE_STATIONS: int = 5
    DEFAULT_SHELTERS: int = 10
    
    # Tree vulnerability distribution
    TREE_LEVEL_I_RATIO: float = 0.1  # High risk
    TREE_LEVEL_II_RATIO: float = 0.3  # Medium risk
    TREE_LEVEL_III_RATIO: float = 0.6  # Low risk
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()