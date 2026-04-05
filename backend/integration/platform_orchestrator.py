# -*- coding: utf-8 -*-
"""
房都督AI平台 - 统一总调度器 (Platform Orchestrator)
=============================================
职责：作为四大体系的统一入口，负责：
1) 按依赖顺序初始化全部子系统（道法自然→自进化→炼丹→修炼）
2) 管理全局生命周期（启动/暂停/恢复/停止/健康检查）
3) 提供跨体系协调接口（数据流路由、事件总线桥接、统一状态查询）
4) 集成监控仪表盘，汇聚所有子系统的运行指标

体系层级关系:
  Layer-0: PlatformOrchestrator (本模块) — 总控台
  Layer-1: 道法自然(B) — 三省六部治理 + 人格融合 + 记忆增强 + 可解释性
  Layer-2: 自进化(C) — 数据生成 → 验证修复 → 闭环进化(PPO+元策略)
  Layer-3: 炼丹(D) — 炼丹炉(成功标准) → 红蓝对抗 → 城市模拟 → 混沌测试
  Layer-4: 修炼(E) — 炼气→练法→练符→天圆地煞→精神→元婴→元神→道法
"""

from __future__ import annotations

import json
import time
import logging
import threading
import traceback
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemLayer(Enum):
    GOVERNANCE = "道法自然"
    SELF_EVOLUTION = "自进化系统"
    ALCHEMY = "炼丹系统"
    CULTIVATION = "修炼体系"


class PlatformState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class SubsystemStatus:
    layer: SystemLayer
    name: str
    initialized: bool = False
    running: bool = False
    healthy: bool = True
    startup_time: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformHealthReport:
    state: PlatformState
    timestamp: str
    uptime_seconds: float = 0.0
    subsystems: List[SubsystemStatus] = field(default_factory=list)
    total_metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, str]] = field(default_factory=list)


