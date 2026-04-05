"""
人工控制台
Human Control Console

提供人工干预接口，实时展示攻击态势、反击进展
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import deque
import structlog

logger = structlog.get_logger()


class OperationMode(Enum):
    DEFENSE = "defense"
    COUNTER_STRIKE = "counter_strike"
    DECEPTION = "deception"
    STAND_DOWN = "stand_down"
    MANUAL = "manual"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class HumanControlConsole:
    console_id: str
    communication_bus: Optional[Any] = None
    
    def __init__(
        self,
        console_id: str = "human_console_001",
        communication_bus: Optional[Any] = None
    ):
        self.console_id = console_id
        self.communication_bus = communication_bus
        
        self.operation_mode = OperationMode.DEFENSE
        self.auto_mode = True
        
        self.pending_approvals: Dict[str, Dict] = {}
        self.approval_history: deque = deque(maxlen=200)
        
        self.alerts: deque = deque(maxlen=100)
        self.notifications: deque = deque(maxlen=100)
        
        self.operation_log: deque = deque(maxlen=1000)
        self.manual_overrides: deque = deque(maxlen=100)
        
        self.dashboard_data: Dict = {}
        
        self.stats = {
            "total_approvals": 0,
            "approved_actions": 0,
            "rejected_actions": 0,
            "manual_overrides": 0,
            "alerts_sent": 0
        }
        
        self._running = False
        
    async def start(self):
        self._running = True
        logger.info(f"HumanControlConsole {self.console_id} started")
        
    async def stop(self):
        self._running = False
        logger.info(f"HumanControlConsole {self.console_id} stopped")
        
    async def request_approval(
        self,
        action_id: str,
        action_type: str,
        target: str,
        reason: str,
        urgency: str = "normal",
        timeout_seconds: int = 300
    ) -> str:
        request_id = self._generate_request_id()
        
        request = {
            "request_id": request_id,
            "action_id": action_id,
            "action_type": action_type,
            "target": target,
            "reason": reason,
            "urgency": urgency,
            "timeout_seconds": timeout_seconds,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + __import__('datetime').timedelta(seconds=timeout_seconds)).isoformat(),
            "status": "pending"
        }
        
        self.pending_approvals[request_id] = request
        
        await self._send_alert(
            level=AlertLevel.WARNING if urgency == "high" else AlertLevel.INFO,
            title=f"Approval Required: {action_type}",
            message=f"Action against {target}: {reason}",
            data=request
        )
        
        return request_id
        
    async def approve_action(
        self,
        request_id: str,
        approver: str,
        notes: Optional[str] = None
    ) -> bool:
        request = self.pending_approvals.get(request_id)
        if not request:
            return False
            
        request["status"] = "approved"
        request["approved_at"] = datetime.now().isoformat()
        request["approved_by"] = approver
        request["notes"] = notes
        
        self.approval_history.append(request)
        del self.pending_approvals[request_id]
        
        self.stats["total_approvals"] += 1
        self.stats["approved_actions"] += 1
        
        self._log_operation("approval", request)
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "action_approved",
                request
            )
            
        logger.info(f"Action approved: {request_id} by {approver}")
        
        return True
        
    async def reject_action(
        self,
        request_id: str,
        rejecter: str,
        reason: str
    ) -> bool:
        request = self.pending_approvals.get(request_id)
        if not request:
            return False
            
        request["status"] = "rejected"
        request["rejected_at"] = datetime.now().isoformat()
        request["rejected_by"] = rejecter
        request["rejection_reason"] = reason
        
        self.approval_history.append(request)
        del self.pending_approvals[request_id]
        
        self.stats["total_approvals"] += 1
        self.stats["rejected_actions"] += 1
        
        self._log_operation("rejection", request)
        
        logger.info(f"Action rejected: {request_id} by {rejecter}")
        
        return True
        
    async def set_operation_mode(self, mode: OperationMode, operator: str) -> bool:
        old_mode = self.operation_mode
        self.operation_mode = mode
        
        override_record = {
            "type": "mode_change",
            "old_mode": old_mode.value,
            "new_mode": mode.value,
            "operator": operator,
            "timestamp": datetime.now().isoformat()
        }
        
        self.manual_overrides.append(override_record)
        self.stats["manual_overrides"] += 1
        
        self._log_operation("mode_change", override_record)
        
        await self._send_notification(
            title="Operation Mode Changed",
            message=f"Mode changed from {old_mode.value} to {mode.value} by {operator}"
        )
        
        logger.info(f"Operation mode changed: {old_mode.value} -> {mode.value}")
        
        return True
        
    def set_auto_mode(self, enabled: bool, operator: str):
        self.auto_mode = enabled
        
        self._log_operation("auto_mode_change", {
            "enabled": enabled,
            "operator": operator,
            "timestamp": datetime.now().isoformat()
        })
        
    async def update_dashboard(self, data: Dict):
        self.dashboard_data = {
            **data,
            "updated_at": datetime.now().isoformat()
        }
        
    async def get_dashboard(self) -> Dict:
        return {
            **self.dashboard_data,
            "operation_mode": self.operation_mode.value,
            "auto_mode": self.auto_mode,
            "pending_approvals_count": len(self.pending_approvals),
            "recent_alerts": list(self.alerts)[-5:]
        }
        
    async def get_pending_approvals(self) -> List[Dict]:
        now = datetime.now()
        valid_approvals = []
        
        for request_id, request in list(self.pending_approvals.items()):
            expires = datetime.fromisoformat(request["expires_at"])
            if now < expires:
                valid_approvals.append(request)
            else:
                request["status"] = "expired"
                self.approval_history.append(request)
                del self.pending_approvals[request_id]
                
        return valid_approvals
        
    async def get_approval_history(self, limit: int = 50) -> List[Dict]:
        return list(self.approval_history)[-limit:]
        
    async def get_alerts(self, limit: int = 20) -> List[Dict]:
        return list(self.alerts)[-limit:]
        
    async def get_operation_log(self, limit: int = 100) -> List[Dict]:
        return list(self.operation_log)[-limit:]
        
    async def _send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ):
        alert = {
            "alert_id": self._generate_alert_id(),
            "level": level.value,
            "title": title,
            "message": message,
            "data": data or {},
            "created_at": datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        self.stats["alerts_sent"] += 1
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "console_alert",
                alert
            )
            
    async def _send_notification(self, title: str, message: str):
        notification = {
            "notification_id": self._generate_notification_id(),
            "title": title,
            "message": message,
            "created_at": datetime.now().isoformat()
        }
        
        self.notifications.append(notification)
        
    def _log_operation(self, operation_type: str, data: Dict):
        self.operation_log.append({
            "operation_type": operation_type,
            "data": data,
            "logged_at": datetime.now().isoformat()
        })
        
    def _generate_request_id(self) -> str:
        return f"req_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def _generate_alert_id(self) -> str:
        return f"alert_{int(time.time() * 1000)}"
        
    def _generate_notification_id(self) -> str:
        return f"notif_{int(time.time() * 1000)}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "pending_approvals": len(self.pending_approvals),
            "recent_alerts": len(self.alerts)
        }
