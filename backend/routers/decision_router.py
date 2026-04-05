"""
命盘与房产综合决策API路由
将命盘解读与房产建议深度结合
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.mingpan_property_decision import mingpan_property_decision_service

router = APIRouter(prefix="/api/decision", tags=["decision"])


class MingpanInfo(BaseModel):
    """命盘信息"""
    main_stars: List[str] = []
    element: str = "木"
    age: int = 30
    palaces: Dict[str, Any] = {}


class BudgetInfo(BaseModel):
    """预算信息"""
    total: float = 200
    annual_income: float = 30
    down_payment: Optional[float] = None


class Requirements(BaseModel):
    """购房需求"""
    city_preference: Optional[List[str]] = None
    property_type: Optional[str] = None
    size: Optional[str] = None


class DecisionRequest(BaseModel):
    """综合决策请求"""
    mingpan_info: MingpanInfo
    budget: BudgetInfo
    requirements: Optional[Requirements] = None


class DecisionResponse(BaseModel):
    """综合决策响应"""
    report: str
    city_recommendations: List[Dict[str, Any]]
    timing_advice: Dict[str, Any]
    timestamp: str


@router.post("/analyze", response_model=DecisionResponse)
async def analyze_decision(request: DecisionRequest):
    """
    综合分析命盘与房产决策
    
    Args:
        request: 综合决策请求
        
    Returns:
        DecisionResponse: 综合决策报告
    """
    mingpan_info = request.mingpan_info.dict()
    budget_info = request.budget.dict()
    requirements = request.requirements.dict() if request.requirements else {}
    
    result = mingpan_property_decision_service.analyze_comprehensive(
        mingpan_info=mingpan_info,
        budget=budget_info,
        requirements=requirements
    )
    
    return DecisionResponse(
        report=result["report"],
        city_recommendations=result["city_recommendations"],
        timing_advice=result["timing_advice"],
        timestamp=result["timestamp"]
    )


@router.get("/cities")
async def get_city_list():
    """获取支持的城市列表"""
    from ..services.mingpan_property_decision import mingpan_property_decision_service
    
    cities = []
    for name, info in mingpan_property_decision_service.city_profiles.items():
        cities.append({
            "name": name,
            "element": info["element"],
            "avg_price": info["avg_price"],
            "features": info["features"],
            "suitable_patterns": info["suitable_patterns"],
            "talent_policy": info["talent_policy"]
        })
    
    return {"cities": cities}


@router.get("/elements")
async def get_element_guide():
    """获取五行方位指南"""
    from ..services.mingpan_property_decision import mingpan_property_decision_service
    
    guide = []
    for element, info in mingpan_property_decision_service.element_directions.items():
        guide.append({
            "element": element,
            "favorable_directions": info["favorable"],
            "unfavorable_directions": info.get("unfavorable", []),
            "favorable_cities": info["cities"],
            "housing_features": info["features"]
        })
    
    return {"elements": guide}


@router.get("/stars")
async def get_star_traits():
    """获取主星特质"""
    from ..services.mingpan_property_decision import mingpan_property_decision_service
    
    stars = []
    for star, info in mingpan_property_decision_service.star_traits.items():
        stars.append({
            "star": star,
            "career": info["career"],
            "wealth": info["wealth"],
            "housing": info["housing"],
            "advice": info["advice"]
        })
    
    return {"stars": stars}
