"""
不可抵赖记录系统API路由器
Non-Repudiation System API Router

提供自适应学习率、跨物种合作、联邦学习、数据隐私、不可抵赖记录等功能的API接口
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from backend.agents.non_repudiation.adaptive_learning import (
    AdaptiveLRScheduler,
    MetaLearner,
    SchedulerType,
)
from backend.agents.non_repudiation.cross_species_cooperation import (
    TaskDecomposer,
    DepartmentCapabilityRegistry,
    TemporaryTeam,
    GlobalReplayBuffer,
    SharedFeatureNet,
    Department,
)
from backend.agents.non_repudiation.federated_learning import (
    FederatedLearner,
    DPModule,
    DifferentialPrivacy,
    NodeStatus,
)
from backend.agents.non_repudiation.data_privacy import (
    DataMasker,
    SensitiveEntityRecognizer,
    ReversibleMasker,
    MaskStrategy,
    EntityType,
)
from backend.agents.non_repudiation.immutable_logger import (
    ImmutableEventLogger,
    EventType,
    EventStatus,
)
from backend.agents.non_repudiation.trusted_timestamp import (
    TrustedTimestampService,
    TimestampSource,
)
from backend.agents.non_repudiation.training_logger import (
    TrainingLogger,
    TrainingPhase,
)
from backend.agents.non_repudiation.model_registry import (
    ModelRegistry,
    ModelStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/non-repudiation", tags=["Non-Repudiation"])


lr_scheduler = AdaptiveLRScheduler()
meta_learner = MetaLearner()
capability_registry = DepartmentCapabilityRegistry()
task_decomposer = TaskDecomposer(capability_registry)
replay_buffer = GlobalReplayBuffer()
shared_net = SharedFeatureNet()
federated_learner = FederatedLearner()
data_masker = DataMasker()
reversible_masker = ReversibleMasker()
event_logger = ImmutableEventLogger()
timestamp_service = TrustedTimestampService()
training_logger = TrainingLogger()
model_registry = ModelRegistry()


class RegisterAgentRequest(BaseModel):
    agent_id: str
    scheduler_type: str = "reduce_on_plateau"
    initial_lr: float = 0.001
    min_lr: float = 1e-6
    factor: float = 0.5
    patience: int = 5


class StepRequest(BaseModel):
    agent_id: str
    metric: float
    epoch: Optional[int] = None


class DecomposeTaskRequest(BaseModel):
    user_request: str
    context: Dict[str, Any] = Field(default_factory=dict)


class RegisterNodeRequest(BaseModel):
    node_id: str
    name: str
    data_size: int


class ReceiveUpdateRequest(BaseModel):
    node_id: str
    parameters: Dict[str, List[float]]
    num_samples: int
    metrics: Dict[str, float] = Field(default_factory=dict)


class MaskDataRequest(BaseModel):
    text: str
    strategy: Optional[str] = None
    entity_types: Optional[List[str]] = None


class LogEventRequest(BaseModel):
    event_type: str
    details: Dict[str, Any]
    source_node: str = "api"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogAttackRequest(BaseModel):
    attack_type: str
    source_ip: str
    target: str
    defense_action: str
    result: str
    details: Dict[str, Any] = Field(default_factory=dict)


class IssueTimestampRequest(BaseModel):
    data: str
    source: str = "hybrid"


class StartTrainingSessionRequest(BaseModel):
    model_name: str
    hyperparams: Dict[str, Any]
    training_data_hash: Optional[str] = None


class LogEpochRequest(BaseModel):
    session_id: str
    epoch: int
    train_loss: float
    val_loss: float
    accuracy: float
    learning_rate: float
    model_params: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = Field(default_factory=dict)


class RegisterModelRequest(BaseModel):
    model_name: str
    version_number: str
    model_params: Dict[str, Any]
    training_session_id: str
    training_data_hash: str
    hyperparams: Dict[str, Any]
    metrics: Dict[str, float]
    parent_version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerifyModelRequest(BaseModel):
    model_name: str
    current_params: Dict[str, Any]


@router.on_event("startup")
async def startup_event():
    await event_logger.start()
    await timestamp_service.start()
    await model_registry.start()
    logger.info("Non-Repudiation System started")


@router.on_event("shutdown")
async def shutdown_event():
    event_logger.stop()
    timestamp_service.stop()
    model_registry.stop()
    logger.info("Non-Repudiation System stopped")


@router.post("/lr/register")
async def register_agent(request: RegisterAgentRequest):
    try:
        scheduler_type = SchedulerType(request.scheduler_type)
    except ValueError:
        scheduler_type = SchedulerType.REDUCE_ON_PLATEAU
    
    agent_id = lr_scheduler.register_agent(
        agent_id=request.agent_id,
        scheduler_type=scheduler_type,
        initial_lr=request.initial_lr,
        min_lr=request.min_lr,
        factor=request.factor,
        patience=request.patience,
    )
    
    return {"success": True, "agent_id": agent_id}


@router.post("/lr/step")
async def step_scheduler(request: StepRequest):
    new_lr, reduced = lr_scheduler.step(
        agent_id=request.agent_id,
        metric=request.metric,
        epoch=request.epoch,
    )
    
    return {
        "new_lr": new_lr,
        "reduced": reduced,
    }


@router.get("/lr/{agent_id}")
async def get_learning_rate(agent_id: str):
    lr = lr_scheduler.get_lr(agent_id)
    history = lr_scheduler.get_history(agent_id)
    
    return {
        "current_lr": lr,
        "history": history,
    }


@router.get("/lr/stats")
async def get_lr_stats():
    return lr_scheduler.get_stats()


@router.post("/meta/suggest-lr")
async def suggest_learning_rate(
    agent_id: str,
    current_lr: float,
    recent_performance: float
):
    suggestion = meta_learner.suggest_lr(agent_id, current_lr, recent_performance)
    return {"suggestion": suggestion.to_dict()}


@router.get("/meta/history/{agent_id}")
async def get_meta_history(agent_id: str, limit: int = Query(50)):
    history = meta_learner.get_adaptation_history(agent_id, limit)
    return {"history": history}


@router.post("/task/decompose")
async def decompose_task(request: DecomposeTaskRequest):
    task_graph = task_decomposer.decompose(request.user_request, request.context)
    return {"task_graph": task_graph.to_dict()}


@router.get("/task/patterns")
async def get_task_patterns():
    return {"patterns": list(task_decomposer.task_patterns.keys())}


@router.post("/task/pattern")
async def add_task_pattern(
    pattern_name: str,
    pattern: List[Dict[str, Any]]
):
    task_decomposer.add_pattern(pattern_name, pattern)
    return {"success": True}


@router.get("/capabilities")
async def get_capabilities():
    return {
        "departments": [cap.to_dict() for cap in capability_registry.capabilities.values()],
        "available": [cap.to_dict() for cap in capability_registry.get_available_departments()],
    }


@router.post("/replay/add")
async def add_experience(
    state: Dict[str, Any],
    actions: Dict[str, Any],
    reward: float,
    next_state: Dict[str, Any],
    done: bool,
    departments: List[str],
    task_type: str
):
    exp_id = replay_buffer.add(
        state=state,
        actions=actions,
        reward=reward,
        next_state=next_state,
        done=done,
        departments=departments,
        task_type=task_type,
    )
    return {"experience_id": exp_id}


@router.get("/replay/sample")
async def sample_experiences(
    batch_size: int = Query(32),
    department: Optional[str] = None,
    task_type: Optional[str] = None
):
    dept_filter = [department] if department else None
    experiences, indices, weights = replay_buffer.sample(
        batch_size=batch_size,
        department_filter=dept_filter,
        task_type_filter=task_type,
    )
    
    return {
        "experiences": [e.to_dict() for e in experiences],
        "indices": indices,
        "weights": weights,
    }


@router.get("/replay/stats")
async def get_replay_stats():
    return replay_buffer.get_stats()


@router.post("/federated/register-node")
async def register_federated_node(request: RegisterNodeRequest):
    success = federated_learner.register_node(
        node_id=request.node_id,
        name=request.name,
        data_size=request.data_size,
    )
    return {"success": success}


@router.post("/federated/receive-update")
async def receive_federated_update(request: ReceiveUpdateRequest):
    update_id = federated_learner.receive_update(
        node_id=request.node_id,
        parameters=request.parameters,
        num_samples=request.num_samples,
        metrics=request.metrics,
    )
    return {"update_id": update_id}


@router.post("/federated/run-round")
async def run_federated_round():
    result = await federated_learner.run_round()
    return result


@router.get("/federated/nodes")
async def get_federated_nodes():
    return {"nodes": federated_learner.get_all_nodes()}


@router.get("/federated/stats")
async def get_federated_stats():
    return federated_learner.get_stats()


@router.post("/privacy/mask")
async def mask_data(request: MaskDataRequest):
    strategy = None
    if request.strategy:
        try:
            strategy = MaskStrategy(request.strategy)
        except ValueError:
            pass
    
    entity_types = None
    if request.entity_types:
        entity_types = []
        for et in request.entity_types:
            try:
                entity_types.append(EntityType(et))
            except ValueError:
                pass
    
    masked_text, entities = data_masker.mask(
        text=request.text,
        strategy=strategy,
        entity_types=entity_types,
    )
    
    return {
        "masked_text": masked_text,
        "entities": [e.to_dict() for e in entities],
        "entity_count": len(entities),
    }


@router.post("/privacy/reversible-mask")
async def reversible_mask(
    value: str,
    entity_type: str,
    context: str = ""
):
    masked = reversible_masker.mask_with_key(value, entity_type, context)
    return {"masked_value": masked}


@router.post("/privacy/unmask")
async def unmask_value(
    token: str,
    entity_type: Optional[str] = None
):
    original = reversible_masker.unmask(token, entity_type)
    if original is None:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"original_value": original}


@router.get("/privacy/stats")
async def get_privacy_stats():
    return data_masker.get_stats()


@router.post("/event/log")
async def log_event(request: LogEventRequest):
    try:
        event_type = EventType(request.event_type)
    except ValueError:
        event_type = EventType.SYSTEM
    
    record = event_logger.log_event(
        event_type=event_type,
        details=request.details,
        source_node=request.source_node,
        metadata=request.metadata,
    )
    
    return {"record": record.to_dict()}


@router.post("/event/log-attack")
async def log_attack_event(request: LogAttackRequest):
    record = event_logger.log_attack_event(
        attack_type=request.attack_type,
        source_ip=request.source_ip,
        target=request.target,
        defense_action=request.defense_action,
        result=request.result,
        details=request.details,
    )
    
    return {"record": record.to_dict()}


@router.get("/event/{record_id}")
async def get_event(record_id: str):
    record = event_logger.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"record": record.to_dict()}


@router.get("/event/{record_id}/verify")
async def verify_event(record_id: str):
    valid, errors = event_logger.verify_record(record_id)
    return {"valid": valid, "errors": errors}


@router.get("/event/type/{event_type}")
async def get_events_by_type(
    event_type: str,
    limit: int = Query(100)
):
    try:
        et = EventType(event_type)
    except ValueError:
        et = EventType.SYSTEM
    
    records = event_logger.get_events_by_type(et, limit)
    return {"records": [r.to_dict() for r in records]}


@router.get("/event/chain/export")
async def export_event_chain(
    start_seq: Optional[int] = None,
    end_seq: Optional[int] = None
):
    export = event_logger.export_chain(start_seq, end_seq)
    return export


@router.get("/event/stats")
async def get_event_stats():
    return event_logger.get_stats()


@router.get("/timestamp/info")
async def get_timestamp_info():
    return timestamp_service.get_time_info()


@router.post("/timestamp/issue")
async def issue_timestamp(request: IssueTimestampRequest):
    try:
        source = TimestampSource(request.source)
    except ValueError:
        source = TimestampSource.HYBRID
    
    token = await timestamp_service.issue_timestamp(request.data, source)
    return {"token": token.to_dict()}


@router.post("/timestamp/verify")
async def verify_timestamp(
    token_id: str,
    data: str
):
    valid, errors = timestamp_service.verify_timestamp(token_id, data)
    return {"valid": valid, "errors": errors}


@router.get("/timestamp/stats")
async def get_timestamp_stats():
    return timestamp_service.get_stats()


@router.post("/training/session/start")
async def start_training_session(request: StartTrainingSessionRequest):
    session_id = training_logger.start_session(
        model_name=request.model_name,
        hyperparams=request.hyperparams,
        training_data_hash=request.training_data_hash,
    )
    return {"session_id": session_id}


@router.post("/training/epoch/log")
async def log_training_epoch(request: LogEpochRequest):
    record = training_logger.log_epoch(
        session_id=request.session_id,
        epoch=request.epoch,
        train_loss=request.train_loss,
        val_loss=request.val_loss,
        accuracy=request.accuracy,
        learning_rate=request.learning_rate,
        model_params=request.model_params,
        metrics=request.metrics,
    )
    return {"record": record.to_dict()}


@router.post("/training/session/{session_id}/end")
async def end_training_session(
    session_id: str,
    status: str = "completed",
    final_metrics: Dict[str, float] = None
):
    try:
        phase = TrainingPhase(status)
    except ValueError:
        phase = TrainingPhase.COMPLETED
    
    training_logger.end_session(session_id, phase, final_metrics)
    return {"success": True}


@router.get("/training/session/{session_id}")
async def get_training_session(session_id: str):
    session = training_logger.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": session}


@router.get("/training/session/{session_id}/verify")
async def verify_training_session(session_id: str):
    valid, result = training_logger.verify_session(session_id)
    return {"valid": valid, "result": result}


@router.get("/training/session/{session_id}/loss-curve")
async def get_loss_curve(session_id: str):
    curve = training_logger.get_loss_curve(session_id)
    return curve


@router.get("/training/stats")
async def get_training_stats():
    return training_logger.get_stats()


@router.post("/model/register")
async def register_model_version(request: RegisterModelRequest):
    version = model_registry.register_version(
        model_name=request.model_name,
        version_number=request.version_number,
        model_params=request.model_params,
        training_session_id=request.training_session_id,
        training_data_hash=request.training_data_hash,
        hyperparams=request.hyperparams,
        metrics=request.metrics,
        parent_version=request.parent_version,
        metadata=request.metadata,
    )
    return {"version": version.to_dict()}


@router.post("/model/{version_id}/deploy")
async def deploy_model_version(version_id: str):
    success, version = model_registry.deploy_version(version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot deploy version")
    return {"success": True, "version": version.to_dict()}


@router.post("/model/{version_id}/validate")
async def validate_model_version(version_id: str):
    success = model_registry.validate_version(version_id)
    return {"success": success}


@router.post("/model/verify")
async def verify_deployed_model(request: VerifyModelRequest):
    valid, verification = model_registry.verify_deployed_model(
        model_name=request.model_name,
        current_params=request.current_params,
    )
    return {
        "valid": valid,
        "verification": verification.to_dict(),
    }


@router.get("/model/{model_name}/deployed")
async def get_deployed_model(model_name: str):
    version = model_registry.get_deployed_version(model_name)
    if not version:
        raise HTTPException(status_code=404, detail="No deployed version")
    return {"version": version.to_dict()}


@router.get("/model/{model_name}/versions")
async def get_model_versions(
    model_name: str,
    status: Optional[str] = None
):
    model_status = None
    if status:
        try:
            model_status = ModelStatus(status)
        except ValueError:
            pass
    
    versions = model_registry.get_model_versions(model_name, model_status)
    return {"versions": [v.to_dict() for v in versions]}


@router.post("/model/{model_name}/rollback")
async def rollback_model(
    model_name: str,
    target_version: Optional[str] = None,
    reason: str = "manual_rollback"
):
    success, version = model_registry.rollback_manager.rollback(
        model_name=model_name,
        target_version=target_version,
        reason=reason,
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Rollback failed")
    
    return {"success": True, "version": version.to_dict()}


@router.get("/model/{model_name}/history")
async def get_model_history(model_name: str):
    history = model_registry.export_model_history(model_name)
    return history


@router.get("/model/stats")
async def get_model_stats():
    return model_registry.get_stats()


@router.get("/system/status")
async def get_system_status():
    return {
        "lr_scheduler": {
            "status": "running",
            "stats": lr_scheduler.get_stats(),
        },
        "federated_learner": {
            "status": "running",
            "stats": federated_learner.get_stats(),
        },
        "event_logger": {
            "status": "running",
            "stats": event_logger.get_stats(),
        },
        "timestamp_service": {
            "status": "running",
            "stats": timestamp_service.get_stats(),
        },
        "training_logger": {
            "status": "running",
            "stats": training_logger.get_stats(),
        },
        "model_registry": {
            "status": "running",
            "stats": model_registry.get_stats(),
        },
        "timestamp": datetime.now().isoformat(),
    }
