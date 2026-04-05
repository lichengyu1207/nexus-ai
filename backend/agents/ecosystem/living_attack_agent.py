"""
活体攻击智能体
Living Attack Agent

具备生命特征的攻击智能体，能够自主决定攻击目标、形成联盟、进化策略
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


class AttackStrategy(Enum):
    STEALTH = "stealth"
    BRUTE_FORCE = "brute_force"
    DISTRIBUTED = "distributed"
    ADAPTIVE = "adaptive"
    COORDINATED = "coordinated"


class LivingAttackAgent(LivingAgent):
    
    def __init__(
        self,
        agent_id: str,
        species: str = "attacker",
        initial_energy: float = 100.0,
        attack_capability: float = 0.5,
        stealth_level: float = 0.5,
        learning_rate: float = 0.001,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ATTACK,
            species=species,
            initial_energy=initial_energy,
            **kwargs
        )
        
        self.attack_capability = attack_capability
        self.stealth_level = stealth_level
        self.learning_rate = learning_rate
        
        self.strategy_library: Dict[str, Dict] = {}
        self.active_attacks: Dict[str, Dict] = {}
        self.attack_history: deque = deque(maxlen=1000)
        
        self.alliance: Set[str] = set()
        self.alliance_leader: Optional[str] = None
        self.alliance_role: Optional[str] = None
        
        self.target_preferences: Dict[str, float] = defaultdict(float)
        self.defense_knowledge: Dict[str, Dict] = {}
        
        self._init_attack_genes()
        self._init_default_strategies()
    
    def _init_attack_genes(self):
        from .living_agent import Gene
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_attack_power",
            name="attack_power",
            value=self.attack_capability,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_stealth",
            name="stealth",
            value=self.stealth_level,
            mutation_rate=0.15,
            mutation_range=(-0.15, 0.15)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_persistence",
            name="persistence",
            value=0.7,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
    
    def _init_default_strategies(self):
        self.strategy_library["stealth_probe"] = {
            "type": AttackStrategy.STEALTH.value,
            "energy_cost": 5.0,
            "success_rate": 0.6,
            "detection_risk": 0.2,
            "duration": 30
        }
        
        self.strategy_library["brute_force"] = {
            "type": AttackStrategy.BRUTE_FORCE.value,
            "energy_cost": 20.0,
            "success_rate": 0.4,
            "detection_risk": 0.8,
            "duration": 10
        }
        
        self.strategy_library["distributed_attack"] = {
            "type": AttackStrategy.DISTRIBUTED.value,
            "energy_cost": 15.0,
            "success_rate": 0.7,
            "detection_risk": 0.4,
            "duration": 60
        }
        
        self.strategy_library["adaptive_evasion"] = {
            "type": AttackStrategy.ADAPTIVE.value,
            "energy_cost": 10.0,
            "success_rate": 0.65,
            "detection_risk": 0.3,
            "duration": 45
        }
    
    def _live_cycle(self):
        self.status = AgentStatus.WORKING
        
        target = self._select_target()
        
        if target:
            strategy = self._select_strategy(target)
            
            if self._can_execute_attack(strategy):
                if self._should_form_alliance(target):
                    self._try_form_alliance(target)
                
                result = self._execute_attack(target, strategy)
                self._process_attack_result(target, strategy, result)
        
        self._learn_from_history()
        
        self.status = AgentStatus.IDLE
    
    def _select_target(self) -> Optional[Dict]:
        if not self.blackboard:
            return None
        
        targets = self.blackboard.read("attack:targets")
        if not targets:
            return None
        
        candidates = []
        for target in targets:
            score = self._evaluate_target(target)
            candidates.append((target, score))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        exploration = self.gene_pool.get_gene("exploration_rate")
        exploration_rate = exploration.value if exploration else 0.3
        
        if random.random() < exploration_rate:
            return random.choice(targets)
        
        return candidates[0][0]
    
    def _evaluate_target(self, target: Dict) -> float:
        score = 0.0
        
        difficulty = target.get("difficulty", 0.5)
        attack_power = self.gene_pool.get_gene("attack_power")
        power = attack_power.value if attack_power else self.attack_capability
        
        if power >= difficulty:
            score += (power - difficulty) * 50
        else:
            score -= (difficulty - power) * 30
        
        reward = target.get("reward", 10)
        score += reward
        
        target_id = target.get("target_id", "")
        preference = self.target_preferences.get(target_id, 0.5)
        score += preference * 10
        
        defense_info = self.defense_knowledge.get(target_id, {})
        if defense_info.get("known_weakness"):
            score += 20
        
        return score
    
    def _select_strategy(self, target: Dict) -> Dict:
        target_difficulty = target.get("difficulty", 0.5)
        target_defense = target.get("defense_level", 0.5)
        
        stealth_gene = self.gene_pool.get_gene("stealth")
        stealth = stealth_gene.value if stealth_gene else self.stealth_level
        
        if stealth > 0.7 and target_defense > 0.6:
            return self.strategy_library["stealth_probe"]
        elif target_difficulty < 0.3:
            return self.strategy_library["brute_force"]
        elif len(self.alliance) > 0:
            return self.strategy_library["distributed_attack"]
        else:
            return self.strategy_library["adaptive_evasion"]
    
    def _can_execute_attack(self, strategy: Dict) -> bool:
        energy_cost = strategy.get("energy_cost", 10)
        return self.energy >= energy_cost * 1.5
    
    def _should_form_alliance(self, target: Dict) -> bool:
        difficulty = target.get("difficulty", 0.5)
        attack_power = self.gene_pool.get_gene("attack_power")
        power = attack_power.value if attack_power else self.attack_capability
        
        cooperation = self.gene_pool.get_gene("cooperation_tendency")
        cooperation_tendency = cooperation.value if cooperation else 0.5
        
        return difficulty > power and random.random() < cooperation_tendency
    
    def _try_form_alliance(self, target: Dict) -> bool:
        if not self.blackboard:
            return False
        
        alliance_request = {
            "requester_id": self.agent_id,
            "target": target,
            "required_power": target.get("difficulty", 0.5) * 1.2,
            "reward_share": 0.7,
            "timestamp": time.time()
        }
        
        self.blackboard.write(
            f"alliance:request:{self.agent_id}",
            alliance_request,
            ttl=300,
            notify=True
        )
        
        self.consume_energy(2.0)
        
        logger.debug(f"Agent {self.agent_id} requested alliance for target {target.get('target_id')}")
        
        return True
    
    def join_alliance(self, leader_id: str, target: Dict) -> bool:
        energy_cost = 5.0
        if not self.consume_energy(energy_cost):
            return False
        
        self.alliance.add(leader_id)
        self.alliance_leader = leader_id
        self.alliance_role = "member"
        
        logger.info(f"Agent {self.agent_id} joined alliance led by {leader_id}")
        
        return True
    
    def _execute_attack(self, target: Dict, strategy: Dict) -> Dict:
        energy_cost = strategy.get("energy_cost", 10)
        self.consume_energy(energy_cost)
        
        attack_power = self.gene_pool.get_gene("attack_power")
        power = attack_power.value if attack_power else self.attack_capability
        
        stealth_gene = self.gene_pool.get_gene("stealth")
        stealth = stealth_gene.value if stealth_gene else self.stealth_level
        
        base_success_rate = strategy.get("success_rate", 0.5)
        difficulty = target.get("difficulty", 0.5)
        defense_level = target.get("defense_level", 0.5)
        
        power_advantage = max(0, power - difficulty)
        stealth_advantage = max(0, stealth - defense_level)
        
        success_rate = base_success_rate + power_advantage * 0.3 + stealth_advantage * 0.2
        success_rate = min(0.95, max(0.05, success_rate))
        
        success = random.random() < success_rate
        
        detection_risk = strategy.get("detection_risk", 0.5)
        detected = random.random() < detection_risk * (1 - stealth)
        
        attack_id = f"attack_{int(time.time() * 1000)}_{self.agent_id}"
        
        result = {
            "attack_id": attack_id,
            "target_id": target.get("target_id"),
            "strategy": strategy.get("type"),
            "success": success,
            "detected": detected,
            "energy_cost": energy_cost,
            "success_rate": success_rate,
            "timestamp": time.time()
        }
        
        self.active_attacks[attack_id] = result
        self.attack_history.append(result)
        
        return result
    
    def _process_attack_result(self, target: Dict, strategy: Dict, result: Dict):
        if result["success"]:
            reward = target.get("reward", 10)
            self.add_energy(reward)
            self.success_count += 1
            self.stats["tasks_completed"] += 1
            
            self.target_preferences[target.get("target_id", "")] += 0.1
            
            self._share_successful_strategy(strategy)
        else:
            penalty = strategy.get("energy_cost", 10) * 0.5
            self.consume_energy(penalty)
            self.failure_count += 1
            self.stats["tasks_failed"] += 1
            
            self.target_preferences[target.get("target_id", "")] -= 0.05
        
        self.record_experience({
            "type": "attack",
            "target": target,
            "strategy": strategy,
            "result": result
        })
    
    def _share_successful_strategy(self, strategy: Dict):
        cooperation = self.gene_pool.get_gene("cooperation_tendency")
        if not cooperation or cooperation.value < 0.5:
            return
        
        if not self.blackboard:
            return
        
        energy_cost = 3.0
        if not self.consume_energy(energy_cost):
            return
        
        self.blackboard.write(
            f"strategy:attack:{self.agent_id}:{int(time.time())}",
            {
                "strategy": strategy,
                "success_rate": strategy.get("success_rate", 0.5),
                "agent_id": self.agent_id,
                "species": self.species,
                "timestamp": time.time()
            },
            ttl=3600,
            notify=True
        )
    
    def learn_strategy(self, strategy: Dict, from_agent: str):
        strategy_type = strategy.get("type")
        if strategy_type not in self.strategy_library:
            self.strategy_library[strategy_type] = strategy.copy()
        else:
            existing = self.strategy_library[strategy_type]
            existing["success_rate"] = (
                existing.get("success_rate", 0.5) * 0.7 +
                strategy.get("success_rate", 0.5) * 0.3
            )
        
        logger.debug(f"Agent {self.agent_id} learned strategy from {from_agent}")
    
    def _learn_from_history(self):
        if len(self.attack_history) < 10:
            return
        
        recent = list(self.attack_history)[-50:]
        
        success_by_strategy = defaultdict(lambda: {"success": 0, "total": 0})
        for attack in recent:
            strategy_type = attack.get("strategy", "unknown")
            success_by_strategy[strategy_type]["total"] += 1
            if attack.get("success"):
                success_by_strategy[strategy_type]["success"] += 1
        
        for strategy_type, stats in success_by_strategy.items():
            if stats["total"] > 0:
                rate = stats["success"] / stats["total"]
                if strategy_type in self.strategy_library:
                    self.strategy_library[strategy_type]["success_rate"] = rate
    
    def update_defense_knowledge(self, target_id: str, defense_info: Dict):
        self.defense_knowledge[target_id] = {
            **defense_info,
            "updated_at": time.time()
        }
    
    def get_state(self) -> Dict:
        state = super().get_state()
        state.update({
            "attack_capability": self.attack_capability,
            "stealth_level": self.stealth_level,
            "strategies_count": len(self.strategy_library),
            "active_attacks": len(self.active_attacks),
            "alliance_size": len(self.alliance),
            "alliance_leader": self.alliance_leader,
            "defense_knowledge_count": len(self.defense_knowledge)
        })
        return state
