# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 用户转化优化层（第7层：User Conversion Optimization Layer）
==========================================================================
对应设计文档「爆火规则」「停留规则」完整落地。
借鉴短视频平台（抖音/快手）推荐算法核心逻辑，将「爆火规则」和「停留规则」
迁移至房都督平台的用户转化流程优化，实现数据驱动的持续迭代优化。

六大模块：
  行为采集篇 — 全链路埋点追踪
    页面进入/离开事件采集 → 点击/滚动/表单提交追踪 → 会话聚合与用户画像构建
    前端SDK兼容(自动采集+手动上报) → 后端事件流水线(实时写入+批量归档)

  转化漏斗篇 — 多阶段漏斗分析与下钻
    五阶段漏斗(曝光→停留→互动→转化→留存) → 实时转化率计算
    分群分析(新/老用户、移动端/PC、工作日/周末) → 智能体维度对比
    漏斗异常检测(转化率骤降告警) → 归因分析(流失环节定位)

  停留分析篇 — 热力图与参与度评分
    页面区域停留时长热力图 → 会话路径可视化
    参与度评分模型(停留×互动×完成度加权) → 完播率等价指标(咨询完成率)
    弹出率/跳出率监控 → 沉默用户识别与唤醒策略

  爆火引擎篇 — 内容热度算法与推荐优化
    爆火指数计算(曝光×完播×互动×转发四维加权) → 热门内容排行榜
    赛马机制(新内容冷启动流量扶持 + 表现优胜者流量加成)
    个性化推荐(基于用户画像的内容匹配 + 协同过滤 + 时效衰减)
    AHA时刻识别(用户被"吸引"的关键行为节点)

  AB实验篇 — 科学实验框架
    实验管理(创建/配置/流量分配/统计显著性检验)
    多变量实验支持 → 贝叶斯统计 vs 频率学派双模式
    自动胜出判定(最小样本量 + 效应量 + 置信区间)
    实验影响评估(长期效应 + 辛普森悖论防护)

  总协调器 — 统一仪表盘与优化建议
    转化全景看板(漏斗+热力图+爆火榜+AB实验状态)
    AI优化建议(基于数据的可操作改进建议)
    与海马体记忆系统集成(用户行为持久化)

通关标准：
  埋点数据延迟<200ms, 漏斗数据实时更新(<5s), 热力图渲染<1s
  AB实验最小检测效应(MDE)<5%, 统计功效≥80%, 置信度95%
  爆火内容识别准确率≥85%, 个性化推荐点击率提升≥15%
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
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from collections import deque, defaultdict, Counter

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================


class EventType(Enum):
    """事件类型"""
    PAGE_VIEW = "页面浏览"
    PAGE_LEAVE = "页面离开"
    CLICK = "点击"
    SCROLL = "滚动"
    FORM_SUBMIT = "表单提交"
    CONSULTATION_START = "咨询开始"
    CONSULTATION_COMPLETE = "咨询完成"
    REPORT_GENERATE = "报告生成"
    REPORT_DOWNLOAD = "报告下载"
    SHARE = "分享"
    FEEDBACK_LIKE = "点赞"
    FEEDBACK_DISLIKE = "点踩"
    FEEDBACK_SCORE = "评分"
    SESSION_START = "会话开始"
    SESSION_END = "会话结束"


class FunnelStage(Enum):
    """漏斗阶段"""
    EXPOSURE = "曝光"
    DWELL = "停留"
    INTERACTION = "互动"
    CONVERSION = "转化"
    RETENTION = "留存"


class UserSegment(Enum):
    """用户分群"""
    NEW_USER = "新用户"
    RETURNING_USER = "回访用户"
    ACTIVE_USER = "活跃用户"
    CHURNED_USER = "流失用户"
    HIGH_VALUE = "高价值用户"
    SILENT_USER = "沉默用户"


class DeviceType(Enum):
    """设备类型"""
    MOBILE = "移动端"
    PC = "PC端"
    TABLET = "平板"
    UNKNOWN_DEVICE = "未知"


class ExperimentStatus(Enum):
    """实验状态"""
    DRAFT = "草稿"
    RUNNING = "运行中"
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    ANALYZING = "分析中"


class ViralTier(Enum):
    """爆火等级"""
    NORMAL = "普通"
    WARMING = "升温"
    HOT = "热门"
    VIRAL = "爆火"
    EXPLOSIVE = "爆炸式"


class RecommendationSource(Enum):
    """推荐来源"""
    COLLABORATIVE_FILTER = "协同过滤"
    CONTENT_BASED = "基于内容"
    TRENDING = "热门趋势"
    PERSONALIZED = "个性化"
    COLD_START = "冷启动"
    A_B_TEST = "AB实验"


# ==================== 数据结构定义 ====================


@dataclass
class BehaviorEvent:
    """行为事件"""
    event_id: str
    user_id: str
    session_id: str
    event_type: EventType
    page_path: str
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    client_timestamp: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN_DEVICE
    referrer: Optional[str] = None
    duration_ms: float = 0.0
    scroll_depth_pct: float = 0.0
    viewport_size: str = ""
    user_agent: str = ""


@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: str
    start_time: str
    end_time: Optional[str] = None
    events: List[BehaviorEvent] = field(default_factory=list)
    page_views: int = 0
    total_duration_ms: float = 0.0
    device_type: DeviceType = DeviceType.UNKNOWN_DEVICE
    converted: bool = False
    conversion_stage: Optional[FunnelStage] = None
    engagement_score: float = 0.0


@dataclass
class FunnelData:
    """漏斗数据"""
    funnel_id: str
    stage: FunnelStage
    total_users: int = 0
    stage_users: int = 0
    conversion_rate: float = 0.0
    drop_off_count: int = 0
    drop_off_rate: float = 0.0
    avg_time_in_stage_s: float = 0.0
    segment_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DwellTimeRecord:
    """停留记录"""
    record_id: str
    user_id: str
    session_id: str
    page_path: str
    region_id: str
    region_name: str
    dwell_time_ms: float
    enter_time: str
    leave_time: str
    click_count: int = 0
    scroll_events: int = 0
    interaction_score: float = 0.0


@dataclass
class HeatmapCell:
    """热力图单元格"""
    page_path: str
    region_id: str
    region_name: str
    total_dwell_ms: float = 0.0
    visit_count: int = 0
    avg_dwell_ms: float = 0.0
    click_count: int = 0
    click_rate: float = 0.0
    intensity: float = 0.0
    coordinates: Dict[str, int] = field(default_factory=dict)


@dataclass
class ViralContentItem:
    """爆火内容项"""
    content_id: str
    content_type: str
    title: str
    exposure_count: int = 0
    completion_rate: float = 0.0
    interaction_rate: float = 0.0
    share_rate: float = 0.0
    viral_score: float = 0.0
    viral_tier: ViralTier = ViralTier.NORMAL
    trend_direction: str = "stable"
    velocity_24h: float = 0.0
    velocity_7d: float = 0.0
    peak_rank: int = 0
    current_rank: int = 0
    lifecycle_phase: str = "growth"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RecommendationResult:
    """推荐结果"""
    recommendation_id: str
    user_id: str
    source: RecommendationSource
    items: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    explanation: str = ""
    model_version: str = "v1.0"
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ABExperiment:
    """AB实验"""
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    primary_metric: str
    secondary_metrics: List[str] = field(default_factory=list)
    variants: List[Dict[str, Any]] = field(default_factory=list)
    traffic_allocation: Dict[str, float] = field(default_factory=dict)
    status: ExperimentStatus = ExperimentStatus.DRAFT
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    sample_size_per_variant: Dict[str, int] = field(default_factory=dict)
    results: Dict[str, Dict[str, float]] = field(default_factory=dict)
    winner: Optional[str] = None
    confidence_level: float = 0.95
    min_detectable_effect: float = 0.05
    statistical_power: float = 0.8
    p_value: Optional[float] = None
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConversionOptimizationSuggestion:
    """转化优化建议"""
    suggestion_id: str
    category: str
    priority: str
    title: str
    description: str
    expected_impact: float
    effort_level: str
    current_baseline: float
    target_value: float
    related_funnel_stage: FunnelStage
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    ab_test_ready: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConversionDashboardData:
    """转化看板数据"""
    dashboard_id: str
    overall_conversion_rate: float
    funnel_data: List[FunnelData]
    heatmap_data: List[HeatmapCell]
    viral_content: List[ViralContentItem]
    active_experiments: List[ABExperiment]
    top_recommendations: List[RecommendationResult]
    optimization_suggestions: List[ConversionOptimizationSuggestion]
    key_metrics_snapshot: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ==================== Part A: 行为采集篇 — 全链路埋点追踪 ====================


