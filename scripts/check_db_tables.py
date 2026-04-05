"""
检查数据库表结构
"""
import asyncio
import aiosqlite
import os

async def check_tables():
    print("="*60)
    print("📊 数据库表结构检查")
    print("="*60)
    
    db_paths = [
        "backend/database.db",
        "data/property-ai.db",
        "app.db",
        "backend/data/property-ai.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n📁 数据库: {db_path}")
            conn = await aiosqlite.connect(db_path)
            
            try:
                cursor = await conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name
                """)
                tables = await cursor.fetchall()
                print(f"   表数量: {len(tables)}")
                
                for table in tables:
                    table_name = table[0]
                    cursor = await conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = (await cursor.fetchone())[0]
                    print(f"   - {table_name}: {count} 条记录")
            except Exception as e:
                print(f"   ❌ 错误: {e}")
            finally:
                await conn.close()

if __name__ == "__main__":
    asyncio.run(check_tables())
