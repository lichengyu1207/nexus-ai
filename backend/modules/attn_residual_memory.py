"""
注意力残差记忆聚合器
Attention Residuals Memory Aggregator

自主实现的按需聚合历史信息技术
基于论文原理：h_{l+1} = h_l + ∑_{i=1..l} α_i · h_i
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


class MemoryAttentionAggregator(nn.Module):
    """
    自主实现的注意力聚合器，用于记忆检索
    
    核心原理：
    1. 将历史记忆分块，块内平均池化
    2. 使用注意力机制动态选择相关块
    3. 残差连接保留原始查询信息
    
    优势：
    - 避免信息稀释：深层信息不被等权累加
    - 节省计算量：块敏感度降低复杂度
    - 动态选择：根据当前需求选择历史信息
    """
    
    def __init__(
        self,
        embed_dim: int = 768,
        num_blocks: int = 8,
        num_heads: int = 8,
        dropout: float = 0.1,
        use_position_encoding: bool = True
    ):
        super().__init__()
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for MemoryAttentionAggregator")
        
        self.embed_dim = embed_dim
        self.num_blocks = num_blocks
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"
        
        self.query_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.key_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.value_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        
        self.use_position_encoding = use_position_encoding
        if use_position_encoding:
            self.pos_encoding = nn.Parameter(
                torch.randn(1, 1000, embed_dim) * 0.02
            )
        
        self.layer_norm = nn.LayerNorm(embed_dim)
        
        self.block_size = None
        self._reset_parameters()
    
    def _reset_parameters(self):
        nn.init.xavier_uniform_(self.query_proj.weight)
        nn.init.xavier_uniform_(self.key_proj.weight)
        nn.init.xavier_uniform_(self.value_proj.weight)
        nn.init.xavier_uniform_(self.out_proj.weight)
    
    def forward(
        self,
        query: torch.Tensor,
        memories: torch.Tensor,
        memory_mask: Optional[torch.Tensor] = None,
        return_attention_weights: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        前向传播
        
        Args:
            query: [batch, embed_dim] 当前查询向量
            memories: [batch, num_memories, embed_dim] 历史记忆向量
            memory_mask: [batch, num_memories] 可选的记忆掩码
            return_attention_weights: 是否返回注意力权重
            
        Returns:
            output: [batch, embed_dim] 聚合后的向量
            attn_weights: [batch, num_blocks] 可选的注意力权重
        """
        batch_size, num_memories, dim = memories.shape
        
        if num_memories == 0:
            if return_attention_weights:
                return query, None
            return query
        
        block_vectors, block_mask = self._create_blocks(memories, memory_mask)
        
        num_blocks = block_vectors.shape[1]
        
        q = self.query_proj(query)
        k = self.key_proj(block_vectors)
        v = self.value_proj(block_vectors)
        
        q = q.view(batch_size, self.num_heads, self.head_dim)
        k = k.view(batch_size, num_blocks, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, num_blocks, self.num_heads, self.head_dim).transpose(1, 2)
        
        attn_scores = torch.matmul(q.unsqueeze(2), k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        if block_mask is not None:
            attn_scores = attn_scores.masked_fill(
                block_mask.unsqueeze(1).unsqueeze(2) == 0,
                float('-inf')
            )
        
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        attended = torch.matmul(attn_weights, v)
        attended = attended.squeeze(2).view(batch_size, self.embed_dim)
        
        output = self.out_proj(attended)
        
        output = self.layer_norm(output + query)
        
        if return_attention_weights:
            return output, attn_weights.squeeze(1).squeeze(1)
        return output
    
    def _create_blocks(
        self,
        memories: torch.Tensor,
        memory_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        创建记忆块
        
        Args:
            memories: [batch, num_memories, embed_dim]
            memory_mask: [batch, num_memories]
            
        Returns:
            block_vectors: [batch, num_blocks, embed_dim]
            block_mask: [batch, num_blocks]
        """
        batch_size, num_memories, dim = memories.shape
        
        if self.block_size is None:
            self.block_size = max(1, num_memories // self.num_blocks)
        
        num_blocks = (num_memories + self.block_size - 1) // self.block_size
        
        block_vectors = []
        block_masks = []
        
        for i in range(num_blocks):
            start = i * self.block_size
            end = min((i + 1) * self.block_size, num_memories)
            
            block_memories = memories[:, start:end, :]
            
            if memory_mask is not None:
                block_mask = memory_mask[:, start:end]
                block_avg = (block_memories * block_mask.unsqueeze(-1)).sum(dim=1)
                block_avg = block_avg / (block_mask.sum(dim=1, keepdim=True) + 1e-9)
                block_masks.append(block_mask.sum(dim=1) > 0)
            else:
                block_avg = block_memories.mean(dim=1)
            
            block_vectors.append(block_avg)
        
        block_vectors = torch.stack(block_vectors, dim=1)
        
        if memory_mask is not None:
            block_mask = torch.stack(block_masks, dim=1).float()
            return block_vectors, block_mask
        
        return block_vectors, None
    
    def update_block_size(self, new_block_size: int):
        """动态更新块大小"""
        self.block_size = new_block_size
    
    def get_attention_pattern(
        self,
        query: torch.Tensor,
        memories: torch.Tensor
    ) -> torch.Tensor:
        """
        获取注意力模式用于可视化
        
        Returns:
            attention_pattern: [batch, num_blocks] 注意力权重
        """
        _, attn_weights = self.forward(
            query, memories, return_attention_weights=True
        )
        return attn_weights


class ChunkedAttentionAggregator(nn.Module):
    """
    分块注意力聚合器
    
    用于处理超长记忆序列，通过分块降低计算复杂度
    """
    
    def __init__(
        self,
        embed_dim: int = 768,
        chunk_size: int = 128,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.embed_dim = embed_dim
        self.chunk_size = chunk_size
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        self.query_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.key_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.value_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(embed_dim)
    
    def forward(
        self,
        query: torch.Tensor,
        memories: torch.Tensor
    ) -> torch.Tensor:
        """
        分块处理长记忆序列
        
        Args:
            query: [batch, embed_dim]
            memories: [batch, num_memories, embed_dim]
            
        Returns:
            output: [batch, embed_dim]
        """
        batch_size, num_memories, dim = memories.shape
        
        if num_memories <= self.chunk_size:
            return self._full_attention(query, memories)
        
        num_chunks = (num_memories + self.chunk_size - 1) // self.chunk_size
        
        chunk_outputs = []
        chunk_weights = []
        
        for i in range(num_chunks):
            start = i * self.chunk_size
            end = min((i + 1) * self.chunk_size, num_memories)
            
            chunk_memories = memories[:, start:end, :]
            
            chunk_output, chunk_weight = self._attend_to_chunk(
                query, chunk_memories
            )
            chunk_outputs.append(chunk_output)
            chunk_weights.append(chunk_weight)
        
        chunk_weights = torch.stack(chunk_weights, dim=1)
        chunk_weights = F.softmax(chunk_weights, dim=1)
        
        output = torch.zeros_like(query)
        for i, chunk_output in enumerate(chunk_outputs):
            output = output + chunk_weights[:, i:i+1] * chunk_output
        
        output = self.layer_norm(output + query)
        return output
    
    def _full_attention(
        self,
        query: torch.Tensor,
        memories: torch.Tensor
    ) -> torch.Tensor:
        """完整注意力计算"""
        q = self.query_proj(query).unsqueeze(1)
        k = self.key_proj(memories)
        v = self.value_proj(memories)
        
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        output = torch.matmul(attn_weights, v).squeeze(1)
        output = self.out_proj(output)
        
        return self.layer_norm(output + query)
    
    def _attend_to_chunk(
        self,
        query: torch.Tensor,
        chunk: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        对单个块计算注意力
        
        Returns:
            output: [batch, embed_dim]
            weight: [batch] 块的重要性权重
        """
        q = self.query_proj(query)
        k = self.key_proj(chunk)
        v = self.value_proj(chunk)
        
        attn_scores = torch.matmul(q.unsqueeze(1), k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn_weights = F.softmax(attn_scores, dim=-1)
        
        output = torch.matmul(attn_weights, v).squeeze(1)
        output = self.out_proj(output)
        
        chunk_weight = attn_scores.max(dim=-1)[0].squeeze(1)
        
        return output, chunk_weight


class HierarchicalMemoryAggregator(nn.Module):
    """
    层次化记忆聚合器
    
    结合局部和全局注意力，实现多层次记忆检索
    """
    
    def __init__(
        self,
        embed_dim: int = 768,
        num_levels: int = 3,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.num_levels = num_levels
        
        self.local_aggregators = nn.ModuleList([
            MemoryAttentionAggregator(
                embed_dim=embed_dim,
                num_blocks=4,
                num_heads=num_heads,
                dropout=dropout
            )
            for _ in range(num_levels)
        ])
        
        self.global_aggregator = MemoryAttentionAggregator(
            embed_dim=embed_dim,
            num_blocks=8,
            num_heads=num_heads,
            dropout=dropout
        )
        
        self.level_weights = nn.Parameter(torch.ones(num_levels) / num_levels)
    
    def forward(
        self,
        query: torch.Tensor,
        memories: torch.Tensor
    ) -> torch.Tensor:
        """
        层次化聚合
        
        Args:
            query: [batch, embed_dim]
            memories: [batch, num_memories, embed_dim]
            
        Returns:
            output: [batch, embed_dim]
        """
        batch_size, num_memories, dim = memories.shape
        
        level_outputs = []
        
        chunk_size = num_memories
        for level in range(self.num_levels):
            chunk_size = max(1, chunk_size // 2)
            
            num_chunks = (num_memories + chunk_size - 1) // chunk_size
            
            level_memories = []
            for i in range(num_chunks):
                start = i * chunk_size
                end = min((i + 1) * chunk_size, num_memories)
                chunk_avg = memories[:, start:end, :].mean(dim=1, keepdim=True)
                level_memories.append(chunk_avg)
            
            level_memories = torch.cat(level_memories, dim=1)
            
            level_output = self.local_aggregators[level](query, level_memories)
            level_outputs.append(level_output)
        
        global_output = self.global_aggregator(query, memories)
        
        weights = F.softmax(self.level_weights, dim=0)
        
        output = global_output
        for i, level_output in enumerate(level_outputs):
            output = output + weights[i] * level_output
        
        return output
