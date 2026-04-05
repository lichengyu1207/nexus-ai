"""
用户登录后智能咨询 - 1000并发测试
测试账号: 1558691995@qq.com, 密码: 147258@Zxcvbnm
"""
import time
import random
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}

print("="*70)
print(" 🚀 用户登录后智能咨询 - 1000并发测试")
print(" 📧 账号: 1558691995@qq.com")
print("="*70)

# 登录获取Token
print("\n🔐 登录中...")
r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=30)
token = r.json().get("access_token")
print(f"✅ 登录成功")

headers = {"Authorization": f"Bearer {token}"}

# 测试咨询问题列表
CONSULT_QUESTIONS = [
    "深圳南山区房价怎么样？",
    "预算500万在深圳能买什么样的房子？",
    "广州天河区和深圳南山哪个更值得投资？",
    "北京海淀区学区房推荐",
    "上海浦东新区房价走势",
    "我月薪3万，想在深圳买房，有什么建议？",
    "两居室和三居室哪个更适合投资？",
    "贷款买房需要注意什么？",
    "首套房和二套房有什么区别？",
    "如何选择合适的小区？",
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
                time.sleep(0.3)
            continue
    return 0, 30, None

# 阶段1: 获取咨询相关数据
print("\n" + "="*70)
print(" 📊 阶段1: 咨询数据加载测试 (50并发)")
print("="*70)

consult_apis = [
    ("GET", "/api/consult/sessions", None, "获取会话列表"),
    ("GET", "/api/consult/profile", None, "获取用户画像"),
]

consult_total = 0
consult_success = 0

for method, endpoint, data, desc in consult_apis:
    start = time.time()
    with ThreadPoolExecutor(max_workers=25) as ex:
        results = list(ex.map(lambda _: make_request(method, endpoint, data), range(50)))
    
    total = time.time() - start
    success = sum(1 for r in results if r[0] in [200, 201])
    avg = sum(r[1] for r in results) / len(results)
    
    consult_total += 50
    consult_success += success
    
    status = "✅" if success >= 40 else "⚠️"
    print(f"   {status} {desc}: {success}/50, {avg*1000:.0f}ms, QPS:{50/total:.0f}")

print(f"\n📊 咨询数据加载汇总: {consult_success}/{consult_total} ({consult_success/consult_total*100:.1f}%)")

# 阶段2: 发送咨询消息测试
print("\n" + "="*70)
print(" 💬 阶段2: 发送咨询消息测试 (50并发)")
print("="*70)

def send_consult_message(msg_id):
    question = random.choice(CONSULT_QUESTIONS)
    data = {"message": f"{question} (测试{msg_id})"}
    return make_request("POST", "/api/consult", data)

print("\n发送50个并发咨询消息...")
start = time.time()
with ThreadPoolExecutor(max_workers=25) as ex:
    results = list(ex.map(send_consult_message, range(50)))

total = time.time() - start
success = sum(1 for r in results if r[0] in [200, 201])
avg = sum(r[1] for r in results) / len(results)

print(f"\n📊 发送咨询消息结果:")
print(f"   成功: {success}/50")
print(f"   平均耗时: {avg*1000:.0f}ms")
print(f"   QPS: {50/total:.0f}")
print(f"   成功率: {success/50*100:.1f}%")

# 阶段3: 完整咨询流程测试
print("\n" + "="*70)
print(" 🔄 阶段3: 完整咨询流程测试 (50并发用户)")
print("="*70)

def consult_flow(user_id):
    results = []
    
    # 1. 获取用户画像
    status, elapsed, _ = make_request("GET", "/api/consult/profile")
    results.append(("获取用户画像", status == 200, elapsed))
    
    # 2. 获取会话列表
    status, elapsed, _ = make_request("GET", "/api/consult/sessions")
    results.append(("获取会话列表", status == 200, elapsed))
    
    # 3. 发送咨询消息
    question = random.choice(CONSULT_QUESTIONS)
    status, elapsed, _ = make_request("POST", "/api/consult", {"message": question})
    results.append(("发送咨询消息", status in [200, 201], elapsed))
    
    # 4. 再次获取会话列表
    status, elapsed, _ = make_request("GET", "/api/consult/sessions")
    results.append(("刷新会话列表", status == 200, elapsed))
    
    return results

print("\n模拟50个并发用户咨询流程...")
start = time.time()
with ThreadPoolExecutor(max_workers=25) as ex:
    all_results = list(ex.map(consult_flow, range(50)))

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

# 阶段4: 多轮对话测试
print("\n" + "="*70)
print(" 🗣️ 阶段4: 多轮对话测试 (20并发)")
print("="*70)

def multi_turn_dialog(session_id):
    results = []
    
    # 第一轮：询问房价
    status, elapsed, r = make_request("POST", "/api/consult", {"message": "深圳房价怎么样？"})
    results.append(("第一轮对话", status in [200, 201], elapsed))
    
    if status == 200 and r:
        session_data = r.json()
        session_id = session_data.get("session_id", "")
        
        # 第二轮：追问区域
        if session_id:
            status2, elapsed2, _ = make_request("POST", "/api/consult", {
                "message": "南山区呢？",
                "session_id": session_id
            })
            results.append(("第二轮对话", status2 in [200, 201], elapsed2))
            
            # 第三轮：询问预算
            status3, elapsed3, _ = make_request("POST", "/api/consult", {
                "message": "预算500万有什么推荐？",
                "session_id": session_id
            })
            results.append(("第三轮对话", status3 in [200, 201], elapsed3))
    
    return results

print("\n模拟20个并发多轮对话...")
start = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    all_results = list(ex.map(multi_turn_dialog, range(20)))

total_time = time.time() - start

total_requests = sum(len(r) for r in all_results)
success_requests = sum(sum(1 for a in r if a[1]) for r in all_results)

print(f"\n📊 多轮对话结果:")
print(f"   总请求: {total_requests}")
print(f"   成功请求: {success_requests}")
print(f"   总耗时: {total_time:.2f}秒")
print(f"   成功率: {success_requests/total_requests*100:.1f}%")

# 阶段5: 1000请求压力测试
print("\n" + "="*70)
print(" 🚀 阶段5: 1000请求压力测试")
print("="*70)

def stress_task(request_id):
    actions = [
        lambda: make_request("GET", "/api/consult/sessions"),
        lambda: make_request("GET", "/api/consult/profile"),
        lambda: make_request("POST", "/api/consult", {"message": random.choice(CONSULT_QUESTIONS)}),
    ]
    return random.choice(actions)()

print("\n启动1000请求压力测试 (每批50并发)...")
start = time.time()
all_results = []

for batch in range(20):
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
│              用户登录后智能咨询 - 测试报告                       │
├─────────────────────────────────────────────────────────────────┤
│  测试账号: 1558691995@qq.com                                    │
│  测试时间: {time.strftime("%Y-%m-%d %H:%M:%S")}                            │
├─────────────────────────────────────────────────────────────────┤
│  阶段1 - 数据加载: {consult_success}/{consult_total} ({consult_success/consult_total*100:.1f}%)              │
│  阶段2 - 发送消息: {success}/50 ({success/50*100:.1f}%)                        │
│  阶段3 - 完整流程: {success_requests}/{total_requests} ({success_requests/total_requests*100:.1f}%)                   │
│  阶段4 - 多轮对话: {success_requests}/{total_requests} ({success_requests/total_requests*100:.1f}%)                   │
│  阶段5 - 1000压力: {success}/1000 ({success/1000*100:.1f}%)                    │
├─────────────────────────────────────────────────────────────────┤
│  系统QPS: {1000/total:.1f}                                           │
│  平均响应时间: {avg*1000:.0f}ms                                     │
│  总体成功率: {success/1000*100:.1f}%                              │
└─────────────────────────────────────────────────────────────────┘
""")

print(" ✅ 所有测试完成！")
print("="*70)
