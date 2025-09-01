"""
Impact Analysis Module (IA)

This module implements the Impact Analysis functionality as specified in the PRD.
Transforms simulation results into meaningful high-level indicators and metrics.

Current implementations:
- IA-3.1: Ambulance Service Range Analysis
"""

from .ambulance_service_analyzer import AmbulanceServiceAnalyzer
from .models import (
    AmbulanceServiceAnalysisRequest,
    AmbulanceServiceAnalysisResponse,
    ServiceGridCell,
    AmbulanceServiceMetrics
)

__all__ = [
    "AmbulanceServiceAnalyzer",
    "AmbulanceServiceAnalysisRequest", 
    "AmbulanceServiceAnalysisResponse",
    "ServiceGridCell",
    "AmbulanceServiceMetrics"
]