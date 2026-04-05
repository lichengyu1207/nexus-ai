"""
测试对比分析API
"""
import asyncio
import aiohttp

async def test_compare():
    async with aiohttp.ClientSession() as session:
        # 登录
        print("1. 登录...")
        login_data = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
        async with session.post("http://localhost:8000/api/auth/login", json=login_data) as resp:
            data = await resp.json()
            token = data.get("access_token")
            print(f"   Token: {token[:20]}...")
        
        # 测试对比分析
        print("\n2. 测试对比分析...")
        headers = {"Authorization": f"Bearer {token}"}
        compare_data = {
            "locations": [
                {"address": "上海市浦东新区陆家嘴"},
                {"address": "上海市浦东新区张江"}
            ]
        }
        
        async with session.post("http://localhost:8000/api/compare", json=compare_data, headers=headers) as resp:
            print(f"   状态: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"   数据: {data}")
            else:
                text = await resp.text()
                print(f"   错误: {text}")

asyncio.run(test_compare())
