# -*- coding: utf-8 -*-
"""
Industrial Park API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

router = APIRouter(prefix="/api/industrial", tags=["Industrial Park"])


class InvestmentRequest(BaseModel):
    preferences: List[str] = Field(default_factory=list)
    budget_min: float = 0
    budget_max: float = 100000


class PropertyImpactRequest(BaseModel):
    latitude: float
    longitude: float
    property_price: float


async def get_industrial_service_dep():
    from backend.services.industrial_park.industrial_park_service import (
        get_industrial_park_service, init_industrial_park_service
    )
    from backend.database_pg import PostgreSQLConnectionPool
    
    service = get_industrial_park_service()
    if not service:
        pool = await PostgreSQLConnectionPool.get_instance()
        if pool._pool is None:
            await pool._initialize()
        service = await init_industrial_park_service(pool._pool)
    return service


@router.get("/parks")
async def list_parks(
    city: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    service = Depends(get_industrial_service_dep)
):
    if city:
        parks = await service.get_parks_by_city(city)
    elif industry:
        parks = await service.get_parks_by_industry(industry)
    else:
        parks = await service.get_all_parks(limit)
    
    return {
        "parks": [p.to_dict() for p in parks],
        "total": len(parks)
    }


@router.get("/parks/nearby")
async def get_nearby_parks(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(50, description="Radius in km"),
    service = Depends(get_industrial_service_dep)
):
    parks_with_distance = await service.get_nearby_parks(lat, lng, radius)
    
    return {
        "parks": [
            {**p.to_dict(), "distance_km": round(d, 2)}
            for p, d in parks_with_distance
        ],
        "total": len(parks_with_distance),
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius
    }


@router.get("/index/{city}")
async def get_city_index(
    city: str,
    service = Depends(get_industrial_service_dep)
):
    index = await service.get_city_integration_index(city)
    if not index:
        raise HTTPException(status_code=404, detail="City index not found")
    return index.to_dict()


@router.post("/property-impact")
async def calculate_property_impact(
    request: PropertyImpactRequest,
    service = Depends(get_industrial_service_dep)
):
    result = await service.calculate_property_impact(
        request.latitude,
        request.longitude,
        request.property_price
    )
    return result


@router.post("/recommendation")
async def get_investment_recommendation(
    request: InvestmentRequest,
    service = Depends(get_industrial_service_dep)
):
    result = await service.get_investment_recommendation(
        request.preferences,
        (request.budget_min, request.budget_max)
    )
    return result


@router.get("/map-data")
async def get_map_data(
    service = Depends(get_industrial_service_dep)
):
    parks = await service.get_all_parks()
    
    markers = []
    for p in parks:
        if p.latitude and p.longitude:
            markers.append({
                "id": p.id,
                "name": p.name,
                "lat": p.latitude,
                "lng": p.longitude,
                "city": p.city,
                "industry": p.industry_type,
                "status": p.status,
                "color": _get_marker_color(p.industry_type)
            })
    
    return {
        "map_type": "hunan_province",
        "center": {"lat": 28.23, "lng": 112.94},
        "zoom": 7,
        "markers": markers
    }


def _get_marker_color(industry_type: Optional[str]) -> str:
    if not industry_type:
        return "#888888"
    
    colors = {
        "锂电池": "#FF6B6B",
        "新能源": "#4ECDC4",
        "3D玻璃": "#45B7D1",
        "临空经济": "#96CEB4",
        "新材料": "#FFEAA7",
        "高端制造": "#DDA0DD"
    }
    
    for key, color in colors.items():
        if key in industry_type:
            return color
    return "#888888"


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "industrial_park",
        "timestamp": datetime.utcnow().isoformat()
    }
