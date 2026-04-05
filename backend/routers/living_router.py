"""
活体智能体系统API路由
Living Agent System API Router

提供活体智能体系统的完整API接口
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..agents.living import (
    P2PCommunication,
    Blackboard,
    global_blackboard,
    TaskBiddingSystem,
    DynamicTeamFormation,
    DefenseLocalRules,
    DynamicRewardField,
    EmergenceAnalyzer,
    ReproductionModule,
    MutationSelection,
    EnvironmentPerception,
    SafetyFence,
    EthicalAlignment,
    TaskStatus,
    TaskPriority
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/living", tags=["living"])

blackboard: Optional[Blackboard] = None
task_bidding: Optional[TaskBiddingSystem] = None
team_formation: Optional[DynamicTeamFormation] = None
reward_field: Optional[DynamicRewardField] = None
emergence_analyzer: Optional[EmergenceAnalyzer] = None
reproduction: Optional[ReproductionModule] = None
selection: Optional[MutationSelection] = None
environment: Optional[EnvironmentPerception] = None
safety_fence: Optional[SafetyFence] = None
ethical_alignment: Optional[EthicalAlignment] = None


class PublishTaskRequest(BaseModel):
    task_type: str
    description: str
    required_skills: List[Dict] = Field(default_factory=list)
    priority: int = Field(default=2, ge=1, le=5)
    reward: float = Field(default=10.0, ge=0)
    max_team_size: int = Field(default=5, ge=1)
    min_team_size: int = Field(default=1, ge=1)
    created_by: str = Field(default="system")


class SubmitBidRequest(BaseModel):
    task_id: str
    agent_id: str
    estimated_completion_time: float
    success_probability: float = Field(default=0.8, ge=0, le=1)
    capabilities: Dict[str, float] = Field(default_factory=dict)


class CompleteTaskRequest(BaseModel):
    task_id: str
    agent_id: str
    result: Optional[Dict] = None
    success: bool = True


class FormTeamRequest(BaseModel):
    team_name: str
    task_id: str
    agent_ids: List[str]
    leader_id: Optional[str] = None


class RegisterAgentRequest(BaseModel):
    agent_id: str
    generation: int = Field(default=0)
    parent_ids: List[str] = Field(default_factory=list)


class ReproduceRequest(BaseModel):
    parent_id: str
    offspring_id: str


class SexualReproduceRequest(BaseModel):
    parent1_id: str
    parent2_id: str
    offspring_id: str


class RecordFitnessRequest(BaseModel):
    agent_id: str
    fitness: float


class CheckActionRequest(BaseModel):
    agent_id: str
    action: Dict
    context: Dict = Field(default_factory=dict)


class VoteJudgmentRequest(BaseModel):
    judgment_id: str
    voter_id: str
    vote: bool
    reason: str = ""


class WriteBlackboardRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None


class SendMessageRequest(BaseModel):
    target_agent_id: str
    message_type: str
    payload: Dict
    priority: int = Field(default=0)
    requires_ack: bool = False


class BroadcastRequest(BaseModel):
    message_type: str
    payload: Dict
    priority: int = Field(default=0)


def get_blackboard() -> Blackboard:
    global blackboard
    if blackboard is None:
        blackboard = Blackboard()
    return blackboard


def get_task_bidding() -> TaskBiddingSystem:
    global task_bidding
    if task_bidding is None:
        task_bidding = TaskBiddingSystem(get_blackboard())
    return task_bidding


def get_reward_field() -> DynamicRewardField:
    global reward_field
    if reward_field is None:
        reward_field = DynamicRewardField(get_blackboard())
    return reward_field


def get_emergence_analyzer() -> EmergenceAnalyzer:
    global emergence_analyzer
    if emergence_analyzer is None:
        emergence_analyzer = EmergenceAnalyzer(get_blackboard())
    return emergence_analyzer


def get_reproduction() -> ReproductionModule:
    global reproduction
    if reproduction is None:
        reproduction = ReproductionModule(get_blackboard())
    return reproduction


def get_safety_fence() -> SafetyFence:
    global safety_fence
    if safety_fence is None:
        safety_fence = SafetyFence(get_blackboard(), None)
    return safety_fence


@router.get("/status")
async def get_system_status():
    return {
        "blackboard": get_blackboard().get_stats(),
        "task_bidding": get_task_bidding().get_stats(),
        "reward_field": get_reward_field().get_stats(),
        "emergence_analyzer": get_emergence_analyzer().get_stats(),
        "reproduction": get_reproduction().get_stats(),
        "safety_fence": get_safety_fence().get_status()
    }


@router.get("/blackboard/keys")
async def get_blackboard_keys():
    bb = get_blackboard()
    return {"keys": bb.get_all_keys()}


@router.get("/blackboard/{key}")
async def read_blackboard(key: str):
    bb = get_blackboard()
    value = bb.read(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value}


@router.post("/blackboard/write")
async def write_blackboard(request: WriteBlackboardRequest):
    bb = get_blackboard()
    success = bb.write(request.key, request.value, request.ttl)
    return {"success": success, "key": request.key}


@router.delete("/blackboard/{key}")
async def delete_blackboard(key: str):
    bb = get_blackboard()
    success = bb.delete(key)
    return {"success": success, "key": key}


@router.get("/blackboard/search/{query}")
async def search_blackboard(query: str, limit: int = Query(100, ge=1, le=500)):
    bb = get_blackboard()
    results = bb.search(query, limit)
    return {"query": query, "results": results, "count": len(results)}


@router.post("/tasks/publish")
async def publish_task(request: PublishTaskRequest):
    tb = get_task_bidding()
    
    priority_map = {
        1: TaskPriority.LOW,
        2: TaskPriority.NORMAL,
        3: TaskPriority.HIGH,
        4: TaskPriority.CRITICAL,
        5: TaskPriority.EMERGENCY
    }
    
    task = tb.publish_task(
        task_type=request.task_type,
        description=request.description,
        required_skills=request.required_skills,
        priority=priority_map.get(request.priority, TaskPriority.NORMAL),
        reward=request.reward,
        max_team_size=request.max_team_size,
        min_team_size=request.min_team_size,
        created_by=request.created_by
    )
    
    return {"task_id": task.task_id, "status": task.status.value}


@router.post("/tasks/bid")
async def submit_bid(request: SubmitBidRequest):
    tb = get_task_bidding()
    
    bid = tb.submit_bid(
        task_id=request.task_id,
        agent_id=request.agent_id,
        estimated_completion_time=request.estimated_completion_time,
        success_probability=request.success_probability,
        capabilities=request.capabilities
    )
    
    if bid is None:
        raise HTTPException(status_code=400, detail="Failed to submit bid")
    
    return {"bid_id": bid.bid_id, "status": "submitted"}


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    tb = get_task_bidding()
    
    if agent_id:
        tasks = tb.get_agent_tasks(agent_id)
    elif status:
        tasks = [t for t in tb.tasks.values() if t.status.value == status]
    else:
        tasks = list(tb.tasks.values())
    
    return {
        "tasks": [t.to_dict() for t in tasks[:limit]],
        "count": len(tasks)
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    tb = get_task_bidding()
    task = tb.get_task(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


@router.post("/tasks/complete")
async def complete_task(request: CompleteTaskRequest):
    tb = get_task_bidding()
    
    success = tb.complete_task(
        task_id=request.task_id,
        agent_id=request.agent_id,
        result=request.result,
        success=request.success
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to complete task")
    
    return {"success": True, "task_id": request.task_id}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, reason: str = ""):
    tb = get_task_bidding()
    
    success = tb.cancel_task(task_id, reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"success": True, "task_id": task_id}


@router.post("/teams/form")
async def form_team(request: FormTeamRequest):
    global team_formation
    if team_formation is None:
        team_formation = DynamicTeamFormation(get_task_bidding(), get_blackboard())
    
    team_id = team_formation.form_team(
        team_name=request.team_name,
        task_id=request.task_id,
        agent_ids=request.agent_ids,
        leader_id=request.leader_id
    )
    
    return {"team_id": team_id, "status": "formed"}


@router.get("/teams")
async def get_teams():
    global team_formation
    if team_formation is None:
        team_formation = DynamicTeamFormation(get_task_bidding(), get_blackboard())
    
    teams = team_formation.get_active_teams()
    return {"teams": teams, "count": len(teams)}


@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    global team_formation
    if team_formation is None:
        team_formation = DynamicTeamFormation(get_task_bidding(), get_blackboard())
    
    team = team_formation.get_team(team_id)
    
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team


@router.post("/teams/{team_id}/dissolve")
async def dissolve_team(team_id: str, reason: str = ""):
    global team_formation
    if team_formation is None:
        team_formation = DynamicTeamFormation(get_task_bidding(), get_blackboard())
    
    team_formation.dissolve_team(team_id, reason)
    
    return {"success": True, "team_id": team_id}


@router.get("/rewards/goals")
async def get_reward_goals():
    rf = get_reward_field()
    return rf.get_goal_status()


@router.get("/rewards/agent/{agent_id}")
async def get_agent_reward(agent_id: str):
    rf = get_reward_field()
    reward = rf.get_agent_reward(agent_id)
    history = rf.get_agent_reward_history(agent_id)
    
    return {
        "agent_id": agent_id,
        "total_reward": reward,
        "recent_history": history[-10:]
    }


@router.get("/rewards/top-performers")
async def get_top_performers(limit: int = Query(10, ge=1, le=50)):
    rf = get_reward_field()
    performers = rf.get_top_performers(limit)
    
    return {
        "performers": [
            {"agent_id": aid, "reward": r}
            for aid, r in performers
        ]
    }


@router.get("/emergence/analyze")
async def analyze_emergence():
    ea = get_emergence_analyzer()
    analysis = ea.analyze_emergence()
    
    return analysis


@router.get("/emergence/patterns")
async def get_emergence_patterns():
    ea = get_emergence_analyzer()
    patterns = ea.get_detected_patterns()
    
    return {"patterns": patterns, "count": len(patterns)}


@router.get("/emergence/graph")
async def get_interaction_graph():
    ea = get_emergence_analyzer()
    graph = ea.get_interaction_graph()
    
    return graph


@router.post("/agents/register")
async def register_agent(request: RegisterAgentRequest):
    rep = get_reproduction()
    
    class DummyModel:
        def parameters(self):
            return []
        def named_modules(self):
            return []
    
    genome = rep.register_agent(
        agent_id=request.agent_id,
        model=DummyModel(),
        parent_ids=request.parent_ids,
        generation=request.generation
    )
    
    return {"genome_id": genome.genome_id, "agent_id": request.agent_id}


@router.get("/agents/{agent_id}/genome")
async def get_agent_genome(agent_id: str):
    rep = get_reproduction()
    genome = rep.get_genome(agent_id)
    
    if genome is None:
        raise HTTPException(status_code=404, detail="Genome not found")
    
    return genome.to_dict()


@router.get("/agents/{agent_id}/ancestry")
async def get_agent_ancestry(agent_id: str, generations: int = Query(5, ge=1, le=10)):
    rep = get_reproduction()
    ancestry = rep.get_ancestry(agent_id, generations)
    
    return {"agent_id": agent_id, "ancestry": ancestry}


@router.get("/agents/{agent_id}/descendants")
async def get_agent_descendants(agent_id: str):
    rep = get_reproduction()
    descendants = rep.get_descendants(agent_id)
    
    return {"agent_id": agent_id, "descendants": descendants}


@router.post("/agents/reproduce/asexual")
async def reproduce_asexual(request: ReproduceRequest):
    rep = get_reproduction()
    
    class DummyModel:
        def parameters(self):
            return []
        def named_modules(self):
            return []
        def named_parameters(self):
            return []
    
    model, genome = rep.reproduce_asexual(
        parent_id=request.parent_id,
        parent_model=DummyModel(),
        offspring_id=request.offspring_id
    )
    
    if genome is None:
        raise HTTPException(status_code=400, detail="Reproduction failed")
    
    return {
        "offspring_id": request.offspring_id,
        "genome_id": genome.genome_id,
        "generation": genome.generation
    }


@router.post("/selection/fitness")
async def record_fitness(request: RecordFitnessRequest):
    global selection
    if selection is None:
        selection = MutationSelection(get_reproduction(), get_blackboard())
    
    selection.record_fitness(request.agent_id, request.fitness)
    
    return {"success": True, "agent_id": request.agent_id}


@router.post("/selection/run")
async def run_selection(agent_ids: List[str]):
    global selection
    if selection is None:
        selection = MutationSelection(get_reproduction(), get_blackboard())
    
    survivors, eliminated = selection.run_selection(agent_ids)
    
    return {
        "survivors": survivors,
        "eliminated": eliminated,
        "elite": list(selection.elite_agents)
    }


@router.get("/selection/stats")
async def get_selection_stats():
    global selection
    if selection is None:
        selection = MutationSelection(get_reproduction(), get_blackboard())
    
    return selection.get_population_stats()


@router.post("/safety/check")
async def check_action(request: CheckActionRequest):
    sf = get_safety_fence()
    
    approved, violations = sf.check_action(
        agent_id=request.agent_id,
        action=request.action,
        context=request.context
    )
    
    return {
        "approved": approved,
        "violations": [
            {
                "violation_id": v.violation_id,
                "constraint_id": v.constraint_id,
                "severity": v.severity.value
            }
            for v in violations
        ]
    }


@router.get("/safety/status")
async def get_safety_status():
    sf = get_safety_fence()
    return sf.get_status()


@router.post("/safety/emergency-stop")
async def trigger_emergency_stop(reason: str):
    sf = get_safety_fence()
    sf.trigger_emergency_stop(reason)
    
    return {"status": "emergency_stop_triggered", "reason": reason}


@router.post("/safety/emergency-stop/clear")
async def clear_emergency_stop(authorized_by: str):
    sf = get_safety_fence()
    success = sf.clear_emergency_stop(authorized_by)
    
    if not success:
        raise HTTPException(status_code=400, detail="No emergency stop active")
    
    return {"status": "emergency_stop_cleared", "authorized_by": authorized_by}


@router.post("/safety/parliament/register")
async def register_parliament_member(agent_id: str):
    sf = get_safety_fence()
    sf.register_parliament_member(agent_id)
    
    return {"success": True, "agent_id": agent_id}


@router.post("/safety/judgment/vote")
async def vote_judgment(request: VoteJudgmentRequest):
    sf = get_safety_fence()
    
    success = sf.vote_judgment(
        judgment_id=request.judgment_id,
        voter_id=request.voter_id,
        vote=request.vote,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to vote")
    
    return {"success": True}


@router.get("/safety/constraints")
async def get_constraints():
    sf = get_safety_fence()
    
    return {
        "constraints": [c.to_dict() for c in sf.constraints.values()],
        "count": len(sf.constraints)
    }


@router.get("/environment/perceive")
async def perceive_environment():
    global environment
    if environment is None:
        environment = EnvironmentPerception(get_blackboard())
    
    return environment.perceive()


@router.get("/environment/anomaly")
async def detect_environment_anomaly():
    global environment
    if environment is None:
        environment = EnvironmentPerception(get_blackboard())
    
    is_anomaly, anomaly_type = environment.detect_anomaly()
    
    return {
        "is_anomaly": is_anomaly,
        "anomaly_type": anomaly_type
    }


@router.on_event("startup")
async def startup_living_system():
    get_blackboard()
    get_task_bidding()
    get_reward_field()
    get_emergence_analyzer()
    get_reproduction()
    get_safety_fence()
    
    logger.info("Living Agent System started")


@router.on_event("shutdown")
async def shutdown_living_system():
    global blackboard, emergence_analyzer, environment
    
    if emergence_analyzer:
        emergence_analyzer.stop()
    
    if environment:
        environment.stop()
    
    # Blackboard doesn't have disconnect method, just clear data
    
    logger.info("Living Agent System stopped")
