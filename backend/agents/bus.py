"""
内存消息总线
实现代理间的消息传递和路由
支持异步持久化到数据库和SSE实时推送
"""
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional
from .message import AgentMessage
import logging

logger = logging.getLogger(__name__)


class MessageBus:
    """
    消息总线类
    每个任务独立的消息总线，管理代理间的消息传递
    
    Attributes:
        task_id: 任务ID
        _queues: 代理消息队列字典
        _history: 消息历史记录
        _registered_agents: 已注册的代理列表
        _db_enabled: 是否启用数据库持久化
        _sse_enabled: 是否启用SSE推送
    
    使用示例:
        >>> bus = MessageBus("task-123")
        >>> bus.register_agent("data_collector")
        >>> bus.register_agent("market_analyst")
        >>> 
        >>> # 发送消息
        >>> msg = AgentMessage(
        ...     task_id="task-123",
        ...     sender="data_collector",
        ...     recipient="market_analyst",
        ...     type=MessageType.REQUEST,
        ...     content={"query": "需要数据"}
        ... )
        >>> await bus.publish(msg)
        >>> 
        >>> # 接收消息
        >>> queue = await bus.subscribe("market_analyst")
        >>> received_msg = await queue.get()
    """
    
    def __init__(self, task_id: str, db_enabled: bool = True, sse_enabled: bool = True):
        """
        初始化消息总线
        
        Args:
            task_id: 任务ID
            db_enabled: 是否启用数据库持久化
            sse_enabled: 是否启用SSE推送
        """
        self.task_id = task_id
        self._queues: Dict[str, asyncio.Queue] = {}
        self._history: List[AgentMessage] = []
        self._registered_agents: List[str] = []
        self._db_enabled = db_enabled
        self._sse_enabled = sse_enabled
    
    def register_agent(self, agent_name: str) -> None:
        """
        为代理创建消息队列
        
        Args:
            agent_name: 代理名称
            
        Raises:
            ValueError: 如果代理已经注册
        """
        if agent_name in self._queues:
            raise ValueError(f"Agent {agent_name} already registered")
        
        self._queues[agent_name] = asyncio.Queue()
        self._registered_agents.append(agent_name)
    
    def unregister_agent(self, agent_name: str) -> None:
        """
        注销代理
        
        Args:
            agent_name: 代理名称
        """
        if agent_name in self._queues:
            del self._queues[agent_name]
            self._registered_agents.remove(agent_name)
    
    async def publish(self, message: AgentMessage) -> None:
        """
        将消息放入目标队列
        若recipient为None则放入所有队列（广播）
        同时异步存入数据库和推送SSE
        
        Args:
            message: 消息对象
            
        Raises:
            ValueError: 如果目标代理未注册
        """
        self._history.append(message)
        
        if message.is_broadcast():
            for agent_name, queue in self._queues.items():
                if agent_name != message.sender:
                    await queue.put(message)
        else:
            if message.recipient not in self._queues:
                logger.warning(f"Agent {message.recipient} not registered, message will be stored in history only")
                self._history.append(message)
                if self._db_enabled:
                    asyncio.create_task(self._save_to_db(message))
                if self._sse_enabled:
                    asyncio.create_task(self._broadcast_sse(message))
                return
            
            queue = self._queues[message.recipient]
            await queue.put(message)
        
        if self._db_enabled:
            asyncio.create_task(self._save_to_db(message))
        
        if self._sse_enabled:
            asyncio.create_task(self._broadcast_sse(message))
    
    async def _save_to_db(self, message: AgentMessage) -> None:
        """
        异步保存消息到数据库
        
        Args:
            message: 消息对象
        """
        try:
            from ..database import AgentMessageDB
            
            await AgentMessageDB.save_message(
                id=message.id,
                task_id=message.task_id,
                sender=message.sender,
                recipient=message.recipient,
                msg_type=message.type.value if hasattr(message.type, 'value') else str(message.type),
                content=message.content,
                in_reply_to=message.in_reply_to,
                timestamp=message.timestamp.isoformat() if message.timestamp else None
            )
            
            logger.debug(f"Message {message.id} saved to database")
        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")
    
    async def _broadcast_sse(self, message: AgentMessage) -> None:
        """
        通过SSE广播消息
        
        Args:
            message: 消息对象
        """
        try:
            from ..sse_manager import sse_manager, SSEEvent
            
            if message.content and message.content.get('event') == 'step':
                step_data = message.content.get('step', {})
                event = SSEEvent(
                    event="step",
                    data=step_data,
                    id=step_data.get('id')
                )
                await sse_manager.broadcast(self.task_id, event)
            else:
                await sse_manager.broadcast_message(
                    task_id=self.task_id,
                    message=message.to_dict()
                )
            
            logger.debug(f"Message {message.id} broadcasted via SSE")
        except Exception as e:
            logger.error(f"Failed to broadcast message via SSE: {e}")
    
    async def subscribe(self, agent_name: str) -> asyncio.Queue:
        """
        返回该代理的消息队列
        
        Args:
            agent_name: 代理名称
            
        Returns:
            asyncio.Queue: 消息队列
            
        Raises:
            ValueError: 如果代理未注册
        """
        if agent_name not in self._queues:
            raise ValueError(f"Agent {agent_name} not registered")
        
        return self._queues[agent_name]
    
    async def receive(
        self,
        agent_name: str,
        timeout: Optional[float] = None
    ) -> Optional[AgentMessage]:
        """
        接收消息（阻塞或超时）
        
        Args:
            agent_name: 代理名称
            timeout: 超时时间（秒），None表示永久等待
            
        Returns:
            Optional[AgentMessage]: 接收到的消息，超时返回None
            
        Raises:
            ValueError: 如果代理未注册
        """
        if agent_name not in self._queues:
            raise ValueError(f"Agent {agent_name} not registered")
        
        queue = self._queues[agent_name]
        
        try:
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()
            
            return message
        except asyncio.TimeoutError:
            return None
    
    def get_history(self) -> List[AgentMessage]:
        """
        返回所有消息记录
        
        Returns:
            List[AgentMessage]: 消息历史列表
        """
        return self._history.copy()
    
    def get_registered_agents(self) -> List[str]:
        """
        获取已注册的代理列表
        
        Returns:
            List[str]: 代理名称列表
        """
        return self._registered_agents.copy()
    
    def get_queue_size(self, agent_name: str) -> int:
        """
        获取代理队列中的消息数量
        
        Args:
            agent_name: 代理名称
            
        Returns:
            int: 消息数量
        """
        if agent_name not in self._queues:
            return 0
        
        return self._queues[agent_name].qsize()
    
    def clear(self) -> None:
        """
        清空消息队列和历史
        """
        for queue in self._queues.values():
            while not queue.empty():
                queue.get_nowait()
        
        self._history.clear()
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 总线信息
        """
        return f"MessageBus(task_id={self.task_id}, agents={len(self._registered_agents)}, messages={len(self._history)})"
