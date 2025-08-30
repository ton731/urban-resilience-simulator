import axios from 'axios';

// API Configuration
const API_BASE_URL = 'http://0.0.0.0:8000';
const API_V1_PREFIX = '/api/v1';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_V1_PREFIX}`,
  timeout: 30000, // 30 seconds for map generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('🔥 API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('🔥 API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// World Generation API
export const worldAPI = {
  /**
   * Generate a new world map with roads, trees, and facilities
   * @param {Object} config - World generation configuration (WS-1.1 + WS-1.2 + WS-1.3)
   * @returns {Promise} - API response with generated map data including trees and facilities
   */
  generateWorld: async (config) => {
    try {
      const response = await apiClient.post('/world/generate', config);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to generate world: ${error.response?.data?.detail?.error || error.message}`);
    }
  },

  /**
   * Get default configuration parameters
   * @returns {Promise} - Default configuration object
   */
  getDefaultConfig: async () => {
    try {
      const response = await apiClient.get('/world/config/defaults');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get default config: ${error.response?.data?.detail?.error || error.message}`);
    }
  }
};

// Disaster Simulation API (SE-2.1)
export const simulationAPI = {
  /**
   * Run disaster simulation on a generated world
   * @param {Object} config - Disaster simulation configuration
   * @returns {Promise} - API response with disaster simulation results
   */
  runDisasterSimulation: async (config) => {
    try {
      const response = await apiClient.post('/simulation/disaster', config);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to run disaster simulation: ${error.response?.data?.detail || error.message}`);
    }
  },

  /**
   * Find path between two points with vehicle constraints
   * @param {Object} pathRequest - Pathfinding request
   * @returns {Promise} - Path result
   */
  findPath: async (pathRequest) => {
    try {
      const response = await apiClient.post('/simulation/pathfinding', pathRequest);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to find path: ${error.response?.data?.detail || error.message}`);
    }
  },

  /**
   * Calculate service area from a center point
   * @param {Object} serviceAreaRequest - Service area request
   * @returns {Promise} - Service area result
   */
  calculateServiceArea: async (serviceAreaRequest) => {
    try {
      const response = await apiClient.post('/simulation/service-area', serviceAreaRequest);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to calculate service area: ${error.response?.data?.detail || error.message}`);
    }
  },

  /**
   * Get list of all simulation results
   * @returns {Promise} - List of simulations
   */
  getSimulations: async () => {
    try {
      const response = await apiClient.get('/simulation/simulations');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get simulations: ${error.response?.data?.detail || error.message}`);
    }
  },

  /**
   * Get detailed results for a specific simulation
   * @param {string} simulationId - Simulation ID
   * @returns {Promise} - Simulation result details
   */
  getSimulationResult: async (simulationId) => {
    try {
      const response = await apiClient.get(`/simulation/simulation/${simulationId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get simulation result: ${error.response?.data?.detail || error.message}`);
    }
  }
};

// Health check API
export const healthAPI = {
  /**
   * Check API health status
   * @returns {Promise} - Health status
   */
  checkHealth: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }
};

export default apiClient;