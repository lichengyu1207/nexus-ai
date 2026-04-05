"""
地理信息API路由
提供地理解析、数据查询、自动补全等接口
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from ..services.geo_parser import GeoParser
from ..services.geo_filter import GeoDataFilter, FilterCondition

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geo", tags=["地理信息"])

# 初始化服务
geo_parser = GeoParser()
geo_filter = GeoDataFilter()


class GeoParseRequest(BaseModel):
    """地理解析请求"""
    text: str = Field(..., description="待解析的文本")


class GeoQueryRequest(BaseModel):
    """地理查询请求"""
    geo: Dict[str, Any] = Field(..., description="地理实体")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="筛选条件")
    limit: int = Field(default=10, description="返回数量限制")
    offset: int = Field(default=0, description="偏移量")


class POIRequest(BaseModel):
    """POI查询请求"""
    community_id: str = Field(..., description="小区ID")
    poi_type: Optional[str] = Field(default=None, description="POI类型")
    limit: int = Field(default=20, description="返回数量限制")


@router.post("/parse")
async def parse_geo(request: GeoParseRequest):
    """
    地理解析接口
    从自然语言中提取标准化地理实体
    
    示例:
    - 输入: {"text": "深圳南山区华润城"}
    - 输出: {"province": "广东省", "city": "深圳市", "district": "南山区", "community": "华润城", ...}
    """
    try:
        result = geo_parser.parse(request.text)
        return geo_parser.to_dict(result)
    except Exception as e:
        logger.error(f"Geo parse failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest")
async def suggest_geo(
    q: str = Query(..., description="查询字符串", min_length=1),
    limit: int = Query(10, description="返回数量限制")
):
    """
    自动补全接口
    根据输入返回匹配的地理实体建议
    
    示例:
    - 输入: /api/geo/suggest?q=深圳南
    - 输出: [{"name": "深圳市", "type": "city"}, {"name": "南山区", "type": "district"}]
    """
    try:
        suggestions = geo_parser.suggest(q, limit)
        return {"query": q, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Suggest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_geo(request: GeoQueryRequest):
    """
    基于地理实体查询房产数据
    
    示例:
    - 输入: {"geo": {"city": "深圳市", "district": "南山区"}, "filters": {"price_max": 10000000}}
    - 输出: {"total": 123, "communities": [...], "houses": [...]}
    """
    try:
        # 构建GeoResult
        from ..services.geo_parser import GeoResult
        geo_result = GeoResult(
            province=request.geo.get("province"),
            province_id=request.geo.get("province_id"),
            city=request.geo.get("city"),
            city_id=request.geo.get("city_id"),
            district=request.geo.get("district"),
            district_id=request.geo.get("district_id"),
            community=request.geo.get("community"),
            community_id=request.geo.get("community_id"),
            level=request.geo.get("level", "unknown"),
            raw_text=str(request.geo)
        )
        
        # 构建筛选条件
        filters = None
        if request.filters:
            filters = FilterCondition(
                price_min=request.filters.get("price_min"),
                price_max=request.filters.get("price_max"),
                area_min=request.filters.get("area_min"),
                area_max=request.filters.get("area_max"),
                rooms=request.filters.get("rooms"),
                tags=request.filters.get("tags", [])
            )
        
        # 查询数据
        results = await geo_filter.query_by_geo(
            geo_result, filters, request.limit, request.offset
        )
        
        return results
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pois")
async def get_pois(
    community_id: str = Query(..., description="小区ID"),
    type: Optional[str] = Query(None, description="POI类型"),
    limit: int = Query(20, description="返回数量限制")
):
    """
    获取周边POI
    
    示例:
    - 输入: /api/geo/pois?community_id=community-001&type=地铁站
    - 输出: [{"type": "地铁站", "name": "科技园站", "distance": 300}, ...]
    """
    try:
        pois = await geo_filter.get_pois(community_id, type, limit)
        return {"community_id": community_id, "pois": pois}
    except Exception as e:
        logger.error(f"Get POIs failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cities")
async def get_cities():
    """
    获取所有城市列表
    """
    try:
        cities = []
        for city_name, city_data in geo_parser.HOT_CITIES.items():
            cities.append({
                "id": city_data["id"],
                "name": city_name,
                "province": city_data["province"],
                "district_count": len(city_data["districts"])
            })
        return {"cities": cities}
    except Exception as e:
        logger.error(f"Get cities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/districts/{city_id}")
async def get_districts(city_id: str):
    """
    获取城市下的区域列表
    """
    try:
        districts = []
        for city_name, city_data in geo_parser.HOT_CITIES.items():
            if city_data["id"] == city_id:
                for district_name, district_data in city_data["districts"].items():
                    districts.append({
                        "id": district_data["id"],
                        "name": district_name,
                        "avg_price": district_data.get("avg_price")
                    })
                break
        
        return {"city_id": city_id, "districts": districts}
    except Exception as e:
        logger.error(f"Get districts failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/communities")
async def get_communities(
    city: Optional[str] = Query(None, description="城市名称"),
    district: Optional[str] = Query(None, description="区域名称"),
    limit: int = Query(20, description="返回数量限制")
):
    """
    获取小区列表
    """
    try:
        communities = []
        for community_name, community_data in geo_parser.HOT_COMMUNITIES.items():
            if city and community_data["city"] != city:
                continue
            if district and community_data["district"] != district:
                continue
            
            communities.append({
                "id": community_data["id"],
                "name": community_name,
                "city": community_data["city"],
                "district": community_data["district"],
                "avg_price": community_data["avg_price"]
            })
            
            if len(communities) >= limit:
                break
        
        return {"total": len(communities), "communities": communities}
    except Exception as e:
        logger.error(f"Get communities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
