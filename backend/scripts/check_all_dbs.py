import asyncio
import aiosqlite
from pathlib import Path
import os

async def check_all_databases():
    """检查所有可能的数据库位置"""
    base_path = Path(r"c:\Users\Administrator\Desktop\測試2\backend\data")
    
    # 检查数据目录
    if base_path.exists():
        print(f"数据目录存在: {base_path}")
        for file in base_path.iterdir():
            print(f"  - {file.name}")
    else:
        print(f"数据目录不存在: {base_path}")
    
    # 检查主数据库
    db_path = base_path / "property-ai.db"
    if db_path.exists():
        print(f"\n数据库存在: {db_path}")
        conn = await aiosqlite.connect(str(db_path))
        conn.row_factory = aiosqlite.Row
        
        # 列出所有表
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        print("\n数据库表:")
        for t in tables:
            print(f"  - {t['name']}")
        
        # 检查用户表
        cursor = await conn.execute("SELECT email, username, role FROM users")
        users = await cursor.fetchall()
        print(f"\n用户列表 ({len(users)} 个):")
        for u in users:
            print(f"  - {u['email']} ({u['username']}) - {u['role']}")
        
        # 检查特定用户
        cursor = await conn.execute(
            "SELECT * FROM users WHERE email = ?",
            ("1558691995@qq.com",)
        )
        user = await cursor.fetchone()
        if user:
            print(f"\n找到用户 1558691995@qq.com:")
            for key in user.keys():
                print(f"  {key}: {user[key]}")
        else:
            print("\n用户 1558691995@qq.com 不存在")
        
        await conn.close()
    else:
        print(f"\n数据库不存在: {db_path}")

if __name__ == "__main__":
    asyncio.run(check_all_databases())
