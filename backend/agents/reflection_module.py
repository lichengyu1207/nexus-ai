"""
反思模块
Reflection Module for Self-Improvement

根据任务记录和用户反馈，生成改进建议
建议格式为"在{场景}下，应{行动}，因为{原因}"
将反思结果存入记忆系统，并转化为训练样本
"""

import json
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ReflectionTrigger(Enum):
    """反思触发器类型"""
    TASK_FAILURE = "task_failure"
    USER_DISLIKE = "user_dislike"
    SCHEDULED = "scheduled"
    PERFORMANCE_DROP = "performance_drop"
    ERROR_PATTERN = "error_pattern"
    MANUAL = "manual"


class ReflectionType(Enum):
    """反思类型"""
    TASK_ANALYSIS = "task_analysis"
    ERROR_DIAGNOSIS = "error_diagnosis"
    STRATEGY_IMPROVEMENT = "strategy_improvement"
    COLLABORATION_REVIEW = "collaboration_review"
    KNOWLEDGE_GAP = "knowledge_gap"
    TOOL_USAGE = "tool_usage"


@dataclass
class ReflectionContext:
    """反思上下文"""
    task_id: str
    agent_id: str
    task_type: str
    user_input: str
    agent_response: str
    intermediate_steps: List[Dict[str, Any]]
    tools_used: List[str]
    task_success: bool
    user_feedback: Optional[str]
    task_duration: float
    error_messages: List[str]
    memory_retrieved: List[Dict[str, Any]]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "user_input": self.user_input,
            "agent_response": self.agent_response,
            "intermediate_steps": self.intermediate_steps,
            "tools_used": self.tools_used,
            "task_success": self.task_success,
            "user_feedback": self.user_feedback,
            "task_duration": self.task_duration,
            "error_messages": self.error_messages,
            "memory_retrieved": self.memory_retrieved,
            "timestamp": self.timestamp
        }


@dataclass
class ImprovementSuggestion:
    """改进建议"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = ""
    recommended_action: str = ""
    reason: str = ""
    priority: int = 1
    confidence: float = 0.5
    category: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "scenario": self.scenario,
            "recommended_action": self.recommended_action,
            "reason": self.reason,
            "priority": self.priority,
            "confidence": self.confidence,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at
        }
    
    def format(self) -> str:
        """格式化为自然语言"""
        return f"在{self.scenario}下，应{self.recommended_action}，因为{self.reason}"
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ImprovementSuggestion":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            scenario=data.get("scenario", ""),
            recommended_action=data.get("recommended_action", ""),
            reason=data.get("reason", ""),
            priority=data.get("priority", 1),
            confidence=data.get("confidence", 0.5),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            created_at=data.get("created_at", time.time())
        )


@dataclass
class ReflectionResult:
    """反思结果"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    trigger: ReflectionTrigger = ReflectionTrigger.TASK_FAILURE
    reflection_type: ReflectionType = ReflectionType.TASK_ANALYSIS
    context: Optional[ReflectionContext] = None
    analysis: str = ""
    root_cause: str = ""
    suggestions: List[ImprovementSuggestion] = field(default_factory=list)
    training_samples: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "trigger": self.trigger.value,
            "reflection_type": self.reflection_type.value,
            "context": self.context.to_dict() if self.context else None,
            "analysis": self.analysis,
            "root_cause": self.root_cause,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "training_samples": self.training_samples,
            "metrics": self.metrics,
            "created_at": self.created_at
        }


class ReflectionRecord(Base):
    """反思记录数据库模型"""
    __tablename__ = "reflection_records"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(50), index=True)
    task_id = Column(String(50), index=True)
    
    trigger = Column(String(30))
    reflection_type = Column(String(30))
    
    context = Column(JSON)
    analysis = Column(Text)
    root_cause = Column(Text)
    suggestions = Column(JSON)
    
    training_samples = Column(JSON)
    metrics = Column(JSON)
    
    applied = Column(Integer, default=0)
    effectiveness_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)


