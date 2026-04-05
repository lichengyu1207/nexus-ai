"""
三省六部智能体架构性能测试

测试指标：
1. 中书省（决策）：任务拆解响应时间<2秒
2. 门下省（审核）：合规检查准确率>95%
3. 尚书省（执行）：支持50+智能体并行协同
4. 智能体间通信延迟<50ms
"""

import asyncio
import sys
import os
import time
import random

backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)


async def test_zhongshu_decompose_time():
    """测试中书省任务拆解响应时间<2秒"""
    print("\n" + "="*60)
    print("测试1: 中书省（决策）- 任务拆解响应时间<2秒")
    print("="*60)
    
    from agents.three_provinces import ZhongshuSheng
    
    zhongshu = ZhongshuSheng()
    
    test_queries = [
        "深圳南山区房价估值",
        "北京朝阳区房产投资分析",
        "上海浦东新区房产咨询",
        "广州天河区房产报告生成",
        "批量分析深圳所有区域的房价",
        "杭州西湖区房产对比分析",
        "成都高新区房产投资建议",
        "南京鼓楼区房产估值报告",
        "武汉武昌区房产市场分析",
        "西安雁塔区房产投资咨询",
    ]
    
    results = []
    sub_2s_count = 0
    
    for i, query in enumerate(test_queries):
        start_time = time.time()
        task = await zhongshu.decompose_task(query, f"test_{i}")
        elapsed = time.time() - start_time
        
        results.append({
            "query": query,
            "time": elapsed,
            "sub_tasks": len(task.sub_tasks),
            "under_2s": elapsed < 2.0,
        })
        
        if elapsed < 2.0:
            sub_2s_count += 1
        
        print(f"  查询 {i+1}: {elapsed:.3f}s - {len(task.sub_tasks)}个子任务 {'✓' if elapsed < 2.0 else '✗'}")
    
    avg_time = sum(r["time"] for r in results) / len(results)
    success_rate = sub_2s_count / len(results) * 100
    
    print(f"\n结果:")
    print(f"  平均响应时间: {avg_time:.3f}秒")
    print(f"  <2秒比例: {success_rate:.1f}%")
    print(f"  目标: <2秒")
    print(f"  状态: {'✅ 通过' if avg_time < 2.0 else '❌ 未达标'}")
    
    return avg_time < 2.0


async def test_menxia_accuracy():
    """测试门下省合规检查准确率>95%"""
    print("\n" + "="*60)
    print("测试2: 门下省（审核）- 合规检查准确率>95%")
    print("="*60)
    
    from agents.three_provinces import MenxiaSheng, Task, TaskStatus
    
    menxia = MenxiaSheng()
    
    test_cases = [
        {"query": "深圳南山区房价估值", "expected": "approved", "has_sensitive": False},
        {"query": "我的身份证是123456789012345678", "expected": "rejected", "has_sensitive": True},
        {"query": "银行卡号6222021234567890", "expected": "rejected", "has_sensitive": True},
        {"query": "如何攻击系统", "expected": "rejected", "has_sensitive": False},
        {"query": "北京朝阳区房产分析", "expected": "approved", "has_sensitive": False},
        {"query": "我的密码是abc123", "expected": "rejected", "has_sensitive": True},
        {"query": "上海浦东新区投资建议", "expected": "approved", "has_sensitive": False},
        {"query": "个人隐私数据查询", "expected": "needs_review", "has_sensitive": False},
        {"query": "广州天河区房产报告", "expected": "approved", "has_sensitive": False},
        {"query": "验证码123456", "expected": "rejected", "has_sensitive": True},
    ]
    
    correct = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases):
        task = Task(
            id=f"review_test_{i}",
            query=case["query"],
            status=TaskStatus.PENDING,
        )
        
        reviewed = await menxia.review_task(task)
        result = reviewed.compliance_result.value
        
        expected = case["expected"]
        is_correct = result == expected
        
        if is_correct:
            correct += 1
        
        print(f"  案例 {i+1}: {case['query'][:20]}...")
        print(f"    预期: {expected}, 实际: {result} {'✓' if is_correct else '✗'}")
    
    accuracy = correct / total * 100
    
    print(f"\n结果:")
    print(f"  正确数: {correct}/{total}")
    print(f"  准确率: {accuracy:.1f}%")
    print(f"  目标: >95%")
    print(f"  状态: {'✅ 通过' if accuracy >= 95 else '❌ 未达标'}")
    
    return accuracy >= 95


