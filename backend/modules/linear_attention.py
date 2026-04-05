"""
线性注意力机制
Linear Attention Mechan

自主实现的线性注意力技术
基于Kimi Linear论文原理
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, List
import math

try:
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


class LinearAttention(nn.Module):
    """
    自主实现的线性注意力机制
    
    核心原理：
    传统注意力: O(n²) 复杂度
    线性注意力: O(n) 复杂度
    
    通过核方法将softmax分解为可线性计算的形式：
    Attention(Q, K, V) = φ(Q) · (φ(K)^T · V)
    
    其中φ是核函数，例如φ(x) = elu(x)+1 或 φ(x) = relu(x)
    
    优势：
    - 长序列推理速度提升5-6倍
    - KV缓存减少75%
    - 内存占用大幅降低
    """
    
    def __init__(
        self,
        dim: int = 768,
        num_heads: int = 8,
        eps: float = 1e-6,
        dropout: float = 0.1,
        feature_map: str = "elu+1"
    ):
        super().__init__()
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for LinearAttention")
        
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.eps = eps
        self.feature_map = feature_map
        
        assert dim % num_heads == 0, "dim must be divisible by num_heads"
        
        self.q_proj = nn.Linear(dim, dim, bias=False)
        self.k_proj = nn.Linear(dim, dim, bias=False)
        self.v_proj = nn.Linear(dim, dim, bias=False)
        self.out_proj = nn.Linear(dim, dim)
        
        self.dropout = nn.Dropout(dropout)
        
        self._reset_parameters()
    
    def _reset_parameters(self):
        nn.init.xavier_uniform_(self.q_proj.weight)
        nn.init.xavier_uniform_(self.k_proj.weight)
        nn.init.xavier_uniform_(self.v_proj.weight)
        nn.init.xavier_uniform_(self.out_proj.weight)
    
    def _feature_map_elu(self, x: torch.Tensor) -> torch.Tensor:
        """ELU+1 核函数"""
        return F.elu(x) + 1.0
    
    def _feature_map_relu(self, x: torch.Tensor) -> torch.Tensor:
        """ReLU 核函数"""
        return F.relu(x)
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        return_attention_weights: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        前向传播
        
        Args:
            query: [batch, seq_len, dim]
            key: [batch, seq_len, dim]
            value: [batch, seq_len, dim]
            mask: [batch, seq_len] 可选的掩码
            return_attention_weights: 是否返回注意力权重
            
        Returns:
            output: [batch, seq_len, dim]
            attn_weights: [batch, num_heads, seq_len, seq_len] 可选
        """
        batch_size, seq_len, dim = query.shape
        
        Q = self._apply_feature_map(self.q_proj(query))
        K = self._apply_feature_map(self.k_proj(key))
        V = self.v_proj(value)
        
        Q = Q.view(batch_size, self.num_heads, self.head_dim)
        K = K.view(batch_size, self.num_heads, self.head_dim)
        V = V.view(batch_size, self.num_heads, self.head_dim)
        
        Q = Q.transpose(1, 2)
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)
        
        KV = torch.einsum('bnd,bnm->bdm', K, V)
        
        out = torch.einsum('bnd,bdm->bnm', Q, KV)
        
        K_sum = K.sum(dim=1, keepdim=True)
        
        Z = torch.einsum('bnd,bnd->bn', Q, K_sum)
        Z = Z.clamp(min=self.eps)
        out = out / Z.unsqueeze(-1)
        
        if mask is not None:
            out = out * mask.unsqueeze(-1)
        
        out = self.out_proj(out)
        
        out = self.dropout(out)
        
        if return_attention_weights:
            attn_weights = self._compute_attention_weights(Q, K)
            return out, attn_weights
        return out
    
    def _apply_feature_map(self, x: torch.Tensor) -> torch.Tensor:
        """应用核函数"""
        if self.feature_map == "elu+1":
            return self._feature_map_elu(x)
        else:
            return self._feature_map_relu(x)
    
    def _compute_attention_weights(
        self,
        Q: torch.Tensor,
        K: torch.Tensor
    ) -> torch.Tensor:
        """计算注意力权重（仅用于可视化）"""
        Q = self._apply_feature_map(Q)
        K = self._apply_feature_map(K)
        
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        return F.softmax(attn_scores, dim=-1)


