import React, { useState, useEffect } from 'react';
import useSimulationStore from '../../store/useSimulationStore';
import Button from '../ui/Button';
import Card from '../ui/Card';
import mapService from '../../services/mapService';

const AmbulanceServicePanel = () => {
  const {
    mapData,
    disasterSimulationData,
    isLoading,
    error,
    mapStats,
    setError,
    clearError
  } = useSimulationStore();

  // Compute derived values
  const worldGenerationId = mapData?.generation_id || null;
  const simulationId = disasterSimulationData?.simulation_id || null;

  // Local state for ambulance service analysis
  const [analysisConfig, setAnalysisConfig] = useState({
    analysisMode: 'pre_disaster',
    gridSizeMeters: 50,
    maxResponseTimeSeconds: 1800,
    vehicleType: 'ambulance'
  });

  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [showGrid, setShowGrid] = useState(true);
  const [showLegend, setShowLegend] = useState(true);

  // Analysis modes
  const analysisModes = [
    { value: 'pre_disaster', label: '災前分析 (Pre-disaster)', icon: '🟢' },
    { value: 'post_disaster', label: '災後分析 (Post-disaster)', icon: '🔴' },
    { value: 'comparison', label: '對比分析 (Comparison)', icon: '🔄' }
  ];

  // Handle config changes
  const handleConfigChange = (key, value) => {
    setAnalysisConfig(prev => ({ ...prev, [key]: value }));
  };

  // Check if analysis can be performed
  const canAnalyze = () => {
    if (!worldGenerationId) return false;
    
    // For post-disaster and comparison modes, need simulation result
    if ((analysisConfig.analysisMode === 'post_disaster' || 
         analysisConfig.analysisMode === 'comparison') && !simulationId) {
      return false;
    }
    
    return true;
  };

  // Get analysis button text and status
  const getAnalysisButtonInfo = () => {
    if (!worldGenerationId) {
      return { text: '請先生成地圖', disabled: true };
    }
    
    if ((analysisConfig.analysisMode === 'post_disaster' || 
         analysisConfig.analysisMode === 'comparison') && !simulationId) {
      return { text: '請先執行災害模擬', disabled: true };
    }
    
    if (isAnalyzing) {
      return { text: '分析中...', disabled: true };
    }
    
    return { text: '開始分析', disabled: false };
  };

  // Perform ambulance service analysis
  const performAnalysis = async () => {
    if (!canAnalyze()) return;
    
    setIsAnalyzing(true);
    clearError();
    
    try {
      const requestBody = {
        world_generation_id: worldGenerationId,
        analysis_mode: analysisConfig.analysisMode,
        grid_size_meters: analysisConfig.gridSizeMeters,
        max_response_time_seconds: analysisConfig.maxResponseTimeSeconds,
        vehicle_type: analysisConfig.vehicleType
      };

      // Add simulation ID for post-disaster modes
      if (analysisConfig.analysisMode !== 'pre_disaster' && simulationId) {
        requestBody.simulation_id = simulationId;
      }

      console.log('🚑 開始救護車服務分析...', requestBody);

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/impact/ambulance-service-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '分析失敗');
      }

      const result = await response.json();
      console.log('✅ 救護車服務分析完成:', result);
      
      setAnalysisResult(result);
      
      // Add to analysis history
      setAnalysisHistory(prev => [...prev, {
        id: result.analysis_id,
        mode: result.analysis_mode,
        timestamp: new Date(result.analyzed_at).toLocaleString('zh-TW'),
        gridCells: result.grid_cells.length,
        coverage: result.pre_disaster_metrics?.coverage_percentage || 
                  result.post_disaster_metrics?.coverage_percentage || 0
      }]);
      
    } catch (error) {
      console.error('❌ 救護車服務分析錯誤:', error);
      setError(`救護車服務分析失敗: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Clear analysis results
  const clearAnalysis = () => {
    setAnalysisResult(null);
    mapService.clearAmbulanceServiceLayers();
    clearError();
  };

  // Handle layer visibility toggle
  const handleLayerToggle = (layerName, visible) => {
    if (layerName === 'grid') {
      setShowGrid(visible);
      mapService.toggleAmbulanceServiceLayer('ambulanceServiceGrid', visible);
    } else if (layerName === 'legend') {
      setShowLegend(visible);
      // Legend visibility is controlled together with grid
    }
  };

  // Update map visualization when analysis results change
  useEffect(() => {
    if (analysisResult) {
      console.log('🗺️ 更新地圖救護車服務範圍可視化');
      mapService.updateAmbulanceServiceData(analysisResult);
      
      // Apply current visibility settings
      if (!showGrid) {
        mapService.toggleAmbulanceServiceLayer('ambulanceServiceGrid', false);
      }
    }
  }, [analysisResult]);

  // Handle layer visibility changes
  useEffect(() => {
    if (analysisResult) {
      mapService.toggleAmbulanceServiceLayer('ambulanceServiceGrid', showGrid);
    }
  }, [showGrid]);

  const buttonInfo = getAnalysisButtonInfo();

  return (
    <Card title="🚑 救護車服務範圍分析 (IA-3.1)">
      <div className="space-y-4">
        
        {/* Analysis Mode Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            分析模式 (Analysis Mode)
          </label>
          <div className="space-y-2">
            {analysisModes.map(mode => (
              <label key={mode.value} className="flex items-center">
                <input
                  type="radio"
                  value={mode.value}
                  checked={analysisConfig.analysisMode === mode.value}
                  onChange={(e) => handleConfigChange('analysisMode', e.target.value)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  {mode.icon} {mode.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Grid Size Configuration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            網格大小 (Grid Size): {analysisConfig.gridSizeMeters}m
          </label>
          <input
            type="range"
            min="25"
            max="100"
            step="25"
            value={analysisConfig.gridSizeMeters}
            onChange={(e) => handleConfigChange('gridSizeMeters', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>精細 (25m)</span>
            <span>平衡 (50m)</span>
            <span>快速 (100m)</span>
          </div>
        </div>

        {/* Max Response Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            最大響應時間 (Max Response): {Math.round(analysisConfig.maxResponseTimeSeconds/60)}分鐘
          </label>
          <input
            type="range"
            min="600"
            max="3600"
            step="300"
            value={analysisConfig.maxResponseTimeSeconds}
            onChange={(e) => handleConfigChange('maxResponseTimeSeconds', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>10分鐘</span>
            <span>30分鐘</span>
            <span>60分鐘</span>
          </div>
        </div>

        {/* Vehicle Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            車輛類型 (Vehicle Type)
          </label>
          <select
            value={analysisConfig.vehicleType}
            onChange={(e) => handleConfigChange('vehicleType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="ambulance">🚑 救護車 (Ambulance)</option>
            <option value="car">🚗 一般車輛 (Car)</option>
            <option value="motorcycle">🏍️ 機車 (Motorcycle)</option>
          </select>
        </div>

        {/* Analysis Action Buttons */}
        <div className="grid grid-cols-2 gap-2 pt-2">
          <Button
            onClick={performAnalysis}
            loading={isAnalyzing}
            disabled={buttonInfo.disabled || isAnalyzing}
            variant="primary"
            size="medium"
          >
            {buttonInfo.text}
          </Button>
          <Button
            onClick={clearAnalysis}
            variant="secondary"
            disabled={!analysisResult && !error}
          >
            清除結果
          </Button>
        </div>

        {/* Layer Visibility Controls */}
        {analysisResult && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">🎚️ 圖層控制</h4>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showGrid}
                  onChange={(e) => handleLayerToggle('grid', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  🗺️ 顯示服務範圍網格
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={showLegend}
                  onChange={(e) => handleLayerToggle('legend', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">
                  🎨 顯示顏色圖例
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Current World/Simulation Info */}
        <div className="text-xs text-gray-500 p-2 bg-gray-50 rounded">
          <div>📍 世界ID: {worldGenerationId || '未生成'}</div>
          {simulationId && (
            <div>💥 模擬ID: {simulationId}</div>
          )}
          {mapStats?.facilityStats?.ambulance_stations && (
            <div>🚑 救護車站: {mapStats.facilityStats.ambulance_stations} 個</div>
          )}
        </div>

        {/* Analysis Results Summary */}
        {analysisResult && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">📊 分析結果</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">分析模式:</span>
                <span className="font-medium">
                  {analysisModes.find(m => m.value === analysisResult.analysis_mode)?.label}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">網格數量:</span>
                <span className="font-medium">{analysisResult.grid_cells.length.toLocaleString()}</span>
              </div>
              
              {/* Pre-disaster metrics */}
              {analysisResult.pre_disaster_metrics && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-600">災前覆蓋率:</span>
                    <span className="font-medium text-green-600">
                      {analysisResult.pre_disaster_metrics.coverage_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">災前平均時間:</span>
                    <span className="font-medium text-green-600">
                      {Math.round(analysisResult.pre_disaster_metrics.average_response_time_seconds / 60)}分鐘
                    </span>
                  </div>
                </>
              )}

              {/* Post-disaster metrics */}
              {analysisResult.post_disaster_metrics && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-600">災後覆蓋率:</span>
                    <span className="font-medium text-red-600">
                      {analysisResult.post_disaster_metrics.coverage_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">災後平均時間:</span>
                    <span className="font-medium text-red-600">
                      {Math.round(analysisResult.post_disaster_metrics.average_response_time_seconds / 60)}分鐘
                    </span>
                  </div>
                </>
              )}

              {/* Comparison metrics */}
              {analysisResult.comparison_metrics && (
                <>
                  <div className="border-t border-gray-200 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">覆蓋率變化:</span>
                      <span className={`font-medium ${
                        analysisResult.comparison_metrics.coverage_change_percentage >= 0 
                          ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {analysisResult.comparison_metrics.coverage_change_percentage > 0 ? '+' : ''}
                        {analysisResult.comparison_metrics.coverage_change_percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">時間增加:</span>
                      <span className="font-medium text-red-600">
                        +{Math.round(analysisResult.comparison_metrics.average_time_increase_seconds / 60)}分鐘
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">新增盲區:</span>
                      <span className="font-medium text-red-600">
                        {analysisResult.comparison_metrics.newly_unreachable_cells} 個網格
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Service Level Legend */}
        {analysisResult && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">🎨 顏色圖例</h4>
            <div className="space-y-1 text-xs">
              {Object.entries(analysisResult.color_legend).map(([level, color]) => (
                <div key={level} className="flex items-center">
                  <div 
                    className="w-4 h-4 rounded border border-gray-300 mr-2"
                    style={{ backgroundColor: color }}
                  ></div>
                  <span className="capitalize">
                    {level === 'excellent' && '優秀 (≤5分鐘)'}
                    {level === 'good' && '良好 (5-10分鐘)'}
                    {level === 'fair' && '一般 (10-15分鐘)'}
                    {level === 'poor' && '較差 (>15分鐘)'}
                    {level === 'unreachable' && '無法到達'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analysis History */}
        {analysisHistory.length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">📝 分析歷史</h4>
            <div className="space-y-1 text-xs max-h-20 overflow-y-auto">
              {analysisHistory.slice(-3).map(record => (
                <div key={record.id} className="text-gray-600">
                  {record.timestamp} - {analysisModes.find(m => m.value === record.mode)?.label} 
                  (覆蓋率: {record.coverage.toFixed(1)}%)
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </Card>
  );
};

export default AmbulanceServicePanel;