class PlatformOrchestrator:
    """
    平台总调度器 — 四大体系的统一管理中枢
    
    初始化顺序（按依赖关系）:
    1. 道法自然(B): 治理基座 → 调度器 → 记忆增强 → 人格引擎 → 可解释性
    2. 自进化(C): 数据生成器 → 验证修复器 → PPO智能体 → 元策略网络 → 可视化看板
    3. 炼丹(D): 炼丹炉核心 → 五层架构 → 版本管理 → 对抗环境 → PER缓冲 → 分布式训练
    4. 修炼(E): 8阶段实例 → 进度仪表盘 → 自动迭代引擎 → E2E测试 → 部署配置
    
    数据流向:
    自进化(C) --生成训练数据--> 炼丹(D) --驱动--> 修炼(E) 各阶段
    修炼(E) --进度/指标--> 道法自然(B) --调度决策--> 全局资源分配
    所有体系 --告警/指标--> 总调度器 --> 统一监控面板
    """

    _instance: Optional['PlatformOrchestrator'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._state = PlatformState.UNINITIALIZED
        self._start_time: Optional[float] = None
        self._subsystems: Dict[SystemLayer, SubsystemStatus] = {}
        self._event_callbacks: List[Callable] = []
        self._lock = threading.RLock()
        self._init_order = [
            SystemLayer.GOVERNANCE,
            SystemLayer.SELF_EVOLUTION,
            SystemLayer.ALCHEMY,
            SystemLayer.CULTIVATION,
        ]
        self._initialized = True

    @property
    def state(self) -> PlatformState:
        return self._state

    def register_event_callback(self, callback: Callable[[str, Dict], None]):
        with self._lock:
            self._event_callbacks.append(callback)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        payload = {"event": event_type, "timestamp": datetime.now().isoformat(), **data}
        for cb in self._event_callbacks:
            try:
                cb(event_type, payload)
            except Exception:
                pass

    def initialize_all(self, skip_errors: bool = True) -> PlatformHealthReport:
        with self._lock:
            self._state = PlatformState.INITIALIZING
            self._emit_event("platform_initializing", {"skip_errors": skip_errors})
        
        results = []
        for layer in self._init_order:
            status = self._initialize_subsystem(layer)
            results.append(status)
            if not status.initialized and not skip_errors:
                self._state = PlatformState.ERROR
                logger.error(f"[总调度] 子系统 {layer.value} 初始化失败，中止")
                break
        
        all_ok = all(s.initialized for s in results)
        self._state = PlatformState.STARTING if all_ok else PlatformState.DEGRADED
        report = self.get_health_report()
        logger.info(f"[总调度] 初始化完成 | 状态={self._state.value} | 成功={sum(1 for s in results if s.initialized)}/{len(results)}")
        return report

    def _initialize_subsystem(self, layer: SystemLayer) -> SubsystemStatus:
        status = SubsystemStatus(layer=layer, name=layer.value)
        try:
            if layer == SystemLayer.GOVERNANCE:
                self._init_governance(status)
            elif layer == SystemLayer.SELF_EVOLUTION:
                self._init_self_evolution(status)
            elif layer == SystemLayer.ALCHEMY:
                self._init_alchemy(status)
            elif layer == SystemLayer.CULTIVATION:
                self._init_cultivation(status)
            status.initialized = True
            status.running = True
            status.startup_time = datetime.now().isoformat()
            logger.info(f"[总调度] ✓ {layer.value} 初始化成功")
        except Exception as e:
            status.initialized = False
            status.healthy = False
            status.error_message = f"{type(e).__name__}: {str(e)[:200]}"
            logger.error(f"[总调度] ✗ {layer.value} 初始化失败: {e}")
        self._subsystems[layer] = status
        return status

    def _init_governance(self, status: SubsystemStatus):
        from backend.governance.dao_fa_zi_ran import dynamic_team_orchestrator
        from backend.governance.enhanced_scheduler import enhanced_scheduler
        from backend.personality.personality_fusion import personality_engine
        from backend.memory.enhanced_retrieval import enhanced_retrieval
        from backend.reporting.explainability_engine import explainability_engine
        from backend.integration_hub import integration_hub
        status.metrics["dynamic_team"] = "loaded"
        status.metrics["enhanced_scheduler"] = "loaded"
        status.metrics["personality_engine"] = "loaded"
        status.metrics["enhanced_retrieval"] = "loaded"
        status.metrics["explainability"] = "loaded"
        status.metrics["integration_hub"] = "loaded"

    def _init_self_evolution(self, status: SubsystemStatus):
        from backend.self_evolution.data_generator import historical_data_generator
        from backend.self_evolution.validator_repair import multi_dimension_validator
        from backend.self_evolution.closed_loop_evolution import (
            ppo_data_agent, meta_strategy_network,
            evolution_visualizer, real_time_dashboard, root_cause_analyzer,
        )
        status.metrics["data_generator"] = "loaded"
        status.metrics["validator"] = "loaded"
        status.metrics["ppo_agent"] = "loaded"
        status.metrics["meta_strategy"] = "loaded"
        status.metrics["visualizer"] = "loaded"
        status.metrics["dashboard"] = "loaded"
        status.metrics["root_cause_analyzer"] = "loaded"

    def _init_alchemy(self, status: SubsystemStatus):
        from backend.alchemy.alchemy_core import alchemy_furnace, layered_architecture, model_version_manager
        from backend.alchemy.self_play_engine import adversarial_env, self_play_orchestrator, per_buffer, distributed_trainer
        from backend.alchemy.city_simulator_optimizer import city_simulator, auto_performance_tuner, alert_notifier
        from backend.alchemy.stability_testing import chaos_engineer, stress_tester
        status.metrics["furnace"] = "loaded"
        status.metrics["architecture"] = "loaded"
        status.metrics["version_mgr"] = "loaded"
        status.metrics["adversarial_env"] = "loaded"
        status.metrics["self_play"] = "loaded"
        status.metrics["per_buffer"] = "loaded"
        status.metrics["distributed"] = "loaded"
        status.metrics["city_simulator"] = "loaded"
        status.metrics["perf_tuner"] = "loaded"
        status.metrics["alert_notifier"] = "loaded"
        status.metrics["chaos_engineer"] = "loaded"
        status.metrics["stress_tester"] = "loaded"

    def _init_cultivation(self, status: SubsystemStatus):
        from backend.cultivation.cultivation_foundations import (
            qi_refining, law_mastery, talisman_composition, heaven_earth,
        )
        from backend.cultivation.cultivation_advanced import (
            spirit, nascent_soul, primordial_spirit, dao_natural,
        )
        from backend.cultivation.cultivation_integration import (
            cultivation_dashboard, auto_iteration_engine, e2e_cultivation_test, deployment_generator,
        )
        stage_names = ["qi_refining", "law_mastery", "talisman_composition", "heaven_earth",
                        "spirit", "nascent_soul", "primordial_spirit", "dao_natural"]
        for sn in stage_names:
            cultivation_dashboard.register_stage(
                {"qi_refining": "炼气期", "law_mastery": "练法期", "talisman_composition": "练符期",
                 "heaven_earth": "天圆地煞期", "spirit": "精神期", "nascent_soul": "元婴期",
                 "primordial_spirit": "元神期", "dao_natural": "道法期"}.get(sn, sn),
                locals().get(sn)
            )
        status.metrics["stages_loaded"] = len(stage_names)
        status.metrics["dashboard"] = "active"
        status.metrics["auto_iteration"] = "ready"
        status.metrics["e2e_test"] = "ready"
        status.metrics["deployment_gen"] = "ready"

    def start_platform(self) -> PlatformHealthReport:
        with self._lock:
            self._state = PlatformState.STARTING
            self._start_time = time.time()
        self._emit_event("platform_starting", {})
        for layer, status in self._subsystems.items():
            if status.initialized:
                status.running = True
        self._state = PlatformState.RUNNING
        self._emit_event("platform_started", {"uptime": 0})
        return self.get_health_report()

    def pause_platform(self):
        with self._lock:
            self._state = PlatformState.PAUSED
        self._emit_event("platform_paused", {})

    def resume_platform(self):
        with self._lock:
            if self._state == PlatformState.PAUSED:
                self._state = PlatformState.RUNNING
        self._emit_event("platform_resumed", {})

    def stop_platform(self):
        with self._lock:
            self._state = PlatformState.STOPPING
        for layer, status in self._subsystems.items():
            status.running = False
        self._state = PlatformState.STOPPED
        self._emit_event("platform_stopped", {"uptime": time.time() - (self._start_time or 0)})

    def get_health_report(self) -> PlatformHealthReport:
        uptime = (time.time() - self._start_time) if self._start_time else 0.0
        alerts = []
        for layer, status in self._subsystems.items():
            if not status.healthy:
                alerts.append({"layer": layer.value, "issue": status.error_message or "unhealthy"})
            if not status.running and status.initialized:
                alerts.append({"layer": layer.value, "issue": "not_running"})
        total_metrics = {
            "total_subsystems": len(self._subsystems),
            "healthy_count": sum(1 for s in self._subsystems.values() if s.healthy),
            "running_count": sum(1 for s in self._subsystems.values() if s.running),
            "uptime_seconds": round(uptime, 1),
        }
        return PlatformHealthReport(
            state=self._state,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime,
            subsystems=list(self._subsystems.values()),
            total_metrics=total_metrics,
            alerts=alerts,
        )

    def get_system_status_dict(self) -> Dict[str, Any]:
        report = self.get_health_report()
        return {
            "platform_state": report.state.value,
            "timestamp": report.timestamp,
            "uptime_seconds": report.uptime_seconds,
            "subsystems": {s.layer.value: {"name": s.name, "initialized": s.initialized,
                                           "running": s.running, "healthy": s.healthy,
                                           "error": s.error_message} for s in report.subsystems},
            "alerts": report.alerts,
            "metrics": report.total_metrics,
        }

    def run_full_integration_cycle(self) -> Dict[str, Any]:
        cycle_start = time.time()
        results = {
            "cycle_id": f"integ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started_at": datetime.now().isoformat(),
            "phases": [],
        }
        try:
            from backend.integration.evolution_cultivation_bridge import evolution_cultivation_bridge
            phase1 = evolution_cultivation_bridge.inject_training_data_to_all_stages(sample_count=50)
            results["phases"].append({"phase": "数据注入", "status": "ok" if phase1.get("success") else "fail", "detail": phase1})

            from backend.integration.cultivation_alchemy_bridge import cultivation_alchemy_bridge
            phase2 = cultivation_alchemy_bridge.run_furnace_driven_evolution(max_iterations=3)
            results["phases"].append({"phase": "炼丹驱动修炼", "status": "ok" if phase2.get("success") else "fail", "detail": phase2})

            from backend.integration.governance_integration_bridge import governance_integration_bridge
            phase3 = governance_integration_bridge.coordinate_all_systems()
            results["phases"].append({"phase": "三省六部统筹", "status": "ok" if phase3.get("success") else "fail", "detail": phase3})

            health = self.get_health_report()
            results["final_health"] = health.state.value
            results["success"] = health.state == PlatformState.RUNNING
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            logger.error(f"[总调度] 集成循环异常: {traceback.format_exc()}")
        results["duration_seconds"] = round(time.time() - cycle_start, 2)
        results["completed_at"] = datetime.now().isoformat()
        self._emit_event("integration_cycle_complete", results)
        return results


platform_orchestrator = PlatformOrchestrator()
