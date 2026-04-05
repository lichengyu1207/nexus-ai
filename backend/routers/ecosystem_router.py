"""
活体智能体生态系统API路由
Living Agent Ecosystem API Router

提供活体智能体生态系统的完整API接口
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

from ..agents.ecosystem import (
    LivingAgent,
    LivingAttackAgent,
    LivingDefenseAgent,
    LivingMemoryAgent,
    EcosystemCoordinator,
    AgentRole,
    AgentStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ecosystem", tags=["ecosystem"])

ecosystem: Optional[EcosystemCoordinator] = None


class SpawnAgentRequest(BaseModel):
    agent_type: str = Field(..., description="Agent type: attack, defense, memory")
    species: str = Field(default="default", description="Agent species")
    parent_ids: List[str] = Field(default_factory=list, description="Parent agent IDs")


class AttackRequest(BaseModel):
    agent_id: str
    target: Dict
    strategy: Optional[str] = None


class DefenseRequest(BaseModel):
    agent_id: str
    threat: Dict
    strategy: Optional[str] = None


class MemoryStoreRequest(BaseModel):
    agent_id: str
    key: str
    value: Dict
    memory_type: str = Field(default="episodic")
    importance: float = Field(default=0.5, ge=0, le=1)
    tags: List[str] = Field(default_factory=list)
    ttl: Optional[int] = None


class MemoryRetrieveRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)


class ReproduceRequest(BaseModel):
    agent_id: str
    agent_type: str
    partner_id: Optional[str] = None


def get_ecosystem() -> EcosystemCoordinator:
    global ecosystem
    if ecosystem is None:
        from ..agents.living import global_blackboard
        ecosystem = EcosystemCoordinator(
            blackboard=global_blackboard,
            communication=None
        )
        ecosystem.start()
    return ecosystem


@router.get("/status")
async def get_ecosystem_status():
    eco = get_ecosystem()
    return eco.get_status()


@router.get("/agents")
async def get_agents(
    agent_type: Optional[str] = Query(None, description="Filter by type: attack, defense, memory"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200)
):
    eco = get_ecosystem()
    agents = eco.get_agent_states(agent_type)
    
    if status:
        agents = [a for a in agents if a.get("status") == status]
    
    return {
        "agents": agents[:limit],
        "total": len(agents)
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    eco = get_ecosystem()
    
    if agent_id in eco.attack_agents:
        return eco.attack_agents[agent_id].get_state()
    elif agent_id in eco.defense_agents:
        return eco.defense_agents[agent_id].get_state()
    elif agent_id in eco.memory_agents:
        return eco.memory_agents[agent_id].get_state()
    else:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/agents/spawn")
async def spawn_agent(request: SpawnAgentRequest):
    eco = get_ecosystem()
    
    if request.agent_type == "attack":
        agent = eco.spawn_attack_agent(
            species=request.species,
            parent_ids=request.parent_ids
        )
    elif request.agent_type == "defense":
        agent = eco.spawn_defense_agent(
            species=request.species,
            parent_ids=request.parent_ids
        )
    elif request.agent_type == "memory":
        agent = eco.spawn_memory_agent(species=request.species)
    else:
        raise HTTPException(status_code=400, detail="Invalid agent type")
    
    return {
        "agent_id": agent.agent_id,
        "type": request.agent_type,
        "status": "spawned"
    }


@router.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    eco = get_ecosystem()
    
    if agent_id in eco.attack_agents:
        eco.attack_agents[agent_id].stop()
    elif agent_id in eco.defense_agents:
        eco.defense_agents[agent_id].stop()
    elif agent_id in eco.memory_agents:
        eco.memory_agents[agent_id].stop()
    else:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"agent_id": agent_id, "status": "stopped"}


@router.post("/agents/{agent_id}/energy")
async def add_agent_energy(agent_id: str, amount: float):
    eco = get_ecosystem()
    
    if agent_id in eco.attack_agents:
        eco.attack_agents[agent_id].add_energy(amount)
    elif agent_id in eco.defense_agents:
        eco.defense_agents[agent_id].add_energy(amount)
    elif agent_id in eco.memory_agents:
        eco.memory_agents[agent_id].add_energy(amount)
    else:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"agent_id": agent_id, "energy_added": amount}


@router.post("/attack/execute")
async def execute_attack(request: AttackRequest):
    eco = get_ecosystem()
    
    if request.agent_id not in eco.attack_agents:
        raise HTTPException(status_code=404, detail="Attack agent not found")
    
    agent = eco.attack_agents[request.agent_id]
    
    if request.strategy:
        strategy = agent.strategy_library.get(request.strategy)
        if not strategy:
            raise HTTPException(status_code=400, detail="Strategy not found")
    else:
        strategy = agent._select_strategy(request.target)
    
    result = agent._execute_attack(request.target, strategy)
    
    return {
        "agent_id": request.agent_id,
        "result": result
    }


@router.get("/attack/strategies")
async def get_attack_strategies(agent_id: Optional[str] = None):
    eco = get_ecosystem()
    
    if agent_id:
        if agent_id not in eco.attack_agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "agent_id": agent_id,
            "strategies": eco.attack_agents[agent_id].strategy_library
        }
    else:
        all_strategies = {}
        for aid, agent in eco.attack_agents.items():
            all_strategies[aid] = list(agent.strategy_library.keys())
        return {"strategies_by_agent": all_strategies}


@router.post("/defense/execute")
async def execute_defense(request: DefenseRequest):
    eco = get_ecosystem()
    
    if request.agent_id not in eco.defense_agents:
        raise HTTPException(status_code=404, detail="Defense agent not found")
    
    agent = eco.defense_agents[request.agent_id]
    
    if request.strategy:
        strategy = agent.defense_strategies.get(request.strategy)
        if not strategy:
            raise HTTPException(status_code=400, detail="Strategy not found")
    else:
        strategy = agent._select_defense_strategy(request.threat)
    
    result = agent._execute_defense(request.threat, strategy)
    
    return {
        "agent_id": request.agent_id,
        "result": result
    }


@router.get("/defense/strategies")
async def get_defense_strategies(agent_id: Optional[str] = None):
    eco = get_ecosystem()
    
    if agent_id:
        if agent_id not in eco.defense_agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "agent_id": agent_id,
            "strategies": eco.defense_agents[agent_id].defense_strategies
        }
    else:
        all_strategies = {}
        for aid, agent in eco.defense_agents.items():
            all_strategies[aid] = list(agent.defense_strategies.keys())
        return {"strategies_by_agent": all_strategies}


@router.post("/memory/store")
async def store_memory(request: MemoryStoreRequest):
    eco = get_ecosystem()
    
    if request.agent_id not in eco.memory_agents:
        raise HTTPException(status_code=404, detail="Memory agent not found")
    
    from ..agents.ecosystem.living_memory_agent import MemoryType
    
    memory_type = MemoryType(request.memory_type)
    
    agent = eco.memory_agents[request.agent_id]
    memory_id = agent.store(
        key=request.key,
        value=request.value,
        memory_type=memory_type,
        importance=request.importance,
        tags=request.tags,
        ttl=request.ttl
    )
    
    return {
        "memory_id": memory_id,
        "agent_id": request.agent_id,
        "status": "stored"
    }


@router.post("/memory/retrieve")
async def retrieve_memory(request: MemoryRetrieveRequest, agent_id: Optional[str] = None):
    eco = get_ecosystem()
    
    if agent_id:
        if agent_id not in eco.memory_agents:
            raise HTTPException(status_code=404, detail="Memory agent not found")
        results = eco.memory_agents[agent_id].retrieve(
            query=request.query,
            top_k=request.top_k
        )
    else:
        results = []
        for agent in eco.memory_agents.values():
            results.extend(agent.retrieve(query=request.query, top_k=request.top_k // len(eco.memory_agents) if eco.memory_agents else request.top_k))
        results = results[:request.top_k]
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }


@router.post("/reproduction/asexual")
async def reproduce_asexual(request: ReproduceRequest):
    eco = get_ecosystem()
    
    if request.agent_type == "attack":
        if request.agent_id not in eco.attack_agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        parent = eco.attack_agents[request.agent_id]
        offspring_id = f"attack_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        offspring = parent.reproduce_asexual(offspring_id)
        if offspring:
            eco.attack_agents[offspring_id] = offspring
            offspring.start()
    elif request.agent_type == "defense":
        if request.agent_id not in eco.defense_agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        parent = eco.defense_agents[request.agent_id]
        offspring_id = f"defense_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        offspring = parent.reproduce_asexual(offspring_id)
        if offspring:
            eco.defense_agents[offspring_id] = offspring
            offspring.start()
    else:
        raise HTTPException(status_code=400, detail="Invalid agent type for reproduction")
    
    return {
        "parent_id": request.agent_id,
        "offspring_id": offspring_id,
        "status": "reproduced"
    }


@router.post("/reproduction/sexual")
async def reproduce_sexual(request: ReproduceRequest):
    eco = get_ecosystem()
    
    if not request.partner_id:
        raise HTTPException(status_code=400, detail="Partner ID required for sexual reproduction")
    
    if request.agent_type == "attack":
        if request.agent_id not in eco.attack_agents or request.partner_id not in eco.attack_agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        parent1 = eco.attack_agents[request.agent_id]
        parent2 = eco.attack_agents[request.partner_id]
        offspring_id = f"attack_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        offspring = parent1.reproduce_sexual(parent2, offspring_id)
        if offspring:
            eco.attack_agents[offspring_id] = offspring
            offspring.start()
    elif request.agent_type == "defense":
        if request.agent_id not in eco.defense_agents or request.partner_id not in eco.defense_agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        parent1 = eco.defense_agents[request.agent_id]
        parent2 = eco.defense_agents[request.partner_id]
        offspring_id = f"defense_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        offspring = parent1.reproduce_sexual(parent2, offspring_id)
        if offspring:
            eco.defense_agents[offspring_id] = offspring
            offspring.start()
    else:
        raise HTTPException(status_code=400, detail="Invalid agent type for reproduction")
    
    return {
        "parent_ids": [request.agent_id, request.partner_id],
        "offspring_id": offspring_id,
        "status": "reproduced"
    }


@router.get("/evolution/history")
async def get_evolution_history(limit: int = Query(100, ge=1, le=500)):
    eco = get_ecosystem()
    return {
        "history": eco.get_evolution_history(limit),
        "generation": eco.generation
    }


@router.get("/emergence/patterns")
async def get_emergence_patterns():
    eco = get_ecosystem()
    return {
        "patterns": eco.get_emergence_patterns(),
        "count": len(eco.emergence_patterns)
    }


@router.post("/selection/trigger")
async def trigger_selection():
    eco = get_ecosystem()
    eco._run_selection()
    return {
        "status": "selection_completed",
        "generation": eco.generation
    }


@router.post("/mutation/trigger")
async def trigger_mutation():
    eco = get_ecosystem()
    eco._run_mutation()
    return {
        "status": "mutation_completed",
        "generation": eco.generation
    }


@router.get("/metrics/history")
async def get_metrics_history(limit: int = Query(100, ge=1, le=500)):
    eco = get_ecosystem()
    return {
        "metrics": [m.__dict__ for m in list(eco.metrics_history)[-limit:]]
    }


@router.on_event("startup")
async def startup_ecosystem():
    get_ecosystem()
    logger.info("Living Agent Ecosystem started")


@router.on_event("shutdown")
async def shutdown_ecosystem():
    global ecosystem
    if ecosystem:
        ecosystem.stop()
    logger.info("Living Agent Ecosystem stopped")


import random
import time
import hashlib
