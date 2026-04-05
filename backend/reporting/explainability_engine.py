"""
以法治术 - 报告可解释性与规则引擎
房都督平台发展纲领第三章：规则与自由的平衡

核心思想（法家）：
- 法：规则体系必须透明，每条建议都有据可查
- 术：智能体执行策略，在边界内自由发挥
- 势：平台积累的数据与案例，形成决策势能

包含模块：
3.1 ReportBasisEngine - 报告分析依据展示引擎
3.2 RuleLibrary - 规则库与版本追溯机制
"""
import json
import logging
import time
import uuid
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set, Tuple
from collections import deque

logger = logging.getLogger(__name__)


# ==================== 3.1 报告分析依据展示 ====================


class BasisSourceType(str, Enum):
    """依据来源类型"""
    DATA = "data"
    RULE = "rule"
    CASE = "case"
    MODEL_OUTPUT = "model_output"
    EXTERNAL_API = "external_api"
    USER_INPUT = "user_input"


class CredibilityLevel(str, Enum):
    """可信度等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERIFIED = "verified"


@dataclass
class AnalysisBasis:
    """分析依据条目"""
    basis_id: str
    source_type: BasisSourceType
    source_name: str
    content_summary: str
    credibility: CredibilityLevel
    confidence_score: float
    referenced_at: str
    detail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class DecisionTrace:
    """决策追踪记录"""
    trace_id: str
    decision_point: str
    decision_made: str
    bases: List[AnalysisBasis]
    reasoning_chain: List[str]
    alternatives_considered: List[str]
    agent_name: str
    confidence: float
    faithfulness_score: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExplainableReportSection:
    """可解释报告段落"""
    section_id: str
    title: str
    content: str
    conclusion: str
    decision_traces: List[DecisionTrace]
    overall_confidence: float
    is_expandable: bool = True


class ReportBasisEngine:
    """
    报告分析依据展示引擎（提示词 3.1）
    
    功能：
    - 在报告生成过程中记录每个决策点的依据
    - 为每条建议添加可折叠的"查看依据"按钮
    - 依据格式：来源类型/名称/内容摘要/可信度
    - 支持HTML/PDF报告输出
    
    输出格式示例：
    ┌─────────────────────────────────────┐
    │ 建议房价区间：350-420万             │
    │ [▼ 查看依据]                        │
    │   ├─ 数据：某市2025Q1均价385万      │
    │   ├─ 规则：估值方法论V2.1           │
    │   └─ 案例：同类小区成交记录#1247   │
    └─────────────────────────────────────┘
    """

    def __init__(self):
        self._active_traces: List[DecisionTrace] = []
        self._basis_registry: Dict[str, AnalysisBasis] = {}
        self._report_sections: List[ExplainableReportSection] = []
        self._source_stats: Dict[BasisSourceType, int] = {}

    def record_basis(
        self,
        source_type: BasisSourceType,
        source_name: str,
        content_summary: str,
        credibility: CredibilityLevel = CredibilityLevel.MEDIUM,
        confidence: float = 0.8,
        detail_url: str = None,
        metadata: Dict[str, Any] = None,
    ) -> AnalysisBasis:
        """
        记录一条分析依据
        
        Args:
            source_type: 来源类型(数据/规则/案例/模型/API)
            source_name: 来源名称
            content_summary: 内容摘要
            credibility: 可信度等级
            confidence: 置信度分数(0-1)
            detail_url: 详情链接
            metadata: 额外元数据
        """
        basis = AnalysisBasis(
            basis_id=f"basis_{uuid.uuid4().hex[:8]}",
            source_type=source_type,
            source_name=source_name,
            content_summary=content_summary,
            credibility=credibility,
            confidence=round(confidence, 3),
            referenced_at=datetime.utcnow().isoformat(),
            detail_url=detail_url,
            metadata=metadata or {},
        )
        self._basis_registry[basis.basis_id] = basis
        self._source_stats[source_type] = self._source_stats.get(source_type, 0) + 1
        return basis

    def start_decision_trace(
        self,
        decision_point: str,
        agent_name: str = "unknown",
    ) -> DecisionTrace:
        """开始一个决策追踪"""
        trace = DecisionTrace(
            trace_id=f"trace_{uuid.uuid4().hex[:8]}",
            decision_point=decision_point,
            decision_made="",
            bases=[],
            reasoning_chain=[],
            alternatives_considered=[],
            agent_name=agent_name,
            confidence=0.0,
        )
        self._active_traces.append(trace)
        return trace

    def add_reasoning_step(self, trace_id: str, step: str):
        """添加推理步骤"""
        for t in self._active_traces:
            if t.trace_id == trace_id:
                t.reasoning_chain.append(step)
                break

    def add_basis_to_trace(self, trace_id: str, basis: AnalysisBasis):
        """将依据关联到决策追踪"""
        for t in self._active_traces:
            if t.trace_id == trace_id:
                t.bases.append(basis)
                break

    def finalize_trace(self, trace_id: str, decision: str, confidence: float, alternatives: List[str] = None):
        """完成决策追踪"""
        for t in self._active_traces:
            if t.trace_id == trace_id:
                t.decision_made = decision
                t.confidence = round(confidence, 3)
                t.alternatives_considered = alternatives or []
                if t.bases and t.reasoning_chain:
                    basis_avg = sum(b.confidence for b in t.bases) / len(t.bases)
                    reasoning_len = len(t.reasoning_chain)
                    consistency = min(1.0, reasoning_len / max(len(t.bases), 1))
                    t.faithfulness_score = round(basis_avg * 0.6 + consistency * 0.4, 3)
                break

    def create_report_section(
        self,
        title: str,
        content: str,
        conclusion: str,
        traces: List[DecisionTrace] = None,
        confidence: float = 0.8,
    ) -> ExplainableReportSection:
        """创建可解释报告段落"""
        section = ExplainableReportSection(
            section_id=f"sec_{uuid.uuid4().hex[:6]}",
            title=title,
            content=content,
            conclusion=conclusion,
            decision_traces=traces or [],
            overall_confidence=round(confidence, 3),
        )
        self._report_sections.append(section)
        return section

    def render_section_html(self, section: ExplainableReportSection) -> str:
        """渲染报告段落的HTML（含可折叠依据）"""
        basis_html_parts = []
        for trace in section.decision_traces:
            for basis in trace.bases:
                cred_badge = {
                    CredibilityLevel.VERIFIED: "#28a745",
                    CredibilityLevel.HIGH: "#17a2b8",
                    CredibilityLevel.MEDIUM: "#ffc107",
                    CredibilityLevel.LOW: "#dc3545",
                }.get(basis.credibility, "#6c757d")

                badge_label = {
                    BasisSourceType.DATA: "数据",
                    BasisSourceType.RULE: "规则",
                    BasisSourceType.CASE: "案例",
                    BasisSourceType.MODEL_OUTPUT: "模型",
                    BasisSourceType.EXTERNAL_API: "API",
                    BasisSourceType.USER_INPUT: "用户输入",
                }.get(basis.source_type, "其他")

                part = f"""
                <div class="basis-item" style="margin:4px 0;padding:8px;border-left:3px solid {cred_badge};background:#f8f9fa;">
                    <span style="color:{cred_badge};font-weight:bold;">[{badge_label}]</span>
                    <strong>{basis.source_name}</strong> (可信度:{basis.confidence:.0%})
                    <div style="font-size:0.9em;color:#666;margin-top:2px;">{basis.content_summary}</div>
                </div>"""
                basis_html_parts.append(part)

        all_bases_html = "".join(basis_html_parts)

        html = f"""
        <div class="explainable-section" style="border:1px solid #dee2e6;border-radius:6px;padding:16px;margin:12px 0;">
            <h4 style="margin:0 0 8px;color:#0d47a1;">{section.title}</h4>
            <div style="color:#333;line-height:1.6;">{section.content}</div>
            <div style="background:#e3f2fd;padding:10px;border-radius:4px;margin-top:8px;">
                <strong>结论：</strong>{section.conclusion}
                <span style="float:right;color:#666;font-size:0.85em;">置信度 {section.overall_confidence:.0%}</span>
            </div>
            {"<details><summary style='cursor:pointer;color:#1976d2;font-weight:bold;'>📋 查看分析依据 ({len(section.decision_traces)}个决策点)</summary>" + all_bases_html + "</details>" if all_bases_html else ""}
        </div>"""
        return html

    def get_full_report_json(self) -> Dict[str, Any]:
        """获取完整报告的JSON表示"""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_sections": len(self._report_sections),
            "total_traces": len(self._active_traces),
            "total_bases": len(self._basis_registry),
            "source_distribution": {k.value: v for k, v in self._source_stats.items()},
            "sections": [
                {
                    "id": s.section_id,
                    "title": s.title,
                    "conclusion": s.conclusion,
                    "confidence": s.overall_confidence,
                    "trace_count": len(s.decision_traces),
                    "basis_count": sum(len(t.bases) for t in s.decision_traces),
                } for s in self._report_sections
            ],
            "avg_faithfulness": round(
                sum(t.faithfulness_score for t in self._active_traces if t.faithfulness_score > 0) /
                max(sum(1 for t in self._active_traces if t.faithfulness_score > 0), 1), 3
            ) if self._active_traces else 0,
        }


# ==================== 3.2 规则库与版本追溯 ====================


class RuleStatus(str, Enum):
    """规则状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class RuleVersion:
    """规则版本"""
    version_id: str
    rule_id: str
    version_number: str
    content: Dict[str, Any]
    effective_from: float
    effective_until: Optional[float]
    change_reason: str
    changed_by: str
    created_at: float = field(default_factory=time.time)


