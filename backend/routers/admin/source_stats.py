"""
管理员来源统计API路由
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from backend.database import get_db
from backend.auth import require_admin
from backend.services.user_source import get_source_config
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/source", tags=["admin-source"])


class SourceOverviewResponse(BaseModel):
    """来源概览响应"""
    total: int
    sources: dict
    referred_by: dict
    cross_analysis: List[dict]
    trend: List[dict]


class SourceLogItem(BaseModel):
    """来源日志项"""
    id: str
    user_id: str
    user_email: str
    source: str
    landing_page: Optional[str]
    referrer: Optional[str]
    created_at: str


class SourceLogsResponse(BaseModel):
    """来源日志响应"""
    logs: List[SourceLogItem]
    total: int
    limit: int
    offset: int


@router.get("/overview", response_model=SourceOverviewResponse)
async def get_source_overview(
    range: str = Query("30d", description="时间范围: 7d, 30d, 90d"),
    current_user: dict = Depends(require_admin)
):
    """
    获取来源统计概览
    
    返回各来源用户数量、占比和趋势
    """
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 30)
    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        # 获取总用户数
        await cursor.execute("SELECT COUNT(*) as total FROM users")
        total_row = await cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        # 获取各客观来源用户数
        await cursor.execute(
            """
            SELECT source, COUNT(*) as count 
            FROM users 
            WHERE source IS NOT NULL AND created_at >= ?
            GROUP BY source
            """,
            (start_date,)
        )
        source_rows = await cursor.fetchall()
        
        sources = {}
        for row in source_rows:
            sources[row["source"]] = row["count"]
        
        # 获取各主观来源用户数
        await cursor.execute(
            """
            SELECT referred_by, COUNT(*) as count 
            FROM users 
            WHERE referred_by IS NOT NULL AND created_at >= ?
            GROUP BY referred_by
            """,
            (start_date,)
        )
        referred_rows = await cursor.fetchall()
        
        referred_by = {}
        for row in referred_rows:
            referred_by[row["referred_by"]] = row["count"]
        
        # 获取交叉分析数据
        await cursor.execute(
            """
            SELECT source, referred_by, COUNT(*) as count 
            FROM users 
            WHERE source IS NOT NULL AND created_at >= ?
            GROUP BY source, referred_by
            ORDER BY count DESC
            """,
            (start_date,)
        )
        cross_rows = await cursor.fetchall()
        
        cross_analysis = []
        for row in cross_rows:
            cross_analysis.append({
                "source": row["source"] or "unknown",
                "referred_by": row["referred_by"] or "unknown",
                "count": row["count"]
            })
        
        # 获取趋势数据
        trend = []
        for i in range(min(days, 7)):
            date = (datetime.utcnow() - timedelta(days=6-i)).strftime("%Y-%m-%d")
            await cursor.execute(
                """
                SELECT source, COUNT(*) as count 
                FROM users 
                WHERE date(created_at) = ?
                GROUP BY source
                """,
                (date,)
            )
            day_rows = await cursor.fetchall()
            
            day_data = {"date": date}
            for row in day_rows:
                day_data[row["source"]] = row["count"]
            trend.append(day_data)
        
        return SourceOverviewResponse(
            total=total,
            sources=sources,
            referred_by=referred_by,
            cross_analysis=cross_analysis,
            trend=trend
        )


@router.get("/detail", response_model=SourceLogsResponse)
async def get_source_detail(
    range: str = Query("30d", description="时间范围"),
    source: Optional[str] = Query(None, description="来源筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """
    获取来源详细日志
    
    支持分页和筛选
    """
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range, 30)
    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        # 构建查询条件
        where_clause = "WHERE us.created_at >= ?"
        params = [start_date]
        
        if source:
            where_clause += " AND us.source = ?"
            params.append(source)
        
        # 获取总数
        await cursor.execute(
            f"""
            SELECT COUNT(*) as total 
            FROM user_sources us 
            {where_clause}
            """,
            params
        )
        total_row = await cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        # 获取日志
        params.extend([limit, offset])
        await cursor.execute(
            f"""
            SELECT us.id, us.user_id, u.email as user_email, us.source, 
                   us.url_params as landing_page, us.ip_address as referrer, us.created_at
            FROM user_sources us
            LEFT JOIN users u ON us.user_id = u.id
            {where_clause}
            ORDER BY us.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params
        )
        rows = await cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append(SourceLogItem(
                id=row["id"],
                user_id=row["user_id"],
                user_email=row["user_email"] or "unknown",
                source=row["source"],
                landing_page=row["landing_page"],
                referrer=row["referrer"],
                created_at=row["created_at"]
            ))
        
        return SourceLogsResponse(
            logs=logs,
            total=total,
            limit=limit,
            offset=offset
        )
