"""
智能体自主工作定时任务调度器
包含任务分配、任务执行、每日限额重置等功能
"""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def assign_tasks_to_idle_agents():
    """
    为空闲智能体分配任务
    
    每分钟执行一次
    """
    from backend.governance.auto_work import auto_task_scheduler
    
    try:
        count = await auto_task_scheduler.scan_and_assign()
        if count > 0:
            logger.info(f"Assigned {count} tasks to idle agents")
    except Exception as e:
        logger.error(f"Failed to assign tasks: {e}")


async def execute_assigned_tasks():
    """
    执行已分配的任务
    
    每30秒执行一次
    """
    from backend.governance.auto_work import task_executor
    
    try:
        count = await task_executor.execute_assigned_tasks()
        if count > 0:
            logger.info(f"Completed {count} auto tasks")
    except asyncio.CancelledError:
        logger.warning("execute_assigned_tasks was cancelled")
        raise
    except Exception as e:
        logger.error(f"Failed to execute tasks: {e}")


async def reset_daily_work_limits():
    """
    重置每日工作限额
    
    每日0点执行
    """
    from backend.database_pg import get_db
    
    try:
        async with get_db() as db:
            result = await db.execute(
                "UPDATE user_agents SET daily_auto_work_seconds = 0"
            )
            logger.info(f"Reset daily work limits for all agents")
    except Exception as e:
        logger.error(f"Failed to reset daily limits: {e}")


async def generate_new_tasks():
    """
    生成新的任务到任务池
    
    每小时执行一次
    """
    import uuid
    from backend.database_pg import get_db
    
    task_templates = [
        {"task_type": "data_collect", "description": "采集公开房产数据", "base_reward": 15, "resource_cost": 2, "priority": 7},
        {"task_type": "data_clean", "description": "清洗原始数据", "base_reward": 5, "resource_cost": 1, "priority": 5},
        {"task_type": "report_generate", "description": "预生成分析报告", "base_reward": 30, "resource_cost": 5, "priority": 6},
        {"task_type": "knowledge_base", "description": "更新知识库", "base_reward": 10, "resource_cost": 2, "priority": 5},
        {"task_type": "market_monitor", "description": "监控市场变化", "base_reward": 20, "resource_cost": 3, "priority": 7},
        {"task_type": "user_profile", "description": "更新用户画像", "base_reward": 20, "resource_cost": 2, "priority": 5},
        {"task_type": "policy_parse", "description": "解析房产政策", "base_reward": 25, "resource_cost": 3, "priority": 7},
        {"task_type": "price_predict", "description": "预测房价走势", "base_reward": 100, "resource_cost": 20, "priority": 9},
        {"task_type": "sentiment_analyze", "description": "分析市场情绪", "base_reward": 15, "resource_cost": 2, "priority": 4},
        {"task_type": "data_validate", "description": "验证数据准确性", "base_reward": 8, "resource_cost": 1, "priority": 3},
    ]
    
    try:
        async with get_db() as db:
            pending_count = await db.fetchval(
                "SELECT COUNT(*) FROM auto_tasks WHERE status = 'pending'"
            )
            
            if pending_count < 50:
                import random
                num_new_tasks = random.randint(5, 15)
                
                for _ in range(num_new_tasks):
                    template = random.choice(task_templates)
                    await db.execute(
                        """INSERT INTO auto_tasks (id, task_type, description, base_reward, resource_cost, priority, status)
                           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        f"{template['task_type']}-{uuid.uuid4().hex[:8]}",
                        template["task_type"],
                        template["description"],
                        template["base_reward"],
                        template["resource_cost"],
                        template["priority"],
                        "pending"
                    )
                
                logger.info(f"Generated {num_new_tasks} new tasks")
    except Exception as e:
        logger.error(f"Failed to generate tasks: {e}")


def setup_auto_work_scheduler():
    """设置自主工作定时任务"""
    scheduler.add_job(
        assign_tasks_to_idle_agents,
        IntervalTrigger(minutes=1),
        id="assign_tasks_to_idle_agents",
        name="为空闲智能体分配任务",
        replace_existing=True
    )
    
    scheduler.add_job(
        execute_assigned_tasks,
        IntervalTrigger(seconds=30),
        id="execute_assigned_tasks",
        name="执行已分配任务",
        replace_existing=True
    )
    
    scheduler.add_job(
        reset_daily_work_limits,
        CronTrigger(hour=0, minute=0),
        id="reset_daily_work_limits",
        name="重置每日工作限额",
        replace_existing=True
    )
    
    scheduler.add_job(
        generate_new_tasks,
        IntervalTrigger(hours=1),
        id="generate_new_tasks",
        name="生成新任务",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
    
    logger.info("Auto work scheduler started")


async def shutdown_auto_work_scheduler():
    """关闭自主工作调度器"""
    if scheduler.running:
        scheduler.shutdown()
    logger.info("Auto work scheduler stopped")
