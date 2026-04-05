"""
积分体系数据库迁移脚本
添加 integral 字段到 users 表
创建 integral_logs 表
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"


async def migrate():
    """执行迁移"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(str(DB_PATH)) as conn:
        cursor = await conn.cursor()
        
        # 检查 integral 字段是否存在
        await cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'integral' not in columns:
            print("添加 integral 字段到 users 表...")
            await cursor.execute("ALTER TABLE users ADD COLUMN integral INTEGER DEFAULT 3")
            print("✅ integral 字段添加成功")
        else:
            print("⏭️ integral 字段已存在，跳过")
        
        # 检查 integral_logs 表是否存在
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integral_logs'")
        if not await cursor.fetchone():
            print("创建 integral_logs 表...")
            await cursor.execute("""
                CREATE TABLE integral_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    change INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    admin_note TEXT,
                    admin_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await cursor.execute("CREATE INDEX idx_integral_logs_user_id ON integral_logs(user_id)")
            await cursor.execute("CREATE INDEX idx_integral_logs_created_at ON integral_logs(created_at)")
            print("✅ integral_logs 表创建成功")
        else:
            print("⏭️ integral_logs 表已存在，跳过")
        
        await conn.commit()
        print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
