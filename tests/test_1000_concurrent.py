"""
优化版1000并发测试
使用单一Token测试API并发性能
"""
import time
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

sys.path.insert(0, '.')

BASE_URL = "http://127.0.0.1:8000"

TEST_USER = {
    "email": "1558691995@qq.com",
    "password": "147258@Zxcvbnm"
}

CONCURRENT_REQUESTS = 100
TOTAL_REQUESTS = 1000

def get_token():
    """获取登录Token"""
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
    except:
        pass
    return None

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_api_concurrent(token, name, method, endpoint, data=None, desc=""):
    """测试单个API并发"""
    print(f"\n📝 {name} - {desc}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    def make_request():
        try:
            start = time.time()
            if method == "GET":
                r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                r = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers, timeout=10)
            else:
                return None, 0
            return r.status_code, time.time() - start
        except Exception as e:
            return None, 0
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(CONCURRENT_REQUESTS)]
        results = [f.result() for f in as_completed(futures)]
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r[0] and r[0] < 500)
    avg_time = sum(r[1] for r in results) / len(results)
    min_time = min(r[1] for r in results)
    max_time = max(r[1] for r in results)
    
    print(f"   请求数: {CONCURRENT_REQUESTS}")
    print(f"   成功: {success_count}")
    print(f"   平均: {avg_time*1000:.1f}ms")
    print(f"   最小: {min_time*1000:.1f}ms")
    print(f"   最大: {max_time*1000:.1f}ms")
    print(f"   QPS: {CONCURRENT_REQUESTS/total_time:.1f}")
    
    return success_count, total_time

def test_all_apis(token):
    """测试所有API"""
    print_header("🔌 全API并发测试")
    
    total_success = 0
    total_requests = 0
    
    # 咨询API
    apis = [
        ("咨询", "GET", "/api/consult/sessions", None, "获取会话列表"),
        ("咨询", "GET", "/api/consult/profile", None, "获取用户画像"),
        ("咨询", "POST", "/api/consult", {"message": "深圳房价怎么样？"}, "发送咨询"),
        ("积分", "GET", "/api/integral/balance", None, "获取余额"),
        ("积分", "GET", "/api/integral/history", None, "获取历史"),
        ("积分", "GET", "/api/integral/plans", None, "获取套餐"),
        ("用户", "GET", "/api/users/me", None, "获取用户信息"),
        ("用户", "GET", "/api/users/me/preferences", None, "获取偏好设置"),
        ("上传", "GET", "/api/uploads/types", None, "获取数据类型"),
        ("上传", "GET", "/api/uploads/my-uploads", None, "获取我的上传"),
    ]
    
    for category, method, endpoint, data, desc in apis:
        success, _ = test_api_concurrent(token, f"{category}API", method, endpoint, data, desc)
        total_success += success
        total_requests += CONCURRENT_REQUESTS
    
    print(f"\n📊 API测试汇总:")
    print(f"   总请求: {total_requests}")
    print(f"   总成功: {total_success}")
    print(f"   成功率: {total_success/total_requests*100:.1f}%")

def test_admin_apis(token):
    """测试管理员API"""
    print_header("🔧 管理员API并发测试")
    
    admin_apis = [
        ("用户管理", "GET", "/api/admin/users", None),
        ("统计数据", "GET", "/api/admin/stats", None),
        ("报告管理", "GET", "/api/admin/reports", None),
        ("积分管理", "GET", "/api/admin/integral", None),
        ("上传管理", "GET", "/api/admin/uploads", None),
        ("反馈管理", "GET", "/api/admin/feedback", None),
        ("系统设置", "GET", "/api/admin/settings", None),
    ]
    
    total_success = 0
    total_requests = 0
    
    for name, method, endpoint, data in admin_apis:
        success, _ = test_api_concurrent(token, "管理员", method, endpoint, data, name)
        total_success += success
        total_requests += CONCURRENT_REQUESTS
    
    print(f"\n📊 管理员API汇总:")
    print(f"   总请求: {total_requests}")
    print(f"   总成功: {total_success}")
    print(f"   成功率: {total_success/total_requests*100:.1f}%")

