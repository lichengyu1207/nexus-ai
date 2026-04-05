"""
新用户引导API
引导新用户完成首次体验
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import logging

from ..auth import get_current_user
from ..database import get_db_connection

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_onboarding_status(user: dict = Depends(get_current_user)):
    """获取用户引导状态"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT * FROM user_onboarding WHERE user_id = ?
        """, (user["id"],))
        status = await cursor.fetchone()
        
        if not status:
            return {
                "completed": False,
                "steps": {
                    "welcome": False,
                    "profile": False,
                    "first_analysis": False,
                    "tutorial": False
                },
                "progress": 0
            }
        
        steps = {
            "welcome": bool(status["welcome_completed"]),
            "profile": bool(status["profile_completed"]),
            "first_analysis": bool(status["first_analysis_completed"]),
            "tutorial": bool(status["tutorial_completed"])
        }
        
        completed_count = sum(1 for v in steps.values() if v)
        
        return {
            "completed": completed_count == 4,
            "steps": steps,
            "progress": completed_count * 25
        }
    finally:
        await conn.close()


@router.post("/complete-step")
async def complete_step(
    data: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """完成引导步骤"""
    conn = await get_db_connection()
    try:
        step = data.get("step")
        
        if step not in ["welcome", "profile", "first_analysis", "tutorial"]:
            return {"error": "无效的步骤"}
        
        cursor = await conn.execute("""
            SELECT * FROM user_onboarding WHERE user_id = ?
        """, (user["id"],))
        existing = await cursor.fetchone()
        
        if not existing:
            await conn.execute("""
                INSERT INTO user_onboarding (user_id, welcome_completed, profile_completed, first_analysis_completed, tutorial_completed)
                VALUES (?, 0, 0, 0, 0)
            """, (user["id"],))
        
        column_map = {
            "welcome": "welcome_completed",
            "profile": "profile_completed",
            "first_analysis": "first_analysis_completed",
            "tutorial": "tutorial_completed"
        }
        
        await conn.execute(f"""
            UPDATE user_onboarding SET {column_map[step]} = 1, updated_at = ?
            WHERE user_id = ?
        """, (datetime.utcnow().isoformat(), user["id"]))
        await conn.commit()
        
        logger.info(f"用户 {user['id']} 完成引导步骤: {step}")
        
        return {"success": True, "step": step}
    finally:
        await conn.close()


@router.post("/skip")
async def skip_onboarding(user: dict = Depends(get_current_user)):
    """跳过引导"""
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT OR REPLACE INTO user_onboarding (user_id, welcome_completed, profile_completed, first_analysis_completed, tutorial_completed)
            VALUES (?, 1, 1, 1, 1)
        """, (user["id"],))
        await conn.commit()
        
        return {"success": True, "message": "引导已跳过"}
    finally:
        await conn.close()


@router.get("/tips")
async def get_tips(user: dict = Depends(get_current_user)):
    """获取新用户提示"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT COUNT(*) as count FROM analysis_tasks WHERE user_id = ?
        """, (user["id"],))
        task_count = (await cursor.fetchone())["count"]
        
        tips = []
        
        if task_count == 0:
            tips.append({
                "id": "first_analysis",
                "title": "开始您的第一次分析",
                "description": "输入地址，获取专业的房产分析报告",
                "action": "/analyze",
                "priority": 1
            })
        
        cursor = await conn.execute("""
            SELECT integral FROM users WHERE id = ?
        """, (user["id"],))
        integral = (await cursor.fetchone())["integral"]
        
        if integral < 10:
            tips.append({
                "id": "low_integral",
                "title": "积分不足",
                "description": "邀请好友或完成任务获取更多积分",
                "action": "/integral",
                "priority": 2
            })
        
        return {"tips": tips}
    finally:
        await conn.close()
