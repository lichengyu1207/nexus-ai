"""
异常行为检测服务
基于审计日志实时检测可疑行为并生成告警
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from ..database import get_db_connection

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AlertCategory(str, Enum):
    SECURITY = "security"
    DATA_LOSS = "data_loss"
    DATA_EXFILTRATION = "data_exfiltration"
    SUSPICIOUS = "suspicious"
    ACCOUNT_COMPROMISE = "account_compromise"


@dataclass
class AnomalyRule:
    id: str
    name: str
    display_name: str
    description: str
    category: str
    severity: str
    enabled: bool
    config: Dict[str, Any]
    cooldown_minutes: int
    notify_admins: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int


@dataclass
class Alert:
    id: str
    alert_type: str
    severity: str
    title: str
    description: str
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    rule_name: str
    matched_count: int
    time_window_start: datetime
    time_window_end: datetime
    status: str
    created_at: datetime


class AnomalyDetector:
    def __init__(self):
        self._rules: Dict[str, AnomalyRule] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 60
    
    async def load_rules(self):
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM anomaly_rules WHERE enabled = 1"
            )
            rows = await cursor.fetchall()
            
            self._rules = {}
            for row in rows:
                self._rules[row["name"]] = AnomalyRule(
                    id=row["id"],
                    name=row["name"],
                    display_name=row["display_name"],
                    description=row["description"],
                    category=row["category"],
                    severity=row["severity"],
                    enabled=bool(row["enabled"]),
                    config=json.loads(row["config"]) if row["config"] else {},
                    cooldown_minutes=row["cooldown_minutes"],
                    notify_admins=bool(row["notify_admins"]),
                    last_triggered_at=datetime.fromisoformat(row["last_triggered_at"]) if row["last_triggered_at"] else None,
                    trigger_count=row["trigger_count"],
                )
            
            logger.info(f"Loaded {len(self._rules)} anomaly detection rules")
        except Exception as e:
            logger.warning(f"Could not load anomaly rules: {e}")
            self._rules = {}
        finally:
            await conn.close()
    
    async def start(self):
        if self._running:
            return
        
        await self.load_rules()
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Anomaly detector started")
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Anomaly detector stopped")
    
    async def _run_loop(self):
        while self._running:
            try:
                await self._check_all_rules()
            except Exception as e:
                logger.error(f"Anomaly detection error: {e}")
            
            await asyncio.sleep(self._check_interval)
    
    async def _check_all_rules(self):
        for rule_name, rule in self._rules.items():
            try:
                if rule.last_triggered_at:
                    cooldown = timedelta(minutes=rule.cooldown_minutes)
                    if datetime.utcnow() - rule.last_triggered_at < cooldown:
                        continue
                
                alerts = await self._check_rule(rule)
                
                if alerts:
                    for alert in alerts:
                        await self._create_alert(alert, rule)
                    
                    await self._update_rule_triggered(rule.name)
                    
            except Exception as e:
                logger.error(f"Error checking rule {rule_name}: {e}")
    
    async def _check_rule(self, rule: AnomalyRule) -> List[Alert]:
        config = rule.config
        alerts = []
        
        if rule.name == "brute_force_login":
            alerts = await self._check_brute_force(rule, config)
        elif rule.name == "bulk_delete":
            alerts = await self._check_bulk_delete(rule, config)
        elif rule.name == "unusual_time_access":
            alerts = await self._check_unusual_time(rule, config)
        elif rule.name == "permission_escalation":
            alerts = await self._check_permission_escalation(rule, config)
        elif rule.name == "mass_export":
            alerts = await self._check_mass_export(rule, config)
        elif rule.name == "multiple_ip_login":
            alerts = await self._check_multiple_ip_login(rule, config)
        elif rule.name == "failed_permission_access":
            alerts = await self._check_failed_permission(rule, config)
        elif rule.name == "suspicious_api_pattern":
            alerts = await self._check_suspicious_api(rule, config)
        else:
            alerts = await self._check_generic_rule(rule, config)
        
        return alerts
    
    async def _check_brute_force(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        time_window = config.get("time_window_minutes", 5)
        threshold = config.get("threshold", 5)
        group_by = config.get("group_by", "ip_address")
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=time_window)
            
            cursor = await conn.execute(f"""
                SELECT {group_by}, COUNT(*) as count,
                       GROUP_CONCAT(id) as log_ids,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE action_type = 'LOGIN'
                  AND status = 'failure'
                  AND timestamp >= ?
                  AND {group_by} IS NOT NULL
                GROUP BY {group_by}
                HAVING count >= ?
            """, (since.isoformat(), threshold))
            
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="brute_force_login",
                    severity=rule.severity,
                    title=f"检测到暴力破解登录尝试",
                    description=f"IP {row[group_by]} 在 {time_window} 分钟内登录失败 {row['count']} 次",
                    user_id=None,
                    username=None,
                    ip_address=row[group_by],
                    rule_name=rule.name,
                    matched_count=row["count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_bulk_delete(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        time_window = config.get("time_window_minutes", 10)
        threshold = config.get("threshold", 10)
        group_by = config.get("group_by", "user_id")
        action_types = config.get("action_type", "TASK_DELETE").split(",")
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=time_window)
            placeholders = ",".join("?" * len(action_types))
            
            cursor = await conn.execute(f"""
                SELECT {group_by}, username, COUNT(*) as count,
                       GROUP_CONCAT(id) as log_ids,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE action_type IN ({placeholders})
                  AND status = 'success'
                  AND timestamp >= ?
                  AND {group_by} IS NOT NULL
                GROUP BY {group_by}
                HAVING count >= ?
            """, action_types + [since.isoformat(), threshold])
            
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="bulk_delete",
                    severity=rule.severity,
                    title=f"检测到批量删除操作",
                    description=f"用户 {row.get('username') or row[group_by]} 在 {time_window} 分钟内执行了 {row['count']} 次删除操作",
                    user_id=row[group_by],
                    username=row.get("username"),
                    ip_address=None,
                    rule_name=rule.name,
                    matched_count=row["count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_unusual_time(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        start_hour = config.get("start_hour", 0)
        end_hour = config.get("end_hour", 6)
        threshold = config.get("threshold", 20)
        time_window = config.get("time_window_minutes", 60)
        
        now = datetime.utcnow()
        current_hour = now.hour
        
        if not (start_hour <= current_hour < end_hour):
            return []
        
        conn = await get_db_connection()
        try:
            since = now - timedelta(minutes=time_window)
            
            cursor = await conn.execute("""
                SELECT user_id, username, COUNT(*) as count,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE timestamp >= ?
                  AND user_id IS NOT NULL
                GROUP BY user_id
                HAVING count >= ?
            """, (since.isoformat(), threshold))
            
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="unusual_time_access",
                    severity=rule.severity,
                    title=f"检测到非常规时间大量操作",
                    description=f"用户 {row.get('username') or row['user_id']} 在凌晨 {current_hour}:00 左右的 {time_window} 分钟内执行了 {row['count']} 次操作",
                    user_id=row["user_id"],
                    username=row.get("username"),
                    ip_address=None,
                    rule_name=rule.name,
                    matched_count=row["count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_permission_escalation(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        action_types = config.get("action_types", [])
        check_role = config.get("check_role", True)
        
        if isinstance(action_types, str):
            action_types = json.loads(action_types)
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=5)
            placeholders = ",".join("?" * len(action_types))
            
            query = f"""
                SELECT al.id, al.user_id, al.username, al.action_type,
                       al.ip_address, al.timestamp, u.role
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE al.action_type IN ({placeholders})
                  AND al.timestamp >= ?
            """
            
            cursor = await conn.execute(query, action_types + [since.isoformat()])
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                if check_role and row.get("role") in ("admin", "super_admin"):
                    continue
                
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="permission_escalation",
                    severity=rule.severity,
                    title=f"检测到权限提升尝试",
                    description=f"用户 {row.get('username') or row['user_id']} 尝试执行特权操作: {row['action_type']}",
                    user_id=row["user_id"],
                    username=row.get("username"),
                    ip_address=row.get("ip_address"),
                    rule_name=rule.name,
                    matched_count=1,
                    time_window_start=datetime.fromisoformat(row["timestamp"]),
                    time_window_end=datetime.fromisoformat(row["timestamp"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_mass_export(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        time_window = config.get("time_window_minutes", 30)
        threshold = config.get("threshold", 20)
        group_by = config.get("group_by", "user_id")
        action_types = config.get("action_type", "REPORT_EXPORT").split(",")
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=time_window)
            placeholders = ",".join("?" * len(action_types))
            
            cursor = await conn.execute(f"""
                SELECT {group_by}, username, COUNT(*) as count,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE action_type IN ({placeholders})
                  AND status = 'success'
                  AND timestamp >= ?
                  AND {group_by} IS NOT NULL
                GROUP BY {group_by}
                HAVING count >= ?
            """, action_types + [since.isoformat(), threshold])
            
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="mass_export",
                    severity=rule.severity,
                    title=f"检测到批量数据导出",
                    description=f"用户 {row.get('username') or row[group_by]} 在 {time_window} 分钟内导出了 {row['count']} 次数据",
                    user_id=row[group_by],
                    username=row.get("username"),
                    ip_address=None,
                    rule_name=rule.name,
                    matched_count=row["count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_multiple_ip_login(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        time_window = config.get("time_window_minutes", 30)
        ip_threshold = config.get("ip_threshold", 3)
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=time_window)
            
            cursor = await conn.execute("""
                SELECT user_id, username, COUNT(DISTINCT ip_address) as ip_count,
                       GROUP_CONCAT(DISTINCT ip_address) as ips,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE action_type = 'LOGIN'
                  AND status = 'success'
                  AND timestamp >= ?
                  AND user_id IS NOT NULL
                  AND ip_address IS NOT NULL
                GROUP BY user_id
                HAVING ip_count >= ?
            """, (since.isoformat(), ip_threshold))
            
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="multiple_ip_login",
                    severity=rule.severity,
                    title=f"检测到多IP登录",
                    description=f"用户 {row.get('username') or row['user_id']} 在 {time_window} 分钟内从 {row['ip_count']} 个不同IP登录: {row['ips']}",
                    user_id=row["user_id"],
                    username=row.get("username"),
                    ip_address=row["ips"],
                    rule_name=rule.name,
                    matched_count=row["ip_count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_failed_permission(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        time_window = config.get("time_window_minutes", 10)
        threshold = config.get("threshold", 10)
        group_by = config.get("group_by", "user_id")
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=time_window)
            
            cursor = await conn.execute(f"""
                SELECT {group_by}, username, COUNT(*) as count,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE status = 'failure'
                  AND timestamp >= ?
                  AND {group_by} IS NOT NULL
                GROUP BY {group_by}
                HAVING count >= ?
            """, (since.isoformat(), threshold))
            
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type="failed_permission_access",
                    severity=rule.severity,
                    title=f"检测到频繁权限访问失败",
                    description=f"用户 {row.get('username') or row[group_by]} 在 {time_window} 分钟内有 {row['count']} 次操作失败",
                    user_id=row[group_by],
                    username=row.get("username"),
                    ip_address=None,
                    rule_name=rule.name,
                    matched_count=row["count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _check_suspicious_api(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        return []
    
    async def _check_generic_rule(self, rule: AnomalyRule, config: Dict) -> List[Alert]:
        action_type = config.get("action_type")
        time_window = config.get("time_window_minutes", 5)
        threshold = config.get("threshold", 10)
        group_by = config.get("group_by", "user_id")
        status_filter = config.get("status")
        
        if not action_type:
            return []
        
        conn = await get_db_connection()
        try:
            since = datetime.utcnow() - timedelta(minutes=time_window)
            
            action_types = action_type.split(",")
            placeholders = ",".join("?" * len(action_types))
            
            query = f"""
                SELECT {group_by}, username, ip_address, COUNT(*) as count,
                       MIN(timestamp) as first_attempt,
                       MAX(timestamp) as last_attempt
                FROM audit_logs
                WHERE action_type IN ({placeholders})
                  AND timestamp >= ?
            """
            params = action_types + [since.isoformat()]
            
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
            
            query += f" AND {group_by} IS NOT NULL GROUP BY {group_by} HAVING count >= ?"
            params.append(threshold)
            
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    alert_type=rule.name,
                    severity=rule.severity,
                    title=f"触发规则: {rule.display_name}",
                    description=f"检测到异常行为: {rule.description}",
                    user_id=row.get(group_by),
                    username=row.get("username"),
                    ip_address=row.get("ip_address"),
                    rule_name=rule.name,
                    matched_count=row["count"],
                    time_window_start=datetime.fromisoformat(row["first_attempt"]),
                    time_window_end=datetime.fromisoformat(row["last_attempt"]),
                    status=AlertStatus.OPEN.value,
                    created_at=datetime.utcnow(),
                ))
            
            return alerts
        finally:
            await conn.close()
    
    async def _create_alert(self, alert: Alert, rule: AnomalyRule):
        conn = await get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO anomaly_alerts
                (id, alert_type, severity, title, description,
                 user_id, username, ip_address, rule_name,
                 matched_count, time_window_start, time_window_end, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.alert_type,
                alert.severity,
                alert.title,
                alert.description,
                alert.user_id,
                alert.username,
                alert.ip_address,
                alert.rule_name,
                alert.matched_count,
                alert.time_window_start.isoformat(),
                alert.time_window_end.isoformat(),
                alert.status,
            ))
            await conn.commit()
            
            logger.warning(f"Created anomaly alert: {alert.title}")
            
            if rule.notify_admins:
                await self._notify_admins(alert)
                
        finally:
            await conn.close()
    
    async def _notify_admins(self, alert: Alert):
        try:
            conn = await get_db_connection()
            cursor = await conn.execute("""
                SELECT id FROM users WHERE is_admin = 1 OR role IN ('admin', 'super_admin')
            """)
            admins = await cursor.fetchall()
            await conn.close()
            
            for admin in admins:
                await self._create_notification(admin["id"], alert)
                
        except Exception as e:
            logger.error(f"Failed to notify admins: {e}")
    
    async def _create_notification(self, user_id: str, alert: Alert):
        conn = await get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO notifications (id, user_id, type, title, content, data)
                VALUES (?, ?, 'anomaly_alert', ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                user_id,
                alert.title,
                alert.description,
                json.dumps({
                    "alert_id": alert.id,
                    "severity": alert.severity,
                    "alert_type": alert.alert_type,
                })
            ))
            await conn.commit()
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
        finally:
            await conn.close()
    
    async def _update_rule_triggered(self, rule_name: str):
        conn = await get_db_connection()
        try:
            await conn.execute("""
                UPDATE anomaly_rules SET
                    last_triggered_at = CURRENT_TIMESTAMP,
                    trigger_count = trigger_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (rule_name,))
            await conn.commit()
        finally:
            await conn.close()
    
    async def run_detection_now(self) -> Dict[str, Any]:
        result = {
            "started_at": datetime.utcnow().isoformat(),
            "alerts_created": 0,
            "rules_checked": len(self._rules),
        }
        
        await self.load_rules()
        
        for rule_name, rule in self._rules.items():
            try:
                alerts = await self._check_rule(rule)
                if alerts:
                    for alert in alerts:
                        await self._create_alert(alert, rule)
                    result["alerts_created"] += len(alerts)
                    await self._update_rule_triggered(rule.name)
            except Exception as e:
                logger.error(f"Error checking rule {rule_name}: {e}")
        
        result["completed_at"] = datetime.utcnow().isoformat()
        return result


anomaly_detector = AnomalyDetector()


async def setup_anomaly_detector():
    await anomaly_detector.start()


async def shutdown_anomaly_detector():
    await anomaly_detector.stop()
