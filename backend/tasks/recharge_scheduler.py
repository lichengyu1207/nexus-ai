"""
充值系统自动化任务脚本
包含订单清理、数据归档、报表预计算等定时任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database import get_db_connection
from backend.services.risk_engine import init_default_rules

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def cleanup_expired_orders():
    """清理过期未处理订单（超过30天仍为pending）"""
    logger.info("开始清理过期订单...")
    
    conn = await get_db_connection()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        cursor = await conn.execute(
            "SELECT id, order_no, user_id FROM recharge_orders WHERE status = 'pending' AND submitted_at < ?",
            (cutoff_date.isoformat(),)
        )
        expired_orders = await cursor.fetchall()
        
        for order in expired_orders:
            await conn.execute(
                "UPDATE recharge_orders SET status = 'expired', admin_notes = '系统自动标记：超过30天未处理', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (order["id"],)
            )
            
            logger.info(f"订单 {order['order_no']} 已标记为过期")
        
        await conn.commit()
        logger.info(f"过期订单清理完成，共处理 {len(expired_orders)} 个订单")
        
    except Exception as e:
        logger.error(f"清理过期订单失败: {e}")
        await conn.rollback()
    finally:
        await conn.close()


async def archive_old_orders():
    """归档旧订单数据（超过1年的已处理订单）"""
    logger.info("开始归档旧订单...")
    
    conn = await get_db_connection()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM recharge_orders WHERE status IN ('approved', 'rejected', 'expired') AND submitted_at < ?",
            (cutoff_date.isoformat(),)
        )
        result = await cursor.fetchone()
        count = result["count"] if result else 0
        
        if count > 0:
            logger.info(f"发现 {count} 条可归档订单")
        
        logger.info(f"订单归档检查完成，可归档订单: {count}")
        
    except Exception as e:
        logger.error(f"归档旧订单失败: {e}")
    finally:
        await conn.close()


async def calculate_daily_stats():
    """计算每日统计数据"""
    logger.info("开始计算每日统计...")
    
    conn = await get_db_connection()
    try:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        
        cursor = await conn.execute(
            """
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(amount), 0) as total_amount,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END) as approved_amount,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
                AVG(CASE WHEN status = 'approved' AND processed_at IS NOT NULL 
                    THEN JULIANDAY(processed_at) - JULIANDAY(submitted_at) END) as avg_process_time
            FROM recharge_orders
            WHERE DATE(submitted_at) = ?
            """,
            (yesterday.isoformat(),)
        )
        stats = await cursor.fetchone()
        
        if stats:
            logger.info(f"昨日统计: 总订单{stats['total_count']}笔, 金额¥{stats['total_amount']:.2f}, 通过{stats['approved_count']}笔")
        
        logger.info("每日统计计算完成")
        
    except Exception as e:
        logger.error(f"计算每日统计失败: {e}")
    finally:
        await conn.close()


async def send_pending_reminders():
    """发送待处理订单提醒"""
    logger.info("检查待处理订单...")
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM recharge_orders WHERE status = 'pending'"
        )
        result = await cursor.fetchone()
        pending_count = result["count"] if result else 0
        
        if pending_count > 10:
            logger.warning(f"当前有 {pending_count} 个待处理订单，请及时处理")
        
        logger.info(f"待处理订单检查完成，当前待处理: {pending_count}")
        
    except Exception as e:
        logger.error(f"检查待处理订单失败: {e}")
    finally:
        await conn.close()


async def init_risk_rules():
    """初始化风控规则"""
    try:
        await init_default_rules()
        logger.info("风控规则初始化完成")
    except Exception as e:
        logger.error(f"初始化风控规则失败: {e}")


def setup_recharge_scheduler():
    """设置充值系统定时任务"""
    scheduler.add_job(
        cleanup_expired_orders,
        CronTrigger(hour=2, minute=0),
        id="cleanup_expired_orders",
        name="清理过期订单",
        replace_existing=True
    )
    
    scheduler.add_job(
        archive_old_orders,
        CronTrigger(hour=3, minute=0),
        id="archive_old_orders",
        name="归档旧订单",
        replace_existing=True
    )
    
    scheduler.add_job(
        calculate_daily_stats,
        CronTrigger(hour=1, minute=0),
        id="calculate_daily_stats",
        name="计算每日统计",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_pending_reminders,
        CronTrigger(hour=9, minute=0),
        id="send_pending_reminders",
        name="待处理订单提醒",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_pending_reminders,
        CronTrigger(hour=18, minute=0),
        id="send_pending_reminders_evening",
        name="待处理订单提醒(晚间)",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("充值系统定时任务已启动")


async def shutdown_recharge_scheduler():
    """关闭充值系统定时任务"""
    scheduler.shutdown(wait=False)
    logger.info("充值系统定时任务已关闭")
