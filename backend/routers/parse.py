"""
查询解析API路由
提供轻量级的需求解析服务
支持 A/B 测试多版本解析
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import uuid

from ..services.entity_recognition import parse_natural_language
from ..services.entity_recognition_v2 import parse_natural_language_v2
from ..services.house_type_service import get_area_estimate
from ..services.price_estimator import estimate_price, get_district_price, DEFAULT_CITY_PRICES
from ..routers.district_info import get_district_info_detail
from ..auth import get_current_user_optional
from ..database import ABTestDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parse", tags=["parse"])


class ParseQueryRequest(BaseModel):
    """解析请求模型"""
    query: str
    enable_inference: bool = True


class ParsedQueryResponse(BaseModel):
    """解析响应模型"""
    raw_query: str
    city: Optional[str] = None
    district: Optional[str] = None
    community: Optional[str] = None
    room_count: Optional[int] = None
    hall_count: Optional[int] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    orientation: Optional[str] = None
    floor_type: Optional[str] = None
    decoration: Optional[str] = None
    is_school_district: Optional[bool] = None
    is_near_subway: Optional[bool] = None
    special_requirements: List[str] = []
    missing_fields: List[str] = []
    confidence: float = 0.0
    inferences: List[Dict[str, Any]] = []
    recommendations: Dict[str, List[Dict[str, Any]]] = {}


class EstimateRequest(BaseModel):
    """估算请求模型"""
    city: Optional[str] = None
    district: Optional[str] = None
    room_count: Optional[int] = None
    hall_count: Optional[int] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    special_requirements: List[str] = []


class EstimateResponse(BaseModel):
    """估算响应模型"""
    area_estimate: Optional[Dict[str, Any]] = None
    price_estimate: Optional[Dict[str, Any]] = None
    confidence: float = 0.0


@router.post("/query", response_model=ParsedQueryResponse)
async def parse_query(
    request: ParseQueryRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """
    解析用户查询，支持 A/B 测试
    
    Args:
        request: 解析请求
        current_user: 当前用户（可选）
        
    Returns:
        ParsedQueryResponse: 解析结果
    """
    query = request.query
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    
    use_v2 = False
    user_group = "control"
    
    if current_user:
        user_group = await ABTestDB.get_user_group(current_user["id"])
        use_v2 = user_group == "treatment"
        
        experiment = await ABTestDB.get_experiment_by_feature("query_parsing")
        if experiment and experiment["status"] == "running":
            metric_id = str(uuid.uuid4())
            await ABTestDB.record_metric(
                metric_id=metric_id,
                experiment_id=experiment["id"],
                user_id=current_user["id"],
                group_name=user_group,
                metric_type="parse_request",
                metric_value=1.0,
                metadata={"query_length": len(query)}
            )
    
    if use_v2:
        parsed_result = parse_natural_language_v2(query)
    else:
        parsed_result = parse_natural_language(query)
    
    response = ParsedQueryResponse(
        raw_query=query,
        city=_extract_value(parsed_result.city),
        district=_extract_value(parsed_result.district),
        community=_extract_value(parsed_result.community),
        room_count=_extract_value(parsed_result.room_count),
        hall_count=_extract_value(parsed_result.hall_count),
        area_min=_extract_value(parsed_result.area_min),
        area_max=_extract_value(parsed_result.area_max),
        price_min=_extract_value(parsed_result.price_min),
        price_max=_extract_value(parsed_result.price_max),
        orientation=_extract_value(parsed_result.orientation),
        floor_type=_extract_value(parsed_result.floor_type),
        decoration=_extract_value(parsed_result.decoration),
        is_school_district=_extract_value(parsed_result.is_school_district),
        is_near_subway=_extract_value(parsed_result.is_near_subway),
        special_requirements=parsed_result.special_requirements,
        missing_fields=parsed_result.missing_fields,
        confidence=_calculate_confidence(parsed_result)
    )
    
    if request.enable_inference:
        inferences = []
        
        if response.room_count and not response.area_min:
            hall_count = response.hall_count or 1
            city = response.city
            
            area_estimate = await get_area_estimate(
                room_count=response.room_count,
                hall_count=hall_count,
                city=city
            )
            
            if area_estimate:
                response.area_min = area_estimate["min_area"]
                response.area_max = area_estimate["max_area"]
                response.area_avg = area_estimate["avg_area"]
                response.area_estimated = True
                
                inferences.append({
                    "field": "area",
                    "inferred_value": {
                        "min": area_estimate["min_area"],
                        "max": area_estimate["max_area"],
                        "avg": area_estimate["avg_area"]
                    },
                    "confidence": area_estimate["confidence"],
                    "reasoning": f"根据{response.room_count}室{hall_count}厅户型估算"
                })
        
        if response.city and not response.price_max:
            city = response.city
            district = response.district
            house_type = None
            if response.room_count:
                hall_count = response.hall_count or 1
                house_type = f"{response.room_count}室{hall_count}厅"
            
            price_estimate = await estimate_price(
                city=city,
                district=district,
                area_min=response.area_min,
                area_max=response.area_max,
                house_type=house_type,
                special_requirements=response.special_requirements
            )
            
            if price_estimate:
                response.price_min = price_estimate["total_price"]["min"]
                response.price_max = price_estimate["total_price"]["max"]
                response.price_avg = price_estimate["total_price"]["avg"]
                response.price_estimated = True
                
                inferences.append({
                    "field": "price",
                    "inferred_value": price_estimate["total_price"],
                    "confidence": price_estimate["confidence"],
                    "reasoning": f"根据{city}{' ' + district if district else ''}房价估算"
                })
        
        response.inferences = inferences
    
    response.recommendations = await _get_recommendations(response)
    
    return response


@router.post("/estimate", response_model=EstimateResponse)
async def estimate_missing_fields(request: EstimateRequest):
    """
    估算缺失字段
    
    Args:
        request: 估算请求
        
    Returns:
        EstimateResponse: 估算结果
    """
    response = EstimateResponse()
    confidence = 0.0
    
    if request.room_count and not request.area_min:
        area_estimate = await get_area_estimate(
            room_count=request.room_count,
            hall_count=request.hall_count or 1,
            city=request.city
        )
        
        if area_estimate:
            response.area_estimate = {
                "min": area_estimate["min_area"],
                "max": area_estimate["max_area"],
                "avg": area_estimate["avg_area"],
                "common_areas": area_estimate.get("common_areas", [])
            }
            confidence = max(confidence, area_estimate["confidence"])
    
    if request.city and not request.price_max:
        house_type = None
        if request.room_count:
            house_type = f"{request.room_count}室{request.hall_count or 1}厅"
        
        price_estimate = await estimate_price(
            city=request.city,
            district=request.district,
            area_min=request.area_min,
            area_max=request.area_max,
            house_type=house_type,
            special_requirements=request.special_requirements
        )
        
        if price_estimate:
            response.price_estimate = {
                "min": price_estimate["total_price"]["min"],
                "max": price_estimate["total_price"]["max"],
                "avg": price_estimate["total_price"]["avg"],
                "unit_price": price_estimate["adjusted_unit_price"]
            }
            confidence = max(confidence, price_estimate["confidence"])
    
    response.confidence = confidence
    return response


@router.get("/recommendations/cities")
async def get_city_recommendations():
    """获取城市推荐列表"""
    cities = list(DEFAULT_CITY_PRICES.keys())
    return {
        "cities": [
            {"value": city, "label": city, "has_data": True}
            for city in cities
        ]
    }


@router.get("/recommendations/districts/{city}")
async def get_district_recommendations(city: str):
    """获取区域推荐列表"""
    if city in DEFAULT_CITY_PRICES:
        districts = DEFAULT_CITY_PRICES[city]
        return {
            "districts": [
                {"value": district, "label": district, "avg_price": prices["avg"]}
                for district, prices in districts.items()
            ]
        }
    return {"districts": []}


@router.get("/recommendations/areas")
async def get_area_recommendations(room_count: Optional[int] = None):
    """获取面积推荐列表"""
    common_areas = [
        {"value": 50, "label": "50㎡ (小户型)", "rooms": 1},
        {"value": 70, "label": "70㎡ (两室)", "rooms": 2},
        {"value": 90, "label": "90㎡ (小三室)", "rooms": 3},
        {"value": 100, "label": "100㎡ (三室)", "rooms": 3},
        {"value": 120, "label": "120㎡ (大三室)", "rooms": 3},
        {"value": 140, "label": "140㎡ (四室)", "rooms": 4},
        {"value": 160, "label": "160㎡ (大四室)", "rooms": 4},
        {"value": 180, "label": "180㎡ (五室)", "rooms": 5},
        {"value": 200, "label": "200㎡ (大平层)", "rooms": 5},
    ]
    
    if room_count:
        common_areas = [a for a in common_areas if a["rooms"] == room_count]
        if not common_areas:
            common_areas = [a for a in common_areas if abs(a["rooms"] - room_count) <= 1]
    
    return {"areas": common_areas}


@router.get("/recommendations/prices")
async def get_price_recommendations(city: Optional[str] = None):
    """获取价格推荐列表"""
    common_prices = [
        {"value": 100, "label": "100万以内", "tier": "经济型"},
        {"value": 200, "label": "200万以内", "tier": "入门级"},
        {"value": 300, "label": "300万以内", "tier": "刚需"},
        {"value": 500, "label": "500万以内", "tier": "改善型"},
        {"value": 800, "label": "800万以内", "tier": "中高端"},
        {"value": 1000, "label": "1000万以内", "tier": "高端"},
        {"value": 1500, "label": "1500万以内", "tier": "豪华"},
        {"value": 2000, "label": "2000万以内", "tier": "豪宅"},
        {"value": 3000, "label": "3000万以内", "tier": "顶级豪宅"},
    ]
    
    return {"prices": common_prices}


def _extract_value(entity) -> Any:
    """提取实体值"""
    if entity is None:
        return None
    return entity.value


def _calculate_confidence(parsed) -> float:
    """计算整体置信度"""
    fields = [
        "city", "district", "community",
        "room_count", "hall_count",
        "area_min", "area_max",
        "price_min", "price_max",
    ]
    
    total_confidence = 0
    field_count = 0
    
    for field in fields:
        entity = getattr(parsed, field, None)
        if entity and entity.value is not None:
            total_confidence += entity.confidence
            field_count += 1
    
    if field_count == 0:
        return 0.0
    
    return round(total_confidence / field_count, 2)


async def _get_recommendations(response: ParsedQueryResponse) -> Dict[str, List[Dict[str, Any]]]:
    """获取推荐值"""
    recommendations = {}
    
    if response.city and not response.district:
        city_prices = DEFAULT_CITY_PRICES.get(response.city, {})
        if city_prices:
            recommendations["districts"] = [
                {"value": d, "label": d, "avg_price": p.get("avg", 0)}
                for d, p in city_prices.items()
            ][:5]
    
    if response.room_count and not response.area_min:
        area_estimate = await get_area_estimate(
            room_count=response.room_count,
            hall_count=response.hall_count or 1,
            city=response.city
        )
        if area_estimate and area_estimate.get("common_areas"):
            recommendations["areas"] = [
                {"value": a, "label": f"{a}㎡"}
                for a in area_estimate["common_areas"]
            ]
    
    if response.city and not response.price_max:
        city = response.city
        district = response.district
        
        city_prices = DEFAULT_CITY_PRICES.get(city, {})
        if city_prices:
            district_prices = city_prices.get(district, {}) if district else None
            if district_prices:
                avg_price = district_prices.get("avg", 0)
                area = response.area_min or 100
                estimated_total = avg_price * area / 10000
                
                recommendations["prices"] = [
                    {"value": int(estimated_total * 0.8), "label": f"约{int(estimated_total * 0.8)}万"},
                    {"value": int(estimated_total), "label": f"约{int(estimated_total)}万"},
                    {"value": int(estimated_total * 1.2), "label": f"约{int(estimated_total * 1.2)}万"},
                ]
    
    return recommendations
