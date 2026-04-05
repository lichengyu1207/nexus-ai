from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base


class AgentType(str, enum.Enum):
    REQUIREMENT_ANALYZER = "requirement_analyzer"
    DATA_COLLECTOR = "data_collector"
    DATA_CLEANER = "data_cleaner"
    DATA_VERIFIER = "data_verifier"
    MARKET_ANALYST = "market_analyst"
    REPORT_GENERATOR = "report_generator"


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, enum.Enum):
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    STEP_ERROR = "step_error"


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, index=True)
    agent_type = Column(SQLEnum(AgentType), index=True)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.PENDING)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # 毫秒
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, index=True)
    event_type = Column(SQLEnum(EventType), index=True)
    agent_id = Column(String, nullable=True, index=True)
    agent_type = Column(SQLEnum(AgentType), nullable=True, index=True)
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskSnapshot(Base):
    __tablename__ = "task_snapshots"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, index=True)
    snapshot_data = Column(JSON)  # 包含代理列表、步骤详情、时间戳
    total_duration = Column(Integer, nullable=True)  # 毫秒
    created_at = Column(DateTime, default=datetime.utcnow)
