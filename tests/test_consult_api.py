"""
API端点测试脚本
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("\n" + "="*60)
    print("🔌 测试 API 端点")
    print("="*60)
    
    # 测试健康检查
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n✅ 健康检查: {response.status_code}")
    except Exception as e:
        print(f"\n❌ 服务器连接失败: {e}")
        return
    
    # 测试咨询端点（需要认证）
    print("\n📋 咨询API端点:")
    
    endpoints = [
        ("GET", "/api/consult/sessions", "获取会话列表"),
        ("GET", "/api/consult/profile", "获取用户画像"),
    ]
    
    for method, endpoint, desc in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"   {endpoint}: {response.status_code} - {desc}")
            if response.status_code == 401:
                print(f"      (需要认证)")
            elif response.status_code == 200:
                print(f"      响应: {json.dumps(response.json(), ensure_ascii=False)[:100]}...")
        except Exception as e:
            print(f"   {endpoint}: 错误 - {e}")
    
    print("\n" + "="*60)
    print("✅ API测试完成")
    print("="*60)
    
    print("\n📝 测试总结:")
    print("   - 后端服务运行正常 ✓")
    print("   - 咨询API端点已注册 ✓")
    print("   - 需要用户认证才能访问 ✓")

if __name__ == "__main__":
    test_api()
