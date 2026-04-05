"""
核心功能使用习惯提醒定时任务
包含目标提醒、连续提醒、唤醒提醒
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database import get_db_connection
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def get_pending_goal_reminders() -> list:
    """获取待发送目标提醒的用户"""
    conn = await get_db_connection()
    try:
        today = date.today()
        
        cursor = await conn.execute('''
            SELECT DISTINCT u.id, u.username, u.email, up.reminder_time
            FROM users u
            JOIN user_preferences up ON u.id = up.user_id
            LEFT JOIN user_function_goals ufg ON u.id = ufg.user_id AND ufg.goal_date = ? AND ufg.period = 'daily'
            WHERE up.reminder_enabled = 1
            AND u.is_active = 1
            AND (ufg.progress < ufg.target_count OR ufg.id IS NULL)
            AND NOT EXISTS (
                SELECT 1 FROM notifications n 
                WHERE n.user_id = u.id 
                AND n.type = 'habit_reminder' 
                AND DATE(n.created_at) = ?
            )
        ''', (today.isoformat(), today.isoformat()))
        
        users = await cursor.fetchall()
        return [dict(row) for row in users]
    finally:
        await conn.close()


async def get_pending_consecutive_reminders() -> list:
    """获取待发送连续提醒的用户（连续6天，提醒第7天）"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT DISTINCT u.id, u.username, u.email, cfu.function_type, cfu.consecutive_days
            FROM users u
            JOIN core_function_usage cfu ON u.id = cfu.user_id
            WHERE cfu.consecutive_days = 6
            AND cfu.usage_date = DATE('now')
            AND NOT EXISTS (
                SELECT 1 FROM notifications n 
                WHERE n.user_id = u.id 
                AND n.type = 'consecutive_reminder' 
                AND DATE(n.created_at) = DATE('now')
            )
        ''')
        
        users = await cursor.fetchall()
        return [dict(row) for row in users]
    finally:
        await conn.close()


async def get_pending_wakeup_reminders() -> list:
    """获取待发送唤醒提醒的用户（超过3天未使用）"""
    conn = await get_db_connection()
    try:
        three_days_ago = date.today() - timedelta(days=3)
        
        cursor = await conn.execute('''
            SELECT DISTINCT u.id, u.username, u.email
            FROM users u
            WHERE u.is_active = 1
            AND NOT EXISTS (
                SELECT 1 FROM core_function_usage cfu 
                WHERE cfu.user_id = u.id 
                AND cfu.usage_date >= ?
                AND cfu.count > 0
            )
            AND NOT EXISTS (
                SELECT 1 FROM notifications n 
                WHERE n.user_id = u.id 
                AND n.type = 'wakeup_reminder' 
                AND DATE(n.created_at) >= ?
            )
        ''', (three_days_ago.isoformat(), three_days_ago.isoformat()))
        
        users = await cursor.fetchall()
        return [dict(row) for row in users]
    finally:
        await conn.close()


async def send_goal_reminders():
    """发送目标提醒"""
    logger.info("开始发送目标提醒...")
    
    users = await get_pending_goal_reminders()
    notification_service = NotificationService()
    
    for user in users:
        try:
            await notification_service.send_notification(
                user_id=user["id"],
                type="habit_reminder",
                title="今日目标提醒",
                content="您今日的习惯目标尚未完成，快来完成任务获取积分奖励吧！"
            )
            logger.info(f"已发送目标提醒给用户 {user['id']}")
        except Exception as e:
            logger.error(f"发送目标提醒失败 (user={user['id']}): {e}")
    
    logger.info(f"目标提醒发送完成，共发送 {len(users)} 条")


async def send_consecutive_reminders():
    """发送连续提醒"""
    logger.info("开始发送连续提醒...")
    
    users = await get_pending_consecutive_reminders()
    notification_service = NotificationService()
    
    for user in users:
        try:
            func_name = "任务分析" if user["function_type"] == "task_analysis" else "智能咨询"
            await notification_service.send_notification(
                user_id=user["id"],
                type="consecutive_reminder",
                title="连续使用提醒",
                content=f"您已连续使用{func_name}6天，明天继续即可获得额外奖励！"
            )
            logger.info(f"已发送连续提醒给用户 {user['id']}")
        except Exception as e:
            logger.error(f"发送连续提醒失败 (user={user['id']}): {e}")
    
    logger.info(f"连续提醒发送完成，共发送 {len(users)} 条")


async def send_wakeup_reminders():
    """发送唤醒提醒"""
    logger.info("开始发送唤醒提醒...")
    
    users = await get_pending_wakeup_reminders()
    notification_service = NotificationService()
    
    for user in users:
        try:
            await notification_service.send_notification(
                user_id=user["id"],
                type="wakeup_reminder",
                title="好久不见",
                content="您已经好几天没有使用房都督AI了，有新的房产数据更新，快来看看吧！"
            )
            logger.info(f"已发送唤醒提醒给用户 {user['id']}")
        except Exception as e:
            logger.error(f"发送唤醒提醒失败 (user={user['id']}): {e}")
    
    logger.info(f"唤醒提醒发送完成，共发送 {len(users)} 条")


async def reset_daily_goals():
    """重置每日目标"""
    from backend.routers.core_habits import reset_daily_goals as do_reset
    await do_reset()


def setup_core_habits_scheduler():
    """设置核心功能习惯提醒定时任务"""
    scheduler.add_job(
        send_goal_reminders,
        CronTrigger(hour=20, minute=0),
        id="goal_reminders",
        name="目标提醒",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_consecutive_reminders,
        CronTrigger(hour=9, minute=0),
        id="consecutive_reminders",
        name="连续提醒",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_wakeup_reminders,
        CronTrigger(hour=10, minute=0),
        id="wakeup_reminders",
        name="唤醒提醒",
        replace_existing=True
    )
    
    scheduler.add_job(
        reset_daily_goals,
        CronTrigger(hour=0, minute=0),
        id="reset_daily_goals",
        name="重置每日目标",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("核心功能习惯提醒定时任务已启动")


async def shutdown_core_habits_scheduler():
    """关闭核心功能习惯提醒定时任务"""
    scheduler.shutdown(wait=False)
    logger.info("核心功能习惯提醒定时任务已关闭")
