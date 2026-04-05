"""
审计日志API路由
提供用户操作日志的查询功能
"""
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

from ..auth import get_current_user
from ..database import AuditDB

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


class AuditLogResponse(BaseModel):
    """审计日志响应模型"""
    id: str
    user_id: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: Optional[str]
    email: Optional[str] = None
    full_name: Optional[str] = None


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    logs: List[AuditLogResponse]
    total: int


class ActionInfo(BaseModel):
    """操作信息"""
    action: str
    label: str
    description: str


AUDIT_ACTIONS: Dict[str, ActionInfo] = {
    "TASK_CREATE": ActionInfo(action="TASK_CREATE", label="创建任务", description="创建新的分析任务"),
    "TASK_DELETE": ActionInfo(action="TASK_DELETE", label="删除任务", description="删除分析任务"),
    "TASK_SHARE": ActionInfo(action="TASK_SHARE", label="分享任务", description="分享任务到团队"),
    "REPORT_VIEW": ActionInfo(action="REPORT_VIEW", label="查看报告", description="查看分析报告"),
    "REPORT_EXPORT": ActionInfo(action="REPORT_EXPORT", label="导出报告", description="导出报告数据"),
    "REPORT_SHARE": ActionInfo(action="REPORT_SHARE", label="分享报告", description="分享报告链接"),
    "TEAM_CREATE": ActionInfo(action="TEAM_CREATE", label="创建团队", description="创建新团队"),
    "TEAM_DELETE": ActionInfo(action="TEAM_DELETE", label="删除团队", description="删除团队"),
    "TEAM_JOIN": ActionInfo(action="TEAM_JOIN", label="加入团队", description="加入团队"),
    "TEAM_LEAVE": ActionInfo(action="TEAM_LEAVE", label="离开团队", description="离开团队"),
    "TEAM_INVITE": ActionInfo(action="TEAM_INVITE", label="邀请成员", description="邀请成员加入团队"),
    "TEAM_MEMBER_REMOVE": ActionInfo(action="TEAM_MEMBER_REMOVE", label="移除成员", description="移除团队成员"),
    "TEAM_ROLE_CHANGE": ActionInfo(action="TEAM_ROLE_CHANGE", label="修改角色", description="修改成员角色"),
    "TEAM_SETTINGS_CHANGE": ActionInfo(action="TEAM_SETTINGS_CHANGE", label="修改设置", description="修改团队设置"),
    "PROFILE_UPDATE": ActionInfo(action="PROFILE_UPDATE", label="更新资料", description="更新个人资料"),
    "PASSWORD_CHANGE": ActionInfo(action="PASSWORD_CHANGE", label="修改密码", description="修改登录密码"),
    "LOGIN": ActionInfo(action="LOGIN", label="登录", description="用户登录"),
    "LOGOUT": ActionInfo(action="LOGOUT", label="登出", description="用户登出"),
    "COMMENT_CREATE": ActionInfo(action="COMMENT_CREATE", label="发表评论", description="发表评论"),
    "COMMENT_DELETE": ActionInfo(action="COMMENT_DELETE", label="删除评论", description="删除评论"),
}


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    request: Request,
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的审计日志
    
    Args:
        request: 请求对象
        action: 操作类型过滤
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        
    Returns:
        AuditLogListResponse: 审计日志列表
    """
    logs = await AuditDB.get_user_logs(
        user_id=current_user["id"],
        limit=limit,
        offset=offset,
        action=action
    )
    
    total = await AuditDB.get_logs_count(
        user_id=current_user["id"],
        action=action
    )
    
    return AuditLogListResponse(
        logs=[
            AuditLogResponse(
                id=log["id"],
                user_id=log["user_id"],
                action=log["action"],
                resource_type=log.get("resource_type"),
                resource_id=log.get("resource_id"),
                details=log.get("details"),
                ip_address=log.get("ip_address"),
                user_agent=log.get("user_agent"),
                created_at=log.get("created_at")
            )
            for log in logs
        ],
        total=total
    )


@router.get("/actions", response_model=List[ActionInfo])
async def get_audit_actions():
    """
    获取所有审计操作类型
    
    Returns:
        List[ActionInfo]: 操作类型列表
    """
    return list(AUDIT_ACTIONS.values())


async def log_action(
    user_id: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None
) -> None:
    """
    记录审计日志（后台任务）
    
    Args:
        user_id: 用户ID
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        details: 详细信息
        ip_address: IP地址
        user_agent: 用户代理
    """
    try:
        await AuditDB.create_log(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to create audit log: {e}")


def get_client_info(request: Request) -> tuple:
    """获取客户端信息"""
    ip_address = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    
    user_agent = request.headers.get("User-Agent", "")[:500]
    
    return ip_address, user_agent
