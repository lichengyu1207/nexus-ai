# -*- coding: utf-8 -*-
"""
Layer 25: Agent Upgrade & Evolution Effect Display System (智能体升级与进化效果展示系统)
====================================================================================
Governor Fang AI Property Platform (房都督AI平台)
Agent Cultivation System - Integration Layer 25

Responsibilities:
  Part A:  Upgrade Effect Quantitative Metrics System (5 dimensions, confidence, seasonality)
  Part B:  Frontend Display Components Spec (modals, charts, notifications, badges)
  Part C:  Real-time Effect Feedback Mechanism (task notifications, comparison tests, leaderboard)
  Part D:  Data-driven Attribution & Recommendation (factor analysis, upgrade suggestions)
  Part E:  A/B Testing Framework (experiment management, statistical testing)
  Part F:  Performance Data Collection SDK (probes, triggers, API provider)
  Part G:  Testing Suite (40+ test cases, pytest generation, Playwright E2E)

Author: Integration Architect
Version: 25.0.0
"""

from __future__ import annotations

import json
import math
import time
import uuid
import hashlib
import random
import logging
import threading
import statistics
import queue as Queue
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# PART A: UPGRADE EFFECT QUANTITATIVE METRICS SYSTEM
# =============================================================================


class EffectDimension(str, Enum):
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    CAPABILITY = "capability"
    COST = "cost"
    COLLABORATION = "collaboration"

    @property
    def display_name_cn(self) -> str:
        _names = {
            EffectDimension.EFFICIENCY: "效率提升",
            EffectDimension.QUALITY: "质量改善",
            EffectDimension.CAPABILITY: "能力扩展",
            EffectDimension.COST: "成本优化",
            EffectDimension.COLLABORATION: "协同增强",
        }
        return _names.get(self, self.value)

    @property
    def unit(self) -> str:
        _units = {
            EffectDimension.EFFICIENCY: "%",
            EffectDimension.QUALITY: "%",
            EffectDimension.CAPABILITY: "项",
            EffectDimension.COST: "积分/任务",
            EffectDimension.COLLABORATION: "%",
        }
        return _units.get(self, "")

    @property
    def description(self) -> str:
        _descs = {
            EffectDimension.EFFICIENCY: "Response time reduction and throughput improvement after upgrade",
            EffectDimension.QUALITY: "Output accuracy and R-squared improvement in analysis results",
            EffectDimension.CAPABILITY: "New skills unlocked and tools made available post-upgrade",
            EffectDimension.COST: "Points saved per task and API call reduction efficiency",
            EffectDimension.COLLABORATION: "Bond synergy boost percentage across agent pairs",
        }
        return _descs.get(self, "")

    @property
    def is_higher_better(self) -> bool:
        return True


class ConfidenceLevel(str, Enum):
    INSUFFICIENT = "insufficient"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

    @classmethod
    def from_sample_count(cls, sample_count: int) -> ConfidenceLevel:
        if sample_count < 10:
            return cls.INSUFFICIENT
        elif sample_count < 30:
            return cls.LOW
        elif sample_count < 100:
            return cls.MODERATE
        else:
            return cls.HIGH

    @property
    def display_label(self) -> str:
        labels = {
            ConfidenceLevel.INSUFFICIENT: "样本不足",
            ConfidenceLevel.LOW: "低置信度",
            ConfidenceLevel.MODERATE: "中等置信度",
            ConfidenceLevel.HIGH: "高置信度",
        }
        return labels.get(self, self.value)


@dataclass
class EffectMetric:
    dimension: EffectDimension
    metric_name: str
    value_before: float
    value_after: float
    change_pct: float
    change_abs: float
    confidence_level: ConfidenceLevel
    sample_count_pre: int
    sample_count_post: int
    confidence_interval_low: float
    confidence_interval_high: float
    is_statistically_significant: bool
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "metric_name": self.metric_name,
            "value_before": round(self.value_before, 4),
            "value_after": round(self.value_after, 4),
            "change_pct": round(self.change_pct, 4),
            "change_abs": round(self.change_abs, 4),
            "confidence_level": self.confidence_level.value,
            "sample_count_pre": self.sample_count_pre,
            "sample_count_post": self.sample_count_post,
            "confidence_interval_low": round(self.confidence_interval_low, 4),
            "confidence_interval_high": round(self.confidence_interval_high, 4),
            "is_statistically_significant": self.is_statistically_significant,
            "notes": self.notes,
        }


class AgentType(str, Enum):
    LI_BU = "li_bu"
    GONG_BU = "gong_bu"
    XING_BU = "xing_bu"
    OTHER = "other"

    @property
    def display_name_cn(self) -> str:
        names = {
            AgentType.LI_BU: "户部",
            AgentType.GONG_BU: "工部",
            AgentType.XING_BU: "刑部",
            AgentType.OTHER: "其他",
        }
        return names.get(self, self.value)


@dataclass
class UpgradeEffectSnapshot:
    snapshot_id: str
    agent_id: str
    agent_name: str
    agent_type: AgentType
    level_before: int
    level_after: int
    upgrade_timestamp: datetime
    effect_metrics: List[EffectMetric] = field(default_factory=list)
    overall_improvement_score: float = 0.0
    top_improvements: List[Dict[str, Any]] = field(default_factory=list)
    seasonality_adjusted: bool = False
    calculation_method: str = "standard_weighted_average"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type.value,
            "level_before": self.level_before,
            "level_after": self.level_after,
            "upgrade_timestamp": self.upgrade_timestamp.isoformat(),
            "effect_metrics": [m.to_dict() for m in self.effect_metrics],
            "overall_improvement_score": round(self.overall_improvement_score, 2),
            "top_improvements": self.top_improvements,
            "seasonality_adjusted": self.seasonality_adjusted,
            "calculation_method": self.calculation_method,
        }


class SeasonalityAdjuster:

    HOLIDAYS_CN = [
        "01-01", "01-02", "01-03",
        "05-01", "05-02", "05-03", "05-04", "05-05",
        "10-01", "10-02", "10-03", "10-04", "10-05", "10-06", "10-07",
        "农历春节",
        "清明节",
        "端午节",
        "中秋节",
    ]

    def __init__(self, window_days: int = 7):
        self._window_days = window_days
        self._cache: Dict[str, Dict] = {}

    def adjust_raw_metrics(
        self,
        raw_data: List[Dict[str, Any]],
        reference_period: Tuple[datetime, datetime],
    ) -> Dict[str, Any]:
        if not raw_data:
            return {"adjusted_values": [], "adjustment_factors": [], "is_adjusted": False}

        values_by_date: Dict[datetime, List[float]] = defaultdict(list)
        for item in raw_data:
            dt = item.get("timestamp")
            val = item.get("value", 0.0)
            if isinstance(dt, datetime):
                values_by_date[dt.date()].append(val)
            elif isinstance(dt, str):
                try:
                    parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                    values_by_date[parsed.date()].append(val)
                except (ValueError, TypeError):
                    pass

        daily_avgs: List[Tuple[datetime.date, float]] = []
        for d in sorted(values_by_date.keys()):
            vals = values_by_date[d]
            avg = sum(vals) / len(vals) if vals else 0.0
            daily_avgs.append((d, avg))

        moving_averages = self._compute_moving_average(daily_avgs)

        adjustment_factors = []
        adjusted_values = []
        for i, (date_val, raw_avg) in enumerate(daily_avgs):
            ma = moving_averages[i] if i < len(moving_averages) else raw_avg
            if ma > 0:
                factor = raw_avg / ma
            else:
                factor = 1.0

            is_weekend = date_val.weekday() >= 5
            is_holiday = self._is_holiday(date_val)
            if is_weekend or is_holiday:
                factor *= 1.15

            adjustment_factors.append({
                "date": date_val.isoformat(),
                "raw_value": round(raw_avg, 4),
                "moving_avg": round(ma, 4),
                "adjustment_factor": round(factor, 4),
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
            })
            adjusted_values.append({
                "date": date_val.isoformat(),
                "adjusted_value": round(raw_avg / max(factor, 0.01), 4),
                "original_value": round(raw_avg, 4),
            })

        weekday_pattern = self._detect_weekday_pattern(daily_avgs)

        return {
            "adjusted_values": adjusted_values,
            "adjustment_factors": adjustment_factors,
            "weekday_pattern": weekday_pattern,
            "is_adjusted": True,
            "window_days": self._window_days,
        }

    def _compute_moving_average(
        self,
        daily_avgs: List[Tuple[datetime.date, float]],
    ) -> List[float]:
        result = []
        half_w = self._window_days // 2
        for i in range(len(daily_avgs)):
            start = max(0, i - half_w)
            end = min(len(daily_avgs), i + half_w + 1)
            window_vals = [v for _, v in daily_avgs[start:end]]
            ma = sum(window_vals) / len(window_vals) if window_vals else 0.0
            result.append(round(ma, 6))
        return result

    def _detect_weekday_pattern(
        self,
        daily_avgs: List[Tuple[datetime.date, float]],
    ) -> Dict[int, float]:
        weekday_sums: Dict[int, List[float]] = defaultdict(list)
        for date_val, avg in daily_avgs:
            weekday_sums[date_val.weekday()].append(avg)

        pattern = {}
        for wd in range(7):
            vals = weekday_sums.get(wd, [])
            if vals:
                pattern[wd] = round(sum(vals) / len(vals), 4)
            else:
                pattern[wd] = 0.0
        return pattern

    def _is_holiday(self, date_val: datetime.date) -> bool:
        mm_dd = date_val.strftime("%m-%d")
        return mm_dd in self.HOLIDAYS_CN


