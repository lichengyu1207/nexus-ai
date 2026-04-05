"""
元认知模块
Meta-Cognition Module

实现智能体的自我监控、偏差检测、归因分析和建议生成
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class AttributionCategory(Enum):
    DATA_DRIFT = "data_drift"
    MODEL_DECAY = "model_decay"
    ENV_CHANGE = "env_change"
    OTHER = "other"


@dataclass
class DiagnosisResult:
    agent_id: str
    is_anomaly: bool
    anomaly_score: float
    attribution: str
    suggestion: str
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrajectoryRecord:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    timestamp: float
    metadata: Dict = field(default_factory=dict)


class AnomalyDetector(nn.Module):
    
    def __init__(self, input_dim: int = 128, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class AttributionNetwork(nn.Module):
    
    def __init__(self, input_dim: int = 64, n_categories: int = 4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, n_categories)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MetaCognitionModule:
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        state_dim: int = 13,
        action_dim: int = 8,
        trajectory_window: int = 1000,
        anomaly_threshold: float = 3.0,
        device: str = "cpu"
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.trajectory_window = trajectory_window
        self.anomaly_threshold = anomaly_threshold
        self.device = device
        
        self.trajectory_buffer: deque = deque(maxlen=trajectory_window)
        
        self.performance_stats = {
            "reward_mean": 0.0,
            "reward_std": 0.0,
            "action_counts": np.zeros(action_dim),
            "success_rate": 0.0,
            "avg_response_time": 0.0
        }
        
        self.anomaly_detector = AnomalyDetector(state_dim * 2, 64)
        self.attribution_net = AttributionNetwork(64, 4)
        
        self.diagnosis_history: List[DiagnosisResult] = []
        self.bus: Optional[Any] = None
    
    def set_bus(self, bus):
        self.bus = bus
    
    def monitor(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        metadata: Optional[Dict] = None
    ):
        record = TrajectoryRecord(
            state=state.copy() if isinstance(state, np.ndarray) else np.array(state),
            action=action,
            reward=reward,
            next_state=next_state.copy() if isinstance(next_state, np.ndarray) else np.array(next_state),
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.trajectory_buffer.append(record)
        self._update_stats(reward, action)
        
        if len(self.trajectory_buffer) >= 100:
            self._check_and_diagnose()
    
    def _update_stats(self, reward: float, action: int):
        alpha = 0.01
        self.performance_stats["reward_mean"] = (
            (1 - alpha) * self.performance_stats["reward_mean"] + alpha * reward
        )
        
        recent_rewards = [r.reward for r in list(self.trajectory_buffer)[-100:]]
        if len(recent_rewards) >= 2:
            self.performance_stats["reward_std"] = np.std(recent_rewards)
        
        self.performance_stats["action_counts"][action] += 1
        
        success_rate = 1.0 if reward > 0 else 0.0
        self.performance_stats["success_rate"] = (
            (1 - alpha) * self.performance_stats["success_rate"] + alpha * success_rate
        )
    
    def _check_and_diagnose(self):
        is_anomaly, anomaly_score = self.detect_anomaly()
        
        if is_anomaly:
            attribution = self.attribute()
            suggestion = self.generate_suggestion(anomaly_score, attribution)
            
            diagnosis = DiagnosisResult(
                agent_id=self.agent_id,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                attribution=attribution,
                suggestion=suggestion,
                metrics={
                    "reward_mean": self.performance_stats["reward_mean"],
                    "reward_std": self.performance_stats["reward_std"],
                    "success_rate": self.performance_stats["success_rate"],
                    "trajectory_size": len(self.trajectory_buffer)
                }
            )
            
            self.diagnosis_history.append(diagnosis)
            
            if self.bus:
                self.bus.publish_diagnosis(diagnosis.to_dict())
            
            logger.warning(
                f"Anomaly detected for {self.agent_name}: "
                f"score={anomaly_score:.2f}, attribution={attribution}"
            )
    
    def detect_anomaly(self) -> Tuple[bool, float]:
        if len(self.trajectory_buffer) < 100:
            return False, 0.0
        
        recent = list(self.trajectory_buffer)[-100:]
        recent_rewards = [r.reward for r in recent]
        recent_mean = np.mean(recent_rewards)
        recent_std = np.std(recent_rewards)
        
        hist_mean = self.performance_stats["reward_mean"]
        hist_std = self.performance_stats["reward_std"]
        
        if hist_std < 0.01:
            return False, 0.0
        
        z_score = abs(recent_mean - hist_mean) / (hist_std + 1e-8)
        
        is_anomaly = abs(z_score) > self.anomaly_threshold
        
        return is_anomaly, z_score
    
    def attribute(self) -> str:
        if len(self.trajectory_buffer) < 50:
            return AttributionCategory.OTHER.value
        
        features = self._extract_features()
        features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.attribution_net(features_tensor)
            category_idx = torch.argmax(logits, dim=-1).item()
        
        categories = [
            AttributionCategory.DATA_DRIFT.value,
            AttributionCategory.MODEL_DECAY.value,
            AttributionCategory.ENV_CHANGE.value,
            AttributionCategory.OTHER.value
        ]
        
        return categories[category_idx]
    
    def _extract_features(self) -> np.ndarray:
        recent = list(self.trajectory_buffer)[-50:]
        
        rewards = [r.reward for r in recent]
        states = [r.state for r in recent]
        actions = [r.action for r in recent]
        
        features = np.zeros(64)
        features[0] = np.mean(rewards)
        features[1] = np.std(rewards)
        features[2] = len(self.trajectory_buffer) / self.trajectory_window
        features[3] = np.mean([s.mean() for s in states])
        features[4] = np.std([s.std() for s in states])
        features[5] = np.mean(actions)
        features[6] = len(set(actions)) / self.action_dim
        
        features[7] = self.performance_stats["success_rate"]
        
        if len(self.diagnosis_history) > 0:
            recent_diag = self.diagnosis_history[-1]
            features[8] = recent_diag.anomaly_score
        else:
            features[8] = 0.0
        
        return features
    
    def generate_suggestion(self, anomaly_score: float, attribution: str) -> str:
        templates = {
            AttributionCategory.DATA_DRIFT.value: (
                f"智能体 {self.agent_name} 检测到数据分布漂移（异常分数: {anomaly_score:.2f}）。"
                f"近期平均奖励: {self.performance_stats['reward_mean']:.4f}，历史平均: {self.performance_stats['reward_mean']:.4f}。"
                f"建议：检查输入数据源是否发生变化，考虑重新采集训练数据或更新数据预处理流程。"
            ),
            AttributionCategory.MODEL_DECAY.value: (
                f"智能体 {self.agent_name} 检测到模型性能衰减（异常分数: {anomaly_score:.2f}）。"
                f"近期成功率: {self.performance_stats['success_rate']:.2%}。"
                f"建议：考虑使用最新数据重新训练模型，或调整学习率进行微调。"
            ),
            AttributionCategory.ENV_CHANGE.value: (
                f"智能体 {self.agent_name} 检测到环境变化（异常分数: {anomaly_score:.2f}）。"
                f"建议：检查外部环境配置，更新环境参数，或重新设计奖励函数。"
            ),
            AttributionCategory.OTHER.value: (
                f"智能体 {self.agent_name} 检测到异常行为（异常分数: {anomaly_score:.2f}）。"
                f"建议：进一步分析具体原因，可能需要增加监控维度或调整异常阈值。"
            )
        }
        
        return templates.get(attribution, templates[AttributionCategory.OTHER.value])
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "trajectory_size": len(self.trajectory_buffer),
            "performance_stats": self.performance_stats.copy(),
            "diagnosis_count": len(self.diagnosis_history),
            "last_diagnosis": self.diagnosis_history[-1].to_dict() if self.diagnosis_history else None
        }
    
    def to_dict(self) -> Dict:
        return self.get_status()


class MetaCognitionBus:
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.diagnosis_channel = "meta:diagnosis"
        self.suggestion_channel = "meta:suggestions"
        self.subscribers: Dict[str, List[Callable]] = {}
        
        try:
            import redis
            self.redis_client = redis.from_url(redis_url)
        except ImportError:
            self.redis_client = None
    
    def publish_diagnosis(self, diagnosis: Dict):
        message = json.dumps({
            "type": "diagnosis",
            "data": diagnosis,
            "timestamp": datetime.now().isoformat()
        })
        
        if self.redis_client:
            self.redis_client.publish(self.diagnosis_channel, message)
        
        for callback in self.subscribers.get("diagnosis", []):
            try:
                callback(diagnosis)
            except Exception as e:
                logger.error(f"Diagnosis callback error: {e}")
    
    def subscribe_diagnosis(self, callback: Callable):
        if "diagnosis" not in self.subscribers:
            self.subscribers["diagnosis"] = []
        self.subscribers["diagnosis"].append(callback)
    
    def publish_suggestion(self, suggestion: Dict):
        message = json.dumps({
            "type": "suggestion",
            "data": suggestion,
            "timestamp": datetime.now().isoformat()
        })
        
        if self.redis_client:
            self.redis_client.publish(self.suggestion_channel, message)
        
        for callback in self.subscribers.get("suggestion", []):
            try:
                callback(suggestion)
            except Exception as e:
                logger.error(f"Suggestion callback error: {e}")
    
    def subscribe_suggestions(self, callback: Callable):
        if "suggestion" not in self.subscribers:
            self.subscribers["suggestion"] = []
        self.subscribers["suggestion"].append(callback)
    
    def get_stats(self) -> Dict:
        return {
            "diagnosis_subscribers": len(self.subscribers.get("diagnosis", [])),
            "suggestion_subscribers": len(self.subscribers.get("suggestion", [])),
            "redis_connected": self.redis_client is not None
        }


meta_bus = MetaCognitionBus()
