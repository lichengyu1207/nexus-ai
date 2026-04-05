"""
业务-合规双向反馈智能体
Compliance Business Feedback Agent

负责收集业务智能体对合规规则的反馈，并持续优化合规系统。
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


class FeedbackType(Enum):
    FEASIBILITY = "feasibility"
    IMPACT = "impact"
    SUGGESTION = "suggestion"
    CONFLICT = "conflict"
    CLARIFICATION = "clarification"


class FeedbackStatus(Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceFeedback:
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    source_agent_id: str = ""
    feedback_type: str = ""
    priority: str = Priority.MEDIUM.value
    
    related_rule_id: str = ""
    related_consultation_id: str = ""
    
    title: str = ""
    description: str = ""
    
    current_situation: str = ""
    proposed_change: str = ""
    business_impact: str = ""
    compliance_impact: str = ""
    
    status: str = FeedbackStatus.SUBMITTED.value
    reviewed_by: str = ""
    reviewed_at: str = ""
    review_notes: str = ""
    
    votes: int = 0
    similar_feedback_count: int = 0


@dataclass
class RuleOptimization:
    optimization_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    rule_id: str = ""
    original_rule: Dict = field(default_factory=dict)
    proposed_change: Dict = field(default_factory=dict)
    
    related_feedback_ids: List[str] = field(default_factory=list)
    justification: str = ""
    
    status: str = "pending"
    approved_by: str = ""
    approved_at: str = ""
    implemented_at: str = ""


class ComplianceBusinessFeedbackAgent:
    """
    业务-合规双向反馈智能体
    
    功能：
    1. 反馈收集：业务智能体反馈合规建议的可行性
    2. 反馈分析：定期汇总反馈，识别常见合规难点
    3. 规则优化：将可行的业务优化建议提交合规官审核
    4. 闭环管理：实现合规-业务-优化的闭环
    5. 效果评估：统计反馈采纳率，评估合规咨询有效性
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ComplianceBusinessFeedbackAgent"
        self.description = "收集业务智能体对合规规则的反馈，持续优化合规系统"
        self.config = config or {}
        
        self.feedbacks: Dict[str, ComplianceFeedback] = {}
        self.agent_feedbacks: Dict[str, List[str]] = defaultdict(list)
        self.optimizations: Dict[str, RuleOptimization] = {}
        
        self.feedback_thresholds = {
            "similar_count_for_priority": 3,
            "votes_for_escalation": 5,
        }
        
        self.stats = {
            "total_feedbacks": 0,
            "feedbacks_by_type": defaultdict(int),
            "feedbacks_by_status": defaultdict(int),
            "feedbacks_by_agent": defaultdict(int),
            "accepted_count": 0,
            "rejected_count": 0,
            "implemented_count": 0,
            "adoption_rate": 0.0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_analysis())
    
    async def _periodic_analysis(self):
        while True:
            await asyncio.sleep(86400)
            await self._analyze_feedbacks()
    
    async def submit_feedback(
        self,
        source_agent_id: str,
        feedback_type: str,
        title: str,
        description: str,
        related_rule_id: str = "",
        related_consultation_id: str = "",
        current_situation: str = "",
        proposed_change: str = "",
        business_impact: str = "",
        compliance_impact: str = "",
    ) -> ComplianceFeedback:
        feedback = ComplianceFeedback(
            source_agent_id=source_agent_id,
            feedback_type=feedback_type,
            title=title,
            description=description,
            related_rule_id=related_rule_id,
            related_consultation_id=related_consultation_id,
            current_situation=current_situation,
            proposed_change=proposed_change,
            business_impact=business_impact,
            compliance_impact=compliance_impact,
        )
        
        similar_count = await self._count_similar_feedbacks(feedback)
        feedback.similar_feedback_count = similar_count
        
        if similar_count >= self.feedback_thresholds["similar_count_for_priority"]:
            feedback.priority = Priority.HIGH.value
        
        self.feedbacks[feedback.feedback_id] = feedback
        self.agent_feedbacks[source_agent_id].append(feedback.feedback_id)
        
        self.stats["total_feedbacks"] += 1
        self.stats["feedbacks_by_type"][feedback_type] += 1
        self.stats["feedbacks_by_status"][FeedbackStatus.SUBMITTED.value] += 1
        self.stats["feedbacks_by_agent"][source_agent_id] += 1
        
        return feedback
    
    async def _count_similar_feedbacks(self, new_feedback: ComplianceFeedback) -> int:
        count = 0
        
        for feedback in self.feedbacks.values():
            if feedback.feedback_type == new_feedback.feedback_type:
                if feedback.related_rule_id and feedback.related_rule_id == new_feedback.related_rule_id:
                    count += 1
                elif any(kw in feedback.description for kw in self._extract_keywords(new_feedback.description)):
                    count += 1
        
        return count
    
    def _extract_keywords(self, text: str) -> List[str]:
        keywords = []
        important_terms = ["同意", "授权", "收集", "使用", "共享", "跨境", "未成年人", "敏感"]
        
        for term in important_terms:
            if term in text:
                keywords.append(term)
        
        return keywords
    
    async def vote_feedback(
        self,
        feedback_id: str,
        voter_agent_id: str,
    ) -> bool:
        feedback = self.feedbacks.get(feedback_id)
        if not feedback:
            return False
        
        feedback.votes += 1
        
        if feedback.votes >= self.feedback_thresholds["votes_for_escalation"]:
            feedback.priority = Priority.HIGH.value
        
        return True
    
    async def review_feedback(
        self,
        feedback_id: str,
        reviewer: str,
        decision: str,
        notes: str = "",
    ) -> bool:
        feedback = self.feedbacks.get(feedback_id)
        if not feedback:
            return False
        
        feedback.status = decision
        feedback.reviewed_by = reviewer
        feedback.reviewed_at = datetime.utcnow().isoformat()
        feedback.review_notes = notes
        
        self.stats["feedbacks_by_status"][FeedbackStatus.SUBMITTED.value] -= 1
        self.stats["feedbacks_by_status"][decision] += 1
        
        if decision == FeedbackStatus.ACCEPTED.value:
            self.stats["accepted_count"] += 1
            await self._create_optimization(feedback)
        elif decision == FeedbackStatus.REJECTED.value:
            self.stats["rejected_count"] += 1
        
        self._update_adoption_rate()
        
        return True
    
    async def _create_optimization(self, feedback: ComplianceFeedback):
        optimization = RuleOptimization(
            rule_id=feedback.related_rule_id,
            proposed_change={
                "type": feedback.feedback_type,
                "change": feedback.proposed_change,
                "justification": feedback.description,
            },
            related_feedback_ids=[feedback.feedback_id],
            justification=f"基于业务反馈: {feedback.title}",
        )
        
        self.optimizations[optimization.optimization_id] = optimization
    
    async def implement_optimization(
        self,
        optimization_id: str,
        implementer: str,
    ) -> bool:
        optimization = self.optimizations.get(optimization_id)
        if not optimization:
            return False
        
        optimization.status = "implemented"
        optimization.implemented_at = datetime.utcnow().isoformat()
        
        for feedback_id in optimization.related_feedback_ids:
            feedback = self.feedbacks.get(feedback_id)
            if feedback:
                feedback.status = FeedbackStatus.IMPLEMENTED.value
                self.stats["feedbacks_by_status"][FeedbackStatus.ACCEPTED.value] -= 1
                self.stats["feedbacks_by_status"][FeedbackStatus.IMPLEMENTED.value] += 1
                self.stats["implemented_count"] += 1
        
        return True
    
    def _update_adoption_rate(self):
        total = self.stats["total_feedbacks"]
        if total > 0:
            implemented_or_accepted = (
                self.stats["accepted_count"] + 
                self.stats["implemented_count"]
            )
            self.stats["adoption_rate"] = implemented_or_accepted / total
    
    async def _analyze_feedbacks(self):
        now = datetime.utcnow()
        month_start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)).isoformat()
        
        monthly_feedbacks = [
            f for f in self.feedbacks.values()
            if f.timestamp >= month_start
        ]
        
        type_distribution = defaultdict(int)
        for feedback in monthly_feedbacks:
            type_distribution[feedback.feedback_type] += 1
        
        pain_points = []
        for feedback in monthly_feedbacks:
            if feedback.similar_feedback_count >= 2:
                pain_points.append({
                    "type": feedback.feedback_type,
                    "rule_id": feedback.related_rule_id,
                    "count": feedback.similar_feedback_count + 1,
                    "sample": feedback.description[:100],
                })
        
        return {
            "month": month_start[:7],
            "total_feedbacks": len(monthly_feedbacks),
            "type_distribution": dict(type_distribution),
            "pain_points": pain_points,
        }
    
    async def get_pending_feedbacks(self) -> List[Dict]:
        return [
            {
                "feedback_id": f.feedback_id,
                "source_agent": f.source_agent_id,
                "type": f.feedback_type,
                "priority": f.priority,
                "title": f.title,
                "description": f.description[:200],
                "status": f.status,
                "votes": f.votes,
                "similar_count": f.similar_feedback_count,
                "timestamp": f.timestamp,
            }
            for f in self.feedbacks.values()
            if f.status == FeedbackStatus.SUBMITTED.value
        ]
    
    async def get_feedback_by_agent(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> List[Dict]:
        feedback_ids = self.agent_feedbacks.get(agent_id, [])
        
        return [
            {
                "feedback_id": self.feedbacks[fid].feedback_id,
                "type": self.feedbacks[fid].feedback_type,
                "title": self.feedbacks[fid].title,
                "status": self.feedbacks[fid].status,
                "timestamp": self.feedbacks[fid].timestamp,
            }
            for fid in feedback_ids[-limit:]
            if fid in self.feedbacks
        ]
    
    async def get_optimization_candidates(self) -> List[Dict]:
        return [
            {
                "optimization_id": o.optimization_id,
                "rule_id": o.rule_id,
                "proposed_change": o.proposed_change,
                "justification": o.justification,
                "status": o.status,
                "related_feedback_count": len(o.related_feedback_ids),
            }
            for o in self.optimizations.values()
            if o.status == "pending"
        ]
    
    async def get_feedback_analytics(self) -> Dict:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_feedbacks = [
            f for f in self.feedbacks.values()
            if datetime.fromisoformat(f.timestamp) >= month_start
        ]
        
        return {
            "period": month_start.isoformat(),
            "total_monthly": len(monthly_feedbacks),
            "by_type": dict(defaultdict(int, {
                t: sum(1 for f in monthly_feedbacks if f.feedback_type == t)
                for t in [ft.value for ft in FeedbackType]
            })),
            "by_status": dict(defaultdict(int, {
                s: sum(1 for f in monthly_feedbacks if f.status == s)
                for s in [fs.value for fs in FeedbackStatus]
            })),
            "top_contributors": sorted(
                [(aid, len(fids)) for aid, fids in self.agent_feedbacks.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_feedbacks": self.stats["total_feedbacks"],
            "feedbacks_by_type": dict(self.stats["feedbacks_by_type"]),
            "feedbacks_by_status": dict(self.stats["feedbacks_by_status"]),
            "accepted_count": self.stats["accepted_count"],
            "rejected_count": self.stats["rejected_count"],
            "implemented_count": self.stats["implemented_count"],
            "adoption_rate": round(self.stats["adoption_rate"], 2),
        }
