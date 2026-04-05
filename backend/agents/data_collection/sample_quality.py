"""
样本质量评估器
对存入样本库的数据进行自动质量评估
"""
import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    DIVERSITY = "diversity"
    LEARNABILITY = "learnability"


class QualityScore(BaseModel):
    overall: float
    dimensions: Dict[str, float]
    confidence: float
    assessed_at: datetime = Field(default_factory=datetime.now)
    assessor: str = "SampleQualityAssessor"


class SampleForAssessment(BaseModel):
    id: str
    type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    tags: List[str] = Field(default_factory=list)


class CompletenessAssessor:
    REQUIRED_FIELDS = {
        "text": ["content", "source"],
        "structured": ["data", "schema"],
        "interaction": ["user_action", "context"],
        "agent_trace": ["state", "action", "reward"],
        "knowledge": ["content", "domain"]
    }
    
    def assess(self, sample: SampleForAssessment) -> Tuple[float, Dict[str, Any]]:
        sample_type = sample.type
        required = self.REQUIRED_FIELDS.get(sample_type, [])
        
        if not required:
            return 0.7, {"note": "No required fields defined for type"}
        
        present_fields = []
        missing_fields = []
        
        for field in required:
            if self._check_field(sample.content, field):
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        completeness = len(present_fields) / len(required) if required else 0.7
        
        details = {
            "present_fields": present_fields,
            "missing_fields": missing_fields,
            "field_count": len(present_fields),
            "required_count": len(required)
        }
        
        return completeness, details
    
    def _check_field(self, content: Dict[str, Any], field_path: str) -> bool:
        parts = field_path.split(".")
        current = content
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        
        return current is not None and current != ""


class AccuracyAssessor:
    REFERENCE_DATA = {
        "property_price": {"min": 1000, "max": 500000},
        "property_area": {"min": 10, "max": 10000},
        "year_built": {"min": 1900, "max": datetime.now().year + 5}
    }
    
    def __init__(self):
        self.known_facts: Dict[str, Any] = {}
    
    def assess(self, sample: SampleForAssessment) -> Tuple[float, Dict[str, Any]]:
        if sample.type != "structured":
            return 0.7, {"note": "Accuracy check mainly for structured data"}
        
        accuracy_score = 1.0
        violations = []
        
        for key, bounds in self.REFERENCE_DATA.items():
            value = self._extract_value(sample.content, key)
            if value is not None:
                if not (bounds["min"] <= value <= bounds["max"]):
                    accuracy_score *= 0.8
                    violations.append({
                        "field": key,
                        "value": value,
                        "expected_range": [bounds["min"], bounds["max"]]
                    })
        
        details = {
            "violations": violations,
            "checked_fields": list(self.REFERENCE_DATA.keys())
        }
        
        return accuracy_score, details
    
    def _extract_value(self, content: Dict[str, Any], key: str) -> Optional[float]:
        if key in content:
            try:
                return float(content[key])
            except (ValueError, TypeError):
                return None
        
        for k, v in content.items():
            if isinstance(v, dict):
                result = self._extract_value(v, key)
                if result is not None:
                    return result
        
        return None
    
    def add_known_fact(self, key: str, value: Any):
        self.known_facts[key] = value


class TimelinessAssessor:
    FRESHNESS_THRESHOLDS = {
        "text": 365,
        "structured": 30,
        "interaction": 7,
        "agent_trace": 1,
        "knowledge": 180
    }
    
    def assess(self, sample: SampleForAssessment) -> Tuple[float, Dict[str, Any]]:
        sample_type = sample.type
        threshold_days = self.FRESHNESS_THRESHOLDS.get(sample_type, 30)
        
        age_days = (datetime.now() - sample.created_at).days
        
        if age_days <= threshold_days:
            timeliness = 1.0 - (age_days / threshold_days) * 0.3
        else:
            timeliness = max(0.1, 0.7 * math.exp(-(age_days - threshold_days) / threshold_days))
        
        details = {
            "age_days": age_days,
            "threshold_days": threshold_days,
            "is_fresh": age_days <= threshold_days
        }
        
        return timeliness, details


