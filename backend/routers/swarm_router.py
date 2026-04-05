# -*- coding: utf-8 -*-
"""
Agent Swarm 可扩展多智能体协作系统 API路由
"""
from fastapi import APIRouter, HTTPException,from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

import json

from ..services.swarm import (
    SwarmConfig, get_default_config,
    SwarmAgent, SwarmTask, SwarmBid, SwarmSession,
    SwarmTaskLog, SwarmHeartbeat, BidResult, TaskResult
)
from ..services.swarm.agent import Agent, SwarmAgentBase, ThreeProvinceAgent, SixMinistryAgent
from ..services.swarm.task_board import TaskBoard, Task, Bid
from ..services.swarm.bidding import BiddingEngine, CapabilityMatcher, LoadBalancer
from ..services.swarm.p2p_network import P2PNetwork, HeartbeatMonitor, TaskMigrator
from ..services.swarm.collaboration import CollaborationManager, ParallelMode, SequentialMode, DebateMode
from ..services.swarm.swarm import SwarmOrchestrator

router = APIRouter(prefix="/swarm", tags=["Agent Swarm - 多智能体协作"])

swarm_config = get_default_config()
swarm_orchestrator = SwarmOrchestrator(swarm_config)
    performance_monitor = PerformanceMonitor()


class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    collaboration_mode: str = "parallel"


class ProcessRequest(BaseModel):
    session_id: Optional[str] = None
    query: List[float]
    key: List[float]
    value: List[float]


class ComputeSparsityRequest(BaseModel):
    context_length: int
    attention_weights: Optional[List[float]] = None
    step: int = 0
    model_name: str = "default"


class EstimateImportanceRequest(BaseModel):
    query: List[float]
    kv_cache: List[Dict[str, List[float]]]
    model_name: str = "default"


class RecordMetricRequest(BaseModel):
    session_id: Optional[str] = None
    metric_type: str
    metric_name: str
    value: float
    unit: str = ""
    metadata: Optional[Dict[str, Any]] = None


class CreateAgentRequest(BaseModel):
    name: str
    agent_type: str = "province"
    department: Optional[str] = None
    capabilities: List[str] = []
    skill_scores: Dict[str, float] = {}
    max_concurrent_tasks: int = 3


class UpdateAgentRequest(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    department: Optional[str] = None
    capabilities: List[str] = []
    skill_scores: Dict[str, float] = {}
    max_concurrent_tasks: int = 3


class UpdateTaskRequest(BaseModel):
    task_id: str
    status: str
    payload: Dict = {}
    result: Optional[Dict] = None
    collaboration_mode: Optional[str] = None


class RecordDecisionRequest(BaseModel):
    session_id: str
    task_id: str
    agent_id: str
    complexity_score: float
    sparsity_rate: float
    memory_saved_mb: float
    compression_ratio: float
    latency_ms: float
    stage: str
    created_at: datetime = field(default_factory=datetime.now)


class RecordMetricRequest(BaseModel):
    session_id: Optional[str] = None
    metric_type: str
    metric_name: str
    value: float
    unit: str = ""
    metadata: Optional[Dict[str, Any]] = None


class RecordHeartbeatRequest(BaseModel):
    agent_id: str
    load: float
    active_tasks: int = 0
    status_info: Dict = {}
    recorded_at: datetime = field(default_factory=datetime.now)


class UpdateSessionRequest(BaseModel):
    session_id: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_latency_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    def increment_task(self):
        self.total_tasks += 1
        self.completed_tasks += 1
    
    def increment_failed(self):
        self.failed_tasks += 1
    
    def complete(self):
        self.ended_at = datetime.now()
        self.total_latency_ms = (datetime.now() - self.started_at).total_seconds() * 1000


    
    def get_statistics(self) -> Dict:
        return {
            "session_id": str(self.session_id),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_latency_ms": self.total_latency_ms,
            "duration_seconds": (datetime.now() - self.started_at).total_seconds(),
            "status": "completed" if self.ended_at else "running"
        }
