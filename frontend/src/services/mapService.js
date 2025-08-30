import L from 'leaflet';

// Fix for default markers in React-Leaflet
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

/**
 * MapService - Encapsulates all Leaflet.js interactions
 * 
 * This service handles all direct DOM manipulations and Leaflet-specific
 * operations, keeping them separate from React components.
 */
class MapService {
  constructor() {
    this.map = null;
    this.layers = {
      nodes: null,
      edges: null,
      mainRoads: null,
      secondaryRoads: null,
      trees: null,
      treesLevelI: null,
      treesLevelII: null,
      treesLevelIII: null
    };
    this.currentMapData = null;
  }

  /**
   * Initialize the map instance
   * @param {HTMLElement} container - DOM element to contain the map
   * @param {Object} options - Map initialization options
   */
  initializeMap(container, options = {}) {
    const defaultOptions = {
      center: [0, 0],
      zoom: 13,
      zoomControl: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      dragging: true
    };

    this.map = L.map(container, { ...defaultOptions, ...options });

    // Add a simple tile layer (we'll replace this with our generated roads)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
      opacity: 0.3 // Make it semi-transparent so our roads are more visible
    }).addTo(this.map);

    // Initialize layer groups
    this.layers.nodes = L.layerGroup().addTo(this.map);
    this.layers.edges = L.layerGroup().addTo(this.map);
    this.layers.mainRoads = L.layerGroup().addTo(this.map);
    this.layers.secondaryRoads = L.layerGroup().addTo(this.map);
    this.layers.trees = L.layerGroup().addTo(this.map);
    this.layers.treesLevelI = L.layerGroup().addTo(this.map);
    this.layers.treesLevelII = L.layerGroup().addTo(this.map);
    this.layers.treesLevelIII = L.layerGroup().addTo(this.map);

    return this.map;
  }

  /**
   * Update map with generated world data
   * @param {Object} mapData - Generated map data from backend
   */
  updateMapData(mapData) {
    if (!this.map) {
      console.error('Map not initialized');
      return;
    }

    this.currentMapData = mapData;
    this.clearAllLayers();
    
    // Convert backend coordinates to Leaflet LatLng
    // Backend uses meters, we need to convert to lat/lng for display
    const { boundary, nodes, edges, trees = {} } = mapData;
    
    // Calculate center and bounds
    const centerX = (boundary.min_x + boundary.max_x) / 2;
    const centerY = (boundary.min_y + boundary.max_y) / 2;
    
    // Convert meters to approximate lat/lng (rough conversion for visualization)
    const metersToLat = 1 / 111000; // Approximate meters per degree latitude
    const metersToLng = 1 / 111000; // Approximate meters per degree longitude (varies by latitude)
    
    // Convert all nodes to lat/lng
    const convertedNodes = {};
    Object.entries(nodes).forEach(([nodeId, node]) => {
      const lat = (node.y - centerY) * metersToLat;
      const lng = (node.x - centerX) * metersToLng;
      convertedNodes[nodeId] = { ...node, lat, lng };
    });

    // Add nodes to map
    this.addNodes(convertedNodes);
    
    // Add edges (roads) to map
    this.addEdges(edges, convertedNodes);
    
    // Add trees to map (WS-1.2)
    if (trees && Object.keys(trees).length > 0) {
      this.addTrees(trees, centerX, centerY, metersToLat, metersToLng);
    }
    
    // Fit map to show all data
    this.fitMapToBounds(boundary, metersToLat, metersToLng);
  }

  /**
   * Add road network nodes to the map
   * @param {Object} nodes - Node data with lat/lng coordinates
   */
  addNodes(nodes) {
    Object.entries(nodes).forEach(([nodeId, node]) => {
      const marker = L.circleMarker([node.lat, node.lng], {
        radius: 4,
        fillColor: node.type === 'intersection' ? '#ff7800' : '#0078ff',
        color: '#000',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
      });

      marker.bindPopup(`
        <div>
          <strong>Node: ${nodeId}</strong><br/>
          Type: ${node.type}<br/>
          Coordinates: (${node.x.toFixed(1)}, ${node.y.toFixed(1)})
        </div>
      `);

      this.layers.nodes.addLayer(marker);
    });
  }

  /**
   * Add road network edges to the map
   * @param {Object} edges - Edge data
   * @param {Object} nodes - Node data with coordinates
   */
  addEdges(edges, nodes) {
    Object.entries(edges).forEach(([edgeId, edge]) => {
      const fromNode = nodes[edge.from_node];
      const toNode = nodes[edge.to_node];

      if (!fromNode || !toNode) {
        console.warn(`Missing nodes for edge ${edgeId}`);
        return;
      }

      const coordinates = [
        [fromNode.lat, fromNode.lng],
        [toNode.lat, toNode.lng]
      ];

      const isMainRoad = edge.road_type === 'main';
      const roadOptions = {
        color: isMainRoad ? '#ff0000' : '#0000ff',
        weight: isMainRoad ? 6 : 3,
        opacity: 0.8,
        dashArray: isMainRoad ? null : '5, 5'
      };

      const road = L.polyline(coordinates, roadOptions);
      
      road.bindPopup(`
        <div>
          <strong>Road: ${edgeId}</strong><br/>
          Type: ${edge.road_type}<br/>
          Width: ${edge.width}m<br/>
          Lanes: ${edge.lanes}<br/>
          Speed Limit: ${edge.speed_limit} km/h<br/>
          Bidirectional: ${edge.is_bidirectional ? 'Yes' : 'No'}
        </div>
      `);

      // Add to appropriate layer
      if (isMainRoad) {
        this.layers.mainRoads.addLayer(road);
      } else {
        this.layers.secondaryRoads.addLayer(road);
      }
      
      this.layers.edges.addLayer(road);
    });
  }

  /**
   * Fit map view to show generated data
   * @param {Object} boundary - Map boundary data
   * @param {number} metersToLat - Conversion factor
   * @param {number} metersToLng - Conversion factor
   */
  fitMapToBounds(boundary, metersToLat, metersToLng) {
    const centerX = (boundary.min_x + boundary.max_x) / 2;
    const centerY = (boundary.min_y + boundary.max_y) / 2;
    
    const bounds = [
      [(boundary.min_y - centerY) * metersToLat, (boundary.min_x - centerX) * metersToLng],
      [(boundary.max_y - centerY) * metersToLat, (boundary.max_x - centerX) * metersToLng]
    ];

    this.map.fitBounds(bounds, { padding: [20, 20] });
  }

  /**
   * Add trees to the map with vulnerability-based styling (WS-1.2)
   * @param {Object} trees - Tree data from backend
   * @param {number} centerX - Map center X coordinate
   * @param {number} centerY - Map center Y coordinate
   * @param {number} metersToLat - Conversion factor for latitude
   * @param {number} metersToLng - Conversion factor for longitude
   */
  addTrees(trees, centerX, centerY, metersToLat, metersToLng) {
    Object.entries(trees).forEach(([treeId, tree]) => {
      // Convert tree coordinates to lat/lng
      const lat = (tree.y - centerY) * metersToLat;
      const lng = (tree.x - centerX) * metersToLng;

      // Define tree styling based on vulnerability level
      const treeStyles = {
        'I': {   // High vulnerability - Red
          fillColor: '#dc2626',
          color: '#7f1d1d',
          radius: 4,
          weight: 2
        },
        'II': {  // Medium vulnerability - Orange
          fillColor: '#ea580c',
          color: '#9a3412',
          radius: 3,
          weight: 2
        },
        'III': { // Low vulnerability - Green
          fillColor: '#16a34a',
          color: '#14532d',
          radius: 2.5,
          weight: 1.5
        }
      };

      const style = treeStyles[tree.vulnerability_level] || treeStyles['III'];

      // Create tree marker
      const treeMarker = L.circleMarker([lat, lng], {
        ...style,
        opacity: 1,
        fillOpacity: 0.8
      });

      // Create detailed popup
      treeMarker.bindPopup(`
        <div style="font-family: monospace;">
          <strong>🌳 樹木 Tree ${treeId.substring(0, 8)}</strong><br/>
          <hr style="margin: 8px 0;">
          <strong>位置 Position:</strong> (${tree.x.toFixed(1)}, ${tree.y.toFixed(1)})<br/>
          <strong>脆弱度 Vulnerability:</strong> Level ${tree.vulnerability_level}<br/>
          <strong>樹高 Height:</strong> ${tree.height.toFixed(1)}m<br/>
          <strong>樹幹寬度 Trunk Width:</strong> ${tree.trunk_width.toFixed(2)}m<br/>
          <hr style="margin: 8px 0;">
          <small style="color: #666;">
            ${tree.vulnerability_level === 'I' ? '⚠️ 高風險 High Risk' : 
              tree.vulnerability_level === 'II' ? '⚡ 中風險 Medium Risk' : 
              '✅ 低風險 Low Risk'}
          </small>
        </div>
      `);

      // Add to appropriate layers
      this.layers.trees.addLayer(treeMarker);
      
      // Add to vulnerability-specific layers for filtering
      if (tree.vulnerability_level === 'I') {
        this.layers.treesLevelI.addLayer(treeMarker);
      } else if (tree.vulnerability_level === 'II') {
        this.layers.treesLevelII.addLayer(treeMarker);
      } else {
        this.layers.treesLevelIII.addLayer(treeMarker);
      }
    });
  }

  /**
   * Clear all map layers
   */
  clearAllLayers() {
    Object.values(this.layers).forEach(layer => {
      if (layer) {
        layer.clearLayers();
      }
    });
  }

  /**
   * Toggle layer visibility
   * @param {string} layerName - Name of layer to toggle
   * @param {boolean} visible - Whether layer should be visible
   */
  toggleLayer(layerName, visible) {
    const layer = this.layers[layerName];
    if (!layer) return;

    if (visible && !this.map.hasLayer(layer)) {
      this.map.addLayer(layer);
    } else if (!visible && this.map.hasLayer(layer)) {
      this.map.removeLayer(layer);
    }
  }

  /**
   * Get map statistics including trees
   * @returns {Object} - Map statistics
   */
  getMapStats() {
    if (!this.currentMapData) return null;

    const { nodes, edges, trees = {} } = this.currentMapData;
    const mainRoads = Object.values(edges).filter(edge => edge.road_type === 'main');
    const secondaryRoads = Object.values(edges).filter(edge => edge.road_type === 'secondary');

    // Tree statistics by vulnerability level
    const treesByLevel = { I: 0, II: 0, III: 0 };
    Object.values(trees).forEach(tree => {
      treesByLevel[tree.vulnerability_level] = (treesByLevel[tree.vulnerability_level] || 0) + 1;
    });

    return {
      totalNodes: Object.keys(nodes).length,
      totalEdges: Object.keys(edges).length,
      totalTrees: Object.keys(trees).length,
      mainRoads: mainRoads.length,
      secondaryRoads: secondaryRoads.length,
      averageRoadWidth: Object.values(edges).reduce((sum, edge) => sum + edge.width, 0) / Object.keys(edges).length,
      treesByVulnerability: treesByLevel
    };
  }

  /**
   * Destroy map instance and clean up
   */
  destroy() {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
    this.currentMapData = null;
    this.layers = {
      nodes: null,
      edges: null,
      mainRoads: null,
      secondaryRoads: null,
      trees: null,
      treesLevelI: null,
      treesLevelII: null,
      treesLevelIII: null
    };
  }
}

// Export singleton instance
export default new MapService();