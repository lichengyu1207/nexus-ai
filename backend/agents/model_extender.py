"""
模型扩展模块
根据实际需求添加更多模型
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from backend.agents.model_manager import ModelInfo, ModelPerformance, get_model_manager

logger = logging.getLogger(__name__)


class ModelExtender:
    """模型扩展器"""
    
    def __init__(self):
        self.model_manager = get_model_manager()
    
    def add_model(self, model_name: str, model_type: str, endpoint: str, 
                  api_key: str, parameters: Dict[str, Any]):
        """添加新模型
        
        Args:
            model_name: 模型名称
            model_type: 模型类型（轻量、大型）
            endpoint: 模型端点
            api_key: API密钥
            parameters: 模型参数
            
        Returns:
            是否添加成功
        """
        try:
            # 创建模型信息
            model_info = ModelInfo(
                name=model_name,
                type=model_type,
                endpoint=endpoint,
                api_key=api_key,
                parameters=parameters
            )
            
            # 添加模型
            self.model_manager.add_model(model_info)
            
            # 初始化模型性能数据
            self._initialize_model_performance(model_name)
            
            logger.info(f"成功添加模型: {model_name}")
            return True
        except Exception as e:
            logger.error(f"添加模型失败: {e}")
            return False
    
    def _initialize_model_performance(self, model_name: str):
        """初始化模型性能数据
        
        Args:
            model_name: 模型名称
        """
        import time
        current_time = time.time()
        
        # 任务类型列表
        task_types = ["问答", "分析", "生成", "报告"]
        
        # 基于模型类型设置默认性能
        model_info = self.model_manager.get_model_info(model_name)
        if not model_info:
            return
        
        # 默认性能数据
        default_performance = {
            "轻量": {
                "问答": ModelPerformance(0.90, 0.3, 0.0005, 0, current_time),
                "分析": ModelPerformance(0.85, 0.5, 0.0008, 0, current_time),
                "生成": ModelPerformance(0.80, 0.7, 0.001, 0, current_time),
                "报告": ModelPerformance(0.75, 1.0, 0.0015, 0, current_time)
            },
            "大型": {
                "问答": ModelPerformance(0.98, 1.2, 0.02, 0, current_time),
                "分析": ModelPerformance(0.95, 1.5, 0.025, 0, current_time),
                "生成": ModelPerformance(0.92, 2.0, 0.03, 0, current_time),
                "报告": ModelPerformance(0.90, 2.5, 0.035, 0, current_time)
            }
        }
        
        # 获取性能映射表
        performance_mapping = self.model_manager.get_performance_mapping()
        
        # 初始化性能数据
        performance_mapping[model_name] = {}
        model_type = model_info.type
        
        for task_type in task_types:
            if model_type in default_performance:
                performance_mapping[model_name][task_type] = default_performance[model_type][task_type]
            else:
                # 默认使用轻量模型的性能数据
                performance_mapping[model_name][task_type] = default_performance["轻量"][task_type]
        
        # 保存性能映射表
        self._save_performance_mapping(performance_mapping)
    
    def _save_performance_mapping(self, mapping: Dict[str, Dict[str, ModelPerformance]]):
        """保存性能映射表"""
        try:
            # 转换为可序列化格式
            serializable_mapping = {}
            for model_name, task_performance in mapping.items():
                serializable_mapping[model_name] = {}
                for task_type, perf in task_performance.items():
                    serializable_mapping[model_name][task_type] = {
                        "accuracy": perf.accuracy,
                        "avg_time": perf.avg_time,
                        "cost": perf.cost,
                        "usage_count": perf.usage_count,
                        "last_updated": perf.last_updated
                    }
            
            # 保存到文件
            mapping_file = os.path.join(
                os.path.dirname(__file__), "..", "data", "model_performance_mapping.json"
            )
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(serializable_mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存性能映射表失败: {e}")
    
    def remove_model(self, model_name: str):
        """移除模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否移除成功
        """
        try:
            self.model_manager.remove_model(model_name)
            logger.info(f"成功移除模型: {model_name}")
            return True
        except Exception as e:
            logger.error(f"移除模型失败: {e}")
            return False
    
    def update_model(self, model_name: str, **kwargs):
        """更新模型信息
        
        Args:
            model_name: 模型名称
            **kwargs: 要更新的参数
            
        Returns:
            是否更新成功
        """
        try:
            # 获取现有模型信息
            model_info = self.model_manager.get_model_info(model_name)
            if not model_info:
                logger.error(f"模型 {model_name} 不存在")
                return False
            
            # 更新模型信息
            updated_info = ModelInfo(
                name=kwargs.get("name", model_info.name),
                type=kwargs.get("type", model_info.type),
                endpoint=kwargs.get("endpoint", model_info.endpoint),
                api_key=kwargs.get("api_key", model_info.api_key),
                parameters=kwargs.get("parameters", model_info.parameters)
            )
            
            # 移除旧模型并添加新模型
            self.model_manager.remove_model(model_name)
            self.model_manager.add_model(updated_info)
            
            logger.info(f"成功更新模型: {model_name}")
            return True
        except Exception as e:
            logger.error(f"更新模型失败: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """列出所有模型
        
        Returns:
            模型名称列表
        """
        models = self.model_manager.get_all_models()
        return list(models.keys())
    
    def get_model_details(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型详细信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型详细信息
        """
        model_info = self.model_manager.get_model_info(model_name)
        if not model_info:
            return None
        
        # 获取模型性能
        performance = {}
        for task_type in ["问答", "分析", "生成", "报告"]:
            perf = self.model_manager.get_model_performance(model_name, task_type)
            if perf:
                performance[task_type] = {
                    "accuracy": perf.accuracy,
                    "avg_time": perf.avg_time,
                    "cost": perf.cost,
                    "usage_count": perf.usage_count
                }
        
        return {
            "name": model_info.name,
            "type": model_info.type,
            "endpoint": model_info.endpoint,
            "parameters": model_info.parameters,
            "performance": performance
        }


# 全局扩展器实例
model_extender: Optional[ModelExtender] = None


def get_model_extender() -> ModelExtender:
    """获取模型扩展器实例"""
    global model_extender
    if model_extender is None:
        model_extender = ModelExtender()
    return model_extender


def add_model(model_name: str, model_type: str, endpoint: str, 
              api_key: str, parameters: Dict[str, Any]):
    """添加新模型"""
    extender = get_model_extender()
    return extender.add_model(model_name, model_type, endpoint, api_key, parameters)


def remove_model(model_name: str):
    """移除模型"""
    extender = get_model_extender()
    return extender.remove_model(model_name)


def update_model(model_name: str, **kwargs):
    """更新模型信息"""
    extender = get_model_extender()
    return extender.update_model(model_name, **kwargs)


def list_models() -> List[str]:
    """列出所有模型"""
    extender = get_model_extender()
    return extender.list_models()


def get_model_details(model_name: str) -> Optional[Dict[str, Any]]:
    """获取模型详细信息"""
    extender = get_model_extender()
    return extender.get_model_details(model_name)
