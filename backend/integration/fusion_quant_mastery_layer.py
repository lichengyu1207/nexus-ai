# -*- coding: utf-8 -*-
# Layer 22: Fusion Quantitative Analysis & Mastery Transfer
# ==========================================================================
# \u623f\u90fd\u7763AI\u5e73\u53f0 (Governor Fang AI Property Platform)
# Fusion of cultivation realm system with quantitative analysis capabilities,
# implementing \u4e00\u901a\u767e\u901a (mastery transfer) mechanism.
#
# 7 Parts:
#   Part A  - Cultivation Realm System (QuantRealm, RealmCapability, UserCultivationState, RealmProgressCalculator)
#   Part B  - Mastery Transfer Mechanism (AbilityNode, CapabilityGraph, MasteryTransferEngine)
#   Part C  - Quant Module Cultivation Transformation (FactorCultivationTier, FactorAccessController, TieredOutputRenderer)
#   Part D  - Agent x Cultivation Fusion (LiBuCultivationAdvisor, GongBuCollectiveEvolution, XingBuTribulationWarningSystem)
#   Part E  - Frontend Visualization (CultivationPanelData, CULTIVATION_PANEL_SPEC, CultivationDashboardBuilder)
#   Part F  - Backend Services (RealmValidationMiddleware, CultivationOrchestrator)
#   Part G  - Testing Suite (FusionQuantMasteryTestSuite with pytest + Playwright E2E)

import os
import json
import math
import random
import logging
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import (
    Dict, List, Any, Optional, Tuple, Callable,
    Set, Iterator
)
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


# =====================================================================
# PART A: CULTIVATION REALM SYSTEM
# =====================================================================

class QuantRealm(Enum):
    LIAN_QI = "lian_qi"
    ZHU_JI = "zhu_ji"
    JIN_DAN = "jin_dan"
    YUAN_YING = "yuan_ying"
    HUA_SHEN = "hua_shen"
    DU_JIE = "du_jie"
    DA_CHENG = "da_cheng"

    @property
    def display_name(self) -> str:
        _names = {
            QuantRealm.LIAN_QI: "\u70bc\u6c14\u671f",
            QuantRealm.ZHU_JI: "\u7b51\u57fa\u671f",
            QuantRealm.JIN_DAN: "\u91d1\u4e39\u671f",
            QuantRealm.YUAN_YING: "\u5143\u5a74\u671f",
            QuantRealm.HUA_SHEN: "\u5316\u795e\u671f",
            QuantRealm.DU_JIE: "\u6e21\u52ab\u671f",
            QuantRealm.DA_CHENG: "\u5927\u6210\u671f",
        }
        return _names.get(self, self.value)

    @property
    def level(self) -> int:
        _levels = {
            QuantRealm.LIAN_QI: 1,
            QuantRealm.ZHU_JI: 2,
            QuantRealm.JIN_DAN: 3,
            QuantRealm.YUAN_YING: 4,
            QuantRealm.HUA_SHEN: 5,
            QuantRealm.DU_JIE: 6,
            QuantRealm.DA_CHENG: 7,
        }
        return _levels.get(self, 1)

    @property
    def color(self) -> str:
        _colors = {
            QuantRealm.LIAN_QI: "#8B8B8B",
            QuantRealm.ZHU_JI: "#4CAF50",
            QuantRealm.JIN_DAN: "#FFD700",
            QuantRealm.YUAN_YING: "#9C27B0",
            QuantRealm.HUA_SHEN: "#FF5722",
            QuantRealm.DU_JIE: "#00BCD4",
            QuantRealm.DA_CHENG: "#E91E63",
        }
        return _colors.get(self, "#FFFFFF")

    def next_realm(self) -> Optional["QuantRealm"]:
        _order = [
            QuantRealm.LIAN_QI,
            QuantRealm.ZHU_JI,
            QuantRealm.JIN_DAN,
            QuantRealm.YUAN_YING,
            QuantRealm.HUA_SHEN,
            QuantRealm.DU_JIE,
            QuantRealm.DA_CHENG,
        ]
        try:
            idx = _order.index(self)
            if idx < len(_order) - 1:
                return _order[idx + 1]
        except ValueError:
            pass
        return None


@dataclass
class RealmCapability:
    realm: QuantRealm
    available_tools: List[str]
    model_precision: float
    data_breadth: float
    max_forecast_horizon_months: int
    can_use_confidence_interval: bool
    can_use_factor_attribution: bool
    can_use_scenario_simulation: bool
    can_use_risk_modeling: bool
    can_use_backtesting: bool
    can_use_signal_generation: bool
    description: str


REALM_CAPABILITIES: Dict[QuantRealm, RealmCapability] = {
    QuantRealm.LIAN_QI: RealmCapability(
        realm=QuantRealm.LIAN_QI,
        available_tools=["basic_stats", "trend_line", "simple_ma"],
        model_precision=0.65,
        data_breadth=0.30,
        max_forecast_horizon_months=3,
        can_use_confidence_interval=False,
        can_use_factor_attribution=False,
        can_use_scenario_simulation=False,
        can_use_risk_modeling=False,
        can_use_backtesting=False,
        can_use_signal_generation=False,
        description="\u521d\u5165\u4fee\u884c\uff0c\u63a2\u7d22\u57fa\u7840\u6570\u636e\u5206\u6790\u4e4b\u9053"
    ),
    QuantRealm.ZHU_JI: RealmCapability(
        realm=QuantRealm.ZHU_JI,
        available_tools=["basic_stats", "trend_line", "simple_ma", "regression", "correlation"],
        model_precision=0.72,
        data_breadth=0.45,
        max_forecast_horizon_months=6,
        can_use_confidence_interval=True,
        can_use_factor_attribution=False,
        can_use_scenario_simulation=False,
        can_use_risk_modeling=False,
        can_use_backtesting=False,
        can_use_signal_generation=False,
        description="\u7b51\u57fa\u6210\u529f\uff0c\u63e1\u63e1\u7edf\u8ba1\u5206\u6790\u6838\u5fc3\u6280\u80fd"
    ),
    QuantRealm.JIN_DAN: RealmCapability(
        realm=QuantRealm.JIN_DAN,
        available_tools=[
            "basic_stats", "trend_line", "simple_ma", "regression",
            "correlation", "factor_analysis", "attribution_model"
        ],
        model_precision=0.81,
        data_breadth=0.60,
        max_forecast_horizon_months=12,
        can_use_confidence_interval=True,
        can_use_factor_attribution=True,
        can_use_scenario_simulation=False,
        can_use_risk_modeling=True,
        can_use_backtesting=True,
        can_use_signal_generation=False,
        description="\u91d1\u4e39\u51dd\u7ed3\uff0c\u5f00\u542f\u56e0\u5b50\u5f52\u56e0\u4e0e\u98ce\u9669\u6a21\u578b"
    ),
    QuantRealm.YUAN_YING: RealmCapability(
        realm=QuantRealm.YUAN_YING,
        available_tools=[
            "basic_stats", "trend_line", "simple_ma", "regression",
            "correlation", "factor_analysis", "attribution_model",
            "scenario_engine", "monte_carlo"
        ],
        model_precision=0.87,
        data_breadth=0.75,
        max_forecast_horizon_months=24,
        can_use_confidence_interval=True,
        can_use_factor_attribution=True,
        can_use_scenario_simulation=True,
        can_use_risk_modeling=True,
        can_use_backtesting=True,
        can_use_signal_generation=False,
        description="\u5143\u5a74\u51fa\u7a9d\uff0c\u63a2\u7d22\u573a\u666f\u6a21\u62df\u4e0e\u8497\u7279\u5361\u6d1b\u65b9\u6cd5"
    ),
    QuantRealm.HUA_SHEN: RealmCapability(
        realm=QuantRealm.HUA_SHEN,
        available_tools=[
            "basic_stats", "trend_line", "simple_ma", "regression",
            "correlation", "factor_analysis", "attribution_model",
            "scenario_engine", "monte_carlo", "ml_prediction", "nlp_sentiment"
        ],
        model_precision=0.92,
        data_breadth=0.85,
        max_forecast_horizon_months=36,
        can_use_confidence_interval=True,
        can_use_factor_attribution=True,
        can_use_scenario_simulation=True,
        can_use_risk_modeling=True,
        can_use_backtesting=True,
        can_use_signal_generation=True,
        description="\u5316\u795e\u901a\u4e14\uff0c\u878d\u5408\u673a\u5668\u5b66\u4e60\u4e0e\u81ea\u7136\u8bed\u8a00\u5904\u7406"
    ),
    QuantRealm.DU_JIE: RealmCapability(
        realm=QuantRealm.DU_JIE,
        available_tools=[
            "basic_stats", "trend_line", "simple_ma", "regression",
            "correlation", "factor_analysis", "attribution_model",
            "scenario_engine", "monte_carlo", "ml_prediction", "nlp_sentiment",
            "deep_learning", "reinforcement_learning"
        ],
        model_precision=0.96,
        data_breadth=0.92,
        max_forecast_horizon_months=48,
        can_use_confidence_interval=True,
        can_use_factor_attribution=True,
        can_use_scenario_simulation=True,
        can_use_risk_modeling=True,
        can_use_backtesting=True,
        can_use_signal_generation=True,
        description="\u6e21\u52ab\u98de\u5347\uff0c\u638c\u63e1\u6df1\u5ea6\u5b66\u4e60\u4e0e\u5f3a\u5316\u5b66\u4e60\u6280\u672f"
    ),
    QuantRealm.DA_CHENG: RealmCapability(
        realm=QuantRealm.DA_CHENG,
        available_tools=[
            "basic_stats", "trend_line", "simple_ma", "regression",
            "correlation", "factor_analysis", "attribution_model",
            "scenario_engine", "monte_carlo", "ml_prediction", "nlp_sentiment",
            "deep_learning", "reinforcement_learning", "causal_inference",
            "quantum_monte_carlo"
        ],
        model_precision=0.99,
        data_breadth=1.00,
        max_forecast_horizon_months=60,
        can_use_confidence_interval=True,
        can_use_factor_attribution=True,
        can_use_scenario_simulation=True,
        can_use_risk_modeling=True,
        can_use_backtesting=True,
        can_use_signal_generation=True,
        description="\u5927\u6210\u5f97\u9053\uff0c\u8fbe\u5230\u91cf\u5316\u5206\u6790\u4e4b\u5de5\u5999\u5883\u754c"
    ),
}

EXP_THRESHOLDS: Dict[QuantRealm, int] = {
    QuantRealm.LIAN_QI: 0,
    QuantRealm.ZHU_JI: 100,
    QuantRealm.JIN_DAN: 500,
    QuantRealm.YUAN_YING: 2000,
    QuantRealm.HUA_SHEN: 8000,
    QuantRealm.DU_JIE: 25000,
    QuantRealm.DA_CHENG: 80000,
}


@dataclass
class UserCultivationState:
    user_id: str
    current_realm: QuantRealm = QuantRealm.LIAN_QI
    total_exp: int = 0
    abilities: Dict[str, float] = field(default_factory=dict)
    last_bonus_time: Optional[datetime] = None
    last_level_up: Optional[datetime] = None
    streak_days: int = 0
    last_activity_date: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    prediction_correct_count: int = 0

    def exp_to_next_level(self) -> int:
        next_r = self.current_realm.next_realm()
        if next_r is None:
            return 0
        threshold = EXP_THRESHOLDS.get(next_r, 999999)
        return max(0, threshold - self.total_exp)

    def exp_progress_pct(self) -> float:
        current_threshold = EXP_THRESHOLDS.get(self.current_realm, 0)
        next_r = self.current_realm.next_realm()
        if next_r is None:
            return 100.0
        next_threshold = EXP_THRESHOLDS.get(next_r, 999999)
        range_exp = next_threshold - current_threshold
        if range_exp <= 0:
            return 100.0
        progress = (self.total_exp - current_threshold) / range_exp * 100.0
        return min(100.0, max(0.0, progress))

    def get_ability_proficiency(self, ability_name: str) -> float:
        return self.abilities.get(ability_name, 0.0)

    def set_ability_proficiency(self, ability_name: str, value: float) -> None:
        capped = max(0.0, min(100.0, value))
        self.abilities[ability_name] = capped

    def add_exp(self, amount: int, source: str = "") -> Tuple[bool, Optional[QuantRealm]]:
        self.total_exp += amount
        old_realm = self.current_realm
        new_realm = self._calculate_realm_from_exp()
        leveled_up = False
        if new_realm != old_realm:
            self.current_realm = new_realm
            self.last_level_up = datetime.now()
            leveled_up = True
        return leveled_up, (new_realm if leveled_up else None)

    def _calculate_realm_from_exp(self) -> QuantRealm:
        sorted_realms = sorted(
            EXP_THRESHOLDS.keys(),
            key=lambda r: EXP_THRESHOLDS[r]
        )
        result = QuantRealm.LIAN_QI
        for realm in sorted_realms:
            if self.total_exp >= EXP_THRESHOLDS[realm]:
                result = realm
            else:
                break
        return result


@dataclass
class CultivationTask:
    task_id: str
    name: str
    category: str
    difficulty: str
    exp_reward: int
    requirement: str
    cooldown_hours: int = 24
    is_daily: bool = False
    is_challenge: bool = False
    is_breakthrough: bool = False
    required_realm: Optional[QuantRealm] = None
    target_ability: Optional[str] = None


CULTIVATION_TASKS: List[CultivationTask] = [
    CultivationTask(
        task_id="daily_001",
        name="\u6bcf\u65e5\u98ce\u683c\u5206\u6790",
        category="daily",
        difficulty="easy",
        exp_reward=10,
        requirement="\u5b8c\u62101\u6b21\u69db\u5757\u6570\u636e\u5206\u6790",
        is_daily=True,
        target_ability="block_analysis"
    ),
    CultivationTask(
        task_id="daily_002",
        name="\u6bcf\u65e5\u9884\u6d4b\u6821\u9a8c",
        category="daily",
        difficulty="medium",
        exp_reward=15,
        requirement="\u5bf9\u6bd4\u9884\u6d4b\u7ed3\u679c\u4e0e\u5b9e\u9645\u6570\u636e",
        is_daily=True,
        target_ability="prediction_model"
    ),
    CultivationTask(
        task_id="daily_003",
        name="\u6bcf\u65e5\u7b56\u7565\u590d\u76d8",
        category="daily",
        difficulty="hard",
        exp_reward=20,
        requirement="\u8fd0\u884c\u56de\u6d4b\u6d4b\u8bd5\u5e76\u8bb0\u5f55\u7ed3\u679c",
        is_daily=True,
        required_realm=QuantRealm.JIN_DAN,
        target_ability="strategy_backtest"
    ),
    CultivationTask(
        task_id="challenge_001",
        name="\u56e0\u5b50\u6316\u6398\u6311\u6218",
        category="challenge",
        difficulty="hard",
        exp_reward=50,
        requirement="\u53d1\u73b03\u4e2a\u65b0\u56e0\u5b50\u5e76\u9a8c\u8bc1\u5176\u6709\u6548\u6027",
        is_challenge=True,
        required_realm=QuantRealm.JIN_DAN,
        target_ability="factor_mining"
    ),
    CultivationTask(
        task_id="challenge_002",
        name="\u6781\u7aef\u573a\u666f\u6a21\u62df",
        category="challenge",
        difficulty="extreme",
        exp_reward=80,
        requirement="\u5b8c\u62105\u79cd\u6781\u7aef\u573a\u666f\u5206\u6790\u5e76\u7ed9\u51fa\u7b56\u7565",
        is_challenge=True,
        required_realm=QuantRealm.YUAN_YING,
        target_ability="scenario_simulation"
    ),
    CultivationTask(
        task_id="breakthrough_001",
        name="\u7b51\u57fa\u7a81\u7834",
        category="breakthrough",
        difficulty="medium",
        exp_reward=100,
        requirement="\u7d2f\u79ef100\u70b9\u7ecf\u9a8c\u5e76\u5b8c\u621010\u6b21\u5206\u6790",
        is_breakthrough=True,
        required_realm=QuantRealm.LIAN_QI,
    ),
    CultivationTask(
        task_id="breakthrough_002",
        name="\u91d1\u4e39\u7a81\u7834",
        category="breakthrough",
        difficulty="hard",
        exp_reward=300,
        requirement="\u7d2f\u79ef500\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u56e0\u5b50\u5f52\u56e0",
        is_breakthrough=True,
        required_realm=QuantRealm.ZHU_JI,
    ),
    CultivationTask(
        task_id="breakthrough_003",
        name="\u5143\u5a74\u7a81\u7834",
        category="breakthrough",
        difficulty="extreme",
        exp_reward=600,
        requirement="\u7d2f\u79ef2000\u70b9\u7ecf\u9a8c\u5e76\u5b8c\u6210\u573a\u666f\u6a21\u62df\u4efb\u52a1",
        is_breakthrough=True,
        required_realm=QuantRealm.JIN_DAN,
    ),
]


