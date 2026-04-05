# -*- coding: utf-8 -*-
"""
Hippocampus Retriever - Attention Residuals 核心实现
基于注意力残差的海马体记忆检索系统
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import math

from backend.services.attention_residuals.models import (
    MemoryEntry, MemoryBlock, AttentionResult
)


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        norm = x.float().pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return (x.float() * norm).type_as(x) * self.weight


class MemoryBlocker:
    def __init__(self, block_size: int = 50):
        self.block_size = block_size

    def block_memories(self, memories: List[MemoryEntry]) -> List[MemoryBlock]:
        blocks = []
        num_memories = len(memories)
        num_blocks = math.ceil(num_memories / self.block_size)
        
        for i in range(num_blocks):
            start_idx = i * self.block_size
            end_idx = min((i + 1) * self.block_size, num_memories)
            block_memories = memories[start_idx:end_idx]
            
            memory_ids = [m.id for m in block_memories]
            embeddings = [m.embedding for m in block_memories if m.embedding]
            
            if embeddings:
                block_vector = np.mean(embeddings, axis=0).tolist()
            else:
                block_vector = None
            
            avg_importance = np.mean([m.importance for m in block_memories])
            
            block = MemoryBlock(
                id=f"block_{i}",
                user_id=memories[0].user_id if memories else "",
                block_index=i,
                memory_ids=memory_ids,
                block_vector=block_vector,
                memory_count=len(block_memories),
                avg_importance=avg_importance
            )
            blocks.append(block)
        
        return blocks

    def aggregate_block(self, embeddings: List[List[float]]) -> List[float]:
        if not embeddings:
            return [0.0] * 768
        return np.mean(embeddings, axis=0).tolist()


class AttentionComputer(nn.Module):
    def __init__(self, embed_dim: int = 768):
        super().__init__()
        self.embed_dim = embed_dim
        self.rms_norm = RMSNorm(embed_dim)
        self.query_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.key_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.value_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        
        nn.init.xavier_uniform_(self.query_proj.weight)
        nn.init.xavier_uniform_(self.key_proj.weight)
        nn.init.xavier_uniform_(self.value_proj.weight)

    def forward(
        self, 
        query: torch.Tensor, 
        block_vectors: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        q = self.query_proj(query.unsqueeze(0))
        k = self.key_proj(self.rms_norm(block_vectors))
        v = self.value_proj(block_vectors)
        
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.embed_dim)
        attn_weights = F.softmax(scores, dim=-1)
        
        aggregated = torch.matmul(attn_weights, v)
        
        return aggregated.squeeze(0), attn_weights.squeeze(0)


class ResidualConnector(nn.Module):
    def __init__(self, embed_dim: int = 768, residual_weight: float = 0.5):
        super().__init__()
        self.embed_dim = embed_dim
        self.residual_weight = residual_weight

    def forward(
        self, 
        aggregated: torch.Tensor, 
        query: torch.Tensor
    ) -> torch.Tensor:
        output = aggregated + self.residual_weight * query
        return output


class HippocampusRetriever(nn.Module):
    def __init__(
        self,
        embed_dim: int = 768,
        block_size: int = 50,
        top_k: int = 100,
        residual_weight: float = 0.5
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.block_size = block_size
        self.top_k = top_k
        
        self.blocker = MemoryBlocker(block_size)
        self.attention = AttentionComputer(embed_dim)
        self.residual = ResidualConnector(embed_dim, residual_weight)
        
        self._initialized = False

    def initialize(self):
        if not self._initialized:
            self._initialized = True

    @torch.no_grad()
    def retrieve(
        self,
        query_vector: List[float],
        memory_entries: List[MemoryEntry],
        return_weights: bool = True
    ) -> AttentionResult:
        if not memory_entries:
            return AttentionResult(
                context_vector=query_vector,
                block_weights=[],
                selected_blocks=[],
                selected_memories=[],
                confidence_score=0.0
            )
        
        query_tensor = torch.tensor(query_vector, dtype=torch.float32)
        
        blocks = self.blocker.block_memories(memory_entries)
        
        block_vectors = []
        valid_blocks = []
        for block in blocks:
            if block.block_vector:
                block_vectors.append(block.block_vector)
                valid_blocks.append(block)
        
        if not block_vectors:
            return AttentionResult(
                context_vector=query_vector,
                block_weights=[],
                selected_blocks=[],
                selected_memories=[],
                confidence_score=0.0
            )
        
        block_tensor = torch.tensor(block_vectors, dtype=torch.float32)
        
        aggregated, attn_weights = self.attention(query_tensor, block_tensor)
        
        context = self.residual(aggregated, query_tensor)
        
        block_weights = attn_weights.tolist()
        
        top_indices = torch.argsort(attn_weights, descending=True)[:3].tolist()
        selected_blocks = [valid_blocks[i].block_index for i in top_indices if i < len(valid_blocks)]
        selected_memories = []
        for idx in top_indices:
            if idx < len(valid_blocks):
                selected_memories.extend(valid_blocks[idx].memory_ids[:5])
        
        confidence = float(torch.max(attn_weights).item())
        
        return AttentionResult(
            context_vector=context.tolist(),
            block_weights=block_weights,
            selected_blocks=selected_blocks,
            selected_memories=selected_memories[:15],
            confidence_score=confidence
        )

    def compute_attention_weights(
        self,
        query_vector: List[float],
        block_vectors: List[List[float]]
    ) -> List[float]:
        if not block_vectors:
            return []
        
        query_tensor = torch.tensor(query_vector, dtype=torch.float32)
        block_tensor = torch.tensor(block_vectors, dtype=torch.float32)
        
        _, attn_weights = self.attention(query_tensor, block_tensor)
        
        return attn_weights.tolist()


_hippocampus_retriever: Optional[HippocampusRetriever] = None


def get_hippocampus_retriever() -> Optional[HippocampusRetriever]:
    return _hippocampus_retriever


def init_hippocampus_retriever(
    embed_dim: int = 768,
    block_size: int = 50,
    top_k: int = 100
) -> HippocampusRetriever:
    global _hippocampus_retriever
    _hippocampus_retriever = HippocampusRetriever(
        embed_dim=embed_dim,
        block_size=block_size,
        top_k=top_k
    )
    _hippocampus_retriever.initialize()
    return _hippocampus_retriever
