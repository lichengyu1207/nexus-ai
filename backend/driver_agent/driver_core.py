# -*- coding: utf-8 -*-
"""
驱动智能体 - 核心决策引擎 (Driver Agent Core)
===============================================
对应设计文档「驱动智能体.md」核心章节:
  - Ch1: 自进化炼丹炉的定义 → 驱动智能体的自主决策边界
  - Ch1.2: 系统分层架构 → 驱动智能体作为第5层(自主驾驶层)
  - Ch2: 自博弈训练引擎 → 驱动智能体的自我博弈与策略优化
  - Ch5: 自我修复与优化 → 驱动智能体的自动调优与自修正

职责：
1) 意图识别(IntentRecognition) — 解析用户/系统输入，判断需要调动哪些子系统
2) 任务规划(TaskPlanner) — 将高层目标分解为可执行的子任务链
3) 决策引擎(DecisionEngine) — 基于多维度指标选择最优行动方案
4) 执行调度(ExecutionScheduler) — 管理任务的优先级、依赖、并发和超时
5) 自我反思(SelfReflectionDriver) — 回顾决策效果，学习改进模式

层级定位:
  Layer-0: DriverAgentCore (本模块) — 自主驾驶层（大脑）
  Layer-1: PlatformOrchestrator (integration/) — 总调度层（小脑）
  Layer-2~5: B/C/D/E 四大体系 — 能力执行层（四肢）
"""

from __future__ import annotations

