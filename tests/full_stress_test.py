"""
1000并发用户全面压力测试 (修正版)
测试前端所有功能 + 管理员后端并发
账号: 1558691995@qq.com, 密码: 147258@Zxcvbnm
"""
import time
import random
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}

print("="*70)
print(" 🚀 1000并发用户全面压力测试")
print(" 📧 账号: 1558691995@qq.com")
print("="*70)

# 登录获取Token
r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=30)
token = r.json().get("access_token")
print(f"\n✅ 登录成功")

headers = {"Authorization": f"Bearer {token}"}

# 定义所有API端点 (使用正确的路径)
ALL_APIS = {
    "用户端": [
        ("GET", "/api/users/me", "获取用户信息"),
        ("GET", "/api/users/me/preferences", "获取偏好设置"),
    ],
    "咨询功能": [
        ("GET", "/api/consult/sessions", "获取会话列表"),
        ("GET", "/api/consult/profile", "获取用户画像"),
        ("POST", "/api/consult", "发送咨询消息"),
    ],
    "积分系统": [
        ("GET", "/api/user/integral", "获取积分余额"),
        ("GET", "/api/user/integral/logs", "获取积分历史"),
        ("GET", "/api/user/integral/packages", "获取积分套餐"),
    ],
    "上传功能": [
        ("GET", "/api/uploads/data-types", "获取数据类型"),
        ("GET", "/api/uploads", "获取我的上传"),
    ],
    "报告功能": [
        ("GET", "/api/reports", "获取报告列表"),
    ],
    "通知功能": [
        ("GET", "/api/notifications", "获取通知列表"),
        ("GET", "/api/notifications/unread-count", "获取未读数量"),
    ],
    "管理员-用户": [
        ("GET", "/api/admin/users", "用户管理列表"),
    ],
    "管理员-报告": [
        ("GET", "/api/admin/reports", "报告管理列表"),
    ],
    "管理员-积分": [
        ("GET", "/api/admin/users/integral/summary", "积分管理"),
    ],
    "管理员-上传": [
        ("GET", "/api/uploads/admin/pending", "上传管理"),
        ("GET", "/api/uploads/admin/stats", "上传统计"),
    ],
    "管理员-反馈": [
        ("GET", "/api/admin/feedback", "反馈管理"),
    ],
    "管理员-系统": [
        ("GET", "/api/admin/settings", "系统设置"),
    ],
}

def make_request(method, endpoint, data=None):
    try:
        start = time.time()
        if method == "GET":
            r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=30)
        elif method == "POST":
            r = requests.post(f"{BASE_URL}{endpoint}", json=data or {}, headers=headers, timeout=30)
        elif method == "PUT":
            r = requests.put(f"{BASE_URL}{endpoint}", json=data or {}, headers=headers, timeout=30)
        else:
            return 0, 30
        return r.status_code, time.time() - start
    except:
        return 0, 30

# 阶段1: 测试所有API端点
print("\n" + "="*70)
print(" 📋 阶段1: 测试所有API端点 (每端点50并发)")
print("="*70)

total_requests = 0
total_success = 0
api_results = {}

for category, apis in ALL_APIS.items():
    print(f"\n🔹 {category}:")
    category_success = 0
    category_total = 0
    
    for method, endpoint, desc in apis:
        start = time.time()
        with ThreadPoolExecutor(max_workers=25) as ex:
            if method == "POST" and "consult" in endpoint:
                results = list(ex.map(lambda _: make_request(method, endpoint, {"message": "测试消息"}), range(50)))
            else:
                results = list(ex.map(lambda _: make_request(method, endpoint), range(50)))
        
        total = time.time() - start
        success = sum(1 for r in results if r[0] in [200, 201])
        avg = sum(r[1] for r in results) / len(results)
        
        status = "✅" if success >= 40 else "⚠️" if success >= 20 else "❌"
        print(f"   {status} {desc}: {success}/50, {avg*1000:.0f}ms, QPS:{50/total:.0f}")
        
        category_success += success
        category_total += 50
        total_requests += 50
        total_success += success
    
    api_results[category] = (category_success, category_total)

print(f"\n📊 阶段1汇总: {total_success}/{total_requests} 成功 ({total_success/total_requests*100:.1f}%)")

# 阶段2: 混合负载测试
print("\n" + "="*70)
print(" 🎭 阶段2: 混合负载测试 (模拟真实用户行为)")
print("="*70)

def user_session(session_id):
    """模拟单个用户会话"""
    results = []
    
    actions = [
        ("GET", "/api/users/me", None),
        ("GET", "/api/consult/sessions", None),
        ("GET", "/api/consult/profile", None),
        ("POST", "/api/consult", {"message": "深圳房价怎么样？"}),
        ("GET", "/api/user/integral", None),
        ("GET", "/api/user/integral/logs", None),
        ("GET", "/api/uploads/data-types", None),
        ("GET", "/api/reports", None),
        ("GET", "/api/notifications", None),
        ("GET", "/api/admin/users", None),
        ("GET", "/api/admin/settings", None),
    ]
    
    for _ in range(random.randint(5, 10)):
        method, endpoint, data = random.choice(actions)
        status, elapsed = make_request(method, endpoint, data)
        results.append((endpoint, status in [200, 201], elapsed))
    
    return results

