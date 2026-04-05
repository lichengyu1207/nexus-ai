"""
人格特征动态融合层
Personality Feature Dynamic Fusion Layer

自主实现的人格特征动态融合技术
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


class PersonalityFusionLayer(nn.Module):
    """
    自主实现的人格特征动态融合层
    
    核心原理：
    1. 人格由多个特征维度组成（儒雅、傲气、隐忍等）
    2. 根据上下文动态选择相关特征
    3. 注意力加权融合，保留原始上下文信息
    
    应用场景：
    - 周瑜/陆逊人格化交互
    - 智能体角色扮演
    - 个性化回复生成
    """
    
    DEFAULT_TRAITS = {
        "周瑜": {
            "儒雅": 0.9,
            "傲气": 0.7,
            "智谋": 0.95,
            "豪迈": 0.8,
            "深情": 0.85,
            "隐忍": 0.3,
        },
        "陆逊": {
            "儒雅": 0.85,
            "傲气": 0.3,
            "智谋": 0.9,
            "豪迈": 0.5,
            "深情": 0.7,
            "隐忍": 0.95,
        },
    }
    
    def __init__(
        self,
        num_traits: int = 6,
        trait_dim: int = 128,
        hidden_dim: int = 768,
        num_heads: int = 4,
        dropout: float = 0.1,
        personality_name: str = "周瑜"
    ):
        super().__init__()
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for PersonalityFusionLayer")
        
        self.num_traits = num_traits
        self.trait_dim = trait_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = trait_dim // num_heads
        
        assert trait_dim % num_heads == 0, "trait_dim must be divisible by num_heads"
        
        self.trait_embeddings = nn.Parameter(
            torch.randn(num_traits, trait_dim) * 0.02
        )
        
        self.trait_names = ["儒雅", "傲气", "智谋", "豪迈", "深情", "隐忍"]
        
        self.query_proj = nn.Linear(hidden_dim, trait_dim)
        self.key_proj = nn.Linear(trait_dim, trait_dim)
        self.value_proj = nn.Linear(trait_dim, trait_dim)
        
        self.context_proj = nn.Linear(trait_dim, hidden_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(hidden_dim)
        
        self.personality_name = personality_name
        self._init_personality_weights()
    
    def _init_personality_weights(self):
        """初始化人格权重"""
        if self.personality_name in self.DEFAULT_TRAITS:
            traits = self.DEFAULT_TRAITS[self.personality_name]
            weights = torch.tensor([
                traits.get(name, 0.5) for name in self.trait_names
            ], dtype=torch.float32)
            
            with torch.no_grad():
                self.trait_embeddings.data = (
                    self.trait_embeddings.data * 0.5 + 
                    weights.unsqueeze(1) * 0.5
                )
    
    def forward(
        self,
        context_embedding: torch.Tensor,
        trait_mask: Optional[torch.Tensor] = None,
        return_attention_weights: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        前向传播
        
        Args:
            context_embedding: [batch, hidden_dim] 当前对话上下文
            trait_mask: [num_traits] 可选的特征掩码
            return_attention_weights: 是否返回注意力权重
            
        Returns:
            fused: [batch, hidden_dim] 融合后的人格向量
            attn_weights: [batch, num_traits] 可选的注意力权重
        """
        batch_size = context_embedding.shape[0]
        
        q = self.query_proj(context_embedding)
        
        traits = self.trait_embeddings.unsqueeze(0).expand(batch_size, -1, -1)
        k = self.key_proj(traits)
        v = self.value_proj(traits)
        
        q = q.view(batch_size, self.num_heads, self.head_dim)
        k = k.view(batch_size, self.num_traits, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, self.num_traits, self.num_heads, self.head_dim).transpose(1, 2)
        
        attn_scores = torch.matmul(q.unsqueeze(2), k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        if trait_mask is not None:
            attn_scores = attn_scores.masked_fill(
                trait_mask.unsqueeze(0).unsqueeze(1).unsqueeze(2) == 0,
                float('-inf')
            )
        
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        attended = torch.matmul(attn_weights, v)
        attended = attended.squeeze(2).view(batch_size, self.trait_dim)
        
        fused_trait = self.context_proj(attended)
        
        fused = self.layer_norm(fused_trait + context_embedding)
        
        if return_attention_weights:
            return fused, attn_weights.squeeze(1).mean(dim=1)
        return fused
    
    def get_trait_importance(
        self,
        context_embedding: torch.Tensor
    ) -> Dict[str, float]:
        """
        获取各特征的重要性权重
        
        Args:
            context_embedding: [batch, hidden_dim]
            
        Returns:
            trait_importance: {trait_name: weight}
        """
        _, attn_weights = self.forward(
            context_embedding, return_attention_weights=True
        )
        
        avg_weights = attn_weights.mean(dim=0).cpu().numpy()
        
        trait_importance = {
            name: float(weight)
            for name, weight in zip(self.trait_names, avg_weights)
        }
        
        return trait_importance
    
    def update_personality(
        self,
        personality_name: str,
        trait_weights: Optional[Dict[str, float]] = None
    ):
        """
        更新人格设定
        
        Args:
            personality_name: 人格名称
            trait_weights: 可选的特征权重
        """
        self.personality_name = personality_name
        
        if trait_weights is None:
            trait_weights = self.DEFAULT_TRAITS.get(personality_name, {})
        
        if trait_weights:
            weights = torch.tensor([
                trait_weights.get(name, 0.5) for name in self.trait_names
            ], dtype=torch.float32)
            
            with torch.no_grad():
                self.trait_embeddings.data = (
                    self.trait_embeddings.data * 0.7 +
                    weights.unsqueeze(1) * 0.3
                )


class MultiPersonalityFusion(nn.Module):
    """
    多人格融合层
    
    支持在多个智能体人格之间动态切换
    """
    
    def __init__(
        self,
        personalities: List[str] = ["周瑜", "陆逊"],
        trait_dim: int = 128,
        hidden_dim: int = 768,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.personalities = personalities
        self.num_personalities = len(personalities)
        
        self.personality_layers = nn.ModuleDict({
            name: PersonalityFusionLayer(
                trait_dim=trait_dim,
                hidden_dim=hidden_dim,
                dropout=dropout,
                personality_name=name
            )
            for name in personalities
        })
        
        self.personality_selector = nn.Linear(hidden_dim, len(personalities))
        
        self.layer_norm = nn.LayerNorm(hidden_dim)
    
    def forward(
        self,
        context_embedding: torch.Tensor,
        personality_hint: Optional[str] = None
    ) -> torch.Tensor:
        """
        多人格融合
        
        Args:
            context_embedding: [batch, hidden_dim]
            personality_hint: 可选的人格提示
            
        Returns:
            fused: [batch, hidden_dim]
        """
        batch_size = context_embedding.shape[0]
        
        if personality_hint is not None and personality_hint in self.personalities:
            idx = self.personalities.index(personality_hint)
            personality_weights = torch.zeros(batch_size, self.num_personalities)
            personality_weights[:, idx] = 1.0
        else:
            personality_weights = F.softmax(
                self.personality_selector(context_embedding), dim=-1
            )
        
        personality_outputs = []
        for name in self.personalities:
            output = self.personality_layers[name](context_embedding)
            personality_outputs.append(output)
        
        personality_outputs = torch.stack(personality_outputs, dim=1)
        
        fused = torch.einsum('bn,bnd->bd', personality_weights, personality_outputs)
        
        return self.layer_norm(fused)
    
    def get_active_personality(
        self,
        context_embedding: torch.Tensor
    ) -> Tuple[str, float]:
        """
        获取当前最活跃的人格
        
        Returns:
            personality_name: 人格名称
            confidence: 置信度
        """
        weights = F.softmax(self.personality_selector(context_embedding), dim=-1)
        
        max_idx = weights.argmax(dim=-1)
        confidence = weights.max(dim=-1)[0]
        
        return self.personalities[max_idx], confidence


class PersonalityEvolutionTracker(nn.Module):
    """
    人格演化追踪器
    
    追踪人格特征随时间的变化
    """
    
    def __init__(
        self,
        num_traits: int = 6,
        trait_dim: int = 128,
        history_length: int = 100
    ):
        super().__init__()
        
        self.num_traits = num_traits
        self.trait_dim = trait_dim
        self.history_length = history_length
        
        self.register_buffer(
            'trait_history',
            torch.zeros(history_length, num_traits, trait_dim)
        )
        self.register_buffer('history_ptr', torch.tensor(0))
        
        self.evolution_proj = nn.Linear(trait_dim, trait_dim)
    
    def update(
        self,
        trait_embedding: torch.Tensor
    ):
        """
        更新特征历史
        
        Args:
            trait_embedding: [num_traits, trait_dim]
        """
        ptr = self.history_ptr.item()
        
        self.trait_history[ptr] = trait_embedding
        
        self.history_ptr.copy_((ptr + 1) % self.history_length)
    
    def get_evolution_trend(
        self,
        trait_idx: int,
        window: int = 10
    ) -> torch.Tensor:
        """
        获取特征演化趋势
        
        Args:
            trait_idx: 特征索引
            window: 时间窗口
            
        Returns:
            trend: [trait_dim] 演化趋势向量
        """
        ptr = self.history_ptr.item()
        
        indices = [(ptr - i - 1) % self.history_length for i in range(window)]
        
        history = self.trait_history[indices, trait_idx, :]
        
        trend = history.mean(dim=0)
        
        return self.evolution_proj(trend)
    
    def get_stability_score(self) -> float:
        """
        获取人格稳定性分数
        
        Returns:
            stability: 稳定性分数 (0-1)
        """
        ptr = self.history_ptr.item()
        
        if ptr < 10:
            return 1.0
        
        recent = self.trait_history[(ptr - 10):ptr]
        
        variance = recent.var(dim=0).mean()
        
        stability = 1.0 / (1.0 + variance.item())
        
        return stability
