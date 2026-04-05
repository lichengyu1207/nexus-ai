"""
五端统一消息总线
Five-End Unified Message Bus

实现基于Redis Streams的跨端消息传递系统
"""

import asyncio
import json
import uuid
import hashlib
import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    REGION_RISK = "REGION_RISK"
    INDUSTRY_REPORT = "INDUSTRY_REPORT"
    USER_DEMAND = "USER_DEMAND"
    POLICY_CHANGE = "POLICY_CHANGE"
    POTENTIAL_CLIENT = "POTENTIAL_CLIENT"
    DEMAND_SIGNAL = "DEMAND_SIGNAL"
    APPOINTMENT_REQUEST = "APPOINTMENT_REQUEST"
    UPDATE_RULE = "UPDATE_RULE"
    DATA_REQUEST = "DATA_REQUEST"
    BAN_EVENT = "BAN_EVENT"
    UNBAN_EVENT = "UNBAN_EVENT"
    ATTACK_DETECTED = "ATTACK_DETECTED"
    CONSENSUS_PROPOSAL = "CONSENSUS_PROPOSAL"
    CONSENSUS_VOTE = "CONSENSUS_VOTE"
    DISCLAIMER_CONFIRMED = "DISCLAIMER_CONFIRMED"
    AGENT_SPAWN = "AGENT_SPAWN"
    AGENT_MERGE = "AGENT_MERGE"
    CROSS_END_SYNC = "CROSS_END_SYNC"
    HEARTBEAT = "HEARTBEAT"
    ALERT = "ALERT"


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20
    EMERGENCY = 30


class EndType(Enum):
    GOV = "gov"
    ENTERPRISE = "enterprise"
    EDU = "edu"
    STD = "std"
    PUBLIC = "public"


@dataclass
class CrossEndEvent:
    event_id: str
    event_type: EventType
    source_end: EndType
    source_agent: str
    target_end: Optional[EndType] = None
    target_agent: Optional[str] = None
    broadcast: bool = False
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3600
    signature: str = ""
    prev_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source_end": self.source_end.value,
            "source_agent": self.source_agent,
            "target_end": self.target_end.value if self.target_end else None,
            "target_agent": self.target_agent,
            "broadcast": self.broadcast,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "signature": self.signature,
            "prev_hash": self.prev_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrossEndEvent":
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            source_end=EndType(data["source_end"]),
            source_agent=data["source_agent"],
            target_end=EndType(data["target_end"]) if data.get("target_end") else None,
            target_agent=data.get("target_agent"),
            broadcast=data.get("broadcast", False),
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", 5)),
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", 3600),
            signature=data.get("signature", ""),
            prev_hash=data.get("prev_hash", ""),
        )
    
    def compute_hash(self) -> str:
        data = f"{self.event_id}{self.event_type.value}{self.timestamp}{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()


