"""
SEO着陆页API路由
支持搜索词动态页面和数据预加载
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo", tags=["seo"])


class SEOLandingRequest(BaseModel):
    """SEO着陆页请求"""
    q: str


class SEOLandingResponse(BaseModel):
    """SEO着陆页响应"""
    query: str
    location: Dict[str, Optional[str]]
    page_title: str
    page_description: str
    market_data: Dict[str, Any]
    price_chart_data: List[Dict[str, Any]]
    key_metrics: Dict[str, Any]
    mascot_message: str
    registration_cta: Dict[str, str]


CITY_DATA = {
    "深圳": {
        "districts": ["南山", "福田", "罗湖", "宝安", "龙岗", "龙华", "光明", "坪山", "盐田"],
        "avg_price": 65000,
        "price_trend": "稳中有升",
        "year_change": 3.2,
        "highlights": ["科技创新中心", "年轻人口流入", "产业升级"],
    },
    "北京": {
        "districts": ["朝阳", "海淀", "西城", "东城", "丰台", "通州", "大兴", "昌平", "顺义"],
        "avg_price": 72000,
        "price_trend": "平稳",
        "year_change": 1.8,
        "highlights": ["首都核心区", "教育资源丰富", "政策调控严格"],
    },
    "上海": {
        "districts": ["浦东", "黄浦", "静安", "徐汇", "长宁", "普陀", "虹口", "杨浦", "闵行", "宝山"],
        "avg_price": 68000,
        "price_trend": "稳中有升",
        "year_change": 2.5,
        "highlights": ["金融中心", "国际化程度高", "配套成熟"],
    },
    "广州": {
        "districts": ["天河", "越秀", "海珠", "荔湾", "白云", "番禺", "黄埔", "花都"],
        "avg_price": 38000,
        "price_trend": "平稳",
        "year_change": 1.5,
        "highlights": ["商业中心", "交通便利", "生活成本适中"],
    },
    "杭州": {
        "districts": ["西湖", "上城", "拱墅", "滨江", "萧山", "余杭", "临平"],
        "avg_price": 42000,
        "price_trend": "稳中有升",
        "year_change": 2.8,
        "highlights": ["互联网产业", "宜居城市", "人才流入"],
    },
    "成都": {
        "districts": ["锦江", "青羊", "武侯", "金牛", "成华", "高新", "天府新区"],
        "avg_price": 22000,
        "price_trend": "上涨",
        "year_change": 4.5,
        "highlights": ["新一线城市", "生活成本低", "发展潜力大"],
    },
    "长沙": {
        "districts": ["岳麓", "芙蓉", "天心", "开福", "雨花", "望城", "长沙县"],
        "avg_price": 12000,
        "price_trend": "平稳",
        "year_change": 2.0,
        "highlights": ["宜居城市", "房价适中", "教育资源丰富"],
    },
}

DISTRICT_DATA = {
    "深圳": {
        "南山": {"avg_price": 95000, "year_change": 3.5, "transaction_volume": "活跃", "liquidity": "高"},
        "福田": {"avg_price": 85000, "year_change": 2.8, "transaction_volume": "活跃", "liquidity": "高"},
        "罗湖": {"avg_price": 65000, "year_change": 1.5, "transaction_volume": "正常", "liquidity": "中"},
        "宝安": {"avg_price": 60000, "year_change": 3.2, "transaction_volume": "活跃", "liquidity": "中"},
        "龙岗": {"avg_price": 45000, "year_change": 4.0, "transaction_volume": "活跃", "liquidity": "中"},
        "龙华": {"avg_price": 55000, "year_change": 5.2, "transaction_volume": "非常活跃", "liquidity": "高"},
    },
    "北京": {
        "朝阳": {"avg_price": 75000, "year_change": 2.0, "transaction_volume": "活跃", "liquidity": "高"},
        "海淀": {"avg_price": 90000, "year_change": 2.5, "transaction_volume": "活跃", "liquidity": "高"},
        "西城": {"avg_price": 100000, "year_change": 1.0, "transaction_volume": "正常", "liquidity": "低"},
        "东城": {"avg_price": 95000, "year_change": 1.2, "transaction_volume": "正常", "liquidity": "低"},
    },
    "上海": {
        "浦东": {"avg_price": 70000, "year_change": 2.8, "transaction_volume": "活跃", "liquidity": "高"},
        "黄浦": {"avg_price": 100000, "year_change": 1.5, "transaction_volume": "正常", "liquidity": "低"},
        "静安": {"avg_price": 85000, "year_change": 2.0, "transaction_volume": "活跃", "liquidity": "中"},
        "徐汇": {"avg_price": 80000, "year_change": 2.2, "transaction_volume": "活跃", "liquidity": "中"},
    },
    "长沙": {
        "岳麓": {"avg_price": 13000, "year_change": 2.5, "transaction_volume": "活跃", "liquidity": "高"},
        "芙蓉": {"avg_price": 11000, "year_change": 1.8, "transaction_volume": "正常", "liquidity": "中"},
        "天心": {"avg_price": 12000, "year_change": 2.0, "transaction_volume": "活跃", "liquidity": "中"},
        "开福": {"avg_price": 11500, "year_change": 1.5, "transaction_volume": "正常", "liquidity": "中"},
        "雨花": {"avg_price": 10500, "year_change": 2.2, "transaction_volume": "活跃", "liquidity": "高"},
    },
}


def parse_location_from_query(query: str) -> Dict[str, Optional[str]]:
    """从查询中解析位置信息"""
    location = {"city": None, "district": None, "community": None, "intent": None}
    
    for city in CITY_DATA.keys():
        if city in query:
            location["city"] = city
            break
    
    if location["city"]:
        city_districts = CITY_DATA[location["city"]]["districts"]
        for district in city_districts:
            if district in query:
                location["district"] = district
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
    
    intent_keywords = {
        "学区": "学区房",
        "学区房": "学区房",
        "地铁": "地铁房",
        "地铁房": "地铁房",
        "投资": "投资",
        "刚需": "刚需",
        "换房": "换房",
        "小户型": "小户型",
        "大户型": "大户型",
        "新房": "新房",
        "二手房": "二手房",
    }
    for keyword, intent in intent_keywords.items():
        if keyword in query:
            location["intent"] = intent
            break
    
    return location


def generate_price_chart_data(city: str, district: Optional[str]) -> List[Dict[str, Any]]:
    """生成价格走势图数据"""
    import random
    
    base_price = 50000
    if city in CITY_DATA:
        base_price = CITY_DATA[city]["avg_price"]
    if district and city in DISTRICT_DATA and district in DISTRICT_DATA[city]:
        base_price = DISTRICT_DATA[city][district]["avg_price"]
    
    months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
    data = []
    
    for i, month in enumerate(months):
        variation = random.uniform(-0.02, 0.03)
        if i == 0:
            price = base_price * (1 - 0.05)
        else:
            price = data[-1]["price"] * (1 + variation)
        
        data.append({
            "month": month,
            "price": round(price),
            "volume": random.randint(100, 500),
        })
    
    return data


def generate_mascot_message(location: Dict[str, Optional[str]]) -> str:
    """生成吉祥物提示消息"""
    city = location.get("city")
    district = location.get("district")
    intent = location.get("intent")
    
    if district:
        return f"我已经帮你分析了{district}的区域数据，注册即可查看完整报告～"
    elif city:
        return f"我帮你整理了{city}的房价信息，注册查看详细分析报告"
    else:
        return "输入你想分析的区域，我帮你快速了解房价走势～"


@router.get("/landing", response_model=SEOLandingResponse)
async def get_seo_landing(q: str):
    """
    获取SEO着陆页数据
    
    根据搜索词生成动态页面标题、描述、预加载数据
    """
    query = q.strip()
    
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="请输入有效的搜索词")
    
    location = parse_location_from_query(query)
    city = location.get("city")
    district = location.get("district")
    
    if city:
        city_data = CITY_DATA.get(city, {})
        district_data = {}
        if district and city in DISTRICT_DATA and district in DISTRICT_DATA.get(city, {}):
            district_data = DISTRICT_DATA[city][district]
        
        page_title = f"{query}分析报告 | 房都督AI"
        page_description = f"查看{query}的最新房价、成交量和市场分析。房都督AI提供专业的房产估值和市场分析服务。"
        
        avg_price = district_data.get("avg_price", city_data.get("avg_price", 50000))
        year_change = district_data.get("year_change", city_data.get("year_change", 2.5))
        
        market_data = {
            "avg_price": avg_price,
            "price_trend": "稳中有升" if year_change > 0 else "平稳",
            "year_change": year_change,
            "transaction_volume": district_data.get("transaction_volume", "正常"),
            "liquidity": district_data.get("liquidity", "中"),
            "highlights": city_data.get("highlights", []),
        }
        
        price_chart_data = generate_price_chart_data(city or "深圳", district)
        
        key_metrics = {
            "avg_price_per_sqm": round(avg_price / 10000, 1),
            "total_listings": 1250,
            "avg_days_on_market": 45,
            "price_range": {
                "min": round(avg_price * 0.8 / 10000, 1),
                "max": round(avg_price * 1.2 / 10000, 1),
            },
        }
        
        mascot_message = generate_mascot_message(location)
        
        registration_cta = {
            "title": "注册查看完整报告",
            "subtitle": "获取详细分析、投资建议、风险提示",
            "button_text": "免费注册，立即查看",
        }
        
        return SEOLandingResponse(
            query=query,
            location=location,
            page_title=page_title,
            page_description=page_description,
            market_data=market_data,
            price_chart_data=price_chart_data,
            key_metrics=key_metrics,
            mascot_message=mascot_message,
            registration_cta=registration_cta,
        )
