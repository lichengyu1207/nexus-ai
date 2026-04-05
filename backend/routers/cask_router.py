# -*- coding: utf-8 -*-
"""
CASK 上下文自适应稀疏KV缓存 API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from ..services.cask import (
    CASKModule, CASKConfig, get_default_config,
    CacheSession, SparsityDecision, PerformanceMetric
)
from ..services.cask.performance_monitor import PerformanceMonitor

router = APIRouter(prefix="/cask", tags=["CASK - 稀疏KV缓存"])

cask_module = CASKModule()
performance_monitor = PerformanceMonitor()


class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    model_name: str = "default"


class ProcessRequest(BaseModel):
    session_id: Optional[str] = None
    query: List[float] = Field(..., description="Query向量")
    key: List[float] = Field(..., description="Key向量")
    value: List[float] = Field(..., description="Value向量")


class ComputeSparsityRequest(BaseModel):
    context_length: int
    attention_weights: Optional[List[float]] = None
    step: int = 0
    model_name: str = "default"


class EstimateImportanceRequest(BaseModel):
    query: List[float]
    kv_cache: List[Dict[str, List[float]]]
    model_name: str = "default"


class RecordMetricRequest(BaseModel):
    session_id: Optional[str] = None
    metric_type: str
    metric_name: str
    value: float
    unit: str = ""
    metadata: Optional[Dict[str, Any]] = None


@router.post("/session/create", summary="创建缓存会话")
async def create_session(request: CreateSessionRequest):
    user_id = UUID(request.user_id) if request.user_id else None
    
    session = cask_module.create_session(
        user_id=user_id,
        model_name=request.model_name
    )
    
    return {
        "success": True,
        "session": session.to_dict()
    }


@router.get("/session/{session_id}", summary="获取会话信息")
async def get_session(session_id: str):
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    stats = cask_module.get_session_statistics(sid)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "statistics": stats
    }


@router.delete("/session/{session_id}", summary="结束会话")
async def end_session(session_id: str):
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    success = cask_module.end_session(sid)
    
    return {
        "success": success,
        "message": "Session ended" if success else "Session not found"
    }


@router.post("/process", summary="处理注意力计算")
async def process_attention(request: ProcessRequest):
    session_id = UUID(request.session_id) if request.session_id else None
    
    output = cask_module.process(
        query=request.query,
        key=request.key,
        value=request.value,
        session_id=session_id
    )
    
    performance_monitor.record_metric(
        metric_type="performance",
        metric_name="latency_ms",
        value=output.latency_ms,
        unit="ms"
    )
    
    if output.sparsity_rate > 0:
        performance_monitor.record_metric(
            metric_type="cask",
            metric_name="sparsity_rate",
            value=output.sparsity_rate
        )
    
    return {
        "success": True,
        "output": output.to_dict()
    }


@router.post("/sparsity/compute", summary="计算稀疏率")
async def compute_sparsity(request: ComputeSparsityRequest):
    config = get_default_config(request.model_name)
    controller = cask_module._default_attention.sparse_controller
    
    sparsity = controller.compute_sparsity(
        context_length=request.context_length,
        attention_weights=request.attention_weights,
        step=request.step
    )
    
    memory_info = controller.estimate_memory_savings(
        kv_pairs_total=request.context_length,
        sparsity_rate=sparsity
    )
    
    return {
        "success": True,
        "sparsity_rate": sparsity,
        "complexity_score": controller.get_complexity(),
        "stage": controller.get_stage(request.step),
        "memory_savings": memory_info
    }


@router.post("/importance/estimate", summary="估计重要性分数")
async def estimate_importance(request: EstimateImportanceRequest):
    config = get_default_config(request.model_name)
    
    from ..services.cask.importance_estimator import ImportanceEstimator
    estimator = ImportanceEstimator(config)
    
    kv_cache = [
        (kv["key"], kv["value"]) 
        for kv in request.kv_cache
    ]
    
    scores = estimator.estimate(request.query, kv_cache)
    
    return {
        "success": True,
        "importance_scores": [s.to_dict() for s in scores],
        "total_count": len(scores)
    }


@router.get("/statistics", summary="获取全局统计")
async def get_statistics():
    global_stats = cask_module.get_global_statistics()
    monitor_stats = performance_monitor.get_statistics()
    
    return {
        "success": True,
        "cask_module": global_stats,
        "performance_monitor": monitor_stats
    }


@router.get("/statistics/summary", summary="获取性能摘要")
async def get_summary():
    summary = performance_monitor.get_summary()
    
    return {
        "success": True,
        "summary": summary
    }


@router.post("/metric/record", summary="记录性能指标")
async def record_metric(request: RecordMetricRequest):
    metric = performance_monitor.record_metric(
        metric_type=request.metric_type,
        metric_name=request.metric_name,
        value=request.value,
        unit=request.unit,
        metadata=request.metadata
    )
    
    return {
        "success": True,
        "metric": metric.to_dict()
    }


@router.get("/metrics", summary="获取性能指标列表")
async def get_metrics(metric_type: Optional[str] = None, limit: int = 100):
    metrics = performance_monitor.get_metrics(metric_type=metric_type, limit=limit)
    
    return {
        "success": True,
        "count": len(metrics),
        "metrics": [
            {
                "metric_type": m.metric_type,
                "metric_name": m.metric_name,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    }


@router.get("/config/{model_name}", summary="获取模型配置")
async def get_config(model_name: str):
    config = get_default_config(model_name)
    
    return {
        "success": True,
        "config": config.to_dict()
    }


@router.post("/reset", summary="重置所有会话")
async def reset_all():
    cask_module.clear_all_sessions()
    performance_monitor.clear()
    
    return {
        "success": True,
        "message": "All sessions cleared"
    }
