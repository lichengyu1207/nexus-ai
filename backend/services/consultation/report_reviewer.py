# -*- coding: utf-8 -*-
"""
Report Reviewer
Reviews reports for quality, objectivity, and completeness
"""
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ReviewCategory(Enum):
    OBJECTIVITY = "objectivity"
    COMPLETENESS = "completeness"
    LOGIC = "logic"
    DATA_ACCURACY = "data_accuracy"
    LANGUAGE = "language"
    STRUCTURE = "structure"


@dataclass
class ReviewIssue:
    category: str
    severity: str  # critical, major, minor
    description: str
    location: str
    suggestion: str
    auto_fixable: bool


@dataclass
class ReviewResult:
    overall_score: float
    passed: bool
    issues: List[ReviewIssue]
    category_scores: Dict[str, float]
    recommendations: List[str]


class ReportReviewer:
    def __init__(self):
        self._objectivity_rules = self._load_objectivity_rules()
        self._completeness_rules = self._load_completeness_rules()
        self._logic_rules = self._load_logic_rules()
        self._language_rules = self._load_language_rules()
    
    def _load_objectivity_rules(self) -> Dict:
        return {
            "absolute_words": {
                "words": ["一定", "必然", "绝对", "肯定", "百分之百", "必须", "肯定能"],
                "severity": "major",
                "suggestion": "建议使用更客观的表述，如'可能'、'建议'、'通常'"
            },
            "guarantee_words": {
                "words": ["保证", "承诺", "确保", "稳赚", "必涨"],
                "severity": "critical",
                "suggestion": "避免使用承诺性语言，使用风险评估替代"
            },
            "subjective_words": {
                "words": ["我觉得", "我认为", "我确信", "我保证"],
                "severity": "minor",
                "suggestion": "建议使用更客观的表述"
            }
        }
    
    def _load_completeness_rules(self) -> Dict:
        return {
            "required_sections": {
                "property_consultation": ["summary", "market_analysis", "recommendations", "disclaimer"],
                "destiny_consultation": ["summary", "destiny_chart", "recommendations", "disclaimer"],
                "investment_advice": ["summary", "investment_analysis", "risk_assessment", "recommendations"],
                "emotional_support": ["summary", "emotional_guidance", "disclaimer"],
                "general_question": ["summary", "recommendations"]
            },
            "min_content_length": {
                "summary": 50,
                "recommendations": 100
            }
        }
    
    def _load_logic_rules(self) -> Dict:
        return {
            "contradiction_patterns": [
                (r"建议买入.*但.*下跌趋势", "建议与市场趋势矛盾"),
                (r"风险很低.*高收益", "风险收益描述矛盾")
            ],
            "missing_causality": [
                "因此", "所以", "综上所述", "基于以上"
            ]
        }
    
    def _load_language_rules(self) -> Dict:
        return {
            "sensitive_words": {
                "words": ["内幕", "关系户", "走后门", "违规操作"],
                "severity": "critical"
            },
            "unprofessional_words": {
                "words": ["随便", "无所谓", "不清楚", "不知道"],
                "severity": "minor"
            }
        }
    
    def review(self, report_content: Dict, intent: str) -> ReviewResult:
        issues = []
        category_scores = {}
        
        objectivity_issues = self._check_objectivity(report_content)
        issues.extend(objectivity_issues)
        category_scores["objectivity"] = self._calculate_category_score(objectivity_issues)
        
        completeness_issues = self._check_completeness(report_content, intent)
        issues.extend(completeness_issues)
        category_scores["completeness"] = self._calculate_category_score(completeness_issues)
        
        logic_issues = self._check_logic(report_content)
        issues.extend(logic_issues)
        category_scores["logic"] = self._calculate_category_score(logic_issues)
        
        language_issues = self._check_language(report_content)
        issues.extend(language_issues)
        category_scores["language"] = self._calculate_category_score(language_issues)
        
        structure_issues = self._check_structure(report_content)
        issues.extend(structure_issues)
        category_scores["structure"] = self._calculate_category_score(structure_issues)
        
        overall_score = sum(category_scores.values()) / len(category_scores)
        
        critical_count = sum(1 for i in issues if i.severity == "critical")
        passed = critical_count == 0 and overall_score >= 0.6
        
        recommendations = self._generate_recommendations(issues)
        
        return ReviewResult(
            overall_score=overall_score,
            passed=passed,
            issues=issues,
            category_scores=category_scores,
            recommendations=recommendations
        )
    
    def _check_objectivity(self, content: Dict) -> List[ReviewIssue]:
        issues = []
        text = json.dumps(content, ensure_ascii=False)
        
        for rule_name, rule in self._objectivity_rules.items():
            for word in rule["words"]:
                if word in text:
                    pattern = re.compile(rf'.{{0,20}}{re.escape(word)}.{{0,20}}')
                    match = pattern.search(text)
                    location = match.group(0) if match else word
                    
                    issues.append(ReviewIssue(
                        category=ReviewCategory.OBJECTIVITY.value,
                        severity=rule["severity"],
                        description=f"发现绝对化/主观语言: {word}",
                        location=location,
                        suggestion=rule["suggestion"],
                        auto_fixable=rule["severity"] != "critical"
                    ))
        
        return issues
    
    def _check_completeness(self, content: Dict, intent: str) -> List[ReviewIssue]:
        issues = []
        sections = content.get("sections", [])
        section_ids = [s.get("id") for s in sections]
        
        required = self._completeness_rules["required_sections"].get(intent, [])
        
        for section_id in required:
            if section_id not in section_ids:
                issues.append(ReviewIssue(
                    category=ReviewCategory.COMPLETENESS.value,
                    severity="major",
                    description=f"缺少必要章节: {section_id}",
                    location="report_structure",
                    suggestion=f"添加{section_id}章节",
                    auto_fixable=False
                ))
        
        min_lengths = self._completeness_rules["min_content_length"]
        for section in sections:
            section_id = section.get("id", "")
            if section_id in min_lengths:
                content_length = len(section.get("content", ""))
                if content_length < min_lengths[section_id]:
                    issues.append(ReviewIssue(
                        category=ReviewCategory.COMPLETENESS.value,
                        severity="minor",
                        description=f"{section_id}章节内容过短",
                        location=section_id,
                        suggestion="补充更多内容",
                        auto_fixable=False
                    ))
        
        return issues
    
    def _check_logic(self, content: Dict) -> List[ReviewIssue]:
        issues = []
        text = json.dumps(content, ensure_ascii=False)
        
        for pattern, description in self._logic_rules["contradiction_patterns"]:
            if re.search(pattern, text):
                issues.append(ReviewIssue(
                    category=ReviewCategory.LOGIC.value,
                    severity="major",
                    description=f"逻辑矛盾: {description}",
                    location="content",
                    suggestion="检查并修正矛盾内容",
                    auto_fixable=False
                ))
        
        return issues
    
    def _check_language(self, content: Dict) -> List[ReviewIssue]:
        issues = []
        text = json.dumps(content, ensure_ascii=False)
        
        sensitive = self._language_rules["sensitive_words"]
        for word in sensitive["words"]:
            if word in text:
                issues.append(ReviewIssue(
                    category=ReviewCategory.LANGUAGE.value,
                    severity=sensitive["severity"],
                    description=f"发现敏感词汇: {word}",
                    location=word,
                    suggestion="移除或替换敏感词汇",
                    auto_fixable=True
                ))
        
        unprofessional = self._language_rules["unprofessional_words"]
        for word in unprofessional["words"]:
            if word in text:
                issues.append(ReviewIssue(
                    category=ReviewCategory.LANGUAGE.value,
                    severity=unprofessional["severity"],
                    description=f"发现不专业表述: {word}",
                    location=word,
                    suggestion="使用更专业的表述",
                    auto_fixable=True
                ))
        
        return issues
    
    def _check_structure(self, content: Dict) -> List[ReviewIssue]:
        issues = []
        sections = content.get("sections", [])
        
        if not sections:
            issues.append(ReviewIssue(
                category=ReviewCategory.STRUCTURE.value,
                severity="critical",
                description="报告缺少章节结构",
                location="report_structure",
                suggestion="添加章节结构",
                auto_fixable=False
            ))
            return issues
        
        orders = [s.get("order", 0) for s in sections]
        if orders != sorted(orders):
            issues.append(ReviewIssue(
                category=ReviewCategory.STRUCTURE.value,
                severity="minor",
                description="章节顺序不正确",
                location="section_order",
                suggestion="调整章节顺序",
                auto_fixable=True
            ))
        
        return issues
    
    def _calculate_category_score(self, issues: List[ReviewIssue]) -> float:
        if not issues:
            return 1.0
        
        score = 1.0
        for issue in issues:
            if issue.severity == "critical":
                score -= 0.3
            elif issue.severity == "major":
                score -= 0.15
            else:
                score -= 0.05
        
        return max(score, 0)
    
    def _generate_recommendations(self, issues: List[ReviewIssue]) -> List[str]:
        recommendations = []
        
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append("报告存在严重问题，建议重新生成")
        
        major_issues = [i for i in issues if i.severity == "major"]
        if major_issues:
            recommendations.append(f"发现{len(major_issues)}个主要问题，建议修正后再发布")
        
        auto_fixable = [i for i in issues if i.auto_fixable]
        if auto_fixable:
            recommendations.append(f"有{len(auto_fixable)}个问题可自动修复")
        
        if not issues:
            recommendations.append("报告质量良好，可以发布")
        
        return recommendations
    
    def auto_fix(self, content: Dict, issues: List[ReviewIssue]) -> Dict:
        fixed_content = json.loads(json.dumps(content))
        
        for issue in issues:
            if not issue.auto_fixable:
                continue
            
            if issue.category == ReviewCategory.OBJECTIVITY.value:
                replacements = {
                    "一定": "可能",
                    "必然": "很有可能",
                    "绝对": "比较",
                    "肯定": "应该",
                    "百分之百": "大概率",
                    "保证": "尽力确保",
                    "承诺": "建议"
                }
                text = json.dumps(fixed_content, ensure_ascii=False)
                for old, new in replacements.items():
                    text = text.replace(old, new)
                fixed_content = json.loads(text)
            
            elif issue.category == ReviewCategory.LANGUAGE.value:
                sensitive_replacements = {
                    "内幕": "内部信息",
                    "关系户": "优先客户",
                    "走后门": "特殊渠道"
                }
                text = json.dumps(fixed_content, ensure_ascii=False)
                for old, new in sensitive_replacements.items():
                    text = text.replace(old, new)
                fixed_content = json.loads(text)
        
        return fixed_content


report_reviewer = ReportReviewer()


def get_report_reviewer() -> ReportReviewer:
    return report_reviewer
