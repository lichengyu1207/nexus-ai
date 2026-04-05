"""优化版并发测试 - 逐步增加负载"""
import time
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}

print("="*60)
print(" 🚀 1000并发请求压力测试")
print("="*60)

# 登录
r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=30)
token = r.json().get("access_token")
print(f"\n✅ 登录成功")

headers = {"Authorization": f"Bearer {token}"}

# 测试函数
def make_request(endpoint):
    try:
        start = time.time()
        r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=30)
        return r.status_code, time.time() - start
    except:
        return 0, 30

# 逐步增加并发测试
print("\n=== 阶段1: 50并发测试 ===")
endpoints = [
    "/api/users/me",
    "/api/consult/sessions", 
    "/api/consult/profile",
]

for endpoint in endpoints:
    start = time.time()
    with ThreadPoolExecutor(max_workers=25) as ex:
        results = list(ex.map(lambda _: make_request(endpoint), range(50)))
    total = time.time() - start
    success = sum(1 for r in results if r[0] == 200)
    avg = sum(r[1] for r in results) / len(results)
    print(f"  {endpoint}: {success}/50成功, {avg*1000:.0f}ms, QPS:{50/total:.0f}")

print("\n=== 阶段2: 100并发测试 ===")
start = time.time()
with ThreadPoolExecutor(max_workers=50) as ex:
    results = list(ex.map(lambda _: make_request("/api/users/me"), range(100)))
total = time.time() - start
success = sum(1 for r in results if r[0] == 200)
avg = sum(r[1] for r in results) / len(results)
print(f"  用户信息: {success}/100成功, {avg*1000:.0f}ms, QPS:{100/total:.0f}")

print("\n=== 阶段3: 500请求测试 (每批50) ===")
start = time.time()
all_results = []
for batch in range(10):
    with ThreadPoolExecutor(max_workers=50) as ex:
        results = list(ex.map(lambda _: make_request("/api/users/me"), range(50)))
        all_results.extend(results)
    print(f"  批次 {batch+1}/10 完成")

total = time.time() - start
success = sum(1 for r in all_results if r[0] == 200)
avg = sum(r[1] for r in all_results) / len(all_results)
print(f"\n📊 500请求结果:")
print(f"   成功: {success}/500")
print(f"   总耗时: {total:.2f}秒")
print(f"   平均响应: {avg*1000:.0f}ms")
print(f"   系统QPS: {500/total:.1f}")
print(f"   成功率: {success/500*100:.1f}%")

print("\n=== 阶段4: 1000请求测试 (每批100) ===")
start = time.time()
all_results = []
for batch in range(10):
    with ThreadPoolExecutor(max_workers=100) as ex:
        results = list(ex.map(lambda _: make_request("/api/users/me"), range(100)))
        all_results.extend(results)
    success = sum(1 for r in all_results if r[0] == 200)
    print(f"  批次 {batch+1}/10 完成, 累计成功: {success}")

total = time.time() - start
success = sum(1 for r in all_results if r[0] == 200)
avg = sum(r[1] for r in all_results) / len(all_results)

print(f"\n📊 1000请求最终结果:")
print(f"   总请求: 1000")
print(f"   成功: {success}")
print(f"   失败: {1000 - success}")
print(f"   总耗时: {total:.2f}秒")
print(f"   平均响应: {avg*1000:.0f}ms")
print(f"   系统QPS: {1000/total:.1f}")
print(f"   成功率: {success/1000*100:.1f}%")

print("\n" + "="*60)
print(" ✅ 压力测试完成")
print("="*60)
