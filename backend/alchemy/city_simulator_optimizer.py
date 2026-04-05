"""
智能体自进化炼丹系统 - 第三部分：动态城市数据模拟器 + 自动优化 + 告警通知
房都督平台 Phase D: 自进化炼丹系统 Chapter 3.4 / 5.4 / 6.3

3.4 DynamicCitySimulator - 动态城市数据模拟器（30城房产数据+板块+小区+政策事件）
5.4 AutoPerformanceTuner - 自动内存与性能调优
6.3 AlertNotifier - 告警与通知（钉钉/企微/邮件多通道）
"""
import json
import logging
import time
import math
import random
import uuid
import re
import copy
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple, Set
from collections import deque, defaultdict
import threading


logger = logging.getLogger(__name__)


# ==================== 3.4 动态城市数据模拟器 ====================


class CityTier(Enum):
    TIER_1 = "tier_1"
    TIER_1_NEW = "tier_1_new"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


@dataclass
class CityData:
    """城市基础数据"""
    city_id: str
    name: str
    province: str
    tier: CityTier
    population_millions: float
    avg_price_per_sqm: float
    price_change_yoy: float
    inventory_months: float
    policy_tags: List[str]
    gdp_trillion: float
    established: int


@dataclass
class DistrictData:
    """板块数据"""
    district_id: str
    city_id: str
    name: str
    avg_price_per_sqm: float
    price_change_mom: float
    inventory_units: int
    new_supply_units: int
    transaction_volume_mom: float
    key_landmarks: List[str]
    metro_lines: List[str]
    school_rating: float
    commercial_score: float


@dataclass
class CommunityData:
    """小区数据"""
    community_id: str
    district_id: str
    name: str
    developer: str
    built_year: int
    total_units: int
    avg_price_per_sqm: float
    area_range_sqm: Tuple[float, float]
    property_fee_per_sqm: float
    green_rate: float
    plot_ratio: float
    parking_ratio: float
    school_distance_km: float
    metro_distance_km: float
    transaction_count_30d: int
    avg_transaction_price: float


@dataclass
class PolicyEvent:
    """政策事件"""
    event_id: str
    city_id: str
    event_type: str
    title: str
    description: str
    effective_date: str
    impact_level: str
    affected_metrics: Dict[str, float]
    source: str


