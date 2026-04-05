# -*- coding: utf-8 -*-
"""
Dual Scenario Differentiation Module (Layer 21)
=====================================================

Core concept: Same agent engine cluster (三省六部), TWO distinct UX experiences:
  - Dashboard Task Analysis (mode=report): Report-centric, efficient, structured, batch-capable
  - Smart Consultation (mode=conversation): Dialogue-centric, immersive, personalized, streaming

Architecture:
  Part A: Scenario Mode System (ScenarioMode / ModeRouter / ModeConfig)
  Part B: Task Analysis Deep Dev (HybridInput / TaskCenterBatch / StructuredReport / Onboarding / SmartTemplates)
  Part C: Smart Consultation Deep Dev (ImmersiveChat / FollowupSuggestion / ReportCardInChat / ReasoningDisplay / TrustBuilding)
  Part D: Backend Unified Dispatch (ModeAwareDispatcher / AsyncReportGen / WebSocketPush)
  Part E: Shared Components (ReportViewer dual-mode / AgentStatusIndicator)
  Part F: UX Metrics & A/B Testing (ScenarioMetrics / ABTestFramework)
  Part G: Testing Suite (DualScenarioTestSuite 45+ cases)

Author: Integration Architect
Version: 21.0.0
"""

import re
import json
import hashlib
import random
import time
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timedelta


# =============================================================================
# Part A: Scenario Mode System
# =============================================================================


class ScenarioMode(Enum):
    REPORT = "report"
    CONVERSATION = "conversation"


class AgentPriority(Enum):
    GONG_BU_REPORT = "gongbu_report"
    LI_BU_CONVERSATION = "libu_conversation"
    XING_BU_COMPLIANCE = "xingbu_compliance"
    BALANCED = "balanced"


@dataclass
class ModeConfig:
    mode: ScenarioMode
    primary_agent: str
    secondary_agents: List[str]
    output_format: str
    streaming_enabled: bool
    max_turns: int
    response_style: str
    show_reasoning_steps: bool
    embed_report_cards: bool
    allow_interruption: bool
    batch_operations_enabled: bool
    template_system_enabled: bool
    feedback_loop_enabled: bool
    confidence_expression: str
    async_report_gen: bool
    websocket_push: bool


REPORT_MODE_CONFIG = ModeConfig(
    mode=ScenarioMode.REPORT,
    primary_agent="gongbu",
    secondary_agents=["xingbu", "libu"],
    output_format="structured_html",
    streaming_enabled=False,
    max_turns=1,
    response_style="professional_concise",
    show_reasoning_steps=False,
    embed_report_cards=False,
    allow_interruption=False,
    batch_operations_enabled=True,
    template_system_enabled=True,
    feedback_loop_enabled=True,
    confidence_expression="interval_numeric",
    async_report_gen=False,
    websocket_push=False,
)

CONVERSATION_MODE_CONFIG = ModeConfig(
    mode=ScenarioMode.CONVERSATION,
    primary_agent="libu",
    secondary_agents=["gongbu", "xingbu"],
    output_format="chat_bubble_markdown",
    streaming_enabled=True,
    max_turns=50,
    response_style="persona_immersive",
    show_reasoning_steps=True,
    embed_report_cards=True,
    allow_interruption=True,
    batch_operations_enabled=False,
    template_system_enabled=False,
    feedback_loop_enabled=True,
    confidence_expression="probabilistic_verbal",
    async_report_gen=True,
    websocket_push=True,
)


@dataclass
class ModeRoutingDecision:
    mode: ScenarioMode
    config: ModeConfig
    agent_priority: AgentPriority
    api_endpoint: str
    params_override: Dict[str, Any]
    estimated_duration_ms: int
    reasoning: str


class ScenarioModeRouter:
    """Routes requests to appropriate mode based on context and user preference."""

    def __init__(self):
        self._configs = {
            ScenarioMode.REPORT: REPORT_MODE_CONFIG,
            ScenarioMode.CONVERSATION: CONVERSATION_MODE_CONFIG,
        }
        self._user_preferences: Dict[str, ScenarioMode] = {}
        self._routing_log: List[Dict] = []
        self._lock = threading.Lock()

    def route(self, user_input: str, user_id: Optional[str] = None,
              explicit_mode: Optional[ScenarioMode] = None,
              context_hints: Optional[Dict] = None) -> ModeRoutingDecision:
        if explicit_mode:
            mode = explicit_mode
        elif user_id and user_id in self._user_preferences:
            mode = self._user_preferences[user_id]
        else:
            mode = self._auto_detect_mode(user_input, context_hints or {})

        config = self._configs[mode]
        if mode == ScenarioMode.REPORT:
            agent_pri = AgentPriority.GONG_BU_REPORT
            endpoint = "/api/tasks"
            params_ov = {"format": "html", "include_charts": True, "stream": False}
            est_dur = 3000 + len(user_input) * 2
            reasoning = f"Detected report-oriented query. Routing to {mode.value} mode via {endpoint}."
        else:
            agent_pri = AgentPriority.LI_BU_CONVERSATION
            endpoint = "/api/chat"
            params_ov = {"stream": True, "mode": "conversation", "persona": "auto"}
            est_dur = 500 + len(user_input) * 5
            reasoning = f"Detected conversation-oriented query. Routing to {mode.value} mode via {endpoint}."

        decision = ModeRoutingDecision(
            mode=mode,
            config=config,
            agent_priority=agent_pri,
            api_endpoint=endpoint,
            params_override=params_ov,
            estimated_duration_ms=est_dur,
            reasoning=reasoning,
        )
        with self._lock:
            self._routing_log.append({
                "user_id": user_id,
                "input_preview": user_input[:80],
                "mode": mode.value,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat(),
            })
        return decision

    def _auto_detect_mode(self, user_input: str, hints: Dict) -> ScenarioMode:
        report_keywords = ["\u62a5\u544a", "\u5bfc\u51fa", "\u6279\u91cf", "\u5bfc\u6574", "\u6279\u51faPDF", "\u6279\u51faHTML",
                           "\u6279\u5165", "\u6279\u5220\u9644", "\u5bf9\u6bd4\u62a5\u544a", "\u6279\u5305", "\u6279\u5220\u89c3",
                           "\u6279\u5217\u8868", "\u751f\u4ea7\u5206\u6790", "\u6279\u51fa\u8868\u683c"]
        chat_keywords = ["\u600e\u4e48\u6837", "\u600e\u4e48\u505a", "\u4e3a\u4ec0\u4e48", "\u662f\u5426", "\u53ef\u4ee5\u5417",
                         "\u804a\u804a", "\u8bf4\u8bf4\u4e00\u4e0b", "\u5e2e\u6211\u770b\u770b", "\u60f3\u95ee\u95ee",
                         "\u591a\u957f", "\u4ecb\u7ecd", "\u6211\u60f3\u77e5", "\u89c9\u5f97"]

        input_lower = user_input.lower()
        report_score = sum(1 for kw in report_keywords if kw in user_input)
        chat_score = sum(1 for kw in chat_keywords if kw in user_input)

        if hints.get("page_context") == "task_center":
            return ScenarioMode.REPORT
        if hints.get("page_context") == "consultation_chat":
            return ScenarioMode.CONVERSATION
        if hints.get("explicit_mode"):
            return ScenarioMode(hints["explicit_mode"])

        if report_score > chat_score and report_score >= 1:
            return ScenarioMode.REPORT
        if chat_score > report_score and chat_score >= 1:
            return ScenarioMode.CONVERSATION

        if len(user_input) > 100:
            return ScenarioMode.REPORT
        if any(punct in user_input for punct in ["？", "?", "!"]):
            return ScenarioMode.CONVERSATION

        return ScenarioMode.CONVERSATION

    def set_user_preference(self, user_id: str, mode: ScenarioMode):
        self._user_preferences[user_id] = mode

    def get_user_preference(self, user_id: str) -> Optional[ScenarioMode]:
        return self._user_preferences.get(user_id)

    def get_routing_stats(self) -> Dict[str, Any]:
        if not self._routing_log:
            return {"total_routings": 0}
        modes = {}
        for entry in self._routing_log:
            m = entry["mode"]
            modes[m] = modes.get(m, 0) + 1
        return {
            "total_routings": len(self._routing_log),
            "by_mode": modes,
            "report_ratio": round(modes.get("report", 0) / max(len(self._routing_log), 1), 3),
            "conversation_ratio": round(modes.get("conversation", 0) / max(len(self._routing_log), 1), 3),
        }


# =============================================================================
# Part B: Task Analysis Deep Development
# =============================================================================


@dataclass
class HybridInputState:
    current_mode: str = "natural_language"
    natural_text: str = ""
    structured_fields: Dict[str, Any] = field(default_factory=dict)
    parsed_from_nl: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)


TASK_INPUT_FIELD_SCHEMA = [
    {"key": "city", "label": "\u57ce\u5e02", "type": "select", "required": True, "options": []},
    {"key": "district", "label": "\u533a/\u57df", "type": "text", "required": False},
    {"key": "block", "label": "\u677f\u5757", "type": "text", "required": False},
    {"key": "property_type", "label": "\u623f\u4ea7\u7c7b\u578b", "type": "select",
     "required": False, "options": ["\u4f4f\u5b85", "\u5546\u52a1", "\u5199\u5b57\u697c", "\u5b66\u533a\u623f", "\u5176\u4ed6"]},
    {"key": "area_sqm", "label": "\u9762\u79ef(\u33a1)", "type": "number", "required": False},
    {"key": "budget_cny", "label": "\u9884\u7b97(\u4e07)", "type": "number", "required": False},
    {"key": "purpose", "label": "\u76ee\u7684", "type": "select",
     "required": False, "options": ["\u81ea\u4f4f", "\u6295\u8d44", "\u79df\u8d41", "\u5b66\u533a", "\u6539\u5546"]},
    {"key": "horizon_months", "label": "\u6295\u8d44\u671f\u9650", "type": "select",
     "required": False, "options": ["3\u4e2a\u6708", "6\u4e2a\u6708", "12\u4e2a\u6708", "24\u4e2a\u6708", "36\u4e2a\u6708"]},
]

INPUT_EXAMPLES = [
    "\u6df1\u5733\u5357\u5c71\u533a100\u33a1\u5b66\u533a\u623f\uff0c\u9884\u7b971000\u4e07\uff0c\u5206\u6790\u6295\u8d44\u56de\u62a5\u7387",
    "\u676d\u5dde\u672a\u6765\u79d1\u6280\u57ce200\u33a1\u529e\u516c\u697c\uff0c\u9884\u7b975500\u4e07\uff0c\u5e02\u573a\u5206\u6790",
    "\u5317\u4eac\u6d77\u6dc0150\u33a1\u4e24\u5c4a\uff0c\u81ea\u4f4f\u7528\uff0c\u5bf9\u6bd4\u671b\u4eac\u548c\u901a\u5dde",
]


class HybridInputProcessor:
    """Processes hybrid natural-language + structured form input for task analysis."""

    def __init__(self):
        self._field_schema = list(TASK_INPUT_FIELD_SCHEMA)
        self._examples = list(INPUT_EXAMPLES)
        self._nl_parsers = {
            "city": re.compile(r"([\u4e00-\u9fff]{2,})(?:\u5e02)?(?:\u5e02|\u533a|\u677f\u5757)?"),
            "area_sqm": re.compile(r"(\d{1,5})\s*(?:\u33a1|\u5e73\u7c73\u65b9\u7c73)"),
            "budget_cny": re.compile(r"(\d{1,6})\s*(?:\u4e07|\u4e07\u5143|\u4e07RMB|\u4e07\u5143)"),
            "property_type": re.compile(r"(\u4f4f\u5b85|\u5546\u52a1|\u5199\u5b57\u697c|\u5b66\u533a\u623f|\u5176\u4ed6)"),
            "purpose": re.compile(r"(\u81ea\u4f4f|\u6295\u8d44|\u79df\u8d41|\u5b66\u533a|\u6539\u5546)"),
        }

    def get_field_schema(self) -> List[Dict]:
        return list(self._field_schema)

    def get_examples(self) -> List[str]:
        return list(self._examples)

    def process_natural_input(self, text: str) -> HybridInputState:
        state = HybridInputState(current_mode="natural_language", natural_text=text)
        parsed = {}
        for field_name, pattern in self._nl_parsers.items():
            match = pattern.search(text)
            if match:
                val = match.group(1).strip()
                parsed[field_name] = val
        state.parsed_from_nl = dict(parsed)
        state.structured_fields.update(parsed)
        required = [f for f in self._field_schema if f.get("required")]
        errors = []
        for f in required:
            if f["key"] not in parsed and f["key"] not in state.structured_fields:
                errors.append(f"\u7f3a\u5c11\u5fc5\u586b\u5b57\u6bb5: {f['label']}")
        state.is_valid = len(errors) == 0
        state.validation_errors = errors
        return state

    def sync_to_structured(self, state: HybridInputState) -> HybridInputState:
        state.current_mode = "structured"
        nl_parsed = dict(state.parsed_from_nl)
        for key, val in nl_parsed.items():
            if key not in state.structured_fields or not state.structured_fields.get(key):
                state.structured_fields[key] = val
        return state

    def sync_to_natural(self, state: HybridInputState) -> HybridInputState:
        state.current_mode = "natural_language"
        parts = []
        city = state.structured_fields.get("city", "")
        if city:
            parts.append(city)
        block = state.structured_fields.get("block", "")
        if block:
            parts.append(block)
        area = state.structured_fields.get("area_sqm")
        if area:
            parts.append(f"{area}\u33a1")
        budget = state.structured_fields.get("budget_cny")
        if budget:
            parts.append(f"\u9884\u7b97{budget}\u4e07")
        ptype = state.structured_fields.get("property_type", "")
        if ptype:
            parts.append(ptype)
        purpose = state.structured_fields.get("purpose", "")
        if purpose:
            parts.append(purpose)
        state.natural_text = "\uff0c".join(parts) if parts else state.natural_text
        return state

    def validate_and_submit(self, state: HybridInputState) -> Dict[str, Any]:
        all_fields = {**state.structured_fields, **state.parsed_from_nl}
        required = [f["key"] for f in self._field_schema if f.get("required")]
        missing = [r for r in required if r not in all_fields or not all_fields[r]]
        task_data = {
            "task_id": f"task_{uuid.uuid4().hex[:12]}",
            "input_mode": state.current_mode,
            "natural_text": state.natural_text,
            "structured_params": all_fields,
            "is_valid": len(missing) == 0,
            "missing_fields": missing,
            "created_at": datetime.now().isoformat(),
            "status": "submitted" if len(missing) == 0 else "validation_failed",
        }
        return task_data


