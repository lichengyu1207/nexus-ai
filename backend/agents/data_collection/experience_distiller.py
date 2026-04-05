"""
经验知识蒸馏智能体
从智能体的历史经验中提炼知识
"""
import asyncio
import json
import logging
from collections import Counter
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from .knowledge_distiller import (
    KnowledgeDistillerAgent,
    DistillationResult,
    DistillationStatus,
    DistillationMethod,
    KnowledgeType
)

logger = logging.getLogger(__name__)


class ExperienceType(str, Enum):
    DECISION_TRACE = "decision_trace"
    COLLABORATION = "collaboration"
    USER_PREFERENCE = "user_preference"
    TASK_EXECUTION = "task_execution"
    ERROR_RECOVERY = "error_recovery"


class ExperienceSample(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    experience_type: ExperienceType
    agent_id: str
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    next_state: Optional[Dict[str, Any]] = None
    outcome: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class Rule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    condition: Dict[str, Any]
    action: Dict[str, Any]
    confidence: float
    support: int
    examples: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class DecisionNode(BaseModel):
    feature: str
    threshold: Optional[float] = None
    categories: Optional[List[str]] = None
    children: Dict[str, Any] = Field(default_factory=dict)
    prediction: Optional[Dict[str, Any]] = None
    samples: int = 0


class HeuristicFunction(BaseModel):
    heuristic_id: str
    name: str
    parameters: Dict[str, float]
    applicable_contexts: List[str]
    performance_score: float
    usage_count: int = 0


class BehaviorCloner:
    def __init__(self, min_samples: int = 10):
        self.min_samples = min_samples
        self.action_mapping: Dict[str, List[Dict[str, Any]]] = {}
    
    def fit(self, experiences: List[ExperienceSample]) -> Dict[str, Any]:
        for exp in experiences:
            state_key = self._state_to_key(exp.state)
            action = exp.action
            
            if state_key not in self.action_mapping:
                self.action_mapping[state_key] = []
            
            self.action_mapping[state_key].append({
                "action": action,
                "reward": exp.reward,
                "outcome": exp.outcome
            })
        
        policy = {}
        for state_key, actions in self.action_mapping.items():
            if len(actions) >= self.min_samples:
                best_action = max(actions, key=lambda x: x["reward"])
                policy[state_key] = best_action["action"]
        
        return policy
    
    def predict(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        state_key = self._state_to_key(state)
        return self.action_mapping.get(state_key, [{}])[0].get("action")
    
    def _state_to_key(self, state: Dict[str, Any]) -> str:
        return json.dumps(state, sort_keys=True, ensure_ascii=False)[:200]


class InverseReinforcementLearner:
    def __init__(self, features: Optional[List[str]] = None):
        self.features = features or []
        self.reward_weights: Dict[str, float] = {}
        self.feature_counts: Dict[str, Counter] = {}
    
    def infer_reward(self, experiences: List[ExperienceSample]) -> Dict[str, float]:
        positive_exps = [e for e in experiences if e.reward > 0]
        negative_exps = [e for e in experiences if e.reward <= 0]
        
        if not self.features:
            self.features = self._extract_features(experiences)
        
        for feature in self.features:
            pos_count = sum(1 for e in positive_exps if self._has_feature(e, feature))
            neg_count = sum(1 for e in negative_exps if self._has_feature(e, feature))
            
            total_pos = len(positive_exps) if positive_exps else 1
            total_neg = len(negative_exps) if negative_exps else 1
            
            pos_ratio = pos_count / total_pos
            neg_ratio = neg_count / total_neg
            
            self.reward_weights[feature] = pos_ratio - neg_ratio
        
        return self.reward_weights
    
    def compute_reward(self, state: Dict[str, Any], action: Dict[str, Any]) -> float:
        total_reward = 0.0
        
        for feature, weight in self.reward_weights.items():
            if self._state_has_feature(state, feature):
                total_reward += weight
        
        return total_reward
    
    def _extract_features(self, experiences: List[ExperienceSample]) -> List[str]:
        features = set()
        
        for exp in experiences:
            features.update(self._get_state_features(exp.state))
        
        return list(features)[:50]
    
    def _get_state_features(self, state: Dict[str, Any]) -> List[str]:
        features = []
        
        for key, value in state.items():
            if isinstance(value, bool):
                features.append(f"{key}={value}")
            elif isinstance(value, (int, float)):
                if value > 0:
                    features.append(f"{key}>0")
                if value > 10:
                    features.append(f"{key}>10")
            elif isinstance(value, str) and len(value) < 50:
                features.append(f"{key}={value[:20]}")
        
        return features
    
    def _has_feature(self, exp: ExperienceSample, feature: str) -> bool:
        return self._state_has_feature(exp.state, feature) or self._state_has_feature(exp.action, feature)
    
    def _state_has_feature(self, state: Dict[str, Any], feature: str) -> bool:
        if "=" in feature:
            key, value = feature.split("=", 1)
            if key in state:
                return str(state[key])[:20] == value
        elif ">" in feature:
            key, threshold = feature.split(">")
            if key in state:
                try:
                    return float(state[key]) > float(threshold)
                except (ValueError, TypeError):
                    return False
        return False


class PatternMiner:
    def __init__(
        self,
        min_support: int = 5,
        min_confidence: float = 0.7
    ):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.patterns: List[Rule] = []
    
    def mine_patterns(self, experiences: List[ExperienceSample]) -> List[Rule]:
        state_action_pairs = []
        
        for exp in experiences:
            state_features = self._extract_features(exp.state)
            action_features = self._extract_features(exp.action)
            
            state_action_pairs.append({
                "state": state_features,
                "action": action_features,
                "reward": exp.reward,
                "outcome": exp.outcome
            })
        
        frequent_patterns = self._find_frequent_patterns(state_action_pairs)
        
        rules = self._generate_rules(frequent_patterns, state_action_pairs)
        
        self.patterns = rules
        return rules
    
    def _extract_features(self, obj: Dict[str, Any]) -> List[str]:
        features = []
        
        for key, value in obj.items():
            if isinstance(value, bool):
                features.append(f"{key}={value}")
            elif isinstance(value, (int, float)):
                if value > 0:
                    features.append(f"{key}>0")
            elif isinstance(value, str) and len(value) < 30:
                features.append(f"{key}={value}")
            elif isinstance(value, dict):
                sub_features = self._extract_features(value)
                features.extend([f"{key}.{f}" for f in sub_features])
        
        return features
    
    def _find_frequent_patterns(
        self,
        pairs: List[Dict[str, Any]]
    ) -> Dict[Tuple[str, ...], int]:
        pattern_counts: Counter = Counter()
        
        for pair in pairs:
            all_features = pair["state"] + pair["action"]
            
            for i in range(len(all_features)):
                for j in range(i + 1, len(all_features)):
                    pattern = tuple(sorted([all_features[i], all_features[j]]))
                    pattern_counts[pattern] += 1
        
        frequent = {
            pattern: count
            for pattern, count in pattern_counts.items()
            if count >= self.min_support
        }
        
        return frequent
    
    def _generate_rules(
        self,
        frequent_patterns: Dict[Tuple[str, ...], int],
        pairs: List[Dict[str, Any]]
    ) -> List[Rule]:
        rules = []
        
        for pattern, support in frequent_patterns.items():
            state_features = []
            action_features = []
            
            for feature in pattern:
                found_in_state = any(feature in pair["state"] for pair in pairs)
                found_in_action = any(feature in pair["action"] for pair in pairs)
                
                if found_in_state and not found_in_action:
                    state_features.append(feature)
                elif found_in_action:
                    action_features.append(feature)
            
            if state_features and action_features:
                confidence = self._compute_confidence(
                    state_features,
                    action_features,
                    pairs
                )
                
                if confidence >= self.min_confidence:
                    rule = Rule(
                        condition={"features": state_features},
                        action={"features": action_features},
                        confidence=confidence,
                        support=support
                    )
                    rules.append(rule)
        
        return rules
    
    def _compute_confidence(
        self,
        condition_features: List[str],
        action_features: List[str],
        pairs: List[Dict[str, Any]]
    ) -> float:
        condition_matches = 0
        both_matches = 0
        
        for pair in pairs:
            condition_met = all(f in pair["state"] for f in condition_features)
            action_met = all(f in pair["action"] for f in action_features)
            
            if condition_met:
                condition_matches += 1
                if action_met:
                    both_matches += 1
        
        return both_matches / condition_matches if condition_matches > 0 else 0.0


class DecisionTreeBuilder:
    def __init__(self, max_depth: int = 5, min_samples: int = 10):
        self.max_depth = max_depth
        self.min_samples = min_samples
    
    def build(self, experiences: List[ExperienceSample]) -> DecisionNode:
        if not experiences:
            return DecisionNode(feature="empty", samples=0)
        
        return self._build_node(experiences, depth=0)
    
    def _build_node(
        self,
        experiences: List[ExperienceSample],
        depth: int
    ) -> DecisionNode:
        if depth >= self.max_depth or len(experiences) < self.min_samples:
            return self._create_leaf(experiences)
        
        best_feature, best_threshold = self._find_best_split(experiences)
        
        if best_feature is None:
            return self._create_leaf(experiences)
        
        left_exps, right_exps = self._split(experiences, best_feature, best_threshold)
        
        if not left_exps or not right_exps:
            return self._create_leaf(experiences)
        
        node = DecisionNode(
            feature=best_feature,
            threshold=best_threshold,
            samples=len(experiences)
        )
        
        node.children["left"] = self._build_node(left_exps, depth + 1)
        node.children["right"] = self._build_node(right_exps, depth + 1)
        
        return node
    
    def _create_leaf(self, experiences: List[ExperienceSample]) -> DecisionNode:
        if not experiences:
            return DecisionNode(feature="leaf", samples=0)
        
        action_counts: Counter = Counter()
        for exp in experiences:
            action_key = json.dumps(exp.action, sort_keys=True)
            action_counts[action_key] += 1
        
        best_action_key = action_counts.most_common(1)[0][0] if action_counts else "{}"
        
        return DecisionNode(
            feature="leaf",
            prediction={"action": json.loads(best_action_key)},
            samples=len(experiences)
        )
    
    def _find_best_split(
        self,
        experiences: List[ExperienceSample]
    ) -> Tuple[Optional[str], Optional[float]]:
        best_gain = 0
        best_feature = None
        best_threshold = None
        
        features = set()
        for exp in experiences:
            features.update(exp.state.keys())
        
        for feature in features:
            values = []
            for exp in experiences:
                if feature in exp.state:
                    val = exp.state[feature]
                    if isinstance(val, (int, float)):
                        values.append(val)
            
            if not values:
                continue
            
            thresholds = [min(values) + i * (max(values) - min(values)) / 10
                         for i in range(1, 10)]
            
            for threshold in thresholds:
                gain = self._compute_information_gain(experiences, feature, threshold)
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold
        
        return best_feature, best_threshold
    
    def _compute_information_gain(
        self,
        experiences: List[ExperienceSample],
        feature: str,
        threshold: float
    ) -> float:
        left = [e for e in experiences if e.state.get(feature, 0) <= threshold]
        right = [e for e in experiences if e.state.get(feature, 0) > threshold]
        
        if not left or not right:
            return 0
        
        def entropy(exps):
            if not exps:
                return 0
            outcomes = [e.outcome for e in exps]
            counts = Counter(outcomes)
            total = len(outcomes)
            import math
            return -sum((c / total) * math.log2(c / total) for c in counts.values())
        
        n = len(experiences)
        return entropy(experiences) - (len(left) / n) * entropy(left) - (len(right) / n) * entropy(right)
    
    def _split(
        self,
        experiences: List[ExperienceSample],
        feature: str,
        threshold: float
    ) -> Tuple[List[ExperienceSample], List[ExperienceSample]]:
        left = [e for e in experiences if e.state.get(feature, 0) <= threshold]
        right = [e for e in experiences if e.state.get(feature, 0) > threshold]
        return left, right


class ExperienceDistillerAgent(KnowledgeDistillerAgent):
    def __init__(
        self,
        agent_id: str,
        name: str = "ExperienceDistiller",
        sample_repository: Optional[Any] = None,
        memory_system: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            sample_repository=sample_repository,
            **kwargs
        )
        
        self.memory_system = memory_system
        
        self.behavior_cloner = BehaviorCloner()
        self.irl_learner = InverseReinforcementLearner()
        self.pattern_miner = PatternMiner()
        self.tree_builder = DecisionTreeBuilder()
        
        self.learned_rules: List[Rule] = []
        self.learned_heuristics: List[HeuristicFunction] = []
        self.decision_tree: Optional[DecisionNode] = None
    
    async def distill(
        self,
        samples: List[Dict[str, Any]],
        method: DistillationMethod,
        config: Optional[Dict[str, Any]] = None
    ) -> DistillationResult:
        result = DistillationResult(
            method=method,
            knowledge_type=KnowledgeType.RULES
        )
        
        try:
            experiences = self._convert_to_experiences(samples)
            
            if not experiences:
                result.status = DistillationStatus.FAILED
                result.error_message = "No valid experiences to distill"
                return result
            
            if method == DistillationMethod.BEHAVIOR_CLONING:
                knowledge = self.behavior_cloner.fit(experiences)
                result.knowledge_type = KnowledgeType.MODEL_PARAMETERS
            elif method == DistillationMethod.INVERSE_REINFORCEMENT:
                knowledge = self.irl_learner.infer_reward(experiences)
                result.knowledge_type = KnowledgeType.HEURISTICS
            elif method == DistillationMethod.PATTERN_MINING:
                rules = self.pattern_miner.mine_patterns(experiences)
                knowledge = {"rules": [r.dict() for r in rules]}
                self.learned_rules = rules
            else:
                knowledge = await self._hybrid_distillation(experiences)
            
            self.decision_tree = self.tree_builder.build(experiences)
            
            result.knowledge_artifact = knowledge
            result.status = DistillationStatus.COMPLETED
            result.completed_at = datetime.now()
            result.samples_used = len(experiences)
            
            performance_gain = self._estimate_performance_gain(experiences, knowledge)
            result.performance_gain = performance_gain
            
        except Exception as e:
            self.logger.error(f"Experience distillation failed: {e}")
            result.status = DistillationStatus.FAILED
            result.error_message = str(e)
        
        return result
    
    def _convert_to_experiences(self, samples: List[Dict[str, Any]]) -> List[ExperienceSample]:
        experiences = []
        
        for sample in samples:
            content = sample.get("content", {})
            
            if "decision_trace" in content:
                for step in content["decision_trace"]:
                    exp = ExperienceSample(
                        experience_type=ExperienceType.DECISION_TRACE,
                        agent_id=sample.get("source_agent_id", "unknown"),
                        state=step.get("state", {}),
                        action=step.get("action", {}),
                        reward=step.get("reward", 0),
                        outcome=step.get("outcome", "unknown"),
                        context={"step_info": step.get("info", {})}
                    )
                    experiences.append(exp)
            
            elif "state" in content and "action" in content:
                exp = ExperienceSample(
                    experience_type=ExperienceType.TASK_EXECUTION,
                    agent_id=sample.get("source_agent_id", "unknown"),
                    state=content.get("state", {}),
                    action=content.get("action", {}),
                    reward=content.get("reward", 0),
                    outcome=content.get("outcome", "unknown"),
                    context=content.get("context", {})
                )
                experiences.append(exp)
        
        return experiences
    
    async def _hybrid_distillation(
        self,
        experiences: List[ExperienceSample]
    ) -> Dict[str, Any]:
        knowledge = {}
        
        successful_exps = [e for e in experiences if e.reward > 0]
        if successful_exps:
            knowledge["behavior_policy"] = self.behavior_cloner.fit(successful_exps)
        
        reward_function = self.irl_learner.infer_reward(experiences)
        knowledge["reward_function"] = reward_function
        
        rules = self.pattern_miner.mine_patterns(experiences)
        knowledge["rules"] = [r.dict() for r in rules]
        self.learned_rules = rules
        
        return knowledge
    
    def _estimate_performance_gain(
        self,
        experiences: List[ExperienceSample],
        knowledge: Dict[str, Any]
    ) -> float:
        if not experiences:
            return 0.0
        
        correct_predictions = 0
        total = min(100, len(experiences))
        
        for exp in experiences[:total]:
            predicted_action = self._predict_action(exp.state, knowledge)
            
            if predicted_action:
                similarity = self._action_similarity(predicted_action, exp.action)
                if similarity > 0.5:
                    correct_predictions += 1
        
        baseline_accuracy = 0.3
        current_accuracy = correct_predictions / total if total > 0 else 0
        
        return max(0, current_accuracy - baseline_accuracy)
    
    def _predict_action(
        self,
        state: Dict[str, Any],
        knowledge: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if "behavior_policy" in knowledge:
            policy = knowledge["behavior_policy"]
            state_key = json.dumps(state, sort_keys=True)[:200]
            if state_key in policy:
                return policy[state_key]
        
        if self.decision_tree:
            return self._traverse_tree(state, self.decision_tree)
        
        return None
    
    def _traverse_tree(
        self,
        state: Dict[str, Any],
        node: DecisionNode
    ) -> Optional[Dict[str, Any]]:
        if node.feature == "leaf":
            return node.prediction.get("action") if node.prediction else None
        
        value = state.get(node.feature, 0)
        
        if isinstance(value, (int, float)) and node.threshold is not None:
            if value <= node.threshold:
                return self._traverse_tree(state, node.children.get("left", node))
            else:
                return self._traverse_tree(state, node.children.get("right", node))
        
        return None
    
    def _action_similarity(
        self,
        action1: Dict[str, Any],
        action2: Dict[str, Any]
    ) -> float:
        keys1 = set(action1.keys())
        keys2 = set(action2.keys())
        
        if not keys1 and not keys2:
            return 1.0
        
        if not keys1 or not keys2:
            return 0.0
        
        common_keys = keys1 & keys2
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if action1[key] == action2[key]:
                matches += 1
        
        return matches / len(common_keys)
    
    async def evaluate(
        self,
        model_id: str,
        test_samples: List[Dict[str, Any]]
    ) -> float:
        test_experiences = self._convert_to_experiences(test_samples)
        
        if not test_experiences:
            return 0.0
        
        correct = 0
        for exp in test_experiences:
            if self.decision_tree:
                predicted = self._traverse_tree(exp.state, self.decision_tree)
                if predicted and self._action_similarity(predicted, exp.action) > 0.5:
                    correct += 1
        
        return correct / len(test_experiences)
    
    async def get_user_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.memory_system:
            return {}
        
        try:
            preferences = await self.memory_system.get_user_preferences(user_id)
            return preferences
        except Exception as e:
            self.logger.error(f"Error getting user preferences: {e}")
            return {}
    
    async def get_collaboration_patterns(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": rule.rule_id,
                "condition": rule.condition,
                "action": rule.action,
                "confidence": rule.confidence,
                "support": rule.support
            }
            for rule in self.learned_rules
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        stats = super().get_statistics()
        stats.update({
            "learned_rules_count": len(self.learned_rules),
            "learned_heuristics_count": len(self.learned_heuristics),
            "has_decision_tree": self.decision_tree is not None,
            "irl_features": len(self.irl_learner.reward_weights)
        })
        return stats
