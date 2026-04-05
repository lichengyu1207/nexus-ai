"""
智能体集群自主数据采集与知识蒸馏模块
Agent Cluster Autonomous Data Collection and Knowledge Distillation

让智能体像生物一样自主获取"食物"（数据），从经验中提炼知识
"""

from .data_collector import (
    DataCollectorAgent,
    DataSourceType,
    CollectionStatus,
    CollectionResult,
    CollectionSchedule,
)
from .web_crawler import (
    WebCrawlerAgent,
    CrawlConfig,
    CrawlResult,
    ParsedPage,
)
from .api_collector import (
    APICollectorAgent,
    APIConfig,
    APIResponse,
    RateLimiter,
)
from .user_interaction_collector import (
    UserInteractionCollectorAgent,
    UserInteractionSample,
    InteractionType,
    FeedbackType,
)
from .agent_interaction_collector import (
    AgentInteractionCollectorAgent,
    AgentInteractionSample,
    AgentInteractionType,
    InteractionOutcome,
)
from .sample_repository import (
    SampleRepository,
    Sample,
    SampleType,
    SampleStatus,
    SampleQuery,
)
from .sample_quality import (
    SampleQualityAssessor,
    QualityScore,
    QualityDimension,
    SampleForAssessment,
)
from .knowledge_distiller import (
    KnowledgeDistillerAgent,
    DistillationResult,
    DistillationStatus,
    DistillationMethod,
    KnowledgeType,
    ModelRegistry,
)
from .llm_distiller import (
    LLMDistillerAgent,
    TeacherModel,
    StudentModelConfig,
    DistillationConfig,
)
from .experience_distiller import (
    ExperienceDistillerAgent,
    ExperienceSample,
    ExperienceType,
    Rule,
    DecisionNode,
)
from .knowledge_transfer import (
    KnowledgeTransferAgent,
    KnowledgePackage,
    KnowledgeForm,
    TransferRequest,
    TransferRecord,
)
from .data_demand import (
    DataDemandSensor,
    DataDemand,
    DemandUrgency,
    DemandStatus,
    KnowledgeBlindSpot,
)
from .adaptive_scheduler import (
    AdaptiveCollectionScheduler,
    CollectionTask,
    CollectorState,
    SourceStats,
    SchedulePriority,
)
from .sample_distribution import (
    SampleDistributionService,
    SampleRequest,
    SampleBatch,
    DistributionMode,
    DistributionPriority,
)
from .online_learning import (
    OnlineLearningInterface,
    LearningSession,
    LearningStatus,
    LearningTrigger,
    LearningConfig,
    IncrementalLearner,
)
from .compliance_checker import (
    DataCollectionComplianceChecker,
    ComplianceRule,
    ViolationRecord,
    ComplianceStatus,
    ViolationSeverity,
)
from .privacy_protector import (
    SamplePrivacyProtector,
    PrivacyLevel,
    AnonymizationMethod,
    AccessPermission,
)
from .memory_bridge import (
    MemorySampleBridge,
    MemoryExport,
    SampleImport,
    SyncDirection,
    SyncStatus,
)
from .evolution_integration import (
    SampleDrivenEvolution,
    EvolutionScore,
    AgentDataProfile,
    DataEvolutionGene,
    FitnessComponent,
)

__all__ = [
    "DataCollectorAgent",
    "DataSourceType",
    "CollectionStatus",
    "CollectionResult",
    "CollectionSchedule",
    "WebCrawlerAgent",
    "CrawlConfig",
    "CrawlResult",
    "ParsedPage",
    "APICollectorAgent",
    "APIConfig",
    "APIResponse",
    "RateLimiter",
    "UserInteractionCollectorAgent",
    "UserInteractionSample",
    "InteractionType",
    "FeedbackType",
    "AgentInteractionCollectorAgent",
    "AgentInteractionSample",
    "AgentInteractionType",
    "InteractionOutcome",
    "SampleRepository",
    "Sample",
    "SampleType",
    "SampleStatus",
    "SampleQuery",
    "SampleQualityAssessor",
    "QualityScore",
    "QualityDimension",
    "SampleForAssessment",
    "KnowledgeDistillerAgent",
    "DistillationResult",
    "DistillationStatus",
    "DistillationMethod",
    "KnowledgeType",
    "ModelRegistry",
    "LLMDistillerAgent",
    "TeacherModel",
    "StudentModelConfig",
    "DistillationConfig",
    "ExperienceDistillerAgent",
    "ExperienceSample",
    "ExperienceType",
    "Rule",
    "DecisionNode",
    "KnowledgeTransferAgent",
    "KnowledgePackage",
    "KnowledgeForm",
    "TransferRequest",
    "TransferRecord",
    "DataDemandSensor",
    "DataDemand",
    "DemandUrgency",
    "DemandStatus",
    "KnowledgeBlindSpot",
    "AdaptiveCollectionScheduler",
    "CollectionTask",
    "CollectorState",
    "SourceStats",
    "SchedulePriority",
    "SampleDistributionService",
    "SampleRequest",
    "SampleBatch",
    "DistributionMode",
    "DistributionPriority",
    "OnlineLearningInterface",
    "LearningSession",
    "LearningStatus",
    "LearningTrigger",
    "LearningConfig",
    "IncrementalLearner",
    "DataCollectionComplianceChecker",
    "ComplianceRule",
    "ViolationRecord",
    "ComplianceStatus",
    "ViolationSeverity",
    "SamplePrivacyProtector",
    "PrivacyLevel",
    "AnonymizationMethod",
    "AccessPermission",
    "MemorySampleBridge",
    "MemoryExport",
    "SampleImport",
    "SyncDirection",
    "SyncStatus",
    "SampleDrivenEvolution",
    "EvolutionScore",
    "AgentDataProfile",
    "DataEvolutionGene",
    "FitnessComponent",
]
