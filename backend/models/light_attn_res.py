"""
轻量级Attention Residuals实现
基于Kimi论文思想，自主实现适合房都督平台的版本

核心思想：将传统残差连接的固定加法累加方式替换为基于Softmax注意力的动态聚合。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LightAttnRes(nn.Module):
    """
    轻量级Attention Residual
    
    核心公式: output = current + Attention(current, history)
    """
    
    def __init__(self, dim: int, dropout: float = 0.1):
        super().__init__()
        self.dim = dim
        
        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        self.out_proj = nn.Linear(dim, dim)
        
        self.norm = nn.LayerNorm(dim)
        self.dropout = nn.Dropout(dropout)
        
        self._init_weights()
        
    def _init_weights(self):
        for proj in [self.q_proj, self.k_proj, self.v_proj, self.out_proj]:
            nn.init.xavier_uniform_(proj.weight)
            nn.init.zeros_(proj.bias)
            
    def forward(self, current: torch.Tensor, history: List[torch.Tensor]) -> torch.Tensor:
        if not history:
            return current
            
        query = self.q_proj(current)
        
        history_stack = torch.stack(history, dim=0)
        keys = self.k_proj(history_stack)
        values = self.v_proj(history_stack)
        
        if query.dim() == 2:
            query = query.unsqueeze(0)
            
        scores = torch.matmul(query, keys.transpose(-2, -1)) / math.sqrt(self.dim)
        weights = F.softmax(scores, dim=-1)
        
        aggregated = torch.matmul(weights, values)
        if aggregated.dim() == 3 and query.dim() == 2:
            aggregated = aggregated.squeeze(0)
            
        output = self.out_proj(aggregated)
        output = self.dropout(output)
        
        return self.norm(current + output)


class MemoryAttnRes(nn.Module):
    """
    记忆系统专用Attention Residual
    
    用于海马体记忆检索，动态选择最相关的记忆片段
    """
    
    def __init__(self, dim: int = 512, max_mem: int = 1000, dropout: float = 0.1):
        super().__init__()
        self.dim = dim
        self.max_mem = max_mem
        
        self.memory_q = nn.Linear(dim, dim)
        self.memory_k = nn.Linear(dim, dim)
        self.memory_v = nn.Linear(dim, dim)
        
        self.gate = nn.Sequential(
            nn.Linear(dim * 2, dim),
            nn.Sigmoid()
        )
        
        self.norm = nn.LayerNorm(dim)
        self.dropout = nn.Dropout(dropout)
        
        self.register_buffer('memory_bank', torch.zeros(max_mem, dim))
        self.register_buffer('mem_ptr', torch.tensor(0))
        
    def store(self, memory: torch.Tensor):
        ptr = self.mem_ptr.item()
        batch = memory.shape[0]
        
        for i, m in enumerate(memory):
            idx = (ptr + i) % self.max_mem
            self.memory_bank[idx] = m.detach()
            
        self.mem_ptr.fill_((ptr + batch) % self.max_mem)
        
    def retrieve(self, query: torch.Tensor, top_k: int = 10) -> Tuple[torch.Tensor, torch.Tensor]:
        q = self.memory_q(query)
        k = self.memory_k(self.memory_bank)
        v = self.memory_v(self.memory_bank)
        
        scores = torch.matmul(q, k.T) / math.sqrt(self.dim)
        weights = F.softmax(scores, dim=-1)
        
        top_weights, top_idx = torch.topk(weights, min(top_k, self.max_mem), dim=-1)
        
        retrieved = v[top_idx]
        return retrieved, top_weights
        
    def forward(self, current: torch.Tensor, short_mem: Optional[torch.Tensor] = None) -> torch.Tensor:
        retrieved, weights = self.retrieve(current)
        context = torch.sum(retrieved * weights.unsqueeze(-1), dim=0)
        
        if short_mem is not None:
            gate = self.gate(torch.cat([current, short_mem], dim=-1))
            current = current + gate * short_mem
            
        output = self.dropout(context)
        return self.norm(current + output)


class PersonalityAttnRes(nn.Module):
    """
    人格化引擎专用Attention Residual
    
    实现多层人格特征按需融合
    """
    
    def __init__(self, dim: int = 256, num_personalities: int = 4, dropout: float = 0.1):
        super().__init__()
        self.dim = dim
        
        self.personality_emb = nn.Embedding(num_personalities, dim)
        
        self.pers_q = nn.Linear(dim, dim)
        self.pers_k = nn.Linear(dim, dim)
        self.pers_v = nn.Linear(dim, dim)
        
        self.fusion_gate = nn.Sequential(
            nn.Linear(dim * 2, dim),
            nn.Sigmoid()
        )
        
        self.norm = nn.LayerNorm(dim)
        self.dropout = nn.Dropout(dropout)
        
        self.history = {i: [] for i in range(num_personalities)}
        
    def forward(self, hidden: torch.Tensor, personality_id: int, 
                history: Optional[List[torch.Tensor]] = None) -> torch.Tensor:
        pers_emb = self.personality_emb(torch.tensor([personality_id], device=hidden.device))
        pers_emb = pers_emb.expand(hidden.shape[0], -1)
        
        q = self.pers_q(hidden)
        k = self.pers_k(pers_emb)
        v = self.pers_v(pers_emb)
        
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.dim)
        weights = F.softmax(scores, dim=-1)
        context = torch.matmul(weights, v)
        
        if history:
            hist_stack = torch.stack(history, dim=0)
            hist_k = self.pers_k(hist_stack)
            hist_v = self.pers_v(hist_stack)
            
            hist_scores = torch.matmul(q.unsqueeze(1), hist_k.transpose(-2, -1)) / math.sqrt(self.dim)
            hist_weights = F.softmax(hist_scores, dim=-1)
            hist_context = torch.matmul(hist_weights, hist_v).squeeze(1)
            
            context = context + hist_context * 0.5
            
        gate = self.fusion_gate(torch.cat([hidden, context], dim=-1))
        output = hidden + gate * context
        output = self.dropout(output)
        
        return self.norm(output)


class AgentSwarmAttnRes(nn.Module):
    """
    智能体协同专用Attention Residual
    
    实现任务分配时动态聚合历史经验
    """
    
    def __init__(self, dim: int = 512, num_agents: int = 6, dropout: float = 0.1):
        super().__init__()
        self.dim = dim
        self.num_agents = num_agents
        
        self.agent_emb = nn.Embedding(num_agents, dim)
        
        self.task_q = nn.Linear(dim, dim)
        self.agent_k = nn.Linear(dim, dim)
        self.agent_v = nn.Linear(dim, dim)
        
        self.coord_attn = nn.MultiheadAttention(dim, num_heads=8, dropout=dropout, batch_first=True)
        
        self.exp_gate = nn.Sequential(
            nn.Linear(dim * 2, dim),
            nn.Sigmoid()
        )
        
        self.norm = nn.LayerNorm(dim)
        self.out_proj = nn.Linear(dim, dim)
        
    def forward(self, task_emb: torch.Tensor, agent_ids: List[int],
                exp_history: Optional[List[torch.Tensor]] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        agent_ids_t = torch.tensor(agent_ids, device=task_emb.device)
        agent_embs = self.agent_emb(agent_ids_t).unsqueeze(0).expand(task_emb.shape[0], -1, -1)
        
        q = self.task_q(task_emb).unsqueeze(1)
        k = self.agent_k(agent_embs)
        v = self.agent_v(agent_embs)
        
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.dim)
        weights = F.softmax(scores, dim=-1)
        agent_weights = weights.squeeze(1)
        
        coord_out, _ = self.coord_attn(q, agent_embs, agent_embs)
        coord_out = coord_out.squeeze(1)
        
        if exp_history:
            hist_stack = torch.stack(exp_history, dim=0)
            hist_mean = torch.mean(hist_stack, dim=0)
            
            gate = self.exp_gate(torch.cat([coord_out, hist_mean], dim=-1))
            coord_out = coord_out + gate * hist_mean
            
        output = self.out_proj(coord_out)
        output = self.norm(task_emb + output)
        
        return output, agent_weights


def retrieve_memories_attn_res(
    query_embedding: torch.Tensor,
    memories: list,
    memory_embeddings: torch.Tensor
) -> torch.Tensor:
    """
    海马体记忆检索 - AttnRes方式
    
    不再简单平均，而是根据当前查询动态决定从哪些记忆中取多少信息
    
    Args:
        query_embedding: [dim] 当前查询向量
        memories: 列表，每条记忆包含内容
        memory_embeddings: [num_memories, dim] 记忆向量矩阵
        
    Returns:
        final: [dim] 聚合后的表示
    """
    query = query_embedding.unsqueeze(0)
    
    keys = memory_embeddings
    values = keys
    
    attn_weights = torch.matmul(query, keys.T)
    attn_weights = F.softmax(attn_weights, dim=-1)
    
    aggregated = torch.matmul(attn_weights, values)
    
    final = aggregated + query
    
    return final.squeeze(0)


class PersonalityFusion(nn.Module):
    """
    人格化交互引擎 - AttnRes方式
    
    角色在不同对话上下文中会动态调整人格特征的权重
    比如用户谈论战争时，"兵部"相关的特征权重提高
    """
    
    def __init__(self, dim: int):
        super().__init__()
        self.query_proj = nn.Linear(dim, dim)
        self.key_proj = nn.Linear(dim, dim)
        self.value_proj = nn.Linear(dim, dim)
        
    def forward(self, current_state: torch.Tensor, trait_embeddings: torch.Tensor) -> torch.Tensor:
        """
        Args:
            current_state: 当前上下文向量
            trait_embeddings: [n_traits, dim] 各人格特征向量
            
        Returns:
            new_state: [dim] 融合后的状态
        """
        query = self.query_proj(current_state).unsqueeze(0)
        keys = self.key_proj(trait_embeddings)
        values = self.value_proj(trait_embeddings)
        
        attn_weights = F.softmax(query @ keys.T, dim=-1)
        aggregated = attn_weights @ values
        
        new_state = aggregated + query
        return new_state.squeeze(0)


def chunked_attn_res(
    query_embedding: torch.Tensor,
    memory_embeddings: torch.Tensor,
    chunk_size: int = 10
) -> torch.Tensor:
    """
    块敏感度优化 - 资源受限时必用
    
    将历史记忆分成块（比如按时间分组），块内用简单平均，块间用注意力聚合
    这样内存和计算量都大幅降低
    
    Args:
        query_embedding: [dim] 查询向量
        memory_embeddings: [n, dim] 记忆向量矩阵
        chunk_size: 块大小
        
    Returns:
        aggregated: [dim] 聚合后的表示
    """
    n = memory_embeddings.shape[0]
    num_chunks = (n + chunk_size - 1) // chunk_size
    
    chunk_vectors = []
    for i in range(num_chunks):
        chunk = memory_embeddings[i*chunk_size:(i+1)*chunk_size]
        chunk_vec = chunk.mean(dim=0)
        chunk_vectors.append(chunk_vec)
    
    chunk_tensor = torch.stack(chunk_vectors, dim=0)
    query = query_embedding.unsqueeze(0)
    attn_weights = F.softmax(query @ chunk_tensor.T, dim=-1)
    aggregated = attn_weights @ chunk_tensor
    
    return aggregated.squeeze(0)


def block_attn_res(
    blocks: list,
    partial_block: torch.Tensor,
    proj: nn.Linear,
    norm: nn.LayerNorm
) -> torch.Tensor:
    """
    块间注意力 - Kimi官方实现
    
    Inter-block attention: attend over block reps + partial sum.
    
    Args:
        blocks: N tensors of shape [B, T, D]: completed block representations
        partial_block: [B, T, D]: intra-block partial sum (b_n^i)
        proj: Linear projection
        norm: LayerNorm
        
    Returns:
        h: [B, T, D] aggregated output
    """
    V = torch.stack(blocks + [partial_block])
    K = norm(V)
    logits = torch.einsum('d, n b t d -> n b t', proj.weight.squeeze(), K)
    h = torch.einsum('n b t, n b t d -> b t d', logits.softmax(0), V)
    return h


def create_attn_res(use_case: str = "general", **kwargs) -> nn.Module:
    """
    工厂函数：创建Attention Residual模块
    
    Args:
        use_case: "general", "memory", "personality", "agent_swarm"
    """
    if use_case == "general":
        return LightAttnRes(**kwargs)
    elif use_case == "memory":
        return MemoryAttnRes(**kwargs)
    elif use_case == "personality":
        return PersonalityAttnRes(**kwargs)
    elif use_case == "agent_swarm":
        return AgentSwarmAttnRes(**kwargs)
    else:
        raise ValueError(f"Unknown use_case: {use_case}")


__all__ = [
    'LightAttnRes',
    'MemoryAttnRes',
    'PersonalityAttnRes',
    'AgentSwarmAttnRes',
    'PersonalityFusion',
    'create_attn_res',
    'retrieve_memories_attn_res',
    'chunked_attn_res',
    'block_attn_res',
]
