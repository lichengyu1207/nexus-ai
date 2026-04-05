"""
联邦学习模块
Federated Learning Module

实现联邦学习框架、差分隐私、安全聚合等功能
"""

import asyncio
import hashlib
import json
import logging
import math
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    TRAINING = "training"
    UPLOADING = "uploading"


class AggregationMethod(Enum):
    FED_AVG = "fed_avg"
    FED_PROX = "fed_prox"
    FED_SGD = "fed_sgd"
    SECURE_AGG = "secure_agg"


@dataclass
class ModelUpdate:
    update_id: str
    node_id: str
    round_num: int
    parameters: Dict[str, List[float]]
    num_samples: int
    metrics: Dict[str, float]
    timestamp: datetime
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "update_id": self.update_id,
            "node_id": self.node_id,
            "round_num": self.round_num,
            "parameters_summary": {
                k: {"shape": len(v), "mean": sum(v)/len(v) if v else 0}
                for k, v in self.parameters.items()
            },
            "num_samples": self.num_samples,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature,
        }


@dataclass
class FederatedNode:
    node_id: str
    name: str
    status: NodeStatus
    data_size: int
    last_seen: datetime
    total_contributions: int
    reputation: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "status": self.status.value,
            "data_size": self.data_size,
            "last_seen": self.last_seen.isoformat(),
            "total_contributions": self.total_contributions,
            "reputation": self.reputation,
        }


