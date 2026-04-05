"""
积分通胀通缩机制 - 经济稳定系统
根据平台活跃度调整积分产出与消耗，稳定经济系统
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


class EconomicState(Enum):
    STABLE = "stable"
    INFLATIONARY = "inflationary"
    DEFLATIONARY = "deflationary"
    CRITICAL_INFLATION = "critical_inflation"
    CRITICAL_DEFLATION = "critical_deflation"


class AdjustmentType(Enum):
    PRODUCTION_RATE = "production_rate"
    CONSUMPTION_RATE = "consumption_rate"
    REWARD_MULTIPLIER = "reward_multiplier"
    COST_MULTIPLIER = "cost_multiplier"
    TAX_RATE = "tax_rate"


@dataclass
class EconomicIndicator:
    timestamp: datetime
    total_integral_supply: float
    total_users: int
    active_users_24h: int
    avg_balance: float
    median_balance: float
    gini_coefficient: float
    velocity_of_money: float
    production_rate: float
    consumption_rate: float
    inflation_rate: float
    

@dataclass
class AdjustmentPolicy:
    policy_id: str
    adjustment_type: AdjustmentType
    adjustment_value: float
    reason: str
    effective_from: datetime
    effective_until: Optional[datetime] = None
    is_active: bool = True


@dataclass
class UserEconomicProfile:
    user_id: str
    balance: float
    total_earned: float
    total_spent: float
    last_activity: datetime
    activity_score: float = 0.0
    contribution_score: float = 0.0


class EconomicMonitor:
    def __init__(self):
        self._indicators: List[EconomicIndicator] = []
        self._user_profiles: Dict[str, UserEconomicProfile] = {}
        self._transaction_history: List[Dict[str, Any]] = []
        
    def record_transaction(
        self,
        user_id: str,
        amount: float,
        transaction_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._transaction_history.append({
            "user_id": user_id,
            "amount": amount,
            "type": transaction_type,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        })
        
        profile = self._user_profiles.get(user_id)
        if profile:
            if transaction_type == "earn":
                profile.total_earned += amount
                profile.balance += amount
            elif transaction_type == "spend":
                profile.total_spent += amount
                profile.balance -= amount
            profile.last_activity = datetime.now()
            
    def calculate_indicators(self) -> EconomicIndicator:
        total_supply = sum(p.balance for p in self._user_profiles.values())
        total_users = len(self._user_profiles)
        
        cutoff = datetime.now() - timedelta(hours=24)
        active_users = len([
            p for p in self._user_profiles.values()
            if p.last_activity >= cutoff
        ])
        
        balances = [p.balance for p in self._user_profiles.values()]
        avg_balance = sum(balances) / len(balances) if balances else 0
        sorted_balances = sorted(balances)
        median_balance = sorted_balances[len(sorted_balances) // 2] if sorted_balances else 0
        
        gini = self._calculate_gini(balances)
        
        velocity = self._calculate_velocity()
        
        production, consumption = self._calculate_rates()
        
        prev_indicators = self._indicators[-1] if self._indicators else None
        inflation_rate = 0.0
        if prev_indicators and prev_indicators.total_integral_supply > 0:
            inflation_rate = (total_supply - prev_indicators.total_integral_supply) / prev_indicators.total_integral_supply * 100
            
        indicator = EconomicIndicator(
            timestamp=datetime.now(),
            total_integral_supply=total_supply,
            total_users=total_users,
            active_users_24h=active_users,
            avg_balance=avg_balance,
            median_balance=median_balance,
            gini_coefficient=gini,
            velocity_of_money=velocity,
            production_rate=production,
            consumption_rate=consumption,
            inflation_rate=inflation_rate
        )
        
        self._indicators.append(indicator)
        return indicator
        
    def _calculate_gini(self, values: List[float]) -> float:
        if not values or sum(values) == 0:
            return 0.0
            
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = 0
        total = 0
        
        for i, value in enumerate(sorted_values):
            cumsum += value
            total += (2 * (i + 1) - n - 1) * value
            
        return total / (n * sum(sorted_values))
        
    def _calculate_velocity(self) -> float:
        cutoff = datetime.now() - timedelta(days=7)
        recent_transactions = [
            t for t in self._transaction_history
            if t["timestamp"] >= cutoff
        ]
        
        total_volume = sum(abs(t["amount"]) for t in recent_transactions)
        total_supply = sum(p.balance for p in self._user_profiles.values())
        
        if total_supply == 0:
            return 0.0
            
        return total_volume / total_supply
        
    def _calculate_rates(self) -> Tuple[float, float]:
        cutoff = datetime.now() - timedelta(days=1)
        recent = [
            t for t in self._transaction_history
            if t["timestamp"] >= cutoff
        ]
        
        production = sum(t["amount"] for t in recent if t["type"] == "earn")
        consumption = sum(abs(t["amount"]) for t in recent if t["type"] == "spend")
        
        return production, consumption


class InflationController:
    def __init__(self, monitor: EconomicMonitor):
        self.monitor = monitor
        self._policies: List[AdjustmentPolicy] = []
        self._target_inflation_rate = 2.0
        self._inflation_tolerance = 1.0
        self._current_multipliers = {
            "reward_multiplier": 1.0,
            "cost_multiplier": 1.0,
            "tax_rate": 0.0
        }
        
    def assess_economic_state(self, indicator: EconomicIndicator) -> EconomicState:
        inflation = indicator.inflation_rate
        
        if inflation > 10:
            return EconomicState.CRITICAL_INFLATION
        elif inflation > 5:
            return EconomicState.INFLATIONARY
        elif inflation < -5:
            return EconomicState.CRITICAL_DEFLATION
        elif inflation < -2:
            return EconomicState.DEFLATIONARY
        else:
            return EconomicState.STABLE
            
    def generate_adjustment_policy(
        self, 
        state: EconomicState,
        indicator: EconomicIndicator
    ) -> Optional[AdjustmentPolicy]:
        if state == EconomicState.STABLE:
            return None
            
        policy_id = f"policy_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if state == EconomicState.CRITICAL_INFLATION:
            return AdjustmentPolicy(
                policy_id=policy_id,
                adjustment_type=AdjustmentType.REWARD_MULTIPLIER,
                adjustment_value=0.7,
                reason=f"严重通胀({indicator.inflation_rate:.2f}%)，降低积分产出",
                effective_from=datetime.now()
            )
            
        elif state == EconomicState.INFLATIONARY:
            return AdjustmentPolicy(
                policy_id=policy_id,
                adjustment_type=AdjustmentType.REWARD_MULTIPLIER,
                adjustment_value=0.85,
                reason=f"通胀压力({indicator.inflation_rate:.2f}%)，适度降低产出",
                effective_from=datetime.now()
            )
            
        elif state == EconomicState.CRITICAL_DEFLATION:
            return AdjustmentPolicy(
                policy_id=policy_id,
                adjustment_type=AdjustmentType.REWARD_MULTIPLIER,
                adjustment_value=1.5,
                reason=f"严重通缩({indicator.inflation_rate:.2f}%)，增加积分产出",
                effective_from=datetime.now()
            )
            
        elif state == EconomicState.DEFLATIONARY:
            return AdjustmentPolicy(
                policy_id=policy_id,
                adjustment_type=AdjustmentType.REWARD_MULTIPLIER,
                adjustment_value=1.2,
                reason=f"通缩压力({indicator.inflation_rate:.2f}%)，适度增加产出",
                effective_from=datetime.now()
            )
            
        return None
        
    def apply_policy(self, policy: AdjustmentPolicy):
        self._policies.append(policy)
        
        if policy.adjustment_type == AdjustmentType.REWARD_MULTIPLIER:
            self._current_multipliers["reward_multiplier"] = policy.adjustment_value
        elif policy.adjustment_type == AdjustmentType.COST_MULTIPLIER:
            self._current_multipliers["cost_multiplier"] = policy.adjustment_value
        elif policy.adjustment_type == AdjustmentType.TAX_RATE:
            self._current_multipliers["tax_rate"] = policy.adjustment_value
            
        logger.info(f"Applied economic policy: {policy.policy_id} - {policy.reason}")
        
    def get_current_multipliers(self) -> Dict[str, float]:
        return self._current_multipliers.copy()
        
    def get_active_policies(self) -> List[AdjustmentPolicy]:
        return [p for p in self._policies if p.is_active]


class DynamicRewardCalculator:
    def __init__(self, controller: InflationController):
        self.controller = controller
        self._base_rewards = {
            "task_completion": 10,
            "consultation": 5,
            "report_generation": 20,
            "referral": 50,
            "daily_login": 2,
            "content_creation": 15,
            "quality_bonus": 10
        }
        self._activity_bonus_threshold = 0.7
        
    def calculate_reward(
        self,
        user_id: str,
        reward_type: str,
        quality_score: float = 1.0,
        user_activity_score: float = 0.5
    ) -> float:
        base_reward = self._base_rewards.get(reward_type, 0)
        
        multipliers = self.controller.get_current_multipliers()
        reward_multiplier = multipliers["reward_multiplier"]
        
        quality_multiplier = 0.5 + quality_score
        
        activity_bonus = 1.0
        if user_activity_score > self._activity_bonus_threshold:
            activity_bonus = 1.0 + (user_activity_score - self._activity_bonus_threshold) * 0.5
            
        final_reward = base_reward * reward_multiplier * quality_multiplier * activity_bonus
        
        return round(final_reward, 2)
        
    def calculate_cost(
        self,
        user_id: str,
        service_type: str,
        base_cost: float
    ) -> float:
        multipliers = self.controller.get_current_multipliers()
        cost_multiplier = multipliers["cost_multiplier"]
        tax_rate = multipliers["tax_rate"]
        
        adjusted_cost = base_cost * cost_multiplier
        tax = adjusted_cost * tax_rate
        
        return round(adjusted_cost + tax, 2)


class EconomicStabilizer:
    def __init__(self):
        self.monitor = EconomicMonitor()
        self.controller = InflationController(self.monitor)
        self.reward_calculator = DynamicRewardCalculator(self.controller)
        self._adjustment_interval = 3600
        self._running = False
        
    async def start_monitoring(self):
        self._running = True
        while self._running:
            await self._run_adjustment_cycle()
            await asyncio.sleep(self._adjustment_interval)
            
    async def stop_monitoring(self):
        self._running = False
        
    async def _run_adjustment_cycle(self):
        indicator = self.monitor.calculate_indicators()
        state = self.controller.assess_economic_state(indicator)
        
        logger.info(f"Economic state: {state.value}, inflation: {indicator.inflation_rate:.2f}%")
        
        if state != EconomicState.STABLE:
            policy = self.controller.generate_adjustment_policy(state, indicator)
            if policy:
                self.controller.apply_policy(policy)
                
    def register_user(self, user_id: str, initial_balance: float = 0):
        self.monitor._user_profiles[user_id] = UserEconomicProfile(
            user_id=user_id,
            balance=initial_balance,
            total_earned=initial_balance,
            total_spent=0,
            last_activity=datetime.now()
        )
        
    def process_earning(
        self,
        user_id: str,
        reward_type: str,
        quality_score: float = 1.0
    ) -> float:
        profile = self.monitor._user_profiles.get(user_id)
        if not profile:
            self.register_user(user_id)
            profile = self.monitor._user_profiles[user_id]
            
        reward = self.reward_calculator.calculate_reward(
            user_id, reward_type, quality_score, profile.activity_score
        )
        
        self.monitor.record_transaction(user_id, reward, "earn", {
            "reward_type": reward_type,
            "quality_score": quality_score
        })
        
        return reward
        
    def process_spending(
        self,
        user_id: str,
        service_type: str,
        base_cost: float
    ) -> Tuple[bool, float]:
        profile = self.monitor._user_profiles.get(user_id)
        if not profile:
            return False, 0
            
        cost = self.reward_calculator.calculate_cost(user_id, service_type, base_cost)
        
        if profile.balance < cost:
            return False, cost
            
        self.monitor.record_transaction(user_id, -cost, "spend", {
            "service_type": service_type
        })
        
        return True, cost
        
    def get_user_balance(self, user_id: str) -> float:
        profile = self.monitor._user_profiles.get(user_id)
        return profile.balance if profile else 0
        
    def get_economic_report(self) -> Dict[str, Any]:
        if not self.monitor._indicators:
            return {"status": "no_data"}
            
        latest = self.monitor._indicators[-1]
        state = self.controller.assess_economic_state(latest)
        policies = self.controller.get_active_policies()
        
        return {
            "economic_state": state.value,
            "indicators": {
                "total_supply": latest.total_integral_supply,
                "total_users": latest.total_users,
                "active_users_24h": latest.active_users_24h,
                "avg_balance": round(latest.avg_balance, 2),
                "median_balance": round(latest.median_balance, 2),
                "gini_coefficient": round(latest.gini_coefficient, 3),
                "velocity_of_money": round(latest.velocity_of_money, 2),
                "inflation_rate": round(latest.inflation_rate, 2)
            },
            "current_multipliers": self.controller.get_current_multipliers(),
            "active_policies": [
                {
                    "policy_id": p.policy_id,
                    "type": p.adjustment_type.value,
                    "value": p.adjustment_value,
                    "reason": p.reason
                }
                for p in policies
            ]
        }


economic_stabilizer = EconomicStabilizer()


def get_economic_stabilizer() -> EconomicStabilizer:
    return economic_stabilizer


async def start_economic_monitoring():
    await economic_stabilizer.start_monitoring()
