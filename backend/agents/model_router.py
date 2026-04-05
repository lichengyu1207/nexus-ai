"""
模型路由集成模块
基于分组模型路由的成本优化系统
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple

from backend.agents.task_analyzer import analyze_task, TaskFeatures
from backend.agents.model_manager import get_model_manager, get_models_by_task_type
from backend.agents.route_decision import make_route_decision, update_route_policy, calculate_reward
from backend.agents.cost_monitor import add_cost, get_daily_cost, is_degraded
from backend.agents.feedback_learner import record_feedback

logger = logging.getLogger(__name__)


class ModelRouter:
    """模型路由器"""
    
    def __init__(self):
        self.model_manager = get_model_manager()
    
    def process_request(self, query: str) -> Dict[str, Any]:
        """处理用户请求
        
        Args:
            query: 用户查询
            
        Returns:
            处理结果
        """
        start_time = time.time()
        
        try:
            # 步骤S1: 分析任务
            logger.info(f"处理请求: {query}")
            task_features = analyze_task(query)
            
            # 步骤S2: 查询模型性能-成本映射表
            available_models = get_models_by_task_type(task_features.task_type)
            if not available_models:
                return {
                    "success": False,
                    "error": "没有可用的模型"
                }
            
            # 步骤S3: 路由决策
            current_cost = get_daily_cost()
            decision = make_route_decision(
                task_type=task_features.task_type,
                complexity=task_features.complexity,
                available_models=available_models,
                current_cost=current_cost
            )
            
            # 步骤S4: 调用模型（这里是模拟调用）
            model_info = self.model_manager.get_model_info(decision.model_name)
            if not model_info:
                return {
                    "success": False,
                    "error": f"模型 {decision.model_name} 不存在"
                }
            
            # 模拟模型调用
            response, time_taken, cost = self._simulate_model_call(
                model_name=decision.model_name,
                query=query,
                task_type=task_features.task_type
            )
            
            # 步骤S5: 记录结果
            self._record_result(
                task_features=task_features,
                model_name=decision.model_name,
                response=response,
                time_taken=time_taken,
                cost=cost
            )
            
            # 计算延迟
            total_delay = time.time() - start_time
            
            return {
                "success": True,
                "query": query,
                "task_features": {
                    "task_type": task_features.task_type,
                    "text_length": task_features.text_length,
                    "keywords": task_features.keywords,
                    "complexity": task_features.complexity
                },
                "model": decision.model_name,
                "response": response,
                "decision_reason": decision.reason,
                "confidence": decision.confidence,
                "time_taken": time_taken,
                "total_delay": total_delay,
                "cost": cost,
                "current_daily_cost": get_daily_cost()
            }
            
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _simulate_model_call(self, model_name: str, query: str, task_type: str) -> Tuple[str, float, float]:
        """模拟模型调用
        
        Args:
            model_name: 模型名称
            query: 用户查询
            task_type: 任务类型
            
        Returns:
            (响应, 耗时, 成本)
        """
        # 模拟不同模型的响应
        if "qwen" in model_name.lower():
            # 轻量模型
            if "房价" in query and "深圳" in query:
                response = "南山区二手房均价约9.8万/㎡"
            else:
                response = "这是一个轻量模型的响应"
            time_taken = 0.4  # 秒
            cost = 0.0005  # 元
        elif "deepseek" in model_name.lower():
            # 大模型
            if "房价" in query and "深圳" in query:
                response = "根据最新数据，深圳市南山区的二手房均价约为9.8万元/平方米，具体价格会因楼盘位置、年限、户型等因素有所差异。"
            else:
                response = "这是一个大模型的详细响应"
            time_taken = 1.2  # 秒
            cost = 0.02  # 元
        else:
            # 默认响应
            response = "模型响应"
            time_taken = 0.5  # 秒
            cost = 0.001  # 元
        
        # 模拟网络延迟
        time.sleep(time_taken * 0.5)
        
        return response, time_taken, cost
    
    def _record_result(self, task_features: TaskFeatures, model_name: str, 
                      response: str, time_taken: float, cost: float):
        """记录结果
        
        Args:
            task_features: 任务特征
            model_name: 模型名称
            response: 模型响应
            time_taken: 耗时
            cost: 成本
        """
        # 更新模型性能
        self.model_manager.update_model_performance(
            model_name=model_name,
            task_type=task_features.task_type,
            time_taken=time_taken,
            cost=cost
        )
        
        # 添加成本
        add_cost(cost)
        
        # 模拟准确率（实际应用中应根据用户反馈或自动评估）
        accuracy = 0.92 if "qwen" in model_name.lower() else 0.98
        
        # 计算奖励并更新路由策略
        reward = calculate_reward(accuracy, cost, time_taken)
        update_route_policy(
            task_type=task_features.task_type,
            complexity=task_features.complexity,
            model_name=model_name,
            reward=reward
        )
        
        # 记录反馈
        record_feedback(
            task_type=task_features.task_type,
            complexity=task_features.complexity,
            model_name=model_name,
            accuracy=accuracy,
            cost=cost,
            delay=time_taken
        )
    
    def get_router_status(self) -> Dict[str, Any]:
        """获取路由器状态
        
        Returns:
            状态信息
        """
        return {
            "daily_cost": get_daily_cost(),
            "is_degraded": is_degraded(),
            "models": list(self.model_manager.get_all_models().keys())
        }


# 全局路由器实例
model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """获取模型路由器实例"""
    global model_router
    if model_router is None:
        model_router = ModelRouter()
    return model_router


def process_request(query: str) -> Dict[str, Any]:
    """处理用户请求"""
    router = get_model_router()
    return router.process_request(query)


def get_router_status() -> Dict[str, Any]:
    """获取路由器状态"""
    router = get_model_router()
    return router.get_router_status()
