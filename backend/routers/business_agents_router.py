"""
业务层活体智能体API路由
Business Layer Living Agents API Router

提供业务层活体智能体的完整API接口
"""

import os
import json
import time
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body, Path as PathParam
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-agents", tags=["Business Agents"])


class AgentStateResponse(BaseModel):
    agent_id: str
    name: str
    role: str
    species: str
    energy: float
    age: int
    generation: int
    status: str
    is_alive: bool
    is_available: bool
    stats: Dict


class TaskCreateRequest(BaseModel):
    task_type: str
    title: str
    description: str
    complexity: float = 1.0
    required_skills: List[str] = []
    required_roles: List[str] = []
    user_id: Optional[str] = None
    request_data: Dict = {}
    priority: int = 2


class TaskBidRequest(BaseModel):
    task_id: str
    agent_id: str
    promised_completion_time: float
    success_rate_estimate: float
    capabilities: List[str]
    message: str = ""


class FeedbackSubmitRequest(BaseModel):
    user_id: str
    agent_id: str
    task_id: str
    feedback_type: str
    content: Optional[str] = None
    rating: Optional[float] = None


class InterventionRequest(BaseModel):
    agent_id: str
    intervention_type: str
    parameters: Dict = {}
    reason: str = ""


class ModeSwitchRequest(BaseModel):
    mode: str
    reason: str = ""


_business_system: Optional[Any] = None


def get_business_system():
    global _business_system
    if _business_system is None:
        from backend.agents.business import (
            TaskMarket,
            CollaborationProtocol,
            LocalRulesEngine,
            BusinessEmergenceObserver,
            OnlineLearningEngine,
            SkillTransferMechanism,
            BusinessAgentReproduction,
            ResourceCompetition,
            CooperativeGameMechanism,
            BusinessEnvironmentField,
            UserFeedbackLoop,
            BusinessGoalAlignment,
            BusinessControlConsole,
            BusinessInterfaceAdapter,
            LifeIndexEvaluator,
            BusinessEvolutionEngine,
        )
        
        _business_system = {
            "task_market": TaskMarket(),
            "collaboration_protocol": CollaborationProtocol(),
            "rules_engine": LocalRulesEngine(),
            "emergence_observer": BusinessEmergenceObserver(),
            "learning_engine": OnlineLearningEngine(),
            "skill_transfer": SkillTransferMechanism(),
            "reproduction": BusinessAgentReproduction(),
            "resource_competition": ResourceCompetition(),
            "cooperative_game": CooperativeGameMechanism(),
            "environment_field": BusinessEnvironmentField(),
            "feedback_loop": UserFeedbackLoop(),
            "goal_alignment": BusinessGoalAlignment(),
            "control_console": BusinessControlConsole(),
            "interface_adapter": BusinessInterfaceAdapter(),
            "life_evaluator": LifeIndexEvaluator(),
            "evolution_engine": BusinessEvolutionEngine(),
        }
    return _business_system


@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


@router.get("/agents")
async def list_agents(
    species: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50),
):
    system = get_business_system()
    evolution = system["evolution_engine"]
    
    agents = evolution.population_manager.get_population()
    
    if species:
        agents = [a for a in agents if a.species == species]
    
    if status:
        agents = [a for a in agents if a.status.value == status]
    
    return {
        "agents": [a.get_state() for a in agents[:limit]],
        "total": len(agents),
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str = PathParam(...)):
    system = get_business_system()
    evolution = system["evolution_engine"]
    
    agent = evolution.population_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_state()


@router.get("/agents/{agent_id}/profile")
async def get_agent_profile(agent_id: str = PathParam(...)):
    system = get_business_system()
    evolution = system["evolution_engine"]
    
    agent = evolution.population_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_business_profile()


