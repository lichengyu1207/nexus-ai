"""
认知负荷监测 - 简明模式切换
当用户连续提出复杂问题时，自动切换至"简明模式"，避免信息过载
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"


class CognitiveState(Enum):
    RELAXED = "relaxed"
    ENGAGED = "engaged"
    STRESSED = "stressed"
    OVERLOADED = "overloaded"


class ResponseMode(Enum):
    DETAILED = "detailed"
    STANDARD = "standard"
    CONCISE = "concise"
    MINIMAL = "minimal"


@dataclass
class QueryAnalysis:
    query_id: str
    query_text: str
    timestamp: datetime
    word_count: int
    sentence_count: int
    question_count: int
    technical_terms: List[str]
    complexity_score: float
    complexity_level: ComplexityLevel
    topic_domains: List[str]
    has_multiple_parts: bool
    requires_calculation: bool
    requires_comparison: bool
    requires_analysis: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "question_count": self.question_count,
            "complexity_score": round(self.complexity_score, 2),
            "complexity_level": self.complexity_level.value,
            "has_multiple_parts": self.has_multiple_parts,
            "requires_calculation": self.requires_calculation,
            "requires_comparison": self.requires_comparison,
            "requires_analysis": self.requires_analysis
        }


@dataclass
class CognitiveLoadMetrics:
    session_id: str
    timestamp: datetime
    cumulative_complexity: float
    query_frequency: float
    avg_response_time: float
    error_rate: float
    interaction_depth: int
    cognitive_state: CognitiveState
    recommended_mode: ResponseMode
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "cumulative_complexity": round(self.cumulative_complexity, 2),
            "query_frequency": round(self.query_frequency, 2),
            "cognitive_state": self.cognitive_state.value,
            "recommended_mode": self.recommended_mode.value
        }


@dataclass
class SessionContext:
    session_id: str
    user_id: str
    started_at: datetime
    query_history: List[QueryAnalysis] = field(default_factory=list)
    current_mode: ResponseMode = ResponseMode.STANDARD
    load_history: List[CognitiveLoadMetrics] = field(default_factory=list)
    mode_transitions: List[Dict[str, Any]] = field(default_factory=list)
    total_queries: int = 0
    avg_complexity: float = 0.0


class QueryComplexityAnalyzer:
    TECHNICAL_TERMS = {
        "算法", "模型", "架构", "神经网络", "机器学习", "深度学习",
        "优化", "收敛", "梯度", "反向传播", "损失函数", "正则化",
        "评估", "估值", "收益率", "折现", "现金流", "资产负债",
        "合规", "审计", "风险", "监管", "隐私", "数据保护",
        "API", "微服务", "分布式", "容器", "编排", "负载均衡"
    }
    
    COMPLEXITY_INDICATORS = [
        r"分析", r"比较", r"评估", r"计算", r"推导",
        r"为什么", r"如何", r"原理", r"机制", r"关系",
        r"多个", r"所有", r"综合", r"整体", r"系统"
    ]
    
    def __init__(self):
        self._complexity_weights = {
            "word_count": 0.1,
            "sentence_count": 0.15,
            "question_count": 0.2,
            "technical_terms": 0.25,
            "complexity_indicators": 0.3
        }
        
    def analyze(self, query: str) -> QueryAnalysis:
        query_id = f"q_{hash(query) % 1000000}_{datetime.now().timestamp()}"
        
        words = query.split()
        word_count = len(words)
        
        sentences = re.split(r'[。！？.!?]', query)
        sentence_count = len([s for s in sentences if s.strip()])
        
        question_count = query.count('?') + query.count('？')
        question_count += query.count('吗') + query.count('呢')
        
        technical_terms = self._extract_technical_terms(query)
        
        complexity_indicators = self._count_complexity_indicators(query)
        
        has_multiple_parts = question_count > 1 or '和' in query or '以及' in query
        
        requires_calculation = any(
            kw in query for kw in ['计算', '多少', '求', '等于', '比率', '百分比']
        )
        
        requires_comparison = any(
            kw in query for kw in ['比较', '对比', '区别', '差异', '优劣']
        )
        
        requires_analysis = any(
            kw in query for kw in ['分析', '原因', '影响', '趋势', '规律']
        )
        
        complexity_score = self._calculate_complexity(
            word_count=word_count,
            sentence_count=sentence_count,
            question_count=question_count,
            technical_term_count=len(technical_terms),
            indicator_count=complexity_indicators
        )
        
        complexity_level = self._determine_complexity_level(complexity_score)
        
        topic_domains = self._extract_domains(query)
        
        return QueryAnalysis(
            query_id=query_id,
            query_text=query,
            timestamp=datetime.now(),
            word_count=word_count,
            sentence_count=sentence_count,
            question_count=question_count,
            technical_terms=technical_terms,
            complexity_score=complexity_score,
            complexity_level=complexity_level,
            topic_domains=topic_domains,
            has_multiple_parts=has_multiple_parts,
            requires_calculation=requires_calculation,
            requires_comparison=requires_comparison,
            requires_analysis=requires_analysis
        )
        
    def _extract_technical_terms(self, query: str) -> List[str]:
        found = []
        for term in self.TECHNICAL_TERMS:
            if term in query:
                found.append(term)
        return found
        
    def _count_complexity_indicators(self, query: str) -> int:
        count = 0
        for pattern in self.COMPLEXITY_INDICATORS:
            matches = re.findall(pattern, query)
            count += len(matches)
        return count
        
    def _calculate_complexity(
        self,
        word_count: int,
        sentence_count: int,
        question_count: int,
        technical_term_count: int,
        indicator_count: int
    ) -> float:
        word_score = min(word_count / 50, 1.0)
        sentence_score = min(sentence_count / 5, 1.0)
        question_score = min(question_count / 3, 1.0)
        tech_score = min(technical_term_count / 5, 1.0)
        indicator_score = min(indicator_count / 5, 1.0)
        
        complexity = (
            word_score * self._complexity_weights["word_count"] +
            sentence_score * self._complexity_weights["sentence_count"] +
            question_score * self._complexity_weights["question_count"] +
            tech_score * self._complexity_weights["technical_terms"] +
            indicator_score * self._complexity_weights["complexity_indicators"]
        )
        
        return complexity
        
    def _determine_complexity_level(self, score: float) -> ComplexityLevel:
        if score < 0.25:
            return ComplexityLevel.SIMPLE
        elif score < 0.5:
            return ComplexityLevel.MODERATE
        elif score < 0.75:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.HIGHLY_COMPLEX
            
    def _extract_domains(self, query: str) -> List[str]:
        domains = []
        
        domain_keywords = {
            "估值": ["估值", "评估", "房产", "资产", "价格"],
            "合规": ["合规", "审计", "监管", "法律", "政策"],
            "技术": ["技术", "系统", "架构", "代码", "API"],
            "经济": ["经济", "市场", "投资", "收益", "成本"],
            "分析": ["分析", "数据", "统计", "趋势", "报告"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in query for kw in keywords):
                domains.append(domain)
                
        return domains


class CognitiveLoadMonitor:
    def __init__(self):
        self._sessions: Dict[str, SessionContext] = {}
        self._complexity_analyzer = QueryComplexityAnalyzer()
        self._overload_threshold = 0.7
        self._recovery_threshold = 0.4
        self._window_size = 10
        self._time_window_minutes = 15
        
    def start_session(self, session_id: str, user_id: str) -> SessionContext:
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.now()
        )
        self._sessions[session_id] = context
        return context
        
    def process_query(
        self,
        session_id: str,
        query: str
    ) -> Tuple[QueryAnalysis, ResponseMode]:
        context = self._sessions.get(session_id)
        if not context:
            context = self.start_session(session_id, "unknown")
            
        analysis = self._complexity_analyzer.analyze(query)
        context.query_history.append(analysis)
        context.total_queries += 1
        
        metrics = self._calculate_load_metrics(context)
        context.load_history.append(metrics)
        
        if self._should_change_mode(context, metrics):
            new_mode = metrics.recommended_mode
            self._record_mode_transition(context, new_mode)
            context.current_mode = new_mode
            
        context.avg_complexity = sum(
            q.complexity_score for q in context.query_history
        ) / len(context.query_history)
        
        return analysis, context.current_mode
        
    def _calculate_load_metrics(
        self,
        context: SessionContext
    ) -> CognitiveLoadMetrics:
        recent_queries = context.query_history[-self._window_size:]
        
        cumulative_complexity = sum(q.complexity_score for q in recent_queries)
        
        if len(recent_queries) >= 2:
            time_diff = (recent_queries[-1].timestamp - recent_queries[0].timestamp).total_seconds()
            query_frequency = len(recent_queries) / max(time_diff / 60, 1)
        else:
            query_frequency = 1.0
            
        cognitive_state = self._determine_cognitive_state(
            cumulative_complexity, query_frequency
        )
        
        recommended_mode = self._recommend_mode(cognitive_state, cumulative_complexity)
        
        return CognitiveLoadMetrics(
            session_id=context.session_id,
            timestamp=datetime.now(),
            cumulative_complexity=cumulative_complexity,
            query_frequency=query_frequency,
            avg_response_time=0.0,
            error_rate=0.0,
            interaction_depth=len(recent_queries),
            cognitive_state=cognitive_state,
            recommended_mode=recommended_mode
        )
        
    def _determine_cognitive_state(
        self,
        cumulative_complexity: float,
        query_frequency: float
    ) -> CognitiveState:
        load_index = cumulative_complexity * (1 + query_frequency / 10)
        
        if load_index < 2:
            return CognitiveState.RELAXED
        elif load_index < 4:
            return CognitiveState.ENGAGED
        elif load_index < 6:
            return CognitiveState.STRESSED
        else:
            return CognitiveState.OVERLOADED
            
    def _recommend_mode(
        self,
        state: CognitiveState,
        cumulative_complexity: float
    ) -> ResponseMode:
        if state == CognitiveState.OVERLOADED:
            return ResponseMode.MINIMAL
        elif state == CognitiveState.STRESSED:
            return ResponseMode.CONCISE
        elif state == CognitiveState.ENGAGED:
            if cumulative_complexity > 3:
                return ResponseMode.CONCISE
            return ResponseMode.STANDARD
        else:
            return ResponseMode.DETAILED
            
    def _should_change_mode(
        self,
        context: SessionContext,
        metrics: CognitiveLoadMetrics
    ) -> bool:
        current_mode = context.current_mode
        recommended = metrics.recommended_mode
        
        if current_mode == recommended:
            return False
            
        if recommended == ResponseMode.MINIMAL:
            return True
            
        if recommended == ResponseMode.CONCISE:
            return metrics.cognitive_state == CognitiveState.STRESSED
            
        if recommended in [ResponseMode.STANDARD, ResponseMode.DETAILED]:
            if len(context.load_history) >= 3:
                recent_states = [m.cognitive_state for m in context.load_history[-3:]]
                if all(s != CognitiveState.OVERLOADED for s in recent_states):
                    return True
                    
        return False
        
    def _record_mode_transition(
        self,
        context: SessionContext,
        new_mode: ResponseMode
    ):
        context.mode_transitions.append({
            "from": context.current_mode.value,
            "to": new_mode.value,
            "timestamp": datetime.now().isoformat(),
            "trigger": "cognitive_load"
        })
        
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        context = self._sessions.get(session_id)
        if not context:
            return None
            
        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "current_mode": context.current_mode.value,
            "total_queries": context.total_queries,
            "avg_complexity": round(context.avg_complexity, 2),
            "current_state": context.load_history[-1].cognitive_state.value if context.load_history else "unknown",
            "mode_transitions": len(context.mode_transitions)
        }
        
    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]


class ResponseAdapter:
    def __init__(self, monitor: CognitiveLoadMonitor):
        self.monitor = monitor
        self._mode_templates = {
            ResponseMode.DETAILED: {
                "max_length": 2000,
                "include_examples": True,
                "include_references": True,
                "detail_level": "high",
                "explanation_depth": 3
            },
            ResponseMode.STANDARD: {
                "max_length": 1000,
                "include_examples": True,
                "include_references": False,
                "detail_level": "medium",
                "explanation_depth": 2
            },
            ResponseMode.CONCISE: {
                "max_length": 500,
                "include_examples": False,
                "include_references": False,
                "detail_level": "low",
                "explanation_depth": 1
            },
            ResponseMode.MINIMAL: {
                "max_length": 200,
                "include_examples": False,
                "include_references": False,
                "detail_level": "minimal",
                "explanation_depth": 0
            }
        }
        
    def adapt_response(
        self,
        session_id: str,
        response: str,
        mode: Optional[ResponseMode] = None
    ) -> Dict[str, Any]:
        if mode is None:
            context = self.monitor._sessions.get(session_id)
            mode = context.current_mode if context else ResponseMode.STANDARD
            
        template = self._mode_templates[mode]
        
        adapted = self._apply_template(response, template)
        
        return {
            "original_length": len(response),
            "adapted_length": len(adapted),
            "mode": mode.value,
            "template": template,
            "content": adapted
        }
        
    def _apply_template(
        self,
        response: str,
        template: Dict[str, Any]
    ) -> str:
        max_length = template["max_length"]
        
        if len(response) <= max_length:
            return response
            
        sentences = re.split(r'([。！？.!?])', response)
        
        result = ""
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if len(result) + len(sentence) <= max_length - 50:
                result += sentence
            else:
                break
                
        if result and not result.endswith(('。', '！', '？', '.', '!', '?')):
            result += "..."
            
        return result
        
    def get_mode_guidance(self, mode: ResponseMode) -> Dict[str, Any]:
        return self._mode_templates.get(mode, self._mode_templates[ResponseMode.STANDARD])


class CognitiveLoadSystem:
    def __init__(self):
        self.monitor = CognitiveLoadMonitor()
        self.adapter = ResponseAdapter(self.monitor)
        self._alert_callbacks: List[Callable] = []
        
    def register_alert_callback(self, callback: Callable):
        self._alert_callbacks.append(callback)
        
    async def process_interaction(
        self,
        session_id: str,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        if session_id not in self.monitor._sessions:
            self.monitor.start_session(session_id, user_id)
            
        analysis, mode = self.monitor.process_query(session_id, query)
        
        status = self.monitor.get_session_status(session_id)
        
        if status and status.get("current_state") == "overloaded":
            await self._trigger_overload_alert(session_id, status)
            
        return {
            "query_analysis": analysis.to_dict(),
            "response_mode": mode.value,
            "session_status": status,
            "mode_guidance": self.adapter.get_mode_guidance(mode)
        }
        
    async def _trigger_overload_alert(
        self,
        session_id: str,
        status: Dict[str, Any]
    ):
        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session_id, status)
                else:
                    callback(session_id, status)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
                
    def adapt_response(
        self,
        session_id: str,
        response: str
    ) -> Dict[str, Any]:
        return self.adapter.adapt_response(session_id, response)
        
    def get_current_mode(self, session_id: str) -> ResponseMode:
        context = self.monitor._sessions.get(session_id)
        return context.current_mode if context else ResponseMode.STANDARD
        
    def force_mode(
        self,
        session_id: str,
        mode: ResponseMode
    ):
        context = self.monitor._sessions.get(session_id)
        if context:
            context.current_mode = mode
            context.mode_transitions.append({
                "from": context.current_mode.value,
                "to": mode.value,
                "timestamp": datetime.now().isoformat(),
                "trigger": "manual"
            })


cognitive_load_system = CognitiveLoadSystem()


def get_cognitive_load_system() -> CognitiveLoadSystem:
    return cognitive_load_system


async def process_user_query(
    session_id: str,
    user_id: str,
    query: str
) -> Dict[str, Any]:
    return await cognitive_load_system.process_interaction(session_id, user_id, query)
