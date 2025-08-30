import React, { useEffect, useRef } from 'react';
import useSimulationStore from '../store/useSimulationStore';
import mapService from '../services/mapService';

const MapContainer = () => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  
  const { 
    mapData, 
    layerVisibility, 
    isLoading 
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
        } else {
          mapService.toggleLayer(layerName, visible);
        }
      });
    }
  }, [layerVisibility]);

  return (
    <div className="relative flex-1 bg-gray-100">
      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg flex items-center space-x-3">
            <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-lg font-medium text-gray-900">生成地圖中...</span>
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
              <div className="w-6 h-3 bg-red-400 border border-red-800"></div>
              <span>主幹道 Main Roads (雙向)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-6 h-3 bg-red-300 border border-red-800" style={{ opacity: 0.7, borderStyle: 'dashed' }}></div>
              <span>主幹道 Main Roads (單向)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-6 h-3 bg-blue-400 border border-blue-800"></div>
              <span>次要道路 Secondary Roads (雙向)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-6 h-3 bg-blue-300 border border-blue-800" style={{ opacity: 0.7, borderStyle: 'dashed' }}></div>
              <span>次要道路 Secondary Roads (單向)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-orange-400 rounded-full"></div>
              <span>交叉路口 Intersections</span>
            </div>
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
          </div>
        </div>
      )}
    </div>
  );
};

export default MapContainer;