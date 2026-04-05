"""
逆强化学习防御模块
Inverse Reinforcement Learning Defense Module

实现从攻击轨迹推断奖励函数、防御策略优化、红蓝对抗训练等功能
"""

import asyncio
import copy
import hashlib
import json
import logging
import math
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class AttackType(Enum):
    DDOS = "ddos"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PROMPT_INJECTION = "prompt_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    BRUTE_FORCE = "brute_force"
    PHISHING = "phishing"
    MALWARE = "malware"
    ZERO_DAY = "zero_day"
    INSIDER_THREAT = "insider_threat"


class DefenseAction(Enum):
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ISOLATE = "isolate"
    ALERT = "alert"
    DECOY = "decoy"
    PATCH = "patch"
    QUARANTINE = "quarantine"
    LOG_ANALYSIS = "log_analysis"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    ADAPTIVE_FIREWALL = "adaptive_firewall"


class GameResult(Enum):
    ATTACKER_WIN = "attacker_win"
    DEFENDER_WIN = "defender_win"
    DRAW = "draw"
    ONGOING = "ongoing"


@dataclass
class StateVector:
    state_id: str
    features: Dict[str, float]
    timestamp: datetime
    
    def to_vector(self) -> List[float]:
        return list(self.features.values())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "features": self.features,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ActionRecord:
    action_id: str
    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
        }


@dataclass
class AttackTrajectory:
    trajectory_id: str
    attack_type: AttackType
    states: List[StateVector]
    actions: List[ActionRecord]
    rewards: List[float]
    final_result: GameResult
    attacker_id: str
    defender_id: str
    start_time: datetime
    end_time: datetime
    total_steps: int
    success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "attack_type": self.attack_type.value,
            "states": [s.to_dict() for s in self.states],
            "actions": [a.to_dict() for a in self.actions],
            "rewards": self.rewards,
            "final_result": self.final_result.value,
            "attacker_id": self.attacker_id,
            "defender_id": self.defender_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_steps": self.total_steps,
            "success_rate": self.success_rate,
        }


@dataclass
class RewardWeights:
    weights: Dict[str, float]
    feature_names: List[str]
    last_updated: datetime
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "feature_names": self.feature_names,
            "last_updated": self.last_updated.isoformat(),
            "confidence": self.confidence,
        }
    
    def get_weight(self, feature: str) -> float:
        return self.weights.get(feature, 0.0)


@dataclass
class DefenseStrategy:
    strategy_id: str
    name: str
    rules: List[Dict[str, Any]]
    risk_weights: Dict[str, float]
    priority: int
    created_at: datetime
    success_rate: float = 0.0
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "rules": self.rules,
            "risk_weights": self.risk_weights,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
        }


