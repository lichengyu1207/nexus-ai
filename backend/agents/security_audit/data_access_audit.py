"""
数据访问审计智能体
Data Access Audit Agent

专门审计业务智能体对用户数据的访问行为。
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

logger = logging.getLogger(__name__)


class DataAccessRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DataAccessRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: str = ""
    accessing_agent_id: str = ""
    data_type: str = ""
    fields: List[str] = field(default_factory=list)
    operation: str = ""
    purpose: str = ""
    authorized: bool = False
    consent_reference: str = ""
    risk_level: str = DataAccessRisk.LOW.value


@dataclass
class AccessAnomaly:
    anomaly_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    anomaly_type: str = ""
    description: str = ""
    affected_user_id: str = ""
    accessing_agent_id: str = ""
    risk_level: str = DataAccessRisk.MEDIUM.value
    evidence: Dict = field(default_factory=dict)
    handled: bool = False


class DataAccessAuditAgent:
    """
    数据访问审计智能体
    
    功能：
    1. 数据源：业务操作日志、数据库查询日志
    2. 审计重点：数据最小化、数据合法性、数据时效性
    3. 异常检测：未授权访问、批量拉取、跨用户访问
    4. 定期报表：数据访问统计报表
    5. 与隐私智能体协同：验证授权状态
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DataAccessAuditAgent"
        self.description = "审计业务智能体对用户数据的访问行为"
        self.config = config or {}
        
        self.access_records: List[DataAccessRecord] = []
        self.anomalies: List[AccessAnomaly] = []
        
        self.sensitive_data_types = {
            "personal_info": ["name", "phone", "email", "id_number", "address"],
            "financial": ["bank_account", "credit_score", "income"],
            "location": ["gps", "ip_address", "home_address", "work_address"],
            "behavior": ["search_history", "click_history", "preferences"],
        }
        
        self.access_thresholds = {
            "max_access_per_minute": 100,
            "max_users_per_hour": 50,
            "max_fields_per_request": 20,
        }
        
        self.stats = {
            "total_access_records": 0,
            "authorized_access": 0,
            "unauthorized_access": 0,
            "anomalies_detected": 0,
            "access_by_type": defaultdict(int),
            "access_by_agent": defaultdict(int),
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_analysis())
    
    async def _periodic_analysis(self):
        while True:
            await asyncio.sleep(300)
            await self._analyze_access_patterns()
    
    def _classify_data_type(self, field_name: str) -> str:
        for data_type, fields in self.sensitive_data_types.items():
            if field_name.lower() in [f.lower() for f in fields]:
                return data_type
        return "general"
    
    def _check_data_minimization(
        self,
        requested_fields: List[str],
        business_purpose: str,
    ) -> Dict:
        purpose_field_mapping = {
            "valuation": ["address", "area", "floor", "building_year"],
            "consultation": ["preferences", "budget", "region"],
            "report_generation": ["name", "phone", "email"],
            "marketing": ["phone", "email"],
        }
        
        allowed_fields = purpose_field_mapping.get(business_purpose, [])
        
        unnecessary_fields = [f for f in requested_fields if f not in allowed_fields]
        
        if len(unnecessary_fields) > len(requested_fields) * 0.5:
            return {
                "compliant": False,
                "risk": DataAccessRisk.HIGH.value,
                "reason": "超过50%的字段超出业务必要范围",
                "unnecessary_fields": unnecessary_fields,
            }
        elif unnecessary_fields:
            return {
                "compliant": True,
                "risk": DataAccessRisk.MEDIUM.value,
                "reason": "部分字段超出业务必要范围",
                "unnecessary_fields": unnecessary_fields,
            }
        
        return {
            "compliant": True,
            "risk": DataAccessRisk.LOW.value,
            "reason": "符合数据最小化原则",
        }
    
    async def record_data_access(
        self,
        user_id: str,
        accessing_agent_id: str,
        data_type: str,
        fields: List[str],
        operation: str,
        purpose: str,
        authorized: bool = False,
        consent_reference: str = "",
    ) -> DataAccessRecord:
        minimization_check = self._check_data_minimization(fields, purpose)
        
        record = DataAccessRecord(
            user_id=user_id,
            accessing_agent_id=accessing_agent_id,
            data_type=data_type,
            fields=fields,
            operation=operation,
            purpose=purpose,
            authorized=authorized,
            consent_reference=consent_reference,
            risk_level=minimization_check["risk"],
        )
        
        self.access_records.append(record)
        
        self.stats["total_access_records"] += 1
        self.stats["access_by_type"][data_type] += 1
        self.stats["access_by_agent"][accessing_agent_id] += 1
        
        if authorized:
            self.stats["authorized_access"] += 1
        else:
            self.stats["unauthorized_access"] += 1
            await self._detect_anomaly("unauthorized_access", record)
        
        return record
    
    async def _detect_anomaly(
        self,
        anomaly_type: str,
        record: DataAccessRecord,
        additional_evidence: Optional[Dict] = None,
    ):
        anomaly = AccessAnomaly(
            anomaly_type=anomaly_type,
            affected_user_id=record.user_id,
            accessing_agent_id=record.accessing_agent_id,
            evidence={
                "record_id": record.record_id,
                "data_type": record.data_type,
                "fields": record.fields,
                "operation": record.operation,
                **(additional_evidence or {}),
            },
        )
        
        if anomaly_type == "unauthorized_access":
            anomaly.description = f"未授权访问用户数据: {record.data_type}"
            anomaly.risk_level = DataAccessRisk.HIGH.value
        
        self.anomalies.append(anomaly)
        self.stats["anomalies_detected"] += 1
        
        logger.warning(f"Data access anomaly detected: {anomaly_type}")
    
    async def _analyze_access_patterns(self):
        now = datetime.utcnow()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        
        recent_records = [
            r for r in self.access_records
            if r.timestamp > one_hour_ago
        ]
        
        agent_access_counts = defaultdict(list)
        for record in recent_records:
            agent_access_counts[record.accessing_agent_id].append(record)
        
        for agent_id, records in agent_access_counts.items():
            if len(records) > self.access_thresholds["max_access_per_minute"]:
                await self._detect_anomaly(
                    "excessive_access",
                    records[0],
                    {"access_count": len(records), "time_window": "1 hour"},
                )
        
        user_access_counts = defaultdict(set)
        for record in recent_records:
            user_access_counts[record.accessing_agent_id].add(record.user_id)
        
        for agent_id, users in user_access_counts.items():
            if len(users) > self.access_thresholds["max_users_per_hour"]:
                await self._detect_anomaly(
                    "bulk_user_access",
                    recent_records[0],
                    {"user_count": len(users), "agent_id": agent_id},
                )
    
    async def check_cross_user_access(
        self,
        requesting_user_id: str,
        accessed_user_id: str,
        accessing_agent_id: str,
    ) -> Dict:
        if requesting_user_id != accessed_user_id:
            anomaly = AccessAnomaly(
                anomaly_type="cross_user_access",
                description=f"用户{requesting_user_id}尝试访问用户{accessed_user_id}的数据",
                affected_user_id=accessed_user_id,
                accessing_agent_id=accessing_agent_id,
                risk_level=DataAccessRisk.CRITICAL.value,
                evidence={
                    "requesting_user": requesting_user_id,
                    "accessed_user": accessed_user_id,
                },
            )
            self.anomalies.append(anomaly)
            self.stats["anomalies_detected"] += 1
            
            return {
                "allowed": False,
                "risk": DataAccessRisk.CRITICAL.value,
                "reason": "跨用户数据访问被阻止",
            }
        
        return {
            "allowed": True,
            "risk": DataAccessRisk.LOW.value,
            "reason": "用户访问自己的数据",
        }
    
    async def generate_access_report(
        self,
        time_range: Optional[tuple] = None,
        group_by: str = "data_type",
    ) -> Dict:
        now = datetime.utcnow()
        
        if time_range:
            start_time = datetime.fromisoformat(time_range[0])
            end_time = datetime.fromisoformat(time_range[1])
        else:
            start_time = now - timedelta(days=7)
            end_time = now
        
        filtered_records = [
            r for r in self.access_records
            if start_time.isoformat() <= r.timestamp <= end_time.isoformat()
        ]
        
        if group_by == "data_type":
            grouped = defaultdict(list)
            for record in filtered_records:
                grouped[record.data_type].append(record)
            
            report = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
                "grouped_stats": {},
            }
            
            for data_type, records in grouped.items():
                report["grouped_stats"][data_type] = {
                    "total_access": len(records),
                    "authorized": sum(1 for r in records if r.authorized),
                    "unauthorized": sum(1 for r in records if not r.authorized),
                    "by_operation": dict(Counter(r.operation for r in records)),
                }
        
        elif group_by == "agent":
            grouped = defaultdict(list)
            for record in filtered_records:
                grouped[record.accessing_agent_id].append(record)
            
            report = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
                "grouped_stats": {},
            }
            
            for agent_id, records in grouped.items():
                report["grouped_stats"][agent_id] = {
                    "total_access": len(records),
                    "unique_users": len(set(r.user_id for r in records)),
                    "data_types": list(set(r.data_type for r in records)),
                }
        
        else:
            report = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
                "summary": {
                    "total_access": len(filtered_records),
                    "authorized": sum(1 for r in filtered_records if r.authorized),
                    "unauthorized": sum(1 for r in filtered_records if not r.authorized),
                    "anomalies": len([a for a in self.anomalies if start_time.isoformat() <= a.timestamp <= end_time.isoformat()]),
                },
            }
        
        return report
    
    async def get_unhandled_anomalies(self) -> List[Dict]:
        return [
            {
                "anomaly_id": a.anomaly_id,
                "timestamp": a.timestamp,
                "type": a.anomaly_type,
                "description": a.description,
                "risk_level": a.risk_level,
                "affected_user": a.affected_user_id,
                "agent": a.accessing_agent_id,
            }
            for a in self.anomalies
            if not a.handled
        ]
    
    async def mark_anomaly_handled(self, anomaly_id: str) -> bool:
        for anomaly in self.anomalies:
            if anomaly.anomaly_id == anomaly_id:
                anomaly.handled = True
                return True
        return False
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_access_records": self.stats["total_access_records"],
            "authorized_access": self.stats["authorized_access"],
            "unauthorized_access": self.stats["unauthorized_access"],
            "anomalies_detected": self.stats["anomalies_detected"],
            "unhandled_anomalies": len([a for a in self.anomalies if not a.handled]),
            "access_by_type": dict(self.stats["access_by_type"]),
        }


from collections import Counter
