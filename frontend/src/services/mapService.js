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
      treesLevelIII: null,
      facilities: null,
      ambulanceStations: null,
      shelters: null,
      buildings: null,
      buildingsResidential: null,
      buildingsCommercial: null,
      buildingsMixed: null,
      buildingsIndustrial: null,
      // Disaster simulation layers (SE-2.1)
      collapsedTrees: null,
      treeBlockages: null,
      roadObstructions: null,
      servicePath: null,
      serviceArea: null,
      // Route planning layers (SE-2.2)
      routeStartMarker: null,
      routeEndMarker: null,
      preDisasterRoute: null,
      postDisasterRoute: null,
      alternativeRoutes: null,
      routeInfo: null
    };
    this.currentMapData = null;
    this.currentDisasterData = null;
    this.currentRouteData = null;
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

    // Add scale control to show distance measurements
    L.control.scale({
      position: 'bottomright',
      metric: true,
      imperial: false,
      maxWidth: 200
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
    this.layers.facilities = L.layerGroup().addTo(this.map);
    this.layers.ambulanceStations = L.layerGroup().addTo(this.map);
    this.layers.shelters = L.layerGroup().addTo(this.map);
    this.layers.buildings = L.layerGroup().addTo(this.map);
    this.layers.buildingsResidential = L.layerGroup().addTo(this.map);
    this.layers.buildingsCommercial = L.layerGroup().addTo(this.map);
    this.layers.buildingsMixed = L.layerGroup().addTo(this.map);
    this.layers.buildingsIndustrial = L.layerGroup().addTo(this.map);
    
    // Initialize disaster simulation layers (SE-2.1)
    this.layers.collapsedTrees = L.layerGroup().addTo(this.map);
    this.layers.treeBlockages = L.layerGroup().addTo(this.map);
    this.layers.roadObstructions = L.layerGroup().addTo(this.map);
    this.layers.servicePath = L.layerGroup().addTo(this.map);
    this.layers.serviceArea = L.layerGroup().addTo(this.map);

    // Initialize route planning layers (SE-2.2)
    this.layers.routeStartMarker = L.layerGroup().addTo(this.map);
    this.layers.routeEndMarker = L.layerGroup().addTo(this.map);
    this.layers.preDisasterRoute = L.layerGroup().addTo(this.map);
    this.layers.postDisasterRoute = L.layerGroup().addTo(this.map);
    this.layers.alternativeRoutes = L.layerGroup().addTo(this.map);
    this.layers.routeInfo = L.layerGroup().addTo(this.map);

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
    const { boundary, nodes, edges, trees = {}, facilities = {}, buildings = {} } = mapData;
    
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
    
    // Add facilities to map (WS-1.3)
    if (facilities && Object.keys(facilities).length > 0) {
      this.addFacilities(facilities, centerX, centerY, metersToLat, metersToLng);
    }
    
    // Add buildings to map (WS-1.5)
    if (buildings && Object.keys(buildings).length > 0) {
      this.addBuildings(buildings, centerX, centerY, metersToLat, metersToLng);
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
   * Add facilities to the map with distinct styling (WS-1.3)
   * @param {Object} facilities - Facility data from backend
   * @param {number} centerX - Map center X coordinate  
   * @param {number} centerY - Map center Y coordinate
   * @param {number} metersToLat - Conversion factor for latitude
   * @param {number} metersToLng - Conversion factor for longitude
   */
  addFacilities(facilities, centerX, centerY, metersToLat, metersToLng) {
    Object.entries(facilities).forEach(([facilityId, facility]) => {
      // Convert facility coordinates to lat/lng
      const lat = (facility.y - centerY) * metersToLat;
      const lng = (facility.x - centerX) * metersToLng;

      // Create facility marker based on type
      const facilityMarker = this._createFacilityIcon([lat, lng], facility);

      // Create detailed popup
      facilityMarker.bindPopup(`
        <div style="font-family: monospace; min-width: 200px;">
          <strong>${this._getFacilityEmoji(facility.facility_type)} ${facility.name || '未命名設施'}</strong><br/>
          <hr style="margin: 8px 0;">
          <strong>類型 Type:</strong> ${this._getFacilityTypeName(facility.facility_type)}<br/>
          <strong>位置 Position:</strong> (${facility.x.toFixed(1)}, ${facility.y.toFixed(1)})<br/>
          <strong>所在節點 Node:</strong> ${facility.node_id.substring(0, 8)}...<br/>
          ${facility.capacity ? `<strong>容量 Capacity:</strong> ${facility.capacity} 人<br/>` : ''}
          <hr style="margin: 8px 0;">
          <small style="color: #666;">
            ${this._getFacilityDescription(facility.facility_type)}
          </small>
        </div>
      `);

      // Add to appropriate layers
      this.layers.facilities.addLayer(facilityMarker);
      
      // Add to type-specific layers for filtering
      if (facility.facility_type === 'ambulance_station') {
        this.layers.ambulanceStations.addLayer(facilityMarker);
      } else if (facility.facility_type === 'shelter') {
        this.layers.shelters.addLayer(facilityMarker);
      }
    });
  }

  /**
   * Create facility icon based on type
   * @param {Array} position - [lat, lng] position for facility
   * @param {Object} facility - Facility data object
   * @returns {Object} - Leaflet marker with facility icon
   */
  _createFacilityIcon(position, facility) {
    const isAmbulance = facility.facility_type === 'ambulance_station';
    
    // Define facility colors and styles
    const facilityStyles = {
      ambulance_station: {
        backgroundColor: '#dc2626', // Red
        borderColor: '#7f1d1d',
        icon: '🚑',
        size: 24
      },
      shelter: {
        backgroundColor: '#059669', // Green  
        borderColor: '#064e3b',
        icon: '🏠',
        size: 22
      }
    };

    const style = facilityStyles[facility.facility_type] || facilityStyles.shelter;

    const facilityIcon = L.divIcon({
      html: `
        <div style="
          width: ${style.size}px;
          height: ${style.size}px;
          background-color: ${style.backgroundColor};
          border: 2px solid ${style.borderColor};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: ${style.size * 0.6}px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
          position: relative;
        ">
          ${style.icon}
          ${facility.capacity ? `
            <div style="
              position: absolute;
              top: -8px;
              right: -8px;
              background-color: white;
              color: ${style.backgroundColor};
              border: 1px solid ${style.borderColor};
              border-radius: 10px;
              padding: 1px 4px;
              font-size: 10px;
              font-weight: bold;
              min-width: 16px;
              text-align: center;
            ">${facility.capacity}</div>
          ` : ''}
        </div>
      `,
      className: 'facility-icon',
      iconSize: [style.size, style.size],
      iconAnchor: [style.size/2, style.size/2],
      popupAnchor: [0, -style.size/2]
    });

    return L.marker(position, { icon: facilityIcon });
  }

  /**
   * Get facility emoji based on type
   * @param {string} facilityType - Type of facility
   * @returns {string} - Emoji representing the facility
   */
  _getFacilityEmoji(facilityType) {
    const emojis = {
      'ambulance_station': '🚑',
      'shelter': '🏠'
    };
    return emojis[facilityType] || '🏢';
  }

  /**
   * Get facility type display name
   * @param {string} facilityType - Type of facility
   * @returns {string} - Display name for the facility type
   */
  _getFacilityTypeName(facilityType) {
    const names = {
      'ambulance_station': '救護車起點 Ambulance Station',
      'shelter': '避難所 Shelter'
    };
    return names[facilityType] || '未知設施 Unknown Facility';
  }

  /**
   * Get facility description
   * @param {string} facilityType - Type of facility  
   * @returns {string} - Description of the facility
   */
  _getFacilityDescription(facilityType) {
    const descriptions = {
      'ambulance_station': '🚨 緊急救護服務據點',
      'shelter': '⛑️ 災害避難收容場所'
    };
    return descriptions[facilityType] || '城市基礎設施';
  }

  /**
   * Add buildings to the map with type-based styling (WS-1.5)
   * @param {Object} buildings - Building data from backend
   * @param {number} centerX - Map center X coordinate  
   * @param {number} centerY - Map center Y coordinate
   * @param {number} metersToLat - Conversion factor for latitude
   * @param {number} metersToLng - Conversion factor for longitude
   */
  addBuildings(buildings, centerX, centerY, metersToLat, metersToLng) {
    Object.entries(buildings).forEach(([buildingId, building]) => {
      // Convert building coordinates to lat/lng
      const lat = (building.y - centerY) * metersToLat;
      const lng = (building.x - centerX) * metersToLng;

      // Create building marker based on type (now returns rectangle scaled by footprint area)
      const buildingMarker = this._createBuildingIcon([lat, lng], building, metersToLat, metersToLng);

      // Create detailed popup content
      const popupContent = `
        <div style="font-family: monospace; min-width: 240px;">
          <strong>${this._getBuildingEmoji(building.building_type)} ${this._getBuildingTypeName(building.building_type)}</strong><br/>
          <hr style="margin: 8px 0;">
          <strong>位置 Position:</strong> (${building.x.toFixed(1)}, ${building.y.toFixed(1)})<br/>
          <strong>樓高 Height:</strong> ${building.height.toFixed(1)}m<br/>
          <strong>樓層 Floors:</strong> ${building.floors}<br/>
          <strong>佔地面積 Footprint:</strong> ${building.footprint_area.toFixed(0)}m² (${Math.sqrt(building.footprint_area).toFixed(1)}m × ${Math.sqrt(building.footprint_area).toFixed(1)}m)<br/>
          <strong>人口 Population:</strong> ${building.population} 人<br/>
          <strong>容量 Capacity:</strong> ${building.capacity} 人<br/>
          <strong>使用率 Occupancy:</strong> ${((building.population / building.capacity) * 100).toFixed(1)}%<br/>
          <hr style="margin: 8px 0;">
          <small style="color: #666;">
            ${this._getBuildingDescription(building.building_type)}<br/>
            📐 建築物按實際佔地面積等比例顯示
          </small>
        </div>
      `;

      // Bind popup to building marker (works for both single markers and layer groups)
      if (buildingMarker instanceof L.LayerGroup) {
        // For layer groups, bind popup to each layer
        buildingMarker.eachLayer(layer => {
          if (layer instanceof L.Rectangle || layer instanceof L.Marker) {
            layer.bindPopup(popupContent);
          }
        });
      } else {
        // For single markers/rectangles
        buildingMarker.bindPopup(popupContent);
      }

      // Add to appropriate layers
      this.layers.buildings.addLayer(buildingMarker);
      
      // Add to type-specific layers for filtering
      switch(building.building_type) {
        case 'residential':
          this.layers.buildingsResidential.addLayer(buildingMarker);
          break;
        case 'commercial':
          this.layers.buildingsCommercial.addLayer(buildingMarker);
          break;
        case 'mixed':
          this.layers.buildingsMixed.addLayer(buildingMarker);
          break;
        case 'industrial':
          this.layers.buildingsIndustrial.addLayer(buildingMarker);
          break;
      }
    });
  }

  /**
   * Create building rectangle based on footprint area
   * @param {Array} position - [lat, lng] position for building
   * @param {Object} building - Building data object
   * @param {number} metersToLat - Conversion factor for latitude
   * @param {number} metersToLng - Conversion factor for longitude
   * @returns {Object} - Leaflet rectangle representing the building
   */
  _createBuildingIcon(position, building, metersToLat, metersToLng) {
    // Define building colors and styles by type
    const buildingStyles = {
      residential: {
        fillColor: '#3b82f6', // Blue
        color: '#1e40af',
        icon: '🏘️'
      },
      commercial: {
        fillColor: '#f59e0b', // Amber
        color: '#d97706',
        icon: '🏢'
      },
      mixed: {
        fillColor: '#8b5cf6', // Purple
        color: '#7c3aed',
        icon: '🏬'
      },
      industrial: {
        fillColor: '#6b7280', // Gray
        color: '#4b5563',
        icon: '🏭'
      }
    };

    const style = buildingStyles[building.building_type] || buildingStyles.residential;
    
    // Calculate building dimensions based on footprint area
    // Assume building is a square for simplicity: side_length = sqrt(area)
    const sideLength = Math.sqrt(building.footprint_area); // meters
    
    // Convert meters to lat/lng offsets
    const halfSideLat = (sideLength / 2) * metersToLat;
    const halfSideLng = (sideLength / 2) * metersToLng;
    
    // Create rectangle bounds
    const bounds = [
      [position[0] - halfSideLat, position[1] - halfSideLng], // Southwest corner
      [position[0] + halfSideLat, position[1] + halfSideLng]  // Northeast corner
    ];
    
    // Create building rectangle
    const buildingRectangle = L.rectangle(bounds, {
      fillColor: style.fillColor,
      color: style.color,
      fillOpacity: 0.7,
      weight: 2,
      opacity: 0.9
    });

    // Add building icon in the center if the building is large enough
    if (sideLength >= 10) { // Only show icon for buildings >= 10m side length
      // Calculate icon size more proportionally to building size
      // For buildings 10-50m: icon size ranges from 16px to 48px
      const iconSize = Math.min(60, Math.max(24, sideLength * 1.8)); // Icon size based on building size
      
      const centerIcon = L.marker(position, {
        icon: L.divIcon({
          html: `
            <div style="
              width: ${iconSize}px;
              height: ${iconSize}px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: ${iconSize * 0.7}px;
              text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
              pointer-events: none;
            ">
              ${style.icon}
            </div>
          `,
          className: 'building-center-icon',
          iconSize: [iconSize, iconSize],
          iconAnchor: [iconSize/2, iconSize/2]
        })
      });
      
      // Create a layer group containing both rectangle and icon
      const buildingGroup = L.layerGroup([buildingRectangle, centerIcon]);
      
      // Add population indicator if there are people
      if (building.population > 0) {
        const popIndicator = L.marker([position[0] + halfSideLat * 0.7, position[1] + halfSideLng * 0.7], {
          icon: L.divIcon({
            html: `
              <div style="
                background-color: white;
                color: ${style.fillColor};
                border: 2px solid ${style.color};
                border-radius: 10px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                white-space: nowrap;
              ">${building.population > 99 ? '99+' : building.population}人</div>
            `,
            className: 'building-population',
            iconSize: [30, 20],
            iconAnchor: [15, 10]
          })
        });
        
        buildingGroup.addLayer(popIndicator);
      }
      
      return buildingGroup;
    } else {
      // For small buildings, just return the rectangle
      return buildingRectangle;
    }
  }

  /**
   * Get building emoji based on type
   * @param {string} buildingType - Type of building
   * @returns {string} - Emoji representing the building
   */
  _getBuildingEmoji(buildingType) {
    const emojis = {
      'residential': '🏘️',
      'commercial': '🏢',
      'mixed': '🏬',
      'industrial': '🏭'
    };
    return emojis[buildingType] || '🏢';
  }

  /**
   * Get building type display name
   * @param {string} buildingType - Type of building
   * @returns {string} - Display name for the building type
   */
  _getBuildingTypeName(buildingType) {
    const names = {
      'residential': '住宅建築 Residential',
      'commercial': '商業建築 Commercial',
      'mixed': '混合建築 Mixed Use',
      'industrial': '工業建築 Industrial'
    };
    return names[buildingType] || '建築物 Building';
  }

  /**
   * Get building description
   * @param {string} buildingType - Type of building  
   * @returns {string} - Description of the building
   */
  _getBuildingDescription(buildingType) {
    const descriptions = {
      'residential': '🏠 主要用於居住的建築物',
      'commercial': '🛒 商業活動與辦公用途',
      'mixed': '🏘️ 商住混合使用建築',
      'industrial': '⚙️ 工業生產與製造設施'
    };
    return descriptions[buildingType] || '城市建築設施';
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

    const { nodes, edges, trees = {}, facilities = {}, buildings = {} } = this.currentMapData;
    const mainRoads = Object.values(edges).filter(edge => edge.road_type === 'main');
    const secondaryRoads = Object.values(edges).filter(edge => edge.road_type === 'secondary');

    // Tree statistics by vulnerability level
    const treesByLevel = { I: 0, II: 0, III: 0 };
    Object.values(trees).forEach(tree => {
      treesByLevel[tree.vulnerability_level] = (treesByLevel[tree.vulnerability_level] || 0) + 1;
    });

    // Facility statistics by type
    const facilitiesByType = { ambulance_station: 0, shelter: 0 };
    let totalCapacity = 0;
    Object.values(facilities).forEach(facility => {
      facilitiesByType[facility.facility_type] = (facilitiesByType[facility.facility_type] || 0) + 1;
      if (facility.capacity) {
        totalCapacity += facility.capacity;
      }
    });

    // Building statistics by type
    const buildingsByType = { residential: 0, commercial: 0, mixed: 0, industrial: 0 };
    let totalPopulation = 0;
    let totalBuildingCapacity = 0;
    Object.values(buildings).forEach(building => {
      buildingsByType[building.building_type] = (buildingsByType[building.building_type] || 0) + 1;
      totalPopulation += building.population || 0;
      totalBuildingCapacity += building.capacity || 0;
    });

    return {
      totalNodes: Object.keys(nodes).length,
      totalEdges: Object.keys(edges).length,
      totalTrees: Object.keys(trees).length,
      totalFacilities: Object.keys(facilities).length,
      totalBuildings: Object.keys(buildings).length,
      mainRoads: mainRoads.length,
      secondaryRoads: secondaryRoads.length,
      averageRoadWidth: Object.values(edges).reduce((sum, edge) => sum + edge.width, 0) / Object.keys(edges).length,
      treesByVulnerability: treesByLevel,
      facilitiesByType: facilitiesByType,
      totalShelterCapacity: totalCapacity,
      buildingsByType: buildingsByType,
      totalPopulation: totalPopulation,
      totalBuildingCapacity: totalBuildingCapacity,
      populationDensity: totalPopulation / 4.0 // Assuming 2km x 2km = 4 sq km
    };
  }

  // === Disaster Simulation Visualization Methods (SE-2.1) ===

  /**
   * Update map with disaster simulation results
   * @param {Object} disasterData - Disaster simulation result data
   */
  updateDisasterData(disasterData) {
    if (!this.map || !this.currentMapData) {
      console.error('Map or world data not available');
      return;
    }

    this.currentDisasterData = disasterData;
    this.clearDisasterLayers();

    // Get coordinate conversion parameters
    const { boundary } = this.currentMapData;
    const centerX = (boundary.min_x + boundary.max_x) / 2;
    const centerY = (boundary.min_y + boundary.max_y) / 2;
    const metersToLat = 1 / 111000;
    const metersToLng = 1 / 111000;

    // Visualize collapsed trees
    this.addCollapsedTrees(disasterData.disaster_events, centerX, centerY, metersToLat, metersToLng);
    
    // Visualize road obstructions
    this.addRoadObstructions(disasterData.road_obstructions, centerX, centerY, metersToLat, metersToLng);
  }

  /**
   * Add collapsed trees visualization with accurate fallen tree representation
   * @param {Array} disasterEvents - Array of tree collapse events
   * @param {number} centerX - Map center X coordinate
   * @param {number} centerY - Map center Y coordinate  
   * @param {number} metersToLat - Meters to latitude conversion factor
   * @param {number} metersToLng - Meters to longitude conversion factor
   */
  addCollapsedTrees(disasterEvents, centerX, centerY, metersToLat, metersToLng) {
    if (!disasterEvents || disasterEvents.length === 0) return;

    disasterEvents.forEach(event => {
      // Convert tree base position
      const baseLat = (event.location[1] - centerY) * metersToLat;
      const baseLng = (event.location[0] - centerX) * metersToLng;

      // Calculate fallen tree end position
      const angleRad = (event.collapse_angle * Math.PI) / 180;
      const heightInLat = event.tree_height * metersToLat;
      const heightInLng = event.tree_height * metersToLng;
      
      const endLat = baseLat + heightInLat * Math.sin(angleRad);
      const endLng = baseLng + heightInLng * Math.cos(angleRad);

      // Create line representing the fallen tree trunk
      // Calculate appropriate trunk width for visualization (scaled for visibility)
      const trunkWidthPixels = Math.max(3, Math.min(20, event.trunk_width * 8)); // Scale trunk width for visibility
      const fallenTreeLine = L.polyline([[baseLat, baseLng], [endLat, endLng]], {
        color: '#8B4513', // Brown color for tree trunk
        weight: trunkWidthPixels,
        opacity: 0.9,
        lineCap: 'round'
      });

      // Add tree crown circle at the end (using real-world radius in meters)
      const crownRadiusMeters = Math.max(2, event.tree_height * 0.4); // Crown radius based on tree height in meters
      const crownCircle = L.circle([endLat, endLng], {
        color: '#654321',
        fillColor: '#8FBC8F',
        fillOpacity: 0.6,
        radius: crownRadiusMeters, // Leaflet circle radius is in meters when using real coordinates
        weight: 2
      });

      // Add popup with tree information
      const popupContent = `
        <div class="text-sm">
          <strong>🌳 倒塌樹木</strong><br/>
          <strong>樹木ID:</strong> ${event.tree_id}<br/>
          <strong>倒塌角度:</strong> ${event.collapse_angle.toFixed(1)}°<br/>
          <strong>樹高:</strong> ${event.tree_height.toFixed(1)}m<br/>
          <strong>樹幹寬度:</strong> ${event.trunk_width.toFixed(1)}m<br/>
          <strong>脆弱度等級:</strong> ${event.vulnerability_level}<br/>
          <strong>嚴重程度:</strong> ${(event.severity * 100).toFixed(1)}%
        </div>
      `;

      fallenTreeLine.bindPopup(popupContent);
      crownCircle.bindPopup(popupContent);

      // Add to collapsed trees layer
      this.layers.collapsedTrees.addLayer(fallenTreeLine);
      this.layers.collapsedTrees.addLayer(crownCircle);

      // Add blockage polygon visualization
      if (event.blockage_polygon && event.blockage_polygon.length > 0) {
        const blockageCoords = event.blockage_polygon.map(coord => [
          (coord[1] - centerY) * metersToLat,
          (coord[0] - centerX) * metersToLng
        ]);

        const blockagePolygon = L.polygon(blockageCoords, {
          color: '#FF6B6B',
          fillColor: '#FF6B6B',
          fillOpacity: 0.3,
          weight: 2,
          dashArray: '5, 5'
        });

        blockagePolygon.bindPopup(`
          <div class="text-sm">
            <strong>🚧 樹木阻塞區域</strong><br/>
            <strong>造成事件:</strong> ${event.tree_id}<br/>
            <strong>阻塞面積:</strong> 約 ${(event.blockage_polygon.length * 10).toFixed(1)}m²
          </div>
        `);

        this.layers.treeBlockages.addLayer(blockagePolygon);
      }
    });

    console.log(`✅ Added ${disasterEvents.length} collapsed trees to visualization`);
  }

  /**
   * Add road obstruction visualization
   * @param {Array} roadObstructions - Array of road obstruction data
   * @param {number} centerX - Map center X coordinate
   * @param {number} centerY - Map center Y coordinate
   * @param {number} metersToLat - Meters to latitude conversion factor
   * @param {number} metersToLng - Meters to longitude conversion factor
   */
  addRoadObstructions(roadObstructions, centerX, centerY, metersToLat, metersToLng) {
    if (!roadObstructions || roadObstructions.length === 0) return;

    roadObstructions.forEach(obstruction => {
      if (!obstruction.obstruction_polygon || obstruction.obstruction_polygon.length === 0) return;

      // Convert obstruction polygon coordinates
      const obstructionCoords = obstruction.obstruction_polygon.map(coord => [
        (coord[1] - centerY) * metersToLat,
        (coord[0] - centerX) * metersToLng
      ]);

      // Create obstruction visualization
      const obstructionPolygon = L.polygon(obstructionCoords, {
        color: '#FF4444',
        fillColor: '#FF4444',
        fillOpacity: 0.5,
        weight: 3,
        dashArray: '10, 5'
      });

      // Add popup with obstruction information
      const popupContent = `
        <div class="text-sm">
          <strong>🚧 道路阻塞</strong><br/>
          <strong>道路ID:</strong> ${obstruction.road_edge_id}<br/>
          <strong>剩餘寬度:</strong> ${obstruction.remaining_width.toFixed(1)}m<br/>
          <strong>阻塞率:</strong> ${obstruction.blocked_percentage.toFixed(1)}%<br/>
          <strong>造成事件:</strong> ${obstruction.caused_by_event}
        </div>
      `;

      obstructionPolygon.bindPopup(popupContent);
      this.layers.roadObstructions.addLayer(obstructionPolygon);
    });

    console.log(`✅ Added ${roadObstructions.length} road obstructions to visualization`);
  }

  /**
   * Clear all disaster simulation layers
   */
  clearDisasterLayers() {
    ['collapsedTrees', 'treeBlockages', 'roadObstructions', 'servicePath', 'serviceArea'].forEach(layerName => {
      if (this.layers[layerName]) {
        this.layers[layerName].clearLayers();
      }
    });
  }

  /**
   * Toggle disaster layer visibility
   * @param {string} layerName - Name of disaster layer
   * @param {boolean} visible - Whether layer should be visible
   */
  toggleDisasterLayer(layerName, visible) {
    const layer = this.layers[layerName];
    if (!layer) return;

    if (visible && !this.map.hasLayer(layer)) {
      this.map.addLayer(layer);
    } else if (!visible && this.map.hasLayer(layer)) {
      this.map.removeLayer(layer);
    }
  }

  /**
   * Get disaster simulation statistics
   * @returns {Object} - Disaster statistics
   */
  getDisasterStats() {
    if (!this.currentDisasterData) return null;

    return {
      totalCollapsed: this.currentDisasterData.total_trees_affected,
      totalObstructions: this.currentDisasterData.total_roads_affected,
      averageBlockage: this.currentDisasterData.average_road_blockage_percentage,
      collapsedByLevel: this.currentDisasterData.trees_affected_by_level
    };
  }

  // === Route Planning Visualization Methods (SE-2.2) ===

  /**
   * Add route planning waypoint markers
   * @param {Array} startPoint - [lng, lat] coordinates for start point
   * @param {Array} endPoint - [lng, lat] coordinates for end point  
   */
  updateRouteWaypoints(startPoint, endPoint) {
    if (!this.map || !this.currentMapData) return;

    // Clear existing markers
    this.clearRouteWaypoints();

    const { boundary } = this.currentMapData;
    const centerX = (boundary.min_x + boundary.max_x) / 2;
    const centerY = (boundary.min_y + boundary.max_y) / 2;
    const metersToLat = 1 / 111000;
    const metersToLng = 1 / 111000;

    // Add start point marker
    if (startPoint) {
      const startLat = (startPoint[1] - centerY) * metersToLat;
      const startLng = (startPoint[0] - centerX) * metersToLng;
      
      const startMarker = this._createWaypointMarker([startLat, startLng], 'start');
      this.layers.routeStartMarker.addLayer(startMarker);
    }

    // Add end point marker  
    if (endPoint) {
      const endLat = (endPoint[1] - centerY) * metersToLat;
      const endLng = (endPoint[0] - centerX) * metersToLng;
      
      const endMarker = this._createWaypointMarker([endLat, endLng], 'end');
      this.layers.routeEndMarker.addLayer(endMarker);
    }
  }

  /**
   * Create waypoint marker for route planning
   * @param {Array} position - [lat, lng] position
   * @param {string} type - 'start' or 'end'
   * @returns {Object} - Leaflet marker
   */
  _createWaypointMarker(position, type) {
    const isStart = type === 'start';
    const markerColor = isStart ? '#10b981' : '#ef4444'; // Green for start, red for end
    const icon = isStart ? '🟢' : '🔴';
    const label = isStart ? '起點' : '終點';

    const waypointIcon = L.divIcon({
      html: `
        <div style="
          width: 30px;
          height: 30px;
          background-color: ${markerColor};
          border: 3px solid white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.4);
          position: relative;
        ">
          ${icon}
          <div style="
            position: absolute;
            top: 35px;
            left: 50%;
            transform: translateX(-50%);
            background-color: white;
            color: ${markerColor};
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid ${markerColor};
            white-space: nowrap;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
          ">${label}</div>
        </div>
      `,
      className: 'waypoint-marker',
      iconSize: [30, 50],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    });

    const marker = L.marker(position, { icon: waypointIcon });
    
    marker.bindPopup(`
      <div style="font-family: monospace;">
        <strong>🎯 路線${label}</strong><br/>
        <strong>座標:</strong> ${position[0].toFixed(6)}, ${position[1].toFixed(6)}<br/>
        <small>點擊地圖其他位置可重新設定</small>
      </div>
    `);

    return marker;
  }

  /**
   * Clear route waypoint markers
   */
  clearRouteWaypoints() {
    this.layers.routeStartMarker.clearLayers();
    this.layers.routeEndMarker.clearLayers();
  }

  /**
   * Update route visualization with paths
   * @param {Object} routeData - Route planning results
   */
  updateRouteVisualization(routeData) {
    if (!this.map || !this.currentMapData) return;

    this.currentRouteData = routeData;
    this.clearRoutePaths();

    const { boundary } = this.currentMapData;
    const centerX = (boundary.min_x + boundary.max_x) / 2;
    const centerY = (boundary.min_y + boundary.max_y) / 2;
    const metersToLat = 1 / 111000;
    const metersToLng = 1 / 111000;

    // Add pre-disaster route if available
    if (routeData.preDisasterRoute && routeData.preDisasterRoute.success) {
      this.addRouteToMap(
        routeData.preDisasterRoute,
        'preDisaster',
        centerX, centerY, metersToLat, metersToLng
      );
    }

    // Add post-disaster route if available  
    if (routeData.postDisasterRoute && routeData.postDisasterRoute.success) {
      this.addRouteToMap(
        routeData.postDisasterRoute,
        'postDisaster',
        centerX, centerY, metersToLat, metersToLng
      );
    }

    // Add alternative routes if available
    if (routeData.alternativeRoutes && routeData.alternativeRoutes.length > 0) {
      routeData.alternativeRoutes.forEach((altRoute, index) => {
        if (altRoute.success) {
          this.addRouteToMap(
            altRoute,
            'alternative',
            centerX, centerY, metersToLat, metersToLng,
            index
          );
        }
      });
    }

    // Add route comparison info if available
    if (routeData.routeStats) {
      this.addRouteComparisonInfo(routeData.routeStats);
    }
  }

  /**
   * Add single route to map
   * @param {Object} route - Route data
   * @param {string} routeType - 'preDisaster', 'postDisaster', or 'alternative'  
   * @param {number} centerX - Map center X coordinate
   * @param {number} centerY - Map center Y coordinate
   * @param {number} metersToLat - Conversion factor
   * @param {number} metersToLng - Conversion factor
   * @param {number} altIndex - Alternative route index (for alternatives)
   */
  addRouteToMap(route, routeType, centerX, centerY, metersToLat, metersToLng, altIndex = 0) {
    if (!route.path_coordinates || route.path_coordinates.length === 0) return;

    // Convert coordinates
    const routeCoords = route.path_coordinates.map(coord => [
      (coord[1] - centerY) * metersToLat,
      (coord[0] - centerX) * metersToLng
    ]);

    // Define route styles
    const routeStyles = {
      preDisaster: {
        color: '#10b981',
        weight: 6,
        opacity: 0.8,
        dashArray: null,
        name: '災前最佳路徑'
      },
      postDisaster: {
        color: '#ef4444',
        weight: 6,
        opacity: 0.8,
        dashArray: null,
        name: '災後最佳路徑'
      },
      alternative: {
        color: '#8b5cf6',
        weight: 4,
        opacity: 0.6,
        dashArray: '10, 5',
        name: `替代路徑 ${altIndex + 1}`
      }
    };

    const style = routeStyles[routeType];
    
    // Create route polyline
    const routeLine = L.polyline(routeCoords, {
      color: style.color,
      weight: style.weight,
      opacity: style.opacity,
      dashArray: style.dashArray,
      lineCap: 'round',
      lineJoin: 'round'
    });

    // Add route information popup
    const popupContent = `
      <div style="font-family: monospace; min-width: 200px;">
        <strong>🛣️ ${style.name}</strong><br/>
        <hr style="margin: 8px 0;">
        <strong>總距離:</strong> ${route.total_distance.toFixed(1)}m<br/>
        <strong>預計時間:</strong> ${route.estimated_travel_time.toFixed(1)}秒<br/>
        <strong>車輛類型:</strong> ${route.vehicle_type}<br/>
        ${route.blocked_roads && route.blocked_roads.length > 0 ? 
          `<strong>受阻道路:</strong> ${route.blocked_roads.length}條<br/>` : ''
        }
        <hr style="margin: 8px 0;">
        <small style="color: #666;">
          ${routeType === 'preDisaster' ? '💚 不考慮災害影響的路徑' :
            routeType === 'postDisaster' ? '🔴 考慮災害影響的路徑' :
            '🔮 替代路徑選項'}
        </small>
      </div>
    `;

    routeLine.bindPopup(popupContent);

    // Add to appropriate layer
    if (routeType === 'preDisaster') {
      this.layers.preDisasterRoute.addLayer(routeLine);
    } else if (routeType === 'postDisaster') {
      this.layers.postDisasterRoute.addLayer(routeLine);
    } else {
      this.layers.alternativeRoutes.addLayer(routeLine);
    }

    // Add direction arrows for better visualization
    this.addRouteDirectionArrows(routeCoords, style.color, routeType);
  }

  /**
   * Add direction arrows along route
   * @param {Array} routeCoords - Route coordinates
   * @param {string} color - Arrow color
   * @param {string} routeType - Route type for layer assignment
   */
  addRouteDirectionArrows(routeCoords, color, routeType) {
    if (routeCoords.length < 2) return;

    const arrowInterval = Math.max(1, Math.floor(routeCoords.length / 6)); // Show ~6 arrows per route
    
    for (let i = arrowInterval; i < routeCoords.length; i += arrowInterval) {
      const prevCoord = routeCoords[i - 1];
      const currCoord = routeCoords[i];
      
      // Calculate arrow angle
      const angle = Math.atan2(currCoord[0] - prevCoord[0], currCoord[1] - prevCoord[1]) * 180 / Math.PI;
      
      const arrowIcon = L.divIcon({
        html: `
          <div style="
            width: 0;
            height: 0;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-bottom: 12px solid ${color};
            transform: rotate(${angle}deg);
            opacity: 0.8;
          "></div>
        `,
        className: 'route-arrow',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      });

      const arrowMarker = L.marker(currCoord, { icon: arrowIcon });
      
      // Add to same layer as route
      if (routeType === 'preDisaster') {
        this.layers.preDisasterRoute.addLayer(arrowMarker);
      } else if (routeType === 'postDisaster') {
        this.layers.postDisasterRoute.addLayer(arrowMarker);
      } else {
        this.layers.alternativeRoutes.addLayer(arrowMarker);
      }
    }
  }

  /**
   * Add route comparison information overlay
   * @param {Object} routeStats - Route comparison statistics
   */
  addRouteComparisonInfo(routeStats) {
    const infoContent = `
      <div style="
        background: rgba(255, 255, 255, 0.95);
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        font-family: monospace;
        font-size: 12px;
        min-width: 200px;
      ">
        <strong>📊 路徑比較</strong><br/>
        <hr style="margin: 8px 0;">
        <strong>距離變化:</strong> ${routeStats.distanceIncrease > 0 ? '+' : ''}${routeStats.distanceIncrease.toFixed(1)}m<br/>
        <strong>時間變化:</strong> ${routeStats.timeIncrease > 0 ? '+' : ''}${routeStats.timeIncrease.toFixed(1)}秒<br/>
        <strong>受阻道路:</strong> ${routeStats.blockedRoadsCount}條<br/>
        ${routeStats.distanceIncreasePercent !== 0 ? 
          `<strong>距離增加:</strong> ${routeStats.distanceIncreasePercent.toFixed(1)}%<br/>` : ''
        }
        ${routeStats.timeIncreasePercent !== 0 ? 
          `<strong>時間增加:</strong> ${routeStats.timeIncreasePercent.toFixed(1)}%<br/>` : ''
        }
      </div>
    `;

    // Create info control (top-right corner)
    const infoControl = L.control({ position: 'topright' });
    infoControl.onAdd = () => {
      const div = L.DomUtil.create('div', 'route-info-control');
      div.innerHTML = infoContent;
      return div;
    };

    // Remove existing info control if any
    if (this._routeInfoControl) {
      this.map.removeControl(this._routeInfoControl);
    }
    
    this._routeInfoControl = infoControl;
    infoControl.addTo(this.map);
  }

  /**
   * Clear all route paths but keep waypoints  
   */
  clearRoutePaths() {
    ['preDisasterRoute', 'postDisasterRoute', 'alternativeRoutes', 'routeInfo'].forEach(layerName => {
      if (this.layers[layerName]) {
        this.layers[layerName].clearLayers();
      }
    });

    // Remove info control
    if (this._routeInfoControl) {
      this.map.removeControl(this._routeInfoControl);
      this._routeInfoControl = null;
    }
  }

  /**
   * Clear all route-related layers
   */
  clearAllRoutes() {
    ['routeStartMarker', 'routeEndMarker', 'preDisasterRoute', 
     'postDisasterRoute', 'alternativeRoutes', 'routeInfo'].forEach(layerName => {
      if (this.layers[layerName]) {
        this.layers[layerName].clearLayers();
      }
    });

    if (this._routeInfoControl) {
      this.map.removeControl(this._routeInfoControl);
      this._routeInfoControl = null;
    }

    this.currentRouteData = null;
  }

  /**
   * Toggle route layer visibility
   * @param {string} layerName - Name of route layer
   * @param {boolean} visible - Whether layer should be visible
   */
  toggleRouteLayer(layerName, visible) {
    const layer = this.layers[layerName];
    if (!layer) return;

    if (visible && !this.map.hasLayer(layer)) {
      this.map.addLayer(layer);
    } else if (!visible && this.map.hasLayer(layer)) {
      this.map.removeLayer(layer);
    }

    // Handle info control visibility
    if (layerName === 'routeInfo' && this._routeInfoControl) {
      if (visible) {
        this._routeInfoControl.addTo(this.map);
      } else {
        this.map.removeControl(this._routeInfoControl);
      }
    }
  }

  /**
   * Get route planning statistics
   * @returns {Object} - Route statistics 
   */
  getRouteStats() {
    if (!this.currentRouteData) return null;

    const stats = {};
    
    if (this.currentRouteData.preDisasterRoute && this.currentRouteData.preDisasterRoute.success) {
      stats.preDisasterDistance = this.currentRouteData.preDisasterRoute.total_distance;
      stats.preDisasterTime = this.currentRouteData.preDisasterRoute.estimated_travel_time;
    }

    if (this.currentRouteData.postDisasterRoute && this.currentRouteData.postDisasterRoute.success) {
      stats.postDisasterDistance = this.currentRouteData.postDisasterRoute.total_distance;
      stats.postDisasterTime = this.currentRouteData.postDisasterRoute.estimated_travel_time;
    }

    if (this.currentRouteData.routeStats) {
      stats.comparison = this.currentRouteData.routeStats;
    }

    stats.alternativeCount = this.currentRouteData.alternativeRoutes ? 
      this.currentRouteData.alternativeRoutes.length : 0;

    return stats;
  }

  /**
   * Add click handler for waypoint selection
   * @param {Function} onMapClick - Callback function for map clicks
   */
  setRouteWaypointClickHandler(onMapClick) {
    if (this.map && onMapClick) {
      this.map.on('click', (e) => {
        const { boundary } = this.currentMapData || {};
        if (!boundary) return;

        const centerX = (boundary.min_x + boundary.max_x) / 2;
        const centerY = (boundary.min_y + boundary.max_y) / 2;
        const metersToLat = 1 / 111000;
        const metersToLng = 1 / 111000;

        // Convert lat/lng back to world coordinates
        const worldX = centerX + (e.latlng.lng / metersToLng);
        const worldY = centerY + (e.latlng.lat / metersToLat);

        onMapClick([worldX, worldY], e.latlng);
      });
    }
  }

  /**
   * Remove click handler for waypoint selection
   */
  removeRouteWaypointClickHandler() {
    if (this.map) {
      this.map.off('click');
    }
  }

  /**
   * Destroy map instance and clean up
   */
  destroy() {
    // Clean up route info control
    if (this._routeInfoControl && this.map) {
      this.map.removeControl(this._routeInfoControl);
      this._routeInfoControl = null;
    }

    if (this.map) {
      this.map.remove();
      this.map = null;
    }
    
    this.currentMapData = null;
    this.currentDisasterData = null;
    this.currentRouteData = null;
    
    this.layers = {
      nodes: null,
      edges: null,
      mainRoads: null,
      secondaryRoads: null,
      trees: null,
      treesLevelI: null,
      treesLevelII: null,
      treesLevelIII: null,
      facilities: null,
      ambulanceStations: null,
      shelters: null,
      buildings: null,
      buildingsResidential: null,
      buildingsCommercial: null,
      buildingsMixed: null,
      buildingsIndustrial: null,
      // Disaster simulation layers (SE-2.1)
      collapsedTrees: null,
      treeBlockages: null,
      roadObstructions: null,
      servicePath: null,
      serviceArea: null,
      // Route planning layers (SE-2.2)
      routeStartMarker: null,
      routeEndMarker: null,
      preDisasterRoute: null,
      postDisasterRoute: null,
      alternativeRoutes: null,
      routeInfo: null
    };
  }
}

// Export singleton instance
export default new MapService();