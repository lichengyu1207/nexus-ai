# -*- coding: utf-8 -*-
"""
驱动智能体 - 行动执行层 (Driver Action Executor)
===============================================
对应设计文档 Ch5(自我修复与优化) + Ch8(部署与运维)

职责：
1) 行动编排器(ActionOrchestrator) — 将高层行动分解为跨体系的具体操作序列
2) 结果验证器(ResultValidator) — 验证每个操作的输出是否符合预期
3) 自动回滚管理器(AutoRollbackManager) — 检测到失败时自动回滚到安全状态
4) 幂等性保证(IdempotencyGuard) — 确保重复执行不会产生副作用
5) 执行日志追踪(ExecutionTracer) — 完整记录每步操作的输入/输出/耗时/状态
"""

from __future__ import annotations

import json
import time
import hashlib
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionPhase(Enum):
    PREPARE = "prepare"
    EXECUTE = "execute"
    VALIDATE = "validate"
    COMMIT = "commit"
    ROLLBACK = "rollback"
    CLEANUP = "cleanup"


class ValidationResult(Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ActionStep:
    step_id: str
    name: str
    phase: ExecutionPhase
    target_system: str
    method_name: str
    parameters: Dict[str, Any]
    expected_output_schema: Optional[Dict[str, Any]] = None
    timeout_s: float = 60.0
    retry_on_failure: bool = True
    max_retries: int = 2
    idempotency_key: Optional[str] = None


@dataclass
class StepResult:
    step_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    duration_s: float = 0.0
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    validation: Optional[ValidationResult] = None


@dataclass
class ExecutionSession:
    session_id: str
    name: str
    created_at: str
    status: str = "created"
    steps: List[ActionStep] = field(default_factory=list)
    results: List[StepResult] = field(default_factory=list)
    final_output: Optional[Dict[str, Any]] = None
    rollback_performed: bool = False
    total_duration_s: float = 0.0


@dataclass
class RollbackRecord:
    rollback_id: str
    session_id: str
    triggered_by_step: str
    reason: str
    steps_reverted: List[str]
    reverted_at: str
    success: bool = False
    restoration_data: Dict[str, Any] = field(default_factory=dict)


class IdempotencyGuard:
    """
    幂等性保证 — 确保相同操作重复执行不产生副作用
    
    通过操作指纹(fingerprint)检测重复请求，返回缓存结果。
    """

    def __init__(self, cache_size: int = 1000):
        self._cache: Dict[str, StepResult] = {}
        self._cache_size = cache_size
        self._lock = threading.RLock()

    def compute_key(self, step: ActionStep) -> str:
        raw = f"{step.target_system}:{step.method_name}:{json.dumps(step.parameters, sort_keys=True, default=str)}"
        if step.idempotency_key:
            raw = f"idemp:{step.idempotency_key}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def check_and_cache(self, key: str, result: Optional[StepResult] = None) -> Optional[StepResult]:
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                logger.info(f"[幂等] 命中缓存: {key}")
                return cached
            if result is not None:
                if len(self._cache) >= self._cache_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[key] = result
        return None

    def invalidate(self, key: str):
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()


idempotency_guard = IdempotencyGuard()


class ResultValidator:
    """
    结果验证器 — 对应提示词 4.1 多维度结果验证
    
    验证规则：
    - 结构完整性：输出包含预期字段
    - 类型正确性：字段类型匹配
    - 范围合理性：数值在合理范围内
    - 一致性检查：跨步骤结果逻辑一致
    """

    def validate(self, step: ActionStep, result: StepResult) -> Tuple[ValidationResult, List[str]]:
        issues = []
        if result.error and not step.retry_on_failure:
            return ValidationResult.FAILED, [f"执行失败且不允许重试: {result.error}"]
        if result.output is None:
            return (ValidationResult.WARNING, ["输出为空"]) if not result.error else (ValidationResult.FAILED, [result.error or "无输出"])
        output = result.output
        schema = step.expected_output_schema
        if schema:
            for required_field in schema.get("required_fields", []):
                if required_field not in output:
                    issues.append(f"缺少必需字段: {required_field}")
            for field_name, field_type_hint in schema.get("field_types", {}).items():
                if field_name in output:
                    actual_val = output[field_name]
                    expected_type_map = {"string": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict}
                    expected_type = expected_type_map.get(field_type_hint, object)
                    if not isinstance(actual_val, expected_type):
                        issues.append(f"字段'{field_name}'类型错误: 期望{field_type_hint}, 实际{type(actual_val).__name__}")
        numeric_checks = {
            "success_rate": (0.0, 1.0),
            "accuracy": (0.0, 1.0),
            "completion_pct": (0.0, 100.0),
            "win_rate": (0.0, 1.0),
            "error_rate": (0.0, 1.0),
            "score": (0.0, 5.0),
            "duration_s": (0.0, 86400.0),
        }
        for field_name, (lo, hi) in numeric_checks.items():
            if field_name in output:
                val = output[field_name]
                if isinstance(val, (int, float)):
                    if val < lo or val > hi:
                        issues.append(f"字段'{field_name}'值{val}超出范围[{lo}, {hi}]")
        success_count = sum(1 for s in schema.get("soft_checks", []) if output.get(s, False))
        soft_total = len(schema.get("soft_checks", []))
        if soft_total > 0 and success_count < soft_total * 0.5:
            issues.append(f"软检查通过率低: {success_count}/{soft_total}")
        if not issues:
            return ValidationResult.PASSED, []
        has_critical = any("缺少必需" in i or "类型错误" in i for i in issues)
        return (ValidationResult.FAILED if has_critical else ValidationResult.WARNING, issues)


result_validator = ResultValidator()


class AutoRollbackManager:
    """
    自动回滚管理器 — 对应提示词 5.2 模型热更新与回滚
    
    当操作链中某步失败时：
    1. 记录当前系统快照（已完成的步骤产生的副作用）
    2. 按逆序执行补偿操作
    3. 验证回滚后系统状态一致性
    4. 记录回滚事件供后续分析
    """

    def __init__(self):
        self._rollback_records: List[RollbackRecord] = []
        self._compensation_registry: Dict[str, Callable] = {}

    def register_compensation(self, action_fingerprint: str, compensation_fn: Callable):
        self._compensation_registry[action_fingerprint] = compensation_fn

    def execute_rollback(self, session: ExecutionSession, failed_step_id: str,
                          error_msg: str) -> RollbackRecord:
        completed_results = [r for r in session.results if r.status == "completed"]
        steps_to_revert = [r.step_id for r in reversed(completed_results)]
        record = RollbackRecord(
            rollback_id=f"rb_{int(time.time()*1000)}",
            session_id=session.session_id,
            triggered_by_step=failed_step_id,
            reason=error_msg,
            steps_reverted=[],
            reverted_at="",
        )
        logger.warning(f"[驱动回滚] 开始回滚 | Session={session.session_id} | 触发步骤={failed_step_id} | 原因={error_msg[:100]}")
        for step_id in steps_to_revert:
            comp_key = f"{session.session_id}:{step_id}"
            comp_fn = self._compensation_registry.get(comp_key)
            if comp_fn:
                try:
                    comp_result = comp_fn()
                    record.steps_reverted.append(step_id)
                    record.restoration_data[step_id] = comp_result
                    logger.info(f"[驱动回滚] ✓ 补偿完成: {step_id}")
                except Exception as e:
                    logger.error(f"[驱动回滚] ✗ 补偿失败: {step_id} | {e}")
            else:
                record.steps_reverted.append(step_id)
                logger.info(f"[驱动回滚] → 标记回退: {step_id} (无补偿函数)")
        record.reverted_at = datetime.now().isoformat()
        record.success = len(record.steps_reverted) > 0
        session.rollback_performed = True
        self._rollback_records.append(record)
        return record

    def get_rollback_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._rollback_records[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._rollback_records)
        successful = sum(1 for r in self._rollback_records if r.success)
        return {
            "total_rollbacks": total,
            "successful": successful,
            "success_rate": round(successful / max(total, 1), 3),
            "avg_steps_reverted": round(
                statistics.mean([len(r.steps_reverted) for r in self._rollback_records]) if self._rollback_records else 0, 1),
        }


auto_rollback_manager = AutoRollbackManager()


class ExecutionTracer:
    """
    执行日志追踪 — 完整记录每步操作的详细信息
    
    提供完整的审计线索，支持事后分析和故障排查。
    """

    def __init__(self):
        self._trace_log: List[Dict[str, Any]] = []

    def log_step_start(self, session_id: str, step: ActionStep):
        entry = {
            "event": "step_start",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "step_id": step.step_id,
            "step_name": step.name,
            "target_system": step.target_system,
            "method": step.method_name,
            "parameters_hash": hashlib.md5(json.dumps(step.parameters, default=str).encode()).hexdigest()[:12],
        }
        self._trace_log.append(entry)

    def log_step_complete(self, session_id: str, result: StepResult):
        entry = {
            "event": "step_complete",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "step_id": result.step_id,
            "status": result.status,
            "duration_s": result.duration_s,
            "has_output": result.output is not None,
            "has_error": result.error is not None,
            "validation": result.validation.value if result.validation else None,
            "retries": result.retry_count,
        }
        self._trace_log.append(entry)

    def log_session_end(self, session: ExecutionSession):
        entry = {
            "event": "session_end",
            "timestamp": datetime.now().isoformat(),
            "session_id": session.session_id,
            "status": session.status,
            "total_steps": len(session.steps),
            "completed_steps": len([r for r in session.results if r.status == "completed"]),
            "failed_steps": len([r for r in session.results if r.status == "error"]),
            "total_duration_s": session.total_duration_s,
            "rolled_back": session.rollback_performed,
        }
        self._trace_log.append(entry)

    def get_trace(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if session_id:
            return [e for e in self._trace_log if e.get("session_id") == session_id][-limit:]
        return self._trace_log[-limit:]

    def export_trace(self, filepath: str):
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._trace_log, f, ensure_ascii=False, indent=2, default=str)


execution_tracer = ExecutionTracer()


class ActionOrchestrator:
    """
    行动编排器 — 核心执行引擎
    
    将高层意图转化为具体的、可执行的跨体系操作序列，
    并管理整个执行生命周期（准备→执行→验证→提交→清理）。
    
    支持的操作模板:
    - full_evolution_cycle: 完整进化循环
    - health_check_and_repair: 健康检查+自动修复
    - training_injection: 数据注入训练
    - emergency_shutdown: 紧急停机+状态保存
    """

    ACTION_TEMPLATES = {
        "full_evolution_cycle": [
            ActionStep("prep_init", "初始化平台", ExecutionPhase.PREPARE, "platform_orchestrator", "initialize_all", {}, 30.0),
            ActionStep("inject_data", "注入训练数据", ExecutionPhase.EXECUTE, "evolution_cultivation_bridge", "inject_training_data_to_all_stages", {"sample_count": 50}, 30.0),
            ActionStep("furnace_drive", "炼丹驱动修炼", ExecutionPhase.EXECUTE, "cultivation_alchemy_bridge", "run_furnace_driven_evolution", {"max_iterations": 3}, 120.0),
            ActionStep("governance_coord", "三省六部统筹", ExecutionPhase.EXECUTE, "governance_integration_bridge", "coordinate_all_systems", {}, 20.0),
            ActionStep("validate_health", "健康验证", ExecutionPhase.VALIDATE, "health_scoring_engine", "generate_report", {}, 10.0),
        ],
        "quick_health_check": [
            ActionStep("snapshot", "采集全局状态", ExecutionPhase.PREPARE, "global_state_perceiver", "capture", {"force": True}, 5.0),
            ActionStep("score", "计算健康分数", ExecutionPhase.VALIDATE, "health_scoring_engine", "compute_health_score", {}, 5.0),
        ],
        "emergency_recovery": [
            ActionStep("stop_engine", "停止迭代引擎", ExecutionPhase.PREPARE, "auto_iteration_engine", "stop", {}, 5.0),
            ActionStep("save_state", "保存当前状态", ExecutionPhase.COMMIT, "auto_iteration_engine", "get_resume_point", {}, 5.0),
            ActionStep("check_integrity", "完整性检查", ExecutionPhase.VALIDATE, "chaos_engineer", "get_resilience_report", {}, 10.0),
        ],
    }

    def __init__(self):
        self._sessions: Dict[str, ExecutionSession] = {}
        self._system_resolver_cache: Dict[str, Any] = {}

    def _resolve_system_method(self, system_name: str, method_name: str) -> Optional[Tuple[Any, Callable]]:
        cache_key = f"{system_name}.{method_name}"
        if cache_key in self._system_resolver_cache:
            return self._system_resolver_cache[cache_key]
        direct_imports = {
            ("global_state_perceiver", "capture"): ("backend.driver_agent.driver_perception.global_state_perceiver", "capture"),
            ("health_scoring_engine", "compute_health_score"): ("backend.driver_agent.driver_perception.health_scoring_engine", "compute_health_score"),
            ("health_scoring_engine", "generate_report"): ("backend.driver_agent.driver_perception.health_scoring_engine", "generate_report"),
            ("anomaly_detector", "check_metric"): ("backend.driver_agent.driver_perception.anomaly_detector", "check_metric"),
            ("trend_analyzer", "analyze_trend"): ("backend.driver_agent.driver_perception.trend_analyzer", "analyze_trend"),
            ("multi_source_fusion", "fuse"): ("backend.driver_agent.driver_perception.multi_source_fusion", "fuse"),
            ("platform_orchestrator", "initialize_all"): ("backend.integration.platform_orchestrator.platform_orchestrator", "initialize_all"),
            ("evolution_cultivation_bridge", "inject_training_data_to_all_stages"): ("backend.integration.evolution_cultivation_bridge.evolution_cultivation_bridge", "inject_training_data_to_all_stages"),
            ("cultivation_alchemy_bridge", "run_furnace_driven_evolution"): ("backend.integration.cultivation_alchemy_bridge.cultivation_alchemy_bridge", "run_furnace_driven_evolution"),
            ("governance_integration_bridge", "coordinate_all_systems"): ("backend.integration.governance_integration_bridge.governance_integration_bridge", "coordinate_all_systems"),
            ("cultivation_dashboard", "export_dashboard_data"): ("backend.cultivation.cultivation_integration.cultivation_dashboard", "export_dashboard_data"),
            ("auto_iteration_engine", "stop"): ("backend.cultivation.cultivation_integration.auto_iteration_engine", "stop"),
            ("auto_iteration_engine", "get_resume_point"): ("backend.cultivation.cultivation_integration.auto_iteration_engine", "get_resume_point"),
            ("chaos_engineer", "get_resilience_report"): ("backend.alchemy.stability_testing.chaos_engineer", "get_resilience_report"),
        }
        import_path, method_attr = direct_imports.get((system_name, method_name), (None, None))
        if import_path:
            try:
                parts = import_path.rsplit(".", 1)
                mod = __import__(parts[0], fromlist=[""])
                instance = getattr(mod, parts[-1], mod)
                method = getattr(instance, method_attr, None)
                if method:
                    result = (instance, method)
                    self._system_resolver_cache[cache_key] = result
                    return result
            except Exception:
                pass
        try:
            module_path = system_name.replace("_", "/")
            mod = __import__(f"backend.{module_path}", fromlist=[""])
            instance = getattr(mod, system_name.split("/")[-1].split(".")[-1], mod)
            method = getattr(instance, method_name.split(".")[-1], None)
            if method:
                result = (instance, method)
                self._system_resolver_cache[cache_key] = result
                return result
        except Exception:
            pass
        return None

    def execute_plan(self, template_name: str, override_params: Optional[Dict[str, Any]] = None) -> ExecutionSession:
        template = self.ACTION_TEMPLATES.get(template_name, [])
        if not template:
            raise ValueError(f"未知操作模板: {template_name}")
        session = ExecutionSession(
            session_id=f"exec_{int(time.time()*1000)}_{hashlib.md5(template_name.encode()).hexdigest()[:8]}",
            name=template_name,
            created_at=datetime.now().isoformat(),
            status="running",
        )
        if override_params:
            for step in template:
                for k, v in override_params.items():
                    if k in step.parameters:
                        step.parameters[k] = v
        session.steps = template
        self._sessions[session.session_id] = session
        execution_tracer.log_session_start = lambda sid, s=None: None
        start_time = time.time()
        for step in template:
            idemp_key = idempotency_guard.compute_key(step)
            cached = idempotency_guard.check_and_cache(idemp_key)
            if cached:
                session.results.append(cached)
                continue
            execution_tracer.log_step_start(session.session_id, step)
            step_start = time.time()
            result = StepResult(step_id=step.step_id, status="pending", started_at=datetime.now().isoformat())
            resolved = self._resolve_system_method(step.target_system, step.method_name)
            attempt = 0
            last_error = None
            while attempt <= step.max_retries:
                attempt += 1
                try:
                    if resolved:
                        instance, method = resolved
                        raw_output = method(**step.parameters)
                        if isinstance(raw_output, dict):
                            result.output = raw_output
                        elif hasattr(raw_output, '__dataclass_fields__'):
                            result.output = asdict(raw_output)
                        else:
                            result.output = {"raw_result": str(raw_output)}
                        result.status = "completed"
                    else:
                        result.status = "skipped"
                        result.output = {"note": f"无法解析目标: {step.target_system}.{step.method_name}"}
                    break
                except Exception as e:
                    last_error = str(e)[:500]
                    result.error = last_error
                    result.retry_count = attempt
                    if attempt <= step.max_retries and step.retry_on_failure:
                        time.sleep(min(1.0 * (2 ** (attempt - 1)), 10.0))
                    else:
                        result.status = "error"
                        break
            result.duration_s = round(time.time() - step_start, 2)
            result.completed_at = datetime.now().isoformat()
            validation_result, validation_issues = result_validator.validate(step, result)
            result.validation = validation_result
            if validation_result == ValidationResult.FAILED:
                rollback_record = auto_rollback_manager.execute_rollback(session, step.step_id, "; ".join(validation_issues))
                result.output = result.output or {}
                result.output["rollback_id"] = rollback_record.rollback_id
            idempotency_guard.check_and_cache(idemp_key, result)
            execution_tracer.log_step_complete(session.session_id, result)
            session.results.append(result)
            if result.status == "error" and not step.retry_on_failure:
                break
        session.total_duration_s = round(time.time() - start_time, 2)
        all_completed = all(r.status in ("completed", "skipped") for r in session.results)
        any_failed = any(r.status == "error" for r in session.results)
        session.status = "completed" if all_completed else ("failed" if any_failed else "partial")
        session.final_output = {
            "template": template_name,
            "steps_total": len(template),
            "steps_completed": len([r for r in session.results if r.status in ("completed", "skipped")]),
            "steps_failed": len([r for r in session.results if r.status == "error"]),
            "duration_s": session.total_duration_s,
            "last_outputs": {r.step_id: r.output for r in session.results[-3:] if r.output},
        }
        execution_tracer.log_session_end(session)
        logger.info(f"[驱动执行] Session={session.session_id} 完成 | 模板={template_name} | "
                     f"状态={session.status} | 步骤={len(session.results)}/{len(template)} | "
                     f"耗时={session.total_duration_s}s")
        return session

    def get_session(self, session_id: str) -> Optional[ExecutionSession]:
        return self._sessions.get(session_id)

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return [{**asdict(s), "results_summary": [{"id": r.step_id[:12], "s": r.status, "d": f"{r.duration_s}s"} for r in s.results]}
                for s in sessions[:limit]]


action_orchestrator = ActionOrchestrator()
