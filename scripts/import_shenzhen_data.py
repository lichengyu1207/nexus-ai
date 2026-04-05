"""
深圳试点城市数据填充脚本
分模块导入行政区划、小区、房价、POI数据
"""
import asyncio
import csv
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
sys.path.insert(0, '.')

from backend.database import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ShenzhenDataImporter:
    """深圳数据导入器"""
    
    def __init__(self):
        self.city_id = "city-440300"
        self.city_name = "深圳市"
        self.province_id = "province-440000"
        self.province_name = "广东省"
        
        # ID映射缓存
        self.districts_map: Dict[str, str] = {}  # name -> id
        self.streets_map: Dict[str, str] = {}    # name -> id
        self.communities_map: Dict[str, str] = {}  # name -> id
    
    async def import_province(self, conn) -> str:
        """导入省份数据"""
        logger.info("导入省份数据...")
        
        await conn.execute('''
            INSERT OR IGNORE INTO provinces (id, name, code, centroid_lng, centroid_lat)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.province_id, self.province_name, "440000", 113.280637, 23.125178))
        
        logger.info(f"✅ 省份导入完成: {self.province_name}")
        return self.province_id
    
    async def import_city(self, conn) -> str:
        """导入城市数据"""
        logger.info("导入城市数据...")
        
        await conn.execute('''
            INSERT OR IGNORE INTO cities (id, province_id, name, code, level, centroid_lng, centroid_lat)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (self.city_id, self.province_id, self.city_name, "440300", "地级市", 114.057868, 22.543099))
        
        logger.info(f"✅ 城市导入完成: {self.city_name}")
        return self.city_id
    
    async def import_districts(self, conn) -> Dict[str, str]:
        """导入区县数据"""
        logger.info("导入区县数据...")
        
        # 深圳区县数据
        districts = [
            {"name": "南山区", "code": "440305", "lng": 113.930056, "lat": 22.532974, "avg_price": 90000},
            {"name": "福田区", "code": "440304", "lng": 114.054542, "lat": 22.521944, "avg_price": 85000},
            {"name": "罗湖区", "code": "440303", "lng": 114.131264, "lat": 22.548361, "avg_price": 55000},
            {"name": "宝安区", "code": "440306", "lng": 113.883083, "lat": 22.555417, "avg_price": 55000},
            {"name": "龙岗区", "code": "440307", "lng": 114.246333, "lat": 22.720583, "avg_price": 45000},
            {"name": "龙华区", "code": "440309", "lng": 114.036786, "lat": 22.686917, "avg_price": 55000},
            {"name": "光明区", "code": "440311", "lng": 113.935972, "lat": 22.748056, "avg_price": 45000},
            {"name": "坪山区", "code": "440310", "lng": 114.346333, "lat": 22.708361, "avg_price": 35000},
            {"name": "盐田区", "code": "440308", "lng": 114.236667, "lat": 22.556972, "avg_price": 50000},
            {"name": "大鹏新区", "code": "440312", "lng": 114.498333, "lat": 22.593111, "avg_price": 35000},
        ]
        
        for district in districts:
            district_id = f"district-{district['code']}"
            await conn.execute('''
                INSERT OR IGNORE INTO districts (id, city_id, name, code, centroid_lng, centroid_lat, avg_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (district_id, self.city_id, district["name"], district["code"], 
                  district["lng"], district["lat"], district["avg_price"]))
            self.districts_map[district["name"]] = district_id
        
        logger.info(f"✅ 区县导入完成: {len(districts)} 个")
        return self.districts_map
    
    async def import_streets(self, conn) -> Dict[str, str]:
        """导入街道数据"""
        logger.info("导入街道数据...")
        
        # 深圳街道数据（部分示例）
        streets_data = {
            "南山区": [
                {"name": "南头街道", "code": "440305001"},
                {"name": "南山街道", "code": "440305002"},
                {"name": "沙河街道", "code": "440305003"},
                {"name": "蛇口街道", "code": "440305004"},
                {"name": "招商街道", "code": "440305005"},
                {"name": "粤海街道", "code": "440305006"},
                {"name": "桃源街道", "code": "440305007"},
                {"name": "西丽街道", "code": "440305008"},
            ],
            "福田区": [
                {"name": "南园街道", "code": "440304001"},
                {"name": "园岭街道", "code": "440304002"},
                {"name": "福田街道", "code": "440304003"},
                {"name": "沙头街道", "code": "440304004"},
                {"name": "香蜜湖街道", "code": "440304005"},
                {"name": "梅林街道", "code": "440304006"},
                {"name": "莲花街道", "code": "440304007"},
                {"name": "华富街道", "code": "440304008"},
                {"name": "福保街道", "code": "440304009"},
            ],
            "罗湖区": [
                {"name": "桂园街道", "code": "440303001"},
                {"name": "黄贝街道", "code": "440303002"},
                {"name": "东门街道", "code": "440303003"},
                {"name": "翠竹街道", "code": "440303004"},
                {"name": "南湖街道", "code": "440303005"},
                {"name": "笋岗街道", "code": "440303006"},
                {"name": "东湖街道", "code": "440303007"},
                {"name": "莲塘街道", "code": "440303008"},
            ],
            "宝安区": [
                {"name": "新安街道", "code": "440306001"},
                {"name": "西乡街道", "code": "440306002"},
                {"name": "福永街道", "code": "440306003"},
                {"name": "沙井街道", "code": "440306004"},
                {"name": "松岗街道", "code": "440306005"},
                {"name": "石岩街道", "code": "440306006"},
            ],
            "龙岗区": [
                {"name": "平湖街道", "code": "440307001"},
                {"name": "布吉街道", "code": "440307002"},
                {"name": "坂田街道", "code": "440307003"},
                {"name": "南湾街道", "code": "440307004"},
                {"name": "横岗街道", "code": "440307005"},
                {"name": "龙城街道", "code": "440307006"},
                {"name": "龙岗街道", "code": "440307007"},
            ],
            "龙华区": [
                {"name": "龙华街道", "code": "440309001"},
                {"name": "大浪街道", "code": "440309002"},
                {"name": "民治街道", "code": "440309003"},
                {"name": "观湖街道", "code": "440309004"},
                {"name": "福城街道", "code": "440309005"},
            ],
        }
        
        total_streets = 0
        for district_name, streets in streets_data.items():
            district_id = self.districts_map.get(district_name)
            if not district_id:
                continue
            
            for street in streets:
                street_id = f"street-{street['code']}"
                await conn.execute('''
                    INSERT OR IGNORE INTO streets (id, district_id, name, code, centroid_lng, centroid_lat)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (street_id, district_id, street["name"], street["code"], None, None))
                self.streets_map[street["name"]] = street_id
                total_streets += 1
        
        logger.info(f"✅ 街道导入完成: {total_streets} 个")
        return self.streets_map
    
    async def import_communities(self, conn) -> Dict[str, str]:
        """导入小区数据"""
        logger.info("导入小区数据...")
        
        # 深圳热门小区数据
        communities = [
            # 南山区
            {"name": "华润城", "district": "南山区", "street": "粤海街道", "address": "深圳市南山区科技园", 
             "lng": 113.942, "lat": 22.538, "avg_price": 98000, "developer": "华润置地", "year": 2018},
            {"name": "深圳湾一号", "district": "南山区", "street": "南山街道", "address": "深圳市南山区深圳湾",
             "lng": 113.935, "lat": 22.521, "avg_price": 150000, "developer": "鹏瑞地产", "year": 2015},
            {"name": "半岛城邦", "district": "南山区", "street": "蛇口街道", "address": "深圳市南山区蛇口",
             "lng": 113.921, "lat": 22.489, "avg_price": 120000, "developer": "半岛城邦地产", "year": 2012},
            {"name": "万科云城", "district": "南山区", "street": "西丽街道", "address": "深圳市南山区西丽",
             "lng": 113.965, "lat": 22.582, "avg_price": 85000, "developer": "万科地产", "year": 2016},
            {"name": "招商双玺", "district": "南山区", "street": "蛇口街道", "address": "深圳市南山区蛇口",
             "lng": 113.918, "lat": 22.492, "avg_price": 140000, "developer": "招商地产", "year": 2014},
            
            # 福田区
            {"name": "香蜜湖一号", "district": "福田区", "street": "香蜜湖街道", "address": "深圳市福田区香蜜湖",
             "lng": 114.012, "lat": 22.548, "avg_price": 130000, "developer": "万科地产", "year": 2008},
            {"name": "中海天钻", "district": "福田区", "street": "福田街道", "address": "深圳市福田区CBD",
             "lng": 114.058, "lat": 22.532, "avg_price": 110000, "developer": "中海地产", "year": 2019},
            {"name": "深业上城", "district": "福田区", "street": "莲花街道", "address": "深圳市福田区莲花",
             "lng": 114.068, "lat": 22.562, "avg_price": 100000, "developer": "深业集团", "year": 2017},
            
            # 罗湖区
            {"name": "京基100", "district": "罗湖区", "street": "桂园街道", "address": "深圳市罗湖区桂园",
             "lng": 114.112, "lat": 22.548, "avg_price": 65000, "developer": "京基集团", "year": 2011},
            {"name": "华润万象城", "district": "罗湖区", "street": "南湖街道", "address": "深圳市罗湖区南湖",
             "lng": 114.118, "lat": 22.542, "avg_price": 55000, "developer": "华润置地", "year": 2005},
            
            # 宝安区
            {"name": "壹方中心", "district": "宝安区", "street": "新安街道", "address": "深圳市宝安区新安",
             "lng": 113.885, "lat": 22.555, "avg_price": 75000, "developer": "鸿荣源地产", "year": 2018},
            {"name": "中海锦城", "district": "宝安区", "street": "西乡街道", "address": "深圳市宝安区西乡",
             "lng": 113.865, "lat": 22.572, "avg_price": 65000, "developer": "中海地产", "year": 2016},
            
            # 龙华区
            {"name": "龙光玖龙玺", "district": "龙华区", "street": "龙华街道", "address": "深圳市龙华区龙华",
             "lng": 114.038, "lat": 22.688, "avg_price": 75000, "developer": "龙光地产", "year": 2017},
            {"name": "鸿荣源壹成中心", "district": "龙华区", "street": "龙华街道", "address": "深圳市龙华区龙华",
             "lng": 114.042, "lat": 22.695, "avg_price": 65000, "developer": "鸿荣源地产", "year": 2019},
            
            # 龙岗区
            {"name": "万科广场", "district": "龙岗区", "street": "龙城街道", "address": "深圳市龙岗区龙城",
             "lng": 114.248, "lat": 22.725, "avg_price": 55000, "developer": "万科地产", "year": 2015},
            {"name": "佳兆业城市广场", "district": "龙岗区", "street": "坂田街道", "address": "深圳市龙岗区坂田",
             "lng": 114.058, "lat": 22.632, "avg_price": 50000, "developer": "佳兆业地产", "year": 2016},
        ]
        
        total_communities = 0
        for community in communities:
            district_id = self.districts_map.get(community["district"])
            street_id = self.streets_map.get(community["street"])
            
            community_id = f"community-{str(uuid.uuid4())[:8]}"
            
            await conn.execute('''
                INSERT OR IGNORE INTO communities 
                (id, city_id, district_id, street_id, name, address, lng, lat, avg_price, developer, completion_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (community_id, self.city_id, district_id, street_id, community["name"],
                  community["address"], community["lng"], community["lat"],
                  community["avg_price"], community["developer"], community["year"]))
            
            self.communities_map[community["name"]] = community_id
            total_communities += 1
        
        logger.info(f"✅ 小区导入完成: {total_communities} 个")
        return self.communities_map
    
    async def import_prices(self, conn) -> int:
        """导入房价数据"""
        logger.info("导入房价数据...")
        
        total_prices = 0
        today = datetime.now().strftime("%Y-%m-%d")
        
        for community_name, community_id in self.communities_map.items():
            # 生成模拟房价数据
            base_price = 50000 + (hash(community_name) % 100000)
            
            await conn.execute('''
                INSERT INTO community_prices (id, community_id, avg_price, date, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (f"price-{str(uuid.uuid4())[:8]}", community_id, base_price, today, "模拟数据"))
            total_prices += 1
        
        logger.info(f"✅ 房价导入完成: {total_prices} 条")
        return total_prices
    
    async def import_pois(self, conn) -> int:
        """导入POI数据"""
        logger.info("导入POI数据...")
        
        # POI类型模板
        poi_templates = [
            {"type": "地铁站", "names": ["科技园站", "深大站", "高新园站", "后海站"], "distances": [300, 500, 400, 600]},
            {"type": "学校", "names": ["南山外国语学校", "深圳大学", "实验学校", "育才中学"], "distances": [400, 800, 600, 500]},
            {"type": "医院", "names": ["南山医院", "北大医院", "人民医院", "中医院"], "distances": [1000, 1500, 1200, 800]},
            {"type": "商场", "names": ["华润万家", "海岸城", "万象天地", "来福士"], "distances": [200, 500, 300, 400]},
            {"type": "公园", "names": ["深圳湾公园", "人才公园", "大沙河公园", "塘朗山公园"], "distances": [1500, 800, 1000, 2000]},
        ]
        
        total_pois = 0
        for community_name, community_id in self.communities_map.items():
            for template in poi_templates:
                for i, name in enumerate(template["names"]):
                    await conn.execute('''
                        INSERT INTO pois (id, community_id, type, name, distance, lng, lat)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (f"poi-{str(uuid.uuid4())[:8]}", community_id, template["type"],
                          name, template["distances"][i], None, None))
                    total_pois += 1
        
        logger.info(f"✅ POI导入完成: {total_pois} 条")
        return total_pois
    
    async def run(self):
        """运行完整导入流程"""
        logger.info("="*60)
        logger.info("🚀 深圳试点城市数据填充")
        logger.info("="*60)
        
        conn = await get_db_connection()
        
        try:
            # 开始事务
            await conn.execute("BEGIN TRANSACTION")
            
            # 按顺序导入
            await self.import_province(conn)
            await self.import_city(conn)
            await self.import_districts(conn)
            await self.import_streets(conn)
            await self.import_communities(conn)
            await self.import_prices(conn)
            await self.import_pois(conn)
            
            # 提交事务
            await conn.commit()
            
            logger.info("\n" + "="*60)
            logger.info("📊 导入统计")
            logger.info("="*60)
            logger.info(f"省份: 1 个")
            logger.info(f"城市: 1 个")
            logger.info(f"区县: {len(self.districts_map)} 个")
            logger.info(f"街道: {len(self.streets_map)} 个")
            logger.info(f"小区: {len(self.communities_map)} 个")
            logger.info("="*60)
            logger.info("✅ 深圳数据导入完成！")
            
        except Exception as e:
            await conn.rollback()
            logger.error(f"❌ 导入失败: {e}")
            raise
        finally:
            await conn.close()


async def main():
    importer = ShenzhenDataImporter()
    await importer.run()


if __name__ == '__main__':
    asyncio.run(main())
