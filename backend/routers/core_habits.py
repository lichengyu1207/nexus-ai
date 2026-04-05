"""
核心功能使用习惯培养API路由
包含任务分析、智能咨询的使用上报、统计、目标设置等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import logging
import asyncio

from backend.database import get_db_connection
from backend.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/habit", tags=["core_habits"])

FUNCTION_TYPES = ["task_analysis", "intelligent_consult"]
DEFAULT_DAILY_GOALS = {
    "task_analysis": 5,
    "intelligent_consult": 3
}
GOAL_REWARDS = {
    "task_analysis": 10,
    "intelligent_consult": 8
}
CONSECUTIVE_REWARDS = {
    7: 50,
    14: 100,
    30: 200
}


class UsageReportRequest(BaseModel):
    user_id: Optional[str] = None
    timestamp: Optional[str] = None


class GoalSettingRequest(BaseModel):
    task_analysis_daily_target: Optional[int] = None
    intelligent_consult_daily_target: Optional[int] = None


class UserPreferences(BaseModel):
    reminder_enabled: bool = True
    reminder_time: str = "20:00"


class FunctionStats(BaseModel):
    today_count: int
    consecutive_days: int
    total_count: int
    total_days: int
    daily_goal: int
    daily_progress: int
    weekly_count: int
    weekly_goal: int
    weekly_progress: int


class HabitStatsResponse(BaseModel):
    task_analysis: FunctionStats
    intelligent_consult: FunctionStats


async def get_or_create_usage_record(conn, user_id: str, function_type: str, usage_date: date) -> dict:
    """获取或创建使用记录"""
    cursor = await conn.execute(
        "SELECT * FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date = ?",
        (user_id, function_type, usage_date.isoformat())
    )
    row = await cursor.fetchone()
    
    if row:
        return dict(row)
    
    record_id = str(uuid.uuid4())
    await conn.execute(
        "INSERT INTO core_function_usage (id, user_id, function_type, usage_date, count, consecutive_days, total_days, total_count) VALUES (?, ?, ?, ?, 0, 0, 0, 0)",
        (record_id, user_id, function_type, usage_date.isoformat())
    )
    await conn.commit()
    
    cursor = await conn.execute(
        "SELECT * FROM core_function_usage WHERE id = ?",
        (record_id,)
    )
    return dict(await cursor.fetchone())


async def calculate_consecutive_days(conn, user_id: str, function_type: str) -> int:
    """计算连续使用天数"""
    today = date.today()
    consecutive = 0
    
    for i in range(365):
        check_date = today - timedelta(days=i)
        cursor = await conn.execute(
            "SELECT count FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date = ? AND count > 0",
            (user_id, function_type, check_date.isoformat())
        )
        row = await cursor.fetchone()
        if row and row["count"] > 0:
            consecutive += 1
        else:
            break
    
    return consecutive


async def get_or_create_goal(conn, user_id: str, function_type: str, period: str, goal_date: date) -> dict:
    """获取或创建目标记录"""
    cursor = await conn.execute(
        "SELECT * FROM user_function_goals WHERE user_id = ? AND function_type = ? AND period = ? AND goal_date = ?",
        (user_id, function_type, period, goal_date.isoformat())
    )
    row = await cursor.fetchone()
    
    if row:
        return dict(row)
    
    goal_id = str(uuid.uuid4())
    default_target = DEFAULT_DAILY_GOALS.get(function_type, 5)
    
    await conn.execute(
        "INSERT INTO user_function_goals (id, user_id, function_type, period, target_count, progress, achieved, goal_date) VALUES (?, ?, ?, ?, ?, 0, 0, ?)",
        (goal_id, user_id, function_type, period, default_target, goal_date.isoformat())
    )
    await conn.commit()
    
    cursor = await conn.execute(
        "SELECT * FROM user_function_goals WHERE id = ?",
        (goal_id,)
    )
    return dict(await cursor.fetchone())


async def award_goal_completion(user_id: str, function_type: str, reward_type: str):
    """发放目标完成奖励"""
    conn = None
    try:
        conn = await get_db_connection()
        await conn.execute("BEGIN IMMEDIATE")
        
        reward_amount = GOAL_REWARDS.get(function_type, 10)
        
        await conn.execute(
            "UPDATE users SET integral = integral + ? WHERE id = ?",
            (reward_amount, user_id)
        )
        
        log_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO integral_logs (id, user_id, change, balance_after, reason, created_at) VALUES (?, ?, ?, (SELECT integral FROM users WHERE id = ?), ?, ?)",
            (log_id, user_id, reward_amount, user_id, f"完成{function_type}每日目标奖励", datetime.utcnow().isoformat())
        )
        
        cursor = await conn.execute(
            "SELECT user_id FROM user_behavior_points WHERE user_id = ?",
            (user_id,)
        )
        if not await cursor.fetchone():
            await conn.execute(
                "INSERT INTO user_behavior_points (user_id, total_points, level) VALUES (?, ?, 1)",
                (user_id, reward_amount)
            )
        else:
            await conn.execute(
                "UPDATE user_behavior_points SET total_points = total_points + ?, level = (total_points + ?) / 1000 + 1, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (reward_amount, reward_amount, user_id)
            )
        
        await conn.commit()
        logger.info(f"用户 {user_id} 完成 {function_type} {reward_type}，获得 {reward_amount} 积分")
        
    except Exception as e:
        if conn:
            await conn.rollback()
        logger.error(f"发放奖励失败: {e}")
    finally:
        if conn:
            await conn.close()


async def process_usage_report(user_id: str, function_type: str) -> dict:
    """处理使用上报"""
    if function_type not in FUNCTION_TYPES:
        return {"success": False, "error": "无效的功能类型"}
    
    conn = None
    try:
        conn = await get_db_connection()
        await conn.execute("BEGIN IMMEDIATE")
        
        today = date.today()
        
        usage = await get_or_create_usage_record(conn, user_id, function_type, today)
        
        new_count = usage["count"] + 1
        new_total_count = (usage["total_count"] or 0) + 1
        
        if usage["count"] == 0:
            yesterday = today - timedelta(days=1)
            cursor = await conn.execute(
                "SELECT count FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date = ? AND count > 0",
                (user_id, function_type, yesterday.isoformat())
            )
            yesterday_row = await cursor.fetchone()
            
            if yesterday_row:
                cursor = await conn.execute(
                    "SELECT consecutive_days, total_days FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date = ?",
                    (user_id, function_type, yesterday.isoformat())
                )
                yesterday_data = await cursor.fetchone()
                new_consecutive = (yesterday_data["consecutive_days"] or 0) + 1 if yesterday_data else 1
                new_total_days = (yesterday_data["total_days"] or 0) + 1 if yesterday_data else 1
            else:
                new_consecutive = 1
                cursor = await conn.execute(
                    "SELECT MAX(total_days) as max_days FROM core_function_usage WHERE user_id = ? AND function_type = ?",
                    (user_id, function_type)
                )
                max_days_row = await cursor.fetchone()
                new_total_days = (max_days_row["max_days"] or 0) + 1
        else:
            new_consecutive = usage["consecutive_days"]
            new_total_days = usage["total_days"]
        
        await conn.execute(
            "UPDATE core_function_usage SET count = ?, last_used_at = ?, consecutive_days = ?, total_days = ?, total_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_count, datetime.utcnow().isoformat(), new_consecutive, new_total_days, new_total_count, usage["id"])
        )
        
        goal = await get_or_create_goal(conn, user_id, function_type, "daily", today)
        new_progress = goal["progress"] + 1
        
        goal_achieved = False
        if new_progress >= goal["target_count"] and goal["achieved"] == 0:
            goal_achieved = True
            await conn.execute(
                "UPDATE user_function_goals SET progress = ?, achieved = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_progress, goal["id"])
            )
        else:
            await conn.execute(
                "UPDATE user_function_goals SET progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_progress, goal["id"])
            )
        
        await conn.commit()
        
        if goal_achieved:
            asyncio.create_task(award_goal_completion(user_id, function_type, "每日目标"))
        
        return {
            "success": True,
            "count": new_count,
            "consecutive_days": new_consecutive,
            "total_count": new_total_count,
            "goal_progress": new_progress,
            "goal_target": goal["target_count"],
            "goal_achieved": goal_achieved
        }
        
    except Exception as e:
        logger.error(f"处理使用上报失败: {e}")
        if conn:
            await conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            await conn.close()


@router.post("/usage/task-analysis")
async def report_task_analysis_usage(
    request: UsageReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """上报任务分析使用"""
    user_id = request.user_id or current_user["id"]
    result = await process_usage_report(user_id, "task_analysis")
    
    if result["success"]:
        return {"status": "success", "data": result}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "上报失败"))


@router.post("/usage/intelligent-consult")
async def report_consult_usage(
    request: UsageReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """上报智能咨询使用"""
    user_id = request.user_id or current_user["id"]
    result = await process_usage_report(user_id, "intelligent_consult")
    
    if result["success"]:
        return {"status": "success", "data": result}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "上报失败"))


@router.get("/stats", response_model=HabitStatsResponse)
async def get_habit_stats(current_user: dict = Depends(get_current_user)):
    """获取用户习惯统计"""
    user_id = current_user["id"]
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    conn = await get_db_connection()
    try:
        stats = {}
        
        for func_type in FUNCTION_TYPES:
            cursor = await conn.execute(
                "SELECT * FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date = ?",
                (user_id, func_type, today.isoformat())
            )
            today_row = await cursor.fetchone()
            
            today_count = today_row["count"] if today_row else 0
            
            cursor = await conn.execute(
                "SELECT SUM(count) as total FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date >= ?",
                (user_id, func_type, week_start.isoformat())
            )
            week_row = await cursor.fetchone()
            weekly_count = week_row["total"] if week_row and week_row["total"] else 0
            
            cursor = await conn.execute(
                "SELECT SUM(count) as total FROM core_function_usage WHERE user_id = ? AND function_type = ?",
                (user_id, func_type)
            )
            total_row = await cursor.fetchone()
            total_count = total_row["total"] if total_row and total_row["total"] else 0
            
            cursor = await conn.execute(
                "SELECT MAX(total_days) as max_days FROM core_function_usage WHERE user_id = ? AND function_type = ?",
                (user_id, func_type)
            )
            days_row = await cursor.fetchone()
            total_days = days_row["max_days"] if days_row and days_row["max_days"] else 0
            
            consecutive = await calculate_consecutive_days(conn, user_id, func_type)
            
            goal = await get_or_create_goal(conn, user_id, func_type, "daily", today)
            
            cursor = await conn.execute(
                "SELECT * FROM user_function_goals WHERE user_id = ? AND function_type = ? AND period = 'weekly' AND goal_date = ?",
                (user_id, func_type, week_start.isoformat())
            )
            weekly_goal_row = await cursor.fetchone()
            
            if not weekly_goal_row:
                weekly_goal_id = str(uuid.uuid4())
                weekly_target = DEFAULT_DAILY_GOALS.get(func_type, 5) * 7
                await conn.execute(
                    "INSERT INTO user_function_goals (id, user_id, function_type, period, target_count, progress, achieved, goal_date) VALUES (?, ?, ?, 'weekly', ?, ?, 0, ?)",
                    (weekly_goal_id, user_id, func_type, weekly_target, weekly_count, week_start.isoformat())
                )
                await conn.commit()
                weekly_target = weekly_target
            else:
                weekly_target = weekly_goal_row["target_count"]
                await conn.execute(
                    "UPDATE user_function_goals SET progress = ? WHERE id = ?",
                    (weekly_count, weekly_goal_row["id"])
                )
                await conn.commit()
            
            stats[func_type] = FunctionStats(
                today_count=today_count,
                consecutive_days=consecutive,
                total_count=total_count,
                total_days=total_days,
                daily_goal=goal["target_count"],
                daily_progress=goal["progress"],
                weekly_count=weekly_count,
                weekly_goal=weekly_target,
                weekly_progress=weekly_count
            )
        
        return HabitStatsResponse(
            task_analysis=stats["task_analysis"],
            intelligent_consult=stats["intelligent_consult"]
        )
    finally:
        await conn.close()


@router.put("/goals")
async def set_habit_goals(
    request: GoalSettingRequest,
    current_user: dict = Depends(get_current_user)
):
    """设置用户目标"""
    user_id = current_user["id"]
    today = date.today()
    
    conn = await get_db_connection()
    try:
        if request.task_analysis_daily_target is not None:
            if request.task_analysis_daily_target < 1 or request.task_analysis_daily_target > 100:
                raise HTTPException(status_code=400, detail="任务分析目标值应在1-100之间")
            
            goal = await get_or_create_goal(conn, user_id, "task_analysis", "daily", today)
            await conn.execute(
                "UPDATE user_function_goals SET target_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (request.task_analysis_daily_target, goal["id"])
            )
        
        if request.intelligent_consult_daily_target is not None:
            if request.intelligent_consult_daily_target < 1 or request.intelligent_consult_daily_target > 100:
                raise HTTPException(status_code=400, detail="智能咨询目标值应在1-100之间")
            
            goal = await get_or_create_goal(conn, user_id, "intelligent_consult", "daily", today)
            await conn.execute(
                "UPDATE user_function_goals SET target_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (request.intelligent_consult_daily_target, goal["id"])
            )
        
        await conn.commit()
        
        return {"status": "success", "message": "目标设置成功"}
    finally:
        await conn.close()


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """获取用户偏好设置"""
    user_id = current_user["id"]
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return UserPreferences(
                reminder_enabled=bool(row["reminder_enabled"]),
                reminder_time=row["reminder_time"]
            )
        else:
            return UserPreferences()
    finally:
        await conn.close()


@router.put("/preferences")
async def set_user_preferences(
    request: UserPreferences,
    current_user: dict = Depends(get_current_user)
):
    """设置用户偏好"""
    user_id = current_user["id"]
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT user_id FROM user_preferences WHERE user_id = ?",
            (user_id,)
        )
        
        if await cursor.fetchone():
            await conn.execute(
                "UPDATE user_preferences SET reminder_enabled = ?, reminder_time = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (1 if request.reminder_enabled else 0, request.reminder_time, user_id)
            )
        else:
            await conn.execute(
                "INSERT INTO user_preferences (user_id, reminder_enabled, reminder_time) VALUES (?, ?, ?)",
                (user_id, 1 if request.reminder_enabled else 0, request.reminder_time)
            )
        
        await conn.commit()
        
        return {"status": "success", "message": "偏好设置已保存"}
    finally:
        await conn.close()


@router.get("/history/{function_type}")
async def get_usage_history(
    function_type: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """获取使用历史"""
    user_id = current_user["id"]
    
    if function_type not in FUNCTION_TYPES:
        raise HTTPException(status_code=400, detail="无效的功能类型")
    
    conn = await get_db_connection()
    try:
        start_date = date.today() - timedelta(days=days)
        
        cursor = await conn.execute(
            "SELECT usage_date, count, consecutive_days FROM core_function_usage WHERE user_id = ? AND function_type = ? AND usage_date >= ? ORDER BY usage_date",
            (user_id, function_type, start_date.isoformat())
        )
        records = await cursor.fetchall()
        
        history = []
        for row in records:
            history.append({
                "date": row["usage_date"],
                "count": row["count"],
                "consecutive_days": row["consecutive_days"]
            })
        
        return {"function_type": function_type, "history": history, "total_days": len(history)}
    finally:
        await conn.close()


async def reset_daily_goals():
    """重置每日目标（定时任务调用）"""
    conn = await get_db_connection()
    try:
        today = date.today()
        
        for func_type in FUNCTION_TYPES:
            default_target = DEFAULT_DAILY_GOALS.get(func_type, 5)
            
            cursor = await conn.execute(
                "SELECT DISTINCT user_id FROM core_function_usage WHERE function_type = ?",
                (func_type,)
            )
            users = await cursor.fetchall()
            
            for user_row in users:
                user_id = user_row["user_id"]
                await get_or_create_goal(conn, user_id, func_type, "daily", today)
        
        await conn.commit()
        logger.info("每日目标已重置")
    except Exception as e:
        logger.error(f"重置每日目标失败: {e}")
        await conn.rollback()
    finally:
        await conn.close()
