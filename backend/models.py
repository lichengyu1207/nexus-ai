"""
Pydantic模型定义
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReportStatus(str, Enum):
    """报告状态枚举"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ReportSection(BaseModel):
    """报告章节模型"""
    id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(default="", description="章节内容")
    order: int = Field(default=0, description="排序")
    is_generating: bool = Field(default=False, description="是否正在生成")
    generated_at: Optional[str] = Field(None, description="生成时间")


class ReportData(BaseModel):
    """报告数据模型"""
    executive_summary: Optional[str] = Field(None, description="执行摘要")
    core_findings: Optional[Dict[str, Any]] = Field(None, description="核心发现")
    detailed_analysis: Optional[Dict[str, Any]] = Field(None, description="详细分析")
    investment_advice: Optional[Dict[str, Any]] = Field(None, description="投资建议")
    risk_warnings: Optional[List[str]] = Field(None, description="风险提示")
    data_sources: Optional[List[Dict[str, str]]] = Field(None, description="数据来源")
    charts: Optional[List[Dict[str, Any]]] = Field(None, description="图表数据")
    sections: Optional[List[ReportSection]] = Field(None, description="章节列表")


class ReportCreate(BaseModel):
    """创建报告请求模型"""
    task_id: str = Field(..., description="任务ID")


class ReportResponse(BaseModel):
    """报告响应模型"""
    id: str = Field(..., description="报告ID")
    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    status: str = Field(..., description="报告状态")
    content: Optional[Dict[str, Any]] = Field(None, description="报告内容")
    summary: Optional[str] = Field(None, description="报告摘要")
    version: int = Field(default=1, description="版本号")
    progress: int = Field(default=0, description="生成进度")
    current_section: Optional[str] = Field(None, description="当前生成章节")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    completed_at: Optional[str] = Field(None, description="完成时间")


class ReportListResponse(BaseModel):
    """报告列表响应模型"""
    reports: List[ReportResponse]
    total: int
    limit: int
    offset: int


class ReportUpdateRequest(BaseModel):
    """报告更新请求模型"""
    status: Optional[str] = Field(None, description="新状态")
    content: Optional[Dict[str, Any]] = Field(None, description="报告内容")
    summary: Optional[str] = Field(None, description="报告摘要")
    progress: Optional[int] = Field(None, description="生成进度")
    current_section: Optional[str] = Field(None, description="当前生成章节")
    error_message: Optional[str] = Field(None, description="错误信息")


class ReportStatusTransition(BaseModel):
    """报告状态迁移请求"""
    new_status: ReportStatus = Field(..., description="新状态")
    reason: Optional[str] = Field(None, description="状态变更原因")


class ReportInteraction(BaseModel):
    """报告交互模型"""
    report_id: str = Field(..., description="报告ID")
    user_id: str = Field(..., description="用户ID")
    interaction_type: str = Field(..., description="交互类型: like/bookmark/share/comment")
    content: Optional[str] = Field(None, description="评论内容")


class ReportVersion(BaseModel):
    """报告版本模型"""
    version: int = Field(..., description="版本号")
    content: Dict[str, Any] = Field(..., description="版本内容")
    created_at: str = Field(..., description="创建时间")
    change_summary: Optional[str] = Field(None, description="变更摘要")


class UserCreate(BaseModel):
    """用户注册请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="用户全名")
    address: Optional[str] = Field(None, max_length=500, description="用户地址（可选）")
    source: Optional[str] = Field(None, description="客观来源（首次触点归因）")
    referred_by: Optional[str] = Field(None, description="主观来源（用户自述）")
    referred_by_other: Optional[str] = Field(None, description="主观来源-其他说明")
    privacy_version_id: Optional[str] = Field(None, description="同意的隐私政策版本ID")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        
        # 检查是否为常见弱密码
        weak_passwords = [
            '123456', 'password', '111111', 'qwerty', 'abc123', 
            '123456789', '12345678', '1234567', '12345', '1234567890',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            '666666', '888888', '000000', '123123', '654321'
        ]
        if v.lower() in weak_passwords:
            raise ValueError('密码过于简单，请使用更复杂的密码')
        
        # 检查是否包含数字和字母
        has_digit = any(c.isdigit() for c in v)
        has_alpha = any(c.isalpha() for c in v)
        
        if not has_digit or not has_alpha:
            raise ValueError('密码必须同时包含字母和数字')
        
        return v


class UserLogin(BaseModel):
    """用户登录请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: Optional[int] = Field(None, description="过期时间(秒)")


