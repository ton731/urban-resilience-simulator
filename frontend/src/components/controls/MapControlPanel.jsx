import React from 'react';
import { useNavigate } from 'react-router-dom';
import useSimulationStore from '../../store/useSimulationStore';
import Button from '../ui/Button';
import Card from '../ui/Card';
import DisasterSimulationPanel from './DisasterSimulationPanel';
import RoutePlanningPanel from './RoutePlanningPanel';

const MapControlPanel = () => {
  const navigate = useNavigate();
  const {
    layerVisibility,
    mapStats,
    clearMapData,
    toggleLayer,
    toggleTreeVulnerability,
    toggleBuildings,
    toggleBuildingType
  } = useSimulationStore();

  const handleBackToGenerate = () => {
    navigate('/generate');
  };

  const handleRegenerateMap = () => {
    clearMapData();
    navigate('/generate');
  };

  return (
    <div className="w-80 bg-gray-50 p-4 overflow-y-auto">
      <div className="space-y-4">
        
        {/* Navigation Controls */}
        <Card title="導航控制 (Navigation)">
          <div className="space-y-2">
            <Button
              onClick={handleBackToGenerate}
              variant="secondary"
              size="medium"
              className="w-full"
            >
              ← 返回設定
            </Button>
            <Button
              onClick={handleRegenerateMap}
              variant="primary"
              size="medium"
              className="w-full"
            >
              🔄 重新生成地圖
            </Button>
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

            {/* Building Layers */}
            {mapStats && mapStats.totalBuildings > 0 && (
              <div className="border-t border-gray-200 pt-3 mt-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={layerVisibility.buildings}
                    onChange={() => toggleBuildings()}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 font-medium">
                    🏢 建築物 (Buildings) - {mapStats.totalBuildings}
                  </span>
                </label>
                
                {/* Building types */}
                <div className="ml-4 space-y-2 mt-2">
                  {[
                    { type: 'residential', label: '住宅建築', emoji: '🏘️', color: 'text-blue-600', bgColor: 'bg-blue-500' },
                    { type: 'commercial', label: '商業建築', emoji: '🏢', color: 'text-amber-600', bgColor: 'bg-amber-500' },
                    { type: 'mixed', label: '混合建築', emoji: '🏬', color: 'text-purple-600', bgColor: 'bg-purple-500' },
                    { type: 'industrial', label: '工業建築', emoji: '🏭', color: 'text-gray-600', bgColor: 'bg-gray-500' }
                  ].map(({ type, label, emoji, color, bgColor }) => {
                    const count = mapStats.buildingsByType?.[type] || 0;
                    const populationCount = mapStats.populationStats?.population_by_type?.[type] || 0;
                    
                    return (
                      <label key={type} className="flex items-center text-xs">
                        <input
                          type="checkbox"
                          checked={layerVisibility.buildingsByType?.[type]}
                          onChange={() => toggleBuildingType(type)}
                          className={`rounded border-gray-300 focus:ring-2 ${color.replace('text-', 'text-')} focus:ring-${color.split('-')[1]}-500`}
                        />
                        <div className={`ml-2 w-4 h-4 ${bgColor} rounded flex items-center justify-center text-white text-xs`}>{emoji}</div>
                        <span className={`ml-1 ${color}`}>
                          {label}: {count} 棟 ({populationCount} 人)
                        </span>
                      </label>
                    );
                  })}
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
              {mapStats.totalBuildings > 0 && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-600">建築物總數:</span>
                    <span className="font-medium text-purple-600">{mapStats.totalBuildings}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">總人口:</span>
                    <span className="font-medium text-indigo-600">{mapStats.totalPopulation?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">人口密度:</span>
                    <span className="font-medium text-indigo-600">{Math.round(mapStats.populationDensity || 0)} /km²</span>
                  </div>
                </>
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
        
        {/* Disaster Simulation Panel */}
        <DisasterSimulationPanel />
        
        {/* Route Planning Panel */}
        <RoutePlanningPanel />

      </div>
    </div>
  );
};

export default MapControlPanel;