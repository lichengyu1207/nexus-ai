"""
测试高德API Key是否有效
"""
import requests
import json

def test_api_key():
    api_key = 'a55b176367bcc6d90c7518e00a27f3e1'
    
    print("="*60)
    print("🔑 高德API Key测试")
    print("="*60)
    print(f"API Key: {api_key}")
    print()
    
    # 测试地理编码API
    url = 'https://restapi.amap.com/v3/geocode/geo'
    params = {
        'key': api_key,
        'address': '深圳市南山区',
        'output': 'json'
    }
    
    print("测试地理编码API...")
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        print(f"状态: {data.get('status')}")
        print(f"信息: {data.get('info')}")
        print(f"错误码: {data.get('infocode')}")
        
        if data.get('status') == '1':
            print("✅ API Key有效！")
            geocodes = data.get('geocodes', [])
            if geocodes:
                print(f"地址: {geocodes[0].get('formatted_address')}")
                print(f"坐标: {geocodes[0].get('location')}")
        else:
            print("❌ API Key无效或服务未开通")
            print()
            print("可能的原因:")
            print("1. API Key未开通Web服务权限")
            print("2. API Key已过期")
            print("3. 服务未启用（需在控制台开启'Web服务'）")
            print()
            print("解决方法:")
            print("1. 登录高德开放平台: https://console.amap.com/")
            print("2. 进入应用管理，找到对应Key")
            print("3. 确保勾选了'Web服务'平台")
            print("4. 或者创建新的Key，选择'Web服务'平台")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print()
    print("="*60)

if __name__ == "__main__":
    test_api_key()
