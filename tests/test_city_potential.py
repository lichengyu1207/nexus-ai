# -*- coding: utf-8 -*-
"""
城市潜力评分工作流测试脚本
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def test_city_potential_workflow():
    """测试城市潜力评分工作流"""
    print("=" * 60)
    print("城市潜力评分工作流测试")
    print("=" * 60)
    
    api_token = os.getenv("COZE_API_TOKEN", "")
    base_url = os.getenv("COZE_BASE_URL", "https://hhvc3vq7mq.coze.site")
    
    print(f"\n配置信息:")
    print(f"  BASE_URL: {base_url}")
    print(f"  API_TOKEN: {api_token[:50]}..." if api_token else "  API_TOKEN: 未配置")
    
    if not api_token:
        print("\n错误: COZE_API_TOKEN 未配置")
        return False
    
    print("\n正在测试连接...")
    
    try:
        import httpx
        
        url = f"{base_url}/run"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "city_name": "深圳",
            "macro_data": {
                "gdp_growth": 5.5,
                "population_growth": 2.1,
                "employment_rate": 95.5
            },
            "scoring_result": {
                "total_score": 85,
                "economy_score": 90,
                "infrastructure_score": 80,
                "environment_score": 85
            },
            "analysis_report": "深圳市房地产市场分析报告"
        }
        
        print(f"\n请求参数:")
        print(json.dumps(params, indent=2, ensure_ascii=False))
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, json=params)
            
            print(f"\n响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n成功! 返回数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                return True
            else:
                print(f"\n失败! 响应内容:")
                print(response.text[:500])
                return False
                
    except Exception as e:
        print(f"\n测试异常: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_city_potential_workflow())