@router.get("/agents/{agent_id}/fitness")
async def get_agent_fitness(agent_id: str = PathParam(...)):
    system = get_business_system()
    evolution = system["evolution_engine"]
    
    agent = evolution.population_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "fitness": agent.get_fitness(),
    }


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    system = get_business_system()
    task_market = system["task_market"]
    
    from backend.agents.business.task_market import TaskType, TaskPriority
    
    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        task_type = TaskType.CONSULTATION
    
    priority = TaskPriority(request.priority) if 1 <= request.priority <= 5 else TaskPriority.NORMAL
    
    task = await task_market.publish_task(
        task_type=task_type,
        title=request.title,
        description=request.description,
        complexity=request.complexity,
        required_skills=request.required_skills,
        required_roles=request.required_roles,
        user_id=request.user_id,
        request_data=request.request_data,
        priority=priority,
    )
    
    return task.to_dict()


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(50),
):
    system = get_business_system()
    task_market = system["task_market"]
    
    tasks = list(task_market.tasks.values())
    
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    
    return {
        "tasks": [t.to_dict() for t in tasks[:limit]],
        "total": len(tasks),
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str = PathParam(...)):
    system = get_business_system()
    task_market = system["task_market"]
    
    task = task_market.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


@router.post("/tasks/{task_id}/bids")
async def submit_bid(task_id: str, request: TaskBidRequest):
    system = get_business_system()
    task_market = system["task_market"]
    
    bid = await task_market.submit_bid(
        task_id=task_id,
        agent_id=request.agent_id,
        promised_completion_time=request.promised_completion_time,
        success_rate_estimate=request.success_rate_estimate,
        capabilities=request.capabilities,
        message=request.message,
    )
    
    if not bid:
        raise HTTPException(status_code=400, detail="Failed to submit bid")
    
    return bid.to_dict()


@router.get("/tasks/{task_id}/bids")
async def get_task_bids(task_id: str = PathParam(...)):
    system = get_business_system()
    task_market = system["task_market"]
    
    bids = task_market.get_bids(task_id)
    
    return {
        "task_id": task_id,
        "bids": [b.to_dict() for b in bids],
    }


