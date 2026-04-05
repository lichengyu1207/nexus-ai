"""
智能体基类 - 包含心跳上报功能
支持异步和同步两种实现方式
"""
import asyncio
import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    智能体基类
    提供心跳上报功能，支持异步和同步两种模式
    """
    
    def __init__(
        self,
        agent_id: str,
        redis_url: str = "redis://localhost:6379/0",
        heartbeat_interval: int = 5,
        heartbeat_ttl: int = 15,
    ):
        """
        初始化智能体基类
        
        Args:
            agent_id: 智能体唯一标识
            redis_url: Redis 连接字符串
            heartbeat_interval: 心跳间隔（秒）
            heartbeat_ttl: 心跳数据 TTL（秒）
        """
        self.agent_id = agent_id
        self.redis_url = redis_url
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_ttl = heartbeat_ttl
        
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._heartbeat_timer: Optional[threading.Timer] = None
        self._stop_heartbeat_flag = threading.Event()
        
        self._process = psutil.Process(os.getpid())
        self._tasks: List[Any] = []
        self._is_async = True
    
    def get_current_tasks_count(self) -> int:
        """获取当前任务数量"""
        return len(self._tasks)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        采集系统指标
        
        Returns:
            包含 CPU、内存等指标的字典
        """
        try:
            cpu_percent = self._process.cpu_percent(interval=0.1)
            memory_percent = self._process.memory_percent()
        except psutil.NoSuchProcess:
            cpu_percent = 0.0
            memory_percent = 0.0
        
        return {
            "agent_id": self.agent_id,
            "pid": os.getpid(),
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "current_tasks": self.get_current_tasks_count(),
            "timestamp": time.time(),
        }
    
    async def start_heartbeat_async(self) -> None:
        """
        启动异步心跳任务
        """
        if self._heartbeat_task is not None:
            logger.warning(f"Heartbeat already running for agent {self.agent_id}")
            return
        
        self._is_async = True
        self._stop_event.clear()
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop_async()
        )
        logger.info(f"Async heartbeat started for agent {self.agent_id}")
    
    async def stop_heartbeat_async(self) -> None:
        """
        停止异步心跳任务
        """
        if self._heartbeat_task is None:
            return
        
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._heartbeat_task, timeout=2)
        except asyncio.TimeoutError:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        self._heartbeat_task = None
        logger.info(f"Async heartbeat stopped for agent {self.agent_id}")
    
    async def _heartbeat_loop_async(self) -> None:
        """
        异步心跳循环
        """
        try:
            import redis.asyncio as redis
        except ImportError:
            logger.error("redis.asyncio not available, install redis-py with async support")
            return
        
        redis_client = None
        try:
            redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            
            while not self._stop_event.is_set():
                try:
                    await self._send_heartbeat_async(redis_client)
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.heartbeat_interval
                    )
                    break
                except asyncio.TimeoutError:
                    pass
        finally:
            if redis_client:
                await redis_client.close()
    
    async def _send_heartbeat_async(self, redis_client) -> None:
        """
        异步发送心跳
        
        Args:
            redis_client: Redis 异步客户端
        """
        metrics = self.collect_metrics()
        key = f"agent:{self.agent_id}:heartbeat"
        
        await redis_client.setex(
            key,
            self.heartbeat_ttl,
            json.dumps(metrics)
        )
        logger.debug(f"Heartbeat sent for agent {self.agent_id}: {metrics}")
    
    def start_heartbeat_sync(self) -> None:
        """
        启动同步心跳任务
        """
        if self._heartbeat_timer is not None:
            logger.warning(f"Heartbeat already running for agent {self.agent_id}")
            return
        
        self._is_async = False
        self._stop_heartbeat_flag.clear()
        self._heartbeat_loop_sync()
        logger.info(f"Sync heartbeat started for agent {self.agent_id}")
    
    def _heartbeat_loop_sync(self) -> None:
        """
        同步心跳循环
        """
        if self._stop_heartbeat_flag.is_set():
            return
        
        try:
            self._send_heartbeat_sync()
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
        
        self._heartbeat_timer = threading.Timer(
            self.heartbeat_interval,
            self._heartbeat_loop_sync
        )
        self._heartbeat_timer.daemon = True
        self._heartbeat_timer.start()
    
    def _send_heartbeat_sync(self) -> None:
        """
        同步发送心跳
        """
        import redis
        
        metrics = self.collect_metrics()
        key = f"agent:{self.agent_id}:heartbeat"
        
        client = redis.from_url(self.redis_url)
        try:
            client.setex(key, self.heartbeat_ttl, json.dumps(metrics))
            logger.debug(f"Heartbeat sent for agent {self.agent_id}: {metrics}")
        finally:
            client.close()
    
    def stop_heartbeat_sync(self) -> None:
        """
        停止同步心跳任务
        """
        self._stop_heartbeat_flag.set()
        if self._heartbeat_timer:
            self._heartbeat_timer.cancel()
            self._heartbeat_timer = None
        logger.info(f"Sync heartbeat stopped for agent {self.agent_id}")
    
    def start_heartbeat(self) -> None:
        """启动心跳（自动检测异步/同步模式）"""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.start_heartbeat_async())
        except RuntimeError:
            self.start_heartbeat_sync()
    
    def stop_heartbeat(self) -> None:
        """停止心跳"""
        if self._is_async and self._heartbeat_task:
            asyncio.create_task(self.stop_heartbeat_async())
        elif self._heartbeat_timer:
            self.stop_heartbeat_sync()
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行智能体任务（子类实现）"""
        pass
