"""
攻击防御智能体集群
实现攻防对抗、协同进化能力

基于全链路.md提示词30-35
"""

import os
import json
import time
import uuid
import random
import logging
import threading
import hashlib
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class AttackType(Enum):
    DDOS = "ddos"
    CC = "cc"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PROMPT_INJECTION = "prompt_injection"
    MIXED = "mixed"
    LOW_SLOW = "low_slow"
    PHISHING = "phishing"
    BRUTE_FORCE = "brute_force"


class DefenseAction(Enum):
    ALLOW = "allow"
    RATE_LIMIT = "rate_limit"
    CAPTCHA = "captcha"
    BLOCK = "block"
    TRAFFIC_CLEAN = "traffic_clean"
    SWITCH_HIGH_DEFENSE = "switch_high_defense"
    CHALLENGE = "challenge"
    LOG_AND_MONITOR = "log_and_monitor"


class AttackIntensity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BattleResult(Enum):
    ATTACKER_WIN = "attacker_win"
    DEFENDER_WIN = "defender_win"
    DRAW = "draw"
    ONGOING = "ongoing"


@dataclass
class AttackPattern:
    attack_type: AttackType
    intensity: AttackIntensity
    target: str
    duration: float
    params: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    
    def __post_init__(self):
        if not self.signature:
            self.signature = self._generate_signature()
    
    def _generate_signature(self) -> str:
        content = f"{self.attack_type.value}:{json.dumps(self.params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_type": self.attack_type.value,
            "intensity": self.intensity.value,
            "target": self.target,
            "duration": self.duration,
            "params": self.params,
            "signature": self.signature
        }


@dataclass
class DefenseStrategy:
    action: DefenseAction
    confidence: float
    target_attack_type: AttackType
    params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "target_attack_type": self.target_attack_type.value,
            "params": self.params,
            "reasoning": self.reasoning
        }


@dataclass
class BattleRecord:
    battle_id: str
    attacker_id: str
    defender_id: str
    attack_type: AttackType
    defense_action: DefenseAction
    attack_intensity: AttackIntensity
    result: BattleResult
    attacker_reward: float
    defender_reward: float
    timestamp: float
    duration: float
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "battle_id": self.battle_id,
            "attacker_id": self.attacker_id,
            "defender_id": self.defender_id,
            "attack_type": self.attack_type.value,
            "defense_action": self.defense_action.value,
            "attack_intensity": self.attack_intensity.value,
            "result": self.result.value,
            "attacker_reward": self.attacker_reward,
            "defender_reward": self.defender_reward,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "details": self.details
        }


class StrategyNetwork:
    def __init__(self, input_dim: int = 64, hidden_dim: int = 128, output_dim: int = 10):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.weights: Dict[str, List[float]] = {
            "w1": self._init_weights(input_dim, hidden_dim),
            "b1": [0.0] * hidden_dim,
            "w2": self._init_weights(hidden_dim, output_dim),
            "b2": [0.0] * output_dim
        }
        self.learning_rate = 0.01
    
    def _init_weights(self, rows: int, cols: int) -> List[float]:
        scale = math.sqrt(2.0 / (rows + cols))
        return [random.gauss(0, scale) for _ in range(rows * cols)]
    
    def forward(self, x: List[float]) -> List[float]:
        h = self._matmul(x, self.weights["w1"], self.input_dim, self.hidden_dim)
        h = [max(0, h[i] + self.weights["b1"][i]) for i in range(self.hidden_dim)]
        out = self._matmul(h, self.weights["w2"], self.hidden_dim, self.output_dim)
        out = [out[i] + self.weights["b2"][i] for i in range(self.output_dim)]
        return self._softmax(out)
    
    def _matmul(self, a: List[float], b: List[float], rows: int, cols: int) -> List[float]:
        result = [0.0] * cols
        for i in range(cols):
            for j in range(rows):
                result[i] += a[j] * b[j * cols + i]
        return result
    
    def _softmax(self, x: List[float]) -> List[float]:
        max_x = max(x)
        exp_x = [math.exp(xi - max_x) for xi in x]
        sum_exp = sum(exp_x)
        return [e / sum_exp for e in exp_x]
    
    def mutate(self, mutation_rate: float = 0.1):
        for key in ["w1", "w2"]:
            weights = self.weights[key]
            for i in range(len(weights)):
                if random.random() < mutation_rate:
                    weights[i] += random.gauss(0, 0.1)
    
    def crossover(self, other: "StrategyNetwork") -> "StrategyNetwork":
        child = StrategyNetwork(self.input_dim, self.hidden_dim, self.output_dim)
        for key in ["w1", "w2"]:
            self_weights = self.weights[key]
            other_weights = other.weights[key]
            child_weights = []
            for i in range(len(self_weights)):
                child_weights.append(random.choice([self_weights[i], other_weights[i]]))
            child.weights[key] = child_weights
        return child
    
    def get_params(self) -> Dict[str, Any]:
        return {
            "weights": {k: v[:10] for k, v in self.weights.items()},
            "dims": {"input": self.input_dim, "hidden": self.hidden_dim, "output": self.output_dim}
        }