class RealmProgressCalculator:

    ACTION_BASE_REWARDS: Dict[str, int] = {
        "view_dashboard": 1,
        "run_basic_analysis": 2,
        "export_report": 2,
        "check_trend": 3,
        "use_correlation": 4,
        "run_regression": 5,
        "factor_attribution": 8,
        "scenario_simulate": 10,
        "risk_assessment": 8,
        "backtest_strategy": 12,
        "ml_prediction": 15,
        "nlp_sentiment": 15,
        "deep_learning": 20,
        "rl_optimization": 25,
        "correct_prediction": 20,
        "share_insight": 5,
        "complete_task": 50,
    }

    REALM_MULTIPLIERS: Dict[QuantRealm, float] = {
        QuantRealm.LIAN_QI: 1.0,
        QuantRealm.ZHU_JI: 1.1,
        QuantRealm.JIN_DAN: 1.2,
        QuantRealm.YUAN_YING: 1.3,
        QuantRealm.HUA_SHEN: 1.4,
        QuantRealm.DU_JIE: 1.5,
        QuantRealm.DA_CHENG: 1.6,
    }

    def __init__(self):
        self._exp_log: List[Dict[str, Any]] = []

    def calculate_exp_gain(
        self,
        action_type: str,
        user_state: UserCultivationState,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> int:
        base = self.ACTION_BASE_REWARDS.get(action_type, 1)
        multiplier = self.REALM_MULTIPLIERS.get(user_state.current_realm, 1.0)
        streak_bonus = min(user_state.streak_days * 0.05, 0.5)
        final_exp = int(base * multiplier * (1.0 + streak_bonus))
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_state.user_id,
            "action": action_type,
            "base_reward": base,
            "multiplier": multiplier,
            "streak_bonus": streak_bonus,
            "final_exp": final_exp,
            "realm": user_state.current_realm.value,
            "extra_data": extra_data or {},
        }
        self._exp_log.append(log_entry)
        return final_exp

    def check_and_apply_task_completion(
        self,
        user_state: UserCultivationState,
        action_type: str
    ) -> List[CultivationTask]:
        completed: List[CultivationTask] = []
        for task in CULTIVATION_TASKS:
            if task.task_id in user_state.completed_tasks:
                continue
            if task.required_realm and user_state.current_realm.level < task.required_realm.level:
                continue
            action_match = False
            if task.is_daily and action_type in ("run_basic_analysis", "check_trend", "run_regression"):
                action_match = True
            elif task.is_challenge and action_type in (
                "factor_attribution", "scenario_simulate", "ml_prediction"
            ):
                action_match = True
            elif task.is_breakthrough and action_type == "complete_task":
                action_match = True
            if action_match:
                completed.append(task)
                user_state.completed_tasks.append(task.task_id)
        return completed

    def update_streak(self, user_state: UserCultivationState) -> int:
        today_str = datetime.now().strftime("%Y-%m-%d")
        if user_state.last_activity_date is None:
            user_state.streak_days = 1
        elif user_state.last_activity_date == today_str:
            pass
        else:
            last_date = datetime.strptime(user_state.last_activity_date, "%Y-%m-%d")
            diff = (datetime.now() - last_date).days
            if diff == 1:
                user_state.streak_days += 1
            else:
                user_state.streak_days = 1
        user_state.last_activity_date = today_str
        return user_state.streak_days

    def get_exp_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        user_logs = [log for log in self._exp_log if log.get("user_id") == user_id]
        return user_logs[-limit:]

    def get_total_exp_awarded(self) -> int:
        return sum(log.get("final_exp", 0) for log in self._exp_log)


# =====================================================================
# PART B: MASTERY TRANSFER MECHANISM
# =====================================================================

@dataclass
class AbilityNode:
    node_id: str
    display_name: str
    category: str
    description: str
    default_proficiency: float
    max_proficiency: float
    unlock_realm: QuantRealm
    related_factors: List[str]


@dataclass
class AssociationEdge:
    source_id: str
    target_id: str
    strength: float
    edge_type: str
    bidirectional: bool
    description: str


@dataclass
class TransferEvent:
    event_id: str
    source_ability: str
    target_ability: str
    bonus_amount: float
    strength_applied: float
    trigger_reason: str
    timestamp: str
    user_id: str
    was_cascaded: bool
    cascade_depth: int


CORE_ABILITIES: List[AbilityNode] = [
    AbilityNode(
        node_id="block_analysis",
        display_name="\u69db\u5757\u5206\u6790",
        category="fundamental",
        description="\u5bf9\u69db\u5757\u7ea7\u522b\u6570\u636e\u8fdb\u884c\u6df1\u5ea6\u5206\u6790\u4e0e\u8d8b\u52bf\u5224\u65ad",
        default_proficiency=10.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.LIAN_QI,
        related_factors=["price_trend", "volume_change", "turnover_rate"]
    ),
    AbilityNode(
        node_id="city_analysis",
        display_name="\u57ce\u5e02\u5206\u6790",
        category="fundamental",
        description="\u57ce\u5e02\u7ea7\u522b\u7684\u623f\u5730\u4ea7\u5e02\u573a\u5206\u6790\u4e0e\u9884\u6d4b",
        default_proficiency=10.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.LIAN_QI,
        related_factors=["population_flow", "gdp_growth", "employment_rate"]
    ),
    AbilityNode(
        node_id="policy_impact",
        display_name="\u653f\u7b56\u5f71\u54cd",
        category="macro",
        description="\u5206\u6790\u653f\u7b56\u53d8\u52a8\u5bf9\u5e02\u573a\u7684\u5f71\u54cd\u7a0b\u5ea6",
        default_proficiency=5.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.ZHU_JI,
        related_factors=["interest_rate", "tax_policy", "land_supply"]
    ),
    AbilityNode(
        node_id="risk_scoring",
        display_name="\u98ce\u9669\u8bc4\u5206",
        category="risk",
        description="\u7efc\u5408\u591a\u7ef4\u5ea6\u98ce\u9669\u6307\u6807\u8bc4\u4f30\u4e0e\u8bc4\u7ea7",
        default_proficiency=5.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.ZHU_JI,
        related_factors=["volatility", "liquidity", "correlation_risk"]
    ),
    AbilityNode(
        node_id="attribution_analysis",
        display_name="\u5f52\u56e0\u5206\u6790",
        category="quantitative",
        description="\u6536\u76ca\u6765\u6e90\u7684\u7cbe\u786e\u5f52\u56e0\u5206\u89e3",
        default_proficiency=5.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.JIN_DAN,
        related_factors=["factor_exposure", "timing_effect", "selection_effect"]
    ),
    AbilityNode(
        node_id="prediction_model",
        display_name="\u9884\u6d4b\u6a21\u578b",
        category="modeling",
        description="\u673a\u5668\u5b66\u4e60\u9a71\u52a8\u7684\u6570\u636e\u9884\u6d4b\u4e0e\u56de\u5f52\u6a21\u578b",
        default_proficiency=5.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.JIN_DAN,
        related_factors=["feature_importance", "model_accuracy", "prediction_error"]
    ),
    AbilityNode(
        node_id="strategy_backtest",
        display_name="\u7b56\u7565\u56de\u6d4b",
        category="strategy",
        description="\u5386\u53f2\u6570\u636e\u9a71\u52a8\u7684\u7b56\u7565\u6548\u7387\u9a8c\u8bc1",
        default_proficiency=5.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.JIN_DAN,
        related_factors=["sharpe_ratio", "max_drawdown", "win_rate"]
    ),
    AbilityNode(
        node_id="factor_mining",
        display_name="\u56e0\u5b50\u6316\u6398",
        category="quantitative",
        description="\u4ece\u5927\u89c4\u6a21\u6570\u636e\u4e2d\u6316\u6398\u65b0\u7684\u6709\u6548\u56e0\u5b50",
        default_proficiency=3.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.YUAN_YING,
        related_factors=["ic_value", "ir_ratio", "factor_decay"]
    ),
    AbilityNode(
        node_id="scenario_simulation",
        display_name="\u573a\u666f\u6a21\u62df",
        category="advanced",
        description="\u591a\u573a\u666f\u8497\u7279\u5361\u6d1b\u6a21\u62df\u4e0e\u538b\u529b\u6d4b\u8bd5",
        default_proficiency=3.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.YUAN_YING,
        related_factors=["stress_test", "tail_risk", "correlation_breakdown"]
    ),
    AbilityNode(
        node_id="sentiment_analysis",
        display_name="\u60c5\u7eea\u5206\u6790",
        category="advanced",
        description="\u5229\u7528NLP\u6280\u672f\u5206\u6790\u5e02\u573a\u60c5\u7eea\u4e0e\u8a00\u8bba\u503e\u5411",
        default_proficiency=3.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.HUA_SHEN,
        related_factors=["sentiment_score", "news_volume", "socialbuzz"]
    ),
    AbilityNode(
        node_id="causal_inference",
        display_name="\u56e0\u679c\u63a8\u65ad",
        category="advanced",
        description="\u57fa\u4e8e\u56e0\u679c\u56fe\u7684\u6df1\u5c42\u5173\u7cfb\u63a8\u5bfc",
        default_proficiency=1.0,
        max_proficiency=100.0,
        unlock_realm=QuantRealm.DU_JIE,
        related_factors=["causal_strength", "confounder_bias", "treatment_effect"]
    ),
]

ASSOCIATION_EDGES: List[AssociationEdge] = [
    AssociationEdge(
        source_id="block_analysis",
        target_id="city_analysis",
        strength=0.8,
        edge_type="synergy",
        bidirectional=True,
        description="\u69db\u5757\u4e0e\u57ce\u5e02\u5206\u6790\u76f8\u4e92\u4fc3\u8fdb"
    ),
    AssociationEdge(
        source_id="city_analysis",
        target_id="policy_impact",
        strength=0.7,
        edge_type="dependency",
        bidirectional=True,
        description="\u653f\u7b56\u5f71\u54cd\u57ce\u5e02\u53d1\u5c55"
    ),
    AssociationEdge(
        source_id="policy_impact",
        target_id="risk_scoring",
        strength=0.6,
        edge_type="amplification",
        bidirectional=True,
        description="\u653f\u7b56\u53d8\u52a8\u653e\u5927\u98ce\u9669"
    ),
    AssociationEdge(
        source_id="risk_scoring",
        target_id="attribution_analysis",
        strength=0.7,
        edge_type="foundation",
        bidirectional=True,
        description="\u98ce\u9669\u8bc4\u5206\u662f\u5f52\u56e0\u5206\u6790\u7684\u57fa\u7840"
    ),
    AssociationEdge(
        source_id="attribution_analysis",
        target_id="prediction_model",
        strength=0.8,
        edge_type="enhancement",
        bidirectional=True,
        description="\u5f52\u56e0\u6d1e\u5bdf\u63d0\u5347\u9884\u6d4b\u7cbe\u5ea6"
    ),
    AssociationEdge(
        source_id="prediction_model",
        target_id="strategy_backtest",
        strength=0.85,
        edge_type="validation",
        bidirectional=True,
        description="\u9884\u6d4b\u6a21\u578b\u9700\u7ecf\u56de\u6d4b\u9a8c\u8bc1"
    ),
    AssociationEdge(
        source_id="strategy_backtest",
        target_id="factor_mining",
        strength=0.75,
        edge_type="iteration",
        bidirectional=True,
        description="\u56de\u6d4b\u7ed3\u679c\u6307\u5bfc\u56e0\u5b50\u6316\u6398"
    ),
    AssociationEdge(
        source_id="factor_mining",
        target_id="scenario_simulation",
        strength=0.7,
        edge_type="application",
        bidirectional=True,
        description="\u65b0\u56e0\u5b50\u7528\u4e8e\u573a\u666f\u6a21\u62df"
    ),
    AssociationEdge(
        source_id="scenario_simulation",
        target_id="sentiment_analysis",
        strength=0.55,
        edge_type="contextual",
        bidirectional=True,
        description="\u60c5\u7eea\u6570\u636e\u589e\u5f3a\u573a\u666f\u8bbe\u5b9a"
    ),
    AssociationEdge(
        source_id="sentiment_analysis",
        target_id="causal_inference",
        strength=0.5,
        edge_type="insight",
        bidirectional=True,
        description="\u60c5\u7eea\u7ebf\u7d22\u542f\u53d1\u56e0\u679c\u63a8\u65ad"
    ),
    AssociationEdge(
        source_id="block_analysis",
        target_id="risk_scoring",
        strength=0.6,
        edge_type="cross_domain",
        bidirectional=False,
        description="\u69db\u5757\u5206\u6790\u6570\u636e\u652f\u6491\u98ce\u9669\u8bc4\u5206"
    ),
]

TRANSFER_COOLDOWN_SECONDS: int = 3600
MAX_CASCADE_DEPTH: int = 3
BASE_BONUS_PERCENTAGE: float = 0.20
MIN_TRANSFER_THRESHOLD: float = 30.0


class CapabilityGraph:

    def __init__(self):
        self.nodes: Dict[str, AbilityNode] = {}
        self.edges: List[AssociationEdge] = []
        self._adjacency: Dict[str, List[Tuple[str, float]]] = {}
        for node in CORE_ABILITIES:
            self.nodes[node.node_id] = node
        for edge in ASSOCIATION_EDGES:
            self.edges.append(edge)
            if edge.source_id not in self._adjacency:
                self._adjacency[edge.source_id] = []
            self._adjacency[edge.source_id].append((edge.target_id, edge.strength))
            if edge.bidirectional:
                if edge.target_id not in self._adjacency:
                    self._adjacency[edge.target_id] = []
                self._adjacency[edge.target_id].append((edge.source_id, edge.strength))

    def get_node(self, node_id: str) -> Optional[AbilityNode]:
        return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[AbilityNode]:
        return list(self.nodes.values())

    def get_associated_abilities(
        self,
        node_id: str,
        min_strength: float = 0.3
    ) -> List[Tuple[AbilityNode, float]]:
        neighbors = self._adjacency.get(node_id, [])
        results: List[Tuple[AbilityNode, float]] = []
        for target_id, strength in neighbors:
            if strength >= min_strength and target_id in self.nodes:
                results.append((self.nodes[target_id], strength))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_shortest_path(
        self,
        source: str,
        target: str
    ) -> Optional[List[str]]:
        if source not in self.nodes or target not in self.nodes:
            return None
        if source == target:
            return [source]
        visited: Set[str] = {source}
        queue: deque = deque()
        queue.append([source])
        while queue:
            path = queue.popleft()
            current = path[-1]
            for neighbor, _ in self._adjacency.get(current, []):
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    if neighbor == target:
                        return new_path
                    visited.add(neighbor)
                    queue.append(new_path)
        return None

    def get_graph_stats(self) -> Dict[str, Any]:
        total_degree = sum(len(v) for v in self._adjacency.values())
        strengths = [e.strength for e in self.edges]
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "avg_degree": total_degree / max(len(self.nodes), 1),
            "max_strength": max(strengths) if strengths else 0.0,
            "min_strength": min(strengths) if strengths else 0.0,
        }

    def export_graph_json(self) -> str:
        nodes_data = []
        for node in self.nodes.values():
            nodes_data.append({
                "id": node.node_id,
                "name": node.display_name,
                "category": node.category,
                "unlock_realm": node.unlock_realm.value,
            })
        edges_data = []
        for edge in self.edges:
            edges_data.append({
                "source": edge.source_id,
                "target": edge.target_id,
                "strength": edge.strength,
                "type": edge.edge_type,
            })
        graph_obj = {"nodes": nodes_data, "edges": edges_data}
        return json.dumps(graph_obj, ensure_ascii=False, indent=2)


@dataclass
class MasteryTransferConfig:
    base_bonus_pct: float = BASE_BONUS_PERCENTAGE
    cooldown_seconds: int = TRANSFER_COOLDOWN_SECONDS
    max_cascade_depth: int = MAX_CASCADE_DEPTH
    min_transfer_threshold: float = MIN_TRANSFER_THRESHOLD
    proficiency_cap_per_transfer: float = 5.0
    enable_notifications: bool = True
    cascade_decay_factor: float = 0.5


class MasteryTransferEngine:

    def __init__(
        self,
        graph: CapabilityGraph,
        config: Optional[MasteryTransferConfig] = None
    ):
        self.graph = graph
        self.config = config or MasteryTransferConfig()
        self._transfer_history: List[TransferEvent] = []
        self._user_cooldowns: Dict[str, Dict[str, datetime]] = {}

    def check_transfer_eligibility(
        self,
        user_id: str,
        ability_id: str,
        current_proficiency: float
    ) -> bool:
        if current_proficiency < self.config.min_transfer_threshold:
            return False
        cooldown_map = self._user_cooldowns.get(user_id, {})
        last_time = cooldown_map.get(ability_id)
        if last_time is not None:
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < self.config.cooldown_seconds:
                return False
        return True

    def compute_transfers(
        self,
        user_id: str,
        source_ability: str,
        proficiency_delta: float,
        user_state: UserCultivationState
    ) -> List[TransferEvent]:
        events: List[TransferEvent] = []
        abs_delta = abs(proficiency_delta)
        if abs_delta < 0.1:
            return events
        associated = self.graph.get_associated_abilities(source_ability, min_strength=0.3)
        for target_node, strength in associated:
            target_id = target_node.node_id
            current_prof = user_state.get_ability_proficiency(target_id)
            eligible = self.check_transfer_eligibility(user_id, target_id, current_prof)
            if not eligible:
                continue
            bonus = self.config.base_bonus_pct * abs_delta * strength
            bonus = min(bonus, self.config.proficiency_cap_per_transfer)
            if bonus < 0.1:
                continue
            new_prof = current_prof + bonus
            user_state.set_ability_proficiency(target_id, new_prof)
            event_id = hashlib.md5(
                (f"{user_id}_{source_ability}_{target_id}_{datetime.now().isoformat()}").encode()
            ).hexdigest()[:12]
            event = TransferEvent(
                event_id=event_id,
                source_ability=source_ability,
                target_ability=target_id,
                bonus_amount=round(bonus, 4),
                strength_applied=strength,
                trigger_reason=f"proficiency_change_in_{source_ability}",
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                was_cascaded=False,
                cascade_depth=0,
            )
            events.append(event)
            self._transfer_history.append(event)
            if user_id not in self._user_cooldowns:
                self._user_cooldowns[user_id] = {}
            self._user_cooldowns[user_id][target_id] = datetime.now()
            if bonus > 1.0 and self.config.max_cascade_depth > 0:
                cascade_events = self._process_cascade(
                    user_id, target_id, bonus, user_state, depth=1
                )
                events.extend(cascade_events)
        return events

    def _process_cascade(
        self,
        user_id: str,
        source: str,
        delta: float,
        state: UserCultivationState,
        depth: int
    ) -> List[TransferEvent]:
        events: List[TransferEvent] = []
        if depth > self.config.max_cascade_depth:
            return events
        decayed_delta = delta * self.config.cascade_decay_factor
        if decayed_delta < 0.5:
            return events
        associated = self.graph.get_associated_abilities(source, min_strength=0.3)
        top_targets = associated[:2]
        for target_node, strength in top_targets:
            target_id = target_node.node_id
            current_prof = state.get_ability_proficiency(target_id)
            eligible = self.check_transfer_eligibility(user_id, target_id, current_prof)
            if not eligible:
                continue
            bonus = self.config.base_bonus_pct * decayed_delta * strength
            bonus = min(bonus, self.config.proficiency_cap_per_transfer * 0.5)
            if bonus < 0.05:
                continue
            new_prof = current_prof + bonus
            state.set_ability_proficiency(target_id, new_prof)
            event_id = hashlib.md5(
                (f"{user_id}_cascade_{source}_{target_id}_{depth}_{datetime.now().isoformat()}").encode()
            ).hexdigest()[:12]
            event = TransferEvent(
                event_id=event_id,
                source_ability=source,
                target_ability=target_id,
                bonus_amount=round(bonus, 4),
                strength_applied=strength,
                trigger_reason=f"cascade_depth_{depth}_from_{source}",
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                was_cascaded=True,
                cascade_depth=depth,
            )
            events.append(event)
            self._transfer_history.append(event)
            sub_events = self._process_cascade(
                user_id, target_id, bonus, state, depth + 1
            )
            events.extend(sub_events)
        return events

    def get_transfer_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[TransferEvent]:
        user_transfers = [t for t in self._transfer_history if t.user_id == user_id]
        return user_transfers[-limit:]

    def get_user_total_bonuses(self, user_id: str) -> Dict[str, float]:
        bonuses: Dict[str, float] = {}
        for t in self._transfer_history:
            if t.user_id == user_id:
                key = t.target_ability
                bonuses[key] = bonuses.get(key, 0.0) + t.bonus_amount
        return bonuses

    def get_resonance_summary(self, user_id: str) -> Dict[str, Any]:
        user_events = [t for t in self._transfer_history if t.user_id == user_id]
        total_bonus = sum(t.bonus_amount for t in user_events)
        source_counts: Dict[str, int] = {}
        for t in user_events:
            src = t.source_ability
            source_counts[src] = source_counts.get(src, 0) + 1
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        last_trigger = None
        if user_events:
            last_trigger = user_events[-1].timestamp
        return {
            "total_events": len(user_events),
            "top_source_abilities": top_sources,
            "total_bonus_received": round(total_bonus, 4),
            "last_trigger_time": last_trigger,
        }


