"""
AI伦理与治理检查智能体
AI Ethics Audit Agent - 检查AI智能体的决策是否符合伦理要求
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import uuid
import random


class EthicsDimension(Enum):
    FAIRNESS = "fairness"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    SAFETY = "safety"
    PRIVACY = "privacy"
    HUMAN_CONTROL = "human_control"


class EthicsCheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


class RiskCategory(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EthicsCheckResult:
    check_id: str
    dimension: EthicsDimension
    check_name: str
    description: str
    status: EthicsCheckStatus
    score: float
    details: Dict[str, Any]
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BiasDetectionResult:
    attribute: str
    groups: Dict[str, float]
    disparity_ratio: float
    bias_detected: bool
    severity: RiskCategory
    affected_samples: int


@dataclass
class ExplainabilityResult:
    decision_id: str
    input_features: Dict[str, Any]
    output: Any
    feature_importance: Dict[str, float]
    explanation: str
    confidence: float


class FairnessChecker:
    def __init__(self):
        self.fairness_metrics: Dict[str, Dict] = {}
        self.bias_thresholds: Dict[str, float] = {
            "disparate_impact": 0.8,
            "statistical_parity": 0.1,
            "equal_opportunity": 0.1,
        }

    def register_fairness_metric(
        self, metric_name: str, calculation_func: callable
    ) -> None:
        self.fairness_metrics[metric_name] = calculation_func

    def check_disparate_impact(
        self, predictions: Dict[str, List[bool]], protected_attribute: str
    ) -> BiasDetectionResult:
        groups = {}
        for group, preds in predictions.items():
            positive_rate = sum(preds) / len(preds) if preds else 0
            groups[group] = positive_rate

        if len(groups) >= 2:
            rates = list(groups.values())
            min_rate = min(r for r in rates if r > 0)
            max_rate = max(rates)
            disparity_ratio = min_rate / max_rate if max_rate > 0 else 0
        else:
            disparity_ratio = 1.0

        bias_detected = disparity_ratio < self.bias_thresholds["disparate_impact"]

        if bias_detected:
            severity = RiskCategory.HIGH
        elif disparity_ratio < 0.9:
            severity = RiskCategory.MEDIUM
        else:
            severity = RiskCategory.LOW

        return BiasDetectionResult(
            attribute=protected_attribute,
            groups=groups,
            disparity_ratio=disparity_ratio,
            bias_detected=bias_detected,
            severity=severity,
            affected_samples=sum(len(p) for p in predictions.values()),
        )

    def check_statistical_parity(
        self, outcomes: Dict[str, List[bool]], threshold: float = None
    ) -> Dict[str, Any]:
        if threshold is None:
            threshold = self.bias_thresholds["statistical_parity"]

        result = {"parity_achieved": True, "group_rates": {}, "differences": []}

        rates = {}
        for group, group_outcomes in outcomes.items():
            rates[group] = sum(group_outcomes) / len(group_outcomes) if group_outcomes else 0
            result["group_rates"][group] = rates[group]

        groups = list(rates.keys())
        for i, g1 in enumerate(groups):
            for g2 in groups[i + 1 :]:
                diff = abs(rates[g1] - rates[g2])
                if diff > threshold:
                    result["parity_achieved"] = False
                result["differences"].append(
                    {"groups": (g1, g2), "difference": diff, "within_threshold": diff <= threshold}
                )

        return result

    def check_equal_opportunity(
        self, predictions: Dict[str, Dict[str, List[bool]]]
    ) -> Dict[str, Any]:
        result = {"equal_opportunity": True, "true_positive_rates": {}, "differences": []}

        tprs = {}
        for group, data in predictions.items():
            true_positives = sum(data.get("true_positives", []))
            actual_positives = sum(data.get("actual_positives", []))
            tpr = true_positives / actual_positives if actual_positives > 0 else 0
            tprs[group] = tpr
            result["true_positive_rates"][group] = tpr

        groups = list(tprs.keys())
        for i, g1 in enumerate(groups):
            for g2 in groups[i + 1 :]:
                diff = abs(tprs[g1] - tprs[g2])
                if diff > self.bias_thresholds["equal_opportunity"]:
                    result["equal_opportunity"] = False
                result["differences"].append({"groups": (g1, g2), "difference": diff})

        return result


class TransparencyChecker:
    def __init__(self):
        self.explanation_records: List[ExplainabilityResult] = []
        self.decision_logs: List[Dict] = []

    def log_decision(
        self,
        decision_id: str,
        agent_id: str,
        input_data: Dict,
        output_data: Any,
        reasoning: str = None,
    ) -> None:
        self.decision_logs.append(
            {
                "decision_id": decision_id,
                "agent_id": agent_id,
                "input_data": input_data,
                "output_data": output_data,
                "reasoning": reasoning,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def generate_explanation(
        self,
        decision_id: str,
        feature_importance: Dict[str, float],
        explanation_template: str = None,
    ) -> ExplainabilityResult:
        decision = next(
            (d for d in self.decision_logs if d["decision_id"] == decision_id), None
        )

        if not decision:
            return None

        sorted_features = sorted(
            feature_importance.items(), key=lambda x: abs(x[1]), reverse=True
        )

        top_factors = sorted_features[:3]
        explanation_parts = []
        for feature, importance in top_factors:
            direction = "增加" if importance > 0 else "降低"
            explanation_parts.append(f"{feature}({direction}了决策概率{abs(importance):.1%})")

        explanation = f"决策主要由以下因素影响: {', '.join(explanation_parts)}"

        if explanation_template:
            explanation = explanation_template.format(
                top_factor=top_factors[0][0] if top_factors else "未知",
                explanation=explanation,
            )

        result = ExplainabilityResult(
            decision_id=decision_id,
            input_features=decision["input_data"],
            output=decision["output_data"],
            feature_importance=feature_importance,
            explanation=explanation,
            confidence=max(abs(v) for v in feature_importance.values())
            if feature_importance
            else 0.5,
        )

        self.explanation_records.append(result)
        return result

    def check_explainability_coverage(self) -> Dict[str, Any]:
        result = {
            "total_decisions": len(self.decision_logs),
            "explained_decisions": len(self.explanation_records),
            "coverage_rate": 0.0,
            "unexplained_decisions": [],
        }

        if result["total_decisions"] > 0:
            result["coverage_rate"] = (
                result["explained_decisions"] / result["total_decisions"]
            )

        explained_ids = {e.decision_id for e in self.explanation_records}
        result["unexplained_decisions"] = [
            d["decision_id"] for d in self.decision_logs if d["decision_id"] not in explained_ids
        ]

        return result

    def check_decision_traceability(self, decision_id: str) -> Dict[str, Any]:
        result = {"traceable": False, "decision_chain": [], "issues": []}

        decision = next(
            (d for d in self.decision_logs if d["decision_id"] == decision_id), None
        )

        if decision:
            result["traceable"] = True
            result["decision_chain"].append(
                {
                    "step": 1,
                    "type": "input",
                    "data": decision["input_data"],
                    "timestamp": decision["timestamp"],
                }
            )

            if decision["reasoning"]:
                result["decision_chain"].append(
                    {
                        "step": 2,
                        "type": "reasoning",
                        "data": decision["reasoning"],
                    }
                )

            result["decision_chain"].append(
                {
                    "step": len(result["decision_chain"]) + 1,
                    "type": "output",
                    "data": decision["output_data"],
                }
            )
        else:
            result["issues"].append(f"Decision {decision_id} not found in logs")

        return result


class SafetyChecker:
    def __init__(self):
        self.red_team_tests: List[Dict] = []
        self.safety_boundaries: Dict[str, Any] = {}
        self.violation_records: List[Dict] = []

    def define_safety_boundary(
        self, boundary_name: str, rules: List[Dict]
    ) -> None:
        self.safety_boundaries[boundary_name] = {
            "rules": rules,
            "defined_at": datetime.utcnow().isoformat(),
        }

    def run_red_team_test(
        self,
        test_id: str,
        test_type: str,
        inputs: List[str],
        expected_safe: bool = True,
    ) -> Dict[str, Any]:
        results = []
        violations = 0

        for input_text in inputs:
            is_safe = self._check_input_safety(input_text)
            results.append({"input": input_text, "is_safe": is_safe})

            if not is_safe:
                violations += 1

        test_result = {
            "test_id": test_id,
            "test_type": test_type,
            "total_inputs": len(inputs),
            "violations": violations,
            "pass_rate": (len(inputs) - violations) / len(inputs) if inputs else 1.0,
            "results": results,
            "tested_at": datetime.utcnow().isoformat(),
        }

        self.red_team_tests.append(test_result)
        return test_result

    def _check_input_safety(self, input_text: str) -> bool:
        dangerous_patterns = [
            "ignore previous instructions",
            "bypass safety",
            "jailbreak",
            "system prompt",
            "admin access",
        ]

        input_lower = input_text.lower()
        for pattern in dangerous_patterns:
            if pattern in input_lower:
                return False
        return True

    def record_violation(
        self,
        agent_id: str,
        violation_type: str,
        details: Dict,
        severity: RiskCategory,
    ) -> str:
        violation_id = f"viol_{uuid.uuid4().hex[:8]}"

        self.violation_records.append(
            {
                "violation_id": violation_id,
                "agent_id": agent_id,
                "violation_type": violation_type,
                "details": details,
                "severity": severity,
                "recorded_at": datetime.utcnow().isoformat(),
            }
        )

        return violation_id

    def check_safety_compliance(self) -> Dict[str, Any]:
        result = {
            "compliant": True,
            "total_tests": len(self.red_team_tests),
            "total_violations": len(self.violation_records),
            "pass_rate": 1.0,
            "recent_violations": [],
        }

        if self.red_team_tests:
            total_pass = sum(t["pass_rate"] for t in self.red_team_tests)
            result["pass_rate"] = total_pass / len(self.red_team_tests)

        if result["pass_rate"] < 0.9 or result["total_violations"] > 0:
            result["compliant"] = False

        recent_cutoff = datetime.utcnow() - datetime.timedelta(days=7)
        result["recent_violations"] = [
            v
            for v in self.violation_records
            if datetime.fromisoformat(v["recorded_at"]) > recent_cutoff
        ]

        return result


class AccountabilityChecker:
    def __init__(self):
        self.responsibility_matrix: Dict[str, List[str]] = {}
        self.audit_trail: List[Dict] = []
        self.human_oversight_records: List[Dict] = []

    def assign_responsibility(
        self, agent_id: str, responsibilities: List[str]
    ) -> None:
        self.responsibility_matrix[agent_id] = responsibilities

    def log_action(
        self,
        action_id: str,
        agent_id: str,
        action_type: str,
        details: Dict,
        human_approved: bool = False,
    ) -> None:
        self.audit_trail.append(
            {
                "action_id": action_id,
                "agent_id": agent_id,
                "action_type": action_type,
                "details": details,
                "human_approved": human_approved,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def record_human_oversight(
        self,
        oversight_id: str,
        agent_id: str,
        oversight_type: str,
        reviewer: str,
        outcome: str,
    ) -> None:
        self.human_oversight_records.append(
            {
                "oversight_id": oversight_id,
                "agent_id": agent_id,
                "oversight_type": oversight_type,
                "reviewer": reviewer,
                "outcome": outcome,
                "recorded_at": datetime.utcnow().isoformat(),
            }
        )

    def check_accountability_coverage(self) -> Dict[str, Any]:
        result = {
            "agents_with_responsibility": len(self.responsibility_matrix),
            "total_agents": 0,
            "coverage_rate": 0.0,
            "agents_without_responsibility": [],
        }

        all_agents = {a["agent_id"] for a in self.audit_trail}
        result["total_agents"] = len(all_agents)

        agents_with_resp = set(self.responsibility_matrix.keys())
        result["agents_without_responsibility"] = list(all_agents - agents_with_resp)

        if result["total_agents"] > 0:
            result["coverage_rate"] = (
                result["agents_with_responsibility"] / result["total_agents"]
            )

        return result

    def check_human_oversight_rate(self) -> Dict[str, Any]:
        result = {
            "total_actions": len(self.audit_trail),
            "human_approved_actions": 0,
            "oversight_rate": 0.0,
            "high_risk_without_oversight": [],
        }

        high_risk_types = ["delete", "modify_critical", "access_sensitive", "export"]

        for action in self.audit_trail:
            if action["human_approved"]:
                result["human_approved_actions"] += 1

            if action["action_type"] in high_risk_types and not action["human_approved"]:
                result["high_risk_without_oversight"].append(action["action_id"])

        if result["total_actions"] > 0:
            result["oversight_rate"] = (
                result["human_approved_actions"] / result["total_actions"]
            )

        return result


class AIEthicsAuditAgent:
    def __init__(self, agent_id: str = "ai_ethics_audit_001"):
        self.agent_id = agent_id
        self.fairness_checker = FairnessChecker()
        self.transparency_checker = TransparencyChecker()
        self.safety_checker = SafetyChecker()
        self.accountability_checker = AccountabilityChecker()

        self.ethics_guidelines: Dict[str, str] = {
            "non_discrimination": "AI系统不应对任何群体进行歧视",
            "transparency": "AI决策过程应可解释、可追溯",
            "safety": "AI系统应确保安全，不被恶意利用",
            "privacy": "AI系统应保护用户隐私",
            "human_control": "关键决策应有人类监督",
        }

        self.audit_history: List[Dict] = []

    async def check_fairness(
        self, predictions: Dict[str, List[bool]], protected_attributes: List[str]
    ) -> EthicsCheckResult:
        check_id = f"fairness_{uuid.uuid4().hex[:8]}"

        all_bias_results = []
        issues = []

        for attr in protected_attributes:
            bias_result = self.fairness_checker.check_disparate_impact(
                predictions, attr
            )
            all_bias_results.append(bias_result)

            if bias_result.bias_detected:
                issues.append(
                    f"检测到{attr}属性存在偏见，差异比率: {bias_result.disparity_ratio:.2f}"
                )

        bias_count = sum(1 for r in all_bias_results if r.bias_detected)
        score = 100 * (1 - bias_count / len(protected_attributes)) if protected_attributes else 100

        if bias_count == 0:
            status = EthicsCheckStatus.PASS
        elif bias_count < len(protected_attributes) / 2:
            status = EthicsCheckStatus.WARNING
        else:
            status = EthicsCheckStatus.FAIL

        recommendations = []
        if issues:
            recommendations.append("审查训练数据是否存在偏见")
            recommendations.append("考虑使用公平性约束重新训练模型")
            recommendations.append("实施偏见缓解技术如重采样或对抗学习")

        return EthicsCheckResult(
            check_id=check_id,
            dimension=EthicsDimension.FAIRNESS,
            check_name="公平性检查",
            description="检查AI决策是否存在歧视性偏见",
            status=status,
            score=score,
            details={
                "bias_results": [
                    {
                        "attribute": r.attribute,
                        "disparity_ratio": r.disparity_ratio,
                        "bias_detected": r.bias_detected,
                        "severity": r.severity.value,
                    }
                    for r in all_bias_results
                ]
            },
            issues=issues,
            recommendations=recommendations,
        )

    async def check_transparency(self, sample_size: int = 100) -> EthicsCheckResult:
        check_id = f"transparency_{uuid.uuid4().hex[:8]}"

        coverage = self.transparency_checker.check_explainability_coverage()

        issues = []
        if coverage["coverage_rate"] < 0.8:
            issues.append(f"决策可解释覆盖率不足: {coverage['coverage_rate']:.1%}")

        if len(coverage["unexplained_decisions"]) > 10:
            issues.append(f"存在{len(coverage['unexplained_decisions'])}个未解释的决策")

        score = coverage["coverage_rate"] * 100

        if coverage["coverage_rate"] >= 0.9:
            status = EthicsCheckStatus.PASS
        elif coverage["coverage_rate"] >= 0.7:
            status = EthicsCheckStatus.WARNING
        else:
            status = EthicsCheckStatus.FAIL

        recommendations = []
        if coverage["coverage_rate"] < 0.9:
            recommendations.append("为所有AI决策生成解释")
            recommendations.append("建立决策追溯机制")
            recommendations.append("提供用户可理解的决策说明")

        return EthicsCheckResult(
            check_id=check_id,
            dimension=EthicsDimension.TRANSPARENCY,
            check_name="透明性检查",
            description="检查AI决策是否可解释、可追溯",
            status=status,
            score=score,
            details={
                "coverage_rate": coverage["coverage_rate"],
                "total_decisions": coverage["total_decisions"],
                "explained_decisions": coverage["explained_decisions"],
            },
            issues=issues,
            recommendations=recommendations,
        )

    async def check_safety(self) -> EthicsCheckResult:
        check_id = f"safety_{uuid.uuid4().hex[:8]}"

        compliance = self.safety_checker.check_safety_compliance()

        issues = []
        if not compliance["compliant"]:
            issues.append("安全测试未通过")

        if compliance["total_violations"] > 0:
            issues.append(f"存在{compliance['total_violations']}次安全违规")

        if compliance["recent_violations"]:
            issues.append(f"近7天有{len(compliance['recent_violations'])}次违规")

        score = compliance["pass_rate"] * 100

        if compliance["compliant"] and compliance["pass_rate"] >= 0.95:
            status = EthicsCheckStatus.PASS
        elif compliance["pass_rate"] >= 0.8:
            status = EthicsCheckStatus.WARNING
        else:
            status = EthicsCheckStatus.FAIL

        recommendations = []
        if issues:
            recommendations.append("加强输入过滤和安全边界")
            recommendations.append("定期进行红队测试")
            recommendations.append("建立安全违规响应机制")

        return EthicsCheckResult(
            check_id=check_id,
            dimension=EthicsDimension.SAFETY,
            check_name="安全性检查",
            description="检查AI系统是否安全，不被恶意利用",
            status=status,
            score=score,
            details={
                "total_tests": compliance["total_tests"],
                "pass_rate": compliance["pass_rate"],
                "total_violations": compliance["total_violations"],
            },
            issues=issues,
            recommendations=recommendations,
        )

    async def check_accountability(self) -> EthicsCheckResult:
        check_id = f"accountability_{uuid.uuid4().hex[:8]}"

        coverage = self.accountability_checker.check_accountability_coverage()
        oversight = self.accountability_checker.check_human_oversight_rate()

        issues = []
        if coverage["coverage_rate"] < 1.0:
            issues.append(
                f"存在{len(coverage['agents_without_responsibility'])}个智能体未分配责任"
            )

        if oversight["high_risk_without_oversight"]:
            issues.append(
                f"存在{len(oversight['high_risk_without_oversight'])}个高风险操作未经人工审核"
            )

        score = (coverage["coverage_rate"] * 50 + oversight["oversight_rate"] * 50)

        if coverage["coverage_rate"] >= 1.0 and not oversight["high_risk_without_oversight"]:
            status = EthicsCheckStatus.PASS
        elif coverage["coverage_rate"] >= 0.8 and oversight["oversight_rate"] >= 0.5:
            status = EthicsCheckStatus.WARNING
        else:
            status = EthicsCheckStatus.FAIL

        recommendations = []
        if issues:
            recommendations.append("为所有智能体分配明确责任")
            recommendations.append("对高风险操作实施人工审核")
            recommendations.append("建立完整的审计追踪机制")

        return EthicsCheckResult(
            check_id=check_id,
            dimension=EthicsDimension.ACCOUNTABILITY,
            check_name="问责性检查",
            description="检查AI系统的责任分配和人类监督",
            status=status,
            score=score,
            details={
                "responsibility_coverage": coverage["coverage_rate"],
                "human_oversight_rate": oversight["oversight_rate"],
                "high_risk_without_oversight": len(
                    oversight["high_risk_without_oversight"]
                ),
            },
            issues=issues,
            recommendations=recommendations,
        )

    async def run_full_audit(
        self, predictions: Dict[str, List[bool]] = None, protected_attributes: List[str] = None
    ) -> Dict[str, Any]:
        audit_id = f"ethics_audit_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        results = []

        fairness_result = await self.check_fairness(
            predictions or {"default": [True, False]},
            protected_attributes or ["default"],
        )
        results.append(fairness_result)

        transparency_result = await self.check_transparency()
        results.append(transparency_result)

        safety_result = await self.check_safety()
        results.append(safety_result)

        accountability_result = await self.check_accountability()
        results.append(accountability_result)

        overall_score = sum(r.score for r in results) / len(results)

        critical_issues = [
            f"[{r.dimension.value}] {issue}"
            for r in results
            if r.status == EthicsCheckStatus.FAIL
            for issue in r.issues
        ]

        audit_result = {
            "audit_id": audit_id,
            "audit_time": datetime.utcnow().isoformat(),
            "overall_score": round(overall_score, 2),
            "dimension_results": {
                r.dimension.value: {
                    "status": r.status.value,
                    "score": r.score,
                    "issues": r.issues,
                }
                for r in results
            },
            "critical_issues": critical_issues,
            "recommendations": list(
                set(rec for r in results for rec in r.recommendations)
            ),
        }

        self.audit_history.append(audit_result)
        return audit_result

    def get_ethics_metrics(self) -> Dict[str, Any]:
        if not self.audit_history:
            return {"total_audits": 0, "average_score": 0}

        scores = [a["overall_score"] for a in self.audit_history]
        return {
            "total_audits": len(self.audit_history),
            "average_score": round(sum(scores) / len(scores), 2),
            "latest_score": scores[-1],
            "ethics_guidelines": self.ethics_guidelines,
        }

    def submit_to_ethics_committee(
        self, audit_id: str, committee_members: List[str]
    ) -> Dict[str, Any]:
        audit = next(
            (a for a in self.audit_history if a["audit_id"] == audit_id), None
        )

        if not audit:
            return {"success": False, "error": "Audit not found"}

        submission = {
            "submission_id": f"sub_{uuid.uuid4().hex[:8]}",
            "audit_id": audit_id,
            "committee_members": committee_members,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "pending_review",
            "audit_summary": {
                "overall_score": audit["overall_score"],
                "critical_issues": audit["critical_issues"],
            },
        }

        return {"success": True, "submission": submission}
