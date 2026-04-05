"""
任务解析智能体
Task Parser Agent - 精准理解用户的分析需求

工部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import re


class TaskType(Enum):
    COMMUNITY_ANALYSIS = "community_analysis"
    REGIONAL_COMPARISON = "regional_comparison"
    PRICE_PREDICTION = "price_prediction"
    INVESTMENT_RETURN = "investment_return"
    PURCHASING_POWER = "purchasing_power"
    RENTAL_ANALYSIS = "rental_analysis"
    SCHOOL_DISTRICT_ANALYSIS = "school_district_analysis"
    MARKET_TREND = "market_trend"


class TaskStatus(Enum):
    PENDING = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    PREMIUM = 5


class ParameterStatus(Enum):
    PROVIDED = "provided"
    INFERRED = "inferred"
    MISSING = "missing"
    INVALID = "invalid"


@dataclass
class TaskParameter:
    name: str
    value: Any
    status: ParameterStatus
    source: str
    confidence: float
    validation_message: str = ""
    alternatives: List[Any] = field(default_factory=list)


@dataclass
class TaskIntent:
    intent_id: str
    task_type: TaskType
    description: str
    parameters: Dict[str, TaskParameter]
    priority: TaskPriority
    subtasks: List[str]
    dependencies: List[str]
    estimated_duration_seconds: int
    required_data_sources: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ParsedTask:
    task_id: str
    intent: TaskIntent
    status: TaskStatus
    missing_parameters: List[str]
    clarification_questions: List[str]
    assigned_agents: List[str]
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ParameterExtractor:
    PARAMETER_PATTERNS = {
        "region": r"(南山|福田|罗湖|宝安|龙岗|龙华|光明|坪山|盐田|大鹏)[区县]?",
        "community": r"([\u4e00-\u9fa5]{2,10})(小区|花园|城|苑|府|院|湾|庭)",
        "budget_min": r"预算(\d+)(万|w)?(?:以上|起)?",
        "budget_max": r"预算(?:.*?)(\d+)(万|w)?(?:以下|以内)?",
        "area_min": r"(\d+)(?:平米|平|m²)?(?:以上|起)?",
        "area_max": r"(\d+)(?:平米|平|m²)?(?:以下|以内)?",
        "room_count": r"(\d)室|(\d)房|(\d)居",
        "age_max": r"房龄(\d+)(?:年)?(?:以下|以内)?",
        "floor_preference": r"(\d+)[层楼](?:以下|以上)?",
    }

    def __init__(self):
        self.default_values = {
            "budget_min": 100,
            "budget_max": 1000,
            "area_min": 50,
            "area_max": 200,
            "room_count": 3,
            "age_max": 20,
        }

    def extract(self, text: str) -> Dict[str, TaskParameter]:
        parameters = {}

        for param_name, pattern in self.PARAMETER_PATTERNS.items():
            matches = re.findall(pattern, text)

            if matches:
                value = self._process_match(param_name, matches)
                parameters[param_name] = TaskParameter(
                    name=param_name,
                    value=value,
                    status=ParameterStatus.PROVIDED,
                    source="user_input",
                    confidence=0.9,
                )

        return parameters

    def _process_match(self, param_name: str, matches: List) -> Any:
        if param_name in ["budget_min", "budget_max"]:
            return int(matches[0][0]) if matches else None
        elif param_name in ["area_min", "area_max", "age_max"]:
            return int(matches[0]) if matches else None
        elif param_name == "room_count":
            for match in matches[0]:
                if match:
                    return int(match)
            return None
        else:
            return matches[0] if matches else None

    def infer_from_context(
        self,
        parameters: Dict[str, TaskParameter],
        user_history: List[Dict] = None,
    ) -> Dict[str, TaskParameter]:
        inferred = parameters.copy()

        for param_name, default_value in self.default_values.items():
            if param_name not in inferred:
                if user_history:
                    historical_value = self._extract_from_history(
                        param_name, user_history
                    )
                    if historical_value:
                        inferred[param_name] = TaskParameter(
                            name=param_name,
                            value=historical_value,
                            status=ParameterStatus.INFERRED,
                            source="user_history",
                            confidence=0.6,
                        )
                        continue

                inferred[param_name] = TaskParameter(
                    name=param_name,
                    value=default_value,
                    status=ParameterStatus.INFERRED,
                    source="default",
                    confidence=0.3,
                )

        return inferred

    def _extract_from_history(
        self, param_name: str, history: List[Dict]
    ) -> Optional[Any]:
        for interaction in reversed(history):
            params = interaction.get("parameters", {})
            if param_name in params:
                return params[param_name]
        return None


class TaskDecomposer:
    TASK_DEPENDENCIES = {
        TaskType.REGIONAL_COMPARISON: [
            "data_collection",
            "price_analysis",
            "comparison_report",
        ],
        TaskType.INVESTMENT_RETURN: [
            "price_collection",
            "rental_data",
            "roi_calculation",
            "risk_assessment",
        ],
        TaskType.PRICE_PREDICTION: [
            "historical_data",
            "market_analysis",
            "prediction_model",
            "confidence_interval",
        ],
        TaskType.COMMUNITY_ANALYSIS: [
            "basic_info",
            "price_trend",
            "surrounding_facilities",
            "traffic_info",
            "school_district",
        ],
    }

    def __init__(self):
        self.subtask_templates: Dict[str, Dict] = {}

    def decompose(self, task_type: TaskType, parameters: Dict[str, TaskParameter]) -> List[str]:
        base_subtasks = self.TASK_DEPENDENCIES.get(task_type, [])

        customized = []
        for subtask in base_subtasks:
            customized.append(f"{subtask}_{task_type.value}")

        if "region" in parameters:
            region = parameters["region"].value
            customized = [f"{s}_{region}" for s in base_subtasks]

        return customized

    def get_dependencies(self, subtasks: List[str]) -> List[Tuple[str, str]]:
        dependencies = []

        for i in range(len(subtasks) - 1):
            dependencies.append((subtasks[i], subtasks[i + 1]))

        return dependencies


class PriorityCalculator:
    def __init__(self):
        self.premium_multiplier = 2.0
        self.urgency_keywords = {
            TaskPriority.URGENT: ["紧急", "立即", "马上", "急"],
            TaskPriority.HIGH: ["尽快", "今天", "明天"],
        }

    def calculate(
        self,
        task_type: TaskType,
        user_tier: str = "free",
        text: str = "",
        deadline: datetime = None,
    ) -> TaskPriority:
        base_priority = TaskPriority.NORMAL

        for priority, keywords in self.urgency_keywords.items():
            if any(kw in text for kw in keywords):
                base_priority = priority
                break

        if user_tier == "premium":
            if base_priority.value < TaskPriority.PREMIUM.value:
                base_priority = TaskPriority.PREMIUM
        elif user_tier == "vip":
            if base_priority.value < TaskPriority.HIGH.value:
                base_priority = TaskPriority.HIGH

        if deadline:
            time_until_deadline = deadline - datetime.utcnow()
            if time_until_deadline < timedelta(hours=1):
                base_priority = TaskPriority.URGENT
            elif time_until_deadline < timedelta(hours=24):
                if base_priority.value < TaskPriority.HIGH.value:
                    base_priority = TaskPriority.HIGH

        return base_priority


class TaskCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, Dict] = {}
        self.access_order: List[str] = []

    def get_cache_key(self, task_type: TaskType, parameters: Dict[str, TaskParameter]) -> str:
        param_str = json.dumps(
            {k: v.value for k, v in sorted(parameters.items())},
            sort_keys=True,
        )
        return f"{task_type.value}_{hash(param_str)}"

    def get(self, task_type: TaskType, parameters: Dict[str, TaskParameter]) -> Optional[Dict]:
        key = self.get_cache_key(task_type, parameters)

        if key in self.cache:
            cached = self.cache[key]

            if cached.get("expires_at"):
                if datetime.fromisoformat(cached["expires_at"]) < datetime.utcnow():
                    del self.cache[key]
                    return None

            self._update_access_order(key)
            return cached.get("result")

        return None

    def set(
        self,
        task_type: TaskType,
        parameters: Dict[str, TaskParameter],
        result: Dict,
        ttl_seconds: int = 3600,
    ) -> None:
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        key = self.get_cache_key(task_type, parameters)
        self.cache[key] = {
            "result": result,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
        }
        self.access_order.append(key)

    def _update_access_order(self, key: str) -> None:
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    def _evict_oldest(self) -> None:
        if self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]


class TaskParserAgent:
    def __init__(self, agent_id: str = "task_parser_001"):
        self.agent_id = agent_id
        self.parameter_extractor = ParameterExtractor()
        self.task_decomposer = TaskDecomposer()
        self.priority_calculator = PriorityCalculator()
        self.task_cache = TaskCache()

        self.task_type_keywords: Dict[TaskType, List[str]] = {
            TaskType.COMMUNITY_ANALYSIS: ["小区分析", "楼盘详情", "小区报告"],
            TaskType.REGIONAL_COMPARISON: ["区域对比", "对比分析", "哪个好"],
            TaskType.PRICE_PREDICTION: ["房价预测", "未来走势", "会涨吗"],
            TaskType.INVESTMENT_RETURN: ["投资回报", "收益率", "租金回报"],
            TaskType.PURCHASING_POWER: ["购房能力", "能买", "买得起"],
            TaskType.SCHOOL_DISTRICT_ANALYSIS: ["学区分析", "学校", "学位"],
        }

        self.parsed_tasks: List[ParsedTask] = []

    def _identify_task_type(self, text: str) -> Tuple[TaskType, float]:
        text_lower = text.lower()
        scores: Dict[TaskType, float] = {}

        for task_type, keywords in self.task_type_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                scores[task_type] = matches / len(keywords)

        if not scores:
            return TaskType.COMMUNITY_ANALYSIS, 0.3

        best = max(scores.items(), key=lambda x: x[1])
        return best[0], best[1]

    async def parse(
        self,
        text: str,
        user_id: str = None,
        user_tier: str = "free",
        user_history: List[Dict] = None,
        deadline: datetime = None,
    ) -> ParsedTask:
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        task_type, confidence = self._identify_task_type(text)

        parameters = self.parameter_extractor.extract(text)

        parameters = self.parameter_extractor.infer_from_context(
            parameters, user_history
        )

        priority = self.priority_calculator.calculate(
            task_type, user_tier, text, deadline
        )

        subtasks = self.task_decomposer.decompose(task_type, parameters)
        dependencies = self.task_decomposer.get_dependencies(subtasks)

        missing_params = [
            name
            for name, param in parameters.items()
            if param.status == ParameterStatus.MISSING
        ]

        clarification_questions = self._generate_clarification_questions(
            missing_params, task_type
        )

        intent = TaskIntent(
            intent_id=f"intent_{task_id}",
            task_type=task_type,
            description=text,
            parameters=parameters,
            priority=priority,
            subtasks=subtasks,
            dependencies=[f"{d[0]}->{d[1]}" for d in dependencies],
            estimated_duration_seconds=self._estimate_duration(task_type, subtasks),
            required_data_sources=self._get_required_data_sources(task_type),
        )

        parsed = ParsedTask(
            task_id=task_id,
            intent=intent,
            status=TaskStatus.PARSED,
            missing_parameters=missing_params,
            clarification_questions=clarification_questions,
            assigned_agents=[],
        )

        self.parsed_tasks.append(parsed)

        return parsed

    def _generate_clarification_questions(
        self, missing_params: List[str], task_type: TaskType
    ) -> List[str]:
        questions = {
            "region": "请问您想分析哪个区域？",
            "community": "请问您想了解哪个小区？",
            "budget_max": "请问您的预算大概是多少？",
            "area_min": "请问您需要多大的面积？",
            "room_count": "请问您需要几居室？",
        }

        return [questions.get(p, f"请提供{p}信息") for p in missing_params[:3]]

    def _estimate_duration(
        self, task_type: TaskType, subtasks: List[str]
    ) -> int:
        base_durations = {
            TaskType.COMMUNITY_ANALYSIS: 30,
            TaskType.REGIONAL_COMPARISON: 60,
            TaskType.PRICE_PREDICTION: 45,
            TaskType.INVESTMENT_RETURN: 40,
            TaskType.PURCHASING_POWER: 20,
        }

        base = base_durations.get(task_type, 30)
        return base + len(subtasks) * 5

    def _get_required_data_sources(self, task_type: TaskType) -> List[str]:
        sources = {
            TaskType.COMMUNITY_ANALYSIS: ["property_db", "price_history", "facility_db"],
            TaskType.REGIONAL_COMPARISON: ["property_db", "price_history", "statistics"],
            TaskType.PRICE_PREDICTION: ["price_history", "market_trend", "policy_db"],
            TaskType.INVESTMENT_RETURN: ["rental_db", "price_history", "market_trend"],
        }
        return sources.get(task_type, ["property_db"])

    async def update_with_clarification(
        self,
        task_id: str,
        clarification_responses: Dict[str, Any],
    ) -> Optional[ParsedTask]:
        task = next((t for t in self.parsed_tasks if t.task_id == task_id), None)

        if not task:
            return None

        for param_name, value in clarification_responses.items():
            if param_name in task.intent.parameters:
                task.intent.parameters[param_name] = TaskParameter(
                    name=param_name,
                    value=value,
                    status=ParameterStatus.PROVIDED,
                    source="clarification",
                    confidence=1.0,
                )

        task.missing_parameters = [
            name
            for name, param in task.intent.parameters.items()
            if param.status == ParameterStatus.MISSING
        ]

        if not task.missing_parameters:
            task.status = TaskStatus.DISPATCHED

        return task

    def check_cache(
        self, task_type: TaskType, parameters: Dict[str, TaskParameter]
    ) -> Optional[Dict]:
        return self.task_cache.get(task_type, parameters)

    def cache_result(
        self,
        task_type: TaskType,
        parameters: Dict[str, TaskParameter],
        result: Dict,
        ttl_seconds: int = 3600,
    ) -> None:
        self.task_cache.set(task_type, parameters, result, ttl_seconds)

    def get_task(self, task_id: str) -> Optional[ParsedTask]:
        return next((t for t in self.parsed_tasks if t.task_id == task_id), None)

    def get_pending_tasks(self) -> List[ParsedTask]:
        return [
            t
            for t in self.parsed_tasks
            if t.status in [TaskStatus.PENDING, TaskStatus.PARSED]
        ]

    def get_task_stats(self) -> Dict[str, Any]:
        if not self.parsed_tasks:
            return {"total": 0}

        type_counts: Dict[str, int] = {}
        for task in self.parsed_tasks:
            tt = task.intent.task_type.value
            type_counts[tt] = type_counts.get(tt, 0) + 1

        return {
            "total": len(self.parsed_tasks),
            "by_type": type_counts,
            "cache_size": len(self.task_cache.cache),
        }
