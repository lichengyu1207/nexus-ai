"""
测试真实API数据采集
"""
import asyncio
import sys
sys.path.insert(0, '.')

from scripts.amap_client import AmapClient, AmapConfig

async def test_real_collection():
    print("="*60)
    print("🗺️  真实API数据采集测试")
    print("="*60)
    
    config = AmapConfig()
    
    async with AmapClient(config) as client:
        # 测试1: 地理编码
        print("\n📍 测试地理编码...")
        result = await client.geocode("深圳市南山区科技园")
        if result.get("status") == "1":
            geocodes = result.get("geocodes", [])
            if geocodes:
                print(f"✅ 地址: {geocodes[0].get('formatted_address')}")
                print(f"   坐标: {geocodes[0].get('location')}")
        
        # 测试2: POI搜索 - 小区
        print("\n🏠 测试小区搜索...")
        result = await client.text_search(
            keywords="小区",
            city="深圳",
            city_limit=True,
            page_size=10
        )
        if result.get("status") == "1":
            pois = result.get("pois", [])
            print(f"✅ 找到 {len(pois)} 个小区")
            for poi in pois[:5]:
                print(f"   - {poi.get('name')}: {poi.get('address', 'N/A')}")
        
        # 测试3: 周边搜索 - 地铁站
        print("\n🚇 测试地铁站搜索...")
        result = await client.around_search(
            location="113.946040,22.544610",  # 华润城坐标
            radius=1000,
            types="150101",  # 地铁站
            page_size=10
        )
        if result.get("status") == "1":
            pois = result.get("pois", [])
            print(f"✅ 找到 {len(pois)} 个地铁站")
            for poi in pois[:5]:
                print(f"   - {poi.get('name')}: 距离 {poi.get('distance')}米")
        
        # 测试4: 周边搜索 - 学校
        print("\n🏫 测试学校搜索...")
        result = await client.around_search(
            location="113.946040,22.544610",
            radius=1000,
            types="050301,050302,050303",  # 学校
            page_size=10
        )
        if result.get("status") == "1":
            pois = result.get("pois", [])
            print(f"✅ 找到 {len(pois)} 个学校")
            for poi in pois[:5]:
                print(f"   - {poi.get('name')}: 距离 {poi.get('distance')}米")
        
        print(f"\n📊 总请求次数: {client.request_count}")
        print("="*60)
        print("✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_real_collection())
