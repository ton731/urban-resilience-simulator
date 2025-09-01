"""
Ambulance Service Analyzer Implementation (IA-3.1)

Implements the core logic for ambulance service range analysis using grid-based
service accessibility mapping. Calculates response times and generates 
visualization data for pre-disaster, post-disaster, and comparison analysis.
"""

import uuid
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..simulation_engine.network_analyzer import NetworkAnalyzer
from ..simulation_engine.models import PathfindingRequest, VehicleType
from .models import (
    AmbulanceServiceAnalysisRequest,
    AmbulanceServiceAnalysisResponse, 
    ServiceGridCell,
    AmbulanceServiceMetrics,
    ComparisonMetrics,
    AnalysisMode
)


class AmbulanceServiceAnalyzer:
    """
    Implements IA-3.1: Ambulance Service Range Analysis
    
    Uses grid-based service accessibility mapping to analyze and visualize
    ambulance response times across the entire map area.
    """
    
    def __init__(self):
        """Initialize the ambulance service analyzer."""
        self.network_analyzer = NetworkAnalyzer()
        
        # Color coding for different service levels
        self.service_level_colors = {
            "excellent": "#00FF00",  # Green: ≤ 5 minutes (300 seconds)
            "good": "#FFFF00",       # Yellow: 5-10 minutes (300-600 seconds)
            "fair": "#FFA500",       # Orange: 10-15 minutes (600-900 seconds)
            "poor": "#FF0000",       # Red: > 15 minutes (> 900 seconds)
            "unreachable": "#808080" # Gray: Unreachable
        }
    
    async def analyze_ambulance_service(
        self, 
        request: AmbulanceServiceAnalysisRequest,
        world_data: Dict[str, Any],
        simulation_data: Optional[Dict[str, Any]] = None
    ) -> AmbulanceServiceAnalysisResponse:
        """
        Perform ambulance service analysis based on the request parameters.
        
        Args:
            request: Analysis request with configuration
            world_data: World generation data (nodes, edges, facilities, etc.)
            simulation_data: Optional simulation data for post-disaster analysis
            
        Returns:
            Complete analysis response with grid data and metrics
        """
        print(f"\n🚑 開始救護車服務範圍分析")
        print(f"分析模式: {request.analysis_mode.value}")
        print(f"網格大小: {request.grid_size_meters}m")
        print(f"最大響應時間: {request.max_response_time_seconds}s ({request.max_response_time_seconds/60:.1f}分鐘)")
        print("=" * 80)
        
        analysis_id = f"ambulance_analysis_{uuid.uuid4()}"
        
        # Initialize network analyzer with world data
        self.network_analyzer.initialize_road_network(
            world_data["nodes"], 
            world_data["edges"]
        )
        
        # Get ambulance stations from facilities
        ambulance_stations = self._get_ambulance_stations(world_data["facilities"])
        if not ambulance_stations:
            raise ValueError("No ambulance stations found in world data")
        
        print(f"找到 {len(ambulance_stations)} 個救護車起點")
        for station in ambulance_stations:
            print(f"  🚑 {station['id']}: ({station['x']:.0f}, {station['y']:.0f})")
        print()
        
        # Generate analysis grid
        grid_cells = self._generate_analysis_grid(
            world_data["boundary"], 
            request.grid_size_meters
        )
        
        print(f"生成 {len(grid_cells)} 個分析網格 ({request.grid_size_meters}m × {request.grid_size_meters}m)")
        print()
        
        # Initialize response object
        response = AmbulanceServiceAnalysisResponse(
            analysis_id=analysis_id,
            world_generation_id=request.world_generation_id,
            analysis_mode=request.analysis_mode,
            analyzed_at=datetime.now(),
            grid_cells=[],
            analysis_config={
                "grid_size_meters": request.grid_size_meters,
                "max_response_time_seconds": request.max_response_time_seconds,
                "vehicle_type": request.vehicle_type,
                "ambulance_stations_count": len(ambulance_stations)
            },
            color_legend=self.service_level_colors,
            map_boundary=world_data["boundary"]
        )
        
        # Perform analysis based on mode
        if request.analysis_mode == AnalysisMode.PRE_DISASTER:
            grid_data, metrics = await self._analyze_pre_disaster(
                grid_cells, ambulance_stations, request
            )
            response.grid_cells = grid_data
            response.pre_disaster_metrics = metrics
            
        elif request.analysis_mode == AnalysisMode.POST_DISASTER:
            if not simulation_data:
                raise ValueError("Simulation data required for post-disaster analysis")
            
            # Apply road obstructions
            if "road_obstructions" in simulation_data:
                self.network_analyzer.update_obstructions(simulation_data["road_obstructions"])
            
            grid_data, metrics = await self._analyze_post_disaster(
                grid_cells, ambulance_stations, request
            )
            response.grid_cells = grid_data
            response.post_disaster_metrics = metrics
            
        elif request.analysis_mode == AnalysisMode.COMPARISON:
            if not simulation_data:
                raise ValueError("Simulation data required for comparison analysis")
            
            # Analyze pre-disaster first
            pre_grid_data, pre_metrics = await self._analyze_pre_disaster(
                grid_cells, ambulance_stations, request
            )
            
            # Apply obstructions and analyze post-disaster
            if "road_obstructions" in simulation_data:
                self.network_analyzer.update_obstructions(simulation_data["road_obstructions"])
            
            post_grid_data, post_metrics = await self._analyze_post_disaster(
                grid_cells, ambulance_stations, request
            )
            
            # Generate comparison data and metrics
            comparison_grid_data, comparison_metrics = self._generate_comparison_analysis(
                pre_grid_data, post_grid_data, pre_metrics, post_metrics
            )
            
            response.grid_cells = comparison_grid_data
            response.pre_disaster_metrics = pre_metrics
            response.post_disaster_metrics = post_metrics
            response.comparison_metrics = comparison_metrics
        
        print(f"\n🎉 救護車服務分析完成!")
        print(f"分析ID: {analysis_id}")
        print(f"處理網格數: {len(response.grid_cells)}")
        print("=" * 80)
        
        return response
    
    def _get_ambulance_stations(self, facilities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract ambulance stations from facilities data."""
        stations = []
        for facility_id, facility_data in facilities.items():
            if facility_data.get("facility_type") == "ambulance_station":
                stations.append({
                    "id": facility_id,
                    "x": facility_data["x"],
                    "y": facility_data["y"],
                    "node_id": facility_data.get("node_id")
                })
        return stations
    
    def _generate_analysis_grid(
        self, 
        map_boundary: Dict[str, float], 
        grid_size: float
    ) -> List[Dict[str, Any]]:
        """
        Generate a grid of analysis points covering the entire map area.
        
        Args:
            map_boundary: Map boundary with min_x, min_y, max_x, max_y
            grid_size: Size of each grid cell in meters
            
        Returns:
            List of grid cell dictionaries with center coordinates
        """
        grid_cells = []
        
        # Calculate grid dimensions
        map_width = map_boundary["max_x"] - map_boundary["min_x"]
        map_height = map_boundary["max_y"] - map_boundary["min_y"]
        
        cols = int(math.ceil(map_width / grid_size))
        rows = int(math.ceil(map_height / grid_size))
        
        print(f"網格維度: {cols} × {rows} = {cols * rows} 個網格")
        
        # Generate grid cells
        for row in range(rows):
            for col in range(cols):
                # Calculate center coordinates
                center_x = map_boundary["min_x"] + (col + 0.5) * grid_size
                center_y = map_boundary["min_y"] + (row + 0.5) * grid_size
                
                # Ensure center is within map boundary
                center_x = min(center_x, map_boundary["max_x"] - grid_size/2)
                center_y = min(center_y, map_boundary["max_y"] - grid_size/2)
                
                grid_cells.append({
                    "grid_id": f"grid_{col}_{row}",
                    "center_x": center_x,
                    "center_y": center_y,
                    "col": col,
                    "row": row
                })
        
        return grid_cells
    
    async def _analyze_pre_disaster(
        self, 
        grid_cells: List[Dict[str, Any]], 
        ambulance_stations: List[Dict[str, Any]], 
        request: AmbulanceServiceAnalysisRequest
    ) -> Tuple[List[ServiceGridCell], AmbulanceServiceMetrics]:
        """Perform pre-disaster service analysis."""
        print("🟢 執行災前分析...")
        
        service_grid_cells = []
        reachable_cells = 0
        response_times = []
        service_level_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "unreachable": 0}
        
        total_cells = len(grid_cells)
        
        for i, grid_cell in enumerate(grid_cells, 1):
            if i % 100 == 0 or i == total_cells:
                print(f"  處理進度: {i}/{total_cells} ({i/total_cells*100:.1f}%)")
            
            # Find nearest ambulance station and calculate service time
            best_time = float('inf')
            best_station_id = None
            
            grid_point = (grid_cell["center_x"], grid_cell["center_y"])
            
            for station in ambulance_stations:
                station_point = (station["x"], station["y"])
                
                # Create pathfinding request
                pathfinding_request = PathfindingRequest(
                    start_point=station_point,
                    end_point=grid_point,
                    vehicle_type=VehicleType.AMBULANCE,
                    max_travel_time=request.max_response_time_seconds
                )
                
                # Find path and get travel time
                result = self.network_analyzer.find_path(pathfinding_request)
                
                if result.success and result.estimated_travel_time < best_time:
                    best_time = result.estimated_travel_time
                    best_station_id = station["id"]
            
            # Determine service level and color
            if best_time == float('inf') or best_time > request.max_response_time_seconds:
                service_time = None
                accessibility_level = "unreachable"
                color_code = self.service_level_colors["unreachable"]
                service_level_counts["unreachable"] += 1
            else:
                service_time = best_time
                reachable_cells += 1
                response_times.append(best_time)
                
                # Categorize service level
                if best_time <= 300:  # ≤ 5 minutes
                    accessibility_level = "excellent"
                    service_level_counts["excellent"] += 1
                elif best_time <= 600:  # 5-10 minutes
                    accessibility_level = "good"
                    service_level_counts["good"] += 1
                elif best_time <= 900:  # 10-15 minutes
                    accessibility_level = "fair"
                    service_level_counts["fair"] += 1
                else:  # > 15 minutes
                    accessibility_level = "poor"
                    service_level_counts["poor"] += 1
                
                color_code = self.service_level_colors[accessibility_level]
            
            # Create service grid cell
            service_cell = ServiceGridCell(
                grid_id=grid_cell["grid_id"],
                center_x=grid_cell["center_x"],
                center_y=grid_cell["center_y"],
                service_time_seconds=service_time,
                nearest_ambulance_station_id=best_station_id,
                grid_size_meters=request.grid_size_meters,
                color_code=color_code,
                accessibility_level=accessibility_level
            )
            
            service_grid_cells.append(service_cell)
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            service_grid_cells, len(ambulance_stations), response_times, service_level_counts
        )
        
        print(f"✅ 災前分析完成:")
        print(f"  📊 可達網格: {reachable_cells}/{total_cells} ({reachable_cells/total_cells*100:.1f}%)")
        print(f"  ⏱️ 平均響應時間: {metrics.average_response_time_seconds:.1f}秒 ({metrics.average_response_time_seconds/60:.1f}分鐘)")
        print(f"  🎯 服務等級分布:")
        print(f"    - 優秀 (≤5分): {service_level_counts['excellent']} ({service_level_counts['excellent']/total_cells*100:.1f}%)")
        print(f"    - 良好 (5-10分): {service_level_counts['good']} ({service_level_counts['good']/total_cells*100:.1f}%)")
        print(f"    - 一般 (10-15分): {service_level_counts['fair']} ({service_level_counts['fair']/total_cells*100:.1f}%)")
        print(f"    - 較差 (>15分): {service_level_counts['poor']} ({service_level_counts['poor']/total_cells*100:.1f}%)")
        print()
        
        return service_grid_cells, metrics
    
    async def _analyze_post_disaster(
        self, 
        grid_cells: List[Dict[str, Any]], 
        ambulance_stations: List[Dict[str, Any]], 
        request: AmbulanceServiceAnalysisRequest
    ) -> Tuple[List[ServiceGridCell], AmbulanceServiceMetrics]:
        """Perform post-disaster service analysis."""
        print("🔴 執行災後分析...")
        
        # Use same logic as pre-disaster but with obstructed network
        return await self._analyze_pre_disaster(grid_cells, ambulance_stations, request)
    
    def _generate_comparison_analysis(
        self,
        pre_grid_data: List[ServiceGridCell],
        post_grid_data: List[ServiceGridCell],
        pre_metrics: AmbulanceServiceMetrics,
        post_metrics: AmbulanceServiceMetrics
    ) -> Tuple[List[ServiceGridCell], ComparisonMetrics]:
        """Generate comparison analysis between pre and post disaster."""
        print("🔄 生成對比分析...")
        
        # Create comparison grid data showing changes
        comparison_grid_data = []
        
        # Comparison metrics
        newly_unreachable = 0
        service_degradation = 0
        cells_improved = 0
        time_changes = []
        
        severely_impacted = 0
        moderately_impacted = 0
        lightly_impacted = 0
        
        for pre_cell, post_cell in zip(pre_grid_data, post_grid_data):
            # Calculate change in service time
            pre_time = pre_cell.service_time_seconds
            post_time = post_cell.service_time_seconds
            
            # Determine comparison status
            if pre_time is not None and post_time is None:
                # Became unreachable
                newly_unreachable += 1
                comparison_color = "#800080"  # Purple for newly unreachable
                accessibility_level = "newly_unreachable"
                
            elif pre_time is None and post_time is not None:
                # Became reachable (rare but possible)
                cells_improved += 1
                comparison_color = "#00FFFF"  # Cyan for improvement
                accessibility_level = "newly_reachable"
                
            elif pre_time is not None and post_time is not None:
                # Both reachable - calculate change
                time_change = post_time - pre_time
                time_changes.append(time_change)
                
                if time_change > pre_time * 0.5:  # >50% increase
                    severely_impacted += 1
                    comparison_color = "#8B0000"  # Dark red
                    accessibility_level = "severely_degraded"
                elif time_change > pre_time * 0.2:  # 20-50% increase
                    moderately_impacted += 1
                    comparison_color = "#FF4500"  # Orange red
                    accessibility_level = "moderately_degraded"
                elif time_change > 0:  # Some increase
                    lightly_impacted += 1
                    comparison_color = "#FFD700"  # Gold
                    accessibility_level = "lightly_degraded"
                else:  # No change or improved
                    cells_improved += 1
                    comparison_color = "#90EE90"  # Light green
                    accessibility_level = "improved_or_same"
                    
                if time_change > 0:
                    service_degradation += 1
            else:
                # Both unreachable
                comparison_color = self.service_level_colors["unreachable"]
                accessibility_level = "unreachable"
            
            # Create comparison grid cell
            comparison_cell = ServiceGridCell(
                grid_id=pre_cell.grid_id,
                center_x=pre_cell.center_x,
                center_y=pre_cell.center_y,
                service_time_seconds=post_time,  # Show post-disaster time
                nearest_ambulance_station_id=post_cell.nearest_ambulance_station_id,
                grid_size_meters=pre_cell.grid_size_meters,
                color_code=comparison_color,
                accessibility_level=accessibility_level
            )
            
            comparison_grid_data.append(comparison_cell)
        
        # Calculate comparison metrics
        comparison_metrics = ComparisonMetrics(
            coverage_change_percentage=post_metrics.coverage_percentage - pre_metrics.coverage_percentage,
            newly_unreachable_cells=newly_unreachable,
            average_time_increase_seconds=sum(time_changes) / len(time_changes) if time_changes else 0,
            median_time_increase_seconds=sorted(time_changes)[len(time_changes)//2] if time_changes else 0,
            service_degradation_cells=service_degradation,
            cells_improved=cells_improved,
            severely_impacted_cells=severely_impacted,
            moderately_impacted_cells=moderately_impacted,
            lightly_impacted_cells=lightly_impacted
        )
        
        print(f"✅ 對比分析完成:")
        print(f"  📉 服務覆蓋率變化: {comparison_metrics.coverage_change_percentage:+.1f}%")
        print(f"  🚫 新增無法到達區域: {newly_unreachable} 個網格")
        print(f"  ⏱️ 平均響應時間增加: {comparison_metrics.average_time_increase_seconds:+.1f}秒")
        print(f"  📊 服務惡化網格: {service_degradation} 個")
        print()
        
        return comparison_grid_data, comparison_metrics
    
    def _calculate_metrics(
        self, 
        grid_cells: List[ServiceGridCell], 
        ambulance_stations_count: int,
        response_times: List[float],
        service_level_counts: Dict[str, int]
    ) -> AmbulanceServiceMetrics:
        """Calculate metrics for the analysis."""
        total_cells = len(grid_cells)
        reachable_cells = len(response_times)
        
        # Calculate area metrics
        grid_size_sqm = grid_cells[0].grid_size_meters ** 2 if grid_cells else 0
        total_area_sqm = total_cells * grid_size_sqm
        service_blind_area_sqm = service_level_counts["unreachable"] * grid_size_sqm
        
        return AmbulanceServiceMetrics(
            total_grid_cells=total_cells,
            reachable_cells=reachable_cells,
            unreachable_cells=total_cells - reachable_cells,
            coverage_percentage=(reachable_cells / total_cells * 100) if total_cells > 0 else 0,
            average_response_time_seconds=sum(response_times) / len(response_times) if response_times else 0,
            median_response_time_seconds=sorted(response_times)[len(response_times)//2] if response_times else 0,
            max_response_time_seconds=max(response_times) if response_times else None,
            excellent_service_cells=service_level_counts["excellent"],
            good_service_cells=service_level_counts["good"],
            fair_service_cells=service_level_counts["fair"],
            poor_service_cells=service_level_counts["poor"],
            service_blind_area_sqm=service_blind_area_sqm,
            total_analyzed_area_sqm=total_area_sqm,
            ambulance_stations_analyzed=ambulance_stations_count
        )