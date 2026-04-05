"""
性能监控API路由
收集和查询前端性能指标
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import json

from ..database import get_db_connection
from backend.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/performance", tags=["performance"])


class PerformanceMetric(BaseModel):
    name: str
    value: float
    rating: str
    delta: float
    id: str
    navigationType: str
    timestamp: int
    url: str
    userAgent: str
    connectionType: Optional[str] = None
    memoryUsage: Optional[float] = None


class VitalsBatch(BaseModel):
    metrics: List[PerformanceMetric]
    sessionId: str
    userId: Optional[str] = None
    pageLoadTime: float


class PerformanceStats(BaseModel):
    metric_name: str
    avg_value: float
    p50_value: float
    p75_value: float
    p95_value: float
    p99_value: float
    good_count: int
    needs_improvement_count: int
    poor_count: int
    total_count: int
    good_rate: float


@router.post("/vitals")
async def submit_vitals(batch: VitalsBatch):
    """接收前端性能指标上报"""
    async with get_db_connection() as db:
        for metric in batch.metrics:
            await db.execute("""
                INSERT INTO performance_metrics (
                    metric_name, value, rating, delta, metric_id,
                    navigation_type, timestamp, url, user_agent,
                    connection_type, memory_usage, session_id, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.value,
                metric.rating,
                metric.delta,
                metric.id,
                metric.navigationType,
                datetime.fromtimestamp(metric.timestamp / 1000),
                metric.url,
                metric.userAgent,
                metric.connectionType,
                metric.memoryUsage,
                batch.sessionId,
                batch.userId,
            ))
        await db.commit()
    
    return {"status": "ok", "count": len(batch.metrics)}


@router.get("/stats", response_model=List[PerformanceStats])
async def get_performance_stats(
    days: int = Query(7, ge=1, le=30),
    metric_name: Optional[str] = None,
    current_user = Depends(require_admin),
):
    """获取性能统计（管理员）"""
    async with get_db_connection() as db:
        where_clause = "WHERE timestamp >= datetime('now', ?)"
        params = [f"-{days} days"]
        
        if metric_name:
            where_clause += " AND metric_name = ?"
            params.append(metric_name)
        
        cursor = await db.execute(f"""
            SELECT 
                metric_name,
                AVG(value) as avg_value,
                COUNT(*) as total_count,
                SUM(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) as good_count,
                SUM(CASE WHEN rating = 'needs-improvement' THEN 1 ELSE 0 END) as needs_improvement_count,
                SUM(CASE WHEN rating = 'poor' THEN 1 ELSE 0 END) as poor_count
            FROM performance_metrics
            {where_clause}
            GROUP BY metric_name
            ORDER BY total_count DESC
        """, params)
        
        rows = await cursor.fetchall()
        
        stats = []
        for row in rows:
            metric = row[0]
            
            percentiles = await _get_percentiles(db, metric, days)
            
            total = row[2]
            good_rate = row[3] / total if total > 0 else 0
            
            stats.append(PerformanceStats(
                metric_name=metric,
                avg_value=round(row[1], 2),
                p50_value=percentiles['p50'],
                p75_value=percentiles['p75'],
                p95_value=percentiles['p95'],
                p99_value=percentiles['p99'],
                good_count=row[3],
                needs_improvement_count=row[4],
                poor_count=row[5],
                total_count=total,
                good_rate=round(good_rate, 4),
            ))
        
        return stats


async def _get_percentiles(db, metric_name: str, days: int) -> dict:
    """计算百分位数"""
    cursor = await db.execute("""
        SELECT value FROM performance_metrics
        WHERE metric_name = ? AND timestamp >= datetime('now', ?)
        ORDER BY value
    """, (metric_name, f"-{days} days"))
    
    values = [row[0] for row in await cursor.fetchall()]
    
    if not values:
        return {'p50': 0, 'p75': 0, 'p95': 0, 'p99': 0}
    
    def percentile(data: List[float], p: float) -> float:
        if not data:
            return 0
        k = (len(data) - 1) * p
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return round(data[f] + (k - f) * (data[c] - data[f]), 2)
    
    return {
        'p50': percentile(values, 0.50),
        'p75': percentile(values, 0.75),
        'p95': percentile(values, 0.95),
        'p99': percentile(values, 0.99),
    }


@router.get("/trend")
async def get_performance_trend(
    days: int = Query(7, ge=1, le=30),
    metric_name: str = Query("LCP"),
    current_user = Depends(require_admin),
):
    """获取性能趋势数据"""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT 
                date(timestamp) as date,
                AVG(value) as avg_value,
                COUNT(*) as count,
                SUM(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) as good_count
            FROM performance_metrics
            WHERE metric_name = ? AND timestamp >= datetime('now', ?)
            GROUP BY date(timestamp)
            ORDER BY date
        """, (metric_name, f"-{days} days"))
        
        rows = await cursor.fetchall()
        
        return [
            {
                "date": row[0],
                "avg_value": round(row[1], 2),
                "count": row[2],
                "good_rate": round(row[3] / row[2], 4) if row[2] > 0 else 0,
            }
            for row in rows
        ]


@router.get("/pages")
async def get_page_performance(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(require_admin),
):
    """获取页面性能排名"""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT 
                url,
                COUNT(*) as total_requests,
                AVG(CASE WHEN metric_name = 'LCP' THEN value END) as avg_lcp,
                AVG(CASE WHEN metric_name = 'FID' THEN value END) as avg_fid,
                AVG(CASE WHEN metric_name = 'CLS' THEN value END) as avg_cls,
                SUM(CASE WHEN rating = 'poor' THEN 1 ELSE 0 END) as poor_count
            FROM performance_metrics
            WHERE timestamp >= datetime('now', ?)
            GROUP BY url
            ORDER BY poor_count DESC, total_requests DESC
            LIMIT ?
        """, (f"-{days} days", limit))
        
        rows = await cursor.fetchall()
        
        return [
            {
                "url": row[0],
                "total_requests": row[1],
                "avg_lcp": round(row[2], 2) if row[2] else None,
                "avg_fid": round(row[3], 2) if row[3] else None,
                "avg_cls": round(row[4], 4) if row[4] else None,
                "poor_count": row[5],
            }
            for row in rows
        ]


@router.get("/summary")
async def get_performance_summary(
    current_user = Depends(require_admin),
):
    """获取性能概览"""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(*) as total_metrics,
                MAX(timestamp) as last_report
            FROM performance_metrics
            WHERE timestamp >= datetime('now', '-1 day')
        """)
        
        row = await cursor.fetchone()
        
        core_metrics = {}
        for metric in ['LCP', 'FID', 'CLS', 'FCP', 'TTFB']:
            cursor = await db.execute("""
                SELECT AVG(value), rating
                FROM performance_metrics
                WHERE metric_name = ? AND timestamp >= datetime('now', '-1 day')
                GROUP BY rating
            """, (metric,))
            
            metric_rows = await cursor.fetchall()
            core_metrics[metric] = {
                rating: round(avg, 2) for avg, rating in metric_rows
            }
        
        return {
            "unique_sessions_24h": row[0],
            "total_metrics_24h": row[1],
            "last_report": row[2],
            "core_metrics": core_metrics,
        }
