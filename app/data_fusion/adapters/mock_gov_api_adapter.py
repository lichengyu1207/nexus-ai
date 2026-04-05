import asyncio
import time
from typing import Dict, Any

from app.data_fusion.data_source import DataSource, SourceResult


class MockGovApiAdapter(DataSource):
    """
    模拟政府公开API适配器
    """
    
    def __init__(self, priority: int = 4):
        """
        初始化模拟政府API适配器
        
        Args:
            priority: 优先级，数字越小优先级越高
        """
        super().__init__(name="mock_gov_api", priority=priority)
        self.base_url = "https://api.gov.cn/real_estate"
        self.timeout = 5.0  # 请求超时时间
        self.request_interval = 1.0  # 请求间隔时间
        self.last_request_time = 0  # 上次请求时间
    
    async def fetch(self, city: str, community: str) -> SourceResult:
        """
        模拟从政府API获取小区数据
        
        Args:
            city: 城市名称
            community: 小区名称
        
        Returns:
            SourceResult: 数据源返回的结果
        """
        try:
            # 模拟API调用延迟
            await asyncio.sleep(0.5)
            
            # 模拟API响应
            data = self._mock_gov_api_response(city, community)
            
            # 更新最后请求时间
            self.last_request_time = time.time()
            
            self.record_success()
            return SourceResult(
                source_name=self.name,
                success=True,
                data=data,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.record_failure()
            return SourceResult(
                source_name=self.name,
                success=False,
                data={},
                error=str(e),
                timestamp=time.time()
            )
    
    def _mock_gov_api_response(self, city: str, community: str) -> Dict[str, Any]:
        """
        模拟政府API响应数据
        
        Args:
            city: 城市名称
            community: 小区名称
        
        Returns:
            Dict[str, Any]: 模拟的API响应数据
        """
        # 模拟政府API返回的JSON数据
        return {
            "community_name": community,
            "city": city,
            "region": "朝阳区",  # 区域
            "district_code": "110105",  # 行政区代码
            "community_code": "110105001001",  # 小区代码
            "land_use_type": "住宅用地",  # 土地用途
            "land_area": 50000.0,  # 占地面积（平方米）
            "building_area": 150000.0,  # 建筑面积（平方米）
            "plot_ratio": 3.0,  # 容积率
            "greening_rate": 0.3,  # 绿化率
            "property_right_period": 70,  # 产权年限
            "approval_date": "2013-05-15",  # 审批日期
            "completion_date": "2015-12-31",  # 竣工日期
            "registered_houses": 1200,  # 已登记房屋数
            "population": 3500,  # 居住人口
            "public_facilities": [  # 公共设施
                "幼儿园",
                "小学",
                "社区服务中心",
                "文化活动站",
                "卫生站"
            ],
            "transportation": [  # 交通设施
                "地铁6号线",
                "地铁10号线",
                "公交站"
            ],
            "market_monitor": {  # 市场监控数据
                "average_price": 62000,  # 平均房价
                "price_trend": [  # 价格趋势
                    {"month": "2023-01", "price": 60000},
                    {"month": "2023-02", "price": 60500},
                    {"month": "2023-03", "price": 61000},
                    {"month": "2023-04", "price": 61500},
                    {"month": "2023-05", "price": 62000}
                ],
                "transaction_volume": 120,  # 成交量
                "transaction_area": 15000  # 成交面积
            },
            "source": "mock_gov_api",
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
