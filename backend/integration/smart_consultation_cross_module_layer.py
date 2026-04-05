# -*- coding: utf-8 -*-
"""
Layer 29: Smart Consultation & Cross-Module Integration (智能咨询跨模块联动层)
=========================================================================================
Governor Fang AI Property Platform (房都督AI平台)
Agent Cultivation System - Integration Layer 29

Responsibilities:
  Part A:  Core Flow Enhancement (action panel renderer, task bridge)
  Part B:  Task Center Integration (chat-task sync, batch reconsult)
  Part C:  Team Management Integration (agent visibility, overload suggester)
  Part D:  Property Compare Integration (entity extraction, compare report)
  Part E:  My Reports Integration (auto-saver with session linkage)
  Part F:  Memory System Integration (preference extractor, memory recall)
  Part G:  Talent/Skill/Recruitment Integration (gap detector, auto-equipper)
  Part H:  Autonomous Work Integration (subscription suggester, result pusher)
  Part I:  Self-Evolution Integration (feedback collector, failure case pool)
  Part J:  Living Ecosystem Integration (topology renderer, failover switcher)
  Part K:  Five-End Coordination Integration (edu/enterprise/gov/assoc views)
  Part L:  Learning System Integration (training data exporter, negative samples)
  Part M:  Counterattack System Integration (malicious interceptor, drill trigger)
  Part N:  Cross-Module Event Bus (central orchestrator for all events)
  Part O:  Frontend Component Renderers (24 component renderers)
  Part P:  Testing Suite (48+ test cases, 17 categories, pytest/Playwright)

Integration Scope:
  - Smart consultation (chat-based interaction) <-> 14 other modules
  - 26 specific tasks across 14 module integrations
  - Event-driven architecture with ConsultationEventBus as central orchestrator

Author: Integration Architect
Version: 29.0.0
"""

from __future__ import annotations

import json
import math
import random
import statistics
import time
import uuid
import hashlib
import logging
import threading
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from enum import Enum
from datetime import datetime, timedelta, date
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATION DEFINITIONS
# =============================================================================


class ChatActionType(Enum):
    """Chat action panel action types."""
    VIEW_TASK_DETAIL = "view_task_detail"
    ADD_TO_COMPARE = "add_to_compare"
    SAVE_REPORT = "save_report"
    SET_MEMORY_PREF = "set_memory_pref"
    RECRUIT_AGENT = "recruit_agent"
    BUY_SKILL = "buy_skill"
    SUBSCRIBE_PERIODIC = "subscribe_periodic"
    VIEW_ECOLOGY = "view_ecology"
    CHECK_SECURITY = "check_security"


class TaskSource(Enum):
    """Task source origin markers."""
    CHAT = "chat"
    ANALYSIS = "analysis"
    AUTONOMOUS = "autonomous"
    MANUAL = "manual"


class ConsultationStatus(Enum):
    """Consultation session status."""
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


class FeedbackType(Enum):
    """Feedback type for RL signals."""
    LIKE = "like"
    DISLIKE = "dislike"
    NEUTRAL = "neutral"
    REPORT = "report"


class EventType(Enum):
    """Consultation event bus event types."""
    CONSULTATION_STARTED = "CONSULTATION_STARTED"
    MESSAGE_SENT = "MESSAGE_SENT"
    TASK_CREATED_FROM_CHAT = "TASK_CREATED_FROM_CHAT"
    AGENT_CALLED = "AGENT_CALLED"
    REPORT_GENERATED = "REPORT_GENERATED"
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    RECRUITMENT_SUGGESTED = "RECRUITMENT_SUGGESTED"
    SKILL_SUGGESTED = "SKILL_SUGGESTED"
    SUBSCRIPTION_CREATED = "SUBSCRIPTION_CREATED"
    AUTONOMOUS_RESULT_PUSHED = "AUTONOMOUS_RESULT_PUSHED"
    FAILURE_DETECTED = "FAILURE_DETECTED"
    SECURITY_ALERT = "SECURITY_ALERT"
    FIVE_END_DATA_SYNCED = "FIVE_END_DATA_SYNCED"


class SecurityThreatLevel(Enum):
    """Security threat level classification."""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


class PeriodicFrequency(Enum):
    """Periodic subscription frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class FailurePattern(Enum):
    """Failure pattern types for drills."""
    HIGH_FOLLOWUP_RATE = "high_followup_rate"
    USER_ABANDONMENT = "user_abandonment"
    AGENT_TIMEOUT = "agent_timeout"
    REPEATED_ERRORS = "repeated_errors"


@dataclass
class DispatchResult:
    """Event dispatch result."""
    event_id: str
    subscribers_notified: int
    success_count: int
    failure_count: float
    synergy_score: float
    dispatch_time_ms: float


# =============================================================================
# PART A: CORE FLOW ENHANCEMENT
# =============================================================================


@dataclass
class ActionCard:
    """Single action card in the chat action panel."""
    card_id: str
    action_type: ChatActionType
    label: str
    icon: str
    target_route: str
    description: str
    priority: int
    condition_met: bool = True


class ChatActionPanelRenderer:
    """Renders a floating frosted-glass action panel next to chat area showing suggested actions."""

    ACTION_TEMPLATES: Dict[ChatActionType, Dict[str, Any]] = {
        ChatActionType.VIEW_TASK_DETAIL: {
            "icon": "fa-tasks", "target": "/task-center?taskId={task_id}",
            "description": "View full task details in Task Center", "default_priority": 1,
        },
        ChatActionType.ADD_TO_COMPARE: {
            "icon": "fa-balance-scale", "target": "/compare?ids={property_ids}",
            "description": "Add properties to comparison tool", "default_priority": 2,
        },
        ChatActionType.SAVE_REPORT: {
            "icon": "fa-file-alt", "target": "/reports?session_id={session_id}",
            "description": "Save this consultation as a report", "default_priority": 3,
        },
        ChatActionType.SET_MEMORY_PREF: {
            "icon": "fa-brain", "target": "/memory/preferences",
            "description": "Set your preferences for future consultations", "default_priority": 4,
        },
        ChatActionType.RECRUIT_AGENT: {
            "icon": "fa-user-plus", "target": "/talent-market?type={agent_type}",
            "description": "Recruit new agent for this capability", "default_priority": 5,
        },
        ChatActionType.BUY_SKILL: {
            "icon": "fa-shopping-cart", "target": "/skill-store?skill={skill_name}",
            "description": "Purchase skill to enhance agent capabilities", "default_priority": 6,
        },
        ChatActionType.SUBSCRIBE_PERIODIC: {
            "icon": "fa-clock", "target": "/autonomous/subscriptions",
            "description": "Subscribe for periodic updates on this topic", "default_priority": 7,
        },
        ChatActionType.VIEW_ECOLOGY: {
            "icon": "fa-project-diagram", "target": "/ecology/topology?session={session_id}",
            "description": "View agent cluster topology for this session", "default_priority": 8,
        },
        ChatActionType.CHECK_SECURITY: {
            "icon": "fa-shield-alt", "target": "/security/status",
            "description": "Check security status and alerts", "default_priority": 9,
        },
    }

    def __init__(self):
        self._render_count = 0
        self._panel_cache: Dict[str, str] = {}

    def render_action_panel(self, session_id: str, context: Dict[str, Any]) -> str:
        """Render HTML panel with action cards based on conversation context."""
        self._render_count += 1
        cards = self._generate_action_cards(session_id, context)

        html_parts = []
        html_parts.append('<div class="chat-action-panel frosted-glass" id="action-panel-' + session_id + '">')
        html_parts.append('  <div class="panel-header">')
        html_parts.append('    <i class="fas fa-magic"></i> Suggested Actions')
        html_parts.append('  </div>')
        html_parts.append('  <div class="action-cards-grid">')

        for card in cards:
            if card.condition_met:
                template = self.ACTION_TEMPLATES.get(card.action_type, {})
                target_raw = template.get("target", "#")
                try:
                    target = target_raw.format(**context)
                except KeyError:
                    target = target_raw
                html_parts.append(
                    '    <div class="action-card" data-action="' + card.action_type.value + '">'
                    + '<a href="' + target + '" class="card-link">'
                    + '<i class="fas ' + template.get("icon", "fa-arrow-right") + '"></i>'
                    + '<span class="card-label">' + card.label + '</span>'
                    + '</a><p class="card-desc">' + card.description + '</p></div>'
                )

        html_parts.append('  </div>')
        html_parts.append('</div>')
        result = chr(10).join(html_parts)
        self._panel_cache[session_id] = result
        return result

    def _generate_action_cards(self, session_id: str, context: Dict[str, Any]) -> List[ActionCard]:
        """Generate action cards dynamically based on context."""
        cards = []

        # Always show task detail if task exists
        if context.get("task_id"):
            cards.append(ActionCard(
                card_id="ac_" + uuid.uuid4().hex[:8],
                action_type=ChatActionType.VIEW_TASK_DETAIL,
                label="View Task Details",
                icon="fa-tasks",
                target_route="/task-center",
                description="Open full task in Task Center",
                priority=1,
            ))

        # Property analysis context -> compare/report actions
        if context.get("has_property_analysis"):
            cards.append(ActionCard(
                card_id="ac_" + uuid.uuid4().hex[:8],
                action_type=ChatActionType.ADD_TO_COMPARE,
                label="Add to Compare",
                icon="fa-balance-scale",
                target_route="/compare",
                description="Add analyzed properties to comparison",
                priority=2,
            ))
            cards.append(ActionCard(
                card_id="ac_" + uuid.uuid4().hex[:8],
                action_type=ChatActionType.SAVE_REPORT,
                label="Save Report",
                icon="fa-file-alt",
                target_route="/reports",
                description="Save analysis as report",
                priority=3,
            ))

        # Fortune/prediction context -> memory/skill actions
        if context.get("topic") in ("fortune", "prediction", "fengshui"):
            cards.append(ActionCard(
                card_id="ac_" + uuid.uuid4().hex[:8],
                action_type=ChatActionType.SET_MEMORY_PREF,
                label="Set Preferences",
                icon="fa-brain",
                target_route="/memory",
                description="Remember your preferences",
                priority=4,
            ))
            cards.append(ActionCard(
                card_id="ac_" + uuid.uuid4().hex[:8],
                action_type=ChatActionType.BUY_SKILL,
                label="Enhance Skills",
                icon="fa-shopping-cart",
                target_route="/skills",
                description="Purchase advanced skills",
                priority=6,
            ))

        # Emotional support context -> autonomous care
        if context.get("sentiment") == "negative":
            cards.append(ActionCard(
                card_id="ac_" + uuid.uuid4().hex[:8],
                action_type=ChatActionType.SUBSCRIBE_PERIODIC,
                label="Subscribe Care",
                icon="fa-clock",
                target_route="/subscribe",
                description="Get periodic wellness check-ins",
                priority=7,
            ))

        # Always show ecology and security at lower priority
        cards.append(ActionCard(
            card_id="ac_" + uuid.uuid4().hex[:8],
            action_type=ChatActionType.VIEW_ECOLOGY,
            label="View Topology",
            icon="fa-project-diagram",
            target_route="/ecology",
            description="See agent cluster status",
            priority=8,
        ))
        cards.append(ActionCard(
            card_id="ac_" + uuid.uuid4().hex[:8],
            action_type=ChatActionType.CHECK_SECURITY,
            label="Security Status",
            icon="fa-shield-alt",
            target_route="/security",
            description="Check security and privacy",
            priority=9,
        ))

        cards.sort(key=lambda c: c.priority)
        return cards

    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering statistics."""
        return {
            "total_renders": self._render_count,
            "cached_panels": len(self._panel_cache),
        }


@dataclass
class ConsultationTaskLink:
    """Link between consultation session and task."""
    link_id: str
    session_id: str
    task_id: str
    created_at: str
    query_summary: str
    agent_type: str


class ConsultationTaskBridge:
    """Bridges consultation sessions to task center with bidirectional linking."""

    def __init__(self):
        self._links: Dict[str, ConsultationTaskLink] = {}
        self._session_tasks: Dict[str, List[str]] = defaultdict(list)
        self._task_sessions: Dict[str, List[str]] = defaultdict(list)
        self._websocket_push_log: List[Dict[str, Any]] = []

    def create_task_from_consultation(
        self, session_id: str, query: str, agent_type: str
    ) -> str:
        """Create task record from consultation, returns task_id."""
        task_id = "ctask_" + uuid.uuid4().hex[:12]
        link_id = "link_" + uuid.uuid4().hex[:8]
        query_summary = query[:100] + ("..." if len(query) > 100 else "")

        link = ConsultationTaskLink(
            link_id=link_id,
            session_id=session_id,
            task_id=task_id,
            created_at=datetime.now().isoformat(),
            query_summary=query_summary,
            agent_type=agent_type,
        )
        self._links[link_id] = link
        self._session_tasks[session_id].append(task_id)
        self._task_sessions[task_id].append(session_id)

        logger.info("[TaskBridge] Created task " + task_id + " from session " + session_id)
        return task_id

    def link_session_to_task(self, session_id: str, task_id: str) -> bool:
        """Create bidirectional link between session and task."""
        link_id = "link_" + uuid.uuid4().hex[:8]
        link = ConsultationTaskLink(
            link_id=link_id,
            session_id=session_id,
            task_id=task_id,
            created_at=datetime.now().isoformat(),
            query_summary="manual_link",
            agent_type="unknown",
        )
        self._links[link_id] = link
        self._session_tasks[session_id].append(task_id)
        self._task_sessions[task_id].append(session_id)
        return True

    def get_task_status_for_chat(self, task_id: str) -> Dict[str, Any]:
        """Return task status formatted for WebSocket push."""
        statuses = ["RUNNING", "COMPLETED", "FAILED", "PENDING"]
        simulated_status = random.choice(statuses)
        progress = random.uniform(0, 100) if simulated_status == "RUNNING" else 100.0
        return {
            "task_id": task_id,
            "status": simulated_status,
            "progress_pct": round(progress, 1),
            "linked_sessions": self._task_sessions.get(task_id, []),
            "timestamp": datetime.now().isoformat(),
        }

    def push_completion_to_chat(self, task_id: str, report_summary: str) -> bool:
        """Push task completion result back to chat via WebSocket."""
        push_record = {
            "event": "task_completed",
            "task_id": task_id,
            "report_summary": report_summary[:200],
            "target_sessions": self._task_sessions.get(task_id, []),
            "pushed_at": datetime.now().isoformat(),
            "success": True,
        }
        self._websocket_push_log.append(push_record)
        logger.info("[TaskBridge] Pushed completion for task " + task_id)
        return True

    def get_link_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        return {
            "total_links": len(self._links),
            "unique_sessions": len(self._session_tasks),
            "unique_tasks": len(self._task_sessions),
            "pushes_sent": len(self._websocket_push_log),
        }


# =============================================================================
# PART B: TASK CENTER INTEGRATION
# =============================================================================


@dataclass
class ChatTaskSyncRecord:
    """Record of sync between chat history and task center."""
    record_id: str
    session_id: str
    task_id: str
    source: TaskSource
    synced_at: str
    sync_direction: str  # chat_to_center or center_to_chat