class LivingAgentBase(ABC):
    def __init__(self, agent_id: str, species: str):
        self.agent_id = agent_id
        self.species = species
        self.energy = 100.0
        self.age = 0
        self.max_age = 1000
        self.gene_pool: Dict[str, Any] = {}
        self.experience_buffer: deque = deque(maxlen=1000)
        self.is_alive = True
        self._energy_lock = threading.Lock()
        self.created_at = time.time()
        self.generation = 1
        self.parent_id: Optional[str] = None
    
    def metabolize(self, environment: Optional[Dict[str, Any]] = None) -> float:
        with self._energy_lock:
            consumption = 0.1
            if environment:
                temp = environment.get("temperature", 1.0)
                consumption *= temp
            self.energy -= consumption
            self.age += 1
            if self.energy <= 0:
                self.is_alive = False
                self.energy = 0
            elif self.age >= self.max_age:
                self.is_alive = False
            return consumption
    
    def add_energy(self, amount: float) -> float:
        with self._energy_lock:
            self.energy = min(self.energy + amount, 500.0)
            return self.energy
    
    def consume_energy(self, amount: float) -> bool:
        with self._energy_lock:
            if self.energy >= amount:
                self.energy -= amount
                return True
            return False
    
    def can_reproduce(self) -> bool:
        return self.energy >= 150.0 and self.age >= 10 and self.is_alive
    
    def reproduce(self) -> Optional["LivingAgentBase"]:
        if not self.can_reproduce():
            return None
        child_id = f"{self.species}_{uuid.uuid4().hex[:8]}"
        child = self._create_child(child_id)
        if child:
            child.generation = self.generation + 1
            child.parent_id = self.agent_id
            child.energy = self.energy * 0.4
            self.energy *= 0.6
            child.gene_pool = self._mutate_genes()
        return child
    
    @abstractmethod
    def _create_child(self, child_id: str) -> "LivingAgentBase":
        pass
    
    def _mutate_genes(self) -> Dict[str, Any]:
        new_genes = {}
        for key, value in self.gene_pool.items():
            if isinstance(value, (int, float)):
                mutation = random.gauss(0, 0.1) * value
                new_genes[key] = value + mutation
            elif isinstance(value, dict):
                new_genes[key] = value.copy()
            else:
                new_genes[key] = value
        return new_genes
    
    def mutate(self, mutation_rate: float = 0.1):
        for key in self.gene_pool:
            if random.random() < mutation_rate:
                if isinstance(self.gene_pool[key], (int, float)):
                    self.gene_pool[key] *= (1 + random.gauss(0, 0.2))
    
    def record_experience(self, experience: Dict[str, Any]):
        self.experience_buffer.append({
            **experience,
            "timestamp": time.time(),
            "energy": self.energy,
            "age": self.age
        })
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "species": self.species,
            "energy": self.energy,
            "age": self.age,
            "is_alive": self.is_alive,
            "generation": self.generation,
            "parent_id": self.parent_id,
            "experience_count": len(self.experience_buffer)
        }


