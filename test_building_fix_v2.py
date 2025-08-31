#!/usr/bin/env python3
"""
Enhanced test script to validate the building generation overlap fix.

This script demonstrates the building generation with the new footprint-aware
positioning logic that prevents buildings from overlapping with roads.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.world_synthesizer.building_generator import BuildingGenerator
from app.core.world_synthesizer.map_generator import MapGenerator
from app.schemas.request import WorldGenerationRequest
from shapely.ops import unary_union

def test_building_generation():
    """Test the building generation with enhanced overlap prevention."""
    print("Testing building generation with enhanced overlap prevention...")
    
    # Create test configuration with stricter settings
    config_request = WorldGenerationRequest(
        map_size=[2000, 2000],
        road_density=0.5,
        building_density=0.3,
        vulnerability_distribution={'I': 0.1, 'II': 0.3, 'III': 0.6},  # Required for tree generation
        config_override={
            'seed': 12345,
            'road_buffer_distance': 15.0,  # 15m buffer beyond road width
            'min_building_distance': 25.0
        }
    )
    
    # Convert to dict format for generators
    config = config_request.model_dump()
    config.update(config.get('config_override', {}))
    
    # Generate map first
    print("Generating map...")
    map_generator = MapGenerator(config)
    map_data = map_generator.generate_map()
    print(f"Generated map with {len(map_data.nodes)} nodes and {len(map_data.edges)} edges")
    
    # Print road width information for analysis
    road_widths = [edge.width for edge in map_data.edges.values()]
    print(f"Road widths: min={min(road_widths):.1f}m, max={max(road_widths):.1f}m, avg={sum(road_widths)/len(road_widths):.1f}m")
    print(f"Total road buffer = road_width/2 + {config.get('road_buffer_distance', 15.0)}m")
    
    # Generate buildings
    print("Generating buildings with enhanced overlap prevention...")
    building_generator = BuildingGenerator(config)
    buildings = building_generator.generate_buildings_for_map(map_data)
    
    print(f"Generated {len(buildings)} buildings")
    
    # Enhanced validation of building placement
    print("Performing detailed overlap validation...")
    overlap_count = 0
    overlap_details = []
    
    # Create road exclusion zones using exact same logic as generation
    exclusion_zones = building_generator._create_exclusion_zones(map_data)
    merged_exclusions = unary_union(exclusion_zones)
    
    print(f"Created {len(exclusion_zones)} exclusion zones")
    
    for building_id, building in buildings.items():
        # Create building polygon (exact same as used in generation)
        building_polygon = building_generator._calculate_building_footprint_polygon(
            building.x, building.y, building.footprint_area
        )
        
        # Check if building polygon intersects with merged exclusion zones
        if merged_exclusions.intersects(building_polygon):
            overlap_count += 1
            
            # Find which specific road/facility it overlaps with
            for i, zone in enumerate(exclusion_zones):
                if zone.intersects(building_polygon):
                    # Calculate overlap area
                    intersection = zone.intersection(building_polygon)
                    overlap_area = intersection.area if hasattr(intersection, 'area') else 0
                    
                    # Calculate building footprint side length for reference
                    side_length = (building.footprint_area ** 0.5)
                    
                    overlap_details.append({
                        'building_id': building_id,
                        'building_center': (building.x, building.y),
                        'building_area': building.footprint_area,
                        'building_side_length': side_length,
                        'overlap_area': overlap_area,
                        'zone_index': i
                    })
                    
                    print(f"❌ Building {building_id[:8]}... at ({building.x:.1f}, {building.y:.1f}) "
                          f"(side={side_length:.1f}m) overlaps with exclusion zone {i} by {overlap_area:.2f} sq meters")
                    break
    
    print(f"\nOverlap validation complete: {overlap_count} buildings with overlaps out of {len(buildings)} total")
    
    if overlap_details:
        print("\nDetailed overlap analysis:")
        for detail in overlap_details[:10]:  # Show first 10 overlaps for debugging
            print(f"  Building at ({detail['building_center'][0]:.1f}, {detail['building_center'][1]:.1f}): "
                  f"side={detail['building_side_length']:.1f}m, overlap={detail['overlap_area']:.2f} sq meters")
    
    # Generate statistics
    stats = building_generator.calculate_population_statistics(buildings)
    print("\nBuilding statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return len(buildings), overlap_count

def analyze_road_coverage():
    """Analyze road coverage and buffer zones for debugging."""
    print("\n" + "="*60)
    print("ROAD COVERAGE ANALYSIS")
    print("="*60)
    
    config_request = WorldGenerationRequest(
        map_size=[2000, 2000],
        road_density=0.5,
        building_density=0.3,
        vulnerability_distribution={'I': 0.1, 'II': 0.3, 'III': 0.6},
        config_override={
            'seed': 12345,
            'road_buffer_distance': 15.0,
            'min_building_distance': 25.0
        }
    )
    config = config_request.model_dump()
    config.update(config.get('config_override', {}))
    
    map_generator = MapGenerator(config)
    map_data = map_generator.generate_map()
    building_generator = BuildingGenerator(config)
    
    # Analyze exclusion zones coverage
    exclusion_zones = building_generator._create_exclusion_zones(map_data)
    merged_exclusions = unary_union(exclusion_zones)
    
    # Calculate total exclusion area
    map_size = config.get('map_size', [2000, 2000])
    total_map_area = map_size[0] * map_size[1]
    exclusion_area = merged_exclusions.area
    exclusion_percentage = (exclusion_area / total_map_area) * 100
    
    print(f"Total map area: {total_map_area:,.0f} sq meters")
    print(f"Total exclusion area: {exclusion_area:,.0f} sq meters ({exclusion_percentage:.1f}%)")
    print(f"Available building area: {total_map_area - exclusion_area:,.0f} sq meters ({100 - exclusion_percentage:.1f}%)")
    
    # Analyze individual roads
    print(f"\nIndividual road analysis (showing first 5 roads):")
    road_buffer_distance = config.get('road_buffer_distance', 15.0)
    for i, (edge_id, edge) in enumerate(list(map_data.edges.items())[:5]):
        from_node = map_data.nodes[edge.from_node]
        to_node = map_data.nodes[edge.to_node]
        
        road_length = ((to_node.x - from_node.x)**2 + (to_node.y - from_node.y)**2)**0.5
        total_buffer = (edge.width / 2) + road_buffer_distance
        road_exclusion_area = exclusion_zones[i].area
        
        print(f"  Road {i+1}: length={road_length:.1f}m, width={edge.width:.1f}m, "
              f"buffer={total_buffer:.1f}m, exclusion_area={road_exclusion_area:.0f} sq meters")

if __name__ == "__main__":
    buildings_count, overlaps = test_building_generation()
    
    # Run additional analysis
    analyze_road_coverage()
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    if overlaps == 0:
        print(f"✅ SUCCESS: All {buildings_count} buildings are properly positioned without overlapping roads!")
    else:
        print(f"❌ FAILURE: {overlaps} buildings still overlap with roads out of {buildings_count} total")
        print(f"   Overlap rate: {(overlaps/buildings_count)*100:.2f}%")
        sys.exit(1)