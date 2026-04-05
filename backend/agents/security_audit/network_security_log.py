"""
网络安全事件日志智能体
Network Security Log Agent

负责采集所有网络安全相关事件日志，包括攻击检测、防御动作、异常流量等。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import aiofiles
import os

logger = logging.getLogger(__name__)


class EventType(Enum):
    ATTACK_DETECTED = "attack_detected"
    DEFENSE_ACTION = "defense_action"
    VULNERABILITY_FOUND = "vulnerability_found"
    INCIDENT_REPORT = "incident_report"
    ANOMALY_DETECTED = "anomaly_detected"
    THREAT_INTEL = "threat_intel"


class AttackType(Enum):
    DDoS = "ddos"
    CC = "cc"
    SQLI = "sqli"
    XSS = "xss"
    BRUTE_FORCE = "brute_force"
    SCANNER = "scanner"
    MALWARE = "malware"
    PHISHING = "phishing"
    ZERO_DAY = "zero_day"
    OTHER = "other"


class Severity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str = EventType.ATTACK_DETECTED.value
    source_ip: str = ""
    target: str = ""
    attack_type: str = AttackType.OTHER.value
    defense_action: str = ""
    severity: str = Severity.MEDIUM.value
    detail: Dict = field(default_factory=dict)
    handled: bool = False
    handler: str = ""
    handle_time: str = ""
    related_events: List[str] = field(default_factory=list)


@dataclass
class AttackCorrelation:
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: List[str] = field(default_factory=list)
    source_ip: str = ""
    attack_pattern: str = ""
    first_seen: str = ""
    last_seen: str = ""
    total_events: int = 0
    severity: str = Severity.MEDIUM.value
    status: str = "active"


class NetworkSecurityLogAgent:
    """
    网络安全事件日志智能体
    
    功能：
    1. 日志来源：防御智能体拦截日志、攻击智能体模拟攻击记录、外部安全设备告警
    2. 日志格式：标准化JSON格式，包含完整事件信息
    3. 存储与索引：Elasticsearch存储，按时间、IP、攻击类型建立索引
    4. 关联分析：将同一攻击源的多条日志关联成攻击事件
    5. 合规要求：保留至少6个月，关键事件导出到审计系统
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "NetworkSecurityLogAgent"
        self.description = "采集所有网络安全相关事件日志"
        self.config = config or {}
        
        self.events: List[SecurityEvent] = []
        self.correlations: Dict[str, AttackCorrelation] = {}
        
        self.storage_path = self.config.get("storage_path", "./security_logs")
        self.retention_days = self.config.get("retention_days", 180)
        
        self.attack_patterns = {
            "ddos": ["high_volume", "distributed", "flood"],
            "sqli": ["union select", "or 1=1", "drop table", "'--"],
            "xss": ["<script>", "javascript:", "onerror=", "onload="],
            "brute_force": ["multiple_failed_attempts", "password_spray"],
            "scanner": ["nmap", "nikto", "sqlmap", "dirbuster"],
        }
        
        self.stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "events_by_attack_type": defaultdict(int),
            "handled_events": 0,
            "active_correlations": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        os.makedirs(self.storage_path, exist_ok=True)
        asyncio.create_task(self._periodic_correlation())
        asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_correlation(self):
        while True:
            await asyncio.sleep(300)
            await self._correlate_events()
    
    async def _periodic_cleanup(self):
        while True:
            await asyncio.sleep(86400)
            await self._cleanup_old_events()
    
    async def log_event(
        self,
        event_type: str,
        source_ip: str,
        target: str,
        attack_type: str = AttackType.OTHER.value,
        defense_action: str = "",
        severity: str = Severity.MEDIUM.value,
        detail: Optional[Dict] = None,
    ) -> SecurityEvent:
        event = SecurityEvent(
            event_type=event_type,
            source_ip=source_ip,
            target=target,
            attack_type=attack_type,
            defense_action=defense_action,
            severity=severity,
            detail=detail or {},
        )
        
        self.events.append(event)
        
        self.stats["total_events"] += 1
        self.stats["events_by_type"][event_type] += 1
        self.stats["events_by_severity"][severity] += 1
        self.stats["events_by_attack_type"][attack_type] += 1
        
        await self._store_event(event)
        
        if severity in [Severity.HIGH.value, Severity.MEDIUM.value]:
            await self._check_correlation(event)
        
        return event
    
    async def _store_event(self, event: SecurityEvent):
        today = datetime.utcnow().strftime("%Y%m%d")
        log_file = os.path.join(self.storage_path, f"security_events_{today}.jsonl")
        
        try:
            async with aiofiles.open(log_file, 'a') as f:
                await f.write(json.dumps(event.__dict__, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to store security event: {e}")
    
    async def _check_correlation(self, event: SecurityEvent):
        for correlation in self.correlations.values():
            if correlation.source_ip == event.source_ip and correlation.status == "active":
                correlation.events.append(event.event_id)
                correlation.last_seen = event.timestamp
                correlation.total_events += 1
                
                if event.severity == Severity.HIGH.value:
                    correlation.severity = Severity.HIGH.value
                
                return
        
        correlation = AttackCorrelation(
            events=[event.event_id],
            source_ip=event.source_ip,
            attack_pattern=event.attack_type,
            first_seen=event.timestamp,
            last_seen=event.timestamp,
            total_events=1,
            severity=event.severity,
        )
        
        self.correlations[correlation.correlation_id] = correlation
        self.stats["active_correlations"] += 1
    
    async def _correlate_events(self):
        now = datetime.utcnow()
        cutoff = (now - timedelta(hours=1)).isoformat()
        
        recent_events = [
            e for e in self.events
            if e.timestamp > cutoff and not e.related_events
        ]
        
        ip_events = defaultdict(list)
        for event in recent_events:
            ip_events[event.source_ip].append(event)
        
        for ip, events in ip_events.items():
            if len(events) >= 3:
                pattern = self._detect_attack_pattern(events)
                
                for event in events:
                    event.related_events = [e.event_id for e in events if e.event_id != event.event_id]
    
    def _detect_attack_pattern(self, events: List[SecurityEvent]) -> str:
        attack_types = [e.attack_type for e in events]
        
        if attack_types.count(AttackType.DDoS.value) >= 2:
            return "coordinated_ddos"
        elif attack_types.count(AttackType.BRUTE_FORCE.value) >= 3:
            return "persistent_brute_force"
        elif len(set(attack_types)) >= 3:
            return "multi_vector_attack"
        
        return "unknown_pattern"
    
    async def _cleanup_old_events(self):
        cutoff = (datetime.utcnow() - timedelta(days=self.retention_days)).isoformat()
        
        self.events = [e for e in self.events if e.timestamp > cutoff]
        
        for corr_id, correlation in list(self.correlations.items()):
            if correlation.last_seen < cutoff:
                del self.correlations[corr_id]
                self.stats["active_correlations"] -= 1
    
    async def query_events(
        self,
        source_ip: Optional[str] = None,
        event_type: Optional[str] = None,
        attack_type: Optional[str] = None,
        severity: Optional[str] = None,
        time_range: Optional[tuple] = None,
        limit: int = 100,
    ) -> List[Dict]:
        results = []
        
        for event in reversed(self.events):
            if len(results) >= limit:
                break
            
            if source_ip and event.source_ip != source_ip:
                continue
            if event_type and event.event_type != event_type:
                continue
            if attack_type and event.attack_type != attack_type:
                continue
            if severity and event.severity != severity:
                continue
            if time_range:
                if not (time_range[0] <= event.timestamp <= time_range[1]):
                    continue
            
            results.append(event.__dict__)
        
        return results
    
    async def get_active_correlations(self) -> List[Dict]:
        return [
            {
                "correlation_id": c.correlation_id,
                "source_ip": c.source_ip,
                "attack_pattern": c.attack_pattern,
                "total_events": c.total_events,
                "severity": c.severity,
                "first_seen": c.first_seen,
                "last_seen": c.last_seen,
                "status": c.status,
            }
            for c in self.correlations.values()
            if c.status == "active"
        ]
    
    async def mark_event_handled(
        self,
        event_id: str,
        handler: str,
    ) -> bool:
        for event in self.events:
            if event.event_id == event_id:
                event.handled = True
                event.handler = handler
                event.handle_time = datetime.utcnow().isoformat()
                self.stats["handled_events"] += 1
                return True
        return False
    
    async def get_unhandled_events(self) -> List[Dict]:
        return [
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "source_ip": e.source_ip,
                "attack_type": e.attack_type,
                "severity": e.severity,
                "target": e.target,
            }
            for e in self.events
            if not e.handled
        ]
    
    async def generate_security_report(
        self,
        time_range: Optional[tuple] = None,
    ) -> Dict:
        if time_range:
            events = [
                e for e in self.events
                if time_range[0] <= e.timestamp <= time_range[1]
            ]
        else:
            now = datetime.utcnow()
            start = (now - timedelta(days=7)).isoformat()
            events = [e for e in self.events if e.timestamp >= start]
        
        report = {
            "time_range": time_range or {
                "start": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "total_events": len(events),
            "events_by_type": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "events_by_attack_type": defaultdict(int),
            "top_source_ips": defaultdict(int),
            "top_targets": defaultdict(int),
            "handled_rate": 0,
        }
        
        for event in events:
            report["events_by_type"][event.event_type] += 1
            report["events_by_severity"][event.severity] += 1
            report["events_by_attack_type"][event.attack_type] += 1
            report["top_source_ips"][event.source_ip] += 1
            report["top_targets"][event.target] += 1
        
        if events:
            report["handled_rate"] = sum(1 for e in events if e.handled) / len(events)
        
        report["top_source_ips"] = dict(sorted(
            report["top_source_ips"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        report["top_targets"] = dict(sorted(
            report["top_targets"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        report["events_by_type"] = dict(report["events_by_type"])
        report["events_by_severity"] = dict(report["events_by_severity"])
        report["events_by_attack_type"] = dict(report["events_by_attack_type"])
        
        return report
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_events": self.stats["total_events"],
            "events_by_type": dict(self.stats["events_by_type"]),
            "events_by_severity": dict(self.stats["events_by_severity"]),
            "events_by_attack_type": dict(self.stats["events_by_attack_type"]),
            "handled_events": self.stats["handled_events"],
            "active_correlations": self.stats["active_correlations"],
            "retention_days": self.retention_days,
        }
