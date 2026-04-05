"""
海马体记忆系统 - 集成Attention Residuals
实现基于注意力残差的记忆检索和融合
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import asyncio
import numpy as np

from backend.models.attention_residual import (
    MemoryAttentionResidual,
    LightweightAttnRes,
    create_attention_residual
)

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    embedding: torch.Tensor
    timestamp: datetime
    importance: float
    memory_type: str  # 'episodic', 'semantic', 'procedural'
    context: Dict[str, Any]
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class HippocampusConfig:
    """海马体配置"""
    memory_dim: int = 768
    max_short_term_memory: int = 100
    max_long_term_memory: int = 10000
    consolidation_threshold: float = 0.7
    forgetting_rate: float = 0.01
    attention_heads: int = 8
    dropout: float = 0.1


class HippocampusMemorySystem(nn.Module):
    """
    海马体记忆系统
    
    集成Attention Residuals技术，实现:
    1. 记忆检索时动态选择最相关的记忆片段
    2. 避免简单加权平均导致的记忆稀释
    3. 支持长期记忆和短期记忆的融合
    """
    
    def __init__(self, config: HippocampusConfig):
        super().__init__()
        self.config = config
        
        self.memory_attn = MemoryAttentionResidual(
            memory_dim=config.memory_dim,
            num_memory_heads=config.attention_heads,
            max_memories=config.max_long_term_memory,
            dropout=config.dropout
        )
        
        self.lightweight_attn = LightweightAttnRes(
            dim=config.memory_dim,
            dropout=config.dropout
        )
        
        self.importance_scorer = nn.Sequential(
            nn.Linear(config.memory_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
        
        self.memory_encoder = nn.Linear(config.memory_dim, config.memory_dim)
        self.context_encoder = nn.Linear(config.memory_dim * 2, config.memory_dim)
        
        self.short_term_memory: List[MemoryEntry] = []
        self.long_term_memory: List[MemoryEntry] = []
        
        self.consolidation_buffer: List[MemoryEntry] = []
        
    def encode_memory(
        self,
        content: str,
        embedding: torch.Tensor,
        context: Optional[Dict[str, Any]] = None
    ) -> torch.Tensor:
        """
        编码记忆
        
        Args:
            content: 记忆内容
            embedding: 原始嵌入向量
            context: 上下文信息
            
        Returns:
            encoded: 编码后的记忆向量
        """
        encoded = self.memory_encoder(embedding)
        
        if context:
            context_vec = self._encode_context(context)
            encoded = self.context_encoder(
                torch.cat([encoded, context_vec], dim=-1)
            )
            
        return encoded
        
    def _encode_context(self, context: Dict[str, Any]) -> torch.Tensor:
        """编码上下文信息"""
        context_str = json.dumps(context, default=str)
        context_hash = hash(context_str) % (2 ** 32)
        context_vec = torch.zeros(self.config.memory_dim)
        
        for i, char in enumerate(context_str[:self.config.memory_dim]):
            context_vec[i] = ord(char) / 255.0
            
        return context_vec
        
    async def store_memory(
        self,
        content: str,
        embedding: torch.Tensor,
        memory_type: str = 'episodic',
        context: Optional[Dict[str, Any]] = None,
        importance: Optional[float] = None
    ) -> str:
        """
        存储新记忆
        
        Args:
            content: 记忆内容
            embedding: 嵌入向量
            memory_type: 记忆类型
            context: 上下文
            importance: 重要性分数
            
        Returns:
            memory_id: 记忆ID
        """
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        encoded_embedding = self.encode_memory(content, embedding, context)
        
        if importance is None:
            with torch.no_grad():
                importance = self.importance_scorer(encoded_embedding).item()
                
        memory_entry = MemoryEntry(
            id=memory_id,
            content=content,
            embedding=encoded_embedding,
            timestamp=datetime.now(),
            importance=importance,
            memory_type=memory_type,
            context=context or {}
        )
        
        self.short_term_memory.append(memory_entry)
        
        if len(self.short_term_memory) > self.config.max_short_term_memory:
            await self._consolidate_memories()
            
        self.memory_attn.store_memory(encoded_embedding.detach())
        
        logger.info(f"Stored memory: {memory_id}, type={memory_type}, importance={importance:.3f}")
        
        return memory_id
        
    async def _consolidate_memories(self):
        """
        记忆巩固：将短期记忆转移到长期记忆
        使用Attention Residuals选择最有价值的记忆
        """
        if not self.short_term_memory:
            return
            
        memories_to_consolidate = []
        memories_to_forget = []
        
        for memory in self.short_term_memory:
            memory.importance *= (1 - self.config.forgetting_rate)
            
            if memory.importance >= self.config.consolidation_threshold:
                memories_to_consolidate.append(memory)
            else:
                memories_to_forget.append(memory)
                
        for memory in memories_to_consolidate:
            self.long_term_memory.append(memory)
            
        self.short_term_memory = [
            m for m in self.short_term_memory 
            if m not in memories_to_forget
        ]
        
        if len(self.long_term_memory) > self.config.max_long_term_memory:
            self.long_term_memory.sort(key=lambda m: m.importance, reverse=True)
            self.long_term_memory = self.long_term_memory[:self.config.max_long_term_memory]
            
        logger.info(
            f"Memory consolidation: {len(memories_to_consolidate)} consolidated, "
            f"{len(memories_to_forget)} forgotten"
        )
        
    async def retrieve_memory(
        self,
        query_embedding: torch.Tensor,
        top_k: int = 5,
        memory_types: Optional[List[str]] = None
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        检索相关记忆
        
        使用Attention Residuals动态选择最相关的记忆片段
        
        Args:
            query_embedding: 查询嵌入向量
            top_k: 返回top-k个记忆
            memory_types: 限制记忆类型
            
        Returns:
            memories: [(MemoryEntry, score), ...]
        """
        all_memories = self.short_term_memory + self.long_term_memory
        
        if memory_types:
            all_memories = [
                m for m in all_memories 
                if m.memory_type in memory_types
            ]
            
        if not all_memories:
            return []
            
        memory_embeddings = torch.stack([m.embedding for m in all_memories])
        
        with torch.no_grad():
            short_term_emb = torch.mean(
                torch.stack([m.embedding for m in self.short_term_memory[:10]]),
                dim=0
            ) if self.short_term_memory else torch.zeros(self.config.memory_dim)
            
            long_term_emb = torch.mean(
                torch.stack([m.embedding for m in self.long_term_memory[:100]]),
                dim=0
            ) if self.long_term_memory else torch.zeros(self.config.memory_dim)
            
            fused_state = self.memory_attn(
                query_embedding,
                short_term_memory=short_term_emb.unsqueeze(0),
                long_term_memory=long_term_emb.unsqueeze(0)
            )
            
            scores = F.cosine_similarity(
                fused_state.unsqueeze(0),
                memory_embeddings,
                dim=-1
            )
            
        top_k_indices = torch.topk(scores, min(top_k, len(all_memories))).indices
        
        results = []
        for idx in top_k_indices:
            memory = all_memories[idx]
            score = scores[idx].item()
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            results.append((memory, score))
            
        return results
        
    def recall_with_attention(
        self,
        query: torch.Tensor,
        history_states: List[torch.Tensor]
    ) -> torch.Tensor:
        """
        使用Attention Residuals回忆
        
        不再简单加权平均历史记忆，而是用注意力机制动态选择最相关的记忆片段
        
        Args:
            query: 查询向量
            history_states: 历史状态列表
            
        Returns:
            recalled: 回忆结果
        """
        return self.lightweight_attn(query, history_states)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "short_term_count": len(self.short_term_memory),
            "long_term_count": len(self.long_term_memory),
            "total_memories": len(self.short_term_memory) + len(self.long_term_memory),
            "avg_importance": np.mean([m.importance for m in self.short_term_memory + self.long_term_memory]) if self.short_term_memory or self.long_term_memory else 0,
            "memory_types": {
                "episodic": len([m for m in self.short_term_memory + self.long_term_memory if m.memory_type == 'episodic']),
                "semantic": len([m for m in self.short_term_memory + self.long_term_memory if m.memory_type == 'semantic']),
                "procedural": len([m for m in self.short_term_memory + self.long_term_memory if m.memory_type == 'procedural']),
            }
        }
        
    def export_memories(self) -> List[Dict[str, Any]]:
        """导出记忆用于持久化"""
        memories = []
        for m in self.short_term_memory + self.long_term_memory:
            memories.append({
                "id": m.id,
                "content": m.content,
                "embedding": m.embedding.tolist() if isinstance(m.embedding, torch.Tensor) else m.embedding,
                "timestamp": m.timestamp.isoformat(),
                "importance": m.importance,
                "memory_type": m.memory_type,
                "context": m.context,
                "access_count": m.access_count,
                "last_accessed": m.last_accessed.isoformat() if m.last_accessed else None
            })
        return memories
        
    def import_memories(self, memories: List[Dict[str, Any]]):
        """导入记忆"""
        for m in memories:
            memory_entry = MemoryEntry(
                id=m["id"],
                content=m["content"],
                embedding=torch.tensor(m["embedding"]),
                timestamp=datetime.fromisoformat(m["timestamp"]),
                importance=m["importance"],
                memory_type=m["memory_type"],
                context=m["context"],
                access_count=m.get("access_count", 0),
                last_accessed=datetime.fromisoformat(m["last_accessed"]) if m.get("last_accessed") else None
            )
            
            if memory_entry.importance >= self.config.consolidation_threshold:
                self.long_term_memory.append(memory_entry)
            else:
                self.short_term_memory.append(memory_entry)


class HippocampusService:
    """
    海马体服务 - 对外接口
    """
    
    def __init__(self, config: Optional[HippocampusConfig] = None):
        self.config = config or HippocampusConfig()
        self.hippocampus = HippocampusMemorySystem(self.config)
        
    async def remember(
        self,
        content: str,
        embedding: torch.Tensor,
        memory_type: str = 'episodic',
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """记住新信息"""
        return await self.hippocampus.store_memory(
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            context=context
        )
        
    async def recall(
        self,
        query_embedding: torch.Tensor,
        top_k: int = 5,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """回忆相关信息"""
        results = await self.hippocampus.retrieve_memory(
            query_embedding=query_embedding,
            top_k=top_k,
            memory_types=memory_types
        )
        
        return [
            {
                "id": memory.id,
                "content": memory.content,
                "score": score,
                "memory_type": memory.memory_type,
                "timestamp": memory.timestamp.isoformat()
            }
            for memory, score in results
        ]
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.hippocampus.get_memory_stats()


__all__ = [
    'HippocampusMemorySystem',
    'HippocampusConfig',
    'HippocampusService',
    'MemoryEntry',
]
