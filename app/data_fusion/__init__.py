"""数据融合模块"""

from app.data_fusion.data_source import DataSource, SourceResult
from app.data_fusion.data_source_manager import DataSourceManager
from app.data_fusion.adapters.lianjia_adapter import LianjiaAdapter
from app.data_fusion.adapters.mock_gov_api_adapter import MockGovApiAdapter
from app.data_fusion.pipelines.cleaner import (
    DataCleaner, DataFrameCleaner, PriceNormalizer, 
    MissingValueFiller, normalize_price, fill_missing_with_mean
)
from app.data_fusion.pipelines.fusion_engine import FusionEngine
from app.data_fusion.pipelines.data_lineage import DataLineageTracker

__all__ = [
    "DataSource",
    "SourceResult",
    "DataSourceManager",
    "LianjiaAdapter",
    "MockGovApiAdapter",
    "DataCleaner",
    "DataFrameCleaner",
    "PriceNormalizer",
    "MissingValueFiller",
    "normalize_price",
    "fill_missing_with_mean",
    "FusionEngine",
    "DataLineageTracker"
]

__version__ = "1.0.0"

"""
数据融合模块，用于管理和访问不同的数据源，以及数据清洗和融合

主要组件：
- data_source: 定义数据源抽象基类和结果数据类
- adapters: 包含各种数据源的适配器实现
- data_source_manager: 管理所有数据源，根据策略选择合适的源
- pipelines: 包含数据清洗和融合的管道组件
  - cleaner: 数据清洗模块，包含各种清洗处理器
  - fusion_engine: 数据融合引擎，用于融合多个数据源的数据
  - data_lineage: 数据血缘追踪，记录数据的来源和转换过程

使用示例：
    from app.data_fusion import DataSourceManager
    
    async def fetch_data():
        manager = DataSourceManager()
        results = await manager.gather_all_sources("北京", "望京SOHO")
        return results

    # 数据清洗和融合示例
    from app.data_fusion import DataCleaner, PriceNormalizer, FusionEngine
    
    def process_data(data_list):
        # 创建清洗器
        cleaner = DataCleaner()
        cleaner.add_processor(PriceNormalizer())
        
        # 清洗数据
        cleaned_data = [cleaner.process(data) for data in data_list]
        
        # 融合数据
        fusion_engine = FusionEngine()
        golden_record = fusion_engine.fuse_property_data(cleaned_data)
        
        return golden_record
"""

