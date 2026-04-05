from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    schema_info = Column(JSON, nullable=True)  # 字段列表、类型
    sensitivity = Column(String(20), nullable=False)  # low, medium, high
    owner = Column(String(100), nullable=True)
    policy = Column(JSON, nullable=True)  # 访问策略
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
