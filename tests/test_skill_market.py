# -*- coding: utf-8 -*-
"""
Test Skill Market System
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import asyncpg
import json
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def test_skill_market():
    print("=" * 60)
    print("Testing Skill Market System")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Test 1: Check Tables Exist
        print("\n[1] Checking database tables...")
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN 
            ('skills', 'skill_versions', 'user_skills', 'agent_skills', 
             'skill_invocations', 'skill_reviews', 'skill_dependencies',
             'point_wallets', 'point_transactions', 'point_earning_rules',
             'workflows', 'workflow_executions')
        """)
        print(f"  Found {len(tables)} tables")
        assert len(tables) == 12, f"Expected 12 tables, found {len(tables)}"
        print("  ✅ All tables exist")
        
        # Test 2: Check Builtin Skills
        print("\n[2] Checking builtin skills...")
        skills = await conn.fetch("SELECT * FROM skills WHERE type = 'builtin'")
        print(f"  Found {len(skills)} builtin skills")
        for skill in skills[:3]:
            print(f"    - {skill['name']} ({skill['category']})")
        assert len(skills) >= 8, f"Expected at least 8 builtin skills, found {len(skills)}"
        print("  ✅ Builtin skills exist")
        
        # Test 3: Check Point Earning Rules
        print("\n[3] Checking point earning rules...")
        rules = await conn.fetch("SELECT * FROM point_earning_rules WHERE is_active = TRUE")
        print(f"  Found {len(rules)} active rules")
        for rule in rules[:3]:
            print(f"    - {rule['action_type']}: {rule['points']} points")
        assert len(rules) >= 8, f"Expected at least 8 rules, found {len(rules)}"
        print("  ✅ Point earning rules exist")
        
        # Test 4: Test Skill Insert
        print("\n[4] Testing skill insert...")
        test_skill_id = await conn.fetchval("""
            INSERT INTO skills (name, description, type, category, input_schema, output_schema, 
                              applicable_agents, cost_points, status, tags)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, 'published', $9)
            RETURNING id
        """, "测试技能", "用于测试的技能", "extension", "general",
            json.dumps({"type": "object"}), json.dumps({"type": "object"}),
            ["test_agent"], 10, ["test"])
        print(f"  Created test skill: {test_skill_id}")
        print("  ✅ Skill insert works")
        
        # Test 5: Test User Skill Purchase
        print("\n[5] Testing user skill purchase...")
        test_user_id = str(__import__("uuid").uuid4())  # Generate valid UUID
        
        # Create wallet
        wallet_id = await conn.fetchval("""
            INSERT INTO point_wallets (user_id, total_points, available_points)
            VALUES ($1, 1000, 1000)
            ON CONFLICT (user_id) DO UPDATE SET available_points = 1000
            RETURNING id
        """, test_user_id)
        print(f"  Created wallet: {wallet_id}")
        
        # Purchase skill
        user_skill_id = await conn.fetchval("""
            INSERT INTO user_skills (user_id, skill_id, proficiency)
            VALUES ($1, $2, 10)
            RETURNING id
        """, test_user_id, str(test_skill_id))
        print(f"  Created user skill: {user_skill_id}")
        print("  ✅ User skill purchase works")
        
        # Test 6: Test Skill Invocation
        print("\n[6] Testing skill invocation...")
        invocation_id = await conn.fetchval("""
            INSERT INTO skill_invocations (skill_id, user_id, input_data, output_data, status, duration_ms)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, 'success', 100)
            RETURNING id
        """, str(test_skill_id), test_user_id,
            json.dumps({"test": "input"}), json.dumps({"test": "output"}))
        print(f"  Created invocation: {invocation_id}")
        print("  ✅ Skill invocation works")
        
        # Test 7: Test Point Transaction
        print("\n[7] Testing point transaction...")
        tx_id = await conn.fetchval("""
            INSERT INTO point_transactions (user_id, transaction_type, amount, balance_before, balance_after, source)
            VALUES ($1, 'spend', 10, 1000, 990, 'skill_purchase')
            RETURNING id
        """, test_user_id)
        print(f"  Created transaction: {tx_id}")
        print("  ✅ Point transaction works")
        
        # Test 8: Test Workflow
        print("\n[8] Testing workflow...")
        workflow_id = await conn.fetchval("""
            INSERT INTO workflows (name, description, nodes, edges, created_by, is_template)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, FALSE)
            RETURNING id
        """, "测试工作流", "用于测试的工作流",
            json.dumps([{"id": "node1", "type": "skill", "skill_id": str(test_skill_id)}]),
            json.dumps([]), test_user_id)
        print(f"  Created workflow: {workflow_id}")
        print("  ✅ Workflow creation works")
        
        # Cleanup
        print("\n[9] Cleaning up test data...")
        await conn.execute("DELETE FROM workflow_executions WHERE workflow_id = $1", workflow_id)
        await conn.execute("DELETE FROM workflows WHERE id = $1", workflow_id)
        await conn.execute("DELETE FROM point_transactions WHERE user_id = $1", test_user_id)
        await conn.execute("DELETE FROM skill_invocations WHERE skill_id = $1", str(test_skill_id))
        await conn.execute("DELETE FROM user_skills WHERE skill_id = $1", str(test_skill_id))
        await conn.execute("DELETE FROM skills WHERE id = $1", str(test_skill_id))
        await conn.execute("DELETE FROM point_wallets WHERE user_id = $1", test_user_id)
        print("  ✅ Cleanup complete")
        
    finally:
        await conn.close()
    
    print("\n" + "=" * 60)
    print("All Tests Passed! ✅")
    print("=" * 60)
    return True


