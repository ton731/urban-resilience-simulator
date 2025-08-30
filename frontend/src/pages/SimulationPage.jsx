import React, { useEffect } from 'react';
import useSimulationStore from '../store/useSimulationStore';
import ControlPanel from '../components/controls/ControlPanel';
import MapContainer from '../containers/MapContainer';

const SimulationPage = () => {
  const { loadDefaultConfig, error } = useSimulationStore();

  // Load default configuration on component mount
  useEffect(() => {
    loadDefaultConfig();
  }, [loadDefaultConfig]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              城市韌性模擬平台
            </h1>
            <p className="text-sm text-gray-600">
              Urban Resilience Simulation Platform - 地圖生成模組 (WS-1.1)
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500">
              後端狀態: <span className="text-green-600 font-medium">已連接</span>
            </div>
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Control Panel - Left Sidebar */}
        <ControlPanel />
        
        {/* Map View - Main Area */}
        <MapContainer />
        
      </div>

      {/* Status Bar */}
      <footer className="bg-white border-t border-gray-200 px-6 py-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            WS-1.1: 程序化地圖生成 - React + FastAPI + Leaflet.js
          </div>
          <div>
            後端 API: http://0.0.0.0:8000
          </div>
        </div>
      </footer>

    </div>
  );
};

export default SimulationPage;