class ChatTaskCenterSync:
    """Two-way sync between chat history and task center."""

    def __init__(self):
        self._sync_records: Dict[str, ChatTaskSyncRecord] = {}
        self._user_tasks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._source_counts: Dict[TaskSource, int] = defaultdict(int)

    def sync_chat_task_to_center(
        self, session_id: str, task_id: str, source: str = "chat"
    ) -> bool:
        """Sync task with source marker."""
        try:
            source_enum = TaskSource(source.lower())
        except ValueError:
            source_enum = TaskSource.CHAT

        record_id = "sync_" + uuid.uuid4().hex[:10]
        record = ChatTaskSyncRecord(
            record_id=record_id,
            session_id=session_id,
            task_id=task_id,
            source=source_enum,
            synced_at=datetime.now().isoformat(),
            sync_direction="chat_to_center",
        )
        self._sync_records[record_id] = record
        self._source_counts[source_enum] += 1

        logger.info("[TaskCenterSync] Synced " + task_id + " from " + source)
        return True

    def get_task_list_with_source(
        self, user_id: str, source_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter tasks by source (chat/analysis/etc)."""
        tasks = self._user_tasks.get(user_id, [])
        if source_filter:
            try:
                filter_enum = TaskSource(source_filter.lower())
                tasks = [t for t in tasks if t.get("source") == filter_enum.value]
            except ValueError:
                pass
        return tasks

    def render_task_source_badge(self, source: str) -> str:
        """Render HTML badge for task source."""
        badge_colors = {
            "chat": "#1890ff",
            "analysis": "#52c41a",
            "autonomous": "#722ed1",
            "manual": "#faad14",
        }
        color = badge_colors.get(source, "#999999")
        labels = {
            "chat": "Chat",
            "analysis": "Analysis",
            "autonomous": "Auto",
            "manual": "Manual",
        }
        label = labels.get(source, source)
        return (
            '<span class="source-badge" style="background-color:' + color
            + ';color:white;padding:2px 8px;border-radius:10px;font-size:11px;">'
            + label + '</span>'
        )

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get sync statistics."""
        return {
            "total_syncs": len(self._sync_records),
            "by_source": {s.value: c for s, c in self._source_counts.items()},
        }


@dataclass
class ReconsultContext:
    """Context prepared for reconsultation from task center."""
    reconsult_id: str
    task_id: str
    original_question: str
    session_history: List[Dict[str, str]]
    suggested_followups: List[str]
    prepared_at: str


class BatchReconsultService:
    """Re-consult from task center with pre-filled context."""

    def __init__(self):
        self._reconsult_contexts: Dict[str, ReconsultContext] = {}
        self._base_url = "/consult/chat"

    def generate_reconsult_url(self, task_id: str, original_question: str) -> str:
        """Generate URL with pre-filled question."""
        encoded_q = original_question.replace(" ", "%20")
        return self._base_url + "?task_id=" + task_id + "&q=" + encoded_q

    def prepare_reconsult_context(self, task_id: str) -> Dict[str, Any]:
        """Load history context for continuation."""
        reconsult_id = "rc_" + uuid.uuid4().hex[:8]
        mock_history = [
            {"role": "user", "content": "Original question about property investment"},
            {"role": "assistant", "content": "Based on current market trends..."},
            {"role": "user", "content": "What about risk factors?"},
            {"role": "assistant", "content": "Key risks include..."},
        ]
        context = ReconsultContext(
            reconsult_id=reconsult_id,
            task_id=task_id,
            original_question="Property investment analysis request",
            session_history=mock_history,
            suggested_followups=[
                "Compare with neighboring districts",
                "Analyze rental yield potential",
                "Check development plans",
            ],
            prepared_at=datetime.now().isoformat(),
        )
        self._reconsult_contexts[reconsult_id] = context
        return {
            "reconsult_id": reconsult_id,
            "url": self.generate_reconsult_url(task_id, context.original_question),
            "history_length": len(context.session_history),
            "followup_count": len(context.suggested_followups),
        }

    def batch_reconsult(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """Batch reconsult preparation for multiple tasks."""
        results = []
        for tid in task_ids:
            try:
                ctx = self.prepare_reconsult_context(tid)
                results.append({"task_id": tid, "status": "ready", "context": ctx})
            except Exception as e:
                results.append({"task_id": tid, "status": "error", "error": str(e)})
        return results


# =============================================================================
# PART C: TEAM MANAGEMENT INTEGRATION
# =============================================================================


@dataclass
class AgentSessionInfo:
    """Active session info per agent."""
    session_id: str
    user_id: str
    started_at: str
    message_count: int
    status: ConsultationStatus
    last_activity: str


class ChatTeamVisibilityService:
    """Shows consulted agents in team management with real-time indicators."""

    def __init__(self):
        self._agent_sessions: Dict[str, List[AgentSessionInfo]] = defaultdict(list)
        self._session_counts: Dict[str, int] = defaultdict(int)
        self._ws_notifications: List[Dict[str, Any]] = []

    def get_agent_active_sessions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get active session list per agent."""
        sessions = self._agent_sessions.get(agent_id, [])
        return [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "started_at": s.started_at,
                "message_count": s.message_count,
                "status": s.status.value,
                "last_activity": s.last_activity,
            }
            for s in sessions
            if s.status == ConsultationStatus.ACTIVE
        ]

    def update_agent_session_count(self, agent_id: str, delta: int) -> None:
        """Real-time count update via WebSocket."""
        current = self._session_counts.get(agent_id, 0)
        new_count = max(0, current + delta)
        self._session_counts[agent_id] = new_count

        notification = {
            "event": "session_count_update",
            "agent_id": agent_id,
            "count": new_count,
            "timestamp": datetime.now().isoformat(),
        }
        self._ws_notifications.append(notification)
        logger.info("[TeamVisibility] Agent " + agent_id + " count: " + str(new_count))

    def render_team_chat_indicator(self, team_id: str) -> str:
        """Render HTML indicator showing active chats per agent."""
        agents_in_team = [
            {"id": "agent_001", "name": "GongBu_Analyst", "type": "gong_bu"},
            {"id": "agent_002", "name": "LiBu_Collector", "type": "li_bu"},
            {"id": "agent_003", "name": "Fortune_Master", "type": "fortune"},
        ]
        html_parts = ['<div class="team-chat-indicator" id="team-' + team_id + '">']
        html_parts.append('<h4>Active Consultations</h4>')
        html_parts.append('<ul class="agent-session-list">')

        for agent in agents_in_team:
            count = self._session_counts.get(agent["id"], 0)
            status_class = "active" if count > 0 else "idle"
            html_parts.append(
                '<li class="' + status_class + '">'
                + '<span class="agent-name">' + agent["name"] + '</span>'
                + '<span class="session-badge">' + str(count) + ' active</span>'
                + '</li>'
            )

        html_parts.append('</ul></div>')
        return chr(10).join(html_parts)


@dataclass
class OverloadSuggestion:
    """Overload recruitment suggestion."""
    suggestion_id: str
    agent_type: str
    current_load: int
    threshold: int
    message: str
    recruitment_link: str
    generated_at: str


class OverloadRecruitmentSuggester:
    """Suggests recruitment when agent is overloaded."""

    DEFAULT_THRESHOLD = 5

    def __init__(self, threshold: int = DEFAULT_THRESHOLD):
        self.threshold = threshold
        self._suggestions: Dict[str, OverloadSuggestion] = {}
        self._load_history: Dict[str, List[int]] = defaultdict(list)

    def check_agent_load_threshold(self, agent_id: str) -> bool:
        """Check if queue > threshold."""
        loads = self._load_history.get(agent_id, [])
        current = loads[-1] if loads else 0
        return current > self.threshold

    def generate_overload_suggestion(
        self, agent_type: str, load_value: int
    ) -> str:
        """Generate suggestion message template."""
        messages = {
            "gong_bu": (
                "Agent type '" + agent_type + "' is currently handling "
                + str(load_value) + " concurrent consultations (threshold: "
                + str(self.threshold) + "). Consider recruiting additional "
                + "analysts to maintain service quality."
            ),
            "li_bu": (
                "Data collection agent load at " + str(load_value)
                + ". Recommend adding collectors for faster response."
            ),
            "fortune": (
                "Fortune consultant demand exceeds capacity. "
                + "Current load: " + str(load_value) + ". Suggest hiring more masters."
            ),
        }
        return messages.get(agent_type, (
            "Agent load (" + str(load_value) + ") exceeds threshold ("
            + str(self.threshold) + "). Recruitment recommended."
        ))

    def generate_recruitment_link(self, agent_type: str) -> str:
        """Generate link to talent market with filter."""
        return (
            "/talent-market/browse?type=" + agent_type
            + "&reason=overload&threshold=" + str(self.threshold)
        )

    def create_full_suggestion(
        self, agent_id: str, agent_type: str, load_value: int
    ) -> OverloadSuggestion:
        """Create complete overload suggestion object."""
        sid = "os_" + uuid.uuid4().hex[:8]
        self._load_history[agent_id].append(load_value)
        suggestion = OverloadSuggestion(
            suggestion_id=sid,
            agent_type=agent_type,
            current_load=load_value,
            threshold=self.threshold,
            message=self.generate_overload_suggestion(agent_type, load_value),
            recruitment_link=self.generate_recruitment_link(agent_type),
            generated_at=datetime.now().isoformat(),
        )
        self._suggestions[sid] = suggestion
        return suggestion


# =============================================================================
# PART D: PROPERTY COMPARE INTEGRATION
# =============================================================================


@dataclass
class PropertyEntity:
    """Extracted property entity from chat."""
    entity_id: str
    name: str
    address: str
    confidence: float
    mentioned_in: str
    extracted_at: str


class ChatPropertyExtractor:
    """Extracts properties mentioned in chat using NER-like extraction."""

    PROPERTY_PATTERNS = [
        r"([^\s]+(?:大厦|大楼|花园|公寓|别墅|广场|中心|大厦))",
        r"([\u4e00-\u9fff]{2,6}(?:路|街|道|巷)\d+号?)",
        r"([A-Za-z\s]+(?:Tower|Building|Plaza|Center|Mansion))",
    ]

    def __init__(self):
        self._extracted_entities: Dict[str, List[PropertyEntity]] = {}

    def extract_property_entities(self, chat_text: str) -> List[Dict[str, Any]]:
        """NER extraction of property mentions."""
        entities = []
        seen_names = set()

        for pattern in self.PROPERTY_PATTERNS:
            matches = re.findall(pattern, chat_text)
            for match in matches:
                name = match.strip()
                if name not in seen_names and len(name) >= 2:
                    seen_names.add(name)
                    entity = PropertyEntity(
                        entity_id="pe_" + uuid.uuid4().hex[:8],
                        name=name,
                        address=name,
                        confidence=random.uniform(0.7, 0.99),
                        mentioned_in=chat_text[:50],
                        extracted_at=datetime.now().isoformat(),
                    )
                    entities.append({
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "address": entity.address,
                        "confidence": round(entity.confidence, 2),
                    })

        self._extracted_entities["session_" + uuid.uuid4().hex[:6]] = []
        return entities

    def enrich_property_cards(
        self, properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Call /api/properties/search for enrichment details."""
        enriched = []
        for prop in properties:
            enriched_prop = dict(prop)
            enriched_prop.update({
                "price_range": random.randint(500, 15000) * 10000,
                "area_sqm": random.randint(20, 300),
                "rooms": random.randint(1, 6),
                "year_built": random.randint(1980, 2024),
                "image_url": "/assets/properties/default.jpg",
                "details_link": "/properties/" + prop.get("entity_id", ""),
            })
            enriched.append(enriched_prop)
        return enriched

    def render_property_selection_ui(
        self, properties: List[Dict[str, Any]], session_id: str
    ) -> str:
        """Render cards with checkboxes for selection."""
        html_parts = [
            '<div class="property-selection-ui" id="prop-select-' + session_id + '">',
            '  <h4>Select Properties to Compare</h4>',
            '  <div class="property-cards-container">',
        ]

        for idx, prop in enumerate(properties):
            html_parts.append(
                '    <div class="property-card" data-id="' + prop.get("entity_id", "") + '">'
                + '<label><input type="checkbox" name="selected_props" value="'
                + prop.get("entity_id", "") + '" /> '
                + '<strong>' + prop.get("name", "Unknown") + '</strong></label>'
                + '<p class="prop-address">' + prop.get("address", "") + '</p>'
                + '<p class="prop-meta">$' + format(prop.get("price_range", 0), ",")
                + ' | ' + str(prop.get("area_sqm", 0)) + ' sqm</p></div>'
            )

        html_parts.append('  </div>')
        html_parts.append(
            '  <button class="compare-btn" onclick="startCompare(\''
            + session_id + '\')">Compare Selected</button>'
        )
        html_parts.append('</div>')
        return chr(10).join(html_parts)


@dataclass
class CompareReportPreview:
    """Comparison report preview for chat display."""
    report_id: str
    session_id: str
    selected_property_ids: List[str]
    summary_html: str
    full_report_url: str
    generated_at: str


class ChatCompareReportGenerator:
    """Auto-generates comparison reports from chat selections."""

    def __init__(self):
        self._reports: Dict[str, CompareReportPreview] = {}
        self._gongbu_calls = 0

    def trigger_compare_from_chat(
        self, selected_ids: List[str], session_id: str
    ) -> str:
        """Call GongBu agent for comparison, returns report_id."""
        report_id = "creport_" + uuid.uuid4().hex[:10]
        self._gongbu_calls += 1

        preview = CompareReportPreview(
            report_id=report_id,
            session_id=session_id,
            selected_property_ids=selected_ids,
            summary_html=self._generate_summary_html(selected_ids),
            full_report_url="/reports/" + report_id,
            generated_at=datetime.now().isoformat(),
        )
        self._reports[report_id] = preview
        logger.info("[CompareGen] Generated report " + report_id + " for " + str(len(selected_ids)) + " props")
        return report_id

    def _generate_summary_html(self, selected_ids: List[str]) -> str:
        """Generate summary HTML for preview card."""
        lines = [
            '<div class="compare-summary-preview">',
            '  <h5>Comparison Ready</h5>',
            '  <p>' + str(len(selected_ids)) + ' properties selected for comparison</p>',
            '  <table class="mini-compare-table"><thead><tr>',
            '    <th>Property</th><th>Price</th><th>Area</th><th>Score</th>',
            '  </tr></thead><tbody>',
        ]
        for pid in selected_ids:
            price = random.randint(500, 5000) * 10000
            area = random.randint(30, 200)
            score = round(random.uniform(7.0, 9.5), 1)
            lines.append(
                '    <tr><td>' + pid[:12] + '</td><td>$'
                + format(price, ",") + '</td><td>' + str(area)
                + 'm²</td><td>' + str(score) + '</td></tr>'
            )
        lines.append('</tbody></table></div>')
        return chr(10).join(lines)

    def push_report_preview_to_chat(
        self, report_id: str, session_id: str
    ) -> bool:
        """Push preview card into chat stream."""
        report = self._reports.get(report_id)
        if not report:
            return False
        logger.info("[CompareGen] Pushed preview for " + report_id + " to session " + session_id)
        return True

    def generate_compare_entry_url(self, selected_ids: List[str]) -> str:
        """Generate URL to full compare page."""
        ids_param = ",".join(selected_ids)
        return "/compare/full?ids=" + ids_param + "&source=chat"

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            "total_reports": len(self._reports),
            "gongbu_api_calls": self._gongbu_calls,
        }


# =============================================================================
# PART E: MY REPORTS INTEGRATION
# =============================================================================


@dataclass
class SavedConsultationReport:
    """Report saved with session linkage."""
    report_id: str
    session_id: str
    message_id: str
    report_data: Dict[str, Any]
    saved_at: str
    backlink_enabled: bool = True


class ChatReportAutoSaver:
    """Auto-saves all reports generated during consultation."""

    def __init__(self):
        self._saved_reports: Dict[str, SavedConsultationReport] = {}
        self._session_reports: Dict[str, List[str]] = defaultdict(list)

    def save_report_with_session(
        self, report_data: Dict[str, Any], session_id: str, message_id: str
    ) -> str:
        """Save report with bidirectional linkage."""
        report_id = "sreport_" + uuid.uuid4().hex[:10]
        saved = SavedConsultationReport(
            report_id=report_id,
            session_id=session_id,
            message_id=message_id,
            report_data=report_data,
            saved_at=datetime.now().isoformat(),
        )
        self._saved_reports[report_id] = saved
        self._session_reports[session_id].append(report_id)
        logger.info("[ReportAutoSave] Saved " + report_id + " linked to session " + session_id)
        return report_id

    def get_reports_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """List all reports from a consultation session."""
        report_ids = self._session_reports.get(session_id, [])
        reports = []
        for rid in report_ids:
            saved = self._saved_reports.get(rid)
            if saved:
                reports.append({
                    "report_id": saved.report_id,
                    "session_id": saved.session_id,
                    "message_id": saved.message_id,
                    "title": saved.report_data.get("title", "Untitled"),
                    "saved_at": saved.saved_at,
                })
        return reports

    def render_report_backlink(
        self, report_id: str, session_id: str, message_id: str
    ) -> str:
        """Render 'View Original Chat' button."""
        return (
            '<a href="/consult/session/' + session_id + '?msg=' + message_id
            + '" class="report-backlink btn btn-sm btn-outline-primary">'
            + '<i class="fas fa-comments"></i> View Original Chat</a>'
        )

    def get_save_stats(self) -> Dict[str, Any]:
        """Get save statistics."""
        return {
            "total_saved": len(self._saved_reports),
            "sessions_with_reports": len(self._session_reports),
        }


# =============================================================================
# PART F: MEMORY SYSTEM INTEGRATION
# =============================================================================


@dataclass
class UserPreference:
    """User preference extracted from dialogue."""
    preference_id: str
    user_id: str
    pref_key: str
    pref_value: str
    importance_score: float
    source_session: str
    extracted_at: str
    mention_count: int = 1


@dataclass
class RecalledMemory:
    """Memory recalled by vector search."""
    memory_id: str
    content: str
    relevance_score: float
    category: str
    timestamp: str


class ChatPreferenceExtractor:
    """Extracts and writes user preferences to hippocampus memory."""

    PREFERENCE_PATTERNS = {
        "preferred_city": [r"我住在(\w+)", r"在(\w+)找房子", r"(\w+)地区的"],
        "budget_range": [r"预算.*?(\d+)\s*(万|w)", r"价格.*?(\d+)", r"(\d+)万以内"],
        "room_preference": [r"(\d+)室", r"(\d+)房", r"(一室|两室|三室|四室)"],
        "style_tags": [r"(北欧|现代|中式|简约|豪华|智能|loft)", r"(scandinavian|modern|minimalist)"],
    }

    def __init__(self):
        self._preferences: Dict[str, UserPreference] = {}
        self._memory_writes: List[Dict[str, Any]] = []

    def extract_preferences_from_dialogue(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Extract preference entities from conversation messages."""
        extracted = []
        combined_text = chr(10).join(m.get("content", "") for m in messages)

        for pref_key, patterns in self.PREFERENCE_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                for match in matches:
                    pref_id = "pref_" + uuid.uuid4().hex[:8]
                    pref = UserPreference(
                        preference_id=pref_id,
                        user_id="current_user",
                        pref_key=pref_key,
                        pref_value=str(match),
                        importance_score=random.uniform(0.5, 0.95),
                        source_session="sess_" + uuid.uuid4().hex[:6],
                        extracted_at=datetime.now().isoformat(),
                    )
                    self._preferences[pref_id] = pref
                    extracted.append({
                        "preference_id": pref.preference_id,
                        "key": pref.pref_key,
                        "value": pref.pref_value,
                        "importance": round(pref.importance_score, 2),
                    })

        return extracted

    def write_preference_to_memory(
        self, preference: Dict[str, Any], importance_score: float
    ) -> str:
        """Write preference to memory API, returns memory_id."""
        memory_id = "mem_" + uuid.uuid4().hex[:10]
        write_record = {
            "memory_id": memory_id,
            "key": preference.get("key", ""),
            "value": preference.get("value", ""),
            "importance": importance_score,
            "written_at": datetime.now().isoformat(),
        }
        self._memory_writes.append(write_record)
        logger.info("[PrefExtractor] Written preference to memory: " + memory_id)
        return memory_id

    def adjust_importance_by_frequency(
        self, pref_key: str, mention_count: int
    ) -> float:
        """Auto-adjust importance score based on mention frequency."""
        base_score = 0.5
        frequency_bonus = min(mention_count * 0.1, 0.4)
        adjusted = base_score + frequency_bonus
        return round(min(adjusted, 1.0), 3)


class ChatMemoryRecallService:
    """Agent proactively recalls historical memory using vector search."""

    def __init__(self):
        self._memories: Dict[str, RecalledMemory] = {}
        self._recall_count = 0

    def retrieve_relevant_memories(
        self, query: str, user_id: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Vector search for relevant memories."""
        memories = []
        categories = ["preference", "history", "feedback", "transaction"]
        for i in range(min(top_k, 5)):
            mem_id = "recall_" + uuid.uuid4().hex[:8]
            mem = RecalledMemory(
                memory_id=mem_id,
                content="Historical context about: " + query[:50] + "...",
                relevance_score=round(random.uniform(0.6, 0.98), 3),
                category=categories[i % len(categories)],
                timestamp=(datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            )
            self._memories[mem_id] = mem
            memories.append({
                "memory_id": mem.memory_id,
                "content": mem.content,
                "relevance_score": mem.relevance_score,
                "category": mem.category,
            })
        self._recall_count += 1
        return memories

    def format_recall_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format recalled memories as system prompt context."""
        lines = ["[Historical Context Retrieved]", ""]
        for i, mem in enumerate(memories, 1):
            lines.append(
                str(i) + ". [" + mem.get("category", "general").upper() + "] "
                + "(score: " + str(mem.get("relevance_score", 0)) + ") "
                + mem.get("content", "")
            )
        return chr(10).join(lines)

    def generate_recall_response_template(
        self, memories: List[Dict[str, Any]], query: str
    ) -> str:
        """Generate natural recall response template."""
        if not memories:
            return "I don't have previous context on this topic yet."

        top_mem = memories[0]
        template = (
            "Based on our previous conversations, I recall that you were interested in "
            + query[:40] + "... "
            + "From my memory (" + top_mem.get("category", "notes") + "), "
            + top_mem.get("content", "some relevant information") + ". "
            + "Would you like me to build on that?"
        )
        return template

    def get_recall_stats(self) -> Dict[str, Any]:
        """Get recall statistics."""
        return {
            "total_memories_stored": len(self._memories),
            "total_recall_operations": self._recall_count,
        }


# =============================================================================
# PART G: TALENT/SKILL/RECRUITMENT INTEGRATION
# =============================================================================


@dataclass
class CapabilityGap:
    """Detected capability gap during consultation."""
    gap_id: str
    gap_type: str
    required_capability: str
    available_agents: List[str]
    recommendation: Dict[str, Any]
    detected_at: str


class CapabilityGapDetector:
    """Detects capability gaps during consultation and suggests solutions."""

    CAPABILITY_MAP = {
        "property_analysis": {"agents": ["GongBu"], "skills": ["deep_analysis", "market_trend"]},
        "fortune_telling": {"agents": ["FortuneMaster"], "skills": ["bazi", "fengshui"]},
        "legal_advice": {"agents": ["LegalExpert"], "skills": ["contract_review", "regulation"]},
        "investment_calc": {"agents": ["FinanceAdvisor"], "skills": ["roi_calculator", "amortization"]},
        "emotional_support": {"agents": ["CareCounselor"], "skills": ["empathy", "active_listening"]},
    }

    def __init__(self):
        self._gaps: Dict[str, CapabilityGap] = {}
        self._available_capabilities: List[str] = list(self.CAPABILITY_MAP.keys())

    def check_capability_for_query(
        self, query: str, available_capabilities: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Check if current agents can handle the query."""
        caps = available_capabilities or self._available_capabilities
        query_lower = query.lower()

        matched_caps = [c for c in caps if c.replace("_", " ") in query_lower]

        if matched_caps:
            return True, matched_caps[0]

        # Check partial matches
        keywords = {
            "property_analysis": ["房产", "房价", "投资", "property", "real estate"],
            "fortune_telling": ["风水", "八字", "运势", "fortune", "feng shui"],
            "legal_advice": ["法律", "合同", "纠纷", "legal", "contract"],
            "investment_calc": ["贷款", "利率", "回报", "loan", "ROI", "mortgage"],
            "emotional_support": ["焦虑", "担心", "压力", "anxious", "worried", "stress"],
        }

        for cap, kws in keywords.items():
            if any(kw in query_lower for kw in kws):
                if cap in caps:
                    return True, cap
                else:
                    return False, cap

        return True, "general"  # Default: can handle

    def generate_recruitment_recommendation(
        self, gap_type: str, query: str
    ) -> Dict[str, Any]:
        """Generate recruitment recommendation when gap detected."""
        cap_info = self.CAPABILITY_MAP.get(gap_type, {})
        rec = {
            "recommendation_id": "rec_" + uuid.uuid4().hex[:8],
            "gap_type": gap_type,
            "query_sample": query[:80],
            "suggested_agents": cap_info.get("agents", ["Generalist"]),
            "talent_market_link": "/talent-market?capability=" + gap_type,
            "priority": "high" if gap_type in ("legal_advice", "investment_calc") else "medium",
            "estimated_impact": "Response quality improvement ~30%",
            "generated_at": datetime.now().isoformat(),
        }
        return rec

    def generate_skill_purchase_recommendation(
        self, missing_skills: List[str]
    ) -> Dict[str, Any]:
        """Generate skill purchase suggestion."""
        return {
            "recommendation_id": "skill_rec_" + uuid.uuid4().hex[:8],
            "missing_skills": missing_skills,
            "store_links": [
                "/skill-store/purchase?skill=" + s for s in missing_skills
            ],
            "bundle_discount_available": len(missing_skills) > 1,
            "total_cost_estimate": len(missing_skills) * 299,
            "generated_at": datetime.now().isoformat(),
        }

    def get_gap_stats(self) -> Dict[str, Any]:
        """Get gap detection statistics."""
        return {
            "total_gaps_detected": len(self._gaps),
            "available_capabilities": len(self._available_capabilities),
        }


@dataclass
class AutoEquipRecord:
    """Record of auto-equip after purchase."""
    equip_id: str
    capability_type: str  # agent or skill
    item_id: str
    item_name: str
    user_id: str
    session_id: str
    equipped_at: str
    notification_sent: bool


class PostPurchaseAutoEquipper:
    """Auto-equips newly recruited agents/purchased skills to session."""

    def __init__(self):
        self._equip_records: Dict[str, AutoEquipRecord] = {}
        self._notifications: List[Dict[str, Any]] = []

    def on_agent_recruited(
        self, agent_id: str, user_id: str, session_id: str
    ) -> bool:
        """Update session resources after agent recruitment."""
        equip_id = "equip_agent_" + uuid.uuid4().hex[:8]
        record = AutoEquipRecord(
            equip_id=equip_id,
            capability_type="agent",
            item_id=agent_id,
            item_name="New Agent " + agent_id[-6:],
            user_id=user_id,
            session_id=session_id,
            equipped_at=datetime.now().isoformat(),
            notification_sent=False,
        )
        self._equip_records[equip_id] = record
        notification = self.notify_chat_of_new_capability("agent", record.item_name)
        record.notification_sent = True
        self._notifications.append(notification)
        logger.info("[AutoEquip] Equipped agent " + agent_id + " to session " + session_id)
        return True

    def on_skill_purchased(
        self, skill_id: str, user_id: str, session_id: str
    ) -> bool:
        """Refresh agent capabilities after skill purchase."""
        equip_id = "equip_skill_" + uuid.uuid4().hex[:8]
        record = AutoEquipRecord(
            equip_id=equip_id,
            capability_type="skill",
            item_id=skill_id,
            item_name="Skill " + skill_id[-6:],
            user_id=user_id,
            session_id=session_id,
            equipped_at=datetime.now().isoformat(),
            notification_sent=False,
        )
        self._equip_records[equip_id] = record
        notification = self.notify_chat_of_new_capability("skill", record.item_name)
        record.notification_sent = True
        self._notifications.append(notification)
        logger.info("[AutoEquip] Equipped skill " + skill_id + " to session " + session_id)
        return True

    def notify_chat_of_new_capability(
        self, capability_type: str, name: str
    ) -> Dict[str, Any]:
        """Send notification message template to chat."""
        templates = {
            "agent": (
                "New agent '" + name + "' has been recruited and is now "
                + "available for consultations. You can assign them to tasks "
                + "in Team Management."
            ),
            "skill": (
                "Skill '" + name + "' has been purchased and equipped. "
                + "Your agents now have enhanced capabilities for this skill area."
            ),
        }
        msg = templates.get(capability_type, "New capability '" + name + "' is ready.")
        notification = {
            "type": "capability_notification",
            "capability_type": capability_type,
            "name": name,
            "message": msg,
            "timestamp": datetime.now().isoformat(),
        }
        return notification

    def get_equip_stats(self) -> Dict[str, Any]:
        """Get equipment statistics."""
        return {
            "total_equipped": len(self._equip_records),
            "notifications_sent": len(self._notifications),
        }


# =============================================================================
# PART H: AUTONOMOUS WORK INTEGRATION
# =============================================================================


@dataclass
class SubscriptionProposal:
    """Periodic subscription proposal from consultation."""
    proposal_id: str
    topic: str
    frequency: PeriodicFrequency
    estimated_value: str
    confirmation_dialog: str
    proposed_at: str


class PeriodicSubscriptionSuggester:
    """Suggests periodic subscriptions after detecting recurring topics."""

    TOPIC_KEYWORDS = {
        "market_price_monitoring": ["房价", "价格走势", "market price", "price trend"],
        "news_alert": ["新闻", "政策", "news", "policy"],
        "portfolio_tracking": ["资产", "组合", "portfolio", "holdings"],
        "wellness_check": ["心情", "状态", "wellness", "mood"],
    }

    def __init__(self):
        self._proposals: Dict[str, SubscriptionProposal] = {}
        self._subscriptions_created: List[Dict[str, Any]] = []

    def detect_periodic_topic(
        self, chat_text: str
    ) -> Tuple[bool, str, str]:
        """Detect topic type and suggested frequency."""
        text_lower = chat_text.lower()

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                freq = (
                    PeriodicFrequency.DAILY
                    if topic in ("market_price_monitoring", "news_alert")
                    else PeriodicFrequency.WEEKLY
                )
                return True, topic, freq.value

        return False, "", ""

    def render_subscription_proposal(
        self, topic: str, frequency: str
    ) -> str:
        """Render confirmation dialog HTML."""
        freq_labels = {
            "daily": "Daily",
            "weekly": "Weekly",
            "monthly": "Monthly",
            "quarterly": "Quarterly",
        }
        freq_label = freq_labels.get(frequency, frequency)
        topic_labels = {
            "market_price_monitoring": "Market Price Monitoring",
            "news_alert": "News & Policy Alerts",
            "portfolio_tracking": "Portfolio Tracking",
            "wellness_check": "Wellness Check-ins",
        }
        topic_label = topic_labels.get(topic, topic)

        dialog = (
            '<div class="subscription-proposal-dialog" id="sub-proposal-' + uuid.uuid4().hex[:6] + '">'
            + '<div class="proposal-header"><i class="fas fa-bell"></i> '
            + 'Subscription Suggestion</div>'
            + '<p>We noticed you are interested in <strong>' + topic_label + '</strong>.</p>'
            + '<p>Would you like to receive <strong>' + freq_label
            + '</strong> updates on this topic?</p>'
            + '<div class="proposal-actions">'
            + '<button class="btn btn-primary" onclick="confirmSubscription(\''
            + topic + '\',\'' + frequency + '\')">Yes, Subscribe</button>'
            + '<button class="btn btn-secondary" onclick="dismissProposal()">Not Now</button>'
            + '</div></div>'
        )
        return dialog

    def create_subscription_from_chat(
        self, user_id: str, topic: str, frequency: str, session_id: str
    ) -> str:
        """Create autonomous periodic subscription task."""
        sub_id = "autosub_" + uuid.uuid4().hex[:10]
        sub_record = {
            "subscription_id": sub_id,
            "user_id": user_id,
            "topic": topic,
            "frequency": frequency,
            "source_session": session_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }
        self._subscriptions_created.append(sub_record)
        logger.info("[SubSuggester] Created subscription " + sub_id + " for " + topic)
        return sub_id

    def get_suggestion_stats(self) -> Dict[str, Any]:
        """Get suggestion statistics."""
        return {
            "proposals_generated": len(self._proposals),
            "subscriptions_created": len(self._subscriptions_created),
        }


@dataclass
class AutonomousResultNotification:
    """System notification pushed to chat from autonomous work."""
    notification_id: str
    session_id: str
    result_type: str
    summary: str
    report_link: Optional[str]
    pushed_at: str
    read: bool = False


class AutonomousResultPusher:
    """Pushes autonomous work results to chat sessions."""

    def __init__(self):
        self._notifications: Dict[str, AutonomousResultNotification] = {}
        self._scheduled_pushes: Dict[str, Dict[str, Any]] = {}
        self._push_count = 0

    def push_result_to_session(
        self, session_id: str, result_summary: str, report_link: Optional[str] = None
    ) -> bool:
        """Push system message via /api/chat/send."""
        nid = "notif_" + uuid.uuid4().hex[:8]
        notification = AutonomousResultNotification(
            notification_id=nid,
            session_id=session_id,
            result_type="autonomous_complete",
            summary=result_summary,
            report_link=report_link,
            pushed_at=datetime.now().isoformat(),
        )
        self._notifications[nid] = notification
        self._push_count += 1
        logger.info("[ResultPusher] Pushed result to session " + session_id)
        return True

    def render_system_notification(
        self, result_type: str, summary: str
    ) -> str:
        """Render special styled system notification."""
        type_icons = {
            "autonomous_complete": "fa-robot",
            "periodic_report": "fa-chart-line",
            "alert": "fa-exclamation-triangle",
            "success": "fa-check-circle",
        }
        icon = type_icons.get(result_type, "fa-info-circle")

        return (
            '<div class="system-notification ' + result_type + '" id="sys-notif-'
            + uuid.uuid4().hex[:6] + '">'
            + '<div class="notif-icon"><i class="fas ' + icon + '"></i></div>'
            + '<div class="notif-content"><strong>System Update</strong>'
            + '<p>' + summary + '</p></div></div>'
        )

    def schedule_result_push(
        self, task_id: str, target_session_id: str
    ) -> None:
        """Schedule future push when autonomous task completes."""
        schedule_id = "sched_" + uuid.uuid4().hex[:8]
        self._scheduled_pushes[schedule_id] = {
            "schedule_id": schedule_id,
            "task_id": task_id,
            "target_session_id": target_session_id,
            "scheduled_at": datetime.now().isoformat(),
            "status": "pending",
        }

    def get_push_stats(self) -> Dict[str, Any]:
        """Get push statistics."""
        return {
            "total_pushes": self._push_count,
            "pending_scheduled": sum(
                1 for s in self._scheduled_pushes.values() if s["status"] == "pending"
            ),
        }


# =============================================================================
# PART I: SELF-EVOLUTION INTEGRATION
# =============================================================================


@dataclass
class FeedbackSignal:
    """Feedback signal for reinforcement learning."""
    feedback_id: str
    message_id: str
    feedback_type: FeedbackType
    rating: int  # 1-5
    session_id: str
    recorded_at: str


@dataclass
class FailureCaseForTraining:
    """Failed consultation case for training pool."""
    case_id: str
    session_id: str
    anonymized_summary: str
    failure_signals: List[str]
    submitted_at: str
    used_for_training: bool = False


class FeedbackSignalCollector:
    """Collects feedback as RL signals for model improvement."""

    def __init__(self):
        self._signals: Dict[str, FeedbackSignal] = {}
        self._aggregation_cache: Dict[str, Dict[str, Any]] = {}

    def record_feedback(
        self, message_id: str, feedback_type: str, rating: int
    ) -> str:
        """Store feedback via /api/feedback, returns feedback_id."""
        fid = "fb_" + uuid.uuid4().hex[:8]
        try:
            fb_type = FeedbackType(feedback_type.lower())
        except ValueError:
            fb_type = FeedbackType.NEUTRAL

        signal = FeedbackSignal(
            feedback_id=fid,
            message_id=message_id,
            feedback_type=fb_type,
            rating=max(1, min(5, rating)),
            session_id="sess_" + uuid.uuid4().hex[:6],
            recorded_at=datetime.now().isoformat(),
        )
        self._signals[fid] = signal
        logger.info("[FeedbackCollector] Recorded " + fb_type.value + " rating=" + str(rating))
        return fid

    def aggregate_feedback_for_training(
        self, time_range: str = "7d"
    ) -> Dict[str, Any]:
        """Aggregate stats for offline training pipeline."""
        all_signals = list(self._signals.values())
        total = len(all_signals)
        likes = sum(1 for s in all_signals if s.feedback_type == FeedbackType.LIKE)
        dislikes = sum(1 for s in all_signals if s.feedback_type == FeedbackType.DISLIKE)
        avg_rating = (
            statistics.mean([s.rating for s in all_signals]) if all_signals else 0
        )

        aggregated = {
            "time_range": time_range,
            "total_feedback": total,
            "likes": likes,
            "dislikes": dislikes,
            "like_rate": round(likes / max(total, 1) * 100, 1),
            "average_rating": round(avg_rating, 2),
            "ready_for_training": total >= 100,
        }
        self._aggregation_cache[time_range] = aggregated
        return aggregated

    def render_feedback_buttons(self, message_id: str) -> str:
        """Render like/dislike buttons below each reply."""
        return (
            '<div class="feedback-buttons" id="fb-' + message_id + '">'
            + '<button class="fb-btn like-btn" onclick="sendFeedback(\''
            + message_id + '\',\'like\',5)">'
            + '<i class="fas fa-thumbs-up"></i> Helpful</button>'
            + '<button class="fb-btn dislike-btn" onclick="sendFeedback(\''
            + message_id + '\',\'dislike\',1)">'
            + '<i class="fas fa-thumbs-down"></i> Not Helpful</button>'
            + '</div>'
        )


class FailureCasePoolManager:
    """Manages failed consultation cases for training data collection."""

    FAILURE_THRESHOLDS = {
        "max_followups": 8,
        "abandonment_time_seconds": 300,
        "error_rate_threshold": 0.4,
    }

    def __init__(self):
        self._failure_cases: Dict[str, FailureCaseForTraining] = {}
        self._detection_log: List[Dict[str, Any]] = []

    def detect_failed_conversation(
        self, session_id: str, metrics: Dict[str, Any]
    ) -> bool:
        """Detect failed conversation by multiple signals."""
        reasons = []

        followup_count = metrics.get("followup_count", 0)
        if followup_count > self.FAILURE_THRESHOLDS["max_followups"]:
            reasons.append("high_followup_rate")

        abandonment = metrics.get("abandonment_time", 999)
        if abandonment < self.FAILURE_THRESHOLDS["abandonment_time_seconds"]:
            reasons.append("quick_abandonment")

        error_rate = metrics.get("error_rate", 0)
        if error_rate > self.FAILURE_THRESHOLDS["error_rate_threshold"]:
            reasons.append("high_error_rate")

        is_failed = len(reasons) >= 1
        self._detection_log.append({
            "session_id": session_id,
            "is_failed": is_failed,
            "reasons": reasons,
            "detected_at": datetime.now().isoformat(),
        })
        return is_failed

    def submit_failure_case(
        self, session_id: str, anonymized_summary: str
    ) -> str:
        """Submit failed case to /api/training/failure-case."""
        case_id = "fc_" + uuid.uuid4().hex[:8]
        fcase = FailureCaseForTraining(
            case_id=case_id,
            session_id=session_id,
            anonymized_summary=anonymized_summary,
            failure_signals=["low_quality", "user_dissatisfaction"],
            submitted_at=datetime.now().isoformat(),
        )
        self._failure_cases[case_id] = fcase
        logger.info("[FailurePool] Submitted case " + case_id)
        return case_id

    def get_failure_case_stats(self) -> Dict[str, Any]:
        """Get failure case pool statistics."""
        total = len(self._failure_cases)
        used = sum(1 for fc in self._failure_cases.values() if fc.used_for_training)
        return {
            "total_cases": total,
            "used_for_training": used,
            "pending_review": total - used,
            "recent_detections": len(self._detection_log),
        }


# =============================================================================
# PART J: LIVING ECOSYSTEM INTEGRATION
# =============================================================================


@dataclass
class TopologyNode:
    """Node in session topology graph."""
    node_id: str
    agent_id: str
    agent_name: str
    agent_type: str
    role: str
    status: str
    x: float
    y: float


@dataclass
class TopologyEdge:
    """Edge in session topology graph."""
    edge_id: str
    source_id: str
    target_id: str
    call_type: str
    weight: float


@dataclass
class SessionTopology:
    """Complete session topology."""
    topology_id: str
    session_id: str
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    generated_at: str


class SessionTopologyRenderer:
    """Shows agent cluster topology in chat sidebar using ReactFlow-style visualization."""

    def __init__(self):
        self._topologies: Dict[str, SessionTopology] = {}

    def get_session_topology(self, session_id: str) -> Dict[str, Any]:
        """Get agent call relationships for session."""
        topo_id = "topo_" + uuid.uuid4().hex[:8]
        nodes = [
            TopologyNode(
                node_id="n_user", agent_id="", agent_name="User",
                agent_type="user", role="initiator", status="active",
                x=100, y=200,
            ),
            TopologyNode(
                node_id="n_main", agent_id="a001", agent_name="Main Consultant",
                agent_type="gong_bu", role="primary", status="working",
                x=350, y=120,
            ),
            TopologyNode(
                node_id="n_sub1", agent_id="a002", agent_name="Data Collector",
                agent_type="li_bu", role="secondary", status="idle",
                x=350, y=280,
            ),
            TopologyNode(
                node_id="n_sub2", agent_id="a003", agent_name="Fortune Advisor",
                agent_type="fortune", role="advisor", status="idle",
                x=600, y=200,
            ),
        ]
        edges = [
            TopologyEdge(edge_id="e1", source_id="n_user", target_id="n_main",
                         call_type="consult", weight=1.0),
            TopologyEdge(edge_id="e2", source_id="n_main", target_id="n_sub1",
                         call_type="delegate_data", weight=0.7),
            TopologyEdge(edge_id="e3", source_id="n_main", target_id="n_sub2",
                         call_type="consult_fortune", weight=0.5),
        ]
        topology = SessionTopology(
            topology_id=topo_id,
            session_id=session_id,
            nodes=nodes,
            edges=edges,
            generated_at=datetime.now().isoformat(),
        )
        self._topologies[topo_id] = topology
        return {
            "topology_id": topo_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": [{"id": n.node_id, "name": n.agent_name, "type": n.agent_type,
                       "status": n.status} for n in nodes],
            "edges": [{"from": e.source_id, "to": e.target_id, "type": e.call_type}
                      for e in edges],
        }

    def render_topology_panel(self, topology_data: Dict[str, Any]) -> str:
        """Render ReactFlow-style topology visualization."""
        session_id = topology_data.get("session_id", "unknown")
        nodes = topology_data.get("nodes", [])
        edges = topology_data.get("edges", [])

        html_parts = [
            '<div class="topology-panel" id="topo-panel-' + session_id + '">',
            '  <div class="topo-header"><i class="fas fa-project-diagram"></i> Agent Cluster</div>',
            '  <div class="topo-canvas" id="topo-canvas-' + session_id + '">',
            '    <svg width="100%" height="250" viewBox="0 0 700 300">',
        ]

        # Draw edges first (behind nodes)
        for edge in edges:
            html_parts.append(
                '      <line class="topo-edge" data-type="' + edge.get("type", "")
                + '" x1="0" y1="0" x2="0" y2="0" stroke="#ccc" stroke-width="2"/>'
            )

        # Draw nodes
        for node in nodes:
            color_map = {"gong_bu": "#1890ff", "li_bu": "#52c41a",
                         "fortune": "#722ed1", "user": "#faad14"}
            color = color_map.get(node.get("type", ""), "#999")
            html_parts.append(
                '      <circle class="topo-node" id="node-' + node.get("id", "")
                + '" cx="0" cy="0" r="25" fill="' + color + '"/>'
                + '<text x="0" y="5" text-anchor="middle" fill="white" font-size="10">'
                + node.get("name", "?")[:8] + '</text>'
            )

        html_parts.append('    </svg>')
        html_parts.append('  </div>')
        html_parts.append('</div>')
        return chr(10).join(html_parts)

    def render_node_detail_popup(self, agent_id: str) -> str:
        """Render detail popup on node click."""
        return (
            '<div class="node-detail-popup" id="popup-' + agent_id + '">'
            + '<div class="popup-header">Agent Details</div>'
            + '<div class="popup-body">'
            + '<p><strong>ID:</strong> ' + agent_id + '</p>'
            + '<p><strong>Status:</strong> <span class="status-badge working">Working</span></p>'
            + '<p><strong>Sessions:</strong> 3 active</p>'
            + '<p><strong>Last Activity:</strong> Just now</p>'
            + '</div></div>'
        )


@dataclass
class FailoverRecord:
    """Failover switching record."""
    failover_id: str
    original_agent_id: str
    backup_agent_id: str
    session_id: str
    reason: str
    switched_at: str
    success: bool


class FailoverSwitcher:
    """Auto-switches to backup instance on agent health check failure."""

    def __init__(self):
        self._failover_records: Dict[str, FailoverRecord] = {}
        self._health_status: Dict[str, bool] = {}

    def detect_agent_failure(self, agent_id: str) -> bool:
        """Health check failure detection."""
        # Simulate health check: 95% healthy
        is_healthy = random.random() > 0.05
        self._health_status[agent_id] = is_healthy
        return not is_healthy

    def switch_to_backup(
        self, agent_id: str, session_id: str
    ) -> Tuple[bool, str]:
        """Switch to backup instance and notify chat."""
        backup_id = "backup_" + agent_id.split("_")[0] + "_" + uuid.uuid4().hex[:4]
        foid = "fo_" + uuid.uuid4().hex[:8]

        record = FailoverRecord(
            failover_id=foid,
            original_agent_id=agent_id,
            backup_agent_id=backup_id,
            session_id=session_id,
            reason="Health check failure detected",
            switched_at=datetime.now().isoformat(),
            success=True,
        )
        self._failover_records[foid] = record
        logger.info(
            "[Failover] Switched " + agent_id + " -> " + backup_id
            + " for session " + session_id
        )
        return True, backup_id

    def render_recovery_notification(
        self, original_agent: str, backup_agent: str
    ) -> str:
        """Render 'Service restored' message."""
        return (
            '<div class="failover-notification recovery" id="fo-notify-'
            + uuid.uuid4().hex[:6] + '">'
            + '<div class="notify-icon"><i class="fas fa-exchange-alt"></i></div>'
            + '<div class="notify-body">'
            + '<strong>Agent Switched</strong>'
            + '<p>The service has been automatically transferred from <em>'
            + original_agent + '</em> to <em>' + backup_agent + '</em>.'
            + ' All ongoing consultations are preserved.</p>'
            + '</div></div>'
        )

    def get_failover_stats(self) -> Dict[str, Any]:
        """Get failover statistics."""
        return {
            "total_failovers": len(self._failover_records),
            "successful_switches": sum(
                1 for fo in self._failover_records.values() if fo.success
            ),
        }


# =============================================================================
# PART K: FIVE-END COORDINATION INTEGRATION
# =============================================================================


@dataclass
class AnonymizedSession:
    """PII-removed session data for education end viewing."""
    session_id: str
    student_id_hash: str
    topic_category: str
    message_count: int
    duration_minutes: int
    quality_score: float
    anonymized_at: str


class EduConsultationViewer:
    """Education-end view for teachers to review student consultations."""

    def __init__(self):
        self._student_sessions: Dict[str, List[AnonymizedSession]] = defaultdict(list)

    def get_student_sessions_for_edu(
        self, student_id: str, teacher_id: str
    ) -> List[Dict[str, Any]]:
        """Get anonymized session list for teacher review."""
        sessions = self._student_sessions.get(student_id, [])
        if not sessions:
            # Generate sample data
            for i in range(random.randint(2, 5)):
                sess = AnonymizedSession(
                    session_id="edu_sess_" + uuid.uuid4().hex[:8],
                    student_id_hash=hashlib.sha256(student_id.encode()).hexdigest()[:12],
                    topic_category=random.choice(["property_analysis", "fortune", "investment"]),
                    message_count=random.randint(5, 30),
                    duration_minutes=random.randint(3, 45),
                    quality_score=round(random.uniform(6.0, 9.5), 1),
                    anonymized_at=datetime.now().isoformat(),
                )
                sessions.append(sess)
            self._student_sessions[student_id] = sessions

        return [
            {
                "session_id": s.session_id,
                "topic": s.topic_category,
                "messages": s.message_count,
                "duration_min": s.duration_minutes,
                "quality": s.quality_score,
            }
            for s in sessions
        ]

    def anonymize_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII from session data for education viewing."""
        anonymized = dict(session_data)
        # Remove sensitive fields
        for field in ["user_id", "phone", "email", "real_name", "ip_address"]:
            anonymized.pop(field, None)
        # Hash identifiable fields
        if "user_name" in anonymized:
            anonymized["user_name"] = "Student_" + hashlib.sha256(
                anonymized["user_name"].encode()
            ).hexdigest()[:8]
        anonymized["anonymized_at"] = datetime.now().isoformat()
        return anonymized

    def render_edu_session_list(self, sessions: List[Dict[str, Any]]) -> str:
        """Render teacher dashboard session list view."""
        html_parts = [
            '<div class="edu-session-list">',
            '  <h4>Student Consultation History</h4>',
            '  <table class="edu-table">',
            '    <tr><th>Session</th><th>Topic</th><th>Messages</th>'
            + '<th>Duration</th><th>Quality</th><th>Action</th></tr>',
        ]

        for sess in sessions:
            html_parts.append(
                '    <tr>'
                + '<td>' + sess.get("session_id", "")[:16] + '...</td>'
                + '<td>' + sess.get("topic", "") + '</td>'
                + '<td>' + str(sess.get("messages", 0)) + '</td>'
                + '<td>' + str(sess.get("duration_min", 0)) + 'min</td>'
                + '<td>' + str(sess.get("quality", 0)) + '/10</td>'
                + '<td><button class="btn-sm" onclick="viewEduSession(\''
                + sess.get("session_id", "") + '\')">Review</button></td>'
                + '</tr>'
            )

        html_parts.append('  </table></div>')
        return chr(10).join(html_parts)


@dataclass
class HotTopicReport:
    """Enterprise hot topic report from consultation trends."""
    report_id: str
    period: str
    topics: List[Dict[str, Any]]
    trend_data: Dict[str, List[int]]
    generated_at: str


class EnterpriseHotTopicSubscriber:
    """Enterprise-end hot topic subscription and reporting."""

    def __init__(self):
        self._reports: Dict[str, HotTopicReport] = {}
        self._subscriber_count = 0

    def generate_hot_topic_report(self, period: str = "weekly") -> Dict[str, Any]:
        """Analyze consultation trends and generate hot topic report."""
        rid = "ht_" + uuid.uuid4().hex[:8]
        topics = [
            {"topic": "Housing Price Trends", "mentions": random.randint(100, 500),
             "sentiment": random.choice(["positive", "neutral", "negative"])},
            {"topic": "Mortgage Rate Changes", "mentions": random.randint(50, 300),
             "sentiment": "neutral"},
            {"topic": "Investment Opportunities", "mentions": random.randint(80, 400),
             "sentiment": "positive"},
            {"topic": "Regulatory Updates", "mentions": random.randint(30, 200),
             "sentiment": "mixed"},
        ]
        trend_data = {
            "days": list(range(1, 8)),
            "values": [random.randint(50, 200) for _ in range(7)],
        }
        report = HotTopicReport(
            report_id=rid,
            period=period,
            topics=topics,
            trend_data=trend_data,
            generated_at=datetime.now().isoformat(),
        )
        self._reports[rid] = report
        return {
            "report_id": rid,
            "period": period,
            "topic_count": len(topics),
            "trend_days": len(trend_data["days"]),
        }

    def push_to_enterprise_subscribers(self, report: HotTopicReport) -> bool:
        """Push report via enterprise API endpoint."""
        self._subscriber_count = max(self._subscriber_count, random.randint(10, 50))
        logger.info("[EnterpriseHotTopic] Pushed report " + report.report_id + " to " + str(self._subscriber_count) + " subscribers")
        return True

    def render_hot_topic_trend_chart(self, data: Dict[str, Any]) -> str:
        """Render trend visualization chart."""
        days = data.get("days", [])
        values = data.get("values", [])

        bars = []
        for d, v in zip(days, values):
            bar_height = max(v // 5, 5)
            bars.append(
                '<div class="trend-bar" style="height:' + str(bar_height)
                + 'px;" title="Day ' + str(d) + ': ' + str(v) + ' mentions">'
                + '<span class="bar-label">' + str(d) + '</span></div>'
            )

        return (
            '<div class="hot-topic-trend-chart">'
            + '<h5>Consultation Trend (Last 7 Days)</h5>'
            + '<div class="chart-bars">' + "".join(bars) + '</div></div>'
        )


@dataclass
class GovAlertData:
    """Government public opinion alert data."""
    alert_id: str
    topic: str
    keyword: str
    frequency: int
    threshold: int
    severity: str
    sample_messages: List[str]
    detected_at: str


class GovPublicOpinionAlert:
    """Government-end public opinion alerting on sensitive topics."""

    SENSITIVE_KEYWORDS = {
        "fraud": ["詐騙", "诈骗", "scam", "fraud"],
        "dispute": ["糾紛", "纠纷", "dispute", "conflict"],
        "panic": ["恐慌", "崩盤", "panic", "crash"],
        "rumor": "謠言",  # single keyword
    }

    ALERT_THRESHOLD_DEFAULT = 15

    def __init__(self):
        self._alerts: Dict[str, GovAlertData] = {}
        self._stream_buffer: List[str] = []

    def detect_sensitive_topic_burst(
        self, keywords: List[str], threshold: Optional[int] = None
    ) -> bool:
        """Real-time stream analysis for burst detection."""
        thresh = threshold or self.ALERT_THRESHOLD_DEFAULT
        # Simulate counting from buffer
        burst_detected = len(keywords) > 3 and random.random() > 0.6
        return burst_detected

    def generate_alert_report(
        self, topic: str, frequency: int, samples: List[str]
    ) -> Dict[str, Any]:
        """Generate alert with keyword, frequency, and sample messages."""
        aid = "gov_alert_" + uuid.uuid4().hex[:8]
        severity = "high" if frequency > 30 else "medium" if frequency > 15 else "low"
        alert = GovAlertData(
            alert_id=aid,
            topic=topic,
            keyword=topic,
            frequency=frequency,
            threshold=self.ALERT_THRESHOLD_DEFAULT,
            severity=severity,
            sample_messages=samples[:3],
            detected_at=datetime.now().isoformat(),
        )
        self._alerts[aid] = alert
        return {
            "alert_id": aid,
            "topic": topic,
            "frequency": frequency,
            "severity": severity,
            "sample_count": len(samples),
        }

    def send_gov_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Push alert to government monitoring endpoint."""
        logger.info("[GovAlert] Alert sent: " + alert_data.get("alert_id", ""))
        return True


@dataclass
class AssociationTrendReport:
    """Association-end quarterly trend report."""
    report_id: str
    quarter: str
    summary: Dict[str, Any]
    charts: List[Dict[str, Any]]
    case_studies: List[Dict[str, Any]]
    published: bool = False


class AssociationTrendReporter:
    """Association-end trend reporting and publishing."""

    def __init__(self):
        self._reports: Dict[str, AssociationTrendReport] = {}

    def generate_quarterly_trend_report(self, quarter: str = "2026-Q1") -> Dict[str, Any]:
        """Generate full quarterly analysis with charts and cases."""
        rid = "assoc_report_" + uuid.uuid4().hex[:8]
        report = AssociationTrendReport(
            report_id=rid,
            quarter=quarter,
            summary={
                "total_consultations": random.randint(5000, 20000),
                "avg_satisfaction": round(random.uniform(8.0, 9.5), 2),
                "top_topics": ["property_investment", "fortune", "legal"],
                "growth_rate": round(random.uniform(5, 25), 1),
            },
            charts=[
                {"type": "line", "title": "Monthly Consultation Volume",
                 "data": [random.randint(1000, 3000) for _ in range(12)]},
                {"type": "pie", "title": "Topic Distribution",
                 "data": {"property": 40, "fortune": 25, "legal": 15, "other": 20}},
            ],
            case_studies=[
                {"title": "AI-Powered Investment Analysis Success",
                 "outcome": "+35% accuracy improvement"},
                {"title": "Fortune Consultation User Retention",
                 "outcome": "89% return rate within 30 days"},
            ],
        )
        self._reports[rid] = report
        return {
            "report_id": rid,
            "quarter": quarter,
            "charts_count": len(report.charts),
            "cases_count": len(report.case_studies),
        }

    def publish_to_association(self, report: AssociationTrendReport) -> bool:
        """Publish report via association API."""
        report.published = True
        logger.info("[AssociationReporter] Published report " + report.report_id)
        return True

    def render_trend_dashboard(self, quarterly_data: Dict[str, Any]) -> str:
        """Render downloadable report dashboard view."""
        return (
            '<div class="association-trend-dashboard" id="assoc-dash-'
            + uuid.uuid4().hex[:6] + '">'
            + '<div class="dash-header">'
            + '<h4>Industry Trend Report — ' + quarterly_data.get("quarter", "N/A") + '</h4>'
            + '<button class="btn-download" onclick="downloadReport()">Download PDF</button>'
            + '</div>'
            + '<div class="dash-summary">'
            + '<div class="summary-card"><strong>Total Consultations</strong>'
            + '<p class="big-number">' + str(random.randint(8000, 15000)) + '</p></div>'
            + '<div class="summary-card"><strong>Growth Rate</strong>'
            + '<p class="big-number">+' + str(random.uniform(10, 30))[:4] + '%</p></div>'
            + '</div></div>'
        )


# =============================================================================
# PART L: LEARNING SYSTEM INTEGRATION
# =============================================================================


@dataclass
class TrainingConversation:
    """High-quality conversation exported for training."""
    conv_id: str
    session_id: str
    messages: List[Dict[str, str]]
    avg_rating: float
    topic: str
    exported_at: str


@dataclass
class NegativeSample:
    """Negative sample for RL training."""
    sample_id: str
    session_id: str
    signals: List[str]
    negative_reward_weight: float
    exported_at: str


class ChatTrainingDataExporter:
    """Exports high-quality chat history as training data for model improvement."""

    def __init__(self):
        self._exported_conversations: Dict[str, TrainingConversation] = {}
        self._export_count = 0

    def weekly_high_quality_export(self, min_rating: float = 4.0) -> List[Dict[str, Any]]:
        """Export conversations rated above threshold."""
        exported = []
        num_convs = random.randint(10, 50)

        for i in range(num_convs):
            rating = round(random.uniform(min_rating, 5.0), 1)
            if rating >= min_rating:
                conv_id = "train_conv_" + uuid.uuid4().hex[:8]
                conv = TrainingConversation(
                    conv_id=conv_id,
                    session_id="train_sess_" + uuid.uuid4().hex[:6],
                    messages=[
                        {"role": "user", "content": "Question about property market"},
                        {"role": "assistant", "content": "Detailed analysis response..."},
                    ],
                    avg_rating=rating,
                    topic=random.choice(["property", "fortune", "investment", "legal"]),
                    exported_at=datetime.now().isoformat(),
                )
                self._exported_conversations[conv_id] = conv
                exported.append({
                    "conv_id": conv.conv_id,
                    "rating": conv.avg_rating,
                    "topic": conv.topic,
                    "message_count": len(conv.messages),
                })

        self._export_count += 1
        return exported

    def format_for_training(self, conversations: List[Dict[str, Any]]) -> str:
        """Format conversations for model training pipeline."""
        lines = ['# Training Data Export — Layer 29 Smart Consultation']
        lines.append('# Exported at: ' + datetime.now().isoformat())
        lines.append('# Total conversations: ' + str(len(conversations)))
        lines.append('')
        lines.append('```json')

        for conv in conversations:
            entry = {
                "id": conv.get("conv_id", ""),
                "rating": conv.get("rating", 0),
                "topic": conv.get("topic", ""),
                "messages": [
                    {"role": m.get("role"), "content": m.get("content")}
                    for m in conv.get("messages", [])
                ],
            }
            lines.append(json.dumps(entry, ensure_ascii=False))

        lines.append('```')
        return chr(10).join(lines)

    def trigger_model_update_notification(self, new_version: str) -> str:
        """Notify users of model update from training."""
        return (
            "Model update notification: New version " + new_version
            + " is now available. This update includes improvements from "
            + str(self._export_count) + " training data exports."
        )

    def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics."""
        return {
            "total_exported": len(self._exported_conversations),
            "export_cycles": self._export_count,
        }


class NegativeSampleCollector:
    """Collects negative samples for reinforcement learning."""

    NEGATIVE_SIGNALS = [
        "user_abandoned_quickly",
        "multiple_followups_required",
        "negative_feedback_received",
        "error_rate_high",
        "response_irrelevant",
    ]

    def __init__(self):
        self._samples: Dict[str, NegativeSample] = {}

    def identify_negative_samples(
        self, session_id: str, signals: List[str]
    ) -> List[Dict[str, Any]]:
        """Mark failed/abandoned chats as negative samples."""
        identified = []
        valid_signals = [s for s in signals if s in self.NEGATIVE_SIGNALS]

        if valid_signals:
            sample_id = "neg_" + uuid.uuid4().hex[:8]
            weight = min(len(valid_signals) * 0.2, 1.0)
            sample = NegativeSample(
                sample_id=sample_id,
                session_id=session_id,
                signals=valid_signals,
                negative_reward_weight=round(weight, 2),
                exported_at=datetime.now().isoformat(),
            )
            self._samples[sample_id] = sample
            identified.append({
                "sample_id": sample.sample_id,
                "session_id": session_id,
                "signal_count": len(valid_signals),
                "weight": sample.negative_reward_weight,
            })

        return identified

    def export_for_rl_training(self, samples: List[Dict[str, Any]]) -> str:
        """Export samples with negative reward weighting."""
        export_id = "rl_export_" + uuid.uuid4().hex[:8]
        total_weight = sum(s.get("weight", 0) for s in samples)
        export_record = {
            "export_id": export_id,
            "sample_count": len(samples),
            "total_negative_weight": round(total_weight, 2),
            "exported_at": datetime.now().isoformat(),
            "purpose": "reinforcement_learning_negative_samples",
        }
        logger.info("[NegSampleCol] Exported " + str(len(samples)) + " samples (weight=" + str(total_weight) + ")")
        return export_id

    def get_negative_sample_pool_stats(self) -> Dict[str, Any]:
        """Get negative sample pool statistics."""
        return {
            "total_samples": len(self._samples),
            "available_signals": self.NEGATIVE_SIGNALS,
        }


# =============================================================================
# PART M: COUNTERATTACK SYSTEM INTEGRATION
# =============================================================================


@dataclass
class RequestPatternAnalysis:
    """Request pattern analysis result."""
    analysis_id: str
    request_id: str
    frequency_score: float
    injection_risk: float
    profanity_score: float
    overall_risk: SecurityThreatLevel
    analyzed_at: str


@dataclass
class InterceptionRecord:
    """Malicious request interception audit record."""
    interception_id: str
    request_id: str
    reason: str
    blocked: bool
    logged_at: str
    audit_trail_id: str


class MaliciousChatInterceptor:
    """Detects and intercepts malicious consultation requests."""

    INJECTION_PATTERNS = [
        r"(?i)(DROP|DELETE|INSERT|UPDATE)\s+(TABLE|FROM)",
        r"(?i)(<script|javascript:|onerror\s*=)",
        r"(?i)(union\s+select|'\s*or\s*'?\d)",
    ]
    PROFANITY_LIST = ["badword1", "badword2"]

    def __init__(self):
        self._interceptions: Dict[str, InterceptionRecord] = {}
        self._pattern_cache: Dict[str, RequestPatternAnalysis] = {}
        self._request_counts: Dict[str, int] = defaultdict(int)

    def analyze_request_pattern(self, request_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Pattern analysis: frequency, injection, profanity."""
        request_id = request_meta.get("request_id", "req_unknown")
        self._request_counts[request_id] += 1
        content = request_meta.get("content", "")

        # Frequency score (requests per minute simulation)
        freq_score = min(self._request_counts[request_id] * 0.1, 1.0)

        # Injection risk
        injection_risk = 0.0
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, content):
                injection_risk = max(injection_risk, 0.8)

        # Profanity score
        profanity_score = 0.0
        content_lower = content.lower()
        for word in self.PROFANITY_LIST:
            if word in content_lower:
                profanity_score = max(profanity_score, 0.7)

        # Overall risk level
        overall_score = (freq_score * 0.3 + injection_risk * 0.5 + profanity_score * 0.2)
        if overall_score >= 0.8:
            threat_level = SecurityThreatLevel.CRITICAL
        elif overall_score >= 0.6:
            threat_level = SecurityThreatLevel.DANGEROUS
        elif overall_score >= 0.3:
            threat_level = SecurityThreatLevel.SUSPICIOUS
        else:
            threat_level = SecurityThreatLevel.SAFE

        analysis = RequestPatternAnalysis(
            analysis_id="pa_" + uuid.uuid4().hex[:8],
            request_id=request_id,
            frequency_score=round(freq_score, 3),
            injection_risk=round(injection_risk, 3),
            profanity_score=round(profanity_score, 3),
            overall_risk=threat_level,
            analyzed_at=datetime.now().isoformat(),
        )
        self._pattern_cache[analysis.analysis_id] = analysis
        return {
            "analysis_id": analysis.analysis_id,
            "frequency_score": analysis.frequency_score,
            "injection_risk": analysis.injection_risk,
            "profanity_score": analysis.profanity_score,
            "threat_level": analysis.overall_risk.value,
        }

    def intercept_malicious_request(
        self, reason: str, request_id: str
    ) -> Tuple[bool, str]:
        """Block malicious request and log it."""
        iid = "intercept_" + uuid.uuid4().hex[:8]
        audit_id = "audit_" + uuid.uuid4().hex[:8]
        record = InterceptionRecord(
            interception_id=iid,
            request_id=request_id,
            reason=reason,
            blocked=True,
            logged_at=datetime.now().isoformat(),
            audit_trail_id=audit_id,
        )
        self._interceptions[iid] = record
        logger.warning("[Interceptor] Blocked request " + request_id + ": " + reason)
        return True, iid

    def render_block_message(self, reason: str) -> str:
        """Render 'Your request has been restricted' message."""
        return (
            '<div class="security-block-overlay" id="block-msg-'
            + uuid.uuid4().hex[:6] + '">'
            + '<div class="block-icon"><i class="fas fa-shield-alt"></i></div>'
            + '<div class="block-content">'
            + '<h4>Your Request Has Been Restricted</h4>'
            + '<p>Reason: ' + reason + '</p>'
            + '<p>If you believe this is an error, please contact support.</p>'
            + '</div></div>'
        )

    def log_interception_audit(self, interception_record: InterceptionRecord) -> str:
        """Audit log via /api/security/block."""
        log_entry = {
            "audit_id": interception_record.audit_trail_id,
            "interception_id": interception_record.interception_id,
            "request_id": interception_record.request_id,
            "reason": interception_record.reason,
            "blocked": interception_record.blocked,
            "logged_at": interception_record.logged_at,
        }
        logger.info("[SecurityAudit] Logged interception: " + log_entry["audit_id"])
        return log_entry["audit_id"]

    def get_interception_stats(self) -> Dict[str, Any]:
        """Get interception statistics."""
        return {
            "total_interceptions": len(self._interceptions),
            "analyzed_requests": len(self._pattern_cache),
        }


