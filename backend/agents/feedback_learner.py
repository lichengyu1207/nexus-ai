"""
反馈学习模块
记录执行结果并优化路由策略
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeedbackLearner:
    """反馈学习器"""
    
    def __init__(self, data_file: str = None):
        self.data_file = data_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "feedback_data.json"
        )
        self.feedback_data = self._load_feedback_data()
    
    def _load_feedback_data(self) -> List[Dict[str, Any]]:
        """加载反馈数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载反馈数据失败: {e}")
        
        # 返回空列表
        return []
    
    def _save_feedback_data(self):
        """保存反馈数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存反馈数据失败: {e}")
    
    def record_feedback(self, task_type: str, complexity: float, model_name: str, 
                       accuracy: float, cost: float, delay: float, 
                       user_feedback: Optional[str] = None):
        """记录反馈
        
        Args:
            task_type: 任务类型
            complexity: 复杂度
            model_name: 模型名称
            accuracy: 准确率
            cost: 成本
            delay: 延迟
            user_feedback: 用户反馈
        """
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "complexity": complexity,
            "model_name": model_name,
            "accuracy": accuracy,
            "cost": cost,
            "delay": delay,
            "user_feedback": user_feedback
        }
        
        self.feedback_data.append(feedback)
        self._save_feedback_data()
        logger.info(f"记录反馈: {model_name} - 准确率: {accuracy:.2f}, 成本: ¥{cost:.4f}, 延迟: {delay:.2f}s")
    
    def get_feedback_stats(self, model_name: str = None, task_type: str = None) -> Dict[str, Any]:
        """获取反馈统计信息
        
        Args:
            model_name: 模型名称（可选）
            task_type: 任务类型（可选）
            
        Returns:
            统计信息
        """
        filtered_data = self.feedback_data
        
        if model_name:
            filtered_data = [data for data in filtered_data if data["model_name"] == model_name]
        
        if task_type:
            filtered_data = [data for data in filtered_data if data["task_type"] == task_type]
        
        if not filtered_data:
            return {
                "count": 0,
                "avg_accuracy": 0.0,
                "avg_cost": 0.0,
                "avg_delay": 0.0
            }
        
        stats = {
            "count": len(filtered_data),
            "avg_accuracy": sum(data["accuracy"] for data in filtered_data) / len(filtered_data),
            "avg_cost": sum(data["cost"] for data in filtered_data) / len(filtered_data),
            "avg_delay": sum(data["delay"] for data in filtered_data) / len(filtered_data)
        }
        
        return stats
    
    def get_recent_feedback(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近的反馈
        
        Args:
            days: 天数
            
        Returns:
            最近的反馈数据
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_data = []
        
        for data in self.feedback_data:
            try:
                data_time = datetime.fromisoformat(data["timestamp"]).timestamp()
                if data_time >= cutoff_time:
                    recent_data.append(data)
            except Exception as e:
                logger.error(f"解析时间戳失败: {e}")
        
        return recent_data
    
    def clear_feedback(self):
        """清空反馈数据"""
        self.feedback_data = []
        self._save_feedback_data()
        logger.info("反馈数据已清空")
    
    def get_feedback_data(self) -> List[Dict[str, Any]]:
        """获取所有反馈数据
        
        Returns:
            反馈数据列表
        """
        return self.feedback_data


# 全局学习器实例
feedback_learner: Optional[FeedbackLearner] = None


def get_feedback_learner() -> FeedbackLearner:
    """获取反馈学习器实例"""
    global feedback_learner
    if feedback_learner is None:
        feedback_learner = FeedbackLearner()
    return feedback_learner


def record_feedback(task_type: str, complexity: float, model_name: str, 
                    accuracy: float, cost: float, delay: float, 
                    user_feedback: Optional[str] = None):
    """记录反馈"""
    learner = get_feedback_learner()
    learner.record_feedback(task_type, complexity, model_name, accuracy, cost, delay, user_feedback)


def get_feedback_stats(model_name: str = None, task_type: str = None) -> Dict[str, Any]:
    """获取反馈统计信息"""
    learner = get_feedback_learner()
    return learner.get_feedback_stats(model_name, task_type)


def get_recent_feedback(days: int = 7) -> List[Dict[str, Any]]:
    """获取最近的反馈"""
    learner = get_feedback_learner()
    return learner.get_recent_feedback(days)
