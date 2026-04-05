"""
智能体自主工作API路由
包含自主工作设置、统计、日志等功能
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..governance.auto_work import auto_task_scheduler, task_executor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auto-work", tags=["auto-work"])


class SetAutoWorkRequest(BaseModel):
    """设置自主工作请求"""
    agent_id: str = Field(..., description="智能体ID")
    enabled: bool = Field(..., description="是否启用")


class SetDailyLimitRequest(BaseModel):
    """设置每日限额请求"""
    agent_id: str = Field(..., description="智能体ID")
    limit_seconds: int = Field(..., ge=0, le=86400, description="每日最大工作秒数")


@router.get("/stats")
async def get_auto_work_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户自主工作统计
    
    包含所有智能体的自主工作状态和收益
    """
    user_id = current_user["id"]
    
    await auto_task_scheduler.initialize()
    stats = await auto_task_scheduler.get_user_auto_work_stats(user_id)
    
    return {
        "success": True,
        **stats
    }


@router.post("/toggle")
async def toggle_auto_work(
    request: SetAutoWorkRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    开启/关闭智能体自主工作
    """
    from ..database_pg import get_db
    
    user_id = current_user["id"]
    
    async with get_db() as db:
        agent = await db.fetchone(
            "SELECT id FROM user_agents WHERE id = $1 AND user_id = $2",
            request.agent_id, user_id
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        await db.execute(
            "UPDATE user_agents SET auto_work_enabled = $1 WHERE id = $2",
            request.enabled, request.agent_id
        )
        
        return {
            "success": True,
            "agent_id": request.agent_id,
            "enabled": request.enabled,
            "message": f"自主工作已{'开启' if request.enabled else '关闭'}"
        }


@router.post("/set-limit")
async def set_daily_limit(
    request: SetDailyLimitRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    设置智能体每日工作限额
    """
    from ..database_pg import get_db
    
    user_id = current_user["id"]
    
    async with get_db() as db:
        agent = await db.fetchone(
            "SELECT id FROM user_agents WHERE id = $1 AND user_id = $2",
            request.agent_id, user_id
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        await db.execute(
            "UPDATE user_agents SET daily_auto_work_limit = $1 WHERE id = $2",
            request.limit_seconds, request.agent_id
        )
        
        return {
            "success": True,
            "agent_id": request.agent_id,
            "daily_limit": request.limit_seconds,
            "message": f"每日限额已设置为 {request.limit_seconds} 秒"
        }


@router.get("/logs")
async def get_work_logs(
    agent_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    获取自主工作日志
    """
    from ..database_pg import get_db
    
    user_id = current_user["id"]
    
    async with get_db() as db:
        if agent_id:
            logs = await db.fetch(
                """SELECT awl.*, at.name as agent_name
                   FROM agent_work_logs awl
                   JOIN user_agents ua ON awl.agent_id = ua.id
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE awl.user_id = $1 AND awl.agent_id = $2
                   ORDER BY awl.created_at DESC
                   LIMIT $3 OFFSET $4""",
                user_id, agent_id, limit, offset
            )
        else:
            logs = await db.fetch(
                """SELECT awl.*, at.name as agent_name
                   FROM agent_work_logs awl
                   JOIN user_agents ua ON awl.agent_id = ua.id
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE awl.user_id = $1
                   ORDER BY awl.created_at DESC
                   LIMIT $2 OFFSET $3""",
                user_id, limit, offset
            )
        
        result = []
        for log in logs:
            result.append({
                "id": log["id"],
                "agent_id": log["agent_id"],
                "agent_name": log["agent_name"],
                "task_type": log["task_type"],
                "duration_seconds": log["duration_seconds"],
                "reward_earned": log["reward_earned"],
                "status": log["status"],
                "created_at": log["created_at"].isoformat() if log["created_at"] else None,
            })
        
        return {
            "success": True,
            "logs": result,
            "count": len(result),
        }


@router.get("/tasks")
async def get_pending_tasks():
    """
    获取待执行任务列表
    """
    from ..database_pg import get_db
    
    async with get_db() as db:
        tasks = await db.fetch(
            """SELECT * FROM auto_tasks 
               WHERE status IN ('pending', 'assigned')
               ORDER BY priority DESC, created_at ASC
               LIMIT 50"""
        )
        
        return {
            "success": True,
            "tasks": [dict(t) for t in tasks],
            "count": len(tasks),
        }


@router.get("/task-types")
async def get_task_types():
    """
    获取任务类型信息
    """
    from ..governance.auto_work import TASK_TYPE_DEPARTMENTS, TASK_DURATION_RANGE
    
    task_types = []
    for task_type, depts in TASK_TYPE_DEPARTMENTS.items():
        duration = TASK_DURATION_RANGE.get(task_type, (30, 60))
        task_types.append({
            "type": task_type,
            "suitable_departments": depts,
            "duration_range": f"{duration[0]}-{duration[1]}秒",
        })
    
    return {
        "success": True,
        "task_types": task_types,
    }


@router.post("/trigger-assign")
async def trigger_task_assignment(
    current_user: dict = Depends(get_current_user)
):
    """
    手动触发任务分配
    """
    await auto_task_scheduler.initialize()
    count = await auto_task_scheduler.scan_and_assign()
    
    return {
        "success": True,
        "assigned_count": count,
        "message": f"已分配 {count} 个任务"
    }


@router.post("/trigger-execute")
async def trigger_task_execution(
    current_user: dict = Depends(get_current_user)
):
    """
    手动触发任务执行
    """
    await task_executor.initialize()
    count = await task_executor.execute_assigned_tasks()
    
    return {
        "success": True,
        "completed_count": count,
        "message": f"已完成 {count} 个任务"
    }
