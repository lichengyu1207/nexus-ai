"""
验证采集数据入库结果
"""
import asyncio
import aiosqlite
import os

async def verify_data():
    print("="*60)
    print("📊 数据入库验证")
    print("="*60)
    
    db_path = "data/property-ai.db"
    if not os.path.exists(db_path):
        db_path = "backend/database.db"
    if not os.path.exists(db_path):
        db_path = "app.db"
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在")
        return
    
    print(f"📁 使用数据库: {db_path}")
    
    conn = await aiosqlite.connect(db_path)
    
    try:
        # 验证区县数据
        cursor = await conn.execute("SELECT COUNT(*) FROM districts")
        count = (await cursor.fetchone())[0]
        print(f"\n✅ 区县数据: {count} 条")
        
        cursor = await conn.execute("SELECT name, code FROM districts LIMIT 5")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"   - {row[0]} ({row[1]})")
        
        # 验证小区数据
        cursor = await conn.execute("SELECT COUNT(*) FROM communities")
        count = (await cursor.fetchone())[0]
        print(f"\n✅ 小区数据: {count} 条")
        
        cursor = await conn.execute("SELECT name, address FROM communities LIMIT 5")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"   - {row[0]}: {row[1]}")
        
        # 验证POI数据
        cursor = await conn.execute("SELECT COUNT(*) FROM pois")
        count = (await cursor.fetchone())[0]
        print(f"\n✅ POI数据: {count} 条")
        
        cursor = await conn.execute("SELECT type, name, distance FROM pois LIMIT 5")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"   - [{row[0]}] {row[1]} ({row[2]}米)")
        
        # 统计POI类型分布
        cursor = await conn.execute("""
            SELECT type, COUNT(*) as cnt 
            FROM pois 
            GROUP BY type 
            ORDER BY cnt DESC
        """)
        rows = await cursor.fetchall()
        print(f"\n📊 POI类型分布:")
        for row in rows:
            print(f"   - {row[0]}: {row[1]} 个")
        
        print("\n" + "="*60)
        print("✅ 数据验证完成！")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_data())
