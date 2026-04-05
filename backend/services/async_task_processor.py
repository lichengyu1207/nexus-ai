"""
异步任务处理优化服务
提供任务预处理、批量处理、进度追踪等功能
"""
import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AsyncTask:
    """异步任务"""
    id: str
    task_type: str
    priority: int = 0
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    callback: Optional[Callable] = None
    metadata: Dict = field(default_factory=dict)


class AsyncTaskProcessor:
    """异步任务处理器"""
    
    _instance: Optional['AsyncTaskProcessor'] = None
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._tasks: Dict[str, AsyncTask] = {}
        self._queue: List[AsyncTask] = []
        self._processing: Dict[str, asyncio.Task] = {}
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "avg_duration": 0.0,
            "durations": []
        }
    
    @classmethod
    async def get_instance(cls) -> 'AsyncTaskProcessor':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def submit_task(
        self,
        task_type: str,
        metadata: Dict = None,
        priority: int = 5,
        callback: Callable = None
    ) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        
        task = AsyncTask(
            id=task_id,
            task_type=task_type,
            priority=priority,
            metadata=metadata or {},
            callback=callback
        )
        
        self._tasks[task_id] = task
        self._queue.append(task)
        self._queue.sort(key=lambda x: -x.priority)
        
        self._stats["total_tasks"] += 1
        
        if not self._running:
            await self.start()
        
        logger.info(f"Task {task_id} submitted with priority {priority}")
        return task_id
    
    async def start(self):
        """启动处理器"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("AsyncTaskProcessor started")
    
    async def stop(self):
        """停止处理器"""
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        
        logger.info("AsyncTaskProcessor stopped")
    
    async def _worker_loop(self):
        """工作循环"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        while self._running:
            try:
                await asyncio.sleep(0.1)
                
                if not self._queue:
                    continue
                
                task = self._queue.pop(0)
                if not task:
                    continue
                
                async with semaphore:
                    await self._process_task(task)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
    
    async def _process_task(self, task: AsyncTask):
        """处理任务"""
        handler = self._handlers.get(task.task_type)
        
        if not handler:
            logger.error(f"No handler for task type: {task.task_type}")
            task.status = "failed"
            task.error = f"No handler for task type: {task.task_type}"
            return
        
        task.status = "processing"
        task.started_at = time.time()
        
        try:
            result = await handler(task.metadata)
            
            task.status = "completed"
            task.result = result
            task.completed_at = time.time()
            
            duration = task.completed_at - task.started_at
            self._stats["completed"] += 1
            self._stats["durations"].append(duration)
            self._stats["avg_duration"] = sum(self._stats["durations"]) / len(self._stats["durations"])
            
            if task.callback:
                try:
                    await task.callback(result)
                except Exception as e:
                    logger.warning(f"Callback error: {e}")
            
            logger.info(f"Task {task.id} completed in {duration:.2f}s")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = time.time()
            
            self._stats["failed"] += 1
            
            logger.error(f"Task {task.id} failed: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if task:
            return {
                "id": task.id,
                "task_type": task.task_type,
                "status": task.status,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "result": task.result,
                "error": task.error
            }
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self._stats,
            "queue_size": len(self._queue),
            "processing_count": len([t for t in self._tasks.values() if t.status == "processing"]),
            "total_tasks": len(self._tasks)
        }


async_task_processor: Optional[AsyncTaskProcessor] = None


async def get_async_processor() -> AsyncTaskProcessor:
    global async_task_processor
    if async_task_processor is None:
        async_task_processor = await AsyncTaskProcessor.get_instance()
    return async_task_processor
