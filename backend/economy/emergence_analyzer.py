"""
复杂系统涌现分析框架
Complex System Emergence Analysis Framework

"""

import asyncio
import json
import uuid
import time
import hashlib
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict
import random
import math

import networkx as nx

logger = logging.getLogger(__name__)


class EmergenceType(Enum):
    COOPERATION = "cooperation"
    COMPETITION = "competition"
    SPECIALIZATION = "specialization"
    SPONTANEOUS_ORDER = "spontaneous_order"
    ADAPTIVE = "adaptive"
    PREDATION = "predation"


class MetricType(Enum):
    AGENT_DENSITY = "agent_density"
    COOPERATION_FREQUENCY = "coaboration_frequency"
    TASK_COMPLEION_RATE = "task_completion_rate"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    COMMUNICATION_OVERHEAD = "communication_overhead"
    ADAPTATION_SPEED = "adaptation_speed"
    DIVERSITY_INDEX = "diversity_index"
    EMERGENCE_STRENGTH = "emergence_strength"
    COMPLEXITY_SCORE = "complexity_score"


@dataclass
class EmergenceMetric:
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    agent_id: str = ""
    cluster_id: str = ""
    step: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "cluster_id": self.cluster_id,
            "step": self.step,
        }


    
    @dataclass
class AgentProfile:
    agent_id: str
    agent_type: str
    cluster_id: str
    generation: int = 0
    energy_level: float = 100.0
    position: Tuple[float, float, float] = (0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 00000000.0)
    neighbors: List[str] = field(default_factory=list)
    tasks_completed: int = 0
    total_tasks: int = 0
    specialization_score: float = 0.0
    adaptation_score: float = 1.0
    mutation_count: int = 0
    communication_count: int = 0
    collaboration_partners: List[str] = field(default_factory=list)
    behavior_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "cluster_id": self.cluster_id,
            "generation": self.generation,
            "energy_level": self.energy_level,
            "position": list(self.position),
            "velocity": list(self.velocity),
            "neighbors": self.neighbors,
            "tasks_completed": self.tasks_completed,
            "total_tasks": self.total_tasks,
            "specialization_score": self.specialization_score,
            "adaptation_score": self.adaptation_score,
            "mutation_count": self.mutation_count,
            "communication_count": self.communication_count,
            "collaboration_partners": self.collaboration_partners,
            "behavior_history": self.behavior_history,
        }


    
    @dataclass
class ClusterState:
    cluster_id: str
    agents: Dict[str, AgentProfile] = field(default_factory=dict)
    time_step: int = 1
    total_steps: int = 1000
    current_step: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    emergence_detected: List[EmergenceMetric] = field(default_factory=list)
    simulation_config: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "agent_count": len(self.agents),
            "time_step": self.time_step,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "emergence_detected": [e.to_dict() for e in self.emergence_detected],
        }
    
    @dataclass