class ReflectionPatterns:
    """反思模式库"""
    
    ERROR_PATTERNS = {
        "data_not_found": {
            "keywords": ["未找到", "无数据", "查询为空", "没有结果"],
            "suggestion_template": "在需要{data_type}数据时，应先调用{tool}获取最新数据",
            "recommended_tools": ["兵部", "data_collector"]
        },
        "timeout": {
            "keywords": ["超时", "timeout", "响应时间过长"],
            "suggestion_template": "在处理{task_type}任务时，应使用异步方式或分批处理",
            "recommended_tools": ["async_processor"]
        },
        "invalid_input": {
            "keywords": ["无效输入", "参数错误", "格式不正确"],
            "suggestion_template": "在接收{input_type}输入时，应先进行格式验证和预处理",
            "recommended_tools": ["input_validator"]
        },
        "permission_denied": {
            "keywords": ["权限不足", "无权访问", "认证失败"],
            "suggestion_template": "在访问{resource}时，应先检查用户权限或使用{alternative}",
            "recommended_tools": ["permission_checker"]
        },
        "model_error": {
            "keywords": ["模型错误", "推理失败", "生成异常"],
            "suggestion_template": "在调用{model}时，应添加重试机制或使用备用模型",
            "recommended_tools": ["model_fallback"]
        }
    }
    
    SUCCESS_PATTERNS = {
        "efficient_tool_use": {
            "indicators": ["快速完成", "一次成功", "用户满意"],
            "lesson": "在{scenario}下，直接调用{tool}是最有效的方式"
        },
        "good_collaboration": {
            "indicators": ["协作顺利", "分工合理", "信息共享"],
            "lesson": "在{task_type}任务中，与{agent}协作可以提高效率"
        }
    }
    
    IMPROVEMENT_TEMPLATES = {
        "tool_selection": {
            "scenario_pattern": "需要获取{data_type}信息",
            "action_pattern": "调用{tool_name}",
            "reason_pattern": "该工具专门用于{purpose}"
        },
        "strategy_adjustment": {
            "scenario_pattern": "处理{task_type}任务",
            "action_pattern": "采用{strategy}策略",
            "reason_pattern": "可以提高{metric}指标"
        },
        "knowledge_update": {
            "scenario_pattern": "遇到{domain}相关问题",
            "action_pattern": "查询{knowledge_source}",
            "reason_pattern": "需要最新的{info_type}信息"
        }
    }


