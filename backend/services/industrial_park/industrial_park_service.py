# -*- coding: utf-8 -*-
"""
Industrial Park Service - 产业园区服务
提供产业园区数据查询、产城融合指数计算、投资推荐等功能
"""
import asyncpg
import uuid
import json
import math
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"


@dataclass
class IndustrialPark:
    id: str
    name: str
    city: str
    district: Optional[str] = None
    industry_type: Optional[str] = None
    industry_tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    development_goal: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = "planning"
    nearby_property_price_min: Optional[float] = None
    nearby_property_price_max: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "district": self.district,
            "industry_type": self.industry_type,
            "industry_tags": self.industry_tags,
            "description": self.description,
            "development_goal": self.development_goal,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "nearby_property_price_min": self.nearby_property_price_min,
            "nearby_property_price_max": self.nearby_property_price_max
        }


@dataclass
class CityIntegrationIndex:
    city: str
    district: Optional[str] = None
    overall_score: float = 0.0
    industry_score: float = 0.0
    infrastructure_score: float = 0.0
    policy_score: float = 0.0
    talent_score: float = 0.0
    investment_potential: str = "中等"
    key_industries: List[str] = field(default_factory=list)
    growth_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "city": self.city,
            "district": self.district,
            "overall_score": self.overall_score,
            "industry_score": self.industry_score,
            "infrastructure_score": self.infrastructure_score,
            "policy_score": self.policy_score,
            "talent_score": self.talent_score,
            "investment_potential": self.investment_potential,
            "key_industries": self.key_industries,
            "growth_rate": self.growth_rate,
            "star_rating": self._get_star_rating()
        }
    
    def _get_star_rating(self) -> str:
        if self.overall_score >= 4.5:
            return "★★★★★"
        elif self.overall_score >= 4.0:
            return "★★★★☆"
        elif self.overall_score >= 3.5:
            return "★★★★"
        elif self.overall_score >= 3.0:
            return "★★★☆"
        else:
            return "★★★"


