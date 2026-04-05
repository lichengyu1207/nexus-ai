"""
信息素通信系统模块
Pheromone Communication System Module

实现威胁信息素、信息素衰减、群体防御协调等功能
"""

import asyncio
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


class PheromoneType(Enum):
    THREAT = "threat"
    DANGER = "danger"
    WARNING = "warning"
    SAFE = "safe"
    RESOURCE = "resource"
    COOPERATION = "cooperation"


class PheromoneIntensity(Enum):
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    CRITICAL = 4


@dataclass
class PheromoneMessage:
    message_id: str
    pheromone_type: PheromoneType
    source_ip: str
    attack_type: str
    intensity: float
    position: str
    timestamp: datetime
    ttl: int
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "pheromone_type": self.pheromone_type.value,
            "source_ip": self.source_ip,
            "attack_type": self.attack_type,
            "intensity": self.intensity,
            "position": self.position,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata,
        }
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


@dataclass
class ThreatPheromone:
    pheromone_id: str
    threat_type: str
    source_ip: str
    target_nodes: List[str]
    intensity: float
    spread_radius: int
    created_at: datetime
    last_updated: datetime
    decay_rate: float
    reinforcement_count: int
    alert_level: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pheromone_id": self.pheromone_id,
            "threat_type": self.threat_type,
            "source_ip": self.source_ip,
            "target_nodes": self.target_nodes,
            "intensity": self.intensity,
            "spread_radius": self.spread_radius,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "decay_rate": self.decay_rate,
            "reinforcement_count": self.reinforcement_count,
            "alert_level": self.alert_level,
        }
    
    def decay(self) -> float:
        self.intensity *= (1 - self.decay_rate)
        self.last_updated = datetime.now()
        return self.intensity
    
    def reinforce(self, amount: float = 0.1):
        self.intensity = min(1.0, self.intensity + amount)
        self.reinforcement_count += 1
        self.last_updated = datetime.now()


class PheromoneDecayManager:
    """信息素衰减管理器"""
    
    def __init__(
        self,
        default_decay_rate: float = 0.1,
        cleanup_interval: int = 300,
        min_intensity: float = 0.05
    ):
        self.default_decay_rate = default_decay_rate
        self.cleanup_interval = cleanup_interval
        self.min_intensity = min_intensity
        
        self.pheromones: Dict[str, ThreatPheromone] = {}
        self.messages: Dict[str, PheromoneMessage] = {}
        
        self._lock = threading.Lock()
        
        self._running = False
        self._decay_task = None
        
        self.stats = {
            "total_decay_cycles": 0,
            "pheromones_decayed": 0,
            "pheromones_removed": 0,
            "messages_expired": 0,
        }
    
    async def start(self):
        self._running = True
        self._decay_task = asyncio.create_task(self._decay_loop())
    
    def stop(self):
        self._running = False
        if self._decay_task:
            self._decay_task.cancel()
    
    async def _decay_loop(self):
        while self._running:
            try:
                await self._run_decay()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Decay loop error: {e}")
                await asyncio.sleep(60)
    
    async def _run_decay(self):
        self.stats["total_decay_cycles"] += 1
        
        with self._lock:
            to_remove = []
            
            for pheromone_id, pheromone in self.pheromones.items():
                new_intensity = pheromone.decay()
                self.stats["pheromones_decayed"] += 1
                
                if new_intensity < self.min_intensity:
                    to_remove.append(pheromone_id)
            
            for pheromone_id in to_remove:
                del self.pheromones[pheromone_id]
                self.stats["pheromones_removed"] += 1
            
            expired_messages = [
                mid for mid, msg in self.messages.items()
                if msg.is_expired()
            ]
            
            for mid in expired_messages:
                del self.messages[mid]
                self.stats["messages_expired"] += 1
    
    def add_pheromone(self, pheromone: ThreatPheromone) -> str:
        with self._lock:
            self.pheromones[pheromone.pheromone_id] = pheromone
            return pheromone.pheromone_id
    
    def add_message(self, message: PheromoneMessage) -> str:
        with self._lock:
            self.messages[message.message_id] = message
            return message.message_id
    
    def get_active_pheromones(
        self,
        min_intensity: float = None
    ) -> List[ThreatPheromone]:
        min_int = min_intensity or self.min_intensity
        
        with self._lock:
            return [
                p for p in self.pheromones.values()
                if p.intensity >= min_int
            ]
    
    def get_active_messages(
        self,
        pheromone_type: PheromoneType = None
    ) -> List[PheromoneMessage]:
        with self._lock:
            messages = [
                m for m in self.messages.values()
                if not m.is_expired()
            ]
            
            if pheromone_type:
                messages = [
                    m for m in messages
                    if m.pheromone_type == pheromone_type
                ]
            
            return messages
    
    def reinforce_pheromone(
        self,
        pheromone_id: str,
        amount: float = 0.1
    ) -> bool:
        with self._lock:
            if pheromone_id in self.pheromones:
                self.pheromones[pheromone_id].reinforce(amount)
                return True
            return False
    
    def get_intensity_by_source(self, source_ip: str) -> float:
        with self._lock:
            total_intensity = 0.0
            for pheromone in self.pheromones.values():
                if pheromone.source_ip == source_ip:
                    total_intensity += pheromone.intensity
            return total_intensity


