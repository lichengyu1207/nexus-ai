"""
业务智能体生命指数评估
Business Agent Life Index Evaluator

评估业务智能体的活体程度
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

logger = logging.getLogger(__name__)


class EvaluationGrade(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class LifeIndex:
    agent_id: str
    adaptability: float
    learning_efficiency: float
    collaboration_degree: float
    emergent_intelligence: float
    reproduction_health: float
    overall_score: float
    grade: EvaluationGrade
    evaluated_at: float
    details: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "adaptability": self.adaptability,
            "learning_efficiency": self.learning_efficiency,
            "collaboration_degree": self.collaboration_degree,
            "emergent_intelligence": self.emergent_intelligence,
            "reproduction_health": self.reproduction_health,
            "overall_score": self.overall_score,
            "grade": self.grade.value,
            "evaluated_at": self.evaluated_at,
            "details": self.details
        }


@dataclass
class EvaluationReport:
    report_id: str
    timestamp: float
    agent_indices: List[LifeIndex]
    population_summary: Dict
    recommendations: List[Dict]
    trends: Dict
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "agent_indices": [idx.to_dict() for idx in self.agent_indices],
            "population_summary": self.population_summary,
            "recommendations": self.recommendations,
            "trends": self.trends
        }


class LifeIndexEvaluator:
    """
    业务智能体生命指数评估系统
    
    评估维度：
    1. 适应性：面对新场景的应对成功率
    2. 学习效率：每单位能量获得的知识增益
    3. 协作度：自发形成的协作团队数量
    4. 涌现智能：解决非预设任务的能力
    5. 繁殖健康：种群多样性、优秀血统传承
    """
    
    WEIGHTS = {
        "adaptability": 0.25,
        "learning_efficiency": 0.20,
        "collaboration_degree": 0.20,
        "emergent_intelligence": 0.20,
        "reproduction_health": 0.15,
    }
    
    GRADE_THRESHOLDS = {
        EvaluationGrade.EXCELLENT: 0.9,
        EvaluationGrade.GOOD: 0.75,
        EvaluationGrade.AVERAGE: 0.5,
        EvaluationGrade.POOR: 0.3,
    }
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        evaluation_interval: float = 3600,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.evaluation_interval = evaluation_interval
        
        self.evaluations: Dict[str, LifeIndex] = {}
        self.evaluation_history: Dict[str, List[LifeIndex]] = defaultdict(list)
        self.reports: deque = deque(maxlen=100)
        
        self._lock = threading.RLock()
        self._running = False
        self._evaluator_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "total_evaluations": 0,
            "avg_overall_score": 0.0,
            "excellent_count": 0,
            "good_count": 0,
            "average_count": 0,
            "poor_count": 0,
            "critical_count": 0,
        }
    
    async def start(self):
        self._running = True
        self._evaluator_task = asyncio.create_task(self._evaluation_loop())
        logger.info("Life index evaluator started")
    
    async def stop(self):
        self._running = False
        if self._evaluator_task:
            self._evaluator_task.cancel()
            try:
                await self._evaluator_task
            except asyncio.CancelledError:
                pass
        logger.info("Life index evaluator stopped")
    
    async def _evaluation_loop(self):
        while self._running:
            try:
                await asyncio.sleep(self.evaluation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evaluation loop: {e}")
    
    async def evaluate_agent(
        self,
        agent: Any,
        context: Optional[Dict] = None,
    ) -> LifeIndex:
        agent_id = agent.agent_id
        
        adaptability = self._evaluate_adaptability(agent, context)
        learning_efficiency = self._evaluate_learning_efficiency(agent)
        collaboration_degree = self._evaluate_collaboration_degree(agent)
        emergent_intelligence = self._evaluate_emergent_intelligence(agent, context)
        reproduction_health = self._evaluate_reproduction_health(agent)
        
        overall_score = (
            adaptability * self.WEIGHTS["adaptability"] +
            learning_efficiency * self.WEIGHTS["learning_efficiency"] +
            collaboration_degree * self.WEIGHTS["collaboration_degree"] +
            emergent_intelligence * self.WEIGHTS["emergent_intelligence"] +
            reproduction_health * self.WEIGHTS["reproduction_health"]
        )
        
        grade = self._determine_grade(overall_score)
        
        index = LifeIndex(
            agent_id=agent_id,
            adaptability=adaptability,
            learning_efficiency=learning_efficiency,
            collaboration_degree=collaboration_degree,
            emergent_intelligence=emergent_intelligence,
            reproduction_health=reproduction_health,
            overall_score=overall_score,
            grade=grade,
            evaluated_at=time.time(),
            details={
                "energy": agent.energy,
                "age": agent.age,
                "generation": getattr(agent, 'generation', 0),
                "tasks_completed": agent.stats.get("tasks_completed", 0),
                "success_rate": agent.stats.get("tasks_success_rate", 0),
            }
        )
        
        with self._lock:
            self.evaluations[agent_id] = index
            self.evaluation_history[agent_id].append(index)
            
            self.stats["total_evaluations"] += 1
            self._update_grade_stats(grade)
            
            old_avg = self.stats["avg_overall_score"]
            count = self.stats["total_evaluations"]
            self.stats["avg_overall_score"] = (
                old_avg * (count - 1) + overall_score
            ) / count
        
        return index
    
    def _evaluate_adaptability(self, agent: Any, context: Optional[Dict]) -> float:
        success_rate = agent.stats.get("tasks_success_rate", 0.5)
        
        experience_count = len(agent.experience_buffer) if hasattr(agent, 'experience_buffer') else 0
        experience_factor = min(1.0, experience_count / 500)
        
        gene_diversity = 0.5
        if hasattr(agent, 'gene_pool') and hasattr(agent.gene_pool, 'genes'):
            gene_diversity = len(agent.gene_pool.genes) / 10
        
        return (
            success_rate * 0.5 +
            experience_factor * 0.3 +
            gene_diversity * 0.2
        )
    
    def _evaluate_learning_efficiency(self, agent: Any) -> float:
        learning_sessions = agent.stats.get("learning_sessions", 0)
        
        energy_earned = agent.stats.get("energy_earned", 1)
        energy_spent = agent.stats.get("energy_spent", 1)
        
        if energy_spent > 0:
            efficiency = min(1.0, energy_earned / energy_spent)
        else:
            efficiency = 0.5
        
        learning_factor = min(1.0, learning_sessions / 10)
        
        return efficiency * 0.7 + learning_factor * 0.3
    
    def _evaluate_collaboration_degree(self, agent: Any) -> float:
        collaborations = agent.stats.get("collaborations", 0)
        
        alliance_count = len(agent.alliance_ids) if hasattr(agent, 'alliance_ids') else 0
        
        cooperation_tendency = 0.5
        if hasattr(agent, 'gene_pool'):
            cooperation_tendency = agent.gene_pool.get_gene_value("cooperation_tendency", 0.5)
        
        collab_factor = min(1.0, collaborations / 20)
        alliance_factor = min(1.0, alliance_count / 5)
        
        return (
            collab_factor * 0.4 +
            alliance_factor * 0.3 +
            cooperation_tendency * 0.3
        )
    
    def _evaluate_emergent_intelligence(
        self,
        agent: Any,
        context: Optional[Dict],
    ) -> float:
        tasks_completed = agent.stats.get("tasks_completed", 0)
        
        user_satisfaction = agent.stats.get("user_satisfaction", 0.5)
        
        success_rate = agent.stats.get("tasks_success_rate", 0.5)
        
        emergent_factor = 0
        if success_rate > 0.8 and user_satisfaction > 0.7:
            emergent_factor = 0.3
        elif success_rate > 0.6 and user_satisfaction > 0.5:
            emergent_factor = 0.1
        
        task_factor = min(1.0, tasks_completed / 50)
        
        return (
            task_factor * 0.4 +
            user_satisfaction * 0.3 +
            emergent_factor + success_rate * 0.3
        ) / (0.4 + 0.3 + emergent_factor + 0.3 if emergent_factor > 0 else 1.0)
    
    def _evaluate_reproduction_health(self, agent: Any) -> float:
        children_count = len(agent.children_ids) if hasattr(agent, 'children_ids') else 0
        
        generation = getattr(agent, 'generation', 0)
        generation_factor = min(1.0, generation / 10)
        
        energy_health = agent.energy / agent.max_energy if hasattr(agent, 'max_energy') else agent.energy / 100
        
        reproduction_factor = min(1.0, children_count / 5)
        
        return (
            reproduction_factor * 0.4 +
            generation_factor * 0.3 +
            energy_health * 0.3
        )
    
    def _determine_grade(self, score: float) -> EvaluationGrade:
        if score >= self.GRADE_THRESHOLDS[EvaluationGrade.EXCELLENT]:
            return EvaluationGrade.EXCELLENT
        elif score >= self.GRADE_THRESHOLDS[EvaluationGrade.GOOD]:
            return EvaluationGrade.GOOD
        elif score >= self.GRADE_THRESHOLDS[EvaluationGrade.AVERAGE]:
            return EvaluationGrade.AVERAGE
        elif score >= self.GRADE_THRESHOLDS[EvaluationGrade.POOR]:
            return EvaluationGrade.POOR
        else:
            return EvaluationGrade.CRITICAL
    
    def _update_grade_stats(self, grade: EvaluationGrade):
        if grade == EvaluationGrade.EXCELLENT:
            self.stats["excellent_count"] += 1
        elif grade == EvaluationGrade.GOOD:
            self.stats["good_count"] += 1
        elif grade == EvaluationGrade.AVERAGE:
            self.stats["average_count"] += 1
        elif grade == EvaluationGrade.POOR:
            self.stats["poor_count"] += 1
        else:
            self.stats["critical_count"] += 1
    
    async def generate_report(
        self,
        agents: List[Any],
    ) -> EvaluationReport:
        indices = []
        for agent in agents:
            index = await self.evaluate_agent(agent)
            indices.append(index)
        
        population_summary = self._calculate_population_summary(indices)
        
        recommendations = self._generate_recommendations(indices)
        
        trends = self._calculate_trends()
        
        report = EvaluationReport(
            report_id=f"report_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            agent_indices=indices,
            population_summary=population_summary,
            recommendations=recommendations,
            trends=trends,
        )
        
        with self._lock:
            self.reports.append(report)
        
        if self.memory_agent:
            await self._store_report(report)
        
        return report
    
    def _calculate_population_summary(self, indices: List[LifeIndex]) -> Dict:
        if not indices:
            return {}
        
        return {
            "total_agents": len(indices),
            "avg_adaptability": sum(i.adaptability for i in indices) / len(indices),
            "avg_learning_efficiency": sum(i.learning_efficiency for i in indices) / len(indices),
            "avg_collaboration_degree": sum(i.collaboration_degree for i in indices) / len(indices),
            "avg_emergent_intelligence": sum(i.emergent_intelligence for i in indices) / len(indices),
            "avg_reproduction_health": sum(i.reproduction_health for i in indices) / len(indices),
            "avg_overall_score": sum(i.overall_score for i in indices) / len(indices),
            "grade_distribution": {
                grade.value: sum(1 for i in indices if i.grade == grade)
                for grade in EvaluationGrade
            }
        }
    
    def _generate_recommendations(self, indices: List[LifeIndex]) -> List[Dict]:
        recommendations = []
        
        avg_adaptability = sum(i.adaptability for i in indices) / len(indices) if indices else 0
        if avg_adaptability < 0.5:
            recommendations.append({
                "type": "adaptability_improvement",
                "priority": "high",
                "description": "Consider increasing exploration rate or mutation frequency",
                "target_metric": "adaptability",
                "current_value": avg_adaptability,
                "target_value": 0.6
            })
        
        avg_collaboration = sum(i.collaboration_degree for i in indices) / len(indices) if indices else 0
        if avg_collaboration < 0.4:
            recommendations.append({
                "type": "collaboration_improvement",
                "priority": "medium",
                "description": "Increase cooperation tendency gene weight",
                "target_metric": "collaboration_degree",
                "current_value": avg_collaboration,
                "target_value": 0.5
            })
        
        critical_agents = [i for i in indices if i.grade == EvaluationGrade.CRITICAL]
        if critical_agents:
            recommendations.append({
                "type": "critical_agents",
                "priority": "critical",
                "description": f"{len(critical_agents)} agents in critical state need attention",
                "agent_ids": [i.agent_id for i in critical_agents]
            })
        
        return recommendations
    
    def _calculate_trends(self) -> Dict:
        trends = {}
        
        for agent_id, history in self.evaluation_history.items():
            if len(history) >= 2:
                recent = history[-1].overall_score
                previous = history[-2].overall_score
                change = recent - previous
                
                trends[agent_id] = {
                    "direction": "improving" if change > 0.05 else "declining" if change < -0.05 else "stable",
                    "change": change,
                    "recent_score": recent
                }
        
        return trends
    
    async def _store_report(self, report: EvaluationReport):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "life_index_report",
                    "report": report.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store report: {e}")
    
    def get_agent_index(self, agent_id: str) -> Optional[LifeIndex]:
        return self.evaluations.get(agent_id)
    
    def get_agent_history(self, agent_id: str) -> List[LifeIndex]:
        return self.evaluation_history.get(agent_id, [])
    
    def get_latest_report(self) -> Optional[EvaluationReport]:
        if self.reports:
            return self.reports[-1]
        return None
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "agents_evaluated": len(self.evaluations),
                "reports_generated": len(self.reports),
            }