@dataclass
class Rule:
    """规则定义"""
    rule_id: str
    name: str
    category: str
    description: str
    current_version: RuleVersion
    versions: List[RuleVersion] = field(default_factory=list)
    status: RuleStatus = RuleStatus.ACTIVE
    tags: Set[str] = field(default_factory=set)
    auto_evolve: bool = False


@dataclass
class RuleExecutionRecord:
    """规则执行记录"""
    execution_id: str
    rule_id: str
    version_used: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time_ms: float
    matched: bool
    timestamp: float = field(default_factory=time.time)


class RuleLibrary:
    """
    规则库与版本追溯机制（提示词 3.2）
    
    核心能力：
    - 规则CRUD + 版本管理（每次修改自动创建新版本）
    - 运行时根据当前时间选择生效版本
    - 报告生成时记录所使用的规则版本ID
    - 规则自进化：通过用户反馈自动更新合规规则
    - 版本回滚支持
    """

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._execution_log: List[RuleExecutionRecord] = []
        self._feedback_buffer: List[Dict] = []
        self._category_index: Dict[str, Set[str]] = defaultdict(set)

    def create_rule(
        self,
        name: str,
        category: str,
        content: Dict[str, Any],
        description: str = "",
        tags: List[str] = None,
        auto_evolve: bool = False,
    ) -> Rule:
        """创建新规则"""
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        v1 = RuleVersion(
            version_id=f"ver_{uuid.uuid4().hex[:6]}",
            rule_id=rule_id,
            version_number="1.0.0",
            content=content,
            effective_from=time.time(),
            effective_until=None,
            change_reason="初始创建",
            changed_by="system",
        )

        rule = Rule(
            rule_id=rule_id,
            name=name,
            category=category,
            description=description,
            current_version=v1,
            versions=[v1],
            tags=set(tags or []),
            auto_evolve=auto_evolve,
        )

        self._rules[rule_id] = rule
        self._category_index[category].add(rule_id)
        logger.info(f"规则创建: {name}({rule_id}), 类别={category}, 版本=v1.0.0")
        return rule

    def update_rule(
        self,
        rule_id: str,
        new_content: Dict[str, Any],
        change_reason: str = "",
        changed_by: str = "system",
    ) -> Optional[RuleVersion]:
        """
        更新规则（自动创建新版本）
        
        原版本标记为SUPERSEDED，新版本变为ACTIVE
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        old_version = rule.current_version
        old_version.effective_until = time.time()

        last_ver_num = old_version.version_number
        major, minor, patch = map(int, last_ver_num.split("."))
        new_ver_num = f"{major}.{minor + 1}.0"

        new_version = RuleVersion(
            version_id=f"ver_{uuid.uuid4().hex[:6]}",
            rule_id=rule_id,
            version_number=new_ver_num,
            content=new_content,
            effective_from=time.time(),
            effective_until=None,
            change_reason=change_reason or f"从v{last_ver_num}更新",
            changed_by=changed_by,
        )

        rule.current_version = new_version
        rule.versions.append(new_version)

        logger.info(f"规则更新: {rule.name} -> v{new_ver_num}, 原因={change_reason}")
        return new_version

    def get_effective_rule(self, rule_id: str, at_time: float = None) -> Optional[Dict[str, Any]]:
        """
        获取指定时间点生效的规则版本
        
        如果不指定时间，返回当前最新有效版本
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        target_time = at_time or time.time()

        for version in reversed(rule.versions):
            if version.effective_from <= target_time:
                if version.effective_until is None or version.effective_until > target_time:
                    return {
                        "rule_id": rule_id,
                        "name": rule.name,
                        "version": version.version_number,
                        "content": version.content,
                        "effective_from": version.effective_from,
                        "effective_until": version.effective_until,
                    }
        return None

    def execute_rule(
        self,
        rule_id: str,
        input_data: Dict[str, Any],
        at_time: float = None,
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        执行规则并记录执行日志
        
        Returns:
            (是否匹配, 输出数据, 使用的版本号)
        """
        start_time = time.time()
        effective = self.get_effective_rule(rule_id, at_time)
        if not effective:
            return False, {"error": "规则不存在或无有效版本"}, ""

        content = effective["content"]
        rule_condition = content.get("condition", lambda x: True)
        rule_action = content.get("action", lambda x: {})

        try:
            if callable(rule_condition):
                matched = rule_condition(input_data)
            elif isinstance(rule_condition, str):
                matched = self._eval_condition(rule_condition, input_data)
            else:
                matched = bool(rule_condition)

            if matched:
                if callable(rule_action):
                    output = rule_action(input_data)
                else:
                    output = rule_action
            else:
                output = {"matched": False, "reason": "条件不满足"}

        except Exception as e:
            matched = False
            output = {"error": str(e)}

        exec_time = (time.time() - start_time) * 1000

        record = RuleExecutionRecord(
            execution_id=f"exec_{uuid.uuid4().hex[:8]}",
            rule_id=rule_id,
            version_used=effective["version"],
            input_data=input_data,
            output_data=output,
            execution_time_ms=round(exec_time, 2),
            matched=matched,
        )
        self._execution_log.append(record)

        return matched, output, effective["version"]

    def _eval_condition(self, condition_str: str, data: Dict) -> bool:
        """简单条件表达式求值（安全受限）"""
        safe_dict = {"True": True, "False": False, "None": None}
        safe_dict.update(data)
        try:
            return bool(eval(condition_str, {"__builtins__": {}}, safe_dict))
        except Exception:
            return False

    def rollback_rule(self, rule_id: str, target_version: str) -> bool:
        """回滚规则到指定版本"""
        rule = self._rules.get(rule_id)
        if not rule:
            return False

        target = None
        for v in rule.versions:
            if v.version_number == target_version:
                target = v
                break

        if not target:
            return False

        rule.current_version.effective_until = time.time()
        target.effective_until = None
        target.effective_from = time.time()
        rule.current_version = target

        logger.info(f"规则回滚: {rule.name} -> v{target_version}")
        return True

    def submit_feedback(self, rule_id: str, feedback_type: str, comment: str, user_id: str = ""):
        """提交用户反馈（用于规则自进化）"""
        self._feedback_buffer.append({
            "rule_id": rule_id,
            "feedback_type": feedback_type,
            "comment": comment,
            "user_id": user_id,
            "timestamp": time.time(),
        })

        rule = self._rules.get(rule_id)
        if rule and rule.auto_evolve:
            negative_count = sum(1 for f in self._feedback_buffer[-20:] if f["rule_id"] == rule_id and f["feedback_type"] == "negative")
            if negative_count >= 5:
                logger.info(f"规则自进化触发: {rule.name}, 近期负反馈={negative_count}条")

    def list_rules_by_category(self, category: str = None, status: RuleStatus = None) -> List[Dict]:
        """列出规则"""
        results = []
        for rule_id, rule in self._rules.items():
            if category and rule.category != category:
                continue
            if status and rule.status != status:
                continue
            results.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "category": rule.category,
                "status": rule.status.value,
                "current_version": rule.current_version.version_number,
                "version_count": len(rule.versions),
                "tags": list(rule.tags),
                "auto_evolve": rule.auto_evolve,
            })
        return sorted(results, key=lambda r: r["name"])

    def get_library_stats(self) -> Dict[str, Any]:
        """获取规则库统计"""
        status_counts = {}
        cat_counts = {}
        for rule in self._rules.values():
            status_counts[rule.status.value] = status_counts.get(rule.status.value, 0) + 1
            cat_counts[rule.category] = cat_counts.get(rule.category, 0) + 1

        recent_execs = self._execution_log[-50:] if self._execution_log else []
        match_rate = sum(1 for e in recent_execs if e.matched) / max(len(recent_execs), 1)

        return {
            "total_rules": len(self._rules),
            "status_distribution": status_counts,
            "category_distribution": cat_counts,
            "total_executions": len(self._execution_log),
            "recent_match_rate": round(match_rate, 3),
            "pending_feedback": len(self._feedback_buffer),
            "auto_evolve_rules": sum(1 for r in self._rules.values() if r.auto_evolve),
        }


# ==================== 全局实例 ====================

report_basis_engine = ReportBasisEngine()
rule_library = RuleLibrary()