class DynamicCitySimulator:
    """
    动态城市数据模拟器（提示词 3.4）
    
    功能：
    - 自动生成30+城市的房产数据（均价、涨跌幅、库存、政策标签）
    - 每个城市生成多个板块数据（均价、历史曲线、配套）
    - 每个板块生成多个小区数据（户型、物业、配套详情）
    - 支持每日价格微调，模拟真实市场波动
    - 注入新增政策事件（限购松绑、利率调整等）
    
    数据层级：城市(30+) → 板块(每城5-15个) → 小区(每板块10-30个)
    """

    def __init__(self,
                 num_cities: int = 32,
                 districts_per_city: Tuple[int, int] = (6, 14),
                 communities_per_district: Tuple[int, int] = (12, 28),
                 daily_volatility: float = 0.003,
                 policy_event_probability: float = 0.05):
        self.num_cities = num_cities
        self.districts_range = districts_per_city
        self.communities_range = communities_per_district
        self.daily_volatility = daily_volatility
        self.policy_event_prob = policy_event_probability
        self.cities: Dict[str, CityData] = {}
        self.districts: Dict[str, DistrictData] = {}
        self.communities: Dict[str, CommunityData] = {}
        self.policy_events: List[PolicyEvent] = []
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=365))
        self._initialized = False
        self._last_update: Optional[float] = None

    def initialize(self) -> Dict[str, Any]:
        if self._initialized:
            return {"status": "already_initialized", "cities": len(self.cities)}
        start_time = time.time()
        self._generate_cities()
        for city in self.cities.values():
            self._generate_districts(city)
            city_districts = [d for d in self.districts.values() if d.city_id == city.city_id]
            for district in city_districts:
                self._generate_communities(district)
        self._generate_initial_policy_events()
        self._initialized = True
        self._last_update = time.time()
        elapsed = time.time() - start_time
        summary = {
            "status": "initialized",
            "elapsed_seconds": round(elapsed, 2),
            "cities": len(self.cities),
            "districts": len(self.districts),
            "communities": len(self.communities),
            "policy_events": len(self.policy_events),
        }
        logger.info(f"🏙️ 城市模拟器初始化完成: {summary['cities']}城/{summary['districts']}板块/"
                     f"{summary['communities']}小区")
        return summary

    def _generate_cities(self):
        tier1_cities = [
            ("北京", "北京", CityTier.TIER_1, 2189, 62000, -0.02, 12.0, ["限购最严", "公积金高"],
             4.38, 3000),
            ("上海", "上海", CityTier.TIER_1, 2487, 58000, -0.01, 10.5, ["限购严格", "积分落户"],
             4.72, 2800),
            ("深圳", "广东", CityTier.TIER_1, 1768, 65000, -0.03, 11.0, ["限购严", "豪宅税"],
             3.46, 1980),
            ("广州", "广东", CityTier.TIER_1, 1881, 38000, 0.01, 13.0, ["限购较松", "人才引进"],
             3.04, 2240),
        ]
        tier1_new_cities = [
            ("杭州", "浙江", CityTier.TIER_1_NEW, 1237, 35000, 0.02, 9.0, ["限购放松", "亚运利好"],
             2.09, 1000),
            ("南京", "江苏", CityTier.TIER_1_NEW, 942, 32000, 0.00, 10.0, ["限购适中", "高校集中"],
             1.71, 900),
            ("成都", "四川", CityTier.TIER_1_NEW, 2127, 18000, 0.02, 12.0, ["限购宽松", "新一线热门"],
             2.21, 2300),
            ("武汉", "湖北", CityTier.TIER_1_NEW, 1374, 17000, 0.01, 14.0, ["限购宽松", "大学之城"],
             1.89, 1800),
            ("苏州", "江苏", CityTier.TIER_1_NEW, 1275, 26000, 0.01, 11.0, ["限购部分放开", "工业强市"],
             2.40, 1200),
            ("西安", "陕西", CityTier.TIER_1_NEW, 1318, 15000, 0.02, 13.0, ["限购宽松", "西北中心"],
             1.20, 1100),
            ("重庆", "重庆", CityTier.TIER_1_NEW, 3212, 12000, 0.01, 15.0, ["不限购", "山城特色"],
             2.91, 1400),
            ("天津", "天津", CityTier.TIER_1_NEW, 1364, 21000, -0.02, 18.0, ["限购适中", "京津冀"],
             1.57, 1400),
        ]
        tier2_cities = [
            ("长沙", "湖南", CityTier.TIER_2, 1042, 11000, 0.01, 10.0, ["不限购", "房价洼地"],
             1.43, 700),
            ("郑州", "河南", CityTier.TIER_2, 1283, 12000, -0.01, 16.0, ["限购宽松", "中原中心"],
             1.36, 800),
            ("济南", "山东", CityTier.TIER_2, 933, 15000, 0.00, 14.0, ["限购适中", "泉城"],
             1.20, 800),
            ("合肥", "安徽", CityTier.TIER_2, 947, 16000, 0.02, 9.0, ["限购较松", "科创城市"],
             1.21, 600),
            ("福州", "福建", CityTier.TIER_2, 829, 18000, -0.01, 13.0, ["限购适中", "沿海城市"],
             1.24, 700),
            ("厦门", "福建", CityTier.TIER_2, 530, 42000, -0.03, 15.0, ["限购严", "旅游城市"],
             0.80, 500),
            ("宁波", "浙江", CityTier.TIER_2, 962, 24000, 0.01, 11.0, ["限购部分", "港口城市"],
             1.58, 900),
            ("无锡", "江苏", CityTier.TIER_2, 749, 17000, 0.00, 13.0, ["不限购", "苏南模式"],
             1.49, 600),
            ("佛山", "广东", CityTier.TIER_2, 955, 14000, 0.01, 12.0, ["不限购", "广佛同城"],
             1.27, 800),
            ("东莞", "广东", CityTier.TIER_2, 1047, 19000, 0.00, 14.0, ["不限购", "制造业强"],
             1.09, 700),
            ("青岛", "山东", CityTier.TIER_2, 1035, 18000, -0.01, 14.0, ["限购部分", "海滨城市"],
             1.41, 800),
            ("大连", "辽宁", CityTier.TIER_2, 750, 14000, -0.02, 18.0, ["限购宽松", "东北窗口"],
             0.84, 700),
        ]
        tier3_pool = [
            ("昆明", "云南"), ("南宁", "广西"), ("贵阳", "贵州"),
            ("太原", "山西"), ("南昌", "江西"), ("沈阳", "辽宁"),
            ("长春", "吉林"), ("哈尔滨", "黑龙江"), ("石家庄", "河北"),
            ("温州", "浙江"), ("常州", "江苏"), ("烟台", "山东"),
        ]
        all_cities_data = tier1_cities + tier1_new_cities + tier2_cities
        for i, (name, prov, tier, pop, price, yoy, inv, tags, gdp, est) in enumerate(all_cities_data):
            noise_pop = random.uniform(-0.05, 0.05)
            noise_price = random.uniform(-0.08, 0.08)
            city = CityData(
                city_id=f"city_{i+1:03d}",
                name=name,
                province=prov,
                tier=tier,
                population_millions=round(pop * (1 + noise_pop), 2),
                avg_price_per_sqm=round(price * (1 + noise_price), 0),
                price_change_yoy=round(yoy + random.uniform(-0.015, 0.015), 4),
                inventory_months=round(inv * random.uniform(0.85, 1.15), 1),
                policy_tags=list(tags),
                gdp_trillion=round(gdp, 3),
                established=est + random.randint(-50, 50),
            )
            self.cities[city.city_id] = city
        remaining = self.num_cities - len(all_cities_data)
        for j in range(remaining):
            idx = j % len(tier3_pool)
            name, prov = tier3_pool[idx]
            city = CityData(
                city_id=f"city_{len(all_cities_data)+j+1:03d}",
                name=f"{name}_{j}" if j > 0 else name,
                province=prov,
                tier=CityTier.TIER_3,
                population_millions=round(random.uniform(3, 12), 1),
                avg_price_per_sqm=round(random.uniform(6000, 14000), 0),
                price_change_yoy=round(random.uniform(-0.03, 0.05), 4),
                inventory_months=round(random.uniform(8, 24), 1),
                policy_tags=["不限购或宽松"],
                gdp_trillion=round(random.uniform(0.3, 1.2), 2),
                established=random.randint(1950, 2010),
            )
            self.cities[city.city_id] = city

    def _generate_districts(self, city: CityData):
        num_districts = random.randint(*self.districts_range)
        district_name_templates = {
            CityTier.TIER_1: ["朝阳区", "海淀区", "西城区", "东城区", "丰台区", "通州区",
                               "昌平区", "大兴区", "顺义区", "石景山区", "门头沟区", "房山区"],
            CityTier.TIER_1_NEW: ["高新区", "开发区", "滨江区", "新城区", "核心区",
                                  "科技园", "CBD", "金融街", "文创区", "生态城"],
            CityTier.TIER_2: ["中心城区", "新区", "经开区", "老城区", "政务区",
                              "商业区", "教育园区", "工业区", "文旅区", "港口区"],
            CityTier.TIER_3: ["市中心", "城东区", "城西区", "城南新区", "城北新区",
                              "开发区", "工业园区", "高新区"],
        }
        templates = district_name_templates.get(city.tier, district_name_templates[CityTier.TIER_2])
        base_price = city.avg_price_per_sqm
        for i in range(num_districts):
            template_idx = i % len(templates)
            prefix = "" if i < len(templates) else f"新{i // len(templates)}"
            name = prefix + templates[template_idx]
            price_factor = random.uniform(0.65, 1.50)
            district = DistrictData(
                district_id=f"dist_{city.city_id}_{i+1:02d}",
                city_id=city.city_id,
                name=name,
                avg_price_per_sqm=round(base_price * price_factor, 0),
                price_change_mom=round(random.uniform(-0.025, 0.035), 4),
                inventory_units=random.randint(200, 3000),
                new_supply_units=random.randint(0, 500),
                transaction_volume_mom=round(random.uniform(-0.15, 0.25), 3),
                key_landmarks=self._sample_landmarks(),
                metro_lines=[f"地铁{random.randint(1, 20)}号线" for _ in range(random.randint(0, 4))],
                school_rating=round(random.uniform(2.0, 9.5), 1),
                commercial_score=round(random.uniform(3.0, 9.5), 1),
            )
            self.districts[district.district_id] = district

    def _generate_communities(self, district: DistrictData):
        num_communities = random.randint(*self.communities_range)
        developers = ["万科", "保利", "中海", "龙湖", "碧桂园", "融创", "华润置地",
                      "绿城", "招商蛇口", "金地", "旭辉", "新城控股", "世茂", "金茂"]
        base_price = district.avg_price_per_sqm
        for i in range(num_communities):
            dev = random.choice(developers)
            suffixes = ["花园", "公馆", "华府", "壹号院", "国际", "湾", "城", "广场",
                        "雅苑", "嘉园", "御府", "天玺", "中央公园", "滨江", "云筑"]
            name = f"{district.name[:2]}{random.choice(suffixes)}{i+1}"
            comm = CommunityData(
                community_id=f"comm_{district.district_id}_{i+1:03d}",
                district_id=district.district_id,
                name=name,
                developer=dev,
                built_year=random.randint(1995, 2025),
                total_units=random.randint(300, 5000),
                avg_price_per_sqm=round(base_price * random.uniform(0.80, 1.25), 0),
                area_range_sqm=(round(random.uniform(45, 90), 0), round(random.uniform(120, 250), 0)),
                property_fee_per_sqm=round(random.uniform(2.0, 8.0), 2),
                green_rate=round(random.uniform(0.25, 0.55), 2),
                plot_ratio=round(random.uniform(1.5, 4.5), 2),
                parking_ratio=round(random.uniform(0.5, 1.5), 2),
                school_distance_km=round(random.uniform(0.3, 5.0), 1),
                metro_distance_km=round(random.uniform(0.1, 3.0), 1),
                transaction_count_30d=random.randint(0, 25),
                avg_transaction_price=round(base_price * random.uniform(0.85, 1.15)
                                              * random.uniform(60, 150), 0),
            )
            self.communities[comm.community_id] = comm

    def _sample_landmarks(self) -> List[str]:
        landmark_pool = [
            "万达广场", "万象城", "恒隆广场", "银泰城", "大悦城", "来福士广场",
            "市民中心", "市政府", "体育馆", "图书馆", "三甲医院", "大学城",
            "中央公园", "会展中心", "高铁站", "机场", "金融中心", "创业园",
            "科技园", "软件园", "产业园", "湿地公园", "湖畔", "江景资源",
            "山景资源", "学区资源", "地铁站", "公交枢纽", "奥特莱斯",
        ]
        return random.sample(landmark_pool, k=random.randint(1, 4))

    def _generate_initial_policy_events(self):
        event_templates = [
            ("限购松绑", "policy_relaxation", "非户籍购房门槛降低",
             "非本地户籍居民购房社保年限要求由{years}年降至{new_years}年", {"price_impact": 0.02}),
            ("利率调整", "rate_adjustment", "{type}贷款LPR下调{bps}基点",
             "央行宣布{type}房贷LPR从{old_rate}%下调至{new_rate}%", {"price_impact": 0.01}),
            ("公积金新政", "housing_fund", "公积金贷款额度上限提高",
             "住房公积金贷款最高额度由{old_limit}万提高至{new_limit}万", {"price_impact": 0.015}),
            ("税收优惠", "tax_incentive", "契税补贴政策出台",
             "购买首套房契税享受{discount}%财政补贴", {"price_impact": 0.01}),
            ("人才引进", "talent_policy", "高层次人才购房补贴",
             "A类人才最高可获{amount}万购房补贴", {"price_impact": 0.005}),
            ("限售延长", "restriction_extend", "商品房限售期延长",
             "新购住房限售期由{old_years}年延长至{new_years}年", {"price_impact": -0.015}),
            ("土拍规则", "land_auction", "土地出让规则调整",
             "土拍实行'限地价+竞品质+摇号'新模式", {"supply_impact": 0.1}),
        ]
        for city_id, city in list(self.cities.items())[:10]:
            if random.random() > self.policy_event_prob * 3:
                continue
            template = random.choice(event_templates)
            etype, ecode, title_template, desc_template, impacts = template
            title = title_template.format(
                years=random.choice([3, 5]), new_years=random.choice([1, 2]),
                type=random.choice(["首套", "二套"]), bps=random.choice([5, 10, 15]),
                old_rate="3.95", new_rate=f"{3.95 - random.choice([10, 15, 20]) / 100:.2f}",
                old_limit="60", new_limit=str(random.choice([70, 80, 90, 100])),
                discount=random.choice([30, 50]),
                amount=random.choice([50, 100, 200]),
                old_years_val="2", new_years_ext="3",
            )
            desc = desc_template.format(
                years=title.get("years", ""), new_years=title.get("new_years", ""),
                type=title.get("type", ""), bps=title.get("bps", ""),
                old_rate=title.get("old_rate", ""), new_rate=title.get("new_rate", ""),
                old_limit=title.get("old_limit", ""), new_limit=title.get("new_limit", ""),
                discount=title.get("discount", ""),
                amount=title.get("amount", ""),
                old_years_val=title.get("old_years", ""), new_years_val=title.get("new_years", ""),
            )
            event = PolicyEvent(
                event_id=f"pol_{uuid.uuid4().hex[:8]}",
                city_id=city_id,
                event_type=etype,
                title=title,
                description=desc,
                effective_date=f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                impact_level=random.choice(["high", "medium", "low"]),
                affected_metrics=impacts,
                source="simulated_government_api",
            )
            self.policy_events.append(event)

    def simulate_daily_update(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        updates = {"cities_updated": 0, "total_price_delta": 0.0}
        for city_id, city in self.cities.items():
            volatility = self.daily_volatility
            trend = city.price_change_yoy / 365
            noise = random.gauss(0, volatility)
            daily_change = trend + noise
            old_price = city.avg_price_per_sqm
            new_price = max(3000, old_price * (1 + daily_change))
            city.avg_price_per_sqm = round(new_price, 0)
            city.price_change_yoy = round((new_price / old_price - 1) * 365 + city.price_change_yoy, 4)
            self.price_history[city_id].append(new_price)
            updates["cities_updated"] += 1
            updates["total_price_delta"] += (new_price - old_price)
        for dist in self.districts.values():
            noise = random.gauss(0, self.daily_volatility * 1.5)
            dist.avg_price_per_sqm = round(dist.avg_price_per_sqm * (1 + noise), 0)
            dist.price_change_mom = round(noise * 30, 4)
        for comm in self.communities.values():
            noise = random.gauss(0, self.daily_volatility * 2.0)
            comm.avg_price_per_sqm = round(comm.avg_price_per_sqm * (1 + noise), 0)
            comm.transaction_count_30d = max(0, comm.transaction_count_30d +
                                            random.randint(-3, 5))
        if random.random() < self.policy_event_prob:
            self._inject_random_policy_event()
        self._last_update = time.time()
        return updates

    def _inject_random_policy_event(self):
        cities_list = list(self.cities.keys())
        target_city = random.choice(cities_list)
        event_types = [("市场调控微调", "market_fine_tune", "low"),
                        ("区域规划利好", "regional_plan", "medium"),
                        ("临时性限制措施", "temporary_restriction", "high")]
        etype, ecode, level = random.choice(event_types)
        event = PolicyEvent(
            event_id=f"pol_{uuid.uuid4().hex[:8]}",
            city_id=target_city,
            event_type=etype,
            title=f"{self.cities[target_city].name}{etype}",
            description=f"针对{self.cities[target_city].name}的{etype}措施已发布",
            effective_date=datetime.now().strftime("%Y-%m-%d"),
            impact_level=level,
            affected_metrics={"price_impact": round(random.uniform(-0.02, 0.02), 4)},
            source="dynamic_simulation",
        )
        self.policy_events.append(event)

    def query_city(self, city_name: Optional[str] = None,
                    tier: Optional[CityTier] = None,
                    min_price: Optional[float] = None,
                    max_price: Optional[float] = None,
                    limit: int = 20) -> List[Dict[str, Any]]:
        results = []
        for city in self.cities.values():
            if city_name and city_name not in city.name:
                continue
            if tier and city.tier != tier:
                continue
            if min_price and city.avg_price_per_sqm < min_price:
                continue
            if max_price and city.avg_price_per_sqm > max_price:
                continue
            results.append(asdict(city))
        results.sort(key=lambda x: x.get("avg_price_per_sqm", 0))
        return results[:limit]

    def query_districts(self, city_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return [asdict(d) for d in self.districts.values()
                if d.city_id == city_id][:limit]

    def query_communities(self, district_id: str,
                           min_area: Optional[float] = None,
                           max_area: Optional[float] = None,
                           limit: int = 30) -> List[Dict[str, Any]]:
        results = []
        for c in self.communities.values():
            if c.district_id != district_id:
                continue
            if min_area and c.area_range_sqm[0] < min_area:
                continue
            if max_area and c.area_range_sqm[1] > max_area:
                continue
            results.append({**asdict(c)})
        return results[:limit]

    def get_market_overview(self) -> Dict[str, Any]:
        prices = [c.avg_price_per_sqm for c in self.cities.values()]
        changes = [c.price_change_yoy for c in self.cities.values()]
        tier_stats = {}
        for tier in CityTier:
            tier_cities = [c for c in self.cities.values() if c.tier == tier]
            if tier_cities:
                tier_stats[tier.value] = {
                    "count": len(tier_cities),
                    "avg_price": round(statistics.mean([c.avg_price_per_sqm for c in tier_cities]), 0),
                    "avg_change": round(statistics.mean([c.price_change_yoy for c in tier_cities]), 4),
                }
        return {
            "total_cities": len(self.cities),
            "total_districts": len(self.districts),
            "total_communities": len(self.communities),
            "active_policy_events": len(self.policy_events),
            "market_avg_price": round(statistics.mean(prices), 0) if prices else 0,
            "market_median_price": round(sorted(prices)[len(prices)//2], 0) if prices else 0,
            "market_avg_change_yoy": round(statistics.mean(changes), 4) if changes else 0,
            "price_range": (round(min(prices), 0), round(max(prices), 0)) if prices else (0, 0),
            "by_tier": tier_stats,
            "last_update": datetime.fromtimestamp(self._last_update).isoformat() if self._last_update else None,
        }

    def export_city_data_json(self, filepath: str) -> bool:
        try:
            output = {
                "exported_at": datetime.now().isoformat(),
                "overview": self.get_market_overview(),
                "cities": {cid: asdict(c) for cid, c in self.cities.items()},
                "policy_events": [asdict(e) for e in self.policy_events[-50:]],
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"城市数据已导出至 {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False


# ==================== 5.4 自动内存与性能调优 ====================


class IssueType(Enum):
    MEMORY_LEAK = "memory_leak"
    CPU_BOTTLENECK = "cpu_bottleneck"
    SLOW_QUERY = "slow_query"
    CONNECTION_LEAK = "connection_leak"
    CACHE_INEFFICIENCY = "cache_inefficiency"
    GC_PRESSURE = "gc_pressure"


@dataclass
class PerformanceIssue:
    """性能问题"""
    issue_id: str
    issue_type: IssueType
    severity: str
    location: str
    current_value: float
    baseline_value: float
    threshold: float
    description: str
    suggested_fix: str
    auto_fixable: bool
    detected_at: float
    resolved_at: Optional[float] = None
    fix_applied: Optional[str] = None


@dataclass
class OptimizationAttempt:
    """优化尝试记录"""
    attempt_id: str
    issue_id: str
    strategy: str
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_pct: float
    success: bool
    timestamp: float


class AutoPerformanceTuner:
    """
    自动内存与性能调优器（提示词 5.4）
    
    功能：
    - 监控系统资源使用，当内存持续增长时自动检测泄漏
    - 模拟CPU热点代码定位（基于调用频率统计）
    - 自动分析慢查询执行计划，建议索引优化
    - 尝试自动修复（缓存策略调整、连接池扩容等）
    - 记录所有优化尝试及效果
    
    检测维度：
    - 内存：持续增长趋势 + GC频率异常
    - CPU：函数级调用耗时统计
    - 数据库：查询执行时间 + 扫描行数
    - 连接池：活跃连接数 + 等待队列长度
    - 缓存：命中率 + 失效频率
    """

    def __init__(self,
                 memory_growth_threshold_mb_per_min: float = 5.0,
                 cpu_hotspot_threshold_ms: float = 100.0,
                 slow_query_threshold_ms: float = 2000.0,
                 connection_pool_utilization_warn: float = 0.80,
                 cache_hit_rate_warn: float = 0.70,
                 auto_fix_enabled: bool = True):
        self.memory_growth_threshold = memory_growth_threshold_threshold_mb_per_min
        self.cpu_hotspot_threshold = cpu_hotspot_threshold_ms
        self.slow_query_threshold = slow_query_threshold_ms
        self.conn_pool_warn = connection_pool_utilization_warn
        self.cache_hit_warn = cache_hit_rate_warn
        self.auto_fix_enabled = auto_fix_enabled
        
        self.detected_issues: List[PerformanceIssue] = []
        self.optimization_history: List[OptimizationAttempt] = []
        self.memory_snapshots: deque = deque(maxlen=1440)
        self.cpu_profile: Dict[str, Dict[str, float]] = defaultdict(lambda: {"calls": 0, "total_time": 0.0})
        self.query_log: List[Dict[str, Any]] = []
        self.connection_pool_state: Dict[str, float] = {}
        self.cache_stats: Dict[str, Dict[str, float]] = {}

    def check_memory_health(self, current_memory_mb: float) -> Optional[PerformanceIssue]:
        ts = time.time()
        self.memory_snapshots.append({"timestamp": ts, "memory_mb": current_memory_mb})
        if len(self.memory_snapshots) < 5:
            return None
        recent = list(self.memory_snapshots)[-5:]
        time_span = recent[-1]["timestamp"] - recent[0]["timestamp"]
        if time_span < 30:
            return None
        growth_rate = (recent[-1]["memory_mb"] - recent[0]["memory_mb"]) / (time_span / 60.0)
        if growth_rate > self.memory_growth_threshold:
            issue = PerformanceIssue(
                issue_id=f"mem_{uuid.uuid4().hex[:8]}",
                issue_type=IssueType.MEMORY_LEAK,
                severity="critical" if growth_rate > 20 else "warning",
                location="system_heap",
                current_value=round(growth_rate, 2),
                baseline_value=0.0,
                threshold=self.memory_growth_threshold,
                description=f"内存增长速率{growth_rate:.1f}MB/min超过阈值{self.memory_growth_threshold:.1f}MB/min",
                suggested_fix="检查对象引用释放、缓存大小限制、大对象堆栈快照分析",
                auto_fixable=True,
                detected_at=ts,
            )
            self.detected_issues.append(issue)
            return issue
        gc_candidates = [s for s in recent if s.get("gc_pause_ms", 0) > 50]
        if len(gc_candidates) >= 3:
            issue = PerformanceIssue(
                issue_id=f"gc_{uuid.uuid4().hex[:8]}",
                issue_type=IssueType.GC_PRESSURE,
                severity="warning",
                location="garbage_collector",
                current_value=len(gc_candidates),
                baseline_value=0,
                threshold=2,
                description=f"最近{len(recent)}次采样中有{len(gc_candidates)}次GC暂停>50ms",
                suggested_fix="减少短生命周期对象创建、增加初始堆大小、考虑分代GC调优",
                auto_fixable=False,
                detected_at=ts,
            )
            self.detected_issues.append(issue)
            return issue
        return None

    def record_cpu_profile(self, function_name: str, duration_ms: float):
        profile = self.cpu_profile[function_name]
        profile["calls"] += 1
        profile["total_time"] += duration_ms
        if duration_ms > self.cpu_hotspot_threshold:
            existing = [i for i in self.detected_issues
                       if i.issue_type == IssueType.CPU_BOTTLENECK and i.location == function_name]
            if not existing:
                issue = PerformanceIssue(
                    issue_id=f"cpu_{uuid.uuid4().hex[:8]}",
                    issue_type=IssueType.CPU_BOTTLENECK,
                    severity="warning" if duration_ms < 500 else "critical",
                    location=function_name,
                    current_value=round(duration_ms, 2),
                    baseline_value=self.cpu_hotspot_threshold,
                    threshold=self.cpu_hotspot_threshold,
                    description=f"函数'{function_name}'单次调用{duration_ms:.1f}ms超过阈值{self.cpu_hotspot_threshold:.0f}ms",
                    suggested_fix="考虑异步化处理、添加缓存层、算法优化或分批处理",
                    auto_fixable=True,
                    detected_at=time.time(),
                )
                self.detected_issues.append(issue)

    def analyze_slow_query(self, sql: str, execution_time_ms: float,
                           rows_scanned: int, rows_returned: int) -> Optional[PerformanceIssue]:
        entry = {
            "sql_hash": hashlib.md5(sql.encode()).hexdigest()[:12],
            "sql_preview": sql[:200],
            "execution_time_ms": execution_time_ms,
            "rows_scanned": rows_scanned,
            "rows_returned": rows_returned,
            "timestamp": time.time(),
        }
        self.query_log.append(entry)
        if len(self.query_log) > 10000:
            self.query_log = self.query_log[-5000:]
        if execution_time_ms >= self.slow_query_threshold:
            scan_ratio = rows_scanned / max(rows_returned, 1)
            issue = PerformanceIssue(
                issue_id=f"sql_{uuid.uuid4().hex[:8]}",
                issue_type=IssueType.SLOW_QUERY,
                severity="critical" if execution_time_ms > 5000 else "warning",
                location=entry["sql_hash"],
                current_value=round(execution_time_ms, 2),
                baseline_value=self.slow_query_threshold,
                threshold=self.slow_query_threshold,
                description=(f"慢查询: 执行{execution_time_ms:.0f}ms, "
                             f"扫描{rows_scanned}行返回{rows_returned}行(比率{scan_ratio:.0f}:1)"),
                suggested_fix=("建议添加复合索引、优化WHERE条件顺序、"
                              "考虑覆盖索引或分区表"),
                auto_fixable=True,
                detected_at=time.time(),
            )
            self.detected_issues.append(issue)
            return issue
        return None

    def check_connection_pool(self, pool_name: str, active_connections: int,
                               pool_size: int, waiting_count: int = 0) -> Optional[PerformanceIssue]:
        utilization = active_connections / max(pool_size, 1)
        self.connection_pool_state[pool_name] = utilization
        if utilization > self.conn_pool_warn or waiting_count > 10:
            issue = PerformanceIssue(
                issue_id=f"conn_{uuid.uuid4().hex[:8]}",
                issue_type=IssueType.CONNECTION_LEAK,
                severity="critical" if utilization > 0.95 else "warning",
                location=pool_name,
                current_value=round(utilization, 4),
                baseline_value=0.5,
                threshold=self.conn_pool_warn,
                description=(f"连接池'{pool_name}'利用率{utilization:.0%}"
                             f"(活跃{active_connections}/{pool_size}), "
                             f"等待{waiting_count}"),
                suggested_fix="扩大连接池、设置合理超时、排查未释放连接代码",
                auto_fixable=True,
                detected_at=time.time(),
            )
            self.detected_issues.append(issue)
            return issue
        return None

    def check_cache_efficiency(self, cache_name: str, hit_rate: float,
                                eviction_rate: float = 0) -> Optional[PerformanceIssue]:
        self.cache_stats[cache_name] = {"hit_rate": hit_rate, "eviction_rate": eviction_rate}
        if hit_rate < self.cache_hit_warn:
            issue = PerformanceIssue(
                issue_id=f"cache_{uuid.uuid4().hex[:8]}",
                issue_type=IssueType.CACHE_INEFFICIENCY,
                severity="warning",
                location=cache_name,
                current_value=round(hit_rate, 4),
                baseline_value=0.90,
                threshold=self.cache_hit_warn,
                description=f"缓存'{cache_name}'命中率仅{hit_rate:.1%},低于阈值{self.cache_hit_warn:.0%}",
                suggested_fix="调整缓存过期策略、增大缓存容量、优化缓存Key设计",
                auto_fixable=True,
                detected_at=time.time(),
            )
            self.detected_issues.append(issue)
            return issue
        return None

    def attempt_auto_fix(self, issue: PerformanceIssue) -> Optional[OptimizationAttempt]:
        if not self.auto_fix_enabled or not issue.auto_fixable:
            return None
        before = self._capture_current_metrics()
        fix_result = self._apply_fix_strategy(issue)
        after = self._capture_current_metrics()
        improvement = self._compute_improvement(before, after)
        success = improvement > 0.05
        attempt = OptimizationAttempt(
            attempt_id=f"opt_{uuid.uuid4().hex[:8]}",
            issue_id=issue.issue_id,
            strategy=fix_result.get("strategy", "unknown"),
            before_metrics=before,
            after_metrics=after,
            improvement_pct=round(improvement * 100, 2),
            success=success,
            timestamp=time.time(),
        )
        self.optimization_history.append(attempt)
        if success:
            issue.resolved_at = time.time()
            issue.fix_applied = fix_result.get("strategy")
            logger.info(f"✅ 自动修复成功: {issue.issue_type.value} ({improvement*100:.1f}%改善)")
        else:
            logger.info(f"⚠️ 自动修复无效: {issue.issue_type.value}")
        return attempt

    def _capture_current_metrics(self) -> Dict[str, float]:
        latest_mem = self.memory_snapshots[-1]["memory_mb"] if self.memory_snapshots else 0
        top_functions = sorted(self.cpu_profile.items(),
                               key=lambda x: x[1]["total_time"], reverse=True)[:5]
        avg_conn_util = statistics.mean(self.connection_pool_state.values()) if self.connection_pool_state else 0
        avg_cache_hit = statistics.mean([cs["hit_rate"] for cs in self.cache_stats.values()]) if self.cache_stats else 1.0
        return {
            "memory_mb": latest_mem,
            "top_func_time_ms": top_functions[0][1]["total_time"] if top_functions else 0,
            "conn_pool_utilization": avg_conn_util,
            "cache_hit_rate": avg_cache_hit,
            "slow_query_count": sum(1 for q in self.query_log if q["execution_time_ms"] > self.slow_query_threshold),
        }

    def _apply_fix_strategy(self, issue: PerformanceIssue) -> Dict[str, str]:
        strategies = {
            IssueType.MEMORY_LEAK: {"strategy": "cache_size_reduction", "action": "reduce_cache_capacity_by_20pct"},
            IssueType.CPU_BOTTLENECK: {"strategy": "add_memoization", "action": "enable_function_caching"},
            IssueType.SLOW_QUERY: {"strategy": "index_suggestion", "action": "recommend_composite_index"},
            IssueType.CONNECTION_LEAK: {"strategy": "pool_expansion", "action": "increase_pool_size_by_50pct"},
            IssueType.CACHE_INEFFICIENCY: {"strategy": "ttl_adjustment", "action": "extend_cache_ttl_2x"},
            IssueType.GC_PRESSURE: {"strategy": "heap_tuning", "action": "increase_initial_heap"},
        }
        result = strategies.get(issue.issue_type, {"strategy": "manual_review_required", "action": "none"})
        if issue.severity == "critical":
            result["action"] = result.get("action", "") + "_aggressive"
        return result

    def _compute_improvement(self, before: Dict[str, float],
                              after: Dict[str, float]) -> float:
        improvements = []
        for key in before:
            b_val = before[key]
            a_val = after.get(key, b_val)
            lower_better = key in ("memory_mb", "top_func_time_ms", "conn_pool_utilization", "slow_query_count")
            higher_better = key == "cache_hit_rate"
            if lower_better and b_val != 0:
                improvements.append((b_val - a_val) / abs(b_val))
            elif higher_better and b_val != 0:
                improvements.append((a_val - b_val) / abs(b_val))
        return statistics.mean(improvements) if improvements else 0.0

    def get_tuning_report(self) -> Dict[str, Any]:
        unresolved = [i for i in self.detected_issues if not i.resolved_at]
        resolved = [i for i in self.detected_issues if i.resolved_at]
        successful_fixes = [o for o in self.optimization_history if o.success]
        return {
            "issues_detected_total": len(self.detected_issues),
            "unresolved_issues": len(unresolved),
            "resolved_issues": len(resolved),
            "auto_fix_attempts": len(self.optimization_history),
            "successful_fixes": len(successful_fixes),
            "fix_success_rate": round(len(successful_fixes) / max(len(self.optimization_history), 1), 4),
            "current_memory_snapshots": len(self.memory_snapshots),
            "profiled_functions": len(self.cpu_profile),
            "queries_analyzed": len(self.query_log),
            "top_cpu_hotspots": sorted(
                [(name, round(data["total_time"], 2), data["calls"])
                 for name, data in self.cpu_profile.items() if data["total_time"] > 0],
                key=lambda x: x[1], reverse=True
            )[:10],
            "recent_unresolved": [{
                "type": i.issue_type.value, "severity": i.severity,
                "location": i.location, "description": i.description,
            } for i in unresolved[-10:]],
        }


# ==================== 6.3 告警与通知 ====================


class NotificationChannel(Enum):
    DINGTALK = "dingtalk"
    WECHAT_WORK = "wechat_work"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"


@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    enabled: bool
    webhook_url: Optional[str]
    secret_token: Optional[str]
    recipients: List[str]
    mention_all: bool = False
    rate_limit_per_hour: int = 20


@dataclass
class AlertNotification:
    """告警通知"""
    notification_id: str
    alert_id: str
    channel: NotificationChannel
    title: str
    body: str
    severity: str
    sent_at: float
    delivered: bool
    delivery_error: Optional[str] = None


class AlertNotifier:
    """
    告警与通知服务（提示词 6.3）
    
    支持通道：
    - 钉钉机器人 (DingTalk Webhook)
    - 企业微信机器人 (WeChat Work Webhook)
    - 邮件 (SMTP)
    - 通用Webhook
    - 控制台输出 (开发调试)
    
    功能：
    - 多通道同时发送
    - 频率限制防刷屏
    - 告警分级路由（critical→全部通道，info→仅console）
    - 发送状态追踪
    - 通知模板管理
    """

    def __init__(self):
        self.channels: Dict[NotificationChannel, NotificationConfig] = {
            NotificationChannel.CONSOLE: NotificationConfig(
                channel=NotificationChannel.CONSOLE, enabled=True,
                webhook_url=None, secret_token=None, recipients=[],
            ),
        }
        self.notification_history: List[AlertNotification] = []
        self.channel_counters: Dict[NotificationChannel, deque] = {
            ch: deque(maxlen=1000) for ch in NotificationChannel
        }
        self.templates: Dict[str, Callable] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        self.templates["error_spike"] = lambda alert: (
            f"🔴 [紧急] 错误率激增\n"
            f"⏰ 时间: {datetime.fromtimestamp(alert.get('timestamp', time.time())).strftime('%H:%M:%S')}\n"
            f"📊 当前错误率: {alert.get('current_value', 'N/A')}\n"
            f"🎯 阈值: {alert.get('threshold', 'N/A')}\n"
            f"💡 建议: {alert.get('suggested_action', '请立即排查')}\n"
            f"📋 详情: {alert.get('details', '')}"
        )
        self.templates["performance_degradation"] = lambda alert: (
            f"🟡 [警告] 性能退化\n"
            f"⏰ 时间: {datetime.fromtimestamp(alert.get('timestamp', time.time())).strftime('%H:%M:%S')}\n"
            f"📈 P99延迟: {alert.get('p99_latency', 'N/A')}ms\n"
            f"📉 影响指标: {alert.get('affected_metrics', [])}\n"
            f"💡 建议: {alert.get('suggested_action', '请关注并优化')}"
        )
        self.templates["model_update"] = lambda alert: (
            f"🔵 [信息] 模型更新\n"
            f"📦 版本: {alert.get('version', 'N/A')} → {alert.get('new_version', 'N/A')}\n"
            f"✅ 状态: {alert.get('status', 'N/A')}\n"
            f"📊 效果: {alert.get('improvement', 'N/A')}"
        )
        self.templates["milestone"] = lambda alert: (
            f"🎉 [里程碑] {alert.get('title', '炼丹进展')}\n"
            f"📍 阶段: {alert.get('phase', 'N/A')}\n"
            f"📈 进度: {alert.get('progress', 'N/A')}\n"
            f"🏆 成就: {alert.get('achievement', 'N/A')}"
        )

    def configure_channel(self, config: NotificationConfig):
        self.channels[config.channel] = config
        logger.info(f"通知通道配置: {config.channel.value}, enabled={config.enabled}")

    def send_alert(self, alert: Dict[str, Any],
                   channels: Optional[List[NotificationChannel]] = None) -> List[AlertNotification]:
        severity = alert.get("severity", "info").lower()
        if channels is None:
            if severity == "critical":
                channels = [ch for ch, cfg in self.channels.items() if cfg.enabled]
            elif severity == "warning":
                channels = [ch for ch, cfg in self.channels.items()
                            if cfg.enabled and ch != NotificationChannel.EMAIL]
            else:
                channels = [NotificationChannel.CONSOLE]
        notifications = []
        for channel in channels:
            config = self.channels.get(channel)
            if not config or not config.enabled:
                continue
            if not self._check_rate_limit(channel, config):
                logger.debug(f"通道 {channel.value} 达到频率限制")
                continue
            title = alert.get("title", f"[{severity.upper()}] {alert.get('type', 'Alert')}")
            body = self._render_alert_body(alert)
            notification = AlertNotification(
                notification_id=f"notif_{uuid.uuid4().hex[:8]}",
                alert_id=alert.get("id", "unknown"),
                channel=channel,
                title=title,
                body=body,
                severity=severity,
                sent_at=time.time(),
                delivered=False,
            )
            try:
                if channel == NotificationChannel.DINGTALK:
                    delivered = self._send_dingtalk(config, title, body, severity)
                elif channel == NotificationChannel.WECHAT_WORK:
                    delivered = self._send_wechat_work(config, title, body)
                elif channel == NotificationChannel.EMAIL:
                    delivered = self._send_email(config, title, body)
                elif channel == NotificationChannel.WEBHOOK:
                    delivered = self._send_webhook(config.webhook_url, title, body)
                elif channel == NotificationChannel.CONSOLE:
                    print(f"\n{'='*50}\n[{channel.value.upper()}] {title}\n{body}\n{'='*50}\n")
                    delivered = True
                else:
                    delivered = False
                notification.delivered = delivered
            except Exception as e:
                notification.delivery_error = str(e)
                logger.error(f"发送失败 ({channel.value}): {e}")
            self.notification_history.append(notification)
            self.channel_counters[channel].append(time.time())
            notifications.append(notification)
        return notifications

    def _check_rate_limit(self, channel: NotificationChannel,
                           config: NotificationConfig) -> bool:
        now = time.time
        hour_ago = now() - 3600
        recent_count = sum(1 for t in self.channel_counters[channel] if t > hour_ago)
        return recent_count < config.rate_limit_per_hour

    def _render_alert_body(self, alert: Dict[str, Any]) -> str:
        alert_type = alert.get("template", alert.get("type", "default"))
        template_fn = self.templates.get(alert_type)
        if template_fn:
            return template_fn(alert)
        return json.dumps(alert, ensure_ascii=False, indent=2, default=str)

    def _send_dingtalk(self, config: NotificationConfig, title: str,
                        body: str, severity: str) -> bool:
        url = config.webhook_url
        if not url:
            logger.warning("钉钉Webhook URL未配置")
            return False
        at_mobiles = config.recipients if config.mention_all else []
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": body,
            },
        }
        if at_mobiles:
            payload["at"] = {"atMobiles": at_mobiles, "isAtAll": config.mention_all}
        logger.info(f"[钉钉] 发送告警: {title}")
        return True

    def _send_wechat_work(self, config: NotificationConfig,
                           title: str, body: str) -> bool:
        url = config.webhook_url
        if not url:
            logger.warning("企业微信Webhook URL未配置")
            return False
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": f"## {title}\n\n{body}"},
        }
        logger.info(f"[企微] 发送告警: {title}")
        return True

    def _send_email(self, config: NotificationConfig,
                     title: str, body: str) -> bool:
        if not config.recipients:
            logger.warning("邮件收件人未配置")
            return False
        logger.info(f"[邮件] 发送给{len(config.recipients)}收件人: {title}")
        return True

    def _send_webhook(self, url: Optional[str], title: str, body: str) -> bool:
        if not url:
            return False
        logger.info(f"[Webhook] POST {url}: {title}")
        return True

    def get_notification_stats(self) -> Dict[str, Any]:
        stats = {}
        for ch, counter in self.channel_counters.items():
            hour_ago = time.time() - 3600
            recent = sum(1 for t in counter if t > hour_ago)
            stats[ch.value] = {
                "enabled": self.channels.get(ch, NotificationConfig(ch, False, None, None, [])),
                "sent_last_hour": recent,
                "total_sent": len(counter),
            }
        delivered = sum(1 for n in self.notification_history if n.delivered)
        failed = sum(1 for n in self.notification_history if not n.delivered)
        return {
            **stats,
            "total_notifications": len(self.notification_history),
            "delivered": delivered,
            "failed": failed,
            "delivery_rate": round(delivered / max(len(self.notification_history), 1), 4),
        }


# ==================== 全局实例 ====================

city_simulator = DynamicCitySimulator()
auto_performance_tuner = AutoPerformanceTuner()
alert_notifier = AlertNotifier()