class ReflectionAnalyzer:
    """反思分析器"""
    
    def __init__(self):
        self.patterns = ReflectionPatterns()
        self._analysis_cache: Dict[str, Any] = {}
    
    def analyze_failure(
        self,
        context: ReflectionContext
    ) -> Tuple[str, str, List[ImprovementSuggestion]]:
        """分析失败原因"""
        analysis_parts = []
        root_causes = []
        suggestions = []
        
        if context.error_messages:
            for error in context.error_messages:
                error_analysis = self._analyze_error(error, context)
                analysis_parts.append(error_analysis["analysis"])
                root_causes.append(error_analysis["root_cause"])
                suggestions.extend(error_analysis["suggestions"])
        
        if not context.tools_used and context.task_type in ["data_query", "analysis"]:
            analysis_parts.append("未使用任何工具完成任务")
            root_causes.append("工具使用策略不当")
            suggestions.append(ImprovementSuggestion(
                scenario=f"执行{context.task_type}任务",
                recommended_action="调用相关工具获取数据或执行分析",
                reason="直接生成可能缺乏准确数据支持",
                priority=2,
                confidence=0.8,
                category="tool_usage"
            ))
        
        if context.task_duration > 30:
            analysis_parts.append(f"任务耗时过长({context.task_duration:.1f}秒)")
            root_causes.append("处理效率低下")
            suggestions.append(ImprovementSuggestion(
                scenario="处理复杂任务",
                recommended_action="采用分步处理或并行执行",
                reason="可以显著减少处理时间",
                priority=2,
                confidence=0.7,
                category="efficiency"
            ))
        
        if not context.memory_retrieved and len(context.user_input) > 50:
            analysis_parts.append("未检索相关记忆")
            root_causes.append("记忆利用不足")
            suggestions.append(ImprovementSuggestion(
                scenario="处理用户请求",
                recommended_action="先检索相关历史记忆",
                reason="可以提供更个性化的响应",
                priority=1,
                confidence=0.6,
                category="memory_usage"
            ))
        
        analysis = "; ".join(analysis_parts) if analysis_parts else "任务执行失败，原因不明"
        root_cause = root_causes[0] if root_causes else "未知原因"
        
        return analysis, root_cause, suggestions
    
    def _analyze_error(
        self,
        error_message: str,
        context: ReflectionContext
    ) -> Dict[str, Any]:
        """分析具体错误"""
        for pattern_name, pattern_config in self.patterns.ERROR_PATTERNS.items():
            for keyword in pattern_config["keywords"]:
                if keyword in error_message:
                    suggestion = self._create_suggestion_from_pattern(
                        pattern_name,
                        pattern_config,
                        context
                    )
                    
                    return {
                        "analysis": f"检测到{pattern_name}类型错误: {error_message}",
                        "root_cause": pattern_name,
                        "suggestions": [suggestion] if suggestion else []
                    }
        
        return {
            "analysis": f"未分类错误: {error_message}",
            "root_cause": "unknown_error",
            "suggestions": [ImprovementSuggestion(
                scenario="遇到未知错误",
                recommended_action="记录错误详情并寻求人工干预",
                reason="需要进一步分析错误模式",
                priority=3,
                confidence=0.3,
                category="error_handling"
            )]
        }
    
    def _create_suggestion_from_pattern(
        self,
        pattern_name: str,
        pattern_config: Dict,
        context: ReflectionContext
    ) -> Optional[ImprovementSuggestion]:
        """从模式创建建议"""
        template = pattern_config.get("suggestion_template", "")
        
        data_type = self._extract_data_type(context.user_input)
        task_type = context.task_type
        tools = pattern_config.get("recommended_tools", [])
        
        scenario = f"执行{task_type}任务"
        action = template.format(
            data_type=data_type,
            task_type=task_type,
            tool=tools[0] if tools else "相关工具",
            input_type="用户",
            resource="资源",
            alternative="替代方案",
            model="模型"
        )
        
        return ImprovementSuggestion(
            scenario=scenario,
            recommended_action=action,
            reason=f"基于{pattern_name}错误模式的改进建议",
            priority=2,
            confidence=0.7,
            category="error_prevention",
            tags=[pattern_name]
        )
    
    def _extract_data_type(self, text: str) -> str:
        """从文本中提取数据类型"""
        data_keywords = {
            "房价": "房价",
            "成交": "成交数据",
            "小区": "小区信息",
            "政策": "政策信息",
            "贷款": "贷款信息",
            "税费": "税费信息"
        }
        
        for keyword, data_type in data_keywords.items():
            if keyword in text:
                return data_type
        
        return "相关"
    
    def analyze_success(
        self,
        context: ReflectionContext
    ) -> Tuple[str, List[ImprovementSuggestion]]:
        """分析成功经验"""
        analysis_parts = []
        suggestions = []
        
        if context.task_duration < 5 and context.task_success:
            analysis_parts.append(f"高效完成任务，耗时{context.task_duration:.1f}秒")
            
            if context.tools_used:
                suggestions.append(ImprovementSuggestion(
                    scenario=f"执行{context.task_type}任务",
                    recommended_action=f"优先使用{context.tools_used[0]}工具",
                    reason="已验证该工具在此场景下高效可靠",
                    priority=1,
                    confidence=0.8,
                    category="best_practice"
                ))
        
        if context.user_feedback == "like":
            analysis_parts.append("获得用户正面反馈")
            suggestions.append(ImprovementSuggestion(
                scenario="类似用户请求",
                recommended_action="采用相同的响应策略",
                reason="用户对此策略表示满意",
                priority=1,
                confidence=0.9,
                category="user_preference"
            ))
        
        analysis = "; ".join(analysis_parts) if analysis_parts else "任务成功完成"
        
        return analysis, suggestions
    
    def analyze_performance_trend(
        self,
        recent_contexts: List[ReflectionContext]
    ) -> Dict[str, Any]:
        """分析性能趋势"""
        if not recent_contexts:
            return {"trend": "no_data"}
        
        success_rate = sum(1 for c in recent_contexts if c.task_success) / len(recent_contexts)
        avg_duration = sum(c.task_duration for c in recent_contexts) / len(recent_contexts)
        
        positive_feedback_rate = sum(
            1 for c in recent_contexts if c.user_feedback == "like"
        ) / len(recent_contexts)
        
        trend = "stable"
        if success_rate < 0.7:
            trend = "declining"
        elif success_rate > 0.9 and positive_feedback_rate > 0.5:
            trend = "improving"
        
        return {
            "trend": trend,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "positive_feedback_rate": positive_feedback_rate,
            "sample_size": len(recent_contexts)
        }


