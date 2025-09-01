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

    </div>
  );
};

export default SimulationPage;