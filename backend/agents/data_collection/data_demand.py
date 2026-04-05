"""
数据需求感知器
让智能体能够感知自身和集群的数据需求
"""
import asyncio
import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DemandUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DemandStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DataDemand(BaseModel):
    demand_id: str = Field(default_factory=lambda: str(uuid4()))
    requesting_agent_id: str
    data_type: str
    required_quality: float = 0.5
    quantity: int = 100
    urgency: DemandUrgency = DemandUrgency.MEDIUM
    reward_offer: float = 10.0
    requirements: Dict[str, Any] = Field(default_factory=dict)
    status: DemandStatus = DemandStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    fulfilled_by: Optional[str] = None


class KnowledgeBlindSpot(BaseModel):
    blind_spot_id: str
    domain: str
    missing_samples: int
    impact_score: float
    detected_at: datetime
    examples: List[str] = Field(default_factory=list)


class DemandHeatMap(BaseModel):
    data_type: str
    demand_count: int
    avg_urgency: float
    avg_reward: float
    fulfillment_rate: float
    trend: str


class BlindSpotDetector:
    def __init__(
        self,
        sample_threshold: int = 50,
        impact_threshold: float = 0.3
    ):
        self.sample_threshold = sample_threshold
        self.impact_threshold = impact_threshold
        
        self.domain_samples: Dict[str, int] = {}
        self.domain_performance: Dict[str, float] = {}
        self.detected_blind_spots: List[KnowledgeBlindSpot] = []
    
    def update_domain_stats(
        self,
        domain: str,
        sample_count: int,
        performance: float
    ):
        self.domain_samples[domain] = sample_count
        self.domain_performance[domain] = performance
    
    def detect_blind_spots(self) -> List[KnowledgeBlindSpot]:
        blind_spots = []
        
        for domain, sample_count in self.domain_samples.items():
            performance = self.domain_performance.get(domain, 0.5)
            
            if sample_count < self.sample_threshold:
                impact = 1.0 - (sample_count / self.sample_threshold)
                
                if impact >= self.impact_threshold:
                    blind_spot = KnowledgeBlindSpot(
                        blind_spot_id=f"bs_{domain}_{datetime.now().timestamp()}",
                        domain=domain,
                        missing_samples=self.sample_threshold - sample_count,
                        impact_score=impact,
                        detected_at=datetime.now()
                    )
                    blind_spots.append(blind_spot)
            
            if performance < 0.5:
                impact = 0.5 - performance
                
                if impact >= self.impact_threshold:
                    blind_spot = KnowledgeBlindSpot(
                        blind_spot_id=f"bs_perf_{domain}_{datetime.now().timestamp()}",
                        domain=domain,
                        missing_samples=int(impact * 100),
                        impact_score=impact * 2,
                        detected_at=datetime.now()
                    )
                    blind_spots.append(blind_spot)
        
        self.detected_blind_spots.extend(blind_spots)
        
        return blind_spots
    
    def get_domain_gaps(self) -> Dict[str, Tuple[int, float]]:
        gaps = {}
        
        for domain, sample_count in self.domain_samples.items():
            if sample_count < self.sample_threshold:
                gaps[domain] = (
                    self.sample_threshold - sample_count,
                    self.domain_performance.get(domain, 0.5)
                )
        
        return gaps


class DemandPredictor:
    def __init__(self, prediction_window: int = 7):
        self.prediction_window = prediction_window
        
        self.historical_demands: List[DataDemand] = []
        self.demand_patterns: Dict[str, List[int]] = {}
    
    def record_demand(self, demand: DataDemand):
        self.historical_demands.append(demand)
        
        data_type = demand.data_type
        if data_type not in self.demand_patterns:
            self.demand_patterns[data_type] = []
        
        self.demand_patterns[data_type].append(1)
    
    def predict_future_demands(self) -> List[Dict[str, Any]]:
        predictions = []
        
        for data_type, pattern in self.demand_patterns.items():
            if len(pattern) < 3:
                continue
            
            recent = pattern[-7:] if len(pattern) >= 7 else pattern
            avg_daily = sum(recent) / len(recent)
            
            trend = "stable"
            if len(pattern) >= 7:
                first_half = sum(pattern[-7:-3])
                second_half = sum(pattern[-3:])
                if second_half > first_half * 1.2:
                    trend = "increasing"
                elif second_half < first_half * 0.8:
                    trend = "decreasing"
            
            predictions.append({
                "data_type": data_type,
                "predicted_daily_demand": avg_daily,
                "trend": trend,
                "confidence": min(1.0, len(pattern) / 30)
            })
        
        return predictions
    
    def get_seasonal_patterns(self) -> Dict[str, Dict[str, Any]]:
        patterns = {}
        
        for data_type, demands in self.demand_patterns.items():
            if len(demands) < 14:
                continue
            
            patterns[data_type] = {
                "weekly_avg": sum(demands[-7:]) / 7,
                "daily_variance": self._variance(demands[-7:]),
                "peak_day": demands[-7:].index(max(demands[-7:]))
            }
        
        return patterns
    
    def _variance(self, values: List[int]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)


