"""
并发测试脚本 - 测试核心功能和辅助功能
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5174"

# 测试结果存储
test_results = {
    "核心功能": {},
    "辅助功能": {},
    "并发测试": {}
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

async def test_core_features(session):
    """测试核心功能"""
    print("\n" + "="*50)
    print("🔍 测试核心功能")
    print("="*50)
    
    # 1. 健康检查
    print("\n1️⃣ 健康检查...")
    result = await test_api(session, "健康检查", "GET", "/health")
    test_results["核心功能"]["健康检查"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 2. 用户认证 - 登录
    print("\n2️⃣ 用户认证 - 登录...")
    login_data = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
    result = await test_api(session, "登录", "POST", "/api/auth/login", data=login_data)
    token = result.get("data", {}).get("access_token") if result["status"] == 200 else None
    test_results["核心功能"]["登录"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # 3. 获取用户信息
    if token:
        print("\n3️⃣ 获取用户信息...")
        result = await test_api(session, "用户信息", "GET", "/api/auth/me", headers=headers)
        test_results["核心功能"]["用户信息"] = result["status"] == 200
        print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 4. 房产分析任务
    if token:
        print("\n4️⃣ 创建房产分析任务...")
        task_data = {"query": "上海市浦东新区陆家嘴"}
        result = await test_api(session, "创建任务", "POST", "/api/tasks", data=task_data, headers=headers)
        task_id = result.get("data", {}).get("id") if result["status"] == 200 else None
        test_results["核心功能"]["创建任务"] = result["status"] == 200
        print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 5. IP工作台
    if token:
        print("\n5️⃣ IP工作台...")
        result = await test_api(session, "IP仪表盘", "GET", "/api/ip/dashboard", headers=headers)
        test_results["核心功能"]["IP工作台"] = result["status"] in [200, 400]
        print(f"   状态: {'✅ 通过' if result['status'] in [200, 400] else '❌ 失败'}")
    
    return token

async def test_auxiliary_features(session, token=None):
    """测试辅助功能"""
    print("\n" + "="*50)
    print("🔧 测试辅助功能")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # 1. 资讯中心 - 文章列表
    print("\n1️⃣ 资讯中心 - 文章列表...")
    result = await test_api(session, "文章列表", "GET", "/api/articles")
    articles = result.get("data", {}).get("articles", []) if result["status"] == 200 else []
    test_results["辅助功能"]["文章列表"] = result["status"] == 200
    print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    print(f"   文章数量: {len(articles)}")
    
    # 2. 文章详情
    if articles:
        print("\n2️⃣ 文章详情...")
        article_id = articles[0].get("id")
        if article_id:
            result = await test_api(session, "文章详情", "GET", f"/api/articles/{article_id}")
            test_results["辅助功能"]["文章详情"] = result["status"] == 200
            print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 3. 反馈系统
    if token:
        print("\n3️⃣ 反馈系统...")
        feedback_data = {
            "type": "general",
            "content": "这是一条测试反馈",
            "rating": 5
        }
        result = await test_api(session, "提交反馈", "POST", "/api/feedback/submit", data=feedback_data, headers=headers)
        test_results["辅助功能"]["反馈系统"] = result["status"] == 200
        print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")
    
    # 4. 管理员后台 - 仪表盘
    if token:
        print("\n4️⃣ 管理员后台 - 仪表盘...")
        result = await test_api(session, "管理仪表盘", "GET", "/api/admin/dashboard", headers=headers)
        test_results["辅助功能"]["管理仪表盘"] = result["status"] in [200, 403]
        print(f"   状态: {'✅ 通过' if result['status'] in [200, 403] else '❌ 失败'}")
    
    # 5. 用户统计
    if token:
        print("\n5️⃣ 用户统计...")
        result = await test_api(session, "用户统计", "GET", "/api/users/me/stats", headers=headers)
        test_results["辅助功能"]["用户统计"] = result["status"] == 200
        print(f"   状态: {'✅ 通过' if result['status'] == 200 else '❌ 失败'}")

async def test_concurrent_requests(session, token=None):
    """测试并发请求"""
    print("\n" + "="*50)
    print("⚡ 并发测试")
    print("="*50)
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # 并发测试：同时发送10个请求
    print("\n1️⃣ 并发健康检查 (10个请求)...")
    start_time = datetime.now()
    
    tasks = [
        test_api(session, f"健康检查-{i}", "GET", "/health")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r["status"] == 200)
    test_results["并发测试"]["健康检查并发"] = success_count == 10
    print(f"   成功: {success_count}/10")
    print(f"   耗时: {duration:.2f}秒")
    
    # 并发测试：同时获取多个API
    if token:
        print("\n2️⃣ 并发API请求 (5个不同API)...")
        start_time = datetime.now()
        
        tasks = [
            test_api(session, "用户信息", "GET", "/api/auth/me", headers=headers),
            test_api(session, "文章列表", "GET", "/api/articles"),
            test_api(session, "用户统计", "GET", "/api/users/me/stats", headers=headers),
            test_api(session, "IP仪表盘", "GET", "/api/ip/dashboard", headers=headers),
            test_api(session, "管理仪表盘", "GET", "/api/admin/dashboard", headers=headers),
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        success_count = sum(1 for r in results if r["status"] in [200, 400, 403])
        test_results["并发测试"]["多API并发"] = success_count == 5
        print(f"   成功: {success_count}/5")
        print(f"   耗时: {duration:.2f}秒")

async def main():
    """主测试函数"""
    print("\n" + "="*50)
    print("🚀 房都督AI 并发测试")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        # 测试核心功能
        token = await test_core_features(session)
        
        # 测试辅助功能
        await test_auxiliary_features(session, token)
        
        # 并发测试
        await test_concurrent_requests(session, token)
    
    # 打印测试结果汇总
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    for category, results in test_results.items():
        print(f"\n{category}:")
        for test, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"   {test}: {status}")
    
    # 计算总体通过率
    total_tests = sum(len(r) for r in test_results.values())
    passed_tests = sum(sum(1 for v in r.values() if v) for r in test_results.values())
    
    print(f"\n{'='*50}")
    print(f"📈 总体通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