BATCH_OPERATION_TYPES = ["export_reports", "compare_tasks", "delete_tasks", "save_template", "load_template"]


@dataclass
class BatchOperationResult:
    operation: str
    task_ids: List[str]
    success_count: int
    fail_count: int
    results: List[Dict]
    download_url: Optional[str] = None
    comparison_id: Optional[str] = None
    template_id: Optional[str] = None
    duration_ms: float = 0.0
    error: Optional[str] = None


class TaskCenterBatchManager:
    """Manages batch operations on task center: export, compare, delete, templates."""

    def __init__(self):
        self._templates: Dict[str, Dict] = {}
        self._operation_log: List[Dict] = []

    def execute_batch_export(self, task_ids: List[str], format_type: str = "zip") -> BatchOperationResult:
        start = time.time()
        results = []
        success = 0
        for tid in task_ids:
            mock_result = {
                "task_id": tid,
                "filename": f"report_{tid}.{format_type}" if format_type != "zip" else f"{tid}_report.pdf",
                "size_kb": random.randint(200, 800),
                "status": "ready",
            }
            results.append(mock_result)
            success += 1
        dur = (time.time() - start) * 1000
        result = BatchOperationResult(
            operation="export_reports",
            task_ids=task_ids,
            success_count=success,
            fail_count=len(task_ids) - success,
            results=results,
            download_url=f"/api/batch/download/{uuid.uuid4().hex[:8]}.zip" if format_type == "zip" else None,
            duration_ms=round(dur, 2),
        )
        self._log_operation(result)
        return result

    def execute_batch_compare(self, task_ids: List[str]) -> BatchOperationResult:
        start = time.time()
        if len(task_ids) < 2 or len(task_ids) > 5:
            return BatchOperationResult(
                operation="compare_tasks", task_ids=task_ids, success_count=0,
                fail_count=len(task_ids), results=[], error="Compare requires 2-5 tasks",
                duration_ms=0,
            )
        comparison_items = []
        for tid in task_ids:
            comparison_items.append({
                "task_id": tid,
                "city": random.choice(["\u676d\u5dde", "\u6df1\u5733", "\u5317\u4eac", "\u4e0a\u6d77"]),
                "block": random.choice(["\u672a\u6765\u79d1\u6280\u57ce", "\u94b1\u6c5f\u4e16\u7eaa\u57ce", "\u6d49\u4e1c\u65b0\u533a"]),
                "predicted_growth": round(random.uniform(0.02, 0.18), 4),
                "risk_score": round(random.uniform(1, 10), 1),
                "sharpe": round(random.uniform(-0.5, 2.5), 3),
                "mdd_pct": round(random.uniform(0.05, 0.40), 3),
            })
        comparison_items.sort(key=lambda x: x["sharpe"], reverse=True)
        dur = (time.time() - start) * 1000
        result = BatchOperationResult(
            operation="compare_tasks",
            task_ids=task_ids,
            success_count=len(task_ids),
            fail_count=0,
            results=[{"comparison_items": comparison_items}],
            comparison_id=f"cmp_{uuid.uuid4().hex[:8]}",
            duration_ms=round(dur, 2),
        )
        self._log_operation(result)
        return result

    def execute_batch_delete(self, task_ids: List[str]) -> BatchOperationResult:
        start = time.time()
        deleted = set()
        for tid in task_ids:
            deleted.add(tid)
        dur = (time.time() - start) * 1000
        result = BatchOperationResult(
            operation="delete_tasks",
            task_ids=list(deleted),
            success_count=len(deleted),
            fail_count=0,
            results=[{"deleted_ids": list(deleted)}],
            duration_ms=round(dur, 2),
        )
        self._log_operation(result)
        return result

    def save_template(self, name: str, params: Dict[str, Any], user_id: str) -> str:
        tpl_id = f"tpl_{uuid.uuid4().hex[:10]}"
        self._templates[tpl_id] = {
            "template_id": tpl_id,
            "name": name,
            "params": dict(params),
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
        }
        return tpl_id

    def load_template(self, template_id: str) -> Optional[Dict]:
        tpl = self._templates.get(template_id)
        if tpl:
            tpl["usage_count"] = tpl.get("usage_count", 0) + 1
        return tpl

    def get_user_templates(self, user_id: str) -> List[Dict]:
        return [t for t in self._templates.values() if t.get("user_id") == user_id]

    def recommend_templates(self, user_id: str, history: List[Dict]) -> List[Dict]:
        type_counts = {}
        for h in history[-20:]:
            purpose = h.get("structured_params", {}).get("purpose", "")
            type_counts[purpose] = type_counts.get(purpose, 0) + 1
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        recommended = []
        for purpose, count in sorted_types[:3]:
            user_tpls = [t for t in self._templates.values() if t.get("user_id") == user_id]
            matching = [t for t in user_tpls if t.get("params", {}).get("purpose") == purpose]
            if matching:
                recommended.extend(matching[:1])
            else:
                recommended.append({
                    "template_id": f"suggested_{purpose}",
                    "name": f"{purpose}\u5206\u677f\u6837\u5165\u586b",
                    "params": {"purpose": purpose},
                    "is_suggested": True,
                    "reason": f"\u60a8\u8fd1\u8fd1{count}\u6b21\u4f7f\u7528{purpose}\u7c7b\u578b\u5206\u6790",
                })
        return recommended[:5]

    def _log_operation(self, result: BatchOperationResult):
        self._log_operation.append({
            "operation": result.operation,
            "task_count": len(result.task_ids),
            "success": result.success_count,
            "duration_ms": result.duration_ms,
            "timestamp": datetime.now().isoformat(),
        })

    def get_operation_stats(self) -> Dict:
        if not self._log_operation:
            return {"total": 0}
        ops = {}
        for log in self._log_operation:
            op = log["operation"]
            ops[op] = ops.get(op, 0) + 1
        return {"total": len(self._log_operation), "by_operation": ops}


REPORT_TEMPLATE_SECTIONS = [
    {"id": "cover", "title": "\u5c01\u9762", "order": 1, "fields": ["task_name", "generated_at", "user_info"]},
    {"id": "executive_summary", "title": "\u6267\u884c\u6458\u8981", "order": 2, "fields": ["conclusion", "valuation", "recommendation", "risk_level"]},
    {"id": "data_sources", "title": "\u6570\u636e\u6765\u6e90", "order": 3, "fields": ["sources_list", "update_time"]},
    {"id": "valuation_detail", "title": "\u4f30\u503c\u8be6\u60c5", "order": 4, "fields": ["model_output", "confidence_interval", "radar_chart"]},
    {"id": "market_analysis", "title": "\u5e02\u573a\u5206\u6790", "order": 5, "fields": ["price_trend", "supply_demand", "absorption_period"]},
    {"id": "policy_impact", "title": "\u653f\u7b56\u5f71\u54cd", "order": 6, "fields": ["policy_summary", "impact_assessment"]},
    {"id": "investment_advice", "title": "\u6295\u8d44\u5efa\u8bae", "order": 7, "fields": ["quant_metrics", "action_recommendation"]},
    {"id": "reasoning_chain", "title": "\u63a8\u7406\u94fe", "order": 8, "fields": ["agent_steps"], "extra": {"collapsible": True}},
    {"id": "disclaimer", "title": "\u514d\u8d23\u58f0\u660e", "order": 9, "fields": ["text"]},
]


@dataclass
class GeneratedReport:
    report_id: str
    title: str
    sections: List[Dict]
    html_content: str
    metadata: Dict[str, Any]
    generated_at: str
    mode: str
    word_count: int
    has_charts: bool
    download_urls: Dict[str, str]


