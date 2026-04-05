"""
管理员审计日志归档API
提供归档管理、恢复、验证功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import json

from ...auth import require_admin, require_super_admin
from ...database import get_db_connection
from ...exceptions import NotFoundException, BadRequestException, ErrorCode
from ...tasks.archive_audit_logs import (
    AuditArchiveConfig,
    AuditArchiver,
    audit_archiver,
    run_archive_task,
)

router = APIRouter(prefix="/api/admin/audit/archives", tags=["admin-audit-archives"])


class ArchiveResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int
    compressed_size: int
    start_timestamp: str
    end_timestamp: str
    log_count: int
    first_log_id: Optional[str]
    last_log_id: Optional[str]
    checksum: Optional[str]
    storage_type: str
    retention_days: int
    archived_at: str
    status: str


class ArchiveListResponse(BaseModel):
    archives: List[ArchiveResponse]
    total: int
    total_size: int
    total_logs: int


class ArchiveConfigResponse(BaseModel):
    enabled: bool
    retention_days: int
    archive_after_days: int
    schedule_cron: str
    storage_type: str
    storage_path: str
    compress_format: str
    max_archive_size_mb: int
    last_run_at: Optional[str]
    next_run_at: Optional[str]


class ArchiveConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    retention_days: Optional[int] = Field(None, ge=30, le=3650)
    archive_after_days: Optional[int] = Field(None, ge=30, le=3650)
    storage_path: Optional[str] = None
    max_archive_size_mb: Optional[int] = Field(None, ge=10, le=1000)


class ArchiveVerifyResponse(BaseModel):
    valid: bool
    log_count: int
    expected_count: int
    checksum_valid: bool
    chain_valid: bool
    chain_errors: List[Dict[str, Any]]
    error: Optional[str] = None


@router.get("", response_model=ArchiveListResponse)
async def list_archives(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    admin: dict = Depends(require_admin),
):
    """获取归档文件列表"""
    conn = await get_db_connection()
    try:
        where_clause = "WHERE status = ?" if status else ""
        params = [status] if status else []
        
        cursor = await conn.execute(f"""
            SELECT * FROM audit_archives
            {where_clause}
            ORDER BY archived_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        archives = await cursor.fetchall()
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as count FROM audit_archives {where_clause}",
            params
        )
        total = (await count_cursor.fetchone())["count"]
        
        stats_cursor = await conn.execute("""
            SELECT 
                COALESCE(SUM(compressed_size), 0) as total_size,
                COALESCE(SUM(log_count), 0) as total_logs
            FROM audit_archives
        """)
        stats = await stats_cursor.fetchone()
        
        return ArchiveListResponse(
            archives=[
                ArchiveResponse(
                    id=a["id"],
                    filename=a["filename"],
                    file_path=a["file_path"],
                    file_size=a["file_size"],
                    compressed_size=a["compressed_size"],
                    start_timestamp=a["start_timestamp"],
                    end_timestamp=a["end_timestamp"],
                    log_count=a["log_count"],
                    first_log_id=a.get("first_log_id"),
                    last_log_id=a.get("last_log_id"),
                    checksum=a.get("checksum"),
                    storage_type=a["storage_type"],
                    retention_days=a["retention_days"],
                    archived_at=a["archived_at"],
                    status=a["status"],
                )
                for a in archives
            ],
            total=total,
            total_size=stats["total_size"],
            total_logs=stats["total_logs"],
        )
    finally:
        await conn.close()


@router.get("/config", response_model=ArchiveConfigResponse)
async def get_archive_config(
    admin: dict = Depends(require_admin),
):
    """获取归档配置"""
    config = await AuditArchiveConfig.load()
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT last_run_at FROM audit_archive_config WHERE id = 'default'"
        )
        row = await cursor.fetchone()
        last_run = row["last_run_at"] if row else None
    finally:
        await conn.close()
    
    return ArchiveConfigResponse(
        enabled=config.enabled,
        retention_days=config.retention_days,
        archive_after_days=config.archive_after_days,
        schedule_cron=config.schedule_cron,
        storage_type=config.storage_type,
        storage_path=config.storage_path,
        compress_format=config.compress_format,
        max_archive_size_mb=config.max_archive_size_mb,
        last_run_at=last_run,
        next_run_at=None,
    )


@router.put("/config", response_model=ArchiveConfigResponse)
async def update_archive_config(
    update_data: ArchiveConfigUpdate,
    request: Request,
    admin: dict = Depends(require_super_admin),
):
    """更新归档配置（仅超级管理员）"""
    config = await AuditArchiveConfig.load()
    
    if update_data.enabled is not None:
        config.enabled = update_data.enabled
    if update_data.retention_days is not None:
        config.retention_days = update_data.retention_days
    if update_data.archive_after_days is not None:
        config.archive_after_days = update_data.archive_after_days
    if update_data.storage_path is not None:
        config.storage_path = update_data.storage_path
    if update_data.max_archive_size_mb is not None:
        config.max_archive_size_mb = update_data.max_archive_size_mb
    
    await config.save(admin["id"])
    
    return await get_archive_config(admin)


