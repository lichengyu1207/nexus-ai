"""
数据模型定义 - Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TriggerType(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class RestartResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class AgentStatus(BaseModel):
    agent_id: str
    last_heartbeat: Optional[float] = None
    is_alive: bool = True
    last_restart: Optional[datetime] = None
    restart_count: int = 0


class RestartEvent(BaseModel):
    agent_id: str
    trigger_type: TriggerType
    last_heartbeat: Optional[float] = None
    operator: Optional[str] = None
    result: RestartResult
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class RestartRequest(BaseModel):
    operator: str = "admin"
    reason: Optional[str] = None


class RestartResponse(BaseModel):
    status: str
    message: str
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    redis_connected: bool = True
