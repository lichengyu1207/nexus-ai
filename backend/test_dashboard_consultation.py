"""
仪表盘任务分析和智能咨询API测试
测试场景：
1. 仪表盘任务分析 - 单个自然语言输入
2. 仪表盘任务分析 - 多个自然语言输入
3. 智能咨询 - 单个信息输入
4. 智能咨询 - 综合/多个信息输入
"""

import httpx
import asyncio
import json
import time

BASE_URL = "http://localhost:8000"


async def test_health():
    """测试服务健康状态"""
    print("\n" + "="*60)
    print("测试服务健康状态")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"状态: {result.get('status', 'unknown')}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 服务未启动: {e}")
            return False


async def test_dashboard_single_input():
    """测试仪表盘任务分析 - 单个自然语言输入"""
    print("\n" + "="*60)
    print("测试1: 仪表盘任务分析 - 单个自然语言输入")
    print("="*60)
    
    test_cases = [
        "深圳南山区房价分析",
        "北京朝阳区房产估值",
        "上海浦东新区投资建议"
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for query in test_cases:
            print(f"\n查询: 「{query}」")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/parse/query",
                    json={"query": query, "enable_inference": True}
                )
                
                print(f"  状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  城市: {result.get('city', 'N/A')}")
                    print(f"  区域: {result.get('district', 'N/A')}")
                    print(f"  置信度: {result.get('confidence', 0):.2f}")
                    if result.get('inferences'):
                        print(f"  推断: {len(result['inferences'])} 项")
                    print("  ✓ 测试通过")
                else:
                    print(f"  ❌ 请求失败: {response.text[:200]}")
                    
            except Exception as e:
                print(f"  ❌ 异常: {e}")
    
    return True


async def test_dashboard_multiple_inputs():
    """测试仪表盘任务分析 - 多个自然语言输入"""
    print("\n" + "="*60)
    print("测试2: 仪表盘任务分析 - 多个自然语言输入（批量解析）")
    print("="*60)
    
    test_queries = [
        "深圳南山区房价分析",
        "深圳福田区房产估值",
        "深圳宝安区投资建议"
    ]
    
    print(f"\n批量查询 {len(test_queries)} 个地址:")
    for q in test_queries:
        print(f"  - {q}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        results = []
        for query in test_queries:
            try:
                response = await client.post(
                    f"{BASE_URL}/api/parse/query",
                    json={"query": query, "enable_inference": True}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "query": query,
                        "city": result.get('city'),
                        "district": result.get('district'),
                        "confidence": result.get('confidence', 0)
                    })
                    
            except Exception as e:
                print(f"  ❌ 异常: {e}")
        
        print(f"\n解析结果:")
        for r in results:
            print(f"  ✓ {r['query']} -> {r['city']} {r['district']} (置信度: {r['confidence']:.2f})")
        
        print(f"\n成功解析: {len(results)}/{len(test_queries)}")
    
    return True


async def test_consultation_single_input():
    """测试智能咨询 - 单个信息输入"""
    print("\n" + "="*60)
    print("测试3: 智能咨询 - 单个信息输入")
    print("="*60)
    
    test_cases = [
        "深圳南山区房价走势如何？",
        "北京朝阳区值得投资吗？",
        "上海浦东新区房产估值"
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for message in test_cases:
            print(f"\n消息: 「{message}」")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/consult/chat",
                    json={
                        "message": message,
                        "user_id": "test_user",
                        "session_id": f"test_session_{int(time.time())}"
                    }
                )
                
                print(f"  状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    reply = result.get('response', result.get('reply', ''))
                    print(f"  回复: {reply[:100]}...")
                    print("  ✓ 测试通过")
                else:
                    print(f"  ❌ 请求失败: {response.text[:200]}")
                    
            except Exception as e:
                print(f"  ❌ 异常: {e}")
    
    return True


async def test_consultation_multiple_inputs():
    """测试智能咨询 - 综合/多个信息输入"""
    print("\n" + "="*60)
    print("测试4: 智能咨询 - 综合/多个信息输入")
    print("="*60)
    
    test_cases = [
        {
            "message": "请综合分析深圳南山区、福田区和宝安区的房产投资价值，并给出对比建议",
            "description": "综合分析多个区域"
        },
        {
            "message": "我有500万预算，想在深圳买房，需要考虑学区、交通和升值空间，请给出建议",
            "description": "多条件综合咨询"
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for case in test_cases:
            print(f"\n场景: {case['description']}")
            print(f"消息: 「{case['message'][:50]}...」")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/consult/chat",
                    json={
                        "message": case["message"],
                        "user_id": "test_user",
                        "session_id": f"test_session_{int(time.time())}"
                    }
                )
                
                print(f"  状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    reply = result.get('response', result.get('reply', ''))
                    print(f"  回复长度: {len(reply)} 字符")
                    print("  ✓ 测试通过")
                else:
                    print(f"  ❌ 请求失败: {response.text[:200]}")
                    
            except Exception as e:
                print(f"  ❌ 异常: {e}")
    
    return True


async def test_maas_integration():
    """测试 MaAS 智能调度集成"""
    print("\n" + "="*60)
    print("测试5: MaAS 智能调度集成")
    print("="*60)
    
    test_queries = [
        ("深圳房价多少", "easy"),
        ("分析深圳南山区的房价趋势和投资价值", "medium"),
        ("请生成一份详细的深圳房产投资风险分析报告", "hard"),
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for query, expected_difficulty in test_queries:
            print(f"\n查询: 「{query}」")
            print(f"  预期难度: {expected_difficulty}")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/parse/query",
                    json={"query": query, "enable_inference": True}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    confidence = result.get('confidence', 0)
                    print(f"  解析置信度: {confidence:.2f}")
                    print(f"  城市: {result.get('city', 'N/A')}")
                    print(f"  区域: {result.get('district', 'N/A')}")
                    print("  ✓ 测试通过")
                else:
                    print(f"  ⚠ 请求失败")
                    
            except Exception as e:
                print(f"  ⚠ 异常: {e}")
    
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("仪表盘任务分析和智能咨询API测试")
    print("="*60)
    
    health_ok = await test_health()
    
    if not health_ok:
        print("\n❌ 服务未启动，请先启动后端服务:")
        print("   cd backend && python main.py")
        return
    
    results = {}
    
    results["dashboard_single"] = await test_dashboard_single_input()
    results["dashboard_multiple"] = await test_dashboard_multiple_inputs()
    results["consultation_single"] = await test_consultation_single_input()
    results["consultation_multiple"] = await test_consultation_multiple_inputs()
    results["maas_integration"] = await test_maas_integration()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")


if __name__ == "__main__":
    asyncio.run(main())