class MessageQueue:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues: Dict[str, List[CrossEndEvent]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def push(self, channel: str, event: CrossEndEvent) -> bool:
        async with self._lock:
            if len(self._queues[channel]) >= self.max_size:
                self._queues[channel] = self._queues[channel][-int(self.max_size * 0.8):]
            self._queues[channel].append(event)
            return True
    
    async def pop(self, channel: str, count: int = 1) -> List[CrossEndEvent]:
        async with self._lock:
            events = self._queues[channel][:count]
            self._queues[channel] = self._queues[channel][count:]
            return events
    
    async def peek(self, channel: str, count: int = 10) -> List[CrossEndEvent]:
        return self._queues[channel][:count]
    
    async def size(self, channel: str) -> int:
        return len(self._queues[channel])


class SubscriptionManager:
    def __init__(self):
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._agent_channels: Dict[str, Set[str]] = defaultdict(set)
    
    def subscribe(self, agent_id: str, channel: str) -> None:
        self._subscriptions[channel].add(agent_id)
        self._agent_channels[agent_id].add(channel)
    
    def unsubscribe(self, agent_id: str, channel: str) -> None:
        self._subscriptions[channel].discard(agent_id)
        self._agent_channels[agent_id].discard(channel)
    
    def unsubscribe_all(self, agent_id: str) -> None:
        for channel in list(self._agent_channels.get(agent_id, [])):
            self._subscriptions[channel].discard(agent_id)
        self._agent_channels.pop(agent_id, None)
    
    def get_subscribers(self, channel: str) -> Set[str]:
        return self._subscriptions[channel].copy()
    
    def get_agent_channels(self, agent_id: str) -> Set[str]:
        return self._agent_channels.get(agent_id, set()).copy()


class EventRouter:
    def __init__(self):
        self._type_routes: Dict[EventType, List[str]] = defaultdict(list)
        self._pattern_routes: Dict[str, List[str]] = {}
    
    def add_route(self, event_type: EventType, target_channels: List[str]) -> None:
        self._type_routes[event_type].extend(target_channels)
    
    def add_pattern_route(self, pattern: str, target_channels: List[str]) -> None:
        self._pattern_routes[pattern] = target_channels
    
    def route(self, event: CrossEndEvent) -> List[str]:
        channels = []
        
        if event.broadcast:
            channels = ["gov", "enterprise", "edu", "std", "public", "cross"]
        elif event.target_end:
            channels = [event.target_end.value]
        else:
            channels = self._type_routes.get(event.event_type, ["cross"])
        
        return channels


class FiveEndMessageBus:
    CHANNELS = {
        EndType.GOV: "gov",
        EndType.ENTERPRISE: "enterprise",
        EndType.EDU: "edu",
        EndType.STD: "std",
        EndType.PUBLIC: "public",
        "cross": "cross",
    }
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client
        self.message_queue = MessageQueue()
        self.subscription_manager = SubscriptionManager()
        self.event_router = EventRouter()
        
        self._event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._event_chain: List[str] = []
        self._last_hash = "0" * 64
        
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        self._setup_default_routes()
    
    def _setup_default_routes(self) -> None:
        self.event_router.add_route(EventType.REGION_RISK, ["enterprise", "public", "edu", "std"])
        self.event_router.add_route(EventType.POLICY_CHANGE, ["enterprise", "public", "edu", "std"])
        self.event_router.add_route(EventType.BAN_EVENT, ["gov", "enterprise", "edu", "std", "public"])
        self.event_router.add_route(EventType.UNBAN_EVENT, ["gov", "enterprise", "edu", "std", "public"])
        self.event_router.add_route(EventType.ATTACK_DETECTED, ["gov", "enterprise", "edu", "std", "public"])
        self.event_router.add_route(EventType.UPDATE_RULE, ["gov", "enterprise", "edu", "public"])
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._process_events()))
        self._tasks.append(asyncio.create_task(self._cleanup_expired_events()))
        self._tasks.append(asyncio.create_task(self._heartbeat()))
        logger.info("FiveEndMessageBus started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("FiveEndMessageBus stopped")
    
    def register_agent(self, agent_id: str, end_type: EndType, 
                       agent_type: str, capabilities: List[str]) -> None:
        self._agent_registry[agent_id] = {
            "end_type": end_type,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
        }
        
        default_channel = self.CHANNELS[end_type]
        self.subscription_manager.subscribe(agent_id, default_channel)
        self.subscription_manager.subscribe(agent_id, "cross")
        
        logger.info(f"Agent {agent_id} registered on {end_type.value} end")
    
    def unregister_agent(self, agent_id: str) -> None:
        self.subscription_manager.unsubscribe_all(agent_id)
        self._agent_registry.pop(agent_id, None)
        logger.info(f"Agent {agent_id} unregistered")
    
    def subscribe(self, agent_id: str, channel: str) -> None:
        self.subscription_manager.subscribe(agent_id, channel)
    
    def unsubscribe(self, agent_id: str, channel: str) -> None:
        self.subscription_manager.unsubscribe(agent_id, channel)
    
    def on_event(self, event_type: EventType, handler: Callable) -> None:
        self._event_handlers[event_type].append(handler)
    
    async def publish(self, event: CrossEndEvent) -> str:
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        
        event.prev_hash = self._last_hash
        event.signature = self._sign_event(event)
        self._last_hash = event.compute_hash()
        self._event_chain.append(self._last_hash)
        
        channels = self.event_router.route(event)
        
        for channel in channels:
            await self.message_queue.push(channel, event)
        
        if self.redis_client:
            await self._publish_to_redis(event, channels)
        
        logger.debug(f"Event {event.event_id} published to channels: {channels}")
        return event.event_id
    
    async def _publish_to_redis(self, event: CrossEndEvent, channels: List[str]) -> None:
        if not self.redis_client:
            return
        
        event_data = json.dumps(event.to_dict())
        for channel in channels:
            try:
                await self.redis_client.xadd(
                    f"five_end_bus:{channel}",
                    {"data": event_data},
                    maxlen=10000
                )
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")
    
    async def consume(self, agent_id: str, count: int = 10) -> List[CrossEndEvent]:
        channels = self.subscription_manager.get_agent_channels(agent_id)
        events = []
        
        for channel in channels:
            channel_events = await self.message_queue.pop(channel, count)
            events.extend(channel_events)
        
        events.sort(key=lambda e: e.priority.value, reverse=True)
        
        for event in events[:count]:
            await self._dispatch_event(event)
        
        return events[:count]
    
    async def _dispatch_event(self, event: CrossEndEvent) -> None:
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    async def _process_events(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
    
    async def _cleanup_expired_events(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(60)
                current_time = time.time()
            except asyncio.CancelledError:
                break
    
    async def _heartbeat(self) -> None:
        while self._running:
            try:
                heartbeat_event = CrossEndEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.HEARTBEAT,
                    source_end=EndType.GOV,
                    source_agent="message_bus",
                    broadcast=True,
                    payload={"timestamp": time.time()},
                    priority=MessagePriority.LOW,
                )
                await self.publish(heartbeat_event)
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
    
    def _sign_event(self, event: CrossEndEvent) -> str:
        data = f"{event.event_id}{event.event_type.value}{event.timestamp}{event.source_end.value}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    async def get_event_chain(self, count: int = 100) -> List[str]:
        return self._event_chain[-count:]
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agent_registry.get(agent_id)
    
    async def get_all_agents(self, end_type: Optional[EndType] = None) -> Dict[str, Dict[str, Any]]:
        if end_type:
            return {
                aid: info for aid, info in self._agent_registry.items()
                if info["end_type"] == end_type
            }
        return self._agent_registry.copy()
    
    async def get_channel_stats(self) -> Dict[str, Dict[str, int]]:
        stats = {}
        for channel in ["gov", "enterprise", "edu", "std", "public", "cross"]:
            stats[channel] = {
                "queue_size": await self.message_queue.size(channel),
                "subscribers": len(self.subscription_manager.get_subscribers(channel)),
            }
        return stats
    
    async def broadcast_to_end(self, end_type: EndType, event_type: EventType,
                                payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        event = CrossEndEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_end=EndType.GOV,
            source_agent="system",
            target_end=end_type,
            payload=payload,
            priority=priority,
        )
        return await self.publish(event)
    
    async def broadcast_all(self, event_type: EventType, payload: Dict[str, Any],
                            priority: MessagePriority = MessagePriority.NORMAL) -> str:
        event = CrossEndEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_end=EndType.GOV,
            source_agent="system",
            broadcast=True,
            payload=payload,
            priority=priority,
        )
        return await self.publish(event)
    
    async def send_direct(self, target_agent: str, event_type: EventType,
                          payload: Dict[str, Any], source_agent: str,
                          source_end: EndType, priority: MessagePriority = MessagePriority.NORMAL) -> str:
        target_info = self._agent_registry.get(target_agent)
        if not target_info:
            raise ValueError(f"Target agent {target_agent} not found")
        
        event = CrossEndEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_end=source_end,
            source_agent=source_agent,
            target_end=target_info["end_type"],
            target_agent=target_agent,
            payload=payload,
            priority=priority,
        )
        return await self.publish(event)


class MessageBusMonitor:
    def __init__(self, message_bus: FiveEndMessageBus):
        self.message_bus = message_bus
        self._metrics: Dict[str, List[float]] = defaultdict(list)
        self._max_metrics = 1000
    
    async def collect_metrics(self) -> Dict[str, Any]:
        channel_stats = await self.message_bus.get_channel_stats()
        agent_count = len(self.message_bus._agent_registry)
        chain_length = len(self.message_bus._event_chain)
        
        return {
            "timestamp": time.time(),
            "agent_count": agent_count,
            "event_chain_length": chain_length,
            "channels": channel_stats,
        }
    
    async def get_communication_topology(self) -> Dict[str, Any]:
        agents = await self.message_bus.get_all_agents()
        
        nodes = []
        edges = []
        
        for agent_id, info in agents.items():
            nodes.append({
                "id": agent_id,
                "end_type": info["end_type"].value,
                "agent_type": info["agent_type"],
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    
    async def get_message_flow(self, duration_seconds: int = 60) -> Dict[str, Any]:
        return {
            "duration": duration_seconds,
            "total_messages": len(self.message_bus._event_chain),
            "by_type": {},
            "by_end": {},
        }
