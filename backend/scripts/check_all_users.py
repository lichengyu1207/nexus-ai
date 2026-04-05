import asyncio
import aiosqlite
from pathlib import Path

async def check_all_dbs():
    db_files = [
        r"c:\Users\Administrator\Desktop\測試2\app.db",
        r"c:\Users\Administrator\Desktop\測試2\backend\data\property-ai.db",
        r"c:\Users\Administrator\Desktop\測試2\data\app.db",
        r"c:\Users\Administrator\Desktop\測試2\data\property-ai.db",
    ]
    
    target_email = "1558691995@qq.com"
    
    for db_path in db_files:
        p = Path(db_path)
        if not p.exists():
            print(f"\n❌ 不存在: {db_path}")
            continue
        
        print(f"\n✅ 检查: {db_path}")
        try:
            conn = await aiosqlite.connect(str(p))
            conn.row_factory = aiosqlite.Row
            
            # 列出所有表
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t['name'] for t in await cursor.fetchall()]
            print(f"   表: {tables}")
            
            # 检查是否有users表
            if 'users' in tables:
                cursor = await conn.execute("SELECT email, username, role FROM users")
                users = await cursor.fetchall()
                print(f"   用户数: {len(users)}")
                for u in users:
                    print(f"      - {u['email']} ({u['username']}) - {u['role']}")
                
                # 检查目标用户
                cursor = await conn.execute(
                    "SELECT * FROM users WHERE email = ?", (target_email,)
                )
                user = await cursor.fetchone()
                if user:
                    print(f"\n   🎯 找到用户 {target_email}!")
                    for key in user.keys():
                        print(f"      {key}: {user[key]}")
            else:
                print("   无 users 表")
            
            await conn.close()
        except Exception as e:
            print(f"   错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_dbs())
