import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useSimulationStore from '../store/useSimulationStore';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const GeneratePage = () => {
  const navigate = useNavigate();
  const {
    generationConfig,
    isLoading,
    error,
    updateConfig,
    generateWorld,
    resetConfig,
    clearError,
    loadDefaultConfig
  } = useSimulationStore();

  const [localConfig, setLocalConfig] = useState(generationConfig);

  // Load default configuration on component mount
  useEffect(() => {
    loadDefaultConfig();
  }, [loadDefaultConfig]);

  // Update local config when store config changes
  useEffect(() => {
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
      // Navigate to map page after successful generation
      navigate('/map');
    } catch (error) {
      // Error is already handled in store
    }
  };

  const handleReset = () => {
    resetConfig();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              城市韌性模擬平台
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Urban Resilience Simulation Platform - 地圖生成設定
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Generation Settings */}
          <div className="space-y-6">
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
              </div>
            </Card>

            {/* Tree Generation */}
            <Card title="樹木生成 (Tree Generation) - WS-1.2">
              <div className="space-y-4">
                {/* Tree Generation Toggle */}
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localConfig.include_trees}
                      onChange={(e) => handleConfigChange('include_trees', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      生成樹木 (Generate Trees)
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
              </div>
            </Card>
          </div>

          {/* Building Generation */}
          <div className="space-y-6">
            <Card title="建築物生成 (Building Generation) - WS-1.5">
              <div className="space-y-4">
                {/* Building Generation Toggle */}
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localConfig.include_buildings}
                      onChange={(e) => handleConfigChange('include_buildings', e.target.checked)}
                      className="rounded border-gray-300 text-purple-600 focus:ring-purple-500 mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      生成建築物 (Generate Buildings)
                    </span>
                  </label>
                </div>

                {/* Building Parameters - Only show if buildings are enabled */}
                {localConfig.include_buildings && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      建築物密度 (Building Density): {(localConfig.building_density * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.1"
                      value={localConfig.building_density}
                      onChange={(e) => handleConfigChange('building_density', parseFloat(e.target.value))}
                      className="w-full"
                    />
                  </div>
                )}
              </div>
            </Card>

            {/* Generation Actions */}
            <Card title="生成動作 (Generation Actions)">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Button
                    onClick={handleGenerate}
                    loading={isLoading}
                    disabled={isLoading}
                    variant="primary"
                    size="large"
                  >
                    {isLoading ? '生成中...' : '生成地圖'}
                  </Button>
                  <Button
                    onClick={handleReset}
                    variant="secondary"
                    disabled={isLoading}
                    size="large"
                  >
                    重置設定
                  </Button>
                </div>

                {/* Instructions */}
                <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
                  <p className="font-medium text-blue-900 mb-1">使用說明：</p>
                  <ol className="list-decimal list-inside space-y-1 text-blue-800">
                    <li>調整地圖生成參數</li>
                    <li>選擇要生成的元素（樹木、建築物）</li>
                    <li>點擊「生成地圖」開始生成</li>
                    <li>生成完成後會自動跳轉到地圖檢視頁面</li>
                  </ol>
                </div>
              </div>
            </Card>

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
      </div>
    </div>
  );
};

export default GeneratePage;