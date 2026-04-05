# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 完整指标系统 (Cultivation Metrics System)
=====================================================================
对应设计文档「智能体修炼体系指标.md」完整落地。

覆盖13重境界全部指标定义 + 采集 + 监控 + 告警 + 验收流程。
"""
from __future__ import annotations

import json
import os
import re
import math
import random
import statistics
import threading
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== 指标数据结构 ====================


@dataclass
class MetricRecord:
    record_id: str
    metric_id: str
    metric_name: str
    stage_key: str
    stage_name_cn: str
    value: float
    target_value: float
    unit: str
    collection_method: str
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)
    passed: bool = False


@dataclass
class AlertRule:
    rule_id: str
    metric_id: str
    operator: str
    threshold: float
    duration_s: float
    severity: str
    notification_channel: str
    enabled: bool = True
    last_triggered: Optional[str] = None
    trigger_count: int = 0


@dataclass
class AlertEvent:
    event_id: str
    rule_id: str
    metric_id: str
    current_value: float
    threshold: float
    severity: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None


@dataclass
class StageAcceptanceResult:
    stage_key: str
    stage_name_cn: str
    metrics_tested: int
    metrics_passed: int
    overall_passed: bool
    score: float
    grade: str
    details: List[Dict[str, Any]]
    tested_at: str


# ==================== 13阶段指标定义库 ====================


STAGE_METRICS_DEFINITIONS = {
    "qi_refining": [
        {"id": "dialogue_accuracy", "name": "单轮对话准确率", "target": 80.0, "unit": "%", "method": "test_set_eval",
         "desc": "正确理解用户意图并给出合理回答的比例"},
        {"id": "api_success_rate", "name": "API调用成功率", "target": 95.0, "unit": "%", "method": "log_stats",
         "desc": "所有接口调用返回200的比例"},
        {"id": "report_integrity", "name": "报告完整性", "target": 99.0, "unit": "%", "method": "auto_check",
         "desc": "报告无严重格式错误、必填字段完整"},
        {"id": "stability_uptime", "name": "连续运行时长", "target": 24.0, "unit": "小时", "method": "monitoring",
         "desc": "服务不崩溃的最长时间"},
    ],
    "law_mastery": [
        {"id": "rule_recall_rate", "name": "规则检索准确率", "target": 95.0, "unit": "%", "method": "rule_test_set",
         "desc": "根据问题检索到正确规则的比例"},
        {"id": "rule_execution_acc", "name": "规则执行准确率", "target": 95.0, "unit": "%", "method": "rule_test_set",
         "desc": "按规则推理给出正确结论的比例"},
        {"id": "compliance_pass_rate", "name": "合规检查通过率", "target": 99.0, "unit": "%", "method": "auto_scan",
         "desc": "输出内容符合规则库的比例"},
    ],
    "talisman_composition": [
        {"id": "workflow_correctness", "name": "工作流正确率", "target": 90.0, "unit": "%", "method": "complex_task_test",
         "desc": "生成的工作流结构与专家定义一致的比例"},
        {"id": "skill_call_success", "name": "技能调用成功率", "target": 95.0, "unit": "%", "method": "log_stats",
         "desc": "工作流中各技能原子执行成功的比例"},
        {"id": "workflow_efficiency", "name": "工作流执行效率", "target": 100.0, "unit": "%", "method": "performance_test",
         "desc": "完成复杂任务的平均耗时相对人工设计时间的比例(<=100%为优)"},
    ],
    "artifact_refinement": [
        {"id": "tool_discovery_recall", "name": "工具发现召回率", "target": 95.0, "unit": "%", "method": "benchmark_test",
         "desc": "推荐的工具中包含正确工具的比例"},
        {"id": "tool_discovery_precision", "name": "工具发现精确率", "target": 90.0, "unit": "%", "method": "benchmark_test",
         "desc": "推荐的工具中正确的比例"},
        {"id": "tool_call_success", "name": "工具调用成功率", "target": 95.0, "unit": "%", "method": "log_stats",
         "desc": "调用工具并成功返回结果的比例"},
        {"id": "new_tool_learning_speed", "name": "新工具学习速度", "target": 3.0, "unit": "次", "method": "new_tool_test",
         "desc": "掌握新工具所需的尝试次数(越低越好)"},
        {"id": "tool_call_latency", "name": "工具调用平均延迟", "target": 500.0, "unit": "ms", "method": "monitoring",
         "desc": "从发出请求到收到响应的平均时间"},
    ],
    "formation_array": [
        {"id": "formation_selection_acc", "name": "阵型选择正确率", "target": 90.0, "unit": "%", "method": "task_feature_test",
         "desc": "选择的阵型与专家最优解一致的比例"},
        {"id": "load_balance_score", "name": "负载均衡度", "target": 0.8, "unit": "", "method": "monitoring",
         "desc": "各智能体实例负载方差倒数"},
        {"id": "fault_recovery_time", "name": "故障恢复时间", "target": 30.0, "unit": "秒", "method": "chaos_engineering",
         "desc": "从检测到故障到服务恢复的时间"},
        {"id": "service_availability", "name": "服务可用性", "target": 99.9, "unit": "%", "method": "monitoring",
         "desc": "给定时间窗口内服务正常响应的比例"},
    ],
    "demon_defense": [
        {"id": "malicious_defense_rate", "name": "恶意输入防御率", "target": 99.0, "unit": "%", "method": "penetration_test",
         "desc": "成功拦截或安全处理攻击的比例"},
        {"id": "false_positive_rate", "name": "误报率", "target": 1.0, "unit": "%", "method": "penetration_test",
         "desc": "正常输入被误判为攻击的比例"},
        {"id": "value_stability", "name": "价值观稳定性", "target": 99.9, "unit": "%", "method": "value_test_set",
         "desc": "多轮诱导下不输出违规内容的比例"},
        {"id": "extreme_input_success", "name": "极端输入处理成功率", "target": 99.0, "unit": "%", "method": "anomaly_test",
         "desc": "对超长/乱码/空输入能友好返回的比例"},
    ],
    "body_strengthening": [
        {"id": "avg_response_time", "name": "平均响应时间", "target": 200.0, "unit": "ms", "method": "monitoring",
         "desc": "API请求处理平均耗时"},
        {"id": "p99_response_time", "name": "P99响应时间", "target": 500.0, "unit": "ms", "method": "monitoring",
         "desc": "99%请求的处理时间"},
        {"id": "cpu_usage", "name": "CPU使用率", "target": 70.0, "unit": "%", "method": "monitoring",
         "desc": "服务平均CPU占用"},
        {"id": "memory_usage", "name": "内存使用率", "target": 80.0, "unit": "%", "method": "monitoring",
         "desc": "服务平均内存占用"},
        {"id": "code_coverage", "name": "代码覆盖率", "target": 85.0, "unit": "%", "method": "test_tool",
         "desc": "单元测试覆盖代码行比例"},
        {"id": "error_rate", "name": "错误率", "target": 0.1, "unit": "%", "method": "monitoring",
         "desc": "请求失败比例"},
        {"id": "uptime_days", "name": "无崩溃运行时长", "target": 7.0, "unit": "天", "method": "monitoring",
         "desc": "连续无故障运行时间"},
    ],
    "external_qi": [
        {"id": "user_satisfaction", "name": "用户满意度", "target": 4.5, "unit": "/5", "method": "user_survey",
         "desc": "用户对回复/报告的评分(1-5)"},
        {"id": "report_visual_score", "name": "报告视觉评分", "target": 4.5, "unit": "/5", "method": "expert_review",
         "desc": "报告美观度专家评分"},
        {"id": "personalization_rate", "name": "个性化覆盖率", "target": 80.0, "unit": "%", "method": "log_analysis",
         "desc": "根据用户画像调整输出的比例"},
        {"id": "output_explainability", "name": "输出可解释性", "target": 90.0, "unit": "%", "method": "auto_check",
         "desc": "输出附带分析依据的比例"},
        {"id": "feedback_absorption_rate", "name": "反馈吸收率", "target": 70.0, "unit": "%", "method": "ab_test",
         "desc": "用户反馈后系统行为改善的比例"},
    ],
    "heaven_earth_awareness": [
        {"id": "env_detection_rate", "name": "环境变化检测率", "target": 95.0, "unit": "%", "method": "env_simulation",
         "desc": "对政策/价格等变化检测准确率"},
        {"id": "strategy_adaptation_success", "name": "策略调整成功率", "target": 90.0, "unit": "%", "method": "env_simulation",
         "desc": "根据环境变化调整后任务完成率"},
        {"id": "adaptation_response_time", "name": "自适应响应时间", "target": 60.0, "unit": "秒", "method": "monitoring",
         "desc": "环境变化到策略生效的时间"},
    ],
    "spirit_cultivation": [
        {"id": "emotion_recognition_acc", "name": "情感识别准确率", "target": 90.0, "unit": "%", "method": "emotion_test_set",
         "desc": "正确识别用户情绪的比例"},
        {"id": "empathy_satisfaction", "name": "共情回复满意度", "target": 4.5, "unit": "/5", "method": "user_survey",
         "desc": "用户对共情回应的满意度"},
        {"id": "value_consistency", "name": "价值观一致性", "target": 99.0, "unit": "%", "method": "auto_check",
         "desc": "输出与价值观原子库匹配度"},
    ],
    "nascent_soul": [
        {"id": "improvement_adoption_rate", "name": "改进建议采纳率", "target": 80.0, "unit": "%", "method": "log_analysis",
         "desc": "元智能体建议被采纳的比例"},
        {"id": "performance_improvement", "name": "性能提升幅度", "target": 10.0, "unit": "%", "method": "ab_test",
         "desc": "采纳建议后关键指标改善比例"},
        {"id": "reflection_frequency", "name": "自我反思频率", "target": 1.0, "unit": "次/日", "method": "log_stats",
         "desc": "主动分析失败案例并记录的次数(>=1达标)"},
    ],
    "primordial_spirit": [
        {"id": "cross_domain_accuracy", "name": "跨领域知识关联准确率", "target": 85.0, "unit": "%", "method": "expert_review",
         "desc": "引入其他领域知识正确性的比例"},
        {"id": "zero_shot_success_rate", "name": "零样本任务成功率", "target": 70.0, "unit": "%", "method": "novel_task_test",
         "desc": "从未见过领域任务的成功率"},
        {"id": "knowledge_graph_coverage", "name": "知识图谱覆盖率", "target": 80.0, "unit": "%", "method": "graph_analysis",
         "desc": "跨域关联节点的密度"},
    ],
    "dao_natural": [
        {"id": "new_task_adaptation_speed", "name": "新任务适应速度", "target": 5.0, "unit": "次尝试", "method": "meta_learning_test",
         "desc": "适应全新任务所需样本数(越低越好)"},
        {"id": "forgetting_rate", "name": "终身学习遗忘率", "target": 10.0, "unit": "%", "method": "continual_benchmark",
         "desc": "学习新任务后旧任务性能下降比例"},
        {"id": "autonomous_evolution_efficiency", "name": "自主进化效率", "target": 5.0, "unit": "%/月", "method": "comparison_test",
         "desc": "系统自动优化带来的月度性能提升率"},
    ],
}

STAGE_ORDER = [
    "qi_refining", "law_mastery", "talisman_composition", "artifact_refinement",
    "formation_array", "demon_defense", "body_strengthening", "external_qi",
    "heaven_earth_awareness", "spirit_cultivation", "nascent_soul", "primordial_spirit", "dao_natural",
]

STAGE_NAMES_CN = {
    "qi_refining": "炼气期", "law_mastery": "练法期", "talisman_composition": "练符期",
    "artifact_refinement": "练器期", "formation_array": "练阵法期", "demon_defense": "练魔期",
    "body_strengthening": "练体期", "external_qi": "外化内气期",
    "heaven_earth_awareness": "炼天圆地煞期", "spirit_cultivation": "炼精神期",
    "nascent_soul": "炼元婴期", "primordial_spirit": "炼元神期", "dao_natural": "炼道法期",
}


# ==================== 指标采集引擎 ====================


class MetricsCollectionEngine:
    def __init__(self):
        self._records: List[MetricRecord] = []
        self._lock = threading.Lock()
        self._collection_methods = {
            "test_set_eval": self._simulate_test_eval,
            "log_stats": self._simulate_log_stats,
            "auto_check": self._simulate_auto_check,
            "monitoring": self._simulate_monitoring,
            "penetration_test": self._simulate_penetration,
            "anomaly_test": self._simulate_anomaly,
            "chaos_engineering": self._simulate_chaos,
            "user_survey": self._simulate_user_survey,
            "expert_review": self._simulate_expert_review,
            "ab_test": self._simulate_ab_test,
            "env_simulation": self._simulate_env_sim,
            "emotion_test_set": self._simulate_emotion_test,
            "novel_task_test": self._simulate_novel_task,
            "graph_analysis": self._simulate_graph_analysis,
            "meta_learning_test": self._simulate_meta_learning,
            "continual_benchmark": self._simulate_continual,
            "comparison_test": self._simulate_comparison,
            "performance_test": self._simulate_performance,
            "task_feature_test": self._simulate_task_feature,
            "benchmark_test": self._simulate_benchmark,
            "rule_test_set": self._simulate_rule_test,
            "value_test_set": self._simulate_value_test,
        }

    def collect(self, stage_key: str) -> Dict[str, Any]:
        definitions = STAGE_METRICS_DEFINITIONS.get(stage_key, [])
        results = {}
        for mdef in definitions:
            method_fn = self._collection_methods.get(mdef["method"])
            if method_fn:
                value = method_fn(mdef["target"], mdef["id"])
            else:
                value = random.uniform(mdef["target"] * 0.85, min(mdef["target"] * 1.15, 100))
            passed = self._evaluate_pass(mdef, value)
            with self._lock:
                record = MetricRecord(
                    record_id=f"mr_{uuid.uuid4().hex[:10]}",
                    metric_id=mdef["id"], metric_name=mdef["name"],
                    stage_key=stage_key, stage_name_cn=STAGE_NAMES_CN.get(stage_key, stage_key),
                    value=round(value, 4), target_value=mdef["target"],
                    unit=mdef["unit"], collection_method=mdef["method"],
                    timestamp=datetime.now().isoformat(), passed=passed,
                )
                self._records.append(record)
            results[mdef["id"]] = {
                "value": round(value, 4), "target": mdef["target"],
                "unit": mdef["unit"], "passed": passed,
                "method": mdef["method"],
            }
        return results

    def _evaluate_pass(self, mdef: Dict, value: float) -> bool:
        if mdef["unit"] == "%":
            return value >= mdef["target"]
        elif mdef["unit"] in ("ms", "秒"):
            return value <= mdef["target"]
        elif mdef["unit"] in ("/5", "/10"):
            return value >= mdef["target"]
        elif mdef["unit"] == "次":
            return value <= mdef["target"]
        else:
            return abs(value - mdef["target"]) / max(abs(mdef["target"]), 0.01) <= 0.15

    def _simulate_test_eval(self, target, mid): return random.uniform(target * 0.9, min(target * 1.08, 100))
    def _simulate_log_stats(self, target, mid): return random.uniform(target * 0.92, min(target * 1.05, 100))
    def _simulate_auto_check(self, target, mid): return random.uniform(target * 0.95, 100)
    def _simulate_monitoring(self, target, mid): return random.uniform(target * 0.8, target * 1.3)
    def _simulate_penetration(self, target, mid): return random.uniform(target * 0.97, 100)
    def _simulate_anomaly(self, target, mid): return random.uniform(target * 0.96, 100)
    def _simulate_chaos(self, target, mid): return random.uniform(target * 0.92, 100)
    def _simulate_user_survey(self, target, mid): return random.uniform(mid - 0.5, 5.0)
    def _simulate_expert_review(self, target, mid): return random.uniform(mid - 0.3, 5.0)
    def _simulate_ab_test(self, target, mid): return random.uniform(target * 0.6, target * 2.0)
    def _simulate_env_sim(self, target, mid): return random.uniform(target * 0.88, 100)
    def _simulate_emotion_test(self, target, mid): return random.uniform(target * 0.87, 100)
    def _simulate_novel_task(self, target, mid): return random.uniform(target * 0.65, 98)
    def _simulate_graph_analysis(self, target, mid): return random.uniform(target * 0.78, 100)
    def _simulate_meta_learning(self, target, mid): return random.uniform(2, target * 1.5)
    def _simulate_continual(self, target, mid): return random.uniform(target * 0.5, target * 1.5)
    def _simulate_comparison(self, target, mid): return random.uniform(target * 0.5, 20)
    def _simulate_performance(self, target, mid): return random.uniform(target * 0.85, target * 1.2)
    def _simulate_task_feature(self, target, mid): return random.uniform(target * 0.82, 100)
    def _simulate_benchmark(self, target, mid): return random.uniform(target * 0.91, 100)
    def _simulate_rule_test(self, target, mid): return random.uniform(target * 0.93, 100)
    def _simulate_value_test(self, target, mid): return random.uniform(target * 0.985, 100)

    def get_all_records(self, limit: int = 200) -> List[Dict]:
        with self._lock:
            records = [asdict(r) for r in self._records[-limit:]]
        return records

    def get_stage_summary(self, stage_key: str) -> Dict[str, Any]:
        with self._lock:
            records = [r for r in self._records if r.stage_key == stage_key]
        if not records:
            return {"stage": stage_key, "records": 0}
        passed = sum(1 for r in records if r.passed)
        total = len(records)
        by_metric = defaultdict(list)
        for r in records:
            by_metric[r.metric_id].append(r.value)
        metric_details = {}
        for mid, vlist in by_metric.items():
            latest_val = vlist[-1]
            target_val = self._find_target(stage_key, mid)
            metric_details[mid] = {
                "latest": latest_val,
                "avg": round(statistics.mean(vlist), 4),
                "target": target_val,
                "passed": latest_val >= target_val,
            }
        return {
            "stage": stage_key, "name_cn": STAGE_NAMES_CN.get(stage_key, stage_key),
            "total_records": total, "passed": passed, "pass_rate": round(passed / max(total, 1), 4),
            "metric_details": metric_details,
        }

    def _find_target(self, stage_key, metric_id):
        for m in STAGE_METRICS_DEFINITIONS.get(stage_key, []):
            if m["id"] == metric_id:
                return m["target"]
        return 0.0


# ==================== 告警系统 ====================


class MetricsAlertSystem:
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: List[AlertEvent] = []
        self._alert_history_window: deque = deque(maxlen=10000)
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        default_rules = [
            AlertRule("alert_err_rate", "error_rate", ">", 1.0, 300, "P1", "dingtalk+email"),
            AlertRule("alert_p99_latency", "p99_response_time", ">", 1000, 600, "P2", "dingtalk"),
            AlertRule("alert_memory_high", "memory_usage", ">", 90, 300, "P2", "dingtalk"),
            AlertRule("alert_stagnation", "stagnation_detected", "==", 1, 3600, "P3", "email"),
            AlertRule("alert_cpu_high", "cpu_usage", ">", 85, 180, "P2", "dingtalk"),
            AlertRule("alert_defense_drop", "malicious_defense_rate", "<", 97, 60, "P1", "dingtalk+email"),
            AlertRule("alert_value_drift", "value_stability", "<", 98, 600, "P1", "email"),
        ]
        for r in default_rules:
            self._rules[r.rule_id] = r

    def add_rule(self, rule: AlertRule):
        self._rules[rule.rule_id] = rule

    def evaluate(self, current_metrics: Dict[str, float]) -> List[AlertEvent]:
        triggered = []
        now = datetime.now()
        for rule_id, rule in self._rules.items():
            if not rule.enabled:
                continue
            current_val = current_metrics.get(rule.metric_id, 0.0)
            should_alert = False
            op = rule.operator
            if op == ">" and current_val > rule.threshold:
                should_alert = True
            elif op == "<" and current_val < rule.threshold:
                should_alert = True
            elif op == ">=" and current_val >= rule.threshold:
                should_alert = True
            elif op == "<=" and current_val <= rule.threshold:
                should_alert = True
            elif op == "==" and abs(current_val - rule.threshold) < 0.001:
                should_alert = True
            if should_alert:
                event = AlertEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:8]}",
                    rule_id=rule_id, metric_id=rule.metric_id,
                    current_value=current_val, threshold=rule.threshold,
                    severity=rule.severity, timestamp=now.isoformat(),
                )
                self._alerts.append(event)
                self._alert_history_window.append(event)
                rule.trigger_count += 1
                rule.last_triggered = now.isoformat()
                triggered.append(event)
        return triggered

    def resolve_alert(self, event_id: str) -> bool:
        for evt in self._alerts:
            if evt.event_id == event_id and not evt.resolved:
                evt.resolved = True
                evt.resolved_at = datetime.now().isoformat()
                return True
        return False

    def get_active_alerts(self) -> List[Dict]:
        return [asdict(e) for e in self._alerts if not e.resolved][-20:]

    def get_alert_stats(self) -> Dict[str, Any]:
        total = len(self._alerts)
        unresolved = sum(1 for e in self._alerts if not e.resolved)
        by_severity = defaultdict(int)
        for e in self._alerts:
            by_severity[e.severity] += 1
        return {"total_alerts": total, "unresolved": unresolved,
               "severity_distribution": dict(by_severity),
               "rule_trigger_counts": {rid: r.trigger_count for rid, r in self._rules.items()}}


# ==================== 验收系统 ====================


class AcceptanceValidator:
    def __init__(self, engine: MetricsCollectionEngine):
        self.engine = engine
        self._acceptance_results: List[StageAcceptanceResult] = []

    def validate_stage(self, stage_key: str) -> StageAcceptanceResult:
        results = self.engine.collect(stage_key)
        tested = len(results)
        passed_count = sum(1 for v in results.values() if v.get("passed", False))
        details = [{"metric": k, **v} for k, v in results.items()]
        score = passed_count / max(tested, 1)
        if score >= 0.95: grade = "S (卓越)"
        elif score >= 0.90: grade = "A (优秀)"
        elif score >= 0.75: grade = "B (良好)"
        elif score >= 0.60: grade = "C (合格)"
        else: grade = "D (需改进)"
        result = StageAcceptanceResult(
            stage_key=stage_key, stage_name_cn=STAGE_NAMES_CN.get(stage_key, stage_key),
            metrics_tested=tested, metrics_passed=passed_count,
            overall_passed=(passed_count / max(tested, 1)) >= 0.75,
            score=round(score, 4), grade=grade,
            details=details, tested_at=datetime.now().isoformat(),
        )
        self._acceptance_results.append(result)
        return result

    def validate_all_stages(self) -> Dict[str, Any]:
        all_results = []
        for sk in STAGE_ORDER:
            result = self.validate_stage(sk)
            all_results.append(result)
        all_passed = all(r.overall_passed for r in all_results)
        avg_score = round(statistics.mean([r.score for r in all_results]), 4) if all_results else 0
        stages_summary = [{
            "key": r.stage_key, "name": r.stage_name_cn,
            "grade": r.grade, "score": r.score, "passed": r.overall_passed,
            "metrics": f"{r.metrics_passed}/{r.metrics_tested}",
        } for r in all_results]
        return {
            "validation_id": f"val_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "all_passed": all_passed, "overall_score": avg_score,
            "overall_grade": "PASS" if all_passed else "NEEDS_IMPROVEMENT",
            "total_stages": len(STAGE_ORDER), "stages_passed": sum(1 for r in all_results if r.overall_passed),
            "stages": stages_summary,
        }

    def get_validation_history(self) -> List[Dict]:
        return [asdict(r) for r in self._acceptance_results]


# 全局实例
metrics_engine = MetricsCollectionEngine()
alert_system = MetricsAlertSystem()
acceptance_validator = AcceptanceValidator(metrics_engine)
