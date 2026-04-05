"""
预览API路由
支持未登录用户预览分析结果
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preview", tags=["preview"])


class PreviewRequest(BaseModel):
    """预览请求模型"""
    query: str


class PreviewResponse(BaseModel):
    """预览响应模型"""
    query: str
    location: Optional[Dict[str, str]] = None
    market_overview: Optional[Dict[str, Any]] = None
    price_range: Optional[Dict[str, float]] = None
    key_highlights: list[str] = []
    sample_report_sections: list[str] = []
    registration_incentive: Dict[str, Any]


def extract_location(query: str) -> Dict[str, str]:
    """从查询中提取位置信息"""
    location = {"city": None, "district": None, "community": None}
    
    city_patterns = [
        r"深圳", r"北京", r"上海", r"广州", r"杭州", r"成都", 
        r"武汉", r"南京", r"苏州", r"西安", r"重庆", r"天津"
    ]
    
    district_patterns = {
        "深圳": [r"南山", r"福田", r"罗湖", r"宝安", r"龙岗", r"龙华", r"光明", r"坪山"],
        "北京": [r"朝阳", r"海淀", r"西城", r"东城", r"丰台", r"通州", r"大兴", r"昌平"],
        "上海": [r"浦东", r"黄浦", r"静安", r"徐汇", r"长宁", r"普陀", r"虹口", r"杨浦"],
    }
    
    for city_pattern in city_patterns:
        if re.search(city_pattern, query):
            location["city"] = city_pattern
            break
    
    if location["city"] and location["city"] in district_patterns:
        for district_pattern in district_patterns[location["city"]]:
            if re.search(district_pattern, query):
                location["district"] = district_pattern
                break
    
    community_patterns = [
        r"([\u4e00-\u9fa5]{2,}(?:花园|小区|公寓|苑|城|府|院|居|庭|阁|轩|园))",
        r"([\u4e00-\u9fa5]{2,}(?:实验|外国语|重点)[\u4e00-\u9fa5]*学区)",
    ]
    
    for pattern in community_patterns:
        match = re.search(pattern, query)
        if match:
            location["community"] = match.group(1)
            break
    
    return location


def generate_mock_preview_data(location: Dict[str, str]) -> Dict[str, Any]:
    """生成模拟预览数据"""
    city = location.get("city") or "深圳"
    district = location.get("district") or "核心区域"
    
    base_prices = {
        "深圳": {"南山": 95000, "福田": 85000, "罗湖": 65000, "宝安": 60000, "龙华": 55000},
        "北京": {"朝阳": 75000, "海淀": 90000, "西城": 100000, "东城": 95000},
        "上海": {"浦东": 70000, "黄浦": 100000, "静安": 85000, "徐汇": 80000},
    }
    
    city_prices = base_prices.get(city, {"核心区域": 50000})
    avg_price = city_prices.get(district, 50000)
    
    return {
        "market_overview": {
            "avg_price": avg_price,
            "price_trend": "稳中有升" if avg_price > 60000 else "平稳",
            "year_change": 3.5 if avg_price > 70000 else 2.1,
            "transaction_volume": "活跃" if avg_price > 60000 else "正常",
        },
        "price_range": {
            "min": avg_price * 0.85,
            "max": avg_price * 1.15,
            "median": avg_price,
        },
        "key_highlights": [
            f"{city}{district}区域房价均价约{avg_price/10000:.1f}万/㎡",
            "该区域交通便利，配套成熟" if avg_price > 60000 else "该区域发展潜力较大",
            "学区资源丰富，适合家庭居住" if "学" in str(location.get("community", "")) else "周边配套完善",
            "近一年房价走势平稳，投资风险较低",
        ],
        "sample_report_sections": [
            "执行摘要：基于大数据分析，为您提供专业的房产估值...",
            "核心发现：该区域市场活跃度高，供需平衡...",
            "周边配套：学校、医院、商场、地铁等配套设施...",
            "投资建议：根据您的需求，我们建议...",
        ]
    }


@router.post("/", response_model=PreviewResponse)
async def create_preview(request: PreviewRequest):
    """
    创建预览分析
    
    无需登录，返回部分分析结果以吸引用户注册
    """
    query = request.query.strip()
    
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="请输入有效的地址或区域")
    
    location = extract_location(query)
    mock_data = generate_mock_preview_data(location)
    
    return PreviewResponse(
        query=query,
        location=location,
        market_overview=mock_data["market_overview"],
        price_range=mock_data["price_range"],
        key_highlights=mock_data["key_highlights"],
        sample_report_sections=mock_data["sample_report_sections"],
        registration_incentive={
            "title": "注册获取完整报告",
            "benefits": [
                "查看完整分析报告",
                "获取详细投资建议",
                "导出PDF报告",
                "免费3次分析机会",
            ],
            "cta_text": "免费注册，查看完整报告",
        }
    )
