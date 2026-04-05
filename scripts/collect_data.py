"""
完整数据采集脚本
基于高德API采集行政区划、小区、POI数据
"""
import asyncio
import csv
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import uuid

sys.path.insert(0, '.')

from scripts.amap_client import AmapClient, AmapConfig, POICollector, CommunityCollector
from backend.database import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollector:
    """数据采集器"""
    
    def __init__(self, api_key: str = None):
        self.config = AmapConfig()
        if api_key:
            self.config.api_key = api_key
        
        self.client: Optional[AmapClient] = None
        self.community_collector: Optional[CommunityCollector] = None
        self.poi_collector: Optional[POICollector] = None
        
        # 缓存
        self.districts_map: Dict[str, str] = {}
        self.communities_map: Dict[str, str] = {}
    
    async def __aenter__(self):
        self.client = AmapClient(self.config)
        await self.client.__aenter__()
        self.community_collector = CommunityCollector(self.client)
        self.poi_collector = POICollector(self.client)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def collect_districts(
        self,
        city: str,
        adcode: str
    ) -> List[Dict]:
        """
        采集区县数据
        
        Args:
            city: 城市名称
            adcode: 城市行政区划代码
        """
        logger.info(f"采集 {city} 的区县数据...")
        
        # 深圳区县数据（实际应从API获取）
        districts_data = {
            "深圳市": [
                {"name": "南山区", "code": "440305", "lng": 113.930056, "lat": 22.532974},
                {"name": "福田区", "code": "440304", "lng": 114.054542, "lat": 22.521944},
                {"name": "罗湖区", "code": "440303", "lng": 114.131264, "lat": 22.548361},
                {"name": "宝安区", "code": "440306", "lng": 113.883083, "lat": 22.555417},
                {"name": "龙岗区", "code": "440307", "lng": 114.246333, "lat": 22.720583},
                {"name": "龙华区", "code": "440309", "lng": 114.036786, "lat": 22.686917},
                {"name": "光明区", "code": "440311", "lng": 113.935972, "lat": 22.748056},
                {"name": "坪山区", "code": "440310", "lng": 114.346333, "lat": 22.708361},
                {"name": "盐田区", "code": "440308", "lng": 114.236667, "lat": 22.556972},
                {"name": "大鹏新区", "code": "440312", "lng": 114.498333, "lat": 22.593111},
            ]
        }
        
        districts = districts_data.get(city, [])
        logger.info(f"✅ 找到 {len(districts)} 个区县")
        
        return districts
    
    async def collect_communities(
        self,
        city: str,
        district: str = None,
        max_pages: int = 10
    ) -> List[Dict]:
        """
        采集小区数据
        
        Args:
            city: 城市名称
            district: 区县名称（可选）
            max_pages: 最大页数
        """
        logger.info(f"采集 {city} {district or ''} 的小区数据...")
        
        all_communities = []
        seen_ids = set()
        
        keywords = ["小区", "住宅", "花园", "苑", "居"]
        
        for keyword in keywords:
            try:
                search_keyword = f"{district}{keyword}" if district else keyword
                
                pois = await self.client.search_all_pages(
                    self.client.text_search,
                    keywords=search_keyword,
                    city=city,
                    city_limit=True,
                    max_pages=max_pages
                )
                
                for poi in pois:
                    poi_id = poi.get("id")
                    if poi_id in seen_ids:
                        continue
                    
                    seen_ids.add(poi_id)
                    location = poi.get("location", "").split(",")
                    
                    community = {
                        "poi_id": poi_id,
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "lng": float(location[0]) if len(location) == 2 else None,
                        "lat": float(location[1]) if len(location) == 2 else None,
                        "province": poi.get("pname"),
                        "city": poi.get("cityname"),
                        "district": poi.get("adname"),
                        "adcode": poi.get("adcode"),
                        "type": poi.get("type"),
                        "type_code": poi.get("typecode")
                    }
                    
                    all_communities.append(community)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"采集失败: {e}")
        
        logger.info(f"✅ 找到 {len(all_communities)} 个小区")
        return all_communities
    
    async def collect_pois_for_community(
        self,
        community_id: str,
        location: str
    ) -> List[Dict]:
        """
        采集小区周边POI
        
        Args:
            community_id: 小区ID
            location: 小区坐标 "lng,lat"
        """
        try:
            pois = await self.poi_collector.collect_community_pois(
                community_location=location,
                community_id=community_id,
                radius_list=[500, 1000, 2000]
            )
            return pois
        except Exception as e:
            logger.error(f"采集POI失败: {e}")
            return []
    
    async def save_to_database(
        self,
        communities: List[Dict],
        pois: List[Dict] = None
    ):
        """
        保存数据到数据库
        
        Args:
            communities: 小区数据列表
            pois: POI数据列表
        """
        logger.info("保存数据到数据库...")
        
        conn = await get_db_connection()
        
        try:
            await conn.execute("BEGIN TRANSACTION")
            
            # 保存小区数据
            for community in communities:
                community_id = f"community-{str(uuid.uuid4())[:8]}"
                
                await conn.execute('''
                    INSERT OR IGNORE INTO communities 
                    (id, name, address, lng, lat, city_id, district_id, avg_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    community_id,
                    community.get("name"),
                    community.get("address"),
                    community.get("lng"),
                    community.get("lat"),
                    "city-440300",  # 深圳市
                    None,  # district_id
                    None   # avg_price
                ))
                
                self.communities_map[community.get("poi_id")] = community_id
            
            # 保存POI数据
            if pois:
                for poi in pois:
                    await conn.execute('''
                        INSERT OR IGNORE INTO pois 
                        (id, community_id, type, name, distance, lng, lat)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        f"poi-{str(uuid.uuid4())[:8]}",
                        poi.get("community_id"),
                        poi.get("type"),
                        poi.get("name"),
                        poi.get("distance"),
                        poi.get("lng"),
                        poi.get("lat")
                    ))
            
            await conn.commit()
            logger.info(f"✅ 保存完成: {len(communities)} 个小区")
            
        except Exception as e:
            await conn.rollback()
            logger.error(f"保存失败: {e}")
            raise
        finally:
            await conn.close()
    
    def save_to_csv(
        self,
        data: List[Dict],
        filename: str,
        output_dir: str = "data"
    ):
        """保存数据到CSV文件"""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        if not data:
            logger.warning(f"没有数据可保存到 {filename}")
            return
        
        fieldnames = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"✅ 已保存 {len(data)} 条记录到 {filepath}")


