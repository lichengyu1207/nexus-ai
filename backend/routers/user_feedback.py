"""
用户反馈和举报 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import logging
import json

from backend.auth import get_current_user, require_admin
from ..database import UserFeedbackDB, ContentReportDB, PrivacyConsentDB, PrivacyPolicyDB, NotificationDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feedback-reports"])


class FeedbackCreate(BaseModel):
    type: str = Field(..., description="类型: feedback/suggestion/bug/complaint")
    title: Optional[str] = Field(None, max_length=100)
    content: str = Field(..., min_length=10, max_length=2000)
    attachments: Optional[List[str]] = None


class FeedbackReply(BaseModel):
    status: str = Field(..., description="状态: pending/processing/resolved/rejected")
    admin_reply: Optional[str] = Field(None, max_length=2000)


class ReportCreate(BaseModel):
    reported_type: str = Field(..., description="举报类型: report/comment/user")
    reported_id: str = Field(..., description="被举报内容ID")
    reason: str = Field(..., description="举报原因")
    details: Optional[str] = Field(None, max_length=1000)
    evidence: Optional[List[str]] = None


class ReportProcess(BaseModel):
    status: str = Field(..., description="状态: pending/investigating/resolved/dismissed")
    admin_notes: Optional[str] = None
    action_taken: Optional[str] = None


class PrivacyConsentCreate(BaseModel):
    policy_version: Optional[str] = None
    policy_title: Optional[str] = None


@router.post("/feedback")
async def create_feedback(
    data: FeedbackCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """提交用户反馈"""
    valid_types = ["feedback", "suggestion", "bug", "complaint"]
    if data.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效类型，可选: {valid_types}")
    
    feedback_id = str(uuid.uuid4())
    
    result = await UserFeedbackDB.create_feedback(
        feedback_id=feedback_id,
        user_id=current_user["id"],
        type=data.type,
        content=data.content,
        title=data.title,
        attachments=data.attachments
    )
    
    logger.info(f"User {current_user['id']} submitted feedback {feedback_id}")
    
    return {"message": "反馈提交成功", "id": feedback_id, "data": result}


@router.get("/feedback/my")
async def get_my_feedbacks(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """获取我的反馈列表"""
    feedbacks = await UserFeedbackDB.get_user_feedbacks(current_user["id"], limit)
    return {"items": feedbacks, "total": len(feedbacks)}


@router.get("/feedback/{feedback_id}")
async def get_feedback_detail(
    feedback_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取反馈详情"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    if feedback["user_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="无权访问")
    
    return feedback


@router.get("/feedback/types")
async def get_feedback_types():
    """获取反馈类型列表"""
    return {"types": UserFeedbackDB.FEEDBACK_TYPES}


@router.post("/reports")
async def create_report(
    data: ReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """提交举报"""
    valid_types = ["report", "comment", "user"]
    if data.reported_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效类型，可选: {valid_types}")
    
    already_reported = await ContentReportDB.check_user_reported(
        current_user["id"], data.reported_type, data.reported_id
    )
    if already_reported:
        raise HTTPException(status_code=400, detail="您已举报过该内容")
    
    report_id = str(uuid.uuid4())
    
    result = await ContentReportDB.create_report(
        report_id=report_id,
        reporter_id=current_user["id"],
        reported_type=data.reported_type,
        reported_id=data.reported_id,
        reason=data.reason,
        details=data.details,
        evidence=data.evidence
    )
    
    logger.info(f"User {current_user['id']} submitted report {report_id}")
    
    return {"message": "举报提交成功", "id": report_id, "data": result}


@router.get("/reports/my")
async def get_my_reports(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """获取我的举报列表"""
    reports = await ContentReportDB.get_user_reports(current_user["id"], limit)
    return {"items": reports, "total": len(reports)}


@router.get("/reports/reasons")
async def get_report_reasons():
    """获取举报原因列表"""
    return {"reasons": ContentReportDB.REASON_OPTIONS}


@router.post("/privacy/consent")
async def agree_privacy_policy(
    data: PrivacyConsentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """同意隐私政策"""
    consent_id = str(uuid.uuid4())
    
    result = await PrivacyConsentDB.record_consent(
        consent_id=consent_id,
        user_id=current_user["id"],
        policy_version=data.policy_version,
        policy_title=data.policy_title,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info(f"User {current_user['id']} agreed to privacy policy v{result['policy_version']}")
    
    return {"message": "已同意隐私政策", "data": result}


@router.get("/privacy/current")
async def get_current_privacy_policy():
    """获取当前生效的隐私政策"""
    policy = await PrivacyPolicyDB.get_current_policy()
    if not policy:
        raise HTTPException(status_code=404, detail="隐私政策不存在")
    return policy


@router.get("/privacy/status")
async def get_privacy_status(current_user: dict = Depends(get_current_user)):
    """获取用户隐私政策同意状态"""
    current_policy = await PrivacyPolicyDB.get_current_policy()
    current_version = current_policy["version"] if current_policy else "1.0.0"
    
    agreed = await PrivacyConsentDB.check_user_agreed_latest(current_user["id"])
    latest_consent = await PrivacyConsentDB.get_user_latest_consent(current_user["id"])
    
    return {
        "agreed_latest": agreed,
        "current_version": current_version,
        "latest_consent": latest_consent,
        "needs_consent": not agreed
    }


@router.get("/privacy/info")
async def get_privacy_info():
    """获取隐私政策信息"""
    policy = await PrivacyPolicyDB.get_current_policy()
    if policy:
        return {
            "version": policy["version"],
            "title": policy.get("title", "房都督AI隐私政策"),
            "effective_date": policy.get("effective_date")
        }
    return {
        "version": "1.0.0",
        "title": "房都督AI隐私政策"
    }


# ============ 管理员 API ============

@router.get("/admin/feedback")
async def admin_list_feedbacks(
    status: str = None,
    type: str = None,
    limit: int = 50,
    offset: int = 0,
    admin: dict = Depends(require_admin)
):
    """管理员获取反馈列表"""
    feedbacks, total = await UserFeedbackDB.get_all_feedbacks(
        status=status, type=type, limit=limit, offset=offset
    )
    return {"items": feedbacks, "total": total}


@router.get("/admin/feedback/stats")
async def admin_get_feedback_stats(admin: dict = Depends(require_admin)):
    """管理员获取反馈统计"""
    stats = await UserFeedbackDB.get_feedback_stats()
    return stats


@router.put("/admin/feedback/{feedback_id}")
async def admin_reply_feedback(
    feedback_id: str,
    data: FeedbackReply,
    admin: dict = Depends(require_admin)
):
    """管理员回复反馈"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    valid_statuses = ["pending", "processing", "resolved", "rejected"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")
    
    success = await UserFeedbackDB.update_feedback_status(
        feedback_id=feedback_id,
        status=data.status,
        admin_reply=data.admin_reply,
        replied_by=admin["id"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    if data.admin_reply:
        await NotificationDB.create_notification(
            notification_id=str(uuid.uuid4()),
            user_id=feedback["user_id"],
            notification_type="feedback_reply",
            content=f"您的反馈已收到回复：{data.admin_reply[:50]}...",
            related_id=feedback_id,
            related_type="feedback",
            title="反馈回复通知"
        )
    
    logger.info(f"Admin {admin['id']} replied to feedback {feedback_id}")
    
    return {"message": "回复成功"}


@router.get("/admin/reports")
async def admin_list_reports(
    status: str = None,
    reported_type: str = None,
    limit: int = 50,
    offset: int = 0,
    admin: dict = Depends(require_admin)
):
    """管理员获取举报列表"""
    reports, total = await ContentReportDB.get_all_reports(
        status=status, reported_type=reported_type, limit=limit, offset=offset
    )
    return {"items": reports, "total": total}


@router.get("/admin/reports/stats")
async def admin_get_report_stats(admin: dict = Depends(require_admin)):
    """管理员获取举报统计"""
    stats = await ContentReportDB.get_report_stats()
    return stats


@router.put("/admin/reports/{report_id}")
async def admin_process_report(
    report_id: str,
    data: ReportProcess,
    admin: dict = Depends(require_admin)
):
    """管理员处理举报"""
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
    
    await NotificationDB.create_notification(
        notification_id=str(uuid.uuid4()),
        user_id=report["reporter_id"],
        notification_type="report_update",
        content=f"您的举报已处理，状态：{data.status}",
        related_id=report_id,
        related_type="report",
        title="举报处理通知"
    )
    
    logger.info(f"Admin {admin['id']} processed report {report_id}")
    
    return {"message": "处理成功"}


@router.get("/admin/privacy/stats")
async def admin_get_privacy_stats(admin: dict = Depends(require_admin)):
    """管理员获取隐私政策统计"""
    stats = await PrivacyConsentDB.get_consent_stats()
    return stats
