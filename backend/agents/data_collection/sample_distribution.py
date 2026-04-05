"""
样本分发服务
负责将样本库中的样本分发给有需要的智能体
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DistributionMode(str, Enum):
    PUSH = "push"
    PULL = "pull"
    STREAMING = "streaming"


class DistributionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class SampleRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    sample_types: List[str]
    quantity: int = 100
    min_quality: float = 0.5
    max_quality: float = 1.0
    tags: Optional[List[str]] = None
    mode: DistributionMode = DistributionMode.PULL
    priority: DistributionPriority = DistributionPriority.NORMAL
    exclude_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class SampleBatch(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    samples: List[Dict[str, Any]]
    total_count: int
    avg_quality: float
    distributed_at: datetime = Field(default_factory=datetime.now)


class SampleLock(BaseModel):
    lock_id: str
    sample_id: str
    agent_id: str
    locked_at: datetime
    expires_at: datetime


class DistributionStats(BaseModel):
    total_distributed: int
    by_type: Dict[str, int]
    by_agent: Dict[str, int]
    avg_quality: float


class SampleDeduplicator:
    def __init__(self):
        self.agent_received: Dict[str, Set[str]] = defaultdict(set)
        self.sample_hash_cache: Dict[str, str] = {}
    
    def mark_received(self, agent_id: str, sample_ids: List[str]):
        self.agent_received[agent_id].update(sample_ids)
    
    def filter_duplicates(
        self,
        agent_id: str,
        samples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        received = self.agent_received.get(agent_id, set())
        
        unique_samples = []
        for sample in samples:
            sample_id = sample.get("id")
            if sample_id and sample_id not in received:
                unique_samples.append(sample)
        
        return unique_samples
    
    def compute_sample_hash(self, sample: Dict[str, Any]) -> str:
        import hashlib
        import json
        
        content = sample.get("content", {})
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def clear_agent_history(self, agent_id: str):
        if agent_id in self.agent_received:
            del self.agent_received[agent_id]


class LoadBalancer:
    def __init__(self, max_concurrent_per_agent: int = 5):
        self.max_concurrent_per_agent = max_concurrent_per_agent
        self.agent_requests: Dict[str, List[str]] = defaultdict(list)
        self.request_queue: List[SampleRequest] = []
    
    def enqueue_request(self, request: SampleRequest) -> int:
        priority_order = {
            DistributionPriority.HIGH: 0,
            DistributionPriority.NORMAL: 1,
            DistributionPriority.LOW: 2
        }
        
        priority = priority_order.get(request.priority, 1)
        
        inserted = False
        for i, queued in enumerate(self.request_queue):
            queued_priority = priority_order.get(queued.priority, 1)
            if priority < queued_priority:
                self.request_queue.insert(i, request)
                inserted = True
                break
        
        if not inserted:
            self.request_queue.append(request)
        
        return len(self.request_queue)
    
    def get_next_request(self) -> Optional[SampleRequest]:
        while self.request_queue:
            request = self.request_queue.pop(0)
            
            active_count = len(self.agent_requests.get(request.agent_id, []))
            if active_count < self.max_concurrent_per_agent:
                self.agent_requests[request.agent_id].append(request.request_id)
                return request
        
        return None
    
    def complete_request(self, request_id: str, agent_id: str):
        if agent_id in self.agent_requests:
            if request_id in self.agent_requests[agent_id]:
                self.agent_requests[agent_id].remove(request_id)
    
    def get_queue_length(self) -> int:
        return len(self.request_queue)


class SampleLockManager:
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.locks: Dict[str, SampleLock] = {}
        self.sample_locks: Dict[str, str] = {}
    
    def acquire_lock(
        self,
        sample_id: str,
        agent_id: str,
        ttl: Optional[int] = None
    ) -> Optional[str]:
        if sample_id in self.sample_locks:
            return None
        
        lock_id = str(uuid4())
        now = datetime.now()
        
        lock = SampleLock(
            lock_id=lock_id,
            sample_id=sample_id,
            agent_id=agent_id,
            locked_at=now,
            expires_at=now + timedelta(seconds=ttl or self.default_ttl)
        )
        
        self.locks[lock_id] = lock
        self.sample_locks[sample_id] = lock_id
        
        return lock_id
    
    def release_lock(self, lock_id: str) -> bool:
        if lock_id not in self.locks:
            return False
        
        lock = self.locks[lock_id]
        
        if lock.sample_id in self.sample_locks:
            del self.sample_locks[lock.sample_id]
        
        del self.locks[lock_id]
        
        return True
    
    def is_locked(self, sample_id: str) -> bool:
        if sample_id not in self.sample_locks:
            return False
        
        lock_id = self.sample_locks[sample_id]
        lock = self.locks.get(lock_id)
        
        if not lock:
            return False
        
        if lock.expires_at < datetime.now():
            self.release_lock(lock_id)
            return False
        
        return True
    
    def cleanup_expired(self):
        now = datetime.now()
        expired_locks = [
            lock_id for lock_id, lock in self.locks.items()
            if lock.expires_at < now
        ]
        
        for lock_id in expired_locks:
            self.release_lock(lock_id)


class FeedbackCollector:
    def __init__(self):
        self.feedback_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.sample_performance: Dict[str, Dict[str, float]] = {}
    
    def record_feedback(
        self,
        sample_id: str,
        agent_id: str,
        feedback_type: str,
        value: float,
        details: Optional[Dict[str, Any]] = None
    ):
        feedback = {
            "sample_id": sample_id,
            "agent_id": agent_id,
            "feedback_type": feedback_type,
            "value": value,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_history[sample_id].append(feedback)
        
        self._update_sample_performance(sample_id, feedback_type, value)
    
    def _update_sample_performance(
        self,
        sample_id: str,
        feedback_type: str,
        value: float
    ):
        if sample_id not in self.sample_performance:
            self.sample_performance[sample_id] = {
                "training_loss_delta": 0.0,
                "task_success_rate": 0.0,
                "feedback_count": 0
            }
        
        perf = self.sample_performance[sample_id]
        perf["feedback_count"] += 1
        
        if feedback_type == "training_loss_delta":
            perf["training_loss_delta"] = (
                perf["training_loss_delta"] * (perf["feedback_count"] - 1) + value
            ) / perf["feedback_count"]
        elif feedback_type == "task_success":
            perf["task_success_rate"] = (
                perf["task_success_rate"] * (perf["feedback_count"] - 1) + value
            ) / perf["feedback_count"]
    
    def get_sample_performance(self, sample_id: str) -> Optional[Dict[str, float]]:
        return self.sample_performance.get(sample_id)
    
    def get_low_performing_samples(self, threshold: float = 0.3) -> List[str]:
        return [
            sample_id for sample_id, perf in self.sample_performance.items()
            if perf.get("task_success_rate", 1.0) < threshold
        ]


class SampleDistributionService:
    def __init__(
        self,
        sample_repository: Optional[Any] = None,
        quality_assessor: Optional[Any] = None
    ):
        self.sample_repository = sample_repository
        self.quality_assessor = quality_assessor
        
        self.deduplicator = SampleDeduplicator()
        self.load_balancer = LoadBalancer()
        self.lock_manager = SampleLockManager()
        self.feedback_collector = FeedbackCollector()
        
        self.distribution_history: List[SampleBatch] = []
        self.streaming_subscriptions: Dict[str, List[str]] = defaultdict(list)
        
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        self.logger.info("SampleDistributionService initialized")
    
    async def request_samples(
        self,
        request: SampleRequest
    ) -> SampleBatch:
        queue_position = self.load_balancer.enqueue_request(request)
        
        self.logger.info(
            f"Sample request {request.request_id} queued at position {queue_position}"
        )
        
        return await self._process_request(request)
    
    async def _process_request(self, request: SampleRequest) -> SampleBatch:
        if not self.sample_repository:
            return SampleBatch(
                request_id=request.request_id,
                samples=[],
                total_count=0,
                avg_quality=0.0
            )
        
        from .sample_repository import SampleQuery, SampleType
        
        sample_types = [SampleType(t) for t in request.sample_types if t]
        
        query = SampleQuery(
            types=sample_types if sample_types else None,
            tags=request.tags,
            min_quality=request.min_quality,
            max_quality=request.max_quality,
            limit=request.quantity * 2
        )
        
        samples = await self.sample_repository.query(query)
        
        samples = self.deduplicator.filter_duplicates(
            request.agent_id,
            [s.dict() for s in samples]
        )
        
        samples = [
            s for s in samples
            if s.get("id") not in request.exclude_ids
        ]
        
        samples = [
            s for s in samples
            if not self.lock_manager.is_locked(s.get("id", ""))
        ]
        
        samples = self._prioritize_samples(samples, request.priority)
        samples = samples[:request.quantity]
        
        for sample in samples:
            sample_id = sample.get("id", "")
            self.lock_manager.acquire_lock(sample_id, request.agent_id)
        
        self.deduplicator.mark_received(
            request.agent_id,
            [s.get("id") for s in samples if s.get("id")]
        )
        
        avg_quality = sum(s.get("quality", 0.5) for s in samples) / len(samples) if samples else 0.0
        
        batch = SampleBatch(
            request_id=request.request_id,
            samples=samples,
            total_count=len(samples),
            avg_quality=avg_quality
        )
        
        self.distribution_history.append(batch)
        
        self.load_balancer.complete_request(request.request_id, request.agent_id)
        
        self.logger.info(
            f"Distributed {len(samples)} samples to {request.agent_id}, "
            f"avg quality: {avg_quality:.2f}"
        )
        
        return batch
    
    def _prioritize_samples(
        self,
        samples: List[Dict[str, Any]],
        priority: DistributionPriority
    ) -> List[Dict[str, Any]]:
        if priority == DistributionPriority.HIGH:
            samples.sort(key=lambda s: s.get("quality", 0), reverse=True)
        elif priority == DistributionPriority.LOW:
            samples.sort(key=lambda s: s.get("usage_count", 0))
        else:
            samples.sort(key=lambda s: (
                -s.get("quality", 0.5),
                s.get("usage_count", 0)
            ))
        
        return samples
    
    async def push_samples(
        self,
        agent_id: str,
        samples: List[Dict[str, Any]],
        priority: DistributionPriority = DistributionPriority.NORMAL
    ) -> bool:
        samples = self.deduplicator.filter_duplicates(agent_id, samples)
        
        if not samples:
            return False
        
        for sample in samples:
            sample_id = sample.get("id", "")
            self.lock_manager.acquire_lock(sample_id, agent_id)
        
        self.deduplicator.mark_received(
            agent_id,
            [s.get("id") for s in samples if s.get("id")]
        )
        
        self.logger.info(f"Pushed {len(samples)} samples to {agent_id}")
        
        return True
    
    async def subscribe_streaming(
        self,
        agent_id: str,
        sample_types: List[str],
        min_quality: float = 0.5
    ):
        for sample_type in sample_types:
            if agent_id not in self.streaming_subscriptions[sample_type]:
                self.streaming_subscriptions[sample_type].append(agent_id)
        
        self.logger.info(f"Agent {agent_id} subscribed to streaming for {sample_types}")
    
    async def unsubscribe_streaming(
        self,
        agent_id: str,
        sample_types: Optional[List[str]] = None
    ):
        if sample_types:
            for sample_type in sample_types:
                if agent_id in self.streaming_subscriptions[sample_type]:
                    self.streaming_subscriptions[sample_type].remove(agent_id)
        else:
            for agents in self.streaming_subscriptions.values():
                if agent_id in agents:
                    agents.remove(agent_id)
    
    async def broadcast_new_sample(self, sample: Dict[str, Any]):
        sample_type = sample.get("type", "")
        
        if sample_type not in self.streaming_subscriptions:
            return
        
        for agent_id in self.streaming_subscriptions[sample_type]:
            await self.push_samples(agent_id, [sample])
    
    async def record_usage_feedback(
        self,
        sample_id: str,
        agent_id: str,
        training_loss_delta: Optional[float] = None,
        task_success: Optional[bool] = None
    ):
        if training_loss_delta is not None:
            self.feedback_collector.record_feedback(
                sample_id, agent_id, "training_loss_delta", training_loss_delta
            )
        
        if task_success is not None:
            self.feedback_collector.record_feedback(
                sample_id, agent_id, "task_success", 1.0 if task_success else 0.0
            )
        
        if self.quality_assessor:
            await self.quality_assessor.record_usage_feedback(
                sample_id,
                training_loss_delta,
                task_success
            )
    
    async def release_samples(self, sample_ids: List[str], agent_id: str):
        for sample_id in sample_ids:
            lock_id = self.lock_manager.sample_locks.get(sample_id)
            if lock_id:
                lock = self.lock_manager.locks.get(lock_id)
                if lock and lock.agent_id == agent_id:
                    self.lock_manager.release_lock(lock_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        total_distributed = sum(b.total_count for b in self.distribution_history)
        
        by_type: Dict[str, int] = defaultdict(int)
        for batch in self.distribution_history:
            for sample in batch.samples:
                sample_type = sample.get("type", "unknown")
                by_type[sample_type] += 1
        
        avg_quality = (
            sum(b.avg_quality for b in self.distribution_history) /
            len(self.distribution_history)
            if self.distribution_history else 0.0
        )
        
        return {
            "total_distributed": total_distributed,
            "total_batches": len(self.distribution_history),
            "by_type": dict(by_type),
            "avg_quality": avg_quality,
            "queue_length": self.load_balancer.get_queue_length(),
            "active_locks": len(self.lock_manager.locks),
            "streaming_subscriptions": {
                k: len(v) for k, v in self.streaming_subscriptions.items()
            }
        }
    
    async def start_cleanup_task(self):
        self._running = True
        asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        self._running = False
    
    async def _cleanup_loop(self):
        while self._running:
            try:
                self.lock_manager.cleanup_expired()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