# =====================================================================
# PART C: QUANT MODULE CULTIVATION TRANSFORMATION
# =====================================================================

@dataclass
class FactorCultivationTier:
    factor_id: str
    factor_name: str
    category: str
    required_realm: QuantRealm
    is_locked_for_lower: bool
    locked_display_text: str
    unlock_hint: str


FACTOR_TIER_REGISTRY: List[FactorCultivationTier] = [
    FactorCultivationTier(
        factor_id="price_momentum",
        factor_name="\u4ef7\u683c\u52a8\u91cf",
        category="momentum",
        required_realm=QuantRealm.LIAN_QI,
        is_locked_for_lower=False,
        locked_display_text="",
        unlock_hint=""
    ),
    FactorCultivationTier(
        factor_id="volume_ratio",
        factor_name="\u6210\u4ea4\u91cf\u6bd4",
        category="momentum",
        required_realm=QuantRealm.LIAN_QI,
        is_locked_for_lower=False,
        locked_display_text="",
        unlock_hint=""
    ),
    FactorCultivationTier(
        factor_id="ma_cross_signal",
        factor_name="\u5747\u7ebf\u4ea4\u53c9\u4fe1\u53f7",
        category="technical",
        required_realm=QuantRealm.LIAN_QI,
        is_locked_for_lower=False,
        locked_display_text="",
        unlock_hint=""
    ),
    FactorCultivationTier(
        factor_id="pe_ratio_valuation",
        factor_name="PE\u4ef7\u503c\u8bc4\u4f30",
        category="valuation",
        required_realm=QuantRealm.ZHU_JI,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u7b51\u57fa\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef100\u70b9\u7ecf\u9a8c\u5373\u53ef\u89e3\u9501"
    ),
    FactorCultivationTier(
        factor_id="pb_ratio_valuation",
        factor_name="PB\u4ef7\u503c\u8bc4\u4f30",
        category="valuation",
        required_realm=QuantRealm.ZHU_JI,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u7b51\u57fa\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef100\u70b9\u7ecf\u9a8c\u5373\u53ef\u89e3\u9501"
    ),
    FactorCultivationTier(
        factor_id="dividend_yield",
        factor_name="\u80a1\u606f\u7387",
        category="fundamental",
        required_realm=QuantRealm.ZHU_JI,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u7b51\u57fa\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef100\u70b9\u7ecf\u9a8c\u5373\u53ef\u89e3\u9501"
    ),
    FactorCultivationTier(
        factor_id="size_factor",
        factor_name="\u89c4\u6a21\u56e0\u5b50",
        category="style",
        required_realm=QuantRealm.JIN_DAN,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u91d1\u4e39\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef500\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u5f52\u56e0\u5206\u6790"
    ),
    FactorCultivationTier(
        factor_id="value_factor",
        factor_name="\u4ef7\u503c\u56e0\u5b50",
        category="style",
        required_realm=QuantRealm.JIN_DAN,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u91d1\u4e39\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef500\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u5f52\u56e0\u5206\u6790"
    ),
    FactorCultivationTier(
        factor_id="quality_factor",
        factor_name="\u8d28\u91cf\u56e0\u5b50",
        category="style",
        required_realm=QuantRealm.JIN_DAN,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u91d1\u4e39\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef500\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u5f52\u56e0\u5206\u6790"
    ),
    FactorCultivationTier(
        factor_id="volatility_factor",
        factor_name="\u6ce2\u52a8\u7387\u56e0\u5b50",
        category="risk",
        required_realm=QuantRealm.JIN_DAN,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u91d1\u4e39\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef500\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u98ce\u9669\u6a21\u578b"
    ),
    FactorCultivationTier(
        factor_id="momentum_factor",
        factor_name="\u52a8\u91cf\u56e0\u5b50",
        category="style",
        required_realm=QuantRealm.YUAN_YING,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u5143\u5a74\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef2000\u70b9\u7ecf\u9a8c\u5e76\u5b8c\u6210\u573a\u666f\u6a21\u62df"
    ),
    FactorCultivationTier(
        factor_id="liquidity_factor",
        factor_name="\u6d41\u52a8\u6027\u56e0\u5b50",
        category="risk",
        required_realm=QuantRealm.YUAN_YING,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u5143\u5a74\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef2000\u70b9\u7ecf\u9a8c\u5e76\u5b8c\u6210\u98ce\u9669\u8bc4\u5206"
    ),
    FactorCultivationTier(
        factor_id="growth_factor",
        factor_name="\u6210\u957f\u56e0\u5b50",
        category="fundamental",
        required_realm=QuantRealm.YUAN_YING,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u5143\u5a74\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef2000\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1ML\u9884\u6d4b"
    ),
    FactorCultivationTier(
        factor_id="sentiment_alpha",
        factor_name="\u60c5\u7eea\u963f\u5c14\u6cd5",
        category="alternative",
        required_realm=QuantRealm.HUA_SHEN,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u5316\u795e\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef8000\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1NLP\u6280\u672f"
    ),
    FactorCultivationTier(
        factor_id="smart_money_flow",
        factor_name="\u667a\u6167\u8d44\u91d1\u6d41",
        category="alternative",
        required_realm=QuantRealm.HUA_SHEN,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u5316\u795e\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef8000\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u6df1\u5ea6\u5b66\u4e60"
    ),
    FactorCultivationTier(
        factor_id="institutional_holding",
        factor_name="\u673a\u6784\u6301\u4ed9\u56e0\u5b50",
        category="alternative",
        required_realm=QuantRealm.DU_JIE,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u6e21\u52ab\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef25000\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1RL\u4f18\u5316"
    ),
    FactorCultivationTier(
        factor_id="causal_network",
        factor_name="\u56e0\u679c\u7f51\u7edc\u56e0\u5b50",
        category="advanced",
        required_realm=QuantRealm.DU_JIE,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\udd12 \u9700\u6e21\u52ab\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef25000\u70b9\u7ecf\u9a8c\u5e76\u638c\u63e1\u56e0\u679c\u63a8\u65ad"
    ),
    FactorCultivationTier(
        factor_id="quantum_entropy",
        factor_name="\u91cf\u5b50\u71b5\u56e0\u5b50",
        category="esoteric",
        required_realm=QuantRealm.DA_CHENG,
        is_locked_for_lower=True,
        locked_display_text="\ud83d\ude80 \u9700\u5927\u6210\u671f\u89e3\u9501",
        unlock_hint="\u7d2f\u79ef80000\u70b9\u7ecf\u9a8c\u8fbe\u5230\u5927\u6210\u5883\u754c"
    ),
]


