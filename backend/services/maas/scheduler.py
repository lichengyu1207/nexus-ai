# -*- coding: utf-8 -*-
"""
MaAS 动态调度服务
实现多智能体架构搜索与动态调度
"""
import asyncpg
import uuid
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from backend.services.maas.models import (
    AgentOperator, ArchitectureTemplate, TaskFeature, 
    SchedulingDecision, SchedulingResult
)

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"


class TaskAnalyzer:
    def __init__(self):
        self.task_patterns = {
            "qa": ["什么", "怎么", "如何", "为什么", "多少", "哪", "是否"],
            "analysis": ["分析", "评估", "比较", "预测", "趋势"],
            "report": ["报告", "生成", "详细", "完整", "综合"],
            "query": ["查询", "搜索", "查找", "获取", "显示"],
            "consultation": ["建议", "推荐", "咨询", "意见", "方案"]
        }
        
        self.complexity_keywords = {
            "high": ["详细", "完整", "综合", "全面", "深度", "专业"],
            "medium": ["分析", "评估", "比较", "预测", "建议"],
            "low": ["查询", "简单", "快速", "基础"]
        }
    
    def analyze(self, task_content: str) -> TaskFeature:
        task_type = self._classify_task_type(task_content)
        keywords = self._extract_keywords(task_content)
        entities = self._extract_entities(task_content)
        
        return TaskFeature(
            content=task_content,
            task_type=task_type,
            length=len(task_content),
            keywords=keywords,
            entities=entities
        )
    
    def _classify_task_type(self, content: str) -> str:
        content_lower = content.lower()
        
        for task_type, patterns in self.task_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return task_type
        
        return "general"
    
    def _extract_keywords(self, content: str) -> List[str]:
        keywords = []
        for level, kws in self.complexity_keywords.items():
            for kw in kws:
                if kw in content:
                    keywords.append(kw)
        return keywords
    
    def _extract_entities(self, content: str) -> List[str]:
        patterns = [
            r'[\u4e00-\u9fa5]{2,}(?:市|区|县)',
            r'\d+(?:万|千|百)?(?:元|块)',
            r'[\u4e00-\u9fa5]{2,}(?:房|楼盘|小区)'
        ]
        
        entities = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            entities.extend(matches)
        
        return list(set(entities))


class ComplexityEstimator:
    def __init__(self):
        self.weights = {
            "length": 0.2,
            "keywords": 0.3,
            "task_type": 0.3,
            "entities": 0.2
        }
        
        self.task_type_scores = {
            "qa": 0.2,
            "query": 0.25,
            "consultation": 0.4,
            "analysis": 0.6,
            "report": 0.85,
            "general": 0.5
        }
    
    def estimate(self, feature: TaskFeature) -> float:
        length_score = min(feature.length / 200, 1.0)
        
        keyword_score = 0.0
        high_count = sum(1 for kw in feature.keywords if kw in ["详细", "完整", "综合", "全面", "深度", "专业"])
        medium_count = sum(1 for kw in feature.keywords if kw in ["分析", "评估", "比较", "预测", "建议"])
        keyword_score = min((high_count * 0.3 + medium_count * 0.15), 1.0)
        
        task_type_score = self.task_type_scores.get(feature.task_type, 0.5)
        
        entity_score = min(len(feature.entities) * 0.1, 1.0)
        
        complexity = (
            self.weights["length"] * length_score +
            self.weights["keywords"] * keyword_score +
            self.weights["task_type"] * task_type_score +
            self.weights["entities"] * entity_score
        )
        
        return round(min(max(complexity, 0.0), 1.0), 3)


class DynamicScheduler:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.task_analyzer = TaskAnalyzer()
        self.complexity_estimator = ComplexityEstimator()
        self._operators: Dict[str, AgentOperator] = {}
        self._templates: List[ArchitectureTemplate] = []
    
    async def initialize(self):
        await self._load_operators()
        await self._load_templates()
    
    async def _load_operators(self):
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM agent_operators WHERE is_active = TRUE"
            )
            self._operators = {
                row["name"]: AgentOperator.from_db_row(dict(row))
                for row in rows
            }
    
    async def _load_templates(self):
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM architecture_templates WHERE is_active = TRUE ORDER BY complexity_range_min"
            )
            self._templates = [ArchitectureTemplate.from_db_row(dict(row)) for row in rows]
    
    async def schedule(self, task_content: str, user_id: str = None) -> SchedulingResult:
        feature = self.task_analyzer.analyze(task_content)
        complexity = self.complexity_estimator.estimate(feature)
        feature.complexity_score = complexity
        
        architecture = self._select_architecture(complexity)
        
        agents = []
        for agent_name in architecture.agent_sequence:
            if agent_name in self._operators:
                agents.append(self._operators[agent_name])
        
        estimated_cost = sum(a.cost_estimate for a in agents)
        estimated_latency = sum(a.latency_estimate for a in agents)
        
        return SchedulingResult(
            architecture=architecture,
            agents=agents,
            estimated_cost=round(estimated_cost, 3),
            estimated_latency=round(estimated_latency, 2),
            complexity_score=complexity
        )
    
    def _select_architecture(self, complexity: float) -> ArchitectureTemplate:
        for template in self._templates:
            if template.matches_complexity(complexity):
                return template
        
        return self._templates[-1] if self._templates else ArchitectureTemplate(
            id="default",
            name="default",
            agent_sequence=["li_bu", "hu_bu"]
        )
    
    async def record_decision(
        self,
        user_id: str,
        task_content: str,
        result: SchedulingResult,
        execution_time: float,
        success: bool,
        result_summary: str = ""
    ) -> str:
        decision_id = str(uuid.uuid4())
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scheduling_decisions 
                (id, user_id, task_content, task_type, task_features, complexity_score,
                 selected_architecture_id, selected_architecture_name, agent_invocations,
                 execution_time, total_cost, success, result_summary)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """, decision_id, user_id, task_content, 
                self.task_analyzer.analyze(task_content).task_type,
                json.dumps({"keywords": self.task_analyzer.analyze(task_content).keywords}),
                result.complexity_score,
                result.architecture.id,
                result.architecture.name,
                json.dumps([{"agent": a.name, "cost": a.cost_estimate} for a in result.agents]),
                execution_time,
                result.estimated_cost,
                success,
                result_summary
            )
            
            await conn.execute("""
                UPDATE architecture_templates 
                SET use_count = use_count + 1,
                    success_rate = (success_rate * use_count + $1) / (use_count + 1)
                WHERE id = $2
            """, 1.0 if success else 0.0, result.architecture.id)
        
        return decision_id
    
    async def get_operators(self) -> List[AgentOperator]:
        return list(self._operators.values())
    
    async def get_templates(self) -> List[ArchitectureTemplate]:
        return self._templates
    
    async def get_decision_history(self, user_id: str, limit: int = 20) -> List[SchedulingDecision]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM scheduling_decisions 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, user_id, limit)
            
            return [SchedulingDecision.from_db_row(dict(row)) for row in rows]


_maas_scheduler: Optional[DynamicScheduler] = None


def get_maas_scheduler() -> Optional[DynamicScheduler]:
    return _maas_scheduler


async def init_maas_scheduler(db_pool) -> DynamicScheduler:
    global _maas_scheduler
    _maas_scheduler = DynamicScheduler(db_pool)
    await _maas_scheduler.initialize()
    return _maas_scheduler
