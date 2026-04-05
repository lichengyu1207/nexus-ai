"""
检查用户积分
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")

async def check_integral():
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    # 检查用户积分
    cursor = await conn.execute(
        "SELECT id, email, username, integral FROM users WHERE email = ?",
        ("1558691995@qq.com",)
    )
    user = await cursor.fetchone()
    
    if user:
        print(f"用户: {user['email']}")
        print(f"积分: {user['integral']}")
        
        # 检查积分日志
        cursor = await conn.execute(
            "SELECT * FROM integral_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (user['id'],)
        )
        logs = await cursor.fetchall()
        
        print(f"\n积分日志 (最近10条):")
        for log in logs:
            print(f"  - {log['action_type']}: {log['amount']} ({log['created_at']})")
    
    await conn.close()

asyncio.run(check_integral())
