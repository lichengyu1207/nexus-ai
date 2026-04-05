import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import get_db

async def make_super_admin():
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        # Check current admin status
        await cursor.execute("SELECT id, email, is_admin, role FROM users WHERE email = ?", ("admin@test.com",))
        row = await cursor.fetchone()
        if row:
            print(f"Current admin: {dict(row)}")
        
        # Update to super admin
        await cursor.execute("""
            UPDATE users SET is_admin = 1, role = 'super_admin' WHERE email = ?
        """, ("admin@test.com",))
        
        # Verify update
        await cursor.execute("SELECT id, email, is_admin, role FROM users WHERE email = ?", ("admin@test.com",))
        row = await cursor.fetchone()
        if row:
            print(f"Updated admin: {dict(row)}")
        
        await conn.commit()
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(make_super_admin())
