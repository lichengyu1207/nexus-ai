"""
行政区划详细数据导入与验证
基于国家统计局官方行政区划数据
"""
import asyncio
import aiosqlite
import os
from datetime import datetime

ADMIN_DIVISION_DATA = {
    "全国": {"地级": 333, "地级市": 293, "县级": 2844, "市辖区": 977, "县级市": 397, "县": 1299, "自治县": 117},
    "北京市": {"地级": 0, "地级市": 0, "县级": 16, "市辖区": 16, "县级市": 0, "县": 0, "自治县": 0},
    "天津市": {"地级": 0, "地级市": 0, "县级": 16, "市辖区": 16, "县级市": 0, "县": 0, "自治县": 0},
    "河北省": {"地级": 11, "地级市": 11, "县级": 167, "市辖区": 49, "县级市": 21, "县": 91, "自治县": 6},
    "山西省": {"地级": 11, "地级市": 11, "县级": 117, "市辖区": 26, "县级市": 11, "县": 80, "自治县": 0},
    "内蒙古自治区": {"地级": 12, "地级市": 9, "县级": 103, "市辖区": 23, "县级市": 11, "县": 17, "自治县": 0},
    "辽宁省": {"地级": 14, "地级市": 14, "县级": 100, "市辖区": 59, "县级市": 16, "县": 17, "自治县": 8},
    "吉林省": {"地级": 9, "地级市": 8, "县级": 60, "市辖区": 21, "县级市": 20, "县": 16, "自治县": 3},
    "黑龙江省": {"地级": 13, "地级市": 12, "县级": 121, "市辖区": 54, "县级市": 21, "县": 45, "自治县": 1},
    "上海市": {"地级": 0, "地级市": 0, "县级": 16, "市辖区": 16, "县级市": 0, "县": 0, "自治县": 0},
    "江苏省": {"地级": 13, "地级市": 13, "县级": 95, "市辖区": 55, "县级市": 21, "县": 19, "自治县": 0},
    "浙江省": {"地级": 11, "地级市": 11, "县级": 90, "市辖区": 37, "县级市": 20, "县": 32, "自治县": 1},
    "安徽省": {"地级": 16, "地级市": 16, "县级": 104, "市辖区": 45, "县级市": 9, "县": 50, "自治县": 0},
    "福建省": {"地级": 9, "地级市": 9, "县级": 84, "市辖区": 31, "县级市": 11, "县": 42, "自治县": 0},
    "江西省": {"地级": 11, "地级市": 11, "县级": 100, "市辖区": 27, "县级市": 12, "县": 61, "自治县": 0},
    "山东省": {"地级": 16, "地级市": 16, "县级": 136, "市辖区": 58, "县级市": 26, "县": 52, "自治县": 0},
    "河南省": {"地级": 17, "地级市": 17, "县级": 157, "市辖区": 54, "县级市": 21, "县": 82, "自治县": 0},
    "湖北省": {"地级": 13, "地级市": 12, "县级": 103, "市辖区": 39, "县级市": 26, "县": 35, "自治县": 2},
    "湖南省": {"地级": 14, "地级市": 13, "县级": 122, "市辖区": 36, "县级市": 19, "县": 60, "自治县": 7},
    "广东省": {"地级": 21, "地级市": 21, "县级": 122, "市辖区": 65, "县级市": 20, "县": 34, "自治县": 3},
    "广西壮族自治区": {"地级": 14, "地级市": 14, "县级": 111, "市辖区": 41, "县级市": 10, "县": 48, "自治县": 12},
    "海南省": {"地级": 4, "地级市": 4, "县级": 25, "市辖区": 10, "县级市": 5, "县": 4, "自治县": 6},
    "重庆市": {"地级": 0, "地级市": 0, "县级": 38, "市辖区": 26, "县级市": 0, "县": 8, "自治县": 4},
    "四川省": {"地级": 21, "地级市": 18, "县级": 183, "市辖区": 55, "县级市": 19, "县": 105, "自治县": 4},
    "贵州省": {"地级": 9, "地级市": 6, "县级": 88, "市辖区": 16, "县级市": 10, "县": 50, "自治县": 11},
    "云南省": {"地级": 16, "地级市": 8, "县级": 129, "市辖区": 17, "县级市": 18, "县": 65, "自治县": 29},
    "西藏自治区": {"地级": 7, "地级市": 6, "县级": 74, "市辖区": 8, "县级市": 2, "县": 64, "自治县": 0},
    "陕西省": {"地级": 10, "地级市": 10, "县级": 107, "市辖区": 31, "县级市": 7, "县": 69, "自治县": 0},
    "甘肃省": {"地级": 14, "地级市": 12, "县级": 86, "市辖区": 17, "县级市": 5, "县": 57, "自治县": 7},
    "青海省": {"地级": 8, "地级市": 2, "县级": 44, "市辖区": 7, "县级市": 5, "县": 25, "自治县": 7},
    "宁夏回族自治区": {"地级": 5, "地级市": 5, "县级": 22, "市辖区": 9, "县级市": 2, "县": 11, "自治县": 0},
    "新疆维吾尔自治区": {"地级": 14, "地级市": 4, "县级": 108, "市辖区": 13, "县级市": 29, "县": 60, "自治县": 6},
}

