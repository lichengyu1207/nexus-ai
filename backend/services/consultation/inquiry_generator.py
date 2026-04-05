# -*- coding: utf-8 -*-
"""
Inquiry Generator
Generates proactive questions based on missing information and context
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import time

from backend.services.consultation.intent_analyzer import (
    IntentAnalyzer, get_intent_analyzer, SlotDefinition
)
from backend.services.consultation.persona_engine import (
    PersonaEngine, PersonaConfig, get_persona_engine
)
from backend.services.consultation.problem_detector import (
    ProblemDetector, DetectedIssue, get_problem_detector, IssueType
)

logger = logging.getLogger(__name__)


class InquiryPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class InquiryQuestion:
    slot_name: str
    question: str
    priority: int
    persona_style: str
    alternatives: List[str] = field(default_factory=list)
    context_hint: str = ""


@dataclass
class InquiryPlan:
    session_id: str
    questions: List[InquiryQuestion]
    total_questions: int
    estimated_rounds: int
    inquiry_strategy: str


class InquiryGenerator:
    def __init__(self):
        self.intent_analyzer = get_intent_analyzer()
        self.persona_engine = get_persona_engine()
        self.problem_detector = get_problem_detector()
        
        self._question_templates = self._load_question_templates()
        self._slot_priorities = self._load_slot_priorities()
    
    def _load_question_templates(self) -> Dict[str, Dict]:
        return {
            "city": {
                "zhouyu": [
                    "阁下欲在何处置业？",
                    "敢问阁下心仪哪座城市？",
                    "阁下欲在何方安家？"
                ],
                "luxun": [
                    "请问您想在哪个城市购房？",
                    "您有偏好的城市吗？",
                    "您目前关注的是哪个城市？"
                ]
            },
            "budget": {
                "zhouyu": [
                    "阁下预算几何？",
                    "敢问阁下准备投入多少银两？",
                    "阁下财力如何？"
                ],
                "luxun": [
                    "请问您的购房预算大概是多少？",
                    "您计划投入多少资金？",
                    "您的预算范围是多少？"
                ]
            },
            "purpose": {
                "zhouyu": [
                    "阁下购房是为了自住还是投资？",
                    "敢问阁下购房意图为何？",
                    "阁下是自用还是投资？"
                ],
                "luxun": [
                    "您购房是自住还是投资？",
                    "您的主要购房目的是什么？",
                    "您是为自己住还是投资？"
                ]
            },
            "rooms": {
                "zhouyu": [
                    "阁下需要几室之宅？",
                    "敢问阁下需要几间房？",
                    "阁下欲购几室？"
                ],
                "luxun": [
                    "您需要几室的房子？",
                    "您对房间数量有要求吗？",
                    "您希望是几室几厅？"
                ]
            },
            "area_preference": {
                "zhouyu": [
                    "阁下有偏好的区域吗？",
                    "敢问阁下心仪哪个地段？",
                    "阁下对地段有何要求？"
                ],
                "luxun": [
                    "您有偏好的区域吗？",
                    "您对哪个地段比较感兴趣？",
                    "您有考虑的具体区域吗？"
                ]
            },
            "birth_date": {
                "zhouyu": [
                    "敢问阁下生辰八字？",
                    "阁下生于何年何月何日？",
                    "请赐阁下出生日期"
                ],
                "luxun": [
                    "请问您的出生日期是？",
                    "您是哪年哪月哪日出生的？",
                    "能告诉我您的出生日期吗？"
                ]
            },
            "gender": {
                "zhouyu": [
                    "阁下是男是女？",
                    "敢问阁下性别？"
                ],
                "luxun": [
                    "请问您的性别是？",
                    "您是先生还是女士？"
                ]
            }
        }
    
    def _load_slot_priorities(self) -> Dict[str, int]:
        return {
            "city": InquiryPriority.CRITICAL.value,
            "budget": InquiryPriority.CRITICAL.value,
            "birth_date": InquiryPriority.CRITICAL.value,
            "gender": InquiryPriority.HIGH.value,
            "purpose": InquiryPriority.HIGH.value,
            "rooms": InquiryPriority.MEDIUM.value,
            "area_preference": InquiryPriority.MEDIUM.value
        }
    
    def generate_inquiry_plan(
        self,
        session_id: str,
        intent: str,
        missing_slots: List[str],
        detected_issues: List[DetectedIssue],
        persona_name: str = "zhouyu",
        context: Dict = None
    ) -> InquiryPlan:
        questions = []
        
        for slot in missing_slots:
            question = self._generate_question(slot, persona_name)
            if question:
                questions.append(question)
        
        for issue in detected_issues:
            if issue.issue_type == IssueType.BUDGET_MISMATCH.value:
                question = self._generate_budget_clarification(issue, persona_name)
                if question:
                    questions.append(question)
            elif issue.issue_type == IssueType.HIDDEN_NEED.value:
                question = self._generate_need_exploration(issue, persona_name)
                if question:
                    questions.append(question)
        
        questions.sort(key=lambda q: q.priority)
        
        strategy = self._determine_strategy(questions, context)
        estimated_rounds = min(len(questions), 3)
        
        return InquiryPlan(
            session_id=session_id,
            questions=questions,
            total_questions=len(questions),
            estimated_rounds=estimated_rounds,
            inquiry_strategy=strategy
        )
    
    def _generate_question(
        self, 
        slot_name: str, 
        persona_name: str
    ) -> Optional[InquiryQuestion]:
        templates = self._question_templates.get(slot_name, {})
        persona_templates = templates.get(persona_name, templates.get("luxun", []))
        
        if not persona_templates:
            return None
        
        question = random.choice(persona_templates)
        alternatives = [t for t in persona_templates if t != question]
        
        priority = self._slot_priorities.get(slot_name, InquiryPriority.MEDIUM.value)
        
        return InquiryQuestion(
            slot_name=slot_name,
            question=question,
            priority=priority,
            persona_style=persona_name,
            alternatives=alternatives
        )
    
    def _generate_budget_clarification(
        self, 
        issue: DetectedIssue, 
        persona_name: str
    ) -> Optional[InquiryQuestion]:
        if persona_name == "zhouyu":
            question = "阁下，此预算恐难如愿。可否调整预算，或另寻他处？"
        else:
            question = "我注意到您的预算可能偏低。您是否考虑调整预算，或者我可以为您推荐其他区域？"
        
        return InquiryQuestion(
            slot_name="budget_clarification",
            question=question,
            priority=InquiryPriority.HIGH.value,
            persona_style=persona_name,
            context_hint=issue.description
        )
    
    def _generate_need_exploration(
        self, 
        issue: DetectedIssue, 
        persona_name: str
    ) -> Optional[InquiryQuestion]:
        need_type = issue.context.get("need_type", "")
        
        need_questions = {
            "investment": {
                "zhouyu": "阁下可是为投资而来？若求收益，我有良策！",
                "luxun": "您是否在考虑房产投资？我可以为您分析投资回报。"
            },
            "education": {
                "zhouyu": "阁下可是为子女教育操心？学区房之事，我略知一二！",
                "luxun": "孩子的教育是您考虑的重要因素吗？我可以为您分析学区情况。"
            },
            "retirement": {
                "zhouyu": "阁下可是为养老打算？宜居之地，我有推荐！",
                "luxun": "您是在为养老做准备吗？我可以为您推荐适合养老的区域。"
            }
        }
        
        question = need_questions.get(need_type, {}).get(persona_name)
        if not question:
            return None
        
        return InquiryQuestion(
            slot_name=f"need_{need_type}",
            question=question,
            priority=InquiryPriority.LOW.value,
            persona_style=persona_name,
            context_hint=f"检测到潜在需求: {need_type}"
        )
    
    def _determine_strategy(
        self, 
        questions: List[InquiryQuestion], 
        context: Dict
    ) -> str:
        if not questions:
            return "no_inquiry_needed"
        
        critical_count = sum(1 for q in questions if q.priority == InquiryPriority.CRITICAL.value)
        
        if critical_count >= 2:
            return "batch_inquiry"
        elif len(questions) > 3:
            return "progressive_inquiry"
        else:
            return "sequential_inquiry"
    
    def get_next_question(
        self, 
        plan: InquiryPlan, 
        asked_slots: List[str]
    ) -> Optional[InquiryQuestion]:
        for question in plan.questions:
            if question.slot_name not in asked_slots:
                return question
        return None
    
    def generate_skip_response(
        self, 
        slot_name: str, 
        persona_name: str
    ) -> str:
        if persona_name == "zhouyu":
            responses = [
                "既如此，阁下且随我来！",
                "好！那我们继续！",
                "明白！且看下一步！"
            ]
        else:
            responses = [
                "好的，那我们继续。",
                "没问题，我们跳过这个。",
                "了解，让我们继续下一步。"
            ]
        
        return random.choice(responses)
    
    def record_inquiry(
        self,
        session_id: str,
        slot_name: str,
        question: str,
        user_response: str = None,
        is_answered: bool = False,
        is_skipped: bool = False
    ) -> Dict:
        return {
            "session_id": session_id,
            "slot_name": slot_name,
            "question": question,
            "user_response": user_response,
            "is_answered": is_answered,
            "is_skipped": is_skipped,
            "timestamp": time.time()
        }


inquiry_generator = InquiryGenerator()


def get_inquiry_generator() -> InquiryGenerator:
    return inquiry_generator