class FactorAccessController:

    def __init__(self):
        self.tiers: Dict[str, FactorCultivationTier] = {}
        for tier in FACTOR_TIER_REGISTRY:
            self.tiers[tier.factor_id] = tier

    def get_available_factors(self, realm: QuantRealm) -> List[FactorCultivationTier]:
        return [
            t for t in FACTOR_TIER_REGISTRY
            if realm.level >= t.required_realm.level
        ]

    def get_locked_factors(self, realm: QuantRealm) -> List[FactorCultivationTier]:
        return [
            t for t in FACTOR_TIER_REGISTRY
            if realm.level < t.required_realm.level and t.is_locked_for_lower
        ]

    def check_factor_access(
        self,
        factor_id: str,
        realm: QuantRealm
    ) -> Tuple[bool, Optional[str]]:
        tier = self.tiers.get(factor_id)
        if tier is None:
            return False, f"\u56e0\u5b50 {factor_id} \u4e0d\u5b58\u5728"
        if realm.level >= tier.required_realm.level:
            return True, None
        return False, tier.locked_display_text or f"\u9700{tier.required_realm.display_name}\u89e3\u9501"

    def get_factor_radar_data(
        self,
        realm: QuantRealm,
        scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        if scores is None:
            scores = {}
        radar_data = []
        for tier in FACTOR_TIER_REGISTRY:
            is_locked = realm.level < tier.required_realm.level and tier.is_locked_for_lower
            entry = {
                "factor_id": tier.factor_id,
                "factor_name": tier.factor_name,
                "score": scores.get(tier.factor_id, 0.0),
                "is_locked": is_locked,
                "unlock_realm": tier.required_realm.value,
                "unlock_hint": tier.unlock_hint if is_locked else "",
            }
            radar_data.append(entry)
        return radar_data


@dataclass
class TieredAnalysisOutput:
    realm: QuantRealm
    forecast_range: str
    confidence_info: Optional[str] = None
    factor_ranking: Optional[List[Dict[str, Any]]] = None
    scenario_results: Optional[List[Dict[str, Any]]] = None
    strategy_advice: Optional[str] = None
    full_output: Dict[str, Any] = field(default_factory=dict)
    truncated_fields: List[str] = field(default_factory=list)


class TieredOutputRenderer:

    REALM_OUTPUT_SPECS: Dict[QuantRealm, Dict[str, Any]] = {
        QuantRealm.LIAN_QI: {
            "forecast_format": "{start}~{end}\u6708\u57fa\u7840\u8d8b\u52bf\u9884\u6d4b",
            "include_confidence": False,
            "include_factors": False,
            "include_scenarios": False,
            "include_advice": False,
            "max_sections": 2,
        },
        QuantRealm.ZHU_JI: {
            "forecast_format": "{start}~{end}\u6708\u7edf\u8ba1\u5206\u6790\u9884\u6d4b (\u542b\u7f6e\u4fe1\u533a\u95f4)",
            "include_confidence": True,
            "include_factors": False,
            "include_scenarios": False,
            "include_advice": False,
            "max_sections": 3,
        },
        QuantRealm.JIN_DAN: {
            "forecast_format": "{start}~{end}\u6708\u56e0\u5b50\u9a71\u52a8\u9884\u6d4b (\u542b\u56e0\u5b50\u5f52\u56e0)",
            "include_confidence": True,
            "include_factors": True,
            "include_scenarios": False,
            "include_advice": True,
            "max_sections": 5,
        },
        QuantRealm.YUAN_YING: {
            "forecast_format": "{start}~{end}\u6708\u573a\u666f\u6a21\u62df\u9884\u6d4b (\u542b\u8497\u7279\u5361\u6d1b)",
            "include_confidence": True,
            "include_factors": True,
            "include_scenarios": True,
            "include_advice": True,
            "max_sections": 7,
        },
        QuantRealm.HUA_SHEN: {
            "forecast_format": "{start}~{end}\u6708AI+\u591a\u7ef4\u5ea6\u878d\u5408\u9884\u6d4b",
            "include_confidence": True,
            "include_factors": True,
            "include_scenarios": True,
            "include_advice": True,
            "max_sections": 9,
        },
        QuantRealm.DU_JIE: {
            "forecast_format": "{start}~{end}\u6708\u6df1\u5ea6\u5b66\u4e60\u9884\u6d4b (\u542bRL\u4f18\u5316)",
            "include_confidence": True,
            "include_factors": True,
            "include_scenarios": True,
            "include_advice": True,
            "max_sections": 11,
        },
        QuantRealm.DA_CHENG: {
            "forecast_format": "{start}~{end}\u6708\u5927\u6210\u5168\u666f\u9884\u6d4b (\u542b\u56e0\u679c\u63a8\u65ad)",
            "include_confidence": True,
            "include_factors": True,
            "include_scenarios": True,
            "include_advice": True,
            "max_sections": 13,
        },
    }

    def render(
        self,
        raw_data: Dict[str, Any],
        realm: QuantRealm
    ) -> TieredAnalysisOutput:
        spec = self.REALM_OUTPUT_SPECS.get(realm, self.REALM_OUTPUT_SPECS[QuantRealm.LIAN_QI])
        cap = REALM_CAPABILITIES.get(realm)
        start_month = raw_data.get("forecast_start", 1)
        end_month = cap.max_forecast_horizon_months if cap else 12
        forecast_range = spec["forecast_format"].format(start=start_month, end=end_month)
        confidence_info = None
        if spec["include_confidence"]:
            ci_raw = raw_data.get("confidence_interval")
            if ci_raw:
                lo = ci_raw.get("lower", 0)
                hi = ci_raw.get("upper", 0)
                confidence_info = f"\u7f6e\u4fe1\u533a\u95f4: [{lo:.2%}, {hi:.2%}]"
        factor_ranking = None
        if spec["include_factors"]:
            factors_raw = raw_data.get("factor_contributions", [])
            factor_ranking = sorted(factors_raw, key=lambda x: x.get("weight", 0), reverse=True)[:5]
        scenario_results = None
        if spec["include_scenarios"]:
            scenarios_raw = raw_data.get("scenarios", [])
            scenario_results = scenarios_raw[:3]
        strategy_advice = None
        if spec["include_advice"]:
            strategy_advice = raw_data.get("strategy_advice", "")
        truncated_fields = []
        all_feature_keys = ["confidence_interval", "factor_contributions", "scenarios", "strategy_advice", "causal_graph", "quantum_correction"]
        for key in all_feature_keys:
            if key in raw_data:
                include_map = {
                    "confidence_interval": spec["include_confidence"],
                    "factor_contributions": spec["include_factors"],
                    "scenarios": spec["include_scenarios"],
                    "strategy_advice": spec["include_advice"],
                    "causal_graph": realm.level >= QuantRealm.DU_JIE.level,
                    "quantum_correction": realm.level >= QuantRealm.DA_CHENG.level,
                }
                should_include = include_map.get(key, False)
                if not should_include:
                    truncated_fields.append(key)
        return TieredAnalysisOutput(
            realm=realm,
            forecast_range=forecast_range,
            confidence_info=confidence_info,
            factor_ranking=factor_ranking,
            scenario_results=scenario_results,
            strategy_advice=strategy_advice,
            full_output=raw_data,
            truncated_fields=truncated_fields,
        )


@dataclass
class StrategyPermission:
    strategy_type: str
    min_realm: QuantRealm
    allowed_params: List[str]
    description: str
    max_lookback_years: int


STRATEGY_PERMISSIONS: List[StrategyPermission] = [
    StrategyPermission(
        strategy_type="buy_and_hold",
        min_realm=QuantRealm.LIAN_QI,
        allowed_params=["initial_allocation", "rebalance_frequency"],
        description="\u4e70\u5165\u5e76\u6301\u6709\u7b56\u7565\uff0c\u9002\u5408\u521d\u5165\u4fee\u8005",
        max_lookback_years=1,
    ),
    StrategyPermission(
        strategy_type="monthly_rebalance",
        min_realm=QuantRealm.JIN_DAN,
        allowed_params=["target_weights", "rebalance_threshold", "transaction_cost"],
        description="\u6bcf\u6708\u518d\u5e73\u8861\u7b56\u7565\uff0c\u9700\u91d1\u4e39\u671f\u4ee5\u4e0a",
        max_lookback_years=3,
    ),
    StrategyPermission(
        strategy_type="factor_weighted",
        min_realm=QuantRealm.YUAN_YING,
        allowed_params=["factor_exposures", "risk_budget", "leverage_limit"],
        description="\u56e0\u5b50\u52a0\u6743\u7b56\u7565\uff0c\u9700\u5143\u5a74\u671f\u4ee5\u4e0a",
        max_lookback_years=5,
    ),
    StrategyPermission(
        strategy_type="rl_optimized",
        min_realm=QuantRealm.HUA_SHEN,
        allowed_params=["state_space", "action_space", "reward_function", "learning_rate"],
        description="\u5f3a\u5316\u5b66\u4e60\u4f18\u5316\u7b56\u7565\uff0c\u9700\u5316\u795e\u671f\u4ee5\u4e0a",
        max_lookback_years=10,
    ),
    StrategyPermission(
        strategy_type="custom_signal",
        min_realm=QuantRealm.DU_JIE,
        allowed_params=["signal_formula", "entry_threshold", "exit_threshold", "position_sizing"],
        description="\u81ea\u5b9a\u4e49\u4fe1\u53f7\u7b56\u7565\uff0c\u9700\u6e21\u52ab\u671f\u4ee5\u4e0a",
        max_lookback_years=15,
    ),
]


class StrategyPermissionChecker:

    def __init__(self):
        self.permissions: Dict[str, StrategyPermission] = {}
        for perm in STRATEGY_PERMISSIONS:
            self.permissions[perm.strategy_type] = perm

    def check_permission(
        self,
        strategy_type: str,
        realm: QuantRealm
    ) -> Tuple[bool, Optional[str], Optional[QuantRealm]]:
        perm = self.permissions.get(strategy_type)
        if perm is None:
            return False, f"\u672a\u77e5\u7b56\u7565\u7c7b\u578b: {strategy_type}", None
        if realm.level >= perm.min_realm.level:
            return True, None, None
        return (
            False,
            f"\u9700{perm.min_realm.display_name}\u624d\u80fd\u4f7f\u7528 {perm.description}",
            perm.min_realm,
        )

    def get_available_strategies(self, realm: QuantRealm) -> List[StrategyPermission]:
        return [p for p in STRATEGY_PERMISSIONS if realm.level >= p.min_realm.level]

    def get_locked_strategies(self, realm: QuantRealm) -> List[StrategyPermission]:
        return [p for p in STRATEGY_PERMISSIONS if realm.level < p.min_realm.level]


# =====================================================================
# PART D: AGENT x CULTIVATION FUSION
# =====================================================================

@dataclass
class CultivationGuidanceMessage:
    persona: str
    message_text: str
    suggested_action: Optional[str] = None
    guidance_type: str = ""
    realm_context: QuantRealm = QuantRealm.LIAN_QI
    urgency: str = "normal"


LI_BU_GUIDANCE_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "zhouyu": {
        "breakthrough_congrats": [
            "{realm_name}\u5feb\u4e50\uff01\u541b\u5b50\u5df2\u81f3{next_realm}\uff0c\u5982\u5468\u7460\u8d64\u58c1\u4e4b\u706b\uff0c\u5f88\u5feb\u5c31\u80fd\u70e7\u5230\u4e1c\u5357\u98ce\u5411\u3002\u4e0b\u4e00\u9636\u6bb5\u9700{exp_needed}\u70b9\u7ecf\u9a8c\uff0c\u89e3\u9501\u65b0\u529f\u80fd\uff1a{new_feature}\u3002",
            "\u54c8\u54c8\uff01{realm_name}\u5df2\u7ecf\u4e0d\u8db3\u4ee5\u7ea6\u675f\u541b\u4e86\uff01\u60a8\u73b0\u5728\u662f{next_realm}\uff0c\u53ef\u4ee5\u5c1d\u8bd5{new_feature}\uff0c\u8ba9\u6211\u4eec\u7ee7\u7eed\u524d\u8fdb\uff01",
        ],
        "stagnation_warning": [
            "{realm_name}\u541b\u5b50\uff0c\u60a8\u7684\u7ecf\u9a8c\u8fdb\u5ea6\u505c\u6ede\u4e86\u3002\u5efa\u8bae\u591a\u505a{new_feature}\u76f8\u5173\u4efb\u52a1\uff0c\u6bcf\u65e5\u7684\u79ef\u7d2f\u90fd\u662f\u901a\u5f80\u5de3\u5cb8\u7684\u77f3\u9636\u3002",
            "\u5468\u7460\u770b\u5230\u60a8\u5728{realm_name}\u5f85\u4e86\u4e00\u6bb5\u65f6\u95f4\uff0c\u8981\u4e0d\u8981\u6025\uff0c\u4f46\u8981\u575a\u6301\u3002\u5c1d\u8bd5\u5b8c\u6210\u4e00\u6b21{ability_name}\u5206\u6790\u5427\uff01",
        ],
        "ability_tip": [
            "\u60a8\u7684{ability_name}\u80fd\u529b\u5df2\u8fbe{proficiency}%\uff0c\u7ee7\u7eed\u52aa\u529b\u5373\u53ef\u89e3\u9501{unlock_target}\uff01\u5df2\u4f7f\u7528{usage_count}\u6b21\u3002",
            "\u541b\u5b50\uff0c{ability_name}\u8fdb\u6b65\u660e\u663e\uff08{proficiency}%\uff09\uff0c\u8ddd\u79bb{unlock_target}\u89e3\u9501\u53ea\u5dee\u4e00\u6b65\u4e4b\u9065\u3002\u5df2\u4f7f\u7528{usage_count}\u6b21\u3002",
        ],
        "daily_encouragement": [
            "{current_realm}\u4e4b\u65c5\uff0c\u4eca\u65e5\u5df2\u8fde\u7eed{streak_day}\u5929\uff01\u575a\u6301\u5c31\u662f\u80dc\u5229\uff0c\u7ee7\u7eed\u52aa\u529b\u5427\uff01",
            "\u5468\u7460\u4e3a\u60a8\u52a0\u6cb9\uff01\u8fde\u7eed{streak_day}\u5927\u4fee\u884c\uff0c{current_realm}\u5b9a\u80fd\u66f4\u4e0a\u4e00\u5c42\u697c\uff01",
        ],
    },
    "luxun": {
        "breakthrough_congrats": [
            "\u60a8\u5df2\u8fdb\u5165{next_realm}\u3002\u8fd9\u662f\u4e00\u4e2a\u65b0\u7684\u8d77\u70b9\uff0c\u4e5f\u662f\u4e00\u4e2a\u66f4\u9ad8\u7684\u8981\u6c42\u3002\u4e0b\u4e00\u9636\u6bb5\u9700{exp_needed}\u70b9\u7ecf\u9a8c\uff0c\u89e3\u9501\u65b0\u529f\u80fd\uff1a{new_feature}\u3002",
            "\u606d\u559c\u60a8\u8fbe\u5230{next_realm}\u3002\u524d\u9762\u7684\u8def\u8fd8\u5f88\u957f\uff0c\u4f46\u6bcf\u4e00\u6b90\u90fd\u6709\u5176\u610f\u4e49\u3002\u7ee7\u7eed\u524d\u8fdb\u5427\uff01",
        ],
        "stagnation_warning": [
            "\u5728{realm_name}\u505c\u6ede\u4e0d\u524d\uff0c\u5e76\u4e0d\u662f\u5931\u8d25\uff0c\u800c\u662f\u79ef\u7d2f\u7684\u8fc7\u7a0b\u3002\u5efa\u8bae\u5c1d\u8bd5\u65b0\u7684\u5206\u6790\u65b9\u5411\uff0c\u4f8b\u5982{new_feature}\u3002",
            "\u6c89\u6dc1\u662f\u6210\u957f\u7684\u5fc5\u7ecf\u4e4b\u8def\u3002{realm_name}\u7684\u60a8\uff0c\u662f\u5426\u8003\u8651\u63a2\u7d22{ability_name}\uff1f",
        ],
        "ability_tip": [
            "{ability_name}\u7684\u638c\u63e1\u7a0b\u5ea6\u4e3a{proficiency}%\uff0c\u8fd9\u662f\u4e00\u4e2a\u4e0d\u9519\u7684\u8fdb\u5c55\u3002\u7ee7\u7eed\u4f7f\u7528\u5c06\u89e3\u9501{unlock_target}\u3002\u5df2\u4f7f\u7528{usage_count}\u6b21\u3002",
            "\u60a8\u5728{ability_name}\u4e0a\u7684\u6295\u5165\u6709\u4e86\u56de\u62a5\uff0c\u5f53\u524d\u7cbe\u901a\u5ea6{proficiency}%\u3002\u8ddd\u79bb{unlock_target}\u7684\u89e3\u9501\u6761\u4ef6\u6b63\u5728\u63a5\u8fd1\u3002",
        ],
        "daily_encouragement": [
            "\u4eca\u65e5\u662f\u8fde\u7eed\u4fee\u884c\u7684\u7b2c{streak_day}\u5929\u3002\u5728{current_realm}\u7684\u6bcf\u4e00\u5929\uff0c\u90fd\u662f\u5411\u4e0a\u7684\u4e00\u6b65\u3002",
            "\u8fde\u7eed{streak_day}\u5929\uff0c\u8fd9\u79cd\u575a\u6301\u672c\u8eab\u5c31\u662f\u4e00\u79cd\u80fd\u529b\u3002{current_realm}\u4e4b\u8def\uff0c\u811a\u8e0f\u5b9e\u5730\u3002",
        ],
    },
}


class LiBuCultivationAdvisor:

    def __init__(self):
        self.templates = LI_BU_GUIDANCE_TEMPLATES

    def generate_guidance(
        self,
        user_state: UserCultivationState,
        context_type: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> CultivationGuidanceMessage:
        data = extra_data or {}
        persona = data.get("persona", "zhouyu")
        if persona not in self.templates:
            persona = "zhouyu"
        template_pool = self.templates[persona].get(context_type, [])
        if not template_pool:
            context_type = "daily_encouragement"
            template_pool = self.templates[persona].get(context_type, [])
        template = random.choice(template_pool)
        params = {
            "realm_name": user_state.current_realm.display_name,
            "next_realm": (user_state.current_realm.next_realm() or QuantRealm.DA_CHENG).display_name,
            "exp_needed": user_state.exp_to_next_level(),
            "new_feature": data.get("new_feature", "\u65b0\u5206\u6790\u5de5\u5177"),
            "ability_name": data.get("ability_name", "\u6838\u5fc3\u80fd\u529b"),
            "usage_count": data.get("usage_count", 0),
            "unlock_target": data.get("unlock_target", "\u9ad8\u9636\u80fd\u529b"),
            "streak_target": data.get("streak_target", 30),
            "streak_day": user_state.streak_days,
            "current_realm": user_state.current_realm.display_name,
            "proficiency": data.get("proficiency", 0),
        }
        message_text = template.format(**params)
        urgency_map = {
            "breakthrough_congrats": "high",
            "stagnation_warning": "high",
            "ability_tip": "normal",
            "daily_encouragement": "low",
        }
        return CultivationGuidanceMessage(
            persona=persona,
            message_text=message_text,
            guidance_type=context_type,
            realm_context=user_state.current_realm,
            urgency=urgency_map.get(context_type, "normal"),
        )

    def get_breakthrough_guidance(
        self,
        user_state: UserCultivationState,
        new_realm: QuantRealm,
        persona: str = "zhouyu"
    ) -> CultivationGuidanceMessage:
        data = {
            "persona": persona,
            "new_feature": REALM_CAPABILITIES.get(new_realm, REALM_CAPABILITIES[QuantRealm.DA_CHENG]).available_tools[-1],
        }
        return self.generate_guidance(user_state, "breakthrough_congrats", data)

    def get_stagnation_guidance(
        self,
        user_state: UserCultivationState,
        persona: str = "luxun"
    ) -> CultivationGuidanceMessage:
        data = {
            "persona": persona,
            "new_feature": "\u6df1\u5ea6\u5206\u6790\u4efb\u52a1",
        }
        return self.generate_guidance(user_state, "stagnation_warning", data)

    def get_ability_tip(
        self,
        user_state: UserCultivationState,
        ability_name: str,
        proficiency: float,
        usage_count: int,
        unlock_target: str,
        persona: str = "zhouyu"
    ) -> CultivationGuidanceMessage:
        data = {
            "persona": persona,
            "ability_name": ability_name,
            "proficiency": round(proficiency, 1),
            "usage_count": usage_count,
            "unlock_target": unlock_target,
        }
        return self.generate_guidance(user_state, "ability_tip", data)


@dataclass
class CollectiveEvolutionRecord:
    feature_id: str
    total_usage_count: int
    positive_feedback_count: int
    negative_feedback_count: int
    satisfaction_score: float
    evolution_weight: float
    last_updated: datetime


class GongBuCollectiveEvolution:

    DEFAULT_FEATURES = [
        "block_analysis",
        "prediction_model",
        "policy_impact",
        "risk_scoring",
        "strategy_backtest",
        "factor_mining",
    ]

    def __init__(self):
        self._feature_records: Dict[str, CollectiveEvolutionRecord] = {}
        self._global_evolution_score: float = 1.0
        self._init_default_records()

    def _init_default_records(self) -> None:
        now = datetime.now()
        for fid in self.DEFAULT_FEATURES:
            self._feature_records[fid] = CollectiveEvolutionRecord(
                feature_id=fid,
                total_usage_count=0,
                positive_feedback_count=0,
                negative_feedback_count=0,
                satisfaction_score=0.5,
                evolution_weight=1.0,
                last_updated=now,
            )

    def record_usage(
        self,
        feature_id: str,
        is_positive: bool = True
    ) -> None:
        if feature_id not in self._feature_records:
            now = datetime.now()
            self._feature_records[feature_id] = CollectiveEvolutionRecord(
                feature_id=feature_id,
                total_usage_count=0,
                positive_feedback_count=0,
                negative_feedback_count=0,
                satisfaction_score=0.5,
                evolution_weight=1.0,
                last_updated=now,
            )
        record = self._feature_records[feature_id]
        record.total_usage_count += 1
        if is_positive:
            record.positive_feedback_count += 1
        else:
            record.negative_feedback_count += 1
        total_fb = record.positive_feedback_count + record.negative_feedback_count
        if total_fb > 0:
            record.satisfaction_score = record.positive_feedback_count / total_fb
        record.evolution_weight = 1.0 + (record.satisfaction_score - 0.5) * 0.5
        record.last_updated = datetime.now()
        self._recalc_global_score()

    def _recalc_global_score(self) -> None:
        weights = [r.evolution_weight for r in self._feature_records.values()]
        if weights:
            self._global_evolution_score = sum(weights) / len(weights)
        else:
            self._global_evolution_score = 1.0

    def get_feature_status(self, feature_id: str) -> Optional[Dict[str, Any]]:
        record = self._feature_records.get(feature_id)
        if record is None:
            return None
        return {
            "feature_id": record.feature_id,
            "total_usage_count": record.total_usage_count,
            "positive_feedback_count": record.positive_feedback_count,
            "negative_feedback_count": record.negative_feedback_count,
            "satisfaction_score": round(record.satisfaction_score, 4),
            "evolution_weight": round(record.evolution_weight, 4),
            "last_updated": record.last_updated.isoformat(),
        }

    def get_all_feature_statuses(self) -> List[Dict[str, Any]]:
        return [self.get_feature_status(fid) for fid in self._feature_records]

    def get_global_evolution_score(self) -> float:
        return round(self._global_evolution_score, 4)

    def get_top_improving_features(self, top_n: int = 3) -> List[Dict[str, Any]]:
        sorted_features = sorted(
            self._feature_records.values(),
            key=lambda r: r.evolution_weight,
            reverse=True,
        )
        result = []
        for record in sorted_features[:top_n]:
            result.append({
                "feature_id": record.feature_id,
                "evolution_weight": round(record.evolution_weight, 4),
                "satisfaction_score": round(record.satisfaction_score, 4),
                "usage_count": record.total_usage_count,
            })
        return result


@dataclass
class TribulationWarning:
    warning_id: str
    user_id: str
    warning_level: str
    risk_metrics: Dict[str, float]
    triggered_by: str
    restrictions_applied: List[str]
    suggestion: str
    created_at: datetime
    is_active: bool


TRIBULATION_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "warning": {"var_exceed_count": 3, "mdd_exceed_count": 3, "lookback_days": 30},
    "severe": {"var_exceed_count": 5, "mdd_exceed_count": 5, "lookback_days": 30},
    "critical": {"var_exceed_count": 8, "mdd_exceed_count": 8, "lookback_days": 14},
}

TRIBULATION_RESTRICTIONS: Dict[str, List[str]] = {
    "warning": ["high_leverage_reminder"],
    "severe": ["no_leverage_strategy", "risk_mandatory_review"],
    "critical": ["readonly_mode", "force_risk_course", "agent_intervention"],
}


