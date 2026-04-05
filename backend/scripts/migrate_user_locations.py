"""
用户位置表迁移脚本
创建 user_locations 表、geocode_cache 表、house_type_area_stats 表、district_price_stats 表
并为 reports 表添加 location_id 字段
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "app.db"


async def migrate():
    """
    执行迁移
    - 创建 user_locations 表
    - 创建 geocode_cache 表
    - 创建 house_type_area_stats 表
    - 创建 district_price_stats 表
    - 为 reports 表添加 location_id 字段
    """
    print("开始迁移用户位置表...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # 检查 user_locations 表是否存在
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_locations'"
        )
        if await cursor.fetchone():
            print("user_locations 表已存在")
        else:
            print("创建 user_locations 表...")
            await db.execute("""
                CREATE TABLE user_locations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    address TEXT NOT NULL,
                    country TEXT,
                    province TEXT,
                    city TEXT,
                    district TEXT,
                    street TEXT,
                    community TEXT,
                    longitude REAL,
                    latitude REAL,
                    geocoded_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # 创建索引
            await db.execute("CREATE INDEX idx_user_locations_user_id ON user_locations(user_id)")
            await db.execute("CREATE INDEX idx_user_locations_city ON user_locations(city)")
            await db.execute("CREATE INDEX idx_user_locations_district ON user_locations(district)")
            await db.execute("CREATE INDEX idx_user_locations_community ON user_locations(community)")
            await db.execute("CREATE INDEX idx_user_locations_source ON user_locations(source)")
            
            await db.commit()
            print("user_locations 表创建成功")
        
        # 检查 geocode_cache 表是否存在
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='geocode_cache'"
        )
        if await cursor.fetchone():
            print("geocode_cache 表已存在")
        else:
            print("创建 geocode_cache 表...")
            await db.execute("""
                CREATE TABLE geocode_cache (
                    address TEXT PRIMARY KEY,
                    result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            print("geocode_cache 表创建成功")
        
        # 检查 house_type_area_stats 表是否存在
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='house_type_area_stats'"
        )
        if await cursor.fetchone():
            print("house_type_area_stats 表已存在")
        else:
            print("创建 house_type_area_stats 表...")
            await db.execute("""
                CREATE TABLE house_type_area_stats (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    min_area REAL,
                    max_area REAL,
                    avg_area REAL,
                    common_areas TEXT,
                    city TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("CREATE INDEX idx_house_type_area_stats_type ON house_type_area_stats(type)")
            await db.execute("CREATE INDEX idx_house_type_area_stats_city ON house_type_area_stats(city)")
            await db.commit()
            print("house_type_area_stats 表创建成功")
            
            # 初始化户型数据
            await init_house_type_data(db)
        
        # 检查 district_price_stats 表是否存在
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='district_price_stats'"
        )
        if await cursor.fetchone():
            print("district_price_stats 表已存在")
        else:
            print("创建 district_price_stats 表...")
            await db.execute("""
                CREATE TABLE district_price_stats (
                    id TEXT PRIMARY KEY,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    avg_price_per_sqm REAL,
                    min_price_per_sqm REAL,
                    max_price_per_sqm REAL,
                    date DATE,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("CREATE INDEX idx_district_price_stats_city ON district_price_stats(city)")
            await db.execute("CREATE INDEX idx_district_price_stats_district ON district_price_stats(district)")
            await db.commit()
            print("district_price_stats 表创建成功")
            
            # 初始化房价数据
            await init_district_price_data(db)
        
        # 检查 reports 表是否有 location_id 字段
        cursor = await db.execute("PRAGMA table_info(reports)")
        columns = [row["name"] for row in await cursor.fetchall()]
        
        if "location_id" not in columns:
            print("为 reports 表添加 location_id 字段...")
            await db.execute("ALTER TABLE reports ADD COLUMN location_id TEXT")
            await db.commit()
            print("location_id 字段添加成功")
        else:
            print("location_id 字段已存在")
        
        # 显示最终表结构
        print("\n最终表结构:")
        
        cursor = await db.execute("PRAGMA table_info(user_locations)")
        print("\nuser_locations 表:")
        for row in await cursor.fetchall():
            print(f"  {row['name']}: {row['type']}")
        
        cursor = await db.execute("PRAGMA table_info(geocode_cache)")
        print("\ngeocode_cache 表:")
        for row in await cursor.fetchall():
            print(f"  {row['name']}: {row['type']}")
        
        cursor = await db.execute("PRAGMA table_info(house_type_area_stats)")
        print("\nhouse_type_area_stats 表:")
        for row in await cursor.fetchall():
            print(f"  {row['name']}: {row['type']}")
        
        cursor = await db.execute("PRAGMA table_info(district_price_stats)")
        print("\ndistrict_price_stats 表:")
        for row in await cursor.fetchall():
            print(f"  {row['name']}: {row['type']}")
        
        print("\n迁移完成！")


async def init_house_type_data(db):
    """初始化户型面积数据"""
    import json
    import uuid
    
    print("初始化户型面积数据...")
    
    DEFAULT_AREA_STATS = {
        "1室0厅": {"min_area": 25, "max_area": 45, "avg_area": 35, "common_areas": [30, 35, 40]},
        "1室1厅": {"min_area": 30, "max_area": 55, "avg_area": 42, "common_areas": [35, 40, 45, 50]},
        "2室0厅": {"min_area": 40, "max_area": 65, "avg_area": 52, "common_areas": [45, 50, 55, 60]},
        "2室1厅": {"min_area": 50, "max_area": 85, "avg_area": 68, "common_areas": [55, 60, 65, 70, 75, 80]},
        "2室2厅": {"min_area": 60, "max_area": 100, "avg_area": 80, "common_areas": [70, 75, 80, 85, 90]},
        "3室1厅": {"min_area": 70, "max_area": 115, "avg_area": 90, "common_areas": [80, 85, 90, 95, 100, 105, 110]},
        "3室2厅": {"min_area": 85, "max_area": 140, "avg_area": 110, "common_areas": [95, 100, 105, 110, 115, 120, 125, 130]},
        "3室3厅": {"min_area": 100, "max_area": 160, "avg_area": 130, "common_areas": [110, 120, 130, 140, 150]},
        "4室1厅": {"min_area": 100, "max_area": 150, "avg_area": 125, "common_areas": [110, 120, 130, 140]},
        "4室2厅": {"min_area": 120, "max_area": 180, "avg_area": 145, "common_areas": [130, 140, 150, 160, 170]},
        "4室3厅": {"min_area": 140, "max_area": 220, "avg_area": 175, "common_areas": [150, 160, 170, 180, 190, 200]},
        "5室2厅": {"min_area": 150, "max_area": 250, "avg_area": 190, "common_areas": [160, 175, 190, 200, 220]},
        "5室3厅": {"min_area": 180, "max_area": 300, "avg_area": 230, "common_areas": [200, 220, 240, 260, 280]},
    }
    
    for house_type, stats in DEFAULT_AREA_STATS.items():
        await db.execute(
            """
            INSERT INTO house_type_area_stats (
                id, type, min_area, max_area, avg_area, common_areas, city, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                house_type,
                stats["min_area"],
                stats["max_area"],
                stats["avg_area"],
                json.dumps(stats["common_areas"]),
                None,
                "默认统计"
            )
        )
    
    await db.commit()
    print(f"初始化户型面积数据完成，共 {len(DEFAULT_AREA_STATS)} 条")


async def init_district_price_data(db):
    """初始化区域房价数据"""
    import uuid
    from datetime import date
    
    print("初始化区域房价数据...")
    
    DEFAULT_CITY_PRICES = {
        "深圳": {
            "南山区": {"avg": 95000, "min": 75000, "max": 120000},
            "福田区": {"avg": 85000, "min": 70000, "max": 110000},
            "罗湖区": {"avg": 65000, "min": 50000, "max": 85000},
            "宝安区": {"avg": 60000, "min": 45000, "max": 80000},
            "龙岗区": {"avg": 45000, "min": 35000, "max": 60000},
            "龙华区": {"avg": 55000, "min": 42000, "max": 75000},
        },
        "北京": {
            "朝阳区": {"avg": 75000, "min": 60000, "max": 100000},
            "海淀区": {"avg": 90000, "min": 70000, "max": 120000},
            "西城区": {"avg": 110000, "min": 85000, "max": 150000},
            "东城区": {"avg": 100000, "min": 80000, "max": 140000},
        },
        "上海": {
            "浦东新区": {"avg": 70000, "min": 55000, "max": 95000},
            "黄浦区": {"avg": 100000, "min": 80000, "max": 140000},
            "静安区": {"avg": 85000, "min": 65000, "max": 115000},
            "徐汇区": {"avg": 80000, "min": 60000, "max": 110000},
        },
        "广州": {
            "天河区": {"avg": 65000, "min": 50000, "max": 90000},
            "越秀区": {"avg": 55000, "min": 42000, "max": 75000},
            "海珠区": {"avg": 50000, "min": 38000, "max": 70000},
            "番禺区": {"avg": 35000, "min": 28000, "max": 48000},
        },
        "杭州": {
            "西湖区": {"avg": 55000, "min": 42000, "max": 75000},
            "上城区": {"avg": 50000, "min": 38000, "max": 70000},
            "滨江区": {"avg": 48000, "min": 38000, "max": 68000},
        },
        "成都": {
            "锦江区": {"avg": 25000, "min": 18000, "max": 35000},
            "青羊区": {"avg": 23000, "min": 17000, "max": 32000},
            "高新区": {"avg": 28000, "min": 20000, "max": 40000},
        },
        "武汉": {
            "武昌区": {"avg": 22000, "min": 16000, "max": 30000},
            "江汉区": {"avg": 20000, "min": 15000, "max": 28000},
        },
        "南京": {
            "鼓楼区": {"avg": 40000, "min": 30000, "max": 55000},
            "建邺区": {"avg": 42000, "min": 32000, "max": 58000},
        },
    }
    
    today = date.today().isoformat()
    count = 0
    
    for city, districts in DEFAULT_CITY_PRICES.items():
        for district, prices in districts.items():
            await db.execute(
                """
                INSERT INTO district_price_stats (
                    id, city, district, avg_price_per_sqm, 
                    min_price_per_sqm, max_price_per_sqm, date, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            count += 1
    
    await db.commit()
    print(f"初始化区域房价数据完成，共 {count} 条")


async def rollback():
    """
    回滚迁移（仅删除表数据，不删除表）
    注意：SQLite 不支持 DROP COLUMN，location_id 字段将保留
    """
    print("开始回滚...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # 删除 user_locations 表
        await db.execute("DROP TABLE IF EXISTS user_locations")
        # 删除 geocode_cache 表
        await db.execute("DROP TABLE IF EXISTS geocode_cache")
        # 删除 house_type_area_stats 表
        await db.execute("DROP TABLE IF EXISTS house_type_area_stats")
        # 删除 district_price_stats 表
        await db.execute("DROP TABLE IF EXISTS district_price_stats")
        await db.commit()
        
        print("user_locations 表已删除")
        print("geocode_cache 表已删除")
        print("house_type_area_stats 表已删除")
        print("district_price_stats 表已删除")
        print("注意: reports.location_id 字段无法删除（SQLite 限制）")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="用户位置表迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    
    args = parser.parse_args()
    
    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())


if __name__ == "__main__":
    main()
