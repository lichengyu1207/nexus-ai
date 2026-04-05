# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 推广变现层（第8层：Promotion & Monetization Layer）
==========================================================================
对应设计文档「房都督平台推广变现策略（2026实战版）」完整落地。
将平台的硬核能力(三省六部/海马体记忆/人格化交互)转化为商业价值，
通过五端市场定位、智能体工时定价、内容生态破圈、商业化产品矩阵、分阶段变现节奏
实现从"技术能力"到"真金白银"的完整闭环。

六大模块：
  五端市场篇 — 目标市场优先级排序
    企业端(⭐⭐⭐⭐⭐ API调用/定制集群 按Token+年费) → 院校端(⭐⭐⭐⭐ 教学实训/能力雷达 按校年费+人头)
    政府端(⭐⭐⭐ 监管驾驶舱/数据大屏 项目制10-50万) → 协会端(⭐⭐ 行业报告/数据共享 会员年费)
    公众端(⭐⭐⭐ 高级报告/深度咨询/命理 单次付费+会员订阅)

  定价模式篇 — "智能体工时"透明计费体系
    免费版100工时/月(个人体验) → 基础版5000工时/299元/月(中小企业)
    专业版2万工时/999元/月(高频批量) → 企业版按需定制面议(私有化部署)
    工时账单明细(任务→消耗工时→费用→价值证明) → 积分系统融合(注册赠送1000积分可兑换工时)

  推广渠道篇 — 内容+生态双轮驱动
    内容营销: 技术博客系列(三省六部架构故事) + 案例拆解(决策故事脱敏) + 短视频(周瑜陆逊人格化配音)
    生态合作: 院校端免费教学版培养未来用户 + 贝壳/房天下数据交换联合产品 + 估价师学会认证绑定
    开发者社区: 人才市场/Skill上传抽成 + 智能体大赛奖金激励 + API文档免费试用额度

  商业化产品篇 — 从功能到解决方案
    标准产品: C端智能咨询助手69元/月(无限咨询+5份深度报告) + B端企业智能体集群(私有化六部按年费)
    行业解决方案: 智慧物业(管家+工程+安保三智能体打包按小区规模) + 房产投资决策平台(热力图+政策预警+估值模型数据服务年费)
    增值服务: 深度报告49元/份(预览部分) + 人工复核99元/次(专业估价师审核) + 私有化部署10-30万一次性

  变现节奏篇 — 四阶段推进路线图
    验证期0-3月: 企业端免费试用收集案例 → 启动期3-6月: 基础版+专业版签约10家(5-10万)
    扩张期6-12月: 行业解决方案落地开发者生态初具规模(50-100万) → 成熟期1-2年: 五端协同闭环年收入300-500万

  总协调器 — 推广变现全景看板
    市场渗透率仪表盘 + 收入流水实时追踪 + 渠道ROI分析 + 产品组合优化建议
    与第7层转化优化层联动(漏斗→付费转化) + 与积分系统集成(积分→工时→付费升级路径)

通关标准:
  五端市场覆盖度≥80%, 定价模型支持4种计费方式灵活切换
  内容营销产出≥20篇/月(博客+案例+短视频), 合作伙伴≥5家(院校/企业/协会各1+)
  验证期完成≥10个免费试用案例收集, 启动期首月收入≥1万
