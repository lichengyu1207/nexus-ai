"""
输出溯源与责任声明系统
Output Traceability and Liability Disclaimer System

实现引用标注、责任声明、合规审查、多智能体协同溯源聚合
"""

import hashlib
import json
import time
import uuid
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """数据来源类型"""
    GOVERNMENT_DATA = "government_data"
    THIRD_PARTY_API = "third_party_api"
    USER_UPLOAD = "user_upload"
    AI_GENERATED = "ai_generated"
    WEB_SCRAPING = "web_scraping"
    INTERNAL_DATABASE = "internal_database"
    EXTERNAL_REPORT = "external_report"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleAction(Enum):
    """规则动作"""
    ALLOW = "allow"
    REWRITE = "rewrite"
    WARN = "warn"
    BLOCK = "block"
    REQUIRE_REVIEW = "require_review"


class DisclaimerVersion(Enum):
    """声明版本"""
    V1_GENERAL = "disclaimer_v1"
    V2_INVESTMENT = "disclaimer_v2"
    V3_USER_CONTENT = "disclaimer_v3"
    V4_AI_GENERATED = "disclaimer_v4"
    V5_LEGAL = "disclaimer_v5"


@dataclass
class DataSource:
    """数据来源"""
    source_id: str
    source_type: SourceType
    name: str
    retrieved_at: datetime
    data_fingerprint: str
    confidence: float = 0.8
    url: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "type": self.source_type.value,
            "name": self.name,
            "retrieved_at": self.retrieved_at.isoformat(),
            "data_fingerprint": self.data_fingerprint[:16],
            "confidence": self.confidence,
            "url": self.url,
            "description": self.description
        }


@dataclass
class OutputTraceability:
    """输出溯源信息"""
    output_id: str
    timestamp: datetime
    agent_id: str
    sources: List[DataSource]
    disclaimer_version: str
    risk_level: RiskLevel
    compliance_passed: bool
    review_required: bool
    warnings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_id": self.output_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "sources": [s.to_dict() for s in self.sources],
            "disclaimer": self.disclaimer_version,
            "risk_level": self.risk_level.value,
            "compliance_passed": self.compliance_passed,
            "review_required": self.review_required,
            "warnings": self.warnings
        }


@dataclass
class ComplianceRule:
    """合规规则"""
    rule_id: str
    name: str
    description: str
    patterns: List[str]
    action: RuleAction
    disclaimer_required: Optional[str] = None
    rewrite_template: str = ""
    severity: RiskLevel = RiskLevel.MEDIUM


@dataclass
class DisclaimerTemplate:
    """声明模板"""
    version: str
    title: str
    content: str
    applicable_scenarios: List[str]
    legal_basis: List[str]


class SourceRegistry:
    """来源注册表"""
    
    def __init__(self):
        self.registered_sources: Dict[str, DataSource] = {}
        self.source_type_index: Dict[SourceType, Set[str]] = defaultdict(set)
        self.stats = {
            "total_registered": 0,
            "by_type": defaultdict(int),
        }
    
    def register_source(
        self,
        source_type: SourceType,
        name: str,
        data: Any = None,
        confidence: float = 0.8,
        url: str = "",
        description: str = "",
        metadata: Dict[str, Any] = None
    ) -> DataSource:
        """注册数据来源"""
        source_id = f"src_{source_type.value}_{uuid.uuid4().hex[:8]}"
        
        data_fingerprint = ""
        if data:
            if isinstance(data, str):
                data_fingerprint = hashlib.sha256(data.encode()).hexdigest()
            elif isinstance(data, dict):
                data_fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            else:
                data_fingerprint = hashlib.sha256(str(data).encode()).hexdigest()
        
        source = DataSource(
            source_id=source_id,
            source_type=source_type,
            name=name,
            retrieved_at=datetime.now(),
            data_fingerprint=data_fingerprint,
            confidence=confidence,
            url=url,
            description=description,
            metadata=metadata or {}
        )
        
        self.registered_sources[source_id] = source
        self.source_type_index[source_type].add(source_id)
        self.stats["total_registered"] += 1
        self.stats["by_type"][source_type.value] += 1
        
        return source
    
    def get_source(self, source_id: str) -> Optional[DataSource]:
        return self.registered_sources.get(source_id)
    
    def get_sources_by_type(self, source_type: SourceType) -> List[DataSource]:
        source_ids = self.source_type_index.get(source_type, set())
        return [self.registered_sources[sid] for sid in source_ids if sid in self.registered_sources]


