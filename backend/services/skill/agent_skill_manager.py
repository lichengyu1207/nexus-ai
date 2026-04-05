# -*- coding: utf-8 -*-
"""
Agent Skill Integration
Integrates skills with six ministries agents
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid


@dataclass
class AgentSkillBinding:
    agent_id: str
    agent_type: str
    skill_id: str
    skill_name: str
    proficiency: int = 0
    use_count: int = 0
    is_active: bool = True
    learned_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None


class AgentSkillManager:
    AGENT_SKILL_RECOMMENDATIONS = {
        "libu": {
            "name": "礼部",
            "description": "情感与对话智能体",
            "recommended_skills": ["情感分析", "话术生成", "多轮对话", "情绪安抚"],
            "categories": ["general", "property"]
        },
        "hubu": {
            "name": "户部",
            "description": "数据采集智能体",
            "recommended_skills": ["数据清洗", "API集成", "爬虫采集", "数据验证"],
            "categories": ["data", "property"]
        },
        "bingbu": {
            "name": "兵部",
            "description": "风险分析智能体",
            "recommended_skills": ["风险评估", "预测模型", "异常检测", "趋势分析"],
            "categories": ["property", "security"]
        },
        "xingbu": {
            "name": "刑部",
            "description": "安全审计智能体",
            "recommended_skills": ["规则引擎", "合规审查", "漏洞扫描", "安全审计"],
            "categories": ["security"]
        },
        "libu2": {
            "name": "吏部",
            "description": "管理调度智能体",
            "recommended_skills": ["任务调度", "资源管理", "智能体监控", "绩效评估"],
            "categories": ["general"]
        },
        "gongbu": {
            "name": "工部",
            "description": "报告生成智能体",
            "recommended_skills": ["GIS分析", "图表生成", "报告模板", "PDF导出"],
            "categories": ["property", "data"]
        },
        "li_bu": {
            "name": "吏部",
            "description": "管理调度智能体",
            "recommended_skills": ["任务调度", "资源管理", "智能体监控"],
            "categories": ["general"]
        },
        "hu_bu": {
            "name": "户部",
            "description": "数据采集智能体",
            "recommended_skills": ["数据清洗", "API集成", "爬虫采集"],
            "categories": ["data", "property"]
        },
        "bing_bu": {
            "name": "兵部",
            "description": "风险分析智能体",
            "recommended_skills": ["风险评估", "预测模型", "异常检测"],
            "categories": ["property", "security"]
        },
        "xing_bu": {
            "name": "刑部",
            "description": "安全审计智能体",
            "recommended_skills": ["规则引擎", "合规审查", "安全审计"],
            "categories": ["security"]
        },
        "gong_bu": {
            "name": "工部",
            "description": "报告生成智能体",
            "recommended_skills": ["GIS分析", "图表生成", "报告模板"],
            "categories": ["property", "data"]
        }
    }

    BOND_EFFECTS = {
        frozenset(["数据清洗", "数据分析"]): {
            "name": "数据专家",
            "effect": "efficiency_boost",
            "value": 0.3,
            "description": "数据清洗+分析组合，效率提升30%"
        },
        frozenset(["情感分析", "话术生成"]): {
            "name": "沟通大师",
            "effect": "conversion_boost",
            "value": 0.2,
            "description": "情感分析+话术生成组合，转化率提升20%"
        },
        frozenset(["风险评估", "预测模型"]): {
            "name": "风险专家",
            "effect": "accuracy_boost",
            "value": 0.25,
            "description": "风险评估+预测模型组合，准确率提升25%"
        },
        frozenset(["GIS分析", "图表生成"]): {
            "name": "可视化专家",
            "effect": "quality_boost",
            "value": 0.35,
            "description": "GIS分析+图表生成组合，报告质量提升35%"
        },
        frozenset(["合规审查", "安全审计"]): {
            "name": "安全卫士",
            "effect": "security_boost",
            "value": 0.4,
            "description": "合规审查+安全审计组合，安全评分提升40%"
        }
    }

    def __init__(self, db_pool, skill_executor):
        self.db_pool = db_pool
        self.skill_executor = skill_executor

    async def initialize_agent_skills(self, agent_id: str, agent_type: str) -> List[AgentSkillBinding]:
        recommendations = self.AGENT_SKILL_RECOMMENDATIONS.get(agent_type.lower(), {})
        if not recommendations:
            return []
        
        skill_names = recommendations.get("recommended_skills", [])
        
        async with self.db_pool.acquire() as conn:
            skills = await conn.fetch(
                "SELECT id, name FROM skills WHERE name = ANY($1) AND status = 'published'",
                skill_names
            )
            
            bindings = []
            for skill in skills:
                existing = await conn.fetchrow(
                    "SELECT id FROM agent_skills WHERE agent_id = $1 AND skill_id = $2",
                    agent_id, str(skill["id"])
                )
                
                if not existing:
                    await conn.execute("""
                        INSERT INTO agent_skills (id, agent_id, skill_id, proficiency, is_active)
                        VALUES ($1, $2, $3, 10, TRUE)
                    """, str(uuid.uuid4()), agent_id, str(skill["id"]))
                    
                    bindings.append(AgentSkillBinding(
                        agent_id=agent_id,
                        agent_type=agent_type,
                        skill_id=str(skill["id"]),
                        skill_name=skill["name"],
                        proficiency=10,
                        is_active=True
                    ))
            
            return bindings

    async def get_agent_skills(self, agent_id: str) -> List[AgentSkillBinding]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT as.*, s.name as skill_name
                FROM agent_skills as
                JOIN skills s ON as.skill_id = s.id
                WHERE as.agent_id = $1 AND as.is_active = TRUE
                ORDER BY as.proficiency DESC
            """, agent_id)
            
            return [
                AgentSkillBinding(
                    agent_id=row["agent_id"],
                    agent_type="",
                    skill_id=str(row["skill_id"]),
                    skill_name=row["skill_name"],
                    proficiency=row["proficiency"],
                    use_count=row["use_count"],
                    is_active=row["is_active"],
                    learned_at=row["learned_at"],
                    last_used_at=row["last_used_at"]
                )
                for row in rows
            ]

    async def invoke_skill(
        self,
        agent_id: str,
        skill_name: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        async with self.db_pool.acquire() as conn:
            skill = await conn.fetchrow("""
                SELECT s.* FROM skills s
                JOIN agent_skills as ON s.id = as.skill_id
                WHERE as.agent_id = $1 AND s.name = $2 AND as.is_active = TRUE
            """, agent_id, skill_name)
            
            if not skill:
                return {
                    "success": False,
                    "error": f"Agent {agent_id} does not have skill {skill_name}"
                }
            
            result = await self.skill_executor.execute(
                str(skill["id"]),
                input_data,
                user_id or agent_id,
                agent_id
            )
            
            return {
                "success": result.status == "success",
                "output": result.output_data,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            }

    async def check_bond_effects(self, agent_id: str) -> List[Dict[str, Any]]:
        skills = await self.get_agent_skills(agent_id)
        skill_names = {s.skill_name for s in skills}
        
        active_bonds = []
        
        for skill_set, effect in self.BOND_EFFECTS.items():
            if skill_set.issubset(skill_names):
                active_bonds.append({
                    "name": effect["name"],
                    "skills": list(skill_set),
                    "effect": effect["effect"],
                    "value": effect["value"],
                    "description": effect["description"]
                })
        
        return active_bonds

    async def get_agent_recommendations(self, agent_id: str, agent_type: str) -> List[Dict[str, Any]]:
        current_skills = await self.get_agent_skills(agent_id)
        current_skill_names = {s.skill_name for s in current_skills}
        
        recommendations = self.AGENT_SKILL_RECOMMENDATIONS.get(agent_type.lower(), {})
        recommended_names = set(recommendations.get("recommended_skills", []))
        
        missing_skills = recommended_names - current_skill_names
        
        async with self.db_pool.acquire() as conn:
            skills = await conn.fetch(
                "SELECT id, name, description, cost_points, category FROM skills WHERE name = ANY($1) AND status = 'published'",
                list(missing_skills)
            )
            
            return [
                {
                    "id": str(s["id"]),
                    "name": s["name"],
                    "description": s["description"],
                    "cost_points": s["cost_points"],
                    "category": s["category"],
                    "reason": f"推荐{recommendations.get('name', agent_type)}使用的技能"
                }
                for s in skills
            ]

    async def learn_skill(
        self,
        agent_id: str,
        skill_id: str,
        initial_proficiency: int = 10
    ) -> AgentSkillBinding:
        async with self.db_pool.acquire() as conn:
            skill = await conn.fetchrow(
                "SELECT id, name FROM skills WHERE id = $1", skill_id
            )
            
            if not skill:
                raise ValueError(f"Skill {skill_id} not found")
            
            existing = await conn.fetchrow(
                "SELECT id FROM agent_skills WHERE agent_id = $1 AND skill_id = $2",
                agent_id, skill_id
            )
            
            if existing:
                await conn.execute("""
                    UPDATE agent_skills SET is_active = TRUE, proficiency = $1
                    WHERE agent_id = $2 AND skill_id = $3
                """, initial_proficiency, agent_id, skill_id)
            else:
                await conn.execute("""
                    INSERT INTO agent_skills (id, agent_id, skill_id, proficiency, is_active)
                    VALUES ($1, $2, $3, $4, TRUE)
                """, str(uuid.uuid4()), agent_id, skill_id, initial_proficiency)
            
            return AgentSkillBinding(
                agent_id=agent_id,
                agent_type="",
                skill_id=skill_id,
                skill_name=skill["name"],
                proficiency=initial_proficiency,
                is_active=True
            )

    async def forget_skill(self, agent_id: str, skill_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE agent_skills SET is_active = FALSE
                WHERE agent_id = $1 AND skill_id = $2
            """, agent_id, skill_id)
            
            return "UPDATE" in result


_agent_skill_manager: Optional[AgentSkillManager] = None


def get_agent_skill_manager() -> Optional[AgentSkillManager]:
    return _agent_skill_manager


async def init_agent_skill_manager(db_pool, skill_executor):
    global _agent_skill_manager
    _agent_skill_manager = AgentSkillManager(db_pool, skill_executor)
    return _agent_skill_manager
