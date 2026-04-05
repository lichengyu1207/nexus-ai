import asyncio
import time
from app.data_fusion.data_source_manager import DataSourceManager
from app.data_fusion.data_source import SourceResult


async def test_gather_all_sources():
    """
    测试从所有数据源获取数据
    """
    print("===== 测试从所有数据源获取数据 =====")
    
    # 创建数据源管理器
    manager = DataSourceManager()
    
    # 获取所有数据源的健康状态
    health_status = manager.get_source_health_status()
    print(f"数据源健康状态: {health_status}")
    
    # 定义测试参数
    city = "北京"
    community = "望京SOHO"
    
    print(f"\n测试获取 {city} {community} 的数据...")
    
    # 记录开始时间
    start_time = time.time()
    
    # 从所有数据源获取数据
    results = await manager.gather_all_sources(city, community)
    
    # 记录结束时间
    end_time = time.time()
    print(f"\n数据获取完成，耗时: {end_time - start_time:.2f} 秒")
    
    # 打印所有结果
    print("\n所有数据源的返回结果:")
    for i, result in enumerate(results):
        print(f"\n数据源 {i+1}: {result.source_name}")
        print(f"  成功: {result.success}")
        if result.success:
            print(f"  数据: {result.data}")
        else:
            print(f"  错误: {result.error}")
        print(f"  时间戳: {result.timestamp}")
    
    # 再次获取健康状态，查看是否有变化
    new_health_status = manager.get_source_health_status()
    print(f"\n数据获取后的健康状态: {new_health_status}")


async def test_get_best_source_result():
    """
    测试获取最佳数据源的结果
    """
    print("\n===== 测试获取最佳数据源的结果 =====")
    
    # 创建数据源管理器
    manager = DataSourceManager()
    
    # 定义测试参数
    city = "上海"
    community = "陆家嘴金融中心"
    
    print(f"测试获取 {city} {community} 的最佳数据源结果...")
    
    # 记录开始时间
    start_time = time.time()
    
    # 获取最佳数据源的结果
    result = await manager.get_best_source_result(city, community)
    
    # 记录结束时间
    end_time = time.time()
    print(f"数据获取完成，耗时: {end_time - start_time:.2f} 秒")
    
    # 打印结果
    if result:
        print(f"\n最佳数据源: {result.source_name}")
        print(f"  成功: {result.success}")
        if result.success:
            print(f"  数据: {result.data}")
        else:
            print(f"  错误: {result.error}")
        print(f"  时间戳: {result.timestamp}")
    else:
        print("\n没有找到可用的数据源")


async def main():
    """
    测试主函数
    """
    print("开始测试数据接入层...")
    
    # 测试从所有数据源获取数据
    await test_gather_all_sources()
    
    # 测试获取最佳数据源的结果
    await test_get_best_source_result()
    
    print("\n测试完成！")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
