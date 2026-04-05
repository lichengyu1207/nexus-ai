"""
智能体调度器
负责管理多个代理的生命周期
"""
import asyncio
from typing import List, Dict, Type, Optional
from .bus import MessageBus
from .base import BaseAgent
from .message import AgentMessage, MessageType
import logging

logger = logging.getLogger(__name__)


class AgentScheduler:
    """
    代理调度器
    负责创建代理实例、注册到总线、启动代理、等待任务完成
    
    Attributes:
        task_id: 任务ID
        bus: 消息总线实例
        agents: 代理字典
    
    使用示例:
        >>> scheduler = AgentScheduler("task-123")
        >>> scheduler.register_agent(RequirementAgent, "requirement")
        >>> scheduler.register_agent(CollectorAgent, "collector")
        >>> await scheduler.start_all()
        >>> # ... 执行任务 ...
        >>> await scheduler.stop_all()
    """
    
    def __init__(
        self, 
        task_id: str, 
        db_enabled: bool = True, 
        sse_enabled: bool = True
    ):
        """
        初始化调度器
        
        Args:
            task_id: 任务ID
            db_enabled: 是否启用数据库持久化
            sse_enabled: 是否启用SSE推送
        """
        self.task_id = task_id
        self.bus = MessageBus(task_id, db_enabled=db_enabled, sse_enabled=sse_enabled)
        self.agents: Dict[str, BaseAgent] = {}
        
        logger.info(f"Scheduler initialized for task {task_id}")
    
    def register_agent(
        self,
        agent_class: Type[BaseAgent],
        agent_name: str,
        **kwargs
    ) -> BaseAgent:
        """
        注册并创建代理实例
        
        Args:
            agent_class: 代理类
            agent_name: 代理名称
            **kwargs: 代理初始化参数
            
        Returns:
            BaseAgent: 创建的代理实例
        """
        agent = agent_class(agent_name, self.task_id, self.bus, **kwargs)
        self.agents[agent_name] = agent
        self.bus.register_agent(agent_name)
        
        logger.info(f"Agent {agent_name} registered")
        
        return agent
    
    async def start_all(self) -> None:
        """
        启动所有代理的消息循环（并行执行）
        """
        logger.info(f"Starting {len(self.agents)} agents in parallel")
        
        tasks = [agent.start() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
        
        logger.info("All agents started in parallel")
    
    async def stop_all(self) -> None:
        """
        停止所有代理
        """
        logger.info(f"Stopping {len(self.agents)} agents")
        
        for agent in self.agents.values():
            await agent.stop()
        
        logger.info("All agents stopped")
    
    async def wait_for_completion(self, timeout: float = 60) -> None:
        """
        等待所有代理完成任务
        
        Args:
            timeout: 超时时间（秒）
        """
        logger.info(f"Waiting for completion (timeout: {timeout}s)")
        
        await asyncio.sleep(timeout)
        
        logger.info("Wait completed")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        获取代理实例
        
        Args:
            name: 代理名称
            
        Returns:
            Optional[BaseAgent]: 代理实例
        """
        return self.agents.get(name)
    
    def get_message_history(self) -> List[AgentMessage]:
        """
        获取消息历史
        
        Returns:
            List[AgentMessage]: 消息历史列表
        """
        return self.bus.get_history()
    
    async def send_initial_message(
        self,
        recipient: str,
        content: dict
    ) -> AgentMessage:
        """
        发送初始消息给指定代理
        
        Args:
            recipient: 接收者代理名称
            content: 消息内容
            
        Returns:
            AgentMessage: 发送的消息
        """
        msg = AgentMessage(
            task_id=self.task_id,
            sender="scheduler",
            recipient=recipient,
            type=MessageType.REQUEST,
            content=content
        )
        
        await self.bus.publish(msg)
        
        logger.info(f"Initial message sent to {recipient}")
        
        return msg
    
    def get_status(self) -> dict:
        """
        获取调度器状态
        
        Returns:
            dict: 状态信息
        """
        return {
            "task_id": self.task_id,
            "agents": list(self.agents.keys()),
            "message_count": len(self.bus.get_history()),
            "registered_agents": self.bus.get_registered_agents()
        }
