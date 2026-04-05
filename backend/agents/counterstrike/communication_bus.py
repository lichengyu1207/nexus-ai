"""
作战通信总线
War Communication Bus

基于XMPP协议的低延迟通信系统
支持点对点通信、群组通信、广播通信
"""

import asyncio
import time
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class MessageType(Enum):
    RECON_REPORT = "recon_report"
    TRACE_UPDATE = "trace_update"
    COUNTER_CMD = "counter_cmd"
    COORDINATE_REQ = "coordinate_req"
    STATUS_SYNC = "status_sync"
    ALERT = "alert"
    TACTICAL_UPDATE = "tactical_update"
    PHEROMONE_DEPOSIT = "pheromone_deposit"
    SYSTEM_EVENT = "system_event"


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class WarMessage:
    message_id: str
    message_type: MessageType
    sender: str
    recipients: List[str]
    timestamp: datetime
    priority: MessagePriority
    payload: Dict[str, Any]
    requires_ack: bool
    acked_by: Set[str]
    ttl_seconds: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender": self.sender,
            "recipients": self.recipients,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "payload": self.payload,
            "requires_ack": self.requires_ack,
            "acked_by": list(self.acked_by),
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata
        }


class MessageQueue:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_size))
        self.priority_queues: Dict[str, Dict[MessagePriority, deque]] = defaultdict(
            lambda: {p: deque(maxlen=max_size) for p in MessagePriority}
        )
        
    def enqueue(self, recipient: str, message: WarMessage):
        self.queues[recipient].append(message)
        self.priority_queues[recipient][message.priority].append(message)
        
    def dequeue(self, recipient: str, priority: Optional[MessagePriority] = None) -> Optional[WarMessage]:
        if priority:
            if self.priority_queues[recipient][priority]:
                return self.priority_queues[recipient][priority].popleft()
        else:
            for p in reversed(list(MessagePriority)):
                if self.priority_queues[recipient][p]:
                    return self.priority_queues[recipient][p].popleft()
        return None
        
    def peek(self, recipient: str) -> Optional[WarMessage]:
        for p in reversed(list(MessagePriority)):
            if self.priority_queues[recipient][p]:
                return self.priority_queues[recipient][p][0]
        return None
        
    def size(self, recipient: str) -> int:
        return len(self.queues[recipient])


class SubscriptionManager:
    def __init__(self):
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.topic_subscribers: Dict[str, Set[str]] = defaultdict(set)
        
    def subscribe(self, agent_id: str, topic: str):
        self.subscriptions[agent_id].add(topic)
        self.topic_subscribers[topic].add(agent_id)
        
    def unsubscribe(self, agent_id: str, topic: str):
        self.subscriptions[agent_id].discard(topic)
        self.topic_subscribers[topic].discard(agent_id)
        
    def get_subscribers(self, topic: str) -> Set[str]:
        return self.topic_subscribers[topic].copy()
        
    def get_subscriptions(self, agent_id: str) -> Set[str]:
        return self.subscriptions[agent_id].copy()


