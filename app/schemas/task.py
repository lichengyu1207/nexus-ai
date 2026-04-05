from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.task import TaskStatus


class TaskStepBase(BaseModel):
    name: str
    description: str


class TaskStepCreate(TaskStepBase):
    pass


class TaskStepUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    progress: Optional[int] = None
    result: Optional[str] = None
    error: Optional[str] = None


class TaskStep(TaskStepBase):
    id: str
    task_id: str
    status: TaskStatus
    progress: int
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    property_id: str


class TaskCreate(TaskBase):
    steps: List[TaskStepCreate]


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    progress: Optional[int] = None


class Task(TaskBase):
    id: str
    status: TaskStatus
    progress: int
    steps: List[TaskStep]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskInDB(Task):
    pass