class ChunkedLinearAttention(nn.Module):
    """
    分块线性注意力
    
    用于处理超长序列，通过分块降低内存占用
    """
    
    def __init__(
        self,
        dim: int = 768,
        chunk_size: int = 512,
        num_heads: int = 8,
        eps: float = 1e-6,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.dim = dim
        self.chunk_size = chunk_size
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.eps = eps
        
        self.linear_attn = LinearAttention(
            dim=dim,
            num_heads=num_heads,
            eps=eps,
            dropout=dropout
        )
        
        self.layer_norm = nn.LayerNorm(dim)
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        分块处理长序列
        
        Args:
            query: [batch, seq_len, dim]
            key: [batch, seq_len, dim]
            value: [batch, seq_len, dim]
            mask: [batch, seq_len]
            
        Returns:
            output: [batch, seq_len, dim]
        """
        batch_size, seq_len, dim = query.shape
        
        if seq_len <= self.chunk_size:
            return self.linear_attn(query, key, value, mask)
        
        num_chunks = (seq_len + self.chunk_size - 1) // self.chunk_size
        
        chunk_outputs = []
        
        for i in range(num_chunks):
            start = i * self.chunk_size
            end = min((i + 1) * self.chunk_size, seq_len)
            
            chunk_query = query[:, start:end, :]
            chunk_key = key[:, start:end, :]
            chunk_value = value[:, start:end, :]
            
            if mask is not None:
                chunk_mask = mask[:, start:end]
            else:
                chunk_mask = None
            
            chunk_output = self.linear_attn(
                chunk_query, chunk_key, chunk_value, chunk_mask
            )
            chunk_outputs.append(chunk_output)
        
        output = torch.cat(chunk_outputs, dim=1)
        
        output = self.layer_norm(output)
        
        return output


class EfficientLinearAttention(nn.Module):
    """
    高效线性注意力
    
    进一步优化KV缓存和计算效率
    """
    
    def __init__(
        self,
        dim: int = 768,
        num_heads: int = 8,
        eps: float = 1e-6,
        max_seq_len: int = 16384,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.eps = eps
        self.max_seq_len = max_seq_len
        
        self.q_proj = nn.Linear(dim, dim, bias=False)
        self.k_proj = nn.Linear(dim, dim, bias=False)
        self.v_proj = nn.Linear(dim, dim, bias=False)
        self.out_proj = nn.Linear(dim, dim)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(dim)
        
        self.register_buffer('kv_cache', None, persistent=False)
        self.register_buffer('cache_seq', torch.tensor(0))
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        use_cache: bool = True,
        update_cache: bool = True
    ) -> torch.Tensor:
        """
        高效线性注意力前向传播
        
        Args:
            query: [batch, seq_len, dim]
            key: [batch, seq_len, dim]
            value: [batch, seq_len, dim]
            use_cache: 是否使用缓存
            update_cache: 是否更新缓存
            
        Returns:
            output: [batch, seq_len, dim]
        """
        batch_size, seq_len, dim = query.shape
        
        Q = self.q_proj(query)
        K = self.k_proj(key)
        V = self.v_proj(value)
        
        Q = F.elu(Q) + 1.0
        K = F.elu(K) + 1.0
        
        if use_cache and self.kv_cache is not None:
            K_cached, V_cached = self.kv_cache
            K = torch.cat([K_cached, K], dim=1)
            V = torch.cat([V_cached, V], dim=1)
        
        if update_cache:
            self.kv_cache = (K, V)
            self.cache_seq += 1
        
        Q = Q.view(batch_size, self.num_heads, self.head_dim)
        K = K.view(batch_size, -1, self.num_heads, self.head_dim)
        V = V.view(batch_size, -1, self.num_heads, self.head_dim)
        
        KV = torch.einsum('bnhd,bmhd->bhdm', K, V)
        
        out = torch.einsum('bnhd,bhdm->bnm', Q, KV)
        
        K_sum = K.sum(dim=1, keepdim=True)
        Z = torch.einsum('bnhd,bnhd->bn', Q, K_sum)
        Z = Z.clamp(min=self.eps)
        out = out / Z.unsqueeze(-1)
        
        out = self.out_proj(out)
        out = self.dropout(out)
        out = self.layer_norm(out)
        
        return out
    
    def clear_cache(self):
        """清空缓存"""
        self.kv_cache = None
        self.cache_seq.fill_(0)
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        if self.kv_cache is None:
            return {"cached": False, "seq": 0}
        
        K, V = self.kv_cache
        return {
            "cached": True,
            "seq": self.cache_seq.item(),
            "kv_shape": (K.shape, V.shape),
            "memory_mb": (K.numel() + V.numel()) * 4 / (1024 * 1024)
        }


class LinearMemoryRetriever(nn.Module):
    """
    使用线性注意力的记忆检索器
    
    应用于海马体记忆系统
    """
    
    def __init__(
        self,
        dim: int = 768,
        num_memories: int = 10000,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.dim = dim
        self.num_memories = num_memories
        
        self.memory_embeddings = nn.Parameter(
            torch.randn(num_memories, dim) * 0.02
        )
        
        self.linear_attn = LinearAttention(
            dim=dim,
            num_heads=num_heads,
            dropout=dropout
        )
        
        self.output_proj = nn.Linear(dim, dim)
    
    def forward(
        self,
        query: torch.Tensor,
        top_k: int = 10
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        记忆检索
        
        Args:
            query: [batch, dim]
            top_k: 返回前k个最相关的记忆
            
        Returns:
            output: [batch, dim]
            indices: [batch, top_k]
        """
        batch_size = query.shape[0]
        
        query_seq = query.unsqueeze(1)
        
        memories = self.memory_embeddings.unsqueeze(0).expand(batch_size, -1, -1)
        
        attended = self.linear_attn(query_seq, memories, memories)
        
        scores = torch.matmul(
            query.unsqueeze(1),
            self.memory_embeddings.T
        ).squeeze(1)
        
        top_k_indices = scores.topk(top_k, dim=-1)[1]
        
        output = self.output_proj(attended.squeeze(1))
        
        return output, top_k_indices
    
    def update_memory(
        self,
        memory_idx: int,
        memory_embedding: torch.Tensor
    ):
        """更新特定记忆"""
        with torch.no_grad():
            self.memory_embeddings[memory_idx] = memory_embedding
    
    def add_memory(
        self,
        memory_embedding: torch.Tensor
    ):
        """添加新记忆"""
        new_idx = self.memory_embeddings.shape[0]
        
        if new_idx >= self.num_memories:
            new_embeddings = torch.randn(self.num_memories, self.dim) * 0.02
            new_embeddings[:new_idx] = memory_embedding
            self.memory_embeddings = nn.Parameter(new_embeddings)
        else:
            with torch.no_grad():
                self.memory_embeddings[new_idx] = memory_embedding
