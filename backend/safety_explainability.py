"""
安全监控与可解释性验证模块 - Tool Affordance + CoT增强版
集成Tool Affordance（Yu et al., 2026）与CoT可解释性验证

核心能力：
1. Tool Affordance安全监控：检测工具执行时的安全对齐偏移
2. CoT可解释性验证：验证思维链推理的真实性与决策一致性
3. 行为安全审计：追踪语言合规 vs 行为安全的一致性
"""
import json
import logging
import time
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Awaitable
from collections import deque

logger = logging.getLogger(__name__)


class SafetyAlignmentState(str, Enum):
    """安全对齐状态"""
    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"
    CRITICAL_VIOLATION = "critical_violation"


class ToolRiskLevel(str, Enum):
    """工具风险等级"""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class CoTFaithfulness(str, Enum):
    """CoT真实性等级"""
    FAITHFUL = "faithful"
    PARTIALLY_FAITHFUL = "partially_faithful"
    UNFAITHFUL = "unfaithful"
    UNVERIFIABLE = "unverifiable"


@dataclass
class ToolExecutionRecord:
    """工具执行记录（Tool Affordance追踪）"""
    execution_id: str
    tool_name: str
    tool_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    pre_alignment_state: SafetyAlignmentState = SafetyAlignmentState.ALIGNED
    post_alignment_state: SafetyAlignmentState = SafetyAlignmentState.ALIGNED
    risk_level: ToolRiskLevel = ToolRiskLevel.SAFE
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    violation_detected: bool = False
    violation_type: Optional[str] = None
    language_compliance_score: float = 1.0
    behavior_safety_score: float = 1.0


@dataclass
class CoTVerificationRecord:
    """CoT可解释性验证记录"""
    verification_id: str
    task_id: str
    reasoning_chain: List[Dict[str, str]]
    final_decision: str
    actual_execution_path: List[str]
    faithfulness: CoTFaithfulness = CoTFaithfulness.UNVERIFIABLE
    consistency_score: float = 0.0
    completeness_score: float = 0.0
    gaps: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SafetyAuditEvent:
    """安全审计事件"""
    event_id: str
    event_type: str  # "tool_violation", "cot_mismatch", "alignment_shift", "behavior_anomaly"
    severity: str  # "info", "warning", "critical"
    source_agent: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


