"""
训练数据收集和处理系统
Training Data Collection and Processing System

收集历史对话、任务执行、用户反馈等数据
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class DialogueRecord:
    """对话记录"""
    session_id: str
    user_input: str
    agent_reply: str
    agent_type: str
    task_id: Optional[str] = None
    response_time: float = 0.0
    user_rating: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


@dataclass
class TaskRecord:
    """任务记录"""
    task_id: str
    user_requirement: str
    subtasks: List[Dict]
    agent_assignments: Dict[str, str]
    execution_status: Dict[str, str]
    final_output: Optional[Dict] = None
    total_time: float = 0.0
    success: bool = False
    error_logs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ValuationRecord:
    """估值记录"""
    property_id: str
    property_info: Dict
    model_output: float
    actual_price: Optional[float] = None
    error_rate: Optional[float] = None
    confidence: float = 0.0
    features_used: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ComplianceRecord:
    """合规记录"""
    operation_id: str
    operation_type: str
    agent_id: str
    is_compliant: bool
    violation_type: Optional[str] = None
    audit_result: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class TrainingDataCollector:
    """
    训练数据收集器
    
    收集并处理各类训练数据：
    1. 对话数据
    2. 任务执行数据
    3. 估值对比数据
    4. 合规检查数据
    5. 用户反馈数据
    """
    
    def __init__(self, data_dir: str = "./training_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.dialogues: List[DialogueRecord] = []
        self.tasks: List[TaskRecord] = []
        self.valuations: List[ValuationRecord] = []
        self.compliances: List[ComplianceRecord] = []
        
        self.expert_demonstrations: List[Dict] = []
        self.user_feedbacks: Dict[str, List[Dict]] = defaultdict(list)
        
        self._load_existing_data()
        
        logger.info(f"TrainingDataCollector initialized with data_dir={data_dir}")
    
    def _load_existing_data(self):
        """加载已有数据"""
        dialogue_file = os.path.join(self.data_dir, "dialogues.json")
        if os.path.exists(dialogue_file):
            try:
                with open(dialogue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.dialogues = [DialogueRecord(**d) for d in data]
                logger.info(f"Loaded {len(self.dialogues)} dialogue records")
            except Exception as e:
                logger.error(f"Failed to load dialogues: {e}")
        
        task_file = os.path.join(self.data_dir, "tasks.json")
        if os.path.exists(task_file):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [TaskRecord(**t) for t in data]
                logger.info(f"Loaded {len(self.tasks)} task records")
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")
        
        valuation_file = os.path.join(self.data_dir, "valuations.json")
        if os.path.exists(valuation_file):
            try:
                with open(valuation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.valuations = [ValuationRecord(**v) for v in data]
                logger.info(f"Loaded {len(self.valuations)} valuation records")
            except Exception as e:
                logger.error(f"Failed to load valuations: {e}")
    
    def record_dialogue(
        self,
        session_id: str,
        user_input: str,
        agent_reply: str,
        agent_type: str,
        task_id: Optional[str] = None,
        response_time: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> DialogueRecord:
        """记录对话"""
        record = DialogueRecord(
            session_id=session_id,
            user_input=user_input,
            agent_reply=agent_reply,
            agent_type=agent_type,
            task_id=task_id,
            response_time=response_time,
            metadata=metadata or {}
        )
        
        self.dialogues.append(record)
        self._save_dialogues()
        
        logger.debug(f"Recorded dialogue: session={session_id}, agent={agent_type}")
        return record
    
    def record_task(
        self,
        task_id: str,
        user_requirement: str,
        subtasks: List[Dict],
        agent_assignments: Dict[str, str],
        execution_status: Dict[str, str],
        final_output: Optional[Dict] = None,
        total_time: float = 0.0,
        success: bool = False,
        error_logs: Optional[List[str]] = None
    ) -> TaskRecord:
        """记录任务执行"""
        record = TaskRecord(
            task_id=task_id,
            user_requirement=user_requirement,
            subtasks=subtasks,
            agent_assignments=agent_assignments,
            execution_status=execution_status,
            final_output=final_output,
            total_time=total_time,
            success=success,
            error_logs=error_logs or []
        )
        
        self.tasks.append(record)
        self._save_tasks()
        
        logger.debug(f"Recorded task: id={task_id}, success={success}")
        return record
    
    def record_valuation(
        self,
        property_id: str,
        property_info: Dict,
        model_output: float,
        actual_price: Optional[float] = None,
        confidence: float = 0.0,
        features_used: Optional[List[str]] = None
    ) -> ValuationRecord:
        """记录估值结果"""
        error_rate = None
        if actual_price is not None and actual_price > 0:
            error_rate = abs(model_output - actual_price) / actual_price
        
        record = ValuationRecord(
            property_id=property_id,
            property_info=property_info,
            model_output=model_output,
            actual_price=actual_price,
            error_rate=error_rate,
            confidence=confidence,
            features_used=features_used or []
        )
        
        self.valuations.append(record)
        self._save_valuations()
        
        logger.debug(f"Recorded valuation: property={property_id}, error_rate={error_rate}")
        return record
    
    def record_compliance(
        self,
        operation_id: str,
        operation_type: str,
        agent_id: str,
        is_compliant: bool,
        violation_type: Optional[str] = None,
        audit_result: Optional[Dict] = None
    ) -> ComplianceRecord:
        """记录合规检查"""
        record = ComplianceRecord(
            operation_id=operation_id,
            operation_type=operation_type,
            agent_id=agent_id,
            is_compliant=is_compliant,
            violation_type=violation_type,
            audit_result=audit_result or {}
        )
        
        self.compliances.append(record)
        
        logger.debug(f"Recorded compliance: operation={operation_id}, compliant={is_compliant}")
        return record
    
    def add_user_feedback(
        self,
        session_id: str,
        rating: int,
        comment: Optional[str] = None,
        feedback_type: str = "general"
    ):
        """添加用户反馈"""
        feedback = {
            "session_id": session_id,
            "rating": rating,
            "comment": comment,
            "feedback_type": feedback_type,
            "timestamp": time.time()
        }
        
        self.user_feedbacks[session_id].append(feedback)
        
        for dialogue in self.dialogues:
            if dialogue.session_id == session_id:
                dialogue.user_rating = rating
                break
        
        self._save_dialogues()
        logger.debug(f"Added user feedback: session={session_id}, rating={rating}")
    
    def add_expert_demonstration(
        self,
        scenario: str,
        user_input: str,
        ideal_task_decomposition: List[str],
        ideal_reply: str,
        expected_valuation: Optional[float] = None,
        confidence: float = 0.95
    ):
        """添加专家示范"""
        demonstration = {
            "scenario": scenario,
            "user_input": user_input,
            "ideal_task_decomposition": ideal_task_decomposition,
            "ideal_reply": ideal_reply,
            "expected_valuation": expected_valuation,
            "confidence": confidence,
            "timestamp": time.time()
        }
        
        self.expert_demonstrations.append(demonstration)
        self._save_expert_demonstrations()
        
        logger.info(f"Added expert demonstration: scenario={scenario}")
    
    def _save_dialogues(self):
        """保存对话数据"""
        filepath = os.path.join(self.data_dir, "dialogues.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(d) for d in self.dialogues], f, ensure_ascii=False, indent=2)
    
    def _save_tasks(self):
        """保存任务数据"""
        filepath = os.path.join(self.data_dir, "tasks.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(t) for t in self.tasks], f, ensure_ascii=False, indent=2)
    
    def _save_valuations(self):
        """保存估值数据"""
        filepath = os.path.join(self.data_dir, "valuations.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(v) for v in self.valuations], f, ensure_ascii=False, indent=2)
    
    def _save_expert_demonstrations(self):
        """保存专家示范"""
        filepath = os.path.join(self.data_dir, "expert_demonstrations.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.expert_demonstrations, f, ensure_ascii=False, indent=2)
    
    def get_training_dataset(
        self,
        data_type: str = "all",
        split_ratio: Tuple[float, float, float] = (0.7, 0.15, 0.15)
    ) -> Dict[str, List]:
        """
        获取训练数据集
        
        Args:
            data_type: 数据类型 (dialogue, task, valuation, all)
            split_ratio: (train, val, test) 比例
            
        Returns:
            {"train": [...], "val": [...], "test": [...]}
        """
        if data_type == "dialogue":
            data = [asdict(d) for d in self.dialogues]
        elif data_type == "task":
            data = [asdict(t) for t in self.tasks]
        elif data_type == "valuation":
            data = [asdict(v) for v in self.valuations]
        else:
            data = {
                "dialogues": [asdict(d) for d in self.dialogues],
                "tasks": [asdict(t) for t in self.tasks],
                "valuations": [asdict(v) for v in self.valuations],
                "expert_demonstrations": self.expert_demonstrations,
            }
            return {"all": data}
        
        random.shuffle(data)
        
        n = len(data)
        train_end = int(n * split_ratio[0])
        val_end = train_end + int(n * split_ratio[1])
        
        return {
            "train": data[:train_end],
            "val": data[train_end:val_end],
            "test": data[val_end:],
        }
    
    def get_statistics(self) -> Dict:
        """获取数据统计信息"""
        stats = {
            "dialogues": {
                "total": len(self.dialogues),
                "with_rating": sum(1 for d in self.dialogues if d.user_rating is not None),
                "avg_response_time": 0.0,
                "by_agent": defaultdict(int),
            },
            "tasks": {
                "total": len(self.tasks),
                "successful": sum(1 for t in self.tasks if t.success),
                "avg_time": 0.0,
            },
            "valuations": {
                "total": len(self.valuations),
                "with_actual_price": sum(1 for v in self.valuations if v.actual_price is not None),
                "avg_error_rate": 0.0,
            },
            "expert_demonstrations": len(self.expert_demonstrations),
            "user_feedbacks": sum(len(v) for v in self.user_feedbacks.values()),
        }
        
        if self.dialogues:
            stats["dialogues"]["avg_response_time"] = sum(d.response_time for d in self.dialogues) / len(self.dialogues)
            for d in self.dialogues:
                stats["dialogues"]["by_agent"][d.agent_type] += 1
        
        if self.tasks:
            stats["tasks"]["avg_time"] = sum(t.total_time for t in self.tasks) / len(self.tasks)
        
        error_rates = [v.error_rate for v in self.valuations if v.error_rate is not None]
        if error_rates:
            stats["valuations"]["avg_error_rate"] = sum(error_rates) / len(error_rates)
        
        return stats
    
    def generate_sample_data(self, num_samples: int = 100):
        """生成示例数据（用于测试）"""
        scenarios = [
            "学区房分析",
            "投资回报评估",
            "购房资格咨询",
            "房产估值",
            "市场趋势分析",
        ]
        
        agent_types = ["li_bu_consult", "gong_bu", "bing_bu", "xing_bu"]
        
        for i in range(num_samples):
            session_id = f"session_{i:04d}"
            user_input = f"帮我分析{random.choice(scenarios)}"
            agent_type = random.choice(agent_types)
            agent_reply = f"关于您的问题，我的建议是..."
            
            self.record_dialogue(
                session_id=session_id,
                user_input=user_input,
                agent_reply=agent_reply,
                agent_type=agent_type,
                response_time=random.uniform(0.5, 3.0)
            )
            
            if random.random() > 0.3:
                self.add_user_feedback(
                    session_id=session_id,
                    rating=random.randint(3, 5)
                )
        
        for i in range(num_samples // 2):
            task_id = f"task_{i:04d}"
            subtasks = [
                {"id": f"sub_{j}", "description": f"子任务{j}", "agent": random.choice(agent_types)}
                for j in range(random.randint(2, 5))
            ]
            
            self.record_task(
                task_id=task_id,
                user_requirement=f"用户需求{i}",
                subtasks=subtasks,
                agent_assignments={s["id"]: s["agent"] for s in subtasks},
                execution_status={s["id"]: "completed" for s in subtasks},
                total_time=random.uniform(5.0, 30.0),
                success=random.random() > 0.1
            )
        
        for i in range(num_samples // 3):
            property_id = f"property_{i:04d}"
            model_output = random.uniform(200, 1000)
            actual_price = model_output * (1 + random.uniform(-0.1, 0.1))
            
            self.record_valuation(
                property_id=property_id,
                property_info={"location": "深圳", "area": random.randint(50, 200)},
                model_output=model_output,
                actual_price=actual_price,
                confidence=random.uniform(0.7, 0.95)
            )
        
        logger.info(f"Generated {num_samples} sample records")


_global_collector: Optional[TrainingDataCollector] = None


def get_data_collector() -> TrainingDataCollector:
    """获取全局数据收集器实例"""
    global _global_collector
    if _global_collector is None:
        _global_collector = TrainingDataCollector()
    return _global_collector
