"""
隐私影响评估智能体
Privacy Impact Assessment Agent

负责对新业务功能进行隐私影响评估（PIA）。
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


class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class AssessmentStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    MITIGATION_REQUIRED = "mitigation_required"


@dataclass
class DataProcessingActivity:
    activity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    data_types: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    purposes: List[str] = field(default_factory=list)
    legal_basis: str = ""
    recipients: List[str] = field(default_factory=list)
    retention_period: str = ""
    cross_border: bool = False
    cross_border_destination: str = ""
    automated_decision_making: bool = False
    sensitive_data: bool = False


@dataclass
class PrivacyRisk:
    risk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    risk_type: str = ""
    description: str = ""
    likelihood: str = "medium"
    impact: str = "medium"
    risk_level: str = RiskLevel.MEDIUM.value
    affected_data_subjects: List[str] = field(default_factory=list)
    affected_data_types: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    residual_risk: str = RiskLevel.LOW.value
    owner: str = ""


@dataclass
class PIAssessment:
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    feature_name: str = ""
    feature_description: str = ""
    trigger_reason: str = ""
    status: str = AssessmentStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    assessor: str = ""
    approver: str = ""
    approved_at: str = ""
    
    processing_activities: List[DataProcessingActivity] = field(default_factory=list)
    risks: List[PrivacyRisk] = field(default_factory=list)
    
    necessity_check: Dict = field(default_factory=dict)
    proportionality_check: Dict = field(default_factory=dict)
    
    overall_risk_level: str = RiskLevel.LOW.value
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    approval_conditions: List[str] = field(default_factory=list)


class PrivacyImpactAssessmentAgent:
    """
    隐私影响评估智能体
    
    功能：
    1. 触发条件：新业务功能上线前、重大变更、法规更新
    2. 评估流程：收集数据处理活动、识别风险、评估等级、提出缓解措施
    3. 评估报告：数据处理清单、风险分析、缓解措施、残余风险
    4. 与规则库交互：检查新功能是否符合所有适用法规
    5. 持续监控：上线后定期复查
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "PrivacyImpactAssessmentAgent"
        self.description = "对新业务功能进行隐私影响评估（PIA）"
        self.config = config or {}
        
        self.assessments: Dict[str, PIAssessment] = {}
        self.risk_templates = self._init_risk_templates()
        
        self.sensitive_data_types = [
            "biometric",
            "religious_beliefs",
            "health",
            "financial",
            "location",
            "minor_data",
        ]
        
        self.stats = {
            "total_assessments": 0,
            "assessments_by_status": defaultdict(int),
            "assessments_by_risk": defaultdict(int),
            "approved_count": 0,
            "rejected_count": 0,
        }
        
        self._initialized = False
    
    def _init_risk_templates(self) -> List[Dict]:
        return [
            {
                "risk_type": "data_breach",
                "description": "数据泄露风险",
                "default_likelihood": "medium",
                "default_impact": "high",
                "mitigation_templates": [
                    "实施加密存储",
                    "加强访问控制",
                    "部署数据防泄漏系统",
                    "建立应急响应机制",
                ],
            },
            {
                "risk_type": "over_collection",
                "description": "过度收集风险",
                "default_likelihood": "medium",
                "default_impact": "medium",
                "mitigation_templates": [
                    "实施最小必要原则审查",
                    "建立数据收集审批流程",
                    "定期审查数据收集范围",
                ],
            },
            {
                "risk_type": "unauthorized_use",
                "description": "未授权使用风险",
                "default_likelihood": "low",
                "default_impact": "high",
                "mitigation_templates": [
                    "建立数据处理目的限制机制",
                    "实施用途审计",
                    "获取用户明确授权",
                ],
            },
            {
                "risk_type": "cross_border_transfer",
                "description": "数据跨境传输风险",
                "default_likelihood": "low",
                "default_impact": "high",
                "mitigation_templates": [
                    "完成安全评估",
                    "签订标准合同",
                    "获取用户单独同意",
                    "确保目的地国家保护水平",
                ],
            },
            {
                "risk_type": "automated_decision",
                "description": "自动化决策风险",
                "default_likelihood": "medium",
                "default_impact": "medium",
                "mitigation_templates": [
                    "提供人工干预选项",
                    "建立申诉机制",
                    "确保决策透明可解释",
                ],
            },
            {
                "risk_type": "minor_data",
                "description": "未成年人数据处理风险",
                "default_likelihood": "medium",
                "default_impact": "high",
                "mitigation_templates": [
                    "实施年龄验证",
                    "获取监护人同意",
                    "制定专门保护措施",
                    "限制数据收集范围",
                ],
            },
        ]
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def create_assessment(
        self,
        feature_name: str,
        feature_description: str,
        trigger_reason: str,
        processing_activities: Optional[List[Dict]] = None,
    ) -> PIAssessment:
        assessment = PIAssessment(
            feature_name=feature_name,
            feature_description=feature_description,
            trigger_reason=trigger_reason,
            status=AssessmentStatus.IN_PROGRESS.value,
        )
        
        if processing_activities:
            for activity_data in processing_activities:
                activity = DataProcessingActivity(
                    name=activity_data.get("name", ""),
                    description=activity_data.get("description", ""),
                    data_types=activity_data.get("data_types", []),
                    data_sources=activity_data.get("data_sources", []),
                    purposes=activity_data.get("purposes", []),
                    legal_basis=activity_data.get("legal_basis", ""),
                    recipients=activity_data.get("recipients", []),
                    retention_period=activity_data.get("retention_period", ""),
                    cross_border=activity_data.get("cross_border", False),
                    cross_border_destination=activity_data.get("cross_border_destination", ""),
                    automated_decision_making=activity_data.get("automated_decision_making", False),
                    sensitive_data=self._check_sensitive_data(activity_data.get("data_types", [])),
                )
                assessment.processing_activities.append(activity)
        
        self.assessments[assessment.assessment_id] = assessment
        self.stats["total_assessments"] += 1
        self.stats["assessments_by_status"][assessment.status] += 1
        
        return assessment
    
    def _check_sensitive_data(self, data_types: List[str]) -> bool:
        return any(dt in self.sensitive_data_types for dt in data_types)
    
    async def identify_risks(
        self,
        assessment_id: str,
    ) -> List[PrivacyRisk]:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return []
        
        risks = []
        
        for activity in assessment.processing_activities:
            if activity.sensitive_data:
                risk = PrivacyRisk(
                    risk_type="sensitive_data_processing",
                    description=f"处理敏感个人信息: {activity.data_types}",
                    likelihood="medium",
                    impact="high",
                    risk_level=RiskLevel.HIGH.value,
                    affected_data_types=activity.data_types,
                    mitigation_measures=[
                        "获取单独同意",
                        "告知处理必要性和影响",
                        "采取更严格的保护措施",
                    ],
                )
                risks.append(risk)
            
            if activity.cross_border:
                risk = PrivacyRisk(
                    risk_type="cross_border_transfer",
                    description=f"数据跨境传输至: {activity.cross_border_destination}",
                    likelihood="medium",
                    impact="high",
                    risk_level=RiskLevel.HIGH.value,
                    affected_data_types=activity.data_types,
                    mitigation_measures=[
                        "完成网信办安全评估或签订标准合同",
                        "获取用户单独同意",
                        "确保目的地国家数据保护水平",
                    ],
                )
                risks.append(risk)
            
            if activity.automated_decision_making:
                risk = PrivacyRisk(
                    risk_type="automated_decision",
                    description="涉及自动化决策",
                    likelihood="medium",
                    impact="medium",
                    risk_level=RiskLevel.MEDIUM.value,
                    affected_data_types=activity.data_types,
                    mitigation_measures=[
                        "提供人工干预选项",
                        "建立申诉机制",
                        "确保决策透明可解释",
                    ],
                )
                risks.append(risk)
            
            if "minor_data" in activity.data_types:
                risk = PrivacyRisk(
                    risk_type="minor_data",
                    description="处理未成年人个人信息",
                    likelihood="medium",
                    impact="high",
                    risk_level=RiskLevel.HIGH.value,
                    affected_data_types=["minor_data"],
                    mitigation_measures=[
                        "实施年龄验证",
                        "获取监护人同意",
                        "制定专门保护措施",
                    ],
                )
                risks.append(risk)
            
            if len(activity.data_types) > 5:
                risk = PrivacyRisk(
                    risk_type="over_collection",
                    description=f"收集多种类型数据: {len(activity.data_types)}种",
                    likelihood="medium",
                    impact="medium",
                    risk_level=RiskLevel.MEDIUM.value,
                    affected_data_types=activity.data_types,
                    mitigation_measures=[
                        "审查数据收集必要性",
                        "实施最小必要原则",
                    ],
                )
                risks.append(risk)
        
        assessment.risks = risks
        assessment.updated_at = datetime.utcnow().isoformat()
        
        return risks
    
    async def evaluate_necessity(
        self,
        assessment_id: str,
    ) -> Dict:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return {"error": "评估不存在"}
        
        necessity_check = {
            "passed": True,
            "details": [],
        }
        
        for activity in assessment.processing_activities:
            if not activity.purposes:
                necessity_check["passed"] = False
                necessity_check["details"].append({
                    "activity": activity.name,
                    "issue": "未明确处理目的",
                })
            
            if not activity.legal_basis:
                necessity_check["passed"] = False
                necessity_check["details"].append({
                    "activity": activity.name,
                    "issue": "未明确法律依据",
                })
            
            if len(activity.data_types) > 10:
                necessity_check["details"].append({
                    "activity": activity.name,
                    "issue": "数据类型过多，建议审查必要性",
                    "warning": True,
                })
        
        assessment.necessity_check = necessity_check
        return necessity_check
    
    async def evaluate_proportionality(
        self,
        assessment_id: str,
    ) -> Dict:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return {"error": "评估不存在"}
        
        proportionality_check = {
            "passed": True,
            "details": [],
        }
        
        for activity in assessment.processing_activities:
            if activity.sensitive_data:
                proportionality_check["details"].append({
                    "activity": activity.name,
                    "finding": "处理敏感个人信息，需要更高保护标准",
                    "requires_enhanced_protection": True,
                })
            
            if activity.cross_border:
                proportionality_check["details"].append({
                    "activity": activity.name,
                    "finding": "数据跨境传输，需要额外合规措施",
                    "requires_cross_border_compliance": True,
                })
            
            if not activity.retention_period:
                proportionality_check["passed"] = False
                proportionality_check["details"].append({
                    "activity": activity.name,
                    "issue": "未明确数据保留期限",
                })
        
        assessment.proportionality_check = proportionality_check
        return proportionality_check
    
    async def calculate_overall_risk(
        self,
        assessment_id: str,
    ) -> str:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return RiskLevel.LOW.value
        
        if not assessment.risks:
            assessment.overall_risk_level = RiskLevel.LOW.value
            return assessment.overall_risk_level
        
        high_count = sum(1 for r in assessment.risks if r.risk_level == RiskLevel.HIGH.value)
        medium_count = sum(1 for r in assessment.risks if r.risk_level == RiskLevel.MEDIUM.value)
        
        if high_count > 0:
            assessment.overall_risk_level = RiskLevel.HIGH.value
        elif medium_count > 2:
            assessment.overall_risk_level = RiskLevel.HIGH.value
        elif medium_count > 0:
            assessment.overall_risk_level = RiskLevel.MEDIUM.value
        else:
            assessment.overall_risk_level = RiskLevel.LOW.value
        
        self.stats["assessments_by_risk"][assessment.overall_risk_level] += 1
        
        return assessment.overall_risk_level
    
    async def generate_recommendations(
        self,
        assessment_id: str,
    ) -> List[str]:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return []
        
        recommendations = []
        
        if assessment.overall_risk_level == RiskLevel.HIGH.value:
            recommendations.append("建议在上线前完成所有高风险缓解措施")
            recommendations.append("建议进行合规官审批")
        
        for risk in assessment.risks:
            recommendations.extend(risk.mitigation_measures)
        
        if not assessment.necessity_check.get("passed", True):
            recommendations.append("完善数据处理目的和法律依据说明")
        
        if not assessment.proportionality_check.get("passed", True):
            recommendations.append("明确数据保留期限")
        
        assessment.recommendations = list(set(recommendations))
        return assessment.recommendations
    
    async def complete_assessment(
        self,
        assessment_id: str,
    ) -> PIAssessment:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return None
        
        await self.identify_risks(assessment_id)
        await self.evaluate_necessity(assessment_id)
        await self.evaluate_proportionality(assessment_id)
        await self.calculate_overall_risk(assessment_id)
        await self.generate_recommendations(assessment_id)
        
        assessment.summary = self._generate_summary(assessment)
        assessment.status = AssessmentStatus.PENDING_APPROVAL.value
        
        self.stats["assessments_by_status"][AssessmentStatus.IN_PROGRESS.value] -= 1
        self.stats["assessments_by_status"][AssessmentStatus.PENDING_APPROVAL.value] += 1
        
        assessment.updated_at = datetime.utcnow().isoformat()
        
        return assessment
    
    def _generate_summary(self, assessment: PIAssessment) -> str:
        summary = f"功能'{assessment.feature_name}'隐私影响评估："
        summary += f"共识别{len(assessment.risks)}项风险，"
        summary += f"整体风险等级为{assessment.overall_risk_level}。"
        
        if assessment.overall_risk_level == RiskLevel.HIGH.value:
            summary += "建议在完成风险缓解措施后上线。"
        elif assessment.overall_risk_level == RiskLevel.MEDIUM.value:
            summary += "建议关注中等风险并实施相应措施。"
        else:
            summary += "风险可控，可以上线。"
        
        return summary
    
    async def approve_assessment(
        self,
        assessment_id: str,
        approver: str,
        conditions: Optional[List[str]] = None,
    ) -> bool:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return False
        
        assessment.status = AssessmentStatus.APPROVED.value
        assessment.approver = approver
        assessment.approved_at = datetime.utcnow().isoformat()
        assessment.approval_conditions = conditions or []
        
        self.stats["assessments_by_status"][AssessmentStatus.PENDING_APPROVAL.value] -= 1
        self.stats["assessments_by_status"][AssessmentStatus.APPROVED.value] += 1
        self.stats["approved_count"] += 1
        
        return True
    
    async def reject_assessment(
        self,
        assessment_id: str,
        reason: str,
    ) -> bool:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return False
        
        assessment.status = AssessmentStatus.REJECTED.value
        assessment.recommendations.append(f"拒绝原因: {reason}")
        
        self.stats["assessments_by_status"][AssessmentStatus.PENDING_APPROVAL.value] -= 1
        self.stats["assessments_by_status"][AssessmentStatus.REJECTED.value] += 1
        self.stats["rejected_count"] += 1
        
        return True
    
    async def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return None
        
        return {
            "assessment_id": assessment.assessment_id,
            "feature_name": assessment.feature_name,
            "status": assessment.status,
            "overall_risk_level": assessment.overall_risk_level,
            "risk_count": len(assessment.risks),
            "processing_activities_count": len(assessment.processing_activities),
            "summary": assessment.summary,
            "recommendations": assessment.recommendations,
            "created_at": assessment.created_at,
            "approved_at": assessment.approved_at,
        }
    
    async def get_pending_approvals(self) -> List[Dict]:
        return [
            await self.get_assessment(aid)
            for aid, a in self.assessments.items()
            if a.status == AssessmentStatus.PENDING_APPROVAL.value
        ]
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_assessments": self.stats["total_assessments"],
            "assessments_by_status": dict(self.stats["assessments_by_status"]),
            "assessments_by_risk": dict(self.stats["assessments_by_risk"]),
            "approved_count": self.stats["approved_count"],
            "rejected_count": self.stats["rejected_count"],
        }