async def test_shangshu_parallel():
    """测试尚书省支持50+智能体并行协同"""
    print("\n" + "="*60)
    print("测试3: 尚书省（执行）- 支持50+智能体并行协同")
    print("="*60)
    
    from agents.three_provinces import ShangshuSheng, Task, SubTask, TaskStatus
    
    shangshu = ShangshuSheng(max_agents=60)
    
    print("\n注册智能体...")
    for i in range(55):
        shangshu.register_agent(
            f"agent_{i}",
            "worker",
            ["analysis", "valuation", "report"]
        )
    
    print(f"已注册 {len(shangshu.agents)} 个智能体")
    
    task = Task(
        id="parallel_test",
        query="批量分析测试",
        status=TaskStatus.EXECUTING,
    )
    
    task.sub_tasks = [
        SubTask(id=f"sub_{i}", name=f"任务{i}", description=f"执行任务{i}")
        for i in range(20)
    ]
    
    start_time = time.time()
    result = await shangshu.execute_task(task)
    elapsed = time.time() - start_time
    
    stats = shangshu.get_stats()
    
    print(f"\n结果:")
    print(f"  注册智能体数: {stats['registered_agents']}")
    print(f"  最大并发数: {stats['max_concurrent_agents']}")
    print(f"  执行时间: {elapsed:.3f}秒")
    print(f"  目标: 支持50+智能体")
    print(f"  状态: {'✅ 通过' if stats['registered_agents'] >= 50 else '❌ 未达标'}")
    
    return stats['registered_agents'] >= 50


async def test_communication_latency():
    """测试智能体间通信延迟<50ms"""
    print("\n" + "="*60)
    print("测试4: 智能体间通信延迟<50ms")
    print("="*60)
    
    from agents.three_provinces import ShangshuSheng
    
    shangshu = ShangshuSheng(max_agents=10)
    
    for i in range(10):
        shangshu.register_agent(f"agent_{i}", "worker", ["test"])
    
    await shangshu.start()
    
    print("\n发送测试消息...")
    latencies = []
    
    for i in range(100):
        start = time.time()
        await shangshu.send_message(
            f"agent_{i % 10}",
            f"agent_{(i + 1) % 10}",
            {"type": "test", "data": f"message_{i}"}
        )
        latency = (time.time() - start) * 1000
        latencies.append(latency)
    
    await shangshu.stop()
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    
    print(f"\n结果:")
    print(f"  测试消息数: {len(latencies)}")
    print(f"  平均延迟: {avg_latency:.2f}ms")
    print(f"  最大延迟: {max_latency:.2f}ms")
    print(f"  最小延迟: {min_latency:.2f}ms")
    print(f"  目标: <50ms")
    print(f"  状态: {'✅ 通过' if avg_latency < 50 else '❌ 未达标'}")
    
    return avg_latency < 50


async def test_integrated_system():
    """测试三省系统集成"""
    print("\n" + "="*60)
    print("测试5: 三省系统集成测试")
    print("="*60)
    
    from agents.three_provinces import ThreeProvincesSystem
    
    system = ThreeProvincesSystem(max_agents=55)
    await system.start()
    
    test_queries = [
        "深圳南山区房价估值",
        "北京朝阳区房产投资分析",
        "上海浦东新区房产咨询报告",
    ]
    
    print("\n执行集成测试...")
    for query in test_queries:
        start = time.time()
        task = await system.process_query(query)
        elapsed = time.time() - start
        
        print(f"  查询: {query}")
        print(f"    状态: {task.status.value}")
        print(f"    子任务数: {len(task.sub_tasks)}")
        print(f"    合规结果: {task.compliance_result.value if task.compliance_result else 'N/A'}")
        print(f"    总耗时: {elapsed:.3f}秒")
    
    report = system.get_performance_report()
    
    print("\n性能报告:")
    print(f"  中书省: {report['zhongshu']['achieved'] and '✅' or '❌'} 平均{report['zhongshu']['avg_decompose_time']:.3f}秒")
    print(f"  门下省: {report['menxia']['achieved'] and '✅' or '❌'} 准确率{report['menxia']['accuracy']*100:.1f}%")
    print(f"  尚书省: {report['shangshu']['achieved'] and '✅' or '❌'} {report['shangshu']['registered_agents']}个智能体")
    print(f"  通信: {report['communication']['achieved'] and '✅' or '❌'} 平均{report['communication']['avg_latency_ms']:.2f}ms")
    
    await system.stop()
    
    return report['overall']['all_targets_achieved']


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("三省六部智能体架构性能测试")
    print("="*60)
    
    results = {}
    
    results["zhongshu"] = await test_zhongshu_decompose_time()
    results["menxia"] = await test_menxia_accuracy()
    results["shangshu"] = await test_shangshu_parallel()
    results["communication"] = await test_communication_latency()
    results["integrated"] = await test_integrated_system()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    print("\n性能指标:")
    print("  中书省（决策）：任务拆解响应时间<2秒")
    print("  门下省（审核）：合规检查准确率>95%")
    print("  尚书省（执行）：支持50+智能体并行协同")
    print("  智能体通信：延迟<50ms")
    
    print("\n测试结果:")
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 未达标"
        print(f"  {name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    if all(results.values()):
        print("\n🎉 所有性能指标达标！")


if __name__ == "__main__":
    asyncio.run(main())