class CitationAnnotator:
    """引用标注器"""
    
    def __init__(self):
        self.citation_templates = self._init_citation_templates()
        self.stats = {
            "total_annotations": 0,
            "by_type": defaultdict(int),
        }
    
    def _init_citation_templates(self) -> Dict[SourceType, str]:
        """初始化引用模板"""
        return {
            SourceType.GOVERNMENT_DATA: "[来源:政府公开数据-{name}]",
            SourceType.THIRD_PARTY_API: "[来源:{name}]",
            SourceType.USER_UPLOAD: "[来源:用户上传]",
            SourceType.AI_GENERATED: "[来源:AI分析]",
            SourceType.WEB_SCRAPING: "[来源:网页采集-{name}]",
            SourceType.INTERNAL_DATABASE: "[来源:平台数据库]",
            SourceType.EXTERNAL_REPORT: "[来源:外部报告-{name}]",
        }
    
    def annotate_inline(self, text: str, source: DataSource) -> str:
        """内联标注"""
        template = self.citation_templates.get(source.source_type, "[来源:{name}]")
        citation = template.format(name=source.name)
        
        self.stats["total_annotations"] += 1
        self.stats["by_type"][source.source_type.value] += 1
        
        return f"{text} {citation}"
    
    def annotate_footer(self, sources: List[DataSource]) -> str:
        """页脚标注"""
        if not sources:
            return ""
        
        footer = "\n\n**数据来源：**\n"
        seen_sources = set()
        
        for source in sources:
            source_key = f"{source.source_type.value}_{source.name}"
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)
            
            time_str = source.retrieved_at.strftime("%Y-%m-%d %H:%M")
            confidence_str = f"(可信度: {source.confidence:.0%})" if source.confidence < 1.0 else ""
            
            footer += f"- {source.source_type.value}: {source.name} (采集时间: {time_str}) {confidence_str}\n"
        
        return footer
    
    def create_source_list(self, sources: List[DataSource]) -> List[Dict[str, Any]]:
        """创建来源列表"""
        seen = set()
        unique_sources = []
        
        for source in sources:
            key = f"{source.source_type.value}_{source.name}"
            if key not in seen:
                seen.add(key)
                unique_sources.append(source.to_dict())
        
        return unique_sources


