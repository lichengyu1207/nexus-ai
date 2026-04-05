"""
联邦学习模块
Federated Learning Module for Security

实现多节点协同学习，共享防御经验
"""

import json
import time
import uuid
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import httpx

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None


@dataclass
class ModelUpdate:
    """模型更新"""
    update_id: str
    node_id: str
    timestamp: float
    gradients: Dict[str, List[float]]
    sample_count: int
    loss: float
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "update_id": self.update_id,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "gradients": self.gradients,
            "sample_count": self.sample_count,
            "loss": self.loss,
            "metrics": self.metrics
        }


@dataclass
class FederatedConfig:
    """联邦学习配置"""
    min_nodes: int = 3
    max_nodes: int = 100
    aggregation_interval: int = 300
    min_samples_per_node: int = 100
    learning_rate: float = 0.01
    momentum: float = 0.9


class ParameterServer:
    """参数服务器"""
    
    def __init__(
        self,
        server_id: str = "param_server_001",
        config: FederatedConfig = None
    ):
        self.server_id = server_id
        self.config = config or FederatedConfig()
        
        self._global_model: Optional[nn.Module] = None
        self._model_version: int = 0
        self._pending_updates: List[ModelUpdate] = []
        self._node_registry: Dict[str, Dict] = {}
        
        self._running = False
        self._aggregation_task: Optional[asyncio.Task] = None
    
    def initialize_model(self, state_dim: int = 20, action_dim: int = 6):
        """初始化全局模型"""
        from .judge_agent import DQNetwork
        
        self._global_model = DQNetwork(state_dim, action_dim)
        self._model_version = 1
    
    async def register_node(self, node_id: str, node_info: Dict) -> bool:
        """注册节点"""
        self._node_registry[node_id] = {
            "node_id": node_id,
            "registered_at": time.time(),
            "last_update": time.time(),
            "total_samples": 0,
            "status": "active",
            **node_info
        }
        
        return True
    
    async def receive_update(self, update: ModelUpdate) -> bool:
        """接收节点更新"""
        if update.node_id not in self._node_registry:
            return False
        
        self._pending_updates.append(update)
        
        self._node_registry[update.node_id]["last_update"] = time.time()
        self._node_registry[update.node_id]["total_samples"] += update.sample_count
        
        return True
    
    async def aggregate_updates(self) -> Dict:
        """聚合更新 (FedAvg)"""
        if not self._pending_updates:
            return {"status": "no_updates"}
        
        if len(self._pending_updates) < self.config.min_nodes:
            return {"status": "insufficient_nodes"}
        
        total_samples = sum(u.sample_count for u in self._pending_updates)
        
        if total_samples < self.config.min_samples_per_node * len(self._pending_updates):
            return {"status": "insufficient_samples"}
        
        aggregated_gradients = {}
        
        first_update = self._pending_updates[0]
        for layer_name, grads in first_update.gradients.items():
            weighted_sum = np.array(grads) * first_update.sample_count
            
            for update in self._pending_updates[1:]:
                if layer_name in update.gradients:
                    weighted_sum += np.array(update.gradients[layer_name]) * update.sample_count
            
            aggregated_gradients[layer_name] = (weighted_sum / total_samples).tolist()
        
        await self._apply_gradients(aggregated_gradients)
        
        self._model_version += 1
        
        result = {
            "status": "success",
            "model_version": self._model_version,
            "aggregated_samples": total_samples,
            "participating_nodes": len(self._pending_updates),
            "timestamp": time.time()
        }
        
        self._pending_updates = []
        
        await self._save_aggregation_result(result)
        
        return result
    
    async def _apply_gradients(self, gradients: Dict[str, List[float]]):
        """应用梯度到全局模型"""
        if self._global_model is None:
            return
        
        with torch.no_grad():
            for name, param in self._global_model.named_parameters():
                if name in gradients:
                    grad_tensor = torch.tensor(gradients[name])
                    param.data -= self.config.learning_rate * grad_tensor
    
    async def _save_aggregation_result(self, result: Dict):
        """保存聚合结果"""
        try:
            from ...database import get_db_connection
            
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        INSERT INTO federated_aggregations 
                        (id, model_version, aggregated_samples, participating_nodes, result, created_at)
                        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                    """, (
                        str(uuid.uuid4()),
                        result["model_version"],
                        result["aggregated_samples"],
                        result["participating_nodes"],
                        json.dumps(result)
                    ))
                    await conn.commit()
                finally:
                    await conn.close()
        except Exception as e:
            print(f"保存聚合结果失败: {e}")
    
    async def get_global_model(self) -> Dict:
        """获取全局模型"""
        if self._global_model is None:
            return {"status": "no_model"}
        
        state_dict = {}
        for name, param in self._global_model.named_parameters():
            state_dict[name] = param.data.tolist()
        
        return {
            "status": "success",
            "model_version": self._model_version,
            "model_state": state_dict,
            "timestamp": time.time()
        }
    
    async def run_aggregation_loop(self):
        """聚合循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.aggregation_interval)
                result = await self.aggregate_updates()
                if result["status"] == "success":
                    print(f"联邦聚合完成: 版本 {result['model_version']}")
            except Exception as e:
                print(f"聚合循环错误: {e}")
                await asyncio.sleep(10)
    
    def start(self):
        """启动"""
        self._running = True
        if self._global_model is None:
            self.initialize_model()
        self._aggregation_task = asyncio.create_task(self.run_aggregation_loop())
    
    def stop(self):
        """停止"""
        self._running = False
        if self._aggregation_task:
            self._aggregation_task.cancel()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "server_id": self.server_id,
            "running": self._running,
            "model_version": self._model_version,
            "registered_nodes": len(self._node_registry),
            "pending_updates": len(self._pending_updates)
        }


