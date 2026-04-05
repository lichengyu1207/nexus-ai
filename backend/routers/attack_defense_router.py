"""
攻击防御智能体集群路由器
提供攻防训练、模拟、状态查询等API接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import time
import logging

from backend.agents.attack_defense import (
    AttackType,
    DefenseAction,
    AttackIntensity,
    BattleResult,
    AttackPattern,
    DefenseStrategy,
    BattleRecord,
    AttackAgent,
    DefenseAgent,
    BattleArena,
    CoEvolutionEngine,
    WarCenter,
    AttackDefenseCluster
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/attack-defense", tags=["attack-defense"])

_cluster_instances: Dict[str, AttackDefenseCluster] = {}


class CreateClusterRequest(BaseModel):
    cluster_id: str = Field(..., description="集群ID")
    attacker_count: int = Field(default=10, description="攻击智能体数量")
    defender_count: int = Field(default=10, description="防御智能体数量")


class SimulateAttackRequest(BaseModel):
    cluster_id: str = Field(..., description="集群ID")
    attack_type: str = Field(default="ddos", description="攻击类型")
    target: str = Field(default="test_target", description="攻击目标")
    environment: Dict[str, Any] = Field(default_factory=lambda: {"defense_level": 0.5})


class RunTrainingRequest(BaseModel):
    cluster_id: str = Field(..., description="集群ID")
    generations: int = Field(default=10, description="进化代数")
    environment: Dict[str, Any] = Field(default_factory=lambda: {"defense_level": 0.5, "target": "training_target"})


class DetectAttackRequest(BaseModel):
    cluster_id: str = Field(..., description="集群ID")
    traffic_data: Dict[str, Any] = Field(..., description="流量数据")
    baseline: Dict[str, float] = Field(default_factory=lambda: {"request_rate": 100.0, "error_rate": 0.01})


@router.post("/cluster/create")
async def create_cluster(request: CreateClusterRequest):
    try:
        if request.cluster_id in _cluster_instances:
            raise HTTPException(status_code=400, detail=f"Cluster {request.cluster_id} already exists")
        cluster = AttackDefenseCluster(request.cluster_id)
        cluster.initialize(request.attacker_count, request.defender_count)
        _cluster_instances[request.cluster_id] = cluster
        return {
            "success": True,
            "cluster_id": request.cluster_id,
            "status": cluster.get_cluster_status()
        }
    except Exception as e:
        logger.error(f"Failed to create cluster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/{cluster_id}/status")
async def get_cluster_status(cluster_id: str):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return cluster.get_cluster_status()


@router.delete("/cluster/{cluster_id}")
async def delete_cluster(cluster_id: str):
    if cluster_id not in _cluster_instances:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    del _cluster_instances[cluster_id]
    return {"success": True, "message": f"Cluster {cluster_id} deleted"}


@router.get("/clusters")
async def list_clusters():
    return {
        "clusters": [
            {"cluster_id": cid, "status": cluster.get_cluster_status()}
            for cid, cluster in _cluster_instances.items()
        ]
    }


@router.post("/training/run")
async def run_training(request: RunTrainingRequest):
    cluster = _cluster_instances.get(request.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {request.cluster_id} not found")
    try:
        results = cluster.run_training(request.generations, request.environment)
        return {
            "success": True,
            "cluster_id": request.cluster_id,
            "generations_completed": len(results),
            "final_status": cluster.get_cluster_status(),
            "evolution_history": results
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attack/simulate")
async def simulate_attack(request: SimulateAttackRequest):
    cluster = _cluster_instances.get(request.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {request.cluster_id} not found")
    try:
        attack_type = AttackType(request.attack_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid attack type: {request.attack_type}")
    try:
        result = cluster.simulate_attack(attack_type, request.target, request.environment)
        return {
            "success": True,
            "cluster_id": request.cluster_id,
            "simulation_result": result
        }
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attack/detect")
async def detect_attack(request: DetectAttackRequest):
    cluster = _cluster_instances.get(request.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {request.cluster_id} not found")
    try:
        attack = cluster.war_center.detect_attack(request.traffic_data, request.baseline)
        if attack:
            cluster.war_center.activate_battle_mode(attack)
            defense = cluster.war_center.coordinate_defense(attack, request.traffic_data)
            return {
                "attack_detected": True,
                "attack": attack.to_dict(),
                "defense_strategy": defense.to_dict(),
                "threat_level": cluster.war_center.threat_level,
                "battle_mode": cluster.war_center.battle_mode
            }
        return {
            "attack_detected": False,
            "threat_level": cluster.war_center.threat_level,
            "battle_mode": cluster.war_center.battle_mode
        }
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/war-center/{cluster_id}/deactivate")
async def deactivate_battle_mode(cluster_id: str):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    cluster.war_center.deactivate_battle_mode()
    return {
        "success": True,
        "battle_mode": False,
        "message": "Battle mode deactivated"
    }


@router.get("/war-center/{cluster_id}/status")
async def get_war_center_status(cluster_id: str):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return cluster.war_center.get_status()


@router.get("/agents/{cluster_id}/best")
async def get_best_agents(cluster_id: str):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return cluster.evolution_engine.get_best_agents()


@router.get("/agents/{cluster_id}/attackers")
async def list_attackers(cluster_id: str, alive_only: bool = Query(True)):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    attackers = [
        attacker.get_status()
        for attacker in cluster.attackers.values()
        if not alive_only or attacker.is_alive
    ]
    return {
        "cluster_id": cluster_id,
        "total_count": len(cluster.attackers),
        "alive_count": len([a for a in cluster.attackers.values() if a.is_alive]),
        "attackers": attackers
    }


@router.get("/agents/{cluster_id}/defenders")
async def list_defenders(cluster_id: str, alive_only: bool = Query(True)):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    defenders = [
        defender.get_status()
        for defender in cluster.defenders.values()
        if not alive_only or defender.is_alive
    ]
    return {
        "cluster_id": cluster_id,
        "total_count": len(cluster.defenders),
        "alive_count": len([d for d in cluster.defenders.values() if d.is_alive]),
        "defenders": defenders
    }


@router.get("/battles/{cluster_id}/history")
async def get_battle_history(cluster_id: str, limit: int = Query(100)):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    records = [record.to_dict() for record in cluster.battle_records[-limit:]]
    return {
        "cluster_id": cluster_id,
        "total_battles": len(cluster.battle_records),
        "records": records
    }


@router.get("/attack-types")
async def list_attack_types():
    return {
        "attack_types": [
            {"value": t.value, "name": t.name}
            for t in AttackType
        ]
    }


@router.get("/defense-actions")
async def list_defense_actions():
    return {
        "defense_actions": [
            {"value": a.value, "name": a.name}
            for a in DefenseAction
        ]
    }


@router.get("/intensities")
async def list_intensities():
    return {
        "intensities": [
            {"value": i.value, "name": i.name}
            for i in AttackIntensity
        ]
    }


@router.get("/arena/{cluster_id}/stats")
async def get_arena_stats(cluster_id: str):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return cluster.evolution_engine.arena.get_stats()


@router.post("/arena/{cluster_id}/tournament")
async def run_tournament(
    cluster_id: str,
    rounds: int = Query(10, description="对战轮数")
):
    cluster = _cluster_instances.get(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    try:
        records = cluster.evolution_engine.arena.run_tournament(rounds=rounds)
        return {
            "success": True,
            "rounds_played": len(records),
            "records": [r.to_dict() for r in records],
            "arena_stats": cluster.evolution_engine.arena.get_stats()
        }
    except Exception as e:
        logger.error(f"Tournament failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
