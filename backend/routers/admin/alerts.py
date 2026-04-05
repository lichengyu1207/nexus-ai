"""
管理员异常告警API
提供告警管理、规则配置功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from ...auth import require_admin, require_super_admin
from ...database import get_db_connection
from ...exceptions import NotFoundException, BadRequestException, ErrorCode
from ...services.anomaly_detector import anomaly_detector, AlertStatus, AlertSeverity

router = APIRouter(prefix="/api/admin/alerts", tags=["admin-alerts"])


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    rule_name: str
    matched_count: int
    time_window_start: str
    time_window_end: str
    status: str
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    resolution_note: Optional[str]
    created_at: str


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    open_count: int
    critical_count: int


class RuleResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    severity: str
    enabled: bool
    config: Dict[str, Any]
    cooldown_minutes: int
    notify_admins: bool
    last_triggered_at: Optional[str]
    trigger_count: int


class RuleUpdate(BaseModel):
    enabled: Optional[bool] = None
    severity: Optional[str] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0, le=1440)
    notify_admins: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class AcknowledgeRequest(BaseModel):
    note: Optional[str] = None


class ResolveRequest(BaseModel):
    note: str


class AlertStatsResponse(BaseModel):
    total_alerts: int
    open_alerts: int
    acknowledged_alerts: int
    resolved_alerts: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    recent_trend: List[Dict[str, Any]]


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin),
):
    """获取告警列表"""
    conn = await get_db_connection()
    try:
        conditions = []
        params = []
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if alert_type:
            conditions.append("alert_type = ?")
            params.append(alert_type)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        cursor = await conn.execute(f"""
            SELECT * FROM anomaly_alerts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        alerts = await cursor.fetchall()
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as count FROM anomaly_alerts {where_clause}",
            params
        )
        total = (await count_cursor.fetchone())["count"]
        
        stats_cursor = await conn.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_count,
                COUNT(CASE WHEN severity = 'critical' AND status = 'open' THEN 1 END) as critical_count
            FROM anomaly_alerts
        """)
        stats = await stats_cursor.fetchone()
        
        return AlertListResponse(
            alerts=[
                AlertResponse(
                    id=a["id"],
                    alert_type=a["alert_type"],
                    severity=a["severity"],
                    title=a["title"],
                    description=a.get("description"),
                    user_id=a.get("user_id"),
                    username=a.get("username"),
                    ip_address=a.get("ip_address"),
                    rule_name=a["rule_name"],
                    matched_count=a["matched_count"],
                    time_window_start=a["time_window_start"],
                    time_window_end=a["time_window_end"],
                    status=a["status"],
                    acknowledged_by=a.get("acknowledged_by"),
                    acknowledged_at=a.get("acknowledged_at"),
                    resolved_by=a.get("resolved_by"),
                    resolved_at=a.get("resolved_at"),
                    resolution_note=a.get("resolution_note"),
                    created_at=a["created_at"],
                )
                for a in alerts
            ],
            total=total,
            open_count=stats["open_count"],
            critical_count=stats["critical_count"],
        )
    finally:
        await conn.close()


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    days: int = Query(7, ge=1, le=30),
    admin: dict = Depends(require_admin),
):
    """获取告警统计"""
    from datetime import timezone, timedelta
    
    conn = await get_db_connection()
    try:
        now = datetime.now(timezone.utc)
        since = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days-1)
        
        cursor = await conn.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_alerts,
                COUNT(CASE WHEN status = 'acknowledged' THEN 1 END) as acknowledged_alerts,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_alerts
            FROM anomaly_alerts
            WHERE created_at >= ?
        """, (since.isoformat(),))
        
        stats = await cursor.fetchone()
        
        severity_cursor = await conn.execute("""
            SELECT severity, COUNT(*) as count
            FROM anomaly_alerts
            WHERE created_at >= ?
            GROUP BY severity
        """, (since.isoformat(),))
        
        by_severity = {row["severity"]: row["count"] for row in await severity_cursor.fetchall()}
        
        type_cursor = await conn.execute("""
            SELECT alert_type, COUNT(*) as count
            FROM anomaly_alerts
            WHERE created_at >= ?
            GROUP BY alert_type
        """, (since.isoformat(),))
        
        by_type = {row["alert_type"]: row["count"] for row in await type_cursor.fetchall()}
        
        trend_cursor = await conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM anomaly_alerts
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (since.isoformat(),))
        
        recent_trend = [dict(row) for row in await trend_cursor.fetchall()]
        
        return AlertStatsResponse(
            total_alerts=stats["total_alerts"] or 0,
            open_alerts=stats["open_alerts"] or 0,
            acknowledged_alerts=stats["acknowledged_alerts"] or 0,
            resolved_alerts=stats["resolved_alerts"] or 0,
            by_severity=by_severity,
            by_type=by_type,
            recent_trend=recent_trend,
        )
    finally:
        await conn.close()


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_detail(
    alert_id: str,
    admin: dict = Depends(require_admin),
):
    """获取告警详情"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM anomaly_alerts WHERE id = ?",
            (alert_id,)
        )
        alert = await cursor.fetchone()
        
        if not alert:
            raise NotFoundException("告警不存在", ErrorCode.NOT_FOUND)
        
        a = dict(alert)
        return AlertResponse(
            id=a["id"],
            alert_type=a["alert_type"],
            severity=a["severity"],
            title=a["title"],
            description=a.get("description"),
            user_id=a.get("user_id"),
            username=a.get("username"),
            ip_address=a.get("ip_address"),
            rule_name=a["rule_name"],
            matched_count=a["matched_count"],
            time_window_start=a["time_window_start"],
            time_window_end=a["time_window_end"],
            status=a["status"],
            acknowledged_by=a.get("acknowledged_by"),
            acknowledged_at=a.get("acknowledged_at"),
            resolved_by=a.get("resolved_by"),
            resolved_at=a.get("resolved_at"),
            resolution_note=a.get("resolution_note"),
            created_at=a["created_at"],
        )
    finally:
        await conn.close()


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeRequest,
    admin: dict = Depends(require_admin),
):
    """确认告警"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM anomaly_alerts WHERE id = ?",
            (alert_id,)
        )
        alert = await cursor.fetchone()
        
        if not alert:
            raise NotFoundException("告警不存在", ErrorCode.NOT_FOUND)
        
        if alert["status"] != AlertStatus.OPEN.value:
            raise BadRequestException("只能确认未处理的告警", ErrorCode.INVALID_STATE)
        
        await conn.execute("""
            UPDATE anomaly_alerts SET
                status = 'acknowledged',
                acknowledged_by = ?,
                acknowledged_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (admin["id"], alert_id))
        await conn.commit()
        
        return {"message": "告警已确认", "alert_id": alert_id}
    finally:
        await conn.close()


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: ResolveRequest,
    admin: dict = Depends(require_admin),
):
    """解决告警"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM anomaly_alerts WHERE id = ?",
            (alert_id,)
        )
        alert = await cursor.fetchone()
        
        if not alert:
            raise NotFoundException("告警不存在", ErrorCode.NOT_FOUND)
        
        if alert["status"] == AlertStatus.RESOLVED.value:
            raise BadRequestException("告警已解决", ErrorCode.INVALID_STATE)
        
        await conn.execute("""
            UPDATE anomaly_alerts SET
                status = 'resolved',
                resolved_by = ?,
                resolved_at = CURRENT_TIMESTAMP,
                resolution_note = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (admin["id"], request.note, alert_id))
        await conn.commit()
        
        return {"message": "告警已解决", "alert_id": alert_id}
    finally:
        await conn.close()


@router.post("/{alert_id}/false-positive")
async def mark_false_positive(
    alert_id: str,
    request: AcknowledgeRequest,
    admin: dict = Depends(require_admin),
):
    """标记为误报"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM anomaly_alerts WHERE id = ?",
            (alert_id,)
        )
        alert = await cursor.fetchone()
        
        if not alert:
            raise NotFoundException("告警不存在", ErrorCode.NOT_FOUND)
        
        await conn.execute("""
            UPDATE anomaly_alerts SET
                status = 'false_positive',
                resolved_by = ?,
                resolved_at = CURRENT_TIMESTAMP,
                resolution_note = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (admin["id"], request.note or "标记为误报", alert_id))
        await conn.commit()
        
        return {"message": "已标记为误报", "alert_id": alert_id}
    finally:
        await conn.close()


@router.get("/rules/list")
async def list_rules(
    admin: dict = Depends(require_admin),
):
    """获取检测规则列表"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM anomaly_rules ORDER BY category, severity DESC"
        )
        rules = await cursor.fetchall()
        
        return {
            "rules": [
                RuleResponse(
                    id=r["id"],
                    name=r["name"],
                    display_name=r["display_name"],
                    description=r.get("description"),
                    category=r["category"],
                    severity=r["severity"],
                    enabled=bool(r["enabled"]),
                    config=json.loads(r["config"]) if r["config"] else {},
                    cooldown_minutes=r["cooldown_minutes"],
                    notify_admins=bool(r["notify_admins"]),
                    last_triggered_at=r.get("last_triggered_at"),
                    trigger_count=r["trigger_count"],
                )
                for r in rules
            ]
        }
    finally:
        await conn.close()


