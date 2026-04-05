"""
用户同意记录智能体
User Consent Recording Agent

负责记录用户对隐私政策的同意情况，并向业务智能体提供授权查询服务。
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


class ConsentMethod(Enum):
    CLICK = "click"
    SIGN = "sign"
    API = "api"
    IMPLICIT = "implicit"


class ConsentStatus(Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


@dataclass
class ConsentRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    policy_version: str = ""
    consent_type: str = ""
    consent_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    consent_method: str = ConsentMethod.CLICK.value
    ip_address: str = ""
    user_agent: str = ""
    device_fingerprint: str = ""
    
    purposes: List[str] = field(default_factory=list)
    data_categories: List[str] = field(default_factory=list)
    
    valid: bool = True
    status: str = ConsentStatus.ACTIVE.value
    withdraw_time: str = ""
    withdraw_reason: str = ""
    
    parent_consent_id: str = ""
    guardian_info: Dict = field(default_factory=dict)
    
    previous_hash: str = ""
    current_hash: str = ""


@dataclass
class ConsentTemplate:
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    policy_version: str = ""
    purposes: List[str] = field(default_factory=list)
    data_categories: List[str] = field(default_factory=list)
    required: bool = True
    minor_required: bool = False
    text: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class UserConsentRecordingAgent:
    """
    用户同意记录智能体
    
    功能：
    1. 同意记录表设计：用户ID、政策版本、同意时间、方式、IP等
    2. 同意查询接口：检查用户是否同意某个处理目的
    3. 同意撤回处理：更新记录并触发数据清理流程
    4. 与业务智能体集成：处理前自动调用同意查询接口
    5. 合规审计：提供同意记录导出接口，哈希链防篡改
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "UserConsentRecordingAgent"
        self.description = "记录用户对隐私政策的同意情况"
        self.config = config or {}
        
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.user_consents: Dict[str, List[str]] = defaultdict(list)
        self.consent_templates: Dict[str, ConsentTemplate] = {}
        
        self.hash_chain_head = ""
        
        self._init_consent_templates()
        
        self.stats = {
            "total_consents": 0,
            "active_consents": 0,
            "withdrawn_consents": 0,
            "consents_by_purpose": defaultdict(int),
            "consents_by_method": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_consent_templates(self):
        templates = [
            ConsentTemplate(
                name="基础服务同意",
                description="同意收集和使用基础个人信息以提供服务",
                purposes=["service_provision"],
                data_categories=["personal_info", "contact"],
                required=True,
                text="我已阅读并同意《隐私政策》，授权平台收集和使用我的个人信息以提供服务。",
            ),
            ConsentTemplate(
                name="营销推广同意",
                description="同意接收营销推广信息",
                purposes=["marketing", "promotion"],
                data_categories=["contact"],
                required=False,
                text="我同意接收平台发送的营销推广信息。",
            ),
            ConsentTemplate(
                name="数据分析同意",
                description="同意将数据用于分析和改进服务",
                purposes=["analytics", "improvement"],
                data_categories=["behavior", "usage"],
                required=False,
                text="我同意平台将我的使用数据用于分析和改进服务。",
            ),
            ConsentTemplate(
                name="第三方共享同意",
                description="同意与第三方共享数据",
                purposes=["third_party_sharing"],
                data_categories=["personal_info"],
                required=False,
                text="我同意平台将我的个人信息共享给合作第三方。",
            ),
            ConsentTemplate(
                name="敏感信息处理同意",
                description="同意处理敏感个人信息",
                purposes=["sensitive_processing"],
                data_categories=["biometric", "financial", "location"],
                required=False,
                minor_required=True,
                text="我同意平台处理我的敏感个人信息。",
            ),
        ]
        
        for template in templates:
            self.consent_templates[template.template_id] = template
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _compute_hash(self, record: ConsentRecord) -> str:
        data = json.dumps({
            "id": record.id,
            "user_id": record.user_id,
            "policy_version": record.policy_version,
            "consent_type": record.consent_type,
            "consent_time": record.consent_time,
            "purposes": record.purposes,
            "data_categories": record.data_categories,
            "previous_hash": record.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def record_consent(
        self,
        user_id: str,
        policy_version: str,
        consent_type: str,
        consent_method: str = ConsentMethod.CLICK.value,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: str = "",
        purposes: Optional[List[str]] = None,
        data_categories: Optional[List[str]] = None,
        guardian_info: Optional[Dict] = None,
    ) -> ConsentRecord:
        record = ConsentRecord(
            user_id=user_id,
            policy_version=policy_version,
            consent_type=consent_type,
            consent_method=consent_method,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            purposes=purposes or [],
            data_categories=data_categories or [],
            guardian_info=guardian_info or {},
            previous_hash=self.hash_chain_head,
        )
        
        record.current_hash = self._compute_hash(record)
        self.hash_chain_head = record.current_hash
        
        self.consent_records[record.id] = record
        self.user_consents[user_id].append(record.id)
        
        self.stats["total_consents"] += 1
        self.stats["active_consents"] += 1
        self.stats["consents_by_method"][consent_method] += 1
        
        for purpose in purposes or []:
            self.stats["consents_by_purpose"][purpose] += 1
        
        return record
    
    async def record_consent_from_template(
        self,
        user_id: str,
        template_id: str,
        consent_method: str = ConsentMethod.CLICK.value,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[ConsentRecord]:
        template = self.consent_templates.get(template_id)
        if not template:
            return None
        
        return await self.record_consent(
            user_id=user_id,
            policy_version=template.policy_version,
            consent_type=template.name,
            consent_method=consent_method,
            ip_address=ip_address,
            user_agent=user_agent,
            purposes=template.purposes,
            data_categories=template.data_categories,
        )
    
    async def has_consented(
        self,
        user_id: str,
        purpose: str,
        data_category: Optional[str] = None,
    ) -> Dict:
        user_record_ids = self.user_consents.get(user_id, [])
        
        for record_id in user_record_ids:
            record = self.consent_records.get(record_id)
            if not record or not record.valid or record.status != ConsentStatus.ACTIVE.value:
                continue
            
            if purpose in record.purposes:
                if data_category and data_category not in record.data_categories:
                    continue
                
                return {
                    "consented": True,
                    "consent_id": record.id,
                    "consent_time": record.consent_time,
                    "policy_version": record.policy_version,
                }
        
        return {
            "consented": False,
            "reason": "未找到有效的同意记录",
        }
    
    async def get_consent_records(
        self,
        user_id: str,
        include_withdrawn: bool = False,
    ) -> List[Dict]:
        user_record_ids = self.user_consents.get(user_id, [])
        
        records = []
        for record_id in user_record_ids:
            record = self.consent_records.get(record_id)
            if not record:
                continue
            
            if not include_withdrawn and not record.valid:
                continue
            
            records.append({
                "id": record.id,
                "consent_type": record.consent_type,
                "consent_time": record.consent_time,
                "consent_method": record.consent_method,
                "purposes": record.purposes,
                "data_categories": record.data_categories,
                "status": record.status,
                "valid": record.valid,
                "withdraw_time": record.withdraw_time,
            })
        
        return records
    
    async def withdraw_consent(
        self,
        user_id: str,
        consent_id: str,
        reason: str = "",
    ) -> Dict:
        record = self.consent_records.get(consent_id)
        
        if not record or record.user_id != user_id:
            return {
                "success": False,
                "reason": "同意记录不存在或不属于该用户",
            }
        
        if not record.valid or record.status == ConsentStatus.WITHDRAWN.value:
            return {
                "success": False,
                "reason": "同意记录已失效或已撤回",
            }
        
        record.valid = False
        record.status = ConsentStatus.WITHDRAWN.value
        record.withdraw_time = datetime.utcnow().isoformat()
        record.withdraw_reason = reason
        
        self.stats["active_consents"] -= 1
        self.stats["withdrawn_consents"] += 1
        
        return {
            "success": True,
            "consent_id": consent_id,
            "withdraw_time": record.withdraw_time,
            "data_cleanup_required": True,
            "affected_purposes": record.purposes,
            "affected_data_categories": record.data_categories,
        }
    
    async def withdraw_all_consents(
        self,
        user_id: str,
        reason: str = "",
    ) -> Dict:
        user_record_ids = self.user_consents.get(user_id, [])
        
        withdrawn_count = 0
        affected_purposes = set()
        affected_data_categories = set()
        
        for record_id in user_record_ids:
            result = await self.withdraw_consent(user_id, record_id, reason)
            if result.get("success"):
                withdrawn_count += 1
                affected_purposes.update(result.get("affected_purposes", []))
                affected_data_categories.update(result.get("affected_data_categories", []))
        
        return {
            "success": True,
            "withdrawn_count": withdrawn_count,
            "affected_purposes": list(affected_purposes),
            "affected_data_categories": list(affected_data_categories),
        }
    
    async def check_minor_consent(
        self,
        user_id: str,
        age: int,
    ) -> Dict:
        if age >= 18:
            return {
                "is_minor": False,
                "guardian_consent_required": False,
            }
        
        if age < 14:
            user_record_ids = self.user_consents.get(user_id, [])
            
            for record_id in user_record_ids:
                record = self.consent_records.get(record_id)
                if record and record.valid and record.guardian_info:
                    return {
                        "is_minor": True,
                        "guardian_consent_required": True,
                        "guardian_consent_exists": True,
                        "guardian_info": {
                            "name": record.guardian_info.get("name", ""),
                            "relationship": record.guardian_info.get("relationship", ""),
                        },
                    }
            
            return {
                "is_minor": True,
                "guardian_consent_required": True,
                "guardian_consent_exists": False,
            }
        
        return {
            "is_minor": True,
            "guardian_consent_required": False,
            "guardian_consent_recommended": True,
        }
    
    async def record_guardian_consent(
        self,
        minor_user_id: str,
        guardian_name: str,
        guardian_id_number: str,
        relationship: str,
        policy_version: str,
        purposes: List[str],
        data_categories: List[str],
        ip_address: str = "",
    ) -> ConsentRecord:
        return await self.record_consent(
            user_id=minor_user_id,
            policy_version=policy_version,
            consent_type="监护人同意",
            consent_method=ConsentMethod.SIGN.value,
            ip_address=ip_address,
            purposes=purposes,
            data_categories=data_categories,
            guardian_info={
                "name": guardian_name,
                "id_number": guardian_id_number[:6] + "****" + guardian_id_number[-4:],
                "relationship": relationship,
            },
        )
    
    async def get_consent_templates(self) -> List[Dict]:
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "purposes": t.purposes,
                "data_categories": t.data_categories,
                "required": t.required,
                "text": t.text,
            }
            for t in self.consent_templates.values()
        ]
    
    async def verify_consent_integrity(self, consent_id: str) -> Dict:
        record = self.consent_records.get(consent_id)
        if not record:
            return {"valid": False, "reason": "记录不存在"}
        
        expected_hash = self._compute_hash(record)
        if record.current_hash != expected_hash:
            return {
                "valid": False,
                "reason": "哈希值不匹配，记录可能被篡改",
            }
        
        return {"valid": True, "reason": "记录完整性验证通过"}
    
    async def export_user_consents(self, user_id: str) -> Dict:
        records = await self.get_consent_records(user_id, include_withdrawn=True)
        
        return {
            "user_id": user_id,
            "export_time": datetime.utcnow().isoformat(),
            "total_records": len(records),
            "records": records,
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_consents": self.stats["total_consents"],
            "active_consents": self.stats["active_consents"],
            "withdrawn_consents": self.stats["withdrawn_consents"],
            "consents_by_purpose": dict(self.stats["consents_by_purpose"]),
            "consents_by_method": dict(self.stats["consents_by_method"]),
            "unique_users": len(self.user_consents),
        }
