from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)  # 操作类型
    resource_type = Column(String(50), nullable=True)  # 资源类型
    resource_id = Column(String(100), nullable=True)  # 资源ID
    agent_id = Column(Integer, nullable=True)  # 智能体ID
    user_id = Column(String(100), nullable=True)  # 用户ID
    ip_address = Column(String(50), nullable=True)  # IP地址
    details = Column(JSON, nullable=True)  # 详细信息
    status = Column(String(20), nullable=False)  # success, failure
    error_message = Column(Text, nullable=True)  # 错误信息
    trace_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
