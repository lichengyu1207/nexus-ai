"""
分析任务调度器 - 修复版
解决任务卡住问题
"""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database_pg import get_db
import json

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def process_queued_analysis_tasks():
    """
    处理队列中的分析任务
    
    每30秒执行一次，从 analysis_tasks 表中获取 queued 状态的任务并处理
    """
    task_id = None
    query = None
    style = None
    user_id = None
    
    try:
        async with get_db() as db:
            # 获取一个 queued 状态的任务
            task = await db.fetchrow(
                """
                SELECT id, query, style, input_data, created_at 
                FROM analysis_tasks 
                WHERE status = 'queued' 
                ORDER BY created_at ASC 
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """
            )
            
            if not task:
                return
            
            task_id = task['id']
            query = task['query']
            style = task['style'] if 'style' in task else 'balanced'
            input_data = task['input_data'] if 'input_data' in task else {}
            
            # 从 input_data 中获取 user_id
            user_id = input_data.get('user_id', 'unknown') if isinstance(input_data, dict) else 'unknown'
            
            logger.info(f"Processing analysis task: {task_id}")
            
            # 更新状态为 running
            await db.execute(
                "UPDATE analysis_tasks SET status = 'running', updated_at = NOW() WHERE id = $1",
                task_id
            )
            
    except Exception as e:
        logger.error(f"Failed to get queued task: {e}")
        return
    
    # 在事务外处理任务
    if task_id:
        try:
            # 导入并调用任务处理函数
            from backend.routers.tasks import process_analysis_task
            
            result = await process_analysis_task({
                "task_id": task_id,
                "user_id": user_id,
                "query": query,
                "style": style
            })
            
            # 更新任务结果
            async with get_db() as db:
                await db.execute(
                    "UPDATE analysis_tasks SET status = 'completed', progress = 100, result = $1, updated_at = NOW() WHERE id = $2",
                    json.dumps(result), task_id
                )
            
            logger.info(f"Analysis task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Analysis task {task_id} failed: {e}")
            
            # 更新状态为 failed
            try:
                async with get_db() as db:
                    await db.execute(
                        "UPDATE analysis_tasks SET status = 'failed', result = $1, updated_at = NOW() WHERE id = $2",
                        json.dumps({"error": str(e)}), task_id
                    )
            except Exception as db_error:
                logger.error(f"Failed to update task status: {db_error}")


async def retry_failed_analysis_tasks():
    """
    重试失败的分析任务
    
    每5分钟执行一次，重试失败次数少于3次的任务
    """
    try:
        async with get_db() as db:
            # 获取失败次数少于3次的任务
            tasks = await db.fetch(
                """
                SELECT id, query, style 
                FROM analysis_tasks 
                WHERE status = 'failed' 
                AND (retry_count IS NULL OR retry_count < 3)
                ORDER BY created_at ASC 
                LIMIT 5
                """
            )
            
            for task in tasks:
                # 重置状态为 queued
                await db.execute(
                    """
                    UPDATE analysis_tasks 
                    SET status = 'queued', 
                        retry_count = COALESCE(retry_count, 0) + 1,
                        updated_at = NOW() 
                    WHERE id = $1
                    """,
                    task['id']
                )
                logger.info(f"Retrying analysis task: {task['id']}")
                
    except Exception as e:
        logger.error(f"Failed to retry analysis tasks: {e}")


def setup_analysis_task_scheduler():
    """
    设置分析任务调度器
    """
    # 每30秒处理队列中的任务
    scheduler.add_job(
        process_queued_analysis_tasks,
        trigger=IntervalTrigger(seconds=30),
        id="process_analysis_tasks",
        name="处理分析任务队列",
        replace_existing=True
    )
    
    # 每5分钟重试失败的任务
    scheduler.add_job(
        retry_failed_analysis_tasks,
        trigger=IntervalTrigger(minutes=5),
        id="retry_failed_analysis_tasks",
        name="重试失败的分析任务",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Analysis task scheduler started")