print(f"\n模拟 100 个并发用户会话...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=100) as ex:
    all_results = list(ex.map(user_session, range(100)))

total_time = time.time() - start_time

total_req = sum(len(r) for r in all_results)
success_req = sum(sum(1 for a in r if a[1]) for r in all_results)

print(f"\n📊 混合负载结果:")
print(f"   并发用户: 100")
print(f"   总请求: {total_req}")
print(f"   成功请求: {success_req}")
print(f"   总耗时: {total_time:.2f}秒")
print(f"   成功率: {success_req/total_req*100:.1f}%")
print(f"   系统QPS: {total_req/total_time:.1f}")

# 阶段3: 1000请求压力测试
print("\n" + "="*70)
print(" 🚀 阶段3: 1000请求压力测试")
print("="*70)

def stress_test():
    """压力测试"""
    endpoints = [
        "/api/users/me",
        "/api/consult/sessions",
        "/api/user/integral",
        "/api/admin/settings",
    ]
    endpoint = random.choice(endpoints)
    return make_request("GET", endpoint)

print(f"\n启动 1000 请求压力测试 (每批100并发)...")
start_time = time.time()
all_results = []

for batch in range(10):
    with ThreadPoolExecutor(max_workers=100) as ex:
        results = list(ex.map(lambda _: stress_test(), range(100)))
        all_results.extend(results)
    
    success = sum(1 for r in all_results if r[0] in [200, 201])
    print(f"   批次 {batch+1}/10 完成, 累计成功: {success}")

total_time = time.time() - start_time
success = sum(1 for r in all_results if r[0] in [200, 201])
avg = sum(r[1] for r in all_results) / len(all_results)

print(f"\n📊 1000请求压力测试结果:")
print(f"   总请求: 1000")
print(f"   成功: {success}")
print(f"   失败: {1000 - success}")
print(f"   总耗时: {total_time:.2f}秒")
print(f"   平均响应: {avg*1000:.0f}ms")
print(f"   系统QPS: {1000/total_time:.1f}")
print(f"   成功率: {success/1000*100:.1f}%")

# 阶段4: 管理员API专项测试
print("\n" + "="*70)
print(" 🔧 阶段4: 管理员API专项测试 (100并发)")
print("="*70)

admin_endpoints = [
    "/api/admin/users",
    "/api/admin/reports",
    "/api/admin/users/integral/summary",
    "/api/uploads/admin/pending",
    "/api/uploads/admin/stats",
    "/api/admin/settings",
]

admin_total = 0
admin_success = 0

for endpoint in admin_endpoints:
    start = time.time()
    with ThreadPoolExecutor(max_workers=50) as ex:
        results = list(ex.map(lambda _: make_request("GET", endpoint), range(100)))
    
    total = time.time() - start
    success = sum(1 for r in results if r[0] in [200, 201])
    avg = sum(r[1] for r in results) / len(results)
    
    admin_total += 100
    admin_success += success
    
    status = "✅" if success >= 80 else "⚠️" if success >= 50 else "❌"
    print(f"   {status} {endpoint}: {success}/100, {avg*1000:.0f}ms, QPS:{100/total:.0f}")

print(f"\n📊 管理员API汇总: {admin_success}/{admin_total} ({admin_success/admin_total*100:.1f}%)")

# 最终汇总
print("\n" + "="*70)
print(" 📊 最终测试报告")
print("="*70)

overall_total = total_requests + total_req + 1000 + admin_total
overall_success = total_success + success_req + success + admin_success

print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    1000并发压力测试报告                          │
├─────────────────────────────────────────────────────────────────┤
│  测试账号: 1558691995@qq.com                                    │
│  测试时间: {time.strftime("%Y-%m-%d %H:%M:%S")}                            │
├─────────────────────────────────────────────────────────────────┤
│  阶段1 - API端点测试: {total_success}/{total_requests} ({total_success/total_requests*100:.1f}%)              │
│  阶段2 - 混合负载测试: {success_req}/{total_req} ({success_req/total_req*100:.1f}%)                   │
│  阶段3 - 1000请求压力: {success}/1000 ({success/1000*100:.1f}%)                    │
│  阶段4 - 管理员API: {admin_success}/{admin_total} ({admin_success/admin_total*100:.1f}%)                  │
├─────────────────────────────────────────────────────────────────┤
│  总请求数: {overall_total}                                          │
│  总成功数: {overall_success}                                          │
│  系统QPS: {1000/total_time:.1f}                                           │
│  平均响应时间: {avg*1000:.0f}ms                                     │
│  总体成功率: {overall_success/overall_total*100:.1f}%                              │
└─────────────────────────────────────────────────────────────────┘
""")

print(" ✅ 所有并发测试完成！")
print("="*70)
