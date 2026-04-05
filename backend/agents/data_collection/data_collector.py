"""
数据采集智能体基类
Data Collector Agent Base Class

从各类数据源主动获取新鲜数据样本，供集群学习进化
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


class DataSourceType(Enum):
    WEB = "web"
    API = "api"
    DATABASE = "database"
    USER_INTERACTION = "user_interaction"
    OTHER_AGENTS = "other_agents"
    FILE_SYSTEM = "file_system"
    STREAM = "stream"


class CollectionStatus(Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    PARSING = "parsing"
    VALIDATING = "validating"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class CollectionResult:
    collection_id: str
    source_type: DataSourceType
    source_url: str
    raw_data: Any
    parsed_samples: List[Dict]
    quality_scores: List[float]
    success: bool
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    energy_consumed: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "collection_id": self.collection_id,
            "source_type": self.source_type.value,
            "source_url": self.source_url,
            "sample_count": len(self.parsed_samples),
            "avg_quality": sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0,
            "success": self.success,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "energy_consumed": self.energy_consumed,
            "metadata": self.metadata
        }


@dataclass
class CollectionSchedule:
    schedule_id: str
    interval_seconds: float
    next_run: float
    adaptive: bool = True
    min_interval: float = 60.0
    max_interval: float = 86400.0
    backoff_factor: float = 1.5
    success_count: int = 0
    failure_count: int = 0
    last_success_rate: float = 1.0
    
    def update_on_success(self):
        self.success_count += 1
        self.last_success_rate = self.success_count / (self.success_count + self.failure_count)
        
        if self.adaptive and self.last_success_rate > 0.9:
            self.interval_seconds = max(self.min_interval, self.interval_seconds / 1.1)
        
        self.next_run = time.time() + self.interval_seconds
    
    def update_on_failure(self):
        self.failure_count += 1
        self.last_success_rate = self.success_count / (self.success_count + self.failure_count)
        
        if self.adaptive:
            self.interval_seconds = min(self.max_interval, self.interval_seconds * self.backoff_factor)
        
        self.next_run = time.time() + self.interval_seconds
    
    def to_dict(self) -> Dict:
        return {
            "schedule_id": self.schedule_id,
            "interval_seconds": self.interval_seconds,
            "next_run": self.next_run,
            "adaptive": self.adaptive,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_success_rate": self.last_success_rate
        }


class DataCollectorAgent:
    """
    数据采集智能体基类
    
    从各类数据源主动获取新鲜数据样本，供集群学习进化
    
    核心能力：
    1. 数据采集：从多种数据源获取数据
    2. 数据解析：将原始数据转换为结构化样本
    3. 数据验证：验证样本有效性
    4. 数据存储：将样本存入样本库
    5. 自适应调度：根据需求和质量动态调整采集频率
    """
    
    ENERGY_COST_PER_COLLECTION = 1.0
    ENERGY_REWARD_PER_QUALITY_SAMPLE = 0.5
    MIN_ENERGY_FOR_COLLECTION = 5.0
    
    def __init__(
        self,
        agent_id: str,
        source_type: DataSourceType,
        target_url: str = "",
        sample_repository: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        compliance_checker: Optional[Any] = None,
        initial_interval: float = 300.0,
        adaptive_scheduling: bool = True,
    ):
        self.agent_id = agent_id
        self.source_type = source_type
        self.target_url = target_url
        
        self.sample_repository = sample_repository
        self.blackboard = blackboard
        self.memory_agent = memory_agent
        self.compliance_checker = compliance_checker
        
        self.status = CollectionStatus.IDLE
        self.energy = 100.0
        self.max_energy = 200.0
        
        self.schedule = CollectionSchedule(
            schedule_id=f"schedule_{uuid.uuid4().hex[:8]}",
            interval_seconds=initial_interval,
            next_run=time.time() + initial_interval,
            adaptive=adaptive_scheduling
        )
        
        self.collected_count = 0
        self.successful_collections = 0
        self.failed_collections = 0
        self.total_samples_collected = 0
        self.avg_quality_score = 0.0
        
        self.collection_history: deque = deque(maxlen=1000)
        self.pending_demands: List[Dict] = []
        
        self._lock = threading.RLock()
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "total_collections": 0,
            "successful_collections": 0,
            "failed_collections": 0,
            "total_samples": 0,
            "total_energy_consumed": 0.0,
            "avg_quality": 0.0,
            "avg_collection_time_ms": 0.0,
        }
    
    async def start(self):
        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info(f"Data collector agent {self.agent_id} started")
    
    async def stop(self):
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Data collector agent {self.agent_id} stopped")
    
    async def _collection_loop(self):
        while self._running:
            try:
                now = time.time()
                
                if now >= self.schedule.next_run and self.energy >= self.MIN_ENERGY_FOR_COLLECTION:
                    await self.execute_collection_cycle()
                
                await self._check_pending_demands()
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop for {self.agent_id}: {e}")
                await asyncio.sleep(30)
    
    async def execute_collection_cycle(self) -> Optional[CollectionResult]:
        """
        执行一次完整的数据采集周期
        """
        if self.energy < self.MIN_ENERGY_FOR_COLLECTION:
            logger.warning(f"Agent {self.agent_id} has insufficient energy for collection")
            return None
        
        collection_id = f"coll_{uuid.uuid4().hex[:8]}"
        self.status = CollectionStatus.COLLECTING
        
        start_time = time.time()
        energy_consumed = 0.0
        
        try:
            if self.compliance_checker:
                compliance_result = await self.compliance_checker.check_collection(
                    self.agent_id, self.target_url, self.source_type
                )
                if not compliance_result.get("allowed", True):
                    raise ValueError(f"Collection blocked by compliance: {compliance_result.get('reason')}")
            
            raw_data = await self.collect()
            energy_consumed += self.ENERGY_COST_PER_COLLECTION
            self.status = CollectionStatus.PARSING
            
            parsed_samples = await self.parse(raw_data)
            energy_consumed += self.ENERGY_COST_PER_COLLECTION * 0.5
            self.status = CollectionStatus.VALIDATING
            
            validated_samples = []
            quality_scores = []
            
            for sample in parsed_samples:
                if await self.validate(sample):
                    quality_score = await self._assess_quality(sample)
                    sample["quality_score"] = quality_score
                    validated_samples.append(sample)
                    quality_scores.append(quality_score)
            
            self.status = CollectionStatus.STORING
            
            stored_count = 0
            if self.sample_repository and validated_samples:
                for sample in validated_samples:
                    try:
                        await self.sample_repository.store_sample(
                            sample=sample,
                            source_agent_id=self.agent_id,
                            source_type=self.source_type.value
                        )
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store sample: {e}")
            
            self.status = CollectionStatus.COMPLETED
            
            quality_reward = sum(
                self.ENERGY_REWARD_PER_QUALITY_SAMPLE * q
                for q in quality_scores
            )
            self.add_energy(quality_reward)
            
            self.schedule.update_on_success()
            
            result = CollectionResult(
                collection_id=collection_id,
                source_type=self.source_type,
                source_url=self.target_url,
                raw_data=raw_data,
                parsed_samples=validated_samples,
                quality_scores=quality_scores,
                success=True,
                completed_at=time.time(),
                energy_consumed=energy_consumed,
            )
            
            with self._lock:
                self.collection_history.append(result)
                self.collected_count += 1
                self.successful_collections += 1
                self.total_samples_collected += len(validated_samples)
                
                if quality_scores:
                    old_avg = self.avg_quality_score
                    count = self.successful_collections
                    self.avg_quality_score = (old_avg * (count - 1) + sum(quality_scores) / len(quality_scores)) / count
                
                self.stats["total_collections"] += 1
                self.stats["successful_collections"] += 1
                self.stats["total_samples"] += len(validated_samples)
                self.stats["total_energy_consumed"] += energy_consumed
            
            logger.info(f"Collection completed: {collection_id}, samples: {len(validated_samples)}")
            
            return result
            
        except Exception as e:
            self.status = CollectionStatus.FAILED
            self.schedule.update_on_failure()
            
            result = CollectionResult(
                collection_id=collection_id,
                source_type=self.source_type,
                source_url=self.target_url,
                raw_data=None,
                parsed_samples=[],
                quality_scores=[],
                success=False,
                error=str(e),
                completed_at=time.time(),
                energy_consumed=energy_consumed,
            )
            
            with self._lock:
                self.collection_history.append(result)
                self.failed_collections += 1
                self.stats["total_collections"] += 1
                self.stats["failed_collections"] += 1
            
            logger.error(f"Collection failed: {collection_id} - {e}")
            
            return result
        
        finally:
            self.consume_energy(energy_consumed)
            self.status = CollectionStatus.IDLE
    
    async def collect(self) -> Any:
        """
        执行一次数据采集，返回原始数据
        
        子类需要重写此方法
        """
        raise NotImplementedError("Subclasses must implement collect()")
    
    async def parse(self, raw_data: Any) -> List[Dict]:
        """
        解析原始数据，提取结构化样本
        
        子类可以重写此方法
        """
        if isinstance(raw_data, dict):
            return [raw_data]
        elif isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, str):
            try:
                parsed = json.loads(raw_data)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except json.JSONDecodeError:
                return [{"content": raw_data}]
        else:
            return [{"data": str(raw_data)}]
    
    async def validate(self, sample: Dict) -> bool:
        """
        验证样本有效性
        
        子类可以重写此方法
        """
        if not isinstance(sample, dict):
            return False
        
        if not sample:
            return False
        
        return True
    
    async def _assess_quality(self, sample: Dict) -> float:
        """
        评估样本质量
        
        子类可以重写此方法
        """
        quality = 0.5
        
        if sample:
            quality += 0.1
        
        if sample.get("quality_score"):
            quality = sample["quality_score"]
        
        return min(1.0, max(0.0, quality))
    
    async def _check_pending_demands(self):
        """
        检查待处理的数据需求
        """
        if self.blackboard:
            try:
                demands = await self.blackboard.read(f"data_demand:{self.source_type.value}")
                if demands:
                    for demand in demands:
                        if demand not in self.pending_demands:
                            self.pending_demands.append(demand)
                            self._adjust_schedule_for_demand(demand)
            except Exception as e:
                logger.error(f"Failed to check pending demands: {e}")
    
    def _adjust_schedule_for_demand(self, demand: Dict):
        """
        根据需求调整采集调度
        """
        urgency = demand.get("urgency", 0.5)
        reward = demand.get("reward_offer", 0)
        
        if urgency > 0.7 or reward > 10:
            self.schedule.interval_seconds = max(
                self.schedule.min_interval,
                self.schedule.interval_seconds * 0.5
            )
            self.schedule.next_run = time.time()
    
    def add_energy(self, amount: float, reason: str = ""):
        with self._lock:
            actual = min(amount, self.max_energy - self.energy)
            self.energy += actual
    
    def consume_energy(self, amount: float) -> bool:
        with self._lock:
            if self.energy >= amount:
                self.energy -= amount
                return True
            return False
    
    def schedule_next(self):
        """
        根据策略调度下次采集时间
        """
        pass
    
    def get_state(self) -> Dict:
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "source_type": self.source_type.value,
                "target_url": self.target_url,
                "status": self.status.value,
                "energy": self.energy,
                "schedule": self.schedule.to_dict(),
                "collected_count": self.collected_count,
                "successful_collections": self.successful_collections,
                "failed_collections": self.failed_collections,
                "total_samples": self.total_samples_collected,
                "avg_quality": self.avg_quality_score,
                "stats": self.stats.copy(),
            }
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "status": self.status.value,
                "energy": self.energy,
                "pending_demands": len(self.pending_demands),
            }
