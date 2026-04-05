"""
活体防御智能体
Living Defense Agent

具备生命特征的防御智能体，能够自适应学习、团队协作、预测攻击
"""

import os
import json
import time
import logging
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import deque, defaultdict
from enum import Enum
import numpy as np

from .living_agent import LivingAgent, AgentRole, AgentStatus

logger = logging.getLogger(__name__)


class DefenseStrategy(Enum):
    BLOCK = "block"
    RATE_LIMIT = "rate_limit"
    CHALLENGE = "challenge"
    ISOLATE = "isolate"
    DECOY = "decoy"
    ADAPTIVE = "adaptive"


class LivingDefenseAgent(LivingAgent):
    
    def __init__(
        self,
        agent_id: str,
        species: str = "defender",
        initial_energy: float = 100.0,
        defense_capability: float = 0.5,
        detection_accuracy: float = 0.5,
        learning_rate: float = 0.001,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.DEFENSE,
            species=species,
            initial_energy=initial_energy,
            **kwargs
        )
        
        self.defense_capability = defense_capability
        self.detection_accuracy = detection_accuracy
        self.learning_rate = learning_rate
        
        self.defense_strategies: Dict[str, Dict] = {}
        self.active_defenses: Dict[str, Dict] = {}
        self.defense_history: deque = deque(maxlen=1000)
        
        self.team: Set[str] = set()
        self.team_leader: Optional[str] = None
        self.team_role: Optional[str] = None
        self.responsibility_zone: Optional[str] = None
        
        self.known_attack_patterns: Dict[str, Dict] = {}
        self.attack_predictions: List[Dict] = []
        
        self.experience_replay: deque = deque(maxlen=5000)
        self.model_update_pending = False
        
        self._init_defense_genes()
        self._init_default_strategies()
    
    def _init_defense_genes(self):
        from .living_agent import Gene
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_defense_power",
            name="defense_power",
            value=self.defense_capability,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_detection",
            name="detection_accuracy",
            value=self.detection_accuracy,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_vigilance",
            name="vigilance_level",
            value=0.7,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_coordination",
            name="coordination_ability",
            value=0.6,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
    
    def _init_default_strategies(self):
        self.defense_strategies["immediate_block"] = {
            "type": DefenseStrategy.BLOCK.value,
            "energy_cost": 5.0,
            "effectiveness": 0.9,
            "false_positive_risk": 0.1,
            "response_time": 0.1
        }
        
        self.defense_strategies["rate_limit"] = {
            "type": DefenseStrategy.RATE_LIMIT.value,
            "energy_cost": 3.0,
            "effectiveness": 0.7,
            "false_positive_risk": 0.05,
            "response_time": 0.5
        }
        
        self.defense_strategies["challenge_response"] = {
            "type": DefenseStrategy.CHALLENGE.value,
            "energy_cost": 2.0,
            "effectiveness": 0.8,
            "false_positive_risk": 0.02,
            "response_time": 2.0
        }
        
        self.defense_strategies["isolation"] = {
            "type": DefenseStrategy.ISOLATE.value,
            "energy_cost": 10.0,
            "effectiveness": 0.95,
            "false_positive_risk": 0.15,
            "response_time": 1.0
        }
        
        self.defense_strategies["decoy_trap"] = {
            "type": DefenseStrategy.DECOY.value,
            "energy_cost": 15.0,
            "effectiveness": 0.85,
            "false_positive_risk": 0.01,
            "response_time": 5.0
        }
        
        self.defense_strategies["adaptive_response"] = {
            "type": DefenseStrategy.ADAPTIVE.value,
            "energy_cost": 8.0,
            "effectiveness": 0.75,
            "false_positive_risk": 0.08,
            "response_time": 1.5
        }
    
    def _live_cycle(self):
        self.status = AgentStatus.WORKING
        
        threat = self._detect_threat()
        
        if threat:
            strategy = self._select_defense_strategy(threat)
            
            if self._should_coordinate(threat):
                self._coordinate_defense(threat)
            
            result = self._execute_defense(threat, strategy)
            self._process_defense_result(threat, strategy, result)
        
        self._predict_future_attacks()
        
        self._learn_from_experience()
        
        self.status = AgentStatus.IDLE
    
    def _detect_threat(self) -> Optional[Dict]:
        if not self.blackboard:
            return None
        
        threats = self.blackboard.read("defense:threats")
        if not threats:
            return None
        
        detection_gene = self.gene_pool.get_gene("detection_accuracy")
        detection = detection_gene.value if detection_gene else self.detection_accuracy
        
        vigilance_gene = self.gene_pool.get_gene("vigilance_level")
        vigilance = vigilance_gene.value if vigilance_gene else 0.7
        
        detected_threats = []
        for threat in threats:
            if random.random() < detection:
                threat["detected_by"] = self.agent_id
                threat["detection_confidence"] = detection
                detected_threats.append(threat)
        
        if not detected_threats:
            return None
        
        detected_threats.sort(
            key=lambda t: t.get("severity", 0) * t.get("detection_confidence", 0),
            reverse=True
        )
        
        return detected_threats[0]
    
    def _select_defense_strategy(self, threat: Dict) -> Dict:
        threat_type = threat.get("type", "unknown")
        severity = threat.get("severity", 0.5)
        
        defense_power = self.gene_pool.get_gene("defense_power")
        power = defense_power.value if defense_power else self.defense_capability
        
        if severity > 0.8:
            return self.defense_strategies["immediate_block"]
        elif threat_type in ["brute_force", "ddos"]:
            return self.defense_strategies["rate_limit"]
        elif threat_type in ["stealth", "probe"]:
            return self.defense_strategies["challenge_response"]
        elif severity > 0.6 and power > 0.7:
            return self.defense_strategies["decoy_trap"]
        else:
            return self.defense_strategies["adaptive_response"]
    
    def _should_coordinate(self, threat: Dict) -> bool:
        severity = threat.get("severity", 0.5)
        coordination = self.gene_pool.get_gene("coordination_ability")
        coordination_ability = coordination.value if coordination else 0.5
        
        return severity > 0.6 and coordination_ability > 0.5
    
    def _coordinate_defense(self, threat: Dict):
        if not self.blackboard:
            return
        
        energy_cost = 5.0
        if not self.consume_energy(energy_cost):
            return
        
        coordination_request = {
            "coordinator_id": self.agent_id,
            "threat": threat,
            "required_defenders": max(2, int(threat.get("severity", 0.5) * 10)),
            "timestamp": time.time()
        }
        
        self.blackboard.write(
            f"defense:coordination:{self.agent_id}",
            coordination_request,
            ttl=300,
            notify=True
        )
        
        logger.debug(f"Agent {self.agent_id} initiated defense coordination for threat")
    
    def join_defense_team(self, leader_id: str, threat: Dict, role: str = "member") -> bool:
        energy_cost = 3.0
        if not self.consume_energy(energy_cost):
            return False
        
        self.team.add(leader_id)
        self.team_leader = leader_id
        self.team_role = role
        
        logger.info(f"Agent {self.agent_id} joined defense team led by {leader_id}")
        
        return True
    
    def _execute_defense(self, threat: Dict, strategy: Dict) -> Dict:
        energy_cost = strategy.get("energy_cost", 5)
        self.consume_energy(energy_cost)
        
        defense_power = self.gene_pool.get_gene("defense_power")
        power = defense_power.value if defense_power else self.defense_capability
        
        base_effectiveness = strategy.get("effectiveness", 0.5)
        threat_severity = threat.get("severity", 0.5)
        
        effectiveness = base_effectiveness * (1 + (power - threat_severity) * 0.5)
        effectiveness = min(0.98, max(0.1, effectiveness))
        
        success = random.random() < effectiveness
        
        false_positive_risk = strategy.get("false_positive_risk", 0.1)
        false_positive = random.random() < false_positive_risk
        
        defense_id = f"defense_{int(time.time() * 1000)}_{self.agent_id}"
        
        result = {
            "defense_id": defense_id,
            "threat_id": threat.get("threat_id"),
            "strategy": strategy.get("type"),
            "success": success,
            "false_positive": false_positive,
            "energy_cost": energy_cost,
            "effectiveness": effectiveness,
            "response_time": strategy.get("response_time", 1.0),
            "timestamp": time.time()
        }
        
        self.active_defenses[defense_id] = result
        self.defense_history.append(result)
        
        return result
    
    def _process_defense_result(self, threat: Dict, strategy: Dict, result: Dict):
        if result["success"] and not result["false_positive"]:
            reward = threat.get("severity", 0.5) * 20
            self.add_energy(reward)
            self.success_count += 1
            self.stats["tasks_completed"] += 1
            
            self._learn_attack_pattern(threat, strategy)
            
            self._share_successful_defense(strategy, threat)
        
        elif result["false_positive"]:
            penalty = strategy.get("energy_cost", 5) * 0.5
            self.consume_energy(penalty)
            self.failure_count += 1
        
        else:
            penalty = strategy.get("energy_cost", 5) * 0.3
            self.consume_energy(penalty)
            self.failure_count += 1
            self.stats["tasks_failed"] += 1
        
        self.experience_replay.append({
            "threat": threat,
            "strategy": strategy,
            "result": result,
            "energy": self.energy,
            "timestamp": time.time()
        })
        
        self.record_experience({
            "type": "defense",
            "threat": threat,
            "strategy": strategy,
            "result": result
        })
    
    def _learn_attack_pattern(self, threat: Dict, successful_strategy: Dict):
        pattern_key = self._generate_pattern_key(threat)
        
        if pattern_key not in self.known_attack_patterns:
            self.known_attack_patterns[pattern_key] = {
                "pattern": threat,
                "effective_strategies": [],
                "occurrence_count": 0,
                "first_seen": time.time()
            }
        
        self.known_attack_patterns[pattern_key]["occurrence_count"] += 1
        self.known_attack_patterns[pattern_key]["last_seen"] = time.time()
        
        strategy_type = successful_strategy.get("type")
        if strategy_type not in self.known_attack_patterns[pattern_key]["effective_strategies"]:
            self.known_attack_patterns[pattern_key]["effective_strategies"].append(strategy_type)
    
    def _generate_pattern_key(self, threat: Dict) -> str:
        key_features = [
            threat.get("type", "unknown"),
            str(int(threat.get("severity", 0) * 10)),
            threat.get("source_type", "unknown")
        ]
        return "_".join(key_features)
    
    def _share_successful_defense(self, strategy: Dict, threat: Dict):
        coordination = self.gene_pool.get_gene("coordination_ability")
        if not coordination or coordination.value < 0.5:
            return
        
        if not self.blackboard:
            return
        
        energy_cost = 3.0
        if not self.consume_energy(energy_cost):
            return
        
        self.blackboard.write(
            f"defense:success:{self.agent_id}:{int(time.time())}",
            {
                "strategy": strategy,
                "threat_type": threat.get("type"),
                "effectiveness": strategy.get("effectiveness"),
                "agent_id": self.agent_id,
                "timestamp": time.time()
            },
            ttl=3600,
            notify=True
        )
    
    def learn_defense_strategy(self, strategy: Dict, threat_type: str):
        strategy_type = strategy.get("type")
        
        if strategy_type not in self.defense_strategies:
            self.defense_strategies[strategy_type] = strategy.copy()
        else:
            existing = self.defense_strategies[strategy_type]
            existing["effectiveness"] = (
                existing.get("effectiveness", 0.5) * 0.7 +
                strategy.get("effectiveness", 0.5) * 0.3
            )
        
        logger.debug(f"Agent {self.agent_id} learned defense strategy for {threat_type}")
    
    def _predict_future_attacks(self):
        if len(self.defense_history) < 20:
            return
        
        recent = list(self.defense_history)[-100:]
        
        attack_intervals = []
        last_time = None
        for defense in recent:
            if last_time:
                interval = defense["timestamp"] - last_time
                attack_intervals.append(interval)
            last_time = defense["timestamp"]
        
        if attack_intervals:
            avg_interval = np.mean(attack_intervals)
            next_predicted = time.time() + avg_interval
            
            self.attack_predictions = [{
                "predicted_time": next_predicted,
                "confidence": 0.6,
                "based_on": "historical_pattern"
            }]
    
    def _learn_from_experience(self):
        if len(self.experience_replay) < 50:
            return
        
        sample_size = min(100, len(self.experience_replay))
        samples = random.sample(list(self.experience_replay), sample_size)
        
        strategy_performance = defaultdict(lambda: {"success": 0, "total": 0})
        
        for sample in samples:
            strategy_type = sample["strategy"].get("type")
            strategy_performance[strategy_type]["total"] += 1
            if sample["result"].get("success"):
                strategy_performance[strategy_type]["success"] += 1
        
        for strategy_type, perf in strategy_performance.items():
            if perf["total"] > 0 and strategy_type in self.defense_strategies:
                new_rate = perf["success"] / perf["total"]
                current = self.defense_strategies[strategy_type].get("effectiveness", 0.5)
                self.defense_strategies[strategy_type]["effectiveness"] = (
                    current * 0.8 + new_rate * 0.2
                )
    
    def request_memory_assistance(self, query: str) -> Optional[Dict]:
        if not self.blackboard:
            return None
        
        energy_cost = 2.0
        if not self.consume_energy(energy_cost):
            return None
        
        self.blackboard.write(
            f"memory:query:{self.agent_id}",
            {
                "query": query,
                "requester_id": self.agent_id,
                "requester_role": "defense",
                "timestamp": time.time()
            },
            ttl=60,
            notify=True
        )
        
        return None
    
    def get_state(self) -> Dict:
        state = super().get_state()
        state.update({
            "defense_capability": self.defense_capability,
            "detection_accuracy": self.detection_accuracy,
            "strategies_count": len(self.defense_strategies),
            "active_defenses": len(self.active_defenses),
            "team_size": len(self.team),
            "team_leader": self.team_leader,
            "known_patterns": len(self.known_attack_patterns),
            "predictions_count": len(self.attack_predictions)
        })
        return state