"""
from __future__ import annotations

import json
import math
import random
import statistics
import logging
import time
import copy
import uuid
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from collections import deque, defaultdict, Counter

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================


class MarketSegment(Enum):
    """市场细分(五端)"""
    ENTERPRISE = "企业端"
    ACADEMIC = "院校端"
    GOVERNMENT = "政府端"
    ASSOCIATION = "协会端"
    PUBLIC = "公众端"


class PricingTier(Enum):
    """定价层级"""
    FREE = "免费版"
    BASIC = "基础版"
    PROFESSIONAL = "专业版"
    ENTERPRISE = "企业版"
    CUSTOM = "定制版"


class ProductCategory(Enum):
    """产品类别"""
    STANDARD_PRODUCT = "标准产品"
    INDUSTRY_SOLUTION = "行业解决方案"
    VALUE_ADDED_SERVICE = "增值服务"
    API_SERVICE = "API服务"
    DEPLOYMENT_SERVICE = "部署服务"
    CERTIFICATION_TRAINING = "认证培训"


class PromotionChannel(Enum):
    """推广渠道"""
    TECH_BLOG = "技术博客"
    CASE_STUDY = "案例拆解"
    SHORT_VIDEO = "短视频"
    UNIVERSITY_COOP = "院校合作"
    ENTERPRISE_PARTNER = "企业合作"
    ASSOCIATION_PARTNER = "协会合作"
    DEVELOPER_COMMUNITY = "开发者社区"
    AGENT_COMPETITION = "智能体大赛"
    WORD_OF_MOUTH = "口碑传播"
    PAID_ADVERTISING = "付费广告"


class MonetizationPhase(Enum):
    """变现阶段"""
    VALIDATION = "验证期"
    LAUNCH = "启动期"
    EXPANSION = "扩张期"
    MATURITY = "成熟期"


class PartnershipStatus(Enum):
    """合作状态"""
    PROSPECTING = "接洽中"
    NEGOTIATING = "谈判中"
    ACTIVE = "合作中"
    PAUSED = "已暂停"
    TERMINATED = "已终止"


class ContentType(Enum):
    """内容类型"""
    TECH_ARTICLE = "技术文章"
    CASE_STORY = "案例故事"
    VIDEO_SHORT = "短视频"
    TUTORIAL = "教程"
    WHITEPAPER = "白皮书"
    PRESS_RELEASE = "新闻稿"
    SOCIAL_POST = "社媒帖子"


# ==================== 数据结构定义 ====================


@dataclass
class MarketSegmentProfile:
    """市场细分画像"""
    segment: MarketSegment
    priority: int  # 1-5 stars
    core_product: str
    pricing_model: str
    target_user_size: str
    estimated_tam: float  # Total Addressable Market (万元)
    estimated_sam: float  # Serviceable Available Market (万元)
    conversion_rate_est: float
    avg_contract_value: float
    sales_cycle_days: int
    key_pain_points: List[str] = field(default_factory=list)
    value_proposition: str = ""
    competitor_landscape: str = ""
    go_to_market_strategy: str = ""


@dataclass
class AgentWorkHour:
    """智能体工时记录"""
    work_id: str
    user_id: str
    task_type: str
    task_description: str
    agent_name: str
    hours_consumed: float
    token_count: int
    complexity_factor: float  # 0.5-2.0
    base_rate_per_hour: float
    total_cost: float
    value_delivered: float
    tier: PricingTier
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PricingPlan:
    """定价方案"""
    plan_id: str
    tier: PricingTier
    name: str
    monthly_work_hours: int
    monthly_price_cny: float
    annual_price_cny: Optional[float] = None
    included_features: List[str] = field(default_factory=list)
    agent_types_included: List[str] = field(default_factory=list)
    api_calls_limit: int = 0
    report_quota: int = 0
    consultation_quota: int = 0
    support_level: str = "community"
    custom_deployment: bool = False
    sla_guarantee: str = ""
    discount_for_annual: float = 0.0
    trial_days: int = 0


@dataclass
class ContentPiece:
    """内容作品"""
    content_id: str
    title: str
    content_type: ContentType
    channel: PromotionChannel
    author: str
    status: str  # draft/published/archived
    publish_date: Optional[str] = None
    word_count: int = 0
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    ctr: float = 0.0
    conversion_tracking_id: Optional[str] = None
    conversions: int = 0
    seo_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PartnershipRecord:
    """合作记录"""
    partnership_id: str
    partner_name: str
    partner_type: str  # university/enterprise/association/developer/media
    market_segment: MarketSegment
    status: PartnershipStatus
    cooperation_mode: str  # data_exchange/joint_product/reseller/certification/white_label
    terms_summary: str
    revenue_share_pct: float = 0.0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    contacts: List[Dict[str, str]] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    total_revenue_generated: float = 0.0
    leads_generated: int = 0
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CommercialProduct:
    """商业化产品"""
    product_id: str
    name: str
    category: ProductCategory
    target_segment: MarketSegment
    pricing_model: str  # subscription/per_task/per_user/project
    base_price_cny: float
    price_range: str
    description: str
    features: List[str] = field(default_factory=list)
    included_agents: List[str] = field(default_factory=list)
    deployment_type: str = "cloud"  # cloud/hybrid/on-premise
    customization_level: str = "standard"  # standard/semi-custom/full-custom
    competitors: List[str] = field(default_factory=dict)
    differentiation: str = ""
    sales_count: int = 0
    revenue_total: float = 0.0
    avg_rating: float = 0.0
    review_count: int = 0
    active: bool = True
    launch_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RevenueRecord:
    """收入记录"""
    record_id: str
    date: str
    segment: MarketSegment
    product_id: str
    product_name: str
    customer_id: str
    customer_name: str
    amount_cny: float
    pricing_tier: PricingTier
    payment_method: str  # alipay/wechat/bank_transfer/invoice
    subscription_month: Optional[int] = None
    is_recurring: bool = False
    commission_deducted: float = 0.0
    net_revenue: float = 0.0
    sales_channel: PromotionChannel = PromotionChannel.WORD_OF_MOUTH
    sales_rep: str = ""
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MonetizationMilestone:
    """变现里程碑"""
    milestone_id: str
    phase: MonetizationPhase
    name: string  # type: ignore
    target_date: str
    target_revenue_cny: float
    actual_revenue_cny: float = 0.0
    target_customers: int = 0
    actual_customers: int = 0
    key_actions: List[str] = field(default_factory=list)
    completed_actions: List[str] = field(default_factory=list)
    status: str = "pending"  # pending/in_progress/completed/overdue
    progress_pct: float = 0.0
    achieved_at: Optional[str] = None


@dataclass
class PointsTransaction:
    """积分交易记录"""
    transaction_id: str
    user_id: str
    transaction_type: str  # earn/redeem/expire/adjust
    points_delta: int
    balance_after: int
    reason: str
    related_work_hours: Optional[float] = None
    related_product: Optional[str] = None
    expires_at: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PromotionDashboardData:
    """推广变现看板数据"""
    dashboard_id: str
    date_range: str
    total_revenue_cny: float
    mrr_cny: float  # Monthly Recurring Revenue
    arr_cny: float  # Annual Recurring Revenue
    paying_customers: int
    trial_customers: int
    conversion_trial_to_paid: float
    revenue_by_segment: Dict[str, float]
    revenue_by_product: Dict[str, float]
    revenue_by_channel: Dict[str, float]
    top_products: List[Dict[str, Any]]
    active_partnerships: int
    content_published_this_month: int
    content_total_views: int
    content_avg_ctr: float
    points_issued_total: int
    points_redeemed_total: int
    work_hours_consumed_total: float
    monetization_phase: MonetizationPhase
    phase_progress: Dict[str, Any]
    milestone_status: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ==================== Part A: 五端市场篇 — 目标市场分析与优先级排序 ====================


class FiveSegmentMarketAnalyzer:
    """五端市场分析器 — 目标市场画像与优先级排序"""

    SEGMENT_PRIORITY = {
        MarketSegment.ENTERPRISE: 5,
        MarketSegment.ACADEMIC: 4,
        MarketSegment.PUBLIC: 3,
        MarketSegment.GOVERNMENT: 3,
        MarketSegment.ASSOCIATION: 2,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._segment_profiles: Dict[MarketSegment, MarketSegmentProfile] = {}
        self._lead_pipeline: List[Dict[str, Any]] = []
        self._competitive_intel: Dict[str, Any] = {}
        self._init_default_profiles()

    def _init_default_profiles(self) -> None:
        """初始化五端默认画像"""
        self._segment_profiles[MarketSegment.ENTERPRISE] = MarketSegmentProfile(
            segment=MarketSegment.ENTERPRISE, priority=5,
            core_product="API智能体调用 + 定制化智能体集群",
            pricing_model="按Token/按任务量计费 + 年费订阅",
            target_user_size="中型房企/中介/投资机构 ~5000家",
            estimated_tam=50000, estimated_sam=5000,
            conversion_rate_est=0.08, avg_contract_value=120000,
            sales_cycle_days=45,
            key_pain_points=["人工估价效率低", "数据分析成本高", "决策缺乏系统性", "合规风险管控难"],
            value_proposition="三省六部智能体集群提供7×24自动化房产决策支持，降低60%人力成本",
            competitor_landscape="贝壳AI顾问/房天下数据通/克而瑞CAIC",
            go_to_market_strategy="直销团队+渠道代理+行业展会",
        )
        self._segment_profiles[MarketSegment.ACADEMIC] = MarketSegmentProfile(
            segment=MarketSegment.ACADEMIC, priority=4,
            core_product="教学实训平台 + 学生能力雷达图",
            pricing_model="按学校年费 + 学生人头分成",
            target_user_size="房地产相关专业院校 ~200所",
            estimated_tam=8000, estimated_sam=1500,
            conversion_rate_est=0.15, avg_contract_value=80000,
            sales_cycle_days=90,
            key_pain_points=["实践教学缺工具", "学生就业对接难", "课程内容滞后", "科研数据获取贵"],
            value_proposition="真实业务场景智能体实训 + AI辅助课题研究",
            competitor_landscape="广联达实训/易居克而瑞教学版",
            go_to_market_strategy="教育展会+学术会议+免费教学版渗透",
        )
        self._segment_profiles[MarketSegment.GOVERNMENT] = MarketSegmentProfile(
            segment=MarketSegment.GOVERNMENT, priority=3,
            core_product="监管驾驶舱 + 城市数据大屏",
            pricing_model="项目制 (10-50万/项目)",
            target_user_size="住建局/规划局/统计局 ~300家",
            estimated_tam=15000, estimated_sam=1200,
            conversion_rate_est=0.05, avg_contract_value=300000,
            sales_cycle_days=180,
            key_pain_points=["数据孤岛严重", "监管时效性差", "预警能力不足", "决策缺乏数据支撑"],
            value_proposition="城市级房地产数据实时监控 + 智能预警 + 政策仿真推演",
            competitor_landscape="政府自建系统/大型IT集成商",
            go_to_market_strategy="政府采购招投标+标杆案例示范",
        )
        self._segment_profiles[MarketSegment.ASSOCIATION] = MarketSegmentProfile(
            segment=MarketSegment.ASSOCIATION, priority=2,
            core_product="行业报告生成 + 数据共享平台",
            pricing_model="会员年费 + 数据服务费",
            target_user_size="房地产协会/估价师学会/经纪商会 ~50家",
            estimated_tam=3000, estimated_sam=400,
            conversion_rate_est=0.12, avg_contract_value=60000,
            sales_cycle_days=60,
            key_pain_points=["行业数据分散", "会员服务单一", "影响力有限", "标准化不足"],
            value_proposition="AI驱动的行业研究报告 + 会员增值服务平台",
            competitor_landscape="传统行业协会服务",
            go_to_market_strategy="高层拜访+联合活动+认证授权",
        )
        self._segment_profiles[MarketSegment.PUBLIC] = MarketSegmentProfile(
            segment=MarketSegment.PUBLIC, priority=3,
            core_product="高级报告 + 深度咨询 + 命理服务",
            pricing_model="单次付费 + 会员订阅",
            target_user_size="购房人群/投资者/从业者 ~百万人级",
            estimated_tam=100000, estimated_sam=20000,
            conversion_rate_est=0.02, avg_contract_value=500,
            sales_cycle_days=1,
            key_pain_points=["信息不对称", "决策焦虑", "专业门槛高", "时间成本大"],
            value_proposition="周瑜/陆逊人格化智能顾问 + 一站式房产决策支持",
            competitor_landscape="安居客/链家咨询师/各类房产APP",
            go_to_market策略="内容营销+社交媒体+口碑裂变",  # type: ignore
        )

    def get_segment_priority_ranking(self) -> List[Tuple[MarketSegment, MarketSegmentProfile]]:
        """获取市场优先级排名"""
        ranked = sorted(self._segment_profiles.items(),
                        key=lambda x: x[1].priority, reverse=True)
        return ranked

    def calculate_market_opportunity_score(self, segment: MarketSegment) -> Dict[str, Any]:
        """计算市场机会评分"""
        profile = self._segment_profiles.get(segment)
        if not profile:
            return {"segment": segment.value, "score": 0}

        attractiveness = (
            profile.estimated_sam / max(profile.estimated_tam, 1) * 30 +
            min(profile.conversion_rate_est * 100 * 2, 30) +
            profile.priority * 6 +
            min(profile.avg_contract_value / 10000, 20)
        )
        fit_score = random.uniform(70, 95)
        overall = (attractiveness * 0.6 + fit_score * 0.4)

        return {
            "segment": segment.value,
            "priority_stars": "⭐" * profile.priority,
            "attractiveness": round(attractiveness, 1),
            "fit_score": round(fit_score, 1),
            "overall_score": round(overall, 1),
            "tam_wan": f"{profile.estimated_tam:.0f}万",
            "sam_wan": f"{profile.estimated_sam:.0f}万",
            "avg_contract": f"{profile.avg_contract_value/10000:.0f}万",
            "recommendation": "重点攻坚" if overall >= 75 else ("积极跟进" if overall >= 55 else "维持关注"),
        }

    def add_lead(self, company_name: str, segment: MarketSegment,
                 contact_person: str, contact_info: str,
                 source: PromotionChannel, notes: str = "") -> Dict[str, Any]:
        """添加销售线索"""
        lead = {
            "lead_id": f"lead_{uuid.uuid4().hex[:8]}",
            "company": company_name, "segment": segment.value,
            "contact": contact_person, "contact_info": contact_info,
            "source": source.value, "status": "new",
            "value_estimate": self._segment_profiles.get(segment, MarketSegmentProfile(
                segment=segment, priority=1, core_product="", pricing_model="",
                target_user_size="", estimated_tam=0, estimated_sam=0,
                conversion_rate_est=0, avg_contract_value=0, sales_cycle_days=0,
            )).avg_contract_value,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assigned_to": "",
        }
        self._lead_pipeline.append(lead)
        return lead

    def get_lead_funnel_stats(self) -> Dict[str, Any]:
        """获取线索漏斗统计"""
        if not self._lead_pipeline:
            return {"total_leads": 0, "by_status": {}, "by_segment": {}}
        by_status = Counter(l["status"] for l in self._lead_pipeline)
        by_segment = Counter(l["segment"] for l in self._lead_pipeline)
        total_value = sum(l.get("value_estimate", 0) for l in self._lead_pipeline)
        return {
            "total_leads": len(self._lead_pipeline),
            "by_status": dict(by_status),
            "by_segment": dict(by_segment),
            "pipeline_value_wan": round(total_value / 10000, 1),
            "avg_lead_value_wan": round(total_value / len(self._lead_pipeline) / 10000, 1)
            if self._lead_pipeline else 0,
        }

    def get_all_segments_overview(self) -> Dict[str, Any]:
        """获取全五端概览"""
        segments_data = []
        for seg, profile in self._segment_profiles.items():
            score = self.calculate_market_opportunity_score(seg)
            segments_data.append({**score, "core_product": profile.core_product})
        return {
            "segments": segments_data,
            "total_tam_wan": sum(p.estimated_tam for p in self._segment_profiles.values()),
            "total_sam_wan": sum(p.estimated_sam for p in self._segment_profiles.values()),
            "primary_focus": self._segment_profiles[
                max(self._segment_profiles.keys(),
                    key=lambda s: self._segment_profiles[s].priority)].segment.value,
        }


# ==================== Part B: 定价模式篇 — 智能体工时计费体系 ====================


class AgentWorkHourPricingEngine:
    """智能体工时定价引擎 — 透明可控的计费体系"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._pricing_plans: Dict[PricingTier, PricingPlan] = {}
        self._work_hour_log: List[AgentWorkHour] = []
        self._user_tiers: Dict[str, PricingTier] = {}
        self._user_balance: Dict[str, float] = defaultdict(float)
        self._points_system: Dict[str, int] = defaultdict(int)
        self._points_transactions: List[PointsTransaction] = []
        self._base_rate_per_hour = self.config.get("base_rate", 0.06)
        self._points_to_hours_ratio = self.config.get("points_ratio", 10)
        self._init_pricing_plans()

    def _init_pricing_plans(self) -> None:
        """初始化四档定价方案"""
        self._pricing_plans[PricingTier.FREE] = PricingPlan(
            plan_id="plan_free", tier=PricingTier.FREE, name="探索版",
            monthly_work_hours=100, monthly_price_cny=0,
            included_features=["基础咨询(周瑜)", "每月3份简易报告", "社区支持"],
            agent_types_included=["zhouyu"], api_calls_limit=200,
            report_quota=3, consultation_quota=20,
            support_level="community", trial_days=0,
        )
        self._pricing_plans[PricingTier.BASIC] = PricingPlan(
            plan_id="plan_basic", tier=PricingTier.BASIC, name="基础版",
            monthly_work_hours=5000, monthly_price_cny=299,
            annual_price_cny=2990,
            included_features=["全部智能体咨询", "每月20份深度报告", "API访问(限流)",
                           "邮件支持", "数据导出"],
            agent_types_included=["zhouyu", "luxun", "zhugeliang"],
            api_calls_limit=5000, report_quota=20, consultation_quota=200,
            support_level="email", sla_guarantee="99.5%可用性",
            discount_for_annual=0.17, trial_days=14,
        )
        self._pricing_plans[PricingTier.PROFESSIONAL] = PricingPlan(
            plan_id="plan_pro", tier=PricingTier.PROFESSIONAL, name="专业版",
            monthly_work_hours=20000, monthly_price_cny=999,
            annual_price_cny=9990,
            included_features=["无限智能体咨询", "无限报告生成", "全功能API访问",
                           "批量任务处理", "专属客户经理", "优先响应"],
            agent_types_included=["zhouyu", "luxun", "zhugeliang", "caocao", "sunquan"],
            api_calls_limit=50000, report_quota=-1, consultation_quota=-1,
            support_level="priority_manager", sla_guarantee="99.9%可用性<4h响应",
            discount_for_annual=0.17, trial_days=14,
        )
        self._pricing_plans[PricingTier.ENTERPRISE] = PricingPlan(
            plan_id="plan_enterprise", tier=PricingTier.ENTERPRISE, name="企业版",
            monthly_work_hours=-1, monthly_price_cny=0,
            included_features=["私有化部署", "定制智能体训练", "SLA保障",
                           "专属技术支持", "安全审计", "数据隔离"],
            agent_types_included=[], custom_deployment=True,
            support_level="dedicated_team", sla_guarantee="99.99%可用性<1h响应",
        )

    def register_user_tier(self, user_id: str, tier: PricingTier) -> None:
        """注册用户定价层级"""
        self._user_tiers[user_id] = tier
        plan = self._pricing_plans[tier]
        if tier != PricingTier.ENTERPRISE and tier != PricingTier.CUSTOM:
            self._user_balance[user_id] = plan.monthly_work_hours
        logger.info(f"[定价引擎] 用户{user_id} 注册为 {tier.value}")

    def consume_work_hours(self, user_id: str, task_type: str,
                           task_description: str, agent_name: str,
                           token_count: int, complexity: float = 1.0) -> AgentWorkHour:
        """消耗智能体工时"""
        wid = f"wh_{uuid.uuid4().hex[:8]}"
        tier = self._user_tiers.get(user_id, PricingTier.FREE)
        plan = self._pricing_plans[tier]

        base_hours = max(token_count / 1000, 0.1) * complexity
        actual_hours = base_hours * (0.8 + random.uniform(0, 0.4))
        rate = self._base_rate_per_hour * {
            PricingTier.FREE: 1.0, PricingTier.BASIC: 1.0,
            PricingTier.PROFESSIONAL: 0.8, PricingTier.ENTERPRISE: 0.6,
        }.get(tier, 1.0)
        cost = actual_hours * rate * 100

        if self._user_balance[user_id] >= actual_hours or tier == PricingTier.ENTERPRISE:
            self._user_balance[user_id] -= actual_hours
        else:
            logger.warning(f"[定价引擎] 用户{user_id} 工时不足! 余额={self._user_balance[user_id]:.1f}, 需要={actual_hours:.1f}")

        work_hour = AgentWorkHour(
            work_id=wid, user_id=user_id, task_type=task_type,
            task_description=task_description, agent_name=agent_name,
            hours_consumed=round(actual_hours, 2), token_count=token_count,
            complexity_factor=complexity, base_rate_per_hour=rate,
            total_cost=round(cost, 2), value_delivered=round(cost * random.uniform(2, 5), 2),
            tier=tier,
        )
        self._work_hour_log.append(work_hour)

        points_earned = int(actual_hours * self._points_to_hours_ratio)
        if points_earned > 0:
            self._award_points(user_id, points_earned, f"工时消耗奖励({actual_hours:.1f}h)")

        return work_hour

    def _award_points(self, user_id: str, points: int, reason: str) -> None:
        """发放积分"""
        self._points_system[user_id] += points
        tx = PointsTransaction(
            transaction_id=f"pts_{uuid.uuid4().hex[:8]}",
            user_id=user_id, transaction_type="earn",
            points_delta=points, balance_after=self._points_system[user_id],
            reason=reason,
        )
        self._points_transactions.append(tx)

    def redeem_points_for_hours(self, user_id: str, points_to_redeem: int) -> Tuple[bool, float]:
        """积分兑换工时"""
        current = self._points_system.get(user_id, 0)
        if current < points_to_redeem:
            return False, 0.0
        hours_gained = points_to_redeem / self._points_to_hours_ratio
        self._points_system[user_id] -= points_to_redeem
        self._user_balance[user_id] += hours_gained
        tx = PointsTransaction(
            transaction_id=f"pts_{uuid.uuid4().hex[:8]}",
            user_id=user_id, transaction_type="redeem",
            points_delta=-points_to_redeem, balance_after=self._points_system[user_id],
            reason=f"积分兑换工时({points_to_redeem}积分→{hours_gained:.1f}h)",
            related_work_hours=hours_gained,
        )
        self._points_transactions.append(tx)
        return True, hours_gained

    def grant_registration_bonus(self, user_id: str, bonus_points: int = 1000) -> None:
        """注册赠送积分"""
        self._award_points(user_id, bonus_points, "注册赠送")
        logger.info(f"[定价引擎] 用户{user_id} 获得注册赠送 {bonus_points} 积分")

    def get_user_billing_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户账单摘要"""
        user_works = [w for w in self._work_hour_log if w.user_id == user_id]
        tier = self._user_tiers.get(user_id, PricingTier.FREE)
        plan = self._pricing_plans[tier]
        total_hours = sum(w.hours_consumed for w in user_works)
        total_cost = sum(w.total_cost for w in user_works)
        total_value = sum(w.value_delivered for w in user_works)
        return {
            "user_id": user_id, "tier": tier.value, "plan_name": plan.name,
            "hours_remaining": round(max(self._user_balance[user_id], 0), 1),
            "hours_consumed_this_month": round(total_hours, 1),
            "total_cost_cny": round(total_cost, 2),
            "value_delivered_cny": round(total_value, 2),
            "roi_ratio": round(total_value / max(total_cost, 0.01), 2),
            "points_balance": self._points_system.get(user_id, 0),
            "tasks_completed": len(user_works),
            "top_agents_used": Counter(w.agent_name for w in user_works).most_common(3),
        }

    def get_pricing_plans_comparison(self) -> List[Dict[str, Any]]:
        """获取定价方案对比表"""
        comparison = []
        for tier, plan in self._pricing_plans.items():
            comparison.append({
                "tier": tier.value, "name": plan.name,
                "monthly_hours": plan.monthly_work_hours if plan.monthly_work_hours > 0 else "∞",
                "monthly_price": f"{plan.monthly_price_cny}元" if plan.monthly_price_cny > 0 else "面议",
                "annual_price": f"{plan.annual_price_cny}元/年" if plan.annual_price_cny else "-",
                "agents": len(plan.agent_types_included) if plan.agent_types_included else "全部",
                "api_calls": f"{plan.api_calls_limit:,}" if plan.api_calls_limit > 0 else "不限",
                "reports": f"{plan.report_quota}" if plan.report_quota >= 0 else "不限",
                "support": plan.support_level,
                "sla": plan.sla_guarantee or "-",
                "trial": f"{plan.trial_days}天免费" if plan.trial_days > 0 else "-",
            })
        return comparison

    def get_engine_stats(self) -> Dict[str, Any]:
        """获取定价引擎统计"""
        total_hours = sum(w.hours_consumed for w in self._work_hour_log)
        total_revenue = sum(w.total_cost for w in self._work_hour_log)
        total_points_issued = sum(tx.points_delta for tx in self._points_transactions
                                   if tx.transaction_type == "earn")
        total_points_redeemed = abs(sum(tx.points_delta for tx in self._points_transactions
                                      if tx.transaction_type == "redeem"))
        tier_dist = Counter(self._user_tiers.values())
        return {
            "total_work_hours_consumed": round(total_hours, 1),
            "total_revenue_cny": round(total_revenue, 2),
            "total_tasks_processed": len(self._work_hour_log),
            "registered_users": len(self._user_tiers),
            "tier_distribution": {t.value: c for t, c in tier_dist.items()},
            "total_points_issued": total_points_issued,
            "total_points_redeemed": total_points_redeemed,
            "redemption_rate": round(total_points_redeemed / max(total_points_issued, 1) * 100, 2),
        }


# ==================== Part C: 推广渠道篇 — 内容营销+生态合作+开发者社区 ====================


class ContentMarketingEngine:
    """内容营销引擎 — 多渠道内容生产与管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._content_library: Dict[str, ContentPiece] = {}
        self._publishing_calendar: List[Dict[str, Any]] = []
        self._content_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._target_platforms = {
            ContentType.TECH_ARTICLE: ["知乎", "CSDN", "Medium", "公众号"],
            ContentType.CASE_STUDY: ["知乎专栏", "公众号", "官网博客"],
            ContentType.VIDEO_SHORT: ["抖音", "视频号", "B站", "小红书"],
            ContentType.TUTORIAL: ["B站", "YouTube", "CSDN"],
            ContentType.WHITEPAPER: ["官网下载", "知乎", "LinkedIn"],
            ContentType.SOCIAL_POST: ["微博", "Twitter/X", "朋友圈"],
        }
        self._content_templates = [
            {"type": ContentType.TECH_ARTICLE, "title_template":
             "我用「三省六部」架构做了一个{topic}", "target_views": 5000},
            {"type": ContentType.CASE_STUDY, "title_template":
             "{role}如何用房都督{action}——{company}真实案例", "target_views": 3000},
            {"type": ContentType.VIDEO_SHORT, "title_template":
             "当{agent_name}{action}时，用户都惊了🔥", "target_views": 10000},
            {"type": ContentType.TUTORIAL, "title_template":
             "手把手教你用房都督{feature}(附源码)", "target_views": 8000},
        ]

    def create_content(self, title: str, content_type: ContentType,
                       channel: PromotionChannel, author: str = "房都督团队",
                       tags: Optional[List[str]] = None) -> ContentPiece:
        """创建内容作品"""
        cid = f"cont_{uuid.uuid4().hex[:8]}"
        content = ContentPiece(
            content_id=cid, title=title, content_type=content_type,
            channel=channel, author=author, status="draft",
            word_count=random.randint(800, 5000),
            tags=tags or [],
        )
        self._content_library[cid] = content
        return content

    def generate_content_ideas(self, count: int = 10) -> List[Dict[str, Any]]:
        """生成内容创意"""
        topics = ["AI房产估值", "智能投顾", "海马体记忆", "三省六部架构",
                   "周瑜军师体验", "陆逊谋士实战", "贝壳数据对比", "学区房分析",
                   "投资回报率计算", "VR看房集成", "人才市场匹配", "Skill市场生态"]
        agents = ["周瑜·房产谋士", "陆逊·战略顾问", "诸葛亮·军师", "曹操·风控专家"]
        actions = ["选到了人生第一套房", "省下了50万中介费", "发现了隐藏的投资机会",
                  "完成了百万级估值报告", "避开了买房陷阱"]
        companies = ["某科技公司", "某投资机构", "某房企", "某中介公司"]

        ideas = []
        templates = self._content_templates * 3
        random.shuffle(templates)
        for i in range(min(count, len(templates))):
            tmpl = templates[i]
            topic = random.choice(topics)
            idea_title = tmpl["title_template"].format(
                topic=topic, role=random.choice(["程序员", "投资人", "购房者"]),
                action=random.choice(actions), agent_name=random.choice(agents),
                company=random.choice(companies), feature=topic,
            )
            ideas.append({
                "title": idea_title, "type": tmpl["type"].value,
                "target_views": tmpl["target_views"],
                "suggested_channels": self._target_platforms.get(tmpl["type"], []),
                "estimated_effort_h": random.randint(2, 8),
            })
        return ideas

    def publish_content(self, content_id: str, url: Optional[str] = None) -> bool:
        """发布内容"""
        content = self._content_library.get(content_id)
        if not content or content.status != "draft":
            return False
        content.status = "published"
        content.publish_date = datetime.now(timezone.utc).isoformat()
        content.url = url
        content.views = random.randint(100, int(self._config.get("base_views", 5000)))
        content.likes = int(content.views * random.uniform(0.01, 0.08))
        content.shares = int(content.views * random.uniform(0.002, 0.02))
        content.comments = int(content.views * random.uniform(0.001, 0.01))
        content.ctr = round(random.uniform(0.5, 5.0), 2)
        content.conversions = int(content.views * content.ctr / 100 * random.uniform(0.05, 0.3))
        content.seo_score = round(random.uniform(60, 98), 1)
        logger.info(f"[内容营销] 发布: {content.title} ({content.channel.value})")
        return True

    def get_content_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """获取内容绩效报告"""
        published = [c for c in self._content_library.values() if c.status == "published"]
        if not published:
            return {"total_published": 0}
        total_views = sum(c.views for c in published)
        total_conversions = sum(c.conversions for c in published)
        by_type = defaultdict(lambda: {"count": 0, "views": 0, "conversions": 0})
        by_channel = defaultdict(lambda: {"count": 0, "views": 0})
        for c in published:
            by_type[c.content_type.value]["count"] += 1
            by_type[c.content_type.value]["views"] += c.views
            by_type[c.content_type.value]["conversions"] += c.conversions
            by_channel[c.channel.value]["count"] += 1
            by_channel[c.channel.value]["views"] += c.views

        top_content = sorted(published, key=lambda c: c.views, reverse=True)[:5]
        return {
            "period_days": days, "total_published": len(published),
            "total_views": total_views, "total_conversions": total_conversions,
            "overall_ctr": round(total_conversions / max(total_views, 1) * 100, 2),
            "avg_engagement": round(statistics.mean([
                (c.likes + c.shares * 2 + c.comments * 3) / max(c.views, 1) * 100
                for c in published]), 2),
            "by_type": dict(by_type),
            "by_channel": dict(by_channel),
            "top_content": [{"title": c.title[:40], "views": c.views,
                            "ctr": c.ctr, "conversions": c.conversions} for c in top_content],
        }


