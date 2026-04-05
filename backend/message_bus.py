"""
消息总线模块
实现代理间通信、事件发布/订阅
"""
import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class Message:
    type: str
    sender: str
    receiver: Optional[str]
    payload: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }

class MessageBus:
    """
    消息总线
    支持点对点消息和广播消息
    支持事件发布/订阅模式
    """
    
    _instance: Optional['MessageBus'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._message_history: List[Message] = []
        self._max_history = 1000
    
    @classmethod
    async def get_instance(cls) -> 'MessageBus':
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.info("MessageBus initialized")
        return cls._instance
    
    async def subscribe(self, agent_name: str, handler: Callable):
        """
        订阅消息
        agent_name: 代理名称
        handler: 消息处理函数
        """
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(handler)
        
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()
        
        logger.debug(f"Agent '{agent_name}' subscribed to MessageBus")
    
    async def unsubscribe(self, agent_name: str, handler: Callable = None):
        """
        取消订阅
        """
        if handler and agent_name in self._subscribers:
            try:
                self._subscribers[agent_name].remove(handler)
            except ValueError:
                pass
        elif agent_name in self._subscribers:
            del self._subscribers[agent_name]
        
        logger.debug(f"Agent '{agent_name}' unsubscribed from MessageBus")
    
    async def send(self, message: Message) -> bool:
        """
        发送点对点消息
        """
        if message.receiver:
            if message.receiver in self._queues:
                await self._queues[message.receiver].put(message)
                logger.debug(f"Message sent from {message.sender} to {message.receiver}")
                return True
            else:
                logger.warning(f"Receiver {message.receiver} not found")
                return False
        return False
    
    async def broadcast(self, message: Message):
        """
        广播消息给所有订阅者
        """
        for agent_name, queue in self._queues.items():
            if agent_name != message.sender:
                await queue.put(message)
        
        logger.debug(f"Message broadcast from {message.sender} to all agents")
    
    async def receive(self, agent_name: str, timeout: float = 30.0) -> Optional[Message]:
        """
        接收消息
        """
        if agent_name not in self._queues:
            return None
        
        try:
            message = await asyncio.wait_for(
                self._queues[agent_name].get(),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def publish_event(self, event_type: str, data: Any):
        """
        发布事件
        """
        message = Message(
            type=event_type,
            sender="system",
            receiver=None,
            payload=data
        )
        
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
        
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
        
        await self.broadcast(message)
        logger.debug(f"Event '{event_type}' published")
    
    async def on_event(self, event_type: str, handler: Callable):
        """
        注册事件处理器
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Event handler registered for '{event_type}'")
    
    async def off_event(self, event_type: str, handler: Callable = None):
        """
        移除事件处理器
        """
        if handler and event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass
        elif event_type in self._event_handlers:
            del self._event_handlers[event_type]
    
    def get_history(self, limit: int = 100) -> List[dict]:
        """
        获取消息历史
        """
        return [m.to_dict() for m in self._message_history[-limit:]]
    
    async def call_agent(self, agent_name: str, request: dict, timeout: float = 60.0) -> dict:
        """
        调用代理并等待响应
        """
        correlation_id = str(__import__('uuid').uuid4())
        
        request_message = Message(
            type="request",
            sender="caller",
            receiver=agent_name,
            payload={"correlation_id": correlation_id, "request": request}
        )
        
        response_queue = asyncio.Queue()
        
        async def response_handler(msg: Message):
            if msg.type == "response" and msg.payload.get("correlation_id") == correlation_id:
                await response_queue.put(msg)
        
        await self.on_event("response", response_handler)
        
        await self.send(request_message)
        
        try:
            response = await asyncio.wait_for(response_queue.get(), timeout=timeout)
            return response.payload.get("result", {})
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from {agent_name}")
            return {"error": "timeout"}
        finally:
            await self.off_event("response", response_handler)

message_bus: Optional[MessageBus] = None

async def get_message_bus() -> MessageBus:
    global message_bus
    if message_bus is None:
        message_bus = await MessageBus.get_instance()
    return message_bus

async def publish_progress(session_id: str, step: str, status: str, progress: int, comment: str = ""):
    bus = await get_message_bus()
    await bus.publish_event("progress", {
        "session_id": session_id,
        "step": step,
        "status": status,
        "progress": progress,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat(),
    })

async def publish_task_complete(session_id: str, result: dict):
    bus = await get_message_bus()
    await bus.publish_event("task_complete", {
        "session_id": session_id,
        "result": result,
        "timestamp": datetime.utcnow().isoformat(),
    })
