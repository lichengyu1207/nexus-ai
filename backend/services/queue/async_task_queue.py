"""
异步任务处理系统
消息队列、任务队列、重试机制、死信队列
"""
import asyncio
import json
import time
import uuid
import logging
from typing import Any, Optional, Callable, Dict, List, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import os
import traceback

try:
    import aio_pika
    from aio_pika import Message, DeliveryMode
    from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    aio_pika = None
    Message = None
    DeliveryMode = None

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class TaskDefinition:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0
    timeout: float = 300.0
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    status: str = "pending"
    result: Any = None
    error: str = None
    callback_url: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.task_id is None:
            self.task_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "callback_url": self.callback_url,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskDefinition':
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("started_at"), str):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if isinstance(data.get("completed_at"), str):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def get_delay(self, retry_count: int) -> float:
        delay = self.base_delay * (self.exponential_base ** retry_count)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay


class TaskHandler(ABC):
    """任务处理器基类"""
    
    @property
    @abstractmethod
    def task_type(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, task: TaskDefinition) -> Any:
        pass
    
    async def on_success(self, task: TaskDefinition, result: Any):
        logger.info(f"Task {task.task_id} completed successfully")
    
    async def on_failure(self, task: TaskDefinition, error: Exception):
        logger.error(f"Task {task.task_id} failed: {error}")
    
    async def on_retry(self, task: TaskDefinition, error: Exception):
        logger.warning(f"Task {task.task_id} retry {task.retry_count}/{task.max_retries}: {error}")


