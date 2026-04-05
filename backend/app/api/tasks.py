import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.task import TaskCreate, TaskResponse, SubTaskResponse
from app.models.task import Task, SubTask
from app.agents.zhongshu import ZhongshuAgent
from app.agents.shangshu import ShangshuAgent
from app.agents.gongbu import GongbuAgent

router = APIRouter()

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """创建任务"""
    # 生成trace_id
    trace_id = str(uuid.uuid4())
    
    # 调用中书省生成任务规格
    zhongshu = ZhongshuAgent()
    spec = zhongshu.generate_spec(task.text)
    
    # 创建任务
    db_task = Task(
        id=spec["task_id"],
        type=spec["task_type"],
        spec=spec,
        trace_id=trace_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 创建子任务
    for subtask_spec in spec["subtasks"]:
        db_subtask = SubTask(
            id=subtask_spec["id"],
            task_id=spec["task_id"],
            type=subtask_spec["type"],
            dependencies=subtask_spec["dependencies"],
            required_agents=subtask_spec["required_agents"],
            parameters=subtask_spec["parameters"],
            trace_id=trace_id
        )
        db.add(db_subtask)
    db.commit()
    
    # 调用尚书省调度任务
    shangshu = ShangshuAgent(db)
    await shangshu.schedule_task(db_task)
    
    # 刷新任务状态
    db.refresh(db_task)
    
    # 获取子任务
    subtasks = db.query(SubTask).filter(SubTask.task_id == db_task.id).all()
    
    # 构建响应
    response = TaskResponse(
        id=db_task.id,
        type=db_task.type,
        spec=spec,
        status=db_task.status,
        trace_id=db_task.trace_id,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        completed_at=db_task.completed_at,
        total_duration=db_task.total_duration,
        subtasks=[
            SubTaskResponse.model_validate(subtask)
            for subtask in subtasks
        ]
    )
    
    return response

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    subtasks = db.query(SubTask).filter(SubTask.task_id == task_id).all()
    
    # 构建响应
    response = TaskResponse(
        id=task.id,
        type=task.type,
        spec=task.spec,
        status=task.status,
        trace_id=task.trace_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        total_duration=task.total_duration,
        subtasks=[
            SubTaskResponse.model_validate(subtask)
            for subtask in subtasks
        ]
    )
    
    return response

@router.get("/{task_id}/status")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """获取任务状态"""
    shangshu = ShangshuAgent(db)
    return shangshu.get_task_status(task_id)

@router.post("/{task_id}/report")
def generate_task_report(task_id: str, db: Session = Depends(get_db)):
    """生成任务报告"""
    gongbu = GongbuAgent(db)
    return gongbu.generate_report(task_id)
