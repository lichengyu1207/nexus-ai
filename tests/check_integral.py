"""检查用户积分余额"""
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}

# 登录
r = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER, timeout=30)
token = r.json().get("access_token")
print(f"登录成功")

headers = {"Authorization": f"Bearer {token}"}

# 检查积分余额
r = requests.get(f"{BASE_URL}/api/user/integral", headers=headers)
print(f"积分余额: {r.json()}")

# 检查任务API
r = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
print(f"任务列表状态: {r.status_code}")

# 尝试创建任务
task_data = {"query": "深圳市南山区科技园测试", "style": "professional"}
r = requests.post(f"{BASE_URL}/api/tasks", json=task_data, headers=headers)
print(f"创建任务状态: {r.status_code}")
print(f"创建任务响应: {r.text[:500]}")
