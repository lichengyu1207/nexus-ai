"""
风险聚合智能体
Risk Aggregation Agent - 汇总各审计智能体发现的风险事件

进行关联分析和优先级排序
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import asyncio
import json
import uuid
from collections import defaultdict


class RiskLevel(Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class RiskCategory(Enum):
    AUDIT_ISSUE = "audit_issue"
    DATA_SECURITY = "data_security"
    PRIVACY_RISK = "privacy_risk"
    AI_ETHICS = "ai_ethics"
    COMPLIANCE_VIOLATION = "compliance_violation"
    ANOMALY = "anomaly"


class RiskStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class RiskEvent:
    event_id: str
    source: str
    category: RiskCategory
    level: RiskLevel
    title: str
    description: str
    affected_entities: List[str]
    raw_data: Dict[str, Any]
    detected_at: datetime
    status: RiskStatus = RiskStatus.OPEN
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    mitigation_actions: List[str] = field(default_factory=list)


@dataclass
class RiskScore:
    entity_id: str
    entity_type: str
    total_score: float
    risk_breakdown: Dict[str, float]
    risk_count: int
    highest_level: RiskLevel
    last_updated: datetime


class RiskCorrelator:
    def __init__(self):
        self.correlation_rules: List[Dict] = []
        self.entity_risk_map: Dict[str, Set[str]] = defaultdict(set)

    def add_correlation_rule(
        self,
        rule_name: str,
        conditions: Dict,
        time_window_minutes: int = 60,
    ) -> None:
        self.correlation_rules.append(
            {
                "name": rule_name,
                "conditions": conditions,
                "time_window_minutes": time_window_minutes,
            }
        )

    def correlate_events(
        self, events: List[RiskEvent]
    ) -> Dict[str, List[List[RiskEvent]]]:
        result = {
            "by_entity": {},
            "by_time": {},
            "by_pattern": [],
        }

        entity_events: Dict[str, List[RiskEvent]] = defaultdict(list)
        for event in events:
            for entity in event.affected_entities:
                entity_events[entity].append(event)
                self.entity_risk_map[entity].add(event.event_id)

        result["by_entity"] = dict(entity_events)

        time_windows = self._group_by_time_window(events, 60)
        result["by_time"] = time_windows

        for rule in self.correlation_rules:
            pattern_matches = self._apply_correlation_rule(events, rule)
            if pattern_matches:
                result["by_pattern"].extend(pattern_matches)

        return result

    def _group_by_time_window(
        self, events: List[RiskEvent], window_minutes: int
    ) -> Dict[str, List[RiskEvent]]:
        if not events:
            return {}

        sorted_events = sorted(events, key=lambda e: e.detected_at)
        windows: Dict[str, List[RiskEvent]] = {}

        current_window_start = sorted_events[0].detected_at
        window_key = current_window_start.strftime("%Y%m%d_%H%M")
        windows[window_key] = []

        for event in sorted_events:
            if (event.detected_at - current_window_start).total_seconds() > window_minutes * 60:
                current_window_start = event.detected_at
                window_key = current_window_start.strftime("%Y%m%d_%H%M")
                windows[window_key] = []

            windows[window_key].append(event)

        return windows

    def _apply_correlation_rule(
        self, events: List[RiskEvent], rule: Dict
    ) -> List[List[RiskEvent]]:
        matches = []
        conditions = rule["conditions"]
        time_window = timedelta(minutes=rule["time_window_minutes"])

        required_categories = conditions.get("categories", [])
        required_levels = conditions.get("levels", [])
        min_count = conditions.get("min_count", 2)

        filtered_events = events
        if required_categories:
            filtered_events = [
                e for e in filtered_events if e.category.value in required_categories
            ]
        if required_levels:
            filtered_events = [
                e for e in filtered_events if e.level.value in required_levels
            ]

        if len(filtered_events) < min_count:
            return matches

        sorted_events = sorted(filtered_events, key=lambda e: e.detected_at)

        for i, event in enumerate(sorted_events):
            window_events = [event]
            for other in sorted_events[i + 1 :]:
                if other.detected_at - event.detected_at <= time_window:
                    window_events.append(other)

            if len(window_events) >= min_count:
                matches.append(window_events)

        return matches

    def detect_attack_chain(self, events: List[RiskEvent]) -> List[Dict]:
        attack_chains = []

        attack_patterns = [
            {
                "name": "数据泄露链",
                "sequence": ["anomaly", "audit_issue", "privacy_risk"],
            },
            {
                "name": "权限提升链",
                "sequence": ["audit_issue", "data_security"],
            },
            {
                "name": "合规违规链",
                "sequence": ["compliance_violation", "privacy_risk", "data_security"],
            },
        ]

        sorted_events = sorted(events, key=lambda e: e.detected_at)

        for pattern in attack_patterns:
            sequence = pattern["sequence"]
            chain = []
            sequence_idx = 0

            for event in sorted_events:
                if sequence_idx < len(sequence):
                    if event.category.value == sequence[sequence_idx]:
                        chain.append(event)
                        sequence_idx += 1

            if len(chain) == len(sequence):
                attack_chains.append(
                    {
                        "pattern": pattern["name"],
                        "events": [e.event_id for e in chain],
                        "start_time": chain[0].detected_at.isoformat(),
                        "end_time": chain[-1].detected_at.isoformat(),
                    }
                )

        return attack_chains


class RiskScorer:
    LEVEL_WEIGHTS = {
        RiskLevel.P0: 100,
        RiskLevel.P1: 50,
        RiskLevel.P2: 20,
        RiskLevel.P3: 5,
    }

    CATEGORY_MULTIPLIERS = {
        RiskCategory.DATA_SECURITY: 1.5,
        RiskCategory.PRIVACY_RISK: 1.4,
        RiskCategory.COMPLIANCE_VIOLATION: 1.3,
        RiskCategory.AI_ETHICS: 1.2,
        RiskCategory.AUDIT_ISSUE: 1.0,
        RiskCategory.ANOMALY: 0.8,
    }

    def __init__(self):
        self.custom_weights: Dict[str, float] = {}

    def set_custom_weight(self, category: str, weight: float) -> None:
        self.custom_weights[category] = weight

    def calculate_event_score(self, event: RiskEvent) -> float:
        base_score = self.LEVEL_WEIGHTS.get(event.level, 10)
        multiplier = self.CATEGORY_MULTIPLIERS.get(event.category, 1.0)

        if event.category.value in self.custom_weights:
            multiplier *= self.custom_weights[event.category.value]

        affected_count = len(event.affected_entities)
        entity_factor = min(1.0 + (affected_count - 1) * 0.1, 2.0)

        return base_score * multiplier * entity_factor

    def calculate_entity_score(
        self, entity_id: str, events: List[RiskEvent]
    ) -> RiskScore:
        entity_events = [
            e for e in events if entity_id in e.affected_entities
        ]

        if not entity_events:
            return RiskScore(
                entity_id=entity_id,
                entity_type="unknown",
                total_score=0,
                risk_breakdown={},
                risk_count=0,
                highest_level=RiskLevel.P3,
                last_updated=datetime.utcnow(),
            )

        risk_breakdown: Dict[str, float] = defaultdict(float)
        total_score = 0
        highest_level = RiskLevel.P3

        for event in entity_events:
            score = self.calculate_event_score(event)
            total_score += score
            risk_breakdown[event.category.value] += score

            if self._level_priority(event.level) < self._level_priority(highest_level):
                highest_level = event.level

        return RiskScore(
            entity_id=entity_id,
            entity_type=self._determine_entity_type(entity_id),
            total_score=round(total_score, 2),
            risk_breakdown=dict(risk_breakdown),
            risk_count=len(entity_events),
            highest_level=highest_level,
            last_updated=datetime.utcnow(),
        )

    def _level_priority(self, level: RiskLevel) -> int:
        priorities = {RiskLevel.P0: 0, RiskLevel.P1: 1, RiskLevel.P2: 2, RiskLevel.P3: 3}
        return priorities.get(level, 4)

    def _determine_entity_type(self, entity_id: str) -> str:
        if entity_id.startswith("user_"):
            return "user"
        elif entity_id.startswith("agent_"):
            return "agent"
        elif entity_id.startswith("asset_"):
            return "asset"
        elif entity_id.startswith("system_"):
            return "system"
        return "unknown"


class RiskPrioritizer:
    def __init__(self):
        self.priority_rules: List[Dict] = []

    def add_priority_rule(
        self, rule_name: str, conditions: Dict, priority_boost: float
    ) -> None:
        self.priority_rules.append(
            {
                "name": rule_name,
                "conditions": conditions,
                "priority_boost": priority_boost,
            }
        )

    def prioritize_events(
        self, events: List[RiskEvent], scores: Dict[str, float]
    ) -> List[RiskEvent]:
        scored_events = []
        for event in events:
            score = scores.get(event.event_id, 0)

            for rule in self.priority_rules:
                if self._matches_conditions(event, rule["conditions"]):
                    score *= rule["priority_boost"]

            scored_events.append((event, score))

        scored_events.sort(key=lambda x: x[1], reverse=True)
        return [event for event, _ in scored_events]

    def _matches_conditions(self, event: RiskEvent, conditions: Dict) -> bool:
        if "categories" in conditions:
            if event.category.value not in conditions["categories"]:
                return False

        if "levels" in conditions:
            if event.level.value not in conditions["levels"]:
                return False

        if "tags" in conditions:
            if not any(tag in event.tags for tag in conditions["tags"]):
                return False

        return True

    def get_top_risks(
        self, events: List[RiskEvent], limit: int = 10
    ) -> List[Dict]:
        return [
            {
                "event_id": event.event_id,
                "level": event.level.value,
                "category": event.category.value,
                "title": event.title,
                "detected_at": event.detected_at.isoformat(),
                "status": event.status.value,
                "affected_entities": event.affected_entities,
            }
            for event in events[:limit]
        ]


class RiskAggregationAgent:
    def __init__(self, agent_id: str = "risk_aggregation_001"):
        self.agent_id = agent_id
        self.correlator = RiskCorrelator()
        self.scorer = RiskScorer()
        self.prioritizer = RiskPrioritizer()

        self.risk_events: List[RiskEvent] = []
        self.entity_scores: Dict[str, RiskScore] = {}
        self.event_scores: Dict[str, float] = {}

        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        self.correlator.add_correlation_rule(
            "multiple_high_risks",
            {"levels": ["p0", "p1"], "min_count": 3},
            time_window_minutes=30,
        )

        self.correlator.add_correlation_rule(
            "cross_category_risks",
            {"min_count": 2},
            time_window_minutes=60,
        )

        self.prioritizer.add_priority_rule(
            "critical_data_security",
            {"categories": ["data_security"], "levels": ["p0", "p1"]},
            1.5,
        )

        self.prioritizer.add_priority_rule(
            "privacy_breach",
            {"categories": ["privacy_risk"], "levels": ["p0"]},
            2.0,
        )

    def ingest_risk_event(
        self,
        source: str,
        category: RiskCategory,
        level: RiskLevel,
        title: str,
        description: str,
        affected_entities: List[str],
        raw_data: Dict[str, Any],
        tags: List[str] = None,
    ) -> RiskEvent:
        event = RiskEvent(
            event_id=f"risk_{uuid.uuid4().hex[:8]}",
            source=source,
            category=category,
            level=level,
            title=title,
            description=description,
            affected_entities=affected_entities,
            raw_data=raw_data,
            detected_at=datetime.utcnow(),
            tags=tags or [],
        )

        self.risk_events.append(event)

        score = self.scorer.calculate_event_score(event)
        self.event_scores[event.event_id] = score

        for entity in affected_entities:
            self.entity_scores[entity] = self.scorer.calculate_entity_score(
                entity, self.risk_events
            )

        return event

    def aggregate_risks(self) -> Dict[str, Any]:
        correlations = self.correlator.correlate_events(self.risk_events)
        attack_chains = self.correlator.detect_attack_chain(self.risk_events)

        prioritized = self.prioritizer.prioritize_events(
            self.risk_events, self.event_scores
        )

        top_risks = self.prioritizer.get_top_risks(prioritized)

        return {
            "total_events": len(self.risk_events),
            "by_level": self._count_by_level(),
            "by_category": self._count_by_category(),
            "by_status": self._count_by_status(),
            "correlations": {
                "entity_correlations": len(correlations["by_entity"]),
                "time_correlations": len(correlations["by_time"]),
                "pattern_correlations": len(correlations["by_pattern"]),
            },
            "attack_chains": attack_chains,
            "top_risks": top_risks,
            "high_risk_entities": self._get_high_risk_entities(),
        }

    def _count_by_level(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for event in self.risk_events:
            counts[event.level.value] += 1
        return dict(counts)

    def _count_by_category(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for event in self.risk_events:
            counts[event.category.value] += 1
        return dict(counts)

    def _count_by_status(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for event in self.risk_events:
            counts[event.status.value] += 1
        return dict(counts)

    def _get_high_risk_entities(self, threshold: float = 50) -> List[Dict]:
        high_risk = [
            {
                "entity_id": entity_id,
                "total_score": score.total_score,
                "risk_count": score.risk_count,
                "highest_level": score.highest_level.value,
                "risk_breakdown": score.risk_breakdown,
            }
            for entity_id, score in self.entity_scores.items()
            if score.total_score >= threshold
        ]

        return sorted(high_risk, key=lambda x: x["total_score"], reverse=True)

    def get_risk_trend(self, days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_events = [e for e in self.risk_events if e.detected_at >= cutoff]

        daily_counts: Dict[str, int] = defaultdict(int)
        for event in recent_events:
            day = event.detected_at.strftime("%Y-%m-%d")
            daily_counts[day] += 1

        daily_scores: Dict[str, float] = defaultdict(float)
        for event in recent_events:
            day = event.detected_at.strftime("%Y-%m-%d")
            daily_scores[day] += self.event_scores.get(event.event_id, 0)

        return {
            "period_days": days,
            "total_events": len(recent_events),
            "daily_counts": dict(daily_counts),
            "daily_scores": {k: round(v, 2) for k, v in daily_scores.items()},
            "average_daily_events": len(recent_events) / days if days > 0 else 0,
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_risks": len(self.risk_events),
                "open_risks": sum(
                    1 for e in self.risk_events if e.status == RiskStatus.OPEN
                ),
                "critical_risks": sum(
                    1 for e in self.risk_events if e.level == RiskLevel.P0
                ),
                "high_risks": sum(
                    1 for e in self.risk_events if e.level == RiskLevel.P1
                ),
            },
            "distribution": {
                "by_level": self._count_by_level(),
                "by_category": self._count_by_category(),
                "by_status": self._count_by_status(),
            },
            "trend": self.get_risk_trend(7),
            "top_risks": self.prioritizer.get_top_risks(
                sorted(self.risk_events, key=lambda e: e.detected_at, reverse=True), 5
            ),
            "high_risk_entities": self._get_high_risk_entities()[:5],
        }

    def update_event_status(
        self, event_id: str, status: RiskStatus, assigned_to: str = None
    ) -> Optional[RiskEvent]:
        event = next((e for e in self.risk_events if e.event_id == event_id), None)
        if event:
            event.status = status
            if assigned_to:
                event.assigned_to = assigned_to
        return event

    def add_mitigation_action(self, event_id: str, action: str) -> Optional[RiskEvent]:
        event = next((e for e in self.risk_events if e.event_id == event_id), None)
        if event:
            event.mitigation_actions.append(action)
        return event

    def generate_daily_report(self) -> Dict[str, Any]:
        today = datetime.utcnow().date()
        today_events = [
            e
            for e in self.risk_events
            if e.detected_at.date() == today
        ]

        return {
            "report_date": today.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "new_risks_today": len(today_events),
                "critical_count": sum(1 for e in today_events if e.level == RiskLevel.P0),
                "high_count": sum(1 for e in today_events if e.level == RiskLevel.P1),
                "resolved_today": sum(
                    1
                    for e in self.risk_events
                    if e.status == RiskStatus.RESOLVED
                    and e.detected_at.date() == today
                ),
            },
            "top_risks": self.prioritizer.get_top_risks(
                sorted(today_events, key=lambda e: e.detected_at, reverse=True), 10
            ),
            "recommendations": self._generate_recommendations(today_events),
        }

    def _generate_recommendations(self, events: List[RiskEvent]) -> List[str]:
        recommendations = []

        critical_events = [e for e in events if e.level == RiskLevel.P0]
        if critical_events:
            recommendations.append(
                f"立即处理{len(critical_events)}个严重风险事件"
            )

        privacy_events = [e for e in events if e.category == RiskCategory.PRIVACY_RISK]
        if privacy_events:
            recommendations.append(
                f"审查{len(privacy_events)}个隐私风险事件，确保符合PIPL要求"
            )

        security_events = [e for e in events if e.category == RiskCategory.DATA_SECURITY]
        if security_events:
            recommendations.append(
                f"检查{len(security_events)}个数据安全事件，加强安全措施"
            )

        return recommendations