class DiversityAssessor:
    def __init__(self):
        self.sample_hashes: Dict[str, List[str]] = {}
        self.similarity_threshold = 0.8
    
    def assess(self, sample: SampleForAssessment, existing_samples: List[SampleForAssessment]) -> Tuple[float, Dict[str, Any]]:
        sample_hash = self._compute_hash(sample)
        
        if not existing_samples:
            return 1.0, {"note": "First sample of its kind"}
        
        max_similarity = 0.0
        most_similar_id = None
        
        for existing in existing_samples[:100]:
            existing_hash = self._compute_hash(existing)
            similarity = self._hash_similarity(sample_hash, existing_hash)
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_id = existing.id
        
        if max_similarity >= self.similarity_threshold:
            diversity = 0.3
        elif max_similarity >= 0.5:
            diversity = 0.6
        else:
            diversity = 1.0
        
        details = {
            "max_similarity": max_similarity,
            "most_similar_sample": most_similar_id,
            "is_duplicate": max_similarity >= self.similarity_threshold
        }
        
        return diversity, details
    
    def _compute_hash(self, sample: SampleForAssessment) -> str:
        content_str = json.dumps(sample.content, sort_keys=True, ensure_ascii=False)
        tags_str = ",".join(sorted(sample.tags))
        return f"{sample.type}:{hash(content_str)}:{hash(tags_str)}"
    
    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        if hash1 == hash2:
            return 1.0
        
        parts1 = hash1.split(":")
        parts2 = hash2.split(":")
        
        if len(parts1) >= 2 and len(parts2) >= 2:
            if parts1[0] == parts2[0] and parts1[1] == parts2[1]:
                return 0.9
        
        return 0.0
    
    def add_sample_hash(self, sample_type: str, sample_hash: str):
        if sample_type not in self.sample_hashes:
            self.sample_hashes[sample_type] = []
        self.sample_hashes[sample_type].append(sample_hash)