class RewardFunctionInference:
    """奖励函数推断器 - 最大熵逆强化学习"""
    
    def __init__(self, feature_dim: int = 20, learning_rate: float = 0.01):
        self.feature_dim = feature_dim
        self.learning_rate = learning_rate
        
        self.feature_names = [
            "request_rate", "error_rate", "latency", "payload_size",
            "auth_failures", "data_volume", "unique_ips", "port_diversity",
            "time_pattern", "geo_diversity", "protocol_mix", "header_anomaly",
            "content_entropy", "session_duration", "api_call_pattern",
            "resource_usage", "network_flow", "user_behavior_score",
            "system_call_pattern", "file_access_pattern",
        ]
        
        self.reward_weights = RewardWeights(
            weights={name: random.gauss(0, 0.1) for name in self.feature_names},
            feature_names=self.feature_names,
            last_updated=datetime.now(),
            confidence=0.5,
        )
        
        self.trajectories: List[AttackTrajectory] = []
        self._lock = threading.Lock()
        
        self.stats = {
            "total_inferences": 0,
            "weight_updates": 0,
            "trajectories_processed": 0,
        }
    
    def add_trajectory(self, trajectory: AttackTrajectory):
        with self._lock:
            self.trajectories.append(trajectory)
            self.stats["trajectories_processed"] += 1
    
    def extract_features(self, state: StateVector) -> List[float]:
        vector = [0.0] * self.feature_dim
        
        for i, name in enumerate(self.feature_names):
            if name in state.features:
                vector[i] = state.features[name]
        
        return vector
    
    def compute_state_reward(self, state: StateVector) -> float:
        features = self.extract_features(state)
        
        reward = 0.0
        for i, name in enumerate(self.feature_names):
            reward += self.reward_weights.get_weight(name) * features[i]
        
        return reward
    
    def compute_trajectory_reward(self, trajectory: AttackTrajectory) -> float:
        total_reward = 0.0
        
        for state in trajectory.states:
            total_reward += self.compute_state_reward(state)
        
        return total_reward / max(len(trajectory.states), 1)
    
    def infer_weights(self, epochs: int = 100) -> RewardWeights:
        self.stats["total_inferences"] += 1
        
        if not self.trajectories:
            return self.reward_weights
        
        expert_trajectories = [
            t for t in self.trajectories if t.final_result == GameResult.ATTACKER_WIN
        ]
        
        if not expert_trajectories:
            return self.reward_weights
        
        expert_features = []
        for traj in expert_trajectories:
            traj_features = []
            for state in traj.states:
                traj_features.append(self.extract_features(state))
            if traj_features:
                avg_features = [
                    sum(f[i] for f in traj_features) / len(traj_features)
                    for i in range(self.feature_dim)
                ]
                expert_features.append(avg_features)
        
        if not expert_features:
            return self.reward_weights
        
        expert_avg = [
            sum(f[i] for f in expert_features) / len(expert_features)
            for i in range(self.feature_dim)
        ]
        
        for epoch in range(epochs):
            policy_features = self._sample_policy_features()
            
            feature_diff = [
                expert_avg[i] - policy_features[i]
                for i in range(self.feature_dim)
            ]
            
            for i, name in enumerate(self.feature_names):
                current = self.reward_weights.weights.get(name, 0.0)
                self.reward_weights.weights[name] = current + self.learning_rate * feature_diff[i]
            
            self.stats["weight_updates"] += 1
        
        self.reward_weights.last_updated = datetime.now()
        self.reward_weights.confidence = min(1.0, len(expert_trajectories) / 100)
        
        return self.reward_weights
    
    def _sample_policy_features(self) -> List[float]:
        if not self.trajectories:
            return [0.0] * self.feature_dim
        
        sampled_traj = random.choice(self.trajectories)
        
        features = []
        for state in sampled_traj.states:
            features.append(self.extract_features(state))
        
        if not features:
            return [0.0] * self.feature_dim
        
        return [
            sum(f[i] for f in features) / len(features)
            for i in range(self.feature_dim)
        ]
    
    def get_risk_score(self, state: StateVector) -> float:
        reward = self.compute_state_reward(state)
        
        risk = 1.0 / (1.0 + math.exp(-reward))
        
        return risk


