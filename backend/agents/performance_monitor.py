"""
性能评估模块
Performance Monitor Module

计算智能体的成功率、平均奖励、用户满意度等指标
并可视化展示在管理员后台
"""

import json
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MetricType(Enum):
    """指标类型"""
    SUCCESS_RATE = "success_rate"
    AVG_REWARD = "avg_reward"
    USER_SATISFACTION = "user_satisfaction"
    AVG_RESPONSE_TIME = "avg_response_time"
    TASK_THROUGHPUT = "task_throughput"
    ERROR_RATE = "error_rate"
    LEARNING_PROGRESS = "learning_progress"
    COLLABORATION_SCORE = "collaboration_score"


class TimeGranularity(Enum):
    """时间粒度"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float
    count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "count": self.count,
            "metadata": self.metadata
        }


@dataclass
class AgentMetrics:
    """智能体指标集合"""
    agent_id: str
    period_start: float
    period_end: float
    
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    total_reward: float = 0.0
    avg_reward: float = 0.0
    
    positive_feedback: int = 0
    negative_feedback: int = 0
    neutral_feedback: int = 0
    
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    
    errors: List[str] = field(default_factory=list)
    
    def calculate_derived_metrics(self):
        """计算派生指标"""
        self.success_rate = self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0.0
        self.avg_reward = self.total_reward / self.total_tasks if self.total_tasks > 0 else 0.0
        self.avg_response_time = self.total_response_time / self.total_tasks if self.total_tasks > 0 else 0.0
        
        total_feedback = self.positive_feedback + self.negative_feedback + self.neutral_feedback
        self.satisfaction_rate = self.positive_feedback / total_feedback if total_feedback > 0 else 0.0
        
        self.error_rate = len(self.errors) / self.total_tasks if self.total_tasks > 0 else 0.0
    
    def to_dict(self) -> Dict:
        self.calculate_derived_metrics()
        return {
            "agent_id": self.agent_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "total_reward": self.total_reward,
            "avg_reward": self.avg_reward,
            "positive_feedback": self.positive_feedback,
            "negative_feedback": self.negative_feedback,
            "satisfaction_rate": self.satisfaction_rate,
            "avg_response_time": self.avg_response_time,
            "error_rate": self.error_rate,
            "error_count": len(self.errors)
        }


class PerformanceRecord(Base):
    """性能记录数据库模型"""
    __tablename__ = "performance_records"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(50), index=True)
    
    metric_type = Column(String(30), index=True)
    metric_value = Column(Float)
    sample_count = Column(Integer, default=1)
    
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime)
    granularity = Column(String(20))
    
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MetricsCollector:
    """指标采集器"""
    
    def __init__(self):
        self._metrics_buffer: Dict[str, List[MetricPoint]] = {}
        self._task_records: Dict[str, List[Dict]] = {}
        
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
    
    def record_task_start(
        self,
        agent_id: str,
        task_id: str,
        task_type: str
    ):
        """记录任务开始"""
        key = f"{agent_id}_{task_id}"
        
        self._task_records[key] = [{
            "agent_id": agent_id,
            "task_id": task_id,
            "task_type": task_type,
            "start_time": time.time()
        }]
        
        self._increment_counter(f"{agent_id}:tasks_started")
    
    def record_task_end(
        self,
        agent_id: str,
        task_id: str,
        success: bool,
        reward: float = 0.0,
        user_feedback: Optional[str] = None
    ):
        """记录任务结束"""
        key = f"{agent_id}_{task_id}"
        
        if key not in self._task_records:
            return
        
        record = self._task_records[key][0]
        record["end_time"] = time.time()
        record["duration"] = record["end_time"] - record["start_time"]
        record["success"] = success
        record["reward"] = reward
        record["user_feedback"] = user_feedback
        
        self._add_metric(agent_id, MetricType.AVG_RESPONSE_TIME, record["duration"])
        self._add_metric(agent_id, MetricType.AVG_REWARD, reward)
        
        if success:
            self._increment_counter(f"{agent_id}:tasks_successful")
        else:
            self._increment_counter(f"{agent_id}:tasks_failed")
        
        if user_feedback == "like":
            self._increment_counter(f"{agent_id}:positive_feedback")
        elif user_feedback == "dislike":
            self._increment_counter(f"{agent_id}:negative_feedback")
    
    def record_error(
        self,
        agent_id: str,
        error_type: str,
        error_message: str
    ):
        """记录错误"""
        self._increment_counter(f"{agent_id}:errors")
        self._increment_counter(f"{agent_id}:error:{error_type}")
        
        self._add_metric(agent_id, MetricType.ERROR_RATE, 1.0, {
            "error_type": error_type,
            "error_message": error_message[:200]
        })
    
    def record_learning_progress(
        self,
        agent_id: str,
        episode: int,
        avg_reward: float,
        policy_loss: float
    ):
        """记录学习进度"""
        self._add_metric(agent_id, MetricType.LEARNING_PROGRESS, avg_reward, {
            "episode": episode,
            "policy_loss": policy_loss
        })
    
    def record_collaboration(
        self,
        agent_id: str,
        partner_id: str,
        task_success: bool,
        communication_count: int
    ):
        """记录协作"""
        self._add_metric(agent_id, MetricType.COLLABORATION_SCORE, 1.0 if task_success else 0.0, {
            "partner_id": partner_id,
            "communication_count": communication_count
        })
    
    def _add_metric(
        self,
        agent_id: str,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """添加指标"""
        key = f"{agent_id}:{metric_type.value}"
        
        if key not in self._metrics_buffer:
            self._metrics_buffer[key] = []
        
        self._metrics_buffer[key].append(MetricPoint(
            timestamp=time.time(),
            value=value,
            metadata=metadata or {}
        ))
    
    def _increment_counter(self, key: str):
        """增加计数器"""
        self._counters[key] = self._counters.get(key, 0) + 1
    
    def get_metrics(
        self,
        agent_id: str,
        metric_type: MetricType,
        since: Optional[float] = None
    ) -> List[MetricPoint]:
        """获取指标"""
        key = f"{agent_id}:{metric_type.value}"
        metrics = self._metrics_buffer.get(key, [])
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    def get_counter(self, key: str) -> int:
        """获取计数器值"""
        return self._counters.get(key, 0)
    
    def clear_old_metrics(self, max_age: float = 86400):
        """清理旧指标"""
        cutoff = time.time() - max_age
        
        for key in self._metrics_buffer:
            self._metrics_buffer[key] = [
                m for m in self._metrics_buffer[key]
                if m.timestamp >= cutoff
            ]
        
        old_task_keys = [
            k for k, v in self._task_records.items()
            if v and v[0].get("end_time", 0) < cutoff
        ]
        for k in old_task_keys:
            del self._task_records[k]


class MetricsAggregator:
    """指标聚合器"""
    
    def __init__(self):
        self._aggregated: Dict[str, AgentMetrics] = {}
    
    def aggregate(
        self,
        agent_id: str,
        records: List[Dict],
        period_start: float,
        period_end: float
    ) -> AgentMetrics:
        """聚合指标"""
        metrics = AgentMetrics(
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end
        )
        
        for record in records:
            metrics.total_tasks += 1
            
            if record.get("success"):
                metrics.successful_tasks += 1
            else:
                metrics.failed_tasks += 1
            
            metrics.total_reward += record.get("reward", 0.0)
            
            feedback = record.get("user_feedback")
            if feedback == "like":
                metrics.positive_feedback += 1
            elif feedback == "dislike":
                metrics.negative_feedback += 1
            else:
                metrics.neutral_feedback += 1
            
            metrics.total_response_time += record.get("duration", 0.0)
            
            if record.get("error"):
                metrics.errors.append(record.get("error"))
        
        metrics.calculate_derived_metrics()
        
        key = f"{agent_id}:{period_start}:{period_end}"
        self._aggregated[key] = metrics
        
        return metrics
    
    def aggregate_by_granularity(
        self,
        agent_id: str,
        records: List[Dict],
        granularity: TimeGranularity
    ) -> List[AgentMetrics]:
        """按时间粒度聚合"""
        if not records:
            return []
        
        grouped: Dict[str, List[Dict]] = {}
        
        for record in records:
            timestamp = record.get("end_time", record.get("start_time", time.time()))
            dt = datetime.fromtimestamp(timestamp)
            
            if granularity == TimeGranularity.MINUTE:
                period_key = dt.strftime("%Y%m%d%H%M")
            elif granularity == TimeGranularity.HOUR:
                period_key = dt.strftime("%Y%m%d%H")
            elif granularity == TimeGranularity.DAY:
                period_key = dt.strftime("%Y%m%d")
            elif granularity == TimeGranularity.WEEK:
                period_key = dt.strftime("%Y%W")
            else:
                period_key = dt.strftime("%Y%m")
            
            if period_key not in grouped:
                grouped[period_key] = []
            grouped[period_key].append(record)
        
        results = []
        for period_key, period_records in sorted(grouped.items()):
            timestamps = [
                r.get("end_time", r.get("start_time", time.time()))
                for r in period_records
            ]
            
            metrics = self.aggregate(
                agent_id=agent_id,
                records=period_records,
                period_start=min(timestamps),
                period_end=max(timestamps)
            )
            results.append(metrics)
        
        return results


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self.aggregator = MetricsAggregator()
    
    def analyze_agent_performance(
        self,
        agent_id: str,
        time_range: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """分析智能体性能"""
        since = time.time() - time_range.total_seconds()
        
        response_times = self.collector.get_metrics(
            agent_id, MetricType.AVG_RESPONSE_TIME, since
        )
        rewards = self.collector.get_metrics(
            agent_id, MetricType.AVG_REWARD, since
        )
        learning_progress = self.collector.get_metrics(
            agent_id, MetricType.LEARNING_PROGRESS, since
        )
        
        successful = self.collector.get_counter(f"{agent_id}:tasks_successful")
        failed = self.collector.get_counter(f"{agent_id}:tasks_failed")
        total = successful + failed
        
        positive = self.collector.get_counter(f"{agent_id}:positive_feedback")
        negative = self.collector.get_counter(f"{agent_id}:negative_feedback")
        
        analysis = {
            "agent_id": agent_id,
            "time_range_hours": time_range.total_seconds() / 3600,
            "task_metrics": {
                "total": total,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / total if total > 0 else 0.0
            },
            "response_time_metrics": {
                "avg": np.mean([m.value for m in response_times]) if response_times else 0.0,
                "min": min([m.value for m in response_times]) if response_times else 0.0,
                "max": max([m.value for m in response_times]) if response_times else 0.0,
                "p95": np.percentile([m.value for m in response_times], 95) if len(response_times) > 1 else 0.0
            },
            "reward_metrics": {
                "avg": np.mean([m.value for m in rewards]) if rewards else 0.0,
                "total": sum([m.value for m in rewards]) if rewards else 0.0,
                "trend": self._calculate_trend([m.value for m in rewards])
            },
            "satisfaction_metrics": {
                "positive": positive,
                "negative": negative,
                "satisfaction_rate": positive / (positive + negative) if (positive + negative) > 0 else 0.0
            },
            "learning_metrics": {
                "episodes": len(learning_progress),
                "latest_avg_reward": learning_progress[-1].value if learning_progress else 0.0,
                "progress_trend": self._calculate_trend([m.value for m in learning_progress])
            }
        }
        
        analysis["health_score"] = self._calculate_health_score(analysis)
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "insufficient_data"
        
        n = len(values)
        x = np.arange(n)
        
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _calculate_health_score(self, analysis: Dict) -> float:
        """计算健康分数"""
        weights = {
            "success_rate": 0.3,
            "satisfaction": 0.25,
            "response_time": 0.15,
            "reward_trend": 0.15,
            "learning_progress": 0.15
        }
        
        success_score = analysis["task_metrics"]["success_rate"]
        satisfaction_score = analysis["satisfaction_metrics"]["satisfaction_rate"]
        
        avg_response = analysis["response_time_metrics"]["avg"]
        response_score = max(0, 1 - avg_response / 30)
        
        reward_trend = analysis["reward_metrics"]["trend"]
        trend_scores = {"improving": 1.0, "stable": 0.7, "declining": 0.3, "insufficient_data": 0.5}
        reward_score = trend_scores.get(reward_trend, 0.5)
        
        learning_trend = analysis["learning_metrics"]["progress_trend"]
        learning_score = trend_scores.get(learning_trend, 0.5)
        
        health_score = (
            weights["success_rate"] * success_score +
            weights["satisfaction"] * satisfaction_score +
            weights["response_time"] * response_score +
            weights["reward_trend"] * reward_score +
            weights["learning_progress"] * learning_score
        )
        
        return round(health_score * 100, 1)
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if analysis["task_metrics"]["success_rate"] < 0.8:
            recommendations.append("成功率低于80%，建议检查错误日志并优化策略")
        
        if analysis["satisfaction_metrics"]["satisfaction_rate"] < 0.7:
            recommendations.append("用户满意度较低，建议分析负面反馈并改进响应质量")
        
        if analysis["response_time_metrics"]["avg"] > 10:
            recommendations.append("响应时间较长，建议优化处理流程或使用异步方式")
        
        if analysis["reward_metrics"]["trend"] == "declining":
            recommendations.append("奖励趋势下降，建议重新训练模型或调整策略")
        
        if analysis["learning_metrics"]["episodes"] < 10:
            recommendations.append("学习样本不足，建议增加训练频率")
        
        if not recommendations:
            recommendations.append("性能良好，继续保持当前策略")
        
        return recommendations
    
    def compare_agents(
        self,
        agent_ids: List[str],
        time_range: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """比较多个智能体"""
        comparisons = {}
        
        for agent_id in agent_ids:
            comparisons[agent_id] = self.analyze_agent_performance(agent_id, time_range)
        
        metrics_comparison = {
            "success_rate": {},
            "avg_response_time": {},
            "satisfaction_rate": {},
            "health_score": {}
        }
        
        for agent_id, data in comparisons.items():
            metrics_comparison["success_rate"][agent_id] = data["task_metrics"]["success_rate"]
            metrics_comparison["avg_response_time"][agent_id] = data["response_time_metrics"]["avg"]
            metrics_comparison["satisfaction_rate"][agent_id] = data["satisfaction_metrics"]["satisfaction_rate"]
            metrics_comparison["health_score"][agent_id] = data["health_score"]
        
        rankings = {
            "by_health_score": sorted(
                agent_ids,
                key=lambda x: comparisons[x]["health_score"],
                reverse=True
            ),
            "by_success_rate": sorted(
                agent_ids,
                key=lambda x: comparisons[x]["task_metrics"]["success_rate"],
                reverse=True
            )
        }
        
        return {
            "individual": comparisons,
            "comparison": metrics_comparison,
            "rankings": rankings
        }
    
    def detect_anomalies(
        self,
        agent_id: str,
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        since = time.time() - 3600
        response_times = self.collector.get_metrics(
            agent_id, MetricType.AVG_RESPONSE_TIME, since
        )
        
        if len(response_times) > 10:
            values = [m.value for m in response_times]
            mean = np.mean(values)
            std = np.std(values)
            
            for point in response_times:
                if abs(point.value - mean) > sensitivity * std:
                    anomalies.append({
                        "type": "response_time_anomaly",
                        "timestamp": point.timestamp,
                        "value": point.value,
                        "expected_range": [mean - sensitivity * std, mean + sensitivity * std],
                        "severity": "high" if point.value > mean + sensitivity * std else "medium"
                    })
        
        error_count = self.collector.get_counter(f"{agent_id}:errors")
        if error_count > 5:
            anomalies.append({
                "type": "high_error_rate",
                "count": error_count,
                "severity": "high",
                "recommendation": "检查错误日志并修复根本原因"
            })
        
        return anomalies


class PerformanceMonitor:
    """性能监控主类"""
    
    def __init__(self):
        self.analyzer = PerformanceAnalyzer()
        self._alert_handlers: List[callable] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start_monitoring(self, interval: int = 60):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop(interval))
        
        print("[PerformanceMonitor] 监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        print("[PerformanceMonitor] 监控已停止")
    
    async def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._running:
            try:
                await self._check_alerts()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[PerformanceMonitor] 监控错误: {e}")
                await asyncio.sleep(interval)
    
    async def _check_alerts(self):
        """检查告警"""
        pass
    
    def add_alert_handler(self, handler: callable):
        """添加告警处理器"""
        self._alert_handlers.append(handler)
    
    def record_task(
        self,
        agent_id: str,
        task_id: str,
        task_type: str,
        success: bool,
        duration: float,
        reward: float = 0.0,
        user_feedback: Optional[str] = None,
        error: Optional[str] = None
    ):
        """记录任务执行"""
        self.analyzer.collector.record_task_start(agent_id, task_id, task_type)
        
        self.analyzer.collector.record_task_end(
            agent_id, task_id, success, reward, user_feedback
        )
        
        if error:
            self.analyzer.collector.record_error(agent_id, "task_error", error)
    
    def get_dashboard_data(
        self,
        agent_ids: List[str],
        time_range: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """获取仪表盘数据"""
        dashboard = {
            "generated_at": time.time(),
            "time_range_hours": time_range.total_seconds() / 3600,
            "agents": {}
        }
        
        for agent_id in agent_ids:
            analysis = self.analyzer.analyze_agent_performance(agent_id, time_range)
            anomalies = self.analyzer.detect_anomalies(agent_id)
            
            dashboard["agents"][agent_id] = {
                "health_score": analysis["health_score"],
                "success_rate": analysis["task_metrics"]["success_rate"],
                "avg_response_time": analysis["response_time_metrics"]["avg"],
                "satisfaction_rate": analysis["satisfaction_metrics"]["satisfaction_rate"],
                "recommendations": analysis["recommendations"],
                "anomalies": anomalies
            }
        
        if agent_ids:
            comparison = self.analyzer.compare_agents(agent_ids, time_range)
            dashboard["comparison"] = comparison["comparison"]
            dashboard["rankings"] = comparison["rankings"]
        
        return dashboard
    
    def get_time_series(
        self,
        agent_id: str,
        metric_type: MetricType,
        granularity: TimeGranularity = TimeGranularity.HOUR,
        time_range: timedelta = timedelta(hours=24)
    ) -> List[Dict[str, Any]]:
        """获取时间序列数据"""
        since = time.time() - time_range.total_seconds()
        metrics = self.analyzer.collector.get_metrics(agent_id, metric_type, since)
        
        if not metrics:
            return []
        
        grouped: Dict[str, List[MetricPoint]] = {}
        
        for m in metrics:
            dt = datetime.fromtimestamp(m.timestamp)
            
            if granularity == TimeGranularity.MINUTE:
                key = dt.strftime("%Y%m%d%H%M")
            elif granularity == TimeGranularity.HOUR:
                key = dt.strftime("%Y%m%d%H")
            elif granularity == TimeGranularity.DAY:
                key = dt.strftime("%Y%m%d")
            else:
                key = dt.strftime("%Y%m%d")
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(m)
        
        series = []
        for key, points in sorted(grouped.items()):
            values = [p.value for p in points]
            series.append({
                "period": key,
                "avg": np.mean(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            })
        
        return series
    
    def export_report(
        self,
        agent_ids: List[str],
        time_range: timedelta = timedelta(hours=24),
        format: str = "json"
    ) -> str:
        """导出报告"""
        dashboard = self.get_dashboard_data(agent_ids, time_range)
        
        if format == "json":
            return json.dumps(dashboard, indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._generate_markdown_report(dashboard)
        else:
            return json.dumps(dashboard, ensure_ascii=False)
    
    def _generate_markdown_report(self, dashboard: Dict) -> str:
        """生成Markdown报告"""
        lines = [
            "# 智能体性能报告",
            f"\n生成时间: {datetime.fromtimestamp(dashboard['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n统计周期: {dashboard['time_range_hours']:.1f} 小时",
            "\n---\n"
        ]
        
        for agent_id, data in dashboard["agents"].items():
            lines.extend([
                f"\n## {agent_id}",
                f"\n| 指标 | 值 |",
                f"|------|------|",
                f"| 健康分数 | {data['health_score']:.1f} |",
                f"| 成功率 | {data['success_rate']:.1%} |",
                f"| 平均响应时间 | {data['avg_response_time']:.2f}s |",
                f"| 用户满意度 | {data['satisfaction_rate']:.1%} |"
            ])
            
            if data["recommendations"]:
                lines.append("\n### 建议\n")
                for rec in data["recommendations"]:
                    lines.append(f"- {rec}")
            
            if data["anomalies"]:
                lines.append("\n### 异常\n")
                for anomaly in data["anomalies"]:
                    lines.append(f"- **{anomaly['type']}**: {anomaly}")
        
        return "\n".join(lines)


performance_monitor = PerformanceMonitor()
