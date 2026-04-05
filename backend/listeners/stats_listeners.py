"""
事件监听器模块
处理各种事件并更新统计数据
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from ..database import get_db_connection
from ..event_bus import event_bus
from ..events import (
    UserRegisteredEvent,
    IntegralChangedEvent,
    TaskCreatedEvent,
    TaskCompletedEvent,
    UserLocationUpdatedEvent,
    SigninEvent
)

logger = logging.getLogger(__name__)


async def update_source_stats(source: str, increment: int = 1):
    """更新来源统计"""
    if not source:
        source = 'unknown'
    
    conn = await get_db_connection()
    try:
        await conn.execute('''
            INSERT INTO user_source_stats (source, user_count, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(source) DO UPDATE SET
                user_count = user_count + ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (source, increment, increment))
        await conn.commit()
        logger.debug(f"Updated source stats: {source} +{increment}")
    except Exception as e:
        logger.error(f"Failed to update source stats: {e}")
    finally:
        await conn.close()


async def update_city_stats(city: str, increment: int = 1):
    """更新城市统计"""
    if not city:
        return
    
    conn = await get_db_connection()
    try:
        await conn.execute('''
            INSERT INTO user_city_stats (city, user_count, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(city) DO UPDATE SET
                user_count = user_count + ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (city, increment, increment))
        await conn.commit()
        logger.debug(f"Updated city stats: {city} +{increment}")
    except Exception as e:
        logger.error(f"Failed to update city stats: {e}")
    finally:
        await conn.close()


async def update_district_stats(city: str, district: str, increment: int = 1):
    """更新区域统计"""
    if not city or not district:
        return
    
    conn = await get_db_connection()
    try:
        stats_id = f"{city}_{district}"
        await conn.execute('''
            INSERT INTO user_district_stats (id, city, district, user_count, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                user_count = user_count + ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (stats_id, city, district, increment, increment))
        await conn.commit()
        logger.debug(f"Updated district stats: {city}/{district} +{increment}")
    except Exception as e:
        logger.error(f"Failed to update district stats: {e}")
    finally:
        await conn.close()


async def update_user_behavior_stats(user_id: str, field: str, increment: int = 1):
    """更新用户行为统计"""
    conn = await get_db_connection()
    try:
        valid_fields = ['total_tasks', 'completed_tasks', 'signin_days', 'total_integral_earned', 'total_integral_spent']
        if field not in valid_fields:
            return
        
        await conn.execute(f'''
            INSERT INTO user_behavior_stats (user_id, {field}, last_active_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                {field} = {field} + ?,
                last_active_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, increment, increment))
        await conn.commit()
    except Exception as e:
        logger.error(f"Failed to update user behavior stats: {e}")
    finally:
        await conn.close()


async def handle_user_registered(event: UserRegisteredEvent):
    """处理用户注册事件"""
    logger.info(f"Handling user_registered event: {event.user_id}")
    
    await update_source_stats(event.source, 1)
    
    if event.city:
        await update_city_stats(event.city, 1)
        if event.district:
            await update_district_stats(event.city, event.district, 1)


async def handle_user_location_updated(event: UserLocationUpdatedEvent):
    """处理用户位置更新事件"""
    logger.info(f"Handling user_location_updated event: {event.user_id}")
    
    if event.old_city:
        await update_city_stats(event.old_city, -1)
        if event.old_district:
            await update_district_stats(event.old_city, event.old_district, -1)
    
    if event.city:
        await update_city_stats(event.city, 1)
        if event.district:
            await update_district_stats(event.city, event.district, 1)


async def handle_integral_changed(event: IntegralChangedEvent):
    """处理积分变动事件"""
    logger.info(f"Handling integral_changed event: {event.user_id}, change: {event.change}")
    
    if event.change > 0:
        await update_user_behavior_stats(event.user_id, 'total_integral_earned', int(event.change))
    else:
        await update_user_behavior_stats(event.user_id, 'total_integral_spent', int(abs(event.change)))


async def handle_task_created(event: TaskCreatedEvent):
    """处理任务创建事件"""
    logger.info(f"Handling task_created event: {event.task_id}")
    await update_user_behavior_stats(event.user_id, 'total_tasks', 1)


async def handle_task_completed(event: TaskCompletedEvent):
    """处理任务完成事件"""
    logger.info(f"Handling task_completed event: {event.task_id}")
    await update_user_behavior_stats(event.user_id, 'completed_tasks', 1)


async def handle_signin(event: SigninEvent):
    """处理签到事件"""
    logger.info(f"Handling signin event: {event.user_id}, days: {event.consecutive_days}")
    await update_user_behavior_stats(event.user_id, 'signin_days', 1)


def register_listeners():
    """注册所有事件监听器"""
    event_bus.subscribe('user_registered', lambda e: asyncio.create_task(handle_user_registered(e)))
    event_bus.subscribe('user_location_updated', lambda e: asyncio.create_task(handle_user_location_updated(e)))
    event_bus.subscribe('integral_changed', lambda e: asyncio.create_task(handle_integral_changed(e)))
    event_bus.subscribe('task_created', lambda e: asyncio.create_task(handle_task_created(e)))
    event_bus.subscribe('task_completed', lambda e: asyncio.create_task(handle_task_completed(e)))
    event_bus.subscribe('user_signin', lambda e: asyncio.create_task(handle_signin(e)))
    
    logger.info("Event listeners registered")
