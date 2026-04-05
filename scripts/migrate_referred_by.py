"""
添加来源相关字段迁移脚本
- source: 客观来源（首次触点归因）
- referred_by: 主观来源（用户自述）
- referred_by_other: 主观来源-其他说明
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
        
        # 检查字段是否存在
        await cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'source' not in columns:
            print("添加 source 字段到 users 表...")
            await cursor.execute("ALTER TABLE users ADD COLUMN source TEXT")
            print("✅ source 字段添加成功")
        else:
            print("⏭️ source 字段已存在，跳过")
        
        if 'referred_by' not in columns:
            print("添加 referred_by 字段到 users 表...")
            await cursor.execute("ALTER TABLE users ADD COLUMN referred_by TEXT")
            print("✅ referred_by 字段添加成功")
        else:
            print("⏭️ referred_by 字段已存在，跳过")
        
        if 'referred_by_other' not in columns:
            print("添加 referred_by_other 字段到 users 表...")
            await cursor.execute("ALTER TABLE users ADD COLUMN referred_by_other TEXT")
            print("✅ referred_by_other 字段添加成功")
        else:
            print("⏭️ referred_by_other 字段已存在，跳过")
        
        await conn.commit()
        print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