class TrainingSampleGenerator:
    """训练样本生成器"""
    
    def generate_samples(
        self,
        reflection_result: ReflectionResult
    ) -> List[Dict[str, Any]]:
        """从反思结果生成训练样本"""
        samples = []
        
        for suggestion in reflection_result.suggestions:
            sample = self._create_preference_sample(suggestion, reflection_result)
            if sample:
                samples.append(sample)
        
        if reflection_result.context and not reflection_result.context.task_success:
            sample = self._create_negative_sample(reflection_result)
            if sample:
                samples.append(sample)
        
        if reflection_result.context and reflection_result.context.task_success:
            sample = self._create_positive_sample(reflection_result)
            if sample:
                samples.append(sample)
        
        return samples
    
    def _create_preference_samples(
        self,
        suggestion: ImprovementSuggestion,
        result: ReflectionResult
    ) -> Optional[Dict[str, Any]]:
        """创建偏好学习样本"""
        if not result.context:
            return None
        
        return {
            "type": "preference",
            "state": {
                "task_type": result.context.task_type,
                "user_input": result.context.user_input[:200],
                "scenario": suggestion.scenario
            },
            "preferred_action": suggestion.recommended_action,
            "reason": suggestion.reason,
            "confidence": suggestion.confidence,
            "source": "reflection"
        }
    
    def _create_negative_sample(
        self,
        result: ReflectionResult
    ) -> Optional[Dict[str, Any]]:
        """创建负样本"""
        if not result.context:
            return None
        
        return {
            "type": "negative",
            "state": {
                "task_type": result.context.task_type,
                "user_input": result.context.user_input[:200]
            },
            "action_taken": {
                "tools_used": result.context.tools_used,
                "response_preview": result.context.agent_response[:200]
            },
            "outcome": "failure",
            "root_cause": result.root_cause,
            "source": "reflection"
        }
    
    def _create_positive_sample(
        self,
        result: ReflectionResult
    ) -> Optional[Dict[str, Any]]:
        """创建正样本"""
        if not result.context:
            return None
        
        return {
            "type": "positive",
            "state": {
                "task_type": result.context.task_type,
                "user_input": result.context.user_input[:200]
            },
            "action_taken": {
                "tools_used": result.context.tools_used,
                "response_preview": result.context.agent_response[:200]
            },
            "outcome": "success",
            "duration": result.context.task_duration,
            "user_feedback": result.context.user_feedback,
            "source": "reflection"
        }


