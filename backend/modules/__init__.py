"""
前沿AI技术模块
Advanced AI Technology Modules

自主实现三项2026年最新AI技术：
1. Attention Residuals - 按需聚合历史信息
2. Kimi Linear - 线性注意力机制
3. MuonClip - 高效优化器
"""

from .attn_residual_memory import MemoryAttentionAggregator
from .personality_fusion import PersonalityFusionLayer
from .agent_scheduler import AgentScheduler
from .linear_attention import LinearAttention, ChunkedLinearAttention
from .muon_clip import MuonClip

__all__ = [
    "MemoryAttentionAggregator",
    "PersonalityFusionLayer",
    "AgentScheduler",
    "LinearAttention",
    "ChunkedLinearAttention",
    "MuonClip",
]