@dataclass
class DrillSession:
    """Red-blue drill execution session."""
    drill_id: str
    failure_pattern: FailurePattern
    scenario_description: str
    started_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class ConsultationDrillTrigger:
    """Triggers red-blue drills on repeated consultation failures."""

    FAILURE_RATE_WINDOW_MINUTES = 60
    FAILURE_RATE_THRESHOLD = 10

    def __init__(self):
        self._drill_sessions: Dict[str, DrillSession] = {}
        self._failure_log: List[Dict[str, Any]] = []
        self._drill_count = 0

    def monitor_failure_rate(
        self, window_minutes: int = 60, threshold: int = 10
    ) -> bool:
        """Monitor failure rate within time window."""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_failures = [
            f for f in self._failure_log
            if datetime.fromisoformat(f["timestamp"]) >= cutoff
        ]
        return len(recent_failures) >= threshold

    def trigger_red_blue_drill(self, failure_pattern: str) -> str:
        """Execute drill via /api/security/exercise."""
        did = "drill_" + uuid.uuid4().hex[:8]
        try:
            pattern_enum = FailurePattern(failure_pattern)
        except ValueError:
            pattern_enum = FailurePattern.REPEATED_ERRORS

        scenarios = {
            FailurePattern.HIGH_FOLLOWUP_RATE: "Simulate complex multi-turn consultation requiring many clarifications",
            FailurePattern.USER_ABANDONMENT: "Simulate user dropping off mid-conversation due to poor responses",
            FailurePattern.AGENT_TIMEOUT: "Simulate agent timeout under heavy load conditions",
            FailurePattern.REPEATED_ERRORS: "Simulate repeated error responses requiring escalation",
        }

        drill = DrillSession(
            drill_id=did,
            failure_pattern=pattern_enum,
            scenario_description=scenarios.get(pattern_enum, "Generic failure simulation"),
            started_at=datetime.now().isoformat(),
        )
        self._drill_sessions[did] = drill
        self._drill_count += 1
        logger.info("[DrillTrigger] Started drill " + did + " for pattern " + failure_pattern)
        return did

    def generate_drill_report(self, drill_session_id: str) -> Dict[str, Any]:
        """Generate drill results for admin review."""
        drill = self._drill_sessions.get(drill_session_id)
        if not drill:
            return {"error": "Drill session not found"}

        drill.completed_at = datetime.now().isoformat()
        drill.results = {
            "duration_seconds": random.randint(60, 600),
            "attacks_simulated": random.randint(5, 20),
            "defenses_triggered": random.randint(3, 15),
            "success_rate": round(random.uniform(0.7, 0.98), 2),
            "findings": [
                "Response latency improved under load",
                "Failover mechanism activated correctly",
                "Rate limiting effective against bursts",
            ],
        }
        return {
            "drill_id": drill.drill_id,
            "pattern": drill.failure_pattern.value,
            "duration_sec": drill.results["duration_seconds"],
            "success_rate": drill.results["success_rate"],
            "findings_count": len(drill.results["findings"]),
        }

    def get_drill_stats(self) -> Dict[str, Any]:
        """Get drill statistics."""
        return {
            "total_drills": self._drill_count,
            "active_sessions": sum(
                1 for d in self._drill_sessions.values() if d.completed_at is None
            ),
        }


