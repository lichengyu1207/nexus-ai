"""
作战复盘智能体
After Action Review Agent

在反击结束后自动复盘，分析成功/失败原因，提炼经验
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class ReviewStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class OutcomeType(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ReviewReport:
    report_id: str
    operation_id: str
    status: ReviewStatus
    outcome: OutcomeType
    created_at: datetime
    completed_at: Optional[datetime]
    timeline: List[Dict]
    key_decisions: List[Dict]
    effectiveness_metrics: Dict[str, float]
    resource_usage: Dict[str, Any]
    success_factors: List[str]
    failure_factors: List[str]
    lessons_learned: List[str]
    recommendations: List[str]
    follow_up_actions: List[Dict]
    participants: List[str]
    overall_score: float
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "operation_id": self.operation_id,
            "status": self.status.value,
            "outcome": self.outcome.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timeline": self.timeline,
            "key_decisions": self.key_decisions,
            "effectiveness_metrics": self.effectiveness_metrics,
            "resource_usage": self.resource_usage,
            "success_factors": self.success_factors,
            "failure_factors": self.failure_factors,
            "lessons_learned": self.lessons_learned,
            "recommendations": self.recommendations,
            "follow_up_actions": self.follow_up_actions,
            "participants": self.participants,
            "overall_score": self.overall_score
        }


class TimelineAnalyzer:
    def __init__(self):
        self.phase_thresholds = {
            "detection": 100,
            "attribution": 500,
            "decision": 200,
            "execution": 1000,
            "verification": 300
        }
        
    def analyze(self, events: List[Dict]) -> Dict:
        if not events:
            return {"timeline": [], "phases": {}, "total_duration": 0}
            
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))
        
        phases = {}
        phase_events = defaultdict(list)
        
        for event in sorted_events:
            event_type = event.get("event_type", "unknown")
            phase_events[event_type].append(event)
            
        for phase, events in phase_events.items():
            if events:
                start = datetime.fromisoformat(events[0]["timestamp"])
                end = datetime.fromisoformat(events[-1]["timestamp"])
                phases[phase] = {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "duration_ms": (end - start).total_seconds() * 1000,
                    "event_count": len(events)
                }
                
        total_duration = 0
        if sorted_events:
            start = datetime.fromisoformat(sorted_events[0]["timestamp"])
            end = datetime.fromisoformat(sorted_events[-1]["timestamp"])
            total_duration = (end - start).total_seconds() * 1000
            
        return {
            "timeline": sorted_events,
            "phases": phases,
            "total_duration": total_duration
        }
        
    def identify_bottlenecks(self, phases: Dict) -> List[Dict]:
        bottlenecks = []
        
        for phase, data in phases.items():
            threshold = self.phase_thresholds.get(phase, 500)
            duration = data.get("duration_ms", 0)
            
            if duration > threshold:
                bottlenecks.append({
                    "phase": phase,
                    "duration_ms": duration,
                    "threshold_ms": threshold,
                    "severity": "high" if duration > threshold * 2 else "medium"
                })
                
        return bottlenecks


class EffectivenessEvaluator:
    def __init__(self):
        self.metrics_weights = {
            "attack_stopped": 0.3,
            "attacker_identified": 0.2,
            "damage_prevented": 0.2,
            "resource_efficiency": 0.15,
            "time_efficiency": 0.15
        }
        
    def evaluate(self, operation_data: Dict) -> Dict[str, float]:
        metrics = {}
        
        metrics["attack_stopped"] = self._evaluate_attack_stopped(operation_data)
        metrics["attacker_identified"] = self._evaluate_attribution(operation_data)
        metrics["damage_prevented"] = self._evaluate_damage_prevention(operation_data)
        metrics["resource_efficiency"] = self._evaluate_resource_efficiency(operation_data)
        metrics["time_efficiency"] = self._evaluate_time_efficiency(operation_data)
        
        return metrics
        
    def _evaluate_attack_stopped(self, data: Dict) -> float:
        if data.get("attack_ongoing", True):
            return 0.0
        return 1.0
        
    def _evaluate_attribution(self, data: Dict) -> float:
        attribution = data.get("attribution_result", {})
        confidence = attribution.get("confidence", 0)
        return confidence / 4.0 if isinstance(confidence, int) else confidence
        
    def _evaluate_damage_prevention(self, data: Dict) -> float:
        potential_damage = data.get("potential_damage_score", 1.0)
        actual_damage = data.get("actual_damage_score", 0.0)
        
        if potential_damage == 0:
            return 1.0
            
        prevented = (potential_damage - actual_damage) / potential_damage
        return max(0, min(1, prevented))
        
    def _evaluate_resource_efficiency(self, data: Dict) -> float:
        agents_used = data.get("agents_deployed", 1)
        optimal_agents = data.get("optimal_agents", agents_used)
        
        if optimal_agents == 0:
            return 1.0
            
        ratio = optimal_agents / agents_used
        return min(1, ratio)
        
    def _evaluate_time_efficiency(self, data: Dict) -> float:
        actual_time = data.get("operation_duration_ms", 1)
        expected_time = data.get("expected_duration_ms", actual_time)
        
        if expected_time == 0:
            return 1.0
            
        ratio = expected_time / actual_time
        return min(1, ratio)
        
    def calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        total = 0.0
        for metric, weight in self.metrics_weights.items():
            total += metrics.get(metric, 0) * weight
        return total


class AfterActionReviewAgent:
    def __init__(
        self,
        agent_id: str = "review_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.timeline_analyzer = TimelineAnalyzer()
        self.evaluator = EffectivenessEvaluator()
        
        self.reports: Dict[str, ReviewReport] = {}
        self.pending_reviews: deque = deque(maxlen=100)
        self.review_history: deque = deque(maxlen=500)
        
        self.stats = {
            "total_reviews": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "lessons_extracted": 0,
            "recommendations_generated": 0,
            "avg_review_time_ms": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._review_loop())
        logger.info(f"AfterActionReviewAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"AfterActionReviewAgent {self.agent_id} stopped")
        
    async def _review_loop(self):
        while self._running:
            try:
                while self.pending_reviews:
                    operation_data = self.pending_reviews.popleft()
                    await self._conduct_review(operation_data)
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in review loop: {e}")
                await asyncio.sleep(5)
                
    async def initiate_review(self, operation_data: Dict) -> str:
        operation_id = operation_data.get("operation_id", self._generate_operation_id())
        
        report = ReviewReport(
            report_id=self._generate_report_id(),
            operation_id=operation_id,
            status=ReviewStatus.PENDING,
            outcome=OutcomeType.INCONCLUSIVE,
            created_at=datetime.now(),
            completed_at=None,
            timeline=[],
            key_decisions=[],
            effectiveness_metrics={},
            resource_usage={},
            success_factors=[],
            failure_factors=[],
            lessons_learned=[],
            recommendations=[],
            follow_up_actions=[],
            participants=[],
            overall_score=0.0
        )
        
        self.reports[report.report_id] = report
        self.pending_reviews.append({**operation_data, "report_id": report.report_id})
        
        logger.info(f"Initiated review for operation {operation_id}")
        
        return report.report_id
        
    async def _conduct_review(self, operation_data: Dict) -> ReviewReport:
        start_time = time.time()
        report_id = operation_data.get("report_id")
        
        report = self.reports.get(report_id)
        if not report:
            report = await self._create_report(operation_data)
            
        report.status = ReviewStatus.IN_PROGRESS
        
        timeline_analysis = self.timeline_analyzer.analyze(
            operation_data.get("events", [])
        )
        report.timeline = timeline_analysis["timeline"]
        
        report.effectiveness_metrics = self.evaluator.evaluate(operation_data)
        report.overall_score = self.evaluator.calculate_overall_score(
            report.effectiveness_metrics
        )
        
        report.outcome = self._determine_outcome(report.overall_score)
        
        report.key_decisions = self._extract_key_decisions(operation_data)
        
        report.resource_usage = self._analyze_resource_usage(operation_data)
        
        report.success_factors = self._identify_success_factors(operation_data, report)
        report.failure_factors = self._identify_failure_factors(operation_data, report)
        
        report.lessons_learned = self._extract_lessons(operation_data, report)
        self.stats["lessons_extracted"] += len(report.lessons_learned)
        
        report.recommendations = self._generate_recommendations(report)
        self.stats["recommendations_generated"] += len(report.recommendations)
        
        report.follow_up_actions = self._create_follow_up_actions(report)
        
        report.participants = operation_data.get("participants", [])
        
        report.status = ReviewStatus.COMPLETED
        report.completed_at = datetime.now()
        
        self.stats["total_reviews"] += 1
        if report.outcome == OutcomeType.SUCCESS:
            self.stats["successful_operations"] += 1
        elif report.outcome == OutcomeType.FAILURE:
            self.stats["failed_operations"] += 1
            
        duration = (time.time() - start_time) * 1000
        self._update_avg_review_time(duration)
        
        self.review_history.append(report.to_dict())
        
        if self.memory_client:
            await self.memory_client.store(
                memory_type="operation_log",
                content=report.to_dict(),
                tags={"after_action_review", report.outcome.value},
                priority=2
            )
            
        if self.communication_bus:
            await self.communication_bus.publish(
                "review_completed",
                report.to_dict()
            )
            
        logger.info(f"Completed review {report_id}: outcome={report.outcome.value}, score={report.overall_score:.2f}")
        
        return report
        
    async def _create_report(self, operation_data: Dict) -> ReviewReport:
        operation_id = operation_data.get("operation_id", self._generate_operation_id())
        
        return ReviewReport(
            report_id=self._generate_report_id(),
            operation_id=operation_id,
            status=ReviewStatus.PENDING,
            outcome=OutcomeType.INCONCLUSIVE,
            created_at=datetime.now(),
            completed_at=None,
            timeline=[],
            key_decisions=[],
            effectiveness_metrics={},
            resource_usage={},
            success_factors=[],
            failure_factors=[],
            lessons_learned=[],
            recommendations=[],
            follow_up_actions=[],
            participants=[],
            overall_score=0.0
        )
        
    def _determine_outcome(self, score: float) -> OutcomeType:
        if score >= 0.8:
            return OutcomeType.SUCCESS
        elif score >= 0.5:
            return OutcomeType.PARTIAL_SUCCESS
        elif score >= 0.2:
            return OutcomeType.FAILURE
        else:
            return OutcomeType.INCONCLUSIVE
            
    def _extract_key_decisions(self, data: Dict) -> List[Dict]:
        decisions = []
        
        events = data.get("events", [])
        for event in events:
            if event.get("event_type") in ["decision", "action", "counter_strike"]:
                decisions.append({
                    "timestamp": event.get("timestamp"),
                    "decision": event.get("description", event.get("action_type", "unknown")),
                    "actor": event.get("agent_id", "system"),
                    "context": event.get("context", {})
                })
                
        return decisions
        
    def _analyze_resource_usage(self, data: Dict) -> Dict:
        return {
            "agents_deployed": data.get("agents_deployed", 0),
            "honeypots_created": data.get("honeypots_created", 0),
            "counter_strikes_executed": data.get("counter_strikes_executed", 0),
            "compute_time_ms": data.get("operation_duration_ms", 0),
            "memory_used_mb": data.get("memory_used_mb", 0)
        }
        
    def _identify_success_factors(self, data: Dict, report: ReviewReport) -> List[str]:
        factors = []
        
        if report.effectiveness_metrics.get("attack_stopped", 0) > 0.8:
            factors.append("及时有效的攻击阻断")
            
        if report.effectiveness_metrics.get("attacker_identified", 0) > 0.7:
            factors.append("准确的攻击者溯源")
            
        if report.effectiveness_metrics.get("time_efficiency", 0) > 0.8:
            factors.append("快速响应时间")
            
        if data.get("honeypot_interactions", 0) > 5:
            factors.append("有效的蜜罐诱捕")
            
        if data.get("coordination_score", 0) > 0.7:
            factors.append("良好的智能体协同")
            
        return factors
        
    def _identify_failure_factors(self, data: Dict, report: ReviewReport) -> List[str]:
        factors = []
        
        if report.effectiveness_metrics.get("attack_stopped", 1) < 0.5:
            factors.append("未能有效阻止攻击")
            
        if report.effectiveness_metrics.get("attacker_identified", 1) < 0.3:
            factors.append("攻击者溯源失败")
            
        bottlenecks = self.timeline_analyzer.identify_bottlenecks(
            self.timeline_analyzer.analyze(data.get("events", []))["phases"]
        )
        
        for bottleneck in bottlenecks:
            factors.append(f"阶段{bottleneck['phase']}耗时过长")
            
        if data.get("false_positives", 0) > 3:
            factors.append("误报过多影响判断")
            
        return factors
        
    def _extract_lessons(self, data: Dict, report: ReviewReport) -> List[str]:
        lessons = []
        
        if report.outcome == OutcomeType.SUCCESS:
            if report.success_factors:
                lessons.append(f"成功经验: {report.success_factors[0]}")
        else:
            if report.failure_factors:
                lessons.append(f"改进方向: {report.failure_factors[0]}")
                
        attack_type = data.get("attack_type")
        if attack_type:
            effective_actions = data.get("effective_actions", [])
            if effective_actions:
                lessons.append(f"针对{attack_type}攻击，{effective_actions[0]}效果显著")
                
        return lessons
        
    def _generate_recommendations(self, report: ReviewReport) -> List[str]:
        recommendations = []
        
        if report.effectiveness_metrics.get("time_efficiency", 1) < 0.5:
            recommendations.append("优化响应流程，缩短决策时间")
            
        if report.effectiveness_metrics.get("resource_efficiency", 1) < 0.5:
            recommendations.append("优化资源分配策略，避免过度部署")
            
        if report.outcome == OutcomeType.FAILURE:
            recommendations.append("复盘失败原因，更新战术库")
            recommendations.append("加强相关场景的训练")
            
        bottlenecks = self.timeline_analyzer.identify_bottlenecks({})
        if bottlenecks:
            recommendations.append("识别并解决流程瓶颈")
            
        return recommendations
        
    def _create_follow_up_actions(self, report: ReviewReport) -> List[Dict]:
        actions = []
        
        if report.outcome != OutcomeType.SUCCESS:
            actions.append({
                "action": "更新战术库",
                "priority": "high",
                "assignee": "tactical_library_agent"
            })
            
        if report.failure_factors:
            actions.append({
                "action": "改进失败因素",
                "priority": "medium",
                "details": report.failure_factors
            })
            
        for rec in report.recommendations[:3]:
            actions.append({
                "action": rec,
                "priority": "low",
                "status": "pending"
            })
            
        return actions
        
    async def get_report(self, report_id: str) -> Optional[Dict]:
        report = self.reports.get(report_id)
        return report.to_dict() if report else None
        
    async def get_recent_reports(self, limit: int = 20) -> List[Dict]:
        reports = list(self.review_history)[-limit:]
        return reports
        
    async def get_reports_by_outcome(self, outcome: OutcomeType) -> List[Dict]:
        return [
            r for r in self.review_history
            if r.get("outcome") == outcome.value
        ]
        
    def _generate_report_id(self) -> str:
        return f"review_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def _generate_operation_id(self) -> str:
        return f"op_{int(time.time())}"
        
    def _update_avg_review_time(self, duration: float):
        current = self.stats["avg_review_time_ms"]
        count = self.stats["total_reviews"]
        self.stats["avg_review_time_ms"] = (current * (count - 1) + duration) / count
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "pending_reviews": len(self.pending_reviews),
            "total_reports": len(self.reports)
        }