class ReflectionModule:
    """反思模块主类"""
    
    def __init__(self):
        self.analyzer = ReflectionAnalyzer()
        self.sample_generator = TrainingSampleGenerator()
        
        self._reflection_history: Dict[str, List[ReflectionResult]] = {}
        self._pending_reflections: List[ReflectionContext] = []
        self._scheduled_times: Dict[str, datetime] = {}
    
    async def reflect_on_failure(
        self,
        context: ReflectionContext
    ) -> ReflectionResult:
        """对失败任务进行反思"""
        analysis, root_cause, suggestions = self.analyzer.analyze_failure(context)
        
        result = ReflectionResult(
            agent_id=context.agent_id,
            trigger=ReflectionTrigger.TASK_FAILURE,
            reflection_type=ReflectionType.ERROR_DIAGNOSIS,
            context=context,
            analysis=analysis,
            root_cause=root_cause,
            suggestions=suggestions
        )
        
        result.training_samples = self.sample_generator.generate_samples(result)
        
        result.metrics = {
            "error_count": len(context.error_messages),
            "tools_used_count": len(context.tools_used),
            "memory_retrieved_count": len(context.memory_retrieved)
        }
        
        await self._store_reflection(result)
        self._add_to_history(result)
        
        return result
    
    async def reflect_on_feedback(
        self,
        context: ReflectionContext
    ) -> ReflectionResult:
        """对用户反馈进行反思"""
        if context.user_feedback == "dislike":
            analysis, root_cause, suggestions = self.analyzer.analyze_failure(context)
            trigger = ReflectionTrigger.USER_DISLIKE
        else:
            analysis, suggestions = self.analyzer.analyze_success(context)
            root_cause = ""
            trigger = ReflectionTrigger.TASK_FAILURE if context.user_feedback == "dislike" else ReflectionTrigger.MANUAL
        
        result = ReflectionResult(
            agent_id=context.agent_id,
            trigger=trigger,
            reflection_type=ReflectionType.TASK_ANALYSIS,
            context=context,
            analysis=analysis,
            root_cause=root_cause,
            suggestions=suggestions
        )
        
        result.training_samples = self.sample_generator.generate_samples(result)
        
        await self._store_reflection(result)
        self._add_to_history(result)
        
        return result
    
    async def scheduled_reflection(
        self,
        agent_id: str,
        time_range: timedelta = timedelta(hours=24)
    ) -> ReflectionResult:
        """定时反思"""
        contexts = await self._get_recent_contexts(agent_id, time_range)
        
        if not contexts:
            return ReflectionResult(
                agent_id=agent_id,
                trigger=ReflectionTrigger.SCHEDULED,
                reflection_type=ReflectionType.TASK_ANALYSIS,
                analysis="无近期任务记录"
            )
        
        trend_analysis = self.analyzer.analyze_performance_trend(contexts)
        
        all_suggestions = []
        for ctx in contexts:
            if not ctx.task_success:
                _, _, suggestions = self.analyzer.analyze_failure(ctx)
                all_suggestions.extend(suggestions)
        
        unique_suggestions = self._deduplicate_suggestions(all_suggestions)
        
        result = ReflectionResult(
            agent_id=agent_id,
            trigger=ReflectionTrigger.SCHEDULED,
            reflection_type=ReflectionType.STRATEGY_IMPROVEMENT,
            analysis=f"过去{time_range.total_seconds()/3600:.0f}小时内完成{len(contexts)}个任务，成功率{trend_analysis['success_rate']:.1%}",
            root_cause=f"性能趋势: {trend_analysis['trend']}",
            suggestions=unique_suggestions[:5],
            metrics=trend_analysis
        )
        
        result.training_samples = self.sample_generator.generate_samples(result)
        
        await self._store_reflection(result)
        self._add_to_history(result)
        
        return result
    
    async def reflect_on_pattern(
        self,
        agent_id: str,
        pattern_type: str
    ) -> Optional[ReflectionResult]:
        """对特定模式进行反思"""
        history = self._reflection_history.get(agent_id, [])
        
        if not history:
            return None
        
        recent_results = history[-20:]
        
        if pattern_type == "error_pattern":
            error_contexts = [
                r.context for r in recent_results
                if r.context and not r.context.task_success
            ]
            
            if not error_contexts:
                return None
            
            common_errors = self._find_common_errors(error_contexts)
            
            return ReflectionResult(
                agent_id=agent_id,
                trigger=ReflectionTrigger.ERROR_PATTERN,
                reflection_type=ReflectionType.ERROR_DIAGNOSIS,
                analysis=f"发现{len(common_errors)}个常见错误模式",
                root_cause=common_errors[0] if common_errors else "未知",
                suggestions=[
                    ImprovementSuggestion(
                        scenario="常见错误场景",
                        recommended_action="添加预防性检查",
                        reason=f"错误'{common_errors[0]}'频繁出现" if common_errors else "",
                        priority=3,
                        confidence=0.9,
                        category="error_prevention"
                    )
                ]
            )
        
        return None
    
    def _find_common_errors(self, contexts: List[ReflectionContext]) -> List[str]:
        """找出常见错误"""
        error_counts: Dict[str, int] = {}
        
        for ctx in contexts:
            for error in ctx.error_messages:
                error_key = error[:50]
                error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [e[0] for e in sorted_errors[:3]]
    
    def _deduplicate_suggestions(
        self,
        suggestions: List[ImprovementSuggestion]
    ) -> List[ImprovementSuggestion]:
        """去重建议"""
        seen = set()
        unique = []
        
        for s in suggestions:
            key = (s.scenario, s.recommended_action)
            if key not in seen:
                seen.add(key)
                unique.append(s)
        
        return unique
    
    def _add_to_history(self, result: ReflectionResult):
        """添加到历史记录"""
        if result.agent_id not in self._reflection_history:
            self._reflection_history[result.agent_id] = []
        
        self._reflection_history[result.agent_id].append(result)
        
        max_history = 100
        if len(self._reflection_history[result.agent_id]) > max_history:
            self._reflection_history[result.agent_id] = self._reflection_history[result.agent_id][-max_history:]
    
    async def _store_reflection(self, result: ReflectionResult):
        """存储反思结果到数据库"""
        try:
            from ..database import get_db_connection
            
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        INSERT INTO reflection_records 
                        (id, agent_id, task_id, trigger, reflection_type, context, analysis, 
                         root_cause, suggestions, training_samples, metrics, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP)
                    """, (
                        result.id,
                        result.agent_id,
                        result.context.task_id if result.context else "",
                        result.trigger.value,
                        result.reflection_type.value,
                        json.dumps(result.context.to_dict()) if result.context else None,
                        result.analysis,
                        result.root_cause,
                        json.dumps([s.to_dict() for s in result.suggestions]),
                        json.dumps(result.training_samples),
                        json.dumps(result.metrics)
                    ))
                    await conn.commit()
                finally:
                    await conn.close()
        except Exception as e:
            print(f"存储反思结果失败: {e}")
    
    async def _get_recent_contexts(
        self,
        agent_id: str,
        time_range: timedelta
    ) -> List[ReflectionContext]:
        """获取近期上下文"""
        history = self._reflection_history.get(agent_id, [])
        cutoff_time = time.time() - time_range.total_seconds()
        
        contexts = []
        for result in reversed(history):
            if result.created_at < cutoff_time:
                break
            if result.context:
                contexts.append(result.context)
        
        return contexts
    
    def get_suggestions_for_scenario(
        self,
        agent_id: str,
        scenario_keywords: List[str]
    ) -> List[ImprovementSuggestion]:
        """获取特定场景的建议"""
        history = self._reflection_history.get(agent_id, [])
        
        relevant_suggestions = []
        for result in history:
            for suggestion in result.suggestions:
                if any(kw in suggestion.scenario for kw in scenario_keywords):
                    relevant_suggestions.append(suggestion)
        
        return relevant_suggestions[-10:]
    
    def get_reflection_summary(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """获取反思摘要"""
        history = self._reflection_history.get(agent_id, [])
        
        if not history:
            return {
                "total_reflections": 0,
                "recent_suggestions": [],
                "common_issues": []
            }
        
        recent = history[-10:]
        
        all_suggestions = []
        for r in recent:
            all_suggestions.extend(r.suggestions)
        
        return {
            "total_reflections": len(history),
            "recent_reflections": len(recent),
            "recent_suggestions": [s.format() for s in all_suggestions[:5]],
            "training_samples_generated": sum(len(r.training_samples) for r in recent)
        }


reflection_module = ReflectionModule()
