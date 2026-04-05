"""
签到任务处理器 - 异步处理签到操作
"""
import asyncio
import logging
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

from backend.database import get_db_connection

logger = logging.getLogger(__name__)

SIGNIN_REWARDS = {
    1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 20
}


async def calculate_signin_reward(consecutive_days: int) -> int:
    """计算签到奖励积分"""
    if consecutive_days >= 7:
        cycle_day = ((consecutive_days - 1) % 7) + 1
    else:
        cycle_day = consecutive_days
    return SIGNIN_REWARDS.get(cycle_day, 15)


async def get_consecutive_days(conn, user_id: str) -> int:
    """计算连续签到天数"""
    today = date.today()
    consecutive = 0
    
    for i in range(365):
        check_date = today - timedelta(days=i)
        cursor = await conn.execute(
            "SELECT id FROM signin_records WHERE user_id = ? AND sign_date = ? AND is_repent = 0",
            (user_id, check_date.isoformat())
        )
        row = await cursor.fetchone()
        if row:
            consecutive += 1
        else:
            break
    
    return consecutive


async def process_signin_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """处理签到任务"""
    user_id = data.get("user_id")
    today = date.today()
    
    max_retries = 5
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        conn = None
        try:
            conn = await get_db_connection()
            
            await conn.execute("BEGIN IMMEDIATE")
            
            cursor = await conn.execute(
                "SELECT id FROM signin_records WHERE user_id = ? AND sign_date = ?",
                (user_id, today.isoformat())
            )
            if await cursor.fetchone():
                await conn.rollback()
                await conn.close()
                return {
                    "success": False,
                    "reward_integral": 0,
                    "consecutive_days": 0,
                    "message": "今日已签到"
                }
            
            consecutive_days = await get_consecutive_days(conn, user_id)
            
            yesterday = today - timedelta(days=1)
            cursor = await conn.execute(
                "SELECT id FROM signin_records WHERE user_id = ? AND sign_date = ?",
                (user_id, yesterday.isoformat())
            )
            if await cursor.fetchone():
                new_consecutive = consecutive_days + 1
            else:
                new_consecutive = 1
            
            reward = await calculate_signin_reward(new_consecutive)
            
            record_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO signin_records (id, user_id, sign_date, reward_integral, consecutive_days, is_repent) VALUES (?, ?, ?, ?, ?, 0)",
                (record_id, user_id, today.isoformat(), reward, new_consecutive)
            )
            
            await conn.execute(
                "UPDATE users SET integral = integral + ? WHERE id = ?",
                (reward, user_id)
            )
            
            log_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO integral_logs (id, user_id, change, balance_after, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (log_id, user_id, reward, reward, "每日签到奖励", datetime.utcnow().isoformat())
            )
            
            cursor = await conn.execute(
                "SELECT user_id FROM user_behavior_points WHERE user_id = ?",
                (user_id,)
            )
            if not await cursor.fetchone():
                await conn.execute(
                    "INSERT INTO user_behavior_points (user_id, total_points, level) VALUES (?, ?, 1)",
                    (user_id, reward)
                )
            else:
                await conn.execute(
                    "UPDATE user_behavior_points SET total_points = total_points + ?, level = (total_points + ?) / 1000 + 1, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (reward, reward, user_id)
                )
            
            await conn.commit()
            await conn.close()
            
            logger.info(f"用户 {user_id} 签到成功，获得 {reward} 积分")
            
            return {
                "success": True,
                "reward_integral": reward,
                "consecutive_days": new_consecutive,
                "message": f"签到成功！获得{reward}积分"
            }
            
        except Exception as e:
            if conn:
                try:
                    await conn.rollback()
                except:
                    pass
                try:
                    await conn.close()
                except:
                    pass
            
            error_msg = str(e)
            if "database is locked" in error_msg.lower() or "locked" in error_msg.lower():
                if attempt < max_retries - 1:
                    logger.warning(f"签到任务数据库锁定，重试 {attempt + 1}/{max_retries}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"签到任务失败（数据库锁定）: {e}")
                    return {
                        "success": False,
                        "reward_integral": 0,
                        "consecutive_days": 0,
                        "message": "系统繁忙，请稍后重试"
                    }
            else:
                logger.error(f"签到任务失败: {e}")
                return {
                    "success": False,
                    "reward_integral": 0,
                    "consecutive_days": 0,
                    "message": f"签到失败: {str(e)}"
                }
    
    return {
        "success": False,
        "reward_integral": 0,
        "consecutive_days": 0,
        "message": "签到失败"
    }


async def init_signin_queue():
    """初始化签到任务队列"""
    from backend.services.task_queue import task_queue
    task_queue.register_handler("signin", process_signin_task)
    logger.info("签到任务处理器已注册")
