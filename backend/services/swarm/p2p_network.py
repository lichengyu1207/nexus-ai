# -*- coding: utf-8 -*-
"""
Agent Swarm P2P通信网络模块
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from uuid import UUID, uuid4
from collections import defaultdict
import time

from .config import SwarmConfig
from .models import SwarmHeartbeat
from .agent import Agent


@dataclass
class Message:
    id: UUID = field(default_factory=uuid4)
    sender_id: UUID = field(default_factory=uuid4)
    receiver_id: Optional[UUID] = None
    message_type: str = "broadcast"
    content: Dict = field(default_factory=dict)
    ttl: int = 3
    timestamp: datetime = field(default_factory=datetime.now)
    visited: Set[UUID] = field(default_factory=set)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "sender_id": str(self.sender_id),
            "receiver_id": str(self.receiver_id) if self.receiver_id else None,
            "message_type": self.message_type,
            "content": self.content,
            "ttl": self.ttl,
            "timestamp": self.timestamp.isoformat(),
            "visited": [str(v) for v in self.visited]
        }


class P2PNetwork:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.agents: Dict[UUID, Agent] = {}
        self.topology: Dict[UUID, List[UUID]] = defaultdict(list)
        self.message_history: List[Message] = []
        self._message_handlers: Dict[str, Any] = {}
    
    def register_agent(self, agent: Agent):
        self.agents[agent.id] = agent
        self._update_topology()
    
    def unregister_agent(self, agent_id: UUID):
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._update_topology()
    
    def _update_topology(self):
        agent_list = list(self.agents.keys())
        n = len(agent_list)
        
        for i, agent_id in enumerate(agent_list):
            neighbors = []
            
            for j in range(max(0, i - 2), min(n, i + 3)):
                if i != j:
                    neighbors.append(agent_list[j])
            
            if n > 3:
                import random
                random_neighbors = random.sample(
                    [a for a in agent_list if a != agent_id and a not in neighbors],
                    min(2, n - 3)
                )
                neighbors.extend(random_neighbors)
            
            self.topology[agent_id] = neighbors
            
            if agent_id in self.agents:
                self.agents[agent_id].update_neighbors(neighbors)
    
    def get_neighbors(self, agent_id: UUID) -> List[UUID]:
        return self.topology.get(agent_id, [])
    
    def send_direct(self, from_id: UUID, to_id: UUID, content: Dict) -> bool:
        if to_id not in self.agents:
            return False
        
        message = Message(
            sender_id=from_id,
            receiver_id=to_id,
            message_type="direct",
            content=content,
            ttl=1
        )
        
        self.message_history.append(message)
        return True
    
    def broadcast(self, from_id: UUID, content: Dict, ttl: Optional[int] = None) -> int:
        ttl = ttl or self.config.flood_ttl
        
        message = Message(
            sender_id=from_id,
            message_type="broadcast",
            content=content,
            ttl=ttl,
            visited={from_id}
        )
        
        self.message_history.append(message)
        
        return self._propagate(message)
    
    def flood_limited(self, from_id: UUID, content: Dict, ttl: int) -> int:
        return self.broadcast(from_id, content, ttl)
    
    def _propagate(self, message: Message) -> int:
        if message.ttl <= 0:
            return 0
        
        neighbors = self.get_neighbors(message.sender_id)
        reachable = 0
        
        for neighbor_id in neighbors:
            if neighbor_id in message.visited:
                continue
            
            message.visited.add(neighbor_id)
            reachable += 1
        
        return reachable
    
    def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        return list(self.agents.values())
    
    def get_network_statistics(self) -> Dict:
        return {
            "total_agents": len(self.agents),
            "total_connections": sum(len(n) for n in self.topology.values()) // 2,
            "avg_neighbors": sum(len(n) for n in self.topology.values()) / len(self.topology) if self.topology else 0,
            "message_count": len(self.message_history)
        }


class HeartbeatMonitor:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.last_seen: Dict[UUID, datetime] = {}
        self.heartbeat_history: Dict[UUID, List[SwarmHeartbeat]] = defaultdict(list)
    
    def record_heartbeat(self, heartbeat: SwarmHeartbeat):
        self.last_seen[heartbeat.agent_id] = heartbeat.recorded_at
        self.heartbeat_history[heartbeat.agent_id].append(heartbeat)
        
        if len(self.heartbeat_history[heartbeat.agent_id]) > 100:
            self.heartbeat_history[heartbeat.agent_id] = self.heartbeat_history[heartbeat.agent_id][-100:]
    
    def check_health(self) -> Dict[UUID, bool]:
        now = datetime.now()
        timeout = timedelta(seconds=self.config.heartbeat_timeout_seconds)
        
        health_status = {}
        for agent_id, last_time in self.last_seen.items():
            health_status[agent_id] = (now - last_time) < timeout
        
        return health_status
    
    def detect_failures(self) -> List[UUID]:
        health = self.check_health()
        return [agent_id for agent_id, is_healthy in health.items() if not is_healthy]
    
    def get_agent_status(self, agent_id: UUID) -> Optional[Dict]:
        if agent_id not in self.last_seen:
            return None
        
        now = datetime.now()
        last = self.last_seen[agent_id]
        timeout = timedelta(seconds=self.config.heartbeat_timeout_seconds)
        
        is_healthy = (now - last) < timeout
        
        history = self.heartbeat_history.get(agent_id, [])
        
        return {
            "agent_id": str(agent_id),
            "is_healthy": is_healthy,
            "last_seen": last.isoformat(),
            "seconds_since_heartbeat": (now - last).total_seconds(),
            "recent_heartbeats": len(history)
        }
    
    def get_average_load(self) -> float:
        if not self.heartbeat_history:
            return 0.0
        
        total_load = 0
        count = 0
        
        for history in self.heartbeat_history.values():
            if history:
                total_load += history[-1].load
                count += 1
        
        return total_load / count if count > 0 else 0.0


class TaskMigrator:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.migration_history: List[Dict] = []
    
    def migrate(
        self, 
        task_id: UUID, 
        from_agent: Agent, 
        to_agent: Agent
    ) -> bool:
        if not to_agent.can_execute(
            type('Task', (), {'required_capabilities': [], 'id': task_id})()
        ):
            return False
        
        success = from_agent.migrate_task(task_id, to_agent)
        
        if success:
            to_agent.assign_task(type('Task', (), {'id': task_id, 'required_capabilities': []})())
            
            self.migration_history.append({
                "task_id": str(task_id),
                "from_agent": str(from_agent.id),
                "to_agent": str(to_agent.id),
                "timestamp": datetime.now().isoformat()
            })
        
        return success
    
    def find_replacement(
        self, 
        failed_agent: Agent, 
        available_agents: List[Agent]
    ) -> Optional[Agent]:
        if not available_agents:
            return None
        
        available = [a for a in available_agents if a.id != failed_agent.id]
        
        if not available:
            return None
        
        return min(available, key=lambda a: a.load)
    
    def get_migration_statistics(self) -> Dict:
        return {
            "total_migrations": len(self.migration_history),
            "recent_migrations": len([
                m for m in self.migration_history 
                if (datetime.now() - datetime.fromisoformat(m["timestamp"])).total_seconds() < 3600
            ])
        }
