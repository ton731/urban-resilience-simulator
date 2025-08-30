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
   * Add road network edges to the map with realistic width rendering
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

      const isMainRoad = edge.road_type === 'main';
      
      // Create road polygon with actual width
      const roadPolygon = this._createRoadPolygon(fromNode, toNode, edge);
      
      // Style based on road type and direction
      const roadOptions = {
        color: isMainRoad ? '#8b0000' : '#00008b', // Darker borders
        fillColor: isMainRoad ? '#ff4444' : '#4444ff',
        fillOpacity: 0.7,
        weight: 2,
        opacity: 0.9
      };

      // Different styling for one-way roads
      if (!edge.is_bidirectional) {
        roadOptions.fillColor = isMainRoad ? '#ff6666' : '#6666ff';
        roadOptions.fillOpacity = 0.5;
        // Add arrow pattern for one-way roads
        roadOptions.dashArray = '10, 5';
      }

      const road = L.polygon(roadPolygon, roadOptions);
      
      // Add direction arrow for one-way roads
      if (!edge.is_bidirectional) {
        const arrowLatLng = this._getArrowPosition(fromNode, toNode);
        const arrow = this._createDirectionArrow(arrowLatLng, this._calculateAngle(fromNode, toNode), isMainRoad);
        
        // Add arrow to the same layer
        if (isMainRoad) {
          this.layers.mainRoads.addLayer(arrow);
        } else {
          this.layers.secondaryRoads.addLayer(arrow);
        }
        this.layers.edges.addLayer(arrow);
      }
      
      road.bindPopup(`
        <div style="font-family: monospace;">
          <strong>🛣️ 道路 Road ${edgeId.substring(0, 8)}</strong><br/>
          <hr style="margin: 8px 0;">
          <strong>類型 Type:</strong> ${edge.road_type === 'main' ? '主幹道 Main' : '次要道路 Secondary'}<br/>
          <strong>寬度 Width:</strong> ${edge.width}m<br/>
          <strong>車道 Lanes:</strong> ${edge.lanes}<br/>
          <strong>速限 Speed Limit:</strong> ${edge.speed_limit} km/h<br/>
          <strong>方向 Direction:</strong> ${edge.is_bidirectional ? '雙向 Bidirectional' : '單向 One-way'}<br/>
          <hr style="margin: 8px 0;">
          <small style="color: #666;">
            ${edge.is_bidirectional ? '⟷ 雙向通行' : '→ 單向通行'}
          </small>
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
   * Create a road polygon with realistic width
   * @param {Object} fromNode - Starting node with lat/lng
   * @param {Object} toNode - Ending node with lat/lng
   * @param {Object} edge - Road edge data with width info
   * @returns {Array} - Array of lat/lng points forming the road polygon
   */
  _createRoadPolygon(fromNode, toNode, edge) {
    // Calculate road direction vector
    const dx = toNode.lng - fromNode.lng;
    const dy = toNode.lat - fromNode.lat;
    const roadLength = Math.sqrt(dx * dx + dy * dy);
    
    // Convert width from meters to approximate degrees
    // (This is a rough approximation for visualization)
    const widthInDegrees = (edge.width / 2) / 111000; // Approximate conversion
    
    // Calculate perpendicular offset
    const offsetX = (-dy / roadLength) * widthInDegrees;
    const offsetY = (dx / roadLength) * widthInDegrees;
    
    // Create road polygon points
    const roadPolygon = [
      [fromNode.lat + offsetY, fromNode.lng + offsetX], // Left side start
      [fromNode.lat - offsetY, fromNode.lng - offsetX], // Right side start
      [toNode.lat - offsetY, toNode.lng - offsetX],     // Right side end
      [toNode.lat + offsetY, toNode.lng + offsetX],     // Left side end
      [fromNode.lat + offsetY, fromNode.lng + offsetX]  // Close polygon
    ];
    
    return roadPolygon;
  }

  /**
   * Create direction arrow for one-way roads
   * @param {Array} position - [lat, lng] position for arrow
   * @param {number} angle - Angle in degrees for arrow direction
   * @param {boolean} isMainRoad - Whether this is a main road
   * @returns {Object} - Leaflet marker with arrow
   */
  _createDirectionArrow(position, angle, isMainRoad) {
    const arrowSize = isMainRoad ? 12 : 8;
    const arrowColor = isMainRoad ? '#ff0000' : '#0000ff';
    
    const arrowIcon = L.divIcon({
      html: `
        <div style="
          width: ${arrowSize}px; 
          height: ${arrowSize}px; 
          background-color: ${arrowColor}; 
          transform: rotate(${angle}deg);
          clip-path: polygon(0 0, 100% 50%, 0 100%);
          border: 1px solid white;
        "></div>
      `,
      className: 'direction-arrow',
      iconSize: [arrowSize, arrowSize],
      iconAnchor: [arrowSize/2, arrowSize/2]
    });

    return L.marker(position, { icon: arrowIcon });
  }

  /**
   * Get position for direction arrow (middle of road)
   * @param {Object} fromNode - Starting node
   * @param {Object} toNode - Ending node
   * @returns {Array} - [lat, lng] for arrow position
   */
  _getArrowPosition(fromNode, toNode) {
    return [
      (fromNode.lat + toNode.lat) / 2,
      (fromNode.lng + toNode.lng) / 2
    ];
  }

  /**
   * Calculate angle between two nodes
   * @param {Object} fromNode - Starting node
   * @param {Object} toNode - Ending node
   * @returns {number} - Angle in degrees
   */
  _calculateAngle(fromNode, toNode) {
    const dx = toNode.lng - fromNode.lng;
    const dy = toNode.lat - fromNode.lat;
    return Math.atan2(dy, dx) * (180 / Math.PI);
  }

  /**
   * Create realistic tree icon
   * @param {Array} position - [lat, lng] position for tree
   * @param {Object} tree - Tree data object
   * @param {number} size - Size of tree icon
   * @returns {Object} - Leaflet marker with tree icon
   */
  _createTreeIcon(position, tree, size) {
    // Tree colors based on vulnerability level
    const treeColors = {
      'I': {   // High vulnerability - Autumn/damaged colors
        crown: '#cc6600',
        trunk: '#8b4513',
        shadow: '#ffcc99'
      },
      'II': {  // Medium vulnerability - Mixed colors
        crown: '#ff8c00',
        trunk: '#654321',
        shadow: '#ffd4aa'
      },
      'III': { // Low vulnerability - Healthy green
        crown: '#228B22',
        trunk: '#8b4513',
        shadow: '#90EE90'
      }
    };

    const colors = treeColors[tree.vulnerability_level] || treeColors['III'];
    const trunkWidth = Math.max(2, size * 0.15);
    const trunkHeight = size * 0.4;
    const crownSize = size * 0.8;

    const treeIcon = L.divIcon({
      html: `
        <div style="position: relative; width: ${size}px; height: ${size}px;">
          <!-- Tree Shadow -->
          <div style="
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: ${crownSize * 1.2}px;
            height: ${crownSize * 0.3}px;
            background: ${colors.shadow};
            border-radius: 50%;
            opacity: 0.3;
            z-index: 1;
          "></div>
          
          <!-- Tree Trunk -->
          <div style="
            position: absolute;
            bottom: ${crownSize * 0.15}px;
            left: 50%;
            transform: translateX(-50%);
            width: ${trunkWidth}px;
            height: ${trunkHeight}px;
            background: ${colors.trunk};
            border-radius: 2px;
            z-index: 2;
          "></div>
          
          <!-- Tree Crown -->
          <div style="
            position: absolute;
            bottom: ${trunkHeight * 0.5}px;
            left: 50%;
            transform: translateX(-50%);
            width: ${crownSize}px;
            height: ${crownSize}px;
            background: ${colors.crown};
            border-radius: 50%;
            border: 1px solid ${colors.crown}dd;
            z-index: 3;
          "></div>
          
          <!-- Tree Crown Highlight -->
          <div style="
            position: absolute;
            bottom: ${trunkHeight * 0.5 + crownSize * 0.6}px;
            left: ${50 + crownSize * 0.15}%;
            transform: translateX(-50%);
            width: ${crownSize * 0.3}px;
            height: ${crownSize * 0.3}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            z-index: 4;
          "></div>
        </div>
      `,
      className: 'tree-icon',
      iconSize: [size, size],
      iconAnchor: [size/2, size],
      popupAnchor: [0, -size]
    });

    return L.marker(position, { icon: treeIcon });
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

      // Create tree marker with realistic tree symbol
      const treeSize = Math.max(8, Math.min(20, tree.height * 0.8)); // Size based on height
      const treeMarker = this._createTreeIcon([lat, lng], tree, treeSize);

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