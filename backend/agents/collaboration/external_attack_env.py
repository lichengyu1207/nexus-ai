"""
外部攻击环境模块
External Attack Environment Module

模拟真实外部攻击，用于训练智能体的协作能力
"""

import os
import json
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class AttackType(Enum):
    DDoS = "ddos"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    SLOW_LORIS = "slow_loris"
    DNS_AMPLIFICATION = "dns_amplification"
    SYN_FLOOD = "syn_flood"
    MIXED = "mixed"


@dataclass
class AttackPattern:
    attack_type: AttackType
    intensity: float
    duration_steps: int
    pattern_params: Dict[str, float]
    stealth_level: float = 0.0


@dataclass
class ExternalAttackState:
    time_step: int = 0
    request_rate: float = 0.0
    error_rate: float = 0.0
    unique_ips: float = 0.0
    avg_packet_size: float = 0.0
    connection_count: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time: float = 0.0
    blocked_rate: float = 0.0
    attack_active: bool = False
    attack_type: int = 0
    attack_intensity: float = 0.0
    
    def to_array(self) -> np.ndarray:
        return np.array([
            self.request_rate,
            self.error_rate,
            self.unique_ips,
            self.avg_packet_size,
            self.connection_count,
            self.cpu_usage,
            self.memory_usage,
            self.response_time,
            self.blocked_rate,
            float(self.attack_active),
            float(self.attack_type),
            self.attack_intensity,
            self.time_step / 1000.0
        ], dtype=np.float32)
    
    def is_service_down(self) -> bool:
        return self.cpu_usage > 0.95 or self.memory_usage > 0.95 or self.response_time > 5.0


class ExternalAttackGenerator:
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.attack_patterns = self._define_attack_patterns()
        self.current_attack: Optional[AttackPattern] = None
        self.attack_step = 0
    
    def _define_attack_patterns(self) -> Dict[AttackType, Dict]:
        return {
            AttackType.DDoS: {
                "request_rate_multiplier": 10.0,
                "unique_ips_range": (0.7, 1.0),
                "connection_multiplier": 5.0,
                "cpu_impact": 0.8,
                "memory_impact": 0.3
            },
            AttackType.SQL_INJECTION: {
                "error_rate_range": (0.3, 0.7),
                "request_rate_multiplier": 1.5,
                "cpu_impact": 0.4,
                "memory_impact": 0.2
            },
            AttackType.SLOW_LORIS: {
                "connection_multiplier": 3.0,
                "request_rate_range": (0.1, 0.3),
                "cpu_impact": 0.2,
                "memory_impact": 0.6
            },
            AttackType.SYN_FLOOD: {
                "connection_multiplier": 8.0,
                "request_rate_range": (0.5, 0.8),
                "cpu_impact": 0.7,
                "memory_impact": 0.4
            },
            AttackType.DNS_AMPLIFICATION: {
                "request_rate_multiplier": 5.0,
                "avg_packet_size_multiplier": 3.0,
                "cpu_impact": 0.5,
                "memory_impact": 0.3
            },
            AttackType.BRUTE_FORCE: {
                "error_rate_range": (0.5, 0.9),
                "request_rate_range": (0.3, 0.6),
                "cpu_impact": 0.3,
                "memory_impact": 0.2
            },
            AttackType.MIXED: {
                "request_rate_multiplier": 3.0,
                "error_rate_range": (0.2, 0.5),
                "connection_multiplier": 2.0,
                "cpu_impact": 0.6,
                "memory_impact": 0.5
            }
        }
    
    def generate_attack(self, intensity: float = 0.5) -> AttackPattern:
        attack_type = random.choice(list(AttackType))
        
        if attack_type == AttackType.MIXED:
            attack_type = AttackType.MIXED
        
        duration = random.randint(50, 200)
        stealth_level = random.uniform(0, intensity * 0.5)
        
        pattern_params = self.attack_patterns.get(attack_type, {})
        
        return AttackPattern(
            attack_type=attack_type,
            intensity=intensity,
            duration_steps=duration,
            pattern_params=pattern_params,
            stealth_level=stealth_level
        )
    
    def apply_attack(self, state: ExternalAttackState, attack: AttackPattern) -> ExternalAttackState:
        params = attack.pattern_params
        intensity = attack.intensity
        stealth = attack.stealth_level
        
        effective_intensity = intensity * (1 - stealth * 0.5)
        
        if "request_rate_multiplier" in params:
            state.request_rate = min(1.0, state.request_rate * params["request_rate_multiplier"] * effective_intensity)
        
        if "request_rate_range" in params:
            r = params["request_rate_range"]
            state.request_rate = np.clip(state.request_rate + random.uniform(*r) * effective_intensity, 0, 1)
        
        if "error_rate_range" in params:
            r = params["error_rate_range"]
            state.error_rate = np.clip(random.uniform(*r) * effective_intensity, 0, 1)
        
        if "unique_ips_range" in params:
            r = params["unique_ips_range"]
            state.unique_ips = random.uniform(*r)
        
        if "connection_multiplier" in params:
            state.connection_count = min(1.0, state.connection_count * params["connection_multiplier"] * effective_intensity)
        
        if "avg_packet_size_multiplier" in params:
            state.avg_packet_size = min(1.0, state.avg_packet_size * params["avg_packet_size_multiplier"])
        
        if "cpu_impact" in params:
            state.cpu_usage = min(1.0, state.cpu_usage + params["cpu_impact"] * effective_intensity)
        
        if "memory_impact" in params:
            state.memory_usage = min(1.0, state.memory_usage + params["memory_impact"] * effective_intensity)
        
        state.attack_active = True
        state.attack_type = list(AttackType).index(attack.attack_type)
        state.attack_intensity = intensity
        
        return state


