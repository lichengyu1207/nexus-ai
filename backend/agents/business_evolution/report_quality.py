"""
报告质量评估器
Report Quality Evaluator - 确保输出高质量分析报告

工部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import json
import re


class QualityDimension(Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    TIMELINESS = "timeliness"
    READABILITY = "readability"
    CONSISTENCY = "consistency"
    RELEVANCE = "relevance"
    ACTIONABILITY = "actionability"


class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


@dataclass
class QualityScore:
    dimension: QualityDimension
    score: float
    max_score: float = 100.0
    details: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    report_id: str
    target_report_id: str
    overall_score: float
    quality_level: QualityLevel
    dimension_scores: List[QualityScore]
    passed: bool
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    evaluator_version: str = "1.0.0"


class AccuracyChecker:
    def __init__(self):
        self.data_source_reliability: Dict[str, float] = {}
        self.validation_rules: List[Dict] = []

    def check(self, report_data: Dict[str, Any]) -> QualityScore:
        issues = []
        score = 100.0

        data_sources = report_data.get("data_sources", [])
        for source in data_sources:
            reliability = self.data_source_reliability.get(source, 0.8)
            if reliability < 0.7:
                issues.append(f"数据源 {source} 可靠性较低")
                score -= 10

        numeric_values = self._extract_numeric_values(report_data)
        for key, value in numeric_values.items():
            if value is not None:
                if value < 0:
                    issues.append(f"{key} 存在负值: {value}")
                    score -= 5

        for rule in self.validation_rules:
            if not self._apply_rule(rule, report_data):
                issues.append(f"规则验证失败: {rule.get('name', 'unknown')}")
                score -= rule.get("penalty", 5)

        return QualityScore(
            dimension=QualityDimension.ACCURACY,
            score=max(0, score),
            details=issues,
            suggestions=self._generate_suggestions(issues),
        )

    def _extract_numeric_values(self, data: Dict) -> Dict[str, float]:
        numeric = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                numeric[key] = value
            elif isinstance(value, dict):
                numeric.update(self._extract_numeric_values(value))
        return numeric

    def _apply_rule(self, rule: Dict, data: Dict) -> bool:
        return True

    def _generate_suggestions(self, issues: List[str]) -> List[str]:
        suggestions = []
        for issue in issues:
            if "可靠性" in issue:
                suggestions.append("建议使用更可靠的数据源进行验证")
            elif "负值" in issue:
                suggestions.append("检查数据计算逻辑，确保数值正确")
        return suggestions


class CompletenessChecker:
    REQUIRED_FIELDS = {
        "community_analysis": [
            "community_name",
            "avg_price",
            "price_trend",
            "location",
            "facilities",
        ],
        "price_analysis": [
            "current_price",
            "historical_prices",
            "price_change_rate",
        ],
        "investment_analysis": [
            "roi",
            "rental_yield",
            "appreciation_potential",
        ],
    }

    def __init__(self):
        self.custom_required_fields: Dict[str, List[str]] = {}

    def check(
        self, report_data: Dict[str, Any], report_type: str = "community_analysis"
    ) -> QualityScore:
        issues = []
        missing_fields = []

        required = self.REQUIRED_FIELDS.get(report_type, [])
        required.extend(self.custom_required_fields.get(report_type, []))

        for field in required:
            if field not in report_data or report_data.get(field) is None:
                missing_fields.append(field)

        if missing_fields:
            issues.append(f"缺失字段: {', '.join(missing_fields)}")

        coverage = (len(required) - len(missing_fields)) / len(required) * 100 if required else 100

        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=coverage,
            details=issues,
            suggestions=["补充缺失的字段数据"] if missing_fields else [],
        )


class TimelinessChecker:
    def __init__(self):
        self.freshness_thresholds: Dict[str, int] = {
            "price_data": 7,
            "market_trend": 30,
            "policy_info": 90,
            "community_info": 180,
        }

    def check(self, report_data: Dict[str, Any]) -> QualityScore:
        issues = []
        score = 100.0

        data_timestamps = report_data.get("data_timestamps", {})
        now = datetime.utcnow()

        for data_type, threshold_days in self.freshness_thresholds.items():
            timestamp_str = data_timestamps.get(data_type)
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age_days = (now - timestamp).days

                    if age_days > threshold_days:
                        issues.append(f"{data_type} 数据已过期 {age_days} 天（阈值: {threshold_days}天）")
                        score -= min(20, (age_days - threshold_days) * 2)
                except ValueError:
                    issues.append(f"{data_type} 时间戳格式错误")

        return QualityScore(
            dimension=QualityDimension.TIMELINESS,
            score=max(0, score),
            details=issues,
            suggestions=["更新过期数据"] if issues else [],
        )


class ReadabilityChecker:
    def __init__(self):
        self.max_sentence_length = 100
        self.max_paragraph_length = 500

    def check(self, report_content: str) -> QualityScore:
        issues = []
        score = 100.0

        sentences = re.split(r"[。！？.!?]", report_content)
        long_sentences = [s for s in sentences if len(s) > self.max_sentence_length]

        if long_sentences:
            issues.append(f"发现 {len(long_sentences)} 个过长句子")
            score -= len(long_sentences) * 5

        paragraphs = report_content.split("\n\n")
        long_paragraphs = [p for p in paragraphs if len(p) > self.max_paragraph_length]

        if long_paragraphs:
            issues.append(f"发现 {len(long_paragraphs)} 个过长段落")
            score -= len(long_paragraphs) * 3

        avg_sentence_length = (
            sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        )

        if avg_sentence_length > 50:
            issues.append(f"平均句长 {avg_sentence_length:.1f} 字，建议控制在30字以内")

        return QualityScore(
            dimension=QualityDimension.READABILITY,
            score=max(0, score),
            details=issues,
            suggestions=["简化长句，分段处理长段落"] if issues else [],
        )


class ConsistencyChecker:
    def __init__(self):
        self.consistency_rules: List[Dict] = []

    def check(self, report_data: Dict[str, Any]) -> QualityScore:
        issues = []
        score = 100.0

        numeric_fields = self._extract_numeric_pairs(report_data)

        for field1, value1 in numeric_fields:
            for field2, value2 in numeric_fields:
                if field1 != field2 and self._should_be_consistent(field1, field2):
                    if abs(value1 - value2) / max(abs(value1), abs(value2), 1) > 0.1:
                        issues.append(f"{field1}({value1}) 与 {field2}({value2}) 不一致")

        for rule in self.consistency_rules:
            if not self._apply_consistency_rule(rule, report_data):
                issues.append(f"一致性规则违反: {rule.get('description', '')}")
                score -= 10

        return QualityScore(
            dimension=QualityDimension.CONSISTENCY,
            score=max(0, score),
            details=issues,
            suggestions=["检查数据计算逻辑，确保相关数据一致"] if issues else [],
        )

    def _extract_numeric_pairs(self, data: Dict) -> List[tuple]:
        pairs = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                pairs.append((key, value))
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)):
                        pairs.append((f"{key}.{sub_key}", sub_value))
        return pairs

    def _should_be_consistent(self, field1: str, field2: str) -> bool:
        consistent_groups = [
            {"avg_price", "average_price", "mean_price"},
            {"total_area", "area_total"},
        ]

        for group in consistent_groups:
            if field1 in group and field2 in group:
                return True
        return False

    def _apply_consistency_rule(self, rule: Dict, data: Dict) -> bool:
        return True


class ReportQualityEvaluator:
    def __init__(self, agent_id: str = "quality_evaluator_001"):
        self.agent_id = agent_id
        self.accuracy_checker = AccuracyChecker()
        self.completeness_checker = CompletenessChecker()
        self.timeliness_checker = TimelinessChecker()
        self.readability_checker = ReadabilityChecker()
        self.consistency_checker = ConsistencyChecker()

        self.quality_threshold = 70.0
        self.evaluation_history: List[QualityReport] = []

    async def evaluate(
        self,
        report_id: str,
        report_data: Dict[str, Any],
        report_content: str = "",
        report_type: str = "community_analysis",
    ) -> QualityReport:
        dimension_scores = []

        dimension_scores.append(self.accuracy_checker.check(report_data))

        dimension_scores.append(
            self.completeness_checker.check(report_data, report_type)
        )

        dimension_scores.append(self.timeliness_checker.check(report_data))

        if report_content:
            dimension_scores.append(self.readability_checker.check(report_content))

        dimension_scores.append(self.consistency_checker.check(report_data))

        relevance_score = self._check_relevance(report_data)
        dimension_scores.append(relevance_score)

        actionability_score = self._check_actionability(report_data)
        dimension_scores.append(actionability_score)

        overall_score = sum(s.score for s in dimension_scores) / len(dimension_scores)

        quality_level = self._determine_quality_level(overall_score)

        issues = self._collect_issues(dimension_scores)

        recommendations = self._generate_recommendations(dimension_scores)

        quality_report = QualityReport(
            report_id=f"quality_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            target_report_id=report_id,
            overall_score=round(overall_score, 2),
            quality_level=quality_level,
            dimension_scores=dimension_scores,
            passed=overall_score >= self.quality_threshold,
            issues=issues,
            recommendations=recommendations,
        )

        self.evaluation_history.append(quality_report)

        return quality_report

    def _check_relevance(self, report_data: Dict[str, Any]) -> QualityScore:
        score = 100.0
        issues = []

        keywords = report_data.get("keywords", [])
        user_interests = report_data.get("user_interests", [])

        if keywords and user_interests:
            overlap = len(set(keywords) & set(user_interests))
            relevance_ratio = overlap / len(user_interests) if user_interests else 0

            if relevance_ratio < 0.3:
                issues.append("报告内容与用户兴趣匹配度较低")
                score = relevance_ratio * 100

        return QualityScore(
            dimension=QualityDimension.RELEVANCE,
            score=score,
            details=issues,
            suggestions=["根据用户兴趣调整报告重点"] if issues else [],
        )

    def _check_actionability(self, report_data: Dict[str, Any]) -> QualityScore:
        score = 100.0
        issues = []

        recommendations = report_data.get("recommendations", [])
        if not recommendations or len(recommendations) < 3:
            issues.append("缺少足够的行动建议")
            score -= 20

        for rec in recommendations:
            if not self._is_actionable(rec):
                issues.append(f"建议不够具体: {rec[:50]}...")
                score -= 5

        return QualityScore(
            dimension=QualityDimension.ACTIONABILITY,
            score=max(0, score),
            details=issues,
            suggestions=["提供具体可执行的建议"] if issues else [],
        )

    def _is_actionable(self, recommendation: str) -> bool:
        action_verbs = ["建议", "推荐", "考虑", "选择", "关注", "查看", "比较"]

        return any(verb in recommendation for verb in action_verbs)

    def _determine_quality_level(self, score: float) -> QualityLevel:
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.ACCEPTABLE
        elif score >= 60:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _collect_issues(self, dimension_scores: List[QualityScore]) -> List[Dict]:
        issues = []
        for score in dimension_scores:
            if score.score < 70:
                issues.append(
                    {
                        "dimension": score.dimension.value,
                        "score": score.score,
                        "details": score.details,
                    }
                )
        return issues

    def _generate_recommendations(
        self, dimension_scores: List[QualityScore]
    ) -> List[str]:
        recommendations = []
        for score in dimension_scores:
            recommendations.extend(score.suggestions)
        return list(set(recommendations))

    def set_quality_threshold(self, threshold: float) -> None:
        self.quality_threshold = threshold

    def get_evaluation_stats(self) -> Dict[str, Any]:
        if not self.evaluation_history:
            return {"total_evaluations": 0}

        passed = sum(1 for e in self.evaluation_history if e.passed)
        avg_score = sum(e.overall_score for e in self.evaluation_history) / len(
            self.evaluation_history
        )

        level_counts: Dict[str, int] = {}
        for e in self.evaluation_history:
            level = e.quality_level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "total_evaluations": len(self.evaluation_history),
            "pass_rate": passed / len(self.evaluation_history),
            "average_score": round(avg_score, 2),
            "quality_level_distribution": level_counts,
        }

    def get_low_quality_reports(self, threshold: float = None) -> List[QualityReport]:
        threshold = threshold or self.quality_threshold
        return [e for e in self.evaluation_history if e.overall_score < threshold]