async def test_skill_services():
    print("\n" + "=" * 60)
    print("Testing Skill Services")
    print("=" * 60)
    
    from backend.services.skill.skill_registry import Skill, SkillType, SkillCategory, SkillStatus
    
    # Test Skill Model
    print("\n[1] Testing Skill model...")
    skill = Skill(
        id="test-id",
        name="Test Skill",
        description="A test skill",
        type=SkillType.BUILTIN,
        category=SkillCategory.GENERAL,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        dependencies=[],
        applicable_agents=["test_agent"],
        cost_points=0,
        version="1.0.0",
        status=SkillStatus.PUBLISHED
    )
    
    skill_dict = skill.to_dict()
    assert skill_dict["name"] == "Test Skill"
    print("  ✅ Skill model works")
    
    # Test Skill from_db_row
    print("\n[2] Testing Skill from_db_row...")
    row = {
        "id": "db-id",
        "name": "DB Skill",
        "description": "From database",
        "type": "builtin",
        "category": "property",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "dependencies": [],
        "applicable_agents": ["agent1"],
        "cost_points": 10,
        "version": "2.0.0",
        "status": "published"
    }
    
    db_skill = Skill.from_db_row(row)
    assert db_skill.name == "DB Skill"
    print("  ✅ Skill from_db_row works")
    
    from backend.services.skill.point_service import PointWallet, PointTransaction, TransactionType
    
    # Test PointWallet
    print("\n[3] Testing PointWallet model...")
    wallet = PointWallet(
        id="wallet-id",
        user_id="user-001",
        total_points=1000,
        available_points=800,
        frozen_points=200,
        withdrawable_points=500
    )
    
    wallet_dict = wallet.to_dict()
    assert wallet_dict["total_points"] == 1000
    print("  ✅ PointWallet model works")
    
    # Test PointTransaction
    print("\n[4] Testing PointTransaction model...")
    tx = PointTransaction(
        id="tx-id",
        user_id="user-001",
        transaction_type=TransactionType.EARN,
        amount=100,
        balance_before=900,
        balance_after=1000,
        source="daily_checkin"
    )
    
    tx_dict = tx.to_dict()
    assert tx_dict["amount"] == 100
    print("  ✅ PointTransaction model works")
    
    from backend.services.skill.agent_skill_manager import AgentSkillManager
    
    # Test Agent Skill Recommendations
    print("\n[5] Testing Agent Skill Recommendations...")
    recommendations = AgentSkillManager.AGENT_SKILL_RECOMMENDATIONS
    
    assert "libu" in recommendations
    assert "gongbu" in recommendations
    assert len(recommendations["libu"]["recommended_skills"]) > 0
    print(f"  Found {len(recommendations)} agent types")
    print("  ✅ Agent recommendations defined")
    
    # Test Bond Effects
    print("\n[6] Testing Bond Effects...")
    bonds = AgentSkillManager.BOND_EFFECTS
    
    assert len(bonds) > 0
    for skill_set, effect in bonds.items():
        print(f"    - {effect['name']}: {effect['description']}")
    print("  ✅ Bond effects defined")
    
    print("\n" + "=" * 60)
    print("All Service Tests Passed! ✅")
    print("=" * 60)
    return True


async def main():
    success1 = await test_skill_market()
    success2 = await test_skill_services()
    
    if success1 and success2:
        print("\n" + "=" * 60)
        print("SKILL MARKET SYSTEM TEST COMPLETE ✅")
        print("=" * 60)
        print("\nCreated files:")
        print("  - backend/migrations/300_create_skill_tables.py")
        print("  - backend/services/skill/skill_registry.py")
        print("  - backend/services/skill/point_service.py")
        print("  - backend/services/skill/recommendation_engine.py")
        print("  - backend/services/skill/skill_executor.py")
        print("  - backend/services/skill/workflow_engine.py")
        print("  - backend/services/skill/agent_skill_manager.py")
        print("  - backend/routers/skill_router.py")
        print("\nDatabase tables created:")
        print("  - skills, skill_versions, user_skills, agent_skills")
        print("  - skill_invocations, skill_reviews, skill_dependencies")
        print("  - point_wallets, point_transactions, point_earning_rules")
        print("  - workflows, workflow_executions")
    
    return success1 and success2


if __name__ == "__main__":
    asyncio.run(main())
