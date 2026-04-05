# -*- coding: utf-8 -*-
"""
Skill Invoker
Handles skill matching and invocation from the talent marketplace
"""
import logging
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import httpx

from backend.database_pg import PostgreSQLConnectionPool

logger = logging.getLogger(__name__)


class SkillStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SkillCategory(Enum):
    PROPERTY = "property"
    DESTINY = "destiny"
    GENERAL = "general"
    ANALYSIS = "analysis"
    EXTERNAL = "external"


@dataclass
class SkillMatch:
    skill_id: str
    skill_name: str
    category: str
    relevance_score: float
    input_match: bool
    estimated_cost: float
    estimated_time: int


@dataclass
class SkillInvocation:
    invocation_id: str
    skill_id: str
    skill_name: str
    input_data: Dict
    output_data: Optional[Dict]
    status: str
    duration_ms: int
    cost_charged: float
    error_message: Optional[str]


class SkillInvoker:
    def __init__(self, db: PostgreSQLConnectionPool = None):
        self.db = db
        self._skill_cache: Dict[str, Dict] = {}
        self._invocation_timeout = 30000
        self._max_retries = 3
    
    async def get_available_skills(self, category: str = None) -> List[Dict]:
        if not self.db:
            return self._get_default_skills()
        
        async with self.db.get_connection() as conn:
            if category:
                rows = await conn.fetch(
                    "SELECT * FROM skill_registry WHERE is_active = true AND category = $1",
                    category
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM skill_registry WHERE is_active = true"
                )
            
            return [dict(row) for row in rows]
    
    def _get_default_skills(self) -> List[Dict]:
        return [
            {
                "id": "property_valuation",
                "name": "property_valuation",
                "display_name": "房产估值",
                "category": "property",
                "input_schema": {"address": "string", "area": "number"},
                "output_schema": {"estimated_value": "number", "confidence": "float"},
                "cost": 1.0,
                "timeout_ms": 10000
            },
            {
                "id": "policy_analysis",
                "name": "policy_analysis",
                "display_name": "政策解读",
                "category": "property",
                "input_schema": {"city": "string", "policy_type": "string"},
                "output_schema": {"summary": "string", "impact": "string"},
                "cost": 0.5,
                "timeout_ms": 5000
            },
            {
                "id": "destiny_analysis",
                "name": "destiny_analysis",
                "display_name": "命理分析",
                "category": "destiny",
                "input_schema": {"birth_date": "string", "gender": "string"},
                "output_schema": {"destiny_chart": "object", "interpretation": "string"},
                "cost": 2.0,
                "timeout_ms": 15000
            }
        ]
    
    async def match_skills(
        self,
        intent: str,
        slots: Dict,
        required_capabilities: List[str] = None
    ) -> List[SkillMatch]:
        skills = await self.get_available_skills()
        matches = []
        
        intent_skill_map = {
            "property_consultation": ["property_valuation", "policy_analysis", "market_analysis"],
            "destiny_consultation": ["destiny_analysis", "fortune_telling"],
            "investment_advice": ["investment_analysis", "risk_assessment"],
            "policy_inquiry": ["policy_analysis"]
        }
        
        relevant_skills = intent_skill_map.get(intent, [])
        
        for skill in skills:
            if skill["name"] in relevant_skills:
                input_match = self._check_input_match(skill, slots)
                relevance = self._calculate_relevance(skill, intent, slots)
                
                matches.append(SkillMatch(
                    skill_id=skill["id"],
                    skill_name=skill["name"],
                    category=skill["category"],
                    relevance_score=relevance,
                    input_match=input_match,
                    estimated_cost=skill.get("cost", 0),
                    estimated_time=skill.get("timeout_ms", 10000)
                ))
        
        matches.sort(key=lambda m: m.relevance_score, reverse=True)
        return matches
    
    def _check_input_match(self, skill: Dict, slots: Dict) -> bool:
        input_schema = skill.get("input_schema", {})
        required_fields = [k for k, v in input_schema.items() if v.get("required", True)]
        
        for field in required_fields:
            if field not in slots or not slots[field]:
                return False
        
        return True
    
    def _calculate_relevance(self, skill: Dict, intent: str, slots: Dict) -> float:
        score = 0.5
        
        if skill["category"] == "property" and intent in ["property_consultation", "investment_advice"]:
            score += 0.3
        elif skill["category"] == "destiny" and intent == "destiny_consultation":
            score += 0.3
        
        if self._check_input_match(skill, slots):
            score += 0.2
        
        return min(score, 1.0)
    
    async def invoke_skill(
        self,
        skill_id: str,
        input_data: Dict,
        session_id: str = None,
        user_id: str = None
    ) -> SkillInvocation:
        invocation_id = str(uuid.uuid4())
        start_time = time.time()
        
        skill = await self._get_skill(skill_id)
        if not skill:
            return SkillInvocation(
                invocation_id=invocation_id,
                skill_id=skill_id,
                skill_name="unknown",
                input_data=input_data,
                output_data=None,
                status=SkillStatus.FAILED.value,
                duration_ms=0,
                cost_charged=0,
                error_message="Skill not found"
            )
        
        await self._record_invocation_start(
            invocation_id, skill, input_data, session_id, user_id
        )
        
        try:
            output_data = await self._execute_skill(skill, input_data)
            duration_ms = int((time.time() - start_time) * 1000)
            
            await self._record_invocation_complete(
                invocation_id, output_data, SkillStatus.SUCCESS.value, duration_ms
            )
            
            return SkillInvocation(
                invocation_id=invocation_id,
                skill_id=skill_id,
                skill_name=skill["name"],
                input_data=input_data,
                output_data=output_data,
                status=SkillStatus.SUCCESS.value,
                duration_ms=duration_ms,
                cost_charged=skill.get("cost", 0),
                error_message=None
            )
            
        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_invocation_complete(
                invocation_id, None, SkillStatus.TIMEOUT.value, duration_ms,
                "Skill execution timed out"
            )
            
            return SkillInvocation(
                invocation_id=invocation_id,
                skill_id=skill_id,
                skill_name=skill["name"],
                input_data=input_data,
                output_data=None,
                status=SkillStatus.TIMEOUT.value,
                duration_ms=duration_ms,
                cost_charged=0,
                error_message="Execution timed out"
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_invocation_complete(
                invocation_id, None, SkillStatus.FAILED.value, duration_ms, str(e)
            )
            
            return SkillInvocation(
                invocation_id=invocation_id,
                skill_id=skill_id,
                skill_name=skill["name"],
                input_data=input_data,
                output_data=None,
                status=SkillStatus.FAILED.value,
                duration_ms=duration_ms,
                cost_charged=0,
                error_message=str(e)
            )
    
    async def _get_skill(self, skill_id: str) -> Optional[Dict]:
        if skill_id in self._skill_cache:
            return self._skill_cache[skill_id]
        
        if self.db:
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM skill_registry WHERE id = $1 OR name = $1",
                    skill_id
                )
                if row:
                    skill = dict(row)
                    self._skill_cache[skill_id] = skill
                    return skill
        
        for skill in self._get_default_skills():
            if skill["id"] == skill_id or skill["name"] == skill_id:
                return skill
        
        return None
    
    async def _execute_skill(self, skill: Dict, input_data: Dict) -> Dict:
        api_endpoint = skill.get("api_endpoint")
        
        if api_endpoint and api_endpoint.startswith("http"):
            return await self._call_external_api(skill, input_data)
        else:
            return await self._simulate_skill(skill, input_data)
    
    async def _call_external_api(self, skill: Dict, input_data: Dict) -> Dict:
        api_endpoint = skill.get("api_endpoint")
        api_method = skill.get("api_method", "POST")
        timeout = skill.get("timeout_ms", 30000) / 1000
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if api_method.upper() == "GET":
                response = await client.get(api_endpoint, params=input_data)
            else:
                response = await client.post(api_endpoint, json=input_data)
            
            response.raise_for_status()
            return response.json()
    
    async def _simulate_skill(self, skill: Dict, input_data: Dict) -> Dict:
        await asyncio.sleep(0.1)
        
        skill_name = skill.get("name", "")
        
        if skill_name == "property_valuation":
            area = input_data.get("area", 100)
            city = input_data.get("city", "深圳")
            base_price = {"深圳": 60000, "北京": 55000, "上海": 52000, "广州": 35000}
            price = base_price.get(city, 30000)
            return {
                "estimated_value": int(area * price),
                "confidence": 0.85,
                "price_per_sqm": price,
                "market_trend": "stable"
            }
        
        elif skill_name == "policy_analysis":
            city = input_data.get("city", "深圳")
            return {
                "summary": f"{city}当前购房政策稳定，限购政策持续执行",
                "impact": "对首套房购买者影响较小",
                "recommendations": ["建议关注公积金贷款政策", "可考虑二手房市场"],
                "last_updated": "2024-01-01"
            }
        
        elif skill_name == "destiny_analysis":
            return {
                "destiny_chart": {
                    "year_pillar": "甲子",
                    "month_pillar": "乙丑",
                    "day_pillar": "丙寅",
                    "hour_pillar": "丁卯"
                },
                "interpretation": "命格显示适合从事房产投资",
                "advice": ["宜在南方发展", "投资需谨慎", "贵人运佳"]
            }
        
        return {"result": "Skill executed successfully", "input": input_data}
    
    async def _record_invocation_start(
        self,
        invocation_id: str,
        skill: Dict,
        input_data: Dict,
        session_id: str,
        user_id: str
    ):
        if not self.db:
            return
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO skill_invocations 
                (id, session_id, skill_id, user_id, input_data, status, invoked_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, 'running', CURRENT_TIMESTAMP)
            """, invocation_id, session_id, skill["id"], user_id, input_data)
    
    async def _record_invocation_complete(
        self,
        invocation_id: str,
        output_data: Optional[Dict],
        status: str,
        duration_ms: int,
        error_message: str = None
    ):
        if not self.db:
            return
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE skill_invocations 
                SET output_data = $1::jsonb, status = $2, duration_ms = $3,
                    error_message = $4, completed_at = CURRENT_TIMESTAMP
                WHERE id = $5
            """, output_data, status, duration_ms, error_message, invocation_id)
    
    async def get_invocation_history(
        self,
        session_id: str = None,
        user_id: str = None,
        limit: int = 10
    ) -> List[Dict]:
        if not self.db:
            return []
        
        async with self.db.get_connection() as conn:
            if session_id:
                rows = await conn.fetch("""
                    SELECT * FROM skill_invocations 
                    WHERE session_id = $1 
                    ORDER BY invoked_at DESC 
                    LIMIT $2
                """, session_id, limit)
            elif user_id:
                rows = await conn.fetch("""
                    SELECT * FROM skill_invocations 
                    WHERE user_id = $1 
                    ORDER BY invoked_at DESC 
                    LIMIT $2
                """, user_id, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM skill_invocations 
                    ORDER BY invoked_at DESC 
                    LIMIT $1
                """, limit)
            
            return [dict(row) for row in rows]


skill_invoker: Optional[SkillInvoker] = None


async def get_skill_invoker(db: PostgreSQLConnectionPool = None) -> SkillInvoker:
    global skill_invoker
    if skill_invoker is None:
        skill_invoker = SkillInvoker(db)
    return skill_invoker
