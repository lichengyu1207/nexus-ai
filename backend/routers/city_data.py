# -*- coding: utf-8 -*-
"""
城市数据API接口
提供城市数据查询和采集控制接口
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cities", tags=["城市数据"])


@router.get("/")
async def list_cities() -> Dict[str, Any]:
    """
    获取所有城市列表
    
    返回已配置的城市列表及其采集状态
    """
    from ..services.city_data_scheduler_service import get_scheduler
    
    scheduler = get_scheduler()
    status = scheduler.get_status()
    
    return {
        "success": True,
        "cities": status["cities"],
        "total": len(status["cities"]),
        "last_run": status["last_run"],
        "run_count": status["run_count"]
    }


@router.get("/{city}/summary")
async def get_city_summary(city: str) -> Dict[str, Any]:
    """
    获取城市数据摘要
    
    适合前端展示的简洁格式数据
    
    Args:
        city: 城市名称
    
    Returns:
        城市数据摘要
    """
    try:
        from ..database_pg import get_db
        
        async with get_db() as db:
            record = await db.fetchrow("""
                SELECT * FROM city_data 
                WHERE city = $1 
                ORDER BY created_at DESC 
                LIMIT 1
            """, city)
            
            if not record:
                raise HTTPException(status_code=404, detail=f"城市 {city} 数据不存在")
            
            return {
                "success": True,
                "city": city,
                "data": {
                    "avg_price": record.get("avg_price"),
                    "total_houses": record.get("total_houses"),
                    "price_trend": record.get("price_trend"),
                    "hot_districts": record.get("hot_districts", []),
                    "last_updated": record.get("created_at").isoformat() if record.get("created_at") else None
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取城市数据失败: {e}")
        return {
            "success": False,
            "city": city,
            "error": str(e),
            "message": "获取城市数据失败"
        }


@router.get("/{city}/detail")
async def get_city_detail(city: str) -> Dict[str, Any]:
    """
    获取城市详细数据
    
    包含完整的城市房源数据
    
    Args:
        city: 城市名称
    """
    try:
        from ..database_pg import get_db
        
        async with get_db() as db:
            records = await db.fetch("""
                SELECT * FROM city_data 
                WHERE city = $1 
                ORDER BY created_at DESC 
                LIMIT 10
            """, city)
            
            if not records:
                raise HTTPException(status_code=404, detail=f"城市 {city} 数据不存在")
            
            return {
                "success": True,
                "city": city,
                "records": [dict(r) for r in records],
                "total": len(records)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取城市详细数据失败: {e}")
        return {
            "success": False,
            "city": city,
            "error": str(e)
        }


@router.post("/collect")
async def trigger_collection(
    background_tasks: BackgroundTasks,
    cities: Optional[List[str]] = Query(None, description="要采集的城市列表")
) -> Dict[str, Any]:
    """
    手动触发城市数据采集
    
    Args:
        cities: 要采集的城市列表, 为空则采集所有配置城市
    """
    from ..services.city_data_scheduler_service import get_scheduler
    
    scheduler = get_scheduler()
    
    async def run_collection():
        try:
            result = await scheduler.run_now(cities)
            logger.info(f"采集完成: {result}")
        except Exception as e:
            logger.error(f"采集失败: {e}")
    
    background_tasks.add_task(run_collection)
    
    return {
        "success": True,
        "message": "采集任务已启动",
        "cities": cities or scheduler.cities,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status/scheduler")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    获取调度器状态
    
    返回调度器运行状态和最近采集记录
    """
    from ..services.city_data_scheduler_service import get_scheduler
    
    scheduler = get_scheduler()
    return {
        "success": True,
        "status": scheduler.get_status()
    }


@router.post("/config")
async def update_config(
    cities: Optional[List[str]] = None,
    schedule_day: Optional[str] = None,
    schedule_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    更新采集配置
    
    Args:
        cities: 新的城市列表
        schedule_day: 调度日期 (monday-sunday)
        schedule_time: 调度时间 (HH:MM)
    """
    from ..services.city_data_scheduler_service import get_scheduler
    
    scheduler = get_scheduler()
    
    schedule = {}
    if schedule_day:
        schedule["day"] = schedule_day
    if schedule_time:
        schedule["time"] = schedule_time
    
    scheduler.configure(cities=cities, schedule=schedule if schedule else None)
    
    return {
        "success": True,
        "message": "配置已更新",
        "config": scheduler.get_status()
    }


def include_router(app):
    """将路由注册到FastAPI应用"""
    app.include_router(router)