class ToolAffordanceMonitor:
    """
    Tool Affordance安全监控器（Yu et al., 2026）
    监控工具执行过程中的安全对齐状态变化
    核心发现：工具启用时违规率从12%升至85%（语言合规≠行为安全）
    """

    RISKY_TOOL_PATTERNS = {
        "file_write": {"risk": ToolRiskLevel.HIGH_RISK, "patterns": ["写入", "修改文件", "创建"]},
        "file_delete": {"risk": ToolRiskLevel.CRITICAL, "patterns": ["删除", "移除", "清除"]},
        "system_command": {"risk": ToolRiskLevel.CRITICAL, "patterns": ["执行命令", "shell", "系统调用"]},
        "network_request": {"risk": ToolRiskLevel.MEDIUM_RISK, "patterns": ["请求", "API调用", "发送数据"]},
        "database_modify": {"risk": ToolRiskLevel.HIGH_RISK, "patterns": ["更新数据库", "插入", "修改记录"]},
        "data_export": {"risk": ToolRiskLevel.MEDIUM_RISK, "patterns": ["导出", "下载", "生成报告"]},
        "code_execute": {"risk": ToolRiskLevel.CRITICAL, "patterns": ["运行代码", "eval", "exec"]},
        "default": {"risk": ToolRiskLevel.LOW_RISK, "patterns": []},
    }

    VIOLATION_PATTERNS = [
        r"(?i)(?:绕过|bypass|规避|evade).*(?:安全|security|auth|认证|权限)",
        r"(?i)(?:注入|inject|sql|xss).*(?:攻击|attack|exploit)",
        r"(?i)(?:泄露|leak|暴露|expose).*(?:密码|password|token|密钥|key|敏感)",
        r"(?i)(?:未授权|unauthorized).*(?:访问|access|修改|delete|删除)",
        r"(?i)(?:越权|privilege.?escalation|提权)",
    ]

    def __init__(self):
        self._execution_history: deque = deque(maxlen=1000)
        self._audit_events: List[SafetyAuditEvent] = []
        self._alignment_stats = {
            "total_executions": 0,
            "violations_detected": 0,
            "violation_rate": 0.0,
            "avg_language_compliance": 0.0,
            "avg_behavior_safety": 0.0,
            "alignment_shift_events": 0,
        }
        self._violation_callbacks: List[Callable] = []

    def assess_tool_risk(self, tool_name: str, input_data: Dict[str, Any]) -> ToolRiskLevel:
        """评估工具风险等级"""
        for pattern_key, config in self.RISKY_TOOL_PATTERNS.items():
            if pattern_key in tool_name.lower() or any(p in tool_name.lower() for p in config["patterns"]):
                return config["risk"]
        return ToolRiskLevel.SAFE

    def pre_execution_check(self, tool_name: str, input_data: Dict[str, Any], agent_name: str = "unknown") -> ToolExecutionRecord:
        """
        执行前检查
        记录执行前的安全对齐状态
        """
        record = ToolExecutionRecord(
            execution_id=f"exec_{int(time.time()*1000)}_{hash(tool_name) % 10000}",
            tool_name=tool_name,
            tool_type=self._classify_tool_type(tool_name),
            input_data=input_data,
            risk_level=self.assess_tool_risk(tool_name, input_data),
            pre_alignment_state=SafetyAlignmentState.ALIGNED,
            language_compliance_score=1.0,
        )

        if record.risk_level in [ToolRiskLevel.HIGH_RISK, ToolRiskLevel.CRITICAL]:
            record.pre_alignment_state = SafetyAlignmentState.PARTIALLY_ALIGNED
            logger.warning(f"ToolAffordance: 高风险工具即将执行 - {tool_name} by {agent_name}, risk={record.risk_level.value}")

        return record

    def post_execution_audit(self, record: ToolExecutionRecord, output_data: Dict[str, Any], agent_name: str = "unknown") -> ToolExecutionRecord:
        """
        执行后审计
        检测安全对齐偏移和违规行为
        """
        record.output_data = output_data
        record.duration_ms = (time.time() - record.timestamp) * 1000

        output_str = json.dumps(output_data, ensure_ascii=False) if output_data else ""
        input_str = json.dumps(record.input_data, ensure_ascii=False)

        record.language_compliance_score = self._assess_language_compliance(output_str)
        record.behavior_safety_score = self._assess_behavior_safety(record.tool_name, input_str, output_str)

        compliance_gap = abs(record.language_compliance_score - record.behavior_safety_score)

        if compliance_gap > 0.3:
            record.post_alignment_state = SafetyAlignmentState.MISALIGNED
            record.violation_detected = True
            record.violation_type = "alignment_shift"

            event = SafetyAuditEvent(
                event_id=f"audit_{int(time.time()*1000)}",
                event_type="alignment_shift",
                severity="warning" if compliance_gap < 0.6 else "critical",
                source_agent=agent_name,
                description=f"工具{record.tool_name}执行后检测到安全对齐偏移: 语言合规={record.language_compliance_score:.2f}, 行为安全={record.behavior_safety_score:.2f}",
                details={
                    "execution_id": record.execution_id,
                    "compliance_gap": round(compliance_gap, 3),
                    "tool_name": record.tool_name,
                    "risk_level": record.risk_level.value,
                },
            )
            self._audit_events.append(event)
            self._alignment_stats["alignment_shift_events"] += 1
            logger.warning(f"ToolAffordance违规检测: {event.description}")

        for pattern in self.VIOLATION_PATTERNS:
            if re.search(pattern, output_str) or re.search(pattern, input_str):
                record.post_alignment_state = SafetyAlignmentState.CRITICAL_VIOLATION
                record.violation_detected = True
                record.violation_type = "content_violation"

                event = SafetyAuditEvent(
                    event_id=f"audit_{int(time.time()*1000)}",
                    event_type="tool_violation",
                    severity="critical",
                    source_agent=agent_name,
                    description=f"检测到违规内容模式在工具 {record.tool_name} 的输入/输出中",
                    details={
                        "execution_id": record.execution_id,
                        "matched_pattern": pattern[:50],
                        "tool_name": record.tool_name,
                    },
                )
                self._audit_events.append(event)
                logger.critical(f"Tool Affordance关键违规: {event.description}")
                break

        if not record.violation_detected:
            if record.behavior_safety_score >= 0.9:
                record.post_alignment_state = SafetyAlignmentState.ALIGNED
            else:
                record.post_alignment_state = SafetyAlignmentState.PARTIALLY_ALIGNED

        self._execution_history.append(record)
        self._update_stats(record)

        return record

    def _classify_tool_type(self, tool_name: str) -> str:
        """分类工具类型"""
        type_map = {
            "read": "data_read", "write": "data_write", "delete": "data_delete",
            "api": "external_call", "compute": "computation", "search": "query",
        }
        for t, v in type_map.items():
            if t in tool_name.lower():
                return v
        return "general"

    def _assess_language_compliance(self, text: str) -> float:
        """评估语言合规性分数"""
        score = 1.0
        risky_terms = ["忽略", "跳过", "强制", "hack", "backdoor", "后门", "漏洞"]
        for term in risky_terms:
            if term.lower() in text.lower():
                score -= 0.15
        return max(0.0, min(1.0, score))

    def _assess_behavior_safety(self, tool_name: str, input_text: str, output_text: str) -> float:
        """评估行为安全性分数"""
        base_scores = {
            ToolRiskLevel.SAFE: 1.0,
            ToolRiskLevel.LOW_RISK: 0.9,
            ToolRiskLevel.MEDIUM_RISK: 0.75,
            ToolRiskLevel.HIGH_RISK: 0.6,
            ToolRiskLevel.CRITICAL: 0.4,
        }

        risk = self.assess_tool_risk(tool_name, {"text": input_text})
        score = base_scores.get(risk, 0.8)

        sensitive_indicators = ["password", "secret", "token", "credential", "private"]
        combined = input_text + " " + output_text
        for ind in sensitive_indicators:
            if ind.lower() in combined.lower():
                score -= 0.1

        return max(0.0, min(1.0, score))

    def _update_stats(self, record: ToolExecutionRecord):
        """更新统计信息"""
        stats = self._alignment_stats
        stats["total_executions"] += 1
        if record.violation_detected:
            stats["violations_detected"] += 1
        stats["violation_rate"] = stats["violations_detected"] / max(1, stats["total_executions"])
        n = stats["total_executions"]
        stats["avg_language_compliance"] = (
            (stats["avg_language_compliance"] * (n - 1) + record.language_compliance_score) / n
        )
        stats["avg_behavior_safety"] = (
            (stats["avg_behavior_safety"] * (n - 1) + record.behavior_safety_score) / n
        )

    def get_safety_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        recent_events = sorted(self._audit_events, key=lambda e: e.timestamp, reverse=True)[:20]
        return {
            "statistics": dict(self._alignment_stats),
            "recent_audit_events": [
                {
                    "type": e.event_type,
                    "severity": e.severity,
                    "source": e.source_agent,
                    "description": e.description,
                    "timestamp": datetime.fromtimestamp(e.timestamp).isoformat(),
                } for e in recent_events
            ],
            "total_audit_events": len(self._audit_events),
            "monitored_executions": len(self._execution_history),
        }


