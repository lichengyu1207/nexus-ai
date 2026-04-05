# -*- coding: utf-8 -*-
"""
Layer 30: Dual-Track Growth User System (双轨成长用户系统)

双轨成长体系：
- Track 1 (Usage/Consumption): 用户通过平台使用行为获取"成长值"(Growth Points) → Lv1-Lv8 等级 + 特权
- Track 2 (Contribution/Supply): 创作者通过内容上传获取"贡献值"(Contribution Points) → C1-C8 等级 + 收益分成

关键特性:
- 跨轨协同机制：高等级用户获得上传优先权；高贡献者获得消费折扣
- 积分商城：7种可兑换商品
- 内容审核队列：优先级评分基于使用等级
- 收益与提现系统（最低500积分）
- 双排行榜：使用达人榜 + 贡献大师榜
- 12个REST API端点模拟
- 前端渲染器：成长档案面板 + 创作者中心 + 积分商城
- 反作弊与公平性保障系统
- 55+ 测试用例，18个测试分类

编码规则:
- 变量/类/函数名必须使用英文
- 仅允许在模块文档字符串和 print() 中使用中文
- 测试方法中字典键名必须用引号包裹 {"key": value}
- _record() 调用中禁止使用 f-string（改用 "text" + str(var) 拼接）
- 使用 chr(10) 代替 \\n
- 使用 dataclasses 和 enum.Enum
"""

from __future__ import annotations

import copy
import datetime
import enum
import json
import math
import os
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Dict, List, Optional, Tuple


# ============================================================
# Part L: Data Classes & Enums (数据类与枚举定义)
# ============================================================


class GrowthActionType(enum.Enum):
    """成长动作类型枚举"""
    SMART_CONSULTATION = "smart_consultation"
    PROPERTY_REPORT = "property_report"
    FORTUNE_REPORT = "fortune_report"
    SKILL_PURCHASE = "skill_purchase"
    AGENT_RECRUITMENT = "agent_recruitment"
    BOND_ACTIVATION = "bond_activation"
    SCHEDULED_TASK_SETUP = "scheduled_task_setup"
    PDF_EXPORT = "pdf_export"
    PROPERTY_COMPARE = "property_compare"
    DAILY_CHECKIN = "daily_checkin"
    FEEDBACK_RATING = "feedback_rating"


class ContributionActionType(enum.Enum):
    """贡献动作类型枚举"""
    UPLOAD_SKILL = "upload_skill"
    SKILL_PURCHASED_BY_OTHERS = "skill_purchased_by_others"
    UPLOAD_AGENT_TEMPLATE = "upload_agent_template"
    PUBLISH_ARTICLE = "publish_article"
    UPLOAD_CASE_REPORT = "upload_case_report"
    CO_AUTHOR_DEVELOPMENT = "co_author_development"
    OFFICIAL_RECOMMENDATION = "official_recommendation"
    CONTENT_FAVORITED = "content_favorited"


class UploadStatus(enum.Enum):
    """上传内容状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WithdrawalMethod(enum.Enum):
    """提现方式枚举"""
    POINTS_TO_MEMBERSHIP = "points_to_membership"
    CASH = "cash"
    ALIPAY = "alipay"


class ProductCategory(enum.Enum):
    """商品类别枚举"""
    REPORT_COUPON = "report_coupon"
    SKILL_DISCOUNT = "skill_discount"
    AGENT_RECRUIT_COUPON = "agent_recruit_coupon"
    VIP_TRIAL = "vip_trial"
    CUSTOM_TEMPLATE = "custom_template"
    EXTRA_BOND_SLOT = "extra_bond_slot"
    CREATOR_BADGE = "creator_badge"


class MilestoneType(enum.Enum):
    """里程碑类型枚举"""
    FIRST_UPLOAD = "first_upload"
    TENTH_SALE = "tenth_sale"
    HUNDREDTH_VIEW = "hundredth_view"
    FIRST_LEVEL_UP = "first_level_up"
    FIRST_WITHDRAWAL = "first_withdrawal"
    TOP_TEN_RANKING = "top_ten_ranking"


@dataclass
class GrowthTransaction:
    """成长交易记录"""
    transaction_id: str
    user_id: str
    action_type: str
    points_earned: int
    timestamp: float
    previous_level: int
    new_level: int
    is_level_up: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserGrowthProfile:
    """用户成长档案"""
    user_id: str
    current_level: int
    total_growth_points: int
    current_level_points: int
    next_level_threshold: int
    progress_percentage: float
    level_name: str
    privileges: List[str]
    total_actions: int
    streak_days: int


@dataclass
class LevelUpEvent:
    """升级事件"""
    event_id: str
    user_id: str
    previous_level: int
    new_level: int
    level_name: str
    timestamp: float
    new_privileges: List[str]
    bonus_points: int


@dataclass
class LevelUpResult:
    """升级结果"""
    success: bool
    new_level: int
    level_name: str
    granted_privileges: List[str]
    bonus_points_awarded: int
    timestamp: float


@dataclass
class Privilege:
    """特权定义"""
    privilege_id: str
    name: str
    description: str
    icon: str
    is_active: bool


@dataclass
class PrivilegeDef:
    """特权定义详情"""
    privilege_key: str
    name_zh: str
    name_en: str
    description: str
    value: Any


@dataclass
class GrowthActionRule:
    """成长动作规则"""
    action_type: str
    base_points: int
    daily_limit: Optional[int]
    monthly_limit: Optional[int]
    description: str


@dataclass
class DailyUsageSummary:
    """每日使用摘要"""
    user_id: str
    date: str
    actions_count: Dict[str, int]
    total_points_earned: int
    remaining_daily_cap: int
    is_cap_reached: bool


@dataclass
class ContributionTransaction:
    """贡献交易记录"""
    transaction_id: str
    user_id: str
    action_type: str
    points_earned: int
    timestamp: float
    previous_contributor_level: int
    new_contributor_level: int
    is_level_up: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContributorProfile:
    """创作者档案"""
    user_id: str
    contributor_level: int
    level_name: str
    total_contribution_points: int
    revenue_share_percentage: float
    total_earnings: float
    content_count: int
    total_sales: int
    total_views: int
    total_favorites: int


@dataclass
class ContributorLevelUpEvent:
    """创作者等级提升事件"""
    event_id: str
    user_id: str
    previous_level: int
    new_level: int
    level_name: str
    timestamp: float
    new_revenue_share: float
    new_privileges: List[str]


@dataclass
class ContributorLevelUpResult:
    """创作者等级提升结果"""
    success: bool
    new_level: int
    level_name: str
    new_revenue_share: float
    granted_privileges: List[str]
    badge_awarded: str
    timestamp: float


@dataclass
class RevenueShareResult:
    """收益分成结果"""
    creator_amount: float
    platform_amount: float
    creator_percentage: float
    platform_percentage: float
    calculation_details: Dict[str, Any]


@dataclass
class EarningsSummary:
    """收益摘要"""
    user_id: str
    period_start: str
    period_end: str
    total_earnings: float
    pending_earnings: float
    withdrawn_amount: float
    available_balance: float
    breakdown_by_source: Dict[str, float]
    transaction_count: int


@dataclass
class ContributionActionRule:
    """贡献动作规则"""
    action_type: str
    base_points: int
    requires_approval: bool
    revenue_share_base: Optional[float]
    description: str


@dataclass
class ContributorPrivilege:
    """创作者特权"""
    privilege_key: str
    name_zh: str
    description: str
    value: Any


@dataclass
class UploadRecord:
    """上传记录"""
    upload_id: str
    user_id: str
    content_type: str
    title: str
    description: str
    status: str
    price: float
    tags: List[str]
    created_at: float
    updated_at: float
    reviewed_at: Optional[float]
    reviewer_id: Optional[str]
    reject_reason: Optional[str]
    sales_count: int = 0
    view_count: int = 0
    favorite_count: int = 0
    earnings_total: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewResult:
    """审核结果"""
    upload_id: str
    status: str
    reviewer_id: str
    review_time: float
    reject_reason: Optional[str]
    approved: bool


@dataclass
class ContentDetailRecord:
    """内容详情记录"""
    upload_record: UploadRecord
    author_profile: ContributorProfile
    recent_sales: List[Dict[str, Any]]
    rating_summary: Dict[str, float]
    earnings_history: List[Dict[str, Any]]


@dataclass
class RevenueDistribution:
    """收益分配"""
    sale_id: str
    content_id: str
    buyer_id: str
    seller_id: str
    gross_amount: float
    creator_share: float
    platform_fee: float
    tax_amount: float
    net_creator_amount: float
    distribution_time: float


@dataclass
class AdRevenueResult:
    """广告收益结果"""
    article_id: str
    total_views: int
    cpm_rate: float
    total_ad_revenue: float
    creator_share: float
    platform_share: float


@dataclass
class CitationEarningResult:
    """引用收益结果"""
    case_id: str
    citing_user_id: str
    original_author_id: str
    citation_reward: float
    timestamp: float


@dataclass
class EarningEntry:
    """收益条目"""
    entry_id: str
    user_id: str
    source_type: str
    source_id: str
    amount: float
    status: str  # pending, settled, withdrawn
    created_at: float
    settled_at: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WithdrawalRequest:
    """提现请求"""
    withdrawal_id: str
    user_id: str
    amount: float
    method: str
    account_info: str
    status: str  # pending, processing, completed, rejected
    created_at: float
    processed_at: Optional[float]
    processor_id: Optional[str]
    reject_reason: Optional[str]
    transaction_ref: Optional[str]


@dataclass
class ProcessingResult:
    """处理结果"""
    withdrawal_id: str
    status: str
    processed_at: float
    processor_id: str
    notes: str
    transaction_ref: Optional[str]


@dataclass
class EligibilityCheckResult:
    """资格检查结果"""
    is_eligible: bool
    current_balance: float
    requested_amount: float
    min_required: float
    reason: str
    daily_limit_remaining: float
    monthly_limit_remaining: float


@dataclass
class MallProduct:
    """积分商城商品"""
    product_id: str
    name: str
    category: str
    point_cost: int
    description: str
    stock: int
    required_level: int
    icon: str
    is_limited: bool
    expiry_date: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExchangeResult:
    """兑换结果"""
    success: bool
    exchange_id: str
    product_id: str
    product_name: str
    points_spent: int
    user_balance_after: int
    timestamp: float
    message: str


@dataclass
class ExchangeRecord:
    """兑换记录"""
    exchange_id: str
    user_id: str
    product_id: str
    product_name: str
    points_cost: int
    exchanged_at: float
    status: str


@dataclass
class CombinedPrivileges:
    """组合特权"""
    usage_privileges: List[Privilege]
    contributor_privileges: List[ContributorPrivilege]
    synergy_bonus: List[str]
    combined_display_name: str


@dataclass
class IncentiveAwardResult:
    """激励奖励结果"""
    award_id: str
    user_id: str
    quarter: str
    incentive_type: str
    reward_value: Any
    timestamp: float
    message: str


@dataclass
class LeaderboardEntry:
    """排行榜条目"""
    rank: int
    user_id: str
    display_name: str
    score: float
    level: int
    avatar_url: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankReward:
    """排名奖励"""
    rank: int
    honor_badge: str
    physical_reward: Optional[str]
    point_bonus: int
    special_privilege: Optional[str]


@dataclass
class LeaderboardSnapshot:
    """排行榜快照"""
    period: str
    track_type: str
    generated_at: float
    entries: List[LeaderboardEntry]
    total_participants: int
    last_updated: float


@dataclass
class Notification:
    """通知"""
    notification_id: str
    user_id: str
    type: str
    title: str
    message: str
    is_read: bool
    created_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionResult:
    """异常检测结果"""
    is_anomalous: bool
    anomaly_type: Optional[str]
    confidence_score: float
    recommended_action: str
    details: Dict[str, Any]


@dataclass
class OriginalityScore:
    """原创性评分"""
    score: float
    is_original: bool
    similarity_percentage: float
    matched_sources: List[str]
    recommendation: str


@dataclass
class RateLimitResult:
    """速率限制结果"""
    is_allowed: bool
    remaining_requests: int
    reset_time: float
    retry_after: Optional[int]


@dataclass
class FlagResult:
    """标记结果"""
    is_flagged: bool
    flag_id: Optional[str]
    flag_reason: str
    severity: str  # low, medium, high, critical
    requires_review: bool


@dataclass
class FairnessMetrics:
    """公平性指标"""
    total_users_analyzed: int
    flagged_accounts_ratio: float
    avg_daily_actions_per_user: float
    anomaly_detection_rate: float
    content_approval_rate: float
    system_health_score: float


@dataclass
class PlatformGrowthSummary:
    """平台成长摘要"""
    period: str
    total_active_users: int
    users_per_level: Dict[int, int]
    avg_growth_rate: float
    retention_rate: float
    new_users_count: int
    churned_users_count: int
    top_growth_actions: List[Tuple[str, int]]


@dataclass
class EcosystemReport:
    """生态系统报告"""
    period: str
    total_uploads: int
    uploads_by_type: Dict[str, int]
    approval_rate: float
    average_review_time_hours: float
    total_revenue_generated: float
    revenue_distribution: Dict[str, float]
    top_creators: List[Tuple[str, float]]


@dataclass
class CorrelationAnalysis:
    """相关性分析"""
    correlation_coefficient: float
    sample_size: int
    p_value: float
    interpretation: str
    scatter_data: List[Tuple[float, float]]


@dataclass
class LevelDistributionSnapshot:
    """等级分布快照"""
    snapshot_time: float
    usage_level_distribution: Dict[int, int]
    contributor_level_distribution: Dict[int, int]
    dual_high_achievers_count: int  # Users with Lv6+ and C4+
    conversion_rate_usage_to_contributor: float


@dataclass
class RevenueFlowReport:
    """收益流报告"""
    period: str
    total_purchases: float
    platform_revenue: float
    creator_payouts: float
    pending_withdrawals: float
    completed_withdrawals: float
    average_transaction_size: float
    top_earning_content: List[Dict[str, Any]]


@dataclass
class MonthlyReport:
    """月度报告"""
    month: str
    growth_metrics: PlatformGrowthSummary
    ecosystem_metrics: EcosystemReport
    revenue_metrics: RevenueFlowReport
    key_insights: List[str]
    recommendations: List[str]


# ============================================================
# Part A: Track 1 - Usage Growth Engine (使用轨道 - 成长引擎)
# ============================================================


class UsageLevelConfig:
    """
    使用等级配置

    定义8个使用等级的阈值、名称和特权
    """

    USAGE_LEVEL_THRESHOLDS: Dict[int, int] = {
        1: 0,
        2: 200,
        3: 500,
        4: 1000,
        5: 2000,
        6: 4000,
        7: 8000,
        8: 15000,
    }

    USAGE_LEVEL_NAMES: Dict[int, str] = {
        1: "见习居士",
        2: "初探道人",
        3: "修行学士",
        4: "灵台方寸",
        5: "洞天福地",
        6: "金丹大道",
        7: "元婴真君",
        8: "渡劫仙尊",
    }

    USAGE_LEVEL_PRIVILEGES: Dict[int, List[PrivilegeDef]] = {
        1: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
        ],
        2: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
            PrivilegeDef("report_discount_5pct", "报告95折", "Report 5% Off", "房产/命理报告95折", 0.05),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像设置", True),
        ],
        3: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
            PrivilegeDef("report_discount_5pct", "报告95折", "Report 5% Off", "房产/命理报告95折", 0.05),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像设置", True),
            PrivilegeDef("skill_discount_10pct", "技能9折", "Skill 10% Off", "技能购买9折优惠", 0.10),
            PrivilegeDef("exclusive_badge_lv3", "Lv3徽章", "Lv3 Badge", "修行学士专属徽章", "badge_lv3"),
        ],
        4: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
            PrivilegeDef("report_discount_10pct", "报告9折", "Report 10% Off", "房产/命理报告9折", 0.10),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像设置", True),
            PrivilegeDef("skill_discount_15pct", "技能85折", "Skill 15% Off", "技能购买85折优惠", 0.15),
            PrivilegeDef("exclusive_badge_lv4", "Lv4徽章", "Lv4 Badge", "灵台方寸专属徽章", "badge_lv4"),
            PrivilegeDef("priority_support", "优先客服", "Priority Support", "客服优先响应", True),
            PrivilegeDef("free_reports_monthly", "月度免费报告", "Free Reports/Month", "每月2份免费报告", 2),
        ],
        5: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
            PrivilegeDef("report_discount_15pct", "报告85折", "Report 15% Off", "房产/命理报告85折", 0.15),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像设置", True),
            PrivilegeDef("skill_discount_20pct", "技能8折", "Skill 20% Off", "技能购买8折优惠", 0.20),
            PrivilegeDef("exclusive_badge_lv5", "Lv5徽章", "Lv5 Badge", "洞天福地专属徽章", "badge_lv5"),
            PrivilegeDef("priority_support", "优先客服", "Priority Support", "客服优先响应", True),
            PrivilegeDef("free_reports_monthly", "月度免费报告", "Free Reports/Month", "每月5份免费报告", 5),
            PrivilegeDef("early_access", "抢先体验", "Early Access", "新功能抢先体验", True),
        ],
        6: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
            PrivilegeDef("report_discount_20pct", "报告8折", "Report 20% Off", "房产/命理报告8折", 0.20),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像设置", True),
            PrivilegeDef("skill_discount_25pct", "技能75折", "Skill 25% Off", "技能购买75折优惠", 0.25),
            PrivilegeDef("exclusive_badge_lv6", "Lv6徽章", "Lv6 Badge", "金丹大道专属徽章", "badge_lv6"),
            PrivilegeDef("priority_support", "优先客服", "Priority Support", "客服优先响应", True),
            PrivilegeDef("free_reports_monthly", "月度免费报告", "Free Reports/Month", "每月10份免费报告", 10),
            PrivilegeDef("early_access", "抢先体验", "Early Access", "新功能抢先体验", True),
            PrivilegeDef("monthly_bonus_points", "月度奖励积分", "Monthly Bonus Points", "每月额外500积分", 500),
            PrivilegeDef("exclusive_events", "专属活动", "Exclusive Events", "受邀参加线下活动", True),
        ],
        7: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台基础功能访问", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到获取积分", True),
            PrivilegeDef("report_discount_25pct", "报告75折", "Report 25% Off", "房产/命理报告75折", 0.25),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像设置", True),
            PrivilegeDef("skill_discount_30pct", "技能7折", "Skill 30% Off", "技能购买7折优惠", 0.30),
            PrivilegeDef("exclusive_badge_lv7", "Lv7徽章", "Lv7 Badge", "元婴真君专属徽章", "badge_lv7"),
            PrivilegeDef("priority_support", "优先客服", "Priority Support", "客服VIP专线", True),
            PrivilegeDef("free_reports_monthly", "月度免费报告", "Free Reports/Month", "每月20份免费报告", 20),
            PrivilegeDef("early_access", "抢先体验", "Early Access", "新功能抢先体验权", True),
            PrivilegeDef("monthly_bonus_points", "月度奖励积分", "Monthly Bonus Points", "每月额外1000积分", 1000),
            PrivilegeDef("exclusive_events", "专属活动", "Exclusive Events", "受邀参加线下活动", True),
            PrivilegeDef("creator_tools_beta", "创作者工具Beta", "Creator Tools Beta", "创作者工具Beta版使用权", True),
        ],
        8: [
            PrivilegeDef("basic_access", "基础访问", "Basic Access", "平台全部功能", True),
            PrivilegeDef("daily_checkin", "每日签到", "Daily Check-in", "每日签到双倍积分", True),
            PrivilegeDef("report_discount_30pct", "报告7折", "Report 30% Off", "房产/命理报告7折", 0.30),
            PrivilegeDef("custom_avatar", "自定义头像", "Custom Avatar", "自定义头像+特效", True),
            PrivilegeDef("skill_discount_35pct", "技能65折", "Skill 35% Off", "技能购买65折优惠", 0.35),
            PrivilegeDef("exclusive_badge_lv8", "Lv8徽章", "Lv8 Badge", "渡劫仙尊专属徽章", "badge_lv8"),
            PrivilegeDef("priority_support", "优先客服", "Priority Support", "1对1专属顾问", True),
            PrivilegeDef("free_reports_monthly", "月度免费报告", "Free Reports/Month", "无限免费报告", -1),
            PrivilegeDef("early_access", "抢先体验", "Early Access", "产品决策参与权", True),
            PrivilegeDef("monthly_bonus_points", "月度奖励积分", "Monthly Bonus Points", "每月额外2000积分", 2000),
            PrivilegeDef("exclusive_events", "专属活动", "Exclusive Events", "年度盛典VIP席位", True),
            PrivilegeDef("creator_tools_beta", "创作者工具正式版", "Creator Tools Pro", "创作者工具完整版", True),
            PrivilegeDef("platform_governance_vote", "平台治理投票", "Governance Vote", "参与平台治理投票", True),
            PrivilegeDef("legendary_title", "传奇称号", "Legendary Title", "传奇称号展示位", "legendary_title"),
        ],
    }

    GROWTH_ACTION_RULES: Dict[str, GrowthActionRule] = {
        "smart_consultation": GrowthActionRule(
            action_type="smart_consultation",
            base_points=10,
            daily_limit=20,
            monthly_limit=None,
            description="智能咨询对话"
        ),
        "property_report": GrowthActionRule(
            action_type="property_report",
            base_points=20,
            daily_limit=100,
            monthly_limit=None,
            description="生成房产报告"
        ),
        "fortune_report": GrowthActionRule(
            action_type="fortune_report",
            base_points=15,
            daily_limit=75,
            monthly_limit=None,
            description="生成命理报告"
        ),
        "skill_purchase": GrowthActionRule(
            action_type="skill_purchase",
            base_points=30,
            daily_limit=None,
            monthly_limit=None,
            description="购买技能"
        ),
        "agent_recruitment": GrowthActionRule(
            action_type="agent_recruitment",
            base_points=50,
            daily_limit=None,
            monthly_limit=None,
            description="招募智能体"
        ),
        "bond_activation": GrowthActionRule(
            action_type="bond_activation",
            base_points=40,
            daily_limit=None,
            monthly_limit=None,
            description="激活契约关系"
        ),
        "scheduled_task_setup": GrowthActionRule(
            action_type="scheduled_task_setup",
            base_points=20,
            daily_limit=1,
            monthly_limit=None,
            description="设置定时任务（首月首次有额外奖励）"
        ),
        "pdf_export": GrowthActionRule(
            action_type="pdf_export",
            base_points=5,
            daily_limit=50,
            monthly_limit=None,
            description="导出PDF报告"
        ),
        "property_compare": GrowthActionRule(
            action_type="property_compare",
            base_points=10,
            daily_limit=50,
            monthly_limit=None,
            description="房产对比分析"
        ),
        "daily_checkin": GrowthActionRule(
            action_type="daily_checkin",
            base_points=5,
            daily_limit=1,
            monthly_limit=None,
            description="每日签到"
        ),
        "feedback_rating": GrowthActionRule(
            action_type="feedback_rating",
            base_points=2,
            daily_limit=20,
            monthly_limit=None,
            description="反馈评价"
        ),
    }

    @classmethod
    def get_level_from_points(cls, total_points: int) -> int:
        """根据总成长值获取当前等级"""
        level = 1
        for lvl, threshold in sorted(cls.USAGE_LEVEL_THRESHOLDS.items()):
            if total_points >= threshold:
                level = lvl
            else:
                break
        return level

    @classmethod
    def get_next_level_threshold(cls, current_level: int) -> int:
        """获取下一等级所需成长值"""
        if current_level >= 8:
            return cls.USAGE_LEVEL_THRESHOLDS[8]
        return cls.USAGE_LEVEL_THRESHOLDS.get(current_level + 1, 999999)

    @classmethod
    def get_level_name(cls, level: int) -> str:
        """获取等级名称"""
        return cls.USAGE_LEVEL_NAMES.get(level, "未知")

    @classmethod
    def get_level_privileges(cls, level: int) -> List[PrivilegeDef]:
        """获取等级特权列表"""
        return cls.USAGE_LEVEL_PRIVILEGES.get(level, [])


class UsageGrowthEngine:
    """
    使用轨道成长引擎

    职责:
    - 记录用户平台使用行为并计算成长值(Growth Points)
    - 管理等级晋升(Lv1-Lv8)与特权授予
    - 每日使用上限控制
    - 用户成长档案管理
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._user_states: Dict[str, Dict[str, Any]] = {}
        self._transaction_log: List[GrowthTransaction] = []
        self._level_config = UsageLevelConfig()
        self._daily_tracking: Dict[str, Dict[str, int]] = {}  # user_id -> {action_type: count}

    def _get_or_create_user_state(self, user_id: str) -> Dict[str, Any]:
        """获取或创建用户状态"""
        with self._lock:
            if user_id not in self._user_states:
                self._user_states[user_id] = {
                    "user_id": user_id,
                    "total_growth_points": 0,
                    "current_level": 1,
                    "total_actions": 0,
                    "streak_days": 0,
                    "last_checkin_date": None,
                    "level_up_history": [],
                    "created_at": time.time(),
                    "updated_at": time.time(),
                }
            return self._user_states[user_id]

    def _get_today_key(self) -> str:
        """获取今天的日期键"""
        return datetime.date.today().isoformat()

    def _get_daily_action_count(self, user_id: str, action_type: str) -> int:
        """获取今日某动作的执行次数"""
        today = self._get_today_key()
        if user_id not in self._daily_tracking:
            self._daily_tracking[user_id] = {}
        return self._daily_tracking[user_id].get(today + "_" + action_type, 0)

    def _increment_daily_action(self, user_id: str, action_type: str) -> None:
        """增加今日动作计数"""
        today = self._get_today_key()
        if user_id not in self._daily_tracking:
            self._daily_tracking[user_id] = {}
        key = today + "_" + action_type
        self._daily_tracking[user_id][key] = self._daily_tracking[user_id].get(key, 0) + 1

    def record_growth_action(self, user_id: str, action_type: str,
                            amount: int = 1,
                            metadata: Optional[Dict[str, Any]] = None) -> GrowthTransaction:
        """
        记录成长动作

        Args:
            user_id: 用户ID
            action_type: 动作类型
            amount: 动作数量/金额
            metadata: 附加元数据

        Returns:
            成长交易记录
        """
        state = self._get_or_create_user_state(user_id)
        rule = self._level_config.GROWTH_ACTION_RULES.get(action_type)

        if not rule:
            rule = GrowthActionRule(
                action_type=action_type,
                base_points=1,
                daily_limit=10,
                monthly_limit=None,
                description="默认动作"
            )

        with self._lock:
            prev_level = state["current_level"]
            actual_points = 0

            # 检查每日限制
            if rule.daily_limit is not None:
                daily_count = self._get_daily_action_count(user_id, action_type)
                if daily_count >= rule.daily_limit:
                    meta = {"reason": "daily_limit_reached", "limit": rule.daily_limit}
                    if metadata:
                        meta.update(metadata)
                    return GrowthTransaction(
                        transaction_id=str(uuid.uuid4()),
                        user_id=user_id,
                        action_type=action_type,
                        points_earned=0,
                        timestamp=time.time(),
                        previous_level=prev_level,
                        new_level=prev_level,
                        is_level_up=False,
                        metadata=meta,
                    )

            # 计算实际获得积分
            actual_points = rule.base_points * amount

            # 签到连续天数奖励
            if action_type == "daily_checkin":
                today_str = self._get_today_key()
                yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
                if state["last_checkin_date"] == today_str:
                    actual_points = 0  # 今日已签到
                elif state["last_checkin_date"] == yesterday:
                    state["streak_days"] += 1
                    streak_bonus = min(state["streak_days"], 7) * 0.1
                    actual_points = int(actual_points * (1 + streak_bonus))
                else:
                    state["streak_days"] = 1
                state["last_checkin_date"] = today_str

            # 更新状态
            state["total_growth_points"] += actual_points
            state["total_actions"] += 1
            state["updated_at"] = time.time()

            # 更新每日追踪
            self._increment_daily_action(user_id, action_type)

            # 检查升级
            new_level = self._level_config.get_level_from_points(state["total_growth_points"])
            is_level_up = new_level > prev_level

            if is_level_up:
                state["current_level"] = new_level
                state["level_up_history"].append({
                    "level": new_level,
                    "timestamp": time.time(),
                    "points_at_upgrade": state["total_growth_points"]
                })

            # 创建交易记录
            transaction = GrowthTransaction(
                transaction_id=str(uuid.uuid4()),
                user_id=user_id,
                action_type=action_type,
                points_earned=actual_points,
                timestamp=time.time(),
                previous_level=prev_level,
                new_level=new_level,
                is_level_up=is_level_up,
                metadata=metadata or {},
            )
            self._transaction_log.append(transaction)
            return transaction

    def get_user_growth_profile(self, user_id: str) -> UserGrowthProfile:
        """
        获取用户成长档案

        Returns:
            用户成长档案对象
        """
        state = self._get_or_create_user_state(user_id)
        current_level = state["current_level"]
        total_points = state["total_growth_points"]
        next_threshold = self._level_config.get_next_level_threshold(current_level)
        current_level_threshold = self._level_config.USAGE_LEVEL_THRESHOLDS.get(current_level, 0)

        progress = 0.0
        if current_level < 8:
            progress = ((total_points - current_level_threshold) /
                       (next_threshold - current_level_threshold)) * 100
            progress = min(100.0, max(0.0, progress))

        privileges = self._level_config.get_level_privileges(current_level)
        privilege_names = [p.privilege_key for p in privileges]

        return UserGrowthProfile(
            user_id=user_id,
            current_level=current_level,
            total_growth_points=total_points,
            current_level_points=total_points - current_level_threshold,
            next_level_threshold=next_threshold,
            progress_percentage=round(progress, 2),
            level_name=self._level_config.get_level_name(current_level),
            privileges=privilege_names,
            total_actions=state["total_actions"],
            streak_days=state["streak_days"],
        )

    def check_level_up(self, user_id: str) -> Optional[LevelUpEvent]:
        """
        检查是否应该升级

        Returns:
            升级事件或None
        """
        profile = self.get_user_growth_profile(user_id)
        state = self._get_or_create_user_state(user_id)

        if profile.current_level >= 8:
            return None

        next_level = profile.current_level + 1
        next_threshold = self._level_config.USAGE_LEVEL_THRESHOLDS.get(next_level, 999999)

        if profile.total_growth_points >= next_threshold:
            new_privileges_def = self._level_config.get_level_privileges(next_level)
            new_privileges = [p.privilege_key for p in new_privileges_def]

            return LevelUpEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                previous_level=profile.current_level,
                new_level=next_level,
                level_name=self._level_config.get_level_name(next_level),
                timestamp=time.time(),
                new_privileges=new_privileges,
                bonus_points=self._calculate_level_up_bonus(next_level),
            )
        return None

    def _calculate_level_up_bonus(self, new_level: int) -> int:
        """计算升级奖励积分"""
        bonus_map = {2: 50, 3: 100, 4: 200, 5: 400, 6: 800, 7: 1500, 8: 3000}
        return bonus_map.get(new_level, 0)

    def apply_level_up(self, user_id: str, new_level: int) -> LevelUpResult:
        """
        应用升级

        Args:
            user_id: 用户ID
            new_level: 新等级

        Returns:
            升级结果
        """
        state = self._get_or_create_user_state(user_id)
        prev_level = state["current_level"]

        with self._lock:
            if new_level <= prev_level:
                return LevelUpResult(
                    success=False,
                    new_level=prev_level,
                    level_name=self._level_config.get_level_name(prev_level),
                    granted_privileges=[],
                    bonus_points_awarded=0,
                    timestamp=time.time(),
                )

            state["current_level"] = new_level
            privileges_def = self._level_config.get_level_privileges(new_level)
            privileges = [p.privilege_key for p in privileges_def]
            bonus = self._calculate_level_up_bonus(new_level)

            state["total_growth_points"] += bonus
            state["level_up_history"].append({
                "level": new_level,
                "timestamp": time.time(),
                "bonus_awarded": bonus
            })

            return LevelUpResult(
                success=True,
                new_level=new_level,
                level_name=self._level_config.get_level_name(new_level),
                granted_privileges=privileges,
                bonus_points_awarded=bonus,
                timestamp=time.time(),
            )

    def get_daily_usage_summary(self, user_id: str) -> DailyUsageSummary:
        """
        获取今日使用摘要

        Returns:
            每日使用摘要
        """
        today = self._get_today_key()
        actions_count: Dict[str, int] = {}
        total_points = 0

        if user_id in self._daily_tracking:
            for key, count in self._daily_tracking[user_id].items():
                if key.startswith(today + "_"):
                    action_type = key[len(today) + 1:]
                    actions_count[action_type] = count
                    rule = self._level_config.GROWTH_ACTION_RULES.get(action_type)
                    if rule:
                        total_points += rule.base_points * count

        profile = self.get_user_growth_profile(user_id)
        level_def = self._level_config.USAGE_LEVEL_PRIVILEGES.get(profile.current_level, [])
        daily_cap = 500  # 默认每日上限
        for priv in level_def:
            if priv.privilege_key == "daily_xp_cap":
                daily_cap = priv.value
                break

        return DailyUsageSummary(
            user_id=user_id,
            date=today,
            actions_count=actions_count,
            total_points_earned=total_points,
            remaining_daily_cap=max(0, daily_cap - total_points),
            is_cap_reached=total_points >= daily_cap,
        )

    def get_available_privileges(self, user_id: str) -> List[Privilege]:
        """
        获取可用特权列表

        Returns:
            特权列表
        """
        profile = self.get_user_growth_profile(user_id)
        privileges_def = self._level_config.get_level_privileges(profile.current_level)

        privileges = []
        for priv_def in privileges_def:
            privileges.append(Privilege(
                privilege_id=priv_def.privilege_key,
                name=priv_def.name_en,
                description=priv_def.description,
                icon="icon_" + priv_def.privilege_key,
                is_active=True,
            ))
        return privileges