@router.get("/rules")
async def list_rules_alias(
    admin: dict = Depends(require_admin),
):
    """获取检测规则列表（别名）"""
    return await list_rules(admin)


@router.put("/rules/{rule_name}")
async def update_rule(
    rule_name: str,
    update_data: RuleUpdate,
    admin: dict = Depends(require_super_admin),
):
    """更新检测规则（仅超级管理员）"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM anomaly_rules WHERE name = ?",
            (rule_name,)
        )
        rule = await cursor.fetchone()
        
        if not rule:
            raise NotFoundException("规则不存在", ErrorCode.NOT_FOUND)
        
        updates = []
        params = []
        
        if update_data.enabled is not None:
            updates.append("enabled = ?")
            params.append(update_data.enabled)
        if update_data.severity is not None:
            updates.append("severity = ?")
            params.append(update_data.severity)
        if update_data.cooldown_minutes is not None:
            updates.append("cooldown_minutes = ?")
            params.append(update_data.cooldown_minutes)
        if update_data.notify_admins is not None:
            updates.append("notify_admins = ?")
            params.append(update_data.notify_admins)
        if update_data.config is not None:
            updates.append("config = ?")
            params.append(json.dumps(update_data.config))
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(rule_name)
            
            await conn.execute(
                f"UPDATE anomaly_rules SET {', '.join(updates)} WHERE name = ?",
                params
            )
            await conn.commit()
        
        return {"message": "规则已更新", "rule_name": rule_name}
    finally:
        await conn.close()


@router.post("/run-detection")
async def run_detection_now(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(require_super_admin),
):
    """立即执行异常检测（仅超级管理员）"""
    result = await anomaly_detector.run_detection_now()
    return result


@router.post("/bulk-acknowledge")
async def bulk_acknowledge(
    alert_ids: List[str],
    admin: dict = Depends(require_admin),
):
    """批量确认告警"""
    conn = await get_db_connection()
    try:
        placeholders = ",".join("?" * len(alert_ids))
        await conn.execute(f"""
            UPDATE anomaly_alerts SET
                status = 'acknowledged',
                acknowledged_by = ?,
                acknowledged_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders}) AND status = 'open'
        """, [admin["id"]] + alert_ids)
        await conn.commit()
        
        return {"message": f"已确认 {len(alert_ids)} 条告警"}
    finally:
        await conn.close()
