"""
防社会工程学智能体集群与蜂群系统
Social Engineering Defense Agent Cluster and Swarm System

该模块实现房都督平台的防社会工程学智能体集群，使智能体能够识别、防御并主动对抗
来自人类或AI的社会工程攻击。系统赋予智能体"防骗免疫力"，在多轮对话、跨平台交互中
精准识别伪装身份、诱导话术、情感操控，确保平台安全与用户信任。

核心能力：
- 提示注入防御：检测和防御提示注入攻击
- 身份验证：多因素身份验证和假冒检测
- 情感识别防御：识别情感操控并防御
- 多轮诱导检测：分析对话意图演化
- 行为基线：建立和维护正常行为模式
- 蜂群协同：分布式防御和情报共享
- 用户教育：实时防骗提示和知识库
"""

from .prompt_injection_detector import PromptInjectionDetectorAgent
from .input_sanitizer import InputSanitizerAgent
from .system_prompt_guard import SystemPromptGuardAgent
from .chain_of_thought_verifier import ChainOfThoughtVerifierAgent
from .prompt_attack_library import PromptAttackLibraryAgent

from .multi_factor_auth import MultiFactorAuthAgent
from .voice_print_recognition import VoicePrintRecognitionAgent
from .behavioral_biometrics import BehavioralBiometricsAgent
from .identity_trust_score import IdentityTrustScoreAgent
from .impersonation_detector import ImpersonationDetectorAgent

from .emotion_recognition import EmotionRecognitionAgent
from .urgency_verification import UrgencyVerificationAgent
from .fear_defense import FearDefenseAgent
from .sympathy_manipulation_defense import SympathyManipulationDefenseAgent

from .intent_evolution_detector import IntentEvolutionDetectorAgent
from .trust_building_analyzer import TrustBuildingAnalyzerAgent
from .context_pollution_detector import ContextPollutionDetectorAgent
from .conversation_pattern_anomaly import ConversationPatternAnomalyAgent

from .user_behavior_baseline import UserBehaviorBaselineAgent
from .agent_behavior_baseline import AgentBehaviorBaselineAgent
from .anomaly_aggregation import AnomalyAggregationAgent
from .attack_chain_reconstruction import AttackChainReconstructionAgent

from .attack_intel_sharing import AttackIntelSharingAgent
from .distributed_defense_consensus import DistributedDefenseConsensusAgent
from .swarm_learning_evolution import SwarmLearningEvolutionAgent
from .defense_situational_awareness import DefenseSituationalAwarenessAgent

from .anti_scam_alert import AntiScamAlertAgent
from .anti_scam_knowledge_base import AntiScamKnowledgeBaseAgent
from .user_report_handling import UserReportHandlingAgent
from .user_trust_feedback import UserTrustFeedbackAgent

from .defense_integration import DefenseIntegrationAgent
from .memory_defense_integration import MemoryDefenseIntegrationAgent
from .audit_defense_integration import AuditDefenseIntegrationAgent
from .multilingual_attack_detector import MultilingualAttackDetectorAgent

__all__ = [
    "PromptInjectionDetectorAgent",
    "InputSanitizerAgent",
    "SystemPromptGuardAgent",
    "ChainOfThoughtVerifierAgent",
    "PromptAttackLibraryAgent",
    "MultiFactorAuthAgent",
    "VoicePrintRecognitionAgent",
    "BehavioralBiometricsAgent",
    "IdentityTrustScoreAgent",
    "ImpersonationDetectorAgent",
    "EmotionRecognitionAgent",
    "UrgencyVerificationAgent",
    "FearDefenseAgent",
    "SympathyManipulationDefenseAgent",
    "IntentEvolutionDetectorAgent",
    "TrustBuildingAnalyzerAgent",
    "ContextPollutionDetectorAgent",
    "ConversationPatternAnomalyAgent",
    "UserBehaviorBaselineAgent",
    "AgentBehaviorBaselineAgent",
    "AnomalyAggregationAgent",
    "AttackChainReconstructionAgent",
    "AttackIntelSharingAgent",
    "DistributedDefenseConsensusAgent",
    "SwarmLearningEvolutionAgent",
    "DefenseSituationalAwarenessAgent",
    "AntiScamAlertAgent",
    "AntiScamKnowledgeBaseAgent",
    "UserReportHandlingAgent",
    "UserTrustFeedbackAgent",
    "DefenseIntegrationAgent",
    "MemoryDefenseIntegrationAgent",
    "AuditDefenseIntegrationAgent",
    "MultilingualAttackDetectorAgent",
]

CLUSTER_INFO = {
    "prompt_injection_defense": {
        "name": "提示注入防御智能体集群",
        "agents": [
            "PromptInjectionDetectorAgent",
            "InputSanitizerAgent",
            "SystemPromptGuardAgent",
            "ChainOfThoughtVerifierAgent",
            "PromptAttackLibraryAgent",
            "MultilingualAttackDetectorAgent",
        ],
        "count": 6,
    },
    "identity_verification": {
        "name": "身份验证智能体集群",
        "agents": [
            "MultiFactorAuthAgent",
            "VoicePrintRecognitionAgent",
            "BehavioralBiometricsAgent",
            "IdentityTrustScoreAgent",
            "ImpersonationDetectorAgent",
        ],
        "count": 5,
    },
    "emotion_defense": {
        "name": "情感识别与操控防御智能体集群",
        "agents": [
            "EmotionRecognitionAgent",
            "UrgencyVerificationAgent",
            "FearDefenseAgent",
            "SympathyManipulationDefenseAgent",
        ],
        "count": 4,
    },
    "multi_turn_induction": {
        "name": "多轮诱导检测智能体集群",
        "agents": [
            "IntentEvolutionDetectorAgent",
            "TrustBuildingAnalyzerAgent",
            "ContextPollutionDetectorAgent",
            "ConversationPatternAnomalyAgent",
        ],
        "count": 4,
    },
    "behavior_baseline": {
        "name": "行为基线智能体集群",
        "agents": [
            "UserBehaviorBaselineAgent",
            "AgentBehaviorBaselineAgent",
            "AnomalyAggregationAgent",
            "AttackChainReconstructionAgent",
        ],
        "count": 4,
    },
    "swarm_defense": {
        "name": "蜂群协同防御智能体集群",
        "agents": [
            "AttackIntelSharingAgent",
            "DistributedDefenseConsensusAgent",
            "SwarmLearningEvolutionAgent",
            "DefenseSituationalAwarenessAgent",
        ],
        "count": 4,
    },
    "user_education": {
        "name": "用户教育与反馈智能体集群",
        "agents": [
            "AntiScamAlertAgent",
            "AntiScamKnowledgeBaseAgent",
            "UserReportHandlingAgent",
            "UserTrustFeedbackAgent",
        ],
        "count": 4,
    },
    "system_integration": {
        "name": "系统集成智能体集群",
        "agents": [
            "DefenseIntegrationAgent",
            "MemoryDefenseIntegrationAgent",
            "AuditDefenseIntegrationAgent",
        ],
        "count": 3,
    },
}

TOTAL_AGENTS = 34