async def main():
    """主函数"""
    print("="*60)
    print("🗺️  房产数据采集系统")
    print("="*60)
    
    async with DataCollector() as collector:
        # 1. 采集区县数据
        print("\n📍 步骤1: 采集区县数据")
        districts = await collector.collect_districts("深圳市", "440300")
        collector.save_to_csv(districts, "shenzhen_districts.csv")
        
        # 2. 采集小区数据（示例：南山区）
        print("\n🏠 步骤2: 采集小区数据")
        communities = await collector.collect_communities(
            city="深圳",
            district="南山",
            max_pages=5
        )
        collector.save_to_csv(communities, "shenzhen_communities.csv")
        
        # 3. 采集POI数据（示例：前5个小区）
        print("\n🏪 步骤3: 采集周边POI数据")
        all_pois = []
        
        for i, community in enumerate(communities[:5]):
            if community.get("lng") and community.get("lat"):
                location = f"{community['lng']},{community['lat']}"
                pois = await collector.collect_pois_for_community(
                    community.get("poi_id"),
                    location
                )
                all_pois.extend(pois)
                print(f"  {i+1}/5: {community.get('name')} - 找到 {len(pois)} 个POI")
        
        collector.save_to_csv(all_pois, "shenzhen_pois.csv")
        
        # 4. 保存到数据库
        print("\n💾 步骤4: 保存到数据库")
        await collector.save_to_database(communities, all_pois)
        
        # 5. 统计报告
        print("\n" + "="*60)
        print("📊 采集统计")
        print("="*60)
        print(f"区县数量: {len(districts)}")
        print(f"小区数量: {len(communities)}")
        print(f"POI数量: {len(all_pois)}")
        print(f"API请求次数: {collector.client.request_count}")
        print("="*60)
        print("✅ 数据采集完成！")


if __name__ == "__main__":
    asyncio.run(main())
