"""
AgentBus - 代理间消息总线系统
负责代理间的消息路由、存储和分发
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime
import uuid
import asyncio
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举"""
    REQUEST = "REQUEST"      # 请求信息或操作
    RESPONSE = "RESPONSE"    # 回复请求
    NOTIFY = "NOTIFY"        # 通知状态变更
    DEBATE = "DEBATE"        # 辩论观点


class AgentMessage:
    """代理消息类"""
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        task_id: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.task_id = task_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.type = message_type
        self.content = content
        self.created_at = datetime.utcnow()
        self.read_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "type": self.type.value if isinstance(self.type, MessageType) else self.type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }
    
    def mark_as_read(self):
        """标记为已读"""
        self.read_at = datetime.utcnow()


class AgentBus:
    """
    代理总线 - 单例模式
    负责管理代理间的消息路由和存储
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化消息总线"""
        if self._initialized:
            return
        
        self._initialized = True
        # 消息队列：{task_id: {agent_name: [messages]}}
        self._message_queues: Dict[str, Dict[str, List[AgentMessage]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # 代理注册表：{task_id: {agent_name: agent_instance}}
        self._agent_registry: Dict[str, Dict[str, Any]] = defaultdict(dict)
        # 消息存储（用于持久化和查询）
        self._message_store: Dict[str, List[AgentMessage]] = defaultdict(list)
        # 事件循环引用
        self._loop = asyncio.get_event_loop()
    
    def register(self, task_id: str, agent_name: str, agent_instance: Any) -> None:
        """
        注册代理到总线
        
        Args:
            task_id: 任务ID
            agent_name: 代理名称
            agent_instance: 代理实例
        """
        self._agent_registry[task_id][agent_name] = agent_instance
        # 初始化消息队列
        if agent_name not in self._message_queues[task_id]:
            self._message_queues[task_id][agent_name] = []
    
    def unregister(self, task_id: str, agent_name: str) -> None:
        """
        从总线注销代理
        
        Args:
            task_id: 任务ID
            agent_name: 代理名称
        """
        if task_id in self._agent_registry:
            self._agent_registry[task_id].pop(agent_name, None)
    
    async def send(
        self,
        task_id: str,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        content: Dict[str, Any]
    ) -> AgentMessage:
        """
        发送消息
        
        Args:
            task_id: 任务ID
            from_agent: 发送方代理名称
            to_agent: 接收方代理名称
            message_type: 消息类型
            content: 消息内容
            
        Returns:
            AgentMessage: 创建的消息对象
        """
        # 创建消息
        message = AgentMessage(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        
        # 添加到接收方的消息队列
        self._message_queues[task_id][to_agent].append(message)
        
        # 添加到消息存储
        self._message_store[task_id].append(message)
        
        # 触发接收方代理的消息处理（如果已注册）
        if to_agent in self._agent_registry[task_id]:
            agent = self._agent_registry[task_id][to_agent]
            if hasattr(agent, 'on_message_received'):
                # 异步调用代理的消息处理方法
                asyncio.create_task(agent.on_message_received(message))
        
        return message
    
    def get_messages(
        self,
        task_id: str,
        agent_name: Optional[str] = None,
        since: Optional[datetime] = None,
        unread_only: bool = False
    ) -> List[AgentMessage]:
        """
        获取消息列表
        
        Args:
            task_id: 任务ID
            agent_name: 代理名称（可选，不指定则返回所有消息）
            since: 获取此时间之后的消息
            unread_only: 是否只返回未读消息
            
        Returns:
            List[AgentMessage]: 消息列表
        """
        if agent_name:
            # 获取特定代理的消息
            messages = self._message_queues[task_id].get(agent_name, [])
        else:
            # 获取任务的所有消息
            messages = self._message_store.get(task_id, [])
        
        # 过滤条件
        filtered_messages = []
        for msg in messages:
            # 时间过滤
            if since and msg.created_at < since:
                continue
            
            # 未读过滤
            if unread_only and msg.read_at is not None:
                continue
            
            filtered_messages.append(msg)
        
        return filtered_messages
    
    def mark_messages_as_read(self, task_id: str, agent_name: str) -> int:
        """
        标记代理的所有消息为已读
        
        Args:
            task_id: 任务ID
            agent_name: 代理名称
            
        Returns:
            int: 标记为已读的消息数量
        """
        messages = self._message_queues[task_id].get(agent_name, [])
        count = 0
        for msg in messages:
            if msg.read_at is None:
                msg.mark_as_read()
                count += 1
        return count
    
    def get_unread_count(self, task_id: str, agent_name: str) -> int:
        """
        获取未读消息数量
        
        Args:
            task_id: 任务ID
            agent_name: 代理名称
            
        Returns:
            int: 未读消息数量
        """
        messages = self._message_queues[task_id].get(agent_name, [])
        return sum(1 for msg in messages if msg.read_at is None)
    
    def clear_task_messages(self, task_id: str) -> None:
        """
        清除任务的所有消息
        
        Args:
            task_id: 任务ID
        """
        self._message_queues.pop(task_id, None)
        self._message_store.pop(task_id, None)
    
    def get_conversation_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务的对话历史（按时间排序）
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict]: 对话历史列表
        """
        messages = self._message_store.get(task_id, [])
        # 按时间排序
        sorted_messages = sorted(messages, key=lambda m: m.created_at)
        return [msg.to_dict() for msg in sorted_messages]


# 全局单例实例
agent_bus = AgentBus()
