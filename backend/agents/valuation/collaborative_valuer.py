"""
协同估价模块
Collaborative Valuation Module

采用注意力机制对P1、P2、P3进行动态加权求和，权重由各智能体在历史任务中的准确率动态决定，得到综合估价结果P。
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AgentHistory:
    """智能体历史记录"""
    agent_type: str  # 智能体类型：location, layout, market
    correct_count: int  # 正确次数
    total_count: int  # 总次数
    accuracy: float  # 准确率
    last_updated: float  # 最后更新时间


@dataclass
class CollaborativeResult:
    """协同估价结果"""
    p: float  # 综合估价
    weights: Dict[str, float]  # 各智能体权重
    individual_values: Dict[str, float]  # 各智能体估价
    attention_scores: Dict[str, float]  # 注意力得分
    metadata: Dict[str, Any] = None


class CollaborativeValuer:
    """协同估价模块"""
    
    def __init__(self):
        # 智能体历史记录
        self.agent_histories = {
            "location": AgentHistory(
                agent_type="location",
                correct_count=100,
                total_count=120,
                accuracy=0.8333,
                last_updated=datetime.now().timestamp()
            ),
            "layout": AgentHistory(
                agent_type="layout",
                correct_count=90,
                total_count=110,
                accuracy=0.8182,
                last_updated=datetime.now().timestamp()
            ),
            "market": AgentHistory(
                agent_type="market",
                correct_count=85,
                total_count=100,
                accuracy=0.85,
                last_updated=datetime.now().timestamp()
            )
        }
        
        # 注意力机制参数
        self.attention_alpha = 0.1  # 注意力学习率
        self.history_decay = 0.9  # 历史准确率衰减因子
    
    def calculate_attention_scores(self, p1: float, p2: float, p3: float, features: Dict[str, float]) -> Dict[str, float]:
        """计算注意力得分"""
        # 基础得分基于历史准确率
        base_scores = {
            "location": self.agent_histories["location"].accuracy,
            "layout": self.agent_histories["layout"].accuracy,
            "market": self.agent_histories["market"].accuracy
        }
        
        # 计算估价差异（差异越小，得分越高）
        values = [p1, p2, p3]
        mean_value = np.mean(values)
        std_value = np.std(values) if len(values) > 1 else 1.0
        
        if std_value == 0:
            std_value = 1.0
        
        # 差异得分
        diff_scores = {
            "location": max(0, 1 - abs(p1 - mean_value) / std_value),
            "layout": max(0, 1 - abs(p2 - mean_value) / std_value),
            "market": max(0, 1 - abs(p3 - mean_value) / std_value)
        }
        
        # 特征相关性得分（基于特征与各智能体的相关性）
        feature_scores = {
            "location": self._calculate_location_feature_score(features),
            "layout": self._calculate_layout_feature_score(features),
            "market": self._calculate_market_feature_score(features)
        }
        
        # 综合得分
        attention_scores = {}
        for agent in ["location", "layout", "market"]:
            # 加权综合得分
            score = (
                0.5 * base_scores[agent] +  # 历史准确率权重
                0.3 * diff_scores[agent] +   # 估价一致性权重
                0.2 * feature_scores[agent]   # 特征相关性权重
            )
            attention_scores[agent] = score
        
        # 归一化注意力得分
        total_score = sum(attention_scores.values())
        if total_score > 0:
            for agent in attention_scores:
                attention_scores[agent] /= total_score
        else:
            # 均分权重
            for agent in attention_scores:
                attention_scores[agent] = 1.0 / 3
        
        return attention_scores
    
    def _calculate_location_feature_score(self, features: Dict[str, float]) -> float:
        """计算区位特征得分"""
        relevant_features = [
            "distance_to_subway",
            "school_district_level",
            "greening_rate",
            "total_floors",
            "is_elevator",
            "property_type"
        ]
        
        score = 0.0
        count = 0
        for feature in relevant_features:
            if feature in features:
                score += abs(features[feature] - 0.5)  # 越接近中间值，得分越高
                count += 1
        
        return score / count if count > 0 else 0.5
    
    def _calculate_layout_feature_score(self, features: Dict[str, float]) -> float:
        """计算户型特征得分"""
        relevant_features = [
            "room_count",
            "bathroom_count",
            "total_area",
            "floor",
            "building_age",
            "is_elevator"
        ]
        
        score = 0.0
        count = 0
        for feature in relevant_features:
            if feature in features:
                score += abs(features[feature] - 0.5)  # 越接近中间值，得分越高
                count += 1
        
        return score / count if count > 0 else 0.5
    
    def _calculate_market_feature_score(self, features: Dict[str, float]) -> float:
        """计算市场特征得分"""
        relevant_features = [
            "price_per_sqm"
        ]
        
        score = 0.0
        count = 0
        for feature in relevant_features:
            if feature in features:
                score += abs(features[feature] - 0.5)  # 越接近中间值，得分越高
                count += 1
        
        return score / count if count > 0 else 0.5
    
    def update_agent_history(self, agent_type: str, is_correct: bool):
        """更新智能体历史记录"""
        if agent_type in self.agent_histories:
            history = self.agent_histories[agent_type]
            history.total_count += 1
            if is_correct:
                history.correct_count += 1
            
            # 更新准确率
            history.accuracy = history.correct_count / history.total_count
            # 应用历史衰减
            history.accuracy = (history.accuracy * (1 - self.history_decay) + 
                             self.agent_histories[agent_type].accuracy * self.history_decay)
            history.last_updated = datetime.now().timestamp()
    
    def calculate_collaborative_value(self, p1: float, p2: float, p3: float, features: Dict[str, float]) -> CollaborativeResult:
        """计算综合估价"""
        # 计算注意力得分
        attention_scores = self.calculate_attention_scores(p1, p2, p3, features)
        
        # 计算加权总和
        p = (
            attention_scores["location"] * p1 +
            attention_scores["layout"] * p2 +
            attention_scores["market"] * p3
        )
        
        # 构建结果
        individual_values = {
            "p1": p1,
            "p2": p2,
            "p3": p3
        }
        
        # 生成元数据
        metadata = {
            "calculation_time": datetime.now().isoformat(),
            "agent_accuracies": {
                "location": self.agent_histories["location"].accuracy,
                "layout": self.agent_histories["layout"].accuracy,
                "market": self.agent_histories["market"].accuracy
            },
            "attention_alpha": self.attention_alpha,
            "history_decay": self.history_decay
        }
        
        return CollaborativeResult(
            p=p,
            weights=attention_scores,
            individual_values=individual_values,
            attention_scores=attention_scores,
            metadata=metadata
        )
    
    def batch_calculate(self, p1_list: List[float], p2_list: List[float], p3_list: List[float], features_list: List[Dict[str, float]]) -> List[CollaborativeResult]:
        """批量计算综合估价"""
        results = []
        
        for p1, p2, p3, features in zip(p1_list, p2_list, p3_list, features_list):
            result = self.calculate_collaborative_value(p1, p2, p3, features)
            results.append(result)
        
        return results


# 示例使用
if __name__ == "__main__":
    valuer = CollaborativeValuer()
    
    # 示例数据
    p1 = 60000.00  # 区位估价
    p2 = 66000.00  # 户型估价
    p3 = 64890.00  # 市场趋势估价
    
    # 示例特征
    features = {
        "building_age": 0.3333,
        "distance_to_subway": 0.3,
        "school_district_level": 0.0,
        "greening_rate": 0.5,
        "price_per_sqm": 0.3636,
        "total_area": 0.3333,
        "room_count": 0.5,
        "bathroom_count": 0.5,
        "floor": 0.5,
        "total_floors": 0.6667,
        "is_elevator": 1.0,
        "property_type": 0.0
    }
    
    result = valuer.calculate_collaborative_value(p1, p2, p3, features)
    print(f"综合估价P: {result.p:.2f} 元/㎡")
    print(f"各智能体权重: {result.weights}")
    print(f"各智能体估价: {result.individual_values}")
    print(f"注意力得分: {result.attention_scores}")
    print(f"元数据: {result.metadata}")
