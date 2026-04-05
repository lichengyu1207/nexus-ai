# -*- coding: utf-8 -*-
"""
MaAS 多智能体架构搜索系统测试
"""
import asyncio
import asyncpg
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"


async def test_maas():
    print("=" * 60)
    print("MaAS Multi-Agent Architecture Search Test")
    print("=" * 60)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("\n[1] Testing agent_operators table...")
        operators = await conn.fetch("SELECT name, display_name, agent_type, cost_estimate FROM agent_operators")
        print(f"   Found {len(operators)} operators:")
        for op in operators:
            print(f"   - {op['display_name']} ({op['agent_type']}): cost={op['cost_estimate']}")
        
        print("\n[2] Testing architecture_templates table...")
        templates = await conn.fetch("SELECT name, complexity_range_min, complexity_range_max, agent_sequence FROM architecture_templates")
        print(f"   Found {len(templates)} templates:")
        for t in templates:
            print(f"   - {t['name']}: complexity [{t['complexity_range_min']}, {t['complexity_range_max']}]")
            print(f"     Agents: {t['agent_sequence']}")
        
        print("\n[3] Testing TaskAnalyzer...")
        from backend.services.maas.scheduler import TaskAnalyzer
        
        analyzer = TaskAnalyzer()
        
        test_tasks = [
            "长沙房价多少",
            "请分析长沙岳麓区的房价走势并给出投资建议",
            "生成一份完整的长沙学区房投资分析报告"
        ]
        
        for task in test_tasks:
            feature = analyzer.analyze(task)
            print(f"   Task: {task[:30]}...")
            print(f"   - Type: {feature.task_type}")
            print(f"   - Keywords: {feature.keywords}")
            print()
        
        print("[4] Testing ComplexityEstimator...")
        from backend.services.maas.scheduler import ComplexityEstimator
        
        estimator = ComplexityEstimator()
        
        for task in test_tasks:
            feature = analyzer.analyze(task)
            complexity = estimator.estimate(feature)
            print(f"   Task: {task[:30]}...")
            print(f"   - Complexity: {complexity}")
            print()
        
        print("[5] Testing scheduling_decisions table...")
        decision_id = str(uuid.uuid4())
        test_user_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO scheduling_decisions 
            (id, user_id, task_content, task_type, complexity_score, selected_architecture_name, success)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, decision_id, test_user_id, "测试任务", "analysis", 0.5, "standard_analysis", True)
        print(f"   Created test decision: {decision_id}")
        
        print("\n[6] Testing architecture selection...")
        for complexity in [0.2, 0.5, 0.8]:
            matching = await conn.fetch("""
                SELECT name FROM architecture_templates 
                WHERE complexity_range_min <= $1 AND complexity_range_max >= $1
            """, complexity)
            print(f"   Complexity {complexity}: {[m['name'] for m in matching]}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_maas())
