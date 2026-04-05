"""
IP扶持计划 - 简化版API测试
"""
import urllib.request
import urllib.error
import json
import uuid

BASE_URL = "http://localhost:8000"

def make_request(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

def run_tests():
    print("\n" + "="*60)
    print("IP扶持计划 - 全周期可用性测试")
    print("="*60 + "\n")
    
    # 1. 健康检查
    print("1. 健康检查...")
    result = make_request("/health")
    if result.get("status") == "healthy":
        print("   ✅ 服务器健康")
    else:
        print("   ❌ 服务器异常")
        return
    
    # 2. 管理员登录
    print("\n2. 管理员登录...")
    result = make_request("/api/auth/login", "POST", {
        "email": "admin@fangtanai.com",
        "password": "147258@Zxcvbnm"
    })
    token = result.get("access_token")
    if token:
        print(f"   ✅ 登录成功, Token: {token[:20]}...")
    else:
        print(f"   ❌ 登录失败: {result}")
        return
    
    # 3. IP申请
    print("\n3. IP申请...")
    unique_id = str(uuid.uuid4())[:8]
    result = make_request("/api/ip/apply", "POST", {
        "name": f"测试IP_{unique_id}",
        "contact": f"wechat_{unique_id}",
        "email": f"ip_{unique_id}@test.com",
        "platform_type": "zhihu",
        "platform_id": f"zhihu_{unique_id}",
        "platform_name": "知乎测试账号",
        "followers": 50000,
        "introduction": "房产领域创作者"
    })
    application_id = result.get("application_id") or result.get("id")
    if application_id:
        print(f"   ✅ 申请成功, ID: {application_id}")
    else:
        print(f"   ⚠️ 申请结果: {result}")
    
    # 4. 获取IP申请列表
    print("\n4. 获取IP申请列表...")
    result = make_request("/api/admin/ip/applications", "GET", token=token)
    applications = result.get("applications", [])
    print(f"   ✅ 申请列表: {len(applications)} 条")
    
    # 5. 获取IP列表
    print("\n5. 获取IP列表...")
    result = make_request("/api/admin/ip", "GET", token=token)
    partners = result.get("partners", [])
    print(f"   ✅ IP列表: {len(partners)} 条")
    
    # 6. 获取IP等级
    print("\n6. 获取IP等级配置...")
    result = make_request("/api/ip/levels", "GET")
    levels = result.get("levels", [])
    print(f"   ✅ 等级配置: {len(levels)} 个等级")
    for level in levels:
        print(f"      - {level.get('level_name')}: {level.get('min_earnings')}元起")
    
    # 7. 获取佣金规则
    print("\n7. 获取佣金规则...")
    result = make_request("/api/ip/commission-rules", "GET")
    rules = result.get("rules", [])
    print(f"   ✅ 佣金规则: {len(rules)} 条")
    for rule in rules:
        print(f"      - {rule.get('name')}: {rule.get('commission_rate')}%")
    
    # 8. IP统计概览
    print("\n8. IP统计概览...")
    result = make_request("/api/admin/ip/stats/overview", "GET", token=token)
    print(f"   ✅ 总IP数: {result.get('total_ips', 0)}")
    print(f"      活跃IP: {result.get('active_ips', 0)}")
    print(f"      总佣金: {result.get('total_commissions', 0)}元")
    
    # 9. 获取提现列表
    print("\n9. 获取提现列表...")
    result = make_request("/api/admin/ip/withdrawals", "GET", token=token)
    withdrawals = result.get("withdrawals", [])
    print(f"   ✅ 提现记录: {len(withdrawals)} 条")
    
    # 10. 获取趋势数据
    print("\n10. 获取趋势数据...")
    result = make_request("/api/admin/ip/stats/trend", "GET", token=token)
    trend = result.get("trend", [])
    print(f"   ✅ 趋势数据: {len(trend)} 天")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    run_tests()
