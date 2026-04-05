# -*- coding: utf-8 -*-
"""
Skill Recommendation Engine
Provides personalized skill recommendations
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class UserSkillProfile:
    user_id: str
    purchased_categories: Dict[str, int] = field(default_factory=dict)
    frequently_used_skills: List[str] = field(default_factory=list)
    agent_types: List[str] = field(default_factory=list)
    search_history: List[str] = field(default_factory=list)
    total_purchases: int = 0
    total_points_spent: int = 0


@dataclass
class Recommendation:
    skill_id: str
    skill_name: str
    score: float
    reason: str
    category: str
    cost_points: int
    match_type: str


class RecommendationEngine:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_user_profile(self, user_id: str) -> UserSkillProfile:
        async with self.db_pool.acquire() as conn:
            purchased = await conn.fetch("""
                SELECT s.category, COUNT(*) as count
                FROM user_skills us
                JOIN skills s ON us.skill_id = s.id
                WHERE us.user_id = $1
                GROUP BY s.category
            """, user_id)
            
            categories = {row["category"]: row["count"] for row in purchased}
            
            used_skills = await conn.fetch("""
                SELECT skill_id, COUNT(*) as use_count
                FROM skill_invocations
                WHERE user_id = $1
                GROUP BY skill_id
                ORDER BY use_count DESC
                LIMIT 10
            """, user_id)
            
            frequently_used = [row["skill_id"] for row in used_skills]
            
            total_purchases = await conn.fetchval("""
                SELECT COUNT(*) FROM user_skills WHERE user_id = $1
            """, user_id)
            
            total_spent = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0) FROM point_transactions
                WHERE user_id = $1 AND transaction_type = 'spend' AND source = 'skill_purchase'
            """, user_id)
            
            return UserSkillProfile(
                user_id=user_id,
                purchased_categories=categories,
                frequently_used=frequently_used,
                total_purchases=total_purchases or 0,
                total_points_spent=total_spent or 0
            )

    async def get_recommendations(
        self,
        user_id: str,
        agent_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Recommendation]:
        profile = await self.get_user_profile(user_id)
        
        recommendations = []
        
        category_recs = await self._recommend_by_category(profile, limit // 3)
        recommendations.extend(category_recs)
        
        if agent_type:
            agent_recs = await self._recommend_by_agent_type(agent_type, limit // 3)
            recommendations.extend(agent_recs)
        
        popular_recs = await self._recommend_popular(limit // 3)
        recommendations.extend(popular_recs)
        
        seen_ids = set()
        unique_recs = []
        for rec in recommendations:
            if rec.skill_id not in seen_ids:
                seen_ids.add(rec.skill_id)
                unique_recs.append(rec)
        
        unique_recs.sort(key=lambda x: x.score, reverse=True)
        return unique_recs[:limit]

    async def _recommend_by_category(
        self,
        profile: UserSkillProfile,
        limit: int
    ) -> List[Recommendation]:
        if not profile.purchased_categories:
            return []
        
        top_category = max(profile.purchased_categories.items(), key=lambda x: x[1])[0]
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, category, cost_points, rating, download_count
                FROM skills
                WHERE category = $1 AND status = 'published'
                AND id NOT IN (
                    SELECT skill_id FROM user_skills WHERE user_id = $2
                )
                ORDER BY rating DESC, download_count DESC
                LIMIT $3
            """, top_category, profile.user_id, limit)
            
            recommendations = []
            for row in rows:
                score = 0.4 + (row["rating"] / 5.0) * 0.3 + min(row["download_count"] / 1000, 0.3)
                recommendations.append(Recommendation(
                    skill_id=str(row["id"]),
                    skill_name=row["name"],
                    score=score,
                    reason=f"基于您对{top_category}类技能的兴趣推荐",
                    category=row["category"],
                    cost_points=row["cost_points"],
                    match_type="category"
                ))
            
            return recommendations

    async def _recommend_by_agent_type(
        self,
        agent_type: str,
        limit: int
    ) -> List[Recommendation]:
        agent_skill_mapping = {
            "libu": ["情感分析", "话术生成", "多轮对话", "情绪安抚"],
            "hubu": ["数据清洗", "API集成", "爬虫采集", "数据验证"],
            "bingbu": ["风险评估", "预测模型", "异常检测", "趋势分析"],
            "xingbu": ["规则引擎", "合规审查", "漏洞扫描", "安全审计"],
            "libu2": ["任务调度", "资源管理", "智能体监控", "绩效评估"],
            "gongbu": ["GIS分析", "图表生成", "报告模板", "PDF导出"],
            "li_bu": ["任务调度", "资源管理", "智能体监控"],
            "hu_bu": ["数据清洗", "API集成", "爬虫采集"],
            "bing_bu": ["风险评估", "预测模型", "异常检测"],
            "xing_bu": ["规则引擎", "合规审查", "安全审计"],
            "gong_bu": ["GIS分析", "图表生成", "报告模板"]
        }
        
        skill_names = agent_skill_mapping.get(agent_type.lower(), [])
        if not skill_names:
            return []
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, category, cost_points, rating
                FROM skills
                WHERE name = ANY($1) AND status = 'published'
                ORDER BY rating DESC
                LIMIT $2
            """, skill_names, limit)
            
            recommendations = []
            for row in rows:
                recommendations.append(Recommendation(
                    skill_id=str(row["id"]),
                    skill_name=row["name"],
                    score=0.8,
                    reason=f"适合{agent_type}智能体使用的技能",
                    category=row["category"],
                    cost_points=row["cost_points"],
                    match_type="agent_type"
                ))
            
            return recommendations

    async def _recommend_popular(self, limit: int) -> List[Recommendation]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, category, cost_points, rating, download_count
                FROM skills
                WHERE status = 'published'
                ORDER BY download_count DESC, rating DESC
                LIMIT $1
            """, limit)
            
            recommendations = []
            for row in rows:
                score = 0.3 + min(row["download_count"] / 5000, 0.5) + (row["rating"] / 5.0) * 0.2
                recommendations.append(Recommendation(
                    skill_id=str(row["id"]),
                    skill_name=row["name"],
                    score=score,
                    reason="热门技能推荐",
                    category=row["category"],
                    cost_points=row["cost_points"],
                    match_type="popular"
                ))
            
            return recommendations

    async def get_similar_skills(self, skill_id: str, limit: int = 5) -> List[Recommendation]:
        async with self.db_pool.acquire() as conn:
            skill = await conn.fetchrow(
                "SELECT category, tags FROM skills WHERE id = $1", skill_id
            )
            
            if not skill:
                return []
            
            rows = await conn.fetch("""
                SELECT id, name, category, cost_points, rating, tags
                FROM skills
                WHERE category = $1 AND id != $2 AND status = 'published'
                ORDER BY rating DESC
                LIMIT $3
            """, skill["category"], skill_id, limit)
            
            recommendations = []
            for row in rows:
                common_tags = set(row["tags"] or []) & set(skill["tags"] or [])
                score = 0.5 + len(common_tags) * 0.1
                
                recommendations.append(Recommendation(
                    skill_id=str(row["id"]),
                    skill_name=row["name"],
                    score=score,
                    reason="相似技能推荐",
                    category=row["category"],
                    cost_points=row["cost_points"],
                    match_type="similar"
                ))
            
            return recommendations

    async def get_trending_skills(self, days: int = 7, limit: int = 10) -> List[Recommendation]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT s.id, s.name, s.category, s.cost_points, s.rating,
                       COUNT(si.id) as recent_invocations
                FROM skills s
                LEFT JOIN skill_invocations si ON s.id = si.skill_id
                    AND si.invoked_at > NOW() - INTERVAL '{days} days'
                WHERE s.status = 'published'
                GROUP BY s.id
                ORDER BY recent_invocations DESC, s.rating DESC
                LIMIT $1
            """, limit)
            
            recommendations = []
            for row in rows:
                recommendations.append(Recommendation(
                    skill_id=str(row["id"]),
                    skill_name=row["name"],
                    score=row["recent_invocations"] / 100.0,
                    reason=f"近{days}天热门技能",
                    category=row["category"],
                    cost_points=row["cost_points"],
                    match_type="trending"
                ))
            
            return recommendations


_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> Optional[RecommendationEngine]:
    return _recommendation_engine


async def init_recommendation_engine(db_pool):
    global _recommendation_engine
    _recommendation_engine = RecommendationEngine(db_pool)
    return _recommendation_engine
