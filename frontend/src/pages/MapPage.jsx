import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useSimulationStore from '../store/useSimulationStore';
import MapControlPanel from '../components/controls/MapControlPanel';
import MapContainer from '../containers/MapContainer';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const MapPage = () => {
  const navigate = useNavigate();
  const { mapData, error, clearError } = useSimulationStore();

  // Redirect to generate page if no map data
  useEffect(() => {
    if (!mapData) {
      navigate('/generate');
    }
  }, [mapData, navigate]);

  // Don't render if no map data
  if (!mapData) {
    return null;
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center">
          {/* Back to Generate Button */}
          <Button
            onClick={() => navigate('/generate')}
            variant="secondary"
            size="medium"
            className="mr-6"
          >
            ← 返回生成設定
          </Button>
          
          {/* Title */}
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              城市韌性模擬平台
            </h1>
            <p className="text-sm text-gray-600">
              地圖檢視與模擬
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Control Panel - Left Sidebar */}
        <MapControlPanel />
        
        {/* Map View - Main Area */}
        <MapContainer />
        
      </div>

      {/* Error Display */}
      {error && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-red-800">錯誤</h4>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
              <Button
                onClick={clearError}
                variant="secondary"
                size="small"
              >
                ✕
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default MapPage;