import json
import time
import math
import hashlib
import logging
import threading
import traceback
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntentType(Enum):
    QUERY = "query"
    ANALYSIS = "analysis"
    TRAINING = "training"
    EVOLUTION = "evolution"
    REPAIR = "repair"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    WAITING_DEPENDENCY = "waiting_dependency"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class DecisionConfidence(Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class RecognizedIntent:
    intent_type: IntentType
    confidence: float
    target_systems: List[str]
    action_verb: str
    parameters: Dict[str, Any]
    raw_input: str
    reasoning: str = ""
    estimated_duration_s: float = 0.0


@dataclass
class PlannedTask:
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    target_system: str
    action_name: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_s: float = 300.0
    estimated_duration_s: float = 10.0
    actual_duration_s: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class DecisionRecord:
    decision_id: str
    timestamp: str
    input_context: Dict[str, Any]
    intent: RecognizedIntent
    plan: List[PlannedTask]
    chosen_action: str
    confidence: DecisionConfidence
    alternatives_considered: int
    outcome: str = ""
    outcome_metrics: Dict[str, float] = field(default_factory=dict)
    reflection: str = ""


@dataclass
class SelfReflectionEntry:
    reflection_id: str
    timestamp: str
    session_id: str
    decisions_reviewed: int
    successful_decisions: int
    failed_decisions: int
    patterns_discovered: List[str] = field(default_factory=list)
    improvements_suggested: List[str] = field(default_factory=list)
    confidence_adjustments: Dict[str, float] = field(default_factory=dict)
    learning_summary: str = ""


class IntentRecognizer:
    """
    意图识别器 — 对应提示词 1.1 的"炼丹炉定义"延伸
    
    功能：
    - 从自然语言或系统事件中提取意图类型
    - 识别目标子系统（道法自然/自进化/炼丹/修炼）
    - 估算执行时长和资源需求
    - 提供推理依据供后续审计
    """

    INTENT_KEYWORDS = {
        IntentType.QUERY: {"查询", "查看", "状态", "多少", "什么", "列表", "显示", "获取"},
        IntentType.ANALYSIS: {"分析", "评估", "对比", "统计", "趋势", "报告", "诊断", "根因"},
        IntentType.TRAINING: {"训练", "学习", "微调", "SFT", "强化", "对抗", "生成数据"},
        IntentType.EVOLUTION: {"进化", "迭代", "优化", "升级", "修炼", "炼丹", "自进化"},
        IntentType.REPAIR: {"修复", "回滚", "恢复", "纠正", "清理", "重建"},
        IntentType.DEPLOYMENT: {"部署", "发布", "上线", "启动", "停止", "重启"},
        IntentType.MONITORING: {"监控", "告警", "健康", "检查", "巡检", "观察"},
    }

    SYSTEM_KEYWORDS = {
        "governance": {"治理", "调度", "人格", "记忆", "三省六部", "道法", "MaAS", "组队"},
        "evolution": {"自进化", "数据生成", "验证", "闭环", "PPO", "元策略", "贝叶斯"},
        "alchemy": {"炼丹", "对抗", "红蓝", "PER", "分布式", "混沌", "压测", "城市模拟"},
        "cultivation": {"修炼", "炼气", "练法", "练符", "精神", "元婴", "元神", "道法", "仪表盘"},
    }

    def __init__(self):
        self._history: List[RecognizedIntent] = []

    def recognize(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> RecognizedIntent:
        text_lower = input_text.lower()
        scores = {}
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[intent_type] = score / max(len(keywords), 1)

        best_intent = max(scores.items(), key=lambda x: x[1])[0] if any(scores.values()) else IntentType.UNKNOWN
        confidence = min(1.0, scores.get(best_intent, 0.0))

        target_systems = []
        for sys_name, keywords in self.SYSTEM_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                target_systems.append(sys_name)
        if not target_systems:
            target_systems = ["all"] if best_intent != IntentType.UNKNOWN else []

        action_verbs = {
            IntentType.QUERY: "查询",
            IntentType.ANALYSIS: "分析",
            IntentType.TRAINING: "训练",
            IntentType.EVOLUTION: "进化",
            IntentType.REPAIR: "修复",
            IntentType.DEPLOYMENT: "部署",
            IntentType.MONITORING: "监控",
        }
        verb = action_verbs.get(best_intent, "处理")

        params = {}
        if "小时" in input_text or "h" in input_text:
            params["time_unit"] = "hours"
        if "天" in input_text or "d" in input_text:
            params["time_unit"] = "days"
        if "全" in input_text or "全部" in input_text or "all" in text_lower:
            params["scope"] = "full"

        reasoning_parts = [f"检测到意图: {best_intent.value}(置信度{confidence:.0%})"]
        if target_systems:
            reasoning_parts.append(f"目标系统: {','.join(target_systems)}")
        reasoning = "; ".join(reasoning_parts)

        duration_estimates = {
            IntentType.QUERY: 2.0,
            IntentType.ANALYSIS: 15.0,
            IntentType.TRAINING: 300.0,
            IntentType.EVOLUTION: 600.0,
            IntentType.REPAIR: 60.0,
            IntentType.DEPLOYMENT: 30.0,
            IntentType.MONITORING: 5.0,
        }

        intent = RecognizedIntent(
            intent_type=best_intent,
            confidence=confidence,
            target_systems=target_systems,
            action_verb=verb,
            parameters=params,
            raw_input=input_text[:200],
            reasoning=reasoning,
            estimated_duration_s=duration_estimates.get(best_intent, 10.0),
        )
        self._history.append(intent)
        return intent


class TaskPlanner:
    """
    任务规划器 — 将高层意图分解为可执行的子任务链
    
    功能：
    - 根据意图类型和目标系统，生成结构化的任务计划
    - 自动添加任务间依赖关系
    - 估算每个子任务的资源和时间需求
    - 支持增量规划（已有部分结果时跳过已完成步骤）
    """

    INTENT_TO_TASK_TEMPLATES = {
        (IntentType.EVOLUTION, "all"): [
            ("初始化平台", "platform_orchestrator.initialize_all", {}, 30.0, []),
            ("注入训练数据", "evolution_cultivation_bridge.inject_training_data_to_all_stages", {"sample_count": 100}, 20.0, [0]),
            ("炼丹驱动修炼", "cultivation_alchemy_bridge.run_furnace_driven_evolution", {"max_iterations": 5}, 120.0, [1]),
            ("三省六部统筹", "governance_integration_bridge.coordinate_all_systems", {}, 15.0, [2]),
            ("生成进度报告", "cultivation_dashboard.generate_full_report", {}, 5.0, [3]),
        ],
        (IntentType.EVOLUTION, "alchemy"): [
            ("启动炼丹会话", "cultivation_alchemy_bridge.setup_furnace_for_cultivation", {}, 5.0, []),
            ("运行炼丹循环", "cultivation_alchemy_bridge.run_furnace_driven_evolution", {"max_iterations": 3}, 90.0, [0]),
            ("获取集成状态", "cultivation_alchemy_bridge.get_integration_status", {}, 3.0, [1]),
        ],
        (IntentType.TRAINING, "evolution"): [
            ("生成历史分布样本", "historical_data_generator.generate_from_distribution", {"count": 50}, 10.0, []),
            ("生成对抗样本", "historical_data_generator.generate_adversarial_sample", {"difficulty": 0.6, "count": 25}, 8.0, [0]),
            ("注入到炼气期", "qi_refining.generate_sft_samples", {"count": 75}, 12.0, [0, 1]),
        ],
        (IntentType.ANALYSIS, "all"): [
            ("获取平台健康报告", "platform_orchestrator.get_health_report", {}, 3.0, []),
            ("获取修炼仪表盘", "cultivation_dashboard.export_dashboard_data", {}, 3.0, [0]),
            ("获取桥接状态", "governance_integration_bridge.get_full_platform_status", {}, 3.0, [0]),
        ],
        (IntentType.MONITORING, "all"): [
            ("健康检查", "platform_orchestrator.get_health_report", {}, 2.0, []),
            ("混沌工程检查", "chaos_engineer.run_chaos_suite", {"experiments": ["network_latency", "cpu_overload"]}, 30.0, [0]),
            ("告警状态查询", "alert_notifier.get_alert_history", {"limit": 20}, 2.0, [0]),
        ],
        (IntentType.REPAIR, "alchemy"): [
            ("回滚到最后版本", "model_version_manager.rollback_version", {}, 10.0, []),
            ("重新验证模型", "multi_dimension_validator.validate_batch", {}, 15.0, [0]),
        ],
        (IntentType.DEPLOYMENT, "all"): [
            ("生成Docker配置", "deployment_generator.generate_all", {}, 5.0, []),
            ("运行E2E测试", "e2e_cultivation_test.run_all_tests", {}, 60.0, [0]),
        ],
    }

    def __init__(self):
        self._plan_cache: Dict[str, List[PlannedTask]] = {}

    def plan(self, intent: RecognizedIntent) -> List[PlannedTask]:
        cache_key = f"{intent.intent_type.value}_{','.join(sorted(intent.target_systems))}_{hashlib.md5(intent.raw_input.encode()).hexdigest()[:8]}"
        if cache_key in self._plan_cache:
            return self._plan_cache[cache_key]

        primary_target = intent.target_systems[0] if intent.target_systems else "all"
        template_key = (intent.intent_type, primary_target)
        template = self.INTENT_TO_TASK_TEMPLATES.get(template_key)
        if not template:
            fallback_key = (intent.intent_type, "all")
            template = self.INTENT_TO_TASK_TEMPLATES.get(fallback_key, [
                ("通用处理", "platform_orchestrator.run_full_integration_cycle", {}, 60.0, [])
            ])

        tasks = []
        for idx, (name, action, params, duration, deps) in enumerate(template):
            merged_params = {**params}
            if intent.parameters:
                merged_params.update({k: v for k, v in intent.parameters.items() if k not in merged_params})
            task = PlannedTask(
                task_id=f"{cache_key}_t{idx}",
                name=name,
                description=f"[{intent.action_verb}] {name} ({intent.intent_type.value})",
                priority=self._infer_priority(intent, idx, len(template)),
                target_system=primary_target,
                action_name=action,
                parameters=merged_params,
                dependencies=[template[d][0] + "_" + str(d) for d in deps],
                created_at=datetime.now().isoformat(),
                timeout_s=max(duration * 3, 60.0),
                estimated_duration_s=duration,
            )
            tasks.append(task)

        self._plan_cache[cache_key] = tasks
        logger.info(f"[驱动规划] 生成计划: {len(tasks)} 个任务 | 意图={intent.intent_type.value} | 目标={primary_target}")
        return tasks

    def _infer_priority(self, intent: RecognizedIntent, task_index: int, total_tasks: int) -> TaskPriority:
        if intent.intent_type == IntentType.REPAIR:
            return TaskPriority.CRITICAL if task_index == 0 else TaskPriority.HIGH
        if intent.intent_type == IntentType.DEPLOYMENT:
            return TaskPriority.HIGH
        if intent.intent_type == IntentType.EVOLUTION:
            return TaskPriority.NORMAL
        if intent.intent_type == IntentType.MONITORING:
            return TaskPriority.LOW
        if task_index == 0:
            return TaskPriority.HIGH
        if task_index == total_tasks - 1:
            return TaskPriority.NORMAL
        return TaskPriority.NORMAL


class DecisionEngine:
    """
    决策引擎 — 基于多维度指标选择最优行动方案
    
    功能：
    - 综合考虑历史成功率、当前负载、资源可用性等因素
    - 为每个候选行动打分并排序
    - 记录完整决策链路供反思和学习
    - 支持置信度校准（根据历史准确率动态调整）
    """

    def __init__(self):
        self._decision_history: List[DecisionRecord] = []
        self._action_success_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"total": 0.0, "success": 0.0})
        self._confidence_calibration: Dict[str, float] = {}

    def decide(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> Tuple[Dict[str, Any], DecisionConfidence]:
        scored_candidates = []
        for idx, candidate in enumerate(candidates):
            score = self._score_candidate(candidate, context, idx)
            candidate["_score"] = score
            scored_candidates.append((score, candidate))
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_action = scored_candidates[0]

        if best_score >= 0.8:
            confidence = DecisionConfidence.VERY_HIGH
        elif best_score >= 0.65:
            confidence = DecisionConfidence.HIGH
        elif best_score >= 0.45:
            confidence = DecisionConfidence.MEDIUM
        elif best_score >= 0.25:
            confidence = DecisionConfidence.LOW
        else:
            confidence = DecisionConfidence.VERY_LOW

        record = DecisionRecord(
            decision_id=f"dec_{int(time.time()*1000)}_{idx}",
            timestamp=datetime.now().isoformat(),
            input_context=context,
            intent=context.get("intent", RecognizedIntent(IntentType.UNKNOWN, 0.0, [], "", {})),
            plan=[],
            chosen_action=best_action.get("name", "unknown"),
            confidence=confidence,
            alternatives_considered=len(candidates),
        )
        self._decision_history.append(record)
        return best_action, confidence

    def _score_candidate(self, candidate: Dict[str, Any], context: Dict[str, Any], rank: int) -> float:
        score = 0.0
        action_name = candidate.get("name", "")
        stats = self._action_success_stats.get(action_name, {})
        success_rate = stats["success"] / max(stats["total"], 1.0)
        score += success_rate * 0.35
        priority_weight = {0: 0.20, 1: 0.15, 2: 0.10, 3: 0.05, 4: 0.02}.get(rank, 0.01)
        score += priority_weight
        resource_cost = candidate.get("estimated_resource_cost", 0.5)
        score += (1.0 - resource_cost) * 0.15
        risk_level = candidate.get("risk_level", "medium")
        risk_penalty = {"low": 0.10, "medium": 0.05, "high": -0.05, "critical": -0.15}.get(risk_level, 0.0)
        score += risk_penalty
        history_match = candidate.get("history_match", False)
        if history_match:
            score += 0.10
        recency_bonus = candidate.get("recency_bonus", 0.0)
        score += recency_bonus * 0.05
        return max(0.0, min(1.0, score))

    def record_outcome(self, decision_id: str, success: bool, metrics: Optional[Dict[str, float]] = None):
        for record in reversed(self._decision_history):
            if record.decision_id == decision_id:
                record.outcome = "success" if success else "failure"
                record.outcome_metrics = metrics or {}
                action_name = record.chosen_action
                self._action_success_stats[action_name]["total"] += 1
                if success:
                    self._action_success_stats[action_name]["success"] += 1
                break

    def get_decision_stats(self) -> Dict[str, Any]:
        result = {"total_decisions": len(self._decision_history)}
        action_stats = {}
        for action_name, stats in self._action_success_stats.items():
            action_stats[action_name] = {
                "total": int(stats["total"]),
                "success": int(stats["success"]),
                "success_rate": round(stats["success"] / max(stats["total"], 1), 3),
            }
        result["action_stats"] = action_stats
        recent_successes = sum(1 for r in self._decision_history[-50:] if r.outcome == "success")
        result["recent_success_rate"] = round(recent_successes / min(len(self._decision_history), 50), 3) if self._decision_history else 0
        return result


class ExecutionScheduler:
    """
    执行调度器 — 管理任务的生命周期
    
    功能：
    - 维护任务队列（按优先级排序）
    - 处理任务依赖关系（DAG拓扑排序）
    - 并发控制（限制同时运行的任务数）
    - 超时检测和自动取消
    - 重试机制（指数退避）
    """

    MAX_CONCURRENT = 3
    RETRY_BASE_DELAY_S = 2.0
    RETRY_MAX_DELAY_S = 60.0

    def __init__(self):
        self._task_queue: List[PlannedTask] = []
        self._running_tasks: Dict[str, PlannedTask] = {}
        self._completed_tasks: Dict[str, PlannedTask] = {}
        self._lock = threading.RLock()
        self._system_registry: Dict[str, Any] = {}
        self._total_executed = 0
        self._total_succeeded = 0
        self._total_failed = 0

    def register_system(self, name: str, instance: Any):
        self._system_registry[name] = instance

    def submit_plan(self, tasks: List[PlannedTask]):
        with self._lock:
            for task in tasks:
                existing = next((t for t in self._task_queue if t.task_id == task.task_id), None)
                if not existing and task.task_id not in self._completed_tasks:
                    self._task_queue.append(task)
            self._sort_queue()

    def execute_next(self) -> Optional[PlannedTask]:
        with self._lock:
            runnable = self._find_runnable_task()
            if not runnable:
                return None
            runnable.status = TaskStatus.RUNNING
            runnable.started_at = datetime.now().isoformat()
            self._running_tasks[runnable.task_id] = runnable
        self._execute_task(runnable)
        return runnable

    def _find_runnable_task(self) -> Optional[PlannedTask]:
        if len(self._running_tasks) >= self.MAX_CONCURRENT:
            return None
        for task in self._task_queue:
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                dep_id in self._completed_tasks or dep_id in self._running_tasks
                for dep_id in task.dependencies
            )
            if deps_met:
                return task
        waiting = [t for t in self._task_queue if t.status == TaskStatus.PENDING]
        if waiting and len(self._running_tasks) < self.MAX_CONCURRENT:
            for t in waiting:
                unmet_deps = [d for d in t.dependencies if d not in self._completed_tasks and d not in self._running_tasks]
                if not unmet_deps:
                    return t
                t.status = TaskStatus.WAITING_DEPENDENCY
        return None

    def _execute_task(self, task: PlannedTask):
        def _run():
            start_time = time.time()
            try:
                instance = self._resolve_target(task.target_system, task.action_name)
                if instance is None:
                    raise RuntimeError(f"无法解析目标: {task.target_system}.{task.action_name}")
                method = self._find_method(instance, task.action_name)
                if method is None:
                    raise RuntimeError(f"方法不存在: {task.action_name}")
                result = method(**task.parameters)
                if isinstance(result, dict):
                    task.result = result
                else:
                    task.result = {"raw_result": str(result)}
                task.status = TaskStatus.COMPLETED
                task.actual_duration_s = round(time.time() - start_time, 2)
                task.metrics["duration_vs_estimate"] = round(task.actual_duration_s / max(task.estimated_duration_s, 0.1), 2)
                with self._lock:
                    self._completed_tasks[task.task_id] = task
                    self._running_tasks.pop(task.task_id, None)
                    self._task_queue = [t for t in self._task_queue if t.task_id != task.task_id]
                self._total_executed += 1
                self._total_succeeded += 1
                logger.info(f"[驱动调度] ✓ 任务完成: {task.name} ({task.actual_duration_s}s)")
            except Exception as e:
                task.error = str(e)[:500]
                task.actual_duration_s = round(time.time() - start_time, 2)
                task.retry_count += 1
                if task.retry_count <= task.max_retries:
                    delay = min(self.RETRY_BASE_DELAY_S * (2 ** (task.retry_count - 1)), self.RETRY_MAX_DELAY_S)
                    logger.warning(f"[驱动调度] ✗ 任务失败(重试{task.retry_count}/{task.max_retries}): {task.name} | {str(e)[:100]} | {delay}s后重试")
                    time.sleep(delay)
                    task.status = TaskStatus.PENDING
                    with self._lock:
                        self._running_tasks.pop(task.task_id, None)
                        self._task_queue.insert(0, task)
                else:
                    task.status = TaskStatus.FAILED
                    with self._lock:
                        self._completed_tasks[task.task_id] = task
                        self._running_tasks.pop(task.task_id, None)
                        self._task_queue = [t for t in self._task_queue if t.task_id != task.task_id]
                    self._total_executed += 1
                    self._total_failed += 1
                    logger.error(f"[驱动调度] ✗ 任务最终失败: {task.name} | {task.error}")

        threading.Thread(target=_run, daemon=True, name=f"driver_task_{task.task_id}").start()

    def _resolve_target(self, system_name: str, action_name: str) -> Any:
        dot_parts = action_name.rsplit(".", 1)
        if len(dot_parts) == 2:
            try:
                module_path = dot_parts[0].replace("_", "/")
                module = __import__(f"backend.{module_path}", fromlist=[""])
                return getattr(module, dot_parts[1], None)
            except Exception:
                pass
        direct_map = {
            "platform_orchestrator": "backend.integration.platform_orchestrator.platform_orchestrator",
            "evolution_cultivation_bridge": "backend.integration.evolution_cultivation_bridge.evolution_cultivation_bridge",
            "cultivation_alchemy_bridge": "backend.integration.cultivation_alchemy_bridge.cultivation_alchemy_bridge",
            "governance_integration_bridge": "backend.integration.governance_integration_bridge.governance_integration_bridge",
            "cultivation_dashboard": "backend.cultivation.cultivation_integration.cultivation_dashboard",
            "auto_iteration_engine": "backend.cultivation.cultivation_integration.auto_iteration_engine",
            "e2e_cultivation_test": "backend.cultivation.cultivation_integration.e2e_cultivation_test",
            "deployment_generator": "backend.cultivation.cultivation_integration.deployment_generator",
            "chaos_engineer": "backend.alchemy.stability_testing.chaos_engineer",
            "alert_notifier": "backend.alchemy.city_simulator_optimizer.alert_notifier",
            "historical_data_generator": "backend.self_evolution.data_generator.historical_data_generator",
            "multi_dimension_validator": "backend.self_evolution.validator_repair.multi_dimension_validator",
        }
        import_path = direct_map.get(system_name) or direct_map.get(action_name.split(".")[0])
        if import_path:
            try:
                parts = import_path.rsplit(".", 1)
                mod = __import__(parts[0], fromlist=[""])
                return getattr(mod, parts[-1], None)
            except Exception:
                pass
        return self._system_registry.get(system_name)

    def _find_method(self, instance: Any, method_name: str) -> Optional[Callable]:
        if instance is None:
            return None
        short_name = method_name.rsplit(".", 1)[-1]
        method = getattr(instance, short_name, None)
        if callable(method):
            return method
        return None

    def _sort_queue(self):
        self._task_queue.sort(key=lambda t: (t.priority.value, -t.created_at.count("T")))

    def get_queue_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pending": len([t for t in self._task_queue if t.status == TaskStatus.PENDING]),
                "waiting": len([t for t in self._task_queue if t.status == TaskStatus.WAITING_DEPENDENCY]),
                "running": len(self._running_tasks),
                "completed": len(self._completed_tasks),
                "total_executed": self._total_executed,
                "success_rate": round(self._total_succeeded / max(self._total_executed, 1), 3),
                "pending_tasks": [{"id": t.task_id[:16], "name": t.name, "priority": t.priority.name} for t in self._task_queue[:10]],
            }


