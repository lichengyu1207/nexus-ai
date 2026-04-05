"""
业务环境场
Business Environment Field

作为业务智能体感知的统一环境
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

logger = logging.getLogger(__name__)


class KPIType(Enum):
    QPS = "qps"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    TASK_SUCCESS_RATE = "task_success_rate"
    ENERGY_EFFICIENCY = "energy_efficiency"
    COLLABORATION_RATE = "collaboration_rate"


class EventType(Enum):
    KPI_ANOMALY = "kpi_anomaly"
    MARKET_CHANGE = "market_change"
    POLICY_UPDATE = "policy_update"
    COMPETITOR_ACTION = "competitor_action"
    USER_SURGE = "user_surge"
    SYSTEM_OVERLOAD = "system_overload"


@dataclass
class KPIIndicator:
    kpi_type: KPIType
    value: float
    target: float
    threshold_low: float
    threshold_high: float
    trend: str
    last_updated: float
    
    def is_healthy(self) -> bool:
        return self.threshold_low <= self.value <= self.threshold_high
    
    def get_deviation(self) -> float:
        if self.value < self.threshold_low:
            return (self.threshold_low - self.value) / self.threshold_low
        elif self.value > self.threshold_high:
            return (self.value - self.threshold_high) / self.threshold_high
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            "kpi_type": self.kpi_type.value,
            "value": self.value,
            "target": self.target,
            "threshold_low": self.threshold_low,
            "threshold_high": self.threshold_high,
            "trend": self.trend,
            "is_healthy": self.is_healthy(),
            "deviation": self.get_deviation(),
            "last_updated": self.last_updated
        }


@dataclass
class EnvironmentSnapshot:
    snapshot_id: str
    timestamp: float
    kpis: Dict[str, KPIIndicator]
    market_data: Dict
    internal_state: Dict
    events: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "kpis": {k: v.to_dict() for k, v in self.kpis.items()},
            "market_data": self.market_data,
            "internal_state": self.internal_state,
            "events": self.events
        }


class BusinessEnvironmentField:
    """
    业务环境场
    
    作为业务智能体感知的统一环境：
    1. 环境指标：实时业务KPI、市场数据、内部状态
    2. 感知接口：sense()获取环境向量
    3. 环境变化事件：KPI异常自动广播
    4. 历史环境记录：存储环境快照
    """
    
    DEFAULT_THRESHOLDS = {
        KPIType.QPS: (10, 1000),
        KPIType.RESPONSE_TIME: (0.1, 5.0),
        KPIType.USER_SATISFACTION: (0.6, 1.0),
        KPIType.TASK_SUCCESS_RATE: (0.7, 1.0),
        KPIType.ENERGY_EFFICIENCY: (0.5, 1.0),
        KPIType.COLLABORATION_RATE: (0.1, 0.8),
    }
    
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        snapshot_interval: float = 60.0,
        history_size: int = 1000,
    ):
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        self.memory_agent = memory_agent
        self.snapshot_interval = snapshot_interval
        self.history_size = history_size
        
        self.kpis: Dict[str, KPIIndicator] = {}
        self.market_data: Dict = {}
        self.internal_state: Dict = {}
        
        self.event_subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.active_events: List[Dict] = []
        
        self.history: deque = deque(maxlen=history_size)
        
        self._lock = threading.RLock()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        self._init_default_kpis()
        
        self.stats = {
            "snapshots_taken": 0,
            "events_broadcast": 0,
            "anomalies_detected": 0,
            "sense_operations": 0,
        }
    
    def _init_default_kpis(self):
        for kpi_type in KPIType:
            thresholds = self.DEFAULT_THRESHOLDS.get(kpi_type, (0.0, 1.0))
            target = (thresholds[0] + thresholds[1]) / 2
            
            self.kpis[kpi_type.value] = KPIIndicator(
                kpi_type=kpi_type,
                value=target,
                target=target,
                threshold_low=thresholds[0],
                threshold_high=thresholds[1],
                trend="stable",
                last_updated=time.time()
            )
    
    async def start(self):
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Business environment field started")
    
    async def stop(self):
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Business environment field stopped")
    
    async def _monitor_loop(self):
        while self._running:
            try:
                await self._update_kpis()
                await self._check_anomalies()
                await self._take_snapshot()
                await asyncio.sleep(self.snapshot_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(10)
    
    async def _update_kpis(self):
        for kpi_name, kpi in self.kpis.items():
            old_value = kpi.value
            
            noise = random.uniform(-0.1, 0.1) * kpi.value
            new_value = kpi.value + noise
            new_value = max(kpi.threshold_low * 0.5, min(kpi.threshold_high * 1.5, new_value))
            
            kpi.value = new_value
            kpi.last_updated = time.time()
            
            if new_value > old_value * 1.05:
                kpi.trend = "rising"
            elif new_value < old_value * 0.95:
                kpi.trend = "falling"
            else:
                kpi.trend = "stable"
    
    async def _check_anomalies(self):
        for kpi_name, kpi in self.kpis.items():
            if not kpi.is_healthy():
                event = {
                    "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                    "event_type": EventType.KPI_ANOMALY.value,
                    "kpi_name": kpi_name,
                    "value": kpi.value,
                    "threshold": (
                        kpi.threshold_low if kpi.value < kpi.threshold_low
                        else kpi.threshold_high
                    ),
                    "deviation": kpi.get_deviation(),
                    "timestamp": time.time(),
                }
                
                await self._broadcast_event(event)
                self.stats["anomalies_detected"] += 1
    
    async def _broadcast_event(self, event: Dict):
        self.active_events.append(event)
        
        event_type = EventType(event.get("event_type", "kpi_anomaly"))
        
        for callback in self.event_subscribers[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        
        if self.communication_bus:
            try:
                await self.communication_bus.broadcast({
                    "type": "environment_event",
                    "event": event
                })
            except Exception as e:
                logger.error(f"Failed to broadcast event: {e}")
        
        self.stats["events_broadcast"] += 1
    
    async def _take_snapshot(self):
        snapshot = EnvironmentSnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            kpis=dict(self.kpis),
            market_data=dict(self.market_data),
            internal_state=dict(self.internal_state),
            events=list(self.active_events)
        )
        
        with self._lock:
            self.history.append(snapshot)
            self.active_events = []
            self.stats["snapshots_taken"] += 1
    
    def update_kpi(
        self,
        kpi_type: KPIType,
        value: float,
        target: Optional[float] = None,
    ):
        with self._lock:
            if kpi_type.value in self.kpis:
                kpi = self.kpis[kpi_type.value]
                old_value = kpi.value
                kpi.value = value
                kpi.last_updated = time.time()
                
                if target is not None:
                    kpi.target = target
                
                if value > old_value * 1.05:
                    kpi.trend = "rising"
                elif value < old_value * 0.95:
                    kpi.trend = "falling"
                else:
                    kpi.trend = "stable"
    
    def update_market_data(self, data: Dict):
        with self._lock:
            self.market_data.update(data)
            self.market_data["last_updated"] = time.time()
    
    def update_internal_state(self, state: Dict):
        with self._lock:
            self.internal_state.update(state)
            self.internal_state["last_updated"] = time.time()
    
    async def sense(self, agent_id: str, energy_cost: float = 0.1) -> Dict:
        """
        感知环境，获取当前环境向量
        
        Args:
            agent_id: 智能体ID
            energy_cost: 感知消耗的能量
            
        Returns:
            dict: 环境向量
        """
        self.stats["sense_operations"] += 1
        
        with self._lock:
            kpi_vector = {
                name: {
                    "value": kpi.value,
                    "trend": kpi.trend,
                    "healthy": kpi.is_healthy()
                }
                for name, kpi in self.kpis.items()
            }
            
            environment = {
                "timestamp": time.time(),
                "agent_id": agent_id,
                "kpis": kpi_vector,
                "market": dict(self.market_data),
                "internal": dict(self.internal_state),
                "events": list(self.active_events),
            }
        
        return environment
    
    def subscribe_to_event(
        self,
        event_type: EventType,
        callback: Callable,
    ):
        self.event_subscribers[event_type].append(callback)
    
    def unsubscribe_from_event(
        self,
        event_type: EventType,
        callback: Callable,
    ):
        if callback in self.event_subscribers[event_type]:
            self.event_subscribers[event_type].remove(callback)
    
    def get_kpi(self, kpi_type: KPIType) -> Optional[KPIIndicator]:
        return self.kpis.get(kpi_type.value)
    
    def get_all_kpis(self) -> Dict[str, KPIIndicator]:
        return dict(self.kpis)
    
    def get_market_data(self) -> Dict:
        return dict(self.market_data)
    
    def get_internal_state(self) -> Dict:
        return dict(self.internal_state)
    
    def get_history(self, limit: int = 10) -> List[EnvironmentSnapshot]:
        return list(self.history)[-limit:]
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "kpi_count": len(self.kpis),
                "history_size": len(self.history),
                "active_events": len(self.active_events),
                "subscriber_count": sum(
                    len(callbacks) for callbacks in self.event_subscribers.values()
                ),
            }
