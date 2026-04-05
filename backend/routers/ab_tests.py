"""
A/B 测试 API 路由
用于管理和查看 A/B 测试实验
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import logging

from backend.auth import get_current_user, require_admin
from ..database import ABTestDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ab-tests", tags=["ab-tests"])


class ExperimentCreate(BaseModel):
    """创建实验请求"""
    name: str = Field(..., description="实验名称")
    feature: str = Field(..., description="测试功能")
    description: Optional[str] = Field(None, description="实验描述")
    control_group: str = Field("control", description="对照组名称")
    experiment_group: str = Field("treatment", description="实验组名称")
    config: Optional[Dict[str, Any]] = Field(None, description="实验配置")


class MetricRecord(BaseModel):
    """记录指标请求"""
    experiment_id: str = Field(..., description="实验ID")
    metric_type: str = Field(..., description="指标类型")
    metric_value: Optional[float] = Field(None, description="指标值")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ExperimentResponse(BaseModel):
    """实验响应"""
    id: str
    name: str
    feature: str
    description: Optional[str]
    status: str
    control_group: str
    experiment_group: str
    start_date: Optional[str]
    end_date: Optional[str]
    config: Optional[Dict[str, Any]]


@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(
    experiment: ExperimentCreate,
    admin: dict = Depends(require_admin)
):
    """
    创建新的 A/B 测试实验
    
    Args:
        experiment: 实验配置
        admin: 管理员用户
        
    Returns:
        ExperimentResponse: 创建的实验
    """
    experiment_id = str(uuid.uuid4())
    
    result = await ABTestDB.create_experiment(
        experiment_id=experiment_id,
        name=experiment.name,
        feature=experiment.feature,
        description=experiment.description,
        control_group=experiment.control_group,
        experiment_group=experiment.experiment_group,
        config=experiment.config
    )
    
    logger.info(f"Admin {admin['id']} created experiment {experiment_id}")
    
    return ExperimentResponse(
        id=experiment_id,
        name=experiment.name,
        feature=experiment.feature,
        description=experiment.description,
        status="running",
        control_group=experiment.control_group,
        experiment_group=experiment.experiment_group,
        start_date=None,
        end_date=None,
        config=experiment.config
    )


@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    status: str = None,
    admin: dict = Depends(require_admin)
):
    """
    列出所有实验
    
    Args:
        status: 状态过滤
        admin: 管理员用户
        
    Returns:
        List[ExperimentResponse]: 实验列表
    """
    experiments = await ABTestDB.list_experiments(status)
    
    return [
        ExperimentResponse(
            id=exp["id"],
            name=exp["name"],
            feature=exp["feature"],
            description=exp.get("description"),
            status=exp["status"],
            control_group=exp["control_group"],
            experiment_group=exp["experiment_group"],
            start_date=exp.get("start_date"),
            end_date=exp.get("end_date"),
            config=exp.get("config")
        )
        for exp in experiments
    ]


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    admin: dict = Depends(require_admin)
):
    """
    获取实验详情
    
    Args:
        experiment_id: 实验ID
        admin: 管理员用户
        
    Returns:
        dict: 实验详情
    """
    experiment = await ABTestDB.get_experiment(experiment_id)
    
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    return experiment


@router.put("/experiments/{experiment_id}/status")
async def update_experiment_status(
    experiment_id: str,
    status: str,
    admin: dict = Depends(require_admin)
):
    """
    更新实验状态
    
    Args:
        experiment_id: 实验ID
        status: 新状态 (running/paused/completed)
        admin: 管理员用户
        
    Returns:
        dict: 操作结果
    """
    valid_statuses = ["running", "paused", "completed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选值: {valid_statuses}")
    
    success = await ABTestDB.update_experiment_status(experiment_id, status)
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    logger.info(f"Admin {admin['id']} updated experiment {experiment_id} to {status}")
    
    return {"message": "状态已更新", "experiment_id": experiment_id, "new_status": status}


@router.get("/experiments/{experiment_id}/stats")
async def get_experiment_stats(
    experiment_id: str,
    admin: dict = Depends(require_admin)
):
    """
    获取实验统计数据
    
    Args:
        experiment_id: 实验ID
        admin: 管理员用户
        
    Returns:
        dict: 统计数据
    """
    stats = await ABTestDB.get_experiment_stats(experiment_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    return stats


@router.get("/experiments/{experiment_id}/metrics")
async def get_experiment_metrics(
    experiment_id: str,
    admin: dict = Depends(require_admin)
):
    """
    获取实验指标列表
    
    Args:
        experiment_id: 实验ID
        admin: 管理员用户
        
    Returns:
        list: 指标列表
    """
    metrics = await ABTestDB.get_experiment_metrics(experiment_id)
    return metrics


@router.post("/metrics")
async def record_metric(
    metric: MetricRecord,
    current_user: dict = Depends(get_current_user)
):
    """
    记录用户行为指标
    
    Args:
        metric: 指标数据
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    experiment = await ABTestDB.get_experiment(metric.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    if experiment["status"] != "running":
        raise HTTPException(status_code=400, detail="实验未在运行中")
    
    user_group = await ABTestDB.get_user_group(current_user["id"])
    
    metric_id = str(uuid.uuid4())
    await ABTestDB.record_metric(
        metric_id=metric_id,
        experiment_id=metric.experiment_id,
        user_id=current_user["id"],
        group_name=user_group,
        metric_type=metric.metric_type,
        metric_value=metric.metric_value,
        metadata=metric.metadata
    )
    
    return {"message": "指标已记录", "metric_id": metric_id}


@router.get("/stats/overall")
async def get_overall_stats(
    admin: dict = Depends(require_admin)
):
    """
    获取整体 A/B 测试统计
    
    Args:
        admin: 管理员用户
        
    Returns:
        dict: 整体统计
    """
    stats = await ABTestDB.get_overall_stats()
    return stats


@router.get("/my-group")
async def get_my_group(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的 A/B 测试分组
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 用户分组信息
    """
    group = await ABTestDB.get_user_group(current_user["id"])
    
    return {
        "user_id": current_user["id"],
        "group": group
    }
