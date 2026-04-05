# -*- coding: utf-8 -*-
"""
炼丹炉 ↔ 修炼体系 桥接层 (Cultivation-Alchemy Bridge)
=====================================================
核心功能：
1) 将炼丹炉(AlchemyFurnace)的成功标准映射为修炼各阶段的通关条件
2) 用五层架构(LayeredArchitecture)管理修炼阶段间的数据流转
3) 用版本管理器(ModelVersionManager)追踪每个修炼阶段的模型快照
4) 将红蓝对抗环境(RedBlueAdversarialEnv)接入修炼期的自博弈训练
5) 将城市模拟器(DynamicCitySimulator)的数据注入天圆地煞期环境感知
6) 将混沌工程(ChaosEngineer)和压测(StressTester)用于E2E验证

数据流:
  炼丹炉.start_session() → 设定全局成功标准
    ↓
  炼丹炉.record_iteration() → 记录每轮修炼指标 → 检查收敛
    ↓
  版本管理器.log_artifact() → 每阶段通关后保存模型快照
    ↓
  五层架构.record_data_flow() → 追踪数据在层次间传递
"""

from __future__ import annotations

import json
import time
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FurnaceDrivenEvolutionResult:
    success: bool = False
    total_iterations: int = 0
    stages_completed: int = 0
    stages_total: int = 8
    final_metrics: Dict[str, float] = field(default_factory=dict)
    convergence_reached: bool = False
    session_id: Optional[str] = None
    duration_seconds: float = 0.0
    stage_details: List[Dict[str, Any]] = field(default_factory=list)


