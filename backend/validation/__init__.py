"""
验证和灰度发布模块
Validation and Gray Release Module

提供模型验证、灰度发布、A/B测试和回滚功能
"""

from .model_validator import (
    ModelValidator,
    ModelMetrics,
    ModelVersion,
    ValidationResult,
    ValidationStatus,
    ValidationSeverity,
    ValidationRule,
    get_validator,
)

from .gray_release import (
    GrayReleaseController,
    ReleaseStatus,
    ReleaseStage,
    StageConfig,
    ReleaseMetrics,
    get_controller,
)

from .ab_testing import (
    ABTestingFramework,
    ExperimentStatus,
    Variant,
    VariantType,
    ExperimentMetrics,
    StatisticalResult,
    get_framework,
)

from .rollback_manager import (
    RollbackManager,
    RollbackStatus,
    RollbackTrigger,
    VersionSnapshot,
    RollbackRecord,
    get_rollback_manager,
)

__all__ = [
    "ModelValidator",
    "ModelMetrics",
    "ModelVersion",
    "ValidationResult",
    "ValidationStatus",
    "ValidationSeverity",
    "ValidationRule",
    "get_validator",
    "GrayReleaseController",
    "ReleaseStatus",
    "ReleaseStage",
    "StageConfig",
    "ReleaseMetrics",
    "get_controller",
    "ABTestingFramework",
    "ExperimentStatus",
    "Variant",
    "VariantType",
    "ExperimentMetrics",
    "StatisticalResult",
    "get_framework",
    "RollbackManager",
    "RollbackStatus",
    "RollbackTrigger",
    "VersionSnapshot",
    "RollbackRecord",
    "get_rollback_manager",
]
