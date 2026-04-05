"""
协同围剿智能体
Coordinated Pursuit Agent

调度攻击智能体集群和防御智能体集群协同围剿
使用虚拟信息素进行间接通信，实现默会协调
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class AgentRole(Enum):
    ATTACKER = "attacker"
    DEFENDER = "defender"
    DECOY = "decoy"
    SCOUT = "scout"
    BLOCKER = "blocker"
    HUNTER = "hunter"


class FormationType(Enum):
    SURROUND = "surround"
    PINCER = "pincer"
    AMBUSH = "ambush"
    PURSUIT = "pursuit"
    BLOCKADE = "blockade"
    DECOY_AND_STRIKE = "decoy_and_strike"


class PursuitPhase(Enum):
    RECONNAISSANCE = "reconnaissance"
    POSITIONING = "positioning"
    ENGAGEMENT = "engagement"
    CONTAINMENT = "containment"
    NEUTRALIZATION = "neutralization"
    CLEANUP = "cleanup"


class PursuitStatus(Enum):
    PLANNING = "planning"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PursuitStrategy:
    strategy_id: str
    formation: FormationType
    target_identity: str
    target_ips: List[str]
    assigned_agents: Dict[str, AgentRole]
    phases: List[PursuitPhase]
    current_phase: PursuitPhase
    created_at: datetime
    estimated_duration: int
    priority: int
    
    def to_dict(self) -> Dict:
        return {
            "strategy_id": self.strategy_id,
            "formation": self.formation.value,
            "target_identity": self.target_identity,
            "target_ips": self.target_ips,
            "assigned_agents": {k: v.value for k, v in self.assigned_agents.items()},
            "phases": [p.value for p in self.phases],
            "current_phase": self.current_phase.value,
            "created_at": self.created_at.isoformat(),
            "estimated_duration": self.estimated_duration,
            "priority": self.priority
        }


@dataclass
class AgentAssignment:
    agent_id: str
    role: AgentRole
    position: Tuple[float, float]
    target_zone: Optional[Tuple[float, float]]
    status: str
    last_action: Optional[str]
    effectiveness: float
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "position": self.position,
            "target_zone": self.target_zone,
            "status": self.status,
            "last_action": self.last_action,
            "effectiveness": self.effectiveness
        }


class VirtualStigmergy:
    def __init__(self, grid_size: int = 100):
        self.grid_size = grid_size
        self.pheromone_grid: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(
            lambda: {"threat": 0.0, "target": 0.0, "path": 0.0, "avoid": 0.0}
        )
        self.deposit_history: deque = deque(maxlen=1000)
        
    def deposit_pheromone(
        self,
        position: Tuple[float, float],
        pheromone_type: str,
        amount: float
    ):
        grid_pos = self._to_grid(position)
        current = self.pheromone_grid[grid_pos].get(pheromone_type, 0.0)
        self.pheromone_grid[grid_pos][pheromone_type] = min(current + amount, 1.0)
        
        self.deposit_history.append({
            "position": position,
            "type": pheromone_type,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        })
        
    def read_pheromone(
        self,
        position: Tuple[float, float],
        pheromone_type: str
    ) -> float:
        grid_pos = self._to_grid(position)
        return self.pheromone_grid[grid_pos].get(pheromone_type, 0.0)
        
    def read_neighborhood(
        self,
        position: Tuple[float, float],
        radius: int = 3
    ) -> Dict[str, float]:
        grid_pos = self._to_grid(position)
        totals = defaultdict(float)
        counts = defaultdict(int)
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                neighbor = (grid_pos[0] + dx, grid_pos[1] + dy)
                for ptype, value in self.pheromone_grid[neighbor].items():
                    totals[ptype] += value
                    counts[ptype] += 1
                    
        return {
            ptype: totals[ptype] / counts[ptype] if counts[ptype] > 0 else 0.0
            for ptype in ["threat", "target", "path", "avoid"]
        }
        
    def evaporate(self, rate: float = 0.1):
        for pos in list(self.pheromone_grid.keys()):
            for ptype in self.pheromone_grid[pos]:
                self.pheromone_grid[pos][ptype] *= (1 - rate)
                
    def _to_grid(self, position: Tuple[float, float]) -> Tuple[int, int]:
        return (
            int(position[0] * self.grid_size) % self.grid_size,
            int(position[1] * self.grid_size) % self.grid_size
        )
        
    def get_hotspots(self, pheromone_type: str, threshold: float = 0.5) -> List[Tuple[int, int]]:
        return [
            pos for pos, values in self.pheromone_grid.items()
            if values.get(pheromone_type, 0) >= threshold
        ]


class FormationManager:
    def __init__(self):
        self.formations = self._define_formations()
        
    def _define_formations(self) -> Dict[FormationType, Dict]:
        return {
            FormationType.SURROUND: {
                "description": "Surround target from all sides",
                "min_agents": 4,
                "positions": self._generate_surround_positions,
                "roles": [AgentRole.BLOCKER, AgentRole.HUNTER, AgentRole.HUNTER, AgentRole.HUNTER]
            },
            FormationType.PINCER: {
                "description": "Attack from two flanks simultaneously",
                "min_agents": 4,
                "positions": self._generate_pincer_positions,
                "roles": [AgentRole.HUNTER, AgentRole.HUNTER, AgentRole.BLOCKER, AgentRole.BLOCKER]
            },
            FormationType.AMBUSH: {
                "description": "Hide and strike when target is vulnerable",
                "min_agents": 3,
                "positions": self._generate_ambush_positions,
                "roles": [AgentRole.DECOY, AgentRole.HUNTER, AgentRole.HUNTER]
            },
            FormationType.PURSUIT: {
                "description": "Chase and corner the target",
                "min_agents": 3,
                "positions": self._generate_pursuit_positions,
                "roles": [AgentRole.SCOUT, AgentRole.HUNTER, AgentRole.HUNTER]
            },
            FormationType.BLOCKADE: {
                "description": "Block all escape routes",
                "min_agents": 4,
                "positions": self._generate_blockade_positions,
                "roles": [AgentRole.BLOCKER, AgentRole.BLOCKER, AgentRole.BLOCKER, AgentRole.HUNTER]
            },
            FormationType.DECOY_AND_STRIKE: {
                "description": "Use decoy to distract, then strike",
                "min_agents": 3,
                "positions": self._generate_decoy_strike_positions,
                "roles": [AgentRole.DECOY, AgentRole.HUNTER, AgentRole.HUNTER]
            }
        }
        
    def _generate_surround_positions(self, center: Tuple[float, float], count: int) -> List[Tuple[float, float]]:
        positions = []
        for i in range(count):
            angle = 2 * 3.14159 * i / count
            x = center[0] + 0.3 * (1 + 0.1 * (i % 2)) * (1 if i % 2 == 0 else -1)
            y = center[1] + 0.3 * (1 + 0.1 * ((i + 1) % 2))
            positions.append((x, y))
        return positions
        
    def _generate_pincer_positions(self, center: Tuple[float, float], count: int) -> List[Tuple[float, float]]:
        positions = []
        for i in range(count):
            if i < count // 2:
                positions.append((center[0] - 0.4 - i * 0.1, center[1] + 0.2 * (i % 2)))
            else:
                positions.append((center[0] + 0.4 + (i - count // 2) * 0.1, center[1] + 0.2 * (i % 2)))
        return positions
        
    def _generate_ambush_positions(self, center: Tuple[float, float], count: int) -> List[Tuple[float, float]]:
        positions = [(center[0], center[1] - 0.3)]
        for i in range(count - 1):
            positions.append((center[0] + 0.3 * (1 if i % 2 == 0 else -1), center[1] + 0.2))
        return positions
        
    def _generate_pursuit_positions(self, center: Tuple[float, float], count: int) -> List[Tuple[float, float]]:
        positions = []
        for i in range(count):
            positions.append((center[0] - 0.2 - i * 0.15, center[1] + 0.1 * (i % 2)))
        return positions
        
    def _generate_blockade_positions(self, center: Tuple[float, float], count: int) -> List[Tuple[float, float]]:
        positions = []
        for i in range(count):
            angle = 2 * 3.14159 * i / count
            x = center[0] + 0.5 * (1 if abs(angle - 3.14159/2) < 0.5 else -1)
            y = center[1] + 0.5 * (1 if angle < 3.14159 else -1)
            positions.append((x, y))
        return positions
        
    def _generate_decoy_strike_positions(self, center: Tuple[float, float], count: int) -> List[Tuple[float, float]]:
        positions = [(center[0], center[1] + 0.4)]
        for i in range(count - 1):
            positions.append((center[0] + 0.3 * (1 if i % 2 == 0 else -1), center[1] - 0.2))
        return positions
        
    def create_formation(
        self,
        formation_type: FormationType,
        center: Tuple[float, float],
        agent_count: int
    ) -> List[Tuple[AgentRole, Tuple[float, float]]]:
        formation_def = self.formations.get(formation_type)
        if not formation_def:
            return []
            
        positions = formation_def["positions"](center, agent_count)
        roles = formation_def["roles"]
        
        assignments = []
        for i, pos in enumerate(positions):
            role = roles[i % len(roles)]
            assignments.append((role, pos))
            
        return assignments


class CoordinatedPursuitAgent:
    def __init__(
        self,
        agent_id: str = "pursuit_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        pheromone_field: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        self.pheromone_field = pheromone_field or VirtualStigmergy()
        
        self.formation_manager = FormationManager()
        
        self.strategies: Dict[str, PursuitStrategy] = {}
        self.active_pursuits: Dict[str, str] = {}
        self.agent_assignments: Dict[str, AgentAssignment] = {}
        
        self.available_agents: Dict[str, Dict] = {}
        self.agent_pools: Dict[AgentRole, List[str]] = defaultdict(list)
        
        self.pursuit_history: deque = deque(maxlen=200)
        
        self.stats = {
            "total_pursuits": 0,
            "successful_pursuits": 0,
            "failed_pursuits": 0,
            "agents_deployed": 0,
            "avg_pursuit_duration": 0.0,
            "formation_changes": 0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._pursuit_monitor_loop())
        logger.info(f"CoordinatedPursuitAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        for strategy_id in list(self.active_pursuits.keys()):
            await self.cancel_pursuit(strategy_id)
            
        logger.info(f"CoordinatedPursuitAgent {self.agent_id} stopped")
        
    async def _pursuit_monitor_loop(self):
        while self._running:
            try:
                await self._evaporate_pheromones()
                await self._check_pursuit_progress()
                await self._adapt_formations()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pursuit monitor loop: {e}")
                await asyncio.sleep(5)
                
    async def _evaporate_pheromones(self):
        self.pheromone_field.evaporate(rate=0.05)
        
    async def _check_pursuit_progress(self):
        for strategy_id, target_ip in list(self.active_pursuits.items()):
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                continue
                
            phase_progress = await self._evaluate_phase_progress(strategy)
            if phase_progress >= 0.8:
                await self._advance_phase(strategy)
                
    async def _adapt_formations(self):
        for strategy_id in self.active_pursuits:
            strategy = self.strategies.get(strategy_id)
            if strategy:
                await self._check_formation_adaptation(strategy)
                
    async def _evaluate_phase_progress(self, strategy: PursuitStrategy) -> float:
        assigned = [a for a in self.agent_assignments.values() if a.agent_id in strategy.assigned_agents]
        
        if not assigned:
            return 0.0
            
        avg_effectiveness = sum(a.effectiveness for a in assigned) / len(assigned)
        return avg_effectiveness
        
    async def _advance_phase(self, strategy: PursuitStrategy):
        current_idx = strategy.phases.index(strategy.current_phase)
        
        if current_idx < len(strategy.phases) - 1:
            strategy.current_phase = strategy.phases[current_idx + 1]
            logger.info(f"Advanced pursuit {strategy.strategy_id} to phase {strategy.current_phase.value}")
            
            await self._update_agent_roles(strategy)
            
    async def _update_agent_roles(self, strategy: PursuitStrategy):
        phase_roles = {
            PursuitPhase.RECONNAISSANCE: AgentRole.SCOUT,
            PursuitPhase.POSITIONING: AgentRole.BLOCKER,
            PursuitPhase.ENGAGEMENT: AgentRole.HUNTER,
            PursuitPhase.CONTAINMENT: AgentRole.BLOCKER,
            PursuitPhase.NEUTRALIZATION: AgentRole.HUNTER,
            PursuitPhase.CLEANUP: AgentRole.SCOUT
        }
        
        primary_role = phase_roles.get(strategy.current_phase, AgentRole.HUNTER)
        
        for agent_id in strategy.assigned_agents:
            if agent_id in self.agent_assignments:
                self.agent_assignments[agent_id].role = primary_role
                
    async def _check_formation_adaptation(self, strategy: PursuitStrategy):
        hotspots = self.pheromone_field.get_hotspots("threat", threshold=0.6)
        
        if len(hotspots) > 3 and strategy.formation != FormationType.SURROUND:
            await self._change_formation(strategy, FormationType.SURROUND)
        elif len(hotspots) == 1 and strategy.formation != FormationType.PINCER:
            await self._change_formation(strategy, FormationType.PINCER)
            
    async def _change_formation(self, strategy: PursuitStrategy, new_formation: FormationType):
        old_formation = strategy.formation
        strategy.formation = new_formation
        
        center = (0.5, 0.5)
        new_assignments = self.formation_manager.create_formation(
            new_formation,
            center,
            len(strategy.assigned_agents)
        )
        
        for i, agent_id in enumerate(strategy.assigned_agents):
            if i < len(new_assignments):
                role, position = new_assignments[i]
                strategy.assigned_agents[agent_id] = role
                if agent_id in self.agent_assignments:
                    self.agent_assignments[agent_id].role = role
                    self.agent_assignments[agent_id].position = position
                    
        self.stats["formation_changes"] += 1
        logger.info(f"Changed formation for {strategy.strategy_id}: {old_formation.value} -> {new_formation.value}")
        
    def register_agent(self, agent_id: str, capabilities: List[str], initial_role: AgentRole = AgentRole.HUNTER):
        self.available_agents[agent_id] = {
            "agent_id": agent_id,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat(),
            "status": "available"
        }
        
        self.agent_pools[initial_role].append(agent_id)
        
        logger.info(f"Registered agent {agent_id} with role {initial_role.value}")
        
    def unregister_agent(self, agent_id: str):
        if agent_id in self.available_agents:
            del self.available_agents[agent_id]
            
        for role in self.agent_pools:
            if agent_id in self.agent_pools[role]:
                self.agent_pools[role].remove(agent_id)
                
        if agent_id in self.agent_assignments:
            del self.agent_assignments[agent_id]
            
    async def create_pursuit(
        self,
        target_identity: str,
        target_ips: List[str],
        formation: FormationType = FormationType.SURROUND,
        priority: int = 1
    ) -> PursuitStrategy:
        strategy_id = self._generate_strategy_id()
        
        required_agents = self.formation_manager.formations[formation]["min_agents"]
        assigned = await self._assign_agents(required_agents, formation)
        
        if len(assigned) < required_agents:
            logger.warning(f"Not enough agents for pursuit {strategy_id}")
            
        phases = [
            PursuitPhase.RECONNAISSANCE,
            PursuitPhase.POSITIONING,
            PursuitPhase.ENGAGEMENT,
            PursuitPhase.CONTAINMENT,
            PursuitPhase.NEUTRALIZATION,
            PursuitPhase.CLEANUP
        ]
        
        strategy = PursuitStrategy(
            strategy_id=strategy_id,
            formation=formation,
            target_identity=target_identity,
            target_ips=target_ips,
            assigned_agents=assigned,
            phases=phases,
            current_phase=PursuitPhase.RECONNAISSANCE,
            created_at=datetime.now(),
            estimated_duration=3600,
            priority=priority
        )
        
        self.strategies[strategy_id] = strategy
        self.stats["total_pursuits"] += 1
        
        await self._deploy_agents(strategy)
        
        for ip in target_ips:
            self.pheromone_field.deposit_pheromone((0.5, 0.5), "target", 0.8)
            
        logger.info(f"Created pursuit {strategy_id} for target {target_identity}")
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "pursuit_created",
                strategy.to_dict()
            )
            
        return strategy
        
    async def _assign_agents(
        self,
        count: int,
        formation: FormationType
    ) -> Dict[str, AgentRole]:
        assigned = {}
        
        formation_def = self.formation_manager.formations.get(formation)
        if not formation_def:
            return assigned
            
        required_roles = formation_def["roles"]
        
        for i, role in enumerate(required_roles[:count]):
            if self.agent_pools[role]:
                agent_id = self.agent_pools[role].pop(0)
                assigned[agent_id] = role
                
                self.agent_assignments[agent_id] = AgentAssignment(
                    agent_id=agent_id,
                    role=role,
                    position=(0.5, 0.5),
                    target_zone=None,
                    status="assigned",
                    last_action=None,
                    effectiveness=0.5
                )
                
        return assigned
        
    async def _deploy_agents(self, strategy: PursuitStrategy):
        center = (0.5, 0.5)
        
        assignments = self.formation_manager.create_formation(
            strategy.formation,
            center,
            len(strategy.assigned_agents)
        )
        
        for i, (agent_id, role) in enumerate(strategy.assigned_agents.items()):
            if i < len(assignments):
                _, position = assignments[i]
                
                if agent_id in self.agent_assignments:
                    self.agent_assignments[agent_id].position = position
                    self.agent_assignments[agent_id].status = "deployed"
                    
                self.available_agents[agent_id]["status"] = "deployed"
                
        self.stats["agents_deployed"] += len(strategy.assigned_agents)
        
        logger.info(f"Deployed {len(strategy.assigned_agents)} agents for pursuit {strategy.strategy_id}")
        
    async def update_agent_position(
        self,
        agent_id: str,
        position: Tuple[float, float],
        action: Optional[str] = None
    ):
        if agent_id not in self.agent_assignments:
            return
            
        assignment = self.agent_assignments[agent_id]
        assignment.position = position
        assignment.last_action = action
        
        if assignment.role == AgentRole.SCOUT:
            self.pheromone_field.deposit_pheromone(position, "path", 0.3)
        elif assignment.role == AgentRole.HUNTER:
            self.pheromone_field.deposit_pheromone(position, "threat", 0.5)
        elif assignment.role == AgentRole.BLOCKER:
            self.pheromone_field.deposit_pheromone(position, "avoid", 0.4)
            
    async def report_target_sighting(
        self,
        agent_id: str,
        target_position: Tuple[float, float],
        confidence: float
    ):
        self.pheromone_field.deposit_pheromone(target_position, "target", confidence * 0.8)
        
        if agent_id in self.agent_assignments:
            self.agent_assignments[agent_id].effectiveness = min(
                self.agent_assignments[agent_id].effectiveness + 0.1,
                1.0
            )
            
    async def complete_pursuit(self, strategy_id: str, success: bool) -> bool:
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return False
            
        for agent_id in strategy.assigned_agents:
            if agent_id in self.agent_assignments:
                role = self.agent_assignments[agent_id].role
                self.agent_pools[role].append(agent_id)
                self.agent_assignments[agent_id].status = "available"
                
            if agent_id in self.available_agents:
                self.available_agents[agent_id]["status"] = "available"
                
        strategy.current_phase = PursuitPhase.CLEANUP
        
        self.pursuit_history.append({
            "strategy_id": strategy_id,
            "target_identity": strategy.target_identity,
            "success": success,
            "duration": (datetime.now() - strategy.created_at).total_seconds(),
            "agents_used": len(strategy.assigned_agents),
            "formation": strategy.formation.value
        })
        
        self.active_pursuits.pop(strategy_id, None)
        
        if success:
            self.stats["successful_pursuits"] += 1
        else:
            self.stats["failed_pursuits"] += 1
            
        logger.info(f"Completed pursuit {strategy_id}: success={success}")
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "pursuit_completed",
                {
                    "strategy_id": strategy_id,
                    "success": success
                }
            )
            
        return True
        
    async def cancel_pursuit(self, strategy_id: str) -> bool:
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return False
            
        for agent_id in strategy.assigned_agents:
            if agent_id in self.agent_assignments:
                role = self.agent_assignments[agent_id].role
                self.agent_pools[role].append(agent_id)
                self.agent_assignments[agent_id].status = "available"
                
            if agent_id in self.available_agents:
                self.available_agents[agent_id]["status"] = "available"
                
        self.active_pursuits.pop(strategy_id, None)
        
        logger.info(f"Cancelled pursuit {strategy_id}")
        
        return True
        
    async def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        strategy = self.strategies.get(strategy_id)
        return strategy.to_dict() if strategy else None
        
    async def get_active_pursuits(self) -> List[Dict]:
        return [
            self.strategies[sid].to_dict()
            for sid in self.active_pursuits.keys()
            if sid in self.strategies
        ]
        
    async def get_agent_assignments(self) -> Dict[str, Dict]:
        return {
            aid: a.to_dict()
            for aid, a in self.agent_assignments.items()
        }
        
    async def get_pheromone_state(self) -> Dict:
        return {
            "hotspots": {
                "threat": self.pheromone_field.get_hotspots("threat"),
                "target": self.pheromone_field.get_hotspots("target"),
                "path": self.pheromone_field.get_hotspots("path")
            },
            "deposit_count": len(self.pheromone_field.deposit_history)
        }
        
    def _generate_strategy_id(self) -> str:
        return f"pursuit_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "active_pursuits": len(self.active_pursuits),
            "available_agents": len(self.available_agents),
            "assigned_agents": len(self.agent_assignments)
        }