class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    username: Optional[str] = Field(None, description="用户名")
    full_name: Optional[str] = Field(None, description="用户全名")
    role: str = Field(default="user", description="用户角色")
    is_admin: bool = Field(default=False, description="是否管理员")
    permissions: Optional[Dict[str, bool]] = Field(default=None, description="细粒度权限")
    integral: int = Field(default=3, description="积分余额")
    membership_level: str = Field(default="free", description="会员等级")
    membership_expires: Optional[str] = Field(None, description="会员到期时间")
    source: Optional[str] = Field(None, description="客观来源（首次触点归因）")
    source_name: Optional[str] = Field(None, description="来源名称")
    bonus_label: Optional[str] = Field(None, description="福利标签")
    referred_by: Optional[str] = Field(None, description="主观来源（用户自述）")
    referred_by_other: Optional[str] = Field(None, description="主观来源-其他说明")
    created_at: Optional[str] = Field(None, description="创建时间")


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class PermissionType(str, Enum):
    """权限类型枚举"""
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_VIEW_LOGS = "can_view_logs"
    CAN_MANAGE_SYSTEM = "can_manage_system"
    CAN_MANAGE_TEAMS = "can_manage_teams"
    CAN_EXPORT_DATA = "can_export_data"
    CAN_VIEW_ALL_REPORTS = "can_view_all_reports"


DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "user": [],
    "admin": [
        "can_manage_users",
        "can_view_logs",
        "can_manage_teams",
        "can_export_data",
    ],
    "super_admin": [
        "can_manage_users",
        "can_view_logs",
        "can_manage_system",
        "can_manage_teams",
        "can_export_data",
        "can_view_all_reports",
    ],
}


class UserUpdate(BaseModel):
    """用户更新请求模型"""
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=50)


