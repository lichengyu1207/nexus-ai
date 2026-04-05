"""
歧义消解API路由
处理用户输入中的歧义实体，提供候选选项
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..services.price_estimator import DEFAULT_CITY_PRICES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/disambiguate", tags=["disambiguate"])


AMBIGUOUS_DISTRICTS = {
    "南山区": [
        {"city": "深圳", "district": "南山区", "description": "深圳核心区域，科技产业聚集地", "avg_price": 95000},
        {"city": "汕头", "district": "南山区", "description": "汕头市辖区", "avg_price": 8000},
    ],
    "福田区": [
        {"city": "深圳", "district": "福田区", "description": "深圳中心城区，金融中心", "avg_price": 85000},
    ],
    "朝阳区": [
        {"city": "北京", "district": "朝阳区", "description": "北京经济强区，国际化窗口", "avg_price": 75000},
        {"city": "长春", "district": "朝阳区", "description": "长春市辖区", "avg_price": 9000},
    ],
    "海淀区": [
        {"city": "北京", "district": "海淀区", "description": "北京科教文化中心", "avg_price": 90000},
    ],
    "浦东新区": [
        {"city": "上海", "district": "浦东新区", "description": "上海金融中心", "avg_price": 70000},
    ],
    "天河区": [
        {"city": "广州", "district": "天河区", "description": "广州城市中心", "avg_price": 65000},
    ],
    "西湖区": [
        {"city": "杭州", "district": "西湖区", "description": "杭州文化旅游中心", "avg_price": 55000},
        {"city": "南昌", "district": "西湖区", "description": "南昌市辖区", "avg_price": 10000},
    ],
    "高新区": [
        {"city": "成都", "district": "高新区", "description": "成都科技创新中心", "avg_price": 28000},
        {"city": "苏州", "district": "高新区", "description": "苏州高新技术开发区", "avg_price": 30000},
        {"city": "西安", "district": "高新区", "description": "西安高新技术开发区", "avg_price": 15000},
        {"city": "郑州", "district": "高新区", "description": "郑州高新技术开发区", "avg_price": 12000},
    ],
    "新城区": [
        {"city": "西安", "district": "新城区", "description": "西安市中心城区", "avg_price": 12000},
        {"city": "呼和浩特", "district": "新城区", "description": "呼和浩特市辖区", "avg_price": 8000},
    ],
    "宝安区": [
        {"city": "深圳", "district": "宝安区", "description": "深圳西部中心", "avg_price": 60000},
    ],
    "龙岗区": [
        {"city": "深圳", "district": "龙岗区", "description": "深圳东部中心", "avg_price": 45000},
    ],
}

AMBIGUOUS_COMMUNITIES = {
    "万科城": [
        {"city": "深圳", "district": "龙岗区", "community": "万科城", "description": "大型综合社区"},
        {"city": "广州", "district": "黄埔区", "community": "万科城", "description": "品质住宅小区"},
        {"city": "成都", "district": "高新区", "community": "万科城", "description": "城市综合体"},
    ],
    "华润城": [
        {"city": "深圳", "district": "南山区", "community": "华润城", "description": "大型综合开发项目"},
    ],
    "碧桂园": [
        {"city": "广州", "district": "增城区", "community": "碧桂园", "description": "大型住宅社区"},
        {"city": "佛山", "district": "顺德区", "community": "碧桂园", "description": "碧桂园总部所在地"},
    ],
}


class DisambiguateRequest(BaseModel):
    """消歧请求模型"""
    query: str
    ambiguous_field: str
    current_value: str
    context: Optional[Dict[str, Any]] = None


class CandidateOption(BaseModel):
    """候选选项模型"""
    value: str
    label: str
    description: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    community: Optional[str] = None
    avg_price: Optional[float] = None
    confidence: float = 0.5


class DisambiguateResponse(BaseModel):
    """消歧响应模型"""
    field: str
    original_value: str
    message: str
    candidates: List[CandidateOption]
    requires_selection: bool


class CheckAmbiguityRequest(BaseModel):
    """检查歧义请求模型"""
    query: str
    city: Optional[str] = None
    district: Optional[str] = None
    community: Optional[str] = None


class CheckAmbiguityResponse(BaseModel):
    """检查歧义响应模型"""
    has_ambiguity: bool
    ambiguous_fields: List[Dict[str, Any]]


@router.post("/check", response_model=CheckAmbiguityResponse)
async def check_ambiguity(request: CheckAmbiguityRequest):
    """
    检查是否存在歧义
    
    Args:
        request: 检查请求
        
    Returns:
        CheckAmbiguityResponse: 歧义检查结果
    """
    ambiguous_fields = []
    
    if request.district and not request.city:
        if request.district in AMBIGUOUS_DISTRICTS:
            candidates = AMBIGUOUS_DISTRICTS[request.district]
            if len(candidates) > 1:
                ambiguous_fields.append({
                    "field": "district",
                    "value": request.district,
                    "message": f"您提到的\"{request.district}\"在多个城市存在，请确认具体位置",
                    "candidate_count": len(candidates)
                })
    
    if request.community and not request.city:
        community_name = request.community.replace("小区", "").replace("花园", "")
        for key, candidates in AMBIGUOUS_COMMUNITIES.items():
            if community_name in key or key in community_name:
                if len(candidates) > 1:
                    ambiguous_fields.append({
                        "field": "community",
                        "value": request.community,
                        "message": f"您提到的\"{request.community}\"在多个区域存在，请确认具体位置",
                        "candidate_count": len(candidates)
                    })
                break
    
    return CheckAmbiguityResponse(
        has_ambiguity=len(ambiguous_fields) > 0,
        ambiguous_fields=ambiguous_fields
    )


@router.post("/resolve", response_model=DisambiguateResponse)
async def resolve_ambiguity(request: DisambiguateRequest):
    """
    解析歧义，返回候选选项
    
    Args:
        request: 消歧请求
        
    Returns:
        DisambiguateResponse: 消歧响应
    """
    candidates = []
    message = ""
    
    if request.ambiguous_field == "district":
        district_name = request.current_value
        
        if district_name in AMBIGUOUS_DISTRICTS:
            raw_candidates = AMBIGUOUS_DISTRICTS[district_name]
            
            if request.context and request.context.get("city"):
                city = request.context["city"]
                raw_candidates = [c for c in raw_candidates if c["city"] == city]
            
            for c in raw_candidates:
                candidates.append(CandidateOption(
                    value=f"{c['city']}_{c['district']}",
                    label=f"{c['city']} {c['district']}",
                    description=c.get("description"),
                    city=c["city"],
                    district=c["district"],
                    avg_price=c.get("avg_price"),
                    confidence=0.8 if c["city"] in DEFAULT_CITY_PRICES else 0.5
                ))
            
            if len(candidates) > 1:
                message = f"您提到的\"{district_name}\"在以下城市存在，请选择："
            elif len(candidates) == 1:
                message = f"已为您匹配到 {candidates[0].city} {candidates[0].district}"
        else:
            for city, districts in DEFAULT_CITY_PRICES.items():
                for district, prices in districts.items():
                    if district_name in district or district in district_name:
                        candidates.append(CandidateOption(
                            value=f"{city}_{district}",
                            label=f"{city} {district}",
                            city=city,
                            district=district,
                            avg_price=prices["avg"],
                            confidence=0.6
                        ))
            
            if candidates:
                message = f"找到以下匹配\"{district_name}\"的区域："
            else:
                message = f"未找到\"{district_name}\"的匹配信息"
    
    elif request.ambiguous_field == "community":
        community_name = request.current_value
        
        for key, raw_candidates in AMBIGUOUS_COMMUNITIES.items():
            if key in community_name or community_name in key:
                for c in raw_candidates:
                    candidates.append(CandidateOption(
                        value=f"{c['city']}_{c['district']}_{c['community']}",
                        label=f"{c['city']} {c['district']} {c['community']}",
                        description=c.get("description"),
                        city=c["city"],
                        district=c["district"],
                        community=c["community"],
                        confidence=0.7
                    ))
                break
    
    elif request.ambiguous_field == "city":
        city_name = request.current_value
        
        if city_name in DEFAULT_CITY_PRICES:
            districts = DEFAULT_CITY_PRICES[city_name]
            for district, prices in districts.items():
                candidates.append(CandidateOption(
                    value=district,
                    label=f"{city_name} {district}",
                    city=city_name,
                    district=district,
                    avg_price=prices["avg"],
                    confidence=0.8
                ))
            message = f"请选择{city_name}的具体区域："
    
    requires_selection = len(candidates) > 1
    
    if not candidates:
        candidates.append(CandidateOption(
            value=request.current_value,
            label=request.current_value,
            confidence=0.3
        ))
        message = f"未找到\"{request.current_value}\"的明确匹配，将使用原始值"
    
    return DisambiguateResponse(
        field=request.ambiguous_field,
        original_value=request.current_value,
        message=message,
        candidates=candidates,
        requires_selection=requires_selection
    )


@router.get("/districts/{district_name}")
async def get_district_candidates(district_name: str):
    """
    获取区域候选列表
    
    Args:
        district_name: 区域名称
        
    Returns:
        候选列表
    """
    candidates = []
    
    if district_name in AMBIGUOUS_DISTRICTS:
        for c in AMBIGUOUS_DISTRICTS[district_name]:
            candidates.append({
                "city": c["city"],
                "district": c["district"],
                "description": c.get("description"),
                "avg_price": c.get("avg_price"),
                "label": f"{c['city']} {c['district']}"
            })
    else:
        for city, districts in DEFAULT_CITY_PRICES.items():
            for district, prices in districts.items():
                if district_name in district or district in district_name:
                    candidates.append({
                        "city": city,
                        "district": district,
                        "avg_price": prices["avg"],
                        "label": f"{city} {district}"
                    })
    
    return {
        "district_name": district_name,
        "candidates": candidates,
        "total": len(candidates)
    }


@router.get("/cities")
async def get_supported_cities():
    """获取支持的城市列表"""
    cities = []
    for city, districts in DEFAULT_CITY_PRICES.items():
        avg_prices = [d["avg"] for d in districts.values()]
        cities.append({
            "city": city,
            "district_count": len(districts),
            "avg_price": sum(avg_prices) / len(avg_prices) if avg_prices else 0
        })
    
    return {
        "cities": cities,
        "total": len(cities)
    }
