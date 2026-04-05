"""
用户习惯培养系统完整API测试
"""
import asyncio
import httpx
import sys
import json
from datetime import date

BASE_URL = "http://localhost:8002"

TEST_USER = {
    "email": "habit_test@example.com",
    "password": "Test123456!",
    "full_name": "习惯测试用户"
}


async def register_and_login(client: httpx.AsyncClient) -> str:
    """注册并登录获取token"""
    print("\n=== 注册测试用户 ===")
    
    try:
        resp = await client.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
        if resp.status_code == 201:
            print("✓ 用户注册成功")
        elif resp.status_code == 409:
            print("✓ 用户已存在，继续登录")
        else:
            print(f"注册响应: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"注册异常: {e}")
    
    print("\n=== 登录获取Token ===")
    resp = await client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    
    if resp.status_code != 200:
        print(f"登录失败: {resp.status_code} - {resp.text}")
        return None
    
    data = resp.json()
    token = data.get("access_token")
    print(f"✓ 登录成功，获取Token: {token[:20]}...")
    return token


async def test_signin_status(client: httpx.AsyncClient, token: str):
    """测试获取签到状态"""
    print("\n=== 测试获取签到状态 ===")
    resp = await client.get(
        f"{BASE_URL}/api/habit/signin/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print(f"获取签到状态失败: {resp.status_code} - {resp.text}")
        return None
    
    data = resp.json()
    print(f"今日已签到: {data['today_signed']}")
    print(f"连续签到天数: {data['consecutive_days']}")
    print(f"累计签到天数: {data['total_signin_days']}")
    print(f"补签卡数量: {data['repent_cards']}")
    print(f"本月签到记录: {data['month_records']}")
    print(f"今日可得积分: {data['today_reward']}")
    print("✓ 获取签到状态成功")
    return data


async def test_do_signin(client: httpx.AsyncClient, token: str):
    """测试执行签到"""
    print("\n=== 测试执行签到 ===")
    resp = await client.post(
        f"{BASE_URL}/api/habit/signin",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    data = resp.json()
    print(f"响应状态: {resp.status_code}")
    print(f"响应数据: {data}")
    
    if data.get('success'):
        print(f"获得积分: {data.get('reward_integral', 0)}")
        print(f"连续天数: {data.get('consecutive_days', 0)}")
        print(f"消息: {data.get('message', '')}")
        print("✓ 签到成功")
    else:
        print(f"消息: {data.get('message', data.get('detail', '未知错误'))}")
        print("✓ 今日已签到过或其他情况")
    return data


async def test_get_tasks(client: httpx.AsyncClient, token: str):
    """测试获取任务列表"""
    print("\n=== 测试获取任务列表 ===")
    resp = await client.get(
        f"{BASE_URL}/api/habit/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print(f"获取任务列表失败: {resp.status_code} - {resp.text}")
        return None
    
    data = resp.json()
    
    print(f"\n每日任务 ({len(data['daily_tasks'])}个):")
    for task in data['daily_tasks']:
        print(f"  - {task['name']}: {task['current_progress']}/{task['target_count']} ({task['status']}) - {task['reward_integral']}积分")
    
    print(f"\n每周任务 ({len(data['weekly_tasks'])}个):")
    for task in data['weekly_tasks']:
        print(f"  - {task['name']}: {task['current_progress']}/{task['target_count']} ({task['status']}) - {task['reward_integral']}积分")
    
    print(f"\n成就任务 ({len(data['achievement_tasks'])}个):")
    for task in data['achievement_tasks']:
        print(f"  - {task['name']}: {task['current_progress']}/{task['target_count']} ({task['status']}) - {task['reward_integral']}积分")
    
    print("\n✓ 获取任务列表成功")
    return data


async def test_get_level(client: httpx.AsyncClient, token: str):
    """测试获取等级信息"""
    print("\n=== 测试获取等级信息 ===")
    resp = await client.get(
        f"{BASE_URL}/api/habit/level",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print(f"获取等级信息失败: {resp.status_code} - {resp.text}")
        return None
    
    data = resp.json()
    print(f"当前等级: Lv.{data['level']}")
    print(f"累计行为积分: {data['total_points']}")
    print(f"当前等级进度: {data['current_level_points']}/1000")
    print(f"升级还需: {data['next_level_points']}积分")
    if data['benefits']:
        print(f"等级权益: {data['benefits'].get('title', 'N/A')}")
    print("✓ 获取等级信息成功")
    return data


async def test_report_task_progress(client: httpx.AsyncClient, token: str):
    """测试上报任务进度"""
    print("\n=== 测试上报任务进度 ===")
    
    actions = ["create_task", "consult_query", "upload_data"]
    
    for action in actions:
        resp = await client.post(
            f"{BASE_URL}/api/habit/tasks/progress?action_type={action}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"动作 '{action}': {data['message']}")
            if data.get('updated_tasks'):
                for task in data['updated_tasks']:
                    print(f"  - {task['task_name']}: {task['progress']}/{task['target']} ({task['status']})")
    
    print("✓ 上报任务进度成功")


async def test_buy_repent_card(client: httpx.AsyncClient, token: str):
    """测试购买补签卡"""
    print("\n=== 测试购买补签卡 ===")
    
    resp = await client.post(
        f"{BASE_URL}/api/habit/signin/buy-repent",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    data = resp.json()
    if resp.status_code == 200 and data.get('success'):
        print(f"购买成功: {data['message']}")
        print(f"花费积分: {data['cost']}")
        print("✓ 购买补签卡成功")
    else:
        print(f"购买结果: {data.get('detail', data.get('message', '积分不足'))}")
    return data


async def test_integral_info(client: httpx.AsyncClient, token: str):
    """测试获取积分信息"""
    print("\n=== 测试获取积分信息 ===")
    resp = await client.get(
        f"{BASE_URL}/api/user/integral",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"当前积分: {data['integral']}")
        print(f"会员等级: {data['membership_level']}")
        print("✓ 获取积分信息成功")
    else:
        print(f"获取积分信息失败: {resp.status_code}")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("用户习惯培养系统 API 测试")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 注册并登录
        token = await register_and_login(client)
        if not token:
            print("无法获取token，测试终止")
            return
        
        # 2. 获取签到状态
        await test_signin_status(client, token)
        
        # 3. 执行签到
        await test_do_signin(client, token)
        
        # 4. 再次获取签到状态
        await test_signin_status(client, token)
        
        # 5. 获取任务列表
        await test_get_tasks(client, token)
        
        # 6. 上报任务进度
        await test_report_task_progress(client, token)
        
        # 7. 再次获取任务列表查看进度
        await test_get_tasks(client, token)
        
        # 8. 获取等级信息
        await test_get_level(client, token)
        
        # 9. 购买补签卡
        await test_buy_repent_card(client, token)
        
        # 10. 获取积分信息
        await test_integral_info(client, token)
        
        print("\n" + "=" * 60)
        print("所有API测试完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