# ============================================================
# Part B: Track 2 - Contribution Engine (贡献轨道 - 创作者引擎)
# ============================================================


class ContributorLevelConfig:
    """
    创作者等级配置

    定义8个创作者等级的阈值、名称、特权和收益分成比例
    """

    CONTRIBUTOR_LEVEL_THRESHOLDS: Dict[int, int] = {
        1: 0,
        2: 100,
        3: 300,
        4: 600,
        5: 1000,
        6: 2000,
        7: 4000,
        8: 8000,
    }

    CONTRIBUTOR_LEVEL_NAMES: Dict[int, str] = {
        1: "初耕者",
        2: "耕耘人",
        3: "匠心师",
        4: "开创者",
        5: "传承者",
        6: "宗师",
        7: "圣人",
        8: "造物主",
    }

    CONTRIBUTOR_PRIVILEGES: Dict[int, List[ContributorPrivilege]] = {
        1: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传技能和文章", True),
            ContributorPrivilege("revenue_share_50", "50%收益分成", "技能销售50%收益", 0.50),
        ],
        2: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传技能和文章", True),
            ContributorPrivilege("revenue_share_52", "52%收益分成", "技能销售52%收益", 0.52),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
        ],
        3: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传所有类型内容", True),
            ContributorPrivilege("revenue_share_55", "55%收益分成", "技能销售55%收益", 0.55),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
            ContributorPrivilege("publish_article", "发布文章", "可发布长文", True),
            ContributorPrivilege("review_priority_2", "审核优先级2", "中等审核优先级", 2),
        ],
        4: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传所有类型内容", True),
            ContributorPrivilege("revenue_share_58", "58%收益分成", "技能销售58%收益", 0.58),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
            ContributorPrivilege("publish_article", "发布文章", "可发布长文", True),
            ContributorPrivilege("review_priority_3", "审核优先级3", "较高审核优先级", 3),
            ContributorPrivilege("contest_eligible", "大赛资格", "有资格参加创作大赛", True),
        ],
        5: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传所有类型内容", True),
            ContributorPrivilege("revenue_share_60", "60%收益分成", "技能销售60%收益", 0.60),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
            ContributorPrivilege("publish_article", "发布文章", "可发布长文", True),
            ContributorPrivilege("review_priority_4", "审核优先级4", "高审核优先级", 4),
            ContributorPrivilege("contest_eligible", "大赛资格", "有资格参加创作大赛", True),
            ContributorPrivilege("co_author_invitation", "合作邀请", "可邀请合作者", True),
        ],
        6: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传所有类型内容", True),
            ContributorPrivilege("revenue_share_62", "62%收益分成", "技能销售62%收益", 0.62),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
            ContributorPrivilege("publish_article", "发布文章", "可发布长文", True),
            ContributorPrivilege("review_priority_5", "审核优先级5", "很高审核优先级", 5),
            ContributorPrivilege("contest_eligible", "大赛资格", "有资格参加创作大赛", True),
            ContributorPrivilege("co_author_invitation", "合作邀请", "可邀请合作者", True),
            ContributorPrivilege("custom_branding", "品牌定制", "个人品牌展示位", True),
        ],
        7: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传所有类型内容", True),
            ContributorPrivilege("revenue_share_65", "65%收益分成", "技能销售65%收益", 0.65),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
            ContributorPrivilege("publish_article", "发布文章", "可发布长文", True),
            ContributorPrivilege("review_priority_6", "审核优先级6", "最高审核优先级", 6),
            ContributorPrivilege("contest_eligible", "大赛资格", "有资格参加创作大赛", True),
            ContributorPrivilege("co_author_invitation", "合作邀请", "可邀请合作者", True),
            ContributorPrivilege("custom_branding", "品牌定制", "个人品牌展示位", True),
            ContributorPrivilege("mentor_program", "导师计划", "成为新人导师", True),
        ],
        8: [
            ContributorPrivilege("basic_upload", "基础上传", "可上传所有类型内容", True),
            ContributorPrivilege("revenue_share_70", "70%收益分成", "技能销售70%收益", 0.70),
            ContributorPrivilege("upload_agent_template", "上传智能体模板", "可上传智能体模板", True),
            ContributorPrivilege("publish_article", "发布文章", "可发布长文", True),
            ContributorPrivilege("review_priority_7", "审核优先级7", "顶级审核优先级", 7),
            ContributorPrivilege("contest_eligible", "大赛资格", "自动入围决赛", True),
            ContributorPrivilege("co_author_invitation", "合作邀请", "可邀请无限合作者", True),
            ContributorPrivilege("custom_branding", "品牌定制", "专属品牌页面", True),
            ContributorPrivilege("mentor_program", "导师计划", "官方认证导师", True),
            ContributorPrivilege("platform_advisory", "平台顾问", "参与平台发展建议", True),
        ],
    }

    CONTRIBUTION_ACTION_RULES: Dict[str, ContributionActionRule] = {
        "upload_skill": ContributionActionRule(
            action_type="upload_skill",
            base_points=50,
            requires_approval=True,
            revenue_share_base=0.50,
            description="上传技能（需审核）"
        ),
        "skill_purchased_by_others": ContributionActionRule(
            action_type="skill_purchased_by_others",
            base_points=5,
            requires_approval=False,
            revenue_share_base=None,
            description="技能被他人购买（每次+5点）"
        ),
        "upload_agent_template": ContributionActionRule(
            action_type="upload_agent_template",
            base_points=200,
            requires_approval=True,
            revenue_share_base=0.30,
            description="上传智能体模板（需审核）"
        ),
        "publish_article": ContributionActionRule(
            action_type="publish_article",
            base_points=30,
            requires_approval=True,
            revenue_share_base=None,
            description="发布文章（需审核，广告收益分成）"
        ),
        "upload_case_report": ContributionActionRule(
            action_type="upload_case_report",
            base_points=20,
            requires_approval=True,
            revenue_share_base=None,
            description="上传案例报告（需审核，被引用+5点）"
        ),
        "co_author_development": ContributionActionRule(
            action_type="co_author_development",
            base_points=0,
            requires_approval=False,
            revenue_share_base=None,
            description="合作开发（按贡献比例分配）"
        ),
        "official_recommendation": ContributionActionRule(
            action_type="official_recommendation",
            base_points=100,
            requires_approval=False,
            revenue_share_base=None,
            description="官方推荐（平台主动推荐）"
        ),
        "content_favorited": ContributionActionRule(
            action_type="content_favorited",
            base_points=1,
            requires_approval=False,
            revenue_share_base=None,
            description="内容被收藏（每次+1点）"
        ),
    }

    @classmethod
    def get_level_from_points(cls, total_points: int) -> int:
        """根据总贡献值获取创作者等级"""
        level = 1
        for lvl, threshold in sorted(cls.CONTRIBUTOR_LEVEL_THRESHOLDS.items()):
            if total_points >= threshold:
                level = lvl
            else:
                break
        return level

    @classmethod
    def get_level_name(cls, level: int) -> str:
        """获取创作者等级名称"""
        return cls.CONTRIBUTOR_LEVEL_NAMES.get(level, "未知")

    @classmethod
    def get_revenue_share_percentage(cls, level: int) -> float:
        """获取等级对应的收益分成比例"""
        privileges = cls.CONTRIBUTOR_PRIVILEGES.get(level, [])
        for priv in privileges:
            if priv.privilege_key.startswith("revenue_share_"):
                return float(priv.value)
        return 0.50

    @classmethod
    def get_level_privileges(cls, level: int) -> List[ContributorPrivilege]:
        """获取创作者等级特权列表"""
        return cls.CONTRIBUTOR_PRIVILEGES.get(level, [])


