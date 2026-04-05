"""
用户行为事件追踪API
"""
from fastapi import APIRouter, Depends, Request, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import json
import logging

from backend.auth import get_current_user_optional, require_admin

router = APIRouter(prefix="/api", tags=["events"])
logger = logging.getLogger(__name__)


@router.post("/events")
async def track_event(
    request: Request,
    data: Dict[str, Any],
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """接收前端埋点事件"""
    from ..database import get_db_connection
    
    event_id = str(uuid.uuid4())
    user_id = user.get("id") if user else None
    session_id = data.get("session_id")
    event_type = data.get("event_type", "unknown")
    page_url = data.get("page_url")
    element_id = data.get("element_id")
    properties = json.dumps(data.get("properties", {}), ensure_ascii=False)
    device_info = json.dumps(data.get("device_info", {}), ensure_ascii=False)
    ip_address = request.client.host if request.client else None
    
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT INTO user_events 
            (id, user_id, session_id, event_type, page_url, element_id, properties, device_info, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, user_id, session_id, event_type, page_url, element_id, properties, device_info, ip_address))
        await conn.commit()
    finally:
        await conn.close()
    
    return {"success": True, "event_id": event_id}


@router.get("/admin/analytics/overview")
async def get_analytics_overview(
    admin: dict = Depends(require_admin)
):
    """获取分析概览数据"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        month_start = today_start.replace(day=1)
        
        cursor = await conn.execute("""
            SELECT COUNT(DISTINCT user_id) as dau 
            FROM user_events 
            WHERE created_at >= ? AND user_id IS NOT NULL
        """, (today_start.isoformat(),))
        dau_today = (await cursor.fetchone())["dau"] or 0
        
        cursor = await conn.execute("""
            SELECT COUNT(DISTINCT user_id) as dau 
            FROM user_events 
            WHERE created_at >= ? AND created_at < ? AND user_id IS NOT NULL
        """, (yesterday_start.isoformat(), today_start.isoformat()))
        dau_yesterday = (await cursor.fetchone())["dau"] or 0
        
        cursor = await conn.execute("""
            SELECT COUNT(DISTINCT user_id) as mau 
            FROM user_events 
            WHERE created_at >= ? AND user_id IS NOT NULL
        """, (month_start.isoformat(),))
        mau = (await cursor.fetchone())["mau"] or 0
        
        cursor = await conn.execute("SELECT COUNT(*) as total FROM user_events")
        total_events = (await cursor.fetchone())["total"] or 0
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as count 
            FROM user_events 
            WHERE event_type = 'task_create' AND created_at >= ?
        """, (today_start.isoformat(),))
        tasks_created_today = (await cursor.fetchone())["count"] or 0
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as count 
            FROM user_events 
            WHERE event_type = 'register' AND created_at >= ?
        """, (today_start.isoformat(),))
        new_users_today = (await cursor.fetchone())["count"] or 0
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as count 
            FROM user_events 
            WHERE event_type = 'login' AND created_at >= ?
        """, (today_start.isoformat(),))
        logins_today = (await cursor.fetchone())["count"] or 0
        
        return {
            "dau_today": dau_today,
            "dau_yesterday": dau_yesterday,
            "mau": mau,
            "total_events": total_events,
            "tasks_created_today": tasks_created_today,
            "new_users_today": new_users_today,
            "logins_today": logins_today
        }
    finally:
        await conn.close()


@router.get("/admin/analytics/events")
async def get_events_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """获取事件列表"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        where_clauses = []
        params = []
        
        if event_type:
            where_clauses.append("event_type = ?")
            params.append(event_type)
        if user_id:
            where_clauses.append("user_id = ?")
            params.append(user_id)
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM user_events {where_clause}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT id, user_id, session_id, event_type, page_url, element_id, 
                   properties, ip_address, created_at
            FROM user_events 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        events = []
        async for row in cursor:
            events.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "session_id": row["session_id"],
                "event_type": row["event_type"],
                "page_url": row["page_url"],
                "element_id": row["element_id"],
                "properties": json.loads(row["properties"]) if row["properties"] else {},
                "ip_address": row["ip_address"],
                "created_at": row["created_at"]
            })
        
        return {
            "events": events,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.get("/admin/analytics/trend")
async def get_analytics_trend(
    days: int = Query(7, ge=1, le=30),
    admin: dict = Depends(require_admin)
):
    """获取趋势数据"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        trend_data = []
        now = datetime.utcnow()
        
        for i in range(days):
            day_end = now - timedelta(days=i)
            day_start = day_end.replace(hour=0, minute=0, second=0, microsecond=0)
            
            cursor = await conn.execute("""
                SELECT COUNT(DISTINCT user_id) as dau 
                FROM user_events 
                WHERE created_at >= ? AND created_at < ? AND user_id IS NOT NULL
            """, (day_start.isoformat(), day_end.replace(hour=23, minute=59, second=59).isoformat()))
            dau = (await cursor.fetchone())["dau"] or 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) as count 
                FROM user_events 
                WHERE created_at >= ? AND created_at < ?
            """, (day_start.isoformat(), day_end.replace(hour=23, minute=59, second=59).isoformat()))
            events = (await cursor.fetchone())["count"] or 0
            
            trend_data.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "dau": dau,
                "events": events
            })
        
        return {"trend": list(reversed(trend_data))}
    finally:
        await conn.close()


@router.get("/admin/analytics/event-types")
async def get_event_types_stats(
    admin: dict = Depends(require_admin)
):
    """获取事件类型统计"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM user_events 
            GROUP BY event_type 
            ORDER BY count DESC 
            LIMIT 20
        """)
        
        types = []
        async for row in cursor:
            types.append({
                "event_type": row["event_type"],
                "count": row["count"]
            })
        
        return {"event_types": types}
    finally:
        await conn.close()
