import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import get_db
from datetime import datetime
import json

USER_SOURCES = {
    "xiaowang@test.com": "laohai",
    "xiaoli@test.com": "direct",
    "laozhang@test.com": "seo",
    "chenjie@test.com": "urgent"
}

async def fix_user_sources():
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        for email, source in USER_SOURCES.items():
            await cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            row = await cursor.fetchone()
            if not row:
                print(f"User {email} not found")
                continue
            
            user_id = row["id"]
            
            await cursor.execute("DELETE FROM user_sources WHERE user_id = ?", (user_id,))
            
            await cursor.execute("""
                INSERT INTO user_sources (id, user_id, source, url_params, ip_address, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"src_{user_id}",
                user_id,
                source,
                json.dumps({"test": "true"}),
                "127.0.0.1",
                "Test Script",
                datetime.utcnow().isoformat()
            ))
            
            await cursor.execute("UPDATE users SET source = ? WHERE id = ?", (source, user_id))
            
            print(f"Updated {email}: source = {source}")
        
        await conn.commit()
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(fix_user_sources())
