# -*- coding: utf-8 -*-
"""
Integration tests for consultation module
"""
import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, patch,from backend.services.consultation import (
    ContextManager, get_context_manager,
    ConsultationContext
)
from backend.services.consultation.intent_analyzer import (
    IntentAnalyzer, get_intent_analyzer
)
from backend.services.consultation.emotion_detector import (
    EmotionDetector, get_emotion_detector, EmotionType
)
from backend.services.consultation.persona_engine import (
    PersonaEngine, get_persona_engine
)
from backend.services.consultation.problem_detector import (
    ProblemDetector, get_problem_detector
)
from backend.services.consultation.inquiry_generator import (
    InquiryGenerator, get_inquiry_generator
)


class TestConsultationFlow:
    
    @pytest.fixture
    def setup_services(self):
        self.context_manager = ContextManager()
        self.intent_analyzer = get_intent_analyzer()
        self.emotion_detector = get_emotion_detector()
        self.persona_engine = get_persona_engine()
        self.problem_detector = get_problem_detector()
        self.inquiry_generator = get_inquiry_generator()
    
    @pytest.mark.asyncio
    async def test_full_consultation_flow(self, setup_services):
        session_id = str(uuid.uuid4())
        user_id = "test-user-001"
        
        context = await setup_services.context_manager.create_context(
            session_id=session_id,
            user_id=user_id,
            gene_name="zhouyu"
        )
        
        assert context.session_id == session_id
        assert context.gene_name == "zhouyu"
        
        user_input = "我想在深圳买房，预算300万左右"
        
        intent_result = setup_services.intent_analyzer.analyze(user_input)
        
        assert intent_result.intent == "property_consultation"
        assert "city" in intent_result.slots
        
        emotion_result = setup_services.emotion_detector.detect(user_input)
        
        assert emotion_result.emotion in [EmotionType.NEUTRAL.value, EmotionType.HOPEFUL.value]
        
        problem_result = setup_services.problem_detector.analyze(
            user_input,
            intent_result.intent,
            intent_result.slots
        )
        
        await setup_services.context_manager.update_intent(
            session_id, intent_result.intent, intent_result.confidence
        )
        await setup_services.context_manager.update_slots(
            session_id, intent_result.slots
        )
        
        updated_context = await setup_services.context_manager.get_context(session_id)
        
        assert updated_context.intent == "property_consultation"
        assert "city" in updated_context.slots
    
    @pytest.mark.asyncio
    async def test_persona_switch_flow(self, setup_services):
        session_id = str(uuid.uuid4())
        
        context = await setup_services.context_manager.create_context(
            session_id=session_id,
            user_id="test-user",
            gene_name="zhouyu"
        )
        
        await setup_services.context_manager.switch_gene(
            session_id, None, "luxun"
        )
        
        updated = await setup_services.context_manager.get_context(session_id)
        assert updated.gene_name == "luxun"
    
    @pytest.mark.asyncio
    async def test_emotion_triggered_flow(self, setup_services):
        session_id = str(uuid.uuid4())
        
        context = await setup_services.context_manager.create_context(
            session_id=session_id,
            user_id="test-user",
            gene_name="zhouyu"
        )
        
        anxious_input = "我很焦虑，压力很大，不知道该怎么办"
        
        emotion_result = setup_services.emotion_detector.detect(anxious_input)
        
        assert emotion_result.emotion == EmotionType.ANXIOUS.value
        assert emotion_result.score > 0.3
        
        should_support = setup_services.emotion_detector.should_provide_support(emotion_result)
        assert should_support
        
        support_message = setup_services.emotion_detector.get_support_message(
            emotion_result.emotion, "zhouyu"
        )
        assert len(support_message) > 0


class TestInquiryFlow:
    
    @pytest.fixture
    def setup_inquiry(self):
        self.inquiry_generator = get_inquiry_generator()
        self.problem_detector = get_problem_detector()
    
    def test_inquiry_plan_generation(self, setup_inquiry):
        missing_slots = ["city", "budget"]
        
        plan = setup_inquiry.inquiry_generator.generate_inquiry_plan(
            session_id="test-session",
            intent="property_consultation",
            missing_slots=missing_slots,
            detected_issues=[],
            persona_name="zhouyu"
        )
        
        assert plan.total_questions == 2
        assert plan.inquiry_strategy in ["batch_inquiry", "progressive_inquiry", "sequential_inquiry"]
    
    def test_question_generation_zhouyu(self, setup_inquiry):
        question = setup_inquiry.inquiry_generator._generate_question("city", "zhouyu")
        
        assert question is not None
        assert "阁下" in question.question or "敢问" in question.question
    
    def test_question_generation_luxun(self, setup_inquiry):
        question = setup_inquiry.inquiry_generator._generate_question("city", "luxun")
        
        assert question is not None
        assert "您" in question.question or "请问" in question.question
    
    def test_skip_response(self, setup_inquiry):
        response = setup_inquiry.inquiry_generator.generate_skip_response("city", "zhouyu")
        
        assert len(response) > 0


class TestReportGeneration:
    
    @pytest.fixture
    def setup_report(self):
        from backend.services.consultation.report_generator import ReportGenerator
        from backend.services.consultation.report_template_engine import get_report_template_engine
        
        self.template_engine = get_report_template_engine()
        self.report_generator = ReportGenerator(db=None)
    
    def test_template_selection(self, setup_report):
        template = setup_report.template_engine.get_template("property_consultation")
        
        assert template is not None
        assert template.intent_type == "property_consultation"
        assert len(template.sections) >= 3
    
    def test_title_generation(self, setup_report):
        title = setup_report.template_engine.generate_report_title(
            "property_consultation",
            {"city": "深圳"},
            "zhouyu"
        )
        
        assert "深圳" in title or "房产" in title
    
    def test_disclaimer_generation(self, setup_report):
        disclaimer = setup_report.template_engine.generate_disclaimer(
            "property_consultation", "zhouyu"
        )
        
        assert len(disclaimer) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