class ExternalAttackEnv:
    
    def __init__(
        self,
        max_steps: int = 1000,
        attack_probability: float = 0.3,
        seed: Optional[int] = None
    ):
        self.max_steps = max_steps
        self.attack_probability = attack_probability
        
        self.attack_generator = ExternalAttackGenerator(seed)
        self.state = ExternalAttackState()
        
        self.attack_history: List[Dict] = []
        self.defense_history: List[Dict] = []
        
        self._reset_state()
    
    def _reset_state(self):
        self.state = ExternalAttackState(
            request_rate=random.uniform(0.1, 0.3),
            error_rate=random.uniform(0.01, 0.05),
            unique_ips=random.uniform(0.3, 0.6),
            avg_packet_size=random.uniform(0.2, 0.4),
            connection_count=random.uniform(0.1, 0.3),
            cpu_usage=random.uniform(0.2, 0.4),
            memory_usage=random.uniform(0.3, 0.5),
            response_time=random.uniform(0.05, 0.2),
            blocked_rate=0.0,
            attack_active=False,
            attack_type=0,
            attack_intensity=0.0
        )
    
    def reset(self) -> Tuple[np.ndarray, Dict]:
        self._reset_state()
        self.attack_generator.current_attack = None
        self.attack_generator.attack_step = 0
        
        return self.state.to_array(), {"initial_state": True}
    
    def step(
        self,
        attack_action: int,
        attack_intensity: float,
        defense_action: int
    ) -> Tuple[Tuple[np.ndarray, np.ndarray], Dict[str, float], bool, Dict]:
        self.state.time_step += 1
        
        if self.attack_generator.current_attack is None:
            if random.random() < self.attack_probability:
                self.attack_generator.current_attack = self.attack_generator.generate_attack(
                    intensity=random.uniform(0.3, 1.0)
                )
                self.attack_generator.attack_step = 0
        
        if self.attack_generator.current_attack:
            self.state = self.attack_generator.apply_attack(
                self.state,
                self.attack_generator.current_attack
            )
            self.attack_generator.attack_step += 1
            
            if self.attack_generator.attack_step >= self.attack_generator.current_attack.duration_steps:
                self.attack_generator.current_attack = None
                self.attack_generator.attack_step = 0
        else:
            self._normal_traffic()
        
        defense_effect = self._apply_defense(defense_action)
        
        rewards = self._compute_rewards(attack_action, defense_action, defense_effect)
        
        done = self.state.time_step >= self.max_steps or self.state.is_service_down()
        
        info = {
            "attack_active": self.state.attack_active,
            "attack_type": self.state.attack_type,
            "defense_effect": defense_effect,
            "service_down": self.state.is_service_down()
        }
        
        if self.state.attack_active:
            self.attack_history.append({
                "step": self.state.time_step,
                "attack_type": self.state.attack_type,
                "intensity": self.state.attack_intensity,
                "defense_action": defense_action,
                "blocked": defense_effect["blocked"]
            })
        
        attacker_state = self._get_attacker_state()
        defender_state = self._get_defender_state()
        
        return (attacker_state, defender_state), rewards, done, info
    
    def _normal_traffic(self):
        self.state.request_rate = np.clip(
            self.state.request_rate + random.gauss(0, 0.05),
            0.1, 0.4
        )
        self.state.error_rate = np.clip(
            self.state.error_rate + random.gauss(0, 0.01),
            0.01, 0.1
        )
        self.state.unique_ips = np.clip(
            self.state.unique_ips + random.gauss(0, 0.05),
            0.3, 0.7
        )
        self.state.cpu_usage = np.clip(
            self.state.cpu_usage - 0.05 + random.gauss(0, 0.02),
            0.1, 0.5
        )
        self.state.memory_usage = np.clip(
            self.state.memory_usage - 0.03 + random.gauss(0, 0.02),
            0.2, 0.6
        )
        self.state.attack_active = False
        self.state.attack_type = 0
        self.state.attack_intensity = 0.0
    
    def _apply_defense(self, defense_action: int) -> Dict:
        defense_effect = {
            "blocked": False,
            "false_positive": False,
            "mitigation": 0.0
        }
        
        if self.state.attack_active:
            correct_actions = self._get_correct_defense_actions(self.state.attack_type)
            
            if defense_action in correct_actions:
                defense_effect["blocked"] = True
                defense_effect["mitigation"] = 0.8
                
                self.state.cpu_usage = max(0.1, self.state.cpu_usage - 0.2)
                self.state.memory_usage = max(0.1, self.state.memory_usage - 0.1)
                self.state.response_time = max(0.05, self.state.response_time - 0.1)
                self.state.blocked_rate += 0.1
            else:
                defense_effect["mitigation"] = 0.2
        else:
            if defense_action != 0:
                defense_effect["false_positive"] = True
                self.state.response_time += 0.05
        
        return defense_effect
    
    def _get_correct_defense_actions(self, attack_type: int) -> List[int]:
        defense_mapping = {
            1: [1, 4],
            2: [2, 5],
            3: [3, 6],
            4: [1, 2],
            5: [2, 3],
            6: [4, 5],
            7: [1, 3, 5],
            8: [1, 4, 6]
        }
        return defense_mapping.get(attack_type, [0])
    
    def _get_attacker_state(self) -> np.ndarray:
        return self.state.to_array()
    
    def _get_defender_state(self) -> np.ndarray:
        return self.state.to_array()
    
    def _compute_rewards(
        self,
        attack_action: int,
        defense_action: int,
        defense_effect: Dict
    ) -> Dict[str, float]:
        attacker_reward = 0.0
        defender_reward = 0.0
        
        if self.state.attack_active:
            if defense_effect["blocked"]:
                attacker_reward = -1.0
                defender_reward = 1.0
            else:
                attacker_reward = self.state.attack_intensity
                defender_reward = -self.state.attack_intensity * 2
            
            if self.state.is_service_down():
                attacker_reward += 5.0
                defender_reward -= 10.0
        else:
            if defense_effect["false_positive"]:
                attacker_reward = 0.0
                defender_reward = -0.5
            else:
                attacker_reward = 0.0
                defender_reward = 0.1
        
        return {
            "attacker": attacker_reward,
            "defender": defender_reward
        }
    
    def get_attack_stats(self) -> Dict:
        if not self.attack_history:
            return {"total_attacks": 0}
        
        blocked = sum(1 for a in self.attack_history if a["blocked"])
        total = len(self.attack_history)
        
        return {
            "total_attacks": total,
            "blocked_attacks": blocked,
            "missed_attacks": total - blocked,
            "block_rate": blocked / total if total > 0 else 0
        }


