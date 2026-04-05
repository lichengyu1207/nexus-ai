"""
地理数据筛选器
根据地理实体和用户需求筛选房产数据
"""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .geo_parser import GeoParser, GeoResult
from backend.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class FilterCondition:
    """筛选条件"""
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    rooms: Optional[int] = None
    halls: Optional[int] = None
    orientation: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class GeoDataFilter:
    """地理数据筛选器"""
    
    def __init__(self):
        self.geo_parser = GeoParser()
    
    async def query_by_geo(
        self, 
        geo_result: GeoResult, 
        filters: FilterCondition = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        根据地理实体查询房产数据
        """
        results = {
            "total": 0,
            "communities": [],
            "houses": [],
            "statistics": {}
        }
        
        try:
            async with get_db() as conn:
                # 根据层级构建查询
                if geo_result.level == "community" and geo_result.community_id:
                    # 查询单个小区
                    results = await self._query_community(
                        conn, geo_result.community_id, filters, limit, offset
                    )
                elif geo_result.level == "district" and geo_result.district_id:
                    # 查询区域下所有小区
                    results = await self._query_district(
                        conn, geo_result.district_id, filters, limit, offset
                    )
                elif geo_result.level == "city" and geo_result.city_id:
                    # 查询城市下所有小区
                    results = await self._query_city(
                        conn, geo_result.city_id, filters, limit, offset
                    )
                else:
                    # 使用模拟数据
                    results = self._get_mock_data(geo_result, filters, limit)
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            results = self._get_mock_data(geo_result, filters, limit)
        
        return results
    
    async def _query_community(
        self, conn, community_id: str, 
        filters: FilterCondition, limit: int, offset: int
    ) -> Dict:
        """查询单个小区"""
        # 查询小区信息
        cursor = await conn.execute(
            "SELECT * FROM communities WHERE id = ?", (community_id,)
        )
        community = await cursor.fetchone()
        
        if not community:
            return {"total": 0, "communities": [], "houses": []}
        
        # 查询房源
        sql = "SELECT * FROM houses WHERE community_id = ?"
        params = [community_id]
        
        if filters:
            if filters.price_min:
                sql += " AND listing_price >= ?"
                params.append(filters.price_min)
            if filters.price_max:
                sql += " AND listing_price <= ?"
                params.append(filters.price_max)
            if filters.rooms:
                sql += " AND rooms = ?"
                params.append(filters.rooms)
        
        sql += f" LIMIT {limit} OFFSET {offset}"
        
        cursor = await conn.execute(sql, params)
        houses = await cursor.fetchall()
        
        return {
            "total": len(houses),
            "communities": [dict(community)],
            "houses": [dict(h) for h in houses]
        }
    
    async def _query_district(
        self, conn, district_id: str,
        filters: FilterCondition, limit: int, offset: int
    ) -> Dict:
        """查询区域下所有小区"""
        cursor = await conn.execute(
            "SELECT * FROM communities WHERE district_id = ? LIMIT ? OFFSET ?",
            (district_id, limit, offset)
        )
        communities = await cursor.fetchall()
        
        return {
            "total": len(communities),
            "communities": [dict(c) for c in communities],
            "houses": []
        }
    
    async def _query_city(
        self, conn, city_id: str,
        filters: FilterCondition, limit: int, offset: int
    ) -> Dict:
        """查询城市下所有小区"""
        cursor = await conn.execute(
            "SELECT * FROM communities WHERE city_id = ? LIMIT ? OFFSET ?",
            (city_id, limit, offset)
        )
        communities = await cursor.fetchall()
        
        return {
            "total": len(communities),
            "communities": [dict(c) for c in communities],
            "houses": []
        }
    
    def _get_mock_data(
        self, geo_result: GeoResult,
        filters: FilterCondition, limit: int
    ) -> Dict:
        """获取模拟数据"""
        communities = []
        
        # 根据地理层级生成模拟数据
        if geo_result.city == "深圳市":
            communities = [
                {
                    "id": "community-001",
                    "name": "华润城",
                    "district": "南山区",
                    "avg_price": 98000,
                    "houses_count": 23,
                    "distance_to_subway": 300,
                    "tags": ["地铁房", "学区房"]
                },
                {
                    "id": "community-002",
                    "name": "深圳湾一号",
                    "district": "南山区",
                    "avg_price": 150000,
                    "houses_count": 15,
                    "distance_to_subway": 200,
                    "tags": ["豪宅", "海景房"]
                },
                {
                    "id": "community-003",
                    "name": "半岛城邦",
                    "district": "南山区",
                    "avg_price": 120000,
                    "houses_count": 18,
                    "distance_to_subway": 500,
                    "tags": ["海景房", "学区房"]
                }
            ]
        elif geo_result.city == "广州市":
            communities = [
                {
                    "id": "community-gz001",
                    "name": "珠江新城",
                    "district": "天河区",
                    "avg_price": 80000,
                    "houses_count": 30,
                    "distance_to_subway": 100,
                    "tags": ["CBD", "地铁房"]
                }
            ]
        elif geo_result.city == "北京市":
            communities = [
                {
                    "id": "community-bj001",
                    "name": "国贸公寓",
                    "district": "朝阳区",
                    "avg_price": 90000,
                    "houses_count": 25,
                    "distance_to_subway": 150,
                    "tags": ["CBD", "地铁房"]
                }
            ]
        
        # 应用筛选条件
        if filters and filters.price_max:
            communities = [
                c for c in communities 
                if c["avg_price"] * 100 <= filters.price_max
            ]
        
        return {
            "total": len(communities[:limit]),
            "communities": communities[:limit],
            "houses": [],
            "statistics": {
                "avg_price": sum(c["avg_price"] for c in communities) / len(communities) if communities else 0,
                "total_houses": sum(c["houses_count"] for c in communities)
            }
        }
    
    async def get_pois(
        self, 
        community_id: str, 
        poi_type: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """获取周边POI"""
        try:
            async with get_db() as conn:
                sql = "SELECT * FROM pois WHERE community_id = ?"
                params = [community_id]
                
                if poi_type:
                    sql += " AND type = ?"
                    params.append(poi_type)
                
                sql += f" ORDER BY distance LIMIT {limit}"
                
                cursor = await conn.execute(sql, params)
                pois = await cursor.fetchall()
                
                return [dict(p) for p in pois]
        except Exception as e:
            logger.error(f"Get POIs failed: {e}")
            return self._get_mock_pois(community_id, poi_type, limit)
    
    def _get_mock_pois(
        self, community_id: str, poi_type: str, limit: int
    ) -> List[Dict]:
        """获取模拟POI数据"""
        all_pois = [
            {"type": "地铁站", "name": "科技园站", "distance": 300, "line": "1号线"},
            {"type": "地铁站", "name": "深大站", "distance": 500, "line": "1号线"},
            {"type": "学校", "name": "南山外国语学校", "distance": 400, "level": "重点"},
            {"type": "学校", "name": "深圳大学", "distance": 800, "level": "本科"},
            {"type": "医院", "name": "南山医院", "distance": 1000, "level": "三甲"},
            {"type": "商场", "name": "华润万家", "distance": 200, "level": "大型"},
            {"type": "公园", "name": "深圳湾公园", "distance": 1500, "level": "市级"},
        ]
        
        if poi_type:
            all_pois = [p for p in all_pois if p["type"] == poi_type]
        
        return all_pois[:limit]


# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test():
        parser = GeoParser()
        filter_service = GeoDataFilter()
        
        # 测试解析和查询
        text = "深圳南山区"
        geo_result = parser.parse(text)
        print(f"解析结果: {parser.to_dict(geo_result)}")
        
        # 查询数据
        filters = FilterCondition(price_max=10000000)
        results = await filter_service.query_by_geo(geo_result, filters)
        print(f"查询结果: {results}")
        
        # 获取POI
        pois = await filter_service.get_pois("community-001", "地铁站")
        print(f"POI结果: {pois}")
    
    asyncio.run(test())
