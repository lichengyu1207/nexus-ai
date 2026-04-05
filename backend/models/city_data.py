# -*- coding: utf-8 -*-
"""
城市数据模型
定义城市数据表结构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class CityDataBase(BaseModel):
    """城市数据基础模型"""
    city: str = Field(..., description="城市名称")
    avg_price: Optional[float] = Field(None, description="平均房价")
    total_houses: Optional[int] = Field(None, description="房源总数")
    price_trend: Optional[str] = Field(None, description="价格趋势")
    hot_districts: Optional[List[str]] = Field(default_factory=list, description="热门区域")
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="原始数据")


class CityDataCreate(CityDataBase):
    """创建城市数据"""
    pass


class CityDataResponse(CityDataBase):
    """城市数据响应"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CityDataSummary(BaseModel):
    """城市数据摘要"""
    city: str
    avg_price: Optional[float] = None
    total_houses: Optional[int] = None
    price_trend: Optional[str] = None
    hot_districts: List[str] = []
    last_updated: Optional[str] = None


class CollectionResult(BaseModel):
    """采集结果"""
    city: str
    success: bool
    message: str
    duration_ms: float = 0.0
    error: Optional[str] = None
    timestamp: str


class BatchCollectionResult(BaseModel):
    """批量采集结果"""
    total_cities: int
    successful: int
    failed: int
    duration_seconds: float
    results: Dict[str, CollectionResult]
    timestamp: str
