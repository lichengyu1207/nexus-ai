"""
户型分析智能体
Layout Analysis Agent

评估户型结构和朝向，输出估价P2
"""

import logging
import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LayoutAnalysisResult:
    """户型分析结果"""
    p2: float  # 户型估价
    factors: Dict[str, float]  # 各因素得分
    confidence: float  # 置信度
    metadata: Dict[str, Any] = None


class LayoutAnalyzer:
    """户型分析智能体"""
    
    def __init__(self):
        # 户型因素权重
        self.weights = {
            "room_count": 0.25,  # 房间数量
            "bathroom_count": 0.2,  # 卫生间数量
            "total_area": 0.2,  # 总面积
            "floor": 0.15,  # 楼层
            "building_age": 0.1,  # 房龄
            "is_elevator": 0.1  # 是否有电梯
        }
        
        # 基础价格调整系数（基于户型评分）
        self.price_adjustment = {
            "excellent": 1.1,  # 优秀户型
            "good": 1.05,       # 良好户型
            "average": 1.0,      # 普通户型
            "poor": 0.95        # 较差户型
        }
    
    def analyze_layout(self, features: Dict[str, float], base_price: float, metadata: Dict[str, Any] = None) -> LayoutAnalysisResult:
        """分析户型价值"""
        # 计算户型得分
        layout_score = 0.0
        factors = {}
        
        # 房间数量得分
        room_count = features.get("room_count", 0.0)
        room_score = room_count
        factors["room_count"] = room_score
        
        # 卫生间数量得分
        bathroom_count = features.get("bathroom_count", 0.0)
        bathroom_score = bathroom_count
        factors["bathroom_count"] = bathroom_score
        
        # 总面积得分
        total_area = features.get("total_area", 0.0)
        area_score = total_area
        factors["total_area"] = area_score
        
        # 楼层得分（中间楼层最好）
        floor = features.get("floor", 0.0)
        # 中间楼层（0.3-0.7）得分最高
        if 0.3 <= floor <= 0.7:
            floor_score = 1.0
        elif 0.1 <= floor < 0.3 or 0.7 < floor <= 0.9:
            floor_score = 0.8
        else:
            floor_score = 0.6
        factors["floor"] = floor_score
        
        # 房龄得分（越新得分越高）
        building_age = features.get("building_age", 0.0)
        # 归一化后的值，越小表示房龄越新
        age_score = max(0, 1.0 - building_age)
        factors["building_age"] = age_score
        
        # 电梯得分
        elevator = features.get("is_elevator", 0.0)
        elevator_score = elevator
        factors["is_elevator"] = elevator_score
        
        # 计算加权总分
        for factor, weight in self.weights.items():
            if factor in factors:
                layout_score += factors[factor] * weight
        
        # 确定户型等级
        if layout_score >= 0.8:
            layout_level = "excellent"
        elif layout_score >= 0.6:
            layout_level = "good"
        elif layout_score >= 0.4:
            layout_level = "average"
        else:
            layout_level = "poor"
        
        # 计算户型调整系数
        adjustment_factor = self.price_adjustment.get(layout_level, 1.0)
        
        # 计算户型估价
        p2 = base_price * adjustment_factor
        
        # 计算置信度
        confidence = min(1.0, layout_score + 0.2)  # 基础置信度 + 得分影响
        
        # 生成元数据
        analysis_metadata = {
            "layout_score": layout_score,
            "layout_level": layout_level,
            "adjustment_factor": adjustment_factor,
            "base_price": base_price,
            "analysis_time": metadata.get("analysis_time", None) if metadata else None
        }
        
        return LayoutAnalysisResult(
            p2=p2,
            factors=factors,
            confidence=confidence,
            metadata=analysis_metadata
        )
    
    def batch_analyze(self, features_list: List[Dict[str, float]], base_prices: List[float], metadata_list: List[Dict[str, Any]] = None) -> List[LayoutAnalysisResult]:
        """批量分析户型价值"""
        results = []
        metadata_list = metadata_list or [{} for _ in features_list]
        
        for features, base_price, metadata in zip(features_list, base_prices, metadata_list):
            result = self.analyze_layout(features, base_price, metadata)
            results.append(result)
        
        return results


# 示例使用
if __name__ == "__main__":
    analyzer = LayoutAnalyzer()
    
    # 示例特征
    sample_features = {
        "room_count": 0.5,  # 3室
        "bathroom_count": 0.5,  # 2卫
        "total_area": 0.3333,  # 120㎡
        "floor": 0.5,  # 中间楼层
        "building_age": 0.3333,  # 10年房龄
        "is_elevator": 1.0  # 有电梯
    }
    
    # 基础价格（来自区位分析）
    base_price = 75000  # 元/㎡
    
    result = analyzer.analyze_layout(sample_features, base_price)
    print(f"户型估价P2: {result.p2:.2f} 元/㎡")
    print(f"各因素得分: {result.factors}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"元数据: {result.metadata}")