class DefenseStrategyOptimizer:
    """防御策略优化器"""
    
    def __init__(self, reward_inference: RewardFunctionInference):
        self.reward_inference = reward_inference
        
        self.strategies: Dict[str, DefenseStrategy] = {}
        self.strategy_history: List[Dict[str, Any]] = []
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_optimizations": 0,
            "strategies_created": 0,
            "strategies_updated": 0,
            "best_strategy_changes": 0,
        }
        
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        default_strategies = [
            DefenseStrategy(
                strategy_id="strategy_ddos_001",
                name="DDoS防护策略",
                rules=[
                    {"condition": "request_rate > 1000", "action": "rate_limit"},
                    {"condition": "unique_ips > 10000", "action": "adaptive_firewall"},
                ],
                risk_weights={"request_rate": 0.8, "unique_ips": 0.6},
                priority=1,
                created_at=datetime.now(),
            ),
            DefenseStrategy(
                strategy_id="strategy_sql_001",
                name="SQL注入防护策略",
                rules=[
                    {"condition": "payload_contains_sql", "action": "block"},
                    {"condition": "error_rate > 0.1", "action": "alert"},
                ],
                risk_weights={"error_rate": 0.7, "payload_size": 0.5},
                priority=2,
                created_at=datetime.now(),
            ),
            DefenseStrategy(
                strategy_id="strategy_brute_001",
                name="暴力破解防护策略",
                rules=[
                    {"condition": "auth_failures > 5", "action": "block_ip"},
                    {"condition": "auth_failures > 3", "action": "rate_limit"},
                ],
                risk_weights={"auth_failures": 0.9},
                priority=1,
                created_at=datetime.now(),
            ),
        ]
        
        for strategy in default_strategies:
            self.strategies[strategy.strategy_id] = strategy
            self.stats["strategies_created"] += 1
    
    def optimize_strategy(
        self,
        trajectories: List[AttackTrajectory]
    ) -> DefenseStrategy:
        self.stats["total_optimizations"] += 1
        
        reward_weights = self.reward_inference.infer_weights()
        
        attack_patterns = self._analyze_attack_patterns(trajectories)
        
        rules = self._generate_rules(attack_patterns, reward_weights)
        
        strategy_id = f"strategy_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        strategy = DefenseStrategy(
            strategy_id=strategy_id,
            name=f"自适应策略_{datetime.now().strftime('%Y%m%d%H%M')}",
            rules=rules,
            risk_weights=reward_weights.weights,
            priority=1,
            created_at=datetime.now(),
        )
        
        with self._lock:
            self.strategies[strategy_id] = strategy
            self.strategy_history.append({
                "strategy_id": strategy_id,
                "created_at": datetime.now().isoformat(),
                "based_on_trajectories": len(trajectories),
            })
            self.stats["strategies_created"] += 1
        
        return strategy
    
    def _analyze_attack_patterns(
        self,
        trajectories: List[AttackTrajectory]
    ) -> Dict[str, Any]:
        patterns = {
            "common_features": defaultdict(float),
            "attack_sequences": [],
            "success_indicators": [],
        }
        
        for traj in trajectories:
            if traj.final_result == GameResult.ATTACKER_WIN:
                for state in traj.states:
                    for feature, value in state.features.items():
                        patterns["common_features"][feature] += value / len(traj.states)
                
                action_sequence = [a.action_type for a in traj.actions]
                patterns["attack_sequences"].append(action_sequence)
        
        return patterns
    
    def _generate_rules(
        self,
        attack_patterns: Dict[str, Any],
        reward_weights: RewardWeights
    ) -> List[Dict[str, Any]]:
        rules = []
        
        common_features = attack_patterns["common_features"]
        
        sorted_features = sorted(
            common_features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        for feature, avg_value in sorted_features:
            weight = reward_weights.get_weight(feature)
            
            if weight > 0.5:
                threshold = avg_value * 0.8
                rules.append({
                    "condition": f"{feature} > {threshold:.2f}",
                    "action": DefenseAction.ALERT.value,
                    "risk_weight": weight,
                })
            elif weight < -0.5:
                threshold = avg_value * 1.2
                rules.append({
                    "condition": f"{feature} < {threshold:.2f}",
                    "action": DefenseAction.BEHAVIOR_ANALYSIS.value,
                    "risk_weight": abs(weight),
                })
        
        return rules
    
    def select_strategy(
        self,
        state: StateVector,
        attack_type: AttackType = None
    ) -> Optional[DefenseStrategy]:
        risk_score = self.reward_inference.get_risk_score(state)
        
        candidates = []
        
        with self._lock:
            for strategy in self.strategies.values():
                match_score = self._calculate_match_score(strategy, state, attack_type)
                candidates.append((strategy, match_score, strategy.priority))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: (-x[1], x[2]))
        
        return candidates[0][0]
    
    def _calculate_match_score(
        self,
        strategy: DefenseStrategy,
        state: StateVector,
        attack_type: AttackType
    ) -> float:
        score = 0.0
        
        for feature, value in state.features.items():
            weight = strategy.risk_weights.get(feature, 0.0)
            score += abs(weight * value)
        
        return score / max(len(state.features), 1)
    
    def update_strategy_performance(
        self,
        strategy_id: str,
        success: bool
    ):
        with self._lock:
            if strategy_id not in self.strategies:
                return
            
            strategy = self.strategies[strategy_id]
            strategy.usage_count += 1
            
            if success:
                strategy.success_rate = (
                    strategy.success_rate * (strategy.usage_count - 1) + 1.0
                ) / strategy.usage_count
            else:
                strategy.success_rate = (
                    strategy.success_rate * (strategy.usage_count - 1)
                ) / strategy.usage_count
            
            self.stats["strategies_updated"] += 1
    
    def get_best_strategies(self, limit: int = 5) -> List[DefenseStrategy]:
        with self._lock:
            sorted_strategies = sorted(
                self.strategies.values(),
                key=lambda s: (s.success_rate, -s.priority),
                reverse=True
            )
            return sorted_strategies[:limit]


