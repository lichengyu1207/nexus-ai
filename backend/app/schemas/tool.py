from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.tool import ToolStatus

class ToolCreate(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    call_type: str  # http, local, grpc
    endpoint: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    status: ToolStatus = ToolStatus.ACTIVE

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    call_type: Optional[str] = None
    endpoint: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    status: Optional[ToolStatus] = None

class ToolResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    call_type: str
    endpoint: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    status: ToolStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
