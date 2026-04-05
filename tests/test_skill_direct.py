# -*- coding: utf-8 -*-
"""
Direct test for Skill Market services (bypassing API)
"""
import asyncio
import asyncpg
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"

async def test_skill_market():
    print("=" * 60)
    print("SKILL MARKET DIRECT SERVICE TEST")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("\n[1] Testing Skills Table...")
        skills = await conn.fetch("SELECT id, name, category, status FROM skills LIMIT 5")
        print(f"   Found {len(skills)} skills:")
        for s in skills:
            print(f"   - {s['name']} ({s['category']}) - {s['status']}")
        
        print("\n[2] Testing Point Wallets Table...")
        await conn.execute("""
            INSERT INTO point_wallets (id, user_id, total_points, available_points, frozen_points, withdrawable_points)
            VALUES ($1, $2, 100, 100, 0, 0)
            ON CONFLICT (user_id) DO UPDATE SET available_points = 100
        """, "test-wallet-001", "test-user-001")
        
        wallet = await conn.fetchrow("SELECT * FROM point_wallets WHERE user_id = $1", "test-user-001")
        print(f"   Wallet: total={wallet['total_points']}, available={wallet['available_points']}")
        
        print("\n[3] Testing Point Transactions...")
        await conn.execute("""
            INSERT INTO point_transactions (id, user_id, transaction_type, amount, balance_before, balance_after, source, description)
            VALUES ($1, $2, 'earn', 50, 0, 50, 'test', 'Test transaction')
        """, "test-tx-001", "test-user-001")
        
        txs = await conn.fetch("SELECT * FROM point_transactions WHERE user_id = $1", "test-user-001")
        print(f"   Found {len(txs)} transactions")
        
        print("\n[4] Testing Point Earning Rules...")
        rules = await conn.fetch("SELECT action_type, points, daily_limit FROM point_earning_rules WHERE is_active = TRUE")
        print(f"   Active rules: {len(rules)}")
        for r in rules:
            print(f"   - {r['action_type']}: {r['points']} points (limit: {r['daily_limit']})")
        
        print("\n[5] Testing Skill Invocation...")
        skill = await conn.fetchrow("SELECT * FROM skills WHERE status = 'published' LIMIT 1")
        if skill:
            await conn.execute("""
                INSERT INTO skill_invocations (id, skill_id, user_id, input_data, output_data, status, duration_ms)
                VALUES ($1, $2, $3, $4, $5, 'success', 100)
            """, "test-inv-001", str(skill['id']), "test-user-001", '{"test": true}', '{"result": "ok"}')
            print(f"   Created invocation for skill: {skill['name']}")
        
        print("\n[6] Testing Agent Skills...")
        await conn.execute("""
            INSERT INTO agent_skills (id, agent_id, skill_id, proficiency, use_count, is_active)
            VALUES ($1, $2, $3, 50, 1, TRUE)
            ON CONFLICT (agent_id, skill_id) DO UPDATE SET proficiency = 50
        """, "test-agent-skill-001", "test-agent-001", str(skill['id']) if skill else "00000000-0000-0000-0000-000000000000")
        print("   Agent skill binding created")
        
        print("\n[7] Testing Workflows...")
        await conn.execute("""
            INSERT INTO workflows (id, name, description, nodes, edges, created_by, is_template)
            VALUES ($1, 'Test Workflow', 'A test workflow', '[]', '[]', 'test-user-001', FALSE)
            ON CONFLICT (id) DO NOTHING
        """, "test-workflow-001")
        print("   Workflow created")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_skill_market())
