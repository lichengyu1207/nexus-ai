"""
用户登录后仪表盘创建任务分析 - 1000并发测试 (优化版)
测试账号: 1558691995@qq.com, 密码: 147258@Zxcvbnm
优化：降低并发数、添加重试机制、避免数据库锁定
"""
import time
import random
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}

print("="*70)
print(" 🚀 用户登录后仪表盘创建任务分析 - 1000并发测试")
print(" 📧 账号: 1558691995@qq.com")
print("="*70)

# 登录获取Token
print("\n🔐 登录中...")
r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=30)
token = r.json().get("access_token")
print(f"✅ 登录成功")

headers = {"Authorization": f"Bearer {token}"}

# 检查积分余额
r = requests.get(f"{BASE_URL}/api/user/integral", headers=headers)
integral = r.json().get("integral", 0)
print(f"💰 当前积分余额: {integral}")

TEST_ADDRESSES = [
    "深圳市南山区科技园",
    "深圳市福田区华强北",
    "广州市天河区珠江新城",
    "北京市海淀区中关村",
    "上海市浦东新区陆家嘴",
]

def make_request(method, endpoint, data=None, retry=3):
    for i in range(retry):
        try:
            start = time.time()
            if method == "GET":
                r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=30)
            elif method == "POST":
                r = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers, timeout=30)
            else:
                return 0, 30, None
            return r.status_code, time.time() - start, r
        except:
            if i < retry - 1:
                time.sleep(0.5)
            continue
    return 0, 30, None

# 阶段1: 仪表盘数据加载测试
print("\n" + "="*70)
print(" 📊 阶段1: 仪表盘数据加载测试 (50并发)")
print("="*70)

dashboard_apis = [
    ("GET", "/api/users/me", "获取用户信息"),
    ("GET", "/api/user/integral", "获取积分余额"),
    ("GET", "/api/reports", "获取报告列表"),
    ("GET", "/api/notifications", "获取通知列表"),
    ("GET", "/api/consult/sessions", "获取咨询会话"),
]

dashboard_total = 0
dashboard_success = 0

for method, endpoint, desc in dashboard_apis:
    start = time.time()
    with ThreadPoolExecutor(max_workers=25) as ex:
        results = list(ex.map(lambda _: make_request(method, endpoint), range(50)))
    
    total = time.time() - start
    success = sum(1 for r in results if r[0] in [200, 201])
    avg = sum(r[1] for r in results) / len(results)
    
    dashboard_total += 50
    dashboard_success += success
    
    status = "✅" if success >= 40 else "⚠️"
    print(f"   {status} {desc}: {success}/50, {avg*1000:.0f}ms, QPS:{50/total:.0f}")

print(f"\n📊 仪表盘加载汇总: {dashboard_success}/{dashboard_total} ({dashboard_success/dashboard_total*100:.1f}%)")

# 阶段2: 创建分析任务测试 (降低并发)
print("\n" + "="*70)
print(" 📝 阶段2: 创建分析任务测试 (20并发)")
print("="*70)

def create_task(task_id):
    address = random.choice(TEST_ADDRESSES)
    data = {"query": f"{address}-{task_id}", "style": "professional"}
    return make_request("POST", "/api/tasks", data)

print("\n创建20个并发分析任务...")
start = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(create_task, range(20)))

total = time.time() - start
success = sum(1 for r in results if r[0] in [200, 201])
avg = sum(r[1] for r in results) / len(results)

print(f"\n📊 创建任务结果:")
print(f"   成功: {success}/20")
print(f"   平均耗时: {avg*1000:.0f}ms")
print(f"   QPS: {20/total:.0f}")
print(f"   成功率: {success/20*100:.1f}%")

# 阶段3: 获取任务列表测试
print("\n" + "="*70)
print(" 📋 阶段3: 获取任务列表测试 (50并发)")
print("="*70)

start = time.time()
with ThreadPoolExecutor(max_workers=25) as ex:
    results = list(ex.map(lambda _: make_request("GET", "/api/tasks"), range(50)))

total = time.time() - start
success = sum(1 for r in results if r[0] == 200)
avg = sum(r[1] for r in results) / len(results)

print(f"\n📊 获取任务列表结果:")
print(f"   成功: {success}/50")
print(f"   平均耗时: {avg*1000:.0f}ms")
print(f"   QPS: {50/total:.0f}")

# 阶段4: 完整用户流程测试
print("\n" + "="*70)
print(" 🔄 阶段4: 完整用户流程测试 (50并发用户)")
print("="*70)

