"""
报表API路由
Report API Router

提供实时数据报表和历史数据查询功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    report_type: str = "defense"
    granularity: str = "hourly"


class DateRangeRequest(BaseModel):
    start_date: datetime
    end_date: datetime


class ReportFilter(BaseModel):
    report_type: str = "defense"
    granularity: str = "hourly"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("/defense/summary")
async def get_defense_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取防御性能摘要"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT 
                        stat_date,
                        total_attacks, blocked_attacks, missed_attacks
                        false_positives, normal_requests
                        service_down_events
                        FROM defense_stats_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date DESC
                """, start_date, end_date)
                
                summary = {
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "total_attacks": sum(r["total_attacks"] or 0 for r in rows),
                    "blocked_attacks": sum(r["blocked_attacks"] or 0 for r in rows),
                    "missed_attacks": sum(r["missed_attacks"] or 0 for r in rows),
                    "false_positives": sum(r["false_positives"] or 0 for r in rows),
                    "normal_requests": sum(r["normal_requests"] or 0 for r in rows),
                    "service_down_events": sum(r["service_down_events"] or 0 for r in rows),
                    "block_rate": sum(r["blocked_attacks"] or 0) / max(sum(r["total_attacks"] or 1), 1) for r in rows],
                    "miss_rate": sum(r["missed_attacks"] or 0) / max(sum(r["total_attacks"] or 1), 1) for r in rows],
                    "false_positive_rate": sum(r["false_positives"] or 0) / max(sum(r["normal_requests"] or 1), 1) for r in rows],
                    "service_availability": 1 - (sum(r["service_down_events"] or 0) / max(sum(r["normal_requests"] or 1) + sum(r["total_attacks"] or 0), 1) for r in rows]
                }
                
                return summary
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defense/trends")
async def get_defense_trends(
    days: int = Query(7, ge=1, le=30)
):
    """获取防御趋势数据"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                rows = await conn.fetch("""
                    SELECT stat_date, total_attacks, blocked_attacks
                    FROM defense_stats_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date
                """, start_date, end_date)
                
                trends = []
                for r in rows:
                    trends.append({
                        "date": r["stat_date"].isoformat(),
                        "total_attacks": r["total_attacks"],
                        "blocked_attacks": r["blocked_attacks"],
                        "block_rate": r["blocked_attacks"] / max(r["total_attacks"], 1) if r["total_attacks"] > 0 else 0
                    })
                
                return {"trends": trends}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attack/distribution")
async def get_attack_distribution(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取攻击类型分布"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT attack_type, attack_counts
                    FROM attack_type_distribution
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date
                """, start_date, end_date)
                
                distribution = {}
                for r in rows:
                    attack_type = r["attack_type"]
                    distribution[attack_type] = {
                        "attack_type": attack_type,
                        "count": r["attack_counts"],
                        "percentage": r["attack_counts"] / total if total > 0 else 0
                    }
                
                total = sum(r["attack_counts"] for r in rows)
                for attack_type in distribution:
                    distribution[attack_type]["percentage"] = total
                
                return {"distribution": distribution,            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/response-time/stats")
async def get_response_time_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取响应时间统计"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT 
                        stat_date, avg_response_time_ms, p50_response_time_ms,
                        p95_response_time_ms, p99_response_time_ms, max_response_time_ms
                    FROM response_time_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date DESC
                """, start_date, end_date)
                
                stats = []
                for r in rows:
                    stats.append({
                        "date": r["stat_date"].isoformat(),
                        "avg_ms": r["avg_response_time_ms"],
                        "p50_ms": r["p50_response_time_ms"],
                        "p95_ms": r["p95_response_time_ms"],
                        "p99_ms": r["p99_response_time_ms"],
                        "max_ms": r["max_response_time_ms"]
                    })
                
                return {"stats": stats}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service/availability")
async def get_service_availability(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取服务可用性统计"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT 
                        stat_date, availability_rate, downtime_seconds, incident_count
                    FROM service_availability_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date DESC
                """, start_date, end_date)
                
                availability = []
                for r in rows:
                    availability.append({
                        "date": r["stat_date"].isoformat(),
                        "availability_rate": r["availability_rate"],
                        "downtime_seconds": r["downtime_seconds"],
                        "incident_count": r["incident_count"]
                    })
                
                return {"availability": availability}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/progress")
async def get_training_progress(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取训练进度"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT 
                        stat_date, total_episodes, best_win_rate, avg_reward, model_version
                    FROM training_progress_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date DESC
                """, start_date, end_date)
                
                progress = []
                for r in rows:
                    progress.append({
                        "date": r["stat_date"].isoformat(),
                        "total_episodes": r["total_episodes"],
                        "win_rate": r["best_win_rate"],
                        "avg_reward": r["avg_reward"],
                        "model_version": r["model_version"]
                    })
                
                return {"progress": progress}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resource/usage")
async def get_resource_usage(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取资源使用统计"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT 
                        stat_date, avg_cpu_percent, avg_memory_percent,
                        disk_usage_percent, network_in_mbps, network_out_mbps
                    FROM resource_usage_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date DESC
                """, start_date, end_date)
                
                usage = []
                for r in rows:
                    usage.append({
                        "date": r["stat_date"].isoformat(),
                        "cpu_percent": r["avg_cpu_percent"],
                        "memory_percent": r["avg_memory_percent"],
                        "disk_percent": r["disk_usage_percent"],
                        "network_in_mbps": r["network_in_mbps"],
                        "network_out_mbps": r["network_out_mbps"]
                    })
                
                return {"usage": usage}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/performance")
