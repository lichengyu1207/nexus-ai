"""
活体智能体生态系统模块
Living Agent Ecosystem Module

实现攻击、防御、记忆三大集群的活体化设计
"""

from .living_agent import (
    LivingAgent,
    AgentRole,
    AgentStatus,
    Gene,
    GenePool
)

from .living_attack_agent import (
    LivingAttackAgent,
    AttackStrategy
)

from .living_defense_agent import (
    LivingDefenseAgent,
    DefenseStrategy
)

from .living_memory_agent import (
    LivingMemoryAgent,
    MemoryType,
    MemoryPriority,
    MemoryEntry
)

from .coordinator import (
    EcosystemCoordinator,
    EcosystemState,
    EcosystemMetrics
)

__all__ = [
    "LivingAgent",
    "AgentRole",
    "AgentStatus",
    "Gene",
    "GenePool",
    "LivingAttackAgent",
    "AttackStrategy",
    "LivingDefenseAgent",
    "DefenseStrategy",
    "LivingMemoryAgent",
    "MemoryType",
    "MemoryPriority",
    "MemoryEntry",
    "EcosystemCoordinator",
    "EcosystemState",
    "EcosystemMetrics"
]
