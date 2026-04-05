import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import get_db
from datetime import datetime

async def fix_admin():
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        # Check current admin status
        await cursor.execute("SELECT id, email, is_admin, role FROM users WHERE email = ?", ("admin@test.com",))
        row = await cursor.fetchone()
        if row:
            print(f"Current admin: {dict(row)}")
        
        # Update admin status
        await cursor.execute("""
            UPDATE users SET is_admin = 1, role = 'admin' WHERE email = ?
        """, ("admin@test.com",))
        
        # Verify update
        await cursor.execute("SELECT id, email, is_admin, role FROM users WHERE email = ?", ("admin@test.com",))
        row = await cursor.fetchone()
        if row:
            print(f"Updated admin: {dict(row)}")
        
        # Also update integral for test users
        test_users = [
            ("xiaoli@test.com", 5),  # Give more integral
            ("chenjie@test.com", 5),
        ]
        
        for email, integral in test_users:
            await cursor.execute("UPDATE users SET integral = ? WHERE email = ?", (integral, email))
            print(f"Updated {email} integral to {integral}")
        
        await conn.commit()
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(fix_admin())
