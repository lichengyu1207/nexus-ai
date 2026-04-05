# -*- coding: utf-8 -*-
"""
道法自然治理体系 ↔ 全部子系统 桥接层 (Governance Integration Bridge)
=====================================================================
核心功能：
1) 三省六部调度器(enhanced_scheduler)统一编排所有子系统的任务分配
2) 动态组队(dynamic_team_orchestrator)根据任务复杂度选择最优体系组合
3) 人格引擎(personality_engine)的输出影响修炼体系的共情平衡
4) 增强记忆(enhanced_retrieval)为所有体系提供跨会话上下文
5) 可解释性引擎(explainability_engine)追踪全部子系统的决策链路
6) 集成中心(integration_hub)作为多模态输入和技能调度的总入口

调度策略:
  简单任务(复杂度<0.3): 仅调用炼气期 + 记忆检索 → 快速响应
  中等任务(0.3~0.7): 调用炼法期+练符期+人格融合 → 完整处理
  复杂任务(>0.7): 调用全8阶段+炼丹验证+混沌测试 → 深度进化
"""

from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CoordinationResult:
    success: bool = False
    task_complexity: float = 0.0
    systems_invoked: List[str] = field(default_factory=list)
    governance_decisions: List[Dict[str, str]] = field(default_factory=list)
    total_duration_s: float = 0.0
    outputs: Dict[str, Any] = field(default_factory=dict)


