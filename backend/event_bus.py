"""
事件总线实现
支持内存模式（默认）和Redis模式
用于模块间解耦通信
"""
import asyncio
import logging
import threading
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], None]


class MemoryEventBus:
    """内存事件总线（默认）"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._lock = threading.Lock()
        self._event_history: List[Dict] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """订阅事件"""
        with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """取消订阅"""
        with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
    
    def publish(self, event_type: str, event_data: Any):
        """发布事件（同步）"""
        with self._lock:
            handlers = self._subscribers[event_type].copy()
        
        self._add_to_history(event_type, event_data)
        
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def publish_async(self, event_type: str, event_data: Any):
        """发布事件（异步）"""
        with self._lock:
            handlers = self._subscribers[event_type].copy()
        
        self._add_to_history(event_type, event_data)
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in async event handler for {event_type}: {e}")
    
    def _add_to_history(self, event_type: str, event_data: Any):
        """添加到事件历史"""
        record = {
            'event_type': event_type,
            'data': event_data.to_dict() if hasattr(event_data, 'to_dict') else event_data,
            'timestamp': datetime.now().isoformat()
        }
        self._event_history.append(record)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取事件历史"""
        if event_type:
            return [e for e in self._event_history if e['event_type'] == event_type][-limit:]
        return self._event_history[-limit:]


class RedisEventBus:
    """Redis事件总线"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None
        self._pubsub = None
        self._listeners: Dict[str, List[EventHandler]] = defaultdict(list)
        self._running = False
    
    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(self.redis_url)
            except ImportError:
                logger.warning("Redis library not installed, falling back to memory bus")
                return None
        return self._redis
    
    async def subscribe(self, event_type: str, handler: EventHandler):
        """订阅事件"""
        self._listeners[event_type].append(handler)
        
        redis = await self._get_redis()
        if redis:
            if self._pubsub is None:
                self._pubsub = redis.pubsub()
            await self._pubsub.subscribe(event_type)
    
    async def unsubscribe(self, event_type: str, handler: EventHandler):
        """取消订阅"""
        if handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)
    
    async def publish(self, event_type: str, event_data: Any):
        """发布事件"""
        redis = await self._get_redis()
        
        if redis:
            data = event_data.to_json() if hasattr(event_data, 'to_json') else json.dumps(event_data)
            await redis.publish(event_type, data)
        
        for handler in self._listeners[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in Redis event handler for {event_type}: {e}")


class EventBus:
    """事件总线统一接口"""
    
    _instance: Optional['EventBus'] = None
    _bus: Any = None
    
    def __new__(cls, use_redis: bool = False, redis_url: str = "redis://localhost:6379/0"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if use_redis:
                cls._bus = RedisEventBus(redis_url)
            else:
                cls._bus = MemoryEventBus()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """订阅事件"""
        self._bus.subscribe(event_type, handler)
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """取消订阅"""
        self._bus.unsubscribe(event_type, handler)
    
    def publish(self, event_type: str, event_data: Any):
        """发布事件（同步）"""
        if hasattr(self._bus, 'publish'):
            self._bus.publish(event_type, event_data)
    
    async def publish_async(self, event_type: str, event_data: Any):
        """发布事件（异步）"""
        if hasattr(self._bus, 'publish_async'):
            await self._bus.publish_async(event_type, event_data)
        elif hasattr(self._bus, 'publish'):
            self._bus.publish(event_type, event_data)
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取事件历史"""
        if hasattr(self._bus, 'get_history'):
            return self._bus.get_history(event_type, limit)
        return []


event_bus = EventBus.get_instance()