class InMemoryTaskQueue:
    """内存任务队列（备用）"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues: Dict[str, List[TaskDefinition]] = {}
        self._tasks: Dict[str, TaskDefinition] = {}
        self._lock = asyncio.Lock()
    
    async def enqueue(self, task: TaskDefinition, queue_name: str = "default") -> bool:
        async with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = []
            
            if len(self._queues[queue_name]) >= self.max_size:
                return False
            
            self._queues[queue_name].append(task)
            self._tasks[task.task_id] = task
            return True
    
    async def dequeue(self, queue_name: str = "default") -> Optional[TaskDefinition]:
        async with self._lock:
            if queue_name not in self._queues or not self._queues[queue_name]:
                return None
            
            task = self._queues[queue_name].pop(0)
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.now()
            return task
    
    async def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        return self._tasks.get(task_id)
    
    async def update_task(self, task: TaskDefinition):
        self._tasks[task.task_id] = task
    
    async def get_queue_size(self, queue_name: str = "default") -> int:
        return len(self._queues.get(queue_name, []))


class RabbitMQTaskQueue:
    """RabbitMQ任务队列"""
    
    def __init__(self, url: str = None):
        self.url = url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractRobustChannel] = None
        self._queues: Dict[str, Any] = {}
        self._connected = False
    
    async def connect(self) -> bool:
        if not RABBITMQ_AVAILABLE:
            logger.warning("aio_pika not installed, RabbitMQ unavailable")
            return False
        
        try:
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)
            self._connected = True
            logger.info(f"RabbitMQ connected: {self.url}")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
            self._connected = False
            return False
    
    async def close(self):
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._channel = None
            self._connected = False
    
    async def declare_queue(self, queue_name: str, dead_letter: bool = True):
        if not self._connected or not self._channel:
            return None
        
        args = {}
        if dead_letter:
            dlq_name = f"{queue_name}.dlq"
            await self._channel.declare_queue(dlq_name, durable=True)
            args = {
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": dlq_name
            }
        
        queue = await self._channel.declare_queue(
            queue_name,
            durable=True,
            arguments=args
        )
        self._queues[queue_name] = queue
        return queue
    
    async def enqueue(self, task: TaskDefinition, queue_name: str = "default") -> bool:
        if not self._connected or not self._channel:
            return False
        
        if queue_name not in self._queues:
            await self.declare_queue(queue_name)
        
        message = Message(
            body=json.dumps(task.to_dict()).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            priority=task.priority,
            message_id=task.task_id
        )
        
        await self._channel.default_exchange.publish(
            message,
            routing_key=queue_name
        )
        
        return True
    
    async def dequeue(self, queue_name: str = "default", timeout: float = 5.0) -> Optional[TaskDefinition]:
        if not self._connected or not self._channel:
            return None
        
        if queue_name not in self._queues:
            await self.declare_queue(queue_name)
        
        queue = self._queues[queue_name]
        
        try:
            message = await asyncio.wait_for(
                queue.get(fail=False, no_ack=False),
                timeout=timeout
            )
            
            if message:
                task_data = json.loads(message.body.decode())
                task = TaskDefinition.from_dict(task_data)
                task.status = TaskStatus.RUNNING.value
                task.started_at = datetime.now()
                task.metadata["_message"] = message
                return task
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Dequeue error: {e}")
            return None
    
    async def ack(self, task: TaskDefinition):
        if task.metadata and "_message" in task.metadata:
            message = task.metadata["_message"]
            await message.ack()
    
    async def nack(self, task: TaskDefinition, requeue: bool = False):
        if task.metadata and "_message" in task.metadata:
            message = task.metadata["_message"]
            await message.nack(requeue=requeue)
    
    async def get_queue_size(self, queue_name: str = "default") -> int:
        if queue_name not in self._queues:
            return 0
        
        queue = self._queues[queue_name]
        info = await queue.declare(passive=True)
        return info.message_count


class TaskWorker:
    """任务工作器"""
    
    def __init__(
        self,
        queue_name: str = "default",
        handlers: Dict[str, TaskHandler] = None,
        concurrency: int = 5
    ):
        self.queue_name = queue_name
        self.handlers = handlers or {}
        self.concurrency = concurrency
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "retried": 0
        }
    
    def register_handler(self, handler: TaskHandler):
        self.handlers[handler.task_type] = handler
    
    async def process_task(self, task: TaskDefinition, queue) -> bool:
        handler = self.handlers.get(task.task_type)
        
        if not handler:
            logger.error(f"No handler for task type: {task.task_type}")
            task.status = TaskStatus.FAILED.value
            task.error = f"No handler for task type: {task.task_type}"
            return False
        
        try:
            result = await asyncio.wait_for(
                handler.execute(task),
                timeout=task.timeout
            )
            
            task.status = TaskStatus.COMPLETED.value
            task.result = result
            task.completed_at = datetime.now()
            
            await handler.on_success(task, result)
            
            if hasattr(queue, 'ack'):
                await queue.ack(task)
            
            self._stats["succeeded"] += 1
            return True
            
        except asyncio.TimeoutError:
            error = TimeoutError(f"Task timeout after {task.timeout}s")
            return await self._handle_failure(task, error, handler, queue)
            
        except Exception as e:
            return await self._handle_failure(task, e, handler, queue)
    
    async def _handle_failure(
        self,
        task: TaskDefinition,
        error: Exception,
        handler: TaskHandler,
        queue
    ) -> bool:
        task.retry_count += 1
        task.error = str(error)
        
        if task.retry_count < task.max_retries:
            task.status = TaskStatus.RETRY.value
            
            retry_policy = RetryPolicy(max_retries=task.max_retries)
            delay = retry_policy.get_delay(task.retry_count - 1)
            
            await handler.on_retry(task, error)
            
            if hasattr(queue, 'nack'):
                await queue.nack(task, requeue=False)
            
            await asyncio.sleep(delay)
            
            if hasattr(queue, 'enqueue'):
                await queue.enqueue(task, self.queue_name)
            
            self._stats["retried"] += 1
            return False
        else:
            task.status = TaskStatus.FAILED.value
            task.completed_at = datetime.now()
            
            await handler.on_failure(task, error)
            
            if hasattr(queue, 'nack'):
                await queue.nack(task, requeue=False)
            
            self._stats["failed"] += 1
            return False
    
    async def start(self, queue):
        self._running = True
        logger.info(f"Task worker started for queue: {self.queue_name}")
        
        while self._running:
            try:
                task = await queue.dequeue(self.queue_name)
                
                if task:
                    self._stats["processed"] += 1
                    
                    if len(self._tasks) < self.concurrency:
                        async_task = asyncio.create_task(
                            self.process_task(task, queue)
                        )
                        self._tasks[task.task_id] = async_task
                        async_task.add_done_callback(
                            lambda t, tid=task.task_id: self._tasks.pop(tid, None)
                        )
                    else:
                        await self.process_task(task, queue)
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
        
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        
        logger.info(f"Task worker stopped for queue: {self.queue_name}")
    
    def stop(self):
        self._running = False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "queue_name": self.queue_name,
            "running": self._running,
            "active_tasks": len(self._tasks),
            "concurrency": self.concurrency,
            **self._stats
        }


class AsyncTaskQueue:
    """异步任务队列服务"""
    
    _instance: Optional['AsyncTaskQueue'] = None
    
    def __init__(self, use_rabbitmq: bool = True):
        self.use_rabbitmq = use_rabbitmq and RABBITMQ_AVAILABLE
        
        if self.use_rabbitmq:
            self._queue = RabbitMQTaskQueue()
        else:
            self._queue = InMemoryTaskQueue()
        
        self._workers: Dict[str, TaskWorker] = {}
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        self._handlers: Dict[str, TaskHandler] = {}
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'AsyncTaskQueue':
        if cls._instance is None:
            cls._instance = cls(use_rabbitmq=True)
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        if self.use_rabbitmq:
            connected = await self._queue.connect()
            if not connected:
                logger.warning("RabbitMQ unavailable, falling back to in-memory queue")
                self._queue = InMemoryTaskQueue()
                self.use_rabbitmq = False
        
        self._initialized = True
        logger.info(f"Async task queue initialized (RabbitMQ: {self.use_rabbitmq})")
        return True
    
    async def close(self):
        for worker in self._workers.values():
            worker.stop()
        
        for task in self._worker_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        if hasattr(self._queue, 'close'):
            await self._queue.close()
        
        self._initialized = False
        logger.info("Async task queue closed")
    
    def register_handler(self, handler: TaskHandler):
        self._handlers[handler.task_type] = handler
        
        for worker in self._workers.values():
            worker.register_handler(handler)
    
    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 5,
        max_retries: int = 3,
        timeout: float = 300.0,
        callback_url: str = None,
        queue_name: str = "default"
    ) -> str:
        task = TaskDefinition(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            callback_url=callback_url
        )
        
        await self._queue.enqueue(task, queue_name)
        
        logger.info(f"Task submitted: {task.task_id} ({task_type})")
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        if hasattr(self._queue, 'get_task'):
            task = await self._queue.get_task(task_id)
            if task:
                return task.to_dict()
        return None
    
    async def start_worker(
        self,
        queue_name: str = "default",
        concurrency: int = 5
    ) -> TaskWorker:
        if queue_name in self._workers:
            return self._workers[queue_name]
        
        worker = TaskWorker(
            queue_name=queue_name,
            handlers=self._handlers.copy(),
            concurrency=concurrency
        )
        
        self._workers[queue_name] = worker
        
        worker_task = asyncio.create_task(worker.start(self._queue))
        self._worker_tasks[queue_name] = worker_task
        
        return worker
    
    async def stop_worker(self, queue_name: str):
        if queue_name in self._workers:
            self._workers[queue_name].stop()
            
        if queue_name in self._worker_tasks:
            self._worker_tasks[queue_name].cancel()
            try:
                await self._worker_tasks[queue_name]
            except asyncio.CancelledError:
                pass
            del self._worker_tasks[queue_name]
    
    async def get_queue_size(self, queue_name: str = "default") -> int:
        return await self._queue.get_queue_size(queue_name)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "use_rabbitmq": self.use_rabbitmq,
            "workers": {
                name: worker.get_stats()
                for name, worker in self._workers.items()
            },
            "handlers": list(self._handlers.keys())
        }


task_queue: Optional[AsyncTaskQueue] = None


async def get_task_queue() -> AsyncTaskQueue:
    global task_queue
    if task_queue is None:
        task_queue = await AsyncTaskQueue.get_instance()
    return task_queue


async def init_task_queue() -> bool:
    global task_queue
    task_queue = await AsyncTaskQueue.get_instance()
    return task_queue._initialized


async def close_task_queue():
    global task_queue
    if task_queue:
        await task_queue.close()
        task_queue = None


def task_handler(task_type: str):
    """任务处理器装饰器"""
    def decorator(func: Callable):
        class DecoratedHandler(TaskHandler):
            @property
            def task_type(self) -> str:
                return task_type
            
            async def execute(self, task: TaskDefinition) -> Any:
                return await func(task.payload)
        
        handler = DecoratedHandler()
        
        async def register():
            queue = await get_task_queue()
            queue.register_handler(handler)
        
        asyncio.create_task(register())
        
        return func
    return decorator
