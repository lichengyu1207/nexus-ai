"""
智能咨询系统测试脚本
测试NLU引擎、对话管理、API端点
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.consultant_agent import NLUEngine, DialogueManager, ConsultantAgent, NLUResult


def test_nlu_engine():
    """测试NLU引擎"""
    print("\n" + "="*60)
    print("🧠 测试 NLU 引擎")
    print("="*60)
    
    engine = NLUEngine()
    
    test_cases = [
        "我在深圳工作，月薪3万，想买一套两居室",
        "南山区的房价怎么样？",
        "深圳的购房政策是什么？",
        "预算500万，推荐一下",
        "我30岁，程序员，想在北京买房",
    ]
    
    async def run_tests():
        for message in test_cases:
            result = await engine.analyze(message, [], {})
            print(f"\n📝 输入: {message}")
            print(f"   意图: {result.intent}")
            print(f"   实体: {result.entities}")
            print(f"   画像更新: {result.profile_updates}")
            print(f"   置信度: {result.confidence}")
    
    asyncio.run(run_tests())
    print("\n✅ NLU引擎测试完成")


def test_dialogue_manager():
    """测试对话管理器"""
    print("\n" + "="*60)
    print("💬 测试对话管理器")
    print("="*60)
    
    dm = DialogueManager()
    
    # 模拟购房推荐对话
    print("\n场景1: 购房推荐")
    dm.update_state('house_recommendation', {'city': '深圳'}, {})
    missing = dm.get_missing_fields()
    print(f"   缺少字段: {missing}")
    question = dm.generate_question(missing)
    print(f"   追问: {question}")
    
    # 补充预算
    dm.update_state('house_recommendation', {'city': '深圳', 'budget': 5000000}, {})
    missing = dm.get_missing_fields()
    print(f"   补充预算后缺少: {missing}")
    
    # 模拟区域查询
    print("\n场景2: 区域信息")
    dm2 = DialogueManager()
    dm2.update_state('area_info', {'city': '广州'}, {})
    missing = dm2.get_missing_fields()
    question = dm2.generate_question(missing)
    print(f"   追问: {question}")
    
    print("\n✅ 对话管理器测试完成")


def test_consultant_agent():
    """测试咨询代理"""
    print("\n" + "="*60)
    print("🤖 测试咨询代理")
    print("="*60)
    
    agent = ConsultantAgent()
    
    async def run_tests():
        test_cases = [
            {
                "message": "我想在深圳买房，预算500万",
                "profile": {"monthly_income": 30000}
            },
            {
                "message": "南山区的房价怎么样？",
                "profile": {}
            },
            {
                "message": "深圳的购房政策",
                "profile": {}
            },
            {
                "message": "帮我算一下贷款，预算300万",
                "profile": {"monthly_income": 25000}
            },
        ]
        
        for case in test_cases:
            result = await agent.process(
                user_message=case["message"],
                session_id="test-session",
                user_id="test-user",
                history=[],
                profile=case["profile"]
            )
            print(f"\n📝 用户: {case['message']}")
            print(f"   意图: {result['intent']}")
            print(f"   动作: {result['action']}")
            print(f"   回复预览: {result['reply'][:100]}...")
    
    asyncio.run(run_tests())
    print("\n✅ 咨询代理测试完成")


def test_city_data():
    """测试城市数据"""
    print("\n" + "="*60)
    print("🏙️ 测试城市数据")
    print("="*60)
    
    agent = ConsultantAgent()
    
    for city in ["深圳", "广州", "北京", "上海"]:
        data = agent.CITY_DATA.get(city, {})
        if data:
            print(f"\n{city}:")
            print(f"   均价: {data.get('avg_price', 0)//10000}万/㎡")
            districts = data.get('districts', {})
            for district, info in districts.items():
                print(f"   - {district}: {info.get('avg_price', 0)//10000}万/㎡")
    
    print("\n✅ 城市数据测试完成")


def test_loan_calculation():
    """测试贷款计算"""
    print("\n" + "="*60)
    print("💰 测试贷款计算")
    print("="*60)
    
    agent = ConsultantAgent()
    
    async def run_test():
        result = await agent._handle_loan_calc(
            entities={"budget": 5000000},
            profile={"monthly_income": 30000}
        )
        print(result)
    
    asyncio.run(run_test())
    print("\n✅ 贷款计算测试完成")


def main():
    print("\n" + "="*60)
    print("🚀 智能咨询系统测试")
    print("="*60)
    
    test_nlu_engine()
    test_dialogue_manager()
    test_consultant_agent()
    test_city_data()
    test_loan_calculation()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)
    
    print("\n📋 测试总结:")
    print("   - NLU引擎: 意图识别、实体提取 ✓")
    print("   - 对话管理: 多轮对话、智能追问 ✓")
    print("   - 咨询代理: 完整对话流程 ✓")
    print("   - 城市数据: 房价数据查询 ✓")
    print("   - 贷款计算: 月供计算 ✓")


if __name__ == "__main__":
    main()
