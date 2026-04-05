"""
全链路智能体监控API路由
Full-Chain Agent Monitoring Router

提供智能体集群、黑板、消息总线、进化系统等全链路监控接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fullchain", tags=["fullchain"])


class AgentCreateRequest(BaseModel):
    species: str
    name: str
    initial_energy: float = 100.0


class MessageSendRequest(BaseModel):
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any]


class BlackboardWriteRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None
    agent_id: str = "api"


@router.get("/overview")
async def get_overview() -> Dict[str, Any]:
    """获取全链路系统概览"""
    from ..agents.living import agent_registry, blackboard, message_bus
    
    registry_stats = agent_registry.get_stats()
    
    return {
        "timestamp": time.time(),
        "registry": registry_stats,
        "blackboard": {
            "total_keys": len(blackboard.get_all_keys()),
            "keys": blackboard.get_all_keys()[:50]
        },
        "message_bus": {
            "registered_agents": len(message_bus._queues)
        }
    }


@router.get("/agents")
async def list_agents(
    species: Optional[str] = None,
    state: Optional[str] = None
) -> List[Dict[str, Any]]:
    """列出所有智能体"""
    from ..agents.living import agent_registry, AgentSpecies, AgentState
    
    agents = agent_registry.get_all()
    
    if species:
        try:
            species_enum = AgentSpecies(species)
            agents = [a for a in agents if a.species == species_enum]
        except ValueError:
            pass
    
    if state:
        agents = [a for a in agents if a.state.value == state]
    
    return [a.get_status() for a in agents]


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """获取单个智能体详情"""
    from ..agents.living import agent_registry
    
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_status()


@router.post("/agents/{agent_id}/energy")
async def modify_energy(
    agent_id: str,
    amount: float,
    reason: str = "api_adjustment"
) -> Dict[str, Any]:
    """调整智能体能量"""
    from ..agents.living import agent_registry
    
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if amount >= 0:
        agent.gain_energy(amount, reason)
    else:
        agent.consume_energy(abs(amount), reason)
    
    return {"success": True, "energy": agent.energy_system.get_level()}


@router.post("/agents/{agent_id}/reproduce")
async def trigger_reproduction(agent_id: str) -> Dict[str, Any]:
    """触发智能体繁殖"""
    from ..agents.living import agent_registry
    
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.can_reproduce():
        return {
            "success": False,
            "reason": "Agent cannot reproduce (insufficient energy or experience)"
        }
    
    child = await agent.reproduce()
    if child:
        agent_registry.register(child)
        return {
            "success": True,
            "child_id": child.agent_id,
            "child_name": child.name
        }
    
    return {"success": False, "reason": "Reproduction failed"}


@router.get("/blackboard")
async def list_blackboard_keys() -> Dict[str, Any]:
    """列出黑板所有键"""
    from ..agents.living import blackboard
    
    keys = blackboard.get_all_keys()
    
    entries = []
    for key in keys[:100]:
        value = blackboard.read(key)
        entries.append({
            "key": key,
            "value": str(value)[:200] if value else None
        })
    
    return {
        "total_keys": len(keys),
        "entries": entries
    }


@router.get("/blackboard/{key:path}")
async def read_blackboard(key: str) -> Dict[str, Any]:
    """读取黑板值"""
    from ..agents.living import blackboard
    
    value = blackboard.read(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found or expired")
    
    return {"key": key, "value": value}


@router.post("/blackboard")
async def write_blackboard(request: BlackboardWriteRequest) -> Dict[str, Any]:
    """写入黑板"""
    from ..agents.living import blackboard
    
    success = blackboard.write(request.key, request.value, request.ttl, request.agent_id)
    return {"success": success, "key": request.key}


@router.delete("/blackboard/{key:path}")
async def delete_blackboard(key: str) -> Dict[str, Any]:
    """删除黑板键"""
    from ..agents.living import blackboard
    
    success = blackboard.delete(key)
    return {"success": success, "key": key}


@router.get("/blackboard/search/{query}")
async def search_blackboard(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """搜索黑板"""
    from ..agents.living import blackboard
    
    results = blackboard.search(query, limit)
    return results


@router.get("/messages/{agent_id}")
async def get_messages(agent_id: str) -> List[Dict[str, Any]]:
    """获取智能体消息队列"""
    from ..agents.living import message_bus
    
    messages = []
    while True:
        msg = message_bus.receive(agent_id)
        if msg is None:
            break
        messages.append(msg.to_dict())
    
    return messages


@router.post("/messages")
async def send_message(request: MessageSendRequest) -> Dict[str, Any]:
    """发送消息"""
    from ..agents.living import message_bus, AgentMessage
    
    message = AgentMessage(
        from_agent=request.from_agent,
        to_agent=request.to_agent,
        message_type=request.message_type,
        payload=request.payload
    )
    
    success = message_bus.send(message)
    return {"success": success, "message_id": message.message_id}


@router.post("/broadcast")
async def broadcast_message(
    from_agent: str,
    message_type: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """广播消息"""
    from ..agents.living import message_bus
    
    message_bus.broadcast(from_agent, message_type, payload)
    return {"success": True}


@router.get("/diagnoses")
async def get_diagnoses() -> List[Dict[str, Any]]:
    """获取所有诊断记录"""
    from ..agents.living import blackboard
    
    diagnoses = []
    for key in blackboard.get_all_keys():
        if key.startswith("diagnosis/"):
            value = blackboard.read(key)
            if value:
                diagnoses.append({
                    "agent_id": key.replace("diagnosis/", ""),
                    **value
                })
    
    return diagnoses


@router.get("/reproductions")
async def get_reproductions() -> List[Dict[str, Any]]:
    """获取繁殖记录"""
    from ..agents.living import blackboard
    
    reproductions = []
    for key in blackboard.get_all_keys():
        if key.startswith("reproduction/"):
            value = blackboard.read(key)
            if value:
                reproductions.append(value)
    
    return reproductions


@router.get("/deaths")
async def get_deaths() -> List[Dict[str, Any]]:
    """获取死亡记录"""
    from ..agents.living import blackboard
    
    deaths = []
    for key in blackboard.get_all_keys():
        if key.startswith("death/"):
            value = blackboard.read(key)
            if value:
                deaths.append(value)
    
    return deaths


@router.get("/species/{species}/stats")
async def get_species_stats(species: str) -> Dict[str, Any]:
    """获取特定物种统计"""
    from ..agents.living import agent_registry, AgentSpecies
    
    try:
        species_enum = AgentSpecies(species)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid species: {species}")
    
    agents = agent_registry.get_by_species(species_enum)
    
    if not agents:
        return {
            "species": species,
            "count": 0,
            "stats": {}
        }
    
    total_energy = sum(a.energy_system.get_level() for a in agents)
    total_tasks = sum(a.stats["tasks_completed"] for a in agents)
    total_failed = sum(a.stats["tasks_failed"] for a in agents)
    
    state_dist = {}
    for a in agents:
        state = a.state.value
        state_dist[state] = state_dist.get(state, 0) + 1
    
    return {
        "species": species,
        "count": len(agents),
        "total_energy": total_energy,
        "avg_energy": total_energy / len(agents),
        "total_tasks_completed": total_tasks,
        "total_tasks_failed": total_failed,
        "success_rate": total_tasks / (total_tasks + total_failed) if (total_tasks + total_failed) > 0 else 0,
        "state_distribution": state_dist,
        "agents": [a.agent_id for a in agents]
    }


@router.get("/energy-flow")
async def get_energy_flow() -> Dict[str, Any]:
    """获取能量流动统计"""
    from ..agents.living import agent_registry
    
    agents = agent_registry.get_all()
    
    total_energy = sum(a.energy_system.get_level() for a in agents)
    max_energy = sum(a.energy_system.max_energy for a in agents)
    
    species_energy = {}
    for a in agents:
        species = a.species.value
        species_energy[species] = species_energy.get(species, 0) + a.energy_system.get_level()
    
    return {
        "total_energy": total_energy,
        "max_possible_energy": max_energy,
        "utilization": total_energy / max_energy if max_energy > 0 else 0,
        "species_energy": species_energy,
        "hibernating_count": sum(1 for a in agents if a.energy_system.is_hibernating()),
        "reproducible_count": sum(1 for a in agents if a.can_reproduce())
    }


@router.post("/cleanup")
async def cleanup_expired() -> Dict[str, Any]:
    """清理过期数据"""
    from ..agents.living import blackboard
    
    expired_count = blackboard.cleanup_expired()
    
    return {
        "success": True,
        "expired_blackboard_entries": expired_count
    }
