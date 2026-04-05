from pydantic import BaseModel
from enum import Enum
from typing import Dict, Any, Optional, List


class TaskStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskCreate(BaseModel):
    query: str
    address: Optional[str] = None
    property_type: Optional[str] = None
    area: Optional[float] = None
    age: Optional[int] = None
    description: Optional[str] = None


class TaskStatus(BaseModel):
    task_id: str
    status: TaskStatusEnum
    progress: float
    nodes: Dict[str, TaskStatusEnum]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum


class AgentSummary(BaseModel):
    id: str
    name: str
    avatar: str
    status: str
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TaskDetailResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum
    progress: float
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agents: List[AgentSummary] = []
