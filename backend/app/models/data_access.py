from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base

class DataAccessLog(Base):
    __tablename__ = "data_access_log"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=True, index=True)  # 数据集ID
    agent_id = Column(Integer, nullable=True)  # 智能体ID
    user_id = Column(String(100), nullable=True)  # 用户ID
    operation = Column(String(50), nullable=False)  # read, write
    resource = Column(String(100), nullable=False)  # 资源路径
    success = Column(Boolean, nullable=False)  # 是否成功
    error_message = Column(Text, nullable=True)  # 错误信息
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    trace_id = Column(String, nullable=False, index=True)