class EcosystemPartnershipManager:
    """生态合作管理器 — 院校/企业/协会/开发者合作伙伴关系"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._partnerships: Dict[str, PartnershipRecord] = {}
        self._cooperation_tracks: Dict[str, List[Dict]] = {
            "university": [], "enterprise": [], "association": [],
            "developer": [], "media": [],
        }

    def add_partnership(self, partner_name: str, partner_type: str,
                        segment: MarketSegment, mode: str,
                        revenue_share: float = 0.0,
                        terms: str = "", contacts: Optional[List[Dict]] = None) -> PartnershipRecord:
        """添加合作关系"""
        pid = f"partner_{uuid.uuid4().hex[:8]}"
        partnership = PartnershipRecord(
            partnership_id=pid, partner_name=partner_name,
            partner_type=partner_type, market_segment=segment,
            status=PartnershipStatus.PROSPECTING,
            cooperation_mode=mode, revenue_share_pct=revenue_share,
            terms_summary=terms, contacts=contacts or [],
        )
        self._partnerships[pid] = partnership
        track_key = partner_type.lower().replace(" ", "_")
        if track_key not in self._cooperation_tracks:
            track_key = "other"
        self._cooperation_tracks.setdefault(track_key, []).append({
            "partner_id": pid, "name": partner_name, "mode": mode,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"[生态合作] 新增伙伴: {partner_name} ({partner_type}/{mode})")
        return partnership

    def activate_partnership(self, partnership_id: str) -> bool:
        """激活合作关系"""
        p = self._partnerships.get(partnership_id)
        if not p:
            return False
        p.status = PartnershipStatus.ACTIVE
        p.start_date = datetime.now(timezone.utc).isoformat()
        return True

    def record_partner_revenue(self, partnership_id: str, amount: float,
                               leads: int = 0) -> None:
        """记录合作带来的收入"""
        p = self._partnerships.get(partnership_id)
        if p:
            p.total_revenue_generated += amount
            p.leads_generated += leads

    def get_default_partnerships(self) -> List[PartnershipRecord]:
        """获取预设的推荐合作伙伴列表"""
        default_configs = [
            {"name": "XX房地产职业学院", "type": "university", "seg": MarketSegment.ACADEMIC,
             "mode": "education_license", "share": 0.15},
            {"name": "YY数据科技有限公司", "type": "enterprise", "seg": MarketSegment.ENTERPRISE,
             "mode": "data_exchange", "share": 0.10},
            {"name": "中国房地产估价师学会", "type": "association", "seg": MarketSegment.ASSOCIATION,
             "mode": "certification", "share": 0.20},
            {"name": "ZZ自媒体联盟", "type": "media", "seg": MarketSegment.PUBLIC,
             "mode": "content_syndication", "share": 0.08},
            {"name": "独立开发者社区", "type": "developer", "seg": MarketSegment.ENTERPRISE,
             "mode": "marketplace_commission", "share": 0.12},
        ]
        partners = []
        for dc in default_configs:
            p = self.add_partnership(
                dc["name"], dc["type"], dc["seg"], dc["mode"], dc["share"])
            partners.append(p)
        return partners

    def get_partnership_dashboard(self) -> Dict[str, Any]:
        """获取合作面板数据"""
        active = [p for p in self._partnerships.values() if p.status == PartnershipStatus.ACTIVE]
        by_type = Counter(p.partner_type for p in self._partnerships.values())
        by_status = Counter(p.status.value for p in self._partnerships.values())
        total_revenue = sum(p.total_revenue_generated for p in self._partnerships.values())
        total_leads = sum(p.leads_generated for p in self._partnerships.values())
        return {
            "total_partnerships": len(self._partnerships),
            "active_partnerships": len(active),
            "by_type": dict(by_type), "by_status": dict(by_status),
            "total_revenue_from_partners_cny": round(total_revenue, 2),
            "total_leads_from_partners": total_leads,
            "top_partners_by_revenue": sorted(
                [(p.partner_name, p.total_revenue_generated) for p in self._partnerships.values()],
                key=lambda x: x[1], reverse=True)[:5],
        }


# ==================== Part D: 商业化产品篇 — 标准产品+解决方案+增值服务 ====================


class CommercialProductManager:
    """商业化产品经理 — 产品目录与收入追踪"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._products: Dict[str, CommercialProduct] = {}
        self._revenue_log: List[RevenueRecord] = []
        self._init_product_catalog()

    def _init_product_catalog(self) -> None:
        """初始化商业化产品目录"""
        products_config = [
            {"id": "prod_consult_c", "name": "智能咨询助手(C端)", "cat": ProductCategory.STANDARD_PRODUCT,
             "seg": MarketSegment.PUBLIC, "model": "subscription", "price": 69, "range": "69元/月",
             "desc": "面向C端用户的月订阅服务，无限次智能体咨询+每月5份深度房产分析报告",
             "features": ["无限次周瑜/陆逊咨询", "每月5份深度报告", "历史对话记录", "手机App访问"],
             "agents": ["zhouyu", "luxun"], "diff": "人格化交互 vs 传统客服机器人"},
            {"id": "prod_enterprise_cluster", "name": "企业智能体集群(B端)", "cat": ProductCategory.STANDARD_PRODUCT,
             "seg": MarketSegment.ENTERPRISE, "model": "subscription", "price": 99900, "range": "8-15万/年",
             "desc": "面向企业的私有化部署六部智能体集群，包含定制训练和专属技术支持",
             "features": ["私有化部署", "六部全部智能体", "定制知识库训练", "API全开放", "SLA保障"],
             "agents": ["zhouyu", "luxun", "zhugeliang", "caocao", "sunquan", "zhaoyun"],
             "deployment": "on-premise", "customization": "full-custom",
             "diff": "完整决策链 vs 单点工具"},
            {"id": "sol_smart_property", "name": "智慧物业解决方案", "cat": ProductCategory.INDUSTRY_SOLUTION,
             "seg": MarketSegment.ENTERPRISE, "model": "project", "price": 200000, "range": "15-30万/项目",
             "desc": "管家智能体+工程智能体+安保智能体三合一打包方案，按小区规模收费",
             "features": ["管家智能体(业主服务)", "工程智能体(设施巡检)", "安保智能体(安防监控)",
                       "物业数据大屏", "报修工单自动派发", "业主满意度分析"],
             "agents": ["guanjia", "gongcheng", "anbao"], "diff": "三智能体协同 vs 单一系统"},
            {"id": "sol_invest_decision", "name": "房产投资决策平台", "cat": ProductCategory.INDUSTRY_SOLUTION,
             "seg": MarketSegment.ENTERPRISE, "model": "subscription", "price": 180000, "range": "12-25万/年",
             "desc": "面向投资机构的城市热力图+政策预警+估值模型一体化数据服务",
             "features": ["全国城市热力图", "政策变化实时预警", "AI估值模型", "竞品分析",
                       "投资组合管理", "风险评级报告"],
             "agents": ["zhouyu", "luxun"], "diff": "预测 vs 回顾"},
            {"id": "serv_deep_report", "name": "深度分析报告(单份)", "cat": ProductCategory.VALUE_ADDED_SERVICE,
             "seg": MarketSegment.PUBLIC, "model": "per_task", "price": 49, "range": "49元/份",
             "desc": "AI生成的深度房产分析报告，含估值/趋势/风险/建议，免费用户可预览摘要",
             "features": ["完整PDF报告(20+页)", "数据来源标注", "三种估值方法交叉验证",
                       "投资建议(买/持/卖)", "风险提示"],
             "diff": "AI+人工复核 vs 纯AI"},
            {"id": "serv_human_review", "name": "人工复核服务", "cat": ProductCategory.VALUE_ADDED_SERVICE,
             "seg": MarketSegment.PUBLIC, "model": "per_task", "price": 99, "range": "99元/次",
             "desc": "由持证专业房产估价师对AI生成的报告进行人工审核和修正",
             "features": ["持证估价师审核", "24小时内返回", "修改标注清晰", "质量保证"],
             "diff": "人机协作 vs 纯机器"},
            {"id": "serv_private_deploy", "name": "私有化部署服务", "cat": ProductCategory.DEPLOYMENT_SERVICE,
             "seg": MarketSegment.ENTERPRISE, "model": "project", "price": 200000, "range": "10-30万一次性",
             "desc": "一次性收取的私有化部署费用，含环境搭建+数据迁移+培训",
             "features": ["服务器环境搭建", "数据迁移", "团队培训(2天)", "上线支持(1个月)",
                       "年度维护费另计"],
             "diff": "完全自主 vs SaaS依赖"},
            {"id": "cert_agent_training", "name": "智能估价师认证培训", "cat": ProductCategory.CERTIFICATION_TRAINING,
             "seg": MarketSegment.ACADEMIC, "model": "per_user", "price": 2999, "range": "1999-3999元/人",
             "desc": "与估价师学会联合推出的AI辅助估价师认证培训课程",
             "features": ["40课时在线课程", "实操作练习", "结业考试", "认证证书", "就业推荐"],
             "diff": "AI增强 vs 传统培训"},
        ]
        for pc in products_config:
            product = CommercialProduct(
                product_id=pc["id"], name=pc["name"], category=pc["cat"],
                target_segment=pc["seg"], pricing_model=pc["model"],
                base_price_cny=pc["price"], price_range=pc["range"],
                description=pc["desc"], features=pc.get("features", []),
                included_agents=pc.get("agents", []),
                deployment_type=pc.get("deployment", "cloud"),
                customization_level=pc.get("customization", "standard"),
                differentiation=pc.get("diff", ""),
            )
            self._products[pc["id"]] = product

    def record_sale(self, customer_id: str, customer_name: str,
                    product_id: str, amount: float,
                    tier: PricingTier = PricingTier.BASIC,
                    channel: PromotionChannel = PromotionChannel.WORD_OF_MOUTH,
                    is_recurring: bool = False,
                    payment_method: str = "alipay") -> RevenueRecord:
        """记录销售收入"""
        product = self._products.get(product_id)
        rid = f"rev_{uuid.uuid4().hex[:8]}"
        commission = amount * 0.05 if product and product.category in (
            ProductCategory.INDUSTRY_SOLUTION,) else 0
        record = RevenueRecord(
            record_id=rid, date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            segment=(product.target_segment if product else MarketSegment.PUBLIC),
            product_id=product_id, product_name=(product.name if product else product_id),
            customer_id=customer_id, customer_name=customer_name,
            amount_cpy=amount, pricing_tier=tier,
            payment_method=payment_method, is_recurring=is_recurring,
            commission_deducted=commission, net_revenue=amount - commission,
            sales_channel=channel,
        )
        self._revenue_log.append(record)
        if product:
            product.sales_count += 1
            product.revenue_total += amount
        return record

    def get_product_catalog(self, segment_filter: Optional[MarketSegment] = None) -> List[Dict[str, Any]]:
        """获取产品目录"""
        catalog = []
        for pid, product in self._products.items():
            if segment_filter and product.target_segment != segment_filter:
                continue
            catalog.append({
                "product_id": pid, "name": product.name,
                "category": product.category.value, "segment": product.target_segment.value,
                "price_range": product.price_range, "description": product.description[:60],
                "features_count": len(product.features), "sales_count": product.sales_count,
                "revenue_total": round(product.revenue_total, 0),
                "rating": round(product.avg_rating, 1), "active": product.active,
            })
        return sorted(catalog, key=lambda x: x["revenue_total"], reverse=True)

    def get_revenue_analytics(self, days: int = 30) -> Dict[str, Any]:
        """收入分析"""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        recent = [r for r in self._revenue_log if r.date >= cutoff]
        if not recent:
            return {"period": f"近{days}天", "total_revenue": 0}
        total = sum(r.amount_cpy for r in recent)
        mrr = sum(r.amount_cpy for r in recent if r.is_recurring)
        by_segment = defaultdict(float)
        by_product = defaultdict(float)
        by_channel = defaultdict(float)
        by_tier = defaultdict(int)
        for r in recent:
            by_segment[r.segment.value] += r.amount_cpy
            by_product[r.product_name] += r.amount_cpy
            by_channel[r.sales_channel.value] += r.amount_cpy
            by_tier[r.pricing_tier.value] += 1
        return {
            "period": f"近{days}天", "total_revenue_cny": round(total, 2),
            "mrr_cny": round(mrr, 2), "arr_estimate_cny": round(mrr * 12, 2),
            "transaction_count": len(recent),
            "avg_transaction_cny": round(total / max(len(recent), 1), 2),
            "by_segment": {k: round(v, 2) for k, v in by_segment.items()},
            "by_product": dict(sorted(by_product.items(), key=lambda x: x[1], reverse=True)[:8]),
            "by_channel": dict(by_channel),
            "paying_customers": len(set(r.customer_id for r in recent)),
            "recurring_ratio": round(len([r for r in recent if r.is_recurring]) / max(len(recent), 1) * 100, 2),
        }