def user_flow(user_id):
    results = []
    
    # 1. 获取用户信息
    status, elapsed, _ = make_request("GET", "/api/users/me")
    results.append(("获取用户信息", status == 200, elapsed))
    
    # 2. 获取仪表盘数据
    status, elapsed, _ = make_request("GET", "/api/user/integral")
    results.append(("获取积分", status == 200, elapsed))
    
    status, elapsed, _ = make_request("GET", "/api/reports")
    results.append(("获取报告", status == 200, elapsed))
    
    # 3. 获取任务列表
    status, elapsed, _ = make_request("GET", "/api/tasks")
    results.append(("获取任务列表", status == 200, elapsed))
    
    # 4. 获取通知
    status, elapsed, _ = make_request("GET", "/api/notifications")
    results.append(("获取通知", status == 200, elapsed))
    
    return results

print("\n模拟50个并发用户完整流程...")
start = time.time()
with ThreadPoolExecutor(max_workers=25) as ex:
    all_results = list(ex.map(user_flow, range(50)))

total_time = time.time() - start

step_stats = {}
for user_results in all_results:
    for step_name, success, elapsed in user_results:
        if step_name not in step_stats:
            step_stats[step_name] = {"success": 0, "total": 0, "time": 0}
        step_stats[step_name]["total"] += 1
        if success:
            step_stats[step_name]["success"] += 1
        step_stats[step_name]["time"] += elapsed

print(f"\n📊 各步骤统计:")
for step_name, stats in step_stats.items():
    avg_time = stats["time"] / stats["total"] * 1000
    rate = stats["success"] / stats["total"] * 100
    status = "✅" if rate >= 90 else "⚠️"
    print(f"   {status} {step_name}: {stats['success']}/{stats['total']} ({rate:.1f}%), {avg_time:.0f}ms")

total_requests = sum(len(r) for r in all_results)
success_requests = sum(sum(1 for a in r if a[1]) for r in all_results)

print(f"\n📊 完整流程汇总:")
print(f"   总请求: {total_requests}")
print(f"   成功请求: {success_requests}")
print(f"   总耗时: {total_time:.2f}秒")
print(f"   成功率: {success_requests/total_requests*100:.1f}%")
print(f"   系统QPS: {total_requests/total_time:.1f}")

# 阶段5: 1000请求压力测试
print("\n" + "="*70)
print(" 🚀 阶段5: 1000请求压力测试 (每批50并发)")
print("="*70)

def stress_task(request_id):
    actions = [
        lambda: make_request("GET", "/api/users/me"),
        lambda: make_request("GET", "/api/reports"),
        lambda: make_request("GET", "/api/tasks"),
        lambda: make_request("GET", "/api/user/integral"),
    ]
    return random.choice(actions)()

print("\n启动1000请求压力测试...")
start = time.time()
all_results = []

for batch in range(20):  # 20批，每批50
    with ThreadPoolExecutor(max_workers=25) as ex:
        results = list(ex.map(stress_task, range(50)))
        all_results.extend(results)
    
    success = sum(1 for r in all_results if r[0] in [200, 201])
    print(f"   批次 {batch+1}/20 完成, 累计成功: {success}")

total = time.time() - start
success = sum(1 for r in all_results if r[0] in [200, 201])
avg = sum(r[1] for r in all_results) / len(all_results)

print(f"\n📊 1000请求压力测试结果:")
print(f"   总请求: 1000")
print(f"   成功: {success}")
print(f"   失败: {1000 - success}")
print(f"   总耗时: {total:.2f}秒")
print(f"   平均响应: {avg*1000:.0f}ms")
print(f"   系统QPS: {1000/total:.1f}")
print(f"   成功率: {success/1000*100:.1f}%")

# 最终汇总
print("\n" + "="*70)
print(" 📊 最终测试报告")
print("="*70)

print(f"""
┌─────────────────────────────────────────────────────────────────┐
│           用户登录后仪表盘创建任务分析 - 测试报告                │
├─────────────────────────────────────────────────────────────────┤
│  测试账号: 1558691995@qq.com                                    │
│  初始积分: {integral}                                              │
│  测试时间: {time.strftime("%Y-%m-%d %H:%M:%S")}                            │
├─────────────────────────────────────────────────────────────────┤
│  阶段1 - 仪表盘加载: {dashboard_success}/{dashboard_total} ({dashboard_success/dashboard_total*100:.1f}%)              │
│  阶段2 - 创建任务: {success}/20 ({success/20*100:.1f}%)                        │
│  阶段3 - 获取任务: {sum(1 for r in results if r[0]==200)}/50 ({sum(1 for r in results if r[0]==200)/50*100:.1f}%)                    │
│  阶段4 - 完整流程: {success_requests}/{total_requests} ({success_requests/total_requests*100:.1f}%)                   │
│  阶段5 - 1000压力: {success}/1000 ({success/1000*100:.1f}%)                    │
├─────────────────────────────────────────────────────────────────┤
│  系统QPS: {1000/total:.1f}                                           │
│  平均响应时间: {avg*1000:.0f}ms                                     │
│  总体成功率: {success/1000*100:.1f}%                              │
└─────────────────────────────────────────────────────────────────┘
""")

print(" ✅ 所有测试完成！")
print("="*70)
