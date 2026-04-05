"""
FastAPI 路由
提供快照管理的 REST API
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .backup import BackupManager
from .config import SnapshotConfig
from .models import BackupResult, RestoreResult, SnapshotInfo
from .restore import RestoreManager
from .scheduler import SnapshotScheduler
from .storage import StorageBackend, create_storage_backend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/snapshot", tags=["snapshot"])

_config: Optional[SnapshotConfig] = None
_storage: Optional[StorageBackend] = None
_backup_manager: Optional[BackupManager] = None
_restore_manager: Optional[RestoreManager] = None
_scheduler: Optional[SnapshotScheduler] = None


def get_config() -> SnapshotConfig:
    """获取配置"""
    global _config
    if _config is None:
        _config = SnapshotConfig()
    return _config


def get_storage(config: SnapshotConfig = Depends(get_config)) -> StorageBackend:
    """获取存储后端"""
    global _storage
    if _storage is None:
        _storage = create_storage_backend(config)
    return _storage


def get_backup_manager(
    config: SnapshotConfig = Depends(get_config),
    storage: StorageBackend = Depends(get_storage)
) -> BackupManager:
    """获取备份管理器"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(config, storage)
    return _backup_manager


def get_restore_manager(
    config: SnapshotConfig = Depends(get_config),
    storage: StorageBackend = Depends(get_storage)
) -> RestoreManager:
    """获取恢复管理器"""
    global _restore_manager
    if _restore_manager is None:
        _restore_manager = RestoreManager(config, storage)
    return _restore_manager


