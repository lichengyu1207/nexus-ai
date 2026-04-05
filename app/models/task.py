from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    property_id = Column(String, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    __tablename__ = "task_steps"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    name = Column(String)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="steps")