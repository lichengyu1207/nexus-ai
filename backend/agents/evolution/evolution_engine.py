"""
三省六部制智能体自我进化系统
Self-Evolution System for Three Provinces Six Ministries Agents

实现智能体的元认知、自我诊断、建议生成和自我升级能力
"""

import os
import json
import time
import uuid
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
from abc import ABC, abstractmethod
import random
import hashlib

logger = logging.getLogger(__name__)


class AgentType(Enum):
    LI = "li"
    HU = "hu"
    LI_GUAN = "li_guan"
    BING = "bing"
    GONG = "gong"
    XING = "xing"
    MEMORY = "memory"
    COORDINATOR = "coordinator"


class DiagnosisType(Enum):
    PERFORMANCE_DROP = "performance_drop"
    ERROR_RATE_HIGH = "error_rate_high"
    LATENCY_INCREASE = "latency_increase"
    USER_FEEDBACK_NEGATIVE = "user_feedback_negative"
    MODEL_DRIFT = "model_drift"
    DATA_STALE = "data_stale"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    COLLABORATION_ISSUE = "collaboration_issue"


class SuggestionType(Enum):
    RETRAIN_MODEL = "retrain_model"
    UPDATE_PARAMETERS = "update_parameters"
    ADD_TRAINING_DATA = "add_training_data"
    ARCHITECTURE_CHANGE = "architecture_change"
    RESOURCE_ADJUSTMENT = "resource_adjustment"
    COLLABORATION_TUNING = "collaboration_tuning"
    MEMORY_OPTIMIZATION = "memory_optimization"
    CODE_UPDATE = "code_update"


class SuggestionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


@dataclass
class DecisionTrajectory:
    trajectory_id: str
    agent_id: str
    timestamp: float
    input_context: Dict
    decision: Dict
    execution_time: float
    success: bool
    user_feedback: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "trajectory_id": self.trajectory_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "input_context": self.input_context,
            "decision": self.decision,
            "execution_time": self.execution_time,
            "success": self.success,
            "user_feedback": self.user_feedback,
            "error_message": self.error_message
        }


@dataclass
class PerformanceStats:
    total_decisions: int = 0
    successful_decisions: int = 0
    failed_decisions: int = 0
    avg_execution_time: float = 0.0
    avg_user_feedback: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    
    recent_success_rate: float = 0.0
    recent_avg_time: float = 0.0
    recent_feedback: float = 0.0
    
    baseline_success_rate: float = 0.8
    baseline_avg_time: float = 1.0
    baseline_feedback: float = 0.7
    
    last_updated: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_decisions": self.total_decisions,
            "successful_decisions": self.successful_decisions,
            "failed_decisions": self.failed_decisions,
            "avg_execution_time": self.avg_execution_time,
            "avg_user_feedback": self.avg_user_feedback,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "recent_success_rate": self.recent_success_rate,
            "recent_avg_time": self.recent_avg_time,
            "recent_feedback": self.recent_feedback,
            "baseline_success_rate": self.baseline_success_rate,
            "baseline_avg_time": self.baseline_avg_time,
            "baseline_feedback": self.baseline_feedback,
            "last_updated": self.last_updated
        }


@dataclass
class Diagnosis:
    diagnosis_id: str
    agent_id: str
    diagnosis_type: DiagnosisType
    severity: float
    description: str
    metrics: Dict
    timestamp: float
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "agent_id": self.agent_id,
            "diagnosis_type": self.diagnosis_type.value,
            "severity": self.severity,
            "description": self.description,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "resolved": self.resolved
        }