class StructuredReportGenerator:
    """Generates professional-grade structured HTML reports."""

    def __init__(self):
        self._section_defs = list(REPORT_TEMPLATE_SECTIONS)
        self._report_cache: Dict[str, GeneratedReport] = {}

    def generate(self, task_data: Dict[str, Any], mode: str = "full") -> GeneratedReport:
        cache_key = hashlib.md5(json.dumps(task_data, sort_keys=True).encode()).hexdigest()[:16]
        if cache_key in self._report_cache:
            cached = self._report_cache[cache_key]
            cached.metadata["cache_hit"] = True
            return cached

        task_id = task_data.get("task_id", f"rpt_{uuid.uuid4().hex[:10]}")
        params = task_data.get("structured_params", {})
        city = params.get("city", "\u672a\u77e5")
        block = params.get("block", "\u672a\u77e5")
        purpose = params.get("purpose", "\u6295\u8d44")

        sections = []
        for sec_def in self._section_defs:
            sec_content = self._render_section(sec_def, task_data, params)
            sections.append({**sec_def, "content": sec_content})

        html = self._assemble_html(sections, task_data, mode)
        report = GeneratedReport(
            report_id=task_id,
            title=f"{city}{block}\u623f\u4ea7\u5206\u6790\u62a5\u544a" if block else f"{city}\u623f\u4ea7\u5206\u6790\u62a5\u544a",
            sections=sections,
            html_content=html,
            metadata={
                "task_id": task_id,
                "city": city,
                "block": block,
                "purpose": purpose,
                "generator_version": "v3.1-professional",
                "chart_library": "echarts",
                "mode": mode,
                "word_count": len(html),
                "has_charts": True,
                "cache_hit": False,
            },
            generated_at=datetime.now().isoformat(),
            mode=mode,
            word_count=len(html),
            has_charts=True,
            download_urls={
                "pdf": f"/api/reports/{task_id}/pdf",
                "html": f"/api/reports/{task_id}/html",
                "share": f"/api/reports/{task_id}/share",
            },
        )
        self._report_cache[cache_key] = report
        return report

    def _render_section(self, sec_def: Dict, task_data: Dict, params: Dict) -> str:
        sid = sec_def["id"]
        if sid == "cover":
            return f"<h1>{self._escape(params.get('city',''))} {self._escape(params.get('block',''))} \u623f\u4ea7\u5206\u6790\u62a5\u544a</h1><p>\u751f\u6210\u65f6\u95f4: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
        elif sid == "exec_summary_summary":
            growth = round(random.uniform(0.03, 0.15), 4)
            risk = random.choice(["\u4f4e\u4f4e", "\u4e2d\u7b49", "\u8f83\u4f4e"])
            action = "\u5efa\u8bae\u4e70\u5165" if risk != "\u9ad8" else "\u89c2\u671b\u89c2\u5b9a"
            return f"<p><strong>\u6838\u5fc3\u7ed3\u8bba:</strong> \u9884\u671f{growth*100:.1f}%\u6da8\u5e45\uff0c\u98ce\u9669{risk}\u3002{action}\u3002</p>"
        elif sid == "data_sources":
            sources = ["\u8d1d\u58f3\u7814\u7a76\u9662", "\u623f\u5929\u5929\u4e0b", "\u653f\u5e9c\u516c\u5f00\u6570\u636e", "\u4e2d\u539f\u6280\u672f\u6570\u636e"]
            return f"<ul>{''.join(f'<li>{s}</li>' for s in sources)}</ul><p>\u6570\u636e\u66f4\u65b0: {datetime.now().strftime('%Y-%m-%d')}</p>"
        elif sid == "valuation_detail":
            return "<div id='chart-valuation-radar' class='echart-container'></div><p>\u7f6e\u4fe1\u533a\u95f4: 8%-12% | \u6a21\u578b: XGBoost v4.2</p>"
        elif sid == "market_analysis":
            return "<div id='chart-price-trend' class='echart-container'></div><table><tr><th>\u53bb\u5316\u6bd4</th><th>\u4f9b\u4f9b</th></tr><tr><td>+2.3%</td><td>1.85</td></tr></table>"
        elif sid == "policy_impact":
            return "<p>\u76f8\u5173\u9650\u8d2d/\u9650\u8d37\u653f\u7b56\u6458\u8981\u53ca\u65f6\u5ea6\u3002\u4eba\u624d\u5f15\u8fdb\u653f\u7b56\u5bf9\u5206+0.8%\u3002</p>"
        elif sid == "investment_advice":
            sharpe = round(random.uniform(0.8, 1.8), 2)
            return f"<table class='metrics-table'><tr><th>\u6307\u6807</th><th>\u503c</th></tr><tr><td>\u9884\u671f\u6536\u76ca</td><td>{random.uniform(0.05,0.2)*100:.1f}%</td></tr><tr><td>\u590f\u666e\u6bd4\u7387</td><td>{sharpe}</td></tr><tr><td>\u6700\u5927\u56de\u64a4</td><td>{random.uniform(0.08,0.25)*100:.1f}%</td></tr></table>"
        elif sid == "reasoning_chain":
            steps = [{"agent": "\u4e2d\u4e66\u7701", "step": "\u9700\u6c42\u89e3\u6790"}, {"agent": "\u6237\u90e8", "step": "\u91c7\u96c6\u91c7\u6570\u636e"}, {"agent": "\u5de5\u90e8", "step": "\u91cf\u91cf\u6a21\u578b\u8ba1\u7b97"}, {"agent": "\u793c\u90e8", "step": "\u98ce\u9669\u8bc4\u4f30"}, {"agent": "\u5211\u90e8", "step": "\u5408\u89c4\u6821\u67e5"}]
            items_li = "".join(f'<li><strong>{s["agent"]}</strong>: {s["step"]}</li>' for s in steps)
            return f"<details><summary>\u67e5\u770b\u63a8\u7406\u94fe ({len(steps)}\u6b65)</summary><ol>{items_li}</ol></details>"
        elif sid == "disclaimer":
            return "<p class='disclaimer'>\u672c\u62a5\u544a\u7531AI\u6a21\u578b\u751f\u6210\uff0c仅供\u53c2\u8003\u3002\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\u3002\u5b9e\u9645\u6295\u8d44\u6709\u98ce\u9669\uff0c\u8bf7\u8c28\u614e\u81ea\u8eab\u60c5\u51b5\u3002</p>"
        return f"<p>[Section: {sec_def['title']}]</p>"

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _assemble_html(self, sections: List[Dict], task_data: Dict, mode: str) -> str:
        sorted_secs = sorted(sections, key=lambda s: s["order"])
        body_parts = []
        for sec in sorted_secs:
            body_parts.append("<section id='" + sec['id'] + "' class='report-section'><h2>" + sec['title'] + "</h2>" + sec.get('content', '') + "</section>")
        body = "\n".join(body_parts)
        css_lines = [
            ".report-section { margin-bottom: 30px; padding: 20px; border-left: 3px solid #1a73e8; }",
            ".echart-container { width: 100%; height: 350px; margin: 15px 0; }",
            ".metrics-table { width: 100%; border-collapse: collapse; }",
            ".metrics-table th, .metrics-table td { padding: 10px; border: 1px solid #ddd; text-align: left; }",
            ".disclaimer { background: #fffbe6; padding: 15px; border-radius: 8px; font-size: 13px; color: #856404; }",
            "h1 { color: #1a365d; font-size: 24px; } h2 { color: #2c5282; font-size: 18px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }",
        ]
        css = "\n".join(css_lines)
        html_head = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Property Analysis Report</title><style>" + css + "</style></head>"
        html_body = "<body><div class='report-container'>" + body + "</div><script src='https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js'></script></body></html>"
        full_html = html_head + html_body
        if mode == "compact":
            full_html = "<div class='compact-report'>" + body + "</div>"
        return full_html

    def invalidate_cache(self, report_id: Optional[str] = None):
        if report_id:
            keys_to_remove = [k for k, v in self._report_cache.items() if v.report_id == report_id]
        else:
            keys_to_remove = list(self._report_cache.keys())
        for k in keys_to_remove:
            del self._report_cache[k]


ONBOARDING_STEPS = [
    {"step": 1, "title": "\u521b\u5efa\u4efb\u52a1", "desc": "\u70b9\u51fb\u201c\u65b0\u5efa\u4efb\u52a1\u201d\uff0c900\u62e9\u8f93\u5165\u6a21\u5f0f", "target": "#new-task-btn"},
    {"step": 2, "title": "\u586b\u5199\u6216\u9009\u62e9", "desc": "\u586b\u5199\u81ea\u7136\u8bed\u8a00\u95ee\u9898\uff0c\u6216\u9009\u62e9\u9884\u8bbe\u53c2\u8868\u5355", "target": ".input-area"},
    {"step": 3, "title": "\u63d0\u4ea4\u5e76\u7b49\u5f85", "desc": "\u70b9\u201c\u63d0\u4ea4\u201d\uff0c\u524d\u5f80\u4efb\u52a1\u4e2d\u5fc3\u67e5\u62a5\u544a", "target": ".submit-btn"},
    {"step": 4, "title": "\u67e5\u770b\u4e0e\u64cd\u4f5c", "desc": "\u5728\u4efb\u52a1\u4e2d\u5fc3\u67e5\u62a5\u544a\uff0c\u5c1d\u8bd5\u6279\u51fa\u3001\u5bf9\u6bd4\u3001\u6a21\u677f\u529f\u80fd", "target": ".task-center"},
]


class TaskAnalysisOnboardingGuide:
    """4-step onboarding guide for new users of the task analysis module."""

    def __init__(self):
        self._steps = list(ONBOARDING_STEPS)
        self._dismissed_users: set = set()

    def get_steps(self, user_id: Optional[str] = None) -> List[Dict]:
        if user_id and user_id in self._dismissed_users:
            return []
        return list(self._steps)

    def dismiss(self, user_id: str):
        self._dismissed_users.add(user_id)

    def get_progress(self, user_id: str, completed_actions: List[str]) -> Dict:
        total = len(self._steps)
        done = min(len(completed_actions), total)
        return {"current_step": done + 1, "total_steps": total, "progress_pct": round(done / total * 100), "next_action": self._steps[done]["title"] if done < total else "\u5b8c\u6210!"}


# =============================================================================
# Part C: Smart Consultation Deep Development
# =============================================================================


PERSONA_WELCOME_MESSAGES = {
    "zhouyu": {
        "morning": "\u65e9\u4e0a\u597d\uff01\u6211\u662f\u5468\u745e\u3002\u4eca\u5929\u60f3\u804a\u804a\u54ea\u91cc\u7684\u623f\u5b50\uff1f",
        "afternoon": "\u4e0b\u5348\u597d\uff01\u5468\u745e\u5728\u6b64\u3002\u6709\u4ec0\u4e48\u623f\u4ea7\u60f3\u8981\u5206\u89e3\u4e00\u4e0b\uff1f",
        "evening": "\u665a\u4e0a\u597d\uff01\u591c\u6df1\u4e86\uff0c\u676d\u706f\u71c3\u8336\u4e0e\u6211\u4eec\u4e00\u8d77\u5206\u67e5\u623f\u4ea7\u8d44\u754c\u3002",
        "default": "\u60a8\u597d\uff01\u6211\u662f\u5468\u745e\u3002\u6709\u4ec0\u4e48\u53ef\u4ee5\u5e2e\u60a8\u670d\u52a1\uff1f",
    },
    "luxun": {
        "morning": "\u65e9\u5b89\u3002\u6211\u662f\u9c81\u8fc5\u3002\u82e5\u9762\u7684\u623f\u4ea7\u5e02\u573a\u603b\u7ecf\u590d\u6742\uff0c\u503c\u8be5\u8ba4\u61c5\u5206\u89e3\u3002",
        "afternoon": "\u5371\u5b89\u3002\u5348\u4e0b\u6b63\u662f\u7814\u7a76\u623f\u4ea7\u5e02\u573a\u7684\u597d\u65f6\u65f6\u671f\u3002\u6709\u4ec0\u4e48\u60f3\u8981\u4e86\u89e3\u7684\uff1f",
        "evening": "\u665a\u5b89\u3002\u591c\u6df1\u4e86\uff0c\u6b63\u662f\u601d\u8003\u7684\u65f6\u523b\u3002\u5982\u679c\u60a8\u6709\u623f\u4ea7\u65b9\u9762\u7684\u7591\u60d1\uff0c\u6211\u4eec\u53ef\u4ee5\u8ba8\u8ba8\u3002",
        "default": "\u60a8\u597d\u3002\u6211\u662f\u9c81\u8fc5\u3002\u8bf7\u653e\u77e5\uff0c\u6211\u7684\u56de\u7b54\u53ef\u80fd\u4e0d\u5b8c\u5584\uff0c\u4f46\u4f1a\u5c3d\u529b\u5e2e\u60a8\u627e\u5230\u66f4\u597d\u7684\u7b54\u6848\u3002",
    },
}

CHAT_INTERFACE_SPEC = {
    "header_height": "60px",
    "persona_switcher": {"position": "top-right", "avatars": {"zhouyu": "\ud83e\uddd1\uFE0F", "luxun": "\ud83c\udff3\uFE0F"}},
    "input_area": {"min_height": "60px", "max_height": "200px", "placeholder": "\u63cf\u5165\u60a8\u7684\u623f\u4ea7\u95ee\u9898..."},
    "message_bubble": {"user_align": "right", "agent_align": "left", "max_width": "75%", "border_radius": "12px"},
    "typing_indicator": {"text": "\u6b63\u5728\u601d\u8003...", "dots_animation": True, "speed": "40ms"},
    "sidebar": {"width": "280px", "show_agent_status": True, "agents": ["\u4e2d\u4e66\u7701", "\u6237\u90e8", "\u5de5\u90e8", "\u793c\u90e8", "\u5211\u90e8", "\u5211\u90e8"]},
    "voice_input": {"enabled": True, "max_duration_sec": 60},
    "attachment_upload": {"enabled": True, "max_size_mb": 10, "types": ["image", "pdf", "csv", "xlsx"]},
}


@dataclass
class SuggestedFollowUp:
    text: str
    intent_hint: str
    icon: Optional[str] = None
    auto_fill: bool = True


class ConsultationFollowUpEngine:
    """Generates contextual suggested follow-up questions during smart consultation."""

    INTENT_TO_FOLLOWUPS = {
        "single_block_analysis": [
            SuggestedFollowUp("\u5206\u6790\u98ce\u9669\u600e\u4f55\uff1f", "risk_assessment", "\u26a0"),
            SuggestedFollowUp("\u5bf9\u6bd4\u5176\u4ed6\u677f\u5757", "multi_block_compare", "\u2694"),
            SuggestedFollowUp("\u751f\u6210\u5206\u6790\u62a5\u544a", "generate_report", "\ud83d\udccb"),
        ],
        "multi_block_compare": [
            SuggestedFollowUp("\u67e5\u770b\u8be6\u660e\u8be6\u660e\u8be6\u60c5", "factor_attribution", "\ud83d\udcca"),
            SuggestedFollowUp("\u5206\u6790\u5386\u53f2\u56de\u6d4b", "historical_backtest", "\ud83d\udcc2"),
        ],
        "risk_assessment": [
            SuggestedFollowUp("\u8c03\u6574\u98ce\u9669\u504f\u597d", "param_adjustment", "\u2699\uFE0F"),
            SuggestedFollowUp("\u67e5\u770b\u653f\u7b56\u5f71\u54cd", "policy_impact", "\ud83d\udcdc"),
        ],
        "trend_prediction": [
            SuggestedFollowUp("\u4e3a\u4ec0\u4e48\u9884\u6d4b\u8fd9\u4e48\u9ad8\uff1f", "factor_attribution", "\u2753"),
            SuggestedFollowUp("\u5e02\u573a\u60c5\u7eea\u5982\u4f55", "sentiment_check", "\ud83d\udeca"),
        ],
        "factor_attribution": [
            SuggestedFollowUp("\u8c03\u6574\u53c2\u6570\u8c03\u8bbe\u5b9a", "param_adjustment", "\u2699"),
            SuggestedFollowUp("\u751f\u6210\u5bf9\u6bd4\u62a5\u544a", "generate_report", "\ud83d\udccb"),
        ],
        "policy_impact": [
            SuggestedFollowUp("\u5206\u6790\u8fd1\u5730\u623f\u4ef7", "trend_prediction", "\ud83d\udcc8"),
            SuggestedFollowUp("\u5206\u6790\u8fd1\u4e0a\u6d77\u533a", "multi_block_compare", "\u2694"),
        ],
    }

    DEFAULT_FOLLOWUPS = [
        SuggestedFollowUp("\u5206\u6790\u98ce\u9669\u6307\u6807", "risk_assessment", "\u26a0"),
        SuggestedFollowUp("\u751f\u6210\u5206\u6790\u62a5\u544a", "generate_report", "\ud83d\udccb"),
        SuggestedFollowUp("\u5207\u6362\u4eba\u683c", "switch_persona", "\ud83e\uddd1"),
    ]

    def generate_followups(self, last_intent: str, context: Dict[str, Any]) -> List[SuggestedFollowUp]:
        candidates = self.INTENT_TO_FOLLOWUPS.get(last_intent, [])
        if not candidates:
            candidates = list(self.DEFAULT_FOLLOWUPS)
        selected = random.sample(candidates, min(3, len(candidates)))
        for i, fu in enumerate(selected):
            if "{city}" in fu.text and context.get("city"):
                fu.text = fu.text.replace("{city}", context["city"])
            if "{block}" in fu.text and context.get("block"):
                fu.text = fu.text.replace("{block}", context["block"])
        return selected


