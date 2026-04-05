"""
测试数据采集任务监控系统
"""
import asyncio
import aiosqlite

async def test():
    conn = await aiosqlite.connect('data/property-ai.db')
    
    cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('data_collection_tasks', 'city_stats', 'data_collection_history')")
    tables = await cursor.fetchall()
    print('已创建的表:', [t[0] for t in tables])
    
    cursor = await conn.execute('SELECT COUNT(*) FROM city_stats')
    count = (await cursor.fetchone())[0]
    print(f'城市统计记录: {count} 条')
    
    cursor = await conn.execute('SELECT COUNT(*) FROM data_collection_tasks')
    count = (await cursor.fetchone())[0]
    print(f'任务记录: {count} 条')
    
    cursor = await conn.execute('SELECT city_name, user_count, community_count FROM city_stats LIMIT 5')
    rows = await cursor.fetchall()
    print('城市统计示例:')
    for row in rows:
        print(f'  {row[0]}: 用户={row[1]}, 小区={row[2]}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test())