class DemandMatcher:
    def __init__(self):
        self.open_demands: Dict[str, DataDemand] = {}
        self.collector_capabilities: Dict[str, List[str]] = {}
    
    def register_demand(self, demand: DataDemand):
        self.open_demands[demand.demand_id] = demand
    
    def register_collector(self, collector_id: str, capabilities: List[str]):
        self.collector_capabilities[collector_id] = capabilities
    
    def find_matching_demands(
        self,
        collector_id: str,
        limit: int = 10
    ) -> List[DataDemand]:
        capabilities = self.collector_capabilities.get(collector_id, [])
        
        matching = []
        for demand in self.open_demands.values():
            if demand.status != DemandStatus.OPEN:
                continue
            
            if self._can_fulfill(capabilities, demand):
                score = self._compute_match_score(demand)
                matching.append((demand, score))
        
        matching.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in matching[:limit]]
    
    def _can_fulfill(
        self,
        capabilities: List[str],
        demand: DataDemand
    ) -> bool:
        data_type = demand.data_type
        
        for cap in capabilities:
            if cap == data_type or cap == "all" or data_type.startswith(cap):
                return True
        
        return False
    
    def _compute_match_score(self, demand: DataDemand) -> float:
        urgency_scores = {
            DemandUrgency.LOW: 1,
            DemandUrgency.MEDIUM: 2,
            DemandUrgency.HIGH: 3,
            DemandUrgency.CRITICAL: 4
        }
        
        return (
            urgency_scores.get(demand.urgency, 1) * 0.4 +
            demand.reward_offer * 0.3 +
            demand.required_quality * 0.3
        )


