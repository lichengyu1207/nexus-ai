"""
蜂群学习与进化智能体
负责从蜂群的防御经验中学习，持续进化防御能力
"""
import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class LearningType(Enum):
    """学习类型"""
    FEDERATED = "federated"
    REINFORCEMENT = "reinforcement"
    EVOLUTIONARY = "evolutionary"
    DISTILLATION = "distillation"


class ExperienceType(Enum):
    """经验类型"""
    SUCCESSFUL_DEFENSE = "successful_defense"
    FAILED_DEFENSE = "failed_defense"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    NEW_ATTACK = "new_attack"


class EvolutionStatus(Enum):
    """进化状态"""
    PENDING = "pending"
    TRAINING = "training"
    EVALUATING = "evaluating"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


@dataclass
class DefenseExperience:
    """防御经验"""
    experience_id: str
    experience_type: ExperienceType
    agent_id: str
    attack_type: str
    attack_features: Dict[str, Any]
    defense_action: str
    outcome: str
    reward: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningModel:
    """学习模型"""
    model_id: str
    version: str
    model_type: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    created_at: datetime
    training_samples: int


@dataclass
class EvolutionResult:
    """进化结果"""
    evolution_id: str
    status: EvolutionStatus
    old_model_id: str
    new_model_id: str
    improvement: float
    validation_score: float
    deployed_at: Optional[datetime]
    rollback_available: bool