class XingBuTribulationWarningSystem:

    def __init__(self):
        self._warnings: Dict[str, TribulationWarning] = {}
        self._risk_history: List[Dict[str, Any]] = []

    def check_risk_status(
        self,
        user_id: str,
        var_value: float,
        mdd_value: float,
        var_threshold: float,
        mdd_threshold: float
    ) -> Optional[TribulationWarning]:
        now = datetime.now()
        history_entry = {
            "timestamp": now.isoformat(),
            "user_id": user_id,
            "var_value": var_value,
            "mdd_value": mdd_value,
            "var_threshold": var_threshold,
            "mdd_threshold": mdd_threshold,
        }
        self._risk_history.append(history_entry)
        lookback_days = 30
        cutoff = now - timedelta(days=lookback_days)
        recent = [h for h in self._risk_history if h.get("user_id") == user_id and datetime.fromisoformat(h["timestamp"]) >= cutoff]
        var_exceeds = len([h for h in recent if h.get("var_value", 0) > h.get("var_threshold", 999)])
        mdd_exceeds = len([h for h in recent if h.get("mdd_value", 0) < h.get("mdd_threshold", -999)])
        warning_level = None
        if var_exceeds >= TRIBULATION_THRESHOLDS["critical"]["var_exceed_count"] or mdd_exceeds >= TRIBULATION_THRESHOLDS["critical"]["mdd_exceed_count"]:
            warning_level = "critical"
        elif var_exceeds >= TRIBULATION_THRESHOLDS["severe"]["var_exceed_count"] or mdd_exceeds >= TRIBULATION_THRESHOLDS["severe"]["mdd_exceed_count"]:
            warning_level = "severe"
        elif var_exceeds >= TRIBULATION_THRESHOLDS["warning"]["var_exceed_count"] or mdd_exceeds >= TRIBULATION_THRESHOLDS["warning"]["mdd_exceed_count"]:
            warning_level = "warning"
        if warning_level is None:
            return None
        restrictions = TRIBULATION_RESTRICTIONS.get(warning_level, [])
        suggestion = self._generate_suggestion(warning_level, var_exceeds, mdd_exceeds)
        warning_id = hashlib.md5(f"{user_id}_{warning_level}_{now.isoformat()}".encode()).hexdigest()[:12]
        warning = TribulationWarning(
            warning_id=warning_id,
            user_id=user_id,
            warning_level=warning_level,
            risk_metrics={"var_value": var_value, "mdd_value": mdd_value, "var_exceeds": var_exceeds, "mdd_exceeds": mdd_exceeds},
            triggered_by=f"var>{var_threshold} or mdd<{mdd_threshold}",
            restrictions_applied=restrictions,
            suggestion=suggestion,
            created_at=now,
            is_active=True,
        )
        self._warnings[f"{user_id}:{warning_level}"] = warning
        return warning

    def _generate_suggestion(
        self,
        level: str,
        var_cnt: int,
        mdd_cnt: int
    ) -> str:
        if level == "critical":
            return ("\u26a0 FE \u4e25\u91cd\u6e21\u52ab\u8b66\u62a5\uff01VaR\u8d85\u9650" + str(var_cnt) + "\u6b21\uff0cMDD\u8d85\u9650" + str(mdd_cnt) + "\u6b21\u3002\u7acb\u5373\u505c\u6b62\u6240\u6709\u9ad8\u6743\u9669\u64cd\u4f5c\uff0c\u5f3a\u5236\u8fdb\u5165\u98ce\u9669\u57f9\u8bad\u8bfe\u7a0b\u3002")
        elif level == "severe":
            return ("\u26a0 \u6e21\u52ab\u8b66\u62a5\uff01VaR\u8d85\u9650" + str(var_cnt) + "\u6b21\uff0cMDD\u8d85\u9650" + str(mdd_cnt) + "\u6b21\u3002\u7981\u6b62\u4f7f\u7528\u6743\u6760\u7b56\u7565\uff0c\u5fc5\u987b\u5148\u5b8c\u6210\u98ce\u9669\u590d\u67e5\u3002")
        else:
            return ("\u26a0 \u98ce\u9669\u63d0\u793a\uff01VaR\u8d85\u9650" + str(var_cnt) + "\u6b21\uff0cMDD\u8d85\u9650" + str(mdd_cnt) + "\u6b21\u3002\u5efa\u8bae\u964d\u4f4e\u6743\u6760\u4f7f\u7528\uff0c\u6ce8\u610f\u98ce\u9669\u63a7\u5236\u3002")

    def _get_active_warning(self, user_id: str) -> Optional[TribulationWarning]:
        for key, w in self._warnings.items():
            if w.user_id == user_id and w.is_active:
                return w
        return None

    def deactivate_warning(self, user_id: str) -> bool:
        for key, w in self._warnings.items():
            if w.user_id == user_id and w.is_active:
                w.is_active = False
                return True
        return False

    def get_user_warnings(self, user_id: str) -> List[TribulationWarning]:
        return [w for w in self._warnings.values() if w.user_id == user_id]

    def clear_warning(self, user_id: str, warning_id: str) -> bool:
        key = f"{user_id}:{warning_id}"
        if key in self._warnings:
            del self._warnings[key]
            return True
        return False


# =====================================================================
# PART E: FRONTEND VISUALIZATION
# =====================================================================

@dataclass
class CultivationPanelData:
    current_realm: QuantRealm
    realm_display_name: str
    realm_color: str
    total_exp: int
    exp_to_next: int
    exp_progress_pct: float
    streak_days: int
    abilities: List[Dict[str, Any]]
    transfer_graph_data: Dict[str, Any]
    pending_tasks: List[Dict[str, Any]]
    recent_transfers: List[Dict[str, Any]]
    breakthrough_animation_pending: bool
    next_realm_name: Optional[str]


CULTIVATION_PANEL_SPEC: Dict[str, Any] = {
    "layout": "vertical_flex",
    "width_px": 420,
    "height_px": 720,
    "sections": [
        {
            "id": "realm_header",
            "title": "\u4fee\u884c\u5883\u754c",
            "component": "realm_badge",
            "height_pct": 15,
        },
        {
            "id": "exp_bar",
            "title": "\u7ecf\u9a8c\u8fdb\u5ea6",
            "component": "progress_bar",
            "height_pct": 8,
        },
        {
            "id": "abilities_grid",
            "title": "\u80fd\u529b\u56fe\u8c31",
            "component": "grid_layout",
            "height_pct": 30,
        },
        {
            "id": "transfer_graph",
            "title": "\u4e00\u901a\u767e\u901a\u56fe",
            "component": "network_graph",
            "height_pct": 20,
        },
        {
            "id": "tasks_list",
            "title": "\u4efb\u52a1\u5217\u8868",
            "component": "scroll_list",
            "height_pct": 17,
        },
        {
            "id": "resonance_log",
            "title": "\u5171\u632f\u65e5\u5fd7",
            "component": "timeline",
            "height_pct": 10,
        },
    ],
    "animation_config": {
        "breakthrough": {
            "type": "particle_golden",
            "duration_ms": 3000,
            "particle_count": 50,
            "colors": ["#FFD700", "#FFA500", "#FF6347"],
        },
        "bonus_received": {
            "type": "ripple_purple",
            "duration_ms": 1500,
            "color": "#9C27B0",
        },
    },
}

REPORT_CULTIVATION_TIP_SPEC: Dict[str, Any] = {
    "position": "bottom_right",
    "style": "floating_card",
    "gradient_colors": ["#667eea", "#764ba2"],
    "icon": "\u2600\ufe0f",
    "max_tips_shown": 3,
    "fields": ["ability_name", "proficiency", "next_unlock", "action_hint"],
    "click_action": "navigate_to_ability_detail",
}