class DataDemandSensor:
    def __init__(
        self,
        agent_id: str,
        blackboard: Optional[Any] = None,
        memory_system: Optional[Any] = None,
        sample_repository: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.blackboard = blackboard
        self.memory_system = memory_system
        self.sample_repository = sample_repository
        
        self.blind_spot_detector = BlindSpotDetector()
        self.demand_predictor = DemandPredictor()
        self.demand_matcher = DemandMatcher()
        
        self.posted_demands: Dict[str, DataDemand] = {}
        self.fulfilled_demands: List[DataDemand] = []
        
        self._demand_check_interval = 300
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"DataDemandSensor {self.agent_id} initialized")
    
    async def detect_knowledge_blind_spots(self) -> List[KnowledgeBlindSpot]:
        await self._update_domain_stats()
        
        blind_spots = self.blind_spot_detector.detect_blind_spots()
        
        for blind_spot in blind_spots:
            demand = await self._create_demand_from_blind_spot(blind_spot)
            if demand:
                await self.post_demand(demand)
        
        return blind_spots
    
    async def _update_domain_stats(self):
        if not self.sample_repository:
            return
        
        try:
            stats = await self.sample_repository.get_statistics()
            
            by_type = stats.get("by_type", {})
            for data_type, count in by_type.items():
                self.blind_spot_detector.update_domain_stats(
                    data_type,
                    count,
                    stats.get("avg_quality", 0.5)
                )
        except Exception as e:
            self.logger.error(f"Error updating domain stats: {e}")
    
    async def _create_demand_from_blind_spot(
        self,
        blind_spot: KnowledgeBlindSpot
    ) -> Optional[DataDemand]:
        urgency = DemandUrgency.MEDIUM
        if blind_spot.impact_score > 0.7:
            urgency = DemandUrgency.CRITICAL
        elif blind_spot.impact_score > 0.5:
            urgency = DemandUrgency.HIGH
        
        reward = blind_spot.impact_score * 50 + blind_spot.missing_samples * 0.1
        
        demand = DataDemand(
            requesting_agent_id=self.agent_id,
            data_type=blind_spot.domain,
            required_quality=0.6,
            quantity=blind_spot.missing_samples,
            urgency=urgency,
            reward_offer=reward,
            requirements={
                "blind_spot_id": blind_spot.blind_spot_id,
                "impact_score": blind_spot.impact_score
            },
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        return demand
    
    async def post_demand(self, demand: DataDemand) -> str:
        self.posted_demands[demand.demand_id] = demand
        
        self.demand_predictor.record_demand(demand)
        
        if self.blackboard:
            await self.blackboard.post(
                topic="data_demand",
                message=demand.dict(),
                publisher=self.agent_id
            )
        
        self.logger.info(
            f"Posted demand {demand.demand_id} for {demand.data_type}, "
            f"urgency: {demand.urgency.value}, reward: {demand.reward_offer}"
        )
        
        return demand.demand_id
    
    async def create_demand(
        self,
        data_type: str,
        quantity: int = 100,
        required_quality: float = 0.5,
        urgency: DemandUrgency = DemandUrgency.MEDIUM,
        requirements: Optional[Dict[str, Any]] = None
    ) -> DataDemand:
        demand = DataDemand(
            requesting_agent_id=self.agent_id,
            data_type=data_type,
            required_quality=required_quality,
            quantity=quantity,
            urgency=urgency,
            requirements=requirements or {}
        )
        
        await self.post_demand(demand)
        
        return demand
    
    async def check_demand_fulfillment(
        self,
        samples: List[Dict[str, Any]],
        data_type: str
    ) -> Optional[DataDemand]:
        for demand_id, demand in self.posted_demands.items():
            if demand.status != DemandStatus.OPEN:
                continue
            
            if demand.data_type != data_type:
                continue
            
            valid_samples = [
                s for s in samples
                if s.get("quality", 0) >= demand.required_quality
            ]
            
            if len(valid_samples) >= demand.quantity:
                demand.status = DemandStatus.FULFILLED
                demand.fulfilled_at = datetime.now()
                demand.fulfilled_by = "collector"
                
                self.fulfilled_demands.append(demand)
                del self.posted_demands[demand_id]
                
                self.logger.info(f"Demand {demand_id} fulfilled")
                
                return demand
        
        return None
    
    async def get_matching_demands(
        self,
        collector_capabilities: List[str]
    ) -> List[DataDemand]:
        collector_id = f"collector_{datetime.now().timestamp()}"
        self.demand_matcher.register_collector(collector_id, collector_capabilities)
        
        return self.demand_matcher.find_matching_demands(collector_id)
    
    async def get_demand_heat_map(self) -> List[DemandHeatMap]:
        heat_map = []
        
        demands_by_type: Dict[str, List[DataDemand]] = {}
        for demand in self.posted_demands.values():
            if demand.status == DemandStatus.OPEN:
                if demand.data_type not in demands_by_type:
                    demands_by_type[demand.data_type] = []
                demands_by_type[demand.data_type].append(demand)
        
        for data_type, demands in demands_by_type.items():
            urgency_values = {
                DemandUrgency.LOW: 1,
                DemandUrgency.MEDIUM: 2,
                DemandUrgency.HIGH: 3,
                DemandUrgency.CRITICAL: 4
            }
            
            avg_urgency = sum(
                urgency_values.get(d.urgency, 2) for d in demands
            ) / len(demands)
            
            avg_reward = sum(d.reward_offer for d in demands) / len(demands)
            
            fulfilled_count = len([
                d for d in self.fulfilled_demands
                if d.data_type == data_type
            ])
            total_count = len(demands) + fulfilled_count
            fulfillment_rate = fulfilled_count / total_count if total_count > 0 else 0
            
            predictions = self.demand_predictor.predict_future_demands()
            trend = "stable"
            for pred in predictions:
                if pred["data_type"] == data_type:
                    trend = pred["trend"]
                    break
            
            heat_map.append(DemandHeatMap(
                data_type=data_type,
                demand_count=len(demands),
                avg_urgency=avg_urgency,
                avg_reward=avg_reward,
                fulfillment_rate=fulfillment_rate,
                trend=trend
            ))
        
        return heat_map
    
    async def analyze_user_feedback(self, feedback_events: List[Dict[str, Any]]):
        for event in feedback_events:
            feedback_type = event.get("feedback_type", "")
            
            if feedback_type in ["negative", "complaint"]:
                task_type = event.get("task_type", "general")
                
                demand = DataDemand(
                    requesting_agent_id=self.agent_id,
                    data_type=task_type,
                    required_quality=0.7,
                    quantity=50,
                    urgency=DemandUrgency.HIGH,
                    reward_offer=30.0,
                    requirements={
                        "trigger": "user_feedback",
                        "feedback_id": event.get("id")
                    }
                )
                
                await self.post_demand(demand)
    
    async def start_monitoring(self):
        self._running = True
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        self._running = False
    
    async def _monitoring_loop(self):
        while self._running:
            try:
                await self.detect_knowledge_blind_spots()
                
                await self._check_expired_demands()
                
                await asyncio.sleep(self._demand_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_expired_demands(self):
        now = datetime.now()
        expired_ids = []
        
        for demand_id, demand in self.posted_demands.items():
            if demand.expires_at and demand.expires_at < now:
                demand.status = DemandStatus.EXPIRED
                expired_ids.append(demand_id)
        
        for demand_id in expired_ids:
            del self.posted_demands[demand_id]
    
    def get_statistics(self) -> Dict[str, Any]:
        open_demands = [d for d in self.posted_demands.values() if d.status == DemandStatus.OPEN]
        
        return {
            "open_demands": len(open_demands),
            "fulfilled_demands": len(self.fulfilled_demands),
            "detected_blind_spots": len(self.blind_spot_detector.detected_blind_spots),
            "domain_gaps": len(self.blind_spot_detector.get_domain_gaps()),
            "demand_predictions": len(self.demand_predictor.predict_future_demands())
        }
