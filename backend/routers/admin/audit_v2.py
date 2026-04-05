"""
管理员合规审计 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import io
import csv
import json
import uuid

from ...auth import require_admin
from ...services.audit_service import audit_service, ActionType, ResourceType, AuditStatus
from ...services.audit_verification import audit_verification, VerificationStatus

router = APIRouter(prefix="/api/admin", tags=["audit-v2"])


class AuditLogResponse(BaseModel):
    id: str
    timestamp: str
    user_id: Optional[str]
    username: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    status: str
    error_message: Optional[str]
    hash: Optional[str]
    prev_hash: Optional[str]


class AnomalyResponse(BaseModel):
    id: str
    user_id: Optional[str]
    username: Optional[str]
    anomaly_type: str
    severity: str
    description: Optional[str]
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    created_at: str


class ChainVerificationResponse(BaseModel):
    valid: bool
    checked: int
    errors: List[dict]


@router.get("/audit/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    admin_user: dict = Depends(require_admin)
):
    """获取审计日志列表"""
    logs = audit_service.get_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return logs


@router.get("/audit/logs/export")
async def export_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = "csv",
    admin_user: dict = Depends(require_admin)
):
    """导出审计日志"""
    content = audit_service.export_logs(
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"
    
    if format == "csv":
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


@router.get("/audit/stats")
async def get_audit_stats(
    days: int = Query(30, le=365),
    admin_user: dict = Depends(require_admin)
):
    """获取审计统计"""
    return audit_service.get_stats(days=days)


class VerificationResponse(BaseModel):
    status: str
    summary: Dict[str, Any]
    verification_time: str
    duration_ms: float
    errors: Dict[str, List[Dict[str, Any]]]
    integrity_score: float
    recommendations: List[str]


@router.post("/audit/verify", response_model=VerificationResponse)
async def verify_audit_chain(
    background_tasks: BackgroundTasks,
    limit: int = Query(10000, le=100000),
    verify_signatures: bool = Query(True),
    save_record: bool = Query(True),
    admin_user: dict = Depends(require_admin)
):
    """验证审计日志哈希链完整性"""
    result = await audit_verification.verify_chain(
        limit=limit,
        verify_signatures=verify_signatures
    )
    
    total_errors = len(result.hash_errors) + len(result.chain_errors) + len(result.signature_errors)
    integrity_score = 100.0 if result.total_logs == 0 else max(0, 100 - (total_errors / result.total_logs * 100))
    
    return VerificationResponse(
        status=result.status.value,
        summary={
            "total_logs": result.total_logs,
            "verified_logs": result.verified_logs,
            "hash_errors": len(result.hash_errors),
            "chain_errors": len(result.chain_errors),
            "signature_errors": len(result.signature_errors)
        },
        verification_time=result.verification_time.isoformat(),
        duration_ms=result.duration_ms,
        errors={
            "hash_errors": result.hash_errors[:10],
            "chain_errors": result.chain_errors[:10],
            "signature_errors": result.signature_errors[:10]
        },
        integrity_score=integrity_score,
        recommendations=[] if integrity_score >= 99 else ["建议检查错误日志并重新签名"]
    )


@router.post("/audit/sign")
async def sign_audit_logs(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(100, ge=10, le=1000),
    admin_user: dict = Depends(require_admin)
):
    """签名未处理的审计日志"""
    signed_count = await audit_verification.sign_unbatched_logs(batch_size)
    
    return {
        "message": f"成功签名 {signed_count} 条日志",
        "signed_count": signed_count
    }


@router.get("/audit/signatures")
async def get_signature_batches(
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin_user: dict = Depends(require_admin)
):
    """获取签名批次列表"""
    return {"batches": [], "total": 0}


@router.get("/audit/verifications")
async def get_verification_history(
    limit: int = Query(20, le=100),
    offset: int = 0,
    admin_user: dict = Depends(require_admin)
):
    """获取验证历史记录"""
    return {"records": [], "total": 0}


@router.get("/audit/verify/quick")
async def quick_verify_audit_chain(
    admin_user: dict = Depends(require_admin)
):
    """快速验证审计日志完整性"""
    result = await audit_verification.verify_chain(
        limit=1000,
        verify_signatures=True
    )
    
    total_errors = len(result.hash_errors) + len(result.chain_errors) + len(result.signature_errors)
    integrity_score = 100.0 if result.total_logs == 0 else max(0, 100 - (total_errors / max(result.total_logs, 1) * 100))
    
    return {
        "status": result.status.value,
        "total_logs": result.total_logs,
        "verified_logs": result.verified_logs,
        "has_errors": len(result.hash_errors) > 0 or len(result.chain_errors) > 0,
        "integrity_score": integrity_score
    }


@router.get("/audit/anomalies", response_model=List[AnomalyResponse])
async def get_audit_anomalies(
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    admin_user: dict = Depends(require_admin)
):
    """获取异常行为列表"""
    return audit_service.get_anomalies(
        is_resolved=is_resolved,
        severity=severity,
        limit=limit,
        offset=offset,
    )


@router.post("/audit/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: str,
    admin_user: dict = Depends(require_admin)
):
    """标记异常为已处理"""
    success = audit_service.resolve_anomaly(
        anomaly_id=anomaly_id,
        resolved_by=admin_user["id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="异常记录不存在"
        )
    
    return {"message": "已标记为已处理"}


@router.get("/audit/action-types")
async def get_action_types(
    admin_user: dict = Depends(require_admin)
):
    """获取所有操作类型"""
    return {
        "types": [
            {"value": t.value, "label": t.name}
            for t in ActionType
        ]
    }


@router.get("/audit/resource-types")
async def get_resource_types(
    admin_user: dict = Depends(require_admin)
):
    """获取所有资源类型"""
    return {
        "types": [
            {"value": t.value, "label": t.name}
            for t in ResourceType
        ]
    }


@router.get("/audit/users/{user_id}")
async def get_user_audit_history(
    user_id: str,
    limit: int = Query(100, le=500),
    admin_user: dict = Depends(require_admin)
):
    """获取指定用户的审计历史"""
    logs = audit_service.get_logs(
        user_id=user_id,
        limit=limit
    )
    
    return {
        "user_id": user_id,
        "logs": logs,
        "total": len(logs)
    }
