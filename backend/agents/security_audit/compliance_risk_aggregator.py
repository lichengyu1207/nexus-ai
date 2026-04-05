"""
合规风险聚合智能体
Compliance Risk Aggregator Agent

负责汇总各审计智能体发现的风险事件，进行关联分析和优先级排序。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    DATA_PRIVACY = "data_privacy"
    DATA_SECURITY = "data_security"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"


class RiskSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RiskEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    source_agent: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    
    severity: str = RiskSeverity.MEDIUM.value
    impact_score: float = 0.0
    probability_score: float = 0.0
    composite_score: float = 0.0
    
    affected_users: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    affected_data_types: List[str] = field(default_factory=list)
    
    root_cause: str = ""
    evidence: Dict = field(default_factory=dict)
    
    status: str = "open"
    assigned_to: str = ""
    due_date: str = ""
    
    related_events: List[str] = field(default_factory=list)
    correlation_group: str = ""


@dataclass
class RiskCorrelation:
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: List[str] = field(default_factory=list)
    correlation_type: str = ""
    pattern_description: str = ""
    aggregate_severity: str = RiskSeverity.MEDIUM.value
    affected_entity: str = ""
    first_occurrence: str = ""
    last_occurrence: str = ""


class ComplianceRiskAggregatorAgent:
    """
    合规风险聚合智能体
    
    功能：
    1. 数据来源：各审计智能体的告警和异常报告、用户投诉、监管问询
    2. 风险评分：根据风险等级、影响范围、发生概率计算综合风险分
    3. 关联分析：识别同一用户/同一业务涉及的多个风险事件
    4. 风险趋势：统计各类风险随时间的变化趋势
    5. 报告生成：生成合规风险月报，高风险事件即时推送
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ComplianceRiskAggregatorAgent"
        self.description = "汇总各审计智能体发现的风险事件，进行关联分析和优先级排序"
        self.config = config or {}
        
        self.risk_events: Dict[str, RiskEvent] = {}
        self.correlations: Dict[str, RiskCorrelation] = {}
        
        self.severity_weights = {
            RiskSeverity.CRITICAL.value: 10,
            RiskSeverity.HIGH.value: 7,
            RiskSeverity.MEDIUM.value: 4,
            RiskSeverity.LOW.value: 1,
        }
        
        self.category_weights = {
            RiskCategory.DATA_PRIVACY.value: 1.5,
            RiskCategory.DATA_SECURITY.value: 1.3,
            RiskCategory.REGULATORY.value: 1.4,
            RiskCategory.OPERATIONAL.value: 1.0,
            RiskCategory.REPUTATIONAL.value: 1.2,
        }
        
        self.stats = {
            "total_events": 0,
            "events_by_category": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "events_by_source": defaultdict(int),
            "open_events": 0,
            "resolved_events": 0,
            "correlations_found": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_correlation())
    
    async def _periodic_correlation(self):
        while True:
            await asyncio.sleep(3600)
            await self._perform_correlation_analysis()
    
    async def ingest_risk_event(
        self,
        source_agent: str,
        category: str,
        title: str,
        description: str,
        severity: str = RiskSeverity.MEDIUM.value,
        impact_score: float = 0.5,
        probability_score: float = 0.5,
        affected_users: Optional[List[str]] = None,
        affected_systems: Optional[List[str]] = None,
        affected_data_types: Optional[List[str]] = None,
        evidence: Optional[Dict] = None,
    ) -> RiskEvent:
        event = RiskEvent(
            source_agent=source_agent,
            category=category,
            title=title,
            description=description,
            severity=severity,
            impact_score=impact_score,
            probability_score=probability_score,
            affected_users=affected_users or [],
            affected_systems=affected_systems or [],
            affected_data_types=affected_data_types or [],
            evidence=evidence or {},
        )
        
        event.composite_score = self._calculate_composite_score(event)
        
        self.risk_events[event.event_id] = event
        
        self.stats["total_events"] += 1
        self.stats["events_by_category"][category] += 1
        self.stats["events_by_severity"][severity] += 1
        self.stats["events_by_source"][source_agent] += 1
        self.stats["open_events"] += 1
        
        if event.severity in [RiskSeverity.CRITICAL.value, RiskSeverity.HIGH.value]:
            await self._send_immediate_notification(event)
        
        return event
    
    def _calculate_composite_score(self, event: RiskEvent) -> float:
        severity_score = self.severity_weights.get(event.severity, 1)
        category_multiplier = self.category_weights.get(event.category, 1.0)
        
        impact = event.impact_score
        probability = event.probability_score
        
        composite = (severity_score * category_multiplier * impact * probability) / 10
        
        return min(10.0, composite)
    
    async def _send_immediate_notification(self, event: RiskEvent):
        logger.warning(f"High severity risk event: {event.title}")
    
    async def _perform_correlation_analysis(self):
        now = datetime.utcnow()
        cutoff = (now - timedelta(hours=24)).isoformat()
        
        recent_events = [
            e for e in self.risk_events.values()
            if e.timestamp > cutoff and not e.correlation_group
        ]
        
        user_groups = defaultdict(list)
        for event in recent_events:
            for user in event.affected_users:
                user_groups[user].append(event)
        
        for user, events in user_groups.items():
            if len(events) >= 2:
                await self._create_correlation(events, "same_user", user)
        
        system_groups = defaultdict(list)
        for event in recent_events:
            for system in event.affected_systems:
                system_groups[system].append(event)
        
        for system, events in system_groups.items():
            if len(events) >= 3:
                await self._create_correlation(events, "same_system", system)
        
        category_groups = defaultdict(list)
        for event in recent_events:
            category_groups[event.category].append(event)
        
        for category, events in category_groups.items():
            if len(events) >= 5:
                await self._create_correlation(events, "systemic_risk", category)
    
    async def _create_correlation(
        self,
        events: List[RiskEvent],
        correlation_type: str,
        entity: str,
    ):
        correlation = RiskCorrelation(
            events=[e.event_id for e in events],
            correlation_type=correlation_type,
            pattern_description=f"{entity}相关的{len(events)}个风险事件",
            affected_entity=entity,
            first_occurrence=min(e.timestamp for e in events),
            last_occurrence=max(e.timestamp for e in events),
        )
        
        max_severity = max(
            events,
            key=lambda e: self.severity_weights.get(e.severity, 0)
        )
        correlation.aggregate_severity = max_severity.severity
        
        for event in events:
            event.correlation_group = correlation.correlation_id
        
        self.correlations[correlation.correlation_id] = correlation
        self.stats["correlations_found"] += 1
    
    async def get_prioritized_risks(
        self,
        limit: int = 20,
        category: Optional[str] = None,
        min_severity: Optional[str] = None,
    ) -> List[Dict]:
        events = list(self.risk_events.values())
        
        if category:
            events = [e for e in events if e.category == category]
        
        if min_severity:
            severity_order = [
                RiskSeverity.CRITICAL.value,
                RiskSeverity.HIGH.value,
                RiskSeverity.MEDIUM.value,
                RiskSeverity.LOW.value,
            ]
            min_index = severity_order.index(min_severity)
            events = [
                e for e in events
                if severity_order.index(e.severity) <= min_index
            ]
        
        events.sort(key=lambda e: e.composite_score, reverse=True)
        
        return [
            {
                "event_id": e.event_id,
                "title": e.title,
                "category": e.category,
                "severity": e.severity,
                "composite_score": e.composite_score,
                "status": e.status,
                "source_agent": e.source_agent,
                "timestamp": e.timestamp,
                "affected_users_count": len(e.affected_users),
            }
            for e in events[:limit]
        ]
    
    async def get_risk_trends(
        self,
        days: int = 30,
    ) -> Dict:
        now = datetime.utcnow()
        start = (now - timedelta(days=days)).isoformat()
        
        events = [
            e for e in self.risk_events.values()
            if e.timestamp >= start
        ]
        
        daily_counts = defaultdict(lambda: defaultdict(int))
        for event in events:
            date = event.timestamp[:10]
            daily_counts[date][event.category] += 1
        
        trends = {
            "period": {"start": start, "end": now.isoformat()},
            "total_events": len(events),
            "daily_breakdown": {},
            "category_trends": defaultdict(list),
        }
        
        for date in sorted(daily_counts.keys()):
            trends["daily_breakdown"][date] = dict(daily_counts[date])
            
            for category in RiskCategory:
                count = daily_counts[date].get(category.value, 0)
                trends["category_trends"][category.value].append({
                    "date": date,
                    "count": count,
                })
        
        trends["category_trends"] = dict(trends["category_trends"])
        
        return trends
    
    async def resolve_risk_event(
        self,
        event_id: str,
        resolution: str,
        resolved_by: str,
    ) -> bool:
        event = self.risk_events.get(event_id)
        if not event:
            return False
        
        event.status = "resolved"
        event.root_cause = resolution
        
        self.stats["open_events"] -= 1
        self.stats["resolved_events"] += 1
        
        return True
    
    async def get_correlations(self) -> List[Dict]:
        return [
            {
                "correlation_id": c.correlation_id,
                "correlation_type": c.correlation_type,
                "pattern_description": c.pattern_description,
                "event_count": len(c.events),
                "aggregate_severity": c.aggregate_severity,
                "affected_entity": c.affected_entity,
                "first_occurrence": c.first_occurrence,
                "last_occurrence": c.last_occurrence,
            }
            for c in self.correlations.values()
        ]
    
    async def generate_risk_report(
        self,
        time_range: Optional[tuple] = None,
    ) -> Dict:
        if time_range:
            events = [
                e for e in self.risk_events.values()
                if time_range[0] <= e.timestamp <= time_range[1]
            ]
        else:
            now = datetime.utcnow()
            start = (now - timedelta(days=30)).isoformat()
            events = [e for e in self.risk_events.values() if e.timestamp >= start]
        
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "time_range": time_range or {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "summary": {
                "total_events": len(events),
                "open_events": sum(1 for e in events if e.status == "open"),
                "resolved_events": sum(1 for e in events if e.status == "resolved"),
            },
            "events_by_category": defaultdict(int),
            "events_by_severity": defaultdict(int),
            "top_risks": [],
            "correlations": [],
            "recommendations": [],
        }
        
        for event in events:
            report["events_by_category"][event.category] += 1
            report["events_by_severity"][event.severity] += 1
        
        report["events_by_category"] = dict(report["events_by_category"])
        report["events_by_severity"] = dict(report["events_by_severity"])
        
        sorted_events = sorted(events, key=lambda e: e.composite_score, reverse=True)
        report["top_risks"] = [
            {
                "title": e.title,
                "severity": e.severity,
                "composite_score": e.composite_score,
                "category": e.category,
            }
            for e in sorted_events[:10]
        ]
        
        report["correlations"] = await self.get_correlations()
        
        report["recommendations"] = self._generate_recommendations(events)
        
        return report
    
    def _generate_recommendations(self, events: List[RiskEvent]) -> List[str]:
        recommendations = []
        
        critical_count = sum(1 for e in events if e.severity == RiskSeverity.CRITICAL.value)
        if critical_count > 0:
            recommendations.append(f"立即处理{critical_count}个严重风险事件")
        
        category_counts = defaultdict(int)
        for event in events:
            category_counts[event.category] += 1
        
        for category, count in category_counts.items():
            if count >= 5:
                recommendations.append(f"重点关注{category}类风险，共{count}个事件")
        
        if len(self.correlations) > 0:
            recommendations.append("存在关联风险事件，建议系统性排查")
        
        return recommendations
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_events": self.stats["total_events"],
            "events_by_category": dict(self.stats["events_by_category"]),
            "events_by_severity": dict(self.stats["events_by_severity"]),
            "events_by_source": dict(self.stats["events_by_source"]),
            "open_events": self.stats["open_events"],
            "resolved_events": self.stats["resolved_events"],
            "correlations_found": self.stats["correlations_found"],
        }
