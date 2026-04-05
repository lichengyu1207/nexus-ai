"""
奖励函数系统
Reward Function System

为各智能体定义奖励信号，用于强化学习训练
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """智能体类型"""
    ZHONGSHU = "zhongshu"  # 中书省 - 决策
    MENSHANG = "menshang"  # 门下省 - 审核
    SHANGSHU = "shangshu"  # 尚书省 - 执行
    LI_BU = "li_bu"        # 吏部 - 管理
    HU_BU = "hu_bu"        # 户部 - 积分
    LI_BU_CONSULT = "li_bu_consult"  # 礼部 - 咨询
    BING_BU = "bing_bu"    # 兵部 - 采集
    XING_BU = "xing_bu"    # 刑部 - 风控
    GONG_BU = "gong_bu"    # 工部 - 分析


@dataclass
class RewardConfig:
    """奖励配置"""
    # 中书省奖励
    task_decomposition_correct: float = 1.0
    unnecessary_subtask_penalty: float = -0.5
    fast_response_bonus: float = 0.2
    slow_response_penalty: float = -1.0
    fast_response_threshold: float = 2.0
    slow_response_threshold: float = 5.0
    
    # 门下省奖励
    correct_interception: float = 1.0
    missed_violation_penalty: float = -2.0
    false_positive_penalty: float = -1.0
    
    # 工部奖励
    valuation_error_low: float = 1.0
    valuation_error_medium: float = 0.5
    valuation_error_high: float = -1.0
    error_low_threshold: float = 0.03
    error_medium_threshold: float = 0.05
    
    # 礼部奖励
    high_user_rating: float = 1.0
    low_user_rating_penalty: float = -2.0
    high_rating_threshold: float = 4.5
    low_rating_threshold: float = 3.0
    
    # 协同奖励
    fast_task_completion: float = 0.5
    low_communication_delay: float = 0.2
    cost_saving: float = 0.1
    task_completion_threshold: float = 10.0
    communication_delay_threshold: float = 0.03


class RewardCalculator:
    """
    奖励计算器
    
    根据智能体类型和执行结果计算奖励值
    """
    
    def __init__(self, config: Optional[RewardConfig] = None):
        self.config = config or RewardConfig()
        self.reward_history: Dict[str, List[float]] = {}
        
        logger.info("RewardCalculator initialized")
    
    def calculate_reward(
        self,
        agent_type: str,
        execution_result: Dict,
        context: Optional[Dict] = None
    ) -> float:
        """
        计算奖励
        
        Args:
            agent_type: 智能体类型
            execution_result: 执行结果
            context: 额外上下文
            
        Returns:
            奖励值
        """
        context = context or {}
        
        if agent_type == AgentType.ZHONGSHU.value:
            reward = self._calculate_zhongshu_reward(execution_result, context)
        elif agent_type == AgentType.MENSHANG.value:
            reward = self._calculate_menshang_reward(execution_result, context)
        elif agent_type == AgentType.GONG_BU.value:
            reward = self._calculate_gongbu_reward(execution_result, context)
        elif agent_type == AgentType.LI_BU_CONSULT.value:
            reward = self._calculate_libu_reward(execution_result, context)
        elif agent_type == AgentType.BING_BU.value:
            reward = self._calculate_bingbu_reward(execution_result, context)
        elif agent_type == AgentType.XING_BU.value:
            reward = self._calculate_xingbu_reward(execution_result, context)
        else:
            reward = self._calculate_general_reward(execution_result, context)
        
        if agent_type not in self.reward_history:
            self.reward_history[agent_type] = []
        self.reward_history[agent_type].append(reward)
        
        return reward
    
    def _calculate_zhongshu_reward(self, result: Dict, context: Dict) -> float:
        """计算中书省奖励"""
        reward = 0.0
        
        if result.get("decomposition_correct"):
            reward += self.config.task_decomposition_correct
        
        if result.get("unnecessary_subtasks", 0) > 0:
            reward += self.config.unnecessary_subtask_penalty * result["unnecessary_subtasks"]
        
        response_time = result.get("response_time", 0)
        if response_time < self.config.fast_response_threshold:
            reward += self.config.fast_response_bonus
        elif response_time > self.config.slow_response_threshold:
            reward += self.config.slow_response_penalty
        
        return reward
    
    def _calculate_menshang_reward(self, result: Dict, context: Dict) -> float:
        """计算门下省奖励"""
        reward = 0.0
        
        if result.get("intercepted_violation"):
            if result.get("was_actual_violation"):
                reward += self.config.correct_interception
            else:
                reward += self.config.false_positive_penalty
        
        if result.get("missed_violation"):
            reward += self.config.missed_violation_penalty
        
        return reward
    
    def _calculate_gongbu_reward(self, result: Dict, context: Dict) -> float:
        """计算工部奖励"""
        reward = 0.0
        
        error_rate = result.get("error_rate")
        if error_rate is not None:
            if error_rate < self.config.error_low_threshold:
                reward += self.config.valuation_error_low
            elif error_rate < self.config.error_medium_threshold:
                reward += self.config.valuation_error_medium
            else:
                reward += self.config.valuation_error_high
        
        confidence = result.get("confidence", 0)
        if confidence > 0.9:
            reward += 0.5
        elif confidence < 0.5:
            reward -= 0.3
        
        return reward
    
    def _calculate_libu_reward(self, result: Dict, context: Dict) -> float:
        """计算礼部奖励"""
        reward = 0.0
        
        user_rating = result.get("user_rating")
        if user_rating is not None:
            if user_rating >= self.config.high_rating_threshold:
                reward += self.config.high_user_rating
            elif user_rating < self.config.low_rating_threshold:
                reward += self.config.low_user_rating_penalty
        
        response_quality = result.get("response_quality", 0)
        reward += response_quality * 0.5
        
        return reward
    
    def _calculate_bingbu_reward(self, result: Dict, context: Dict) -> float:
        """计算兵部奖励"""
        reward = 0.0
        
        records_collected = result.get("records_collected", 0)
        reward += records_collected * 0.01
        
        quality_score = result.get("quality_score", 0)
        if quality_score > 0.8:
            reward += 0.5
        elif quality_score < 0.5:
            reward -= 0.3
        
        coverage_rate = result.get("coverage_rate", 0)
        reward += coverage_rate * 0.5
        
        return reward
    
    def _calculate_xingbu_reward(self, result: Dict, context: Dict) -> float:
        """计算刑部奖励"""
        reward = 0.0
        
        if result.get("anomaly_detected"):
            if result.get("was_actual_anomaly"):
                reward += 1.0
            else:
                reward -= 0.5
        
        risk_assessment_accuracy = result.get("risk_assessment_accuracy", 0)
        reward += risk_assessment_accuracy * 0.5
        
        return reward
    
    def _calculate_general_reward(self, result: Dict, context: Dict) -> float:
        """计算通用奖励"""
        reward = 0.0
        
        if result.get("success"):
            reward += 1.0
        else:
            reward -= 0.5
        
        execution_time = result.get("execution_time", 0)
        if execution_time < 5:
            reward += 0.2
        elif execution_time > 30:
            reward -= 0.3
        
        return reward
    
    def calculate_collaborative_reward(
        self,
        agent_results: Dict[str, Dict],
        task_completion_time: float,
        communication_delay: float,
        api_cost: float,
        cost_budget: float
    ) -> float:
        """计算协同奖励"""
        reward = 0.0
        
        if task_completion_time < self.config.task_completion_threshold:
            reward += self.config.fast_task_completion
        
        if communication_delay < self.config.communication_delay_threshold:
            reward += self.config.low_communication_delay
        
        if api_cost < cost_budget:
            savings = cost_budget - api_cost
            reward += self.config.cost_saving * savings
        
        success_count = sum(1 for r in agent_results.values() if r.get("success"))
        total_count = len(agent_results)
        if total_count > 0:
            reward += (success_count / total_count) * 0.5
        
        return reward
    
    def get_statistics(self) -> Dict:
        """获取奖励统计"""
        stats = {}
        
        for agent_type, rewards in self.reward_history.items():
            if rewards:
                stats[agent_type] = {
                    "total_rewards": sum(rewards),
                    "avg_reward": sum(rewards) / len(rewards),
                    "max_reward": max(rewards),
                    "min_reward": min(rewards),
                    "count": len(rewards),
                }
        
        return stats
    
    def reset_history(self):
        """重置历史记录"""
        self.reward_history.clear()


_global_calculator: Optional[RewardCalculator] = None


def get_reward_calculator() -> RewardCalculator:
    """获取全局奖励计算器实例"""
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = RewardCalculator()
    return _global_calculator
