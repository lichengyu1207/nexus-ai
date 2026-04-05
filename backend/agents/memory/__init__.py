"""
记忆系统免疫模块
Memory System Immunity Module

实现记忆污染检测、置信度管理、对抗性净化、攻击模式识别等功能
"""

from .memory_immunity import (
    MemoryPollutionDetector,
    SourceReputationManager,
    CrossValidator,
    ConfidenceManager,
    AdversarialMemoryCleaner,
    MemoryIsolationZone,
    MemoryImmunitySystem,
    MemoryStatus,
    SourceType,
    ValidatedMemory,
)

from .irl_defense import (
    IRLDefense,
    AttackTrajectory,
    RewardFunctionInference,
    DefenseStrategyOptimizer,
    AttackType,
    DefenseAction,
    GameResult,
    StateVector,
    ActionRecord,
    DefenseStrategy,
)

from .attack_pattern_recognizer import (
    AttackPatternRecognizer,
    AttackPatternLibrary,
    NovelAttackHandler,
    CollectiveDefenseCoordinator,
    AttackPattern,
    AttackEvent,
    AttackSeverity,
    AttackStatus,
)

from .pheromone_communication import (
    PheromoneField,
    PheromoneMessage,
    ThreatPheromone,
    PheromoneDecayManager,
    PheromoneType,
)

from .genetic_evolution import (
    GeneticEvolution,
    Chromosome,
    Population,
    SelectionStrategy,
    CrossoverOperator,
    MutationOperator,
    EvolutionTree,
    Gene,
    GeneType,
    SelectionMethod,
    CrossoverType,
    MutationType,
)

from .adversarial_tests import (
    AdversarialTestSuite,
    TestReport,
    TestCategory,
    TestResult,
)

memory_immunity_system = MemoryImmunitySystem()
irl_defense_system = IRLDefense()
attack_pattern_recognizer = AttackPatternRecognizer()
pheromone_field = None
genetic_evolution = GeneticEvolution()

__all__ = [
    "MemoryPollutionDetector",
    "SourceReputationManager",
    "CrossValidator",
    "ConfidenceManager",
    "AdversarialMemoryCleaner",
    "MemoryIsolationZone",
    "MemoryImmunitySystem",
    "MemoryStatus",
    "SourceType",
    "ValidatedMemory",
    "IRLDefense",
    "AttackTrajectory",
    "RewardFunctionInference",
    "DefenseStrategyOptimizer",
    "AttackType",
    "DefenseAction",
    "GameResult",
    "StateVector",
    "ActionRecord",
    "DefenseStrategy",
    "AttackPatternRecognizer",
    "AttackPatternLibrary",
    "NovelAttackHandler",
    "CollectiveDefenseCoordinator",
    "AttackPattern",
    "AttackEvent",
    "AttackSeverity",
    "AttackStatus",
    "PheromoneField",
    "PheromoneMessage",
    "ThreatPheromone",
    "PheromoneDecayManager",
    "PheromoneType",
    "GeneticEvolution",
    "Chromosome",
    "Population",
    "SelectionStrategy",
    "CrossoverOperator",
    "MutationOperator",
    "EvolutionTree",
    "Gene",
    "GeneType",
    "SelectionMethod",
    "CrossoverType",
    "MutationType",
    "AdversarialTestSuite",
    "TestReport",
    "TestCategory",
    "TestResult",
    "memory_immunity_system",
    "irl_defense_system",
    "attack_pattern_recognizer",
    "pheromone_field",
    "genetic_evolution",
]