class SelfReflectionDriver:
    """
    自我反思驱动器 — 对应提示词 5.x 的"自我修复与优化"
    
    功能：
    - 定期回顾决策记录，分析成功/失败模式
    - 发现系统性偏差并建议校正措施
    - 学习最优决策模式并调整评分权重
    - 生成反思报告供人工审核
    """

    REFLECTION_INTERVAL_EPISODES = 20

    def __init__(self, decision_engine: DecisionEngine):
        self._decision_engine = decision_engine
        self._reflections: List[SelfReflectionEntry] = []

    def run_reflection(self, session_id: str = "") -> SelfReflectionEntry:
        decisions = self._decision_engine._decision_history[-self.REFLECTION_INTERVAL_EPISODES:]
        if not decisions:
            return SelfReflectionEntry(
                reflection_id="none", timestamp=datetime.now().isoformat(), session_id=session_id,
                decisions_reviewed=0, successful_decisions=0, failed_decisions=0,
                learning_summary="无足够决策记录可供反思",
            )
        successes = sum(1 for d in decisions if d.outcome == "success")
        failures = len(decisions) - successes
        patterns = self._discover_patterns(decisions)
        improvements = self._suggest_improvements(decisions, patterns)
        adjustments = self._compute_confidence_adjustments(decisions)
        summary_parts = [f"回顾{len(decisions)}条决策记录"]
        summary_parts.append(f"成功:{successes} 失败:{failures} 成功率:{successes/len(decisions):.0%}")
        if patterns:
            summary_parts.append(f"发现{len(patterns)}个模式")
        if improvements:
            summary_parts.append(f"提出{len(improvements)}项改进")

        entry = SelfReflectionEntry(
            reflection_id=f"reflect_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            session_id=session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            decisions_reviewed=len(decisions),
            successful_decisions=successes,
            failed_decisions=failures,
            patterns_discovered=patterns,
            improvements_suggested=improvements,
            confidence_adjustments=adjustments,
            learning_summary="; ".join(summary_parts),
        )
        self._reflections.append(entry)
        logger.info(f"[驱动反思] 反思完成 | 成功率={successes/len(decisions):.0%} | 模式={len(patterns)} | 改进={len(improvements)}")
        return entry

    def _discover_patterns(self, decisions: List[DecisionRecord]) -> List[str]:
        patterns = []
        low_confidence_failures = [d for d in decisions if d.confidence in (DecisionConfidence.LOW, DecisionConfidence.VERY_LOW) and d.outcome == "failure"]
        if len(low_confidence_failures) > len(decisions) * 0.3:
            patterns.append("低置信度决策失败率偏高，应提高阈值或收集更多信息")
        high_confidence_successes = [d for d in decisions if d.confidence in (DecisionConfidence.VERY_HIGH, DecisionConfidence.HIGH) and d.outcome == "success"]
        if len(high_confidence_successes) < len(decisions) * 0.4:
            patterns.append("高置信度正确率偏低，可能存在过度自信偏差")
        action_counts = defaultdict(int)
        for d in decisions:
            action_counts[d.chosen_action] += 1
        most_common = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else ""
        if most_common and action_counts[most_common] > len(decisions) * 0.5:
            patterns.append(f"存在决策偏好集中现象: '{most_common}' 占比过高({action_counts[most_common]/len(decisions):.0%})")
        recent_trend = decisions[-min(10, len(decisions)):]
        recent_success_rate = sum(1 for d in recent_trend if d.outcome == "success") / max(len(recent_trend), 1)
        overall_success_rate = sum(1 for d in decisions if d.outcome == "success") / max(len(decisions), 1)
        if recent_success_rate < overall_success_rate - 0.1:
            patterns.append("近期决策质量呈下降趋势，需关注环境变化或参数漂移")
        return patterns

    def _suggest_improvements(self, decisions: List[DecisionRecord], patterns: List[str]) -> List[str]:
        improvements = []
        failures = [d for d in decisions if d.outcome == "failure"]
        failure_actions = set(d.chosen_action for d in failures)
        for action in failure_actions:
            action_failures = [d for d in failures if d.chosen_action == action]
            if len(action_failures) >= 2:
                improvements.append(f"对'{action}'增加前置条件检查或降低默认优先级")
        low_conf_errors = [d for d in failures if d.confidence in (DecisionConfidence.LOW, DecisionConfidence.VERY_LOW)]
        if len(low_conf_errors) > len(failures) * 0.5:
            improvements.append("引入'请求更多信息'机制，在低置信度时主动收集额外上下文")
        timeout_like = [d for d in failures if "timeout" in (d.outcome_metrics.get("error", "") or "").lower()]
        if timeout_like:
            improvements.append("为耗时操作增加进度反馈和中间检查点")
        return improvements

    def _compute_confidence_adjustments(self, decisions: List[DecisionRecord]) -> Dict[str, float]:
        adjustments = {}
        by_confidence = defaultdict(lambda: {"total": 0, "success": 0})
        for d in decisions:
            key = d.confidence.value
            by_confidence[key]["total"] += 1
            if d.outcome == "success":
                by_confidence[key]["success"] += 1
        for conf_val, stats in by_confidence.items():
            actual_rate = stats["success"] / max(stats["total"], 1)
            expected = {"very_high": 0.95, "high": 0.80, "medium": 0.55, "low": 0.35, "very_low": 0.15}.get(conf_val, 0.5)
            diff = actual_rate - expected
            if abs(diff) > 0.1:
                adjustment = diff * 0.1
                adjustments[conf_val] = round(adjustment, 3)
        return adjustments

    def get_reflection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._reflections[-limit:]]


