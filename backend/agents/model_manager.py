"""
模型管理模块
维护模型性能-成本映射表
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """模型信息"""
    name: str  # 模型名称
    type: str  # 模型类型，如"轻量"、"大型"
    endpoint: str  # 模型端点
    api_key: str  # API密钥
    parameters: Dict[str, Any]  # 模型参数


@dataclass
class ModelPerformance:
    """模型性能"""
    accuracy: float  # 准确率
    avg_time: float  # 平均耗时（秒）
    cost: float  # 调用成本（元）
    usage_count: int  # 使用次数
    last_updated: float  # 最后更新时间


class ModelManager:
    """模型管理器"""
    
    def __init__(self, mapping_file: str = None):
        self.mapping_file = mapping_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "model_performance_mapping.json"
        )
        self.models = self._load_models()
        self.performance_mapping = self._load_performance_mapping()
    
    def _load_models(self) -> Dict[str, ModelInfo]:
        """加载模型信息"""
        # 预定义模型信息
        models = {
            "qwen-1.8b": ModelInfo(
                name="Qwen-1.8B",
                type="轻量",
                endpoint="http://localhost:8001/api/chat",
                api_key="",
                parameters={"temperature": 0.7, "max_tokens": 512}
            ),
            "deepseek": ModelInfo(
                name="DeepSeek",
                type="大型",
                endpoint="https://api.deepseek.com/v1/chat/completions",
                api_key="sk-efbefa84afed4e358498aca72724fc7b",
                parameters={"temperature": 0.7, "max_tokens": 2048}
            )
        }
        return models
    
    def _load_performance_mapping(self) -> Dict[str, Dict[str, ModelPerformance]]:
        """加载性能映射表"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 转换为ModelPerformance对象
                    mapping = {}
                    for model_name, task_performance in data.items():
                        mapping[model_name] = {}
                        for task_type, perf_data in task_performance.items():
                            mapping[model_name][task_type] = ModelPerformance(**perf_data)
                    return mapping
            else:
                # 创建默认映射表
                return self._create_default_mapping()
        except Exception as e:
            logger.error(f"加载性能映射表失败: {e}")
            return self._create_default_mapping()
    
    def _create_default_mapping(self) -> Dict[str, Dict[str, ModelPerformance]]:
        """创建默认性能映射表"""
        import time
        current_time = time.time()
        
        mapping = {
            "qwen-1.8b": {
                "问答": ModelPerformance(
                    accuracy=0.92,
                    avg_time=0.3,
                    cost=0.0005,
                    usage_count=0,
                    last_updated=current_time
                ),
                "分析": ModelPerformance(
                    accuracy=0.85,
                    avg_time=0.5,
                    cost=0.0008,
                    usage_count=0,
                    last_updated=current_time
                ),
                "生成": ModelPerformance(
                    accuracy=0.80,
                    avg_time=0.7,
                    cost=0.001,
                    usage_count=0,
                    last_updated=current_time
                ),
                "报告": ModelPerformance(
                    accuracy=0.75,
                    avg_time=1.0,
                    cost=0.0015,
                    usage_count=0,
                    last_updated=current_time
                )
            },
            "deepseek": {
                "问答": ModelPerformance(
                    accuracy=0.98,
                    avg_time=1.2,
                    cost=0.02,
                    usage_count=0,
                    last_updated=current_time
                ),
                "分析": ModelPerformance(
                    accuracy=0.95,
                    avg_time=1.5,
                    cost=0.025,
                    usage_count=0,
                    last_updated=current_time
                ),
                "生成": ModelPerformance(
                    accuracy=0.92,
                    avg_time=2.0,
                    cost=0.03,
                    usage_count=0,
                    last_updated=current_time
                ),
                "报告": ModelPerformance(
                    accuracy=0.90,
                    avg_time=2.5,
                    cost=0.035,
                    usage_count=0,
                    last_updated=current_time
                )
            }
        }
        
        # 保存默认映射表
        self._save_performance_mapping(mapping)
        return mapping
    
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
            
            os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
            with open(self.mapping_file, "w", encoding="utf-8") as f:
                json.dump(serializable_mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存性能映射表失败: {e}")
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """获取模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型信息
        """
        return self.models.get(model_name)
    
    def get_model_performance(self, model_name: str, task_type: str) -> Optional[ModelPerformance]:
        """获取模型性能
        
        Args:
            model_name: 模型名称
            task_type: 任务类型
            
        Returns:
            模型性能
        """
        if model_name in self.performance_mapping:
            return self.performance_mapping[model_name].get(task_type)
        return None
    
    def update_model_performance(self, model_name: str, task_type: str, time_taken: float, cost: float):
        """更新模型性能
        
        Args:
            model_name: 模型名称
            task_type: 任务类型
            time_taken: 实际耗时
            cost: 实际成本
        """
        import time
        current_time = time.time()
        
        if model_name not in self.performance_mapping:
            self.performance_mapping[model_name] = {}
        
        if task_type not in self.performance_mapping[model_name]:
            # 创建新的性能记录
            self.performance_mapping[model_name][task_type] = ModelPerformance(
                accuracy=0.0,
                avg_time=time_taken,
                cost=cost,
                usage_count=1,
                last_updated=current_time
            )
        else:
            # 更新现有性能记录
            perf = self.performance_mapping[model_name][task_type]
            total_time = perf.avg_time * perf.usage_count + time_taken
            total_cost = perf.cost * perf.usage_count + cost
            perf.usage_count += 1
            perf.avg_time = total_time / perf.usage_count
            perf.cost = total_cost / perf.usage_count
            perf.last_updated = current_time
        
        # 保存更新后的映射表
        self._save_performance_mapping(self.performance_mapping)
        logger.info(f"更新模型性能: {model_name} - {task_type} - 耗时: {time_taken:.2f}s, 成本: ¥{cost:.4f}")
    
    def get_models_by_task_type(self, task_type: str) -> List[Tuple[str, ModelPerformance]]:
        """根据任务类型获取模型列表
        
        Args:
            task_type: 任务类型
            
        Returns:
            模型名称和性能列表
        """
        models = []
        for model_name, task_performance in self.performance_mapping.items():
            if task_type in task_performance:
                models.append((model_name, task_performance[task_type]))
        return models
    
    def add_model(self, model_info: ModelInfo):
        """添加新模型
        
        Args:
            model_info: 模型信息
        """
        self.models[model_info.name.lower().replace(" ", "-")] = model_info
        logger.info(f"添加新模型: {model_info.name}")
    
    def remove_model(self, model_name: str):
        """移除模型
        
        Args:
            model_name: 模型名称
        """
        if model_name in self.models:
            del self.models[model_name]
        if model_name in self.performance_mapping:
            del self.performance_mapping[model_name]
        logger.info(f"移除模型: {model_name}")
    
    def get_all_models(self) -> Dict[str, ModelInfo]:
        """获取所有模型
        
        Returns:
            模型信息字典
        """
        return self.models
    
    def get_performance_mapping(self) -> Dict[str, Dict[str, ModelPerformance]]:
        """获取性能映射表
        
        Returns:
            性能映射表
        """
        return self.performance_mapping


# 全局管理器实例
model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """获取模型管理器实例"""
    global model_manager
    if model_manager is None:
        model_manager = ModelManager()
    return model_manager


def get_model_info(model_name: str) -> Optional[ModelInfo]:
    """获取模型信息"""
    manager = get_model_manager()
    return manager.get_model_info(model_name)


def get_model_performance(model_name: str, task_type: str) -> Optional[ModelPerformance]:
    """获取模型性能"""
    manager = get_model_manager()
    return manager.get_model_performance(model_name, task_type)


def update_model_performance(model_name: str, task_type: str, time_taken: float, cost: float):
    """更新模型性能"""
    manager = get_model_manager()
    manager.update_model_performance(model_name, task_type, time_taken, cost)


def get_models_by_task_type(task_type: str) -> List[Tuple[str, ModelPerformance]]:
    """根据任务类型获取模型列表"""
    manager = get_model_manager()
    return manager.get_models_by_task_type(task_type)
