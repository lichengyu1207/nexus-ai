"""
性能优化模块
根据实际运行数据调整模型性能-成本映射表
"""

import os
import json
import logging
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.agents.model_manager import get_model_manager, ModelPerformance
from backend.agents.feedback_learner import get_feedback_learner

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.model_manager = get_model_manager()
        self.feedback_learner = get_feedback_learner()
    
    def optimize_performance(self, days: int = 7):
        """优化模型性能
        
        Args:
            days: 考虑最近多少天的数据
            
        Returns:
            优化结果
        """
        logger.info(f"开始优化模型性能，考虑最近 {days} 天的数据")
        
        # 获取最近的反馈数据
        recent_feedback = self.feedback_learner.get_recent_feedback(days)
        if not recent_feedback:
            logger.warning("没有足够的反馈数据进行优化")
            return {
                "success": False,
                "message": "没有足够的反馈数据"
            }
        
        # 按模型和任务类型分组
        model_task_data = self._group_feedback_by_model_task(recent_feedback)
        
        # 更新每个模型的性能数据
        updated_models = []
        for (model_name, task_type), data in model_task_data.items():
            if self._update_model_performance(model_name, task_type, data):
                updated_models.append(f"{model_name}-{task_type}")
        
        logger.info(f"性能优化完成，更新了 {len(updated_models)} 个模型-任务组合")
        return {
            "success": True,
            "updated": updated_models
        }
    
    def _group_feedback_by_model_task(self, feedback_data: List[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
        """按模型和任务类型分组反馈数据
        
        Args:
            feedback_data: 反馈数据
            
        Returns:
            分组后的数据
        """
        grouped = {}
        for data in feedback_data:
            key = (data["model_name"], data["task_type"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(data)
        return grouped
    
    def _update_model_performance(self, model_name: str, task_type: str, data: List[Dict[str, Any]]):
        """更新模型性能
        
        Args:
            model_name: 模型名称
            task_type: 任务类型
            data: 反馈数据
            
        Returns:
            是否更新成功
        """
        try:
            # 计算统计数据
            accuracies = [d["accuracy"] for d in data]
            costs = [d["cost"] for d in data]
            delays = [d["delay"] for d in data]
            
            avg_accuracy = statistics.mean(accuracies)
            avg_cost = statistics.mean(costs)
            avg_delay = statistics.mean(delays)
            
            # 获取当前性能数据
            current_perf = self.model_manager.get_model_performance(model_name, task_type)
            if not current_perf:
                logger.warning(f"模型 {model_name} 在任务类型 {task_type} 上没有性能数据")
                return False
            
            # 更新性能数据
            current_perf.accuracy = avg_accuracy
            current_perf.avg_time = avg_delay
            current_perf.cost = avg_cost
            current_perf.usage_count += len(data)
            current_perf.last_updated = datetime.now().timestamp()
            
            # 保存更新后的性能数据
            self._save_performance_mapping()
            
            logger.info(f"更新模型 {model_name} 在任务类型 {task_type} 上的性能:")
            logger.info(f"  准确率: {avg_accuracy:.2f}")
            logger.info(f"  平均耗时: {avg_delay:.2f}s")
            logger.info(f"  平均成本: ¥{avg_cost:.4f}")
            logger.info(f"  使用次数: {current_perf.usage_count}")
            
            return True
        except Exception as e:
            logger.error(f"更新模型性能失败: {e}")
            return False
    
    def _save_performance_mapping(self):
        """保存性能映射表"""
        try:
            performance_mapping = self.model_manager.get_performance_mapping()
            
            # 转换为可序列化格式
            serializable_mapping = {}
            for model_name, task_performance in performance_mapping.items():
                serializable_mapping[model_name] = {}
                for task_type, perf in task_performance.items():
                    serializable_mapping[model_name][task_type] = {
                        "accuracy": perf.accuracy,
                        "avg_time": perf.avg_time,
                        "cost": perf.cost,
                        "usage_count": perf.usage_count,
                        "last_updated": perf.last_updated
                    }
            
            # 保存到文件
            mapping_file = os.path.join(
                os.path.dirname(__file__), "..", "data", "model_performance_mapping.json"
            )
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(serializable_mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存性能映射表失败: {e}")
    
    def get_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """获取性能报告
        
        Args:
            days: 考虑最近多少天的数据
            
        Returns:
            性能报告
        """
        # 获取最近的反馈数据
        recent_feedback = self.feedback_learner.get_recent_feedback(days)
        if not recent_feedback:
            return {
                "success": False,
                "message": "没有足够的反馈数据"
            }
        
        # 按模型分组
        model_data = {}
        for data in recent_feedback:
            model_name = data["model_name"]
            if model_name not in model_data:
                model_data[model_name] = []
            model_data[model_name].append(data)
        
        # 生成报告
        report = {}
        for model_name, data in model_data.items():
            accuracies = [d["accuracy"] for d in data]
            costs = [d["cost"] for d in data]
            delays = [d["delay"] for d in data]
            
            report[model_name] = {
                "total_usage": len(data),
                "avg_accuracy": statistics.mean(accuracies),
                "avg_cost": statistics.mean(costs),
                "avg_delay": statistics.mean(delays),
                "total_cost": sum(costs),
                "min_cost": min(costs),
                "max_cost": max(costs)
            }
        
        # 计算总体统计
        all_accuracies = [d["accuracy"] for d in recent_feedback]
        all_costs = [d["cost"] for d in recent_feedback]
        all_delays = [d["delay"] for d in recent_feedback]
        
        overall = {
            "total_requests": len(recent_feedback),
            "avg_accuracy": statistics.mean(all_accuracies),
            "avg_cost": statistics.mean(all_costs),
            "avg_delay": statistics.mean(all_delays),
            "total_cost": sum(all_costs)
        }
        
        return {
            "success": True,
            "overall": overall,
            "models": report
        }
    
    def get_task_performance(self, task_type: str, days: int = 30) -> Dict[str, Any]:
        """获取特定任务类型的性能
        
        Args:
            task_type: 任务类型
            days: 考虑最近多少天的数据
            
        Returns:
            任务性能
        """
        # 获取最近的反馈数据
        recent_feedback = self.feedback_learner.get_recent_feedback(days)
        # 过滤特定任务类型
        task_feedback = [d for d in recent_feedback if d["task_type"] == task_type]
        
        if not task_feedback:
            return {
                "success": False,
                "message": f"没有任务类型 {task_type} 的反馈数据"
            }
        
        # 按模型分组
        model_data = {}
        for data in task_feedback:
            model_name = data["model_name"]
            if model_name not in model_data:
                model_data[model_name] = []
            model_data[model_name].append(data)
        
        # 生成报告
        report = {}
        for model_name, data in model_data.items():
            accuracies = [d["accuracy"] for d in data]
            costs = [d["cost"] for d in data]
            delays = [d["delay"] for d in data]
            
            report[model_name] = {
                "total_usage": len(data),
                "avg_accuracy": statistics.mean(accuracies),
                "avg_cost": statistics.mean(costs),
                "avg_delay": statistics.mean(delays),
                "total_cost": sum(costs)
            }
        
        return {
            "success": True,
            "task_type": task_type,
            "models": report
        }


# 全局优化器实例
performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取性能优化器实例"""
    global performance_optimizer
    if performance_optimizer is None:
        performance_optimizer = PerformanceOptimizer()
    return performance_optimizer


def optimize_performance(days: int = 7) -> Dict[str, Any]:
    """优化模型性能"""
    optimizer = get_performance_optimizer()
    return optimizer.optimize_performance(days)


def get_performance_report(days: int = 30) -> Dict[str, Any]:
    """获取性能报告"""
    optimizer = get_performance_optimizer()
    return optimizer.get_performance_report(days)


def get_task_performance(task_type: str, days: int = 30) -> Dict[str, Any]:
    """获取特定任务类型的性能"""
    optimizer = get_performance_optimizer()
    return optimizer.get_task_performance(task_type, days)