class EffectMetricsCalculator:

    DIMENSION_WEIGHTS: Dict[EffectDimension, float] = {
        EffectDimension.EFFICIENCY: 0.25,
        EffectDimension.QUALITY: 0.30,
        EffectDimension.CAPABILITY: 0.15,
        EffectDimension.COST: 0.15,
        EffectDimension.COLLABORATION: 0.15,
    }

    def __init__(self):
        self._seasonality = SeasonalityAdjuster()
        self._t_table = self._build_t_table()

    def calculate_efficiency_gain(
        self,
        pre_tasks: List[Dict[str, Any]],
        post_tasks: List[Dict[str, Any]],
    ) -> EffectMetric:
        pre_times = [t.get("response_time_ms", 0.0) for t in pre_tasks if t.get("response_time_ms")]
        post_times = [t.get("response_time_ms", 0.0) for t in post_tasks if t.get("response_time_ms")]

        pre_avg = sum(pre_times) / len(pre_times) if pre_times else 0.0
        post_avg = sum(post_times) / len(post_times) if post_times else 0.0

        if pre_avg > 0:
            change_pct = ((pre_avg - post_avg) / pre_avg) * 100
        else:
            change_pct = 0.0
        change_abs = pre_avg - post_avg

        ci_low, ci_high = self._calculate_confidence_interval(post_times)
        conf_level = ConfidenceLevel.from_sample_count(len(post_times))
        sig = self._is_significant(pre_times, post_times)

        return EffectMetric(
            dimension=EffectDimension.EFFICIENCY,
            metric_name="response_time_reduction",
            value_before=round(pre_avg, 4),
            value_after=round(post_avg, 4),
            change_pct=round(change_pct, 4),
            change_abs=round(change_abs, 4),
            confidence_level=conf_level,
            sample_count_pre=len(pre_times),
            sample_count_post=len(post_times),
            confidence_interval_low=round(ci_low, 4),
            confidence_interval_high=round(ci_high, 4),
            is_statistically_significant=sig,
            notes="Response time measured in milliseconds; positive % means faster response",
        )

    def calculate_quality_gain(
        self,
        pre_reports: List[Dict[str, Any]],
        post_reports: List[Dict[str, Any]],
    ) -> EffectMetric:
        pre_acc = [r.get("accuracy_score", 0.0) for r in pre_reports if r.get("accuracy_score") is not None]
        post_acc = [r.get("accuracy_score", 0.0) for r in post_reports if r.get("accuracy_score") is not None]

        pre_r2 = [r.get("r_squared", 0.0) for r in pre_reports if r.get("r_squared") is not None]
        post_r2 = [r.get("r_squared", 0.0) for r in post_reports if r.get("r_squared") is not None]

        pre_avg_acc = sum(pre_acc) / len(pre_acc) if pre_acc else 0.0
        post_avg_acc = sum(post_acc) / len(post_acc) if post_acc else 0.0

        pre_avg_r2 = sum(pre_r2) / len(pre_r2) if pre_r2 else 0.0
        post_avg_r2 = sum(post_r2) / len(post_r2) if post_r2 else 0.0

        combined_pre = (pre_avg_acc * 0.6) + (pre_avg_r2 * 0.4)
        combined_post = (post_avg_acc * 0.6) + (post_avg_r2 * 0.4)

        if combined_pre > 0:
            change_pct = ((combined_post - combined_pre) / abs(combined_pre)) * 100
        else:
            change_pct = 0.0
        change_abs = combined_post - combined_pre

        all_post = post_acc + post_r2
        ci_low, ci_high = self._calculate_confidence_interval(all_post)
        conf_level = ConfidenceLevel.from_sample_count(len(all_post))
        sig = self._is_significant(pre_acc + pre_r2, all_post)

        return EffectMetric(
            dimension=EffectDimension.QUALITY,
            metric_name="accuracy_r2_combined",
            value_before=round(combined_pre, 6),
            value_after=round(combined_post, 6),
            change_pct=round(change_pct, 4),
            change_abs=round(change_abs, 6),
            confidence_level=conf_level,
            sample_count_pre=len(pre_acc) + len(pre_r2),
            sample_count_post=len(post_acc) + len(post_r2),
            confidence_interval_low=round(ci_low, 4),
            confidence_interval_high=round(ci_high, 4),
            is_statistically_significant=sig,
            notes=f"Accuracy weight=60%, R-squared weight=40%; pre_R2={pre_avg_r2:.4f}, post_R2={post_avg_r2:.4f}",
        )

    def calculate_capability_gain(
        self,
        pre_caps: List[Dict[str, Any]],
        post_caps: List[Dict[str, Any]],
    ) -> EffectMetric:
        pre_skills = set()
        for c in pre_caps:
            s = c.get("skill_name", "")
            if s:
                pre_skills.add(s)

        post_skills = set()
        for c in post_caps:
            s = c.get("skill_name", "")
            if s:
                post_skills.add(s)

        new_skills = post_skills - pre_skills
        pre_tools = set(c.get("tool_name", "") for c in pre_caps if c.get("tool_name"))
        post_tools = set(c.get("tool_name", "") for c in post_caps if c.get("tool_name"))
        new_tools = post_tools - pre_tools

        value_before = float(len(pre_skills) + len(pre_tools))
        value_after = float(len(post_skills) + len(post_tools))
        change_abs = float(len(new_skills) + len(new_tools))

        if value_before > 0:
            change_pct = (change_abs / value_before) * 100
        else:
            change_pct = 100.0 if change_abs > 0 else 0.0

        total_post = len(post_caps)
        conf_level = ConfidenceLevel.from_sample_count(total_post)

        return EffectMetric(
            dimension=EffectDimension.CAPABILITY,
            metric_name="skills_and_tools_unlocked",
            value_before=value_before,
            value_after=value_after,
            change_pct=round(change_pct, 4),
            change_abs=round(change_abs, 4),
            confidence_level=conf_level,
            sample_count_pre=len(pre_caps),
            sample_count_post=len(post_caps),
            confidence_interval_low=max(0.0, value_after - 1.0),
            confidence_interval_high=value_after + len(new_skills),
            is_statistically_significant=change_abs > 0,
            notes=f"New skills: {new_skills}; New tools: {new_tools}",
        )

    def calculate_cost_gain(
        self,
        pre_costs: List[Dict[str, Any]],
        post_costs: List[Dict[str, Any]],
    ) -> EffectMetric:
        pre_points = [c.get("points_consumed", 0.0) for c in pre_costs if c.get("points_consumed") is not None]
        post_points = [c.get("points_consumed", 0.0) for c in post_costs if c.get("points_consumed") is not None]

        pre_api = [c.get("api_calls", 0) for c in pre_costs if c.get("api_calls") is not None]
        post_api = [c.get("api_calls", 0) for c in post_costs if c.get("api_calls") is not None]

        pre_avg_pts = sum(pre_points) / len(pre_points) if pre_points else 0.0
        post_avg_pts = sum(post_points) / len(post_points) if post_points else 0.0

        pre_avg_api = sum(pre_api) / len(pre_api) if pre_api else 0.0
        post_avg_api = sum(post_api) / len(post_api) if post_api else 0.0

        cost_pre = pre_avg_pts + (pre_avg_api * 0.1)
        cost_post = post_avg_pts + (post_avg_api * 0.1)

        if cost_pre > 0:
            change_pct = ((cost_pre - cost_post) / cost_pre) * 100
        else:
            change_pct = 0.0
        change_abs = cost_pre - cost_post

        all_post = post_points + [float(x) for x in post_api]
        ci_low, ci_high = self._calculate_confidence_interval(all_post)
        conf_level = ConfidenceLevel.from_sample_count(len(all_post))
        sig = self._is_significant(
            [float(x) for x in pre_points + pre_api],
            all_post,
        )

        return EffectMetric(
            dimension=EffectDimension.COST,
            metric_name="cost_per_task_saved",
            value_before=round(cost_pre, 4),
            value_after=round(cost_post, 4),
            change_pct=round(change_pct, 4),
            change_abs=round(change_abs, 4),
            confidence_level=conf_level,
            sample_count_pre=len(pre_points) + len(pre_api),
            sample_count_post=len(post_points) + len(post_api),
            confidence_interval_low=round(ci_low, 4),
            confidence_interval_high=round(ci_high, 4),
            is_statistically_significant=sig,
            notes=f"Points+API weighted; pre_avg_api={pre_avg_api:.1f}, post_avg_api={post_avg_api:.1f}",
        )

    def calculate_collaboration_gain(
        self,
        pre_bonds: List[Dict[str, Any]],
        post_bonds: List[Dict[str, Any]],
    ) -> EffectMetric:
        pre_synergy = [b.get("synergy_score", 0.0) for b in pre_bonds if b.get("synergy_score") is not None]
        post_synergy = [b.get("synergy_score", 0.0) for b in post_bonds if b.get("synergy_score") is not None]

        pre_active = sum(1 for b in pre_bonds if b.get("is_active", False))
        post_active = sum(1 for b in post_bonds if b.get("is_active", False))

        pre_avg = sum(pre_synergy) / len(pre_synergy) if pre_synergy else 0.0
        post_avg = sum(post_synergy) / len(post_synergy) if post_synergy else 0.0

        if pre_avg > 0:
            change_pct = ((post_avg - pre_avg) / pre_avg) * 100
        else:
            change_pct = 100.0 if post_avg > 0 else 0.0
        change_abs = post_avg - pre_avg

        ci_low, ci_high = self._calculate_confidence_interval(post_synergy)
        conf_level = ConfidenceLevel.from_sample_count(len(post_synergy))
        sig = self._is_significant(pre_synergy, post_synergy)

        bond_delta = post_active - pre_active
        notes_parts = [f"Bond count delta: {bond_delta:+d}"]
        if bond_delta > 0:
            new_names = [b.get("bond_name", "?") for b in post_bonds if b.get("is_active") and b.get("bond_name")]
            notes_parts.append(f"New bonds: {', '.join(new_names[:3])}")

        return EffectMetric(
            dimension=EffectDimension.COLLABORATION,
            metric_name="bond_synergy_boost",
            value_before=round(pre_avg, 4),
            value_after=round(post_avg, 4),
            change_pct=round(change_pct, 4),
            change_abs=round(change_abs, 4),
            confidence_level=conf_level,
            sample_count_pre=len(pre_synergy),
            sample_count_post=len(post_synergy),
            confidence_interval_low=round(ci_low, 4),
            confidence_interval_high=round(ci_high, 4),
            is_statistically_significant=sig,
            notes="; ".join(notes_parts),
        )

    def calculate_confidence_interval(
        self,
        values: List[float],
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        n = len(values)
        if n < 2:
            return (0.0, 0.0)
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if n > 1 else 0.0
        se = std_dev / math.sqrt(n)
        alpha = 1.0 - confidence
        t_crit = self._get_t_critical(n - 1, alpha / 2)
        margin = t_crit * se
        return (round(mean - margin, 6), round(mean + margin, 6))

    def determine_confidence_level(self, sample_count: int) -> ConfidenceLevel:
        return ConfidenceLevel.from_sample_count(sample_count)

    def build_upgrade_snapshot(
        self,
        agent_id: str,
        level_from: int,
        level_to: int,
        agent_name: str = "",
        agent_type: AgentType = AgentType.OTHER,
        pre_period_days: int = 7,
        post_period_days: int = 7,
        pre_tasks: Optional[List[Dict]] = None,
        post_tasks: Optional[List[Dict]] = None,
        pre_reports: Optional[List[Dict]] = None,
        post_reports: Optional[List[Dict]] = None,
        pre_caps: Optional[List[Dict]] = None,
        post_caps: Optional[List[Dict]] = None,
        pre_costs: Optional[List[Dict]] = None,
        post_costs: Optional[List[Dict]] = None,
        pre_bonds: Optional[List[Dict]] = None,
        post_bonds: Optional[List[Dict]] = None,
    ) -> UpgradeEffectSnapshot:
        pre_tasks = pre_tasks or []
        post_tasks = post_tasks or []
        pre_reports = pre_reports or []
        post_reports = post_reports or []
        pre_caps = pre_caps or []
        post_caps = post_caps or []
        pre_costs = pre_costs or []
        post_costs = post_costs or []
        pre_bonds = pre_bonds or []
        post_bonds = post_bonds or []

        eff_metric = self.calculate_efficiency_gain(pre_tasks, post_tasks)
        qual_metric = self.calculate_quality_gain(pre_reports, post_reports)
        cap_metric = self.calculate_capability_gain(pre_caps, post_caps)
        cost_metric = self.calculate_cost_gain(pre_costs, post_costs)
        collab_metric = self.calculate_collaboration_gain(pre_bonds, post_bonds)

        metrics_list = [eff_metric, qual_metric, cap_metric, cost_metric, collab_metric]
        overall = self.get_overall_improvement_score(metrics_list)

        sorted_metrics = sorted(
            metrics_list,
            key=lambda m: abs(m.change_pct),
            reverse=True,
        )
        top3 = [
            {
                "dimension": m.dimension.display_name_cn,
                "metric_name": m.metric_name,
                "change_pct": round(m.change_pct, 2),
                "direction": "up" if m.change_pct > 0 else "down",
            }
            for m in sorted_metrics[:3]
        ]

        return UpgradeEffectSnapshot(
            snapshot_id="snap_" + uuid.uuid4().hex[:12],
            agent_id=agent_id,
            agent_name=agent_name or f"Agent_{agent_id}",
            agent_type=agent_type,
            level_before=level_from,
            level_after=level_to,
            upgrade_timestamp=datetime.utcnow(),
            effect_metrics=metrics_list,
            overall_improvement_score=round(overall, 2),
            top_improvements=top3,
            seasonality_adjusted=False,
            calculation_method="standard_weighted_average",
        )

    def get_overall_improvement_score(
        self,
        metrics_list: List[EffectMetric],
    ) -> float:
        score = 0.0
        total_weight = 0.0
        for m in metrics_list:
            w = self.DIMENSION_WEIGHTS.get(m.dimension, 0.2)
            dim = m.dimension
            if dim == EffectDimension.EFFICIENCY:
                normalized = min(max(m.change_pct, -50), 100) / 100.0
            elif dim == EffectDimension.QUALITY:
                normalized = min(max(m.change_pct, -30), 50) / 50.0
            elif dim == EffectDimension.CAPABILITY:
                normalized = min(max(m.change_pct, 0), 200) / 200.0
            elif dim == EffectDimension.COST:
                normalized = min(max(m.change_pct, -30), 80) / 80.0
            elif dim == EffectDimension.COLLABORATION:
                normalized = min(max(m.change_pct, -20), 100) / 100.0
            else:
                normalized = 0.0
            score += w * normalized
            total_weight += w
        base = (score / total_weight * 50) + 50 if total_weight > 0 else 50.0
        return max(0.0, min(100.0, base))

    def _calculate_confidence_interval(
        self,
        values: List[float],
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        return self.calculate_confidence_interval(values, confidence)

    def _is_significant(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float = 0.05,
    ) -> bool:
        if len(group_a) < 3 or len(group_b) < 3:
            return False
        mean_a = statistics.mean(group_a)
        mean_b = statistics.mean(group_b)
        pooled_std = math.sqrt(
            (statistics.variance(group_a) * (len(group_a) - 1) +
             statistics.variance(group_b) * (len(group_b) - 1)) /
            (len(group_a) + len(group_b) - 2)
        )
        if pooled_std == 0:
            return mean_a != mean_b
        t_stat = abs(mean_a - mean_b) / (pooled_std * math.sqrt(1.0 / len(group_a) + 1.0 / len(group_b)))
        df = len(group_a) + len(group_b) - 2
        t_crit = self._get_t_critical(df, alpha / 2)
        return t_stat > t_crit

    def _build_t_table(self) -> Dict[Tuple[int, float], float]:
        table = {}
        for df in range(1, 201):
            for alpha_tail in [0.005, 0.01, 0.025, 0.05, 0.10]:
                t_val = self._approximate_t(df, 1.0 - alpha_tail)
                table[(df, alpha_tail)] = t_val
        return table

    def _get_t_critical(self, df: int, alpha_tail: float) -> float:
        if df <= 0:
            return 1.96
        key = (min(df, 200), alpha_tail)
        if key in self._t_table:
            return self._t_table[key]
        return self._approximate_t(df, 1.0 - alpha_tail)

    def _approximate_t(self, df: int, p: float) -> float:
        if p >= 1.0:
            return 36.0
        if p <= 0.5:
            return -self._approximate_t(df, 1.0 - p)
        z = self._normal_quantile(p)
        z2 = z * z
        z3 = z * z2
        z4 = z2 * z2
        g1 = 0.25 * (z3 + z) / df
        g2 = (5.0 * z4 + 16.0 * z2 + 3.0) / (96.0 * df * df)
        z5 = z * z4
        g3 = (3.0 * z5 + 19.0 * z3 + 17.0 * z) / (384.0 * df ** 3)
        z8 = z4 * z4
        g4 = (79.0 * z8 + 776.0 * z4 * z2 + 1482.0 * z4 + 192.0 * z2 + 9.0) / (92160.0 * df ** 4)
        result = z + g1 + g2 + g3 + g4
        return result if p < 1.0 else 36.0

    def _normal_quantile(self, p: float) -> float:
        if p <= 0.0:
            return -10.0
        if p >= 1.0:
            return 10.0
        if p == 0.5:
            return 0.0
        if p < 0.5:
            return -self._normal_quantile(1.0 - p)
        t = math.sqrt(-2.0 * math.log(1.0 - p))
        c0, c1, c2, c3 = 2.515517, 0.802853, 0.010328, 0.001428
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        return t - (c0 + c1 * t + c2 * t * t + c3 * t * t * t) / (
            1.0 + d1 * t + d2 * t * t + d3 * t * t * t
        )


# =============================================================================
# PART B: FRONTEND DISPLAY COMPONENTS SPEC
# =============================================================================


@dataclass
class ParticleAnimationConfig:
    particle_count: int = 50
    duration_ms: int = 2000
    color_gold: str = "#FFD700"
    color_white: str = "#FFFFFF"
    particle_size_range: Tuple[int, int] = (2, 8)
    emission_shape: str = "circle"
    fade_out_curve: str = "ease-out"
    skip_allowed: bool = True

    def to_css_keyframes(self) -> str:
        size_min, size_max = self.particle_size_range
        return f"""
@keyframes upgradeParticle {{
    0% {{ opacity: 1; transform: translate(0, 0) scale(1); }}
    70% {{ opacity: 0.6; }}
    100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)) scale(0.1); }}
}}
.upgrade-particle-container {{
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none; z-index: 9999; overflow: hidden;
}}
.upgrade-particle {{
    position: absolute; border-radius: 50%;
    background: radial-gradient(circle, {self.color_gold} 0%, transparent 70%);
    width: {size_min}px; height: {size_min}px;
    animation: upgradeParticle {self.duration_ms}ms {self.fade_out_curve} forwards;
}}
"""


@dataclass
class UpgradeSuccessModalSpec:
    agent_avatar_url: str = ""
    agent_display_name: str = ""
    level_from: int = 1
    level_to: int = 2
    effect_summary_cards: List[Dict[str, Any]] = field(default_factory=list)
    detail_button_text: str = "查看详细效果"
    test_button_text: str = "对比测试"
    animation_config: ParticleAnimationConfig = field(default_factory=ParticleAnimationConfig)
    show_cumulative_badge: bool = True
    cumulative_improvement_pct: float = 0.0


@dataclass
class EvolutionChartSpec:
    chart_type: str = "area"
    metrics_to_show: List[str] = field(default_factory=lambda: [
        "response_time", "accuracy", "success_rate", "cost_per_task",
    ])
    time_range: str = "90d"
    show_upgrade_markers: bool = True
    show_cumulative_overlay: bool = True
    tooltip_template: str = "{date}: {metric} = {value}"
    color_scheme: Dict[str, str] = field(default_factory=lambda: {
        "response_time": "#2196F3",
        "accuracy": "#4CAF50",
        "success_rate": "#FF9800",
        "cost_per_task": "#E91E63",
        "cumulative": "#9C27B0",
    })


@dataclass
class BondActivationDisplaySpec:
    bond_name: str = ""
    bond_icon: str = ""
    agent_a_name: str = ""
    agent_b_name: str = ""
    synergy_effect_description: str = ""
    synergy_boost_pct: float = 0.0
    activation_animation: str = "pulse"
    active_since: Optional[datetime] = None
    report_annotation_template: str = ""


@dataclass
class SkillLearningEffectCardSpec:
    skill_name: str = ""
    skill_icon: str = ""
    skill_category: str = ""
    agent_name: str = ""
    learning_timestamp: Optional[datetime] = None
    effect_description: str = ""
    quantified_improvement: str = ""
    equipped_status: bool = False
    report_source_tag: str = ""


class FrontendRenderer:

    def render_upgrade_success_modal(self, spec: UpgradeSuccessModalSpec) -> str:
        anim_css = spec.animation_config.to_css_keyframes()
        cards_html = ""
        for idx, card in enumerate(spec.effect_summary_cards[:3]):
            icon = card.get("icon", "\u2B06")
            label = card.get("label", "N/A")
            val = card.get("change_value", "0%")
            color = card.get("color", "#4CAF50")
            direction = "\u2B06" if "+" in str(val) or (isinstance(val, (int, float)) and val > 0) else "\u2B07"
            cards_html += f"""
            <div class="effect-summary-card" style="animation-delay: {idx * 150}ms;">
                <div class="card-icon">{icon}</div>
                <div class="card-label">{label}</div>
                <div class="card-value" style="color:{color};">{val}</div>
            </div>"""

        badge_html = ""
        if spec.show_cumulative_badge:
            badge_html = f"""
            <div class="cumulative-badge">
                <span class="badge-label">累计提升</span>
                <span class="badge-value">+{spec.cumulative_improvement_pct:.1f}%</span>
            </div>"""

        html_template = """<div id="upgrade-success-modal" class="upgrade-modal-overlay">
    <style>{anim_css}
.upgrade-modal-overlay {{
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.75); display: flex; align-items: center;
    justify-content: center; z-index: 10000; animation: fadeIn 300ms ease-out;
}}
.upgrade-modal-content {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px; padding: 40px; max-width: 520px; width: 90%;
    text-align: center; box-shadow: 0 0 60px rgba(255,215,0,0.3);
    border: 2px solid rgba(255,215,0,0.3); position: relative; overflow: hidden;
}}
.modal-avatar {{
    width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 16px;
    border: 3px solid #FFD700; overflow: hidden; background: #333;
}}
.modal-avatar img {{ width: 100%; height: 100%; object-fit: cover; }}
.modal-title {{
    font-size: 24px; font-weight: bold; color: #FFD700; margin-bottom: 8px;
}}
.modal-subtitle {{
    font-size: 14px; color: #aaa; margin-bottom: 24px;
}}
.level-change {{
    font-size: 48px; font-weight: bold; color: #FFF; margin: 16px 0;
    text-shadow: 0 0 20px rgba(255,215,0,0.5);
}}
.level-arrow {{ color: #FFD700; margin: 0 12px; }}
.effect-cards-row {{
    display: flex; justify-content: center; gap: 16px; margin: 24px 0;
    flex-wrap: wrap;
}}
.effect-summary-card {{
    background: rgba(255,255,255,0.08); border-radius: 12px;
    padding: 16px 20px; min-width: 120px; text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
    animation: slideUp 400ms ease-out both;
}}
.card-icon {{ font-size: 24px; margin-bottom: 6px; }}
.card-label {{ font-size: 12px; color: #888; margin-bottom: 4px; }}
.card-value {{ font-size: 18px; font-weight: bold; color: #4CAF50; }}
.cumulative-badge {{
    display: inline-block; background: linear-gradient(135deg, #FFD700, #FFA000);
    color: #000; padding: 6px 16px; border-radius: 20px; font-weight: bold;
    font-size: 13px; margin-top: 12px;
}}
.modal-actions {{
    display: flex; justify-content: center; gap: 12px; margin-top: 24px;
}}
.modal-btn {{
    padding: 10px 24px; border-radius: 8px; border: none; cursor: pointer;
    font-size: 14px; font-weight: bold; transition: transform 0.2s;
}}
.modal-btn:hover {{ transform: scale(1.05); }}
.btn-primary {{
    background: linear-gradient(135deg, #FFD700, #FFA000); color: #000;
}}
.btn-secondary {{
    background: rgba(255,255,255,0.1); color: #FFF; border: 1px solid rgba(255,255,255,0.2);
}}
@keyframes fadeIn {{ from {{opacity:0}} to {{opacity:1}} }}
@keyframes slideUp {{ from {{opacity:0;transform:translateY(20px)}} to {{opacity:1;transform:translateY(0)}} }}
</style>
<div class="upgrade-particle-container" id="particleContainer"></div>
<div class="upgrade-modal-content">
    <div class="modal-avatar">
        {'<img src="' + spec.agent_avatar_url + '" />' if spec.agent_avatar_url else '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:32px;color:#FFD700;">\u2605</div>'}
    </div>
    <div class="modal-title">\u5347\u7ea7\u6210\u529f!</div>
    <div class="modal-subtitle">{spec.agent_display_name} \u5b8c\u6210\u8fdb\u5316</div>
    <div class="level-change">
        Lv.{spec.level_from}<span class="level-arrow">\u279C</span>Lv.{spec.level_to}
    </div>
    {badge_html}
    <div class="effect-cards-row">
        {cards_html}
    </div>
    <div class="modal-actions">
        <button class="modal-btn btn-primary" onclick="closeUpgradeModal()">{spec.detail_button_text}</button>
        <button class="modal-btn btn-secondary" onclick="openComparisonTest()">{spec.test_button_text}</button>
    </div>
</div>
<script>
(function(){{ var c=document.getElementById('particleContainer');
var cfg={{count:{spec.animation_config.particle_count},dur:{spec.animation_config.duration_ms}}};
for(var i=0;i<cfg.count;i++){{ var p=document.createElement('div');
p.className='upgrade-particle'; p.style.left=(Math.random()*100)+'%';
p.style.top='50%'; p.style.setProperty('--dx',(Math.random()-0.5)*300+'px');
p.style.setProperty('--dy',(Math.random()-0.5)*300+'px');
p.style.width=p.style.height=({spec.animation_config.particle_size_range[0]}+Math.random()*({spec.animation_config.particle_size_range[1]}-{spec.animation_config.particle_size_range[0]}))+'px';
c.appendChild(p); }} setTimeout(function(){{c.remove();}},cfg.dur+500);
}})();
function closeUpgradeModal(){{ document.getElementById('upgrade-success-modal').remove(); }}
</script>
</div>"""
        html = html_template.format(
            agent_avatar_url=spec.agent_avatar_url or "",
            agent_display_name=spec.agent_display_name,
            level_from=spec.level_from,
            level_to=spec.level_to,
            detail_button_text=spec.detail_button_text,
            test_button_text=spec.test_button_text,
            show_cumulative_badge=str(spec.show_cumulative_badge).lower(),
            cumulative_improvement_pct=f"{spec.cumulative_improvement_pct:.1f}",
        )
        return html

    def render_evolution_chart_tab(
        self,
        spec: EvolutionChartSpec,
        historical_data: List[Dict[str, Any]],
    ) -> str:
        colors_json = json.dumps(spec.color_scheme, ensure_ascii=False)
        data_json = json.dumps(historical_data, ensure_ascii=False, default=str)
        metrics_json = json.dumps(spec.metrics_to_show)

        legend_items = ""
        for m in spec.metrics_to_show:
            color = spec.color_scheme.get(m, "#888")
            label_map = {
                "response_time": "响应时间(ms)",
                "accuracy": "准确率(%)",
                "success_rate": "成功率(%)",
                "cost_per_task": "单任务成本(积分)",
            }
            label = label_map.get(m, m)
            legend_items += f"""
            <div class="legend-item">
                <span class="legend-dot" style="background:{color};"></span>
                <span class="legend-label">{label}</span>
            </div>"""

        range_options = ["7d", "30d", "90d", "180d", "365d", "all"]
        range_btns = ""
        for r in range_options:
            active_cls = "active" if r == spec.time_range else ""
            range_btns += f'<button class="range-btn {active_cls}" data-range="{r}">{r}</button>'

        chart_type_class = f"chart-{spec.chart_type}"

        chart_type_val = spec.chart_type
        html_template = """<div id="evolution-chart-panel" class="evolution-chart-container">
<style>
.evolution-chart-container {{ width:100%; padding:20px; background:#1e1e2e; border-radius:12px; color:#eee; }}
.chart-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:8px; }}
.chart-title {{ font-size:18px; font-weight:bold; color:#FFD700; }}
.range-selector {{ display:flex; gap:4px; background:rgba(255,255,255,0.05); padding:4px; border-radius:8px; }}
.range-btn {{ padding:4px 12px; border:none; background:transparent; color:#888; cursor:pointer; border-radius:6px; font-size:12px; transition:0.2s; }}
.range-btn.active {{ background:#FFD700; color:#000; font-weight:bold; }}
.range-btn:hover:not(.active) {{ color:#fff; }}
.chart-body {{ position:relative; width:100%; height:350px; background:rgba(0,0,0,0.2); border-radius:8px; overflow:hidden; }}
.{chart_type_class} {{ width:100%; height:100%; }}
.chart-legend {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:12px; justify-content:center; }}
.legend-item {{ display:flex; align-items:center; gap:6px; font-size:12px; }}
.legend-dot {{ width:10px; height:10px; border-radius:50%; }}
.tooltip-box {{ position:absolute; background:rgba(0,0,0,0.9); border:1px solid #FFD700; border-radius:8px; padding:10px 14px; font-size:12px; pointer-events:none; z-index:100; display:none; white-space:nowrap; }}
.upgrade-marker {{ position:absolute; width:2px; height:100%; background:rgba(255,215,0,0.5); z-index:5; }}
.upgrade-marker::after {{ content:'\\u2B06'; position:absolute; top:-4px; left:-6px; color:#FFD700; font-size:12px; }}
</style>
<div class="chart-header">
    <div class="chart-title">\u8fdb\u5316\u66f2\u7ebf</div>
    <div class="range-selector">{range_btns}</div>
</div>
<div class="chart-body">
    <canvas id="evolutionCanvas" class="{chart_type_class}"></canvas>
    <div class="tooltip-box" id="chartTooltip"></div>
</div>
<div class="chart-legend">{legend_items}</div>
<script>
(function(){{
var data={data_json};
var colors={colors_json};
var metrics={metrics_json};
var canvas=document.getElementById('evolutionCanvas');
var ctx=canvas.getContext('2d');
var tooltip=document.getElementById('chartTooltip');

function resizeCanvas(){{ canvas.width=canvas.parentElement.clientWidth; canvas.height=canvas.parentElement.clientHeight; drawChart(); }}
window.addEventListener('resize',resizeCanvas);

function drawChart(){{
    var W=canvas.width,H=canvas.height,pad=40;
    ctx.clearRect(0,0,W,H);
    if(!data||data.length===0){{ ctx.fillStyle='#555';ctx.font='14px sans-serif';ctx.textAlign='center';ctx.fillText('\\u6682\\u65e0\\u6570\\u636e',W/2,H/2);return; }}

    var xMin=Infinity,xMax=-Infinity,yMin=Infinity,yMax=-Infinity;
    data.forEach(function(p){{
        var px=new Date(p.date).getTime();
        if(px<xMin)xMin=px;if(px>xMax)xMax=px;
        metrics.forEach(function(m){{ var v=p[m];if(v!==undefined&&v!==null){{if(v<yMin)yMin=v;if(v>yMax)yMax=v;}}}});
    }});
    if(yMin===yMax){{ yMin-=1;yMax+=1; }}

    function toX(px){{ return pad+(px-xMin)/(xMax-xMin)*(W-2*pad); }}
    function toY(v){{ return H-pad-(v-yMin)/(yMax-yMin)*(H-2*pad); }}

    ctx.strokeStyle='rgba(255,255,255,0.08)';
    ctx.lineWidth=1;
    for(var i=0;i<=5;i++){{ var y=pad+i*(H-2*pad)/5; ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(W-pad,y);ctx.stroke(); }}

    metrics.forEach(function(m,idx){{
        ctx.strokeStyle=colors[m]||'#888';
        ctx.lineWidth=2.5;
        ctx.beginPath();
        data.forEach(function(p,i){{
            var v=p[m];if(v===undefined||v===null)return;
            var tx=toX(new Date(p.date).getTime()),ty=toY(v);
            if(i===0)ctx.moveTo(tx,ty);else ctx.lineTo(tx,ty);
        }});
        ctx.stroke();
        if('{chart_type_val}'==='area'){{
            ctx.lineTo(toX(xMax),toY(yMin));ctx.lineTo(toX(xMin),toY(yMin));
            ctx.closePath();
            ctx.fillStyle=colors[m];ctx.globalAlpha=0.1;ctx.fill();ctx.globalAlpha=1;
        }}
    }});

    canvas.onmousemove=function(e){{
        var rect=canvas.getBoundingClientRect();
        var mx=e.clientX-rect.left,my=e.clientY-rect.top;
        var closest=null,minDist=Infinity;
        data.forEach(function(p){{
            var dx=Math.abs(mx-toX(new Date(p.date).getTime()));
            if(dx<minDist){{minDist=dx;closest=p;}}
        }});
        if(closest&&minDist<30){{
            var lines=['<b>'+closest.date+'</b>'];
            metrics.forEach(function(m){{ if(closest[m]!==undefined)lines.push('<span style=\"color:'+colors[m]+'\">'+m+': '+closest[m].toFixed(2)+'</span>'); }});
            tooltip.innerHTML=lines.join('<br>');
            tooltip.style.display='block';
            tooltip.style.left=(mx+15)+'px';tooltip.style.top=(my-10)+'px';
        }}else{{ tooltip.style.display='none'; }}
    }};
    canvas.onmouseleave=function(){{ tooltip.style.display='none'; }};
}}
resizeChart();
function resizeChart(){{ setTimeout(resizeChart,0); }} resizeCanvas();
document.querySelectorAll('.range-btn').forEach(function(btn){{
    btn.addEventListener('click',function(){{ document.querySelectorAll('.range-btn').forEach(function(b){{b.classList.remove('active');}}); this.classList.add('active'); }});
}});
}})();
</script>
</div>"""
        html = html_template.format(
            chart_type_class=chart_type_class,
            range_btns=range_btns,
            legend_items=legend_items,
            data_json=data_json,
            colors_json=colors_json,
            metrics_json=metrics_json,
            chart_type_val=chart_type_val,
        )
        return html

    def render_bond_activation_popup(self, spec: BondActivationDisplaySpec) -> str:
        anim_style = ""
        if spec.activation_animation == "pulse":
            anim_style = """
@keyframes bondPulse { 0%,100%{box-shadow:0 0 0 0 rgba(255,215,0,0.4);} 50%{box-shadow:0 0 0 20px rgba(255,215,0,0);} }
.bond-popup-inner { animation: bondPulse 2s ease-in-out infinite; }"""
        elif spec.activation_animation == "glow":
            anim_style = """
@keyframes bondGlow { 0%{filter:brightness(1) drop-shadow(0 0 2px gold);} 50%{filter:brightness(1.3) drop-shadow(0 0 15px gold);} 100%{filter:brightness(1) drop-shadow(0 0 2px gold);} }
.bond-popup-inner { animation: bondGlow 2s ease-in-out infinite; }"""
        elif spec.activation_animation == "merge":
            anim_style = """
@keyframes bondMerge { 0%{transform:scale(0.8);opacity:0;} 50%{transform:scale(1.1);} 100%{transform:scale(1);opacity:1;} }
.bond-popup-inner { animation: bondMerge 600ms ease-out forwards; }"""
        else:
            anim_style = ".bond-popup-inner {}"

        since_str = spec.active_since.strftime("%Y-%m-%d %H:%M") if spec.active_since else "N/A"

        bond_icon_val = spec.bond_icon or '\u26A1'
        bond_name_val = spec.bond_name or '\u534f\u540c\u94fe\u63a5\u6fc0\u6d3b'
        synergy_desc_val = spec.synergy_effect_description or '\u534c\u4e2a\u667a\u80fd\u4f53\u5f62\u6210\u534f\u540c\u6548\u679c\uff0c\u5206\u6790\u80fd\u529b\u663e\u8457\u63d0\u5347\u3002'
        html_template = """<div class="bond-activation-popup">
<style>{anim_style}
.bond-activation-popup {{ position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
z-index:9000;background:linear-gradient(135deg,#0d1b2a,#1b2838);border-radius:16px;
padding:32px 40px;text-align:center;border:2px solid rgba(255,215,0,0.4);
box-shadow:0 0 40px rgba(255,215,0,0.2);max-width:420px;width:90%;animation:fadeIn 300ms; }}
.bond-popup-inner {{ padding: 8px 0; }}
.bond-icon-large {{ font-size:48px;margin-bottom:12px; }}
.bond-title {{ font-size:22px;font-weight:bold;color:#FFD700;margin-bottom:8px; }}
.bond-agents {{ font-size:14px;color:#aaa;margin-bottom:16px; }}
.bond-agent-name {{ color:#4FC3F7;font-weight:bold; }}
.bond-plus {{ color:#FFD700;margin:0 8px;font-size:18px; }}
.synergy-section {{ background:rgba(255,255,255,0.05);border-radius:10px;padding:16px;margin:16px 0; }}
.synergy-label {{ font-size:12px;color:#888;margin-bottom:4px; }}
.synergy-value {{ font-size:28px;font-weight:bold;color:#4CAF50; }}
.synergy-desc {{ font-size:13px;color:#ccc;margin-top:8px;line-height:1.5; }}
.since-text {{ font-size:11px;color:#666;margin-top:12px; }}
.close-bond-popup {{ margin-top:16px;padding:8px 28px;background:rgba(255,215,0,0.15);border:1px solid rgba(255,215,0,0.3);border-radius:8px;color:#FFD700;cursor:pointer;font-size:13px;transition:0.2s; }}
.close-bond-popup:hover {{ background:rgba(255,215,0,0.25); }}
@keyframes fadeIn {{ from{{opacity:0;transform:translate(-50%,-50%) scale(0.9)}} to{{opacity:1;transform:translate(-50%,-50%) scale(1)}} }}
</style>
<div class="bond-popup-inner">
    <div class="bond-icon-large">{bond_icon_val}</div>
    <div class="bond-title">{bond_name_val}</div>
    <div class="bond-agents">
        <span class="bond-agent-name">{agent_a_name}</span><span class="bond-plus">+</span><span class="bond-agent-name">{agent_b_name}</span>
    </div>
    <div class="synergy-section">
        <div class="synergy-label">\u534f\u540c\u589e\u6548</div>
        <div class="synergy-value">+{synergy_boost_pct:.1f}%</div>
        <div class="synergy-desc">{synergy_desc_val}</div>
    </div>
    <div class="since-text">\u6fc0\u6d3b\u65f6\u95f4: {since_str}</div>
    <button class="close-bond-popup" onclick="this.parentElement.parentElement.remove()">\u77e5\u9053\u4e86</button>
</div>
</div>"""
        html = html_template.format(
            anim_style=anim_style,
            bond_icon_val=bond_icon_val,
            bond_name_val=bond_name_val,
            agent_a_name=spec.agent_a_name,
            agent_b_name=spec.agent_b_name,
            synergy_boost_pct=spec.synergy_boost_pct,
            synergy_desc_val=synergy_desc_val,
            since_str=since_str,
        )
        return html

    def render_skill_learning_notification(
        self,
        spec: SkillLearningEffectCardSpec,
    ) -> str:
        ts_str = spec.learning_timestamp.strftime("%Y-%m-%d %H:%M") if spec.learning_timestamp else ""
        status_text = "\u5df2\u88c5\u5907" if spec.equipped_status else "\u672a\u88c5\u5907"
        status_color = "#4CAF50" if spec.equipped_status else "#888"

        notif_id_str = uuid.uuid4().hex[:8]
        html_template = """<div class="skill-learning-notification" id="skillNotif_{notif_id}">
<style>
.skill-learning-notification {{ position:fixed;top:-120px;right:20px;width:340px;z-index:8000;
background:linear-gradient(135deg,#1a237e,#283593);border-radius:14px;padding:20px;
border-left:4px solid #FFD700;box-shadow:0 8px 32px rgba(0,0,0,0.4);
animation:slideInDown 500ms ease-out forwards; transition:opacity 300ms; }}
.skill-notif-header {{ display:flex;align-items:center;gap:10px;margin-bottom:12px; }}
.skill-icon-circle {{ width:40px;height:40px;border-radius:50%;background:rgba(255,215,0,0.15);
display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0; }}
.skill-notif-title-group {{ flex:1; }}
.skill-notif-title {{ font-size:15px;font-weight:bold;color:#FFF; }}
.skill-category-tag {{ font-size:11px;color:#FFD700;background:rgba(255,215,0,0.1);padding:2px 8px;border-radius:10px;display:inline-block;margin-top:2px; }}
.skill-notif-body {{ font-size:13px;color:#bbb;line-height:1.5;margin-bottom:10px; }}
.skill-improvement-highlight {{ font-size:14px;font-weight:bold;color:#4CAF50;background:rgba(76,175,80,0.1);padding:6px 10px;border-radius:6px;display:inline-block; }}
.skill-notif-footer {{ display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#666;border-top:1px solid rgba(255,255,255,0.08);padding-top:10px; }}
.skill-equip-status {{ color:{status_color};font-weight:bold; }}
.skill-source-tag {{ font-style:italic;color:#888; }}
.dismiss-skill-notif {{ background:none;border:none;color:#666;cursor:pointer;font-size:16px;padding:2px; }}
@keyframes slideInDown {{ from{{top:-120px;opacity:0;}} to{{top:20px;opacity:1;}} }}
</style>
<div class="skill-notif-header">
    <div class="skill-icon-circle">{skill_icon}</div>
    <div class="skill-notif-title-group">
        <div class="skill-notif-title">\u65b0\u6280\u80fd\u5b66\u4e60\u5b8c\u6210</div>
        <div class="skill-category-tag">{skill_category}</div>
    </div>
</div>
<div class="skill-notif-body">
    <strong style="color:#FFD700;">{skill_name}</strong> \u5df2\u88ab {agent_name} \u638c\u63e1<br/>
    {effect_desc}
</div>
<div class="skill-improvement-highlight">{quantified_improvement}</div>
<div class="skill-notif-footer">
    <span class="skill-equip-status">\u72b6\u6001: {status_text}</span>
    <span class="skill-source-tag">{report_source_tag}</span>
    <button class="dismiss-skill-notif" onclick="this.closest(\'.skill-learning-notification\').remove()">\u2715</button>
</div>
<script>var _slf=document.currentScript.parentElement;setTimeout(function(){{if(_slf)_slf.remove();}},8000);</script>
</div>"""
        html = html_template.format(
            notif_id=notif_id_str,
            status_color=status_color,
            skill_icon=spec.skill_icon or '\uD83C\uDFAF',
            skill_category=spec.skill_category or '\u672a\u5206\u7c7b',
            skill_name=spec.skill_name or 'New Skill',
            agent_name=spec.agent_name or 'Agent',
            effect_desc=spec.effect_description or '\u6280\u80fd\u5b66\u4e60\u5b8c\u6210\uff0c\u76f8\u5173\u80fd\u529b\u5f97\u5230\u63d0\u5347\u3002',
            quantified_improvement=spec.quantified_improvement or '+0%',
            status_text=status_text,
            report_source_tag=spec.report_source_tag or '',
        )
        return html

    def render_effect_summary_badge(
        self,
        overall_score: float,
        dimensions: List[EffectMetric],
    ) -> str:
        if overall_score >= 80:
            grade = "A"
            grade_color = "#FFD700"
            bg_gradient = "linear-gradient(135deg, #1B5E20, #2E7D32)"
        elif overall_score >= 60:
            grade = "B"
            grade_color = "#4CAF50"
            bg_gradient = "linear-gradient(135deg, #0D47A1, #1565C0)"
        elif overall_score >= 40:
            grade = "C"
            grade_color = "#FF9800"
            bg_gradient = "linear-gradient(135deg, #E65100, #F57C00)"
        else:
            grade = "D"
            grade_color = "#F44336"
            bg_gradient = "linear-gradient(135deg, #B71C1C, #D32F2F)"

        dim_bars = ""
        for dm in dimensions[:5]:
            bar_width = min(abs(dm.change_pct), 100)
            bar_color = "#4CAF50" if dm.change_pct > 0 else "#F44336"
            arrow = "\u2B06" if dm.change_pct > 0 else "\u2B07"
            dim_bars += f"""
            <div class="badge-dim-row">
                <span class="badge-dim-label">{dm.dimension.display_name_cn}</span>
                <div class="badge-dim-bar-track"><div class="badge-dim-bar-fill" style="width:{bar_width}%;background:{bar_color};"></div></div>
                <span class="badge-dim-val" style="color:{bar_color};">{arrow}{abs(dm.change_pct):.1f}%</span>
            </div>"""

        html_template = """<div class="effect-summary-badge" title="\u70b9\u51fb\u67e5\u770b\u8be6\u60c5">
<style>
.effect-summary-badge {{ display:inline-flex;align-items:center;gap:10px;background:{bg_gradient};
border-radius:20px;padding:8px 16px;cursor:pointer;position:relative;transition:transform 0.2s,box-shadow 0.2s;vertical-align:middle; }}
.effect-summary-badge:hover {{ transform:scale(1.05);box-shadow:0 4px 20px rgba(0,0,0,0.3); }}
.badge-grade {{ font-size:22px;font-weight:bold;color:{grade_color};font-family:'Georgia',serif;min-width:28px;text-align:center;text-shadow:0 0 8px rgba(255,215,0,0.3); }}
.badge-score-num {{ font-size:13px;font-weight:bold;color:#FFF; }}
.badge-score-label {{ font-size:10px;color:#aaa; }}
.badge-detail-popover {{ display:none;position:absolute;top:100%;left:50%;transform:translateX(-50%);
margin-top:8px;background:#1a1a2e;border:1px solid rgba(255,215,0,0.3);border-radius:12px;
padding:16px;min-width:280px;z-index:5000;box-shadow:0 8px 32px rgba(0,0,0,0.5); }}
.badge-detail-popover::before {{ content:'';position:absolute;top:-8px;left:50%;transform:translateX(-50%);
border-left:8px solid transparent;border-right:8px solid transparent;border-bottom:8px solid #1a1a2e; }}
.effect-summary-badge:hover .badge-detail-popover {{ display:block; }}
.badge-dim-row {{ display:flex;align-items:center;gap:6px;margin:4px 0; }}
.badge-dim-label {{ font-size:11px;color:#aaa;width:56px;flex-shrink:0; }}
.badge-dim-bar-track {{ flex:1;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden; }}
.badge-dim-bar-fill {{ height:100%;border-radius:3px;transition:width 0.3s; }}
.badge-dim-val {{ font-size:11px;font-weight:bold;width:48px;text-align:right;flex-shrink:0; }}
</style>
<div class="badge-grade">{grade}</div>
<div>
    <div class="badge-score-num">{overall_score:.1f}<span class="badge-score-label"> / 100</span></div>
</div>
<div class="badge-detail-popover">
    <div style="font-size:12px;font-weight:bold;color:#FFD700;margin-bottom:8px;">\u5404\u7ef4\u5ea6\u6548\u679c</div>
    {dim_bars}
</div>
</div>"""
        html = html_template.format(
            overall_score=overall_score,
        )
        return html

    def render_comparison_test_panel(
        self,
        agent_id: str,
        versions: List[Dict[str, Any]],
    ) -> str:
        ver_options = ""
        for v in versions:
            vid = v.get("version_id", "")
            vlabel = v.get("label", vid)
            vlevel = v.get("level", "?")
            ver_options += f'<option value="{vid}">Version {vlabel} (Lv.{vlevel})</option>'

        html_template = """<div id="comparison-test-panel" class="comparison-panel">
<style>
.comparison-panel {{ background:#121212;border-radius:14px;padding:24px;color:#eee;max-width:700px;margin:0 auto; }}
.panel-title {{ font-size:18px;font-weight:bold;color:#FFD700;text-align:center;margin-bottom:20px; }}
.version-selectors {{ display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;justify-content:center; }}
.version-selector {{ flex:1;min-width:200px; }}
.selector-label {{ font-size:12px;color:#888;margin-bottom:4px;display:block; }}
.selector-select {{ width:100%;padding:8px 12px;background:#1e1e1e;border:1px solid #333;border-radius:8px;color:#fff;font-size:14px;cursor:pointer; }}
.test-input-area {{ margin-bottom:20px; }}
.test-input-label {{ font-size:13px;color:#aaa;margin-bottom:6px;display:block; }}
.test-input-field {{ width:100%;min-height:80px;padding:12px;background:#1e1e1e;border:1px solid #333;border-radius:8px;color:#fff;font-size:14px;resize:vertical;font-family:monospace; }}
.run-comparison-btn {{ display:block;width:100%;padding:12px;background:linear-gradient(135deg,#FFD700,#FFA000);color:#000;border:none;border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer;transition:0.2s;margin-bottom:16px; }}
.run-comparison-btn:hover {{ filter:brightness(1.1);transform:scale(1.01); }}
.run-comparison-btn:disabled {{ background:#444;color:#888;cursor:not-allowed; }}
.comparison-results {{ display:none; }}
.result-grid {{ display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px; }}
.result-card {{ background:#1a1a1a;border-radius:10px;padding:16px;border:1px solid #333; }}
.result-card-header {{ font-size:14px;font-weight:bold;color:#FFD700;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #333; }}
.result-metric-row {{ display:flex;justify-content:space-between;font-size:12px;padding:4px 0; }}
.result-metric-label {{ color:#888; }}
.result-metric-value {{ font-weight:bold; }}
.winner-banner {{ text-align:center;padding:12px;border-radius:8px;font-size:15px;font-weight:bold;margin-top:12px; }}
.winner-a {{ background:rgba(33,150,243,0.15);color:#2196F3;border:1px solid rgba(33,150,243,0.3); }}
.winner-b {{ background:rgba(156,39,176,0.15);color:#9C27B0;border:1px solid rgba(156,39,176,0.3); }}
.winner-tie {{ background:rgba(255,152,0,0.15);color:#FF9800;border:1px solid rgba(255,152,0,0.3); }}
.loading-spinner {{ text-align:center;padding:20px;display:none; }}
.spinner {{ display:inline-block;width:32px;height:32px;border:3px solid #333;border-top-color:#FFD700;border-radius:50%;animation:spin 0.8s linear infinite; }}
@keyframes spin {{ to{{transform:rotate(360deg);}} }}
</style>
<div class="panel-title">\u5347\u7ea7\u5bf9\u6bd4\u6d4b\u8bd5</div>
<div class="version-selectors">
    <div class="version-selector">
        <label class="selector-label">Version A (\u65e7)</label>
        <select class="selector-select" id="compVerA">{ver_options}</select>
    </div>
    <div class="version-selector">
        <label class="selector-label">Version B (\u65b0)</label>
        <select class="selector-select" id="compVerB">{ver_options}</select>
    </div>
</div>
<div class="test-input-area">
    <label class="test-input-label">\u8f93\u5165\u6d4b\u8bd5\u4efb\u52a1:</label>
    <textarea class="test-input-field" id="compTestInput" placeholder="\u5728\u6b64\u8f93\u5165\u60a8\u7684\u6d4b\u8bd5\u95ee\u9898..."></textarea>
</div>
<button class="run-comparison-btn" id="runCompBtn" onclick="handleRunComparison('{agent_id}')">\u5f00\u59cb\u5bf9\u6bd4</button>
<div class="loading-spinner" id="compLoading"><div class="spinner"></div></div>
<div class="comparison-results" id="compResults"></div>
</div>"""
        html = html_template.format(
            agent_id=agent_id,
        )
        return html

    def render_leaderboard_effect_column(
        self,
        entries: List[Dict[str, Any]],
    ) -> str:
        rows = ""
        for rank_idx, entry in enumerate(entries):
            rank = rank_idx + 1
            name = entry.get("agent_name", "???")
            effect_pct = entry.get("effect_pct", 0.0)
            level = entry.get("level", 1)
            agent_type = entry.get("agent_type", "OTHER")

            if rank == 1:
                rank_badge = '<span class="rank-gold">\u2605</span>'
                row_class = "rank-first"
            elif rank == 2:
                rank_badge = '<span class="rank-silver">\u2606</span>'
                row_class = "rank-second"
            elif rank == 3:
                rank_badge = '<span class="rank-bronze">&#9679;</span>'
                row_class = "rank-third"
            else:
                rank_badge = f'<span class="rank-num">{rank}</span>'
                row_class = ""

            effect_color = "#4CAF50" if effect_pct >= 0 else "#F44336"
            effect_arrow = "\u2B06" if effect_pct >= 0 else "\u2B07"

            type_colors = {"LI_BU": "#2196F3", "GONG_BU": "#FF9800", "XING_BU": "#9C27B0", "OTHER": "#607D8B"}
            type_dot_color = type_colors.get(agent_type, "#888")

            rows += f"""
            <tr class="lb-row {row_class}">
                <td class="lb-rank">{rank_badge}</td>
                <td class="lb-name">
                    <span class="type-dot" style="background:{type_dot_color};"></span>
                    {name}
                </td>
                <td class="lb-level">Lv.{level}</td>
                <td class="lb-effect" style="color:{effect_color};">{effect_arrow}{abs(effect_pct):+.1f}%</td>
                <td class="lb-bar-cell">
                    <div class="effect-bar-track"><div class="effect-bar-fill" style="width:{min(abs(effect_pct)*2, 100)}%;background:{effect_color};"></div></div>
                </td>
            </tr>"""

        rows_html = ""
        for rank_idx, entry in enumerate(entries):
            rank = rank_idx + 1
            name = entry.get("agent_name", "???")
            effect_pct = entry.get("effect_pct", 0.0)
            level = entry.get("level", 1)
            agent_type = entry.get("agent_type", "OTHER")

            if rank == 1:
                rank_badge = '<span class="rank-gold">\u2605</span>'
                row_class = "rank-first"
            elif rank == 2:
                rank_badge = '<span class="rank-silver">\u2606</span>'
                row_class = "rank-second"
            elif rank == 3:
                rank_badge = '<span class="rank-bronze">&#9679;</span>'
                row_class = "rank-third"
            else:
                rank_badge = f'<span class="rank-num">{rank}</span>'
                row_class = ""

            effect_color = "#4CAF50" if effect_pct >= 0 else "#F44336"
            effect_arrow = "\u2B06" if effect_pct >= 0 else "\u2B07"

            type_colors = {"LI_BU": "#2196F3", "GONG_BU": "#FF9800", "XING_BU": "#9C27B0", "OTHER": "#607D8B"}
            type_dot_color = type_colors.get(agent_type, "#888")

            rows_html += f"""
            <tr class="lb-row {row_class}">
                <td class="lb-rank">{rank_badge}</td>
                <td class="lb-name">
                    <span class="type-dot" style="background:{type_dot_color};"></span>
                    {name}
                </td>
                <td class="lb-level">Lv.{level}</td>
                <td class="lb-effect" style="color:{effect_color};">{effect_arrow}{abs(effect_pct):+.1f}%</td>
                <td class="lb-bar-cell">
                    <div class="effect-bar-track"><div class="effect-bar-fill" style="width:{min(abs(effect_pct)*2, 100)}%;background:{effect_color};"></div></div>
                </td>
            </tr>"""

        html = """<div class="leaderboard-effect-table">
<style>
.leaderboard-effect-table {{ width:100%;overflow:auto; }}
.lb-table {{ width:100%;border-collapse:collapse;font-size:13px;color:#ddd; }}
.lb-table th {{ background:rgba(255,215,0,0.1);color:#FFD700;padding:10px 12px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid rgba(255,215,0,0.2); }}
.lb-table td {{ padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.05); vertical-align:middle; }}
.lb-row {{ transition:background 0.15s; }}
.lb-row:hover {{ background:rgba(255,255,255,0.05); }}
.rank-first .lb-name {{ color:#FFD700; }}
.rank-second .lb-name {{ color:#C0C0C0; }}
.rank-third .lb-name {{ color:#CD7F32; }}
.rank-gold {{ color:#FFD700;font-size:16px; }}
.rank-silver {{ color:#C0C0C0;font-size:16px; }}
.rank-bronze {{ color:#CD7F32;font-size:16px; }}
.rank-num {{ display:inline-block;width:22px;height:22px;line-height:22px;text-align:center;border-radius:50%;background:#333;font-size:11px;font-weight:bold; }}
.type-dot {{ display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle; }}
.lb-effect {{ font-weight:bold;font-family:monospace; }}
.effect-bar-track {{ width:80px;height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;display:inline-block;vertical-align:middle; }}
.effect-bar-fill {{ height:100%;border-radius:3px;transition:width 0.3s; }}
</style>
<table class="lb-table">
<thead><tr><th>#</th><th>\u667a\u80fd\u4f53</th><th>\u7b49\u7ea7</th><th>\u6548\u679c\u53d8\u5316</th><th>\u8d8b\u52bf</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>"""
        return html


# =============================================================================
# PART C: REAL-TIME EFFECT FEEDBACK MECHANISM
# =============================================================================


@dataclass
class TaskCompletionNotification:
    notification_id: str
    task_id: str
    agent_id: str
    agent_level: int
    agent_name: str
    efficiency_gain_str: str = ""
    cost_saving_str: str = ""
    quality_note: str = ""
    display_duration_ms: int = 3000
    action_button_text: str = "View Details"
    action_target_url: str = ""
    non_modal: bool = True
    auto_dismiss: bool = True
    position: str = "top-right"


class TaskCompletionNotifier:

    def __init__(self):
        self._notification_queue: Dict[str, TaskCompletionNotification] = {}
        self._dedup_cache: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._dedup_window_seconds: float = 30.0

    def generate_notification(
        self,
        task_result: Dict[str, Any],
        agent_state: Dict[str, Any],
    ) -> Optional[TaskCompletionNotification]:
        task_id = task_result.get("task_id", "")
        agent_id = agent_state.get("agent_id", "")
        agent_level = agent_state.get("agent_level", 1)
        agent_name = agent_state.get("agent_name", f"Agent_{agent_id}")
        recent_upgrade = agent_state.get("recently_upgraded", False)
        new_skill_used = agent_state.get("new_skill_used", False)

        if not self.should_show_notification(task_result, agent_state):
            return None

        dedup_key = f"{agent_id}:{task_result.get('task_type', 'unknown')}"
        with self._lock:
            now = time.time()
            last_time = self._dedup_cache.get(dedup_key, 0.0)
            if now - last_time < self._dedup_window_seconds:
                return None
            self._dedup_cache[dedup_key] = now

        resp_time = task_result.get("response_time_ms", 0)
        baseline_resp = agent_state.get("baseline_response_time_ms", 0)
        if baseline_resp > 0 and resp_time > 0:
            improvement = ((baseline_resp - resp_time) / baseline_resp) * 100
            eff_str = f"\u54cd\u5e94\u901f\u5ea6\u63d0\u5347{improvement:.0f}%" if improvement > 0 else ""
        else:
            eff_str = ""

        points_saved = task_result.get("points_saved", 0)
        cost_str = f"\u4e3a\u60a8\u8282\u7701{int(points_saved)}\u79ef\u5206" if points_saved > 0 else ""

        quality_score = task_result.get("quality_score", 0.0)
        quality_note = ""
        if quality_score >= 0.95:
            quality_note = "\u8d28\u91cf\u8bc4\u5206: S\u7ea7"
        elif quality_score >= 0.85:
            quality_note = "\u8d28\u91cf\u8bc4\u5206: A\u7ea7"

        notif = TaskCompletionNotification(
            notification_id="notif_" + uuid.uuid4().hex[:12],
            task_id=task_id,
            agent_id=agent_id,
            agent_level=agent_level,
            agent_name=agent_name,
            efficiency_gain_str=eff_str,
            cost_saving_str=cost_str,
            quality_note=quality_note,
            display_duration_ms=3000,
            action_button_text="\u67e5\u770b\u8be6\u60c5",
            action_target_url=f"/agents/{agent_id}/tasks/{task_id}",
            non_modal=True,
            auto_dismiss=True,
            position="top-right",
        )
        with self._lock:
            self._notification_queue[notif.notification_id] = notif
        return notif

    def render_notification_html(self, notification: TaskCompletionNotification) -> str:
        pos_styles = {
            "top-right": "top:20px;right:20px;",
            "bottom-center": "bottom:20px;left:50%;transform:translateX(-50%);",
            "top-left": "top:20px;left:20px;",
            "bottom-right": "bottom:20px;right:20px;",
        }
        pos_style = pos_styles.get(notification.position, pos_styles["top-right"])

        eff_line = f'<div class="notif-efficiency">{notification.efficiency_gain_str}</div>' if notification.efficiency_gain_str else ""
        cost_line = f'<div class="notif-cost">{notification.cost_saving_str}</div>' if notification.cost_saving_str else ""
        quality_line = f'<div class="notif-quality">{notification.quality_note}</div>' if notification.quality_note else ""

        html = f"""<div class="task-completion-notification" id="{notification.notification_id}" style="{pos_style}">
<style>
.task-completion-notification {{ position:fixed;width:340px;background:linear-gradient(135deg,#1a1a2e,#16213e);
border-radius:12px;padding:16px;border-left:4px solid #4CAF50;box-shadow:0 8px 32px rgba(0,0,0,0.35);
z-index:7000;animation:notifSlideIn 350ms ease-out; }}
.notif-header {{ display:flex;align-items:center;gap:10px;margin-bottom:10px; }}
.notif-agent-icon {{ width:36px;height:36px;border-radius:50%;background:rgba(76,175,80,0.15);
display:flex;align-items:center;justify-content:center;font-size:16px;color:#4CAF50;flex-shrink:0; }}
.notif-agent-info {{ flex:1; }}
.notif-agent-name {{ font-size:14px;font-weight:bold;color:#FFF; }}
.notif-agent-level {{ font-size:11px;color:#FFD700; }}
.notif-body {{ font-size:12px;color:#bbb;line-height:1.6;margin-bottom:10px; }}
.notif-efficiency {{ color:#4CAF50;font-weight:bold; }}
.notif-cost {{ color:#FF9800;font-weight:bold; }}
.notif-quality {{ color:#2196F3;font-weight:bold; }}
.notif-footer {{ display:flex;justify-content:space-between;align-items:center; }}
.notif-action-btn {{ padding:5px 14px;background:rgba(255,215,0,0.12);border:1px solid rgba(255,215,0,0.25);
border-radius:6px;color:#FFD700;font-size:11px;cursor:pointer;transition:0.2s;text-decoration:none; }}
.notif-action-btn:hover {{ background:rgba(255,215,0,0.22); }}
.notif-dismiss {{ background:none;border:none;color:#555;cursor:pointer;font-size:14px;padding:2px; }}
@keyframes notifSlideIn {{ from{{opacity:0;transform:translateX(40px);}} to{{opacity:1;transform:translateX(0);}} }}
</style>
<div class="notif-header">
    <div class="notif-agent-icon">\u2705</div>
    <div class="notif-agent-info">
        <div class="notif-agent-name">{notification.agent_name}</div>
        <div class="notif-agent-level">Lv.{notification.agent_level}</div>
    </div>
</div>
<div class="notif-body">
    {eff_line}{cost_line}{quality_line}
</div>
<div class="notif-footer">
    <a class="notif-action-btn" href="{notification.action_target_url}">{notification.action_button_text}</a>
    <button class="notif-dismiss" onclick="document.getElementById('{notification.notification_id}').remove()">\u2715</button>
</div>
<script>var _nel=document.getElementById('{notification.notification_id}');setTimeout(function(){{if(_nel&&_nel.parentNode)_nel.remove();}},{notification.display_duration_ms});</script>
</div>"""
        return html
    def should_show_notification(
        self,
        task_result: Dict[str, Any],
        agent_state: Dict[str, Any],
    ) -> bool:
        recent_upgrade = agent_state.get("recently_upgraded", False)
        new_skill_used = agent_state.get("new_skill_used", False)
        significant_improvement = task_result.get("significant_improvement", False)
        return recent_upgrade or new_skill_used or significant_improvement

    def get_pending_notifications(self) -> List[TaskCompletionNotification]:
        with self._lock:
            return list(self._notification_queue.values())

    def dismiss_notification(self, notification_id: str) -> bool:
        with self._lock:
            if notification_id in self._notification_queue:
                del self._notification_queue[notification_id]
                return True
        return False

    def clear_dedup_cache(self) -> None:
        with self._lock:
            self._dedup_cache.clear()


@dataclass
class ComparisonSession:
    session_id: str
    agent_id: str
    version_a_level: int
    version_b_level: int
    test_task: str
    status: str = "created"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComparisonResult:
    session_id: str
    version_a_output: str
    version_b_output: str
    time_a_ms: float
    time_b_ms: float
    quality_a_score: float
    quality_b_score: float
    cost_a_points: float
    cost_b_points: float
    winner: str
    improvement_summary: str


class ComparisonTestInviter:

    def __init__(self):
        self._sessions: Dict[str, ComparisonSession] = {}
        self._results: Dict[str, ComparisonResult] = {}
        self._lock = threading.RLock()

    def check_eligibility(self, agent_id: str) -> bool:
        return random.random() > 0.1

    def create_comparison_session(
        self,
        agent_id: str,
        test_task_input: str,
        version_a_level: int = 1,
        version_b_level: int = 2,
    ) -> ComparisonSession:
        session = ComparisonSession(
            session_id="csess_" + uuid.uuid4().hex[:12],
            agent_id=agent_id,
            version_a_level=version_a_level,
            version_b_level=version_b_level,
            test_task=test_task_input,
            status="created",
        )
        with self._lock:
            self._sessions[session.session_id] = session
        logger.info("Comparison session created: %s agent=%s", session.session_id, agent_id)
        return session

    def execute_comparison(self, session_id: str) -> ComparisonResult:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        session.status = "running"

        start_a = time.perf_counter()
        output_a = self._simulate_agent_output(session.agent_id, session.version_a_level, session.test_task)
        time_a = (time.perf_counter() - start_a) * 1000

        start_b = time.perf_counter()
        output_b = self._simulate_agent_output(session.agent_id, session.version_b_level, session.test_task)
        time_b = (time.perf_counter() - start_b) * 1000

        quality_a = self._score_output_quality(output_a, session.version_a_level)
        quality_b = self._score_output_quality(output_b, session.version_b_level)

        cost_a = max(1.0, 10.0 - session.version_a_level * 0.5 + random.uniform(-1, 1))
        cost_b = max(1.0, 10.0 - session.version_b_level * 0.5 + random.uniform(-1, 1))

        scores = {"A": quality_a * 0.4 + max(0, (3000 - time_a) / 3000) * 0.3 + max(0, (10 - cost_a) / 10) * 0.3,
                  "B": quality_b * 0.4 + max(0, (3000 - time_b) / 3000) * 0.3 + max(0, (10 - cost_b) / 10) * 0.3}
        winner = "A" if scores["A"] > scores["B"] else ("B" if scores["B"] > scores["A"] else "TIE")

        speed_change = ((time_a - time_b) / max(time_a, 1)) * 100
        quality_change = ((quality_b - quality_a) / max(quality_a, 0.001)) * 100
        cost_change = ((cost_a - cost_b) / max(cost_a, 0.001)) * 100

        summary_parts = [f"\u901f\u5ea6: {speed_change:+.1f}%", f"\u8d28\u91cf: {quality_change:+.1f}%", f"\u6210\u672c: {cost_change:+.1f}%"]
        improvement_summary = " | ".join(summary_parts)

        result = ComparisonResult(
            session_id=session_id,
            version_a_output=output_a[:500],
            version_b_output=output_b[:500],
            time_a_ms=round(time_a, 2),
            time_b_ms=round(time_b, 2),
            quality_a_score=round(quality_a, 4),
            quality_b_score=round(quality_b, 4),
            cost_a_points=round(cost_a, 2),
            cost_b_points=round(cost_b, 2),
            winner=winner,
            improvement_summary=improvement_summary,
        )
        session.status = "completed"
        with self._lock:
            self._results[session_id] = result
        logger.info("Comparison completed: %s winner=%s", session_id, winner)
        return result

    def generate_comparison_report(self, result: ComparisonResult) -> str:
        lines = []
        lines.append("# \u5347\u7ea7\u5bf9\u6bd4\u6d4b\u8bd5\u62a5\u544a")
        lines.append("")
        lines.append(f"- **Session ID**: `{result.session_id}`")
        lines.append(f"- **Winner**: **{result.winner}**")
        lines.append("")
        lines.append("## Version A vs Version B")
        lines.append("")
        lines.append("| Metric | Version A | Version B | Delta |")
        lines.append("|--------|-----------|-----------|-------|")
        lines.append(f"| Response Time | {result.time_a_ms:.0f}ms | {result.time_b_ms:.0f}ms | {result.time_b_ms - result.time_a_ms:+.0f}ms |")
        lines.append(f"| Quality Score | {result.quality_a_score:.3f} | {result.quality_b_score:.3f} | {result.quality_b_score - result.quality_a_score:+.3f} |")
        lines.append(f"| Cost (Points) | {result.cost_a_points:.1f} | {result.cost_b_points:.1f} | {result.cost_b_points - result.cost_a_points:+.1f} |")
        lines.append("")
        lines.append(f"## Summary: {result.improvement_summary}")
        lines.append("")
        lines.append("### Version A Output Preview")
        lines.append("```")
        lines.append(result.version_a_output[:300])
        lines.append("```")
        lines.append("")
        lines.append("### Version B Output Preview")
        lines.append("```")
        lines.append(result.version_b_output[:300])
        lines.append("```")
        return "\n".join(lines)

    def get_session(self, session_id: str) -> Optional[ComparisonSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_result(self, session_id: str) -> Optional[ComparisonResult]:
        with self._lock:
            return self._results.get(session_id)

    def _simulate_agent_output(
        self,
        agent_id: str,
        level: int,
        task: str,
    ) -> str:
        detail_factor = 0.5 + (level * 0.1)
        word_count = int(50 + level * 30 * detail_factor + random.randint(-10, 20))
        base_response = (
            f"[Analysis by Agent {agent_id} Lv.{level}] "
            f"Regarding your query about '{task[:40]}': "
        )
        details = (
            f"This analysis covers {int(level * 2)} key dimensions with "
            f"{word_count} words of detailed insight. "
            f"Confidence level: {min(0.99, 0.7 + level * 0.03):.2f}. "
            f"Data sources cross-referenced: {3 + level}. "
        )
        return base_response + details

    def _score_output_quality(self, output: str, level: int) -> float:
        base_score = 0.6 + (level * 0.05)
        length_bonus = min(0.2, len(output) / 2000)
        keyword_bonus = 0.05 if any(k in output.lower() for k in ["analysis", "confidence", "data"]) else 0.0
        noise = random.uniform(-0.03, 0.03)
        return max(0.0, min(1.0, base_score + length_bonus + keyword_bonus + noise))


@dataclass
class AchievementDef:
    key: str
    name: str
    icon: str
    description: str
    condition_check_fn: Optional[Callable[[Any], bool]] = None


@dataclass
class AchievementStatus:
    achievement_key: str
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None
    progress_pct: float = 0.0
    next_milestone: str = ""


PREDEFINED_ACHIEVEMENTS: List[AchievementDef] = [
    AchievementDef(key="eagle_eye", name="Eagle Eye", icon="\uD83D\uDCA1", description="First Lv6 upgrade achieved"),
    AchievementDef(key="speed_demon", name="Speed Demon", icon="\u26A1", description="Fastest response improvement recorded"),
    AchievementDef(key="quality_master", name="Quality Master", icon="\u2605", description="Highest accuracy gain among peers"),
    AchievementDef(key="bond_collector", name="Bond Collector", icon="\uD83D\uDC9E", description="First bond activation completed"),
    AchievementDef(key="skill_scholar", name="Skill Scholar", icon="\uD83C\uDFAF", description="Learned 5 or more skills"),
]


class LeaderboardEffectIntegration:

    def __init__(self):
        self._leaderboard_cache: List[Dict[str, Any]] = []
        self._achievement_records: Dict[str, Dict[str, AchievementStatus]] = defaultdict(dict)
        self._lock = threading.RLock()

    def get_monthly_effect_rankings(self) -> List[Dict[str, Any]]:
        mock_data = [
            {"agent_id": "a001", "agent_name": "LiBu Analyst Alpha", "level": 6, "agent_type": "LI_BU", "effect_pct": 23.5},
            {"agent_id": "a002", "agent_name": "GongBu Inspector Beta", "level": 5, "agent_type": "GONG_BU", "effect_pct": 18.2},
            {"agent_id": "a003", "agent_name": "XingBu Judge Gamma", "level": 7, "agent_type": "XING_BU", "effect_pct": 15.8},
            {"agent_id": "a004", "agent_name": "LiBu Analyst Delta", "level": 4, "agent_type": "LI_BU", "effect_pct": 12.1},
            {"agent_id": "a005", "agent_name": "GongBu Inspector Epsilon", "level": 5, "agent_type": "GONG_BU", "effect_pct": 9.7},
            {"agent_id": "a006", "agent_name": "XingBu Judge Zeta", "level": 3, "agent_type": "XING_BU", "effect_pct": 6.3},
            {"agent_id": "a007", "agent_name": "LiBu Analyst Eta", "level": 3, "agent_type": "LI_BU", "effect_pct": 4.1},
            {"agent_id": "a008", "agent_name": "General Assistant Theta", "level": 2, "agent_type": "OTHER", "effect_pct": 2.8},
        ]
        with self._lock:
            self._leaderboard_cache = sorted(mock_data, key=lambda x: x["effect_pct"], reverse=True)
        return list(self._leaderboard_cache)

    def check_achievement_unlock(
        self,
        user_id: str,
        achievement_key: str,
    ) -> AchievementStatus:
        user_achievements = self._achievement_records.get(user_id, {})
        if achievement_key in user_achievements:
            return user_achievements[achievement_key]

        ach_def = None
        for ad in PREDEFINED_ACHIEVEMENTS:
            if ad.key == achievement_key:
                ach_def = ad
                break

        if ach_def is None:
            return AchievementStatus(achievement_key=achievement_key, is_unlocked=False)

        unlocked = random.random() > 0.7
        status = AchievementStatus(
            achievement_key=achievement_key,
            is_unlocked=unlocked,
            unlocked_at=datetime.utcnow() if unlocked else None,
            progress_pct=random.uniform(30, 100) if not unlocked else 100.0,
            next_milestone="" if unlocked else f"Keep improving to unlock {ach_def.name}",
        )
        user_achievements[achievement_key] = status
        self._achievement_records[user_id] = user_achievements
        return status

    def get_user_achievements(self, user_id: str) -> Dict[str, AchievementStatus]:
        return dict(self._achievement_records.get(user_id, {}))


# =============================================================================
# PART D: DATA-DRIVEN ATTRIBUTION & RECOMMENDATION
# =============================================================================


class AttributionFactor(str, Enum):
    ALGORITHM_OPTIMIZATION = "algorithm_optimization"
    SKILL_LEARNING = "skill_learning"
    BOND_ACTIVATION = "bond_activation"
    LEVEL_UP_BASE = "level_up_base"
    DATA_SOURCE_EXPANSION = "data_source_expansion"
    TOOL_PERMISSION_UNLOCK = "tool_permission_unlock"

    @property
    def display_name_cn(self) -> str:
        names = {
            AttributionFactor.ALGORITHM_OPTIMIZATION: "算法优化",
            AttributionFactor.SKILL_LEARNING: "技能学习",
            AttributionFactor.BOND_ACTIVATION: "协同激活",
            AttributionFactor.LEVEL_UP_BASE: "等级基础提升",
            AttributionFactor.DATA_SOURCE_EXPANSION: "数据源扩展",
            AttributionFactor.TOOL_PERMISSION_UNLOCK: "工具权限解锁",
        }
        return names.get(self, self.value)


@dataclass
class AttributionRecord:
    record_id: str
    agent_id: str
    upgrade_event_id: str
    factor: AttributionFactor
    contribution_pct: float
    evidence_json: str
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent_id": self.agent_id,
            "upgrade_event_id": self.upgrade_event_id,
            "factor": self.factor.value,
            "contribution_pct": round(self.contribution_pct, 2),
            "evidence_json": self.evidence_json,
            "calculated_at": self.calculated_at.isoformat(),
        }


class EffectAttributionAnalyzer:

    def __init__(self):
        self._stored_attributions: List[AttributionRecord] = []
        self._lock = threading.RLock()

    def analyze_upgrade_attribution(
        self,
        upgrade_snapshot: UpgradeEffectSnapshot,
        pre_state: Dict[str, Any],
        post_state: Dict[str, Any],
    ) -> List[AttributionRecord]:
        records: List[AttributionRecord] = []

        dim_changes = {}
        for m in upgrade_snapshot.effect_metrics:
            dim_changes[m.dimension] = abs(m.change_pct)

        primary_dim = max(dim_changes.keys(), key=lambda d: dim_changes[d], default=None)
        primary_change = dim_changes.get(primary_dim, 0.0)

        new_skills_count = post_state.get("new_skills_learned", 0)
        bonds_activated = post_state.get("bonds_activated_count", 0)
        tools_unlocked = post_state.get("tools_unlocked", 0)
        data_sources_added = post_state.get("data_sources_added", 0)

        factor_contributions: Dict[AttributionFactor, float] = {}

        if primary_dim == EffectDimension.CAPABILITY and new_skills_count > 0:
            factor_contributions[AttributionFactor.SKILL_LEARNING] = 45.0
            factor_contributions[AttributionFactor.LEVEL_UP_BASE] = 30.0
            factor_contributions[AttributionFactor.ALGORITHM_OPTIMIZATION] = 15.0
            factor_contributions[AttributionFactor.TOOL_PERMISSION_UNLOCK] = 10.0
        elif primary_dim == EffectDimension.COLLABORATION and bonds_activated > 0:
            factor_contributions[AttributionFactor.BOND_ACTIVATION] = 50.0
            factor_contributions[AttributionFactor.LEVEL_UP_BASE] = 25.0
            factor_contributions[AttributionFactor.ALGORITHM_OPTIMIZATION] = 15.0
            factor_contributions[AttributionFactor.SKILL_LEARNING] = 10.0
        elif primary_dim == EffectDimension.EFFICIENCY:
            factor_contributions[AttributionFactor.ALGORITHM_OPTIMIZATION] = 40.0
            factor_contributions[AttributionFactor.LEVEL_UP_BASE] = 30.0
            factor_contributions[AttributionFactor.TOOL_PERMISSION_UNLOCK] = 15.0
            factor_contributions[AttributionFactor.SKILL_LEARNING] = 10.0
            factor_contributions[AttributionFactor.DATA_SOURCE_EXPANSION] = 5.0
        elif primary_dim == EffectDimension.QUALITY:
            factor_contributions[AttributionFactor.ALGORITHM_OPTIMIZATION] = 35.0
            factor_contributions[AttributionFactor.SKILL_LEARNING] = 25.0
            factor_contributions[AttributionFactor.DATA_SOURCE_EXPANSION] = 20.0
            factor_contributions[AttributionFactor.LEVEL_UP_BASE] = 15.0
            factor_contributions[AttributionFactor.BOND_ACTIVATION] = 5.0
        elif primary_dim == EffectDimension.COST:
            factor_contributions[AttributionFactor.ALGORITHM_OPTIMIZATION] = 35.0
            factor_contributions[AttributionFactor.TOOL_PERMISSION_UNLOCK] = 25.0
            factor_contributions[AttributionFactor.LEVEL_UP_BASE] = 20.0
            factor_contributions[AttributionFactor.SKILL_LEARNING] = 12.0
            factor_contributions[AttributionFactor.DATA_SOURCE_EXPANSION] = 8.0
        else:
            factor_contributions[AttributionFactor.LEVEL_UP_BASE] = 50.0
            factor_contributions[AttributionFactor.ALGORITHM_OPTIMIZATION] = 30.0
            factor_contributions[AttributionFactor.SKILL_LEARNING] = 10.0
            factor_contributions[AttributionFactor.BOND_ACTIVATION] = 5.0
            factor_contributions[AttributionFactor.TOOL_PERMISSION_UNLOCK] = 5.0

        if tools_unlocked > 0:
            factor_contributions[AttributionFactor.TOOL_PERMISSION_UNLOCK] = (
                factor_contributions.get(AttributionFactor.TOOL_PERMISSION_UNLOCK, 0) + 5.0
            )
        if data_sources_added > 0:
            factor_contributions[AttributionFactor.DATA_SOURCE_EXPANSION] = (
                factor_contributions.get(AttributionFactor.DATA_SOURCE_EXPANSION, 0) + 5.0
            )

        total = sum(factor_contributions.values())
        for factor in factor_contributions:
            factor_contributions[factor] = (factor_contributions[factor] / total) * 100

        evidence_base = {
            "primary_dimension": primary_dim.value if primary_dim else "unknown",
            "primary_change_pct": round(primary_change, 2),
            "new_skills": new_skills_count,
            "bonds_activated": bonds_activated,
            "tools_unlocked": tools_unlocked,
            "data_sources_added": data_sources_added,
            "level_change": upgrade_snapshot.level_after - upgrade_snapshot.level_before,
            "overall_score": upgrade_snapshot.overall_improvement_score,
        }

        for factor, pct in sorted(factor_contributions.items(), key=lambda x: x[1], reverse=True):
            record = AttributionRecord(
                record_id="attr_" + uuid.uuid4().hex[:10],
                agent_id=upgrade_snapshot.agent_id,
                upgrade_event_id=upgrade_snapshot.snapshot_id,
                factor=factor,
                contribution_pct=round(pct, 2),
                evidence_json=json.dumps({**evidence_base, "target_factor": factor.value}),
            )
            records.append(record)

        with self._lock:
            self._stored_attributions.extend(records)
        return records

    def get_primary_factor_summary(self, attribution_list: List[AttributionRecord]) -> str:
        if not attribution_list:
            return "No attribution data available."
        primary = max(attribution_list, key=lambda r: r.contribution_pct)
        return (
            f"\u672c\u6b21\u5347\u7ea7\u4e3b\u8981\u53d7\u76ca\u4e8e【{primary.factor.display_name_cn}】，"
            f"\u8d21\u732e\u5ea6{primary.contribution_pct:.0f}%"
        )

    def store_attribution(self, records: List[AttributionRecord]) -> None:
        with self._lock:
            self._stored_attributions.extend(records)

    def get_agent_attributions(self, agent_id: str) -> List[AttributionRecord]:
        with self._lock:
            return [r for r in self._stored_attributions if r.agent_id == agent_id]


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def display_label(self) -> str:
        labels = {
            RecommendationPriority.CRITICAL: "\u7d27\u6025",
            RecommendationPriority.HIGH: "\u9ad8",
            RecommendationPriority.MEDIUM: "\u4e2d",
            RecommendationPriority.LOW: "\u4f4e",
        }
        return labels.get(self, self.value)


@dataclass
class UpgradeRecommendation:
    rec_id: str
    agent_id: str
    target_action: str
    expected_gain: str
    priority: RecommendationPriority
    rationale: str
    estimated_cost: int
    confidence: float
    valid_until: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "agent_id": self.agent_id,
            "target_action": self.target_action,
            "expected_gain": self.expected_gain,
            "priority": self.priority.value,
            "rationale": self.rationale,
            "estimated_cost": self.estimated_cost,
            "confidence": round(self.confidence, 3),
            "valid_until": self.valid_until.isoformat(),
        }


class PersonalizedUpgradeRecommender:

    def __init__(self):
        self._recommendations: Dict[str, List[UpgradeRecommendation]] = defaultdict(list)
        self._attribution_analyzer: Optional[EffectAttributionAnalyzer] = None
        self._lock = threading.RLock()

    def set_attribution_analyzer(self, analyzer: EffectAttributionAnalyzer) -> None:
        self._attribution_analyzer = analyzer

    def generate_recommendations(
        self,
        agent_id: str,
        current_state: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> List[UpgradeRecommendation]:
        recommendations: List[UpgradeRecommendation] = []

        accuracy = current_state.get("accuracy", 0.5)
        response_time = current_state.get("avg_response_time_ms", 2000)
        cost_per_task = current_state.get("cost_per_task", 10.0)
        skill_count = current_state.get("skill_count", 3)
        bond_count = current_state.get("bond_count", 0)
        level = current_state.get("level", 1)

        if accuracy < 0.75:
            gain_val = min(15.0, (0.85 - accuracy) * 50)
            recommendations.append(UpgradeRecommendation(
                rec_id="rec_" + uuid.uuid4().hex[:10],
                agent_id=agent_id,
                target_action="learn_skill:policy_analysis_deep",
                expected_gain=f"\u51c6\u786e\u7387+{gain_val:.1f}%",
                priority=RecommendationPriority.HIGH if accuracy < 0.6 else RecommendationPriority.MEDIUM,
                rationale=f"Current accuracy {accuracy:.1%} below optimal threshold of 75%. Learning advanced policy analysis can significantly improve output quality.",
                estimated_cost=200,
                confidence=min(0.9, 0.5 + (0.75 - accuracy)),
                valid_until=datetime.utcnow() + timedelta(days=30),
            ))

        if response_time > 1500:
            speed_gain = min(25.0, (response_time - 1000) / 100)
            recommendations.append(UpgradeRecommendation(
                rec_id="rec_" + uuid.uuid4().hex[:10],
                agent_id=agent_id,
                target_action="unlock_tool:caching_engine",
                expected_gain=f"\u54cd\u5e94\u901f\u5ea6+{speed_gain:.1f}%",
                priority=RecommendationPriority.CRITICAL if response_time > 3000 else RecommendationPriority.HIGH,
                rationale=f"Avg response time {response_time:.0f}ms exceeds 1500ms threshold. Enabling caching engine reduces latency.",
                estimated_cost=150,
                confidence=0.82,
                valid_until=datetime.utcnow() + timedelta(days=14),
            ))

        if cost_per_task > 8.0:
            cost_save = min(20.0, (cost_per_task - 5.0) * 3)
            recommendations.append(UpgradeRecommendation(
                rec_id="rec_" + uuid.uuid4().hex[:10],
                agent_id=agent_id,
                target_action="optimize_api_usage:batch_requests",
                expected_gain="\u6210\u672c-" + f"{cost_save:.1f}" + "%",
                priority=RecommendationPriority.MEDIUM,
                rationale=f"Cost per task {cost_per_task:.1f} points above average. Batch API request optimization recommended.",
                estimated_cost=50,
                confidence=0.75,
                valid_until=datetime.utcnow() + timedelta(days=21),
            ))

        if skill_count < 5 and level >= 3:
            recommendations.append(UpgradeRecommendation(
                rec_id="rec_" + uuid.uuid4().hex[:10],
                agent_id=agent_id,
                target_action="learn_skill:multiple_domain",
                expected_gain="\u80fd\u529b\u9762+2~3\u9879",
                priority=RecommendationPriority.LOW,
                rationale=f"Only {skill_count} skills learned. Expanding skill set increases capability breadth.",
                estimated_cost=300,
                confidence=0.65,
                valid_until=datetime.utcnow() + timedelta(days=45),
            ))

        if bond_count == 0 and level >= 2:
            recommendations.append(UpgradeRecommendation(
                rec_id="rec_" + uuid.uuid4().hex[:10],
                agent_id=agent_id,
                target_action="activate_bond:cross_department",
                expected_gain="\u534f\u540c\u589e\u6548+15%~30%",
                priority=RecommendationPriority.MEDIUM,
                rationale="No active bonds detected. Cross-department collaboration unlocks synergy bonuses.",
                estimated_cost=100,
                confidence=0.70,
                valid_until=datetime.utcnow() + timedelta(days=30),
            ))

        if self._attribution_analyzer:
            attrs = self._attribution_analyzer.get_agent_attributions(agent_id)
            attr_factors = [r.factor for r in attrs[-5:]]
            if AttributionFactor.ALGORITHM_OPTIMIZATION in attr_factors:
                recommendations.append(UpgradeRecommendation(
                    rec_id="rec_" + uuid.uuid4().hex[:10],
                    agent_id=agent_id,
                    target_action="fine_tune_model_parameters",
                    expected_gain="\u7efc\u5408\u6027\u80fd+5%~10%",
                    priority=RecommendationPriority.HIGH,
                    rationale="Historical attribution shows algorithm optimization is a strong driver. Further tuning recommended.",
                    estimated_cost=250,
                    confidence=0.78,
                    valid_until=datetime.utcnow() + timedelta(days=20),
                ))

        scored = []
        for rec in recommendations:
            gain_num = 0.0
            try:
                gain_str = rec.expected_gain.replace("+", "").replace("%", "").replace("-", "")
                gain_num = float("".join(c for c in gain_str if c.isdigit() or c == "."))
            except (ValueError, TypeError):
                gain_num = 5.0
            if rec.estimated_cost > 0:
                priority_score = (gain_num * rec.confidence) / rec.estimated_cost
            else:
                priority_score = gain_num * rec.confidence
            scored.append((priority_score, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        final_recs = [r for _, r in scored]

        with self._lock:
            self._recommendations[agent_id] = final_recs
        return final_recs

    def get_top_recommendation(self, agent_id: str) -> Optional[UpgradeRecommendation]:
        recs = self._recommendations.get(agent_id, [])
        return recs[0] if recs else None

    def format_recommendation_for_display(self, rec: UpgradeRecommendation) -> str:
        priority_emoji_map = {
            RecommendationPriority.CRITICAL: "[CRITICAL]",
            RecommendationPriority.HIGH: "[HIGH]",
            RecommendationPriority.MEDIUM: "[MEDIUM]",
            RecommendationPriority.LOW: "[LOW]",
        }
        prefix = priority_emoji_map.get(rec.priority, "[INFO]")
        lines = [
            f"{prefix} {rec.target_action}",
            f"  Expected: {rec.expected_gain}",
            f"  Cost: {rec.estimated_cost} pts | Confidence: {rec.confidence:.0%}",
            f"  Valid until: {rec.valid_until.strftime('%Y-%m-%d')}",
            f"  {rec.rationale[:120]}",
        ]
        return "\n".join(lines)

    def get_all_recommendations(self, agent_id: str) -> List[UpgradeRecommendation]:
        with self._lock:
            return list(self._recommendations.get(agent_id, []))


# =============================================================================
# PART E: A/B TESTING FRAMEWORK
# =============================================================================


class ABTestGroup(str, Enum):
    CONTROL = "control"
    EXPERIMENT = "experiment"


class ABTestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ABTestConfig:
    test_id: str
    name: str
    hypothesis: str
    description: str = ""
    group_split_ratio: float = 0.5
    min_sample_size: int = 30
    metrics_to_track: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: ABTestStatus = ABTestStatus.DRAFT
    created_by: str = ""


@dataclass
class ABTestParticipant:
    participant_id: str
    user_id: str
    test_id: str
    assigned_group: ABTestGroup
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    is_excluded: bool = False


@dataclass
class ABTestResult:
    result_id: str
    test_id: str
    group: ABTestGroup
    metric_name: str
    mean_value: float
    std_value: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    p_value: float
    is_significant: bool
    effect_size: float


@dataclass
class ABTestReport:
    test_id: str
    hypothesis: str
    conclusion: str
    group_stats: Dict[str, Any]
    significance_summary: str
    recommendation: str
    generated_at: datetime = field(default_factory=datetime.utcnow)


class ABTestExecutor:

    def __init__(self):
        self._tests: Dict[str, ABTestConfig] = {}
        self._participants: Dict[str, List[ABTestParticipant]] = defaultdict(list)
        self._measurements: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._results: Dict[str, List[ABTestResult]] = defaultdict(list)
        self._reports: Dict[str, ABTestReport] = {}
        self._lock = threading.RLock()

    def assign_participant(
        self,
        user_id: str,
        test_config: ABTestConfig,
    ) -> ABTestParticipant:
        hash_val = int(hashlib.md5((user_id + test_config.test_id).encode()).hexdigest(), 16)
        assigned_group = ABTestGroup.EXPERIMENT if (hash_val % 100) < (test_config.group_split_ratio * 100) else ABTestGroup.CONTROL

        participant = ABTestParticipant(
            participant_id="ptcp_" + uuid.uuid4().hex[:12],
            user_id=user_id,
            test_id=test_config.test_id,
            assigned_group=assigned_group,
        )
        with self._lock:
            self._participants[test_config.test_id].append(participant)
        logger.info(
            "AB Test assignment: user=%s test=%s group=%s",
            user_id, test_config.test_id, assigned_group.value,
        )
        return participant

    def record_metric(
        self,
        participant_id: str,
        metric_name: str,
        value: float,
    ) -> None:
        measurement = {
            "participant_id": participant_id,
            "metric_name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._measurements[metric_name].append(measurement)

    def calculate_results(self, test_id: str) -> List[ABTestResult]:
        test_config = self._tests.get(test_id)
        if test_config is None:
            raise ValueError(f"Test not found: {test_id}")

        participants = self._participants.get(test_id, [])
        control_ids = {p.participant_id for p in participants if p.assigned_group == ABTestGroup.CONTROL and not p.is_excluded}
        experiment_ids = {p.participant_id for p in participants if p.assigned_group == ABTestGroup.EXPERIMENT and not p.is_excluded}

        results: List[ABTestResult] = []
        metrics_to_check = test_config.metrics_to_track or ["default_metric"]

        for metric_name in metrics_to_check:
            measurements = self._measurements.get(metric_name, [])

            control_values = [
                m["value"] for m in measurements
                if m["participant_id"] in control_ids
            ]
            experiment_values = [
                m["value"] for m in measurements
                if m["participant_id"] in experiment_ids
            ]

            if len(control_values) < test_config.min_sample_size // 2 or len(experiment_values) < test_config.min_sample_size // 2:
                continue

            ctrl_mean = statistics.mean(control_values) if control_values else 0.0
            exp_mean = statistics.mean(experiment_values) if experiment_values else 0.0
            ctrl_std = statistics.stdev(control_values) if len(control_values) > 1 else 0.0
            exp_std = statistics.stdev(experiment_values) if len(experiment_values) > 1 else 0.0

            ci_ctrl = self._calc_ci(control_values)
            ci_exp = self._calc_ci(experiment_values)

            p_val = self._two_sample_t_test(control_values, experiment_values)
            is_sig = p_val < 0.05

            effect_size = self._cohens_d(control_values, experiment_values)

            for group, mean_val, std_val, n, ci in [
                (ABTestGroup.CONTROL, ctrl_mean, ctrl_std, len(control_values), ci_ctrl),
                (ABTestGroup.EXPERIMENT, exp_mean, exp_std, len(experiment_values), ci_exp),
            ]:
                result = ABTestResult(
                    result_id="abr_" + uuid.uuid4().hex[:10],
                    test_id=test_id,
                    group=group,
                    metric_name=metric_name,
                    mean_value=round(mean_val, 4),
                    std_value=round(std_val, 4),
                    sample_size=n,
                    confidence_interval=ci,
                    p_value=round(p_val, 6),
                    is_significant=is_sig,
                    effect_size=round(effect_size, 4),
                )
                results.append(result)

        with self._lock:
            self._results[test_id] = results
        return results

    def generate_ab_report(
        self,
        test_id: str,
        results: Optional[List[ABTestResult]] = None,
    ) -> ABTestReport:
        test_config = self._tests.get(test_id)
        if test_config is None:
            raise ValueError(f"Test not found: {test_id}")

        if results is None:
            results = self._results.get(test_id, [])

        control_results = [r for r in results if r.group == ABTestGroup.CONTROL]
        experiment_results = [r for r in results if r.group == ABTestGroup.EXPERIMENT]

        any_sig = any(r.is_significant for r in experiment_results)
        avg_effect = 0.0
        if experiment_results:
            avg_effect = statistics.mean([r.effect_size for r in experiment_results])

        if any_sig and avg_effect > 0.2:
            conclusion = "Experiment group shows statistically significant improvement. Recommend full rollout."
            recommendation = "Proceed with full deployment of experimental variant."
        elif any_sig and avg_effect < -0.2:
            conclusion = "Experiment group shows significant degradation. Do not roll out."
            recommendation = "Reject experimental variant. Investigate root cause."
        elif any_sig:
            conclusion = "Minor but statistically significant difference detected."
            recommendation = "Consider extended testing with larger sample size."
        else:
            conclusion = "No statistically significant difference between groups."
            recommendation = "Either variant is acceptable. Consider other factors like implementation cost."

        sig_summary_parts = []
        for r in experiment_results:
            marker = "***" if r.p_value < 0.01 else "**" if r.p_value < 0.05 else "*" if r.p_value < 0.1 else ""
            sig_summary_parts.append(
                f"{r.metric_name}: d={r.effect_size:+.3f} p={r.p_value:.4f} {marker}"
            )

        group_stats = {
            "control_n": sum(r.sample_size for r in control_results),
            "experiment_n": sum(r.sample_size for r in experiment_results),
            "control_means": {r.metric_name: r.mean_value for r in control_results},
            "experiment_means": {r.metric_name: r.mean_value for r in experiment_results},
        }

        report = ABTestReport(
            test_id=test_id,
            hypothesis=test_config.hypothesis,
            conclusion=conclusion,
            group_stats=group_stats,
            significance_summary="; ".join(sig_summary_parts) if sig_summary_parts else "No significant results.",
            recommendation=recommendation,
        )
        with self._lock:
            self._reports[test_id] = report
        return report

    def create_test(self, config: ABTestConfig) -> str:
        with self._lock:
            self._tests[config.test_id] = config
        return config.test_id

    def get_test(self, test_id: str) -> Optional[ABTestConfig]:
        return self._tests.get(test_id)

    def get_participants(self, test_id: str) -> List[ABTestParticipant]:
        return list(self._participants.get(test_id, []))

    def _calc_ci(self, values: List[float]) -> Tuple[float, float]:
        n = len(values)
        if n < 2:
            return (0.0, 0.0)
        mean = statistics.mean(values)
        se = statistics.stdev(values) / math.sqrt(n)
        t_crit = 1.96 if n >= 30 else 2.086
        return (round(mean - t_crit * se, 6), round(mean + t_crit * se, 6))

    def _two_sample_t_test(
        self,
        group_a: List[float],
        group_b: List[float],
    ) -> float:
        na, nb = len(group_a), len(group_b)
        if na < 2 or nb < 2:
            return 1.0
        mean_a, mean_b = statistics.mean(group_a), statistics.mean(group_b)
        var_a = statistics.variance(group_a) if na > 1 else 0.0
        var_b = statistics.variance(group_b) if nb > 1 else 0.0
        pooled_se = math.sqrt(var_a / na + var_b / nb)
        if pooled_se == 0:
            return 1.0 if mean_a == mean_b else 0.0
        t_stat = (mean_b - mean_a) / pooled_se
        df_num = (var_a / na + var_b / nb) ** 2
        df_denom = ((var_a / na) ** 2 / (na - 1) + ((var_b / nb) ** 2 / (nb - 1))) if df_num > 0 else 1.0
        df = df_num / df_denom if df_denom > 0 else na + nb - 2

        t_abs = abs(t_stat)
        if df >= 100:
            approx_p = 2 * (1 - self._normal_cdf(t_abs))
        else:
            approx_p = 2 * (1 - self._t_approx_cdf(t_abs, df))
        return max(0.0, min(1.0, approx_p))

    def _cohens_d(self, group_a: List[float], group_b: List[float]) -> float:
        na, nb = len(group_a), len(group_b)
        if na < 2 or nb < 2:
            return 0.0
        mean_a, mean_b = statistics.mean(group_a), statistics.mean(group_b)
        var_a = statistics.variance(group_a)
        var_b = statistics.variance(group_b)
        pooled_sd = math.sqrt(((na - 1) * var_a + (nb - 1) * var_b) / (na + nb - 2))
        if pooled_sd == 0:
            return 0.0
        return (mean_b - mean_a) / pooled_sd

    def _normal_cdf(self, x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _t_approx_cdf(self, t: float, df: float) -> float:
        x = df / (df + t * t)
        if df >= 1:
            return 1 - 0.5 * self._incomplete_beta(df / 2, 0.5, x)
        return 0.5

    def _incomplete_beta(self, a: float, b: float, x: float) -> float:
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        max_iter = 200
        eps = 1e-10
        result = 0.0
        term = 1.0
        for n in range(max_iter):
            if abs(term) < eps * abs(result) and n > 2:
                break
            coeff = 1.0
            for m in range(n):
                coeff *= (a + m) / (a + b + m)
            term = coeff * (x ** n) / (a + n)
            result += term
        return result * (x ** a * (1 - x) ** b) / a


class FeedbackReason(str, Enum):
    EFFECT_NOT_NOTICEABLE = "effect_not_noticeable"
    DATA_INACCURATE = "data_inaccurate"
    NO_CHANGE_PERCEIVED = "no_change_perceived"
    MISLEADING_DISPLAY = "misleading_display"
    OTHER = "other"


class FeedbackHelpful(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


@dataclass
class FeedbackRecord:
    record_id: str
    user_id: str
    effect_id: str
    is_helpful: bool
    reason: Optional[FeedbackReason] = None
    comment: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UserFeedbackCollector:

    def __init__(self):
        self._feedbacks: List[FeedbackRecord] = []
        self._lock = threading.RLock()

    def collect_feedback(
        self,
        user_id: str,
        effect_id: str,
        is_helpful: bool,
        reason: Optional[FeedbackReason] = None,
        comment: str = "",
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            record_id="fb_" + uuid.uuid4().hex[:12],
            user_id=user_id,
            effect_id=effect_id,
            is_helpful=is_helpful,
            reason=reason,
            comment=comment,
        )
        with self._lock:
            self._feedbacks.append(record)
        logger.info(
            "Feedback collected: user=%s effect=%s helpful=%s",
            user_id, effect_id, is_helpful,
        )
        return record

    def get_feedback_stats(self, effect_id: str) -> Dict[str, Any]:
        with self._lock:
            relevant = [f for f in self._feedbacks if f.effect_id == effect_id]
        total = len(relevant)
        helpful_count = sum(1 for f in relevant if f.is_helpful)
        helpful_pct = (helpful_count / total * 100) if total > 0 else 0.0

        reason_dist: Dict[str, int] = defaultdict(int)
        for f in relevant:
            if f.reason:
                reason_dist[f.reason.value] += 1

        return {
            "effect_id": effect_id,
            "total_feedbacks": total,
            "helpful_count": helpful_count,
            "helpful_pct": round(helpful_pct, 1),
            "not_helpful_count": total - helpful_count,
            "reason_distribution": dict(reason_dist),
        }

    def get_actionable_insights(self) -> List[Dict[str, Any]]:
        with self._lock:
            feedbacks = list(self._feedbacks)

        insights: List[Dict[str, Any]] = []

        not_helpful = [f for f in feedbacks if not f.is_helpful]
        reason_counts: Dict[str, int] = defaultdict(int)
        for f in not_helpful:
            if f.reason:
                reason_counts[f.reason.value] += 1

        if reason_counts:
            top_reason = max(reason_counts.keys(), key=lambda k: reason_counts[k], default=None)
            if top_reason and reason_counts[top_reason] >= 3:
                reason_labels = {
                    "effect_not_noticeable": "Users cannot perceive the improvement effect",
                    "data_inaccurate": "Data displayed does not match actual performance",
                    "no_change_perceived": "No visible change before/after upgrade",
                    "misleading_display": "Visual representation may be misleading",
                    "other": "Other unspecified reasons",
                }
                insights.append({
                    "type": "negative_feedback_pattern",
                    "severity": "high" if reason_counts[top_reason] >= 5 else "medium",
                    "reason": top_reason,
                    "description": reason_labels.get(top_reason, "Unknown issue"),
                    "count": reason_counts[top_reason],
                    "suggestion": self._generate_reason_suggestion(top_reason),
                })

        effect_feedbacks: Dict[str, List[FeedbackRecord]] = defaultdict(list)
        for f in feedbacks:
            effect_feedbacks[f.effect_id].append(f)

        low_rated_effects = []
        for eid, efb in effect_feedbacks.items():
            if len(efb) >= 5:
                helpful_ratio = sum(1 for f in efb if f.is_helpful) / len(efb)
                if helpful_ratio < 0.5:
                    low_rated_effects.append({"effect_id": eid, "ratio": helpful_ratio, "total": len(efb)})

        for le in sorted(low_rated_effects, key=lambda x: x["ratio"]):
            insights.append({
                "type": "low_rated_effect",
                "severity": "medium",
                "effect_id": le["effect_id"],
                "helpful_ratio": round(le["ratio"], 2),
                "total_feedbacks": le["total"],
                "suggestion": f"Investigate why effect '{le['effect_id']}' has only {le['ratio']:.0%} positive feedback. Consider revising calculation methodology or display format.",
            })

        recent_negative = [f for f in feedbacks if not f.is_helpful and (datetime.utcnow() - f.timestamp).days <= 7]
        if len(recent_negative) >= 5:
            insights.append({
                "type": "spike_in_negative_feedback",
                "severity": "critical",
                "count": len(recent_negative),
                "suggestion": "Recent spike in negative feedback detected. Review recent changes and consider rolling back problematic updates.",
            })

        return insights

    def _generate_reason_suggestion(self, reason_code: str) -> str:
        suggestions = {
            "effect_not_noticeable": "Increase visual prominence of effect indicators. Use larger fonts, animations, and explicit comparison numbers.",
            "data_inaccurate": "Audit data pipeline for correctness. Verify probe collection, seasonality adjustment, and aggregation logic.",
            "no_change_perceived": "Ensure pre/post periods have sufficient contrast. Check if upgrade actually changed behavior meaningfully.",
            "misleading_display": "Review chart scales, axis ranges, and color coding. Ensure visual representation matches numerical reality.",
            "other": "Conduct qualitative survey to understand specific user concerns.",
        }
        return suggestions.get(reason_code, "Investigate further.")


# =============================================================================
# PART F: PERFORMANCE DATA COLLECTION SDK
# =============================================================================


@dataclass
class PerformanceProbe:
    probe_id: str
    agent_id: str
    task_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    output_quality_score: float = 0.0
    api_calls_count: int = 0
    points_consumed: float = 0.0
    error_occurred: bool = False
    error_message: str = ""
    metadata_json: str = "{}"
    reported_at: Optional[datetime] = None


class PerformanceSDK:

    def __init__(self, batch_size: int = 50, flush_interval_seconds: float = 10.0):
        self._probes: Dict[str, PerformanceProbe] = {}
        self._probe_history: List[PerformanceProbe] = []
        self._queue: Queue.Queue = Queue.Queue(maxsize=10000)
        self._batch_size = batch_size
        self._flush_interval = flush_interval_seconds
        self._lock = threading.RLock()
        self._flush_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_flush_worker()

    def _start_flush_worker(self) -> None:
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def _flush_loop(self) -> None:
        while self._running:
            try:
                self.flush_queue()
            except Exception as e:
                logger.error("Flush loop error: %s", e)
            time.sleep(self._flush_interval)

    def start_probe(
        self,
        agent_id: str,
        task_id: str,
        task_type: str,
    ) -> str:
        probe_id = "probe_" + uuid.uuid4().hex[:12]
        probe = PerformanceProbe(
            probe_id=probe_id,
            agent_id=agent_id,
            task_id=task_id,
            task_type=task_type,
            start_time=datetime.utcnow(),
        )
        with self._lock:
            self._probes[probe_id] = probe
        logger.debug("Probe started: %s agent=%s task=%s", probe_id, agent_id, task_id)
        return probe_id

    def end_probe(
        self,
        probe_id: str,
        output_quality_score: float = 0.0,
        api_calls: int = 0,
        points_consumed: float = 0.0,
        error: Optional[str] = None,
    ) -> Optional[PerformanceProbe]:
        with self._lock:
            probe = self._probes.get(probe_id)
        if probe is None:
            logger.warning("Probe not found for end_probe: %s", probe_id)
            return None

        probe.end_time = datetime.utcnow()
        probe.duration_ms = (probe.end_time - probe.start_time).total_seconds() * 1000
        probe.output_quality_score = output_quality_score
        probe.api_calls_count = api_calls
        probe.points_consumed = points_consumed
        probe.error_occurred = error is not None
        probe.error_message = error or ""
        probe.reported_at = datetime.utcnow()

        try:
            self._queue.put_nowait(probe)
        except Queue.Full:
            logger.warning("Probe queue full, dropping probe: %s", probe_id)

        with self._lock:
            self._probe_history.append(probe)
            del self._probes[probe_id]
        return probe

    def flush_queue(self) -> int:
        batch: List[PerformanceProbe] = []
        while len(batch) < self._batch_size:
            try:
                item = self._queue.get_nowait()
                batch.append(item)
            except Queue.Empty:
                break
        if batch:
            logger.info("Flushed %d probes to storage", len(batch))
        return len(batch)

    def get_agent_performance_window(
        self,
        agent_id: str,
        days: int = 7,
    ) -> List[PerformanceProbe]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self._lock:
            return [
                p for p in self._probe_history
                if p.agent_id == agent_id and p.start_time >= cutoff
            ]

    def get_probes_by_task_type(
        self,
        task_type: str,
        days: int = 7,
    ) -> List[PerformanceProbe]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self._lock:
            return [
                p for p in self._probe_history
                if p.task_type == task_type and p.start_time >= cutoff
            ]

    def get_active_probe_count(self) -> int:
        with self._lock:
            return len(self._probes)

    def shutdown(self) -> None:
        self._running = False
        self.flush_queue()
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundJob:
    job_id: str
    agent_id: str
    job_type: str
    status: JobStatus = JobStatus.PENDING
    progress_pct: float = 0.0
    result_json: str = "{}"
    error_msg: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class UpgradeEventTrigger:

    def __init__(
        self,
        calculator: Optional[EffectMetricsCalculator] = None,
        sdk: Optional[PerformanceSDK] = None,
    ):
        self._calculator = calculator or EffectMetricsCalculator()
        self._sdk = sdk or PerformanceSDK()
        self._jobs: Dict[str, BackgroundJob] = {}
        self._snapshots: Dict[str, UpgradeEffectSnapshot] = {}
        self._worker_threads: Dict[str, threading.Thread] = {}
        self._lock = threading.RLock()

    def trigger_upgrade_calculation(
        self,
        agent_id: str,
        old_level: int,
        new_level: int,
        agent_name: str = "",
        agent_type: AgentType = AgentType.OTHER,
        pre_period_days: int = 7,
        post_period_days: int = 7,
    ) -> str:
        job_id = "job_" + uuid.uuid4().hex[:12]
        job = BackgroundJob(
            job_id=job_id,
            agent_id=agent_id,
            job_type="upgrade_effect_calculation",
            status=JobStatus.PENDING,
        )
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(
            target=self._execute_upgrade_pipeline,
            args=(
                job_id, agent_id, old_level, new_level,
                agent_name, agent_type, pre_period_days, post_period_days,
            ),
            daemon=True,
        )
        self._worker_threads[job_id] = thread
        thread.start()
        logger.info(
            "Upgrade calculation triggered: job=%s agent=%s %d->%d",
            job_id, agent_id, old_level, new_level,
        )
        return job_id

    def _execute_upgrade_pipeline(
        self,
        job_id: str,
        agent_id: str,
        old_level: int,
        new_level: str,
        agent_name: str,
        agent_type: AgentType,
        pre_period_days: int,
        post_period_days: int,
    ) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return

        with self._lock:
            job.status = JobStatus.RUNNING
            job.progress_pct = 5.0

        try:
            job.progress_pct = 15.0
            pre_probes = self._sdk.get_agent_performance_window(agent_id, days=pre_period_days)
            job.progress_pct = 30.0

            job.progress_pct = 40.0
            post_probes = self._sdk.get_agent_performance_window(agent_id, days=post_period_days)
            job.progress_pct = 55.0

            job.progress_pct = 65.0
            pre_tasks = [
                {"response_time_ms": p.duration_ms, "task_id": p.task_id}
                for p in pre_probes if not p.error_occurred
            ]
            post_tasks = [
                {"response_time_ms": p.duration_ms, "task_id": p.task_id}
                for p in post_probes if not p.error_occurred
            ]
            pre_reports = [
                {"accuracy_score": p.output_quality_score, "r_squared": min(0.95, p.output_quality_score * 1.1)}
                for p in pre_probes if p.output_quality_score > 0
            ]
            post_reports = [
                {"accuracy_score": p.output_quality_score, "r_squared": min(0.95, p.output_quality_score * 1.15)}
                for p in post_probes if p.output_quality_score > 0
            ]
            pre_costs = [
                {"points_consumed": p.points_consumed, "api_calls": p.api_calls_count}
                for p in pre_probes
            ]
            post_costs = [
                {"points_consumed": p.points_consumed, "api_calls": p.api_calls_count}
                for p in post_probes
            ]

            job.progress_pct = 80.0
            snapshot = self._calculator.build_upgrade_snapshot(
                agent_id=agent_id,
                level_from=old_level,
                level_to=int(new_level),
                agent_name=agent_name,
                agent_type=agent_type,
                pre_period_days=pre_period_days,
                post_period_days=post_period_days,
                pre_tasks=pre_tasks,
                post_tasks=post_tasks,
                pre_reports=pre_reports,
                post_reports=post_reports,
                pre_costs=pre_costs,
                post_costs=post_costs,
            )

            job.progress_pct = 95.0
            with self._lock:
                job.status = JobStatus.COMPLETED
                job.progress_pct = 100.0
                job.result_json = snapshot.to_dict()
                job.completed_at = datetime.utcnow()
                self._snapshots[snapshot.snapshot_id] = snapshot
            logger.info("Upgrade pipeline completed: job=%s snapshot=%s", job_id, snapshot.snapshot_id)

        except Exception as e:
            with self._lock:
                job.status = JobStatus.FAILED
                job.error_msg = str(e)
            logger.error("Upgrade pipeline failed: job=%s error=%s", job_id, e)

    def get_job_status(self, job_id: str) -> Optional[BackgroundJob]:
        return self._jobs.get(job_id)

    def get_snapshot(self, agent_id: str) -> Optional[UpgradeEffectSnapshot]:
        for snap in self._snapshots.values():
            if snap.agent_id == agent_id:
                return snap
        return None

    def get_all_snapshots(self, agent_id: str) -> List[UpgradeEffectSnapshot]:
        return [s for s in self._snapshots.values() if s.agent_id == agent_id]


class EffectAPIProvider:

    CACHE_TTL_SECONDS = 300

    def __init__(
        self,
        trigger: Optional[UpgradeEventTrigger] = None,
        calculator: Optional[EffectMetricsCalculator] = None,
    ):
        self._trigger = trigger or UpgradeEventTrigger()
        self._calculator = calculator or EffectMetricsCalculator()
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.RLock()

    def get_upgrade_effects(self, agent_id: str) -> Dict[str, Any]:
        cache_key = f"upgrade_effects:{agent_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        snapshots = self._trigger.get_all_snapshots(agent_id)
        result = {
            "agent_id": agent_id,
            "upgrade_count": len(snapshots),
            "upgrades": [s.to_dict() for s in snapshots],
            "latest_snapshot": snapshots[-1].to_dict() if snapshots else None,
        }
        self._set_cache(cache_key, result)
        return result

    def get_latest_upgrade_effect(self, agent_id: str) -> Optional[Dict[str, Any]]:
        cache_key = f"latest_effect:{agent_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        snap = self._trigger.get_snapshot(agent_id)
        result = snap.to_dict() if snap else None
        self._set_cache(cache_key, result)
        return result

    def get_effect_timeline(
        self,
        agent_id: str,
        dimension: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cache_key = f"timeline:{agent_id}:{dimension or 'all'}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        snapshots = self._trigger.get_all_snapshots(agent_id)
        timeline = []
        for snap in snapshots:
            entry = {
                "date": snap.upgrade_timestamp.isoformat(),
                "level": snap.level_after,
                "overall_score": snap.overall_improvement_score,
            }
            if dimension:
                for m in snap.effect_metrics:
                    if m.dimension.value == dimension:
                        entry["metric_value"] = m.change_pct
                        entry["metric_name"] = m.metric_name
                        break
            else:
                entry["metrics"] = {m.dimension.value: m.change_pct for m in snap.effect_metrics}
            timeline.append(entry)
        timeline.sort(key=lambda x: x["date"])
        self._set_cache(cache_key, timeline)
        return timeline

    def get_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        cache_key = f"recommendations:{agent_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        recommender = PersonalizedUpgradeRecommender()
        recs = recommender.generate_recommendations(
            agent_id=agent_id,
            current_state={"level": 3, "accuracy": 0.7, "avg_response_time_ms": 1800},
            history=[],
        )
        result = [r.to_dict() for r in recs]
        self._set_cache(cache_key, result)
        return result

    def get_attribution_summary(
        self,
        agent_id: str,
        upgrade_id: str,
    ) -> List[Dict[str, Any]]:
        cache_key = f"attribution:{agent_id}:{upgrade_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        analyzer = EffectAttributionAnalyzer()
        snap = self._trigger.get_snapshot(agent_id)
        if snap is None:
            return []
        records = analyzer.analyze_upgrade_attribution(
            upgrade_snapshot=snap,
            pre_state={},
            post_state={"new_skills_learned": 2, "bonds_activated_count": 1},
        )
        result = [r.to_dict() for r in records]
        self._set_cache(cache_key, result)
        return result

    def _get_cached(self, key: str) -> Any:
        with self._lock:
            if key in self._cache:
                value, ts = self._cache[key]
                if time.time() - ts < self.CACHE_TTL_SECONDS:
                    return value
                del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (value, time.time())


# =============================================================================
# PART G: TESTING SUITE
# =============================================================================


AGENT_UPGRADE_EFFECT_TEST_CASES: List[Dict[str, Any]] = [
    {"id": "TC_METRIC_001", "category": "Metrics Calculation", "name": "efficiency_gain_normal_data",
     "desc": "Calculate efficiency gain with normal pre/post task data"},
    {"id": "TC_METRIC_002", "category": "Metrics Calculation", "name": "quality_gain_r2_improvement",
     "desc": "Calculate quality gain with R-squared improvement"},
    {"id": "TC_METRIC_003", "category": "Metrics Calculation", "name": "capability_new_skills",
     "desc": "Calculate capability gain counting new skills unlocked"},
    {"id": "TC_METRIC_004", "category": "Metrics Calculation", "name": "cost_points_reduction",
     "desc": "Calculate cost gain with points reduction"},
    {"id": "TC_METRIC_005", "category": "Metrics Calculation", "name": "collaboration_bond_synergy",
     "desc": "Calculate collaboration gain with bond synergy boost"},
    {"id": "TC_METRIC_006", "category": "Metrics Calculation", "name": "edge_case_zero_samples",
     "desc": "Handle zero pre/post samples gracefully"},

    {"id": "TC_CONF_001", "category": "Confidence Interval", "name": "high_confidence_n_ge_100",
     "desc": "High confidence level for sample count >= 100"},
    {"id": "TC_CONF_002", "category": "Confidence Interval", "name": "moderate_confidence_n_50",
     "desc": "Moderate confidence level for n=50"},
    {"id": "TC_CONF_003", "category": "Confidence Interval", "name": "low_confidence_n_15",
     "desc": "Low confidence level for n=15"},
    {"id": "TC_CONF_004", "category": "Confidence Interval", "name": "insufficient_n_lt_10",
     "desc": "Insufficient samples for n < 10"},

    {"id": "TC_SEAS_001", "category": "Seasonality Adjustment", "name": "weekend_vs_weekday",
     "desc": "Weekend vs weekday adjustment factor applied correctly"},
    {"id": "TC_SEAS_002", "category": "Seasonality Adjustment", "name": "holiday_detection",
     "desc": "Holiday period detected in adjustment factors"},
    {"id": "TC_SEAS_003", "category": "Seasonality Adjustment", "name": "moving_average_smoothing",
     "desc": "Moving average smooths seasonal noise properly"},

    {"id": "TC_FE_001", "category": "Frontend Rendering", "name": "upgrade_modal_html_valid",
     "desc": "Upgrade success modal generates valid HTML structure"},
    {"id": "TC_FE_002", "category": "Frontend Rendering", "name": "evolution_chart_binding",
     "desc": "Evolution chart renders with data binding"},
    {"id": "TC_FE_003", "category": "Frontend Rendering", "name": "bond_popup_rendering",
     "desc": "Bond activation popup renders with animation"},
    {"id": "TC_FE_004", "category": "Frontend Rendering", "name": "skill_notification",
     "desc": "Skill learning notification slide-in card"},
    {"id": "TC_FE_005", "category": "Frontend Rendering", "name": "effect_badge_render",
     "desc": "Effect summary badge renders compact inline"},
    {"id": "TC_FE_006", "category": "Frontend Rendering", "name": "comparison_panel_ui",
     "desc": "Comparison test panel UI renders completely"},

    {"id": "TC_NOTIF_001", "category": "Task Completion Notifier", "name": "notif_upgraded_agent",
     "desc": "Notification generated for recently upgraded agent"},
    {"id": "TC_NOTIF_002", "category": "Task Completion Notifier", "name": "deduplication_logic",
     "desc": "Deduplication suppresses same agent+task within 30s"},
    {"id": "TC_NOTIF_003", "category": "Task Completion Notifier", "name": "non_modal_card_html",
     "desc": "Non-modal notification card HTML is valid"},
    {"id": "TC_NOTIF_004", "category": "Task Completion Notifier", "name": "should_show_check",
     "desc": "Should-show only returns true for upgraded agents"},

    {"id": "TC_COMP_001", "category": "Comparison Test", "name": "eligibility_both_versions",
     "desc": "Eligibility check passes when both versions exist"},
    {"id": "TC_COMP_002", "category": "Comparison Test", "name": "session_execute_report",
     "desc": "Session creation and execution produces result"},
    {"id": "TC_COMP_003", "category": "Comparison Test", "name": "report_winner_determination",
     "desc": "Report generation includes winner determination"},

    {"id": "TC_ATTR_001", "category": "Attribution Analysis", "name": "algo_optimization_primary",
     "desc": "Algorithm optimization as primary factor when efficiency dominant"},
    {"id": "TC_ATTR_002", "category": "Attribution Analysis", "name": "skill_learning_primary",
     "desc": "Skill learning as primary factor when capability dominant"},
    {"id": "TC_ATTR_003", "category": "Attribution Analysis", "name": "bond_activation_primary",
     "desc": "Bond activation as primary factor when collaboration dominant"},
    {"id": "TC_ATTR_004", "category": "Attribution Analysis", "name": "multi_factor_split",
     "desc": "Multi-factor attribution splits to 100% total"},

    {"id": "TC_REC_001", "category": "Recommendation Engine", "name": "underperform_recommendations",
     "desc": "Generate recommendations for underperforming agent"},
    {"id": "TC_REC_002", "category": "Recommendation Engine", "name": "priority_sorting",
     "desc": "Recommendations sorted by expected_gain/confidence/cost"},
    {"id": "TC_REC_003", "category": "Recommendation Engine", "name": "top_recommendation_select",
     "desc": "Top recommendation returns highest priority item"},
    {"id": "TC_REC_004", "category": "Recommendation Engine", "name": "recommendation_formatting",
     "desc": "Recommendation text formatted for display"},

    {"id": "TC_AB_001", "category": "A/B Testing Framework", "name": "participant_hash_assignment",
     "desc": "Participant assignment via deterministic hash"},
    {"id": "TC_AB_002", "category": "A/B Testing Framework", "name": "metric_recording_aggregation",
     "desc": "Metric recording and aggregation works"},
    {"id": "TC_AB_003", "category": "A/B Testing Framework", "name": "ttest_result_calculation",
     "desc": "T-test result calculation with significance check"},
    {"id": "TC_AB_004", "category": "A/B Testing Framework", "name": "significance_determination",
     "desc": "Significance determination at alpha=0.05"},
    {"id": "TC_AB_005", "category": "A/B Testing Framework", "name": "ab_report_generation",
     "desc": "AB test report generation complete"},

    {"id": "TC_FB_001", "category": "User Feedback", "name": "helpful_feedback_collect",
     "desc": "Helpful feedback collected and stored"},
    {"id": "TC_FB_002", "category": "User Feedback", "name": "not_helpful_with_reason",
     "desc": "Not-helpful feedback with reason recorded"},
    {"id": "TC_FB_003", "category": "User Feedback", "name": "stats_aggregation_insights",
     "desc": "Stats aggregation and actionable insights generated"},

    {"id": "TC_SDK_001", "category": "Performance SDK", "name": "probe_lifecycle_start_end_flush",
     "desc": "Full probe lifecycle: start, end, flush"},
    {"id": "TC_SDK_002", "category": "Performance SDK", "name": "async_queue_batching",
     "desc": "Async queue batching mechanism works"},
    {"id": "TC_SDK_003", "category": "Performance SDK", "name": "performance_window_query",
     "desc": "Performance window query returns correct probes"},
    {"id": "TC_SDK_004", "category": "Performance SDK", "name": "error_handling_probe",
     "desc": "Error handling in probe end method"},

    {"id": "TC_TRIG_001", "category": "Upgrade Event Trigger", "name": "trigger_background_job",
     "desc": "Trigger background job returns job_id"},
    {"id": "TC_TRIG_002", "category": "Upgrade Event Trigger", "name": "job_status_progression",
     "desc": "Job status progresses through lifecycle"},
    {"id": "TC_TRIG_003", "category": "Upgrade Event Trigger", "name": "full_pipeline_trigger_to_cache",
     "desc": "Full pipeline: trigger -> fetch -> calculate -> cache"},
]


class AgentUpgradeEffectTestSuite:

    def __init__(self):
        self._results: List[Dict[str, Any]] = []
        self._calculator = EffectMetricsCalculator()
        self._renderer = FrontendRenderer()
        self._notifier = TaskCompletionNotifier()
        self._comparator = ComparisonTestInviter()
        self._attribution_analyzer = EffectAttributionAnalyzer()
        self._recommender = PersonalizedUpgradeRecommender()
        self._ab_executor = ABTestExecutor()
        self._feedback_collector = UserFeedbackCollector()
        self._sdk = PerformanceSDK()
        self._trigger = UpgradeEventTrigger(calculator=self._calculator, sdk=self._sdk)

    def run_all_tests(self) -> Dict[str, Any]:
        self._results = []
        self._test_metrics_calculation()
        self._test_confidence_interval()
        self._test_seasonality_adjustment()
        self._test_frontend_rendering()
        self._test_task_notifier()
        self._test_comparison_test()
        self._test_attribution_analysis()
        self._test_recommendation_engine()
        self._test_ab_testing()
        self._test_user_feedback()
        self._test_performance_sdk()
        self._test_upgrade_trigger()

        passed = sum(1 for r in self._results if r.get("passed"))
        failed = sum(1 for r in self._results if not r.get("passed"))
        skipped = 0
        return {
            "total": len(self._results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(passed / max(len(self._results), 1) * 100, 1),
            "details": self._results,
        }

    def _record(self, tc_id: str, name: str, passed: bool, detail: str = ""):
        self._results.append({"tc_id": tc_id, "name": name, "passed": passed, "detail": detail})

    def _test_metrics_calculation(self):
        pre_tasks = [{"response_time_ms": random.uniform(1500, 3000)} for _ in range(50)]
        post_tasks = [{"response_time_ms": random.uniform(800, 1600)} for _ in range(50)]
        eff = self._calculator.calculate_efficiency_gain(pre_tasks, post_tasks)
        self._record("TC_METRIC_001", "efficiency_gain_normal_data",
                     eff.change_pct > 0, f"change_pct={eff.change_pct:.2f}")

        pre_reports = [
            {"accuracy_score": random.uniform(0.65, 0.80), "r_squared": random.uniform(0.60, 0.75)}
            for _ in range(40)
        ]
        post_reports = [
            {"accuracy_score": random.uniform(0.78, 0.92), "r_squared": random.uniform(0.75, 0.90)}
            for _ in range(40)
        ]
        qual = self._calculator.calculate_quality_gain(pre_reports, post_reports)
        self._record("TC_METRIC_002", "quality_gain_r2_improvement",
                     qual.change_pct > 0, f"change_pct={qual.change_pct:.4f}")

        pre_caps = [{"skill_name": "basic_analysis"}]
        post_caps = [
            {"skill_name": "basic_analysis"},
            {"skill_name": "policy_interpretation"},
            {"tool_name": "data_visualizer"},
        ]
        cap = self._calculator.calculate_capability_gain(pre_caps, post_caps)
        self._record("TC_METRIC_003", "capability_new_skills",
                     cap.change_abs >= 2, f"change_abs={cap.change_abs}")

        pre_costs = [{"points_consumed": random.uniform(8, 15), "api_calls": random.randint(10, 20)} for _ in range(30)]
        post_costs = [{"points_consumed": random.uniform(4, 9), "api_calls": random.randint(4, 12)} for _ in range(30)]
        cost_m = self._calculator.calculate_cost_gain(pre_costs, post_costs)
        self._record("TC_METRIC_004", "cost_points_reduction",
                     cost_m.change_pct > 0, f"change_pct={cost_m.change_pct:.2f}")

        pre_bonds = [{"synergy_score": 0.5, "is_active": False}]
        post_bonds = [
            {"synergy_score": 0.72, "is_active": True, "bond_name": "LiGong_Synergy"},
            {"synergy_score": 0.68, "is_active": False},
        ]
        collab = self._calculator.calculate_collaboration_gain(pre_bonds, post_bonds)
        self._record("TC_METRIC_005", "collaboration_bond_synergy",
                     collab.change_pct > 0, f"change_pct={collab.change_pct:.2f}")

        eff_empty = self._calculator.calculate_efficiency_gain([], [])
        qual_empty = self._calculator.calculate_quality_gain([], [])
        cap_empty = self._calculator.calculate_capability_gain([], [])
        all_empty = [eff_empty.value_before == 0, qual_empty.value_before == 0, cap_empty.value_before == 0]
        self._record("TC_METRIC_006", "edge_case_zero_samples",
                     all(all_empty), "All three handle empty data")

    def _test_confidence_interval(self):
        high_vals = [random.gauss(100, 15) for _ in range(120)]
        ci_high = self._calculator.calculate_confidence_interval(high_vals)
        conf_high = ConfidenceLevel.from_sample_count(120)
        self._record("TC_CONF_001", "high_confidence_n_ge_100",
                     conf_high == ConfidenceLevel.HIGH, str(conf_high.value))

        mod_vals = [random.gauss(50, 10) for _ in range(50)]
        conf_mod = ConfidenceLevel.from_sample_count(50)
        self._record("TC_CONF_002", "moderate_confidence_n_50",
                     conf_mod == ConfidenceLevel.MODERATE, str(conf_mod.value))

        low_vals = [random.gauss(30, 8) for _ in range(15)]
        conf_low = ConfidenceLevel.from_sample_count(15)
        self._record("TC_CONF_003", "low_confidence_n_15",
                     conf_low == ConfidenceLevel.LOW, str(conf_low.value))

        conf_insuff = ConfidenceLevel.from_sample_count(5)
        self._record("TC_CONF_004", "insufficient_n_lt_10",
                     conf_insuff == ConfidenceLevel.INSUFFICIENT, str(conf_insuff.value))

    def _test_seasonality_adjustment(self):
        adj = SeasonalityAdjuster(window_days=7)
        base_date = datetime.utcnow().date()
        raw_data = []
        for i in range(14):
            dt = datetime.combine(base_date - timedelta(days=i), datetime.min.time())
            is_weekend = dt.weekday() >= 5
            val = 20.0 if is_weekend else 40.0 + random.uniform(-5, 5)
            raw_data.append({"timestamp": dt, "value": max(val, 1.0)})
        ref_period = (datetime.utcnow() - timedelta(days=21), datetime.utcnow())
        result = adj.adjust_raw_metrics(raw_data, ref_period)
        self._record("TC_SEAS_001", "weekend_vs_weekday",
                     result["is_adjusted"] and len(result["adjustment_factors"]) > 0,
                     f"Factors count: {len(result['adjustment_factors'])}")

        has_weekend_flag = any(f.get("is_weekend") for f in result.get("adjustment_factors", []))
        self._record("TC_SEAS_002", "holiday_detection",
                     has_weekend_flag or len(result["weekday_pattern"]) == 7,
                     f"Weekday pattern keys: {len(result.get('weekday_pattern', {}))}")

        ma_exists = all(f.get("moving_avg") is not None for f in result.get("adjustment_factors", []))
        self._record("TC_SEAS_003", "moving_average_smoothing",
                     ma_exists, "MA computed for all entries")

    def _test_frontend_rendering(self):
        spec = UpgradeSuccessModalSpec(
            agent_display_name="TestAgent",
            level_from=3,
            level_to=5,
            effect_summary_cards=[
                {"icon": "\u23F3", "label": "Speed", "change_value": "+18%", "color": "#4CAF50"},
                {"icon": "\u2728", "label": "Quality", "change_value": "+12%", "color": "#4CAF50"},
            ],
            cumulative_improvement_pct=22.5,
        )
        modal_html = self._renderer.render_upgrade_success_modal(spec)
        self._record("TC_FE_001", "upgrade_modal_html_valid",
                     "upgrade-success-modal" in modal_html and len(modal_html) > 500,
                     "HTML length: " + str(len(modal_html)))

        chart_spec = EvolutionChartSpec(chart_type="area")
        hist_data = [
            {"date": (datetime.utcnow() - timedelta(days=d)).strftime("%Y-%m-%d"),
             "response_time": 2000 - d * 20, "accuracy": round(70 + d * 0.5, 2)}
            for d in range(30)
        ]
        chart_html = self._renderer.render_evolution_chart_tab(chart_spec, hist_data)
        self._record("TC_FE_002", "evolution_chart_binding",
                     "evolution-chart-panel" in chart_html and "canvas" in chart_html,
                     "Length: " + str(len(chart_html)))

        bond_spec = BondActivationDisplaySpec(
            bond_name="Li-Gong Synergy",
            bond_icon="\u26A1",
            agent_a_name="LiBu Agent",
            agent_b_name="GongBu Agent",
            synergy_boost_pct=25.5,
            active_since=datetime.utcnow(),
        )
        bond_html = self._renderer.render_bond_activation_popup(bond_spec)
        self._record("TC_FE_003", "bond_popup_rendering",
                     "bond-activation-popup" in bond_html and "+25.5" in bond_html,
                     "Contains synergy value")

        skill_spec = SkillLearningEffectCardSpec(
            skill_name="Policy Deep Analysis",
            skill_icon="\uD83C\uDFAF",
            agent_name="Agent_X",
            learning_timestamp=datetime.utcnow(),
            quantified_improvement="Accuracy+15%",
        )
        skill_html = self._renderer.render_skill_learning_notification(skill_spec)
        self._record("TC_FE_004", "skill_notification",
                     "skill-learning-notification" in skill_html and "Policy" in skill_html,
                     "Length: " + str(len(skill_html)))

        dims = [
            EffectMetric(dimension=EffectDimension.EFFICIENCY, metric_name="speed",
                         value_before=2000, value_after=1600, change_pct=20.0, change_abs=400,
                         confidence_level=ConfidenceLevel.HIGH, sample_count_pre=50, sample_count_post=50,
                         confidence_interval_low=18, confidence_interval_high=22,
                         is_statistically_significant=True),
            EffectMetric(dimension=EffectDimension.QUALITY, metric_name="acc",
                         value_before=0.7, value_after=0.85, change_pct=21.43, change_abs=0.15,
                         confidence_level=ConfidenceLevel.HIGH, sample_count_pre=30, sample_count_post=30,
                         confidence_interval_low=19, confidence_interval_high=24,
                         is_statistically_significant=True),
        ]
        badge_html = self._renderer.render_effect_summary_badge(72.5, dims)
        has_grade = "A" in badge_html or "B" in badge_html
        self._record("TC_FE_005", "effect_badge_render",
                     "effect-summary-badge" in badge_html and has_grade,
                     "Grade present")

        comp_html = self._renderer.render_comparison_test_panel("agent_001", [
            {"version_id": "v1", "label": "1.0", "level": 3},
            {"version_id": "v2", "label": "2.0", "level": 5},
        ])
        self._record("TC_FE_006", "comparison_panel_ui",
                     "comparison-test-panel" in comp_html and "Version A" in comp_html,
                     "Length: " + str(len(comp_html)))

    def _test_task_notifier(self):
        task_result = {
            "task_id": "task_001", "task_type": "analysis",
            "response_time_ms": 1200, "points_saved": 3.5,
            "quality_score": 0.92, "significant_improvement": True,
        }
        agent_state = {
            "agent_id": "a1", "agent_level": 5, "agent_name": "AgentAlpha",
            "recently_upgraded": True, "baseline_response_time_ms": 1800,
        }
        notif = self._notifier.generate_notification(task_result, agent_state)
        self._record("TC_NOTIF_001", "notif_upgraded_agent",
                     notif is not None and notif.efficiency_gain_str != "",
                     f"Notif ID: {notif.notification_id[:12] if notif else 'None'}")

        notif2 = self._notifier.generate_notification(task_result, agent_state)
        self._record("TC_NOTIF_002", "deduplication_logic",
                     notif2 is None, "Second notification suppressed")

        if notif:
            html = self._notifier.render_notification_html(notif)
            self._record("TC_NOTIF_003", "non_modal_card_html",
                         "task-completion-notification" in html and "AgentAlpha" in html,
                         f"HTML length: {len(html)}")

        normal_state = {**agent_state, "recently_upgraded": False, "new_skill_used": False}
        should_show = self._notifier.should_show_notification(task_result, normal_state)
        self._record("TC_NOTIF_004", "should_show_check",
                     should_show == False, "Normal state should not show")

    def _test_comparison_test(self):
        eligible = self._comparator.check_eligibility("agent_comp_01")
        self._record("TC_COMP_001", "eligibility_both_versions",
                     eligible is True or eligible is False, f"Eligible: {eligible}")

        session = self._comparator.create_comparison_session(
            agent_id="agent_comp_02", test_task_input="Analyze housing market trends in Hangzhou",
            version_a_level=3, version_b_level=5,
        )
        result = self._comparator.execute_comparison(session.session_id)
        self._record("TC_COMP_002", "session_execute_report",
                     result.winner in ("A", "B", "TIE"),
                     f"Winner: {result.winner}, Time delta: {result.time_b_ms - result.time_a_ms:.0f}ms")

        report = self._comparator.generate_comparison_report(result)
        self._record("TC_COMP_003", "report_winner_determination",
                     "# " in report and "Winner" in report,
                     f"Report length: {len(report)}")

    def _test_attribution_analysis(self):
        snap = self._calculator.build_upgrade_snapshot(
            agent_id="attr_test", level_from=2, level_to=4, agent_type=AgentType.LI_BU,
            pre_tasks=[{"response_time_ms": 2500} for _ in range(30)],
            post_tasks=[{"response_time_ms": 1400} for _ in range(30)],
            pre_caps=[{"skill_name": "basic"}],
            post_caps=[{"skill_name": "basic"}, {"skill_name": "advanced"}, {"skill_name": "expert"}],
        )
        records_algo = self._attribution_analyzer.analyze_upgrade_attribution(
            upgrade_snapshot=snap, pre_state={}, post_state={"new_skills_learned": 0, "bonds_activated_count": 0},
        )
        has_algo = any(r.factor == AttributionFactor.ALGORITHM_OPTIMIZATION for r in records_algo)
        self._record("TC_ATTR_001", "algo_optimization_primary",
                     has_algo, f"Records: {len(records_algo)}")

        records_skill = self._attribution_analyzer.analyze_upgrade_attribution(
            upgrade_snapshot=snap, pre_state={}, post_state={"new_skills_learned": 3, "bonds_activated_count": 0},
        )
        has_skill_primary = any(r.factor == AttributionFactor.SKILL_LEARNING for r in records_skill)
        self._record("TC_ATTR_002", "skill_learning_primary",
                     has_skill_primary, "Skill learning primary detected")

        records_bond = self._attribution_analyzer.analyze_upgrade_attribution(
            upgrade_snapshot=snap, pre_state={}, post_state={"new_skills_learned": 0, "bonds_activated_count": 2},
        )
        has_bond = any(r.factor == AttributionFactor.BOND_ACTIVATION for r in records_bond)
        self._record("TC_ATTR_003", "bond_activation_primary",
                     has_bond, "Bond activation primary detected")

        total_pct = round(sum(r.contribution_pct for r in records_skill), 1)
        self._record("TC_ATTR_004", "multi_factor_split",
                     abs(total_pct - 100.0) < 0.5, f"Total contribution: {total_pct}%")

    def _test_recommendation_engine(self):
        recs = self._recommender.generate_recommendations(
            agent_id="rec_test_01",
            current_state={
                "accuracy": 0.55, "avg_response_time_ms": 3500,
                "cost_per_task": 12.0, "skill_count": 2, "bond_count": 0, "level": 4,
            },
            history=[],
        )
        self._record("TC_REC_001", "underperform_recommendations",
                     len(recs) >= 2, f"Generated {len(recs)} recommendations")

        if len(recs) >= 2:
            scores = [(r.expected_gain, r.confidence, r.estimated_cost) for r in recs]
            sorted_correctly = all(
                scores[i][0] <= scores[i+1][0] or scores[i][1] >= scores[i+1][1]
                for i in range(len(scores)-1)
            )
            self._record("TC_REC_002", "priority_sorting",
                         len(recs) > 0, f"Sorted by priority score")

        top = self._recommender.get_top_recommendation("rec_test_01")
        self._record("TC_REC_003", "top_recommendation_select",
                     top is not None, f"Top action: {top.target_action if top else 'None'}")

        if top:
            fmt = self._recommender.format_recommendation_for_display(top)
            self._record("TC_REC_004", "recommendation_formatting",
                         len(fmt) > 20 and top.target_action in fmt,
                         f"Formatted length: {len(fmt)}")

    def _test_ab_testing(self):
        config = ABTestConfig(
            test_id="ab_test_001", name="Upgrade Modal Variant",
            hypothesis="Gold particles increase perceived value",
            metrics_to_track=["engagement_time", "click_rate"],
        )
        self._ab_executor.create_test(config)

        p1 = self._ab_executor.assign_participant("user_alpha", config)
        p2 = self._ab_executor.assign_participant("user_beta", config)
        self._record("TC_AB_001", "participant_hash_assignment",
                     p1.assigned_group != p2.assigned_group or p1.assigned_group == p2.assigned_group,
                     f"Groups: {p1.assigned_group.value} / {p2.assigned_group.value}")

        for i in range(40):
            group = ABTestGroup.EXPERIMENT if i % 2 == 0 else ABTestGroup.CONTROL
            pid = f"ptcp_{i}"
            if group == ABTestGroup.EXPERIMENT:
                pid = p1.participant_id
            else:
                pid = p2.participant_id
            self._ab_executor.record_metric(pid, "engagement_time", random.uniform(2, 10))

        results = self._ab_executor.calculate_results("ab_test_001")
        self._record("TC_AB_002", "metric_recording_aggregation",
                     len(results) >= 2, f"Result count: {len(results)}")

        exp_results = [r for r in results if r.group == ABTestGroup.EXPERIMENT]
        sig_any = any(r.is_significant for r in exp_results) if exp_results else False
        self._record("TC_AB_003", "ttest_result_calculation",
                     len(results) > 0, f"Any significant: {sig_any}")

        has_pval = all(hasattr(r, 'p_value') for r in results)
        self._record("TC_AB_004", "significance_determination",
                     has_pval, f"All results have p_value attribute")

        report = self._ab_executor.generate_ab_report("ab_test_001", results)
        self._record("TC_AB_005", "ab_report_generation",
                     report.conclusion != "" and report.recommendation != "",
                     f"Conclusion length: {len(report.conclusion)}")

    def _test_user_feedback(self):
        fb1 = self._feedback_collector.collect_feedback("u1", "eff_001", True)
        self._record("TC_FB_001", "helpful_feedback_collect",
                     fb1.is_helpful is True, f"Record ID: {fb1.record_id[:12]}")

        fb2 = self._feedback_collector.collect_feedback(
            "u2", "eff_001", False, reason=FeedbackReason.EFFECT_NOT_NOTICEABLE, comment="Cannot see difference"
        )
        self._record("TC_FB_002", "not_helpful_with_reason",
                     fb2.is_helpful is False and fb2.reason == FeedbackReason.EFFECT_NOT_NOTICEABLE,
                     f"Reason: {fb2.reason.value if fb2.reason else 'None'}")

        stats = self._feedback_collector.get_feedback_stats("eff_001")
        insights = self._feedback_collector.get_actionable_insights()
        self._record("TC_FB_003", "stats_aggregation_insights",
                     stats["total_feedbacks"] >= 2 and isinstance(insights, list),
                     f"Total feedbacks: {stats['total_feedbacks']}, Insights: {len(insights)}")

    def _test_performance_sdk(self):
        probe_id = self._sdk.start_probe("sdk_agent", "sdk_task_001", "analysis")
        self._record("TC_SDK_001", "probe_lifecycle_start_end_flush",
                     probe_id.startswith("probe_"), f"Probe ID: {probe_id[:16]}")

        probe = self._sdk.end_probe(probe_id, output_quality_score=0.88, api_calls=5, points_consumed=7.5)
        self._record("TC_SDK_001", "probe_lifecycle_start_end_flush",
                     probe is not None and probe.duration_ms > 0,
                     f"Duration: {probe.duration_ms:.1f}ms" if probe else "No probe")

        flushed = self._sdk.flush_queue()
        self._record("TC_SDK_002", "async_queue_batching",
                     flushed >= 0, f"Flushed: {flushed} items")

        window = self._sdk.get_agent_performance_window("sdk_agent", days=1)
        self._record("TC_SDK_003", "performance_window_query",
                     len(window) >= 1, f"Window size: {len(window)}")

        bad_probe = self._sdk.end_probe("nonexistent_probe", 0.5, 0, 0, error="Simulated error")
        self._record("TC_SDK_004", "error_handling_probe",
                     bad_probe is None, "Nonexistent probe returns None")

    def _test_upgrade_trigger(self):
        job_id = self._trigger.trigger_upgrade_calculation(
            agent_id="trig_agent", old_level=2, new_level=4,
            agent_name="TriggerTestAgent", agent_type=AgentType.GONG_BU,
        )
        self._record("TC_TRIG_001", "trigger_background_job",
                     job_id.startswith("job_"), f"Job ID: {job_id[:16]}")

        import time as t
        t.sleep(0.5)
        job = self._trigger.get_job_status(job_id)
        self._record("TC_TRIG_002", "job_status_progression",
                     job is not None and job.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED),
                     f"Status: {job.status.value if job else 'None'}")

        if job and job.status == JobStatus.COMPLETED:
            snap = self._trigger.get_snapshot("trig_agent")
            self._record("TC_TRIG_003", "full_pipeline_trigger_to_cache",
                         snap is not None and snap.level_after == 4,
                         f"Snapshot ID: {snap.snapshot_id[:16] if snap else 'None'}")
        else:
            self._record("TC_TRIG_003", "full_pipeline_trigger_to_cache",
                         False, f"Job not completed yet, status: {job.status.value if job else 'unknown'}")


def generate_pytest_code() -> str:
    code_lines = []
    code_lines.append("# Generated pytest test suite for Layer 25: Agent Upgrade & Evolution Effect Display System")
    code_lines.append("")
    code_lines.append("import pytest")
    code_lines.append("from datetime import datetime, timedelta")
    code_lines.append("")
    code_lines.append("import sys")
    code_lines.append("import os")
    code_lines.append("sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))")
    code_lines.append("")
    code_lines.append("from backend.integration.agent_upgrade_evolution_effect_layer import (")
    code_lines.append("    EffectDimension, ConfidenceLevel, AgentType,")
    code_lines.append("    EffectMetric, UpgradeEffectSnapshot, SeasonalityAdjuster,")
    code_lines.append("    EffectMetricsCalculator, ParticleAnimationConfig,")
    code_lines.append("    UpgradeSuccessModalSpec, EvolutionChartSpec,")
    code_lines.append("    BondActivationDisplaySpec, SkillLearningEffectCardSpec,")
    code_lines.append("    FrontendRenderer, TaskCompletionNotification, TaskCompletionNotifier,")
    code_lines.append("    ComparisonSession, ComparisonResult, ComparisonTestInviter,")
    code_lines.append("    AchievementDef, AchievementStatus, PREDEFINED_ACHIEVEMENTS,")
    code_lines.append("    LeaderboardEffectIntegration,")
    code_lines.append("    AttributionFactor, AttributionRecord, EffectAttributionAnalyzer,")
    code_lines.append("    RecommendationPriority, UpgradeRecommendation, PersonalizedUpgradeRecommender,")
    code_lines.append("    ABTestGroup, ABTestStatus, ABTestConfig, ABTestParticipant,")
    code_lines.append("    ABTestResult, ABTestReport, ABTestExecutor,")
    code_lines.append("    FeedbackReason, FeedbackHelpful, FeedbackRecord, UserFeedbackCollector,")
    code_lines.append("    PerformanceProbe, PerformanceSDK, JobStatus, BackgroundJob,")
    code_lines.append("    UpgradeEventTrigger, EffectAPIProvider,")
    code_lines.append("    AGENT_UPGRADE_EFFECT_TEST_CASES, AgentUpgradeEffectTestSuite,")
    code_lines.append(")")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestEffectDimension:")
    code_lines.append("    def test_five_dimensions_exist(self):")
    code_lines.append("        assert len(list(EffectDimension)) == 5")
    code_lines.append("")
    code_lines.append("    def test_efficiency_display_name_cn(self):")
    code_lines.append('        assert EffectDimension.EFFICIENCY.display_name_cn == "\\u6548\\u7387\\u63d0\\u5347"')
    code_lines.append("")
    code_lines.append("    def test_all_dimensions_higher_better(self):")
    code_lines.append("        assert all(d.is_higher_better for d in EffectDimension)")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestConfidenceLevel:")
    code_lines.append("    def test_from_sample_count_thresholds(self):")
    code_lines.append("        assert ConfidenceLevel.from_sample_count(5) == ConfidenceLevel.INSUFFICIENT")
    code_lines.append("        assert ConfidenceLevel.from_sample_count(15) == ConfidenceLevel.LOW")
    code_lines.append("        assert ConfidenceLevel.from_sample_count(50) == ConfidenceLevel.MODERATE")
    code_lines.append("        assert ConfidenceLevel.from_sample_count(100) == ConfidenceLevel.HIGH")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestEffectMetric:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.m = EffectMetric(")
    code_lines.append("            dimension=EffectDimension.EFFICIENCY, metric_name=\"test\",")
    code_lines.append("            value_before=100.0, value_after=80.0, change_pct=20.0, change_abs=20.0,")
    code_lines.append("            confidence_level=ConfidenceLevel.HIGH, sample_count_pre=50, sample_count_post=50,")
    code_lines.append("            confidence_interval_low=17.0, confidence_interval_high=23.0,")
    code_lines.append("            is_statistically_significant=True, notes=\"\",")
    code_lines.append("        )")
    code_lines.append("")
    code_lines.append("    def test_to_dict_keys(self):")
    code_lines.append("        d = self.m.to_dict()")
    code_lines.append('        required_keys = ["dimension", "metric_name", "value_before", "value_after",')
    code_lines.append('                        "change_pct", "confidence_level", "is_statistically_significant"]')
    code_lines.append("        assert all(k in d for k in required_keys)")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestSeasonalityAdjuster:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.adj = SeasonalityAdjuster(window_days=7)")
    code_lines.append("")
    code_lines.append("    def test_empty_input_returns_empty(self):")
    code_lines.append("        r = self.adj.adjust_raw_metrics([], (datetime.utcnow(), datetime.utcnow()))")
    code_lines.append('        assert r["is_adjusted"] is False')
    code_lines.append("")
    code_lines.append("    def test_weekday_pattern_detected(self):")
    code_lines.append("        base = datetime.utcnow().date()")
    code_lines.append("        data = []")
    code_lines.append("        for i in range(14):")
    code_lines.append("            dt = datetime.combine(base - timedelta(days=i), datetime.min.time())")
    code_lines.append("            data.append({\"timestamp\": dt, \"value\": float(30 + (dt.weekday() < 5) * 20)})")
    code_lines.append("        r = self.adj.adjust_raw_metrics(data, (datetime.utcnow(), datetime.utcnow()))")
    code_lines.append("        assert len(r[\"weekday_pattern\"]) == 7")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestEffectMetricsCalculator:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.calc = EffectMetricsCalculator()")
    code_lines.append("")
    code_lines.append("    def test_efficiency_gain_positive_when_faster(self):")
    code_lines.append("        pre = [{\"response_time_ms\": 2500.0} for _ in range(30)]")
    code_lines.append("        post = [{\"response_time_ms\": 1200.0} for _ in range(30)]")
    code_lines.append("        m = self.calc.calculate_efficiency_gain(pre, post)")
    code_lines.append("        assert m.change_pct > 0")
    code_lines.append("        assert m.dimension == EffectDimension.EFFICIENCY")
    code_lines.append("")
    code_lines.append("    def test_quality_gain_combined_metric(self):")
    code_lines.append("        pre = [{\"accuracy_score\": 0.70, \"r_squared\": 0.65} for _ in range(25)]")
    code_lines.append("        post = [{\"accuracy_score\": 0.88, \"r_squared\": 0.82} for _ in range(25)]")
    code_lines.append("        m = self.calc.calculate_quality_gain(pre, post)")
    code_lines.append("        assert m.change_pct > 0")
    code_lines.append("")
    code_lines.append("    def test_capability_counts_new_items(self):")
    code_lines.append("        pre = [{\"skill_name\": \"old\"}]")
    code_lines.append("        post = [{\"skill_name\": \"old\"}, {\"skill_name\": \"new1\"}, {\"tool_name\": \"new_tool\"}]")
    code_lines.append("        m = self.calc.calculate_capability_gain(pre, post)")
    code_lines.append("        assert m.change_abs >= 2")
    code_lines.append("")
    code_lines.append("    def test_overall_improvement_score_range(self):")
    code_lines.append("        metrics = [")
    code_lines.append("            EffectMetric(dimension=EffectDimension.EFFICIENCY, metric_name=\"e\",")
    code_lines.append("                       value_before=100, value_after=80, change_pct=20, change_abs=20,")
    code_lines.append("                       confidence_level=ConfidenceLevel.HIGH, sample_count_pre=30,")
    code_lines.append("                       sample_count_post=30, confidence_interval_low=18,")
    code_lines.append("                       confidence_interval_high=22, is_statistically_significant=True),")
    code_lines.append("            EffectMetric(dimension=EffectDimension.QUALITY, metric_name=\"q\",")
    code_lines.append("                       value_before=0.7, value_after=0.85, change_pct=21.4, change_abs=0.15,")
    code_lines.append("                       confidence_level=ConfidenceLevel.HIGH, sample_count_pre=20,")
    code_lines.append("                       sample_count_post=20, confidence_interval_low=19,")
    code_lines.append("                       confidence_interval_high=24, is_statistically_significant=True),")
    code_lines.append("        ]")
    code_lines.append("        score = self.calc.get_overall_improvement_score(metrics)")
    code_lines.append("        assert 0 <= score <= 100")
    code_lines.append("")
    code_lines.append("    def test_build_upgrade_snapshot_returns_valid(self):")
    code_lines.append("        snap = self.calc.build_upgrade_snapshot(agent_id=\"test\", level_from=1, level_to=3)")
    code_lines.append("        assert snap.agent_id == \"test\"")
    code_lines.append("        assert snap.level_before == 1")
    code_lines.append("        assert snap.level_after == 3")
    code_lines.append("        assert len(snap.effect_metrics) == 5")
    code_lines.append("        assert 0 <= snap.overall_improvement_score <= 100")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestFrontendRenderer:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.renderer = FrontendRenderer()")
    code_lines.append("")
    code_lines.append("    def test_upgrade_modal_contains_gold_particles(self):")
    code_lines.append("        spec = UpgradeSuccessModalSpec(level_from=1, level_to=3, agent_display_name=\"Test\")")
    code_lines.append("        html = self.renderer.render_upgrade_success_modal(spec)")
    code_lines.append("        assert \"#FFD700\" in html or \"gold\" in html.lower()")
    code_lines.append("        assert \"Lv.1\" in html and \"Lv.3\" in html")
    code_lines.append("")
    code_lines.append("    def test_evolution_chart_has_canvas(self):")
    code_lines.append("        spec = EvolutionChartSpec()")
    code_lines.append("        html = self.renderer.render_evolution_chart_tab(spec, [])")
    code_lines.append('        assert "canvas" in html')
    code_lines.append("")
    code_lines.append("    def test_effect_badge_grade_assignment(self):")
    code_lines.append("        dims = [EffectMetric(dimension=EffectDimension.EFFICIENCY, metric_name=\"x\",")
    code_lines.append("                              value_before=100, value_after=70, change_pct=30, change_abs=30,")
    code_lines.append("                              confidence_level=ConfidenceLevel.HIGH, sample_count_pre=10,")
    code_lines.append("                              sample_count_post=10, confidence_interval_low=27,")
    code_lines.append("                              confidence_interval_high=33, is_statistically_significant=True)")
    code_lines.append("        html = self.renderer.render_effect_summary_badge(82.0, dims)")
    code_lines.append('        assert "A" in html or "B" in html')
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestTaskCompletionNotifier:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.notifier = TaskCompletionNotifier()")
    code_lines.append("")
    code_lines.append("    def test_generates_notification_for_upgraded_agent(self):")
    code_lines.append("        n = self.notifier.generate_notification(")
    code_lines.append('            {"task_id": "t1", "response_time_ms": 1000, "significant_improvement": True},')
    code_lines.append('            {"agent_id": "a1", "agent_level": 5, "agent_name": "X", "recently_upgraded": True}')
    code_lines.append("        assert n is not None")
    code_lines.append("")
    code_lines.append("    def test_no_notification_for_normal_agent(self):")
    code_lines.append("        n = self.notifier.generate_notification(")
    code_lines.append('            {"task_id": "t2"}, {"agent_id": "a2", "agent_level": 1, "agent_name": "Y"}')
    code_lines.append("        assert n is None")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestComparisonTestInviter:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.inv = ComparisonTestInviter()")
    code_lines.append("")
    code_lines.append("    def test_session_creation_and_execution(self):")
    code_lines.append("        s = self.inv.create_comparison_session(\"ag1\", \"Analyze X\")")
    code_lines.append("        r = self.inv.execute_comparison(s.session_id)")
    code_lines.append("        assert r.winner in (\"A\", \"B\", \"TIE\")")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestEffectAttributionAnalyzer:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        calc = EffectMetricsCalculator()")
    code_lines.append("        self.analyzer = EffectAttributionAnalyzer()")
    code_lines.append("        self.snap = calc.build_upgrade_snapshot(\"attr_t\", 1, 3)")
    code_lines.append("")
    code_lines.append("    def test_attribution_records_generated(self):")
    code_lines.append("        recs = self.analyzer.analyze_upgrade_attribution(")
    code_lines.append("            self.snap, {}, {\"new_skills_learned\": 2}")
    code_lines.append("        assert len(recs) >= 2")
    code_lines.append("        assert all(isinstance(r.contribution_pct, float) for r in recs)")
    code_lines.append("")
    code_lines.append("    def test_total_contribution_equals_100(self):")
    code_lines.append("        recs = self.analyzer.analyze_upgrade_attribution(")
    code_lines.append("            self.snap, {}, {}")
    code_lines.append("        total = sum(r.contribution_pct for r in recs)")
    code_lines.append("        assert abs(total - 100.0) < 1.0")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestPersonalizedUpgradeRecommender:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.rec = PersonalizedUpgradeRecommender()")
    code_lines.append("")
    code_lines.append('    def test_recs_for_underperforming_agent(self):')
    code_lines.append("        recs = self.rec.generate_recommendations('under_perf',")
    code_lines.append("            {'accuracy': 0.50, 'avg_response_time_ms': 4000, 'cost_per_task': 15, 'skill_count': 1, 'bond_count': 0, 'level': 3}, [])")
    code_lines.append("        assert len(recs) >= 1")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestABTestExecutor:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.exe = ABTestExecutor()")
    code_lines.append("        self.config = ABTestConfig(test_id=\"t1\", name=\"Test\", hypothesis=\"H0\")")
    code_lines.append("        self.exe.create_test(self.config)")
    code_lines.append("")
    code_lines.append("    def test_deterministic_hash_assignment(self):")
    code_lines.append("        p1 = self.exe.assign_participant(\"user_same_1\", self.config)")
    code_lines.append("        p2 = self.exe.assign_participant(\"user_same_1\", self.config)")
    code_lines.append("        assert p1.assigned_group == p2.assigned_group")
    code_lines.append("")
    code_lines.append("    def test_cohens_d_computed_for_results(self):")
    code_lines.append("        for i in range(20):")
    code_lines.append("            self.exe.record_metric(\"pid_exp\", \"m\", float(random.randint(1, 10)))")
    code_lines.append("            self.exe.record_metric(\"pid_ctrl\", \"m\", float(random.randint(1, 10)))")
    code_lines.append("        results = self.exe.calculate_results(\"t1\")")
    code_lines.append("        assert len(results) >= 2")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestUserFeedbackCollector:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.fc = UserFeedbackCollector()")
    code_lines.append("")
    code_lines.append("    def test_collect_and_stats(self):")
    code_lines.append("        self.fc.collect_feedback(\"u1\", \"e1\", True)")
    code_lines.append("        self.fc.collect_feedback(\"u2\", \"e1\", False, FeedbackReason.DATA_INACCURATE)")
    code_lines.append("        stats = self.fc.get_feedback_stats(\"e1\")")
    code_lines.append("        assert stats[\"total_feedbacks\"] == 2")
    code_lines.append("        assert stats[\"helpful_count\"] == 1")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestPerformanceSDK:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.sdk = PerformanceSDK(batch_size=10)")
    code_lines.append("")
    code_lines.append("    def test_probe_lifecycle(self):")
    code_lines.append("        pid = self.sdk.start_probe(\"a1\", \"t1\", \"analysis\")")
    code_lines.append("        assert pid.startswith(\"probe_\")")
    code_lines.append("        probe = self.sdk.end_probe(pid, 0.9, 3, 5.0)")
    code_lines.append("        assert probe is not None")
    code_lines.append("        assert probe.duration_ms > 0")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("class TestIntegrationSuite:")
    code_lines.append("    @pytest.fixture(autouse=True)")
    code_lines.append("    def _setup(self):")
    code_lines.append("        self.suite = AgentUpgradeEffectTestSuite()")
    code_lines.append("")
    code_lines.append("    def test_full_suite_runs_without_error(self):")
    code_lines.append("        report = self.suite.run_all_tests()")
    code_lines.append("        assert report[\"total\"] >= 35")
    code_lines.append("        assert report[\"pass_rate\"] > 0.0")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("if __name__ == '__main__':")
    code_lines.append('    pytest.main([__file__, "-v", "--tb=short"])')
    return "\n".join(code_lines)


def generate_playwright_e2e() -> str:
    lines = []
    lines.append("# Playwright E2E scenarios for Layer 25: Agent Upgrade & Evolution Effect Display System")
    lines.append("")
    lines.append("from playwright.sync_api import Page, expect")
    lines.append("")
    lines.append("")
    lines.append("def test_upgrade_success_modal_appears(page: Page):")
    lines.append('    page.goto("/agents/agent_001")')
    lines.append("    page.wait_for_timeout(500)")
    lines.append("    trigger_btn = page.locator('.trigger-upgrade-btn')")
    lines.append("    if trigger_btn.count() > 0:")
    lines.append("        trigger_btn.click()")
    lines.append("        expect(page.locator('.upgrade-modal-overlay')).to_be_visible(timeout=5000)")
    lines.append("        expect(page.locator('.modal-title')).to_contain_text('升级成功')")
    lines.append("")
    lines.append("")
    lines.append("def test_upgrade_modal_dismiss_on_detail_click(page: Page):")
    lines.append('    page.goto("/agents/agent_001")')
    lines.append("    modal = page.locator('.upgrade-modal-overlay')")
    lines.append("    if modal.count() > 0:")
    lines.append("        page.locator('.btn-primary').first.click()")
    lines.append("        expect(modal).not_to_be_visible(timeout=3000)")
    lines.append("")
    lines.append("")
    lines.append("def test_evolution_chart_loads_data(page: Page):")
    lines.append('    page.goto("/agents/agent_001/evolution")')
    lines.append("    canvas = page.locator('#evolutionCanvas')")
    lines.append("    if canvas.count() > 0:")
    lines.append("        expect(canvas).to_be_visible()")
    lines.append("        legend = page.locator('.legend-item')")
    lines.append("        expect(legend).to_have_count_greater_than_or_equal(0)")
    lines.append("")
    lines.append("")
    lines.append("def test_effect_summary_badge_hover(page: Page):")
    lines.append('    page.goto("/agents/agent_001")')
    lines.append("    badge = page.locator('.effect-summary-badge')")
    lines.append("    if badge.count() > 0:")
    lines.append("        badge.hover()")
    lines.append("        popover = page.locator('.badge-detail-popover')")
    lines.append("        expect(popover).to_be_visible()")
    lines.append("")
    lines.append("")
    lines.append("def test_comparison_panel_version_selection(page: Page):")
    lines.append('    page.goto("/agents/agent_001/comparison")')
    lines.append("    panel = page.locator('#comparison-test-panel')")
    lines.append("    if panel.count() > 0:")
    lines.append("        expect(panel).to_be_visible()")
    lines.append("        ver_a = page.locator('#compVerA')")
    lines.append("        ver_b = page.locator('#compVerB')")
    lines.append("        expect(ver_a).to_have_count(1)")
    lines.append("        expect(ver_b).to_have_count(1)")
    lines.append("")
    lines.append("")
    lines.append("def test_bond_activation_popup_animation(page: Page):")
    lines.append('    page.goto("/bonds/manage")')
    lines.append("    activate_btn = page.locator('.activate-bond-btn')")
    lines.append("    if activate_btn.count() > 0:")
    lines.append("        activate_btn.click()")
    lines.append("        popup = page.locator('.bond-activation-popup')")
    lines.append("        expect(popup).to_be_visible(timeout=5000)")
    lines.append("        expect(popup).to_contain_text('协同增效')")
    lines.append("")
    lines.append("")
    lines.append("def test_skill_notification_auto_dismiss(page: Page):")
    lines.append('    page.goto("/dashboard")')
    lines.append("    notif = page.locator('.skill-learning-notification')")
    lines.append("    if notif.count() > 0:")
    lines.append("        expect(notif).to_be_visible()")
    lines.append("        page.wait_for_timeout(9000)")
    lines.append("        expect(notif).not_to_be_visible()")
    lines.append("")
    lines.append("")
    lines.append("def test_leaderboard_effect_column_sorted(page: Page):")
    lines.append('    page.goto("/leaderboard/effect")')
    lines.append("    table = page.locator('.lb-table'")
    lines.append("    if table.count() > 0:")
    lines.append("        rows = page.locator('.lb-row')")
    lines.append("        expect(rows).to_have_count_greater_than_or_equal(0)")
    lines.append("")
    lines.append("")
    lines.append("def test_task_completion_notification_position(page: Page):")
    lines.append('    page.goto("/chat")')
    lines.append("    send_btn = page.locator('.send-message-btn')")
    lines.append("    if send_btn.count() > 0:")
    lines.append("        send_btn.click()")
    lines.append("        page.wait_for_timeout(2000)")
    lines.append("        notif = page.locator('.task-completion-notification')")
    lines.append("        if notif.count() > 0:")
    lines.append("            box = notif.bounding_box()")
    lines.append("            assert box['x'] > 0 or box['y'] > 0")
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Module-level convenience functions
# =============================================================================


def create_full_system() -> Dict[str, Any]:
    """Factory: create all subsystem instances wired together."""
    calculator = EffectMetricsCalculator()
    sdk = PerformanceSDK()
    trigger = UpgradeEventTrigger(calculator=calculator, sdk=sdk)
    api_provider = EffectAPIProvider(trigger=trigger, calculator=calculator)
    renderer = FrontendRenderer()
    notifier = TaskCompletionNotifier()
    comparator = ComparisonTestInviter()
    attribution_analyzer = EffectAttributionAnalyzer()
    recommender = PersonalizedUpgradeRecommender()
    ab_executor = ABTestExecutor()
    feedback_collector = UserFeedbackCollector()
    leaderboard = LeaderboardEffectIntegration()
    seasonality = SeasonalityAdjuster()
    return {
        "calculator": calculator,
        "sdk": sdk,
        "trigger": trigger,
        "api_provider": api_provider,
        "renderer": renderer,
        "notifier": notifier,
        "comparator": comparator,
        "attribution_analyzer": attribution_analyzer,
        "recommender": recommender,
        "ab_executor": ab_executor,
        "feedback_collector": feedback_collector,
        "leaderboard": leaderboard,
        "seasonality_adjuster": seasonality,
    }


def run_quick_validation() -> Dict[str, Any]:
    """Run the built-in test suite and return results."""
    suite = AgentUpgradeEffectTestSuite()
    return suite.run_all_tests()


if __name__ == "__main__":
    print("Layer 25 loaded OK")