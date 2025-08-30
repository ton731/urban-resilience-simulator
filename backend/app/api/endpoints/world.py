from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid
from typing import Dict, Any

from app.schemas.request import WorldGenerationRequest
from app.schemas.response import (
    WorldGenerationResponse, 
    MapBoundaryResponse,
    MapNodeResponse, 
    RoadEdgeResponse,
    TreeResponse,
    FacilityResponse,
    BuildingResponse,
    ErrorResponse
)
from app.core.world_synthesizer.map_generator import MapGenerator

router = APIRouter()


@router.post(
    "/world/generate",
    response_model=WorldGenerationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Generate World Map (WS-1.1 + WS-1.2 + WS-1.3 + WS-1.5)",
    description="""
    Generates a procedural 2D map with road network, trees, facilities, and buildings according to WS-1.1 + WS-1.2 + WS-1.3 + WS-1.5 specifications.
    
    Creates:
    - 2D grid map with geographical boundaries
    - Random but logical road networks (main roads and secondary roads)
    - Trees along road edges with vulnerability levels (WS-1.2)
    - Critical facilities on road network nodes (WS-1.3): ambulance stations and shelters
    - Buildings with population data in non-road areas (WS-1.5): residential, commercial, mixed, industrial
    - Graph data structure with nodes and edges
    - Configurable generation parameters
    
    The generated map includes intersections, road segments, trees, facilities, and buildings with properties
    suitable for disaster simulation and emergency response analysis including population-based evacuation scenarios.
    """
)
async def generate_world(request: WorldGenerationRequest):
    """
    Generate a new world map with road network.
    
    Args:
        request: World generation configuration parameters
        
    Returns:
        WorldGenerationResponse: Complete generated map data
        
    Raises:
        HTTPException: If generation fails or invalid parameters provided
    """
    try:
        # Prepare configuration for map generator
        config = {
            "map_size": request.map_size,
            "road_density": request.road_density,
            "main_road_count": request.main_road_count,
            "secondary_road_density": request.secondary_road_density,
            # Tree generation parameters (WS-1.2)
            "tree_spacing": request.tree_spacing,
            "tree_max_offset": request.tree_max_offset,
            "tree_road_buffer": 3.0,  # From config
            "tree_height_range": [4.0, 25.0],  # From config
            "tree_trunk_width_range": [0.2, 1.5],  # From config
            # Building generation parameters (WS-1.5)
            "building_density": getattr(request, 'building_density', 0.3),
            "min_building_distance": 25.0,
            "road_buffer_distance": 15.0
        }
        
        # Set vulnerability distribution
        if request.vulnerability_distribution:
            config["vulnerability_distribution"] = request.vulnerability_distribution
        else:
            config["vulnerability_distribution"] = {
                "I": 0.1, "II": 0.3, "III": 0.6
            }
        
        # Apply any configuration overrides
        if request.config_override:
            config.update(request.config_override)
        
        # Validate map size
        if (request.map_size[0] < 500 or request.map_size[0] > 10000 or 
            request.map_size[1] < 500 or request.map_size[1] > 10000):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid map size",
                    "detail": "Map dimensions must be between 500 and 10000 meters",
                    "code": "INVALID_MAP_SIZE"
                }
            )
        
        # Initialize map generator and generate map
        generator = MapGenerator(config)
        generated_map = generator.generate_map(
            include_trees=request.include_trees,
            include_facilities=request.include_facilities if hasattr(request, 'include_facilities') else True,
            include_buildings=getattr(request, 'include_buildings', True)
        )
        
        # Convert to response format
        generation_id = f"gen_{uuid.uuid4().hex[:12]}"
        
        # Build response
        boundary_response = MapBoundaryResponse(**generated_map.boundary.to_dict())
        
        nodes_response = {
            node_id: MapNodeResponse(**node.to_dict())
            for node_id, node in generated_map.nodes.items()
        }
        
        edges_response = {
            edge_id: RoadEdgeResponse(**edge.to_dict())
            for edge_id, edge in generated_map.edges.items()
        }
        
        # Build facilities response (WS-1.3)
        facilities_response = {
            facility_id: FacilityResponse(**facility.to_dict())
            for facility_id, facility in generated_map.facilities.items()
        }
        
        # Build buildings response (WS-1.5)
        buildings_response = {
            building_id: BuildingResponse(**building.to_dict())
            for building_id, building in generated_map.buildings.items()
        }
        
        # Build trees response (WS-1.2)
        trees_response = {}
        tree_stats = None
        if request.include_trees and generated_map.trees:
            trees_response = {
                tree_id: TreeResponse(**tree.to_dict())
                for tree_id, tree in generated_map.trees.items()
            }
            
            # Calculate tree statistics
            from app.core.world_synthesizer.tree_generator import TreeGenerator
            tree_generator = TreeGenerator(config)
            tree_stats = tree_generator.get_generation_stats(generated_map.trees)
        
        # Calculate facility statistics (WS-1.3)
        facility_stats = None
        if generated_map.facilities:
            from app.core.world_synthesizer.facility_generator import FacilityGenerator
            facility_generator = FacilityGenerator(config)
            facility_stats = facility_generator.get_generation_stats(generated_map.facilities)
        
        # Calculate population statistics (WS-1.5)
        population_stats = None
        if generated_map.buildings:
            from app.core.world_synthesizer.building_generator import BuildingGenerator
            building_generator = BuildingGenerator(config)
            population_stats = building_generator.calculate_population_statistics(generated_map.buildings)
        
        # Calculate road type counts
        main_road_count = sum(1 for edge in generated_map.edges.values() 
                             if edge.road_type == "main")
        secondary_road_count = sum(1 for edge in generated_map.edges.values() 
                                  if edge.road_type == "secondary")
        
        response = WorldGenerationResponse(
            generation_id=generation_id,
            generated_at=datetime.utcnow(),
            boundary=boundary_response,
            nodes=nodes_response,
            edges=edges_response,
            trees=trees_response,
            facilities=facilities_response,
            buildings=buildings_response,
            node_count=len(generated_map.nodes),
            edge_count=len(generated_map.edges),
            tree_count=len(generated_map.trees),
            facility_count=len(generated_map.facilities),
            building_count=len(generated_map.buildings),
            main_road_count=main_road_count,
            secondary_road_count=secondary_road_count,
            tree_stats=tree_stats,
            facility_stats=facility_stats,
            population_stats=population_stats,
            generation_config=config
        )
        
        # Store world data for simulation use
        from app.api.endpoints.simulation import set_world_state
        world_data = {
            "generation_id": generation_id,
            "nodes": {node_id: node.to_dict() for node_id, node in generated_map.nodes.items()},
            "edges": {edge_id: edge.to_dict() for edge_id, edge in generated_map.edges.items()},
            "trees": {tree_id: tree.to_dict() for tree_id, tree in generated_map.trees.items()},
            "facilities": {facility_id: facility.to_dict() for facility_id, facility in generated_map.facilities.items()},
            "buildings": {building_id: building.to_dict() for building_id, building in generated_map.buildings.items()},
            "boundary": generated_map.boundary.to_dict(),
            "generated_at": datetime.utcnow().isoformat(),
            "config": config
        }
        set_world_state(generation_id, world_data)
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"World generation error: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "World generation failed",
                "detail": f"An error occurred during map generation: {str(e)}",
                "code": "GENERATION_ERROR"
            }
        )