class CollaborationRewardCalculator:
    
    def __init__(
        self,
        defense_success_bonus: float = 1.0,
        advice_quality_weight: float = 0.3,
        contribution_decay: float = 0.95
    ):
        self.defense_success_bonus = defense_success_bonus
        self.advice_quality_weight = advice_quality_weight
        self.contribution_decay = contribution_decay
    
    def calculate_collaboration_reward(
        self,
        defense_success: bool,
        advices: List[Dict],
        final_action: int,
        correct_actions: List[int]
    ) -> Dict[str, float]:
        rewards = {}
        
        base_reward = self.defense_success_bonus if defense_success else -0.5
        
        for advice in advices:
            agent_id = advice["agent_id"]
            advised_action = advice["top_advices"][0]["action"] if advice["top_advices"] else 0
            confidence = advice["top_advices"][0]["confidence"] if advice["top_advices"] else 0
            
            if advised_action in correct_actions:
                quality_bonus = confidence * self.advice_quality_weight
                rewards[agent_id] = base_reward + quality_bonus
            else:
                rewards[agent_id] = -0.2 * confidence
        
        return rewards
    
    def update_contribution_scores(
        self,
        agents: List,
        rewards: Dict[str, float]
    ):
        for agent in agents:
            agent_id = agent.agent_id
            if agent_id in rewards:
                current = agent.stats.get("contribution_score", 1.0)
                new_score = current * self.contribution_decay + rewards[agent_id] * (1 - self.contribution_decay)
                agent.stats["contribution_score"] = max(0.1, min(2.0, new_score))
