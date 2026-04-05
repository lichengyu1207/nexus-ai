"""
签到功能并发测试 - 验证优化效果
"""
import asyncio
import httpx
import time
import random
import string
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
CONCURRENT_USERS = 50

results = {
    "signin_success": 0,
    "signin_already": 0,
    "signin_failed": 0,
    "errors": [],
}


def generate_random_email():
    chars = string.ascii_lowercase + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(8))
    return f"opt2_{random_str}@test.com"


async def test_signin(user_id: int):
    """测试签到"""
    email = generate_random_email()
    password = "Test123456!"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            await client.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": email, "password": password, "full_name": f"测试用户{user_id}"},
                timeout=10.0
            )
            
            resp = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10.0
            )
            
            if resp.status_code != 200:
                results["signin_failed"] += 1
                return
            
            token = resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = await client.post(f"{BASE_URL}/api/habit/signin", headers=headers, timeout=15.0)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    results["signin_success"] += 1
                else:
                    results["signin_already"] += 1
            else:
                results["signin_failed"] += 1
                if len(results["errors"]) < 5:
                    results["errors"].append(f"用户{user_id}: HTTP {resp.status_code}")
            
        except Exception as e:
            results["signin_failed"] += 1
            if len(results["errors"]) < 5:
                results["errors"].append(f"用户{user_id}: {str(e)}")


async def main():
    print(f"\n{'='*50}")
    print(f"签到功能并发测试 ({CONCURRENT_USERS}用户)")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    start_time = time.time()
    
    tasks = [test_signin(i) for i in range(CONCURRENT_USERS)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    total = results["signin_success"] + results["signin_already"] + results["signin_failed"]
    success_rate = ((results["signin_success"] + results["signin_already"]) / total * 100) if total > 0 else 0
    
    print(f"\n{'='*50}")
    print("测试结果")
    print(f"{'='*50}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"签到成功: {results['signin_success']}")
    print(f"已签到过: {results['signin_already']}")
    print(f"签到失败: {results['signin_failed']}")
    print(f"成功率: {success_rate:.2f}%")
    print(f"QPS: {total / total_time:.2f}" if total_time > 0 else "QPS: N/A")
    
    if results["errors"]:
        print(f"\n错误示例:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(main())
