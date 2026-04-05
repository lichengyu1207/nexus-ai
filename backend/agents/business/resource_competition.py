"""
业务资源竞争机制
Business Resource Competition

模拟有限资源下的智能体竞争
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    COMPUTE = "compute"
    DATA_ACCESS = "data_access"
    HIGH_VALUE_TASK = "high_value_task"
    USER_ATTENTION = "user_attention"
    MEMORY = "memory"
    NETWORK = "network"


class CompetitionType(Enum):
    BID = "bid"
    AUCTION = "auction"
    LOTTERY = "lottery"
    MERIT = "merit"
    HYBRID = "hybrid"


@dataclass
class CompetitionResult:
    competition_id: str
    resource_type: ResourceType
    winner_id: str
    participants: List[str]
    resource_allocated: Dict
    energy_transferred: float
    competition_type: CompetitionType
    timestamp: float
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "competition_id": self.competition_id,
            "resource_type": self.resource_type.value,
            "winner_id": self.winner_id,
            "participants": self.participants,
            "resource_allocated": self.resource_allocated,
            "energy_transferred": self.energy_transferred,
            "competition_type": self.competition_type.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ResourceCompetition:
    """
    业务资源竞争机制
    
    模拟有限资源下的智能体竞争：
    1. 资源类型：计算资源、数据访问、高价值任务、用户注意力
    2. 竞争方式：竞标、竞价、信誉分配
    3. 竞争演化：优胜者获得更多繁殖机会
    4. 防内耗：设定竞争上限
    """
    
    MAX_COMPETITION_INTENSITY = 0.8
    MIN_COMPETITION_INTENSITY = 0.2
    
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
    ):
        self.blackboard = blackboard
        self.memory_agent = memory_agent
        
        self.resources: Dict[str, Dict] = {}
        self.competition_history: deque = deque(maxlen=10000)
        self.agent_wins: Dict[str, int] = defaultdict(int)
        self.agent_losses: Dict[str, int] = defaultdict(int)
        
        self.competition_intensity = 0.5
        
        self._lock = threading.RLock()
        
        self.stats = {
            "total_competitions": 0,
            "total_energy_transferred": 0.0,
            "avg_participants": 0.0,
            "resource_utilization": 0.0,
        }
    
    def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        capacity: float,
        allocation_unit: float = 1.0,
        priority: int = 1,
    ):
        with self._lock:
            self.resources[resource_id] = {
                "resource_id": resource_id,
                "resource_type": resource_type,
                "capacity": capacity,
                "allocated": 0.0,
                "available": capacity,
                "allocation_unit": allocation_unit,
                "priority": priority,
                "allocations": {},
            }
    
    async def compete(
        self,
        resource_id: str,
        participants: List[Any],
        competition_type: CompetitionType = CompetitionType.HYBRID,
    ) -> Optional[CompetitionResult]:
        if resource_id not in self.resources:
            logger.warning(f"Resource not found: {resource_id}")
            return None
        
        resource = self.resources[resource_id]
        
        if resource["available"] <= 0:
            return None
        
        if len(participants) < 1:
            return None
        
        competition_id = f"comp_{uuid.uuid4().hex[:8]}"
        
        if competition_type == CompetitionType.BID:
            winner = await self._bid_competition(participants, resource)
        elif competition_type == CompetitionType.AUCTION:
            winner = await self._auction_competition(participants, resource)
        elif competition_type == CompetitionType.LOTTERY:
            winner = await self._lottery_competition(participants, resource)
        elif competition_type == CompetitionType.MERIT:
            winner = await self._merit_competition(participants, resource)
        else:
            winner = await self._hybrid_competition(participants, resource)
        
        if winner is None:
            return None
        
        allocation = min(
            resource["allocation_unit"],
            resource["available"]
        )
        
        with self._lock:
            resource["allocated"] += allocation
            resource["available"] -= allocation
            resource["allocations"][winner.agent_id] = allocation
        
        energy_transfer = allocation * 0.1
        
        result = CompetitionResult(
            competition_id=competition_id,
            resource_type=resource["resource_type"],
            winner_id=winner.agent_id,
            participants=[p.agent_id for p in participants],
            resource_allocated={"amount": allocation, "resource_id": resource_id},
            energy_transferred=energy_transfer,
            competition_type=competition_type,
            timestamp=time.time(),
        )
        
        with self._lock:
            self.competition_history.append(result)
            self.agent_wins[winner.agent_id] += 1
            
            for p in participants:
                if p.agent_id != winner.agent_id:
                    self.agent_losses[p.agent_id] += 1
            
            self.stats["total_competitions"] += 1
            self.stats["total_energy_transferred"] += energy_transfer
            
            old_avg = self.stats["avg_participants"]
            count = self.stats["total_competitions"]
            self.stats["avg_participants"] = (
                old_avg * (count - 1) + len(participants)
            ) / count
        
        self._adjust_competition_intensity(winner, participants)
        
        return result
    
    async def _bid_competition(
        self,
        participants: List[Any],
        resource: Dict,
    ) -> Optional[Any]:
        bids = []
        
        for agent in participants:
            bid_amount = agent.energy * random.uniform(0.1, 0.3)
            success_rate = agent.stats.get("tasks_success_rate", 0.5)
            bid_score = bid_amount * (1 + success_rate)
            
            bids.append({
                "agent": agent,
                "bid_amount": bid_amount,
                "bid_score": bid_score,
            })
        
        bids.sort(key=lambda x: x["bid_score"], reverse=True)
        
        return bids[0]["agent"] if bids else None
    
    async def _auction_competition(
        self,
        participants: List[Any],
        resource: Dict,
    ) -> Optional[Any]:
        current_bid = resource["allocation_unit"] * 0.1
        winner = None
        
        sorted_participants = sorted(
            participants,
            key=lambda p: p.energy,
            reverse=True
        )
        
        for agent in sorted_participants:
            max_bid = agent.energy * 0.3
            if max_bid > current_bid:
                current_bid = max_bid
                winner = agent
        
        return winner
    
    async def _lottery_competition(
        self,
        participants: List[Any],
        resource: Dict,
    ) -> Optional[Any]:
        tickets = []
        
        for agent in participants:
            success_rate = agent.stats.get("tasks_success_rate", 0.5)
            reputation = getattr(agent, 'reputation', 50)
            
            ticket_count = int(
                success_rate * 10 +
                reputation / 10 +
                agent.energy / 100
            )
            
            for _ in range(max(1, ticket_count)):
                tickets.append(agent)
        
        if not tickets:
            return participants[0] if participants else None
        
        return random.choice(tickets)
    
    async def _merit_competition(
        self,
        participants: List[Any],
        resource: Dict,
    ) -> Optional[Any]:
        merits = []
        
        for agent in participants:
            success_rate = agent.stats.get("tasks_success_rate", 0.5)
            tasks_completed = agent.stats.get("tasks_completed", 0)
            user_satisfaction = agent.stats.get("user_satisfaction", 0.5)
            
            merit_score = (
                success_rate * 0.4 +
                min(1.0, tasks_completed / 100) * 0.3 +
                user_satisfaction * 0.3
            )
            
            merits.append({
                "agent": agent,
                "merit_score": merit_score,
            })
        
        merits.sort(key=lambda x: x["merit_score"], reverse=True)
        
        return merits[0]["agent"] if merits else None
    
    async def _hybrid_competition(
        self,
        participants: List[Any],
        resource: Dict,
    ) -> Optional[Any]:
        scores = []
        
        for agent in participants:
            success_rate = agent.stats.get("tasks_success_rate", 0.5)
            energy_factor = min(1.0, agent.energy / 100)
            reputation = getattr(agent, 'reputation', 50) / 100
            
            merit_score = success_rate * 0.3 + reputation * 0.2
            
            bid_factor = random.uniform(0.5, 1.5)
            
            lottery_factor = random.uniform(0.8, 1.2)
            
            total_score = (
                merit_score * 0.4 +
                energy_factor * bid_factor * 0.3 +
                lottery_factor * 0.3
            )
            
            scores.append({
                "agent": agent,
                "score": total_score,
            })
        
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        return scores[0]["agent"] if scores else None
    
    def _adjust_competition_intensity(
        self,
        winner: Any,
        participants: List[Any],
    ):
        winner_energy_ratio = winner.energy / sum(p.energy for p in participants)
        
        if winner_energy_ratio > 0.5:
            self.competition_intensity = min(
                self.MAX_COMPETITION_INTENSITY,
                self.competition_intensity + 0.05
            )
        else:
            self.competition_intensity = max(
                self.MIN_COMPETITION_INTENSITY,
                self.competition_intensity - 0.02
            )
    
    def release_resource(
        self,
        resource_id: str,
        agent_id: str,
    ) -> float:
        with self._lock:
            if resource_id not in self.resources:
                return 0.0
            
            resource = self.resources[resource_id]
            
            if agent_id not in resource["allocations"]:
                return 0.0
            
            released = resource["allocations"][agent_id]
            del resource["allocations"][agent_id]
            
            resource["allocated"] -= released
            resource["available"] += released
            
            return released
    
    def get_agent_win_rate(self, agent_id: str) -> float:
        wins = self.agent_wins.get(agent_id, 0)
        losses = self.agent_losses.get(agent_id, 0)
        total = wins + losses
        
        return wins / total if total > 0 else 0.0
    
    def get_resource_status(self, resource_id: str) -> Optional[Dict]:
        return self.resources.get(resource_id)
    
    def get_all_resources(self) -> Dict[str, Dict]:
        return self.resources.copy()
    
    def get_stats(self) -> Dict:
        with self._lock:
            total_capacity = sum(r["capacity"] for r in self.resources.values())
            total_allocated = sum(r["allocated"] for r in self.resources.values())
            
            utilization = total_allocated / total_capacity if total_capacity > 0 else 0
            
            return {
                **self.stats,
                "competition_intensity": self.competition_intensity,
                "resource_utilization": utilization,
                "total_resources": len(self.resources),
                "active_allocations": sum(
                    len(r["allocations"]) for r in self.resources.values()
                ),
            }