class SwarmLearningEvolutionAgent:
    """蜂群学习与进化智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "SwarmLearningEvolutionAgent"
        self.config = config or {}
        self.experience_buffer: List[DefenseExperience] = []
        self.models: Dict[str, LearningModel] = {}
        self.current_model_id: Optional[str] = None
        self.evolution_history: List[EvolutionResult] = []
        self.agent_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: {"score": 0.5, "samples": 0})
        self.reward_config = self._init_reward_config()
        self.evolution_config = self._init_evolution_config()
        self.stats = {
            "total_experiences": 0,
            "total_evolutions": 0,
            "successful_evolutions": 0,
            "rolled_back_evolutions": 0,
            "avg_improvement": 0.0,
        }
    
    def _init_reward_config(self) -> Dict[str, float]:
        """初始化奖励配置"""
        return {
            "successful_defense": 1.0,
            "failed_defense": -1.0,
            "false_positive": -0.5,
            "false_negative": -2.0,
            "new_attack_detected": 0.5,
            "early_detection_bonus": 0.3,
            "low_latency_bonus": 0.2,
        }
    
    def _init_evolution_config(self) -> Dict[str, Any]:
        """初始化进化配置"""
        return {
            "min_samples_for_evolution": 100,
            "evolution_interval": 3600,
            "improvement_threshold": 0.05,
            "max_rollback_time": 3600,
            "population_size": 10,
            "mutation_rate": 0.1,
            "crossover_rate": 0.7,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        
        initial_model = self._create_initial_model()
        self.models[initial_model.model_id] = initial_model
        self.current_model_id = initial_model.model_id
        
        return True
    
    def _create_initial_model(self) -> LearningModel:
        """创建初始模型"""
        return LearningModel(
            model_id="model_initial_v1",
            version="1.0.0",
            model_type="defense_classifier",
            parameters={
                "threshold": 0.5,
                "weights": {},
                "rules": []
            },
            performance_metrics={
                "accuracy": 0.5,
                "precision": 0.5,
                "recall": 0.5,
                "f1_score": 0.5,
            },
            created_at=datetime.now(),
            training_samples=0
        )
    
    def record_experience(
        self,
        agent_id: str,
        experience_type: ExperienceType,
        attack_type: str,
        attack_features: Dict[str, Any],
        defense_action: str,
        outcome: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """记录经验"""
        experience_id = f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.experience_buffer)}"
        
        reward = self._calculate_reward(experience_type, metadata)
        
        experience = DefenseExperience(
            experience_id=experience_id,
            experience_type=experience_type,
            agent_id=agent_id,
            attack_type=attack_type,
            attack_features=attack_features,
            defense_action=defense_action,
            outcome=outcome,
            reward=reward,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.experience_buffer.append(experience)
        self.stats["total_experiences"] += 1
        
        self._update_agent_performance(agent_id, experience_type, reward)
        
        return experience_id
    
    def _calculate_reward(
        self, 
        experience_type: ExperienceType,
        metadata: Dict[str, Any]
    ) -> float:
        """计算奖励"""
        base_reward = self.reward_config.get(experience_type.value, 0)
        
        bonus = 0.0
        if metadata:
            if metadata.get("early_detection", False):
                bonus += self.reward_config["early_detection_bonus"]
            if metadata.get("low_latency", False):
                bonus += self.reward_config["low_latency_bonus"]
        
        return base_reward + bonus
    
    def _update_agent_performance(
        self,
        agent_id: str,
        experience_type: ExperienceType,
        reward: float
    ):
        """更新智能体性能"""
        current = self.agent_performance[agent_id]
        current["samples"] += 1
        
        alpha = 0.1
        current["score"] = current["score"] * (1 - alpha) + (reward + 1) / 2 * alpha
    
    def federated_learning_round(self) -> Dict[str, Any]:
        """联邦学习轮次"""
        if len(self.experience_buffer) < self.evolution_config["min_samples_for_evolution"]:
            return {"status": "insufficient_data", "samples": len(self.experience_buffer)}
        
        agent_updates: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"gradients": {}, "samples": 0})
        
        for exp in self.experience_buffer[-1000:]:
            agent_id = exp.agent_id
            
            for feature, value in exp.attack_features.items():
                if feature not in agent_updates[agent_id]["gradients"]:
                    agent_updates[agent_id]["gradients"][feature] = 0
                agent_updates[agent_id]["gradients"][feature] += value * exp.reward
            
            agent_updates[agent_id]["samples"] += 1
        
        aggregated_gradients: Dict[str, float] = defaultdict(float)
        total_samples = 0
        
        for agent_id, update in agent_updates.items():
            weight = update["samples"] / max(1, sum(u["samples"] for u in agent_updates.values()))
            total_samples += update["samples"]
            
            for feature, gradient in update["gradients"].items():
                aggregated_gradients[feature] += gradient * weight
        
        current_model = self.models.get(self.current_model_id)
        if current_model:
            new_parameters = current_model.parameters.copy()
            
            for feature, gradient in aggregated_gradients.items():
                if "weights" not in new_parameters:
                    new_parameters["weights"] = {}
                new_parameters["weights"][feature] = gradient / max(1, total_samples)
            
            new_model = LearningModel(
                model_id=f"model_fl_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                version=f"{len(self.models) + 1}.0.0",
                model_type="defense_classifier",
                parameters=new_parameters,
                performance_metrics=current_model.performance_metrics.copy(),
                created_at=datetime.now(),
                training_samples=total_samples
            )
            
            self.models[new_model.model_id] = new_model
            
            return {
                "status": "completed",
                "new_model_id": new_model.model_id,
                "aggregated_samples": total_samples,
                "participating_agents": len(agent_updates)
            }
        
        return {"status": "no_current_model"}
    
    def reinforcement_learning_update(self) -> Dict[str, Any]:
        """强化学习更新"""
        recent_experiences = self.experience_buffer[-100:]
        
        if len(recent_experiences) < 10:
            return {"status": "insufficient_data"}
        
        state_action_values: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        for exp in recent_experiences:
            state_key = self._extract_state_key(exp.attack_features)
            state_action_values[state_key][exp.defense_action].append(exp.reward)
        
        policy_updates: Dict[str, str] = {}
        
        for state_key, actions in state_action_values.items():
            best_action = max(actions.keys(), key=lambda a: sum(actions[a]) / len(actions[a]))
            policy_updates[state_key] = best_action
        
        current_model = self.models.get(self.current_model_id)
        if current_model:
            new_parameters = current_model.parameters.copy()
            if "policy" not in new_parameters:
                new_parameters["policy"] = {}
            new_parameters["policy"].update(policy_updates)
            
            new_model = LearningModel(
                model_id=f"model_rl_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                version=f"{len(self.models) + 1}.0.0",
                model_type="defense_policy",
                parameters=new_parameters,
                performance_metrics=current_model.performance_metrics.copy(),
                created_at=datetime.now(),
                training_samples=len(recent_experiences)
            )
            
            self.models[new_model.model_id] = new_model
            
            return {
                "status": "completed",
                "new_model_id": new_model.model_id,
                "policy_updates": len(policy_updates)
            }
        
        return {"status": "no_current_model"}
    
    def _extract_state_key(self, features: Dict[str, Any]) -> str:
        """提取状态键"""
        key_features = ["attack_type", "severity", "source"]
        key_values = [str(features.get(k, "unknown")) for k in key_features]
        return "_".join(key_values)
    
    def evolutionary_optimization(self) -> EvolutionResult:
        """进化优化"""
        population_size = self.evolution_config["population_size"]
        mutation_rate = self.evolution_config["mutation_rate"]
        
        current_model = self.models.get(self.current_model_id)
        if not current_model:
            return self._create_failed_evolution("No current model")
        
        population = [current_model.parameters.copy() for _ in range(population_size)]
        
        for i in range(1, population_size):
            population[i] = self._mutate_parameters(population[i], mutation_rate)
        
        best_params = None
        best_score = -float("inf")
        
        for params in population:
            score = self._evaluate_parameters(params)
            if score > best_score:
                best_score = score
                best_params = params
        
        improvement = best_score - self._evaluate_parameters(current_model.parameters)
        
        if improvement > self.evolution_config["improvement_threshold"]:
            new_model = LearningModel(
                model_id=f"model_evo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                version=f"{len(self.models) + 1}.0.0",
                model_type="defense_classifier",
                parameters=best_params,
                performance_metrics={"validation_score": best_score},
                created_at=datetime.now(),
                training_samples=len(self.experience_buffer)
            )
            
            self.models[new_model.model_id] = new_model
            
            old_model_id = self.current_model_id
            self.current_model_id = new_model.model_id
            
            result = EvolutionResult(
                evolution_id=f"evo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                status=EvolutionStatus.DEPLOYED,
                old_model_id=old_model_id,
                new_model_id=new_model.model_id,
                improvement=improvement,
                validation_score=best_score,
                deployed_at=datetime.now(),
                rollback_available=True
            )
            
            self.evolution_history.append(result)
            self.stats["total_evolutions"] += 1
            self.stats["successful_evolutions"] += 1
            self._update_avg_improvement(improvement)
            
            return result
        
        return self._create_failed_evolution("No improvement achieved")
    
    def _mutate_parameters(self, params: Dict[str, Any], rate: float) -> Dict[str, Any]:
        """变异参数"""
        import random
        
        mutated = params.copy()
        
        if "threshold" in mutated:
            if random.random() < rate:
                mutated["threshold"] = max(0.1, min(0.9, mutated["threshold"] + random.uniform(-0.1, 0.1)))
        
        if "weights" in mutated:
            for key in mutated["weights"]:
                if random.random() < rate:
                    mutated["weights"][key] *= random.uniform(0.8, 1.2)
        
        return mutated
    
    def _evaluate_parameters(self, params: Dict[str, Any]) -> float:
        """评估参数"""
        recent_experiences = self.experience_buffer[-200:]
        
        if not recent_experiences:
            return 0.5
        
        correct = 0
        total = 0
        
        threshold = params.get("threshold", 0.5)
        
        for exp in recent_experiences:
            total += 1
            
            if exp.experience_type == ExperienceType.SUCCESSFUL_DEFENSE:
                correct += 1
            elif exp.experience_type == ExperienceType.FAILED_DEFENSE:
                pass
            elif exp.experience_type == ExperienceType.FALSE_POSITIVE:
                correct -= 0.5
            elif exp.experience_type == ExperienceType.FALSE_NEGATIVE:
                correct -= 1
        
        return max(0, correct / max(1, total))
    
    def _create_failed_evolution(self, reason: str) -> EvolutionResult:
        """创建失败进化结果"""
        return EvolutionResult(
            evolution_id=f"evo_failed_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status=EvolutionStatus.PENDING,
            old_model_id=self.current_model_id or "none",
            new_model_id="none",
            improvement=0.0,
            validation_score=0.0,
            deployed_at=None,
            rollback_available=False
        )
    
    def _update_avg_improvement(self, improvement: float):
        """更新平均改进"""
        successful = self.stats["successful_evolutions"]
        current_avg = self.stats["avg_improvement"]
        self.stats["avg_improvement"] = (current_avg * (successful - 1) + improvement) / successful
    
    def rollback_evolution(self, evolution_id: str) -> bool:
        """回滚进化"""
        for result in reversed(self.evolution_history):
            if result.evolution_id == evolution_id and result.rollback_available:
                if result.old_model_id in self.models:
                    self.current_model_id = result.old_model_id
                    result.status = EvolutionStatus.ROLLED_BACK
                    self.stats["rolled_back_evolutions"] += 1
                    return True
        return False
    
    def distill_knowledge(self) -> Dict[str, Any]:
        """知识蒸馏"""
        experiences = self.experience_buffer[-500:]
        
        if len(experiences) < 50:
            return {"status": "insufficient_data"}
        
        rules: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "success": 0})
        
        for exp in experiences:
            state_key = self._extract_state_key(exp.attack_features)
            rules[state_key]["count"] += 1
            if exp.experience_type == ExperienceType.SUCCESSFUL_DEFENSE:
                rules[state_key]["success"] += 1
                rules[state_key]["best_action"] = exp.defense_action
        
        distilled_rules = []
        for state_key, data in rules.items():
            if data["count"] >= 5 and data["success"] / data["count"] > 0.7:
                distilled_rules.append({
                    "state": state_key,
                    "action": data.get("best_action", "block"),
                    "confidence": data["success"] / data["count"],
                    "samples": data["count"]
                })
        
        current_model = self.models.get(self.current_model_id)
        if current_model and distilled_rules:
            new_parameters = current_model.parameters.copy()
            new_parameters["rules"] = distilled_rules
            
            new_model = LearningModel(
                model_id=f"model_distill_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                version=f"{len(self.models) + 1}.0.0",
                model_type="defense_rules",
                parameters=new_parameters,
                performance_metrics=current_model.performance_metrics.copy(),
                created_at=datetime.now(),
                training_samples=len(experiences)
            )
            
            self.models[new_model.model_id] = new_model
            
            return {
                "status": "completed",
                "new_model_id": new_model.model_id,
                "rules_distilled": len(distilled_rules)
            }
        
        return {"status": "no_rules_distilled"}
    
    def get_current_model(self) -> Optional[LearningModel]:
        """获取当前模型"""
        return self.models.get(self.current_model_id)
    
    def get_agent_rankings(self) -> List[Dict[str, Any]]:
        """获取智能体排名"""
        rankings = [
            {"agent_id": agent_id, "score": data["score"], "samples": data["samples"]}
            for agent_id, data in self.agent_performance.items()
        ]
        return sorted(rankings, key=lambda x: x["score"], reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "total_models": len(self.models),
            "experience_buffer_size": len(self.experience_buffer),
            "current_model_id": self.current_model_id,
        }
