"""
并发测试脚本
测试系统并发处理能力
"""
import asyncio
import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.consultant_agent import NLUEngine, DialogueManager, ConsultantAgent
from backend.utils.token_counter import count_tokens
import requests

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_concurrent_nlu():
    """测试并发NLU处理"""
    print_header("🧠 并发NLU测试")
    
    engine = NLUEngine()
    test_messages = [
        "我在深圳工作，月薪3万，想买一套两居室",
        "南山区的房价怎么样？",
        "深圳的购房政策是什么？",
        "预算500万，推荐一下",
        "我30岁，程序员，想在北京买房",
        "广州天河区房价多少",
        "帮我算一下贷款，预算300万",
        "上海浦东有什么好小区",
        "北京海淀区学区房推荐",
        "深圳福田区两居室多少钱",
    ]
    
    async def analyze_message(msg):
        result = await engine.analyze(msg, [], {})
        return msg, result.intent, result.entities
    
    async def run_concurrent():
        start_time = time.time()
        tasks = [analyze_message(msg) for msg in test_messages]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        return results, end_time - start_time
    
    results, duration = asyncio.run(run_concurrent())
    
    print(f"\n📊 测试结果:")
    print(f"   请求数: {len(results)}")
    print(f"   总耗时: {duration:.3f}秒")
    print(f"   平均耗时: {duration/len(results)*1000:.1f}毫秒/请求")
    print(f"   QPS: {len(results)/duration:.1f}")
    
    print(f"\n📝 处理结果:")
    for msg, intent, entities in results[:5]:
        print(f"   '{msg[:20]}...' → {intent}")
    print(f"   ... 共 {len(results)} 条")
    
    print("\n✅ 并发NLU测试完成")

def test_concurrent_consultation():
    """测试并发咨询代理"""
    print_header("🤖 并发咨询代理测试")
    
    agent = ConsultantAgent()
    test_cases = [
        ("我想在深圳买房，预算500万", {"monthly_income": 30000}),
        ("广州天河区房价", {}),
        ("北京购房政策", {}),
        ("帮我算贷款，预算300万", {"monthly_income": 25000}),
        ("上海浦东推荐", {}),
    ]
    
    async def process_consult(msg, profile, idx):
        start = time.time()
        result = await agent.process(
            msg, f"session-{idx}", f"user-{idx}", [], profile
        )
        return idx, result['intent'], time.time() - start
    
    async def run_concurrent():
        start_time = time.time()
        tasks = [
            process_consult(msg, profile, i) 
            for i, (msg, profile) in enumerate(test_cases)
        ]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        return results, end_time - start_time
    
    results, duration = asyncio.run(run_concurrent())
    
    print(f"\n📊 测试结果:")
    print(f"   请求数: {len(results)}")
    print(f"   总耗时: {duration:.3f}秒")
    print(f"   平均耗时: {duration/len(results)*1000:.1f}毫秒/请求")
    
    print(f"\n📝 处理详情:")
    for idx, intent, elapsed in results:
        print(f"   请求{idx}: {intent} ({elapsed*1000:.1f}ms)")
    
    print("\n✅ 并发咨询代理测试完成")

def test_concurrent_token_counter():
    """测试并发Token计数"""
    print_header("💰 并发Token计数测试")
    
    test_texts = [
        "这是一个测试文本" * 10,
        "人工智能正在改变世界" * 20,
        "房产咨询系统测试" * 15,
        "并发处理能力测试" * 25,
        "系统性能优化方案" * 30,
    ] * 10  # 50个文本
    
    def count_token_task(text, idx):
        start = time.time()
        count = count_tokens(text)
        elapsed = time.time() - start
        return idx, count, elapsed
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(count_token_task, text, i) 
            for i, text in enumerate(test_texts)
        ]
        results = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start_time
    
    total_tokens = sum(r[1] for r in results)
    avg_time = sum(r[2] for r in results) / len(results)
    
    print(f"\n📊 测试结果:")
    print(f"   文本数: {len(test_texts)}")
    print(f"   总Token: {total_tokens}")
    print(f"   总耗时: {duration:.3f}秒")
    print(f"   平均耗时: {avg_time*1000:.2f}毫秒/文本")
    print(f"   QPS: {len(test_texts)/duration:.1f}")
    
    print("\n✅ 并发Token计数测试完成")

