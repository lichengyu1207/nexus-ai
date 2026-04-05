# -*- coding: utf-8 -*-
"""
Unit Tests for Consultation Module
Tests individual components in isolation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

from backend.services.consultation.intent_analyzer import (
    IntentAnalyzer, IntentType, IntentResult, get_intent_analyzer
)
from backend.services.consultation.emotion_detector import (
    EmotionDetector, EmotionType, EmotionResult, get_emotion_detector
)
from backend.services.consultation.problem_detector import (
    ProblemDetector, IssueType, DetectedIssue, get_problem_detector
)


class TestIntentAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return IntentAnalyzer()
    
    def test_property_consultation_detection(self, analyzer):
        result = analyzer.analyze("我想在深圳买房，预算300万")
        assert result.intent == "property_consultation"
        assert result.confidence > 0
        assert "city" in result.detected_entities
        assert "budget" in result.detected_entities
    
    def test_destiny_consultation_detection(self, analyzer):
        result = analyzer.analyze("帮我算一下八字，我是1990年出生的")
        assert result.intent == "destiny_consultation"
        assert result.confidence > 0
    
    def test_emotional_support_detection(self, analyzer):
        result = analyzer.analyze("我最近压力很大，很焦虑")
        assert result.intent == "emotional_support"
        assert result.confidence > 0
    
    def test_investment_advice_detection(self, analyzer):
        result = analyzer.analyze("我想投资房产，预算500万，求建议")
        assert result.intent in ["investment_advice", "property_consultation"]
    
    def test_slot_extraction_city(self, analyzer):
        result = analyzer.analyze("我想在北京买房")
        assert "city" in result.detected_entities
        assert "北京" in result.detected_entities["city"]
    
    def test_slot_extraction_budget(self, analyzer):
        result = analyzer.analyze("预算300万")
        assert "budget" in result.detected_entities
    
    def test_slot_extraction_area(self, analyzer):
        result = analyzer.analyze("想要100平的房子")
        assert "area" in result.detected_entities
    
    def test_missing_slots_detection(self, analyzer):
        result = analyzer.analyze("我想买房")
        assert len(result.missing_slots) > 0
        assert len(result.suggested_questions) > 0
    
    def test_context_integration(self, analyzer):
        context = {"slots": {"city": "深圳"}}
        result = analyzer.analyze("预算200万", context)
        assert "city" in result.slots
        assert result.slots["city"] == "深圳"


class TestEmotionDetector:
    
    @pytest.fixture
    def detector(self):
        return EmotionDetector()
    
    def test_anxious_emotion_detection(self, detector):
        result = detector.detect("我很焦虑，压力很大")
        assert result.emotion == EmotionType.ANXIOUS.value
        assert result.score > 0
    
    def test_excited_emotion_detection(self, detector):
        result = detector.detect("太好了！终于等到机会了！")
        assert result.emotion == EmotionType.EXCITED.value
    
    def test_confused_emotion_detection(self, detector):
        result = detector.detect("我不明白，很困惑")
        assert result.emotion == EmotionType.CONFUSED.value
    
    def test_sad_emotion_detection(self, detector):
        result = detector.detect("我很难过，心情不好")
        assert result.emotion == EmotionType.SAD.value
    
    def test_neutral_emotion_detection(self, detector):
        result = detector.detect("我想咨询房产问题")
        assert result.emotion == EmotionType.NEUTRAL.value
    
    def test_support_needed_detection(self, detector):
        result = detector.detect("我很焦虑，压力很大")
        assert detector.should_provide_support(result) == True
    
    def test_support_not_needed_detection(self, detector):
        result = detector.detect("我想买房")
        assert detector.should_provide_support(result) == False
    
    def test_support_message_generation(self, detector):
        message = detector.get_support_message("anxious", "zhouyu")
        assert "阁下" in message or "不必" in message
        
        message = detector.get_support_message("anxious", "luxun")
        assert "理解" in message or "担忧" in message
    
    def test_emotion_trend_analysis(self, detector):
        emotions = [
            EmotionResult(emotion="anxious", score=0.5, confidence=0.8, keywords=[], suggested_response_style="calming"),
            EmotionResult(emotion="anxious", score=0.7, confidence=0.9, keywords=[], suggested_response_style="calming"),
            EmotionResult(emotion="neutral", score=0.3, confidence=0.7, keywords=[], suggested_response_style="professional")
        ]
        trend = detector.get_emotion_trend(emotions)
        assert trend["trend"] == "improving"
        assert "dominant_emotion" in trend


class TestProblemDetector:
    
    @pytest.fixture
    def detector(self):
        return ProblemDetector()
    
    def test_missing_info_detection(self, detector):
        result = detector.analyze(
            "我想买房",
            "property_consultation",
            {},
            None
        )
        assert result.has_issues == True
        assert any(i.issue_type == IssueType.MISSING_INFO.value for i in result.issues)
    
    def test_budget_mismatch_detection(self, detector):
        result = detector.analyze(
            "预算100万想买别墅",
            "property_consultation",
            {"budget": 1000000},
            None
        )
        assert result.has_issues == True
    
    def test_hidden_need_detection(self, detector):
        result = detector.analyze(
            "我想买学区房，孩子要上学",
            "property_consultation",
            {},
            None
        )
        hidden_needs = [i for i in result.issues if i.issue_type == IssueType.HIDDEN_NEED_DETECTED.value]
        assert len(hidden_needs) > 0
    
    def test_no_issues_detection(self, detector):
        result = detector.analyze(
            "我想在深圳买房，预算300万",
            "property_consultation",
            {"city": "深圳", "budget": 3000000},
            None
        )
        assert result.overall_severity in ["none", "low"]
    
    def test_follow_up_questions_generation(self, detector):
        issues = [
            DetectedIssue(
                issue_type=IssueType.MISSING_INFO.value,
                severity="high",
                description="缺少城市信息",
                affected_slots=["city"],
                suggestion="询问城市",
                auto_fixable=False
            )
        ]
        questions = detector._generate_follow_up_questions(issues)
        assert len(questions) > 0


class TestPersonaEngine:
    
    @pytest.fixture
    def engine(self):
        from backend.services.consultation.persona_engine import PersonaEngine
        return PersonaEngine()
    
    def test_greeting_generation_zhouyu(self, engine):
        from backend.services.consultation.persona_engine import PersonaConfig
        config = PersonaConfig(
            name="zhouyu",
            display_name="周瑜",
            decision_speed=80,
            risk_preference=75,
            expression_style=85,
            inquiry_depth=60,
            report_style=70,
            emotional_resonance=65,
            logic_rigor=75,
            knowledge_preference=80
        )
        greeting = engine.generate_greeting(config)
        assert "阁下" in greeting or "哈哈" in greeting
    
    def test_greeting_generation_luxun(self, engine):
        from backend.services.consultation.persona_engine import PersonaConfig
        config = PersonaConfig(
            name="luxun",
            display_name="陆逊",
            decision_speed=40,
            risk_preference=30,
            expression_style=35,
            inquiry_depth=80,
            report_style=50,
            emotional_resonance=85,
            logic_rigor=90,
            knowledge_preference=60
        )
        greeting = engine.generate_greeting(config)
        assert len(greeting) > 0
        assert isinstance(greeting, str)
    
    def test_inquiry_generation(self, engine):
        from backend.services.consultation.persona_engine import PersonaConfig
        config = PersonaConfig(
            name="zhouyu",
            display_name="周瑜",
            decision_speed=80,
            risk_preference=75,
            expression_style=85,
            inquiry_depth=60,
            report_style=70,
            emotional_resonance=65,
            logic_rigor=75,
            knowledge_preference=80
        )
        inquiry = engine.generate_inquiry(config, "city", "目标城市")
        assert len(inquiry) > 0
    
    def test_persona_blending(self, engine):
        from backend.services.consultation.persona_engine import PersonaConfig
        config1 = PersonaConfig(
            name="zhouyu",
            display_name="周瑜",
            decision_speed=80,
            risk_preference=75,
            expression_style=85,
            inquiry_depth=60,
            report_style=70,
            emotional_resonance=65,
            logic_rigor=75,
            knowledge_preference=80
        )
        config2 = PersonaConfig(
            name="luxun",
            display_name="陆逊",
            decision_speed=40,
            risk_preference=30,
            expression_style=35,
            inquiry_depth=80,
            report_style=50,
            emotional_resonance=85,
            logic_rigor=90,
            knowledge_preference=60
        )
        blended = engine.blend_personas([config1, config2], [0.7, 0.3])
        assert blended.decision_speed > 40 and blended.decision_speed < 80
        assert blended.name == "blended"


class TestInquiryGenerator:
    
    @pytest.fixture
    def generator(self):
        from backend.services.consultation.inquiry_generator import InquiryGenerator
        return InquiryGenerator()
    
    def test_inquiry_plan_generation(self, generator):
        from backend.services.consultation.problem_detector import DetectedIssue
        issues = [
            DetectedIssue(
                issue_type=IssueType.MISSING_INFO.value,
                severity="high",
                description="缺少城市",
                affected_slots=["city"],
                suggestion="询问城市",
                auto_fixable=False
            )
        ]
        plan = generator.generate_inquiry_plan(
            "session-1",
            "property_consultation",
            ["city"],
            issues,
            "zhouyu"
        )
        assert plan.total_questions > 0
        assert plan.inquiry_strategy in ["batch_inquiry", "progressive_inquiry", "sequential_inquiry"]
    
    def test_skip_response_generation(self, generator):
        response = generator.generate_skip_response("city", "zhouyu")
        assert len(response) > 0
        assert isinstance(response, str)


class TestReportTemplateEngine:
    
    @pytest.fixture
    def engine(self):
        from backend.services.consultation.report_template_engine import ReportTemplateEngine
        return ReportTemplateEngine()
    
    def test_template_retrieval(self, engine):
        template = engine.get_template("property_consultation")
        assert template is not None
        assert template.intent_type == "property_consultation"
    
    def test_title_generation(self, engine):
        title = engine.generate_report_title(
            "property_consultation",
            {"city": "深圳"},
            "zhouyu"
        )
        assert "深圳" in title or "房产" in title
    
    def test_disclaimer_generation(self, engine):
        disclaimer = engine.generate_disclaimer("property_consultation", "zhouyu")
        assert len(disclaimer) > 0


class TestReportReviewer:
    
    @pytest.fixture
    def reviewer(self):
        from backend.services.consultation.report_reviewer import ReportReviewer
        return ReportReviewer()
    
    def test_objectivity_check(self, reviewer):
        content = {
            "sections": [
                {"id": "summary", "content": "这个房子一定会升值"},
                {"id": "recommendations", "content": "建议购买"}
            ]
        }
        result = reviewer.review(content, "property_consultation")
        assert result.category_scores["objectivity"] < 1.0
    
    def test_completeness_check(self, reviewer):
        content = {
            "sections": [
                {"id": "summary", "content": "摘要"}
            ]
        }
        result = reviewer.review(content, "property_consultation")
        assert result.category_scores["completeness"] < 1.0
    
    def test_auto_fix(self, reviewer):
        content = {
            "sections": [
                {"id": "summary", "content": "这个房子一定会升值"}
            ]
        }
        issues = [i for i in reviewer._check_objectivity(content) if i.auto_fixable]
        fixed = reviewer.auto_fix(content, issues)
        text = json.dumps(fixed, ensure_ascii=False)
        assert "一定" not in text or "可能" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
