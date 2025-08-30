#!/usr/bin/env python3
"""
Demo script for WS-1.1: Procedural Map Generation

This script demonstrates the core functionality of the World Synthesizer
module for procedural map generation without needing to run the full API.
"""

import json
from app.core.world_synthesizer.map_generator import MapGenerator


def demo_basic_map_generation():
    """Demonstrate basic map generation with default settings"""
    print("=== WS-1.1 Demo: Basic Map Generation ===\n")
    
    # Configuration for map generation
    config = {
        "map_size": [1000, 1000],
        "road_density": 0.6,
        "main_road_count": 4,
        "secondary_road_density": 0.4
    }
    
    print(f"Configuration: {json.dumps(config, indent=2)}")
    print("\nGenerating map...")
    
    # Create map generator and generate map
    generator = MapGenerator(config)
    generated_map = generator.generate_map()
    
    # Display results
    print(f"\n✅ Map Generation Complete!")
    print(f"Map boundary: {generated_map.boundary.width}m × {generated_map.boundary.height}m")
    print(f"Total nodes: {len(generated_map.nodes)}")
    print(f"Total edges: {len(generated_map.edges)}")
    
    # Count road types
    main_roads = sum(1 for edge in generated_map.edges.values() if edge.road_type == "main")
    secondary_roads = sum(1 for edge in generated_map.edges.values() if edge.road_type == "secondary")
    
    print(f"Main roads: {main_roads}")
    print(f"Secondary roads: {secondary_roads}")
    
    # Show network graph stats
    if generated_map.graph:
        print(f"NetworkX graph nodes: {generated_map.graph.number_of_nodes()}")
        print(f"NetworkX graph edges: {generated_map.graph.number_of_edges()}")
        print(f"Is connected: {len(list(nx.connected_components(generated_map.graph))) == 1}")
    
    return generated_map


def demo_custom_configuration():
    """Demonstrate map generation with custom configuration"""
    print("\n=== WS-1.1 Demo: Custom Configuration ===\n")
    
    config = {
        "map_size": [1500, 800],  # Rectangular map
        "road_density": 0.8,      # Higher density
        "main_road_count": 6,     # More main roads
        "secondary_road_density": 0.7
    }
    
    print(f"Custom configuration: {json.dumps(config, indent=2)}")
    print("\nGenerating custom map...")
    
    generator = MapGenerator(config)
    generated_map = generator.generate_map()
    
    print(f"\n✅ Custom Map Generation Complete!")
    print(f"Map boundary: {generated_map.boundary.width}m × {generated_map.boundary.height}m")
    print(f"Total nodes: {len(generated_map.nodes)}")
    print(f"Total edges: {len(generated_map.edges)}")
    
    return generated_map


def demo_export_to_json():
    """Demonstrate exporting generated map to JSON format"""
    print("\n=== WS-1.1 Demo: Export to JSON ===\n")
    
    config = {"map_size": [800, 800], "road_density": 0.5}
    generator = MapGenerator(config)
    generated_map = generator.generate_map()
    
    # Convert to dictionary format
    map_data = generated_map.to_dict()
    
    # Save to JSON file
    output_file = "generated_map_demo.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Map data exported to {output_file}")
    print(f"File contains {len(map_data['nodes'])} nodes and {len(map_data['edges'])} edges")
    
    # Show sample node and edge
    if map_data['nodes']:
        sample_node_id = list(map_data['nodes'].keys())[0]
        sample_node = map_data['nodes'][sample_node_id]
        print(f"\nSample node: {json.dumps(sample_node, indent=2)}")
    
    if map_data['edges']:
        sample_edge_id = list(map_data['edges'].keys())[0]
        sample_edge = map_data['edges'][sample_edge_id]
        print(f"\nSample edge: {json.dumps(sample_edge, indent=2)}")


def main():
    """Run all demo functions"""
    try:
        # Import networkx here to handle potential import issues
        import networkx as nx
        globals()['nx'] = nx
        
        demo_basic_map_generation()
        demo_custom_configuration()
        demo_export_to_json()
        
        print("\n🎉 All WS-1.1 demos completed successfully!")
        print("\nTo run the full API server:")
        print("cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies:")
        print("pip install -r requirements.txt")
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()