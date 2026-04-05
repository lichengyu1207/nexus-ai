"""
WebSocket批量任务推送路由
提供实时批量任务进度更新
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@dataclass
class BatchProgressMessage:
    """批量任务进度消息"""
    type: str
    parent_task_id: str
    total: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float
    tasks: List[Dict]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "parent_task_id": self.parent_task_id,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "running": self.running,
            "pending": self.pending,
            "progress_percent": self.progress_percent,
            "tasks": self.tasks,
            "timestamp": self.timestamp,
        })


class BatchTaskConnectionManager:
    """批量任务WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, parent_task_id: str):
        """建立连接"""
        await websocket.accept()
        
        async with self._lock:
            if parent_task_id not in self.active_connections:
                self.active_connections[parent_task_id] = set()
            self.active_connections[parent_task_id].add(websocket)
        
        logger.info(f"WebSocket connected for batch task {parent_task_id}")

    async def disconnect(self, websocket: WebSocket, parent_task_id: str):
        """断开连接"""
        async with self._lock:
            if parent_task_id in self.active_connections:
                self.active_connections[parent_task_id].discard(websocket)
                if not self.active_connections[parent_task_id]:
                    del self.active_connections[parent_task_id]
        
        logger.info(f"WebSocket disconnected for batch task {parent_task_id}")

    async def broadcast(self, parent_task_id: str, message: BatchProgressMessage):
        """广播消息到所有订阅者"""
        async with self._lock:
            connections = self.active_connections.get(parent_task_id, set()).copy()
        
        if not connections:
            return
        
        message_json = message.to_json()
        disconnected = set()
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message: {e}")
                disconnected.add(connection)
        
        async with self._lock:
            for conn in disconnected:
                if parent_task_id in self.active_connections:
                    self.active_connections[parent_task_id].discard(conn)

    async def send_to_all(self, message: BatchProgressMessage):
        """发送消息到所有连接"""
        async with self._lock:
            all_connections = list(self.active_connections.items())
        
        for parent_task_id, connections in all_connections:
            await self.broadcast(parent_task_id, message)

    def get_connection_count(self, parent_task_id: Optional[str] = None) -> int:
        """获取连接数"""
        if parent_task_id:
            return len(self.active_connections.get(parent_task_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


manager = BatchTaskConnectionManager()


async def get_batch_progress(parent_task_id: str) -> Dict:
    """获取批量任务进度"""
    from backend.services.task_queue import get_task_queue
    
    try:
        queue = await get_task_queue()
        child_tasks = await queue.get_child_tasks(parent_task_id)
        
        if not child_tasks:
            return {
                "parent_task_id": parent_task_id,
                "total": 0,
                "completed": 0,
                "failed": 0,
                "running": 0,
                "pending": 0,
                "progress_percent": 0,
                "tasks": []
            }
        
        total = len(child_tasks)
        completed = sum(1 for t in child_tasks if t.get("status") == "completed")
        failed = sum(1 for t in child_tasks if t.get("status") == "failed")
        running = sum(1 for t in child_tasks if t.get("status") == "running")
        pending = sum(1 for t in child_tasks if t.get("status") == "pending")
        
        progress_percent = round((completed / total) * 100, 1) if total > 0 else 0
        
        tasks_info = [
            {
                "id": t.get("id"),
                "type": t.get("type"),
                "status": t.get("status"),
                "progress": t.get("progress", 0),
                "message": t.get("message", "")
            }
            for t in child_tasks
        ]
        
        return {
            "parent_task_id": parent_task_id,
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": progress_percent,
            "tasks": tasks_info
        }
    except Exception as e:
        logger.error(f"Failed to get batch progress: {e}")
        return {
            "parent_task_id": parent_task_id,
            "total": 0,
            "completed": 0,
            "failed": 0,
            "running": 0,
            "pending": 0,
            "progress_percent": 0,
            "tasks": [],
            "error": str(e)
        }


@router.websocket("/ws/batch/{parent_task_id}")
async def websocket_batch_progress(websocket: WebSocket, parent_task_id: str):
    """
    WebSocket端点 - 批量任务进度
    
    连接后自动推送任务进度更新
    """
    await manager.connect(websocket, parent_task_id)
    
    try:
        initial_progress = await get_batch_progress(parent_task_id)
        await websocket.send_text(BatchProgressMessage(
            type="batch_progress",
            **initial_progress
        ).to_json())
        
        poll_interval = 1.0
        last_progress_percent = initial_progress.get("progress_percent", 0)
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=poll_interval
                )
                
                try:
                    message = json.loads(data)
                    
                    if message.get("type") == "subscribe":
                        logger.info(f"Client subscribed to batch {parent_task_id}")
                    
                    elif message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                pass
            
            progress = await get_batch_progress(parent_task_id)
            
            current_percent = progress.get("progress_percent", 0)
            if current_percent != last_progress_percent:
                await websocket.send_text(BatchProgressMessage(
                    type="batch_progress",
                    **progress
                ).to_json())
                last_progress_percent = current_percent
            
            if progress.get("completed", 0) + progress.get("failed", 0) >= progress.get("total", 0):
                if progress.get("total", 0) > 0:
                    await websocket.send_text(BatchProgressMessage(
                        type="batch_complete",
                        **progress
                    ).to_json())
                    break
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from batch {parent_task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket, parent_task_id)


async def notify_batch_progress(parent_task_id: str, progress_data: Dict):
    """
    通知批量任务进度更新
    
    可从其他模块调用以触发进度推送
    """
    message = BatchProgressMessage(
        type="batch_progress",
        parent_task_id=parent_task_id,
        **progress_data
    )
    await manager.broadcast(parent_task_id, message)


async def notify_task_complete(parent_task_id: str, task_id: str, success: bool):
    """
    通知单个任务完成
    """
    progress = await get_batch_progress(parent_task_id)
    
    message = BatchProgressMessage(
        type="task_complete" if success else "task_failed",
        parent_task_id=parent_task_id,
        task_id=task_id,
        **progress
    )
    await manager.broadcast(parent_task_id, message)


@router.get("/ws/batch/{parent_task_id}/status")
async def get_batch_ws_status(parent_task_id: str):
    """
    获取批量任务WebSocket状态
    """
    return {
        "parent_task_id": parent_task_id,
        "active_connections": manager.get_connection_count(parent_task_id),
        "is_active": parent_task_id in manager.active_connections
    }


@router.get("/ws/stats")
async def get_ws_stats():
    """
    获取WebSocket统计信息
    """
    return {
        "total_connections": manager.get_connection_count(),
        "active_batches": list(manager.active_connections.keys())
    }
