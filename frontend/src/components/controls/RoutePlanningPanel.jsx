import React from 'react';
import useSimulationStore from '../../store/useSimulationStore';
import Card from '../ui/Card';

/**
 * RoutePlanningPanel - 路線規劃控制面板 (SE-2.2)
 * 
 * This component provides interface for route planning functionality:
 * - Start and end point selection
 * - Vehicle type selection
 * - Route calculation and visualization
 * - Pre/post disaster route comparison
 */
const RoutePlanningPanel = () => {
  const {
    // Map data
    mapData,
    disasterSimulationData,
    
    // Route planning state
    routePlanning,
    routeLayerVisibility,
    
    // Route planning actions
    setRouteStartPoint,
    setRouteEndPoint,
    enableStartPointSelection,
    enableEndPointSelection,
    clearRoutePoints,
    setRouteVehicleType,
    calculateRoute,
    
    // Layer visibility actions
    toggleRouteLayer,
    
    // Statistics
    getRouteStats,
    clearRouteError
  } = useSimulationStore();

  // Vehicle type options - 只包含后端支持的车辆类型
  const vehicleTypes = [
    { value: 'pedestrian', label: '🚶 行人 Pedestrian', description: '步行，最高速度 5 km/h，可使用人行道' },
    { value: 'motorcycle', label: '🏍️ 摩托車 Motorcycle', description: '摩托车，最高速度 60 km/h，最小道路宽度 1.2m' },
    { value: 'car', label: '🚗 汽車 Car', description: '一般私家車，最高速度 50 km/h，最小道路宽度 2.2m' },
    { value: 'ambulance', label: '🚑 救護車 Ambulance', description: '救護車，最高速度 80 km/h，最小道路宽度 3.0m' },
    { value: 'fire_truck', label: '🚒 消防車 Fire Truck', description: '消防車，最高速度 60 km/h，最小道路宽度 3.5m' }
  ];

  const handleCalculateRoute = async () => {
    try {
      await calculateRoute();
    } catch (error) {
      console.error('Route calculation error:', error);
    }
  };

  const handleClearRoute = () => {
    clearRoutePoints();
    clearRouteError();
  };

  const routeStats = getRouteStats();
  const hasMapData = Boolean(mapData);
  const hasDisasterData = Boolean(disasterSimulationData);
  const hasStartPoint = Boolean(routePlanning.startPoint);
  const hasEndPoint = Boolean(routePlanning.endPoint);
  const canCalculateRoute = hasMapData && hasStartPoint && hasEndPoint;
  const isCalculating = routePlanning.isCalculatingRoute;

  return (
    <Card title="路線規劃 (SE-2.2 Route Planning)" collapsible={true}>
      {!hasMapData && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div className="flex items-center">
            <span className="text-yellow-600 text-lg mr-2">⚠️</span>
            <div>
              <p className="text-yellow-800 font-medium">請先生成地圖</p>
              <p className="text-yellow-600 text-sm">需要地圖資料才能進行路線規劃</p>
            </div>
          </div>
        </div>
      )}

      {hasMapData && (
        <div className="space-y-4">
          {/* Waypoint Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                路線設定
              </label>
              {(hasStartPoint || hasEndPoint) && (
                <button
                  onClick={handleClearRoute}
                  className="text-xs text-red-600 hover:text-red-800 underline"
                >
                  清除路線
                </button>
              )}
            </div>

            {/* Start Point */}
            <div className="flex items-center space-x-2">
              <button
                onClick={enableStartPointSelection}
                disabled={routePlanning.isSettingStartPoint}
                className={`flex-1 flex items-center space-x-2 px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${
                  routePlanning.isSettingStartPoint
                    ? 'bg-green-100 border-green-300 text-green-700'
                    : hasStartPoint
                    ? 'bg-green-50 border-green-200 text-green-700'
                    : 'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span className="text-lg">🟢</span>
                <div className="flex-1 text-left">
                  <div className="font-medium">起點</div>
                  {hasStartPoint ? (
                    <div className="text-xs opacity-75">
                      ({routePlanning.startPoint[0].toFixed(1)}, {routePlanning.startPoint[1].toFixed(1)})
                    </div>
                  ) : routePlanning.isSettingStartPoint ? (
                    <div className="text-xs">點擊地圖設定...</div>
                  ) : (
                    <div className="text-xs">點擊設定起點</div>
                  )}
                </div>
              </button>
            </div>

            {/* End Point */}
            <div className="flex items-center space-x-2">
              <button
                onClick={enableEndPointSelection}
                disabled={routePlanning.isSettingEndPoint}
                className={`flex-1 flex items-center space-x-2 px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${
                  routePlanning.isSettingEndPoint
                    ? 'bg-red-100 border-red-300 text-red-700'
                    : hasEndPoint
                    ? 'bg-red-50 border-red-200 text-red-700'
                    : 'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span className="text-lg">🔴</span>
                <div className="flex-1 text-left">
                  <div className="font-medium">終點</div>
                  {hasEndPoint ? (
                    <div className="text-xs opacity-75">
                      ({routePlanning.endPoint[0].toFixed(1)}, {routePlanning.endPoint[1].toFixed(1)})
                    </div>
                  ) : routePlanning.isSettingEndPoint ? (
                    <div className="text-xs">點擊地圖設定...</div>
                  ) : (
                    <div className="text-xs">點擊設定終點</div>
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* Vehicle Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              車輛類型
            </label>
            <select
              value={routePlanning.vehicleType}
              onChange={(e) => setRouteVehicleType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {vehicleTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {vehicleTypes.find(t => t.value === routePlanning.vehicleType)?.description}
            </p>
          </div>



          {/* Calculate Route Button */}
          <button
            onClick={handleCalculateRoute}
            disabled={!canCalculateRoute || isCalculating}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              canCalculateRoute && !isCalculating
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {isCalculating ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
                計算路線中...
              </div>
            ) : (
              '🚀 計算最佳路線'
            )}
          </button>

          {/* Error Display */}
          {routePlanning.routeError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-start">
                <span className="text-red-500 text-sm mr-2">❌</span>
                <div>
                  <p className="text-red-800 text-sm font-medium">路線計算失敗</p>
                  <p className="text-red-600 text-xs mt-1">{routePlanning.routeError}</p>
                </div>
              </div>
            </div>
          )}

          {/* Route Statistics */}
          {routeStats && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-800 mb-3">📊 路線統計</h4>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(routeStats).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-gray-600">{key}:</span>
                    <span className="font-mono text-gray-800">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}


          {/* Layer Visibility Controls */}
          {(routePlanning.preDisasterRoute || routePlanning.postDisasterRoute) && (
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                圖層顯示
              </label>
              
              <div className="space-y-2">
                {/* Pre-disaster Route */}
                {routePlanning.preDisasterRoute && (routePlanning.preDisasterRoute.success || routePlanning.preDisasterRoute.is_partial_path) && (
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={routeLayerVisibility.preDisasterRoute}
                      onChange={() => toggleRouteLayer('preDisasterRoute')}
                      className="rounded border-gray-300 text-green-600"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      <span className="inline-block w-3 h-3 bg-green-500 rounded mr-1"></span>
                      災前路徑 (綠色)
                    </span>
                  </label>
                )}

                {/* Post-disaster Route */}
                {routePlanning.postDisasterRoute && (routePlanning.postDisasterRoute.success || routePlanning.postDisasterRoute.is_partial_path) && (
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={routeLayerVisibility.postDisasterRoute}
                      onChange={() => toggleRouteLayer('postDisasterRoute')}
                      className="rounded border-gray-300 text-red-600"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      <span className="inline-block w-3 h-3 bg-red-500 rounded mr-1"></span>
                      災後路徑 (紅色)
                    </span>
                  </label>
                )}



                {/* Route Info */}
                {routePlanning.routeStats && (
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={routeLayerVisibility.routeInfo}
                      onChange={() => toggleRouteLayer('routeInfo')}
                      className="rounded border-gray-300 text-blue-600"
                    />
                    <span className="ml-2 text-sm text-gray-700">路徑資訊面板</span>
                  </label>
                )}
              </div>
            </div>
          )}


          {!hasDisasterData && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center">
                <span className="text-blue-600 text-lg mr-2">💡</span>
                <div>
                  <p className="text-blue-800 text-sm font-medium">提示</p>
                  <p className="text-blue-600 text-xs">
                    執行災害模擬後可以比較災前災後路徑差異
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default RoutePlanningPanel;