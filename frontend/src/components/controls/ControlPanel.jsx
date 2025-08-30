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
    toggleTreeVulnerability,
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

            {/* Tree Generation Toggle */}
            <div className="pt-2 border-t border-gray-200">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={localConfig.include_trees}
                  onChange={(e) => handleConfigChange('include_trees', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                />
                <span className="text-sm font-medium text-gray-700">
                  生成樹木 (Generate Trees) - WS-1.2
                </span>
              </label>
            </div>

            {/* Tree Parameters - Only show if trees are enabled */}
            {localConfig.include_trees && (
              <>
                {/* Tree Spacing */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    樹木間距 (Tree Spacing): {localConfig.tree_spacing.toFixed(0)}m
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={localConfig.tree_spacing}
                    onChange={(e) => handleConfigChange('tree_spacing', parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* Tree Max Offset */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    樹木偏移 (Max Offset): {localConfig.tree_max_offset.toFixed(0)}m
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="20"
                    step="1"
                    value={localConfig.tree_max_offset}
                    onChange={(e) => handleConfigChange('tree_max_offset', parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* Vulnerability Distribution */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    脆弱度分佈 (Vulnerability Distribution)
                  </label>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center">
                        <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                        Level I (高風險):
                      </span>
                      <span>{(localConfig.vulnerability_distribution.I * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.05"
                      max="0.5"
                      step="0.05"
                      value={localConfig.vulnerability_distribution.I}
                      onChange={(e) => {
                        const newI = parseFloat(e.target.value);
                        const remaining = 1 - newI;
                        const ratio = localConfig.vulnerability_distribution.II / (localConfig.vulnerability_distribution.II + localConfig.vulnerability_distribution.III);
                        handleConfigChange('vulnerability_distribution', {
                          I: newI,
                          II: remaining * ratio,
                          III: remaining * (1 - ratio)
                        });
                      }}
                      className="w-full"
                    />
                    
                    <div className="flex items-center justify-between">
                      <span className="flex items-center">
                        <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
                        Level II (中風險):
                      </span>
                      <span>{(localConfig.vulnerability_distribution.II * 100).toFixed(0)}%</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="flex items-center">
                        <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                        Level III (低風險):
                      </span>
                      <span>{(localConfig.vulnerability_distribution.III * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </>
            )}

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
            {/* Road Layers */}
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
            
            {/* Tree Layers */}
            {mapStats && mapStats.totalTrees > 0 && (
              <>
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={layerVisibility.trees}
                      onChange={() => toggleLayer('trees')}
                      className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 font-medium">
                      🌳 樹木 (Trees) - {mapStats.totalTrees}
                    </span>
                  </label>
                </div>
                
                {/* Tree vulnerability levels */}
                <div className="ml-4 space-y-2">
                  {[
                    { level: 'I', label: '高風險 High Risk', color: 'text-red-600', bgColor: 'bg-red-500' },
                    { level: 'II', label: '中風險 Medium Risk', color: 'text-orange-600', bgColor: 'bg-orange-500' },
                    { level: 'III', label: '低風險 Low Risk', color: 'text-green-600', bgColor: 'bg-green-500' }
                  ].map(({ level, label, color, bgColor }) => {
                    const count = mapStats.treeStats?.vulnerability_distribution?.[level] || 0;
                    const percentage = mapStats.treeStats?.vulnerability_percentages?.[level] || 0;
                    
                    return (
                      <label key={level} className="flex items-center text-xs">
                        <input
                          type="checkbox"
                          checked={layerVisibility.treesByVulnerability?.[level]}
                          onChange={() => toggleTreeVulnerability(level)}
                          className={`rounded border-gray-300 focus:ring-2 ${color.replace('text-', 'text-')} focus:ring-${color.split('-')[1]}-500`}
                        />
                        <div className={`ml-2 w-2 h-2 ${bgColor} rounded-full`}></div>
                        <span className={`ml-1 ${color}`}>
                          Level {level}: {count} ({percentage}%)
                        </span>
                      </label>
                    );
                  })}
                </div>
              </>
            )}

            {/* Facility Layers */}
            {mapStats && mapStats.totalFacilities > 0 && (
              <div className="border-t border-gray-200 pt-3 mt-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={layerVisibility.facilities}
                    onChange={() => toggleLayer('facilities')}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 font-medium">
                    🏢 設施 (Facilities) - {mapStats.totalFacilities}
                  </span>
                </label>
                
                {/* Facility types */}
                <div className="ml-4 space-y-2 mt-2">
                  <label className="flex items-center text-xs">
                    <input
                      type="checkbox"
                      checked={layerVisibility.ambulanceStations}
                      onChange={() => toggleLayer('ambulanceStations')}
                      className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <div className="ml-2 w-4 h-4 bg-red-600 rounded-full flex items-center justify-center text-white text-xs">🚑</div>
                    <span className="ml-1 text-red-700">
                      救護車起點: {mapStats.facilityStats?.ambulance_stations || 0}
                    </span>
                  </label>
                  
                  <label className="flex items-center text-xs">
                    <input
                      type="checkbox"
                      checked={layerVisibility.shelters}
                      onChange={() => toggleLayer('shelters')}
                      className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    />
                    <div className="ml-2 w-4 h-4 bg-green-600 rounded-full flex items-center justify-center text-white text-xs">🏠</div>
                    <span className="ml-1 text-green-700">
                      避難所: {mapStats.facilityStats?.shelters || 0} (容量: {mapStats.facilityStats?.total_shelter_capacity || 0})
                    </span>
                  </label>
                </div>
              </div>
            )}
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
              {mapStats.totalTrees > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">樹木總數:</span>
                  <span className="font-medium text-green-600">{mapStats.totalTrees}</span>
                </div>
              )}
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