"""
特征提取智能体
Feature Extraction Agent

负责对采集的数据进行预处理，包括缺失值填充、异常值剔除、归一化，
并提取特征向量（如房龄、距地铁距离、学区等级、绿化率等）。
"""

import os
import json
import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)


class FeatureType(Enum):
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATE = "date"


@dataclass
class FeatureConfig:
    """特征配置"""
    name: str
    feature_type: FeatureType
    fill_strategy: str = "mean"  # mean, median, mode, constant
    fill_value: Any = None
    normalize: bool = True
    outlier_strategy: str = "iqr"  # iqr, zscore, none
    outlier_threshold: float = 1.5
    scale_range: Tuple[float, float] = (0, 1)


@dataclass
class FeatureExtractionResult:
    """特征提取结果"""
    features: Dict[str, Any]
    feature_vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureExtractor:
    """特征提取智能体"""
    
    def __init__(self):
        self.feature_configs = {
            "building_age": FeatureConfig(
                name="building_age",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="median",
                normalize=True
            ),
            "distance_to_subway": FeatureConfig(
                name="distance_to_subway",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="median",
                normalize=True
            ),
            "school_district_level": FeatureConfig(
                name="school_district_level",
                feature_type=FeatureType.CATEGORICAL,
                fill_strategy="most_frequent",
                normalize=True
            ),
            "greening_rate": FeatureConfig(
                name="greening_rate",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="mean",
                normalize=True
            ),
            "price_per_sqm": FeatureConfig(
                name="price_per_sqm",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="mean",
                normalize=True
            ),
            "total_area": FeatureConfig(
                name="total_area",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="median",
                normalize=True
            ),
            "room_count": FeatureConfig(
                name="room_count",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="most_frequent",
                normalize=True
            ),
            "bathroom_count": FeatureConfig(
                name="bathroom_count",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="most_frequent",
                normalize=True
            ),
            "floor": FeatureConfig(
                name="floor",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="median",
                normalize=True
            ),
            "total_floors": FeatureConfig(
                name="total_floors",
                feature_type=FeatureType.NUMERICAL,
                fill_strategy="median",
                normalize=True
            ),
            "is_elevator": FeatureConfig(
                name="is_elevator",
                feature_type=FeatureType.BOOLEAN,
                fill_strategy="most_frequent",
                normalize=True
            ),
            "property_type": FeatureConfig(
                name="property_type",
                feature_type=FeatureType.CATEGORICAL,
                fill_strategy="most_frequent",
                normalize=True
            )
        }
        
        self.scalers = {}
        self.imputers = {}
        self.category_mappings = {}
    
    def preprocess_numerical(self, value: Any, config: FeatureConfig) -> float:
        """预处理数值型特征"""
        # 处理缺失值
        if pd.isna(value):
            if config.fill_strategy == "mean" and hasattr(self.imputers.get(config.name), 'statistics_'):
                return float(self.imputers[config.name].statistics_[0])
            elif config.fill_strategy == "median":
                return 0.0  # 默认值
            elif config.fill_strategy == "mode":
                return 0.0  # 默认值
            elif config.fill_strategy == "constant" and config.fill_value is not None:
                return float(config.fill_value)
            else:
                return 0.0
        
        # 转换为数值
        try:
            value = float(value)
        except (ValueError, TypeError):
            return 0.0
        
        return value
    
    def preprocess_categorical(self, value: Any, config: FeatureConfig) -> str:
        """预处理分类特征"""
        # 处理缺失值
        if pd.isna(value) or value is None:
            if config.fill_strategy == "mode" and config.name in self.category_mappings:
                return self.category_mappings[config.name].get('mode', 'unknown')
            elif config.fill_strategy == "constant" and config.fill_value is not None:
                return str(config.fill_value)
            else:
                return 'unknown'
        
        return str(value)
    
    def preprocess_boolean(self, value: Any, config: FeatureConfig) -> bool:
        """预处理布尔特征"""
        # 处理缺失值
        if pd.isna(value) or value is None:
            if config.fill_strategy == "mode" and config.name in self.category_mappings:
                return self.category_mappings[config.name].get('mode', False)
            elif config.fill_strategy == "constant" and config.fill_value is not None:
                return bool(config.fill_value)
            else:
                return False
        
        # 转换为布尔值
        if isinstance(value, str):
            value = value.lower()
            return value in ['true', '1', 'yes', '是', '有']
        
        return bool(value)
    
    def detect_outliers(self, values: List[float], config: FeatureConfig) -> List[bool]:
        """检测异常值"""
        if config.outlier_strategy == "none":
            return [False] * len(values)
        
        if not values:
            return []
        
        data = np.array(values)
        outliers = [False] * len(data)
        
        if config.outlier_strategy == "iqr":
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - config.outlier_threshold * iqr
            upper_bound = q3 + config.outlier_threshold * iqr
            outliers = (data < lower_bound) | (data > upper_bound)
        
        elif config.outlier_strategy == "zscore":
            mean = np.mean(data)
            std = np.std(data)
            if std > 0:
                z_scores = np.abs((data - mean) / std)
                outliers = z_scores > config.outlier_threshold
        
        return outliers.tolist()
    
    def normalize_feature(self, value: float, config: FeatureConfig, feature_name: str) -> float:
        """归一化特征"""
        if not config.normalize:
            return value
        
        if feature_name not in self.scalers:
            # 初始化scaler
            self.scalers[feature_name] = MinMaxScaler(feature_range=config.scale_range)
            # 使用默认值进行拟合
            self.scalers[feature_name].fit([[0], [100]])
        
        try:
            return float(self.scalers[feature_name].transform([[value]])[0][0])
        except:
            return 0.0
    
    def encode_categorical(self, value: str, feature_name: str) -> float:
        """编码分类特征"""
        if feature_name not in self.category_mappings:
            # 初始化类别映射
            self.category_mappings[feature_name] = {
                'unknown': 0.0,
                'mode': 'unknown'
            }
        
        mapping = self.category_mappings[feature_name]
        if value not in mapping:
            # 为新类别分配一个唯一值
            mapping[value] = float(len(mapping))
        
        return mapping[value]
    
    def extract_features(self, property_data: Dict[str, Any]) -> FeatureExtractionResult:
        """提取特征"""
        features = {}
        processed_values = {}
        
        # 处理每个特征
        for feature_name, config in self.feature_configs.items():
            raw_value = property_data.get(feature_name)
            
            if config.feature_type == FeatureType.NUMERICAL:
                processed_value = self.preprocess_numerical(raw_value, config)
            elif config.feature_type == FeatureType.CATEGORICAL:
                processed_value = self.preprocess_categorical(raw_value, config)
                # 编码分类特征
                processed_value = self.encode_categorical(processed_value, feature_name)
            elif config.feature_type == FeatureType.BOOLEAN:
                processed_value = self.preprocess_boolean(raw_value, config)
                # 转换为数值
                processed_value = 1.0 if processed_value else 0.0
            else:
                processed_value = 0.0
            
            # 归一化
            if config.feature_type == FeatureType.NUMERICAL:
                processed_value = self.normalize_feature(processed_value, config, feature_name)
            
            features[feature_name] = processed_value
            processed_values[feature_name] = processed_value
        
        # 构建特征向量
        feature_vector = np.array([v for v in features.values()])
        
        # 生成元数据
        metadata = {
            'feature_count': len(features),
            'feature_names': list(features.keys()),
            'extraction_time': time.time()
        }
        
        return FeatureExtractionResult(
            features=features,
            feature_vector=feature_vector,
            metadata=metadata
        )
    
    def batch_extract_features(self, properties_data: List[Dict[str, Any]]) -> List[FeatureExtractionResult]:
        """批量提取特征"""
        results = []
        
        # 首先收集所有数据以进行更准确的统计
        collected_data = {feature: [] for feature in self.feature_configs.keys()}
        
        for property_data in properties_data:
            for feature_name in self.feature_configs.keys():
                value = property_data.get(feature_name)
                if value is not None and not pd.isna(value):
                    collected_data[feature_name].append(value)
        
        # 计算统计信息并更新imputers和category_mappings
        for feature_name, config in self.feature_configs.items():
            values = collected_data[feature_name]
            
            if config.feature_type == FeatureType.NUMERICAL and values:
                # 拟合imputer
                self.imputers[feature_name] = SimpleImputer(strategy=config.fill_strategy)
                self.imputers[feature_name].fit(np.array(values).reshape(-1, 1))
                
                # 拟合scaler
                self.scalers[feature_name] = MinMaxScaler(feature_range=config.scale_range)
                self.scalers[feature_name].fit(np.array(values).reshape(-1, 1))
            
            elif config.feature_type == FeatureType.CATEGORICAL and values:
                # 计算最常见的值作为mode
                from collections import Counter
                counter = Counter(values)
                mode = counter.most_common(1)[0][0]
                self.category_mappings[feature_name] = {
                    'mode': mode
                }
                # 为每个类别分配编码
                for i, category in enumerate(counter.keys()):
                    self.category_mappings[feature_name][category] = float(i)
            
            elif config.feature_type == FeatureType.BOOLEAN and values:
                # 计算最常见的值作为mode
                from collections import Counter
                counter = Counter(values)
                if counter:
                    mode = counter.most_common(1)[0][0]
                    self.category_mappings[feature_name] = {
                        'mode': mode
                    }
        
        # 处理每个属性
        for property_data in properties_data:
            result = self.extract_features(property_data)
            results.append(result)
        
        return results


# 示例使用
if __name__ == "__main__":
    # 创建特征提取器
    extractor = FeatureExtractor()
    
    # 示例数据
    sample_data = [
        {
            "building_age": 10,
            "distance_to_subway": 500,
            "school_district_level": "A",
            "greening_rate": 35,
            "price_per_sqm": 85000,
            "total_area": 120,
            "room_count": 3,
            "bathroom_count": 2,
            "floor": 15,
            "total_floors": 30,
            "is_elevator": True,
            "property_type": "apartment"
        },
        {
            "building_age": None,  # 缺失值
            "distance_to_subway": 1200,
            "school_district_level": "B",
            "greening_rate": 25,
            "price_per_sqm": 65000,
            "total_area": 80,
            "room_count": 2,
            "bathroom_count": 1,
            "floor": 5,
            "total_floors": 10,
            "is_elevator": False,
            "property_type": "house"
        }
    ]
    
    # 批量提取特征
    results = extractor.batch_extract_features(sample_data)
    
    for i, result in enumerate(results):
        print(f"Property {i+1}:")
        print(f"Features: {result.features}")
        print(f"Feature Vector: {result.feature_vector}")
        print(f"Metadata: {result.metadata}")
        print()
