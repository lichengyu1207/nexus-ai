from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.atomic_action import ActionStatus

class AtomicActionCreate(BaseModel):
    action_name: str
    params: Dict[str, Any]
    max_attempts: int = 3
    agent_id: Optional[int] = None

class AtomicActionResponse(BaseModel):
    id: int
    action_name: str
    params: Dict[str, Any]
    status: ActionStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int
    max_attempts: int
    agent_id: Optional[int] = None
    trace_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