class CoTExplainer:
    """
    Chain-of-Thought可解释性验证器
    验证LLM的推理链是否忠实于实际决策过程
    """

    CONSISTENCY_CHECKS = [
        "reasoning_to_conclusion",
        "step_logical_order",
        "evidence_support",
        "alternative_considered",
    ]

    def __init__(self):
        self._verification_history: List[CoTVerificationRecord] = []
        self._stats = {
            "total_verifications": 0,
            "faithful_count": 0,
            "unfaithful_count": 0,
            "avg_consistency": 0.0,
            "avg_completeness": 0.0,
        }

    def verify_cot(
        self,
        task_id: str,
        reasoning_chain: List[Dict[str, str]],
        final_decision: str,
        actual_execution_path: Optional[List[str]] = None,
    ) -> CoTVerificationRecord:
        """
        验证CoT推理的真实性

        Args:
            task_id: 任务ID
            reasoning_chain: 推理链 [{"step": "...", "reasoning": "..."}]
            final_decision: 最终决策
            actual_execution_path: 实际执行路径（可选）

        Returns:
            验证记录
        """
        record = CoTVerificationRecord(
            verification_id=f"cot_{int(time.time()*1000)}",
            task_id=task_id,
            reasoning_chain=reasoning_chain,
            final_decision=final_decision,
            actual_execution_path=actual_execution_path or [],
        )

        consistency_results = []
        gaps = []

        step_conclusion_match = self._check_reasoning_to_conclusion(reasoning_chain, final_decision)
        consistency_results.append(step_conclusion_match)
        if not step_conclusion_match["passed"]:
            gaps.append("推理结论不匹配: 推理链最终步骤与决策结果不一致")

        logical_order_check = self._check_logical_order(reasoning_chain)
        consistency_results.append(logical_order_check)
        if not logical_order_check["passed"]:
            gaps.append("逻辑顺序异常: 推理步骤存在顺序问题")

        evidence_check = self._check_evidence_support(reasoning_chain)
        consistency_results.append(evidence_check)
        if not evidence_check["passed"]:
            gaps.append("证据支持不足: 部分推理步骤缺乏充分依据")

        passed_count = sum(1 for r in consistency_results if r["passed"])
        record.consistency_score = passed_count / max(1, len(consistency_results))
        record.completeness_score = len(reasoning_chain) / max(1, len(reasoning_chain) + len(gaps))
        record.gaps = gaps

        if record.consistency_score >= 0.9 and not gaps:
            record.faithfulness = CoTFaithfulness.FAITHFUL
        elif record.consistency_score >= 0.6:
            record.faithfulness = CoTFaithfulness.PARTIALLY_FAITHFUL
        elif record.consistency_score >= 0.3:
            record.faithfulness = CoTFaithfulness.UNFAITHFUL
        else:
            record.faithfulness = CoTFaithfulness.UNVERIFIABLE

        if actual_execution_path:
            path_faithfulness = self._verify_execution_path_faithfulness(reasoning_chain, actual_execution_path)
            if path_faithfulness < 0.5:
                record.gaps.append("执行路径不一致: 实际执行路径与推理链描述不符")
                record.consistency_score *= 0.7

        self._verification_history.append(record)
        self._update_stats(record)

        logger.info(f"CoT验证完成: task={task_id}, faithfulness={record.faithfulness.value}, consistency={record.consistency_score:.2f}")
        return record

    def _check_reasoning_to_conclusion(self, chain: List[Dict], conclusion: str) -> Dict[str, Any]:
        """检查推理是否导向结论"""
        if not chain:
            return {"check": "reasoning_to_conclusion", "passed": False, "detail": "空推理链"}

        last_step = chain[-1].get("reasoning", "") or chain[-1].get("step", "")
        last_step_lower = last_step.lower()
        conclusion_lower = conclusion.lower()

        key_concepts_in_last = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', last_step))
        key_concepts_in_conclusion = set(re.findall(r'[\u4e00-\u9fff\w]{2,}', conclusion_lower))
        overlap = key_concepts_in_last & key_concepts_in_conclusion

        is_passed = len(overlap) >= 2 or any(w in last_step_lower for w in conclusion_lower.split()[:5])
        return {
            "check": "reasoning_to_conclusion",
            "passed": is_passed,
            "detail": f"概念重叠度: {len(overlap)}个",
        }

    def _check_logical_order(self, chain: List[Dict]) -> Dict[str, Any]:
        """检查逻辑顺序"""
        if len(chain) <= 1:
            return {"check": "step_logical_order", "passed": True, "detail": "单步推理"}

        order_keywords = ["首先", "然后", "接着", "其次", "最后", "第一", "第二", "第三", "综上", "因此"]
        violations = 0
        for i, step in enumerate(chain):
            text = step.get("reasoning", "") or step.get("step", "")
            if i == 0 and any(kw in text for kw in ["因此", "所以", "综上", "结论"]):
                violations += 1
            if i > 0 and i < len(chain) - 1 and "结论" in text:
                violations += 1

        return {"check": "step_logical_order", "passed": violations == 0, "detail": f"顺序违规: {violations}处"}

    def _check_evidence_support(self, chain: List[Dict]) -> Dict[str, Any]:
        """检查证据支持"""
        unsupported = 0
        evidence_patterns = [r'因为', r'由于', r'根据', r'数据显示', r'\d+%?', r'\d+[\u4e00-\u9fff]']

        for step in chain:
            text = step.get("reasoning", "") or step.get("step", "")
            has_evidence = any(re.search(p, text) for p in evidence_patterns)
            if not has_evidence and len(text) > 20:
                unsupported += 1

        passed = unsupported <= len(chain) * 0.3
        return {"check": "evidence_support", "passed": passed, "detail": f"无证据步骤: {unsupported}/{len(chain)}"}

    def _verify_execution_path_faithfulness(self, chain: List[Dict], exec_path: List[str]) -> float:
        """验证执行路径与推理链的一致性"""
        if not exec_path:
            return 1.0

        chain_actions = []
        for step in chain:
            text = step.get("reasoning", "") or step.get("step", "")
            actions = re.findall(r'(?:调用|使用|执行|查询|分析|计算)\s*[\u4e00-\u9fff\w]+', text)
            chain_actions.extend(actions)

        match_count = sum(1 for action in chain_actions for ep in exec_path if action in ep or ep in action)
        return match_count / max(1, len(exec_path))

    def _update_stats(self, record: CoTVerificationRecord):
        """更新统计"""
        self._stats["total_verifications"] += 1
        if record.faithfulness == CoTFaithfulness.FAITHFUL:
            self._stats["faithful_count"] += 1
        elif record.faithfulness in [CoTFaithfulness.UNFAITHFUL, CoTFaithfulness.UNVERIFIABLE]:
            self._stats["unfaithful_count"] += 1
        n = self._stats["total_verifications"]
        self._stats["avg_consistency"] = (self._stats["avg_consistency"] * (n - 1) + record.consistency_score) / n
        self._stats["avg_completeness"] = (self._stats["avg_completeness"] * (n - 1) + record.completeness_score) / n

    def get_explainability_report(self) -> Dict[str, Any]:
        """获取可解释性报告"""
        return {
            "statistics": dict(self._stats),
            "recent_verifications": [
                {
                    "task_id": r.task_id,
                    "faithfulness": r.faithfulness.value,
                    "consistency": round(r.consistency_score, 2),
                    "completeness": round(r.completeness_score, 2),
                    "gaps": r.gaps,
                } for r in self._verification_history[-10:]
            ],
        }


