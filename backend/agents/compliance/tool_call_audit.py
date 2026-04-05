"""
工具调用审计智能体
记录和审计所有工具调用行为
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


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolCategory(str, Enum):
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIG = "system_config"
    EXTERNAL_API = "external_api"
    AI_INFERENCE = "ai_inference"
    FILE_OPERATION = "file_operation"
    NETWORK = "network"


class ToolCallRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    tool_category: ToolCategory
    caller_agent_id: str
    caller_session_id: Optional[str] = None
    user_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    status: str = "pending"
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RiskAssessment(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    record_id: str
    risk_level: RiskLevel
    risk_factors: List[str]
    recommendations: List[str]
    requires_approval: bool = False
    assessed_at: datetime = Field(default_factory=datetime.now)


class ToolRiskProfile(BaseModel):
    tool_name: str
    category: ToolCategory
    base_risk: RiskLevel
    sensitive_params: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    approval_threshold: int = 1
    rate_limit: int = 100
    allowed_roles: List[str] = Field(default_factory=list)


class RiskAssessor:
    TOOL_PROFILES = {
        "valuation.calculate": ToolRiskProfile(
            tool_name="valuation.calculate",
            category=ToolCategory.AI_INFERENCE,
            base_risk=RiskLevel.LOW,
            sensitive_params=["property_data"],
            rate_limit=100
        ),
        "data.export": ToolRiskProfile(
            tool_name="data.export",
            category=ToolCategory.DATA_ACCESS,
            base_risk=RiskLevel.HIGH,
            sensitive_params=["user_ids", "personal_data"],
            requires_approval=True,
            rate_limit=10
        ),
        "data.delete": ToolRiskProfile(
            tool_name="data.delete",
            category=ToolCategory.DATA_MODIFICATION,
            base_risk=RiskLevel.CRITICAL,
            sensitive_params=["ids", "cascade"],
            requires_approval=True,
            rate_limit=5
        ),
        "system.config": ToolRiskProfile(
            tool_name="system.config",
            category=ToolCategory.SYSTEM_CONFIG,
            base_risk=RiskLevel.HIGH,
            sensitive_params=["all"],
            requires_approval=True,
            rate_limit=10
        ),
        "api.external": ToolRiskProfile(
            tool_name="api.external",
            category=ToolCategory.EXTERNAL_API,
            base_risk=RiskLevel.MEDIUM,
            sensitive_params=["api_key", "credentials"],
            rate_limit=50
        ),
    }
    
    SENSITIVE_PATTERNS = [
        (r'\b\d{17}[\dXx]\b', "id_card"),
        (r'\b1[3-9]\d{9}\b', "phone"),
        (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', "email"),
        (r'password|secret|key|token', "credential"),
    ]
    
    def assess(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        caller_role: Optional[str] = None
    ) -> RiskAssessment:
        profile = self.TOOL_PROFILES.get(tool_name)
        
        if not profile:
            profile = ToolRiskProfile(
                tool_name=tool_name,
                category=ToolCategory.DATA_ACCESS,
                base_risk=RiskLevel.LOW
            )
        
        risk_level = profile.base_risk
        risk_factors = []
        recommendations = []
        requires_approval = profile.requires_approval
        
        for param_name, param_value in parameters.items():
            if param_name in profile.sensitive_params or "all" in profile.sensitive_params:
                risk_factors.append(f"敏感参数: {param_name}")
                if risk_level.value < RiskLevel.HIGH.value:
                    risk_level = RiskLevel.HIGH
            
            if isinstance(param_value, str):
                for pattern, data_type in self.SENSITIVE_PATTERNS:
                    import re
                    if re.search(pattern, param_value, re.IGNORECASE):
                        risk_factors.append(f"参数包含敏感数据: {data_type}")
                        risk_level = RiskLevel.CRITICAL
        
        if caller_role and profile.allowed_roles:
            if caller_role not in profile.allowed_roles:
                risk_factors.append(f"角色 {caller_role} 无权限调用此工具")
                risk_level = RiskLevel.CRITICAL
                requires_approval = True
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("建议进行人工审核")
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("需要管理员审批")
            requires_approval = True
        
        return RiskAssessment(
            record_id="",
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations,
            requires_approval=requires_approval
        )


class RateLimiter:
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.call_history: Dict[str, List[datetime]] = {}
    
    def check_rate(
        self,
        tool_name: str,
        caller_id: str,
        limit: int
    ) -> Tuple[bool, int]:
        key = f"{caller_id}:{tool_name}"
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self.call_history:
            self.call_history[key] = []
        
        self.call_history[key] = [
            ts for ts in self.call_history[key] if ts > window_start
        ]
        
        current_count = len(self.call_history[key])
        
        if current_count >= limit:
            return False, current_count
        
        self.call_history[key].append(now)
        return True, current_count + 1
    
    def get_remaining_calls(
        self,
        tool_name: str,
        caller_id: str,
        limit: int
    ) -> int:
        key = f"{caller_id}:{tool_name}"
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self.call_history:
            return limit
        
        current_count = len([
            ts for ts in self.call_history[key] if ts > window_start
        ])
        
        return max(0, limit - current_count)


class ApprovalWorkflow:
    def __init__(self):
        self.pending_approvals: Dict[str, ToolCallRecord] = {}
        self.approval_history: List[Dict[str, Any]] = []
    
    def request_approval(
        self,
        record: ToolCallRecord,
        assessment: RiskAssessment,
        approvers: List[str]
    ) -> str:
        approval_id = str(uuid4())
        
        self.pending_approvals[approval_id] = record
        
        return approval_id
    
    def approve(
        self,
        approval_id: str,
        approver_id: str,
        comment: Optional[str] = None
    ) -> bool:
        if approval_id not in self.pending_approvals:
            return False
        
        record = self.pending_approvals.pop(approval_id)
        
        self.approval_history.append({
            "approval_id": approval_id,
            "record_id": record.record_id,
            "approver_id": approver_id,
            "action": "approved",
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def reject(
        self,
        approval_id: str,
        approver_id: str,
        reason: str
    ) -> bool:
        if approval_id not in self.pending_approvals:
            return False
        
        record = self.pending_approvals.pop(approval_id)
        
        self.approval_history.append({
            "approval_id": approval_id,
            "record_id": record.record_id,
            "approver_id": approver_id,
            "action": "rejected",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        return True


class ToolCallAuditAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "ToolCallAudit",
        storage: Optional[Any] = None,
        notification_service: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.storage = storage
        self.notification_service = notification_service
        
        self.risk_assessor = RiskAssessor()
        self.rate_limiter = RateLimiter()
        self.approval_workflow = ApprovalWorkflow()
        
        self.call_records: List[ToolCallRecord] = []
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"ToolCallAuditAgent {self.agent_id} initialized")
    
    async def record_call(
        self,
        tool_name: str,
        caller_agent_id: str,
        parameters: Dict[str, Any],
        caller_role: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        profile = self.risk_assessor.TOOL_PROFILES.get(tool_name)
        category = profile.category if profile else ToolCategory.DATA_ACCESS
        
        assessment = self.risk_assessor.assess(
            tool_name,
            parameters,
            caller_role
        )
        
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_category=category,
            caller_agent_id=caller_agent_id,
            caller_session_id=session_id,
            user_id=user_id,
            parameters=parameters,
            risk_level=assessment.risk_level,
            risk_factors=assessment.risk_factors,
            status="pending"
        )
        
        assessment.record_id = record.record_id
        
        if profile:
            allowed, count = self.rate_limiter.check_rate(
                tool_name,
                caller_agent_id,
                profile.rate_limit
            )
            
            if not allowed:
                record.status = "rate_limited"
                self.call_records.append(record)
                return {
                    "allowed": False,
                    "reason": "rate_limit_exceeded",
                    "current_count": count,
                    "limit": profile.rate_limit
                }
        
        if assessment.requires_approval:
            approval_id = self.approval_workflow.request_approval(
                record,
                assessment,
                ["admin", "security_officer"]
            )
            
            record.status = "pending_approval"
            self.call_records.append(record)
            
            if self.notification_service:
                await self.notification_service.notify({
                    "type": "approval_required",
                    "approval_id": approval_id,
                    "tool_name": tool_name,
                    "risk_level": assessment.risk_level.value,
                    "risk_factors": assessment.risk_factors
                })
            
            return {
                "allowed": False,
                "reason": "approval_required",
                "approval_id": approval_id,
                "assessment": assessment.dict()
            }
        
        record.status = "allowed"
        self.call_records.append(record)
        
        return {
            "allowed": True,
            "record_id": record.record_id,
            "risk_level": assessment.risk_level.value
        }
    
    async def record_result(
        self,
        record_id: str,
        result: Dict[str, Any],
        status: str = "completed"
    ):
        for record in self.call_records:
            if record.record_id == record_id:
                record.result = result
                record.status = status
                record.execution_time = (
                    datetime.now() - record.timestamp
                ).total_seconds()
                
                if status == "failed":
                    await self._handle_failed_call(record)
                
                return True
        
        return False
    
    async def _handle_failed_call(self, record: ToolCallRecord):
        if record.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.logger.warning(
                f"High-risk tool call failed: {record.tool_name} "
                f"by {record.caller_agent_id}"
            )
            
            if self.notification_service:
                await self.notification_service.notify({
                    "type": "high_risk_failure",
                    "record_id": record.record_id,
                    "tool_name": record.tool_name,
                    "risk_level": record.risk_level.value
                })
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        return [
            {
                "approval_id": approval_id,
                "record": record.dict()
            }
            for approval_id, record in self.approval_workflow.pending_approvals.items()
        ]
    
    async def approve_call(
        self,
        approval_id: str,
        approver_id: str,
        comment: Optional[str] = None
    ) -> bool:
        success = self.approval_workflow.approve(approval_id, approver_id, comment)
        
        if success:
            self.logger.info(f"Tool call approved: {approval_id} by {approver_id}")
        
        return success
    
    async def reject_call(
        self,
        approval_id: str,
        approver_id: str,
        reason: str
    ) -> bool:
        success = self.approval_workflow.reject(approval_id, approver_id, reason)
        
        if success:
            self.logger.info(f"Tool call rejected: {approval_id} by {approver_id}")
        
        return success
    
    async def query_calls(
        self,
        tool_name: Optional[str] = None,
        caller_id: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        results = []
        
        for record in reversed(self.call_records):
            if tool_name and record.tool_name != tool_name:
                continue
            if caller_id and record.caller_agent_id != caller_id:
                continue
            if risk_level and record.risk_level != risk_level:
                continue
            if status and record.status != status:
                continue
            if start_time and record.timestamp < start_time:
                continue
            
            results.append(record.dict())
            
            if len(results) >= limit:
                break
        
        return results
    
    async def get_high_risk_calls(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        start_time = datetime.now() - timedelta(hours=hours)
        
        return await self.query_calls(
            risk_level=RiskLevel.HIGH,
            start_time=start_time,
            limit=1000
        )
    
    async def get_tool_statistics(
        self,
        tool_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        start_time = datetime.now() - timedelta(hours=hours)
        
        relevant_records = [
            r for r in self.call_records
            if r.timestamp >= start_time and (not tool_name or r.tool_name == tool_name)
        ]
        
        if not relevant_records:
            return {"total_calls": 0}
        
        by_status = {}
        by_risk = {}
        total_time = 0
        
        for record in relevant_records:
            by_status[record.status] = by_status.get(record.status, 0) + 1
            by_risk[record.risk_level.value] = by_risk.get(record.risk_level.value, 0) + 1
            total_time += record.execution_time
        
        return {
            "total_calls": len(relevant_records),
            "by_status": by_status,
            "by_risk": by_risk,
            "avg_execution_time": total_time / len(relevant_records),
            "approval_pending": len(self.approval_workflow.pending_approvals)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        by_tool = {}
        for record in self.call_records:
            by_tool[record.tool_name] = by_tool.get(record.tool_name, 0) + 1
        
        by_risk = {}
        for record in self.call_records:
            risk = record.risk_level.value
            by_risk[risk] = by_risk.get(risk, 0) + 1
        
        return {
            "total_calls": len(self.call_records),
            "by_tool": by_tool,
            "by_risk": by_risk,
            "pending_approvals": len(self.approval_workflow.pending_approvals)
        }


from typing import Tuple
