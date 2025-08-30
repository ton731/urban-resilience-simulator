import uuid
import random
import math
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .map_generator import GeneratedMap, MapNode


class FacilityType(Enum):
    """設施類型枚舉"""
    AMBULANCE_STATION = "ambulance_station"  # 救護車起點（消防分隊、醫院）
    SHELTER = "shelter"  # 避難所


@dataclass
class Facility:
    """代表城市中的關鍵設施"""
    id: str
    x: float
    y: float
    facility_type: FacilityType
    node_id: str  # 所在的道路節點ID
    capacity: Optional[int] = None  # 容量（避難所適用）
    name: Optional[str] = None  # 設施名稱
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "facility_type": self.facility_type.value,
            "node_id": self.node_id,
            "capacity": self.capacity,
            "name": self.name
        }


class FacilityGenerator:
    """
    實作 WS-1.3：關鍵設施生成
    
    在地圖的道路網路節點上生成關鍵設施：
    - 救護車起點（消防分隊、醫院）
    - 避難所
    確保設施與主要交通網路相連。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 設施生成數量配置
        self.ambulance_stations = config.get("ambulance_stations", 3)
        self.shelters = config.get("shelters", 8)
        
        # 避難所容量範圍
        self.shelter_capacity_range = config.get("shelter_capacity_range", [100, 1000])
        
        # 設施名稱前綴
        self.ambulance_station_names = [
            "中央消防分隊", "市立醫院", "區域醫療中心", "急救中心",
            "消防第一分隊", "消防第二分隊", "醫療急救站"
        ]
        
        self.shelter_names = [
            "市民活動中心", "體育館", "學校體育館", "社區中心", 
            "文化中心", "運動中心", "大型會議廳", "展覽館",
            "圖書館", "市政大樓"
        ]
    
    def generate_facilities_for_map(self, generated_map: GeneratedMap) -> Dict[str, Facility]:
        """
        為地圖生成關鍵設施
        
        Args:
            generated_map: 已生成道路網路的地圖
            
        Returns:
            Dict[str, Facility]: 設施字典，facility_id -> Facility
        """
        if not generated_map.nodes:
            raise ValueError("地圖必須包含道路節點才能生成設施")
        
        facilities = {}
        
        # 選擇適合的節點（優先選擇交叉路口且連接度高的節點）
        suitable_nodes = self._select_suitable_nodes(generated_map)
        
        if len(suitable_nodes) < (self.ambulance_stations + self.shelters):
            raise ValueError(
                f"可用節點數量不足：需要 {self.ambulance_stations + self.shelters} 個節點，"
                f"但只找到 {len(suitable_nodes)} 個合適節點"
            )
        
        # 生成救護車起點
        ambulance_facilities = self._generate_ambulance_stations(
            suitable_nodes, generated_map.nodes
        )
        facilities.update(ambulance_facilities)
        
        # 從剩餘節點中生成避難所
        used_nodes = {f.node_id for f in ambulance_facilities.values()}
        available_nodes = [node_id for node_id in suitable_nodes if node_id not in used_nodes]
        
        shelter_facilities = self._generate_shelters(
            available_nodes, generated_map.nodes
        )
        facilities.update(shelter_facilities)
        
        return facilities
    
    def _select_suitable_nodes(self, generated_map: GeneratedMap) -> List[str]:
        """
        選擇適合設置設施的節點
        
        優先級：
        1. 交叉路口節點
        2. 連接度高的節點（連接多條道路）
        3. 位於主幹道上的節點
        
        Args:
            generated_map: 生成的地圖數據
            
        Returns:
            List[str]: 按優先級排序的節點ID列表
        """
        # 計算每個節點的連接度（連接多少條道路）
        node_connections = {}
        for edge in generated_map.edges.values():
            node_connections[edge.from_node] = node_connections.get(edge.from_node, 0) + 1
            node_connections[edge.to_node] = node_connections.get(edge.to_node, 0) + 1
        
        # 統計連接到主幹道的節點
        main_road_nodes = set()
        for edge in generated_map.edges.values():
            if edge.road_type == "main":
                main_road_nodes.add(edge.from_node)
                main_road_nodes.add(edge.to_node)
        
        # 評分節點適合度
        node_scores = []
        for node_id, node in generated_map.nodes.items():
            score = 0
            
            # 基本分數：交叉路口
            if node.node_type == "intersection":
                score += 10
            
            # 連接度分數
            connections = node_connections.get(node_id, 0)
            score += connections * 5
            
            # 主幹道獎勵
            if node_id in main_road_nodes:
                score += 20
            
            # 位置分散獎勵（避免設施太集中）
            # 簡單的位置評分，偏好分散在地圖各個區域
            boundary = generated_map.boundary
            x_ratio = (node.x - boundary.min_x) / boundary.width
            y_ratio = (node.y - boundary.min_y) / boundary.height
            
            # 獎勵非中心位置（提高分散性）
            center_distance = math.sqrt((x_ratio - 0.5)**2 + (y_ratio - 0.5)**2)
            if center_distance > 0.2:  # 距離中心較遠
                score += 5
            
            node_scores.append((score, node_id))
        
        # 按分數排序，返回最佳節點
        node_scores.sort(key=lambda x: x[0], reverse=True)
        return [node_id for score, node_id in node_scores]
    
    def _generate_ambulance_stations(self, suitable_nodes: List[str], 
                                   nodes: Dict[str, MapNode]) -> Dict[str, Facility]:
        """生成救護車起點設施"""
        facilities = {}
        selected_nodes = suitable_nodes[:self.ambulance_stations]
        
        for i, node_id in enumerate(selected_nodes):
            node = nodes[node_id]
            facility_id = str(uuid.uuid4())
            
            # 隨機選擇設施名稱
            name = random.choice(self.ambulance_station_names)
            if i > 0:  # 避免重複名稱
                name = f"{name} {i+1}"
            
            facility = Facility(
                id=facility_id,
                x=node.x,
                y=node.y,
                facility_type=FacilityType.AMBULANCE_STATION,
                node_id=node_id,
                name=name
            )
            
            facilities[facility_id] = facility
        
        return facilities
    
    def _generate_shelters(self, available_nodes: List[str], 
                          nodes: Dict[str, MapNode]) -> Dict[str, Facility]:
        """生成避難所設施"""
        facilities = {}
        selected_nodes = available_nodes[:self.shelters]
        
        for i, node_id in enumerate(selected_nodes):
            node = nodes[node_id]
            facility_id = str(uuid.uuid4())
            
            # 生成避難所容量
            min_capacity, max_capacity = self.shelter_capacity_range
            capacity = random.randint(min_capacity, max_capacity)
            
            # 隨機選擇設施名稱
            name = random.choice(self.shelter_names)
            if i > 0:  # 避免重複名稱
                name = f"{name} {i+1}" if len(selected_nodes) > len(self.shelter_names) else name
            
            facility = Facility(
                id=facility_id,
                x=node.x,
                y=node.y,
                facility_type=FacilityType.SHELTER,
                node_id=node_id,
                capacity=capacity,
                name=name
            )
            
            facilities[facility_id] = facility
        
        return facilities
    
    def get_generation_stats(self, facilities: Dict[str, Facility]) -> Dict[str, Any]:
        """
        獲取設施生成統計
        
        Args:
            facilities: 生成的設施字典
            
        Returns:
            Dict: 統計數據
        """
        if not facilities:
            return {
                "total_facilities": 0,
                "ambulance_stations": 0,
                "shelters": 0,
                "total_shelter_capacity": 0,
                "average_shelter_capacity": 0
            }
        
        ambulance_count = 0
        shelter_count = 0
        total_capacity = 0
        shelter_capacities = []
        
        for facility in facilities.values():
            if facility.facility_type == FacilityType.AMBULANCE_STATION:
                ambulance_count += 1
            elif facility.facility_type == FacilityType.SHELTER:
                shelter_count += 1
                if facility.capacity:
                    total_capacity += facility.capacity
                    shelter_capacities.append(facility.capacity)
        
        return {
            "total_facilities": len(facilities),
            "ambulance_stations": ambulance_count,
            "shelters": shelter_count,
            "total_shelter_capacity": total_capacity,
            "average_shelter_capacity": round(
                sum(shelter_capacities) / len(shelter_capacities) if shelter_capacities else 0, 2
            ),
            "shelter_capacity_range": [
                min(shelter_capacities) if shelter_capacities else 0,
                max(shelter_capacities) if shelter_capacities else 0
            ]
        }
    
    def validate_facility_locations(self, facilities: Dict[str, Facility], 
                                  generated_map: GeneratedMap) -> Dict[str, Any]:
        """
        驗證設施位置的合理性
        
        Args:
            facilities: 生成的設施
            generated_map: 地圖數據
            
        Returns:
            Dict: 驗證結果
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "connectivity_check": True,
            "distribution_score": 0
        }
        
        # 檢查所有設施是否都在有效節點上
        for facility in facilities.values():
            if facility.node_id not in generated_map.nodes:
                validation_results["is_valid"] = False
                validation_results["issues"].append(
                    f"設施 {facility.name} 位於無效節點 {facility.node_id}"
                )
        
        # 檢查設施分布的均勻性
        if len(facilities) >= 2:
            positions = [(f.x, f.y) for f in facilities.values()]
            distribution_score = self._calculate_distribution_score(positions, generated_map.boundary)
            validation_results["distribution_score"] = distribution_score
            
            if distribution_score < 0.3:
                validation_results["issues"].append("設施分布過於集中")
        
        return validation_results
    
    def _calculate_distribution_score(self, positions: List[Tuple[float, float]], 
                                    boundary) -> float:
        """
        計算設施分布均勻性分數 (0-1, 1為最均勻)
        """
        if len(positions) < 2:
            return 1.0
        
        # 計算所有設施間的最小距離
        min_distances = []
        for i, pos1 in enumerate(positions):
            distances = []
            for j, pos2 in enumerate(positions):
                if i != j:
                    dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                    distances.append(dist)
            if distances:
                min_distances.append(min(distances))
        
        # 理想最小距離（假設均勻分布）
        map_area = boundary.width * boundary.height
        ideal_min_distance = math.sqrt(map_area / len(positions)) * 0.5
        
        # 計算分數
        avg_min_distance = sum(min_distances) / len(min_distances)
        score = min(1.0, avg_min_distance / ideal_min_distance)
        
        return round(score, 3)