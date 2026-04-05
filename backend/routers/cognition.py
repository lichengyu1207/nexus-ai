"""
智能体认知系统API
Agent Cognition System API

提供思维框架、价值体系、决策引擎等接口
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import get_current_user
from ..database import get_db_connection
from ..logger import get_logger
from .core import (
    cognition_db, framework_applier, value_evaluator, decision_engine,
    ThinkingFramework, ValueProposition, DecisionResult
)

logger = get_logger("cognition_api")

router = APIRouter(prefix="/api/cognition", tags=["cognition"])

@router.get("/status")
async def get_cognition_status():
    """获取认知系统状态"""
    return {
        "status": "running",
        "modules": {
            "thinking_frameworks": "active",
            "value_system": "active", 
            "decision_engine": "active"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


class ApplyFrameworkRequest(BaseModel):
    framework_id: str
    problem: str
    context: Optional[Dict[str, Any]] = None


class EvaluateOptionsRequest(BaseModel):
    options: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


class MakeDecisionRequest(BaseModel):
    problem: str
    context: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    feedback: str
    score: float


@router.get("/frameworks")
async def get_frameworks(
    scenario: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取思维框架列表"""
    if scenario:
        frameworks = cognition_db.get_frameworks_by_scenario(scenario)
    else:
        frameworks = cognition_db.get_all_frameworks()
    
    return {
        "frameworks": [
            {
                "id": fw.id,
                "name": fw.name,
                "description": fw.description,
                "steps": [
                    {"order": s.order, "name": s.name, "description": s.description}
                    for s in fw.steps
                ],
                "applicable_scenarios": fw.applicable_scenarios,
                "usage_count": fw.usage_count,
                "success_rate": fw.success_rate
            }
            for fw in frameworks
        ],
        "total": len(frameworks)
    }


@router.get("/frameworks/{framework_id}")
async def get_framework_detail(
    framework_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取思维框架详情"""
    framework = cognition_db.get_framework(framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    return {
        "id": framework.id,
        "name": framework.name,
        "description": framework.description,
        "steps": [
            {
                "order": s.order,
                "name": s.name,
                "description": s.description,
                "prompt": s.prompt
            }
            for s in framework.steps
        ],
        "applicable_scenarios": framework.applicable_scenarios,
        "usage_count": framework.usage_count,
        "success_rate": framework.success_rate
    }


@router.post("/frameworks/apply")
async def apply_framework(
    request: ApplyFrameworkRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """应用思维框架分析问题"""
    framework = cognition_db.get_framework(request.framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    result = framework_applier.apply(
        framework, 
        request.problem, 
        request.context or {}
    )
    
    cognition_db.update_framework_usage(request.framework_id, True)
    
    return {
        "success": True,
        "framework_name": framework.name,
        "thinking_process": result["steps"],
        "conclusion": result["conclusion"]
    }


@router.get("/values")
async def get_values(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取价值体系列表"""
    values = cognition_db.get_all_values()
    
    return {
        "values": [
            {
                "id": v.id,
                "name": v.name,
                "type": v.type.value,
                "statement": v.statement,
                "explanation": v.explanation,
                "priority": v.priority,
                "weight": v.weight
            }
            for v in values
        ],
        "total": len(values)
    }


@router.post("/evaluate")
async def evaluate_options(
    request: EvaluateOptionsRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """评估选项"""
    result = value_evaluator.evaluate(request.options, request.context or {})
    
    return {
        "success": True,
        "results": result["results"],
        "best_option": result["best_option"],
        "evaluation_time": result["evaluation_time"]
    }


@router.post("/decide")
async def make_decision(
    request: MakeDecisionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """做出决策"""
    result = decision_engine.decide(
        request.problem,
        request.context or {},
        request.agent_id
    )
    
    return {
        "success": True,
        "decision": result.decision,
        "confidence": result.confidence,
        "framework_used": result.framework_used,
        "thinking_process": result.thinking_process,
        "evaluation": result.evaluation,
        "alternatives": result.alternatives
    }


@router.get("/agent/{agent_id}")
async def get_agent_cognition(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取智能体认知状态"""
    cognition = cognition_db.get_agent_cognition(agent_id)
    if not cognition:
        return {
            "agent_id": agent_id,
            "frameworks": [],
            "values": {},
            "cognitive_bias": {},
            "experience_points": 0,
            "level": 1,
            "decision_quality": 0.5,
            "growth_history": []
        }
    
    return cognition


@router.post("/agent/{agent_id}/feedback/{decision_id}")
async def provide_feedback(
    agent_id: str,
    decision_id: str,
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """提供决策反馈"""
    if request.score < 0 or request.score > 1:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 1")
    
    decision_engine.reflect_on_decision(
        agent_id, decision_id, request.feedback, request.score
    )
    
    return {
        "success": True,
        "message": "Feedback recorded",
        "agent_id": agent_id,
        "decision_id": decision_id
    }


@router.get("/agent/{agent_id}/decisions")
async def get_agent_decisions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取智能体决策历史"""
    conn = sqlite3.connect(cognition_db.db_path)
    try:
        cursor = conn.execute("""
            SELECT id, problem, decision_result, framework_used, confidence, 
                   feedback, feedback_score, created_at
            FROM decision_logs
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, limit))
        
        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                "id": row[0],
                "problem": row[1],
                "decision": row[2],
                "framework_used": row[3],
                "confidence": row[4],
                "feedback": row[5],
                "feedback_score": row[6],
                "created_at": row[7]
            })
        
        return {
            "agent_id": agent_id,
            "decisions": decisions,
            "total": len(decisions)
        }
    finally:
        conn.close()


@router.get("/agent/{agent_id}/growth")
async def get_agent_growth(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取智能体成长记录"""
    import sqlite3
    conn = sqlite3.connect(cognition_db.db_path)
    try:
        cursor = conn.execute("""
            SELECT id, event_type, description, experience_gained,
                   frameworks_unlocked, values_refined, created_at
            FROM agent_growth_events
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (agent_id,))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row[0],
                "event_type": row[1],
                "description": row[2],
                "experience_gained": row[3],
                "frameworks_unlocked": json.loads(row[4]) if row[4] else [],
                "values_refined": json.loads(row[5]) if row[5] else {},
                "created_at": row[6]
            })
        
        return {
            "agent_id": agent_id,
            "growth_events": events,
            "total": len(events)
        }
    finally:
        conn.close()


@router.get("/analogies")
async def get_analogies(
    scenario: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取类比库"""
    import sqlite3
    conn = sqlite3.connect(cognition_db.db_path)
    try:
        cursor = conn.execute("""
            SELECT id, type, name, source_domain, target_domain, 
                   description, mapping_json, lesson, applicable_scenarios
            FROM cognitive_analogies
        """)
        
        analogies = []
        for row in cursor.fetchall():
            analogy = {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "source_domain": row[3],
                "target_domain": row[4],
                "description": row[5],
                "mapping": json.loads(row[6]) if row[6] else {},
                "lesson": row[7],
                "applicable_scenarios": json.loads(row[8]) if row[8] else []
            }
            
            if scenario is None or scenario in analogy["applicable_scenarios"]:
                analogies.append(analogy)
        
        return {
            "analogies": analogies,
            "total": len(analogies)
        }
    finally:
        conn.close()


import sqlite3