def test_mixed_workload(token):
    """混合负载测试"""
    print_header("🎭 混合负载测试")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    def user_session(session_id):
        results = []
        actions = [
            ("GET", "/api/consult/sessions", None),
            ("GET", "/api/consult/profile", None),
            ("GET", "/api/integral/balance", None),
            ("GET", "/api/users/me", None),
            ("POST", "/api/consult", {"message": "深圳房价"}),
            ("GET", "/api/integral/history", None),
            ("GET", "/api/uploads/types", None),
        ]
        
        for _ in range(random.randint(5, 10)):
            method, endpoint, data = random.choice(actions)
            try:
                start = time.time()
                if method == "GET":
                    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                else:
                    r = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers, timeout=10)
                results.append((endpoint, r.status_code in [200, 201], time.time() - start))
            except:
                results.append((endpoint, False, 0))
        
        return results
    
    print(f"\n模拟 {CONCURRENT_REQUESTS} 个并发会话...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(user_session, i) for i in range(CONCURRENT_REQUESTS)]
        all_results = [f.result() for f in as_completed(futures)]
    
    total_time = time.time() - start_time
    
    total_requests = sum(len(r) for r in all_results)
    success_requests = sum(sum(1 for a in r if a[1]) for r in all_results)
    
    print(f"\n📊 混合负载结果:")
    print(f"   并发会话: {CONCURRENT_REQUESTS}")
    print(f"   总请求: {total_requests}")
    print(f"   成功请求: {success_requests}")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功率: {success_requests/total_requests*100:.1f}%")
    print(f"   系统QPS: {total_requests/total_time:.1f}")

def test_1000_requests(token):
    """1000请求压力测试"""
    print_header("🚀 1000请求压力测试")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    def make_request(req_id):
        try:
            start = time.time()
            r = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=10)
            return r.status_code == 200, time.time() - start
        except:
            return False, 0
    
    print(f"\n启动 {TOTAL_REQUESTS} 请求压力测试...")
    print(f"   每批并发: {CONCURRENT_REQUESTS}")
    
    start_time = time.time()
    all_results = []
    
    batches = TOTAL_REQUESTS // CONCURRENT_REQUESTS
    for batch in range(batches):
        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
            futures = [executor.submit(make_request, i) for i in range(CONCURRENT_REQUESTS)]
            batch_results = [f.result() for f in as_completed(futures)]
            all_results.extend(batch_results)
        
        print(f"   批次 {batch+1}/{batches} 完成")
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in all_results if r[0])
    avg_time = sum(r[1] for r in all_results) / len(all_results)
    
    print(f"\n📊 压力测试结果:")
    print(f"   总请求: {TOTAL_REQUESTS}")
    print(f"   成功: {success_count}")
    print(f"   失败: {TOTAL_REQUESTS - success_count}")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   平均响应: {avg_time*1000:.1f}毫秒")
    print(f"   系统QPS: {TOTAL_REQUESTS/total_time:.1f}")
    print(f"   成功率: {success_count/TOTAL_REQUESTS*100:.1f}%")

def main():
    print("\n" + "="*60)
    print(" 🚀 1000并发请求全面测试")
    print(" 📧 账号: 1558691995@qq.com")
    print("="*60)
    
    # 检查服务
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print("❌ 后端服务未就绪")
            return
        print("✅ 后端服务运行正常")
    except:
        print("❌ 无法连接后端服务")
        return
    
    # 登录获取Token
    print("\n🔐 登录获取Token...")
    token = get_token()
    if not token:
        print("❌ 登录失败")
        return
    print(f"✅ 登录成功, Token: {token[:50]}...")
    
    # 执行测试
    test_all_apis(token)
    test_admin_apis(token)
    test_mixed_workload(token)
    test_1000_requests(token)
    
    print("\n" + "="*60)
    print(" ✅ 所有并发测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()
