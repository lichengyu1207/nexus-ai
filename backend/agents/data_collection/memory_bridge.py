"""
记忆与样本库桥接
实现海马体记忆系统与数据样本库的双向同步
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    META = "meta"


class SyncDirection(str, Enum):
    MEMORY_TO_SAMPLE = "memory_to_sample"
    SAMPLE_TO_MEMORY = "sample_to_memory"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MemoryExport(BaseModel):
    export_id: str = Field(default_factory=lambda: str(uuid4()))
    memory_type: MemoryType
    agent_id: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    exported_at: datetime = Field(default_factory=datetime.now)


class SampleImport(BaseModel):
    import_id: str = Field(default_factory=lambda: str(uuid4()))
    sample_id: str
    memory_type: MemoryType
    importance: float = 0.5
    imported_at: datetime = Field(default_factory=datetime.now)


class SyncRecord(BaseModel):
    sync_id: str = Field(default_factory=lambda: str(uuid4()))
    direction: SyncDirection
    status: SyncStatus = SyncStatus.PENDING
    items_synced: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MemoryToSampleConverter:
    def __init__(self):
        self.memory_type_mapping = {
            MemoryType.EPISODIC: "interaction",
            MemoryType.SEMANTIC: "knowledge",
            MemoryType.PROCEDURAL: "agent_trace",
            MemoryType.META: "knowledge"
        }
    
    def convert(
        self,
        memory: Dict[str, Any],
        memory_type: MemoryType
    ) -> Dict[str, Any]:
        sample_type = self.memory_type_mapping.get(memory_type, "text")
        
        sample = {
            "type": sample_type,
            "content": self._extract_content(memory, memory_type),
            "tags": self._extract_tags(memory, memory_type),
            "metadata": {
                "source": "memory",
                "memory_type": memory_type.value,
                "original_memory_id": memory.get("id"),
                "agent_id": memory.get("agent_id")
            }
        }
        
        if memory_type == MemoryType.EPISODIC:
            sample["content"]["episode_summary"] = self._summarize_episode(memory)
        
        return sample
    
    def _extract_content(
        self,
        memory: Dict[str, Any],
        memory_type: MemoryType
    ) -> Dict[str, Any]:
        content = memory.get("content", {})
        
        if memory_type == MemoryType.EPISODIC:
            return {
                "event": content.get("event", ""),
                "context": content.get("context", {}),
                "outcome": content.get("outcome", ""),
                "timestamp": memory.get("created_at", datetime.now().isoformat())
            }
        elif memory_type == MemoryType.SEMANTIC:
            return {
                "knowledge": content.get("knowledge", ""),
                "domain": content.get("domain", "general"),
                "confidence": content.get("confidence", 0.5),
                "source": content.get("source", "unknown")
            }
        elif memory_type == MemoryType.PROCEDURAL:
            return {
                "procedure": content.get("procedure", ""),
                "steps": content.get("steps", []),
                "success_rate": content.get("success_rate", 0.5)
            }
        else:
            return content
    
    def _extract_tags(
        self,
        memory: Dict[str, Any],
        memory_type: MemoryType
    ) -> List[str]:
        tags = [memory_type.value]
        
        content = memory.get("content", {})
        
        if "domain" in content:
            tags.append(content["domain"])
        
        if "event_type" in content:
            tags.append(content["event_type"])
        
        if memory.get("importance", 0) > 0.8:
            tags.append("high_importance")
        
        return tags
    
    def _summarize_episode(self, memory: Dict[str, Any]) -> str:
        content = memory.get("content", {})
        event = content.get("event", "")
        outcome = content.get("outcome", "")
        
        return f"{event[:100]}... -> {outcome[:50]}"


class SampleToMemoryConverter:
    def __init__(self):
        self.sample_type_mapping = {
            "interaction": MemoryType.EPISODIC,
            "knowledge": MemoryType.SEMANTIC,
            "agent_trace": MemoryType.PROCEDURAL,
            "text": MemoryType.SEMANTIC
        }
    
    def convert(
        self,
        sample: Dict[str, Any],
        importance_threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        sample_type = sample.get("type", "text")
        memory_type = self.sample_type_mapping.get(sample_type, MemoryType.SEMANTIC)
        
        quality = sample.get("quality", 0.5)
        if quality < importance_threshold:
            return None
        
        memory = {
            "type": memory_type.value,
            "content": self._build_content(sample, memory_type),
            "importance": quality,
            "metadata": {
                "source": "sample_library",
                "sample_id": sample.get("id"),
                "collected_at": sample.get("created_at")
            }
        }
        
        return memory
    
    def _build_content(
        self,
        sample: Dict[str, Any],
        memory_type: MemoryType
    ) -> Dict[str, Any]:
        content = sample.get("content", {})
        
        if memory_type == MemoryType.EPISODIC:
            return {
                "event": content.get("event", content.get("query", "")),
                "context": content.get("context", {}),
                "outcome": content.get("outcome", content.get("response", "")),
                "feedback": sample.get("feedback")
            }
        elif memory_type == MemoryType.SEMANTIC:
            return {
                "knowledge": content.get("knowledge", json.dumps(content, ensure_ascii=False)[:500]),
                "domain": self._infer_domain(sample),
                "confidence": sample.get("quality", 0.5),
                "tags": sample.get("tags", [])
            }
        elif memory_type == MemoryType.PROCEDURAL:
            return {
                "procedure": content.get("procedure", ""),
                "steps": content.get("steps", content.get("decision_trace", [])),
                "success_rate": sample.get("quality", 0.5)
            }
        
        return content
    
    def _infer_domain(self, sample: Dict[str, Any]) -> str:
        tags = sample.get("tags", [])
        
        domain_keywords = {
            "valuation": ["valuation", "property", "price"],
            "legal": ["legal", "law", "contract"],
            "market": ["market", "trend", "analysis"],
            "user": ["user", "preference", "behavior"]
        }
        
        for domain, keywords in domain_keywords.items():
            for tag in tags:
                if any(kw in tag.lower() for kw in keywords):
                    return domain
        
        return "general"


class MemorySampleBridge:
    def __init__(
        self,
        memory_system: Optional[Any] = None,
        sample_repository: Optional[Any] = None,
        quality_assessor: Optional[Any] = None
    ):
        self.memory_system = memory_system
        self.sample_repository = sample_repository
        self.quality_assessor = quality_assessor
        
        self.memory_to_sample_converter = MemoryToSampleConverter()
        self.sample_to_memory_converter = SampleToMemoryConverter()
        
        self.sync_history: List[SyncRecord] = []
        self.export_history: List[MemoryExport] = []
        self.import_history: List[SampleImport] = []
        
        self.auto_sync_interval = timedelta(hours=6)
        self.importance_threshold = 0.7
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        self.logger.info("MemorySampleBridge initialized")
    
    async def export_memory_to_sample(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> SyncRecord:
        record = SyncRecord(
            direction=SyncDirection.MEMORY_TO_SAMPLE,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            memories = await self._fetch_memories(agent_id, memory_type, limit)
            
            for memory in memories:
                try:
                    sample = self.memory_to_sample_converter.convert(
                        memory,
                        MemoryType(memory.get("type", "semantic"))
                    )
                    
                    if self.quality_assessor:
                        from .sample_quality import SampleForAssessment
                        assessment = await self.quality_assessor.assess(
                            SampleForAssessment(
                                id=str(uuid4()),
                                type=sample["type"],
                                content=sample["content"],
                                created_at=datetime.now()
                            )
                        )
                        sample["quality"] = assessment.overall
                    
                    if self.sample_repository:
                        sample_id = await self.sample_repository.store(sample)
                        record.items_synced += 1
                        
                        export = MemoryExport(
                            memory_type=MemoryType(memory.get("type", "semantic")),
                            agent_id=agent_id,
                            content=sample["content"],
                            metadata={"sample_id": sample_id}
                        )
                        self.export_history.append(export)
                        
                except Exception as e:
                    record.errors.append(f"Failed to export memory {memory.get('id')}: {str(e)}")
            
            record.status = SyncStatus.COMPLETED
            record.completed_at = datetime.now()
            
        except Exception as e:
            record.status = SyncStatus.FAILED
            record.errors.append(str(e))
            record.completed_at = datetime.now()
        
        self.sync_history.append(record)
        return record
    
    async def import_sample_to_memory(
        self,
        sample_types: Optional[List[str]] = None,
        min_quality: float = 0.7,
        limit: int = 100
    ) -> SyncRecord:
        record = SyncRecord(
            direction=SyncDirection.SAMPLE_TO_MEMORY,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            samples = await self._fetch_samples(sample_types, min_quality, limit)
            
            for sample in samples:
                try:
                    memory = self.sample_to_memory_converter.convert(
                        sample,
                        self.importance_threshold
                    )
                    
                    if memory and self.memory_system:
                        memory_id = await self._store_memory(memory)
                        record.items_synced += 1
                        
                        import_record = SampleImport(
                            sample_id=sample.get("id"),
                            memory_type=MemoryType(memory["type"]),
                            importance=memory.get("importance", 0.5)
                        )
                        self.import_history.append(import_record)
                        
                except Exception as e:
                    record.errors.append(f"Failed to import sample {sample.get('id')}: {str(e)}")
            
            record.status = SyncStatus.COMPLETED
            record.completed_at = datetime.now()
            
        except Exception as e:
            record.status = SyncStatus.FAILED
            record.errors.append(str(e))
            record.completed_at = datetime.now()
        
        self.sync_history.append(record)
        return record
    
    async def bidirectional_sync(
        self,
        agent_id: str,
        sample_types: Optional[List[str]] = None
    ) -> Dict[str, SyncRecord]:
        export_record = await self.export_memory_to_sample(agent_id)
        
        import_record = await self.import_sample_to_memory(sample_types)
        
        return {
            "export": export_record,
            "import": import_record
        }
    
    async def _fetch_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType],
        limit: int
    ) -> List[Dict[str, Any]]:
        if not self.memory_system:
            return []
        
        try:
            memories = await self.memory_system.get_agent_memories(
                agent_id,
                memory_type.value if memory_type else None,
                limit
            )
            return memories or []
        except Exception as e:
            self.logger.error(f"Error fetching memories: {e}")
            return []
    
    async def _fetch_samples(
        self,
        sample_types: Optional[List[str]],
        min_quality: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        if not self.sample_repository:
            return []
        
        try:
            from .sample_repository import SampleQuery, SampleType
            
            types = [SampleType(t) for t in sample_types] if sample_types else None
            
            query = SampleQuery(
                types=types,
                min_quality=min_quality,
                limit=limit,
                order_by="quality",
                order_desc=True
            )
            
            samples = await self.sample_repository.query(query)
            return [s.dict() for s in samples]
        except Exception as e:
            self.logger.error(f"Error fetching samples: {e}")
            return []
    
    async def _store_memory(self, memory: Dict[str, Any]) -> str:
        if not self.memory_system:
            return ""
        
        try:
            memory_id = await self.memory_system.store_long_term_memory(memory)
            return memory_id
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            return ""
    
    async def export_attack_patterns(self, agent_id: str) -> List[str]:
        if not self.memory_system:
            return []
        
        try:
            attack_memories = await self.memory_system.get_agent_memories(
                agent_id,
                MemoryType.PROCEDURAL.value,
                50
            )
            
            sample_ids = []
            for memory in attack_memories:
                if "attack" in memory.get("content", {}).get("procedure", "").lower():
                    sample = self.memory_to_sample_converter.convert(
                        memory,
                        MemoryType.PROCEDURAL
                    )
                    sample["tags"].append("attack_pattern")
                    
                    if self.sample_repository:
                        sample_id = await self.sample_repository.store(sample)
                        sample_ids.append(sample_id)
            
            return sample_ids
            
        except Exception as e:
            self.logger.error(f"Error exporting attack patterns: {e}")
            return []
    
    async def import_high_quality_samples(self, min_quality: float = 0.8) -> int:
        record = await self.import_sample_to_memory(
            sample_types=None,
            min_quality=min_quality,
            limit=100
        )
        
        return record.items_synced
    
    async def start_auto_sync(self):
        self._running = True
        asyncio.create_task(self._auto_sync_loop())
    
    async def stop_auto_sync(self):
        self._running = False
    
    async def _auto_sync_loop(self):
        while self._running:
            try:
                await self.bidirectional_sync("system")
                
                await asyncio.sleep(self.auto_sync_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto sync loop: {e}")
                await asyncio.sleep(300)
    
    def get_statistics(self) -> Dict[str, Any]:
        successful_exports = [r for r in self.sync_history 
                            if r.direction == SyncDirection.MEMORY_TO_SAMPLE 
                            and r.status == SyncStatus.COMPLETED]
        successful_imports = [r for r in self.sync_history 
                            if r.direction == SyncDirection.SAMPLE_TO_MEMORY 
                            and r.status == SyncStatus.COMPLETED]
        
        return {
            "total_syncs": len(self.sync_history),
            "successful_exports": len(successful_exports),
            "successful_imports": len(successful_imports),
            "total_items_exported": sum(r.items_synced for r in successful_exports),
            "total_items_imported": sum(r.items_synced for r in successful_imports),
            "export_history_size": len(self.export_history),
            "import_history_size": len(self.import_history)
        }
    
    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [
            {
                "sync_id": r.sync_id,
                "direction": r.direction.value,
                "status": r.status.value,
                "items_synced": r.items_synced,
                "errors": r.errors,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in self.sync_history[-limit:]
        ]