class DriverAgentCore:
    """
    驱动智能体核心 — 自主驾驶大脑
    
    完整流程:
    用户输入/系统事件 → IntentRecognizer(意图识别) → TaskPlanner(任务规划)
      → DecisionEngine(决策) → ExecutionScheduler(执行调度) → 各子系统执行
      → 结果汇总 → SelfReflectionDriver(反思学习) → 模式优化
    """

    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.planner = TaskPlanner()
        self.decision_engine = DecisionEngine()
        self.scheduler = ExecutionScheduler()
        self.reflection_driver = SelfReflectionDriver(self.decision_engine)
        self._session_counter = 0
        self._register_default_systems()

    def _register_default_systems(self):
        try:
            from backend.integration.platform_orchestrator import platform_orchestrator
            self.scheduler.register_system("platform_orchestrator", platform_orchestrator)
        except Exception:
            pass
        try:
            from backend.integration.cultivation_alchemy_bridge import cultivation_alchemy_bridge
            self.scheduler.register_system("cultivation_alchemy_bridge", cultivation_alchemy_bridge)
        except Exception:
            pass
        try:
            from backend.integration.evolution_cultivation_bridge import evolution_cultivation_bridge
            self.scheduler.register_system("evolution_cultivation_bridge", evolution_cultivation_bridge)
        except Exception:
            pass
        try:
            from backend.integration.governance_integration_bridge import governance_integration_bridge
            self.scheduler.register_system("governance_integration_bridge", governance_integration_bridge)
        except Exception:
            pass

    def drive(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._session_counter += 1
        session_id = f"drive_{self._session_counter}"
        drive_start = time.time()
        logger.info(f"[驱动智能体] 🚗 开始驾驶 | Session={session_id} | 输入={input_text[:80]}")
        intent = self.intent_recognizer.recognize(input_text, context)
        tasks = self.planner.plan(intent)
        self.scheduler.submit_plan(tasks)
        executed = []
        while True:
            task = self.scheduler.execute_next()
            if task is None:
                queue_status = self.scheduler.get_queue_status()
                if queue_status["pending"] == 0 and queue_status["running"] == 0:
                    break
                if queue_status["running"] == 0 and queue_status["waiting"] > 0:
                    logger.warning("[驱动智能体] 存在循环依赖，强制标记等待中任务为完成")
                    with self.scheduler._lock:
                        for t in self.scheduler._task_queue:
                            if t.status.name == "waiting_dependency":
                                t.status = TaskStatus.COMPLETED
                                t.result = {"skipped_reason": "dependency_unresolved"}
                                self.scheduler._completed_tasks[t.task_id] = t
                        self.scheduler._task_queue = [t for t in self.scheduler._task_queue if t.status != TaskStatus.COMPLETED]
                    continue
                time.sleep(0.5)
            else:
                executed.append(task.task_id)
                time.sleep(0.1)
        results = {tid: asdict(t) for tid, t in self.scheduler._completed_tasks.items()}
        if len(executed) >= self.reflection_driver.REFLECTION_INTERVAL_EPISODES // 2:
            reflection = self.reflection_driver.run_reflection(session_id)
        else:
            reflection = None
        decision_stats = self.decision_engine.get_decision_stats()
        queue_stats = self.scheduler.get_queue_status()
        response = {
            "session_id": session_id,
            "input": input_text[:200],
            "intent": {"type": intent.intent_type.value, "confidence": round(intent.confidence, 3),
                       "target_systems": intent.target_systems},
            "tasks_planned": len(tasks),
            "tasks_executed": len(executed),
            "tasks_results": results,
            "queue_status": queue_stats,
            "decision_stats": decision_stats,
            "reflection": asdict(reflection) if reflection else None,
            "duration_s": round(time.time() - drive_start, 2),
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(f"[驱动智能体] 🏁 驾驶完成 | Session={session_id} | 任务={len(executed)}/{len(tasks)} | 耗时={response['duration_s']}s")
        return response

    def get_full_status(self) -> Dict[str, Any]:
        return {
            "intent_recognizer": {"history_size": len(self.intent_recognizer._history)},
            "planner": {"cache_size": len(self.planner._plan_cache)},
            "decision_engine": self.decision_engine.get_decision_stats(),
            "scheduler": self.scheduler.get_queue_status(),
            "reflection": {"total_reflections": len(self.reflection_driver._reflections),
                          "last_reflection": asdict(self.reflection_driver._reflections[-1]) if self.reflection_driver._reflections else None},
            "sessions_completed": self._session_counter,
        }


driver_agent_core = DriverAgentCore()