class AttackAgent(LivingAgentBase):
    def __init__(self, agent_id: str, strategy_network: Optional[StrategyNetwork] = None):
        super().__init__(agent_id, "attacker")
        self.strategy_network = strategy_network or StrategyNetwork(
            input_dim=64, hidden_dim=128, output_dim=len(AttackType)
        )
        self.gene_pool = {
            "aggression": random.uniform(0.3, 0.9),
            "stealth": random.uniform(0.3, 0.9),
            "adaptation_rate": random.uniform(0.01, 0.1),
            "entropy_bonus": random.uniform(0.01, 0.1)
        }
        self.attack_history: List[AttackPattern] = []
        self.success_rate = 0.5
        self.total_attacks = 0
        self.successful_attacks = 0
    
    def _create_child(self, child_id: str) -> "AttackAgent":
        child_network = StrategyNetwork(
            self.strategy_network.input_dim,
            self.strategy_network.hidden_dim,
            self.strategy_network.output_dim
        )
        child_network.weights = {
            k: v.copy() if isinstance(v, list) else v 
            for k, v in self.strategy_network.weights.items()
        }
        child_network.mutate(mutation_rate=0.1)
        child = AttackAgent(child_id, child_network)
        child.gene_pool = self._mutate_genes()
        return child
    
    def plan_attack(self, target: str, environment: Dict[str, Any]) -> AttackPattern:
        state = self._encode_environment(environment)
        probs = self.strategy_network.forward(state)
        attack_idx = self._sample_action(probs)
        attack_type = list(AttackType)[attack_idx]
        intensity = self._select_intensity(environment)
        duration = random.uniform(1.0, 60.0)
        params = self._generate_attack_params(attack_type, target)
        pattern = AttackPattern(
            attack_type=attack_type,
            intensity=intensity,
            target=target,
            duration=duration,
            params=params
        )
        self.attack_history.append(pattern)
        self.consume_energy(5.0)
        return pattern
    
    def _encode_environment(self, environment: Dict[str, Any]) -> List[float]:
        state = [0.0] * 64
        state[0] = self.energy / 100.0
        state[1] = self.age / self.max_age
        state[2] = self.gene_pool.get("aggression", 0.5)
        state[3] = self.gene_pool.get("stealth", 0.5)
        state[4] = environment.get("defense_level", 0.5)
        state[5] = environment.get("target_value", 0.5)
        state[6] = self.success_rate
        state[7] = len(self.attack_history) / 100.0
        for i in range(8, 64):
            state[i] = random.gauss(0, 0.1)
        return state
    
    def _sample_action(self, probs: List[float]) -> int:
        entropy_bonus = self.gene_pool.get("entropy_bonus", 0.05)
        if random.random() < entropy_bonus:
            return random.randint(0, len(probs) - 1)
        r = random.random()
        cumsum = 0.0
        for i, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return i
        return len(probs) - 1
    
    def _select_intensity(self, environment: Dict[str, Any]) -> AttackIntensity:
        defense_level = environment.get("defense_level", 0.5)
        aggression = self.gene_pool.get("aggression", 0.5)
        score = aggression * (1 - defense_level) + random.gauss(0, 0.1)
        if score > 0.7:
            return AttackIntensity.CRITICAL
        elif score > 0.5:
            return AttackIntensity.HIGH
        elif score > 0.3:
            return AttackIntensity.MEDIUM
        return AttackIntensity.LOW
    
    def _generate_attack_params(self, attack_type: AttackType, target: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if attack_type == AttackType.DDOS:
            params = {
                "packet_rate": random.randint(10000, 1000000),
                "source_ips": random.randint(100, 10000),
                "protocol": random.choice(["TCP", "UDP", "ICMP", "HTTP"])
            }
        elif attack_type == AttackType.SQL_INJECTION:
            params = {
                "injection_type": random.choice(["union", "blind", "error", "time"]),
                "payload_template": random.choice([
                    "' OR 1=1--",
                    "UNION SELECT * FROM users--",
                    "'; DROP TABLE users;--"
                ])
            }
        elif attack_type == AttackType.XSS:
            params = {
                "injection_type": random.choice(["reflected", "stored", "dom"]),
                "payload_template": random.choice([
                    "<script>alert('XSS')</script>",
                    "<img src=x onerror=alert('XSS')>",
                    "javascript:alert('XSS')"
                ])
            }
        elif attack_type == AttackType.PROMPT_INJECTION:
            params = {
                "injection_type": random.choice(["jailbreak", "role_play", "ignore_instructions"]),
                "payload_template": random.choice([
                    "Ignore all previous instructions",
                    "DAN (Do Anything Now)",
                    "You are now in developer mode"
                ])
            }
        elif attack_type == AttackType.LOW_SLOW:
            params = {
                "connection_count": random.randint(10, 100),
                "interval": random.uniform(1.0, 10.0),
                "method": random.choice(["slowloris", "slowpost", "slowread"])
            }
        elif attack_type == AttackType.CC:
            params = {
                "request_rate": random.randint(100, 10000),
                "target_page": random.choice(["/", "/api", "/login", "/search"]),
                "method": random.choice(["GET", "POST"])
            }
        elif attack_type == AttackType.PHISHING:
            params = {
                "technique": random.choice(["credential_harvest", "malware_delivery", "social_engineering"]),
                "channel": random.choice(["email", "sms", "web"])
            }
        elif attack_type == AttackType.BRUTE_FORCE:
            params = {
                "target_service": random.choice(["ssh", "ftp", "web_login", "api"]),
                "method": random.choice(["dictionary", "rainbow_table", "hybrid"])
            }
        elif attack_type == AttackType.MIXED:
            params = {
                "primary_attack": random.choice(["ddos", "sql_injection", "xss"]),
                "secondary_attack": random.choice(["phishing", "brute_force", "cc"]),
                "timing": random.choice(["simultaneous", "sequential", "staggered"])
            }
        params["target"] = target
        return params
    
    def receive_reward(self, reward: float, battle_result: BattleResult):
        self.add_energy(reward)
        self.total_attacks += 1
        if battle_result == BattleResult.ATTACKER_WIN:
            self.successful_attacks += 1
        self.success_rate = self.successful_attacks / max(1, self.total_attacks)
        self.record_experience({
            "type": "battle_result",
            "reward": reward,
            "result": battle_result.value,
            "success_rate": self.success_rate
        })
    
    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "success_rate": self.success_rate,
            "total_attacks": self.total_attacks,
            "successful_attacks": self.successful_attacks,
            "gene_pool": self.gene_pool
        })
        return status


