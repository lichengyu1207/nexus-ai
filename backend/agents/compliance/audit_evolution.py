"""
审计智能体进化引擎
Audit Evolution Engine - 让审计智能体从历史经验中学习进化
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import uuid
import hashlib
import re


class ExperienceType(Enum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_NEGATIVE = "false_negative"


class KnowledgeType(Enum):
    PATTERN = "pattern"
    RULE = "rule"
    THRESHOLD = "threshold"
    CORRELATION = "correlation"
    EXCEPTION = "exception"


class LearningStatus(Enum):
    PENDING = "pending"
    TRAINING = "training"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"


@dataclass
class AuditExperience:
    experience_id: str
    experience_type: ExperienceType
    event_data: Dict[str, Any]
    detection_method: str
    original_result: str
    human_feedback: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    used_for_training: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditKnowledge:
    knowledge_id: str
    knowledge_type: KnowledgeType
    name: str
    description: str
    pattern: str
    conditions: Dict[str, Any]
    confidence: float
    effectiveness_score: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    success_rate: float = 0.0
    status: LearningStatus = LearningStatus.VALIDATED
    source_experiences: List[str] = field(default_factory=list)


@dataclass
class LearningSession:
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    experiences_processed: int = 0
    knowledge_created: int = 0
    knowledge_updated: int = 0
    validation_score: float = 0.0
    status: str = "pending"


class ExperienceReplay:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.experiences: List[AuditExperience] = []
        self.experience_index: Dict[str, AuditExperience] = {}

    def add_experience(self, experience: AuditExperience) -> None:
        if len(self.experiences) >= self.max_size:
            removed = self.experiences.pop(0)
            if removed.experience_id in self.experience_index:
                del self.experience_index[removed.experience_id]

        self.experiences.append(experience)
        self.experience_index[experience.experience_id] = experience

    def get_experiences_by_type(
        self, experience_type: ExperienceType
    ) -> List[AuditExperience]:
        return [e for e in self.experiences if e.experience_type == experience_type]

    def get_recent_experiences(self, days: int = 30) -> List[AuditExperience]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [e for e in self.experiences if e.created_at >= cutoff]

    def sample_for_training(
        self, sample_size: int = 1000
    ) -> Tuple[List[AuditExperience], List[AuditExperience]]:
        positives = [e for e in self.experiences if e.experience_type in [
            ExperienceType.TRUE_POSITIVE, ExperienceType.FALSE_NEGATIVE
        ]]
        negatives = [e for e in self.experiences if e.experience_type in [
            ExperienceType.FALSE_POSITIVE, ExperienceType.TRUE_NEGATIVE
        ]]

        import random

        pos_sample = random.sample(positives, min(sample_size, len(positives)))
        neg_sample = random.sample(negatives, min(sample_size, len(negatives)))

        return pos_sample, neg_sample

    def get_experience_stats(self) -> Dict[str, int]:
        stats = {et.value: 0 for et in ExperienceType}
        for exp in self.experiences:
            stats[exp.experience_type.value] += 1
        return stats


class PatternLearner:
    def __init__(self):
        self.learned_patterns: Dict[str, AuditKnowledge] = {}
        self.pattern_candidates: List[Dict] = []

    def extract_patterns(
        self, experiences: List[AuditExperience]
    ) -> List[Dict]:
        patterns = []

        event_texts = []
        for exp in experiences:
            event_data = exp.event_data
            if "description" in event_data:
                event_texts.append(event_data["description"])
            if "title" in event_data:
                event_texts.append(event_data["title"])

        word_freq: Dict[str, int] = {}
        for text in event_texts:
            words = re.findall(r"\w+", text.lower())
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1

        significant_words = [
            (word, freq)
            for word, freq in word_freq.items()
            if freq >= len(experiences) * 0.3
        ]

        for word, freq in significant_words:
            pattern = {
                "pattern_type": "keyword",
                "pattern": word,
                "frequency": freq,
                "confidence": freq / len(experiences),
            }
            patterns.append(pattern)

        return patterns

    def create_pattern_knowledge(
        self, pattern: Dict, source_experiences: List[str]
    ) -> AuditKnowledge:
        knowledge_id = f"pattern_{uuid.uuid4().hex[:8]}"

        knowledge = AuditKnowledge(
            knowledge_id=knowledge_id,
            knowledge_type=KnowledgeType.PATTERN,
            name=f"Pattern: {pattern['pattern']}",
            description=f"Auto-learned pattern from {len(source_experiences)} experiences",
            pattern=pattern["pattern"],
            conditions={"min_frequency": pattern["frequency"]},
            confidence=pattern["confidence"],
            effectiveness_score=0.0,
            source_experiences=source_experiences,
        )

        self.learned_patterns[knowledge_id] = knowledge
        return knowledge

    def validate_pattern(
        self, knowledge: AuditKnowledge, test_experiences: List[AuditExperience]
    ) -> float:
        matches = 0
        total = len(test_experiences)

        for exp in test_experiences:
            event_data = exp.event_data
            text = f"{event_data.get('title', '')} {event_data.get('description', '')}"
            if knowledge.pattern.lower() in text.lower():
                matches += 1

        return matches / total if total > 0 else 0.0


class RuleLearner:
    def __init__(self):
        self.learned_rules: Dict[str, AuditKnowledge] = {}

    def extract_rules(
        self, experiences: List[AuditExperience]
    ) -> List[Dict]:
        rules = []

        true_positives = [
            e for e in experiences if e.experience_type == ExperienceType.TRUE_POSITIVE
        ]
        false_positives = [
            e for e in experiences if e.experience_type == ExperienceType.FALSE_POSITIVE
        ]

        tp_features = self._extract_features(true_positives)
        fp_features = self._extract_features(false_positives)

        for feature, tp_count in tp_features.items():
            fp_count = fp_features.get(feature, 0)
            total = tp_count + fp_count

            if total >= 5 and tp_count / total >= 0.8:
                rules.append(
                    {
                        "feature": feature,
                        "tp_count": tp_count,
                        "fp_count": fp_count,
                        "precision": tp_count / total,
                        "rule_type": "include",
                    }
                )

        for feature, fp_count in fp_features.items():
            tp_count = tp_features.get(feature, 0)
            total = tp_count + fp_count

            if total >= 5 and fp_count / total >= 0.8:
                rules.append(
                    {
                        "feature": feature,
                        "tp_count": tp_count,
                        "fp_count": fp_count,
                        "precision": fp_count / total,
                        "rule_type": "exclude",
                    }
                )

        return rules

    def _extract_features(
        self, experiences: List[AuditExperience]
    ) -> Dict[str, int]:
        features: Dict[str, int] = {}

        for exp in experiences:
            event_data = exp.event_data

            if "category" in event_data:
                key = f"category:{event_data['category']}"
                features[key] = features.get(key, 0) + 1

            if "severity" in event_data:
                key = f"severity:{event_data['severity']}"
                features[key] = features.get(key, 0) + 1

            if "source" in event_data:
                key = f"source:{event_data['source']}"
                features[key] = features.get(key, 0) + 1

        return features

    def create_rule_knowledge(
        self, rule: Dict, source_experiences: List[str]
    ) -> AuditKnowledge:
        knowledge_id = f"rule_{uuid.uuid4().hex[:8]}"

        rule_type = "include" if rule["rule_type"] == "include" else "exclude"

        knowledge = AuditKnowledge(
            knowledge_id=knowledge_id,
            knowledge_type=KnowledgeType.RULE,
            name=f"Rule: {rule['feature']}",
            description=f"Auto-learned rule with precision {rule['precision']:.2f}",
            pattern=rule["feature"],
            conditions={
                "rule_type": rule_type,
                "precision": rule["precision"],
            },
            confidence=rule["precision"],
            effectiveness_score=rule["precision"],
            source_experiences=source_experiences,
        )

        self.learned_rules[knowledge_id] = knowledge
        return knowledge


class ThresholdOptimizer:
    def __init__(self):
        self.thresholds: Dict[str, float] = {}
        self.threshold_history: Dict[str, List[float]] = {}

    def optimize_threshold(
        self,
        parameter: str,
        experiences: List[AuditExperience],
        target_metric: str = "f1",
    ) -> Dict[str, Any]:
        values = []
        labels = []

        for exp in experiences:
            if parameter in exp.event_data:
                values.append(float(exp.event_data[parameter]))
                labels.append(
                    1
                    if exp.experience_type
                    in [ExperienceType.TRUE_POSITIVE, ExperienceType.FALSE_NEGATIVE]
                    else 0
                )

        if not values:
            return {"status": "no_data", "parameter": parameter}

        best_threshold = 0.0
        best_score = 0.0

        sorted_values = sorted(set(values))
        for threshold in sorted_values:
            predictions = [1 if v >= threshold else 0 for v in values]

            tp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
            fp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
            fn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            score = f1 if target_metric == "f1" else precision if target_metric == "precision" else recall

            if score > best_score:
                best_score = score
                best_threshold = threshold

        self.thresholds[parameter] = best_threshold
        if parameter not in self.threshold_history:
            self.threshold_history[parameter] = []
        self.threshold_history[parameter].append(best_threshold)

        return {
            "status": "optimized",
            "parameter": parameter,
            "threshold": best_threshold,
            "score": best_score,
            "metric": target_metric,
        }

    def get_threshold(self, parameter: str) -> Optional[float]:
        return self.thresholds.get(parameter)


class KnowledgeSharing:
    def __init__(self):
        self.shared_knowledge: Dict[str, AuditKnowledge] = {}
        self.knowledge_versions: Dict[str, List[Dict]] = {}

    def share_knowledge(
        self, knowledge: AuditKnowledge, source_agent: str
    ) -> str:
        share_id = f"share_{uuid.uuid4().hex[:8]}"

        self.shared_knowledge[share_id] = knowledge

        if knowledge.knowledge_id not in self.knowledge_versions:
            self.knowledge_versions[knowledge.knowledge_id] = []

        self.knowledge_versions[knowledge.knowledge_id].append(
            {
                "share_id": share_id,
                "source_agent": source_agent,
                "shared_at": datetime.utcnow().isoformat(),
                "version": knowledge.usage_count,
            }
        )

        return share_id

    def receive_knowledge(
        self, share_id: str, target_agent: str
    ) -> Optional[AuditKnowledge]:
        knowledge = self.shared_knowledge.get(share_id)
        if knowledge:
            knowledge.usage_count += 1
        return knowledge

    def get_latest_knowledge(
        self, knowledge_type: KnowledgeType = None
    ) -> List[AuditKnowledge]:
        knowledge_list = list(self.shared_knowledge.values())

        if knowledge_type:
            knowledge_list = [
                k for k in knowledge_list if k.knowledge_type == knowledge_type
            ]

        knowledge_list.sort(key=lambda k: k.updated_at, reverse=True)
        return knowledge_list


class AuditEvolutionEngine:
    def __init__(self, engine_id: str = "audit_evolution_001"):
        self.engine_id = engine_id
        self.experience_replay = ExperienceReplay()
        self.pattern_learner = PatternLearner()
        self.rule_learner = RuleLearner()
        self.threshold_optimizer = ThresholdOptimizer()
        self.knowledge_sharing = KnowledgeSharing()

        self.knowledge_base: Dict[str, AuditKnowledge] = {}
        self.learning_sessions: List[LearningSession] = []
        self.evolution_metrics: Dict[str, Any] = {}

    def record_experience(
        self,
        experience_type: ExperienceType,
        event_data: Dict[str, Any],
        detection_method: str,
        original_result: str,
        human_feedback: str,
        confidence: float = 1.0,
    ) -> AuditExperience:
        experience = AuditExperience(
            experience_id=f"exp_{uuid.uuid4().hex[:8]}",
            experience_type=experience_type,
            event_data=event_data,
            detection_method=detection_method,
            original_result=original_result,
            human_feedback=human_feedback,
            confidence=confidence,
        )

        self.experience_replay.add_experience(experience)
        return experience

    async def run_learning_session(self) -> LearningSession:
        session = LearningSession(
            session_id=f"session_{uuid.uuid4().hex[:8]}",
            start_time=datetime.utcnow(),
            status="running",
        )

        pos_experiences, neg_experiences = self.experience_replay.sample_for_training(
            500
        )
        all_experiences = pos_experiences + neg_experiences
        session.experiences_processed = len(all_experiences)

        patterns = self.pattern_learner.extract_patterns(pos_experiences)
        for pattern in patterns[:10]:
            source_ids = [e.experience_id for e in pos_experiences[:10]]
            knowledge = self.pattern_learner.create_pattern_knowledge(
                pattern, source_ids
            )
            self.knowledge_base[knowledge.knowledge_id] = knowledge
            session.knowledge_created += 1

        rules = self.rule_learner.extract_rules(all_experiences)
        for rule in rules[:10]:
            source_ids = [e.experience_id for e in all_experiences[:10]]
            knowledge = self.rule_learner.create_rule_knowledge(rule, source_ids)
            self.knowledge_base[knowledge.knowledge_id] = knowledge
            session.knowledge_created += 1

        threshold_params = ["risk_score", "anomaly_score", "frequency"]
        for param in threshold_params:
            result = self.threshold_optimizer.optimize_threshold(
                param, all_experiences
            )
            if result["status"] == "optimized":
                session.knowledge_updated += 1

        session.validation_score = self._validate_learning()
        session.end_time = datetime.utcnow()
        session.status = "completed"

        self.learning_sessions.append(session)
        return session

    def _validate_learning(self) -> float:
        recent_experiences = self.experience_replay.get_recent_experiences(7)

        if not recent_experiences:
            return 0.0

        correct = 0
        total = 0

        for exp in recent_experiences:
            if exp.experience_type in [
                ExperienceType.TRUE_POSITIVE,
                ExperienceType.TRUE_NEGATIVE,
            ]:
                correct += 1
            total += 1

        return correct / total if total > 0 else 0.0

    def apply_knowledge(
        self, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        results = {
            "matched_patterns": [],
            "matched_rules": [],
            "threshold_adjustments": {},
            "overall_confidence": 0.0,
        }

        text = f"{event_data.get('title', '')} {event_data.get('description', '')}"

        for knowledge in self.knowledge_base.values():
            if knowledge.status != LearningStatus.DEPLOYED:
                continue

            if knowledge.knowledge_type == KnowledgeType.PATTERN:
                if knowledge.pattern.lower() in text.lower():
                    results["matched_patterns"].append(
                        {
                            "knowledge_id": knowledge.knowledge_id,
                            "pattern": knowledge.pattern,
                            "confidence": knowledge.confidence,
                        }
                    )

            elif knowledge.knowledge_type == KnowledgeType.RULE:
                feature = knowledge.pattern
                feature_type, feature_value = feature.split(":", 1)
                if event_data.get(feature_type) == feature_value:
                    rule_type = knowledge.conditions.get("rule_type", "include")
                    results["matched_rules"].append(
                        {
                            "knowledge_id": knowledge.knowledge_id,
                            "feature": feature,
                            "rule_type": rule_type,
                            "confidence": knowledge.confidence,
                        }
                    )

        for param, threshold in self.threshold_optimizer.thresholds.items():
            if param in event_data:
                results["threshold_adjustments"][param] = threshold

        if results["matched_patterns"] or results["matched_rules"]:
            confidences = [
                p["confidence"] for p in results["matched_patterns"]
            ] + [r["confidence"] for r in results["matched_rules"]]
            results["overall_confidence"] = sum(confidences) / len(confidences)

        return results

    def share_knowledge_with_swarm(self, knowledge_ids: List[str]) -> List[str]:
        share_ids = []
        for kid in knowledge_ids:
            if kid in self.knowledge_base:
                knowledge = self.knowledge_base[kid]
                share_id = self.knowledge_sharing.share_knowledge(
                    knowledge, self.engine_id
                )
                share_ids.append(share_id)
        return share_ids

    def receive_knowledge_from_swarm(self, share_ids: List[str]) -> int:
        received_count = 0
        for share_id in share_ids:
            knowledge = self.knowledge_sharing.receive_knowledge(
                share_id, self.engine_id
            )
            if knowledge:
                self.knowledge_base[knowledge.knowledge_id] = knowledge
                received_count += 1
        return received_count

    def get_evolution_metrics(self) -> Dict[str, Any]:
        exp_stats = self.experience_replay.get_experience_stats()

        return {
            "total_experiences": len(self.experience_replay.experiences),
            "experience_distribution": exp_stats,
            "knowledge_base_size": len(self.knowledge_base),
            "learning_sessions": len(self.learning_sessions),
            "validation_score": (
                self.learning_sessions[-1].validation_score
                if self.learning_sessions
                else 0
            ),
            "knowledge_by_type": self._count_knowledge_by_type(),
            "thresholds_optimized": len(self.threshold_optimizer.thresholds),
        }

    def _count_knowledge_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for knowledge in self.knowledge_base.values():
            type_name = knowledge.knowledge_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def deploy_knowledge(self, knowledge_id: str) -> bool:
        if knowledge_id in self.knowledge_base:
            self.knowledge_base[knowledge_id].status = LearningStatus.DEPLOYED
            return True
        return False

    def deprecate_knowledge(
        self, knowledge_id: str, reason: str = ""
    ) -> bool:
        if knowledge_id in self.knowledge_base:
            self.knowledge_base[knowledge_id].status = LearningStatus.DEPRECATED
            self.knowledge_base[knowledge_id].metadata["deprecation_reason"] = reason
            return True
        return False

    def get_effective_knowledge(self) -> List[AuditKnowledge]:
        return [
            k
            for k in self.knowledge_base.values()
            if k.status == LearningStatus.DEPLOYED and k.effectiveness_score >= 0.7
        ]
