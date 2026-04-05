"""
智能体监控仪表盘 - API路由
包含实时状态、任务监控、统计等功能
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..database_pg import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class StartTaskRequest(BaseModel):
    """启动任务请求"""
    task_type: str = Field(..., description="任务类型")
    input: str = Field("", description="任务输入")
    agent_ids: Optional[List[str]] = Field(None, description="指定智能体ID")
    auto_assign: bool = Field(True, description="自动分配")


TASK_DEPARTMENTS = {
    "analysis": ["工部"],
    "consult": ["礼部", "吏部"],
    "auto_work": ["兵部", "刑部", "工部", "礼部", "吏部"],
}

RARITY_COLORS = {
    "N": "#9e9e9e",
    "R": "#3498db",
    "SR": "#9b59b6",
    "SSR": "#f39c12",
    "UR": "#e74c3c",
}

RARITY_LEVEL_CAPS = {
    "N": 30,
    "R": 50,
    "SR": 70,
    "SSR": 90,
    "UR": 100,
}


@router.get("/agents-status")
async def get_agents_status(current_user: dict = Depends(get_current_user)):
    """获取所有智能体实时状态"""
    user_id = current_user["id"]
    
    async with get_db() as db:
        agents = await db.fetch(
            """SELECT ua.id, ua.status, ua.level, ua.rarity, ua.department,
                      ua.current_task_id, ua.current_task_type, ua.work_start_time,
                      ua.work_duration_seconds, ua.efficiency, ua.performance_today,
                      ua.auto_work_enabled, ua.daily_auto_work_seconds, ua.daily_auto_work_limit,
                      ua.total_auto_work_reward,
                      at.name, at.skills, at.stats, at.description, at.base_salary
               FROM user_agents ua
               JOIN agent_templates at ON ua.template_id = at.id
               WHERE ua.user_id = $1
               ORDER BY ua.level DESC""",
            user_id
        )
        
        result = []
        for agent in agents:
            current_task_desc = "空闲"
            if agent["status"] == "busy":
                current_task_desc = "执行用户任务中"
            elif agent["status"] == "working":
                current_task_desc = "自主工作中"
            
            result.append({
                "id": agent["id"],
                "name": agent["name"],
                "department": agent["department"],
                "level": agent["level"],
                "rarity": agent["rarity"],
                "rarity_color": RARITY_COLORS.get(agent["rarity"], "#9e9e9e"),
                "level_cap": RARITY_LEVEL_CAPS.get(agent["rarity"], 30),
                "status": agent["status"],
                "current_task_id": agent["current_task_id"],
                "current_task_type": agent["current_task_type"],
                "current_task_description": current_task_desc,
                "work_start_time": agent["work_start_time"].isoformat() if agent["work_start_time"] else None,
                "work_duration_seconds": agent["work_duration_seconds"] or 0,
                "efficiency": float(agent["efficiency"]) if agent["efficiency"] else 1.0,
                "performance_today": agent["performance_today"] or 0,
                "base_salary": agent["base_salary"],
                "skills": json.loads(agent["skills"]) if isinstance(agent["skills"], str) else agent["skills"],
                "stats": json.loads(agent["stats"]) if isinstance(agent["stats"], str) else agent["stats"],
                "description": agent["description"],
                "auto_work_enabled": agent["auto_work_enabled"],
                "daily_work_seconds": agent["daily_auto_work_seconds"] or 0,
                "daily_limit": agent["daily_auto_work_limit"] or 3600,
                "total_reward": agent["total_auto_work_reward"] or 0,
            })
        
        return {"success": True, "agents": result, "count": len(result)}


@router.get("/current-tasks")
async def get_current_tasks(current_user: dict = Depends(get_current_user)):
    """获取当前进行中的任务"""
    user_id = current_user["id"]
    
    async with get_db() as db:
        user_tasks = await db.fetch(
            """SELECT id, task_type, input, status, created_at, assigned_agents
               FROM user_tasks
               WHERE user_id = $1 AND status IN ('pending', 'processing')
               ORDER BY created_at DESC""",
            user_id
        )
        
        auto_tasks = await db.fetch(
            """SELECT t.id, t.task_type, t.description, t.status, t.started_at as created_at,
                      t.assigned_agent_id, t.base_reward, t.priority
               FROM auto_tasks t
               JOIN user_agents ua ON t.assigned_agent_id = ua.id
               WHERE ua.user_id = $1 AND t.status = 'assigned'
               ORDER BY t.priority DESC""",
            user_id
        )
        
        tasks = []
        
        for task in user_tasks:
            assigned_agents = json.loads(task["assigned_agents"]) if isinstance(task["assigned_agents"], str) else (task["assigned_agents"] or [])
            
            agent_names = []
            for aid in assigned_agents:
                agent = await db.fetchrow(
                    """SELECT ua.id, at.name 
                       FROM user_agents ua 
                       JOIN agent_templates at ON ua.template_id = at.id 
                       WHERE ua.id = $1""",
                    aid
                )
                if agent:
                    agent_names.append({"id": aid, "name": agent["name"]})
            
            tasks.append({
                "id": task["id"],
                "type": "user_task",
                "task_type": task["task_type"],
                "description": task["input"] or "用户任务",
                "status": task["status"],
                "progress": 50,
                "start_time": task["created_at"].isoformat() if task["created_at"] else None,
                "assigned_agents": agent_names,
            })
        
        for task in auto_tasks:
            agent = await db.fetchrow(
                """SELECT ua.id, at.name 
                   FROM user_agents ua 
                   JOIN agent_templates at ON ua.template_id = at.id 
                   WHERE ua.id = $1""",
                task["assigned_agent_id"]
            )
            
            tasks.append({
                "id": task["id"],
                "type": "auto_task",
                "task_type": task["task_type"],
                "description": task["description"],
                "status": task["status"],
                "progress": 30,
                "start_time": task["created_at"].isoformat() if task["created_at"] else None,
                "assigned_agents": [{"id": task["assigned_agent_id"], "name": agent["name"] if agent else "未知"}] if agent else [],
                "base_reward": task["base_reward"],
            })
        
        return {"success": True, "tasks": tasks, "count": len(tasks)}


@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """获取仪表盘统计数据"""
    user_id = current_user["id"]
    
    async with get_db() as db:
        total_agents = await db.fetchval(
            "SELECT COUNT(*) FROM user_agents WHERE user_id = $1", user_id
        )
        
        online_agents = await db.fetchval(
            "SELECT COUNT(*) FROM user_agents WHERE user_id = $1 AND status != 'offline'", user_id
        )
        
        busy_agents = await db.fetchval(
            "SELECT COUNT(*) FROM user_agents WHERE user_id = $1 AND status = 'busy'", user_id
        )
        
        auto_work_agents = await db.fetchval(
            "SELECT COUNT(*) FROM user_agents WHERE user_id = $1 AND status = 'working'", user_id
        )
        
        idle_agents = await db.fetchval(
            "SELECT COUNT(*) FROM user_agents WHERE user_id = $1 AND status = 'idle'", user_id
        )
        
        total_reward = await db.fetchval(
            "SELECT COALESCE(SUM(total_auto_work_reward), 0) FROM user_agents WHERE user_id = $1", user_id
        )
        
        today_work = await db.fetchval(
            "SELECT COALESCE(SUM(daily_auto_work_seconds), 0) FROM user_agents WHERE user_id = $1", user_id
        )
        
        pending_tasks = await db.fetchval(
            """SELECT COUNT(*) FROM user_tasks 
               WHERE user_id = $1 AND status IN ('pending', 'processing')""",
            user_id
        )
        
        return {
            "success": True,
            "stats": {
                "total_agents": total_agents or 0,
                "online_agents": online_agents or 0,
                "busy_agents": busy_agents or 0,
                "auto_work_agents": auto_work_agents or 0,
                "idle_agents": idle_agents or 0,
                "total_reward": total_reward or 0,
                "today_work_seconds": today_work or 0,
                "pending_tasks": pending_tasks or 0,
            }
        }


@router.post("/start-task")
async def start_task(
    request: StartTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """启动新任务"""
    user_id = current_user["id"]
    
    if request.task_type not in ["analysis", "consult", "auto_work"]:
        raise HTTPException(status_code=400, detail="无效的任务类型")
    
    async with get_db() as db:
        if request.auto_assign and not request.agent_ids:
            available = await db.fetch(
                """SELECT ua.id FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.user_id = $1 AND ua.status = 'idle'
                   AND at.department = ANY($2)
                   ORDER BY ua.level DESC LIMIT 3""",
                user_id, TASK_DEPARTMENTS.get(request.task_type, [])
            )
            
            if not available:
                available = await db.fetch(
                    """SELECT ua.id FROM user_agents ua
                       WHERE ua.user_id = $1 AND ua.status = 'idle'
                       ORDER BY ua.level DESC LIMIT 1""",
                    user_id
                )
            
            if not available:
                raise HTTPException(status_code=400, detail="没有可用的智能体")
            
            agent_ids = [a["id"] for a in available]
        else:
            agent_ids = request.agent_ids or []
        
        if not agent_ids:
            raise HTTPException(status_code=400, detail="请选择智能体")
        
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        await db.execute(
            """INSERT INTO user_tasks 
               (id, user_id, task_type, input, status, created_at, assigned_agents)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            task_id, user_id, request.task_type, request.input, "processing", now, json.dumps(agent_ids)
        )
        
        for aid in agent_ids:
            await db.execute(
                """UPDATE user_agents 
                   SET status = 'busy', current_task_id = $1, current_task_type = 'user_task', work_start_time = $2
                   WHERE id = $3""",
                task_id, now, aid
            )
        
        return {
            "success": True,
            "task_id": task_id,
            "assigned_agents": agent_ids,
            "message": f"任务已启动，分配 {len(agent_ids)} 个智能体"
        }


