from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 智能体类型，如中书省、户部等
    description = Column(Text, nullable=True)
    allowed_tools = Column(JSON, nullable=False, default=list)  # 工具白名单
    config = Column(JSON, nullable=True)  # 其他配置
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