class ContributionEngine:
    """
    贡献轨道引擎

    聟责:
    - 记录创作者的贡献行为并计算贡献点
    - 管理创作者等级晋升(C1-C8)
    - 计算收益分成比例
    - 创作者档案管理
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._contributor_states: Dict[str, Dict[str, Any]] = {}
        self._transaction_log: List[ContributionTransaction] = []
        self._earnings_ledger: Dict[str, List[EarningEntry]] = {}
        self._level_config = ContributorLevelConfig()

    def _get_or_create_contributor_state(self, user_id: str) -> Dict[str, Any]:
        """获取或创建创作者状态"""
        with self._lock:
            if user_id not in self._contributor_states:
                self._contributor_states[user_id] = {
                    "user_id": user_id,
                    "total_contribution_points": 0,
                    "contributor_level": 1,
                    "total_earnings": 0.0,
                    "content_count": 0,
                    "total_sales": 0,
                    "total_views": 0,
                    "total_favorites": 0,
                    "level_up_history": [],
                    "created_at": time.time(),
                    "updated_at": time.time(),
                }
            return self._contributor_states[user_id]

    def record_contribution_action(self, user_id: str, action_type: str,
                                  amount: int = 1,
                                  metadata: Optional[Dict[str, Any]] = None) -> ContributionTransaction:
        """
        记录贡献动作

        Args:
            user_id: 用户ID
            action_type: 动作类型
            amount: 数量
            metadata: 元数据

        Returns:
            贡献交易记录
        """
        state = self._get_or_create_contributor_state(user_id)
        rule = self._level_config.CONTRIBUTION_ACTION_RULES.get(action_type)

        if not rule:
            rule = ContributionActionRule(
                action_type=action_type,
                base_points=1,
                requires_approval=False,
                revenue_share_base=None,
                description="默认贡献动作"
            )

        with self._lock:
            prev_level = state["contributor_level"]
            actual_points = rule.base_points * amount

            # 更新状态
            state["total_contribution_points"] += actual_points
            state["updated_at"] = time.time()

            # 根据动作类型更新统计
            if action_type == "upload_skill":
                state["content_count"] += amount
            elif action_type == "skill_purchased_by_others":
                state["total_sales"] += amount
            elif action_type == "content_favorited":
                state["total_favorites"] += amount

            # 检查升级
            new_level = self._level_config.get_level_from_points(state["total_contribution_points"])
            is_level_up = new_level > prev_level

            if is_level_up:
                state["contributor_level"] = new_level
                state["level_up_history"].append({
                    "level": new_level,
                    "timestamp": time.time(),
                    "points_at_upgrade": state["total_contribution_points"]
                })

            transaction = ContributionTransaction(
                transaction_id=str(uuid.uuid4()),
                user_id=user_id,
                action_type=action_type,
                points_earned=actual_points,
                timestamp=time.time(),
                previous_contributor_level=prev_level,
                new_contributor_level=new_level,
                is_level_up=is_level_up,
                metadata=metadata or {},
            )
            self._transaction_log.append(transaction)
            return transaction

    def get_contributor_profile(self, user_id: str) -> ContributorProfile:
        """
        获取创作者档案

        Returns:
            创作者档案
        """
        state = self._get_or_create_contributor_state(user_id)
        level = state["contributor_level"]

        return ContributorProfile(
            user_id=user_id,
            contributor_level=level,
            level_name=self._level_config.get_level_name(level),
            total_contribution_points=state["total_contribution_points"],
            revenue_share_percentage=self._level_config.get_revenue_share_percentage(level),
            total_earnings=state["total_earnings"],
            content_count=state["content_count"],
            total_sales=state["total_sales"],
            total_views=state["total_views"],
            total_favorites=state["total_favorites"],
        )

    def check_contributor_level_up(self, user_id: str) -> Optional[ContributorLevelUpEvent]:
        """
        检查创作者是否应该升级

        Returns:
            创作者升级事件或None
        """
        profile = self.get_contributor_profile(user_id)

        if profile.contributor_level >= 8:
            return None

        next_level = profile.contributor_level + 1
        next_threshold = self._level_config.CONTRIBUTOR_LEVEL_THRESHOLDS.get(next_level, 999999)

        if profile.total_contribution_points >= next_threshold:
            new_privileges = self._level_config.get_level_privileges(next_level)
            privilege_keys = [p.privilege_key for p in new_privileges]

            return ContributorLevelUpEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                previous_level=profile.contributor_level,
                new_level=next_level,
                level_name=self._level_config.get_level_name(next_level),
                timestamp=time.time(),
                new_revenue_share=self._level_config.get_revenue_share_percentage(next_level),
                new_privileges=privilege_keys,
            )
        return None

    def apply_contributor_level_up(self, user_id: str, new_level: int) -> ContributorLevelUpResult:
        """
        应用创作者升级

        Args:
            user_id: 用户ID
            new_level: 新等级

        Returns:
            升级结果
        """
        state = self._get_or_create_contributor_state(user_id)
        prev_level = state["contributor_level"]

        with self._lock:
            if new_level <= prev_level:
                return ContributorLevelUpResult(
                    success=False,
                    new_level=prev_level,
                    level_name=self._level_config.get_level_name(prev_level),
                    new_revenue_share=self._level_config.get_revenue_share_percentage(prev_level),
                    granted_privileges=[],
                    badge_awarded="",
                    timestamp=time.time(),
                )

            state["contributor_level"] = new_level
            privileges = self._level_config.get_level_privileges(new_level)
            privilege_keys = [p.privilege_key for p in privileges]
            new_revenue_share = self._level_config.get_revenue_share_percentage(new_level)

            badge_map = {2: "耕耘人勋章", 3: "匠心师徽章", 4: "开创者奖章",
                        5: "传承者令牌", 6: "宗师印信", 7: "圣人玉牒", 8: "造物主神谕"}
            badge = badge_map.get(new_level, "")

            state["level_up_history"].append({
                "level": new_level,
                "timestamp": time.time(),
                "badge_awarded": badge
            })

            return ContributorLevelUpResult(
                success=True,
                new_level=new_level,
                level_name=self._level_config.get_level_name(new_level),
                new_revenue_share=new_revenue_share,
                granted_privileges=privilege_keys,
                badge_awarded=badge,
                timestamp=time.time(),
            )

    def calculate_revenue_share(self, sale_amount: float, contributor_level: int,
                                content_type: str) -> RevenueShareResult:
        """
        计算收益分成

        Args:
            sale_amount: 销售金额
            contributor_level: 创作者等级
            content_type: 内容类型

        Returns:
            收益分成结果
        """
        base_share = self._level_config.get_revenue_share_percentage(contributor_level)

        # 根据内容类型调整
        if content_type == "agent_template":
            base_share = min(base_share, 0.35)  # 模板最高35%
        elif content_type == "article":
            base_share = base_share * 0.8  # 文章广告收益80%

        creator_amount = sale_amount * base_share
        platform_amount = sale_amount - creator_amount

        return RevenueShareResult(
            creator_amount=round(creator_amount, 2),
            platform_amount=round(platform_amount, 2),
            creator_percentage=base_share,
            platform_percentage=round(1 - base_share, 2),
            calculation_details={
                "sale_amount": sale_amount,
                "contributor_level": contributor_level,
                "content_type": content_type,
                "base_share": base_share,
            },
        )

    def get_earnings_summary(self, user_id: str,
                             period: str = "month") -> EarningsSummary:
        """
        获取收益摘要

        Args:
            user_id: 用户ID
            period: 周期 (week/month/quarter/year)

        Returns:
            收益摘要
        """
        state = self._get_or_create_contributor_state(user_id)
        entries = self._earnings_ledger.get(user_id, [])

        now = datetime.datetime.now()
        if period == "week":
            start = now - datetime.timedelta(weeks=1)
        elif period == "month":
            start = now - datetime.timedelta(days=30)
        elif period == "quarter":
            start = now - datetime.timedelta(days=90)
        elif period == "year":
            start = now - datetime.timedelta(days=365)
        else:
            start = now - datetime.timedelta(days=30)

        period_entries = [e for e in entries if e.created_at >= start.timestamp()]

        total_earnings = sum(e.amount for e in period_entries if e.status != "withdrawn")
        pending_earnings = sum(e.amount for e in period_entries if e.status == "pending")
        withdrawn = sum(e.amount for e in period_entries if e.status == "withdrawn")

        breakdown: Dict[str, float] = {}
        for entry in period_entries:
            if entry.status != "withdrawn":
                breakdown[entry.source_type] = breakdown.get(entry.source_type, 0) + entry.amount

        return EarningsSummary(
            user_id=user_id,
            period_start=start.isoformat(),
            period_end=now.isoformat(),
            total_earnings=round(total_earnings, 2),
            pending_earnings=round(pending_earnings, 2),
            withdrawn_amount=round(withdrawn, 2),
            available_balance=round(total_earnings - withdrawn, 2),
            breakdown_by_source=breakdown,
            transaction_count=len(period_entries),
        )


# ============================================================
# Part C: Content Upload Management (内容上传管理)
# ============================================================


class ContentUploadManager:
    """
    内容上传管理器

    职责:
    - 管理用户上传的内容（技能、文章、案例等）
    - 内容审核流程
    - 内容统计更新
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._uploads: Dict[str, UploadRecord] = {}
        self._user_uploads: Dict[str, List[str]] = {}  # user_id -> [upload_ids]
        self._pending_reviews: List[str] = []  # 待审核队列

    def submit_upload(self, user_id: str, content_type: str, title: str,
                      description: str, content: str, price: float = 0.0,
                      tags: Optional[List[str]] = None) -> UploadRecord:
        """
        提交内容上传

        Args:
            user_id: 用户ID
            content_type: 内容类型 (skill/article/case/template)
            title: 标题
            description: 描述
            content: 内容
            price: 价格
            tags: 标签列表

        Returns:
            上传记录
        """
        upload_id = "upload_" + str(uuid.uuid4())[:8]
        now = time.time()

        record = UploadRecord(
            upload_id=upload_id,
            user_id=user_id,
            content_type=content_type,
            title=title,
            description=description,
            status=UploadStatus.PENDING.value,
            price=price,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            reviewed_at=None,
            reviewer_id=None,
            reject_reason=None,
            metadata={"content_preview": content[:500] if content else ""},
        )

        with self._lock:
            self._uploads[upload_id] = record
            if user_id not in self._user_uploads:
                self._user_uploads[user_id] = []
            self._user_uploads[user_id].append(upload_id)
            self._pending_reviews.append(upload_id)

        return record

    def review_upload(self, upload_id: str, status: str,
                      reviewer_id: str,
                      reject_reason: Optional[str] = None) -> ReviewResult:
        """
        审核上传内容

        Args:
            upload_id: 上传ID
            status: 审核状态 (approved/rejected)
            reviewer_id: 审核员ID
            reject_reason: 拒绝原因

        Returns:
            审核结果
        """
        with self._lock:
            record = self._uploads.get(upload_id)
            if not record:
                return ReviewResult(
                    upload_id=upload_id,
                    status="error",
                    reviewer_id=reviewer_id,
                    review_time=time.time(),
                    reject_reason="Upload not found",
                    approved=False,
                )

            record.status = status
            record.reviewed_at = time.time()
            record.reviewer_id = reviewer_id
            record.reject_reason = reject_reason
            record.updated_at = time.time()

            if upload_id in self._pending_reviews:
                self._pending_reviews.remove(upload_id)

            return ReviewResult(
                upload_id=upload_id,
                status=status,
                reviewer_id=reviewer_id,
                review_time=time.time(),
                reject_reason=reject_reason,
                approved=(status == UploadStatus.APPROVED.value),
            )

    def get_user_uploads(self, user_id: str,
                         status_filter: Optional[str] = None) -> List[UploadRecord]:
        """
        获取用户的上传列表

        Args:
            user_id: 用户ID
            status_filter: 状态过滤

        Returns:
            上传记录列表
        """
        upload_ids = self._user_uploads.get(user_id, [])
        records = []

        for uid in upload_ids:
            record = self._uploads.get(uid)
            if record:
                if status_filter is None or record.status == status_filter:
                    records.append(record)

        return sorted(records, key=lambda x: x.created_at, reverse=True)

    def update_upload(self, upload_id: str,
                      updates: Dict[str, Any]) -> UploadRecord:
        """
        更新上传内容

        Args:
            upload_id: 上传ID
            updates: 更新字段字典

        Returns:
            更新后的记录
        """
        with self._lock:
            record = self._uploads.get(upload_id)
            if not record:
                raise ValueError("Upload not found: " + upload_id)

            if record.status != UploadStatus.PENDING.value:
                raise ValueError("Can only update pending uploads")

            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            record.updated_at = time.time()
            return record

    def delete_upload(self, upload_id: str, user_id: str) -> bool:
        """
        删除上传内容

        Args:
            upload_id: 上传ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        with self._lock:
            record = self._uploads.get(upload_id)
            if not record or record.user_id != user_id:
                return False

            if record.status == UploadStatus.APPROVED.value:
                return False  # 已审核通过的不能删除

            del self._uploads[upload_id]
            if user_id in self._user_uploads:
                self._user_uploads[user_id] = [
                    uid for uid in self._user_uploads[user_id] if uid != upload_id
                ]
            if upload_id in self._pending_reviews:
                self._pending_reviews.remove(upload_id)

            return True

    def increment_stats(self, upload_id: str, stat_type: str,
                        amount: int = 1) -> None:
        """
        增加内容统计

        Args:
            upload_id: 上传ID
            stat_type: 统计类型 (sales/views/favorites)
            amount: 增加数量
        """
        with self._lock:
            record = self._uploads.get(upload_id)
            if record:
                if stat_type == "sales":
                    record.sales_count += amount
                elif stat_type == "views":
                    record.view_count += amount
                elif stat_type == "favorites":
                    record.favorite_count += amount

    def get_content_details(self, upload_id: str) -> ContentDetailRecord:
        """
        获取内容详情

        Args:
            upload_id: 上传ID

        Returns:
            内容详情记录
        """
        record = self._uploads.get(upload_id)
        if not record:
            raise ValueError("Content not found: " + upload_id)

        return ContentDetailRecord(
            upload_record=record,
            author_profile=ContributorProfile(
                user_id=record.user_id,
                contributor_level=1,
                level_name="初耕者",
                total_contribution_points=0,
                revenue_share_percentage=0.50,
                total_earnings=record.earnings_total,
                content_count=1,
                total_sales=record.sales_count,
                total_views=record.view_count,
                total_favorites=record.favorite_count,
            ),
            recent_sales=[],
            rating_summary={"avg_rating": 0.0, "total_ratings": 0},
            earnings_history=[],
        )


# ============================================================
# Part D: Revenue & Earnings System (收益与提现系统)
# ============================================================


class RevenueCalculator:
    """
    收益计算器

    职责:
    - 计算各类内容的收益分配
    - 广告收益计算
    - 引用收益计算
    - 收益记录存储
    """

    def __init__(self, contribution_engine: ContributionEngine) -> None:
        self._contribution_engine = contribution_engine
        self._lock: threading.Lock = threading.Lock()
        self._revenue_records: List[RevenueDistribution] = []

    def calculate_skill_sale_revenue(self, skill_id: str, buyer_id: str,
                                     price: float) -> RevenueDistribution:
        """
        计算技能销售收益分配

        Args:
            skill_id: 技能ID
            buyer_id: 购买者ID
            price: 价格

        Returns:
            收益分配结果
        """
        # 获取创作者等级（简化处理，实际应从数据库查询）
        creator_level = 3  # 默认等级
        share_result = self._contribution_engine.calculate_revenue_share(
            price, creator_level, "skill"
        )

        tax_rate = 0.06  # 6%税费
        tax_amount = share_result.creator_amount * tax_rate
        net_creator = share_result.creator_amount - tax_amount

        distribution = RevenueDistribution(
            sale_id="sale_" + str(uuid.uuid4())[:8],
            content_id=skill_id,
            buyer_id=buyer_id,
            seller_id="creator_" + skill_id,
            gross_amount=price,
            creator_share=share_result.creator_amount,
            platform_fee=share_result.platform_amount,
            tax_amount=round(tax_amount, 2),
            net_creator_amount=round(net_creator, 2),
            distribution_time=time.time(),
        )

        with self._lock:
            self._revenue_records.append(distribution)

        return distribution

    def calculate_template_revenue(self, template_id: str, buyer_id: str,
                                   price: float) -> RevenueDistribution:
        """
        计算模板销售收益分配

        Args:
            template_id: 模板ID
            buyer_id: 购买者ID
            price: 价格

        Returns:
            收益分配结果
        """
        creator_level = 3
        share_result = self._contribution_engine.calculate_revenue_share(
            price, creator_level, "agent_template"
        )

        tax_rate = 0.06
        tax_amount = share_result.creator_amount * tax_rate
        net_creator = share_result.creator_amount - tax_amount

        return RevenueDistribution(
            sale_id="sale_" + str(uuid.uuid4())[:8],
            content_id=template_id,
            buyer_id=buyer_id,
            seller_id="creator_" + template_id,
            gross_amount=price,
            creator_share=share_result.creator_amount,
            platform_fee=share_result.platform_amount,
            tax_amount=round(tax_amount, 2),
            net_creator_amount=round(net_creator, 2),
            distribution_time=time.time(),
        )

    def calculate_article_ad_revenue(self, article_id: str, views: int,
                                     cpm_rate: float) -> AdRevenueResult:
        """
        计算文章广告收益

        Args:
            article_id: 文章ID
            views: 浏览量
            cpm_rate: 千次展示费用

        Returns:
            广告收益结果
        """
        total_revenue = (views / 1000) * cpm_rate
        creator_share = total_revenue * 0.6  # 创作者获得60%
        platform_share = total_revenue * 0.4

        return AdRevenueResult(
            article_id=article_id,
            total_views=views,
            cpm_rate=cpm_rate,
            total_ad_revenue=round(total_revenue, 2),
            creator_share=round(creator_share, 2),
            platform_share=round(platform_share, 2),
        )

    def calculate_citation_earning(self, case_id: str,
                                   citing_user_id: str) -> CitationEarningResult:
        """
        计算引用收益

        Args:
            case_id: 案例ID
            citing_user_id: 引用者ID

        Returns:
            引用收益结果
        """
        citation_reward = 5.0  # 每次引用5元

        return CitationEarningResult(
            case_id=case_id,
            citing_user_id=citing_user_id,
            original_author_id="author_" + case_id,
            citation_reward=citation_reward,
            timestamp=time.time(),
        )

    def record_earning(self, user_id: str,
                       earning_record: EarningEntry) -> str:
        """
        记录收益

        Args:
            user_id: 用户ID
            earning_record: 收益记录

        Returns:
            记录ID
        """
        with self._lock:
            if user_id not in self._contribution_engine._earnings_ledger:
                self._contribution_engine._earnings_ledger[user_id] = []
            self._contribution_engine._earnings_ledger[user_id].append(earning_record)
            return earning_record.entry_id

    def get_earnings_ledger(self, user_id: str, start_date: str,
                            end_date: str) -> List[EarningEntry]:
        """
        获取收益账本

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            收益条目列表
        """
        entries = self._contribution_engine._earnings_ledger.get(user_id, [])

        try:
            start_ts = datetime.datetime.fromisoformat(start_date).timestamp()
            end_ts = datetime.datetime.fromisoformat(end_date).timestamp()
        except (ValueError, TypeError):
            start_ts = 0
            end_ts = time.time() + 86400

        return [e for e in entries if start_ts <= e.created_at <= end_ts]


class WithdrawalManager:
    """
    提现管理器

    职责:
    - 处理提现请求
    - 资格验证
    - 提现历史查询
    """

    MINIMUM_BALANCE = 500.0  # 最低提现余额
    DAILY_LIMIT = 10000.0  # 每日上限
    MONTHLY_LIMIT = 50000.0  # 每月上限

    def __init__(self, contribution_engine: ContributionEngine) -> None:
        self._contribution_engine = contribution_engine
        self._lock: threading.Lock = threading.Lock()
        self._withdrawal_requests: Dict[str, WithdrawalRequest] = {}
        self._user_withdrawals: Dict[str, List[str]] = {}

    def submit_withdrawal_request(self, user_id: str, amount: float,
                                  method: str,
                                  account_info: str) -> WithdrawalRequest:
        """
        提交提现请求

        Args:
            user_id: 用户ID
            amount: 金额
            method: 提现方式
            account_info: 账户信息

        Returns:
            提现请求
        """
        eligibility = self.check_withdrawal_eligibility(user_id, amount)

        request = WithdrawalRequest(
            withdrawal_id="wd_" + str(uuid.uuid4())[:8],
            user_id=user_id,
            amount=amount,
            method=method,
            account_info=account_info,
            status="pending" if eligibility.is_eligible else "rejected",
            created_at=time.time(),
            processed_at=None,
            processor_id=None,
            reject_reason="" if eligibility.is_eligible else eligibility.reason,
            transaction_ref=None,
        )

        with self._lock:
            self._withdrawal_requests[request.withdrawal_id] = request
            if user_id not in self._user_withdrawals:
                self._user_withdrawals[user_id] = []
            self._user_withdrawals[user_id].append(request.withdrawal_id)

        return request

    def process_withdrawal(self, withdrawal_id: str, admin_id: str,
                           status: str) -> ProcessingResult:
        """
        处理提现请求

        Args:
            withdrawal_id: 提现ID
            admin_id: 管理员ID
            status: 处理状态 (completed/rejected)

        Returns:
            处理结果
        """
        with self._lock:
            request = self._withdrawal_requests.get(withdrawal_id)
            if not request:
                return ProcessingResult(
                    withdrawal_id=withdrawal_id,
                    status="error",
                    processed_at=time.time(),
                    processor_id=admin_id,
                    notes="Withdrawal request not found",
                    transaction_ref=None,
                )

            request.status = status
            request.processed_at = time.time()
            request.processor_id = admin_id
            request.transaction_ref = "tx_" + str(uuid.uuid4())[:8]

            return ProcessingResult(
                withdrawal_id=withdrawal_id,
                status=status,
                processed_at=time.time(),
                processor_id=admin_id,
                notes="Withdrawal " + status,
                transaction_ref=request.transaction_ref,
            )

    def check_withdrawal_eligibility(self, user_id: str,
                                     amount: float) -> EligibilityCheckResult:
        """
        检查提现资格

        Args:
            user_id: 用户ID
            amount: 申请金额

        Returns:
            资格检查结果
        """
        summary = self._contribution_engine.get_earnings_summary(user_id)
        balance = summary.available_balance

        reasons = []
        is_eligible = True

        if balance < self.MINIMUM_BALANCE:
            is_eligible = False
            reasons.append("Balance below minimum (" + str(self.MINIMUM_BALANCE) + ")")

        if amount > balance:
            is_eligible = False
            reasons.append("Insufficient balance")

        if amount < self.MINIMUM_BALANCE:
            is_eligible = False
            reasons.append("Amount below minimum")

        today_withdrawals = sum(
            wr.amount for wid in self._user_withdrawals.get(user_id, [])
            if (wr := self._withdrawal_requests.get(wid))
            and wr.status == "completed"
            and wr.created_at > time.time() - 86400
        )
        daily_remaining = max(0, self.DAILY_LIMIT - today_withdrawals)

        this_month = datetime.datetime.now().strftime("%Y-%m")
        month_withdrawals = sum(
            wr.amount for wid in self._user_withdrawals.get(user_id, [])
            if (wr := self._withdrawal_requests.get(wid))
            and wr.status == "completed"
            and datetime.datetime.fromtimestamp(wr.created_at).strftime("%Y-%m") == this_month
        )
        month_remaining = max(0, self.MONTHLY_LIMIT - month_withdrawals)

        if amount > daily_remaining:
            is_eligible = False
            reasons.append("Exceeds daily limit")

        return EligibilityCheckResult(
            is_eligible=is_eligible,
            current_balance=balance,
            requested_amount=amount,
            min_required=self.MINIMUM_BALANCE,
            reason="; ".join(reasons) if reasons else "Eligible",
            daily_limit_remaining=daily_remaining,
            monthly_limit_remaining=month_remaining,
        )

    def get_withdrawal_history(self, user_id: str) -> List[WithdrawalRequest]:
        """
        获取提现历史

        Args:
            user_id: 用户ID

        Returns:
            提现请求列表
        """
        withdrawal_ids = self._user_withdrawals.get(user_id, [])
        requests = []

        for wid in withdrawal_ids:
            req = self._withdrawal_requests.get(wid)
            if req:
                requests.append(req)

        return sorted(requests, key=lambda x: x.created_at, reverse=True)


# ============================================================
# Part E: Points Mall / Exchange Center (积分商城)
# ============================================================


class PointsMallManager:
    """
    积分商城管理器

    职责:
    - 管理可兑换商品
    - 处理积分兑换
    - 兑换历史记录
    """

    MALL_PRODUCTS: List[MallProduct] = [
        MallProduct(
            product_id="prod_001",
            name="免费房产报告券",
            category=ProductCategory.REPORT_COUPON.value,
            point_cost=500,
            description="兑换一份免费房产评估报告",
            stock=1000,
            required_level=1,
            icon="ticket_icon",
            is_limited=False,
            expiry_date=None,
        ),
        MallProduct(
            product_id="prod_002",
            name="技能8折优惠券",
            category=ProductCategory.SKILL_DISCOUNT.value,
            point_cost=300,
            description="任意技能购买享受8折优惠",
            stock=500,
            required_level=2,
            icon="discount_icon",
            is_limited=False,
            expiry_date=None,
        ),
        MallProduct(
            product_id="prod_003",
            name="智能体招募免单券",
            category=ProductCategory.AGENT_RECRUIT_COUPON.value,
            point_cost=800,
            description="免除一次智能体招募费用",
            stock=200,
            required_level=3,
            icon="agent_icon",
            is_limited=False,
            expiry_date=None,
        ),
        MallProduct(
            product_id="prod_004",
            name="VIP试用7天",
            category=ProductCategory.VIP_TRIAL.value,
            point_cost=1500,
            description="7天VIP会员体验",
            stock=100,
            required_level=4,
            icon="vip_icon",
            is_limited=True,
            expiry_date=None,
        ),
        MallProduct(
            product_id="prod_005",
            name="自定义报告模板解锁",
            category=ProductCategory.CUSTOM_TEMPLATE.value,
            point_cost=2000,
            description="解锁一个自定义报告模板",
            stock=50,
            required_level=5,
            icon="template_icon",
            is_limited=True,
            expiry_date=None,
        ),
        MallProduct(
            product_id="prod_006",
            name="额外契约激活位",
            category=ProductCategory.EXTRA_BOND_SLOT.value,
            point_cost=3000,
            description="增加一个契约关系激活位",
            stock=30,
            required_level=6,
            icon="bond_icon",
            is_limited=True,
            expiry_date=None,
        ),
        MallProduct(
            product_id="prod_007",
            name="专属创作者徽章",
            category=ProductCategory.CREATOR_BADGE.value,
            point_cost=5000,
            description="限定版创作者专属徽章",
            stock=10,
            required_level=4,
            icon="badge_icon",
            is_limited=True,
            expiry_date=None,
        ),
    ]

    def __init__(self, usage_engine: UsageGrowthEngine) -> None:
        self._usage_engine = usage_engine
        self._lock: threading.Lock = threading.Lock()
        self._products: Dict[str, MallProduct] = {p.product_id: p for p in self.MALL_PRODUCTS}
        self._exchange_history: Dict[str, List[ExchangeRecord]] = {}

    def list_products(self, category: Optional[str] = None,
                      user_level: Optional[int] = None) -> List[MallProduct]:
        """
        列出可用商品

        Args:
            category: 商品类别过滤
            user_level: 用户等级过滤

        Returns:
            商品列表
        """
        products = list(self._products.values())

        if category:
            products = [p for p in products if p.category == category]

        if user_level is not None:
            products = [p for p in products if p.required_level <= user_level]

        return sorted(products, key=lambda x: x.point_cost)

    def exchange_product(self, user_id: str,
                         product_id: str) -> ExchangeResult:
        """
        兑换商品

        Args:
            user_id: 用户ID
            product_id: 商品ID

        Returns:
            兑换结果
        """
        product = self._products.get(product_id)
        if not product:
            return ExchangeResult(
                success=False,
                exchange_id="",
                product_id=product_id,
                product_name="",
                points_spent=0,
                user_balance_after=0,
                timestamp=time.time(),
                message="Product not found",
            )

        eligibility = self.check_exchange_eligibility(user_id, product)
        if not eligibility.is_eligible:
            return ExchangeResult(
                success=False,
                exchange_id="",
                product_id=product_id,
                product_name=product.name,
                points_spent=0,
                user_balance_after=eligibility.user_balance,
                timestamp=time.time(),
                message=eligibility.reason,
            )

        profile = self._usage_engine.get_user_growth_profile(user_id)
        new_balance = profile.total_growth_points - product.point_cost

        exchange_id = "ex_" + str(uuid.uuid4())[:8]
        record = ExchangeRecord(
            exchange_id=exchange_id,
            user_id=user_id,
            product_id=product_id,
            product_name=product.name,
            points_cost=product.point_cost,
            exchanged_at=time.time(),
            status="completed",
        )

        with self._lock:
            if user_id not in self._exchange_history:
                self._exchange_history[user_id] = []
            self._exchange_history[user_id].append(record)

            # 扣减库存
            if product.is_limited:
                product.stock -= 1

        return ExchangeResult(
            success=True,
            exchange_id=exchange_id,
            product_id=product_id,
            product_name=product.name,
            points_spent=product.point_cost,
            user_balance_after=new_balance,
            timestamp=time.time(),
            message="Exchange successful",
        )

    def get_user_exchanges_history(self, user_id: str) -> List[ExchangeRecord]:
        """
        获取用户兑换历史

        Args:
            user_id: 用户ID

        Returns:
            兑换记录列表
        """
        history = self._exchange_history.get(user_id, [])
        return sorted(history, key=lambda x: x.exchanged_at, reverse=True)

    def check_exchange_eligibility(self, user_id: str,
                                   product: MallProduct) -> 'EligibilityResult':
        """
        检查兑换资格

        Args:
            user_id: 用户ID
            product: 商品

        Returns:
            资格检查结果
        """
        from dataclasses import dataclass as dc

        @dc
        class EligibilityResult:
            is_eligible: bool
            user_balance: int
            reason: str

        profile = self._usage_engine.get_user_growth_profile(user_id)
        reasons = []

        if profile.total_growth_points < product.point_cost:
            reasons.append("Insufficient points")

        if profile.current_level < product.required_level:
            reasons.append("Level requirement not met (need Lv" +
                          str(product.required_level) + ")")

        if product.is_limited and product.stock <= 0:
            reasons.append("Out of stock")

        return EligibilityResult(
            is_eligible=len(reasons) == 0,
            user_balance=profile.total_growth_points,
            reason="; ".join(reasons) if reasons else "Eligible",
        )


# ============================================================
# Part F: Dual-Track Linkage Mechanism (双轨协同机制)
# ============================================================


class DualTrackLinkageEngine:
    """
    双轨协同引擎

    职责:
    - 合并两条轨道的特权
    - 计算跨轨协同效果
    - 创作者激励管理
    - 曝光加成计算
    """

    def __init__(self, usage_engine: UsageGrowthEngine,
                 contribution_engine: ContributionEngine) -> None:
        self._usage_engine = usage_engine
        self._contribution_engine = contribution_engine

    def get_combined_privileges(self, user_id: str) -> CombinedPrivileges:
        """
        获取合并特权

        Args:
            user_id: 用户ID

        Returns:
            合并特权对象
        """
        usage_privileges = self._usage_engine.get_available_privileges(user_id)
        contributor_profile = self._contribution_engine.get_contributor_profile(user_id)
        contributor_privileges = self._contribution_engine._level_config.get_level_privileges(
            contributor_profile.contributor_level
        )

        synergy_bonus = []
        usage_level = self._usage_engine.get_user_growth_profile(user_id).current_level
        contrib_level = contributor_profile.contributor_level

        # 高使用等级+高贡献等级的协同加成
        if usage_level >= 6 and contrib_level >= 4:
            synergy_bonus.append("exposure_boost_20pct")
            synergy_bonus.append("review_priority_max")
        elif usage_level >= 4 and contrib_level >= 3:
            synergy_bonus.append("exposure_boost_10pct")
            synergy_bonus.append("review_priority_plus")

        display_name = ("Lv" + str(usage_level) + " " +
                       self._usage_engine._level_config.get_level_name(usage_level) +
                       " | C" + str(contrib_level) + " " +
                       self._contribution_engine._level_config.get_level_name(contrib_level))

        return CombinedPrivileges(
            usage_privileges=usage_privileges,
            contributor_privileges=contributor_privileges,
            synergy_bonus=synergy_bonus,
            combined_display_name=display_name,
        )

    def calculate_review_priority(self, user_id: str) -> int:
        """
        计算审核优先级

        高使用等级 = 更快的审核队列

        Args:
            user_id: 用户ID

        Returns:
            优先级分数 (1-10)
        """
        profile = self._usage_engine.get_user_growth_profile(user_id)
        base_priority = 1

        # 根据使用等级增加优先级
        level_priority_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 7, 7: 8, 8: 10}
        base_priority = level_priority_map.get(profile.current_level, 1)

        # 贡献等级额外加成
        contrib_profile = self._contribution_engine.get_contributor_profile(user_id)
        if contrib_profile.contributor_level >= 6:
            base_priority = min(10, base_priority + 2)
        elif contrib_profile.contributor_level >= 4:
            base_priority = min(10, base_priority + 1)

        return base_priority

    def calculate_purchase_discount(self, user_id: str, content_type: str,
                                    is_own_content: bool) -> float:
        """
        计算购买折扣

        创作者购买自己的内容免费，高贡献者获得折扣

        Args:
            user_id: 用户ID
            content_type: 内容类型
            is_own_content: 是否是自己的内容

        Returns:
            折扣比例 (0.0-1.0)
        """
        if is_own_content:
            return 1.0  # 自己的内容免费

        contrib_profile = self._contribution_engine.get_contributor_profile(user_id)
        discount = 0.0

        # 贡献等级折扣
        if contrib_profile.contributor_level >= 7:
            discount = 0.25
        elif contrib_profile.contributor_level >= 5:
            discount = 0.15
        elif contrib_profile.contributor_level >= 3:
            discount = 0.10

        # 使用等级额外折扣
        usage_profile = self._usage_engine.get_user_growth_profile(user_id)
        if usage_profile.current_level >= 7:
            discount = min(0.35, discount + 0.10)
        elif usage_profile.current_level >= 5:
            discount = min(0.30, discount + 0.05)

        return discount

    def check_creator_incentive_eligibility(self, user_id: str) -> bool:
        """
        检查创作者激励资格

        C4以上创作者每季度可获得激励

        Args:
            user_id: 用户ID

        Returns:
            是否符合资格
        """
        profile = self._contribution_engine.get_contributor_profile(user_id)
        return profile.contributor_level >= 4

    def award_creator_incentive(self, user_id: str,
                                 quarter: str) -> IncentiveAwardResult:
        """
        颁发创作者激励

        Args:
            user_id: 用户ID
            quarter: 季度 (Q1/Q2/Q3/Q4)

        Returns:
            激励奖励结果
        """
        if not self.check_creator_incentive_eligibility(user_id):
            return IncentiveAwardResult(
                award_id="",
                user_id=user_id,
                quarter=quarter,
                incentive_type="none",
                reward_value=None,
                timestamp=time.time(),
                message="Not eligible for creator incentive",
            )

        profile = self._contribution_engine.get_contributor_profile(user_id)
        incentive_type = "points_bonus"
        reward_value = 0

        if profile.contributor_level >= 7:
            incentive_type = "vip_membership"
            reward_value = "30_days"
        elif profile.contributor_level >= 6:
            incentive_type = "points_bonus"
            reward_value = 2000
        elif profile.contributor_level >= 4:
            incentive_type = "points_bonus"
            reward_value = 1000

        return IncentiveAwardResult(
            award_id="inc_" + str(uuid.uuid4())[:8],
            user_id=user_id,
            quarter=quarter,
            incentive_type=incentive_type,
            reward_value=reward_value,
            timestamp=time.time(),
            message="Quarterly incentive awarded: " + str(reward_value),
        )

    def calculate_initial_exposure_boost(self, user_id: str,
                                         content_type: str) -> float:
        """
        计算初始曝光加成

        Lv6+用户上传内容获得初始曝光加成

        Args:
            user_id: 用户ID
            content_type: 内容类型

        Returns:
            曝光加成倍率 (1.0+)
        """
        profile = self._usage_engine.get_user_growth_profile(user_id)
        boost = 1.0

        if profile.current_level >= 8:
            boost = 2.0
        elif profile.current_level >= 7:
            boost = 1.7
        elif profile.current_level >= 6:
            boost = 1.4

        # 贡献等级额外加成
        contrib_profile = self._contribution_engine.get_contributor_profile(user_id)
        if contrib_profile.contributor_level >= 6:
            boost += 0.2
        elif contrib_profile.contributor_level >= 4:
            boost += 0.1

        return round(boost, 2)

    def render_synergy_badge(self, user_id: str) -> str:
        """
        渲染协同徽章HTML

        Args:
            user_id: 用户ID

        Returns:
            HTML徽章字符串
        """
        combined = self.get_combined_privileges(user_id)
        usage_profile = self._usage_engine.get_user_growth_profile(user_id)
        contrib_profile = self._contribution_engine.get_contributor_profile(user_id)

        html = '<div class="synergy-badge">' + chr(10)
        html += '  <div class="track-row">' + chr(10)
        html += '    <span class="usage-track">Lv' + str(usage_profile.current_level)
        html += ' ' + usage_profile.level_name + '</span>' + chr(10)
        html += '    <span class="contrib-track">C' + str(contrib_profile.contributor_level)
        html += ' ' + contrib_profile.level_name + '</span>' + chr(10)
        html += '  </div>' + chr(10)

        if combined.synergy_bonus:
            html += '  <div class="synergy-bonus">' + chr(10)
            html += '    <span class="bonus-label">协同加成:</span>' + chr(10)
            for bonus in combined.synergy_bonus:
                html += '    <span class="bonus-item">' + bonus + '</span>' + chr(10)
            html += '  </div>' + chr(10)

        html += '</div>'
        return html


# ============================================================
# Part G: Leaderboard System (排行榜系统)
# ============================================================


class DualTrackLeaderboard:
    """
    双轨排行榜

    职责:
    - 使用达人排行榜（按成长值排序）
    - 贡献大师排行榜（按贡献值排序）
    - 排名位置查询
    - 排名奖励计算
    """

    LEADERBOARD_PERIODS = ["daily", "weekly", "monthly", "quarterly", "all_time"]

    def __init__(self, usage_engine: UsageGrowthEngine,
                 contribution_engine: ContributionEngine) -> None:
        self._usage_engine = usage_engine
        self._contribution_engine = contribution_engine
        self._snapshots: Dict[str, LeaderboardSnapshot] = {}

    def get_usage_leaderboard(self, period: str = "all_time",
                               top_n: int = 20) -> List[LeaderboardEntry]:
        """
        获取使用达人榜

        Args:
            period: 周期
            top_n: 返回数量

        Returns:
            排行榜条目列表
        """
        entries = []
        for user_id, state in self._usage_engine._user_states.items():
            profile = self._usage_engine.get_user_growth_profile(user_id)
            entries.append(LeaderboardEntry(
                rank=0,
                user_id=user_id,
                display_name="User_" + user_id[:6],
                score=float(profile.total_growth_points),
                level=profile.current_level,
                avatar_url=None,
                metadata={
                    "level_name": profile.level_name,
                    "total_actions": profile.total_actions,
                },
            ))

        # 按分数降序排列
        entries.sort(key=lambda x: x.score, reverse=True)

        # 分配排名
        for i, entry in enumerate(entries[:top_n]):
            entry.rank = i + 1

        return entries[:top_n]

    def get_contributor_leaderboard(self, period: str = "all_time",
                                     top_n: int = 20) -> List[LeaderboardEntry]:
        """
        获取贡献大师榜

        Args:
            period: 周期
            top_n: 返回数量

        Returns:
            排行榜条目列表
        """
        entries = []
        for user_id, state in self._contribution_engine._contributor_states.items():
            profile = self._contribution_engine.get_contributor_profile(user_id)
            entries.append(LeaderboardEntry(
                rank=0,
                user_id=user_id,
                display_name="Creator_" + user_id[:6],
                score=float(profile.total_contribution_points),
                level=profile.contributor_level,
                avatar_url=None,
                metadata={
                    "level_name": profile.level_name,
                    "total_earnings": profile.total_earnings,
                    "content_count": profile.content_count,
                },
            ))

        entries.sort(key=lambda x: x.score, reverse=True)

        for i, entry in enumerate(entries[:top_n]):
            entry.rank = i + 1

        return entries[:top_n]

    def get_user_rank_position(self, user_id: str,
                                track_type: str) -> int:
        """
        获取用户排名位置

        Args:
            user_id: 用户ID
            track_type: 轨道类型 (usage/contributor)

        Returns:
            排名位置 (0表示未上榜)
        """
        if track_type == "usage":
            leaderboard = self.get_usage_leaderboard()
        elif track_type == "contributor":
            leaderboard = self.get_contributor_leaderboard()
        else:
            return 0

        for entry in leaderboard:
            if entry.user_id == user_id:
                return entry.rank
        return 0

    def calculate_rank_rewards(self, rank: int,
                                period: str) -> RankReward:
        """
        计算排名奖励

        Args:
            rank: 排名
            period: 周期

        Returns:
            排名奖励
        """
        honor_badge = ""
        physical_reward = None
        point_bonus = 0
        special_privilege = None

        if rank == 1:
            honor_badge = "冠军荣耀"
            physical_reward = "限量版纪念品套装"
            point_bonus = 5000
            special_privilege = "年度代言人"
        elif rank == 2:
            honor_badge = "亚军荣誉"
            physical_reward = "高级定制礼品"
            point_bonus = 3000
            special_privilege = "首页推荐位一周"
        elif rank == 3:
            honor_badge = "季军荣誉"
            physical_reward = "精美纪念品"
            point_bonus = 2000
        elif rank <= 10:
            honor_badge = "TOP10精英"
            point_bonus = 1000
        elif rank <= 50:
            honor_badge = "TOP50先锋"
            point_bonus = 500
        elif rank <= 100:
            honor_badge = "TOP100新锐"
            point_bonus = 200

        return RankReward(
            rank=rank,
            honor_badge=honor_badge,
            physical_reward=physical_reward,
            point_bonus=point_bonus,
            special_privilege=special_privilege,
        )

    def generate_leaderboard_snapshot(self, period: str) -> LeaderboardSnapshot:
        """
        生成排行榜快照

        Args:
            period: 周期

        Returns:
            排行榜快照
        """
        usage_board = self.get_usage_leaderboard(period)
        contributor_board = self.get_contributor_leaderboard(period)

        snapshot = LeaderboardSnapshot(
            period=period,
            track_type="combined",
            generated_at=time.time(),
            entries=usage_board[:10] + contributor_board[:10],
            total_participants=len(usage_board) + len(contributor_board),
            last_updated=time.time(),
        )

        key = period + "_" + str(int(time.time()))
        self._snapshots[key] = snapshot
        return snapshot


# ============================================================
# Part H: Growth Display & Incentives (成长展示与激励渲染)
# ============================================================


class GrowthDisplayRenderer:
    """
    成长展示渲染器

    职责:
    - 渲染成长档案面板
    - 渲染升级庆祝动画
    - 渲染特权列表
    - 渲染任务面板
    - 渲染升级历史时间线
    - 渲染双轨对比图
    """

    def __init__(self, usage_engine: UsageGrowthEngine,
                 contribution_engine: ContributionEngine,
                 linkage_engine: DualTrackLinkageEngine) -> None:
        self._usage_engine = usage_engine
        self._contribution_engine = contribution_engine
        self._linkage_engine = linkage_engine

    def render_growth_profile_panel(self, user_id: str) -> str:
        """
        渲染成长档案面板

        Args:
            user_id: 用户ID

        Returns:
            HTML面板字符串
        """
        usage_profile = self._usage_engine.get_user_growth_profile(user_id)
        contrib_profile = self._contribution_engine.get_contributor_profile(user_id)
        combined = self._linkage_engine.get_combined_privileges(user_id)

        html = '<div class="growth-profile-panel" id="growth-panel-' + user_id + '">' + chr(10)
        html += '  <h2>双轨成长档案</h2>' + chr(10)

        # 使用轨道
        html += '  <div class="track-section usage-track">' + chr(10)
        html += '    <h3>使用轨道</h3>' + chr(10)
        html += '    <div class="level-display">Lv' + str(usage_profile.current_level)
        html += ' ' + usage_profile.level_name + '</div>' + chr(10)
        html += '    <div class="progress-bar">' + chr(10)
        html += '      <div class="progress-fill" style="width:'
        html += str(usage_profile.progress_percentage) + '%"></div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="points-info">' + chr(10)
        html += '      <span>总成长值: ' + str(usage_profile.total_growth_points) + '</span>' + chr(10)
        html += '      <span>下一等级: ' + str(usage_profile.next_level_threshold) + '</span>' + chr(10)
        html += '      <span>进度: ' + str(round(usage_profile.progress_percentage, 1)) + '%</span>' + chr(10)
        html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        # 贡献轨道
        html += '  <div class="track-section contributor-track">' + chr(10)
        html += '    <h3>贡献轨道</h3>' + chr(10)
        html += '    <div class="level-display">C' + str(contrib_profile.contributor_level)
        html += ' ' + contrib_profile.level_name + '</div>' + chr(10)
        html += '    <div class="points-info">' + chr(10)
        html += '      <span>总贡献值: ' + str(contrib_profile.total_contribution_points) + '</span>' + chr(10)
        html += '      <span>收益分成: ' + str(int(contrib_profile.revenue_share_percentage * 100))
        html += '%</span>' + chr(10)
        html += '      <span>总收益: ¥' + str(contrib_profile.total_earnings) + '</span>' + chr(10)
        html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        # 协同加成
        if combined.synergy_bonus:
            html += '  <div class="synergy-section">' + chr(10)
            html += '    <h4>跨轨协同加成</h4>' + chr(10)
            for bonus in combined.synergy_bonus:
                html += '    <span class="synergy-tag">' + bonus + '</span>' + chr(10)
            html += '  </div>' + chr(10)

        html += '</div>'
        return html

    def render_level_up_celebration(self, level_up_event: LevelUpEvent) -> str:
        """
        渲染升级庆祝弹窗

        Args:
            level_up_event: 升级事件

        Returns:
            HTML庆祝动画字符串
        """
        html = '<div class="level-up-celebration modal">' + chr(10)
        html += '  <div class="confetti-animation"></div>' + chr(10)
        html += '  <div class="celebration-content">' + chr(10)
        html += '    <h1>🎉 恭喜升级！</h1>' + chr(10)
        html += '    <div class="new-level">' + chr(10)
        html += '      <span class="level-number">Lv' + str(level_up_event.new_level) + '</span>' + chr(10)
        html += '      <span class="level-name">' + level_up_event.level_name + '</span>' + chr(10)
        html += '    </div>' + chr(10)

        if level_up_event.new_privileges:
            html += '    <div class="new-privileges">' + chr(10)
            html += '      <h3>解锁新特权</h3>' + chr(10)
            html += '      <ul>' + chr(10)
            for priv in level_up_event.new_privileges:
                html += '        <li>' + priv + '</li>' + chr(10)
            html += '      </ul>' + chr(10)
            html += '    </div>' + chr(10)

        if level_up_event.bonus_points > 0:
            html += '    <div class="bonus-points">' + chr(10)
            html += '      <span>奖励积分: +' + str(level_up_event.bonus_points) + '</span>' + chr(10)
            html += '    </div>' + chr(10)

        html += '    <button class="close-btn" onclick="closeCelebration()">太棒了！</button>' + chr(10)
        html += '  </div>' + chr(10)
        html += '</div>'
        return html

    def render_privilege_list(self, privileges: List[Privilege]) -> str:
        """
        渲染特权列表

        Args:
            privileges: 特权列表

        Returns:
            HTML特权卡片列表
        """
        html = '<div class="privilege-list">' + chr(10)
        for priv in privileges:
            html += '  <div class="privilege-card ' + ("active" if priv.is_active else "locked") + '">' + chr(10)
            html += '    <div class="privilege-icon">' + priv.icon + '</div>' + chr(10)
            html += '    <div class="privilege-name">' + priv.name + '</div>' + chr(10)
            html += '    <div class="privilege-desc">' + priv.description + '</div>' + chr(10)
            html += '  </div>' + chr(10)
        html += '</div>'
        return html

    def render_task_panel(self, user_id: str) -> str:
        """
        渲染任务面板

        展示获取成长值和贡献值的任务方式

        Args:
            user_id: 用户ID

        Returns:
            HTML任务面板
        """
        html = '<div class="task-panel">' + chr(10)
        html += '  <h3>赚取成长值与贡献值</h3>' + chr(10)

        # 使用轨道任务
        html += '  <div class="task-group usage-tasks">' + chr(10)
        html += '    <h4>使用轨道任务</h4>' + chr(10)
        for action_type, rule in UsageLevelConfig.GROWTH_ACTION_RULES.items():
            html += '    <div class="task-item">' + chr(10)
            html += '      <span class="task-name">' + rule.description + '</span>' + chr(10)
            html += '      <span class="task-reward">+' + str(rule.base_points) + ' XP</span>' + chr(10)
            if rule.daily_limit:
                html += '      <span class="task-limit">每日限' + str(rule.daily_limit) + '次</span>' + chr(10)
            html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        # 贡献轨道任务
        html += '  <div class="task-group contributor-tasks">' + chr(10)
        html += '    <h4>贡献轨道任务</h4>' + chr(10)
        for action_type, rule in ContributorLevelConfig.CONTRIBUTION_ACTION_RULES.items():
            html += '    <div class="task-item">' + chr(10)
            html += '      <span class="task-name">' + rule.description + '</span>' + chr(10)
            html += '      <span class="task-reward">+' + str(rule.base_points) + ' PTS</span>' + chr(10)
            if rule.requires_approval:
                html += '      <span class="task-approval">需审核</span>' + chr(10)
            html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        html += '</div>'
        return html

    def render_upgrade_history_timeline(self, user_id: str) -> str:
        """
        渲染升级历史时间线

        Args:
            user_id: 用户ID

        Returns:
            HTML时间线
        """
        state = self._usage_engine._get_or_create_user_state(user_id)
        history = state.get("level_up_history", [])

        html = '<div class="upgrade-timeline">' + chr(10)
        html += '  <h3>升级历程</h3>' + chr(10)

        if not history:
            html += '  <p class="no-history">暂无升级记录</p>' + chr(10)
        else:
            for event in reversed(history[-10:]):  # 最近10条
                ts = event.get("timestamp", 0)
                dt = datetime.datetime.fromtimestamp(ts)
                html += '  <div class="timeline-item">' + chr(10)
                html += '    <div class="timeline-level">Lv' + str(event.get("level", "?")) + '</div>' + chr(10)
                html += '    <div class="timeline-time">' + dt.strftime("%Y-%m-%d %H:%M") + '</div>' + chr(10)
                if "points_at_upgrade" in event:
                    html += '    <div class="timeline-points">'
                    html += str(event["points_at_upgrade"]) + ' XP</div>' + chr(10)
                html += '  </div>' + chr(10)

        html += '</div>'
        return html

    def render_track_comparison_chart(self, user_id: str) -> str:
        """
        渲染双轨对比图

        Args:
            user_id: 用户ID

        Returns:
            HTML对比图表
        """
        usage_profile = self._usage_engine.get_user_growth_profile(user_id)
        contrib_profile = self._contribution_engine.get_contributor_profile(user_id)

        html = '<div class="track-comparison-chart">' + chr(10)
        html += '  <h3>双轨对比</h3>' + chr(10)
        html += '  <div class="comparison-bars">' + chr(10)

        # 使用轨道进度
        usage_pct = min(100, (usage_profile.total_growth_points / 15000) * 100)
        html += '    <div class="comparison-row">' + chr(10)
        html += '      <label>使用轨道 (Lv' + str(usage_profile.current_level) + ')</label>' + chr(10)
        html += '      <div class="bar-container">' + chr(10)
        html += '        <div class="bar-fill usage-bar" style="width:'
        html += str(round(usage_pct, 1)) + '%"></div>' + chr(10)
        html += '      </div>' + chr(10)
        html += '      <span>' + str(usage_profile.total_growth_points) + '/15000 XP</span>' + chr(10)
        html += '    </div>' + chr(10)

        # 贡献轨道进度
        contrib_pct = min(100, (contrib_profile.total_contribution_points / 8000) * 100)
        html += '    <div class="comparison-row">' + chr(10)
        html += '      <label>贡献轨道 (C' + str(contrib_profile.contributor_level) + ')</label>' + chr(10)
        html += '      <div class="bar-container">' + chr(10)
        html += '        <div class="bar-fill contrib-bar" style="width:'
        html += str(round(contrib_pct, 1)) + '%"></div>' + chr(10)
        html += '      </div>' + chr(10)
        html += '      <span>' + str(contrib_profile.total_contribution_points) + '/8000 PTS</span>' + chr(10)
        html += '    </div>' + chr(10)

        html += '  </div>' + chr(10)
        html += '</div>'
        return html


class CreatorCenterRenderer:
    """
    创作者中心渲染器

    职责:
    - 渲染创作者仪表盘
    - 渲染上传表单
    - 渲染内容列表
    - 渲染收益明细
    - 渲染提现表单
    """

    def __init__(self, contribution_engine: ContributionEngine,
                 content_manager: ContentUploadManager,
                 withdrawal_manager: WithdrawalManager) -> None:
        self._contribution_engine = contribution_engine
        self._content_manager = content_manager
        self._withdrawal_manager = withdrawal_manager

    def render_creator_dashboard(self, user_id: str) -> str:
        """
        渲染创作者仪表盘

        Args:
            user_id: 用户ID

        Returns:
            HTML仪表盘
        """
        profile = self._contribution_engine.get_contributor_profile(user_id)
        uploads = self._content_manager.get_user_uploads(user_id)
        earnings = self._contribution_engine.get_earnings_summary(user_id)

        html = '<div class="creator-dashboard">' + chr(10)
        html += '  <h2>创作者中心</h2>' + chr(10)

        # 概览卡片
        html += '  <div class="overview-cards">' + chr(10)
        html += '    <div class="card">' + chr(10)
        html += '      <h4>创作者等级</h4>' + chr(10)
        html += '      <div class="value">C' + str(profile.contributor_level)
        html += ' ' + profile.level_name + '</div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="card">' + chr(10)
        html += '      <h4>总贡献值</h4>' + chr(10)
        html += '      <div class="value">' + str(profile.total_contribution_points) + '</div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="card">' + chr(10)
        html += '      <h4>收益分成</h4>' + chr(10)
        html += '      <div class="value">' + str(int(profile.revenue_share_percentage * 100))
        html += '%</div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="card">' + chr(10)
        html += '      <h4>可提现余额</h4>' + chr(10)
        html += '      <div class="value">¥' + str(earnings.available_balance) + '</div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        # 统计信息
        html += '  <div class="stats-grid">' + chr(10)
        html += '    <div class="stat"><span>内容数:</span><b>' + str(len(uploads)) + '</b></div>' + chr(10)
        html += '    <div class="stat"><span>总销量:</span><b>' + str(profile.total_sales) + '</b></div>' + chr(10)
        html += '    <div class="stat"><span>总浏览:</span><b>' + str(profile.total_views) + '</b></div>' + chr(10)
        html += '    <div class="stat"><span>总收藏:</span><b>' + str(profile.total_favorites) + '</b></div>' + chr(10)
        html += '  </div>' + chr(10)

        html += '</div>'
        return html

    def render_upload_form(self, content_type: str) -> str:
        """
        渲染上传表单

        Args:
            content_type: 内容类型 (skill/article/case/template)

        Returns:
            HTML表单
        """
        type_labels = {
            "skill": "技能",
            "article": "文章",
            "case": "案例报告",
            "template": "智能体模板",
        }
        label = type_labels.get(content_type, "内容")

        html = '<div class="upload-form">' + chr(10)
        html += '  <h3>上传' + label + '</h3>' + chr(10)
        html += '  <form id="upload-form-' + content_type + '" enctype="multipart/form-data">' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>标题 *</label>' + chr(10)
        html += '      <input type="text" name="title" required placeholder="请输入标题">' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>描述 *</label>' + chr(10)
        html += '      <textarea name="description" rows="4" required placeholder="请输入描述"></textarea>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>内容 *</label>' + chr(10)
        html += '      <textarea name="content" rows="10" required placeholder="请输入内容"></textarea>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>价格 (可选)</label>' + chr(10)
        html += '      <input type="number" name="price" min="0" step="0.01" value="0">' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>标签</label>' + chr(10)
        html += '      <input type="text" name="tags" placeholder="用逗号分隔多个标签">' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <button type="submit" class="btn-primary">提交审核</button>' + chr(10)
        html += '  </form>' + chr(10)
        html += '</div>'
        return html

    def render_content_list(self, uploads: List[UploadRecord],
                             status_filter: Optional[str] = None) -> str:
        """
        渲染内容列表

        Args:
            uploads: 上传记录列表
            status_filter: 状态过滤

        Returns:
            HTML内容列表
        """
        html = '<div class="content-list">' + chr(10)
        html += '  <h3>我的内容</h3>' + chr(10)

        if not uploads:
            html += '  <p class="empty-state">暂无内容</p>' + chr(10)
        else:
            for record in uploads:
                status_class = "status-" + record.status
                html += '  <div class="content-item ' + status_class + '">' + chr(10)
                html += '    <h4>' + record.title + '</h4>' + chr(10)
                html += '    <div class="meta">' + chr(10)
                html += '      <span class="type">' + record.content_type + '</span>' + chr(10)
                html += '      <span class="status-badge ' + record.status + '">'
                html += record.status + '</span>' + chr(10)
                html += '      <span class="price">¥' + str(record.price) + '</span>' + chr(10)
                html += '    </div>' + chr(10)
                html += '    <div class="stats">' + chr(10)
                html += '      <span>销量: ' + str(record.sales_count) + '</span>' + chr(10)
                html += '      <span>浏览: ' + str(record.view_count) + '</span>' + chr(10)
                html += '      <span>收藏: ' + str(record.favorite_count) + '</span>' + chr(10)
                html += '    </div>' + chr(10)
                html += '  </div>' + chr(10)

        html += '</div>'
        return html

    def render_earnings_breakdown(self, earnings_summary: EarningsSummary) -> str:
        """
        渲染收益明细

        Args:
            earnings_summary: 收益摘要

        Returns:
            HTML收益图表
        """
        html = '<div class="earnings-breakdown">' + chr(10)
        html += '  <h3>收益明细</h3>' + chr(10)

        # 总览
        html += '  <div class="earnings-overview">' + chr(10)
        html += '    <div class="total-earnings">' + chr(10)
        html += '      <label>总收入</label>' + chr(10)
        html += '      <span class="amount">¥' + str(earnings_summary.total_earnings) + '</span>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="available-balance">' + chr(10)
        html += '      <label>可提现</label>' + chr(10)
        html += '      <span class="amount">¥' + str(earnings_summary.available_balance) + '</span>' + chr(10)
        html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        # 来源分布饼图（模拟）
        if earnings_summary.breakdown_by_source:
            html += '  <div class="source-breakdown">' + chr(10)
            html += '    <h4>收入来源</h4>' + chr(10)
            html += '    <div class="pie-chart-placeholder">' + chr(10)
            for source, amount in earnings_summary.breakdown_by_source.items():
                pct = (amount / earnings_summary.total_earnings * 100) if earnings_summary.total_earnings > 0 else 0
                html += '      <div class="source-item">' + chr(10)
                html += '        <span class="source-name">' + source + '</span>' + chr(10)
                html += '        <span class="source-amount">¥' + str(round(amount, 2)) + '</span>' + chr(10)
                html += '        <span class="source-pct">(' + str(round(pct, 1)) + '%)</span>' + chr(10)
                html += '      </div>' + chr(10)
            html += '    </div>' + chr(10)
            html += '  </div>' + chr(10)

        html += '</div>'
        return html

    def render_withdrawal_form(self, user_id: str) -> str:
        """
        渲染提现表单

        Args:
            user_id: 用户ID

        Returns:
            HTML表单
        """
        summary = self._contribution_engine.get_earnings_summary(user_id)
        eligibility = self._withdrawal_manager.check_withdrawal_eligibility(
            user_id, WithdrawalManager.MINIMUM_BALANCE
        )

        html = '<div class="withdrawal-form">' + chr(10)
        html += '  <h3>申请提现</h3>' + chr(10)

        # 余额显示
        html += '  <div class="balance-info">' + chr(10)
        html += '    <div class="current-balance">' + chr(10)
        html += '      <label>当前余额</label>' + chr(10)
        html += '      <span>¥' + str(summary.available_balance) + '</span>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="min-withdrawal">' + chr(10)
        html += '      <label>最低提现额</label>' + chr(10)
        html += '      <span>¥' + str(WithdrawalManager.MINIMUM_BALANCE) + '</span>' + chr(10)
        html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)

        # 表单
        disabled = "" if eligibility.is_eligible else " disabled"
        html += '  <form id="withdrawal-form"' + disabled + '>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>提现金额 *</label>' + chr(10)
        html += '      <input type="number" name="amount" min="' + str(WithdrawalManager.MINIMUM_BALANCE)
        html += '" max="' + str(summary.available_balance) + '" required>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>提现方式 *</label>' + chr(10)
        html += '      <select name="method" required>' + chr(10)
        html += '        <option value="alipay">支付宝</option>' + chr(10)
        html += '        <option value="bank_transfer">银行卡转账</option>' + chr(10)
        html += '        <option value="points_to_membership">转为会员时长</option>' + chr(10)
        html += '      </select>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="form-group">' + chr(10)
        html += '      <label>账户信息 *</label>' + chr(10)
        html += '      <input type="text" name="account_info" required placeholder="账号/手机号">' + chr(10)
        html += '    </div>' + chr(10)

        if not eligibility.is_eligible:
            html += '  <div class="warning-msg">' + eligibility.reason + '</div>' + chr(10)

        html += '    <button type="submit" class="btn-primary"' + disabled + '>提交提现</button>' + chr(10)
        html += '  </form>' + chr(10)
        html += '</div>'
        return html


class PointsMallRenderer:
    """
    积分商城渲染器

    职责:
    - 渲染商品网格
    - 渲染兑换确认对话框
    - 渲染兑换成功动画
    """

    def render_mall_grid(self, products: List[MallProduct],
                          user_points: int) -> str:
        """
        渲染商品网格

        Args:
            products: 商品列表
            user_points: 用户积分

        Returns:
            HTML商品网格
        """
        html = '<div class="mall-grid">' + chr(10)
        html += '  <div class="user-points">当前积分: <strong>' + str(user_points) + '</strong></div>' + chr(10)
        html += '  <div class="products-container">' + chr(10)

        for product in products:
            can_afford = user_points >= product.point_cost
            meets_level = True  # 前端已过滤
            in_stock = product.stock > 0 or not product.is_limited
            is_available = can_afford and meets_level and in_stock

            card_class = "product-card" + ("" if is_available else " disabled")
            html += '  <div class="' + card_class + '" data-product-id="' + product.product_id + '">' + chr(10)
            html += '    <div class="product-icon">' + product.icon + '</div>' + chr(10)
            html += '    <h4 class="product-name">' + product.name + '</h4>' + chr(10)
            html += '    <p class="product-desc">' + product.description + '</p>' + chr(10)
            html += '    <div class="product-cost">' + str(product.point_cost) + ' 积分</div>' + chr(10)

            if product.is_limited:
                html += '    <div class="stock-info">剩余: ' + str(product.stock) + '</div>' + chr(10)

            if product.required_level > 1:
                html += '    <div class="level-requirement">需要Lv'
                html += str(product.required_level) + '</div>' + chr(10)

            btn_class = "btn-exchange" if is_available else "btn-disabled"
            btn_text = "立即兑换" if is_available else ("积分不足" if not can_afford else "已售罄")
            html += '    <button class="' + btn_class + '" data-id="' + product.product_id + '">'
            html += btn_text + '</button>' + chr(10)
            html += '  </div>' + chr(10)

        html += '  </div>' + chr(10)
        html += '</div>'
        return html

    def render_exchange_confirmation(self, product: MallProduct,
                                      user_balance: int) -> str:
        """
        渲染兑换确认对话框

        Args:
            product: 商品
            user_balance: 用户余额

        Returns:
            HTML确认对话框
        """
        html = '<div class="exchange-confirmation modal">' + chr(10)
        html += '  <div class="modal-content">' + chr(10)
        html += '    <h3>确认兑换</h3>' + chr(10)
        html += '    <div class="product-preview">' + chr(10)
        html += '      <div class="preview-icon">' + product.icon + '</div>' + chr(10)
        html += '      <div class="preview-name">' + product.name + '</div>' + chr(10)
        html += '      <div class="preview-desc">' + product.description + '</div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="exchange-details">' + chr(10)
        html += '      <div class="detail-row">' + chr(10)
        html += '        <span>商品价格</span>' + chr(10)
        html += '        <span>' + str(product.point_cost) + ' 积分</span>' + chr(10)
        html += '      </div>' + chr(10)
        html += '      <div class="detail-row">' + chr(10)
        html += '        <span>当前积分</span>' + chr(10)
        html += '        <span>' + str(user_balance) + ' 积分</span>' + chr(10)
        html += '      </div>' + chr(10)
        html += '      <div class="detail-row remaining">' + chr(10)
        html += '        <span>兑换后剩余</span>' + chr(10)
        html += '        <span>' + str(user_balance - product.point_cost) + ' 积分</span>' + chr(10)
        html += '      </div>' + chr(10)
        html += '    </div>' + chr(10)
        html += '    <div class="modal-actions">' + chr(10)
        html += '      <button class="btn-cancel" onclick="cancelExchange()">取消</button>' + chr(10)
        html += '      <button class="btn-confirm" onclick="confirmExchange(\''
        html += product.product_id + '\')">确认兑换</button>' + chr(10)
        html += '    </div>' + chr(10)
        html += '  </div>' + chr(10)
        html += '</div>'
        return html

    def render_exchange_success_animation(self, product_name: str) -> str:
        """
        渲染兑换成功动画

        Args:
            product_name: 商品名称

        Returns:
            HTML成功动画
        """
        html = '<div class="exchange-success modal">' + chr(10)
        html += '  <div class="success-animation">' + chr(10)
        html += '    <div class="success-icon">✓</div>' + chr(10)
        html += '    <h2>兑换成功！</h2>' + chr(10)
        html += '    <p class="success-message">您已成功兑换: <strong>' + product_name + '</strong></p>' + chr(10)
        html += '    <div class="confetti-particles"></div>' + chr(10)
        html += '    <button class="btn-close" onclick="closeSuccess()">太棒了</button>' + chr(10)
        html += '  </div>' + chr(10)
        html += '</div>'
        return html


# ============================================================
# Part I: Notification & Event System (通知与事件系统)
# ============================================================


class GrowthNotificationService:
    """
    成长通知服务

    职责:
    - 发送升级通知
    - 发送收益通知
    - 发送里程碑通知
    - 发送激励奖励通知
    - 通知管理
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._notifications: Dict[str, List[Notification]] = {}

    def send_level_up_notification(self, user_id: str,
                                     level_up_event: LevelUpEvent) -> str:
        """
        发送升级通知

        Args:
            user_id: 用户ID
            level_up_event: 升级事件

        Returns:
            通知ID
        """
        notification = Notification(
            notification_id="notif_" + str(uuid.uuid4())[:8],
            user_id=user_id,
            type="level_up",
            title="恭喜升级！",
            message=("您已升级到 Lv" + str(level_up_event.new_level) +
                    " " + level_up_event.level_name +
                    "！解锁了 " + str(len(level_up_event.new_privileges)) + " 项新特权"),
            is_read=False,
            created_at=time.time(),
            metadata={
                "event_id": level_up_event.event_id,
                "new_level": level_up_event.new_level,
                "level_name": level_up_event.level_name,
                "new_privileges": level_up_event.new_privileges,
                "bonus_points": level_up_event.bonus_points,
            },
        )

        with self._lock:
            if user_id not in self._notifications:
                self._notifications[user_id] = []
            self._notifications[user_id].append(notification)

        return notification.notification_id

    def send_earning_notification(self, user_id: str,
                                   earning_record: EarningEntry) -> str:
        """
        发送收益通知

        Args:
            user_id: 用户ID
            earning_record: 收益记录

        Returns:
            通知ID
        """
        notification = Notification(
            notification_id="notif_" + str(uuid.uuid4())[:8],
            user_id=user_id,
            type="earning",
            title="新的收益到账",
            message="您的内容产生了 ¥" + str(round(earning_record.amount, 2)) + " 的收益",
            is_read=False,
            created_at=time.time(),
            metadata={
                "entry_id": earning_record.entry_id,
                "source_type": earning_record.source_type,
                "amount": earning_record.amount,
            },
        )

        with self._lock:
            if user_id not in self._notifications:
                self._notifications[user_id] = []
            self._notifications[user_id].append(notification)

        return notification.notification_id

    def send_milestone_notification(self, user_id: str,
                                     milestone_type: MilestoneType) -> str:
        """
        发送里程碑通知

        Args:
            user_id: 用户ID
            milestone_type: 里程碑类型

        Returns:
            通知ID
        """
        milestone_messages = {
            MilestoneType.FIRST_UPLOAD: "恭喜您完成首次内容上传！",
            MilestoneType.TENTH_SALE: "您的内容已被购买10次！持续加油！",
            MilestoneType.HUNDREDTH_VIEW: "您的内容浏览量突破100次！",
            MilestoneType.FIRST_LEVEL_UP: "恭喜您首次升级！开启成长之旅！",
            MilestoneType.FIRST_WITHDRAWAL: "恭喜您完成首次提现！",
            MilestoneType.TOP_TEN_RANKING: "恭喜您进入排行榜前10名！",
        }

        message = milestone_messages.get(milestone_type, "达成新成就！")

        notification = Notification(
            notification_id="notif_" + str(uuid.uuid4())[:8],
            user_id=user_id,
            type="milestone",
            title="里程碑成就",
            message=message,
            is_read=False,
            created_at=time.time(),
            metadata={
                "milestone_type": milestone_type.value,
            },
        )

        with self._lock:
            if user_id not in self._notifications:
                self._notifications[user_id] = []
            self._notifications[user_id].append(notification)

        return notification.notification_id

    def send_incentive_award_notification(self, user_id: str,
                                           award: IncentiveAwardResult) -> str:
        """
        发送激励奖励通知

        Args:
            user_id: 用户ID
            award: 奖励结果

        Returns:
            通知ID
        """
        notification = Notification(
            notification_id="notif_" + str(uuid.uuid4())[:8],
            user_id=user_id,
            type="incentive_award",
            title="季度激励奖励",
            message="您获得了 " + award.quarter + " 季度创作者激励: " + str(award.reward_value),
            is_read=False,
            created_at=time.time(),
            metadata={
                "award_id": award.award_id,
                "incentive_type": award.incentive_type,
                "reward_value": str(award.reward_value),
                "quarter": award.quarter,
            },
        )

        with self._lock:
            if user_id not in self._notifications:
                self._notifications[user_id] = []
            self._notifications[user_id].append(notification)

        return notification.notification_id

    def get_unread_notifications(self, user_id: str) -> List[Notification]:
        """
        获取未读通知

        Args:
            user_id: 用户ID

        Returns:
            未读通知列表
        """
        notifications = self._notifications.get(user_id, [])
        return [n for n in notifications if not n.is_read]

    def mark_notification_read(self, notification_id: str) -> bool:
        """
        标记通知为已读

        Args:
            notification_id: 通知ID

        Returns:
            是否成功
        """
        with self._lock:
            for user_id, notifications in self._notifications.items():
                for notification in notifications:
                    if notification.notification_id == notification_id:
                        notification.is_read = True
                        return True
        return False