@router.get("/task-assignment-options")
async def get_task_assignment_options(
    task_type: str,
    current_user: dict = Depends(get_current_user)
):
    """获取任务分配选项"""
    user_id = current_user["id"]
    
    async with get_db() as db:
        agents = await db.fetch(
            """SELECT ua.id, ua.level, ua.rarity, ua.efficiency, ua.status,
                      at.name, at.department, at.skills
               FROM user_agents ua
               JOIN agent_templates at ON ua.template_id = at.id
               WHERE ua.user_id = $1
               ORDER BY ua.level DESC""",
            user_id
        )
        
        options = []
        preferred_depts = TASK_DEPARTMENTS.get(task_type, [])
        
        for agent in agents:
            score = 0.0
            
            if agent["department"] in preferred_depts:
                score += 30
            
            score += (agent["level"] or 1) * 5
            
            rarity_scores = {"N": 0, "R": 10, "SR": 20, "SSR": 30, "UR": 40}
            score += rarity_scores.get(agent["rarity"], 0)
            
            score += float(agent["efficiency"] or 1.0) * 10
            
            options.append({
                "id": agent["id"],
                "name": agent["name"],
                "department": agent["department"],
                "level": agent["level"],
                "rarity": agent["rarity"],
                "efficiency": float(agent["efficiency"]) if agent["efficiency"] else 1.0,
                "skills": json.loads(agent["skills"]) if isinstance(agent["skills"], str) else agent["skills"],
                "recommendation_score": score,
                "is_available": agent["status"] == "idle",
            })
        
        options.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return {"success": True, "task_type": task_type, "options": options}


@router.get("/task-types")
async def get_task_types():
    """获取任务类型信息"""
    return {
        "success": True,
        "task_types": [
            {"type": "analysis", "name": "任务分析", "departments": ["工部"]},
            {"type": "consult", "name": "智能咨询", "departments": ["礼部", "吏部"]},
            {"type": "auto_work", "name": "自主工作", "departments": ["兵部", "刑部", "工部", "礼部", "吏部"]},
        ]
    }


@router.get("/logs")
async def get_recent_logs(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """获取最近工作日志"""
    user_id = current_user["id"]
    
    async with get_db() as db:
        logs = await db.fetch(
            """SELECT awl.*, at.name as agent_name
               FROM agent_work_logs awl
               JOIN user_agents ua ON awl.agent_id = ua.id
               JOIN agent_templates at ON ua.template_id = at.id
               WHERE awl.user_id = $1
               ORDER BY awl.created_at DESC
               LIMIT $2""",
            user_id, limit
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
        
        return {"success": True, "logs": result}