class PasswordChange(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class UserStats(BaseModel):
    """用户统计模型"""
    total_tasks: int = Field(default=0, description="总任务数")
    completed_tasks: int = Field(default=0, description="已完成任务数")
    running_tasks: int = Field(default=0, description="进行中任务数")
    failed_tasks: int = Field(default=0, description="失败任务数")


class MascotPreferences(BaseModel):
    """吉祥物偏好设置"""
    enabled: bool = Field(default=True, description="是否启用吉祥物")
    display_mode: str = Field(default="all", description="显示模式: all(所有场景), empty(仅空状态)")
    show_bubble: bool = Field(default=True, description="是否显示气泡")
    show_onboarding: bool = Field(default=True, description="是否显示新手引导")


class UserPreferences(BaseModel):
    """用户偏好设置"""
    mascot: MascotPreferences = Field(default_factory=MascotPreferences, description="吉祥物设置")
    theme: str = Field(default="system", description="主题: light, dark, system")
    language: str = Field(default="zh-CN", description="语言")
    notifications: Dict[str, bool] = Field(default_factory=lambda: {
        "email": True,
        "push": True,
        "task_complete": True,
    }, description="通知设置")


class UserPreferencesUpdate(BaseModel):
    """用户偏好更新请求"""
    mascot: Optional[MascotPreferences] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications: Optional[Dict[str, bool]] = None


class LocationSource(str, Enum):
    """位置来源枚举"""
    REGISTRATION = "registration"
    INTEREST = "interest"
    REPORT = "report"


class UserLocationCreate(BaseModel):
    """用户位置创建请求模型"""
    source: str = Field(..., description="位置来源: registration, interest, report")
    address: str = Field(..., min_length=1, max_length=500, description="原始地址")
    country: Optional[str] = Field(None, max_length=100, description="国家")
    province: Optional[str] = Field(None, max_length=100, description="省份")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    district: Optional[str] = Field(None, max_length=100, description="区县")
    street: Optional[str] = Field(None, max_length=200, description="街道")
    community: Optional[str] = Field(None, max_length=200, description="小区名称")
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")


class UserLocationResponse(BaseModel):
    """用户位置响应模型"""
    id: str
    user_id: str
    source: str
    address: str
    country: Optional[str]
    province: Optional[str]
    city: Optional[str]
    district: Optional[str]
    street: Optional[str]
    community: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    geocoded_at: Optional[str]
    created_at: Optional[str]


class UserLocationListResponse(BaseModel):
    """用户位置列表响应"""
    locations: List[UserLocationResponse]
    total: int


class LocationStatsResponse(BaseModel):
    """位置统计响应"""
    total: int
    geocoded: int
    by_source: Dict[str, int]
    by_province: List[Dict[str, Any]]
    by_city: List[Dict[str, Any]]


class MapDataPoint(BaseModel):
    """地图数据点"""
    longitude: float
    latitude: float
    city: Optional[str]
    district: Optional[str]
    community: Optional[str]


class MapBounds(BaseModel):
    """地图边界"""
    north: float
    south: float
    east: float
    west: float


class ExtractedEntityModel(BaseModel):
    """提取的实体模型"""
    value: Any
    confidence: float = Field(ge=0, le=1)
    source: str = Field(description="来源: explicit/inferred/default")


class ParsedRequirementModel(BaseModel):
    """解析后的需求模型"""
    raw_query: str = Field(..., description="原始查询")
    
    city: Optional[ExtractedEntityModel] = None
    district: Optional[ExtractedEntityModel] = None
    community: Optional[ExtractedEntityModel] = None
    
    room_count: Optional[ExtractedEntityModel] = None
    hall_count: Optional[ExtractedEntityModel] = None
    
    area_min: Optional[ExtractedEntityModel] = None
    area_max: Optional[ExtractedEntityModel] = None
    
    price_min: Optional[ExtractedEntityModel] = None
    price_max: Optional[ExtractedEntityModel] = None
    
    age_min: Optional[ExtractedEntityModel] = None
    age_max: Optional[ExtractedEntityModel] = None
    
    orientation: Optional[ExtractedEntityModel] = None
    floor_type: Optional[ExtractedEntityModel] = None
    decoration: Optional[ExtractedEntityModel] = None
    
    is_school_district: Optional[ExtractedEntityModel] = None
    is_near_subway: Optional[ExtractedEntityModel] = None
    
    special_requirements: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)


class RequirementInference(BaseModel):
    """需求推断模型"""
    field_name: str
    inferred_value: Any
    confidence: float
    reasoning: str
    data_source: str


class TaskCreate(BaseModel):
    """任务创建请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="用户查询")
    style: Optional[str] = Field("balanced", description="分析风格: conservative/balanced/aggressive")


class BatchTaskCreate(BaseModel):
    """批量任务创建请求模型"""
    queries: List[str] = Field(..., min_items=1, max_items=5, description="查询列表（最多5个）")
    style: Optional[str] = Field("balanced", description="分析风格: conservative/balanced/aggressive")


class AgentSummary(BaseModel):
    """代理摘要模型"""
    name: str = Field(..., description="代理名称")
    status: str = Field(..., description="代理状态")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="用户查询")
    status: str = Field(..., description="任务状态")
    progress: int = Field(default=0, description="进度百分比")
    style: str = Field(default="balanced", description="分析风格")
    created_at: Optional[str] = Field(None, description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    agents: Optional[List[AgentSummary]] = Field(default=[], description="代理摘要")


class BatchTaskResponse(BaseModel):
    """批量任务创建响应模型"""
    tasks: List[TaskResponse] = Field(..., description="创建的任务列表")
    total: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    integral_consumed: int = Field(..., description="消耗积分")


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[TaskResponse]
    total: int
    limit: int
    offset: int


class TaskStepResponse(BaseModel):
    """任务步骤响应模型"""
    id: str
    task_id: str
    agent_name: str
    step_name: str
    step_order: int
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskMessagesResponse(BaseModel):
    """任务消息响应模型"""
    task_id: str
    messages: List[dict]
    total: int


class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="用户查询")
    style: Optional[str] = Field("balanced", description="分析风格")


class AnalyzeResponse(BaseModel):
    """分析响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="消息")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    query: str
    result: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: str
    task_id: str
    sender: str
    recipient: Optional[str]
    type: str
    content: dict
    in_reply_to: Optional[str]
    timestamp: str


class ErrorResponse(BaseModel):
    """错误响应模型"""
    detail: str = Field(..., description="错误详情")
    code: Optional[str] = Field(None, description="错误代码")


class IntegralLogResponse(BaseModel):
    """积分变动日志响应模型"""
    id: str = Field(..., description="日志ID")
    user_id: str = Field(..., description="用户ID")
    change: int = Field(..., description="变动数量（正数增加，负数消耗）")
    balance_after: int = Field(..., description="变动后余额")
    reason: str = Field(..., description="变动原因")
    admin_note: Optional[str] = Field(None, description="管理员备注")
    admin_id: Optional[str] = Field(None, description="管理员ID")
    created_at: Optional[str] = Field(None, description="创建时间")


class IntegralLogListResponse(BaseModel):
    """积分变动日志列表响应"""
    logs: List[IntegralLogResponse]
    total: int
    limit: int
    offset: int


class UserIntegralResponse(BaseModel):
    """用户积分信息响应"""
    integral: int = Field(..., description="当前积分余额")
    membership_level: str = Field(default="free", description="会员等级")
    membership_expires: Optional[str] = Field(None, description="会员到期时间")
    is_member: bool = Field(default=False, description="是否为有效会员")
    recent_logs: List[IntegralLogResponse] = Field(default=[], description="最近积分变动")
    source: Optional[str] = Field(None, description="用户来源类型")
    source_name: Optional[str] = Field(None, description="来源名称")
    bonus_label: Optional[str] = Field(None, description="福利标签（如：粉丝专属福利）")
    initial_integral: Optional[int] = Field(None, description="初始赠送积分")


class AdminAdjustIntegralRequest(BaseModel):
    """管理员调整积分请求"""
    user_id: str = Field(..., description="目标用户ID")
    change: int = Field(..., description="变动数量（正数增加，负数减少）")
    reason: str = Field(..., min_length=1, max_length=500, description="调整原因")
    admin_note: Optional[str] = Field(None, max_length=500, description="管理员备注")


class IntegralSummaryResponse(BaseModel):
    """积分统计响应"""
    total_users: int = Field(..., description="总用户数")
    total_integral: int = Field(..., description="总发放积分")
    total_consumed: int = Field(..., description="总消耗积分")
    total_admin_added: int = Field(..., description="管理员充值积分")
    total_register: int = Field(..., description="注册赠送积分")


class IntegralPackage(BaseModel):
    """积分套餐模型"""
    id: str = Field(..., description="套餐ID")
    name: str = Field(..., description="套餐名称")
    integral: int = Field(..., description="积分数量")
    price: float = Field(..., description="价格（元）")
    unit_price: float = Field(..., description="单价（元/积分）")
    description: str = Field(..., description="套餐描述")
    is_popular: bool = Field(default=False, description="是否为热门推荐")


class MembershipPlan(BaseModel):
    """会员套餐模型"""
    id: str = Field(..., description="套餐ID")
    name: str = Field(..., description="套餐名称")
    price: float = Field(..., description="价格（元/月）")
    duration_months: int = Field(..., description="有效月数")
    description: str = Field(..., description="套餐描述")
    features: List[str] = Field(default=[], description="套餐特性")
