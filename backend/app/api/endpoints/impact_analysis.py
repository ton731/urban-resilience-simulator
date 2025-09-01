"""
Impact Analysis API Endpoints

Provides REST API endpoints for impact analysis functionality including
ambulance service range analysis (IA-3.1).
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from ...core.impact_analysis import AmbulanceServiceAnalyzer
from ...core.impact_analysis.models import (
    AmbulanceServiceAnalysisRequest,
    AmbulanceServiceAnalysisResponse
)

# Import data access functions from simulation module
from .simulation import _world_states, _simulation_results

router = APIRouter(prefix="/impact", tags=["Impact Analysis"])

# Global storage for analysis results (consistent with simulation.py pattern)
_analysis_results: Dict[str, Dict[str, Any]] = {}


@router.post("/ambulance-service-analysis", response_model=AmbulanceServiceAnalysisResponse)
async def analyze_ambulance_service(request: AmbulanceServiceAnalysisRequest) -> AmbulanceServiceAnalysisResponse:
    """
    Perform ambulance service range analysis (IA-3.1).
    
    Generates a grid-based service accessibility map showing ambulance response times
    across the entire map area. Supports pre-disaster, post-disaster, and comparison analysis.
    
    Args:
        request: Analysis request with configuration parameters
        
    Returns:
        Complete analysis results with grid data, metrics, and visualization information
        
    Raises:
        HTTPException: 
            - 404 if world generation data not found
            - 404 if simulation data not found (for post-disaster/comparison modes)
            - 400 for invalid request parameters
            - 500 for internal processing errors
    """
    try:
        print(f"\n📡 收到救護車服務分析請求")
        print(f"🌍 世界生成ID: {request.world_generation_id}")
        print(f"📊 分析模式: {request.analysis_mode.value}")
        print(f"🔧 網格大小: {request.grid_size_meters}m")
        print("=" * 60)
        
        # Validate and get world generation data
        if request.world_generation_id not in _world_states:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"World generation {request.world_generation_id} not found"
            )
        
        world_data = _world_states[request.world_generation_id]
        
        print(f"✅ 找到世界生成資料")
        print(f"   - 道路節點: {len(world_data['nodes'])}")
        print(f"   - 道路邊: {len(world_data['edges'])}")
        print(f"   - 設施數量: {len(world_data['facilities'])}")
        
        # Count ambulance stations
        ambulance_stations = [
            f for f in world_data['facilities'].values() 
            if f.get('facility_type') == 'ambulance_station'
        ]
        
        if not ambulance_stations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ambulance stations found in the world data"
            )
            
        print(f"   - 救護車站: {len(ambulance_stations)}")
        print()
        
        # Get simulation data for post-disaster analysis
        simulation_data = None
        if request.analysis_mode in ["post_disaster", "comparison"]:
            if not request.simulation_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Simulation ID required for post-disaster and comparison analysis"
                )
            
            if request.simulation_id not in _simulation_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Simulation {request.simulation_id} not found"
                )
                
            # Get simulation data from stored result
            sim_data = _simulation_results[request.simulation_id]
            simulation_result = sim_data["result"]
            
            # Extract disaster events and road obstructions
            simulation_data = {
                "disaster_events": simulation_result.disaster_events,
                "road_obstructions": simulation_result.road_obstructions
            }
                
            print(f"✅ 找到災害模擬資料")
            print(f"   - 模擬ID: {request.simulation_id}")
            print(f"   - 災害事件: {len(simulation_data.get('disaster_events', []))}")
            print(f"   - 道路阻塞: {len(simulation_data.get('road_obstructions', []))}")
            print()
        
        # Validate request parameters
        if request.grid_size_meters < 10 or request.grid_size_meters > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grid size must be between 10 and 200 meters"
            )
            
        if request.max_response_time_seconds <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum response time must be positive"
            )
        
        # Create analyzer and perform analysis
        analyzer = AmbulanceServiceAnalyzer()
        
        print(f"🚀 開始執行分析...")
        result = await analyzer.analyze_ambulance_service(
            request=request,
            world_data=world_data,
            simulation_data=simulation_data
        )
        
        # Store analysis result for future reference
        _analysis_results[result.analysis_id] = {
            "type": "ambulance_service_analysis",
            "request": request.dict(),
            "result": result.dict(),
            "world_generation_id": request.world_generation_id,
            "simulation_id": request.simulation_id
        }
        
        print(f"💾 分析結果已儲存，ID: {result.analysis_id}")
        print(f"🎉 API 請求處理完成!")
        print("=" * 60)
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except ValueError as e:
        print(f"❌ 參數驗證錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        print(f"❌ 內部處理錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during ambulance service analysis"
        )


@router.get("/ambulance-service-analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str) -> Dict[str, Any]:
    """
    Retrieve a previously completed ambulance service analysis result.
    
    Args:
        analysis_id: Unique identifier of the analysis
        
    Returns:
        Stored analysis result
        
    Raises:
        HTTPException: 404 if analysis not found
    """
    try:
        if analysis_id not in _analysis_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )
            
        analysis_data = _analysis_results[analysis_id]
        
        if analysis_data.get("type") != "ambulance_service_analysis":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} is not an ambulance service analysis"
            )
        
        return analysis_data["result"]
        
    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving analysis result"
        )


@router.delete("/ambulance-service-analysis/{analysis_id}")
async def delete_analysis_result(analysis_id: str) -> Dict[str, str]:
    """
    Delete a stored ambulance service analysis result.
    
    Args:
        analysis_id: Unique identifier of the analysis to delete
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: 404 if analysis not found
    """
    try:
        if analysis_id not in _analysis_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )
        
        del _analysis_results[analysis_id]
        
        return {"message": f"Analysis {analysis_id} deleted successfully"}
        
    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting analysis result"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for impact analysis service."""
    return {"status": "healthy", "service": "impact_analysis"}