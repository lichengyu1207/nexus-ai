from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    agent_id: Optional[int] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    trace_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
