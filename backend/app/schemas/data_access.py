from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DataAccessLogResponse(BaseModel):
    id: int
    dataset_id: Optional[int] = None
    agent_id: Optional[int] = None
    user_id: Optional[str] = None
    operation: str
    resource: str
    success: bool
    error_message: Optional[str] = None
    accessed_at: datetime
    trace_id: str
    
    class Config:
        from_attributes = True
