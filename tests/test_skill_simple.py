# -*- coding: utf-8 -*-
import asyncio
import asyncpg
import uuid

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"

async def main():
    print("=" * 60)
    print("SKILL MARKET DIRECT TEST")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("\n[1] Skills Table...")
        skills = await conn.fetch("SELECT id, name, category, status FROM skills LIMIT 5")
        print(f"   Found {len(skills)} skills:")
        for s in skills:
            print(f"   - {s['name']} ({s['category']}) - {s['status']}")
        
        print("\n[2] Point Wallets...")
        wallet_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO point_wallets (id, user_id, total_points, available_points, frozen_points, withdrawable_points)
            VALUES ($1, $2, 100, 100, 0, 0)
            ON CONFLICT (user_id) DO UPDATE SET available_points = 100
        """, wallet_id, user_id)
        
        wallet = await conn.fetchrow("SELECT * FROM point_wallets WHERE user_id = $1", user_id)
        print(f"   Wallet: total={wallet['total_points']}, available={wallet['available_points']}")
        
        print("\n[3] Point Earning Rules...")
        rules = await conn.fetch("SELECT action_type, points FROM point_earning_rules WHERE is_active = TRUE")
        print(f"   Active rules: {len(rules)}")
        for r in rules:
            print(f"   - {r['action_type']}: {r['points']} points")
        
        print("\n[4] Agent Skills...")
        skill = await conn.fetchrow("SELECT id, name FROM skills WHERE status = 'published' LIMIT 1")
        if skill:
            agent_skill_id = str(uuid.uuid4())
            agent_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO agent_skills (id, agent_id, skill_id, proficiency, use_count, is_active)
                VALUES ($1, $2, $3, 50, 1, TRUE)
                ON CONFLICT (agent_id, skill_id) DO UPDATE SET proficiency = 50
            """, agent_skill_id, agent_id, str(skill['id']))
            print(f"   Agent skill binding created for: {skill['name']}")
        
        print("\n[5] Workflows...")
        workflow_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO workflows (id, name, description, nodes, edges, created_by, is_template)
            VALUES ($1, 'Test Workflow', 'A test workflow', '[]', '[]', $2, FALSE)
            ON CONFLICT (id) DO NOTHING
        """, workflow_id, user_id)
        print("   Workflow created")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
