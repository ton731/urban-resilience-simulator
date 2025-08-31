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
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="text-center">
            <h1 className="text-3xl font-semibold text-gray-900 mb-2">
              城市韌性模擬平台
            </h1>
            <p className="text-gray-600">Urban Resilience Simulation Platform</p>
            <p className="text-sm text-gray-500 mt-2">
              設定地圖生成參數，建立您的虛擬城市環境
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Left Column - Basic Settings */}
          <div className="space-y-4">
            {/* Basic Configuration */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">基礎設定</h3>
              </div>
              <div className="p-6 space-y-4">
                {/* Map Size */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    地圖尺寸 (米)
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="number"
                      value={localConfig.map_size[0]}
                      onChange={(e) => handleMapSizeChange(0, e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-gray-500"
                      placeholder="寬度"
                      min="500"
                      max="10000"
                    />
                    <input
                      type="number"
                      value={localConfig.map_size[1]}
                      onChange={(e) => handleMapSizeChange(1, e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-gray-500"
                      placeholder="高度"
                      min="500"
                      max="10000"
                    />
                  </div>
                </div>

                {/* Road Density */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-medium text-gray-700">道路密度</label>
                    <span className="text-sm text-gray-500">
                      {(localConfig.road_density * 100).toFixed(0)}%
                    </span>
                  </div>
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
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-medium text-gray-700">主幹道數量</label>
                    <span className="text-sm text-gray-500">
                      {localConfig.main_road_count}
                    </span>
                  </div>
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
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-medium text-gray-700">次要道路密度</label>
                    <span className="text-sm text-gray-500">
                      {(localConfig.secondary_road_density * 100).toFixed(0)}%
                    </span>
                  </div>
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
            </div>

            {/* Trees Settings */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">樹木設定</h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localConfig.include_trees}
                      onChange={(e) => handleConfigChange('include_trees', e.target.checked)}
                      className="rounded border-gray-300 text-gray-600 focus:ring-gray-500 mr-3"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      生成樹木
                    </span>
                  </label>
                </div>

                {localConfig.include_trees && (
                  <div className="space-y-4 pl-8">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <label className="text-sm font-medium text-gray-700">樹木間距</label>
                        <span className="text-sm text-gray-500">
                          {localConfig.tree_spacing.toFixed(0)}m
                        </span>
                      </div>
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

                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <label className="text-sm font-medium text-gray-700">樹木偏移</label>
                        <span className="text-sm text-gray-500">
                          {localConfig.tree_max_offset.toFixed(0)}m
                        </span>
                      </div>
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

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">脆弱度分佈</label>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>高風險: {(localConfig.vulnerability_distribution.I * 100).toFixed(0)}%</span>
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
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>中風險: {(localConfig.vulnerability_distribution.II * 100).toFixed(0)}%</span>
                          <span>低風險: {(localConfig.vulnerability_distribution.III * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Buildings & Actions */}
          <div className="space-y-4">
            {/* Buildings Settings */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">建築物設定</h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localConfig.include_buildings}
                      onChange={(e) => handleConfigChange('include_buildings', e.target.checked)}
                      className="rounded border-gray-300 text-gray-600 focus:ring-gray-500 mr-3"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      生成建築物
                    </span>
                  </label>
                </div>

                {localConfig.include_buildings && (
                  <div className="pl-8">
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-sm font-medium text-gray-700">建築物密度</label>
                      <span className="text-sm text-gray-500">
                        {(localConfig.building_density * 100).toFixed(0)}%
                      </span>
                    </div>
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
            </div>

            {/* Generation Actions */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">生成地圖</h3>
              </div>
              <div className="p-6 space-y-4">
                <Button
                  onClick={handleGenerate}
                  loading={isLoading}
                  disabled={isLoading}
                  variant="primary"
                  className="w-full"
                >
                  {isLoading ? '生成中...' : '生成地圖'}
                </Button>
                
                <Button
                  onClick={handleReset}
                  variant="secondary"
                  disabled={isLoading}
                  className="w-full"
                >
                  重置設定
                </Button>

                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                  <p className="font-medium mb-1">使用說明</p>
                  <ol className="list-decimal list-inside space-y-1 text-sm">
                    <li>調整地圖生成參數</li>
                    <li>選擇要生成的元素</li>
                    <li>點擊生成地圖開始</li>
                    <li>完成後自動跳轉到檢視頁面</li>
                  </ol>
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <div className="flex-1">
                    <h4 className="text-red-800 font-medium">發生錯誤</h4>
                    <p className="text-red-600 text-sm mt-1">{error}</p>
                  </div>
                  <Button
                    onClick={clearError}
                    variant="secondary"
                    size="small"
                    className="ml-4 text-red-600 hover:bg-red-100"
                  >
                    ✕
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeneratePage;