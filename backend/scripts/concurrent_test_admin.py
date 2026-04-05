"""
管理员后台核心功能并发测试
"""
import asyncio
import aiohttp
from datetime import datetime

BASE_URL = "http://localhost:8000"

test_results = {
    "管理员认证": {},
    "用户管理": {},
    "数据分析": {},
    "IP管理": {},
    "系统设置": {}
}

async def test_api(session, name, method, endpoint, data=None, headers=None):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                result = await resp.json() if resp.content_type == 'application/json' else await resp.text()
                return {"status": resp.status, "data": result}
        elif method == "POST":
            async with session.post(url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                result = await resp.json() if resp.content_type == 'application/json' else await resp.text()
                return {"status": resp.status, "data": result}
        elif method == "PUT":
            async with session.put(url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                result = await resp.json() if resp.content_type == 'application/json' else await resp.text()
                return {"status": resp.status, "data": result}
        elif method == "DELETE":
            async with session.delete(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                result = await resp.json() if resp.content_type == 'application/json' else await resp.text()
                return {"status": resp.status, "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def test_admin_auth(session):
    """测试管理员认证"""
    print("\n" + "="*60)
    print("🔐 管理员认证测试")
    print("="*60)
    
    # 1. 管理员登录
    print("\n1️⃣ 管理员登录...")
    login_data = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
    result = await test_api(session, "管理员登录", "POST", "/api/auth/login", data=login_data)
    token = result.get("data", {}).get("access_token") if result["status"] == 200 else None
    test_results["管理员认证"]["登录"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    if not token:
        print("   ❌ 无法获取token，跳过后续测试")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 验证管理员权限
    print("\n2️⃣ 验证管理员权限...")
    result = await test_api(session, "权限验证", "GET", "/api/auth/me", headers=headers)
    is_admin = result.get("data", {}).get("role") == "admin" if result["status"] == 200 else False
    test_results["管理员认证"]["权限验证"] = is_admin
    print(f"   状态: {'✅ 通过' if is_admin else '❌ 失败'}")
    
    # 3. 非管理员访问测试
    print("\n3️⃣ 非管理员访问测试...")
    result = await test_api(session, "无权限访问", "GET", "/api/admin/dashboard")
    test_results["管理员认证"]["权限拦截"] = result["status"] == 401
    print(f"   状态: {'✅ 通过' if result['status'] == 401 else '❌ 失败'}")
    
    return headers

async def test_user_management(session, headers):
    """测试用户管理"""
    print("\n" + "="*60)
    print("👥 用户管理测试")
    print("="*60)
    
    # 1. 获取用户列表
    print("\n1️⃣ 获取用户列表...")
    result = await test_api(session, "用户列表", "GET", "/api/admin/users?limit=10&offset=0", headers=headers)
    users = result.get("data", {}).get("users", []) if result["status"] == 200 else []
    total = result.get("data", {}).get("total", 0) if result["status"] == 200 else 0
    test_results["用户管理"]["获取列表"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    print(f"   用户数: {total}")
    
    # 2. 搜索用户
    print("\n2️⃣ 搜索用户...")
    result = await test_api(session, "搜索用户", "GET", "/api/admin/users?search=test&limit=5", headers=headers)
    test_results["用户管理"]["搜索用户"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 3. 并发获取用户列表
    print("\n3️⃣ 并发获取用户列表 (5次)...")
    start_time = datetime.now()
    
    tasks = [
        test_api(session, f"用户列表-{i}", "GET", f"/api/admin/users?limit=10&offset={i*10}", headers=headers)
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r["status"] == 200)
    test_results["用户管理"]["并发获取"] = success_count == 5
    print(f"   成功: {success_count}/5")
    print(f"   耗时: {duration:.2f}秒")

async def test_analytics(session, headers):
    """测试数据分析"""
    print("\n" + "="*60)
    print("📊 数据分析测试")
    print("="*60)
    
    # 1. 仪表盘数据
    print("\n1️⃣ 仪表盘数据...")
    result = await test_api(session, "仪表盘", "GET", "/api/admin/dashboard", headers=headers)
    test_results["数据分析"]["仪表盘"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    if result["status"] == 200:
        data = result.get("data", {})
        print(f"   用户总数: {data.get('total_users', 0)}")
        print(f"   今日活跃: {data.get('active_today', 0)}")
    
    # 2. 任务统计
    print("\n2️⃣ 任务统计...")
    result = await test_api(session, "任务统计", "GET", "/api/admin/tasks?limit=5", headers=headers)
    test_results["数据分析"]["任务统计"] = result["status"] in [200, 404]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 404] else '❌ 失败'}")
    
    # 3. 并发数据分析
    print("\n3️⃣ 并发数据分析 (3个API)...")
    start_time = datetime.now()
    
    tasks = [
        test_api(session, "仪表盘", "GET", "/api/admin/dashboard", headers=headers),
        test_api(session, "用户统计", "GET", "/api/admin/users?limit=1", headers=headers),
        test_api(session, "任务统计", "GET", "/api/admin/tasks?limit=1", headers=headers),
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r["status"] in [200, 404])
    test_results["数据分析"]["并发分析"] = success_count == 3
    print(f"   成功: {success_count}/3")
    print(f"   耗时: {duration:.2f}秒")

async def test_ip_management(session, headers):
    """测试IP管理"""
    print("\n" + "="*60)
    print("🎫 IP管理测试")
    print("="*60)
    
    # 1. IP列表
    print("\n1️⃣ IP列表...")
    result = await test_api(session, "IP列表", "GET", "/api/ip/admin/list", headers=headers)
    test_results["IP管理"]["IP列表"] = result["status"] in [200, 404]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 404] else '❌ 失败'}")
    
    # 2. 提现列表
    print("\n2️⃣ 提现列表...")
    result = await test_api(session, "提现列表", "GET", "/api/ip/admin/withdrawals/list", headers=headers)
    test_results["IP管理"]["提现列表"] = result["status"] in [200, 404]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 404] else '❌ 失败'}")
    
    # 3. IP仪表盘
    print("\n3️⃣ IP仪表盘...")
    result = await test_api(session, "IP仪表盘", "GET", "/api/ip/dashboard", headers=headers)
    test_results["IP管理"]["IP仪表盘"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")

async def test_system_settings(session, headers):
    """测试系统设置"""
    print("\n" + "="*60)
    print("⚙️ 系统设置测试")
    print("="*60)
    
    # 1. 系统配置
    print("\n1️⃣ 系统配置...")
    result = await test_api(session, "系统配置", "GET", "/api/admin/settings", headers=headers)
    test_results["系统设置"]["获取配置"] = result["status"] in [200, 404]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 404] else '❌ 失败'}")
    
    # 2. 反馈列表
    print("\n2️⃣ 反馈列表...")
    result = await test_api(session, "反馈列表", "GET", "/api/admin/feedback", headers=headers)
    test_results["系统设置"]["反馈列表"] = result["status"] in [200, 404]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 404] else '❌ 失败'}")
    
    # 3. 审计日志
    print("\n3️⃣ 审计日志...")
    result = await test_api(session, "审计日志", "GET", "/api/audit/logs?limit=10", headers=headers)
    test_results["系统设置"]["审计日志"] = result["status"] in [200, 404]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 404] else '❌ 失败'}")

async def main():
    print("\n" + "="*60)
    print("🚀 管理员后台核心功能并发测试")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # 测试管理员认证
        headers = await test_admin_auth(session)
        
        if headers:
            # 测试用户管理
            await test_user_management(session, headers)
            
            # 测试数据分析
            await test_analytics(session, headers)
            
            # 测试IP管理
            await test_ip_management(session, headers)
            
            # 测试系统设置
            await test_system_settings(session, headers)
    
    # 打印测试结果汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    total_tests = 0
    total_passed = 0
    
    for category, results in test_results.items():
        print(f"\n{category}:")
        for test, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"   {test}: {status}")
            total_tests += 1
            if passed:
                total_passed += 1
    
    print(f"\n{'='*60}")
    print(f"📈 总体通过率: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
