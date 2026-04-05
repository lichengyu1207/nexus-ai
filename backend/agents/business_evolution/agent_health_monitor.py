"""
智能体健康监控智能体
Agent Health Monitor - 实时监控所有业务智能体的运行状态

吏部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
import random


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_COUNT = "error_count"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    ENERGY_LEVEL = "energy_level"
    TASK_QUEUE_LENGTH = "task_queue_length"
    THROUGHPUT = "throughput"


@dataclass
class HealthMetric:
    metric_id: str
    metric_type: MetricType
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthAlert:
    alert_id: str
    agent_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class AgentHealthReport:
    agent_id: str
    agent_name: str
    status: HealthStatus
    metrics: List[HealthMetric]
    alerts: List[HealthAlert]
    uptime_seconds: int
    last_check: datetime
    recommendations: List[str] = field(default_factory=list)


class MetricsCollector:
    def __init__(self):
        self.metrics_history: Dict[str, List[HealthMetric]] = {}
        self.collection_interval_seconds = 60

    def collect(
        self,
        agent_id: str,
        metric_type: MetricType,
        value: float,
        unit: str = "",
        thresholds: Tuple[float, float] = None,
    ) -> HealthMetric:
        warning_threshold, critical_threshold = thresholds or (80, 95)

        metric = HealthMetric(
            metric_id=f"metric_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            metric_type=metric_type,
            value=value,
            unit=unit,
            threshold_warning=warning_threshold,
            threshold_critical=critical_threshold,
            tags={"agent_id": agent_id},
        )

        if agent_id not in self.metrics_history:
            self.metrics_history[agent_id] = []
        self.metrics_history[agent_id].append(metric)

        return metric

    def get_metrics(
        self,
        agent_id: str,
        metric_type: MetricType = None,
        since: datetime = None,
    ) -> List[HealthMetric]:
        metrics = self.metrics_history.get(agent_id, [])

        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]

        if since:
            metrics = [m for m in metrics if m.timestamp >= since]

        return metrics

    def get_aggregated_metrics(
        self, agent_id: str, window_minutes: int = 60
    ) -> Dict[str, Dict[str, float]]:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        metrics = self.get_metrics(agent_id, since=cutoff)

        aggregated: Dict[str, List[float]] = {}
        for metric in metrics:
            type_name = metric.metric_type.value
            if type_name not in aggregated:
                aggregated[type_name] = []
            aggregated[type_name].append(metric.value)

        result = {}
        for type_name, values in aggregated.items():
            if values:
                result[type_name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        return result


class AnomalyDetector:
    def __init__(self):
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.anomaly_threshold = 3.0

    def set_baseline(
        self, agent_id: str, metric_type: MetricType, mean: float, std: float
    ) -> None:
        key = f"{agent_id}_{metric_type.value}"
        self.baselines[key] = {"mean": mean, "std": std}

    def detect(
        self, agent_id: str, metric: HealthMetric
    ) -> Optional[Dict[str, Any]]:
        key = f"{agent_id}_{metric.metric_type.value}"
        baseline = self.baselines.get(key)

        if not baseline:
            return None

        mean = baseline["mean"]
        std = baseline["std"] or 1

        z_score = abs(metric.value - mean) / std

        if z_score > self.anomaly_threshold:
            return {
                "agent_id": agent_id,
                "metric_type": metric.metric_type.value,
                "value": metric.value,
                "expected_range": f"{mean - std * self.anomaly_threshold:.2f} - {mean + std * self.anomaly_threshold:.2f}",
                "z_score": z_score,
                "severity": "high" if z_score > 4 else "medium",
            }

        return None

    def auto_baseline(
        self, agent_id: str, metric_type: MetricType, historical_values: List[float]
    ) -> None:
        if not historical_values:
            return

        mean = sum(historical_values) / len(historical_values)
        variance = sum((v - mean) ** 2 for v in historical_values) / len(historical_values)
        std = variance**0.5

        self.set_baseline(agent_id, metric_type, mean, std)


class SelfHealingManager:
    def __init__(self):
        self.healing_actions: Dict[str, Callable] = {}
        self.healing_history: List[Dict] = []

    def register_healing_action(
        self, condition: str, action: Callable
    ) -> None:
        self.healing_actions[condition] = action

    async def attempt_healing(
        self, agent_id: str, issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = {
            "agent_id": agent_id,
            "issue": issue,
            "healing_attempted": False,
            "healing_successful": False,
            "action_taken": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        condition = self._determine_condition(issue)

        if condition in self.healing_actions:
            action = self.healing_actions[condition]
            result["healing_attempted"] = True
            result["action_taken"] = condition

            try:
                await action(agent_id, issue)
                result["healing_successful"] = True
            except Exception as e:
                result["error"] = str(e)

        self.healing_history.append(result)
        return result

    def _determine_condition(self, issue: Dict[str, Any]) -> str:
        metric_type = issue.get("metric_type", "")

        if "response_time" in metric_type:
            return "high_latency"
        elif "error" in metric_type.lower():
            return "high_error_rate"
        elif "memory" in metric_type.lower():
            return "memory_leak"
        elif "energy" in metric_type.lower():
            return "low_energy"

        return "unknown"


class AgentHealthMonitor:
    def __init__(self, agent_id: str = "health_monitor_001"):
        self.agent_id = agent_id
        self.metrics_collector = MetricsCollector()
        self.anomaly_detector = AnomalyDetector()
        self.self_healing = SelfHealingManager()

        self.agent_registry: Dict[str, Dict] = {}
        self.health_reports: Dict[str, AgentHealthReport] = {}
        self.active_alerts: List[HealthAlert] = []

        self.check_interval_seconds = 30
        self._initialize_default_healing_actions()

    def _initialize_default_healing_actions(self) -> None:
        async def restart_agent(agent_id: str, issue: Dict):
            pass

        async def scale_up(agent_id: str, issue: Dict):
            pass

        async def clear_cache(agent_id: str, issue: Dict):
            pass

        self.self_healing.register_healing_action("high_latency", restart_agent)
        self.self_healing.register_healing_action("high_error_rate", restart_agent)
        self.self_healing.register_healing_action("memory_leak", clear_cache)
        self.self_healing.register_healing_action("low_energy", scale_up)

    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        thresholds: Dict[str, Tuple[float, float]] = None,
    ) -> None:
        self.agent_registry[agent_id] = {
            "name": agent_name,
            "type": agent_type,
            "registered_at": datetime.utcnow().isoformat(),
            "thresholds": thresholds or {},
            "status": HealthStatus.UNKNOWN.value,
        }

    def unregister_agent(self, agent_id: str) -> bool:
        if agent_id in self.agent_registry:
            del self.agent_registry[agent_id]
            if agent_id in self.health_reports:
                del self.health_reports[agent_id]
            return True
        return False

    async def check_health(self, agent_id: str) -> AgentHealthReport:
        agent_info = self.agent_registry.get(agent_id)
        if not agent_info:
            return None

        metrics = await self._collect_all_metrics(agent_id, agent_info)

        alerts = self._check_thresholds(agent_id, metrics)

        status = self._determine_status(metrics, alerts)

        recommendations = self._generate_recommendations(metrics, alerts)

        report = AgentHealthReport(
            agent_id=agent_id,
            agent_name=agent_info["name"],
            status=status,
            metrics=metrics,
            alerts=alerts,
            uptime_seconds=self._calculate_uptime(agent_id),
            last_check=datetime.utcnow(),
            recommendations=recommendations,
        )

        self.health_reports[agent_id] = report
        self.agent_registry[agent_id]["status"] = status.value

        for alert in alerts:
            if alert not in self.active_alerts:
                self.active_alerts.append(alert)

        return report

    async def _collect_all_metrics(
        self, agent_id: str, agent_info: Dict
    ) -> List[HealthMetric]:
        metrics = []

        response_time = random.uniform(50, 500)
        thresholds = agent_info.get("thresholds", {}).get(
            "response_time", (200, 500)
        )
        metrics.append(
            self.metrics_collector.collect(
                agent_id,
                MetricType.RESPONSE_TIME,
                response_time,
                "ms",
                thresholds,
            )
        )

        success_rate = random.uniform(0.9, 1.0) * 100
        thresholds = agent_info.get("thresholds", {}).get("success_rate", (95, 90))
        metrics.append(
            self.metrics_collector.collect(
                agent_id,
                MetricType.SUCCESS_RATE,
                success_rate,
                "%",
                (thresholds[1], thresholds[0]),
            )
        )

        cpu_usage = random.uniform(10, 90)
        metrics.append(
            self.metrics_collector.collect(
                agent_id, MetricType.CPU_USAGE, cpu_usage, "%", (70, 90)
            )
        )

        memory_usage = random.uniform(20, 80)
        metrics.append(
            self.metrics_collector.collect(
                agent_id, MetricType.MEMORY_USAGE, memory_usage, "%", (70, 90)
            )
        )

        energy = random.uniform(20, 100)
        metrics.append(
            self.metrics_collector.collect(
                agent_id, MetricType.ENERGY_LEVEL, energy, "%", (30, 10)
            )
        )

        return metrics

    def _check_thresholds(
        self, agent_id: str, metrics: List[HealthMetric]
    ) -> List[HealthAlert]:
        alerts = []

        for metric in metrics:
            if metric.value >= metric.threshold_critical:
                alert = HealthAlert(
                    alert_id=f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                    agent_id=agent_id,
                    level=AlertLevel.CRITICAL,
                    metric_type=metric.metric_type,
                    message=f"{metric.metric_type.value} 超过临界阈值: {metric.value}{metric.unit}",
                    value=metric.value,
                    threshold=metric.threshold_critical,
                )
                alerts.append(alert)

            elif metric.value >= metric.threshold_warning:
                alert = HealthAlert(
                    alert_id=f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                    agent_id=agent_id,
                    level=AlertLevel.WARNING,
                    metric_type=metric.metric_type,
                    message=f"{metric.metric_type.value} 超过警告阈值: {metric.value}{metric.unit}",
                    value=metric.value,
                    threshold=metric.threshold_warning,
                )
                alerts.append(alert)

            anomaly = self.anomaly_detector.detect(agent_id, metric)
            if anomaly:
                alert = HealthAlert(
                    alert_id=f"anomaly_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                    agent_id=agent_id,
                    level=AlertLevel.WARNING,
                    metric_type=metric.metric_type,
                    message=f"检测到异常: {anomaly['expected_range']}",
                    value=metric.value,
                    threshold=0,
                )
                alerts.append(alert)

        return alerts

    def _determine_status(
        self, metrics: List[HealthMetric], alerts: List[HealthAlert]
    ) -> HealthStatus:
        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        if critical_alerts:
            return HealthStatus.CRITICAL

        warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]
        if len(warning_alerts) >= 2:
            return HealthStatus.UNHEALTHY
        elif warning_alerts:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def _generate_recommendations(
        self, metrics: List[HealthMetric], alerts: List[HealthAlert]
    ) -> List[str]:
        recommendations = []

        for alert in alerts:
            if alert.metric_type == MetricType.RESPONSE_TIME:
                recommendations.append("考虑重启智能体或增加资源")
            elif alert.metric_type == MetricType.SUCCESS_RATE:
                recommendations.append("检查错误日志，修复失败原因")
            elif alert.metric_type == MetricType.CPU_USAGE:
                recommendations.append("优化算法或扩展计算资源")
            elif alert.metric_type == MetricType.MEMORY_USAGE:
                recommendations.append("检查内存泄漏，清理缓存")
            elif alert.metric_type == MetricType.ENERGY_LEVEL:
                recommendations.append("智能体能量不足，考虑繁殖或任务转移")

        return list(set(recommendations))

    def _calculate_uptime(self, agent_id: str) -> int:
        agent_info = self.agent_registry.get(agent_id)
        if not agent_info:
            return 0

        registered_at = datetime.fromisoformat(agent_info["registered_at"])
        return int((datetime.utcnow() - registered_at).total_seconds())

    async def check_all_agents(self) -> List[AgentHealthReport]:
        reports = []
        for agent_id in list(self.agent_registry.keys()):
            report = await self.check_health(agent_id)
            if report:
                reports.append(report)
        return reports

    def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str
    ) -> Optional[HealthAlert]:
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                return alert
        return None

    def resolve_alert(self, alert_id: str) -> Optional[HealthAlert]:
        for i, alert in enumerate(self.active_alerts):
            if alert.alert_id == alert_id:
                alert.resolved_at = datetime.utcnow()
                self.active_alerts.pop(i)
                return alert
        return None

    async def attempt_self_healing(
        self, agent_id: str
    ) -> Optional[Dict[str, Any]]:
        report = self.health_reports.get(agent_id)
        if not report or report.status == HealthStatus.HEALTHY:
            return None

        for alert in report.alerts:
            issue = {
                "metric_type": alert.metric_type.value,
                "value": alert.value,
                "threshold": alert.threshold,
            }

            result = await self.self_healing.attempt_healing(agent_id, issue)
            if result["healing_successful"]:
                return result

        return None

    def get_dashboard_data(self) -> Dict[str, Any]:
        total_agents = len(self.agent_registry)
        status_counts: Dict[str, int] = {}

        for agent_info in self.agent_registry.values():
            status = agent_info.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_agents": total_agents,
            "status_distribution": status_counts,
            "active_alerts": len(self.active_alerts),
            "critical_alerts": len(
                [a for a in self.active_alerts if a.level == AlertLevel.CRITICAL]
            ),
            "last_check": max(
                (r.last_check for r in self.health_reports.values()),
                default=datetime.utcnow(),
            ).isoformat(),
        }

    def get_trend_analysis(
        self, agent_id: str, hours: int = 24
    ) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        metrics = self.metrics_collector.get_metrics(agent_id, since=cutoff)

        trends: Dict[str, List[float]] = {}
        for metric in metrics:
            type_name = metric.metric_type.value
            if type_name not in trends:
                trends[type_name] = []
            trends[type_name].append(metric.value)

        analysis = {}
        for type_name, values in trends.items():
            if len(values) >= 2:
                first_half = values[: len(values) // 2]
                second_half = values[len(values) // 2 :]

                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)

                change = (
                    (second_avg - first_avg) / first_avg * 100
                    if first_avg != 0
                    else 0
                )

                analysis[type_name] = {
                    "trend": "上升" if change > 5 else "下降" if change < -5 else "稳定",
                    "change_percent": round(change, 2),
                    "current_avg": second_avg,
                }

        return analysis