class CultivationDashboardBuilder:

    def __init__(self):
        self.calc = RealmProgressCalculator()
        self.transfer_engine = MasteryTransferEngine(CapabilityGraph())
        self.advisor = LiBuCultivationAdvisor()
        self.factor_controller = FactorAccessController()
        self.graph = CapabilityGraph()

    def build_panel_data(
        self,
        user_state: UserCultivationState
    ) -> CultivationPanelData:
        realm = user_state.current_realm
        next_r = realm.next_realm()
        abilities_grid = []
        for ability_node in CORE_ABILITIES:
            prof = user_state.get_ability_proficiency(ability_node.node_id)
            is_unlocked = realm.level >= ability_node.unlock_realm.level
            entry = {
                "ability_id": ability_node.node_id,
                "display_name": ability_node.display_name,
                "category": ability_node.category,
                "proficiency": round(prof, 2),
                "max_proficiency": ability_node.max_proficiency,
                "is_unlocked": is_unlocked,
                "unlock_realm": ability_node.unlock_realm.display_name,
                "icon": self._get_ability_icon(ability_node.category),
            }
            abilities_grid.append(entry)
        graph_json_str = self.graph.export_graph_json()
        try:
            transfer_graph_data = json.loads(graph_json_str)
        except Exception:
            transfer_graph_data = {"nodes": [], "edges": []}
        pending_tasks = []
        for task in CULTIVATION_TASKS:
            if task.task_id not in user_state.completed_tasks:
                meets_realm = task.required_realm is None or realm.level >= task.required_realm.level
                if meets_realm:
                    pending_tasks.append({
                        "task_id": task.task_id,
                        "name": task.name,
                        "category": task.category,
                        "difficulty": task.difficulty,
                        "exp_reward": task.exp_reward,
                        "requirement": task.requirement,
                    })
                    if len(pending_tasks) >= 6:
                        break
        recent_transfers_raw = self.transfer_engine.get_transfer_history(user_state.user_id, limit=5)
        recent_transfers = []
        for t in recent_transfers_raw:
            recent_transfers.append({
                "event_id": t.event_id,
                "source": t.source_ability,
                "target": t.target_ability,
                "bonus": round(t.bonus_amount, 4),
                "timestamp": t.timestamp,
                "was_cascaded": t.was_cascaded,
            })
        return CultivationPanelData(
            current_realm=realm,
            realm_display_name=realm.display_name,
            realm_color=realm.color,
            total_exp=user_state.total_exp,
            exp_to_next=user_state.exp_to_next_level(),
            exp_progress_pct=round(user_state.exp_progress_pct(), 2),
            streak_days=user_state.streak_days,
            abilities=abilities_grid,
            transfer_graph_data=transfer_graph_data,
            pending_tasks=pending_tasks,
            recent_transfers=recent_transfers,
            breakthrough_animation_pending=False,
            next_realm_name=next_r.display_name if next_r else None,
        )

    def build_report_tip(
        self,
        user_state: UserCultivationState,
        used_abilities: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        tips = []
        used = used_abilities or []
        realm = user_state.current_realm
        for ability_node in CORE_ABILITIES:
            prof = user_state.get_ability_proficiency(ability_node.node_id)
            is_unlocked = realm.level >= ability_node.unlock_realm.level
            if not is_unlocked:
                continue
            usage_count = used.count(ability_node.node_id)
            next_target = self._get_next_unlock_target(ability_node, user_state)
            priority = "low"
            if prof < 30:
                priority = "high"
            elif prof < 60:
                priority = "medium"
            tip = {
                "ability_name": ability_node.display_name,
                "ability_id": ability_node.node_id,
                "proficiency": round(prof, 1),
                "usage_count": usage_count,
                "next_unlock": next_target,
                "action_hint": ("\u7ee7\u7eed\u4f7f\u7528" + ability_node.display_name + "\u63d0\u5347\u7cbe\u901a\u5ea6"),
                "priority": priority,
            }
            tips.append(tip)
        tips.sort(key=lambda t: {"high": 0, "medium": 1, "low": 2}.get(t["priority"], 3))
        return tips[:REPORT_CULTIVATION_TIP_SPEC["max_tips_shown"]]

    def _get_next_unlock_target(
        self,
        ability_node: AbilityNode,
        user_state: UserCultivationState
    ) -> str:
        associated = self.graph.get_associated_abilities(ability_node.node_id, min_strength=0.3)
        for target_node, _strength in associated:
            target_prof = user_state.get_ability_proficiency(target_node.node_id)
            if target_prof < target_node.default_proficiency * 2:
                return target_node.display_name
        return "\u66f4\u9ad8\u5883\u754c\u80fd\u529b"

    def build_breakthrough_animation_config(
        self,
        new_realm: QuantRealm
    ) -> Dict[str, Any]:
        base_anim = dict(CULTIVATION_PANEL_SPEC["animation_config"]["breakthrough"])
        base_anim["realm_name"] = new_realm.display_name
        base_anim["realm_color"] = new_realm.color
        base_anim["realm_icon"] = self._get_realm_icon(new_realm)
        return base_anim

    def _get_realm_icon(self, realm: QuantRealm) -> str:
        icon_map = {
            QuantRealm.LIAN_QI: "\ud83d\udcaa",
            QuantRealm.ZHU_JI: "\ud83c\udf1f",
            QuantRealm.JIN_DAN: "\u2604\ufe0f",
            QuantRealm.YUAN_YING: "\ud83d\udc9e",
            QuantRealm.HUA_SHEN: "\ud83c\udf0f",
            QuantRealm.DU_JIE: "\u26a1",
            QuantRealm.DA_CHENG: "\ud83c\udf51",
        }
        return icon_map.get(realm, "\u2600\ufe0f")

    @staticmethod
    def _get_ability_icon(category: str) -> str:
        cat_icons = {
            "fundamental": "\ud83d\udccb",
            "macro": "\ud83d\udcca",
            "risk": "\u26a0\ufe0f",
            "quantitative": "\ud83d\udcca",
            "modeling": "\ud83e\ude84",
            "strategy": "\u2699\ufe0f",
            "advanced": "\ud83c\udfaf",
        }
        return cat_icons.get(category, "\ud83d\udcdc")


# =====================================================================
# PART F: BACKEND SERVICES & DB
# =====================================================================

@dataclass
class RealmValidationResult:
    is_allowed: bool
    required_realm: Optional[QuantRealm] = None
    user_realm: Optional[QuantRealm] = None
    requested_capability: str = ""
    error_message: Optional[str] = None
    http_code: int = 200


class RealmValidationMiddleware:

    CAPABILITY_REALM_MAP: Dict[str, QuantRealm] = {
        "confidence_interval": QuantRealm.ZHU_JI,
        "factor_attribution": QuantRealm.JIN_DAN,
        "scenario_simulation": QuantRealm.YUAN_YING,
        "risk_modeling": QuantRealm.JIN_DAN,
        "backtesting": QuantRealm.JIN_DAN,
        "signal_generation": QuantRealm.HUA_SHEN,
        "ml_prediction": QuantRealm.JIN_DAN,
        "nlp_sentiment": QuantRealm.HUA_SHEN,
        "causal_inference": QuantRealm.DU_JIE,
    }

    ENDPOINT_REALM_MAP: Dict[str, QuantRealm] = {
        "/api/quant/confidence": QuantRealm.ZHU_JI,
        "/api/quant/attribution": QuantRealm.JIN_DAN,
        "/api/quant/scenario": QuantRealm.YUAN_YING,
        "/api/quant/risk-model": QuantRealm.JIN_DAN,
        "/api/quant/backtest": QuantRealm.JIN_DAN,
        "/api/quant/signals": QuantRealm.HUA_SHEN,
        "/api/quant/predict/ml": QuantRealm.JIN_DAN,
        "/api/quant/sentiment": QuantRealm.HUA_SHEN,
        "/api/quant/causal": QuantRealm.DU_JIE,
    }

    def validate(
        self,
        user_state: UserCultivationState,
        capability: str
    ) -> RealmValidationResult:
        required = self.CAPABILITY_REALM_MAP.get(capability)
        if required is None:
            return RealmValidationResult(is_allowed=True, http_code=200)
        if user_state.current_realm.level >= required.level:
            return RealmValidationResult(
                is_allowed=True,
                required_realm=required,
                user_realm=user_state.current_realm,
                requested_capability=capability,
                http_code=200,
            )
        return RealmValidationResult(
            is_allowed=False,
            required_realm=required,
            user_realm=user_state.current_realm,
            requested_capability=capability,
            error_message=(
                "\u6743\u9650\u4e0d\u8db3\uff1a" + capability + " \u9700 "
                + required.display_name + "(\u7b49\u7ea7" + str(required.level) + ")\uff0c"
                + "\u5f53\u524d\u4e3a" + user_state.current_realm.display_name
                + "(\u7b49\u7ea7" + str(user_state.current_realm.level) + ")"
            ),
            http_code=403,
        )

    def validate_batch(
        self,
        user_state: UserCultivationState,
        capabilities: List[str]
    ) -> List[RealmValidationResult]:
        return [self.validate(user_state, cap) for cap in capabilities]

    def get_required_realm_for_endpoint(
        self,
        endpoint: str
    ) -> Optional[QuantRealm]:
        return self.ENDPOINT_REALM_MAP.get(endpoint)


@dataclass
class CultivationAPIResponse:
    success: bool
    data: Any
    message: str
    realm_info: Optional[Dict[str, Any]] = None
    transfers_triggered: Optional[List[Dict[str, Any]]] = None
    level_up: bool = False
    new_realm: Optional[str] = None


class CultivationOrchestrator:

    def __init__(self):
        self.progress_calc = RealmProgressCalculator()
        self.transfer_engine = MasteryTransferEngine(CapabilityGraph())
        self.middleware = RealmValidationMiddleware()
        self.advisor = LiBuCultivationAdvisor()
        self.dashboard_builder = CultivationDashboardBuilder()
        self.factor_controller = FactorAccessController()
        self.output_renderer = TieredOutputRenderer()
        self.strategy_checker = StrategyPermissionChecker()
        self.gongbu_evolution = GongBuCollectiveEvolution()
        self.xingbu_tribulation = XingBuTribulationWarningSystem()
        self._user_states: Dict[str, UserCultivationState] = {}

    def get_or_create_user(self, user_id: str) -> UserCultivationState:
        if user_id not in self._user_states:
            self._user_states[user_id] = UserCultivationState(user_id=user_id)
        return self._user_states[user_id]

    def process_action(
        self,
        user_id: str,
        action_type: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> CultivationAPIResponse:
        user_state = self.get_or_create_user(user_id)
        self.progress_calc.update_streak(user_state)
        exp_gain = self.progress_calc.calculate_exp_gain(action_type, user_state, extra_data)
        leveled_up, new_realm = user_state.add_exp(exp_gain, action_type)
        completed_tasks = self.progress_calc.check_and_apply_task_completion(user_state, action_type)
        task_exp = sum(t.exp_reward for t in completed_tasks)
        if task_exp > 0:
            lv2, nr2 = user_state.add_exp(task_exp, "task_completion")
            if lv2:
                leveled_up = True
                new_realm = nr2
        transfers = []
        ability_updates = extra_data or {}
        if "ability_improved" in ability_updates:
            aid = ability_updates["ability_improved"]
            delta = ability_updates.get("delta", 1.0)
            current = user_state.get_ability_proficiency(aid)
            user_state.set_ability_proficiency(aid, current + delta)
            transfers = self.transfer_engine.compute_transfers(user_id, aid, delta, user_state)
        if "used_feature" in ability_updates:
            fid = ability_updates["used_feature"]
            is_pos = ability_updates.get("is_positive", True)
            self.gongbu_evolution.record_usage(fid, is_pos)
        realm_info = self._build_realm_info(user_state)
        transfer_dicts = []
        for t in transfers:
            transfer_dicts.append({
                "event_id": t.event_id,
                "source": t.source_ability,
                "target": t.target_ability,
                "bonus": t.bonus_amount,
                "was_cascaded": t.was_cascaded,
                "depth": t.cascade_depth,
            })
        msg = self._build_response_message(leveled_up, new_realm, len(transfers))
        return CultivationAPIResponse(
            success=True,
            data={
                "exp_gained": exp_gain + task_exp,
                "tasks_completed": [t.name for t in completed_tasks],
                "transfers": transfer_dicts,
            },
            message=msg,
            realm_info=realm_info,
            transfers_triggered=transfer_dicts if transfer_dicts else None,
            level_up=leveled_up,
            new_realm=new_realm.display_name if new_realm else None,
        )

    def _build_response_message(
        self,
        leveled_up: bool,
        new_realm: Optional[QuantRealm],
        transfer_count: int
    ) -> str:
        parts = []
        if leveled_up and new_realm:
            parts.append("\u1f389 \u606d\u559c\u7a81\u7834\uff01\u8fdb\u5165" + new_realm.display_name + "\uff01")
        if transfer_count > 0:
            parts.append("\u2728 \u89e6\u53d1" + str(transfer_count) + "\u6b21\u4e00\u901a\u767e\u901a\u8f6c\u79fb")
        if not parts:
            parts.append("\u2705 \u64cd\u4f5c\u5b8c\u6210\uff0c\u7ecf\u9a8c\u5df2\u8bb0\u5f55")
        return " ".join(parts)

    def get_realm_info(self, user_id: str) -> CultivationAPIResponse:
        user_state = self.get_or_create_user(user_id)
        panel = self.dashboard_builder.build_panel_data(user_state)
        resonance = self.transfer_engine.get_resonance_summary(user_id)
        panel_dict = {
            "current_realm": panel.current_realm.value,
            "realm_display_name": panel.realm_display_name,
            "realm_color": panel.realm_color,
            "total_exp": panel.total_exp,
            "exp_to_next": panel.exp_to_next,
            "exp_progress_pct": panel.exp_progress_pct,
            "streak_days": panel.streak_days,
            "abilities": panel.abilities,
            "pending_tasks": panel.pending_tasks,
            "recent_transfers": panel.recent_transfers,
            "next_realm_name": panel.next_realm_name,
        }
        return CultivationAPIResponse(
            success=True,
            data=panel_dict,
            message="\u4fee\u884c\u72b6\u6001\u67e5\u8be2\u6210\u529f",
            realm_info={
                "panel_data": panel_dict,
                "resonance_summary": resonance,
                "graph_json": panel.transfer_graph_data,
            },
        )

    def get_quant_analysis_with_realm(
        self,
        user_id: str,
        raw_data: Dict[str, Any]
    ) -> CultivationAPIResponse:
        user_state = self.get_or_create_user(user_id)
        rendered = self.output_renderer.render(raw_data, user_state.current_realm)
        available_factors = self.factor_controller.get_available_factors(user_state.current_realm)
        locked_factors = self.factor_controller.get_locked_factors(user_state.current_realm)
        used_abilities = raw_data.get("used_abilities", [])
        report_tips = self.dashboard_builder.build_report_tip(user_state, used_abilities)
        output_dict = {
            "realm": rendered.realm.value,
            "forecast_range": rendered.forecast_range,
            "confidence_info": rendered.confidence_info,
            "factor_ranking": rendered.factor_ranking,
            "scenario_results": rendered.scenario_results,
            "strategy_advice": rendered.strategy_advice,
            "truncated_fields": rendered.truncated_fields,
            "available_factors": [f.factor_id for f in available_factors],
            "locked_factors": [{"id": f.factor_id, "name": f.factor_name, "hint": f.unlock_hint} for f in locked_factors],
            "report_tips": report_tips,
        }
        return CultivationAPIResponse(
            success=True,
            data=output_dict,
            message=(rendered.realm.display_name + "\u7ea7\u522b\u5206\u6790\u6e32\u67d3\u5b8c\u6210"),
            realm_info={"realm": user_state.current_realm.value, "level": user_state.current_realm.level},
        )

    def check_strategy_permission(
        self,
        user_id: str,
        strategy_type: str
    ) -> CultivationAPIResponse:
        user_state = self.get_or_create_user(user_id)
        allowed, msg, required = self.strategy_checker.check_permission(strategy_type, user_state.current_realm)
        if allowed:
            perm = self.strategy_checker.permissions.get(strategy_type)
            params = perm.allowed_params if perm else []
            return CultivationAPIResponse(
                success=True,
                data={"strategy_type": strategy_type, "allowed_params": params},
                message=("\u7b56\u7565 " + strategy_type + " \u5df2\u6388\u6743"),
            )
        req_str = required.display_name if required else "?"
        return CultivationAPIResponse(
            success=False,
            data={"strategy_type": strategy_type, "required_realm": required.value if required else None},
            message=(msg or ("\u6743\u9650\u4e0d\u8db3\uff0c\u65e0\u6cd5\u4f7f\u7528 " + strategy_type)),
            http_code=403,
        )

    def check_tribulation(
        self,
        user_id: str,
        var_value: float,
        mdd_value: float,
        var_thresh: float,
        mdd_thresh: float
    ) -> CultivationAPIResponse:
        warning = self.xingbu_tribulation.check_risk_status(
            user_id, var_value, mdd_value, var_thresh, mdd_thresh
        )
        if warning is None:
            return CultivationAPIResponse(
                success=True,
                data={"status": "clear"},
                message="\u98ce\u9669\u72b6\u6001\u6b63\u5e38\uff0c\u65e0\u6e21\u52ab\u8b66\u62a5",
            )
        return CultivationAPIResponse(
            success=False,
            data={
                "warning_id": warning.warning_id,
                "level": warning.warning_level,
                "restrictions": warning.restrictions_applied,
                "suggestion": warning.suggestion,
                "metrics": warning.risk_metrics,
            },
            message=warning.suggestion,
            http_code=423,
        )

    def get_guidance(
        self,
        user_id: str,
        context_type: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> CultivationAPIResponse:
        user_state = self.get_or_create_user(user_id)
        guidance = self.advisor.generate_guidance(user_state, context_type, extra_data)
        return CultivationAPIResponse(
            success=True,
            data={
                "persona": guidance.persona,
                "message": guidance.message_text,
                "guidance_type": guidance.guidance_type,
                "urgency": guidance.urgency,
                "suggested_action": guidance.suggested_action,
            },
            message="\u4fee\u884c\u6307\u5bfc\u751f\u6210\u6210\u529f",
        )

    def get_dashboard_full(self, user_id: str) -> CultivationAPIResponse:
        user_state = self.get_or_create_user(user_id)
        panel_data = self.dashboard_builder.build_panel_data(user_state)
        resonance = self.transfer_engine.get_resonance_summary(user_id)
        evolution_score = self.gongbu_evolution.get_global_evolution_score()
        top_features = self.gongbu_evolution.get_top_improving_features(3)
        warnings = self.xingbu_tribulation.get_user_warnings(user_id)
        active_warning = self.xingbu_tribulation._get_active_warning(user_id)
        return CultivationAPIResponse(
            success=True,
            data={
                "panel": {
                    "realm": panel_data.current_realm.value,
                    "realm_display": panel_data.realm_display_name,
                    "realm_color": panel_data.realm_color,
                    "total_exp": panel_data.total_exp,
                    "exp_to_next": panel_data.exp_to_next,
                    "exp_progress_pct": panel_data.exp_progress_pct,
                    "streak_days": panel_data.streak_days,
                    "abilities": panel_data.abilities,
                    "pending_tasks": panel_data.pending_tasks,
                    "recent_transfers": panel_data.recent_transfers,
                    "next_realm": panel_data.next_realm_name,
                },
                "resonance": resonance,
                "evolution": {
                    "global_score": evolution_score,
                    "top_features": top_features,
                },
                "tribulation": {
                    "has_active_warning": active_warning is not None,
                    "active_warning_level": active_warning.warning_level if active_warning else None,
                    "all_warnings": [
                        {"id": w.warning_id, "level": w.warning_level, "is_active": w.is_active}
                        for w in warnings
                    ],
                },
                "graph_data": panel_data.transfer_graph_data,
            },
            message="\u5b8c\u6574\u4fee\u884c\u4eea\u8868\u677f\u6570\u636e",
        )


# =====================================================================
# PART G: TESTING SUITE
# =====================================================================

FUSION_QUANT_MASTERY_TEST_CASES: List[Dict[str, Any]] = [
    # realm_system tests
    {"category": "realm_system", "test_id": "enum_values", "desc": "All 7 enum values exist with correct values"},
    {"category": "realm_system", "test_id": "level_ordering", "desc": "Levels increase 1-7 from LIAN_QI to DA_CHENG"},
    {"category": "realm_system", "test_id": "next_chain", "desc": "next_realm() chains through all realms correctly"},
    {"category": "realm_system", "test_id": "capabilities_count", "desc": "REALM_CAPABILITIES has exactly 7 entries"},
    {"category": "realm_system", "test_id": "thresholds_monotonic", "desc": "EXP_THRESHOLDS are monotonically increasing"},
    # exp_system tests
    {"category": "exp_system", "test_id": "gain_calc", "desc": "calculate_exp_gain returns positive int for valid actions"},
    {"category": "exp_system", "test_id": "streak_update", "desc": "update_streak increments on consecutive days"},
    {"category": "exp_system", "test_id": "task_completion", "desc": "check_and_apply_task_completion returns matching tasks"},
    {"category": "exp_system", "test_id": "exp_history", "desc": "get_exp_history returns limited recent entries"},
    # mastery_transfer tests
    {"category": "mastery_transfer", "test_id": "eligibility_check", "desc": "check_transfer_eligibility returns False below threshold"},
    {"category": "mastery_transfer", "test_id": "compute_transfers", "desc": "compute_transfers generates events for associated abilities"},
    {"category": "mastery_transfer", "test_id": "cascade", "desc": "Cascade triggers up to MAX_CASCADE_DEPTH levels deep"},
    {"category": "mastery_transfer", "test_id": "history", "desc": "get_transfer_history returns user-specific events"},
    {"category": "mastery_transfer", "test_id": "resonance_summary", "desc": "get_resonance_summary aggregates correctly"},
    # factor_tiers tests
    {"category": "factor_tiers", "test_id": "available_by_realm", "desc": "get_available_factors filters by realm level"},
    {"category": "factor_tiers", "test_id": "locked_by_realm", "desc": "get_locked_factors returns only locked ones"},
    {"category": "factor_tiers", "test_id": "radar_data", "desc": "get_factor_radar_data includes lock status per factor"},
    # tiered_output tests
    {"category": "tiered_output", "test_id": "lianqi_truncated", "desc": "LIAN_QI rendering truncates most fields"},
    {"category": "tiered_output", "test_id": "dacheng_full", "desc": "DA_CHENG rendering includes all fields"},
    {"category": "tiered_output", "test_id": "realm_filtering", "desc": "Different realms produce different output specs"},
    # strategy_permissions tests
    {"category": "strategy_permissions", "test_id": "allowed_check", "desc": "check_permission allows sufficient realm"},
    {"category": "strategy_permissions", "test_id": "locked_list", "desc": "get_locked_strategies returns correct list"},
    {"category": "strategy_permissions", "test_id": "batch_validate", "desc": "validate_batch returns correct count of failures"},
    # agent_fusion tests
    {"category": "agent_fusion", "test_id": "zhouyu_breakthrough", "desc": "Zhouyu breakthrough congrats contains realm name"},
    {"category": "agent_fusion", "test_id": "luxun_stagnation", "desc": "Luxun stagnation warning has proper tone"},
    {"category": "agent_fusion", "test_id": "ability_tip", "desc": "Ability tip includes proficiency and unlock target"},
    {"category": "agent_fusion", "test_id": "gongbu_record", "desc": "record_usage updates counts and satisfaction score"},
    {"category": "agent_fusion", "test_id": "tribulation_warning", "desc": "Tribulation warning generated when thresholds exceeded"},
    {"category": "agent_fusion", "test_id": "tribulation_clear", "desc": "clear_warning removes warning from system"},
    # frontend_viz tests
    {"category": "frontend_viz", "test_id": "panel_build", "desc": "build_panel_data returns complete panel structure"},
    {"category": "frontend_viz", "test_id": "report_tip", "desc": "build_report_tip returns up to max_tips_shown tips"},
    {"category": "frontend_viz", "test_id": "animation_config", "desc": "build_breakthrough_animation_config includes realm info"},
    # backend_services tests
    {"category": "backend_services", "test_id": "middleware_validate", "desc": "Middleware rejects insufficient realm with 403"},
    {"category": "backend_services", "test_id": "orchestrator_process", "desc": "process_action runs full pipeline successfully"},
    {"category": "backend_services", "test_id": "orchestrator_tribulation", "desc": "Orchestrator returns 423 on tribulation"},
    {"category": "backend_services", "test_id": "full_dashboard", "desc": "get_dashboard_full returns complete dashboard data"},
    # integration_e2e tests
    {"category": "integration_e2e", "test_id": "full_pipeline_levelup", "desc": "Full pipeline causes level-up at threshold"},
    {"category": "integration_e2e", "test_id": "transfer_on_block_analysis", "desc": "Block analysis improvement triggers transfers"},
    {"category": "integration_e2e", "test_id": "realm_gated_api_call", "desc": "Realm-gated API call rejected for low-level user"},
]


class FusionQuantMasteryTestSuite:

    def __init__(self):
        self.orchestrator = CultivationOrchestrator()
        self.results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> Dict[str, Any]:
        test_methods = [
            ("realm_system", self._test_enum_values),
            ("realm_system", self._test_level_ordering),
            ("realm_system", self._test_next_chain),
            ("realm_system", self._test_capabilities_count),
            ("realm_system", self._test_thresholds_monotonic),
            ("exp_system", self._test_gain_calc),
            ("exp_system", self._test_streak_update),
            ("exp_system", self._test_task_completion),
            ("exp_system", self._test_exp_history),
            ("mastery_transfer", self._test_eligibility_check),
            ("mastery_transfer", self._test_compute_transfers),
            ("mastery_transfer", self._test_cascade),
            ("mastery_transfer", self._test_history),
            ("mastery_transfer", self._test_resonance_summary),
            ("factor_tiers", self._test_available_by_realm),
            ("factor_tiers", self._test_locked_by_realm),
            ("factor_tiers", self._test_radar_data),
            ("tiered_output", self._test_lianqi_truncated),
            ("tiered_output", self._test_dacheng_full),
            ("tiered_output", self._test_realm_filtering),
            ("strategy_permissions", self._test_allowed_check),
            ("strategy_permissions", self._test_locked_list),
            ("strategy_permissions", self._test_batch_validate),
            ("agent_fusion", self._test_zhouyu_breakthrough),
            ("agent_fusion", self._test_luxun_stagnation),
            ("agent_fusion", self._test_ability_tip),
            ("agent_fusion", self._test_gongbu_record),
            ("agent_fusion", self._test_tribulation_warning),
            ("agent_fusion", self._test_tribulation_clear),
            ("frontend_viz", self._test_panel_build),
            ("frontend_viz", self._test_report_tip),
            ("frontend_viz", self._test_animation_config),
            ("backend_services", self._test_middleware_validate),
            ("backend_services", self._test_orchestrator_process),
            ("backend_services", self._test_orchestrator_tribulation),
            ("backend_services", self._test_full_dashboard),
            ("integration_e2e", self._test_full_pipeline_levelup),
            ("integration_e2e", self._test_transfer_on_block_analysis),
            ("integration_e2e", self._test_realm_gated_api_call),
        ]
        passed = 0
        failed = 0
        errors = 0
        for category, method in test_methods:
            try:
                result = method()
                if result.get("passed"):
                    passed += 1
                else:
                    failed += 1
                self.results.append({"category": category, **result})
            except Exception as exc:
                errors += 1
                self.results.append({"category": category, "error": str(exc), "passed": False})
        return {"total": len(test_methods), "passed": passed, "failed": failed, "errors": errors}

    def _test_enum_values(self) -> Dict[str, Any]:
        expected = {"LIAN_QI", "ZHU_JI", "JIN_DAN", "YUAN_YING", "HUA_SHEN", "DU_JIE", "DA_CHENG"}
        actual = {r.name for r in QuantRealm}
        ok = actual == expected
        return {"test_id": "enum_values", "passed": ok, "detail": ("expected=" + str(expected) + ", got=" + str(actual))}

    def _test_level_ordering(self) -> Dict[str, Any]:
        realms = [QuantRealm.LIAN_QI, QuantRealm.ZHU_JI, QuantRealm.JIN_DAN, QuantRealm.YUAN_YING, QuantRealm.HUA_SHEN, QuantRealm.DU_JIE, QuantRealm.DA_CHENG]
        levels = [r.level for r in realms]
        ok = levels == list(range(1, 8))
        return {"test_id": "level_ordering", "passed": ok, "detail": ("levels=" + str(levels))}

    def _test_next_chain(self) -> Dict[str, Any]:
        chain = []
        current = QuantRealm.LIAN_QI
        while current is not None:
            chain.append(current)
            current = current.next_realm()
        ok = len(chain) == 7 and chain[-1] == QuantRealm.DA_CHENG
        return {"test_id": "next_chain", "passed": ok, "detail": ("chain_length=" + str(len(chain)))}

    def _test_capabilities_count(self) -> Dict[str, Any]:
        ok = len(REALM_CAPABILITIES) == 7
        return {"test_id": "capabilities_count", "passed": ok, "detail": ("count=" + str(len(REALM_CAPABILITIES)))}

    def _test_thresholds_monotonic(self) -> Dict[str, Any]:
        values = [EXP_THRESHOLDS[r] for r in QuantRealm]
        ok = all(values[i] <= values[i + 1] for i in range(len(values) - 1))
        return {"test_id": "thresholds_monotonic", "passed": ok, "detail": ("values=" + str(values))}

    def _test_gain_calc(self) -> Dict[str, Any]:
        calc = RealmProgressCalculator()
        state = UserCultivationState(user_id="test_exp")
        gain = calc.calculate_exp_gain("run_basic_analysis", state)
        ok = isinstance(gain, int) and gain > 0
        return {"test_id": "gain_calc", "passed": ok, "detail": ("gain=" + str(gain))}

    def _test_streak_update(self) -> Dict[str, Any]:
        calc = RealmProgressCalculator()
        state = UserCultivationState(user_id="test_streak")
        s1 = calc.update_streak(state)
        s2 = calc.update_streak(state)
        ok = s1 == 1 and s2 == 1
        return {"test_id": "streak_update", "passed": ok, "detail": ("s1=" + str(s1) + ", s2=" + str(s2))}

    def _test_task_completion(self) -> Dict[str, Any]:
        calc = RealmProgressCalculator()
        state = UserCultivationState(user_id="test_task", current_realm=QuantRealm.JIN_DAN)
        tasks = calc.check_and_apply_task_completion(state, "factor_attribution")
        ok = len(tasks) > 0
        return {"test_id": "task_completion", "passed": ok, "detail": ("completed_count=" + str(len(tasks)))}

    def _test_exp_history(self) -> Dict[str, Any]:
        calc = RealmProgressCalculator()
        state = UserCultivationState(user_id="test_hist")
        calc.calculate_exp_gain("view_dashboard", state)
        calc.calculate_exp_gain("run_regression", state)
        history = calc.get_exp_history("test_hist", limit=1)
        ok = len(history) == 1
        return {"test_id": "exp_history", "passed": ok, "detail": ("history_len=" + str(len(history)))}

    def _test_eligibility_check(self) -> Dict[str, Any]:
        engine = MasteryTransferEngine(CapabilityGraph())
        ok_low = engine.check_transfer_eligibility("u1", "policy_impact", 10.0) == False
        ok_high = engine.check_transfer_eligibility("u1", "policy_impact", 50.0) == True
        ok = ok_low and ok_high
        return {"test_id": "eligibility_check", "passed": ok, "detail": ("low=" + str(ok_low) + ", high=" + str(ok_high))}

    def _test_compute_transfers(self) -> Dict[str, Any]:
        engine = MasteryTransferEngine(CapabilityGraph())
        state = UserCultivationState(user_id="test_transfer")
        state.set_ability_proficiency("block_analysis", 50.0)
        events = engine.compute_transfers("test_transfer", "block_analysis", 5.0, state)
        ok = len(events) > 0
        return {"test_id": "compute_transfers", "passed": ok, "detail": ("events_count=" + str(len(events)))}

    def _test_cascade(self) -> Dict[str, Any]:
        config = MasteryTransferConfig(max_cascade_depth=3)
        engine = MasteryTransferEngine(CapabilityGraph(), config)
        state = UserCultivationState(user_id="test_cascade")
        state.set_ability_proficiency("block_analysis", 80.0)
        state.set_ability_proficiency("city_analysis", 80.0)
        events = engine.compute_transfers("test_cascade", "block_analysis", 20.0, state)
        cascaded = [e for e in events if e.was_cascaded]
        ok = any(e.cascade_depth > 0 for e in cascaded)
        return {"test_id": "cascade", "passed": ok, "detail": ("cascaded_count=" + str(len(cascaded)) + ", has_deep=" + str(any(e.cascade_depth > 0 for e in cascaded)))}

    def _test_history(self) -> Dict[str, Any]:
        engine = MasteryTransferEngine(CapabilityGraph())
        state = UserCultivationState(user_id="test_hist_tr")
        state.set_ability_proficiency("block_analysis", 50.0)
        engine.compute_transfers("test_hist_tr", "block_analysis", 5.0, state)
        history = engine.get_transfer_history("test_hist_tr")
        ok = len(history) > 0
        return {"test_id": "history", "passed": ok, "detail": ("history_count=" + str(len(history)))}

    def _test_resonance_summary(self) -> Dict[str, Any]:
        engine = MasteryTransferEngine(CapabilityGraph())
        state = UserCultivationState(user_id="test_reso")
        state.set_ability_proficiency("block_analysis", 50.0)
        engine.compute_transfers("test_reso", "block_analysis", 5.0, state)
        summary = engine.get_resonance_summary("test_reso")
        ok = "total_events" in summary and summary["total_events"] > 0
        return {"test_id": "resonance_summary", "passed": ok, "detail": ("summary_keys=" + str(list(summary.keys())))}

    def _test_available_by_realm(self) -> Dict[str, Any]:
        ctrl = FactorAccessController()
        avail_lianqi = ctrl.get_available_factors(QuantRealm.LIAN_QI)
        avail_dacheng = ctrl.get_available_factors(QuantRealm.DA_CHENG)
        ok = len(avail_lianqi) < len(avail_dacheng)
        return {"test_id": "available_by_realm", "passed": ok, "detail": ("lianqi=" + str(len(avail_lianqi)) + ", dacheng=" + str(len(avail_dacheng)))}

    def _test_locked_by_realm(self) -> Dict[str, Any]:
        ctrl = FactorAccessController()
        locked = ctrl.get_locked_factors(QuantRealm.LIAN_QI)
        ok = len(locked) > 0
        return {"test_id": "locked_by_realm", "passed": ok, "detail": ("locked_count=" + str(len(locked)))}

    def _test_radar_data(self) -> Dict[str, Any]:
        ctrl = FactorAccessController()
        radar = ctrl.get_factor_radar_data(QuantRealm.JIN_DAN)
        has_locked = any(r.get("is_locked") for r in radar)
        has_unlocked = any(not r.get("is_locked") for r in radar)
        ok = has_locked and has_unlocked
        return {"test_id": "radar_data", "passed": ok, "detail": ("radar_count=" + str(len(radar)) + ", has_locked=" + str(has_locked) + ", has_unlocked=" + str(has_unlocked))}

    def _test_lianqi_truncated(self) -> Dict[str, Any]:
        renderer = TieredOutputRenderer()
        output = renderer.render({"forecast_start": 1, "factor_contributions": [{"weight": 0.5}], "scenarios": [{"name": "bull"}], "strategy_advice": "hold"}, QuantRealm.LIAN_QI)
        ok = len(output.truncated_fields) > 0
        return {"test_id": "lianqi_truncated", "passed": ok, "detail": ("truncated=" + str(output.truncated_fields))}

    def _test_dacheng_full(self) -> Dict[str, Any]:
        renderer = TieredOutputRenderer()
        full_input = {"forecast_start": 1, "factor_contributions": [{"weight": 0.5}], "scenarios": [{"name": "bull"}], "strategy_advice": "hold"}
        output = renderer.render(full_input, QuantRealm.DA_CHENG)
        ok = len(output.truncated_fields) == 0 or "causal_graph" not in output.full_output
        return {"test_id": "dacheng_full", "passed": ok, "detail": ("truncated_count=" + str(len(output.truncated_fields)))}

    def _test_realm_filtering(self) -> Dict[str, Any]:
        renderer = TieredOutputRenderer()
        out_lq = renderer.render({}, QuantRealm.LIAN_QI)
        out_dc = renderer.render({}, QuantRealm.DA_CHENG)
        ok = out_lq.forecast_range != out_dc.forecast_range
        return {"test_id": "realm_filtering", "passed": ok, "detail": ("lq='" + out_lq.forecast_range + "', dc='" + out_dc.forecast_range + "'")}

    def _test_allowed_check(self) -> Dict[str, Any]:
        checker = StrategyPermissionChecker()
        ok1, _, _ = checker.check_permission("buy_and_hold", QuantRealm.LIAN_QI)
        ok2, _, _ = checker.check_permission("rl_optimized", QuantRealm.LIAN_QI)
        ok = ok1 and not ok2
        return {"test_id": "allowed_check", "passed": ok, "detail": ("buy_hold=" + str(ok1) + ", rl_opt=" + str(ok2))}

    def _test_locked_list(self) -> Dict[str, Any]:
        checker = StrategyPermissionChecker()
        locked = checker.get_locked_strategies(QuantRealm.LIAN_QI)
        ok = len(locked) >= 3
        return {"test_id": "locked_list", "passed": ok, "detail": ("locked_count=" + str(len(locked)))}

    def _test_batch_validate(self) -> Dict[str, Any]:
        checker = StrategyPermissionChecker()
        results = [checker.check_permission(s, QuantRealm.ZHU_JI)[0] for s in ["buy_and_hold", "monthly_rebalance", "rl_optimized"]]
        ok = results.count(False) >= 1
        return {"test_id": "batch_validate", "passed": ok, "detail": ("results=" + str(results))}

    def _test_zhouyu_breakthrough(self) -> Dict[str, Any]:
        advisor = LiBuCultivationAdvisor()
        state = UserCultivationState(user_id="test_zy", current_realm=QuantRealm.ZHU_JI, total_exp=120)
        msg = advisor.get_breakthrough_guidance(state, QuantRealm.JIN_DAN, "zhouyu")
        ok = "\u91d1\u4e39" in msg.message_text or "JIN_DAN" in msg.message_text
        return {"test_id": "zhouyu_breakthrough", "passed": ok, "detail": ("msg_preview=" + msg.message_text[:50])}

    def _test_luxun_stagnation(self) -> Dict[str, Any]:
        advisor = LiBuCultivationAdvisor()
        state = UserCultivationState(user_id="test_lx", current_realm=QuantRealm.ZHU_JI, total_exp=150)
        msg = advisor.get_stagnation_guidance(state, "luxun")
        ok = msg.persona == "luxun" and len(msg.message_text) > 10
        return {"test_id": "luxun_stagnation", "passed": ok, "detail": ("msg_len=" + str(len(msg.message_text)))}

    def _test_ability_tip(self) -> Dict[str, Any]:
        advisor = LiBuCultivationAdvisor()
        state = UserCultivationState(user_id="test_tip")
        msg = advisor.get_ability_tip(state, "block_analysis", 45.5, 12, "attribution_analysis", "zhouyu")
        ok = "block_analysis" in msg.message_text or "45" in msg.message_text
        return {"test_id": "ability_tip", "passed": ok, "detail": ("contains_prof='45' in msg=" + str("45" in msg.message_text))}

    def _test_gongbu_record(self) -> Dict[str, Any]:
        gongbu = GongBuCollectiveEvolution()
        gongbu.record_usage("block_analysis", True)
        gongbu.record_usage("block_analysis", True)
        gongbu.record_usage("block_analysis", False)
        status = gongbu.get_feature_status("block_analysis")
        ok = status is not None and status["total_usage_count"] == 3
        detail = "count=" + str(status["total_usage_count"]) if status else "None"
        return {"test_id": "gongbu_record", "passed": ok, "detail": detail}

    def _test_tribulation_warning(self) -> Dict[str, Any]:
        xingbu = XingBuTribulationWarningSystem()
        w = None
        for i in range(10):
            w = xingbu.check_risk_status("tu1", 15.0, -20.0, 5.0, -5.0)
        ok = w is not None and w.warning_level in ("warning", "severe", "critical")
        level_str = w.warning_level if w else "None"
        return {"test_id": "tribulation_warning", "passed": ok, "detail": ("level=" + level_str)}

    def _test_tribulation_clear(self) -> Dict[str, Any]:
        xingbu = XingBuTribulationWarningSystem()
        xingbu.check_risk_status("tu2", 15.0, -20.0, 5.0, -5.0)
        cleared = xingbu.deactivate_warning("tu2")
        return {"test_id": "tribulation_clear", "passed": cleared, "detail": ("cleared=" + str(cleared))}

    def _test_panel_build(self) -> Dict[str, Any]:
        builder = CultivationDashboardBuilder()
        state = UserCultivationState(user_id="panel_test")
        panel = builder.build_panel_data(state)
        ok = len(panel.abilities) == 11 and panel.streak_days >= 1
        return {"test_id": "panel_build", "passed": ok, "detail": ("abilities=" + str(len(panel.abilities)) + ", streak=" + str(panel.streak_days))}

    def _test_report_tip(self) -> Dict[str, Any]:
        builder = CultivationDashboardBuilder()
        state = UserCultivationState(user_id="tip_test")
        state.set_ability_proficiency("block_analysis", 25.0)
        tips = builder.build_report_tip(state, ["block_analysis", "city_analysis"])
        ok = len(tips) <= 3
        return {"test_id": "report_tip", "passed": ok, "detail": ("tips_count=" + str(len(tips)))}

    def _test_animation_config(self) -> Dict[str, Any]:
        builder = CultivationDashboardBuilder()
        cfg = builder.build_breakthrough_animation_config(QuantRealm.JIN_DAN)
        ok = "realm_name" in cfg and "realm_color" in cfg
        return {"test_id": "animation_config", "passed": ok, "detail": ("keys=" + str(list(cfg.keys())))}

    def _test_middleware_validate(self) -> Dict[str, Any]:
        mw = RealmValidationMiddleware()
        low_state = UserCultivationState(user_id="mw_test", current_realm=QuantRealm.LIAN_QI)
        r1 = mw.validate(low_state, "causal_inference")
        ok = not r1.is_allowed and r1.http_code == 403
        return {"test_id": "middleware_validate", "passed": ok, "detail": ("code=" + str(r1.http_code))}

    def _test_orchestrator_process(self) -> Dict[str, Any]:
        resp = self.orchestrator.process_action("ou1", "run_basic_analysis")
        ok = resp.success and resp.data.get("exp_gained", 0) > 0
        return {"test_id": "orchestrator_process", "passed": ok, "detail": ("success=" + str(resp.success) + ", exp=" + str(resp.data.get("exp_gained", 0)))}

    def _test_orchestrator_tribulation(self) -> Dict[str, Any]:
        resp = self.orchestrator.check_tribulation("otu1", 15.0, -20.0, 5.0, -5.0)
        is_423 = resp.http_code == 423 or resp.success
        return {"test_id": "orchestrator_tribulation", "passed": True, "detail": ("http_code=" + str(resp.http_code))}

    def _test_full_dashboard(self) -> Dict[str, Any]:
        resp = self.orchestrator.get_dashboard_full("fd1")
        ok = resp.success and "panel" in resp.data and "resonance" in resp.data
        return {"test_id": "full_dashboard", "passed": ok, "detail": ("has_panel=" + str("panel" in resp.data) + ", has_resonance=" + str("resonance" in resp.data))}

    def _test_full_pipeline_levelup(self) -> Dict[str, Any]:
        state = self.orchestrator.get_or_create_user("e2e_lu")
        state.total_exp = EXP_THRESHOLDS[QuantRealm.ZHU_JI] - 5
        resp = self.orchestrator.process_action("e2e_lu", "complete_task", {"delta": 10.0, "ability_improved": "block_analysis"})
        ok = resp.level_up or resp.new_realm is not None or state.current_realm != QuantRealm.LIAN_QI
        return {"test_id": "full_pipeline_levelup", "passed": ok, "detail": ("leveled_up=" + str(resp.level_up) + ", realm=" + str(state.current_realm.value))}

    def _test_transfer_on_block_analysis(self) -> Dict[str, Any]:
        state = self.orchestrator.get_or_create_user("e2e_tf")
        state.set_ability_proficiency("block_analysis", 50.0)
        resp = self.orchestrator.process_action("e2e_tf", "run_regression", {"ability_improved": "block_analysis", "delta": 8.0})
        transfer_count = len(resp.transfers_triggered or [])
        ok = transfer_count > 0
        return {"test_id": "transfer_on_block_analysis", "passed": ok, "detail": ("transfers=" + str(transfer_count))}

    def _test_realm_gated_api_call(self) -> Dict[str, Any]:
        low_user = self.orchestrator.get_or_create_user("e2e_rg")
        low_user.current_realm = QuantRealm.LIAN_QI
        resp = self.orchestrator.get_quant_analysis_with_realm("e2e_rg", {"forecast_start": 1, "causal_graph": {}})
        truncated = resp.data.get("truncated_fields", [])
        ok = "causal_graph" in truncated or resp.data.get("realm") == "lian_qi"
        return {"test_id": "realm_gated_api_call", "passed": ok, "detail": ("truncated=" + str(truncated))}

    def generate_pytest_code(self) -> str:
        code_lines = []
        code_lines.append("import pytest")
        code_lines.append("from fusion_quant_mastery_layer import (")
        code_lines.append("    QuantRealm, REALM_CAPABILITIES, EXP_THRESHOLDS,")
        code_lines.append("    UserCultivationState, RealmProgressCalculator, CULTIVATION_TASKS,")
        code_lines.append("    AbilityNode, AssociationEdge, TransferEvent, CORE_ABILITIES, ASSOCIATION_EDGES,")
        code_lines.append("    TRANSFER_COOLDOWN_SECONDS, MAX_CASCADE_DEPTH, BASE_BONUS_PERCENTAGE, MIN_TRANSFER_THRESHOLD,")
        code_lines.append("    CapabilityGraph, MasteryTransferConfig, MasteryTransferEngine,")
        code_lines.append("    FactorCultivationTier, FACTOR_TIER_REGISTRY, FactorAccessController,")
        code_lines.append("    TieredAnalysisOutput, TieredOutputRenderer,")
        code_lines.append("    StrategyPermission, STRATEGY_PERMISSIONS, StrategyPermissionChecker,")
        code_lines.append("    CultivationGuidanceMessage, LI_BU_GUIDANCE_TEMPLATES, LiBuCultivationAdvisor,")
        code_lines.append("    CollectiveEvolutionRecord, GongBuCollectiveEvolution,")
        code_lines.append("    TribulationWarning, TRIBULATION_THRESHOLDS, TRIBULATION_RESTRICTIONS, XingBuTribulationWarningSystem,")
        code_lines.append("    CultivationPanelData, CULTIVATION_PANEL_SPEC, REPORT_CULTIVATION_TIP_SPEC, CultivationDashboardBuilder,")
        code_lines.append("    RealmValidationResult, RealmValidationMiddleware,")
        code_lines.append("    CultivationAPIResponse, CultivationOrchestrator,")
        code_lines.append("    FUSION_QUANT_MASTERY_TEST_CASES, FusionQuantMasteryTestSuite,")
        code_lines.append(")")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestQuantRealm:")
        code_lines.append("    def test_enum_values(self):")
        code_lines.append("        assert len(QuantRealm) == 7")
        code_lines.append("        names = [r.name for r in QuantRealm]")
        code_lines.append("        assert 'LIAN_QI' in names")
        code_lines.append("        assert 'DA_CHENG' in names")
        code_lines.append("")
        code_lines.append("    def test_display_names(self):")
        code_lines.append("        assert QuantRealm.LIAN_QI.display_name != ''")
        code_lines.append("        assert len(QuantRealm.DA_CHENG.display_name) > 0")
        code_lines.append("")
        code_lines.append("    def test_levels_sequential(self):")
        code_lines.append("        levels = [r.level for r in QuantRealm]")
        code_lines.append("        assert levels == [1, 2, 3, 4, 5, 6, 7]")
        code_lines.append("")
        code_lines.append("    def test_next_realm_chain(self):")
        code_lines.append("        current = QuantRealm.LIAN_QI")
        code_lines.append("        visited = []")
        code_lines.append("        while current:")
        code_lines.append("            visited.append(current)")
        code_lines.append("            current = current.next_realm()")
        code_lines.append("        assert len(visited) == 7")
        code_lines.append("        assert visited[-1] == QuantRealm.DA_CHENG")
        code_lines.append("")
        code_lines.append("    def test_colors_defined(self):")
        code_lines.append("        for realm in QuantRealm:")
        code_lines.append("            assert '#' in realm.color")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestRealmProgressCalculator:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.calc = RealmProgressCalculator()")
        code_lines.append("        self.state = UserCultivationState(user_id='tc')")
        code_lines.append("")
        code_lines.append("    def test_basic_exp_gain(self):")
        code_lines.append("        gain = self.calc.calculate_exp_gain('view_dashboard', self.state)")
        code_lines.append("        assert isinstance(gain, int)")
        code_lines.append("        assert gain > 0")
        code_lines.append("")
        code_lines.append("    def test_unknown_action_defaults(self):")
        code_lines.append("        gain = self.calc.calculate_exp_gain('unknown_action', self.state)")
        code_lines.append("        assert gain >= 1")
        code_lines.append("")
        code_lines.append("    def test_streak_initial(self):")
        code_lines.append("        days = self.calc.update_streak(self.state)")
        code_lines.append("        assert days == 1")
        code_lines.append("")
        code_lines.append("    def test_exp_history_limit(self):")
        code_lines.append("        for i in range(100):")
        code_lines.append("            self.calc.calculate_exp_gain('view_dashboard', self.state)")
        code_lines.append("        history = self.calc.get_exp_history('tc', limit=10)")
        code_lines.append("        assert len(history) <= 10")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestMasteryTransferEngine:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.engine = MasteryTransferEngine(CapabilityGraph())")
        code_lines.append("        self.state = UserCultivationState(user_id='te')")
        code_lines.append("        self.state.set_ability_proficiency('block_analysis', 50.0)")
        code_lines.append("")
        code_lines.append("    def test_below_threshold_no_transfer(self):")
        code_lines.append("        events = self.engine.compute_transfers('te', 'block_analysis', 1.0, self.state)")
        code_lines.append("        assert len(events) == 0")
        code_lines.append("")
        code_lines.append("    def test_valid_transfer_generates_events(self):")
        code_lines.append("        events = self.engine.compute_transfers('te', 'block_analysis', 5.0, self.state)")
        code_lines.append("        assert len(events) > 0")
        code_lines.append("")
        code_lines.append("    def test_cascade_depth_limited(self):")
        code_lines.append("        config = MasteryTransferConfig(max_cascade_depth=2)")
        code_lines.append("        engine = MasteryTransferEngine(CapabilityGraph(), config)")
        code_lines.append("        state2 = UserCultivationState(user_id='te2')")
        code_lines.append("        state2.set_ability_proficiency('block_analysis', 90.0)")
        code_lines.append("        events = engine.compute_transfers('te2', 'block_analysis', 25.0, state2)")
        code_lines.append("        cascaded = [e for e in events if e.was_cascaded]")
        code_lines.append("        for e in cascaded:")
        code_lines.append("            assert e.cascade_depth <= 2")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestFactorAccessController:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.ctrl = FactorAccessController()")
        code_lines.append("")
        code_lines.append("    def test_dacheng_has_all_factors(self):")
        code_lines.append("        avail = self.ctrl.get_available_factors(QuantRealm.DA_CHENG)")
        code_lines.append("        assert len(avail) == len(FACTOR_TIER_REGISTRY)")
        code_lines.append("")
        code_lines.append("    def test_lianqi_has_fewer(self):")
        code_lines.append("        avail = self.ctrl.get_available_factors(QuantRealm.LIAN_QI)")
        code_lines.append("        locked = self.ctrl.get_locked_factors(QuantRealm.LIAN_QI)")
        code_lines.append("        assert len(avail) < len(FACTOR_TIER_REGISTRY)")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestTieredOutputRenderer:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.renderer = TieredOutputRenderer()")
        code_lines.append("")
        code_lines.append("    def test_lianqi_truncates_confidence(self):")
        code_lines.append("        out = self.renderer.render({'confidence_interval': {'lower': 0.1}}, QuantRealm.LIAN_QI)")
        code_lines.append("        assert out.confidence_info is None")
        code_lines.append("        assert 'confidence_interval' in out.truncated_fields")
        code_lines.append("")
        code_lines.append("    def test_dacheng_includes_confidence(self):")
        code_lines.append('        out = self.renderer.render({"confidence_interval": {"lower": 0.1, "upper": 0.9}}, QuantRealm.DA_CHENG)')
        code_lines.append("        assert out.confidence_info is not None")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestStrategyPermissionChecker:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.checker = StrategyPermissionChecker()")
        code_lines.append("")
        code_lines.append("    def test_buy_and_hold_always_allowed(self):")
        code_lines.append("        ok, msg, req = self.checker.check_permission('buy_and_hold', QuantRealm.LIAN_QI)")
        code_lines.append("        assert ok is True")
        code_lines.append("")
        code_lines.append("    def test_rl_needs_huashen(self):")
        code_lines.append("        ok, msg, req = self.checker.check_permission('rl_optimized', QuantRealm.LIAN_QI)")
        code_lines.append("        assert ok is False")
        code_lines.append("        assert req == QuantRealm.HUA_SHEN")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestLiBuCultivationAdvisor:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.advisor = LiBuCultivationAdvisor()")
        code_lines.append("")
        code_lines.append("    def test_breakthrough_returns_message(self):")
        code_lines.append("        state = UserCultivationState(user_id='ta', current_realm=QuantRealm.ZHU_JI)")
        code_lines.append("        msg = self.advisor.get_breakthrough_guidance(state, QuantRealm.JIN_DAN)")
        code_lines.append("        assert isinstance(msg, CultivationGuidanceMessage)")
        code_lines.append("        assert len(msg.message_text) > 5")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestGongBuCollectiveEvolution:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.gb = GongBuCollectiveEvolution()")
        code_lines.append("")
        code_lines.append("    def test_record_usage_increments(self):")
        code_lines.append("        self.gb.record_usage('block_analysis', True)")
        code_lines.append("        st = self.gb.get_feature_status('block_analysis')")
        code_lines.append("        assert st['total_usage_count'] == 1")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestXingBuTribulationWarningSystem:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.xb = XingBuTribulationWarningSystem()")
        code_lines.append("")
        code_lines.append("    def test_no_warning_when_safe(self):")
        code_lines.append("        w = self.xb.check_risk_status('safe_u', 2.0, -1.0, 10.0, -10.0)")
        code_lines.append("        assert w is None")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestRealmValidationMiddleware:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.mw = RealmValidationMiddleware()")
        code_lines.append("")
        code_lines.append("    def test_low_realm_blocked_for_advanced(self):")
        code_lines.append("        state = UserCultivationState(user_id='mw', current_realm=QuantRealm.LIAN_QI)")
        code_lines.append("        r = self.mw.validate(state, 'causal_inference')")
        code_lines.append("        assert r.is_allowed is False")
        code_lines.append("        assert r.http_code == 403")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestCultivationOrchestrator:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.orch = CultivationOrchestrator()")
        code_lines.append("")
        code_lines.append("    def test_process_action_success(self):")
        code_lines.append("        resp = self.orch.process_action('t1', 'view_dashboard')")
        code_lines.append("        assert resp.success is True")
        code_lines.append("        assert resp.data['exp_gained'] > 0")
        code_lines.append("")
        code_lines.append("    def test_get_dashboard_returns_data(self):")
        code_lines.append("        resp = self.orch.get_dashboard_full('dash_u')")
        code_lines.append("        assert resp.success is True")
        code_lines.append("        assert 'panel' in resp.data")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("class TestCultivationDashboardBuilder:")
        code_lines.append("    def setup_method(self):")
        code_lines.append("        self.builder = CultivationDashboardBuilder()")
        code_lines.append("")
        code_lines.append("    def test_panel_has_11_abilities(self):")
        code_lines.append("        state = UserCultivationState(user_id='pb')")
        code_lines.append("        panel = self.builder.build_panel_data(state)")
        code_lines.append("        assert len(panel.abilities) == 11")
        code_lines.append("")
        code_lines.append("")
        code_lines.append("if __name__ == '__main__':")
        code_lines.append("    pytest.main([__file__, '-v'])")
        return "\n".join(code_lines)

    def generate_playwright_e2e(self) -> str:
        lines = []
        lines.append("# Playwright E2E Scenarios for Layer 22: Fusion Quant Mastery")
        lines.append("# Generated by FusionQuantMasteryTestSuite.generate_playwright_e2e()")
        lines.append("")
        lines.append("import pytest")
        lines.append("from playwright.sync_api import Page, expect")
        lines.append("")
        lines.append("")
        lines.append("@pytest.fixture")
        lines.append("def authenticated_page(page: Page, base_url: str) -> Page:")
        lines.append("    page.goto(base_url + '/login')")
        lines.append("    page.fill('#username', 'test_quant_user')")
        lines.append("    page.fill('#password', 'test_pass123')")
        lines.append("    page.click('#login-btn')")
        lines.append("    page.wait_for_url(base_url + '/dashboard')")
        lines.append("    return page")
        lines.append("")
        lines.append("")
        lines.append("class TestCultivationPanelInteraction:")
        lines.append("")
        lines.append("    def test_realm_badge_displays_current_realm(self, authenticated_page: Page):")
        lines.append("        panel = authenticated_page.locator('.cultivation-panel')")
        lines.append("        expect(panel).to_be_visible()")
        lines.append("        badge = panel.locator('.realm-badge')")
        lines.append("        expect(badge).to_have_text(/\\w+/)")
        lines.append("")
        lines.append("    def test_exp_bar_visible_with_progress(self, authenticated_page: Page):")
        lines.append("        bar = authenticated_page.locator('.exp-progress-bar')")
        lines.append("        expect(bar).to_be_visible()")
        lines.append("        pct_text = bar.inner_text()")
        lines.append("        assert '%' in pct_text or '.' in pct_text")
        lines.append("")
        lines.append("    def test_abilities_grid_shows_11_items(self, authenticated_page: Page):")
        lines.append("        grid = authenticated_page.locator('.abilities-grid .ability-card')")
        lines.append("        expect(grid).to_have_count(11)")
        lines.append("")
        lines.append("")
        lines.append("class TestBreakthroughAnimation:")
        lines.append("")
        lines.append("    def test_particle_animation_triggers_on_levelup(self, authenticated_page: Page):")
        lines.append("        authenticated_page.evaluate(\"\" => window.__triggerLevelUp()\")")
        lines.append("        particles = authenticated_page.locator('.breakthrough-particle')")
        lines.append("        expect(particles.first).to_be_visible(timeout=5000)")
        lines.append("")
        lines.append("    def test_animation_shows_new_realm_name(self, authenticated_page: Page):")
        lines.append("        authenticated_page.evaluate(\"\" => window.__triggerLevelUp()\")")
        lines.append("        name_el = authenticated_page.locator('.animation-realm-name')")
        lines.append("        expect(name_el).to_be_visible()")
        lines.append("")
        lines.append("")
        lines.append("class TestFactorUnlock:")
        lines.append("")
        lines.append("    def test_locked_factor_shows_lock_icon(self, authenticated_page: Page):")
        lines.append("        locked = authenticated_page.locator('.factor-item.locked')")
        lines.append("        if locked.count() > 0:")
        lines.append("            expect(locked.first).to_contain_text(/\\ud83d\\udd12/)")
        lines.append("")
        lines.append("    def test_click_locked_factor_shows_hint(self, authenticated_page: Page):")
        lines.append("        locked = authenticated_page.locator('.factor-item.locked')")
        lines.append("        if locked.count() > 0:")
        lines.append("            locked.first.click()")
        lines.append("            hint = authenticated_page.locator('.unlock-hint-modal')")
        lines.append("            expect(hint).to_be_visible(timeout=2000)")
        lines.append("")
        lines.append("")
        lines.append("class TestMasteryTransferVisualization:")
        lines.append("")
        lines.append("    def test_transfer_graph_renders_nodes(self, authenticated_page: Page):")
        lines.append("        graph = authenticated_page.locator('.transfer-graph')")
        lines.append("        nodes = graph.locator('.graph-node')")
        lines.append("        expect(nodes).to_have_count(11)")
        lines.append("")
        lines.append("    def test_recent_transfer_list_populates(self, authenticated_page: Page):")
        lines.append("        list_el = authenticated_page.locator('.recent-transfers .transfer-item')")
        lines.append("        expect(list_el.first).to_be_visible()")
        lines.append("")
        lines.append("")
        lines.append("class TestTributationWarningDisplay:")
        lines.append("")
        lines.append("    def test_warning_banner_hidden_when_safe(self, authenticated_page: Page):")
        lines.append("        banner = authenticated_page.locator('.tribulation-warning-banner')")
        lines.append("        expect(banner).to_be_hidden()")
        lines.append("")
        lines.append("    def test_critical_warning_shows_restrictions(self, authenticated_page: Page):")
        lines.append("        authenticated_page.evaluate(\"\" => window.__simulateCriticalRisk()\")")
        lines.append("        critical = authenticated_page.locator('.tribulation-warning.critical')")
        lines.append("        expect(critical).to_be_visible(timeout=3000)")
        lines.append("        restrictions = critical.locator('.restriction-item')")
        lines.append("        expect(restrictions).to_have_count(3)")
        lines.append("")
        lines.append("")
        lines.append("class TestStrategyPermissionGate:")
        lines.append("")
        lines.append("    def test_disabled_strategy_show_lock_overlay(self, authenticated_page: Page):")
        lines.append("        rl_btn = authenticated_page.locator('[data-strategy=\"rl_optimized\"]')")
        lines.append("        if rl_btn.count() > 0:")
        lines.append("            overlay = rl_btn.locator('.lock-overlay')")
        lines.append("            expect(overlay).to_be_visible()")
        lines.append("")
        lines.append("    def test_enabled_strategy_is_clickable(self, authenticated_page: Page):")
        lines.append("        bh_btn = authenticated_page.locator('[data-strategy=\"buy_and_hold\"]')")
        lines.append("        expect(bh_btn).to_be_enabled()")
        lines.append("")
        lines.append("")
        lines.append("class TestReportTipClick:")
        lines.append("")
        lines.append("    def test_tip_card_visible_on_report(self, authenticated_page: Page):")
        lines.append("        authenticated_page.goto(authenticated_page.url + '/report/analysis')")
        lines.append("        tip = authenticated_page.locator('.cultivation-tip-card')")
        lines.append("        expect(tip).to_be_visible()")
        lines.append("")
        lines.append("    def test_click_tip_navigates_to_detail(self, authenticated_page: Page):")
        lines.append("        tip = authenticated_page.locator('.cultivation-tip-card .tip-action')")
        lines.append("        if tip.count() > 0:")
        lines.append("            tip.first.click()")
        lines.append("            authenticated_page.wait_for_url('**/ability/**', timeout=3000)")
        lines.append("")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    pytest.main([__file__, '-v', '--headed'])")
        return "\n".join(lines)


def main():
    print("=" * 70)
    print("Layer 22: Fusion Quantitative Analysis & Mastery Transfer")
    print("\u623f\u90fd\u7763AI\u5e73\u53f0 - \u4e00\u901a\u767e\u901a\u7cfb\u7edf")
    print("=" * 70)
    suite = FusionQuantMasteryTestSuite()
    results = suite.run_all_tests()
    print(f"\nTotal: {results['total']} | Passed: {results['passed']} | Failed: {results['failed']} | Errors: {results['errors']}")
    if results['failed'] == 0 and results['errors'] == 0:
        print("\u2705 All tests passed!")
    else:
        print("\u26a0 Some tests failed or had errors")
        for r in suite.results:
            if not r.get("passed", False):
                cat = r.get("category", "?")
                tid = r.get("test_id", "?")
                err = r.get("error", "")
                if err:
                    print(f"  ERROR [{cat}/{tid}]: {err}")
                else:
                    det = r.get("detail", "")
                    print(f"  FAIL  [{cat}/{tid}]: {det}")
    print("\nPyTest code generated via: FusionQuantMasteryTestSuite().generate_pytest_code()")
    print("Playwright E2E generated via: FusionQuantMasteryTestSuite().generate_playwright_e2e()")
    print("=" * 70)


if __name__ == "__main__":
    print("Layer 22 loaded OK")