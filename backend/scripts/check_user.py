import asyncio
import aiosqlite
from pathlib import Path

async def check_user():
    DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    # 检查用户是否存在
    cursor = await conn.execute(
        "SELECT id, email, username, role FROM users WHERE email = ?",
        ("1558691995@qq.com",)
    )
    row = await cursor.fetchone()
    
    if row:
        print(f"用户存在: {dict(row)}")
    else:
        print("用户不存在")
    
    # 列出所有用户
    cursor = await conn.execute("SELECT email, username, role FROM users LIMIT 10")
    rows = await cursor.fetchall()
    print("\n数据库中的用户列表:")
    for r in rows:
        print(f"  - {r['email']} ({r['username']}) - {r['role']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_user())
