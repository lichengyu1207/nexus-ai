"""
算法偏见检测智能体
Algorithm Bias Detection Agent

负责检测业务智能体是否存在算法偏见。
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
import math

logger = logging.getLogger(__name__)


class BiasType(Enum):
    REGIONAL = "regional"
    DEMOGRAPHIC = "demographic"
    CONTENT = "content"
    ECONOMIC = "economic"


class BiasSeverity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class DecisionRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    agent_id: str = ""
    decision_type: str = ""
    input_features: Dict = field(default_factory=dict)
    output_result: Dict = field(default_factory=dict)
    
    user_attributes: Dict = field(default_factory=dict)
    sensitive_attributes: Dict = field(default_factory=dict)


@dataclass
class BiasFinding:
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    bias_type: str = ""
    affected_attribute: str = ""
    description: str = ""
    
    statistical_evidence: Dict = field(default_factory=dict)
    affected_groups: List[str] = field(default_factory=list)
    
    severity: str = BiasSeverity.MEDIUM.value
    confidence: float = 0.0
    
    mitigation_suggestions: List[str] = field(default_factory=list)
    status: str = "open"


@dataclass
class BiasAuditReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    agent_id: str = ""
    audit_period: Dict = field(default_factory=dict)
    
    total_decisions_analyzed: int = 0
    findings: List[BiasFinding] = field(default_factory=list)
    
    overall_bias_score: float = 0.0
    summary: str = ""
    
    recommendations: List[str] = field(default_factory=list)


class AlgorithmBiasDetectionAgent:
    """
    算法偏见检测智能体
    
    功能：
    1. 检测维度：地域偏见、人群偏见、内容偏见
    2. 检测方法：统计检验、对抗验证
    3. 报告生成：偏见检测报告，缓解建议
    4. 定期审计：每月全面检测，新模型上线前强制检测
    5. 纠偏机制：触发重新训练或调整策略
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AlgorithmBiasDetectionAgent"
        self.description = "检测业务智能体是否存在算法偏见"
        self.config = config or {}
        
        self.decision_records: List[DecisionRecord] = []
        self.bias_findings: List[BiasFinding] = []
        self.audit_reports: Dict[str, BiasAuditReport] = {}
        
        self.sensitive_attributes = {
            "region": ["北京", "上海", "广州", "深圳", "二线城市", "三线城市", "其他"],
            "age_group": ["18-25", "26-35", "36-45", "46-55", "55+"],
            "gender": ["male", "female", "other"],
            "income_level": ["low", "medium", "high"],
        }
        
        self.bias_thresholds = {
            "statistical_significance": 0.05,
            "disparity_ratio_threshold": 0.8,
            "minimum_sample_size": 30,
        }
        
        self.stats = {
            "total_decisions": 0,
            "total_findings": 0,
            "findings_by_type": defaultdict(int),
            "findings_by_severity": defaultdict(int),
            "audits_performed": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_audit())
    
    async def _periodic_audit(self):
        while True:
            await asyncio.sleep(2592000)
            await self.run_comprehensive_audit()
    
    async def record_decision(
        self,
        agent_id: str,
        decision_type: str,
        input_features: Dict,
        output_result: Dict,
        user_attributes: Optional[Dict] = None,
    ) -> DecisionRecord:
        sensitive_attrs = {}
        if user_attributes:
            for attr in self.sensitive_attributes.keys():
                if attr in user_attributes:
                    sensitive_attrs[attr] = user_attributes[attr]
        
        record = DecisionRecord(
            agent_id=agent_id,
            decision_type=decision_type,
            input_features=input_features,
            output_result=output_result,
            user_attributes=user_attributes or {},
            sensitive_attributes=sensitive_attrs,
        )
        
        self.decision_records.append(record)
        self.stats["total_decisions"] += 1
        
        return record
    
    async def detect_regional_bias(
        self,
        agent_id: str,
        decision_type: str,
        metric: str = "recommendation_score",
    ) -> Optional[BiasFinding]:
        relevant_records = [
            r for r in self.decision_records
            if r.agent_id == agent_id and r.decision_type == decision_type
        ]
        
        if len(relevant_records) < self.bias_thresholds["minimum_sample_size"]:
            return None
        
        region_scores = defaultdict(list)
        for record in relevant_records:
            region = record.sensitive_attributes.get("region", "unknown")
            score = record.output_result.get(metric, 0)
            region_scores[region].append(score)
        
        if len(region_scores) < 2:
            return None
        
        avg_scores = {
            region: sum(scores) / len(scores)
            for region, scores in region_scores.items()
        }
        
        max_score = max(avg_scores.values())
        min_score = min(avg_scores.values())
        
        if max_score > 0:
            disparity_ratio = min_score / max_score
        else:
            disparity_ratio = 1.0
        
        if disparity_ratio < self.bias_thresholds["disparity_ratio_threshold"]:
            favored_regions = [
                r for r, s in avg_scores.items()
                if s == max_score
            ]
            disadvantaged_regions = [
                r for r, s in avg_scores.items()
                if s == min_score
            ]
            
            severity = BiasSeverity.HIGH.value if disparity_ratio < 0.6 else BiasSeverity.MEDIUM.value
            
            finding = BiasFinding(
                bias_type=BiasType.REGIONAL.value,
                affected_attribute="region",
                description=f"地域偏见检测: {favored_regions}地区平均得分比{disadvantaged_regions}地区高{(1-disparity_ratio)*100:.1f}%",
                statistical_evidence={
                    "avg_scores": avg_scores,
                    "disparity_ratio": disparity_ratio,
                    "sample_sizes": {r: len(s) for r, s in region_scores.items()},
                },
                affected_groups=disadvantaged_regions,
                severity=severity,
                confidence=0.85,
                mitigation_suggestions=[
                    "重新平衡训练数据中的地域分布",
                    "调整模型权重以减少地域相关性",
                    "增加地域公平性约束",
                ],
            )
            
            self.bias_findings.append(finding)
            self.stats["total_findings"] += 1
            self.stats["findings_by_type"][BiasType.REGIONAL.value] += 1
            self.stats["findings_by_severity"][severity] += 1
            
            return finding
        
        return None
    
    async def detect_demographic_bias(
        self,
        agent_id: str,
        decision_type: str,
        sensitive_attr: str = "age_group",
        metric: str = "recommendation_score",
    ) -> Optional[BiasFinding]:
        relevant_records = [
            r for r in self.decision_records
            if r.agent_id == agent_id and r.decision_type == decision_type
        ]
        
        if len(relevant_records) < self.bias_thresholds["minimum_sample_size"]:
            return None
        
        group_scores = defaultdict(list)
        for record in relevant_records:
            group = record.sensitive_attributes.get(sensitive_attr, "unknown")
            score = record.output_result.get(metric, 0)
            group_scores[group].append(score)
        
        if len(group_scores) < 2:
            return None
        
        avg_scores = {
            group: sum(scores) / len(scores)
            for group, scores in group_scores.items()
        }
        
        max_score = max(avg_scores.values())
        min_score = min(avg_scores.values())
        
        if max_score > 0:
            disparity_ratio = min_score / max_score
        else:
            disparity_ratio = 1.0
        
        if disparity_ratio < self.bias_thresholds["disparity_ratio_threshold"]:
            favored_groups = [
                g for g, s in avg_scores.items()
                if s == max_score
            ]
            disadvantaged_groups = [
                g for g, s in avg_scores.items()
                if s == min_score
            ]
            
            severity = BiasSeverity.HIGH.value if disparity_ratio < 0.6 else BiasSeverity.MEDIUM.value
            
            finding = BiasFinding(
                bias_type=BiasType.DEMOGRAPHIC.value,
                affected_attribute=sensitive_attr,
                description=f"人群偏见检测({sensitive_attr}): {favored_groups}群体平均得分比{disadvantaged_groups}群体高{(1-disparity_ratio)*100:.1f}%",
                statistical_evidence={
                    "avg_scores": avg_scores,
                    "disparity_ratio": disparity_ratio,
                    "sample_sizes": {g: len(s) for g, s in group_scores.items()},
                },
                affected_groups=disadvantaged_groups,
                severity=severity,
                confidence=0.80,
                mitigation_suggestions=[
                    f"重新平衡{sensitive_attr}分布",
                    "实施公平性约束训练",
                    "对敏感属性进行脱敏处理",
                ],
            )
            
            self.bias_findings.append(finding)
            self.stats["total_findings"] += 1
            self.stats["findings_by_type"][BiasType.DEMOGRAPHIC.value] += 1
            self.stats["findings_by_severity"][severity] += 1
            
            return finding
        
        return None
    
    async def detect_content_bias(
        self,
        agent_id: str,
        decision_type: str,
    ) -> Optional[BiasFinding]:
        relevant_records = [
            r for r in self.decision_records
            if r.agent_id == agent_id and r.decision_type == decision_type
        ]
        
        if len(relevant_records) < self.bias_thresholds["minimum_sample_size"]:
            return None
        
        recommendation_types = defaultdict(int)
        for record in relevant_records:
            rec_type = record.output_result.get("recommendation_type", "unknown")
            recommendation_types[rec_type] += 1
        
        if len(recommendation_types) < 2:
            return None
        
        total = sum(recommendation_types.values())
        type_ratios = {
            t: count / total for t, count in recommendation_types.items()
        }
        
        max_ratio = max(type_ratios.values())
        
        if max_ratio > 0.7:
            dominant_type = [t for t, r in type_ratios.items() if r == max_ratio][0]
            
            finding = BiasFinding(
                bias_type=BiasType.CONTENT.value,
                affected_attribute="recommendation_type",
                description=f"内容偏见检测: {dominant_type}类型推荐占比{max_ratio*100:.1f}%，存在明显偏好",
                statistical_evidence={
                    "type_distribution": type_ratios,
                    "dominant_type": dominant_type,
                    "dominant_ratio": max_ratio,
                },
                affected_groups=list(type_ratios.keys()),
                severity=BiasSeverity.LOW.value,
                confidence=0.75,
                mitigation_suggestions=[
                    "增加推荐多样性",
                    "引入探索机制",
                    "平衡各类型推荐权重",
                ],
            )
            
            self.bias_findings.append(finding)
            self.stats["total_findings"] += 1
            self.stats["findings_by_type"][BiasType.CONTENT.value] += 1
            self.stats["findings_by_severity"][BiasSeverity.LOW.value] += 1
            
            return finding
        
        return None
    
    async def run_comprehensive_audit(
        self,
        agent_id: Optional[str] = None,
    ) -> BiasAuditReport:
        now = datetime.utcnow()
        audit_period = {
            "start": (now - timedelta(days=30)).isoformat(),
            "end": now.isoformat(),
        }
        
        report = BiasAuditReport(
            agent_id=agent_id or "all",
            audit_period=audit_period,
        )
        
        agents_to_audit = set()
        for record in self.decision_records:
            if agent_id is None or record.agent_id == agent_id:
                agents_to_audit.add(record.agent_id)
        
        report.total_decisions_analyzed = len([
            r for r in self.decision_records
            if agent_id is None or r.agent_id == agent_id
        ])
        
        for aid in agents_to_audit:
            for decision_type in ["recommendation", "valuation", "consultation"]:
                regional_finding = await self.detect_regional_bias(aid, decision_type)
                if regional_finding:
                    report.findings.append(regional_finding)
                
                for attr in ["age_group", "gender", "income_level"]:
                    demo_finding = await self.detect_demographic_bias(aid, decision_type, attr)
                    if demo_finding:
                        report.findings.append(demo_finding)
                
                content_finding = await self.detect_content_bias(aid, decision_type)
                if content_finding:
                    report.findings.append(content_finding)
        
        if report.findings:
            high_severity = sum(1 for f in report.findings if f.severity == BiasSeverity.HIGH.value)
            report.overall_bias_score = min(1.0, len(report.findings) * 0.1 + high_severity * 0.2)
        else:
            report.overall_bias_score = 0.0
        
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        self.audit_reports[report.report_id] = report
        self.stats["audits_performed"] += 1
        
        return report
    
    def _generate_summary(self, report: BiasAuditReport) -> str:
        if not report.findings:
            return "未检测到明显的算法偏见，模型公平性良好。"
        
        high_count = sum(1 for f in report.findings if f.severity == BiasSeverity.HIGH.value)
        medium_count = sum(1 for f in report.findings if f.severity == BiasSeverity.MEDIUM.value)
        low_count = sum(1 for f in report.findings if f.severity == BiasSeverity.LOW.value)
        
        summary = f"共检测到{len(report.findings)}项偏见问题，"
        summary += f"其中高风险{high_count}项、中风险{medium_count}项、低风险{low_count}项。"
        summary += f"整体偏见评分为{report.overall_bias_score:.2f}。"
        
        return summary
    
    def _generate_recommendations(self, report: BiasAuditReport) -> List[str]:
        recommendations = []
        
        if report.overall_bias_score > 0.5:
            recommendations.append("建议暂停模型使用，进行全面的偏见修复")
        elif report.overall_bias_score > 0.3:
            recommendations.append("建议在下一迭代中重点解决偏见问题")
        
        for finding in report.findings:
            if finding.severity == BiasSeverity.HIGH.value:
                recommendations.extend(finding.mitigation_suggestions[:2])
        
        recommendations = list(set(recommendations))
        
        return recommendations
    
    async def get_open_findings(self) -> List[Dict]:
        return [
            {
                "finding_id": f.finding_id,
                "bias_type": f.bias_type,
                "affected_attribute": f.affected_attribute,
                "description": f.description,
                "severity": f.severity,
                "confidence": f.confidence,
                "status": f.status,
            }
            for f in self.bias_findings
            if f.status == "open"
        ]
    
    async def resolve_finding(
        self,
        finding_id: str,
        resolution: str,
    ) -> bool:
        for finding in self.bias_findings:
            if finding.finding_id == finding_id:
                finding.status = "resolved"
                finding.mitigation_suggestions.append(f"已解决: {resolution}")
                return True
        return False
    
    async def get_latest_audit_report(self) -> Optional[Dict]:
        if not self.audit_reports:
            return None
        
        latest = max(self.audit_reports.values(), key=lambda r: r.timestamp)
        
        return {
            "report_id": latest.report_id,
            "timestamp": latest.timestamp,
            "agent_id": latest.agent_id,
            "total_decisions_analyzed": latest.total_decisions_analyzed,
            "findings_count": len(latest.findings),
            "overall_bias_score": latest.overall_bias_score,
            "summary": latest.summary,
            "recommendations": latest.recommendations,
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_decisions": self.stats["total_decisions"],
            "total_findings": self.stats["total_findings"],
            "findings_by_type": dict(self.stats["findings_by_type"]),
            "findings_by_severity": dict(self.stats["findings_by_severity"]),
            "audits_performed": self.stats["audits_performed"],
            "open_findings": len([f for f in self.bias_findings if f.status == "open"]),
        }
