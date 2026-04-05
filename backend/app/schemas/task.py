from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.task import TaskStatus, SubTaskStatus

class SubTaskSpec(BaseModel):
    id: str
    type: str
    dependencies: List[str] = Field(default_factory=list)
    required_agents: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)

class TaskSpec(BaseModel):
    task_id: str
    task_type: str
    subtasks: List[SubTaskSpec]
    execution_mode: str = "parallel"
    success_criteria: str = "all_subtasks_completed"
    failure_criteria: str = "any_subtask_failed"

class TaskCreate(BaseModel):
    text: str  # 用户输入文本

class SubTaskResponse(BaseModel):
    id: str
    task_id: str
    type: str
    dependencies: List[str]
    required_agents: List[str]
    parameters: Dict[str, Any]
    status: SubTaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    trace_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: str
    type: str
    spec: TaskSpec
    status: TaskStatus
    trace_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    total_duration: Optional[int] = None
    subtasks: Optional[List[SubTaskResponse]] = None
    
    class Config:
        from_attributes = True
