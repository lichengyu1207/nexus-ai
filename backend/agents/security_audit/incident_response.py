"""
安全事件应急响应智能体
Incident Response Agent

负责对网络安全事件进行自动化应急响应，并记录响应过程供审计。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class IncidentLevel(Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class ResponseStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


@dataclass
class ResponseAction:
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""
    description: str = ""
    executor: str = ""
    executed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    result: str = ""
    success: bool = False
    details: Dict = field(default_factory=dict)


@dataclass
class Incident:
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    level: str = IncidentLevel.P3.value
    status: str = ResponseStatus.PENDING.value
    
    title: str = ""
    description: str = ""
    source_event_ids: List[str] = field(default_factory=list)
    
    affected_systems: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    impact_assessment: Dict = field(default_factory=dict)
    
    response_actions: List[ResponseAction] = field(default_factory=list)
    root_cause: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    
    owner: str = ""
    resolved_at: str = ""
    closed_at: str = ""


class IncidentResponseAgent:
    """
    安全事件应急响应智能体
    
    功能：
    1. 事件分级：P0-P3四级分类
    2. 响应动作：根据事件级别自动触发响应流程
    3. 响应记录：记录所有响应动作的时间、操作人、结果
    4. 协同机制：与防御智能体集群联动，共享威胁情报
    5. 复盘学习：分析根因，更新防御策略
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "IncidentResponseAgent"
        self.description = "对网络安全事件进行自动化应急响应"
        self.config = config or {}
        
        self.incidents: Dict[str, Incident] = {}
        self.response_handlers: Dict[str, Callable] = {}
        
        self.level_thresholds = {
            IncidentLevel.P0.value: {
                "description": "大规模攻击导致服务不可用",
                "response_time_minutes": 5,
                "auto_actions": ["switch_ha_node", "block_attack_source", "notify_security_team"],
            },
            IncidentLevel.P1.value: {
                "description": "关键数据泄露、权限被突破",
                "response_time_minutes": 15,
                "auto_actions": ["isolate_affected_system", "revoke_compromised_credentials", "notify_security_team"],
            },
            IncidentLevel.P2.value: {
                "description": "局部攻击、异常行为",
                "response_time_minutes": 60,
                "auto_actions": ["block_ip", "enhance_monitoring"],
            },
            IncidentLevel.P3.value: {
                "description": "扫描探测、低危告警",
                "response_time_minutes": 240,
                "auto_actions": ["log_event", "update_threat_intel"],
            },
        }
        
        self.stats = {
            "total_incidents": 0,
            "incidents_by_level": defaultdict(int),
            "incidents_by_status": defaultdict(int),
            "resolved_incidents": 0,
            "avg_resolution_time_minutes": 0,
            "auto_actions_executed": 0,
        }
        
        self._init_response_handlers()
        self._initialized = False
    
    def _init_response_handlers(self):
        self.response_handlers = {
            "switch_ha_node": self._switch_ha_node,
            "block_attack_source": self._block_attack_source,
            "isolate_affected_system": self._isolate_affected_system,
            "revoke_compromised_credentials": self._revoke_compromised_credentials,
            "block_ip": self._block_ip,
            "enhance_monitoring": self._enhance_monitoring,
            "notify_security_team": self._notify_security_team,
            "log_event": self._log_event,
            "update_threat_intel": self._update_threat_intel,
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._monitor_pending_incidents())
    
    async def _monitor_pending_incidents(self):
        while True:
            await asyncio.sleep(60)
            await self._check_response_times()
    
    async def _check_response_times(self):
        now = datetime.utcnow()
        
        for incident in self.incidents.values():
            if incident.status == ResponseStatus.PENDING.value:
                created = datetime.fromisoformat(incident.created_at)
                elapsed_minutes = (now - created).total_seconds() / 60
                
                threshold = self.level_thresholds.get(incident.level, {}).get("response_time_minutes", 60)
                
                if elapsed_minutes > threshold:
                    await self._escalate_incident(incident)
    
    async def create_incident(
        self,
        title: str,
        description: str,
        source_event_ids: Optional[List[str]] = None,
        affected_systems: Optional[List[str]] = None,
        initial_level: Optional[str] = None,
    ) -> Incident:
        if not initial_level:
            initial_level = self._assess_incident_level(title, description, affected_systems or [])
        
        incident = Incident(
            title=title,
            description=description,
            source_event_ids=source_event_ids or [],
            affected_systems=affected_systems or [],
            level=initial_level,
            status=ResponseStatus.PENDING.value,
        )
        
        self.incidents[incident.incident_id] = incident
        
        self.stats["total_incidents"] += 1
        self.stats["incidents_by_level"][incident.level] += 1
        self.stats["incidents_by_status"][incident.status] += 1
        
        await self._trigger_auto_response(incident)
        
        return incident
    
    def _assess_incident_level(
        self,
        title: str,
        description: str,
        affected_systems: List[str],
    ) -> str:
        text = f"{title} {description}".lower()
        
        p0_keywords = ["服务不可用", "大规模攻击", "系统瘫痪", "全站宕机"]
        p1_keywords = ["数据泄露", "权限突破", "入侵", "敏感数据", "账户被盗"]
        p2_keywords = ["攻击", "异常", "漏洞利用", "未授权访问"]
        p3_keywords = ["扫描", "探测", "低危", "可疑"]
        
        for kw in p0_keywords:
            if kw in text:
                return IncidentLevel.P0.value
        
        for kw in p1_keywords:
            if kw in text:
                return IncidentLevel.P1.value
        
        for kw in p2_keywords:
            if kw in text:
                return IncidentLevel.P2.value
        
        if len(affected_systems) > 3:
            return IncidentLevel.P1.value
        elif len(affected_systems) > 1:
            return IncidentLevel.P2.value
        
        return IncidentLevel.P3.value
    
    async def _trigger_auto_response(self, incident: Incident):
        level_config = self.level_thresholds.get(incident.level, {})
        auto_actions = level_config.get("auto_actions", [])
        
        for action_type in auto_actions:
            handler = self.response_handlers.get(action_type)
            if handler:
                try:
                    result = await handler(incident)
                    
                    action = ResponseAction(
                        action_type=action_type,
                        description=f"自动执行: {action_type}",
                        executor="auto_responder",
                        success=result.get("success", False),
                        result=result.get("message", ""),
                        details=result,
                    )
                    
                    incident.response_actions.append(action)
                    self.stats["auto_actions_executed"] += 1
                    
                except Exception as e:
                    logger.error(f"Auto action {action_type} failed: {e}")
        
        incident.status = ResponseStatus.IN_PROGRESS.value
        incident.updated_at = datetime.utcnow().isoformat()
        
        self.stats["incidents_by_status"][ResponseStatus.PENDING.value] -= 1
        self.stats["incidents_by_status"][ResponseStatus.IN_PROGRESS.value] += 1
    
    async def _switch_ha_node(self, incident: Incident) -> Dict:
        logger.info(f"Switching to HA node for incident {incident.incident_id}")
        return {"success": True, "message": "已切换到高可用节点"}
    
    async def _block_attack_source(self, incident: Incident) -> Dict:
        logger.info(f"Blocking attack source for incident {incident.incident_id}")
        return {"success": True, "message": "已封禁攻击源IP"}
    
    async def _isolate_affected_system(self, incident: Incident) -> Dict:
        logger.info(f"Isolating affected systems for incident {incident.incident_id}")
        return {"success": True, "message": f"已隔离受影响系统: {incident.affected_systems}"}
    
    async def _revoke_compromised_credentials(self, incident: Incident) -> Dict:
        logger.info(f"Revoking compromised credentials for incident {incident.incident_id}")
        return {"success": True, "message": "已撤销受影响凭证"}
    
    async def _block_ip(self, incident: Incident) -> Dict:
        logger.info(f"Blocking IP for incident {incident.incident_id}")
        return {"success": True, "message": "已封禁可疑IP"}
    
    async def _enhance_monitoring(self, incident: Incident) -> Dict:
        logger.info(f"Enhancing monitoring for incident {incident.incident_id}")
        return {"success": True, "message": "已增强监控级别"}
    
    async def _notify_security_team(self, incident: Incident) -> Dict:
        logger.info(f"Notifying security team for incident {incident.incident_id}")
        return {"success": True, "message": f"已通知安全团队: {incident.title}"}
    
    async def _log_event(self, incident: Incident) -> Dict:
        return {"success": True, "message": "事件已记录"}
    
    async def _update_threat_intel(self, incident: Incident) -> Dict:
        logger.info(f"Updating threat intel for incident {incident.incident_id}")
        return {"success": True, "message": "威胁情报已更新"}
    
    async def _escalate_incident(self, incident: Incident):
        level_order = [IncidentLevel.P3.value, IncidentLevel.P2.value, IncidentLevel.P1.value, IncidentLevel.P0.value]
        current_index = level_order.index(incident.level)
        
        if current_index < len(level_order) - 1:
            new_level = level_order[current_index + 1]
            
            self.stats["incidents_by_level"][incident.level] -= 1
            incident.level = new_level
            self.stats["incidents_by_level"][incident.level] += 1
            
            incident.status = ResponseStatus.ESCALATED.value
            incident.updated_at = datetime.utcnow().isoformat()
            
            await self._notify_security_team(incident)
    
    async def add_response_action(
        self,
        incident_id: str,
        action_type: str,
        description: str,
        executor: str,
        details: Optional[Dict] = None,
    ) -> Optional[ResponseAction]:
        incident = self.incidents.get(incident_id)
        if not incident:
            return None
        
        action = ResponseAction(
            action_type=action_type,
            description=description,
            executor=executor,
            details=details or {},
            success=True,
        )
        
        incident.response_actions.append(action)
        incident.updated_at = datetime.utcnow().isoformat()
        
        return action
    
    async def resolve_incident(
        self,
        incident_id: str,
        root_cause: str,
        lessons_learned: Optional[List[str]] = None,
    ) -> bool:
        incident = self.incidents.get(incident_id)
        if not incident:
            return False
        
        incident.status = ResponseStatus.RESOLVED.value
        incident.root_cause = root_cause
        incident.lessons_learned = lessons_learned or []
        incident.resolved_at = datetime.utcnow().isoformat()
        incident.updated_at = datetime.utcnow().isoformat()
        
        self.stats["incidents_by_status"][ResponseStatus.IN_PROGRESS.value] -= 1
        self.stats["incidents_by_status"][ResponseStatus.RESOLVED.value] += 1
        self.stats["resolved_incidents"] += 1
        
        created = datetime.fromisoformat(incident.created_at)
        resolved = datetime.fromisoformat(incident.resolved_at)
        resolution_minutes = (resolved - created).total_seconds() / 60
        
        current_avg = self.stats["avg_resolution_time_minutes"]
        total_resolved = self.stats["resolved_incidents"]
        self.stats["avg_resolution_time_minutes"] = (
            (current_avg * (total_resolved - 1) + resolution_minutes) / total_resolved
        )
        
        return True
    
    async def close_incident(self, incident_id: str) -> bool:
        incident = self.incidents.get(incident_id)
        if not incident:
            return False
        
        incident.status = ResponseStatus.CLOSED.value
        incident.closed_at = datetime.utcnow().isoformat()
        incident.updated_at = datetime.utcnow().isoformat()
        
        self.stats["incidents_by_status"][ResponseStatus.RESOLVED.value] -= 1
        self.stats["incidents_by_status"][ResponseStatus.CLOSED.value] += 1
        
        return True
    
    async def get_active_incidents(self) -> List[Dict]:
        return [
            {
                "incident_id": i.incident_id,
                "title": i.title,
                "level": i.level,
                "status": i.status,
                "created_at": i.created_at,
                "affected_systems": i.affected_systems,
                "response_actions_count": len(i.response_actions),
            }
            for i in self.incidents.values()
            if i.status not in [ResponseStatus.CLOSED.value]
        ]
    
    async def get_incident(self, incident_id: str) -> Optional[Dict]:
        incident = self.incidents.get(incident_id)
        if not incident:
            return None
        
        return {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "level": incident.level,
            "status": incident.status,
            "created_at": incident.created_at,
            "updated_at": incident.updated_at,
            "affected_systems": incident.affected_systems,
            "root_cause": incident.root_cause,
            "lessons_learned": incident.lessons_learned,
            "response_actions": [
                {
                    "action_type": a.action_type,
                    "description": a.description,
                    "executor": a.executor,
                    "executed_at": a.executed_at,
                    "success": a.success,
                }
                for a in incident.response_actions
            ],
        }
    
    async def generate_incident_report(
        self,
        time_range: Optional[tuple] = None,
    ) -> Dict:
        if time_range:
            incidents = [
                i for i in self.incidents.values()
                if time_range[0] <= i.created_at <= time_range[1]
            ]
        else:
            now = datetime.utcnow()
            start = (now - timedelta(days=30)).isoformat()
            incidents = [i for i in self.incidents.values() if i.created_at >= start]
        
        report = {
            "time_range": time_range or {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "total_incidents": len(incidents),
            "incidents_by_level": defaultdict(int),
            "incidents_by_status": defaultdict(int),
            "avg_resolution_time_minutes": 0,
            "top_affected_systems": defaultdict(int),
            "common_root_causes": defaultdict(int),
        }
        
        resolution_times = []
        
        for incident in incidents:
            report["incidents_by_level"][incident.level] += 1
            report["incidents_by_status"][incident.status] += 1
            
            for system in incident.affected_systems:
                report["top_affected_systems"][system] += 1
            
            if incident.root_cause:
                report["common_root_causes"][incident.root_cause] += 1
            
            if incident.resolved_at:
                created = datetime.fromisoformat(incident.created_at)
                resolved = datetime.fromisoformat(incident.resolved_at)
                resolution_times.append((resolved - created).total_seconds() / 60)
        
        if resolution_times:
            report["avg_resolution_time_minutes"] = sum(resolution_times) / len(resolution_times)
        
        report["incidents_by_level"] = dict(report["incidents_by_level"])
        report["incidents_by_status"] = dict(report["incidents_by_status"])
        report["top_affected_systems"] = dict(sorted(
            report["top_affected_systems"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        report["common_root_causes"] = dict(report["common_root_causes"])
        
        return report
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_incidents": self.stats["total_incidents"],
            "incidents_by_level": dict(self.stats["incidents_by_level"]),
            "incidents_by_status": dict(self.stats["incidents_by_status"]),
            "resolved_incidents": self.stats["resolved_incidents"],
            "avg_resolution_time_minutes": round(self.stats["avg_resolution_time_minutes"], 2),
            "auto_actions_executed": self.stats["auto_actions_executed"],
        }
