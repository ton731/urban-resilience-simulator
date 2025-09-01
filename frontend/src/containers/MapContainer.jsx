import React, { useEffect, useRef } from 'react';
import useSimulationStore from '../store/useSimulationStore';
import mapService from '../services/mapService';

const MapContainer = () => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  
  const { 
    mapData, 
    layerVisibility, 
    isLoading,
    disasterSimulationData,
    disasterLayerVisibility,
    isRunningSimulation,
    // Route planning state
    routePlanning,
    routeLayerVisibility,
    // Route planning actions
    setRouteStartPoint,
    setRouteEndPoint
  } = useSimulationStore();

  // Initialize map on component mount
  useEffect(() => {
    if (mapRef.current && !mapInstanceRef.current) {
      try {
        console.log('🗺️ Initializing map...');
        mapInstanceRef.current = mapService.initializeMap(mapRef.current, {
          center: [0, 0],
          zoom: 13
        });
        console.log('✅ Map initialized successfully');
      } catch (error) {
        console.error('❌ Failed to initialize map:', error);
      }
    }

    // Cleanup on unmount
    return () => {
      if (mapInstanceRef.current) {
        mapService.destroy();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update map when mapData changes
  useEffect(() => {
    if (mapData && mapInstanceRef.current) {
      try {
        console.log('🗺️ Updating map with new data...');
        mapService.updateMapData(mapData);
        console.log('✅ Map updated successfully');
        
        // Clear previous route data when new map is loaded
        mapService.clearAllRoutes();
      } catch (error) {
        console.error('❌ Failed to update map:', error);
      }
    }
  }, [mapData]);

  // Update layer visibility when settings change
  useEffect(() => {
    if (mapInstanceRef.current) {
      Object.entries(layerVisibility).forEach(([layerName, visible]) => {
        if (layerName === 'treesByVulnerability') {
          // Handle tree vulnerability level visibility
          Object.entries(visible).forEach(([level, levelVisible]) => {
            const levelLayerName = `treesLevel${level}`;
            mapService.toggleLayer(levelLayerName, levelVisible);
          });
        } else if (layerName === 'buildingsByType') {
          // Handle building type visibility
          Object.entries(visible).forEach(([buildingType, typeVisible]) => {
            const typeLayerName = `buildings${buildingType.charAt(0).toUpperCase() + buildingType.slice(1)}`;
            mapService.toggleLayer(typeLayerName, typeVisible);
          });
        } else {
          mapService.toggleLayer(layerName, visible);
        }
      });
    }
  }, [layerVisibility]);

  // Update map with disaster simulation data
  useEffect(() => {
    if (disasterSimulationData && mapInstanceRef.current) {
      try {
        console.log('🔥 Updating map with disaster simulation data...');
        mapService.updateDisasterData(disasterSimulationData);
        console.log('✅ Disaster simulation visualization updated successfully');
      } catch (error) {
        console.error('❌ Failed to update disaster visualization:', error);
      }
    }
  }, [disasterSimulationData]);

  // Update disaster layer visibility when settings change
  useEffect(() => {
    if (mapInstanceRef.current && disasterSimulationData) {
      Object.entries(disasterLayerVisibility).forEach(([layerName, visible]) => {
        mapService.toggleDisasterLayer(layerName, visible);
      });
    }
  }, [disasterLayerVisibility, disasterSimulationData]);

  // Handle route waypoint setting interactions
  useEffect(() => {
    if (mapInstanceRef.current && mapData) {
      if (routePlanning.isSettingStartPoint || routePlanning.isSettingEndPoint) {
        // Set up map click handler for waypoint selection
        const handleWaypointClick = (worldCoords, latLng) => {
          if (routePlanning.isSettingStartPoint) {
            setRouteStartPoint(worldCoords);
          } else if (routePlanning.isSettingEndPoint) {
            setRouteEndPoint(worldCoords);
          }
        };
        
        mapService.setRouteWaypointClickHandler(handleWaypointClick);
      } else {
        // Remove click handler when not setting waypoints
        mapService.removeRouteWaypointClickHandler();
      }
    }
    
    // Cleanup on unmount or when setting mode changes
    return () => {
      if (mapInstanceRef.current) {
        mapService.removeRouteWaypointClickHandler();
      }
    };
  }, [routePlanning.isSettingStartPoint, routePlanning.isSettingEndPoint, mapData, setRouteStartPoint, setRouteEndPoint]);

  // Update route waypoints visualization
  useEffect(() => {
    if (mapInstanceRef.current && mapData) {
      mapService.updateRouteWaypoints(routePlanning.startPoint, routePlanning.endPoint);
    }
  }, [routePlanning.startPoint, routePlanning.endPoint, mapData]);

  // Update route visualization
  useEffect(() => {
    if (mapInstanceRef.current && mapData && 
        (routePlanning.preDisasterRoute || routePlanning.postDisasterRoute)) {
      const routeData = {
        preDisasterRoute: routePlanning.preDisasterRoute,
        postDisasterRoute: routePlanning.postDisasterRoute,
        routeStats: routePlanning.routeStats
      };
      
      mapService.updateRouteVisualization(routeData);
    }
  }, [
    routePlanning.preDisasterRoute, 
    routePlanning.postDisasterRoute, 
    routePlanning.routeStats,
    mapData
  ]);

  // Update route layer visibility
  useEffect(() => {
    if (mapInstanceRef.current) {
      Object.entries(routeLayerVisibility).forEach(([layerName, visible]) => {
        mapService.toggleRouteLayer(layerName, visible);
      });
    }
  }, [routeLayerVisibility]);

  return (
    <div className="relative flex-1 bg-gray-100">
      {/* Loading Overlay */}
      {(isLoading || isRunningSimulation) && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg flex items-center space-x-3">
            <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-lg font-medium text-gray-900">
              {isLoading ? '生成地圖中...' : isRunningSimulation ? '災害模擬中...' : '處理中...'}
            </span>
          </div>
        </div>
      )}

      {/* Map Container */}
      <div 
        ref={mapRef} 
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />

      {/* Map Info Overlay */}
      {!mapData && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center p-8 bg-white bg-opacity-90 rounded-lg shadow-md">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              城市韌性模擬平台
            </h3>
            <p className="text-gray-600 mb-4">
              使用左側控制面板生成地圖以開始模擬
            </p>
            <p className="text-sm text-gray-500">
              Urban Resilience Simulation Platform<br/>
              Generate a map using the control panel to start simulation
            </p>
          </div>
        </div>
      )}

      {/* Legend */}
      {mapData && (
        <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-md text-sm">
          <h4 className="font-medium mb-2">圖例 Legend</h4>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-3 bg-black border border-black"></div>
              <span>道路 Roads</span>
            </div>
            {mapData && mapData.facility_count > 0 && (
              <>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '20px',
                    height: '20px', 
                    backgroundColor: '#dc2626',
                    border: '2px solid #7f1d1d',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px'
                  }}>🚑</div>
                  <span>救護車起點 Ambulance Stations</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '20px',
                    height: '20px',
                    backgroundColor: '#059669', 
                    border: '2px solid #064e3b',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px'
                  }}>🏠</div>
                  <span>避難所 Shelters</span>
                </div>
              </>
            )}
            {mapData && mapData.tree_count > 0 && (
              <>
                <div className="flex items-center space-x-2">
                  <div style={{ 
                    width: '12px', 
                    height: '12px', 
                    background: '#cc6600',
                    borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
                    position: 'relative'
                  }}>
                    <div style={{
                      position: 'absolute',
                      bottom: '-2px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: '2px',
                      height: '4px',
                      background: '#8b4513'
                    }}></div>
                  </div>
                  <span>樹木-高風險 Trees Level I</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{ 
                    width: '12px', 
                    height: '12px', 
                    background: '#ff8c00',
                    borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
                    position: 'relative'
                  }}>
                    <div style={{
                      position: 'absolute',
                      bottom: '-2px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: '2px',
                      height: '4px',
                      background: '#654321'
                    }}></div>
                  </div>
                  <span>樹木-中風險 Trees Level II</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{ 
                    width: '12px', 
                    height: '12px', 
                    background: '#228B22',
                    borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
                    position: 'relative'
                  }}>
                    <div style={{
                      position: 'absolute',
                      bottom: '-2px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: '2px',
                      height: '4px',
                      background: '#8b4513'
                    }}></div>
                  </div>
                  <span>樹木-低風險 Trees Level III</span>
                </div>
              </>
            )}
            {mapData && mapData.building_count > 0 && (
              <>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '16px',
                    height: '16px', 
                    backgroundColor: '#3b82f6',
                    border: '2px solid #1e40af',
                    borderRadius: '3px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px'
                  }}>🏘️</div>
                  <span>住宅建築 Residential</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '18px',
                    height: '18px', 
                    backgroundColor: '#f59e0b',
                    border: '2px solid #d97706',
                    borderRadius: '3px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px'
                  }}>🏢</div>
                  <span>商業建築 Commercial</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '17px',
                    height: '17px', 
                    backgroundColor: '#8b5cf6',
                    border: '2px solid #7c3aed',
                    borderRadius: '3px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px'
                  }}>🏬</div>
                  <span>混合建築 Mixed Use</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '19px',
                    height: '19px', 
                    backgroundColor: '#6b7280',
                    border: '2px solid #4b5563',
                    borderRadius: '3px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px'
                  }}>🏭</div>
                  <span>工業建築 Industrial</span>
                </div>
              </>
            )}
            
            {/* Disaster Simulation Legend */}
            {disasterSimulationData && (
              <>
                <div className="border-t border-gray-300 pt-2 mt-2">
                  <h5 className="font-medium mb-1 text-orange-800">🔥 災害模擬結果</h5>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '20px',
                    height: '3px',
                    background: '#8B4513',
                    borderRadius: '2px'
                  }}></div>
                  <span>倒塌樹木 Collapsed Trees</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '12px',
                    height: '12px',
                    background: '#8FBC8F',
                    border: '2px solid #654321',
                    borderRadius: '50%'
                  }}></div>
                  <span>樹冠 Tree Crowns</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '16px',
                    height: '16px',
                    background: 'rgba(255, 107, 107, 0.3)',
                    border: '2px dashed #FF6B6B'
                  }}></div>
                  <span>樹木阻塞區域 Tree Blockage</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div style={{
                    width: '16px',
                    height: '16px',
                    background: 'rgba(255, 68, 68, 0.5)',
                    border: '3px dashed #FF4444'
                  }}></div>
                  <span>道路阻塞 Road Obstructions</span>
                </div>
                <div className="text-xs text-orange-700 mt-1">
                  總計 {disasterSimulationData.total_trees_affected} 棵樹倒塌，
                  {disasterSimulationData.total_roads_affected} 條道路受影響
                </div>
              </>
            )}

            {/* Route Planning Legend */}
            {(routePlanning.preDisasterRoute || routePlanning.postDisasterRoute) && (
              <>
                <div className="border-t border-gray-300 pt-2 mt-2">
                  <h5 className="font-medium mb-1 text-blue-800">🗺️ 路線規劃結果</h5>
                  <p className="text-xs text-gray-600 mb-2">
                    注意：所有道路現在都是灰色，路徑會以綠色(災前)和紅色(災後)清楚顯示
                  </p>
                </div>
                {(routePlanning.startPoint || routePlanning.endPoint) && (
                  <>
                    <div className="flex items-center space-x-2">
                      <div style={{
                        width: '20px',
                        height: '20px',
                        backgroundColor: '#10b981',
                        border: '3px solid white',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                      }}>🟢</div>
                      <span>起點 Start Point</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div style={{
                        width: '20px',
                        height: '20px',
                        backgroundColor: '#ef4444',
                        border: '3px solid white',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                      }}>🔴</div>
                      <span>終點 End Point</span>
                    </div>
                  </>
                )}
                {routePlanning.preDisasterRoute?.success && (
                  <div className="flex items-center space-x-2">
                    <div style={{
                      width: '20px',
                      height: '4px',
                      background: '#10b981',
                      borderRadius: '2px'
                    }}></div>
                    <span>災前路徑 Pre-disaster Route (綠色)</span>
                  </div>
                )}
                {routePlanning.postDisasterRoute?.success && (
                  <div className="flex items-center space-x-2">
                    <div style={{
                      width: '20px',
                      height: '4px',
                      background: '#ef4444',
                      borderRadius: '2px'
                    }}></div>
                    <span>災後路徑 Post-disaster Route (紅色)</span>
                  </div>
                )}

                {routePlanning.routeStats && (
                  <div className="text-xs text-blue-700 mt-1">
                    車輛: {routePlanning.vehicleType} |
                    {routePlanning.routeStats.distanceIncrease !== undefined && (
                      <> 距離變化: {routePlanning.routeStats.distanceIncrease > 0 ? '+' : ''}{routePlanning.routeStats.distanceIncrease.toFixed(0)}m</>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapContainer;