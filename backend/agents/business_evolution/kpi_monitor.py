"""
业务KPI自监控智能体
Business KPI Monitor - 实时评估自身表现

自我评价模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import random


class KPIType(Enum):
    SUCCESS_RATE = "success_rate"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    TASK_THROUGHPUT = "task_throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_UTILIZATION = "resource_utilization"
    CONVERSION_RATE = "conversion_rate"
    RETENTION_RATE = "retention_rate"


class KPITrend(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class KPITarget:
    kpi_type: KPIType
    target_value: float
    min_acceptable: float
    max_acceptable: float
    unit: str
    higher_is_better: bool = True


@dataclass
class KPIMetric:
    metric_id: str
    kpi_type: KPIType
    value: float
    target: float
    deviation: float
    status: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class KPIAlert:
    alert_id: str
    kpi_type: KPIType
    severity: AlertSeverity
    message: str
    current_value: float
    target_value: float
    deviation_percent: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class KPIReport:
    report_id: str
    agent_id: str
    period_start: datetime
    period_end: datetime
    metrics: List[KPIMetric]
    alerts: List[KPIAlert]
    overall_score: float
    trends: Dict[str, KPITrend]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class MetricsAggregator:
    def __init__(self):
        self.raw_metrics: Dict[str, List[Dict]] = {}
        self.aggregation_window_minutes = 5

    def record(
        self,
        metric_name: str,
        value: float,
        tags: Dict[str, str] = None,
    ) -> None:
        if metric_name not in self.raw_metrics:
            self.raw_metrics[metric_name] = []

        self.raw_metrics[metric_name].append(
            {
                "value": value,
                "tags": tags or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def aggregate(
        self,
        metric_name: str,
        window_minutes: int = None,
        aggregation_type: str = "avg",
    ) -> Optional[float]:
        window = window_minutes or self.aggregation_window_minutes
        cutoff = datetime.utcnow() - timedelta(minutes=window)

        metrics = self.raw_metrics.get(metric_name, [])
        recent = [
            m
            for m in metrics
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]

        if not recent:
            return None

        values = [m["value"] for m in recent]

        if aggregation_type == "avg":
            return sum(values) / len(values)
        elif aggregation_type == "sum":
            return sum(values)
        elif aggregation_type == "max":
            return max(values)
        elif aggregation_type == "min":
            return min(values)
        elif aggregation_type == "count":
            return len(values)
        else:
            return sum(values) / len(values)

    def get_percentile(
        self, metric_name: str, percentile: int, window_minutes: int = None
    ) -> Optional[float]:
        window = window_minutes or self.aggregation_window_minutes
        cutoff = datetime.utcnow() - timedelta(minutes=window)

        metrics = self.raw_metrics.get(metric_name, [])
        recent = [
            m
            for m in metrics
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]

        if not recent:
            return None

        values = sorted([m["value"] for m in recent])
        index = int(len(values) * percentile / 100)

        return values[min(index, len(values) - 1)]


class TrendAnalyzer:
    def __init__(self):
        self.history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.trend_window_points = 10

    def record(self, kpi_type: KPIType, value: float) -> None:
        key = kpi_type.value
        if key not in self.history:
            self.history[key] = []

        self.history[key].append((datetime.utcnow(), value))

        if len(self.history[key]) > 100:
            self.history[key] = self.history[key][-100:]

    def analyze_trend(self, kpi_type: KPIType) -> KPITrend:
        key = kpi_type.value
        history = self.history.get(key, [])

        if len(history) < self.trend_window_points:
            return KPITrend.STABLE

        recent = history[-self.trend_window_points :]
        values = [v for _, v in recent]

        if len(values) < 3:
            return KPITrend.STABLE

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if first_avg == 0:
            return KPITrend.STABLE

        change = (second_avg - first_avg) / first_avg

        variance = sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)
        cv = (variance**0.5) / (sum(values) / len(values)) if sum(values) > 0 else 0

        if cv > 0.3:
            return KPITrend.VOLATILE
        elif change > 0.1:
            return KPITrend.IMPROVING
        elif change < -0.1:
            return KPITrend.DECLINING
        else:
            return KPITrend.STABLE

    def predict_next(self, kpi_type: KPIType) -> Optional[float]:
        key = kpi_type.value
        history = self.history.get(key, [])

        if len(history) < 3:
            return None

        values = [v for _, v in history[-5:]]

        if len(values) < 3:
            return None

        weights = [i + 1 for i in range(len(values))]
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight


class DeviationAnalyzer:
    def __init__(self):
        self.baselines: Dict[str, Dict[str, float]] = {}

    def set_baseline(
        self, kpi_type: KPIType, mean: float, std: float
    ) -> None:
        self.baselines[kpi_type.value] = {"mean": mean, "std": std}

    def analyze_deviation(
        self, kpi_type: KPIType, value: float
    ) -> Dict[str, Any]:
        baseline = self.baselines.get(kpi_type.value)

        if not baseline:
            return {
                "deviation": 0,
                "z_score": 0,
                "status": "unknown",
                "within_normal": True,
            }

        mean = baseline["mean"]
        std = baseline["std"] or 1

        deviation = value - mean
        z_score = deviation / std

        if abs(z_score) < 1:
            status = "normal"
        elif abs(z_score) < 2:
            status = "elevated"
        elif abs(z_score) < 3:
            status = "high"
        else:
            status = "critical"

        return {
            "deviation": deviation,
            "z_score": z_score,
            "status": status,
            "within_normal": abs(z_score) < 2,
        }

    def analyze_root_cause(
        self, kpi_type: KPIType, deviation: float, context: Dict[str, Any]
    ) -> List[str]:
        causes = []

        if kpi_type == KPIType.SUCCESS_RATE:
            if deviation < -0.1:
                causes.append("检查最近部署的变更")
                causes.append("分析错误日志定位失败原因")
                causes.append("检查依赖服务状态")

        elif kpi_type == KPIType.RESPONSE_TIME:
            if deviation > 0.5:
                causes.append("检查服务器负载")
                causes.append("分析慢查询日志")
                causes.append("检查网络延迟")

        elif kpi_type == KPIType.USER_SATISFACTION:
            if deviation < -0.1:
                causes.append("分析用户反馈和投诉")
                causes.append("检查最近功能变更")
                causes.append("评估服务质量变化")

        return causes


class BusinessKPIMonitor:
    def __init__(self, agent_id: str = "kpi_monitor_001"):
        self.agent_id = agent_id
        self.metrics_aggregator = MetricsAggregator()
        self.trend_analyzer = TrendAnalyzer()
        self.deviation_analyzer = DeviationAnalyzer()

        self.kpi_targets: Dict[KPIType, KPITarget] = {}
        self.current_metrics: Dict[KPIType, KPIMetric] = {}
        self.active_alerts: List[KPIAlert] = []
        self.reports: List[KPIReport] = []

        self._initialize_default_targets()

    def _initialize_default_targets(self) -> None:
        default_targets = [
            (KPIType.SUCCESS_RATE, 0.95, 0.90, 1.0, "%", True),
            (KPIType.RESPONSE_TIME, 200, 100, 500, "ms", False),
            (KPIType.USER_SATISFACTION, 4.5, 3.5, 5.0, "score", True),
            (KPIType.TASK_THROUGHPUT, 100, 50, 200, "tasks/hour", True),
            (KPIType.ERROR_RATE, 0.05, 0, 0.1, "%", False),
        ]

        for kpi_type, target, min_val, max_val, unit, higher_better in default_targets:
            self.kpi_targets[kpi_type] = KPITarget(
                kpi_type=kpi_type,
                target_value=target,
                min_acceptable=min_val,
                max_acceptable=max_val,
                unit=unit,
                higher_is_better=higher_better,
            )

    def record_metric(
        self,
        kpi_type: KPIType,
        value: float,
        tags: Dict[str, str] = None,
    ) -> KPIMetric:
        self.metrics_aggregator.record(kpi_type.value, value, tags)

        self.trend_analyzer.record(kpi_type, value)

        target = self.kpi_targets.get(kpi_type)
        if not target:
            target = KPITarget(
                kpi_type=kpi_type,
                target_value=0,
                min_acceptable=0,
                max_acceptable=100,
                unit="",
            )

        if target.higher_is_better:
            deviation = (value - target.target_value) / target.target_value if target.target_value else 0
        else:
            deviation = (target.target_value - value) / target.target_value if target.target_value else 0

        if target.min_acceptable <= value <= target.max_acceptable:
            status = "healthy"
        elif deviation > -0.1:
            status = "warning"
        else:
            status = "critical"

        metric = KPIMetric(
            metric_id=f"metric_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            kpi_type=kpi_type,
            value=value,
            target=target.target_value,
            deviation=deviation,
            status=status,
            tags=tags or {},
        )

        self.current_metrics[kpi_type] = metric

        self._check_and_alert(kpi_type, value, target)

        return metric

    def _check_and_alert(
        self, kpi_type: KPIType, value: float, target: KPITarget
    ) -> Optional[KPIAlert]:
        if target.higher_is_better:
            if value < target.min_acceptable:
                severity = AlertSeverity.CRITICAL
            elif value < target.target_value * 0.9:
                severity = AlertSeverity.WARNING
            else:
                return None
        else:
            if value > target.max_acceptable:
                severity = AlertSeverity.CRITICAL
            elif value > target.target_value * 1.1:
                severity = AlertSeverity.WARNING
            else:
                return None

        deviation_percent = abs(value - target.target_value) / target.target_value * 100

        alert = KPIAlert(
            alert_id=f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            kpi_type=kpi_type,
            severity=severity,
            message=f"{kpi_type.value} {severity.value}: 当前值 {value}{target.unit}, 目标 {target.target_value}{target.unit}",
            current_value=value,
            target_value=target.target_value,
            deviation_percent=deviation_percent,
        )

        self.active_alerts.append(alert)

        return alert

    def get_current_status(self) -> Dict[str, Any]:
        status = {}

        for kpi_type, metric in self.current_metrics.items():
            trend = self.trend_analyzer.analyze_trend(kpi_type)
            prediction = self.trend_analyzer.predict_next(kpi_type)

            status[kpi_type.value] = {
                "value": metric.value,
                "target": metric.target,
                "deviation": metric.deviation,
                "status": metric.status,
                "trend": trend.value,
                "prediction": prediction,
            }

        return status

    def generate_report(
        self,
        period_hours: int = 24,
        agent_id: str = None,
    ) -> KPIReport:
        period_start = datetime.utcnow() - timedelta(hours=period_hours)
        period_end = datetime.utcnow()

        metrics = list(self.current_metrics.values())

        trends = {}
        for kpi_type in self.kpi_targets.keys():
            trends[kpi_type.value] = self.trend_analyzer.analyze_trend(kpi_type)

        if metrics:
            overall_score = sum(
                m.value / m.target if m.target > 0 else 1
                for m in metrics
            ) / len(metrics) * 100
        else:
            overall_score = 0

        recommendations = self._generate_recommendations(metrics, trends)

        report = KPIReport(
            report_id=f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            agent_id=agent_id or self.agent_id,
            period_start=period_start,
            period_end=period_end,
            metrics=metrics,
            alerts=[a for a in self.active_alerts if a.triggered_at >= period_start],
            overall_score=round(overall_score, 2),
            trends=trends,
            recommendations=recommendations,
        )

        self.reports.append(report)

        return report

    def _generate_recommendations(
        self, metrics: List[KPIMetric], trends: Dict[str, KPITrend]
    ) -> List[str]:
        recommendations = []

        for metric in metrics:
            if metric.status == "critical":
                if metric.kpi_type == KPIType.SUCCESS_RATE:
                    recommendations.append("紧急检查系统错误，优先修复失败原因")
                elif metric.kpi_type == KPIType.RESPONSE_TIME:
                    recommendations.append("优化性能瓶颈，考虑扩容或缓存优化")
                elif metric.kpi_type == KPIType.USER_SATISFACTION:
                    recommendations.append("分析用户反馈，改进服务质量")

            elif metric.status == "warning":
                trend = trends.get(metric.kpi_type.value, KPITrend.STABLE)
                if trend == KPITrend.DECLINING:
                    recommendations.append(f"{metric.kpi_type.value} 指标下降趋势，建议关注")

        for kpi_type, trend in trends.items():
            if trend == KPITrend.VOLATILE:
                recommendations.append(f"{kpi_type} 波动较大，建议分析原因")

        return list(set(recommendations))

    def acknowledge_alert(self, alert_id: str) -> bool:
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        for i, alert in enumerate(self.active_alerts):
            if alert.alert_id == alert_id:
                alert.resolved_at = datetime.utcnow()
                self.active_alerts.pop(i)
                return True
        return False

    def set_target(
        self,
        kpi_type: KPIType,
        target_value: float,
        min_acceptable: float,
        max_acceptable: float,
        unit: str = "",
        higher_is_better: bool = True,
    ) -> None:
        self.kpi_targets[kpi_type] = KPITarget(
            kpi_type=kpi_type,
            target_value=target_value,
            min_acceptable=min_acceptable,
            max_acceptable=max_acceptable,
            unit=unit,
            higher_is_better=higher_is_better,
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        return {
            "current_status": self.get_current_status(),
            "active_alerts": len(self.active_alerts),
            "critical_alerts": len(
                [a for a in self.active_alerts if a.severity == AlertSeverity.CRITICAL]
            ),
            "overall_health": self._calculate_overall_health(),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _calculate_overall_health(self) -> str:
        if not self.current_metrics:
            return "unknown"

        critical_count = sum(
            1 for m in self.current_metrics.values() if m.status == "critical"
        )
        warning_count = sum(
            1 for m in self.current_metrics.values() if m.status == "warning"
        )

        if critical_count > 0:
            return "critical"
        elif warning_count > 1:
            return "degraded"
        elif warning_count > 0:
            return "warning"
        else:
            return "healthy"

    def compare_with_baseline(self) -> Dict[str, Any]:
        comparison = {}

        for kpi_type, metric in self.current_metrics.items():
            deviation = self.deviation_analyzer.analyze_deviation(
                kpi_type, metric.value
            )
            comparison[kpi_type.value] = deviation

        return comparison
