"""
业务层人工控制台
Business Control Console

提供人工干预接口，实时展示攻击态势、反击进展
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    DEFENSE = "defense"
    COUNTER_STRIKE = "counter_strike"
    DECEPTION = "deception"
    STAND_DOWN = "stand_down"
    MANUAL = "manual"


class InterventionType(Enum):
    ENERGY_ADJUST = "energy_adjust"
    FORCE_REPRODUCE = "force_reproduce"
    FORCE_TERMINATE = "force_terminate"
    MODE_SWITCH = "mode_switch"
    ROLLBACK = "rollback"
    APPROVAL = "approval"
    REJECTION = "rejection"


@dataclass
class InterventionRecord:
    intervention_id: str
    operator_id: str
    intervention_type: InterventionType
    target_agent_id: Optional[str]
    parameters: Dict
    reason: str
    created_at: float
    executed: bool = False
    result: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "intervention_id": self.intervention_id,
            "operator_id": self.operator_id,
            "intervention_type": self.intervention_type.value,
            "target_agent_id": self.target_agent_id,
            "parameters": self.parameters,
            "reason": self.reason,
            "created_at": self.created_at,
            "executed": self.executed,
            "result": self.result
        }


class BusinessControlConsole:
    """
    业务层人工控制台
    
    供管理员干预智能体进化：
    1. 监控仪表盘：实时显示各业务智能体状态
    2. 干预操作：能量调整、强制繁殖/淘汰、模式切换
    3. 版本管理：记录版本历史，支持回滚
    4. 审计日志：所有操作记录，不可篡改
    """
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        task_market: Optional[Any] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        self.task_market = task_market
        
        self.operation_mode = OperationMode.DEFENSE
        self.mode_history: List[Dict] = []
        
        self.interventions: Dict[str, InterventionRecord] = {}
        self.intervention_log: deque = deque(maxlen=10000)
        
        self.agent_versions: Dict[str, List[Dict]] = defaultdict(list)
        self.agent_snapshots: Dict[str, Dict] = {}
        
        self.approval_queue: asyncio.Queue = asyncio.Queue()
        self.pending_approvals: Dict[str, Dict] = {}
        
        self.alerts: deque = deque(maxlen=100)
        
        self._lock = threading.RLock()
        self._running = False
        self._approval_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "total_interventions": 0,
            "energy_adjustments": 0,
            "forced_reproductions": 0,
            "forced_terminations": 0,
            "mode_switches": 0,
            "rollbacks": 0,
            "approvals_granted": 0,
            "approvals_rejected": 0,
        }
    
    async def start(self):
        self._running = True
        self._approval_task = asyncio.create_task(self._approval_loop())
        logger.info("Business control console started")
    
    async def stop(self):
        self._running = False
        if self._approval_task:
            self._approval_task.cancel()
            try:
                await self._approval_task
            except asyncio.CancelledError:
                pass
        logger.info("Business control console stopped")
    
    async def _approval_loop(self):
        while self._running:
            try:
                approval = await asyncio.wait_for(
                    self.approval_queue.get(),
                    timeout=5.0
                )
                await self._process_pending_approval(approval)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in approval loop: {e}")
    
    async def _process_pending_approval(self, approval: Dict):
        approval_id = approval.get("approval_id")
        self.pending_approvals[approval_id] = approval
    
    def set_operation_mode(
        self,
        mode: OperationMode,
        operator_id: str,
        reason: str = "",
    ) -> Dict:
        old_mode = self.operation_mode
        self.operation_mode = mode
        
        mode_record = {
            "mode": mode.value,
            "previous_mode": old_mode.value,
            "operator_id": operator_id,
            "reason": reason,
            "timestamp": time.time(),
        }
        
        with self._lock:
            self.mode_history.append(mode_record)
            self.stats["mode_switches"] += 1
        
        logger.info(f"Operation mode changed: {old_mode.value} -> {mode.value} by {operator_id}")
        
        return mode_record
    
    async def adjust_energy(
        self,
        agent_id: str,
        amount: float,
        operator_id: str,
        reason: str = "",
    ) -> InterventionRecord:
        intervention = await self._create_intervention(
            operator_id=operator_id,
            intervention_type=InterventionType.ENERGY_ADJUST,
            target_agent_id=agent_id,
            parameters={"amount": amount},
            reason=reason
        )
        
        if self.communication_bus:
            await self.communication_bus.send(
                to=agent_id,
                message={
                    "type": "energy_adjustment",
                    "amount": amount,
                    "intervention_id": intervention.intervention_id
                }
            )
        
        intervention.executed = True
        intervention.result = {"new_energy": amount}
        
        with self._lock:
            self.stats["energy_adjustments"] += 1
        
        return intervention
    
    async def force_reproduce(
        self,
        agent_id: str,
        operator_id: str,
        reason: str = "",
    ) -> InterventionRecord:
        intervention = await self._create_intervention(
            operator_id=operator_id,
            intervention_type=InterventionType.FORCE_REPRODUCE,
            target_agent_id=agent_id,
            parameters={},
            reason=reason
        )
        
        if self.communication_bus:
            await self.communication_bus.send(
                to=agent_id,
                message={
                    "type": "force_reproduce",
                    "intervention_id": intervention.intervention_id
                }
            )
        
        intervention.executed = True
        
        with self._lock:
            self.stats["forced_reproductions"] += 1
        
        return intervention
    
    async def force_terminate(
        self,
        agent_id: str,
        operator_id: str,
        reason: str = "",
    ) -> InterventionRecord:
        intervention = await self._create_intervention(
            operator_id=operator_id,
            intervention_type=InterventionType.FORCE_TERMINATE,
            target_agent_id=agent_id,
            parameters={},
            reason=reason
        )
        
        if self.communication_bus:
            await self.communication_bus.send(
                to=agent_id,
                message={
                    "type": "terminate",
                    "intervention_id": intervention.intervention_id
                }
            )
        
        intervention.executed = True
        
        with self._lock:
            self.stats["forced_terminations"] += 1
        
        return intervention
    
    async def rollback_agent(
        self,
        agent_id: str,
        version: int,
        operator_id: str,
        reason: str = "",
    ) -> InterventionRecord:
        intervention = await self._create_intervention(
            operator_id=operator_id,
            intervention_type=InterventionType.ROLLBACK,
            target_agent_id=agent_id,
            parameters={"version": version},
            reason=reason
        )
        
        versions = self.agent_versions.get(agent_id, [])
        target_version = None
        for v in versions:
            if v.get("version") == version:
                target_version = v
                break
        
        if target_version:
            intervention.executed = True
            intervention.result = {"rolled_back_to": version}
            
            with self._lock:
                self.stats["rollbacks"] += 1
        else:
            intervention.result = {"error": f"Version {version} not found"}
        
        return intervention
    
    async def _create_intervention(
        self,
        operator_id: str,
        intervention_type: InterventionType,
        target_agent_id: Optional[str],
        parameters: Dict,
        reason: str,
    ) -> InterventionRecord:
        intervention_id = f"int_{uuid.uuid4().hex[:8]}"
        
        intervention = InterventionRecord(
            intervention_id=intervention_id,
            operator_id=operator_id,
            intervention_type=intervention_type,
            target_agent_id=target_agent_id,
            parameters=parameters,
            reason=reason,
            created_at=time.time(),
        )
        
        with self._lock:
            self.interventions[intervention_id] = intervention
            self.intervention_log.append(intervention.to_dict())
            self.stats["total_interventions"] += 1
        
        if self.memory_agent:
            await self._store_intervention(intervention)
        
        return intervention
    
    async def _store_intervention(self, intervention: InterventionRecord):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "intervention_log",
                    "intervention": intervention.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store intervention: {e}")
    
    def save_agent_version(
        self,
        agent_id: str,
        state: Dict,
        version: Optional[int] = None,
    ):
        if version is None:
            versions = self.agent_versions.get(agent_id, [])
            version = max([v.get("version", 0) for v in versions], default=0) + 1
        
        version_record = {
            "version": version,
            "state": state,
            "timestamp": time.time(),
        }
        
        with self._lock:
            self.agent_versions[agent_id].append(version_record)
    
    def create_agent_snapshot(
        self,
        agent_id: str,
        state: Dict,
    ) -> str:
        snapshot_id = f"snap_{uuid.uuid4().hex[:8]}"
        
        snapshot = {
            "snapshot_id": snapshot_id,
            "agent_id": agent_id,
            "state": state,
            "timestamp": time.time(),
        }
        
        with self._lock:
            self.agent_snapshots[snapshot_id] = snapshot
        
        return snapshot_id
    
    def get_agent_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        return self.agent_snapshots.get(snapshot_id)
    
    async def request_approval(
        self,
        request_type: str,
        agent_id: str,
        details: Dict,
    ) -> str:
        approval_id = f"appr_{uuid.uuid4().hex[:8]}"
        
        approval = {
            "approval_id": approval_id,
            "request_type": request_type,
            "agent_id": agent_id,
            "details": details,
            "status": "pending",
            "created_at": time.time(),
        }
        
        await self.approval_queue.put(approval)
        
        return approval_id
    
    async def grant_approval(
        self,
        approval_id: str,
        operator_id: str,
        notes: str = "",
    ) -> bool:
        if approval_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[approval_id]
        approval["status"] = "approved"
        approval["approved_by"] = operator_id
        approval["approved_at"] = time.time()
        approval["notes"] = notes
        
        with self._lock:
            self.stats["approvals_granted"] += 1
        
        return True
    
    async def reject_approval(
        self,
        approval_id: str,
        operator_id: str,
        reason: str = "",
    ) -> bool:
        if approval_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[approval_id]
        approval["status"] = "rejected"
        approval["rejected_by"] = operator_id
        approval["rejected_at"] = time.time()
        approval["reason"] = reason
        
        with self._lock:
            self.stats["approvals_rejected"] += 1
        
        return True
    
    def add_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        agent_id: Optional[str] = None,
    ):
        alert = {
            "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "agent_id": agent_id,
            "timestamp": time.time(),
            "acknowledged": False,
        }
        
        with self._lock:
            self.alerts.append(alert)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.get("alert_id") == alert_id:
                alert["acknowledged"] = True
                return True
        return False
    
    def get_dashboard_data(self) -> Dict:
        with self._lock:
            return {
                "operation_mode": self.operation_mode.value,
                "mode_history": self.mode_history[-10:],
                "recent_interventions": list(self.intervention_log)[-20:],
                "pending_approvals": len(self.pending_approvals),
                "recent_alerts": [
                    a for a in self.alerts
                    if not a.get("acknowledged")
                ][-10:],
                "stats": self.stats.copy(),
            }
    
    def get_intervention(self, intervention_id: str) -> Optional[InterventionRecord]:
        return self.interventions.get(intervention_id)
    
    def get_agent_versions(self, agent_id: str) -> List[Dict]:
        return self.agent_versions.get(agent_id, [])
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "operation_mode": self.operation_mode.value,
                "total_interventions": len(self.interventions),
                "pending_approvals": len(self.pending_approvals),
                "alert_count": len(self.alerts),
            }
