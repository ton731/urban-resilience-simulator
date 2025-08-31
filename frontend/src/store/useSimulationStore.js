import { create } from 'zustand';
import { worldAPI, simulationAPI } from '../api/apiClient';

/**
 * Zustand store for managing simulation state
 * 
 * This store handles all global state related to:
 * - World generation configuration
 * - Generated map data
 * - UI state (loading, errors, etc.)
 * - Layer visibility settings
 */
const useSimulationStore = create((set, get) => ({
  // World Generation State
  mapData: null,
  generationConfig: {
    map_size: [2000, 2000],
    road_density: 0.7,
    main_road_count: 4,
    secondary_road_density: 0.5,
    // Tree generation parameters (WS-1.2)
    include_trees: true,
    tree_spacing: 25.0,
    tree_max_offset: 8.0,
    vulnerability_distribution: {
      I: 0.1,
      II: 0.3,
      III: 0.6
    },
    // Facility generation parameters (WS-1.3)
    include_facilities: true,
    ambulance_stations: 3,
    shelters: 8,
    shelter_capacity_range: [100, 1000],
    // Building generation parameters (WS-1.5)
    include_buildings: true,
    building_density: 0.3
  },
  defaultConfig: null,
  
  // UI State
  isLoading: false,
  error: null,
  lastGeneratedAt: null,
  
  // Layer Visibility
  layerVisibility: {
    nodes: true,
    mainRoads: true,
    secondaryRoads: true,
    edges: true,
    trees: true,
    treesByVulnerability: {
      I: true,   // High risk trees
      II: true,  // Medium risk trees
      III: true  // Low risk trees
    },
    facilities: true,
    ambulanceStations: true,
    shelters: true,
    buildings: true,
    buildingsByType: {
      residential: true,
      commercial: true,
      mixed: true,
      industrial: true
    }
  },
  
  // Statistics
  mapStats: null,
  
  // Disaster Simulation State (SE-2.1)
  disasterSimulationData: null,
  disasterIntensity: 5.0,
  isRunningSimulation: false,
  simulationError: null,
  lastSimulationAt: null,
  
  // Disaster visualization layers
  disasterLayerVisibility: {
    collapsedTrees: true,
    treeBlockages: true,
    roadObstructions: true,
    servicePath: false,
    serviceArea: false
  },

  // Route Planning State (SE-2.2)
  routePlanning: {
    startPoint: null,
    endPoint: null,
    vehicleType: 'car', // car, truck, motorcycle, bicycle, emergency
    isSettingStartPoint: false,
    isSettingEndPoint: false,
    isCalculatingRoute: false,
    routeError: null,
    
    // Route results
    preDisasterRoute: null,    // Route without disaster effects
    postDisasterRoute: null,   // Route with disaster effects
    alternativeRoutes: [],     // Alternative routes
    routeStats: null,          // Route comparison statistics
    
    // Advanced options
    maxTravelTime: 600, // Maximum travel time in seconds (10 minutes)
    findAlternatives: false,
    showRouteComparison: true
  },

  // Route visualization layers
  routeLayerVisibility: {
    startMarker: true,
    endMarker: true,
    preDisasterRoute: true,
    postDisasterRoute: true,
    alternativeRoutes: false,
    routeInfo: true
  },

  // Actions
  
  /**
   * Update generation configuration
   * @param {Object} newConfig - New configuration parameters
   */
  updateConfig: (newConfig) => set((state) => ({
    generationConfig: { ...state.generationConfig, ...newConfig }
  })),

  /**
   * Load default configuration from API
   */
  loadDefaultConfig: async () => {
    try {
      set({ isLoading: true, error: null });
      const defaultConfig = await worldAPI.getDefaultConfig();
      set({ 
        defaultConfig,
        generationConfig: { ...defaultConfig },
        isLoading: false 
      });
    } catch (error) {
      set({ 
        error: `Failed to load default configuration: ${error.message}`,
        isLoading: false 
      });
    }
  },

  /**
   * Generate new world map
   */
  generateWorld: async () => {
    const { generationConfig } = get();
    
    try {
      set({ isLoading: true, error: null });
      console.log('🗺️ Generating world with config:', generationConfig);
      
      const mapData = await worldAPI.generateWorld(generationConfig);
      
      // Calculate statistics
      const mapStats = {
        totalNodes: mapData.node_count,
        totalEdges: mapData.edge_count,
        totalTrees: mapData.tree_count || 0,
        totalFacilities: mapData.facility_count || 0,
        totalBuildings: mapData.building_count || 0,
        mainRoads: mapData.main_road_count,
        secondaryRoads: mapData.secondary_road_count,
        mapSize: `${mapData.boundary.width}m × ${mapData.boundary.height}m`,
        generationId: mapData.generation_id,
        treeStats: mapData.tree_stats || null,
        facilityStats: mapData.facility_stats || null,
        populationStats: mapData.population_stats || null,
        buildingsByType: mapData.building_stats?.by_type || null,
        totalPopulation: mapData.population_stats?.total_population || 0,
        populationDensity: mapData.population_stats?.population_density || 0
      };

      set({ 
        mapData,
        mapStats,
        lastGeneratedAt: new Date(mapData.generated_at),
        isLoading: false,
        error: null
      });

      console.log('✅ World generation completed:', mapStats);
      return mapData;
      
    } catch (error) {
      const errorMessage = error.message || 'Unknown error occurred';
      set({ 
        error: errorMessage,
        isLoading: false 
      });
      console.error('❌ World generation failed:', error);
      throw error;
    }
  },

  /**
   * Clear generated map data
   */
  clearMapData: () => set({
    mapData: null,
    mapStats: null,
    lastGeneratedAt: null,
    error: null
  }),

  /**
   * Toggle layer visibility
   * @param {string} layerName - Name of layer to toggle
   */
  toggleLayer: (layerName) => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      [layerName]: !state.layerVisibility[layerName]
    }
  })),

  /**
   * Set layer visibility
   * @param {string} layerName - Name of layer
   * @param {boolean} visible - Whether layer should be visible
   */
  setLayerVisibility: (layerName, visible) => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      [layerName]: visible
    }
  })),

  /**
   * Reset all layers to visible
   */
  resetLayerVisibility: () => set({
    layerVisibility: {
      nodes: true,
      mainRoads: true,
      secondaryRoads: true,
      edges: true,
      trees: true,
      treesByVulnerability: {
        I: true,
        II: true,
        III: true
      },
      facilities: true,
      ambulanceStations: true,
      shelters: true,
      buildings: true,
      buildingsByType: {
        residential: true,
        commercial: true,
        mixed: true,
        industrial: true
      }
    }
  }),

  /**
   * Clear error state
   */
  clearError: () => set({ error: null }),

  /**
   * Reset configuration to defaults
   */
  resetConfig: () => {
    const { defaultConfig } = get();
    if (defaultConfig) {
      set({ generationConfig: { ...defaultConfig } });
    }
  },

  /**
   * Get configuration for display
   */
  getDisplayConfig: () => {
    const { generationConfig } = get();
    return {
      'Map Size': `${generationConfig.map_size[0]} × ${generationConfig.map_size[1]} meters`,
      'Road Density': `${(generationConfig.road_density * 100).toFixed(0)}%`,
      'Main Roads': generationConfig.main_road_count,
      'Secondary Road Density': `${(generationConfig.secondary_road_density * 100).toFixed(0)}%`,
      'Trees Enabled': generationConfig.include_trees ? 'Yes' : 'No',
      'Tree Spacing': `${generationConfig.tree_spacing}m`,
      'Tree Max Offset': `${generationConfig.tree_max_offset}m`,
      'Facilities Enabled': generationConfig.include_facilities ? 'Yes' : 'No',
      'Ambulance Stations': generationConfig.ambulance_stations,
      'Shelters': generationConfig.shelters,
      'Buildings Enabled': generationConfig.include_buildings ? 'Yes' : 'No',
      'Building Density': `${(generationConfig.building_density * 100).toFixed(0)}%`
    };
  },

  /**
   * Toggle tree vulnerability level visibility
   * @param {string} level - Vulnerability level (I, II, III)
   */
  toggleTreeVulnerability: (level) => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      treesByVulnerability: {
        ...state.layerVisibility.treesByVulnerability,
        [level]: !state.layerVisibility.treesByVulnerability[level]
      }
    }
  })),

  /**
   * Update vulnerability distribution
   * @param {Object} distribution - New vulnerability distribution
   */
  updateVulnerabilityDistribution: (distribution) => set((state) => ({
    generationConfig: {
      ...state.generationConfig,
      vulnerability_distribution: distribution
    }
  })),

  /**
   * Toggle facility visibility
   * @param {string} facilityType - Facility type (ambulanceStations, shelters)  
   */
  toggleFacilityType: (facilityType) => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      [facilityType]: !state.layerVisibility[facilityType]
    }
  })),

  /**
   * Update facility configuration
   * @param {Object} facilityConfig - New facility configuration
   */
  updateFacilityConfig: (facilityConfig) => set((state) => ({
    generationConfig: {
      ...state.generationConfig,
      ...facilityConfig
    }
  })),

  /**
   * Toggle building visibility
   */
  toggleBuildings: () => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      buildings: !state.layerVisibility.buildings
    }
  })),

  /**
   * Toggle building type visibility
   * @param {string} buildingType - Building type (residential, commercial, mixed, industrial)
   */
  toggleBuildingType: (buildingType) => set((state) => ({
    layerVisibility: {
      ...state.layerVisibility,
      buildingsByType: {
        ...state.layerVisibility.buildingsByType,
        [buildingType]: !state.layerVisibility.buildingsByType[buildingType]
      }
    }
  })),

  /**
   * Update building configuration
   * @param {Object} buildingConfig - New building configuration
   */
  updateBuildingConfig: (buildingConfig) => set((state) => ({
    generationConfig: {
      ...state.generationConfig,
      ...buildingConfig
    }
  })),

  // Disaster Simulation Actions (SE-2.1)

  /**
   * Set disaster intensity
   * @param {number} intensity - Disaster intensity (1.0-10.0)
   */
  setDisasterIntensity: (intensity) => set({ disasterIntensity: intensity }),

  /**
   * Run disaster simulation
   */
  runDisasterSimulation: async () => {
    const { mapData, disasterIntensity } = get();
    
    if (!mapData) {
      set({ simulationError: '請先生成地圖才能執行災害模擬' });
      return;
    }

    try {
      set({ 
        isRunningSimulation: true, 
        simulationError: null,
        disasterSimulationData: null 
      });
      
      console.log('🔥 Starting disaster simulation with intensity:', disasterIntensity);
      
      const simulationConfig = {
        world_generation_id: mapData.generation_id,
        disaster_intensity: disasterIntensity,
        random_seed: Math.floor(Math.random() * 1000000), // Random seed for varied results
        include_minor_debris: false
      };
      
      const simulationResult = await simulationAPI.runDisasterSimulation(simulationConfig);
      
      set({
        disasterSimulationData: simulationResult,
        lastSimulationAt: new Date(),
        isRunningSimulation: false,
        simulationError: null
      });
      
      console.log('✅ Disaster simulation completed:', simulationResult);
      return simulationResult;
      
    } catch (error) {
      const errorMessage = error.message || 'Unknown error occurred';
      set({
        simulationError: errorMessage,
        isRunningSimulation: false
      });
      console.error('❌ Disaster simulation failed:', error);
      throw error;
    }
  },

  /**
   * Clear disaster simulation data
   */
  clearDisasterSimulation: () => set({
    disasterSimulationData: null,
    simulationError: null,
    lastSimulationAt: null
  }),

  /**
   * Toggle disaster layer visibility
   * @param {string} layerName - Name of disaster layer to toggle
   */
  toggleDisasterLayer: (layerName) => set((state) => ({
    disasterLayerVisibility: {
      ...state.disasterLayerVisibility,
      [layerName]: !state.disasterLayerVisibility[layerName]
    }
  })),

  /**
   * Set disaster layer visibility
   * @param {string} layerName - Name of disaster layer
   * @param {boolean} visible - Whether layer should be visible
   */
  setDisasterLayerVisibility: (layerName, visible) => set((state) => ({
    disasterLayerVisibility: {
      ...state.disasterLayerVisibility,
      [layerName]: visible
    }
  })),

  /**
   * Get disaster simulation statistics for display
   */
  getDisasterStats: () => {
    const { disasterSimulationData } = get();
    if (!disasterSimulationData) return null;
    
    return {
      '災害強度': `${disasterSimulationData.simulation_config.disaster_intensity}/10`,
      '倒塌樹木總數': disasterSimulationData.total_trees_affected,
      '受影響道路': disasterSimulationData.total_roads_affected,
      '道路阻塞長度': `${disasterSimulationData.total_blocked_road_length.toFixed(1)}m`,
      '平均阻塞率': `${disasterSimulationData.average_road_blockage_percentage.toFixed(1)}%`,
      '高風險樹木倒塌': disasterSimulationData.trees_affected_by_level.I || 0,
      '中風險樹木倒塌': disasterSimulationData.trees_affected_by_level.II || 0,
      '低風險樹木倒塌': disasterSimulationData.trees_affected_by_level.III || 0
    };
  },

  /**
   * Clear all simulation-related errors
   */
  clearSimulationError: () => set({ simulationError: null }),

  // Route Planning Actions (SE-2.2)

  /**
   * Set route planning start point
   * @param {Array} point - [longitude, latitude] coordinates
   */
  setRouteStartPoint: (point) => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      startPoint: point,
      isSettingStartPoint: false
    }
  })),

  /**
   * Set route planning end point
   * @param {Array} point - [longitude, latitude] coordinates  
   */
  setRouteEndPoint: (point) => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      endPoint: point,
      isSettingEndPoint: false
    }
  })),

  /**
   * Enable start point selection mode
   */
  enableStartPointSelection: () => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      isSettingStartPoint: true,
      isSettingEndPoint: false
    }
  })),

  /**
   * Enable end point selection mode
   */
  enableEndPointSelection: () => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      isSettingStartPoint: false,
      isSettingEndPoint: true
    }
  })),

  /**
   * Clear route planning waypoints
   */
  clearRoutePoints: () => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      startPoint: null,
      endPoint: null,
      isSettingStartPoint: false,
      isSettingEndPoint: false,
      preDisasterRoute: null,
      postDisasterRoute: null,
      alternativeRoutes: [],
      routeStats: null,
      routeError: null
    }
  })),

  /**
   * Set vehicle type for route planning
   * @param {string} vehicleType - Vehicle type (car, truck, motorcycle, etc.)
   */
  setRouteVehicleType: (vehicleType) => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      vehicleType
    }
  })),

  /**
   * Set maximum travel time
   * @param {number} maxTime - Maximum travel time in seconds
   */
  setMaxTravelTime: (maxTime) => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      maxTravelTime: maxTime
    }
  })),

  /**
   * Calculate route between start and end points
   */
  calculateRoute: async () => {
    const { mapData, disasterSimulationData, routePlanning } = get();
    
    if (!mapData) {
      set((state) => ({
        routePlanning: {
          ...state.routePlanning,
          routeError: '請先生成地圖才能計算路線'
        }
      }));
      return;
    }

    if (!routePlanning.startPoint || !routePlanning.endPoint) {
      set((state) => ({
        routePlanning: {
          ...state.routePlanning,
          routeError: '請設定起點和終點'
        }
      }));
      return;
    }

    try {
      set((state) => ({
        routePlanning: {
          ...state.routePlanning,
          isCalculatingRoute: true,
          routeError: null,
          preDisasterRoute: null,
          postDisasterRoute: null,
          alternativeRoutes: [],
          routeStats: null
        }
      }));

      console.log('🚗 Calculating route from', routePlanning.startPoint, 'to', routePlanning.endPoint);

      const pathRequest = {
        world_generation_id: mapData.generation_id,
        start_point: routePlanning.startPoint,
        end_point: routePlanning.endPoint,
        vehicle_type: routePlanning.vehicleType,
        max_travel_time: routePlanning.maxTravelTime,
        find_alternatives: routePlanning.findAlternatives,
        simulation_id: null // Pre-disaster route first
      };

      // Calculate pre-disaster route
      const preDisasterRoute = await simulationAPI.findPath(pathRequest);
      console.log('✅ Pre-disaster route calculated:', preDisasterRoute);

      let postDisasterRoute = null;
      let routeStats = null;

      // Calculate post-disaster route if disaster simulation exists
      if (disasterSimulationData) {
        const postDisasterRequest = {
          ...pathRequest,
          simulation_id: disasterSimulationData.simulation_id
        };

        postDisasterRoute = await simulationAPI.findPath(postDisasterRequest);
        console.log('✅ Post-disaster route calculated:', postDisasterRoute);

        // Calculate route comparison statistics
        if (preDisasterRoute.success && postDisasterRoute.success) {
          routeStats = {
            distanceIncrease: postDisasterRoute.total_distance - preDisasterRoute.total_distance,
            timeIncrease: postDisasterRoute.estimated_travel_time - preDisasterRoute.estimated_travel_time,
            distanceIncreasePercent: ((postDisasterRoute.total_distance - preDisasterRoute.total_distance) / preDisasterRoute.total_distance) * 100,
            timeIncreasePercent: ((postDisasterRoute.estimated_travel_time - preDisasterRoute.estimated_travel_time) / preDisasterRoute.estimated_travel_time) * 100,
            blockedRoadsCount: postDisasterRoute.blocked_roads ? postDisasterRoute.blocked_roads.length : 0
          };
        }
      }

      // Calculate alternative routes if requested
      let alternativeRoutes = [];
      if (routePlanning.findAlternatives && preDisasterRoute.success) {
        try {
          const alternativesResponse = await simulationAPI.findAlternativePaths(pathRequest, 2, 1.5);
          alternativeRoutes = alternativesResponse.alternatives || [];
          console.log('✅ Alternative routes calculated:', alternativeRoutes.length);
        } catch (error) {
          console.warn('⚠️ Could not calculate alternative routes:', error.message);
        }
      }

      set((state) => ({
        routePlanning: {
          ...state.routePlanning,
          preDisasterRoute,
          postDisasterRoute,
          alternativeRoutes,
          routeStats,
          isCalculatingRoute: false,
          routeError: null
        }
      }));

      return { preDisasterRoute, postDisasterRoute, routeStats, alternativeRoutes };

    } catch (error) {
      const errorMessage = error.message || 'Route calculation failed';
      set((state) => ({
        routePlanning: {
          ...state.routePlanning,
          routeError: errorMessage,
          isCalculatingRoute: false
        }
      }));
      console.error('❌ Route calculation failed:', error);
      throw error;
    }
  },

  /**
   * Toggle route layer visibility
   * @param {string} layerName - Name of route layer to toggle
   */
  toggleRouteLayer: (layerName) => set((state) => ({
    routeLayerVisibility: {
      ...state.routeLayerVisibility,
      [layerName]: !state.routeLayerVisibility[layerName]
    }
  })),

  /**
   * Set route layer visibility
   * @param {string} layerName - Name of route layer
   * @param {boolean} visible - Whether layer should be visible
   */
  setRouteLayerVisibility: (layerName, visible) => set((state) => ({
    routeLayerVisibility: {
      ...state.routeLayerVisibility,
      [layerName]: visible
    }
  })),

  /**
   * Toggle find alternatives setting
   */
  toggleFindAlternatives: () => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      findAlternatives: !state.routePlanning.findAlternatives
    }
  })),

  /**
   * Toggle route comparison display
   */
  toggleRouteComparison: () => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      showRouteComparison: !state.routePlanning.showRouteComparison
    }
  })),

  /**
   * Get route planning statistics for display
   */
  getRouteStats: () => {
    const { routePlanning } = get();
    
    if (!routePlanning.routeStats) return null;
    
    const stats = routePlanning.routeStats;
    
    return {
      '距離變化': `${stats.distanceIncrease > 0 ? '+' : ''}${stats.distanceIncrease.toFixed(1)}m (${stats.distanceIncreasePercent > 0 ? '+' : ''}${stats.distanceIncreasePercent.toFixed(1)}%)`,
      '時間變化': `${stats.timeIncrease > 0 ? '+' : ''}${stats.timeIncrease.toFixed(1)}s (${stats.timeIncreasePercent > 0 ? '+' : ''}${stats.timeIncreasePercent.toFixed(1)}%)`,
      '受阻道路數': `${stats.blockedRoadsCount}條`,
      '車輛類型': routePlanning.vehicleType,
      '最大旅行時間': `${routePlanning.maxTravelTime}秒`
    };
  },

  /**
   * Clear route planning error
   */
  clearRouteError: () => set((state) => ({
    routePlanning: {
      ...state.routePlanning,
      routeError: null
    }
  }))
}));

export default useSimulationStore;