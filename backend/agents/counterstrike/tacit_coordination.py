"""
默会协调模块
Tacit Coordination Module

通过预训练和奖励塑形，让智能体形成无需通信的默契配合
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


class CoordinationPattern(Enum):
    FLANK = "flank"
    SURROUND = "surround"
    PINCER = "pincer"
    FEINT = "feint"
    AMBUSH = "ambush"
    RETREAT = "retreat"
    REGROUP = "regroup"


class AgentState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    ATTACKING = "attacking"
    DEFENDING = "defending"
    RETREATING = "retreating"


@dataclass
class CoordinationPattern:
    pattern_id: str
    pattern_type: str
    positions: Dict[str, Tuple[float, float]]
    roles: Dict[str, str]
    conditions: Dict[str, Any]
    effectiveness: float
    
    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "positions": self.positions,
            "roles": self.roles,
            "conditions": self.conditions,
            "effectiveness": self.effectiveness
        }


class SpatialReasoner:
    def __init__(self):
        self.spatial_thresholds = {
            "close": 0.2,
            "medium": 0.5,
            "far": 0.8
        }
        
    def calculate_distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
        
    def calculate_angle(
        self,
        from_pos: Tuple[float, float],
        to_pos: Tuple[float, float]
    ) -> float:
        import math
        return math.atan2(to_pos[1] - from_pos[1], to_pos[0] - from_pos[0])
        
    def get_relative_position(
        self,
        agent_pos: Tuple[float, float],
        target_pos: Tuple[float, float]
    ) -> str:
        distance = self.calculate_distance(agent_pos, target_pos)
        
        if distance < self.spatial_thresholds["close"]:
            return "close"
        elif distance < self.spatial_thresholds["medium"]:
            return "medium"
        else:
            return "far"
            
    def calculate_formation_score(
        self,
        positions: Dict[str, Tuple[float, float]],
        target_pos: Tuple[float, float]
    ) -> float:
        if not positions:
            return 0.0
            
        angles = []
        for pos in positions.values():
            angle = self.calculate_angle(pos, target_pos)
            angles.append(angle)
            
        if len(angles) < 2:
            return 0.5
            
        angles.sort()
        gaps = []
        for i in range(len(angles)):
            next_i = (i + 1) % len(angles)
            gap = angles[next_i] - angles[i]
            if gap < 0:
                gap += 2 * 3.14159
            gaps.append(gap)
            
        import statistics
        if not gaps:
            return 0.5
            
        avg_gap = statistics.mean(gaps)
        std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        ideal_gap = 2 * 3.14159 / len(angles)
        gap_score = 1.0 - min(1.0, abs(avg_gap - ideal_gap) / ideal_gap)
        spread_score = 1.0 - min(1.0, std_gap / ideal_gap)
        
        return (gap_score + spread_score) / 2


class RewardShaper:
    def __init__(self):
        self.reward_weights = {
            "spatial": 0.3,
            "coordination": 0.3,
            "effectiveness": 0.2,
            "efficiency": 0.2
        }
        
    def calculate_intrinsic_reward(
        self,
        agent_state: Dict,
        team_states: Dict[str, Dict],
        outcome: Dict
    ) -> float:
        spatial_reward = self._calculate_spatial_reward(agent_state, team_states)
        coordination_reward = self._calculate_coordination_reward(agent_state, team_states)
        effectiveness_reward = self._calculate_effectiveness_reward(outcome)
        efficiency_reward = self._calculate_efficiency_reward(agent_state, outcome)
        
        total_reward = (
            spatial_reward * self.reward_weights["spatial"] +
            coordination_reward * self.reward_weights["coordination"] +
            effectiveness_reward * self.reward_weights["effectiveness"] +
            efficiency_reward * self.reward_weights["efficiency"]
        )
        
        return total_reward
        
    def _calculate_spatial_reward(
        self,
        agent_state: Dict,
        team_states: Dict[str, Dict]
    ) -> float:
        position = agent_state.get("position", (0.5, 0.5))
        target = agent_state.get("target_position")
        
        if not target:
            return 0.5
            
        import math
        distance = math.sqrt(
            (position[0] - target[0]) ** 2 +
            (position[1] - target[1]) ** 2
        )
        
        return max(0, 1.0 - distance)
        
    def _calculate_coordination_reward(
        self,
        agent_state: Dict,
        team_states: Dict[str, Dict]
    ) -> float:
        if not team_states:
            return 0.5
            
        role = agent_state.get("role", "unknown")
        position = agent_state.get("position", (0.5, 0.5))
        
        role_distances = {
            "hunter": {"optimal": 0.3, "min": 0.1},
            "blocker": {"optimal": 0.4, "min": 0.2},
            "decoy": {"optimal": 0.5, "min": 0.3},
            "scout": {"optimal": 0.6, "min": 0.2}
        }
        
        optimal_config = role_distances.get(role, {"optimal": 0.4, "min": 0.2})
        
        teammate_distances = []
        for teammate_state in team_states.values():
            teammate_pos = teammate_state.get("position", (0.5, 0.5))
            import math
            dist = math.sqrt(
                (position[0] - teammate_pos[0]) ** 2 +
                (position[1] - teammate_pos[1]) ** 2
            )
            teammate_distances.append(dist)
            
        if not teammate_distances:
            return 0.5
            
        avg_distance = sum(teammate_distances) / len(teammate_distances)
        
        if avg_distance < optimal_config["min"]:
            return 0.3
        elif avg_distance < optimal_config["optimal"]:
            return 1.0
        else:
            return max(0.3, 1.0 - (avg_distance - optimal_config["optimal"]))
            
    def _calculate_effectiveness_reward(self, outcome: Dict) -> float:
        return outcome.get("effectiveness", 0.5)
        
    def _calculate_efficiency_reward(
        self,
        agent_state: Dict,
        outcome: Dict
    ) -> float:
        actions_taken = agent_state.get("actions_taken", 1)
        optimal_actions = outcome.get("optimal_actions", actions_taken)
        
        if optimal_actions == 0:
            return 1.0
            
        ratio = optimal_actions / max(actions_taken, 1)
        return min(1.0, ratio)


class PatternRecognizer:
    def __init__(self):
        self.patterns = self._load_patterns()
        self.pattern_history: deque = deque(maxlen=1000)
        
    def _load_patterns(self) -> Dict[str, Dict]:
        return {
            "flank": {
                "description": "Approach target from the side",
                "angle_threshold": 0.5,
                "distance_range": (0.2, 0.5),
                "min_agents": 2
            },
            "surround": {
                "description": "Encircle target from all sides",
                "angle_threshold": 0.3,
                "distance_range": (0.3, 0.6),
                "min_agents": 4
            },
            "pincer": {
                "description": "Attack from two opposite sides",
                "angle_threshold": 0.4,
                "distance_range": (0.2, 0.4),
                "min_agents": 2
            },
            "feint": {
                "description": "Fake attack to distract",
                "angle_threshold": 0.6,
                "distance_range": (0.4, 0.7),
                "min_agents": 2
            }
        }
        
    def recognize_pattern(
        self,
        positions: Dict[str, Tuple[float, float]],
        target_pos: Tuple[float, float]
    ) -> Optional[str]:
        if len(positions) < 2:
            return None
            
        angles = []
        for agent_id, pos in positions.items():
            import math
            angle = math.atan2(
                target_pos[1] - pos[1],
                target_pos[0] - pos[0]
            )
            angles.append(angle)
            
        angles.sort()
        
        for pattern_name, pattern_def in self.patterns.items():
            if len(positions) < pattern_def["min_agents"]:
                continue
                
            if self._match_pattern(angles, pattern_def):
                self.pattern_history.append({
                    "pattern": pattern_name,
                    "agents": list(positions.keys()),
                    "timestamp": datetime.now().isoformat()
                })
                return pattern_name
                
        return None
        
    def _match_pattern(self, angles: List[float], pattern_def: Dict) -> bool:
        if len(angles) < pattern_def["min_agents"]:
            return False
            
        if pattern_def.get("angle_threshold"):
            gaps = []
            for i in range(len(angles)):
                next_i = (i + 1) % len(angles)
                gap = angles[next_i] - angles[i]
                if gap < 0:
                    gap += 2 * 3.14159
                gaps.append(gap)
                
            import statistics
            if gaps:
                std = statistics.stdev(gaps)
                return std < pattern_def["angle_threshold"]
                
        return False


class TacitCoordinationModule:
    def __init__(
        self,
        module_id: str = "tacit_coord_001",
        communication_bus: Optional[Any] = None
    ):
        self.module_id = module_id
        self.communication_bus = communication_bus
        
        self.spatial_reasoner = SpatialReasoner()
        self.reward_shaper = RewardShaper()
        self.pattern_recognizer = PatternRecognizer()
        
        self.agent_states: Dict[str, Dict] = {}
        self.team_formations: Dict[str, str] = {}
        
        self.coordination_history: deque = deque(maxlen=500)
        
        self.stats = {
            "patterns_recognized": 0,
            "rewards_calculated": 0,
            "avg_team_score": 0.0
        }
        
        self._running = False
        
    async def start(self):
        self._running = True
        logger.info(f"TacitCoordinationModule {self.module_id} started")
        
    async def stop(self):
        self._running = False
        logger.info(f"TacitCoordinationModule {self.module_id} stopped")
        
    def update_agent_state(
        self,
        agent_id: str,
        position: Tuple[float, float],
        role: str,
        state: AgentState,
        target: Optional[Tuple[float, float]] = None
    ):
        self.agent_states[agent_id] = {
            "agent_id": agent_id,
            "position": position,
            "role": role,
            "state": state.value,
            "target_position": target,
            "updated_at": datetime.now().isoformat()
        }
        
    def get_coordination_action(
        self,
        agent_id: str,
        team_ids: List[str]
    ) -> Dict:
        agent_state = self.agent_states.get(agent_id)
        if not agent_state:
            return {"action": "idle", "confidence": 0.0}
            
        team_states = {
            tid: self.agent_states.get(tid, {})
            for tid in team_ids
            if tid in self.agent_states
        }
        
        positions = {
            aid: state["position"]
            for aid, state in team_states.items()
            if "position" in state
        }
        positions[agent_id] = agent_state["position"]
        
        target = agent_state.get("target_position", (0.5, 0.5))
        
        pattern = self.pattern_recognizer.recognize_pattern(positions, target)
        
        if pattern:
            self.stats["patterns_recognized"] += 1
            
        suggested_action = self._suggest_action(agent_id, pattern, agent_state, team_states)
        
        return {
            "action": suggested_action,
            "pattern": pattern,
            "confidence": 0.8 if pattern else 0.5
        }
        
    def _suggest_action(
        self,
        agent_id: str,
        pattern: Optional[str],
        agent_state: Dict,
        team_states: Dict[str, Dict]
    ) -> str:
        role = agent_state.get("role", "hunter")
        state = agent_state.get("state", "idle")
        
        if pattern == "flank":
            if role == "hunter":
                return "approach_side"
            elif role == "blocker":
                return "cut_off_escape"
                
        elif pattern == "surround":
            if role == "hunter":
                return "close_in"
            elif role == "blocker":
                return "seal_perimeter"
                
        elif pattern == "pincer":
            if role == "hunter":
                return "squeeze"
            elif role == "decoy":
                return "distract"
                
        if state == "idle":
            return "move_to_position"
        elif state == "moving":
            return "continue"
        else:
            return "hold"
            
    def calculate_team_reward(
        self,
        team_ids: List[str],
        outcome: Dict
    ) -> Dict[str, float]:
        rewards = {}
        
        for agent_id in team_ids:
            agent_state = self.agent_states.get(agent_id, {})
            team_states = {
                tid: self.agent_states.get(tid, {})
                for tid in team_ids
                if tid != agent_id and tid in self.agent_states
            }
            
            reward = self.reward_shaper.calculate_intrinsic_reward(
                agent_state,
                team_states,
                outcome
            )
            
            rewards[agent_id] = reward
            
        self.stats["rewards_calculated"] += len(rewards)
        
        if rewards:
            self.stats["avg_team_score"] = sum(rewards.values()) / len(rewards)
            
        return rewards
        
    def get_formation_score(
        self,
        team_ids: List[str],
        target_pos: Tuple[float, float]
    ) -> float:
        positions = {}
        for agent_id in team_ids:
            state = self.agent_states.get(agent_id)
            if state and "position" in state:
                positions[agent_id] = state["position"]
                
        return self.spatial_reasoner.calculate_formation_score(positions, target_pos)
        
    async def get_coordination_stats(self) -> Dict:
        return {
            **self.stats,
            "active_agents": len(self.agent_states),
            "recent_patterns": list(self.pattern_recognizer.pattern_history)[-10:]
        }