class DisclaimerManager:
    """责任声明管理器"""
    
    def __init__(self):
        self.templates = self._init_templates()
        self.stats = {
            "total_applied": 0,
            "by_version": defaultdict(int),
        }
    
    def _init_templates(self) -> Dict[str, DisclaimerTemplate]:
        """初始化声明模板"""
        return {
            DisclaimerVersion.V1_GENERAL.value: DisclaimerTemplate(
                version=DisclaimerVersion.V1_GENERAL.value,
                title="免责声明",
                content="本平台提供的所有房产信息、价格数据、分析报告均由AI智能体生成，部分数据来源于第三方公开渠道。平台尽力确保数据准确性，但不对信息的完整性、及时性、准确性作出任何保证。用户在使用本平台信息进行决策前，应自行核实并承担相应风险。",
                applicable_scenarios=["general_property_info", "market_data"],
                legal_basis=["电子商务法", "网络安全法"]
            ),
            DisclaimerVersion.V2_INVESTMENT.value: DisclaimerTemplate(
                version=DisclaimerVersion.V2_INVESTMENT.value,
                title="投资风险提示",
                content="房价预测基于历史数据模型，存在不确定性。投资有风险，决策需谨慎。平台不对因使用本信息进行投资决策产生的任何损失承担责任。用户在进行房产投资前，应咨询专业机构并独立评估风险。",
                applicable_scenarios=["investment_analysis", "price_prediction", "roi_calculation"],
                legal_basis=["广告法", "证券法相关条款"]
            ),
            DisclaimerVersion.V3_USER_CONTENT.value: DisclaimerTemplate(
                version=DisclaimerVersion.V3_USER_CONTENT.value,
                title="用户内容声明",
                content="此部分内容由用户自行上传，平台未对内容真实性进行核实。用户需自行判断其可靠性，平台不对因使用该内容产生的任何损失承担责任。如发现不当内容，请及时举报。",
                applicable_scenarios=["user_upload", "user_comment", "user_review"],
                legal_basis=["电子商务法", "网络安全法"]
            ),
            DisclaimerVersion.V4_AI_GENERATED.value: DisclaimerTemplate(
                version=DisclaimerVersion.V4_AI_GENERATED.value,
                title="AI生成内容声明",
                content="此报告由AI智能体生成，已标注数据来源，仅供参考。AI生成内容可能存在偏差，用户应结合实际情况进行判断。平台持续优化AI模型，但不保证输出内容的绝对准确性。",
                applicable_scenarios=["ai_report", "ai_analysis", "ai_summary"],
                legal_basis=["生成式人工智能服务管理暂行办法"]
            ),
            DisclaimerVersion.V5_LEGAL.value: DisclaimerTemplate(
                version=DisclaimerVersion.V5_LEGAL.value,
                title="法律声明",
                content="本平台不提供法律咨询服务。以下内容仅供参考，不构成法律意见。如有法律问题，请咨询专业律师。平台不对因依赖本内容产生的法律后果承担责任。",
                applicable_scenarios=["legal_info", "policy_interpretation"],
                legal_basis=["律师法"]
            ),
        }
    
    def select_disclaimer(
        self,
        content_type: str,
        risk_level: RiskLevel,
        has_user_content: bool = False,
        has_investment_content: bool = False
    ) -> DisclaimerTemplate:
        """选择声明模板"""
        if has_investment_content or risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return self.templates[DisclaimerVersion.V2_INVESTMENT.value]
        
        if has_user_content:
            return self.templates[DisclaimerVersion.V3_USER_CONTENT.value]
        
        if content_type in ["ai_report", "ai_analysis"]:
            return self.templates[DisclaimerVersion.V4_AI_GENERATED.value]
        
        if content_type in ["legal_info", "policy_interpretation"]:
            return self.templates[DisclaimerVersion.V5_LEGAL.value]
        
        return self.templates[DisclaimerVersion.V1_GENERAL.value]
    
    def apply_disclaimer(self, output: str, disclaimer: DisclaimerTemplate) -> str:
        """应用声明"""
        self.stats["total_applied"] += 1
        self.stats["by_version"][disclaimer.version] += 1
        
        disclaimer_text = f"\n\n---\n**{disclaimer.title}**\n\n{disclaimer.content}\n"
        return output + disclaimer_text
    
    def get_disclaimer_text(self, version: str) -> str:
        """获取声明文本"""
        template = self.templates.get(version)
        if template:
            return f"**{template.title}**\n\n{template.content}"
        return ""


