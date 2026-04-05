"""
用户习惯培养系统并发测试 - 快速版
"""
import asyncio
import httpx
import time
import random
import string
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
CONCURRENT_USERS = 100

results = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "signin_success": 0,
    "signin_failed": 0,
    "task_progress_success": 0,
    "level_success": 0,
    "register_success": 0,
    "login_success": 0,
    "errors": [],
}


def generate_random_email():
    chars = string.ascii_lowercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(8))
    return f"opt_{random_str}@test.com"


async def test_user_flow(user_id: int):
    """测试单个用户流程"""
    email = generate_random_email()
    password = "Test123456!"
    
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
                results["failed_requests"] += 1
                return
            
            results["login_success"] += 1
            token = resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = await client.get(f"{BASE_URL}/api/habit/signin/status", headers=headers, timeout=10.0)
            results["total_requests"] += 1
            if resp.status_code == 200:
                results["successful_requests"] += 1
            
            resp = await client.post(f"{BASE_URL}/api/habit/signin", headers=headers, timeout=15.0)
            results["total_requests"] += 1
            if resp.status_code == 200:
                data = resp.json()
                results["successful_requests"] += 1
                if data.get("success"):
                    results["signin_success"] += 1
                else:
                    results["signin_failed"] += 1
            else:
                results["failed_requests"] += 1
                results["signin_failed"] += 1
            
            actions = ["create_task", "consult_query", "upload_data"]
            action = random.choice(actions)
            resp = await client.post(
                f"{BASE_URL}/api/habit/tasks/progress?action_type={action}",
                headers=headers,
                timeout=10.0
            )
            results["total_requests"] += 1
            if resp.status_code == 200:
                results["successful_requests"] += 1
                results["task_progress_success"] += 1
            else:
                results["failed_requests"] += 1
            
            resp = await client.get(f"{BASE_URL}/api/habit/level", headers=headers, timeout=10.0)
            results["total_requests"] += 1
            if resp.status_code == 200:
                results["successful_requests"] += 1
                results["level_success"] += 1
            else:
                results["failed_requests"] += 1
            
        except Exception as e:
            results["failed_requests"] += 1
            if len(results["errors"]) < 10:
                results["errors"].append(f"用户{user_id}: {str(e)}")


async def run_concurrent_test():
    """运行并发测试"""
    print(f"\n{'='*60}")
    print(f"用户习惯培养系统 {CONCURRENT_USERS} 用户并发测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    tasks = [test_user_flow(i) for i in range(CONCURRENT_USERS)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    print(f"并发用户数: {CONCURRENT_USERS}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"总请求数: {results['total_requests']}")
    print(f"成功请求数: {results['successful_requests']}")
    print(f"失败请求数: {results['failed_requests']}")
    
    if results['total_requests'] > 0:
        success_rate = (results['successful_requests'] / results['total_requests']) * 100
        print(f"成功率: {success_rate:.2f}%")
    else:
        success_rate = 0
        print(f"成功率: 0%")
    
    qps = results['total_requests'] / total_time if total_time > 0 else 0
    print(f"系统QPS: {qps:.2f}")
    
    print(f"\n功能测试结果:")
    print(f"  注册成功: {results['register_success']}")
    print(f"  登录成功: {results['login_success']}")
    print(f"  签到成功: {results['signin_success']}")
    print(f"  签到失败: {results['signin_failed']}")
    print(f"  任务进度上报成功: {results['task_progress_success']}")
    print(f"  等级查询成功: {results['level_success']}")
    
    if results['errors']:
        print(f"\n错误示例:")
        for error in results['errors'][:5]:
            print(f"  - {error}")
    
    print(f"\n{'='*60}")
    
    return {
        "success_rate": success_rate,
        "qps": qps,
    }


if __name__ == "__main__":
    asyncio.run(run_concurrent_test())
