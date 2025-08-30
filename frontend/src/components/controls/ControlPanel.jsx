import React, { useState } from 'react';
import useSimulationStore from '../../store/useSimulationStore';
import Button from '../ui/Button';
import Card from '../ui/Card';

const ControlPanel = () => {
  const {
    generationConfig,
    isLoading,
    error,
    layerVisibility,
    mapStats,
    updateConfig,
    generateWorld,
    clearMapData,
    toggleLayer,
    resetConfig,
    clearError
  } = useSimulationStore();

  const [localConfig, setLocalConfig] = useState(generationConfig);

  // Update local config when store config changes
  React.useEffect(() => {
    setLocalConfig(generationConfig);
  }, [generationConfig]);

  const handleConfigChange = (key, value) => {
    const newConfig = { ...localConfig, [key]: value };
    setLocalConfig(newConfig);
    updateConfig(newConfig);
  };

  const handleMapSizeChange = (index, value) => {
    const newMapSize = [...localConfig.map_size];
    newMapSize[index] = parseInt(value) || 0;
    handleConfigChange('map_size', newMapSize);
  };

  const handleGenerate = async () => {
    try {
      clearError();
      await generateWorld();
    } catch (error) {
      // Error is already handled in store
    }
  };

  const handleReset = () => {
    resetConfig();
    clearMapData();
  };

  return (
    <div className="w-80 bg-gray-50 p-4 overflow-y-auto">
      <div className="space-y-4">
        
        {/* Generation Controls */}
        <Card title="世界生成控制 (World Generation)">
          <div className="space-y-4">
            
            {/* Map Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                地圖尺寸 (Map Size) - 米
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  value={localConfig.map_size[0]}
                  onChange={(e) => handleMapSizeChange(0, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="寬度 Width"
                  min="500"
                  max="10000"
                />
                <input
                  type="number"
                  value={localConfig.map_size[1]}
                  onChange={(e) => handleMapSizeChange(1, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="高度 Height"
                  min="500"
                  max="10000"
                />
              </div>
            </div>

            {/* Road Density */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                道路密度 (Road Density): {(localConfig.road_density * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={localConfig.road_density}
                onChange={(e) => handleConfigChange('road_density', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Main Road Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                主幹道數量 (Main Roads): {localConfig.main_road_count}
              </label>
              <input
                type="range"
                min="2"
                max="10"
                step="1"
                value={localConfig.main_road_count}
                onChange={(e) => handleConfigChange('main_road_count', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Secondary Road Density */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                次要道路密度 (Secondary Roads): {(localConfig.secondary_road_density * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={localConfig.secondary_road_density}
                onChange={(e) => handleConfigChange('secondary_road_density', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-2 pt-2">
              <Button
                onClick={handleGenerate}
                loading={isLoading}
                disabled={isLoading}
                variant="primary"
                size="medium"
              >
                {isLoading ? '生成中...' : '生成地圖'}
              </Button>
              <Button
                onClick={handleReset}
                variant="secondary"
                disabled={isLoading}
              >
                重置
              </Button>
            </div>

          </div>
        </Card>

        {/* Layer Controls */}
        <Card title="圖層控制 (Layer Controls)">
          <div className="space-y-3">
            {Object.entries({
              nodes: '節點 (Nodes)',
              mainRoads: '主幹道 (Main Roads)', 
              secondaryRoads: '次要道路 (Secondary Roads)'
            }).map(([layerKey, layerLabel]) => (
              <label key={layerKey} className="flex items-center">
                <input
                  type="checkbox"
                  checked={layerVisibility[layerKey]}
                  onChange={() => toggleLayer(layerKey)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">{layerLabel}</span>
              </label>
            ))}
          </div>
        </Card>

        {/* Statistics */}
        {mapStats && (
          <Card title="地圖統計 (Statistics)">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">總節點:</span>
                <span className="font-medium">{mapStats.totalNodes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">總道路:</span>
                <span className="font-medium">{mapStats.totalEdges}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">主幹道:</span>
                <span className="font-medium text-red-600">{mapStats.mainRoads}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">次要道路:</span>
                <span className="font-medium text-blue-600">{mapStats.secondaryRoads}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">地圖大小:</span>
                <span className="font-medium">{mapStats.mapSize}</span>
              </div>
              {mapStats.generationId && (
                <div className="text-xs text-gray-500 mt-3 p-2 bg-gray-100 rounded">
                  ID: {mapStats.generationId}
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50">
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
          </Card>
        )}

      </div>
    </div>
  );
};

export default ControlPanel;