"""
创建对比分析表
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")

async def create_compare_table():
    conn = await aiosqlite.connect(str(DB_PATH))
    
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS compare_analyses (
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
    
    print("✅ compare_analyses 表创建成功")
    
    await conn.close()

asyncio.run(create_compare_table())
