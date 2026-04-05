"""
业务接口适配器
Business Interface Adapter

将现有三省六部业务逻辑无缝集成到活体智能体框架
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class AgentWrapper:
    original_agent: Any
    living_agent: Any
    migration_status: MigrationStatus
    original_methods: Dict[str, Callable]
    wrapped_methods: Dict[str, Callable]
    created_at: float
    migration_completed_at: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "original_type": type(self.original_agent).__name__,
            "living_agent_id": getattr(self.living_agent, 'agent_id', 'unknown'),
            "migration_status": self.migration_status.value,
            "original_methods": list(self.original_methods.keys()),
            "wrapped_methods": list(self.wrapped_methods.keys()),
            "created_at": self.created_at,
            "migration_completed_at": self.migration_completed_at,
            "error": self.error
        }


class BusinessInterfaceAdapter:
    """
    业务接口适配器
    
    将现有三省六部业务逻辑无缝集成到活体智能体框架：
    1. 包装现有代码：将现有Agent包装为BusinessAgent子类
    2. 状态迁移：现有状态作为初始基因
    3. 平滑过渡：小流量启用，对比效果
    4. 回滚机制：一键切回旧版本
    """
    
    METHOD_MAPPING = {
        "handle_message": "execute_business",
        "process": "execute_business",
        "run": "execute_business",
        "analyze": "execute_business",
        "generate": "execute_business",
    }
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        task_market: Optional[Any] = None,
        traffic_split_ratio: float = 0.1,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.task_market = task_market
        self.traffic_split_ratio = traffic_split_ratio
        
        self.wrappers: Dict[str, AgentWrapper] = {}
        self.migration_log: deque = deque(maxlen=1000)
        
        self.rollback_snapshots: Dict[str, Dict] = {}
        
        self._lock = threading.RLock()
        
        self.stats = {
            "agents_wrapped": 0,
            "migrations_completed": 0,
            "migrations_failed": 0,
            "rollbacks": 0,
            "traffic_routed_to_living": 0,
            "traffic_routed_to_original": 0,
        }
    
    async def wrap_agent(
        self,
        original_agent: Any,
        living_agent_class: Type,
        species: str,
        role: Any,
        initial_energy: float = 100.0,
    ) -> AgentWrapper:
        agent_id = f"{species}_{uuid.uuid4().hex[:8]}"
        
        original_methods = self._extract_methods(original_agent)
        
        living_agent = living_agent_class(
            agent_id=agent_id,
            role=role,
            species=species,
            initial_energy=initial_energy,
            blackboard=self.blackboard,
            task_market=self.task_market,
            memory_agent=self.memory_agent,
        )
        
        self._migrate_state(original_agent, living_agent)
        
        wrapped_methods = self._wrap_methods(original_agent, living_agent)
        
        wrapper = AgentWrapper(
            original_agent=original_agent,
            living_agent=living_agent,
            migration_status=MigrationStatus.IN_PROGRESS,
            original_methods=original_methods,
            wrapped_methods=wrapped_methods,
            created_at=time.time(),
        )
        
        with self._lock:
            self.wrappers[agent_id] = wrapper
            self.rollback_snapshots[agent_id] = self._create_snapshot(original_agent)
            self.stats["agents_wrapped"] += 1
        
        self._log_migration(agent_id, "wrap_started", {"species": species})
        
        return wrapper
    
    def _extract_methods(self, agent: Any) -> Dict[str, Callable]:
        methods = {}
        
        for attr_name in dir(agent):
            if attr_name.startswith('_'):
                continue
            
            attr = getattr(agent, attr_name)
            if callable(attr):
                methods[attr_name] = attr
        
        return methods
    
    def _migrate_state(self, original: Any, living: Any):
        if hasattr(original, '__dict__'):
            for key, value in original.__dict__.items():
                if key.startswith('_'):
                    continue
                
                if hasattr(living, 'gene_pool') and isinstance(value, (int, float, str, bool)):
                    living.gene_pool.add_gene(type('BusinessGene', (), {
                        'gene_id': f"gene_{key}",
                        'name': key,
                        'value': value,
                        'mutation_rate': 0.1,
                        'mutation_range': (-0.1, 0.1),
                        'business_weight': 1.0
                    })())
        
        if hasattr(original, 'stats'):
            living.stats.update(original.stats)
        
        if hasattr(original, 'experience_buffer'):
            if hasattr(living, 'experience_buffer'):
                for exp in original.experience_buffer:
                    living.experience_buffer.append(exp)
    
    def _wrap_methods(self, original: Any, living: Any) -> Dict[str, Callable]:
        wrapped = {}
        
        for original_name, living_name in self.METHOD_MAPPING.items():
            if hasattr(original, original_name):
                original_method = getattr(original, original_name)
                
                async def wrapped_method(*args, _original=original_method, _living=living, **kwargs):
                    if random.random() < self.traffic_split_ratio:
                        self.stats["traffic_routed_to_living"] += 1
                        return await _living.execute_business(kwargs.get("request", {}))
                    else:
                        self.stats["traffic_routed_to_original"] += 1
                        if asyncio.iscoroutinefunction(_original):
                            return await _original(*args, **kwargs)
                        else:
                            return _original(*args, **kwargs)
                
                wrapped[original_name] = wrapped_method
        
        return wrapped
    
    def _create_snapshot(self, agent: Any) -> Dict:
        snapshot = {
            "type": type(agent).__name__,
            "state": {},
            "timestamp": time.time(),
        }
        
        if hasattr(agent, '__dict__'):
            for key, value in agent.__dict__.items():
                try:
                    json.dumps(value)
                    snapshot["state"][key] = value
                except (TypeError, ValueError):
                    snapshot["state"][key] = str(value)
        
        return snapshot
    
    def _log_migration(self, agent_id: str, event: str, details: Dict):
        log_entry = {
            "agent_id": agent_id,
            "event": event,
            "details": details,
            "timestamp": time.time(),
        }
        
        with self._lock:
            self.migration_log.append(log_entry)
    
    async def complete_migration(self, agent_id: str) -> bool:
        if agent_id not in self.wrappers:
            return False
        
        wrapper = self.wrappers[agent_id]
        
        try:
            wrapper.migration_status = MigrationStatus.COMPLETED
            wrapper.migration_completed_at = time.time()
            
            self.stats["migrations_completed"] += 1
            
            self._log_migration(agent_id, "migration_completed", {})
            
            logger.info(f"Migration completed for agent {agent_id}")
            return True
            
        except Exception as e:
            wrapper.migration_status = MigrationStatus.FAILED
            wrapper.error = str(e)
            
            self.stats["migrations_failed"] += 1
            
            self._log_migration(agent_id, "migration_failed", {"error": str(e)})
            
            logger.error(f"Migration failed for agent {agent_id}: {e}")
            return False
    
    async def rollback(self, agent_id: str) -> bool:
        if agent_id not in self.wrappers:
            return False
        
        if agent_id not in self.rollback_snapshots:
            return False
        
        wrapper = self.wrappers[agent_id]
        snapshot = self.rollback_snapshots[agent_id]
        
        try:
            original = wrapper.original_agent
            
            for key, value in snapshot["state"].items():
                if hasattr(original, key):
                    setattr(original, key, value)
            
            wrapper.migration_status = MigrationStatus.ROLLED_BACK
            
            self.stats["rollbacks"] += 1
            
            self._log_migration(agent_id, "rollback_completed", {})
            
            logger.info(f"Rollback completed for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for agent {agent_id}: {e}")
            return False
    
    def set_traffic_split(self, ratio: float):
        self.traffic_split_ratio = max(0.0, min(1.0, ratio))
        logger.info(f"Traffic split ratio set to {self.traffic_split_ratio}")
    
    def get_wrapper(self, agent_id: str) -> Optional[AgentWrapper]:
        return self.wrappers.get(agent_id)
    
    def get_living_agent(self, agent_id: str) -> Optional[Any]:
        wrapper = self.wrappers.get(agent_id)
        if wrapper:
            return wrapper.living_agent
        return None
    
    def get_original_agent(self, agent_id: str) -> Optional[Any]:
        wrapper = self.wrappers.get(agent_id)
        if wrapper:
            return wrapper.original_agent
        return None
    
    def get_migration_status(self, agent_id: str) -> Optional[MigrationStatus]:
        wrapper = self.wrappers.get(agent_id)
        if wrapper:
            return wrapper.migration_status
        return None
    
    def get_all_wrappers(self) -> Dict[str, AgentWrapper]:
        return dict(self.wrappers)
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "total_wrappers": len(self.wrappers),
                "traffic_split_ratio": self.traffic_split_ratio,
                "migration_statuses": {
                    status.value: sum(
                        1 for w in self.wrappers.values()
                        if w.migration_status == status
                    )
                    for status in MigrationStatus
                },
            }
