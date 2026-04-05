"""
兵部智能体 - 示例实现
继承 BaseAgent 并启用心跳上报
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from ..config.settings import settings

logger = logging.getLogger(__name__)


class BingAgent(BaseAgent):
    """
    兵部智能体
    负责房产数据采集和初步分析
    """
    
    def __init__(
        self,
        agent_id: str = "bing_001",
        redis_url: Optional[str] = None,
        heartbeat_interval: Optional[int] = None,
        heartbeat_ttl: Optional[int] = None,
    ):
        """
        初始化兵部智能体
        
        Args:
            agent_id: 智能体唯一标识
            redis_url: Redis 连接字符串
            heartbeat_interval: 心跳间隔（秒）
            heartbeat_ttl: 心跳数据 TTL（秒）
        """
        super().__init__(
            agent_id=agent_id,
            redis_url=redis_url or settings.redis_url,
            heartbeat_interval=heartbeat_interval or settings.heartbeat_interval,
            heartbeat_ttl=heartbeat_ttl or settings.heartbeat_ttl,
        )
        
        self._tasks: List[Dict[str, Any]] = []
        self._is_running = False
        logger.info(f"BingAgent {self.agent_id} initialized")
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """
        添加任务
        
        Args:
            task: 任务数据
        """
        self._tasks.append(task)
        logger.debug(f"Task added to agent {self.agent_id}: {task.get('id', 'unknown')}")
    
    def remove_task(self, task_id: str) -> None:
        """
        移除任务
        
        Args:
            task_id: 任务 ID
        """
        self._tasks = [t for t in self._tasks if t.get("id") != task_id]
        logger.debug(f"Task removed from agent {self.agent_id}: {task_id}")
    
    def get_current_tasks_count(self) -> int:
        """获取当前任务数量"""
        return len(self._tasks)
    
    async def start(self) -> None:
        """启动智能体"""
        if self._is_running:
            logger.warning(f"BingAgent {self.agent_id} is already running")
            return
        
        self._is_running = True
        await self.start_heartbeat_async()
        logger.info(f"BingAgent {self.agent_id} started with heartbeat")
    
    async def stop(self) -> None:
        """停止智能体"""
        if not self._is_running:
            return
        
        self._is_running = False
        await self.stop_heartbeat_async()
        self._tasks.clear()
        logger.info(f"BingAgent {self.agent_id} stopped")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务数据
            
        Returns:
            执行结果
        """
        self.add_task(task)
        
        try:
            result = await self._process_task(task)
            return result
        finally:
            self.remove_task(task.get("id", ""))
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务（模拟实现）
        
        Args:
            task: 任务数据
            
        Returns:
            处理结果
        """
        await asyncio.sleep(0.1)
        
        return {
            "task_id": task.get("id"),
            "status": "completed",
            "result": f"Processed by BingAgent {self.agent_id}",
        }
    
    def __repr__(self) -> str:
        return f"BingAgent(agent_id={self.agent_id}, tasks={len(self._tasks)})"


class HubuAgent(BaseAgent):
    """
    户部智能体
    负责用户管理和权限控制
    """
    
    def __init__(
        self,
        agent_id: str = "hubu_001",
        redis_url: Optional[str] = None,
        heartbeat_interval: Optional[int] = None,
        heartbeat_ttl: Optional[int] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            redis_url=redis_url or settings.redis_url,
            heartbeat_interval=heartbeat_interval or settings.heartbeat_interval,
            heartbeat_ttl=heartbeat_ttl or settings.heartbeat_ttl,
        )
        
        self._tasks: List[Dict[str, Any]] = []
        logger.info(f"HubuAgent {self.agent_id} initialized")
    
    def get_current_tasks_count(self) -> int:
        return len(self._tasks)
    
    async def start(self) -> None:
        await self.start_heartbeat_async()
        logger.info(f"HubuAgent {self.agent_id} started")
    
    async def stop(self) -> None:
        await self.stop_heartbeat_async()
        self._tasks.clear()
        logger.info(f"HubuAgent {self.agent_id} stopped")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self._tasks.append(task)
        try:
            await asyncio.sleep(0.05)
            return {
                "task_id": task.get("id"),
                "status": "completed",
                "result": f"Processed by HubuAgent {self.agent_id}",
            }
        finally:
            self._tasks = [t for t in self._tasks if t.get("id") != task.get("id")]


class LibuAgent(BaseAgent):
    """
    礼部智能体
    负责通知和消息推送
    """
    
    def __init__(
        self,
        agent_id: str = "libu_001",
        redis_url: Optional[str] = None,
        heartbeat_interval: Optional[int] = None,
        heartbeat_ttl: Optional[int] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            redis_url=redis_url or settings.redis_url,
            heartbeat_interval=heartbeat_interval or settings.heartbeat_interval,
            heartbeat_ttl=heartbeat_ttl or settings.heartbeat_ttl,
        )
        
        self._tasks: List[Dict[str, Any]] = []
        logger.info(f"LibuAgent {self.agent_id} initialized")
    
    def get_current_tasks_count(self) -> int:
        return len(self._tasks)
    
    async def start(self) -> None:
        await self.start_heartbeat_async()
        logger.info(f"LibuAgent {self.agent_id} started")
    
    async def stop(self) -> None:
        await self.stop_heartbeat_async()
        self._tasks.clear()
        logger.info(f"LibuAgent {self.agent_id} stopped")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self._tasks.append(task)
        try:
            await asyncio.sleep(0.02)
            return {
                "task_id": task.get("id"),
                "status": "completed",
                "result": f"Processed by LibuAgent {self.agent_id}",
            }
        finally:
            self._tasks = [t for t in self._tasks if t.get("id") != task.get("id")]
