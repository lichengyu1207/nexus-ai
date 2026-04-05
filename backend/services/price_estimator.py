"""
智能估价服务 - 虚实结合的多层级估价算法

估价策略（按优先级）：
1. 真实数据层：数据采集仪采集的真实成交/挂牌数据
2. 相似推断层：基于相似区域/小区的价格推断
3. 城市均价层：城市平均价格估算
4. 默认兜底层：全国均价兜底

算法公式：
最终价格 = 基础单价 × 面积 × 调整系数
调整系数 = 户型系数 × 特殊需求系数 × 市场趋势系数

置信度计算：
- 真实数据：0.85-0.95
- 相似推断：0.65-0.80
- 城市均价：0.50-0.65
- 默认兜底：0.30-0.50
"""
import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from ..database import get_db_connection

logger = logging.getLogger(__name__)


@dataclass
class PriceSource:
    """价格来源"""
    level: int  # 1=真实, 2=推断, 3=城市均价, 4=默认
    name: str
    confidence: float
    is_real: bool  # 是否为真实数据
    description: str


# 默认城市价格数据（兜底数据）
DEFAULT_CITY_PRICES = {
    "深圳": {
        "南山区": {"avg": 95000, "min": 75000, "max": 120000},
        "福田区": {"avg": 85000, "min": 70000, "max": 110000},
        "罗湖区": {"avg": 65000, "min": 50000, "max": 85000},
        "宝安区": {"avg": 60000, "min": 45000, "max": 80000},
        "龙岗区": {"avg": 45000, "min": 35000, "max": 60000},
        "龙华区": {"avg": 55000, "min": 42000, "max": 75000},
        "光明区": {"avg": 40000, "min": 30000, "max": 55000},
        "坪山区": {"avg": 35000, "min": 28000, "max": 48000},
        "南山": {"avg": 95000, "min": 75000, "max": 120000},
        "福田": {"avg": 85000, "min": 70000, "max": 110000},
    },
    "北京": {
        "朝阳区": {"avg": 75000, "min": 60000, "max": 100000},
        "海淀区": {"avg": 90000, "min": 70000, "max": 120000},
        "西城区": {"avg": 110000, "min": 85000, "max": 150000},
        "东城区": {"avg": 100000, "min": 80000, "max": 140000},
        "丰台区": {"avg": 60000, "min": 45000, "max": 80000},
        "通州区": {"avg": 45000, "min": 35000, "max": 60000},
    },
    "上海": {
        "浦东新区": {"avg": 70000, "min": 55000, "max": 95000},
        "黄浦区": {"avg": 100000, "min": 80000, "max": 140000},
        "静安区": {"avg": 85000, "min": 65000, "max": 115000},
        "徐汇区": {"avg": 80000, "min": 60000, "max": 110000},
        "长宁区": {"avg": 75000, "min": 55000, "max": 100000},
        "闵行区": {"avg": 55000, "min": 42000, "max": 75000},
    },
    "广州": {
        "天河区": {"avg": 65000, "min": 50000, "max": 90000},
        "越秀区": {"avg": 55000, "min": 42000, "max": 75000},
        "海珠区": {"avg": 50000, "min": 38000, "max": 70000},
        "番禺区": {"avg": 35000, "min": 28000, "max": 48000},
        "白云区": {"avg": 32000, "min": 25000, "max": 45000},
    },
    "湘潭": {
        "岳塘区": {"avg": 6500, "min": 5000, "max": 8500},
        "雨湖区": {"avg": 5500, "min": 4000, "max": 7500},
        "岳塘": {"avg": 6500, "min": 5000, "max": 8500},
        "雨湖": {"avg": 5500, "min": 4000, "max": 7500},
    },
}

