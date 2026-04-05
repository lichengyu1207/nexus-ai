"""
SSE API路由 - PostgreSQL版本
提供Server-Sent Events实时消息推送
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import logging

from ..sse_manager import sse_manager, SSEEvent
from ..database_pg import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sse", tags=["sse"])


@router.get("/tasks/{task_id}/stream")
async def stream_task_events(task_id: str):
    """
    SSE流式获取任务事件
    
    Args:
        task_id: 任务ID
        
    Returns:
        StreamingResponse: SSE流
    """
    async with get_db() as conn:
        task = await conn.fetchrow(
            "SELECT id FROM analysis_tasks WHERE id = $1",
            task_id
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    
    async def event_generator():
        queue = await sse_manager.subscribe(task_id)
        
        try:
            yield SSEEvent(
                event="connected",
                data={"task_id": task_id, "message": "SSE connection established"}
            ).to_sse_format()
            
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse_format()
                    
                    if event.event == "complete":
                        break
                        
                except asyncio.TimeoutError:
                    yield SSEEvent(
                        event="heartbeat",
                        data={"timestamp": asyncio.get_event_loop().time()}
                    ).to_sse_format()
                    
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for task {task_id}")
        finally:
            await sse_manager.unsubscribe(task_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/tasks/{task_id}/status")
async def get_sse_status(task_id: str):
    """
    获取任务的SSE连接状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        dict: 连接状态
    """
    return {
        "task_id": task_id,
        "subscribers": sse_manager.get_subscriber_count(task_id),
        "is_active": task_id in sse_manager.get_active_tasks()
    }


@router.get("/stats")
async def get_sse_stats():
    """
    获取SSE统计信息
    
    Returns:
        dict: 统计信息
    """
    return {
        "total_connections": sse_manager.get_subscriber_count(),
        "active_tasks": sse_manager.get_active_tasks()
    }
