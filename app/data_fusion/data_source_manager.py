import asyncio
from typing import List, Dict, Any, Optional
from app.data_fusion.data_source import DataSource, SourceResult
from app.data_fusion.adapters.lianjia_adapter import LianjiaAdapter
from app.data_fusion.adapters.mock_gov_api_adapter import MockGovApiAdapter
from app.core import redis_cache


class DataSourceManager:
    """
    数据源管理器
    """
    
    def __init__(self):
        """
        初始化数据源管理器
        """
        self.data_sources: List[DataSource] = []  # 数据源列表
        self._initialize_sources()  # 初始化数据源
    
    def _initialize_sources(self):
        """
        初始化数据源
        """
        # 添加链家适配器
        lianjia_adapter = LianjiaAdapter(priority=3)
        self.data_sources.append(lianjia_adapter)
        
        # 添加模拟政府API适配器
        mock_gov_api_adapter = MockGovApiAdapter(priority=4)
        self.data_sources.append(mock_gov_api_adapter)
        
        # 按优先级排序（优先级数字越小，优先级越高）
        self.data_sources.sort(key=lambda x: x.priority)
    
    @redis_cache(ttl=300, key_prefix="prop:")
    async def gather_all_sources(self, city: str, community: str) -> List[SourceResult]:
        """
        从所有数据源获取数据
        
        Args:
            city: 城市名称
            community: 小区名称
        
        Returns:
            List[SourceResult]: 所有数据源的返回结果
        """
        # 并行从所有数据源获取数据
        tasks = []
        for source in self.data_sources:
            tasks.append(source.fetch(city, community))
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def get_best_source_result(self, city: str, community: str) -> Optional[SourceResult]:
        """
        获取最佳数据源的结果
        
        Args:
            city: 城市名称
            community: 小区名称
        
        Returns:
            Optional[SourceResult]: 最佳数据源的返回结果
        """
        # 首先获取所有数据源的健康度
        healthy_sources = self._get_healthy_sources()
        
        if not healthy_sources:
            return None
        
        # 并行从健康的数据源获取数据
        tasks = []
        for source in healthy_sources:
            tasks.append(source.fetch(city, community))
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 过滤出成功的结果
        successful_results = [result for result in results if result.success]
        
        if not successful_results:
            return None
        
        # 按数据源优先级排序，选择优先级最高的
        successful_results.sort(
            key=lambda x: next(
                (source.priority for source in self.data_sources if source.name == x.source_name),
                999
            )
        )
        
        return successful_results[0]
    
    def _get_healthy_sources(self, min_health_score: float = 0.3) -> List[DataSource]:
        """
        获取健康的数据源
        
        Args:
            min_health_score: 最小健康度分数
        
        Returns:
            List[DataSource]: 健康的数据源列表
        """
        healthy_sources = []
        
        for source in self.data_sources:
            health_score = source.get_health_score()
            if health_score >= min_health_score:
                healthy_sources.append(source)
        
        # 按优先级排序
        healthy_sources.sort(key=lambda x: x.priority)
        
        return healthy_sources
    
    def add_data_source(self, data_source: DataSource):
        """
        添加数据源
        
        Args:
            data_source: 要添加的数据源
        """
        self.data_sources.append(data_source)
        # 重新排序
        self.data_sources.sort(key=lambda x: x.priority)
    
    def remove_data_source(self, source_name: str):
        """
        移除数据源
        
        Args:
            source_name: 要移除的数据源名称
        """
        self.data_sources = [source for source in self.data_sources if source.name != source_name]
    
    def get_source_health_status(self) -> Dict[str, float]:
        """
        获取所有数据源的健康状态
        
        Returns:
            Dict[str, float]: 数据源名称到健康度分数的映射
        """
        health_status = {}
        
        for source in self.data_sources:
            health_status[source.name] = source.get_health_score()
        
        return health_status
    
    def reset_all_health_stats(self):
        """
        重置所有数据源的健康统计信息
        """
        for source in self.data_sources:
            source.reset_health_stats()
