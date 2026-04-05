"""
管理员举报管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import logging

from ...auth import require_admin
from ...database import ContentReportDB, NotificationDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/reports", tags=["admin-reports"])


class ReportProcess(BaseModel):
    status: str = Field(..., description="状态: pending/investigating/resolved/dismissed")
    admin_notes: Optional[str] = Field(None, max_length=1000)
    action_taken: Optional[str] = Field(None, max_length=500)


@router.get("")
async def list_reports(
    status: str = Query(None),
    reported_type: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin)
):
    """获取举报列表"""
    reports, total = await ContentReportDB.get_all_reports(
        status=status, reported_type=reported_type, limit=limit, offset=offset
    )
    return {"items": reports, "total": total}


@router.get("/stats")
async def get_report_stats(admin: dict = Depends(require_admin)):
    """获取举报统计"""
    stats = await ContentReportDB.get_report_stats()
    return stats


@router.get("/{report_id}")
async def get_report_detail(
    report_id: str,
    admin: dict = Depends(require_admin)
):
    """获取举报详情"""
    report = await ContentReportDB.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="举报不存在")
    return report


@router.put("/{report_id}")
async def process_report(
    report_id: str,
    data: ReportProcess,
    admin: dict = Depends(require_admin)
):
    """处理举报"""
    report = await ContentReportDB.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="举报不存在")
    
    valid_statuses = ["pending", "investigating", "resolved", "dismissed"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")
    
    success = await ContentReportDB.update_report_status(
        report_id=report_id,
        status=data.status,
        admin_notes=data.admin_notes,
        action_taken=data.action_taken,
        processed_by=admin["id"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    status_messages = {
        "investigating": "您的举报正在调查中",
        "resolved": "您的举报已处理完成",
        "dismissed": "您的举报已被驳回"
    }
    
    if data.status in status_messages:
        await NotificationDB.create_notification(
            notification_id=str(uuid.uuid4()),
            user_id=report["reporter_id"],
            notification_type="report_update",
            content=status_messages[data.status],
            related_id=report_id,
            related_type="report",
            title="举报处理通知"
        )
    
    logger.info(f"Admin {admin['id']} processed report {report_id}")
    
    return {"message": "处理成功"}
