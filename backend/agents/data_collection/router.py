"""
数据采集与知识蒸馏 API 路由
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-collection", tags=["数据采集与知识蒸馏"])


class SampleCreateRequest(BaseModel):
    type: str
    content: Dict[str, Any]
    tags: List[str] = Field(default_factory=list)
    quality: float = 0.5
    source_agent_id: str = "api"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SampleQueryRequest(BaseModel):
    types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    min_quality: float = 0.0
    max_quality: float = 1.0
    limit: int = 100
    offset: int = 0


class CollectionTaskRequest(BaseModel):
    collector_type: str
    source_config: Dict[str, Any]
    data_type: str
    priority: str = "normal"


class DistillationRequest(BaseModel):
    sample_type: str
    method: str = "response_distillation"
    batch_size: int = 100
    config: Optional[Dict[str, Any]] = None


class KnowledgeTransferRequest(BaseModel):
    teacher_agent_id: str
    knowledge_form: str
    requirements: Optional[Dict[str, Any]] = None
    offered_reward: float = 10.0


class DemandRequest(BaseModel):
    data_type: str
    quantity: int = 100
    required_quality: float = 0.5
    urgency: str = "medium"
    requirements: Optional[Dict[str, Any]] = None


class ComplianceCheckRequest(BaseModel):
    source_config: Dict[str, Any]
    content: Optional[str] = None


class PrivacyProtectRequest(BaseModel):
    sample: Dict[str, Any]
    privacy_level: str = "internal"


_data_collection_system: Optional[Any] = None


def get_data_collection_system():
    global _data_collection_system
    if _data_collection_system is None:
        from . import SampleRepository, SampleQualityAssessor
        _data_collection_system = {
            "sample_repository": SampleRepository(),
            "quality_assessor": SampleQualityAssessor(),
        }
    return _data_collection_system


@router.post("/samples", summary="创建样本")
async def create_sample(
    request: SampleCreateRequest,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import SampleRepository, SampleType, SampleStatus
        from datetime import datetime
        import uuid
        
        repo = system.get("sample_repository")
        if not repo:
            raise HTTPException(status_code=500, detail="Sample repository not initialized")
        
        sample_data = {
            "id": str(uuid.uuid4()),
            "type": request.type,
            "content": request.content,
            "tags": request.tags,
            "quality": request.quality,
            "source_agent_id": request.source_agent_id,
            "metadata": request.metadata,
            "created_at": datetime.now()
        }
        
        sample_id = await repo.store(sample_data)
        
        return {
            "success": True,
            "sample_id": sample_id,
            "message": "Sample created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/samples/{sample_id}", summary="获取样本")
async def get_sample(
    sample_id: str,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        repo = system.get("sample_repository")
        if not repo:
            raise HTTPException(status_code=500, detail="Sample repository not initialized")
        
        sample = await repo.get(sample_id)
        
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        return {
            "success": True,
            "sample": sample.dict() if hasattr(sample, 'dict') else sample
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/samples/query", summary="查询样本")
async def query_samples(
    request: SampleQueryRequest,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import SampleQuery, SampleType
        
        repo = system.get("sample_repository")
        if not repo:
            raise HTTPException(status_code=500, detail="Sample repository not initialized")
        
        types = [SampleType(t) for t in request.types] if request.types else None
        
        query = SampleQuery(
            types=types,
            tags=request.tags,
            min_quality=request.min_quality,
            max_quality=request.max_quality,
            limit=request.limit,
            offset=request.offset
        )
        
        samples = await repo.query(query)
        
        return {
            "success": True,
            "count": len(samples),
            "samples": [s.dict() if hasattr(s, 'dict') else s for s in samples]
        }
    except Exception as e:
        logger.error(f"Error querying samples: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/samples/{sample_id}", summary="删除样本")
async def delete_sample(
    sample_id: str,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        repo = system.get("sample_repository")
        if not repo:
            raise HTTPException(status_code=500, detail="Sample repository not initialized")
        
        success = await repo.delete(sample_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        return {
            "success": True,
            "message": f"Sample {sample_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/samples/statistics", summary="获取样本统计")
async def get_sample_statistics(
    system: Dict = Depends(get_data_collection_system)
):
    try:
        repo = system.get("sample_repository")
        if not repo:
            raise HTTPException(status_code=500, detail="Sample repository not initialized")
        
        stats = await repo.get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/assess", summary="评估样本质量")
async def assess_sample_quality(
    sample: Dict[str, Any],
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import SampleForAssessment
        
        assessor = system.get("quality_assessor")
        if not assessor:
            raise HTTPException(status_code=500, detail="Quality assessor not initialized")
        
        sample_for_assessment = SampleForAssessment(
            id=sample.get("id", "unknown"),
            type=sample.get("type", "text"),
            content=sample.get("content", {}),
            metadata=sample.get("metadata", {}),
            created_at=sample.get("created_at", datetime.now()),
            tags=sample.get("tags", [])
        )
        
        quality_score = await assessor.assess(sample_for_assessment)
        
        return {
            "success": True,
            "quality_score": quality_score.dict()
        }
    except Exception as e:
        logger.error(f"Error assessing quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/distillation/execute", summary="执行知识蒸馏")
async def execute_distillation(
    request: DistillationRequest,
    background_tasks: BackgroundTasks,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import KnowledgeDistillerAgent, DistillationMethod
        
        distiller = KnowledgeDistillerAgent(
            agent_id="api_distiller",
            sample_repository=system.get("sample_repository")
        )
        
        method = DistillationMethod(request.method)
        
        async def run_distillation():
            result = await distiller.execute_distillation_cycle(
                sample_type=request.sample_type,
                method=method,
                config=request.config
            )
            logger.info(f"Distillation completed: {result.id}")
        
        background_tasks.add_task(run_distillation)
        
        return {
            "success": True,
            "message": "Distillation task started in background",
            "method": request.method,
            "sample_type": request.sample_type
        }
    except Exception as e:
        logger.error(f"Error starting distillation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demand/create", summary="创建数据需求")
async def create_data_demand(
    request: DemandRequest,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import DataDemandSensor, DemandUrgency
        
        sensor = DataDemandSensor(
            agent_id="api",
            sample_repository=system.get("sample_repository")
        )
        
        urgency = DemandUrgency(request.urgency)
        
        demand = await sensor.create_demand(
            data_type=request.data_type,
            quantity=request.quantity,
            required_quality=request.required_quality,
            urgency=urgency,
            requirements=request.requirements
        )
        
        return {
            "success": True,
            "demand_id": demand.demand_id,
            "message": "Data demand created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating demand: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand/heatmap", summary="获取需求热力图")
async def get_demand_heatmap(
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import DataDemandSensor
        
        sensor = DataDemandSensor(
            agent_id="api",
            sample_repository=system.get("sample_repository")
        )
        
        heatmap = await sensor.get_demand_heat_map()
        
        return {
            "success": True,
            "heatmap": [h.dict() for h in heatmap]
        }
    except Exception as e:
        logger.error(f"Error getting heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/check", summary="合规检查")
async def check_compliance(
    request: ComplianceCheckRequest,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import DataCollectionComplianceChecker
        
        checker = DataCollectionComplianceChecker()
        
        result = await checker.check_collection(
            agent_id="api",
            source_config=request.source_config,
            content=request.content
        )
        
        return {
            "success": True,
            "status": result.status.value,
            "violations": [v.dict() for v in result.violations],
            "warnings": result.warnings
        }
    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/protect", summary="隐私保护处理")
async def protect_sample_privacy(
    request: PrivacyProtectRequest,
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import SamplePrivacyProtector, PrivacyLevel
        
        protector = SamplePrivacyProtector(
            sample_repository=system.get("sample_repository")
        )
        
        privacy_level = PrivacyLevel(request.privacy_level)
        
        protected_sample = await protector.protect_sample(
            request.sample,
            privacy_level
        )
        
        return {
            "success": True,
            "protected_sample": protected_sample
        }
    except Exception as e:
        logger.error(f"Error protecting privacy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution/statistics", summary="获取进化统计")
async def get_evolution_statistics(
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import SampleDrivenEvolution
        
        evolution = SampleDrivenEvolution(
            sample_repository=system.get("sample_repository")
        )
        
        stats = evolution.get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting evolution statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution/leaderboard", summary="获取进化排行榜")
async def get_evolution_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    system: Dict = Depends(get_data_collection_system)
):
    try:
        from . import SampleDrivenEvolution
        
        evolution = SampleDrivenEvolution(
            sample_repository=system.get("sample_repository")
        )
        
        leaderboard = evolution.get_leaderboard(limit)
        
        return {
            "success": True,
            "leaderboard": leaderboard
        }
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="健康检查")
async def health_check():
    return {
        "status": "healthy",
        "module": "data_collection",
        "timestamp": datetime.now().isoformat()
    }
