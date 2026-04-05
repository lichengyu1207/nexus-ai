# -*- coding: utf-8 -*-
"""
驱动智能体 - 感知层 (Driver Perception Layer)
=============================================
对应设计文档 Ch4(自我验证与评估) + Ch6(闭环进化与监控)

职责：
1) 全局状态感知(GlobalStatePerceiver) — 汇聚4大体系+集成层的实时运行状态
2) 多源数据融合(MultiSourceFusion) — 合并来自不同子系统的指标数据，消除冲突
3) 异常检测器(AnomalyDetector) — 基于统计方法检测系统异常（漂移、突变、周期性异常）
4) 趋势分析器(TrendAnalyzer) — 分析关键指标的时间序列趋势，预测未来走向
5) 健康评分引擎(HealthScoringEngine) — 综合多维度指标生成统一健康分数
"""

from __future__ import annotations

import json
import time
import math
import logging
import threading
import statistics
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class AnomalySeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthGrade(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class SystemSnapshot:
    timestamp: str
    governance_status: Dict[str, Any] = field(default_factory=dict)
    evolution_status: Dict[str, Any] = field(default_factory=dict)
    alchemy_status: Dict[str, Any] = field(default_factory=dict)
    cultivation_status: Dict[str, Any] = field(default_factory=dict)
    integration_status: Dict[str, Any] = field(default_factory=dict)
    resource_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class FusedMetric:
    name: str
    value: float
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    last_updated: str = ""
    trend: str = "stable"
    anomaly_score: float = 0.0


@dataclass
class AnomalyEvent:
    event_id: str
    severity: AnomalySeverity
    metric_name: str
    detected_at: str
    current_value: float
    expected_range: Tuple[float, float]
    description: str
    source_systems: List[str] = field(default_factory=list)
    resolved: bool = False
    suggested_action: str = ""


@dataclass
class HealthReport:
    report_id: str
    timestamp: str
    overall_grade: HealthGrade
    overall_score: float
    subsystem_scores: Dict[str, float]
    key_findings: List[str]
    anomalies: List[AnomalyEvent]
    recommendations: List[str]
    next_check_suggested: float


class GlobalStatePerceiver:
    """
    全局状态感知器 — 对应提示词 6.1 进化过程可视化
    
    定期从所有子系统采集状态快照，形成全局一致的状态视图。
    """

    SNAPSHOT_INTERVAL_S = 30.0
    MAX_SNAPSHOTS = 500

    def __init__(self):
        self._snapshots: List[SystemSnapshot] = []
        self._lock = threading.RLock()
        self._last_snapshot_time: float = 0

    def capture(self, force: bool = False) -> SystemSnapshot:
        now = time.time()
        if not force and (now - self._last_snapshot_time) < self.SNAPSHOT_INTERVAL_S:
            return self._snapshots[-1] if self._snapshots else self._do_capture()
        snapshot = self._do_capture()
        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self.MAX_SNAPSHOTS:
                self._snapshots = self._snapshots[-self.MAX_SNAPSHOTS // 2:]
            self._last_snapshot_time = now
        return snapshot

    def _do_capture(self) -> SystemSnapshot:
        snap = SystemSnapshot(timestamp=datetime.now().isoformat())
        try:
            from backend.integration.platform_orchestrator import platform_orchestrator
            status_dict = platform_orchestrator.get_system_status_dict()
            snap.governance_status = {"platform_state": status_dict.get("platform_state", "unknown"),
                                         "subsystems": len(status_dict.get("subsystems", {}))}
        except Exception as e:
            snap.governance_status = {"error": str(e)[:100]}
        try:
            from backend.cultivation.cultivation_integration import cultivation_dashboard
            overview = cultivation_dashboard.get_system_overview()
            snap.cultivation_status = {
                "overall_completion": overview.overall_completion_pct,
                "completed_stages": overview.completed_stages,
                "total_stages": overview.total_stages,
                "avg_win_rate": round(overview.avg_win_rate_across_stages, 4),
                "health": overview.system_health,
                "dao_achievement": overview.dao_achievement_pct,
                "active_alerts": overview.active_alerts_count,
            }
        except Exception as e:
            snap.cultivation_status = {"error": str(e)[:100]}
        try:
            from backend.integration.cultivation_alchemy_bridge import cultivation_alchemy_bridge
            bridge_status = cultivation_alchemy_bridge.get_integration_status()
            snap.alchemy_status = bridge_status
        except Exception as e:
            snap.alchemy_status = {"error": str(e)[:100]}
        try:
            from backend.integration.evolution_cultivation_bridge import evolution_cultivation_bridge
            evol_status = evolution_cultivation_bridge.get_bridge_status()
            snap.evolution_status = evol_status
        except Exception as e:
            snap.evolution_status = {"error": str(e)[:100]}
        try:
            import psutil
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            snap.resource_metrics = {
                "cpu_percent": cpu,
                "memory_percent": mem.percent,
                "memory_used_mb": mem.used / (1024 * 1024),
                "memory_available_mb": mem.available / (1024 * 1024),
                "disk_percent": psutil.disk_usage(".").percent,
            }
        except Exception:
            snap.resource_metrics = {}
        return snap

    def get_latest(self) -> Optional[SystemSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def get_history(self, count: int = 10) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self._snapshots[-count:]]

    def get_delta(self, since_seconds: float = 300.0) -> Dict[str, Any]:
        cutoff = datetime.now() - timedelta(seconds=since_seconds)
        recent = [s for s in self._snapshots if datetime.fromisoformat(s.timestamp.replace("Z", "+00:00").replace("+00:00", "")) > cutoff - timedelta(hours=8)]
        if len(recent) < 2:
            return {"message": "insufficient_data", "snapshots": len(recent)}
        first = recent[0]
        latest = recent[-1]
        delta = {
            "time_span_s": (datetime.fromisoformat(latest.timestamp) - datetime.fromisoformat(first.timestamp)).total_seconds(),
            "cultivation_completion_delta": (
                latest.cultivation_status.get("overall_completion", 0) -
                first.cultivation_status.get("overall_completion", 0)
            ),
            "alerts_delta": (
                latest.cultivation_status.get("active_alerts", 0) -
                first.cultivation_status.get("active_alerts", 0)
            ),
            "cpu_delta": latest.resource_metrics.get("cpu_percent", 0) - first.resource_metrics.get("cpu_percent", 0),
            "memory_delta_pct": latest.resource_metrics.get("memory_percent", 0) - first.resource_metrics.get("memory_percent", 0),
        }
        return delta


global_state_perceiver = GlobalStatePerceiver()


class MultiSourceFusion:
    """
    多源数据融合器 — 对应提示词 4.1 多维度结果验证
    
    当多个子系统报告同一指标时，进行融合处理：
    - 加权平均（按来源可信度）
    - 冲突检测（超出阈值差异时标记）
    - 缺失值插值（基于历史趋势）
    """

    def __init__(self):
        self._metric_sources: Dict[str, List[Tuple[float, str, float]]] = defaultdict(list)
        self._source_reliability: Dict[str, float] = {
            "governance": 0.9, "evolution": 0.85, "alchemy": 0.88,
            "cultivation": 0.92, "integration": 0.95, "direct": 1.0,
        }

    def ingest(self, metric_name: str, value: float, source: str, reliability_override: Optional[float] = None):
        rel = reliability_override or self._source_reliability.get(source, 0.7)
        self._metric_sources[metric_name].append((value, source, rel))

    def fuse(self, metric_name: str, method: str = "weighted_average") -> FusedMetric:
        entries = self._metric_sources.get(metric_name, [])
        if not entries:
            return FusedMetric(name=metric_name, value=0.0, confidence=0.0, sources=[],
                              last_updated=datetime.now().isoformat())
        if method == "weighted_average":
            total_weight = sum(e[2] for e in entries)
            fused_val = sum(e[0] * e[2] for e in entries) / max(total_weight, 0.001)
            variance = statistics.stdev([e[0] for e in entries]) if len(entries) >= 2 else 0.0
            confidence = max(0.1, 1.0 - min(variance / max(abs(fused_val), 0.001), 5.0))
        elif method == "median":
            values_sorted = sorted(e[0] for e in entries)
            mid = len(values_sorted) // 2
            fused_val = (values_sorted[mid] + values_sorted[~mid]) / 2 if len(values_sorted) % 2 == 0 else values_sorted[mid]
            confidence = 0.9
        elif method == "max_confidence":
            best_entry = max(entries, key=lambda e: e[2])
            fused_val = best_entry[0]
            confidence = best_entry[2]
        else:
            fused_val = statistics.mean(e[0] for e in entries)
            confidence = 0.7
        sources_info = [{"value": e[0], "source": e[1], "reliability": round(e[2], 3)} for e in entries[-10:]]
        trend = self._compute_trend_from_entries(entries)
        return FusedMetric(
            name=metric_name,
            value=round(fused_val, 4),
            sources=sources_info,
            confidence=round(confidence, 3),
            last_updated=datetime.now().isoformat(),
            trend=trend,
        )

    def _compute_trend_from_entries(self, entries: List[Tuple]) -> str:
        if len(entries) < 3:
            return "stable"
        recent = [e[0] for e in entries[-5:]]
        if len(recent) < 3:
            return "stable"
        first_half_avg = statistics.mean(recent[:len(recent)//2])
        second_half_avg = statistics.mean(recent[len(recent)//2:])
        change_pct = (second_half_avg - first_half_avg) / max(abs(first_half_avg), 0.001)
        if change_pct > 0.05:
            return "rising"
        elif change_pct < -0.05:
            return "falling"
        return "stable"

    def detect_conflicts(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        conflicts = []
        for metric_name, entries in self._metric_sources.items():
            if len(entries) < 2:
                continue
            values = [e[0] for e in entries]
            val_range = max(values) - min(values)
            mean_val = abs(statistics.mean(values))
            normalized_range = val_range / max(mean_val, 0.001)
            if normalized_range > threshold:
                conflicts.append({
                    "metric": metric_name,
                    "range": round(val_range, 4),
                    "normalized_range": round(normalized_range, 3),
                    "sources": [(e[1], round(e[0], 4)) for e in entries],
                    "severity": "high" if normalized_range > 0.5 else "medium",
                })
        return conflicts

    def clear_old_entries(self, max_age_hours: float = 24.0):
        cutoff = time.time() - max_age_hours * 3600
        for metric_name in list(self._metric_sources.keys()):
            original_count = len(self._metric_sources[metric_name])
            self._metric_sources[metric_name] = [
                e for e in self._metric_sources[metric_name]
                if True
            ]
            while len(self._metric_sources[metric_name]) > original_count // 2:
                self._metric_sources[metric_name].pop(0)


multi_source_fusion = MultiSourceFusion()


class AnomalyDetector:
    """
    异常检测器 — 对应提示词 6.2 异常根因分析 + 提示词 7.1 混沌工程测试
    
    使用统计方法检测：
    - 突变检测（Z-score超过阈值）
    - 趋势漂移检测（均值/方差偏移）
    - 周期性异常（偏离正常周期模式）
    """

    Z_SCORE_THRESHOLD = 2.5
    DRIFT_WINDOW_SIZE = 20
    DRIFT_THRESHOLD = 0.15

    def __init__(self):
        self._event_history: List[AnomalyEvent] = []
        self._baseline_stats: Dict[str, Dict[str, float]] = {}

    def set_baseline(self, metric_name: str, mean: float, std: float, min_val: float = 0.0, max_val: float = 1.0):
        self._baseline_stats[metric_name] = {"mean": mean, "std": max(std, 0.001), "min": min_val, "max": max_val}

    def check_metric(self, metric_name: str, value: float, source_systems: Optional[List[str]] = None) -> Optional[AnomalyEvent]:
        baseline = self._baseline_stats.get(metric_name)
        if not baseline:
            return None
        z_score = abs(value - baseline["mean"]) / baseline["std"]
        if z_score < self.Z_SCORE_THRESHOLD:
            return None
        if value > baseline["mean"]:
            severity = AnomalySeverity.CRITICAL if z_score > 4.0 else AnomalySeverity.WARNING
        else:
            severity = AnomalySeverity.CRITICAL if z_score > 3.5 else AnomalySeverity.WARNING
        expected_lo = max(baseline["mean"] - 2 * baseline["std"], baseline["min"])
        expected_hi = min(baseline["mean"] + 2 * baseline["std"], baseline["max"])
        action_hints = {
            "cpu_percent": "检查是否有高负载进程或死循环",
            "memory_percent": "排查内存泄漏或增加缓存清理频率",
            "error_rate": "查看错误日志并触发修复流程",
            "response_time_ms": "检查下游服务延迟或网络状况",
            "win_rate": "审查训练数据和模型参数",
        }.get(metric_name, "建议人工介入分析")
        event = AnomalyEvent(
            event_id=f"anom_{int(time.time()*1000)}_{hash(metric_name) % 10000}",
            severity=severity,
            metric_name=metric_name,
            detected_at=datetime.now().isoformat(),
            current_value=value,
            expected_range=(round(expected_lo, 4), round(expected_hi, 4)),
            description=f"{metric_name}={value:.4f}, Z-Score={z_score:.2f}, 预期范围[{expected_lo:.2f}, {expected_hi:.2f}]",
            source_systems=source_systems or [],
            suggested_action=action_hints,
        )
        self._event_history.append(event)
        logger.warning(f"[驱动感知] ⚠ 异常检测: {event.description}")
        return event

    def check_drift(self, metric_name: str, recent_values: List[float]) -> Optional[AnomalyEvent]:
        if len(recent_values) < self.DRIFT_WINDOW_SIZE:
            return None
        baseline = self._baseline_stats.get(metric_name)
        if not baseline:
            self.set_baseline(metric_name, statistics.mean(recent_values), statistics.stdev(recent_values) or 0.01,
                               min(recent_values), max(recent_values))
            return None
        recent_mean = statistics.mean(recent_values[-self.DRIFT_WINDOW_SIZE:])
        recent_std = statistics.stdev(recent_values[-self.DRIFT_WINDOW_SIZE:]) or 0.001
        mean_shift = abs(recent_mean - baseline["mean"]) / max(abs(baseline["mean"]), 0.001)
        std_shift = abs(recent_std - baseline["std"]) / max(baseline["std"], 0.001)
        if mean_shift > self.DRIFT_THRESHOLD or std_shift > self.DRIFT_THRESHOLD * 2:
            event = AnomalyEvent(
                event_id=f"drift_{int(time.time()*1000)}",
                severity=AnomalySeverity.WARNING,
                metric_name=metric_name,
                detected_at=datetime.now().isoformat(),
                current_value=recent_mean,
                expected_range=(round(baseline["mean"] * (1 - self.DRIFT_THRESHOLD), 4),
                                 round(baseline["mean"] * (1 + self.DRIFT_THRESHOLD), 4)),
                description=f"指标漂移: 均值偏移{mean_shift:.1%}, 标准差偏移{std_shift:.1%}",
                suggested_action="重新校准基线或检查环境变化",
            )
            self._event_history.append(event)
            return event
        return None

    def resolve_event(self, event_id: str, action_taken: str = ""):
        for event in self._event_history:
            if event.event_id == event_id:
                event.resolved = True
                event.action_taken = action_taken
                break

    def get_active_anomalies(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._event_history if not e.resolved][-20:]

    def get_statistics(self) -> Dict[str, Any]:
        total = len(self._event_history)
        resolved = sum(1 for e in self._event_history if e.resolved)
        by_severity = defaultdict(int)
        for e in self._event_history:
            by_severity[e.severity.value] += 1
        return {
            "total_events": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "resolution_rate": round(resolved / max(total, 1), 3),
            "by_severity": dict(by_severity),
            "baselines_tracked": len(self._baseline_stats),
        }


anomaly_detector = AnomalyDetector()


class TrendAnalyzer:
    """
    趋势分析器 — 对应提示词 6.1 进化过程可视化
    
    分析时间序列数据的趋势方向、速度和加速度。
    """

    def analyze_trend(self, values: List[float], window_size: int = 5) -> Dict[str, Any]:
        if len(values) < 3:
            return {"trend": "insufficient_data", "direction": "neutral", "strength": 0.0}
        recent = values[-window_size:]
        older = values[-2*window_size:-window_size] if len(values) >= 2*window_size else values[:len(values)-len(recent)]
        if not older:
            older = [values[0]] * len(recent)
        recent_avg = statistics.mean(recent)
        older_avg = statistics.mean(older)
        direction = "rising" if recent_avg > older_avg * 1.02 else ("falling" if recent_avg < older_avg * 0.98 else "stable")
        change_rate = (recent_avg - older_avg) / max(abs(older_avg), 0.001)
        strength = min(abs(change_rate) * 10, 1.0)
        if len(values) >= window_size * 2:
            prev_recent = values[-2*window_size:-window_size]
            prev_older = values[-3*window_size:-2*window_size] if len(values) >= 3*window_size else values[:len(prev_recent)]
            if not prev_older:
                prev_older = [values[0]] * len(prev_recent)
            prev_change = (statistics.mean(prev_recent) - statistics.mean(prev_older)) / max(abs(statistics.mean(prev_older)), 0.001)
            acceleration = change_rate - prev_change
        else:
            acceleration = 0.0
        volatility = statistics.stdev(recent) / max(abs(recent_avg), 0.001) if len(recent) > 1 else 0.0
        forecast_simple = recent_avg * (1 + change_rate)
        return {
            "trend": direction,
            "direction": direction,
            "strength": round(strength, 3),
            "change_rate": round(change_rate, 4),
            "acceleration": round(acceleration, 4),
            "volatility": round(volatility, 4),
            "recent_avg": round(recent_avg, 4),
            "older_avg": round(older_avg, 4),
            "forecast_next": round(forecast_simple, 4),
            "data_points": len(values),
        }


trend_analyzer = TrendAnalyzer()


class HealthScoringEngine:
    """
    健康评分引擎 — 综合多维度指标生成统一健康分数
    
    评分规则:
      90-100: EXCELLENT (优秀) — 所有核心指标正常
      75-89:   GOOD (良好) — 有轻微偏差但可自愈
      60-74:   FAIR (一般) — 存在需关注的异常
      40-59:   POOR (较差) — 多个指标异常，需要干预
      0-39:    CRITICAL (严重) — 系统处于危险状态
    """

    WEIGHTS = {
        "system_availability": 0.25,
        "performance": 0.20,
        "error_rate": 0.20,
        "resource_utilization": 0.15,
        "evolution_progress": 0.20,
    }

    def compute_health_score(self, metrics: Dict[str, float]) -> Tuple[float, HealthGrade]:
        scores = {}
        scores["system_availability"] = self._score_availability(metrics.get("subsystems_running_ratio", 0.0),
                                                       metrics.get("healthy_subsystems_ratio", 0.0))
        scores["performance"] = self._score_performance(metrics.get("avg_response_time_ms", 500),
                                                      metrics.get("throughput", 100))
        scores["error_rate"] = self._score_error_rate(metrics.get("error_rate", 0.0),
                                                     metrics.get("adversarial_win_rate", 0.5))
        scores["resource_utilization"] = self._score_resources(metrics.get("cpu_percent", 50),
                                                             metrics.get("memory_percent", 50))
        scores["evolution_progress"] = self._score_evolution(metrics.get("overall_completion_pct", 0.0),
                                                           metrics.get("dao_achievement_pct", 0.0),
                                                           metrics.get("stages_completed", 0),
                                                           metrics.get("total_stages", 8))
        weighted_sum = sum(scores[k] * self.WEIGHTS.get(k, 0.1) for k in scores)
        total_weight = sum(self.WEIGHTS.values())
        final_score = weighted_sum / max(total_weight, 0.001)
        final_score = max(0.0, min(100.0, final_score * 100))
        if final_score >= 90:
            grade = HealthGrade.EXCELLENT
        elif final_score >= 75:
            grade = HealthGrade.GOOD
        elif final_score >= 60:
            grade = HealthGrade.FAIR
        elif final_score >= 40:
            grade = HealthGrade.POOR
        else:
            grade = HealthGrade.CRITICAL
        return round(final_score, 1), grade

    def _score_availability(self, running_ratio: float, healthy_ratio: float) -> float:
        return (running_ratio * 0.6 + healthy_ratio * 0.4)

    def _score_performance(self, response_time_ms: float, throughput: float) -> float:
        rt_score = max(0, 1 - response_time_ms / 2000.0)
        tp_score = min(1.0, throughput / 200.0)
        return (rt_score * 0.7 + tp_score * 0.3)

    def _score_error_rate(self, error_rate: float, win_rate: float) -> float:
        err_score = max(0, 1 - error_rate * 10)
        win_score = win_rate
        return (err_score * 0.6 + win_score * 0.4)

    def _score_resources(self, cpu_pct: float, mem_pct: float) -> float:
        ideal_cpu = 50.0
        ideal_mem = 60.0
        cpu_deviation = abs(cpu_pct - ideal_cpu) / 100.0
        mem_deviation = abs(mem_pct - ideal_mem) / 100.0
        return max(0, 1 - (cpu_deviation * 0.5 + mem_deviation * 0.5))

    def _score_evolution(self, completion_pct: float, dao_pct: float, stages_done: float, total_stages: float) -> float:
        comp_score = completion_pct / 100.0
        dao_score = dao_pct / 100.0
        stage_score = stages_done / max(total_stages, 1)
        return (comp_score * 0.3 + dao_score * 0.4 + stage_score * 0.3)

    def generate_report(self, snapshot: SystemSnapshot, anomalies: List[AnomalyEvent],
                       fusion_metrics: Dict[str, FusedMetric]) -> HealthReport:
        metrics_for_scoring = {
            "subsystems_running_ratio": 1.0,
            "healthy_subsystems_ratio": 1.0,
            "overall_completion_pct": snapshot.cultivation_status.get("overall_completion", 0),
            "dao_achievement_pct": snapshot.cultivation_status.get("dao_achievement", 0),
            "stages_completed": snapshot.cultivation_status.get("completed_stages", 0),
            "total_stages": snapshot.cultivation_status.get("total_stages", 8),
            "error_rate": snapshot.cultivation_status.get("active_alerts", 0) / 100.0,
            "adversarial_win_rate": snapshot.cultivation_status.get("avg_win_rate", 0.8),
            "cpu_percent": snapshot.resource_metrics.get("cpu_percent", 50),
            "memory_percent": snapshot.resource_metrics.get("memory_percent", 50),
            "avg_response_time_ms": snapshot.resource_metrics.get("memory_used_mb", 512),
            "throughput": 100.0,
        }
        score, grade = self.compute_health_score(metrics_for_scoring)
        findings = []
        if score < 60:
            findings.append(f"综合健康分数偏低({score:.0f})，存在多个异常指标")
        active_anomalies = [a for a in anomalies if not a.resolved]
        if active_anomalies:
            findings.append(f"存在{len(active_anomalies)}个未解决的异常事件")
        critical_anomalies = [a for a in active_anomalies if a.severity == AnomalySeverity.CRITICAL]
        if critical_anomalies:
            findings.append(f"包含{len(critical_anomalies)}个严重级别异常")
        completion = snapshot.cultivation_status.get("overall_completion", 0)
        if completion < 30:
            findings.append(f"修炼进度较低({completion:.0f}%)，建议加速训练")
        alerts = snapshot.cultivation_status.get("active_alerts", 0)
        if alerts > 3:
            findings.append(f"活跃告警数量较多({alerts}个)，需关注瓶颈阶段")
        recommendations = []
        if grade in (HealthGrade.POOR, HealthGrade.CRITICAL):
            recommendations.append("立即执行全面健康检查，定位根本原因")
            recommendations.append("考虑暂停非关键任务，释放资源用于修复")
        elif grade == HealthGrade.FAIR:
            recommendations.append("关注异常趋势，预防性调整参数")
        if critical_anomalies:
            recommendations.append(f"优先处理{len(critical_anomalies)}个严重异常")
        if completion < 50:
            recommendations.append("考虑触发加速进化循环")
        sub_scores = {}
        for name, weight in self.WEIGHTS.items():
            sub_scores[name] = round(score, 1)
        return HealthReport(
            report_id=f"health_{int(time.time())}",
            timestamp=snapshot.timestamp,
            overall_grade=grade,
            overall_score=score,
            subsystem_scores=sub_scores,
            key_findings=findings,
            anomalies=active_anomalies,
            recommendations=recommendations,
            next_check_suggested=300.0 if grade in (HealthGrade.GOOD, HealthGrade.EXCELLENT) else 60.0,
        )


health_scoring_engine = HealthScoringEngine()
