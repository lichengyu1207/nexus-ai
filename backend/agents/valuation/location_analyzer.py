"""
区位分析智能体
Location Analysis Agent

重点评估地理位置和配套价值，输出估价P1
"""

import logging
import numpy as np
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LocationAnalysisResult:
    """区位分析结果"""
    p1: float  # 区位估价
    factors: Dict[str, float]  # 各因素得分
    confidence: float  # 置信度
    metadata: Dict[str, Any] = None


class LocationAnalyzer:
    """区位分析智能体"""
    
    def __init__(self):
        # 区位因素权重
        self.weights = {
            "distance_to_subway": 0.3,  # 距地铁距离（权重最高）
            "school_district_level": 0.25,  # 学区等级
            "greening_rate": 0.15,  # 绿化率
            "total_floors": 0.1,  # 总楼层（间接反映小区品质）
            "is_elevator": 0.1,  # 是否有电梯
            "property_type": 0.1  # 物业类型
        }
        
        # 基础价格范围（元/㎡）
        self.base_price_range = {
            "apartment": (50000, 100000),
            "house": (80000, 150000),
            "villa": (120000, 200000)
        }
    
    def analyze_location(self, features: Dict[str, float], metadata: Dict[str, Any] = None) -> LocationAnalysisResult:
        """分析区位价值"""
        # 计算区位得分
        location_score = 0.0
        factors = {}
        
        # 距地铁距离得分（距离越近得分越高）
        subway_distance = features.get("distance_to_subway", 1.0)
        subway_score = max(0, 1.0 - subway_distance)  # 归一化后距离越近值越小
        factors["subway_distance"] = subway_score
        
        # 学区等级得分
        school_level = features.get("school_district_level", 0.0)
        school_score = min(1.0, school_level / 3.0)  # 假设学区等级最高为3
        factors["school_district"] = school_score
        
        # 绿化率得分
        greening = features.get("greening_rate", 0.0)
        greening_score = greening
        factors["greening_rate"] = greening_score
        
        # 总楼层得分（间接反映小区品质）
        total_floors = features.get("total_floors", 0.0)
        floor_score = total_floors
        factors["total_floors"] = floor_score
        
        # 电梯得分
        elevator = features.get("is_elevator", 0.0)
        elevator_score = elevator
        factors["is_elevator"] = elevator_score
        
        # 物业类型得分
        property_type = features.get("property_type", 0.0)
        property_score = property_type
        factors["property_type"] = property_score
        
        # 计算加权总分
        for factor, weight in self.weights.items():
            if factor in factors:
                location_score += factors[factor] * weight
        
        # 确定物业类型
        property_type_code = features.get("property_type", 0.0)
        property_type_str = "apartment"  # 默认公寓
        if property_type_code > 0.5:
            property_type_str = "house"
        
        # 计算基础价格范围
        min_price, max_price = self.base_price_range.get(property_type_str, (50000, 100000))
        
        # 根据区位得分计算估价
        p1 = min_price + (max_price - min_price) * location_score
        
        # 计算置信度
        confidence = min(1.0, location_score + 0.3)  # 基础置信度 + 得分影响
        
        # 生成元数据
        analysis_metadata = {
            "property_type": property_type_str,
            "location_score": location_score,
            "base_price_range": (min_price, max_price),
            "analysis_time": metadata.get("analysis_time", None) if metadata else None
        }
        
        return LocationAnalysisResult(
            p1=p1,
            factors=factors,
            confidence=confidence,
            metadata=analysis_metadata
        )
    
    def batch_analyze(self, features_list: List[Dict[str, float]], metadata_list: List[Dict[str, Any]] = None) -> List[LocationAnalysisResult]:
        """批量分析区位价值"""
        results = []
        metadata_list = metadata_list or [{} for _ in features_list]
        
        for features, metadata in zip(features_list, metadata_list):
            result = self.analyze_location(features, metadata)
            results.append(result)
        
        return results


# 示例使用
if __name__ == "__main__":
    analyzer = LocationAnalyzer()
    
    # 示例特征
    sample_features = {
        "distance_to_subway": 0.3,  # 归一化后的值，越小表示距离越近
        "school_district_level": 0.0,  # A级学区
        "greening_rate": 0.5,  # 35%绿化率
        "total_floors": 0.6667,  # 30层
        "is_elevator": 1.0,  # 有电梯
        "property_type": 0.0  # 公寓
    }
    
    result = analyzer.analyze_location(sample_features)
    print(f"区位估价P1: {result.p1:.2f} 元/㎡")
    print(f"各因素得分: {result.factors}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"元数据: {result.metadata}")