class ComplianceChecker:
    """合规审查器"""
    
    def __init__(self):
        self.rules = self._init_rules()
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "by_rule": defaultdict(int),
            "blocked": 0,
            "rewritten": 0,
        }
    
    def _init_rules(self) -> List[ComplianceRule]:
        """初始化合规规则"""
        return [
            ComplianceRule(
                rule_id="RULE001",
                name="绝对化承诺检测",
                description="检测如'一定涨'、'必定升值'等绝对化表述",
                patterns=["一定涨", "必定升值", "保证收益", "稳赚不赔", "百分百", "绝对安全"],
                action=RuleAction.REWRITE,
                rewrite_template="可能{original}",
                severity=RiskLevel.HIGH
            ),
            ComplianceRule(
                rule_id="RULE002",
                name="医疗健康建议检测",
                description="检测涉及医疗健康的不当建议",
                patterns=["买房治抑郁", "住房治疗", "房产医疗", "治愈疾病"],
                action=RuleAction.BLOCK,
                severity=RiskLevel.CRITICAL
            ),
            ComplianceRule(
                rule_id="RULE003",
                name="投资回报率预测",
                description="检测投资回报率相关内容",
                patterns=["回报率", "收益率", "投资回报", "年化收益"],
                action=RuleAction.WARN,
                disclaimer_required=DisclaimerVersion.V2_INVESTMENT.value,
                severity=RiskLevel.HIGH
            ),
            ComplianceRule(
                rule_id="RULE004",
                name="未标注来源检测",
                description="检测引用数据但未标注来源的情况",
                patterns=["数据显示", "据统计", "研究表明", "调查发现"],
                action=RuleAction.WARN,
                severity=RiskLevel.MEDIUM
            ),
            ComplianceRule(
                rule_id="RULE005",
                name="法律建议检测",
                description="检测可能被解读为法律建议的内容",
                patterns=["法律上", "合同有效", "法律责任", "违法的"],
                action=RuleAction.WARN,
                disclaimer_required=DisclaimerVersion.V5_LEGAL.value,
                severity=RiskLevel.HIGH
            ),
            ComplianceRule(
                rule_id="RULE006",
                name="歧视性内容检测",
                description="检测可能存在歧视的表述",
                patterns=["歧视词A", "歧视词B"],
                action=RuleAction.BLOCK,
                severity=RiskLevel.CRITICAL
            ),
        ]
    
    def check(self, output: str, sources: List[DataSource]) -> Dict[str, Any]:
        """合规检查"""
        self.stats["total_checks"] += 1
        
        violations = []
        warnings = []
        rewritten_output = output
        required_disclaimer = None
        should_block = False
        
        for rule in self.rules:
            matched_patterns = []
            for pattern in rule.patterns:
                if pattern in output:
                    matched_patterns.append(pattern)
            
            if matched_patterns:
                violation = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "matched_patterns": matched_patterns,
                    "action": rule.action.value,
                    "severity": rule.severity.value
                }
                
                self.stats["by_rule"][rule.rule_id] += 1
                self.stats["violations_detected"] += 1
                
                if rule.action == RuleAction.BLOCK:
                    should_block = True
                    violations.append(violation)
                elif rule.action == RuleAction.REWRITE:
                    for pattern in matched_patterns:
                        rewritten_output = rewritten_output.replace(
                            pattern,
                            rule.rewrite_template.format(original=pattern)
                        )
                    self.stats["rewritten"] += 1
                    warnings.append(f"已重写绝对化表述: {matched_patterns}")
                elif rule.action == RuleAction.WARN:
                    warnings.append(f"检测到{rule.name}: {matched_patterns}")
                    if rule.disclaimer_required:
                        required_disclaimer = rule.disclaimer_required
        
        if not sources and self._is_data_driven(output):
            warnings.append("输出包含数据引用但缺少来源标注")
        
        if should_block:
            self.stats["blocked"] += 1
        
        return {
            "passed": not should_block,
            "rewritten_output": rewritten_output,
            "violations": violations,
            "warnings": warnings,
            "required_disclaimer": required_disclaimer,
            "risk_level": self._calculate_risk_level(violations, warnings)
        }
    
    def _is_data_driven(self, output: str) -> bool:
        """判断是否为数据驱动内容"""
        data_indicators = ["数据", "统计", "报告", "分析", "研究", "调查"]
        return any(indicator in output for indicator in data_indicators)
    
    def _calculate_risk_level(
        self,
        violations: List[Dict],
        warnings: List[str]
    ) -> RiskLevel:
        """计算风险等级"""
        if any(v["severity"] == RiskLevel.CRITICAL.value for v in violations):
            return RiskLevel.CRITICAL
        if any(v["severity"] == RiskLevel.HIGH.value for v in violations):
            return RiskLevel.HIGH
        if len(warnings) >= 3:
            return RiskLevel.HIGH
        if warnings:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


class TraceabilityAggregator:
    """溯源聚合器"""
    
    def __init__(self):
        self.trace_records: Dict[str, OutputTraceability] = {}
        self.stats = {
            "total_aggregations": 0,
            "multi_agent_outputs": 0,
        }
    
    def aggregate_sources(
        self,
        agent_sources: Dict[str, List[DataSource]]
    ) -> List[DataSource]:
        """聚合多智能体来源"""
        self.stats["total_aggregations"] += 1
        
        if len(agent_sources) > 1:
            self.stats["multi_agent_outputs"] += 1
        
        all_sources = []
        seen_fingerprints = set()
        
        for agent_id, sources in agent_sources.items():
            for source in sources:
                if source.data_fingerprint and source.data_fingerprint in seen_fingerprints:
                    continue
                
                if source.data_fingerprint:
                    seen_fingerprints.add(source.data_fingerprint)
                
                all_sources.append(source)
        
        return all_sources
    
    def create_trace_record(
        self,
        output_id: str,
        agent_id: str,
        sources: List[DataSource],
        disclaimer_version: str,
        risk_level: RiskLevel,
        compliance_passed: bool,
        warnings: List[str]
    ) -> OutputTraceability:
        """创建溯源记录"""
        record = OutputTraceability(
            output_id=output_id,
            timestamp=datetime.now(),
            agent_id=agent_id,
            sources=sources,
            disclaimer_version=disclaimer_version,
            risk_level=risk_level,
            compliance_passed=compliance_passed,
            review_required=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            warnings=warnings
        )
        
        self.trace_records[output_id] = record
        return record
    
    def get_trace_record(self, output_id: str) -> Optional[OutputTraceability]:
        return self.trace_records.get(output_id)
    
    def get_audit_trail(self, output_id: str) -> Dict[str, Any]:
        """获取审计追踪"""
        record = self.trace_records.get(output_id)
        if not record:
            return {"error": "Record not found"}
        
        return {
            "output_id": record.output_id,
            "timestamp": record.timestamp.isoformat(),
            "agent_id": record.agent_id,
            "source_count": len(record.sources),
            "source_types": list(set(s.source_type.value for s in record.sources)),
            "disclaimer": record.disclaimer_version,
            "risk_level": record.risk_level.value,
            "compliance_passed": record.compliance_passed,
            "review_required": record.review_required,
            "warnings": record.warnings
        }


