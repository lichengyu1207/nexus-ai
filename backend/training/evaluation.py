"""
训练评估和监控系统
Training Evaluation and Monitoring System

提供训练过程的评估、监控和可视化
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """评估指标"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    latency: float = 0.0
    success_rate: float = 0.0
    user_satisfaction: float = 0.0
    cost_efficiency: float = 0.0


@dataclass
class TrainingProgress:
    """训练进度"""
    epoch: int = 0
    total_epochs: int = 0
    current_loss: float = 0.0
    best_loss: float = float('inf')
    learning_rate: float = 0.0
    samples_processed: int = 0
    total_samples: int = 0
    start_time: float = field(default_factory=time.time)
    estimated_completion: Optional[float] = None


class TrainingEvaluator:
    """
    训练评估器
    
    功能：
    1. 离线评估
    2. 在线评估
    3. 性能监控
    4. 用户反馈闭环
    """
    
    def __init__(self, log_dir: str = "./logs/training"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.evaluation_history: List[Dict] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.alerts: List[Dict] = []
        
        self.baseline_metrics: Dict[str, float] = {
            "zhongshu_accuracy": 0.92,
            "menshang_accuracy": 0.95,
            "gongbu_error_rate": 0.05,
            "libu_satisfaction": 4.5,
            "collaboration_latency": 50.0,
        }
        
        self.target_metrics: Dict[str, float] = {
            "zhongshu_accuracy": 0.96,
            "menshang_accuracy": 0.98,
            "gongbu_error_rate": 0.03,
            "libu_satisfaction": 4.7,
            "collaboration_latency": 30.0,
        }
        
        self.thresholds: Dict[str, Dict[str, float]] = {
            "latency_warning": {"threshold": 5.0, "severity": "warning"},
            "latency_critical": {"threshold": 10.0, "severity": "critical"},
            "error_rate_warning": {"threshold": 0.05, "severity": "warning"},
            "error_rate_critical": {"threshold": 0.1, "severity": "critical"},
            "memory_usage_warning": {"threshold": 0.8, "severity": "warning"},
            "memory_usage_critical": {"threshold": 0.9, "severity": "critical"},
        }
        
        logger.info("TrainingEvaluator initialized")
    
    def evaluate_agent(
        self,
        agent_type: str,
        predictions: List[Any],
        ground_truth: List[Any],
        metadata: Optional[Dict] = None
    ) -> EvaluationMetrics:
        """评估单个智能体"""
        if len(predictions) != len(ground_truth):
            logger.warning(f"Prediction and ground truth length mismatch: {len(predictions)} vs {len(ground_truth)}")
        
        correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        total = len(ground_truth)
        accuracy = correct / total if total > 0 else 0.0
        
        true_positives = sum(
            1 for p, g in zip(predictions, ground_truth)
            if p == g and p == 1
        )
        false_positives = sum(
            1 for p, g in zip(predictions, ground_truth)
            if p != g and p == 1
        )
        false_negatives = sum(
            1 for p, g in zip(predictions, ground_truth)
            if p != g and g == 1
        )
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics = EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
        )
        
        self._record_evaluation(agent_type, metrics, metadata)
        
        logger.info(f"Evaluated {agent_type}: accuracy={accuracy:.4f}, f1={f1_score:.4f}")
        return metrics
    
    def evaluate_collaboration(
        self,
        task_results: List[Dict],
        execution_times: List[float],
        communication_delays: List[float]
    ) -> Dict:
        """评估协同效果"""
        if not task_results:
            return {"error": "No task results"}
        
        success_count = sum(1 for r in task_results if r.get("success", False))
        success_rate = success_count / len(task_results)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        avg_comm_delay = sum(communication_delays) / len(communication_delays) if communication_delays else 0.0
        
        agent_contributions = defaultdict(lambda: {"success": 0, "total": 0})
        for result in task_results:
            for agent, agent_result in result.get("agent_results", {}).items():
                agent_contributions[agent]["total"] += 1
                if agent_result.get("success", False):
                    agent_contributions[agent]["success"] += 1
        
        agent_success_rates = {}
        for agent, stats in agent_contributions.items():
            agent_success_rates[agent] = stats["success"] / stats["total"] if stats["total"] > 0 else 0.0
        
        collaboration_score = success_rate * 0.5
        if avg_execution_time < 10:
            collaboration_score += 0.3
        if avg_comm_delay < 0.03:
            collaboration_score += 0.2
        
        result = {
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "avg_communication_delay": avg_comm_delay,
            "agent_success_rates": agent_success_rates,
            "collaboration_score": collaboration_score,
            "total_tasks": len(task_results),
        }
        
        self._record_evaluation("collaboration", result)
        
        logger.info(f"Collaboration evaluation: success_rate={success_rate:.2%}, score={collaboration_score:.2f}")
        return result
    
    def monitor_performance(
        self,
        agent_type: str,
        metrics: Dict[str, float]
    ) -> Dict:
        """监控性能"""
        timestamp = time.time()
        
        for metric_name, value in metrics.items():
            key = f"{agent_type}_{metric_name}"
            self.performance_metrics[key].append(value)
            
            if len(self.performance_metrics[key]) > 1000:
                self.performance_metrics[key] = self.performance_metrics[key][-1000:]
        
        alerts = self._check_thresholds(agent_type, metrics)
        
        result = {
            "agent_type": agent_type,
            "timestamp": timestamp,
            "metrics": metrics,
            "alerts": alerts,
        }
        
        return result
    
    def _check_thresholds(self, agent_type: str, metrics: Dict[str, float]) -> List[Dict]:
        """检查阈值"""
        alerts = []
        
        if "latency" in metrics:
            latency = metrics["latency"]
            if latency > self.thresholds["latency_critical"]["threshold"]:
                alert = {
                    "agent_type": agent_type,
                    "metric": "latency",
                    "value": latency,
                    "threshold": self.thresholds["latency_critical"]["threshold"],
                    "severity": "critical",
                    "message": f"Latency {latency:.2f}s exceeds critical threshold",
                    "timestamp": time.time(),
                }
                alerts.append(alert)
                self.alerts.append(alert)
            elif latency > self.thresholds["latency_warning"]["threshold"]:
                alert = {
                    "agent_type": agent_type,
                    "metric": "latency",
                    "value": latency,
                    "threshold": self.thresholds["latency_warning"]["threshold"],
                    "severity": "warning",
                    "message": f"Latency {latency:.2f}s exceeds warning threshold",
                    "timestamp": time.time(),
                }
                alerts.append(alert)
                self.alerts.append(alert)
        
        if "error_rate" in metrics:
            error_rate = metrics["error_rate"]
            if error_rate > self.thresholds["error_rate_critical"]["threshold"]:
                alert = {
                    "agent_type": agent_type,
                    "metric": "error_rate",
                    "value": error_rate,
                    "threshold": self.thresholds["error_rate_critical"]["threshold"],
                    "severity": "critical",
                    "message": f"Error rate {error_rate:.2%} exceeds critical threshold",
                    "timestamp": time.time(),
                }
                alerts.append(alert)
                self.alerts.append(alert)
        
        return alerts
    
    def _record_evaluation(self, eval_type: str, result: Any, metadata: Optional[Dict] = None):
        """记录评估结果"""
        record = {
            "type": eval_type,
            "result": result.__dict__ if hasattr(result, '__dict__') else result,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        
        self.evaluation_history.append(record)
        
        if len(self.evaluation_history) > 10000:
            self.evaluation_history = self.evaluation_history[-10000:]
    
    def compare_with_baseline(self, agent_type: str, current_metrics: Dict) -> Dict:
        """与基线对比"""
        baseline_key = f"{agent_type}_accuracy"
        baseline = self.baseline_metrics.get(baseline_key, 0.0)
        target = self.target_metrics.get(baseline_key, 0.0)
        
        current = current_metrics.get("accuracy", 0.0)
        
        improvement = current - baseline
        progress_to_target = (current - baseline) / (target - baseline) if target != baseline else 0.0
        
        result = {
            "agent_type": agent_type,
            "baseline": baseline,
            "current": current,
            "target": target,
            "improvement": improvement,
            "progress_to_target": min(1.0, max(0.0, progress_to_target)),
            "status": "on_track" if progress_to_target >= 0.5 else "needs_improvement",
        }
        
        return result
    
    def generate_report(self, period: str = "daily") -> Dict:
        """生成报告"""
        now = time.time()
        
        if period == "daily":
            start_time = now - 24 * 3600
        elif period == "weekly":
            start_time = now - 7 * 24 * 3600
        else:
            start_time = 0
        
        period_evaluations = [
            e for e in self.evaluation_history
            if e["timestamp"] >= start_time
        ]
        
        agent_evaluations = defaultdict(list)
        for e in period_evaluations:
            if e["type"] != "collaboration":
                agent_evaluations[e["type"]].append(e)
        
        agent_summaries = {}
        for agent_type, evals in agent_evaluations.items():
            if evals:
                accuracies = [
                    e["result"].get("accuracy", 0)
                    for e in evals
                    if isinstance(e["result"], dict)
                ]
                avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
                
                agent_summaries[agent_type] = {
                    "total_evaluations": len(evals),
                    "avg_accuracy": avg_accuracy,
                }
        
        period_alerts = [
            a for a in self.alerts
            if a["timestamp"] >= start_time
        ]
        
        alert_counts = defaultdict(int)
        for alert in period_alerts:
            key = f"{alert['agent_type']}_{alert['metric']}"
            alert_counts[key] += 1
        
        report = {
            "period": period,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(now).isoformat(),
            "total_evaluations": len(period_evaluations),
            "agent_summaries": agent_summaries,
            "total_alerts": len(period_alerts),
            "alert_breakdown": dict(alert_counts),
            "recommendations": self._generate_recommendations(agent_summaries, period_alerts),
        }
        
        logger.info(f"Generated {period} report with {len(period_evaluations)} evaluations")
        return report
    
    def _generate_recommendations(
        self,
        agent_summaries: Dict,
        alerts: List[Dict]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for agent_type, summary in agent_summaries.items():
            baseline_key = f"{agent_type}_accuracy"
            baseline = self.baseline_metrics.get(baseline_key, 0.0)
            target = self.target_metrics.get(baseline_key, 0.0)
            current = summary.get("avg_accuracy", 0.0)
            
            if current < baseline:
                recommendations.append(
                    f"{agent_type}: 性能低于基线，建议检查数据质量或调整训练参数"
                )
            elif current < target:
                progress = (current - baseline) / (target - baseline) if target != baseline else 0
                if progress < 0.5:
                    recommendations.append(
                        f"{agent_type}: 距离目标还有差距，建议增加训练数据或优化模型"
                    )
        
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        if critical_alerts:
            alert_types = set(a["metric"] for a in critical_alerts)
            for alert_type in alert_types:
                recommendations.append(
                    f"发现{alert_type}严重告警，建议立即排查"
                )
        
        if not recommendations:
            recommendations.append("系统运行良好，继续保持当前训练策略")
        
        return recommendations
    
    def get_performance_trend(self, agent_type: str, metric: str = "accuracy") -> Dict:
        """获取性能趋势"""
        key = f"{agent_type}_{metric}"
        values = self.performance_metrics.get(key, [])
        
        if not values:
            return {"error": "No data available"}
        
        if len(values) >= 10:
            recent = values[-10:]
            trend = "improving" if recent[-1] > recent[0] else "declining"
            avg_recent = sum(recent) / len(recent)
        else:
            trend = "insufficient_data"
            avg_recent = sum(values) / len(values)
        
        return {
            "agent_type": agent_type,
            "metric": metric,
            "current_value": values[-1] if values else 0,
            "average": avg_recent,
            "trend": trend,
            "data_points": len(values),
        }
    
    def export_metrics(self, filepath: str):
        """导出指标"""
        data = {
            "evaluation_history": self.evaluation_history[-1000:],
            "performance_metrics": dict(self.performance_metrics),
            "alerts": self.alerts[-100:],
            "baseline_metrics": self.baseline_metrics,
            "target_metrics": self.target_metrics,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported metrics to {filepath}")


_global_evaluator: Optional[TrainingEvaluator] = None


def get_evaluator() -> TrainingEvaluator:
    """获取全局评估器实例"""
    global _global_evaluator
    if _global_evaluator is None:
        _global_evaluator = TrainingEvaluator()
    return _global_evaluator
