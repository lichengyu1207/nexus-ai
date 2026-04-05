"""
合规咨询智能体
Compliance Consultant Agent

作为业务智能体的合规顾问，提供实时合规咨询。
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


class ConsultationType(Enum):
    DATA_COLLECTION = "data_collection"
    DATA_USE = "data_use"
    DATA_SHARING = "data_sharing"
    CROSS_BORDER = "cross_border"
    USER_RIGHTS = "user_rights"
    CONSENT = "consent"
    MINOR_DATA = "minor_data"
    SENSITIVE_DATA = "sensitive_data"
    GENERAL = "general"


class ComplianceDecision(Enum):
    ALLOWED = "allowed"
    ALLOWED_WITH_CONDITIONS = "allowed_with_conditions"
    PROHIBITED = "prohibited"
    NEEDS_APPROVAL = "needs_approval"
    UNCLEAR = "unclear"


@dataclass
class ConsultationRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    requester_agent_id: str = ""
    consultation_type: str = ""
    question: str = ""
    
    context: Dict = field(default_factory=dict)
    proposed_action: str = ""
    data_types: List[str] = field(default_factory=list)
    purposes: List[str] = field(default_factory=list)
    user_id: Optional[str] = None
    
    urgency: str = "normal"


@dataclass
class ConsultationResponse:
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    decision: str = ComplianceDecision.ALLOWED.value
    summary: str = ""
    
    applicable_rules: List[Dict] = field(default_factory=list)
    legal_basis: List[str] = field(default_factory=list)
    
    conditions: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    prohibited_actions: List[str] = field(default_factory=list)
    
    risk_level: str = "low"
    risk_factors: List[str] = field(default_factory=list)
    
    recommendations: List[str] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)
    
    confidence: float = 0.0


class ComplianceConsultantAgent:
    """
    合规咨询智能体
    
    功能：
    1. 服务方式：业务智能体在处理用户请求前调用合规咨询
    2. 咨询处理：从合规规则库检索规则，结合用户授权记录推理
    3. 返回结果：合规结论、依据、建议动作
    4. 日志记录：记录每次咨询和答复
    5. 学习能力：根据采纳情况优化咨询质量
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ComplianceConsultantAgent"
        self.description = "作为业务智能体的合规顾问，提供实时合规咨询"
        self.config = config or {}
        
        self.consultation_history: Dict[str, ConsultationRequest] = {}
        self.responses: Dict[str, ConsultationResponse] = {}
        
        self.rule_knowledge = self._init_rule_knowledge()
        self.decision_templates = self._init_decision_templates()
        
        self.stats = {
            "total_consultations": 0,
            "consultations_by_type": defaultdict(int),
            "consultations_by_decision": defaultdict(int),
            "avg_response_time_ms": 0,
            "adoption_rate": 0.0,
        }
        
        self._initialized = False
    
    def _init_rule_knowledge(self) -> Dict:
        return {
            "data_collection": {
                "rules": [
                    {
                        "id": "R001",
                        "condition": "收集个人信息",
                        "requirement": "获取用户同意",
                        "legal_basis": "个人信息保护法第13条",
                    },
                    {
                        "id": "R002",
                        "condition": "收集非必要个人信息",
                        "requirement": "用户可拒绝",
                        "legal_basis": "App违规收集认定方法",
                    },
                ],
            },
            "sensitive_data": {
                "rules": [
                    {
                        "id": "R003",
                        "condition": "处理敏感个人信息",
                        "requirement": "获取单独同意",
                        "legal_basis": "个人信息保护法第29条",
                    },
                    {
                        "id": "R004",
                        "condition": "处理生物识别信息",
                        "requirement": "告知必要性和影响",
                        "legal_basis": "个人信息保护法第30条",
                    },
                ],
            },
            "minor_data": {
                "rules": [
                    {
                        "id": "R005",
                        "condition": "处理不满14周岁未成年人信息",
                        "requirement": "监护人同意",
                        "legal_basis": "个人信息保护法第32条",
                    },
                ],
            },
            "cross_border": {
                "rules": [
                    {
                        "id": "R006",
                        "condition": "向境外提供个人信息",
                        "requirement": "安全评估或标准合同",
                        "legal_basis": "数据出境安全评估办法",
                    },
                ],
            },
            "consent": {
                "rules": [
                    {
                        "id": "R007",
                        "condition": "处理个人信息",
                        "requirement": "告知处理目的、方式、范围",
                        "legal_basis": "个人信息保护法第17条",
                    },
                ],
            },
        }
    
    def _init_decision_templates(self) -> Dict:
        return {
            ComplianceDecision.ALLOWED.value: {
                "summary_template": "该操作符合合规要求，可以执行。",
                "risk_level": "low",
            },
            ComplianceDecision.ALLOWED_WITH_CONDITIONS.value: {
                "summary_template": "该操作在满足特定条件后可以执行。",
                "risk_level": "medium",
            },
            ComplianceDecision.PROHIBITED.value: {
                "summary_template": "该操作违反合规要求，禁止执行。",
                "risk_level": "high",
            },
            ComplianceDecision.NEEDS_APPROVAL.value: {
                "summary_template": "该操作需要人工审批后才能执行。",
                "risk_level": "medium",
            },
            ComplianceDecision.UNCLEAR.value: {
                "summary_template": "无法确定合规状态，建议咨询合规官。",
                "risk_level": "unknown",
            },
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def consult(
        self,
        requester_agent_id: str,
        question: str,
        consultation_type: str = ConsultationType.GENERAL.value,
        context: Optional[Dict] = None,
        proposed_action: Optional[str] = None,
        data_types: Optional[List[str]] = None,
        purposes: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        urgency: str = "normal",
    ) -> ConsultationResponse:
        start_time = datetime.utcnow()
        
        request = ConsultationRequest(
            requester_agent_id=requester_agent_id,
            consultation_type=consultation_type,
            question=question,
            context=context or {},
            proposed_action=proposed_action or "",
            data_types=data_types or [],
            purposes=purposes or [],
            user_id=user_id,
            urgency=urgency,
        )
        
        self.consultation_history[request.request_id] = request
        
        response = await self._process_consultation(request)
        
        self.responses[response.response_id] = response
        
        self.stats["total_consultations"] += 1
        self.stats["consultations_by_type"][consultation_type] += 1
        self.stats["consultations_by_decision"][response.decision] += 1
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        current_avg = self.stats["avg_response_time_ms"]
        total = self.stats["total_consultations"]
        self.stats["avg_response_time_ms"] = (current_avg * (total - 1) + response_time) / total
        
        return response
    
    async def _process_consultation(
        self,
        request: ConsultationRequest,
    ) -> ConsultationResponse:
        response = ConsultationResponse(request_id=request.request_id)
        
        applicable_rules = self._find_applicable_rules(request)
        response.applicable_rules = applicable_rules
        
        decision = self._determine_decision(request, applicable_rules)
        response.decision = decision
        
        template = self.decision_templates.get(decision, {})
        response.summary = template.get("summary_template", "")
        response.risk_level = template.get("risk_level", "unknown")
        
        response.legal_basis = [r.get("legal_basis", "") for r in applicable_rules]
        
        response.conditions = self._determine_conditions(request, applicable_rules)
        response.required_actions = self._determine_required_actions(request, applicable_rules)
        response.prohibited_actions = self._determine_prohibited_actions(request, applicable_rules)
        
        response.recommendations = self._generate_recommendations(request, decision)
        response.alternative_approaches = self._suggest_alternatives(request, decision)
        
        response.confidence = self._calculate_confidence(request, applicable_rules)
        
        return response
    
    def _find_applicable_rules(self, request: ConsultationRequest) -> List[Dict]:
        applicable_rules = []
        
        for category, knowledge in self.rule_knowledge.items():
            if category in request.consultation_type:
                applicable_rules.extend(knowledge.get("rules", []))
        
        if request.data_types:
            sensitive_types = ["biometric", "financial", "health", "location"]
            if any(dt in sensitive_types for dt in request.data_types):
                applicable_rules.extend(
                    self.rule_knowledge.get("sensitive_data", {}).get("rules", [])
                )
        
        if "minor" in str(request.context).lower() or "儿童" in str(request.context).lower():
            applicable_rules.extend(
                self.rule_knowledge.get("minor_data", {}).get("rules", [])
            )
        
        if request.consultation_type == ConsultationType.CROSS_BORDER.value:
            applicable_rules.extend(
                self.rule_knowledge.get("cross_border", {}).get("rules", [])
            )
        
        return applicable_rules
    
    def _determine_decision(
        self,
        request: ConsultationRequest,
        rules: List[Dict],
    ) -> str:
        if not rules:
            return ComplianceDecision.ALLOWED.value
        
        has_prohibition = False
        has_condition = False
        
        for rule in rules:
            requirement = rule.get("requirement", "")
            
            if "禁止" in requirement or "不得" in requirement:
                has_prohibition = True
            
            if any(kw in requirement for kw in ["同意", "审批", "评估", "告知"]):
                has_condition = True
        
        if has_prohibition:
            return ComplianceDecision.PROHIBITED.value
        
        if has_condition:
            consent_status = request.context.get("user_consent", None)
            if consent_status is False:
                return ComplianceDecision.PROHIBITED.value
            elif consent_status is True:
                return ComplianceDecision.ALLOWED.value
            else:
                return ComplianceDecision.ALLOWED_WITH_CONDITIONS.value
        
        return ComplianceDecision.ALLOWED.value
    
    def _determine_conditions(
        self,
        request: ConsultationRequest,
        rules: List[Dict],
    ) -> List[str]:
        conditions = []
        
        for rule in rules:
            requirement = rule.get("requirement", "")
            if requirement and requirement not in conditions:
                conditions.append(requirement)
        
        return conditions
    
    def _determine_required_actions(
        self,
        request: ConsultationRequest,
        rules: List[Dict],
    ) -> List[str]:
        actions = []
        
        for rule in rules:
            requirement = rule.get("requirement", "")
            
            if "同意" in requirement:
                if "单独同意" in requirement:
                    actions.append("获取用户单独同意")
                elif "监护人同意" in requirement:
                    actions.append("获取监护人同意")
                else:
                    actions.append("获取用户同意")
            
            if "告知" in requirement:
                actions.append("告知用户处理目的、方式和范围")
            
            if "评估" in requirement:
                actions.append("完成安全评估")
        
        return list(set(actions))
    
    def _determine_prohibited_actions(
        self,
        request: ConsultationRequest,
        rules: List[Dict],
    ) -> List[str]:
        prohibited = []
        
        for rule in rules:
            requirement = rule.get("requirement", "")
            if "禁止" in requirement or "不得" in requirement:
                prohibited.append(requirement)
        
        return prohibited
    
    def _generate_recommendations(
        self,
        request: ConsultationRequest,
        decision: str,
    ) -> List[str]:
        recommendations = []
        
        if decision == ComplianceDecision.PROHIBITED.value:
            recommendations.append("建议停止该操作，重新评估业务需求")
            recommendations.append("可考虑替代方案实现相同业务目标")
        
        elif decision == ComplianceDecision.ALLOWED_WITH_CONDITIONS.value:
            recommendations.append("请确保满足所有条件后再执行")
            recommendations.append("建议记录合规检查过程")
        
        elif decision == ComplianceDecision.NEEDS_APPROVAL.value:
            recommendations.append("请提交合规审批流程")
            recommendations.append("准备相关材料支持审批")
        
        if request.data_types:
            recommendations.append("建议遵循数据最小化原则")
        
        return recommendations
    
    def _suggest_alternatives(
        self,
        request: ConsultationRequest,
        decision: str,
    ) -> List[str]:
        alternatives = []
        
        if decision == ComplianceDecision.PROHIBITED.value:
            if "收集" in request.proposed_action:
                alternatives.append("考虑使用脱敏或匿名化数据")
                alternatives.append("评估是否可以减少数据收集范围")
            
            if "跨境" in request.question or "境外" in request.question:
                alternatives.append("考虑在本地处理数据，避免跨境传输")
        
        return alternatives
    
    def _calculate_confidence(
        self,
        request: ConsultationRequest,
        rules: List[Dict],
    ) -> float:
        if not rules:
            return 0.5
        
        confidence = 0.7
        
        if request.context:
            confidence += 0.1
        
        if request.data_types:
            confidence += 0.05
        
        if request.purposes:
            confidence += 0.05
        
        if request.user_id:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    async def get_consultation_history(
        self,
        requester_agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        requests = list(self.consultation_history.values())
        
        if requester_agent_id:
            requests = [r for r in requests if r.requester_agent_id == requester_agent_id]
        
        requests.sort(key=lambda r: r.timestamp, reverse=True)
        
        return [
            {
                "request_id": r.request_id,
                "timestamp": r.timestamp,
                "requester": r.requester_agent_id,
                "type": r.consultation_type,
                "question": r.question[:100],
                "decision": self.responses.get(r.request_id, ConsultationResponse()).decision,
            }
            for r in requests[:limit]
        ]
    
    async def record_adoption(
        self,
        request_id: str,
        adopted: bool,
        feedback: Optional[str] = None,
    ) -> bool:
        request = self.consultation_history.get(request_id)
        if not request:
            return False
        
        total = self.stats["total_consultations"]
        current_rate = self.stats["adoption_rate"]
        
        if adopted:
            self.stats["adoption_rate"] = (current_rate * (total - 1) + 1) / total
        else:
            self.stats["adoption_rate"] = current_rate * (total - 1) / total
        
        return True
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_consultations": self.stats["total_consultations"],
            "consultations_by_type": dict(self.stats["consultations_by_type"]),
            "consultations_by_decision": dict(self.stats["consultations_by_decision"]),
            "avg_response_time_ms": round(self.stats["avg_response_time_ms"], 2),
            "adoption_rate": round(self.stats["adoption_rate"], 2),
        }