class OutputTraceabilitySystem:
    """输出溯源系统主控"""
    
    def __init__(self):
        self.source_registry = SourceRegistry()
        self.citation_annotator = CitationAnnotator()
        self.disclaimer_manager = DisclaimerManager()
        self.compliance_checker = ComplianceChecker()
        self.traceability_aggregator = TraceabilityAggregator()
        
        self.output_counter = 0
    
    def process_output(
        self,
        output: str,
        agent_id: str,
        sources: List[DataSource],
        content_type: str = "general",
        has_user_content: bool = False,
        has_investment_content: bool = False
    ) -> Dict[str, Any]:
        """处理输出"""
        self.output_counter += 1
        output_id = f"out_{int(time.time())}_{self.output_counter}"
        
        compliance_result = self.compliance_checker.check(output, sources)
        
        if not compliance_result["passed"]:
            return {
                "output_id": output_id,
                "blocked": True,
                "reason": "compliance_violation",
                "violations": compliance_result["violations"],
                "warnings": compliance_result["warnings"]
            }
        
        processed_output = compliance_result["rewritten_output"]
        
        footer = self.citation_annotator.annotate_footer(sources)
        processed_output += footer
        
        required_disclaimer = compliance_result.get("required_disclaimer")
        if required_disclaimer:
            disclaimer = self.disclaimer_manager.templates.get(required_disclaimer)
        else:
            disclaimer = self.disclaimer_manager.select_disclaimer(
                content_type,
                compliance_result["risk_level"],
                has_user_content,
                has_investment_content
            )
        
        processed_output = self.disclaimer_manager.apply_disclaimer(processed_output, disclaimer)
        
        trace_record = self.traceability_aggregator.create_trace_record(
            output_id=output_id,
            agent_id=agent_id,
            sources=sources,
            disclaimer_version=disclaimer.version,
            risk_level=compliance_result["risk_level"],
            compliance_passed=True,
            warnings=compliance_result["warnings"]
        )
        
        return {
            "output_id": output_id,
            "output": processed_output,
            "blocked": False,
            "traceability": trace_record.to_dict(),
            "warnings": compliance_result["warnings"],
            "review_required": trace_record.review_required
        }
    
    def register_source(
        self,
        source_type: SourceType,
        name: str,
        data: Any = None,
        confidence: float = 0.8,
        url: str = "",
        description: str = ""
    ) -> DataSource:
        """注册数据来源"""
        return self.source_registry.register_source(
            source_type=source_type,
            name=name,
            data=data,
            confidence=confidence,
            url=url,
            description=description
        )
    
    def aggregate_multi_agent_sources(
        self,
        agent_sources: Dict[str, List[DataSource]]
    ) -> List[DataSource]:
        """聚合多智能体来源"""
        return self.traceability_aggregator.aggregate_sources(agent_sources)
    
    def get_audit_trail(self, output_id: str) -> Dict[str, Any]:
        """获取审计追踪"""
        return self.traceability_aggregator.get_audit_trail(output_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "output_counter": self.output_counter,
            "source_registry": self.source_registry.stats,
            "citation_annotator": self.citation_annotator.stats,
            "disclaimer_manager": self.disclaimer_manager.stats,
            "compliance_checker": self.compliance_checker.stats,
            "traceability_aggregator": self.traceability_aggregator.stats,
        }
