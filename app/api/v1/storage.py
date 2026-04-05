from typing import Dict, Any, Optional
from .schemas.task import TaskStatusEnum


class TaskStore:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_task(self, query: str, address: Optional[str] = None, property_type: Optional[str] = None, area: Optional[float] = None, age: Optional[int] = None, description: Optional[str] = None) -> str:
        import uuid
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "task_id": task_id,
            "query": query,
            "address": address,
            "property_type": property_type,
            "area": area,
            "age": age,
            "description": description,
            "status": TaskStatusEnum.PENDING,
            "progress": 0.0,
            "nodes": {},
            "result": None,
            "error": None
        }
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)
    
    async def update_node_status(self, task_id: str, node: str, status: TaskStatusEnum, log: str):
        if task_id in self.tasks:
            if "nodes" not in self.tasks[task_id]:
                self.tasks[task_id]["nodes"] = {}
            self.tasks[task_id]["nodes"][node] = status
            # 计算进度
            total_nodes = max(len(self.tasks[task_id]["nodes"]), 1)
            completed_nodes = sum(1 for s in self.tasks[task_id]["nodes"].values() 
                                if s in [TaskStatusEnum.SUCCESS, TaskStatusEnum.FAILED])
            self.tasks[task_id]["progress"] = completed_nodes / total_nodes
            
            # 广播WebSocket消息
            from .schemas.ws import WebSocketMessage, NodeStatusEnum
            from .endpoints.ws import manager
            message = WebSocketMessage(
                node=node,
                status=NodeStatusEnum(status),
                log=log
            )
            await manager.broadcast(message, task_id)


# 创建全局task_store实例
task_store = TaskStore()
