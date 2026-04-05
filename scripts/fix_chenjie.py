import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import get_db

async def fix_chenjie():
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        # Check chenjie's current integral
        await cursor.execute("SELECT id, email, integral FROM users WHERE email = ?", ("chenjie@test.com",))
        row = await cursor.fetchone()
        if row:
            print(f"Current chenjie: {dict(row)}")
        
        # Update integral
        await cursor.execute("UPDATE users SET integral = 10 WHERE email = ?", ("chenjie@test.com",))
        
        # Verify
        await cursor.execute("SELECT id, email, integral FROM users WHERE email = ?", ("chenjie@test.com",))
        row = await cursor.fetchone()
        if row:
            print(f"Updated chenjie: {dict(row)}")
        
        await conn.commit()
    
    print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_chenjie())
