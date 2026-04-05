"""
任务管理API路由
为已认证用户提供任务创建、查询、管理功能
支持SSE实时推送和任务队列异步处理
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import uuid
import asyncio
import logging
import json

from ..models import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskStepResponse,
    TaskMessagesResponse,
    AgentSummary,
    BatchTaskCreate,
    BatchTaskResponse
)
from ..auth import get_current_user, get_current_user_optional
from ..database import (
    get_db,
    get_db_connection,
    AgentTaskDB,
    SearchDB,
    AnalysisTaskDB,
    AnalysisStepDB,
    AgentMessageDB,
    AnalysisReportDB,
    ReportDB
)
from ..sse_manager import sse_manager
from ..services.audit_service import log_audit, ActionType, ResourceType, AuditStatus
from ..services.task_queue import get_task_queue, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def process_analysis_task(data: dict) -> dict:
    """处理分析任务（队列处理器）- 使用三省六部制系统 + 智能缓存"""
    from ..services.progress_manager import progress_manager
    from ..sse_manager import sse_manager as task_sse_manager
    from ..governance import ThreeDepartmentsScheduler
    from ..services.task_analysis_cache import get_task_analysis_cache
    
    task_id = data.get("task_id")
    user_id = data.get("user_id")
    query = data.get("query")
    style = data.get("style", "balanced")
    
    try:
        cache = await get_task_analysis_cache()
        cached_result = await cache.get_cached_result(query, style)
        if cached_result:
            logger.info(f"Task {task_id}: Using cached result for query: {query[:50]}...")
            await AnalysisTaskDB.update_task(
                task_id,
                status="completed",
                result=cached_result
            )
            await task_sse_manager.broadcast_status(task_id, "completed", {
                "progress": 100,
                "cached": True
            })
            return {"status": "completed", "result": cached_result, "cached": True}
        
        await progress_manager.create_progress(task_id)
        await progress_manager.start_step(task_id, "init", "正在初始化三省六部制分析系统...")
        
        await AnalysisTaskDB.update_task(task_id, status="running")
        await task_sse_manager.broadcast_status(task_id, "running", {"query": query})
        
        # 使用三省六部制系统
        scheduler = ThreeDepartmentsScheduler(user_id)
        
        # 注册事件回调
        async def on_status_update(event_data):
            await task_sse_manager.broadcast_workflow_step(
                task_id,
                event_data.get("status", "unknown"),
                "governance",
                "status_update",
                "running",
                event_data
            )
        
        scheduler.on_event("task_status", on_status_update)
        
        await progress_manager.complete_step(task_id, "init", {"system": "三省六部制"})
        
        # 步骤2: 中书省规划
        await progress_manager.start_step(task_id, "zhongshu", "中书省正在制定分析方案...")
        
        await task_sse_manager.broadcast_workflow_step(
            task_id, "zhongshu_planning", "中书省", "planning", "running",
            {"query": query, "description": "任务拆解与策略制定"}
        )
        
        # 步骤3: 门下省审核
        await progress_manager.start_step(task_id, "menxia", "门下省正在审核方案...")
        
        await task_sse_manager.broadcast_workflow_step(
            task_id, "menxia_reviewing", "门下省", "reviewing", "running",
            {"description": "合规检查与方案审核"}
        )
        
        # 步骤4: 尚书省执行
        await progress_manager.start_step(task_id, "shangshu", "尚书省正在执行分析任务...")
        
        await task_sse_manager.broadcast_workflow_step(
            task_id, "shangshu_executing", "尚书省", "executing", "running",
            {"description": "六部协同执行分析任务"}
        )
        
        # 执行三省六部制工作流
        result = await scheduler.process_request(query, {"style": style, "task_id": task_id})
        
        await progress_manager.complete_step(task_id, "shangshu", {"execution_complete": True})
        
        # 步骤5: 报告生成
        await progress_manager.start_step(task_id, "report", "正在生成分析报告...")
        
        await AnalysisTaskDB.update_task(
            task_id,
            status="completed",
            result=result
        )
        
        await update_task_progress(task_id, 100)
        await task_sse_manager.broadcast_status(task_id, "completed", {"progress": 100})
        await task_sse_manager.broadcast_workflow_step(
            task_id, "complete", "scheduler", "workflow_done", "completed",
            {"result": result, "system": "三省六部制"}
        )
        
        await progress_manager.complete_step(task_id, "report")
        await progress_manager.complete_task(task_id, result)
        
        try:
            await cache.set_cached_result(query, result, style)
            logger.info(f"Task {task_id}: Result cached for query: {query[:50]}...")
        except Exception as cache_err:
            logger.warning(f"Failed to cache result: {cache_err}")
        
        return {"status": "completed", "result": result, "cached": False}
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        await AnalysisTaskDB.update_task(
            task_id,
            status="failed",
            result={"error": str(e)}
        )
        await task_sse_manager.broadcast_status(task_id, "failed", {"error": str(e)})
        await progress_manager.fail_task(task_id, str(e))
        return {"status": "failed", "error": str(e)}


# Handler registration moved to lifespan startup phase
# See app lifespan in main.py for registration call


async def register_task_handlers():
    """Register task queue handlers - called during app lifespan startup"""
    queue = await get_task_queue()
    queue.register_handler("analysis", process_analysis_task)
    logger.info(f"Registered 'analysis' handler with task_queue, handlers: {list(queue._handlers.keys())}")


def get_client_info(request: Request):
    """获取客户端信息"""
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


async def run_agent_workflow(task_id: str, user_id: str, query: str, style: str = "balanced"):
    """
    后台运行智能体工作流
    
    Args:
        task_id: 任务ID
        user_id: 用户ID
        query: 用户查询
        style: 分析风格
    """
    from ..agents import (
        AgentScheduler,
        SupervisorAgent,
        RequirementAgent,
        CollectorAgent,
        IntelligentAnalystAgent
    )
    
    try:
        await AnalysisTaskDB.update_task(task_id, status="running")
        await sse_manager.broadcast_status(task_id, "running", {"query": query})
        
        scheduler = AgentScheduler(task_id, db_enabled=True, sse_enabled=True)
        
        supervisor = scheduler.register_agent(SupervisorAgent, "supervisor")
        scheduler.register_agent(RequirementAgent, "requirement")
        scheduler.register_agent(CollectorAgent, "collector")
        scheduler.register_agent(
            IntelligentAnalystAgent,
            "analyst",
            style=style,
            use_memory=True
        )
        
        await sse_manager.broadcast_workflow_step(
            task_id, "init", "scheduler", "register_agents", "completed",
            {"agents": ["supervisor", "requirement", "collector", "analyst"]}
        )
        
        await scheduler.start_all()
        
        await asyncio.sleep(0.5)
        
        await scheduler.send_initial_message(
            recipient="supervisor",
            content={"action": "start", "query": query}
        )
        
        max_wait = 60
        waited = 0
        while waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
            
            state = supervisor.get_workflow_state()
            
            progress = min(waited * 2, 90)
            await update_task_progress(task_id, progress)
            await sse_manager.broadcast_status(task_id, "running", {"progress": progress})
            
            if state == "completed":
                break
            if state == "failed":
                await AnalysisTaskDB.update_task(
                    task_id,
                    status="failed",
                    result={"error": "Workflow failed"}
                )
                await sse_manager.broadcast_status(task_id, "failed", {"error": "Workflow failed"})
                await scheduler.stop_all()
                return
        
        result = supervisor.get_workflow_result()
        
        await AnalysisTaskDB.update_task(
            task_id,
            status="completed",
            result=result
        )
        
        await update_task_progress(task_id, 100)
        await sse_manager.broadcast_status(task_id, "completed", {"progress": 100})
        await sse_manager.broadcast_workflow_step(
            task_id, "complete", "scheduler", "workflow_done", "completed",
            {"result": result}
        )
        
        await scheduler.stop_all()
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        await AnalysisTaskDB.update_task(
            task_id,
            status="failed",
            result={"error": str(e)}
        )
        await sse_manager.broadcast_status(task_id, "failed", {"error": str(e)})


async def update_task_progress(task_id: str, progress: int):
    """更新任务进度"""
    async with get_db() as conn:
        await conn.execute(
            "UPDATE analysis_tasks SET progress = ? WHERE id = ?",
            (progress, task_id)
        )


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """
    创建分析任务（使用任务队列）
    """
    from ..services.integral import IntegralService
    
    task_id = str(uuid.uuid4())
    user_id = current_user["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
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
    
    async with get_db() as conn:
        import json
        await conn.execute(
            """
            INSERT INTO analysis_tasks (id, query, status, progress, style, input_data)
            VALUES ($1, $2, 'queued', 0, $3, $4)
            """,
            task_id, task_data.query, task_data.style, json.dumps({"user_id": user_id})
        )
    
    await SearchDB.index_task(
        task_id=task_id,
        query=task_data.query,
        user_id=user_id,
        created_at=None
    )
    
    log_audit(
        action_type=ActionType.TASK_CREATE,
        user_id=user_id,
        username=current_user.get("email"),
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.TASK,
        resource_id=task_id,
        new_value={"query": task_data.query, "style": task_data.style},
        status=AuditStatus.SUCCESS,
    )
    
    queue = await get_task_queue()
    queue_task_id = await queue.enqueue(
        task_id=task_id,
        priority=5,
        metadata={
            "task_type": "analysis",
            "user_id": user_id,
            "query": task_data.query,
            "style": task_data.style
        }
    )
    
    logger.info(f"Task {task_id} submitted to queue, queue_id: {queue_task_id}")
    
    return TaskResponse(
        id=task_id,
        user_id=user_id,
        query=task_data.query,
        status="queued",
        progress=0,
        style=task_data.style,
        created_at=None,
        completed_at=None,
        agents=[]
    )


@router.post("/batch", response_model=BatchTaskResponse, status_code=201)
async def create_batch_tasks(
    task_data: BatchTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """
    批量创建分析任务
    
    一次最多创建5个任务，每个任务消耗1积分
    
    Args:
        task_data: 批量任务数据
        background_tasks: 后台任务
        current_user: 当前用户
        request: 请求对象
        
    Returns:
        BatchTaskResponse: 批量创建结果
    """
    from ..services.integral import IntegralService
    
    user_id = current_user["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    queries = [q.strip() for q in task_data.queries if q.strip()]
    if not queries:
        raise HTTPException(status_code=400, detail="请输入至少一个有效的查询")
    
    task_count = len(queries)
    
    success, error_message, current_balance = await IntegralService.check_and_consume(
        user_id, cost=task_count
    )
    
    if not success:
        raise HTTPException(
            status_code=403,
            detail={
                "message": error_message,
                "code": "INSUFFICIENT_INTEGRAL",
                "current_balance": current_balance,
                "required": task_count
            }
        )
    
    created_tasks = []
    failed_count = 0
    
    for query in queries:
        try:
            task_id = str(uuid.uuid4())
            
            async with get_db() as conn:
                await conn.execute(
                    """
                    INSERT INTO analysis_tasks (id, user_id, query, status, progress, style)
                    VALUES (?, ?, ?, 'pending', 0, ?)
                    """,
                    (task_id, user_id, query, task_data.style)
                )
            
            await SearchDB.index_task(
                task_id=task_id,
                query=query,
                user_id=user_id,
                created_at=None
            )
            
            log_audit(
                action_type=ActionType.TASK_CREATE,
                user_id=user_id,
                username=current_user.get("email"),
                ip_address=ip,
                user_agent=user_agent,
                resource_type=ResourceType.TASK,
                resource_id=task_id,
                new_value={"query": query, "style": task_data.style, "batch": True},
                status=AuditStatus.SUCCESS,
            )
            
            background_tasks.add_task(
                run_agent_workflow,
                task_id,
                user_id,
                query,
                task_data.style
            )
            
            created_tasks.append(TaskResponse(
                id=task_id,
                user_id=user_id,
                query=query,
                status="pending",
                progress=0,
                style=task_data.style,
                created_at=None,
                completed_at=None,
                agents=[]
            ))
            
        except Exception as e:
            logger.error(f"Failed to create task for query '{query}': {e}")
            failed_count += 1
    
    logger.info(f"Batch created {len(created_tasks)} tasks for user {user_id}")
    
    return BatchTaskResponse(
        tasks=created_tasks,
        total=task_count,
        success_count=len(created_tasks),
        failed_count=failed_count,
        integral_consumed=len(created_tasks)
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务列表
    
    Args:
        limit: 数量限制
        offset: 偏移量
        status: 状态过滤
        current_user: 当前用户
        
    Returns:
        TaskListResponse: 任务列表
    """
    user_id = current_user["id"]
    
    async with get_db() as conn:
        if status:
            rows = await conn.fetch(
                """
                SELECT * FROM analysis_tasks 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                user_id, status, limit, offset
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM analysis_tasks 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                user_id, limit, offset
            )
        
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ?",
            user_id
        )
        
        tasks = []
        for row in rows:
            task = dict(row)
            tasks.append(TaskResponse(
                id=task["id"],
                user_id=task["user_id"],
                query=task["query"],
                status=task["status"],
                progress=task.get("progress", 0),
                style=task.get("style", "balanced"),
                created_at=task.get("created_at"),
                completed_at=task.get("completed_at"),
                agents=[]
            ))
        
        return TaskListResponse(
            tasks=tasks,
            total=total,
            limit=limit,
            offset=offset
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务详情
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        TaskResponse: 任务详情
    """
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM analysis_tasks WHERE id = $1",
            task_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = dict(row)
        
        # 检查用户权限
        input_data = task.get("input_data")
        if isinstance(input_data, str):
            import json
            input_data = json.loads(input_data)
        if input_data and input_data.get("user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="无权访问此任务")
        
        agent_rows = await conn.fetch(
            """
            SELECT DISTINCT sender as agent_name, 
                   MIN(timestamp) as started_at,
                   MAX(timestamp) as completed_at
            FROM agent_messages 
            WHERE task_id = $1
            GROUP BY sender
            """,
            task_id
        )
        
        agents = []
        for agent_row in agent_rows:
            agents.append(AgentSummary(
                name=agent_row["agent_name"],
                status="completed" if task["status"] == "completed" else "running",
                started_at=agent_row["started_at"],
                completed_at=agent_row["completed_at"]
            ))
        
        result = None
        if task.get("result"):
            try:
                result = json.loads(task["result"])
            except:
                result = task["result"]
        
        # 从 input_data 中提取 user_id
        input_data = task.get("input_data")
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except:
                input_data = {}
        user_id = input_data.get("user_id") if isinstance(input_data, dict) else None
        
        return TaskResponse(
            id=task["id"],
            user_id=user_id or current_user["id"],
            query=task["query"],
            status=task["status"],
            progress=task.get("progress", 0),
            style=task.get("style", "balanced"),
            created_at=task.get("created_at"),
            completed_at=task.get("completed_at"),
            agents=agents,
            result=result
        )


@router.get("/{task_id}/steps", response_model=list)
async def get_task_steps(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务步骤
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        list: 步骤列表
    """
    async with get_db() as conn:
        exists = await conn.fetchval(
            "SELECT id FROM analysis_tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"])
        )
        if not exists:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        rows = await conn.fetch(
            """
            SELECT * FROM analysis_steps 
            WHERE task_id = ?
            ORDER BY step_order ASC
            """,
            task_id
        )
        
        steps = []
        for row in rows:
            step = dict(row)
            steps.append(TaskStepResponse(
                id=step["id"],
                task_id=step["task_id"],
                agent_name=step.get("agent_name", "unknown"),
                step_name=step["step_name"],
                step_order=step["step_order"],
                status=step["status"],
                input_data=json.loads(step["input_data"]) if step.get("input_data") else None,
                output_data=json.loads(step["output_data"]) if step.get("output_data") else None,
                error_message=step.get("error_message"),
                started_at=step.get("started_at"),
                completed_at=step.get("completed_at")
            ))
        
        return steps


@router.get("/{task_id}/messages", response_model=TaskMessagesResponse)
async def get_task_messages(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务消息
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        TaskMessagesResponse: 消息列表
    """
    async with get_db() as conn:
        exists = await conn.fetchval(
            "SELECT id FROM analysis_tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"])
        )
        if not exists:
            raise HTTPException(status_code=404, detail="任务不存在")
    
    messages = await AgentMessageDB.get_messages_by_task(task_id)
    
    return TaskMessagesResponse(
        task_id=task_id,
        messages=messages,
        total=len(messages)
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """
    删除任务
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        request: 请求对象
        
    Returns:
        dict: 删除结果
    """
    user_id = current_user["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT id, query, status FROM analysis_tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        if not row:
            log_audit(
                action_type=ActionType.TASK_DELETE,
                user_id=user_id,
                username=current_user.get("email"),
                ip_address=ip,
                user_agent=user_agent,
                resource_type=ResourceType.TASK,
                resource_id=task_id,
                status=AuditStatus.FAILURE,
                error_message="任务不存在或无权删除",
            )
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = dict(row)
        old_value = {"query": task["query"], "status": task["status"]}
        
        await conn.execute("DELETE FROM agent_messages WHERE task_id = ?", (task_id,))
        await conn.execute("DELETE FROM analysis_steps WHERE task_id = ?", (task_id,))
        await conn.execute("DELETE FROM analysis_tasks WHERE id = ?", (task_id,))
        
        log_audit(
            action_type=ActionType.TASK_DELETE,
            user_id=user_id,
            username=current_user.get("email"),
            ip_address=ip,
            user_agent=user_agent,
            resource_type=ResourceType.TASK,
            resource_id=task_id,
            old_value=old_value,
            status=AuditStatus.SUCCESS,
        )
        
        return {"message": "任务已删除", "task_id": task_id}


@router.delete("")
async def batch_delete_tasks(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    批量删除任务
    
    Args:
        request: 请求对象
        current_user: 当前用户
        
    Returns:
        dict: 删除结果
    """
    body = await request.json()
    task_ids = body.get("taskIds", []) or body.get("task_ids", [])
    
    if not task_ids:
        raise HTTPException(status_code=400, detail="请提供要删除的任务ID")
    
    user_id = current_user["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    deleted_count = 0
    failed_count = 0
    
    async with get_db() as conn:
        for task_id in task_ids:
            row = await conn.fetchrow(
                "SELECT id, query, status FROM analysis_tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )
            if not row:
                failed_count += 1
                continue
            
            task = dict(row)
            
            await conn.execute("DELETE FROM agent_messages WHERE task_id = ?", (task_id,))
            await conn.execute("DELETE FROM analysis_steps WHERE task_id = ?", (task_id,))
            await conn.execute("DELETE FROM analysis_tasks WHERE id = ?", (task_id,))
            
            deleted_count += 1
            
            await log_audit(
                action_type=ActionType.TASK_DELETE,
                user_id=user_id,
                username=current_user.get("email"),
                ip_address=ip,
                user_agent=user_agent,
                resource_type=ResourceType.TASK,
                resource_id=task_id,
                old_value={"query": task["query"], "status": task["status"]},
                status=AuditStatus.SUCCESS,
            )
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "message": f"成功删除 {deleted_count} 个任务"
    }


@router.get("/stats")
async def get_task_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务统计
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 任务统计
    """
    user_id = current_user["id"]
    
    async with get_db() as conn:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ?",
            (user_id,)
        )
        completed = await conn.fetchval(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ? AND status = 'completed'",
            (user_id,)
        )
        processing = await conn.fetchval(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ? AND status IN ('pending', 'queued', 'running')",
            (user_id,)
        )
        failed = await conn.fetchval(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ? AND status = 'failed'",
            (user_id,)
        )
    
    return {
        "total": total or 0,
        "completed": completed or 0,
        "processing": processing or 0,
        "failed": failed or 0
    }


@router.get("/{task_id}/progress")
async def get_task_progress(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务实时进度
    
    返回当前进度、步骤详情、预计剩余时间等信息
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        Dict: 进度信息
    """
    from ..services.progress_manager import progress_manager
    
    user_id = current_user["id"]
    
    async with get_db() as conn:
        cursor = await conn.execute(
            "SELECT user_id FROM analysis_tasks WHERE id = ?",
            (task_id,)
        )
        task = await cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="无权访问此任务")
    
    progress = progress_manager.get_progress(task_id)
    
    if not progress:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT status, progress FROM analysis_tasks WHERE id = ?",
                (task_id,)
            )
            task = await cursor.fetchone()
            
            if task:
                progress = {
                    "task_id": task_id,
                    "status": task["status"],
                    "overall_progress": task["progress"] or 0,
                    "current_step": 0,
                    "total_steps": 5,
                    "elapsed_time": 0,
                    "estimated_remaining": 0,
                    "current_step_name": None,
                    "current_step_description": None,
                    "steps": [],
                }
    
    return progress


@router.get("/{task_id}/stream")
async def stream_task_events(
    task_id: str,
    token: str = None,
    current_user: dict = Depends(get_current_user_optional)
):
    """
    SSE事件流端点
    实时推送任务进度、消息和工作流事件
    
    Args:
        task_id: 任务ID
        token: JWT令牌（可选，用于EventSource）
        current_user: 当前用户
        
    Returns:
        StreamingResponse: SSE事件流
    """
    # 如果 URL 参数中有 token，使用它来验证用户
    if token and not current_user:
        from ..auth import decode_access_token
        token_data = decode_access_token(token)
        if token_data and token_data.user_id:
            from ..database import UserDB
            current_user = await UserDB.get_user_by_id(token_data.user_id)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="未授权")
    
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT id, status FROM analysis_tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"])
        )
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_status = row["status"]
    
    async def event_generator():
        """
        SSE事件生成器
        """
        queue = await sse_manager.subscribe(task_id)
        
        try:
            yield f"event: connected\ndata: {{\"task_id\": \"{task_id}\", \"status\": \"{task_status}\"}}\n\n"
            
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse_format()
                    
                    if event.event == "status" and event.data.get("status") in ["completed", "failed"]:
                        break
                        
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {{\"timestamp\": \"{__import__('datetime').datetime.now().isoformat()}\"}}\n\n"
                    
                    async with get_db() as conn:
                        row = await conn.fetchrow(
                            "SELECT status FROM analysis_tasks WHERE id = ?",
                            (task_id,)
                        )
                        if row and row["status"] in ["completed", "failed"]:
                            yield f"event: status\ndata: {{\"task_id\": \"{task_id}\", \"status\": \"{row['status']}\"}}\n\n"
                            break
                        
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


@router.get("/{task_id}/report")
async def get_task_report(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务分析报告
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        dict: 分析报告
    """
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT id, status, query, style, result FROM analysis_tasks WHERE id = ? AND user_id = ?",
            (task_id, current_user["id"])
        )
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_status = row["status"]
        task_query = row["query"]
        task_style = row["style"]
        task_result = json.loads(row["result"]) if row["result"] else None
    
    if task_status != "completed":
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task_status}")
    
    from ..database import AnalysisReportDB
    report = await AnalysisReportDB.get_report_by_task(task_id)
    
    if not report:
        from ..agents import ReportAgent, MessageBus
        
        if not task_result:
            raise HTTPException(status_code=404, detail="任务结果不存在，无法生成报告")
        
        bus = MessageBus(task_id)
        bus.register_agent("report")
        bus.register_agent("system")
        
        report_agent = ReportAgent(
            "report",
            task_id,
            bus,
            style=task_style,
            user_id=current_user["id"]
        )
        
        await report_agent.start()
        
        try:
            parsed = task_result.get("parsed", {})
            data = task_result.get("data", {})
            analysis = task_result.get("analysis", {})
            
            from ..agents.message import AgentMessage, MessageType
            import uuid
            
            mock_message = AgentMessage(
                id=str(uuid.uuid4()),
                task_id=task_id,
                sender="system",
                recipient="report",
                type=MessageType.REQUEST,
                content={
                    "action": "generate",
                    "query": task_query,
                    "parsed": parsed,
                    "data": data,
                    "analysis": analysis
                }
            )
            
            await report_agent.handle_message(mock_message)
            
            report = await AnalysisReportDB.get_report_by_task(task_id)
            
        finally:
            await report_agent.stop()
        
        if not report:
            raise HTTPException(status_code=500, detail="报告生成失败")
    
    formatted_report = {
        'id': report.get('id'),
        'task_id': report.get('task_id'),
        'query': report.get('query', ''),
        'style': report.get('style', 'balanced'),
        'confidence_score': report.get('confidence_score'),
        'executive_summary': report.get('executive_summary', ''),
        'core_findings': report.get('core_findings', {}),
        'detailed_analysis': report.get('detailed_analysis', {}),
        'investment_advice': report.get('investment_advice', {}),
        'risk_warnings': report.get('risk_warnings', []),
        'data_sources': report.get('data_sources', []),
        'created_at': report.get('created_at'),
        'completed_at': report.get('completed_at'),
    }
    
    return {
        "task_id": task_id,
        "report": formatted_report
    }
