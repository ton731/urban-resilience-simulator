import React, { useState } from 'react';
import useSimulationStore from '../../store/useSimulationStore';
import Button from '../ui/Button';
import Card from '../ui/Card';

/**
 * DisasterSimulationPanel Component
 * 
 * Provides controls for disaster simulation (SE-2.1)
 * Including disaster intensity input and simulation trigger
 */
const DisasterSimulationPanel = () => {
  const {
    mapData,
    disasterIntensity,
    isRunningSimulation,
    simulationError,
    disasterSimulationData,
    lastSimulationAt,
    disasterLayerVisibility,
    setDisasterIntensity,
    runDisasterSimulation,
    clearDisasterSimulation,
    toggleDisasterLayer,
    getDisasterStats,
    clearSimulationError
  } = useSimulationStore();

  const [showIntensityInput, setShowIntensityInput] = useState(false);
  const [tempIntensity, setTempIntensity] = useState(disasterIntensity);

  const handleStartDisaster = () => {
    if (!mapData) {
      alert('請先生成地圖！');
      return;
    }
    setShowIntensityInput(true);
    setTempIntensity(disasterIntensity);
  };

  const handleConfirmSimulation = async () => {
    try {
      clearSimulationError();
      setDisasterIntensity(tempIntensity);
      await runDisasterSimulation();
      setShowIntensityInput(false);
    } catch (error) {
      // Error is handled in the store
      console.error('Simulation failed:', error);
    }
  };

  const handleCancelSimulation = () => {
    setShowIntensityInput(false);
    setTempIntensity(disasterIntensity);
  };

  const disasterStats = getDisasterStats();

  return (
    <Card title="災害模擬 (SE-2.1 Disaster Simulation)" collapsible={true}>
      <div className="space-y-4">
        
        {/* Status indicator */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            地圖狀態: {mapData ? 
              <span className="text-green-600 font-medium">已生成</span> : 
              <span className="text-red-600 font-medium">未生成</span>
            }
          </div>
          {mapData && (
            <div className="w-3 h-3 bg-green-400 rounded-full"></div>
          )}
        </div>

        {/* Disaster intensity input modal/panel */}
        {showIntensityInput && (
          <div className="border-2 border-orange-300 rounded-lg p-4 bg-orange-50">
            <h4 className="font-semibold text-orange-800 mb-3">
              🌪️ 設定災害強度
            </h4>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  災害強度: {tempIntensity.toFixed(1)}/10.0
                </label>
                <input
                  type="range"
                  min="1.0"
                  max="10.0"
                  step="0.5"
                  value={tempIntensity}
                  onChange={(e) => setTempIntensity(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>輕微</span>
                  <span>中等</span>
                  <span>嚴重</span>
                </div>
              </div>
              
              <div className="text-sm text-gray-600 p-3 bg-white rounded border">
                <div className="font-medium mb-1">預期影響：</div>
                <div>• 高風險樹木 (Level I): ~{Math.round(tempIntensity * 8)}% 倒塌率</div>
                <div>• 中風險樹木 (Level II): ~{Math.round(tempIntensity * 5)}% 倒塌率</div>
                <div>• 低風險樹木 (Level III): ~{Math.round(tempIntensity * 1)}% 倒塌率</div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleConfirmSimulation}
                  disabled={isRunningSimulation}
                  className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
                >
                  {isRunningSimulation ? '模擬中...' : '執行災害模擬'}
                </Button>
                <Button
                  onClick={handleCancelSimulation}
                  className="px-3 bg-gray-300 hover:bg-gray-400"
                  disabled={isRunningSimulation}
                >
                  取消
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Main disaster button */}
        {!showIntensityInput && (
          <Button
            onClick={handleStartDisaster}
            disabled={!mapData || isRunningSimulation}
            className={`w-full py-3 font-semibold ${
              !mapData 
                ? 'bg-gray-300 cursor-not-allowed' 
                : disasterSimulationData
                  ? 'bg-orange-600 hover:bg-orange-700 text-white'
                  : 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
            }`}
          >
            {isRunningSimulation ? (
              <span className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                災害模擬執行中...
              </span>
            ) : !mapData ? (
              '請先生成地圖'
            ) : disasterSimulationData ? (
              '🔥 重新執行災害模擬'
            ) : (
              '🚨 啟動災害模擬'
            )}
          </Button>
        )}

        {/* Error display */}
        {simulationError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <span className="text-red-600 text-sm font-medium">
                ❌ 模擬失敗
              </span>
            </div>
            <div className="text-red-600 text-sm mt-1">{simulationError}</div>
            <Button
              onClick={clearSimulationError}
              className="mt-2 text-xs bg-red-100 hover:bg-red-200 text-red-700"
            >
              清除錯誤
            </Button>
          </div>
        )}

        {/* Simulation Results */}
        {disasterSimulationData && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-800">模擬結果</h4>
              {lastSimulationAt && (
                <span className="text-xs text-gray-500">
                  {lastSimulationAt.toLocaleTimeString()}
                </span>
              )}
            </div>
            
            {/* Statistics */}
            {disasterStats && (
              <div className="bg-white border rounded-md p-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(disasterStats).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600">{key}:</span>
                      <span className="font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Clear simulation button */}
            <div className="flex space-x-2">
              <Button
                onClick={clearDisasterSimulation}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white text-sm"
              >
                清除模擬結果
              </Button>
            </div>
          </div>
        )}

        {/* Layer visibility controls for disaster visualization */}
        {disasterSimulationData && (
          <Card title="災害視覺化圖層" collapsible={true}>
            <div className="space-y-2">
              
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-700">倒塌樹木</label>
                <input
                  type="checkbox"
                  checked={disasterLayerVisibility.collapsedTrees}
                  onChange={() => toggleDisasterLayer('collapsedTrees')}
                  className="rounded"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-700">樹木阻塞範圍</label>
                <input
                  type="checkbox"
                  checked={disasterLayerVisibility.treeBlockages}
                  onChange={() => toggleDisasterLayer('treeBlockages')}
                  className="rounded"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-700">道路阻塞</label>
                <input
                  type="checkbox"
                  checked={disasterLayerVisibility.roadObstructions}
                  onChange={() => toggleDisasterLayer('roadObstructions')}
                  className="rounded"
                />
              </div>
              
            </div>
          </Card>
        )}

        {/* Instructions */}
        <div className="text-xs text-gray-500 p-3 bg-gray-100 rounded">
          <div className="font-medium mb-1">使用說明：</div>
          <div>1. 先生成包含樹木的地圖</div>
          <div>2. 點擊「啟動災害模擬」設定強度</div>
          <div>3. 模擬將根據樹木脆弱度隨機產生倒塌</div>
          <div>4. 查看地圖上的倒塌樹木和道路阻塞情況</div>
        </div>

      </div>
    </Card>
  );
};

export default DisasterSimulationPanel;