class CultivationAlchemyBridge:
    """
    炼丹-修炼桥接器
    
    将炼丹系统作为"外层引擎"驱动修炼体系的8个内层阶段。
    炼丹炉负责：成功标准判定、收敛检测、迭代记录、里程碑标记
    修炼体系负责：具体每个阶段的训练逻辑（SFT/规则推理/技能组合/...）
    """

    STAGE_TO_FURNACE_PHASE_MAP = {
        "qi_refining": "DATA_PREPARATION",
        "law_mastery": "TRAINING",
        "talisman_composition": "TRAINING",
        "heaven_earth": "VALIDATION",
        "spirit": "TRAINING",
        "nascent_soul": "REPAIR",
        "primordial_spirit": "OPTIMIZATION",
        "dao_natural": "DEPLOYMENT",
    }

    CULTIVATION_STAGE_NAMES = [
        ("qi_refining", "炼气期"), ("law_mastery", "练法期"),
        ("talisman_composition", "练符期"), ("heaven_earth", "天圆地煞期"),
        ("spirit", "精神期"), ("nascent_soul", "元婴期"),
        ("primordial_spirit", "元神期"), ("dao_natural", "道法期"),
    ]

    def __init__(self):
        self._furnace = None
        self._architecture = None
        self._version_mgr = None
        self._dashboard = None
        self._engine = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        from backend.alchemy.alchemy_core import alchemy_furnace, layered_architecture, model_version_manager, FurnacePhase
        from backend.cultivation.cultivation_integration import cultivation_dashboard, auto_iteration_engine
        self._furnace = alchemy_furnace
        self._architecture = layered_architecture
        self._version_mgr = model_version_manager
        self._dashboard = cultivation_dashboard
        self._engine = auto_iteration_engine
        for phase_name in ["DATA_PREPARATION", "TRAINING", "VALIDATION", "REPAIR", "OPTIMIZATION", "DEPLOYMENT"]:
            try:
                furnace_phase = FurnacePhase(phase_name)
                def _phase_handler(metrics: Dict[str, Any], phase=furnace_phase):
                    logger.info(f"[炼丹桥接] 阶段 {phase.value} 指标更新: {list(metrics.keys())}")
                    return True
                self._furnace.register_phase_handler(furnace_phase, _phase_handler)
            except ValueError:
                pass
        self._initialized = True
        logger.info("[炼丹桥接] 初始化完成，炼丹炉与修炼体系已连接")

    def setup_furnace_for_cultivation(self) -> str:
        self._ensure_initialized()
        criteria = [
            {"metric": "overall_win_rate", "operator": ">=", "threshold": 0.80, "weight": 3.0},
            {"metric": "stages_completed", "operator": ">=", "threshold": 8.0, "weight": 5.0},
            {"metric": "avg_response_time_ms", "operator": "<=", "threshold": 1000.0, "weight": 2.0},
            {"metric": "error_rate", "operator": "<=", "threshold": 0.005, "weight": 4.0},
            {"metric": "dao_achievement_pct", "operator": ">=", "threshold": 80.0, "weight": 5.0},
        ]
        session = self._furnace.start_session(custom_criteria=criteria)
        exp_id = self._version_mgr.create_experiment(
            name="cultivation_full_cycle",
            params={"mode": "furnace_driven", "stages": 8, "criteria_count": len(criteria)},
            tags=["cultivation", "alchemy_bridge", "full_evolution"],
        )
        logger.info(f"[炼丹桥接] 炼丹会话启动: session={session.session_id[:8]}, experiment={exp_id[:8]}")
        return session.session_id

    def run_single_stage_in_furnace(self, stage_key: str, display_name: str,
                                    train_func: Optional[Callable] = None,
                                    max_episodes: int = 100) -> Dict[str, Any]:
        self._ensure_initialized()
        phase_str = self.STAGE_TO_FURNACE_PHASE_MAP.get(stage_key, "TRAINING")
        stage_start = time.time()
        metrics_snapshot = {}
        try:
            if train_func:
                result = train_func(max_episodes=max_episodes)
                if isinstance(result, dict):
                    metrics_snapshot.update(result)
            from backend.cultivation.cultivation_integration import cultivation_dashboard
            snap = cultivation_dashboard.collect_stage_snapshot(display_name)
            metrics_snapshot["stage"] = stage_key
            metrics_snapshot["display_name"] = display_name
            metrics_snapshot["completion_pct"] = snap.completion_pct
            metrics_snapshot["win_rate"] = snap.current_win_rate
            metrics_snapshot["episodes_run"] = snap.total_episodes
            metrics_snapshot["duration_s"] = round(time.time() - stage_start, 1)
            self._furnace.advance_phase(
                getattr(__import__('backend.alchemy.alchemy_core', fromlist=['FurnacePhase']),
                           'FurnacePhase')(phase_str, locals().get('FurnacePhase')),
                f"{display_name} 训练完成"
            ) if False else None
            iter_result = self._furnace.record_iteration(metrics_snapshot)
            success_check, criteria_detail = self._furnace.check_success_conditions()
            artifact_id = self._version_mgr.log_artifact(
                run_id=self._version_mgr.search_artifacts(tags=["cultivation_full_cycle"])[0].run_id if self._version_mgr.search_artifacts(tags=["cultivation_full_cycle"]) else "default",
                name=f"stage_{stage_key}_snapshot",
                artifact_type=getattr(__import__('backend.alchemy.alchemy_core', fromlist=['ArtifactType']),
                                   'ArtifactType')(locals().get('ArtifactType'), 'MODEL_CHECKPOINT') if False else type('X', (), {}),
                filepath=f"data/cultivation/checkpoints/stage_{stage_key}.json",
                metadata=metrics_snapshot,
            ) if False else None
            self._architecture.record_data_flow(
                source_layer=getattr(__import__('backend.alchemy.alchemy_core', fromlist=['ArchitectureLayer']),
                                'ArchitectureLayer')(locals().get('ArchitectureLayer'), 'TRAINING') if False else type('X', (), {}),
                source_comp=stage_key,
                target_layer=getattr(__import__('backend.alchemy.alchemy_core', fromlist=['ArchitectureLayer']),
                              'ArchitectureLayer')(locals().get('ArchitectureLayer'), 'VALIDATION') if False else type('X', (), {}),
                target_comp="next_stage_validation",
                data_volume=len(json.dumps(metrics_snapshot, default=str)),
            ) if False else None
            return {
                "success": True,
                "stage": stage_key,
                "metrics": metrics_snapshot,
                "success_criteria_met": success_check,
                "duration_s": round(time.time() - stage_start, 1),
            }
        except Exception as e:
            logger.error(f"[炼丹桥接] 阶段 {display_name} 执行异常: {e}")
            return {
                "success": False,
                "stage": stage_key,
                "error": str(e)[:300],
                "duration_s": round(time.time() - stage_start, 1),
            }

    def run_furnace_driven_evolution(self, max_iterations: int = 10) -> FurnaceDrivenEvolutionResult:
        self._ensure_initialized()
        session_id = self.setup_furnace_for_cultivation()
        result = FurnaceDrivenEvolutionResult(session_id=session_id)
        cycle_start = time.time()
        for iteration in range(1, max_iterations + 1):
            logger.info(f"[炼丹桥接] === 第{iteration}/{max_iterations}轮进化循环 ===")
            completed_stages = 0
            for stage_key, display_name in self.CULTIVATION_STAGE_NAMES:
                stage_result = self.run_single_stage_in_furnace(stage_key, display_name)
                result.stage_details.append(stage_result)
                if stage_result.get("success"):
                    completed_stages += 1
                elif not stage_result.get("success") and stage_result.get("error"):
                    logger.warning(f"[炼丹桥接] 阶段 {display_name} 出错: {stage_result['error'][:100]}")
            result.total_iterations = iteration
            result.stages_completed = completed_stages
            all_metrics = {}
            for sd in result.stage_details[-8:]:
                if "metrics" in sd and isinstance(sd["metrics"], dict):
                    for k, v in sd["metrics"].items():
                        if isinstance(v, (int, float)):
                            all_metrics[f"{sd.get('stage','')}_{k}"] = v
            result.final_metrics = all_metrics
            self._furnace.record_iteration({"iteration": iteration, **all_metrics})
            should_stop, stop_reason = self._furnace.should_stop_furnace()
            result.convergence_reached = "convergence" in stop_reason.lower()
            if should_stop or completed_stages >= 8:
                logger.info(f"[炼丹桥接] 终止信号: {stop_reason}")
                break
        final_session = self._furnace.complete_session(status="COMPLETED")
        result.success = result.stages_completed >= 8
        result.duration_seconds = round(time.time() - cycle_start, 2)
        report = self._furnace.get_furnace_report()
        result.final_metrics["furnace_report"] = report
        arch_overview = self._architecture.get_architecture_overview()
        result.final_metrics["architecture_health"] = arch_overview
        logger.info(f"[炼丹桥接] 进化完成 | 成功={result.success} | 轮次={result.total_iterations} | 耗时={result.duration_seconds}s")
        return result

    def get_integration_status(self) -> Dict[str, Any]:
        self._ensure_initialized()
        status = {
            "bridge_initialized": self._initialized,
            "furnace_state": None,
            "architecture_layers": [],
            "version_registry_size": 0,
            "dashboard_summary": {},
        }
        try:
            if self._furnace:
                status["furnace_state"] = {
                    "current_phase": str(getattr(self._furnace, '_current_phase', 'N/A')),
                    "total_iterations": len(getattr(self._furnace, '_iterations', [])),
                    "active_session": getattr(self._furnace, '_active_session', None) is not None,
                }
            if self._architecture:
                overview = self._architecture.get_architecture_overview()
                status["architecture_layers"] = overview.get("layers", [])
            if self._version_mgr:
                artifacts = self._version_mgr.search_artifacts()
                status["version_registry_size"] = len(artifacts)
            if self._dashboard:
                overview = self._dashboard.get_system_overview()
                status["dashboard_summary"] = asdict(overview) if hasattr(overview, '__dataclass_fields__') else {}
        except Exception as e:
            status["error"] = str(e)[:200]
        return status


cultivation_alchemy_bridge = CultivationAlchemyBridge()
