"""
修复对比分析表结构
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")

async def fix_compare_table():
    conn = await aiosqlite.connect(str(DB_PATH))
    
    # 检查表是否存在
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='compare_analyses'"
    )
    table_exists = await cursor.fetchone()
    
    if table_exists:
        # 删除旧表
        await conn.execute("DROP TABLE compare_analyses")
        print("旧表已删除")
    
    # 创建新表
    await conn.executescript("""
        CREATE TABLE compare_analyses (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            locations TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_compare_analyses_user_id ON compare_analyses(user_id);
        CREATE INDEX IF NOT EXISTS idx_compare_analyses_status ON compare_analyses(status);
    """)
    
    await conn.commit()
    
    # 验证表结构
    cursor = await conn.execute("PRAGMA table_info(compare_analyses)")
    columns = await cursor.fetchall()
    
    print("✅ compare_analyses 表结构:")
    for col in columns:
        print(f"   - {col[1]}: {col[2]}")
    
    await conn.close()

asyncio.run(fix_compare_table())
