"""
管理员审计日志API路由 - 简化版
普通管理员可访问的审计日志查询
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any
import sqlite3
import os

from ...auth import require_admin

router = APIRouter(tags=["admin-audit-simple"])

def get_db_path():
    db_path = os.getenv("DATABASE_PATH", "data/property-ai.db")
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), db_path)
    return db_path

@router.get("/api/admin/audit/simple")
async def get_audit_logs_simple(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """获取审计日志列表（普通管理员可访问）"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM audit_logs")
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT id, user_id, action, resource_type, resource_id, 
                   ip_address, status, created_at
            FROM audit_logs 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "action": row[2],
                "resource_type": row[3],
                "resource_id": row[4],
                "ip_address": row[5],
                "status": row[6],
                "created_at": row[7]
            })
        
        conn.close()
        
        return {"logs": logs, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        return {"logs": [], "total": 0, "page": page, "page_size": page_size, "error": str(e)}

@router.get("/api/admin/audit/simple/stats")
async def get_audit_stats_simple(
    admin: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """获取审计日志统计（普通管理员可访问）"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total_logs = cursor.fetchone()[0]
        
        conn.close()
        
        return {"total_logs": total_logs}
    except Exception as e:
        return {"total_logs": 0, "error": str(e)}
