from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Set
import asyncio
from ..schemas.ws import WebSocketMessage, NodeStatusEnum
from ..schemas.task import TaskStatusEnum
from ..storage import task_store

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # 存储任务ID到WebSocket连接的映射
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def send_personal_message(self, message: WebSocketMessage, websocket: WebSocket):
        await websocket.send_json(message.model_dump())
    
    async def broadcast(self, message: WebSocketMessage, task_id: str):
        if task_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message.model_dump())
                except:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for connection in disconnected:
                self.disconnect(connection, task_id)


manager = ConnectionManager()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    # 检查任务是否存在
    task = task_store.get_task(task_id)
    if not task:
        await websocket.close(code=1008, reason="Task not found")
        return
    
    # 建立连接
    await manager.connect(websocket, task_id)
    
    try:
        # 发送初始状态
        if task.get("nodes"):
            for node, status in task["nodes"].items():
                message = WebSocketMessage(
                    node=node,
                    status=NodeStatusEnum(status),
                    log=f"节点{node}当前状态: {status}"
                )
                await manager.send_personal_message(message, websocket)
        
        # 模拟实时状态更新（实际项目中应该从DAGExecutor获取）
        while True:
            # 检查任务状态
            current_task = task_store.get_task(task_id)
            if current_task:
                # 模拟状态变更检测
                await asyncio.sleep(0.5)
            else:
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        manager.disconnect(websocket, task_id)