class DefenseAgent(LivingAgentBase):
    def __init__(self, agent_id: str, strategy_network: Optional[StrategyNetwork] = None):
        super().__init__(agent_id, "defender")
        self.strategy_network = strategy_network or StrategyNetwork(
            input_dim=64, hidden_dim=128, output_dim=len(DefenseAction)
        )
        self.gene_pool = {
            "sensitivity": random.uniform(0.5, 0.9),
            "false_positive_tolerance": random.uniform(0.01, 0.1),
            "coordination_weight": random.uniform(0.3, 0.8),
            "learning_rate": random.uniform(0.01, 0.1)
        }
        self.defense_history: List[DefenseStrategy] = []
        self.true_positive_rate = 0.9
        self.false_positive_rate = 0.05
        self.total_defenses = 0
        self.successful_defenses = 0
        self.known_attack_patterns: Dict[str, float] = {}
    
    def _create_child(self, child_id: str) -> "DefenseAgent":
        child_network = StrategyNetwork(
            self.strategy_network.input_dim,
            self.strategy_network.hidden_dim,
            self.strategy_network.output_dim
        )
        child_network.weights = {
            k: v.copy() if isinstance(v, list) else v 
            for k, v in self.strategy_network.weights.items()
        }
        child_network.mutate(mutation_rate=0.1)
        child = DefenseAgent(child_id, child_network)
        child.gene_pool = self._mutate_genes()
        return child
    
    def analyze_attack(self, attack_pattern: AttackPattern, context: Dict[str, Any]) -> DefenseStrategy:
        state = self._encode_attack_state(attack_pattern, context)
        probs = self.strategy_network.forward(state)
        action_idx = self._select_defense_action(probs, attack_pattern)
        action = list(DefenseAction)[action_idx]
        confidence = probs[action_idx]
        strategy = DefenseStrategy(
            action=action,
            confidence=confidence,
            target_attack_type=attack_pattern.attack_type,
            params=self._generate_defense_params(action, attack_pattern),
            reasoning=self._generate_reasoning(action, attack_pattern)
        )
        self.defense_history.append(strategy)
        self.consume_energy(3.0)
        return strategy
    
    def _encode_attack_state(self, attack: AttackPattern, context: Dict[str, Any]) -> List[float]:
        state = [0.0] * 64
        state[0] = self.energy / 100.0
        state[1] = self.age / self.max_age
        state[2] = self.gene_pool.get("sensitivity", 0.5)
        state[3] = self.true_positive_rate
        state[4] = self.false_positive_rate
        attack_types = list(AttackType)
        if attack.attack_type in attack_types:
            state[5 + attack_types.index(attack.attack_type)] = 1.0
        intensities = list(AttackIntensity)
        if attack.intensity in intensities:
            state[15 + intensities.index(attack.intensity)] = 1.0
        state[20] = attack.duration / 60.0
        state[21] = context.get("threat_level", 0.5)
        state[22] = len(self.known_attack_patterns) / 100.0
        for i in range(23, 64):
            state[i] = random.gauss(0, 0.1)
        return state
    
    def _select_defense_action(self, probs: List[float], attack: AttackPattern) -> int:
        signature = attack.signature
        if signature in self.known_attack_patterns:
            weight = self.known_attack_patterns[signature]
            adjusted_probs = [p * (1 + weight * 0.5) for p in probs]
            total = sum(adjusted_probs)
            probs = [p / total for p in adjusted_probs]
        r = random.random()
        cumsum = 0.0
        for i, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return i
        return len(probs) - 1
    
    def _generate_defense_params(self, action: DefenseAction, attack: AttackPattern) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if action == DefenseAction.RATE_LIMIT:
            params = {
                "requests_per_second": random.randint(10, 100),
                "burst_size": random.randint(5, 20),
                "duration": random.randint(60, 3600)
            }
        elif action == DefenseAction.BLOCK:
            params = {
                "block_type": random.choice(["ip", "subnet", "asn"]),
                "duration": random.randint(300, 86400),
                "reason": f"Detected {attack.attack_type.value} attack"
            }
        elif action == DefenseAction.CAPTCHA:
            params = {
                "type": random.choice(["recaptcha", "hcaptcha", "image"]),
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "trigger_threshold": random.randint(3, 10)
            }
        elif action == DefenseAction.TRAFFIC_CLEAN:
            params = {
                "provider": random.choice(["cloudflare", "akamai", "aws_shield"]),
                "mode": random.choice(["standard", "aggressive"]),
                "duration": random.randint(300, 7200)
            }
        elif action == DefenseAction.SWITCH_HIGH_DEFENSE:
            params = {
                "target_node": random.choice(["hk", "us", "eu"]),
                "bandwidth": random.choice(["10g", "100g", "1t"])
            }
        elif action == DefenseAction.CHALLENGE:
            params = {
                "challenge_type": random.choice(["js_challenge", "cookie_challenge", "dns_challenge"]),
                "timeout": random.randint(5, 30)
            }
        return params
    
    def _generate_reasoning(self, action: DefenseAction, attack: AttackPattern) -> str:
        reasons = {
            DefenseAction.ALLOW: f"Attack {attack.attack_type.value} deemed low risk, allowing with monitoring",
            DefenseAction.RATE_LIMIT: f"Rate limiting to mitigate {attack.attack_type.value} with {attack.intensity.value} intensity",
            DefenseAction.CAPTCHA: f"Challenging requests to verify human traffic against {attack.attack_type.value}",
            DefenseAction.BLOCK: f"Blocking source due to confirmed {attack.attack_type.value} attack",
            DefenseAction.TRAFFIC_CLEAN: f"Activating traffic cleaning for {attack.intensity.value} intensity {attack.attack_type.value}",
            DefenseAction.SWITCH_HIGH_DEFENSE: f"Switching to high defense node for {attack.attack_type.value} attack",
            DefenseAction.CHALLENGE: f"Issuing challenge to verify legitimate traffic",
            DefenseAction.LOG_AND_MONITOR: f"Logging and monitoring {attack.attack_type.value} for pattern analysis"
        }
        return reasons.get(action, f"Executing {action.value} defense")
    
    def coordinate(self, other_defenders: List["DefenseAgent"], attack: AttackPattern) -> DefenseStrategy:
        if not other_defenders:
            return self.analyze_attack(attack, {})
        all_strategies = [self.analyze_attack(attack, {})]
        for defender in other_defenders:
            if defender.is_alive and defender.energy > 10:
                all_strategies.append(defender.analyze_attack(attack, {}))
        best_strategy = max(all_strategies, key=lambda s: s.confidence)
        coordination_weight = self.gene_pool.get("coordination_weight", 0.5)
        if coordination_weight > 0.5:
            action_counts: Dict[DefenseAction, int] = {}
            for strategy in all_strategies:
                action_counts[strategy.action] = action_counts.get(strategy.action, 0) + 1
            most_common = max(action_counts.items(), key=lambda x: x[1])
            if most_common[1] > len(all_strategies) / 2:
                best_strategy.action = most_common[0]
        return best_strategy
    
    def learn_from_attack(self, attack: AttackPattern, was_successful: bool):
        signature = attack.signature
        if was_successful:
            self.known_attack_patterns[signature] = self.known_attack_patterns.get(signature, 0) + 0.1
        else:
            self.known_attack_patterns[signature] = self.known_attack_patterns.get(signature, 0) - 0.05
        self.known_attack_patterns[signature] = max(-1.0, min(1.0, self.known_attack_patterns[signature]))
        self.consume_energy(2.0)
    
    def predict_attack(self, context: Dict[str, Any]) -> Optional[AttackType]:
        if not self.known_attack_patterns:
            return None
        state = [0.0] * 64
        state[0] = context.get("traffic_anomaly", 0.0)
        state[1] = context.get("error_rate", 0.0)
        state[2] = context.get("latency_increase", 0.0)
        for i in range(3, 64):
            state[i] = random.gauss(0, 0.1)
        probs = self.strategy_network.forward(state)
        attack_types = list(AttackType)
        max_prob_idx = probs.index(max(probs))
        if probs[max_prob_idx] > 0.3:
            return attack_types[max_prob_idx]
        return None
    
    def receive_reward(self, reward: float, battle_result: BattleResult):
        self.add_energy(reward)
        self.total_defenses += 1
        if battle_result == BattleResult.DEFENDER_WIN:
            self.successful_defenses += 1
        success_rate = self.successful_defenses / max(1, self.total_defenses)
        self.record_experience({
            "type": "battle_result",
            "reward": reward,
            "result": battle_result.value,
            "success_rate": success_rate
        })
    
    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "true_positive_rate": self.true_positive_rate,
            "false_positive_rate": self.false_positive_rate,
            "total_defenses": self.total_defenses,
            "successful_defenses": self.successful_defenses,
            "known_patterns": len(self.known_attack_patterns)
        })
        return status


