# -*- coding: utf-8 -*-
"""
MaAS API Router
多智能体架构搜索API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

router = APIRouter(prefix="/api/maas", tags=["MaAS"])


class ScheduleRequest(BaseModel):
    task_content: str
    user_id: Optional[str] = None


class RecordRequest(BaseModel):
    user_id: str
    task_content: str
    architecture_id: str
    execution_time: float
    success: bool
    result_summary: Optional[str] = None


async def get_scheduler_dep():
    from backend.services.maas.scheduler import get_maas_scheduler, init_maas_scheduler
    from backend.database_pg import PostgreSQLConnectionPool
    
    scheduler = get_maas_scheduler()
    if not scheduler:
        pool = await PostgreSQLConnectionPool.get_instance()
        if pool._pool is None:
            await pool._initialize()
        scheduler = await init_maas_scheduler(pool._pool)
    return scheduler


@router.post("/schedule")
async def schedule_task(
    request: ScheduleRequest,
    scheduler = Depends(get_scheduler_dep)
):
    start_time = time.time()
    
    result = await scheduler.schedule(request.task_content, request.user_id)
    
    return {
        "success": True,
        "scheduling": result.to_dict(),
        "processing_time_ms": round((time.time() - start_time) * 1000, 2)
    }


@router.post("/analyze")
async def analyze_task(
    request: ScheduleRequest,
    scheduler = Depends(get_scheduler_dep)
):
    from backend.services.maas.scheduler import TaskAnalyzer, ComplexityEstimator
    
    analyzer = TaskAnalyzer()
    estimator = ComplexityEstimator()
    
    feature = analyzer.analyze(request.task_content)
    complexity = estimator.estimate(feature)
    feature.complexity_score = complexity
    
    return {
        "task_feature": feature.to_dict(),
        "complexity_score": complexity,
        "recommendation": _get_complexity_recommendation(complexity)
    }


def _get_complexity_recommendation(complexity: float) -> str:
    if complexity < 0.3:
        return "简单任务，建议使用轻量架构（礼部+户部）"
    elif complexity < 0.7:
        return "中等任务，建议使用标准架构（三省核心流程）"
    else:
        return "复杂任务，建议使用完整架构（三省六部全流程）"


@router.get("/operators")
async def list_operators(
    scheduler = Depends(get_scheduler_dep)
):
    operators = await scheduler.get_operators()
    return {
        "operators": [op.to_dict() for op in operators],
        "total": len(operators)
    }


@router.get("/architectures")
async def list_architectures(
    scheduler = Depends(get_scheduler_dep)
):
    templates = await scheduler.get_templates()
    return {
        "architectures": [t.to_dict() for t in templates],
        "total": len(templates)
    }


@router.post("/record")
async def record_decision(
    request: RecordRequest,
    scheduler = Depends(get_scheduler_dep)
):
    from backend.services.maas.models import ArchitectureTemplate, SchedulingResult
    
    templates = await scheduler.get_templates()
    arch = next((t for t in templates if t.id == request.architecture_id), None)
    
    if not arch:
        raise HTTPException(status_code=404, detail="Architecture not found")
    
    result = SchedulingResult(
        architecture=arch,
        agents=[],
        estimated_cost=arch.avg_cost,
        estimated_latency=arch.avg_latency,
        complexity_score=0.5
    )
    
    decision_id = await scheduler.record_decision(
        user_id=request.user_id,
        task_content=request.task_content,
        result=result,
        execution_time=request.execution_time,
        success=request.success,
        result_summary=request.result_summary or ""
    )
    
    return {
        "success": True,
        "decision_id": decision_id
    }


@router.get("/history/{user_id}")
async def get_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    scheduler = Depends(get_scheduler_dep)
):
    decisions = await scheduler.get_decision_history(user_id, limit)
    return {
        "decisions": [d.to_dict() for d in decisions],
        "total": len(decisions)
    }


@router.get("/stats")
async def get_stats(
    scheduler = Depends(get_scheduler_dep)
):
    operators = await scheduler.get_operators()
    templates = await scheduler.get_templates()
    
    return {
        "total_operators": len(operators),
        "total_architectures": len(templates),
        "operator_types": list(set(op.agent_type for op in operators)),
        "complexity_ranges": [
            {
                "name": t.name,
                "range": [t.complexity_range_min, t.complexity_range_max],
                "agents": len(t.agent_sequence)
            }
            for t in templates
        ]
    }


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "maas",
        "timestamp": datetime.utcnow().isoformat()
    }
