"""
活体智能体系统模块
Living Agent System Module

实现自组织、涌现智能、自适应进化的活体智能体系统
"""

import os
import sys
import json
import time
import uuid
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
from abc import ABC, abstractmethod
import random
import hashlib

logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = "idle"
    WORKING = "working"
    SUSPICIOUS = "suspicious"
    ATTACKING = "attacking"
    RESTING = "resting"
    REPRODUCING = "reproducing"


class MessageType(Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"
    BLACKBOARD = "blackboard"
    TASK = "task"
    ALERT = "alert"
    COORDINATION = "coordination"


@dataclass
class Message:
    message_id: str
    from_agent: str
    to_agent: Optional[str]
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    ttl: int = 300
    priority: int = 0
    requires_ack: bool = False
    ack_received: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "priority": self.priority,
            "requires_ack": self.requires_ack,
            "ack_received": self.ack_received
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            message_id=data["message_id"],
            from_agent=data["from_agent"],
            to_agent=data.get("to_agent"),
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", 300),
            priority=data.get("priority", 0),
            requires_ack=data.get("requires_ack", False),
            ack_received=data.get("ack_received", False)
        )


class P2PCommunication:
    
    def __init__(
        self,
        agent_id: str,
        redis_url: Optional[str] = None,
        max_queue_size: int = 10000,
        message_timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.agent_id = agent_id
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.max_queue_size = max_queue_size
        self.message_timeout = message_timeout
        self.max_retries = max_retries
        
        self.message_queue: deque = deque(maxlen=max_queue_size)
        self.sent_messages: Dict[str, Message] = {}
        self.pending_acks: Dict[str, float] = {}
        
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        self.redis_client = None
        self.pubsub = None
        self._running = False
        self._listener_thread = None
        
        self.stats = {
            "sent": 0,
            "received": 0,
            "acknowledged": 0,
            "timeout": 0,
            "retries": 0
        }
    
    def connect(self) -> bool:
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(f"agent:{self.agent_id}")
            self.pubsub.subscribe("broadcast:all")
            
            self._running = True
            self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._listener_thread.start()
            
            logger.info(f"P2P Communication connected for agent {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect P2P Communication: {e}")
            self.redis_client = None
            return False
    
    def disconnect(self):
        self._running = False
        if self.pubsub:
            self.pubsub.unsubscribe()
            self.pubsub.close()
        if self.redis_client:
            self.redis_client.close()
        logger.info(f"P2P Communication disconnected for agent {self.agent_id}")
    
    def _listen_loop(self):
        while self._running:
            try:
                if self.pubsub:
                    message = self.pubsub.get_message(timeout=0.1)
                    if message and message["type"] == "message":
                        self._handle_redis_message(message)
                
                self._check_timeouts()
                
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                time.sleep(0.1)
    
    def _handle_redis_message(self, raw_message: Dict):
        try:
            data = json.loads(raw_message["data"])
            message = Message.from_dict(data)
            
            if message.to_agent and message.to_agent != self.agent_id:
                return
            
            self.message_queue.append(message)
            self.stats["received"] += 1
            
            if message.requires_ack:
                self._send_ack(message)
            
            self._dispatch_message(message)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _send_ack(self, message: Message):
        ack = Message(
            message_id=f"ack_{message.message_id}",
            from_agent=self.agent_id,
            to_agent=message.from_agent,
            message_type=MessageType.DIRECT,
            payload={"ack_for": message.message_id},
            requires_ack=False
        )
        self._publish_message(ack)
    
    def _dispatch_message(self, message: Message):
        if message.message_type in self.message_handlers:
            try:
                self.message_handlers[message.message_type](message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
        
        for callback in self.subscribers.get("message", []):
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in subscriber callback: {e}")
    
    def _check_timeouts(self):
        current_time = time.time()
        timed_out = []
        
        for msg_id, send_time in list(self.pending_acks.items()):
            if current_time - send_time > self.message_timeout:
                timed_out.append(msg_id)
        
        for msg_id in timed_out:
            del self.pending_acks[msg_id]
            self.stats["timeout"] += 1
            
            if msg_id in self.sent_messages:
                original = self.sent_messages[msg_id]
                if original.requires_ack and self.stats["retries"] < self.max_retries:
                    self._retry_message(original)
    
    def _retry_message(self, message: Message):
        self.stats["retries"] += 1
        self._publish_message(message)
    
    def _publish_message(self, message: Message) -> bool:
        if not self.redis_client:
            return False
        
        try:
            channel = f"agent:{message.to_agent}" if message.to_agent else "broadcast:all"
            self.redis_client.publish(channel, json.dumps(message.to_dict()))
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def send_message(
        self,
        target_agent_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: int = 0,
        requires_ack: bool = False
    ) -> str:
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        message = Message(
            message_id=message_id,
            from_agent=self.agent_id,
            to_agent=target_agent_id,
            message_type=message_type,
            payload=payload,
            priority=priority,
            requires_ack=requires_ack
        )
        
        self.sent_messages[message_id] = message
        
        if requires_ack:
            self.pending_acks[message_id] = time.time()
        
        success = self._publish_message(message)
        
        if success:
            self.stats["sent"] += 1
        
        return message_id
    
    def broadcast(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> str:
        message_id = f"bcast_{uuid.uuid4().hex[:12]}"
        
        message = Message(
            message_id=message_id,
            from_agent=self.agent_id,
            to_agent=None,
            message_type=message_type,
            payload=payload,
            priority=priority
        )
        
        self._publish_message(message)
        self.stats["sent"] += 1
        
        return message_id
    
    def receive_message(self, timeout: float = 0.1) -> Optional[Message]:
        try:
            if self.message_queue:
                return self.message_queue.popleft()
        except IndexError:
            pass
        return None
    
    def receive_all_messages(self) -> List[Message]:
        messages = list(self.message_queue)
        self.message_queue.clear()
        return messages
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        self.message_handlers[message_type] = handler
    
    def subscribe(self, event_type: str, callback: Callable):
        self.subscribers[event_type].append(callback)
    
    def get_stats(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "queue_size": len(self.message_queue),
            "pending_acks": len(self.pending_acks),
            "stats": self.stats.copy(),
            "connected": self.redis_client is not None
        }


class Blackboard:
    
    def __init__(
        self,
        name: str = "global",
        redis_url: Optional[str] = None,
        default_ttl: int = 3600
    ):
        self.name = name
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.default_ttl = default_ttl
        
        self.redis_client = None
        self.local_cache: Dict[str, Tuple[Any, float, float]] = {}
        
        self.watchers: Dict[str, List[Callable]] = defaultdict(list)
        self._running = False
        self._watcher_thread = None
        
        self.stats = {
            "writes": 0,
            "reads": 0,
            "searches": 0,
            "evictions": 0
        }
    
    def connect(self) -> bool:
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            
            self._running = True
            self._watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
            self._watcher_thread.start()
            
            logger.info(f"Blackboard '{self.name}' connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Blackboard: {e}")
            return False
    
    def disconnect(self):
        self._running = False
        if self.redis_client:
            self.redis_client.close()
    
    def _watch_loop(self):
        last_check = time.time()
        while self._running:
            try:
                current_time = time.time()
                if current_time - last_check > 1.0:
                    self._check_expirations()
                    last_check = current_time
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
    
    def _check_expirations(self):
        expired_keys = []
        current_time = time.time()
        
        for key, (value, expiry, created) in list(self.local_cache.items()):
            if expiry > 0 and current_time > created + expiry:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.local_cache[key]
            self.stats["evictions"] += 1
    
    def _make_key(self, key: str) -> str:
        return f"blackboard:{self.name}:{key}"
    
    def write(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        notify: bool = True
    ) -> bool:
        full_key = self._make_key(key)
        ttl = ttl if ttl is not None else self.default_ttl
        
        try:
            data = json.dumps(value) if not isinstance(value, str) else value
            
            if self.redis_client:
                if ttl > 0:
                    self.redis_client.setex(full_key, ttl, data)
                else:
                    self.redis_client.set(full_key, data)
            
            self.local_cache[key] = (value, ttl, time.time())
            self.stats["writes"] += 1
            
            if notify:
                self._notify_watchers(key, value)
            
            return True
        except Exception as e:
            logger.error(f"Failed to write to blackboard: {e}")
            return False
    
    def read(self, key: str, default: Any = None) -> Any:
        full_key = self._make_key(key)
        
        if key in self.local_cache:
            value, expiry, created = self.local_cache[key]
            if expiry == 0 or time.time() < created + expiry:
                self.stats["reads"] += 1
                return value
        
        if self.redis_client:
            try:
                data = self.redis_client.get(full_key)
                if data:
                    value = json.loads(data)
                    self.local_cache[key] = (value, 0, time.time())
                    self.stats["reads"] += 1
                    return value
            except Exception as e:
                logger.error(f"Failed to read from blackboard: {e}")
        
        return default
    
    def delete(self, key: str) -> bool:
        full_key = self._make_key(key)
        
        if key in self.local_cache:
            del self.local_cache[key]
        
        if self.redis_client:
            try:
                self.redis_client.delete(full_key)
            except Exception as e:
                logger.error(f"Failed to delete from blackboard: {e}")
        
        return True
    
    def exists(self, key: str) -> bool:
        if key in self.local_cache:
            return True
        
        if self.redis_client:
            full_key = self._make_key(key)
            return self.redis_client.exists(full_key) > 0
        
        return False
    
    def search(self, query: str, limit: int = 100) -> List[Dict]:
        results = []
        pattern = f"blackboard:{self.name}:*{query}*"
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                for key in keys[:limit]:
                    data = self.redis_client.get(key)
                    if data:
                        key_name = key.decode().replace(f"blackboard:{self.name}:", "")
                        results.append({
                            "key": key_name,
                            "value": json.loads(data)
                        })
                self.stats["searches"] += 1
            except Exception as e:
                logger.error(f"Failed to search blackboard: {e}")
        
        return results
    
    def watch(self, key_pattern: str, callback: Callable):
        self.watchers[key_pattern].append(callback)
    
    def _notify_watchers(self, key: str, value: Any):
        for pattern, callbacks in self.watchers.items():
            if pattern == "*" or pattern in key:
                for callback in callbacks:
                    try:
                        callback(key, value)
                    except Exception as e:
                        logger.error(f"Error in watcher callback: {e}")
    
    def get_all_keys(self) -> List[str]:
        keys = set(self.local_cache.keys())
        
        if self.redis_client:
            pattern = f"blackboard:{self.name}:*"
            try:
                redis_keys = self.redis_client.keys(pattern)
                for k in redis_keys:
                    key_name = k.decode().replace(f"blackboard:{self.name}:", "")
                    keys.add(key_name)
            except Exception as e:
                logger.error(f"Failed to get all keys: {e}")
        
        return list(keys)
    
    def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "local_cache_size": len(self.local_cache),
            "watchers_count": sum(len(v) for v in self.watchers.values()),
            "stats": self.stats.copy(),
            "connected": self.redis_client is not None
        }


global_blackboard = Blackboard("global")
