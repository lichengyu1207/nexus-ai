"""
智能体间数据交换智能体
收集其他智能体的交互数据（通信、协作、任务执行过程）
"""
import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

from .data_collector import DataCollectorAgent, CollectionResult


class AgentInteractionType(str, Enum):
    COMMUNICATION = "communication"
    COLLABORATION = "collaboration"
    TASK_EXECUTION = "task_execution"
    DECISION_TRACE = "decision_trace"
    KNOWLEDGE_SHARING = "knowledge_sharing"


class InteractionOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ONGOING = "ongoing"


class AgentInteractionSample(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    interaction_type: AgentInteractionType
    source_agent_id: str
    target_agent_id: Optional[str] = None
    involved_agents: List[str] = Field(default_factory=list)
    content: Dict[str, Any]
    outcome: InteractionOutcome = InteractionOutcome.ONGOING
    decision_trace: List[Dict[str, Any]] = Field(default_factory=list)
    reward: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)


class CollaborationPattern(BaseModel):
    pattern_id: str
    agents_involved: List[str]
    task_type: str
    success_rate: float
    avg_completion_time: float
    communication_patterns: List[str]
    failure_modes: List[str]


class DecisionTraceRecorder:
    def __init__(self):
        self.traces: Dict[str, List[Dict[str, Any]]] = {}
        self.max_trace_length = 100
    
    def start_trace(self, agent_id: str, task_id: str) -> str:
        trace_id = f"{agent_id}_{task_id}_{datetime.now().timestamp()}"
        self.traces[trace_id] = []
        return trace_id
    
    def record_step(
        self,
        trace_id: str,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float = 0.0,
        info: Optional[Dict[str, Any]] = None
    ):
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        
        step = {
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "action": action,
            "reward": reward,
            "info": info or {}
        }
        
        self.traces[trace_id].append(step)
        
        if len(self.traces[trace_id]) > self.max_trace_length:
            self.traces[trace_id] = self.traces[trace_id][-self.max_trace_length:]
    
    def end_trace(self, trace_id: str, outcome: str) -> Optional[List[Dict[str, Any]]]:
        if trace_id in self.traces:
            trace = self.traces[trace_id]
            for step in trace:
                step["outcome"] = outcome
            del self.traces[trace_id]
            return trace
        return None
    
    def get_active_traces(self) -> List[str]:
        return list(self.traces.keys())


class CollaborationAnalyzer:
    def __init__(self):
        self.patterns: Dict[str, CollaborationPattern] = {}
        self.interaction_history: List[AgentInteractionSample] = []
        self.max_history = 1000
    
    def analyze_interaction(self, sample: AgentInteractionSample) -> Optional[CollaborationPattern]:
        self.interaction_history.append(sample)
        if len(self.interaction_history) > self.max_history:
            self.interaction_history = self.interaction_history[-self.max_history:]
        
        if sample.interaction_type == AgentInteractionType.COLLABORATION:
            pattern_key = self._generate_pattern_key(sample)
            
            if pattern_key not in self.patterns:
                self.patterns[pattern_key] = CollaborationPattern(
                    pattern_id=pattern_key,
                    agents_involved=sample.involved_agents,
                    task_type=sample.content.get("task_type", "unknown"),
                    success_rate=1.0 if sample.outcome == InteractionOutcome.SUCCESS else 0.0,
                    avg_completion_time=sample.metadata.get("duration", 0),
                    communication_patterns=[],
                    failure_modes=[]
                )
            else:
                self._update_pattern(self.patterns[pattern_key], sample)
            
            return self.patterns[pattern_key]
        
        return None
    
    def _generate_pattern_key(self, sample: AgentInteractionSample) -> str:
        agents = sorted(sample.involved_agents)
        task_type = sample.content.get("task_type", "unknown")
        return f"{'_'.join(agents)}_{task_type}"
    
    def _update_pattern(self, pattern: CollaborationPattern, sample: AgentInteractionSample):
        total = len([s for s in self.interaction_history 
                    if self._generate_pattern_key(s) == pattern.pattern_id])
        
        successes = len([s for s in self.interaction_history 
                        if self._generate_pattern_key(s) == pattern.pattern_id 
                        and s.outcome == InteractionOutcome.SUCCESS])
        
        pattern.success_rate = successes / total if total > 0 else 0.0
        
        if sample.metadata.get("duration"):
            durations = [s.metadata.get("duration", 0) for s in self.interaction_history 
                        if self._generate_pattern_key(s) == pattern.pattern_id]
            pattern.avg_completion_time = sum(durations) / len(durations) if durations else 0
        
        if sample.outcome == InteractionOutcome.FAILURE:
            failure_mode = sample.content.get("error_type", "unknown")
            if failure_mode not in pattern.failure_modes:
                pattern.failure_modes.append(failure_mode)
    
    def get_successful_patterns(self, min_success_rate: float = 0.8) -> List[CollaborationPattern]:
        return [p for p in self.patterns.values() if p.success_rate >= min_success_rate]
    
    def get_failure_patterns(self) -> List[CollaborationPattern]:
        return [p for p in self.patterns.values() if p.success_rate < 0.5]