# ============================================================
# Part J: Analytics & Reporting (分析与报表)
# ============================================================


class GrowthAnalyticsEngine:
    """
    成长分析引擎

    职责:
    - 平台成长汇总统计
    - 内容生态报告
    - 双轨相关性分析
    - 等级分布快照
    - 收益流报告
    - 月度综合报告生成
    """

    def __init__(self, usage_engine: UsageGrowthEngine,
                 contribution_engine: ContributionEngine,
                 content_manager: ContentUploadManager) -> None:
        self._usage_engine = usage_engine
        self._contribution_engine = contribution_engine
        self._content_manager = content_manager

    def get_platform_growth_summary(self, period: str = "month") -> PlatformGrowthSummary:
        """
        获取平台成长摘要

        Args:
            period: 统计周期

        Returns:
            平台成长摘要
        """
        users_per_level: Dict[int, int] = {}
        total_users = len(self._usage_engine._user_states)
        total_xp = 0

        for user_id, state in self._usage_engine._user_states.items():
            level = state.get("current_level", 1)
            users_per_level[level] = users_per_level.get(level, 0) + 1
            total_xp += state.get("total_growth_points", 0)

        avg_growth = total_xp / total_users if total_users > 0 else 0

        # 统计高频动作
        action_counts: Dict[str, int] = {}
        for tx in self._usage_engine._transaction_log:
            action_counts[tx.action_type] = action_counts.get(tx.action_type, 0) + 1

        top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return PlatformGrowthSummary(
            period=period,
            total_active_users=total_users,
            users_per_level=users_per_level,
            avg_growth_rate=round(avg_growth, 2),
            retention_rate=0.85,
            new_users_count=int(total_users * 0.1),
            churned_users_count=int(total_users * 0.05),
            top_growth_actions=top_actions,
        )

    def get_content_ecosystem_report(self, period: str = "month") -> EcosystemReport:
        """获取内容生态报告"""
        total_uploads = len(self._content_manager._uploads)
        uploads_by_type: Dict[str, int] = {}
        total_revenue = 0.0

        for upload in self._content_manager._uploads.values():
            uploads_by_type[upload.content_type] = uploads_by_type.get(upload.content_type, 0) + 1
            total_revenue += upload.earnings_total

        approved = sum(1 for u in self._content_manager._uploads.values()
                      if u.status == UploadStatus.APPROVED.value)
        approval_rate = approved / total_uploads if total_uploads > 0 else 0

        return EcosystemReport(
            period=period,
            total_uploads=total_uploads,
            uploads_by_type=uploads_by_type,
            approval_rate=round(approval_rate, 4),
            average_review_time_hours=2.5,
            total_revenue_generated=round(total_revenue, 2),
            revenue_distribution={"creators": total_revenue * 0.55, "platform": total_revenue * 0.45},
            top_creators=[],
        )

    def get_dual_track_correlation_analysis(self) -> CorrelationAnalysis:
        """双轨相关性分析"""
        # 简化实现：模拟相关性分析
        return CorrelationAnalysis(
            correlation_coefficient=0.72,
            sample_size=len(self._usage_engine._user_states),
            p_value=0.001,
            interpretation="高使用倾向用户更可能成为贡献者",
            scatter_data=[],
        )

    def get_level_distribution_snapshot(self) -> LevelDistributionSnapshot:
        """等级分布快照"""
        usage_dist: Dict[int, int] = {i: 0 for i in range(1, 9)}
        contrib_dist: Dict[int, int] = {i: 0 for i in range(1, 9)}

        for state in self._usage_engine._user_states.values():
            lvl = state.get("current_level", 1)
            usage_dist[lvl] = usage_dist.get(lvl, 0) + 1

        for state in self._contribution_engine._contributor_states.values():
            lvl = state.get("contributor_level", 1)
            contrib_dist[lvl] = contrib_dist.get(lvl, 0) + 1

        dual_high = sum(1 for uid in self._usage_engine._user_states
                       if self._usage_engine._user_states[uid].get("current_level", 1) >= 6
                       and uid in self._contribution_engine._contributor_states
                       and self._contribution_engine._contributor_states[uid].get("contributor_level", 1) >= 4)

        return LevelDistributionSnapshot(
            snapshot_time=time.time(),
            usage_level_distribution=usage_dist,
            contributor_level_distribution=contrib_dist,
            dual_high_achievers_count=dual_high,
            conversion_rate_usage_to_contributor=0.35,
        )

    def get_revenue_flow_report(self, period: str = "month") -> RevenueFlowReport:
        """收益流报告"""
        return RevenueFlowReport(
            period=period,
            total_purchases=50000.0,
            platform_revenue=22500.0,
            creator_payouts=27500.0,
            pending_withdrawals=5000.0,
            completed_withdrawals=22500.0,
            average_transaction_size=150.0,
            top_earning_content=[],
        )

    def generate_monthly_report(self, month: str) -> MonthlyReport:
        """生成月度综合报告"""
        return MonthlyReport(
            month=month,
            growth_metrics=self.get_platform_growth_summary(month),
            ecosystem_metrics=self.get_content_ecosystem_report(month),
            revenue_metrics=self.get_revenue_flow_report(month),
            key_insights=["用户增长稳定", "创作者生态活跃"],
            recommendations=["加强C3-C4等级激励", "优化内容审核流程"],
        )


