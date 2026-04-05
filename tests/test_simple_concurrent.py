"""简单并发测试"""
import asyncio
import time
import sys
sys.path.insert(0, '.')
from backend.services.consultant_agent import NLUEngine, DialogueManager, ConsultantAgent
from backend.utils.token_counter import count_tokens

print("="*50)
print(" 并发测试")
print("="*50)

# 1. NLU并发
print("\n1. NLU并发测试")
engine = NLUEngine()
msgs = ["深圳买房", "北京房价", "广州政策"] * 3

async def test_nlu():
    start = time.time()
    tasks = [engine.analyze(m, [], {}) for m in msgs]
    await asyncio.gather(*tasks)
    print(f"   {len(msgs)}请求, {time.time()-start:.3f}秒, QPS:{len(msgs)/(time.time()-start):.0f}")

asyncio.run(test_nlu())

# 2. Token并发
print("\n2. Token并发测试")
from concurrent.futures import ThreadPoolExecutor
texts = ["测试文本"] * 20

start = time.time()
with ThreadPoolExecutor(max_workers=5) as ex:
    list(ex.map(count_tokens, texts))
print(f"   {len(texts)}请求, {time.time()-start:.3f}秒, QPS:{len(texts)/(time.time()-start):.0f}")

# 3. 对话管理并发
print("\n3. 对话管理并发测试")
def dm_test(i):
    dm = DialogueManager()
    dm.update_state('house_recommendation', {'city': '深圳'}, {})
    return dm.get_missing_fields()

start = time.time()
with ThreadPoolExecutor(max_workers=5) as ex:
    list(ex.map(dm_test, range(20)))
print(f"   20请求, {time.time()-start:.3f}秒, QPS:{20/(time.time()-start):.0f}")

# 4. 贷款计算并发
print("\n4. 贷款计算并发测试")
agent = ConsultantAgent()

async def test_loan():
    cases = [(3000000, 20000)] * 10
    start = time.time()
    tasks = [agent._handle_loan_calc({'budget': b}, {'monthly_income': i}) for b, i in cases]
    await asyncio.gather(*tasks)
    print(f"   {len(cases)}请求, {time.time()-start:.3f}秒, QPS:{len(cases)/(time.time()-start):.0f}")

asyncio.run(test_loan())

print("\n" + "="*50)
print(" 并发测试完成")
print("="*50)
