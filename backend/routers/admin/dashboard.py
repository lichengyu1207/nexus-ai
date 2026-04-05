"""
管理员仪表盘API路由
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import sqlite3
import os

from ...auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])

def get_db_path():
    db_path = os.getenv("DATABASE_PATH", "data/property-ai.db")
    if not os.path.isabs(db_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        db_path = os.path.join(base_dir, db_path)
    return db_path

@router.get("/dashboard")
async def get_dashboard(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取仪表盘统计数据"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'super_admin')")
        admin_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1 OR is_active IS NULL")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_tasks")
        total_tasks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_tasks WHERE status = 'completed'")
        completed_tasks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reports")
        total_reports = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teams")
        total_teams = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM article_comments")
        total_comments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM manual_recharge_orders WHERE status = 'pending'")
        pending_recharge = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM manual_recharge_orders WHERE status = 'completed'")
        completed_recharge = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_users": total_users,
            "admin_users": admin_users,
            "active_users": active_users,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "total_reports": total_reports,
            "total_teams": total_teams,
            "total_comments": total_comments,
            "pending_recharge": pending_recharge,
            "completed_recharge": completed_recharge,
        }
    except Exception as e:
        return {
            "total_users": 0,
            "admin_users": 0,
            "active_users": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "total_reports": 0,
            "total_teams": 0,
            "total_comments": 0,
            "pending_recharge": 0,
            "completed_recharge": 0,
            "error": str(e)
        }

@router.get("/stats/overview")
async def get_stats_overview(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取系统概览统计"""
    return await get_dashboard(admin)
