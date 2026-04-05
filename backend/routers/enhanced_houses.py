#!/usr/bin/env python3
"""
房源数据智能体集群调用接口
为三省六部智能体集群、估值引擎、GIS引擎等提供统一数据接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import asyncpg

router = APIRouter(prefix="/api/houses", tags=["房源数据"])

DB_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DB_URL,
            min_size=5,
            max_size=20,
            command_timeout=60.0
        )
    return _pool

async def get_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn

class HouseBase(BaseModel):
    id: str
    community_name: str
    city: str
    district: str
    price_per_sqm: float
    area: float
    layout: Optional[str] = None
    floor: Optional[str] = None
    building_year: Optional[str] = None
    address: Optional[str] = None
    features: Optional[str] = None
    description: Optional[str] = None
    tag: Optional[str] = None
    image_url: Optional[str] = None

class HouseListResponse(BaseModel):
    total: int
    houses: List[HouseBase]
    city_stats: Optional[Dict[str, Any]] = None
    district_stats: Optional[Dict[str, Any]] = None

@router.get("", response_model=HouseListResponse)
async def get_houses(
    city: Optional[str] = None,
    district: Optional[str] = None,
    community_name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    layout: Optional[str] = None,
    features: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn = Depends(get_db)
):
    """
    获取房源列表 - 智能体集群调用接口
    
    支持多维度筛选：
    - 城市、区域、小区
    - 价格区间
    - 面积区间
    - 户型
    - 特色标签
    """
    conditions = []
    params = []
    param_idx = 1
    
    if city:
        conditions.append(f"city = ${param_idx}")
        params.append(city)
        param_idx += 1
    
    if district:
        conditions.append(f"district = ${param_idx}")
        params.append(district)
        param_idx += 1
    
    if community_name:
        conditions.append(f"community_name LIKE ${param_idx}")
        params.append(f"%{community_name}%")
        param_idx += 1
    
    if min_price:
        conditions.append(f"price_per_sqm >= ${param_idx}")
        params.append(min_price)
        param_idx += 1
    
    if max_price:
        conditions.append(f"price_per_sqm <= ${param_idx}")
        params.append(max_price)
        param_idx += 1
    
    if min_area:
        conditions.append(f"area >= ${param_idx}")
        params.append(min_area)
        param_idx += 1
    
    if max_area:
        conditions.append(f"area <= ${param_idx}")
        params.append(max_area)
        param_idx += 1
    
    if layout:
        conditions.append(f"layout LIKE ${param_idx}")
        params.append(f"%{layout}%")
        param_idx += 1
    
    if features:
        conditions.append(f"features LIKE ${param_idx}")
        params.append(f"%{features}%")
        param_idx += 1
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    count_sql = f"SELECT COUNT(*) FROM enhanced_houses WHERE {where_clause}"
    total = await conn.fetchval(count_sql, *params)
    
    data_sql = f"""
        SELECT * FROM enhanced_houses 
        WHERE {where_clause}
        ORDER BY price_per_sqm DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])
    
    rows = await conn.fetch(data_sql, *params)
    houses = [dict(row) for row in rows]
    
    city_stats = None
    district_stats = None
    
    if city and not district:
        district_stats = await conn.fetch("""
            SELECT district, COUNT(*) as count, AVG(price_per_sqm) as avg_price
            FROM enhanced_houses
            WHERE city = $1
            GROUP BY district
            ORDER BY count DESC
        """, city)
        district_stats = [dict(s) for s in district_stats]
    
    return {
        "total": total,
        "houses": houses,
        "city_stats": city_stats,
        "district_stats": district_stats
    }

@router.get("/{house_id}", response_model=HouseBase)
async def get_house(house_id: str, conn = Depends(get_db)):
    """获取单个房源详情 - 智能体集群调用接口"""
    row = await conn.fetchrow(
        "SELECT * FROM enhanced_houses WHERE id = $1", house_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="房源不存在")
    return dict(row)

@router.get("/city/{city}/stats")
async def get_city_stats(city: str, conn = Depends(get_db)):
    """获取城市统计信息 - 估值引擎调用接口"""
    stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total_count,
            AVG(price_per_sqm) as avg_price,
            MIN(price_per_sqm) as min_price,
            MAX(price_per_sqm) as max_price,
            AVG(area) as avg_area
        FROM enhanced_houses
        WHERE city = $1
    """, city)
    
    districts = await conn.fetch("""
        SELECT district, COUNT(*) as count, AVG(price_per_sqm) as avg_price
        FROM enhanced_houses
        WHERE city = $1
        GROUP BY district
        ORDER BY avg_price DESC
    """, city)
    
    return {
        "city": city,
        "stats": dict(stats) if stats else None,
        "districts": [dict(d) for d in districts]
    }

@router.get("/district/{city}/{district}/stats")
async def get_district_stats(city: str, district: str, conn = Depends(get_db)):
    """获取区域统计信息 - GIS引擎调用接口"""
    stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total_count,
            AVG(price_per_sqm) as avg_price,
            MIN(price_per_sqm) as min_price,
            MAX(price_per_sqm) as max_price,
            AVG(area) as avg_area
        FROM enhanced_houses
        WHERE city = $1 AND district = $2
    """, city, district)
    
    communities = await conn.fetch("""
        SELECT community_name, COUNT(*) as count, AVG(price_per_sqm) as avg_price
        FROM enhanced_houses
        WHERE city = $1 AND district = $2
        GROUP BY community_name
        ORDER BY avg_price DESC
    """, city, district)
    
    return {
        "city": city,
        "district": district,
        "stats": dict(stats) if stats else None,
        "communities": [dict(c) for c in communities]
    }

@router.get("/search/suggest")
async def search_suggest(q: str, limit: int = 10, conn = Depends(get_db)):
    """搜索建议 - 智能体咨询接口"""
    results = await conn.fetch("""
        SELECT DISTINCT community_name, city, district
        FROM enhanced_houses
        WHERE community_name LIKE $1 OR district LIKE $1 OR city LIKE $1
        LIMIT $2
    """, f"%{q}%", limit)
    
    return {"suggestions": [dict(r) for r in results]}
