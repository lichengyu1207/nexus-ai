"""
用户授权管理智能体
管理用户对数据处理的授权同意
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    EXPLICIT = "explicit"
    IMPLIED = "implied"
    OPT_IN = "opt_in"
    OPT_OUT = "opt_out"
    WITHDRAWN = "withdrawn"


class ConsentScope(str, Enum):
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY = "third_party"
    CROSS_BORDER = "cross_border"
    AI_TRAINING = "ai_training"


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"
    REJECTED = "rejected"


class ConsentRecord(BaseModel):
    consent_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    consent_type: ConsentType
    scope: ConsentScope
    status: ConsentStatus = ConsentStatus.PENDING
    purpose: str
    data_categories: List[str] = Field(default_factory=list)
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConsentTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    scope: ConsentScope
    purpose: str
    data_categories: List[str]
    required: bool = False
    default_status: ConsentStatus = ConsentStatus.PENDING
    validity_days: int = 365
    version: str = "1.0"


class ConsentRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    template_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"


class ConsentValidator:
    def __init__(self):
        self.required_fields = ["user_id", "scope", "purpose"]
    
    def validate(self, consent_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        for field in self.required_fields:
            if field not in consent_data or not consent_data[field]:
                errors.append(f"缺少必填字段: {field}")
        
        if "data_categories" in consent_data:
            if not isinstance(consent_data["data_categories"], list):
                errors.append("data_categories 必须是列表")
            elif not consent_data["data_categories"]:
                errors.append("data_categories 不能为空")
        
        return len(errors) == 0, errors


class ConsentRegistry:
    def __init__(self):
        self.records: Dict[str, ConsentRecord] = {}
        self.user_consents: Dict[str, Set[str]] = {}
        self.scope_index: Dict[str, Set[str]] = {}
    
    def register(self, record: ConsentRecord):
        self.records[record.consent_id] = record
        
        if record.user_id not in self.user_consents:
            self.user_consents[record.user_id] = set()
        self.user_consents[record.user_id].add(record.consent_id)
        
        scope = record.scope.value
        if scope not in self.scope_index:
            self.scope_index[scope] = set()
        self.scope_index[scope].add(record.consent_id)
    
    def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        consent_ids = self.user_consents.get(user_id, set())
        return [self.records[cid] for cid in consent_ids if cid in self.records]
    
    def get_by_scope(self, scope: ConsentScope) -> List[ConsentRecord]:
        consent_ids = self.scope_index.get(scope.value, set())
        return [self.records[cid] for cid in consent_ids if cid in self.records]
    
    def get_active_consents(self, user_id: str, scope: ConsentScope) -> List[ConsentRecord]:
        consents = self.get_user_consents(user_id)
        
        active = []
        for consent in consents:
            if consent.scope != scope:
                continue
            
            if consent.status != ConsentStatus.GRANTED:
                continue
            
            if consent.expires_at and consent.expires_at < datetime.now():
                continue
            
            active.append(consent)
        
        return active


class UserConsentManagerAgent:
    DEFAULT_TEMPLATES = [
        ConsentTemplate(
            name="数据收集授权",
            description="授权平台收集您的个人信息",
            scope=ConsentScope.DATA_COLLECTION,
            purpose="提供房产估值服务",
            data_categories=["基本信息", "房产信息"],
            required=True,
            validity_days=365
        ),
        ConsentTemplate(
            name="数据处理授权",
            description="授权平台处理您的个人信息",
            scope=ConsentScope.DATA_PROCESSING,
            purpose="房产估值分析",
            data_categories=["房产信息", "交易数据"],
            required=True,
            validity_days=365
        ),
        ConsentTemplate(
            name="营销推送授权",
            description="接收平台营销信息",
            scope=ConsentScope.MARKETING,
            purpose="营销推广",
            data_categories=["联系方式"],
            required=False,
            default_status=ConsentStatus.REJECTED,
            validity_days=180
        ),
        ConsentTemplate(
            name="数据分析授权",
            description="授权使用数据进行统计分析",
            scope=ConsentScope.ANALYTICS,
            purpose="改善服务质量",
            data_categories=["使用记录", "行为数据"],
            required=False,
            validity_days=365
        ),
        ConsentTemplate(
            name="第三方共享授权",
            description="授权与合作伙伴共享数据",
            scope=ConsentScope.THIRD_PARTY,
            purpose="提供增值服务",
            data_categories=["基本信息"],
            required=False,
            default_status=ConsentStatus.REJECTED,
            validity_days=90
        ),
        ConsentTemplate(
            name="AI训练授权",
            description="授权使用数据训练AI模型",
            scope=ConsentScope.AI_TRAINING,
            purpose="提升AI服务能力",
            data_categories=["交互数据", "反馈数据"],
            required=False,
            default_status=ConsentStatus.REJECTED,
            validity_days=365
        ),
    ]
    
    def __init__(
        self,
        agent_id: str,
        name: str = "UserConsentManager",
        audit_agent: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.audit_agent = audit_agent
        
        self.validator = ConsentValidator()
        self.registry = ConsentRegistry()
        
        self.templates: Dict[str, ConsentTemplate] = {}
        self._init_default_templates()
        
        self.consent_requests: Dict[str, ConsentRequest] = {}
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    def _init_default_templates(self):
        for template in self.DEFAULT_TEMPLATES:
            self.templates[template.template_id] = template
    
    async def initialize(self):
        self.logger.info(f"UserConsentManagerAgent {self.agent_id} initialized")
    
    async def request_consent(
        self,
        user_id: str,
        template_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConsentRequest:
        template = self.templates.get(template_id)
        
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        request = ConsentRequest(
            user_id=user_id,
            template_id=template_id,
            context=context or {}
        )
        
        self.consent_requests[request.request_id] = request
        
        return request
    
    async def grant_consent(
        self,
        user_id: str,
        scope: ConsentScope,
        purpose: str,
        data_categories: List[str],
        consent_type: ConsentType = ConsentType.EXPLICIT,
        expires_in_days: Optional[int] = None,
        source: str = "user_action",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConsentRecord:
        validity_days = expires_in_days or 365
        expires_at = datetime.now() + timedelta(days=validity_days)
        
        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            scope=scope,
            status=ConsentStatus.GRANTED,
            purpose=purpose,
            data_categories=data_categories,
            granted_at=datetime.now(),
            expires_at=expires_at,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.registry.register(record)
        
        if self.audit_agent:
            await self.audit_agent.log_user_session(
                user_id=user_id,
                session_id=None,
                action="consent_granted",
                details={
                    "consent_id": record.consent_id,
                    "scope": scope.value,
                    "purpose": purpose
                }
            )
        
        self.logger.info(f"Consent granted: {record.consent_id} for user {user_id}")
        
        return record
    
    async def withdraw_consent(
        self,
        consent_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> bool:
        record = self.registry.records.get(consent_id)
        
        if not record:
            return False
        
        if record.user_id != user_id:
            return False
        
        record.status = ConsentStatus.WITHDRAWN
        record.withdrawn_at = datetime.now()
        record.metadata["withdrawal_reason"] = reason
        
        if self.audit_agent:
            await self.audit_agent.log_user_session(
                user_id=user_id,
                session_id=None,
                action="consent_withdrawn",
                details={
                    "consent_id": consent_id,
                    "scope": record.scope.value,
                    "reason": reason
                }
            )
        
        self.logger.info(f"Consent withdrawn: {consent_id} by user {user_id}")
        
        return True
    
    async def check_consent(
        self,
        user_id: str,
        scope: ConsentScope,
        data_category: Optional[str] = None
    ) -> bool:
        active_consents = self.registry.get_active_consents(user_id, scope)
        
        if not active_consents:
            return False
        
        if data_category:
            for consent in active_consents:
                if data_category in consent.data_categories:
                    return True
            return False
        
        return True
    
    async def get_user_consents(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        consents = self.registry.get_user_consents(user_id)
        
        result = []
        for consent in consents:
            if not include_expired:
                if consent.status == ConsentStatus.WITHDRAWN:
                    continue
                if consent.expires_at and consent.expires_at < datetime.now():
                    continue
            
            result.append({
                "consent_id": consent.consent_id,
                "scope": consent.scope.value,
                "purpose": consent.purpose,
                "status": consent.status.value,
                "data_categories": consent.data_categories,
                "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None
            })
        
        return result
    
    async def get_required_consents(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        required = []
        
        for template in self.templates.values():
            if not template.required:
                continue
            
            has_consent = await self.check_consent(
                user_id,
                template.scope
            )
            
            if not has_consent:
                required.append({
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "scope": template.scope.value,
                    "purpose": template.purpose,
                    "data_categories": template.data_categories
                })
        
        return required
    
    async def batch_grant(
        self,
        user_id: str,
        consents: List[Dict[str, Any]]
    ) -> List[ConsentRecord]:
        records = []
        
        for consent_data in consents:
            is_valid, errors = self.validator.validate(consent_data)
            
            if not is_valid:
                self.logger.warning(f"Invalid consent data: {errors}")
                continue
            
            record = await self.grant_consent(
                user_id=user_id,
                scope=ConsentScope(consent_data["scope"]),
                purpose=consent_data["purpose"],
                data_categories=consent_data.get("data_categories", []),
                consent_type=ConsentType(consent_data.get("consent_type", "explicit")),
                expires_in_days=consent_data.get("expires_in_days")
            )
            
            records.append(record)
        
        return records
    
    async def cleanup_expired(self) -> int:
        expired_count = 0
        
        for record in self.registry.records.values():
            if record.status == ConsentStatus.GRANTED:
                if record.expires_at and record.expires_at < datetime.now():
                    record.status = ConsentStatus.EXPIRED
                    expired_count += 1
        
        self.logger.info(f"Marked {expired_count} consents as expired")
        
        return expired_count
    
    async def get_consent_statistics(
        self,
        scope: Optional[ConsentScope] = None
    ) -> Dict[str, Any]:
        records = list(self.registry.records.values())
        
        if scope:
            records = [r for r in records if r.scope == scope]
        
        by_status = {}
        by_scope = {}
        
        for record in records:
            status = record.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            scope_val = record.scope.value
            by_scope[scope_val] = by_scope.get(scope_val, 0) + 1
        
        return {
            "total_consents": len(records),
            "by_status": by_status,
            "by_scope": by_scope,
            "unique_users": len(self.registry.user_consents)
        }
    
    def add_template(self, template: ConsentTemplate):
        self.templates[template.template_id] = template
        self.logger.info(f"Added consent template: {template.name}")
    
    def get_templates(self) -> List[Dict[str, Any]]:
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "scope": t.scope.value,
                "purpose": t.purpose,
                "required": t.required,
                "data_categories": t.data_categories
            }
            for t in self.templates.values()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_records": len(self.registry.records),
            "total_users": len(self.registry.user_consents),
            "templates_count": len(self.templates)
        }


from typing import Tuple
