"""
路由决策模块
根据任务特征和预算选择模型
"""

import os
import json
import logging
import random
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    """路由决策"""
    model_name: str  # 选择的模型名称
    confidence: float  # 决策置信度
    reason: str  # 决策原因


class RouteDecisionMaker:
    """路由决策器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "route_config.json"
        )
        self.config = self._load_config()
        self.q_table = self._load_q_table()
        self.alpha = 0.1  # 学习率
        self.gamma = 0.9  # 折扣因子
        self.epsilon = 0.1  # 探索率
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "reward_weights": {
                "accuracy": 1.0,
                "cost": 0.5,
                "delay": 0.3
            },
            "complexity_thresholds": {
                "low": 0.3,
                "medium": 0.7
            },
            "budget": {
                "daily_limit": 100.0,
                "warning_threshold": 80.0,
                "degradation_threshold": 95.0
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
        
        # 保存默认配置
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def _load_q_table(self) -> Dict[str, Dict[str, float]]:
        """加载Q表"""
        q_table_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "q_table.json"
        )
        
        try:
            if os.path.exists(q_table_file):
                with open(q_table_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载Q表失败: {e}")
        
        # 返回空Q表
        return {}
    
    def _save_q_table(self):
        """保存Q表"""
        q_table_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "q_table.json"
        )
        
        try:
            os.makedirs(os.path.dirname(q_table_file), exist_ok=True)
            with open(q_table_file, "w", encoding="utf-8") as f:
                json.dump(self.q_table, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存Q表失败: {e}")
    
    def _get_state_key(self, task_type: str, complexity: float) -> str:
        """获取状态键
        
        Args:
            task_type: 任务类型
            complexity: 复杂度
            
        Returns:
            状态键
        """
        # 根据复杂度划分状态
        if complexity < self.config["complexity_thresholds"]["low"]:
            complexity_level = "low"
        elif complexity < self.config["complexity_thresholds"]["medium"]:
            complexity_level = "medium"
        else:
            complexity_level = "high"
        
        return f"{task_type}_{complexity_level}"
    
    def make_decision(self, task_type: str, complexity: float, available_models: List[Tuple[str, Any]], current_cost: float) -> RouteDecision:
        """做出路由决策
        
        Args:
            task_type: 任务类型
            complexity: 复杂度
            available_models: 可用模型列表
            current_cost: 当前日累计成本
            
        Returns:
            路由决策
        """
        logger.info(f"做出路由决策: 任务类型={task_type}, 复杂度={complexity:.2f}, 当前成本=¥{current_cost:.2f}")
        
        # 检查预算
        if current_cost >= self.config["budget"]["degradation_threshold"]:
            # 触发降级策略，选择轻量模型
            for model_name, _ in available_models:
                if "qwen" in model_name.lower():
                    return RouteDecision(
                        model_name=model_name,
                        confidence=1.0,
                        reason="预算超限，触发降级策略"
                    )
        elif current_cost >= self.config["budget"]["warning_threshold"]:
            logger.warning(f"预算预警: 当前成本 ¥{current_cost:.2f} 接近上限")
        
        # 获取状态
        state_key = self._get_state_key(task_type, complexity)
        
        # 探索或利用
        if random.random() < self.epsilon:
            # 探索
            model_name = random.choice([model[0] for model in available_models])
            confidence = 0.5
            reason = "探索策略"
        else:
            # 利用
            model_name, confidence = self._select_best_model(state_key, available_models)
            reason = "利用策略"
        
        decision = RouteDecision(
            model_name=model_name,
            confidence=confidence,
            reason=reason
        )
        
        logger.info(f"路由决策: {decision}")
        return decision
    
    def _select_best_model(self, state_key: str, available_models: List[Tuple[str, Any]]) -> Tuple[str, float]:
        """选择最佳模型
        
        Args:
            state_key: 状态键
            available_models: 可用模型列表
            
        Returns:
            (模型名称, 置信度)
        """
        # 获取状态的Q值
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        state_q = self.q_table[state_key]
        model_names = [model[0] for model in available_models]
        
        # 计算每个模型的Q值
        q_values = {}
        for model_name in model_names:
            q_values[model_name] = state_q.get(model_name, 0.0)
        
        # 选择Q值最高的模型
        best_model = max(q_values, key=q_values.get)
        confidence = q_values[best_model] / (sum(q_values.values()) + 1e-9)
        
        return best_model, confidence
    
    def update_policy(self, task_type: str, complexity: float, model_name: str, reward: float):
        """更新路由策略
        
        Args:
            task_type: 任务类型
            complexity: 复杂度
            model_name: 选择的模型
            reward: 奖励值
        """
        # 获取状态
        state_key = self._get_state_key(task_type, complexity)
        
        # 初始化状态
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        # 获取当前Q值
        current_q = self.q_table[state_key].get(model_name, 0.0)
        
        # 更新Q值
        new_q = current_q + self.alpha * (reward - current_q)
        self.q_table[state_key][model_name] = new_q
        
        # 保存Q表
        self._save_q_table()
        
        logger.info(f"更新策略: 状态={state_key}, 模型={model_name}, 奖励={reward:.2f}, 新Q值={new_q:.2f}")
    
    def calculate_reward(self, accuracy: float, cost: float, delay: float) -> float:
        """计算奖励
        
        Args:
            accuracy: 准确率
            cost: 成本
            delay: 延迟
            
        Returns:
            奖励值
        """
        weights = self.config["reward_weights"]
        reward = (
            weights["accuracy"] * accuracy - 
            weights["cost"] * cost - 
            weights["delay"] * delay
        )
        return reward
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置
        
        Returns:
            配置
        """
        return self.config
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self.config.update(config)
        self._save_config(self.config)
        logger.info("更新配置成功")


# 全局决策器实例
route_decision_maker: Optional[RouteDecisionMaker] = None


def get_route_decision_maker() -> RouteDecisionMaker:
    """获取路由决策器实例"""
    global route_decision_maker
    if route_decision_maker is None:
        route_decision_maker = RouteDecisionMaker()
    return route_decision_maker


def make_route_decision(task_type: str, complexity: float, available_models: List[Tuple[str, Any]], current_cost: float) -> RouteDecision:
    """做出路由决策"""
    decision_maker = get_route_decision_maker()
    return decision_maker.make_decision(task_type, complexity, available_models, current_cost)


def update_route_policy(task_type: str, complexity: float, model_name: str, reward: float):
    """更新路由策略"""
    decision_maker = get_route_decision_maker()
    decision_maker.update_policy(task_type, complexity, model_name, reward)


def calculate_reward(accuracy: float, cost: float, delay: float) -> float:
    """计算奖励"""
    decision_maker = get_route_decision_maker()
    return decision_maker.calculate_reward(accuracy, cost, delay)