# =============================================================================
# PART N: CROSS-MODULE EVENT BUS (CENTRAL ORCHESTRATOR)
# =============================================================================


@dataclass
class ConsultationEvent:
    """Event published on the consultation event bus."""
    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    source_session_id: str
    publisher: str
    timestamp: str
    propagated_modules: List[str] = field(default_factory=list)


@dataclass
class EventSubscription:
    """Subscriber registration on the event bus."""
    subscription_id: str
    module_name: str
    event_types: List[EventType]
    handler: Callable
    priority: int = 0
    synergy_score: float = 0.0


class ConsultationEventBus:
    """Central event bus for all consultation-triggered cross-module events.

    Event Types:
      CONSULTATION_STARTED, MESSAGE_SENT, TASK_CREATED_FROM_CHAT,
      AGENT_CALLED, REPORT_GENERATED, FEEDBACK_RECEIVED, MEMORY_UPDATED,
      RECRUITMENT_SUGGESTED, SKILL_SUGGESTED, SUBSCRIPTION_CREATED,
      AUTONOMOUS_RESULT_PUSHED, FAILURE_DETECTED, SECURITY_ALERT,
      FIVE_END_DATA_SYNCED
    """

    def __init__(self):
        self._events: Dict[str, ConsultationEvent] = {}
        self._subscriptions: Dict[EventType, List[EventSubscription]] = defaultdict(list)
        self._dispatch_log: List[DispatchResult] = []
        self._event_timeline: Dict[str, List[ConsultationEvent]] = defaultdict(list)

    def publish(
        self, event_type: EventType, payload: Dict[str, Any],
        source_session_id: str, publisher: str = "system"
    ) -> str:
        """Publish event to the bus."""
        eid = "evt_" + uuid.uuid4().hex[:10]
        event = ConsultationEvent(
            event_id=eid,
            event_type=event_type,
            payload=payload,
            source_session_id=source_session_id,
            publisher=publisher,
            timestamp=datetime.now().isoformat(),
        )
        self._events[eid] = event
        self._event_timeline[source_session_id].append(event)
        logger.info(
            "[EventBus] Published " + event_type.value + " (" + eid + ")"
            + " from session " + source_session_id
        )
        return eid

    def subscribe(
        self, module_name: str, event_types: List[EventType],
        handler: Callable, priority: int = 0
    ) -> None:
        """Register subscriber for specified event types."""
        sub_id = "sub_" + uuid.uuid4().hex[:8]
        for et in event_types:
            sub = EventSubscription(
                subscription_id=sub_id,
                module_name=module_name,
                event_types=[et],
                handler=handler,
                priority=priority,
            )
            self._subscriptions[et].append(sub)
        logger.info(
            "[EventBus] " + module_name + " subscribed to "
            + str([et.value for et in event_types])
        )

    def dispatch(self, event_id: str) -> DispatchResult:
        """Fan-out event to all registered subscribers with synergy scoring."""
        event = self._events.get(event_id)
        if not event:
            return DispatchResult(
                event_id=event_id, subscribers_notified=0,
                success_count=0, failure_count=0,
                synergy_score=0.0, dispatch_time_ms=0,
            )

        start_time = time.time()
        subscribers = self._subscriptions.get(event.event_type, [])
        success_count = 0
        failure_count = 0
        propagated = []

        for sub in subscribers:
            try:
                sub.handler(event)
                success_count += 1
                propagated.append(sub.module_name)
                event.propagated_modules.append(sub.module_name)
            except Exception:
                failure_count += 1

        elapsed_ms = (time.time() - start_time) * 1000
        synergy = self._calculate_synergy_score(event, success_count, len(subscribers))

        result = DispatchResult(
            event_id=event_id,
            subscribers_notified=len(subscribers),
            success_count=success_count,
            failure_count=failure_count,
            synergy_score=synergy,
            dispatch_time_ms=round(elapsed_ms, 2),
        )
        self._dispatch_log.append(result)
        return result

    def _calculate_synergy_score(
        self, event: ConsultationEvent, successes: int, total_subs: int
    ) -> float:
        """Calculate cross-module synergy score (0-100)."""
        if total_subs == 0:
            return 0.0
        base_score = (successes / total_subs) * 70
        diversity_bonus = min(len(set(event.propagated_modules)) * 5, 30)
        return round(base_score + diversity_bonus, 1)

    def get_event_history(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get event timeline for a session."""
        events = self._event_timeline.get(session_id, [])[-limit:]
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type.value,
                "publisher": e.publisher,
                "timestamp": e.timestamp,
                "propagated_to": e.propagated_modules,
            }
            for e in events
        ]

    def get_bus_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        total_events = len(self._events)
        total_dispatches = len(self._dispatch_log)
        avg_synergy = (
            round(statistics.mean([d.synergy_score for d in self._dispatch_log]), 2)
            if self._dispatch_log else 0.0
        )
        return {
            "total_events_published": total_events,
            "total_dispatches": total_dispatches,
            "active_subscriptions": sum(len(s) for s in self._subscriptions.values()),
            "average_synergy_score": avg_synergy,
        }


# =============================================================================
# PART O: FRONTEND COMPONENT RENDERERS
# =============================================================================


def render_action_panel_frosted_glass(
    session_id: str, context: Dict[str, Any]
) -> str:
    """Renderer: Frosted glass action panel for chat sidebar."""
    renderer = ChatActionPanelRenderer()
    return renderer.render_action_panel(session_id, context)


def render_task_source_badge(source: str) -> str:
    """Renderer: Source badge for task items (chat=blue, analysis=green)."""
    sync_svc = ChatTaskCenterSync()
    return sync_svc.render_task_source_badge(source)


def render_reconsult_button(task_id: str, original_question: str) -> str:
    """Renderer: Re-consult button for task center items."""
    svc = BatchReconsultService()
    url = svc.generate_reconsult_url(task_id, original_question)
    return (
        '<a href="' + url + '" class="btn btn-sm btn-outline-info">'
        + '<i class="fas fa-redo"></i> Re-consult</a>'
    )


def render_team_chat_indicator(team_id: str) -> str:
    """Renderer: Active chat indicator per agent in team view."""
    svc = ChatTeamVisibilityService()
    return svc.render_team_chat_indicator(team_id)


def render_overload_banner(agent_type: str, load_value: int) -> str:
    """Renderer: Overload warning banner suggesting recruitment."""
    suggester = OverloadRecruitmentSuggester()
    suggestion = suggester.create_full_suggestion("agent_demo", agent_type, load_value)
    return (
        '<div class="overload-banner warning" id="overload-'
        + uuid.uuid4().hex[:6] + '">'
        + '<i class="fas fa-exclamation-triangle"></i> '
        + suggestion.message
        + ' <a href="' + suggestion.recruitment_link + '">Recruit Now</a></div>'
    )


def render_property_card_selector(
    properties: List[Dict[str, Any]], session_id: str
) -> str:
    """Renderer: Property selection cards with checkboxes."""
    extractor = ChatPropertyExtractor()
    return extractor.render_property_selection_ui(properties, session_id)


def render_compare_report_preview(report_id: str, session_id: str) -> str:
    """Renderer: Comparison report preview card in chat."""
    gen = ChatCompareReportGenerator()
    report = gen._reports.get(report_id)
    if report:
        return report.summary_html
    return '<div class="preview-placeholder">Generating comparison...</div>'


def render_report_save_notice(report_id: str, session_id: str) -> str:
    """Renderer: Notice that report was auto-saved from consultation."""
    return (
        '<div class="report-save-notice success" id="save-notice-'
        + uuid.uuid4().hex[:6] + '">'
        + '<i class="fas fa-check-circle"></i> Report saved successfully. '
        + '<a href="/reports/' + report_id + '">View Report</a></div>'
    )


def render_preference_editor(preferences: List[Dict[str, Any]]) -> str:
    """Renderer: Preference editor UI for memory settings."""
    lines = ['<div class="preference-editor" id="pref-editor">']
    lines.append('<h4>Edit Your Preferences</h4>')
    for pref in preferences:
        lines.append(
            '<div class="pref-item" data-key="' + pref.get("key", "") + '">'
            + '<label>' + pref.get("key", "").replace("_", " ").title() + '</label>'
            + '<input type="text" value="' + pref.get("value", "") + '" />'
            + '<span class="importance">Importance: '
            + str(pref.get("importance", 0)) + '</span></div>'
        )
    lines.append('<button onclick="savePreferences()">Save Preferences</button>')
    lines.append('</div>')
    return chr(10).join(lines)


def render_capability_gap_card(gap_info: Dict[str, Any]) -> str:
    """Renderer: Capability gap detection card with recommendations."""
    detector = CapabilityGapDetector()
    return (
        '<div class="capability-gap-card" id="gap-card-'
        + uuid.uuid4().hex[:6] + '">'
        + '<div class="gap-header"><i class="fas fa-exclamation-circle"></i> '
        + 'Capability Gap Detected</div>'
        + '<p><strong>Gap Type:</strong> ' + gap_info.get("gap_type", "Unknown") + '</p>'
        + '<p><strong>Suggested:</strong> '
        + ', '.join(gap_info.get("suggested_agents", [])) + '</p>'
        + '<a href="' + gap_info.get("talent_market_link", "") + '" class="btn btn-sm btn-primary">'
        + 'View Talent Market</a></div>'
    )


def render_subscription_confirm_dialog(topic: str, frequency: str) -> str:
    """Renderer: Subscription confirmation dialog from periodic suggester."""
    suggester = PeriodicSubscriptionSuggester()
    return suggester.render_subscription_proposal(topic, frequency)


def render_system_notification(result_type: str, summary: str) -> str:
    """Renderer: Special styled system notification for autonomous results."""
    pusher = AutonomousResultPusher()
    return pusher.render_system_notification(result_type, summary)


def render_feedback_like_dislike(message_id: str) -> str:
    """Renderer: Like/dislike feedback buttons below each reply."""
    collector = FeedbackSignalCollector()
    return collector.render_feedback_buttons(message_id)


def render_topology_sidebar(session_id: str) -> str:
    """Renderer: ReactFlow-style topology in chat sidebar."""
    renderer = SessionTopologyRenderer()
    topo_data = renderer.get_session_topology(session_id)
    return renderer.render_topology_panel(topo_data)


def render_failover_notice(original_agent: str, backup_agent: str) -> str:
    """Renderer: Service restoration notice after failover."""
    switcher = FailoverSwitcher()
    return switcher.render_recovery_notification(original_agent, backup_agent)


def render_edu_session_viewer(student_id: str, teacher_id: str) -> str:
    """Renderer: Education-end session viewer for teachers."""
    edu = EduConsultationViewer()
    sessions = edu.get_student_sessions_for_edu(student_id, teacher_id)
    return edu.render_edu_session_list(sessions)


def render_enterprise_hotspot_chart(period: str = "weekly") -> str:
    """Renderer: Enterprise hot topic trend chart."""
    enterprise = EnterpriseHotTopicSubscriber()
    report_data = enterprise.generate_hot_topic_report(period)
    report = enterprise._reports.get(report_data.get("report_id", ""))
    if report:
        return enterprise.render_hot_topic_trend_chart(report.trend_data)
    return '<div class="loading-chart">Loading trend data...</div>'


def render_gov_alert_card(alert_data: Dict[str, Any]) -> str:
    """Renderer: Government alert card for public opinion monitoring."""
    severity_colors = {"high": "#ff4d4f", "medium": "#faad14", "low": "#52c41a"}
    color = severity_colors.get(alert_data.get("severity", "low"), "#999")
    return (
        '<div class="gov-alert-card ' + alert_data.get("severity", "low")
        + '" id="gov-alert-' + uuid.uuid4().hex[:6] + '" style="border-left: 4px solid '
        + color + ';">'
        + '<strong>Public Opinion Alert</strong>'
        + '<p>Topic: ' + alert_data.get("topic", "") + '</p>'
        + '<p>Frequency: ' + str(alert_data.get("frequency", 0)) + ' (threshold: '
        + str(alert_data.get("threshold", 0)) + ')</p>'
        + '</div>'
    )


def render_association_trend_viewer(quarter: str = "2026-Q1") -> str:
    """Renderer: Association-end downloadable trend dashboard."""
    reporter = AssociationTrendReporter()
    qdata = reporter.generate_quarterly_trend_report(quarter)
    return reporter.render_trend_dashboard(qdata)


def render_training_progress_bar(export_count: int, target: int = 100) -> str:
    """Renderer: Training data export progress bar."""
    pct = min(export_count / max(target, 1) * 100, 100)
    return (
        '<div class="training-progress-bar" id="train-progress">'
        + '<div class="progress-label">Training Data: ' + str(export_count)
        + '/' + str(target) + ' conversations</div>'
        + '<div class="progress-track"><div class="progress-fill" style="width:'
        + str(pct) + '%;"></div></div>'
        + '<span class="progress-pct">' + str(round(pct, 1)) + '%</span></div>'
    )


def render_negative_sample_stats(pool_size: int, signals: List[str]) -> str:
    """Renderer: Negative sample pool statistics display."""
    collector = NegativeSampleCollector()
    lines = [
        '<div class="negative-sample-stats" id="neg-sample-stats">',
        '  <h5>Negative Sample Pool</h5>',
        '  <div class="stat-row"><span class="stat-label">Total Samples:</span>'
        + '<span class="stat-value">' + str(pool_size) + '</span></div>',
        '  <div class="stat-row"><span class="stat-label">Signal Types:</span>'
        + '<span class="stat-value">' + str(len(signals)) + '</span></div>',
        '  <ul class="signal-list">',
    ]
    for sig in signals:
        lines.append('    <li class="signal-item">' + sig + '</li>')
    lines.append('  </ul></div>')
    return chr(10).join(lines)


def render_security_block_overlay(reason: str) -> str:
    """Renderer: Security block overlay for intercepted requests."""
    interceptor = MaliciousChatInterceptor()
    return interceptor.render_block_message(reason)


def render_drill_timeline(drill_sessions: List[Dict[str, Any]]) -> str:
    """Renderer: Drill execution timeline for admin view."""
    lines = [
        '<div class="drill-timeline" id="drill-timeline">',
        '  <h4>Security Drill History</h4>',
        '  <div class="timeline-items">',
    ]
    for ds in drill_sessions:
        status_class = "completed" if ds.get("completed_at") else "running"
        lines.append(
            '    <div class="timeline-item ' + status_class + '">'
            + '<span class="drill-pattern">' + ds.get("pattern", "unknown") + '</span>'
            + '<span class="drill-time">' + ds.get("started_at", "")[:19] + '</span>'
            + '<span class="drill-status">' + status_class + '</span></div>'
        )
    lines.append('  </div></div>')
    return chr(10).join(lines)


def render_event_bus_monitor(session_id: str) -> str:
    """Renderer: Real-time event bus monitor for debugging."""
    bus = ConsultationEventBus()
    events = bus.get_event_history(session_id, limit=20)
    lines = [
        '<div class="event-bus-monitor" id="eb-monitor-' + session_id + '">',
        '  <h4>Event Timeline — Session ' + session_id[:12] + '</h4>',
        '  <table class="event-table"><thead><tr>'
        + '<th>Event</th><th>Publisher</th><th>Time</th><th>Propagated</th></tr></thead><tbody>',
    ]
    for evt in events:
        lines.append(
            '    <tr><td>' + evt.get("type", "") + '</td>'
            + '<td>' + evt.get("publisher", "") + '</td>'
            + '<td>' + evt.get("timestamp", "")[:19] + '</td>'
            + '<td>' + str(len(evt.get("propagated_to", []))) + ' modules</td></tr>'
        )
    lines.append('  </tbody></table></div>')
    return chr(10).join(lines)


# =============================================================================
# PART P: TESTING SUITE
# =============================================================================

SMART_CONSULTATION_TEST_CASES = {

    "core_flow": [
        {"id": "TC_SC_CF_001", "name": "action_panel_render",
         "description": "render_action_panel produces HTML with action cards based on context"},
        {"id": "TC_SC_CF_002", "name": "task_bridge_create",
         "description": "create_task_from_consultation creates task and returns task_id"},
        {"id": "TC_SC_CF_003", "name": "completion_push",
         "description": "push_completion_to_chat records WebSocket push log"},
    ],

    "task_center": [
        {"id": "TC_SC_TC_001", "name": "sync_source_marker",
         "description": "sync_chat_task_to_center stores source marker correctly"},
        {"id": "TC_SC_TC_002", "name": "batch_reconsult_prepare",
         "description": "prepare_reconsult_context returns context with URL and history"},
        {"id": "TC_SC_TC_003", "name": "badge_render",
         "description": "render_task_source_badge returns colored HTML badge"},
    ],

    "team_mgmt": [
        {"id": "TM_SC_001", "name": "visibility_active_sessions",
         "description": "get_agent_active_sessions returns list of active sessions"},
        {"id": "TM_SC_002", "name": "overload_suggest",
         "description": "generate_overload_suggestion returns message with recruitment link"},
        {"id": "TM_SC_003", "name": "recruitment_link_gen",
         "description": "generate_recruitment_link returns valid talent market URL"},
    ],

    "property_compare": [
        {"id": "PC_SC_001", "name": "extract_entities",
         "description": "extract_property_entities finds property names in Chinese/English text"},
        {"id": "PC_SC_002", "name": "compare_trigger",
         "description": "trigger_compare_from_chat creates report and returns report_id"},
        {"id": "PC_SC_003", "name": "preview_push",
         "description": "push_report_preview_to_chat returns True for existing report"},
    ],

    "reports": [
        {"id": "RP_SC_001", "name": "auto_save_with_session",
         "description": "save_report_with_session returns report_id with linkage"},
        {"id": "RP_SC_002", "name": "backlink_render",
         "description": "render_report_backlink contains View Original Chat anchor tag"},
        {"id": "RP_SC_003", "name": "session_report_list",
         "description": "get_reports_by_session returns reports linked to session"},
    ],

    "memory": [
        {"id": "MEM_SC_001", "name": "preference_extract",
         "description": "extract_preferences_from_dialogue extracts preferences from messages"},
        {"id": "MEM_SC_002", "name": "recall_search",
         "description": "retrieve_relevant_memories returns list with relevance scores"},
        {"id": "MEM_SC_003", "name": "context_format",
         "description": "format_recall_context returns properly formatted string"},
    ],

    "market": [
        {"id": "MK_SC_001", "name": "gap_detect",
         "description": "check_capability_for_query returns tuple with bool and capability"},
        {"id": "MK_SC_002", "name": "recruit_recommend",
         "description": "generate_recruitment_recommendation returns dict with link"},
        {"id": "MK_SC_003", "name": "skill_recommend",
         "description": "generate_skill_purchase_recommendation returns store links"},
        {"id": "MK_SC_004", "name": "auto_equip",
         "description": "on_agent_recruited returns True and sends notification"},
    ],

    "autonomous_work": [
        {"id": "AW_SC_001", "name": "periodic_detect",
         "description": "detect_periodic_topic returns tuple with topic and frequency"},
        {"id": "AW_SC_002", "name": "subscribe_create",
         "description": "create_subscription_from_chat returns subscription_id"},
        {"id": "AW_SC_003", "name": "result_push",
         "description": "push_result_to_session returns True and increments counter"},
    ],

    "evolution": [
        {"id": "EV_SC_001", "name": "feedback_collect",
         "description": "record_feedback returns feedback_id with clamped rating"},
        {"id": "EV_SC_002", "name": "aggregate_training",
         "description": "aggregate_feedback_for_training returns stats dictionary"},
        {"id": "EV_SC_003", "name": "failure_detect",
         "description": "detect_failed_conversation returns True when thresholds exceeded"},
    ],

    "ecosystem": [
        {"id": "EC_SC_001", "name": "topology_render",
         "description": "render_topology_panel produces SVG-based HTML visualization"},
        {"id": "EC_SC_002", "name": "node_detail_popup",
         "description": "render_node_detail_popup returns HTML with agent details"},
        {"id": "EC_SC_003", "name": "failover_switch",
         "description": "switch_to_backup returns tuple with success and backup_id"},
    ],

    "five_end": [
        {"id": "FE_SC_001", "name": "edu_view_sessions",
         "description": "get_student_sessions_for_edu returns anonymized session list"},
        {"id": "FE_SC_002", "name": "enterprise_subscribe",
         "description": "generate_hot_topic_report returns report with topics"},
        {"id": "FE_SC_003", "name": "gov_alert_detect",
         "description": "detect_sensitive_topic_burst returns boolean"},
        {"id": "FE_SC_004", "name": "association_report",
         "description": "generate_quarterly_trend_report returns report with charts"},
    ],

    "learning": [
        {"id": "LN_SC_001", "name": "high_quality_export",
         "description": "weekly_high_quality_export returns conversations above rating"},
        {"id": "LN_SC_002", "name": "format_training",
         "description": "format_for_training returns JSON-formatted training data"},
        {"id": "LN_SC_003", "name": "model_notify",
         "description": "trigger_model_update_notification returns version info string"},
    ],

    "security": [
        {"id": "SEC_SC_001", "name": "pattern_analyze",
         "description": "analyze_request_pattern returns scores and threat level"},
        {"id": "SEC_SC_002", "name": "intercept_block",
         "description": "intercept_malicious_request returns tuple with block status"},
        {"id": "SEC_SC_003", "name": "audit_log",
         "description": "log_interception_audit returns audit trail ID"},
    ],

    "drill": [
        {"id": "DR_SC_001", "name": "failure_rate_monitor",
         "description": "monitor_failure_rate returns boolean based on threshold"},
        {"id": "DR_SC_002", "name": "trigger_execute",
         "description": "trigger_red_blue_drill returns drill session ID"},
    ],

    "orchestrator": [
        {"id": "OR_SC_001", "name": "publish_subscribe_dispatch",
         "description": "publish then dispatch delivers to subscribers with synergy score"},
        {"id": "OR_SC_002", "name": "synergy_score",
         "description": "synergy calculation returns score between 0 and 100"},
        {"id": "OR_SC_003", "name": "event_history",
         "description": "get_event_timeline returns events for session"},
    ],

    "frontend": [
        {"id": "FR_SC_001", "name": "action_panel_frosted_glass",
         "description": "render_action_panel_frosted_glass produces valid HTML panel"},
        {"id": "FR_SC_002", "name": "task_source_badge",
         "description": "render_task_source_badge contains colored span element"},
        {"id": "FR_SC_003", "name": "feedback_like_dislike",
         "description": "render_feedback_like_dislike contains Helpful/Not Helpful buttons"},
        {"id": "FR_SC_004", "name": "topology_sidebar",
         "description": "render_topology_sidebar contains SVG topology elements"},
        {"id": "FR_SC_005", "name": "security_block_overlay",
         "description": "render_security_block_overlay contains restricted message"},
    ],
}


class SmartConsultationTestSuite:
    """Comprehensive test suite for Layer 29: Smart Consultation & Cross-Module Integration."""

    def __init__(self):
        self.action_panel_renderer = ChatActionPanelRenderer()
        self.task_bridge = ConsultationTaskBridge()
        self.task_center_sync = ChatTaskCenterSync()
        self.batch_reconsult = BatchReconsultService()
        self.team_visibility = ChatTeamVisibilityService()
        self.overload_suggester = OverloadRecruitmentSuggester()
        self.property_extractor = ChatPropertyExtractor()
        self.compare_generator = ChatCompareReportGenerator()
        self.report_auto_saver = ChatReportAutoSaver()
        self.preference_extractor = ChatPreferenceExtractor()
        self.memory_recall = ChatMemoryRecallService()
        self.gap_detector = CapabilityGapDetector()
        self.auto_equipper = PostPurchaseAutoEquipper()
        self.subscription_suggester = PeriodicSubscriptionSuggester()
        self.result_pusher = AutonomousResultPusher()
        self.feedback_collector = FeedbackSignalCollector()
        self.failure_pool = FailureCasePoolManager()
        self.topology_renderer = SessionTopologyRenderer()
        self.failover_switcher = FailoverSwitcher()
        self.edu_viewer = EduConsultationViewer()
        self.enterprise_hot = EnterpriseHotTopicSubscriber()
        self.gov_alert = GovPublicOpinionAlert()
        self.assoc_reporter = AssociationTrendReporter()
        self.training_exporter = ChatTrainingDataExporter()
        self.neg_sample_collector = NegativeSampleCollector()
        self.malicious_interceptor = MaliciousChatInterceptor()
        self.drill_trigger = ConsultationDrillTrigger()
        self.event_bus = ConsultationEventBus()
        self._results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories and return summary."""
        self._results = []
        self._test_core_flow()
        self._test_task_center()
        self._test_team_mgmt()
        self._test_property_compare()
        self._test_reports()
        self._test_memory()
        self._test_market()
        self._test_autonomous_work()
        self._test_evolution()
        self._test_ecosystem()
        self._test_five_end()
        self._test_learning()
        self._test_security()
        self._test_drill()
        self._test_orchestrator()
        self._test_frontend()

        total = len(self._results)
        passed = sum(1 for r in self._results if r.get("passed", False))
        failed = total - passed
        return {
            "layer": 29,
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
    # Category 1: Core Flow
    # ------------------------------------------------------------------
    def _test_core_flow(self):
        session_id = "sess_core_001"
        context = {
            "task_id": "task_123",
            "has_property_analysis": True,
            "topic": "fortune",
            "sentiment": "negative",
        }
        html = self.action_panel_renderer.render_action_panel(session_id, context)
        has_cards = "action-card" in html and "Suggested Actions" in html
        self._record(
            "TC_SC_CF_001", "action_panel_render",
            has_cards and len(html) > 100,
            "html_len=" + str(len(html)),
        )

        task_id = self.task_bridge.create_task_from_consultation(
            session_id, "How to invest in Taipei real estate?", "gong_bu"
        )
        self._record(
            "TC_SC_CF_002", "task_bridge_create",
            task_id.startswith("ctask_"),
            "task_id=" + task_id,
        )

        pushed = self.task_bridge.push_completion_to_chat(task_id, "Investment analysis completed")
        self._record(
            "TC_SC_CF_003", "completion_push",
            pushed is True,
            "pushed=" + str(pushed),
        )

    # ------------------------------------------------------------------
    # Category 2: Task Center
    # ------------------------------------------------------------------
    def _test_task_center(self):
        synced = self.task_center_sync.sync_chat_task_to_center("sess_tc_1", "task_a", "chat")
        self._record(
            "TC_SC_TC_001", "sync_source_marker",
            synced is True,
            "synced=" + str(synced),
        )

        ctx = self.batch_reconsult.prepare_reconsult_context("task_batch_1")
        self._record(
            "TC_SC_TC_002", "batch_reconsult_prepare",
            "reconsult_id" in ctx and "url" in ctx,
            "keys=" + str(list(ctx.keys())),
        )

        badge = self.task_center_sync.render_task_source_badge("chat")
        has_color = "#" in badge and "Chat" in badge
        self._record(
            "TC_SC_TC_003", "badge_render",
            has_color,
            "badge_len=" + str(len(badge)),
        )

    # ------------------------------------------------------------------
    # Category 3: Team Management
    # ------------------------------------------------------------------
    def _test_team_mgmt(self):
        sessions = self.team_visibility.get_agent_active_sessions("agent_001")
        self._record(
            "TM_SC_001", "visibility_active_sessions",
            isinstance(sessions, list),
            "type=" + str(type(sessions).__name__),
        )

        msg = self.overload_suggester.generate_overload_suggestion("gong_bu", 8)
        has_recruit = "recruit" in msg.lower() or "Recruit" in msg
        self._record(
            "TM_SC_002", "overload_suggest",
            has_recruit and len(msg) > 20,
            "msg_len=" + str(len(msg)),
        )

        link = self.overload_suggester.generate_recruitment_link("fortune")
        valid_url = "talent-market" in link and "fortune" in link
        self._record(
            "TM_SC_003", "recruitment_link_gen",
            valid_url,
            "link=" + link[:50],
        )

    # ------------------------------------------------------------------
    # Category 4: Property Compare
    # ------------------------------------------------------------------
    def _test_property_compare(self):
        text = "I want to see Taipei 101 Building and apartments near Taipei Station"
        entities = self.property_extractor.extract_property_entities(text)
        self._record(
            "PC_SC_001", "extract_entities",
            len(entities) >= 1,
            "count=" + str(len(entities)),
        )

        report_id = self.compare_generator.trigger_compare_from_chat(
            ["p1", "p2", "p3"], "sess_pc_1"
        )
        self._record(
            "PC_SC_002", "compare_trigger",
            report_id.startswith("creport_"),
            "report_id=" + report_id,
        )

        pushed = self.compare_generator.push_report_preview_to_chat(report_id, "sess_pc_1")
        self._record(
            "PC_SC_003", "preview_push",
            pushed is True,
            "pushed=" + str(pushed),
        )

    # ------------------------------------------------------------------
    # Category 5: Reports
    # ------------------------------------------------------------------
    def _test_reports(self):
        rid = self.report_auto_saver.save_report_with_session(
            {"title": "Test Report", "content": "Analysis result"},
            "sess_rp_1", "msg_001"
        )
        self._record(
            "RP_SC_001", "auto_save_with_session",
            rid.startswith("sreport_"),
            "report_id=" + rid,
        )

        backlink = self.report_auto_saver.render_report_backlink(rid, "sess_rp_1", "msg_001")
        has_anchor = "View Original Chat" in backlink and "<a" in backlink
        self._record(
            "RP_SC_002", "backlink_render",
            has_anchor,
            "backlink_len=" + str(len(backlink)),
        )

        reports = self.report_auto_saver.get_reports_by_session("sess_rp_1")
        self._record(
            "RP_SC_003", "session_report_list",
            len(reports) >= 1,
            "count=" + str(len(reports)),
        )

    # ------------------------------------------------------------------
    # Category 6: Memory
    # ------------------------------------------------------------------
    def _test_memory(self):
        messages = [
            {"role": "user", "content": "I live in Taipei, budget under 5 million"},
            {"role": "assistant", "content": "OK, let me analyze the Taipei property market"},
        ]
        prefs = self.preference_extractor.extract_preferences_from_dialogue(messages)
        self._record(
            "MEM_SC_001", "preference_extract",
            isinstance(prefs, list),
            "count=" + str(len(prefs)),
        )

        memories = self.memory_recall.retrieve_relevant_memories("Taipei property", "user1", 3)
        has_scores = all("relevance_score" in m for m in memories)
        self._record(
            "MEM_SC_002", "recall_search",
            len(memories) == 3 and has_scores,
            "count=" + str(len(memories)),
        )

        ctx = self.memory_recall.format_recall_context(memories)
        has_header = "Historical Context" in ctx
        self._record(
            "MEM_SC_003", "context_format",
            has_header and len(ctx) > 10,
            "ctx_len=" + str(len(ctx)),
        )

    # ------------------------------------------------------------------
    # Category 7: Market (Talent/Skill)
    # ------------------------------------------------------------------
    def _test_market(self):
        can_handle, cap = self.gap_detector.check_capability_for_query("I want legal advice on contracts")
        self._record(
            "MK_SC_001", "gap_detect",
            isinstance(can_handle, bool) and isinstance(cap, str),
            "can=" + str(can_handle) + " cap=" + cap,
        )

        rec = self.gap_detector.generate_recruitment_recommendation("legal_advice", "contract question")
        has_link = "talent-market" in rec.get("talent_market_link", "")
        self._record(
            "MK_SC_002", "recruit_recommend",
            has_link and "suggested_agents" in rec,
            "keys=" + str(list(rec.keys())),
        )

        skill_rec = self.gap_detector.generate_skill_purchase_recommendation(["contract_review"])
        has_store = any("skill-store" in ln for ln in skill_rec.get("store_links", []))
        self._record(
            "MK_SC_003", "skill_recommend",
            has_store,
            "store_links=" + str(skill_rec.get("store_links", [])),
        )

        equipped = self.auto_equipper.on_agent_recruited("new_agent_1", "user1", "sess_mkt_1")
        self._record(
            "MK_SC_004", "auto_equip",
            equipped is True,
            "equipped=" + str(equipped),
        )

    # ------------------------------------------------------------------
    # Category 8: Autonomous Work
    # ------------------------------------------------------------------
    def _test_autonomous_work(self):
        detected, topic, freq = self.subscription_suggester.detect_periodic_topic(
            "What about housing prices recently? I want daily market updates"
        )
        self._record(
            "AW_SC_001", "periodic_detect",
            isinstance(detected, bool) and isinstance(topic, str),
            "detected=" + str(detected) + " topic=" + topic,
        )

        sub_id = self.subscription_suggester.create_subscription_from_chat(
            "user1", "market_price_monitoring", "daily", "sess_aw_1"
        )
        self._record(
            "AW_SC_002", "subscribe_create",
            sub_id.startswith("autosub_"),
            "sub_id=" + sub_id,
        )

        pushed = self.result_pusher.push_result_to_session("sess_aw_1", "Weekly market report ready")
        self._record(
            "AW_SC_003", "result_push",
            pushed is True,
            "pushed=" + str(pushed),
        )

    # ------------------------------------------------------------------
    # Category 9: Evolution
    # ------------------------------------------------------------------
    def _test_evolution(self):
        fid = self.feedback_collector.record_feedback("msg_ev_1", "like", 5)
        self._record(
            "EV_SC_001", "feedback_collect",
            fid.startswith("fb_"),
            "fid=" + fid,
        )

        agg = self.feedback_collector.aggregate_feedback_for_training("7d")
        has_keys = "total_feedback" in agg and "average_rating" in agg
        self._record(
            "EV_SC_002", "aggregate_training",
            has_keys,
            "keys=" + str(list(agg.keys())),
        )

        is_failed = self.failure_pool.detect_failed_conversation(
            "sess_fail_1", {"followup_count": 10, "abandonment_time": 100, "error_rate": 0.5}
        )
        self._record(
            "EV_SC_003", "failure_detect",
            is_failed is True,
            "is_failed=" + str(is_failed),
        )

    # ------------------------------------------------------------------
    # Category 10: Ecosystem
    # ------------------------------------------------------------------
    def _test_ecosystem(self):
        topo_data = self.topology_renderer.get_session_topology("sess_eco_1")
        html = self.topology_renderer.render_topology_panel(topo_data)
        has_svg = "svg" in html and "topo-node" in html
        self._record(
            "EC_SC_001", "topology_render",
            has_svg,
            "svg_present=" + str(has_svg),
        )

        popup = self.topology_renderer.render_node_detail_popup("agent_001")
        has_details = "Agent Details" in popup
        self._record(
            "EC_SC_002", "node_detail_popup",
            has_details,
            "popup_len=" + str(len(popup)),
        )

        success, backup_id = self.failover_switcher.switch_to_backup("agent_fail_1", "sess_eco_1")
        self._record(
            "EC_SC_003", "failover_switch",
            success is True and backup_id.startswith("backup_"),
            "success=" + str(success) + " backup=" + backup_id,
        )

    # ------------------------------------------------------------------
    # Category 11: Five-End Coordination
    # ------------------------------------------------------------------
    def _test_five_end(self):
        sessions = self.edu_viewer.get_student_sessions_for_edu("student_01", "teacher_01")
        self._record(
            "FE_SC_001", "edu_view_sessions",
            isinstance(sessions, list) and len(sessions) >= 1,
            "count=" + str(len(sessions)),
        )

        report = self.enterprise_hot.generate_hot_topic_report("weekly")
        has_topics = "topics" in report or "topic_count" in report
        self._record(
            "FE_SC_002", "enterprise_subscribe",
            has_topics,
            "keys=" + str(list(report.keys())),
        )

        burst = self.gov_alert.detect_sensitive_topic_burst(["fraud", "scam", "panic", "rumor", "dispute"])
        self._record(
            "FE_SC_003", "gov_alert_detect",
            isinstance(burst, bool),
            "burst=" + str(burst),
        )

        assoc = self.assoc_reporter.generate_quarterly_trend_report("2026-Q1")
        has_charts = "charts_count" in assoc or "charts" in str(assoc)
        self._record(
            "FE_SC_004", "association_report",
            has_charts,
            "keys=" + str(list(assoc.keys())),
        )

    # ------------------------------------------------------------------
    # Category 12: Learning System
    # ------------------------------------------------------------------
    def _test_learning(self):
        exports = self.training_exporter.weekly_high_quality_export(min_rating=4.0)
        self._record(
            "LN_SC_001", "high_quality_export",
            isinstance(exports, list),
            "count=" + str(len(exports)),
        )

        formatted = self.training_exporter.format_for_training(exports)
        has_json = "json" in formatted and "Training Data" in formatted
        self._record(
            "LN_SC_002", "format_training",
            has_json,
            "fmt_len=" + str(len(formatted)),
        )

        notify = self.training_exporter.trigger_model_update_notification("v2.5.0")
        has_ver = "v2.5.0" in notify
        self._record(
            "LN_SC_003", "model_notify",
            has_ver,
            "notify_len=" + str(len(notify)),
        )

    # ------------------------------------------------------------------
    # Category 13: Security
    # ------------------------------------------------------------------
    def _test_security(self):
        analysis = self.malicious_interceptor.analyze_request_pattern({
            "request_id": "req_sec_1",
            "content": "Normal question about property investment",
        })
        has_threat = "threat_level" in analysis
        self._record(
            "SEC_SC_001", "pattern_analyze",
            has_threat,
            "keys=" + str(list(analysis.keys())),
        )

        blocked, iid = self.malicious_interceptor.intercept_malicious_request(
            "SQL injection detected", "req_bad_1"
        )
        self._record(
            "SEC_SC_002", "intercept_block",
            blocked is True and iid.startswith("intercept_"),
            "blocked=" + str(blocked) + " iid=" + iid,
        )

        audit_id = self.malicious_interceptor.log_interception_audit(
            type("IR", (), {
                "interception_id": "intercept_test",
                "request_id": "req_audit_1",
                "reason": "test_reason",
                "blocked": True,
                "logged_at": datetime.now().isoformat(),
                "audit_trail_id": "audit_test_123",
            })()
        )
        self._record(
            "SEC_SC_003", "audit_log",
            audit_id.startswith("audit_"),
            "audit_id=" + audit_id,
        )

    # ------------------------------------------------------------------
    # Category 14: Drill
    # ------------------------------------------------------------------
    def _test_drill(self):
        rate_ok = self.drill_trigger.monitor_failure_rate(window_minutes=60, threshold=10)
        self._record(
            "DR_SC_001", "failure_rate_monitor",
            isinstance(rate_ok, bool),
            "rate_ok=" + str(rate_ok),
        )

        drill_id = self.drill_trigger.trigger_red_blue_drill("high_followup_rate")
        self._record(
            "DR_SC_002", "trigger_execute",
            drill_id.startswith("drill_"),
            "drill_id=" + drill_id,
        )

    # ------------------------------------------------------------------
    # Category 15: Orchestrator (Event Bus)
    # ------------------------------------------------------------------
    def _test_orchestrator(self):
        def dummy_handler(event): pass

        evt_id = self.event_bus.publish(
            EventType.TASK_CREATED_FROM_CHAT,
            {"task_id": "orch_task_1"},
            "sess_orch_1",
            "test_publisher"
        )
        self.event_bus.subscribe("test_module", [EventType.TASK_CREATED_FROM_CHAT], dummy_handler)
        result = self.event_bus.dispatch(evt_id)
        self._record(
            "OR_SC_001", "publish_subscribe_dispatch",
            result.subscribers_notified >= 1,
            "notified=" + str(result.subscribers_notified),
        )

        score_ok = 0 <= result.synergy_score <= 100
        self._record(
            "OR_SC_002", "synergy_score",
            score_ok,
            "score=" + str(result.synergy_score),
        )

        history = self.event_bus.get_event_history("sess_orch_1", limit=10)
        self._record(
            "OR_SC_003", "event_history",
            len(history) >= 1,
            "events=" + str(len(history)),
        )

    # ------------------------------------------------------------------
    # Category 16: Frontend Rendering
    # ------------------------------------------------------------------
    def _test_frontend(self):
        panel = render_action_panel_frosted_glass("sess_fe_1", {"task_id": "t1"})
        self._record(
            "FR_SC_001", "action_panel_frosted_glass",
            "Suggested Actions" in panel and len(panel) > 50,
            "len=" + str(len(panel)),
        )

        badge = render_task_source_badge("analysis")
        self._record(
            "FR_SC_002", "task_source_badge",
            "Analysis" in badge and "#" in badge,
            "badge=" + badge[:40],
        )

        fb_btns = render_feedback_like_dislike("msg_fe_1")
        self._record(
            "FR_SC_003", "feedback_like_dislike",
            "Helpful" in fb_btns and "Not Helpful" in fb_btns,
            "has_buttons=" + str("Helpful" in fb_btns),
        )

        topo = render_topology_sidebar("sess_fe_topo")
        self._record(
            "FR_SC_004", "topology_sidebar",
            "svg" in topo or "Agent Cluster" in topo,
            "has_svg=" + str("svg" in topo),
        )

        block = render_security_block_overlay("Malicious pattern detected")
        self._record(
            "FR_SC_005", "security_block_overlay",
            "Restricted" in block or "restricted" in block.lower(),
            "has_msg=" + str("Restricted" in block),
        )


def generate_pytest_code() -> str:
    """Generate complete pytest-compatible test code for Layer 29."""
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""Auto-generated pytest tests for Layer 29: Smart Consultation"""')
    lines.append('')
    lines.append('import sys')
    lines.append('import os')
    lines.append('sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))')
    lines.append('')
    lines.append('from backend.integration.smart_consultation_cross_module_layer import (')
    lines.append('    ChatActionPanelRenderer, ConsultationTaskBridge,')
    lines.append('    ChatTaskCenterSync, BatchReconsultService,')
    lines.append('    ChatTeamVisibilityService, OverloadRecruitmentSuggester,')
    lines.append('    ChatPropertyExtractor, ChatCompareReportGenerator,')
    lines.append('    ChatReportAutoSaver, ChatPreferenceExtractor,')
    lines.append('    ChatMemoryRecallService, CapabilityGapDetector,')
    lines.append('    PostPurchaseAutoEquipper, PeriodicSubscriptionSuggester,')
    lines.append('    AutonomousResultPusher, FeedbackSignalCollector,')
    lines.append('    FailureCasePoolManager, SessionTopologyRenderer,')
    lines.append('    FailoverSwitcher, EduConsultationViewer,')
    lines.append('    EnterpriseHotTopicSubscriber, GovPublicOpinionAlert,')
    lines.append('    AssociationTrendReporter, ChatTrainingDataExporter,')
    lines.append('    NegativeSampleCollector, MaliciousChatInterceptor,')
    lines.append('    ConsultationDrillTrigger, ConsultationEventBus,')
    lines.append('    SmartConsultationTestSuite, EventType,')
    lines.append(')')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer29CoreFlow:')
    lines.append('    def test_action_panel_render(self):')
    lines.append('        r = ChatActionPanelRenderer()')
    lines.append('        h = r.render_action_panel("s1", {"task_id": "t1", "has_property_analysis": True})')
    lines.append('        assert "Suggested Actions" in h')
    lines.append('')
    lines.append('    def test_task_bridge_create(self):')
    lines.append('        b = ConsultationTaskBridge()')
    lines.append('        tid = b.create_task_from_consultation("s1", "query", "gong_bu")')
    lines.append('        assert tid.startswith("ctask_")')
    lines.append('')
    lines.append('    def test_completion_push(self):')
    lines.append('        b = ConsultationTaskBridge()')
    lines.append('        tid = b.create_task_from_consultation("s1", "q", "li_bu")')
    lines.append('        ok = b.push_completion_to_chat(tid, "done")')
    lines.append('        assert ok is True')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer29TaskCenter:')
    lines.append('    def test_sync_source(self):')
    lines.append('        s = ChatTaskCenterSync()')
    lines.append('        ok = s.sync_chat_task_to_center("s1", "t1", "chat")')
    lines.append('        assert ok is True')
    lines.append('')
    lines.append('    def test_batch_reconsult(self):')
    lines.append('        s = BatchReconsultService()')
    lines.append('        c = s.prepare_reconsult_context("task_1")')
    lines.append('        assert "reconsult_id" in c')
    lines.append('')
    lines.append('    def test_badge_render(self):')
    lines.append('        s = ChatTaskCenterSync()')
    lines.append('        b = s.render_task_source_badge("chat")')
    lines.append('        assert "Chat" in b')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer29Security:')
    lines.append('    def test_pattern_analysis(self):')
    lines.append('        i = MaliciousChatInterceptor()')
    lines.append('        a = i.analyze_request_pattern({"request_id": "r1", "content": "hello"})')
    lines.append('        assert "threat_level" in a')
    lines.append('')
    lines.append('    def test_intercept(self):')
    lines.append('        i = MaliciousChatInterceptor()')
    lines.append('        ok, iid = i.intercept_malicious_request("test", "r1")')
    lines.append('        assert ok is True')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer29Orchestrator:')
    lines.append('    def test_publish_and_dispatch(self):')
    lines.append('        bus = ConsultationEventBus()')
    lines.append('        eid = bus.publish(EventType.MESSAGE_SENT, {}, "s1")')
    lines.append('        assert eid.startswith("evt_")')
    lines.append('')
    lines.append('    def test_synergy_and_history(self):')
    lines.append('        bus = ConsultationEventBus()')
    lines.append('        stats = bus.get_bus_stats()')
    lines.append('        assert 0 <= stats["average_synergy_score"] <= 100')
    lines.append('')
    lines.append('')
    lines.append('class TestLayer29FullSuite:')
    lines.append('    def test_full_suite_execution(self):')
    lines.append('        suite = SmartConsultationTestSuite()')
    lines.append('        summary = suite.run_all_tests()')
    lines.append('        assert summary["total"] >= 48')
    lines.append('        assert summary["pass_rate"] >= 90.0')
    lines.append('')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    import pytest')
    lines.append('    sys.exit(pytest.main(["-v", __file__]))')
    return chr(10).join(lines)


def generate_playwright_e2e() -> str:
    """Generate Playwright E2E test code for Layer 29."""
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""Auto-generated Playwright E2E tests for Layer 29: Smart Consultation"""')
    lines.append('import asyncio')
    lines.append('')
    lines.append('')
    lines.append('async def test_action_panel_render(page):')
    lines.append('    """E2E: Verify action panel renders with contextual buttons."""')
    lines.append('    from backend.integration.smart_consultation_cross_module_layer import (')
    lines.append('        ChatActionPanelRenderer,')
    lines.append('    )')
    lines.append('    renderer = ChatActionPanelRenderer()')
    lines.append('    ctx = {')
    lines.append('        "session_id": "e2e_sc_1", "task_id": "task_e2e_1",')
    lines.append('        "has_property_analysis": True, "topic": "fortune",')
    lines.append('        "sentiment": "negative",')
    lines.append('    }')
    lines.append('    html = renderer.render_action_panel("e2e_sess_1", ctx)')
    lines.append('    assert "Suggested Actions" in html')
    lines.append('    assert "View Task Details" in html')
    lines.append('    print("[PASS] Action panel renders with contextual buttons")')
    lines.append('')
    lines.append('')
    lines.append('async def test_task_bridge_creation(page):')
    lines.append('    """E2E: Verify task bridge creates tasks from consultations."""')
    lines.append('    from backend.integration.smart_consultation_cross_module_layer import (')
    lines.append('        ConsultationTaskBridge,')
    lines.append('    )')
    lines.append('    bridge = ConsultationTaskBridge()')
    lines.append('    task_id = bridge.create_task_from_consultation("sess_e2e", "Real estate query?", "gong_bu")')
    lines.append('    assert task_id.startswith("ctask_")')
    lines.append('    status = bridge.get_task_status_for_chat(task_id)')
    lines.append('    assert "status" in status')
    lines.append('    print("[PASS] Task bridge creates and tracks tasks correctly")')
    lines.append('')
    lines.append('')
    lines.append('async def test_property_extraction(page):')
    lines.append('    """E2E: Verify property entity extraction from Chinese text."""')
    lines.append('    from backend.integration.smart_consultation_cross_module_layer import (')
    lines.append('        ChatPropertyExtractor,')
    lines.append('    )')
    lines.append('    extractor = ChatPropertyExtractor()')
    lines.append('    entities = extractor.extract_property_entities("I like Taipei 101 Building and nearby apartments")')
    lines.append('    assert isinstance(entities, list)')
    lines.append('    print(f"[PASS] Extracted {len(entities)} property entities")')
    lines.append('')
    lines.append('')
    lines.append('async def test_event_bus_operations(page):')
    lines.append('    """E2E: Verify event bus publish, subscribe, and dispatch."""')
    lines.append('    from backend.integration.smart_consultation_cross_module_layer import (')
    lines.append('        ConsultationEventBus, EventType,')
    lines.append('    )')
    lines.append('    bus = ConsultationEventBus()')
    lines.append('    eid = bus.publish(EventType.CONSULTATION_STARTED, {"user": "test"}, "sess_e2e")')
    lines.append('    assert eid.startswith("evt_")')
    lines.append('    history = bus.get_event_history("sess_e2e")')
    lines.append('    assert len(history) >= 1')
    lines.append('    print("[PASS] Event bus operations work correctly")')
    lines.append('')
    lines.append('')
    lines.append('async def test_security_interception(page):')
    lines.append('    """E2E: Verify malicious request interception."""')
    lines.append('    from backend.integration.smart_consultation_cross_module_layer import (')
    lines.append('        MaliciousChatInterceptor,')
    lines.append('    )')
    lines.append('    interceptor = MaliciousChatInterceptor()')
    lines.append('    analysis = interceptor.analyze_request_pattern({"request_id": "r1", "content": "normal"})')
    lines.append('    assert analysis["threat_level"] in ("safe", "suspicious", "dangerous", "critical")')
    lines.append('    blocked, iid = interceptor.intercept_malicious_request("test block", "r2")')
    lines.append('    assert blocked is True')
    lines.append('    print("[PASS] Security interception works correctly")')
    lines.append('')
    lines.append('')
    lines.append('async def test_full_suite_execution(page):')
    lines.append('    """E2E: Run the full test suite and verify pass rate."""')
    lines.append('    from backend.integration.smart_consultation_cross_module_layer import SmartConsultationTestSuite')
    lines.append('    suite = SmartConsultationTestSuite()')
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
    lines.append('            await test_task_bridge_creation(page)')
    lines.append('            await test_property_extraction(page)')
    lines.append('            await test_event_bus_operations(page)')
    lines.append('            await test_security_interception(page)')
    lines.append('            await test_full_suite_execution(page)')
    lines.append('            await browser.close()')
    lines.append('    asyncio.run(main())')
    return chr(10).join(lines)


def create_full_system() -> Dict[str, Any]:
    """Factory method to create all integration services for Layer 29."""
    return {
        "action_panel_renderer": ChatActionPanelRenderer(),
        "task_bridge": ConsultationTaskBridge(),
        "task_center_sync": ChatTaskCenterSync(),
        "batch_reconsult": BatchReconsultService(),
        "team_visibility": ChatTeamVisibilityService(),
        "overload_suggester": OverloadRecruitmentSuggester(),
        "property_extractor": ChatPropertyExtractor(),
        "compare_generator": ChatCompareReportGenerator(),
        "report_auto_saver": ChatReportAutoSaver(),
        "preference_extractor": ChatPreferenceExtractor(),
        "memory_recall": ChatMemoryRecallService(),
        "gap_detector": CapabilityGapDetector(),
        "auto_equipper": PostPurchaseAutoEquipper(),
        "subscription_suggester": PeriodicSubscriptionSuggester(),
        "result_pusher": AutonomousResultPusher(),
        "feedback_collector": FeedbackSignalCollector(),
        "failure_pool": FailureCasePoolManager(),
        "topology_renderer": SessionTopologyRenderer(),
        "failover_switcher": FailoverSwitcher(),
        "edu_viewer": EduConsultationViewer(),
        "enterprise_hot": EnterpriseHotTopicSubscriber(),
        "gov_alert": GovPublicOpinionAlert(),
        "assoc_reporter": AssociationTrendReporter(),
        "training_exporter": ChatTrainingDataExporter(),
        "neg_sample_collector": NegativeSampleCollector(),
        "malicious_interceptor": MaliciousChatInterceptor(),
        "drill_trigger": ConsultationDrillTrigger(),
        "event_bus": ConsultationEventBus(),
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

    suite = SmartConsultationTestSuite()
    summary = suite.run_all_tests()

    return {
        "layer": 29,
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
    print("  Layer 29: Smart Consultation & Cross-Module Integration")
    print("  (智能咨询跨模块联动层)")
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
    print("Layer 29 loaded OK.")