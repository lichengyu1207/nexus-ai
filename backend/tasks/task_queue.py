"""
后台任务队列
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..logger import get_logger

logger = get_logger("task_queue")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None


class TaskQueue:
    """简单的任务队列"""
    
    def __init__(self, max_workers: int = 2):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: dict[str, Task] = {}
        self._workers: list[asyncio.Task] = []
        self._max_workers = max_workers
        self._running = False
    
    async def enqueue(self, name: str, func: Callable, args: tuple = (), kwargs: dict = None) -> str:
        """添加任务到队列"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(id=task_id, name=name, func=func, args=args, kwargs=kwargs or {})
        self._tasks[task_id] = task
        await self._queue.put(task_id)
        logger.info(f"Task enqueued: {name} (id={task_id})")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if task:
            return {"id": task.id, "name": task.name, "status": task.status.value}
        return None
    
    async def _worker(self, worker_id: int):
        """工作协程"""
        while self._running:
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                task = self._tasks.get(task_id)
                if not task or not task.func:
                    continue
                
                task.status = TaskStatus.RUNNING
                logger.info(f"Worker {worker_id} processing: {task.name}")
                
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        result = await task.func(*task.args, **task.kwargs)
                    else:
                        result = task.func(*task.args, **task.kwargs)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    logger.error(f"Task failed: {task.name} - {e}")
            except asyncio.TimeoutError:
                continue
    
    async def start(self):
        """启动任务队列"""
        self._running = True
        for i in range(self._max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        logger.info(f"Task queue started with {self._max_workers} workers")
    
    async def stop(self):
        """停止任务队列"""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        self._workers.clear()


task_queue = TaskQueue()


async def setup_task_queue():
    """初始化任务队列"""
    await task_queue.start()


async def shutdown_task_queue():
    """关闭任务队列"""
    await task_queue.stop()
