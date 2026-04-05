"""简单测试登录"""
import requests

BASE_URL = "http://127.0.0.1:8000"

# 测试健康检查
print("1. 测试健康检查...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   状态: {r.status_code}")
except Exception as e:
    print(f"   错误: {e}")

# 测试登录
print("\n2. 测试登录...")
login_data = {
    "email": "1558691995@qq.com",
    "password": "147258@Zxcvbnm"
}

try:
    r = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
    print(f"   状态: {r.status_code}")
    print(f"   响应: {r.text[:500]}")
    
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        print(f"   Token: {token[:50]}...")
        
        # 测试获取用户信息
        print("\n3. 测试获取用户信息...")
        headers = {"Authorization": f"Bearer {token}"}
        r2 = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=10)
        print(f"   状态: {r2.status_code}")
        print(f"   响应: {r2.text[:300]}")
        
except Exception as e:
    print(f"   错误: {e}")
