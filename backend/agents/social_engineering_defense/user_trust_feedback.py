"""
用户信任度反馈智能体
负责收集用户对平台安全性的信任度反馈
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class FeedbackType(Enum):
    """反馈类型"""
    TRUST_SURVEY = "trust_survey"
    OPERATION_SATISFACTION = "operation_satisfaction"
    SECURITY_INCIDENT = "security_incident"
    FEATURE_FEEDBACK = "feature_feedback"
    GENERAL_FEEDBACK = "general_feedback"


class TrustLevel(Enum):
    """信任等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FeedbackSentiment(Enum):
    """反馈情感"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class TrustSurvey:
    """信任度调查"""
    survey_id: str
    user_id: str
    trust_score: int
    trust_level: TrustLevel
    security_rating: int
    privacy_rating: int
    transparency_rating: int
    responsiveness_rating: int
    comments: str
    created_at: datetime


@dataclass
class OperationFeedback:
    """操作反馈"""
    feedback_id: str
    user_id: str
    operation_type: str
    felt_safe: bool
    satisfaction_score: int
    concerns: List[str]
    suggestions: str
    created_at: datetime


@dataclass
class TrustMetrics:
    """信任指标"""
    avg_trust_score: float
    trust_distribution: Dict[str, int]
    trend: str
    low_trust_users: int
    high_trust_users: int
    total_responses: int


class UserTrustFeedbackAgent:
    """用户信任度反馈智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "UserTrustFeedbackAgent"
        self.config = config or {}
        self.trust_surveys: Dict[str, List[TrustSurvey]] = defaultdict(list)
        self.operation_feedbacks: Dict[str, List[OperationFeedback]] = defaultdict(list)
        self.survey_counter = 0
        self.feedback_counter = 0
        self.survey_questions = self._init_survey_questions()
        self.stats = {
            "total_surveys": 0,
            "total_feedbacks": 0,
            "avg_trust_score": 0.0,
            "trust_trend": "stable",
            "low_trust_alerts": 0,
            "follow_ups_sent": 0,
        }
    
    def _init_survey_questions(self) -> List[Dict[str, Any]]:
        """初始化调查问题"""
        return [
            {
                "id": "trust_score",
                "question": "您对平台的安全性有多信任？",
                "type": "scale",
                "min": 1,
                "max": 10
            },
            {
                "id": "security_rating",
                "question": "您如何评价平台的安全措施？",
                "type": "scale",
                "min": 1,
                "max": 5
            },
            {
                "id": "privacy_rating",
                "question": "您如何评价平台的隐私保护？",
                "type": "scale",
                "min": 1,
                "max": 5
            },
            {
                "id": "transparency_rating",
                "question": "您认为平台的操作透明度如何？",
                "type": "scale",
                "min": 1,
                "max": 5
            },
            {
                "id": "responsiveness_rating",
                "question": "您对平台安全事件的响应速度满意吗？",
                "type": "scale",
                "min": 1,
                "max": 5
            }
        ]
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def submit_trust_survey(
        self,
        user_id: str,
        trust_score: int,
        security_rating: int,
        privacy_rating: int,
        transparency_rating: int,
        responsiveness_rating: int,
        comments: str = ""
    ) -> TrustSurvey:
        """提交信任度调查"""
        self.survey_counter += 1
        survey_id = f"survey_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.survey_counter}"
        
        if trust_score <= 2:
            trust_level = TrustLevel.VERY_LOW
        elif trust_score <= 4:
            trust_level = TrustLevel.LOW
        elif trust_score <= 6:
            trust_level = TrustLevel.NEUTRAL
        elif trust_score <= 8:
            trust_level = TrustLevel.HIGH
        else:
            trust_level = TrustLevel.VERY_HIGH
        
        survey = TrustSurvey(
            survey_id=survey_id,
            user_id=user_id,
            trust_score=trust_score,
            trust_level=trust_level,
            security_rating=security_rating,
            privacy_rating=privacy_rating,
            transparency_rating=transparency_rating,
            responsiveness_rating=responsiveness_rating,
            comments=comments,
            created_at=datetime.now()
        )
        
        self.trust_surveys[user_id].append(survey)
        self.stats["total_surveys"] += 1
        
        self._update_avg_trust_score()
        
        if trust_level in [TrustLevel.VERY_LOW, TrustLevel.LOW]:
            self.stats["low_trust_alerts"] += 1
        
        return survey
    
    def submit_operation_feedback(
        self,
        user_id: str,
        operation_type: str,
        felt_safe: bool,
        satisfaction_score: int,
        concerns: List[str] = None,
        suggestions: str = ""
    ) -> OperationFeedback:
        """提交操作反馈"""
        self.feedback_counter += 1
        feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.feedback_counter}"
        
        feedback = OperationFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            operation_type=operation_type,
            felt_safe=felt_safe,
            satisfaction_score=satisfaction_score,
            concerns=concerns or [],
            suggestions=suggestions,
            created_at=datetime.now()
        )
        
        self.operation_feedbacks[user_id].append(feedback)
        self.stats["total_feedbacks"] += 1
        
        return feedback
    
    def _update_avg_trust_score(self):
        """更新平均信任分数"""
        all_scores = []
        for surveys in self.trust_surveys.values():
            for survey in surveys:
                all_scores.append(survey.trust_score)
        
        if all_scores:
            self.stats["avg_trust_score"] = sum(all_scores) / len(all_scores)
    
    def calculate_trust_metrics(self, days: int = 30) -> TrustMetrics:
        """计算信任指标"""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_surveys = []
        for surveys in self.trust_surveys.values():
            recent_surveys.extend([s for s in surveys if s.created_at > cutoff])
        
        if not recent_surveys:
            return TrustMetrics(
                avg_trust_score=0,
                trust_distribution={},
                trend="unknown",
                low_trust_users=0,
                high_trust_users=0,
                total_responses=0
            )
        
        avg_score = sum(s.trust_score for s in recent_surveys) / len(recent_surveys)
        
        distribution = defaultdict(int)
        for survey in recent_surveys:
            distribution[survey.trust_level.value] += 1
        
        user_scores: Dict[str, List[int]] = defaultdict(list)
        for survey in recent_surveys:
            user_scores[survey.user_id].append(survey.trust_score)
        
        user_avg_scores = {
            uid: sum(scores) / len(scores)
            for uid, scores in user_scores.items()
        }
        
        low_trust = sum(1 for score in user_avg_scores.values() if score <= 4)
        high_trust = sum(1 for score in user_avg_scores.values() if score >= 8)
        
        trend = self._calculate_trend(recent_surveys)
        
        return TrustMetrics(
            avg_trust_score=avg_score,
            trust_distribution=dict(distribution),
            trend=trend,
            low_trust_users=low_trust,
            high_trust_users=high_trust,
            total_responses=len(recent_surveys)
        )
    
    def _calculate_trend(self, surveys: List[TrustSurvey]) -> str:
        """计算趋势"""
        if len(surveys) < 10:
            return "insufficient_data"
        
        sorted_surveys = sorted(surveys, key=lambda x: x.created_at)
        mid = len(sorted_surveys) // 2
        
        first_half_avg = sum(s.trust_score for s in sorted_surveys[:mid]) / mid
        second_half_avg = sum(s.trust_score for s in sorted_surveys[mid:]) / (len(sorted_surveys) - mid)
        
        change = second_half_avg - first_half_avg
        
        if change > 0.5:
            return "improving"
        elif change < -0.5:
            return "declining"
        else:
            return "stable"
    
    def identify_low_trust_users(self, threshold: int = 4) -> List[Dict[str, Any]]:
        """识别低信任用户"""
        low_trust_users = []
        
        for user_id, surveys in self.trust_surveys.items():
            if surveys:
                recent = [s for s in surveys if s.created_at > datetime.now() - timedelta(days=30)]
                if recent:
                    avg_score = sum(s.trust_score for s in recent) / len(recent)
                    if avg_score <= threshold:
                        low_trust_users.append({
                            "user_id": user_id,
                            "avg_trust_score": avg_score,
                            "survey_count": len(recent),
                            "last_survey": max(s.created_at for s in recent).isoformat()
                        })
        
        return sorted(low_trust_users, key=lambda x: x["avg_trust_score"])
    
    def analyze_trust_by_user_segment(self) -> Dict[str, Any]:
        """按用户群体分析信任度"""
        segments: Dict[str, List[int]] = defaultdict(list)
        
        for user_id, surveys in self.trust_surveys.items():
            for survey in surveys:
                segment = self._get_user_segment(user_id)
                segments[segment].append(survey.trust_score)
        
        segment_analysis = {}
        for segment, scores in segments.items():
            if scores:
                segment_analysis[segment] = {
                    "avg_score": sum(scores) / len(scores),
                    "count": len(scores),
                    "min": min(scores),
                    "max": max(scores)
                }
        
        return segment_analysis
    
    def _get_user_segment(self, user_id: str) -> str:
        """获取用户群体"""
        return "general"
    
    def get_concern_analysis(self) -> Dict[str, int]:
        """分析用户关注点"""
        concern_counts = defaultdict(int)
        
        for feedbacks in self.operation_feedbacks.values():
            for feedback in feedbacks:
                for concern in feedback.concerns:
                    concern_counts[concern] += 1
        
        return dict(sorted(concern_counts.items(), key=lambda x: x[1], reverse=True))
    
    def should_send_follow_up(self, user_id: str) -> bool:
        """是否应该发送跟进"""
        surveys = self.trust_surveys.get(user_id, [])
        
        if not surveys:
            return True
        
        recent = [s for s in surveys if s.created_at > datetime.now() - timedelta(days=30)]
        
        if not recent:
            return True
        
        avg_score = sum(s.trust_score for s in recent) / len(recent)
        
        if avg_score <= 4:
            return True
        
        return False
    
    def generate_follow_up_message(self, user_id: str) -> str:
        """生成跟进消息"""
        surveys = self.trust_surveys.get(user_id, [])
        
        if not surveys:
            return "感谢您使用我们的平台。我们非常重视您的安全体验，如有任何问题请随时联系我们。"
        
        latest = max(surveys, key=lambda x: x.created_at)
        
        if latest.trust_score <= 4:
            return f"我们注意到您对平台安全性的信任度较低（评分：{latest.trust_score}/10）。我们非常重视您的反馈，安全团队将主动与您联系，了解具体情况并提供帮助。"
        elif latest.trust_score >= 8:
            return f"感谢您对平台安全性的信任（评分：{latest.trust_score}/10）！我们将继续努力为您提供安全可靠的服务。"
        else:
            return "感谢您的反馈。我们持续改进安全措施，如有任何建议欢迎告诉我们。"
    
    def get_user_trust_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户信任历史"""
        surveys = self.trust_surveys.get(user_id, [])
        
        return [
            {
                "survey_id": s.survey_id,
                "trust_score": s.trust_score,
                "trust_level": s.trust_level.value,
                "security_rating": s.security_rating,
                "created_at": s.created_at.isoformat()
            }
            for s in sorted(surveys, key=lambda x: x.created_at)
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        metrics = self.calculate_trust_metrics()
        
        return {
            **self.stats,
            "trust_distribution": metrics.trust_distribution,
            "trust_trend": metrics.trend,
            "users_with_surveys": len(self.trust_surveys),
            "users_with_feedbacks": len(self.operation_feedbacks),
        }
