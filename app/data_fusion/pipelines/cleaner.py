import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod


class Processor(ABC):
    """
    数据处理器抽象基类
    """
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        处理数据
        
        Args:
            data: 输入数据
        
        Returns:
            处理后的数据
        """
        pass
    
    def __call__(self, data: Any) -> Any:
        """
        支持直接调用处理器
        
        Args:
            data: 输入数据
        
        Returns:
            处理后的数据
        """
        return self.process(data)


class DataFrameProcessor(Processor):
    """
    DataFrame处理器基类
    """
    
    @abstractmethod
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理DataFrame
        
        Args:
            df: 输入DataFrame
        
        Returns:
            处理后的DataFrame
        """
        pass


class PriceNormalizer(Processor):
    """
    价格标准化处理器
    """
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理价格数据，将“万元/套”转换为“元/㎡”
        
        Args:
            data: 包含价格信息的字典
        
        Returns:
            处理后的数据字典
        """
        processed_data = data.copy()
        
        # 处理价格字段
        if 'price' in processed_data:
            price_value = processed_data['price']
            price_unit = processed_data.get('price_unit', '')
            area = processed_data.get('area', 0)
            
            # 如果是万元/套，转换为元/㎡，且价格不为None
            if price_value is not None and price_unit == '万元/套' and area > 0:
                # 万元/套 -> 元/㎡
                price_per_square = (price_value * 10000) / area
                processed_data['price'] = price_per_square
                processed_data['price_unit'] = '元/㎡'
            
        return processed_data


def normalize_price(value: Any, unit: str = '万元/套', area: float = 100.0) -> float:
    """
    标准化价格，处理“万元/套”到“元/㎡”的转换
    
    Args:
        value: 价格值
        unit: 价格单位
        area: 面积（平方米）
    
    Returns:
        标准化后的价格（元/㎡）
    """
    if unit == '万元/套' and area > 0:
        # 万元/套 -> 元/㎡
        return (value * 10000) / area
    elif unit == '元/㎡':
        return value
    else:
        # 其他单位，返回原值
        return value


class MissingValueFiller(DataFrameProcessor):
    """
    缺失值填充处理器
    """
    
    def __init__(self, column: str, method: str = 'mean'):
        """
        初始化缺失值填充处理器
        
        Args:
            column: 要填充的列名
            method: 填充方法，支持 'mean', 'median', 'mode'
        """
        self.column = column
        self.method = method
    
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        填充缺失值
        
        Args:
            df: 输入DataFrame
        
        Returns:
            处理后的DataFrame
        """
        processed_df = df.copy()
        
        if self.column in processed_df.columns:
            if self.method == 'mean':
                fill_value = processed_df[self.column].mean()
            elif self.method == 'median':
                fill_value = processed_df[self.column].median()
            elif self.method == 'mode':
                fill_value = processed_df[self.column].mode().iloc[0]
            else:
                raise ValueError(f"Unsupported method: {self.method}")
            
            processed_df[self.column] = processed_df[self.column].fillna(fill_value)
        
        return processed_df


def fill_missing_with_mean(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    用均值填充缺失值
    
    Args:
        df: 输入DataFrame
        column: 要填充的列名
    
    Returns:
        处理后的DataFrame
    """
    processor = MissingValueFiller(column, method='mean')
    return processor.process(df)


class DataCleaner:
    """
    数据清洗器，支持多个处理器的链式调用
    """
    
    def __init__(self):
        """
        初始化数据清洗器
        """
        self.processors: List[Processor] = []
    
    def add_processor(self, processor: Processor) -> 'DataCleaner':
        """
        添加处理器
        
        Args:
            processor: 要添加的处理器
        
        Returns:
            清洗器实例，支持链式调用
        """
        self.processors.append(processor)
        return self
    
    def process(self, data: Any) -> Any:
        """
        处理数据，按顺序应用所有处理器
        
        Args:
            data: 输入数据
        
        Returns:
            处理后的数据
        """
        processed_data = data
        
        for processor in self.processors:
            processed_data = processor.process(processed_data)
        
        return processed_data
    
    def __call__(self, data: Any) -> Any:
        """
        支持直接调用清洗器
        
        Args:
            data: 输入数据
        
        Returns:
            处理后的数据
        """
        return self.process(data)


class DataFrameCleaner(DataCleaner):
    """
    DataFrame清洗器，专门处理DataFrame数据
    """
    
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理DataFrame，按顺序应用所有处理器
        
        Args:
            df: 输入DataFrame
        
        Returns:
            处理后的DataFrame
        """
        processed_df = df
        
        for processor in self.processors:
            processed_df = processor.process(processed_df)
        
        return processed_df