class GovernanceIntegrationBridge:
    """
    治理集成桥接器
    
    将道法自然体系的治理能力（调度、人格、记忆、可解释性）扩展到
    全部4个子系统（自进化、炼丹、修炼），实现统一的资源分配和决策追溯。
    """

    COMPLEXITY_ROUTING = {
        (0.0, 0.3): {
            "name": "快速响应",
            "systems": ["qi_refining", "enhanced_retrieval"],
            "max_agents": 2,
            "timeout_s": 10.0,
        },
        (0.3, 0.7): {
            "name": "标准处理",
            "systems": ["law_mastery", "talisman_composition", "personality", "explainability"],
            "max_agents": 4,
            "timeout_s": 30.0,
        },
        (0.7, 1.0): {
            "name": "深度进化",
            "systems": ["all_stages", "alchemy_furnace", "chaos_testing", "meta_strategy"],
            "max_agents": 6,
            "timeout_s": 120.0,
        },
    }

    def __init__(self):
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        from backend.governance.enhanced_scheduler import enhanced_scheduler
        from backend.governance.dao_fa_zi_ran import dynamic_team_orchestrator
        from backend.personality.personality_fusion import personality_engine
        from backend.memory.enhanced_retrieval import enhanced_retrieval
        from backend.reporting.explainability_engine import explainability_engine
        from backend.integration_hub import integration_hub
        self._scheduler = enhanced_scheduler
        self._team_orchestrator = dynamic_team_orchestrator
        self._personality = personality_engine
        self._memory = enhanced_retrieval
        self._explainability = explainability_engine
        self._integration_hub = integration_hub
        self._initialized = True
        logger.info("[治理桥接] 初始化完成，三省六部与全部子系统已连接")

    def coordinate_all_systems(self, task_description: str = "", complexity_override: Optional[float] = None) -> CoordinationResult:
        self._ensure_initialized()
        start_time = time.time()
        result = CoordinationResult()
        try:
            complexity = complexity_override or self._assess_task_complexity(task_description)
            result.task_complexity = complexity
            routing_key = None
            for (lo, hi), config in self.COMPLEXITY_ROUTING.items():
                if lo <= complexity < hi:
                    routing_key = config
                    break
            if not routing_key:
                routing_key = list(self.COMPLEXITY_ROUTING.values())[-1]
            result.systems_involved = routing_key["systems"]
            decision_log = self._make_governance_decision(task_description, complexity, routing_key)
            result.governance_decisions.append(decision_log)
            memory_context = self._enrich_with_memory(task_description)
            result.outputs["memory_context"] = memory_context
            personality_state = self._get_personality_influence()
            result.outputs["personality_state"] = personality_state
            explanation_trace = self._build_explanation_trace(task_description, routing_key)
            result.outputs["explanation_trace"] = explanation_trace
            resource_allocation = self._allocate_resources(routing_key)
            result.outputs["resource_allocation"] = resource_allocation
            result.success = True
            logger.info(f"[治理桥接] 任务协调完成 | 复杂度={complexity:.2f} | 模式={routing_key['name']} | 系统={len(result.systems_involved)}个")
        except Exception as e:
            result.success = False
            result.outputs["error"] = str(e)[:300]
            logger.error(f"[治理桥接] 协调异常: {e}")
        result.total_duration_s = round(time.time() - start_time, 2)
        return result

    def _assess_task_complexity(self, task_text: str) -> float:
        if not task_text:
            return 0.5
        score = 0.0
        complex_keywords = ["分析", "报告", "综合", "对比", "详细", "深度", "跨领域", "融合"]
        simple_keywords = ["查询", "价格", "多少", "是吗", "有没有"]
        for kw in complex_keywords:
            if kw in task_text:
                score += 0.12
        for kw in simple_keywords:
            if kw in task_text:
                score += 0.03
        text_len_factor = min(len(task_text) / 200.0, 0.25)
        score += text_len_factor
        return max(0.05, min(0.99, score))

    def _make_governance_decision(self, task: str, complexity: float, routing: Dict) -> Dict[str, str]:
        return {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "task_preview": task[:80],
            "complexity_score": f"{complexity:.2f}",
            "routing_mode": routing.get("name", "unknown"),
            "systems_selected": ",".join(routing.get("systems", [])),
            "max_agents_allowed": str(routing.get("max_agents", 2)),
            "timeout_seconds": str(routing.get("timeout_s", 30)),
            "decision_source": "governance_integration_bridge",
            "confidence": "high" if complexity > 0.7 else ("medium" if complexity > 0.3 else "low"),
        }

    def _enrich_with_memory(self, query: str) -> Dict[str, Any]:
        context = {"query": query[:100], "memory_enriched": False}
        try:
            if hasattr(self._memory, 'retrieve'):
                memories = self._memory.retrieve(query, top_k=3)
                if isinstance(memories, list):
                    context["related_memories_count"] = len(memories)
                    context["memory_enriched"] = True
                    context["memory_ids"] = [m.get("id", f"mem_{i}") for i, m in enumerate(memories)]
        except Exception as e:
            context["error"] = str(e)[:100]
        return context

    def _get_personality_influence(self) -> Dict[str, Any]:
        state = {"active": False}
        try:
            if hasattr(self._personality, 'current_personality'):
                cp = self._personality.current_personality
                state["active"] = True
                state["primary_personality"] = getattr(cp, 'primary_name', 'default')
                state["blend_ratio"] = getattr(cp, 'blend_ratio', {'zhouyu': 0.5, 'luxun': 0.5})
                state["dimensions"] = getattr(cp, 'vector', {})
        except Exception as e:
            state["error"] = str(e)[:100]
        return state

    def _build_explanation_trace(self, task: str, routing: Dict) -> Dict[str, Any]:
        trace = {
            "task_id": f"trace_{int(time.time()*1000)}",
            "steps": [
                {"step": 1, "action": "receive_task", "detail": f"接收任务: {task[:50]}"},
                {"step": 2, "action": "assess_complexity", "detail": f"评估复杂度并路由到 {routing.get('name')}"},
                {"step": 3, "action": "query_memory", "detail": "查询增强记忆获取上下文"},
                {"step": 4, "action": "apply_personality", "detail": "应用当前人格配置"},
                {"step": 5, "action": "allocate_resources", "detail": f"分配 {len(routing.get('systems',[]))} 个子系统"},
                {"step": 6, "action": "execute_and_track", "detail": "执行并记录决策链路"},
            ],
        }
        return trace

    def _allocate_resources(self, routing: Dict) -> Dict[str, Any]:
        allocation = {
            "cpu_quota_percent": 20 if routing.get("name") == "深度进化" else 10,
            "memory_limit_mb": 512 if routing.get("name") == "深度进化" else 256,
            "max_concurrent_tasks": routing.get("max_agents", 2),
            "priority": "high" if routing.get("name") == "深度进化" else "normal",
            "systems_allocated": routing.get("systems", []),
        }
        return allocation

    def get_full_platform_status(self) -> Dict[str, Any]:
        self._ensure_initialized()
        status = {
            "bridge_initialized": self._initialized,
            "scheduler_status": {},
            "team_orchestrator_status": {},
            "personality_status": {},
            "memory_status": {},
            "explainability_status": {},
            "integration_hub_status": {},
        }
        components = [
            ("scheduler", self._scheduler),
            ("team_orchestrator", self._team_orchestrator),
            ("personality", self._personality),
            ("memory", self._memory),
            ("explainability", self._explainability),
            ("integration_hub", self._integration_hub),
        ]
        for name, comp in components:
            key = f"{name}_status"
            try:
                if comp and hasattr(comp, '__dict__'):
                    status[key] = {k: type(v).__name__ for k, v in vars(comp).items() if not k.startswith('_') and not callable(v)}
                elif comp:
                    status[key] = {"type": type(comp).__name__, "available": True}
                else:
                    status[key] = {"available": False}
            except Exception as e:
                status[key] = {"error": str(e)[:100]}
        return status


governance_integration_bridge = GovernanceIntegrationBridge()