class IRLDefense:
    """逆强化学习防御系统主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.reward_inference = RewardFunctionInference(
            feature_dim=self.config.get("feature_dim", 20),
            learning_rate=self.config.get("learning_rate", 0.01)
        )
        self.strategy_optimizer = DefenseStrategyOptimizer(self.reward_inference)
        
        self.trajectory_buffer: deque = deque(maxlen=10000)
        self.active_games: Dict[str, Dict[str, Any]] = {}
        
        self._lock = threading.Lock()
        
        self._running = False
        self._training_task = None
        
        self.stats = {
            "total_games": 0,
            "attacker_wins": 0,
            "defender_wins": 0,
            "strategies_deployed": 0,
            "training_sessions": 0,
        }
    
    async def start(self):
        self._running = True
        self._training_task = asyncio.create_task(self._periodic_training())
    
    def stop(self):
        self._running = False
        if self._training_task:
            self._training_task.cancel()
    
    async def _periodic_training(self):
        while self._running:
            try:
                await self._run_training()
                await asyncio.sleep(86400)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Training error: {e}")
                await asyncio.sleep(3600)
    
    async def _run_training(self):
        self.stats["training_sessions"] += 1
        
        trajectories = list(self.trajectory_buffer)
        
        if len(trajectories) < 10:
            return
        
        self.reward_inference.infer_weights(epochs=100)
        
        self.strategy_optimizer.optimize_strategy(trajectories)
    
    def record_attack_trajectory(
        self,
        attack_type: AttackType,
        states: List[Dict[str, float]],
        actions: List[Dict[str, Any]],
        rewards: List[float],
        result: GameResult,
        attacker_id: str,
        defender_id: str
    ) -> AttackTrajectory:
        trajectory_id = f"traj_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        state_vectors = [
            StateVector(
                state_id=f"state_{i}_{uuid.uuid4().hex[:6]}",
                features=s,
                timestamp=datetime.now()
            )
            for i, s in enumerate(states)
        ]
        
        action_records = [
            ActionRecord(
                action_id=f"action_{i}_{uuid.uuid4().hex[:6]}",
                action_type=a.get("type", "unknown"),
                parameters=a.get("parameters", {}),
                timestamp=datetime.now(),
                success=a.get("success", False)
            )
            for i, a in enumerate(actions)
        ]
        
        success_rate = sum(1 for a in action_records if a.success) / max(len(action_records), 1)
        
        trajectory = AttackTrajectory(
            trajectory_id=trajectory_id,
            attack_type=attack_type,
            states=state_vectors,
            actions=action_records,
            rewards=rewards,
            final_result=result,
            attacker_id=attacker_id,
            defender_id=defender_id,
            start_time=datetime.now() - timedelta(seconds=len(states)),
            end_time=datetime.now(),
            total_steps=len(states),
            success_rate=success_rate,
        )
        
        with self._lock:
            self.trajectory_buffer.append(trajectory)
            self.reward_inference.add_trajectory(trajectory)
        
        self.stats["total_games"] += 1
        if result == GameResult.ATTACKER_WIN:
            self.stats["attacker_wins"] += 1
        elif result == GameResult.DEFENDER_WIN:
            self.stats["defender_wins"] += 1
        
        return trajectory
    
    def get_defense_action(
        self,
        current_state: Dict[str, float],
        attack_type: AttackType = None
    ) -> Tuple[DefenseAction, DefenseStrategy, float]:
        state_vector = StateVector(
            state_id=f"current_{uuid.uuid4().hex[:8]}",
            features=current_state,
            timestamp=datetime.now()
        )
        
        strategy = self.strategy_optimizer.select_strategy(state_vector, attack_type)
        
        if not strategy:
            return DefenseAction.ALERT, None, 0.5
        
        risk_score = self.reward_inference.get_risk_score(state_vector)
        
        action = self._select_action(strategy, current_state, risk_score)
        
        return action, strategy, risk_score
    
    def _select_action(
        self,
        strategy: DefenseStrategy,
        state: Dict[str, float],
        risk_score: float
    ) -> DefenseAction:
        for rule in strategy.rules:
            condition = rule.get("condition", "")
            action_str = rule.get("action", "alert")
            
            if self._evaluate_condition(condition, state):
                try:
                    return DefenseAction(action_str)
                except ValueError:
                    return DefenseAction.ALERT
        
        if risk_score > 0.8:
            return DefenseAction.BLOCK_IP
        elif risk_score > 0.6:
            return DefenseAction.RATE_LIMIT
        elif risk_score > 0.4:
            return DefenseAction.ALERT
        else:
            return DefenseAction.LOG_ANALYSIS
    
    def _evaluate_condition(self, condition: str, state: Dict[str, float]) -> bool:
        try:
            for feature, value in state.items():
                condition = condition.replace(feature, str(value))
            
            return eval(condition)
        except Exception:
            return False
    
    def report_defense_result(
        self,
        strategy_id: str,
        success: bool
    ):
        self.strategy_optimizer.update_strategy_performance(strategy_id, success)
    
    def get_risk_perception(self, state: Dict[str, float]) -> Dict[str, Any]:
        state_vector = StateVector(
            state_id=f"risk_check_{uuid.uuid4().hex[:8]}",
            features=state,
            timestamp=datetime.now()
        )
        
        risk_score = self.reward_inference.get_risk_score(state_vector)
        state_reward = self.reward_inference.compute_state_reward(state_vector)
        
        top_risk_features = []
        for feature, value in state.items():
            weight = self.reward_inference.reward_weights.get_weight(feature)
            contribution = weight * value
            top_risk_features.append((feature, weight, contribution))
        
        top_risk_features.sort(key=lambda x: abs(x[2]), reverse=True)
        
        return {
            "risk_score": risk_score,
            "state_reward": state_reward,
            "top_risk_features": top_risk_features[:5],
            "confidence": self.reward_inference.reward_weights.confidence,
        }
    
    def get_strategies(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self.strategy_optimizer.get_best_strategies()]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "defense_system": self.stats,
            "reward_inference": {
                "trajectories_count": len(self.reward_inference.trajectories),
                "confidence": self.reward_inference.reward_weights.confidence,
                **self.reward_inference.stats,
            },
            "strategy_optimizer": {
                "total_strategies": len(self.strategy_optimizer.strategies),
                **self.strategy_optimizer.stats,
            },
        }
