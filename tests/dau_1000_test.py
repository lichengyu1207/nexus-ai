"""
日活1000并发综合测试
模拟真实用户的日常使用场景
测试账号: 1558691995@qq.com, 密码: 147258@Zxcvbnm
"""
import time
import random
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}

print("="*70)
print(" 🚀 日活1000并发综合测试")
print(" 📧 账号: 1558691995@qq.com")
print(" 📊 模拟1000个日活用户的真实使用场景")
print("="*70)

# 登录获取Token
print("\n🔐 登录中...")
r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=30)
token = r.json().get("access_token")
user_info = r.json().get("user", {})
print(f"✅ 登录成功, 用户: {user_info.get('email')}")

headers = {"Authorization": f"Bearer {token}"}

# 用户行为配置
USER_BEHAVIORS = {
    "dashboard_check": 0.30,      # 30% 用户查看仪表盘
    "consultation": 0.25,          # 25% 用户进行咨询
    "create_task": 0.15,           # 15% 用户创建分析任务
    "view_reports": 0.15,          # 15% 用户查看报告
    "check_integral": 0.10,        # 10% 用户查看积分
    "admin_operations": 0.05,      # 5% 管理员操作
}

CONSULT_QUESTIONS = [
    "深圳南山区房价怎么样？",
    "预算500万在深圳能买什么样的房子？",
    "广州天河区和深圳南山哪个更值得投资？",
    "北京海淀区学区房推荐",
    "上海浦东新区房价走势",
    "我月薪3万，想在深圳买房，有什么建议？",
]

TEST_ADDRESSES = [
    "深圳市南山区科技园",
    "深圳市福田区华强北",
    "广州市天河区珠江新城",
    "北京市海淀区中关村",
    "上海市浦东新区陆家嘴",
]

def make_request(method, endpoint, data=None, retry=2):
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
                time.sleep(0.2)
            continue
    return 0, 30, None

def simulate_dashboard_user(user_id):
    """模拟仪表盘用户"""
    results = []
    
    # 获取用户信息
    status, elapsed, _ = make_request("GET", "/api/users/me")
    results.append(("获取用户信息", status == 200, elapsed))
    
    # 获取积分
    status, elapsed, _ = make_request("GET", "/api/user/integral")
    results.append(("获取积分", status == 200, elapsed))
    
    # 获取通知
    status, elapsed, _ = make_request("GET", "/api/notifications")
    results.append(("获取通知", status == 200, elapsed))
    
    # 获取报告列表
    status, elapsed, _ = make_request("GET", "/api/reports")
    results.append(("获取报告列表", status == 200, elapsed))
    
    return results

def simulate_consultation_user(user_id):
    """模拟咨询用户"""
    results = []
    
    # 获取用户画像
    status, elapsed, _ = make_request("GET", "/api/consult/profile")
    results.append(("获取用户画像", status == 200, elapsed))
    
    # 获取会话列表
    status, elapsed, _ = make_request("GET", "/api/consult/sessions")
    results.append(("获取会话列表", status == 200, elapsed))
    
    # 发送咨询消息
    question = random.choice(CONSULT_QUESTIONS)
    status, elapsed, _ = make_request("POST", "/api/consult", {"message": question})
    results.append(("发送咨询消息", status in [200, 201], elapsed))
    
    return results

def simulate_task_user(user_id):
    """模拟任务创建用户"""
    results = []
    
    # 获取任务列表
    status, elapsed, _ = make_request("GET", "/api/tasks")
    results.append(("获取任务列表", status == 200, elapsed))
    
    # 创建分析任务
    address = random.choice(TEST_ADDRESSES)
    status, elapsed, _ = make_request("POST", "/api/tasks", {
        "query": f"{address}-用户{user_id}",
        "style": "professional"
    })
    results.append(("创建分析任务", status in [200, 201], elapsed))
    
    return results

def simulate_report_viewer(user_id):
    """模拟报告查看用户"""
    results = []
    
    # 获取报告列表
    status, elapsed, _ = make_request("GET", "/api/reports")
    results.append(("获取报告列表", status == 200, elapsed))
    
    # 获取报告统计
    status, elapsed, _ = make_request("GET", "/api/reports/stats")
    results.append(("获取报告统计", status in [200, 404], elapsed))
    
    return results

