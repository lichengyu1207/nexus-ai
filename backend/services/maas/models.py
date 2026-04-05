# -*- coding: utf-8 -*-
"""
MaAS 数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class AgentOperator:
    id: str
    name: str
    display_name: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    cost_estimate: float = 0.1
    latency_estimate: float = 0.5
    description: str = ""
    is_active: bool = True
    
    @classmethod
    def from_db_row(cls, row: dict) -> "AgentOperator":
        return cls(
            id=str(row.get("id", "")),
            name=row.get("name", ""),
            display_name=row.get("display_name", ""),
            agent_type=row.get("agent_type", ""),
            capabilities=row.get("capabilities", []) or [],
            cost_estimate=row.get("cost_estimate", 0.1),
            latency_estimate=row.get("latency_estimate", 0.5),
            description=row.get("description", ""),
            is_active=row.get("is_active", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "cost_estimate": self.cost_estimate,
            "latency_estimate": self.latency_estimate,
            "description": self.description,
            "is_active": self.is_active
        }


@dataclass
class ArchitectureTemplate:
    id: str
    name: str
    complexity_range_min: float = 0.0
    complexity_range_max: float = 1.0
    agent_sequence: List[str] = field(default_factory=list)
    connection_graph: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    avg_cost: float = 0.0
    avg_latency: float = 0.0
    success_rate: float = 0.0
    use_count: int = 0
    is_active: bool = True
    
    @classmethod
    def from_db_row(cls, row: dict) -> "ArchitectureTemplate":
        return cls(
            id=str(row.get("id", "")),
            name=row.get("name", ""),
            complexity_range_min=row.get("complexity_range_min", 0.0),
            complexity_range_max=row.get("complexity_range_max", 1.0),
            agent_sequence=row.get("agent_sequence", []) or [],
            connection_graph=row.get("connection_graph", {}) or {},
            description=row.get("description", ""),
            avg_cost=row.get("avg_cost", 0.0),
            avg_latency=row.get("avg_latency", 0.0),
            success_rate=row.get("success_rate", 0.0),
            use_count=row.get("use_count", 0),
            is_active=row.get("is_active", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "complexity_range": [self.complexity_range_min, self.complexity_range_max],
            "agent_sequence": self.agent_sequence,
            "connection_graph": self.connection_graph,
            "description": self.description,
            "avg_cost": self.avg_cost,
            "avg_latency": self.avg_latency,
            "success_rate": self.success_rate,
            "use_count": self.use_count
        }
    
    def matches_complexity(self, complexity: float) -> bool:
        return self.complexity_range_min <= complexity <= self.complexity_range_max


@dataclass
class TaskFeature:
    content: str
    task_type: str = "general"
    length: int = 0
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    complexity_score: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "task_type": self.task_type,
            "length": self.length,
            "keywords": self.keywords,
            "entities": self.entities,
            "complexity_score": self.complexity_score
        }


@dataclass
class SchedulingDecision:
    id: str
    user_id: str
    task_content: str
    task_type: str = "general"
    task_features: Dict[str, Any] = field(default_factory=dict)
    complexity_score: float = 0.5
    selected_architecture_id: str = ""
    selected_architecture_name: str = ""
    agent_invocations: List[Dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0
    total_cost: float = 0.0
    success: bool = False
    result_summary: str = ""
    feedback: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_db_row(cls, row: dict) -> "SchedulingDecision":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            task_content=row.get("task_content", ""),
            task_type=row.get("task_type", "general"),
            task_features=row.get("task_features", {}) or {},
            complexity_score=row.get("complexity_score", 0.5),
            selected_architecture_id=str(row.get("selected_architecture_id", "")),
            selected_architecture_name=row.get("selected_architecture_name", ""),
            agent_invocations=row.get("agent_invocations", []) or [],
            execution_time=row.get("execution_time", 0.0),
            total_cost=row.get("total_cost", 0.0),
            success=row.get("success", False),
            result_summary=row.get("result_summary", ""),
            feedback=row.get("feedback", {}) or {},
            created_at=row.get("created_at", datetime.now())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_content": self.task_content,
            "task_type": self.task_type,
            "task_features": self.task_features,
            "complexity_score": self.complexity_score,
            "selected_architecture_id": self.selected_architecture_id,
            "selected_architecture_name": self.selected_architecture_name,
            "agent_invocations": self.agent_invocations,
            "execution_time": self.execution_time,
            "total_cost": self.total_cost,
            "success": self.success,
            "result_summary": self.result_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class SchedulingResult:
    architecture: ArchitectureTemplate
    agents: List[AgentOperator]
    estimated_cost: float
    estimated_latency: float
    complexity_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture": self.architecture.to_dict(),
            "agents": [a.to_dict() for a in self.agents],
            "estimated_cost": self.estimated_cost,
            "estimated_latency": self.estimated_latency,
            "complexity_score": self.complexity_score
        }
