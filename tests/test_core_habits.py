"""
任务分析与智能咨询的用户习惯培养系统测试
"""
import asyncio
import httpx
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"

results = {
    "register_success": 0,
    "login_success": 0,
    "task_analysis_report": 0,
    "consult_report": 0,
    "stats_success": 0,
    "goals_success": 0,
    "preferences_success": 0,
    "errors": [],
}


async def test_core_habits():
    """测试核心功能习惯系统"""
    print(f"\n{'='*60}")
    print(f"任务分析与智能咨询的用户习惯培养系统测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. 注册测试用户
            email = f"core_habit_{int(time.time())}@test.com"
            password = "Test123456!"
            
            resp = await client.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": email, "password": password, "full_name": "习惯测试用户"},
                timeout=10.0
            )
            if resp.status_code in [201, 409]:
                results["register_success"] += 1
                print(f"✓ 注册成功: {email}")
            
            # 2. 登录
            resp = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10.0
            )
            
            if resp.status_code != 200:
                results["errors"].append(f"登录失败: {resp.status_code}")
                return
            
            results["login_success"] += 1
            token = resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✓ 登录成功")
            
            # 3. 上报任务分析使用
            resp = await client.post(
                f"{BASE_URL}/api/habit/usage/task-analysis",
                json={},
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results["task_analysis_report"] += 1
                print(f"✓ 任务分析上报成功: 今日{data['data']['count']}次, 连续{data['data']['consecutive_days']}天")
            else:
                results["errors"].append(f"任务分析上报失败: {resp.status_code}")
            
            # 4. 上报智能咨询使用
            resp = await client.post(
                f"{BASE_URL}/api/habit/usage/intelligent-consult",
                json={},
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results["consult_report"] += 1
                print(f"✓ 智能咨询上报成功: 今日{data['data']['count']}次, 连续{data['data']['consecutive_days']}天")
            else:
                results["errors"].append(f"智能咨询上报失败: {resp.status_code}")
            
            # 5. 获取习惯统计
            resp = await client.get(
                f"{BASE_URL}/api/habit/stats",
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results["stats_success"] += 1
                print(f"✓ 获取统计成功:")
                print(f"  - 任务分析: 今日{data['task_analysis']['today_count']}次, 目标{data['task_analysis']['daily_goal']}次")
                print(f"  - 智能咨询: 今日{data['intelligent_consult']['today_count']}次, 目标{data['intelligent_consult']['daily_goal']}次")
            else:
                results["errors"].append(f"获取统计失败: {resp.status_code}")
            
            # 6. 设置目标
            resp = await client.put(
                f"{BASE_URL}/api/habit/goals",
                json={"task_analysis_daily_target": 10, "intelligent_consult_daily_target": 5},
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                results["goals_success"] += 1
                print(f"✓ 设置目标成功")
            else:
                results["errors"].append(f"设置目标失败: {resp.status_code}")
            
            # 7. 获取偏好设置
            resp = await client.get(
                f"{BASE_URL}/api/habit/preferences",
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results["preferences_success"] += 1
                print(f"✓ 获取偏好成功: 提醒{'开启' if data['reminder_enabled'] else '关闭'}, 时间{data['reminder_time']}")
            else:
                results["errors"].append(f"获取偏好失败: {resp.status_code}")
            
            # 8. 设置偏好
            resp = await client.put(
                f"{BASE_URL}/api/habit/preferences",
                json={"reminder_enabled": True, "reminder_time": "19:30"},
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                print(f"✓ 设置偏好成功")
            
            # 9. 获取使用历史
            resp = await client.get(
                f"{BASE_URL}/api/habit/history/task_analysis?days=7",
                headers=headers,
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"✓ 获取历史成功: {data['total_days']}天记录")
            
        except Exception as e:
            results["errors"].append(f"测试异常: {str(e)}")
    
    # 打印结果
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    print(f"注册成功: {results['register_success']}")
    print(f"登录成功: {results['login_success']}")
    print(f"任务分析上报成功: {results['task_analysis_report']}")
    print(f"智能咨询上报成功: {results['consult_report']}")
    print(f"获取统计成功: {results['stats_success']}")
    print(f"设置目标成功: {results['goals_success']}")
    print(f"获取偏好成功: {results['preferences_success']}")
    
    if results["errors"]:
        print(f"\n错误:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    total = sum([v for k, v in results.items() if k not in ["errors"]])
    success = total - len(results["errors"])
    print(f"\n总测试项: {total}, 成功: {success}, 失败: {len(results['errors'])}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_core_habits())
