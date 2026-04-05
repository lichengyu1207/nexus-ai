"""
分析API路由
使用主管代理驱动整个分析流程
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncio
import logging

from ..agents import (
    AgentScheduler,
    SupervisorAgent,
    RequirementAgent,
    CollectorAgent,
    AnalystAgent
)
from ..database import init_db, AgentTaskDB, AgentMessageDB, AnalysisTaskDB, get_db_connection
from ..auth import get_current_user
from ..services.audit_service import log_audit, ActionType, ResourceType, AuditStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    query: str
    style: Optional[str] = "balanced"


class AnalyzeResponse(BaseModel):
    """分析响应模型"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    query: str
    result: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: str
    task_id: str
    sender: str
    recipient: Optional[str]
    type: str
    content: Dict[str, Any]
    in_reply_to: Optional[str]
    timestamp: str


def get_client_info(request: Request):
    """获取客户端信息"""
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


@router.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    await init_db()
    logger.info("Database initialized")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    http_request: Request = None
):
    """
    启动分析任务
    
    使用主管代理协调需求解析、数据采集、分析等代理完成分析
    """
    from ..services.integral import IntegralService
    
    task_id = str(uuid.uuid4())
    user_id = current_user["id"]
    ip, user_agent = get_client_info(http_request) if http_request else (None, None)
    
    success, error_message, current_balance = await IntegralService.check_and_consume(user_id, cost=1)
    
    if not success:
        raise HTTPException(
            status_code=403,
            detail={
                "message": error_message,
                "code": "INSUFFICIENT_INTEGRAL",
                "current_balance": current_balance,
                "required": 1
            }
        )
    
    await AgentTaskDB.create_task(task_id, request.query)
    
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            INSERT INTO analysis_tasks (id, user_id, query, status, progress, style)
            VALUES (?, ?, ?, 'pending', 0, ?)
            """,
            (task_id, user_id, request.query, request.style)
        )
        await conn.commit()
    finally:
        await conn.close()
    
    log_audit(
        action_type=ActionType.TASK_CREATE,
        user_id=user_id,
        username=current_user.get("email"),
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.TASK,
        resource_id=task_id,
        new_value={"query": request.query, "style": request.style},
        status=AuditStatus.SUCCESS,
    )
    
    background_tasks.add_task(
        run_agent_workflow,
        task_id,
        user_id,
        request.query,
        request.style
    )
    
    logger.info(f"Task {task_id} created for user {user_id}")
    
    return AnalyzeResponse(
        task_id=task_id,
        status="pending",
        message="任务已创建，正在处理中"
    )


async def run_agent_workflow(task_id: str, user_id: str, query: str, style: str = "balanced"):
    """
    运行代理工作流
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
        query: 用户查询
        style: 分析风格
    """
    try:
        await AgentTaskDB.update_task_status(task_id, "running")
        
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE analysis_tasks SET status = 'running' WHERE id = ?",
                (task_id,)
            )
            await conn.commit()
        finally:
            await conn.close()
        
        scheduler = AgentScheduler(task_id)
        
        supervisor = scheduler.register_agent(SupervisorAgent, "supervisor")
        scheduler.register_agent(RequirementAgent, "requirement")
        scheduler.register_agent(CollectorAgent, "collector")
        scheduler.register_agent(AnalystAgent, "analyst", style=style)
        
        await scheduler.start_all()
        
        await asyncio.sleep(0.5)
        
        await scheduler.send_initial_message(
            recipient="supervisor",
            content={
                "action": "start",
                "query": query
            }
        )
        
        max_wait = 30
        waited = 0
        while waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
            
            progress = min(waited * 3, 90)
            conn = await get_db_connection()
            try:
                await conn.execute(
                    "UPDATE analysis_tasks SET progress = ? WHERE id = ?",
                    (progress, task_id)
                )
                await conn.commit()
            finally:
                await conn.close()
            
            if supervisor.get_workflow_state() == "completed":
                break
            if supervisor.get_workflow_state() == "failed":
                raise Exception("Workflow failed")
        
        result = supervisor.get_workflow_result()
        
        await AgentTaskDB.update_task_status(task_id, "completed", result)
        
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE analysis_tasks SET status = 'completed', progress = 100 WHERE id = ?",
                (task_id,)
            )
            await conn.commit()
        finally:
            await conn.close()
        
        await scheduler.stop_all()
        
        logger.info(f"Task {task_id} completed")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        await AgentTaskDB.update_task_status(
            task_id, 
            "failed", 
            {"error": str(e)}
        )
        
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE analysis_tasks SET status = 'failed' WHERE id = ?",
                (task_id,)
            )
            await conn.commit()
        finally:
            await conn.close()


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        TaskStatusResponse: 任务状态
    """
    task = await AgentTaskDB.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        query=task.get("query", ""),
        result=task.get("result"),
        created_at=task.get("created_at"),
        updated_at=task.get("updated_at")
    )


@router.get("/tasks/{task_id}/messages", response_model=List[MessageResponse])
async def get_task_messages(task_id: str):
    """
    获取任务的所有消息
    
    Args:
        task_id: 任务ID
        
    Returns:
        List[MessageResponse]: 消息列表
    """
    task = await AgentTaskDB.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    messages = await AgentMessageDB.get_messages_by_task(task_id)
    
    return [
        MessageResponse(
            id=msg["id"],
            task_id=msg["task_id"],
            sender=msg["sender"],
            recipient=msg["recipient"],
            type=msg["type"],
            content=msg.get("content", {}),
            in_reply_to=msg.get("in_reply_to"),
            timestamp=msg.get("timestamp", "")
        )
        for msg in messages
    ]


@router.get("/tasks", response_model=List[TaskStatusResponse])
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """
    列出任务
    
    Args:
        status: 状态过滤
        limit: 数量限制
        
    Returns:
        List[TaskStatusResponse]: 任务列表
    """
    tasks = await AgentTaskDB.list_tasks(status, limit)
    
    return [
        TaskStatusResponse(
            task_id=task["task_id"],
            status=task["status"],
            query=task.get("query", ""),
            result=task.get("result"),
            created_at=task.get("created_at"),
            updated_at=task.get("updated_at")
        )
        for task in tasks
    ]
