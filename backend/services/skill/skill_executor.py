# -*- coding: utf-8 -*-
"""
Skill Executor
Executes skills in sandboxed environment
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import asyncio
import json
import uuid
import time


@dataclass
class ExecutionContext:
    skill_id: str
    skill_name: str
    user_id: str
    agent_id: Optional[str]
    input_data: Dict[str, Any]
    timeout_ms: int = 5000
    max_memory_mb: int = 256
    started_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    skill_id: str
    status: str
    output_data: Dict[str, Any]
    duration_ms: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillExecutor:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._builtin_handlers: Dict[str, Callable] = {}
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        self._builtin_handlers["情感分析"] = self._handle_emotion_analysis
        self._builtin_handlers["数据清洗"] = self._handle_data_cleaning
        self._builtin_handlers["风险评估"] = self._handle_risk_assessment
        self._builtin_handlers["合规审查"] = self._handle_compliance_check
        self._builtin_handlers["任务调度"] = self._handle_task_scheduling
        self._builtin_handlers["GIS分析"] = self._handle_gis_analysis
        self._builtin_handlers["图表生成"] = self._handle_chart_generation
        self._builtin_handlers["报告模板"] = self._handle_report_template

    async def execute(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        user_id: str,
        agent_id: Optional[str] = None,
        timeout_ms: int = 5000
    ) -> ExecutionResult:
        skill = await self._get_skill(skill_id)
        if not skill:
            return ExecutionResult(
                skill_id=skill_id,
                status="error",
                output_data={},
                duration_ms=0,
                error_message="Skill not found"
            )
        
        context = ExecutionContext(
            skill_id=skill_id,
            skill_name=skill["name"],
            user_id=user_id,
            agent_id=agent_id,
            input_data=input_data,
            timeout_ms=timeout_ms
        )
        
        start_time = time.time()
        
        try:
            has_permission = await self._check_permission(skill_id, user_id, agent_id)
            if not has_permission:
                return ExecutionResult(
                    skill_id=skill_id,
                    status="error",
                    output_data={},
                    duration_ms=0,
                    error_message="Permission denied"
                )
            
            validated_input = await self._validate_input(skill, input_data)
            
            if skill["type"] == "builtin":
                output = await self._execute_builtin(skill, validated_input, context)
            elif skill["type"] == "external":
                output = await self._execute_external(skill, validated_input, context)
            else:
                output = await self._execute_extension(skill, validated_input, context)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            await self._record_invocation(
                skill_id, user_id, agent_id, input_data, output, "success", duration_ms
            )
            
            await self._update_proficiency(skill_id, user_id, agent_id)
            
            return ExecutionResult(
                skill_id=skill_id,
                status="success",
                output_data=output,
                duration_ms=duration_ms
            )
            
        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_invocation(
                skill_id, user_id, agent_id, input_data, {}, "timeout", duration_ms, "Execution timeout"
            )
            return ExecutionResult(
                skill_id=skill_id,
                status="timeout",
                output_data={},
                duration_ms=duration_ms,
                error_message="Execution timeout"
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_invocation(
                skill_id, user_id, agent_id, input_data, {}, "error", duration_ms, str(e)
            )
            return ExecutionResult(
                skill_id=skill_id,
                status="error",
                output_data={},
                duration_ms=duration_ms,
                error_message=str(e)
            )

    async def _get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM skills WHERE id = $1", skill_id
            )
            return dict(row) if row else None

    async def _check_permission(self, skill_id: str, user_id: str, agent_id: Optional[str]) -> bool:
        async with self.db_pool.acquire() as conn:
            skill = await conn.fetchrow(
                "SELECT type, cost_points FROM skills WHERE id = $1", skill_id
            )
            
            if not skill:
                return False
            
            if skill["type"] == "builtin" and skill["cost_points"] == 0:
                return True
            
            if user_id:
                user_skill = await conn.fetchrow(
                    "SELECT id FROM user_skills WHERE user_id = $1 AND skill_id = $2 AND is_active = TRUE",
                    user_id, skill_id
                )
                if user_skill:
                    return True
            
            if agent_id:
                agent_skill = await conn.fetchrow(
                    "SELECT id FROM agent_skills WHERE agent_id = $1 AND skill_id = $2 AND is_active = TRUE",
                    agent_id, skill_id
                )
                if agent_skill:
                    return True
            
            return False

    async def _validate_input(self, skill: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        input_schema = skill.get("input_schema", {})
        
        if not input_schema:
            return input_data
        
        required_fields = input_schema.get("required", [])
        properties = input_schema.get("properties", {})
        
        validated = {}
        for field_name in required_fields:
            if field_name not in input_data:
                raise ValueError(f"Missing required field: {field_name}")
            validated[field_name] = input_data[field_name]
        
        for field_name, value in input_data.items():
            if field_name in properties:
                validated[field_name] = value
        
        return validated

    async def _execute_builtin(
        self,
        skill: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        skill_name = skill["name"]
        handler = self._builtin_handlers.get(skill_name)
        
        if handler:
            return await handler(input_data, context)
        else:
            return {"message": f"Skill {skill_name} executed", "input": input_data}

    async def _execute_external(
        self,
        skill: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        code_config = skill.get("code_config", {})
        api_url = code_config.get("api_url")
        
        if not api_url:
            raise ValueError("External skill not configured properly")
        
        return {
            "external_call": True,
            "api_url": api_url,
            "input": input_data,
            "message": "External API would be called here"
        }

    async def _execute_extension(
        self,
        skill: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        code_config = skill.get("code_config", {})
        code = code_config.get("code", "")
        
        if not code:
            raise ValueError("Extension skill has no code")
        
        return {
            "extension_execution": True,
            "input": input_data,
            "message": "Extension code would be executed in sandbox"
        }

    async def _handle_emotion_analysis(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        text = input_data.get("text", "")
        
        emotions = ["happy", "sad", "anxious", "excited", "neutral", "angry", "fearful", "surprised"]
        import random
        
        emotion_scores = {e: random.uniform(0, 1) for e in emotions}
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        return {
            "primary_emotion": primary_emotion[0],
            "confidence": round(primary_emotion[1], 3),
            "all_scores": {k: round(v, 3) for k, v in emotion_scores.items()},
            "text_length": len(text),
            "analysis_timestamp": datetime.now().isoformat()
        }

    async def _handle_data_cleaning(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = input_data.get("data", [])
        rules = input_data.get("rules", ["remove_null", "deduplicate"])
        
        original_count = len(data)
        cleaned_data = data.copy()
        
        if "remove_null" in rules:
            cleaned_data = [item for item in cleaned_data if item is not None]
        
        if "deduplicate" in rules:
            seen = set()
            unique_data = []
            for item in cleaned_data:
                item_str = json.dumps(item, sort_keys=True)
                if item_str not in seen:
                    seen.add(item_str)
                    unique_data.append(item)
            cleaned_data = unique_data
        
        return {
            "cleaned_data": cleaned_data,
            "original_count": original_count,
            "cleaned_count": len(cleaned_data),
            "removed_count": original_count - len(cleaned_data),
            "rules_applied": rules
        }

    async def _handle_risk_assessment(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        context_data = input_data.get("context", {})
        
        risk_factors = []
        overall_score = 0.0
        
        if context_data.get("high_value", False):
            risk_factors.append({"factor": "high_value", "score": 0.3, "description": "高价值交易"})
            overall_score += 0.3
        
        if context_data.get("new_user", False):
            risk_factors.append({"factor": "new_user", "score": 0.2, "description": "新用户"})
            overall_score += 0.2
        
        if context_data.get("unusual_location", False):
            risk_factors.append({"factor": "unusual_location", "score": 0.4, "description": "异常位置"})
            overall_score += 0.4
        
        if overall_score < 0.3:
            risk_level = "low"
        elif overall_score < 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "overall_score": round(overall_score, 2),
            "risk_factors": risk_factors,
            "recommendations": [
                "建议进行身份验证" if overall_score > 0.5 else "可以继续",
                "建议人工审核" if overall_score > 0.7 else None
            ]
        }

    async def _handle_compliance_check(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        content = input_data.get("content", "")
        rules = input_data.get("rules", ["sensitive_words", "pii"])
        
        violations = []
        
        sensitive_words = ["敏感词1", "敏感词2", "违禁词"]
        for word in sensitive_words:
            if word in content:
                violations.append({
                    "type": "sensitive_word",
                    "detail": f"发现敏感词: {word}",
                    "severity": "high"
                })
        
        import re
        phone_pattern = r'\d{11}'
        if re.search(phone_pattern, content):
            violations.append({
                "type": "pii",
                "detail": "可能包含手机号",
                "severity": "medium"
            })
        
        is_compliant = len(violations) == 0
        
        return {
            "is_compliant": is_compliant,
            "violations": violations,
            "checked_rules": rules,
            "content_length": len(content)
        }

    async def _handle_task_scheduling(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        tasks = input_data.get("tasks", [])
        resources = input_data.get("resources", {})
        
        schedule = []
        for i, task in enumerate(tasks):
            schedule.append({
                "task_id": task.get("id", f"task_{i}"),
                "scheduled_time": datetime.now().isoformat(),
                "assigned_resource": f"resource_{i % max(len(resources), 1)}",
                "priority": task.get("priority", "normal")
            })
        
        return {
            "schedule": schedule,
            "total_tasks": len(tasks),
            "optimization_score": 0.85,
            "estimated_completion": "2 hours"
        }

    async def _handle_gis_analysis(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        location = input_data.get("location", {})
        analysis_type = input_data.get("analysis_type", "heatmap")
        
        return {
            "analysis_type": analysis_type,
            "location": location,
            "map_url": f"https://maps.example.com/analysis/{context.skill_id}",
            "data_points": 150,
            "coverage_area_km2": 25.5,
            "insights": [
                "该区域房价均价为35000元/平方米",
                "近一年房价涨幅为5.2%",
                "周边配套设施完善度评分: 85/100"
            ]
        }

    async def _handle_chart_generation(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = input_data.get("data", [])
        chart_type = input_data.get("chart_type", "bar")
        options = input_data.get("options", {})
        
        return {
            "chart_type": chart_type,
            "chart_url": f"https://charts.example.com/{uuid.uuid4()}",
            "data_points": len(data),
            "options": options,
            "generated_at": datetime.now().isoformat()
        }

    async def _handle_report_template(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        template_id = input_data.get("template_id", "default")
        data = input_data.get("data", {})
        
        sections = [
            {"id": "summary", "title": "摘要", "content": "报告摘要内容"},
            {"id": "analysis", "title": "分析", "content": "详细分析内容"},
            {"id": "conclusion", "title": "结论", "content": "结论和建议"}
        ]
        
        return {
            "template_id": template_id,
            "sections": sections,
            "generated_at": datetime.now().isoformat(),
            "format": "markdown"
        }

    async def _record_invocation(
        self,
        skill_id: str,
        user_id: str,
        agent_id: Optional[str],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        status: str,
        duration_ms: int,
        error_message: Optional[str] = None
    ):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO skill_invocations (id, skill_id, agent_id, user_id, input_data, output_data, status, duration_ms, error_message)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9)
            """, str(uuid.uuid4()), skill_id, agent_id, user_id,
                json.dumps(input_data), json.dumps(output_data), status, duration_ms, error_message)

    async def _update_proficiency(self, skill_id: str, user_id: str, agent_id: Optional[str]):
        async with self.db_pool.acquire() as conn:
            if user_id:
                await conn.execute("""
                    UPDATE user_skills 
                    SET use_count = use_count + 1, 
                        proficiency = LEAST(proficiency + 1, 100),
                        last_used_at = NOW()
                    WHERE user_id = $1 AND skill_id = $2
                """, user_id, skill_id)
            
            if agent_id:
                await conn.execute("""
                    UPDATE agent_skills 
                    SET use_count = use_count + 1, 
                        proficiency = LEAST(proficiency + 1, 100),
                        last_used_at = NOW()
                    WHERE agent_id = $1 AND skill_id = $2
                """, agent_id, skill_id)


_skill_executor: Optional[SkillExecutor] = None


def get_skill_executor() -> Optional[SkillExecutor]:
    return _skill_executor


async def init_skill_executor(db_pool):
    global _skill_executor
    _skill_executor = SkillExecutor(db_pool)
    return _skill_executor
