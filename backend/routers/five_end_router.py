"""
五端智能体集群API路由
Five-End Agent Cluster API Router
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/five-end", tags=["五端智能体集群"])

_initialized = False
message_bus = None
blackboard = None
consensus = None
disclaimer_system = None
ban_system = None
gov_cluster = None
enterprise_cluster = None
education_cluster = None
standard_cluster = None
public_cluster = None


async def _ensure_initialized():
    global _initialized, message_bus, blackboard, consensus, disclaimer_system, ban_system
    global gov_cluster, enterprise_cluster, education_cluster, standard_cluster, public_cluster
    
    if _initialized:
        return
    
    try:
        from backend.agents.five_end import (
            FiveEndMessageBus, FiveEndBlackboard, CrossEndConsensus,
            DisclaimerSystem, BanAppealSystem,
            GovernmentCluster, EnterpriseCluster, EducationCluster,
            StandardCluster, PublicCluster,
        )
        
        message_bus = FiveEndMessageBus()
        blackboard = FiveEndBlackboard()
        consensus = CrossEndConsensus(message_bus=message_bus, blackboard=blackboard)
        disclaimer_system = DisclaimerSystem(message_bus=message_bus)
        ban_system = BanAppealSystem(message_bus=message_bus)
        
        gov_cluster = GovernmentCluster()
        enterprise_cluster = EnterpriseCluster()
        education_cluster = EducationCluster()
        standard_cluster = StandardCluster()
        public_cluster = PublicCluster()
        
        await message_bus.start()
        await consensus.start()
        await ban_system.start()
        
        _initialized = True
        logger.info("Five-end system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize five-end system: {e}")
        raise


class EventCreateRequest(BaseModel):
    event_type: str = Field(..., min_length=1)
    source_end: str = Field(..., min_length=1)
    source_agent: str = Field(..., min_length=1)
    target_end: Optional[str] = None
    target_agent: Optional[str] = None
    broadcast: bool = False
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


class BlackboardWriteRequest(BaseModel):
    key: str = Field(..., min_length=1)
    value: Any
    source_end: str = Field(..., min_length=1)
    source_agent: str = Field(..., min_length=1)
    knowledge_type: str = Field(default="config")
    region: str = Field(default="public")
    ttl: int = Field(default=86400, ge=0)
    tags: List[str] = Field(default_factory=list)


class ProposalCreateRequest(BaseModel):
    proposal_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    content: Dict[str, Any] = Field(default_factory=dict)
    proposer_end: str = Field(..., min_length=1)
    proposer_agent: str = Field(..., min_length=1)
    voting_duration: int = Field(default=300, ge=60)
    required_quorum: float = Field(default=0.67, ge=0.5, le=1.0)


class VoteRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    voter_end: str = Field(..., min_length=1)
    voter_agent: str = Field(..., min_length=1)
    choice: str = Field(..., min_length=1)
    reason: str = Field(default="")


class DisclaimerConsentRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    disclaimer_type: str = Field(..., min_length=1)
    ip_address: str = Field(default="")
    device_fingerprint: str = Field(default="")
    user_agent: str = Field(default="")
    session_id: str = Field(default="")


class BanCreateRequest(BaseModel):
    ban_type: str = Field(..., min_length=1)
    target_value: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    risk_score: int = Field(default=0, ge=0, le=100)
    duration_seconds: int = Field(default=86400, ge=0)
    is_permanent: bool = Field(default=False)
    source_end: str = Field(default="system")
    source_agent: str = Field(default="ban_system")


class AppealCreateRequest(BaseModel):
    ban_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    contact_info: str = Field(..., min_length=1)
    appeal_reason: str = Field(..., min_length=1)
    evidence: List[str] = Field(default_factory=list)


class AppealResolveRequest(BaseModel):
    appeal_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    reviewer_id: str = Field(..., min_length=1)
    notes: str = Field(default="")


@router.on_event("startup")
async def startup():
    await _ensure_initialized()


@router.on_event("shutdown")
async def shutdown():
    global _initialized
    if message_bus:
        await message_bus.stop()
    if consensus:
        await consensus.stop()
    if ban_system:
        await ban_system.stop()
    _initialized = False


@router.get("/status")
async def get_system_status():
    await _ensure_initialized()
    return {
        "status": "running",
        "timestamp": time.time(),
        "initialized": _initialized,
    }


@router.get("/government/cluster/status")
async def get_government_cluster_status():
    await _ensure_initialized()
    if not gov_cluster:
        raise HTTPException(status_code=503, detail="Government cluster not initialized")
    
    return {
        "cluster_id": getattr(gov_cluster, 'cluster_id', 'unknown'),
        "agents": {
            "monitoring": len(getattr(gov_cluster, 'monitoring_agents', [])),
            "warning": len(getattr(gov_cluster, 'warning_agents', [])),
            "policy_simulation": len(getattr(gov_cluster, 'policy_agents', [])),
            "report": len(getattr(gov_cluster, 'report_agents', [])),
        },
        "energy": getattr(gov_cluster, 'energy', 0),
        "status": getattr(gov_cluster, 'status', 'unknown'),
    }


@router.get("/enterprise/cluster/status")
async def get_enterprise_cluster_status():
    await _ensure_initialized()
    if not enterprise_cluster:
        raise HTTPException(status_code=503, detail="Enterprise cluster not initialized")
    
    return {
        "cluster_id": getattr(enterprise_cluster, 'cluster_id', 'unknown'),
        "agents": {
            "valuation": len(getattr(enterprise_cluster, 'valuation_agents', [])),
            "report": len(getattr(enterprise_cluster, 'report_agents', [])),
            "customer_profile": len(getattr(enterprise_cluster, 'customer_profile_agents', [])),
            "risk_control": len(getattr(enterprise_cluster, 'risk_control_agents', [])),
        },
        "energy": getattr(enterprise_cluster, 'energy', 0),
        "status": getattr(enterprise_cluster, 'status', 'unknown'),
    }


@router.get("/education/cluster/status")
async def get_education_cluster_status():
    await _ensure_initialized()
    if not education_cluster:
        raise HTTPException(status_code=503, detail="Education cluster not initialized")
    
    return {
        "cluster_id": getattr(education_cluster, 'cluster_id', 'unknown'),
        "agents": {
            "teaching": len(getattr(education_cluster, 'teaching_agents', [])),
            "assessment": len(getattr(education_cluster, 'assessment_agents', [])),
            "case": len(getattr(education_cluster, 'case_agents', [])),
            "course": len(getattr(education_cluster, 'course_agents', [])),
        },
        "energy": getattr(education_cluster, 'energy', 0),
        "status": getattr(education_cluster, 'status', 'unknown'),
    }


@router.get("/standard/cluster/status")
async def get_standard_cluster_status():
    await _ensure_initialized()
    if not standard_cluster:
        raise HTTPException(status_code=503, detail="Standard cluster not initialized")
    
    return {
        "cluster_id": getattr(standard_cluster, 'cluster_id', 'unknown'),
        "agents": {
            "standardization": len(getattr(standard_cluster, 'standardization_agents', [])),
            "compliance_review": len(getattr(standard_cluster, 'compliance_agents', [])),
            "industry_report": len(getattr(standard_cluster, 'industry_report_agents', [])),
            "standard_update": len(getattr(standard_cluster, 'standard_update_agents', [])),
        },
        "energy": getattr(standard_cluster, 'energy', 0),
        "status": getattr(standard_cluster, 'status', 'unknown'),
    }


@router.get("/public/cluster/status")
async def get_public_cluster_status():
    await _ensure_initialized()
    if not public_cluster:
        raise HTTPException(status_code=503, detail="Public cluster not initialized")
    
    return {
        "cluster_id": getattr(public_cluster, 'cluster_id', 'unknown'),
        "agents": {
            "customer_service": len(getattr(public_cluster, 'customer_service_agents', [])),
            "recommendation": len(getattr(public_cluster, 'recommendation_agents', [])),
            "transaction_assistant": len(getattr(public_cluster, 'transaction_agents', [])),
            "community": len(getattr(public_cluster, 'community_agents', [])),
        },
        "energy": getattr(public_cluster, 'energy', 0),
        "status": getattr(public_cluster, 'status', 'unknown'),
    }
