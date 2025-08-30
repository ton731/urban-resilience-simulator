#!/usr/bin/env node
/**
 * Frontend API Integration Test Script
 * 
 * This script tests the integration between the React frontend and the FastAPI backend
 * by simulating the API calls that the frontend would make.
 */

import axios from 'axios';

// API Configuration
const API_BASE_URL = 'http://0.0.0.0:8000';
const API_V1_PREFIX = '/api/v1';

// Test configuration
const testConfig = {
  map_size: [1500, 1500],
  road_density: 0.6,
  main_road_count: 4,
  secondary_road_density: 0.4
};

console.log('🧪 Frontend API Integration Test');
console.log('=================================\n');

async function testHealthCheck() {
  console.log('1. Testing health check...');
  try {
    const response = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ Health check passed:', response.data);
    return true;
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    return false;
  }
}

async function testGetDefaultConfig() {
  console.log('\n2. Testing default configuration endpoint...');
  try {
    const response = await axios.get(`${API_BASE_URL}${API_V1_PREFIX}/world/config/defaults`);
    console.log('✅ Default config retrieved:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Failed to get default config:', error.response?.data || error.message);
    return null;
  }
}

async function testWorldGeneration() {
  console.log('\n3. Testing world generation endpoint...');
  console.log('📝 Config:', JSON.stringify(testConfig, null, 2));
  
  try {
    const startTime = Date.now();
    const response = await axios.post(
      `${API_BASE_URL}${API_V1_PREFIX}/world/generate`,
      testConfig,
      { timeout: 30000 }
    );
    const endTime = Date.now();
    
    console.log(`✅ World generation completed in ${endTime - startTime}ms`);
    console.log('📊 Generation Summary:');
    console.log(`   - Generation ID: ${response.data.generation_id}`);
    console.log(`   - Map Size: ${response.data.boundary.width}m × ${response.data.boundary.height}m`);
    console.log(`   - Total Nodes: ${response.data.node_count}`);
    console.log(`   - Total Edges: ${response.data.edge_count}`);
    console.log(`   - Main Roads: ${response.data.main_road_count}`);
    console.log(`   - Secondary Roads: ${response.data.secondary_road_count}`);
    
    // Test data structure
    const { nodes, edges } = response.data;
    const sampleNodeId = Object.keys(nodes)[0];
    const sampleEdgeId = Object.keys(edges)[0];
    
    if (sampleNodeId && sampleEdgeId) {
      console.log('\n📋 Sample Data Structure:');
      console.log('   Sample Node:', JSON.stringify(nodes[sampleNodeId], null, 2));
      console.log('   Sample Edge:', JSON.stringify(edges[sampleEdgeId], null, 2));
    }
    
    return response.data;
    
  } catch (error) {
    console.error('❌ World generation failed:', error.response?.data || error.message);
    if (error.response?.data?.detail) {
      console.error('   Error details:', error.response.data.detail);
    }
    return null;
  }
}

async function testErrorHandling() {
  console.log('\n4. Testing error handling...');
  
  const invalidConfig = {
    map_size: [100, 100], // Too small - should trigger error
    road_density: 2.0,    // Invalid value - should trigger error
  };
  
  try {
    await axios.post(
      `${API_BASE_URL}${API_V1_PREFIX}/world/generate`,
      invalidConfig,
      { timeout: 10000 }
    );
    console.log('❌ Error handling test failed - should have thrown an error');
    return false;
  } catch (error) {
    if (error.response && error.response.status >= 400) {
      console.log('✅ Error handling works correctly');
      console.log('   Error response:', error.response.data);
      return true;
    } else {
      console.error('❌ Unexpected error type:', error.message);
      return false;
    }
  }
}

async function simulateFrontendWorkflow() {
  console.log('\n5. Simulating complete frontend workflow...');
  
  try {
    // Step 1: Load default config (like frontend would do on startup)
    const defaultConfig = await testGetDefaultConfig();
    if (!defaultConfig) {
      throw new Error('Failed to load default config');
    }
    
    // Step 2: User adjusts parameters
    const userConfig = {
      ...defaultConfig,
      map_size: [2000, 1200], // User makes it rectangular
      road_density: 0.8,      // User increases density
      main_road_count: 6      // User adds more main roads
    };
    
    console.log('👤 User adjusted config:', JSON.stringify(userConfig, null, 2));
    
    // Step 3: Generate world with user config
    const worldData = await axios.post(
      `${API_BASE_URL}${API_V1_PREFIX}/world/generate`,
      userConfig,
      { timeout: 30000 }
    );
    
    console.log('✅ Complete frontend workflow simulation successful!');
    console.log(`   Final result: ${worldData.data.node_count} nodes, ${worldData.data.edge_count} edges`);
    
    return worldData.data;
    
  } catch (error) {
    console.error('❌ Frontend workflow simulation failed:', error.message);
    return null;
  }
}

async function runAllTests() {
  console.log(`🔗 Testing backend API at: ${API_BASE_URL}\n`);
  
  let allTestsPassed = true;
  
  // Run tests sequentially
  const healthOk = await testHealthCheck();
  if (!healthOk) {
    console.error('\n💥 Backend is not available. Please ensure it\'s running on http://0.0.0.0:8000');
    process.exit(1);
  }
  
  const defaultConfig = await testGetDefaultConfig();
  allTestsPassed = allTestsPassed && (defaultConfig !== null);
  
  const worldData = await testWorldGeneration();
  allTestsPassed = allTestsPassed && (worldData !== null);
  
  const errorHandling = await testErrorHandling();
  allTestsPassed = allTestsPassed && errorHandling;
  
  const workflow = await simulateFrontendWorkflow();
  allTestsPassed = allTestsPassed && (workflow !== null);
  
  // Summary
  console.log('\n' + '='.repeat(50));
  if (allTestsPassed) {
    console.log('🎉 All API integration tests PASSED!');
    console.log('\n✅ The frontend can successfully:');
    console.log('   - Connect to the backend API');
    console.log('   - Retrieve default configuration');
    console.log('   - Generate world maps with custom parameters');
    console.log('   - Handle errors gracefully');
    console.log('   - Complete the full user workflow');
    console.log('\n🚀 Ready to start the React frontend!');
    console.log('   Run: cd frontend && npm install && npm run dev');
  } else {
    console.log('❌ Some API integration tests FAILED!');
    console.log('   Please check the backend implementation and try again.');
    process.exit(1);
  }
}

// Run tests
runAllTests().catch(error => {
  console.error('💥 Test suite failed:', error.message);
  process.exit(1);
});