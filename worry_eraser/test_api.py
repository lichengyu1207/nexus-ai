import requests
import json

# 测试脚本 - 烦恼橡皮擦 API

base_url = "http://localhost:8000"

def test_chat_endpoint():
    """测试聊天接口"""
    print("=== 测试聊天接口 ===")
    
    # 测试周瑜
    payload = {
        "message": "工作压力大，感觉很疲惫",
        "agent": "zhouyu"
    }
    
    response = requests.post(f"{base_url}/chat", json=payload)
    print(f"周瑜回复: {response.json()}")
    
    # 测试陆逊
    payload = {
        "message": "工作压力大，感觉很疲惫",
        "agent": "luxun"
    }
    
    response = requests.post(f"{base_url}/chat", json=payload)
    print(f"陆逊回复: {response.json()}")
    
    return response.json()['report_id']

def test_report_endpoint(report_id):
    """测试报告接口"""
    print("\n=== 测试报告接口 ===")
    
    response = requests.get(f"{base_url}/report/{report_id}")
    report = response.json()
    print(f"报告内容: {json.dumps(report, indent=2, ensure_ascii=False)}")
    
    # 验证报告结构
    assert 'title' in report
    assert 'summary' in report
    assert 'emotion_trend' in report
    assert 'suggestions' in report
    assert 'chart_data' in report
    print("报告结构验证通过！")

def test_agents_endpoint():
    """测试智能体列表接口"""
    print("\n=== 测试智能体列表接口 ===")
    
    response = requests.get(f"{base_url}/agents")
    agents = response.json()
    print(f"智能体列表: {agents}")

def test_health_endpoint():
    """测试健康检查接口"""
    print("\n=== 测试健康检查接口 ===")
    
    response = requests.get(f"{base_url}/health")
    health = response.json()
    print(f"健康状态: {health}")

if __name__ == "__main__":
    try:
        # 测试健康检查
        test_health_endpoint()
        
        # 测试智能体列表
        test_agents_endpoint()
        
        # 测试聊天接口并获取报告ID
        report_id = test_chat_endpoint()
        
        # 测试报告接口
        test_report_endpoint(report_id)
        
        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