def get_scheduler(
    config: SnapshotConfig = Depends(get_config),
    backup_manager: BackupManager = Depends(get_backup_manager)
) -> SnapshotScheduler:
    """获取调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SnapshotScheduler(config, backup_manager)
    return _scheduler


class CreateSnapshotRequest(BaseModel):
    """创建快照请求"""
    description: str = Field(default="", description="快照描述")


class CreateSnapshotResponse(BaseModel):
    """创建快照响应"""
    success: bool
    snapshot_id: Optional[str] = None
    filename: Optional[str] = None
    size_bytes: int = 0
    message: str = ""


class SnapshotInfoResponse(BaseModel):
    """快照信息响应"""
    filename: str
    created_at: str
    size_bytes: int
    description: str
    status: str
    created_by: str


class ListSnapshotsResponse(BaseModel):
    """列出快照响应"""
    snapshots: List[SnapshotInfoResponse]
    total: int


class RollbackRequest(BaseModel):
    """回滚请求"""
    confirm: bool = Field(default=False, description="确认执行回滚")


class RollbackResponse(BaseModel):
    """回滚响应"""
    success: bool
    status: str
    message: str
    services_restarted: List[str] = []


class RollbackStatusResponse(BaseModel):
    """回滚状态响应"""
    status: str
    current_step: str
    progress_percent: float
    error_message: str = ""


class VerifySnapshotResponse(BaseModel):
    """验证快照响应"""
    exists: bool
    downloadable: bool
    metadata: Optional[dict] = None
    error: Optional[str] = None


class SchedulerJobsResponse(BaseModel):
    """调度任务响应"""
    jobs: List[dict]


class TriggerResponse(BaseModel):
    """触发响应"""
    success: bool
    message: str


@router.post("/create", response_model=CreateSnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    background_tasks: BackgroundTasks,
    backup_manager: BackupManager = Depends(get_backup_manager)
) -> CreateSnapshotResponse:
    """
    创建快照
    
    手动触发创建系统状态快照
    """
    logger.info(f"收到创建快照请求: {request.description}")
    
    result = await backup_manager.create_snapshot(
        description=request.description,
        created_by="manual"
    )
    
    if result.success:
        return CreateSnapshotResponse(
            success=True,
            snapshot_id=result.filename.replace(".tar.gz", ""),
            filename=result.filename,
            size_bytes=result.size_bytes,
            message=f"快照创建成功，耗时 {result.duration_seconds:.2f} 秒"
        )
    else:
        return CreateSnapshotResponse(
            success=False,
            message=result.error_message
        )


@router.get("/list", response_model=ListSnapshotsResponse)
async def list_snapshots(
    backup_manager: BackupManager = Depends(get_backup_manager)
) -> ListSnapshotsResponse:
    """
    列出所有快照
    
    返回所有可用的快照列表
    """
    snapshots = await backup_manager.list_snapshots()
    
    snapshot_responses = [
        SnapshotInfoResponse(
            filename=s.filename,
            created_at=s.created_at.isoformat(),
            size_bytes=s.size_bytes,
            description=s.description,
            status=s.status.value,
            created_by=s.created_by
        )
        for s in snapshots
    ]
    
    return ListSnapshotsResponse(
        snapshots=snapshot_responses,
        total=len(snapshot_responses)
    )


@router.post("/rollback/{filename}", response_model=RollbackResponse)
async def rollback_snapshot(
    filename: str,
    request: RollbackRequest,
    background_tasks: BackgroundTasks,
    restore_manager: RestoreManager = Depends(get_restore_manager)
) -> RollbackResponse:
    """
    回滚到指定快照
    
    从指定快照恢复系统状态，此操作会停止服务并恢复数据
    """
    logger.info(f"收到回滚请求: {filename}, 确认: {request.confirm}")
    
    if restore_manager.is_restoring():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已有恢复任务在进行中"
        )
    
    result = await restore_manager.restore(filename, confirm=request.confirm)
    
    if result.success:
        return RollbackResponse(
            success=True,
            status="completed",
            message=f"系统已从快照 {filename} 恢复，耗时 {result.duration_seconds:.2f} 秒",
            services_restarted=result.services_restarted
        )
    else:
        return RollbackResponse(
            success=False,
            status="failed",
            message=result.error_message
        )


@router.get("/rollback/status", response_model=RollbackStatusResponse)
async def get_rollback_status(
    restore_manager: RestoreManager = Depends(get_restore_manager)
) -> RollbackStatusResponse:
    """
    获取回滚状态
    
    返回当前回滚任务的进度
    """
    progress = restore_manager.get_progress()
    
    if progress is None:
        return RollbackStatusResponse(
            status="idle",
            current_step="",
            progress_percent=0
        )
    
    progress_dict = progress.to_dict()
    return RollbackStatusResponse(
        status=progress_dict["status"],
        current_step=progress_dict["current_step"],
        progress_percent=progress_dict["progress_percent"],
        error_message=progress_dict["error_message"]
    )


@router.get("/verify/{filename}", response_model=VerifySnapshotResponse)
async def verify_snapshot(
    filename: str,
    restore_manager: RestoreManager = Depends(get_restore_manager)
) -> VerifySnapshotResponse:
    """
    验证快照
    
    检查快照是否存在、是否可下载、并获取元数据
    """
    result = await restore_manager.verify_snapshot(filename)
    return VerifySnapshotResponse(**result)


@router.delete("/{filename}")
async def delete_snapshot(
    filename: str,
    backup_manager: BackupManager = Depends(get_backup_manager)
) -> dict:
    """
    删除快照
    
    删除指定的快照文件
    """
    logger.info(f"收到删除快照请求: {filename}")
    
    from .storage import create_storage_backend
    config = get_config()
    storage = create_storage_backend(config)
    
    remote_path = config.get_snapshot_path(filename)
    
    if not await storage.exists(remote_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"快照不存在: {filename}"
        )
    
    success = await storage.delete(remote_path)
    
    if success:
        return {"success": True, "message": f"快照 {filename} 已删除"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除快照失败"
        )


@router.get("/scheduler/jobs", response_model=SchedulerJobsResponse)
async def get_scheduler_jobs(
    scheduler: SnapshotScheduler = Depends(get_scheduler)
) -> SchedulerJobsResponse:
    """
    获取调度任务列表
    
    返回所有已配置的定时任务
    """
    jobs = scheduler.get_jobs()
    return SchedulerJobsResponse(jobs=jobs)


@router.post("/scheduler/trigger/snapshot", response_model=TriggerResponse)
async def trigger_snapshot(
    scheduler: SnapshotScheduler = Depends(get_scheduler)
) -> TriggerResponse:
    """
    手动触发快照任务
    
    立即执行一次快照创建
    """
    success = scheduler.trigger_snapshot()
    
    if success:
        return TriggerResponse(success=True, message="快照任务已触发")
    else:
        return TriggerResponse(success=False, message="触发快照任务失败")


@router.post("/scheduler/trigger/cleanup", response_model=TriggerResponse)
async def trigger_cleanup(
    scheduler: SnapshotScheduler = Depends(get_scheduler)
) -> TriggerResponse:
    """
    手动触发清理任务
    
    立即执行一次旧快照清理
    """
    success = scheduler.trigger_cleanup()
    
    if success:
        return TriggerResponse(success=True, message="清理任务已触发")
    else:
        return TriggerResponse(success=False, message="触发清理任务失败")


@router.post("/scheduler/start")
async def start_scheduler(
    scheduler: SnapshotScheduler = Depends(get_scheduler)
) -> dict:
    """启动调度器"""
    scheduler.start()
    return {"success": True, "message": "调度器已启动"}


@router.post("/scheduler/stop")
async def stop_scheduler(
    scheduler: SnapshotScheduler = Depends(get_scheduler)
) -> dict:
    """停止调度器"""
    scheduler.stop()
    return {"success": True, "message": "调度器已停止"}


@router.get("/health")
async def health_check() -> dict:
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


def init_snapshot_module(
    config: SnapshotConfig,
    start_scheduler: bool = True
) -> None:
    """
    初始化快照模块
    
    Args:
        config: 配置对象
        start_scheduler: 是否启动调度器
    """
    global _config, _storage, _backup_manager, _restore_manager, _scheduler
    
    _config = config
    _storage = create_storage_backend(config)
    _backup_manager = BackupManager(config, _storage)
    _restore_manager = RestoreManager(config, _storage)
    _scheduler = SnapshotScheduler(config, _backup_manager)
    
    if start_scheduler:
        _scheduler.start()
    
    logger.info("快照模块初始化完成")


def shutdown_snapshot_module() -> None:
    """关闭快照模块"""
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()
    
    logger.info("快照模块已关闭")


def get_router() -> APIRouter:
    """获取路由器"""
    return router
