import { create } from 'zustand';
import { worldAPI } from '../api/apiClient';

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
    shelter_capacity_range: [100, 1000]
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
    shelters: true
  },
  
  // Statistics
  mapStats: null,

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
        mainRoads: mapData.main_road_count,
        secondaryRoads: mapData.secondary_road_count,
        mapSize: `${mapData.boundary.width}m × ${mapData.boundary.height}m`,
        generationId: mapData.generation_id,
        treeStats: mapData.tree_stats || null,
        facilityStats: mapData.facility_stats || null
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
      shelters: true
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
      'Shelters': generationConfig.shelters
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
  }))
}));

export default useSimulationStore;