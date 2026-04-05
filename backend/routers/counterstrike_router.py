"""
反击系统API路由
Counterstrike System API Router

提供反击系统的完整API接口
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/counterstrike", tags=["counterstrike"])


class TrafficData(BaseModel):
    source_ip: str
    destination_ip: Optional[str] = None
    port: Optional[int] = None
    method: Optional[str] = None
    path: Optional[str] = None
    payload: Optional[str] = None
    headers: Optional[Dict] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None


class HoneypotCreate(BaseModel):
    honeypot_type: str
    attacker_profile: Optional[Dict] = None
    custom_config: Optional[Dict] = None


class CounterStrikeCreate(BaseModel):
    action_type: str
    target_identity: str
    target_ip: str
    parameters: Optional[Dict] = None
    severity: int = 2
    duration_hours: int = 24


class ApprovalRequest(BaseModel):
    request_id: str
    approver: str
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    request_id: str
    rejecter: str
    reason: str


class TacticCreate(BaseModel):
    name: str
    category: str
    description: str
    conditions: Dict
    parameters: Dict
    required_agents: Dict
    tags: List[str]


class PursuitCreate(BaseModel):
    target_identity: str
    target_ips: List[str]
    formation: str = "surround"
    priority: int = 1


command_center = None


def get_command_center():
    global command_center
    if command_center is None:
        from backend.agents.counterstrike.command_center import CounterStrikeCommandCenter
        command_center = CounterStrikeCommandCenter()
    return command_center


@router.on_event("startup")
async def startup():
    center = get_command_center()
    await center.start()


@router.on_event("shutdown")
async def shutdown():
    center = get_command_center()
    await center.stop()


@router.get("/status")
async def get_system_status():
    center = get_command_center()
    return await center.get_system_status()


@router.get("/stats")
async def get_system_stats():
    center = get_command_center()
    return center.get_stats()


@router.post("/traffic/process")
async def process_traffic(traffic: TrafficData, background_tasks: BackgroundTasks):
    center = get_command_center()
    result = await center.process_traffic(traffic.dict())
    return {"status": "processed", "result": result}


@router.get("/threats/active")
async def get_active_threats():
    center = get_command_center()
    return await center.get_active_threats()


@router.get("/assessments/recent")
async def get_recent_assessments(limit: int = Query(20, ge=1, le=100)):
    center = get_command_center()
    return await center.get_recent_assessments(limit)


@router.get("/recon/attackers")
async def get_all_attackers():
    center = get_command_center()
    recon = center.agents.get("recon")
    if not recon:
        raise HTTPException(status_code=404, detail="Recon agent not found")
    return await recon.get_all_attackers()


@router.get("/recon/reports")
async def get_recon_reports(limit: int = Query(20, ge=1, le=100)):
    center = get_command_center()
    recon = center.agents.get("recon")
    if not recon:
        raise HTTPException(status_code=404, detail="Recon agent not found")
    return await recon.get_recent_reports(limit)


@router.get("/trace/chains")
async def get_attack_chains(status: Optional[str] = None):
    center = get_command_center()
    trace = center.agents.get("trace")
    if not trace:
        raise HTTPException(status_code=404, detail="Trace agent not found")
    return await trace.get_all_chains(status)


@router.get("/trace/chains/{chain_id}")
async def get_attack_chain(chain_id: str):
    center = get_command_center()
    trace = center.agents.get("trace")
    if not trace:
        raise HTTPException(status_code=404, detail="Trace agent not found")
    chain = await trace.get_attack_chain(chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    return chain


@router.get("/trace/chains/{chain_id}/timeline")
async def get_chain_timeline(chain_id: str):
    center = get_command_center()
    trace = center.agents.get("trace")
    if not trace:
        raise HTTPException(status_code=404, detail="Trace agent not found")
    return await trace.get_chain_timeline(chain_id)


@router.get("/trace/chains/{chain_id}/graph")
async def get_chain_graph(chain_id: str):
    center = get_command_center()
    trace = center.agents.get("trace")
    if not trace:
        raise HTTPException(status_code=404, detail="Trace agent not found")
    graph = await trace.get_chain_graph(chain_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Chain not found")
    return graph


@router.post("/honeypot/create")
async def create_honeypot(config: HoneypotCreate):
    center = get_command_center()
    honeypot = center.agents.get("honeypot")
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot agent not found")
    
    from backend.agents.counterstrike.honeypot_agent import HoneypotType
    try:
        hp_type = HoneypotType(config.honeypot_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid honeypot type")
    
    result = await honeypot.create_honeypot(
        honeypot_type=hp_type,
        attacker_profile=config.attacker_profile,
        custom_config=config.custom_config
    )
    return result.to_dict()


@router.get("/honeypot/list")
async def list_honeypots():
    center = get_command_center()
    honeypot = center.agents.get("honeypot")
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot agent not found")
    return await honeypot.get_all_honeypots()


@router.get("/honeypot/{honeypot_id}")
async def get_honeypot(honeypot_id: str):
    center = get_command_center()
    honeypot = center.agents.get("honeypot")
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot agent not found")
    result = await honeypot.get_honeypot(honeypot_id)
    if not result:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    return result


@router.delete("/honeypot/{honeypot_id}")
async def shutdown_honeypot(honeypot_id: str):
    center = get_command_center()
    honeypot = center.agents.get("honeypot")
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot agent not found")
    success = await honeypot.shutdown_honeypot(honeypot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    return {"status": "shutdown", "honeypot_id": honeypot_id}


@router.get("/honeypot/credentials")
async def get_captured_credentials():
    center = get_command_center()
    honeypot = center.agents.get("honeypot")
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot agent not found")
    return await honeypot.get_captured_credentials()


@router.get("/attribution/identities")
async def get_all_identities():
    center = get_command_center()
    attribution = center.agents.get("attribution")
    if not attribution:
        raise HTTPException(status_code=404, detail="Attribution agent not found")
    return await attribution.get_all_identities()


@router.get("/attribution/identities/{identity_id}")
async def get_identity(identity_id: str):
    center = get_command_center()
    attribution = center.agents.get("attribution")
    if not attribution:
        raise HTTPException(status_code=404, detail="Attribution agent not found")
    result = await attribution.get_identity(identity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Identity not found")
    return result


@router.get("/attribution/blacklist")
async def get_blacklist():
    center = get_command_center()
    attribution = center.agents.get("attribution")
    if not attribution:
        raise HTTPException(status_code=404, detail="Attribution agent not found")
    return await attribution.get_blacklist()


@router.get("/attribution/watchlist")
async def get_watchlist():
    center = get_command_center()
    attribution = center.agents.get("attribution")
    if not attribution:
        raise HTTPException(status_code=404, detail="Attribution agent not found")
    return await attribution.get_watchlist()


@router.post("/counter-strike/create")
async def create_counter_strike(action: CounterStrikeCreate):
    center = get_command_center()
    counter_strike = center.agents.get("counter_strike")
    if not counter_strike:
        raise HTTPException(status_code=404, detail="Counter strike agent not found")
    
    from backend.agents.counterstrike.counter_strike_agent import CounterStrikeType, Severity
    try:
        action_type = CounterStrikeType(action.action_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid action type")
    
    try:
        severity = Severity(action.severity)
    except ValueError:
        severity = Severity.MEDIUM
    
    result = await counter_strike.create_action(
        action_type=action_type,
        target_identity=action.target_identity,
        target_ip=action.target_ip,
        parameters=action.parameters,
        severity=severity,
        duration_hours=action.duration_hours
    )
    return result.to_dict()


@router.post("/counter-strike/{action_id}/approve")
async def approve_counter_strike(action_id: str, request: ApprovalRequest):
    center = get_command_center()
    counter_strike = center.agents.get("counter_strike")
    if not counter_strike:
        raise HTTPException(status_code=404, detail="Counter strike agent not found")
    success = await counter_strike.approve_action(action_id, request.approver)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to approve action")
    return {"status": "approved", "action_id": action_id}


@router.get("/counter-strike/active")
async def get_active_counter_strikes():
    center = get_command_center()
    counter_strike = center.agents.get("counter_strike")
    if not counter_strike:
        raise HTTPException(status_code=404, detail="Counter strike agent not found")
    return await counter_strike.get_active_actions()


@router.get("/counter-strike/history")
async def get_counter_strike_history(limit: int = Query(50, ge=1, le=200)):
    center = get_command_center()
    counter_strike = center.agents.get("counter_strike")
    if not counter_strike:
        raise HTTPException(status_code=404, detail="Counter strike agent not found")
    return await counter_strike.get_action_history(limit)


@router.post("/pursuit/create")
async def create_pursuit(pursuit: PursuitCreate):
    center = get_command_center()
    pursuit_agent = center.agents.get("pursuit")
    if not pursuit_agent:
        raise HTTPException(status_code=404, detail="Pursuit agent not found")
    
    from backend.agents.counterstrike.pursuit_agent import FormationType
    try:
        formation = FormationType(pursuit.formation)
    except ValueError:
        formation = FormationType.SURROUND
    
    result = await pursuit_agent.create_pursuit(
        target_identity=pursuit.target_identity,
        target_ips=pursuit.target_ips,
        formation=formation,
        priority=pursuit.priority
    )
    return result.to_dict()


@router.get("/pursuit/active")
async def get_active_pursuits():
    center = get_command_center()
    pursuit_agent = center.agents.get("pursuit")
    if not pursuit_agent:
        raise HTTPException(status_code=404, detail="Pursuit agent not found")
    return await pursuit_agent.get_active_pursuits()


@router.post("/pursuit/{strategy_id}/complete")
async def complete_pursuit(strategy_id: str, success: bool = True):
    center = get_command_center()
    pursuit_agent = center.agents.get("pursuit")
    if not pursuit_agent:
        raise HTTPException(status_code=404, detail="Pursuit agent not found")
    result = await pursuit_agent.complete_pursuit(strategy_id, success)
    if not result:
        raise HTTPException(status_code=404, detail="Pursuit not found")
    return {"status": "completed", "strategy_id": strategy_id, "success": success}


@router.get("/tactics")
async def get_all_tactics():
    center = get_command_center()
    tactical_library = center.agents.get("tactical_library")
    if not tactical_library:
        raise HTTPException(status_code=404, detail="Tactical library not found")
    return await tactical_library.get_all_tactics()


@router.post("/tactics/create")
async def create_tactic(tactic: TacticCreate):
    center = get_command_center()
    tactical_library = center.agents.get("tactical_library")
    if not tactical_library:
        raise HTTPException(status_code=404, detail="Tactical library not found")
    
    from backend.agents.counterstrike.tactical_library import TacticCategory
    try:
        category = TacticCategory(tactic.category)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    result = await tactical_library.register_tactic(
        name=tactic.name,
        category=category,
        description=tactic.description,
        conditions=tactic.conditions,
        parameters=tactic.parameters,
        required_agents=tactic.required_agents,
        tags=set(tactic.tags)
    )
    return result.to_dict()


@router.get("/tactics/recommend")
async def recommend_tactics(
    attack_type: str,
    threat_level: int = 2,
    confidence: float = 0.5
):
    center = get_command_center()
    tactical_library = center.agents.get("tactical_library")
    if not tactical_library:
        raise HTTPException(status_code=404, detail="Tactical library not found")
    
    scenario = {
        "attack_type": attack_type,
        "threat_level": threat_level,
        "confidence": confidence
    }
    
    recommendations = await tactical_library.recommend_tactics(scenario)
    return [
        {"tactic": t.to_dict(), "score": s}
        for t, s in recommendations
    ]


@router.get("/memory/query")
async def query_memory(
    memory_type: Optional[str] = None,
    attacker_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    center = get_command_center()
    memory = center.agents.get("memory")
    if not memory:
        raise HTTPException(status_code=404, detail="Memory agent not found")
    
    if attacker_id:
        return await memory.get_attacker_history(attacker_id)
    
    return await memory.get_memory_stats()


@router.get("/review/reports")
async def get_review_reports(limit: int = Query(20, ge=1, le=100)):
    center = get_command_center()
    review = center.agents.get("review")
    if not review:
        raise HTTPException(status_code=404, detail="Review agent not found")
    return await review.get_recent_reports(limit)


@router.get("/console/dashboard")
async def get_console_dashboard():
    center = get_command_center()
    console = center.agents.get("console")
    if not console:
        raise HTTPException(status_code=404, detail="Console not found")
    return await console.get_dashboard()


@router.get("/console/approvals/pending")
async def get_pending_approvals():
    center = get_command_center()
    console = center.agents.get("console")
    if not console:
        raise HTTPException(status_code=404, detail="Console not found")
    return await console.get_pending_approvals()


@router.post("/console/approve")
async def console_approve(request: ApprovalRequest):
    center = get_command_center()
    console = center.agents.get("console")
    if not console:
        raise HTTPException(status_code=404, detail="Console not found")
    success = await console.approve_action(
        request.request_id,
        request.approver,
        request.notes
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to approve")
    return {"status": "approved"}


@router.post("/console/reject")
async def console_reject(request: RejectionRequest):
    center = get_command_center()
    console = center.agents.get("console")
    if not console:
        raise HTTPException(status_code=404, detail="Console not found")
    success = await console.reject_action(
        request.request_id,
        request.rejecter,
        request.reason
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reject")
    return {"status": "rejected"}


@router.post("/console/mode")
async def set_operation_mode(mode: str, operator: str):
    center = get_command_center()
    console = center.agents.get("console")
    if not console:
        raise HTTPException(status_code=404, detail="Console not found")
    
    from backend.agents.counterstrike.human_console import OperationMode
    try:
        op_mode = OperationMode(mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    success = await console.set_operation_mode(op_mode, operator)
    return {"status": "mode_changed", "mode": mode}


@router.get("/boundary/rules")
async def get_boundary_rules():
    center = get_command_center()
    boundary = center.agents.get("boundary")
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary controller not found")
    return await boundary.get_all_rules()


@router.get("/boundary/violations")
async def get_boundary_violations(limit: int = Query(50, ge=1, le=200)):
    center = get_command_center()
    boundary = center.agents.get("boundary")
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary controller not found")
    return await boundary.get_violations(limit)


@router.get("/pheromone/state")
async def get_pheromone_state():
    center = get_command_center()
    pheromone = center.agents.get("pheromone")
    if not pheromone:
        raise HTTPException(status_code=404, detail="Pheromone field not found")
    return await pheromone.get_field_state()


@router.get("/coordination/stats")
async def get_coordination_stats():
    center = get_command_center()
    coordination = center.agents.get("coordination")
    if not coordination:
        raise HTTPException(status_code=404, detail="Coordination module not found")
    return await coordination.get_coordination_stats()