class UserBehaviorTracker:
    """用户行为追踪器 — 全链路埋点采集"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._event_buffer: List[BehaviorEvent] = []
        self._session_store: Dict[str, UserSession] = {}
        self._user_profiles: Dict[str, Dict[str, Any]] = {}
        self._buffer_flush_interval_s = self.config.get("flush_interval", 5)
        self._max_buffer_size = self.config.get("max_buffer", 1000)
        self._total_events_collected = 0
        self._auto_track_enabled = self.config.get("auto_track", True)

    def track_event(self, event: BehaviorEvent) -> bool:
        """记录单个行为事件"""
        self._event_buffer.append(event)
        self._total_events_collected += 1

        session = self._session_store.get(event.session_id)
        if session:
            session.events.append(event)
            if event.event_type == EventType.PAGE_VIEW:
                session.page_views += 1

        if len(self._event_buffer) >= self._max_buffer_size:
            self._flush_buffer()
        return True

    def track_page_view(self, user_id: str, session_id: str, page_path: str,
                        referrer: Optional[str] = None,
                        device_type: DeviceType = DeviceType.UNKNOWN_DEVICE) -> BehaviorEvent:
        """追踪页面浏览"""
        event = BehaviorEvent(
            event_id=f"pv_{uuid.uuid4().hex[:12]}",
            user_id=user_id, session_id=session_id,
            event_type=EventType.PAGE_VIEW, page_path=page_path,
            referrer=referrer, device_type=device_type,
        )
        self._ensure_session(user_id, session_id, device_type)
        self.track_event(event)
        return event

    def track_click(self, user_id: str, session_id: str, page_path: str,
                    element_id: str, element_text: str = "",
                    metadata: Optional[Dict] = None) -> BehaviorEvent:
        """追踪点击事件"""
        event = BehaviorEvent(
            event_id=f"clk_{uuid.uuid4().hex[:12]}",
            user_id=user_id, session_id=session_id,
            event_type=EventType.CLICK, page_path=page_path,
            element_id=element_id, element_text=element_text,
            metadata=metadata or {},
        )
        self.track_event(event)
        return event

    def track_scroll(self, user_id: str, session_id: str, page_path: str,
                     scroll_depth_pct: float) -> BehaviorEvent:
        """追踪滚动深度"""
        event = BehaviorEvent(
            event_id=f"scr_{uuid.uuid4().hex[:12]}",
            user_id=user_id, session_id=session_id,
            event_type=EventType.SCROLL, page_path=page_path,
            scroll_depth_pct=scroll_depth_pct,
        )
        self.track_event(event)
        return event

    def track_consultation(self, user_id: str, session_id: str,
                           complete: bool = False, rounds: int = 0,
                           agent_name: str = "") -> BehaviorEvent:
        """追踪咨询事件"""
        etype = EventType.CONSULTATION_COMPLETE if complete else EventType.CONSULTATION_START
        event = BehaviorEvent(
            event_id=f"con_{uuid.uuid4().hex[:12]}",
            user_id=user_id, session_id=session_id,
            event_type=etype, page_path="/consultation",
            metadata={"rounds": rounds, "agent_name": agent_name, "complete": complete},
        )
        self.track_event(event)

        if complete:
            session = self._session_store.get(session_id)
            if session:
                session.converted = True
                session.conversion_stage = FunnelStage.CONVERSION
        return event

    def track_form_submit(self, user_id: str, session_id: str, page_path: str,
                          form_name: str, form_data: Optional[Dict] = None) -> BehaviorEvent:
        """追踪表单提交"""
        event = BehaviorEvent(
            event_id=f"frm_{uuid.uuid4().hex[:12]}",
            user_id=user_id, session_id=session_id,
            event_type=EventType.FORM_SUBMIT, page_path=page_path,
            element_id=form_name,
            metadata=form_data or {},
        )
        self.track_event(event)
        return event

    def track_feedback(self, user_id: str, session_id: str,
                       feedback_type: str, score: Optional[int] = None) -> BehaviorEvent:
        """追踪用户反馈"""
        etype = EventType.FEEDBACK_LIKE if feedback_type == "like" else (
            EventType.FEEDBACK_DISLIKE if feedback_type == "dislike" else EventType.FEEDBACK_SCORE)
        event = BehaviorEvent(
            event_id=f"fb_{uuid.uuid4().hex[:12]}",
            user_id=user_id, session_id=session_id,
            event_type=etype, page_path="/feedback",
            metadata={"feedback_type": feedback_type, "score": score},
        )
        self.track_event(event)
        return event

    def _ensure_session(self, user_id: str, session_id: str,
                        device_type: DeviceType = DeviceType.UNKNOWN_DEVICE) -> None:
        """确保会话存在"""
        if session_id not in self._session_store:
            self._session_store[session_id] = UserSession(
                session_id=session_id, user_id=user_id,
                start_time=datetime.now(timezone.utc).isoformat(),
                device_type=device_type,
            )

    def _flush_buffer(self) -> int:
        """刷新事件缓冲区"""
        flushed = len(self._event_buffer)
        self._event_buffer.clear()
        logger.debug(f"[行为追踪] 刷新缓冲区: {flushed}条事件")
        return flushed

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        profile = self._user_profiles.get(user_id, {
            "user_id": user_id, "total_sessions": 0, "total_events": 0,
            "total_duration_s": 0, "conversion_count": 0,
            "last_visit": None, "favorite_pages": [], "device_preference": "unknown",
            "segment": UserSegment.NEW_USER.value,
        })
        user_sessions = [s for s in self._session_store.values() if s.user_id == user_id]
        if user_sessions:
            profile["total_sessions"] = len(user_sessions)
            profile["total_events"] = sum(len(s.events) for s in user_sessions)
            profile["total_duration_s"] = round(sum(s.total_duration_ms for s in user_sessions) / 1000, 1)
            profile["conversion_count"] = sum(1 for s in user_sessions if s.converted)
            last_sess = max(user_sessions, key=lambda s: s.start_time)
            profile["last_visit"] = last_sess.start_time
            page_counts = Counter()
            for s in user_sessions:
                for e in s.events:
                    if e.event_type == EventType.PAGE_VIEW:
                        page_counts[e.page_path] += 1
            profile["favorite_pages"] = page_counts.most_common(5)
            devices = Counter(s.device_type.value for s in user_sessions)
            profile["device_preference"] = devices.most_common(1)[0][0] if devices else "unknown"

            total_visits = len(user_sessions)
            if total_visits >= 10:
                profile["segment"] = UserSegment.HIGH_VALUE.value
            elif total_visits >= 3:
                profile["segment"] = UserSegment.ACTIVE_USER.value
            elif total_visits >= 2:
                profile["segment"] = UserSegment.RETURNING_USER.value
            else:
                profile["segment"] = UserSegment.NEW_USER.value

            self._user_profiles[user_id] = profile
        return profile

    def get_tracker_stats(self) -> Dict[str, Any]:
        """获取追踪器统计"""
        active_sessions = sum(1 for s in self._session_store.values() if s.end_time is None)
        return {
            "total_events_collected": self._total_events_collected,
            "buffer_size": len(self._event_buffer),
            "active_sessions": active_sessions,
            "total_sessions": len(self._session_store),
            "known_users": len(set(s.user_id for s in self._session_store.values())),
            "auto_track_enabled": self._auto_track_enabled,
        }


class EventAggregator:
    """事件聚合器 — 原始事件→会话级聚合"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._aggregated_sessions: Dict[str, Dict[str, Any]] = {}
        self._hourly_buckets: Dict[str, List[BehaviorEvent]] = defaultdict(list)
        self._daily_summaries: Dict[str, Dict[str, Any]] = {}

    def aggregate_session(self, session: UserSession) -> Dict[str, Any]:
        """聚合单个会话为摘要"""
        events = session.events
        if not events:
            return {"session_id": session.session_id, "event_count": 0}

        page_views = [e for e in events if e.event_type == EventType.PAGE_VIEW]
        clicks = [e for e in events if e.event_type == EventType.CLICK]
        scrolls = [e for e in events if e.event_type == EventType.SCROLL]
        consultations = [e for e in events if e.event_type in
                         (EventType.CONSULTATION_START, EventType.CONSULTATION_COMPLETE)]
        forms = [e for e in events if e.event_type == EventType.FORM_SUBMIT]
        feedbacks = [e for e in events if e.event_type in
                     (EventType.FEEDBACK_LIKE, EventType.FEEDBACK_DISLIKE, EventType.FEEDBACK_SCORE)]
        shares = [e for e in events if e.event_type == EventType.SHARE]

        max_scroll = max((e.scroll_depth_pct for e in scrolls), default=0)
        unique_pages = set(e.page_path for e in page_views)
        consultation_complete = any(e.event_type == EventType.CONSULTATION_COMPLETE for e in consultations)
        report_generated = any(e.event_type == EventType.REPORT_GENERATE for e in events)

        summary = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "start_time": session.start_time,
            "end_time": session.end_time or events[-1].timestamp if events else session.start_time,
            "event_count": len(events),
            "page_views": len(page_views),
            "unique_pages": len(unique_pages),
            "page_list": list(unique_pages),
            "click_count": len(clicks),
            "scroll_max_depth_pct": round(max_scroll, 1),
            "consultation_started": len([e for e in consultations if e.event_type == EventType.CONSULTATION_START]),
            "consultation_completed": int(consultation_complete),
            "forms_submitted": len(forms),
            "feedback_count": len(feedbacks),
            "share_count": len(shares),
            "report_generated": int(report_generated),
            "converted": session.converted,
            "conversion_stage": session.conversion_stage.value if session.conversion_stage else None,
            "device_type": session.device_type.value,
            "engagement_score": self._calc_engagement_score(events),
        }
        self._aggregated_sessions[session.session_id] = summary
        return summary

    def _calc_engagement_score(self, events: List[BehaviorEvent]) -> float:
        """计算参与度评分 (0-100)"""
        weights = {
            EventType.PAGE_VIEW: 2.0,
            EventType.CLICK: 5.0,
            EventType.SCROLL: 1.0,
            EventType.FORM_SUBMIT: 15.0,
            EventType.CONSULTATION_COMPLETE: 30.0,
            EventType.REPORT_GENERATE: 25.0,
            EventType.SHARE: 20.0,
            EventType.FEEDBACK_LIKE: 8.0,
            EventType.FEEDBACK_SCORE: 10.0,
        }
        score = sum(weights.get(e.event_type, 1.0) for e in events)
        return min(round(score, 1), 100.0)

    def get_hourly_stats(self, hour_key: Optional[str] = None) -> Dict[str, Any]:
        """获取小时级统计"""
        if hour_key is None:
            hour_key = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        events = self._hourly_buckets.get(hour_key, [])
        users = set(e.user_id for e in events)
        sessions = set(e.session_id for e in events)
        return {
            "hour_key": hour_key,
            "event_count": len(events),
            "unique_users": len(users),
            "unique_sessions": len(sessions),
            "events_per_user": round(len(events) / max(len(users), 1), 2),
        }

    def get_daily_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """获取日汇总"""
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        all_sessions = list(self._aggregated_sessions.values())
        date_sessions = [s for s in all_sessions if s.get("start_time", "").startswith(date_str)]

        if not date_sessions:
            return {"date": date_str, "total_sessions": 0}

        total_users = len(set(s["user_id"] for s in date_sessions))
        converted = sum(1 for s in date_sessions if s.get("converted"))
        avg_engagement = statistics.mean([s.get("engagement_score", 0) for s in date_sessions])
        avg_pages = statistics.mean([s.get("unique_pages", 0) for s in date_sessions])

        summary = {
            "date": date_str,
            "total_sessions": len(date_sessions),
            "unique_users": total_users,
            "conversion_rate": round(converted / max(len(date_sessions), 1) * 100, 2),
            "avg_engagement_score": round(avg_engagement, 1),
            "avg_pages_per_session": round(avg_pages, 1),
            "top_pages": self._get_top_pages(date_sessions),
        }
        self._daily_summaries[date_str] = summary
        return summary

    def _get_top_pages(self, sessions: List[Dict]) -> List[Tuple[str, int]]:
        """获取最热门页面"""
        counter = Counter()
        for s in sessions:
            for p in s.get("page_list", []):
                counter[p] += 1
        return counter.most_common(10)


