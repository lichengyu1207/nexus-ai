"""
智能体自进化炼丹系统 - 第一部分：炼丹炉核心架构
房都督平台 Phase D: 自进化炼丹系统 Chapter 1

第一章：总体架构与设计哲学
1.1 AlchemyFurnace - 炼丹炉定义与成功标准
1.2 LayeredArchitecture - 五层分层架构
1.3 ModelVersionManager - 数据与模型版本管理（MLflow风格）
"""
import json
import logging
import time
import math
import random
import uuid
import re
import copy
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple, Set
from collections import deque, defaultdict
import threading


logger = logging.getLogger(__name__)


# ==================== 1.1 炼丹炉的定义 ====================


class FurnacePhase(Enum):
    """炼丹阶段"""
    INITIALIZATION = "initialization"
    DATA_GENERATION = "data_generation"
    SELF_PLAY_TRAINING = "self_play_training"
    VALIDATION = "validation"
    SELF_REPAIR = "self_repair"
    EVOLUTION = "evolution"
    STABILITY_TEST = "stability_test"
    FINAL_VERIFICATION = "final_verification"
    COMPLETED = "completed"
    FAILED = "failed"


class SuccessCriteria(Enum):
    """成功判定标准项"""
    ACCURACY_RATE = "accuracy_rate"
    ERROR_RATE = "error_rate"
    AVG_RESPONSE_TIME = "avg_response_time"
    UPTIME_7D = "uptime_7d"
    NO_MANUAL_INTERVENTION = "no_manual_intervention"
    CONVERGENCE_STABLE = "convergence_stable"


@dataclass
class SuccessThreshold:
    """成功阈值配置"""
    criteria: SuccessCriteria
    target_value: float
    operator: str
    weight: float
    description: str
    current_value: float = 0.0
    achieved: bool = False


@dataclass
class AlchemySession:
    """一次完整的炼丹会话"""
    session_id: str
    start_time: float
    phase: FurnacePhase
    success_criteria: List[SuccessThreshold]
    iteration_count: int = 0
    best_metrics: Dict[str, float] = field(default_factory=dict)
    convergence_history: List[Dict[str, float]] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    end_time: Optional[float] = None
    final_status: Optional[str] = None


@dataclass
class IterationResult:
    """单次迭代结果"""
    iteration_id: int
    timestamp: float
    phase: FurnacePhase
    metrics: Dict[str, float]
    improvements: Dict[str, float]
    actions_taken: List[str]
    duration_seconds: float
    converged: bool = False