class FederatedClient:
    """联邦学习客户端"""
    
    def __init__(
        self,
        node_id: str,
        server_url: str = "http://localhost:8000/api/federated",
        config: FederatedConfig = None
    ):
        self.node_id = node_id
        self.server_url = server_url
        self.config = config or FederatedConfig()
        
        self._local_model: Optional[nn.Module] = None
        self._sample_count: int = 0
        self._last_sync_version: int = 0
        
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
    
    def set_local_model(self, model: nn.Module):
        """设置本地模型"""
        self._local_model = model
    
    async def register(self) -> bool:
        """注册到服务器"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/register",
                    json={
                        "node_id": self.node_id,
                        "node_info": {
                            "platform": "python",
                            "version": "1.0.0"
                        }
                    }
                )
                return response.status_code == 200
        except Exception as e:
            print(f"注册失败: {e}")
            return False
    
    async def compute_gradients(self) -> Dict[str, List[float]]:
        """计算本地梯度"""
        if self._local_model is None:
            return {}
        
        gradients = {}
        for name, param in self._local_model.named_parameters():
            if param.grad is not None:
                gradients[name] = param.grad.data.tolist()
        
        return gradients
    
    async def send_update(self, loss: float, metrics: Dict = None) -> bool:
        """发送更新到服务器"""
        gradients = await self.compute_gradients()
        
        if not gradients:
            return False
        
        update = ModelUpdate(
            update_id=str(uuid.uuid4()),
            node_id=self.node_id,
            timestamp=time.time(),
            gradients=gradients,
            sample_count=self._sample_count,
            loss=loss,
            metrics=metrics or {}
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/update",
                    json=update.to_dict()
                )
                
                if response.status_code == 200:
                    self._sample_count = 0
                    return True
                return False
        except Exception as e:
            print(f"发送更新失败: {e}")
            return False
    
    async def sync_model(self) -> bool:
        """同步全局模型"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_url}/model")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        model_state = data.get("model_state", {})
                        version = data.get("model_version", 0)
                        
                        if version > self._last_sync_version and self._local_model:
                            with torch.no_grad():
                                for name, param in self._local_model.named_parameters():
                                    if name in model_state:
                                        param.data = torch.tensor(model_state[name])
                            
                            self._last_sync_version = version
                            return True
                
                return False
        except Exception as e:
            print(f"同步模型失败: {e}")
            return False
    
    def add_samples(self, count: int):
        """添加样本计数"""
        self._sample_count += count
    
    async def run_sync_loop(self):
        """同步循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.aggregation_interval // 2)
                
                if self._sample_count >= self.config.min_samples_per_node:
                    await self.sync_model()
                
            except Exception as e:
                print(f"同步循环错误: {e}")
                await asyncio.sleep(10)
    
    def start(self):
        """启动"""
        self._running = True
        self._sync_task = asyncio.create_task(self.run_sync_loop())
    
    def stop(self):
        """停止"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "node_id": self.node_id,
            "running": self._running,
            "last_sync_version": self._last_sync_version,
            "sample_count": self._sample_count
        }


parameter_server = ParameterServer()
