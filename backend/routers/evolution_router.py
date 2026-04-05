"""
三省六部制智能体自我进化系统API
Self-Evolution System API

提供进化引擎、诊断、建议等接口
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import get_current_user
from ..logger import get_logger
from ..agents.evolution.evolution_engine import (
    evolution_engine, AgentType, DiagnosisType, SuggestionType, SuggestionStatus
)

logger = get_logger("evolution_api")

router = APIRouter(prefix="/api/evolution", tags=["evolution"])


class RecordTrajectoryRequest(BaseModel):
    agent_id: str
    input_context: Dict[str, Any]
    decision: Dict[str, Any]
    execution_time: float
    success: bool
    user_feedback: Optional[float] = None
    error_message: Optional[str] = None


class SetBaselineRequest(BaseModel):
    agent_id: str
    success_rate: Optional[float] = None
    avg_time: Optional[float] = None
    feedback: Optional[float] = None


class CreateVersionRequest(BaseModel):
    agent_id: str
    version_number: str
    strategy_hash: str
    parameters_hash: str
    performance_metrics: Dict[str, Any]


class SuggestionActionRequest(BaseModel):
    suggestion_id: str
    reviewer: str = "system"
    reason: Optional[str] = None


@router.get("/report")
async def get_evolution_report(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取进化系统整体报告"""
    return evolution_engine.get_evolution_report()


@router.get("/agents")
async def get_registered_agents(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取已注册的智能体列表"""
    report = evolution_engine.get_evolution_report()
    return {
        "agents": report.get("agents", {}),
        "total": len(report.get("agents", {}))
    }


@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取智能体性能报告"""
    if agent_id not in evolution_engine.meta_cognition_modules:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    module = evolution_engine.meta_cognition_modules[agent_id]
    return module.get_performance_report()


@router.post("/trajectory")
async def record_trajectory(
    request: RecordTrajectoryRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """记录决策轨迹"""
    if request.agent_id not in evolution_engine.meta_cognition_modules:
        raise HTTPException(status_code=404, detail="Agent not registered")
    
    module = evolution_engine.meta_cognition_modules[request.agent_id]
    trajectory_id = module.record_trajectory(
        input_context=request.input_context,
        decision=request.decision,
        execution_time=request.execution_time,
        success=request.success,
        user_feedback=request.user_feedback,
        error_message=request.error_message
    )
    
    return {
        "success": True,
        "trajectory_id": trajectory_id
    }


@router.post("/diagnose/{agent_id}")
async def trigger_diagnosis(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """触发智能体诊断"""
    if agent_id not in evolution_engine.meta_cognition_modules:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    module = evolution_engine.meta_cognition_modules[agent_id]
    diagnoses = module.detect_anomalies()
    suggestions = module.generate_suggestions(diagnoses)
    
    evolution_engine.pending_suggestions.extend(suggestions)
    
    return {
        "success": True,
        "diagnoses": [d.to_dict() for d in diagnoses],
        "suggestions": [s.to_dict() for s in suggestions]
    }


@router.get("/suggestions")
async def get_pending_suggestions(
    agent_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取待处理的建议"""
    suggestions = evolution_engine.get_pending_suggestions(agent_id)
    return {
        "suggestions": [s.to_dict() for s in suggestions],
        "total": len(suggestions)
    }


@router.post("/suggestions/approve")
async def approve_suggestion(
    request: SuggestionActionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """批准建议"""
    success = evolution_engine.approve_suggestion(
        request.suggestion_id, 
        request.reviewer
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    return {
        "success": True,
        "message": "Suggestion approved"
    }


@router.post("/suggestions/reject")
async def reject_suggestion(
    request: SuggestionActionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """拒绝建议"""
    success = evolution_engine.reject_suggestion(
        request.suggestion_id,
        request.reviewer,
        request.reason or ""
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    return {
        "success": True,
        "message": "Suggestion rejected"
    }


@router.post("/suggestions/apply")
async def apply_suggestion(
    request: SuggestionActionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """应用建议"""
    success = evolution_engine.apply_suggestion(request.suggestion_id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Failed to apply suggestion. It may not be approved or not found."
        )
    
    return {
        "success": True,
        "message": "Suggestion applied successfully"
    }


@router.post("/baseline")
async def set_baseline(
    request: SetBaselineRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """设置智能体性能基线"""
    if request.agent_id not in evolution_engine.meta_cognition_modules:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    module = evolution_engine.meta_cognition_modules[request.agent_id]
    module.set_baseline(
        success_rate=request.success_rate,
        avg_time=request.avg_time,
        feedback=request.feedback
    )
    
    return {
        "success": True,
        "message": "Baseline updated"
    }


@router.get("/versions/{agent_id}")
async def get_agent_versions(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取智能体版本历史"""
    versions = evolution_engine.get_agent_versions(agent_id)
    active = evolution_engine.get_active_version(agent_id)
    
    return {
        "agent_id": agent_id,
        "versions": [v.to_dict() for v in versions],
        "active_version": active.to_dict() if active else None,
        "total": len(versions)
    }


@router.post("/versions")
async def create_version(
    request: CreateVersionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """创建新版本"""
    version = evolution_engine.create_version(
        agent_id=request.agent_id,
        version_number=request.version_number,
        strategy_hash=request.strategy_hash,
        parameters_hash=request.parameters_hash,
        performance_metrics=request.performance_metrics
    )
    
    return {
        "success": True,
        "version": version.to_dict()
    }


@router.post("/rollback/{agent_id}")
async def rollback_version(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """回滚到上一版本"""
    version = evolution_engine.rollback_version(agent_id)
    
    if not version:
        raise HTTPException(
            status_code=400, 
            detail="No version available for rollback"
        )
    
    return {
        "success": True,
        "rolled_back_to": version.to_dict()
    }


@router.post("/register")
async def register_agent(
    agent_id: str = Query(...),
    agent_type: str = Query(...),
    initial_version: str = Query("1.0.0"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """注册新智能体到进化系统"""
    try:
        agent_type_enum = AgentType(agent_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent type. Valid types: {[t.value for t in AgentType]}"
        )
    
    module = evolution_engine.register_agent(
        agent_id=agent_id,
        agent_type=agent_type_enum,
        initial_version=initial_version
    )
    
    return {
        "success": True,
        "agent_id": agent_id,
        "message": f"Agent registered with version {initial_version}"
    }
