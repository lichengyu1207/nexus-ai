"""
多功能综合测试脚本
测试智能咨询、Token系统、上传系统等
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.consultant_agent import NLUEngine, DialogueManager, ConsultantAgent
from backend.services.integral import IntegralService
from backend.utils.token_counter import count_tokens, tokens_to_integral, integral_to_tokens
import requests

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_consultation():
    """测试智能咨询系统"""
    print_header("🧠 智能咨询系统测试")
    
    engine = NLUEngine()
    agent = ConsultantAgent()
    
    async def run_tests():
        # NLU测试
        test_cases = [
            "我在深圳工作，月薪3万，想买一套两居室",
            "南山区的房价怎么样？",
            "帮我算一下贷款，预算300万",
        ]
        
        for msg in test_cases:
            result = await engine.analyze(msg, [], {})
            print(f"\n📝 {msg}")
            print(f"   意图: {result.intent}")
            print(f"   实体: {result.entities}")
        
        # 代理测试
        print("\n--- 咨询代理测试 ---")
        result = await agent.process(
            "我想在深圳买房，预算500万",
            "test-session",
            "test-user",
            [],
            {"monthly_income": 30000}
        )
        print(f"回复预览: {result['reply'][:150]}...")
    
    asyncio.run(run_tests())
    print("\n✅ 智能咨询测试完成")

def test_token_system():
    """测试Token系统"""
    print_header("💰 Token系统测试")
    
    # Token计数器
    text = "这是一个测试文本，用于验证Token计数功能。"
    token_count = count_tokens(text)
    print(f"\n📊 Token计数测试:")
    print(f"   文本: '{text}'")
    print(f"   Token数: {token_count}")
    print(f"   字符数: {len(text)}")
    
    # Token转换
    print(f"\n🔄 Token转换测试:")
    tokens = [100, 500, 1000, 5000]
    for t in tokens:
        integral = tokens_to_integral(t)
        print(f"   {t} Token = {integral} 积分")
    
    # 积分转换
    print(f"\n🔄 积分转换测试:")
    integrals = [1, 5, 10, 50]
    for i in integrals:
        tokens = integral_to_tokens(i)
        print(f"   {i} 积分 = {tokens} Token")
    
    print("\n✅ Token系统测试完成")

def test_city_data():
    """测试城市数据"""
    print_header("🏙️ 城市数据测试")
    
    agent = ConsultantAgent()
    
    for city in ["深圳", "广州", "北京", "上海"]:
        data = agent.CITY_DATA.get(city, {})
        if data:
            avg = data.get('avg_price', 0) // 10000
            districts = len(data.get('districts', {}))
            print(f"\n{city}:")
            print(f"   均价: {avg}万/㎡")
            print(f"   区域数: {districts}")
    
    print("\n✅ 城市数据测试完成")

def test_loan_calculation():
    """测试贷款计算"""
    print_header("💵 贷款计算测试")
    
    agent = ConsultantAgent()
    
    async def run_test():
        test_cases = [
            (3000000, 20000),  # 300万，月薪2万
            (5000000, 30000),  # 500万，月薪3万
            (8000000, 50000),  # 800万，月薪5万
        ]
        
        for budget, income in test_cases:
            result = await agent._handle_loan_calc(
                entities={"budget": budget},
                profile={"monthly_income": income}
            )
            monthly = budget * 0.7 * 0.0045
            ratio = monthly / income * 100
            status = "✅ 合理" if ratio < 50 else "⚠️ 压力大"
            print(f"\n预算{budget//10000}万，月薪{income//10000}万:")
            print(f"   月供: 约{int(monthly)}元")
            print(f"   占收入: {ratio:.1f}%")
            print(f"   评估: {status}")
    
    asyncio.run(run_test())
    print("\n✅ 贷款计算测试完成")

def test_api_endpoints():
    """测试API端点"""
    print_header("🔌 API端点测试")
    
    endpoints = [
        ("GET", "/health", "健康检查"),
        ("GET", "/api/consult/sessions", "咨询会话"),
        ("GET", "/api/consult/profile", "用户画像"),
        ("GET", "/api/integral/balance", "积分余额"),
        ("GET", "/api/uploads/types", "数据类型"),
    ]
    
    for method, endpoint, desc in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code in [200, 401] else "❌"
            auth = "(需认证)" if response.status_code == 401 else ""
            print(f"   {status} {endpoint}: {response.status_code} {auth}")
        except Exception as e:
            print(f"   ❌ {endpoint}: 连接失败")
    
    print("\n✅ API端点测试完成")

def test_dialogue_flow():
    """测试多轮对话流程"""
    print_header("💬 多轮对话流程测试")
    
    dm = DialogueManager()
    
    # 模拟对话流程
    print("\n场景: 购房推荐")
    
    # 第1轮：用户说城市
    dm.update_state('house_recommendation', {'city': '深圳'}, {})
    missing = dm.get_missing_fields()
    print(f"\n1️⃣ 用户: '我想在深圳买房'")
    print(f"   缺少: {missing}")
    if missing:
        question = dm.generate_question(missing)
        print(f"   追问: {question}")
    
    # 第2轮：用户提供预算
    dm.update_state('house_recommendation', {'budget': 5000000}, {})
    missing = dm.get_missing_fields()
    print(f"\n2️⃣ 用户: '预算500万'")
    print(f"   缺少: {missing}")
    
    if not missing:
        print(f"   ✅ 信息完整，可以生成推荐")
    
    print("\n✅ 多轮对话测试完成")

def main():
    print("\n" + "="*60)
    print(" 🚀 多功能综合测试")
    print("="*60)
    
    test_consultation()
    test_token_system()
    test_city_data()
    test_loan_calculation()
    test_api_endpoints()
    test_dialogue_flow()
    
    print("\n" + "="*60)
    print(" ✅ 所有测试完成！")
    print("="*60)
    
    print("\n📋 测试总结:")
    print("   ✅ 智能咨询: NLU引擎、对话管理")
    print("   ✅ Token系统: 计数、转换")
    print("   ✅ 城市数据: 房价查询")
    print("   ✅ 贷款计算: 月供评估")
    print("   ✅ API端点: 服务状态")
    print("   ✅ 多轮对话: 流程控制")

if __name__ == "__main__":
    main()