class AgentInteractionCollectorAgent(DataCollectorAgent):
    def __init__(
        self,
        agent_id: str,
        name: str = "AgentInteractionCollector",
        message_bus: Optional[Any] = None,
        sample_repository: Optional[Any] = None,
        memory_system: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            source_type="other_agents",
            **kwargs
        )
        self.message_bus = message_bus
        self.sample_repository = sample_repository
        self.memory_system = memory_system
        self.trace_recorder = DecisionTraceRecorder()
        self.collaboration_analyzer = CollaborationAnalyzer()
        self._collection_buffer: List[AgentInteractionSample] = []
        self._subscribed_topics: Set[str] = set()
        self._sensitive_keywords = [
            "password", "secret", "key", "token", "credential",
            "private", "confidential"
        ]
    
    async def initialize(self):
        await super().initialize()
        await self._subscribe_to_message_bus()
        self.logger.info(f"AgentInteractionCollector {self.agent_id} initialized")
    
    async def _subscribe_to_message_bus(self):
        if self.message_bus:
            topics = [
                "agent.communication",
                "agent.collaboration",
                "agent.task.start",
                "agent.task.complete",
                "agent.decision",
                "agent.knowledge.share"
            ]
            
            for topic in topics:
                self.message_bus.subscribe(topic, self._handle_message)
                self._subscribed_topics.add(topic)
    
    async def _handle_message(self, topic: str, message: Dict[str, Any]):
        try:
            if self._contains_sensitive_info(message):
                self.logger.debug(f"Skipping message with sensitive info: {topic}")
                return
            
            if "communication" in topic:
                await self._process_communication(message)
            elif "collaboration" in topic:
                await self._process_collaboration(message)
            elif "task" in topic:
                await self._process_task_event(topic, message)
            elif "decision" in topic:
                await self._process_decision(message)
            elif "knowledge" in topic:
                await self._process_knowledge_sharing(message)
                
        except Exception as e:
            self.logger.error(f"Error handling message from {topic}: {e}")
    
    def _contains_sensitive_info(self, message: Dict[str, Any]) -> bool:
        message_str = json.dumps(message, ensure_ascii=False).lower()
        return any(keyword in message_str for keyword in self._sensitive_keywords)
    
    async def _process_communication(self, message: Dict[str, Any]):
        sample = AgentInteractionSample(
            interaction_type=AgentInteractionType.COMMUNICATION,
            source_agent_id=message.get("sender_id", "unknown"),
            target_agent_id=message.get("receiver_id"),
            involved_agents=[
                message.get("sender_id", "unknown"),
                message.get("receiver_id", "unknown")
            ],
            content={
                "message_type": message.get("type", "unknown"),
                "subject": message.get("subject", ""),
                "summary": self._summarize_content(message.get("content", ""))
            },
            outcome=InteractionOutcome.SUCCESS if message.get("delivered", True) else InteractionOutcome.FAILURE,
            metadata={
                "channel": message.get("channel", "default"),
                "priority": message.get("priority", "normal")
            },
            tags=["communication", message.get("type", "unknown")]
        )
        
        await self._add_to_buffer(sample)
    
    async def _process_collaboration(self, message: Dict[str, Any]):
        outcome = InteractionOutcome.ONGOING
        if message.get("status") == "completed":
            outcome = InteractionOutcome.SUCCESS
        elif message.get("status") == "failed":
            outcome = InteractionOutcome.FAILURE
        elif message.get("status") == "partial":
            outcome = InteractionOutcome.PARTIAL
        
        sample = AgentInteractionSample(
            interaction_type=AgentInteractionType.COLLABORATION,
            source_agent_id=message.get("initiator_id", "unknown"),
            involved_agents=message.get("participants", []),
            content={
                "task_type": message.get("task_type", "unknown"),
                "task_description": message.get("description", ""),
                "coordination_method": message.get("coordination_method", "unknown")
            },
            outcome=outcome,
            metadata={
                "duration": message.get("duration", 0),
                "resource_usage": message.get("resource_usage", {}),
                "error_type": message.get("error_type")
            },
            tags=["collaboration", message.get("task_type", "unknown")]
        )
        
        pattern = self.collaboration_analyzer.analyze_interaction(sample)
        if pattern:
            sample.metadata["pattern_id"] = pattern.pattern_id
            sample.metadata["pattern_success_rate"] = pattern.success_rate
        
        await self._add_to_buffer(sample)
    
    async def _process_task_event(self, topic: str, message: Dict[str, Any]):
        if "start" in topic:
            trace_id = self.trace_recorder.start_trace(
                message.get("agent_id", "unknown"),
                message.get("task_id", "unknown")
            )
            message["trace_id"] = trace_id
        elif "complete" in topic:
            trace_id = message.get("trace_id")
            if trace_id:
                outcome = InteractionOutcome.SUCCESS if message.get("success", True) else InteractionOutcome.FAILURE
                trace = self.trace_recorder.end_trace(trace_id, outcome.value)
                
                if trace:
                    sample = AgentInteractionSample(
                        interaction_type=AgentInteractionType.TASK_EXECUTION,
                        source_agent_id=message.get("agent_id", "unknown"),
                        content={
                            "task_id": message.get("task_id"),
                            "task_type": message.get("task_type", "unknown"),
                            "result_summary": self._summarize_content(str(message.get("result", "")))
                        },
                        outcome=outcome,
                        decision_trace=trace,
                        reward=message.get("reward", 0.0),
                        metadata={
                            "duration": message.get("duration", 0),
                            "resource_usage": message.get("resource_usage", {})
                        },
                        tags=["task_execution", message.get("task_type", "unknown")]
                    )
                    
                    await self._add_to_buffer(sample)
    
    async def _process_decision(self, message: Dict[str, Any]):
        trace_id = message.get("trace_id")
        if trace_id:
            self.trace_recorder.record_step(
                trace_id=trace_id,
                state=message.get("state", {}),
                action=message.get("action", {}),
                reward=message.get("reward", 0.0),
                info=message.get("info")
            )
    
    async def _process_knowledge_sharing(self, message: Dict[str, Any]):
        sample = AgentInteractionSample(
            interaction_type=AgentInteractionType.KNOWLEDGE_SHARING,
            source_agent_id=message.get("sender_id", "unknown"),
            target_agent_id=message.get("receiver_id"),
            involved_agents=[
                message.get("sender_id", "unknown"),
                message.get("receiver_id", "unknown")
            ],
            content={
                "knowledge_type": message.get("knowledge_type", "unknown"),
                "knowledge_summary": self._summarize_content(str(message.get("knowledge", ""))),
                "transfer_method": message.get("method", "direct")
            },
            outcome=InteractionOutcome.SUCCESS if message.get("accepted", True) else InteractionOutcome.FAILURE,
            metadata={
                "knowledge_size": len(str(message.get("knowledge", ""))),
                "compression_ratio": message.get("compression_ratio", 1.0)
            },
            tags=["knowledge_sharing", message.get("knowledge_type", "unknown")]
        )
        
        await self._add_to_buffer(sample)
    
    def _summarize_content(self, content: str, max_length: int = 200) -> str:
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."
    
    async def _add_to_buffer(self, sample: AgentInteractionSample):
        self._collection_buffer.append(sample)
        self.collected_count += 1
        
        if len(self._collection_buffer) >= 100:
            await self.collect()
    
    async def collect(self) -> CollectionResult:
        try:
            if not self._collection_buffer:
                return CollectionResult(
                    success=True,
                    data={"samples_stored": 0},
                    metadata={"buffer_empty": True}
                )
            
            samples = self._collection_buffer.copy()
            self._collection_buffer.clear()
            
            stored_count = 0
            for sample in samples:
                if await self._store_sample(sample):
                    stored_count += 1
            
            await self._store_to_memory(samples)
            
            return CollectionResult(
                success=True,
                data={"samples_stored": stored_count},
                metadata={"total_samples": len(samples)}
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting agent interactions: {e}")
            return CollectionResult(
                success=False,
                error=str(e)
            )
    
    async def _store_sample(self, sample: AgentInteractionSample) -> bool:
        if self.sample_repository:
            try:
                await self.sample_repository.store({
                    "id": sample.id,
                    "type": "agent_interaction",
                    "interaction_type": sample.interaction_type.value,
                    "source_agent_id": sample.source_agent_id,
                    "target_agent_id": sample.target_agent_id,
                    "involved_agents": sample.involved_agents,
                    "content": sample.content,
                    "outcome": sample.outcome.value,
                    "decision_trace": sample.decision_trace,
                    "reward": sample.reward,
                    "metadata": sample.metadata,
                    "tags": sample.tags,
                    "collected_at": sample.collected_at.isoformat(),
                    "collector_agent_id": self.agent_id
                })
                return True
            except Exception as e:
                self.logger.error(f"Error storing sample: {e}")
                return False
        return True
    
    async def _store_to_memory(self, samples: List[AgentInteractionSample]):
        if self.memory_system:
            try:
                for sample in samples:
                    if sample.outcome in [InteractionOutcome.SUCCESS, InteractionOutcome.FAILURE]:
                        await self.memory_system.store_meta_memory({
                            "type": "agent_interaction",
                            "interaction_type": sample.interaction_type.value,
                            "agents": sample.involved_agents,
                            "outcome": sample.outcome.value,
                            "lesson": self._extract_lesson(sample),
                            "timestamp": sample.collected_at.isoformat()
                        })
            except Exception as e:
                self.logger.error(f"Error storing to memory: {e}")
    
    def _extract_lesson(self, sample: AgentInteractionSample) -> str:
        if sample.outcome == InteractionOutcome.SUCCESS:
            return f"Successful {sample.interaction_type.value} pattern for {sample.content.get('task_type', 'unknown')} task"
        else:
            return f"Failed {sample.interaction_type.value}: {sample.content.get('error_type', 'unknown reason')}"
    
    async def get_collaboration_insights(self) -> Dict[str, Any]:
        successful_patterns = self.collaboration_analyzer.get_successful_patterns()
        failure_patterns = self.collaboration_analyzer.get_failure_patterns()
        
        return {
            "successful_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "agents": p.agents_involved,
                    "task_type": p.task_type,
                    "success_rate": p.success_rate,
                    "avg_time": p.avg_completion_time
                }
                for p in successful_patterns
            ],
            "failure_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "agents": p.agents_involved,
                    "task_type": p.task_type,
                    "failure_modes": p.failure_modes
                }
                for p in failure_patterns
            ],
            "active_traces": self.trace_recorder.get_active_traces(),
            "total_collected": self.collected_count
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_collected": self.collected_count,
            "buffer_size": len(self._collection_buffer),
            "subscribed_topics": list(self._subscribed_topics),
            "active_traces": len(self.trace_recorder.get_active_traces()),
            "known_patterns": len(self.collaboration_analyzer.patterns)
        }