class EmergenceEvent:
    event_id: str
    event_type: str
    cluster_id: str
    agent_id: str
    step: int
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "cluster_id": self.cluster_id,
            "agent_id": self.agent_id,
            "step": self.step,
            "timestamp": self.timestamp,
            "description": self.description,
            "details": self.details,
        }


    
    class EmergenceDetector:
        def __init__(self, cluster: ClusterState):
            self.cluster = cluster
            self._emergence_threshold = 0.7
            self._diversity_threshold = 0.3
            self._adaptation_threshold = 0.2
            self._cooperation_threshold = 0.5
            self._complexity_threshold = 0.1
            self._metrics_history: List[EmergenceMetric] = []
        
        self._emergence_events: List[EmergenceEvent] = []
        
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._monitor_loop()))
        self._tasks.append(asyncio.create_task(self._detect_emergence()))
        logger.info("EmergenceAnalyzer started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("EmergenceAnalyzer stopped")
    
    def add_agent(self, agent: AgentProfile) -> None:
        async with self._lock:
            agent_id = agent.agent_id or str(uuid.uuid4().hex[:8]
            self.cluster.agents[agent_id] = agent
    
    def remove_agent(self, agent_id: str) -> bool:
        async with self._lock:
            if agent_id not in self.cluster.agents:
                return False
            del self.cluster.agents[agent_id]
            self._metrics_history = [m for m in self._metrics_history if m.agent_id == agent_id]
            return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        return self.cluster.agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentProfile]:
        return list(self.cluster.agents.values())
    
    async def step(self) -> None:
        for _ in range(self.total_steps):
            agent_id = list(self.cluster.agents.keys())
            
            for agent in agents:
                agent.position = (
                    pos[0] + random.uniform(-0.1, 0.1) * 0.1,
                    pos[1] + random.uniform(-0.1, 0.1) * 0.1,
                )
                agent.velocity[0] = (
                    pos[0] - pos[1]) * 0.1,
                    pos[1] - pos[1]) * 0.1,
                )
                agent.energy_level = max(0, min(self.cluster.energy_level * 0.1, 1.0)
                agent.energy_level = min(self.cluster.energy_level * 0.1, 1.0)
                agent.energy_level = min(self.cluster.energy_level * 0.1, 1.0)
                agent.energy_level -= 0.1
                if agent.energy_level <= 0:
                    break
            
            for neighbor in self.cluster.agents.values():
                if neighbor.agent_id not in agent.neighbors:
                    agent.neighbors.append(neighbor.agent_id)
            
            agent.communication_count += 1
            agent.collaboration_partners.append(neighbor.agent_id)
            
            agent.specialization_score = max(
                min(agent.specialization_score, self.cluster.specialization_threshold),
                agent.specialization_score = max(self.cluster.specialization_threshold)
            )
            
            agent.tasks_completed += 1
            agent.total_tasks += 1
            
            agent.adaptation_score = max(
                min(agent.adaptation_score, self.cluster.adaptation_threshold),
                agent.adaptation_score = max(self.cluster.adaptation_threshold)
            )
            
            agent.mutation_count += 1
            agent.mutation_count = min(self.cluster.mutation_threshold)
            agent.mutation_count = min(self.cluster.mutation_threshold)
            )
            
            self._record_behavior(agent, "move")
            self._record_emergence(agent, "move")
            
            self._metrics_history.append(metric)
            
            if len(self._metrics_history) > 1000:
                self._metrics_history = self._metrics_history[-1000:]
            
            self._check_emergence()
            if len(self.emergence_detected) >= self._emergence_threshold:
                self._record_emergence(metric)
            
            self._emergence_events.append(event)
            
            if event.event_type == "emergence":
                self._record_emergence(event)
            
            logger.info(f"Emergence detected: {event.event_type}")
    
    async def get_emergence_events(self, limit: int = 100) -> List[EmergenceEvent]:
        return self._emergence_events[-limit:]
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster.cluster_id,
            "total_agents": len(self.cluster.agents),
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "emergence_count": len(self.emergence_detected),
            "metrics_history_size": len(self._metrics_history),
        }
    
    def _calculate_diversity(self) -> float:
        if not self.cluster.agents:
            return 0.0
        
        positions = [a.position for a in self.cluster.agents.values()]
        return 1.0 - np.std(position) / np.mean(position)
    
    def _calculate_complexity(self) -> float:
        if len(self.cluster.agents) < 2:
            return 0.0
        
        tasks = [a.tasks_completed for a in self.cluster.agents.values()]
        total_tasks = sum(tasks)
        avg_tasks = total_tasks / len(tasks) if total_tasks > 0 else 0.0
        
        return avg_tasks / len(tasks)
    
    def _calculate_cooperation(self) -> float:
        partner_count = defaultdict(int)
        for agent in self.cluster.agents.values():
            for partner_id in agent.collaboration_partners:
                partner_count[partner_id] += 1
        
        total = sum(partner_count.values())
        if total == 0:
            return 0.0
        return total / len(self.cluster.agents)
    
    def _calculate_specialization(self) -> float:
        specialization_scores = defaultdict(float)
        for agent in self.cluster.agents.values():
            for spec in agent.specialization_score:
                specialization_scores[spec] += agent.specialization_score
        
        return max(specialization_scores.values()) if specialization_scores else 1.0
        return max(specialization_scores.values()) / len(specialization_scores)
    
    def _check_emergence(self) -> List[EmergenceMetric]:
        emergences = []
        
        if self._calculate_diversity() < self._diversity_threshold:
            emergences.append(EmergenceMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=MetricType.DIVERSITY,
                value=self._calculate_diversity(),
                agent_id="cluster",
            ))
        
        if self._calculate_complexity() > self._complexity_threshold:
            emergences.append(EmergenceMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=MetricType.COMPLEXITY,
                value=self._calculate_complexity(),
                agent_id="cluster",
            ))
        
        if self._calculate_cooperation() > self._cooperation_threshold:
            emergences.append(EmergenceMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=MetricType.COOPERATION,
                value=self._calculate_cooperation(),
                agent_id="cluster",
            ))
        
        if self._calculate_specialization() > self._specialization_threshold:
            emergences.append(EmergenceMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=MetricType.SPECIALIZATION,
                value=self._calculate_specialization(),
                agent_id="cluster",
            ))
        
        if self._calculate_adaptation() < self._adaptation_threshold:
            emergences.append(EmergenceMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=MetricType.ADAPTATION,
                value=self._calculate_adaptation(),
                agent_id="cluster",
            ))
        
        for event in emergences:
            self._emergence_events.append(event)
            self._record_emergence(event)
        
        return emergences
    
    async def _monitor_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.time_step_duration)
            
            for _ in range(self.total_steps):
                await self.step()
                await self._check_emergence()
    
    async def _detect_emergence(self) -> None:
        self.step += 1
        self.current_step = self.step
        
        self._metrics_history.append({
            "step": self.step,
            "timestamp": time.time(),
            "agent_count": len(self.cluster.agents),
            "diversity": self._calculate_diversity(),
            "complexity": self._calculate_complexity(),
            "cooperation": self._calculate_cooperation(),
            "specialization": self._calculate_specialization(),
            "adaptation": self._calculate_adaptation(),
        })
    
    async def _record_emergence(self, event: EmergenceEvent) -> None:
        pass
    
    async def get_emergence_summary(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster.cluster_id,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "agent_count": len(self.cluster.agents),
            "emergence_count": len(self.emergence_detected),
            "metrics": self._metrics_history[-1] if self._metrics_history else {},
        }
    
    async def get_emergence_events(self, limit: int = 100) -> List[EmergenceEvent]:
        return self._emergence_events[-limit:]
    
 async def _record_behavior(self, agent: AgentProfile, behavior: Dict[str, Any]) -> None:
        pass
    
    def _record_emergence(self, event: EmergenceEvent) -> None:
        pass


