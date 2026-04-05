"""
城市统计更新服务
用于更新城市用户数、小区数等统计信息
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from backend.database import get_db_connection

logger = logging.getLogger(__name__)


async def increment_user_count(city: str, district: str = None):
    """
    增加城市用户计数
    
    Args:
        city: 城市名称
        district: 区县名称（可选）
    """
    if not city:
        return
    
    conn = await get_db_connection()
    
    try:
        now = datetime.now()
        
        await conn.execute('''
            INSERT INTO city_stats (id, city_name, user_count, updated_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(city_name) DO UPDATE SET 
                user_count = user_count + 1,
                updated_at = ?
        ''', (f"city-{city}", city, now, now))
        
        await conn.commit()
        
        logger.info(f"城市 {city} 用户数 +1")
        
        await broadcast_city_stats_update(city)
        
    except Exception as e:
        logger.error(f"更新城市用户数失败: {e}")
    finally:
        await conn.close()


async def decrement_user_count(city: str, district: str = None):
    """
    减少城市用户计数
    
    Args:
        city: 城市名称
        district: 区县名称（可选）
    """
    if not city:
        return
    
    conn = await get_db_connection()
    
    try:
        now = datetime.now()
        
        await conn.execute('''
            UPDATE city_stats 
            SET user_count = MAX(0, user_count - 1), updated_at = ?
            WHERE city_name = ?
        ''', (now, city))
        
        await conn.commit()
        
        logger.info(f"城市 {city} 用户数 -1")
        
        await broadcast_city_stats_update(city)
        
    except Exception as e:
        logger.error(f"更新城市用户数失败: {e}")
    finally:
        await conn.close()


async def update_user_city(user_id: str, old_city: str, new_city: str):
    """
    用户城市变更时更新统计
    
    Args:
        user_id: 用户ID
        old_city: 旧城市
        new_city: 新城市
    """
    if old_city:
        await decrement_user_count(old_city)
    
    if new_city:
        await increment_user_count(new_city)
    
    conn = await get_db_connection()
    
    try:
        await conn.execute(
            "UPDATE users SET city = ? WHERE id = ?",
            (new_city, user_id)
        )
        await conn.commit()
        
    except Exception as e:
        logger.error(f"更新用户城市失败: {e}")
    finally:
        await conn.close()


async def increment_community_count(city: str, count: int = 1):
    """
    增加城市小区计数
    
    Args:
        city: 城市名称
        count: 增加数量
    """
    if not city:
        return
    
    conn = await get_db_connection()
    
    try:
        now = datetime.now()
        
        await conn.execute('''
            INSERT INTO city_stats (id, city_name, community_count, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(city_name) DO UPDATE SET 
                community_count = community_count + ?,
                updated_at = ?
        ''', (f"city-{city}", city, count, now, count, now))
        
        await conn.commit()
        
        await broadcast_city_stats_update(city)
        
    except Exception as e:
        logger.error(f"更新城市小区数失败: {e}")
    finally:
        await conn.close()


async def increment_poi_count(city: str, count: int = 1):
    """
    增加城市POI计数
    
    Args:
        city: 城市名称
        count: 增加数量
    """
    if not city:
        return
    
    conn = await get_db_connection()
    
    try:
        now = datetime.now()
        
        await conn.execute('''
            INSERT INTO city_stats (id, city_name, poi_count, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(city_name) DO UPDATE SET 
                poi_count = poi_count + ?,
                updated_at = ?
        ''', (f"city-{city}", city, count, now, count, now))
        
        await conn.commit()
        
    except Exception as e:
        logger.error(f"更新城市POI数失败: {e}")
    finally:
        await conn.close()


async def get_city_stats(city: str = None) -> list:
    """
    获取城市统计数据
    
    Args:
        city: 城市名称（可选，不传则返回所有）
    """
    conn = await get_db_connection()
    
    try:
        if city:
            cursor = await conn.execute(
                "SELECT * FROM city_stats WHERE city_name = ?", (city,)
            )
            row = await cursor.fetchone()
            return [dict(row)] if row else []
        else:
            cursor = await conn.execute("SELECT * FROM city_stats ORDER BY city_name")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    finally:
        await conn.close()


async def get_all_cities_summary() -> dict:
    """获取所有城市统计汇总"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT 
                COUNT(*) as total_cities,
                SUM(user_count) as total_users,
                SUM(community_count) as total_communities,
                SUM(poi_count) as total_pois
            FROM city_stats
        ''')
        row = await cursor.fetchone()
        
        return dict(row) if row else {}
        
    finally:
        await conn.close()


_websocket_connections = []


async def broadcast_city_stats_update(city: str):
    """
    广播城市统计更新（WebSocket）
    
    Args:
        city: 城市名称
    """
    if not _websocket_connections:
        return
    
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM city_stats WHERE city_name = ?", (city,)
        )
        row = await cursor.fetchone()
        
        if row:
            message = {
                "type": "city_stats_update",
                "data": dict(row)
            }
            
            for ws in _websocket_connections:
                try:
                    await ws.send_json(message)
                except:
                    _websocket_connections.remove(ws)
                    
    finally:
        await conn.close()


def register_websocket(ws):
    """注册WebSocket连接"""
    _websocket_connections.append(ws)


def unregister_websocket(ws):
    """注销WebSocket连接"""
    if ws in _websocket_connections:
        _websocket_connections.remove(ws)
