from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Property(Base):
    """小区基本信息模型"""
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(512), nullable=True)
    built_year = Column(Integer, nullable=True)
    property_type = Column(String(100), nullable=True)
    developer = Column(String(255), nullable=True)
    property_management = Column(String(255), nullable=True)
    greening_rate = Column(Float, nullable=True)
    plot_ratio = Column(Float, nullable=True)
    total_houses = Column(Integer, nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    price_histories = relationship("PriceHistory", back_populates="property", cascade="all, delete-orphan")
    
    # 复合索引
    __table_args__ = (
        Index('idx_city_name', 'city', 'name'),
    )


class PriceHistory(Base):
    """小区价格历史模型"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    price_date = Column(Date, nullable=False, index=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    property = relationship("Property", back_populates="price_histories")
    
    # 复合索引
    __table_args__ = (
        Index('idx_property_date', 'property_id', 'price_date'),
    )


__all__ = ["Property", "PriceHistory"]