class DPModule:
    """差分隐私模块"""
    
    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        max_grad_norm: float = 1.0,
        noise_multiplier: float = 1.0
    ):
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        self.noise_multiplier = noise_multiplier
        
        self.privacy_spent: float = 0.0
        self.noise_history: List[Dict[str, Any]] = []
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_clips": 0,
            "total_noise_added": 0,
            "privacy_budget_used": 0.0,
        }
    
    def clip_gradients(
        self,
        gradients: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        self.stats["total_clips"] += 1
        
        total_norm = 0.0
        for key, grad in gradients.items():
            total_norm += sum(g * g for g in grad)
        total_norm = math.sqrt(total_norm)
        
        clip_factor = 1.0
        if total_norm > self.max_grad_norm:
            clip_factor = self.max_grad_norm / total_norm
        
        clipped = {}
        for key, grad in gradients.items():
            clipped[key] = [g * clip_factor for g in grad]
        
        return clipped
    
    def add_noise(
        self,
        parameters: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        self.stats["total_noise_added"] += 1
        
        noisy_params = {}
        noise_scale = self.noise_multiplier * self.max_grad_norm
        
        for key, params in parameters.items():
            noise = [random.gauss(0, noise_scale) for _ in params]
            noisy_params[key] = [p + n for p, n in zip(params, noise)]
        
        with self._lock:
            self.noise_history.append({
                "timestamp": datetime.now().isoformat(),
                "noise_scale": noise_scale,
                "num_params": sum(len(p) for p in parameters.values()),
            })
        
        return noisy_params
    
    def compute_privacy_spent(
        self,
        num_rounds: int,
        sampling_rate: float
    ) -> float:
        privacy_spent = num_rounds * self.epsilon * sampling_rate
        
        with self._lock:
            self.privacy_spent += privacy_spent
            self.stats["privacy_budget_used"] = self.privacy_spent
        
        return privacy_spent
    
    def get_privacy_budget_remaining(self) -> float:
        return max(0, self.epsilon - self.privacy_spent)
    
    def reset_privacy_budget(self):
        with self._lock:
            self.privacy_spent = 0.0
            self.stats["privacy_budget_used"] = 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "epsilon": self.epsilon,
            "delta": self.delta,
            "privacy_spent": self.privacy_spent,
            "privacy_remaining": self.get_privacy_budget_remaining(),
        }


class DifferentialPrivacy:
    """差分隐私管理器"""
    
    def __init__(
        self,
        target_epsilon: float = 2.0,
        target_delta: float = 1e-5,
        accountant: str = "rdp"
    ):
        self.target_epsilon = target_epsilon
        self.target_delta = target_delta
        self.accountant = accountant
        
        self.epsilon_spent: float = 0.0
        self.delta_spent: float = 0.0
        self.rounds: List[Dict[str, float]] = []
        
        self._lock = threading.Lock()
    
    def accumulate(
        self,
        epsilon: float,
        delta: float = 0.0
    ) -> Tuple[float, float]:
        with self._lock:
            if self.accountant == "rdp":
                self.epsilon_spent += epsilon ** 2
                self.epsilon_spent = math.sqrt(self.epsilon_spent)
            else:
                self.epsilon_spent += epsilon
            
            self.delta_spent += delta
            
            self.rounds.append({
                "epsilon": epsilon,
                "delta": delta,
                "cumulative_epsilon": self.epsilon_spent,
                "cumulative_delta": self.delta_spent,
            })
            
            return self.epsilon_spent, self.delta_spent
    
    def get_budget_remaining(self) -> Tuple[float, float]:
        return (
            max(0, self.target_epsilon - self.epsilon_spent),
            max(0, self.target_delta - self.delta_spent),
        )
    
    def is_budget_exceeded(self) -> bool:
        return self.epsilon_spent >= self.target_epsilon or self.delta_spent >= self.target_delta
    
    def get_composition_info(self) -> Dict[str, Any]:
        return {
            "total_rounds": len(self.rounds),
            "epsilon_spent": self.epsilon_spent,
            "delta_spent": self.delta_spent,
            "target_epsilon": self.target_epsilon,
            "target_delta": self.target_delta,
            "budget_remaining": self.get_budget_remaining(),
            "budget_exceeded": self.is_budget_exceeded(),
        }


class PrivacyBudgetTracker:
    """隐私预算跟踪器"""
    
    def __init__(self, total_budget: float = 10.0):
        self.total_budget = total_budget
        self.used_budget: float = 0.0
        self.allocations: Dict[str, float] = {}
        self.usage_history: List[Dict[str, Any]] = []
        
        self._lock = threading.Lock()
    
    def allocate(
        self,
        operation_id: str,
        epsilon: float
    ) -> bool:
        with self._lock:
            if self.used_budget + epsilon > self.total_budget:
                return False
            
            self.allocations[operation_id] = epsilon
            self.used_budget += epsilon
            
            self.usage_history.append({
                "operation_id": operation_id,
                "epsilon": epsilon,
                "timestamp": datetime.now().isoformat(),
                "remaining": self.total_budget - self.used_budget,
            })
            
            return True
    
    def get_remaining_budget(self) -> float:
        return self.total_budget - self.used_budget
    
    def get_utilization(self) -> float:
        return self.used_budget / self.total_budget


class FedAvgAggregator:
    """联邦平均聚合器"""
    
    def __init__(self):
        self.aggregation_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self.stats = {
            "total_aggregations": 0,
            "total_updates_processed": 0,
        }
    
    def aggregate(
        self,
        updates: List[ModelUpdate],
        global_params: Dict[str, List[float]] = None
    ) -> Dict[str, List[float]]:
        self.stats["total_aggregations"] += 1
        self.stats["total_updates_processed"] += len(updates)
        
        if not updates:
            return global_params or {}
        
        total_samples = sum(u.num_samples for u in updates)
        
        if total_samples == 0:
            return global_params or {}
        
        aggregated = {}
        
        first_update = updates[0]
        for key in first_update.parameters.keys():
            weighted_sum = [0.0] * len(first_update.parameters[key])
            
            for update in updates:
                if key in update.parameters:
                    weight = update.num_samples / total_samples
                    params = update.parameters[key]
                    for i in range(min(len(weighted_sum), len(params))):
                        weighted_sum[i] += weight * params[i]
            
            aggregated[key] = weighted_sum
        
        with self._lock:
            self.aggregation_history.append({
                "timestamp": datetime.now().isoformat(),
                "num_updates": len(updates),
                "total_samples": total_samples,
                "param_keys": list(aggregated.keys()),
            })
        
        return aggregated


class SecureAggregator:
    """安全聚合器"""
    
    def __init__(self, key_size: int = 2048):
        self.key_size = key_size
        self.node_keys: Dict[str, Dict[str, Any]] = {}
        self.aggregation_secrets: Dict[str, bytes] = {}
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_encryptions": 0,
            "total_decryptions": 0,
            "total_secure_aggregations": 0,
        }
    
    def generate_keys(self, node_id: str) -> Dict[str, Any]:
        private_key = hashlib.sha256(f"{node_id}_{time.time()}".encode()).hexdigest()
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        
        keys = {
            "private_key": private_key,
            "public_key": public_key,
            "created_at": datetime.now().isoformat(),
        }
        
        with self._lock:
            self.node_keys[node_id] = keys
        
        return keys
    
    def encrypt_update(
        self,
        update: ModelUpdate,
        node_id: str
    ) -> Dict[str, Any]:
        self.stats["total_encryptions"] += 1
        
        serialized = json.dumps({
            "update_id": update.update_id,
            "parameters": update.parameters,
            "num_samples": update.num_samples,
        })
        
        encrypted = hashlib.sha256((serialized + str(time.time())).encode()).hexdigest()
        
        return {
            "encrypted_data": encrypted,
            "node_id": node_id,
            "timestamp": datetime.now().isoformat(),
        }
    
    def secure_aggregate(
        self,
        encrypted_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        self.stats["total_secure_aggregations"] += 1
        
        combined_hash = hashlib.sha256(
            "".join(u["encrypted_data"] for u in encrypted_updates).encode()
        ).hexdigest()
        
        return {
            "aggregated_hash": combined_hash,
            "num_contributors": len(encrypted_updates),
            "timestamp": datetime.now().isoformat(),
        }


class FederatedLearner:
    """联邦学习主控"""
    
    def __init__(
        self,
        config: Dict[str, Any] = None
    ):
        self.config = config or {}
        
        self.nodes: Dict[str, FederatedNode] = {}
        self.global_model: Dict[str, List[float]] = {}
        self.model_updates: Dict[int, List[ModelUpdate]] = defaultdict(list)
        
        self.current_round = 0
        self.max_rounds = self.config.get("max_rounds", 100)
        self.min_nodes_per_round = self.config.get("min_nodes_per_round", 2)
        
        self.aggregator = FedAvgAggregator()
        self.secure_aggregator = SecureAggregator()
        self.dp_module = DPModule(
            epsilon=self.config.get("epsilon", 1.0),
            delta=self.config.get("delta", 1e-5),
        )
        self.privacy_tracker = DifferentialPrivacy(
            target_epsilon=self.config.get("target_epsilon", 10.0),
        )
        
        self._lock = threading.Lock()
        
        self._running = False
        self._training_task = None
        
        self.stats = {
            "total_rounds": 0,
            "total_updates": 0,
            "avg_participation": 0.0,
            "model_improvements": 0,
        }
    
    def register_node(
        self,
        node_id: str,
        name: str,
        data_size: int
    ) -> bool:
        with self._lock:
            if node_id in self.nodes:
                return False
            
            node = FederatedNode(
                node_id=node_id,
                name=name,
                status=NodeStatus.ONLINE,
                data_size=data_size,
                last_seen=datetime.now(),
                total_contributions=0,
                reputation=1.0,
            )
            
            self.nodes[node_id] = node
            self.secure_aggregator.generate_keys(node_id)
            
            return True
    
    def unregister_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self.nodes:
                self.nodes[node_id].status = NodeStatus.OFFLINE
                return True
            return False
    
    def update_node_status(
        self,
        node_id: str,
        status: NodeStatus
    ):
        with self._lock:
            if node_id in self.nodes:
                self.nodes[node_id].status = status
                self.nodes[node_id].last_seen = datetime.now()
    
    def initialize_global_model(self, model_params: Dict[str, List[float]]):
        with self._lock:
            self.global_model = model_params
    
    def receive_update(
        self,
        node_id: str,
        parameters: Dict[str, List[float]],
        num_samples: int,
        metrics: Dict[str, float] = None
    ) -> str:
        update_id = f"upd_{uuid.uuid4().hex[:8]}"
        
        if self.config.get("differential_privacy", False):
            parameters = self.dp_module.add_noise(parameters)
        
        update = ModelUpdate(
            update_id=update_id,
            node_id=node_id,
            round_num=self.current_round,
            parameters=parameters,
            num_samples=num_samples,
            metrics=metrics or {},
            timestamp=datetime.now(),
        )
        
        with self._lock:
            self.model_updates[self.current_round].append(update)
            self.stats["total_updates"] += 1
            
            if node_id in self.nodes:
                self.nodes[node_id].total_contributions += 1
        
        return update_id
    
    async def run_round(self) -> Dict[str, Any]:
        self.current_round += 1
        self.stats["total_rounds"] += 1
        
        with self._lock:
            online_nodes = [
                n for n in self.nodes.values()
                if n.status in [NodeStatus.ONLINE, NodeStatus.TRAINING]
            ]
        
        if len(online_nodes) < self.min_nodes_per_round:
            return {
                "success": False,
                "error": "Insufficient nodes",
                "round": self.current_round,
            }
        
        updates = self.model_updates.get(self.current_round, [])
        
        if not updates:
            return {
                "success": False,
                "error": "No updates received",
                "round": self.current_round,
            }
        
        if self.config.get("secure_aggregation", False):
            encrypted = [
                self.secure_aggregator.encrypt_update(u, u.node_id)
                for u in updates
            ]
            secure_result = self.secure_aggregator.secure_aggregate(encrypted)
        
        aggregated_params = self.aggregator.aggregate(updates, self.global_model)
        
        with self._lock:
            self.global_model = aggregated_params
        
        if self.config.get("differential_privacy", False):
            epsilon_used = self.config.get("epsilon_per_round", 0.1)
            self.privacy_tracker.accumulate(epsilon_used)
        
        participation_rate = len(updates) / len(online_nodes)
        self.stats["avg_participation"] = (
            self.stats["avg_participation"] * (self.stats["total_rounds"] - 1) + participation_rate
        ) / self.stats["total_rounds"]
        
        return {
            "success": True,
            "round": self.current_round,
            "num_updates": len(updates),
            "participation_rate": participation_rate,
            "privacy_spent": self.privacy_tracker.epsilon_spent,
        }
    
    async def run_training(self, num_rounds: int = None) -> Dict[str, Any]:
        rounds = num_rounds or self.max_rounds
        results = []
        
        for _ in range(rounds):
            result = await self.run_round()
            results.append(result)
            
            if self.privacy_tracker.is_budget_exceeded():
                break
        
        return {
            "total_rounds": len(results),
            "successful_rounds": sum(1 for r in results if r.get("success")),
            "final_privacy_spent": self.privacy_tracker.epsilon_spent,
            "results": results,
        }
    
    def get_global_model(self) -> Dict[str, List[float]]:
        return self.global_model.copy()
    
    def get_node_stats(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if node_id in self.nodes:
                return self.nodes[node_id].to_dict()
            return None
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [n.to_dict() for n in self.nodes.values()]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "federated_learner": self.stats,
            "current_round": self.current_round,
            "total_nodes": len(self.nodes),
            "online_nodes": sum(
                1 for n in self.nodes.values()
                if n.status == NodeStatus.ONLINE
            ),
            "privacy_tracker": self.privacy_tracker.get_composition_info(),
            "dp_module": self.dp_module.get_stats(),
        }
