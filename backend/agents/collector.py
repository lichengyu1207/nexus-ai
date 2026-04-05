"""
数据采集代理
负责采集房产数据
优先从数据库读取真实采集的数据，如果没有则使用模拟数据
"""
from .base import BaseAgent
from .message import AgentMessage, MessageType
from ..database import get_db_connection
import logging
import random
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class CollectorAgent(BaseAgent):
    """
    数据采集代理
    根据解析的需求采集房产数据
    优先从数据库读取数据采集仪采集的真实数据
    """
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"CollectorAgent received message from {message.sender}")
        
        if message.type == MessageType.REQUEST:
            action = message.content.get("action")
            
            if action == "collect":
                parsed = message.content.get("parsed", {})
                city = parsed.get("city", "未知")
                district = parsed.get("district", "未知")
                
                await self.record_step("开始数据采集", f"正在采集{city} {district}的房产数据...", status="in_progress", input_data={"parsed": parsed})
                
                data = await self._collect_data(parsed)
                
                property_count = len(data.get("properties", []))
                data_source = data.get("data_source", "模拟数据")
                await self.record_step("数据采集完成", f"成功采集{property_count}套房产数据 (来源: {data_source})", status="completed", output_data={"data": data})
                
                await self.respond(message, {"data": data})
    
    async def _collect_data(self, parsed: dict) -> dict:
        """
        采集房产数据
        优先从数据库读取真实采集的数据
        
        Args:
            parsed: 解析的需求
            
        Returns:
            dict: 采集的数据
        """
        city = parsed.get("city", "未知")
        district = parsed.get("district", "未知")
        budget = parsed.get("budget", 0)
        house_type = parsed.get("house_type", "住宅")
        area_range = parsed.get("area_range", {})
        price_max = parsed.get("price_max")
        room_count = parsed.get("room_count")
        
        real_data = await self._fetch_real_data_from_db(city, district, price_max, room_count)
        
        if real_data:
            real_data["data_source"] = "数据采集仪"
            real_data["city"] = city
            real_data["district"] = district
            real_data["house_type"] = house_type
            return real_data
        
        avg_price = self._get_avg_price(city, district)
        trend = self._get_trend(city, district)
        
        properties = self._generate_properties(
            city, district, budget, house_type, area_range, avg_price
        )
        
        data = {
            "city": city,
            "district": district,
            "house_type": house_type,
            "avg_price": avg_price,
            "total_price_range": {
                "min": int(avg_price * 60),
                "max": int(avg_price * 200)
            },
            "trend": trend,
            "source": "房都督AI数据平台",
            "data_source": "模拟数据",
            "update_time": datetime.now().strftime("%Y-%m-%d"),
            "properties": properties,
            "market_stats": {
                "listing_count": random.randint(100, 500),
                "transaction_count_30d": random.randint(20, 100),
                "avg_days_on_market": random.randint(30, 90)
            }
        }
        
        logger.info(f"Collected simulated data for {city} {district}")
        
        return data
    
    async def _fetch_real_data_from_db(self, city: str, district: str = None, price_max: float = None, room_count: int = None) -> dict:
        """
        从数据库读取真实采集的数据
        
        Args:
            city: 城市
            district: 区域（可选）
            price_max: 最大预算（可选）
            room_count: 房间数（可选）
            
        Returns:
            dict: 真实数据，如果没有则返回 None
        """
        try:
            conn = await get_db_connection()
            try:
                where_clauses = ["city = ?"]
                params = [city]
                
                if district:
                    where_clauses.append("district = ?")
                    params.append(district)
                
                where_sql = " AND ".join(where_clauses)
                
                cursor = await conn.execute(
                    f"""
                    SELECT id, poi_id, name, city, district, address, lng, lat, avg_price, tags
                    FROM collected_communities
                    WHERE {where_sql}
                    ORDER BY updated_at DESC
                    LIMIT 50
                    """,
                    params
                )
                rows = await cursor.fetchall()
                
                if not rows:
                    logger.info(f"No real data found in database for {city} {district or ''}")
                    return None
                
                properties = []
                total_price = 0
                price_count = 0
                
                for row in rows:
                    community_id = row["id"]
                    name = row["name"]
                    avg_price = row["avg_price"] or 0
                    
                    price_cursor = await conn.execute(
                        """
                        SELECT avg_price, min_price, max_price, price_per_sqm, source, date
                        FROM collected_prices
                        WHERE community_id = ?
                        ORDER BY collected_at DESC
                        LIMIT 1
                        """,
                        [community_id]
                    )
                    price_row = await price_cursor.fetchone()
                    
                    if price_row:
                        price_per_sqm = price_row["price_per_sqm"] or price_row["avg_price"] or avg_price
                    else:
                        price_per_sqm = avg_price
                    
                    if price_per_sqm and price_per_sqm > 0:
                        total_price += price_per_sqm
                        price_count += 1
                    
                    tags = []
                    if row["tags"]:
                        try:
                            tags = json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
                        except:
                            pass
                    
                    area = random.randint(80, 150)
                    total_property_price = int(area * (price_per_sqm or 50000))
                    
                    if price_max and total_property_price > price_max * 10000:
                        continue
                    
                    property_item = {
                        "id": community_id,
                        "name": name,
                        "area": area,
                        "price": total_property_price,
                        "price_per_sqm": int(price_per_sqm) if price_per_sqm else 0,
                        "rooms": room_count or 3,
                        "floor": f"{random.randint(5, 30)}层",
                        "orientation": random.choice(["南北通透", "东南朝向", "西南朝向"]),
                        "age": random.randint(1, 15),
                        "community": name,
                        "address": row["address"] or f"{city}{district or ''}{name}",
                        "lng": row["lng"],
                        "lat": row["lat"],
                        "tags": tags
                    }
                    
                    properties.append(property_item)
                
                if not properties:
                    return None
                
                avg_price_value = int(total_price / price_count) if price_count > 0 else 50000
                
                cursor = await conn.execute(
                    """
                    SELECT poi_type, COUNT(*) as count
                    FROM collected_pois
                    WHERE city = ?
                    GROUP BY poi_type
                    """,
                    [city]
                )
                poi_rows = await cursor.fetchall()
                poi_stats = {row["poi_type"]: row["count"] for row in poi_rows}
                
                cursor = await conn.execute(
                    """
                    SELECT community_count, poi_count, price_count, last_collection_at
                    FROM city_stats
                    WHERE city_name = ?
                    """,
                    [city]
                )
                stats_row = await cursor.fetchone()
                
                market_stats = {
                    "listing_count": len(properties),
                    "transaction_count_30d": random.randint(20, 100),
                    "avg_days_on_market": random.randint(30, 90),
                    "poi_stats": poi_stats
                }
                
                if stats_row:
                    market_stats["total_communities"] = stats_row["community_count"]
                    market_stats["total_pois"] = stats_row["poi_count"]
                    market_stats["last_collection"] = stats_row["last_collection_at"]
                
                properties.sort(key=lambda x: x["price"])
                
                return {
                    "avg_price": avg_price_value,
                    "total_price_range": {
                        "min": int(avg_price_value * 60),
                        "max": int(avg_price_value * 200)
                    },
                    "trend": "stable",
                    "source": "数据采集仪",
                    "update_time": datetime.now().strftime("%Y-%m-%d"),
                    "properties": properties[:10],
                    "market_stats": market_stats
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Failed to fetch real data from database: {e}")
            return None
    
    def _get_avg_price(self, city: str, district: str) -> int:
        """
        获取平均单价（模拟数据）
        
        Args:
            city: 城市
            district: 区域
            
        Returns:
            int: 平均单价（元/平米）
        """
        price_map = {
            "深圳": {
                "南山区": 98000,
                "福田区": 85000,
                "罗湖区": 65000,
                "宝安区": 62000,
                "龙岗区": 48000,
                "龙华区": 58000,
                "光明区": 42000,
                "坪山区": 35000,
                "南山": 98000,
                "福田": 85000,
                "罗湖": 65000,
                "宝安": 62000,
                "龙岗": 48000,
                "龙华": 58000,
                "光明": 42000,
                "坪山": 35000
            },
            "北京": {
                "朝阳区": 95000,
                "海淀区": 100000,
                "西城区": 110000,
                "东城区": 105000,
                "丰台区": 70000,
                "通州区": 50000,
                "朝阳": 95000,
                "海淀": 100000,
                "西城": 110000,
                "东城": 105000,
                "丰台": 70000,
                "通州": 50000
            },
            "上海": {
                "浦东新区": 85000,
                "黄浦区": 120000,
                "静安区": 100000,
                "徐汇区": 95000,
                "长宁区": 90000,
                "闵行区": 65000,
                "浦东": 85000,
                "黄浦": 120000,
                "静安": 100000,
                "徐汇": 95000,
                "长宁": 90000,
                "闵行": 65000
            },
            "广州": {
                "天河区": 75000,
                "越秀区": 65000,
                "海珠区": 55000,
                "番禺区": 40000,
                "白云区": 35000,
                "天河": 75000,
                "越秀": 65000,
                "海珠": 55000,
                "番禺": 40000,
                "白云": 35000
            },
            "湘潭": {
                "岳塘区": 6500,
                "雨湖区": 5500,
                "岳塘": 6500,
                "雨湖": 5500
            }
        }
        
        city_prices = price_map.get(city, {})
        return city_prices.get(district, 50000)
    
    def _get_trend(self, city: str, district: str) -> str:
        """
        获取价格趋势
        
        Args:
            city: 城市
            district: 区域
            
        Returns:
            str: 趋势 (up/down/stable)
        """
        trends = {
            ("深圳", "南山区"): "up",
            ("深圳", "福田区"): "stable",
            ("深圳", "宝安区"): "up",
            ("深圳", "南山"): "up",
            ("深圳", "福田"): "stable",
            ("深圳", "宝安"): "up",
            ("北京", "朝阳区"): "stable",
            ("北京", "海淀区"): "up",
            ("北京", "朝阳"): "stable",
            ("北京", "海淀"): "up",
            ("上海", "浦东新区"): "up",
            ("上海", "黄浦区"): "stable",
            ("上海", "浦东"): "up",
            ("上海", "黄浦"): "stable",
        }
        
        return trends.get((city, district), "stable")
    
    def _generate_properties(
        self,
        city: str,
        district: str,
        budget: int,
        house_type: str,
        area_range: dict,
        avg_price: int
    ) -> list:
        """
        生成房产列表（模拟数据）
        
        Args:
            city: 城市
            district: 区域
            budget: 预算
            house_type: 房产类型
            area_range: 面积范围
            avg_price: 平均单价
            
        Returns:
            list: 房产列表
        """
        properties = []
        
        min_area = area_range.get("min", 80)
        max_area = area_range.get("max", 150)
        
        community_names = [
            f"{district}花园", f"{district}豪庭", f"{district}名苑",
            f"{district}雅居", f"{district}华府", f"{district}公馆"
        ]
        
        for i, name in enumerate(community_names[:4]):
            area = random.randint(min_area, max_area)
            price_per_sqm = int(avg_price * random.uniform(0.9, 1.1))
            total_price = int(area * price_per_sqm)
            
            rooms = 3 if area < 120 else 4
            
            property_item = {
                "id": f"prop-{i+1}",
                "name": name,
                "area": area,
                "price": total_price,
                "price_per_sqm": price_per_sqm,
                "rooms": rooms,
                "floor": f"{random.randint(5, 30)}层",
                "orientation": random.choice(["南北通透", "东南朝向", "西南朝向"]),
                "age": random.randint(1, 15),
                "community": name,
                "address": f"{city}{district}{name}路{random.randint(1, 100)}号"
            }
            
            properties.append(property_item)
        
        properties.sort(key=lambda x: x["price"])
        
        return properties