class BattleArena:
    def __init__(self, arena_id: str):
        self.arena_id = arena_id
        self.attackers: List[AttackAgent] = []
        self.defenders: List[DefenseAgent] = []
        self.battle_history: List[BattleRecord] = []
        self.current_battles: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register_attacker(self, attacker: AttackAgent):
        with self._lock:
            self.attackers.append(attacker)
    
    def register_defender(self, defender: DefenseAgent):
        with self._lock:
            self.defenders.append(defender)
    
    def run_battle(
        self,
        attacker: AttackAgent,
        defender: DefenseAgent,
        environment: Dict[str, Any]
    ) -> BattleRecord:
        battle_id = f"battle_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        attack = attacker.plan_attack(environment.get("target", "default"), environment)
        defense = defender.analyze_attack(attack, environment)
        result, attacker_reward, defender_reward = self._simulate_battle(
            attack, defense, environment
        )
        duration = time.time() - start_time
        record = BattleRecord(
            battle_id=battle_id,
            attacker_id=attacker.agent_id,
            defender_id=defender.agent_id,
            attack_type=attack.attack_type,
            defense_action=defense.action,
            attack_intensity=attack.intensity,
            result=result,
            attacker_reward=attacker_reward,
            defender_reward=defender_reward,
            timestamp=start_time,
            duration=duration,
            details={
                "attack_params": attack.params,
                "defense_params": defense.params,
                "environment": environment
            }
        )
        attacker.receive_reward(attacker_reward, result)
        defender.receive_reward(defender_reward, result)
        defender.learn_from_attack(attack, result == BattleResult.DEFENDER_WIN)
        with self._lock:
            self.battle_history.append(record)
        return record
    
    def _simulate_battle(
        self,
        attack: AttackPattern,
        defense: DefenseStrategy,
        environment: Dict[str, Any]
    ) -> Tuple[BattleResult, float, float]:
        attack_power = self._calculate_attack_power(attack)
        defense_power = self._calculate_defense_power(defense, attack)
        defense_level = environment.get("defense_level", 0.5)
        defense_power *= (1 + defense_level)
        noise = random.gauss(0, 0.1)
        outcome = attack_power - defense_power + noise
        if outcome > 0.3:
            result = BattleResult.ATTACKER_WIN
            attacker_reward = 100.0 * (1 + attack_power)
            defender_reward = -50.0
        elif outcome < -0.3:
            result = BattleResult.DEFENDER_WIN
            attacker_reward = -50.0
            defender_reward = 10.0 * attack_power
        else:
            result = BattleResult.DRAW
            attacker_reward = 10.0
            defender_reward = 10.0
        return result, attacker_reward, defender_reward
    
    def _calculate_attack_power(self, attack: AttackPattern) -> float:
        intensity_scores = {
            AttackIntensity.LOW: 0.2,
            AttackIntensity.MEDIUM: 0.5,
            AttackIntensity.HIGH: 0.8,
            AttackIntensity.CRITICAL: 1.0
        }
        base_power = intensity_scores.get(attack.intensity, 0.5)
        type_multipliers = {
            AttackType.DDOS: 1.2,
            AttackType.SQL_INJECTION: 0.8,
            AttackType.XSS: 0.6,
            AttackType.PROMPT_INJECTION: 0.7,
            AttackType.MIXED: 1.0,
            AttackType.LOW_SLOW: 0.9,
            AttackType.CC: 1.1,
            AttackType.PHISHING: 0.5,
            AttackType.BRUTE_FORCE: 0.7
        }
        multiplier = type_multipliers.get(attack.attack_type, 1.0)
        return base_power * multiplier
    
    def _calculate_defense_power(self, defense: DefenseStrategy, attack: AttackPattern) -> float:
        effectiveness = {
            DefenseAction.ALLOW: 0.1,
            DefenseAction.RATE_LIMIT: 0.5,
            DefenseAction.CAPTCHA: 0.6,
            DefenseAction.BLOCK: 0.8,
            DefenseAction.TRAFFIC_CLEAN: 0.9,
            DefenseAction.SWITCH_HIGH_DEFENSE: 0.95,
            DefenseAction.CHALLENGE: 0.7,
            DefenseAction.LOG_AND_MONITOR: 0.2
        }
        base_power = effectiveness.get(defense.action, 0.5)
        if defense.target_attack_type == attack.attack_type:
            base_power *= 1.3
        base_power *= defense.confidence
        return base_power
    
    def run_tournament(self, rounds: int = 10, environment: Optional[Dict[str, Any]] = None) -> List[BattleRecord]:
        records = []
        env = environment or {"defense_level": 0.5, "target": "test_target"}
        for _ in range(rounds):
            alive_attackers = [a for a in self.attackers if a.is_alive]
            alive_defenders = [d for d in self.defenders if d.is_alive]
            if not alive_attackers or not alive_defenders:
                break
            attacker = random.choice(alive_attackers)
            defender = random.choice(alive_defenders)
            record = self.run_battle(attacker, defender, env)
            records.append(record)
        return records
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            attacker_wins = sum(1 for r in self.battle_history if r.result == BattleResult.ATTACKER_WIN)
            defender_wins = sum(1 for r in self.battle_history if r.result == BattleResult.DEFENDER_WIN)
            draws = sum(1 for r in self.battle_history if r.result == BattleResult.DRAW)
            return {
                "arena_id": self.arena_id,
                "total_battles": len(self.battle_history),
                "attacker_wins": attacker_wins,
                "defender_wins": defender_wins,
                "draws": draws,
                "alive_attackers": len([a for a in self.attackers if a.is_alive]),
                "alive_defenders": len([d for d in self.defenders if d.is_alive])
            }


