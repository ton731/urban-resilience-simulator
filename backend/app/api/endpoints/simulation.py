"""
FastAPI endpoints for disaster simulation and network analysis (SE-2.1, SE-2.2)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.schemas.request import (
    DisasterSimulationRequest,
    PathfindingRequest,
    ServiceAreaRequest,
)
from app.schemas.response import (
    DisasterSimulationResponse,
    PathfindingResponse,
    ServiceAreaResponse,
    TreeCollapseEventResponse,
    RoadObstructionResponse,
    ErrorResponse,
)
from app.core.simulation_engine import DisasterSimulator, NetworkAnalyzer
from app.core.simulation_engine.models import (
    DisasterSimulationConfig,
    VehicleType,
    PathfindingRequest as SimPathfindingRequest,
)

# Initialize router
router = APIRouter(prefix="/simulation", tags=["Simulation Engine"])

# Global storage for world states and simulation results
# In production, this would be replaced with a database
_world_states: Dict[str, Dict[str, Any]] = {}
_simulation_results: Dict[str, Dict[str, Any]] = {}
_network_analyzers: Dict[str, NetworkAnalyzer] = {}

logger = logging.getLogger(__name__)


@router.post("/disaster", response_model=DisasterSimulationResponse)
async def simulate_disaster(request: DisasterSimulationRequest):
    """
    Execute disaster simulation (SE-2.1) on a generated world.

    This endpoint implements the tree collapse simulation based on vulnerability
    levels and disaster intensity as specified in SE-2.1.

    Args:
        request: DisasterSimulationRequest with world ID and simulation parameters

    Returns:
        DisasterSimulationResponse with collapse events and road obstructions
    """
    try:
        # Validate world generation exists
        if request.world_generation_id not in _world_states:
            raise HTTPException(
                status_code=404,
                detail=f"World generation {request.world_generation_id} not found. Generate a world first using /api/v1/world/generate",
            )

        world_data = _world_states[request.world_generation_id]

        # Create simulation configuration
        config_data = {
            "disaster_intensity": request.disaster_intensity,
            "random_seed": request.random_seed,
            "include_minor_debris": request.include_minor_debris,
        }

        if request.vulnerability_collapse_rates:
            config_data["vulnerability_collapse_rates"] = (
                request.vulnerability_collapse_rates
            )

        simulation_config = DisasterSimulationConfig(**config_data)

        # Initialize disaster simulator
        disaster_simulator = DisasterSimulator(simulation_config)

        # Extract world data
        trees_data = world_data.get("trees", {})
        roads_data = world_data.get("edges", {})  # Road edges
        nodes_data = world_data.get("nodes", {})  # Road nodes for geometry

        if not trees_data:
            raise HTTPException(
                status_code=400,
                detail="No trees found in the world generation. Ensure trees were generated with include_trees=True",
            )

        # Run disaster simulation with node data for precise geometry
        logger.info(
            f"Running disaster simulation on world {request.world_generation_id} with intensity {request.disaster_intensity}"
        )
        simulation_result = disaster_simulator.simulate_tree_collapse(
            trees_data, roads_data, nodes_data
        )

        # Store simulation result for later use
        _simulation_results[simulation_result.simulation_id] = {
            "result": simulation_result,
            "world_generation_id": request.world_generation_id,
        }

        # Initialize network analyzer with this simulation's obstructions
        network_analyzer = NetworkAnalyzer()
        network_analyzer.initialize_road_network(
            world_data.get("nodes", {}), world_data.get("edges", {})
        )
        network_analyzer.update_obstructions(simulation_result.road_obstructions)
        _network_analyzers[simulation_result.simulation_id] = network_analyzer

        # Convert to response format
        disaster_events_response = []
        for event in simulation_result.disaster_events:
            disaster_events_response.append(
                TreeCollapseEventResponse(
                    event_id=event.event_id,
                    tree_id=event.tree_id,
                    location=event.location,
                    vulnerability_level=event.vulnerability_level.value,
                    collapse_angle=event.collapse_angle,
                    tree_height=event.tree_height,
                    trunk_width=event.trunk_width,
                    blockage_polygon=event.blockage_polygon,
                    severity=event.severity,
                    timestamp=event.timestamp,
                )
            )

        road_obstructions_response = []
        for obstruction in simulation_result.road_obstructions:
            road_obstructions_response.append(
                RoadObstructionResponse(
                    obstruction_id=obstruction.obstruction_id,
                    road_edge_id=obstruction.road_edge_id,
                    obstruction_polygon=obstruction.obstruction_polygon,
                    remaining_width=obstruction.remaining_width,
                    blocked_percentage=obstruction.blocked_percentage,
                    caused_by_event=obstruction.caused_by_event,
                )
            )

        return DisasterSimulationResponse(
            simulation_id=simulation_result.simulation_id,
            world_generation_id=request.world_generation_id,
            simulated_at=simulation_result.simulated_at,
            disaster_events=disaster_events_response,
            road_obstructions=road_obstructions_response,
            total_trees_affected=simulation_result.total_trees_affected,
            total_roads_affected=simulation_result.total_roads_affected,
            total_blocked_road_length=simulation_result.total_blocked_road_length,
            trees_affected_by_level=simulation_result.trees_affected_by_level,
            average_road_blockage_percentage=simulation_result.average_road_blockage_percentage,
            simulation_config=simulation_result.simulation_config.dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in disaster simulation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during disaster simulation: {str(e)}",
        )


@router.post("/pathfinding", response_model=PathfindingResponse)
async def find_path(request: PathfindingRequest):
    """
    Find optimal path between two points (SE-2.2).

    This endpoint implements A* pathfinding with obstruction awareness and
    vehicle-specific constraints as specified in SE-2.2.

    Args:
        request: PathfindingRequest with start/end points and vehicle type

    Returns:
        PathfindingResponse with path details or failure indication
    """
    try:
        # Validate world generation exists
        if request.world_generation_id not in _world_states:
            raise HTTPException(
                status_code=404,
                detail=f"World generation {request.world_generation_id} not found",
            )

        # Get network analyzer
        network_analyzer = None

        if request.simulation_id:
            # Post-disaster pathfinding
            if request.simulation_id not in _network_analyzers:
                raise HTTPException(
                    status_code=404,
                    detail=f"Simulation {request.simulation_id} not found. Run disaster simulation first",
                )
            network_analyzer = _network_analyzers[request.simulation_id]

        else:
            # Pre-disaster pathfinding - create clean network analyzer
            world_data = _world_states[request.world_generation_id]
            network_analyzer = NetworkAnalyzer()
            network_analyzer.initialize_road_network(
                world_data.get("nodes", {}), world_data.get("edges", {})
            )

        # Validate vehicle type
        try:
            vehicle_type_enum = VehicleType(request.vehicle_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid vehicle type: {request.vehicle_type}. Valid types: {[v.value for v in VehicleType]}",
            )

        # Create pathfinding request
        pathfinding_request = SimPathfindingRequest(
            start_point=request.start_point,
            end_point=request.end_point,
            vehicle_type=vehicle_type_enum,
            max_travel_time=request.max_travel_time,
        )

        # Execute pathfinding
        logger.info(
            f"Finding path from {request.start_point} to {request.end_point} for {request.vehicle_type}"
        )
        result = network_analyzer.find_path(pathfinding_request)

        # Optionally find alternative routes if the main path succeeded
        alternative_routes = []
        if result.success and request.find_alternatives:
            try:
                alternatives = network_analyzer.find_alternative_paths(
                    pathfinding_request, max_alternatives=2, diversity_factor=1.5
                )
                # Skip the first alternative as it might be very similar to the main path
                for alt in alternatives[1:]:
                    alternative_routes.append(
                        {
                            "path_coordinates": alt.path_coordinates,
                            "total_distance": alt.total_distance,
                            "estimated_travel_time": alt.estimated_travel_time,
                            "blocked_roads": alt.blocked_roads,
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not find alternative routes: {str(e)}")

        print(
            PathfindingResponse(
                success=result.success,
                path_coordinates=result.path_coordinates,
                path_node_ids=result.path_node_ids,
            )
        )
        print()

        return PathfindingResponse(
            success=result.success,
            path_coordinates=result.path_coordinates,
            path_node_ids=result.path_node_ids,
            total_distance=result.total_distance,
            estimated_travel_time=result.estimated_travel_time,
            vehicle_type=result.vehicle_type.value,
            world_generation_id=request.world_generation_id,
            simulation_id=request.simulation_id,
            blocked_roads=result.blocked_roads,
            alternative_routes=alternative_routes,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in pathfinding: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during pathfinding: {str(e)}",
        )


@router.post("/service-area", response_model=ServiceAreaResponse)
async def calculate_service_area(request: ServiceAreaRequest):
    """
    Calculate service area (isochrone) from a center point.

    This endpoint calculates reachable areas within specified travel times,
    useful for emergency response coverage analysis.

    Args:
        request: ServiceAreaRequest with center point and time constraints

    Returns:
        ServiceAreaResponse with service area boundaries and metrics
    """
    try:
        # Validate world generation exists
        if request.world_generation_id not in _world_states:
            raise HTTPException(
                status_code=404,
                detail=f"World generation {request.world_generation_id} not found",
            )

        # Get network analyzer
        network_analyzer = None

        if request.simulation_id:
            # Post-disaster analysis
            if request.simulation_id not in _network_analyzers:
                raise HTTPException(
                    status_code=404,
                    detail=f"Simulation {request.simulation_id} not found",
                )
            network_analyzer = _network_analyzers[request.simulation_id]

        else:
            # Pre-disaster analysis
            world_data = _world_states[request.world_generation_id]
            network_analyzer = NetworkAnalyzer()
            network_analyzer.initialize_road_network(
                world_data.get("nodes", {}), world_data.get("edges", {})
            )

        # Validate vehicle type
        try:
            vehicle_type_enum = VehicleType(request.vehicle_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid vehicle type: {request.vehicle_type}"
            )

        # Calculate main service area
        logger.info(
            f"Calculating service area from {request.center_point} for {request.max_travel_time}s with {request.vehicle_type}"
        )

        service_area_coords = network_analyzer.calculate_service_area(
            center_point=request.center_point,
            vehicle_type=vehicle_type_enum,
            max_travel_time=request.max_travel_time,
        )

        # Calculate multiple isochrones if requested (optimized)
        isochrones = None
        if request.time_intervals:
            isochrones_dict = network_analyzer.calculate_multiple_isochrones(
                center_point=request.center_point,
                vehicle_type=vehicle_type_enum,
                time_intervals=request.time_intervals,
            )
            # Convert float keys to string keys for JSON serialization
            isochrones = {str(int(k)): v for k, v in isochrones_dict.items()}

        # Calculate approximate area (simplified)
        # In practice, you'd use proper geometric calculations
        area_coverage = len(service_area_coords) * 100.0  # Rough approximation

        # Extract reachable nodes (simplified - would need proper implementation)
        reachable_nodes = [
            f"node_{i:03d}" for i in range(min(50, len(service_area_coords)))
        ]

        return ServiceAreaResponse(
            service_area_coordinates=service_area_coords,
            reachable_nodes=reachable_nodes,
            isochrones=isochrones,
            area_coverage_sqm=area_coverage,
            max_travel_time_used=request.max_travel_time,
            center_point=request.center_point,
            vehicle_type=request.vehicle_type,
            world_generation_id=request.world_generation_id,
            simulation_id=request.simulation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in service area calculation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during service area calculation: {str(e)}",
        )


@router.get("/simulations")
async def list_simulations():
    """List all available simulation results."""
    simulations = []
    for sim_id, sim_data in _simulation_results.items():
        result = sim_data["result"]
        simulations.append(
            {
                "simulation_id": sim_id,
                "world_generation_id": sim_data["world_generation_id"],
                "simulated_at": result.simulated_at.isoformat(),
                "total_trees_affected": result.total_trees_affected,
                "total_roads_affected": result.total_roads_affected,
                "disaster_intensity": result.simulation_config.disaster_intensity,
            }
        )

    return {"simulations": simulations}


@router.post("/network-analysis", response_model=Dict[str, Any])
async def analyze_network_connectivity(
    world_generation_id: str,
    vehicle_type: str = "car",
    simulation_id: Optional[str] = None,
):
    """
    Analyze road network connectivity for a specific vehicle type.

    This endpoint implements SE-2.2 network analysis capabilities to assess
    how disaster-related obstructions affect network accessibility.

    Args:
        world_generation_id: ID of the generated world
        vehicle_type: Type of vehicle for analysis
        simulation_id: Optional simulation ID for post-disaster analysis

    Returns:
        Network connectivity analysis results
    """
    try:
        # Validate world generation exists
        if world_generation_id not in _world_states:
            raise HTTPException(
                status_code=404,
                detail=f"World generation {world_generation_id} not found",
            )

        # Get network analyzer
        network_analyzer = None

        if simulation_id:
            # Post-disaster analysis
            if simulation_id not in _network_analyzers:
                raise HTTPException(
                    status_code=404,
                    detail=f"Simulation {simulation_id} not found. Run disaster simulation first",
                )
            network_analyzer = _network_analyzers[simulation_id]
        else:
            # Pre-disaster analysis
            world_data = _world_states[world_generation_id]
            network_analyzer = NetworkAnalyzer()
            network_analyzer.initialize_road_network(
                world_data.get("nodes", {}), world_data.get("edges", {})
            )

        # Validate vehicle type
        try:
            vehicle_type_enum = VehicleType(vehicle_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid vehicle type: {vehicle_type}. Valid types: {[v.value for v in VehicleType]}",
            )

        # Perform network connectivity analysis
        logger.info(
            f"Analyzing network connectivity for {vehicle_type} in world {world_generation_id}"
        )

        connectivity_stats = network_analyzer.analyze_road_network_connectivity(
            vehicle_type_enum
        )

        return {
            "world_generation_id": world_generation_id,
            "simulation_id": simulation_id,
            "analysis_type": "network_connectivity",
            "vehicle_type": vehicle_type,
            "connectivity_analysis": connectivity_stats,
            "analyzed_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in network analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during network analysis: {str(e)}",
        )


@router.post("/pathfinding/alternatives")
async def find_alternative_paths(
    request: PathfindingRequest,
    max_alternatives: int = 3,
    diversity_factor: float = 1.5,
):
    """
    Find multiple alternative paths between two points (SE-2.2 Advanced).

    This endpoint finds diverse alternative routes useful for emergency
    response planning and route redundancy analysis.

    Args:
        request: PathfindingRequest with start/end points and vehicle type
        max_alternatives: Maximum number of alternative paths to find
        diversity_factor: Factor to increase cost of previously used edges

    Returns:
        List of alternative PathfindingResponse objects
    """
    try:
        # Validate world generation exists
        if request.world_generation_id not in _world_states:
            raise HTTPException(
                status_code=404,
                detail=f"World generation {request.world_generation_id} not found",
            )

        # Get network analyzer
        network_analyzer = None

        if request.simulation_id:
            if request.simulation_id not in _network_analyzers:
                raise HTTPException(
                    status_code=404,
                    detail=f"Simulation {request.simulation_id} not found",
                )
            network_analyzer = _network_analyzers[request.simulation_id]
        else:
            world_data = _world_states[request.world_generation_id]
            network_analyzer = NetworkAnalyzer()
            network_analyzer.initialize_road_network(
                world_data.get("nodes", {}), world_data.get("edges", {})
            )

        # Validate vehicle type
        try:
            vehicle_type_enum = VehicleType(request.vehicle_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid vehicle type: {request.vehicle_type}"
            )

        # Create pathfinding request
        pathfinding_request = SimPathfindingRequest(
            start_point=request.start_point,
            end_point=request.end_point,
            vehicle_type=vehicle_type_enum,
            max_travel_time=request.max_travel_time,
        )

        # Find alternative paths
        logger.info(
            f"Finding {max_alternatives} alternative paths from {request.start_point} to {request.end_point}"
        )
        alternatives = network_analyzer.find_alternative_paths(
            pathfinding_request, max_alternatives, diversity_factor
        )

        # Convert to response format
        alternative_responses = []
        for i, result in enumerate(alternatives):
            alternative_responses.append(
                PathfindingResponse(
                    success=result.success,
                    path_coordinates=result.path_coordinates,
                    path_node_ids=result.path_node_ids,
                    total_distance=result.total_distance,
                    estimated_travel_time=result.estimated_travel_time,
                    vehicle_type=result.vehicle_type.value,
                    world_generation_id=request.world_generation_id,
                    simulation_id=request.simulation_id,
                    blocked_roads=result.blocked_roads,
                    alternative_routes=[],  # Not needed for individual alternatives
                )
            )

        return {
            "alternatives": alternative_responses,
            "total_alternatives_found": len(alternatives),
            "max_alternatives_requested": max_alternatives,
            "diversity_factor_used": diversity_factor,
            "start_point": request.start_point,
            "end_point": request.end_point,
            "vehicle_type": request.vehicle_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding alternative paths: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error finding alternative paths: {str(e)}",
        )


@router.get("/simulation/{simulation_id}")
async def get_simulation_result(simulation_id: str):
    """Get detailed results for a specific simulation."""
    if simulation_id not in _simulation_results:
        raise HTTPException(
            status_code=404, detail=f"Simulation {simulation_id} not found"
        )

    sim_data = _simulation_results[simulation_id]
    result = sim_data["result"]

    # Convert to response format (similar to simulate_disaster endpoint)
    disaster_events_response = []
    for event in result.disaster_events:
        disaster_events_response.append(
            TreeCollapseEventResponse(
                event_id=event.event_id,
                tree_id=event.tree_id,
                location=event.location,
                vulnerability_level=event.vulnerability_level.value,
                collapse_angle=event.collapse_angle,
                tree_height=event.tree_height,
                trunk_width=event.trunk_width,
                blockage_polygon=event.blockage_polygon,
                severity=event.severity,
                timestamp=event.timestamp,
            )
        )

    road_obstructions_response = []
    for obstruction in result.road_obstructions:
        road_obstructions_response.append(
            RoadObstructionResponse(
                obstruction_id=obstruction.obstruction_id,
                road_edge_id=obstruction.road_edge_id,
                obstruction_polygon=obstruction.obstruction_polygon,
                remaining_width=obstruction.remaining_width,
                blocked_percentage=obstruction.blocked_percentage,
                caused_by_event=obstruction.caused_by_event,
            )
        )

    return DisasterSimulationResponse(
        simulation_id=result.simulation_id,
        world_generation_id=sim_data["world_generation_id"],
        simulated_at=result.simulated_at,
        disaster_events=disaster_events_response,
        road_obstructions=road_obstructions_response,
        total_trees_affected=result.total_trees_affected,
        total_roads_affected=result.total_roads_affected,
        total_blocked_road_length=result.total_blocked_road_length,
        trees_affected_by_level=result.trees_affected_by_level,
        average_road_blockage_percentage=result.average_road_blockage_percentage,
        simulation_config=result.simulation_config.dict(),
    )


# Dependency injection functions for external integration
def set_world_state(world_id: str, world_data: Dict[str, Any]):
    """Store world state data for simulation use."""
    _world_states[world_id] = world_data


def get_simulation_result(simulation_id: str) -> Dict[str, Any]:
    """Retrieve simulation result by ID."""
    return _simulation_results.get(simulation_id)
