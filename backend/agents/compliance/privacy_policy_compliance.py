"""
隐私政策合规检查智能体
检查平台隐私政策是否符合法律法规要求
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PolicyRequirement(str, Enum):
    DATA_COLLECTION_PURPOSE = "data_collection_purpose"
    CONSENT_MECHANISM = "consent_mechanism"
    DATA_MINIMIZATION = "data_minimization"
    STORAGE_LIMITATION = "storage_limitation"
    DATA_SUBJECT_RIGHTS = "data_subject_rights"
    DATA_SHARING_DISCLOSURE = "data_sharing_disclosure"
    SECURITY_MEASURES = "security_measures"
    CROSS_BORDER_TRANSFER = "cross_border_transfer"
    COOKIE_POLICY = "cookie_policy"
    CHILDREN_PROTECTION = "children_protection"
    DATA_BREACH_NOTIFICATION = "data_breach_notification"
    THIRD_PARTY_SHARING = "third_party_sharing"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    NOT_FOUND = "not_found"


class PolicyCheckResult(BaseModel):
    check_id: str = Field(default_factory=lambda: str(uuid4()))
    requirement: PolicyRequirement
    status: ComplianceStatus
    score: float = 0.0
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.now)


class PolicyDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    version: str = "1.0"
    content: str
    sections: Dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    effective_date: Optional[datetime] = None


class LegalRequirement(BaseModel):
    requirement_id: str
    law_name: str
    article: str
    requirement_type: PolicyRequirement
    description: str
    mandatory: bool = True
    check_keywords: List[str] = Field(default_factory=list)


class PolicyAnalyzer:
    KEYWORD_MAPPINGS = {
        PolicyRequirement.DATA_COLLECTION_PURPOSE: [
            "收集目的", "使用目的", "数据处理目的", "purpose",
            "收集信息", "信息收集"
        ],
        PolicyRequirement.CONSENT_MECHANISM: [
            "同意", "授权", "consent", "opt-in", "opt-out",
            "用户同意", "明示同意"
        ],
        PolicyRequirement.DATA_MINIMIZATION: [
            "最小化", "必要", "最小范围", "最小必要",
            "仅限于", "限于"
        ],
        PolicyRequirement.STORAGE_LIMITATION: [
            "存储期限", "保存期限", "保留时间", "存储时间",
            "删除", "销毁"
        ],
        PolicyRequirement.DATA_SUBJECT_RIGHTS: [
            "用户权利", "数据主体权利", "查询", "更正", "删除",
            "撤回同意", "可携带", "投诉"
        ],
        PolicyRequirement.DATA_SHARING_DISCLOSURE: [
            "共享", "披露", "第三方", "对外提供",
            "合作方", "关联公司"
        ],
        PolicyRequirement.SECURITY_MEASURES: [
            "安全措施", "加密", "访问控制", "安全保护",
            "技术措施", "管理措施"
        ],
        PolicyRequirement.CROSS_BORDER_TRANSFER: [
            "跨境", "境外", "国际传输", "出境",
            "数据出境"
        ],
        PolicyRequirement.COOKIE_POLICY: [
            "cookie", "cookies", "追踪", "本地存储",
            "浏览器"
        ],
        PolicyRequirement.CHILDREN_PROTECTION: [
            "未成年人", "儿童", "14周岁", "18周岁",
            "监护人"
        ],
        PolicyRequirement.DATA_BREACH_NOTIFICATION: [
            "数据泄露", "安全事件", "通知", "报告",
            "应急响应"
        ],
    }
    
    def analyze(self, policy_content: str) -> Dict[str, Any]:
        sections = self._extract_sections(policy_content)
        
        coverage = {}
        for requirement, keywords in self.KEYWORD_MAPPINGS.items():
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in policy_content.lower():
                    found_keywords.append(keyword)
            
            coverage[requirement.value] = {
                "found_keywords": found_keywords,
                "coverage_ratio": len(found_keywords) / len(keywords) if keywords else 0
            }
        
        return {
            "sections": sections,
            "coverage": coverage,
            "total_length": len(policy_content)
        }
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        sections = {}
        
        section_patterns = [
            (r'第[一二三四五六七八九十]+[章节条款][^\n]*\n([\s\S]*?)(?=第[一二三四五六七八九十]+[章节条款]|$)', 'numbered'),
            (r'(\d+\.?\s*[^\n]+)\n([\s\S]*?)(?=\d+\.?\s*[^\n]+\n|$)', 'numbered_items'),
        ]
        
        lines = content.split('\n')
        current_section = "main"
        current_content = []
        
        for line in lines:
            if re.match(r'^[一二三四五六七八九十]+[、.]', line) or re.match(r'^\d+[、.]', line):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.strip()[:50]
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections


class PrivacyPolicyComplianceAgent:
    LEGAL_REQUIREMENTS = [
        LegalRequirement(
            requirement_id="pipl_art6",
            law_name="个人信息保护法",
            article="第六条",
            requirement_type=PolicyRequirement.DATA_COLLECTION_PURPOSE,
            description="应当具有明确、合理的目的",
            mandatory=True,
            check_keywords=["目的", "明确", "合理"]
        ),
        LegalRequirement(
            requirement_id="pipl_art13",
            law_name="个人信息保护法",
            article="第十三条",
            requirement_type=PolicyRequirement.CONSENT_MECHANISM,
            description="处理个人信息应当取得个人同意",
            mandatory=True,
            check_keywords=["同意", "授权", "告知"]
        ),
        LegalRequirement(
            requirement_id="pipl_art6_min",
            law_name="个人信息保护法",
            article="第六条",
            requirement_type=PolicyRequirement.DATA_MINIMIZATION,
            description="应当遵循最小必要原则",
            mandatory=True,
            check_keywords=["最小", "必要", "限于"]
        ),
        LegalRequirement(
            requirement_id="pipl_art19",
            law_name="个人信息保护法",
            article="第十九条",
            requirement_type=PolicyRequirement.STORAGE_LIMITATION,
            description="应当明确存储期限",
            mandatory=True,
            check_keywords=["存储期限", "保存期限", "删除"]
        ),
        LegalRequirement(
            requirement_id="pipl_art44_47",
            law_name="个人信息保护法",
            article="第四十四条至四十七条",
            requirement_type=PolicyRequirement.DATA_SUBJECT_RIGHTS,
            description="保障个人知情权、决定权、查阅复制权、更正删除权",
            mandatory=True,
            check_keywords=["权利", "查询", "更正", "删除"]
        ),
        LegalRequirement(
            requirement_id="pipl_art23",
            law_name="个人信息保护法",
            article="第二十三条",
            requirement_type=PolicyRequirement.THIRD_PARTY_SHARING,
            description="向他人提供个人信息应当告知并取得同意",
            mandatory=True,
            check_keywords=["第三方", "共享", "提供"]
        ),
        LegalRequirement(
            requirement_id="pipl_art38_43",
            law_name="个人信息保护法",
            article="第三十八条至四十三条",
            requirement_type=PolicyRequirement.CROSS_BORDER_TRANSFER,
            description="跨境提供个人信息需满足特定条件",
            mandatory=True,
            check_keywords=["跨境", "出境", "境外"]
        ),
        LegalRequirement(
            requirement_id="pipl_art51",
            law_name="个人信息保护法",
            article="第五十一条",
            requirement_type=PolicyRequirement.SECURITY_MEASURES,
            description="应当采取必要的安全保护措施",
            mandatory=True,
            check_keywords=["安全", "加密", "保护"]
        ),
    ]
    
    def __init__(
        self,
        agent_id: str,
        name: str = "PrivacyPolicyCompliance",
        regulation_parser: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.regulation_parser = regulation_parser
        
        self.analyzer = PolicyAnalyzer()
        
        self.policies: Dict[str, PolicyDocument] = {}
        self.check_results: List[PolicyCheckResult] = []
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"PrivacyPolicyComplianceAgent {self.agent_id} initialized")
    
    async def register_policy(
        self,
        name: str,
        content: str,
        version: str = "1.0",
        effective_date: Optional[datetime] = None
    ) -> str:
        analysis = self.analyzer.analyze(content)
        
        policy = PolicyDocument(
            name=name,
            version=version,
            content=content,
            sections=analysis["sections"],
            effective_date=effective_date
        )
        
        self.policies[policy.document_id] = policy
        
        return policy.document_id
    
    async def check_compliance(
        self,
        policy_id: str,
        requirements: Optional[List[PolicyRequirement]] = None
    ) -> List[PolicyCheckResult]:
        policy = self.policies.get(policy_id)
        
        if not policy:
            return []
        
        if not requirements:
            requirements = list(PolicyRequirement)
        
        results = []
        analysis = self.analyzer.analyze(policy.content)
        
        for requirement in requirements:
            result = await self._check_requirement(policy, requirement, analysis)
            results.append(result)
            self.check_results.append(result)
        
        return results
    
    async def _check_requirement(
        self,
        policy: PolicyDocument,
        requirement: PolicyRequirement,
        analysis: Dict[str, Any]
    ) -> PolicyCheckResult:
        coverage = analysis["coverage"].get(requirement.value, {})
        found_keywords = coverage.get("found_keywords", [])
        coverage_ratio = coverage.get("coverage_ratio", 0)
        
        findings = []
        recommendations = []
        evidence = []
        
        legal_reqs = [
            lr for lr in self.LEGAL_REQUIREMENTS
            if lr.requirement_type == requirement
        ]
        
        for lr in legal_reqs:
            keyword_matches = [
                kw for kw in lr.check_keywords
                if kw.lower() in policy.content.lower()
            ]
            
            if keyword_matches:
                evidence.append(f"发现关键词: {', '.join(keyword_matches)}")
            else:
                findings.append(f"未找到法律要求的关键内容: {lr.description}")
                recommendations.append(f"建议添加: {lr.law_name} {lr.article} 要求的内容")
        
        if coverage_ratio >= 0.8:
            status = ComplianceStatus.COMPLIANT
            score = coverage_ratio
        elif coverage_ratio >= 0.5:
            status = ComplianceStatus.PARTIAL
            score = coverage_ratio
            recommendations.append(f"建议完善{requirement.value}相关内容")
        elif coverage_ratio > 0:
            status = ComplianceStatus.PARTIAL
            score = coverage_ratio
            recommendations.append(f"需要补充{requirement.value}相关内容")
        else:
            status = ComplianceStatus.NOT_FOUND
            score = 0.0
            recommendations.append(f"缺少{requirement.value}相关内容，需要添加")
        
        return PolicyCheckResult(
            requirement=requirement,
            status=status,
            score=score,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence
        )
    
    async def get_compliance_summary(
        self,
        policy_id: str
    ) -> Dict[str, Any]:
        policy = self.policies.get(policy_id)
        
        if not policy:
            return {"error": "Policy not found"}
        
        results = await self.check_compliance(policy_id)
        
        by_status = {}
        total_score = 0.0
        
        for result in results:
            status = result.status.value
            by_status[status] = by_status.get(status, 0) + 1
            total_score += result.score
        
        avg_score = total_score / len(results) if results else 0.0
        
        compliant_count = by_status.get(ComplianceStatus.COMPLIANT.value, 0)
        compliance_rate = compliant_count / len(results) if results else 0.0
        
        return {
            "policy_id": policy_id,
            "policy_name": policy.name,
            "total_requirements": len(results),
            "by_status": by_status,
            "average_score": avg_score,
            "compliance_rate": compliance_rate,
            "checked_at": datetime.now().isoformat()
        }
    
    async def compare_policies(
        self,
        policy_id_1: str,
        policy_id_2: str
    ) -> Dict[str, Any]:
        policy1 = self.policies.get(policy_id_1)
        policy2 = self.policies.get(policy_id_2)
        
        if not policy1 or not policy2:
            return {"error": "One or both policies not found"}
        
        results1 = await self.check_compliance(policy_id_1)
        results2 = await self.check_compliance(policy_id_2)
        
        comparison = {}
        
        for r1, r2 in zip(results1, results2):
            req = r1.requirement.value
            comparison[req] = {
                "policy1_score": r1.score,
                "policy1_status": r1.status.value,
                "policy2_score": r2.score,
                "policy2_status": r2.status.value,
                "difference": r2.score - r1.score
            }
        
        return {
            "policy1": {"id": policy_id_1, "name": policy1.name},
            "policy2": {"id": policy_id_2, "name": policy2.name},
            "comparison": comparison
        }
    
    async def suggest_improvements(
        self,
        policy_id: str
    ) -> List[Dict[str, Any]]:
        results = await self.check_compliance(policy_id)
        
        improvements = []
        
        for result in results:
            if result.status != ComplianceStatus.COMPLIANT:
                improvements.append({
                    "requirement": result.requirement.value,
                    "current_score": result.score,
                    "findings": result.findings,
                    "recommendations": result.recommendations,
                    "priority": "high" if result.score < 0.3 else "medium"
                })
        
        improvements.sort(key=lambda x: x["current_score"])
        
        return improvements
    
    async def get_policy(self, policy_id: str) -> Optional[PolicyDocument]:
        return self.policies.get(policy_id)
    
    async def list_policies(self) -> List[Dict[str, Any]]:
        return [
            {
                "document_id": p.document_id,
                "name": p.name,
                "version": p.version,
                "last_updated": p.last_updated.isoformat(),
                "effective_date": p.effective_date.isoformat() if p.effective_date else None
            }
            for p in self.policies.values()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        by_requirement = {}
        for result in self.check_results:
            req = result.requirement.value
            if req not in by_requirement:
                by_requirement[req] = {"total": 0, "compliant": 0}
            by_requirement[req]["total"] += 1
            if result.status == ComplianceStatus.COMPLIANT:
                by_requirement[req]["compliant"] += 1
        
        return {
            "total_policies": len(self.policies),
            "total_checks": len(self.check_results),
            "by_requirement": by_requirement
        }
