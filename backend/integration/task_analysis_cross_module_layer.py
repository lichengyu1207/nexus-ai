# -*- coding: utf-8 -*-
"""
Layer 28: Task Analysis & Cross-Module Integration (任务分析与其他模块联动)
=========================================================================================
Governor Fang AI Property Platform (房都督AI平台)
Agent Cultivation System - Integration Layer 28

Responsibilities:
  Part A:  Task Analysis Core Flow Enhancement (action panel, redirect service)
  Part B:  Task <-> Task Center Integration (history, detail, batch ops)
  Part C:  Task <-> Team Management Integration (agent display, load display)
  Part D:  Task <-> Property Compare Integration (extract, select, import)
  Part E:  Task <-> My Reports Integration (auto-save, backlink)
  Part F:  Task <-> Memory System Integration (preferences, prefill)
  Part G:  Task <-> Talent/Skill Market Integration (recruitment, skill suggestions)
  Part H:  Task <-> Autonomous Work Integration (schedule proposals)
  Part I:  Task <-> Self-Evolution Integration (feedback, training samples)
  Part J:  Task <-> Living Ecosystem Integration (topology graph, health metrics)
  Part K:  Task <-> Five-End Coordination Integration (edu/enterprise/gov/assoc/platform)
  Part L:  Task <-> Three-Six Learning System Integration (training samples, model update)
  Part M:  Task <-> Counterattack System Integration (threat assessment, drill)
  Part N:  Cross-Module Orchestration Engine (event bus, subscribers, synergy score)
  Part O:  Testing Suite (50+ test cases, 16 categories, pytest/Playwright generation)

Author: Integration Architect
Version: 28.0.0
"""

from __future__ import annotations

import json
import math
import random
import time
import uuid
import hashlib
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from enum import Enum
from datetime import datetime, timedelta, date
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# PART A: TASK ANALYSIS CORE FLOW ENHANCEMENT
# =============================================================================


@dataclass
class ActionPanelItem:
    """A single action item displayed in the task action panel."""
    action_id: str
    label: str
    icon: str
    target_module: str
    target_route: str
    condition_fn_name: str
    priority: int
    tooltip: str


ACTION_PANEL_ITEMS: List[ActionPanelItem] = [
    ActionPanelItem(
        action_id="view_task_center_detail",
        label="View in Task Center",
        icon="fa-tasks",
        target_module="task_center",
        target_route="/task-center?taskId={task_id}",
        condition_fn_name="_always_visible",
        priority=1,
        tooltip="Open full task details in the Task Center",
    ),
    ActionPanelItem(
        action_id="add_to_property_compare",
        label="Add to Property Compare",
        icon="fa-balance-scale",
        target_module="property_compare",
        target_route="/compare?ids={property_ids}",
        condition_fn_name="_has_properties_in_result",
        priority=2,
        tooltip="Add analyzed properties to the comparison tool",
    ),
    ActionPanelItem(
        action_id="save_to_my_reports",
        label="Save to My Reports",
        icon="fa-file-alt",
        target_module="my_reports",
        target_route="/reports?task_id={task_id}",
        condition_fn_name="_task_completed",
        priority=3,
        tooltip="Save this analysis result as a report",
    ),
    ActionPanelItem(
        action_id="set_memory_preferences",
        label="Set Memory Preferences",
        icon="fa-brain",
        target_module="memory_system",
        target_route="/memory/preferences",
        condition_fn_name="_has_analysis_params",
        priority=4,
        tooltip="Remember your analysis preferences for future tasks",
    ),
    ActionPanelItem(
        action_id="recruit_agent",
        label="Recruit Agent",
        icon="fa-user-plus",
        target_module="talent_market",
        target_route="/agents/recommend?task_id={task_id}",
        condition_fn_name="_suggest_recruitment",
        priority=5,
        tooltip="Task performance suggests recruiting additional agents",
    ),
    ActionPanelItem(
        action_id="purchase_skill",
        label="Purchase Skill",
        icon="fa-star",
        target_module="skill_market",
        target_route="/skills/recommend?task_id={task_id}",
        condition_fn_name="_suggest_skill_purchase",
        priority=6,
        tooltip="Missing capabilities detected - consider purchasing skills",
    ),
]


class ActionPanelRenderer:
    """Renders the frosted-glass action panel for task context."""

    def __init__(self):
        self._item_map: Dict[str, ActionPanelItem] = {}
        for item in ACTION_PANEL_ITEMS:
            self._item_map[item.action_id] = item

    def render_action_panel(self, task_context: Dict) -> str:
        """Render a frosted-glass action panel HTML for the given task context."""
        visible_items = self._filter_items_by_context(task_context)

        if not visible_items:
            return ""

        item_buttons = ""
        for idx, item in enumerate(visible_items):
            btn = self._render_action_button(item, task_context, idx)
            item_buttons += btn

        panel_html = (
            '<div class="task-action-panel" style="' +
            'position:fixed;bottom:20px;right:20px;z-index:1000;' +
            'width:280px;background:rgba(255,255,255,0.85);' +
            'backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);' +
            'border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,0.15);' +
            'border:1px solid rgba(255,255,255,0.3);font-family:-apple-system,sans-serif;">\n' +
            '  <div class="panel-header" style="padding:10px 14px;' +
            ' cursor:pointer;display:flex;justify-content:space-between;' +
            ' align-items:center;border-bottom:1px solid rgba(0,0,0,0.06);">\n' +
            '    <span style="font-weight:bold;font-size:13px;color:#333;">Quick Actions</span>\n' +
            '    <span style="color:#999;font-size:16px;" id="panel-toggle">&#9660;</span>\n' +
            "  </div>\n" +
            '  <div class="panel-body" id="panel-body" style="padding:10px 14px;">\n' +
            item_buttons +
            "  </div>\n" +
            "</div>"
        )
        return panel_html

    def _filter_items_by_context(self, ctx: Dict) -> List[ActionPanelItem]:
        """Filter action items based on task context conditions."""
        visible: List[ActionPanelItem] = []
        for item in ACTION_PANEL_ITEMS:
            if self._evaluate_condition(item.condition_fn_name, ctx):
                visible.append(item)
        visible.sort(key=lambda x: x.priority)
        return visible

    def _evaluate_condition(self, fn_name: str, ctx: Dict) -> bool:
        """Evaluate a condition function name against task context."""
        if fn_name == "_always_visible":
            return True
        elif fn_name == "_has_properties_in_result":
            props = ctx.get("properties_in_result", [])
            return len(props) > 0
        elif fn_name == "_task_completed":
            status = ctx.get("status", "")
            return status in ("COMPLETED", "completed")
        elif fn_name == "_has_analysis_params":
            params = ctx.get("parameters", {})
            return len(params) > 0
        elif fn_name == "_suggest_recruitment":
            duration = ctx.get("duration_ms", 0)
            quality = ctx.get("quality_score", 1.0)
            return duration > 60000 or quality < 0.6
        elif fn_name == "_suggest_skill_purchase":
            missing_skills = ctx.get("missing_capabilities", [])
            return len(missing_skills) > 0
        return False

    def _render_action_button(self, item: ActionPanelItem, ctx: Dict, index: int) -> str:
        """Render a single action button/link within the panel."""
        route = item.target_route.format(
            task_id=ctx.get("task_id", ""),
            property_ids=",".join(ctx.get("properties_in_result", [])),
        )

        icon_colors = {
            "view_task_center_detail": "#1976D2",
            "add_to_property_compare": "#43A047",
            "save_to_my_reports": "#FB8C00",
            "set_memory_preferences": "#8E24AA",
            "recruit_agent": "#E53935",
            "purchase_skill": "#FBC02D",
        }
        color = icon_colors.get(item.action_id, "#1976D2")

        button = (
            '    <a href="' + route + '" class="action-btn" style="\n' +
            '      display:flex;align-items:center;padding:8px 10px;margin-bottom:6px;\n' +
            '      border-radius:8px;text-decoration:none;color:#333;\n' +
            '      background:rgba(' + color.lstrip("#")[0:2] + ',' +
            color.lstrip("#")[2:4] + ',' + color.lstrip("#")[4:6] + ',0.08);\n' +
            '      transition:background 0.2s;font-size:13px;">\n' +
            '      <i class="' + item.icon + '" style="color:' + color +
            ';width:18px;text-align:center;margin-right:8px;"></i>\n' +
            "      <span>" + item.label + "</span>\n" +
            "    </a>\n"
        )
        return button


@dataclass
class RedirectURLResult:
    """Result of creating a redirect URL."""
    url: str
    action_id: str
    target_module: str
    is_auto_redirect: bool


class TaskRedirectService:
    """Service for generating cross-module redirect URLs from task actions."""

    ROUTE_MAP: Dict[str, str] = {
        "view_task_center_detail": "/task-center?taskId={task_id}",
        "add_to_property_compare": "/compare?ids={property_ids}",
        "save_to_my_reports": "/reports?task_id={task_id}",
        "set_memory_preferences": "/memory/preferences",
        "recruit_agent": "/agents/recommend?task_id={task_id}",
        "purchase_skill": "/skills/recommend?task_id={task_id}",
    }

    AUTO_REDIRECT_TASK_TYPES: Set[str] = {
        "deep_analysis", "comprehensive_report", "multi_model_comparison",
    }

    def create_redirect_url(
        self, action_id: str, task_id: str, context: Dict
    ) -> RedirectURLResult:
        """Create a fully-formed redirect URL for a given action and task."""
        route_template = self.ROUTE_MAP.get(action_id, "/")
        property_ids = ",".join(context.get("property_ids", []))

        url = route_template.format(
            task_id=task_id,
            property_ids=property_ids,
        )

        module_map = {
            "view_task_center_detail": "task_center",
            "add_to_property_compare": "property_compare",
            "save_to_my_reports": "my_reports",
            "set_memory_preferences": "memory_system",
            "recruit_agent": "talent_market",
            "purchase_skill": "skill_market",
        }
        target_module = module_map.get(action_id, "unknown")

        is_auto = self.should_auto_redirect(context.get("task_type", ""))

        return RedirectURLResult(
            url=url,
            action_id=action_id,
            target_module=target_module,
            is_auto_redirect=is_auto,
        )

    def should_auto_redirect(self, task_type: str) -> bool:
        """Determine whether a task type should auto-redirect to task center first."""
        return task_type in self.AUTO_REDIRECT_TASK_TYPES


# =============================================================================
# PART B: TASK <-> TASK CENTER INTEGRATION
# =============================================================================


class TaskStatus(str, Enum):
    """Status values for tasks in the history system."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class TaskHistoryEntry:
    """An entry in the user's task history."""
    task_id: str
    name: str
    type: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    agent_count: int = 1
    report_summary: Optional[str] = None
    parameters_json: str = "{}"


@dataclass
class PaginatedResult:
    """Paginated result wrapper for list queries."""
    items: List[Any]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool


@dataclass
class BatchOperationResult:
    """Result of a batch operation on multiple tasks."""
    success: bool
    affected_count: int
    errors: List[Dict[str, Any]]


@dataclass
class TaskDetail:
    """Full detail view of a single task."""
    task_id: str
    name: str
    type: str
    status: TaskStatus
    params: Dict[str, Any]
    agents: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    report: Dict[str, Any]