@router.get(
    "/world/config/defaults",
    summary="Get Default Configuration",
    description="Returns the default configuration parameters for world generation"
)
async def get_default_config():
    """
    Get default configuration parameters for world generation.
    
    Returns:
        Dict: Default configuration values
    """
    return {
        "map_size": [2000, 2000],
        "road_density": 0.7,
        "main_road_count": 4,
        "secondary_road_density": 0.5,
        "main_road_width": 12.0,
        "secondary_road_width": 6.0,
        "main_road_lanes": 4,
        "secondary_road_lanes": 2,
        "main_road_speed_limit": 70.0,
        "secondary_road_speed_limit": 40.0,
        # Tree generation defaults (WS-1.2)
        "include_trees": True,
        "tree_spacing": 25.0,
        "tree_max_offset": 8.0,
        "vulnerability_distribution": {
            "I": 0.1,
            "II": 0.3,
            "III": 0.6
        },
        # Facility generation defaults (WS-1.3)
        "include_facilities": True,
        "ambulance_stations": 3,
        "shelters": 8,
        "shelter_capacity_range": [100, 1000],
        # Building generation defaults (WS-1.5)
        "include_buildings": True,
        "building_density": 0.3,
        "min_building_distance": 25.0,
        "road_buffer_distance": 15.0,
        "building_type_weights": {
            "residential": 0.6,
            "commercial": 0.2,
            "mixed": 0.15,
            "industrial": 0.05
        }
    }