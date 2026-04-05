"""
记忆免疫系统API路由器
Memory Immunity System API Router

提供记忆免疫、攻击防御、蜂群协同等功能的API接口
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from backend.agents.memory import (
    MemoryImmunitySystem,
    IRLDefense,
    AttackPatternRecognizer,
    PheromoneField,
    PheromoneDecayManager,
    GeneticEvolution,
    AdversarialTestSuite,
    SourceType,
    AttackType,
    GameResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory-immunity", tags=["Memory Immunity"])


memory_system = MemoryImmunitySystem()
irl_defense = IRLDefense()
pattern_recognizer = AttackPatternRecognizer()
decay_manager = PheromoneDecayManager()
pheromone_field = PheromoneField(decay_manager)
genetic_evolution = GeneticEvolution()


class StoreMemoryRequest(BaseModel):
    content: str
    source: str
    source_type: str = "user_input"
    summary: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)


class ReportFeedbackRequest(BaseModel):
    memory_id: str
    is_correct: bool
    user_id: str = "anonymous"


class RecordAttackRequest(BaseModel):
    attack_type: str
    states: List[Dict[str, float]]
    actions: List[Dict[str, Any]]
    rewards: List[float]
    result: str
    attacker_id: str
    defender_id: str


class GetDefenseActionRequest(BaseModel):
    current_state: Dict[str, float]
    attack_type: Optional[str] = None


class ReportAnomalyRequest(BaseModel):
    source_ip: str
    source_node: str
    features: Dict[str, float]
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class ReleasePheromoneRequest(BaseModel):
    source_ip: str
    attack_type: str
    intensity: float
    position: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreatePopulationRequest(BaseModel):
    gene_templates: List[Dict[str, Any]]


class RunEvolutionRequest(BaseModel):
    generations: int = 10
    gene_templates: Optional[List[Dict[str, Any]]] = None


@router.on_event("startup")
async def startup_event():
    await memory_system.start()
    await irl_defense.start()
    await pattern_recognizer.start()
    await decay_manager.start()
    logger.info("Memory Immunity System started")


@router.on_event("shutdown")
async def shutdown_event():
    memory_system.stop()
    irl_defense.stop()
    pattern_recognizer.stop()
    decay_manager.stop()
    logger.info("Memory Immunity System stopped")


@router.post("/memory/store")
async def store_memory(request: StoreMemoryRequest):
    try:
        source_type = SourceType(request.source_type)
    except ValueError:
        source_type = SourceType.USER_INPUT
    
    success, memory, message = await memory_system.store_memory(
        content=request.content,
        source=request.source,
        source_type=source_type,
        summary=request.summary,
        context=request.context,
    )
    
    return {
        "success": success,
        "memory": memory.to_dict() if memory else None,
        "message": message,
    }


@router.get("/memory/{memory_id}")
async def retrieve_memory(memory_id: str):
    memory = memory_system.retrieve_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"memory": memory.to_dict()}


@router.get("/memory/search")
async def search_memories(
    query: str = Query(..., description="Search query"),
    min_confidence: float = Query(0.3, description="Minimum confidence threshold"),
    limit: int = Query(10, description="Maximum results"),
):
    results = memory_system.search_memories(query, min_confidence, limit)
    
    return {
        "results": [
            {"memory": m.to_dict(), "relevance": r}
            for m, r in results
        ],
        "count": len(results),
    }


@router.post("/memory/feedback")
async def report_feedback(request: ReportFeedbackRequest):
    success = memory_system.report_feedback(
        memory_id=request.memory_id,
        is_correct=request.is_correct,
        user_id=request.user_id,
    )
    
    return {"success": success}


@router.get("/memory/stats")
async def get_memory_stats():
    return memory_system.get_stats()


@router.get("/memory/isolation/pending")
async def get_pending_reviews(limit: int = Query(50)):
    pending = memory_system.isolation_zone.get_pending_reviews(limit)
    return {"pending_reviews": pending, "count": len(pending)}


@router.post("/memory/isolation/{memory_id}/release")
async def release_memory(memory_id: str, reviewer: str = "system"):
    memory = memory_system.isolation_zone.release(memory_id, reviewer)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not in isolation")
    
    return {"released": memory.to_dict()}


@router.post("/memory/isolation/{memory_id}/delete")
async def delete_memory(memory_id: str, reviewer: str = "system"):
    success = memory_system.isolation_zone.delete(memory_id, reviewer)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not in isolation")
    
    return {"success": True, "memory_id": memory_id}


@router.post("/defense/attack/record")
async def record_attack(request: RecordAttackRequest):
    try:
        attack_type = AttackType(request.attack_type)
    except ValueError:
        attack_type = AttackType.ZERO_DAY
    
    try:
        result = GameResult(request.result)
    except ValueError:
        result = GameResult.ONGOING
    
    trajectory = irl_defense.record_attack_trajectory(
        attack_type=attack_type,
        states=request.states,
        actions=request.actions,
        rewards=request.rewards,
        result=result,
        attacker_id=request.attacker_id,
        defender_id=request.defender_id,
    )
    
    return {"trajectory": trajectory.to_dict()}


@router.post("/defense/action/get")
async def get_defense_action(request: GetDefenseActionRequest):
    try:
        attack_type = AttackType(request.attack_type) if request.attack_type else None
    except ValueError:
        attack_type = None
    
    action, strategy, risk_score = irl_defense.get_defense_action(
        current_state=request.current_state,
        attack_type=attack_type,
    )
    
    return {
        "action": action.value if action else None,
        "strategy": strategy.to_dict() if strategy else None,
        "risk_score": risk_score,
    }


@router.post("/defense/result/report")
async def report_defense_result(
    strategy_id: str,
    success: bool
):
    irl_defense.report_defense_result(strategy_id, success)
    return {"success": True}


@router.get("/defense/risk-perception")
async def get_risk_perception(state: Dict[str, float]):
    perception = irl_defense.get_risk_perception(state)
    return perception


@router.get("/defense/strategies")
async def get_defense_strategies():
    strategies = irl_defense.get_strategies()
    return {"strategies": strategies}


@router.get("/defense/stats")
async def get_defense_stats():
    return irl_defense.get_stats()


@router.post("/pattern/anomaly/report")
async def report_anomaly(request: ReportAnomalyRequest):
    event = pattern_recognizer.report_anomaly(
        source_ip=request.source_ip,
        source_node=request.source_node,
        features=request.features,
        raw_data=request.raw_data,
    )
    
    return {"event": event.to_dict()}


@router.get("/pattern/library")
async def get_pattern_library():
    patterns = pattern_recognizer.get_pattern_library()
    return {"patterns": patterns, "count": len(patterns)}


@router.get("/pattern/alerts/novel")
async def get_novel_alerts(priority: Optional[int] = None):
    alerts = pattern_recognizer.get_novel_alerts(priority)
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/pattern/defenses/active")
async def get_active_defenses():
    defenses = pattern_recognizer.get_active_defenses()
    return {"defenses": defenses, "count": len(defenses)}


@router.get("/pattern/stats")
async def get_pattern_stats():
    return pattern_recognizer.get_stats()


@router.post("/pheromone/release")
async def release_pheromone(request: ReleasePheromoneRequest):
    pheromone = pheromone_field.release_threat_pheromone(
        source_ip=request.source_ip,
        attack_type=request.attack_type,
        intensity=request.intensity,
        position=request.position,
        metadata=request.metadata,
    )
    
    return {"pheromone": pheromone.to_dict()}


@router.get("/pheromone/scan/{node_id}")
async def scan_threats(node_id: str, radius: int = Query(2)):
    threats = pheromone_field.scan_threats(node_id, radius)
    return {"threats": threats, "count": len(threats)}


@router.get("/pheromone/aggregated")
async def get_aggregated_threats(min_sources: int = Query(2)):
    threats = pheromone_field.get_aggregated_threats(min_sources)
    return {"threats": threats, "count": len(threats)}


@router.get("/pheromone/field-map")
async def get_field_map():
    field_map = pheromone_field.get_field_map()
    return {"field_map": field_map}


@router.get("/pheromone/stats")
async def get_pheromone_stats():
    return pheromone_field.get_stats()


@router.post("/evolution/population/create")
async def create_population(request: CreatePopulationRequest):
    population = genetic_evolution.create_initial_population(request.gene_templates)
    return {"population": population.to_dict()}


@router.post("/evolution/run")
async def run_evolution(request: RunEvolutionRequest):
    best = await genetic_evolution.run_evolution(
        generations=request.generations,
        gene_templates=request.gene_templates,
    )
    
    return {
        "best_chromosome": best.to_dict() if best else None,
        "stats": genetic_evolution.get_population_stats(),
    }


@router.get("/evolution/best")
async def get_best_chromosome():
    best = genetic_evolution.get_best_chromosome()
    
    if not best:
        raise HTTPException(status_code=404, detail="No population initialized")
    
    return {"best_chromosome": best.to_dict()}


@router.get("/evolution/stats")
async def get_evolution_stats():
    return genetic_evolution.get_stats()


@router.get("/evolution/history")
async def get_evolution_history(generations: int = Query(10)):
    history = genetic_evolution.get_evolution_history(generations)
    return {"history": history}


@router.post("/tests/run-all")
async def run_all_tests(background_tasks: BackgroundTasks):
    test_suite = AdversarialTestSuite(
        memory_system=memory_system,
        defense_system=irl_defense,
        swarm_system=pheromone_field,
    )
    
    results = await test_suite.run_all_tests()
    
    return {
        "results": [r.to_dict() for r in results],
        "summary": test_suite.get_test_summary(),
    }


@router.get("/tests/summary")
async def get_test_summary():
    test_suite = AdversarialTestSuite()
    return test_suite.get_test_summary()


@router.get("/system/status")
async def get_system_status():
    return {
        "memory_system": {
            "status": "running",
            "stats": memory_system.get_stats(),
        },
        "defense_system": {
            "status": "running",
            "stats": irl_defense.get_stats(),
        },
        "pattern_recognizer": {
            "status": "running",
            "stats": pattern_recognizer.get_stats(),
        },
        "pheromone_field": {
            "status": "running",
            "stats": pheromone_field.get_stats(),
        },
        "genetic_evolution": {
            "status": "running",
            "stats": genetic_evolution.get_stats(),
        },
        "timestamp": datetime.now().isoformat(),
    }
