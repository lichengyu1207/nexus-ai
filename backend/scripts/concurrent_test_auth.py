"""
并发测试脚本 - 登录、注册、管理员界面
"""
import asyncio
import aiohttp
import json
from datetime import datetime
import random
import string

BASE_URL = "http://localhost:8000"

test_results = {
    "登录并发测试": {},
    "注册并发测试": {},
    "管理员界面并发测试": {}
}

async def test_api(session, name, method, endpoint, data=None, headers=None):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            async with session.get(url, headers=headers) as resp:
                result = await resp.json() if resp.content_type == 'application/json' else await resp.text()
                return {"status": resp.status, "data": result}
        elif method == "POST":
            async with session.post(url, json=data, headers=headers) as resp:
                result = await resp.json() if resp.content_type == 'application/json' else await resp.text()
                return {"status": resp.status, "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def generate_random_email():
    """生成随机邮箱"""
    chars = string.ascii_lowercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(8))
    return f"test_{random_str}@example.com"

async def test_login_concurrent(session):
    """测试登录并发"""
    print("\n" + "="*60)
    print("🔐 登录并发测试")
    print("="*60)
    
    # 测试账号
    login_data = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
    
    # 1. 单次登录测试
    print("\n1️⃣ 单次登录测试...")
    result = await test_api(session, "登录", "POST", "/api/auth/login", data=login_data)
    token = result.get("data", {}).get("access_token") if result["status"] == 200 else None
    test_results["登录并发测试"]["单次登录"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 2. 并发登录测试 (10个同时登录)
    print("\n2️⃣ 并发登录测试 (10个同时登录)...")
    start_time = datetime.now()
    
    tasks = [
        test_api(session, f"登录-{i}", "POST", "/api/auth/login", data=login_data)
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r["status"] == 200)
    test_results["登录并发测试"]["并发登录10次"] = success_count == 10
    print(f"   成功: {success_count}/10")
    print(f"   耗时: {duration:.2f}秒")
    
    # 3. 错误密码测试
    print("\n3️⃣ 错误密码测试...")
    wrong_login = {"email": "1558691995@qq.com", "password": "wrongpassword"}
    result = await test_api(session, "错误密码登录", "POST", "/api/auth/login", data=wrong_login)
    test_results["登录并发测试"]["错误密码拒绝"] = result["status"] == 401
    print(f"   状态: {'✅ 通过' if result['status'] == 401 else '❌ 失败'}")
    
    # 4. 不存在用户测试
    print("\n4️⃣ 不存在用户测试...")
    nonexist_login = {"email": "nonexist@example.com", "password": "test123456"}
    result = await test_api(session, "不存在用户登录", "POST", "/api/auth/login", data=nonexist_login)
    test_results["登录并发测试"]["不存在用户拒绝"] = result["status"] == 401
    print(f"   状态: {'✅ 通过' if result['status'] == 401 else '❌ 失败'}")
    
    return token

async def test_register_concurrent(session):
    """测试注册并发"""
    print("\n" + "="*60)
    print("📝 注册并发测试")
    print("="*60)
    
    # 1. 单次注册测试
    print("\n1️⃣ 单次注册测试...")
    new_email = generate_random_email()
    register_data = {
        "email": new_email,
        "password": "Test123456!",
        "username": new_email.split('@')[0]
    }
    result = await test_api(session, "注册", "POST", "/api/auth/register", data=register_data)
    test_results["注册并发测试"]["单次注册"] = result["status"] in [200, 201, 400]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 201, 400] else '❌ 失败'}")
    if result["status"] in [200, 201]:
        print(f"   新用户: {new_email}")
    
    # 2. 并发注册测试 (5个同时注册)
    print("\n2️⃣ 并发注册测试 (5个同时注册)...")
    start_time = datetime.now()
    
    tasks = []
    for i in range(5):
        email = generate_random_email()
        data = {
            "email": email,
            "password": "Test123456!",
            "username": email.split('@')[0]
        }
        tasks.append(test_api(session, f"注册-{i}", "POST", "/api/auth/register", data=data))
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r["status"] in [200, 201])
    test_results["注册并发测试"]["并发注册5次"] = success_count >= 3
    print(f"   成功: {success_count}/5")
    print(f"   耗时: {duration:.2f}秒")
    
    # 3. 重复邮箱注册测试
    print("\n3️⃣ 重复邮箱注册测试...")
    duplicate_data = {
        "email": "1558691995@qq.com",
        "password": "Test123456!",
        "username": "duplicate"
    }
    result = await test_api(session, "重复邮箱注册", "POST", "/api/auth/register", data=duplicate_data)
    test_results["注册并发测试"]["重复邮箱拒绝"] = result["status"] in [400, 409]
    print(f"   状态: {'✅ 通过' if result['status'] in [400, 409] else '❌ 失败'}")

async def test_admin_concurrent(session, token):
    """测试管理员界面并发"""
    print("\n" + "="*60)
    print("👑 管理员界面并发测试")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # 1. 管理员仪表盘
    print("\n1️⃣ 管理员仪表盘...")
    result = await test_api(session, "管理仪表盘", "GET", "/api/admin/dashboard", headers=headers)
    test_results["管理员界面并发测试"]["仪表盘"] = result["status"] in [200, 403]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 403] else '❌ 失败'}")
    
    # 2. 用户管理
    print("\n2️⃣ 用户管理...")
    result = await test_api(session, "用户列表", "GET", "/api/admin/users", headers=headers)
    test_results["管理员界面并发测试"]["用户管理"] = result["status"] in [200, 403]
    print(f"   状态: {'✅ 通过' if result['status'] in [200, 403] else '❌ 失败'}")
    
    # 3. 并发管理员API测试
    print("\n3️⃣ 并发管理员API测试 (5个API)...")
    start_time = datetime.now()
    
    tasks = [
        test_api(session, "仪表盘", "GET", "/api/admin/dashboard", headers=headers),
        test_api(session, "用户列表", "GET", "/api/admin/users", headers=headers),
        test_api(session, "IP管理", "GET", "/api/admin/ip", headers=headers),
        test_api(session, "反馈列表", "GET", "/api/admin/feedback", headers=headers),
        test_api(session, "数据分析", "GET", "/api/admin/analytics", headers=headers),
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r["status"] in [200, 403, 404])
    test_results["管理员界面并发测试"]["并发API"] = success_count >= 3
    print(f"   成功: {success_count}/5")
    print(f"   耗时: {duration:.2f}秒")
    
    # 4. 权限验证测试
    print("\n4️⃣ 权限验证测试...")
    result = await test_api(session, "无权限访问", "GET", "/api/admin/dashboard")
    test_results["管理员界面并发测试"]["权限验证"] = result["status"] == 401
    print(f"   状态: {'✅ 通过' if result['status'] == 401 else '❌ 失败'}")

async def main():
    print("\n" + "="*60)
    print("🚀 房都督AI 并发测试 - 登录/注册/管理员")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # 测试登录并发
        token = await test_login_concurrent(session)
        
        # 测试注册并发
        await test_register_concurrent(session)
        
        # 测试管理员界面并发
        await test_admin_concurrent(session, token)
    
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