class LearnabilityAssessor:
    def __init__(self):
        self.information_entropy_weights = {
            "text": 1.0,
            "structured": 0.8,
            "interaction": 0.9,
            "agent_trace": 1.0,
            "knowledge": 0.7
        }
    
    def assess(self, sample: SampleForAssessment) -> Tuple[float, Dict[str, Any]]:
        content = sample.content
        weight = self.information_entropy_weights.get(sample.type, 0.8)
        
        entropy = self._calculate_entropy(content)
        
        complexity = self._estimate_complexity(content)
        
        has_labels = self._check_labels(sample)
        
        learnability = entropy * 0.4 + complexity * 0.3 + has_labels * 0.3
        learnability *= weight
        
        details = {
            "entropy": entropy,
            "complexity": complexity,
            "has_labels": has_labels > 0.5,
            "weight": weight
        }
        
        return min(1.0, learnability), details
    
    def _calculate_entropy(self, content: Dict[str, Any]) -> float:
        content_str = json.dumps(content, ensure_ascii=False)
        
        if not content_str:
            return 0.0
        
        char_counts: Dict[str, int] = {}
        for char in content_str:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        total = len(content_str)
        entropy = 0.0
        
        for count in char_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        max_entropy = math.log2(len(char_counts)) if len(char_counts) > 1 else 1
        
        return min(1.0, entropy / max_entropy) if max_entropy > 0 else 0.0
    
    def _estimate_complexity(self, content: Dict[str, Any]) -> float:
        content_str = json.dumps(content, ensure_ascii=False)
        
        length_score = min(1.0, len(content_str) / 1000)
        
        depth = self._get_json_depth(content)
        depth_score = min(1.0, depth / 5)
        
        return (length_score + depth_score) / 2
    
    def _get_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        if not isinstance(obj, (dict, list)):
            return current_depth
        
        max_depth = current_depth
        
        if isinstance(obj, dict):
            for value in obj.values():
                depth = self._get_json_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        elif isinstance(obj, list):
            for item in obj:
                depth = self._get_json_depth(item, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _check_labels(self, sample: SampleForAssessment) -> float:
        content = sample.content
        
        label_fields = ["label", "annotation", "ground_truth", "target", "class"]
        
        for field in label_fields:
            if field in content:
                return 1.0
        
        if "feedback" in sample.metadata:
            return 0.8
        
        if "outcome" in sample.metadata:
            return 0.7
        
        return 0.3


class SampleQualityAssessor:
    DIMENSION_WEIGHTS = {
        QualityDimension.COMPLETENESS: 0.2,
        QualityDimension.ACCURACY: 0.2,
        QualityDimension.TIMELINESS: 0.15,
        QualityDimension.DIVERSITY: 0.2,
        QualityDimension.LEARNABILITY: 0.25
    }
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        sample_repository: Optional[Any] = None
    ):
        self.llm_client = llm_client
        self.sample_repository = sample_repository
        
        self.completeness_assessor = CompletenessAssessor()
        self.accuracy_assessor = AccuracyAssessor()
        self.timeliness_assessor = TimelinessAssessor()
        self.diversity_assessor = DiversityAssessor()
        self.learnability_assessor = LearnabilityAssessor()
        
        self.quality_history: Dict[str, List[QualityScore]] = {}
        self.feedback_adjustments: Dict[str, float] = {}
    
    async def assess(self, sample: SampleForAssessment) -> QualityScore:
        dimensions: Dict[str, float] = {}
        details: Dict[str, Any] = {}
        
        completeness, comp_details = self.completeness_assessor.assess(sample)
        dimensions[QualityDimension.COMPLETENESS.value] = completeness
        details["completeness"] = comp_details
        
        accuracy, acc_details = self.accuracy_assessor.assess(sample)
        dimensions[QualityDimension.ACCURACY.value] = accuracy
        details["accuracy"] = acc_details
        
        timeliness, time_details = self.timeliness_assessor.assess(sample)
        dimensions[QualityDimension.TIMELINESS.value] = timeliness
        details["timeliness"] = time_details
        
        existing_samples = await self._get_similar_samples(sample)
        diversity, div_details = self.diversity_assessor.assess(sample, existing_samples)
        dimensions[QualityDimension.DIVERSITY.value] = diversity
        details["diversity"] = div_details
        
        learnability, learn_details = self.learnability_assessor.assess(sample)
        dimensions[QualityDimension.LEARNABILITY.value] = learnability
        details["learnability"] = learn_details
        
        overall = self._compute_weighted_score(dimensions)
        
        confidence = self._compute_confidence(details)
        
        if self.llm_client:
            llm_score = await self._llm_assessment(sample)
            if llm_score is not None:
                overall = overall * 0.7 + llm_score * 0.3
                details["llm_score"] = llm_score
        
        adjustment = self.feedback_adjustments.get(sample.id, 0.0)
        overall = max(0.0, min(1.0, overall + adjustment))
        
        quality_score = QualityScore(
            overall=overall,
            dimensions=dimensions,
            confidence=confidence
        )
        
        self._record_quality(sample.id, quality_score)
        
        return quality_score
    
    async def _get_similar_samples(self, sample: SampleForAssessment) -> List[SampleForAssessment]:
        if not self.sample_repository:
            return []
        
        try:
            from .sample_repository import SampleQuery, SampleType
            
            samples = await self.sample_repository.query(SampleQuery(
                types=[SampleType(sample.type)],
                limit=100
            ))
            
            return [
                SampleForAssessment(
                    id=s.id,
                    type=s.type.value,
                    content=s.content,
                    metadata=s.metadata,
                    created_at=s.created_at,
                    tags=s.tags
                )
                for s in samples
            ]
        except Exception as e:
            logger.error(f"Error getting similar samples: {e}")
            return []
    
    def _compute_weighted_score(self, dimensions: Dict[str, float]) -> float:
        total = 0.0
        weight_sum = 0.0
        
        for dimension, weight in self.DIMENSION_WEIGHTS.items():
            dim_value = dimensions.get(dimension.value, 0.5)
            total += dim_value * weight
            weight_sum += weight
        
        return total / weight_sum if weight_sum > 0 else 0.5
    
    def _compute_confidence(self, details: Dict[str, Any]) -> float:
        confidence = 1.0
        
        if details.get("completeness", {}).get("missing_fields"):
            missing_count = len(details["completeness"]["missing_fields"])
            confidence *= max(0.5, 1.0 - missing_count * 0.1)
        
        if details.get("accuracy", {}).get("violations"):
            violation_count = len(details["accuracy"]["violations"])
            confidence *= max(0.3, 1.0 - violation_count * 0.2)
        
        if details.get("diversity", {}).get("is_duplicate"):
            confidence *= 0.3
        
        return confidence
    
    async def _llm_assessment(self, sample: SampleForAssessment) -> Optional[float]:
        if not self.llm_client:
            return None
        
        try:
            prompt = f"""
            请评估以下数据样本的质量（0-1分）：
            
            类型: {sample.type}
            内容: {json.dumps(sample.content, ensure_ascii=False)[:500]}
            标签: {sample.tags}
            
            评估标准：
            1. 数据完整性
            2. 信息价值
            3. 可用于训练的潜力
            
            请只返回一个0到1之间的数字。
            """
            
            response = await self.llm_client.generate(prompt)
            
            try:
                score = float(response.strip())
                return max(0.0, min(1.0, score))
            except ValueError:
                return None
                
        except Exception as e:
            logger.error(f"LLM assessment failed: {e}")
            return None
    
    def _record_quality(self, sample_id: str, score: QualityScore):
        if sample_id not in self.quality_history:
            self.quality_history[sample_id] = []
        self.quality_history[sample_id].append(score)
    
    async def record_usage_feedback(
        self,
        sample_id: str,
        training_loss_delta: Optional[float] = None,
        task_success: Optional[bool] = None
    ):
        adjustment = 0.0
        
        if training_loss_delta is not None:
            if training_loss_delta < 0:
                adjustment += 0.05
            elif training_loss_delta > 0:
                adjustment -= 0.03
        
        if task_success is not None:
            if task_success:
                adjustment += 0.05
            else:
                adjustment -= 0.05
        
        current = self.feedback_adjustments.get(sample_id, 0.0)
        self.feedback_adjustments[sample_id] = max(-0.3, min(0.3, current + adjustment))
    
    async def batch_assess(
        self,
        samples: List[SampleForAssessment]
    ) -> List[Tuple[str, QualityScore]]:
        results = []
        
        for sample in samples:
            score = await self.assess(sample)
            results.append((sample.id, score))
        
        return results
    
    def get_quality_trend(self, sample_id: str) -> Optional[Dict[str, Any]]:
        history = self.quality_history.get(sample_id)
        if not history or len(history) < 2:
            return None
        
        scores = [h.overall for h in history]
        
        return {
            "initial_score": scores[0],
            "current_score": scores[-1],
            "trend": "improving" if scores[-1] > scores[0] else "declining",
            "change": scores[-1] - scores[0],
            "assessment_count": len(scores)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        all_scores = []
        for scores in self.quality_history.values():
            all_scores.extend([s.overall for s in scores])
        
        if not all_scores:
            return {"total_assessed": 0}
        
        return {
            "total_assessed": len(self.quality_history),
            "avg_quality": sum(all_scores) / len(all_scores),
            "min_quality": min(all_scores),
            "max_quality": max(all_scores),
            "feedback_adjustments_count": len(self.feedback_adjustments)
        }
