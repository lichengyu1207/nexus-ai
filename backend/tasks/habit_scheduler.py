"""
用户习惯培养系统定时任务
包含每日任务重置、每周任务重置等功能
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def reset_daily_tasks():
    """重置每日任务"""
    from backend.routers.habit import reset_daily_tasks as do_reset
    try:
        await do_reset()
        logger.info("每日任务重置完成")
    except Exception as e:
        logger.error(f"每日任务重置失败: {e}")


async def reset_weekly_tasks():
    """重置每周任务"""
    from backend.routers.habit import reset_weekly_tasks as do_reset
    try:
        await do_reset()
        logger.info("每周任务重置完成")
    except Exception as e:
        logger.error(f"每周任务重置失败: {e}")


async def init_default_tasks():
    """初始化默认任务数据"""
    from backend.routers.habit import init_default_tasks as do_init
    try:
        await do_init()
        logger.info("默认任务数据初始化完成")
    except Exception as e:
        logger.error(f"默认任务数据初始化失败: {e}")


async def send_signin_reminders():
    """发送签到提醒"""
    from backend.database import get_db_connection
    from backend.services.notification_service import NotificationService
    try:
        today = datetime.now().date().isoformat()
        
        conn = await get_db_connection()
        notification_service = NotificationService()
        try:
            cursor = await conn.execute(
                """
                SELECT u.id, u.username, u.email
                FROM users u
                WHERE u.is_active = 1
                AND NOT EXISTS (
                    SELECT 1 FROM signin_records sr
                    WHERE sr.user_id = u.id AND sr.sign_date = ?
                )
                """,
                (today,)
            )
            users = await cursor.fetchall()
            
            for user in users:
                try:
                    user_id = user["id"] if hasattr(user, "__getitem__") else user[0]
                    await notification_service.send_notification(
                        user_id=user_id,
                        type="reminder",
                        title="签到提醒",
                        content="您今日尚未签到，快来签到获取积分吧！"
                    )
                except Exception as e:
                    user_id = user["id"] if hasattr(user, "__getitem__") else user[0] if user else "unknown"
                    logger.error(f"发送签到提醒失败 (user={user_id}): {e}", exc_info=True)
            
            logger.info(f"签到提醒发送完成，共发送 {len(users)} 条")
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"发送签到提醒失败: {e}", exc_info=True)


def setup_habit_scheduler():
    """设置习惯培养系统定时任务"""
    scheduler.add_job(
        reset_daily_tasks,
        CronTrigger(hour=0, minute=0),
        id="reset_daily_tasks",
        name="重置每日任务",
        replace_existing=True
    )
    
    scheduler.add_job(
        reset_weekly_tasks,
        CronTrigger(day_of_week="mon", hour=0, minute=0),
        id="reset_weekly_tasks",
        name="重置每周任务",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_signin_reminders,
        CronTrigger(hour=20, minute=0),
        id="send_signin_reminders",
        name="发送签到提醒",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("习惯培养系统定时任务已启动")


async def shutdown_habit_scheduler():
    """关闭习惯培养系统定时任务"""
    scheduler.shutdown(wait=False)
    logger.info("习惯培养系统定时任务已关闭")
