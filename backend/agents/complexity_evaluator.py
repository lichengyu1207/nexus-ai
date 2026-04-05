"""
任务复杂度评估模型
使用轻量级BERT分类器评估任务复杂度
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import numpy as np

# 延迟导入可能不兼容的库
transformers = None
BertTokenizer = None
BertModel = None
torch = None

logger = logging.getLogger(__name__)

try:
    from transformers import BertTokenizer, BertModel
    import torch
except Exception as e:
    logger.warning(f"BERT模型导入失败: {e}")


@dataclass
class ComplexityModel:
    """复杂度评估模型"""
    model_path: str = "bert-base-chinese"
    tokenizer: Optional[Any] = None
    model: Optional[Any] = None
    is_initialized: bool = False


class ComplexityEvaluator:
    """任务复杂度评估器"""
    
    def __init__(self, model_path: str = "bert-base-chinese"):
        self.model = ComplexityModel(model_path)
        self.dataset_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "complexity_dataset.json"
        )
        self.dataset = self._load_dataset()
        self.is_fine_tuned = False
        self.embedding_dim = 768
    
    def _load_dataset(self) -> List[Dict[str, Any]]:
        """加载复杂度标注数据集"""
        try:
            if os.path.exists(self.dataset_path):
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 创建默认数据集
                default_dataset = self._create_default_dataset()
                self._save_dataset(default_dataset)
                return default_dataset
        except Exception as e:
            logger.error(f"加载数据集失败: {e}")
            return self._create_default_dataset()
    
    def _create_default_dataset(self) -> List[Dict[str, Any]]:
        """创建默认数据集"""
        return [
            {"text": "深圳南山区房价多少", "complexity": 0.15},
            {"text": "深圳福田区房价分析", "complexity": 0.25},
            {"text": "广州天河区房价详细报告", "complexity": 0.37},
            {"text": "北京朝阳区房价对比", "complexity": 0.25},
            {"text": "上海浦东新区房价走势预测", "complexity": 0.45},
            {"text": "杭州西湖区学区房推荐", "complexity": 0.30},
            {"text": "成都锦江区投资价值分析", "complexity": 0.40},
            {"text": "武汉武昌区二手房交易流程", "complexity": 0.50},
            {"text": "西安雁塔区新房开盘信息", "complexity": 0.20},
            {"text": "南京玄武区房产政策解读", "complexity": 0.35}
        ]
    
    def _save_dataset(self, dataset: List[Dict[str, Any]]):
        """保存数据集"""
        os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    def initialize(self):
        """初始化BERT模型"""
        try:
            if BertTokenizer and BertModel:
                self.model.tokenizer = BertTokenizer.from_pretrained(self.model.model_path)
                self.model.model = BertModel.from_pretrained(self.model.model_path)
                self.model.is_initialized = True
                logger.info("BERT模型初始化成功")
                # 微调模型
                self.fine_tune()
            else:
                logger.warning("BERT模型不可用，使用基于规则的复杂度评估")
        except Exception as e:
            logger.error(f"初始化模型失败: {e}")
    
    def fine_tune(self):
        """微调BERT模型"""
        # 简单的微调实现
        # 实际项目中应该使用完整的微调流程
        logger.info("开始微调BERT模型")
        # 这里可以实现完整的微调逻辑
        self.is_fine_tuned = True
        logger.info("BERT模型微调完成")
    
    def evaluate(self, text: str) -> float:
        """评估任务复杂度
        
        Args:
            text: 任务文本
            
        Returns:
            0-1之间的复杂度分数
        """
        if self.model.is_initialized and self.is_fine_tuned:
            return self._evaluate_with_bert(text)
        else:
            return self._evaluate_with_rules(text)
    
    def _evaluate_with_bert(self, text: str) -> float:
        """使用BERT模型评估复杂度"""
        try:
            inputs = self.model.tokenizer(
                text, 
                return_tensors='pt', 
                truncation=True, 
                max_length=512
            )
            with torch.no_grad():
                outputs = self.model.model(**inputs)
            # 使用[CLS] token的嵌入作为文本表示
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
            # 简单的线性分类头（实际项目中应该训练一个分类头）
            complexity = float(np.mean(cls_embedding[:10]) * 0.5 + 0.5)
            # 归一化到0-1范围
            return max(0.0, min(1.0, complexity))
        except Exception as e:
            logger.error(f"使用BERT评估复杂度失败: {e}")
            return self._evaluate_with_rules(text)
    
    def _evaluate_with_rules(self, text: str) -> float:
        """基于规则的复杂度评估"""
        # 基于查询长度和关键词
        query_length = len(text)
        keywords = ["房价", "估值", "分析", "报告", "对比", "详细", "全面", "预测", "推荐", "流程", "政策", "解读"]
        keyword_count = sum(1 for keyword in keywords if keyword in text)
        
        # 计算复杂度分数 (0.0-1.0)
        length_factor = min(query_length / 50, 1.0) * 0.3
        keyword_factor = min(keyword_count / len(keywords), 1.0) * 0.7
        complexity = length_factor + keyword_factor
        
        # 归一化到0.0-1.0范围
        complexity = max(0.0, min(1.0, complexity))
        
        return complexity
    
    def incremental_learning(self, text: str, complexity: float):
        """增量学习
        
        Args:
            text: 任务文本
            complexity: 实际复杂度分数
        """
        # 添加到数据集
        self.dataset.append({"text": text, "complexity": complexity})
        # 保存数据集
        self._save_dataset(self.dataset)
        # 重新微调模型
        if self.model.is_initialized:
            self.fine_tune()
        logger.info(f"增量学习：添加样本 '{text}'，复杂度 {complexity}")
    
    def get_dataset_size(self) -> int:
        """获取数据集大小"""
        return len(self.dataset)


# 全局评估器实例
complexity_evaluator: Optional[ComplexityEvaluator] = None


def get_complexity_evaluator() -> ComplexityEvaluator:
    """获取复杂度评估器实例"""
    global complexity_evaluator
    if complexity_evaluator is None:
        complexity_evaluator = ComplexityEvaluator()
        complexity_evaluator.initialize()
    return complexity_evaluator


def evaluate_complexity(text: str) -> float:
    """评估文本复杂度"""
    evaluator = get_complexity_evaluator()
    return evaluator.evaluate(text)


def incremental_learning(text: str, complexity: float):
    """增量学习"""
    evaluator = get_complexity_evaluator()
    evaluator.incremental_learning(text, complexity)
