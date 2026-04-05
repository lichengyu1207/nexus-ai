"""
核心指标看板API
DAU、MAU、留存率、转化率、NPS
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from ..auth import get_current_user
from ..database import get_db_connection

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def metrics_dashboard(user: dict = Depends(get_current_user)):
    """获取核心指标看板"""
    conn = await get_db_connection()
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        dau = 0
        dau_yesterday = 0
        mau = 0
        retained = 0
        
        try:
            cursor = await conn.execute("""
                SELECT COUNT(DISTINCT user_id) as dau
                FROM user_events
                WHERE DATE(created_at) = ?
            """, (today.isoformat(),))
            row = await cursor.fetchone()
            dau = row["dau"] if row else 0
        except Exception as e:
            logger.warning(f"Failed to get DAU: {e}")
        
        try:
            cursor = await conn.execute("""
                SELECT COUNT(DISTINCT user_id) as dau
                FROM user_events
                WHERE DATE(created_at) = ?
            """, (yesterday.isoformat(),))
            row = await cursor.fetchone()
            dau_yesterday = row["dau"] if row else 0
        except Exception as e:
            logger.warning(f"Failed to get yesterday DAU: {e}")
        
        try:
            cursor = await conn.execute("""
                SELECT COUNT(DISTINCT user_id) as mau
                FROM user_events
                WHERE DATE(created_at) >= ?
            """, (month_ago.isoformat(),))
            row = await cursor.fetchone()
            mau = row["mau"] if row else 0
        except Exception as e:
            logger.warning(f"Failed to get MAU: {e}")
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as new_users
            FROM users
            WHERE DATE(created_at) = ?
        """, (today.isoformat(),))
        new_users_today = (await cursor.fetchone())["new_users"]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as tasks
            FROM analysis_tasks
            WHERE DATE(created_at) = ?
        """, (today.isoformat(),))
        tasks_today = (await cursor.fetchone())["tasks"]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as reports
            FROM analysis_tasks
            WHERE DATE(created_at) = ? AND status = 'completed'
        """, (today.isoformat(),))
        reports_today = (await cursor.fetchone())["reports"]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as paid_users
            FROM users
            WHERE role IN ('member', 'vip', 'admin')
        """)
        paid_users = (await cursor.fetchone())["paid_users"]
        
        cursor = await conn.execute("SELECT COUNT(*) as total FROM users")
        total_users = (await cursor.fetchone())["total"]
        
        conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
        dau_growth = ((dau - dau_yesterday) / dau_yesterday * 100) if dau_yesterday > 0 else 0
        
        try:
            cursor = await conn.execute("""
                SELECT COUNT(DISTINCT e.user_id) as retained
                FROM user_events e
                JOIN users u ON e.user_id = u.id
                WHERE DATE(u.created_at) = ?
                AND DATE(e.created_at) >= ?
            """, (week_ago.isoformat(), today.isoformat()))
            row = await cursor.fetchone()
            retained = row["retained"] if row else 0
        except Exception as e:
            logger.warning(f"Failed to get retention: {e}")
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as cohort
            FROM users
            WHERE DATE(created_at) = ?
        """, (week_ago.isoformat(),))
        cohort = (await cursor.fetchone())["cohort"]
        
        retention_7d = (retained / cohort * 100) if cohort > 0 else 0
        
        try:
            cursor = await conn.execute("""
                SELECT AVG(rating) as avg_rating
                FROM user_feedback
                WHERE rating IS NOT NULL
            """)
            avg_rating = (await cursor.fetchone())["avg_rating"] or 0
        except Exception as e:
            logger.warning(f"Failed to get avg rating: {e}")
            avg_rating = 0
        
        return {
            "dau": {
                "today": dau,
                "yesterday": dau_yesterday,
                "growth": round(dau_growth, 1)
            },
            "mau": mau,
            "new_users_today": new_users_today,
            "tasks_today": tasks_today,
            "reports_today": reports_today,
            "users": {
                "total": total_users,
                "paid": paid_users,
                "conversion_rate": round(conversion_rate, 1)
            },
            "retention": {
                "7d": round(retention_7d, 1)
            },
            "nps": {
                "avg_rating": round(avg_rating, 1)
            }
        }
    finally:
        await conn.close()


@router.get("/trend")
async def metrics_trend(
    days: int = 7,
    user: dict = Depends(get_current_user)
):
    """获取指标趋势"""
    conn = await get_db_connection()
    try:
        today = datetime.utcnow().date()
        trend = []
        
        for i in range(days):
            date = today - timedelta(days=days - i - 1)
            
            dau = 0
            try:
                cursor = await conn.execute("""
                    SELECT COUNT(DISTINCT user_id) as dau
                    FROM user_events
                    WHERE DATE(created_at) = ?
                """, (date.isoformat(),))
                row = await cursor.fetchone()
                dau = row["dau"] if row else 0
            except:
                pass
            
            cursor = await conn.execute("""
                SELECT COUNT(*) as new_users
                FROM users
                WHERE DATE(created_at) = ?
            """, (date.isoformat(),))
            new_users = (await cursor.fetchone())["new_users"]
            
            cursor = await conn.execute("""
                SELECT COUNT(*) as tasks
                FROM analysis_tasks
                WHERE DATE(created_at) = ?
            """, (date.isoformat(),))
            tasks = (await cursor.fetchone())["tasks"]
            
            trend.append({
                "date": date.isoformat(),
                "dau": dau,
                "new_users": new_users,
                "tasks": tasks
            })
        
        return {"trend": trend}
    finally:
        await conn.close()
