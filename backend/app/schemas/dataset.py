from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    sensitivity: str  # low, medium, high
    owner: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None

class DatasetPolicyUpdate(BaseModel):
    policy: Dict[str, Any]

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    sensitivity: str
    owner: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
