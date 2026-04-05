"""
智能体间知识迁移智能体
促进智能体间的知识迁移
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KnowledgeForm(str, Enum):
    MODEL_PARAMETERS = "model_parameters"
    SAMPLES = "samples"
    RULES = "rules"
    HEURISTICS = "heuristics"
    EMBEDDINGS = "embeddings"


class TransferStatus(str, Enum):
    PENDING = "pending"
    PACKAGING = "packaging"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class KnowledgePackage(BaseModel):
    package_id: str = Field(default_factory=lambda: str(uuid4()))
    teacher_agent_id: str
    knowledge_form: KnowledgeForm
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    size_bytes: int = 0
    compression_ratio: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class TransferRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    student_agent_id: str
    teacher_agent_id: str
    knowledge_form: KnowledgeForm
    requirements: Dict[str, Any] = Field(default_factory=dict)
    offered_reward: float = 10.0
    status: TransferStatus = TransferStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)


class TransferRecord(BaseModel):
    transfer_id: str = Field(default_factory=lambda: str(uuid4()))
    request: TransferRequest
    package: Optional[KnowledgePackage] = None
    student_performance_before: Optional[float] = None
    student_performance_after: Optional[float] = None
    performance_improvement: float = 0.0
    teacher_reward: float = 0.0
    completed_at: Optional[datetime] = None


class KnowledgeProvenance(BaseModel):
    knowledge_id: str
    original_source: str
    derivation_chain: List[str]
    transfer_count: int
    last_transferred: Optional[datetime]
    quality_score: float


class TeacherStudentMatcher:
    def __init__(
        self,
        min_compatibility: float = 0.5,
        max_distance: int = 3
    ):
        self.min_compatibility = min_compatibility
        self.max_distance = max_distance
        
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        self.agent_specializations: Dict[str, List[str]] = {}
    
    def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        specializations: Optional[List[str]] = None
    ):
        self.agent_capabilities[agent_id] = set(capabilities)
        self.agent_specializations[agent_id] = specializations or []
    
    def update_performance(
        self,
        agent_id: str,
        task_type: str,
        performance: float
    ):
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {}
        self.agent_performance[agent_id][task_type] = performance
    
    def find_best_teacher(
        self,
        student_id: str,
        task_type: str,
        knowledge_form: KnowledgeForm
    ) -> Optional[str]:
        candidates = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if agent_id == student_id:
                continue
            
            if knowledge_form.value in capabilities or "knowledge_transfer" in capabilities:
                performance = self.agent_performance.get(agent_id, {}).get(task_type, 0.5)
                
                compatibility = self._compute_compatibility(
                    student_id,
                    agent_id,
                    task_type
                )
                
                if compatibility >= self.min_compatibility:
                    candidates.append((agent_id, performance * compatibility))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def _compute_compatibility(
        self,
        student_id: str,
        teacher_id: str,
        task_type: str
    ) -> float:
        student_specs = set(self.agent_specializations.get(student_id, []))
        teacher_specs = set(self.agent_specializations.get(teacher_id, []))
        
        if not student_specs or not teacher_specs:
            return 0.5
        
        overlap = len(student_specs & teacher_specs)
        total = len(student_specs | teacher_specs)
        
        return overlap / total if total > 0 else 0.0


class KnowledgePackager:
    def __init__(self, compression_threshold: int = 1024):
        self.compression_threshold = compression_threshold
    
    async def package(
        self,
        knowledge_form: KnowledgeForm,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgePackage:
        package = KnowledgePackage(
            teacher_agent_id=metadata.get("agent_id", "unknown") if metadata else "unknown",
            knowledge_form=knowledge_form,
            content=content,
            metadata=metadata or {}
        )
        
        content_str = json.dumps(content, ensure_ascii=False)
        package.size_bytes = len(content_str.encode())
        
        if package.size_bytes > self.compression_threshold:
            compressed = self._compress(content)
            if compressed:
                package.content = compressed
                package.compression_ratio = len(json.dumps(compressed)) / len(content_str)
        
        package.expires_at = datetime.now() + timedelta(days=30)
        
        return package
    
    def _compress(self, content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "parameters" in content:
            params = content["parameters"]
            if isinstance(params, dict):
                compressed_params = {}
                for key, value in params.items():
                    if isinstance(value, list) and len(value) > 100:
                        compressed_params[key] = {
                            "mean": sum(value) / len(value),
                            "std": self._std(value),
                            "sample": value[:10]
                        }
                    else:
                        compressed_params[key] = value
                
                return {"parameters_compressed": compressed_params}
        
        return None
    
    def _std(self, values: List[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5


class KnowledgeTransferAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "KnowledgeTransfer",
        energy_manager: Optional[Any] = None,
        knowledge_base: Optional[Any] = None,
        **kwargs
    ):
        self.agent_id = agent_id
        self.name = name
        self.energy_manager = energy_manager
        self.knowledge_base = knowledge_base
        
        self.matcher = TeacherStudentMatcher()
        self.packager = KnowledgePackager()
        
        self.published_knowledge: Dict[str, KnowledgePackage] = {}
        self.transfer_history: List[TransferRecord] = []
        self.provenance: Dict[str, KnowledgeProvenance] = {}
        
        self._subscriptions: Dict[str, List[str]] = {}
        self._pending_requests: Dict[str, TransferRequest] = {}
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.matcher.register_agent(
            self.agent_id,
            capabilities=["knowledge_transfer", "model_parameters", "rules", "samples"],
            specializations=["distillation", "transfer"]
        )
        self.logger.info(f"KnowledgeTransferAgent {self.agent_id} initialized")
    
    async def publish_knowledge(
        self,
        knowledge_form: KnowledgeForm,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        target_agents: Optional[List[str]] = None
    ) -> str:
        package = await self.packager.package(knowledge_form, content, metadata)
        package.teacher_agent_id = self.agent_id
        
        self.published_knowledge[package.package_id] = package
        
        self._record_provenance(
            package.package_id,
            self.agent_id,
            knowledge_form
        )
        
        if target_agents:
            for agent_id in target_agents:
                await self._notify_agent(agent_id, package)
        else:
            await self._broadcast_knowledge(package)
        
        self.logger.info(f"Published knowledge package {package.package_id}")
        
        return package.package_id
    
    async def request_knowledge(
        self,
        teacher_agent_id: str,
        knowledge_form: KnowledgeForm,
        requirements: Optional[Dict[str, Any]] = None,
        offered_reward: float = 10.0
    ) -> str:
        request = TransferRequest(
            student_agent_id=self.agent_id,
            teacher_agent_id=teacher_agent_id,
            knowledge_form=knowledge_form,
            requirements=requirements or {},
            offered_reward=offered_reward
        )
        
        self._pending_requests[request.request_id] = request
        
        await self._send_transfer_request(request)
        
        self.logger.info(f"Requested knowledge from {teacher_agent_id}")
        
        return request.request_id
    
    async def find_teacher(
        self,
        task_type: str,
        knowledge_form: KnowledgeForm
    ) -> Optional[str]:
        return self.matcher.find_best_teacher(
            self.agent_id,
            task_type,
            knowledge_form
        )
    
    async def handle_transfer_request(
        self,
        request: TransferRequest
    ) -> Optional[KnowledgePackage]:
        if request.teacher_agent_id != self.agent_id:
            return None
        
        matching_packages = [
            p for p in self.published_knowledge.values()
            if p.knowledge_form == request.knowledge_form
        ]
        
        if matching_packages:
            best_package = self._select_best_package(matching_packages, request.requirements)
            
            if self.energy_manager:
                reward = request.offered_reward * 0.1
                await self.energy_manager.reward(
                    self.agent_id,
                    reward,
                    "knowledge_transfer"
                )
            
            return best_package
        
        return None
    
    async def receive_knowledge(
        self,
        package: KnowledgePackage,
        request_id: str
    ) -> bool:
        if request_id not in self._pending_requests:
            return False
        
        request = self._pending_requests[request_id]
        
        if self.energy_manager:
            cost = request.offered_reward
            can_afford = await self.energy_manager.consume(
                self.agent_id,
                cost,
                "knowledge_reception"
            )
            if not can_afford:
                request.status = TransferStatus.REJECTED
                return False
        
        record = TransferRecord(
            request=request,
            package=package
        )
        
        self.transfer_history.append(record)
        
        request.status = TransferStatus.COMPLETED
        del self._pending_requests[request_id]
        
        self._update_provenance(package.package_id)
        
        self.logger.info(f"Received knowledge package {package.package_id}")
        
        return True
    
    async def report_performance(
        self,
        transfer_id: str,
        performance_before: float,
        performance_after: float
    ):
        for record in self.transfer_history:
            if record.transfer_id == transfer_id:
                record.student_performance_before = performance_before
                record.student_performance_after = performance_after
                record.performance_improvement = performance_after - performance_before
                record.completed_at = datetime.now()
                
                if record.performance_improvement > 0 and self.energy_manager:
                    bonus = record.performance_improvement * 100
                    record.teacher_reward = bonus
                    await self.energy_manager.reward(
                        record.request.teacher_agent_id,
                        bonus,
                        "successful_knowledge_transfer"
                    )
                
                break
    
    def _select_best_package(
        self,
        packages: List[KnowledgePackage],
        requirements: Dict[str, Any]
    ) -> KnowledgePackage:
        scored_packages = []
        
        for package in packages:
            score = 0.0
            
            if requirements.get("min_size"):
                if package.size_bytes >= requirements["min_size"]:
                    score += 1
            
            if requirements.get("max_size"):
                if package.size_bytes <= requirements["max_size"]:
                    score += 1
            
            if requirements.get("prefer_compressed"):
                score += package.compression_ratio
            
            if requirements.get("freshness_weight"):
                age_hours = (datetime.now() - package.created_at).total_seconds() / 3600
                score -= age_hours * requirements["freshness_weight"]
            
            scored_packages.append((package, score))
        
        scored_packages.sort(key=lambda x: x[1], reverse=True)
        return scored_packages[0][0]
    
    def _record_provenance(
        self,
        knowledge_id: str,
        source: str,
        knowledge_form: KnowledgeForm
    ):
        self.provenance[knowledge_id] = KnowledgeProvenance(
            knowledge_id=knowledge_id,
            original_source=source,
            derivation_chain=[source],
            transfer_count=0,
            quality_score=0.5
        )
    
    def _update_provenance(self, knowledge_id: str):
        if knowledge_id in self.provenance:
            provenance = self.provenance[knowledge_id]
            provenance.transfer_count += 1
            provenance.last_transferred = datetime.now()
            provenance.derivation_chain.append(self.agent_id)
    
    async def _notify_agent(self, agent_id: str, package: KnowledgePackage):
        self.logger.debug(f"Notifying agent {agent_id} about package {package.package_id}")
    
    async def _broadcast_knowledge(self, package: KnowledgePackage):
        self.logger.debug(f"Broadcasting knowledge package {package.package_id}")
    
    async def _send_transfer_request(self, request: TransferRequest):
        self.logger.debug(f"Sending transfer request {request.request_id}")
    
    def subscribe_to_knowledge(
        self,
        knowledge_form: KnowledgeForm,
        callback_agent_id: str
    ):
        form_key = knowledge_form.value
        if form_key not in self._subscriptions:
            self._subscriptions[form_key] = []
        self._subscriptions[form_key].append(callback_agent_id)
    
    def get_available_knowledge(
        self,
        knowledge_form: Optional[KnowledgeForm] = None
    ) -> List[Dict[str, Any]]:
        packages = list(self.published_knowledge.values())
        
        if knowledge_form:
            packages = [p for p in packages if p.knowledge_form == knowledge_form]
        
        return [
            {
                "package_id": p.package_id,
                "knowledge_form": p.knowledge_form.value,
                "size_bytes": p.size_bytes,
                "compression_ratio": p.compression_ratio,
                "created_at": p.created_at.isoformat(),
                "expires_at": p.expires_at.isoformat() if p.expires_at else None
            }
            for p in packages
        ]
    
    def get_transfer_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            {
                "transfer_id": r.transfer_id,
                "teacher": r.request.teacher_agent_id,
                "student": r.request.student_agent_id,
                "knowledge_form": r.request.knowledge_form.value,
                "performance_improvement": r.performance_improvement,
                "teacher_reward": r.teacher_reward,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in self.transfer_history[-limit:]
        ]
    
    def get_provenance(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        if knowledge_id in self.provenance:
            p = self.provenance[knowledge_id]
            return {
                "knowledge_id": p.knowledge_id,
                "original_source": p.original_source,
                "derivation_chain": p.derivation_chain,
                "transfer_count": p.transfer_count,
                "quality_score": p.quality_score
            }
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        successful_transfers = [
            r for r in self.transfer_history
            if r.performance_improvement > 0
        ]
        
        avg_improvement = 0.0
        if successful_transfers:
            avg_improvement = sum(r.performance_improvement for r in successful_transfers) / len(successful_transfers)
        
        return {
            "published_packages": len(self.published_knowledge),
            "total_transfers": len(self.transfer_history),
            "successful_transfers": len(successful_transfers),
            "average_improvement": avg_improvement,
            "total_teacher_rewards": sum(r.teacher_reward for r in self.transfer_history),
            "tracked_provenance": len(self.provenance)
        }
