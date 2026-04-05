# -*- coding: utf-8 -*-
"""
仪表盘功能诊断与重构服务模块

包含6个阶段的诊断与重构功能:
- Phase 1: 环境与依赖检查 (提示词1-3)
- Phase 2: 接口联调与数据流验证 (提示词4-6)
- Phase 3: 功能模块拆解与单元测试 (提示词7-9)
- Phase 4: 错误定位与日志分析 (提示词10-12)
- Phase 5: 代码重构与优化 (提示词13-15)
- Phase 6: 测试与部署验证 (提示词16-22)
"""

from .environment_diagnostic import (
    EnvironmentChecker,
    BackendStartupDiagnostics,
    FrontendBuildChecker,
    run_dashboard_environment_check,
    generate_environment_report
)

from .interface_diagnostic import (
    ApiConnectivityTester,
    DataIntegrityValidator,
    CachePreloadTester,
    run_interface_diagnostic,
    generate_interface_report
)

from .module_diagnostic import (
    StatisticsModule,
    TaskListModule,
    MemoryTrendModule,
    ModuleUnitTests,
    PerformanceAnalyzer,
    run_module_tests
)

from .error_diagnostic import (
    DetailedLogger,
    UserBehaviorSimulator,
    ExceptionSimulator,
    DegradationStrategy,
    run_error_diagnostic
)

from .refactor_optimizer import (
    BaseService,
    BaseDAO,
    StatisticsService,
    TaskService,
    QueryOptimizer,
    FrontendOptimizer,
    run_refactor_analysis
)

from .testing_deployment import (
    TestEnvironmentBuilder,
    E2ETestRunner,
    StressTester,
    DeploymentChecker,
    CanaryDeployment,
    FixReportGenerator,
    DocumentationUpdater,
    run_full_deployment_verification
)


__all__ = [
    "EnvironmentChecker",
    "BackendStartupDiagnostics",
    "FrontendBuildChecker",
    "run_dashboard_environment_check",
    "generate_environment_report",
    "ApiConnectivityTester",
    "DataIntegrityValidator",
    "CachePreloadTester",
    "run_interface_diagnostic",
    "generate_interface_report",
    "StatisticsModule",
    "TaskListModule",
    "MemoryTrendModule",
    "ModuleUnitTests",
    "PerformanceAnalyzer",
    "run_module_tests",
    "DetailedLogger",
    "UserBehaviorSimulator",
    "ExceptionSimulator",
    "DegradationStrategy",
    "run_error_diagnostic",
    "BaseService",
    "BaseDAO",
    "StatisticsService",
    "TaskService",
    "QueryOptimizer",
    "FrontendOptimizer",
    "run_refactor_analysis",
    "TestEnvironmentBuilder",
    "E2ETestRunner",
    "StressTester",
    "DeploymentChecker",
    "CanaryDeployment",
    "FixReportGenerator",
    "DocumentationUpdater",
    "run_full_deployment_verification"
]