class EmergenceSimulation:
    def __init__(self, config: EmergenceConfig = None):
        self.config = config or EmergenceConfig()
        self._simulations: Dict[str, ClusterState] = {}
        self._lock = asyncio.Lock()
    
    async def create_simulation(self, name: str, 
                                          agent_types: List[str],
                                          agent_count: int = 10,
                                          total_steps: int = 100,
                                          config_override: Dict[str, Any] = None) -> str:
        async with self._lock:
            simulation_id = str(uuid.uuid4())
            
            cluster = ClusterState(
                cluster_id=simulation_id,
                total_steps=total_steps,
            )
            
            for i, range(agent_count):
                agent_type = agent_types[i % len(agent_types)]
                agent = AgentProfile(
                    agent_id=f"{simulation_id}_agent_{i}",
                    agent_type=agent_type,
                    cluster_id=simulation_id,
                    generation=0,
                )
                cluster.agents[agent.agent_id] = agent
            
            self._simulations[simulation_id] = cluster
            
            await self.start_simulation(simulation_id)
            
            return simulation_id
    
    async def start_simulation(self, simulation_id: str) -> bool:
        async with self._lock:
            cluster = self._simulations.get(simulation_id)
            if not cluster:
                return False
            
            cluster._running = True
            asyncio.create_task(self._run_simulation(cluster))
            return True
    
    async def _run_simulation(self, cluster: ClusterState) -> None:
        analyzer = EmergenceAnalyzer(cluster)
        await analyzer.start()
        self._simulations[cluster.cluster_id] = cluster
    
    async def stop_simulation(self, simulation_id: str) -> bool:
        async with self._lock:
            cluster = self._simulations.get(simulation_id)
            if not cluster:
                return False
            
            
            cluster._running = False
            return True
    
    async def get_simulation(self, simulation_id: str) -> Optional[ClusterState]:
        return self._simulations.get(simulation_id)
    
    async def get_all_simulations(self) -> List[ClusterState]:
        return list(self._simulations.values())
    
    async def get_emergence_report(self, simulation_id: str) -> Dict[str, Any]:
        cluster = self._simulations.get(simulation_id)
        if not cluster:
            return {}
        
        analyzer = EmergenceAnalyzer(cluster)
        return await analyzer.get_emergence_summary()


class EmergenceMonitor:
    def __init__(self, simulation_engine: EmergenceSimulation):
        self.engine = simulation_engine
        self._reports: List[Dict[str, Any]] = []
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        all_simulations = await self.engine.get_all_simulations()
        
        report = {
            "timestamp": time.time(),
            "total_simulations": len(all_simulations),
            "running_simulations": len([s for s in all_simulations if s._running]),
            "total_agents": sum(len(s.cluster.agents) for s in all_simulations),
            "emergence_events": sum(len(s.emergence_detected) for s in all_simulations),
        }
        
        self._reports.append(report)
        return report