async def create_admin_division_table():
    """创建行政区划统计表"""
    db_path = "data/property-ai.db"
    conn = await aiosqlite.connect(db_path)
    
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_division_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_name TEXT,
                prefecture_count INTEGER DEFAULT 0,
                prefecture_city_count INTEGER DEFAULT 0,
                county_count INTEGER DEFAULT 0,
                district_count INTEGER DEFAULT 0,
                county_city_count INTEGER DEFAULT 0,
                county_count_raw INTEGER DEFAULT 0,
                autonomous_county_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region_name)
            )
        ''')
        
        for region, data in ADMIN_DIVISION_DATA.items():
            await conn.execute('''
                INSERT OR REPLACE INTO admin_division_stats 
                (region_name, prefecture_count, prefecture_city_count, county_count, 
                 district_count, county_city_count, county_count_raw, autonomous_county_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                region,
                data.get("地级", 0),
                data.get("地级市", 0),
                data.get("县级", 0),
                data.get("市辖区", 0),
                data.get("县级市", 0),
                data.get("县", 0),
                data.get("自治县", 0)
            ))
        
        await conn.commit()
        print("✅ 行政区划统计表创建完成")
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
    finally:
        await conn.close()


async def verify_collection_progress():
    """验证数据采集进度"""
    print("="*70)
    print("📊 行政区划数据采集进度报告")
    print("="*70)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db_path = "data/property-ai.db"
    conn = await aiosqlite.connect(db_path)
    
    try:
        # 全国总体进度
        print("📈 全国数据采集总览")
        print("-"*50)
        
        cursor = await conn.execute("SELECT COUNT(*) FROM provinces")
        provinces_collected = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM cities")
        cities_collected = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM districts")
        districts_collected = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM streets")
        streets_collected = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM communities")
        communities_collected = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM pois")
        pois_collected = (await cursor.fetchone())[0]
        
        national_stats = ADMIN_DIVISION_DATA["全国"]
        
        print(f"   省级: {provinces_collected}/34 ({provinces_collected/34*100:.1f}%)")
        print(f"   地级市: {cities_collected}/{national_stats['地级市']} ({cities_collected/national_stats['地级市']*100:.1f}%)")
        print(f"   区县: {districts_collected}/{national_stats['县级']} ({districts_collected/national_stats['县级']*100:.1f}%)")
        print(f"   街道/乡镇: {streets_collected}")
        print(f"   小区: {communities_collected}")
        print(f"   POI: {pois_collected}")
        print()
        
        # 各省份详细进度
        print("="*70)
        print("📋 各省份区县数据采集进度")
        print("="*70)
        print(f"{'省份':<15} {'应采区县':>8} {'已采区县':>8} {'进度':>8} {'状态':>8}")
        print("-"*50)
        
        provinces_to_check = [
            ("广东省", 122), ("江苏省", 95), ("山东省", 136), ("浙江省", 90),
            ("河南省", 157), ("四川省", 183), ("湖北省", 103), ("湖南省", 122),
            ("河北省", 167), ("福建省", 84), ("安徽省", 104), ("辽宁省", 100),
            ("陕西省", 107), ("江西省", 100), ("广西壮族自治区", 111),
            ("云南省", 129), ("山西省", 117), ("贵州省", 88), ("重庆市", 38),
            ("黑龙江省", 121), ("新疆维吾尔自治区", 108), ("甘肃省", 86),
            ("内蒙古自治区", 103), ("吉林省", 60), ("海南省", 25),
            ("青海省", 44), ("宁夏回族自治区", 22), ("西藏自治区", 74),
            ("北京市", 16), ("天津市", 16), ("上海市", 16)
        ]
        
        for province, expected_count in provinces_to_check:
            cursor = await conn.execute('''
                SELECT COUNT(*) FROM districts d
                JOIN cities c ON d.city_id = c.id
                JOIN provinces p ON c.province_id = p.id
                WHERE p.name = ?
            ''', (province,))
            collected = (await cursor.fetchone())[0]
            
            progress = collected / expected_count * 100 if expected_count > 0 else 0
            status = "✅" if progress >= 100 else "🔄" if progress > 0 else "⏳"
            
            print(f"{province:<12} {expected_count:>8} {collected:>8} {progress:>7.1f}% {status}")
        
        print()
        
        # 重点城市采集建议
        print("="*70)
        print("🎯 重点城市数据采集建议")
        print("="*70)
        
        priority_cities = [
            ("广东省", ["深圳", "广州", "东莞", "佛山"], 122),
            ("江苏省", ["南京", "苏州", "无锡", "常州"], 95),
            ("浙江省", ["杭州", "宁波", "温州"], 90),
            ("山东省", ["济南", "青岛", "烟台"], 136),
            ("四川省", ["成都"], 183),
            ("湖北省", ["武汉"], 103),
            ("河南省", ["郑州"], 157),
            ("福建省", ["福州", "厦门", "泉州"], 84),
            ("陕西省", ["西安"], 107),
            ("湖南省", ["长沙"], 122),
            ("安徽省", ["合肥"], 104),
        ]
        
        print("\n📊 第一批采集城市 (GDP TOP10省份):")
        for i, (province, cities, total_counties) in enumerate(priority_cities[:5], 1):
            print(f"   {i}. {province}: {', '.join(cities)}")
            print(f"      区县总数: {total_counties}")
        
        print("\n📊 第二批采集城市 (新一线城市):")
        for i, (province, cities, _) in enumerate(priority_cities[5:], 1):
            print(f"   {i}. {province}: {', '.join(cities)}")
        
        print()
        
        # 数据质量统计
        print("="*70)
        print("🔍 数据质量统计")
        print("="*70)
        
        cursor = await conn.execute('''
            SELECT COUNT(*) FROM communities 
            WHERE lng IS NOT NULL AND lat IS NOT NULL
        ''')
        coords_count = (await cursor.fetchone())[0]
        
        cursor = await conn.execute('''
            SELECT COUNT(*) FROM communities 
            WHERE address IS NOT NULL AND address != ''
        ''')
        address_count = (await cursor.fetchone())[0]
        
        cursor = await conn.execute('''
            SELECT type, COUNT(*) as cnt 
            FROM pois 
            GROUP BY type 
            ORDER BY cnt DESC
            LIMIT 6
        ''')
        poi_stats = await cursor.fetchall()
        
        print(f"   小区坐标完整率: {coords_count}/{communities_collected} ({coords_count/communities_collected*100:.1f}%)")
        print(f"   小区地址完整率: {address_count}/{communities_collected} ({address_count/communities_collected*100:.1f}%)")
        print(f"   POI类型分布:")
        for poi_type, cnt in poi_stats:
            print(f"      - {poi_type}: {cnt}")
        
        print()
        print("="*70)
        print("✅ 验证完成！")
        print("="*70)
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()


async def main():
    """主函数"""
    await create_admin_division_table()
    await verify_collection_progress()


if __name__ == "__main__":
    asyncio.run(main())
