"""
战术库智能体
Tactical Library Agent

管理反击战术库，根据攻击场景推荐最佳战术
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class TacticCategory(Enum):
    LURE = "lure"
    CONSUME = "consume"
    DIVERT = "divert"
    ENCIRCLE = "encircle"
    BLOCKADE = "blockade"
    COUNTER = "counter"
    DECEPTION = "deception"


class TacticStatus(Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    UNDER_TEST = "under_test"


@dataclass
class Tactic:
    tactic_id: str
    name: str
    category: TacticCategory
    description: str
    conditions: Dict[str, Any]
    parameters: Dict[str, Any]
    required_agents: Dict[str, int]
    expected_effectiveness: float
    success_rate: float
    risk_level: float
    created_at: datetime
    last_used: Optional[datetime]
    use_count: int
    success_count: int
    failure_count: int
    tags: Set[str]
    
    def to_dict(self) -> Dict:
        return {
            "tactic_id": self.tactic_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "conditions": self.conditions,
            "parameters": self.parameters,
            "required_agents": self.required_agents,
            "expected_effectiveness": self.expected_effectiveness,
            "success_rate": self.success_rate,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "tags": list(self.tags)
        }


class TacticalLibraryAgent:
    def __init__(
        self,
        agent_id: str = "tactical_library_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.tactics: Dict[str, Tactic] = {}
        self.tactic_index: Dict[str, Set[str]] = defaultdict(set)
        self.tactic_history: deque = deque(maxlen=500)
        
        self._load_default_tactics()
        
        self.stats = {
            "total_tactics": 0,
            "tactics_recommended": 0,
            "tactics_executed": 0,
            "successful_executions": 0,
            "avg_effectiveness": 0.0
        }
        
    def _load_default_tactics(self):
        default_tactics = [
            {
                "name": "蜜罐诱捕",
                "category": TacticCategory.LURE,
                "description": "利用蜜罐引诱攻击者深入，暴露更多信息",
                "conditions": {"attack_type": ["sql_injection", "brute_force", "malware"]},
                "parameters": {"honeypot_count": 3, "interaction_timeout": 600},
                "required_agents": {"honeypot": 2, "forged_response": 1},
                "expected_effectiveness": 0.85,
                "tags": {"deception", "intelligence"}
            },
            {
                "name": "资源消耗",
                "category": TacticCategory.CONSUME,
                "description": "对攻击者实施限流、延迟响应，消耗其资源",
                "conditions": {"attack_type": ["ddos", "brute_force"]},
                "parameters": {"rate_limit": 1, "delay_ms": 5000},
                "required_agents": {"counter_strike": 1},
                "expected_effectiveness": 0.7,
                "tags": {"defensive", "resource_drain"}
            },
            {
                "name": "声东击西",
                "category": TacticCategory.DIVERT,
                "description": "佯攻攻击者其他资产，分散其注意力",
                "conditions": {"threat_level": ["high", "critical"]},
                "parameters": {"decoy_targets": 2, "confusion_level": 0.8},
                "required_agents": {"honeypot": 3, "network_morph": 1},
                "expected_effectiveness": 0.65,
                "tags": {"deception", "confusion"}
            },
            {
                "name": "围点打援",
                "category": TacticCategory.ENCIRCLE,
                "description": "围住攻击者控制的僵尸节点，诱使其主力救援",
                "conditions": {"botnet_detected": True},
                "parameters": {"bait_nodes": 2, "trap_nodes": 3},
                "required_agents": {"honeypot": 3, "pursuit": 2},
                "expected_effectiveness": 0.75,
                "tags": {"offensive", "encircle"}
            },
            {
                "name": "断其后路",
                "category": TacticCategory.BLOCKADE,
                "description": "封锁攻击者退出路径，防止其逃跑",
                "conditions": {"attack_ongoing": True},
                "parameters": {"block_exit_routes": True, "monitor_escape": True},
                "required_agents": {"pursuit": 2, "counter_strike": 1},
                "expected_effectiveness": 0.8,
                "tags": {"offensive", "containment"}
            },
            {
                "name": "快速反击",
                "category": TacticCategory.COUNTER,
                "description": "对攻击者实施精确反击",
                "conditions": {"attribution_confirmed": True, "confidence": 0.8},
                "parameters": {"counter_actions": ["rate_limit", "tcp_window"]},
                "required_agents": {"counter_strike": 1},
                "expected_effectiveness": 0.6,
                "tags": {"offensive", "aggressive"}
            },
            {
                "name": "动态迷惑",
                "category": TacticCategory.DECEPTION,
                "description": "实时变换网络结构，使攻击者无法稳定攻击",
                "conditions": {"attack_persistent": True},
                "parameters": {"ip_shift_interval": 300, "port_hop": True},
                "required_agents": {"network_morph": 1},
                "expected_effectiveness": 0.7,
                "tags": {"defensive", "evasion"}
            }
        ]
        
        for t in default_tactics:
            tactic = Tactic(
                tactic_id=self._generate_tactic_id(),
                name=t["name"],
                category=t["category"],
                description=t["description"],
                conditions=t["conditions"],
                parameters=t["parameters"],
                required_agents=t["required_agents"],
                expected_effectiveness=t["expected_effectiveness"],
                success_rate=0.7,
                risk_level=0.3,
                created_at=datetime.now(),
                last_used=None,
                use_count=0,
                success_count=0,
                failure_count=0,
                tags=t["tags"]
            )
            self.tactics[tactic.tactic_id] = tactic
            
        self.stats["total_tactics"] = len(self.tactics)
        
    async def recommend_tactics(
        self,
        attack_scenario: Dict,
        limit: int = 3
    ) -> List[Tuple[Tactic, float]]:
        scores = []
        
        for tactic in self.tactics.values():
            score = self._calculate_tactic_score(tactic, attack_scenario)
            if score > 0.3:
                scores.append((tactic, score))
                
        scores.sort(key=lambda x: x[1], reverse=True)
        
        self.stats["tactics_recommended"] += len(scores[:limit])
        
        return scores[:limit]
        
    def _calculate_tactic_score(self, tactic: Tactic, scenario: Dict) -> float:
        score = tactic.expected_effectiveness * 0.5
        
        conditions_met = 0
        total_conditions = len(tactic.conditions)
        
        for key, expected in tactic.conditions.items():
            actual = scenario.get(key)
            
            if actual is None:
                continue
                
            if isinstance(expected, list):
                if actual in expected:
                    conditions_met += 1
            elif isinstance(expected, bool):
                if actual == expected:
                    conditions_met += 1
            else:
                if actual == expected:
                    conditions_met += 1
                    
        if total_conditions > 0:
            condition_score = conditions_met / total_conditions
            score += condition_score * 0.3
            
        risk_factor = 1.0 - tactic.risk_level * 0.2
        score *= risk_factor
        
        return min(score, 1.0)
        
    async def register_tactic(
        self,
        name: str,
        category: TacticCategory,
        description: str,
        conditions: Dict,
        parameters: Dict,
        required_agents: Dict,
        tags: Set[str]
    ) -> Tactic:
        tactic = Tactic(
            tactic_id=self._generate_tactic_id(),
            name=name,
            category=category,
            description=description,
            conditions=conditions,
            parameters=parameters,
            required_agents=required_agents,
            expected_effectiveness=0.7,
            success_rate=0.7,
            risk_level=0.3,
            created_at=datetime.now(),
            last_used=None,
            use_count=0,
            success_count=0,
            failure_count=0,
            tags=tags
        )
        
        self.tactics[tactic.tactic_id] = tactic
        
        for tag in tags:
            self.tactic_index[tag].add(tactic.tactic_id)
            
        self.stats["total_tactics"] += 1
        
        logger.info(f"Registered new tactic: {name}")
        
        return tactic
        
    async def update_tactic_usage(
        self,
        tactic_id: str,
        success: bool
    ) -> bool:
        tactic = self.tactics.get(tactic_id)
        if not tactic:
            return False
            
        tactic.use_count += 1
        tactic.last_used = datetime.now()
        
        if success:
            tactic.success_count += 1
            self.stats["successful_executions"] += 1
        else:
            tactic.failure_count += 1
            
        tactic.success_rate = (
            tactic.success_count / tactic.use_count
            if tactic.use_count > 0 else 0.7
        )
        
        self.tactic_history.append({
            "tactic_id": tactic_id,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        self.stats["tactics_executed"] += 1
        
        self._update_avg_effectiveness()
        
        return True
        
    def _update_avg_effectiveness(self):
        if not self.tactics:
            return
            
        total_effectiveness = sum(
            t.expected_effectiveness for t in self.tactics.values()
        )
        self.stats["avg_effectiveness"] = total_effectiveness / len(self.tactics)
        
    async def get_tactic(self, tactic_id: str) -> Optional[Dict]:
        tactic = self.tactics.get(tactic_id)
        return tactic.to_dict() if tactic else None
        
    async def get_tactics_by_category(self, category: TacticCategory) -> List[Dict]:
        return [
            t.to_dict() for t in self.tactics.values()
            if t.category == category
        ]
        
    async def get_tactics_by_tags(self, tags: Set[str]) -> List[Dict]:
        matching_ids = None
        
        for tag in tags:
            ids = self.tactic_index.get(tag, set())
            if matching_ids is None:
                matching_ids = ids
            else:
                matching_ids &= ids
                
        if matching_ids is None:
            return []
            
        return [
            self.tactics[tid].to_dict()
            for tid in matching_ids
            if tid in self.tactics
        ]
        
    async def get_all_tactics(self) -> List[Dict]:
        return [t.to_dict() for t in self.tactics.values()]
        
    def _generate_tactic_id(self) -> str:
        return f"tactic_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "total_tactics": len(self.tactics),
            "tactic_history_size": len(self.tactic_history)
        }