class CoEvolutionEngine:
    def __init__(self, engine_id: str):
        self.engine_id = engine_id
        self.arena = BattleArena(f"arena_{engine_id}")
        self.generation = 0
        self.population_size = 20
        self.elite_ratio = 0.2
        self.mutation_rate = 0.1
        self.evolution_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def initialize_population(self, attacker_count: int = 10, defender_count: int = 10):
        for i in range(attacker_count):
            attacker = AttackAgent(f"attacker_gen0_{i}")
            self.arena.register_attacker(attacker)
        for i in range(defender_count):
            defender = DefenseAgent(f"defender_gen0_{i}")
            self.arena.register_defender(defender)
    
    def evolve_generation(self, environment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.generation += 1
        records = self.arena.run_tournament(rounds=50, environment=environment)
        self._reproduce_population()
        self._cleanup_dead()
        stats = self.arena.get_stats()
        evolution_record = {
            "generation": self.generation,
            "stats": stats,
            "timestamp": time.time()
        }
        with self._lock:
            self.evolution_history.append(evolution_record)
        return evolution_record
    
    def _reproduce_population(self):
        alive_attackers = [a for a in self.arena.attackers if a.is_alive]
        alive_defenders = [d for d in self.arena.defenders if d.is_alive]
        sorted_attackers = sorted(alive_attackers, key=lambda a: a.success_rate, reverse=True)
        sorted_defenders = sorted(alive_defenders, key=lambda d: d.successful_defenses / max(1, d.total_defenses), reverse=True)
        elite_count = max(1, int(len(sorted_attackers) * self.elite_ratio))
        elite_attackers = sorted_attackers[:elite_count]
        for attacker in elite_attackers:
            if attacker.can_reproduce():
                child = attacker.reproduce()
                if child:
                    self.arena.register_attacker(child)
        elite_count = max(1, int(len(sorted_defenders) * self.elite_ratio))
        elite_defenders = sorted_defenders[:elite_count]
        for defender in elite_defenders:
            if defender.can_reproduce():
                child = defender.reproduce()
                if child:
                    self.arena.register_defender(child)
    
    def _cleanup_dead(self):
        self.arena.attackers = [a for a in self.arena.attackers if a.is_alive]
        self.arena.defenders = [d for d in self.arena.defenders if d.is_alive]
        if len(self.arena.attackers) < self.population_size // 2:
            for i in range(self.population_size - len(self.arena.attackers)):
                attacker = AttackAgent(f"attacker_gen{self.generation}_{i}")
                self.arena.register_attacker(attacker)
        if len(self.arena.defenders) < self.population_size // 2:
            for i in range(self.population_size - len(self.arena.defenders)):
                defender = DefenseAgent(f"defender_gen{self.generation}_{i}")
                self.arena.register_defender(defender)
    
    def run_evolution(self, generations: int = 10, environment: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = []
        for _ in range(generations):
            result = self.evolve_generation(environment)
            results.append(result)
        return results
    
    def get_best_agents(self) -> Dict[str, Any]:
        alive_attackers = [a for a in self.arena.attackers if a.is_alive]
        alive_defenders = [d for d in self.arena.defenders if d.is_alive]
        best_attacker = max(alive_attackers, key=lambda a: a.success_rate) if alive_attackers else None
        best_defender = max(alive_defenders, key=lambda d: d.successful_defenses / max(1, d.total_defenses)) if alive_defenders else None
        return {
            "best_attacker": best_attacker.get_status() if best_attacker else None,
            "best_defender": best_defender.get_status() if best_defender else None,
            "generation": self.generation
        }


class WarCenter:
    def __init__(self, center_id: str):
        self.center_id = center_id
        self.defenders: List[DefenseAgent] = []
        self.battle_mode = False
        self.threat_level = 0.0
        self.alerts: List[Dict[str, Any]] = []
        self.defense_strategies: Dict[str, DefenseStrategy] = {}
        self._lock = threading.Lock()
        self._message_handlers: Dict[str, Callable] = {}
    
    def register_defender(self, defender: DefenseAgent):
        with self._lock:
            self.defenders.append(defender)
    
    def detect_attack(self, traffic_data: Dict[str, Any], baseline: Dict[str, float]) -> Optional[AttackPattern]:
        anomaly_score = self._calculate_anomaly_score(traffic_data, baseline)
        if anomaly_score > 2.0:
            self.threat_level = min(1.0, anomaly_score / 5.0)
            attack_type = self._classify_attack(traffic_data)
            intensity = self._determine_intensity(anomaly_score)
            return AttackPattern(
                attack_type=attack_type,
                intensity=intensity,
                target=traffic_data.get("target", "unknown"),
                duration=traffic_data.get("duration", 60.0),
                params=traffic_data
            )
        return None
    
    def _calculate_anomaly_score(self, traffic_data: Dict[str, Any], baseline: Dict[str, float]) -> float:
        score = 0.0
        for key, baseline_value in baseline.items():
            current_value = traffic_data.get(key, baseline_value)
            if baseline_value > 0:
                deviation = abs(current_value - baseline_value) / baseline_value
                score += deviation
        return score / max(1, len(baseline))
    
    def _classify_attack(self, traffic_data: Dict[str, Any]) -> AttackType:
        request_rate = traffic_data.get("request_rate", 0)
        error_rate = traffic_data.get("error_rate", 0)
        sql_patterns = traffic_data.get("sql_patterns", 0)
        xss_patterns = traffic_data.get("xss_patterns", 0)
        if request_rate > 10000:
            return AttackType.DDOS
        if sql_patterns > 0:
            return AttackType.SQL_INJECTION
        if xss_patterns > 0:
            return AttackType.XSS
        if error_rate > 0.5:
            return AttackType.CC
        return AttackType.MIXED
    
    def _determine_intensity(self, anomaly_score: float) -> AttackIntensity:
        if anomaly_score > 4.0:
            return AttackIntensity.CRITICAL
        elif anomaly_score > 3.0:
            return AttackIntensity.HIGH
        elif anomaly_score > 2.0:
            return AttackIntensity.MEDIUM
        return AttackIntensity.LOW
    
    def activate_battle_mode(self, attack: AttackPattern):
        with self._lock:
            self.battle_mode = True
            self.alerts.append({
                "type": "battle_mode_activated",
                "attack": attack.to_dict(),
                "timestamp": time.time()
            })
    
    def deactivate_battle_mode(self):
        with self._lock:
            self.battle_mode = False
            self.alerts.append({
                "type": "battle_mode_deactivated",
                "timestamp": time.time()
            })
    
    def coordinate_defense(self, attack: AttackPattern, context: Dict[str, Any]) -> DefenseStrategy:
        alive_defenders = [d for d in self.defenders if d.is_alive]
        if not alive_defenders:
            return DefenseStrategy(
                action=DefenseAction.LOG_AND_MONITOR,
                confidence=0.5,
                target_attack_type=attack.attack_type,
                reasoning="No active defenders available"
            )
        if len(alive_defenders) == 1:
            return alive_defenders[0].analyze_attack(attack, context)
        team_size = min(5, len(alive_defenders))
        team = random.sample(alive_defenders, team_size)
        leader = team[0]
        return leader.coordinate(team[1:], attack)
    
    def broadcast_message(self, message_type: str, payload: Dict[str, Any]):
        with self._lock:
            for defender in self.defenders:
                if defender.is_alive:
                    handler = self._message_handlers.get(defender.agent_id)
                    if handler:
                        try:
                            handler(message_type, payload)
                        except Exception as e:
                            logger.error(f"Error broadcasting to {defender.agent_id}: {e}")
    
    def register_message_handler(self, defender_id: str, handler: Callable):
        with self._lock:
            self._message_handlers[defender_id] = handler
    
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "center_id": self.center_id,
                "battle_mode": self.battle_mode,
                "threat_level": self.threat_level,
                "active_defenders": len([d for d in self.defenders if d.is_alive]),
                "total_defenders": len(self.defenders),
                "recent_alerts": self.alerts[-10:]
            }


class AttackDefenseCluster:
    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self.evolution_engine = CoEvolutionEngine(f"evo_{cluster_id}")
        self.war_center = WarCenter(f"war_{cluster_id}")
        self.attackers: Dict[str, AttackAgent] = {}
        self.defenders: Dict[str, DefenseAgent] = {}
        self.battle_records: List[BattleRecord] = []
        self._initialized = False
    
    def initialize(self, attacker_count: int = 10, defender_count: int = 10):
        self.evolution_engine.initialize_population(attacker_count, defender_count)
        for attacker in self.evolution_engine.arena.attackers:
            self.attackers[attacker.agent_id] = attacker
        for defender in self.evolution_engine.arena.defenders:
            self.defenders[defender.agent_id] = defender
            self.war_center.register_defender(defender)
        self._initialized = True
    
    def run_training(self, generations: int = 10, environment: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self._initialized:
            self.initialize()
        return self.evolution_engine.run_evolution(generations, environment)
    
    def simulate_attack(self, attack_type: AttackType, target: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        alive_attackers = [a for a in self.attackers.values() if a.is_alive]
        if not alive_attackers:
            return {"error": "No active attackers available"}
        attacker = random.choice(alive_attackers)
        attack = attacker.plan_attack(target, environment)
        alive_defenders = [d for d in self.defenders.values() if d.is_alive]
        if not alive_defenders:
            return {
                "attack": attack.to_dict(),
                "result": "attacker_win",
                "reason": "No defenders available"
            }
        defender = random.choice(alive_defenders)
        defense = defender.analyze_attack(attack, environment)
        arena = BattleArena(f"sim_{uuid.uuid4().hex[:8]}")
        record = arena.run_battle(attacker, defender, environment)
        self.battle_records.append(record)
        return {
            "attack": attack.to_dict(),
            "defense": defense.to_dict(),
            "result": record.result.value,
            "attacker_reward": record.attacker_reward,
            "defender_reward": record.defender_reward
        }
    
    def get_cluster_status(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "initialized": self._initialized,
            "evolution_generation": self.evolution_engine.generation,
            "total_attackers": len(self.attackers),
            "alive_attackers": len([a for a in self.attackers.values() if a.is_alive]),
            "total_defenders": len(self.defenders),
            "alive_defenders": len([d for d in self.defenders.values() if d.is_alive]),
            "war_center_status": self.war_center.get_status(),
            "total_battles": len(self.battle_records)
        }


__all__ = [
    "AttackType",
    "DefenseAction", 
    "AttackIntensity",
    "BattleResult",
    "AttackPattern",
    "DefenseStrategy",
    "BattleRecord",
    "StrategyNetwork",
    "LivingAgentBase",
    "AttackAgent",
    "DefenseAgent",
    "BattleArena",
    "CoEvolutionEngine",
    "WarCenter",
    "AttackDefenseCluster"
]
