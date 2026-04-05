from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SourceResult:
    """
    数据源返回结果的数据类
    """
    source_name: str  # 数据源名称
    success: bool     # 是否成功
    data: Dict[str, Any]  # 返回的数据
    error: Optional[str] = None  # 错误信息
    timestamp: Optional[float] = None  # 数据获取时间戳


class DataSource(ABC):
    """
    数据源抽象基类
    """
    
    def __init__(self, name: str, priority: int = 5):
        """
        初始化数据源
        
        Args:
            name: 数据源名称
            priority: 优先级，数字越小优先级越高
        """
        self.name = name
        self.priority = priority
        self.failure_count = 0  # 失败计数
        self.success_count = 0  # 成功计数
        self.total_requests = 0  # 总请求数
    
    @abstractmethod
    async def fetch(self, city: str, community: str) -> SourceResult:
        """
        从数据源获取数据
        
        Args:
            city: 城市名称
            community: 小区名称
        
        Returns:
            SourceResult: 数据源返回的结果
        """
        pass
    
    def record_success(self):
        """
        记录成功请求
        """
        self.success_count += 1
        self.total_requests += 1
    
    def record_failure(self):
        """
        记录失败请求
        """
        self.failure_count += 1
        self.total_requests += 1
    
    def get_health_score(self) -> float:
        """
        获取数据源健康度分数
        
        Returns:
            float: 健康度分数，范围0-1
        """
        if self.total_requests == 0:
            return 1.0
        success_rate = self.success_count / self.total_requests
        return success_rate
    
    def reset_health_stats(self):
        """
        重置健康度统计信息
        """
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0
