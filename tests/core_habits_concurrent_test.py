"""
核心功能习惯培养系统并发测试 - 简化版
"""
import asyncio
import httpx
import time
import random
import string
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"
CONCURRENT_USERS = 100

results = {
    "register_success": 0,
    "login_success": 0,
    "task_analysis_report": 0,
    "consult_report": 0,
    "stats_success": 0,
    "errors": [],
    "response_times": [],
}


def generate_random_email():
    chars = string.ascii_lowercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(8))
    return f"perf_{random_str}@test.com"


async def test_user_flow(user_id: int):
    """测试单个用户流程"""
    email = generate_random_email()
    password = "Test123456!"
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": email, "password": password, "full_name": f"测试用户{user_id}"},
                timeout=10.0
            )
            if resp.status_code in [201, 409]:
                results["register_success"] += 1
            
            resp = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10.0
            )
            
            if resp.status_code != 200:
                results["errors"].append(f"用户{user_id}: 登录失败")
                return
            
            results["login_success"] += 1
            token = resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = await client.post(
                f"{BASE_URL}/api/habit/usage/task-analysis",
                json={},
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                results["task_analysis_report"] += 1
            else:
                if len(results["errors"]) < 10:
                    results["errors"].append(f"用户{user_id}: 任务分析上报失败 {resp.status_code}")
            
            resp = await client.post(
                f"{BASE_URL}/api/habit/usage/intelligent-consult",
                json={},
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                results["consult_report"] += 1
            
            resp = await client.get(
                f"{BASE_URL}/api/habit/stats",
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                results["stats_success"] += 1
            
            end_time = time.time()
            results["response_times"].append(end_time - start_time)
            
        except Exception as e:
            if len(results["errors"]) < 10:
                results["errors"].append(f"用户{user_id}: {str(e)}")


async def run_concurrent_test():
    """运行并发测试"""
    print(f"\n{'='*60}")
    print(f"核心功能习惯培养系统 {CONCURRENT_USERS} 用户并发测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    tasks = [test_user_flow(i) for i in range(CONCURRENT_USERS)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    total_requests = (
        results["register_success"] + results["login_success"] + 
        results["task_analysis_report"] + results["consult_report"] +
        results["stats_success"]
    )
    
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    print(f"并发用户数: {CONCURRENT_USERS}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"总请求数: {total_requests}")
    
    if results['response_times']:
        avg_time = sum(results['response_times']) / len(results['response_times'])
        max_time = max(results['response_times'])
        min_time = min(results['response_times'])
        print(f"平均响应时间: {avg_time:.3f} 秒")
        print(f"最大响应时间: {max_time:.3f} 秒")
        print(f"最小响应时间: {min_time:.3f} 秒")
    
    qps = total_requests / total_time if total_time > 0 else 0
    print(f"系统QPS: {qps:.2f}")
    
    print(f"\n功能测试结果:")
    print(f"  注册成功: {results['register_success']}")
    print(f"  登录成功: {results['login_success']}")
    print(f"  任务分析上报成功: {results['task_analysis_report']}")
    print(f"  智能咨询上报成功: {results['consult_report']}")
    print(f"  获取统计成功: {results['stats_success']}")
    
    success_rate = (total_requests / (CONCURRENT_USERS * 5)) * 100 if CONCURRENT_USERS > 0 else 0
    print(f"\n成功率: {success_rate:.2f}%")
    
    if results['errors']:
        print(f"\n错误示例:")
        for error in results['errors'][:5]:
            print(f"  - {error}")
    
    print(f"\n{'='*60}")


if __name__ == "__main__":
    asyncio.run(run_concurrent_test())
