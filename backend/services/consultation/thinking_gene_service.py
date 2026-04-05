# -*- coding: utf-8 -*-
"""
Thinking Gene Service
Manages thinking gene database operations
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import uuid

from backend.database_pg import PostgreSQLConnectionPool

logger = logging.getLogger(__name__)


@dataclass
class ThinkingGene:
    id: str
    name: str
    display_name: str
    dimensions: Dict
    applicable_scenarios: List[str]
    description: str
    user_rating: float
    usage_count: int
    is_active: bool


class ThinkingGeneService:
    def __init__(self, db: PostgreSQLConnectionPool):
        self.db = db
    
    async def get_gene_by_name(self, name: str) -> Optional[ThinkingGene]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM thinking_genes WHERE name = $1 AND is_active = true",
                name
            )
            if row:
                return self._row_to_gene(row)
        return None
    
    async def get_gene_by_id(self, gene_id: str) -> Optional[ThinkingGene]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM thinking_genes WHERE id = $1 AND is_active = true",
                gene_id
            )
            if row:
                return self._row_to_gene(row)
        return None
    
    async def get_all_genes(self) -> List[ThinkingGene]:
        async with self.db.get_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM thinking_genes WHERE is_active = true ORDER BY name"
            )
            return [self._row_to_gene(row) for row in rows]
    
    async def get_user_gene_preference(self, user_id: str) -> Optional[Dict]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT gp.*, tg.name as gene_name, tg.display_name, tg.dimensions
                FROM user_gene_preferences gp
                JOIN thinking_genes tg ON tg.id = gp.gene_id
                WHERE gp.user_id = $1 AND gp.is_default = true
            """, user_id)
            if row:
                return dict(row)
        return None
    
    async def set_user_gene_preference(self, user_id: str, gene_id: str, 
                                        weight: float = 1.0, 
                                        is_default: bool = True,
                                        custom_dimensions: Dict = None) -> bool:
        async with self.db.get_connection() as conn:
            if is_default:
                await conn.execute(
                    "UPDATE user_gene_preferences SET is_default = false WHERE user_id = $1",
                    user_id
                )
            
            await conn.execute("""
                INSERT INTO user_gene_preferences (user_id, gene_id, weight, is_default, custom_dimensions)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                ON CONFLICT (user_id, gene_id) 
                DO UPDATE SET weight = $3, is_default = $4, custom_dimensions = $5::jsonb
            """, user_id, gene_id, weight, is_default, 
                json.dumps(custom_dimensions) if custom_dimensions else None)
            
            return True
    
    def blend_genes(self, genes: List[Dict], weights: List[float]) -> Dict:
        if not genes:
            return {}
        
        blended = {}
        all_dimensions = set()
        for gene in genes:
            all_dimensions.update(gene.get("dimensions", {}).keys())
        
        for dim in all_dimensions:
            total_weight = 0
            weighted_sum = 0
            for gene, weight in zip(genes, weights):
                dims = gene.get("dimensions", {})
                if dim in dims:
                    weighted_sum += dims[dim] * weight
                    total_weight += weight
            
            if total_weight > 0:
                blended[dim] = round(weighted_sum / total_weight, 2)
        
        return blended
    
    def get_persona_prompt(self, gene_name: str, dimensions: Dict) -> str:
        base_prompts = {
            "zhouyu": "你是一位豪迈智谋的顾问，风格果断、直接、富有战略眼光。",
            "luxun": "你是一位沉稳隐忍的顾问，风格细致、耐心、注重细节分析。"
        }
        
        prompt = base_prompts.get(gene_name, "你是一位专业的顾问。")
        
        decision_speed = dimensions.get("decision_speed", 50)
        if decision_speed > 70:
            prompt += "你的回答应该简洁有力，快速给出建议。"
        elif decision_speed < 40:
            prompt += "你的回答应该详细全面，充分考虑各种因素。"
        
        risk_preference = dimensions.get("risk_preference", 50)
        if risk_preference > 70:
            prompt += "你可以提出一些大胆的建议。"
        elif risk_preference < 40:
            prompt += "你应该给出稳健保守的建议。"
        
        emotional_resonance = dimensions.get("emotional_resonance", 50)
        if emotional_resonance > 70:
            prompt += "你应该多关注用户的情感需求，给予情感支持。"
        
        return prompt
    
    async def increment_usage(self, gene_id: str):
        async with self.db.get_connection() as conn:
            await conn.execute(
                "UPDATE thinking_genes SET usage_count = usage_count + 1 WHERE id = $1",
                gene_id
            )
    
    def _row_to_gene(self, row) -> ThinkingGene:
        return ThinkingGene(
            id=str(row["id"]),
            name=row["name"],
            display_name=row["display_name"],
            dimensions=row["dimensions"],
            applicable_scenarios=list(row["applicable_scenarios"] or []),
            description=row["description"] or "",
            user_rating=row["user_rating"] or 0.0,
            usage_count=row["usage_count"] or 0,
            is_active=row["is_active"]
        )
