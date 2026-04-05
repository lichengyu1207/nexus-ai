from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SubTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)
    spec = Column(JSON, nullable=False)  # 任务规格
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    trace_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_duration = Column(Integer, nullable=True)  # 总耗时（秒）

class SubTask(Base):
    __tablename__ = "subtasks"
    
    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    dependencies = Column(JSON, nullable=False, default=list)  # 依赖的子任务ID列表
    required_agents = Column(JSON, nullable=False, default=list)  # 所需智能体类型
    parameters = Column(JSON, nullable=False, default=dict)  # 参数
    status = Column(Enum(SubTaskStatus), default=SubTaskStatus.PENDING)
    result = Column(JSON, nullable=True)  # 执行结果
    error = Column(Text, nullable=True)  # 错误信息
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # 耗时（秒）
    trace_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
