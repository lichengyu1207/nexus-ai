"""
给用户增加积分
"""
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db")

async def add_integral():
    conn = await aiosqlite.connect(str(DB_PATH))
    
    user_email = "1558691995@qq.com"
    add_amount = 1000
    
    # 更新积分
    await conn.execute(
        "UPDATE users SET integral = integral + ? WHERE email = ?",
        (add_amount, user_email)
    )
    
    await conn.commit()
    
    # 验证
    cursor = await conn.execute(
        "SELECT email, integral FROM users WHERE email = ?",
        (user_email,)
    )
    user = await cursor.fetchone()
    
    print(f"用户: {user[0]}")
    print(f"新积分: {user[1]}")
    
    await conn.close()

asyncio.run(add_integral())
