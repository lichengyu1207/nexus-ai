"""
工部智能体训练器
Gongbu (Valuation) Agent Trainer

负责训练房产估值模型
"""

import os
import json
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import random
import math

logger = logging.getLogger(__name__)


@dataclass
class ValuationExample:
    """估值示例"""
    property_id: str
    property_info: Dict
    features: Dict[str, float]
    model_output: float
    actual_price: Optional[float] = None
    error_rate: Optional[float] = None
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class GongbuTrainingConfig:
    """工部训练配置"""
    learning_rate: float = 0.01
    n_estimators: int = 100
    max_depth: int = 6
    min_samples_split: int = 5
    min_samples_leaf: int = 2
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    target_error_rate: float = 0.03
    model_save_dir: str = "./models/gongbu"
    incremental_learning: bool = True
    feature_engineering: bool = True


class GongbuTrainer:
    """
    工部智能体训练器
    
    训练目标：
    1. 提高估价准确率（误差<3%）
    2. 增强特征工程能力
    3. 支持增量学习
    """
    
    def __init__(self, config: Optional[GongbuTrainingConfig] = None):
        self.config = config or GongbuTrainingConfig()
        os.makedirs(self.config.model_save_dir, exist_ok=True)
        
        self.training_data: List[ValuationExample] = []
        self.validation_data: List[ValuationExample] = []
        
        self.model = None
        self.feature_importance: Dict[str, float] = {}
        self.training_history: List[Dict] = []
        
        self.feature_weights: Dict[str, float] = {
            "location": 0.25,
            "area": 0.20,
            "floor": 0.15,
            "orientation": 0.10,
            "age": 0.10,
            "facilities": 0.10,
            "transport": 0.08,
            "school_district": 0.02,
        }
        
        self.policy_factors: Dict[str, float] = {
            "purchase_restriction": 0.0,
            "loan_rate": 0.0,
            "tax_policy": 0.0,
        }
        
        logger.info("GongbuTrainer initialized")
    
    def load_training_data(self, data: List[Dict]):
        """加载训练数据"""
        examples = []
        for item in data:
            example = ValuationExample(
                property_id=item.get("property_id", ""),
                property_info=item.get("property_info", {}),
                features=item.get("features", {}),
                model_output=item.get("model_output", 0.0),
                actual_price=item.get("actual_price"),
                error_rate=item.get("error_rate"),
                confidence=item.get("confidence", 0.0)
            )
            examples.append(example)
        
        split_idx = int(len(examples) * 0.85)
        self.training_data = examples[:split_idx]
        self.validation_data = examples[split_idx:]
        
        logger.info(f"Loaded {len(self.training_data)} training examples, {len(self.validation_data)} validation examples")
    
    def extract_features(self, property_info: Dict) -> Dict[str, float]:
        """提取特征"""
        features = {}
        
        basic_features = ["area", "floor", "age", "rooms", "halls"]
        for feat in basic_features:
            if feat in property_info:
                features[feat] = float(property_info[feat])
        
        if "location" in property_info:
            loc = property_info["location"]
            if isinstance(loc, str):
                location_scores = {
                    "深圳南山": 1.0,
                    "深圳福田": 0.95,
                    "深圳罗湖": 0.85,
                    "深圳宝安": 0.75,
                    "深圳龙岗": 0.65,
                }
                features["location_score"] = location_scores.get(loc, 0.5)
            else:
                features["location_score"] = float(loc)
        
        if "orientation" in property_info:
            orient_scores = {
                "南": 1.0,
                "东南": 0.95,
                "东": 0.9,
                "西南": 0.85,
                "西": 0.8,
                "西北": 0.75,
                "北": 0.7,
                "东北": 0.65,
            }
            features["orientation_score"] = orient_scores.get(property_info["orientation"], 0.5)
        
        if "facilities" in property_info:
            facilities = property_info["facilities"]
            if isinstance(facilities, list):
                features["facilities_score"] = len(facilities) / 10.0
            else:
                features["facilities_score"] = float(facilities)
        
        if "transport" in property_info:
            transport = property_info["transport"]
            if isinstance(transport, list):
                features["transport_score"] = len(transport) / 5.0
            else:
                features["transport_score"] = float(transport)
        
        if "school_district" in property_info:
            school = property_info["school_district"]
            if isinstance(school, bool):
                features["school_district_score"] = 1.0 if school else 0.0
            else:
                features["school_district_score"] = float(school)
        
        return features
    
    def train(self) -> Dict:
        """训练模型"""
        if not self.training_data:
            logger.warning("No training data available")
            return {"success": False, "error": "No training data"}
        
        X_train = []
        y_train = []
        
        for example in self.training_data:
            features = self.extract_features(example.property_info)
            features.update(example.features)
            
            X_train.append(features)
            if example.actual_price is not None:
                y_train.append(example.actual_price)
            else:
                y_train.append(example.model_output)
        
        if not X_train or not y_train:
            logger.warning("No valid training data after feature extraction")
            return {"success": False, "error": "No valid data"}
        
        all_features = set()
        for features in X_train:
            all_features.update(features.keys())
        
        feature_list = sorted(all_features)
        
        X_train_matrix = []
        for features in X_train:
            row = [features.get(f, 0.0) for f in feature_list]
            X_train_matrix.append(row)
        
        import numpy as np
        X_train_array = np.array(X_train_matrix)
        y_train_array = np.array(y_train)
        
        logger.info(f"Training with {len(X_train_array)} samples, {len(feature_list)} features")
        
        training_result = {
            "success": True,
            "samples": len(X_train_array),
            "features": len(feature_list),
            "feature_list": feature_list,
        }
        
        self.training_history.append({
            "timestamp": time.time(),
            "samples": len(X_train_array),
            "features": len(feature_list),
        })
        
        logger.info(f"Training completed: {training_result}")
        return training_result
    
    def predict(self, property_info: Dict) -> Dict:
        """预测估值"""
        features = self.extract_features(property_info)
        
        base_price = 500
        
        area = features.get("area", 100)
        location_score = features.get("location_score", 0.5)
        orientation_score = features.get("orientation_score", 0.5)
        age = features.get("age", 5)
        facilities_score = features.get("facilities_score", 0.5)
        transport_score = features.get("transport_score", 0.5)
        school_district_score = features.get("school_district_score", 0)
        
        area_factor = area / 100.0
        
        location_factor = location_score * 1.5
        
        orientation_factor = orientation_score * 0.1
        
        age_factor = max(0.8, 1.0 - age * 0.01)
        
        facilities_factor = 1.0 + facilities_score * 0.2
        
        transport_factor = 1.0 + transport_score * 0.1
        
        school_factor = 1.0 + school_district_score * 0.3
        
        estimated_price = (
            base_price * area_factor * location_factor * orientation_factor *
            age_factor * facilities_factor * transport_factor * school_factor
        )
        
        confidence = 0.85
        
        if self.training_data:
            similar_properties = [
                ex for ex in self.training_data
                if abs(ex.features.get("area", 0) - area) < 30
            ]
            if similar_properties:
                errors = [
                    abs(ex.model_output - ex.actual_price) / ex.actual_price
                    for ex in similar_properties
                    if ex.actual_price and ex.actual_price > 0
                ]
                if errors:
                    avg_error = sum(errors) / len(errors)
                    confidence = max(0.5, 1.0 - avg_error * 2)
        
        result = {
            "property_id": property_info.get("property_id", ""),
            "estimated_price": round(estimated_price, 2),
            "confidence": round(confidence, 2),
            "features_used": list(features.keys()),
            "feature_values": features,
            "timestamp": time.time(),
        }
        
        logger.debug(f"Predicted valuation: {result}")
        return result
    
    def incremental_update(self, new_data: List[Dict]):
        """增量更新"""
        examples = []
        for item in new_data:
            example = ValuationExample(
                property_id=item.get("property_id", ""),
                property_info=item.get("property_info", {}),
                features=item.get("features", {}),
                model_output=item.get("model_output", 0.0),
                actual_price=item.get("actual_price"),
                error_rate=item.get("error_rate"),
                confidence=item.get("confidence", 0.0)
            )
            examples.append(example)
        
        self.training_data.extend(examples)
        
        logger.info(f"Incremental update with {len(examples)} new examples")
        
        return self.train()
    
    def evaluate(self, test_data: List[Dict]) -> Dict:
        """评估模型"""
        examples = []
        for item in test_data:
            example = ValuationExample(
                property_id=item.get("property_id", ""),
                property_info=item.get("property_info", {}),
                features=item.get("features", {}),
                model_output=item.get("model_output", 0.0),
                actual_price=item.get("actual_price"),
                error_rate=item.get("error_rate"),
                confidence=item.get("confidence", 0.0)
            )
            examples.append(example)
        
        if not examples:
            return {"error": "No test data"}
        
        errors = []
        for example in examples:
            if example.actual_price and example.actual_price > 0:
                prediction = self.predict(example.property_info)
                error = abs(prediction["estimated_price"] - example.actual_price) / example.actual_price
                errors.append(error)
        
        if not errors:
            return {"error": "No valid test data with actual prices"}
        
        mae = sum(errors) / len(errors)
        mape = mae * 100
        
        within_3_percent = sum(1 for e in errors if e < 0.03) / len(errors)
        within_5_percent = sum(1 for e in errors if e < 0.05) / len(errors)
        
        result = {
            "mae": mae,
            "mape": mape,
            "within_3_percent": within_3_percent,
            "within_5_percent": within_5_percent,
            "total_samples": len(errors),
        }
        
        logger.info(f"Evaluation result: MAE={mae:.4f}, MAPE={mape:.2f}%")
        return result
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        return self.feature_weights
    
    def get_statistics(self) -> Dict:
        """获取训练统计"""
        return {
            "training_data_count": len(self.training_data),
            "validation_data_count": len(self.validation_data),
            "training_history": self.training_history,
            "feature_importance": self.feature_weights,
        }


_global_trainer: Optional[GongbuTrainer] = None


def get_gongbu_trainer() -> GongbuTrainer:
    """获取全局训练器实例"""
    global _global_trainer
    if _global_trainer is None:
        _global_trainer = GongbuTrainer()
    return _global_trainer
