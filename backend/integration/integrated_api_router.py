# -*- coding: utf-8 -*-
"""
房都督AI平台 - 集成API路由 (Integrated API Router)
==================================================
将四大体系（道法自然/自进化/炼丹/修炼）的所有能力通过统一REST API暴露，
支持前端调用、外部系统集成、自动化测试。

路由结构:
  /api/integration/
    ├── /health              — 平台健康检查（全部子系统状态）
    ├── /initialize          — 初始化全部子系统
    ├── /start               — 启动平台
    ├── /stop                — 停止平台
    ├── /status              — 详细状态查询
    │
    ├── /governance/
    │   └── /coordinate      — 三省六部任务协调
    │
    ├── /evolution/
    │   └── /inject-data     — 自进化数据注入修炼
    │
    ├── /alchemy/
    │   └── /drive-evolution — 炼丹炉驱动修炼进化
    │
    ├── /cultivation/
    │   ├── /dashboard       — 修炼进度仪表盘数据
    │   ├── /run-engine      — 启动自动迭代引擎
    │   └── /e2e-test        — 运行端到端测试
    │
    └── /full-cycle          — 完整集成循环（一键跑通）
"""

from __future__ import annotations

import json
import time
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration", tags=["集成平台"])


@router.get("/health")
async def get_platform_health():
    from backend.integration.platform_orchestrator import platform_orchestrator
    report = platform_orchestrator.get_health_report()
    return {
        "platform_state": report.state.value,
        "timestamp": report.timestamp,
        "uptime_seconds": round(report.uptime_seconds, 1),
        "subsystems_count": len(report.subsystems),
        "healthy_count": sum(1 for s in report.subsystems if s.healthy),
        "alerts_count": len(report.alerts),
        "alerts": report.alerts[:5],
    }


@router.post("/initialize")
async def initialize_platform(skip_errors: bool = Query(True, description="跳过初始化失败的子系统")):
    from backend.integration.platform_orchestrator import platform_orchestrator
    try:
        report = platform_orchestrator.initialize_all(skip_errors=skip_errors)
        return {"success": True, "state": report.state.value, "subsystems_initialized": len(report.subsystems)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_platform():
    from backend.integration.platform_orchestrator import platform_orchestrator
    try:
        report = platform_orchestrator.start_platform()
        return {"success": True, "state": report.state.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_platform():
    from backend.integration.platform_orchestrator import platform_orchestrator
    platform_orchestrator.stop_platform()
    return {"success": True, "state": platform_orchestrator.state.value}


@router.get("/status")
async def get_detailed_status():
    from backend.integration.platform_orchestrator import platform_orchestrator
    status = platform_orchestrator.get_system_status_dict()
    return status


@router.post("/governance/coordinate")
async def coordinate_task(task_description: str = "", complexity: Optional[float] = None):
    from backend.integration.governance_integration_bridge import governance_integration_bridge
    result = governance_integration_bridge.coordinate_all_systems(
        task_description=task_description,
        complexity_override=complexity,
    )
    return result


@router.post("/evolution/inject-data")
async def inject_evolution_data(sample_count: int = Query(100, ge=1, le=1000)):
    from backend.integration.evolution_cultivation_bridge import evolution_cultivation_bridge
    result = evolution_cultivation_bridge.inject_training_data_to_all_stages(sample_count=sample_count)
    return result


@router.post("/alchemy/drive-evolution")
async def drive_evolution_via_furnace(max_iterations: int = Query(5, ge=1, le=50)):
    from backend.integration.cultivation_alchemy_bridge import cultivation_alchemy_bridge
    result = cultivation_alchemy_bridge.run_furnace_driven_evolution(max_iterations=max_iterations)
    return {
        "success": result.success,
        "session_id": result.session_id,
        "iterations": result.total_iterations,
        "stages_completed": f"{result.stages_completed}/{result.stages_total}",
        "convergence_reached": result.convergence_reached,
        "duration_s": result.duration_seconds,
        "final_metrics_keys": list(result.final_metrics.keys()),
    }


@router.get("/cultivation/dashboard")
async def get_cultivation_dashboard():
    from backend.cultivation.cultivation_integration import cultivation_dashboard
    data = cultivation_dashboard.export_dashboard_data()
    overview = cultivation_dashboard.get_system_overview()
    return {
        "overview": {k: v for k, v in overview.__dict__.items() if not k.startswith('_')},
        "stages": data.get("stages", {}),
        "active_alerts_count": data.get("active_alerts", 0),
        "dao_achievement": data.get("dao_achievement", {}),
    }


@router.post("/cultivation/run-engine")
async def run_auto_iteration_engine(background_tasks: BackgroundTasks):
    async def _run_engine():
        from backend.cultivation.cultivation_integration import auto_iteration_engine
        report = auto_iteration_engine.run_full_evolution()
        logger.info(f"[API] 自动迭代引擎完成: state={report.engine_state}")
    background_tasks.add_task(_run_engine)
    return {"message": "自动迭代引擎已在后台启动", "started_at": datetime.now().isoformat()}


@router.post("/cultivation/e2e-test")
async def run_e2e_test():
    from backend.cultivation.cultivation_integration import e2e_cultivation_test
    report = e2e_cultivation_test.run_all_tests()
    return {
        "verdict": report.final_verdict,
        "deployment_readiness": report.deployment_readiness,
        "total_tests": report.total_tests,
        "passed": report.passed_tests,
        "failed": report.failed_tests,
        "pass_pct": round(report.passed_tests / max(report.total_tests, 1) * 100, 1),
        "duration_s": round(report.total_duration_s, 2),
        "recommendations": report.recommendations[:3],
    }


@router.post("/full-cycle")
async def run_full_integration_cycle():
    from backend.integration.platform_orchestrator import platform_orchestrator
    result = platform_orchestrator.run_full_integration_cycle()
    return result


@router.get("/bridge-statuses")
async def get_all_bridge_statuses():
    from backend.integration.cultivation_alchemy_bridge import cultivation_alchemy_bridge
    from backend.integration.evolution_cultivation_bridge import evolution_cultivation_bridge
    from backend.integration.governance_integration_bridge import governance_integration_bridge
    return {
        "alchemy_cultivation": cultivation_alchemy_bridge.get_integration_status(),
        "evolution_cultivation": evolution_cultivation_bridge.get_bridge_status(),
        "governance_all": governance_integration_bridge.get_full_platform_status(),
    }


def register_integration_routes(app):
    app.include_router(router)
    logger.info("[集成路由] 已注册 /api/integration/* 路由到FastAPI应用")


__all__ = ["router", "register_integration_routes"]
