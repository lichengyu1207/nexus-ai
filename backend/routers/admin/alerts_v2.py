"""
告警管理API
处理告警记录和通知
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import httpx

from ...database import get_db_connection
from ...auth import require_admin, require_super_admin
from ...logger import get_logger

logger = get_logger("alerts_api")

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class Alert(BaseModel):
    id: int
    name: str
    severity: str
    status: str
    message: str
    labels: dict
    starts_at: datetime
    ends_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[int]


class AlertCreate(BaseModel):
    name: str
    severity: str
    message: str
    labels: dict = {}


class AlertAcknowledge(BaseModel):
    note: Optional[str] = None


class NotificationConfig(BaseModel):
    type: str
    enabled: bool
    config: dict


DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK_URL")
EMAIL_SMTP = os.getenv("SMTP_SERVER")


@router.post("/webhook")
async def receive_alertmanager_webhook(alerts: dict):
    """接收Alertmanager的告警webhook"""
    logger.info(f"Received alertmanager webhook: {alerts}")
    
    async with get_db_connection() as db:
        for alert in alerts.get("alerts", []):
            await db.execute("""
                INSERT INTO alert_history (
                    name, severity, status, message, labels,
                    starts_at, ends_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.get("labels", {}).get("alertname", "unknown"),
                alert.get("labels", {}).get("severity", "warning"),
                alert.get("status", "firing"),
                alert.get("annotations", {}).get("summary", ""),
                str(alert.get("labels", {})),
                alert.get("startsAt"),
                alert.get("endsAt"),
                datetime.now(),
            ))
        await db.commit()
    
    return {"status": "ok", "count": len(alerts.get("alerts", []))}


@router.get("/history")
async def get_alert_history(
    days: int = Query(7, ge=1, le=30),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_admin),
):
    """获取告警历史"""
    async with get_db_connection() as db:
        where_clauses = ["created_at >= datetime('now', ?)"]
        params = [f"-{days} days"]
        
        if severity:
            where_clauses.append("severity = ?")
            params.append(severity)
        
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(where_clauses)
        
        cursor = await db.execute(f"""
            SELECT COUNT(*) FROM alert_history WHERE {where_clause}
        """, params)
        total = (await cursor.fetchone())[0]
        
        cursor = await db.execute(f"""
            SELECT id, name, severity, status, message, labels,
                   starts_at, ends_at, acknowledged_at, acknowledged_by,
                   created_at
            FROM alert_history
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        rows = await cursor.fetchall()
        
        alerts = [
            {
                "id": row[0],
                "name": row[1],
                "severity": row[2],
                "status": row[3],
                "message": row[4],
                "labels": eval(row[5]) if row[5] else {},
                "starts_at": row[6],
                "ends_at": row[7],
                "acknowledged_at": row[8],
                "acknowledged_by": row[9],
                "created_at": row[10],
            }
            for row in rows
        ]
        
        return {"alerts": alerts, "total": total}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledge,
    current_user = Depends(require_admin),
):
    """确认告警"""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            UPDATE alert_history
            SET acknowledged_at = ?, acknowledged_by = ?, status = 'acknowledged'
            WHERE id = ? AND acknowledged_at IS NULL
        """, (datetime.now(), current_user.id, alert_id))
        
        await db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
        
        return {"status": "acknowledged", "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user = Depends(require_admin),
):
    """解决告警"""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            UPDATE alert_history
            SET status = 'resolved', ends_at = ?
            WHERE id = ? AND status != 'resolved'
        """, (datetime.now(), alert_id))
        
        await db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
        
        return {"status": "resolved", "alert_id": alert_id}


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=30),
    current_user = Depends(require_admin),
):
    """获取告警统计"""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT 
                severity,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'firing' THEN 1 ELSE 0 END) as firing,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN acknowledged_at IS NOT NULL THEN 1 ELSE 0 END) as acknowledged
            FROM alert_history
            WHERE created_at >= datetime('now', ?)
            GROUP BY severity
        """, (f"-{days} days",))
        
        by_severity = {}
        for row in await cursor.fetchall():
            by_severity[row[0]] = {
                "total": row[1],
                "firing": row[2],
                "resolved": row[3],
                "acknowledged": row[4],
            }
        
        cursor = await db.execute("""
            SELECT name, COUNT(*) as count
            FROM alert_history
            WHERE created_at >= datetime('now', ?)
            GROUP BY name
            ORDER BY count DESC
            LIMIT 10
        """, (f"-{days} days",))
        
        top_alerts = [{"name": row[0], "count": row[1]} for row in await cursor.fetchall()]
        
        return {
            "by_severity": by_severity,
            "top_alerts": top_alerts,
        }


@router.post("/test/dingtalk")
async def test_dingtalk_notification(
    current_user = Depends(require_super_admin),
):
    """测试钉钉通知"""
    if not DINGTALK_WEBHOOK:
        raise HTTPException(status_code=400, detail="DingTalk webhook not configured")
    
    message = {
        "msgtype": "text",
        "text": {
            "content": f"【房都督AI】测试告警\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n这是一条测试消息"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(DINGTALK_WEBHOOK, json=message)
            return {"status": "ok", "response": response.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/email")
async def test_email_notification(
    email: str,
    current_user = Depends(require_super_admin),
):
    """测试邮件通知"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not all([smtp_server, smtp_user, smtp_password]):
        raise HTTPException(status_code=400, detail="Email not configured")
    
    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email
        msg["Subject"] = "【房都督AI】测试告警邮件"
        
        body = f"""
        房都督AI 告警测试邮件
        
        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        这是一封测试邮件，用于验证邮件通知配置是否正确。
        """
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return {"status": "ok", "message": f"Test email sent to {email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_notification_config(
    current_user = Depends(require_super_admin),
):
    """获取通知配置"""
    return {
        "dingtalk": {
            "enabled": bool(DINGTALK_WEBHOOK),
            "webhook_configured": bool(DINGTALK_WEBHOOK),
        },
        "email": {
            "enabled": bool(EMAIL_SMTP),
            "smtp_server": EMAIL_SMTP,
        },
    }


async def init_alert_tables():
    """初始化告警表"""
    async with get_db_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT DEFAULT 'firing',
                message TEXT,
                labels TEXT,
                starts_at DATETIME,
                ends_at DATETIME,
                acknowledged_at DATETIME,
                acknowledged_by INTEGER,
                note TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_history_created
            ON alert_history(created_at)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_history_severity
            ON alert_history(severity)
        """)
        
        await db.commit()
