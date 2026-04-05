from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import uuid
import asyncio
from app.ai_agents.event_system import (
    event_manager, AgentStartEvent, AgentProgressEvent, AgentCompleteEvent, AgentErrorEvent
)
from app.ai_agents.bus import agent_bus, MessageType
from app.ai_agents.memory import memory_service
from app.ai_agents.debate import debate_manager


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", self.__class__.__name__)
        self.description = kwargs.get("description", "")
        self.timeout = kwargs.get("timeout", 300)
        self.max_retries = kwargs.get("max_retries", 3)
        self.agent_id = str(uuid.uuid4())
        self.bus = kwargs.get("bus", agent_bus)  # 注入消息总线
        self.task_id: Optional[str] = None  # 当前任务ID
        self._message_handlers: Dict[str, Any] = {}  # 消息处理器
        
        # 初始化风格配置
        self.style: Dict[str, Any] = kwargs.get("style_config", {})
        
        # 初始化记忆服务
        self._memory_collection = memory_service.get_or_create_collection(self.name)
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task"""
        pass
    
    async def initialize(self) -> None:
        """Initialize the agent"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get the agent's status"""
        return {
            "name": self.name,
            "description": self.description,
            "status": "ready",
            "agent_id": self.agent_id
        }
    
    def publish_start_event(self, task: Dict[str, Any]):
        """Publish agent start event"""
        event = AgentStartEvent(self.agent_id, self.name, task)
        event_manager.publish(event)
    
    def publish_progress_event(self, progress: float, message: str):
        """Publish agent progress event"""
        event = AgentProgressEvent(self.agent_id, self.name, progress, message)
        event_manager.publish(event)
    
    def publish_complete_event(self, result: Dict[str, Any]):
        """Publish agent complete event"""
        event = AgentCompleteEvent(self.agent_id, self.name, result)
        event_manager.publish(event)
    
    def publish_error_event(self, error: str):
        """Publish agent error event"""
        event = AgentErrorEvent(self.agent_id, self.name, error)
        event_manager.publish(event)
    
    # ========== 消息通信功能 ==========
    
    async def send_message(
        self,
        to_agent: str,
        message_type: MessageType,
        content: Dict[str, Any]
    ) -> None:
        """
        发送消息给其他代理
        
        Args:
            to_agent: 接收方代理名称
            message_type: 消息类型
            content: 消息内容
        """
        if not self.task_id:
            raise ValueError("Task ID not set. Cannot send message.")
        
        await self.bus.send(
            task_id=self.task_id,
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        
        # 发布消息发送事件
        self.publish_progress_event(0.1, f"发送消息给 {to_agent}: {message_type.value}")
    
    async def wait_for_message(
        self,
        timeout: float = 30.0,
        message_type: Optional[MessageType] = None,
        from_agent: Optional[str] = None
    ) -> Optional[Any]:
        """
        等待特定消息
        
        Args:
            timeout: 超时时间（秒）
            message_type: 期望的消息类型（可选）
            from_agent: 期望的发送方代理（可选）
            
        Returns:
            AgentMessage: 接收到的消息，超时返回None
        """
        if not self.task_id:
            raise ValueError("Task ID not set. Cannot wait for message.")
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 获取未读消息
            messages = self.bus.get_messages(
                task_id=self.task_id,
                agent_name=self.name,
                unread_only=True
            )
            
            # 过滤消息
            for msg in messages:
                # 类型过滤
                if message_type and msg.type != message_type:
                    continue
                
                # 发送方过滤
                if from_agent and msg.from_agent != from_agent:
                    continue
                
                # 找到匹配的消息
                msg.mark_as_read()
                return msg
            
            # 检查超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                return None
            
            # 短暂等待后重试
            await asyncio.sleep(0.1)
    
    async def on_message_received(self, message: Any) -> None:
        """
        接收到消息时的回调方法
        
        Args:
            message: 接收到的消息
        """
        # 默认实现：记录日志
        self.publish_progress_event(0.1, f"收到来自 {message.from_agent} 的消息: {message.type.value}")
        
        # 调用注册的消息处理器
        handler_key = f"{message.type.value}_{message.from_agent}"
        if handler_key in self._message_handlers:
            await self._message_handlers[handler_key](message)
        elif message.type.value in self._message_handlers:
            await self._message_handlers[message.type.value](message)
    
    def register_message_handler(
        self,
        message_type: str,
        handler: Any,
        from_agent: Optional[str] = None
    ) -> None:
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数
            from_agent: 发送方代理（可选）
        """
        if from_agent:
            key = f"{message_type}_{from_agent}"
        else:
            key = message_type
        
        self._message_handlers[key] = handler
    
    def get_unread_messages(self) -> List[Any]:
        """
        获取所有未读消息
        
        Returns:
            List[AgentMessage]: 未读消息列表
        """
        if not self.task_id:
            return []
        
        return self.bus.get_messages(
            task_id=self.task_id,
            agent_name=self.name,
            unread_only=True
        )
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Returns:
            List[Dict]: 对话历史列表
        """
        if not self.task_id:
            return []
        
        return self.bus.get_conversation_history(self.task_id)
    
    # ========== 记忆功能 ==========
    
    async def remember(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储当前步骤的关键信息到长期记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据（可选）
            
        Returns:
            str: 记忆ID
        """
        # 添加任务ID到元数据
        if metadata is None:
            metadata = {}
        
        if self.task_id:
            metadata["task_id"] = self.task_id
        
        # 存储记忆
        memory_id = memory_service.add_memory(
            agent_name=self.name,
            content=content,
            metadata=metadata
        )
        
        # 发布进度事件
        self.publish_progress_event(0.1, f"存储记忆: {content[:50]}...")
        
        return memory_id
    
    async def recall(
        self,
        query: str,
        n: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        从长期记忆中检索相关信息
        
        Args:
            query: 查询文本
            n: 返回结果数量
            where_filter: 元数据过滤条件（可选）
            
        Returns:
            List[Dict]: 相关记忆列表
        """
        # 检索记忆
        memories = memory_service.search_memories(
            agent_name=self.name,
            query=query,
            n_results=n,
            where_filter=where_filter
        )
        
        # 发布进度事件
        if memories:
            self.publish_progress_event(0.1, f"回忆起 {len(memories)} 条相关记忆")
        
        return memories
    
    def get_memory_count(self) -> int:
        """
        获取记忆数量
        
        Returns:
            int: 记忆数量
        """
        return memory_service.get_memory_count(self.name)
    
    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取所有记忆
        
        Args:
            limit: 最大返回数量
            
        Returns:
            List[Dict]: 记忆列表
        """
        return memory_service.get_all_memories(self.name, limit)
    
    def clear_memories(self) -> int:
        """
        清空所有记忆
        
        Returns:
            int: 删除的记忆数量
        """
        return memory_service.delete_memories(self.name)
    
    # ========== 辩论功能 ==========
    
    async def raise_disagreement(
        self,
        topic: str,
        opposing_agent: str,
        description: str = ""
    ) -> Optional[str]:
        """
        提出分歧点，触发辩论
        
        Args:
            topic: 分歧主题
            opposing_agent: 对立代理名称
            description: 分歧描述
            
        Returns:
            str: 辩论会话ID
        """
        if not self.task_id:
            raise ValueError("Task ID not set. Cannot raise disagreement.")
        
        # 创建辩论会话
        session = debate_manager.start_debate(
            task_id=self.task_id,
            topic=topic,
            participants=[self.name, opposing_agent]
        )
        
        # 发布进度事件
        self.publish_progress_event(0.1, f"提出分歧点：{topic}")
        
        # 发送辩论请求消息
        await self.send_message(
            to_agent=opposing_agent,
            message_type=MessageType.DEBATE,
            content={
                "session_id": session.id,
                "topic": topic,
                "description": description
            }
        )
        
        return session.id
    
    async def participate_in_debate(
        self,
        session_id: str,
        content: str
    ) -> bool:
        """
        参与辩论，添加发言
        
        Args:
            session_id: 辩论会话ID
            content: 发言内容
            
        Returns:
            bool: 是否成功
        """
        turn = debate_manager.add_turn(
            session_id=session_id,
            agent_name=self.name,
            content=content
        )
        
        if turn:
            # 发布进度事件
            self.publish_progress_event(0.1, f"参与辩论发言")
            
            # 存储辩论记忆
            await self.remember(
                content=f"辩论发言：{content}",
                metadata={"type": "debate", "session_id": session_id}
            )
            
            return True
        
        return False
    
    def get_debate_transcript(self, session_id: str) -> Dict[str, Any]:
        """
        获取辩论记录
        
        Args:
            session_id: 辩论会话ID
            
        Returns:
            Dict: 辩论记录
        """
        return debate_manager.get_transcript(session_id)
    
    def get_task_debates(self) -> List[Dict[str, Any]]:
        """
        获取当前任务的所有辩论记录
        
        Returns:
            List[Dict]: 辩论记录列表
        """
        if not self.task_id:
            return []
        
        return debate_manager.get_all_transcripts(self.task_id)