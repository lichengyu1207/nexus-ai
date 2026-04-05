"""
可解释性审计智能体
Explainability Audit Agent

负责检查业务智能体的决策是否可解释，并记录解释供审计。
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


class ExplanationType(Enum):
    NATURAL_LANGUAGE = "natural_language"
    DECISION_TREE = "decision_tree"
    FEATURE_IMPORTANCE = "feature_importance"
    RULE_BASED = "rule_based"
    COUNTERFACTUAL = "counterfactual"


class ExplanationQuality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MISSING = "missing"


@dataclass
class DecisionExplanation:
    explanation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    agent_id: str = ""
    decision_id: str = ""
    decision_type: str = ""
    
    explanation_type: str = ExplanationType.NATURAL_LANGUAGE.value
    explanation_text: str = ""
    structured_explanation: Dict = field(default_factory=dict)
    
    key_factors: List[str] = field(default_factory=list)
    decision_path: List[str] = field(default_factory=list)
    confidence: float = 0.0
    
    completeness_score: float = 0.0
    understandability_score: float = 0.0
    faithfulness_score: float = 0.0
    overall_quality: str = ExplanationQuality.MEDIUM.value
    
    user_feedback: Optional[str] = None
    feedback_score: Optional[int] = None


@dataclass
class ExplainabilityAuditResult:
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    agent_id: str = ""
    audit_period: Dict = field(default_factory=dict)
    
    total_decisions: int = 0
    explained_decisions: int = 0
    unexplained_decisions: int = 0
    
    quality_distribution: Dict = field(default_factory=dict)
    avg_completeness: float = 0.0
    avg_understandability: float = 0.0
    avg_faithfulness: float = 0.0
    
    issues: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ExplainabilityAuditAgent:
    """
    可解释性审计智能体
    
    功能：
    1. 解释采集：每个业务智能体决策时生成解释
    2. 解释质量评估：完整性、可理解性、忠实性
    3. 审计记录：将解释与决策日志关联存储
    4. 改进反馈：对解释质量低的智能体触发调整
    5. 合规要求：满足个保法关于自动化决策解释的要求
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ExplainabilityAuditAgent"
        self.description = "检查业务智能体的决策是否可解释"
        self.config = config or {}
        
        self.explanations: Dict[str, DecisionExplanation] = {}
        self.agent_explanations: Dict[str, List[str]] = defaultdict(list)
        self.audit_results: Dict[str, ExplainabilityAuditResult] = {}
        
        self.quality_thresholds = {
            "completeness": 0.6,
            "understandability": 0.6,
            "faithfulness": 0.7,
        }
        
        self.stats = {
            "total_explanations": 0,
            "explanations_by_quality": defaultdict(int),
            "explanations_by_agent": defaultdict(int),
            "avg_quality_scores": {
                "completeness": 0.0,
                "understandability": 0.0,
                "faithfulness": 0.0,
            },
            "audits_performed": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def record_explanation(
        self,
        agent_id: str,
        decision_id: str,
        decision_type: str,
        explanation_text: str,
        explanation_type: str = ExplanationType.NATURAL_LANGUAGE.value,
        key_factors: Optional[List[str]] = None,
        decision_path: Optional[List[str]] = None,
        confidence: float = 0.0,
        structured_explanation: Optional[Dict] = None,
    ) -> DecisionExplanation:
        explanation = DecisionExplanation(
            agent_id=agent_id,
            decision_id=decision_id,
            decision_type=decision_type,
            explanation_type=explanation_type,
            explanation_text=explanation_text,
            key_factors=key_factors or [],
            decision_path=decision_path or [],
            confidence=confidence,
            structured_explanation=structured_explanation or {},
        )
        
        await self._evaluate_explanation_quality(explanation)
        
        self.explanations[explanation.explanation_id] = explanation
        self.agent_explanations[agent_id].append(explanation.explanation_id)
        
        self.stats["total_explanations"] += 1
        self.stats["explanations_by_quality"][explanation.overall_quality] += 1
        self.stats["explanations_by_agent"][agent_id] += 1
        
        self._update_avg_scores(explanation)
        
        return explanation
    
    async def _evaluate_explanation_quality(
        self,
        explanation: DecisionExplanation,
    ):
        explanation.completeness_score = self._evaluate_completeness(explanation)
        explanation.understandability_score = self._evaluate_understandability(explanation)
        explanation.faithfulness_score = self._evaluate_faithfulness(explanation)
        
        avg_score = (
            explanation.completeness_score +
            explanation.understandability_score +
            explanation.faithfulness_score
        ) / 3
        
        if avg_score >= 0.8:
            explanation.overall_quality = ExplanationQuality.HIGH.value
        elif avg_score >= 0.5:
            explanation.overall_quality = ExplanationQuality.MEDIUM.value
        elif avg_score >= 0.2:
            explanation.overall_quality = ExplanationQuality.LOW.value
        else:
            explanation.overall_quality = ExplanationQuality.MISSING.value
    
    def _evaluate_completeness(self, explanation: DecisionExplanation) -> float:
        score = 0.0
        
        if explanation.explanation_text:
            score += 0.3
        
        if explanation.key_factors:
            score += min(0.3, len(explanation.key_factors) * 0.1)
        
        if explanation.decision_path:
            score += min(0.2, len(explanation.decision_path) * 0.05)
        
        if explanation.structured_explanation:
            score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_understandability(self, explanation: DecisionExplanation) -> float:
        score = 0.0
        
        text = explanation.explanation_text
        if text:
            word_count = len(text.split())
            
            if 20 <= word_count <= 200:
                score += 0.4
            elif word_count < 20:
                score += 0.2
            else:
                score += 0.3
            
            jargon_words = ["模型", "算法", "参数", "权重", "神经网络"]
            jargon_count = sum(1 for w in jargon_words if w in text)
            score += max(0, 0.3 - jargon_count * 0.1)
            
            if any(w in text for w in ["因为", "由于", "所以", "因此"]):
                score += 0.3
        
        return min(1.0, score)
    
    def _evaluate_faithfulness(self, explanation: DecisionExplanation) -> float:
        score = 0.5
        
        if explanation.key_factors:
            score += 0.2
        
        if explanation.decision_path:
            score += 0.2
        
        if explanation.confidence > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def _update_avg_scores(self, explanation: DecisionExplanation):
        total = self.stats["total_explanations"]
        
        for metric, score in [
            ("completeness", explanation.completeness_score),
            ("understandability", explanation.understandability_score),
            ("faithfulness", explanation.faithfulness_score),
        ]:
            current_avg = self.stats["avg_quality_scores"][metric]
            self.stats["avg_quality_scores"][metric] = (
                (current_avg * (total - 1) + score) / total
            )
    
    async def record_user_feedback(
        self,
        explanation_id: str,
        feedback: str,
        score: int,
    ) -> bool:
        explanation = self.explanations.get(explanation_id)
        if not explanation:
            return False
        
        explanation.user_feedback = feedback
        explanation.feedback_score = score
        
        return True
    
    async def get_explanation(self, decision_id: str) -> Optional[Dict]:
        for exp in self.explanations.values():
            if exp.decision_id == decision_id:
                return {
                    "explanation_id": exp.explanation_id,
                    "agent_id": exp.agent_id,
                    "decision_type": exp.decision_type,
                    "explanation_text": exp.explanation_text,
                    "key_factors": exp.key_factors,
                    "decision_path": exp.decision_path,
                    "confidence": exp.confidence,
                    "quality": exp.overall_quality,
                    "completeness_score": exp.completeness_score,
                    "understandability_score": exp.understandability_score,
                    "faithfulness_score": exp.faithfulness_score,
                }
        return None
    
    async def audit_agent_explainability(
        self,
        agent_id: str,
        time_range: Optional[tuple] = None,
    ) -> ExplainabilityAuditResult:
        explanation_ids = self.agent_explanations.get(agent_id, [])
        
        if time_range:
            explanations = [
                self.explanations[eid] for eid in explanation_ids
                if eid in self.explanations
                and time_range[0] <= self.explanations[eid].timestamp <= time_range[1]
            ]
        else:
            now = datetime.utcnow()
            start = (now - timedelta(days=30)).isoformat()
            explanations = [
                self.explanations[eid] for eid in explanation_ids
                if eid in self.explanations
                and self.explanations[eid].timestamp >= start
            ]
        
        result = ExplainabilityAuditResult(
            agent_id=agent_id,
            audit_period=time_range or {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            total_decisions=len(explanations),
            explained_decisions=len([e for e in explanations if e.overall_quality != ExplanationQuality.MISSING.value]),
            unexplained_decisions=len([e for e in explanations if e.overall_quality == ExplanationQuality.MISSING.value]),
        )
        
        if explanations:
            result.quality_distribution = {
                ExplanationQuality.HIGH.value: sum(1 for e in explanations if e.overall_quality == ExplanationQuality.HIGH.value),
                ExplanationQuality.MEDIUM.value: sum(1 for e in explanations if e.overall_quality == ExplanationQuality.MEDIUM.value),
                ExplanationQuality.LOW.value: sum(1 for e in explanations if e.overall_quality == ExplanationQuality.LOW.value),
                ExplanationQuality.MISSING.value: sum(1 for e in explanations if e.overall_quality == ExplanationQuality.MISSING.value),
            }
            
            result.avg_completeness = sum(e.completeness_score for e in explanations) / len(explanations)
            result.avg_understandability = sum(e.understandability_score for e in explanations) / len(explanations)
            result.avg_faithfulness = sum(e.faithfulness_score for e in explanations) / len(explanations)
        
        result.issues = self._identify_issues(result, explanations)
        result.recommendations = self._generate_recommendations(result)
        
        self.audit_results[result.audit_id] = result
        self.stats["audits_performed"] += 1
        
        return result
    
    def _identify_issues(
        self,
        result: ExplainabilityAuditResult,
        explanations: List[DecisionExplanation],
    ) -> List[Dict]:
        issues = []
        
        if result.unexplained_decisions > 0:
            issues.append({
                "type": "missing_explanation",
                "count": result.unexplained_decisions,
                "severity": "high",
                "description": f"{result.unexplained_decisions}个决策缺少解释",
            })
        
        if result.avg_completeness < self.quality_thresholds["completeness"]:
            issues.append({
                "type": "low_completeness",
                "score": result.avg_completeness,
                "severity": "medium",
                "description": f"解释完整性得分{result.avg_completeness:.2f}低于阈值",
            })
        
        if result.avg_understandability < self.quality_thresholds["understandability"]:
            issues.append({
                "type": "low_understandability",
                "score": result.avg_understandability,
                "severity": "medium",
                "description": f"解释可理解性得分{result.avg_understandability:.2f}低于阈值",
            })
        
        if result.avg_faithfulness < self.quality_thresholds["faithfulness"]:
            issues.append({
                "type": "low_faithfulness",
                "score": result.avg_faithfulness,
                "severity": "high",
                "description": f"解释忠实性得分{result.avg_faithfulness:.2f}低于阈值",
            })
        
        return issues
    
    def _generate_recommendations(
        self,
        result: ExplainabilityAuditResult,
    ) -> List[str]:
        recommendations = []
        
        if result.unexplained_decisions > 0:
            recommendations.append("为所有决策生成解释，确保满足个保法要求")
        
        if result.avg_completeness < self.quality_thresholds["completeness"]:
            recommendations.append("增加解释的关键因素和决策路径信息")
        
        if result.avg_understandability < self.quality_thresholds["understandability"]:
            recommendations.append("使用更通俗易懂的语言生成解释")
            recommendations.append("控制解释长度在合理范围内")
        
        if result.avg_faithfulness < self.quality_thresholds["faithfulness"]:
            recommendations.append("确保解释真实反映模型内部决策逻辑")
            recommendations.append("考虑使用可解释AI技术如SHAP、LIME")
        
        return recommendations
    
    async def get_low_quality_explanations(
        self,
        agent_id: Optional[str] = None,
    ) -> List[Dict]:
        explanations = self.explanations.values()
        
        if agent_id:
            explanations = [e for e in explanations if e.agent_id == agent_id]
        
        low_quality = [
            e for e in explanations
            if e.overall_quality in [ExplanationQuality.LOW.value, ExplanationQuality.MISSING.value]
        ]
        
        return [
            {
                "explanation_id": e.explanation_id,
                "agent_id": e.agent_id,
                "decision_type": e.decision_type,
                "quality": e.overall_quality,
                "completeness_score": e.completeness_score,
                "understandability_score": e.understandability_score,
                "faithfulness_score": e.faithfulness_score,
            }
            for e in low_quality
        ]
    
    async def generate_explanation_for_query(
        self,
        decision_id: str,
        query: str,
    ) -> Dict:
        explanation = await self.get_explanation(decision_id)
        
        if not explanation:
            return {
                "found": False,
                "message": "未找到该决策的解释记录",
            }
        
        response = {
            "found": True,
            "decision_id": decision_id,
            "explanation": explanation["explanation_text"],
            "key_factors": explanation["key_factors"],
            "confidence": explanation["confidence"],
        }
        
        if "为什么" in query:
            response["answer"] = f"该决策的原因如下：{explanation['explanation_text']}"
        elif "因素" in query or "影响" in query:
            response["answer"] = f"影响该决策的主要因素包括：{', '.join(explanation['key_factors'])}"
        else:
            response["answer"] = explanation["explanation_text"]
        
        return response
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_explanations": self.stats["total_explanations"],
            "explanations_by_quality": dict(self.stats["explanations_by_quality"]),
            "avg_quality_scores": {
                k: round(v, 2) for k, v in self.stats["avg_quality_scores"].items()
            },
            "audits_performed": self.stats["audits_performed"],
        }
