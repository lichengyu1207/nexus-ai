"""
检查并创建用户统计所需的数据库表
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")

async def check_and_create_tables():
    """检查并创建必要的表"""
    print("=" * 60)
    print("检查数据库表结构")
    print("=" * 60)
    
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    # 获取所有表
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [t[0] for t in await cursor.fetchall()]
    print(f"\n现有表: {tables}")
    
    # 检查 analysis_tasks 表
    if 'analysis_tasks' not in tables:
        print("\n❌ analysis_tasks 表不存在，正在创建...")
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                result TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            );
            CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON analysis_tasks(user_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
        """)
        await conn.commit()
        print("✅ analysis_tasks 表创建成功")
    else:
        print("\n✅ analysis_tasks 表已存在")
    
    # 检查 analysis_reports 表
    if 'analysis_reports' not in tables:
        print("\n❌ analysis_reports 表不存在，正在创建...")
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_id TEXT,
                title TEXT,
                content TEXT,
                summary TEXT,
                report TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_analysis_reports_user_id ON analysis_reports(user_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_reports_task_id ON analysis_reports(task_id);
        """)
        await conn.commit()
        print("✅ analysis_reports 表创建成功")
    else:
        print("\n✅ analysis_reports 表已存在")
    
    await conn.close()
    print("\n" + "=" * 60)
    print("✅ 检查完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_and_create_tables())
