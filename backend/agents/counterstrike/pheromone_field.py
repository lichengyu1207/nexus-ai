"""
虚拟信息素场
Pheromone Field

通过环境间接通信，引导智能体行动
支持威胁信息素、目标信息素、路径信息素
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import math
import structlog

logger = structlog.get_logger()


class PheromoneType(Enum):
    THREAT = "threat"
    TARGET = "target"
    PATH = "path"
    AVOID = "avoid"
    COOPERATE = "cooperate"
    DANGER = "danger"


@dataclass
class Pheromone:
    pheromone_id: str
    pheromone_type: PheromoneType
    position: Tuple[float, float]
    strength: float
    deposited_at: datetime
    deposited_by: str
    decay_rate: float
    diffusion_radius: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "pheromone_id": self.pheromone_id,
            "pheromone_type": self.pheromone_type.value,
            "position": self.position,
            "strength": self.strength,
            "deposited_at": self.deposited_at.isoformat(),
            "deposited_by": self.deposited_by,
            "decay_rate": self.decay_rate,
            "diffusion_radius": self.diffusion_radius,
            "metadata": self.metadata
        }


class SpatialGrid:
    def __init__(self, width: int = 100, height: int = 100, cell_size: float = 0.1):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], Dict[PheromoneType, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        
    def to_grid_coords(self, position: Tuple[float, float]) -> Tuple[int, int]:
        return (
            int(position[0] / self.cell_size),
            int(position[1] / self.cell_size)
        )
        
    def to_world_coords(self, grid_pos: Tuple[int, int]) -> Tuple[float, float]:
        return (
            grid_pos[0] * self.cell_size,
            grid_pos[1] * self.cell_size
        )
        
    def deposit(self, position: Tuple[float, float], ptype: PheromoneType, strength: float):
        grid_pos = self.to_grid_coords(position)
        current = self.grid[grid_pos][ptype]
        self.grid[grid_pos][ptype] = min(current + strength, 1.0)
        
    def read(self, position: Tuple[float, float], ptype: PheromoneType) -> float:
        grid_pos = self.to_grid_coords(position)
        return self.grid[grid_pos][ptype]
        
    def read_neighborhood(
        self,
        position: Tuple[float, float],
        radius: int = 3
    ) -> Dict[PheromoneType, float]:
        grid_pos = self.to_grid_coords(position)
        totals = defaultdict(float)
        counts = defaultdict(int)
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                neighbor = (grid_pos[0] + dx, grid_pos[1] + dy)
                for ptype in PheromoneType:
                    value = self.grid[neighbor][ptype]
                    if value > 0:
                        distance = math.sqrt(dx * dx + dy * dy)
                        weight = 1.0 / (1.0 + distance)
                        totals[ptype] += value * weight
                        counts[ptype] += weight
                        
        return {
            ptype: totals[ptype] / counts[ptype] if counts[ptype] > 0 else 0.0
            for ptype in PheromoneType
        }
        
    def get_gradient(
        self,
        position: Tuple[float, float],
        ptype: PheromoneType
    ) -> Tuple[float, float]:
        grid_pos = self.to_grid_coords(position)
        
        dx = (
            self.grid[(grid_pos[0] + 1, grid_pos[1])][ptype] -
            self.grid[(grid_pos[0] - 1, grid_pos[1])][ptype]
        ) / 2
        
        dy = (
            self.grid[(grid_pos[0], grid_pos[1] + 1)][ptype] -
            self.grid[(grid_pos[0], grid_pos[1] - 1)][ptype]
        ) / 2
        
        return (dx, dy)
        
    def evaporate(self, rate: float = 0.1):
        for pos in list(self.grid.keys()):
            for ptype in list(self.grid[pos].keys()):
                self.grid[pos][ptype] *= (1 - rate)
                if self.grid[pos][ptype] < 0.01:
                    del self.grid[pos][ptype]
                    
    def diffuse(self, diffusion_rate: float = 0.1):
        new_grid: Dict[Tuple[int, int], Dict[PheromoneType, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        
        for pos, types in self.grid.items():
            for ptype, strength in types.items():
                keep = strength * (1 - diffusion_rate)
                spread = strength * diffusion_rate / 4
                
                new_grid[pos][ptype] += keep
                
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    neighbor = (pos[0] + dx, pos[1] + dy)
                    new_grid[neighbor][ptype] += spread
                    
        self.grid = new_grid


class PheromoneField:
    def __init__(
        self,
        field_id: str = "pheromone_field_001",
        communication_bus: Optional[Any] = None
    ):
        self.field_id = field_id
        self.communication_bus = communication_bus
        
        self.grid = SpatialGrid()
        self.pheromones: Dict[str, Pheromone] = {}
        self.position_index: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        
        self.deposit_history: deque = deque(maxlen=5000)
        
        self.default_decay_rates = {
            PheromoneType.THREAT: 0.05,
            PheromoneType.TARGET: 0.02,
            PheromoneType.PATH: 0.1,
            PheromoneType.AVOID: 0.08,
            PheromoneType.COOPERATE: 0.03,
            PheromoneType.DANGER: 0.15
        }
        
        self.stats = {
            "total_deposits": 0,
            "total_evaporations": 0,
            "total_diffusions": 0,
            "active_pheromones": 0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._field_loop())
        logger.info(f"PheromoneField {self.field_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"PheromoneField {self.field_id} stopped")
        
    async def _field_loop(self):
        while self._running:
            try:
                await self._evaporate_and_diffuse()
                await self._cleanup_weak_pheromones()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in field loop: {e}")
                await asyncio.sleep(5)
                
    async def _evaporate_and_diffuse(self):
        self.grid.evaporate(rate=0.05)
        self.grid.diffuse(diffusion_rate=0.02)
        
        self.stats["total_evaporations"] += 1
        self.stats["total_diffusions"] += 1
        
    async def _cleanup_weak_pheromones(self):
        to_remove = []
        
        for pheromone_id, pheromone in self.pheromones.items():
            age = (datetime.now() - pheromone.deposited_at).total_seconds()
            decayed_strength = pheromone.strength * math.exp(
                -pheromone.decay_rate * age
            )
            
            if decayed_strength < 0.01:
                to_remove.append(pheromone_id)
                
        for pheromone_id in to_remove:
            await self.remove_pheromone(pheromone_id)
            
    async def deposit(
        self,
        pheromone_type: PheromoneType,
        position: Tuple[float, float],
        strength: float,
        deposited_by: str,
        diffusion_radius: float = 0.1,
        metadata: Optional[Dict] = None
    ) -> Pheromone:
        pheromone_id = self._generate_pheromone_id()
        
        decay_rate = self.default_decay_rates.get(pheromone_type, 0.05)
        
        pheromone = Pheromone(
            pheromone_id=pheromone_id,
            pheromone_type=pheromone_type,
            position=position,
            strength=strength,
            deposited_at=datetime.now(),
            deposited_by=deposited_by,
            decay_rate=decay_rate,
            diffusion_radius=diffusion_radius,
            metadata=metadata or {}
        )
        
        self.pheromones[pheromone_id] = pheromone
        
        grid_pos = self.grid.to_grid_coords(position)
        self.position_index[grid_pos].add(pheromone_id)
        
        self.grid.deposit(position, pheromone_type, strength)
        
        self._diffuse_pheromone(position, pheromone_type, strength, diffusion_radius)
        
        self.deposit_history.append({
            "pheromone_id": pheromone_id,
            "type": pheromone_type.value,
            "position": position,
            "strength": strength,
            "deposited_by": deposited_by,
            "timestamp": datetime.now().isoformat()
        })
        
        self.stats["total_deposits"] += 1
        self.stats["active_pheromones"] = len(self.pheromones)
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "pheromone_deposited",
                pheromone.to_dict()
            )
            
        return pheromone
        
    def _diffuse_pheromone(
        self,
        position: Tuple[float, float],
        ptype: PheromoneType,
        strength: float,
        radius: float
    ):
        grid_radius = int(radius / self.grid.cell_size)
        center = self.grid.to_grid_coords(position)
        
        for dx in range(-grid_radius, grid_radius + 1):
            for dy in range(-grid_radius, grid_radius + 1):
                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= grid_radius and distance > 0:
                    falloff = 1.0 - (distance / (grid_radius + 1))
                    diffused_strength = strength * falloff * 0.5
                    
                    neighbor = (center[0] + dx, center[1] + dy)
                    current = self.grid.grid[neighbor][ptype]
                    self.grid.grid[neighbor][ptype] = min(current + diffused_strength, 1.0)
                    
    async def remove_pheromone(self, pheromone_id: str) -> bool:
        if pheromone_id not in self.pheromones:
            return False
            
        pheromone = self.pheromones.pop(pheromone_id)
        
        grid_pos = self.grid.to_grid_coords(pheromone.position)
        self.position_index[grid_pos].discard(pheromone_id)
        
        self.stats["active_pheromones"] = len(self.pheromones)
        
        return True
        
    def sense(
        self,
        position: Tuple[float, float],
        radius: int = 3
    ) -> Dict[PheromoneType, float]:
        return self.grid.read_neighborhood(position, radius)
        
    def sense_type(
        self,
        position: Tuple[float, float],
        pheromone_type: PheromoneType
    ) -> float:
        return self.grid.read(position, pheromone_type)
        
    def follow_gradient(
        self,
        position: Tuple[float, float],
        pheromone_type: PheromoneType
    ) -> Tuple[float, float]:
        gradient = self.grid.get_gradient(position, pheromone_type)
        
        magnitude = math.sqrt(gradient[0] ** 2 + gradient[1] ** 2)
        if magnitude > 0:
            return (gradient[0] / magnitude, gradient[1] / magnitude)
        return (0.0, 0.0)
        
    def find_strongest(
        self,
        position: Tuple[float, float],
        pheromone_type: PheromoneType,
        search_radius: int = 10
    ) -> Optional[Tuple[float, float]]:
        grid_pos = self.grid.to_grid_coords(position)
        
        strongest_pos = None
        strongest_value = 0
        
        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                neighbor = (grid_pos[0] + dx, grid_pos[1] + dy)
                value = self.grid.grid[neighbor][pheromone_type]
                
                if value > strongest_value:
                    strongest_value = value
                    strongest_pos = neighbor
                    
        if strongest_pos:
            return self.grid.to_world_coords(strongest_pos)
        return None
        
    def get_pheromones_in_radius(
        self,
        position: Tuple[float, float],
        radius: float
    ) -> List[Pheromone]:
        grid_pos = self.grid.to_grid_coords(position)
        grid_radius = int(radius / self.grid.cell_size)
        
        result = []
        
        for dx in range(-grid_radius, grid_radius + 1):
            for dy in range(-grid_radius, grid_radius + 1):
                neighbor = (grid_pos[0] + dx, grid_pos[1] + dy)
                
                for pheromone_id in self.position_index.get(neighbor, set()):
                    pheromone = self.pheromones.get(pheromone_id)
                    if pheromone:
                        distance = math.sqrt(
                            (pheromone.position[0] - position[0]) ** 2 +
                            (pheromone.position[1] - position[1]) ** 2
                        )
                        if distance <= radius:
                            result.append(pheromone)
                            
        return result
        
    async def get_field_state(self) -> Dict:
        hotspots = {}
        for ptype in PheromoneType:
            positions = []
            for pos, types in self.grid.grid.items():
                if types[ptype] > 0.3:
                    positions.append({
                        "position": self.grid.to_world_coords(pos),
                        "strength": types[ptype]
                    })
            hotspots[ptype.value] = positions
            
        return {
            "field_id": self.field_id,
            "active_pheromones": len(self.pheromones),
            "hotspots": hotspots,
            "stats": self.stats
        }
        
    def _generate_pheromone_id(self) -> str:
        return f"ph_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return self.stats


from collections import deque
