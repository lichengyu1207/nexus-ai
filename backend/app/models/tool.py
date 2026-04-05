from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class ToolStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

class Tool(Base):
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    input_schema = Column(JSON, nullable=True)  # JSON Schema 描述输入
    output_schema = Column(JSON, nullable=True)
    call_type = Column(String(20), nullable=False)  # http, local, grpc
    endpoint = Column(String(500), nullable=True)  # 如果是 http，存储 URL
    auth_config = Column(JSON, nullable=True)  # 认证配置（API Key, OAuth）
    status = Column(Enum(ToolStatus), default=ToolStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
