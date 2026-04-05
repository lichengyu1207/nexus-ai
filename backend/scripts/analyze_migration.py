"""
全面检测所有数据库数据，判断是否需要迁移
"""
import asyncio
import aiosqlite
from pathlib import Path
import json

# 主数据库
MAIN_DB = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")

# 其他数据库
OTHER_DBS = [
    ("app.db", Path(r"c:\Users\Administrator\Desktop\測試2\app.db")),
    ("backend/data/property-ai.db", Path(r"c:\Users\Administrator\Desktop\測試2\backend\data\property-ai.db")),
    ("data/app.db", Path(r"c:\Users\Administrator\Desktop\測試2\data\app.db")),
]

async def analyze_database(db_path, db_name):
    """分析单个数据库"""
    if not db_path.exists():
        return None
    
    result = {
        "name": db_name,
        "path": str(db_path),
        "tables": {},
        "total_records": 0,
        "needs_migration": False,
        "migration_candidates": []
    }
    
    try:
        conn = await aiosqlite.connect(str(db_path))
        conn.row_factory = aiosqlite.Row
        
        # 获取所有表
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [t['name'] for t in await cursor.fetchall()]
        
        for table in tables:
            # 获取记录数
            cursor = await conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = (await cursor.fetchone())['cnt']
            
            if count > 0:
                result["tables"][table] = count
                result["total_records"] += count
                
                # 获取表结构
                cursor = await conn.execute(f"PRAGMA table_info({table})")
                columns = [c['name'] for c in await cursor.fetchall()]
                
                # 判断是否需要迁移
                if table in ['users', 'analysis_tasks', 'analysis_reports', 'articles', 'plans', 
                            'feedback', 'ip_applications', 'ip_referrals', 'orders', 'recharge_records']:
                    result["needs_migration"] = True
                    result["migration_candidates"].append({
                        "table": table,
                        "count": count,
                        "columns": columns
                    })
        
        await conn.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result

async def check_main_db():
    """检查主数据库现有数据"""
    print("=" * 70)
    print("主数据库现状分析")
    print("=" * 70)
    print(f"路径: {MAIN_DB}")
    
    if not MAIN_DB.exists():
        print("❌ 主数据库不存在!")
        return
    
    conn = await aiosqlite.connect(str(MAIN_DB))
    conn.row_factory = aiosqlite.Row
    
    # 获取所有表
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [t['name'] for t in await cursor.fetchall()]
    
    print(f"\n表数量: {len(tables)}")
    print("\n各表记录数:")
    
    for table in tables:
        cursor = await conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        count = (await cursor.fetchone())['cnt']
        status = "✅" if count > 0 else "⚪"
        print(f"  {status} {table}: {count} 条")
    
    await conn.close()

async def main():
    # 1. 检查主数据库
    await check_main_db()
    
    # 2. 检查其他数据库
    print("\n" + "=" * 70)
    print("其他数据库分析")
    print("=" * 70)
    
    all_results = []
    
    for db_name, db_path in OTHER_DBS:
        result = await analyze_database(db_path, db_name)
        if result:
            all_results.append(result)
    
    # 3. 输出分析结果
    print("\n" + "=" * 70)
    print("迁移建议")
    print("=" * 70)
    
    needs_migration = [r for r in all_results if r.get("needs_migration")]
    
    if not needs_migration:
        print("\n✅ 没有需要迁移的数据")
    else:
        print(f"\n⚠️ 发现 {len(needs_migration)} 个数据库需要迁移:\n")
        
        for result in needs_migration:
            print(f"📁 {result['name']}")
            print(f"   路径: {result['path']}")
            print(f"   总记录数: {result['total_records']}")
            print(f"   需迁移的表:")
            
            for candidate in result["migration_candidates"]:
                print(f"      - {candidate['table']}: {candidate['count']} 条")
                print(f"        字段: {', '.join(candidate['columns'][:5])}{'...' if len(candidate['columns']) > 5 else ''}")
            print()
    
    # 4. 详细数据预览
    print("=" * 70)
    print("详细数据预览")
    print("=" * 70)
    
    for result in all_results:
        if result["total_records"] > 0:
            print(f"\n📁 {result['name']} ({result['total_records']} 条记录)")
            
            for table, count in result["tables"].items():
                print(f"   {table}: {count} 条")
    
    # 5. 生成迁移脚本建议
    if needs_migration:
        print("\n" + "=" * 70)
        print("建议执行的迁移操作")
        print("=" * 70)
        
        for result in needs_migration:
            for candidate in result["migration_candidates"]:
                table = candidate["table"]
                count = candidate["count"]
                print(f"\n# 迁移 {result['name']} -> {table} ({count} 条)")
                print(f"# 需要检查字段匹配和数据去重")

if __name__ == "__main__":
    asyncio.run(main())
