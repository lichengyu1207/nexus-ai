# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 十三重境界集大成总调度器 (Grand Cultivation Orchestrator)
=====================================================================
对应设计文档「智能体修炼体系集大成.md」完整落地。

本模块是整个修炼体系的"大脑"，统一协调13个阶段的训练、验证、流转和监控。
架构：用户输入 → 总调度器 → 13阶段流水线 → 各阶段引擎 → 指标采集 → 验收报告
"""
from __future__ import annotations

import json
import os
import re
import math
import random
import hashlib
import statistics
import threading
import logging
import time
import copy
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Set

logger = logging.getLogger(__name__)


# ==================== 十三重境界定义 ====================


class CultivationStage(Enum):
    QI_REFINING = ("qi_refining", "炼气期", "筑基培元")
    LAW_MASTERY = ("law_mastery", "练法期", "规行矩步")
    TALISMAN = ("talisman_composition", "练符期", "符文成阵")
    ARTIFACT_REFINEMENT = ("artifact_refinement", "练器期", "万法皆器")
    FORMATION_ARRAY = ("formation_array", "练阵法期", "布阵成军")
    DEMON_DEFENSE = ("demon_defense", "练魔期", "心魔外邪")
    BODY_STRENGTHENING = ("body_strengthening", "练体期", "强筋健骨")
    EXTERNAL_QI = ("external_qi", "外化内气期", "气韵外显")
    HEAVEN_EARTH = ("heaven_earth_awareness", "炼天圆地煞期", "天机感应")
    SPIRIT_CULTIVATION = ("spirit_cultivation", "炼精神期", "灵台清明")
    NASCENT_SOUL = ("nascent_soul", "炼元婴期", "元神初显")
    PRIMORDIAL_SPIRIT = ("primordial_spirit", "炼元神期", "道贯天地")
    DAO_NATURAL = ("dao_natural", "炼道法期", "万法归一")

    @classmethod
    def ordered_stages(cls) -> List['CultivationStage']:
        return [cls.QI_REFINING, cls.LAW_MASTERY, cls.TALISMAN, cls.ARTIFACT_REFINEMENT,
                cls.FORMATION_ARRAY, cls.DEMON_DEFENSE, cls.BODY_STRENGTHENING,
                cls.EXTERNAL_QI, cls.HEAVEN_EARTH, cls.SPIRIT_CULTIVATION,
                cls.NASENT_SOUL, cls.PRIMORDIAL_SPIRIT, cls.DAO_NATURAL]

    @property
    def key(self): return self.value[0]
    @property
    def name_cn(self): return self.value[1]
    @property
    def description(self): return self.value[2]


@dataclass
class StageConfig:
    stage: CultivationStage
    enabled: bool = True
    timeout_hours: float = 168.0
    auto_advance: bool = True
    criteria: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class StageProgress:
    stage_key: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_phase: str = "not_started"
    sub_scores: Dict[str, float] = field(default_factory=dict)
    adversarial_results: Dict[str, float] = field(default_factory=dict)
    checkpoint_path: Optional[str] = None
    error_message: Optional[str] = None
    model_snapshot_id: Optional[str] = None


@dataclass
class GrandOrchestratorState:
    orchestrator_id: str
    current_stage_index: int
    stages_progress: Dict[str, StageProgress]
    global_metrics: Dict[str, float]
    total_episodes: int
    started_at: str
    last_updated: str
    paused: bool = False
    completed: bool = False
    overall_score: float = 0.0


# ==================== 指标定义（对应指标大全） ====================


@dataclass
class MetricDefinition:
    metric_id: str
    name: str
    stage_key: str
    unit: str
    target_value: float
    collection_method: str
    description: str
    category: str


class MetricRegistry:
    METRICS = [
        MetricDefinition("m_dialog_accuracy", "单轮对话准确率", "qi_refining", "%", 80.0,
                        "test_set_eval", "正确理解用户意图并给出合理回答的比例", "accuracy"),
        MetricDefinition("m_api_success_rate", "API调用成功率", "qi_refining", "%", 95.0,
                        "log_stats", "所有接口调用返回200的比例", "reliability"),
        MetricDefinition("m_report_integrity", "报告完整性", "qi_refining", "%", 99.0,
                        "auto_check", "报告无严重格式错误、必填字段完整", "quality"),
        MetricDefinition("m_rule_recall", "规则检索准确率", "law_mastery", "%", 95.0,
                        "rule_test_set", "检索到正确规则的比例", "accuracy"),
        MetricDefinition("m_rule_execution", "规则执行准确率", "law_mastery", "%", 95.0,
                        "rule_test_set", "按规则推理给出正确结论的比例", "accuracy"),
        MetricDefinition("m_workflow_correctness", "工作流正确率", "talisman", "%", 90.0,
                        "complex_task_test", "工作流结构与专家定义一致", "accuracy"),
        MetricDefinition("m_tool_discovery_recall", "工具发现召回率", "artifact_refinement", "%", 95.0,
                        "benchmark_test", "推荐工具中包含正确工具的比例", "accuracy"),
        MetricDefinition("m_tool_call_success", "工具调用成功率", "artifact_refinement", "%", 95.0,
                        "call_log_stats", "调用工具成功返回结果比例", "reliability"),
        MetricDefinition("m_tool_learning_speed", "新工具学习速度", "artifact_refinement", "次", 3.0,
                        "new_tool_test", "掌握新工具所需尝试次数(越低越好)", "efficiency"),
        MetricDefinition("m_formation_selection_acc", "阵型选择正确率", "formation_array", "%", 90.0,
                        "task_feature_match", "选择的阵型与专家最优解一致", "accuracy"),
        MetricDefinition("m_fault_recovery_time", "故障恢复时间", "formation_array", "s", 30.0,
                        "chaos_engineering", "从检测到故障到服务恢复的时间", "availability"),
        MetricDefinition("m_service_availability", "服务可用性", "formation_array", "%", 99.9,
                        "monitoring", "给定窗口内服务正常响应比例", "availability"),
        MetricDefinition("m_malicious_defense_rate", "恶意输入防御率", "demon_defense", "%", 99.0,
                        "penetration_test", "成功拦截或安全处理攻击比例", "security"),
        MetricDefinition("m_false_positive_rate", "误报率", "demon_defense", "%", 1.0,
                        "penetration_test", "正常输入被误判为攻击比例", "precision"),
        MetricDefinition("m_value_stability", "价值观稳定性", "demon_defense", "%", 99.9,
                        "value_test_set", "多轮诱导下不输出违规内容比例", "safety"),
        MetricDefinition("m_avg_response_time", "平均响应时间", "body_strengthening", "ms", 200.0,
                        "monitoring", "API请求处理平均耗时", "performance"),
        MetricDefinition("m_p99_response_time", "P99响应时间", "body_strengthening", "ms", 500.0,
                        "monitoring", "99%请求的处理时间", "performance"),
        MetricDefinition("m_cpu_usage", "CPU使用率", "body_strengthening", "%", 70.0,
                        "monitoring", "服务平均CPU占用", "resource"),
        MetricDefinition("m_memory_usage", "内存使用率", "body_strengthening", "%", 80.0,
                        "monitoring", "服务平均内存占用", "resource"),
        MetricDefinition("m_user_satisfaction", "用户满意度", "external_qi", "/5", 4.5,
                        "user_survey", "用户对回复/报告评分(1-5)", "experience"),
        MetricDefinition("m_report_visual_score", "报告视觉评分", "external_qi", "/5", 4.5,
                        "expert_review", "报告美观度专家评分", "quality"),
        MetricDefinition("m_personalization_rate", "个性化覆盖率", "external_qi", "%", 80.0,
                        "log_analysis", "根据用户画像调整输出的比例", "personalization"),
        MetricDefinition("m_env_detection_rate", "环境变化检测率", "heaven_earth", "%", 95.0,
                        "env_simulation", "对政策/价格等变化检测准确率", "adaptation"),
        MetricDefinition("m_strategy_adaptation", "策略调整成功率", "heaven_earth", "%", 90.0,
                        "env_simulation", "环境变化后任务完成率", "adaptation"),
        MetricDefinition("m_emotion_recognition", "情感识别准确率", "spirit_cultivation", "%", 90.0,
                        "emotion_test_set", "正确识别用户情绪比例", "intelligence"),
        MetricDefinition("m_empathy_score", "共情回复满意度", "spirit_cultivation", "/5", 4.5,
                        "user_survey", "用户对共情回应满意度", "experience"),
        MetricDefinition("m_improvement_adoption_rate", "改进建议采纳率", "nascent_soul", "%", 80.0,
                        "log_analysis", "元智能体建议被采纳比例", "self_improvement"),
        MetricDefinition("m_performance_improvement", "性能提升幅度", "nascent_soul", "%", 10.0,
                        "ab_test", "采纳建议后关键指标改善比例", "self_improvement"),
        MetricDefinition("m_cross_domain_accuracy", "跨领域关联准确率", "primordial_spirit", "%", 85.0,
                        "expert_review", "引入其他领域知识正确性", "knowledge"),
        MetricDefinition("m_zero_shot_success", "零样本任务成功率", "primordial_spirit", "%", 70.0,
                        "novel_task_test", "从未见过领域任务成功率", "adaptation"),
        MetricDefinition("m_new_task_adaptation_speed", "新任务适应速度", "dao_natural", "次", 5.0,
                        "meta_learning_test", "适应全新任务所需样本数(越低越好)", "adaptation"),
        MetricDefinition("m_forgetting_rate", "终身学习遗忘率", "dao_natural", "%", 10.0,
                        "continual_benchmark", "学习新任务后旧任务性能下降比例", "learning"),
    ]

    @classmethod
    def get_by_stage(cls, stage_key: str) -> List[MetricDefinition]:
        return [m for m in cls.METRICS if m.stage_key == stage_key]

    @classmethod
    def get_all(cls) -> List[MetricDefinition]:
        return list(cls.METRICS)

    @classmethod
    def get_target(cls, metric_id: str) -> Optional[float]:
        for m in cls.METRICS:
            if m.metric_id == metric_id:
                return m.target_value
        return None


# ==================== 总调度器核心 ====================


class GrandCultivationOrchestrator:
    STAGE_ORDER = [s.key for s in CultivationStage.ordered_stages()]

    def __init__(self):
        self.state: Optional[GrandOrchestratorState] = None
        self._stage_configs: Dict[str, StageConfig] = {}
        self._checkpoints_dir: str = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints")
        self._metrics_collector: MetricsCollector = MetricsCollector()
        self._lock = threading.RLock()
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        defaults = {
            "qi_refining": StageConfig(CultivationStage.QI_REFINING, timeout=168.0,
                                       criteria={"dialogue_accuracy": 80.0, "api_success": 95.0}, dependencies=[]),
            "law_mastery": StageConfig(CultivationStage.LAW_MASTERY, timeout=168.0,
                                      criteria={"rule_recall": 95.0, "rule_execution": 95.0}, dependencies=["qi_refining"]),
            "talisman_composition": StageConfig(CultivationStage.TALISMAN, timeout=168.0,
                                              criteria={"workflow_correctness": 90.0, "skill_call_success": 95.0},
                                              dependencies=["law_mastery"]),
            "artifact_refinement": StageConfig(CultivationStage.ARTIFACT_REFINEMENT, timeout=240.0,
                                               criteria={"tool_discovery_recall": 95.0, "tool_call_success": 95.0,
                                                        "tool_learning_speed": 3.0},
                                               dependencies=["talisman_composition"]),
            "formation_array": StageConfig(CultivationStage.FORMATION_ARRAY, timeout=240.0,
                                          criteria={"formation_selection_acc": 90.0, "fault_recovery_time": 30.0,
                                                    "service_availability": 99.9},
                                          dependencies=["artifact_refinement"]),
            "demon_defense": StageConfig(CultivationStage.DEMON_DEFENSE, timeout=240.0,
                                         criteria={"malicious_defense_rate": 99.0, "false_positive_rate": 1.0,
                                                   "value_stability": 99.9},
                                         dependencies=["formation_array"]),
            "body_strengthening": StageConfig(CultivationStage.BODY_STRENGTHENING, timeout=240.0,
                                             criteria={"avg_response_time": 200.0, "p99_response_time": 500.0,
                                                       "cpu_usage": 70.0, "memory_usage": 80.0},
                                             dependencies=["demon_defense"]),
            "external_qi": StageConfig(CultivationStage.EXTERNAL_QI, timeout=240.0,
                                     criteria={"user_satisfaction": 4.5, "report_visual_score": 4.5,
                                                "personalization_rate": 80.0},
                                     dependencies=["body_strengthening"]),
            "heaven_earth_awareness": StageConfig(CultivationStage.HEAVEN_EARTH, timeout=300.0,
                                                  criteria={"env_detection_rate": 95.0, "strategy_adaptation": 90.0},
                                                  dependencies=["external_qi"]),
            "spirit_cultivation": StageConfig(CultivationStage.SPIRIT_CULTIVATION, timeout=300.0,
                                            criteria={"emotion_recognition": 90.0, "empathy_score": 4.5},
                                            dependencies=["heaven_earth_awareness"]),
            "nascent_soul": StageConfig(CultivationStage.NASENT_SOUL, timeout=300.0,
                                        criteria={"improvement_adoption_rate": 80.0, "performance_improvement": 10.0},
                                        dependencies=["spirit_cultivation"]),
            "primordial_spirit": StageConfig(CultivationStage.PRIMORDIAL_SPIRIT, timeout=480.0,
                                              criteria={"cross_domain_accuracy": 85.0, "zero_shot_success": 70.0},
                                              dependencies=["nascent_soul"]),
            "dao_natural": StageConfig(CultivationStage.DAO_NATURAL, timeout=720.0,
                                       criteria={"new_task_adaptation_speed": 5.0, "forgetting_rate": 10.0},
                                       dependencies=["primordial_spirit"]),
        }
        self._stage_configs = defaults

    def initialize(self) -> GrandOrchestratorState:
        with self._lock:
            if self.state and not self.state.completed:
                return self.state
            progress = {}
            for stage in CultivationStage.ordered_stages():
                progress[stage.key] = StageProgress(
                    stage_key=stage.key, status="not_started",
                    current_phase="waiting_for_dependencies",
                    sub_scores={}, adversarial_results={},
                )
            self.state = GrandOrchestratorState(
                orchestrator_id=f"orch_{uuid.uuid4().hex[:12]}",
                current_stage_index=0, stages_progress=progress,
                global_metrics={}, total_episodes=0,
                started_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )
            logger.info(f"[总调度器] 初始化完成，共{len(progress)}个阶段")
            return self.state

    def start_next_stage(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self.state:
                self.initialize()
            if self.state.paused or self.state.completed:
                return None
            idx = self.state.current_stage_index
            if idx >= len(self.STAGE_ORDER):
                self.state.completed = True
                self.state.last_updated = datetime.now().isoformat()
                self._calculate_overall_score()
                return {"status": "all_stages_completed", "overall_score": self.state.overall_score}
            stage_key = self.STAGE_ORDER[idx]
            config = self._stage_configs.get(stage_key)
            if not config or not config.enabled:
                return self._advance_stage()
            progress = self.state.stages_progress[stage_key]
            deps_met = all(
                self.state.stages_progress.get(d, StageProgress(stage_key=d)).status == "completed"
                for d in (config.dependencies or [])
            )
            if not deps_met:
                return {"status": "waiting_dependencies", "stage": stage_key,
                       "missing": [d for d in (config.dependencies or [])
                               if self.state.stages_progress.get(d, StageProgress(stage_key=d)).status != "completed"]}
            progress.status = "in_progress"
            progress.started_at = datetime.now().isoformat()
            progress.current_phase = "training"
            self.state.last_updated = datetime.now().isoformat()
            stage_enum = next((s for s in CultivationStage if s.key == stage_key), None)
            return {
                "action": "stage_started", "stage_key": stage_key,
                "stage_name": stage_enum.name_cn if stage_enum else stage_key,
                "config": {"timeout_h": config.timeout_hours, "criteria": config.criteria},
                "index": idx, "total": len(self.STAGE_ORDER),
            }

    def complete_current_stage(self, results: Dict[str, Any]) -> Optional[Dict]:
        with self._lock:
            if not self.state:
                return None
            idx = self.state.current_stage_index
            if idx >= len(self.STAGE_ORDER):
                return None
            stage_key = self.STAGE_ORDER[idx]
            progress = self.state.stages_progress[stage_key]
            progress.status = "completed"
            progress.completed_at = datetime.now().isoformat()
            progress.sub_scores.update(results.get("sub_scores", {}))
            progress.adversarial_results.update(results.get("adversarial", {}))
            self._save_checkpoint(stage_key)
            self._collect_stage_metrics(stage_key, results)
            self.state.total_episodes += 1
            self.state.last_updated = datetime.now().isoformat()
            return self._advance_stage()

    def _advance_stage(self) -> Optional[Dict]:
        self.state.current_stage_index += 1
        if self.state.current_stage_index >= len(self.STAGE_ORDER):
            self.state.completed = True
            self._calculate_overall_score()
            return {"status": "cultivation_complete", "overall_score": self.state.overall_score}
        next_key = self.STAGE_ORDER[self.state.current_stage_index]
        return {"status": "advanced", "next_stage": next_key,
               "index": self.state.current_stage_index}

    def pause(self):
        if self.state:
            self.state.paused = True
            self.state.last_updated = datetime.now().isoformat()

    def resume(self):
        if self.state:
            self.state.paused = False
            self.state.last_updated = datetime.now().isoformat()

    def _save_checkpoint(self, stage_key: str):
        os.makedirs(self._checkpoints_dir, exist_ok=True)
        cp_data = {
            "orchestrator_id": self.state.orchestrator_id if self.state else "",
            "stage_key": stage_key,
            "progress": asdict(self.state.stages_progress.get(stage_key, StageProgress(stage_key))),
            "global_metrics": self.state.global_metrics,
            "timestamp": datetime.now().isoformat(),
        }
        cp_path = os.path.join(self._checkpoints_dir, f"cp_{stage_key}_{int(time.time())}.json")
        with open(cp_path, "w", encoding="utf-8") as f:
            json.dump(cp_data, f, ensure_ascii=False, indent=2, default=str)

    def load_checkpoint(self, checkpoint_path: str) -> bool:
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                cp_data = json.load(f)
            if not self.state:
                self.initialize()
            stage_key = cp_data["stage_key"]
            if stage_key in self.state.stages_progress:
                sp = StageProgress(**cp_data["progress"])
                self.state.stages_progress[stage_key] = sp
            self.state.global_metrics.update(cp_data.get("global_metrics", {}))
            idx = self.STAGE_ORDER.index(stage_key) if stage_key in self.STAGE_ORDER else 0
            self.state.current_stage_index = idx + 1
            return True
        except Exception as e:
            logger.error(f"[总调度器] 加载检查点失败: {e}")
            return False

    def _collect_stage_metrics(self, stage_key: str, results: Dict[str, Any]):
        for metric_key, value in results.get("sub_scores", {}).items():
            full_metric_id = f"m_{metric_key}" if not metric_key.startswith("m_") else metric_key
            self.state.global_metrics[full_metric_id] = value
            self._metrics_collector.record(full_metric_id, value, stage_key)

    def _calculate_overall_score(self):
        if not self.state:
            return
        scores = []
        for stage_key, progress in self.state.stages_progress.items():
            if progress.sub_scores:
                avg = statistics.mean(progress.sub_scores.values())
                weights = {sk: 1.0 for sk in progress.sub_scores}
                weighted = sum(v * weights.get(sk, 1.0) for sk, v in progress.sub_scores.items())
                total_w = sum(weights.values()) if weights else 1
                stage_score = weighted / max(total_w, 1)
                scores.append(stage_score)
        self.state.overall_score = round(statistics.mean(scores), 4) if scores else 0.0

    def get_status_report(self) -> Dict[str, Any]:
        if not self.state:
            return {"error": "调度器未初始化"}
        stages_info = []
        for i, stage_key in enumerate(self.STAGE_ORDER):
            prog = self.state.stages_progress.get(stage_key)
            stage_enum = next((s for s in CultivationStage if s.key == stage_key), None)
            stages_info.append({
                "index": i, "key": stage_key, "name": stage_enum.name_cn if stage_enum else stage_key,
                "status": prog.status if prog else "unknown",
                "current": i == self.state.current_stage_index,
                "scores": dict(prog.sub_scores) if prog else {},
            })
        return {
            "orchestrator_id": self.state.orchestrator_id,
            "current_stage": self.STAGE_ORDER[self.state.current_stage_index] if self.state.current_stage_index < len(self.STAGE_ORDER) else "completed",
            "paused": self.state.paused, "completed": self.state.completed,
            "overall_score": self.state.overall_score,
            "total_episodes": self.state.total_episodes,
            "stages": stages_info,
            "started_at": self.state.started_at,
            "last_updated": self.state.last_updated,
        }


class MetricsCollector:
    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(self, metric_id: str, value: float, stage_key: str,
              tags: Optional[Dict[str, str]] = None):
        self._records.append({
            "metric_id": metric_id, "value": round(value, 6),
            "stage_key": stage_key, "tags": tags or {},
            "timestamp": datetime.now().isoformat(),
        })

    def query(self, metric_ids: Optional[List[str]] = None,
              stage_keys: Optional[List[str]] = None,
              limit: int = 100) -> List[Dict]:
        records = self._records[-limit:] if limit else list(self._records)
        if metric_ids:
            records = [r for r in records if r["metric_id"] in metric_ids]
        if stage_keys:
            records = [r for r in records if r["stage_key"] in stage_keys]
        return sorted(records, key=lambda x: x["timestamp"], reverse=True)

    def get_summary(self) -> Dict[str, Any]:
        by_metric = defaultdict(list)
        by_stage = defaultdict(list)
        for r in self._records:
            by_metric[r["metric_id"]].append(r["value"])
            by_stage[r["stage_key"]].append(r["value"])
        summary = {"total_records": len(self._records)}
        summary["by_metric"] = {mid: {"count": len(vals), "latest": vals[-1], "avg": round(statistics.mean(vals), 4),
                                   "target": MetricRegistry.get_target(mid)} for mid, vals in by_metric.items()}
        summary["by_stage"] = {sk: {"count": len(vals), "avg": round(statistics.mean(vals), 4)}
                             for sk, vals in by_stage.items()}
        return summary


# 全局实例
grand_orchestrator = GrandCultivationOrchestrator()
metrics_collector = MetricsCollector()