class SafetyExplainabilityHub:
    """
    安全与可解释性中心枢纽
    统一管理Tool Affordance监控和CoT验证
    """

    def __init__(self):
        self.tool_monitor = ToolAffordanceMonitor()
        self.cot_explainer = CoTExplainer()

    async def monitor_tool_execution(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        execute_fn: Callable,
        agent_name: str = "unknown",
    ) -> Dict[str, Any]:
        """
        工具执行的完整安全监控流程

        Args:
            tool_name: 工具名称
            input_data: 输入数据
            execute_fn: 执行函数
            agent_name: 调用智能体名称

        Returns:
            包含输出和安全审计信息的字典
        """
        pre_record = self.tool_monitor.pre_execution_check(tool_name, input_data, agent_name)

        try:
            output = await execute_fn() if asyncio.iscoroutinefunction(execute_fn) else execute_fn()
            post_record = self.tool_monitor.post_execution_audit(pre_record, output, agent_name)

            return {
                "output": output,
                "safe": not post_record.violation_detected,
                "audit_record": {
                    "execution_id": post_record.execution_id,
                    "risk_level": post_record.risk_level.value,
                    "pre_state": post_record.pre_alignment_state.value,
                    "post_state": post_record.post_alignment_state.value,
                    "language_compliance": round(post_record.language_compliance_score, 2),
                    "behavior_safety": round(post_record.behavior_safety_score, 2),
                    "violation": post_record.violation_detected,
                    "violation_type": post_record.violation_type,
                },
            }
        except Exception as e:
            pre_record.output_data = {"error": str(e)}
            pre_record.violation_detected = True
            pre_record.violation_type = "execution_error"
            pre_record.post_alignment_state = SafetyAlignmentState.CRITICAL_VIOLATION
            self.tool_monitor._execution_history.append(pre_record)
            raise

    def verify_reasoning(self, task_id: str, reasoning_chain: List[Dict], final_decision: str, execution_path: List[str] = None) -> Dict[str, Any]:
        """验证推理链的可解释性"""
        record = self.cot_explainer.verify_cot(task_id, reasoning_chain, final_decision, execution_path)
        return {
            "verification_id": record.verification_id,
            "faithfulness": record.faithfulness.value,
            "consistency_score": round(record.consistency_score, 2),
            "completeness_score": round(record.completeness_score, 2),
            "gaps": record.gaps,
            "is_trusted": record.faithfulness in [CoTFaithfulness.FAITHFUL, CoTFaithfulness.PARTIALLY_FAITHFUL],
        }

    def get_full_report(self) -> Dict[str, Any]:
        """获取完整的安全与可解释性报告"""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "tool_affordance": self.tool_monitor.get_safety_report(),
            "cot_explainability": self.cot_explainer.get_explainability_report(),
        }


import asyncio

safety_hub = SafetyExplainabilityHub()