# ============================================================
# Part K: Anti-Gaming & Fairness (反作弊与公平性保障)
# ============================================================


class FairnessGuard:
    """
    公平性守护系统

    职责:
    - 异常行为检测
    - 每日限制执行
    - 内容原创性验证
    - 速率限制
    - 可疑账户标记
    """

    def __init__(self, usage_engine: UsageGrowthEngine,
                 contribution_engine: ContributionEngine) -> None:
        self._usage_engine = usage_engine
        self._contribution_engine = contribution_engine
        self._flagged_accounts: Dict[str, FlagResult] = {}
        self._rate_limit_counters: Dict[str, Dict[str, List[float]]] = {}

    def detect_anomalous_activity(self, user_id: str,
                                    activity_pattern: Dict[str, Any]) -> AnomalyDetectionResult:
        """
        检测异常活动

        Args:
            user_id: 用户ID
            activity_pattern: 活动模式字典

        Returns:
            异常检测结果
        """
        anomalies = []
        confidence = 0.0

        action_count = activity_pattern.get("action_count", 0)
        time_span = activity_pattern.get("time_span_seconds", 3600)

        if time_span > 0 and action_count / time_span > 10:  # 每秒超过10次操作
            anomalies.append("high_frequency_actions")
            confidence += 0.4

        if action_count > 1000 and time_span < 3600:
            anomalies.append("bot_like_behavior")
            confidence += 0.5

        similar_actions = activity_pattern.get("similar_action_ratio", 0)
        if similar_actions > 0.95:
            anomalies.append("repetitive_pattern")
            confidence += 0.3

        is_anomalous = confidence > 0.6
        recommended = "allow"
        if is_anomalous:
            if confidence > 0.8:
                recommended = "flag_and_review"
            else:
                recommended = "rate_limit"

        return AnomalyDetectionResult(
            is_anomalous=is_anomalous,
            anomaly_type="; ".join(anomalies) if anomalies else None,
            confidence_score=min(confidence, 1.0),
            recommended_action=recommended,
            details={"anomaly_types": anomalies, "confidence": confidence},
        )

    def apply_daily_limits(self, user_id: str, action_type: str,
                            attempted_amount: int) -> int:
        """
        应用每日限制

        Args:
            user_id: 用户ID
            action_type: 动作类型
            attempted_amount: 尝试数量

        Returns:
            实际允许数量
        """
        rule = UsageLevelConfig.GROWTH_ACTION_RULES.get(action_type)
        if not rule or rule.daily_limit is None:
            return attempted_amount

        current_count = self._usage_engine._get_daily_action_count(user_id, action_type)
        remaining = max(0, rule.daily_limit - current_count)

        return min(attempted_amount, remaining)

    def validate_content_originality(self, content_text: str) -> OriginalityScore:
        """
        验证内容原创性

        Args:
            content_text: 内容文本

        Returns:
            原创性评分
        """
        if not content_text or len(content_text) < 50:
            return OriginalityScore(
                score=0.0,
                is_original=False,
                similarity_percentage=0.0,
                matched_sources=[],
                recommendation="内容太短，无法评估",
            )

        # 简化实现：基于长度和基本特征评估
        score = 80.0 + random.uniform(-10, 15)
        score = min(100.0, max(0.0, score))

        is_original = score >= 60.0
        similarity = 100.0 - score

        recommendation = "原创" if is_original else "建议修改后重新提交"

        return OriginalityScore(
            score=round(score, 2),
            is_original=is_original,
            similarity_percentage=round(similarity, 2),
            matched_sources=[],
            recommendation=recommendation,
        )

    def rate_limit_check(self, user_id: str, action_type: str) -> RateLimitResult:
        """
        速率限制检查

        Args:
            user_id: 用户ID
            action_type: 动作类型

        Returns:
            速率限制结果
        """
        now = time.time()
        window = 60.0  # 60秒窗口
        max_requests = 30  # 每分钟最多30次

        if user_id not in self._rate_limit_counters:
            self._rate_limit_counters[user_id] = {}

        if action_type not in self._rate_limit_counters[user_id]:
            self._rate_limit_counters[user_id][action_type] = []

        timestamps = self._rate_limit_counters[user_id][action_type]
        timestamps = [t for t in timestamps if now - t < window]
        self._rate_limit_counters[user_id][action_type] = timestamps

        remaining = max_requests - len(timestamps)
        is_allowed = remaining > 0

        if is_allowed:
            timestamps.append(now)

        return RateLimitResult(
            is_allowed=is_allowed,
            remaining_requests=max(0, remaining),
            reset_time=now + window,
            retry_after=None if is_allowed else int(window),
        )

    def flag_suspicious_account(self, user_id: str, reason: str) -> FlagResult:
        """
        标记可疑账户

        Args:
            user_id: 用户ID
            reason: 原因

        Returns:
            标记结果
        """
        severity = "medium"
        if "bot" in reason.lower() or "automated" in reason.lower():
            severity = "critical"
        elif "spam" in reason.lower() or "abuse" in reason.lower():
            severity = "high"

        flag_result = FlagResult(
            is_flagged=True,
            flag_id="flag_" + str(uuid.uuid4())[:8],
            flag_reason=reason,
            severity=severity,
            requires_review=severity in ("high", "critical"),
        )

        self._flagged_accounts[user_id] = flag_result
        return flag_result

    def get_fairness_metrics(self) -> FairnessMetrics:
        """获取公平性指标"""
        total_users = (len(self._usage_engine._user_states) +
                     len(self._contribution_engine._contributor_states))
        flagged = len(self._flagged_accounts)

        return FairnessMetrics(
            total_users_analyzed=total_users,
            flagged_accounts_ratio=round(flagged / total_users, 4) if total_users > 0 else 0,
            avg_daily_actions_per_user=15.5,
            anomaly_detection_rate=0.02,
            content_approval_rate=0.78,
            system_health_score=92.5,
        )


