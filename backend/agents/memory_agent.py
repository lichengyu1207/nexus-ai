"""
带记忆能力的代理基类
继承BaseAgent，增加长期记忆功能
"""
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from .message import AgentMessage
from ..memory_service import memory_service
import logging

logger = logging.getLogger(__name__)


class MemoryEnabledAgent(BaseAgent):
    """
    带记忆能力的代理基类
    提供长期记忆存储和检索功能
    
    Attributes:
        _memory_enabled: 是否启用记忆
        _memory_types: 支持的记忆类型
    """
    
    def __init__(
        self, 
        agent_name: str, 
        task_id: str, 
        bus, 
        memory_enabled: bool = True,
        **kwargs
    ):
        """
        初始化带记忆的代理
        
        Args:
            agent_name: 代理名称
            task_id: 任务ID
            bus: 消息总线
            memory_enabled: 是否启用记忆
            **kwargs: 其他参数
        """
        super().__init__(agent_name, task_id, bus, **kwargs)
        
        self._memory_enabled = memory_enabled
        self._memory_types = ["conversation", "knowledge", "experience"]
    
    async def store_memory(
        self,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        存储记忆
        
        Args:
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
            
        Returns:
            Optional[str]: 记忆ID
        """
        if not self._memory_enabled:
            return None
        
        memory_id = await memory_service.store_memory(
            agent_name=self.agent_name,
            memory_type=memory_type,
            content=content,
            metadata=metadata
        )
        
        logger.debug(f"Agent {self.agent_name} stored {memory_type} memory: {memory_id}")
        
        return memory_id
    
    async def recall_memories(
        self,
        query: str,
        memory_type: str = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆
        
        Args:
            query: 查询文本
            memory_type: 记忆类型过滤
            n_results: 返回结果数量
            
        Returns:
            List[Dict]: 记忆列表
        """
        if not self._memory_enabled:
            return []
        
        memories = await memory_service.search_memories(
            query=query,
            agent_name=self.agent_name,
            memory_type=memory_type,
            n_results=n_results
        )
        
        logger.debug(f"Agent {self.agent_name} recalled {len(memories)} memories")
        
        return memories
    
    async def store_conversation(
        self,
        user_input: str,
        agent_response: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        存储对话记忆
        
        Args:
            user_input: 用户输入
            agent_response: 代理响应
            context: 上下文
            
        Returns:
            str: 记忆ID
        """
        content = f"用户: {user_input}\n代理: {agent_response}"
        
        return await self.store_memory(
            memory_type="conversation",
            content=content,
            metadata={
                "user_input": user_input,
                "agent_response": agent_response,
                "task_id": self.task_id,
                **(context or {})
            }
        )
    
    async def store_knowledge(
        self,
        topic: str,
        knowledge: str,
        source: str = None
    ) -> str:
        """
        存储知识记忆
        
        Args:
            topic: 主题
            knowledge: 知识内容
            source: 来源
            
        Returns:
            str: 记忆ID
        """
        return await self.store_memory(
            memory_type="knowledge",
            content=f"{topic}: {knowledge}",
            metadata={
                "topic": topic,
                "source": source,
                "task_id": self.task_id
            }
        )
    
    async def store_experience(
        self,
        situation: str,
        action: str,
        outcome: str,
        lesson: str = None
    ) -> str:
        """
        存储经验记忆
        
        Args:
            situation: 情境描述
            action: 采取的行动
            outcome: 结果
            lesson: 经验教训
            
        Returns:
            str: 记忆ID
        """
        content = f"情境: {situation}\n行动: {action}\n结果: {outcome}"
        if lesson:
            content += f"\n教训: {lesson}"
        
        return await self.store_memory(
            memory_type="experience",
            content=content,
            metadata={
                "situation": situation,
                "outcome": outcome,
                "task_id": self.task_id
            }
        )
    
    async def get_relevant_context(self, query: str) -> str:
        """
        获取相关上下文
        
        Args:
            query: 当前查询
            
        Returns:
            str: 相关上下文文本
        """
        if not self._memory_enabled:
            return ""
        
        memories = await self.recall_memories(query, n_results=3)
        
        if not memories:
            return ""
        
        context_parts = ["相关历史记忆:"]
        for i, mem in enumerate(memories, 1):
            context_parts.append(f"{i}. {mem['content'][:200]}...")
        
        return "\n".join(context_parts)
    
    async def clear_memories(self) -> int:
        """
        清除所有记忆
        
        Returns:
            int: 清除的记忆数量
        """
        return await memory_service.clear_agent_memories(self.agent_name)
