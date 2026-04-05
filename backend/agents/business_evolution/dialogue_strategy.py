"""
对话策略自适应引擎
Dialogue Strategy Engine - 根据用户类型、场景动态调整回复风格

礼部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
import random


class UserType(Enum):
    NOVICE = "novice"
    REGULAR = "regular"
    EXPERT = "expert"
    INVESTOR = "investor"
    FIRST_TIME_BUYER = "first_time_buyer"
    RENTER = "renter"


class DialogueStyle(Enum):
    ENTHUSIASTIC = "enthusiastic"
    PROFESSIONAL = "professional"
    CONCISE = "concise"
    ZHOUYU = "zhouyu"
    LUXUN = "luxun"
    FRIENDLY = "friendly"
    FORMAL = "formal"


class StrategyType(Enum):
    Q_AND_A = "q_and_a"
    GUIDED = "guided"
    STEP_BY_STEP = "step_by_step"
    CONSULTATIVE = "consultative"
    PROACTIVE = "proactive"


class ScenarioType(Enum):
    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    GUIDANCE = "guidance"
    NEGOTIATION = "negotiation"
    EDUCATION = "education"
    SUPPORT = "support"


@dataclass
class UserProfile:
    user_id: str
    user_type: UserType
    experience_level: int
    preferred_style: DialogueStyle
    interaction_count: int
    last_interaction: datetime
    satisfaction_history: List[float] = field(default_factory=list)
    style_preferences: Dict[str, float] = field(default_factory=dict)
    topic_interests: List[str] = field(default_factory=list)
    response_length_preference: str = "medium"
    emoji_usage_ok: bool = True
    technical_terms_ok: bool = False


@dataclass
class DialogueStrategy:
    strategy_id: str
    strategy_type: StrategyType
    style: DialogueStyle
    response_template: str
    follow_up_questions: List[str]
    proactive_suggestions: List[str]
    tone_markers: List[str]
    emoji_usage: bool
    technical_depth: int
    estimated_response_length: int


@dataclass
class StrategyFeedback:
    feedback_id: str
    strategy_id: str
    user_id: str
    rating: int
    continued_conversation: bool
    response_time_seconds: float
    feedback_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UserClassifier:
    def __init__(self):
        self.classification_rules: List[Dict] = []

    def classify(
        self,
        interaction_count: int,
        query_complexity: float,
        topic_diversity: float,
        account_age_days: int,
    ) -> UserType:
        if interaction_count < 3 and account_age_days < 7:
            return UserType.NOVICE

        if query_complexity > 0.7 and topic_diversity > 0.6:
            return UserType.EXPERT

        if topic_diversity < 0.3 and "investment" in str(topic_diversity).lower():
            return UserType.INVESTOR

        if interaction_count > 20:
            return UserType.REGULAR

        return UserType.REGULAR

    def update_classification_rules(self, rules: List[Dict]) -> None:
        self.classification_rules.extend(rules)


class StyleAdapter:
    STYLE_CHARACTERISTICS = {
        DialogueStyle.ENTHUSIASTIC: {
            "greetings": ["您好呀！", "欢迎光临~", "嗨，很高兴见到您！"],
            "closings": ["祝您愉快！", "有问题随时找我哦~", "期待为您服务！"],
            "tone_words": ["太棒了", "非常好", "真不错"],
            "emoji_rate": 0.8,
        },
        DialogueStyle.PROFESSIONAL: {
            "greetings": ["您好", "欢迎咨询", "请问有什么可以帮您"],
            "closings": ["如有其他问题，请随时联系", "感谢您的咨询"],
            "tone_words": ["根据数据", "分析显示", "建议"],
            "emoji_rate": 0.1,
        },
        DialogueStyle.CONCISE: {
            "greetings": ["您好"],
            "closings": ["还有其他问题吗"],
            "tone_words": [],
            "emoji_rate": 0.0,
        },
        DialogueStyle.ZHOUYU: {
            "greetings": ["阁下有礼了", "久仰大名", "幸会幸会"],
            "closings": ["愿阁下诸事顺遂", "后会有期"],
            "tone_words": ["依某之见", "容某细说", "此乃"],
            "emoji_rate": 0.0,
        },
        DialogueStyle.LUXUN: {
            "greetings": ["你好", "请坐"],
            "closings": ["就这样吧", "还有事吗"],
            "tone_words": ["我认为", "据我观察", "实际上"],
            "emoji_rate": 0.0,
        },
    }

    def __init__(self):
        self.style_performance: Dict[DialogueStyle, float] = {
            style: 1.0 for style in DialogueStyle
        }

    def adapt_response(
        self,
        content: str,
        style: DialogueStyle,
        user_preferences: Dict[str, Any] = None,
    ) -> str:
        characteristics = self.STYLE_CHARACTERISTICS.get(style, {})

        if not characteristics:
            return content

        adapted = content

        greeting = random.choice(characteristics.get("greetings", [""]))
        closing = random.choice(characteristics.get("closings", [""]))

        tone_words = characteristics.get("tone_words", [])
        if tone_words and len(adapted) > 50:
            insert_pos = adapted.find("。")
            if insert_pos > 0:
                tone = random.choice(tone_words)
                adapted = adapted[: insert_pos + 1] + f"{tone}，" + adapted[insert_pos + 1 :]

        emoji_rate = characteristics.get("emoji_rate", 0)
        if emoji_rate > 0 and random.random() < emoji_rate:
            emojis = ["😊", "👍", "🏠", "💼", "✨"]
            adapted += " " + random.choice(emojis)

        if user_preferences:
            if user_preferences.get("no_emoji"):
                adapted = adapted.replace("😊", "").replace("👍", "").replace("🏠", "")
                adapted = adapted.replace("💼", "").replace("✨", "").strip()

        return adapted.strip()

    def record_style_performance(
        self, style: DialogueStyle, performance: float
    ) -> None:
        current = self.style_performance.get(style, 1.0)
        self.style_performance[style] = current * 0.9 + performance * 0.1


class ScenarioDetector:
    SCENARIO_INDICATORS = {
        ScenarioType.INQUIRY: ["咨询", "了解", "问一下", "请问"],
        ScenarioType.COMPLAINT: ["投诉", "不满", "差评", "问题", "退款"],
        ScenarioType.GUIDANCE: ["怎么", "如何", "步骤", "流程", "指导"],
        ScenarioType.NEGOTIATION: ["价格", "优惠", "折扣", "便宜"],
        ScenarioType.EDUCATION: ["什么是", "为什么", "解释", "意思"],
        ScenarioType.SUPPORT: ["帮助", "解决", "问题", "故障"],
    }

    def __init__(self):
        self.scenario_history: List[Dict] = []

    def detect(self, text: str, intent_category: str = None) -> ScenarioType:
        text_lower = text.lower()
        scores: Dict[ScenarioType, float] = {}

        for scenario, indicators in self.SCENARIO_INDICATORS.items():
            matches = sum(1 for ind in indicators if ind in text_lower)
            if matches > 0:
                scores[scenario] = matches / len(indicators)

        if not scores:
            return ScenarioType.INQUIRY

        best_scenario = max(scores.items(), key=lambda x: x[1])

        self.scenario_history.append(
            {
                "scenario": best_scenario[0].value,
                "confidence": best_scenario[1],
                "text_preview": text[:50],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return best_scenario[0]


class ABTestManager:
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.results: Dict[str, List[Dict]] = {}

    def create_experiment(
        self,
        experiment_id: str,
        variants: List[Dict],
        traffic_allocation: float = 0.1,
    ) -> None:
        self.experiments[experiment_id] = {
            "variants": variants,
            "traffic_allocation": traffic_allocation,
            "status": "running",
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_variant(self, experiment_id: str, user_id: str) -> Optional[Dict]:
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment["status"] != "running":
            return None

        if random.random() > experiment["traffic_allocation"]:
            return None

        user_hash = hash(user_id) % 100
        variants = experiment["variants"]
        variant_index = user_hash % len(variants)

        return variants[variant_index]

    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        metric: str,
        value: float,
    ) -> None:
        if experiment_id not in self.results:
            self.results[experiment_id] = []

        self.results[experiment_id].append(
            {
                "variant_id": variant_id,
                "metric": metric,
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        results = self.results.get(experiment_id, [])
        if not results:
            return {"status": "no_data"}

        variant_stats: Dict[str, Dict] = {}
        for r in results:
            vid = r["variant_id"]
            if vid not in variant_stats:
                variant_stats[vid] = {"total": 0, "count": 0}
            variant_stats[vid]["total"] += r["value"]
            variant_stats[vid]["count"] += 1

        return {
            "experiment_id": experiment_id,
            "variant_stats": {
                vid: {
                    "average": stats["total"] / stats["count"],
                    "sample_size": stats["count"],
                }
                for vid, stats in variant_stats.items()
            },
        }


class DialogueStrategyEngine:
    def __init__(self, agent_id: str = "dialogue_strategy_001"):
        self.agent_id = agent_id
        self.user_classifier = UserClassifier()
        self.style_adapter = StyleAdapter()
        self.scenario_detector = ScenarioDetector()
        self.ab_test_manager = ABTestManager()

        self.user_profiles: Dict[str, UserProfile] = {}
        self.strategy_templates: Dict[str, DialogueStrategy] = {}
        self.feedback_history: List[StrategyFeedback] = []

        self._initialize_default_strategies()

    def _initialize_default_strategies(self) -> None:
        self.strategy_templates["novice_inquiry"] = DialogueStrategy(
            strategy_id="novice_inquiry",
            strategy_type=StrategyType.GUIDED,
            style=DialogueStyle.ENTHUSIASTIC,
            response_template="让我为您详细解释一下{topic}。{explanation}。您还有其他问题吗？",
            follow_up_questions=["您想了解哪方面的详情？", "需要我推荐相关内容吗？"],
            proactive_suggestions=["查看新手指南", "了解购房流程"],
            tone_markers=["别担心", "我来帮您", "很简单"],
            emoji_usage=True,
            technical_depth=1,
            estimated_response_length=200,
        )

        self.strategy_templates["expert_inquiry"] = DialogueStrategy(
            strategy_id="expert_inquiry",
            strategy_type=StrategyType.Q_AND_A,
            style=DialogueStyle.PROFESSIONAL,
            response_template="{data_summary}。{analysis}。",
            follow_up_questions=["需要更详细的数据吗？", "查看相关报告？"],
            proactive_suggestions=["下载完整报告", "对比分析"],
            tone_markers=["根据分析", "数据显示", "建议"],
            emoji_usage=False,
            technical_depth=3,
            estimated_response_length=150,
        )

        self.strategy_templates["complaint"] = DialogueStrategy(
            strategy_id="complaint",
            strategy_type=StrategyType.CONSULTATIVE,
            style=DialogueStyle.FRIENDLY,
            response_template="非常抱歉给您带来不便。{acknowledgment}。{solution}。",
            follow_up_questions=["这样处理您满意吗？", "还有其他需要帮助的吗？"],
            proactive_suggestions=["联系客服", "提交反馈"],
            tone_markers=["理解您的感受", "我们会改进", "感谢您的反馈"],
            emoji_usage=False,
            technical_depth=1,
            estimated_response_length=180,
        )

        self.strategy_templates["investor"] = DialogueStrategy(
            strategy_id="investor",
            strategy_type=StrategyType.CONSULTATIVE,
            style=DialogueStyle.PROFESSIONAL,
            response_template="{market_analysis}。{roi_projection}。{risk_assessment}。",
            follow_up_questions=["查看投资回报计算？", "对比其他区域？"],
            proactive_suggestions=["投资分析报告", "市场趋势预测"],
            tone_markers=["投资回报率", "增值潜力", "风险评估"],
            emoji_usage=False,
            technical_depth=4,
            estimated_response_length=250,
        )

    def get_or_create_profile(
        self,
        user_id: str,
        interaction_data: Dict[str, Any] = None,
    ) -> UserProfile:
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]

        profile = UserProfile(
            user_id=user_id,
            user_type=UserType.NOVICE,
            experience_level=1,
            preferred_style=DialogueStyle.FRIENDLY,
            interaction_count=0,
            last_interaction=datetime.utcnow(),
        )

        if interaction_data:
            profile.user_type = self.user_classifier.classify(
                interaction_data.get("interaction_count", 0),
                interaction_data.get("query_complexity", 0.5),
                interaction_data.get("topic_diversity", 0.5),
                interaction_data.get("account_age_days", 0),
            )

        self.user_profiles[user_id] = profile
        return profile

    def select_strategy(
        self,
        user_profile: UserProfile,
        scenario: ScenarioType,
        context: Dict[str, Any] = None,
    ) -> DialogueStrategy:
        strategy_key = self._determine_strategy_key(
            user_profile.user_type, scenario
        )

        strategy = self.strategy_templates.get(strategy_key)
        if not strategy:
            strategy = self.strategy_templates.get("novice_inquiry")

        if user_profile.preferred_style != strategy.style:
            if user_profile.satisfaction_history:
                avg_satisfaction = sum(user_profile.satisfaction_history[-5:]) / min(
                    5, len(user_profile.satisfaction_history)
                )
                if avg_satisfaction < 3.0:
                    strategy = DialogueStrategy(
                        strategy_id=f"adapted_{strategy.strategy_id}",
                        strategy_type=strategy.strategy_type,
                        style=user_profile.preferred_style,
                        response_template=strategy.response_template,
                        follow_up_questions=strategy.follow_up_questions,
                        proactive_suggestions=strategy.proactive_suggestions,
                        tone_markers=strategy.tone_markers,
                        emoji_usage=user_profile.emoji_usage_ok,
                        technical_depth=strategy.technical_depth,
                        estimated_response_length=strategy.estimated_response_length,
                    )

        return strategy

    def _determine_strategy_key(
        self, user_type: UserType, scenario: ScenarioType
    ) -> str:
        if scenario == ScenarioType.COMPLAINT:
            return "complaint"

        if user_type == UserType.INVESTOR:
            return "investor"

        if user_type == UserType.EXPERT:
            return "expert_inquiry"

        return "novice_inquiry"

    async def generate_response(
        self,
        strategy: DialogueStrategy,
        content_data: Dict[str, Any],
        user_profile: UserProfile,
    ) -> str:
        response = strategy.response_template

        for key, value in content_data.items():
            placeholder = "{" + key + "}"
            response = response.replace(placeholder, str(value))

        response = self.style_adapter.adapt_response(
            response,
            strategy.style,
            {
                "no_emoji": not user_profile.emoji_usage_ok,
                "technical_ok": user_profile.technical_terms_ok,
            },
        )

        return response

    def record_feedback(
        self,
        strategy_id: str,
        user_id: str,
        rating: int,
        continued_conversation: bool,
        response_time: float,
        feedback_type: str = "explicit",
    ) -> StrategyFeedback:
        feedback = StrategyFeedback(
            feedback_id=f"feedback_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            strategy_id=strategy_id,
            user_id=user_id,
            rating=rating,
            continued_conversation=continued_conversation,
            response_time_seconds=response_time,
            feedback_type=feedback_type,
        )

        self.feedback_history.append(feedback)

        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile.satisfaction_history.append(rating / 5.0)
            profile.satisfaction_history = profile.satisfaction_history[-20:]

            if rating >= 4:
                self.style_adapter.record_style_performance(
                    self._get_style_from_strategy(strategy_id), rating / 5.0
                )

        return feedback

    def _get_style_from_strategy(self, strategy_id: str) -> DialogueStyle:
        strategy = self.strategy_templates.get(strategy_id)
        return strategy.style if strategy else DialogueStyle.FRIENDLY

    def update_user_style_preference(
        self, user_id: str, style: DialogueStyle, weight: float
    ) -> None:
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile.style_preferences[style.value] = weight

            best_style = max(
                profile.style_preferences.items(), key=lambda x: x[1]
            )[0]
            profile.preferred_style = DialogueStyle(best_style)

    def get_strategy_performance(self) -> Dict[str, Any]:
        if not self.feedback_history:
            return {"total_feedback": 0}

        strategy_stats: Dict[str, Dict] = {}
        for feedback in self.feedback_history:
            sid = feedback.strategy_id
            if sid not in strategy_stats:
                strategy_stats[sid] = {
                    "total_ratings": 0,
                    "rating_sum": 0,
                    "continuation_rate": 0,
                    "continuation_count": 0,
                }

            strategy_stats[sid]["total_ratings"] += 1
            strategy_stats[sid]["rating_sum"] += feedback.rating
            if feedback.continued_conversation:
                strategy_stats[sid]["continuation_count"] += 1

        for sid, stats in strategy_stats.items():
            stats["average_rating"] = stats["rating_sum"] / stats["total_ratings"]
            stats["continuation_rate"] = (
                stats["continuation_count"] / stats["total_ratings"]
            )

        return {
            "total_feedback": len(self.feedback_history),
            "strategy_stats": strategy_stats,
        }
