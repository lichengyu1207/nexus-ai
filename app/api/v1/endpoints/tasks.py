from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime
from ..schemas.task import TaskCreate, TaskStatus, TaskStatusEnum, TaskResponse, TaskDetailResponse, AgentSummary
from ..storage import task_store
from app.services.task_manager import task_manager

router = APIRouter()


@router.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate, background_tasks: BackgroundTasks):
    # 创建任务，传递结构化字段
    task_id = task_store.create_task(
        query=task.query,
        address=task.address,
        property_type=task.property_type,
        area=task.area,
        age=task.age,
        description=task.description
    )
    
    # 使用BackgroundTasks异步执行多代理工作流
    background_tasks.add_task(
        execute_task, 
        task_id, 
        task.query,
        task.address,
        task.property_type,
        task.area,
        task.age,
        task.description
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatusEnum.PENDING
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task_status(task_id: str):
    task = task_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 转换为TaskDetailResponse格式
    agents = []
    if "agents" in task:
        for agent_type, agent_info in task["agents"].items():
            agent_summary = AgentSummary(
                id=agent_info.get("agent_id", agent_type),
                name=agent_type,
                avatar=get_agent_avatar(agent_type),
                status=agent_info.get("status", "pending"),
                started_at=agent_info.get("start_time"),
                completed_at=agent_info.get("end_time")
            )
            agents.append(agent_summary)
    
    task_detail = TaskDetailResponse(
        task_id=task["task_id"],
        status=TaskStatusEnum(task["status"]),
        progress=task.get("progress", 0.0),
        created_at=task.get("created_at"),
        updated_at=task.get("updated_at"),
        result=task.get("result"),
        error=task.get("error"),
        agents=agents
    )
    
    return task_detail


@router.get("/tasks/{task_id}/steps")
async def get_task_steps(task_id: str, group_by_agent: bool = Query(False, description="按代理分组返回步骤")):
    result = task_manager.get_task_steps(task_id, group_by_agent)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/tasks/{task_id}/snapshot")
async def get_task_snapshot(task_id: str):
    """Get task snapshot for replay"""
    from app.services.snapshot_service import snapshot_service
    
    snapshot = snapshot_service.get(task_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return snapshot


@router.post("/tasks/{task_id}/snapshot")
async def create_task_snapshot(task_id: str):
    """Create task snapshot manually"""
    from app.services.snapshot_service import snapshot_service
    
    try:
        snapshot_id = snapshot_service.save(task_id)
        return {
            "task_id": task_id,
            "snapshot_id": snapshot_id,
            "message": "Snapshot created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")



async def execute_task(task_id: str, query: str, address: Optional[str] = None, property_type: Optional[str] = None, area: Optional[float] = None, age: Optional[int] = None, description: Optional[str] = None):
    await task_manager.start_analysis(
        task_id=task_id,
        query=query,
        address=address,
        property_type=property_type,
        area=area,
        age=age,
        description=description
    )


def get_agent_avatar(agent_type: str) -> str:
    """Get agent avatar based on agent type"""
    avatar_map = {
        "requirement_analyzer": "🔍",
        "data_collector": "📊",
        "data_cleaner": "🧹",
        "data_verifier": "✅",
        "market_analyst": "📈",
        "report_generator": "📄"
    }
    return avatar_map.get(agent_type, "🤖")

