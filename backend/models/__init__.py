"""
房都督AI - 数据模型包
整合 models.py 和 models/ 目录的内容
"""
import sys
from pathlib import Path

_parent_models_path = Path(__file__).parent.parent / "models.py"
if _parent_models_path.exists():
    import importlib.util
    _spec = importlib.util.spec_from_file_location("_parent_models", _parent_models_path)
    _parent_models = importlib.util.module_from_spec(_spec)
    sys.modules["_parent_models"] = _parent_models
    _spec.loader.exec_module(_parent_models)
    
    # Auth models
    TokenData = _parent_models.TokenData
    Token = _parent_models.Token
    UserCreate = _parent_models.UserCreate
    UserLogin = _parent_models.UserLogin
    UserResponse = _parent_models.UserResponse
    UserUpdate = _parent_models.UserUpdate
    PasswordChange = _parent_models.PasswordChange
    UserStats = _parent_models.UserStats
    UserRole = _parent_models.UserRole
    PermissionType = _parent_models.PermissionType
    DEFAULT_ROLE_PERMISSIONS = _parent_models.DEFAULT_ROLE_PERMISSIONS
    
    # Report models
    ReportStatus = _parent_models.ReportStatus
    ReportSection = _parent_models.ReportSection
    ReportData = _parent_models.ReportData
    ReportCreate = _parent_models.ReportCreate
    ReportResponse = _parent_models.ReportResponse
    ReportListResponse = _parent_models.ReportListResponse
    ReportUpdateRequest = _parent_models.ReportUpdateRequest
    ReportStatusTransition = _parent_models.ReportStatusTransition
    ReportInteraction = _parent_models.ReportInteraction
    ReportVersion = _parent_models.ReportVersion
    
    # Location models
    UserLocationCreate = _parent_models.UserLocationCreate
    UserLocationResponse = _parent_models.UserLocationResponse
    UserLocationListResponse = _parent_models.UserLocationListResponse
    LocationStatsResponse = _parent_models.LocationStatsResponse
    MapDataPoint = _parent_models.MapDataPoint
    MapBounds = _parent_models.MapBounds
    
    # Task models
    TaskCreate = _parent_models.TaskCreate
    BatchTaskCreate = _parent_models.BatchTaskCreate
    TaskResponse = _parent_models.TaskResponse
    BatchTaskResponse = _parent_models.BatchTaskResponse
    TaskListResponse = _parent_models.TaskListResponse
    TaskStepResponse = _parent_models.TaskStepResponse
    TaskMessagesResponse = _parent_models.TaskMessagesResponse
    
    # Analysis models
    AnalyzeRequest = _parent_models.AnalyzeRequest
    AnalyzeResponse = _parent_models.AnalyzeResponse
    TaskStatusResponse = _parent_models.TaskStatusResponse
    MessageResponse = _parent_models.MessageResponse
    ErrorResponse = _parent_models.ErrorResponse
    IntegralLogResponse = _parent_models.IntegralLogResponse
    IntegralLogListResponse = _parent_models.IntegralLogListResponse
    UserIntegralResponse = _parent_models.UserIntegralResponse
    IntegralPackage = _parent_models.IntegralPackage
    MembershipPlan = _parent_models.MembershipPlan
    AdminAdjustIntegralRequest = _parent_models.AdminAdjustIntegralRequest
    IntegralSummaryResponse = _parent_models.IntegralSummaryResponse
    
    # Other models
    ExtractedEntityModel = _parent_models.ExtractedEntityModel
    ParsedRequirementModel = _parent_models.ParsedRequirementModel
    RequirementInference = _parent_models.RequirementInference
    AgentSummary = _parent_models.AgentSummary
    MascotPreferences = _parent_models.MascotPreferences
    UserPreferences = _parent_models.UserPreferences
    UserPreferencesUpdate = _parent_models.UserPreferencesUpdate
    LocationSource = _parent_models.LocationSource

from .mingpan_case import (
    PatternType,
    WealthType,
    MarriageLevel,
    CareerStage,
    RelationType,
    ExecutionLevel,
    DimensionAnalysis,
    CaseOutcome,
    CaseFull,
    CaseBase,
    CaseCreateRequest,
    CaseSearchRequest,
    CaseStatistics,
    SAMPLE_CASES,
    CASE_TABLE_SCHEMA,
)

    
__all__ = [
    # Auth models
    "TokenData",
    "Token",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "PasswordChange",
    "UserStats",
    "UserRole",
    "PermissionType",
    "DEFAULT_ROLE_PERMISSIONS",
    # Report models
    "ReportStatus",
    "ReportSection",
    "ReportData",
    "ReportCreate",
    "ReportResponse",
    "ReportListResponse",
    "ReportUpdateRequest",
    "ReportStatusTransition",
    "ReportInteraction",
    "ReportVersion",
    # Location models
    "UserLocationCreate",
    "UserLocationResponse",
    "UserLocationListResponse",
    "LocationStatsResponse",
    "MapDataPoint",
    "MapBounds",
    # Task models
    "TaskCreate",
    "BatchTaskCreate",
    "TaskResponse",
    "BatchTaskResponse",
    "TaskListResponse",
    "TaskStepResponse",
    "TaskMessagesResponse",
    # Analysis models
    "AnalyzeRequest",
    "AnalyzeResponse",
    "TaskStatusResponse",
    "MessageResponse",
    "ErrorResponse",
    "IntegralLogResponse",
    "IntegralLogListResponse",
    "UserIntegralResponse",
    "IntegralPackage",
    "MembershipPlan",
    "AdminAdjustIntegralRequest",
    "IntegralSummaryResponse",
    # Other models
    "ExtractedEntityModel",
    "ParsedRequirementModel",
    "RequirementInference",
    "AgentSummary",
    "MascotPreferences",
    "UserPreferences",
    "UserPreferencesUpdate",
    "LocationSource",
    # Mingpan models
    "PatternType",
    "WealthType",
    "MarriageLevel",
    "CareerStage",
    "RelationType",
    "ExecutionLevel",
    "DimensionAnalysis",
    "CaseOutcome",
    "CaseFull",
    "CaseBase",
    "CaseCreateRequest",
    "CaseSearchRequest",
    "CaseStatistics",
    "SAMPLE_CASES",
    "CASE_TABLE_SCHEMA",
]