class PheromoneField:
    """信息素场 - 模拟蚁群信息素机制"""
    
    def __init__(
        self,
        decay_manager: PheromoneDecayManager,
        spread_factor: float = 0.8,
        aggregation_threshold: float = 0.3
    ):
        self.decay_manager = decay_manager
        self.spread_factor = spread_factor
        self.aggregation_threshold = aggregation_threshold
        
        self.field_grid: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.node_positions: Dict[str, Tuple[int, int]] = {}
        self.neighbors: Dict[str, List[str]] = defaultdict(list)
        
        self.blackboard: Dict[str, List[PheromoneMessage]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "pheromones_released": 0,
            "pheromones_spread": 0,
            "aggregations_triggered": 0,
            "collective_defenses": 0,
        }
    
    def register_node(
        self,
        node_id: str,
        position: Tuple[int, int],
        neighbors: List[str] = None
    ):
        with self._lock:
            self.node_positions[node_id] = position
            if neighbors:
                self.neighbors[node_id] = neighbors
    
    def release_threat_pheromone(
        self,
        source_ip: str,
        attack_type: str,
        intensity: float,
        position: str,
        metadata: Dict[str, Any] = None
    ) -> ThreatPheromone:
        self.stats["pheromones_released"] += 1
        
        pheromone_id = f"ph_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        alert_level = self._calculate_alert_level(intensity)
        
        pheromone = ThreatPheromone(
            pheromone_id=pheromone_id,
            threat_type=attack_type,
            source_ip=source_ip,
            target_nodes=[position],
            intensity=intensity,
            spread_radius=3,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            decay_rate=0.1,
            reinforcement_count=0,
            alert_level=alert_level,
        )
        
        self.decay_manager.add_pheromone(pheromone)
        
        message = PheromoneMessage(
            message_id=f"msg_{pheromone_id}",
            pheromone_type=PheromoneType.THREAT,
            source_ip=source_ip,
            attack_type=attack_type,
            intensity=intensity,
            position=position,
            timestamp=datetime.now(),
            ttl=300,
            expires_at=datetime.now() + timedelta(seconds=300),
            metadata=metadata or {},
        )
        
        self.decay_manager.add_message(message)
        
        with self._lock:
            self.blackboard[position].append(message)
        
        self._spread_pheromone(pheromone, position)
        
        return pheromone
    
    def _calculate_alert_level(self, intensity: float) -> int:
        if intensity >= 0.8:
            return 4
        elif intensity >= 0.6:
            return 3
        elif intensity >= 0.4:
            return 2
        else:
            return 1
    
    def _spread_pheromone(
        self,
        pheromone: ThreatPheromone,
        source_position: str
    ):
        self.stats["pheromones_spread"] += 1
        
        with self._lock:
            neighbors = self.neighbors.get(source_position, [])
            
            for neighbor in neighbors:
                spread_intensity = pheromone.intensity * self.spread_factor
                
                message = PheromoneMessage(
                    message_id=f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                    pheromone_type=PheromoneType.THREAT,
                    source_ip=pheromone.source_ip,
                    attack_type=pheromone.threat_type,
                    intensity=spread_intensity,
                    position=neighbor,
                    timestamp=datetime.now(),
                    ttl=180,
                    expires_at=datetime.now() + timedelta(seconds=180),
                    metadata={"spread_from": source_position},
                )
                
                self.blackboard[neighbor].append(message)
                self.decay_manager.add_message(message)
    
    def scan_threats(
        self,
        node_id: str,
        radius: int = 2
    ) -> List[Dict[str, Any]]:
        threats = []
        
        with self._lock:
            messages = self.blackboard.get(node_id, [])
            
            for message in messages:
                if not message.is_expired():
                    threats.append({
                        "source_ip": message.source_ip,
                        "attack_type": message.attack_type,
                        "intensity": message.intensity,
                        "position": message.position,
                        "timestamp": message.timestamp.isoformat(),
                    })
        
        return threats
    
    def get_aggregated_threats(
        self,
        min_sources: int = 2
    ) -> List[Dict[str, Any]]:
        self.stats["aggregations_triggered"] += 1
        
        source_detections: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        with self._lock:
            for node_id, messages in self.blackboard.items():
                for message in messages:
                    if not message.is_expired():
                        source_detections[message.source_ip].append({
                            "node_id": node_id,
                            "intensity": message.intensity,
                            "attack_type": message.attack_type,
                        })
        
        aggregated = []
        for source_ip, detections in source_detections.items():
            if len(detections) >= min_sources:
                total_intensity = sum(d["intensity"] for d in detections)
                avg_intensity = total_intensity / len(detections)
                
                aggregated.append({
                    "source_ip": source_ip,
                    "detection_count": len(detections),
                    "total_intensity": total_intensity,
                    "average_intensity": avg_intensity,
                    "attack_type": detections[0]["attack_type"],
                    "alert_level": self._calculate_alert_level(avg_intensity),
                })
        
        return sorted(aggregated, key=lambda x: x["total_intensity"], reverse=True)
    
    def trigger_collective_defense(
        self,
        source_ip: str,
        defense_action: str
    ) -> Dict[str, Any]:
        self.stats["collective_defenses"] += 1
        
        with self._lock:
            affected_nodes = set()
            
            for node_id, messages in self.blackboard.items():
                for message in messages:
                    if message.source_ip == source_ip and not message.is_expired():
                        affected_nodes.add(node_id)
            
            defense = {
                "defense_id": f"def_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                "source_ip": source_ip,
                "action": defense_action,
                "affected_nodes": list(affected_nodes),
                "timestamp": datetime.now().isoformat(),
                "status": "executed",
            }
            
            return defense
    
    def get_field_intensity(self, position: str) -> float:
        with self._lock:
            messages = self.blackboard.get(position, [])
            
            total_intensity = sum(
                m.intensity for m in messages
                if not m.is_expired()
            )
            
            return total_intensity
    
    def get_field_map(self) -> Dict[str, float]:
        field_map = {}
        
        with self._lock:
            for position, messages in self.blackboard.items():
                total_intensity = sum(
                    m.intensity for m in messages
                    if not m.is_expired()
                )
                if total_intensity > 0:
                    field_map[position] = total_intensity
        
        return field_map
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "pheromone_field": self.stats,
            "decay_manager": self.decay_manager.stats,
            "active_pheromones": len(self.decay_manager.pheromones),
            "active_messages": len(self.decay_manager.messages),
            "registered_nodes": len(self.node_positions),
        }
