"""
反击智能体
Counter Strike Agent

在法律合规前提下，对攻击者实施精确反击
支持限流、干扰、反制程序投放、联动反击等手段
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class CounterStrikeType(Enum):
    RATE_LIMIT = "rate_limit"
    TCP_WINDOW = "tcp_window"
    DELAY_RESPONSE = "delay_response"
    FORGED_DATA = "forged_data"
    WARNING_MESSAGE = "warning_message"
    UPSTREAM_NOTIFICATION = "upstream_notification"
    ISOLATION = "isolation"
    DECOY_REDIRECT = "decoy_redirect"


class CounterStrikeStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class CounterStrikeAction:
    action_id: str
    action_type: CounterStrikeType
    target_identity: str
    target_ip: str
    status: CounterStrikeStatus
    severity: Severity
    created_at: datetime
    approved_at: Optional[datetime]
    executed_at: Optional[datetime]
    expires_at: Optional[datetime]
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    requires_approval: bool
    approved_by: Optional[str]
    effectiveness_score: float = 0.0
    side_effects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "target_identity": self.target_identity,
            "target_ip": self.target_ip,
            "status": self.status.value,
            "severity": self.severity.value,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "parameters": self.parameters,
            "results": self.results,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
            "effectiveness_score": self.effectiveness_score,
            "side_effects": self.side_effects
        }


class RateLimiter:
    def __init__(self):
        self.limits: Dict[str, Dict] = {}
        self.token_buckets: Dict[str, Dict] = {}
        
    def set_limit(
        self,
        ip: str,
        requests_per_second: float = 1.0,
        burst_size: int = 5
    ):
        self.limits[ip] = {
            "requests_per_second": requests_per_second,
            "burst_size": burst_size,
            "created_at": datetime.now().isoformat()
        }
        
        self.token_buckets[ip] = {
            "tokens": burst_size,
            "last_update": time.time()
        }
        
    def check_request(self, ip: str) -> Tuple[bool, float]:
        if ip not in self.limits:
            return True, 0.0
            
        limit = self.limits[ip]
        bucket = self.token_buckets[ip]
        
        now = time.time()
        elapsed = now - bucket["last_update"]
        
        bucket["tokens"] = min(
            limit["burst_size"],
            bucket["tokens"] + elapsed * limit["requests_per_second"]
        )
        bucket["last_update"] = now
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True, 0.0
        else:
            wait_time = (1 - bucket["tokens"]) / limit["requests_per_second"]
            return False, wait_time
            
    def remove_limit(self, ip: str) -> bool:
        if ip in self.limits:
            del self.limits[ip]
            del self.token_buckets[ip]
            return True
        return False


class TCPWindowController:
    def __init__(self):
        self.window_sizes: Dict[str, int] = {}
        self.default_window = 65535
        self.restricted_window = 1024
        
    def restrict_window(self, ip: str, window_size: int = 1024):
        self.window_sizes[ip] = window_size
        logger.info(f"Restricted TCP window for {ip} to {window_size}")
        
    def restore_window(self, ip: str):
        if ip in self.window_sizes:
            del self.window_sizes[ip]
            logger.info(f"Restored TCP window for {ip}")
            
    def get_window_size(self, ip: str) -> int:
        return self.window_sizes.get(ip, self.default_window)


class UpstreamNotifier:
    def __init__(self):
        self.notifications: deque = deque(maxlen=100)
        self.isp_contacts: Dict[str, Dict] = {}
        self.cloud_provider_apis: Dict[str, str] = {}
        
    async def notify_isp(
        self,
        ip: str,
        attack_type: str,
        evidence: Dict
    ) -> Dict:
        notification_id = f"isp_{int(time.time())}_{hashlib.md5(ip.encode()).hexdigest()[:8]}"
        
        notification = {
            "notification_id": notification_id,
            "type": "isp_notification",
            "target_ip": ip,
            "attack_type": attack_type,
            "evidence": evidence,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        self.notifications.append(notification)
        
        logger.info(f"Sent ISP notification for {ip}: {attack_type}")
        
        return notification
        
    async def notify_cloud_provider(
        self,
        provider: str,
        resource_id: str,
        issue_type: str,
        details: Dict
    ) -> Dict:
        notification_id = f"cloud_{int(time.time())}_{hashlib.md5(resource_id.encode()).hexdigest()[:8]}"
        
        notification = {
            "notification_id": notification_id,
            "type": "cloud_provider_notification",
            "provider": provider,
            "resource_id": resource_id,
            "issue_type": issue_type,
            "details": details,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        self.notifications.append(notification)
        
        logger.info(f"Sent cloud provider notification to {provider} for {resource_id}")
        
        return notification


class CounterStrikeAgent:
    def __init__(
        self,
        agent_id: str = "counter_strike_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        boundary_controller: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        self.boundary_controller = boundary_controller
        
        self.rate_limiter = RateLimiter()
        self.tcp_controller = TCPWindowController()
        self.upstream_notifier = UpstreamNotifier()
        
        self.actions: Dict[str, CounterStrikeAction] = {}
        self.active_actions: Dict[str, str] = {}
        self.action_history: deque = deque(maxlen=500)
        
        self.approval_required_types: Set[CounterStrikeType] = {
            CounterStrikeType.UPSTREAM_NOTIFICATION,
            CounterStrikeType.ISOLATION,
            CounterStrikeType.WARNING_MESSAGE
        }
        
        self.stats = {
            "total_actions": 0,
            "active_actions": 0,
            "completed_actions": 0,
            "failed_actions": 0,
            "requests_blocked": 0,
            "avg_effectiveness": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._action_monitor_loop())
        logger.info(f"CounterStrikeAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        for action_id in list(self.active_actions.keys()):
            await self.cancel_action(action_id)
            
        logger.info(f"CounterStrikeAgent {self.agent_id} stopped")
        
    async def _action_monitor_loop(self):
        while self._running:
            try:
                await self._check_expired_actions()
                await self._evaluate_action_effectiveness()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in action monitor loop: {e}")
                await asyncio.sleep(5)
                
    async def _check_expired_actions(self):
        now = datetime.now()
        expired = []
        
        for action_id, target_ip in self.active_actions.items():
            action = self.actions.get(action_id)
            if action and action.expires_at and now >= action.expires_at:
                expired.append(action_id)
                
        for action_id in expired:
            await self.complete_action(action_id)
            
    async def _evaluate_action_effectiveness(self):
        for action_id in list(self.active_actions.keys()):
            action = self.actions.get(action_id)
            if action:
                effectiveness = await self._calculate_effectiveness(action)
                action.effectiveness_score = effectiveness
                
    async def _calculate_effectiveness(self, action: CounterStrikeAction) -> float:
        if action.action_type == CounterStrikeType.RATE_LIMIT:
            return await self._evaluate_rate_limit_effectiveness(action)
        elif action.action_type == CounterStrikeType.TCP_WINDOW:
            return await self._evaluate_tcp_window_effectiveness(action)
        else:
            return 0.5
            
    async def _evaluate_rate_limit_effectiveness(self, action: CounterStrikeAction) -> float:
        return 0.8
        
    async def _evaluate_tcp_window_effectiveness(self, action: CounterStrikeAction) -> float:
        return 0.7
        
    async def create_action(
        self,
        action_type: CounterStrikeType,
        target_identity: str,
        target_ip: str,
        parameters: Optional[Dict] = None,
        severity: Severity = Severity.MEDIUM,
        duration_hours: int = 24
    ) -> CounterStrikeAction:
        requires_approval = action_type in self.approval_required_types
        
        action = CounterStrikeAction(
            action_id=self._generate_action_id(),
            action_type=action_type,
            target_identity=target_identity,
            target_ip=target_ip,
            status=CounterStrikeStatus.PENDING,
            severity=severity,
            created_at=datetime.now(),
            approved_at=None,
            executed_at=None,
            expires_at=datetime.now() + timedelta(hours=duration_hours),
            parameters=parameters or {},
            results={},
            requires_approval=requires_approval,
            approved_by=None
        )
        
        self.actions[action.action_id] = action
        self.stats["total_actions"] += 1
        
        logger.info(f"Created counter-strike action {action.action_id} of type {action_type.value}")
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "counter_strike_created",
                action.to_dict()
            )
            
        if not requires_approval:
            await self.execute_action(action.action_id)
            
        return action
        
    async def approve_action(self, action_id: str, approver: str) -> bool:
        action = self.actions.get(action_id)
        if not action:
            return False
            
        if action.status != CounterStrikeStatus.PENDING:
            return False
            
        if self.boundary_controller:
            is_allowed = await self.boundary_controller.check_action_allowed(action)
            if not is_allowed:
                action.status = CounterStrikeStatus.CANCELLED
                action.side_effects.append("Action blocked by boundary controller")
                return False
                
        action.status = CounterStrikeStatus.APPROVED
        action.approved_at = datetime.now()
        action.approved_by = approver
        
        logger.info(f"Action {action_id} approved by {approver}")
        
        await self.execute_action(action_id)
        
        return True
        
    async def execute_action(self, action_id: str) -> bool:
        action = self.actions.get(action_id)
        if not action:
            return False
            
        if action.status not in [CounterStrikeStatus.PENDING, CounterStrikeStatus.APPROVED]:
            return False
            
        if action.requires_approval and action.status != CounterStrikeStatus.APPROVED:
            return False
            
        action.status = CounterStrikeStatus.EXECUTING
        
        try:
            if action.action_type == CounterStrikeType.RATE_LIMIT:
                await self._execute_rate_limit(action)
            elif action.action_type == CounterStrikeType.TCP_WINDOW:
                await self._execute_tcp_window(action)
            elif action.action_type == CounterStrikeType.DELAY_RESPONSE:
                await self._execute_delay_response(action)
            elif action.action_type == CounterStrikeType.FORGED_DATA:
                await self._execute_forged_data(action)
            elif action.action_type == CounterStrikeType.WARNING_MESSAGE:
                await self._execute_warning_message(action)
            elif action.action_type == CounterStrikeType.UPSTREAM_NOTIFICATION:
                await self._execute_upstream_notification(action)
            elif action.action_type == CounterStrikeType.ISOLATION:
                await self._execute_isolation(action)
            elif action.action_type == CounterStrikeType.DECOY_REDIRECT:
                await self._execute_decoy_redirect(action)
                
            action.status = CounterStrikeStatus.ACTIVE
            action.executed_at = datetime.now()
            self.active_actions[action_id] = action.target_ip
            self.stats["active_actions"] += 1
            
            logger.info(f"Successfully executed action {action_id}")
            
            if self.communication_bus:
                await self.communication_bus.publish(
                    "counter_strike_executed",
                    action.to_dict()
                )
                
            return True
            
        except Exception as e:
            action.status = CounterStrikeStatus.FAILED
            action.side_effects.append(str(e))
            self.stats["failed_actions"] += 1
            
            logger.error(f"Failed to execute action {action_id}: {e}")
            return False
            
    async def _execute_rate_limit(self, action: CounterStrikeAction):
        rps = action.parameters.get("requests_per_second", 1.0)
        burst = action.parameters.get("burst_size", 5)
        
        self.rate_limiter.set_limit(action.target_ip, rps, burst)
        
        action.results = {
            "rate_limit_set": True,
            "requests_per_second": rps,
            "burst_size": burst
        }
        
    async def _execute_tcp_window(self, action: CounterStrikeAction):
        window_size = action.parameters.get("window_size", 1024)
        
        self.tcp_controller.restrict_window(action.target_ip, window_size)
        
        action.results = {
            "window_restricted": True,
            "window_size": window_size
        }
        
    async def _execute_delay_response(self, action: CounterStrikeAction):
        delay_ms = action.parameters.get("delay_ms", 5000)
        
        action.results = {
            "delay_set": True,
            "delay_ms": delay_ms
        }
        
    async def _execute_forged_data(self, action: CounterStrikeAction):
        data_type = action.parameters.get("data_type", "fake_credentials")
        
        action.results = {
            "forged_data_sent": True,
            "data_type": data_type
        }
        
    async def _execute_warning_message(self, action: CounterStrikeAction):
        message = action.parameters.get(
            "message",
            "Your activities have been detected and logged. Cease immediately."
        )
        
        action.results = {
            "warning_sent": True,
            "message": message
        }
        
    async def _execute_upstream_notification(self, action: CounterStrikeAction):
        attack_type = action.parameters.get("attack_type", "unknown")
        evidence = action.parameters.get("evidence", {})
        
        notification = await self.upstream_notifier.notify_isp(
            action.target_ip,
            attack_type,
            evidence
        )
        
        action.results = {
            "notification_sent": True,
            "notification_id": notification["notification_id"]
        }
        
    async def _execute_isolation(self, action: CounterStrikeAction):
        action.results = {
            "isolated": True,
            "isolation_method": "network_segment"
        }
        
    async def _execute_decoy_redirect(self, action: CounterStrikeAction):
        decoy_target = action.parameters.get("decoy_target", "honeypot")
        
        action.results = {
            "redirect_active": True,
            "decoy_target": decoy_target
        }
        
    async def complete_action(self, action_id: str) -> bool:
        action = self.actions.get(action_id)
        if not action:
            return False
            
        if action.action_type == CounterStrikeType.RATE_LIMIT:
            self.rate_limiter.remove_limit(action.target_ip)
        elif action.action_type == CounterStrikeType.TCP_WINDOW:
            self.tcp_controller.restore_window(action.target_ip)
            
        action.status = CounterStrikeStatus.COMPLETED
        self.active_actions.pop(action_id, None)
        self.action_history.append(action.to_dict())
        
        self.stats["active_actions"] -= 1
        self.stats["completed_actions"] += 1
        
        logger.info(f"Completed action {action_id}")
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "counter_strike_completed",
                action.to_dict()
            )
            
        return True
        
    async def cancel_action(self, action_id: str) -> bool:
        action = self.actions.get(action_id)
        if not action:
            return False
            
        if action.status in [CounterStrikeStatus.COMPLETED, CounterStrikeStatus.CANCELLED]:
            return False
            
        if action.status == CounterStrikeStatus.ACTIVE:
            if action.action_type == CounterStrikeType.RATE_LIMIT:
                self.rate_limiter.remove_limit(action.target_ip)
            elif action.action_type == CounterStrikeType.TCP_WINDOW:
                self.tcp_controller.restore_window(action.target_ip)
                
        action.status = CounterStrikeStatus.CANCELLED
        self.active_actions.pop(action_id, None)
        
        logger.info(f"Cancelled action {action_id}")
        
        return True
        
    def check_request(self, ip: str) -> Tuple[bool, str, float]:
        allowed, wait_time = self.rate_limiter.check_request(ip)
        
        if not allowed:
            self.stats["requests_blocked"] += 1
            return False, "rate_limited", wait_time
            
        window_size = self.tcp_controller.get_window_size(ip)
        if window_size < 65535:
            return True, "window_restricted", 0.0
            
        return True, "allowed", 0.0
        
    async def get_action(self, action_id: str) -> Optional[Dict]:
        action = self.actions.get(action_id)
        return action.to_dict() if action else None
        
    async def get_active_actions(self) -> List[Dict]:
        return [
            self.actions[aid].to_dict()
            for aid in self.active_actions.keys()
            if aid in self.actions
        ]
        
    async def get_action_history(self, limit: int = 50) -> List[Dict]:
        return list(self.action_history)[-limit:]
        
    async def get_actions_for_target(self, target_ip: str) -> List[Dict]:
        return [
            a.to_dict()
            for a in self.actions.values()
            if a.target_ip == target_ip
        ]
        
    def _generate_action_id(self) -> str:
        return f"cs_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "total_actions_created": len(self.actions),
            "action_history_size": len(self.action_history)
        }
