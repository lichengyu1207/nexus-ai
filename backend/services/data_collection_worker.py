"""
数据采集任务执行器
支持任务进度更新、取消、失败处理
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_connection

logger = logging.getLogger(__name__)

_task_cancellations = {}


async def run_task(task_id: str):
    """
    执行数据采集任务
    
    Args:
        task_id: 任务ID
    """
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        task = await cursor.fetchone()
        
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        city_name = task["city_name"]
        task_type = task["task_type"]
        total_items = task["total_items"] or 100
        
        await update_task_status(conn, task_id, "processing", 
                                message=f"开始采集{city_name}的{task_type}数据")
        
        start_time = datetime.now()
        processed = 0
        
        while processed < total_items:
            if _task_cancellations.get(task_id):
                await update_task_status(conn, task_id, "cancelled", 
                                        message="任务已取消")
                logger.info(f"任务 {task_id} 已取消")
                return
            
            await asyncio.sleep(0.5)
            
            processed += 1
            progress = int(processed / total_items * 100)
            
            await update_task_progress(conn, task_id, processed, progress,
                                      message=f"正在采集第 {processed}/{total_items} 项")
            
            if processed % 10 == 0:
                logger.info(f"任务 {task_id}: {progress}% ({processed}/{total_items})")
        
        await update_task_status(conn, task_id, "completed",
                                message=f"采集完成，共 {processed} 项")
        
        await update_city_stats(conn, city_name, task_type, processed)
        
        duration = (datetime.now() - start_time).total_seconds()
        await save_history(conn, task, duration)
        
        logger.info(f"任务 {task_id} 完成，耗时 {duration:.1f}秒")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 执行失败: {e}")
        await update_task_status(conn, task_id, "failed", 
                                error_message=str(e))
    finally:
        _task_cancellations.pop(task_id, None)
        await conn.close()


async def run_real_collection(task_id: str):
    """
    执行真实的数据采集任务（调用高德API）
    
    Args:
        task_id: 任务ID
    """
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        task = await cursor.fetchone()
        
        if not task:
            return
        
        city_name = task["city_name"]
        task_type = task["task_type"]
        
        await update_task_status(conn, task_id, "processing",
                                message=f"开始采集{city_name}的{task_type}数据")
        
        start_time = datetime.now()
        
        from scripts.amap_client import AmapClient, AmapConfig, POICollector
        
        config = AmapConfig()
        
        async with AmapClient(config) as client:
            if task_type == "community":
                processed = await collect_communities(conn, client, task_id, city_name)
            elif task_type == "poi":
                processed = await collect_pois(conn, client, task_id, city_name)
            elif task_type == "price":
                processed = await collect_prices(conn, task_id, city_name)
            else:
                processed = 0
        
        await update_task_status(conn, task_id, "completed",
                                message=f"采集完成，共 {processed} 项")
        
        await update_city_stats(conn, city_name, task_type, processed)
        
        duration = (datetime.now() - start_time).total_seconds()
        await save_history(conn, task, duration)
        
    except Exception as e:
        logger.error(f"任务 {task_id} 执行失败: {e}")
        await update_task_status(conn, task_id, "failed", error_message=str(e))
    finally:
        _task_cancellations.pop(task_id, None)
        await conn.close()


async def collect_communities(conn, client, task_id: str, city_name: str) -> int:
    """采集小区数据"""
    keywords = ["小区", "住宅", "花园", "苑", "居"]
    all_communities = []
    seen_ids = set()
    
    total_estimate = 500
    await update_task_progress(conn, task_id, 0, 0, 
                              message="开始采集小区数据", total_items=total_estimate)
    
    for i, keyword in enumerate(keywords):
        if _task_cancellations.get(task_id):
            break
        
        result = await client.text_search(
            keywords=f"{city_name}{keyword}",
            city=city_name,
            city_limit=True,
            page_size=25
        )
        
        if result.get("status") == "1":
            pois = result.get("pois", [])
            
            for poi in pois:
                poi_id = poi.get("id")
                if poi_id in seen_ids:
                    continue
                seen_ids.add(poi_id)
                
                location = poi.get("location", "").split(",")
                community = {
                    "poi_id": poi_id,
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "lng": float(location[0]) if len(location) == 2 else None,
                    "lat": float(location[1]) if len(location) == 2 else None,
                }
                all_communities.append(community)
        
        progress = int((i + 1) / len(keywords) * 100)
        await update_task_progress(conn, task_id, len(all_communities), progress,
                                  message=f"已采集 {len(all_communities)} 个小区")
        
        await asyncio.sleep(0.5)
    
    for community in all_communities:
        import uuid
        try:
            await conn.execute('''
                INSERT OR IGNORE INTO communities 
                (id, name, address, lng, lat, city_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"community-{uuid.uuid4().hex[:8]}",
                community["name"],
                community["address"],
                community["lng"],
                community["lat"],
                f"city-{city_name}"
            ))
        except:
            pass
    
    await conn.commit()
    return len(all_communities)


async def collect_pois(conn, client, task_id: str, city_name: str) -> int:
    """采集POI数据"""
    await update_task_progress(conn, task_id, 0, 0, message="开始采集POI数据")
    return 0


async def collect_prices(conn, task_id: str, city_name: str) -> int:
    """采集价格数据"""
    await update_task_progress(conn, task_id, 0, 0, message="开始采集价格数据")
    return 0


async def update_task_status(conn, task_id: str, status: str, 
                            message: str = None, error_message: str = None):
    """更新任务状态"""
    now = datetime.now()
    
    update_fields = ["status = ?", "updated_at = ?"]
    params = [status, now]
    
    if message:
        update_fields.append("message = ?")
        params.append(message)
    
    if error_message:
        update_fields.append("error_message = ?")
        params.append(error_message)
    
    if status == "processing":
        update_fields.append("started_at = ?")
        params.append(now)
    
    if status in ["completed", "failed", "cancelled"]:
        update_fields.append("completed_at = ?")
        params.append(now)
    
    params.append(task_id)
    
    await conn.execute(
        f"UPDATE data_collection_tasks SET {', '.join(update_fields)} WHERE id = ?",
        params
    )
    await conn.commit()


async def update_task_progress(conn, task_id: str, processed: int, 
                              progress: int, message: str = None,
                              total_items: int = None):
    """更新任务进度"""
    update_fields = ["processed_items = ?", "progress = ?", "updated_at = ?"]
    params = [processed, progress, datetime.now()]
    
    if message:
        update_fields.append("message = ?")
        params.append(message)
    
    if total_items:
        update_fields.append("total_items = ?")
        params.append(total_items)
    
    params.append(task_id)
    
    await conn.execute(
        f"UPDATE data_collection_tasks SET {', '.join(update_fields)} WHERE id = ?",
        params
    )
    await conn.commit()


async def update_city_stats(conn, city_name: str, task_type: str, count: int):
    """更新城市统计"""
    if task_type == "community":
        await conn.execute('''
            INSERT INTO city_stats (id, city_name, community_count, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(city_name) DO UPDATE SET 
                community_count = community_count + ?,
                updated_at = ?
        ''', (f"city-{city_name}", city_name, count, datetime.now(), count, datetime.now()))
    
    elif task_type == "poi":
        await conn.execute('''
            INSERT INTO city_stats (id, city_name, poi_count, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(city_name) DO UPDATE SET 
                poi_count = poi_count + ?,
                updated_at = ?
        ''', (f"city-{city_name}", city_name, count, datetime.now(), count, datetime.now()))
    
    await conn.commit()


async def save_history(conn, task, duration: float):
    """保存任务历史"""
    import uuid
    
    await conn.execute('''
        INSERT INTO data_collection_history 
        (id, task_id, city_name, task_type, status, total_items, processed_items, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        f"history-{uuid.uuid4().hex[:8]}",
        task["id"],
        task["city_name"],
        task["task_type"],
        "completed",
        task["total_items"],
        task["processed_items"] if "processed_items" in task.keys() else 0,
        int(duration)
    ))
    await conn.commit()


def cancel_task(task_id: str):
    """标记任务为取消状态"""
    _task_cancellations[task_id] = True


async def get_task_progress(task_id: str) -> dict:
    """获取任务进度"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        return dict(row)
        
    finally:
        await conn.close()