class IndustrialParkService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def get_parks_by_city(self, city: str) -> List[IndustrialPark]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM industrial_parks WHERE city = $1 ORDER BY status, name",
                city
            )
            return [self._row_to_park(dict(row)) for row in rows]
    
    async def get_all_parks(self, limit: int = 100) -> List[IndustrialPark]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM industrial_parks ORDER BY city, status LIMIT $1",
                limit
            )
            return [self._row_to_park(dict(row)) for row in rows]
    
    async def get_parks_by_industry(self, industry: str) -> List[IndustrialPark]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM industrial_parks 
                   WHERE industry_type ILIKE $1 OR industry_tags::text ILIKE $1
                   ORDER BY city""",
                f"%{industry}%"
            )
            return [self._row_to_park(dict(row)) for row in rows]
    
    async def get_nearby_parks(
        self, 
        lat: float, 
        lng: float, 
        radius_km: float = 50
    ) -> List[Tuple[IndustrialPark, float]]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT *, 
                   (6371 * acos(cos(radians($1)) * cos(radians(latitude)) * 
                   cos(radians(longitude) - radians($2)) + 
                   sin(radians($1)) * sin(radians(latitude)))) AS distance
                   FROM industrial_parks
                   WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                   HAVING distance < $3
                   ORDER BY distance""",
                lat, lng, radius_km
            )
            return [(self._row_to_park(dict(row)), row["distance"]) for row in rows]
    
    async def get_city_integration_index(self, city: str) -> Optional[CityIntegrationIndex]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM city_integration_index WHERE city = $1",
                city
            )
            if row:
                return self._row_to_index(dict(row))
        return None
    
    async def calculate_property_impact(
        self,
        property_lat: float,
        property_lng: float,
        property_price: float
    ) -> Dict[str, Any]:
        nearby_parks = await self.get_nearby_parks(property_lat, property_lng, 30)
        
        if not nearby_parks:
            return {
                "impact_factor": 1.0,
                "nearby_parks": [],
                "price_adjustment": 0,
                "investment_recommendation": "该区域暂无重点产业园区规划"
            }
        
        total_impact = 0.0
        park_details = []
        
        for park, distance in nearby_parks:
            distance_factor = max(0, 1 - distance / 30)
            industry_factor = self._get_industry_factor(park.industry_type)
            status_factor = self._get_status_factor(park.status)
            
            impact = distance_factor * industry_factor * status_factor
            total_impact += impact
            
            park_details.append({
                "name": park.name,
                "industry": park.industry_type,
                "distance_km": round(distance, 2),
                "impact": round(impact, 3),
                "nearby_price_range": f"{park.nearby_property_price_min}-{park.nearby_property_price_max}元/㎡" if park.nearby_property_price_min else "暂无数据"
            })
        
        avg_impact = total_impact / len(nearby_parks) if nearby_parks else 0
        impact_factor = 1 + avg_impact * 0.15
        price_adjustment = property_price * (impact_factor - 1)
        
        if avg_impact > 0.6:
            recommendation = "产业集聚效应显著，未来升值空间大，建议重点关注"
        elif avg_impact > 0.3:
            recommendation = "有一定产业支撑，具备投资潜力"
        else:
            recommendation = "产业影响有限，需综合考虑其他因素"
        
        return {
            "impact_factor": round(impact_factor, 3),
            "nearby_parks": park_details,
            "price_adjustment": round(price_adjustment, 2),
            "investment_recommendation": recommendation,
            "industry_impact_score": round(avg_impact * 100, 1)
        }
    
    def _get_industry_factor(self, industry_type: Optional[str]) -> float:
        if not industry_type:
            return 0.5
        
        high_impact = ["锂电池", "新能源", "3D玻璃", "智能制造", "临空经济"]
        medium_impact = ["新材料", "高端制造", "储能", "钛材料"]
        
        for h in high_impact:
            if h in industry_type:
                return 1.0
        for m in medium_impact:
            if m in industry_type:
                return 0.8
        return 0.6
    
    def _get_status_factor(self, status: str) -> float:
        factors = {
            "operating": 1.0,
            "construction": 0.8,
            "planning": 0.5
        }
        return factors.get(status, 0.5)
    
    async def get_investment_recommendation(
        self,
        user_preferences: List[str],
        budget_range: Tuple[float, float]
    ) -> Dict[str, Any]:
        all_parks = await self.get_all_parks()
        
        matched_parks = []
        for park in all_parks:
            if park.nearby_property_price_min and park.nearby_property_price_max:
                if budget_range[0] <= park.nearby_property_price_max and budget_range[1] >= park.nearby_property_price_min:
                    pref_match = any(
                        pref.lower() in " ".join(park.industry_tags).lower()
                        for pref in user_preferences
                    )
                    if pref_match or not user_preferences:
                        matched_parks.append(park)
        
        recommendations = []
        for park in matched_parks[:5]:
            city_index = await self.get_city_integration_index(park.city)
            recommendations.append({
                "park": park.to_dict(),
                "city_index": city_index.to_dict() if city_index else None,
                "recommendation": f"您关注{park.industry_type}产业，推荐{park.city}{park.name}周边房源，该区域产业集聚，未来升值空间大。"
            })
        
        return {
            "recommendations": recommendations,
            "total_matched": len(matched_parks),
            "budget_range": budget_range
        }
    
    def _row_to_park(self, row: dict) -> IndustrialPark:
        return IndustrialPark(
            id=str(row.get("id", "")),
            name=row.get("name", ""),
            city=row.get("city", ""),
            district=row.get("district"),
            industry_type=row.get("industry_type"),
            industry_tags=row.get("industry_tags", []) or [],
            description=row.get("description"),
            development_goal=row.get("development_goal"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            status=row.get("status", "planning"),
            nearby_property_price_min=row.get("nearby_property_price_min"),
            nearby_property_price_max=row.get("nearby_property_price_max")
        )
    
    def _row_to_index(self, row: dict) -> CityIntegrationIndex:
        return CityIntegrationIndex(
            city=row.get("city", ""),
            district=row.get("district"),
            overall_score=row.get("overall_score", 0),
            industry_score=row.get("industry_score", 0),
            infrastructure_score=row.get("infrastructure_score", 0),
            policy_score=row.get("policy_score", 0),
            talent_score=row.get("talent_score", 0),
            investment_potential=row.get("investment_potential", "中等"),
            key_industries=row.get("key_industries", []) or [],
            growth_rate=row.get("growth_rate")
        )


_industrial_park_service: Optional[IndustrialParkService] = None


def get_industrial_park_service() -> Optional[IndustrialParkService]:
    return _industrial_park_service


async def init_industrial_park_service(db_pool) -> IndustrialParkService:
    global _industrial_park_service
    _industrial_park_service = IndustrialParkService(db_pool)
    return _industrial_park_service
