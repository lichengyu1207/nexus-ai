# -*- coding: utf-8 -*-
"""
Problem Detector
Detects issues in user input: missing info, contradictions, hidden needs
"""
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class IssueType(Enum):
    MISSING_INFO = "missing_info"
    CONTRADICTION = "contradiction"
    HIDDEN_NEED = "hidden_need"
    EMOTION_ABNORMAL = "emotion_abnormal"
    UNCLEAR_INTENT = "unclear_intent"
    BUDGET_MISMATCH = "budget_mismatch"
    LOCATION_CONFLICT = "location_conflict"
    HIDDEN_NEED_DETECTED = "hidden_need_detected"


@dataclass
class DetectedIssue:
    issue_type: str
    severity: str  # low, medium, high
    description: str
    affected_slots: List[str]
    suggestion: str
    auto_fixable: bool
    context: Dict = field(default_factory=dict)


@dataclass
class ProblemAnalysisResult:
    has_issues: bool
    issues: List[DetectedIssue]
    overall_severity: str
    recommended_action: str
    follow_up_questions: List[str]


class ProblemDetector:
    def __init__(self):
        self._contradiction_patterns = self._load_contradiction_patterns()
        self._hidden_need_indicators = self._load_hidden_need_indicators()
        self._budget_ranges = self._load_budget_ranges()
    
    def _load_contradiction_patterns(self) -> List[Dict]:
        return [
            {
                "pattern": r"预算.{0,10}(\d+).{0,10}(别墅|豪宅|大平层)",
                "check": lambda m: int(m.group(1)) < 500,
                "issue_type": IssueType.BUDGET_MISMATCH,
                "message": "预算与房产类型不匹配"
            },
            {
                "pattern": r"(\d+)平.{0,10}预算.{0,10}(\d+)",
                "check": lambda m: int(m.group(2)) / int(m.group(1)) < 1,
                "issue_type": IssueType.BUDGET_MISMATCH,
                "message": "面积与预算比例异常"
            }
        ]
    
    def _load_hidden_need_indicators(self) -> Dict[str, List[str]]:
        return {
            "investment": ["升值", "投资回报", "租金", "收益", "理财"],
            "education": ["学区", "学校", "教育", "孩子上学", "名校"],
            "retirement": ["养老", "退休", "安静", "环境好"],
            "upgrade": ["改善", "换房", "升级", "大一点"],
            "first_home": ["首套", "刚需", "结婚", "安家"]
        }
    
    def _load_budget_ranges(self) -> Dict[str, Dict]:
        return {
            "一线城市": {"low": 300, "medium": 500, "high": 1000},
            "二线城市": {"low": 150, "medium": 300, "high": 500},
            "三四线城市": {"low": 80, "medium": 150, "high": 300}
        }
    
    def analyze(
        self, 
        text: str, 
        intent: str, 
        slots: Dict, 
        context: Dict = None
    ) -> ProblemAnalysisResult:
        issues = []
        
        missing_info = self._check_missing_info(intent, slots)
        issues.extend(missing_info)
        
        contradictions = self._check_contradictions(text, slots)
        issues.extend(contradictions)
        
        hidden_needs = self._detect_hidden_needs(text)
        issues.extend(hidden_needs)
        
        if context:
            context_issues = self._check_context_consistency(text, slots, context)
            issues.extend(context_issues)
        
        has_issues = len(issues) > 0
        overall_severity = self._calculate_overall_severity(issues)
        recommended_action = self._get_recommended_action(issues)
        follow_up_questions = self._generate_follow_up_questions(issues)
        
        return ProblemAnalysisResult(
            has_issues=has_issues,
            issues=issues,
            overall_severity=overall_severity,
            recommended_action=recommended_action,
            follow_up_questions=follow_up_questions
        )
    
    def _check_missing_info(self, intent: str, slots: Dict) -> List[DetectedIssue]:
        issues = []
        
        required_slots = {
            "property_consultation": ["city", "budget"],
            "destiny_consultation": ["birth_date", "gender"],
            "investment_advice": ["investment_amount"]
        }
        
        intent_required = required_slots.get(intent, [])
        
        for slot in intent_required:
            if slot not in slots or not slots[slot]:
                issues.append(DetectedIssue(
                    issue_type=IssueType.MISSING_INFO.value,
                    severity="high",
                    description=f"缺少关键信息: {slot}",
                    affected_slots=[slot],
                    suggestion=f"请询问用户的{slot}",
                    auto_fixable=False
                ))
        
        return issues
    
    def _check_contradictions(self, text: str, slots: Dict) -> List[DetectedIssue]:
        issues = []
        
        for pattern_config in self._contradiction_patterns:
            match = re.search(pattern_config["pattern"], text)
            if match and pattern_config["check"](match):
                issues.append(DetectedIssue(
                    issue_type=pattern_config["issue_type"].value,
                    severity="medium",
                    description=pattern_config["message"],
                    affected_slots=["budget", "property_type"],
                    suggestion="指出预算与需求的不匹配，提供调整建议",
                    auto_fixable=True,
                    context={"matched_text": match.group(0)}
                ))
        
        city = slots.get("city", "")
        budget = slots.get("budget", 0)
        
        if city and budget:
            city_tier = self._get_city_tier(city)
            budget_range = self._budget_ranges.get(city_tier, {})
            
            if budget_range:
                if budget < budget_range.get("low", 0) * 10000:
                    issues.append(DetectedIssue(
                        issue_type=IssueType.BUDGET_MISMATCH.value,
                        severity="medium",
                        description=f"{city}的购房预算可能偏低",
                        affected_slots=["budget"],
                        suggestion=f"建议提醒用户{city}的购房门槛",
                        auto_fixable=True
                    ))
        
        return issues
    
    def _detect_hidden_needs(self, text: str) -> List[DetectedIssue]:
        issues = []
        
        for need_type, indicators in self._hidden_need_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    issues.append(DetectedIssue(
                        issue_type=IssueType.HIDDEN_NEED_DETECTED.value,
                        severity="low",
                        description=f"检测到潜在需求: {need_type}",
                        affected_slots=[],
                        suggestion=f"可以进一步了解用户的{need_type}需求",
                        auto_fixable=False,
                        context={"need_type": need_type, "indicator": indicator}
                    ))
                    break
        
        return issues
    
    def _check_context_consistency(
        self, 
        text: str, 
        slots: Dict, 
        context: Dict
    ) -> List[DetectedIssue]:
        issues = []
        
        previous_slots = context.get("slots", {})
        
        if "city" in previous_slots and "city" in slots:
            if previous_slots["city"] != slots["city"]:
                issues.append(DetectedIssue(
                    issue_type=IssueType.LOCATION_CONFLICT.value,
                    severity="low",
                    description=f"城市偏好从{previous_slots['city']}变为{slots['city']}",
                    affected_slots=["city"],
                    suggestion="确认用户是否改变了城市偏好",
                    auto_fixable=False
                ))
        
        return issues
    
    def _get_city_tier(self, city: str) -> str:
        tier1 = ["北京", "上海", "广州", "深圳"]
        tier2 = ["杭州", "南京", "苏州", "成都", "武汉", "西安", "重庆", "天津"]
        
        if city in tier1:
            return "一线城市"
        elif city in tier2:
            return "二线城市"
        else:
            return "三四线城市"
    
    def _calculate_overall_severity(self, issues: List[DetectedIssue]) -> str:
        if not issues:
            return "none"
        
        severity_scores = {"high": 3, "medium": 2, "low": 1}
        total_score = sum(severity_scores.get(i.severity, 0) for i in issues)
        
        if total_score >= 5:
            return "high"
        elif total_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _get_recommended_action(self, issues: List[DetectedIssue]) -> str:
        if not issues:
            return "continue"
        
        high_severity = [i for i in issues if i.severity == "high"]
        if high_severity:
            return "ask_missing_info"
        
        contradictions = [i for i in issues if i.issue_type == IssueType.CONTRADICTION.value]
        if contradictions:
            return "clarify_contradiction"
        
        hidden_needs = [i for i in issues if i.issue_type == IssueType.HIDDEN_NEED_DETECTED.value]
        if hidden_needs:
            return "explore_hidden_needs"
        
        return "continue_with_caution"
    
    def _generate_follow_up_questions(self, issues: List[DetectedIssue]) -> List[str]:
        questions = []
        
        for issue in issues:
            if issue.issue_type == IssueType.MISSING_INFO.value:
                slot_names = {
                    "city": "您想在哪个城市购房？",
                    "budget": "您的购房预算大概是多少？",
                    "birth_date": "请问您的出生日期是？",
                    "gender": "请问您的性别是？",
                    "investment_amount": "您计划投资多少资金？"
                }
                for slot in issue.affected_slots:
                    if slot in slot_names:
                        questions.append(slot_names[slot])
            
            elif issue.issue_type == IssueType.BUDGET_MISMATCH.value:
                questions.append("我注意到您的预算可能偏低，是否需要调整预算或考虑其他区域？")
            
            elif issue.issue_type == IssueType.HIDDEN_NEED.value:
                need_type = issue.context.get("need_type", "")
                need_questions = {
                    "investment": "您对投资回报有什么期望吗？",
                    "education": "孩子的教育需求是您考虑的重要因素吗？",
                    "retirement": "您是在为养老做准备吗？",
                    "upgrade": "您是想改善现有的居住条件吗？",
                    "first_home": "这是您的首套房吗？"
                }
                if need_type in need_questions:
                    questions.append(need_questions[need_type])
        
        return questions


problem_detector = ProblemDetector()


def get_problem_detector() -> ProblemDetector:
    return problem_detector