# 户型价格调整系数
HOUSE_TYPE_ADJUSTMENTS = {
    "1室0厅": 1.00, "1室1厅": 1.05,
    "2室0厅": 1.00, "2室1厅": 1.00, "2室2厅": 1.05,
    "3室1厅": 0.98, "3室2厅": 1.00, "3室3厅": 1.08,
    "4室1厅": 0.95, "4室2厅": 0.98, "4室3厅": 1.05,
    "5室2厅": 0.92, "5室3厅": 1.00,
}

# 特殊需求调整系数
SPECIAL_REQUIREMENT_ADJUSTMENTS = {
    "学区房": 1.15, "学区": 1.15,
    "地铁": 1.08, "近地铁": 1.08, "地铁房": 1.10,
    "精装": 1.05, "豪装": 1.12, "毛坯": 0.90,
    "新房": 1.05, "次新房": 1.03, "二手房": 0.98,
    "江景": 1.12, "湖景": 1.10, "海景": 1.15,
    "南北通透": 1.03, "高层": 1.02,
}

# 城市等级（用于推断相似城市价格）
CITY_TIERS = {
    "tier1": ["北京", "上海", "广州", "深圳"],
    "tier1_5": ["杭州", "南京", "苏州", "成都", "武汉", "重庆", "天津"],
    "tier2": ["长沙", "郑州", "西安", "青岛", "大连", "厦门", "宁波", "无锡"],
    "tier3": ["湘潭", "株洲", "岳阳", "常州", "南通"],
}

# 城市等级价格系数（相对于一线城市均价）
TIER_PRICE_MULTIPLIERS = {
    "tier1": 1.0,
    "tier1_5": 0.65,
    "tier2": 0.45,
    "tier3": 0.25,
}


