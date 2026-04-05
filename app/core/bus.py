"""
内存消息总线
实现代理间的消息传递和路由
"""
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional
from app.core.message import AgentMessage, MessageHistory


class MessageBus:
    """
    消息总线
    每个任务独立的消息总线，管理代理间的消息传递
    """
    
    def __init__(self, task_id: str):
        """
        初始化消息总线
        
        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        self._queues: Dict[str, asyncio.Queue] = {}  # agent_name -> queue
        self._history = MessageHistory()  # 消息历史记录
        self._registered_agents: List[str] = []  # 已注册的代理列表
    
    def register_agent(self, agent_name: str) -> None:
        """
        代理注册自己的消息队列
        
        Args:
            agent_name: 代理名称
        """
        if agent_name not in self._queues:
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
        发布消息到指定代理或广播
        
        Args:
            message: 消息对象
        """
        # 记录到历史
        self._history.add(message)
        
        if message.is_broadcast():
            # 广播给所有代理
            for agent_name, queue in self._queues.items():
                if agent_name != message.sender:  # 不发给自己
                    await queue.put(message)
        else:
            # 点对点发送
            queue = self._queues.get(message.recipient)
            if queue:
                await queue.put(message)
            else:
                raise ValueError(f"Agent {message.recipient} not registered")
    
    async def subscribe(self, agent_name: str) -> asyncio.Queue:
        """
        代理获取自己的消息队列
        
        Args:
            agent_name: 代理名称
            
        Returns:
            asyncio.Queue: 消息队列
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
        """
        queue = self._queues.get(agent_name)
        if not queue:
            raise ValueError(f"Agent {agent_name} not registered")
        
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
        获取消息历史
        
        Returns:
            List[AgentMessage]: 消息历史列表
        """
        return self._history.get_all()
    
    def get_registered_agents(self) -> List[str]:
        """
        获取已注册的代理列表
        
        Returns:
            List[str]: 代理名称列表
        """
        return self._registered_agents.copy()
    
    def clear(self) -> None:
        """清空消息队列和历史"""
        for queue in self._queues.values():
            while not queue.empty():
                queue.get_nowait()
        
        self._history.clear()


class MessageBusManager:
    """
    消息总线管理器
    管理所有任务的消息总线
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化消息总线管理器"""
        if self._initialized:
            return
        
        self._buses: Dict[str, MessageBus] = {}
        self._initialized = True
    
    def create_bus(self, task_id: str) -> MessageBus:
        """
        创建任务的消息总线
        
        Args:
            task_id: 任务ID
            
        Returns:
            MessageBus: 消息总线实例
        """
        if task_id not in self._buses:
            self._buses[task_id] = MessageBus(task_id)
        
        return self._buses[task_id]
    
    def get_bus(self, task_id: str) -> Optional[MessageBus]:
        """
        获取任务的消息总线
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[MessageBus]: 消息总线实例
        """
        return self._buses.get(task_id)
    
    def remove_bus(self, task_id: str) -> None:
        """
        移除任务的消息总线
        
        Args:
            task_id: 任务ID
        """
        if task_id in self._buses:
            self._buses[task_id].clear()
            del self._buses[task_id]
    
    def get_all_tasks(self) -> List[str]:
        """
        获取所有任务ID
        
        Returns:
            List[str]: 任务ID列表
        """
        return list(self._buses.keys())


# 全局消息总线管理器实例
message_bus_manager = MessageBusManager()
