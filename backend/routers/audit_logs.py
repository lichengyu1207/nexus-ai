"""
审计日志API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
import json

from backend.auth import get_current_user, require_admin
from ..database import get_db_connection

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """
    获取审计日志列表
    
    Args:
        limit: 每页数量
        offset: 偏移量
        action_type: 操作类型过滤
        user_id: 用户ID过滤
        start_date: 开始日期
        end_date: 结束日期
        admin: 管理员用户
        
    Returns:
        审计日志列表
    """
    async with get_db_connection() as conn:
        # 构建查询条件
        conditions = []
        params = []
        
        if action_type:
            conditions.append("action_type = ?")
            params.append(action_type)
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}"
        cursor = await conn.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        # 获取日志列表
        query = f"""
            SELECT id, user_id, username, action_type, resource_type, resource_id,
                   ip_address, user_agent, status, error_message, created_at
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "username": row[2],
                "action_type": row[3],
                "resource_type": row[4],
                "resource_id": row[5],
                "ip_address": row[6],
                "user_agent": row[7],
                "status": row[8],
                "error_message": row[9],
                "created_at": row[10]
            })
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }

@router.get("/stats")
async def get_audit_stats(
    days: int = Query(7, ge=1, le=30),
    admin: dict = Depends(require_admin)
):
    """
    获取审计统计
    
    Args:
        days: 统计天数
        admin: 管理员用户
        
    Returns:
        审计统计数据
    """
    async with get_db_connection() as conn:
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 按操作类型统计
        cursor = await conn.execute("""
            SELECT action_type, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= ?
            GROUP BY action_type
            ORDER BY count DESC
        """, (start_date,))
        
        action_stats = []
        for row in await cursor.fetchall():
            action_stats.append({
                "action_type": row[0],
                "count": row[1]
            })
        
        # 按状态统计
        cursor = await conn.execute("""
            SELECT status, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= ?
            GROUP BY status
        """, (start_date,))
        
        status_stats = []
        for row in await cursor.fetchall():
            status_stats.append({
                "status": row[0],
                "count": row[1]
            })
        
        # 按日期统计
        cursor = await conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (start_date,))
        
        daily_stats = []
        for row in await cursor.fetchall():
            daily_stats.append({
                "date": row[0],
                "count": row[1]
            })
        
        # 活跃用户统计
        cursor = await conn.execute("""
            SELECT username, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= ?
            GROUP BY username
            ORDER BY count DESC
            LIMIT 10
        """, (start_date,))
        
        active_users = []
        for row in await cursor.fetchall():
            active_users.append({
                "username": row[0],
                "count": row[1]
            })
        
        return {
            "action_stats": action_stats,
            "status_stats": status_stats,
            "daily_stats": daily_stats,
            "active_users": active_users,
            "days": days
        }

@router.get("/actions")
async def get_action_types(admin: dict = Depends(require_admin)):
    """获取所有操作类型"""
    async with get_db_connection() as conn:
        cursor = await conn.execute("""
            SELECT DISTINCT action_type FROM audit_logs ORDER BY action_type
        """)
        types = [row[0] for row in await cursor.fetchall()]
        return {"action_types": types}