class IntelligentPriceEstimator:
    """智能估价器 - 虚实结合"""
    
    def __init__(self):
        self.default_unit_price = 30000  # 默认单价（元/㎡）
        self.default_confidence = 0.35
    
    async def estimate(
        self,
        city: str,
        district: str = None,
        community: str = None,
        area: float = None,
        area_min: float = None,
        area_max: float = None,
        house_type: str = None,
        room_count: int = None,
        hall_count: int = None,
        special_requirements: List[str] = None,
        lng: float = None,
        lat: float = None,
    ) -> Dict[str, Any]:
        """
        智能估价 - 多层级虚实结合
        
        Args:
            city: 城市
            district: 区域
            community: 小区名
            area: 面积
            area_min: 最小面积
            area_max: 最大面积
            house_type: 户型（如"3室2厅"）
            room_count: 室数
            hall_count: 厅数
            special_requirements: 特殊需求
            lng: 经度（用于查找附近价格）
            lat: 纬度
            
        Returns:
            估价结果，包含价格、置信度、来源等信息
        """
        if house_type is None and room_count:
            hall_count = hall_count or 1
            house_type = f"{room_count}室{hall_count}厅"
        
        if area is None:
            if area_min and area_max:
                area = (area_min + area_max) / 2
            elif area_min:
                area = area_min
            elif area_max:
                area = area_max
            else:
                area = 100
        
        special_requirements = special_requirements or []
        
        price_result = await self._get_price_from_multiple_sources(
            city=city,
            district=district,
            community=community,
            lng=lng,
            lat=lat
        )
        
        base_unit_price = price_result["unit_price"]
        price_source = price_result["source"]
        
        adjustment = self._calculate_adjustment(house_type, special_requirements)
        
        adjusted_unit_price = base_unit_price * adjustment
        
        total_price = adjusted_unit_price * area
        
        confidence = self._calculate_final_confidence(
            base_confidence=price_source.confidence,
            has_area=area is not None,
            has_house_type=house_type is not None,
            data_freshness=price_result.get("data_age_days", 999)
        )
        
        result = {
            "total_price": {
                "estimated": round(total_price, 0),
                "min": round(adjusted_unit_price * 0.85 * area, 0),
                "max": round(adjusted_unit_price * 1.15 * area, 0),
            },
            "unit_price": {
                "base": round(base_unit_price, 0),
                "adjusted": round(adjusted_unit_price, 0),
            },
            "area_used": area,
            "adjustment_factor": round(adjustment, 3),
            "adjustments": {
                "house_type": HOUSE_TYPE_ADJUSTMENTS.get(house_type, 1.0) if house_type else None,
                "special_requirements": self._get_special_req_adjustments(special_requirements),
            },
            "confidence": round(confidence, 2),
            "source": {
                "level": price_source.level,
                "name": price_source.name,
                "is_real": price_source.is_real,
                "description": price_source.description,
            },
            "data_source": price_source.name,
            "is_real_data": price_source.is_real,
            "price_range": {
                "low": round(adjusted_unit_price * 0.85 * area, 0),
                "mid": round(total_price, 0),
                "high": round(adjusted_unit_price * 1.15 * area, 0),
            },
            "market_analysis": self._generate_market_analysis(
                city=city,
                district=district,
                unit_price=adjusted_unit_price,
                confidence=confidence,
                is_real=price_source.is_real
            ),
        }
        
        return result
    
    async def _get_price_from_multiple_sources(
        self,
        city: str,
        district: str = None,
        community: str = None,
        lng: float = None,
        lat: float = None,
    ) -> Dict[str, Any]:
        """
        从多个来源获取价格（按优先级）
        
        优先级：
        1. 真实数据（数据库采集数据）
        2. 相似区域推断
        3. 城市均价
        4. 默认值
        """
        real_data = await self._fetch_real_price_data(city, district, community)
        if real_data:
            return {
                "unit_price": real_data["unit_price"],
                "source": PriceSource(
                    level=1,
                    name="数据采集仪",
                    confidence=0.90,
                    is_real=True,
                    description=f"基于{real_data.get('sample_count', 0)}条真实数据"
                ),
                "data_age_days": real_data.get("age_days", 0),
            }
        
        similar_price = await self._infer_from_similar_areas(city, district, lng, lat)
        if similar_price:
            return {
                "unit_price": similar_price["unit_price"],
                "source": PriceSource(
                    level=2,
                    name="相似推断",
                    confidence=0.70,
                    is_real=False,
                    description=similar_price.get("reason", "基于相似区域推断")
                ),
            }
        
        city_price = await self._get_city_average_price(city, district)
        if city_price:
            return {
                "unit_price": city_price["unit_price"],
                "source": PriceSource(
                    level=3,
                    name="城市均价",
                    confidence=0.55,
                    is_real=False,
                    description=f"{city}{' ' + district if district else ''}均价"
                ),
            }
        
        default_price = self._get_default_price(city, district)
        return {
            "unit_price": default_price["unit_price"],
            "source": PriceSource(
                level=4,
                name="默认估值",
                confidence=0.35,
                is_real=False,
                description="基于城市等级的默认估值"
            ),
        }
    
    async def _fetch_real_price_data(
        self,
        city: str,
        district: str = None,
        community: str = None,
    ) -> Optional[Dict[str, Any]]:
        """从数据库获取真实采集的价格数据"""
        try:
            conn = await get_db_connection()
            try:
                if community:
                    cursor = await conn.execute(
                        """
                        SELECT 
                            cp.avg_price,
                            cp.price_per_sqm,
                            cc.name,
                            cc.district,
                            cc.updated_at
                        FROM collected_communities cc
                        LEFT JOIN collected_prices cp ON cc.id = cp.community_id
                        WHERE cc.city = $1 AND cc.name LIKE $2
                        ORDER BY cp.collected_at DESC
                        LIMIT 1
                        """,
                        [city, f"%{community}%"]
                    )
                    row = await cursor.fetchone()
                    if row and row["price_per_sqm"]:
                        age_days = self._calculate_data_age(row["updated_at"])
                        return {
                            "unit_price": row["price_per_sqm"],
                            "sample_count": 1,
                            "age_days": age_days,
                        }
                
                if district:
                    cursor = await conn.execute(
                        """
                        SELECT 
                            AVG(cp.price_per_sqm) as avg_price,
                            COUNT(*) as sample_count,
                            MAX(cc.updated_at) as latest_update
                        FROM collected_communities cc
                        LEFT JOIN collected_prices cp ON cc.id = cp.community_id
                        WHERE cc.city = $1 AND (cc.district = $2 OR cc.district LIKE $3)
                        """,
                        [city, district, f"%{district}%"]
                    )
                    row = await cursor.fetchone()
                    if row and row["avg_price"]:
                        age_days = self._calculate_data_age(row["latest_update"])
                        return {
                            "unit_price": row["avg_price"],
                            "sample_count": row["sample_count"],
                            "age_days": age_days,
                        }
                
                cursor = await conn.execute(
                    """
                    SELECT 
                        AVG(cp.price_per_sqm) as avg_price,
                        COUNT(*) as sample_count,
                        MAX(cc.updated_at) as latest_update
                    FROM collected_communities cc
                    LEFT JOIN collected_prices cp ON cc.id = cp.community_id
                    WHERE cc.city = $1
                    """,
                    [city]
                )
                row = await cursor.fetchone()
                if row and row["avg_price"]:
                    age_days = self._calculate_data_age(row["latest_update"])
                    return {
                        "unit_price": row["avg_price"],
                        "sample_count": row["sample_count"],
                        "age_days": age_days,
                    }
                
                return None
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Failed to fetch real price data: {e}")
            return None
    
    async def _infer_from_similar_areas(
        self,
        city: str,
        district: str = None,
        lng: float = None,
        lat: float = None,
    ) -> Optional[Dict[str, Any]]:
        """从相似区域推断价格"""
        city_prices = DEFAULT_CITY_PRICES.get(city, {})
        
        if district:
            for dist_name, prices in city_prices.items():
                if district in dist_name or dist_name in district:
                    return {
                        "unit_price": prices["avg"],
                        "reason": f"基于{dist_name}价格推断",
                    }
        
        if city_prices:
            avg_prices = [p["avg"] for p in city_prices.values()]
            return {
                "unit_price": sum(avg_prices) / len(avg_prices),
                "reason": f"基于{city}各区域均价推断",
            }
        
        city_tier = self._get_city_tier(city)
        tier_multiplier = TIER_PRICE_MULTIPLIERS.get(city_tier, 0.5)
        tier1_avg = 80000
        inferred_price = tier1_avg * tier_multiplier
        
        return {
            "unit_price": inferred_price,
            "reason": f"基于{city}城市等级({city_tier})推断",
        }
    
    async def _get_city_average_price(
        self,
        city: str,
        district: str = None,
    ) -> Optional[Dict[str, Any]]:
        """获取城市平均价格"""
        city_prices = DEFAULT_CITY_PRICES.get(city, {})
        
        if district:
            for dist_name, prices in city_prices.items():
                if district in dist_name or dist_name in district:
                    return {"unit_price": prices["avg"]}
        
        if city_prices:
            avg_prices = [p["avg"] for p in city_prices.values()]
            return {"unit_price": sum(avg_prices) / len(avg_prices)}
        
        return None
    
    def _get_default_price(
        self,
        city: str,
        district: str = None,
    ) -> Dict[str, Any]:
        """获取默认价格（兜底）"""
        city_tier = self._get_city_tier(city)
        tier_multiplier = TIER_PRICE_MULTIPLIERS.get(city_tier, 0.5)
        default_price = 80000 * tier_multiplier
        
        return {"unit_price": default_price}
    
    def _calculate_adjustment(
        self,
        house_type: str = None,
        special_requirements: List[str] = None,
    ) -> float:
        """计算总调整系数"""
        adjustment = 1.0
        
        if house_type and house_type in HOUSE_TYPE_ADJUSTMENTS:
            adjustment *= HOUSE_TYPE_ADJUSTMENTS[house_type]
        
        if special_requirements:
            for req in special_requirements:
                for key, adj in SPECIAL_REQUIREMENT_ADJUSTMENTS.items():
                    if key in req:
                        adjustment *= adj
        
        return adjustment
    
    def _get_special_req_adjustments(
        self,
        special_requirements: List[str],
    ) -> Dict[str, float]:
        """获取特殊需求调整系数"""
        result = {}
        if special_requirements:
            for req in special_requirements:
                for key, adj in SPECIAL_REQUIREMENT_ADJUSTMENTS.items():
                    if key in req:
                        result[key] = adj
        return result
    
    def _calculate_final_confidence(
        self,
        base_confidence: float,
        has_area: bool,
        has_house_type: bool,
        data_freshness: int,
    ) -> float:
        """计算最终置信度"""
        confidence = base_confidence
        
        if has_area:
            confidence *= 1.05
        else:
            confidence *= 0.85
        
        if has_house_type:
            confidence *= 1.03
        
        if data_freshness < 7:
            confidence *= 1.05
        elif data_freshness < 30:
            confidence *= 1.0
        elif data_freshness < 90:
            confidence *= 0.95
        else:
            confidence *= 0.85
        
        return min(confidence, 0.98)
    
    def _calculate_data_age(self, date_str: str) -> int:
        """计算数据年龄（天）"""
        if not date_str:
            return 999
        try:
            if isinstance(date_str, str):
                data_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                data_date = date_str
            age = (datetime.now() - data_date.replace(tzinfo=None)).days
            return max(0, age)
        except:
            return 999
    
    def _get_city_tier(self, city: str) -> str:
        """获取城市等级"""
        for tier, cities in CITY_TIERS.items():
            if city in cities:
                return tier
        return "tier3"
    
    def _generate_market_analysis(
        self,
        city: str,
        district: str,
        unit_price: float,
        confidence: float,
        is_real: bool,
    ) -> Dict[str, Any]:
        """生成市场分析"""
        analysis = {
            "price_level": self._get_price_level(unit_price),
            "market_trend": "stable",
            "recommendation": "",
        }
        
        if confidence >= 0.8:
            analysis["recommendation"] = "估价结果可信度高，可作为参考依据"
        elif confidence >= 0.6:
            analysis["recommendation"] = "估价结果可信度中等，建议结合实地考察"
        else:
            analysis["recommendation"] = "估价结果仅供参考，建议咨询专业评估机构"
        
        if not is_real:
            analysis["recommendation"] += "（基于推断数据）"
        
        return analysis
    
    def _get_price_level(self, unit_price: float) -> str:
        """获取价格等级"""
        if unit_price >= 80000:
            return "高端"
        elif unit_price >= 50000:
            return "中高端"
        elif unit_price >= 30000:
            return "中端"
        elif unit_price >= 15000:
            return "中低端"
        else:
            return "低端"


