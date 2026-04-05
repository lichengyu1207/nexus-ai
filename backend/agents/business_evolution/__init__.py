"""
业务级智能体深度进化模块
Business Agent Deep Evolution System

让业务智能体真正理解用户、适应场景、优化服务
"""

from .intent_recognizer import (
    IntentRecognizer,
    UserIntent,
    IntentCategory,
    EmotionType,
)
from .dialogue_strategy import (
    DialogueStrategyEngine,
    UserProfile,
    DialogueStyle,
    StrategyType,
)
from .session_memory import (
    SessionMemoryManager,
    MemoryType,
    MemoryItem,
)
from .proactive_recommender import (
    ProactiveRecommender,
    RecommendationContext,
    RecommendationType,
)
from .task_parser import (
    TaskParserAgent,
    TaskIntent,
    TaskParameter,
    TaskPriority,
)
from .personalized_report import (
    PersonalizedReportGenerator,
    ReportTemplate,
    ReportStyle,
)
from .report_quality import (
    ReportQualityEvaluator,
    QualityDimension,
    QualityScore,
)
from .dynamic_pricing import (
    DynamicPricingAgent,
    PricingFactor,
    PriceAdjustment,
)
from .agent_health_monitor import (
    AgentHealthMonitor,
    HealthMetric,
    HealthStatus,
    AlertLevel,
)
from .task_flow_engine import (
    CrossDepartmentTaskFlowEngine,
    TaskFlow,
    FlowNode,
    FlowStatus,
)
from .experience_replay import (
    BusinessExperienceReplay,
    BusinessExperience,
    ExperiencePriority,
)
from .kpi_monitor import (
    BusinessKPIMonitor,
    KPIType,
    KPITarget,
    KPIMetric,
)

__all__ = [
    "IntentRecognizer",
    "UserIntent",
    "IntentCategory",
    "EmotionType",
    "DialogueStrategyEngine",
    "UserProfile",
    "DialogueStyle",
    "StrategyType",
    "SessionMemoryManager",
    "MemoryType",
    "MemoryItem",
    "ProactiveRecommender",
    "RecommendationContext",
    "RecommendationType",
    "TaskParserAgent",
    "TaskIntent",
    "TaskParameter",
    "TaskPriority",
    "PersonalizedReportGenerator",
    "ReportTemplate",
    "ReportStyle",
    "ReportQualityEvaluator",
    "QualityDimension",
    "QualityScore",
    "DynamicPricingAgent",
    "PricingFactor",
    "PriceAdjustment",
    "AgentHealthMonitor",
    "HealthMetric",
    "HealthStatus",
    "AlertLevel",
    "CrossDepartmentTaskFlowEngine",
    "TaskFlow",
    "FlowNode",
    "FlowStatus",
    "BusinessExperienceReplay",
    "BusinessExperience",
    "ExperiencePriority",
    "BusinessKPIMonitor",
    "KPIType",
    "KPITarget",
    "KPIMetric",
]
