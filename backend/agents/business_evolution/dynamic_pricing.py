"""
动态积分定价智能体
Dynamic Pricing Agent - 根据供需关系动态调整积分获取/消耗规则

户部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import random


class PricingFactor(Enum):
    DEMAND = "demand"
    SUPPLY = "supply"
    TIME = "time"
    USER_SEGMENT = "user_segment"
    TASK_PRIORITY = "task_priority"
    MARKET_CONDITION = "market_condition"


class AdjustmentType(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MULTIPLIER = "multiplier"


@dataclass
class PriceAdjustment:
    adjustment_id: str
    factor: PricingFactor
    adjustment_type: AdjustmentType
    base_value: float
    adjusted_value: float
    reason: str
    valid_from: datetime
    valid_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PricingRule:
    rule_id: str
    task_type: str
    base_points: int
    current_points: int
    min_points: int
    max_points: int
    factors: List[PricingFactor]
    last_adjusted: datetime
    adjustment_history: List[PriceAdjustment] = field(default_factory=list)


@dataclass
class DemandSupplyState:
    task_type: str
    demand_count: int
    supply_count: int
    ratio: float
    timestamp: datetime
    trend: str = "stable"


class DemandAnalyzer:
    def __init__(self):
        self.demand_history: Dict[str, List[Dict]] = {}
        self.demand_thresholds = {
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5,
        }

    def record_demand(self, task_type: str, count: int = 1) -> None:
        if task_type not in self.demand_history:
            self.demand_history[task_type] = []

        self.demand_history[task_type].append(
            {
                "count": count,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def analyze_demand(self, task_type: str, window_hours: int = 24) -> Dict[str, Any]:
        history = self.demand_history.get(task_type, [])
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)

        recent = [
            h
            for h in history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]

        total_demand = sum(h["count"] for h in recent)

        hourly_demand = total_demand / window_hours if window_hours > 0 else 0

        if len(recent) >= 2:
            first_half = sum(h["count"] for h in recent[: len(recent) // 2])
            second_half = sum(h["count"] for h in recent[len(recent) // 2 :])

            if first_half > 0:
                trend = "increasing" if second_half > first_half * 1.2 else "decreasing" if second_half < first_half * 0.8 else "stable"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "task_type": task_type,
            "total_demand": total_demand,
            "hourly_demand": hourly_demand,
            "trend": trend,
            "window_hours": window_hours,
        }


class SupplyAnalyzer:
    def __init__(self):
        self.supply_capacity: Dict[str, int] = {}
        self.current_load: Dict[str, int] = {}

    def set_capacity(self, task_type: str, capacity: int) -> None:
        self.supply_capacity[task_type] = capacity

    def update_load(self, task_type: str, load: int) -> None:
        self.current_load[task_type] = load

    def analyze_supply(self, task_type: str) -> Dict[str, Any]:
        capacity = self.supply_capacity.get(task_type, 100)
        load = self.current_load.get(task_type, 0)

        available = max(0, capacity - load)
        utilization = load / capacity if capacity > 0 else 0

        return {
            "task_type": task_type,
            "total_capacity": capacity,
            "current_load": load,
            "available_capacity": available,
            "utilization_rate": utilization,
        }


class PricingAlgorithm:
    def __init__(self):
        self.elasticity: Dict[str, float] = {}
        self.base_adjustment_rate = 0.1

    def calculate_adjustment(
        self,
        rule: PricingRule,
        demand_state: Dict[str, Any],
        supply_state: Dict[str, Any],
    ) -> PriceAdjustment:
        demand = demand_state.get("hourly_demand", 0)
        supply = supply_state.get("available_capacity", 100)

        if supply > 0:
            ratio = demand / supply
        else:
            ratio = demand

        elasticity = self.elasticity.get(rule.task_type, 1.0)

        if ratio > 2.0:
            adjustment_factor = 1 - self.base_adjustment_rate * elasticity
            reason = "需求过剩，降低积分奖励"
        elif ratio < 0.5:
            adjustment_factor = 1 + self.base_adjustment_rate * elasticity
            reason = "需求不足，提高积分奖励"
        else:
            adjustment_factor = 1.0
            reason = "供需平衡，维持当前积分"

        new_points = int(rule.base_points * adjustment_factor)
        new_points = max(rule.min_points, min(rule.max_points, new_points))

        adjustment_type = (
            AdjustmentType.DECREASE
            if new_points < rule.current_points
            else AdjustmentType.INCREASE
            if new_points > rule.current_points
            else AdjustmentType.MULTIPLIER
        )

        return PriceAdjustment(
            adjustment_id=f"adj_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            factor=PricingFactor.DEMAND,
            adjustment_type=adjustment_type,
            base_value=rule.current_points,
            adjusted_value=new_points,
            reason=reason,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(hours=24),
            metadata={
                "demand_ratio": ratio,
                "elasticity": elasticity,
            },
        )

    def set_elasticity(self, task_type: str, elasticity: float) -> None:
        self.elasticity[task_type] = elasticity


class ABTestingPricing:
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.results: Dict[str, List[Dict]] = {}

    def create_experiment(
        self,
        experiment_id: str,
        control_points: int,
        variant_points: int,
        traffic_split: float = 0.5,
    ) -> None:
        self.experiments[experiment_id] = {
            "control_points": control_points,
            "variant_points": variant_points,
            "traffic_split": traffic_split,
            "status": "running",
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_variant(self, experiment_id: str, user_id: str) -> int:
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment["status"] != "running":
            return None

        user_hash = hash(user_id) % 100 / 100

        if user_hash < experiment["traffic_split"]:
            return experiment["variant_points"]
        else:
            return experiment["control_points"]

    def record_conversion(
        self,
        experiment_id: str,
        variant: str,
        converted: bool,
    ) -> None:
        if experiment_id not in self.results:
            self.results[experiment_id] = []

        self.results[experiment_id].append(
            {
                "variant": variant,
                "converted": converted,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        results = self.results.get(experiment_id, [])
        if not results:
            return {"status": "no_data"}

        variant_stats: Dict[str, Dict] = {}
        for r in results:
            v = r["variant"]
            if v not in variant_stats:
                variant_stats[v] = {"total": 0, "conversions": 0}
            variant_stats[v]["total"] += 1
            if r["converted"]:
                variant_stats[v]["conversions"] += 1

        analysis = {}
        for variant, stats in variant_stats.items():
            analysis[variant] = {
                "conversion_rate": stats["conversions"] / stats["total"],
                "sample_size": stats["total"],
            }

        return {
            "experiment_id": experiment_id,
            "status": self.experiments.get(experiment_id, {}).get("status"),
            "variant_analysis": analysis,
        }


class DynamicPricingAgent:
    def __init__(self, agent_id: str = "dynamic_pricing_001"):
        self.agent_id = agent_id
        self.demand_analyzer = DemandAnalyzer()
        self.supply_analyzer = SupplyAnalyzer()
        self.pricing_algorithm = PricingAlgorithm()
        self.ab_testing = ABTestingPricing()

        self.pricing_rules: Dict[str, PricingRule] = {}
        self.adjustment_history: List[PriceAdjustment] = []

        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        default_rules = [
            ("community_analysis", 10, 5, 20),
            ("price_query", 5, 2, 10),
            ("report_generation", 20, 10, 50),
            ("data_upload", 15, 5, 30),
            ("user_referral", 50, 20, 100),
        ]

        for task_type, base, min_p, max_p in default_rules:
            self.pricing_rules[task_type] = PricingRule(
                rule_id=f"rule_{task_type}",
                task_type=task_type,
                base_points=base,
                current_points=base,
                min_points=min_p,
                max_points=max_p,
                factors=[PricingFactor.DEMAND, PricingFactor.SUPPLY],
                last_adjusted=datetime.utcnow(),
            )

    def record_task_demand(self, task_type: str, count: int = 1) -> None:
        self.demand_analyzer.record_demand(task_type, count)

    def update_supply_capacity(self, task_type: str, capacity: int, load: int = 0) -> None:
        self.supply_analyzer.set_capacity(task_type, capacity)
        self.supply_analyzer.update_load(task_type, load)

    async def adjust_pricing(self, task_type: str) -> Optional[PriceAdjustment]:
        rule = self.pricing_rules.get(task_type)
        if not rule:
            return None

        demand_state = self.demand_analyzer.analyze_demand(task_type)
        supply_state = self.supply_analyzer.analyze_supply(task_type)

        adjustment = self.pricing_algorithm.calculate_adjustment(
            rule, demand_state, supply_state
        )

        rule.current_points = adjustment.adjusted_value
        rule.last_adjusted = datetime.utcnow()
        rule.adjustment_history.append(adjustment)

        self.adjustment_history.append(adjustment)

        return adjustment

    async def adjust_all_pricing(self) -> List[PriceAdjustment]:
        adjustments = []
        for task_type in self.pricing_rules.keys():
            adjustment = await self.adjust_pricing(task_type)
            if adjustment:
                adjustments.append(adjustment)
        return adjustments

    def get_current_points(self, task_type: str) -> int:
        rule = self.pricing_rules.get(task_type)
        return rule.current_points if rule else 0

    def get_points_for_user(
        self, task_type: str, user_id: str = None, experiment_id: str = None
    ) -> int:
        if experiment_id:
            variant_points = self.ab_testing.get_variant(experiment_id, user_id)
            if variant_points:
                return variant_points

        return self.get_current_points(task_type)

    def create_pricing_experiment(
        self,
        experiment_id: str,
        task_type: str,
        variant_points: int,
        traffic_split: float = 0.5,
    ) -> None:
        rule = self.pricing_rules.get(task_type)
        if not rule:
            return

        self.ab_testing.create_experiment(
            experiment_id,
            rule.current_points,
            variant_points,
            traffic_split,
        )

    def record_experiment_conversion(
        self, experiment_id: str, user_id: str, converted: bool
    ) -> None:
        variant = "variant" if hash(user_id) % 100 / 100 < 0.5 else "control"
        self.ab_testing.record_conversion(experiment_id, variant, converted)

    def get_pricing_stats(self) -> Dict[str, Any]:
        return {
            "total_rules": len(self.pricing_rules),
            "current_prices": {
                task_type: rule.current_points
                for task_type, rule in self.pricing_rules.items()
            },
            "total_adjustments": len(self.adjustment_history),
            "active_experiments": len(
                [e for e in self.ab_testing.experiments.values() if e["status"] == "running"]
            ),
        }

    def get_adjustment_history(self, task_type: str = None, limit: int = 10) -> List[Dict]:
        history = self.adjustment_history

        if task_type:
            rule = self.pricing_rules.get(task_type)
            if rule:
                history = rule.adjustment_history

        return [
            {
                "adjustment_id": a.adjustment_id,
                "base_value": a.base_value,
                "adjusted_value": a.adjusted_value,
                "reason": a.reason,
                "timestamp": a.valid_from.isoformat(),
            }
            for a in history[-limit:]
        ]

    def set_elasticity(self, task_type: str, elasticity: float) -> None:
        self.pricing_algorithm.set_elasticity(task_type, elasticity)

    def get_best_deal(self) -> Dict[str, Any]:
        best_task = None
        best_ratio = 0

        for task_type, rule in self.pricing_rules.items():
            ratio = rule.current_points / rule.base_points
            if ratio > best_ratio:
                best_ratio = ratio
                best_task = task_type

        if best_task:
            rule = self.pricing_rules[best_task]
            return {
                "task_type": best_task,
                "current_points": rule.current_points,
                "base_points": rule.base_points,
                "bonus_ratio": best_ratio,
                "message": f"当前{best_task}任务积分奖励最高，比基准高{best_ratio:.0%}",
            }

        return {"message": "暂无特别优惠"}
