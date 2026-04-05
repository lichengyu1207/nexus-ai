"""
SSE事件管理器
实现Server-Sent Events实时消息推送
"""
import asyncio
from typing import Dict, Set, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """SSE事件数据类"""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_sse_format(self) -> str:
        """
        转换为SSE格式字符串
        
        Returns:
            str: SSE格式字符串
        """
        lines = []
        
        if self.id:
            lines.append(f"id: {self.id}")
        
        lines.append(f"event: {self.event}")
        
        data_str = json.dumps(self.data, ensure_ascii=False, default=str)
        lines.append(f"data: {data_str}")
        
        if self.retry:
            lines.append(f"retry: {self.retry}")
        
        return "\n".join(lines) + "\n\n"


class SSEManager:
    """
    SSE事件管理器
    管理所有SSE连接，广播消息到所有订阅者
    
    Attributes:
        _subscribers: 任务ID到订阅者队列的映射
        _event_handlers: 事件处理器字典
    """
    
    def __init__(self):
        """初始化SSE管理器"""
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._event_handlers: Dict[str, Callable] = {}
        self._connection_count = 0
        
        logger.info("SSEManager initialized")
    
    async def subscribe(self, task_id: str) -> asyncio.Queue:
        """
        订阅任务事件
        
        Args:
            task_id: 任务ID
            
        Returns:
            asyncio.Queue: 事件队列
        """
        if task_id not in self._subscribers:
            self._subscribers[task_id] = set()
        
        queue = asyncio.Queue()
        self._subscribers[task_id].add(queue)
        self._connection_count += 1
        
        logger.info(f"SSE subscriber added for task {task_id}, total connections: {self._connection_count}")
        
        return queue
    
    async def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """
        取消订阅
        
        Args:
            task_id: 任务ID
            queue: 事件队列
        """
        if task_id in self._subscribers:
            self._subscribers[task_id].discard(queue)
            self._connection_count -= 1
            
            if not self._subscribers[task_id]:
                del self._subscribers[task_id]
        
        logger.info(f"SSE subscriber removed for task {task_id}, remaining: {self._connection_count}")
    
    async def broadcast(self, task_id: str, event: SSEEvent) -> int:
        """
        广播事件到所有订阅者
        
        Args:
            task_id: 任务ID
            event: SSE事件
            
        Returns:
            int: 接收事件的订阅者数量
        """
        if task_id not in self._subscribers:
            return 0
        
        count = 0
        dead_queues = set()
        
        for queue in self._subscribers[task_id]:
            try:
                queue.put_nowait(event)
                count += 1
            except asyncio.QueueFull:
                dead_queues.add(queue)
        
        for queue in dead_queues:
            self._subscribers[task_id].discard(queue)
        
        logger.debug(f"Broadcast event {event.event} to {count} subscribers for task {task_id}")
        
        return count
    
    async def broadcast_message(self, task_id: str, message: dict) -> None:
        """
        广播代理消息
        
        Args:
            task_id: 任务ID
            message: 消息内容
        """
        event = SSEEvent(
            event="message",
            data=message,
            id=message.get("id")
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_status(self, task_id: str, status: str, details: dict = None) -> None:
        """
        广播状态更新
        
        Args:
            task_id: 任务ID
            status: 状态
            details: 详细信息
        """
        event = SSEEvent(
            event="status",
            data={
                "task_id": task_id,
                "status": status,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_workflow_step(
        self,
        task_id: str,
        step: str,
        agent: str,
        action: str,
        status: str,
        details: dict = None
    ) -> None:
        """
        广播工作流步骤
        
        Args:
            task_id: 任务ID
            step: 步骤名称
            agent: 代理名称
            action: 动作
            status: 状态
            details: 详细信息
        """
        event = SSEEvent(
            event="workflow",
            data={
                "task_id": task_id,
                "step": step,
                "agent": agent,
                "action": action,
                "status": status,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_report_chunk(
        self,
        task_id: str,
        report_id: str,
        section: str,
        content: Any,
        progress: int = None
    ) -> None:
        """
        广播报告片段
        
        Args:
            task_id: 任务ID
            report_id: 报告ID
            section: 章节名称
            content: 章节内容
            progress: 进度百分比
        """
        event = SSEEvent(
            event="report_chunk",
            data={
                "task_id": task_id,
                "report_id": report_id,
                "section": section,
                "content": content,
                "progress": progress,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_report_complete(
        self,
        task_id: str,
        report_id: str,
        content: dict = None
    ) -> None:
        """
        广播报告完成
        
        Args:
            task_id: 任务ID
            report_id: 报告ID
            content: 完整报告内容
        """
        event = SSEEvent(
            event="report_complete",
            data={
                "task_id": task_id,
                "report_id": report_id,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_report_error(
        self,
        task_id: str,
        report_id: str,
        error: str
    ) -> None:
        """
        广播报告错误
        
        Args:
            task_id: 任务ID
            report_id: 报告ID
            error: 错误信息
        """
        event = SSEEvent(
            event="report_error",
            data={
                "task_id": task_id,
                "report_id": report_id,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_report_progress(
        self,
        task_id: str,
        report_id: str,
        event_type: str,
        data: dict
    ) -> None:
        """
        广播报告进度
        
        Args:
            task_id: 任务ID
            report_id: 报告ID
            event_type: 事件类型
            data: 事件数据
        """
        event = SSEEvent(
            event=f"report_{event_type}",
            data={
                "task_id": task_id,
                "report_id": report_id,
                **data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    async def broadcast_timeline_highlight(
        self,
        task_id: str,
        report_id: str,
        agent_name: str,
        step_name: str,
        section: str,
        status: str,
        description: str = None,
        content: Any = None
    ) -> None:
        """
        广播时间线高亮事件
        
        Args:
            task_id: 任务ID
            report_id: 报告ID
            agent_name: 代理名称
            step_name: 步骤名称
            section: 报告章节
            status: 状态 (started/completed)
            description: 描述
            content: 内容
        """
        event = SSEEvent(
            event="timeline_highlight",
            data={
                "task_id": task_id,
                "report_id": report_id,
                "agent_name": agent_name,
                "step_name": step_name,
                "section": section,
                "status": status,
                "description": description,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await self.broadcast(task_id, event)
    
    def get_subscriber_count(self, task_id: str = None) -> int:
        """
        获取订阅者数量
        
        Args:
            task_id: 任务ID（可选）
            
        Returns:
            int: 订阅者数量
        """
        if task_id:
            return len(self._subscribers.get(task_id, set()))
        
        return self._connection_count
    
    def get_active_tasks(self) -> list:
        """
        获取有活跃订阅者的任务列表
        
        Returns:
            list: 任务ID列表
        """
        return list(self._subscribers.keys())


sse_manager = SSEManager()