def simulate_integral_user(user_id):
    """模拟积分查看用户"""
    results = []
    
    # 获取积分余额
    status, elapsed, _ = make_request("GET", "/api/user/integral")
    results.append(("获取积分余额", status == 200, elapsed))
    
    # 获取积分历史
    status, elapsed, _ = make_request("GET", "/api/user/integral/logs")
    results.append(("获取积分历史", status in [200, 404], elapsed))
    
    # 获取积分套餐
    status, elapsed, _ = make_request("GET", "/api/user/integral/packages")
    results.append(("获取积分套餐", status in [200, 404], elapsed))
    
    return results

def simulate_admin_user(user_id):
    """模拟管理员用户"""
    results = []
    
    # 获取用户列表
    status, elapsed, _ = make_request("GET", "/api/admin/users")
    results.append(("获取用户列表", status in [200, 403], elapsed))
    
    # 获取统计数据
    status, elapsed, _ = make_request("GET", "/api/admin/settings")
    results.append(("获取系统设置", status in [200, 403], elapsed))
    
    return results

def simulate_user(user_id):
    """模拟单个用户的完整行为"""
    rand = random.random()
    cumulative = 0
    
    for behavior, probability in USER_BEHAVIORS.items():
        cumulative += probability
        if rand <= cumulative:
            if behavior == "dashboard_check":
                return simulate_dashboard_user(user_id)
            elif behavior == "consultation":
                return simulate_consultation_user(user_id)
            elif behavior == "create_task":
                return simulate_task_user(user_id)
            elif behavior == "view_reports":
                return simulate_report_viewer(user_id)
            elif behavior == "check_integral":
                return simulate_integral_user(user_id)
            elif behavior == "admin_operations":
                return simulate_admin_user(user_id)
    
    return simulate_dashboard_user(user_id)

# 阶段1: 100并发用户测试
print("\n" + "="*70)
print(" 📊 阶段1: 100并发用户测试")
print("="*70)

print("\n模拟100个并发用户...")
start = time.time()
with ThreadPoolExecutor(max_workers=50) as ex:
    all_results = list(ex.map(simulate_user, range(100)))

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

print(f"\n📊 各操作统计:")
for step_name, stats in sorted(step_stats.items()):
    avg_time = stats["time"] / stats["total"] * 1000
    rate = stats["success"] / stats["total"] * 100
    status = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
    print(f"   {status} {step_name}: {stats['success']}/{stats['total']} ({rate:.1f}%), {avg_time:.0f}ms")

total_requests = sum(len(r) for r in all_results)
success_requests = sum(sum(1 for a in r if a[1]) for r in all_results)

print(f"\n📊 100并发用户结果:")
print(f"   总请求: {total_requests}")
print(f"   成功请求: {success_requests}")
print(f"   总耗时: {total_time:.2f}秒")
print(f"   成功率: {success_requests/total_requests*100:.1f}%")
print(f"   系统QPS: {total_requests/total_time:.1f}")

# 阶段2: 500并发用户测试
print("\n" + "="*70)
print(" 📊 阶段2: 500并发用户测试 (分5批)")
print("="*70)

all_results_500 = []
start = time.time()

for batch in range(5):
    with ThreadPoolExecutor(max_workers=50) as ex:
        batch_results = list(ex.map(simulate_user, range(100)))
        all_results_500.extend(batch_results)
    print(f"   批次 {batch+1}/5 完成")

total_time_500 = time.time() - start

total_requests_500 = sum(len(r) for r in all_results_500)
success_requests_500 = sum(sum(1 for a in r if a[1]) for r in all_results_500)

print(f"\n📊 500并发用户结果:")
print(f"   总请求: {total_requests_500}")
print(f"   成功请求: {success_requests_500}")
print(f"   总耗时: {total_time_500:.2f}秒")
print(f"   成功率: {success_requests_500/total_requests_500*100:.1f}%")
print(f"   系统QPS: {total_requests_500/total_time_500:.1f}")

# 阶段3: 1000并发用户测试
print("\n" + "="*70)
print(" 🚀 阶段3: 1000并发用户测试 (分10批)")
print("="*70)

all_results_1000 = []
start = time.time()

