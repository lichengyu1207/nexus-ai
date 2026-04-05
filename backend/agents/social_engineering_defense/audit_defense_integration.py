"""
审计防御集成智能体
负责将防社会工程决策记录到审计日志系统
"""
import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """审计事件类型"""
    RISK_DETECTION = "risk_detection"
    DEFENSE_DECISION = "defense_decision"
    USER_REPORT = "user_report"
    SECURITY_ALERT = "security_alert"
    POLICY_VIOLATION = "policy_violation"
    ACCESS_DENIED = "access_denied"
    VERIFICATION_REQUIRED = "verification_required"
    ATTACK_BLOCKED = "attack_blocked"


class AuditSeverity(Enum):
    """审计严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditStatus(Enum):
    """审计状态"""
    RECORDED = "recorded"
    REVIEWED = "reviewed"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


@dataclass
class AuditEntry:
    """审计条目"""
    audit_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: str
    agent_id: str
    session_id: str
    description: str
    details: Dict[str, Any]
    risk_score: float
    timestamp: datetime
    status: AuditStatus
    checksum: str
    reviewed_by: Optional[str] = None
    review_notes: str = ""
    related_audits: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    """审计报告"""
    report_id: str
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    top_risks: List[Dict[str, Any]]
    compliance_status: Dict[str, Any]
    generated_at: datetime


class AuditDefenseIntegrationAgent:
    """审计防御集成智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AuditDefenseIntegrationAgent"
        self.config = config or {}
        self.audit_log: List[AuditEntry] = []
        self.audit_index: Dict[AuditEventType, List[str]] = defaultdict(list)
        self.user_audit_index: Dict[str, List[str]] = defaultdict(list)
        self.audit_counter = 0
        self.retention_days = 180
        self.stats = {
            "total_audits": 0,
            "audits_by_type": defaultdict(int),
            "audits_by_severity": defaultdict(int),
            "audits_reviewed": 0,
            "audits_escalated": 0,
            "reports_generated": 0,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def record_audit(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: str,
        agent_id: str,
        session_id: str,
        description: str,
        details: Dict[str, Any],
        risk_score: float = 0.0
    ) -> AuditEntry:
        """记录审计"""
        self.audit_counter += 1
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.audit_counter}"
        
        checksum = self._generate_checksum(
            event_type, user_id, agent_id, session_id, description, details
        )
        
        entry = AuditEntry(
            audit_id=audit_id,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            description=description,
            details=details,
            risk_score=risk_score,
            timestamp=datetime.now(),
            status=AuditStatus.RECORDED,
            checksum=checksum
        )
        
        self.audit_log.append(entry)
        self.audit_index[event_type].append(audit_id)
        self.user_audit_index[user_id].append(audit_id)
        
        self.stats["total_audits"] += 1
        self.stats["audits_by_type"][event_type.value] += 1
        self.stats["audits_by_severity"][severity.value] += 1
        
        return entry
    
    def _generate_checksum(
        self,
        event_type: AuditEventType,
        user_id: str,
        agent_id: str,
        session_id: str,
        description: str,
        details: Dict[str, Any]
    ) -> str:
        """生成校验和"""
        data = json.dumps({
            "event_type": event_type.value,
            "user_id": user_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }, sort_keys=True)
        
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def verify_integrity(self, audit_id: str) -> bool:
        """验证完整性"""
        entry = self._get_audit_by_id(audit_id)
        if not entry:
            return False
        
        expected_checksum = self._generate_checksum(
            entry.event_type,
            entry.user_id,
            entry.agent_id,
            entry.session_id,
            entry.description,
            entry.details
        )
        
        return entry.checksum == expected_checksum
    
    def _get_audit_by_id(self, audit_id: str) -> Optional[AuditEntry]:
        """根据ID获取审计"""
        for entry in self.audit_log:
            if entry.audit_id == audit_id:
                return entry
        return None
    
    def record_risk_detection(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
        risk_type: str,
        risk_score: float,
        detection_details: Dict[str, Any]
    ) -> AuditEntry:
        """记录风险检测"""
        severity = AuditSeverity.INFO
        if risk_score >= 0.8:
            severity = AuditSeverity.CRITICAL
        elif risk_score >= 0.6:
            severity = AuditSeverity.ERROR
        elif risk_score >= 0.4:
            severity = AuditSeverity.WARNING
        
        return self.record_audit(
            event_type=AuditEventType.RISK_DETECTION,
            severity=severity,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            description=f"检测到{risk_type}风险，风险分数: {risk_score:.2f}",
            details=detection_details,
            risk_score=risk_score
        )
    
    def record_defense_decision(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
        decision: str,
        reasoning: str,
        outcome: str
    ) -> AuditEntry:
        """记录防御决策"""
        severity = AuditSeverity.WARNING if decision == "block" else AuditSeverity.INFO
        
        return self.record_audit(
            event_type=AuditEventType.DEFENSE_DECISION,
            severity=severity,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            description=f"防御决策: {decision}，结果: {outcome}",
            details={
                "decision": decision,
                "reasoning": reasoning,
                "outcome": outcome
            }
        )
    
    def record_user_report(
        self,
        reporter_id: str,
        report_type: str,
        reported_user_id: str,
        description: str,
        report_details: Dict[str, Any]
    ) -> AuditEntry:
        """记录用户举报"""
        return self.record_audit(
            event_type=AuditEventType.USER_REPORT,
            severity=AuditSeverity.WARNING,
            user_id=reporter_id,
            agent_id="report_system",
            session_id="",
            description=f"用户举报: {report_type}",
            details={
                "report_type": report_type,
                "reported_user_id": reported_user_id,
                "description": description,
                **report_details
            }
        )
    
    def record_attack_blocked(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
        attack_type: str,
        attack_details: Dict[str, Any]
    ) -> AuditEntry:
        """记录攻击拦截"""
        return self.record_audit(
            event_type=AuditEventType.ATTACK_BLOCKED,
            severity=AuditSeverity.CRITICAL,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            description=f"成功拦截{attack_type}攻击",
            details=attack_details,
            risk_score=0.9
        )
    
    def review_audit(
        self,
        audit_id: str,
        reviewer_id: str,
        notes: str,
        escalate: bool = False
    ) -> bool:
        """审核审计"""
        entry = self._get_audit_by_id(audit_id)
        if not entry:
            return False
        
        entry.reviewed_by = reviewer_id
        entry.review_notes = notes
        
        if escalate:
            entry.status = AuditStatus.ESCALATED
            self.stats["audits_escalated"] += 1
        else:
            entry.status = AuditStatus.REVIEWED
        
        self.stats["audits_reviewed"] += 1
        
        return True
    
    def query_audits(
        self,
        event_type: AuditEventType = None,
        severity: AuditSeverity = None,
        user_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """查询审计"""
        results = list(self.audit_log)
        
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        
        if severity:
            results = [e for e in results if e.severity == severity]
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def generate_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> AuditReport:
        """生成报告"""
        audits = [
            a for a in self.audit_log
            if start_time <= a.timestamp <= end_time
        ]
        
        events_by_type: Dict[str, int] = defaultdict(int)
        events_by_severity: Dict[str, int] = defaultdict(int)
        
        for audit in audits:
            events_by_type[audit.event_type.value] += 1
            events_by_severity[audit.severity.value] += 1
        
        top_risks = sorted(
            [a for a in audits if a.risk_score > 0],
            key=lambda x: x.risk_score,
            reverse=True
        )[:10]
        
        top_risks_data = [
            {
                "audit_id": a.audit_id,
                "event_type": a.event_type.value,
                "risk_score": a.risk_score,
                "description": a.description,
                "timestamp": a.timestamp.isoformat()
            }
            for a in top_risks
        ]
        
        compliance_status = {
            "data_retention_compliant": True,
            "audit_trail_integrity": self._check_integrity(),
            "review_rate": self.stats["audits_reviewed"] / max(1, self.stats["total_audits"]),
        }
        
        self.stats["reports_generated"] += 1
        
        return AuditReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_start=start_time,
            period_end=end_time,
            total_events=len(audits),
            events_by_type=dict(events_by_type),
            events_by_severity=dict(events_by_severity),
            top_risks=top_risks_data,
            compliance_status=compliance_status,
            generated_at=datetime.now()
        )
    
    def _check_integrity(self) -> bool:
        """检查完整性"""
        sample_size = min(10, len(self.audit_log))
        if sample_size == 0:
            return True
        
        import random
        sample = random.sample(self.audit_log, sample_size)
        
        for entry in sample:
            if not self.verify_integrity(entry.audit_id):
                return False
        
        return True
    
    def cleanup_old_audits(self):
        """清理旧审计"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        self.audit_log = [
            a for a in self.audit_log
            if a.timestamp > cutoff
        ]
        
        for event_type in self.audit_index:
            self.audit_index[event_type] = [
                aid for aid in self.audit_index[event_type]
                if self._get_audit_by_id(aid) is not None
            ]
    
    def export_audits(
        self,
        start_time: datetime,
        end_time: datetime,
        format: str = "json"
    ) -> str:
        """导出审计"""
        audits = self.query_audits(start_time=start_time, end_time=end_time, limit=10000)
        
        if format == "json":
            return json.dumps([
                {
                    "audit_id": a.audit_id,
                    "event_type": a.event_type.value,
                    "severity": a.severity.value,
                    "user_id": a.user_id,
                    "agent_id": a.agent_id,
                    "session_id": a.session_id,
                    "description": a.description,
                    "details": a.details,
                    "risk_score": a.risk_score,
                    "timestamp": a.timestamp.isoformat(),
                    "status": a.status.value,
                    "checksum": a.checksum
                }
                for a in audits
            ], ensure_ascii=False, indent=2)
        
        return ""
    
    def get_user_audit_history(self, user_id: str, limit: int = 50) -> List[AuditEntry]:
        """获取用户审计历史"""
        audit_ids = self.user_audit_index.get(user_id, [])[-limit:]
        return [self._get_audit_by_id(aid) for aid in reversed(audit_ids) if self._get_audit_by_id(aid)]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            **self.stats,
            "audits_by_type": dict(self.stats["audits_by_type"]),
            "audits_by_severity": dict(self.stats["audits_by_severity"]),
            "audit_log_size": len(self.audit_log),
            "retention_days": self.retention_days,
        }
