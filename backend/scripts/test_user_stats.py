"""
测试用户统计API
"""
import asyncio
import aiohttp

async def test_user_stats():
    print("=" * 60)
    print("测试用户统计API")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 登录
        print("\n1. 登录...")
        login_data = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
        async with session.post("http://localhost:8000/api/auth/login", json=login_data) as resp:
            print(f"   状态: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                token = data.get("access_token")
                print(f"   Token: {token[:20]}...")
            else:
                print(f"   错误: {await resp.text()}")
                return
        
        # 测试用户统计API
        print("\n2. 获取用户统计...")
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get("http://localhost:8000/api/users/me/stats", headers=headers) as resp:
            print(f"   状态: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"   数据: {data}")
            else:
                print(f"   错误: {await resp.text()}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_user_stats())
