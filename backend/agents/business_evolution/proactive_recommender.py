"""
主动推荐引擎
Proactive Recommender - 在适当时机向用户推荐相关服务

礼部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import random
from collections import defaultdict


class RecommendationType(Enum):
    COMMUNITY = "community"
    REPORT = "report"
    FEATURE = "feature"
    ACTIVITY = "activity"
    ARTICLE = "article"
    EXPERT_QA = "expert_qa"
    SIMILAR_PROPERTY = "similar_property"
    PRICE_ALERT = "price_alert"
    LOAN_CALCULATOR = "loan_calculator"
    SCHOOL_INFO = "school_info"


class RecommendationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TriggerType(Enum):
    POST_CONSULTATION = "post_consultation"
    POST_PRICE_QUERY = "post_price_query"
    USER_SILENCE = "user_silence"
    REPEATED_QUESTION = "repeated_question"
    DATA_UPDATE = "data_update"
    TIME_BASED = "time_based"
    BEHAVIOR_PATTERN = "behavior_pattern"


@dataclass
class RecommendationContext:
    context_id: str
    trigger_type: TriggerType
    current_topic: str
    recent_queries: List[str]
    user_state: Dict[str, Any]
    session_duration_seconds: int
    interaction_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Recommendation:
    recommendation_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    action_url: str
    priority: RecommendationPriority
    relevance_score: float
    trigger_type: TriggerType
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationResult:
    recommendations: List[Recommendation]
    context: RecommendationContext
    total_score: float
    algorithm_used: str
    generated_at: datetime = field(default_factory=datetime.utcnow)


class TriggerDetector:
    def __init__(self):
        self.silence_threshold_seconds = 10
        self.repeat_threshold = 3

    def detect_triggers(
        self,
        context: RecommendationContext,
        conversation_history: List[Dict] = None,
    ) -> List[TriggerType]:
        triggers = []

        if context.trigger_type == TriggerType.POST_CONSULTATION:
            triggers.append(TriggerType.POST_CONSULTATION)

        if context.trigger_type == TriggerType.POST_PRICE_QUERY:
            triggers.append(TriggerType.POST_PRICE_QUERY)

        if context.session_duration_seconds > self.silence_threshold_seconds:
            if context.interaction_count == 0:
                triggers.append(TriggerType.USER_SILENCE)

        if conversation_history:
            recent_queries = [
                msg.get("content", "")
                for msg in conversation_history[-5:]
                if msg.get("role") == "user"
            ]

            if len(recent_queries) >= 2:
                similarity = self._calculate_similarity(recent_queries[-1], recent_queries[-2])
                if similarity > 0.8:
                    triggers.append(TriggerType.REPEATED_QUESTION)

        return triggers

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


class ContentMatcher:
    TOPIC_MAPPINGS = {
        "房价": [RecommendationType.PRICE_ALERT, RecommendationType.REPORT],
        "小区": [RecommendationType.COMMUNITY, RecommendationType.SIMILAR_PROPERTY],
        "学区": [RecommendationType.SCHOOL_INFO, RecommendationType.COMMUNITY],
        "贷款": [RecommendationType.LOAN_CALCULATOR, RecommendationType.ARTICLE],
        "投资": [RecommendationType.REPORT, RecommendationType.EXPERT_QA],
    }

    def __init__(self):
        self.content_library: Dict[RecommendationType, List[Dict]] = {
            rt: [] for rt in RecommendationType
        }

    def register_content(
        self,
        recommendation_type: RecommendationType,
        content: Dict[str, Any],
    ) -> None:
        self.content_library[recommendation_type].append(content)

    def match(
        self,
        topic: str,
        user_preferences: Dict[str, Any] = None,
        limit: int = 5,
    ) -> List[Tuple[RecommendationType, float]]:
        matches = []

        for keyword, types in self.TOPIC_MAPPINGS.items():
            if keyword in topic:
                for rt in types:
                    relevance = 0.8
                    if user_preferences:
                        pref_score = user_preferences.get(rt.value, 0.5)
                        relevance = (relevance + pref_score) / 2
                    matches.append((rt, relevance))

        if not matches:
            default_types = [
                RecommendationType.FEATURE,
                RecommendationType.ACTIVITY,
            ]
            matches = [(rt, 0.3) for rt in default_types]

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]


class CollaborativeFilter:
    def __init__(self):
        self.user_item_matrix: Dict[str, Dict[str, float]] = {}
        self.item_similarity: Dict[str, Dict[str, float]] = {}

    def record_interaction(
        self,
        user_id: str,
        item_id: str,
        interaction_type: str,
        score: float = 1.0,
    ) -> None:
        if user_id not in self.user_item_matrix:
            self.user_item_matrix[user_id] = {}

        current_score = self.user_item_matrix[user_id].get(item_id, 0)
        self.user_item_matrix[user_id][item_id] = current_score + score

    def find_similar_users(self, user_id: str, limit: int = 10) -> List[Tuple[str, float]]:
        if user_id not in self.user_item_matrix:
            return []

        user_items = self.user_item_matrix[user_id]
        similarities = []

        for other_user, other_items in self.user_item_matrix.items():
            if other_user == user_id:
                continue

            similarity = self._cosine_similarity(user_items, other_items)
            if similarity > 0:
                similarities.append((other_user, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def recommend_from_similar_users(
        self, user_id: str, limit: int = 5
    ) -> List[Tuple[str, float]]:
        similar_users = self.find_similar_users(user_id)

        if not similar_users:
            return []

        user_items = set(self.user_item_matrix.get(user_id, {}).keys())
        recommendations: Dict[str, float] = {}

        for similar_user, similarity in similar_users:
            for item_id, score in self.user_item_matrix[similar_user].items():
                if item_id not in user_items:
                    recommendations[item_id] = recommendations.get(item_id, 0) + similarity * score

        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return sorted_recs[:limit]

    def _cosine_similarity(
        self, items1: Dict[str, float], items2: Dict[str, float]
    ) -> float:
        common_items = set(items1.keys()) & set(items2.keys())

        if not common_items:
            return 0.0

        dot_product = sum(items1[item] * items2[item] for item in common_items)

        norm1 = sum(v**2 for v in items1.values()) ** 0.5
        norm2 = sum(v**2 for v in items2.values()) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class RecommendationFrequencyController:
    def __init__(self):
        self.user_recommendation_history: Dict[str, List[Dict]] = {}
        self.default_cooldown_minutes = 30
        self.max_per_session = 3

    def can_recommend(
        self,
        user_id: str,
        recommendation_type: RecommendationType,
        session_id: str = None,
    ) -> bool:
        history = self.user_recommendation_history.get(user_id, [])

        recent = [
            h
            for h in history
            if datetime.fromisoformat(h["timestamp"])
            > datetime.utcnow() - timedelta(minutes=self.default_cooldown_minutes)
        ]

        if len(recent) >= self.max_per_session:
            return False

        type_recent = [
            h
            for h in recent
            if h["type"] == recommendation_type.value
        ]

        if type_recent:
            return False

        return True

    def record_recommendation(
        self,
        user_id: str,
        recommendation_type: RecommendationType,
        session_id: str = None,
    ) -> None:
        if user_id not in self.user_recommendation_history:
            self.user_recommendation_history[user_id] = []

        self.user_recommendation_history[user_id].append(
            {
                "type": recommendation_type.value,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def record_feedback(
        self,
        user_id: str,
        recommendation_id: str,
        action: str,
    ) -> None:
        pass

    def set_user_preference(
        self, user_id: str, enable_recommendations: bool
    ) -> None:
        pass


class ProactiveRecommender:
    def __init__(self, agent_id: str = "proactive_recommender_001"):
        self.agent_id = agent_id
        self.trigger_detector = TriggerDetector()
        self.content_matcher = ContentMatcher()
        self.collaborative_filter = CollaborativeFilter()
        self.frequency_controller = RecommendationFrequencyController()

        self.recommendation_history: List[RecommendationResult] = []
        self._initialize_default_content()

    def _initialize_default_content(self) -> None:
        self.content_matcher.register_content(
            RecommendationType.REPORT,
            {
                "title": "房价分析报告",
                "description": "生成详细的房价趋势分析报告",
                "action_url": "/report/generate",
            },
        )

        self.content_matcher.register_content(
            RecommendationType.COMMUNITY,
            {
                "title": "小区详情",
                "description": "查看小区完整信息",
                "action_url": "/community/",
            },
        )

        self.content_matcher.register_content(
            RecommendationType.LOAN_CALCULATOR,
            {
                "title": "贷款计算器",
                "description": "计算您的月供和总利息",
                "action_url": "/tools/loan-calculator",
            },
        )

        self.content_matcher.register_content(
            RecommendationType.SCHOOL_INFO,
            {
                "title": "学区查询",
                "description": "查看周边学校信息",
                "action_url": "/school/search",
            },
        )

        self.content_matcher.register_content(
            RecommendationType.PRICE_ALERT,
            {
                "title": "价格提醒",
                "description": "设置房价变动提醒",
                "action_url": "/alert/price",
            },
        )

    async def generate_recommendations(
        self,
        context: RecommendationContext,
        user_id: str = None,
        user_preferences: Dict[str, Any] = None,
        conversation_history: List[Dict] = None,
    ) -> RecommendationResult:
        triggers = self.trigger_detector.detect_triggers(
            context, conversation_history
        )

        content_matches = self.content_matcher.match(
            context.current_topic, user_preferences
        )

        collab_recs = []
        if user_id:
            collab_recs = self.collaborative_filter.recommend_from_similar_users(user_id)

        recommendations = []

        for rec_type, relevance in content_matches:
            if user_id and not self.frequency_controller.can_recommend(
                user_id, rec_type
            ):
                continue

            content = self.content_matcher.content_library.get(rec_type, [])
            if content:
                item = content[0]
                rec = Recommendation(
                    recommendation_id=f"rec_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                    recommendation_type=rec_type,
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    action_url=item.get("action_url", ""),
                    priority=RecommendationPriority.MEDIUM,
                    relevance_score=relevance,
                    trigger_type=triggers[0] if triggers else TriggerType.TIME_BASED,
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                )
                recommendations.append(rec)

                if user_id:
                    self.frequency_controller.record_recommendation(user_id, rec_type)

        for item_id, score in collab_recs[:2]:
            try:
                rec_type = RecommendationType(item_id.split("_")[0])
            except ValueError:
                continue

            if user_id and not self.frequency_controller.can_recommend(
                user_id, rec_type
            ):
                continue

            rec = Recommendation(
                recommendation_id=f"rec_collab_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                recommendation_type=rec_type,
                title=f"推荐: {item_id}",
                description="基于相似用户行为推荐",
                action_url=f"/recommend/{item_id}",
                priority=RecommendationPriority.LOW,
                relevance_score=score,
                trigger_type=TriggerType.BEHAVIOR_PATTERN,
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        recommendations = recommendations[:5]

        result = RecommendationResult(
            recommendations=recommendations,
            context=context,
            total_score=sum(r.relevance_score for r in recommendations),
            algorithm_used="hybrid_content_collaborative",
        )

        self.recommendation_history.append(result)

        return result

    def record_user_interaction(
        self,
        user_id: str,
        item_id: str,
        interaction_type: str = "view",
    ) -> None:
        score_map = {"view": 1.0, "click": 2.0, "purchase": 5.0, "like": 3.0}
        score = score_map.get(interaction_type, 1.0)

        self.collaborative_filter.record_interaction(
            user_id, item_id, interaction_type, score
        )

    def get_recommendation_stats(self) -> Dict[str, Any]:
        if not self.recommendation_history:
            return {"total_recommendations": 0}

        type_counts: Dict[str, int] = defaultdict(int)
        for result in self.recommendation_history:
            for rec in result.recommendations:
                type_counts[rec.recommendation_type.value] += 1

        return {
            "total_recommendations": sum(len(r.recommendations) for r in self.recommendation_history),
            "by_type": dict(type_counts),
            "average_relevance": sum(
                r.total_score for r in self.recommendation_history
            )
            / len(self.recommendation_history),
        }

    def add_custom_content(
        self,
        recommendation_type: RecommendationType,
        content: Dict[str, Any],
    ) -> None:
        self.content_matcher.register_content(recommendation_type, content)