estimator = IntelligentPriceEstimator()


async def estimate_price(
    city: str,
    district: str = None,
    area_min: float = None,
    area_max: float = None,
    house_type: str = None,
    special_requirements: List[str] = None
) -> Dict[str, Any]:
    """
    估算房价（便捷函数）
    
    Args:
        city: 城市
        district: 区域
        area_min: 最小面积
        area_max: 最大面积
        house_type: 户型
        special_requirements: 特殊需求
        
    Returns:
        估价结果
    """
    return await estimator.estimate(
        city=city,
        district=district,
        area_min=area_min,
        area_max=area_max,
        house_type=house_type,
        special_requirements=special_requirements,
    )


async def get_district_price(city: str, district: str) -> Optional[Dict[str, Any]]:
    """获取区域价格"""
    return await estimator._get_city_average_price(city, district)


async def init_district_price_data():
    """初始化区域房价数据"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM district_price_stats"
        )
        result = await cursor.fetchone()
        
        if result["count"] > 0:
            logger.info("区域房价数据已存在，跳过初始化")
            return
        
        import uuid
        today = date.today().isoformat()
        
        for city, districts in DEFAULT_CITY_PRICES.items():
            for district, prices in districts.items():
                await conn.execute(
                    """
                    INSERT INTO district_price_stats (
                        id, city, district, avg_price_per_sqm, 
                        min_price_per_sqm, max_price_per_sqm, date, source
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    (
                        str(uuid.uuid4()),
                        city,
                        district,
                        prices["avg"],
                        prices["min"],
                        prices["max"],
                        today,
                        "默认统计"
                    )
                )
        
        await conn.commit()
        total = sum(len(d) for d in DEFAULT_CITY_PRICES.values())
        logger.info(f"初始化区域房价数据完成，共 {total} 条")
    finally:
        await conn.close()