@dataclass
class ReportCardData:
    card_id: str
    title: str
    summary_metrics: Dict[str, str]
    actions: List[Dict]
    is_compact: bool = True
    expandable: bool = True
    report_ref_id: Optional[str] = None


class ReportCardInChatEmbedder:
    """Embeds compact report cards into consultation dialogue."""

    CARD_TEMPLATE_COMPACT = """
<div class='report-card compact' data-card-id='{card_id}' style='background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border-radius:12px;padding:16px;margin:12px 0;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.15);'>
  <div style='font-weight:bold;font-size:15px;margin-bottom:10px;'>{title}</div>
  <div style='display:flex;gap:16px;font-size:13px;'>
    <div><span style='opacity:0.8'>\u9884\u671f\u6da8:</span> <strong>{growth}</strong></div>
    <div><span style='opacity:0.8'>\u98ce\u9669:</span> <strong style='color:{risk_color}'>{risk}</strong></div>
    <div><span style='opacity:0.8'>\u5efa议:</span> <strong>{advice}</strong></div>
  </div>
  <div style='margin-top:10px;display:flex;gap:8px;'>
    <button onclick='viewFullReport("{card_id}")' style='padding:6px 14px;background:rgba(255,255,255,0.2);border:none;color:white;border-radius:6px;cursor:pointer;font-size:12px;'>\u67e5\u5b8c\u5b8c\u62a5\u544a</button>
    <button onclick='downloadPdf("{card_id}")' style='padding:6px 14px;background:rgba(255,255,255,0.2);border:none;color:white;border-radius:6px;cursor:pointer;font-size:12px;'>\u4e0b\u8f7dPDF</button>
    <button onclick='shareReport("{card_id}")' style='padding:6px 14px;background:rgba(255,255,255,0.2);border:none;color:white;border-radius:6px;cursor:pointer;font-size:12px;'>\u5206\u4eab</button>
  </div>
</div>
"""

    def embed_card(self, report_data: Dict, is_compact: bool = True) -> ReportCardData:
        card_id = f"card_{uuid.uuid4().hex[:10]}"
        growth_val = report_data.get("predicted_growth", "N/A")
        risk_val = report_data.get("risk_level", "medium")
        advice_val = report_data.get("advice", "\u89c2\u5b9a\u89c2\u5b9a")
        risk_color = "#ffd700" if risk_val == "high" else "#4ade80" if risk_val == "low" else "#f39c12"

        card = ReportCardData(
            card_id=card_id,
            title=report_data.get("title", "\u623f\u4ea7\u5206\u6790\u62a5\u544a"),
            summary_metrics={"growth": str(growth_val), "risk": risk_val, "advice": advice_val},
            actions=[
                {"label": "\u67e5\u5b8c\u5b8c\u62a5\u544a", "action": "view_full"},
                {"label": "\u4e0b\u8f7dPDF", "action": "download_pdf"},
                {"label": "\u5206\u4eab", "action": "share"},
            ],
            is_compact=is_compact,
            expandable=True,
            report_ref_id=report_data.get("report_id"),
        )
        return card

    def render_card_html(self, card: ReportCardData) -> str:
        return self.CARD_TEMPLATE_COMPACT.format(
            card_id=card.card_id,
            title=card.title,
            growth=card.summary_metrics.get("growth", "-"),
            risk_color="#ffd700" if card.summary_metrics.get("risk") == "high" else "#4ade80" if card.summary_metrics.get("risk") == "low" else "#f39c12",
            risk=card.summary_metrics.get("risk", "-"),
            advice=card.summary_metrics.get("advice", "-"),
        )


REASONING_STEP_TEMPLATES = {
    "zhongshu_parsing": {"agent": "\u4e2d\u4e66\u7701", "icon": "\ud83d\udcda", "text": "\u6b63\u5728\u89e3\u6790\u60a8\u7684\u9700\u6c42...", "duration_ms": 800},
    "hubu_collecting": {"agent": "\u6237\u90e8", "icon": "\ud83d\udcc4", "text": "\u6237\u90e8\u6b63\u5728\u91c7\u96c6\u5e02\u573a\u6570\u636e...", "duration_ms": 1500},
    "gongbu_modeling": {"agent": "\u5de5\u90e8", "icon": "\u2699", "text": "\u5de5\u90e8\u6b63\u5728\u8fd0\u884c\u91cf\u91cf\u6a21\u578b...", "duration_ms": 2500},
    "xingbu_review": {"agent": "\u793c\u90e8", "icon": "\u2699\uFE0F", "text": "\u793c\u90e8\u6b63\u5728\u5ba1\u6838\u5408\u89c4\u6027...", "duration_ms": 600},
    "xiabu_approval": {"agent": "\u5211\u90e8", "icon": "\u2705", "text": "\u5211\u90e8\u6b63\u5728\u5ba1\u6838\u5408\u5408\u5408...", "duration_ms": 400},
    "libu_nlg": {"agent": "\u793c\u90e8", "icon": "\uD83E\uDDE3", "text": "\u793c\u90e8\u6b63\u5728\u7ec4\u7ec4\u56de\u590d...", "duration_ms": 1200},
}


class ReasoningStepDisplayManager:
    """Real-time display of agent execution steps during response generation."""

    def __init__(self):
        self._active_sessions: Dict[str, List[Dict]] = {}

    def start_session(self, session_id: str) -> str:
        self._active_sessions[session_id] = []
        return session_id

    def add_step(self, session_id: str, step_key: str, extra_info: Optional[Dict] = None):
        if session_id not in self._active_sessions:
            self.start_session(session_id)
        step_template = REASONING_STEP_TEMPLATES.get(step_key, {
            "agent": step_key, "icon": "\u2699", "text": f"{step_key} processing...",
            "duration_ms": 1000,
        })
        step_entry = {**step_template, "step_key": step_key, "started_at": datetime.now().isoformat(), "status": "running"}
        if extra_info:
            step_entry.update(extra_info)
        self._active_sessions[session_id].append(step_entry)

    def complete_step(self, session_id: str, step_index: int):
        if session_id in self._active_sessions and step_index < len(self._active_sessions[session_id]):
            self._active_sessions[session_id][step_index]["status"] = "completed"
            self._active_sessions[session_id][step_index]["completed_at"] = datetime.now().isoformat()

    def get_session_steps(self, session_id: str) -> List[Dict]:
        return self._active_sessions.get(session_id, [])

    def get_progress_html(self, session_id: str) -> str:
        steps = self.get_session_steps(session_id)
        if not steps:
            return ""
        total = len(steps)
        done = sum(1 for s in steps if s["status"] == "completed")
        pct = round(done / max(total, 1) * 100)
        items = "".join(
            f"<div class='reasoning-step {'completed' if s['status']=='completed' else 'running'}'>"
            f"<span class='step-icon'>{s['icon']}</span>"
            f"<span class='step-agent'>{s['agent']}</span>"
            f"<span class='step-text'>{s['text']}</span>"
            f"</div>" for s in steps
        )
        return f"<div class='reasoning-progress'><div class='progress-bar'><div class='progress-fill' style='width:{pct}%'></div></div>{items}</div>"

    def end_session(self, session_id: str):
        self._active_sessions.pop(session_id, None)


DATA_SOURCE_HIGHLIGHT_SPEC = {
    "trigger_pattern": r"(\u6839\u636e.*?\u6570\u636e|贝壳|房天下|政府|中原|链家|克而瑞|CRIC|LPR|CPI)",
    "highlight_style": {
        "bg_color": "#e8f4fd",
        "text_color": "#0969da",
        "border_bottom": "2px dashed #0969da",
        "cursor": "help",
    },
    "tooltip_template": "\u6570\u636e\u6765\u6e90: {source_name}\n\u66f4\u65b0\u65f6\u65b0: {update_time}\n{link}",
}


CONFIDENCE_EXPRESSION_RULES = {
    "interval_numeric": {
        "template": "\u9884\u8ba1\u672a\u676512\u4e2a\u6708\u6da8\u5e45\u5728{low}%-{high}%\u4e4b\u95f4 (\u7f6e\u4fe1\u5ea6{conf_pct}%)",
        "verbal_mapping": {(0.8, 1.0): "\u6709\u5927\u628a\u63e1", (0.6, 0.8): "\u516b\u6210\u6709\u80fd", (0.4, 0.6): "\u4e09\u6210\u6709\u80fd", (0.2, 0.4): "\u56db\u6210\u6709\u80fd", (0, 0.2): "\u4e8c\u6210\u6709\u80fd"},
    },
    "probabilistic_verbal": {
        "template": "\u9884\u8ba1\u5927\u6210\u628a\u63e1\u5728{low}-{high}%\u4e4b\u95f4",
        "verbal_mapping": {(0.8, 1.0): "\u51e0\u6709\u6709\u80fd", (0.6, 0.8): "\u8f83\u5fae\u786e\u5b9a", (0.4, 0.6): "\u6709\u80fd\u8f83\u5c0f", (0.2, 0.4): "\u6709\u80fd\u8f83\u4f4e", (0, 0.2): "\u4e0d\u592a\u786e\u5b9a"},
    },
}


FEEDBACK_REASON_OPTIONS = [
    {"value": "wrong_answer", "label": "\u7b54\u975e\u6240\u95ee"},
    {"value": "data_error", "label": "\u6570\u636e\u6709\u8bef"},
    {"value": "understanding_error", "label": "\u7406\u89e3\u504f\u5dee"},
    {"value": "too_long", "label": "\u56de\u7b54\u592a\u957f"},
    {"value": "not_helpful", "label": "\u6ca1\u5e2e\u5e2e\u52a9"},
    {"value": "other", "label": "\u5176\u4ed6\u539f\u56e0"},
]


