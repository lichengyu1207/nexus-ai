"""
管理员合规管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import csv
import io
from datetime import datetime

from ...auth import require_admin
from ...database import get_db_connection

router = APIRouter(prefix="/api/admin/compliance", tags=["admin-compliance"])


@router.get("/privacy-logs")
async def get_privacy_logs(
    user_id: str = Query(None),
    policy_version: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin)
):
    """获取隐私政策同意日志"""
    conn = await get_db_connection()
    try:
        conditions = []
        params = []
        
        if user_id:
            conditions.append("pc.user_id = ?")
            params.append(user_id)
        if policy_version:
            conditions.append("pc.policy_version = ?")
            params.append(policy_version)
        if start_date:
            conditions.append("date(pc.agreed_at) >= date(?)")
            params.append(start_date)
        if end_date:
            conditions.append("date(pc.agreed_at) <= date(?)")
            params.append(end_date)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        count_cursor = await conn.execute(
            f"""
            SELECT COUNT(*) as count 
            FROM privacy_consents pc
            {where_clause}
            """,
            params
        )
        total = (await count_cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            f"""
            SELECT pc.*, u.email, u.username, u.full_name
            FROM privacy_consents pc
            LEFT JOIN users u ON pc.user_id = u.id
            {where_clause}
            ORDER BY pc.agreed_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        logs = [dict(row) for row in rows]
        
        return {"items": logs, "total": total}
    finally:
        await conn.close()


@router.get("/privacy-logs/export")
async def export_privacy_logs(
    user_id: str = Query(None),
    policy_version: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    admin: dict = Depends(require_admin)
):
    """导出隐私政策同意日志为 CSV"""
    conn = await get_db_connection()
    try:
        conditions = []
        params = []
        
        if user_id:
            conditions.append("pc.user_id = ?")
            params.append(user_id)
        if policy_version:
            conditions.append("pc.policy_version = ?")
            params.append(policy_version)
        if start_date:
            conditions.append("date(pc.agreed_at) >= date(?)")
            params.append(start_date)
        if end_date:
            conditions.append("date(pc.agreed_at) <= date(?)")
            params.append(end_date)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        cursor = await conn.execute(
            f"""
            SELECT pc.id, pc.user_id, u.email, u.username, pc.policy_version, 
                   pc.policy_title, pc.ip_address, pc.user_agent, pc.agreed_at
            FROM privacy_consents pc
            LEFT JOIN users u ON pc.user_id = u.id
            {where_clause}
            ORDER BY pc.agreed_at DESC
            """,
            params
        )
        rows = await cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "ID", "用户ID", "邮箱", "用户名", "政策版本", 
            "政策标题", "IP地址", "User-Agent", "同意时间"
        ])
        
        for row in rows:
            writer.writerow([
                row["id"],
                row["user_id"],
                row["email"] or "",
                row["username"] or "",
                row["policy_version"],
                row["policy_title"] or "",
                row["ip_address"] or "",
                row["user_agent"] or "",
                row["agreed_at"]
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=privacy_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    finally:
        await conn.close()


@router.get("/privacy-logs/stats")
async def get_privacy_logs_stats(admin: dict = Depends(require_admin)):
    """获取隐私政策同意统计"""
    conn = await get_db_connection()
    try:
        stats = {}
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM privacy_consents")
        stats["total_agreements"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(DISTINCT user_id) as count FROM privacy_consents"
        )
        stats["unique_users"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT policy_version, COUNT(*) as count 
            FROM privacy_consents 
            GROUP BY policy_version
            ORDER BY policy_version DESC
            """
        )
        stats["by_version"] = {row["policy_version"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            """
            SELECT date(agreed_at) as date, COUNT(*) as count 
            FROM privacy_consents 
            WHERE agreed_at >= date('now', '-30 days')
            GROUP BY date(agreed_at)
            ORDER BY date
            """
        )
        stats["trend_30_days"] = [
            {"date": row["date"], "count": row["count"]} 
            for row in await cursor.fetchall()
        ]
        
        cursor = await conn.execute(
            """
            SELECT COUNT(*) as count 
            FROM privacy_consents 
            WHERE agreed_at >= date('now', '-7 days')
            """
        )
        stats["recent_week"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT COUNT(*) as count 
            FROM privacy_consents 
            WHERE agreed_at >= date('now', '-30 days')
            """
        )
        stats["recent_month"] = (await cursor.fetchone())["count"]
        
        return stats
    finally:
        await conn.close()


@router.get("/policy-versions")
async def get_policy_versions(admin: dict = Depends(require_admin)):
    """获取所有隐私政策版本"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT id, version, title, effective_date, is_current, created_at
            FROM privacy_policy_versions
            ORDER BY effective_date DESC
            """
        )
        versions = [dict(row) for row in await cursor.fetchall()]
        return {"items": versions}
    finally:
        await conn.close()
