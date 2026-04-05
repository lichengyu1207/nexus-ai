"""
人格化引擎 - 集成Attention Residuals
实现多层人格特征的按需融合，避免浅层特征被深层稀释
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from models.light_attn_res import PersonalityFusion
except ImportError:
    from backend.models.light_attn_res import PersonalityFusion

logger = logging.getLogger(__name__)


class PersonalityType(Enum):
    ZHOUYU = "zhouyu"
    LUXUN = "luxun"
    ZHUGELIANG = "zhugeliang"
    SIMAYI = "simayi"


@dataclass
class PersonalityProfile:
    name: str
    style: str
    icon: str
    description: str
    traits: Dict[str, float]


PERSONALITIES = {
    PersonalityType.ZHOUYU: PersonalityProfile(
        name="周瑜",
        style="激进",
        icon="🔥",
        description="火眼金睛，快速发现价值",
        traits={"decisiveness": 0.9, "risk_tolerance": 0.85, "speed": 0.95, "confidence": 0.88}
    ),
    PersonalityType.LUXUN: PersonalityProfile(
        name="陆逊",
        style="稳健",
        icon="⚖️",
        description="稳扎稳打，全面评估",
        traits={"decisiveness": 0.7, "risk_tolerance": 0.5, "caution": 0.9, "patience": 0.85}
    ),
    PersonalityType.ZHUGELIANG: PersonalityProfile(
        name="诸葛亮",
        style="深度",
        icon="🧠",
        description="运筹帷幄，深度分析",
        traits={"depth": 0.95, "wisdom": 0.98, "foresight": 0.92, "strategy": 0.96}
    ),
    PersonalityType.SIMAYI: PersonalityProfile(
        name="司马懿",
        style="数据",
        icon="📊",
        description="精打细算，数据驱动",
        traits={"precision": 0.95, "calculation": 0.98, "patience": 0.9, "data_driven": 0.97}
    )
}


class AttnResPersonalityEngine:
    """
    基于Attention Residuals的人格化引擎
    
    角色在不同对话上下文中会动态调整人格特征的权重
    比如用户谈论战争时，"兵部"相关的特征权重提高
    """
    
    def __init__(self, dim: int = 256):
        self.dim = dim
        self.fusion = PersonalityFusion(dim)
        
        self.trait_embeddings = nn.ParameterDict({
            p_type.value: nn.Parameter(torch.randn(len(profile.traits), dim))
            for p_type, profile in PERSONALITIES.items()
        })
        
        self.trait_names = {
            p_type: list(profile.traits.keys())
            for p_type, profile in PERSONALITIES.items()
        }
        
        self.trait_values = {
            p_type: torch.tensor(list(profile.traits.values()))
            for p_type, profile in PERSONALITIES.items()
        }
        
    def get_personality_embedding(self, personality_type: PersonalityType) -> torch.Tensor:
        """获取人格嵌入向量"""
        return self.trait_embeddings[personality_type.value]
        
    def fuse_with_context(
        self,
        context_embedding: torch.Tensor,
        personality_type: PersonalityType
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        将上下文与人格特征融合
        
        Args:
            context_embedding: [dim] 当前上下文向量
            personality_type: 人格类型
            
        Returns:
            fused: [dim] 融合后的向量
            trait_weights: 各特征的权重
        """
        trait_emb = self.trait_embeddings[personality_type.value]
        
        fused = self.fusion(context_embedding, trait_emb)
        
        query = self.fusion.query_proj(context_embedding).unsqueeze(0)
        keys = self.fusion.key_proj(trait_emb)
        
        attn_weights = F.softmax(query @ keys.T, dim=-1).squeeze(0)
        
        trait_names = self.trait_names[personality_type]
        trait_weights = {
            name: weight.item()
            for name, weight in zip(trait_names, attn_weights)
        }
        
        return fused, trait_weights
        
    def blend_personalities(
        self,
        context_embedding: torch.Tensor,
        personality_weights: Dict[PersonalityType, float]
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        混合多个人格
        
        Args:
            context_embedding: 上下文向量
            personality_weights: 人格权重字典
            
        Returns:
            blended: 混合后的向量
            metadata: 元数据
        """
        total_weight = sum(personality_weights.values())
        
        blended = torch.zeros(self.dim)
        trait_contributions = {}
        
        for p_type, weight in personality_weights.items():
            normalized = weight / total_weight
            
            fused, trait_weights = self.fuse_with_context(context_embedding, p_type)
            blended = blended + normalized * fused
            
            profile = PERSONALITIES[p_type]
            for trait, tw in trait_weights.items():
                if trait not in trait_contributions:
                    trait_contributions[trait] = 0
                trait_contributions[trait] += normalized * tw
                
        dominant = max(personality_weights.items(), key=lambda x: x[1])[0]
        
        metadata = {
            "dominant_personality": PERSONALITIES[dominant].name,
            "trait_contributions": trait_contributions,
            "blend_ratio": {PERSONALITIES[p].name: w/total_weight for p, w in personality_weights.items()}
        }
        
        return blended, metadata
        
    def get_personality_profile(self, personality_type: PersonalityType) -> Dict[str, Any]:
        """获取人格档案"""
        profile = PERSONALITIES[personality_type]
        return {
            "name": profile.name,
            "style": profile.style,
            "icon": profile.icon,
            "description": profile.description,
            "traits": profile.traits
        }
        
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """获取所有人格档案"""
        return {
            profile.name: {
                "name": profile.name,
                "style": profile.style,
                "icon": profile.icon,
                "description": profile.description,
                "traits": profile.traits
            }
            for profile in PERSONALITIES.values()
        }


personality_engine = AttnResPersonalityEngine()


def get_personality_response(
    context: str,
    personality_name: str,
    context_embedding: Optional[torch.Tensor] = None
) -> Dict[str, Any]:
    """
    获取人格化响应
    
    Args:
        context: 上下文文本
        personality_name: 人格名称
        context_embedding: 上下文嵌入（可选）
        
    Returns:
        response: 响应信息
    """
    name_map = {
        "周瑜": PersonalityType.ZHOUYU,
        "陆逊": PersonalityType.LUXUN,
        "诸葛亮": PersonalityType.ZHUGELIANG,
        "司马懿": PersonalityType.SIMAYI,
        "zhouyu": PersonalityType.ZHOUYU,
        "luxun": PersonalityType.LUXUN,
        "zhugeliang": PersonalityType.ZHUGELIANG,
        "simayi": PersonalityType.SIMAYI
    }
    
    p_type = name_map.get(personality_name, PersonalityType.ZHUGELIANG)
    
    if context_embedding is None:
        context_embedding = torch.randn(256)
        
    fused, trait_weights = personality_engine.fuse_with_context(context_embedding, p_type)
    
    profile = PERSONALITIES[p_type]
    
    return {
        "personality": profile.name,
        "style": profile.style,
        "icon": profile.icon,
        "trait_weights": trait_weights,
        "context": context
    }


__all__ = [
    'AttnResPersonalityEngine',
    'PersonalityType',
    'PersonalityProfile',
    'PERSONALITIES',
    'personality_engine',
    'get_personality_response',
]