def get_city_average_price(city: str) -> Optional[float]:
    """获取城市平均房价"""
    city_prices = DEFAULT_CITY_PRICES.get(city, {})
    if city_prices:
        return sum(d["avg"] for d in city_prices.values()) / len(city_prices)
    return None


async def get_all_district_prices(city: str = None) -> List[Dict[str, Any]]:
    """
    获取所有区域价格数据
    
    Args:
        city: 可选的城市筛选
        
    Returns:
        区域价格列表
    """
    results = []
    
    for city_name, districts in DEFAULT_CITY_PRICES.items():
        if city and city != city_name:
            continue
        for district_name, prices in districts.items():
            results.append({
                "city": city_name,
                "district": district_name,
                "avg_price_per_sqm": prices["avg"],
                "min_price_per_sqm": prices["min"],
                "max_price_per_sqm": prices["max"],
                "source": "默认数据"
            })
    
    return results


async def add_district_price(
    city: str,
    district: str,
    avg_price: float,
    min_price: float = None,
    max_price: float = None,
    source: str = "用户录入"
) -> bool:
    """
    添加区域价格数据
    
    Args:
        city: 城市
        district: 区域
        avg_price: 平均价格
        min_price: 最低价格
        max_price: 最高价格
        source: 数据来源
        
    Returns:
        是否添加成功
    """
    try:
        conn = await get_db_connection()
        try:
            import uuid
            today = date.today().isoformat()
            
            await conn.execute(
                """
                INSERT INTO district_price_stats (
                    id, city, district, avg_price_per_sqm, 
                    min_price_per_sqm, max_price_per_sqm, date, source
                ) VALUES (
                    COALESCE(
                        (SELECT id FROM district_price_stats WHERE city = $1 AND district = $2),
                        $3
                    ),
                    $4, $5, $6, $7, $8, $9, $10
                )
                ON CONFLICT (id) DO UPDATE SET
                    city = EXCLUDED.city,
                    district = EXCLUDED.district,
                    avg_price_per_sqm = EXCLUDED.avg_price_per_sqm,
                    min_price_per_sqm = EXCLUDED.min_price_per_sqm,
                    max_price_per_sqm = EXCLUDED.max_price_per_sqm,
                    date = EXCLUDED.date,
                    source = EXCLUDED.source
                """,
                (
                    city, district,
                    str(uuid.uuid4()),
                    city, district, avg_price,
                    min_price or avg_price * 0.8,
                    max_price or avg_price * 1.2,
                    today, source
                )
            )
            await conn.commit()
            return True
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Failed to add district price: {e}")
        return False


HOUSE_TYPE_PRICE_ADJUSTMENTS = HOUSE_TYPE_ADJUSTMENTS
SPECIAL_REQUIREMENT_ADJUSTMENTS = SPECIAL_REQUIREMENT_ADJUSTMENTS
DEFAULT_CITY_PRICES_EXPORT = DEFAULT_CITY_PRICES
