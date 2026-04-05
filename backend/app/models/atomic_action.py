from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AtomicAction(Base):
    __tablename__ = "atomic_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_name = Column(String(100), nullable=False)
    params = Column(JSON, nullable=False)
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    agent_id = Column(Integer, nullable=True)
    trace_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