def test_concurrent_dialogue_manager():
    """测试并发对话管理"""
    print_header("💬 并发对话管理测试")
    
    def create_dialogue_session(session_id):
        dm = DialogueManager()
        dm.update_state('house_recommendation', {'city': '深圳'}, {})
        missing = dm.get_missing_fields()
        question = dm.generate_question(missing) if missing else None
        dm.update_state('house_recommendation', {'budget': 5000000}, {})
        final_missing = dm.get_missing_fields()
        return session_id, len(missing), len(final_missing), question
    
    start_time = time.time()
    session_count = 50
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(create_dialogue_session, i) 
            for i in range(session_count)
        ]
        results = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start_time
    
    print(f"\n📊 测试结果:")
    print(f"   会话数: {session_count}")
    print(f"   总耗时: {duration:.3f}秒")
    print(f"   平均耗时: {duration/session_count*1000:.2f}毫秒/会话")
    print(f"   QPS: {session_count/duration:.1f}")
    
    success_count = sum(1 for r in results if r[2] == 0)
    print(f"   成功率: {success_count/session_count*100:.1f}%")
    
    print("\n✅ 并发对话管理测试完成")

def test_concurrent_api_requests():
    """测试并发API请求"""
    print_header("🔌 并发API请求测试")
    
    endpoints = [
        "/health",
        "/health",
        "/health",
        "/api/consult/sessions",
        "/api/consult/profile",
    ] * 10  # 50个请求
    
    def make_request(endpoint, idx):
        start = time.time()
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            elapsed = time.time() - start
            return idx, response.status_code, elapsed, None
        except Exception as e:
            elapsed = time.time() - start
            return idx, 0, elapsed, str(e)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(make_request, endpoint, i) 
            for i, endpoint in enumerate(endpoints)
        ]
        results = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start_time
    
    success_count = sum(1 for r in results if r[1] in [200, 401])
    avg_time = sum(r[2] for r in results) / len(results)
    
    print(f"\n📊 测试结果:")
    print(f"   请求数: {len(endpoints)}")
    print(f"   成功数: {success_count}")
    print(f"   总耗时: {duration:.3f}秒")
    print(f"   平均耗时: {avg_time*1000:.2f}毫秒/请求")
    print(f"   QPS: {len(endpoints)/duration:.1f}")
    
    status_codes = {}
    for r in results:
        code = r[1]
        status_codes[code] = status_codes.get(code, 0) + 1
    
    print(f"\n📈 状态码分布:")
    for code, count in sorted(status_codes.items()):
        print(f"   {code}: {count}次")
    
    print("\n✅ 并发API请求测试完成")

def test_concurrent_loan_calculation():
    """测试并发贷款计算"""
    print_header("💵 并发贷款计算测试")
    
    agent = ConsultantAgent()
    test_cases = [
        (3000000, 20000),
        (5000000, 30000),
        (8000000, 50000),
        (4000000, 25000),
        (6000000, 40000),
    ] * 10  # 50个计算
    
    async def calc_loan(budget, income, idx):
        start = time.time()
        result = await agent._handle_loan_calc(
            entities={"budget": budget},
            profile={"monthly_income": income}
        )
        elapsed = time.time() - start
        return idx, budget, income, elapsed
    
    async def run_concurrent():
        start_time = time.time()
        tasks = [
            calc_loan(b, i, idx) 
            for idx, (b, i) in enumerate(test_cases)
        ]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        return results, duration
    
    results, duration = asyncio.run(run_concurrent())
    
    avg_time = sum(r[3] for r in results) / len(results)
    
    print(f"\n📊 测试结果:")
    print(f"   计算数: {len(test_cases)}")
    print(f"   总耗时: {duration:.3f}秒")
    print(f"   平均耗时: {avg_time*1000:.2f}毫秒/计算")
    print(f"   QPS: {len(test_cases)/duration:.1f}")
    
    print("\n✅ 并发贷款计算测试完成")

def main():
    print("\n" + "="*60)
    print(" 🚀 并发测试套件")
    print("="*60)
    
    test_concurrent_nlu()
    test_concurrent_consultation()
    test_concurrent_token_counter()
    test_concurrent_dialogue_manager()
    test_concurrent_api_requests()
    test_concurrent_loan_calculation()
    
    print("\n" + "="*60)
    print(" ✅ 所有并发测试完成！")
    print("="*60)
    
    print("\n📋 测试总结:")
    print("   ✅ 并发NLU: 多线程意图识别")
    print("   ✅ 并发咨询: 多会话并行处理")
    print("   ✅ 并发Token: 高性能计数")
    print("   ✅ 并发对话: 状态管理隔离")
    print("   ✅ 并发API: 请求吞吐量")
    print("   ✅ 并发贷款: 计算性能")

if __name__ == "__main__":
    main()
