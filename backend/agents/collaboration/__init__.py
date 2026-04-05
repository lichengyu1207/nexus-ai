"""
协作模块初始化文件
Collaboration Module Init
"""

from backend.agents.collaboration.dual_mode_agent import (
    DualModeAttackAgent,
    WarDefenseAgent,
    AgentCluster,
    AgentMode,
    AgentConfig
)

from backend.agents.collaboration.war_center import (
    WarCenter,
    AttackDetector,
    ModeSwitcher,
    AdviceFuser,
    WarBus,
    SystemState,
    AttackSignature,
    DefenseAdvice,
    FusedDecision
)

from backend.agents.collaboration.external_attack_env import (
    ExternalAttackEnv,
    ExternalAttackGenerator,
    AttackType,
    AttackPattern,
    ExternalAttackState,
    CollaborationRewardCalculator
)

from backend.agents.collaboration.collaboration_training import (
    CollaborationTrainingPipeline,
    Stage1Trainer,
    Stage2Trainer,
    Stage3Trainer,
    TrainingConfig
)

from backend.agents.collaboration.security_redundancy import (
    SecurityManager,
    AdviceValidator,
    MaliciousDetector,
    RedundancyManager,
    ConsensusEngine
)

__all__ = [
    "DualModeAttackAgent",
    "WarDefenseAgent",
    "AgentCluster",
    "AgentMode",
    "AgentConfig",
    "WarCenter",
    "AttackDetector",
    "ModeSwitcher",
    "AdviceFuser",
    "WarBus",
    "SystemState",
    "AttackSignature",
    "DefenseAdvice",
    "FusedDecision",
    "ExternalAttackEnv",
    "ExternalAttackGenerator",
    "AttackType",
    "AttackPattern",
    "ExternalAttackState",
    "CollaborationRewardCalculator",
    "CollaborationTrainingPipeline",
    "Stage1Trainer",
    "Stage2Trainer",
    "Stage3Trainer",
    "TrainingConfig",
    "SecurityManager",
    "AdviceValidator",
    "MaliciousDetector",
    "RedundancyManager",
    "ConsensusEngine"
]