async def get_model_performance(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取模型性能统计"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=7)
                if end_date is None:
                    end_date = datetime.now()
                
                rows = await conn.fetch("""
                    SELECT 
                        stat_date, model_version, tpr, fpr, avg_latency_ms
                    FROM model_performance_daily
                    WHERE stat_date BETWEEN $1 AND $2
                    ORDER BY stat_date DESC
                """, start_date, end_date)
                
                performance = []
                for r in rows:
                    performance.append({
                        "date": r["stat_date"].isoformat(),
                        "version": r["model_version"],
                        "tpr": r["tpr"],
                        "fpr": r["fpr"],
                        "avg_latency_ms": r["avg_latency_ms"]
                    })
                
                return {"performance": performance}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data():
    """获取仪表盘汇总数据"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                today = datetime.now().date()
                
                defense_row = await conn.fetchrow("""
                    SELECT * FROM defense_stats_daily 
                    WHERE stat_date = $1
                """, today)
                
                attack_rows = await conn.fetch("""
                    SELECT * FROM attack_trend_daily 
                    WHERE stat_date = $1
                """, today)
                
                response_row = await conn.fetchrow("""
                    SELECT * FROM response_time_daily 
                    WHERE stat_date = $1
                """, today)
                
                availability_row = await conn.fetchrow("""
                    SELECT * FROM service_availability_daily 
                    WHERE stat_date = $1
                """, today)
                
                training_row = await conn.fetchrow("""
                    SELECT * FROM training_progress_daily 
                    WHERE stat_date = $1
                """, today)
                
                resource_row = await conn.fetchrow("""
                    SELECT * FROM resource_usage_daily 
                    WHERE stat_date = $1
                """, today)
                
                model_row = await conn.fetchrow("""
                    SELECT * FROM model_performance_daily 
                    WHERE stat_date = $1
                """, today)
                
                return {
                    "defense": dict(defense_row[0]) if defense_row else None,
                    "attack_distribution": dict(attack_row[0]) if attack_rows else None,
                    "response_time": dict(response_row[0]) if response_row else None,
                    "availability": dict(availability_row[0]) if availability_row else None,
                    "training": dict(training_row[0]) if training_row else None,
                    "resource": dict(resource_row[0]) if resource_row else None,
                    "model": dict(model_row[0]) if model_row else None,
                    "timestamp": datetime.now().isoformat()
                }
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime")
async def get_realtime_stats():
    """获取实时统计"""
    try:
        from ..database import get_db_connection
        from ..agents.selfplay import advanced_kernel
        
        async for conn in get_db_connection():
            try:
                recent_episodes = await conn.fetch("""
                    SELECT * FROM selfplay_episodes 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                
                hourly_stats = await conn.fetchrow("""
                    SELECT * FROM defense_stats_hourly_summary
                    WHERE stat_hour = date_trunc('hour', CURRENT_TIMESTAMP)
                """)
                
                kernel_status = advanced_kernel.get_status()
                
                return {
                    "recent_episodes": [dict(e) for e in recent_episodes],
                    "hourly_stats": dict(hourly_stats) if hourly_stats else None,
                    "kernel_status": kernel_status,
                    "timestamp": datetime.now().isoformat()
                }
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts():
    """获取活跃告警"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                alerts = await conn.fetch("""
                    SELECT * FROM system_alerts 
                    WHERE is_resolved = FALSE 
                    ORDER BY created_at DESC 
                    LIMIT 20
                """)
                
                return {
                    "alerts": [dict(a) for a in alerts],
                    "total": len(alerts)
                }
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """解决告警"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    UPDATE system_alerts 
                    SET is_resolved = TRUE, resolved_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, alert_id)
                
                return {"success": True, "alert_id": alert_id}
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_report(request: ReportRequest):
    """导出报表"""
    try:
        from ..database import get_db_connection
        import csv
        import io
        
        async for conn in get_db_connection():
            try:
                output = io.StringIO()
                writer = csv.writer(output)
                
                if request.report_type == "defense":
                    rows = await conn.fetch("""
                        SELECT * FROM defense_stats_daily
                        WHERE stat_date BETWEEN $1 AND $2
                        ORDER BY stat_date
                    """, request.start_date or datetime.now() - timedelta(days=7), 
                        request.end_date or datetime.now())
                    
                    writer.writerow([
                        "日期", "总攻击数", "已拦截", "漏拦截", "误判数",
                        "正常请求", "服务宕机", "拦截率"
                    ])
                    
                    for row in rows:
                        writer.writerow([
                            row["stat_date"], row["total_attacks"], row["blocked_attacks"],
                            row["missed_attacks"], row["false_positives"], row["normal_requests"],
                            row["service_down_events"], row["blocked_attacks"] / max(row["total_attacks"], 1)
                        ])
                
                return {
                    "success": True,
                    "data": output.getvalue(),
                    "filename": f"defense_report_{datetime.now().strftime('%Y%m%d')}.csv"
                }
            finally:
                await conn.close()
                break
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "report-api"
    }
