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
        populationStats: mapData.population_stats || null
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
  clearSimulationError: () => set({ simulationError: null })
}));

export default useSimulationStore;