# -*- coding: utf-8 -*-
"""
Agent Swarm 数据模型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import json


@dataclass
class SwarmAgent:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    agent_type: str = "ministry"
    department: str = ""
    capabilities: List[str] = field(default_factory=list)
    skill_scores: Dict[str, float] = field(default_factory=dict)
    current_load: float = 0.0
    max_concurrent_tasks: int = 3
    neighbors: List[str] = field(default_factory=list)
    status: str = "idle"
    last_heartbeat: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "agent_type": self.agent_type,
            "department": self.department,
            "capabilities": self.capabilities,
            "skill_scores": self.skill_scores,
            "current_load": self.current_load,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "neighbors": self.neighbors,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'SwarmAgent':
        return cls(
            id=row["id"],
            name=row.get("name", ""),
            agent_type=row.get("agent_type", "ministry"),
            department=row.get("department", ""),
            capabilities=row.get("capabilities", []),
            skill_scores=row.get("skill_scores", {}),
            current_load=row.get("current_load", 0.0),
            max_concurrent_tasks=row.get("max_concurrent_tasks", 3),
            neighbors=row.get("neighbors", []),
            status=row.get("status", "idle"),
            last_heartbeat=row.get("last_heartbeat"),
            metadata=row.get("metadata", {}),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )


@dataclass
class SwarmTask:
    id: UUID = field(default_factory=uuid4)
    parent_task_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    task_type: str = "general"
    required_capabilities: List[str] = field(default_factory=list)
    priority: int = 5
    status: str = "pending"
    payload: Dict = field(default_factory=dict)
    result: Dict = field(default_factory=dict)
    collaboration_mode: str = "parallel"
    decomposition_level: int = 0
    assigned_agent_id: Optional[UUID] = None
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "parent_task_id": str(self.parent_task_id) if self.parent_task_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "task_type": self.task_type,
            "required_capabilities": self.required_capabilities,
            "priority": self.priority,
            "status": self.status,
            "payload": self.payload,
            "result": self.result,
            "collaboration_mode": self.collaboration_mode,
            "decomposition_level": self.decomposition_level,
            "assigned_agent_id": str(self.assigned_agent_id) if self.assigned_agent_id else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'SwarmTask':
        return cls(
            id=row["id"],
            parent_task_id=row.get("parent_task_id"),
            session_id=row.get("session_id"),
            task_type=row.get("task_type", "general"),
            required_capabilities=row.get("required_capabilities", []),
            priority=row.get("priority", 5),
            status=row.get("status", "pending"),
            payload=row.get("payload", {}),
            result=row.get("result", {}),
            collaboration_mode=row.get("collaboration_mode", "parallel"),
            decomposition_level=row.get("decomposition_level", 0),
            assigned_agent_id=row.get("assigned_agent_id"),
            deadline=row.get("deadline"),
            created_at=row.get("created_at"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at")
        )


@dataclass
class SwarmBid:
    id: UUID = field(default_factory=uuid4)
    task_id: UUID = field(default_factory=uuid4)
    agent_id: UUID = field(default_factory=uuid4)
    score: float = 0.0
    estimated_time: float = 0.0
    confidence: float = 0.5
    proposal: Dict = field(default_factory=dict)
    is_winner: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id),
            "score": self.score,
            "estimated_time": self.estimated_time,
            "confidence": self.confidence,
            "proposal": self.proposal,
            "is_winner": self.is_winner,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'SwarmBid':
        return cls(
            id=row["id"],
            task_id=row["task_id"],
            agent_id=row["agent_id"],
            score=row.get("score", 0.0),
            estimated_time=row.get("estimated_time", 0.0),
            confidence=row.get("confidence", 0.5),
            proposal=row.get("proposal", {}),
            is_winner=row.get("is_winner", False),
            created_at=row.get("created_at")
        )


@dataclass
class SwarmSession:
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    collaboration_mode: str = "parallel"
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_latency_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "collaboration_mode": self.collaboration_mode,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_latency_ms": self.total_latency_ms,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }


@dataclass
class SwarmTaskLog:
    id: UUID = field(default_factory=uuid4)
    task_id: UUID = field(default_factory=uuid4)
    agent_id: Optional[UUID] = None
    event_type: str = ""
    event_data: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class SwarmHeartbeat:
    id: UUID = field(default_factory=uuid4)
    agent_id: UUID = field(default_factory=uuid4)
    load: float = 0.0
    active_tasks: int = 0
    status_info: Dict = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "load": self.load,
            "active_tasks": self.active_tasks,
            "status_info": self.status_info,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }


@dataclass
class BidResult:
    agent_id: UUID
    score: float
    capability_match: float
    load_factor: float
    history_factor: float
    estimated_time: float
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": str(self.agent_id),
            "score": self.score,
            "capability_match": self.capability_match,
            "load_factor": self.load_factor,
            "history_factor": self.history_factor,
            "estimated_time": self.estimated_time,
            "confidence": self.confidence
        }


@dataclass
class TaskResult:
    task_id: UUID
    agent_id: UUID
    success: bool
    result: Dict
    latency_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id),
            "success": self.success,
            "result": self.result,
            "latency_ms": self.latency_ms,
            "error": self.error
        }
