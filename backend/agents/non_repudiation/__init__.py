"""
不可抵赖记录系统模块
Non-Repudiation Record System Module

实现自适应学习率、跨物种合作、联邦学习、数据隐私、关键事件不可抵赖记录等功能
"""

from .adaptive_learning import (
    AdaptiveLRScheduler,
    LearningRateHistory,
    CosineAnnealingScheduler,
    ReduceOnPlateauScheduler,
    MetaLearner,
    MetaLearningRate,
)

from .cross_species_cooperation import (
    TaskDecomposer,
    DepartmentCapabilityRegistry,
    TemporaryTeam,
    SharedFeatureNet,
    DepartmentAgent,
    GlobalReplayBuffer,
    CrossSpeciesExperience,
)

from .federated_learning import (
    FederatedLearner,
    FederatedNode,
    FedAvgAggregator,
    SecureAggregator,
    DPModule,
    DifferentialPrivacy,
    PrivacyBudgetTracker,
)

from .data_privacy import (
    DataMasker,
    SensitiveEntityRecognizer,
    AnonymizationEngine,
    ReversibleMasker,
)

from .immutable_logger import (
    ImmutableEventLogger,
    EventRecord,
    HashChain,
    DigitalSigner,
    EventVerifier,
)

from .trusted_timestamp import (
    TrustedTimestampService,
    TimestampToken,
    NTPSynchronizer,
    ExternalTSA,
)

from .training_logger import (
    TrainingLogger,
    TrainingRecord,
    ModelHashCalculator,
    TrainingIntegrityVerifier,
)

from .model_registry import (
    ModelRegistry,
    ModelVersion,
    ModelVerification,
    ModelRollbackManager,
)

__all__ = [
    "AdaptiveLRScheduler",
    "LearningRateHistory",
    "CosineAnnealingScheduler",
    "ReduceOnPlateauScheduler",
    "MetaLearner",
    "MetaLearningRate",
    "TaskDecomposer",
    "DepartmentCapabilityRegistry",
    "TemporaryTeam",
    "SharedFeatureNet",
    "DepartmentAgent",
    "GlobalReplayBuffer",
    "CrossSpeciesExperience",
    "FederatedLearner",
    "FederatedNode",
    "FedAvgAggregator",
    "SecureAggregator",
    "DPModule",
    "DifferentialPrivacy",
    "PrivacyBudgetTracker",
    "DataMasker",
    "SensitiveEntityRecognizer",
    "AnonymizationEngine",
    "ReversibleMasker",
    "ImmutableEventLogger",
    "EventRecord",
    "HashChain",
    "DigitalSigner",
    "EventVerifier",
    "TrustedTimestampService",
    "TimestampToken",
    "NTPSynchronizer",
    "ExternalTSA",
    "TrainingLogger",
    "TrainingRecord",
    "ModelHashCalculator",
    "TrainingIntegrityVerifier",
    "ModelRegistry",
    "ModelVersion",
    "ModelVerification",
    "ModelRollbackManager",
]