@dataclass
class Suggestion:
    suggestion_id: str
    agent_id: str
    suggestion_type: SuggestionType
    title: str
    description: str
    priority: int
    impact_estimate: float
    implementation_effort: str
    code_changes: Optional[str] = None
    parameters: Optional[Dict] = None
    status: SuggestionStatus = SuggestionStatus.PENDING
    created_at: float = 0.0
    reviewed_at: Optional[float] = None
    reviewed_by: Optional[str] = None
    applied_at: Optional[float] = None
    result: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "suggestion_id": self.suggestion_id,
            "agent_id": self.agent_id,
            "suggestion_type": self.suggestion_type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "impact_estimate": self.impact_estimate,
            "implementation_effort": self.implementation_effort,
            "code_changes": self.code_changes,
            "parameters": self.parameters,
            "status": self.status.value,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "applied_at": self.applied_at,
            "result": self.result
        }


@dataclass
class AgentVersion:
    version_id: str
    agent_id: str
    version_number: str
    strategy_hash: str
    parameters_hash: str
    created_at: float
    performance_metrics: Dict
    is_active: bool = False
    rollback_available: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "agent_id": self.agent_id,
            "version_number": self.version_number,
            "strategy_hash": self.strategy_hash,
            "parameters_hash": self.parameters_hash,
            "created_at": self.created_at,
            "performance_metrics": self.performance_metrics,
            "is_active": self.is_active,
            "rollback_available": self.rollback_available
        }


