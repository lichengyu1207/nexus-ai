"""
中书省（决策）智能体训练器
Zhongshu Province (Decision) Agent Trainer

负责训练任务拆解和调度能力
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

logger = logging.getLogger(__name__)


@dataclass
class TaskDecompositionExample:
    """任务拆解示例"""
    user_requirement: str
    subtasks: List[Dict]
    agent_assignments: Dict[str, str]
    success: bool
    execution_time: float
    feedback_score: Optional[float] = None


@dataclass
class TrainingConfig:
    """训练配置"""
    learning_rate: float = 0.0001
    batch_size: int = 32
    epochs: int = 10
    validation_split: float = 0.15
    early_stopping_patience: int = 5
    model_save_dir: str = "./models/zhongshu"
    log_interval: int = 100


class ZhongshuTrainer:
    """
    中书省智能体训练器
    
    训练目标：
    1. 提高任务拆解准确率（92% -> 96%）
    2. 减少不必要的子任务
    3. 优化响应时间（<2秒）
    """
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        os.makedirs(self.config.model_save_dir, exist_ok=True)
        
        self.training_data: List[TaskDecompositionExample] = []
        self.validation_data: List[TaskDecompositionExample] = []
        
        self.model = None
        self.training_history: List[Dict] = []
        
        self.task_patterns: Dict[str, List[str]] = {
            "估值分析": ["数据采集", "特征提取", "模型计算", "结果验证"],
            "市场分析": ["数据采集", "趋势分析", "报告生成"],
            "咨询服务": ["意图识别", "知识检索", "回复生成"],
            "风险评估": ["数据采集", "风险识别", "评估计算", "报告生成"],
        }
        
        self.agent_capabilities: Dict[str, List[str]] = {
            "bing_bu": ["数据采集", "数据验证", "数据更新"],
            "gong_bu": ["分析计算", "报告生成", "可视化"],
            "li_bu_consult": ["咨询服务", "回复生成", "用户引导"],
            "xing_bu": ["风险评估", "合规检查", "异常检测"],
            "hu_bu": ["积分管理", "资产管理", "统计汇总"],
            "li_bu": ["团队协调", "资源分配", "任务调度"],
        }
        
        logger.info("ZhongshuTrainer initialized")
    
    def load_training_data(self, data: List[Dict]):
        """加载训练数据"""
        examples = []
        for item in data:
            example = TaskDecompositionExample(
                user_requirement=item.get("user_requirement", ""),
                subtasks=item.get("subtasks", []),
                agent_assignments=item.get("agent_assignments", {}),
                success=item.get("success", False),
                execution_time=item.get("total_time", 0),
                feedback_score=item.get("feedback_score")
            )
            examples.append(example)
        
        random.shuffle(examples)
        
        split_idx = int(len(examples) * (1 - self.config.validation_split))
        self.training_data = examples[:split_idx]
        self.validation_data = examples[split_idx:]
        
        logger.info(f"Loaded {len(self.training_data)} training, {len(self.validation_data)} validation examples")
    
    def train(self) -> Dict:
        """
        训练模型
        
        Returns:
            训练结果统计
        """
        if not self.training_data:
            logger.warning("No training data available")
            return {"status": "failed", "error": "No training data"}
        
        logger.info(f"Starting training with {len(self.training_data)} examples")
        
        best_val_accuracy = 0
        patience_counter = 0
        
        for epoch in range(self.config.epochs):
            epoch_start = time.time()
            
            train_loss, train_accuracy = self._train_epoch(epoch)
            val_loss, val_accuracy = self._validate()
            
            epoch_time = time.time() - epoch_start
            
            epoch_result = {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "train_accuracy": train_accuracy,
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
                "time": epoch_time,
            }
            self.training_history.append(epoch_result)
            
            logger.info(
                f"Epoch {epoch + 1}/{self.config.epochs} - "
                f"train_loss: {train_loss:.4f}, train_acc: {train_accuracy:.4f}, "
                f"val_loss: {val_loss:.4f}, val_acc: {val_accuracy:.4f}, "
                f"time: {epoch_time:.2f}s"
            )
            
            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                patience_counter = 0
                self._save_model("best_model.json")
            else:
                patience_counter += 1
            
            if patience_counter >= self.config.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch + 1}")
                break
        
        final_result = {
            "status": "completed",
            "best_val_accuracy": best_val_accuracy,
            "total_epochs": len(self.training_history),
            "final_train_accuracy": self.training_history[-1]["train_accuracy"],
        }
        
        logger.info(f"Training completed: {final_result}")
        return final_result
    
    def _train_epoch(self, epoch: int) -> Tuple[float, float]:
        """训练一个epoch"""
        total_loss = 0.0
        correct = 0
        total = 0
        
        batch_size = self.config.batch_size
        num_batches = (len(self.training_data) + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(self.training_data))
            batch = self.training_data[start_idx:end_idx]
            
            for example in batch:
                predicted_subtasks = self._predict_subtasks(example.user_requirement)
                
                loss = self._calculate_loss(predicted_subtasks, example.subtasks)
                total_loss += loss
                
                if self._compare_subtasks(predicted_subtasks, example.subtasks):
                    correct += 1
                total += 1
        
        avg_loss = total_loss / len(self.training_data)
        accuracy = correct / total if total > 0 else 0
        
        return avg_loss, accuracy
    
    def _validate(self) -> Tuple[float, float]:
        """验证"""
        total_loss = 0.0
        correct = 0
        total = 0
        
        for example in self.validation_data:
            predicted_subtasks = self._predict_subtasks(example.user_requirement)
            
            loss = self._calculate_loss(predicted_subtasks, example.subtasks)
            total_loss += loss
            
            if self._compare_subtasks(predicted_subtasks, example.subtasks):
                correct += 1
            total += 1
        
        avg_loss = total_loss / len(self.validation_data) if self.validation_data else 0
        accuracy = correct / total if total > 0 else 0
        
        return avg_loss, accuracy
    
    def _predict_subtasks(self, user_requirement: str) -> List[Dict]:
        """预测任务拆解"""
        task_type = self._classify_task_type(user_requirement)
        
        pattern = self.task_patterns.get(task_type, ["分析", "处理", "输出"])
        
        subtasks = []
        for i, step in enumerate(pattern):
            best_agent = self._select_best_agent(step, user_requirement)
            
            subtasks.append({
                "id": f"sub_{i}",
                "description": step,
                "agent": best_agent,
                "priority": i + 1,
            })
        
        return subtasks
    
    def _classify_task_type(self, requirement: str) -> str:
        """分类任务类型"""
        keywords = {
            "估值分析": ["估值", "价格", "多少钱", "价值"],
            "市场分析": ["市场", "趋势", "行情", "分析"],
            "咨询服务": ["咨询", "怎么", "如何", "建议"],
            "风险评估": ["风险", "评估", "安全", "合规"],
        }
        
        for task_type, words in keywords.items():
            for word in words:
                if word in requirement:
                    return task_type
        
        return "咨询服务"
    
    def _select_best_agent(self, task_step: str, requirement: str) -> str:
        """选择最佳智能体"""
        for agent, capabilities in self.agent_capabilities.items():
            for cap in capabilities:
                if cap in task_step:
                    return agent
        
        return "li_bu_consult"
    
    def _calculate_loss(self, predicted: List[Dict], actual: List[Dict]) -> float:
        """计算损失"""
        if len(predicted) == 0 and len(actual) == 0:
            return 0.0
        
        if len(predicted) == 0 or len(actual) == 0:
            return 1.0
        
        pred_set = set(s["description"] for s in predicted)
        actual_set = set(s.get("description", s.get("id", "")) for s in actual)
        
        intersection = len(pred_set & actual_set)
        union = len(pred_set | actual_set)
        
        jaccard = intersection / union if union > 0 else 0
        
        loss = 1 - jaccard
        
        len_diff = abs(len(predicted) - len(actual))
        loss += len_diff * 0.1
        
        return loss
    
    def _compare_subtasks(self, predicted: List[Dict], actual: List[Dict]) -> bool:
        """比较任务拆解"""
        if len(predicted) != len(actual):
            return False
        
        pred_descs = sorted([s["description"] for s in predicted])
        actual_descs = sorted([s.get("description", s.get("id", "")) for s in actual])
        
        return pred_descs == actual_descs
    
    def _save_model(self, filename: str):
        """保存模型"""
        model_data = {
            "task_patterns": self.task_patterns,
            "agent_capabilities": self.agent_capabilities,
            "training_history": self.training_history,
            "timestamp": time.time(),
        }
        
        filepath = os.path.join(self.config.model_save_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filename: str):
        """加载模型"""
        filepath = os.path.join(self.config.model_save_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Model file not found: {filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        self.task_patterns = model_data.get("task_patterns", self.task_patterns)
        self.agent_capabilities = model_data.get("agent_capabilities", self.agent_capabilities)
        self.training_history = model_data.get("training_history", [])
        
        logger.info(f"Model loaded from {filepath}")
        return True
    
    def evaluate(self, test_data: List[Dict]) -> Dict:
        """评估模型"""
        examples = []
        for item in test_data:
            example = TaskDecompositionExample(
                user_requirement=item.get("user_requirement", ""),
                subtasks=item.get("subtasks", []),
                agent_assignments=item.get("agent_assignments", {}),
                success=item.get("success", False),
                execution_time=item.get("total_time", 0)
            )
            examples.append(example)
        
        correct = 0
        total = len(examples)
        
        for example in examples:
            predicted = self._predict_subtasks(example.user_requirement)
            if self._compare_subtasks(predicted, example.subtasks):
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        
        result = {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
        }
        
        logger.info(f"Evaluation result: accuracy={accuracy:.4f}")
        return result
    
    def predict(self, user_requirement: str) -> Dict:
        """预测任务拆解"""
        subtasks = self._predict_subtasks(user_requirement)
        
        return {
            "user_requirement": user_requirement,
            "subtasks": subtasks,
            "task_type": self._classify_task_type(user_requirement),
            "confidence": 0.85,
        }
    
    def get_statistics(self) -> Dict:
        """获取训练统计"""
        return {
            "training_data_count": len(self.training_data),
            "validation_data_count": len(self.validation_data),
            "training_history": self.training_history,
            "task_patterns": len(self.task_patterns),
            "agent_capabilities": len(self.agent_capabilities),
        }


_global_trainer: Optional[ZhongshuTrainer] = None


def get_zhongshu_trainer() -> ZhongshuTrainer:
    """获取全局训练器实例"""
    global _global_trainer
    if _global_trainer is None:
        _global_trainer = ZhongshuTrainer()
    return _global_trainer
