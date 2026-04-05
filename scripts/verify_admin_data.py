"""
行政区划统计数据导入与验证
基于国家统计局官方数据验证采集数据的完整性
"""
import asyncio
import aiosqlite
import os
from datetime import datetime

NATIONAL_STATS = {
    2024: {
        "地级区划数": 333,
        "地级市数": 293,
        "县级区划数": 2846,
        "市辖区数": 977,
        "县级市数": 397,
        "县数": 1301,
        "自治县数": 117
    },
    2023: {
        "地级区划数": 333,
        "地级市数": 293,
        "县级区划数": 2844,
        "市辖区数": 977,
        "县级市数": 397,
        "县数": 1299,
        "自治县数": 117
    },
    2022: {
        "地级区划数": 333,
        "地级市数": 293,
        "县级区划数": 2843,
        "市辖区数": 977,
        "县级市数": 394,
        "县数": 1301,
        "自治县数": 117
    }
}

async def verify_administrative_data():
    """验证行政区划数据完整性"""
    print("="*70)
    print("📊 行政区划数据完整性验证报告")
    print("="*70)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db_path = "data/property-ai.db"
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    conn = await aiosqlite.connect(db_path)
    
    try:
        # 获取国家统计数据（使用2024年最新数据）
        stats = NATIONAL_STATS[2024]
        
        print("📈 国家统计局官方数据 (2024年)")
        print("-"*50)
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()
        
        # 查询数据库中的行政区划数据
        print("📦 数据库采集数据统计")
        print("-"*50)
        
        # 省级
        cursor = await conn.execute("SELECT COUNT(*) FROM provinces")
        province_count = (await cursor.fetchone())[0]
        print(f"   省级区划: {province_count} 个 (预期: 34个)")
        
        # 市级
        cursor = await conn.execute("SELECT COUNT(*) FROM cities")
        city_count = (await cursor.fetchone())[0]
        print(f"   地级市: {city_count} 个 (预期: {stats['地级市数']}个)")
        
        # 区县级
        cursor = await conn.execute("SELECT COUNT(*) FROM districts")
        district_count = (await cursor.fetchone())[0]
        print(f"   区县: {district_count} 个 (预期: {stats['县级区划数']}个)")
        
        # 街道级
        cursor = await conn.execute("SELECT COUNT(*) FROM streets")
        street_count = (await cursor.fetchone())[0]
        print(f"   街道/乡镇: {street_count} 个")
        
        # 小区
        cursor = await conn.execute("SELECT COUNT(*) FROM communities")
        community_count = (await cursor.fetchone())[0]
        print(f"   小区: {community_count} 个")
        
        # POI
        cursor = await conn.execute("SELECT COUNT(*) FROM pois")
        poi_count = (await cursor.fetchone())[0]
        print(f"   POI: {poi_count} 个")
        
        print()
        
        # 数据完整性评估
        print("="*70)
        print("📋 数据完整性评估")
        print("="*70)
        
        # 省级覆盖率
        province_rate = (province_count / 34) * 100 if province_count > 0 else 0
        print(f"   省级覆盖率: {province_rate:.1f}% ({province_count}/34)")
        
        # 地级市覆盖率
        city_rate = (city_count / stats['地级市数']) * 100 if city_count > 0 else 0
        print(f"   地级市覆盖率: {city_rate:.1f}% ({city_count}/{stats['地级市数']})")
        
        # 区县覆盖率
        district_rate = (district_count / stats['县级区划数']) * 100 if district_count > 0 else 0
        print(f"   区县覆盖率: {district_rate:.1f}% ({district_count}/{stats['县级区划数']})")
        
        print()
        
        # 数据采集建议
        print("="*70)
        print("💡 数据采集建议")
        print("="*70)
        
        if province_count < 34:
            print(f"   ⚠️ 需要补充 {34 - province_count} 个省级区划数据")
        
        if city_count < stats['地级市数']:
            print(f"   ⚠️ 需要补充 {stats['地级市数'] - city_count} 个地级市数据")
        
        if district_count < stats['县级区划数']:
            print(f"   ⚠️ 需要补充 {stats['县级区划数'] - district_count} 个区县数据")
        
        if community_count < 1000:
            print(f"   ⚠️ 小区数据较少，建议扩大采集范围")
        
        print()
        
        # 采集优先级建议
        print("="*70)
        print("🎯 采集优先级建议")
        print("="*70)
        print("   1. 一线城市: 北京、上海、广州、深圳")
        print("   2. 新一线城市: 成都、杭州、重庆、武汉、西安、苏州、天津、南京")
        print("   3. 二线城市: 无锡、宁波、南通、福州、厦门等")
        print("   4. 70个大中城市: 国家统计局房价监测城市")
        print("   5. 全国所有地级市: 最终覆盖目标")
        print()
        
        # 数据质量检查
        print("="*70)
        print("🔍 数据质量检查")
        print("="*70)
        
        # 检查小区数据完整性
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM communities 
            WHERE lng IS NOT NULL AND lat IS NOT NULL
        """)
        communities_with_coords = (await cursor.fetchone())[0]
        print(f"   有坐标的小区: {communities_with_coords}/{community_count}")
        
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM communities 
            WHERE address IS NOT NULL AND address != ''
        """)
        communities_with_address = (await cursor.fetchone())[0]
        print(f"   有地址的小区: {communities_with_address}/{community_count}")
        
        # 检查POI数据分布
        cursor = await conn.execute("""
            SELECT type, COUNT(*) as cnt 
            FROM pois 
            GROUP BY type 
            ORDER BY cnt DESC
        """)
        poi_types = await cursor.fetchall()
        print(f"   POI类型分布:")
        for poi_type, cnt in poi_types[:10]:
            print(f"      - {poi_type}: {cnt}")
        
        print()
        print("="*70)
        print("✅ 验证完成！")
        print("="*70)
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    finally:
        await conn.close()


async def create_stats_table():
    """创建统计数据表"""
    db_path = "data/property-ai.db"
    conn = await aiosqlite.connect(db_path)
    
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS admin_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                stat_type TEXT,
                stat_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入统计数据
        for year, stats in NATIONAL_STATS.items():
            for stat_type, value in stats.items():
                await conn.execute('''
                    INSERT OR REPLACE INTO admin_stats (year, stat_type, stat_value)
                    VALUES (?, ?, ?)
                ''', (year, stat_type, value))
        
        await conn.commit()
        print("✅ 统计数据表创建完成")
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_stats_table())
    asyncio.run(verify_administrative_data())
