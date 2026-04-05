"""
跨部门协作协议
Cross-Department Collaboration Protocol

定义标准化的跨部门协作协议，供业务智能体通信
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


class CollaborationMessageType(Enum):
    REQUEST_HELP = "request_help"
    OFFER_RESULT = "offer_result"
    TASK_SPLIT = "task_split"
    PROGRESS_UPDATE = "progress_update"
    MERGE_REQUEST = "merge_request"
    ACCEPT = "accept"
    REJECT = "reject"
    COUNTER_OFFER = "counter_offer"
    ACKNOWLEDGE = "acknowledge"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    TEAM_FORM = "team_form"
    TEAM_DISSOLVE = "team_dissolve"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RELEASE = "resource_release"


@dataclass
class CollaborationMessage:
    message_id: str
    from_agent: str
    to_agent: str
    message_type: CollaborationMessageType
    payload: Dict
    energy_offer: float = 0.0
    deadline: Optional[float] = None
    task_id: Optional[str] = None
    team_id: Optional[str] = None
    priority: int = 1
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "energy_offer": self.energy_offer,
            "deadline": self.deadline,
            "task_id": self.task_id,
            "team_id": self.team_id,
            "priority": self.priority,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata
        }
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class CollaborationResponse:
    response_id: str
    original_message_id: str
    from_agent: str
    to_agent: str
    response_type: str
    accepted: bool
    payload: Dict
    energy_transfer: float = 0.0
    created_at: float = field(default_factory=time.time)
    message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "response_id": self.response_id,
            "original_message_id": self.original_message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "response_type": self.response_type,
            "accepted": self.accepted,
            "payload": self.payload,
            "energy_transfer": self.energy_transfer,
            "created_at": self.created_at,
            "message": self.message
        }


@dataclass
class CollaborationRecord:
    record_id: str
    task_id: str
    requester_id: str
    helper_id: str
    message_type: CollaborationMessageType
    energy_offered: float
    energy_transferred: float
    success: bool
    started_at: float
    completed_at: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "record_id": self.record_id,
            "task_id": self.task_id,
            "requester_id": self.requester_id,
            "helper_id": self.helper_id,
            "message_type": self.message_type.value,
            "energy_offered": self.energy_offered,
            "energy_transferred": self.energy_transferred,
            "success": self.success,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }


class ReputationSystem:
    """
    协作信誉系统
    
    维护每个智能体的协作信誉分
    """
    
    def __init__(
        self,
        initial_reputation: float = 50.0,
        max_reputation: float = 100.0,
        min_reputation: float = 0.0,
        success_bonus: float = 2.0,
        failure_penalty: float = 5.0,
        timeout_penalty: float = 10.0,
    ):
        self.initial_reputation = initial_reputation
        self.max_reputation = max_reputation
        self.min_reputation = min_reputation
        self.success_bonus = success_bonus
        self.failure_penalty = failure_penalty
        self.timeout_penalty = timeout_penalty
        
        self.reputations: Dict[str, float] = {}
        self.collaboration_history: Dict[str, List[Dict]] = defaultdict(list)
        
        self._lock = threading.RLock()
    
    def get_reputation(self, agent_id: str) -> float:
        with self._lock:
            if agent_id not in self.reputations:
                self.reputations[agent_id] = self.initial_reputation
            return self.reputations[agent_id]
    
    def update_reputation(
        self,
        agent_id: str,
        success: bool,
        is_timeout: bool = False,
    ) -> float:
        with self._lock:
            if agent_id not in self.reputations:
                self.reputations[agent_id] = self.initial_reputation
            
            current = self.reputations[agent_id]
            
            if success:
                delta = self.success_bonus
            elif is_timeout:
                delta = -self.timeout_penalty
            else:
                delta = -self.failure_penalty
            
            new_reputation = max(
                self.min_reputation,
                min(self.max_reputation, current + delta)
            )
            
            self.reputations[agent_id] = new_reputation
            
            self.collaboration_history[agent_id].append({
                "timestamp": time.time(),
                "success": success,
                "is_timeout": is_timeout,
                "reputation_change": delta,
                "new_reputation": new_reputation
            })
            
            return new_reputation
    
    def record_collaboration(
        self,
        agent_id: str,
        partner_id: str,
        task_id: str,
        success: bool,
    ):
        with self._lock:
            self.collaboration_history[agent_id].append({
                "timestamp": time.time(),
                "partner_id": partner_id,
                "task_id": task_id,
                "success": success
            })
    
    def get_collaboration_score(
        self,
        agent_id: str,
        partner_id: str,
    ) -> float:
        with self._lock:
            history = self.collaboration_history.get(agent_id, [])
            partner_collabs = [
                h for h in history
                if h.get("partner_id") == partner_id
            ]
            
            if not partner_collabs:
                return 0.5
            
            success_count = sum(1 for h in partner_collabs if h.get("success"))
            return success_count / len(partner_collabs)
    
    def get_top_collaborators(
        self,
        agent_id: str,
        limit: int = 5,
    ) -> List[Tuple[str, float]]:
        with self._lock:
            history = self.collaboration_history.get(agent_id, [])
            
            partner_scores: Dict[str, List[bool]] = defaultdict(list)
            for h in history:
                if "partner_id" in h:
                    partner_scores[h["partner_id"]].append(h.get("success", False))
            
            scores = [
                (partner, sum(successes) / len(successes))
                for partner, successes in partner_scores.items()
            ]
            
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return scores[:limit]
    
    def get_all_reputations(self) -> Dict[str, float]:
        with self._lock:
            return self.reputations.copy()


class CollaborationProtocol:
    """
    跨部门协作协议
    
    定义标准化的跨部门协作协议：
    1. 协作消息类型
    2. 消息格式
    3. 响应机制
    4. 能量结算
    5. 信誉系统
    """
    
    DEFAULT_MESSAGE_TIMEOUT = 300
    MAX_PENDING_MESSAGES = 1000
    
    def __init__(
        self,
        communication_bus: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        reputation_system: Optional[ReputationSystem] = None,
    ):
        self.communication_bus = communication_bus
        self.blackboard = blackboard
        self.reputation_system = reputation_system or ReputationSystem()
        
        self.pending_messages: Dict[str, CollaborationMessage] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_handlers: Dict[CollaborationMessageType, Callable] = {}
        
        self.active_collaborations: Dict[str, CollaborationRecord] = {}
        self.collaboration_history: deque = deque(maxlen=10000)
        
        self.teams: Dict[str, Dict] = {}
        self.agent_teams: Dict[str, str] = {}
        
        self._lock = threading.RLock()
        self._running = False
        
        self._register_default_handlers()
        
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "collaborations_started": 0,
            "collaborations_completed": 0,
            "collaborations_failed": 0,
            "total_energy_transferred": 0.0,
            "avg_response_time_ms": 0.0,
        }
    
    def _register_default_handlers(self):
        self.message_handlers[CollaborationMessageType.REQUEST_HELP] = self._handle_request_help
        self.message_handlers[CollaborationMessageType.OFFER_RESULT] = self._handle_offer_result
        self.message_handlers[CollaborationMessageType.TASK_SPLIT] = self._handle_task_split
        self.message_handlers[CollaborationMessageType.PROGRESS_UPDATE] = self._handle_progress_update
        self.message_handlers[CollaborationMessageType.MERGE_REQUEST] = self._handle_merge_request
        self.message_handlers[CollaborationMessageType.ACCEPT] = self._handle_accept
        self.message_handlers[CollaborationMessageType.REJECT] = self._handle_reject
        self.message_handlers[CollaborationMessageType.COUNTER_OFFER] = self._handle_counter_offer
    
    async def start(self):
        self._running = True
        logger.info("Collaboration protocol started")
    
    async def stop(self):
        self._running = False
        logger.info("Collaboration protocol stopped")
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: CollaborationMessageType,
        payload: Dict,
        energy_offer: float = 0.0,
        deadline: Optional[float] = None,
        task_id: Optional[str] = None,
        team_id: Optional[str] = None,
        priority: int = 1,
        timeout: float = DEFAULT_MESSAGE_TIMEOUT,
    ) -> CollaborationMessage:
        """
        发送协作消息
        
        Args:
            from_agent: 发送方智能体ID
            to_agent: 接收方智能体ID
            message_type: 消息类型
            payload: 消息负载
            energy_offer: 愿意支付的协作能量
            deadline: 截止时间
            task_id: 关联任务ID
            team_id: 团队ID
            priority: 优先级
            timeout: 超时时间
            
        Returns:
            CollaborationMessage: 创建的消息
        """
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        
        message = CollaborationMessage(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            energy_offer=energy_offer,
            deadline=deadline,
            task_id=task_id,
            team_id=team_id,
            priority=priority,
            expires_at=time.time() + timeout,
        )
        
        with self._lock:
            self.pending_messages[message_id] = message
            self.stats["messages_sent"] += 1
        
        if self.communication_bus:
            await self._deliver_message(message)
        
        logger.debug(f"Message sent: {message_id} from {from_agent} to {to_agent}")
        
        return message
    
    async def request_help(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        required_skill: str,
        data: Dict,
        energy_offer: float = 5.0,
        deadline: Optional[float] = None,
    ) -> CollaborationMessage:
        """
        请求协助
        
        Args:
            from_agent: 请求方智能体ID
            to_agent: 协助方智能体ID
            task_id: 任务ID
            required_skill: 所需技能
            data: 数据
            energy_offer: 愿意支付的协作能量
            deadline: 截止时间
            
        Returns:
            CollaborationMessage: 请求消息
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=CollaborationMessageType.REQUEST_HELP,
            payload={
                "task_id": task_id,
                "required_skill": required_skill,
                "data": data,
            },
            energy_offer=energy_offer,
            deadline=deadline,
            task_id=task_id,
        )
    
    async def offer_result(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        result: Dict,
        energy_request: float = 0.0,
    ) -> CollaborationMessage:
        """
        提供结果
        
        Args:
            from_agent: 提供方智能体ID
            to_agent: 接收方智能体ID
            task_id: 任务ID
            result: 结果数据
            energy_request: 请求的能量
            
        Returns:
            CollaborationMessage: 结果消息
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=CollaborationMessageType.OFFER_RESULT,
            payload={
                "task_id": task_id,
                "result": result,
            },
            energy_offer=energy_request,
            task_id=task_id,
        )
    
    async def task_split(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        sub_tasks: List[Dict],
    ) -> CollaborationMessage:
        """
        任务拆解建议
        
        Args:
            from_agent: 发送方智能体ID
            to_agent: 接收方智能体ID
            task_id: 任务ID
            sub_tasks: 子任务列表
            
        Returns:
            CollaborationMessage: 拆解消息
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=CollaborationMessageType.TASK_SPLIT,
            payload={
                "task_id": task_id,
                "sub_tasks": sub_tasks,
            },
            task_id=task_id,
        )
    
    async def progress_update(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        progress: float,
        status: str,
        details: Optional[Dict] = None,
    ) -> CollaborationMessage:
        """
        进度更新
        
        Args:
            from_agent: 发送方智能体ID
            to_agent: 接收方智能体ID
            task_id: 任务ID
            progress: 进度 (0.0-1.0)
            status: 状态
            details: 详情
            
        Returns:
            CollaborationMessage: 进度消息
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=CollaborationMessageType.PROGRESS_UPDATE,
            payload={
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "details": details or {},
            },
            task_id=task_id,
            priority=2,
        )
    
    async def merge_request(
        self,
        from_agent: str,
        to_agent: str,
        task_id: str,
        partial_results: Dict,
    ) -> CollaborationMessage:
        """
        合并结果请求
        
        Args:
            from_agent: 发送方智能体ID
            to_agent: 接收方智能体ID
            task_id: 任务ID
            partial_results: 部分结果
            
        Returns:
            CollaborationMessage: 合并请求
        """
        return await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=CollaborationMessageType.MERGE_REQUEST,
            payload={
                "task_id": task_id,
                "partial_results": partial_results,
            },
            task_id=task_id,
        )
    
    async def accept(
        self,
        original_message: CollaborationMessage,
        from_agent: str,
        payload: Optional[Dict] = None,
    ) -> CollaborationResponse:
        """
        接受协作请求
        
        Args:
            original_message: 原始消息
            from_agent: 接受方智能体ID
            payload: 额外负载
            
        Returns:
            CollaborationResponse: 响应
        """
        response = CollaborationResponse(
            response_id=f"resp_{uuid.uuid4().hex[:8]}",
            original_message_id=original_message.message_id,
            from_agent=from_agent,
            to_agent=original_message.from_agent,
            response_type="accept",
            accepted=True,
            payload=payload or {},
            energy_transfer=original_message.energy_offer,
        )
        
        await self._record_collaboration_start(
            original_message, response
        )
        
        return response
    
    async def reject(
        self,
        original_message: CollaborationMessage,
        from_agent: str,
        reason: str = "",
    ) -> CollaborationResponse:
        """
        拒绝协作请求
        
        Args:
            original_message: 原始消息
            from_agent: 拒绝方智能体ID
            reason: 原因
            
        Returns:
            CollaborationResponse: 响应
        """
        return CollaborationResponse(
            response_id=f"resp_{uuid.uuid4().hex[:8]}",
            original_message_id=original_message.message_id,
            from_agent=from_agent,
            to_agent=original_message.from_agent,
            response_type="reject",
            accepted=False,
            payload={"reason": reason},
            message=reason,
        )
    
    async def counter_offer(
        self,
        original_message: CollaborationMessage,
        from_agent: str,
        new_energy_offer: float,
        new_deadline: Optional[float] = None,
        conditions: Optional[Dict] = None,
    ) -> CollaborationResponse:
        """
        反报价
        
        Args:
            original_message: 原始消息
            from_agent: 反报价方智能体ID
            new_energy_offer: 新能量报价
            new_deadline: 新截止时间
            conditions: 附加条件
            
        Returns:
            CollaborationResponse: 响应
        """
        return CollaborationResponse(
            response_id=f"resp_{uuid.uuid4().hex[:8]}",
            original_message_id=original_message.message_id,
            from_agent=from_agent,
            to_agent=original_message.from_agent,
            response_type="counter_offer",
            accepted=False,
            payload={
                "new_energy_offer": new_energy_offer,
                "new_deadline": new_deadline,
                "conditions": conditions or {},
            },
            energy_transfer=new_energy_offer,
        )
    
    async def _deliver_message(self, message: CollaborationMessage):
        if self.communication_bus:
            try:
                await self.communication_bus.send(
                    to=message.to_agent,
                    message=message.to_dict()
                )
            except Exception as e:
                logger.error(f"Failed to deliver message: {e}")
    
    async def _record_collaboration_start(
        self,
        message: CollaborationMessage,
        response: CollaborationResponse,
    ):
        record_id = f"collab_{uuid.uuid4().hex[:8]}"
        
        record = CollaborationRecord(
            record_id=record_id,
            task_id=message.task_id or "",
            requester_id=message.from_agent,
            helper_id=response.from_agent,
            message_type=message.message_type,
            energy_offered=message.energy_offer,
            energy_transferred=response.energy_transfer,
            success=False,
            started_at=time.time(),
        )
        
        with self._lock:
            self.active_collaborations[record_id] = record
            self.stats["collaborations_started"] += 1
    
    async def complete_collaboration(
        self,
        record_id: str,
        success: bool,
        energy_settled: float = 0.0,
    ):
        with self._lock:
            if record_id not in self.active_collaborations:
                return
            
            record = self.active_collaborations[record_id]
            record.success = success
            record.completed_at = time.time()
            record.energy_transferred = energy_settled
            
            self.collaboration_history.append(record)
            del self.active_collaborations[record_id]
            
            if success:
                self.stats["collaborations_completed"] += 1
                self.reputation_system.update_reputation(
                    record.helper_id, success=True
                )
            else:
                self.stats["collaborations_failed"] += 1
                self.reputation_system.update_reputation(
                    record.helper_id, success=False
                )
            
            self.stats["total_energy_transferred"] += energy_settled
    
    async def _handle_request_help(self, message: CollaborationMessage):
        logger.debug(f"Handling REQUEST_HELP from {message.from_agent}")
    
    async def _handle_offer_result(self, message: CollaborationMessage):
        logger.debug(f"Handling OFFER_RESULT from {message.from_agent}")
    
    async def _handle_task_split(self, message: CollaborationMessage):
        logger.debug(f"Handling TASK_SPLIT from {message.from_agent}")
    
    async def _handle_progress_update(self, message: CollaborationMessage):
        logger.debug(f"Handling PROGRESS_UPDATE from {message.from_agent}")
    
    async def _handle_merge_request(self, message: CollaborationMessage):
        logger.debug(f"Handling MERGE_REQUEST from {message.from_agent}")
    
    async def _handle_accept(self, message: CollaborationMessage):
        logger.debug(f"Handling ACCEPT from {message.from_agent}")
    
    async def _handle_reject(self, message: CollaborationMessage):
        logger.debug(f"Handling REJECT from {message.from_agent}")
    
    async def _handle_counter_offer(self, message: CollaborationMessage):
        logger.debug(f"Handling COUNTER_OFFER from {message.from_agent}")
    
    async def form_team(
        self,
        leader_id: str,
        member_ids: List[str],
        task_id: str,
        team_name: str = "",
    ) -> str:
        team_id = f"team_{uuid.uuid4().hex[:8]}"
        
        team = {
            "team_id": team_id,
            "name": team_name or f"Team-{team_id[:8]}",
            "leader_id": leader_id,
            "member_ids": member_ids,
            "task_id": task_id,
            "created_at": time.time(),
            "status": "active",
        }
        
        with self._lock:
            self.teams[team_id] = team
            for member_id in [leader_id] + member_ids:
                self.agent_teams[member_id] = team_id
        
        logger.info(f"Team formed: {team_id} with leader {leader_id}")
        
        return team_id
    
    async def dissolve_team(self, team_id: str):
        with self._lock:
            if team_id not in self.teams:
                return
            
            team = self.teams[team_id]
            
            for member_id in [team["leader_id"]] + team["member_ids"]:
                if member_id in self.agent_teams:
                    del self.agent_teams[member_id]
            
            team["status"] = "dissolved"
            del self.teams[team_id]
        
        logger.info(f"Team dissolved: {team_id}")
    
    def get_team(self, team_id: str) -> Optional[Dict]:
        return self.teams.get(team_id)
    
    def get_agent_team(self, agent_id: str) -> Optional[str]:
        return self.agent_teams.get(agent_id)
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "pending_messages": len(self.pending_messages),
                "active_collaborations": len(self.active_collaborations),
                "active_teams": len(self.teams),
                "reputation_summary": self.reputation_system.get_all_reputations(),
            }