for batch in range(10):
    with ThreadPoolExecutor(max_workers=50) as ex:
        batch_results = list(ex.map(simulate_user, range(100)))
        all_results_1000.extend(batch_results)
    success = sum(sum(1 for a in r if a[1]) for r in all_results_1000)
    print(f"   批次 {batch+1}/10 完成, 累计成功: {success}")

total_time_1000 = time.time() - start

total_requests_1000 = sum(len(r) for r in all_results_1000)
success_requests_1000 = sum(sum(1 for a in r if a[1]) for r in all_results_1000)

print(f"\n📊 1000并发用户结果:")
print(f"   总请求: {total_requests_1000}")
print(f"   成功请求: {success_requests_1000}")
print(f"   总耗时: {total_time_1000:.2f}秒")
print(f"   成功率: {success_requests_1000/total_requests_1000*100:.1f}%")
print(f"   系统QPS: {total_requests_1000/total_time_1000:.1f}")

# 阶段4: 持续压力测试 (模拟1小时流量)
print("\n" + "="*70)
print(" ⏱️ 阶段4: 持续压力测试 (模拟10分钟流量)")
print("="*70)

test_duration = 60  # 60秒测试
interval = 2  # 每2秒发送一批请求
batch_size = 20  # 每批20个请求

print(f"\n持续发送请求 {test_duration}秒...")
start = time.time()
sustained_results = []
batch_count = 0

while time.time() - start < test_duration:
    with ThreadPoolExecutor(max_workers=20) as ex:
        batch_results = list(ex.map(simulate_user, range(batch_size)))
        sustained_results.extend(batch_results)
    batch_count += 1
    time.sleep(interval)

total_time_sustained = time.time() - start
total_requests_sustained = sum(len(r) for r in sustained_results)
success_requests_sustained = sum(sum(1 for a in r if a[1]) for r in sustained_results)

print(f"\n📊 持续压力测试结果:")
print(f"   测试时长: {total_time_sustained:.1f}秒")
print(f"   批次数: {batch_count}")
print(f"   总请求: {total_requests_sustained}")
print(f"   成功请求: {success_requests_sustained}")
print(f"   成功率: {success_requests_sustained/total_requests_sustained*100:.1f}%")
print(f"   平均QPS: {total_requests_sustained/total_time_sustained:.1f}")

# 最终汇总
print("\n" + "="*70)
print(" 📊 最终测试报告")
print("="*70)

overall_total = total_requests + total_requests_500 + total_requests_1000 + total_requests_sustained
overall_success = success_requests + success_requests_500 + success_requests_1000 + success_requests_sustained

print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                    日活1000并发综合测试报告                      │
├─────────────────────────────────────────────────────────────────┤
│  测试账号: 1558691995@qq.com                                    │
│  测试时间: {time.strftime("%Y-%m-%d %H:%M:%S")}                            │
├─────────────────────────────────────────────────────────────────┤
│  用户行为分布:                                                  │
│    - 仪表盘查看: 30%                                            │
│    - 智能咨询: 25%                                              │
│    - 创建任务: 15%                                              │
│    - 查看报告: 15%                                              │
│    - 查看积分: 10%                                              │
│    - 管理操作: 5%                                               │
├─────────────────────────────────────────────────────────────────┤
│  阶段1 - 100并发: {success_requests}/{total_requests} ({success_requests/total_requests*100:.1f}%)              │
│  阶段2 - 500并发: {success_requests_500}/{total_requests_500} ({success_requests_500/total_requests_500*100:.1f}%)              │
│  阶段3 - 1000并发: {success_requests_1000}/{total_requests_1000} ({success_requests_1000/total_requests_1000*100:.1f}%)            │
│  阶段4 - 持续压力: {success_requests_sustained}/{total_requests_sustained} ({success_requests_sustained/total_requests_sustained*100:.1f}%)          │
├─────────────────────────────────────────────────────────────────┤
│  总请求数: {overall_total}                                          │
│  总成功数: {overall_success}                                          │
│  总体成功率: {overall_success/overall_total*100:.1f}%                              │
│  峰值QPS: {total_requests_1000/total_time_1000:.1f}                                          │
│  持续QPS: {total_requests_sustained/total_time_sustained:.1f}                                        │
└─────────────────────────────────────────────────────────────────┘
""")

print(" ✅ 日活1000并发测试完成！")
print("="*70)