class WarCommunicationBus:
    def __init__(
        self,
        bus_id: str = "war_comm_bus_001",
        redis_client: Optional[Any] = None
    ):
        self.bus_id = bus_id
        self.redis_client = redis_client
        
        self.message_queue = MessageQueue()
        self.subscription_manager = SubscriptionManager()
        
        self.handlers: Dict[str, Dict[MessageType, List[Callable]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        self.sent_messages: deque = deque(maxlen=5000)
        self.received_messages: deque = deque(maxlen=5000)
        self.pending_acks: Dict[str, WarMessage] = {}
        
        self.stats = {
            "total_sent": 0,
            "total_received": 0,
            "total_acked": 0,
            "total_dropped": 0,
            "avg_latency_ms": 0.0,
            "queue_size": 0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info(f"WarCommunicationBus {self.bus_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"WarCommunicationBus {self.bus_id} stopped")
        
    async def _process_loop(self):
        while self._running:
            try:
                await self._process_pending_acks()
                await self._cleanup_expired_messages()
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process loop: {e}")
                await asyncio.sleep(1)
                
    async def _process_pending_acks(self):
        now = datetime.now()
        expired = []
        
        for message_id, message in self.pending_acks.items():
            age = (now - message.timestamp).total_seconds()
            if age > message.ttl_seconds:
                expired.append(message_id)
                
        for message_id in expired:
            self.pending_acks.pop(message_id)
            self.stats["total_dropped"] += 1
            
    async def _cleanup_expired_messages(self):
        pass
        
    async def send(
        self,
        message_type: MessageType,
        sender: str,
        recipients: List[str],
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_ack: bool = False,
        ttl_seconds: int = 300
    ) -> WarMessage:
        message = WarMessage(
            message_id=self._generate_message_id(),
            message_type=message_type,
            sender=sender,
            recipients=recipients,
            timestamp=datetime.now(),
            priority=priority,
            payload=payload,
            requires_ack=requires_ack,
            acked_by=set(),
            ttl_seconds=ttl_seconds,
            metadata={}
        )
        
        for recipient in recipients:
            self.message_queue.enqueue(recipient, message)
            
        self.sent_messages.append(message)
        self.stats["total_sent"] += 1
        
        if requires_ack:
            self.pending_acks[message.message_id] = message
            
        if self.redis_client:
            await self._publish_to_redis(message)
            
        logger.debug(f"Sent message {message.message_id} from {sender} to {recipients}")
        
        return message
        
    async def broadcast(
        self,
        message_type: MessageType,
        sender: str,
        topic: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> WarMessage:
        subscribers = self.subscription_manager.get_subscribers(topic)
        
        return await self.send(
            message_type=message_type,
            sender=sender,
            recipients=list(subscribers),
            payload=payload,
            priority=priority
        )
        
    async def publish(self, topic: str, data: Dict[str, Any]) -> str:
        message = await self.broadcast(
            message_type=MessageType.SYSTEM_EVENT,
            sender=self.bus_id,
            topic=topic,
            payload={"topic": topic, "data": data}
        )
        return message.message_id
        
    async def receive(self, agent_id: str) -> Optional[WarMessage]:
        message = self.message_queue.dequeue(agent_id)
        
        if message:
            self.received_messages.append(message)
            self.stats["total_received"] += 1
            
            await self._invoke_handlers(agent_id, message)
            
            if message.requires_ack:
                await self.ack(message.message_id, agent_id)
                
        return message
        
    async def ack(self, message_id: str, agent_id: str):
        message = self.pending_acks.get(message_id)
        if message:
            message.acked_by.add(agent_id)
            
            if message.acked_by.issuperset(set(message.recipients)):
                self.pending_acks.pop(message_id)
                self.stats["total_acked"] += 1
                
    def register_handler(
        self,
        agent_id: str,
        message_type: MessageType,
        handler: Callable
    ):
        self.handlers[agent_id][message_type].append(handler)
        
    def unregister_handler(
        self,
        agent_id: str,
        message_type: MessageType,
        handler: Callable
    ):
        if handler in self.handlers[agent_id][message_type]:
            self.handlers[agent_id][message_type].remove(handler)
            
    async def _invoke_handlers(self, agent_id: str, message: WarMessage):
        handlers = self.handlers[agent_id].get(message.message_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                
    async def _publish_to_redis(self, message: WarMessage):
        if self.redis_client:
            try:
                channel = f"war_bus:{message.message_type.value}"
                await self.redis_client.publish(
                    channel,
                    json.dumps(message.to_dict())
                )
            except Exception as e:
                logger.error(f"Redis publish error: {e}")
                
    def subscribe(self, agent_id: str, topic: str):
        self.subscription_manager.subscribe(agent_id, topic)
        logger.debug(f"Agent {agent_id} subscribed to {topic}")
        
    def unsubscribe(self, agent_id: str, topic: str):
        self.subscription_manager.unsubscribe(agent_id, topic)
        logger.debug(f"Agent {agent_id} unsubscribed from {topic}")
        
    async def get_pending_messages(self, agent_id: str) -> List[Dict]:
        messages = list(self.message_queue.queues[agent_id])
        return [m.to_dict() for m in messages]
        
    async def get_message(self, message_id: str) -> Optional[Dict]:
        for message in self.sent_messages:
            if message.message_id == message_id:
                return message.to_dict()
        for message in self.received_messages:
            if message.message_id == message_id:
                return message.to_dict()
        return None
        
    def _generate_message_id(self) -> str:
        return f"msg_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
    def get_stats(self) -> Dict:
        total_queue_size = sum(
            self.message_queue.size(agent)
            for agent in self.message_queue.queues.keys()
        )
        
        return {
            **self.stats,
            "queue_size": total_queue_size,
            "pending_acks": len(self.pending_acks),
            "active_subscriptions": len(self.subscription_manager.subscriptions)
        }
