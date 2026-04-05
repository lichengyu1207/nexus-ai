"""
简化版数据采集脚本 - 快速验证
"""
import asyncio
import csv
import logging
import os
import sys
import uuid

sys.path.insert(0, '.')

from scripts.amap_client import AmapClient, AmapConfig, POICollector
from backend.database import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def quick_collect():
    """快速采集测试"""
    print("="*60)
    print("🗺️  快速数据采集测试")
    print("="*60)
    
    config = AmapConfig()
    
    async with AmapClient(config) as client:
        # 1. 采集小区数据
        print("\n🏠 步骤1: 采集小区数据...")
        result = await client.text_search(
            keywords="南山小区",
            city="深圳",
            city_limit=True,
            page_size=20
        )
        
        communities = []
        if result.get("status") == "1":
            pois = result.get("pois", [])
            print(f"✅ 找到 {len(pois)} 个小区")
            
            for poi in pois:
                location = poi.get("location", "").split(",")
                community = {
                    "poi_id": poi.get("id"),
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "lng": float(location[0]) if len(location) == 2 else None,
                    "lat": float(location[1]) if len(location) == 2 else None,
                    "province": poi.get("pname"),
                    "city": poi.get("cityname"),
                    "district": poi.get("adname"),
                    "adcode": poi.get("adcode")
                }
                communities.append(community)
                print(f"   - {community['name']}: {community['address']}")
        
        # 2. 采集POI数据
        print("\n🏪 步骤2: 采集周边POI数据...")
        all_pois = []
        poi_collector = POICollector(client)
        
        for i, community in enumerate(communities[:3]):
            if community.get("lng") and community.get("lat"):
                location = f"{community['lng']},{community['lat']}"
                print(f"  采集 {community['name']} 周边POI...")
                
                try:
                    pois = await poi_collector.collect_community_pois(
                        community_location=location,
                        community_id=community.get("poi_id"),
                        radius_list=[1000]
                    )
                    all_pois.extend(pois)
                    print(f"    找到 {len(pois)} 个POI")
                except Exception as e:
                    print(f"    采集失败: {e}")
        
        # 3. 保存到CSV
        print("\n💾 步骤3: 保存数据...")
        os.makedirs("data", exist_ok=True)
        
        if communities:
            with open("data/quick_communities.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(communities[0].keys()))
                writer.writeheader()
                writer.writerows(communities)
            print(f"✅ 保存 {len(communities)} 个小区到 data/quick_communities.csv")
        
        if all_pois:
            with open("data/quick_pois.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(all_pois[0].keys()))
                writer.writeheader()
                writer.writerows(all_pois)
            print(f"✅ 保存 {len(all_pois)} 个POI到 data/quick_pois.csv")
        
        # 4. 保存到数据库
        print("\n📊 步骤4: 保存到数据库...")
        try:
            conn = await get_db_connection()
            
            for community in communities:
                community_id = f"community-{str(uuid.uuid4())[:8]}"
                try:
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
                        "city-440300",
                        None,
                        None
                    ))
                except Exception as e:
                    print(f"  插入失败: {e}")
            
            await conn.commit()
            await conn.close()
            print(f"✅ 保存到数据库完成")
        except Exception as e:
            print(f"❌ 数据库操作失败: {e}")
        
        # 5. 统计
        print("\n" + "="*60)
        print("📊 采集统计")
        print("="*60)
        print(f"小区数量: {len(communities)}")
        print(f"POI数量: {len(all_pois)}")
        print(f"API请求次数: {client.request_count}")
        print("="*60)
        print("✅ 快速采集完成！")


if __name__ == "__main__":
    asyncio.run(quick_collect())
