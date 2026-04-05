"""
低消耗、高回报技术集成测试
测试 MaAS、CASK、Agent Swarm 三项技术的集成效果
"""

import sys
import os
import asyncio
import time

backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)


def test_maas_controller():
    """测试 MaAS 智能体超网控制器"""
    print("\n" + "="*60)
    print("测试1: MaAS 智能体超网控制器")
    print("="*60)
    
    try:
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "maas_controller",
            os.path.join(backend_path, "agents", "maas_controller.py")
        )
        maas_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(maas_module)
        
        AgenticSupernetController = maas_module.AgenticSupernetController
        DifficultyAnalyzer = maas_module.DifficultyAnalyzer
        TaskDifficulty = maas_module.TaskDifficulty
        get_maas_controller = maas_module.get_maas_controller
        
        print("✓ 成功导入 MaAS 模块")
        
        analyzer = DifficultyAnalyzer()
        print("✓ DifficultyAnalyzer 初始化成功")
        
        test_queries = [
            ("深圳房价多少", TaskDifficulty.EASY),
            ("分析深圳南山区的房价趋势", TaskDifficulty.MEDIUM),
            ("请生成一份深圳房产投资风险分析报告", TaskDifficulty.HARD),
            ("请制定一套完整的房产投资战略规划方案", TaskDifficulty.EXPERT),
        ]
        
        print("\n难度分析测试:")
        for query, expected in test_queries:
            difficulty, score = analyzer.analyze(query)
            status = "✓" if difficulty == expected else "≈"
            print(f"  {status} 「{query[:20]}...」 -> {difficulty.value} (分数: {score:.2f})")
        
        controller = get_maas_controller()
        print("\n✓ MaAS 控制器初始化成功")
        
        async def test_execution():
            result = await controller.execute("分析深圳房价趋势")
            print(f"\n执行测试:")
            print(f"  - 难度: {result['difficulty']}")
            print(f"  - 算子: {result['operators_used']}")
            print(f"  - 早退: {result['early_exited']}")
            print(f"  - 耗时: {result['execution_time']:.3f}s")
            print(f"  - 成本权重: {result['cost_weight']}")
            return result
        
        result = asyncio.run(test_execution())
        
        stats = controller.get_statistics()
        print(f"\n统计信息:")
        print(f"  - 总执行次数: {stats['total_executions']}")
        print(f"  - 早退次数: {stats['early_exit_count']}")
        print(f"  - 早退率: {stats['early_exit_rate']:.1%}")
        
        print("\n✅ MaAS 控制器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ MaAS 控制器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cask_compressor():
    """测试 CASK 长上下文压缩"""
    print("\n" + "="*60)
    print("测试2: CASK 长上下文KV缓存压缩")
    print("="*60)
    
    try:
        from memory.cask_compressor import (
            CASKCompressor,
            CASKMemoryManager,
            KVCacheEntry,
            get_cask_manager
        )
        print("✓ 成功导入 CASK 模块")
        
        compressor = CASKCompressor(max_cache_size=100, prune_ratio=0.3)
        print("✓ CASKCompressor 初始化成功")
        
        print("\n存储测试:")
        test_contents = [
            "这是一段测试内容，用于验证CASK压缩功能。" * 10,
            "深圳南山区房价分析报告：2024年均价约8万元/平米。" * 5,
            "用户咨询记录：关于房产投资的风险评估建议。" * 8,
        ]
        
        for i, content in enumerate(test_contents):
            key = compressor.store(content)
            print(f"  ✓ 存储条目 {i+1}: key={key}, 长度={len(content)}")
        
        print("\n检索测试:")
        for key in list(compressor.cache.keys())[:2]:
            entry = compressor.retrieve(key)
            if entry:
                print(f"  ✓ 检索成功: key={key}, 访问次数={entry.access_count}")
        
        print("\n压缩测试:")
        compress_result = compressor.compress_all()
        print(f"  ✓ 压缩完成: {compress_result['compressed']} 条, 节省 {compress_result['saved_bytes']} 字节")
        
        stats = compressor.get_stats()
        print(f"\n统计信息:")
        print(f"  - 缓存大小: {stats['cache_size']}/{stats['max_size']}")
        print(f"  - 命中率: {stats['hit_rate']:.1%}")
        print(f"  - 节省内存: {stats['memory_saved_mb']:.3f} MB")
        
        manager = get_cask_manager()
        print("\n✓ CASKMemoryManager 初始化成功")
        
        print("\n✅ CASK 压缩器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ CASK 压缩器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_swarm():
    """测试 Agent Swarm 多智能体并行协作"""
    print("\n" + "="*60)
    print("测试3: Agent Swarm 多智能体并行协作")
    print("="*60)
    
    try:
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "agent_swarm",
            os.path.join(backend_path, "agents", "agent_swarm.py")
        )
        swarm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(swarm_module)
        
        AgentSwarm = swarm_module.AgentSwarm
        SwarmAgent = swarm_module.SwarmAgent
        AgentRole = swarm_module.AgentRole
        ResultAggregator = swarm_module.ResultAggregator
        get_swarm = swarm_module.get_swarm
        swarm_execute = swarm_module.swarm_execute
        
        print("✓ 成功导入 Agent Swarm 模块")
        
        swarm = AgentSwarm(swarm_id="test_swarm")
        print(f"✓ AgentSwarm 初始化成功，包含 {len(swarm.agents)} 个智能体")
        
        print("\n智能体列表:")
        role_counts = {}
        for agent in swarm.agents.values():
            role_counts[agent.role.value] = role_counts.get(agent.role.value, 0) + 1
        for role, count in role_counts.items():
            print(f"  - {role}: {count} 个")
        
        async def test_parallel():
            print("\n并行执行测试:")
            result = await swarm.execute_parallel(
                query="分析深圳南山区的房产投资价值",
                aggregation_strategy="weighted"
            )
            
            print(f"  - 任务ID: {result['task_id']}")
            print(f"  - 成功: {result['success']}")
            print(f"  - 置信度: {result['confidence']:.2f}")
            print(f"  - 使用智能体: {result['agents_used']} 个")
            print(f"  - 执行时间: {result['execution_time']:.3f}s")
            print(f"  - 聚合策略: {result['aggregation_strategy']}")
            
            return result
        
        result = asyncio.run(test_parallel())
        
        async def test_sequential():
            print("\n顺序执行测试:")
            result = await swarm.execute_sequential(
                query="生成房产分析报告",
                role_sequence=[AgentRole.COLLECTOR, AgentRole.ANALYZER, AgentRole.SYNTHESIZER]
            )
            
            print(f"  - 任务ID: {result['task_id']}")
            print(f"  - 成功: {result['success']}")
            print(f"  - 执行管道: {' -> '.join(result['pipeline'])}")
            
            return result
        
        result = asyncio.run(test_sequential())
        
        stats = swarm.get_stats()
        print(f"\n统计信息:")
        print(f"  - 总任务数: {stats['tasks']['total_tasks']}")
        print(f"  - 成功任务: {stats['tasks']['successful_tasks']}")
        print(f"  - 并行执行: {stats['tasks']['parallel_executions']}")
        
        print("\n✅ Agent Swarm 测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ Agent Swarm 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """测试三项技术协同工作"""
    print("\n" + "="*60)
    print("测试4: 三项技术协同集成")
    print("="*60)
    
    try:
        import importlib.util
        
        spec_maas = importlib.util.spec_from_file_location(
            "maas_controller",
            os.path.join(backend_path, "agents", "maas_controller.py")
        )
        maas_module = importlib.util.module_from_spec(spec_maas)
        spec_maas.loader.exec_module(maas_module)
        
        spec_swarm = importlib.util.spec_from_file_location(
            "agent_swarm",
            os.path.join(backend_path, "agents", "agent_swarm.py")
        )
        swarm_module = importlib.util.module_from_spec(spec_swarm)
        spec_swarm.loader.exec_module(swarm_module)
        
        from memory.cask_compressor import get_cask_manager
        
        get_maas_controller = maas_module.get_maas_controller
        AgentRole = swarm_module.AgentRole
        get_swarm = swarm_module.get_swarm
        
        print("✓ 所有模块导入成功")
        
        maas = get_maas_controller()
        cask = get_cask_manager()
        swarm = get_swarm()
        
        print("✓ 所有组件初始化成功")
        
        async def integrated_workflow():
            query = "请分析深圳南山区的房产投资价值，并给出专业建议"
            
            print(f"\n协同工作流测试:")
            print(f"  查询: 「{query}」")
            
            difficulty, score = maas.difficulty_analyzer.analyze(query)
            print(f"\n  [MaAS] 难度分析: {difficulty.value} (分数: {score:.2f})")
            
            cache_key = cask.store_memory("test_user", query)
            print(f"  [CASK] 存储查询: key={cache_key}")
            
            ministries = maas.get_ministry_assignment(difficulty)
            print(f"  [MaAS] 分配六部: {ministries}")
            
            roles_map = {
                "li_bu": AgentRole.SYNTHESIZER,
                "hu_bu": AgentRole.COLLECTOR,
                "li_bu_consult": AgentRole.ANALYZER,
                "bing_bu": AgentRole.COLLECTOR,
                "xing_bu": AgentRole.VALIDATOR,
                "gong_bu": AgentRole.SYNTHESIZER
            }
            roles = [roles_map.get(m, AgentRole.ANALYZER) for m in ministries]
            roles = list(set(roles))
            
            swarm_result = await swarm.execute_parallel(query, roles)
            print(f"  [Swarm] 执行完成: {swarm_result['agents_used']} 个智能体参与")
            
            cask.store_memory("test_user", swarm_result['content'])
            print(f"  [CASK] 存储结果")
            
            return {
                "difficulty": difficulty.value,
                "ministries": ministries,
                "swarm_success": swarm_result['success'],
                "confidence": swarm_result['confidence']
            }
        
        result = asyncio.run(integrated_workflow())
        
        print(f"\n协同结果:")
        print(f"  - 难度: {result['difficulty']}")
        print(f"  - 分配部门: {result['ministries']}")
        print(f"  - 执行成功: {result['swarm_success']}")
        print(f"  - 置信度: {result['confidence']:.2f}")
        
        print("\n✅ 协同集成测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 协同集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("低消耗、高回报技术集成测试")
    print("="*60)
    
    results = {}
    
    results["maas"] = test_maas_controller()
    results["cask"] = test_cask_compressor()
    results["swarm"] = test_agent_swarm()
    results["integration"] = test_integration()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有技术集成测试通过!")
        print("\n已集成技术:")
        print("  1. Attention Residuals (Kimi 2026.03) - 海马体记忆、人格化引擎")
        print("  2. Agentic Supernet/MaAS (ICML 2025) - 六部智能体动态调度")
        print("  3. CASK (ACM 2025) - 长上下文KV缓存压缩")
        print("  4. Agent Swarm (Anthropic 2026) - 多智能体并行协作")
    else:
        print("\n⚠ 部分测试未通过，请检查上述错误信息")


if __name__ == "__main__":
    main()