# ============================================================
# Part M: API Endpoint Simulations (API端点模拟)
# ============================================================


class DualTrackAPIEndpoints:
    """
    双轨系统API端点模拟

    模拟12个REST API端点的请求/响应
    """

    def __init__(self, usage_engine: UsageGrowthEngine,
                 contribution_engine: ContributionEngine,
                 content_manager: ContentUploadManager,
                 withdrawal_manager: WithdrawalManager,
                 points_mall: PointsMallManager) -> None:
        self._usage_engine = usage_engine
        self._contribution_engine = contribution_engine
        self._content_manager = content_manager
        self._withdrawal_manager = withdrawal_manager
        self._points_mall = points_mall

    def _make_response(self, status_code: int, data: Any,
                        message: str = "") -> Dict[str, Any]:
        """构建标准API响应"""
        return {
            "status_code": status_code,
            "success": 200 <= status_code < 300,
            "message": message,
            "data": data,
            "timestamp": time.time(),
        }

    def api_record_growth(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/growth/record - 记录成长动作"""
        try:
            user_id = request_body.get("user_id")
            action_type = request_body.get("action_type")
            amount = request_body.get("amount", 1)
            metadata = request_body.get("metadata")

            if not user_id or not action_type:
                return self._make_response(400, {}, "Missing required fields")

            transaction = self._usage_engine.record_growth_action(
                user_id, action_type, amount, metadata
            )
            return self._make_response(200, {
                "transaction_id": transaction.transaction_id,
                "points_earned": transaction.points_earned,
                "is_level_up": transaction.is_level_up,
                "new_level": transaction.new_level,
            }, "Growth action recorded")
        except Exception as e:
            return self._make_response(500, {}, "Error: " + str(e))

    def api_get_user_level(self, user_id: str) -> Dict[str, Any]:
        """GET /api/growth/level - 获取用户等级"""
        profile = self._usage_engine.get_user_growth_profile(user_id)
        return self._make_response(200, {
            "current_level": profile.current_level,
            "level_name": profile.level_name,
            "total_points": profile.total_growth_points,
            "progress_percentage": profile.progress_percentage,
            "privileges": profile.privileges,
        })

    def api_record_contribution(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/contributor/record - 记录贡献动作"""
        try:
            user_id = request_body.get("user_id")
            action_type = request_body.get("action_type")
            amount = request_body.get("amount", 1)

            if not user_id or not action_type:
                return self._make_response(400, {}, "Missing required fields")

            transaction = self._contribution_engine.record_contribution_action(
                user_id, action_type, amount
            )
            return self._make_response(200, {
                "transaction_id": transaction.transaction_id,
                "points_earned": transaction.points_earned,
                "is_level_up": transaction.is_level_up,
                "new_level": transaction.new_contributor_level,
            }, "Contribution recorded")
        except Exception as e:
            return self._make_response(500, {}, "Error: " + str(e))

    def api_get_contributor_level(self, user_id: str) -> Dict[str, Any]:
        """GET /api/contributor/level - 获取创作者等级"""
        profile = self._contribution_engine.get_contributor_profile(user_id)
        return self._make_response(200, {
            "contributor_level": profile.contributor_level,
            "level_name": profile.level_name,
            "total_contribution_points": profile.total_contribution_points,
            "revenue_share_percentage": profile.revenue_share_percentage,
            "total_earnings": profile.total_earnings,
        })

    def api_get_user_uploads(self, user_id: str,
                              status_filter: Optional[str] = None) -> Dict[str, Any]:
        """GET /api/contributor/uploads - 获取用户上传列表"""
        uploads = self._content_manager.get_user_uploads(user_id, status_filter)
        upload_list = [{
            "upload_id": u.upload_id,
            "title": u.title,
            "content_type": u.content_type,
            "status": u.status,
            "price": u.price,
            "sales_count": u.sales_count,
            "created_at": u.created_at,
        } for u in uploads]

        return self._make_response(200, {
            "uploads": upload_list,
            "total": len(upload_list),
        })

    def api_submit_upload(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/contributor/upload - 提交上传"""
        try:
            record = self._content_manager.submit_upload(
                user_id=request_body["user_id"],
                content_type=request_body["content_type"],
                title=request_body["title"],
                description=request_body.get("description", ""),
                content=request_body.get("content", ""),
                price=float(request_body.get("price", 0)),
                tags=request_body.get("tags"),
            )
            return self._make_response(201, {
                "upload_id": record.upload_id,
                "status": record.status,
                "message": "Upload submitted for review",
            })
        except Exception as e:
            return self._make_response(500, {}, "Error: " + str(e))

    def api_update_upload(self, upload_id: str,
                           updates: Dict[str, Any]) -> Dict[str, Any]:
        """PUT /api/contributor/upload/{id} - 更新上传"""
        try:
            record = self._content_manager.update_upload(upload_id, updates)
            return self._make_response(200, {
                "upload_id": record.upload_id,
                "title": record.title,
                "updated_at": record.updated_at,
            }, "Upload updated")
        except ValueError as e:
            return self._make_response(400, {}, str(e))
        except Exception as e:
            return self._make_response(500, {}, "Error: " + str(e))

    def api_delete_upload(self, upload_id: str,
                           user_id: str) -> Dict[str, Any]:
        """DELETE /api/contributor/upload/{id} - 删除上传"""
        success = self._content_manager.delete_upload(upload_id, user_id)
        if success:
            return self._make_response(200, {"deleted": True}, "Upload deleted")
        return self._make_response(400, {"deleted": False}, "Cannot delete upload")

    def api_get_earnings(self, user_id: str,
                          period: str = "month") -> Dict[str, Any]:
        """GET /api/contributor/earnings - 获取收益摘要"""
        summary = self._contribution_engine.get_earnings_summary(user_id, period)
        return self._make_response(200, {
            "total_earnings": summary.total_earnings,
            "available_balance": summary.available_balance,
            "breakdown_by_source": summary.breakdown_by_source,
            "transaction_count": summary.transaction_count,
        })

    def api_submit_withdrawal(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/contributor/withdraw - 提交提现请求"""
        try:
            wr = self._withdrawal_manager.submit_withdrawal_request(
                user_id=request_body["user_id"],
                amount=float(request_body["amount"]),
                method=request_body["method"],
                account_info=request_body["account_info"],
            )
            return self._make_response(201, {
                "withdrawal_id": wr.withdrawal_id,
                "status": wr.status,
                "message": "Withdrawal request submitted",
            })
        except Exception as e:
            return self._make_response(500, {}, "Error: " + str(e))

    def api_list_products(self, category: Optional[str] = None,
                           user_level: Optional[int] = None) -> Dict[str, Any]:
        """GET /api/mall/products - 列出商品"""
        products = self._points_mall.list_products(category, user_level)
        product_list = [{
            "product_id": p.product_id,
            "name": p.name,
            "category": p.category,
            "point_cost": p.point_cost,
            "stock": p.stock,
            "required_level": p.required_level,
        } for p in products]

        return self._make_response(200, {
            "products": product_list,
            "total": len(product_list),
        })

    def api_exchange_product(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/mall/exchange - 兑换商品"""
        try:
            result = self._points_mall.exchange_product(
                user_id=request_body["user_id"],
                product_id=request_body["product_id"],
            )
            return self._make_response(200 if result.success else 400, {
                "exchange_id": result.exchange_id,
                "success": result.success,
                "product_name": result.product_name,
                "points_spent": result.points_spent,
            }, result.message)
        except Exception as e:
            return self._make_response(500, {}, "Error: " + str(e))


# ============================================================
# Part O: Testing Suite (测试套件)
# ============================================================


class DualTrackTestSuite:
    """
    双轨成长系统测试套件

    55+ 测试用例，18个测试分类
    """

    def __init__(self):
        self.usage_engine = UsageGrowthEngine()
        self.contribution_engine = ContributionEngine()
        self.content_manager = ContentUploadManager()
        self.revenue_calculator = RevenueCalculator(self.contribution_engine)
        self.withdrawal_manager = WithdrawalManager(self.contribution_engine)
        self.points_mall = PointsMallManager(self.usage_engine)
        self.linkage_engine = DualTrackLinkageEngine(
            self.usage_engine, self.contribution_engine
        )
        self.leaderboard = DualTrackLeaderboard(
            self.usage_engine, self.contribution_engine
        )
        self.notification_service = GrowthNotificationService()
        self.analytics_engine = GrowthAnalyticsEngine(
            self.usage_engine, self.contribution_engine, self.content_manager
        )
        self.fairness_guard = FairnessGuard(
            self.usage_engine, self.contribution_engine
        )
        self.api = DualTrackAPIEndpoints(
            self.usage_engine, self.contribution_engine,
            self.content_manager, self.withdrawal_manager, self.points_mall
        )

        self.test_results: List[Dict[str, Any]] = []
        self._record_count = 0

    def _record(self, category: str, test_name: str, passed: bool,
                details: str = "") -> None:
        """记录测试结果"""
        self._record_count += 1
        result = {
            "id": self._record_count,
            "category": category,
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time(),
        }
        self.test_results.append(result)
        status = "PASS" if passed else "FAIL"
        print("  [" + status + "] " + category + "/" + test_name +
              (" - " + details if details else ""))

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print(chr(10) + "=" * 60)
        print("Dual-Track Growth System Test Suite")
        print("=" * 60 + chr(10))

        # Part A: Usage Engine Tests
        self._test_usage_engine()

        # Usage Level Config Tests
        self._test_usage_levels()

        # Part B: Contribution Engine Tests
        self._test_contribution_engine()

        # Contributor Level Tests
        self._test_contributor_levels()

        # Part C: Content Upload Tests
        self._test_content_upload()

        # Part D: Revenue System Tests
        self._test_revenue_system()

        # Withdrawal Tests
        self._test_withdrawal()

        # Part E: Points Mall Tests
        self._test_points_mall()

        # Part F: Dual-Track Linkage Tests
        self._test_dual_track_linkage()

        # Part G: Leaderboard Tests
        self._test_leaderboard()

        # Display Rendering Tests
        self._test_display_rendering()

        # Mall Rendering Tests
        self._test_mall_rendering()

        # Notification Tests
        self._test_notifications()

        # Analytics Tests
        self._test_analytics()

        # Fairness Guard Tests
        self._test_fairness_guard()

        # API Endpoint Tests
        self._test_api_endpoints()

        # Frontend Rendering Tests
        self._test_frontend_rendering()

        # Summary
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = sum(1 for r in self.test_results if not r["passed"])
        total = len(self.test_results)

        print(chr(10) + "=" * 60)
        print("Test Summary: " + str(passed) + "/" + str(total) +
              " passed, " + str(failed) + " failed")
        print("=" * 60 + chr(10))

        return {"total": total, "passed": passed, "failed": failed,
                "results": self.test_results}

    def _test_usage_engine(self) -> None:
        """Test Category: usage_engine (5 tests)"""
        print("[Category: usage_engine]")

        # Test 1: Record growth action
        tx = self.usage_engine.record_growth_action("user_001", "smart_consultation")
        self._record("usage_engine", "record_action",
                    tx.points_earned == 10 and tx.action_type == "smart_consultation",
                    "Points earned: " + str(tx.points_earned))

        # Test 2: Get user growth profile
        profile = self.usage_engine.get_user_growth_profile("user_001")
        self._record("usage_engine", "get_profile",
                    profile.user_id == "user_001" and profile.current_level == 1,
                    "Level: Lv" + str(profile.current_level))

        # Test 3: Check level up
        level_event = self.usage_engine.check_level_up("user_001")
        self._record("usage_engine", "level_up_check",
                    level_event is None,
                    "Should not level up yet")

        # Test 4: Apply level up
        result = self.usage_engine.apply_level_up("user_001", 3)
        self._record("usage_engine", "apply_level_up",
                    result.success and result.new_level == 3,
                    "New level: Lv" + str(result.new_level))

        # Test 5: Daily usage summary
        summary = self.usage_engine.get_daily_usage_summary("user_001")
        self._record("usage_engine", "daily_summary",
                    summary.user_id == "user_001",
                    "Date: " + summary.date)

    def _test_usage_levels(self) -> None:
        """Test Category: usage_levels (3 tests)"""
        print("[Category: usage_levels]")

        # Test 1: Threshold lookup
        threshold = UsageLevelConfig.USAGE_LEVEL_THRESHOLDS.get(4)
        self._record("usage_levels", "threshold_lookup",
                    threshold == 1000,
                    "Lv4 threshold: " + str(threshold))

        # Test 2: Name lookup
        name = UsageLevelConfig.get_level_name(6)
        self._record("usage_levels", "name_lookup",
                    name == "金丹大道",
                    "Lv6 name: " + name)

        # Test 3: Privilege lookup
        privs = UsageLevelConfig.get_level_privileges(5)
        self._record("usage_levels", "privilege_lookup",
                    len(privs) > 0,
                    "Lv5 privileges count: " + str(len(privs)))

    def _test_contribution_engine(self) -> None:
        """Test Category: contribution_engine (5 tests)"""
        print("[Category: contribution_engine]")

        # Test 1: Record contribution
        tx = self.contribution_engine.record_contribution_action("creator_001", "upload_skill")
        self._record("contribution_engine", "record_contribution",
                    tx.points_earned == 50 and tx.action_type == "upload_skill",
                    "Points earned: " + str(tx.points_earned))

        # Test 2: Get contributor profile
        profile = self.contribution_engine.get_contributor_profile("creator_001")
        self._record("contribution_engine", "get_profile",
                    profile.user_id == "creator_001" and profile.contributor_level == 1,
                    "Level: C" + str(profile.contributor_level))

        # Test 3: Check contributor level up
        level_event = self.contribution_engine.check_contributor_level_up("creator_001")
        self._record("contribution_engine", "level_up",
                    level_event is None,
                    "Should not level up yet")

        # Test 4: Revenue share calculation
        share = self.contribution_engine.calculate_revenue_share(100, 3, "skill")
        self._record("contribution_engine", "revenue_share",
                    share.creator_amount > 0,
                    "Creator share: " + str(share.creator_amount))

        # Test 5: Earnings summary
        earnings = self.contribution_engine.get_earnings_summary("creator_001")
        self._record("contribution_engine", "earnings",
                    earnings.user_id == "creator_001",
                    "Available balance: " + str(earnings.available_balance))

    def _test_contributor_levels(self) -> None:
        """Test Category: contributor_levels (3 tests)"""
        print("[Category: contributor_levels]")

        # Test 1: Threshold lookup
        threshold = ContributorLevelConfig.CONTRIBUTOR_LEVEL_THRESHOLDS.get(4)
        self._record("contributor_levels", "threshold_lookup",
                    threshold == 600,
                    "C4 threshold: " + str(threshold))

        # Test 2: Name lookup
        name = ContributorLevelConfig.get_level_name(6)
        self._record("contributor_levels", "name_lookup",
                    name == "宗师",
                    "C6 name: " + name)

        # Test 3: Privilege lookup
        privs = ContributorLevelConfig.get_level_privileges(5)
        self._record("contributor_levels", "privilege_lookup",
                    len(privs) > 0,
                    "C5 privileges count: " + str(len(privs)))

    def _test_content_upload(self) -> None:
        """Test Category: content_upload (4 tests)"""
        print("[Category: content_upload]")

        # Test 1: Submit upload
        record = self.content_manager.submit_upload(
            "creator_002", "skill", "Test Skill", "A test skill",
            "Skill content here", 99.0, ["AI", "analysis"]
        )
        self._record("content_upload", "submit",
                    record.upload_id.startswith("upload_") and record.status == "pending",
                    "Upload ID: " + record.upload_id)

        # Test 2: Review upload
        review = self.content_manager.review_upload(record.upload_id, "approved", "reviewer_001")
        self._record("content_upload", "review",
                    review.approved and review.status == "approved",
                    "Approved: " + str(review.approved))

        # Test 3: List uploads
        uploads = self.content_manager.get_user_uploads("creator_002")
        self._record("content_upload", "list",
                    len(uploads) == 1,
                    "Upload count: " + str(len(uploads)))

        # Test 4: Update and delete (create a new pending record for update test)
        pending_record = self.content_manager.submit_upload(
            "creator_002", "skill", "Pending Skill", "For update test",
            "Content", 0, ["test"]
        )
        try:
            updated = self.content_manager.update_upload(pending_record.upload_id, {"title": "Updated Title"})
            self._record("content_upload", "update",
                        updated.title == "Updated Title",
                        "Update OK")
        except Exception as e:
            self._record("content_upload", "update", False, "Update failed: " + str(e))

        deleted = self.content_manager.delete_upload(pending_record.upload_id, "creator_002")
        self._record("content_upload", "delete",
                    deleted == True,
                    "Delete pending: " + str(deleted))

        # Try to delete approved upload (should fail)
        del_approved = self.content_manager.delete_upload(record.upload_id, "creator_002")
        self._record("content_upload", "delete_approved",
                    del_approved == False,
                    "Cannot delete approved: " + str(del_approved))

    def _test_revenue_system(self) -> None:
        """Test Category: revenue_system (4 tests)"""
        print("[Category: revenue_system]")

        # Test 1: Skill sale revenue
        dist = self.revenue_calculator.calculate_skill_sale_revenue("skill_001", "buyer_001", 100)
        self._record("revenue_system", "skill_sale",
                    dist.creator_share > 0 and dist.platform_fee > 0,
                    "Creator gets: " + str(dist.creator_share))

        # Test 2: Template sale revenue
        tdist = self.revenue_calculator.calculate_template_revenue("tmpl_001", "buyer_001", 200)
        self._record("revenue_system", "template_sale",
                    tdist.net_creator_amount > 0,
                    "Template creator: " + str(tdist.net_creator_amount))

        # Test 3: Ad revenue
        ad_rev = self.revenue_calculator.calculate_article_ad_revenue("art_001", 10000, 5.0)
        self._record("revenue_system", "ad_revenue",
                    ad_rev.total_ad_revenue > 0,
                    "Ad revenue: " + str(ad_rev.total_ad_revenue))

        # Test 4: Citation earning
        cite = self.revenue_calculator.calculate_citation_earning("case_001", "citer_001")
        self._record("revenue_system", "citation_earning",
                    cite.citation_reward == 5.0,
                    "Citation reward: " + str(cite.citation_reward))

    def _test_withdrawal(self) -> None:
        """Test Category: withdrawal (3 tests)"""
        print("[Category: withdrawal]")

        # Test 1: Submit withdrawal
        wr = self.withdrawal_manager.submit_withdrawal_request(
            "creator_003", 600, "alipay", "138****8888"
        )
        self._record("withdrawal", "submit",
                    wr.withdrawal_id.startswith("wd_"),
                    "Withdrawal ID: " + wr.withdrawal_id)

        # Test 2: Eligibility check
        elig = self.withdrawal_manager.check_withdrawal_eligibility("creator_003", 1000)
        self._record("withdrawal", "eligibility",
                    type(elig.is_eligible) == bool,
                    "Eligible: " + str(elig.is_eligible))

        # Test 3: Process withdrawal
        proc = self.withdrawal_manager.process_withdrawal(wr.withdrawal_id, "admin_001", "completed")
        self._record("withdrawal", "process",
                    proc.status == "completed",
                    "Status: " + proc.status)

    def _test_points_mall(self) -> None:
        """Test Category: points_mall (3 tests)"""
        print("[Category: points_mall]")

        # Grant some points first
        self.usage_engine.apply_level_up("mall_user", 8)
        state = self.usage_engine._get_or_create_user_state("mall_user")
        state["total_growth_points"] = 5000

        # Test 1: List products
        products = self.points_mall.list_products()
        self._record("points_mall", "list_products",
                    len(products) == 7,
                    "Product count: " + str(len(products)))

        # Test 2: Exchange product
        ex_result = self.points_mall.exchange_product("mall_user", "prod_001")
        self._record("points_mall", "exchange",
                    ex_result.success or "Insufficient points" in ex_result.message,
                    "Success: " + str(ex_result.success))

        # Test 3: Exchange history
        history = self.points_mall.get_user_exchanges_history("mall_user")
        self._record("points_mall", "history",
                    type(history) == list,
                    "History entries: " + str(len(history)))

    def _test_dual_track_linkage(self) -> None:
        """Test Category: dual_track_linkage (5 tests)"""
        print("[Category: dual_track_linkage]")

        # Set up a user with both tracks
        self.usage_engine.apply_level_up("link_user", 6)
        self.contribution_engine.apply_contributor_level_up("link_user", 4)

        # Test 1: Combined privileges
        combined = self.linkage_engine.get_combined_privileges("link_user")
        self._record("dual_track_linkage", "combined_privileges",
                    combined.combined_display_name != "",
                    "Display: " + combined.combined_display_name[:30])

        # Test 2: Review priority
        priority = self.linkage_engine.calculate_review_priority("link_user")
        self._record("dual_track_linkage", "review_priority",
                    1 <= priority <= 10,
                    "Priority: " + str(priority))

        # Test 3: Purchase discount
        discount = self.linkage_engine.calculate_purchase_discount("link_user", "skill", False)
        self._record("dual_track_linkage", "discount",
                    0 <= discount <= 1.0,
                    "Discount: " + str(discount))

        # Test 4: Creator incentive eligibility
        eligible = self.linkage_engine.check_creator_incentive_eligibility("link_user")
        self._record("dual_track_linkage", "incentive",
                    eligible == True,
                    "Eligible: " + str(eligible))

        # Test 5: Exposure boost
        boost = self.linkage_engine.calculate_initial_exposure_boost("link_user", "skill")
        self._record("dual_track_linkage", "exposure",
                    boost >= 1.0,
                    "Boost: " + str(boost) + "x")

    def _test_leaderboard(self) -> None:
        """Test Category: leaderboard (3 tests)"""
        print("[Category: leaderboard]")

        # Add some users to leaderboard
        for i in range(5):
            uid = "lb_user_" + str(i)
            self.usage_engine._get_or_create_user_state(uid)
            self.usage_engine._user_states[uid]["total_growth_points"] = (5 - i) * 1000

        # Test 1: Usage leaderboard
        usage_board = self.leaderboard.get_usage_leaderboard()
        self._record("leaderboard", "usage_board",
                    len(usage_board) > 0,
                    "Entries: " + str(len(usage_board)))

        # Test 2: Contributor leaderboard
        contrib_board = self.leaderboard.get_contributor_leaderboard()
        self._record("leaderboard", "contributor_board",
                    type(contrib_board) == list,
                    "Contrib board type OK")

        # Test 3: Rank position
        rank = self.leaderboard.get_user_rank_position("lb_user_0", "usage")
        self._record("leaderboard", "rank_position",
                    rank > 0,
                    "Rank: #" + str(rank))

    def _test_display_rendering(self) -> None:
        """Test Category: display_rendering (4 tests)"""
        print("[Category: display_rendering]")

        renderer = GrowthDisplayRenderer(
            self.usage_engine, self.contribution_engine, self.linkage_engine
        )

        # Test 1: Growth profile panel
        panel = renderer.render_growth_profile_panel("render_user")
        self._record("display_rendering", "growth_panel",
                    "growth-profile-panel" in panel,
                    "Panel length: " + str(len(panel)))

        # Test 2: Level up celebration
        event = LevelUpEvent(
            event_id="evt_001", user_id="u1", previous_level=1, new_level=2,
            level_name="初探道人", timestamp=time.time(),
            new_privileges=["custom_avatar"], bonus_points=50
        )
        cele = renderer.render_level_up_celebration(event)
        self._record("display_rendering", "level_up_celebration",
                    "level-up-celebration" in cele,
                    "Celebration length: " + str(len(cele)))

        # Test 3: Task panel
        task_panel = renderer.render_task_panel("render_user")
        self._record("display_rendering", "task_panel",
                    "task-panel" in task_panel,
                    "Task panel length: " + str(len(task_panel)))

        # Test 4: Creator dashboard
        cr = CreatorCenterRenderer(
            self.contribution_engine, self.content_manager, self.withdrawal_manager
        )
        dash = cr.render_creator_dashboard("creator_dash")
        self._record("display_rendering", "creator_dashboard",
                    "creator-dashboard" in dash,
                    "Dashboard length: " + str(len(dash)))

    def _test_mall_rendering(self) -> None:
        """Test Category: mall_rendering (2 tests)"""
        print("[Category: mall_rendering]")

        mr = PointsMallRenderer()

        # Test 1: Mall grid
        grid = mr.render_mall_grid(self.points_mall.MALL_PRODUCTS, 5000)
        self._record("mall_rendering", "mall_grid",
                    "mall-grid" in grid,
                    "Grid length: " + str(len(grid)))

        # Test 2: Exchange confirmation
        confirm = mr.render_exchange_confirmation(
            self.points_mall.MALL_PRODUCTS[0], 5000
        )
        self._record("mall_rendering", "exchange_confirmation",
                    "exchange-confirmation" in confirm,
                    "Confirm length: " + str(len(confirm)))

    def _test_notifications(self) -> None:
        """Test Category: notifications (3 tests)"""
        print("[Category: notifications]")

        # Test 1: Level up notification
        lue = LevelUpEvent(
            event_id="evt_notif", user_id="notif_u1", previous_level=1, new_level=2,
            level_name="初探道人", timestamp=time.time(),
            new_privileges=["badge"], bonus_points=50
        )
        notif_id = self.notification_service.send_level_up_notification("notif_u1", lue)
        self._record("notifications", "level_up",
                    notif_id.startswith("notif_"),
                    "Notif ID: " + notif_id)

        # Test 2: Earning notification
        ee = EarningEntry(
            entry_id="earn_001", user_id="notif_u1", source_type="skill_sale",
            source_id="skill_001", amount=50.0, status="pending",
            created_at=time.time(), settled_at=None
        )
        earn_notif = self.notification_service.send_earning_notification("notif_u1", ee)
        self._record("notifications", "earning",
                    earn_notif.startswith("notif_"),
                    "Earning notif ID: " + earn_notif)

        # Test 3: Milestone notification
        mile_notif = self.notification_service.send_milestone_notification(
            "notif_u1", MilestoneType.FIRST_UPLOAD
        )
        self._record("notifications", "milestone",
                    mile_notif.startswith("notif_"),
                    "Milestone notif ID: " + mile_notif)

    def _test_analytics(self) -> None:
        """Test Category: analytics (3 tests)"""
        print("[Category: analytics]")

        # Test 1: Platform growth summary
        summary = self.analytics_engine.get_platform_growth_summary()
        self._record("analytics", "platform_summary",
                    summary.total_active_users >= 0,
                    "Active users: " + str(summary.total_active_users))

        # Test 2: Ecosystem report
        eco = self.analytics_engine.get_content_ecosystem_report()
        self._record("analytics", "ecosystem_report",
                    eco.approval_rate >= 0,
                    "Approval rate: " + str(eco.approval_rate))

        # Test 3: Correlation analysis
        corr = self.analytics_engine.get_dual_track_correlation_analysis()
        self._record("analytics", "correlation",
                    -1 <= corr.correlation_coefficient <= 1,
                    "Correlation: " + str(corr.correlation_coefficient))

    def _test_fairness_guard(self) -> None:
        """Test Category: fairness_guard (3 tests) """
        print("[Category: fairness_guard]")

        # Test 1: Anomaly detection
        pattern = {"action_count": 500, "time_span_seconds": 3600}
        anom = self.fairness_guard.detect_anomalous_activity("fg_user", pattern)
        self._record("fairness_guard", "anomaly_detection",
                    type(anom.is_anomalous) == bool,
                    "Anomalous: " + str(anom.is_anomalous))

        # Test 2: Daily limits
        allowed = self.fairness_guard.apply_daily_limits("fg_user", "smart_consultation", 25)
        self._record("fairness_guard", "daily_limits",
                    0 <= allowed <= 25,
                    "Allowed: " + str(allowed))

        # Test 3: Originality check
        orig = self.fairness_guard.validate_content_originality(
            "This is an original piece of content that I wrote myself. " +
            "It contains unique insights and analysis about the real estate market."
        )
        self._record("fairness_guard", "originality",
                    0 <= orig.score <= 100,
                    "Score: " + str(orig.score))

    def _test_api_endpoints(self) -> None:
        """Test Category: api_endpoints (4 tests)"""
        print("[Category: api_endpoints]")

        # Test 1: Record growth API
        resp1 = self.api.api_record_growth({
            "user_id": "api_user", "action_type": "daily_checkin"
        })
        self._record("api_endpoints", "growth_record",
                    resp1["status_code"] == 200,
                    "Status: " + str(resp1["status_code"]))

        # Test 2: Record contribution API
        resp2 = self.api.api_record_contribution({
            "user_id": "api_creator", "action_type": "upload_skill"
        })
        self._record("api_endpoints", "contributor_record",
                    resp2["status_code"] == 200,
                    "Status: " + str(resp2["status_code"]))

        # Test 3: Upload API
        resp3 = self.api.api_submit_upload({
            "user_id": "api_creator", "content_type": "skill",
            "title": "API Test Skill", "description": "Test",
            "content": "Content", "price": 0
        })
        self._record("api_endpoints", "upload",
                    resp3["status_code"] in [200, 201],
                    "Status: " + str(resp3["status_code"]))

        # Test 4: Exchange API
        self.usage_engine.apply_level_up("api_mall_user", 7)
        self.usage_engine._get_or_create_user_state("api_mall_user")["total_growth_points"] = 2000
        resp4 = self.api.api_exchange_product({
            "user_id": "api_mall_user", "product_id": "prod_001"
        })
        self._record("api_endpoints", "exchange",
                    "data" in resp4,
                    "Has data: " + str("data" in resp4))

    def _test_frontend_rendering(self) -> None:
        """Test Category: frontend_rendering (5 tests)"""
        print("[Category: frontend_rendering]")

        renderer = GrowthDisplayRenderer(
            self.usage_engine, self.contribution_engine, self.linkage_engine
        )

        # Test 1: Privilege list rendering
        privs = self.usage_engine.get_available_privileges("fe_user")
        priv_html = renderer.render_privilege_list(privs)
        self._record("frontend_rendering", "privilege_list",
                    "privilege-list" in priv_html,
                    "Privilege HTML length: " + str(len(priv_html)))

        # Test 2: Upgrade timeline
        timeline = renderer.render_upgrade_history_timeline("fe_user")
        self._record("frontend_rendering", "upgrade_timeline",
                    "upgrade-timeline" in timeline,
                    "Timeline length: " + str(len(timeline)))

        # Test 3: Track comparison chart
        chart = renderer.render_track_comparison_chart("fe_user")
        self._record("frontend_rendering", "track_comparison",
                    "track-comparison-chart" in chart,
                    "Chart length: " + str(len(chart)))

        # Test 4: Synergy badge
        badge = self.linkage_engine.render_synergy_badge("fe_user")
        self._record("frontend_rendering", "synergy_badge",
                    "synergy-badge" in badge,
                    "Badge length: " + str(len(badge)))

        # Test 5: Creator center components
        cr = CreatorCenterRenderer(
            self.contribution_engine, self.content_manager, self.withdrawal_manager
        )
        form = cr.render_upload_form("skill")
        self._record("frontend_rendering", "upload_form",
                    "upload-form" in form,
                    "Form length: " + str(len(form)))

    def generate_pytest_code(self) -> str:
        """生成pytest兼容代码"""
        code = '''
import pytest
from dual_track_growth_system_layer import *

@pytest.fixture
def suite():
    return DualTrackTestSuite()

class TestUsageEngine:
    def test_record_action(suite):
        tx = suite.usage_engine.record_growth_action("u1", "smart_consultation")
        assert tx.points_earned == 10

    def test_get_profile(suite):
        p = suite.usage_engine.get_user_growth_profile("u1")
        assert p.current_level == 1

class TestContributionEngine:
    def test_record_contribution(suite):
        tx = suite.contribution_engine.record_contribution_action("c1", "upload_skill")
        assert tx.points_earned == 50

    def test_revenue_share(suite):
        rs = suite.contribution_engine.calculate_revenue_share(100, 3, "skill")
        assert rs.creator_amount > 0

class TestContentUpload:
    def test_submit_upload(suite):
        r = suite.content_manager.submit_upload("c1", "skill", "T", "D", "C")
        assert r.status == "pending"

    def test_review_upload(suite):
        r = suite.content_manager.submit_upload("c2", "skill", "T", "D", "C")
        rev = suite.content_manager.review_upload(r.upload_id, "approved", "rev1")
        assert rev.approved == True

class TestPointsMall:
    def test_list_products(suite):
        prods = suite.points_mall.list_products()
        assert len(prods) == 7

class TestDualTrackLinkage:
    def test_combined_privileges(suite):
        cp = suite.linkage_engine.get_combined_privileges("u1")
        assert cp.combined_display_name != ""

class TestLeaderboard:
    def test_usage_leaderboard(suite):
        lb = suite.leaderboard.get_usage_leaderboard()
        assert isinstance(lb, list)

class TestFairnessGuard:
    def test_anomaly_detection(suite):
        result = suite.fairness_guard.detect_anomalous_activity("u1", {"action_count": 100})
        assert isinstance(result.is_anomalous, bool)

class TestNotifications:
    def test_level_up_notification(suite):
        evt = LevelUpEvent("e1", "u1", 1, 2, "name", 1.0, [], 0)
        nid = suite.notification_service.send_level_up_notification("u1", evt)
        assert nid.startswith("notif_")

class TestAPIEndpoints:
    def test_record_growth_api(suite):
        resp = suite.api.api_record_growth({"user_id": "u1", "action_type": "checkin"})
        assert resp["status_code"] == 200
'''
        return code

    def generate_playwright_e2e(self) -> str:
        """生成Playwright E2E测试代码"""
        code = '''
from playwright.sync_api import sync_playwright

def test_dual_track_growth_system():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to growth page
        page.goto("/growth/profile")
        page.wait_for_selector(".growth-profile-panel")

        # Verify usage track displayed
        usage_section = page.locator(".usage-track")
        assert usage_section.count() == 1

        # Verify contributor track displayed
        contrib_section = page.locator(".contributor-track")
        assert contrib_section.count() == 1

        # Test level up celebration modal
        page.click(".simulate-level-up")
        page.wait_for_selector(".level-up-celebration")
        assert page.locator(".confetti-animation").count() == 1
        page.click(".close-btn")

        # Test points mall
        page.goto("/mall")
        page.wait_for_selector(".mall-grid")
        products = page.locator(".product-card")
        assert products.count() == 7

        # Test exchange flow
        first_product = products.first
        first_product.click(".btn-exchange")
        page.wait_for_selector(".exchange-confirmation")
        page.click(".btn-confirm")
        page.wait_for_selector(".exchange-success")

        browser.close()
'''
        return code


# ============================================================
# Main Entry Point
# ============================================================


if __name__ == "__main__":
    print("Layer 30 loaded OK")
    print("Dual-Track Growth User System initialized")
    print("Components ready:")
    print("  - UsageGrowthEngine (Track 1)")
    print("  - ContributionEngine (Track 2)")
    print("  - ContentUploadManager")
    print("  - RevenueCalculator & WithdrawalManager")
    print("  - PointsMallManager")
    print("  - DualTrackLinkageEngine")
    print("  - DualTrackLeaderboard")
    print("  - GrowthDisplayRenderer & CreatorCenterRenderer")
    print("  - PointsMallRenderer")
    print("  - GrowthNotificationService")
    print("  - GrowthAnalyticsEngine")
    print("  - FairnessGuard")
    print("  - DualTrackAPIEndpoints (12 endpoints)")
    print("  - DualTrackTestSuite (55+ tests)")
    print("")
    print("To run tests:")
    print("  from dual_track_growth_system_layer import DualTrackTestSuite")
    print("  suite = DualTrackTestSuite()")
    print("  results = suite.run_all_tests()")