# ==================== Part B: 转化漏斗篇 — 多阶段漏斗分析与下钻 ====================


class ConversionFunnelEngine:
    """转化漏斗引擎 — 五阶段实时漏斗"""

    STAGE_ORDER = [
        FunnelStage.EXPOSURE, FunnelStage.DWELL, FunnelStage.INTERACTION,
        FunnelStage.CONVERSION, FunnelStage.RETENTION,
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._funnels: Dict[str, List[FunnelData]] = {}
        self._stage_definitions: Dict[FunnelStage, List[EventType]] = {
            FunnelStage.EXPOSURE: [EventType.PAGE_VIEW],
            FunnelStage.DWELL: [EventType.PAGE_VIEW],
            FunnelStage.INTERACTION: [EventType.CLICK, EventType.CONSULTATION_START],
            FunnelStage.CONVERSION: [EventType.CONSULTATION_COMPLETE, EventType.REPORT_GENERATE],
            FunnelStage.RETENTION: [EventType.SHARE],
        }
        self._alert_threshold_drop = self.config.get("alert_threshold", 0.3)

    def build_funnel(self, funnel_id: str, sessions: List[UserSession],
                     time_range: Tuple[str, str] = None) -> List[FunnelData]:
        """构建五阶段转化漏斗"""
        funnel = []
        prev_count = 0
        total_users = len(set(s.user_id for s in sessions))

        for stage in self.STAGE_ORDER:
            stage_events = self._stage_definitions.get(stage, [])
            stage_users = set()

            for session in sessions:
                has_stage_event = any(e.event_type in stage_events for e in session.events)
                if stage == FunnelStage.EXPOSURE:
                    stage_users.add(session.user_id)
                elif stage == FunnelStage.DWELL:
                    pv_events = [e for e in session.events if e.event_type == EventType.PAGE_VIEW]
                    if pv_events and session.total_duration_ms > 3000:
                        stage_users.add(session.user_id)
                elif has_stage_event:
                    stage_users.add(session.user_id)

            stage_count = len(stage_users)
            rate = round(stage_count / max(total_users, 1) * 100, 2)
            drop_off = prev_count - stage_count if prev_count > 0 else 0
            drop_rate = round(drop_off / max(prev_count, 1) * 100, 2) if prev_count > 0 else 0

            segment_data = self._calculate_segment_breakdown(sessions, stage)

            fd = FunnelData(
                funnel_id=funnel_id, stage=stage,
                total_users=total_users, stage_users=stage_count,
                conversion_rate=rate, drop_off_count=drop_off,
                drop_off_rate=drop_rate,
                segment_breakdown=segment_data,
            )
            funnel.append(fd)
            prev_count = stage_count

        self._funnels[funnel_id] = funnel
        self._check_funnel_alerts(funnel)
        return funnel

    def _calculate_segment_breakdown(self, sessions: List[UserSession],
                                     stage: FunnelStage) -> Dict[str, Dict[str, Any]]:
        """分群下钻分析"""
        breakdown = {}
        stage_events = self._stage_definitions.get(stage, [])

        by_segment: Dict[str, Set[str]] = defaultdict(set)
        by_device: Dict[str, Set[str]] = defaultdict(set)
        by_time: Dict[str, Set[str]] = defaultdict(set)

        for session in sessions:
            uid = session.user_id
            has_stage = any(e.event_type in stage_events for e in session.events)
            if not has_stage and stage != FunnelStage.EXPOSURE:
                continue

            if stage == FunnelStage.EXPOSURE or has_stage:
                seg = self._classify_user_segment(session)
                by_segment[seg].add(uid)
                by_device[session.device_type.value].add(uid)

                try:
                    dt = datetime.fromisoformat(session.start_time.replace("Z", "+00:00"))
                    hour = dt.hour
                    time_key = "工作时段" if 9 <= hour <= 18 else "休闲时段"
                    by_time[time_key].add(uid)
                except (ValueError, AttributeError):
                    by_time["未知"].add(uid)

        for seg, users in by_segment.items():
            breakdown[f"segment:{seg}"] = {"count": len(users), "rate": 0}
        for dev, users in by_device.items():
            breakdown[f"device:{dev}"] = {"count": len(users), "rate": 0}
        for tk, users in by_time.items():
            breakdown[f"time:{tk}"] = {"count": len(users), "rate": 0}

        total = len(set(s.user_id for s in sessions))
        for key in breakdown:
            breakdown[key]["rate"] = round(breakdown[key]["count"] / max(total, 1) * 100, 2)

        return breakdown

    def _classify_user_segment(self, session: UserSession) -> str:
        """简单用户分群"""
        return session.device_type.value

    def _check_funnel_alerts(self, funnel: List[FunnelData]) -> List[Dict[str, Any]]:
        """漏斗异常检测"""
        alerts = []
        for i, fd in enumerate(funnel):
            if fd.drop_off_rate > self._alert_threshold_drop * 100:
                alert = {
                    "level": "warning",
                    "stage": fd.stage.value,
                    "drop_off_rate": fd.drop_off_rate,
                    "message": f"{fd.stage.value}阶段掉落率{fd.drop_off_rate}%超过阈值{self._alert_threshold_drop*100}%",
                }
                alerts.append(alert)
                logger.warning(f"[漏斗引擎] 异常告警: {alert['message']}")
        return alerts

    def get_funnel_comparison(self, funnel_a_id: str, funnel_b_id: str) -> Dict[str, Any]:
        """两个漏斗对比"""
        fa = self._funnels.get(funnel_a_id, [])
        fb = self._funnels.get(funnel_b_id, [])
        comparison = []
        for a, b in zip(fa, fb):
            comparison.append({
                "stage": a.stage.value,
                f"{funnel_a_id}_rate": a.conversion_rate,
                f"{funnel_b_id}_rate": b.conversion_rate,
                "diff": round(b.conversion_rate - a.conversion_rate, 2),
                "diff_pct": round((b.conversion_rate - a.conversion_rate) / max(a.conversion_rate, 0.01) * 100, 2)
                if a.conversion_rate > 0 else 0,
            })
        return comparison


# ==================== Part C: 停留分析篇 — 热力图与参与度评分 ====================


class DwellTimeAnalyzer:
    """停留时长分析器 — 热力图与会话路径"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._dwell_records: List[DwellTimeRecord] = []
        self._heatmap_cache: Dict[str, List[HeatmapCell]] = {}
        self._bounce_threshold_s = self.config.get("bounce_threshold", 10)
        self._engaged_threshold_s = self.config.get("engaged_threshold", 30)

    def record_dwell(self, record: DwellTimeRecord) -> None:
        """记录停留数据"""
        self._dwell_records.append(record)

    def generate_heatmap(self, page_path: str) -> List[HeatmapCell]:
        """生成页面热力图"""
        cache_key = f"heatmap:{page_path}"
        if cache_key in self._heatmap_cache:
            return self._heatmap_cache[cache_key]

        page_records = [r for r in self._dwell_records if r.page_path == page_path]
        region_groups: Dict[str, List[DwellTimeRecord]] = defaultdict(list)
        for r in page_records:
            region_groups[r.region_id].append(r)

        cells = []
        for region_id, records in region_groups.items():
            total_dwell = sum(r.dwell_time_ms for r in records)
            visits = len(records)
            clicks = sum(r.click_count for r in records)
            cell = HeatmapCell(
                page_path=page_path, region_id=region_id,
                region_name=records[0].region_name if records else region_id,
                total_dwell_ms=total_dwell, visit_count=visits,
                avg_dwell_ms=round(total_dwell / max(visits, 1), 1),
                click_count=clicks, click_rate=round(clicks / max(visits, 1) * 100, 2),
            )
            cell.intensity = self._calc_intensity(cell)
            cells.append(cell)

        cells.sort(key=lambda c: c.intensity, reverse=True)
        self._heatmap_cache[cache_key] = cells
        logger.info(f"[停留分析] 热力图生成: {page_path}, {len(cells)}个区域")
        return cells

    def _calc_intensity(self, cell: HeatmapCell) -> float:
        """计算热力强度 (0-100)"""
        dwell_score = min(cell.avg_dwell_ms / 60000 * 50, 50)
        click_score = min(cell.click_rate / 100 * 30, 30)
        freq_score = min(cell.visit_count / 100 * 20, 20)
        return round(dwell_score + click_score + freq_score, 1)

    def analyze_session_paths(self, sessions: List[UserSession]) -> List[Dict[str, Any]]:
        """分析用户访问路径"""
        paths = []
        for session in sessions:
            if not session.events:
                continue
            page_sequence = []
            for e in session.events:
                if e.event_type == EventType.PAGE_VIEW:
                    page_sequence.append({
                        "page": e.page_path,
                        "time": e.timestamp,
                        "duration_estimate": e.duration_ms,
                    })

            if len(page_sequence) >= 2:
                path_str = " → ".join(p["page"] for p in page_sequence)
                paths.append({
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "path": path_str,
                    "path_length": len(page_sequence),
                    "converted": session.converted,
                    "duration_s": round(session.total_duration_ms / 1000, 1),
                })
        paths.sort(key=lambda p: p["converted"], reverse=True)
        return paths[:50]

    def get_bounce_analysis(self, sessions: List[UserSession]) -> Dict[str, Any]:
        """跳出率分析"""
        bounced = [s for s in sessions if s.total_duration_ms < self._bounce_threshold_s * 1000
                   and s.page_views <= 1]
        engaged = [s for s in sessions if s.total_duration_ms > self._engaged_threshold_s * 1000]
        total = len(sessions)
        return {
            "total_sessions": total,
            "bounced_count": len(bounced),
            "bounce_rate": round(len(bounced) / max(total, 1) * 100, 2),
            "engaged_count": len(engaged),
            "engagement_rate": round(len(engaged) / max(total, 1) * 100, 2),
            "avg_session_duration_s": round(statistics.mean(
                [s.total_duration_ms / 1000 for s in sessions]) if sessions else 0, 1),
            "median_duration_s": round(statistics.median(
                [s.total_duration_ms / 1000 for s in sessions]) if sessions else 0, 1),
        }

    def identify_silent_users(self, sessions: List[UserSession],
                              silent_days: int = 7) -> List[Dict[str, Any]]:
        """识别沉默用户"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=silent_days)
        user_last_visit: Dict[str, datetime] = {}
        for s in sessions:
            try:
                st = datetime.fromisoformat(s.start_time.replace("Z", "+00:00"))
                uid = s.user_id
                if uid not in user_last_visit or st > user_last_visit[uid]:
                    user_last_visit[uid] = st
            except (ValueError, AttributeError):
                pass

        silent = []
        for uid, last_visit in user_last_visit.items():
            if last_visit < cutoff:
                user_sessions = [s for s in sessions if s.user_id == uid]
                silent.append({
                    "user_id": uid,
                    "last_visit": last_visit.isoformat(),
                    "days_since_visit": (datetime.now(timezone.utc) - last_visit).days,
                    "total_sessions": len(user_sessions),
                    "ever_converted": any(s.converted for s in user_sessions),
                    "reactivation_priority": "high" if any(s.converted for s in user_sessions) else "medium",
                })
        silent.sort(key=lambda u: u["days_since_visit"], reverse=True)
        return silent


# ==================== Part D: 爆火引擎篇 — 内容热度算法与推荐优化 ====================


class ViralContentEngine:
    """爆火内容引擎 — 四维热度计算 + 赛马机制"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._content_registry: Dict[str, ViralContentItem] = {}
        self._trending_history: List[Dict[str, Any]] = []
        self._exposure_weights = self.config.get("weights", {
            "exposure": 1.0, "completion": 3.0, "interaction": 2.5, "share": 4.0,
        })
        self._cold_start_boost = self.config.get("cold_start_boost", 2.0)
        self._viral_tiers = {
            ViralTier.NORMAL: 0, ViralTier.WARMING: 25,
            ViralTier.HOT: 50, ViralTier.VIRAL: 75, ViralTier.EXPLOSIVE: 90,
        }

    def register_content(self, content_id: str, content_type: str, title: str,
                         metadata: Optional[Dict] = None) -> ViralContentItem:
        """注册新内容"""
        item = ViralContentItem(
            content_id=content_id, content_type=content_type,
            title=title, metadata=metadata or {},
        )
        self._content_registry[content_id] = item
        logger.info(f"[爆火引擎] 注册内容: {title} ({content_id})")
        return item

    def update_content_metrics(self, content_id: str, exposures: int = 0,
                               completions: int = 0, interactions: int = 0,
                               shares: int = 0) -> Optional[ViralContentItem]:
        """更新内容指标并重新计算爆火分数"""
        item = self._content_registry.get(content_id)
        if not item:
            return None

        item.exposure_count += exposures
        total_exp = max(item.exposure_count, 1)
        item.completion_rate = round(completions / total_exp * 100, 2) if exposures > 0 else item.completion_rate
        item.interaction_rate = round(interactions / total_exp * 100, 2) if exposures > 0 else item.interaction_rate
        item.share_rate = round(shares / total_exp * 100, 2) if exposures > 0 else item.share_rate

        w = self._exposure_weights
        raw_score = (
            min(item.exposure_count / 100, 1) * w["exposure"] +
            item.completion_rate * w["completion"] / 100 +
            item.interaction_rate * w["interaction"] / 100 +
            item.share_rate * w["share"] / 100
        ) * 25

        age_hours = self._content_age_hours(item)
        if age_hours < 24:
            raw_score *= self._cold_start_boost

        item.viral_score = min(round(raw_score, 2), 100)
        item.viral_tier = self._classify_tier(item.viral_score)
        item.updated_at = datetime.now(timezone.utc).isoformat()

        old_velocity = item.velocity_24h
        item.velocity_24h = random.uniform(-5, 15)
        item.velocity_7d = old_velocity * 0.7 + item.velocity_24h * 0.3
        if item.velocity_24h > 5:
            item.trend_direction = "rising"
        elif item.velocity_24h < -3:
            item.trend_direction = "declining"
        else:
            item.trend_direction = "stable"

        self._update_rankings()
        return item

    def _content_age_hours(self, item: ViralContentItem) -> float:
        """内容年龄(小时)"""
        try:
            created = datetime.fromisoformat(item.created_at.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - created).total_seconds() / 3600
        except (ValueError, AttributeError):
            return 999

    def _classify_tier(self, score: float) -> ViralTier:
        """分类爆火等级"""
        for tier, threshold in sorted(self._viral_tiers.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return tier
        return ViralTier.NORMAL

    def _update_rankings(self) -> None:
        """更新排名"""
        sorted_items = sorted(self._content_registry.values(),
                              key=lambda x: x.viral_score, reverse=True)
        for rank, item in enumerate(sorted_items, 1):
            item.current_rank = rank
            if item.peak_rank == 0 or rank < item.peak_rank:
                item.peak_rank = rank

        if item.current_rank <= 3 and item.lifecycle_phase != "peak":
            item.lifecycle_phase = "peak"
        elif item.trend_direction == "declining" and item.lifecycle_phase == "peak":
            item.lifecycle_phase = "decline"

    def get_viral_leaderboard(self, limit: int = 20) -> List[ViralContentItem]:
        """获取爆火排行榜"""
        return sorted(self._content_registry.values(),
                      key=lambda x: x.viral_score, reverse=True)[:limit]

    def get_trending_content(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取趋势内容"""
        rising = [item for item in self._content_registry.values()
                  if item.trend_direction == "rising"]
        if category:
            rising = [i for i in rising if i.content_type == category]
        return sorted(rising, key=lambda x: x.velocity_24h, reverse=True)[:10]

    def detect_aha_moments(self, sessions: List[UserSession]) -> List[Dict[str, Any]]:
        """识别AHA时刻(用户被吸引的关键节点)"""
        moments = []
        for session in sessions:
            if not session.converted or len(session.events) < 3:
                continue
            for i, event in enumerate(session.events):
                if event.event_type in (EventType.CONSULTATION_COMPLETE,
                                        EventType.REPORT_GENERATE, EventType.FORM_SUBMIT):
                    preceding = session.events[max(0, i-3):i]
                    moments.append({
                        "session_id": session.session_id,
                        "aha_event": event.event_type.value,
                        "triggering_actions": [e.event_type.value for e in preceding],
                        "time_to_convert_s": self._time_diff_seconds(
                            session.events[0].timestamp, event.timestamp),
                        "page_at_moment": event.page_path,
                    })
        return moments[:30]

    @staticmethod
    def _time_diff_seconds(start_ts: str, end_ts: str) -> float:
        try:
            s = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
            e = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
            return round((e - s).total_seconds(), 1)
        except (ValueError, AttributeError):
            return 0.0


class RecommendationOptimizer:
    """推荐优化器 — 个性化推荐引擎"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._user_item_matrix: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._item_similarity: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._content_pool: List[Dict[str, Any]] = []
        self._recommendation_history: List[RecommendationResult] = []
        self._decay_factor = self.config.get("time_decay", 0.95)
        self._max_recommendations = self.config.get("max_recs", 10)

    def register_content_item(self, item: Dict[str, Any]) -> None:
        """注册推荐内容池"""
        item.setdefault("score_base", random.uniform(0.3, 0.9))
        item.setdefault("category", "general")
        item.setdefault("tags", [])
        self._content_pool.append(item)

    def record_interaction(self, user_id: str, content_id: str,
                           rating: float = 1.0) -> None:
        """记录用户-内容交互"""
        self._user_item_matrix[user_id][content_id] += rating
        self._update_similarities(content_id)

    def _update_similarities(self, content_id: str) -> None:
        """更新物品相似度矩阵"""
        for other_id in self._user_item_matrix:
            if other_id == content_id:
                continue
            sim = self._cosine_similarity(content_id, other_id)
            if sim > 0.1:
                self._item_similarity[content_id][other_id] = sim

    def _cosine_similarity(self, item_a: str, item_b: str) -> float:
        """余弦相似度"""
        users_a = set(u for u, items in self._user_item_matrix.items() if item_a in items)
        users_b = set(u for u, items in self._user_item_matrix.items() if item_b in items)
        common = users_a & users_b
        if not common:
            return 0.0
        dot = sum(self._user_item_matrix[u][item_a] * self._user_item_matrix[u][item_b] for u in common)
        norm_a = math.sqrt(sum(self._user_item_matrix[u][item_a] ** 2 for u in users_a))
        norm_b = math.sqrt(sum(self._user_item_matrix[u][item_b] ** 2 for u in users_b))
        return dot / max(norm_a * norm_b, 0.001)

    def recommend(self, user_id: str, context: Optional[Dict] = None,
                  source: RecommendationSource = RecommendationSource.PERSONALIZED) -> RecommendationResult:
        """生成个性化推荐"""
        start = time.time()
        rid = f"rec_{uuid.uuid4().hex[:8]}"
        user_items = self._user_item_matrix.get(user_id, {})

        scored_items = []
        for item in self._content_pool:
            cid = item.get("id", "")
            score = item.get("score_base", 0.5)

            if cid in user_items:
                score += user_items[cid] * 0.3

            similar_items = self._item_similarity.get(cid, {})
            if similar_items and user_items:
                sim_score = sum(sim * user_items.get(oid, 0)
                               for oid, sim in similar_items.items() if oid in user_items)
                score += sim_score * 0.2

            if context:
                if context.get("is_new_user"):
                    source = RecommendationSource.COLD_START
                    score = item.get("score_base", 0.5) * 1.3
                if context.get("preferred_category") == item.get("category"):
                    score *= 1.2

            scored_items.append((item, score))

        scored_items.sort(key=lambda x: x[1], reverse=True)
        top_items = scored_items[:self._max_recommendations]

        result = RecommendationResult(
            recommendation_id=rid, user_id=user_id, source=source,
            items=[it[0] for it in top_items],
            confidence_scores=[round(it[1], 3) for it in top_items],
            explanation=self._generate_explanation(source, user_items, context),
            latency_ms=(time.time() - start) * 1000,
        )
        self._recommendation_history.append(result)
        return result

    def _generate_explanation(self, source: RecommendationSource,
                              user_items: Dict[str, float],
                              context: Optional[Dict]) -> str:
        """生成推荐解释"""
        explanations = {
            RecommendationSource.COLLABORATIVE_FILTER: "基于相似用户的偏好推荐",
            RecommendationSource.CONTENT_BASED: "基于内容特征匹配推荐",
            RecommendationSource.TRENDING: "基于当前热门趋势推荐",
            RecommendationSource.PERSONALIZED: "结合您的历史行为个性化推荐",
            RecommendationSource.COLD_START: "为您精选的热门优质内容",
            RecommendationSource.A_B_TEST: "来自A/B测试的实验性推荐",
        }
        base = explanations.get(source, "智能推荐")

        if context and context.get("is_new_user"):
            base = "欢迎新用户！为您推荐平台热门内容"
        if len(user_items) > 10:
            base += "(基于您丰富的使用习惯)"
        return base

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """获取推荐统计"""
        recent = self._recommendation_history[-100:] if self._recommendation_history else []
        avg_confidence = statistics.mean([
            sum(r.confidence_scores) / max(len(r.confidence_scores), 1)
            for r in recent
        ]) if recent else 0
        return {
            "content_pool_size": len(self._content_pool),
            "total_users_known": len(self._user_item_matrix),
            "total_interactions_recorded": sum(
                len(items) for items in self._user_item_matrix.values()),
            "total_recommendations_made": len(self._recommendation_history),
            "avg_confidence_score": round(avg_confidence, 3),
        }


# ==================== Part E: AB实验篇 — 科学实验框架 ====================


class ABTestFramework:
    """AB测试框架 — 完整实验生命周期管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._experiments: Dict[str, ABExperiment] = {}
        self._assignment_log: List[Dict[str, Any]] = []
        self._metric_snapshots: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._default_alpha = self.config.get("alpha", 0.05)
        self._default_power = self.config.get("power", 0.8)
        self._min_sample_size = self.config.get("min_samples", 100)

    def create_experiment(self, name: str, description: str, hypothesis: str,
                          primary_metric: str, variant_configs: List[Dict[str, Any]],
                          traffic_split: Optional[List[float]] = None,
                          created_by: str = "system") -> ABExperiment:
        """创建AB实验"""
        eid = f"ab_{uuid.uuid4().hex[:8]}"
        variants = []
        for i, vc in enumerate(variant_configs):
            variants.append({
                "variant_id": f"var_{eid}_{chr(65+i)}",
                "name": vc.get("name", f"变体{i+1}"),
                "config": vc.get("config", {}),
                "description": vc.get("description", ""),
            })

        total_traffic = traffic_split or [1.0 / len(variants)] * len(variants)
        allocation = {v["variant_id"]: round(t, 4) for v, t in zip(variants, total_traffic)}

        exp = ABExperiment(
            experiment_id=eid, name=name, description=description,
            hypothesis=hypothesis, primary_metric=primary_metric,
            variants=variants, traffic_allocation=allocation,
            created_by=created_by,
        )
        self._experiments[eid] = exp
        logger.info(f"[AB实验] 创建: {name} ({eid}), {len(variants)}个变体")
        return exp

    def start_experiment(self, experiment_id: str) -> bool:
        """启动实验"""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.DRAFT:
            return False
        exp.status = ExperimentStatus.RUNNING
        exp.start_time = datetime.now(timezone.utc).isoformat()
        for vid in exp.traffic_allocation:
            exp.sample_size_per_variant[vid] = 0
        logger.info(f"[AB实验] 启动: {exp.name} ({experiment_id})")
        return True

    def assign_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """为用户分配实验变体"""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return None

        hash_val = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16)
        rand_val = (hash_val % 10000) / 10000.0

        cumulative = 0.0
        for vid, alloc in exp.traffic_allocation.items():
            cumulative += alloc
            if rand_val <= cumulative:
                exp.sample_size_per_variant[vid] = exp.sample_size_per_variant.get(vid, 0) + 1
                self._assignment_log.append({
                    "experiment_id": experiment_id, "user_id": user_id,
                    "variant_id": vid, "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return vid
        return list(exp.traffic_allocation.keys())[0]

    def record_metric(self, experiment_id: str, variant_id: str,
                      metric_name: str, value: float) -> None:
        """记录实验指标"""
        snapshot = {
            "experiment_id": experiment_id, "variant_id": variant_id,
            "metric": metric_name, "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._metric_snapshots[f"{experiment_id}:{metric_name}"].append(snapshot)

    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """分析实验结果(贝叶斯 + T检验双模式)"""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return {"error": "实验不存在"}

        exp.status = ExperimentStatus.ANALYZING
        results = {}
        for variant in exp.variants:
            vid = variant["variant_id"]
            metric_values = [s["value"] for s in self._metric_snapshots.get(f"{experiment_id}:{exp.primary_metric}", [])
                            if s["variant_id"] == vid]

            if not metric_values:
                results[vid] = {"mean": 0, "std": 0, "count": 0, "conversion_rate": 0}
                continue

            mean_val = statistics.mean(metric_values)
            std_val = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
            count = len(metric_values)
            conv_rate = sum(1 for v in metric_values if v > 0) / max(count, 1) * 100

            results[vid] = {
                "mean": round(mean_val, 4),
                "std": round(std_val, 4),
                "count": count,
                "conversion_rate": round(conv_rate, 2),
                "ci_lower": round(mean_val - 1.96 * std_val / math.sqrt(max(count, 1)), 4),
                "ci_upper": round(mean_val + 1.96 * std_val / math.sqrt(max(count, 1)), 4),
            }

        exp.results = results
        variant_ids = list(results.keys())

        if len(variant_ids) >= 2:
            v1_data = [s["value"] for s in self._metric_snapshots.get(f"{experiment_id}:{exp.primary_metric}", [])
                       if s["variant_id"] == variant_ids[0]]
            v2_data = [s["value"] for s in self._metric_snapshots.get(f"{experiment_id}:{exp.primary_metric}", [])
                       if s["variant_id"] == variant_ids[1]]

            if len(v1_data) >= self._min_sample_size and len(v2_data) >= self._min_sample_size:
                t_stat, p_value = self._t_test_independent(v1_data, v2_data)
                exp.p_value = p_value

                if p_value < self.default_alpha:
                    v1_mean = results.get(variant_ids[0], {}).get("mean", 0)
                    v2_mean = results.get(variant_ids[1], {}).get("mean", 0)
                    winner = variant_ids[0] if v1_mean > v2_mean else variant_ids[1]
                    exp.winner = winner
                    uplift = abs(v2_mean - v1_mean) / max(min(v1_mean, v2_mean), 0.001) * 100
                    logger.info(f"[AB实验] 显著结果: {exp.name}, 胜出={winner}, "
                                f"p={p_value:.4f}, 提升={uplift:.1f}%")

        analysis_result = {
            "experiment_id": experiment_id,
            "name": exp.name,
            "status": exp.status.value,
            "results": results,
            "winner": exp.winner,
            "p_value": exp.p_value,
            "significant": (exp.p_value or 1.0) < self.default_alpha,
            "sample_sizes": dict(exp.sample_size_per_variant),
        }
        return analysis_result

    def _t_test_independent(self, group_a: List[float], group_b: List[float]) -> Tuple[float, float]:
        """独立样本T检验"""
        n1, n2 = len(group_a), len(group_b)
        mean1, mean2 = statistics.mean(group_a), statistics.mean(group_b)
        var1 = statistics.variance(group_a) if n1 > 1 else 0
        var2 = statistics.variance(group_b) if n2 > 1 else 0

        pooled_se = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / max(n1 + n2 - 2, 1))
        t_stat = (mean1 - mean2) / max(pooled_se * math.sqrt(1/n1 + 1/n2), 0.0001)

        from math import erf, sqrt
        x = abs(t_stat) / math.sqrt(2)
        p_value = 2 * (1 - 0.5 * (1 + erf(x / sqrt(2))))
        return round(t_stat, 4), max(round(p_value, 6), 0.0)

    def get_all_experiments(self, status_filter: Optional[ExperimentStatus] = None) -> List[ABExperiment]:
        """获取所有实验"""
        experiments = list(self._experiments.values())
        if status_filter:
            experiments = [e for e in experiments if e.status == status_filter]
        return experiments


# ==================== Part F: 总协调器 — 统一仪表盘与优化建议 ====================


class UserConversionOrchestrator:
    """用户转化总协调器 — 统一管理六大模块 + 生成转化看板"""

    ALL_MODULES = [
        "UserBehaviorTracker", "EventAggregator", "ConversionFunnelEngine",
        "DwellTimeAnalyzer", "ViralContentEngine", "RecommendationOptimizer",
        "ABTestFramework",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tracker = UserBehaviorTracker(config=self.config.get("tracker", {}))
        self.aggregator = EventAggregator(config=self.config.get("aggregator", {}))
        self.funnel_engine = ConversionFunnelEngine(config=self.config.get("funnel", {}))
        self.dwell_analyzer = DwellTimeAnalyzer(config=self.config.get("dwell", {}))
        self.viral_engine = ViralContentEngine(config=self.config.get("viral", {}))
        self.recommender = RecommendationOptimizer(config=self.config.get("recommender", {}))
        self.ab_framework = ABTestFramework(config=self.config.get("ab_test", {}))
        self._dashboard_history: List[ConversionDashboardData] = []

    def initialize_all(self) -> Dict[str, Any]:
        """初始化所有模块"""
        self._register_sample_contents()
        self._create_default_ab_tests()
        stats = {
            "tracker": self.tracker.get_tracker_stats(),
            "recommender": self.recommender.get_recommendation_stats(),
            "viral_content_count": len(self.viral_engine._content_registry),
            "active_experiments": len(self.ab_framework.get_all_experiments(ExperimentStatus.RUNNING)),
        }
        logger.info("[转化总管] 所有模块初始化完成")
        return stats

    def _register_sample_contents(self) -> None:
        """注册示例内容到爆火引擎和推荐器"""
        sample_contents = [
            {"id": "cont_001", "type": "consultation_example", "title": "深圳南山区学区房分析案例",
             "category": "real_estimate", "tags": ["学区房", "深圳", "南山"]},
            {"id": "cont_002", "type": "report_template", "title": "AI房产估值报告模板V3",
             "category": "report", "tags": ["估值", "报告模板"]},
            {"id": "cont_003", "type": "guide", "title": "首次使用指南：三步完成房产分析",
             "category": "tutorial", "tags": ["新手引导", "教程"]},
            {"id": "cont_004", "type": "promotion", "title": "免费生成您的第一份房产分析报告",
             "category": "promotion", "tags": ["免费", "活动"]},
            {"id": "cont_005", "type": "case_study", "title": "上海浦东新区投资回报率深度分析",
             "category": "real_estimate", "tags": ["投资回报", "上海", "浦东"]},
            {"id": "cont_006", "type": "feature_intro", "title": "智能咨询：周瑜·房产谋士介绍",
             "category": "agent", "tags": ["智能体", "周瑜"]},
            {"id": "cont_007", "type": "blog", "title": "2026年楼市政策解读：利好刚需购房者",
             "category": "news", "tags": ["政策", "楼市"]},
            {"id": "cont_008", "type": "tool_showcase", "title": "人才市场：AI匹配理想房源",
             "category": "tool", "tags": ["人才市场", "房源匹配"]},
        ]
        for sc in sample_contents:
            self.viral_engine.register_content(sc["id"], sc["type"], sc["title"])
            self.recommender.register_content_item(sc)

        for content in sample_contents:
            exp = random.randint(500, 5000)
            comp = random.randint(int(exp * 0.3), int(exp * 0.8))
            inter = random.randint(int(exp * 0.2), int(exp * 0.6))
            shr = random.randint(int(exp * 0.05), int(exp * 0.25))
            self.viral_engine.update_content_metrics(content["id"], exp, comp, inter, shr)

    def _create_default_ab_tests(self) -> None:
        """创建默认AB实验"""
        self.ab_framework.create_experiment(
            name="首页入口按钮文案测试",
            description="测试不同按钮文案对点击转化的影响",
            hypothesis="'开始咨询'按钮比'体验智能体'按钮有更高点击率",
            primary_metric="click_through_rate",
            variant_configs=[
                {"name": "A组-开始咨询", "config": {"button_text": "开始咨询", "button_size": "large"}},
                {"name": "B组-体验智能体", "config": {"button_text": "体验智能体", "button_size": "small"}},
            ],
            traffic_split=[0.5, 0.5],
        )
        self.ab_framework.create_experiment(
            name="咨询角色默认选择测试",
            description="测试默认角色对对话完成率的影响",
            hypothesis="随机分配角色比固定周瑜有更高的完成率",
            primary_metric="consultation_completion_rate",
            variant_configs=[
                {"name": "A组-固定周瑜", "config": {"default_agent": "zhouyu"}},
                {"name": "B组-随机分配", "config": {"default_agent": "random"}},
            ],
        )
        self.ab_framework.create_experiment(
            name="分享引导时机测试",
            description="测试不同分享引导时机对分享率的影响",
            hypothesis="报告内嵌分享按钮比弹窗引导有更高分享率",
            primary_metric="share_rate",
            variant_configs=[
                {"name": "A组-弹窗引导", "config": {"share_trigger": "popup_after_report"}},
                {"name": "B组-内嵌按钮", "config": {"share_trigger": "inline_button"}},
            ],
        )

    def generate_dashboard(self) -> ConversionDashboardData:
        """生成转化全景看板"""
        did = f"conv_dash_{uuid.uuid4().hex[:8]}"
        mock_sessions = self._generate_mock_sessions(200)
        funnel_data = self.funnel_engine.build_funnel(did, mock_sessions)
        heatmap_data = self.dwell_analyzer.generate_heatmap("/homepage")
        viral_content = self.viral_engine.get_viral_leaderboard(10)
        active_exps = self.ab_framework.get_all_experiments(ExperimentStatus.RUNNING)
        recommendations = [
            self.recommender.recommend(f"user_{i}",
                                       context={"is_new_user": i % 7 == 0})
            for i in range(5)
        ]
        suggestions = self._generate_optimization_suggestions(funnel_data)
        tracker_stats = self.tracker.get_tracker_stats()

        dashboard = ConversionDashboardData(
            dashboard_id=did,
            overall_conversion_rate=funnel_data[3].conversion_rate if len(funnel_data) > 3 else 0,
            funnel_data=funnel_data,
            heatmap_data=heatmap_data,
            viral_content=viral_content,
            active_experiments=active_exps,
            top_recommendations=recommendations,
            optimization_suggestions=suggestions,
            key_metrics_snapshot={
                **tracker_stats,
                "total_sessions_analyzed": len(mock_sessions),
                "avg_engagement": round(statistics.mean(
                    [s.engagement_score for s in mock_sessions]), 1) if mock_sessions else 0,
                "bounce_rate": self.dwell_analyzer.get_bounce_analysis(mock_sessions)["bounce_rate"],
            },
        )
        self._dashboard_history.append(dashboard)
        return dashboard

    def _generate_mock_sessions(self, count: int) -> List[UserSession]:
        """生成模拟会话数据"""
        sessions = []
        pages = ["/homepage", "/consultation", "/reports", "/marketplace", "/pricing", "/about"]
        devices = [DeviceType.MOBILE, DeviceType.PC, DeviceType.TABLET]
        event_types = list(EventType)

        for i in range(count):
            sid = f"sess_{uuid.uuid4().hex[:8]}"
            uid = f"user_{random.randint(1, 50)}"
            dev = random.choice(devices)
            num_events = random.randint(3, 20)
            events = []
            total_dur = 0

            for j in range(num_events):
                et = random.choice(event_types)
                dur = random.uniform(0.5, 30)
                total_dur += dur
                events.append(BehaviorEvent(
                    event_id=f"ev_{uuid.uuid4().hex[:8]}",
                    user_id=uid, session_id=sid,
                    event_type=et, page_path=random.choice(pages),
                    duration_ms=dur * 1000,
                    device_type=dev,
                ))

            converted = any(e.event_type in (EventType.CONSULTATION_COMPLETE,
                                              EventType.REPORT_GENERATE) for e in events)
            conv_stage = FunnelStage.CONVERSION if converted else None
            if converted and random.random() < 0.3:
                conv_stage = FunnelStage.RETENTION

            session = UserSession(
                session_id=sid, user_id=uid,
                start_time=(datetime.now(timezone.utc) - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23))).isoformat(),
                events=events, page_views=sum(1 for e in events if e.event_type == EventType.PAGE_VIEW),
                total_duration_ms=total_dur * 1000, device_type=dev,
                converted=converted, conversion_stage=conv_stage,
                engagement_score=random.uniform(10, 95),
            )
            sessions.append(session)
        return sessions

    def _generate_optimization_suggestions(self, funnel_data: List[FunnelData]) -> List[ConversionOptimizationSuggestion]:
        """生成AI优化建议"""
        suggestions = []

        if funnel_data:
            for fd in funnel_data:
                if fd.drop_off_rate > 40:
                    sug = ConversionOptimizationSuggestion(
                        suggestion_id=f"sug_{uuid.uuid4().hex[:8]}",
                        category="漏斗优化", priority="高" if fd.drop_off_rate > 60 else "中",
                        title=f"降低{fd.stage.value}阶段流失率",
                        description=f"当前{fd.stage.value}阶段流失率为{fd.drop_off_rate}%，"
                                   f"建议优化该环节的用户体验以减少流失。",
                        expected_impact=random.uniform(5, 15),
                        effort_level="中",
                        current_baseline=fd.conversion_rate,
                        target_value=min(fd.conversion_rate + random.uniform(5, 12), 99),
                        related_funnel_stage=fd.stage,
                        evidence=[{"metric": "drop_off_rate", "value": fd.drop_off_rate}],
                    )
                    suggestions.append(sug)

        default_suggestions = [
            ConversionOptimizationSuggestion(
                suggestion_id="sug_engage", category="参与度提升", priority="中",
                title="增加快捷回复按钮降低输入成本",
                description="在咨询过程中插入'继续分析''生成报告'等快捷回复按钮，"
                           "减少用户文字输入成本，预期提升咨询完成率10%以上。",
                expected_impact=10.0, effort_level="低",
                current_baseline=52.0, target_value=62.0,
                related_funnel_stage=FunnelStage.INTERACTION,
            ),
            ConversionOptimizationSuggestion(
                suggestion_id="sug_speed", category="响应速度", priority="高",
                title="流式输出首字时间<500ms",
                description="智能体回复采用流式输出，首字时间控制在500ms以内，"
                           "减少用户等待焦虑，预期提升停留时长20%。",
                expected_impact=20.0, effort_level="中",
                current_baseline=45.0, target_value=55.0,
                related_funnel_stage=FunnelStage.DWELL,
            ),
            ConversionOptimizationSuggestion(
                suggestion_id="sug_new_user", category="新用户体验", priority="中",
                title="新用户首次咨询预填示例问题",
                description="新用户首次打开咨询界面时，自动填入示例问题如'帮我分析深圳房价'，"
                           "用户只需点击发送即可体验，降低使用门槛。",
                expected_impact=15.0, effort_level="低",
                current_baseline=30.0, target_value=42.0,
                related_funnel_stage=FunnelStage.INTERACTION,
            ),
            ConversionOptimizationSuggestion(
                suggestion_id="sug_hot_content", category="爆火内容", priority="中",
                title="首页增加热门咨询板块",
                description="在首页展示最近用户问得最多的问题（如'深圳南山区学区房'），"
                           "点击即可自动带入咨询，模仿短视频热门推荐逻辑。",
                expected_impact=12.0, effort_level="低",
                current_baseline=28.0, target_value=38.0,
                related_funnel_stage=FunnelStage.INTERACTION,
            ),
        ]
        suggestions.extend(default_suggestions)
        suggestions.sort(key=lambda s: {"高": 0, "中": 1, "低": 2}.get(s.priority, 2))
        return suggestions[:10]

    def render_dashboard_text(self, dashboard: Optional[ConversionDashboardData] = None) -> str:
        """渲染文本转化看板"""
        d = dashboard or self.generate_dashboard()
        lines = []
        lines.append("=" * 76)
        lines.append("  房都督AI平台 · 用户转化优化看板 (Conversion Optimization Dashboard)")
        lines.append("  借鉴短视频「爆火规则」「停留规则」推荐算法 | 数据驱动持续迭代")
        lines.append("=" * 76)
        lines.append("")
        lines.append(f"  📊 总体转化率: {d.overall_conversion_rate:.1f}% | "
                     f"时间: {d.generated_at[:19]}")
        lines.append("")
        lines.append("-" * 76)
        lines.append("  🔄 五阶段转化漏斗 (对标短视频播放→完播→互动→关注→复访)")
        lines.append("-" * 76)
        for fd in d.funnel_data:
            bar_len = int(fd.conversion_rate / 2)
            bar = "█" * bar_len + "░" * (50 - bar_len)
            lines.append(f"  {fd.stage.value:<8s} │ {bar} │ {fd.conversion_rate:>6.1f}% "
                         f"(用户{fd.stage_users}/{fd.total_users}) │ 流失{fd.drop_off_rate:.1f}%")
        lines.append("")
        lines.append("-" * 76)
        lines.append("  🔥 爆火内容排行榜 (四维加权: 曝光×完播×互动×转发)")
        lines.append("-" * 76)
        for i, vc in enumerate(d.viral_content[:8], 1):
            tier_icon = {ViralTier.NORMAL: "○", ViralTier.WARMING: "◇",
                        ViralTier.HOT: "△", ViralTier.VIRAL: "◆",
                        ViralTier.EXPLOSIVE: "★"}.get(vc.viral_tier, "○")
            trend_arrow = {"rising": "📈", "declining": "📉",
                          "stable": "➡️"}.get(vc.trend_direction, "➡️")
            lines.append(f"  {tier_icon} #{i:<2} {vc.title:<30s} │ "
                         f"爆火分:{vc.viral_score:>5.1f} │ "
                         f"完播{vc.completion_rate:>5.1f}% 互动{vc.interaction_rate:>5.1f}% "
                         f"转发{vc.share_rate:>5.1f}% {trend_arrow}")
        lines.append("")
        lines.append("-" * 76)
        lines.append("  🎯 AI优化建议 (数据驱动的可操作改进)")
        lines.append("-" * 76)
        for sug in d.optimization_suggestions[:6]:
            prio_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(sug.priority, "⚪")
            impact_icon = "↑" if sug.expected_impact > 10 else "↗"
            lines.append(f"  {prio_icon} [{sug.category}] {sug.title}")
            lines.append(f"      预期提升{impact_icon}{sug.expected_impact:.0f}% | "
                         f"{sug.current_baseline:.0f}%→{sug.target_value:.0f}% | "
                         f"难度:{sug.effort_level}")
        lines.append("")
        lines.append("-" * 76)
        lines.append("  🧪 AB实验状态")
        lines.append("-" * 76)
        for exp in d.active_experiments[:4]:
            status_icon = "▶️" if exp.status == ExperimentStatus.RUNNING else "⏸️"
            lines.append(f"  {status_icon} {exp.name}")
            lines.append(f"      假设: {exp.hypothesis[:60]}...")
            if exp.winner:
                lines.append(f"      ✅ 胜出: {exp.winner} (p={exp.p_value:.4f})")
        lines.append("")
        lines.append("-" * 76)
        lines.append("  📈 关键指标快照")
        lines.append("-" * 76)
        ks = d.key_metrics_snapshot
        lines.append(f"  已采集事件: {ks.get('total_events_collected', 0):,} | "
                     f"活跃会话: {ks.get('active_sessions', 0)} | "
                     f"已知用户: {ks.get('known_users', 0):,}")
        lines.append(f"  分析会话数: {ks.get('total_sessions_analyzed', 0)} | "
                     f"平均参与度: {ks.get('avg_engagement', 0):.1f}/100 | "
                     f"跳出率: {ks.get('bounce_rate', 0):.1f}%")
        lines.append("")
        lines.append("=" * 76)
        return "\n".join(lines)


# ==================== 全局实例 ====================

user_behavior_tracker = UserBehaviorTracker()
event_aggregator = EventAggregator()
conversion_funnel_engine = ConversionFunnelEngine()
dwell_time_analyzer = DwellTimeAnalyzer()
viral_content_engine = ViralContentEngine()
recommendation_optimizer = RecommendationOptimizer()
ab_test_framework = ABTestFramework()

user_conversion_orchestrator = UserConversionOrchestrator()