class MetaCognitionModule:
    """
    元认知模块
    
    为智能体提供自我监控、偏差检测、归因分析和改进提案能力
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        trajectory_buffer_size: int = 1000,
        anomaly_threshold: float = 2.0,
        min_samples_for_analysis: int = 50
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.trajectory_buffer_size = trajectory_buffer_size
        self.anomaly_threshold = anomaly_threshold
        self.min_samples_for_analysis = min_samples_for_analysis
        
        self.trajectory_buffer: deque = deque(maxlen=trajectory_buffer_size)
        self.recent_buffer: deque = deque(maxlen=100)
        
        self.performance_stats = PerformanceStats()
        
        self.diagnosis_history: List[Diagnosis] = []
        self.suggestion_history: List[Suggestion] = []
        
        self._lock = threading.RLock()
        
        self.stats = {
            "trajectories_recorded": 0,
            "diagnoses_generated": 0,
            "suggestions_generated": 0,
            "anomalies_detected": 0
        }
    
    def record_trajectory(
        self,
        input_context: Dict,
        decision: Dict,
        execution_time: float,
        success: bool,
        user_feedback: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> str:
        trajectory_id = f"traj_{uuid.uuid4().hex[:12]}"
        
        trajectory = DecisionTrajectory(
            trajectory_id=trajectory_id,
            agent_id=self.agent_id,
            timestamp=time.time(),
            input_context=input_context,
            decision=decision,
            execution_time=execution_time,
            success=success,
            user_feedback=user_feedback,
            error_message=error_message
        )
        
        with self._lock:
            self.trajectory_buffer.append(trajectory)
            self.recent_buffer.append(trajectory)
            self._update_stats(trajectory)
            self.stats["trajectories_recorded"] += 1
        
        return trajectory_id
    
    def _update_stats(self, new_trajectory: DecisionTrajectory):
        stats = self.performance_stats
        
        stats.total_decisions += 1
        if new_trajectory.success:
            stats.successful_decisions += 1
        else:
            stats.failed_decisions += 1
        
        n = stats.total_decisions
        stats.avg_execution_time = (
            (stats.avg_execution_time * (n - 1) + new_trajectory.execution_time) / n
        )
        
        if new_trajectory.user_feedback is not None:
            feedback_count = sum(1 for t in self.trajectory_buffer if t.user_feedback is not None)
            if feedback_count > 0:
                total_feedback = sum(t.user_feedback for t in self.trajectory_buffer if t.user_feedback is not None)
                stats.avg_user_feedback = total_feedback / feedback_count
        
        stats.success_rate = stats.successful_decisions / stats.total_decisions
        stats.error_rate = stats.failed_decisions / stats.total_decisions
        
        if len(self.recent_buffer) >= 10:
            recent = list(self.recent_buffer)
            stats.recent_success_rate = sum(1 for t in recent if t.success) / len(recent)
            stats.recent_avg_time = sum(t.execution_time for t in recent) / len(recent)
            
            recent_feedbacks = [t.user_feedback for t in recent if t.user_feedback is not None]
            if recent_feedbacks:
                stats.recent_feedback = sum(recent_feedbacks) / len(recent_feedbacks)
        
        stats.last_updated = time.time()
    
    def detect_anomalies(self) -> List[Diagnosis]:
        if len(self.trajectory_buffer) < self.min_samples_for_analysis:
            return []
        
        diagnoses = []
        stats = self.performance_stats
        
        if stats.recent_success_rate < stats.baseline_success_rate - 0.1:
            severity = (stats.baseline_success_rate - stats.recent_success_rate) / stats.baseline_success_rate
            diagnoses.append(Diagnosis(
                diagnosis_id=f"diag_{uuid.uuid4().hex[:8]}",
                agent_id=self.agent_id,
                diagnosis_type=DiagnosisType.PERFORMANCE_DROP,
                severity=min(1.0, severity),
                description=f"成功率下降: {stats.recent_success_rate:.2%} vs 基线 {stats.baseline_success_rate:.2%}",
                metrics={
                    "current_rate": stats.recent_success_rate,
                    "baseline_rate": stats.baseline_success_rate,
                    "drop": stats.baseline_success_rate - stats.recent_success_rate
                },
                timestamp=time.time()
            ))
        
        if stats.recent_avg_time > stats.baseline_avg_time * 1.5:
            severity = (stats.recent_avg_time - stats.baseline_avg_time) / stats.baseline_avg_time
            diagnoses.append(Diagnosis(
                diagnosis_id=f"diag_{uuid.uuid4().hex[:8]}",
                agent_id=self.agent_id,
                diagnosis_type=DiagnosisType.LATENCY_INCREASE,
                severity=min(1.0, severity * 0.5),
                description=f"执行时间增加: {stats.recent_avg_time:.2f}s vs 基线 {stats.baseline_avg_time:.2f}s",
                metrics={
                    "current_time": stats.recent_avg_time,
                    "baseline_time": stats.baseline_avg_time,
                    "increase_ratio": stats.recent_avg_time / stats.baseline_avg_time
                },
                timestamp=time.time()
            ))
        
        if stats.error_rate > 0.1:
            diagnoses.append(Diagnosis(
                diagnosis_id=f"diag_{uuid.uuid4().hex[:8]}",
                agent_id=self.agent_id,
                diagnosis_type=DiagnosisType.ERROR_RATE_HIGH,
                severity=stats.error_rate,
                description=f"错误率过高: {stats.error_rate:.2%}",
                metrics={
                    "error_rate": stats.error_rate,
                    "failed_count": stats.failed_decisions
                },
                timestamp=time.time()
            ))
        
        if stats.recent_feedback < stats.baseline_feedback - 0.15:
            severity = (stats.baseline_feedback - stats.recent_feedback) / stats.baseline_feedback
            diagnoses.append(Diagnosis(
                diagnosis_id=f"diag_{uuid.uuid4().hex[:8]}",
                agent_id=self.agent_id,
                diagnosis_type=DiagnosisType.USER_FEEDBACK_NEGATIVE,
                severity=min(1.0, severity),
                description=f"用户反馈下降: {stats.recent_feedback:.2f} vs 基线 {stats.baseline_feedback:.2f}",
                metrics={
                    "current_feedback": stats.recent_feedback,
                    "baseline_feedback": stats.baseline_feedback
                },
                timestamp=time.time()
            ))
        
        with self._lock:
            self.diagnosis_history.extend(diagnoses)
            self.stats["diagnoses_generated"] += len(diagnoses)
            self.stats["anomalies_detected"] += len(diagnoses)
        
        return diagnoses
    
    def generate_suggestions(self, diagnoses: List[Diagnosis]) -> List[Suggestion]:
        suggestions = []
        
        for diagnosis in diagnoses:
            if diagnosis.diagnosis_type == DiagnosisType.PERFORMANCE_DROP:
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{uuid.uuid4().hex[:8]}",
                    agent_id=self.agent_id,
                    suggestion_type=SuggestionType.RETRAIN_MODEL,
                    title=f"重新训练{self.agent_type.value}智能体模型",
                    description=f"检测到性能下降，建议使用最新数据重新训练模型。原因: {diagnosis.description}",
                    priority=1 if diagnosis.severity > 0.5 else 2,
                    impact_estimate=diagnosis.severity * 0.8,
                    implementation_effort="medium",
                    parameters={
                        "training_data_days": 30,
                        "validation_split": 0.2
                    },
                    created_at=time.time()
                ))
                
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{uuid.uuid4().hex[:8]}",
                    agent_id=self.agent_id,
                    suggestion_type=SuggestionType.ADD_TRAINING_DATA,
                    title="补充训练数据",
                    description="性能下降可能由于数据分布变化，建议补充近期数据",
                    priority=2,
                    impact_estimate=diagnosis.severity * 0.6,
                    implementation_effort="low",
                    created_at=time.time()
                ))
            
            elif diagnosis.diagnosis_type == DiagnosisType.LATENCY_INCREASE:
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{uuid.uuid4().hex[:8]}",
                    agent_id=self.agent_id,
                    suggestion_type=SuggestionType.RESOURCE_ADJUSTMENT,
                    title="优化执行效率",
                    description=f"执行时间增加，建议优化算法或增加资源。当前: {diagnosis.metrics.get('current_time', 0):.2f}s",
                    priority=2,
                    impact_estimate=diagnosis.severity * 0.5,
                    implementation_effort="medium",
                    created_at=time.time()
                ))
            
            elif diagnosis.diagnosis_type == DiagnosisType.ERROR_RATE_HIGH:
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{uuid.uuid4().hex[:8]}",
                    agent_id=self.agent_id,
                    suggestion_type=SuggestionType.CODE_UPDATE,
                    title="修复错误模式",
                    description=f"错误率过高({diagnosis.metrics.get('error_rate', 0):.2%})，建议检查并修复常见错误模式",
                    priority=1,
                    impact_estimate=diagnosis.severity * 0.9,
                    implementation_effort="low",
                    created_at=time.time()
                ))
            
            elif diagnosis.diagnosis_type == DiagnosisType.USER_FEEDBACK_NEGATIVE:
                suggestions.append(Suggestion(
                    suggestion_id=f"sug_{uuid.uuid4().hex[:8]}",
                    agent_id=self.agent_id,
                    suggestion_type=SuggestionType.UPDATE_PARAMETERS,
                    title="调整响应策略",
                    description="用户反馈下降，建议调整响应策略以提高用户满意度",
                    priority=2,
                    impact_estimate=diagnosis.severity * 0.7,
                    implementation_effort="low",
                    parameters={
                        "adjustment_type": "user_preference_learning"
                    },
                    created_at=time.time()
                ))
        
        with self._lock:
            self.suggestion_history.extend(suggestions)
            self.stats["suggestions_generated"] += len(suggestions)
        
        return suggestions
    
    def get_performance_report(self) -> Dict:
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type.value,
                "performance_stats": self.performance_stats.to_dict(),
                "trajectory_count": len(self.trajectory_buffer),
                "recent_trajectory_count": len(self.recent_buffer),
                "diagnosis_count": len(self.diagnosis_history),
                "suggestion_count": len(self.suggestion_history),
                "stats": self.stats.copy()
            }
    
    def set_baseline(
        self,
        success_rate: Optional[float] = None,
        avg_time: Optional[float] = None,
        feedback: Optional[float] = None
    ):
        with self._lock:
            if success_rate is not None:
                self.performance_stats.baseline_success_rate = success_rate
            if avg_time is not None:
                self.performance_stats.baseline_avg_time = avg_time
            if feedback is not None:
                self.performance_stats.baseline_feedback = feedback


class EvolutionEngine:
    """
    进化引擎
    
    中央控制器，管理所有智能体的版本、诊断、建议、升级
    """
    
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        db_path: Optional[str] = None
    ):
        self.blackboard = blackboard
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "property-ai.db"
        )
        
        self.meta_cognition_modules: Dict[str, MetaCognitionModule] = {}
        self.agent_versions: Dict[str, List[AgentVersion]] = defaultdict(list)
        self.active_versions: Dict[str, AgentVersion] = {}
        
        self.pending_suggestions: List[Suggestion] = []
        self.applied_suggestions: List[Suggestion] = []
        
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        self._lock = threading.RLock()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "total_agents": 0,
            "total_diagnoses": 0,
            "total_suggestions": 0,
            "suggestions_applied": 0,
            "suggestions_rejected": 0,
            "rollbacks_performed": 0
        }
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        initial_version: str = "1.0.0"
    ) -> MetaCognitionModule:
        with self._lock:
            module = MetaCognitionModule(agent_id, agent_type)
            self.meta_cognition_modules[agent_id] = module
            
            version = AgentVersion(
                version_id=f"ver_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                version_number=initial_version,
                strategy_hash=hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                parameters_hash=hashlib.md5(str({}).encode()).hexdigest()[:8],
                created_at=time.time(),
                performance_metrics={},
                is_active=True
            )
            
            self.agent_versions[agent_id].append(version)
            self.active_versions[agent_id] = version
            
            self.stats["total_agents"] += 1
            
            logger.info(f"Registered agent {agent_id} with version {initial_version}")
            
            return module
    
    def unregister_agent(self, agent_id: str):
        with self._lock:
            if agent_id in self.meta_cognition_modules:
                del self.meta_cognition_modules[agent_id]
            self.stats["total_agents"] -= 1
    
    async def start(self):
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Evolution engine started")
    
    async def stop(self):
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Evolution engine stopped")
    
    async def _monitor_loop(self):
        while self._running:
            try:
                await self._collect_diagnoses()
                await self._process_suggestions()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evolution monitor loop: {e}")
                await asyncio.sleep(10)
    
    async def _collect_diagnoses(self):
        all_diagnoses = []
        
        with self._lock:
            for agent_id, module in self.meta_cognition_modules.items():
                diagnoses = module.detect_anomalies()
                all_diagnoses.extend(diagnoses)
                
                for diagnosis in diagnoses:
                    suggestions = module.generate_suggestions([diagnosis])
                    self.pending_suggestions.extend(suggestions)
                    self.stats["total_suggestions"] += len(suggestions)
        
        self.stats["total_diagnoses"] += len(all_diagnoses)
        
        if all_diagnoses and self.blackboard:
            self.blackboard.write(
                "evolution:latest_diagnoses",
                [d.to_dict() for d in all_diagnoses],
                ttl=3600
            )
        
        self._notify_subscribers("diagnoses_collected", all_diagnoses)
    
    async def _process_suggestions(self):
        pass
    
    def get_pending_suggestions(self, agent_id: Optional[str] = None) -> List[Suggestion]:
        with self._lock:
            if agent_id:
                return [s for s in self.pending_suggestions if s.agent_id == agent_id]
            return list(self.pending_suggestions)
    
    def approve_suggestion(self, suggestion_id: str, reviewer: str = "system") -> bool:
        with self._lock:
            for i, suggestion in enumerate(self.pending_suggestions):
                if suggestion.suggestion_id == suggestion_id:
                    suggestion.status = SuggestionStatus.APPROVED
                    suggestion.reviewed_at = time.time()
                    suggestion.reviewed_by = reviewer
                    
                    self._notify_subscribers("suggestion_approved", suggestion)
                    return True
        return False
    
    def reject_suggestion(self, suggestion_id: str, reviewer: str = "system", reason: str = "") -> bool:
        with self._lock:
            for i, suggestion in enumerate(self.pending_suggestions):
                if suggestion.suggestion_id == suggestion_id:
                    suggestion.status = SuggestionStatus.REJECTED
                    suggestion.reviewed_at = time.time()
                    suggestion.reviewed_by = reviewer
                    suggestion.result = reason
                    
                    self.pending_suggestions.pop(i)
                    self.applied_suggestions.append(suggestion)
                    self.stats["suggestions_rejected"] += 1
                    
                    self._notify_subscribers("suggestion_rejected", suggestion)
                    return True
        return False
    
    def apply_suggestion(self, suggestion_id: str) -> bool:
        with self._lock:
            for i, suggestion in enumerate(self.pending_suggestions):
                if suggestion.suggestion_id == suggestion_id:
                    if suggestion.status != SuggestionStatus.APPROVED:
                        return False
                    
                    try:
                        suggestion.status = SuggestionStatus.APPLIED
                        suggestion.applied_at = time.time()
                        
                        self.pending_suggestions.pop(i)
                        self.applied_suggestions.append(suggestion)
                        self.stats["suggestions_applied"] += 1
                        
                        self._notify_subscribers("suggestion_applied", suggestion)
                        return True
                    except Exception as e:
                        suggestion.status = SuggestionStatus.FAILED
                        suggestion.result = str(e)
                        logger.error(f"Failed to apply suggestion: {e}")
                        return False
        return False
    
    def create_version(
        self,
        agent_id: str,
        version_number: str,
        strategy_hash: str,
        parameters_hash: str,
        performance_metrics: Dict
    ) -> AgentVersion:
        with self._lock:
            if agent_id in self.active_versions:
                self.active_versions[agent_id].is_active = False
            
            version = AgentVersion(
                version_id=f"ver_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                version_number=version_number,
                strategy_hash=strategy_hash,
                parameters_hash=parameters_hash,
                created_at=time.time(),
                performance_metrics=performance_metrics,
                is_active=True
            )
            
            self.agent_versions[agent_id].append(version)
            self.active_versions[agent_id] = version
            
            return version
    
    def rollback_version(self, agent_id: str) -> Optional[AgentVersion]:
        with self._lock:
            versions = self.agent_versions.get(agent_id, [])
            if len(versions) < 2:
                return None
            
            current = self.active_versions.get(agent_id)
            if current:
                current.is_active = False
            
            for version in reversed(versions[:-1]):
                if version.rollback_available:
                    version.is_active = True
                    self.active_versions[agent_id] = version
                    self.stats["rollbacks_performed"] += 1
                    
                    self._notify_subscribers("version_rollback", {
                        "agent_id": agent_id,
                        "from_version": current.version_number if current else None,
                        "to_version": version.version_number
                    })
                    
                    return version
        
        return None
    
    def get_agent_versions(self, agent_id: str) -> List[AgentVersion]:
        return list(self.agent_versions.get(agent_id, []))
    
    def get_active_version(self, agent_id: str) -> Optional[AgentVersion]:
        return self.active_versions.get(agent_id)
    
    def get_evolution_report(self) -> Dict:
        with self._lock:
            agent_reports = {}
            for agent_id, module in self.meta_cognition_modules.items():
                agent_reports[agent_id] = module.get_performance_report()
            
            return {
                "stats": self.stats.copy(),
                "agents": agent_reports,
                "pending_suggestions": len(self.pending_suggestions),
                "applied_suggestions": len(self.applied_suggestions),
                "total_versions": sum(len(v) for v in self.agent_versions.values())
            }
    
    def subscribe(self, event_type: str, callback: Callable):
        self.subscribers[event_type].append(callback)
    
    def _notify_subscribers(self, event_type: str, data: Any):
        for callback in self.subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in subscriber callback: {e}")


evolution_engine = EvolutionEngine()
