"""
会话审计日志智能体
记录所有用户会话和智能体交互的审计日志
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuditLogType(str, Enum):
    USER_SESSION = "user_session"
    AGENT_INTERACTION = "agent_interaction"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"


class AuditLogStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    BLOCKED = "blocked"


class AuditLog(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid4()))
    log_type: AuditLogType
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    action: str
    resource: Optional[str] = None
    resource_type: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    status: AuditLogStatus = AuditLogStatus.SUCCESS
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    previous_hash: Optional[str] = None
    current_hash: str = ""
    chain_index: int = 0


class SessionContext(BaseModel):
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    actions_count: int = 0
    risk_score: float = 0.0


class AuditQuery(BaseModel):
    log_types: Optional[List[AuditLogType]] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AuditLogStatus] = None
    limit: int = 100
    offset: int = 0


class AuditLogStorage:
    def __init__(self, db_pool: Optional[Any] = None):
        self.db_pool = db_pool
        self.logs: List[AuditLog] = []
        self.log_index: Dict[str, AuditLog] = {}
        self.session_contexts: Dict[str, SessionContext] = {}
        self.max_memory_logs = 10000
    
    async def store(self, log: AuditLog) -> str:
        self.logs.append(log)
        self.log_index[log.log_id] = log
        
        if len(self.logs) > self.max_memory_logs:
            removed = self.logs[:-self.max_memory_logs]
            for removed_log in removed:
                if removed_log.log_id in self.log_index:
                    del self.log_index[removed_log.log_id]
            self.logs = self.logs[-self.max_memory_logs:]
        
        return log.log_id
    
    async def query(self, query: AuditQuery) -> List[AuditLog]:
        results = []
        
        for log in reversed(self.logs):
            if query.log_types and log.log_type not in query.log_types:
                continue
            
            if query.user_id and log.user_id != query.user_id:
                continue
            
            if query.agent_id and log.agent_id != query.agent_id:
                continue
            
            if query.session_id and log.session_id != query.session_id:
                continue
            
            if query.start_time and log.timestamp < query.start_time:
                continue
            
            if query.end_time and log.timestamp > query.end_time:
                continue
            
            if query.status and log.status != query.status:
                continue
            
            results.append(log)
        
        return results[query.offset:query.offset + query.limit]
    
    async def get_by_id(self, log_id: str) -> Optional[AuditLog]:
        return self.log_index.get(log_id)
    
    async def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        return self.session_contexts.get(session_id)
    
    async def update_session_context(
        self,
        session_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = SessionContext(
                session_id=session_id,
                user_id=user_id,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent
            )
        else:
            ctx = self.session_contexts[session_id]
            ctx.last_activity = datetime.now()
            ctx.actions_count += 1


class SessionAuditAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "SessionAudit",
        db_pool: Optional[Any] = None,
        integrity_agent: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.db_pool = db_pool
        self.integrity_agent = integrity_agent
        
        self.storage = AuditLogStorage(db_pool)
        
        self.last_hash: Optional[str] = None
        self.chain_index: int = 0
        
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"SessionAuditAgent {self.agent_id} initialized")
    
    async def log_user_session(
        self,
        user_id: str,
        session_id: str,
        action: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: AuditLogStatus = AuditLogStatus.SUCCESS
    ) -> str:
        await self.storage.update_session_context(
            session_id, user_id, ip_address, user_agent
        )
        
        log = AuditLog(
            log_type=AuditLogType.USER_SESSION,
            user_id=user_id,
            session_id=session_id,
            action=action,
            details=self._sanitize_details(details),
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=self.last_hash,
            chain_index=self.chain_index
        )
        
        log.current_hash = self._compute_hash(log)
        
        log_id = await self.storage.store(log)
        
        self.last_hash = log.current_hash
        self.chain_index += 1
        
        return log_id
    
    async def log_agent_interaction(
        self,
        agent_id: str,
        session_id: Optional[str],
        action: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        status: AuditLogStatus = AuditLogStatus.SUCCESS
    ) -> str:
        log = AuditLog(
            log_type=AuditLogType.AGENT_INTERACTION,
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            action=action,
            details=self._sanitize_details(details),
            status=status,
            previous_hash=self.last_hash,
            chain_index=self.chain_index
        )
        
        log.current_hash = self._compute_hash(log)
        
        log_id = await self.storage.store(log)
        
        self.last_hash = log.current_hash
        self.chain_index += 1
        
        return log_id
    
    async def log_data_access(
        self,
        user_id: str,
        resource: str,
        resource_type: str,
        action: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None,
        status: AuditLogStatus = AuditLogStatus.SUCCESS
    ) -> str:
        log = AuditLog(
            log_type=AuditLogType.DATA_ACCESS,
            user_id=user_id,
            session_id=session_id,
            action=action,
            resource=resource,
            resource_type=resource_type,
            details=self._sanitize_details(details),
            status=status,
            previous_hash=self.last_hash,
            chain_index=self.chain_index
        )
        
        log.current_hash = self._compute_hash(log)
        
        log_id = await self.storage.store(log)
        
        self.last_hash = log.current_hash
        self.chain_index += 1
        
        return log_id
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        log = AuditLog(
            log_type=AuditLogType.SECURITY_EVENT,
            user_id=user_id,
            session_id=session_id,
            action=event_type,
            details={
                **self._sanitize_details(details),
                "severity": severity
            },
            status=AuditLogStatus.FAILURE if severity in ["high", "critical"] else AuditLogStatus.SUCCESS,
            ip_address=ip_address,
            previous_hash=self.last_hash,
            chain_index=self.chain_index
        )
        
        log.current_hash = self._compute_hash(log)
        
        log_id = await self.storage.store(log)
        
        self.last_hash = log.current_hash
        self.chain_index += 1
        
        if severity in ["high", "critical"]:
            self.logger.warning(f"Security event logged: {event_type}")
        
        return log_id
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        
        sensitive_keys = [
            "password", "token", "secret", "key", "credential",
            "api_key", "access_token", "refresh_token"
        ]
        
        for key, value in details.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "...[truncated]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _compute_hash(self, log: AuditLog) -> str:
        data = {
            "log_id": log.log_id,
            "log_type": log.log_type.value,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "session_id": log.session_id,
            "action": log.action,
            "status": log.status.value,
            "previous_hash": log.previous_hash
        }
        
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def query_logs(self, query: AuditQuery) -> List[Dict[str, Any]]:
        logs = await self.storage.query(query)
        
        return [log.dict() for log in logs]
    
    async def get_session_timeline(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        query = AuditQuery(
            session_id=session_id,
            limit=1000
        )
        
        logs = await self.storage.query(query)
        
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "type": log.log_type.value,
                "action": log.action,
                "status": log.status.value,
                "details": log.details
            }
            for log in sorted(logs, key=lambda x: x.timestamp)
        ]
    
    async def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        start_time = datetime.now() - timedelta(days=days)
        
        query = AuditQuery(
            user_id=user_id,
            start_time=start_time,
            limit=10000
        )
        
        logs = await self.storage.query(query)
        
        by_type = {}
        by_status = {}
        by_day = {}
        
        for log in logs:
            log_type = log.log_type.value
            by_type[log_type] = by_type.get(log_type, 0) + 1
            
            status = log.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            day = log.timestamp.date().isoformat()
            by_day[day] = by_day.get(day, 0) + 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            "by_type": by_type,
            "by_status": by_status,
            "by_day": by_day
        }
    
    async def verify_chain_integrity(self) -> Dict[str, Any]:
        if not self.integrity_agent:
            return {"verified": False, "reason": "No integrity agent configured"}
        
        logs = self.storage.logs
        
        for i in range(1, len(logs)):
            if logs[i].previous_hash != logs[i-1].current_hash:
                return {
                    "verified": False,
                    "reason": f"Chain broken at index {i}",
                    "expected": logs[i-1].current_hash,
                    "actual": logs[i].previous_hash
                }
        
        return {
            "verified": True,
            "chain_length": len(logs),
            "last_hash": self.last_hash
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        by_type = {}
        for log in self.storage.logs:
            log_type = log.log_type.value
            by_type[log_type] = by_type.get(log_type, 0) + 1
        
        by_status = {}
        for log in self.storage.logs:
            status = log.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_logs": len(self.storage.logs),
            "chain_index": self.chain_index,
            "active_sessions": len(self.storage.session_contexts),
            "logs_by_type": by_type,
            "logs_by_status": by_status
        }