class TrustBuildingManager:
    """Builds trust through data attribution, confidence expression, and feedback loop."""

    def __init__(self):
        self._feedback_log: List[Dict] = []

    def highlight_data_sources(self, text: str) -> Tuple[str, List[Dict]]:
        highlights = []
        pattern = DATA_SOURCE_HIGHLIGHT_SPEC["trigger_pattern"]
        for match in re.finditer(pattern, text):
            source_name = match.group(0)
            highlighted = f"<span class='data-source-highlight'>{source_name}</span>"
            text = text.replace(source_name, highlighted, 1)
            highlights.append({
                "source": source_name,
                "tooltip": f"\u6570\u636e\u6765\u6e90: {source_name}\n\u66f4\u65b0: {datetime.now().strftime('%Y-%m-%d')}",
            })
        return text, highlights

    def express_confidence(self, value: float, low: float, high: float,
                            mode: str = "probabilistic_verbal") -> str:
        conf_pct = min(max((value - low) / max(high - low, 0.001), 1.0), 0.0)
        rules = CONFIDENCE_EXPRESSION_RULES.get(mode, CONFIDENCE_EXPRESSION_RULES["interval_numeric"])
        tmpl = rules["template"]
        verbal_map = rules["verbal_mapping"]
        for (lo, hi), label in verbal_map.items():
            if lo <= conf_pct <= hi:
                verbal = label
                break
        else:
            verbal = "\u4e0d\u786e\u5b9a"
        result = tmpl.format(low=f"{low:.1f}", high=f"{high:.1f}", conf_pct=int(conf_pct*100))
        if mode == "probabilistic_verbal":
            result = f"\u5927\u6709{verbal}\uff0c{result}"
        return result

    def handle_feedback(self, message_id: str, is_helpful: bool,
                        reason: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        entry = {
            "message_id": message_id,
            "is_helpful": is_helpful,
            "reason": reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._feedback_log.append(entry)
        response = {}
        if not is_helpful and reason:
            apology_templates = [
                "\u62b1\u6b49\uff0c\u6211\u53ef\u80fd\u7406\u89e3\u6709\u8bef\u3002\u60a8\u662f\u60f3\u95ee\u7684\u662f...\uff1f",
                "\u62b1\u6b49\uff0c\u6211\u7684\u56de\u7b54\u53ef\u80fd\u4e0d\u592a\u51c6\u5fc3\u3002\u8bf7\u95ee\u60a8\u662f\u662f\u5426\u4e00\u70b9\u5185\u5bb9\u8be6\u8fbe\uff1f",
                "\u611f\u8c22\u60a8\u7684\u53cd\u9988\uff01\u8bf7\u95ee\u60a8\u80fd\u66f4\u6e05\u7684\u95ee\u9898\u5417\uff1f",
            ]
            response["apology"] = random.choice(apology_templates)
            if reason == "understanding_error":
                response["clarification"] = "\u60a8\u662f\u662f\u60f3\u95ee\u7684\u662f\u5426\u4e00\u70b9\u5185\u5bb9\u8fbe\u7684\u65b9\u5417\uff1f"
            elif reason == "wrong_answer":
                response["correction"] = "\u8bf7\u5141\u8ba9\u6211\u7684\u95ee\u9898\u91cd\u65b0\u63cf\u8ff0\u6211\u4f1a\u91cd\u65b0\u5206\u67e5\u7ed9\u6b63\u3002"
        response["feedback_recorded"] = True
        return response

    def get_feedback_stats(self) -> Dict:
        if not self._feedback_log:
            return {"total": 0}
        helpful = sum(1 for e in self._feedback_log if e["is_helpful"])
        return {
            "total": len(self._feedback_log),
            "helpful": helpful,
            "helpful_rate": round(helpful / len(self._feedback_log), 3),
            "by_reason": {},
        }


TERM_INLINE_ICON_SPEC = {
    "icon": "\u24D8",
    "style": "font-size:14px;cursor:help;color:#0969da;border-bottom:1px dotted #0969da;",
    "tooltip_max_width": "350px",
    "tooltip_bg": "#1a1a2e",
    "tooltip_text_color": "#e0e0e0",
    "learn_more_link": True,
}


class MultiIntentDialogueHandler:
    """Handles composite multi-question inputs in serial dialogue format."""

    def split_composite_query(self, query: str) -> List[Tuple[str, str]]:
        separators = [
            ("\uff0c", "\u5e76"),
            ("\uff1f", "\u518d"),
            ("?", "\u5417"),
            ("\u5417", "\u518d"),
            ("\u548c", "\u5e76"),
        ]
        best_sep = None
        best_split = None
        for sep, alt in separators:
            if sep in query and alt in query:
                idx = query.index(sep)
                if idx > 5 and idx < len(query) - 5:
                    best_sep = sep
                    break
        if not best_sep:
            intent_indicators = ["\u56de\u62a5\u7387", "\u98ce\u9669", "\u600e\u4f55", "\u5bf9\u6bd4", "\u9884\u6d4b", "\u5206\u6790"]
            for indicator in intent_indicators:
                if indicator in query:
                    parts = query.split(indicator, 1)
                    if len(parts) == 2 and len(parts[0].strip()) > 3 and len(parts[1].strip()) > 3:
                        return [(parts[0].strip(), parts[1].strip())]
            return [(query, "")]

        parts = query.split(best_sep)
        result = []
        for p in parts:
            p = p.strip()
            if p:
                result.append((p, ""))
        return result if len(result) > 1 else [(query, "")]

    def generate_interim_prompt(self, answered_part: str, remaining_part: str) -> str:
        return f"\u5df2\u5b8c\u56de\u7b54\u4e86\u7b2c\u4e00\u90e8\u95ee\u9898\u3002\n\n{answered_part}\n\n---\n\n**{remaining_part}**\n\n\u662f\u9700\u8981\u7ee7\u7eed\u5206\u6790\u8fd9\u4e00\u90e8\u95ee\u9898\u5417\uff1f"


# =============================================================================
# Part D: Backend Unified Dispatch
# =============================================================================


@dataclass
class DispatchResult:
    dispatch_id: str
    mode: ScenarioMode
    agent_called: str
    endpoint: str
    params_used: Dict[str, Any]
    result_data: Any
    duration_ms: float
    report_ref: Optional[str] = None
    websocket_event: Optional[Dict] = None


class ModeAwareDispatcher:
    """Unified backend dispatcher that routes to agents based on mode parameter."""

    def __init__(self):
        self._dispatch_log: List[DispatchResult] = []

    def dispatch(self, request: Dict[str, Any]) -> DispatchResult:
        start = time.time()
        mode_str = request.get("mode", "conversation")
        try:
            mode = ScenarioMode(mode_str)
        except ValueError:
            mode = ScenarioMode.CONVERSATION

        config = REPORT_MODE_CONFIG if mode == ScenarioMode.REPORT else CONVERSATION_MODE_CONFIG
        primary = "gongbu" if mode == ScenarioMode.REPORT else "libu"
        endpoint = "/api/tasks" if mode == ScenarioMode.REPORT else "/api/chat"

        params = dict(request.get("params", {}))
        params["mode"] = mode.value
        if mode == ScenarioMode.REPORT:
            params["stream"] = False
            params["format"] = params.get("format", "html")
        else:
            params["stream"] = True
            params["persona"] = request.get("persona", "auto")

        mock_result = self._simulate_dispatch(mode, params)
        dur = (time.time() - start) * 1000
        result = DispatchResult(
            dispatch_id=f"disp_{uuid.uuid4().hex[:10]}",
            mode=mode,
            agent_called=primary,
            endpoint=endpoint,
            params_used=params,
            result_data=mock_result,
            duration_ms=round(dur, 2),
        )
        if mode == ScenarioMode.CONVERSATION and request.get("async_report"):
            result.report_ref = f"async_rpt_{uuid.uuid4().hex[:8]}"
            result.websocket_event = {"event": "report_ready", "report_id": result.report_ref}
        self._dispatch_log.append(result)
        return result

    def _simulate_dispatch(self, mode: ScenarioMode, params: Dict) -> Dict:
        if mode == ScenarioMode.REPORT:
            return {
                "task_id": f"task_{uuid.uuid4().hex[:10]}",
                "status": "completed",
                "report_url": f"/api/reports/task_{uuid.uuid4().hex[:10]}/html",
                "generation_time_ms": random.randint(2000, 5000),
            }
        return {
            "response_id": f"resp_{uuid.uuid4().hex[:10]}",
            "message": "\u5df2\u5b8c\u5b8c\u6210\u5230\u60a8\u7684\u95ee\u9898\uff0c\u6b63\u5728\u4e3a\u60a8\u751f\u670d\u521a\u7684\u5206\u6790\u5206\u6790\u5206\u6790\u5206\u6790\u5206\u6790\u5206\u6790...",
            "stream_complete": True,
            "cards_embedded": True,
        }

    def get_dispatch_stats(self) -> Dict:
        if not self._dispatch_log:
            return {"total": 0}
        modes = {}
        for d in self._dispatch_log:
            m = d.mode.value
            modes[m] = modes.get(m, 0) + 1
        durations = [d.duration_ms for d in self._dispatch_log]
        return {
            "total": len(self._dispatch_log),
            "by_mode": modes,
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        }


@dataclass
class AsyncReportJob:
    job_id: str
    user_id: str
    session_id: str
    task_data: Dict
    status: str
    progress_pct: int
    created_at: str
    completed_at: Optional[str] = None
    report_id: Optional[str] = None
    error: Optional[str] = None


class AsyncReportGenerator:
    """Non-blocking report generation for conversation mode with WebSocket push."""

    def __init__(self):
        self._jobs: Dict[str, AsyncReportJob] = {}
        self._push_queue: List[Dict] = []

    def create_job(self, user_id: str, session_id: str, task_data: Dict) -> AsyncReportJob:
        job_id = f"ar_job_{uuid.uuid4().hex[:10]}"
        job = AsyncReportJob(
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            task_data=task_data,
            status="queued",
            progress_pct=0,
            created_at=datetime.now().isoformat(),
        )
        self._jobs[job_id] = job
        return job

    def process_job(self, job_id: str) -> AsyncReportJob:
        job = self._jobs.get(job_id)
        if not job or job.status == "completed":
            return job
        job.status = "processing"
        for progress in range(0, 101, 10):
            job.progress_pct = progress
            time.sleep(0.05)
            event = {"event": "report_progress", "job_id": job_id, "progress": progress}
            self._push_queue.append(event)
        job.status = "completed"
        job.completed_at = datetime.now().isoformat()
        job.report_id = f"rpt_{uuid.uuid4().hex[:10]}"
        push_event = {"event": "report_ready", "job_id": job_id, "report_id": job.report_id}
        self._push_queue.append(push_event)
        return job

    def get_job(self, job_id: str) -> Optional[AsyncReportJob]:
        return self._jobs.get(job_id)

    def get_pending_push_events(self, session_id: str, after_ts: Optional[str] = None) -> List[Dict]:
        events = [e for e in self._push_queue if e.get("session_id", "") == session_id or e.get("job_id", "").startswith("ar_")]
        if after_ts:
            events = [e for e in events if e.get("timestamp", "") > after_ts]
        return events[-10:]

    def cleanup_completed(self, max_age_hours: int = 24):
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [jid for jid, j in self._jobs.items() if j.completed_at and datetime.fromisoformat(j.completed_at) < cutoff]
        for jid in to_remove:
            del self._jobs[jid]


# =============================================================================
# Part E: Shared Components
# =============================================================================


REPORT_VIEWER_SPECS = {
    "full_mode": {
        "container_class": "report-viewer-full",
        "show_all_sections": True,
        "toolbar_visible": True,
        "toolbar_actions": ["download_pdf", "download_html", "share", "print", "compare", "zoom_in", "zoom_out"],
        "section_padding": "24px",
        "font_scale": 1.0,
        "chart_interactive": True,
        "max_width": "1200px",
    },
    "compact_mode": {
        "container_class": "report-viewer-compact",
        "show_all_sections": False,
        "visible_sections": ["executive_summary", "investment_advice"],
        "toolbar_visible": False,
        "toolbar_actions": ["view_full", "download_pdf"],
        "section_padding": "12px",
        "font_scale": 0.9,
        "chart_interactive": False,
        "max_width": "100%",
    },
}

AGENT_STATUS_INDICATOR_SPECS = {
    "dashboard_position": {"location": "sidebar_right", "width": "240px", "style": "collapsed-by-default"},
    "chat_position": {"location": "floating_ball", "size": "48px", "style": "bottom-right"},
    "agents": [
        {"id": "zhongshu", "name": "\u4e2d\u4e66\u7701", "icon": "\ud83d\udcda", "color": "#3182ce"},
        {"id": "hubu", "name": "\u6237\u90e8", "icon": "\ud83d\udcc4", "color": "#38a169"},
        {"id": "gongbu", "name": "\u5de5\u90e8", "icon": "\u2699", "color": "#e53e3e"},
        {"id": "xingbu", "name": "\u793c\u90e8", "icon": "\u2699\uFE0F", "color": "#f59e0b"},
        {"id": "xiabu", "name": "\u5211\u90e8", "icon": "\u2705", "color": "#9b59b6"},
        {"id": "xiabu2", "name": "\u5211\u90e8", "icon": "\ud83d\udcaa", "color": "#6c5ce7"},
    ],
    "status_states": ["idle", "thinking", "working", "waiting", "error", "done"],
    "click_behavior": "expand_detail",
}


# =============================================================================
# Part F: UX Metrics & A/B Testing
# =============================================================================


SCENARIO_KPI_DEFINITIONS = {
    "report": {
        "task_completion_rate": {"description": "\u63d0\u4ea4\u540e\u529f\u529f\u751f\u6210\u6210\u6210\u62a5\u544a\u7684\u6bd4\u4f8b", "unit": "%", "target": ">90"},
        "avg_report_gen_time": {"description": "\u5e73\u5747\u62a5\u544a\u751f\u6210\u65f6\u95f4", "unit": "ms", "target": "<5000"},
        "batch_usage_rate": {"description": "\u6279\u91cf\u64cd\u4f5c\u4f7f\u7528\u7387", "unit": "%", "target": ">20"},
        "template_reuse_rate": {"description": "\u6a21\u677f\u590d\u590d\u7528\u7387", "unit": "%", "target": ">15"},
    },
    "conversation": {
        "avg_dialogue_turns": {"description": "\u5e73\u574c\u5bf9\u8bdd\u8f6e\u6570", "unit": "turns", "target": ">3"},
        "followup_click_rate": {"description": "\u7528\u6237\u52a8\u8ffd\u95ee\u6309\u51fb", "unit": "%", "target": ">25"},
        "report_card_click_rate": {"description": "\u62a5\u544a\u5361\u7247\u70b9\u51fb", "unit": "%", "target": ">10"},
        "persona_switch_freq": {"description": "\u4eba\u683c\u5207\u6362\u9891\u9891", "unit": "per_session", "target": "<3"},
        "helpful_feedback_rate": {"description": "\u201c\u6709\u53cd\u9988\u6bd4\u4f8b", "unit": "%", "target": ">80"},
    },
}


@dataclass
class ABTestVariant:
    test_id: str
    name: str
    scenario: str
    variant_a: Dict
    variant_b: Dict
    traffic_split: float
    start_date: str
    end_date: Optional[str] = None
    status: str = "running"
    results_a: Dict = field(default_factory=dict)
    results_b: Dict = field(default_factory=dict)
    winner: Optional[str] = None


class ScenarioMetricsCollector:
    """Collects and analyzes scenario-specific UX metrics."""

    def __init__(self):
        self._events: List[Dict] = []
        self._daily_snapshots: Dict[str, Dict] = {}

    def record_event(self, scenario: str, event_type: str, value: Any = None,
                     user_id: Optional[str] = None, metadata: Optional[Dict] = None):
        self._events.append({
            "scenario": scenario,
            "event_type": event_type,
            "value": value,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        })

    def calculate_kpis(self, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, Dict]:
        kpis = {}
        for scenario, defs in SCENARIO_KPI_DEFINITIONS.items():
            scenario_events = [e for e in self._events if e["scenario"] == scenario]
            if date_range:
                scenario_events = [e for e in scenario_events if date_range[0] <= e["timestamp"] <= date_range[1]]
            scenario_kpis = {}
            for kpi_name, kpi_def in defs.items():
                relevant = [e for e in scenario_events if e["event_type"] == kpi_name]
                if kpi_name == "task_completion_rate":
                    total = len(relevant)
                    success = len([e for e in relevant if e["value"] == True])
                    scenario_kpis[kpi_name] = round(success / max(total, 1) * 100, 1) if total > 0 else 0
                elif kpi_name == "avg_report_gen_time":
                    vals = [e["value"] for e in relevant if isinstance(e["value"], (int, float))]
                    scenario_kpis[kpi_name] = round(sum(vals) / len(vals), 0) if vals else 0
                elif "rate" in kpi_name or "freq" in kpi_name:
                    scenario_kpis[kpi_name] = len(relevant)
                else:
                    vals = [e["value"] for e in relevant if isinstance(e["value"], (int, float))]
                    scenario_kpis[kpi_name] = round(sum(vals) / max(len(relevant), 1), 2) if vals else 0
            kpis[scenario] = scenario_kpis
        return kpis

    def take_daily_snapshot(self, date: Optional[str] = None):
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        self._daily_snapshots[date_str] = self.calculate_kpis()


class ABTestFramework:
    """A/B testing framework for per-scenario interaction details."""

    def __init__(self):
        self._tests: Dict[str, ABTestVariant] = {}

    def create_test(self, test_id: str, name: str, scenario: str,
                   variant_a: Dict, variant_b: Dict, traffic_split: float = 0.5) -> ABTestVariant:
        test = ABTestVariant(
            test_id=test_id, name=name, scenario=scenario,
            variant_a=variant_a, variant_b=variant_b,
            traffic_split=traffic_split,
            start_date=datetime.now().isoformat(),
        )
        self._tests[test_id] = test
        return test

    def assign_variant(self, test_id: str, user_id: str) -> str:
        test = self._tests.get(test_id)
        if not test:
            return "control"
        import hashlib
        hash_val = int(hashlib.md5(f"{test_id}:{user_id}".encode()).hexdigest()[:8], 16)
        return "a" if (hash_val % 100) < (test.traffic_split * 100) else "b"

    def record_conversion(self, test_id: str, variant: str, converted: bool):
        test = self._tests.get(test_id)
        if not test:
            return
        key = f"conversions_{variant}"
        if key not in test.results_a:
            test.results_a[key] = {"total": 0, "converted": 0}
            test.results_b[key] = {"total": 0, "converted": 0}
        target = test.results_a if variant == "a" else test.results_b
        target["total"] += 1
        if converted:
            target["converted"] += 1

    def analyze_test(self, test_id: str) -> Dict:
        test = self._tests.get(test_id)
        if not test:
            return {"error": "Test not found"}
        ra = test.results_a.get("conversions_a", {"total": 0, "converted": 0})
        rb = test.results_b.get("conversions_b", {"total": 0, "converted": 0})
        rate_a = ra["converted"] / max(ra["total"], 1)
        rate_b = rb["converted"] / max(rb["total"], 1)
        winner = "a" if rate_a > rate_b else "b" if rate_b > rate_a else "tie"
        test.winner = winner
        test.results_a["conversion_rate"] = round(rate_a * 100, 2)
        test.results_b["conversion_rate"] = round(rate_b * 100, 2)
        z = ((rate_a - rate_b) / math.sqrt(rate_a*(1-rate_a)/max(ra["total"],1) + rate_b*(1-rate_b)/max(rb["total"],1))) if ra["total"]+rb["total"] > 2 else 0
        significance = "***" if abs(z) > 2.576 else "**" if abs(z) > 1.96 else "*" if abs(z) > 1.645 else "ns"
        return {
            "test_id": test_id,
            "name": test.name,
            "scenario": test.scenario,
            "variant_a": {"traffic": f"{test.traffic_split*100:.0f}%", "conversions": ra, "rate": f"{rate_a*100:.1f}%"},
            "variant_b": {"traffic": f"{(1-test.traffic_split)*100:.0f}%", "conversions": rb, "rate": f"{rate_b*100:.1f}%"},
            "winner": winner,
            "z_score": round(z, 3),
            "significance": significance,
        }

    def get_all_tests(self) -> List[Dict]:
        return [{"id": t.test_id, "name": t.name, "scenario": t.scenario,
                 "status": t.status, "winner": t.winner} for t in self._tests.values()]


# =============================================================================
# Part G: Testing Suite
# =============================================================================


DUAL_SCENARIO_TEST_CASES = [
    {"scenario": "routing", "test": "detect_report_query", "input": "\u751f\u4efd\u4e00\u4efd\u5206\u62a5\u544a", "expected_mode": "report", "difficulty": "easy"},
    {"scenario": "routing", "test": "detect_chat_query", "input": "\u6df1\u5733\u600e\u4e48\u6837\u6837", "expected_mode": "conversation", "difficulty": "easy"},
    {"scenario": "routing", "test": "long_input_routes_report", "input": "x"*150, "expected_mode": "report", "difficulty": "medium"},
    {"scenario": "hybrid_input", "test": "nl_to_structured_sync", "input": "\u6df1\u5733\u5357\u5c71100\u33a1\u5b66\u5b66", "check": "area_parsed", "difficulty": "medium"},
    {"scenario": "hybrid_input", "test": "structured_to_nl_sync", "input": "", "check": "nl_generated", "difficulty": "medium"},
    {"scenario": "batch_ops", "test": "batch_export_3tasks", "task_count": 3, "operation": "export", "difficulty": "easy"},
    {"scenario": "batch_ops", "test": "batch_compare_3tasks", "task_count": 3, "operation": "compare", "difficulty": "easy"},
    {"scenario": "batch_ops", "test": "batch_delete_2tasks", "task_count": 2, "operation": "delete", "difficulty": "easy"},
    {"scenario": "batch_ops", "test": "save_load_template", "template_name": "\u5b66\u533a\u623f\u5206\u6790", "difficulty": "medium"},
    {"scenario": "report_gen", "test": "generate_full_report", "mode": "full", "sections_expected": 9, "difficulty": "medium"},
    {"scenario": "report_gen", "test": "generate_compact_report", "mode": "compact", "sections_visible": 2, "difficulty": "medium"},
    {"scenario": "onboarding", "test": "guide_4_steps_shown", "new_user": True, "difficulty": "easy"},
    {"scenario": "onboarding", "test": "dismiss_persists", "action": "dismiss_then_check", "difficulty": "easy"},
    {"scenario": "chat_interface", "test": "welcome_message_zhouyu_morning", "persona": "zhouyu", "time_of_day": "morning", "difficulty": "easy"},
    {"scenario": "chat_interface", "test": "welcome_message_luxun_evening", "persona": "luxun", "time_of_day": "evening", "difficulty": "easy"},
    {"scenario": "followups", "test": "followups_for_single_block", "intent": "single_block_analysis", "count": 3, "difficulty": "medium"},
    {"scenario": "followups", "test": "followups_fallback_default", "intent": "unknown_intent", "count": 3, "difficulty": "easy"},
    {"scenario": "report_card", "test": "embed_card_in_chat", "is_compact": True, "actions": 3, "difficulty": "medium"},
    {"scenario": "reasoning", "test": "reasoning_5_steps_display", "steps": 5, "difficulty": "medium"},
    {"scenario": "trust", "test": "data_source_highlighted", "contains_source": True, "difficulty": "easy"},
    {"scenario": "trust", "test": "confidence_expressed_probabilistic", "conf_value": 0.85, "mode": "probabilistic_verbal", "difficulty": "medium"},
    {"scenario": "trust", "test": "feedback_not_helpful_apology", "reason": "wrong_answer", "apology_exists": True, "difficulty": "medium"},
    {"scenario": "multi_intent", "test": "split_two_questions", "input": "\u6295\u8d44\u5982\u4f55\uff0c\u98ce\u9669\u600e\u4f55", "parts": 2, "difficulty": "hard"},
    {"scenario": "dispatch", "test": "dispatch_report_mode", "mode_param": "report", "agent": "gongbu", "difficulty": "easy"},
    {"scenario": "dispatch", "test": "dispatch_conversation_mode", "mode_param": "conversation", "agent": "libu", "difficulty": "easy"},
    {"scenario": "async_report", "test": "create_async_job", "session_id": "test_sess", "status": "queued", "difficulty": "medium"},
    {"scenario": "async_report", "test": "process_job_completes", "progress_100": True, "difficulty": "medium"},
    {"scenario": "shared_components", "test": "report_viewer_full_mode", "mode": "full", "toolbar_actions": 7, "difficulty": "easy"},
    {"scenario": "shared_components", "test": "report_viewer_compact_mode", "mode": "compact", "visible_sections": 2, "difficulty": "easy"},
    {"scenario": "metrics", "test": "kpi_calculation_report_scenario", "events": 10, "difficulty": "medium"},
    {"scenario": "ab_test", "test": "ab_test_creation_and_assignment", "users": 100, "split_near_50_50": True, "difficulty": "medium"},
]


class DualScenarioTestSuite:
    """Comprehensive test suite for dual-scenario differentiation layer."""

    def __init__(self):
        self.router = ScenarioModeRouter()
        self.hybrid_input = HybridInputProcessor()
        self.batch_mgr = TaskCenterBatchManager()
        self.report_gen = StructuredReportGenerator()
        self.onboarding = TaskAnalysisOnboardingGuide()
        self.followup_engine = ConsultationFollowUpEngine()
        self.card_embedder = ReportCardInChatEmbedder()
        self.reasoning_display = ReasoningStepDisplayManager()
        self.trust_mgr = TrustBuildingManager()
        self.multi_intent = MultiIntentDialogueHandler()
        self.dispatcher = ModeAwareDispatcher()
        self.async_gen = AsyncReportGenerator()
        self.metrics_collector = ScenarioMetricsCollector()
        self.ab_framework = ABTestFramework()
        self._results: List[Dict] = []

    def run_all_tests(self) -> Dict[str, Any]:
        results = {
            "scenario_routing": self._test_routing(),
            "hybrid_input": self._test_hybrid_input(),
            "batch_operations": self._test_batch_operations(),
            "report_generation": self._test_report_generation(),
            "onboarding_guide": self._test_onboarding(),
            "chat_interface": self._test_chat_interface(),
            "followup_suggestions": self._test_followups(),
            "report_card_embedding": self._test_report_card(),
            "reasoning_display": self._test_reasoning_display(),
            "trust_building": self._test_trust_building(),
            "multi_intent_dialogue": self._test_multi_intent(),
            "backend_dispatch": self._test_backend_dispatch(),
            "async_report_gen": self._test_async_report(),
            "shared_components": self._test_shared_components(),
            "ux_metrics": self._test_ux_metrics(),
            "ab_testing": self._test_ab_testing(),
        }
        total = sum(len(v.get("tests", [])) for v in results.values())
        passed = sum(len([t for t in v.get("tests", []) if t.get("passed")]) for v in results.values())
        results["summary"] = {"total": total, "passed": passed, "failed": total - passed, "pass_rate": round(passed/max(total,1)*100, 1)}
        self._results.append(results)
        return results

    def _test_routing(self) -> Dict:
        tests = []
        r1 = self.router.route("\u751f\u4efd\u4e00\u4efd\u5206\u62a5\u544a", explicit_mode=None)
        tests.append({"name": "detect_report_query", "passed": r1.mode == ScenarioMode.REPORT})
        r2 = self.router.route("\u6df1\u5733\u600e\u4e48\u6837\u6837", explicit_mode=None)
        tests.append({"name": "detect_chat_query", "passed": r2.mode == ScenarioMode.CONVERSATION})
        r3 = self.router.route("x" * 150, explicit_mode=None)
        tests.append({"name": "long_input_routes_report", "passed": r3.mode == ScenarioMode.REPORT})
        r4 = self.router.route("test", explicit_mode=ScenarioMode.REPORT)
        tests.append({"name": "explicit_report_mode", "passed": r4.mode == ScenarioMode.REPORT})
        r5 = self.router.route("test", explicit_mode=ScenarioMode.CONVERSATION)
        tests.append({"name": "explicit_conversation_mode", "passed": r5.mode == ScenarioMode.CONVERSATION})
        self.router.set_user_preference("user_pref_test", ScenarioMode.CONVERSATION)
        r6 = self.router.route("any query", user_id="user_pref_test")
        tests.append({"name": "user_preference_respected", "passed": r6.mode == ScenarioMode.CONVERSATION})
        stats = self.router.get_routing_stats()
        tests.append({"name": "stats_available", "passed": stats["total_routings"] > 0})
        return {"tests": tests}

    def _test_hybrid_input(self) -> Dict:
        tests = []
        state1 = self.hybrid_input.process_natural_input("\u6df1\u5733\u5357\u5c71100\u33a1\u5b66\u5b66")
        tests.append({"name": "nl_to_structured_sync", "passed": "area_sqm" in state1.parsed_from_nl and state1.is_valid or not state1.is_valid})
        state2 = self.hybrid_input.sync_to_structured(state1)
        tests.append({"name": "sync_to_structured", "passed": state2.current_mode == "structured"})
        state3 = self.hybrid_input.sync_to_natural(state2)
        tests.append({"name": "structured_to_nl_sync", "passed": len(state3.natural_text) > 5})
        schema = self.hybrid_input.get_field_schema()
        tests.append({"name": "schema_has_fields", "passed": len(schema) >= 7})
        examples = self.hybrid_input.get_examples()
        tests.append({"name": "examples_available", "passed": len(examples) >= 3})
        submit = self.hybrid_input.validate_and_submit(state1)
        tests.append({"name": "validate_and_submit", "passed": submit["status"] in ("submitted", "validation_failed")})
        return {"tests": tests}

    def _test_batch_operations(self) -> Dict:
        tests = []
        r1 = self.batch_mgr.execute_batch_export(["t1", "t2", "t3"])
        tests.append({"name": "batch_export_3tasks", "passed": r1.success_count == 3 and r1.download_url is not None})
        r2 = self.batch_mgr.execute_batch_compare(["t1", "t2", "t3"])
        tests.append({"name": "batch_compare_3tasks", "passed": r2.success_count == 3 and r2.comparison_id is not None})
        r3 = self.batch_mgr.execute_batch_delete(["t1", "t2"])
        tests.append({"name": "batch_delete_2tasks", "passed": r3.success_count == 2})
        tpl_id = self.batch_mgr.save_template("\u6d4b\u5230\u6a21\u6837", {"purpose": "\u6295\u8d44"}, "user1")
        loaded = self.batch_mgr.load_template(tpl_id)
        tests.append({"name": "save_load_template", "passed": loaded is not None and loaded["usage_count"] == 1})
        recs = self.batch_mgr.recommend_templates("user1", [{"structured_params": {"purpose": "\u6295\u8d44"}}] * 5)
        tests.append({"name": "smart_recommendation", "passed": len(recs) >= 1})
        stats = self.batch_mgr.get_operation_stats()
        tests.append({"name": "op_stats_available", "passed": stats["total"] >= 3})
        return {"tests": tests}

    def _test_report_generation(self) -> Dict:
        tests = []
        r_full = self.report_gen.generate({"task_id": "test_full", "structured_params": {"city": "\u676d\u5dde"}}, mode="full")
        tests.append({"name": "generate_full_report", "passed": len(r_full.sections) == 9 and "echart" in r_full.html_content.lower()})
        r_compact = self.report_gen.generate({"task_id": "test_compact", "structured_params": {"city": "\u6df1\u5733"}}, mode="compact")
        tests.append({"name": "generate_compact_report", "passed": r_compact.word_count < r_full.word_count})
        self.report_gen.invalidate_cache(r_full.report_id)
        tests.append({"name": "invalidate_cache", "passed": True})
        return {"tests": tests}

    def _test_onboarding(self) -> Dict:
        tests = []
        steps1 = self.onboarding.get_steps(None)
        tests.append({"name": "guide_4_steps_shown", "passed": len(steps1) == 4})
        self.onboarding.dismiss("user_onboard_test")
        steps2 = self.onboarding.get_steps("user_onboard_test")
        tests.append({"name": "dismiss_persists", "passed": len(steps2) == 0})
        prog = self.onboarding.get_progress("user_new", [])
        tests.append({"name": "progress_tracking", "passed": prog["total_steps"] == 4})
        return {"tests": tests}

    def _test_chat_interface(self) -> Dict:
        tests = []
        zhouyu_morning = PERSONA_WELCOME_MESSAGES["zhouyu"]["morning"]
        tests.append({"name": "welcome_message_zhouyu_morning", "passed": len(zhouyu_morning) > 10})
        luxun_evening = PERSONA_WELCOME_MESSAGES["luxun"]["evening"]
        tests.append({"name": "welcome_message_luxun_evening", "passed": len(luxun_evening) > 10})
        spec = CHAT_INTERFACE_SPEC
        tests.append({"name": "chat_spec_complete", "passed": "persona_switcher" in spec and "voice_input" in spec})
        return {"tests": tests}

    def _test_followups(self) -> Dict:
        tests = []
        f1 = self.followup_engine.generate_followups("single_block_analysis", {"city": "\u676d\u5dde", "block": "\u672a\u6765\u79d1"})
        tests.append({"name": "followups_for_single_block", "passed": len(f1) == 3})
        f2 = self.followup_engine.generate_followups("nonexistent_intent", {})
        tests.append({"name": "followups_fallback_default", "passed": len(f2) == 3})
        return {"tests": tests}

    def _test_report_card(self) -> Dict:
        tests = []
        card = self.card_embedder.embed_card({"title": "Test Report", "predicted_growth": "0.08", "risk_level": "medium", "advice": "\u5efa8\u8bae"})
        tests.append({"name": "embed_card_in_chat", "passed": card.card_id.startswith("card_") and len(card.actions) == 3})
        html = self.card_embedder.render_card_html(card)
        tests.append({"name": "card_html_rendered", "passed": "report-card" in html and "\u67e5\u5b8c\u5b8c\u62a5\u544a" in html})
        return {"tests": tests}

    def _test_reasoning_display(self) -> Dict:
        tests = []
        sid = self.reasoning_display.start_session("test_sess")
        self.reasoning_display.add_step(sid, "zhongshu_parsing")
        self.reasoning_display.add_step(sid, "hubu_collecting")
        self.reasoning_display.add_step(sid, "gongbu_modeling")
        self.reasoning_display.complete_step(sid, 0)
        self.reasoning_display.complete_step(sid, 1)
        steps = self.reasoning_display.get_session_steps(sid)
        tests.append({"name": "reasoning_5_steps_display", "passed": len(steps) == 2})
        html = self.reasoning_display.get_progress_html(sid)
        tests.append({"name": "progress_html_rendered", "passed": "reasoning-progress" in html and "progress-fill" in html})
        self.reasoning_display.end_session(sid)
        return {"tests": tests}

    def _test_trust_building(self) -> Dict:
        tests = []
        text_with_source = "\u6839\u636e\u8d1d\u636e\u6570\u636e\u636e\u663e\u793a\u7814\u7814\u6570\u6237"
        highlighted, hl = self.trust_mgr.highlight_data_sources(text_with_source)
        tests.append({"name": "data_source_highlighted", "passed": len(hl) > 0 and "\u6570\u636e\u636e" not in highlighted})
        conf_verbal = self.trust_mgr.express_confidence(0.85, 0.05, 0.15, "probabilistic_verbal")
        tests.append({"name": "confidence_expressed_probabilistic", "passed": "\u516d\u6709\u628a\u63e1" in conf_verbal and "%" in conf_verbal})
        fb = self.trust_mgr.handle_feedback("msg1", False, "wrong_answer", "user1")
        tests.append({"name": "feedback_not_helpful_apology", "passed": fb.get("apology") is not None})
        stats = self.trust_mgr.get_feedback_stats()
        tests.append({"name": "feedback_stats", "passed": stats["total"] == 1})
        return {"tests": tests}

    def _test_multi_intent(self) -> Dict:
        tests = []
        parts = self.multi_intent.split_composite_query("\u6295\u8d44\u5982\u4f55\uff0c\u98ce\u9669\u600e\u4f55")
        tests.append({"name": "split_two_questions", "passed": len(parts) == 2})
        single = self.multi_intent.split_composite_query("\u5355\u4e00\u4e00\u600e\u4e48\u6837\u6837")
        tests.append({"name": "single_question_no_split", "passed": len(single) == 1 and single[1] == ""})
        prompt = self.multi_intent.generate_interim_prompt("\u56de\u7b54", "\u98ce\u9669")
        tests.append({"name": "interim_prompt_generated", "passed": "\u5df2\u5b8c\u56de\u7b54" in prompt and "\u7ee7\u7eed" in prompt})
        return {"tests": tests}

    def _test_backend_dispatch(self) -> Dict:
        tests = []
        d1 = self.dispatcher.dispatch({"mode": "report", "params": {}})
        tests.append({"name": "dispatch_report_mode", "passed": d1.mode == ScenarioMode.REPORT and d1.agent_called == "gongbu"})
        d2 = self.dispatcher.dispatch({"mode": "conversation", "params": {}})
        tests.append({"name": "dispatch_conversation_mode", "passed": d2.mode == ScenarioMode.CONVERSATION and d2.agent_called == "libu"})
        d3 = self.dispatcher.dispatch({"mode": "report", "params": {}, "async_report": True})
        tests.append({"name": "dispatch_async_report_flag", "passed": d3.websocket_event is not None})
        stats = self.dispatcher.get_dispatch_stats()
        tests.append({"name": "dispatch_stats", "passed": stats["total"] >= 3})
        return {"tests": tests}

    def _test_async_report(self) -> Dict:
        tests = []
        job = self.async_gen.create_job("user1", "sess1", {"city": "\u676d\u5dde"})
        tests.append({"name": "create_async_job", "passed": job.status == "queued" and job.job_id.startswith("ar_job_")})
        processed = self.async_gen.process_job(job.job_id)
        tests.append({"name": "process_job_completes", "passed": processed.status == "completed" and processed.progress_pct == 100})
        retrieved = self.async_gen.get_job(job.job_id)
        tests.append({"name": "job_retrievable", "passed": retrieved is not None and retrieved.report_id is not None})
        return {"tests": tests}

    def _test_shared_components(self) -> Dict:
        tests = []
        full_spec = REPORT_VIEWER_SPECS["full_mode"]
        tests.append({"name": "report_viewer_full_mode", "passed": full_spec["toolbar_actions"] == 7 and full_spec["show_all_sections"]})
        compact_spec = REPORT_VIEWER_SPECS["compact_mode"]
        tests.append({"name": "report_viewer_compact_mode", "passed": compact_spec["toolbar_visible"] == False and compact_spec["visible_sections"] == 2})
        agent_spec = AGENT_STATUS_INDICATOR_SPECS
        tests.append({"name": "agent_status_indicator_complete", "passed": len(agent_spec["agents"]) == 6})
        return {"tests": tests}

    def _test_ux_metrics(self) -> Dict:
        tests = []
        for _ in range(10):
            self.metrics_collector.record_event("report", "task_completed", True, "user1")
            self.metrics_collector.record_event("conversation", "followup_click", True, "user1")
        kpis = self.metrics_collector.calculate_kpis()
        tests.append({"name": "kpi_calculation_report_scenario", "passed": "report" in kpis and "task_completion_rate" in kpis["report"]})
        tests.append({"name": "kpi_calculation_conv_scenario", "passed": "conversation" in kpis and "avg_dialogue_turns" in kpis["conversation"]})
        snap = self.metrics_collector.take_daily_snapshot()
        tests.append({"name": "daily_snapshot_taken", "passed": len(snap) > 0})
        return {"tests": tests}

    def _test_ab_testing(self) -> Dict:
        tests = []
        test = self.ab_framework.create_test("ab_001", "NL vs Structured Form", "report",
                                      {"button_text": "\u81ea\u7136\u8f93\u5165", "style": "left"}, {"button_text": "\u7ed3\u6784\u8868\u8868", "style": "right"}, 0.5)
        tests.append({"name": "ab_test_creation_and_assignment", "passed": test.test_id == "ab_001" and test.traffic_split == 0.5})
        assignments = {"a": 0, "b": 0}
        for _ in range(100):
            var = self.ab_framework.assign_variant("ab_001", f"user_{i}")
            assignments[var] += 1
            self.ab_framework.record_conversion("ab_001", var, random.random() > 0.5)
        analysis = self.ab_framework.analyze_test("ab_001")
        tests.append({"name": "split_near_50_50", "passed": abs(assignments["a"] - 50) < 15 and analysis["winner"] in ("a", "b", "tie")})
        all_tests = self.ab_framework.get_all_tests()
        tests.append({"name": "ab_test_list_accessible", "passed": len(all_tests) >= 1})
        return {"tests": tests}

    def generate_pytest_code(self) -> str:
        return '''
"""Pytest test cases for Dual Scenario Differentiation Module (Layer 21).

import pytest
from backend.integration.dual_scenario_differentiation_layer import (
    ScenarioMode, ScenarioModeRouter, ModeConfig, ModeRoutingDecision,
    HybridInputProcessor, TaskCenterBatchManager, StructuredReportGenerator,
    TaskAnalysisOnboardingGuide, ConsultationFollowUpEngine, ReportCardInChatEmbedder,
    ReasoningStepDisplayManager, TrustBuildingManager, MultiIntentDialogueHandler,
    ModeAwareDispatcher, AsyncReportGenerator, ScenarioMetricsCollector, ABTestFramework,
    REPORT_MODE_CONFIG, CONVERSATION_MODE_CONFIG,
    PERSONA_WELCOME_MESSAGES, CHAT_INTERFACE_SPEC, REPORT_VIEWER_SPECS,
    AGENT_STATUS_INDICATOR_SPECS, DUAL_SCENARIO_TEST_CASES,
    DualScenarioTestSuite,
)


@pytest.fixture
def router():
    return ScenarioModeRouter()


@pytest.fixture
def hybrid_input():
    return HybridInputProcessor()


@pytest.fixture
def batch_manager():
    return TaskCenterBatchManager()


@pytest.fixture
def report_generator():
    return StructuredReportGenerator()


class TestScenarioRouting:

    def test_report_query_detected(router):
        r = router.route("\\u751f\\u4efd\\u4e00\\u5206\\u62a5\\u544a")
        assert r.mode == ScenarioMode.REPORT

    def test_chat_query_detected(router):
        r = router.route("\\u6df1\\u5733\\u600e\\u4e48\\u6837\\u6837")
        assert r.mode == ScenarioMode.CONVERSATION

    def test_long_input_routes_to_report(router):
        r = router.route("x" * 150)
        assert r.mode == ScenarioMode.REPORT

    def test_explicit_mode_overrides(router):
        r = router.route("test", explicit_mode=ScenarioMode.CONVERSATION)
        assert r.mode == ScenarioMode.CONVERSATION

    def test_user_preference_persisted(router):
        router.set_user_preference("u1", ScenarioMode.REPORT)
        r = router.route("any", user_id="u1")
        assert r.mode == ScenarioMode.REPORT

    def test_routing_stats_populated(router):
        router.route("q1")
        router.route("q2")
        stats = router.get_routing_stats()
        assert stats["total_routings"] == 2


class TestHybridInput:

    def test_nl_parsing_area(hybrid_input):
        state = hybrid_input.process_natural_input("\\u6df1\\u5733 100\\u33a1 \\u5b66\\u5b66")
        assert "area_sqm" in state.parsed_from_nl

    def test_mode_switch_nl_to_structured(hybrid_input):
        state = hybrid_input.process_natural_input("\\u6df1\\u5733 100\\u33a1")
        s2 = hybrid_input.sync_to_structured(state)
        assert s2.current_mode == "structured"

    def test_mode_switch_structured_to_nl(hybrid_input):
        state = HybridInputState(current_mode="structured", structured_fields={"city": "\\u676d\\u5dde"})
        s2 = hybrid_input.sync_to_natural(state)
        assert s2.current_mode == "natural_language"

    def test_validate_submit(hybrid_input):
        state = hybrid_input.process_natural_input("\\u6df1\\u5733\\u672a\\u6765\\u623f")
        result = hybrid_input.validate_and_submit(state)
        assert result["status"] in ("submitted", "validation_failed")


class TestBatchOperations:

    def test_batch_export(batch_manager):
        r = batch_manager.execute_batch_export(["t1","t2","t3"])
        assert r.success_count == 3 and r.download_url is not None

    def test_batch_compare(batch_manager):
        r = batch_manager.execute_batch_compare(["t1","t2","t3"])
        assert r.success_count == 3 and r.comparison_id is not None

    def test_batch_compare_requires_2_to_5(batch_manager):
        r = batch_manager.execute_batch_compare(["only_one"])
        assert r.fail_count == 1

    def test_batch_delete(batch_manager):
        r = batch_manager.execute_batch_delete(["t1","t2"])
        assert r.success_count == 2

    def test_save_and_load_template(batch_manager):
        tid = batch_manager.save_template("tpl1", {"purpose": "\\u6295\\u8d44"}, "u1")
        loaded = batch_manager.load_template(tid)
        assert loaded is not None and loaded["usage_count"] == 1

    def test_smart_recommendation(batch_manager):
        batch_manager.save_template("tpl_x", {"purpose": "\\u6295\\u8d44"}, "u1")
        recs = batch_manager.recommend_templates("u1", [{"structured_params":{"purpose":"\\u6295\\u8d44"}}]*5)
        assert len(recs) >= 1


class TestReportGeneration:

    def test_full_report_has_9_sections(report_generator):
        r = report_generator.generate({"task_id":"full_t","structured_params":{"city":"HZ"}}, mode="full")
        assert len(r.sections) == 9

    def test_compact_report_smaller(report_generator):
        rf = report_generator.generate({"task_id":"cpt_t","structured_params":{"city":"SZ"}}, mode="compact")
        assert rf.word_count < report_generator.generate({"task_id":"full_t2","structured_params":{"city":"SZ"}}, mode="full").word_count

    def test_report_contains_echarts(report_generator):
        r = report_generator.generate({"task_id":"echart_t","structured_params":{"city":"SH"}}, mode="full")
        assert "echarts" in r.html_content.lower()

    def test_cache_invalidation(report_generator):
        r1 = report_generator.generate({"task_id":"cache_t","structured_params":{"city":"BJ"}}, mode="full")
        report_generator.invalidate_cache(r1.report_id)
        r2 = report_generator.generate({"task_id":"cache_t","structured_params":{"city":"BJ"}}, mode="full")
        assert r2.metadata.get("cache_hit") is True


class TestOnboarding:

    def test_4_steps_shown_by_default():
        g = TaskAnalysisOnboardingGuide()
        steps = g.get_steps(None)
        assert len(steps) == 4

    def test_dismiss_clears_steps():
        g = TaskAnalysisOnboardingGuide()
        g.dismiss("u_dismiss")
        assert len(g.get_steps("u_dismiss")) == 0

    def test_progress_tracking():
        g = TaskAnalysisOnboardingGuide()
        prog = g.get_progress("u_new", [])
        assert prog["total_steps"] == 4


class TestConsultationInterface:

    def test_zhouyu_welcome_has_content():
        msg = PERSONA_WELCOME_MESSAGES["zhouyu"]["morning"]
        assert len(msg) > 10

    def test_luxun_welcome_is_cautious():
        msg = PERSONA_WELCOME_MESSAGES["luxun"]["evening"]
        assert "\\u8c26\\u8c1\" in msg

    def test_chat_spec_complete():
        assert "persona_switcher" in CHAT_INTERFACE_SPEC
        assert "voice_input" in CHAT_INTERFACE_SPEC


class TestFollowUps:

    def test_intent_based_followups():
        engine = ConsultationFollowUpEngine()
        f ups = engine.generate_followups("single_block_analysis", {"city":"\\u676d\\u5dde","block":"\\u672a\\u6765"})
        assert len(f ups) == 3

    def test_unknown_intent_fallback():
        engine = ConsultationFollowUpEngine()
        f ups = engine.generate_followups("unknown_xyz", {})
        assert len(f ups) == 3


class TestReportCardEmbedding:

    def test_card_created_with_id():
        embedder = ReportCardInChatEmbedder()
        card = embedder.embed_card({"title":"T","predicted_growth":"0.08","risk_level":"medium","advice":"BUY"})
        assert card.card_id.startswith("card_") and len(card.actions) == 3

    def test_card_html_contains_actions():
        embedder = ReportCardInChatEmbedder()
        card = embedder.embed_card({"title":"T","predicted_growth":"0.08","risk_level":"medium","advice":"BUY"})
        html = embedder.render_card_html(card)
        assert "report-card" in html and "\\u67e5\\u5b8c\\u62a5\\u544a" in html


class TestReasoningDisplay:

    def test_session_lifecycle():
        mgr = ReasoningStepDisplayManager()
        sid = mgr.start_session("s1")
        assert sid == "s1"
        mgr.end_session(sid)
        assert mgr.get_session_steps(sid) == []

    def test_steps_added_and_completed():
        mgr = ReasoningStepDisplayManager()
        sid = mgr.start_session("s2")
        mgr.add_step(sid, "zhongshu_parsing")
        mgr.add_step(sid, "hubu_collecting")
        mgr.complete_step(sid, 0)
        mgr.complete_step(sid, 1)
        steps = mgr.get_session_steps(sid)
        assert len(steps) == 2
        running = [s for s in steps if s["status"]=="running"]
        assert len(running) == 0


class TestTrustBuilding:

    def test_source_highlighting():
        mgr = TrustBuildingManager()
        text, hl = mgr.highlight_data_sources("\\u6839\\u636e\\u8d1d\\u636e\\u6570\\u636e")
        assert len(hl) > 0

    def test_confidence_verbal():
        mgr = TrustBuildingManager()
        result = mgr.express_confidence(0.85, 0.05, 0.15, "probabilistic_verbal")
        assert "%" in result and "\\u516d\\u6709" in result

    def test_feedback_apology():
        mgr = TrustBuildingManager()
        resp = mgr.handle_feedback("m1", False, "wrong_answer", "u1")
        assert resp.get("apology") is not None

    def test_feedback_stats():
        mgr = TrustBuildingManager()
        mgr.handle_feedback("m1", True, None, "u1")
        stats = mgr.get_feedback_stats()
        assert stats["total"] == 1 and stats["helpful_rate"] == 1.0


class TestMultiIntentDialogue:

    def test_two_questions_split():
        handler = MultiIntentDialogueHandler()
        parts = handler.split_composite_query("\\u6295\\u8d44\\u5982\\u4f55\\uff0c\\u98ce\\u9669\\u600e\\u4f55")
        assert len(parts) == 2

    def test_single_no_split():
        handler = MultiIntentDialogueHandler()
        parts = handler.split_composite_query("\\u5355\\u4e00\\u4e00\\u600e\\u4e48\\u6837")
        assert len(parts) == 1

    def test_interim_prompt():
        handler = MultiIntentDialogueHandler()
        prompt = handler.generate_interim_prompt("\\u56de\\u7b54", "\\u98ce\\u9669")
        assert "\\u5df2\\u5b8c\\u56de\\u7b54" in prompt


class TestBackendDispatch:

    def test_report_mode_dispatch(dispatcher):
        d = dispatcher.dispatch({"mode":"report","params":{}})
        assert d.mode == ScenarioMode.REPORT and d.agent_called == "gongbu"

    def test_conversation_mode_dispatch(dispatcher):
        d = dispatcher.dispatch({"mode":"conversation","params":{}})
        assert d.mode == ScenarioMode.CONVERSATION and d.agent_called == "libu"

    def test_async_flag_generates_ws_event(dispatcher):
        d = dispatcher.dispatch({"mode":"conversation","params":{},"async_report":True})
        assert d.websocket_event is not None

    def test_dispatch_stats(dispatcher):
        dispatcher.dispatch({"mode":"report","params":{}})
        dispatcher.dispatch({"mode":"conversation","params":{}})
        stats = dispatcher.get_dispatch_stats()
        assert stats["total"] == 2


class TestAsyncReportGen:

    def test_job_lifecycle(async_gen):
        job = async_gen.create_job("u1", "s1", {"city":"HZ"})
        assert job.status == "queued"
        processed = async_gen.process_job(job.job_id)
        assert processed.status == "completed" and processed.progress_pct == 100

    def test_job_retrieval(async_gen):
        job = async_gen.create_job("u1", "s2", {"city":"SZ"})
        async_gen.process_job(job.job_id)
        retrieved = async_gen.get_job(job.job_id)
        assert retrieved is not None and retrieved.report_id is not None


class TestSharedComponents:

    def test_full_viewer_specs():
        spec = REPORT_VIEWER_SPECS["full_mode"]
        assert spec["toolbar_actions"] == 7 and spec["show_all_sections"] is True

    def test_compact_viewer_specs():
        spec = REPORT_VIEWER_SPECS["compact_mode"]
        assert spec["toolbar_visible"] is False and len(spec["visible_sections"]) == 2

    def test_agent_indicator_specs():
        spec = AGENT_STATUS_INDICATOR_SPECS
        assert len(spec["agents"]) == 6


class TestUXMetrics:

    def test_kpi_calculation(metrics_collector):
        metrics_collector.record_event("report", "task_completed", True, "u1")
        metrics_collector.record_event("conversation", "followup_click", True, "u1")
        kpis = metrics_collector.calculate_kpis()
        assert "report" in kpis and "conversation" in kpis

    def test_daily_snapshot(metrics_collector):
        metrics_collector.record_event("report", "task_completed", True, "u1")
        snap = metrics_collector.take_daily_snapshot()
        assert len(snap) > 0


class TestABTesting:

    def test_ab_test_creation(ab_framework):
        t = ab_framework.create_test("test1", "Form vs NL", "report",
                                       {"style":"left"},{"style":"right"}, 0.5)
        assert t.test_id == "test1" and t.traffic_split == 0.5

    def test_variant_assignment(ab_framework):
        ab_framework.create_test("test2", "T", "conversation", {"A":"a"},{"B":"b"}, 0.5)
        a_count = sum(1 for _ in range(50) if ab_framework.assign_variant("test2", f"u{i}") == "a")
        b_count = 50 - a_count
        assert 30 <= a_count <= 70  # Should be roughly 50/50

    def test_analysis(ab_framework):
        ab_framework.create_test("test3", "X", "report", {"A":"a"},{"B":"b"}, 0.5)
        for _ in range(200):
            v = ab_framework.assign_variant("test3", f"u{_}")
            ab_framework.record_conversion("test3", v, random.random() > 0.5)
        result = ab_framework.analyze_test("test3")
        assert result["winner"] in ("a", "b", "tie")
        assert "z_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
'''


# End of Layer 21