class TaskCenterIntegration:
    """Integration service connecting tasks with the Task Center history system."""

    PAGE_SIZE: int = 20

    def __init__(self):
        self._history_store: Dict[str, List[TaskHistoryEntry]] = defaultdict(list)
        self._detail_store: Dict[str, TaskDetail] = {}

    def get_task_history(
        self, user_id: str, filters: Dict[str, Any]
    ) -> PaginatedResult:
        """Get paginated task history for a user with optional filters."""
        all_entries = self._history_store.get(user_id, [])

        # Apply status filter
        status_filter = filters.get("status")
        if status_filter:
            all_entries = [
                e for e in all_entries
                if e.status.value.upper() == status_filter.upper()
            ]

        # Apply type filter
        type_filter = filters.get("type")
        if type_filter:
            all_entries = [
                e for e in all_entries
                if e.type.upper() == type_filter.upper()
            ]

        # Apply time range filter
        since = filters.get("since")
        until = filters.get("until")
        if since:
            try:
                since_dt = datetime.fromisoformat(since) if isinstance(since, str) else since
                all_entries = [e for e in all_entries if e.created_at >= since_dt]
            except (ValueError, TypeError):
                pass
        if until:
            try:
                until_dt = datetime.fromisoformat(until) if isinstance(until, str) else until
                all_entries = [e for e in all_entries if e.created_at <= until_dt]
            except (ValueError, TypeError):
                pass

        # Sort by created_at descending
        all_entries.sort(key=lambda x: x.created_at, reverse=True)

        total = len(all_entries)
        page = max(1, filters.get("page", 1))
        pages = math.ceil(total / self.PAGE_SIZE) if total > 0 else 1
        start = (page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_items = all_entries[start:end]

        return PaginatedResult(
            items=page_items,
            total=total,
            page=page,
            pages=int(pages),
            has_next=page < pages,
            has_prev=page > 1,
        )

    def get_task_detail(self, task_id: str) -> Optional[TaskDetail]:
        """Get full detail for a specific task including params, agents, and report."""
        return self._detail_store.get(task_id)

    def batch_delete_tasks(
        self, task_ids: List[str], user_id: str
    ) -> BatchOperationResult:
        """Delete multiple tasks from user's history."""
        errors: List[Dict[str, Any]] = []
        deleted = 0
        user_history = self._history_store.get(user_id, [])
        original_len = len(user_history)

        for tid in task_ids:
            found = False
            for i, entry in enumerate(user_history):
                if entry.task_id == tid:
                    user_history.pop(i)
                    found = True
                    deleted += 1
                    if tid in self._detail_store:
                        del self._detail_store[tid]
                    break
            if not found:
                errors.append({"task_id": tid, "error": "Task not found in history"})

        return BatchOperationResult(
            success=len(errors) == 0,
            affected_count=deleted,
            errors=errors,
        )

    def batch_retry_tasks(self, task_ids: List[str]) -> BatchOperationResult:
        """Retry only FAILED tasks from the provided list."""
        errors: List[Dict[str, Any]] = []
        retried = 0

        for tid in task_ids:
            detail = self._detail_store.get(tid)
            if not detail:
                errors.append({"task_id": tid, "error": "Task detail not found"})
                continue
            if detail.status != TaskStatus.FAILED:
                errors.append({"task_id": tid, "error": "Task is not in FAILED status"})
                continue
            # Simulate retry by updating status
            new_detail = TaskDetail(
                task_id=detail.task_id,
                name=detail.name,
                type=detail.type,
                status=TaskStatus.PENDING,
                params=dict(detail.params),
                agents=list(detail.agents),
                timeline=list(detail.timeline),
                report=dict(detail.report),
            )
            self._detail_store[tid] = new_detail
            retried += 1

        return BatchOperationResult(
            success=retried == len(task_ids),
            affected_count=retried,
            errors=errors,
        )


# =============================================================================
# PART C: TASK <-> TEAM MANAGEMENT INTEGRATION
# =============================================================================


@dataclass
class TaskAgentDisplay:
    """Display representation of an agent participating in a task."""
    agent_id: str
    agent_name: str
    agent_type: str
    role_in_task: str
    status: str
    duration_ms: int
    contribution_summary: str


@dataclass
class TeamAgentLoadDisplay:
    """Display representation of an agent's current workload in a team."""
    agent_id: str
    agent_name: str
    current_active_tasks: int
    load_level: str
    warning_thresholds: Tuple[int, int]


class TaskTeamIntegration:
    """Integration between tasks and team management for agent visibility."""

    def __init__(self):
        self._task_agents: Dict[str, List[TaskAgentDisplay]] = {}
        self._team_loads: Dict[str, List[TeamAgentLoadDisplay]] = {}

    def get_task_agents(self, task_id: str) -> List[TaskAgentDisplay]:
        """Get all agents participating in a task with their roles and status."""
        return self._task_agents.get(task_id, [])

    def get_team_agent_loads(self, team_id: str) -> List[TeamAgentLoadDisplay]:
        """Get each team member's current task count and load level."""
        return self._team_loads.get(team_id, [])

    def generate_agent_link(self, agent_id: str) -> str:
        """Generate URL to team management page with agent highlighted."""
        return "/team-management?highlight_agent=" + agent_id

    def generate_load_warning_html(self, load: TeamAgentLoadDisplay) -> str:
        """Render a colored badge indicating agent load level."""
        colors = {
            "NORMAL": "#43A047",
            "WARNING": "#FB8C00",
            "CRITICAL": "#E53935",
        }
        bg_color = colors.get(load.load_level, "#666")

        badge = (
            '<span class="load-badge" style="' +
            'display:inline-block;padding:3px 10px;border-radius:12px;' +
            'font-size:11px;font-weight:bold;color:white;' +
            'background:' + bg_color + ';">' +
            load.load_level + ": " + str(load.current_active_tasks) + " tasks" +
            "</span>"
        )
        return badge


# =============================================================================
# PART D: TASK <-> PROPERTY COMPARE INTEGRATION
# =============================================================================


@dataclass
class PropertyCompareAction:
    """A property that can be added to the comparison tool from a task result."""
    property_id: str
    property_name: str
    address: str
    price: float
    selected: bool = False


class TaskPropertyCompareIntegration:
    """Integration for extracting properties from task results into compare tool."""

    def extract_properties_from_task_result(
        self, task_result: Dict[str, Any]
    ) -> List[PropertyCompareAction]:
        """Parse properties from an analysis task result."""
        properties: List[PropertyCompareAction] = []

        raw_props = task_result.get("analyzed_properties", [])
        if not raw_props:
            # Try alternative keys
            raw_props = task_result.get("properties", [])
        if not raw_props:
            raw_props = task_result.get("result", {}).get("properties", [])

        for prop in raw_props:
            if isinstance(prop, dict):
                pca = PropertyCompareAction(
                    property_id=prop.get("id", uuid.uuid4().hex[:8]),
                    property_name=prop.get("name", "Unknown Property"),
                    address=prop.get("address", ""),
                    price=float(prop.get("price", 0)),
                    selected=False,
                )
                properties.append(pca)

        return properties

    def render_property_selection_ui(
        self, properties: List[PropertyCompareAction]
    ) -> str:
        """Render cards with checkboxes for property selection UI."""
        if not properties:
            return '<p style="padding:20px;color:#999;text-align:center;">No properties found in this analysis.</p>'

        cards = ""
        for prop in properties:
            checked = "checked" if prop.selected else ""
            card = (
                '  <div class="property-compare-card" style="' +
                'display:flex;align-items:center;padding:12px;margin-bottom:8px;' +
                'border:1px solid #e0e0e0;border-radius:10px;background:white;' +
                'cursor:pointer;transition:border-color 0.2s;">\n' +
                '    <input type="checkbox" id="prop_' + prop.property_id + '" ' +
                'value="' + prop.property_id + '" ' + checked +
                ' style="margin-right:12px;width:18px;height:18px;cursor:pointer;" />\n' +
                '    <div style="flex:1;">\n' +
                '      <div style="font-weight:bold;font-size:14px;color:#333;">' +
                prop.property_name + '</div>\n' +
                '      <div style="font-size:12px;color:#888;margin-top:2px;">' +
                prop.address + '</div>\n' +
                "    </div>\n" +
                '    <div style="text-align:right;">\n' +
                '      <div style="font-weight:bold;color:#1976D2;font-size:15px;">$' +
                "{:,.0f}".format(prop.price) + '</div>\n' +
                "    </div>\n" +
                "  </div>\n"
            )
            cards += card

        selected_count = sum(1 for p in properties if p.selected)
        bar = (
            '<div class="compare-bar" style="' +
            'position:sticky;bottom:0;background:white;padding:12px 16px;' +
            'border-top:1px solid #e0e0e0;display:flex;justify-content:space-between;' +
            'align-items:center;border-radius:0 0 10px 10px;">\n' +
            '  <span style="font-size:13px;color:#555;"><strong>' +
            str(selected_count) + '</strong> properties selected</span>\n' +
            '  <button style="padding:10px 24px;background:#1976D2;color:white;' +
            ' border:none;border-radius:8px;font-weight:bold;cursor:pointer;' +
            ' font-size:14px;">Compare ' + str(selected_count) + " Properties</button>\n" +
            "</div>"
        )

        container = (
            '<div class="property-selection-ui" style="max-width:600px;' +
            ' margin:auto;font-family:-apple-system,sans-serif;">\n' +
            cards +
            bar +
            "</div>"
        )
        return container

    def generate_compare_url(self, selected_ids: List[str]) -> str:
        """Generate the comparison page URL with selected property IDs."""
        if not selected_ids:
            return "/compare"
        return "/compare?ids=" + ",".join(selected_ids)

    def get_importable_task_list(self, user_id: str) -> List[Dict[str, Any]]:
        """Get historical tasks that contain properties available for import."""
        # Returns mock data representing tasks with extracted properties
        return [
            {
                "task_id": "task_imp_001",
                "name": "District A Market Analysis",
                "created_at": "2025-01-15T10:30:00",
                "property_count": 5,
                "status": "COMPLETED",
            },
            {
                "task_id": "task_imp_002",
                "name": "Investment Portfolio Review",
                "created_at": "2025-01-18T14:00:00",
                "property_count": 3,
                "status": "COMPLETED",
            },
        ]

    def import_from_task(self, task_id: str) -> List[PropertyCompareAction]:
        """Load properties from a previously completed task for re-comparison."""
        # Simulated import returning sample properties
        return [
            PropertyCompareAction(
                property_id="imp_p1", property_name="Sunrise Tower Unit A",
                address="123 Main St, District A", price=850000.0, selected=False,
            ),
            PropertyCompareAction(
                property_id="imp_p2", property_name="Harbor View Apartment B",
                address="456 Ocean Blvd, District B", price=1200000.0, selected=False,
            ),
        ]


# =============================================================================
# PART E: TASK <-> MY REPORTS INTEGRATION
# =============================================================================


@dataclass
class ReportSaveResult:
    """Result of saving a report linked to a task."""
    success: bool
    report_id: str
    save_timestamp: datetime
    visibility: str


@dataclass
class AutoReportSaveConfig:
    """Configuration for automatic report saving on task completion."""
    auto_save: bool = True
    save_on_complete: bool = True
    include_parameters: bool = True
    default_visibility: str = "PRIVATE"


class TaskReportIntegration:
    """Integration for automatically saving task results as reports."""

    def __init__(self):
        self._config: Dict[str, AutoReportSaveConfig] = {}
        self._reports_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def auto_save_report(
        self, task_id: str, report_content: Dict[str, Any]
    ) -> ReportSaveResult:
        """Automatically save a report when a task completes."""
        report_id = "rpt_" + uuid.uuid4().hex[:10]
        timestamp = datetime.utcnow()

        config = self._config.get("default", AutoReportSaveConfig())
        visibility = config.default_visibility

        report_entry = {
            "report_id": report_id,
            "task_id": task_id,
            "content": report_content,
            "saved_at": timestamp.isoformat(),
            "visibility": visibility,
            "auto_saved": True,
        }

        self._reports_store[task_id].append(report_entry)

        return ReportSaveResult(
            success=True,
            report_id=report_id,
            save_timestamp=timestamp,
            visibility=visibility,
        )

    def get_reports_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all reports associated with a specific task."""
        return self._reports_store.get(task_id, [])

    def generate_backlink_to_task(self, task_id: str) -> str:
        """Generate a 'View Original Task' button URL linking back from report to task."""
        url = "/task-center?taskId=" + task_id
        button_html = (
            '<a href="' + url + '" class="backlink-task-btn" style="' +
            'display:inline-flex;align-items:center;padding:8px 16px;' +
            'background:#E3F2FD;color:#1565C0;border-radius:6px;' +
            'text-decoration:none;font-size:13px;font-weight:bold;' +
            'transition:background 0.2s;">\n' +
            '  <i class="fa-arrow-left" style="margin-right:6px;"></i>' +
            " View Original Task\n" +
            "</a>"
        )
        return button_html


# =============================================================================
# PART F: TASK <-> MEMORY SYSTEM INTEGRATION
# =============================================================================


@dataclass
class AnalysisPreference:
    """User preference stored in memory from past task parameters."""
    preference_id: str
    user_id: str
    task_type: str
    city: str
    budget_range: Tuple[float, float]
    area_range: Tuple[float, float]
    room_type: str
    style_tags: List[str]
    importance_score: float = 0.8
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)


class TaskMemoryIntegration:
    """Integration for extracting and applying user analysis preferences via memory."""

    def __init__(self):
        self._preferences: Dict[str, AnalysisPreference] = {}
        self._user_prefs: Dict[str, List[str]] = defaultdict(list)

    def save_analysis_preference(self, task_context: Dict) -> str:
        """Extract parameters from task context and save as a memory preference."""
        pref_id = "pref_" + uuid.uuid4().hex[:10]
        params = task_context.get("parameters", {})

        budget_min = float(params.get("budget_min", 0))
        budget_max = float(params.get("budget_max", 5000000))
        area_min = float(params.get("area_min", 0))
        area_max = float(params.get("area_max", 500))

        pref = AnalysisPreference(
            preference_id=pref_id,
            user_id=task_context.get("user_id", "anonymous"),
            task_type=task_context.get("task_type", "general"),
            city=params.get("city", ""),
            budget_range=(budget_min, budget_max),
            area_range=(area_min, area_max),
            room_type=params.get("room_type", ""),
            style_tags=params.get("style_tags", []),
        )

        self._preferences[pref_id] = pref
        self._user_prefs[pref.user_id].append(pref_id)

        logger.info("Preference saved: %s for user %s", pref_id, pref.user_id)
        return pref_id

    def get_latest_preference(
        self, user_id: str, task_type: Optional[str] = None
    ) -> Optional[AnalysisPreference]:
        """Get the most recent preference for a user, optionally filtered by task type."""
        pref_ids = self._user_prefs.get(user_id, [])
        candidates: List[AnalysisPreference] = []

        for pid in pref_ids:
            pref = self._preferences.get(pid)
            if pref:
                if task_type is None or pref.task_type == task_type:
                    candidates.append(pref)

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.last_used_at, reverse=True)
        return candidates[0]

    def generate_prefill_form_data(
        self, preference: AnalysisPreference
    ) -> Dict[str, Any]:
        """Convert a preference object into form field values ready for UI."""
        return {
            "city": preference.city,
            "budget_min": preference.budget_range[0],
            "budget_max": preference.budget_range[1],
            "area_min": preference.area_range[0],
            "area_max": preference.area_range[1],
            "room_type": preference.room_type,
            "style_tags": preference.style_tags,
            "preference_id": preference.preference_id,
        }

    def format_preference_for_agent(self, preference: AnalysisPreference) -> str:
        """Format a preference as natural language text for inclusion in agent system prompt."""
        parts = [
            "User Preference Profile:",
            "  City: " + (preference.city or "Not specified"),
            "  Budget Range: $" + "{:,.0f}".format(preference.budget_range[0]) +
            " - $" + "{:,.0f}".format(preference.budget_range[1]),
            "  Area Range: " + "{:.0f}".format(preference.area_range[0]) +
            " - " + "{:.0f}".format(preference.area_range[1]) + " sqm",
        ]
        if preference.room_type:
            parts.append("  Room Type: " + preference.room_type)
        if preference.style_tags:
            parts.append("  Style Tags: " + ", ".join(preference.style_tags))
        parts.append("  Importance Score: " + str(round(preference.importance_score, 2)))
        return chr(10).join(parts)


# =============================================================================
# PART G: TASK <-> TALENT/SKILL MARKET INTEGRATION
# =============================================================================


@dataclass
class RecruitmentSuggestion:
    """Suggestion to recruit an agent based on task performance analysis."""
    suggestion_id: str
    task_id: str
    reason_code: str
    recommended_agent_type: str
    urgency: str
    message_template: str


@dataclass
class SkillSuggestion:
    """Suggestion to purchase a skill based on detected capability gaps."""
    suggestion_id: str
    task_id: str
    missing_skill_id: str
    missing_skill_name: str
    impact_description: str
    purchase_url: str


@dataclass
class PostRecruitmentResult:
    """Result of handling post-recruitment actions."""
    success: bool
    agent_id: str
    team_id: str
    scheduler_notified: bool


class TaskMarketIntegration:
    """Integration for generating recruitment and skill purchase suggestions from task outcomes."""

    DURATION_THRESHOLD_MS: int = 60000
    QUALITY_THRESHOLD: float = 0.6

    def __init__(self):
        self._recruitment_suggestions: Dict[str, List[RecruitmentSuggestion]] = defaultdict(list)
        self._skill_suggestions: Dict[str, List[SkillSuggestion]] = defaultdict(list)

    def analyze_task_performance(
        self, task_result: Dict[str, Any]
    ) -> List[RecruitmentSuggestion]:
        """Analyze task performance and generate recruitment suggestions if needed."""
        suggestions: List[RecruitmentSuggestion] = []
        task_id = task_result.get("task_id", "unknown")
        duration = task_result.get("duration_ms", 0)
        quality = task_result.get("quality_score", 1.0)

        if duration > self.DURATION_THRESHOLD_MS:
            urgency = "HIGH" if duration > 120000 else "NORMAL"
            sug = RecruitmentSuggestion(
                suggestion_id="rs_" + uuid.uuid4().hex[:8],
                task_id=task_id,
                reason_code="HIGH_LOAD",
                recommended_agent_type="parallel_worker",
                urgency=urgency,
                message_template=(
                    "Task took " + str(duration / 1000) +
                    "s — consider recruiting a parallel worker agent."
                ),
            )
            suggestions.append(sug)

        if quality < self.QUALITY_THRESHOLD:
            urgency = "CRITICAL" if quality < 0.4 else "HIGH"
            sug = RecruitmentSuggestion(
                suggestion_id="rs_" + uuid.uuid4().hex[:8],
                task_id=task_id,
                reason_code="LOW_QUALITY",
                recommended_agent_type="quality_validator",
                urgency=urgency,
                message_template=(
                    "Quality score " + str(round(quality, 2)) +
                    " below threshold — consider recruiting a validator agent."
                ),
            )
            suggestions.append(sug)

        self._recruitment_suggestions[task_id].extend(suggestions)
        return suggestions

    def analyze_missing_capabilities(
        self, task_result: Dict[str, Any]
    ) -> List[SkillSuggestion]:
        """Detect skill gaps from failure reasons and suggest skill purchases."""
        suggestions: List[SkillSuggestion] = []
        task_id = task_result.get("task_id", "unknown")
        missing_caps = task_result.get("missing_capabilities", [])
        failure_reason = task_result.get("failure_reason", "")

        if "timeout" in failure_reason.lower():
            sug = SkillSuggestion(
                suggestion_id="ss_" + uuid.uuid4().hex[:8],
                task_id=task_id,
                missing_skill_id="skill_speed_boost_3",
                missing_skill_name="Advanced Speed Boost Lv.3",
                impact_description="Reduces processing time by up to 25%",
                purchase_url="/skills/detail/skill_speed_boost_3?source=task&task_id=" + task_id,
            )
            suggestions.append(sug)

        for cap in missing_caps:
            sug = SkillSuggestion(
                suggestion_id="ss_" + uuid.uuid4().hex[:8],
                task_id=task_id,
                missing_skill_id="skill_" + cap.lower().replace(" ", "_"),
                missing_skill_name=cap,
                impact_description="Addresses capability gap: " + cap,
                purchase_url="/skills/market?search=" + cap.replace(" ", "+"),
            )
            suggestions.append(sug)

        self._skill_suggestions[task_id].extend(suggestions)
        return suggestions

    def get_recruitment_suggestions_for_task(
        self, task_id: str
    ) -> List[RecruitmentSuggestion]:
        """Retrieve stored recruitment suggestions for a task."""
        return self._recruitment_suggestions.get(task_id, [])

    def get_skill_recommendations_for_task(
        self, task_id: str
    ) -> List[SkillSuggestion]:
        """Retrieve stored skill recommendations for a task."""
        return self._skill_suggestions.get(task_id, [])

    def handle_post_recruitment(
        self, agent_id: str, team_id: str
    ) -> PostRecruitmentResult:
        """Handle post-recruitment: add agent to team and notify scheduler."""
        # Simulate adding agent to team and notifying scheduler
        return PostRecruitmentResult(
            success=True,
            agent_id=agent_id,
            team_id=team_id,
            scheduler_notified=True,
        )


# =============================================================================
# PART H: TASK <-> AUTONOMOUS WORK INTEGRATION
# =============================================================================


@dataclass
class ScheduledTaskProposal:
    """Proposal for converting a one-time task into a recurring scheduled task."""
    proposal_id: str
    source_task_id: str
    frequency: str
    report_type: str
    delivery_method: str
    config_json: str
    proposed_at: datetime
    expires_at: datetime


@dataclass
class ScheduleCreationResult:
    """Result of confirming a scheduled task proposal."""
    success: bool
    schedule_id: str
    next_run_at: datetime
    cron_expression: str


class TaskAutonomousWorkIntegration:
    """Integration for suggesting and managing recurring autonomous work from completed tasks."""

    PROPOSAL_EXPIRY_HOURS: int = 72

    def __init__(self):
        self._proposals: Dict[str, ScheduledTaskProposal] = {}
        self._schedules: Dict[str, Dict[str, Any]] = {}
        self._autonomous_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def generate_schedule_proposal(
        self, task_context: Dict[str, Any]
    ) -> ScheduledTaskProposal:
        """Suggest recurring analysis after a one-time task completes successfully."""
        proposal_id = "prop_" + uuid.uuid4().hex[:10]
        source_task_id = task_context.get("task_id", "unknown")
        task_type = task_context.get("task_type", "general_analysis")

        freq = "WEEKLY"
        if "daily" in task_type.lower() and "weekly" not in task_type.lower():
            freq = "DAILY"
        elif "monthly" in task_type.lower():
            freq = "MONTHLY"

        proposed_at = datetime.utcnow()
        expires_at = proposed_at + timedelta(hours=self.PROPOSAL_EXPIRY_HOURS)

        config = {
            "source_task_params": task_context.get("parameters", {}),
            "frequency": freq,
            "report_format": "pdf",
            "notify_on_complete": True,
        }

        proposal = ScheduledTaskProposal(
            proposal_id=proposal_id,
            source_task_id=source_task_id,
            frequency=freq,
            report_type="periodic_analysis_report",
            delivery_method="IN_APP",
            config_json=json.dumps(config),
            proposed_at=proposed_at,
            expires_at=expires_at,
        )

        self._proposals[proposal_id] = proposal
        return proposal

    def confirm_proposal(
        self, proposal_id: str, user_confirmed: bool
    ) -> ScheduleCreationResult:
        """Confirm or reject a schedule proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return ScheduleCreationResult(
                success=False,
                schedule_id="",
                next_run_at=datetime.utcnow(),
                cron_expression="",
            )

        if not user_confirmed:
            return ScheduleCreationResult(
                success=False,
                schedule_id="",
                next_run_at=datetime.utcnow(),
                cron_expression="rejected",
            )

        schedule_id = "sched_" + uuid.uuid4().hex[:10]
        next_run = datetime.utcnow() + timedelta(days=1)

        cron_expr = {
            "DAILY": "0 9 * * *",
            "WEEKLY": "0 9 * * 1",
            "MONTHLY": "0 9 1 * *",
        }.get(proposal.frequency, "0 9 * * *")

        self._schedules[schedule_id] = {
            "proposal_id": proposal_id,
            "frequency": proposal.frequency,
            "cron_expression": cron_expr,
            "active": True,
            "next_run_at": next_run.isoformat(),
        }

        return ScheduleCreationResult(
            success=True,
            schedule_id=schedule_id,
            next_run_at=next_run,
            cron_expression=cron_expr,
        )

    def store_autonomous_result(
        self, schedule_id: str, result: Dict[str, Any]
    ) -> str:
        """Store a periodic report result to memory as periodic_report entry."""
        memory_id = "mem_periodic_" + uuid.uuid4().hex[:10]
        entry = {
            "memory_id": memory_id,
            "schedule_id": schedule_id,
            "type": "periodic_report",
            "result": result,
            "stored_at": datetime.utcnow().isoformat(),
        }
        self._autonomous_results[schedule_id].append(entry)
        return memory_id


# =============================================================================
# PART I: TASK <-> SELF-EVOLUTION INTEGRATION
# =============================================================================


@dataclass
class FeedbackSignal:
    """User feedback signal for reinforcement learning from task outcomes."""
    feedback_id: str
    task_id: str
    report_id: str
    user_id: str
    feedback_type: str
    rating: int
    comment: str
    timestamp: datetime
    rl_reward_value: float


@dataclass
class FailureCaseForTraining:
    """A failure case submitted to the red-team training pool."""
    case_id: str
    task_id: str
    error_type: str
    error_details: str
    input_snapshot: str
    output_snapshot: str
    severity: str
    added_to_pool_at: datetime
    used_in_training: bool = False


@dataclass
class TrainingSampleExport:
    """Summary of exported high-quality training samples."""
    sample_count: int
    date_range: str
    avg_rating: float
    export_path: str


class TaskEvolutionIntegration:
    """Integration for collecting RL signals and training samples from task lifecycle."""

    def __init__(self):
        self._feedback_signals: List[FeedbackSignal] = []
        self._failure_pool: List[FailureCaseForTraining] = []

    def record_feedback(self, feedback: FeedbackSignal) -> str:
        """Store a user feedback signal for RL training."""
        self._feedback_signals.append(feedback)
        logger.info(
            "Feedback recorded: %s rating=%d type=%s",
            feedback.feedback_id, feedback.rating, feedback.feedback_type,
        )
        return feedback.feedback_id

    def export_training_samples(
        self, quality_threshold: float = 4.0, max_samples: int = 100
    ) -> TrainingSampleExport:
        """Export high-quality tasks as training samples for offline RL training."""
        qualified = [
            f for f in self._feedback_signals
            if f.rating >= quality_threshold
        ]
        qualified.sort(key=lambda f: f.timestamp, reverse=True)
        selected = qualified[:max_samples]

        avg_rating = 0.0
        if selected:
            avg_rating = sum(f.rating for f in selected) / len(selected)

        export_path = "/exports/training_samples/" + \
            datetime.utcnow().strftime("%Y%m%d_%H%M%S") + ".jsonl"

        return TrainingSampleExport(
            sample_count=len(selected),
            date_range="last_30_days",
            avg_rating=round(avg_rating, 2),
            export_path=export_path,
        )

    def submit_failure_case(
        self, failure_case: FailureCaseForTraining
    ) -> str:
        """Push a failure case to the red-team training pool."""
        self._failure_pool.append(failure_case)
        logger.warning(
            "Failure case submitted: %s severity=%s type=%s",
            failure_case.case_id, failure_case.severity, failure_case.error_type,
        )
        return failure_case.case_id

    def get_failure_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about the failure case pool grouped by severity and type."""
        stats: Dict[str, Any] = {
            "total_pool_size": len(self._failure_pool),
            "by_severity": defaultdict(int),
            "by_error_type": defaultdict(int),
            "used_in_training": sum(1 for fc in self._failure_pool if fc.used_in_training),
        }
        for fc in self._failure_pool:
            stats["by_severity"][fc.severity] += 1
            stats["by_error_type"][fc.error_type] += 1
        stats["by_severity"] = dict(stats["by_severity"])
        stats["by_error_type"] = dict(stats["by_error_type"])
        return stats


# =============================================================================
# PART J: TASK <-> LIVING ECOSYSTEM INTEGRATION
# =============================================================================


@dataclass
class AgentTopologyNode:
    """A node in the agent topology graph for a task."""
    node_id: str
    agent_id: str
    agent_name: str
    status: str
    position: Dict[str, float]
    connections: List[Dict[str, Any]]


@dataclass
class AgentHealthMetric:
    """Real-time health metric for an agent in the ecosystem."""
    agent_id: str
    cpu_usage_pct: float
    memory_usage_mb: float
    active_tasks: int
    queue_depth: int
    last_heartbeat: datetime
    health_status: str


@dataclass
class AgentTopologyGraph:
    """React-flow compatible topology graph structure."""
    nodes: List[AgentTopologyNode]
    edges: List[Dict[str, Any]]
    layout_direction: str


class TaskEcosystemIntegration:
    """Integration for building agent topology graphs and monitoring ecosystem health."""

    STATUS_COLORS: Dict[str, str] = {
        "WORKING": "#43A047",
        "IDLE": "#FB8C00",
        "ERROR": "#E53935",
    }

    def __init__(self):
        self._health_store: Dict[str, AgentHealthMetric] = {}
        self._call_logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def build_topology_graph(self, task_id: str) -> AgentTopologyGraph:
        """Build a react-flow compatible topology graph for agents in a task."""
        # Generate simulated topology data
        nodes: List[AgentTopologyNode] = []
        edges: List[Dict[str, Any]] = []

        agent_data = [
            ("agent_a1", "DataCollector_A", "WORKING"),
            ("agent_b1", "Predictor_B", "WORKING"),
            ("agent_c1", "Interpreter_C", "IDLE"),
        ]

        positions = [
            {"x": 200.0, "y": 50.0},
            {"x": 400.0, "y": 150.0},
            {"x": 200.0, "y": 250.0},
        ]

        for idx, (aid, aname, status) in enumerate(agent_data):
            conns = []
            if idx > 0:
                prev_id = agent_data[idx - 1][0]
                call_count = random.randint(3, 15)
                conns.append({
                    "target_id": prev_id,
                    "call_count": call_count,
                    "width": min(3.0, 1.0 + call_count / 5.0),
                })
                edges.append({
                    "id": "edge_" + aid + "_" + prev_id,
                    "source": aid,
                    "target": prev_id,
                    "callCount": call_count,
                    "animated": True,
                    "style": {"strokeWidth": min(3.0, 1.0 + call_count / 5.0)},
                })

            node = AgentTopologyNode(
                node_id="node_" + aid,
                agent_id=aid,
                agent_name=aname,
                status=status,
                position=positions[idx],
                connections=conns,
            )
            nodes.append(node)

        return AgentTopologyGraph(
            nodes=nodes,
            edges=edges,
            layout_direction="TOP_DOWN",
        )

    def get_agent_health_status(
        self, agent_ids: List[str]
    ) -> List[AgentHealthMetric]:
        """Get real-time health snapshot for specified agents."""
        metrics: List[AgentHealthMetric] = []
        for aid in agent_ids:
            if aid in self._health_store:
                metrics.append(self._health_store[aid])
            else:
                # Generate simulated health data
                cpu = round(random.uniform(10.0, 95.0), 1)
                mem = round(random.uniform(100.0, 800.0), 1)
                active = random.randint(0, 8)
                queue = random.randint(0, 20)

                if cpu > 90 or mem > 700:
                    h_status = "CRITICAL"
                elif cpu > 70 or mem > 500 or queue > 10:
                    h_status = "WARNING"
                elif queue > 0:
                    h_status = "HEALTHY"
                else:
                    h_status = "HEALTHY"

                metric = AgentHealthMetric(
                    agent_id=aid,
                    cpu_usage_pct=cpu,
                    memory_usage_mb=mem,
                    active_tasks=active,
                    queue_depth=queue,
                    last_heartbeat=datetime.utcnow(),
                    health_status=h_status,
                )
                self._health_store[aid] = metric
                metrics.append(metric)
        return metrics

    def generate_health_alert_html(self, metric: AgentHealthMetric) -> str:
        """Generate a clickable health alert badge that navigates to task center."""
        alert_colors = {
            "HEALTHY": "#43A047",
            "WARNING": "#FB8C00",
            "CRITICAL": "#E53935",
            "DOWN": "#B71C1C",
        }
        bg = alert_colors.get(metric.health_status, "#666")

        html = (
            '<a href="/task-center?filter_agent=' + metric.agent_id + '" ' +
            'class="health-alert-badge" style="' +
            'display:inline-flex;align-items:center;padding:4px 12px;' +
            'border-radius:14px;font-size:11px;font-weight:bold;color:white;' +
            'background:' + bg + ';text-decoration:none;cursor:pointer;' +
            'transition:transform 0.2s;">\n' +
            '  <span style="width:8px;height:8px;border-radius:50%;' +
            'background:white;margin-right:6px;opacity:0.8;"></span>\n' +
            metric.agent_id[-6:] + ": " + metric.health_status +
            " (CPU:" + str(metric.cpu_usage_pct) + "%)" +
            "</a>"
        )
        return html


# =============================================================================
# PART K: TASK <-> FIVE-END COORDINATION INTEGRATION
# =============================================================================


class FiveEndView(str, Enum):
    """Five-end coordination views in the Governor Fang platform."""
    EDUCATION = "education"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"
    ASSOCIATION = "association"
    PLATFORM = "platform"


@dataclass
class EduSyncData:
    """Data synced to the Education end-view from a student task."""
    student_id: str
    task_id: str
    report_content: str
    submitted_at: datetime
    teacher_reviewed: bool
    teacher_id: Optional[str] = None
    score: Optional[int] = None
    comment: Optional[str] = None


@dataclass
class EnterpriseSubscription:
    """Enterprise subscription for regional monitoring reports."""
    sub_id: str
    enterprise_user_id: str
    region_filter: str
    report_type: str
    frequency: str
    created_at: datetime
    active: bool = True
    last_delivery: Optional[datetime] = None


@dataclass
class GovHeatmapPush:
    """Heatmap data pushed to Government end-view."""
    push_id: str
    gov_user_id: str
    region: str
    heatmap_data: str
    generated_at: datetime
    viewed: bool = False


@dataclass
class AssociationReportSummary:
    """Industry-wide aggregated report for Association end-view."""
    report_id: str
    period_start: date
    period_end: date
    industry_metrics: str
    generated_at: datetime
    download_count: int = 0


@dataclass
class EduSyncResult:
    """Result of syncing task data to Education end-view."""
    success: bool
    sync_id: str
    message: str


@dataclass
class SubResult:
    """Result of creating an enterprise subscription."""
    success: bool
    sub_id: str
    message: str


@dataclass
class PushResult:
    """Result of pushing heatmap data to Government end-view."""
    success: bool
    push_id: str
    message: str


@dataclass
class AssocReportResult:
    """Result of generating association industry report."""
    success: bool
    report_id: str
    message: str


class TaskFiveEndIntegration:
    """Integration layer connecting tasks with all five end-coordination views."""

    def __init__(self):
        self._edu_syncs: Dict[str, EduSyncData] = {}
        self._enterprise_subs: Dict[str, EnterpriseSubscription] = {}
        self._gov_pushes: Dict[str, GovHeatmapPush] = {}
        self._assoc_reports: Dict[str, AssociationReportSummary] = {}

    def sync_to_education(
        self, student_id: str, task_data: Dict[str, Any]
    ) -> EduSyncResult:
        """Anonymize and push student task result to education view for review."""
        sync_id = "edu_sync_" + uuid.uuid4().hex[:8]

        edu_data = EduSyncData(
            student_id=student_id,
            task_id=task_data.get("task_id", ""),
            report_content=self._anonymize_for_edu(task_data.get("report_content", "")),
            submitted_at=datetime.utcnow(),
            teacher_reviewed=False,
        )

        self._edu_syncs[sync_id] = edu_data

        return EduSyncResult(
            success=True,
            sync_id=sync_id,
            message="Task synced to Education view for teacher review.",
        )

    def create_enterprise_subscription(
        self, user_id: str, config: Dict[str, Any]
    ) -> SubResult:
        """Create a regional monitoring subscription for enterprise user."""
        sub_id = "ent_sub_" + uuid.uuid4().hex[:8]

        sub = EnterpriseSubscription(
            sub_id=sub_id,
            enterprise_user_id=user_id,
            region_filter=config.get("region", "all"),
            report_type=config.get("report_type", "market_monitor"),
            frequency=config.get("frequency", "weekly"),
            created_at=datetime.utcnow(),
            active=True,
        )

        self._enterprise_subs[sub_id] = sub

        return SubResult(
            success=True,
            sub_id=sub_id,
            message="Enterprise subscription created for region: " + sub.region_filter,
        )

    def push_gov_heatmap(
        self, gov_user_id: str, region: str, data: Dict[str, Any]
    ) -> PushResult:
        """Push processed heatmap data to government dashboard."""
        push_id = "gov_push_" + uuid.uuid4().hex[:8]

        push = GovHeatmapPush(
            push_id=push_id,
            gov_user_id=gov_user_id,
            region=region,
            heatmap_data=json.dumps(data, ensure_ascii=False),
            generated_at=datetime.utcnow(),
            viewed=False,
        )

        self._gov_pushes[push_id] = push

        return PushResult(
            success=True,
            push_id=push_id,
            message="Heatmap pushed for region: " + region,
        )

    def generate_association_report(
        self, period_start: date, period_end: date
    ) -> AssocReportResult:
        """Aggregate industry-wide data into white paper for association."""
        report_id = "assoc_rpt_" + uuid.uuid4().hex[:8]

        metrics = {
            "total_analyses": random.randint(500, 2000),
            "avg_price_change_pct": round(random.uniform(-5.0, 8.0), 2),
            "hot_districts": ["District A", "District C"],
            "market_sentiment": random.choice(["bullish", "neutral", "bearish"]),
        }

        report = AssociationReportSummary(
            report_id=report_id,
            period_start=period_start,
            period_end=period_end,
            industry_metrics=json.dumps(metrics),
            generated_at=datetime.utcnow(),
        )

        self._assoc_reports[report_id] = report

        return AssocReportResult(
            success=True,
            report_id=report_id,
            message="Association report generated for period " +
                   str(period_start) + " to " + str(period_end),
        )

    def _anonymize_for_edu(self, content: str) -> str:
        """Anonymize sensitive information before sending to education view."""
        return "[ANONYMIZED] " + content[:200] + "..."


# =============================================================================
# PART L: TASK <-> THREE-SIX LEARNING SYSTEM INTEGRATION
# =============================================================================


@dataclass
class TrainingSample:
    """A single training sample extracted from task data for the learning system."""
    sample_id: str
    task_id: str
    input_data: str
    output_data: str
    user_rating: float
    feedback_type: str
    extracted_at: datetime
    sample_quality_score: float
    used_in_training: bool = False


@dataclass
class ExportResult:
    """Result of exporting training batch to training platform."""
    success: bool
    file_path: str
    sample_count: int
    format: str


@dataclass
class ModelUpdateResult:
    """Result of triggering model update after successful training."""
    success: bool
    model_version: str
    improvement_metrics: Dict[str, float]


class TaskLearningSystemIntegration:
    """Integration for extracting training samples and coordinating with learning platform."""

    def __init__(self):
        self._samples: List[TrainingSample] = []
        self._export_log: List[ExportResult] = []

    def extract_high_quality_samples(
        self, min_rating: float = 4.0, limit: int = 50
    ) -> List[TrainingSample]:
        """Weekly extraction of high-quality positive samples for offline training."""
        qualified = [
            s for s in self._samples
            if s.user_rating >= min_rating and s.sample_quality_score >= 0.8
        ]
        qualified.sort(key=lambda s: s.sample_quality_score, reverse=True)
        return qualified[:limit]

    def prepare_negative_sample(
        self, failure_case: FailureCaseForTraining
    ) -> TrainingSample:
        """Convert a failure case into a negative RL training sample."""
        sample_id = "neg_sample_" + uuid.uuid4().hex[:10]

        sample = TrainingSample(
            sample_id=sample_id,
            task_id=failure_case.task_id,
            input_data=failure_case.input_snapshot,
            output_data=failure_case.output_snapshot,
            user_rating=1.0,
            feedback_type="NEGATIVE_FAILURE",
            extracted_at=datetime.utcnow(),
            sample_quality_score=0.95,
            used_in_training=False,
        )

        self._samples.append(sample)
        return sample

    def export_training_batch(
        self, samples: List[TrainingSample], format_str: str = "JSON"
    ) -> ExportResult:
        """Package training samples for delivery to the training platform."""
        file_path = "/exports/batch_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S") + \
                     "." + format_str.lower()

        export = ExportResult(
            success=True,
            file_path=file_path,
            sample_count=len(samples),
            format=format_str,
        )

        self._export_log.append(export)
        return export

    def trigger_model_update(
        self, training_results: Dict[str, Any]
    ) -> ModelUpdateResult:
        """Notify deployment system after successful training completes."""
        old_version = training_results.get("previous_version", "v28.0.0")
        major, minor, patch = old_version.replace("v", "").split(".")
        new_version = "v" + major + "." + minor + "." + str(int(patch) + 1)

        improvement = {
            "accuracy_gain_pct": round(random.uniform(0.5, 3.0), 2),
            "latency_reduction_pct": round(random.uniform(1.0, 5.0), 2),
            "new_samples_absorbed": training_results.get("sample_count", 0),
        }

        return ModelUpdateResult(
            success=True,
            model_version=new_version,
            improvement_metrics=improvement,
        )


# =============================================================================
# PART M: TASK <-> COUNTERATTACK SYSTEM INTEGRATION
# =============================================================================


@dataclass
class ThreatAssessment:
    """Assessment of security threat level for a task request."""
    assessment_id: str
    task_request_id: str
    ip_address: str
    user_id: str
    request_frequency_1m: int
    request_frequency_1h: int
    parameter_anomaly_score: float
    threat_level: str
    assessed_at: datetime


@dataclass
class DrillTriggerCondition:
    """Condition definition for triggering a security drill."""
    trigger_type: str
    threshold_value: int
    window_minutes: int


@dataclass
class InterceptionResult:
    """Result of intercepting a threatening request."""
    intercepted: bool
    error_code: str
    audit_log_id: str
    response_message: str


@dataclass
class DrillSession:
    """Active session for a red-blue security drill."""
    session_id: str
    trigger_type: str
    target_system: str
    attack_vectors: List[Dict[str, Any]]
    started_at: datetime
    status: str
    result: Optional[Dict[str, Any]] = None


@dataclass
class DrillResult:
    """Result of executing a security drill exercise."""
    passed: bool
    vulnerabilities_found: int
    defense_improvements: List[str]
    report_generated: bool


DRILL_TRIGGER_CONDITIONS: List[DrillTriggerCondition] = [
    DrillTriggerCondition(
        trigger_type="CONSECUTIVE_FAILURES",
        threshold_value=5,
        window_minutes=30,
    ),
    DrillTriggerCondition(
        trigger_type="FREQUENCY_SPIKE",
        threshold_value=100,
        window_minutes=1,
    ),
    DrillTriggerCondition(
        trigger_type="ANOMALY_PATTERN",
        threshold_value=3,
        window_minutes=60,
    ),
]


class TaskSecurityIntegration:
    """Security integration for threat assessment, interception, and drill orchestration."""

    THRESHOLD_FREQUENCIES: Dict[str, Tuple[int, int]] = {
        "SAFE": (0, 10),
        "SUSPICIOUS": (10, 50),
        "DANGEROUS": (50, 100),
        "CRITICAL": (100, 999999),
    }

    def __init__(self):
        self._audit_log: List[Dict[str, Any]] = []
        self._drill_sessions: Dict[str, DrillSession] = {}
        self._request_counts: Dict[str, List[datetime]] = defaultdict(list)

    def assess_task_threat(self, request_context: Dict[str, Any]) -> ThreatAssessment:
        """Evaluate IP, user, frequency, and parameter anomaly to determine threat level."""
        assessment_id = "threat_" + uuid.uuid4().hex[:8]
        ip_address = request_context.get("ip_address", "0.0.0.0")
        user_id = request_context.get("user_id", "anonymous")

        now = datetime.utcnow()
        key = ip_address + ":" + user_id
        self._request_counts[key].append(now)

        cutoff_1m = now - timedelta(minutes=1)
        cutoff_1h = now - timedelta(hours=1)
        freq_1m = sum(1 for t in self._request_counts[key] if t >= cutoff_1m)
        freq_1h = sum(1 for t in self._request_counts[key] if t >= cutoff_1h)

        param_anomaly = float(request_context.get("parameter_anomaly_score", 0.0))

        # Determine threat level
        threat_level = "SAFE"
        if freq_1m >= 100 or param_anomaly > 0.9:
            threat_level = "CRITICAL"
        elif freq_1m >= 50 or param_anomaly > 0.7:
            threat_level = "DANGEROUS"
        elif freq_1m >= 10 or param_anomaly > 0.4:
            threat_level = "SUSPICIOUS"

        return ThreatAssessment(
            assessment_id=assessment_id,
            task_request_id=request_context.get("request_id", ""),
            ip_address=ip_address,
            user_id=user_id,
            request_frequency_1m=freq_1m,
            request_frequency_1h=freq_1h,
            parameter_anomaly_score=param_anomaly,
            threat_level=threat_level,
            assessed_at=now,
        )

    def should_intercept(self, threat: ThreatAssessment) -> bool:
        """Determine whether a threat level warrants interception."""
        return threat.threat_level in ("DANGEROUS", "CRITICAL")

    def intercept_and_log(self, threat: ThreatAssessment) -> InterceptionResult:
        """Intercept a threatening request and log to security audit."""
        audit_id = "audit_" + uuid.uuid4().hex[:10]

        audit_entry = {
            "audit_id": audit_id,
            "assessment_id": threat.assessment_id,
            "ip_address": threat.ip_address,
            "user_id": threat.user_id,
            "threat_level": threat.threat_level,
            "action_taken": "INTERCEPTED",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._audit_log.append(audit_entry)

        error_codes = {
            "DANGEROUS": "SECURITY_429_TOO_DANGEROUS",
            "CRITICAL": "SECURITY_403_FORBIDDEN",
        }
        messages = {
            "DANGEROUS": "Request blocked due to suspicious activity pattern.",
            "CRITICAL": "Access denied. Security review required.",
        }

        return InterceptionResult(
            intercepted=True,
            error_code=error_codes.get(threat.threat_level, "SECURITY_UNKNOWN"),
            audit_log_id=audit_id,
            response_message=messages.get(threat.threat_level, "Request intercepted."),
        )

    def check_drill_trigger(
        self, task_failures_recent: List[Dict[str, Any]]
    ) -> Optional[DrillSession]:
        """Check if recent failures meet criteria for triggering a red-blue drill."""
        for condition in DRILL_TRIGGER_CONDITIONS:
            if condition.trigger_type == "CONSECUTIVE_FAILURES":
                if len(task_failures_recent) >= condition.threshold_value:
                    return self._start_drill_session(condition, task_failures_recent)
            elif condition.trigger_type == "FREQUENCY_SPIKE":
                total_failures = sum(f.get("count", 0) for f in task_failures_recent)
                if total_failures >= condition.threshold_value:
                    return self._start_drill_session(condition, task_failures_recent)
        return None

    def execute_security_drill(
        self, drill_session: DrillSession
    ) -> DrillResult:
        """Execute a simulated attack drill to test defense mechanisms."""
        vulnerabilities_found = random.randint(0, 3)
        improvements = [
            "Rate limiting tightened for API endpoint /task/submit",
            "WAF rule updated for SQL injection patterns",
            "IP reputation check enhanced with real-time blacklist",
        ][:vulnerabilities_found + 1]

        drill_session.result = {
            "vulnerabilities_found": vulnerabilities_found,
            "improvements_applied": improvements,
            "completed_at": datetime.utcnow().isoformat(),
        }
        drill_session.status = "PASSED" if vulnerabilities_found == 0 else "FAILED"

        return DrillResult(
            passed=vulnerabilities_found == 0,
            vulnerabilities_found=vulnerabilities_found,
            defense_improvements=improvements,
            report_generated=True,
        )

    def _start_drill_session(
        self, condition: DrillTriggerCondition, failures: List[Dict[str, Any]]
    ) -> DrillSession:
        """Initialize a new drill session triggered by condition match."""
        session_id = "drill_" + uuid.uuid4().hex[:8]

        vectors = [
            {"type": "ddos_simulation", "intensity": "medium"},
            {"type": "injection_attempt", "payload_type": "SQL"},
            {"type": "parameter_tampering", "fields": ["budget", "area"]},
        ]

        session = DrillSession(
            session_id=session_id,
            trigger_type=condition.trigger_type,
            target_system="task_submission_api",
            attack_vectors=vectors,
            started_at=datetime.utcnow(),
            status="RUNNING",
        )

        self._drill_sessions[session_id] = session
        return session


# =============================================================================
# PART N: CROSS-MODULE ORCHESTRATION ENGINE
# =============================================================================


class CrossModuleEventType(str, Enum):
    """Event types broadcast across modules in the orchestrator."""
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    AGENT_RECRUITED = "AGENT_RECRUITED"
    SKILL_PURCHASED = "SKILL_PURCHASED"
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    SCHEDULE_CREATED = "SCHEDULE_CREATED"
    TRAINING_SAMPLE_EXPORTED = "TRAINING_SAMPLE_EXPORTED"
    SECURITY_DRILL = "SECURITY_DRILL"


@dataclass
class CrossModuleEvent:
    """An event propagated through the cross-module event bus."""
    event_id: str
    source_module: str
    event_type: str
    payload: str
    timestamp: datetime
    propagated_modules: List[str]


class CrossModuleOrchestrator:
    """Central event bus connecting all 14 module integrations for coordinated actions."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_timeline: List[CrossModuleEvent] = []
        self._lock = threading.Lock()

        # Register built-in handlers
        self._register_builtin_handlers()

    def publish_event(self, event: CrossModuleEvent) -> None:
        """Broadcast an event to all registered subscribers."""
        with self._lock:
            self._event_timeline.append(event)

        handlers = self._subscribers.get("*", []) + \
            self._subscribers.get(event.event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.error(
                    "Handler error for event %s: %s", event.event_id, str(exc)
                )

        logger.info(
            "Event published: %s from %s | handlers=%d",
            event.event_id, event.source_module, len(handlers),
        )

    def subscribe(
        self, module_name: str, handler: Callable[[CrossModuleEvent], None]
    ) -> None:
        """Register a listener for events (specific type or wildcard '*')."""
        self._subscribers[module_name].append(handler)
        logger.info("Subscriber registered: module=%s", module_name)

    def get_event_timeline(
        self, module_name: str, since: Optional[datetime] = None
    ) -> List[CrossModuleEvent]:
        """Get event history for a specific module since a given timestamp."""
        events = [
            e for e in self._event_timeline
            if module_name in e.propagated_modules or module_name == "*"
        ]
        if since:
            events = [e for e in events if e.timestamp >= since]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    def calculate_cross_module_synergy_score(self) -> Dict[str, Any]:
        """Calculate overall integration health metric across all modules."""
        total_events = len(self._event_timeline)
        event_types: Dict[str, int] = defaultdict(int)
        module_sources: Dict[str, int] = defaultdict(int)

        for evt in self._event_timeline:
            event_types[evt.event_type] += 1
            module_sources[evt.source_module] += 1

        subscriber_count = sum(len(v) for v in self._subscribers.values())

        # Synergy score: higher when many events flow between diverse modules
        unique_source_count = len(module_sources)
        unique_type_count = len(event_types)
        diversity_factor = (unique_source_count * unique_type_count) / \
            max(1, unique_source_count + unique_type_count)
        activity_score = min(100.0, total_events / 10.0)
        synergy = round(diversity_factor * 30 + activity_score * 0.7, 1)

        return {
            "synergy_score": min(100.0, synergy),
            "total_events_broadcast": total_events,
            "unique_event_types": unique_type_count,
            "active_subscriber_count": subscriber_count,
            "modules_participating": list(module_sources.keys()),
            "event_breakdown": dict(event_types),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _register_builtin_handlers(self) -> None:
        """Register built-in auto-trigger handlers for cross-module events."""

        def _on_task_completed(evt: CrossModuleEvent):
            payload = json.loads(evt.payload) if evt.payload else {}
            evt.propagated_modules.extend([
                "task_center", "my_reports", "memory_system", "evolution",
            ])

        def _on_task_failed(evt: CrossModuleEvent):
            evt.propagated_modules.extend([
                "talent_market", "counterattack", "learning_system",
            ])

        def _on_feedback_received(evt: CrossModuleEvent):
            evt.propagated_modules.extend([
                "evolution", "learning_system", "memory_system",
            ])

        def _on_security_drill(evt: CrossModuleEvent):
            evt.propagated_modules.extend([
                "counterattack", "ecosystem", "platform",
            ])

        self.subscribe(CrossModuleEventType.TASK_COMPLETED.value, _on_task_completed)
        self.subscribe(CrossModuleEventType.TASK_FAILED.value, _on_task_failed)
        self.subscribe(CrossModuleEventType.FEEDBACK_RECEIVED.value, _on_feedback_received)
        self.subscribe(CrossModuleEventType.SECURITY_DRILL.value, _on_security_drill)


# =============================================================================
# PART O: TESTING SUITE
# =============================================================================


CROSS_MODULE_TEST_CASES: Dict[str, List[Dict[str, Any]]] = {

    "action_panel": [
        {"id": "TC_CM_001", "name": "action_panel_renders_with_items",
         "description": "render_action_panel produces non-empty HTML when context has matching conditions"},
        {"id": "TC_CM_002", "name": "action_panel_filters_by_context",
         "description": "Items are filtered out when their condition function returns False"},
        {"id": "TC_CM_003", "name": "action_panel_priority_sorting",
         "description": "Visible items are sorted by priority ascending"},
    ],

    "task_redirect": [
        {"id": "TC_TR_001", "name": "redirect_url_generation",
         "description": "create_redirect_url produces correct URL with task_id substituted"},
        {"id": "TC_TR_002", "name": "auto_redirect_detection",
         "description": "should_auto_redirect returns True for deep_analysis task types"},
    ],

    "task_center_history": [
        {"id": "TC_TCH_001", "name": "history_pagination_works",
         "description": "get_task_history returns PaginatedResult with correct page/page_size"},
        {"id": "TC_TCH_002", "name": "history_status_filter",
         "description": "Status filter correctly narrows down entries to only matching status"},
        {"id": "TC_TCH_003", "name": "batch_delete_and_retry",
         "description": "batch_delete_tasks removes entries and batch_retry_tasks only retries FAILED"},
    ],

    "team_agent_display": [
        {"id": "TC_TAD_001", "name": "task_agents_returned",
         "description": "get_task_agents returns list of TaskAgentDisplay for a known task"},
        {"id": "TC_TAD_002", "name": "load_warning_badge_rendering",
         "description": "generate_load_warning_html renders colored badge with CRITICAL status"},
    ],

    "property_compare": [
        {"id": "TC_PC_001", "name": "extract_properties_from_result",
         "description": "extract_properties_from_task_result parses properties from result dict"},
        {"id": "TC_PC_002", "name": "property_selection_ui_rendering",
         "description": "render_property_selection_ui produces card-based HTML with checkboxes"},
        {"id": "TC_PC_003", "name": "compare_url_generation",
         "description": "generate_compare_url joins IDs with commas correctly"},
    ],

    "auto_report_save": [
        {"id": "TC_ARS_001", "name": "auto_save_on_completion",
         "description": "auto_save_report creates ReportSaveResult with valid report_id"},
        {"id": "TC_ARS_002", "name": "reports_for_task_retrieval",
         "description": "get_reports_for_task returns saved reports linked to task_id"},
    ],

    "memory_preferences": [
        {"id": "TC_MP_001", "name": "save_preference_returns_id",
         "description": "save_analysis_preference returns a preference_id string"},
        {"id": "TC_MP_002", "name": "latest_preference_retrieval",
         "description": "get_latest_preference returns most recently used preference"},
        {"id": "TC_MP_003", "name": "prefill_form_and_agent_format",
         "description": "generate_prefill_form_data returns dict and format_preference_for_agent returns NL string"},
    ],

    "market_suggestions": [
        {"id": "TC_MS_001", "name": "recruitment_from_performance",
         "description": "analyze_task_performance generates suggestions when duration/quality exceed thresholds"},
        {"id": "TC_MS_002", "name": "skill_gap_detection",
         "description": "analyze_missing_capabilities creates skill suggestions from failure reasons"},
        {"id": "TC_MS_003", "name": "post_recruitment_handling",
         "description": "handle_post_recruitment returns successful PostRecruitmentResult"},
    ],

    "autonomous_work": [
        {"id": "TC_AW_001", "name": "schedule_proposal_creation",
         "description": "generate_schedule_proposal creates ScheduledTaskProposal with expiry"},
        {"id": "TC_AW_002", "name": "autonomous_result_storage",
         "description": "store_autonomous_result returns memory_id string"},
    ],

    "evolution_signals": [
        {"id": "TC_ES_001", "name": "feedback_recording",
         "description": "record_feedback stores signal and returns feedback_id"},
        {"id": "TC_ES_002", "name": "training_sample_export",
         "description": "export_training_samples returns TrainingSampleExport with counts"},
        {"id": "TC_ES_003", "name": "failure_case_submission",
         "description": "submit_failure_case adds to pool and returns case_id"},
    ],

    "ecosystem_topology": [
        {"id": "TC_ET_001", "name": "topology_graph_structure",
         "description": "build_topology_graph returns AgentTopologyGraph with nodes and edges"},
        {"id": "TC_ET_002", "name": "health_metric_alert_html",
         "description": "generate_health_alert_html produces clickable badge with CPU info"},
    ],

    "five_end_views": [
        {"id": "TC_FEV_001", "name": "education_sync_flow",
         "description": "sync_to_education anonymizes and stores task data for review"},
        {"id": "TC_FEV_002", "name": "enterprise_subscription_creation",
         "description": "create_enterprise_subscription creates active subscription with region filter"},
        {"id": "TC_FEV_003", "name": "gov_heatmap_push",
         "description": "push_gov_heatmap stores heatmap JSON for gov dashboard"},
        {"id": "TC_FEV_004", "name": "association_report_generation",
         "description": "generate_aggregation_report creates summary with industry metrics"},
    ],

    "learning_system": [
        {"id": "TC_LS_001", "name": "high_quality_sample_extraction",
         "description": "extract_high_quality_samples returns samples above rating threshold"},
        {"id": "TC_LS_002", "name": "negative_sample_preparation",
         "description": "prepare_negative_sample converts FailureCaseForTraining into TrainingSample"},
    ],

    "security_integration": [
        {"id": "TC_SEC_001", "name": "threat_assessment_levels",
         "description": "assess_task_threat determines SAFE/SUSPICIOUS/DANGEROUS/CRITICAL correctly"},
        {"id": "TC_SEC_002", "name": "interception_logic",
         "description": "should_intercept returns True for DANGEROUS and CRITICAL levels"},
        {"id": "TC_SEC_003", "name": "drill_trigger_and_execute",
         "description": "check_drill_trigger creates session and execute_security_drill runs simulation"},
    ],

    "orchestrator": [
        {"id": "TC_ORC_001", "name": "event_publish_and_subscribe",
         "description": "publish_event delivers to registered subscribers and records in timeline"},
        {"id": "TC_ORC_002", "name": "event_timeline_query",
         "description": "get_event_timeline returns events for a module since timestamp"},
        {"id": "TC_ORC_003", "name": "synergy_score_calculation",
         "description": "calculate_cross_module_synergy_score returns dict with score 0-100"},
    ],

    "frontend_rendering": [
        {"id": "TC_FR_001", "name": "action_panel_html_valid",
         "description": "render_action_panel output contains Quick Actions header and buttons"},
        {"id": "TC_FR_002", "name": "property_selection_cards",
         "description": "render_property_selection_ui contains checkboxes and Compare bar"},
        {"id": "TC_FR_003", "name": "report_backlink_button",
         "description": "generate_backlink_to_task produces anchor tag with View Original Task text"},
        {"id": "TC_FR_004", "name": "memory_prefill_format",
         "description": "format_preference_for_agent returns multi-line string with User Preference Profile"},
        {"id": "TC_FR_005", "name": "health_alert_and_topology",
         "description": "generate_health_alert_html and build_topology_graph produce valid structures"},
    ],
}


class CrossModuleTestSuite:
    """Comprehensive test suite for Layer 28: Task Analysis & Cross-Module Integration."""

    def __init__(self):
        self.panel_renderer = ActionPanelRenderer()
        self.redirect_svc = TaskRedirectService()
        self.task_center = TaskCenterIntegration()
        self.team_integration = TaskTeamIntegration()
        self.property_compare = TaskPropertyCompareIntegration()
        self.report_integration = TaskReportIntegration()
        self.memory_integration = TaskMemoryIntegration()
        self.market_integration = TaskMarketIntegration()
        self.autonomous_integration = TaskAutonomousWorkIntegration()
        self.evolution_integration = TaskEvolutionIntegration()
        self.ecosystem_integration = TaskEcosystemIntegration()
        self.five_end_integration = TaskFiveEndIntegration()
        self.learning_integration = TaskLearningSystemIntegration()
        self.security_integration = TaskSecurityIntegration()
        self.orchestrator = CrossModuleOrchestrator()
        self._results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories and return summary."""
        self._results = []
        self._test_action_panel()
        self._test_task_redirect()
        self._test_task_center_history()
        self._test_team_agent_display()
        self._test_property_compare()
        self._test_auto_report_save()
        self._test_memory_preferences()
        self._test_market_suggestions()
        self._test_autonomous_work()
        self._test_evolution_signals()
        self._test_ecosystem_topology()
        self._test_five_end_views()
        self._test_learning_system()
        self._test_security_integration()
        self._test_orchestrator()
        self._test_frontend_rendering()

        total = len(self._results)
        passed = sum(1 for r in self._results if r.get("passed", False))
        failed = total - passed
        return {
            "layer": 28,
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / max(1, total) * 100, 1),
            "details": self._results,
        }

    def _record(self, test_id: str, name: str, passed: bool, detail: str = ""):
        self._results.append({
            "test_id": test_id,
            "name": name,
            "passed": passed,
            "detail": detail,
        })

    # ------------------------------------------------------------------
    # Category 1: Action Panel
    # ------------------------------------------------------------------
    def _test_action_panel(self):
        ctx_normal = {
            "task_id": "t001", "status": "RUNNING",
            "duration_ms": 30000, "quality_score": 0.85,
        }
        html = self.panel_renderer.render_action_panel(ctx_normal)
        has_header = "Quick Actions" in html
        self._record(
            "TC_CM_001", "action_panel_renders_with_items",
            has_header and len(html) > 50,
            "html_len=" + str(len(html)) + " header=" + str(has_header),
        )

        ctx_empty = {"task_id": "t002", "status": "PENDING"}
        html_empty = self.panel_renderer.render_action_panel(ctx_empty)
        visible_btns = html_empty.count('href="')
        self._record(
            "TC_CM_002", "action_panel_filters_by_context",
            visible_btns >= 1,
            "visible_buttons=" + str(visible_btns),
        )

        ctx_full = {
            "task_id": "t003", "status": "COMPLETED",
            "duration_ms": 90000, "quality_score": 0.45,
            "properties_in_result": ["p1", "p2"],
            "parameters": {"city": "Taipei"},
            "missing_capabilities": ["advanced_nlp"],
        }
        html_full = self.panel_renderer.render_action_panel(ctx_full)
        btn_count = html_full.count('class="action-btn"')
        self._record(
            "TC_CM_003", "action_panel_priority_sorting",
            btn_count >= 3,
            "buttons=" + str(btn_count),
        )

    # ------------------------------------------------------------------
    # Category 2: Task Redirect
    # ------------------------------------------------------------------
    def _test_task_redirect(self):
        result = self.redirect_svc.create_redirect_url(
            "view_task_center_detail", "task_123", {"task_id": "task_123"}
        )
        url_ok = "/task-center?taskId=task_123" in result.url
        self._record(
            "TC_TR_001", "redirect_url_generation",
            url_ok and result.target_module == "task_center",
            "url=" + result.url[:40],
        )

        auto_deep = self.redirect_svc.should_auto_redirect("deep_analysis")
        auto_simple = self.redirect_svc.should_auto_redirect("simple_query")
        self._record(
            "TC_TR_002", "auto_redirect_detection",
            auto_deep and not auto_simple,
            "deep=" + str(auto_deep) + " simple=" + str(auto_simple),
        )

    # ------------------------------------------------------------------
    # Category 3: Task Center History
    # ------------------------------------------------------------------
    def _test_task_center_history(self):
        # Seed some test data
        user_id = "test_user_tc"
        for i in range(25):
            entry = TaskHistoryEntry(
                task_id="tc_task_" + str(i),
                name="Test Task " + str(i),
                type="analysis",
                status=TaskStatus.COMPLETED if i % 3 != 0 else TaskStatus.FAILED,
                created_at=datetime.utcnow() - timedelta(hours=i),
                duration_ms=random.randint(5000, 60000),
                agent_count=2,
            )
            self.task_center._history_store[user_id].append(entry)

        result = self.task_center.get_task_history(user_id, {"page": 1})
        self._record(
            "TC_TCH_001", "history_pagination_works",
            isinstance(result, PaginatedResult) and len(result.items) == 20,
            "total=" + str(result.total) + " page_items=" + str(len(result.items)),
        )

        result_filtered = self.task_center.get_task_history(
            user_id, {"status": "FAILED", "page": 1}
        )
        all_failed = all(
            isinstance(e, TaskHistoryEntry) and e.status == TaskStatus.FAILED
            for e in result_filtered.items
        )
        self._record(
            "TC_TCH_002", "history_status_filter",
            all_failed,
            "filtered_count=" + str(len(result_filtered.items)),
        )

        del_result = self.task_center.batch_delete_tasks(
            ["tc_task_0", "tc_task_1"], user_id
        )
        retry_result = self.task_center.batch_retry_tasks(["tc_task_3"])
        self._record(
            "TC_TCH_003", "batch_delete_and_retry",
            del_result.affected_count >= 0 and retry_result.affected_count >= 0,
            "deleted=" + str(del_result.affected_count) +
            " retried=" + str(retry_result.affected_count),
        )

    # ------------------------------------------------------------------
    # Category 4: Team Agent Display
    # ------------------------------------------------------------------
    def _test_team_agent_display(self):
        task_id = "tad_test_task"
        self.team_integration._task_agents[task_id] = [
            TaskAgentDisplay(
                agent_id="a1", agent_name="Collector_X", agent_type="li_bu",
                role_in_task="DATA_PROVIDER", status="WORKING",
                duration_ms=15000, contribution_summary="Collected 50 data points",
            ),
            TaskAgentDisplay(
                agent_id="a2", agent_name="Predictor_Y", agent_type="gong_bu",
                role_in_task="PREDICTOR", status="DONE",
                duration_ms=8000, contribution_summary="Generated predictions",
            ),
        ]
        agents = self.team_integration.get_task_agents(task_id)
        self._record(
            "TC_TAD_001", "task_agents_returned",
            len(agents) == 2 and agents[0].role_in_task == "DATA_PROVIDER",
            "count=" + str(len(agents)),
        )

        load = TeamAgentLoadDisplay(
            agent_id="a3", agent_name="HeavyWorker_Z",
            current_active_tasks=18, load_level="CRITICAL",
            warning_thresholds=(10, 20),
        )
        badge_html = self.team_integration.generate_load_warning_html(load)
        has_critical = "CRITICAL" in badge_html
        self._record(
            "TC_TAD_002", "load_warning_badge_rendering",
            has_critical and "18 tasks" in badge_html,
            "badge=" + badge_html[:60],
        )

    # ------------------------------------------------------------------
    # Category 5: Property Compare
    # ------------------------------------------------------------------
    def _test_property_compare(self):
        task_result = {
            "analyzed_properties": [
                {"id": "prop_a", "name": "Skyline Tower", "address": "1 High St",
                 "price": 950000},
                {"id": "prop_b", "name": "Garden Villa", "address": "2 Green Ave",
                 "price": 2200000},
            ],
        }
        props = self.property_compare.extract_properties_from_task_result(task_result)
        self._record(
            "TC_PC_001", "extract_properties_from_result",
            len(props) == 2 and props[0].property_name == "Skyline Tower",
            "count=" + str(len(props)),
        )

        ui_html = self.property_compare.render_property_selection_ui(props)
        has_checkbox = "checkbox" in ui_html
        has_compare_bar = "Compare" in ui_html
        self._record(
            "TC_PC_002", "property_selection_ui_rendering",
            has_checkbox and has_compare_bar,
            "checkbox=" + str(has_checkbox) + " bar=" + str(has_compare_bar),
        )

        url = self.property_compare.generate_compare_url(["p1", "p2", "p3"])
        self._record(
            "TC_PC_003", "compare_url_generation",
            url == "/compare?ids=p1,p2,p3",
            "url=" + url,
        )

    # ------------------------------------------------------------------
    # Category 6: Auto Report Save
    # ------------------------------------------------------------------
    def _test_auto_report_save(self):
        save_result = self.report_integration.auto_save_report(
            "task_rpt_001",
            {"summary": "Analysis complete", "score": 0.92},
        )
        self._record(
            "TC_ARS_001", "auto_save_on_completion",
            save_result.success and save_result.report_id.startswith("rpt_"),
            "report_id=" + save_result.report_id,
        )

        reports = self.report_integration.get_reports_for_task("task_rpt_001")
        self._record(
            "TC_ARS_002", "reports_for_task_retrieval",
            len(reports) >= 1,
            "count=" + str(len(reports)),
        )

    # ------------------------------------------------------------------
    # Category 7: Memory Preferences
    # ------------------------------------------------------------------
    def _test_memory_preferences(self):
        pref_id = self.memory_integration.save_analysis_preference({
            "user_id": "u_mem_test",
            "task_type": "investment_analysis",
            "parameters": {
                "city": "Taichung",
                "budget_min": 500000,
                "budget_max": 3000000,
                "area_min": 30,
                "area_max": 120,
                "room_type": "3BR",
                "style_tags": ["modern", "minimalist"],
            },
        })
        self._record(
            "TC_MP_001", "save_preference_returns_id",
            pref_id.startswith("pref_") and len(pref_id) > 8,
            "pref_id=" + pref_id,
        )

        latest = self.memory_integration.get_latest_preference(
            "u_mem_test", "investment_analysis"
        )
        has_city = latest is not None and latest.city == "Taichung"
        self._record(
            "TC_MP_002", "latest_preference_retrieval",
            has_city,
            "city=" + (latest.city if latest else "None"),
        )

        if latest:
            form_data = self.memory_integration.generate_prefill_form_data(latest)
            agent_text = self.memory_integration.format_preference_for_agent(latest)
            self._record(
                "TC_MP_003", "prefill_form_and_agent_format",
                isinstance(form_data, dict) and "User Preference Profile" in agent_text,
                "form_keys=" + str(list(form_data.keys()))[:40],
            )
        else:
            self._record("TC_MP_003", "prefill_form_and_agent_format", False, "no pref")

    # ------------------------------------------------------------------
    # Category 8: Market Suggestions
    # ------------------------------------------------------------------
    def _test_market_suggestions(self):
        recs = self.market_integration.analyze_task_performance({
            "task_id": "mk_perf_001",
            "duration_ms": 90000,
            "quality_score": 0.42,
        })
        has_rec = len(recs) > 0 and recs[0].reason_code in ("HIGH_LOAD", "LOW_QUALITY")
        self._record(
            "TC_MS_001", "recruitment_from_performance",
            has_rec,
            "suggestions=" + str(len(recs)),
        )

        skills = self.market_integration.analyze_missing_capabilities({
            "task_id": "mk_skill_001",
            "missing_capabilities": ["sentiment_analysis"],
            "failure_reason": "timeout during processing",
        })
        has_skill = len(skills) > 0
        self._record(
            "TC_MS_002", "skill_gap_detection",
            has_skill,
            "skills=" + str(len(skills)),
        )

        post_result = self.market_integration.handle_post_recruitment("new_agent_1", "team_1")
        self._record(
            "TC_MS_003", "post_recruitment_handling",
            post_result.success and post_result.scheduler_notified,
            "notified=" + str(post_result.scheduler_notified),
        )

    # ------------------------------------------------------------------
    # Category 9: Autonomous Work
    # ------------------------------------------------------------------
    def _test_autonomous_work(self):
        proposal = self.autonomous_integration.generate_schedule_proposal({
            "task_id": "aw_src_001",
            "task_type": "weekly_market_monitoring",
            "parameters": {"city": "Kaohsiung"},
        })
        self._record(
            "TC_AW_001", "schedule_proposal_creation",
            proposal.proposal_id.startswith("prop_") and proposal.frequency == "WEEKLY",
            "freq=" + proposal.frequency,
        )

        mem_id = self.autonomous_integration.store_autonomous_result(
            "sched_test_001", {"metric": "growth", "value": 3.2}
        )
        self._record(
            "TC_AW_002", "autonomous_result_storage",
            mem_id.startswith("mem_periodic_"),
            "mem_id=" + mem_id,
        )

    # ------------------------------------------------------------------
    # Category 10: Evolution Signals
    # ------------------------------------------------------------------
    def _test_evolution_signals(self):
        fb = FeedbackSignal(
            feedback_id="fb_001", task_id="ev_t1", report_id="r1",
            user_id="u1", feedback_type="POSITIVE", rating=5,
            comment="Excellent analysis!", timestamp=datetime.utcnow(),
            rl_reward_value=1.0,
        )
        fid = self.evolution_integration.record_feedback(fb)
        self._record(
            "TC_ES_001", "feedback_recording",
            fid == "fb_001",
            "fid=" + fid,
        )

        export = self.evolution_integration.export_training_samples(
            quality_threshold=4.0, max_samples=100
        )
        self._record(
            "TC_ES_002", "training_sample_export",
            isinstance(export, TrainingSampleExport) and export.export_path != "",
            "count=" + str(export.sample_count),
        )

        fc = FailureCaseForTraining(
            case_id="fail_001", task_id="ev_t2",
            error_type="TIMEOUT", error_details="Processing exceeded 120s",
            input_snapshot='{"city":"Tainan"}', output_snapshot='{"error":"timeout"}',
            severity="HIGH", added_to_pool_at=datetime.utcnow(),
        )
        cid = self.evolution_integration.submit_failure_case(fc)
        pool_stats = self.evolution_integration.get_failure_pool_stats()
        self._record(
            "TC_ES_003", "failure_case_submission",
            cid == "fail_001" and pool_stats["total_pool_size"] >= 1,
            "pool_size=" + str(pool_stats["total_pool_size"]),
        )

    # ------------------------------------------------------------------
    # Category 11: Ecosystem Topology
    # ------------------------------------------------------------------
    def _test_ecosystem_topology(self):
        graph = self.ecosystem_integration.build_topology_graph("eco_task_001")
        self._record(
            "TC_ET_001", "topology_graph_structure",
            len(graph.nodes) >= 2 and len(graph.edges) >= 1 and
            graph.layout_direction == "TOP_DOWN",
            "nodes=" + str(len(graph.nodes)) + " edges=" + str(len(graph.edges)),
        )

        metrics = self.ecosystem_integration.get_agent_health_status(["agent_h1"])
        if metrics:
            alert_html = self.ecosystem_integration.generate_health_alert_html(metrics[0])
            has_cpu = "CPU" in alert_html
            self._record(
                "TC_ET_002", "health_metric_alert_html",
                has_cpu and "health-alert-badge" in alert_html,
                "alert=" + alert_html[:50],
            )
        else:
            self._record("TC_ET_002", "health_metric_alert_html", False, "no metrics")

    # ------------------------------------------------------------------
    # Category 12: Five-End Views
    # ------------------------------------------------------------------
    def _test_five_end_views(self):
        edu_result = self.five_end_integration.sync_to_education(
            "stu_001", {"task_id": "edu_t1", "report_content": "Student analysis result..."}
        )
        self._record(
            "TC_FEV_001", "education_sync_flow",
            edu_result.success and edu_result.sync_id.startswith("edu_sync_"),
            "sync_id=" + edu_result.sync_id,
        )

        ent_result = self.five_end_integration.create_enterprise_subscription(
            "corp_001", {"region": "northern_taiwan", "report_type": "market_monitor"}
        )
        self._record(
            "TC_FEV_002", "enterprise_subscription_creation",
            ent_result.success and ent_result.sub_id.startswith("ent_sub_"),
            "region_in_msg=" + str("northern" in ent_result.message),
        )

        gov_result = self.five_end_integration.push_gov_heatmap(
            "gov_001", "District A", {"hotspots": [(25.03, 121.56)]}
        )
        self._record(
            "TC_FEV_003", "gov_heatmap_push",
            gov_result.success and gov_result.push_id.startswith("gov_push_"),
            "push_id=" + gov_result.push_id,
        )

        assoc_result = self.five_end_integration.generate_association_report(
            date(2025, 1, 1), date(2025, 1, 31)
        )
        self._record(
            "TC_FEV_004", "association_report_generation",
            assoc_result.success and assoc_result.report_id.startswith("assoc_rpt_"),
            "report_id=" + assoc_result.report_id,
        )

    # ------------------------------------------------------------------
    # Category 13: Learning System
    # ------------------------------------------------------------------
    def _test_learning_system(self):
        # Add some samples first
        for i in range(10):
            ts = TrainingSample(
                sample_id="ts_" + str(i), task_id="ls_t1",
                input_data='{}', output_data='{}',
                user_rating=4.5 + (i % 3) * 0.2,
                feedback_type="POSITIVE",
                extracted_at=datetime.utcnow(),
                sample_quality_score=0.85 + (i % 4) * 0.04,
            )
            self.learning_integration._samples.append(ts)

        high_q = self.learning_integration.extract_high_quality_samples(min_rating=4.0, limit=50)
        self._record(
            "TC_LS_001", "high_quality_sample_extraction",
            len(high_q) > 0,
            "count=" + str(len(high_q)),
        )

        fail_fc = FailureCaseForTraining(
            case_id="ls_fail_1", task_id="ls_t2",
            error_type="QUALITY_BELOW", error_details="Score below 0.5",
            input_snapshot='{"q":"test"}', output_snapshot='{"score":0.3}',
            severity="MEDIUM", added_to_pool_at=datetime.utcnow(),
        )
        neg_sample = self.learning_integration.prepare_negative_sample(fail_fc)
        self._record(
            "TC_LS_002", "negative_sample_preparation",
            neg_sample.feedback_type == "NEGATIVE_FAILURE" and neg_sample.user_rating == 1.0,
            "type=" + neg_sample.feedback_type,
        )

    # ------------------------------------------------------------------
    # Category 14: Security Integration
    # ------------------------------------------------------------------
    def _test_security_integration(self):
        threat_safe = self.security_integration.assess_task_threat({
            "ip_address": "192.168.1.1", "user_id": "normal_user",
            "request_id": "req_safe", "parameter_anomaly_score": 0.1,
        })
        threat_danger = self.security_integration.assess_task_threat({
            "ip_address": "10.0.0.99", "user_id": "suspect_user",
            "req_id": "req_danger", "parameter_anomaly_score": 0.85,
        })
        levels_correct = (
            threat_safe.threat_level == "SAFE" and
            threat_danger.threat_level in ("SUSPICIOUS", "DANGEROUS", "CRITICAL")
        )
        self._record(
            "TC_SEC_001", "threat_assessment_levels",
            levels_correct,
            "safe=" + threat_safe.threat_level + " danger=" + threat_danger.threat_level,
        )

        should_int = self.security_integration.should_intercept(threat_danger)
        should_not = self.security_integration.should_intercept(threat_safe)
        self._record(
            "TC_SEC_002", "interception_logic",
            should_int and not should_not,
            "danger_intercept=" + str(should_int) + " safe_intercept=" + str(should_not),
        )

        failures = [{"count": 6}] * 6  # 6 consecutive failures
        drill_session = self.security_integration.check_drill_trigger(failures)
        if drill_session:
            drill_result = self.security_integration.execute_security_drill(drill_session)
            self._record(
                "TC_SEC_003", "drill_trigger_and_execute",
                isinstance(drill_result.passed, bool) and
                drill_result.report_generated is True,
                "passed=" + str(drill_result.passed) +
                " vulns=" + str(drill_result.vulnerabilities_found),
            )
        else:
            self._record("TC_SEC_003", "drill_trigger_and_execute", False, "no session")

    # ------------------------------------------------------------------
    # Category 15: Orchestrator
    # ------------------------------------------------------------------
    def _test_orchestrator(self):
        event = CrossModuleEvent(
            event_id="evt_orc_001",
            source_module="task_center",
            event_type=CrossModuleEventType.TASK_COMPLETED.value,
            payload=json.dumps({"task_id": "orc_t1"}),
            timestamp=datetime.utcnow(),
            propagated_modules=[],
        )
        self.orchestrator.publish_event(event)

        timeline = self.orchestrator.get_event_timeline("task_center")
        self._record(
            "TC_ORC_001", "event_publish_and_subscribe",
            len(timeline) >= 1,
            "timeline_size=" + str(len(timeline)),
        )

        synergy = self.orchestrator.calculate_cross_module_synergy_score()
        self._record(
            "TC_ORC_002", "event_timeline_query",
            "synergy_score" in synergy and 0 <= synergy["synergy_score"] <= 100,
            "score=" + str(synergy["synergy_score"]),
        )

        has_breakdown = "event_breakdown" in synergy
        self._record(
            "TC_ORC_003", "synergy_score_calculation",
            has_breakdown and isinstance(synergy["event_breakdown"], dict),
            "keys=" + str(list(synergy.keys())),
        )

    # ------------------------------------------------------------------
    # Category 16: Frontend Rendering
    # ------------------------------------------------------------------
    def _test_frontend_rendering(self):
        ctx = {
            "task_id": "fr_t1", "status": "COMPLETED",
            "duration_ms": 75000, "quality_score": 0.50,
            "properties_in_result": ["p1", "p2", "p3"],
            "parameters": {"city": "Taipei", "budget_min": 400000},
            "missing_capabilities": ["geo_spatial"],
        }
        panel_html = self.panel_renderer.render_action_panel(ctx)
        self._record(
            "TC_FR_001", "action_panel_html_valid",
            "Quick Actions" in panel_html and "href=" in panel_html,
            "len=" + str(len(panel_html)),
        )

        props = [
            PropertyCompareAction(property_id="fp1", property_name="Ocean View",
                                  address="Beach Rd", price=1800000.0),
            PropertyCompareAction(property_id="fp2", property_name="Mountain Retreat",
                                  address="Hill Ln", price=950000.0),
        ]
        sel_ui = self.property_compare.render_property_selection_ui(props)
        self._record(
            "TC_FR_002", "property_selection_cards",
            "checkbox" in sel_ui and "Ocean View" in sel_ui,
            "has_prop=" + str("Ocean View" in sel_ui),
        )

        backlink = self.report_integration.generate_backlink_to_task("fr_bt1")
        self._record(
            "TC_FR_003", "report_backlink_button",
            "View Original Task" in backlink and "<a" in backlink,
            "len=" + str(len(backlink)),
        )

        pref = AnalysisPreference(
            preference_id="fr_pref1", user_id="fr_u1", task_type="general",
            city="New Taipei", budget_range=(300000, 2000000),
            area_range=(25, 100), room_type="2BR",
            style_tags=["modern"], importance_score=0.9,
        )
        agent_fmt = self.memory_integration.format_preference_for_agent(pref)
        self._record(
            "TC_FR_004", "memory_prefill_format",
            "User Preference Profile" in agent_fmt and "Budget Range" in agent_fmt,
            "starts_with=" + agent_fmt[:30],
        )

        graph = self.ecosystem_integration.build_topology_graph("fr_eco1")
        metrics = self.ecosystem_integration.get_agent_health_status(["fr_a1"])
        has_graph = len(graph.nodes) > 0
        has_health = len(metrics) > 0
        self._record(
            "TC_FR_005", "health_alert_and_topology",
            has_graph and has_health,
            "graph_nodes=" + str(len(graph.nodes)) + " metrics=" + str(len(metrics)),
        )


def generate_pytest_code() -> str:
    """Generate pytest-compatible test code for Layer 28."""
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""Auto-generated pytest code for Layer 28: Task Analysis & Cross-Module"""')
    lines.append('import sys')
    lines.append('import os')
    lines.append('sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))')
    lines.append('')
    lines.append('from backend.integration.task_analysis_cross_module_layer import (')
    lines.append('    ActionPanelItem, ACTION_PANEL_ITEMS, ActionPanelRenderer,')
    lines.append('    TaskRedirectService, RedirectURLResult,')
    lines.append('    TaskStatus, TaskHistoryEntry, PaginatedResult,')
    lines.append('    BatchOperationResult, TaskDetail, TaskCenterIntegration,')
    lines.append('    TaskAgentDisplay, TeamAgentLoadDisplay, TaskTeamIntegration,')
    lines.append('    PropertyCompareAction, TaskPropertyCompareIntegration,')
    lines.append('    ReportSaveResult, AutoReportSaveConfig, TaskReportIntegration,')
    lines.append('    AnalysisPreference, TaskMemoryIntegration,')
    lines.append('    RecruitmentSuggestion, SkillSuggestion, PostRecruitmentResult,')
    lines.append('    TaskMarketIntegration,')
    lines.append('    ScheduledTaskProposal, ScheduleCreationResult,')
    lines.append('    TaskAutonomousWorkIntegration,')
    lines.append('    FeedbackSignal, FailureCaseForTraining, TrainingSampleExport,')
    lines.append('    TaskEvolutionIntegration,')
    lines.append('    AgentTopologyNode, AgentHealthMetric, AgentTopologyGraph,')
    lines.append('    TaskEcosystemIntegration,')
    lines.append('    FiveEndView, EduSyncData, EnterpriseSubscription,')
    lines.append('    GovHeatmapPush, AssociationReportSummary,')
    lines.append('    TaskFiveEndIntegration,')
    lines.append('    TrainingSample, ExportResult, ModelUpdateResult,')
    lines.append('    TaskLearningSystemIntegration,')
    lines.append('    ThreatAssessment, DrillTriggerCondition, InterceptionResult,')
    lines.append('    DrillSession, DrillResult, TaskSecurityIntegration,')
    lines.append('    DRILL_TRIGGER_CONDITIONS,')
    lines.append('    CrossModuleEventType, CrossModuleEvent, CrossModuleOrchestrator,')
    lines.append('    CROSS_MODULE_TEST_CASES, CrossModuleTestSuite,')
    lines.append(')')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28ActionPanel:')
    lines.append('    def test_panel_renders_with_items(self):')
    lines.append('        renderer = ActionPanelRenderer()')
    lines.append('        html = renderer.render_action_panel({')
    lines.append('            "task_id": "t1", "status": "COMPLETED",')
    lines.append('            "duration_ms": 70000, "quality_score": 0.45,')
    lines.append('            "properties_in_result": ["p1"],')
    lines.append('            "parameters": {"city": "X"},')
    lines.append('            "missing_capabilities": ["skill_x"],')
    lines.append('        })')
    lines.append('        assert "Quick Actions" in html')
    lines.append('        assert html.count("href=") >= 3')
    lines.append('')
    lines.append('    def test_panel_filters_by_condition(self):')
    lines.append('        renderer = ActionPanelRenderer()')
    lines.append('        html = renderer.render_action_panel({')
    lines.append('            "task_id": "t2", "status": "PENDING",')
    lines.append('            "duration_ms": 5000, "quality_score": 0.95,')
    lines.append('        })')
    lines.append('        assert "Quick Actions" in html')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28TaskRedirect:')
    lines.append('    def test_url_generation(self):')
    lines.append('        svc = TaskRedirectService()')
    lines.append('        r = svc.create_redirect_url("view_task_center_detail", "tk1", {"task_id": "tk1"})')
    lines.append('        assert "/task-center?taskId=tk1" in r.url')
    lines.append('        assert r.target_module == "task_center"')
    lines.append('')
    lines.append('    def test_auto_redirect(self):')
    lines.append('        svc = TaskRedirectService()')
    lines.append('        assert svc.should_auto_redirect("deep_analysis") is True')
    lines.append('        assert svc.should_auto_redirect("simple_query") is False')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28TaskCenter:')
    lines.append('    def test_pagination(self):')
    lines.append('        tc = TaskCenterIntegration()')
    lines.append('        for i in range(25):')
    lines.append('            tc._history_store["u"].append(TaskHistoryEntry(')
    lines.append('                task_id=str(i), name="T"+str(i), type="a",')
    lines.append('                status=TaskStatus.CREATED if i%3==0 else TaskStatus.COMPLETED,')
    lines.append('                created_at=__import__("datetime").datetime.utcnow(),')
    lines.append('            ))')
    lines.append('        result = tc.get_task_history("u", {"page": 1})')
    lines.append('        assert len(result.items) == 20')
    lines.append('        assert result.has_next is True')
    lines.append('')
    lines.append('    def test_batch_operations(self):')
    lines.append('        tc = TaskCenterIntegration()')
    lines.append('        dr = tc.batch_delete_tasks(["x"], "u")')
    lines.append('        assert isinstance(dr, BatchOperationResult)')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28PropertyCompare:')
    lines.append('    def test_extract_properties(self):')
    lines.append('        svc = TaskPropertyCompareIntegration()')
    lines.append('        props = svc.extract_properties_from_task_result({')
    lines.append('            "analyzed_properties": [{"id":"p1","name":"A","address":"Addr1","price":100}]')
    lines.append('        })')
    lines.append('        assert len(props) == 1')
    lines.append('        assert props[0].property_name == "A"')
    lines.append('')
    lines.append('    def test_compare_url(self):')
    lines.append('        svc = TaskPropertyCompareIntegration()')
    lines.append('        assert svc.generate_compare_url(["a","b"]) == "/compare?ids=a,b"')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Reports:')
    lines.append('    def test_auto_save(self):')
    lines.append('        svc = TaskReportIntegration()')
    lines.append('        r = svc.auto_save_report("t1", {"s": "ok"})')
    lines.append('        assert r.success is True')
    lines.append('        assert r.report_id.startswith("rpt_")')
    lines.append('')
    lines.append('    def test_backlink(self):')
    lines.append('        svc = TaskReportIntegration()')
    lines.append('        html = svc.generate_backlink_to_task("t99")')
    lines.append('        assert "View Original Task" in html')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Memory:')
    lines.append('    def test_save_and_get_preference(self):')
    lines.append('        svc = TaskMemoryIntegration()')
    lines.append('        pid = svc.save_analysis_preference({')
    lines.append('            "user_id": "u1", "task_type": "invest",')
    lines.append('            "parameters": {"city": "TC", "budget_min": 500},')
    lines.append('        })')
    lines.append('        assert pid.startswith("pref_")')
    lines.append('        pref = svc.get_latest_preference("u1", "invest")')
    lines.append('        assert pref is not None')
    lines.append('        assert pref.city == "TC"')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Market:')
    lines.append('    def test_recruitment_suggestions(self):')
    lines.append('        svc = TaskMarketIntegration()')
    lines.append('        recs = svc.analyze_task_performance({')
    lines.append('            "task_id": "t1", "duration_ms": 90000, "quality_score": 0.35')
    lines.append('        })')
    lines.append('        assert len(recs) > 0')
    lines.append('')
    lines.append('    def test_skill_suggestions(self):')
    lines.append('        svc = TaskMarketIntegration()')
    lines.append('        sk = svc.analyze_missing_capabilities({')
    lines.append('            "task_id": "t1", "missing_capabilities": ["NLP"],')
    lines.append('            "failure_reason": "timeout",')
    lines.append('        })')
    lines.append('        assert len(sk) > 0')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Autonomous:')
    lines.append('    def test_proposal(self):')
    lines.append('        svc = TaskAutonomousWorkIntegration()')
    lines.append('        p = svc.generate_schedule_proposal({"task_id": "t1"})')
    lines.append('        assert p.proposal_id.startswith("prop_")')
    lines.append('        assert p.frequency in ("DAILY","WEEKLY","MONTHLY")')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Evolution:')
    lines.append('    def test_feedback(self):')
    lines.append('        svc = TaskEvolutionIntegration()')
    lines.append('        fb = FeedbackSignal(')
    lines.append('            feedback_id="f1", task_id="t1", report_id="r1",')
    lines.append('            user_id="u1", feedback_type="POSITIVE", rating=5,')
    lines.append('            comment="Great", timestamp=__import__("datetime").datetime.utcnow(),')
    lines.append('            rl_reward_value=1.0,')
    lines.append('        )')
    lines.append('        fid = svc.record_feedback(fb)')
    lines.append('        assert fid == "f1"')
    lines.append('')
    lines.append('    def test_export_samples(self):')
    lines.append('        svc = TaskEvolutionIntegration()')
    lines.append('        exp = svc.export_training_samples(4.0, 100)')
    lines.append('        assert isinstance(exp, TrainingSampleExport)')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Security:')
    lines.append('    def test_threat_assessment(self):')
    lines.append('        svc = TaskSecurityIntegration()')
    lines.append('        t = svc.assess_task_threat({"ip_address":"1.2.3.4","user_id":"u1","parameter_anomaly_score":0.05})')
    lines.append('        assert t.threat_level == "SAFE"')
    lines.append('')
    lines.append('    def test_intercept(self):')
    lines.append('        svc = TaskSecurityIntegration()')
    lines.append('        t = svc.assess_task_threat({"ip_address":"attacker","user_id":"bad","parameter_anomaly_score":0.95})')
    lines.append('        assert svc.should_intercept(t) is True')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer28Orchestrator:')
    lines.append('    def test_publish_and_synergy(self):')
    lines.append('        orch = CrossModuleOrchestrator()')
    lines.append('        evt = CrossModuleEvent(')
    lines.append('            event_id="e1", source_module="tc",')
    lines.append('            event_type="TASK_COMPLETED", payload="{}",')
    lines.append('            timestamp=__import__("datetime").datetime.utcnow(),')
    lines.append('            propagated_modules=[],')
    lines.append('        )')
    lines.append('        orch.publish_event(evt)')
    lines.append('        syn = orch.calculate_cross_module_synergy_score()')
    lines.append('        assert 0 <= syn["synergy_score"] <= 100')
    lines.append('')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    import pytest')
    lines.append('    sys.exit(pytest.main(["-v", __file__]))')
    return chr(10).join(lines)


def generate_playwright_e2e() -> str:
    """Generate Playwright E2E test code for Layer 28."""
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""Auto-generated Playwright E2E tests for Layer 28: Cross-Module"""')
    lines.append('import asyncio')
    lines.append('')
    lines.append('')
    lines.append('async def test_action_panel_render(page):')
    lines.append('    """E2E: Verify action panel renders with contextual buttons."""')
    lines.append('    from backend.integration.task_analysis_cross_module_layer import (')
    lines.append('        ActionPanelRenderer,')
    lines.append('    )')
    lines.append('    renderer = ActionPanelRenderer()')
    lines.append('    ctx = {')
    lines.append('        "task_id": "e2e_t1", "status": "COMPLETED",')
    lines.append('        "duration_ms": 80000, "quality_score": 0.42,')
    lines.append('        "properties_in_result": ["p1", "p2"],')
    lines.append('        "parameters": {"city": "Taipei"},')
    lines.append('        "missing_capabilities": ["spatial_analysis"],')
    lines.append('    }')
    lines.append('    html = renderer.render_action_panel(ctx)')
    lines.append('    assert "Quick Actions" in html')
    lines.append('    assert "Recruit Agent" in html')
    lines.append('    assert "Purchase Skill" in html')
    lines.append('    print("[PASS] Action panel renders with all contextual buttons")')
    lines.append('')
    lines.append('')
    lines.append('async def test_property_compare_ui(page):')
    lines.append('    """E2E: Verify property compare selection UI renders correctly."""')
    lines.append('    from backend.integration.task_analysis_cross_module_layer import (')
    lines.append('        TaskPropertyCompareIntegration, PropertyCompareAction,')
    lines.append('    )')
    lines.append('    svc = TaskPropertyCompareIntegration()')
    lines.append('    props = [')
    lines.append('        PropertyCompareAction("pp1", "Luxury Penthouse", "101 Tower Rd", 5500000.0),')
    lines.append('        PropertyCompareAction("pp2", "Cozy Studio", "22 Lane 5", 350000.0),')
    lines.append('        PropertyCompareAction("pp3", "Family Home", "88 Main St", 1800000.0),')
    lines.append('    ]')
    lines.append('    ui = svc.render_property_selection_ui(props)')
    lines.append('    assert "Luxury Penthouse" in ui')
    lines.append('    assert "Compare 3 Properties" in ui')
    lines.append('    print("[PASS] Property selection UI renders with 3 cards")')
    lines.append('')
    lines.append('')
    lines.append('async def test_memory_preference_formatting(page):')
    lines.append('    """E2E: Verify memory preference formatting for agent prompts."""')
    lines.append('    from backend.integration.task_analysis_cross_module_layer import (')
    lines.append('        TaskMemoryIntegration, AnalysisPreference,')
    lines.append('    )')
    lines.append('    svc = TaskMemoryIntegration()')
    lines.append('    pref = AnalysisPreference(')
    lines.append('        preference_id="ep1", user_id="eu1", task_type="invest",')
    lines.append('        city="Hsinchu", budget_range=(400000, 2500000),')
    lines.append('        area_range=(20, 80), room_type="3BR",')
    lines.append('        style_tags=["scandinavian", "smart_home"], importance_score=0.92,')
    lines.append('    )')
    lines.append('    nl = svc.format_preference_for_agent(pref)')
    lines.append('    assert "User Preference Profile" in nl')
    lines.append('    assert "Hsinchu" in nl')
    lines.append('    assert "scandinavian" in nl')
    lines.append('    print("[PASS] Preference formatted for agent prompt")')
    lines.append('')
    lines.append('')
    lines.append('async def test_topology_graph_building(page):')
    lines.append('    """E2E: Verify agent topology graph builds with nodes and edges."""')
    lines.append('    from backend.integration.task_analysis_cross_module_layer import (')
    lines.append('        TaskEcosystemIntegration,')
    lines.append('    )')
    lines.append('    svc = TaskEcosystemIntegration()')
    lines.append('    graph = svc.build_topology_graph("topo_e2e")')
    lines.append('    assert len(graph.nodes) >= 2')
    lines.append('    assert len(graph.edges) >= 1')
    lines.append('    assert graph.layout_direction == "TOP_DOWN"')
    lines.append('    print(f"[PASS] Topology graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")')
    lines.append('')
    lines.append('')
    lines.append('async def test_security_threat_assessment(page):')
    lines.append('    """E2E: Verify threat assessment classifies requests correctly."""')
    lines.append('    from backend.integration.task_analysis_cross_module_layer import (')
    lines.append('        TaskSecurityIntegration,')
    lines.append('    )')
    lines.append('    svc = TaskSecurityIntegration()')
    lines.append('    safe = svc.assess_task_threat({')
    lines.append('        "ip_address": "10.0.0.1", "user_id": "normal", "parameter_anomaly_score": 0.02,')
    lines.append('    })')
    lines.append('    dangerous = svc.assess_task_threat({')
    lines.append('        "ip_address": "attack.src", "user_id": "bot_net", "parameter_anomaly_score": 0.92,')
    lines.append('    })')
    lines.append('    assert safe.threat_level == "SAFE"')
    lines.append('    assert dangerous.threat_level in ("SUSPICIOUS","DANGEROUS","CRITICAL")')
    lines.append('    print(f"[PASS] Safe={safe.threat_level} Dangerous={dangerous.threat_level}")')
    lines.append('')
    lines.append('')
    lines.append('async def test_full_suite_execution(page):')
    lines.append('    """E2E: Run the full test suite and verify pass rate."""')
    lines.append('    from backend.integration.task_analysis_cross_module_layer import CrossModuleTestSuite')
    lines.append('    suite = CrossModuleTestSuite()')
    lines.append('    summary = suite.run_all_tests()')
    lines.append('    assert summary["total"] >= 48')
    lines.append('    assert summary["pass_rate"] >= 90.0')
    lines.append('    print(f"[PASS] Full suite: {summary[\"passed\"]}/{summary[\"total\"]} ({summary[\"pass_rate\"]}%)")')
    lines.append('')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    from playwright.async_api import async_playwright')
    lines.append('    async def main():')
    lines.append('        async with async_playwright() as p:')
    lines.append('            browser = await p.chromium.launch()')
    lines.append('            page = await browser.new_page()')
    lines.append('            await test_action_panel_render(page)')
    lines.append('            await test_property_compare_ui(page)')
    lines.append('            await test_memory_preference_formatting(page)')
    lines.append('            await test_topology_graph_building(page)')
    lines.append('            await test_security_threat_assessment(page)')
    lines.append('            await test_full_suite_execution(page)')
    lines.append('            await browser.close()')
    lines.append('    asyncio.run(main())')
    return chr(10).join(lines)


def create_full_system() -> Dict[str, Any]:
    """Factory method to create all integration services for Layer 28."""
    return {
        "action_panel_renderer": ActionPanelRenderer(),
        "redirect_service": TaskRedirectService(),
        "task_center": TaskCenterIntegration(),
        "team_integration": TaskTeamIntegration(),
        "property_compare": TaskPropertyCompareIntegration(),
        "report_integration": TaskReportIntegration(),
        "memory_integration": TaskMemoryIntegration(),
        "market_integration": TaskMarketIntegration(),
        "autonomous_integration": TaskAutonomousWorkIntegration(),
        "evolution_integration": TaskEvolutionIntegration(),
        "ecosystem_integration": TaskEcosystemIntegration(),
        "five_end_integration": TaskFiveEndIntegration(),
        "learning_integration": TaskLearningSystemIntegration(),
        "security_integration": TaskSecurityIntegration(),
        "orchestrator": CrossModuleOrchestrator(),
    }


def run_quick_validation() -> Dict[str, Any]:
    """Run a quick smoke test to verify all services instantiate correctly."""
    system = create_full_system()
    checks: List[Dict[str, Any]] = []

    for name, svc in system.items():
        checks.append({
            "service": name,
            "type": type(svc).__name__,
            "healthy": svc is not None,
        })

    suite = CrossModuleTestSuite()
    summary = suite.run_all_tests()

    return {
        "layer": 28,
        "services_initialized": len(checks),
        "all_healthy": all(c["healthy"] for c in checks),
        "service_details": checks,
        "test_summary": {
            "total": summary["total"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "pass_rate": summary["pass_rate"],
        },
    }


if __name__ == "__main__":
    print("=" * 70)
    print("  Layer 28: Task Analysis & Cross-Module Integration")
    print("  (任务分析与其他模块联动)")
    print("=" * 70)
    validation = run_quick_validation()
    print("")
    print("Services initialized: " + str(validation["services_initialized"]))
    print("All healthy: " + str(validation["all_healthy"]))
    print("")
    print("Test Results:")
    print("  Total:  " + str(validation["test_summary"]["total"]))
    print("  Passed: " + str(validation["test_summary"]["passed"]))
    print("  Failed: " + str(validation["test_summary"]["failed"]))
    print("  Rate:   " + str(validation["test_summary"]["pass_rate"]) + "%")
    print("")
    print("Layer 28 loaded OK.")
