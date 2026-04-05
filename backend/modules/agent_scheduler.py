"""
智能体调度器
Agent Scheduler

自主实现的智能体调度技术
基于Attention Residuals原理
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import math

try:
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


class AgentScheduler(nn.Module):
    """
    自主实现的智能体调度器
    
    核心原理：
    1. 各智能体有历史表现向量
    2. 根据任务特征动态选择智能体
    3. 注意力加权分配任务优先级
    
    应用场景：
    - 六部智能体调度（礼、户、兵、刑、吏、工）
    - 任务分配优化
    - 资源协调
    """
    
    DEFAULT_AGENTS = {
        "li_bu": {"name": "吏部", "capability": "管理", "priority": 0.8},
        "hu_bu": {"name": "户部", "capability": "积分", "priority": 0.7},
        "li_bu_consult": {"name": "礼部", "capability": "咨询", "priority": 0.9},
        "bing_bu": {"name": "兵部", "capability": "采集", "priority": 0.75},
        "xing_bu": {"name": "刑部", "capability": "风控", "priority": 0.85},
        "gong_bu": {"name": "工部", "capability": "分析", "priority": 0.9},
    }
    
    def __init__(
        self,
        num_agents: int = 6,
        agent_dim: int = 128,
        task_dim: int = 256,
        num_heads: int = 4,
        dropout: float = 0.1
    ):
        super().__init__()
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for AgentScheduler")
        
        self.num_agents = num_agents
        self.agent_dim = agent_dim
        self.task_dim = task_dim
        self.num_heads = num_heads
        self.head_dim = agent_dim // num_heads
        
        assert agent_dim % num_heads == 0, "agent_dim must be divisible by num_heads"
        
        self.agent_embeddings = nn.Parameter(
            torch.randn(num_agents, agent_dim) * 0.02
        )
        
        self.agent_names = ["li_bu", "hu_bu", "li_bu_consult", "bing_bu", "xing_bu", "gong_bu"]
        
        self._init_agent_embeddings()
        
        self.query_proj = nn.Linear(task_dim, agent_dim)
        self.key_proj = nn.Linear(agent_dim, agent_dim)
        self.value_proj = nn.Linear(agent_dim, agent_dim)
        
        self.task_encoder = nn.Sequential(
            nn.Linear(task_dim, task_dim),
            nn.ReLU(),
            nn.Linear(task_dim, task_dim)
        )
        
        self.history_attention = nn.MultiheadAttention(
            embed_dim=agent_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(agent_dim)
        
        self.register_buffer(
            'performance_history',
            torch.zeros(num_agents, 100, agent_dim)
        )
        self.register_buffer('history_ptr', torch.zeros(num_agents, dtype=torch.long))
    
    def _init_agent_embeddings(self):
        """初始化智能体嵌入"""
        for i, name in enumerate(self.agent_names):
            if name in self.DEFAULT_AGENTS:
                info = self.DEFAULT_AGENTS[name]
                priority = info.get("priority", 0.5)
                
                with torch.no_grad():
                    self.agent_embeddings.data[i] = (
                        self.agent_embeddings.data[i] * 0.7 +
                        torch.ones(self.agent_dim) * priority * 0.3
                    )
    
    def forward(
        self,
        task_embedding: torch.Tensor,
        agent_mask: Optional[torch.Tensor] = None,
        return_attention_weights: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        前向传播
        
        Args:
            task_embedding: [batch, task_dim] 任务特征
            agent_mask: [num_agents] 可选的智能体掩码
            return_attention_weights: 是否返回注意力权重
            
        Returns:
            weights: [batch, num_agents] 调度权重
            attn_weights: [batch, num_heads, num_agents] 可选的注意力权重
        """
        batch_size = task_embedding.shape[0]
        
        task_encoded = self.task_encoder(task_embedding)
        
        q = self.query_proj(task_encoded)
        
        agents = self.agent_embeddings.unsqueeze(0).expand(batch_size, -1, -1)
        k = self.key_proj(agents)
        v = self.value_proj(agents)
        
        q = q.view(batch_size, self.num_heads, self.head_dim)
        k = k.view(batch_size, self.num_agents, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, self.num_agents, self.num_heads, self.head_dim).transpose(1, 2)
        
        attn_scores = torch.matmul(q.unsqueeze(2), k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        if agent_mask is not None:
            attn_scores = attn_scores.masked_fill(
                agent_mask.unsqueeze(0).unsqueeze(1).unsqueeze(2) == 0,
                float('-inf')
            )
        
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        attended = torch.matmul(attn_weights, v)
        attended = attended.squeeze(2).view(batch_size, self.agent_dim)
        
        weights = F.softmax(
            torch.matmul(q, attended.unsqueeze(-1)).squeeze(-1).mean(dim=1),
            dim=-1
        )
        
        if return_attention_weights:
            return weights, attn_weights
        return weights, None
    
    def schedule(
        self,
        task_embedding: torch.Tensor,
        top_k: int = 3,
        agent_mask: Optional[torch.Tensor] = None
    ) -> List[Tuple[str, float]]:
        """
        调度任务到智能体
        
        Args:
            task_embedding: [batch, task_dim]
            top_k: 返回前k个智能体
            agent_mask: 可选的智能体掩码
            
        Returns:
            assignments: [(agent_name, weight), ...]
        """
        weights, _ = self.forward(task_embedding, agent_mask)
        
        weights_1d = weights.squeeze(0)
        
        top_k = min(top_k, self.num_agents)
        top_weights, top_indices = torch.topk(weights_1d, top_k)
        
        assignments = [
            (self.agent_names[idx], weight.item())
            for idx, weight in zip(top_indices, top_weights)
        ]
        
        return assignments
    
    def update_performance(
        self,
        agent_idx: int,
        performance_vector: torch.Tensor
    ):
        """
        更新智能体性能历史
        
        Args:
            agent_idx: 智能体索引
            performance_vector: [agent_dim] 性能向量
        """
        ptr = self.history_ptr[agent_idx].item()
        
        self.performance_history[agent_idx, ptr] = performance_vector
        
        self.history_ptr[agent_idx] = (ptr + 1) % 100
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """
        获取各智能体状态
        
        Returns:
            status: {agent_name: {priority, recent_performance}}
        """
        status = {}
        
        for i, name in enumerate(self.agent_names):
            embedding = self.agent_embeddings[i]
            
            ptr = self.history_ptr[i].item()
            if ptr > 0:
                recent = self.performance_history[i, :ptr]
                avg_performance = recent.mean(dim=0)
            else:
                avg_performance = torch.zeros(self.agent_dim)
            
            status[name] = {
                "name": self.DEFAULT_AGENTS.get(name, {}).get("name", name),
                "capability": self.DEFAULT_AGENTS.get(name, {}).get("capability", "unknown"),
                "priority": float(embedding.mean()),
                "recent_performance": float(avg_performance.mean())
            }
        
        return status


class DynamicAgentScheduler(nn.Module):
    """
    动态智能体调度器
    
    支持智能体能力动态更新和负载均衡
    """
    
    def __init__(
        self,
        num_agents: int = 6,
        agent_dim: int = 128,
        task_dim: int = 256,
        max_concurrent_tasks: int = 10
    ):
        super().__init__()
        
        self.base_scheduler = AgentScheduler(
            num_agents=num_agents,
            agent_dim=agent_dim,
            task_dim=task_dim
        )
        
        self.max_concurrent_tasks = max_concurrent_tasks
        
        self.register_buffer(
            'current_load',
            torch.zeros(num_agents)
        )
        
        self.register_buffer(
            'task_queue',
            torch.zeros(max_concurrent_tasks, task_dim)
        )
        self.register_buffer('queue_ptr', torch.tensor(0))
        
        self.load_balancer = nn.Linear(agent_dim + 1, agent_dim)
    
    def forward(
        self,
        task_embedding: torch.Tensor
    ) -> Tuple[torch.Tensor, List[Tuple[str, float]]]:
        """
        动态调度
        
        Args:
            task_embedding: [batch, task_dim]
            
        Returns:
            weights: [batch, num_agents]
            assignments: [(agent_name, weight), ...]
        """
        base_weights, _ = self.base_scheduler(task_embedding)
        
        load_adjusted = self._adjust_for_load(base_weights)
        
        assignments = self.base_scheduler.schedule(
            task_embedding,
            top_k=3,
            agent_mask=None
        )
        
        return load_adjusted, assignments
    
    def _adjust_for_load(
        self,
        weights: torch.Tensor
    ) -> torch.Tensor:
        """
        根据负载调整权重
        
        Args:
            weights: [batch, num_agents]
            
        Returns:
            adjusted: [batch, num_agents]
        """
        load_factor = 1.0 - (self.current_load / self.max_concurrent_tasks)
        load_factor = torch.clamp(load_factor, min=0.1)
        
        adjusted = weights * load_factor.unsqueeze(0)
        adjusted = F.softmax(adjusted, dim=-1)
        
        return adjusted
    
    def assign_task(
        self,
        task_embedding: torch.Tensor,
        agent_name: str
    ):
        """
        分配任务
        
        Args:
            task_embedding: [task_dim]
            agent_name: 智能体名称
        """
        agent_idx = self.base_scheduler.agent_names.index(agent_name)
        
        self.current_load[agent_idx] += 1
        
        ptr = self.queue_ptr.item()
        self.task_queue[ptr] = task_embedding
        self.queue_ptr.copy_((ptr + 1) % self.max_concurrent_tasks)
    
    def complete_task(
        self,
        agent_name: str,
        performance_score: float
    ):
        """
        完成任务
        
        Args:
            agent_name: 智能体名称
            performance_score: 性能分数
        """
        agent_idx = self.base_scheduler.agent_names.index(agent_name)
        
        self.current_load[agent_idx] = max(0, self.current_load[agent_idx] - 1)
        
        performance_vector = torch.zeros(self.base_scheduler.agent_dim)
        performance_vector[0] = performance_score
        
        self.base_scheduler.update_performance(agent_idx, performance_vector)
    
    def get_load_status(self) -> Dict[str, int]:
        """
        获取负载状态
        
        Returns:
            load_status: {agent_name: current_load}
        """
        return {
            name: int(self.current_load[i])
            for i, name in enumerate(self.base_scheduler.agent_names)
        }


class CollaborativeScheduler(nn.Module):
    """
    协作调度器
    
    支持多智能体协作任务分配
    """
    
    def __init__(
        self,
        num_agents: int = 6,
        agent_dim: int = 128,
        task_dim: int = 256,
        collaboration_patterns: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__()
        
        self.base_scheduler = AgentScheduler(
            num_agents=num_agents,
            agent_dim=agent_dim,
            task_dim=task_dim
        )
        
        self.collaboration_patterns = collaboration_patterns or {
            "valuation_analysis": ["zhongshu", "bing_bu", "gong_bu"],
            "market_report": ["zhongshu", "bing_bu", "gong_bu", "li_bu_consult"],
            "risk_assessment": ["zhongshu", "xing_bu", "gong_bu"],
            "investment_consultation": ["zhongshu", "gong_bu", "li_bu_consult"],
        }
        
        self.pattern_classifier = nn.Sequential(
            nn.Linear(task_dim, 256),
            nn.ReLU(),
            nn.Linear(256, len(self.collaboration_patterns))
        )
        
        self.pattern_names = list(self.collaboration_patterns.keys())
    
    def forward(
        self,
        task_embedding: torch.Tensor
    ) -> Tuple[str, List[str], torch.Tensor]:
        """
        协作调度
        
        Args:
            task_embedding: [batch, task_dim]
            
        Returns:
            pattern_name: 协作模式名称
            agents: 参与的智能体列表
            weights: 各智能体权重
        """
        pattern_logits = self.pattern_classifier(task_embedding)
        pattern_idx = pattern_logits.argmax(dim=-1).item()
        pattern_name = self.pattern_names[pattern_idx]
        
        agents = self.collaboration_patterns[pattern_name]
        
        agent_mask = torch.zeros(self.base_scheduler.num_agents)
        for agent in agents:
            if agent in self.base_scheduler.agent_names:
                idx = self.base_scheduler.agent_names.index(agent)
                agent_mask[idx] = 1
        
        weights, _ = self.base_scheduler(task_embedding, agent_mask)
        
        return pattern_name, agents, weights
    
    def get_collaboration_plan(
        self,
        task_embedding: torch.Tensor
    ) -> Dict[str, Dict]:
        """
        获取协作计划
        
        Returns:
            plan: {agent_name: {role, priority, expected_contribution}}
        """
        pattern_name, agents, weights = self.forward(task_embedding)
        
        plan = {}
        for i, agent in enumerate(agents):
            if agent in self.base_scheduler.agent_names:
                idx = self.base_scheduler.agent_names.index(agent)
                weight = weights[0, idx].item()
                
                plan[agent] = {
                    "role": self.base_scheduler.DEFAULT_AGENTS.get(agent, {}).get("capability", "unknown"),
                    "priority": weight,
                    "expected_contribution": weight * 100
                }
        
        return plan