class AlchemyFurnace:
    """
    炼丹炉核心（提示词 1.1）
    
    核心目标：构建全自动的智能体自进化引擎，实现"一次上线，100%稳定"
    
    成功标准：
    - 连续7天自动化测试中，核心任务准确率≥95%
    - 错误率<0.5%
    - 平均响应时间<1秒
    - 无任何人工干预即可保持稳定
    
    终点条件：
    - 连续3次迭代均未带来显著提升(<1%)
    - 且所有指标达标 → 宣布炼丹成功，智能体"出炉"
    
    输入：初始智能体代码、配置文件、历史数据
    输出：优化后的智能体模型、性能报告、进化日志
    """

    def __init__(self,
                 max_iterations: int = 1000,
                 convergence_window: int = 3,
                 improvement_threshold: float = 0.01,
                 stability_days: float = 7.0,
                 auto_stop_on_success: bool = True):
        self.max_iterations = max_iterations
        self.convergence_window = convergence_window
        self.improvement_threshold = improvement_threshold
        self.stability_days = stability_days
        self.auto_stop_on_success = auto_stop_on_success
        
        self._default_criteria = self._build_default_criteria()
        self.current_session: Optional[AlchemySession] = None
        self._session_lock = threading.Lock()
        
        self.iteration_history: List[IterationResult] = []
        self._phase_handlers: Dict[FurnacePhase, Callable] = {}
        self.global_state: Dict[str, Any] = {
            "total_iterations": 0,
            "total_duration_hours": 0.0,
            "best_accuracy": 0.0,
            "best_error_rate": 1.0,
            "best_response_time": float("inf"),
            "furnace_started_at": None,
            "last_improvement_iteration": 0,
        }
        self._event_callbacks: List[Callable] = []
        self._milestones: List[Dict[str, Any]] = []

    def _build_default_criteria(self) -> List[SuccessThreshold]:
        return [
            SuccessThreshold(
                criteria=SuccessCriteria.ACCURACY_RATE,
                target_value=0.95,
                operator=">=",
                weight=0.30,
                description="核心任务准确率≥95%（房产估价/命理分析）",
            ),
            SuccessThreshold(
                criteria=SuccessCriteria.ERROR_RATE,
                target_value=0.005,
                operator="<=",
                weight=0.25,
                description="错误率<0.5%",
            ),
            SuccessThreshold(
                criteria=SuccessCriteria.AVG_RESPONSE_TIME,
                target_value=1.0,
                operator="<=",
                weight=0.20,
                description="平均响应时间<1秒",
            ),
            SuccessThreshold(
                criteria=SuccessCriteria.UPTIME_7D,
                target_value=0.999,
                operator=">=",
                weight=0.15,
                description="7天可用性≥99.9%",
            ),
            SuccessThreshold(
                criteria=SuccessCriteria.NO_MANUAL_INTERVENTION,
                target_value=1.0,
                operator="==",
                weight=0.05,
                description="全程无人工干预",
            ),
            SuccessThreshold(
                criteria=SuccessCriteria.CONVERGENCE_STABLE,
                target_value=1.0,
                operator="==",
                weight=0.05,
                description="连续3次迭代提升<1%且全部达标",
            ),
        ]

    def start_session(self, custom_criteria: Optional[List[SuccessThreshold]] = None) -> AlchemySession:
        session = AlchemySession(
            session_id=f"furnace_{uuid.uuid4().hex[:12]}",
            start_time=time.time(),
            phase=FurnacePhase.INITIALIZATION,
            success_criteria=custom_criteria or list(self._default_criteria),
        )
        with self._session_lock:
            self.current_session = session
        self.global_state["furnace_started_at"] = session.start_time
        self._log_event(session, "SESSION_STARTED", f"炼丹会话 {session.session_id} 启动")
        logger.info(f"🔥 炼丹炉启动: {session.session_id}, 最大迭代={self.max_iterations}")
        return session

    def register_phase_handler(self, phase: FurnacePhase, handler: Callable):
        self._phase_handlers[phase] = handler

    def advance_phase(self, new_phase: FurnacePhase, reason: str = "") -> bool:
        with self._session_lock:
            if not self.current_session:
                return False
            old_phase = self.current_session.phase
            self.current_session.phase = new_phase
        self._log_event(self.current_session, "PHASE_CHANGE",
                       f"{old_phase.value} → {new_phase.value}: {reason}")
        logger.info(f"🔥 阶段切换: {old_phase.value} → {new_phase.value}")
        handler = self._phase_handlers.get(new_phase)
        if handler:
            try:
                handler(self.current_session)
            except Exception as e:
                logger.error(f"阶段处理器执行失败 ({new_phase.value}): {e}")
        return True

    def record_iteration(self, metrics: Dict[str, float],
                          actions: List[str],
                          duration: float) -> IterationResult:
        with self._session_lock:
            if not self.current_session:
                raise RuntimeError("没有活跃的炼丹会话")
            session = self.current_session
            session.iteration_count += 1
            iter_id = session.iteration_count
        
        improvements = self._compute_improvements(metrics)
        converged = self._check_convergence(iter_id)
        
        result = IterationResult(
            iteration_id=iter_id,
            timestamp=time.time(),
            phase=session.phase,
            metrics=dict(metrics),
            improvements=improvements,
            actions_taken=list(actions),
            duration_seconds=duration,
            converged=converged,
        )
        
        self.iteration_history.append(result)
        self.global_state["total_iterations"] = iter_id
        self.global_state["total_duration_hours"] += duration / 3600.0
        
        for crit in session.success_criteria:
            metric_key = crit.criteria.value
            if metric_key in metrics:
                crit.current_value = metrics[metric_key]
                crit.achieved = self._evaluate_criteria(crit)
        
        if metrics.get("accuracy_rate", 0) > self.global_state["best_accuracy"]:
            self.global_state["best_accuracy"] = metrics["accuracy_rate"]
            self.global_state["last_improvement_iteration"] = iter_id
        if metrics.get("error_rate", 1.0) < self.global_state["best_error_rate"]:
            self.global_state["best_error_rate"] = metrics["error_rate"]
        rt = metrics.get("avg_response_time", float("inf"))
        if rt < self.global_state["best_response_time"]:
            self.global_state["best_response_time"] = rt
        
        session.convergence_history.append({
            "iteration": iter_id,
            "timestamp": result.timestamp,
            **metrics,
        })
        session.best_metrics = dict(metrics)
        
        if any(imp > self.improvement_threshold for imp in improvements.values()):
            self._add_milestone("IMPROVEMENT", f"迭代{iter_id}显著提升", metrics)
        
        self._notify_callbacks(result)
        return result

    def _compute_improvements(self, current_metrics: Dict[str, float]) -> Dict[str, float]:
        if len(self.iteration_history) < 2:
            return {k: 0.0 for k in current_metrics}
        prev = self.iteration_history[-2].metrics
        improvements = {}
        for key, current_val in current_metrics.items():
            prev_val = prev.get(key)
            if prev_val is not None and prev_val != 0:
                improvements[key] = (current_val - prev_val) / abs(prev_val)
            else:
                improvements[key] = 0.0
        return improvements

    def _check_convergence(self, current_iter: int) -> bool:
        if len(self.iteration_history) < self.convergence_window:
            return False
        recent = self.iteration_history[-self.convergence_window:]
        all_small = all(
            all(abs(imp) < self.improvement_threshold for imp in r.improvements.values())
            for r in recent
        )
        return all_small and current_iter >= self.convergence_window

    def _evaluate_criteria(self, criterion: SuccessThreshold) -> bool:
        val = criterion.current_value
        target = criterion.target_value
        op = criterion.operator
        if op == ">=":
            return val >= target
        elif op == "<=":
            return val <= target
        elif op == "==":
            return abs(val - target) < 0.001
        elif op == ">":
            return val > target
        elif op == "<":
            return val < target
        return False

    def check_success_conditions(self) -> Tuple[bool, Dict[str, Any]]:
        session = self.current_session
        if not session:
            return False, {"reason": "no_active_session"}
        results = {"all_met": True, "details": [], "score": 0.0}
        total_weight = sum(c.weight for c in session.success_criteria)
        for crit in session.success_criteria:
            met = crit.achieved
            detail = {
                "criteria": crit.criteria.value,
                "target": crit.target_value,
                "current": round(crit.current_value, 4),
                "met": met,
                "weight": crit.weight,
                "description": crit.description,
            }
            results["details"].append(detail)
            if met:
                results["score"] += crit.weight / total_weight
            else:
                results["all_met"] = False
        results["score"] = round(results["score"], 4)
        is_converged = len(self.iteration_history) >= self.convergence_window
        if is_converged:
            recent = self.iteration_history[-self.convergence_window:]
            is_converged = all(r.converged for r in recent)
        results["converged"] = is_converged
        results["success"] = results["all_met"] and is_converged
        return results["success"], results

    def should_stop_furnace(self) -> Tuple[bool, str]:
        session = self.current_session
        if not session:
            return True, "no_session"
        if session.iteration_count >= self.max_iterations:
            return True, "max_iterations_reached"
        success, details = self.check_success_conditions()
        if success and self.auto_stop_on_success:
            return True, "success_all_criteria_met"
        if details.get("converged") and details.get("all_met"):
            return True, "converged_and_stable"
        elapsed = time.time() - session.start_time
        if elapsed > self.stability_days * 86400:
            return True, f"stability_period_exceeded_{self.stability_days}d"
        return False, "continue"

    def complete_session(self, status: str = "COMPLETED") -> AlchemySession:
        with self._session_lock:
            if not self.current_session:
                raise RuntimeError("没有活跃的炼丹会话")
            session = self.current_session
            session.end_time = time.time()
            session.final_status = status
            if status == "COMPLETED":
                session.phase = FurnacePhase.COMPLETED
            else:
                session.phase = FurnacePhase.FAILED
        _, details = self.check_success_conditions()
        summary = {
            "session_id": session.session_id,
            "status": status,
            "total_iterations": session.iteration_count,
            "duration_hours": round((session.end_time - session.start_time) / 3600, 2),
            "best_metrics": session.best_metrics,
            "criteria_score": details.get("score", 0),
            "criteria_details": details.get("details", []),
            "artifacts": session.artifacts,
        }
        self._log_event(session, "SESSION_COMPLETED", json.dumps(summary, ensure_ascii=False))
        logger.info(f"🔥 炼丹{'成功' if status == 'COMPLETED' else '终止'}: "
                     f"{session.session_id}, 迭代{session.iteration_count}次")
        return session

    def _log_event(self, session: AlchemySession, event_type: str, message: str):
        entry = {
            "timestamp": time.time(),
            "type": event_type,
            "message": message,
            "phase": session.phase.value,
            "iteration": session.iteration_count,
        }
        session.logs.append(entry)

    def _add_milestone(self, milestone_type: str, title: str, data: Dict[str, Any]):
        self._milestones.append({
            "type": milestone_type,
            "title": title,
            "data": data,
            "timestamp": time.time(),
            "iteration": self.current_session.iteration_count if self.current_session else 0,
        })

    def register_callback(self, callback: Callable):
        self._event_callbacks.append(callback)

    def _notify_callbacks(self, result: IterationResult):
        for cb in self._event_callbacks:
            try:
                cb(result)
            except Exception as e:
                logger.warning(f"回调执行失败: {e}")

    def get_furnace_report(self) -> Dict[str, Any]:
        session = self.current_session
        success, details = self.check_success_conditions()
        report = {
            "furnace_state": {
                "active": session is not None,
                "current_phase": session.phase.value if session else None,
                "session_id": session.session_id if session else None,
                "elapsed_hours": round((time.time() - session.start_time) / 3600, 2) if session else 0,
            },
            "progress": {
                "iterations_done": session.iteration_count if session else 0,
                "max_iterations": self.max_iterations,
                "progress_pct": round((session.iteration_count / max(self.max_iterations, 1)) * 100, 1) if session else 0,
            },
            "global_best": {
                "accuracy": round(self.global_state["best_accuracy"], 4),
                "error_rate": round(self.global_state["best_error_rate"], 4),
                "response_time_ms": round(self.global_state["best_response_time"], 2),
                "last_improvement_iter": self.global_state["last_improvement_iteration"],
            },
            "success_check": details,
            "recent_iterations": [
                {
                    "id": r.iteration_id,
                    "metrics": r.metrics,
                    "improvements": {k: round(v, 4) for k, v in r.improvements.items()},
                    "converged": r.converged,
                } for r in self.iteration_history[-10:]
            ],
            "milestones": self._milestones[-10:],
        }
        return report

    def export_session_log(self, filepath: str) -> bool:
        session = self.current_session
        if not session:
            return False
        try:
            output = {
                "session_info": {
                    "session_id": session.session_id,
                    "start_time": datetime.fromtimestamp(session.start_time).isoformat(),
                    "end_time": (datetime.fromtimestamp(session.end_time).isoformat()
                                 if session.end_time else None),
                    "status": session.final_status or session.phase.value,
                    "total_iterations": session.iteration_count,
                },
                "success_criteria": [asdict(c) for c in session.success_criteria],
                "best_metrics": session.best_metrics,
                "convergence_history": session.convergence_history[-200:],
                "artifacts": session.artifacts,
                "logs": session.logs[-500:],
                "furnace_report": self.get_furnace_report(),
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"炼丹日志已导出至 {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            return False


# ==================== 1.2 五层分层架构 ====================


class ArchitectureLayer(Enum):
    DATA_LAYER = "data_layer"
    TRAINING_LAYER = "training_layer"
    VALIDATION_LAYER = "validation_layer"
    REPAIR_LAYER = "repair_layer"
    MONITORING_LAYER = "monitoring_layer"


@dataclass
class LayerComponent:
    """层组件"""
    component_id: str
    name: str
    layer: ArchitectureLayer
    version: str
    status: str
    health_score: float
    last_active: float
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlowRecord:
    """数据流记录"""
    flow_id: str
    source_layer: ArchitectureLayer
    source_component: str
    target_layer: ArchitectureLayer
    target_component: str
    data_type: str
    data_volume: int
    latency_ms: float
    timestamp: float
    success: bool


class LayeredArchitecture:
    """
    五层分层架构（提示词 1.2）
    
    层级定义：
    1. 数据层(DataLayer): 存储历史数据、生成数据、模型版本、进化日志
    2. 训练层(TrainingLayer): 执行自博弈训练、强化学习、元学习
    3. 验证层(ValidationLayer): 多维度评估智能体性能
    4. 修复层(RepairLayer): 自动调优、热更新、规则修正
    5. 监控层(MonitoringLayer): 可视化、告警、根因分析
    
    数据流：
    训练层产出模型→验证层评估→修复层优化→监控层记录→训练层再迭代
    """

    def __init__(self):
        self.layers: Dict[ArchitectureLayer, Dict[str, LayerComponent]] = {
            layer: {} for layer in ArchitectureLayer
        }
        self.data_flows: List[DataFlowRecord] = []
        self._flow_lock = threading.LayeredArchitecture = threading.Lock() if hasattr(threading, 'Lock') else type('Lock', (), {'__enter__': lambda s: s, '__exit__': lambda s, *a: None})()
        self._layer_descriptions = {
            ArchitectureLayer.DATA_LAYER: "存储历史数据、生成数据、模型版本、进化日志",
            ArchitectureLayer.TRAINING_LAYER: "执行自博弈训练、强化学习、元学习",
            ArchitectureLayer.VALIDATION_LAYER: "多维度评估智能体性能",
            ArchitectureLayer.REPAIR_LAYER: "自动调优、热更新、规则修正",
            ArchitectureLayer.MONITORING_LAYER: "可视化、告警、根因分析",
        }

    def register_component(self, component: LayerComponent) -> bool:
        layer = component.layer
        if layer not in self.layers:
            return False
        self.layers[layer][component.component_id] = component
        logger.debug(f"组件注册: {component.name} → {layer.value}")
        return True

    def get_layer_health(self, layer: ArchitectureLayer) -> Dict[str, Any]:
        components = list(self.layers.get(layer, {}).values())
        if not components:
            return {"layer": layer.value, "component_count": 0, "health": 1.0, "status": "empty"}
        healths = [c.health_score for c in components]
        avg_health = round(statistics.mean(healths), 4) if healths else 1.0
        min_health = round(min(healths), 4) if healths else 1.0
        active_count = sum(1 for c in components if c.status == "active")
        return {
            "layer": layer.value,
            "description": self._layer_descriptions.get(layer, ""),
            "component_count": len(components),
            "active_components": active_count,
            "avg_health": avg_health,
            "min_health": min_health,
            "overall_status": "healthy" if avg_health >= 0.8 else "degraded" if avg_health >= 0.5 else "critical",
            "components": [{"id": c.component_id, "name": c.name, "health": c.health_score, "status": c.status}
                           for c in components],
        }

    def record_data_flow(self, source_layer: ArchitectureLayer, source_comp: str,
                          target_layer: ArchitectureLayer, target_comp: str,
                          data_type: str, volume: int, latency_ms: float,
                          success: bool = True) -> DataFlowRecord:
        flow = DataFlowRecord(
            flow_id=f"flow_{uuid.uuid4().hex[:8]}",
            source_layer=source_layer,
            source_component=source_comp,
            target_layer=target_layer,
            target_component=target_comp,
            data_type=data_type,
            data_volume=volume,
            latency_ms=latency_ms,
            timestamp=time.time(),
            success=success,
        )
        self.data_flows.append(flow)
        if len(self.data_flows) > 50000:
            self.data_flows = self.data_flows[-30000:]
        return flow

    def get_architecture_overview(self) -> Dict[str, Any]:
        overview = {
            "architecture_name": "房都督智能体自进化炼丹系统-五层架构",
            "layers": {},
            "data_flow_stats": {},
            "system_health": 1.0,
        }
        all_health = []
        for layer in ArchitectureLayer:
            info = self.get_layer_health(layer)
            overview["layers"][layer.value] = info
            if info["component_count"] > 0:
                all_health.append(info["avg_health"])
        if all_health:
            overview["system_health"] = round(statistics.mean(all_health), 4)
        recent_flows = [f for f in self.data_flows if time.time() - f.timestamp < 3600]
        if recent_flows:
            overview["data_flow_stats"] = {
                "flows_last_hour": len(recent_flows),
                "avg_latency_ms": round(statistics.mean([f.latency_ms for f in recent_flows]), 2),
                "success_rate": round(sum(1 for f in recent_flows if f.success) / len(recent_flows), 4),
                "total_data_volume": sum(f.data_volume for f in recent_flows),
            }
        return overview

    def validate_data_flow_integrity(self) -> List[Dict[str, str]]:
        issues = []
        layer_order = [
            ArchitectureLayer.DATA_LAYER,
            ArchitectureLayer.TRAINING_LAYER,
            ArchitectureLayer.VALIDATION_LAYER,
            ArchitectureLayer.REPAIR_LAYER,
            ArchitectureLayer.MONITORING_LAYER,
        ]
        for i, layer in enumerate(layer_order):
            comps = self.layers.get(layer, {})
            if not comps:
                issues.append({
                    "severity": "warning",
                    "layer": layer.value,
                    "issue": f"{layer.value}无注册组件",
                })
            for comp in comps.values():
                for dep_id in comp.dependencies:
                    found = any(dep_id == c.component_id
                                for l in self.layers.values()
                                for c in l.values())
                    if not found:
                        issues.append({
                            "severity": "error",
                            "component": comp.name,
                            "issue": f"依赖'{dep_id}'未找到对应组件",
                        })
        return issues


# ==================== 1.3 数据与模型版本管理 ====================


class ArtifactType(Enum):
    MODEL = "model"
    DATASET = "dataset"
    CONFIG = "config"
    LOG = "log"
    REPORT = "report"
    METRIC = "metric"


@dataclass
class VersionedArtifact:
    """带版本的产物"""
    artifact_id: str
    name: str
    artifact_type: ArtifactType
    version: str
    parent_version: Optional[str]
    tags: List[str]
    storage_path: Optional[str]
    metadata: Dict[str, Any]
    created_at: float
    created_by: str
    checksum: str
    size_bytes: int
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ExperimentRun:
    """实验运行记录"""
    run_id: str
    experiment_name: string
    artifact_versions: Dict[str, str]
    params: Dict[str, Any]
    metrics: Dict[str, float]
    status: str
    start_time: float
    end_time: Optional[float]
    duration_seconds: float = 0.0
    tags: List[str] = field(default_factory=list)
    parent_run_id: Optional[str] = None


class ModelVersionManager:
    """
    数据与模型版本管理器（MLflow风格）（提示词 1.3）
    
    功能：
    - 为每次炼丹生成唯一ID，关联所有产物（数据、模型、日志、报告）
    - 使用版本化存储，支持追溯和回滚
    - 记录每次训练的超参数、训练数据版本、验证指标
    - 支持产物间的血缘关系追踪
    
    设计参考 MLflow 的 Model Registry + Experiment Tracking
    """

    def __init__(self, storage_base_path: str = "./alchemy_artifacts"):
        self.storage_base_path = storage_base_path
        self.artifacts: Dict[str, VersionedArtifact] = {}
        self.experiments: Dict[str, ExperimentRun] = {}
        self.type_index: Dict[ArtifactType, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.version_chains: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.Lock()

    def create_experiment(self, name: str, params: Dict[str, Any],
                           tags: Optional[List[str]] = None,
                           parent_run_id: Optional[str] = None) -> ExperimentRun:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run = ExperimentRun(
            run_id=run_id,
            experiment_name=name,
            artifact_versions={},
            params=params,
            metrics={},
            status="running",
            start_time=time.time(),
            tags=tags or [],
            parent_run_id=parent_run_id,
        )
        with self._lock:
            self.experiments[run_id] = run
        logger.info(f"实验创建: {run_id} ({name})")
        return run

    def log_artifact(self, run_id: str, name: str, artifact_type: ArtifactType,
                      version: str, metadata: Dict[str, Any],
                      content: Optional[Any] = None,
                      parent_version: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> Optional[VersionedArtifact]:
        artifact_id = f"{artifact_type.value}_{name}_{version}"
        checksum = ""
        size_bytes = 0
        storage_path = None
        if content is not None:
            import os as _os
            type_dir = self.storage_base_path + "/" + artifact_type.value + "/"
            _os.makedirs(type_dir, exist_ok=True)
            file_path = type_dir + f"{name}_v{version}.json"
            if isinstance(content, (dict, list)):
                content_str = json.dumps(content, ensure_ascii=False)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content_str)
                checksum = hashlib.md5(content_str.encode()).hexdigest()[:16]
                size_bytes = len(content_str.encode())
            elif isinstance(content, str):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                checksum = hashlib.md5(content.encode()).hexdigest()[:16]
                size_bytes = len(content.encode())
            storage_path = file_path
        artifact = VersionedArtifact(
            artifact_id=artifact_id,
            name=name,
            artifact_type=artifact_type,
            version=version,
            parent_version=parent_version,
            tags=tags or [],
            storage_path=storage_path,
            metadata=metadata,
            created_at=time.time(),
            created_by="alchemy_system",
            checksum=checksum,
            size_bytes=size_bytes,
        )
        with self._lock:
            self.artifacts[artifact_id] = artifact
            self.type_index[artifact_type].append(artifact_id)
            for tag in tags or []:
                self.tag_index[tag].append(artifact_id)
            if parent_version:
                chain_key = f"{artifact_type.value}_{name}"
                self.version_chains[chain_key].append(artifact_id)
            if run_id in self.experiments:
                self.experiments[run_id].artifact_versions[name] = artifact_id
        return artifact

    def log_metric(self, run_id: str, key: str, value: float, step: int = 0):
        with self._lock:
            if run_id in self.experiments:
                self.experiments[run_id].metrics[f"{key}_step{step}"] = value
                if step == 0:
                    self.experiments[run_id].metrics[key] = value

    def log_param(self, run_id: str, key: str, value: Any):
        with self._lock:
            if run_id in self.experiments:
                self.experiments[run_id].params[key] = value

    def finish_experiment(self, run_id: str, status: str = "completed"):
        with self._lock:
            if run_id in self.experiments:
                run = self.experiments[run_id]
                run.status = status
                run.end_time = time.time()
                run.duration_seconds = run.end_time - run.start_time

    def get_artifact(self, artifact_id: str) -> Optional[VersionedArtifact]:
        return self.artifacts.get(artifact_id)

    def get_latest_version(self, name: str, artifact_type: ArtifactType) -> Optional[VersionedArtifact]:
        candidates = [self.artifacts[aid] for aid in self.type_index.get(artifact_type, [])
                      if self.artifacts.get(aid) and self.artifacts[aid].name == name]
        if not candidates:
            return None
        candidates.sort(key=lambda a: a.created_at, reverse=True)
        return candidates[0]

    def get_lineage(self, artifact_id: str) -> List[VersionedArtifact]:
        lineage = []
        current = self.artifacts.get(artifact_id)
        while current:
            lineage.append(current)
            current = self.artifacts.get(current.parent_version or "") if current.parent_version else None
        return lineage

    def search_artifacts(self, artifact_type: Optional[ArtifactType] = None,
                          tags: Optional[List[str]] = None,
                          name_pattern: Optional[str] = None,
                          limit: int = 50) -> List[VersionedArtifact]:
        results = list(self.artifacts.values())
        if artifact_type:
            results = [a for a in results if a.artifact_type == artifact_type]
        if tags:
            for tag in tags:
                tagged_ids = set(self.tag_index.get(tag, []))
                results = [a for a in results if a.artifact_id in tagged_ids]
        if name_pattern:
            regex = re.compile(name_pattern, re.IGNORECASE)
            results = [a for a in results if regex.search(a.name)]
        results.sort(key=lambda a: a.created_at, reverse=True)
        return results[:limit]

    def get_experiment_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.experiments.get(run_id)
        if not run:
            return None
        artifact_details = []
        for aname, aid in run.artifact_versions.items():
            art = self.artifacts.get(aid)
            if art:
                artifact_details.append({
                    "name": aname,
                    "id": aid,
                    "type": art.artifact_type.value,
                    "version": art.version,
                    "size": art.size_bytes,
                })
        return {
            "run_id": run.run_id,
            "experiment_name": run.experiment_name,
            "status": run.status,
            "params": run.params,
            "metrics": run.metrics,
            "duration_seconds": round(run.duration_seconds, 2),
            "artifacts": artifact_details,
            "tags": run.tags,
            "parent_run_id": run.parent_run_id,
        }

    def compare_versions(self, name: str, artifact_type: ArtifactType,
                          v1: str, v2: str) -> Optional[Dict[str, Any]]:
        a1 = None
        a2 = None
        for aid in self.type_index.get(artifact_type, []):
            art = self.artifacts.get(aid)
            if art and art.name == name:
                if art.version == v1:
                    a1 = art
                elif art.version == v2:
                    a2 = art
        if not a1 or not a2:
            return None
        shared_keys = set(a1.metrics.keys()) & set(a2.metrics.keys())
        comparison = {
            "artifact_name": name,
            "v1": {"version": v1, "created": datetime.fromtimestamp(a1.created_at).isoformat(),
                   "metrics": a1.metrics, "checksum": a1.checksum},
            "v2": {"version": v2, "created": datetime.fromtimestamp(a2.created_at).isoformat(),
                   "metrics": a2.metrics, "checksum": a2.checksum},
            "metric_delta": {},
        }
        for key in sorted(shared_keys):
            delta = a2.metrics.get(key, 0) - a1.metrics.get(key, 0)
            comparison["metric_delta"][key] = round(delta, 6)
        return comparison

    def export_registry(self, filepath: str) -> bool:
        try:
            registry_data = {
                "exported_at": datetime.now().isoformat(),
                "total_artifacts": len(self.artifacts),
                "total_experiments": len(self.experiments),
                "artifacts": [{**asdict(a), "created_at": datetime.fromtimestamp(a.created_at).isoformat()}
                               for a in list(self.artifacts.values())[:500]],
                "experiments": [{**asdict(e), "start_time": datetime.fromtimestamp(e.start_time).isoformat(),
                                  "end_time": (datetime.fromtimestamp(e.end_time).isoformat() if e.end_time else None)}
                                 for e in list(self.experiments.values())[:200]],
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(registry_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"版本注册表已导出至 {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出注册表失败: {e}")
            return False


# ==================== 全局实例 ====================

alchemy_furnace = AlchemyFurnace()
layered_architecture = LayeredArchitecture()
model_version_manager = ModelVersionManager()
