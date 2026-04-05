from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    allowed_tools: List[int] = Field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    status: str = "active"

class AgentToolsUpdate(BaseModel):
    allowed_tools: List[int]

class AgentResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str] = None
    allowed_tools: List[int]
    config: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
