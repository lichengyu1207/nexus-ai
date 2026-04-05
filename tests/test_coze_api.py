# -*- coding: utf-8 -*-
"""
Coze API 连接测试脚本
验证 API Token 和工作流调用是否正常
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def test_coze_connection():
    """测试 Coze API 连接"""
    print("=" * 60)
    print("Coze API 连接测试")
    print("=" * 60)
    
    api_token = os.getenv("COZE_API_TOKEN", "")
    base_url = os.getenv("COZE_BASE_URL", "https://mqbpk2ntqq.coze.site")
    
    print(f"\n配置信息:")
    print(f"  BASE_URL: {base_url}")
    print(f"  API_TOKEN: {api_token[:50]}..." if api_token else "  API_TOKEN: 未配置")
    
    if not api_token:
        print("\n❌ 错误: COZE_API_TOKEN 未配置")
        print("请在 .env 文件中设置 COZE_API_TOKEN")
        return False
    
    print("\n正在测试连接...")
    
    try:
        from backend.services.coze_workflow_client import CozeWorkflowClient
        
        client = CozeWorkflowClient(api_token=api_token, base_url=base_url)
        
        result = await client.collect_city_data(city="长沙")
        
        print(f"\n测试结果:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")
        print(f"  耗时: {result.duration_ms:.2f}ms")
        
        if result.success:
            print(f"\n✅ Coze API 连接成功!")
            print(f"\n返回数据:")
            print(json.dumps(result.data, indent=2, ensure_ascii=False)[:500])
            return True
        else:
            print(f"\n❌ Coze API 调用失败")
            print(f"  错误: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return False


async def test_batch_collection():
    """测试批量采集"""
    print("\n" + "=" * 60)
    print("批量采集测试")
    print("=" * 60)
    
    from backend.services.coze_workflow_client import run_city_data_collection
    
    cities = ["长沙", "杭州"]
    
    print(f"\n测试城市: {cities}")
    
    result = await run_city_data_collection(cities=cities)
    
    print(f"\n批量采集结果:")
    print(f"  总数: {result['total_cities']}")
    print(f"  成功: {result['successful']}")
    print(f"  失败: {result['failed']}")
    print(f"  耗时: {result['duration_seconds']:.2f}秒")
    
    return result['successful'] > 0


if __name__ == "__main__":
    async def main():
        success = await test_coze_connection()
        
        if success:
            print("\n" + "-" * 60)
            await test_batch_collection()
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
    
    asyncio.run(main())
