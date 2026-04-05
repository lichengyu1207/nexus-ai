"""
三省六部治理API路由
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..database_pg import get_db
from ..governance import (
    ThreeDepartmentsScheduler,
    AgentMarket,
    SalaryManager,
    agent_market,
    salary_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/governance", tags=["governance"])


class TaskRequest(BaseModel):
    """任务请求"""
    request: str = Field(..., description="用户请求内容")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")


class TaskResponse(BaseModel):
    """任务响应"""
    success: bool
    task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    integral_cost: Optional[int] = None
    steps: Optional[list] = None
    error: Optional[str] = None


_schedulers: Dict[str, ThreeDepartmentsScheduler] = {}


async def get_scheduler(user_id: str) -> ThreeDepartmentsScheduler:
    """获取用户的调度器实例"""
    if user_id not in _schedulers:
        scheduler = ThreeDepartmentsScheduler(user_id)
        await scheduler.initialize()
        _schedulers[user_id] = scheduler
    return _schedulers[user_id]


@router.post("/task", response_model=TaskResponse)
async def submit_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    提交任务，触发三省流程
    
    流程：
    1. 中书省（决策与规划）
    2. 门下省（审核与监督）
    3. 尚书省（执行与协调）
    4. 各部执行
    5. 结果汇总
    """
    user_id = current_user["id"]
    
    try:
        scheduler = await get_scheduler(user_id)
        
        result = await scheduler.process_request(
            request=request.request,
            context=request.context or {}
        )
        
        if result.get("success"):
            integral_cost = result.get("integral_cost", 0)
            if integral_cost > 0:
                from ..governance.salary import salary_manager
                await salary_manager.initialize()
                
                async with get_db() as db:
                    user_row = await db.fetchone(
                        "SELECT integral FROM users WHERE id = $1",
                        user_id
                    )
                    
                    if user_row and (user_row["integral"] or 0) >= integral_cost:
                        await db.execute(
                            "UPDATE users SET integral = integral - $1, total_spent_integral = COALESCE(total_spent_integral, 0) + $1 WHERE id = $2",
                            integral_cost, user_id
                        )
                        
                        await db.execute(
                            """INSERT INTO integral_logs (id, user_id, change, action_type, reason, created_at)
                               VALUES ($1, $2, $3, $4, $5, $6)""",
                            str(uuid.uuid4()),
                            user_id,
                            -integral_cost,
                            "governance_task",
                            f"三省六部任务执行：{request.request[:50]}...",
                            datetime.utcnow().isoformat()
                        )
        
        return TaskResponse(
            success=result.get("success", False),
            task_id=result.get("task_id"),
            result=result.get("result"),
            integral_cost=result.get("integral_cost"),
            steps=result.get("steps"),
            error=result.get("error"),
        )
        
    except Exception as e:
        logger.error(f"Submit task error: {e}")
        return TaskResponse(
            success=False,
            error=str(e),
        )


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    查询任务执行状态
    """
    user_id = current_user["id"]
    
    scheduler = _schedulers.get(user_id)
    if not scheduler:
        raise HTTPException(status_code=404, detail="调度器未初始化")
    
    status = scheduler.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status


@router.get("/agents")
async def get_user_agents(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的内阁组成（三省六部智能体）
    """
    user_id = current_user["id"]
    
    scheduler = _schedulers.get(user_id)
    if not scheduler:
        scheduler = await get_scheduler(user_id)
    
    agents = scheduler.get_user_agents()
    
    async with get_db() as db:
        user_agents = await db.fetch(
            """SELECT ua.*, am.name, am.department, am.skills, am.description
               FROM user_agents ua
               JOIN agents_market am ON ua.agent_id = am.id
               WHERE ua.user_id = $1 AND ua.status = $2
               ORDER BY ua.recruited_at DESC""",
            user_id, "active"
        )
        
        recruited_agents = []
        for row in user_agents:
            recruited_agents.append({
                "id": row["id"],
                "agent_id": row["agent_id"],
                "name": row["name"],
                "department": row["department"],
                "level": row["level"],
                "salary": row["salary"],
                "status": row["status"],
                "recruited_at": row["recruited_at"].isoformat() if row["recruited_at"] else None,
                "skills": row["skills"],
                "description": row["description"],
            })
    
    return {
        "success": True,
        "core_agents": agents,
        "recruited_agents": recruited_agents,
        "total_count": len(agents) + len(recruited_agents),
    }


@router.get("/finance")
async def get_finance_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    获取财务摘要
    """
    user_id = current_user["id"]
    
    await salary_manager.initialize()
    summary = await salary_manager.get_finance_summary(user_id)
    
    return {
        "success": True,
        "summary": summary.to_dict(),
    }


@router.get("/salary-logs")
async def get_salary_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    查看薪资消耗记录
    """
    user_id = current_user["id"]
    
    await salary_manager.initialize()
    logs = await salary_manager.get_salary_logs(user_id, limit, offset)
    
    return {
        "success": True,
        "logs": [log.to_dict() for log in logs],
        "count": len(logs),
    }


@router.get("/agent-stats")
async def get_agent_salary_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取智能体薪资统计
    """
    user_id = current_user["id"]
    
    await salary_manager.initialize()
    stats = await salary_manager.get_agent_salary_stats(user_id)
    
    return {
        "success": True,
        "stats": stats,
    }


@router.get("/departments")
async def get_departments_info():
    """
    获取三省六部信息
    """
    return {
        "success": True,
        "departments": {
            "三省": [
                {
                    "name": "中书省",
                    "role": "决策与规划",
                    "agent": "中书令",
                    "description": "接收用户需求，拆解任务，制定执行方案，分派给尚书省"
                },
                {
                    "name": "门下省",
                    "role": "审核与监督",
                    "agent": "门下侍郎",
                    "description": "审核中书省的方案，监督执行过程，确保合规，可驳回或建议修改"
                },
                {
                    "name": "尚书省",
                    "role": "执行与协调",
                    "agent": "尚书令",
                    "description": "统领六部，协调资源，确保各部完成任务，并汇总结果"
                }
            ],
            "六部": [
                {
                    "name": "吏部",
                    "role": "智能体管理",
                    "agent": "吏部尚书",
                    "description": "管理智能体招募、晋升、考核、解雇"
                },
                {
                    "name": "户部",
                    "role": "财务与积分",
                    "agent": "户部尚书",
                    "description": "处理积分收支、用户账单、智能体薪资"
                },
                {
                    "name": "礼部",
                    "role": "外部交流与咨询",
                    "agent": "礼部尚书",
                    "description": "负责智能咨询、客户服务、对外沟通"
                },
                {
                    "name": "兵部",
                    "role": "数据采集与情报",
                    "agent": "兵部尚书",
                    "description": "网络爬虫、API调用、数据采集"
                },
                {
                    "name": "刑部",
                    "role": "规则与风控",
                    "agent": "刑部尚书",
                    "description": "合规检查、风险预警、异常监控"
                },
                {
                    "name": "工部",
                    "role": "任务分析与报告生成",
                    "agent": "工部尚书",
                    "description": "房产分析报告生成、任务处理"
                }
            ]
        }
    }