# ==================== Part E: 变现节奏篇 — 四阶段推进追踪 ====================


class MonetizationTimelineTracker:
    """变现节奏追踪器 — 四阶段里程碑管理"""

    PHASE_CONFIG = {
        MonetizationPhase.VALIDATION: {
            "duration_months": 3, "target_revenue": 0, "target_customers": 0,
            "key_actions": ["完成产品内测", "招募10家免费试用企业", "收集5个完整案例",
                         "建立销售流程", "确定核心定价", "准备营销物料"],
            "success_criteria": ["≥10家试用企业", "≥5个完整案例", "NPS≥40"],
        },
        MonetizationPhase.LAUNCH: {
            "duration_months": 3, "target_revenue": 75000, "target_customers": 10,
            "key_actions": ["正式发布基础版+专业版", "签约首批付费客户(目标10家)",
                         "启动内容营销(博客+案例+视频)", "建立合作伙伴关系(≥3家)",
                         "开通支付系统", "建立客户成功团队"],
            "success_criteria": ["MRR≥1万", "付费客户≥10", "续约率≥60%"],
        },
        MonetizationPhase.EXPANSION: {
            "duration_months": 6, "target_revenue": 750000, "target_customers": 50,
            "key_actions": ["推出行业解决方案(智慧物业/投资决策)", "开发者生态初具规模(≥50个Skill)",
                         "拓展政府端/协会端项目", "建立渠道代理网络",
                         "品牌曝光提升(行业媒体覆盖)", "产品线扩展(命理/留学等)"],
            "success_criteria": ["ARR≥100万", "付费客户≥50", "月增长率≥15%"],
        },
        MonetizationPhase.MATURITY: {
            "duration_months": 12, "target_revenue": 4000000, "target_customers": 200,
            "key_actions": ["五端协同形成闭环", "年收入稳定增长300-500万",
                         "建立行业壁垒(数据/网络/品牌)", "考虑融资或战略投资",
                         "国际化探索", "平台生态自我演化"],
            "success_criteria": ["ARR≥400万", "市场份额领先", "净利润率≥20%"],
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._milestones: List[MonetizationMilestone] = []
        self._current_phase = MonetizationPhase.VALIDATION
        self._phase_start_date = datetime.now(timezone.utc).isoformat()
        self._phase_history: List[Dict[str, Any]] = []
        self._init_milestones()

    def _init_milestones(self) -> None:
        """初始化各阶段里程碑"""
        for phase, cfg in self.PHASE_CONFIG.items():
            ms = MonetizationMilestone(
                milestone_id=f"ms_{phase.value}_{uuid.uuid4().hex[:6]}",
                phase=phase, name=f"{phase.value}目标",
                target_date=(datetime.now(timezone.utc) +
                           timedelta(days=cfg["duration_months"] * 30)).strftime("%Y-%m-%d"),
                target_revenue_cpy=cfg["target_revenue"],
                target_customers=cfg["target_customers"],
                key_actions=cfg["key_actions"],
                status="pending",
            )
            self._milestones.append(ms)

    def advance_phase(self, new_phase: Optional[MonetizationPhase] = None) -> Dict[str, Any]:
        """进入下一阶段"""
        phases_order = [MonetizationPhase.VALIDATION, MonetizationPhase.LAUNCH,
                        MonetimizationPhase.EXPANSION, MonetizationPhase.MATURITY]
        current_idx = phases_order.index(self._current_phase)
        self._phase_history.append({
            "phase": self._current_phase.value,
            "start_date": self._phase_start_date,
            "end_date": datetime.now(timezone.utc).isoformat(),
        })

        if new_phase:
            self._current_phase = new_phase
        elif current_idx < len(phases_order) - 1:
            self._current_phase = phases_order[current_idx + 1]

        self._phase_start_date = datetime.now(timezone.utc).isoformat()
        cfg = self.PHASE_CONFIG.get(self._current_phase, {})
        logger.info(f"[变现节奏] 进入阶段: {self._current_phase.value}")
        return {
            "new_phase": self._current_phase.value,
            "target_revenue_cpy": cfg.get("target_revenue", 0),
            "target_customers": cfg.get("target_customers", 0),
            "key_actions": cfg.get("key_actions", []),
            "duration_months": cfg.get("duration_months", 0),
        }

    def update_milestone_progress(self, milestone_id: str,
                                  completed_action: Optional[str] = None,
                                  actual_revenue: float = 0,
                                  actual_customers: int = 0) -> None:
        """更新里程碑进度"""
        for ms in self._milestones:
            if ms.milestone_id == milestone_id:
                if completed_action:
                    ms.completed_actions.append(completed_action)
                if actual_revenue > 0:
                    ms.actual_revenue_cpy += actual_revenue
                if actual_customers > 0:
                    ms.actual_customers += actual_customers
                progress = len(ms.completed_actions) / max(len(ms.key_actions), 1) * 100
                revenue_progress = min(ms.actual_revenue_cpy / max(ms.target_revenue_cpy, 1) * 100, 100)
                customer_progress = min(ms.actual_customers / max(ms.target_customers, 1) * 100, 100)
                ms.progress_pct = (progress * 0.4 + revenue_progress * 0.35 + customer_progress * 0.25)
                if ms.progress_pct >= 95 and ms.status != "completed":
                    ms.status = "completed"
                    ms.achieved_at = datetime.now(timezone.utc).isoformat()
                elif ms.progress_pct > 0 and ms.status == "pending":
                    ms.status = "in_progress"
                break

    def get_timeline_dashboard(self) -> Dict[str, Any]:
        """获取时间线仪表盘"""
        current_cfg = self.PHASE_CONFIG.get(self._current_phase, {})
        phase_milestones = [ms for ms in self._milestones if ms.phase == self._current_phase]
        all_phases_status = []
        for phase in [MonetizationPhase.VALIDATION, MonetizationPhase.LAUNCH,
                      MonetizationPhase.EXPANSION, MonetizationPhase.MATURATION]:
            phase_ms = [ms for ms in self._milestones if ms.phase == phase]
            if phase_ms:
                avg_progress = statistics.mean([ms.progress_pct for ms in phase_ms])
                all_phases_status.append({
                    "phase": phase.value, "is_current": phase == self._current_phase,
                    "progress": round(avg_progress, 1), "status": phase_ms[0].status,
                    "target_revenue": phase_ms[0].target_revenue_cpy,
                    "actual_revenue": phase_ms[0].actual_revenue_cpy,
                })

        return {
            "current_phase": self._current_phase.value,
            "phase_start": self._phase_start_date,
            "phase_target_revenue_cpy": current_cfg.get("target_revenue", 0),
            "phase_target_customers": current_cfg.get("target_customers", 0),
            "phase_key_actions": current_cfg.get("key_actions", []),
            "phase_success_criteria": current_cfg.get("success_criteria", []),
            "milestone_details": [{
                "id": ms.milestone_id, "name": ms.name, "status": ms.status,
                "progress": round(ms.progress_pct, 1),
                "actions_done": f"{len(ms.completed_actions)}/{len(ms.key_actions)}",
                "revenue": f"{ms.actual_revenue_cpy:.0f}/{ms.target_revenue_cpy:.0f}万",
                "customers": f"{ms.actual_customers}/{ms.target_customers}",
            } for ms in phase_milestones],
            "all_phases": all_phases_status,
            "phases_completed": sum(1 for ps in all_phases_status if ps["status"] == "completed"),
        }


# ==================== Part F: 推广变现总协调器 — 全景看板 ====================


class PromotionMonetizationOrchestrator:
    """推广变现总协调器 — 统一管理六大模块 + 生成推广变现全景看板"""

    ALL_MODULES = [
        "FiveSegmentMarketAnalyzer", "AgentWorkHourPricingEngine",
        "ContentMarketingEngine", "EcosystemPartnershipManager",
        "CommercialProductManager", "MonetizationTimelineTracker",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.market_analyzer = FiveSegmentMarketAnalyzer(config=self.config.get("market", {}))
        self.pricing_engine = AgentWorkHourPricingEngine(config=self.config.get("pricing", {}))
        self.content_engine = ContentMarketingEngine(config=self.config.get("content", {}))
        self.partnership_mgr = EcosystemPartnershipManager(config=self.config.get("partnership", {}))
        self.product_mgr = CommercialProductManager(config=self.config.get("product", {}))
        self.timeline_tracker = MonetizationTimelineTracker(config=self.config.get("timeline", {}))
        self._dashboard_history: List[PromotionDashboardData] = []

    def initialize_all(self) -> Dict[str, Any]:
        """初始化所有模块"""
        self.partnership_mgr.get_default_partnerships()
        results = {
            "market_segments": self.market_analyzer.get_all_segments_overview(),
            "pricing_plans": len(self.pricing_engine._pricing_plans),
            "products": len(self.product_mgr._products),
            "partners": len(self.partnership_mgr._partnerships),
            "current_phase": self.timeline_tracker._current_phase.value,
        }
        logger.info("[推广变现总管] 所有模块初始化完成")
        return results

    def simulate_business_activity(self, num_days: int = 30) -> None:
        """模拟业务活动(用于演示看板数据)"""
        users = [f"user_demo_{i}" for i in range(random.randint(50, 200))]
        for u in users:
            tier = random.choices([PricingTier.FREE, PricingTier.BASIC,
                                PricingTier.PROFESSIONAL], weights=[0.6, 0.3, 0.1])[0]
            self.pricing_engine.register_user_tier(u, tier)
            if random.random() < 0.3:
                self.pricing_engine.grant_registration_bonus(u)

        for _ in range(random.randint(100, 500)):
            u = random.choice(users)
            self.pricing_engine.consume_work_hours(
                u, random.choice(["房产估值", "市场分析", "政策查询", "投资计算"]),
                f"测试任务-{random.randint(1,999)}",
                random.choice(["zhouyu", "luxun", "zhugeliang"]),
                random.randint(500, 5000), random.uniform(0.5, 1.5))

        ideas = self.content_engine.generate_content_ideas(8)
        for idea in ideas[:5]:
            ct = ContentType(idea["type"])
            ch = PromotionChannel(random.choice(list(PromotionChannel)))
            content = self.content_engine.create_content(idea["title"], ct, ch)
            self.content_engine.publish_content(content.content_id)

        for _ in range(random.randint(5, 20)):
            seg = random.choice(list(MarketSegment))
            self.product_mgr.record_sale(
                f"cust_{uuid.uuid4().hex[:6]}",
                f"{'某' if random.random()<0.5 else 'XX'}{random.choice(['科技','置业','投资','教育'])}公司",
                random.choice(list(self.product_mgr._products.keys())),
                random.choice([69, 299, 999, 49000, 99000, 49, 99, 200000]),
                random.choice(list(PricingTier)),
                random.choice(list(PromotionChannel)),
                is_recurring=(random.random() < 0.4),
            )

    def generate_dashboard(self) -> PromotionDashboardData:
        """生成推广变现全景看板"""
        did = f"promo_dash_{uuid.uuid4().hex[:8]}"
        market_overview = self.market_analyzer.get_all_segments_overview()
        pricing_stats = self.pricing_engine.get_engine_stats()
        content_report = self.content_engine.get_content_performance_report(30)
        partner_dash = self.partnership_mgr.get_partnership_dashboard()
        revenue_analytics = self.product_mgr.get_revenue_analytics(30)
        timeline_dash = self.timeline_tracker.get_timeline_dashboard()
        product_catalog = self.product_mgr.get_product_catalog()
        billing_samples = [self.pricing_engine.get_user_billing_summary(u)
                          for u in list(self.pricing_engine._user_tiers.keys())[:5]]

        total_rev = revenue_analytics.get("total_revenue_cpy", 0)
        mrr = revenue_analytics.get("mrr_cpy", 0)
        arr_est = revenue_analytics.get("arr_estimate_cpy", 0)

        dashboard = PromotionDashboardData(
            dashboard_id=did, date_range="近30天",
            total_revenue_cpy=total_rev, mrr_cpy=mrr, arr_cpy=arr_est,
            paying_customers=revenue_analytics.get("paying_customers", 0),
            trial_customers=len([u for u, t in self.pricing_engine._user_tiers.items()
                              if t == PricingTier.FREE]),
            conversion_trial_to_paid=round(
                revenue_analytics.get("paying_customers", 0) /
                max(revenue_analytics.get("paying_customers", 0) +
                    len([u for u, t in self.pricing_engine._user_tiers.items()
                         if t == PricingTier.FREE]), 1) * 100, 2),
            revenue_by_segment=revenue_analytics.get("by_segment", {}),
            revenue_by_product={k: v for k, v in list(revenue_analytics.get("by_product", {}).items())[:8]},
            revenue_by_channel=revenue_analytics.get("by_channel", {}),
            top_products=[{"name": p["name"], "revenue": p["revenue_total"],
                          "sales": p["sales_count"]} for p in product_catalog[:6]],
            active_partnerships=partner_dash["active_partnerships"],
            content_published_this_month=len(
                [c for c in self.content_engine._content_library.values() if c.status == "published"]),
            content_total_views=content_report.get("total_views", 0),
            content_avg_ctr=content_report.get("overall_ctr", 0),
            points_issued_total=pricing_stats["total_points_issued"],
            points_redeemed_total=pricing_stats["total_points_redeemed"],
            work_hours_consumed_total=pricing_stats["total_work_hours_consumed"],
            monetization_phase=self.timeline_tracker._current_phase,
            phase_progress=timeline_dash,
            milestone_status=timeline_dash.get("milestone_details", []),
            recommendations=self._generate_recommendations(revenue_analytics, timeline_dash),
        )
        self._dashboard_history.append(dashboard)
        return dashboard

    def _generate_recommendations(self, revenue_data: Dict,
                                    timeline_data: Dict) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recs = []
        total_rev = revenue_data.get("total_revenue_cpy", 0)
        phase = timeline_data.get("current_phase", "")

        if phase == "验证期":
            recs.append({"category": "阶段目标", "priority": "高",
                        "action": "加速免费试用企业招募，目标从当前{}家提升至10家".format(
                            len(self.market_analyzer._lead_pipeline)),
                        "expected_impact": "为启动期储备足够案例"})
            recs.append({"category": "产品打磨", "priority": "高",
                        "action": "完善核心场景(估值/咨询/报告)的用户体验，目标NPS≥40",
                        "expected_impact": "提高付费转化率基线"})
        elif phase == "启动期":
            recs.append({"category": "收入增长", "priority": "高",
                        "action": "重点突破企业端(⭐⭐⭐⭐⭐)，推出定制化演示+POC方案",
                        "expected_impact": "提升客单价至10万+/年"})
            recs.append({"category": "内容营销", "priority": "中",
                        "action": "保持每周2篇技术博客+1个案例故事+4条短视频的内容产出节奏",
                        "expected_impact": "自然流量增长30%+"})

        if total_rev < 10000:
            recs.append({"category": "紧急行动", "priority": "高",
                        "action": "月收入低于1万，建议立即启动首单优惠政策(首月5折)+老客户转介绍奖励(返佣10%)",
                        "expected_impact": "快速提升现金流"})
        if self.pricing_engine._user_tiers:
            free_ratio = len([u for u, t in self.pricing_engine._user_tiers.items()
                             if t == PricingTier.FREE]) / len(self.pricing_engine._user_tiers)
            if free_ratio > 0.7:
                recs.append({"category": "转化优化", "priority": "中",
                            "action": f"免费用户占比{free_ratio*100:.0f}%过高，建议加强付费引导(报告解锁/高级功能墙/限时优惠)",
                            "expected_impact": "付费转化率提升5-10%"})

        recs.append({"category": "长期布局", "priority": "中",
                     "action": "院校端免费教学版持续投入，培养未来企业端用户(学生→从业者→决策者)",
                     "expected_impact": "6-12个月后收获企业端订单"})
        recs.append({"category": "差异化竞争", "priority": "低",
                     "action": "强化'决策价值'定位——不是聊天是决策，用户省下的钱>>平台费用",
                     "expected_impact": "支撑溢价定价策略"})
        return recs[:8]

    def render_dashboard_text(self, dashboard: Optional[PromotionDashboardData] = None) -> str:
        """渲染文本推广变现看板"""
        d = dashboard or self.generate_dashboard()
        lines = []
        lines.append("=" * 78)
        lines.append("  房都督AI平台 · 推广变现全景看板 (Promotion & Monetization Dashboard)")
        lines.append("  内测期 · 全部前三个月免费 | 注册赠送1,000积分")
        lines.append("=" * 78)
        lines.append("")
        lines.append(f"  💰 总收入: ¥{d.total_revenue_cpy:,.0f} | "
                     f"MRR: ¥{d.mrr_cpy:,.0f}/月 | ARR(估): ¥{d.arr_cpy:,.0f}/年 | "
                     f"阶段: 【{d.monetization_phase.value}】")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  🎯 五端市场机会评分")
        lines.append("-" * 78)
        for seg in d.revenue_by_segment:
            rev = d.revenue_by_segment[seg]
            bar_len = min(int(rev / max(d.total_revenue_cpy, 1) * 40), 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            lines.append(f"  {seg:<10s} │ {bar} │ ¥{rev:>10,.0f}")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  📦 热门产品 TOP6")
        lines.append("-" * 78)
        for tp in d.top_products:
            lines.append(f"  💎 {tp['name']:<24s} │ 收入¥{tp['revenue']:>10,.0f} │ 销量{tp['sales']}单")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  ⏱️ 智能体工时 & 积分系统")
        lines.append("-" * 78)
        lines.append(f"  本月工时消耗: {d.work_hours_consumed_total:,.1f}h | "
                     f"积分发: {d.points_issued_total:,} | 兑换: {d.points_redeemed_total:,} | "
                     f"兑换率: {d.points_redeemed_total/max(d.points_issued_total,1)*100:.1f}%")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  📢 内容营销效果")
        lines.append("-" * 78)
        lines.append(f"  本月发布: {d.content_published_this_month}篇 | "
                     f"总阅读: {d.content_total_views:,} | 平均CTR: {d.content_avg_ctr}%")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  🤝 生态合作")
        lines.append("-" * 78)
        lines.append(f"  活跃合作: {d.active_partnerships}家 | "
                     f"付费客户: {d.paying_customers} | 试用客户: {d.trial_customers}")
        lines.append(f"  试用→付费转化率: {d.conversion_trial_to_paid}% | "
                     f"续订/复购率: {d.revenue_by_channel.get('WORD_OF_MOUTH', 0):.0f}%")
        lines.append("")
        lines.append("-" * 78)
        lines.append(f"  📈 变现阶段进度: 【{d.monetization_phase.value}】")
        lines.append("-" * 78)
        for ms in d.milestone_status[:4]:
            icon = "✅" if ms["status"] == "completed" else ("🔄" if ms["status"] == "in_progress" else "⬜")
            lines.append(f"  {icon} {ms['name']:<20s} | 进度{ms['progress']:>5.1f}% | "
                         f"{ms['actions_done']} | {ms['revenue']}")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  💡 AI优化建议")
        lines.append("-" * 78)
        for rec in d.recommendations[:5]:
            prio = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(rec.get("priority", "中"), "⚪")
            lines.append(f"  {prio} [{rec['category']}] {rec['action'][:65]}")
            lines.append(f"      预期效果: {rec.get('expected_impact', '')}")
        lines.append("")
        lines.append("=" * 78)
        return "\n".join(lines)


# ==================== 全局实例 ====================

five_segment_market_analyzer = FiveSegmentMarketAnalyzer()
agent_work_hour_pricing_engine = AgentWorkHourPricingEngine()
content_marketing_engine = ContentMarketingEngine()
ecosystem_partnership_manager = EcosystemPartnershipManager()
commercial_product_manager = CommercialProductManager()
monetization_timeline_tracker = MonetizationTimelineTracker()

promotion_monetization_orchestrator = PromotionMonetizationOrchestrator()
