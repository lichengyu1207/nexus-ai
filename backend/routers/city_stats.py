"""
城市统计API
用于用户地图展示城市统计数据
"""
from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel

from backend.database import get_db_connection

router = APIRouter(prefix="/api/city-stats", tags=["城市统计"])


class CityStatsResponse(BaseModel):
    id: str
    city_name: str
    province_name: Optional[str]
    user_count: int
    community_count: int
    house_count: int
    poi_count: int
    latitude: Optional[float]
    longitude: Optional[float]


class CityStatsSummary(BaseModel):
    total_cities: int
    total_users: int
    total_communities: int
    total_pois: int


@router.get("", response_model=List[CityStatsResponse])
async def get_all_city_stats():
    """获取所有城市统计数据"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT * FROM city_stats 
            WHERE user_count > 0 OR community_count > 0 OR poi_count > 0
            ORDER BY user_count DESC, community_count DESC
        ''')
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
        
    finally:
        await conn.close()


@router.get("/summary", response_model=CityStatsSummary)
async def get_city_stats_summary():
    """获取城市统计汇总"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT 
                COUNT(*) as total_cities,
                COALESCE(SUM(user_count), 0) as total_users,
                COALESCE(SUM(community_count), 0) as total_communities,
                COALESCE(SUM(poi_count), 0) as total_pois
            FROM city_stats
        ''')
        row = await cursor.fetchone()
        
        return dict(row) if row else {
            "total_cities": 0,
            "total_users": 0,
            "total_communities": 0,
            "total_pois": 0
        }
        
    finally:
        await conn.close()


@router.get("/{city_name}", response_model=CityStatsResponse)
async def get_city_stats(city_name: str):
    """获取单个城市统计数据"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM city_stats WHERE city_name = ?", (city_name,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return {
                "id": f"city-{city_name}",
                "city_name": city_name,
                "province_name": None,
                "user_count": 0,
                "community_count": 0,
                "house_count": 0,
                "poi_count": 0,
                "latitude": None,
                "longitude": None
            }
        
        return dict(row)
        
    finally:
        await conn.close()