@router.post("/tasks/{task_id}/select-winners")
async def select_task_winners(
    task_id: str,
    max_winners: int = Body(1, embed=True),
    strategy: str = Body("best_fit", embed=True),
):
    system = get_business_system()
    task_market = system["task_market"]
    
    winners = await task_market.select_winners(
        task_id=task_id,
        max_winners=max_winners,
        strategy=strategy,
    )
    
    return {
        "task_id": task_id,
        "winners": winners,
    }


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    result: Dict = Body({}, embed=True),
    contributions: Dict = Body({}, embed=True),
):
    system = get_business_system()
    task_market = system["task_market"]
    
    success = await task_market.complete_task(
        task_id=task_id,
        result=result,
        agent_contributions=contributions,
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to complete task")
    
    return {"success": True, "task_id": task_id}


@router.get("/market/stats")
async def get_market_stats():
    system = get_business_system()
    task_market = system["task_market"]
    
    return await task_market.get_state()


@router.post("/feedback")
async def submit_feedback(request: FeedbackSubmitRequest):
    system = get_business_system()
    feedback_loop = system["feedback_loop"]
    
    from backend.agents.business.user_feedback import FeedbackType
    
    try:
        feedback_type = FeedbackType(request.feedback_type)
    except ValueError:
        feedback_type = FeedbackType.RATING
    
    feedback = await feedback_loop.submit_feedback(
        user_id=request.user_id,
        agent_id=request.agent_id,
        task_id=request.task_id,
        feedback_type=feedback_type,
        content=request.content,
        rating=request.rating,
    )
    
    return feedback.to_dict()


@router.get("/feedback/agents/{agent_id}")
async def get_agent_feedback(agent_id: str = PathParam(...)):
    system = get_business_system()
    feedback_loop = system["feedback_loop"]
    
    feedbacks = feedback_loop.get_agent_feedbacks(agent_id)
    
    return {
        "agent_id": agent_id,
        "feedbacks": [f.to_dict() for f in feedbacks],
    }


@router.get("/users/{user_id}/preferences")
async def get_user_preferences(user_id: str = PathParam(...)):
    system = get_business_system()
    feedback_loop = system["feedback_loop"]
    
    pref = feedback_loop.get_user_preference(user_id)
    
    if not pref:
        return {"user_id": user_id, "preferences": None}
    
    return pref.to_dict()


@router.get("/environment")
async def get_environment():
    system = get_business_system()
    env_field = system["environment_field"]
    
    return {
        "kpis": {k: v.to_dict() for k, v in env_field.kpis.items()},
        "market_data": env_field.market_data,
        "internal_state": env_field.internal_state,
    }


@router.get("/environment/history")
async def get_environment_history(limit: int = Query(10)):
    system = get_business_system()
    env_field = system["environment_field"]
    
    history = env_field.get_history(limit)
    
    return {
        "snapshots": [s.to_dict() for s in history],
    }


@router.get("/emergence/patterns")
async def get_emergence_patterns(
    pattern_type: Optional[str] = Query(None),
    limit: int = Query(20),
):
    system = get_business_system()
    observer = system["emergence_observer"]
    
    if pattern_type:
        from backend.agents.business.emergence_observer import PatternType
        try:
            pt = PatternType(pattern_type)
            patterns = observer.get_patterns_by_type(pt)
        except ValueError:
            patterns = list(observer.patterns.values())
    else:
        patterns = list(observer.patterns.values())
    
    return {
        "patterns": [p.to_dict() for p in patterns[:limit]],
        "total": len(patterns),
    }


@router.get("/emergence/network")
async def get_collaboration_network():
    system = get_business_system()
    observer = system["emergence_observer"]
    
    network = observer.get_latest_network()
    
    if not network:
        return {"network": None}
    
    return network.to_dict()


@router.get("/learning/sessions")
async def get_learning_sessions(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(20),
):
    system = get_business_system()
    learning_engine = system["learning_engine"]
    
    if agent_id:
        sessions = learning_engine.get_agent_sessions(agent_id)
    else:
        sessions = list(learning_engine.learning_sessions.values())
    
    return {
        "sessions": [s.to_dict() for s in sessions[-limit:]],
        "total": len(sessions),
    }


@router.get("/learning/stats")
async def get_learning_stats():
    system = get_business_system()
    learning_engine = system["learning_engine"]
    
    return learning_engine.get_stats()


@router.get("/skill-transfer/teachers")
async def list_teachers():
    system = get_business_system()
    skill_transfer = system["skill_transfer"]
    
    return {
        "teachers": list(skill_transfer.teacher_registry.values()),
    }


@router.get("/skill-transfer/students")
async def list_students():
    system = get_business_system()
    skill_transfer = system["skill_transfer"]
    
    return {
        "students": list(skill_transfer.student_registry.values()),
    }


@router.get("/skill-transfer/apprenticeship-tree")
async def get_apprenticeship_tree():
    system = get_business_system()
    skill_transfer = system["skill_transfer"]
    
    return skill_transfer.get_apprenticeship_tree()


@router.get("/reproduction/offspring")
async def list_offspring(
    parent_id: Optional[str] = Query(None),
    limit: int = Query(20),
):
    system = get_business_system()
    reproduction = system["reproduction"]
    
    if parent_id:
        offspring = reproduction.get_children(parent_id)
    else:
        offspring = list(reproduction.offspring_records.values())
    
    return {
        "offspring": [o.to_dict() for o in offspring[-limit:]],
        "total": len(offspring),
    }


@router.get("/reproduction/family-tree")
async def get_family_tree():
    system = get_business_system()
    reproduction = system["reproduction"]
    
    return reproduction.get_family_tree()


@router.get("/competition/resources")
async def list_resources():
    system = get_business_system()
    competition = system["resource_competition"]
    
    return competition.get_all_resources()


@router.get("/competition/stats")
async def get_competition_stats():
    system = get_business_system()
    competition = system["resource_competition"]
    
    return competition.get_stats()


@router.get("/cooperation/teams")
async def list_teams():
    system = get_business_system()
    coop_game = system["cooperative_game"]
    
    return {
        "teams": list(coop_game.teams.values()),
    }


@router.get("/cooperation/stats")
async def get_cooperation_stats():
    system = get_business_system()
    coop_game = system["cooperative_game"]
    
    return coop_game.get_stats()


@router.get("/alignment/rules")
async def list_alignment_rules():
    system = get_business_system()
    alignment = system["goal_alignment"]
    
    return {
        "rules": [r.to_dict() for r in alignment.get_all_rules()],
    }


@router.get("/alignment/stats")
async def get_alignment_stats():
    system = get_business_system()
    alignment = system["goal_alignment"]
    
    return alignment.get_stats()


@router.post("/console/interventions")
async def create_intervention(request: InterventionRequest):
    system = get_business_system()
    console = system["control_console"]
    
    from backend.agents.business.control_console import InterventionType
    
    try:
        intervention_type = InterventionType(request.intervention_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid intervention type")
    
    if intervention_type == InterventionType.ENERGY_ADJUST:
        intervention = await console.adjust_energy(
            agent_id=request.agent_id,
            amount=request.parameters.get("amount", 0),
            operator_id="api_user",
            reason=request.reason,
        )
    elif intervention_type == InterventionType.FORCE_REPRODUCE:
        intervention = await console.force_reproduce(
            agent_id=request.agent_id,
            operator_id="api_user",
            reason=request.reason,
        )
    elif intervention_type == InterventionType.FORCE_TERMINATE:
        intervention = await console.force_terminate(
            agent_id=request.agent_id,
            operator_id="api_user",
            reason=request.reason,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported intervention type")
    
    return intervention.to_dict()


@router.post("/console/mode")
async def set_operation_mode(request: ModeSwitchRequest):
    system = get_business_system()
    console = system["control_console"]
    
    from backend.agents.business.control_console import OperationMode
    
    try:
        mode = OperationMode(request.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid operation mode")
    
    result = console.set_operation_mode(
        mode=mode,
        operator_id="api_user",
        reason=request.reason,
    )
    
    return result


@router.get("/console/dashboard")
async def get_console_dashboard():
    system = get_business_system()
    console = system["control_console"]
    
    return console.get_dashboard_data()


@router.get("/life-index/agents/{agent_id}")
async def get_agent_life_index(agent_id: str = PathParam(...)):
    system = get_business_system()
    evaluator = system["life_evaluator"]
    
    index = evaluator.get_agent_index(agent_id)
    
    if not index:
        raise HTTPException(status_code=404, detail="Life index not found")
    
    return index.to_dict()


@router.get("/life-index/report")
async def get_life_index_report():
    system = get_business_system()
    evaluator = system["life_evaluator"]
    
    report = evaluator.get_latest_report()
    
    if not report:
        return {"report": None}
    
    return report.to_dict()


@router.get("/rules")
async def list_rules(
    department: Optional[str] = Query(None),
):
    system = get_business_system()
    rules_engine = system["rules_engine"]
    
    if department:
        rules = rules_engine.get_department_rules(department)
    else:
        rules = rules_engine.get_all_rules()
    
    return {
        "rules": [r.to_dict() for r in rules],
    }


@router.get("/rules/stats")
async def get_rules_stats():
    system = get_business_system()
    rules_engine = system["rules_engine"]
    
    return rules_engine.get_stats()


@router.get("/stats")
async def get_system_stats():
    system = get_business_system()
    
    return {
        "task_market": system["task_market"].stats,
        "learning_engine": system["learning_engine"].get_stats(),
        "skill_transfer": system["skill_transfer"].get_stats(),
        "reproduction": system["reproduction"].get_stats(),
        "competition": system["resource_competition"].get_stats(),
        "cooperation": system["cooperative_game"].get_stats(),
        "environment": system["environment_field"].get_stats(),
        "feedback": system["feedback_loop"].get_stats(),
        "alignment": system["goal_alignment"].get_stats(),
        "console": system["control_console"].get_stats(),
        "life_evaluator": system["life_evaluator"].get_stats(),
        "evolution": system["evolution_engine"].stats,
    }
