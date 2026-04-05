"""
智能体模块
提供消息总线、基础代理类和示例代理
"""

from .message import AgentMessage, MessageType
from .bus import MessageBus
from .base import BaseAgent
from .scheduler import AgentScheduler
from .requirement import RequirementAgent
from .collector import CollectorAgent
from .analyst import AnalystAgent
from .supervisor import SupervisorAgent, SubTask
from .memory_agent import MemoryEnabledAgent
from .intelligent_analyst import IntelligentAnalystAgent
from .report_agent import ReportAgent
from .dialogue_agents import (
    InputProcessorAgent,
    DialogueSupervisorAgent
)
from .learning_agent import LearningAgent, PolicyNetwork, ValueNetwork
from .experience_collector import (
    ExperienceCollector,
    Experience,
    State,
    Action,
    Reward,
    experience_collector
)
# from .ppo_trainer import PPOTrainer, PPOConfig, MultiAgentPPOTrainer
from .reflection_module import ReflectionModule, reflection_module
from .learning_engine import LearningEngine, learning_engine
from .performance_monitor import PerformanceMonitor, performance_monitor
from .dudu_agent import (
    DuduAgent,
    DuduManager,
    dudu_manager,
    EmotionType,
    ActionType,
    EventType,
    EmotionState,
    DuduLevel,
    DuduCostume,
    EmotionEngine,
    DuduQuoteEngine
)

__all__ = [
    "AgentMessage",
    "MessageType",
    "MessageBus",
    "BaseAgent",
    "AgentScheduler",
    "RequirementAgent",
    "CollectorAgent",
    "AnalystAgent",
    "SupervisorAgent",
    "SubTask",
    "MemoryEnabledAgent",
    "IntelligentAnalystAgent",
    "ReportAgent",
    "InputProcessorAgent",
    "DialogueSupervisorAgent",
    "LearningAgent",
    "PolicyNetwork",
    "ValueNetwork",
    "ExperienceCollector",
    "Experience",
    "State",
    "Action",
    "Reward",
    "experience_collector",
    "ReflectionModule",
    "reflection_module",
    "LearningEngine",
    "learning_engine",
    "PerformanceMonitor",
    "performance_monitor",
    "DuduAgent",
    "DuduManager",
    "dudu_manager",
    "EmotionType",
    "ActionType",
    "EventType",
    "EmotionState",
    "DuduLevel",
    "DuduCostume",
    "EmotionEngine",
    "DuduQuoteEngine"
]