@router.post("/run")
async def run_archive_now(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(require_super_admin),
):
    """立即执行归档任务（仅超级管理员）"""
    background_tasks.add_task(run_archive_task)
    
    return {"message": "归档任务已启动"}


@router.get("/{archive_id}", response_model=ArchiveResponse)
async def get_archive_detail(
    archive_id: str,
    admin: dict = Depends(require_admin),
):
    """获取归档详情"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM audit_archives WHERE id = ?",
            (archive_id,)
        )
        archive = await cursor.fetchone()
        
        if not archive:
            raise NotFoundException("归档文件不存在", ErrorCode.NOT_FOUND)
        
        a = dict(archive)
        return ArchiveResponse(
            id=a["id"],
            filename=a["filename"],
            file_path=a["file_path"],
            file_size=a["file_size"],
            compressed_size=a["compressed_size"],
            start_timestamp=a["start_timestamp"],
            end_timestamp=a["end_timestamp"],
            log_count=a["log_count"],
            first_log_id=a.get("first_log_id"),
            last_log_id=a.get("last_log_id"),
            checksum=a.get("checksum"),
            storage_type=a["storage_type"],
            retention_days=a["retention_days"],
            archived_at=a["archived_at"],
            status=a["status"],
        )
    finally:
        await conn.close()


@router.get("/{archive_id}/download")
async def download_archive(
    archive_id: str,
    admin: dict = Depends(require_admin),
):
    """下载归档文件"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM audit_archives WHERE id = ?",
            (archive_id,)
        )
        archive = await cursor.fetchone()
        
        if not archive:
            raise NotFoundException("归档文件不存在", ErrorCode.NOT_FOUND)
        
        file_path = archive["file_path"]
        
        if not os.path.exists(file_path):
            raise NotFoundException("归档文件已丢失", ErrorCode.NOT_FOUND)
        
        return FileResponse(
            file_path,
            filename=archive["filename"],
            media_type="application/gzip",
        )
    finally:
        await conn.close()


@router.post("/{archive_id}/restore")
async def restore_archive(
    archive_id: str,
    admin: dict = Depends(require_super_admin),
):
    """恢复归档日志（仅超级管理员）"""
    result = await audit_archiver.restore_archive(archive_id, admin["id"])
    
    if result["status"] == "failed":
        raise BadRequestException(result.get("error", "恢复失败"), ErrorCode.OPERATION_FAILED)
    
    return result


@router.post("/{archive_id}/verify", response_model=ArchiveVerifyResponse)
async def verify_archive(
    archive_id: str,
    admin: dict = Depends(require_admin),
):
    """验证归档完整性"""
    result = await audit_archiver.verify_archive(archive_id)
    
    return ArchiveVerifyResponse(
        valid=result.get("valid", False),
        log_count=result.get("log_count", 0),
        expected_count=result.get("expected_count", 0),
        checksum_valid=result.get("checksum_valid", False),
        chain_valid=result.get("chain_valid", False),
        chain_errors=result.get("chain_errors", []),
        error=result.get("error"),
    )


@router.delete("/{archive_id}")
async def delete_archive(
    archive_id: str,
    admin: dict = Depends(require_super_admin),
):
    """删除归档文件（仅超级管理员）"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM audit_archives WHERE id = ?",
            (archive_id,)
        )
        archive = await cursor.fetchone()
        
        if not archive:
            raise NotFoundException("归档文件不存在", ErrorCode.NOT_FOUND)
        
        file_path = archive["file_path"]
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        await conn.execute(
            "DELETE FROM audit_archives WHERE id = ?",
            (archive_id,)
        )
        await conn.commit()
        
        return {"message": "归档文件已删除", "archive_id": archive_id}
    finally:
        await conn.close()


@router.get("/stats/summary")
async def get_archive_stats(
    admin: dict = Depends(require_admin),
):
    """获取归档统计"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT 
                COUNT(*) as total_archives,
                COALESCE(SUM(log_count), 0) as total_logs,
                COALESCE(SUM(file_size), 0) as total_uncompressed_size,
                COALESCE(SUM(compressed_size), 0) as total_compressed_size,
                MIN(start_timestamp) as earliest_log,
                MAX(end_timestamp) as latest_log
            FROM audit_archives
        """)
        stats = await cursor.fetchone()
        
        return {
            "total_archives": stats["total_archives"],
            "total_logs": stats["total_logs"],
            "total_uncompressed_size": stats["total_uncompressed_size"],
            "total_compressed_size": stats["total_compressed_size"],
            "compression_ratio": (
                stats["total_compressed_size"] / stats["total_uncompressed_size"]
                if stats["total_uncompressed_size"] > 0 else 0
            ),
            "earliest_log": stats["earliest_log"],
            "latest_log": stats["latest_log"],
        }
    finally:
        await conn.close()
