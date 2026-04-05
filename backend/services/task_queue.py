# -*- coding: utf-8 -*-
"""
TaskQueue - 持久化任务队列
支持优先级、重试、状态追踪
"""
import asyncio
import heapq
import time
import uuid
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from backend.database_pg import PostgreSQLConnectionPool

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=True)
class PrioritizedTask:
    priority: int
    created_at: float = field(compare=True)
    task_id: str = field(compare=False)
    task_data: Dict = field(compare=False, default_factory=dict)


class TaskQueue:
    """
    持久化任务队列
    
    Features:
    - 优先级队列 (heapq)
    - 持久化存储 (PostgreSQL)
    - 自动重试机制
    - 状态追踪
    - 并发控制
    """
    
    _instance: Optional['TaskQueue'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._queue: List[PrioritizedTask] = []
        self._processing: Dict[str, PrioritizedTask] = {}
        self._counter = 0
        self._db = None
        self._initialized = False
        self._handlers: Dict[str, Callable] = {}
    
    @classmethod
    async def get_instance(cls) -> 'TaskQueue':
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        if self._initialized:
            return
        self._db = await PostgreSQLConnectionPool.get_instance()
        await self._load_pending_tasks()
        self._initialized = True
        logger.info(f"TaskQueue initialized with {len(self._queue)} pending tasks")
    
    def register_handler(self, task_type: str, handler: Callable):
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def _load_pending_tasks(self):
        """从数据库加载待处理任务"""
        async with self._db.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT id, task_id, priority
                FROM task_queue
                WHERE status = $1
                ORDER BY priority DESC, created_at ASC
            """, TaskStatus.PENDING.value)
            
            for row in rows:
                task = PrioritizedTask(
                    priority=-row['priority'],
                    created_at=time.time(),
                    task_id=str(row['task_id']),
                    task_data={
                        'queue_id': str(row['id']),
                    }
                )
                heapq.heappush(self._queue, task)
    
    def start(self):
        """启动任务队列（同步版本，兼容旧代码）"""
        logger.info("TaskQueue started (no-op for persistent queue)")
    
    def stop(self):
        """停止任务队列（同步版本，兼容旧代码）"""
        logger.info("TaskQueue stopped (no-op for persistent queue)")
    
    async def enqueue(
        self, 
        task_id: str, 
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        将任务加入队列
        
        Args:
            task_id: 任务ID
            priority: 优先级 (0-10, 数字越大优先级越高)
            scheduled_at: 计划执行时间
            metadata: 额外元数据
        
        Returns:
            queue_id: 队列记录ID
        """
        queue_id = str(uuid.uuid4())
        
        async with self._db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO task_queue (id, task_id, priority, status, scheduled_at)
                VALUES ($1, $2, $3, $4, $5)
            """, queue_id, task_id, priority, TaskStatus.PENDING.value, scheduled_at)
        
        task = PrioritizedTask(
            priority=-priority,
            created_at=time.time(),
            task_id=task_id,
            task_data={'queue_id': queue_id, **(metadata or {})}
        )
        heapq.heappush(self._queue, task)
        
        logger.info(f"Task {task_id} enqueued with priority {priority}")
        return queue_id
    
    async def dequeue(self, agent_id: Optional[str] = None) -> Optional[Dict]:
        """
        从队列取出任务
        
        Args:
            agent_id: 执行任务的智能体ID
        
        Returns:
            任务数据或None
        """
        if not self._queue:
            return None
        
        if len(self._processing) >= self.max_concurrent:
            logger.warning(f"Max concurrent tasks reached: {self.max_concurrent}")
            return None
        
        task = heapq.heappop(self._queue)
        self._processing[task.task_id] = task
        
        async with self._db.get_connection() as conn:
            queue_id = task.task_data.get('queue_id')
            if queue_id:
                await conn.execute("""
                    UPDATE task_queue 
                    SET status = $1, assigned_agent_id = $2, started_at = $3
                    WHERE id = $4
                """, TaskStatus.PROCESSING.value, agent_id, datetime.utcnow(), queue_id)
        
        logger.info(f"Task {task.task_id} dequeued for agent {agent_id}")
        return {
            'task_id': task.task_id,
            'priority': -task.priority,
            **task.task_data
        }
    
    async def complete(self, task_id: str, result: Optional[Dict] = None) -> bool:
        """标记任务完成"""
        if task_id in self._processing:
            del self._processing[task_id]
        
        async with self._db.get_connection() as conn:
            await conn.execute("""
                UPDATE task_queue 
                SET status = $1, completed_at = $2
                WHERE task_id = $3 AND status = $4
            """, TaskStatus.COMPLETED.value, datetime.utcnow(), task_id, TaskStatus.PROCESSING.value)
            
            if result:
                await conn.execute("""
                    UPDATE tasks SET result = $1, status = $2, completed_at = $3
                    WHERE id = $4
                """, result, TaskStatus.COMPLETED.value, datetime.utcnow(), task_id)
        
        logger.info(f"Task {task_id} completed")
        return True
    
    async def fail(
        self, 
        task_id: str, 
        error: str, 
        retry: bool = True
    ) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            retry: 是否允许重试
        """
        if task_id in self._processing:
            task = self._processing.pop(task_id)
        else:
            task = None
        
        async with self._db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT retry_count, max_retries FROM task_queue 
                WHERE task_id = $1 AND status = $2
            """, task_id, TaskStatus.PROCESSING.value)
            
            if row is None:
                return False
            
            retry_count = row['retry_count']
            max_retries = row['max_retries']
            
            if retry and retry_count < max_retries:
                await conn.execute("""
                    UPDATE task_queue 
                    SET status = $1, retry_count = retry_count + 1, started_at = NULL
                    WHERE task_id = $2
                """, TaskStatus.PENDING.value, task_id)
                
                if task:
                    heapq.heappush(self._queue, task)
                
                logger.warning(f"Task {task_id} failed, will retry ({retry_count + 1}/{max_retries})")
            else:
                await conn.execute("""
                    UPDATE task_queue 
                    SET status = $1, completed_at = $2
                    WHERE task_id = $3
                """, TaskStatus.FAILED.value, datetime.utcnow(), task_id)
                
                await conn.execute("""
                    UPDATE tasks SET status = $1, error_message = $2, completed_at = $3
                    WHERE id = $4
                """, TaskStatus.FAILED.value, error, datetime.utcnow(), task_id)
                
                logger.error(f"Task {task_id} failed permanently: {error}")
        
        return True
    
    async def cancel(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self._processing:
            del self._processing[task_id]
        
        self._queue = [t for t in self._queue if t.task_id != task_id]
        heapq.heapify(self._queue)
        
        async with self._db.get_connection() as conn:
            await conn.execute("""
                UPDATE task_queue SET status = $1 WHERE task_id = $2
            """, TaskStatus.CANCELLED.value, task_id)
        
        logger.info(f"Task {task_id} cancelled")
        return True
    
    async def get_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        async with self._db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT tq.*, t.query, t.style, t.result, t.progress
                FROM task_queue tq
                JOIN tasks t ON t.id = tq.task_id
                WHERE tq.task_id = $1
            """, task_id)
            
            if row is None:
                return None
            
            return dict(row)
    
    async def get_child_tasks(self, parent_task_id: str) -> List[Dict]:
        """
        获取父任务下的所有子任务
        
        Args:
            parent_task_id: 父任务ID
            
        Returns:
            子任务列表
        """
        async with self._db.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT 
                    tq.task_id as id,
                    tq.task_type as type,
                    tq.status,
                    tq.progress,
                    tq.message,
                    tq.priority,
                    tq.created_at,
                    tq.started_at,
                    tq.completed_at,
                    t.query,
                    t.result
                FROM task_queue tq
                LEFT JOIN tasks t ON t.id = tq.task_id
                WHERE tq.parent_task_id = $1
                ORDER BY tq.priority DESC, tq.created_at ASC
            """, parent_task_id)
            
            return [dict(row) for row in rows]
    
    async def add_task(
        self,
        task_id: str,
        task_type: str,
        params: Dict,
        priority: int = 5,
        user_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        level: int = 0
    ) -> str:
        """
        添加任务到队列
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            params: 任务参数
            priority: 优先级
            user_id: 用户ID
            parent_id: 父任务ID
            level: 执行层级
            
        Returns:
            queue_id: 队列记录ID
        """
        queue_id = str(uuid.uuid4())
        
        async with self._db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO task_queue 
                (id, task_id, task_type, params, priority, status, user_id, parent_task_id, level)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, queue_id, task_id, task_type, params, priority, 
               TaskStatus.PENDING.value, user_id, parent_id, level)
        
        task = PrioritizedTask(
            priority=-priority,
            created_at=time.time(),
            task_id=task_id,
            task_data={'queue_id': queue_id, 'task_type': task_type, 'params': params}
        )
        heapq.heappush(self._queue, task)
        
        logger.info(f"Task {task_id} added to queue with type {task_type}")
        return queue_id
    
    async def get_queue_stats(self) -> Dict:
        """获取队列统计"""
        async with self._db.get_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM task_queue
            """)
            
            return {
                'pending': stats['pending'] or 0,
                'processing': stats['processing'] or 0,
                'completed': stats['completed'] or 0,
                'failed': stats['failed'] or 0,
                'in_memory_queue': len(self._queue),
                'in_memory_processing': len(self._processing),
                'max_concurrent': self.max_concurrent
            }
    
    @property
    def size(self) -> int:
        return len(self._queue)
    
    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0


task_queue: Optional[TaskQueue] = None


async def get_task_queue() -> TaskQueue:
    global task_queue
    if task_queue is None:
        task_queue = await TaskQueue.get_instance()
    elif not task_queue._initialized:
        await task_queue._initialize()
    return task_queue
