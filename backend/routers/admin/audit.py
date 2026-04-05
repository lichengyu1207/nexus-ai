"""
管理员审计日志API路由
提供审计日志的多维筛选、分页、排序和导出功能
安全保护：所有审计API仅限super_admin访问，且访问行为本身也被记录
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import json
import csv
import io
import asyncio

from ...auth import require_admin, require_super_admin
from ...database import get_db_connection
from ...exceptions import BadRequestException, NotFoundException, ErrorCode
from ...services.audit_service import log_audit, ActionType, ResourceType, AuditStatus

router = APIRouter(prefix="/api/admin/audit", tags=["admin-audit"])


def get_client_info(request: Request):
    """获取客户端信息"""
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


def log_audit_access(admin: dict, action: str, request: Request, details: Dict = None):
    """记录审计日志访问行为"""
    ip, user_agent = get_client_info(request)
    log_audit(
        action_type=ActionType.ADMIN_USER_VIEW,
        user_id=admin.get("id"),
        username=admin.get("email") or admin.get("username"),
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.SYSTEM,
        resource_id="audit_logs",
        new_value={"action": action, **(details or {})},
        status=AuditStatus.SUCCESS,
    )


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: str
    timestamp: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    filters_applied: Dict[str, Any]


class AuditStatsResponse(BaseModel):
    """审计统计响应"""
    total_logs: int
    logs_today: int
    logs_this_week: int
    logs_this_month: int
    success_count: int
    failure_count: int
    unique_users: int
    unique_ips: int
    top_actions: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    daily_trend: List[Dict[str, Any]]


ACTION_TYPE_LABELS = {
    "LOGIN": "登录",
    "LOGOUT": "登出",
    "LOGIN_FAILED": "登录失败",
    "REGISTER": "注册",
    "PASSWORD_CHANGE": "修改密码",
    "PROFILE_UPDATE": "更新资料",
    "TASK_CREATE": "创建任务",
    "TASK_VIEW": "查看任务",
    "TASK_UPDATE": "更新任务",
    "TASK_DELETE": "删除任务",
    "TASK_ASSIGN": "分配任务",
    "REPORT_CREATE": "创建报告",
    "REPORT_VIEW": "查看报告",
    "REPORT_EXPORT": "导出报告",
    "REPORT_DELETE": "删除报告",
    "REPORT_SHARE": "分享报告",
    "TEAM_CREATE": "创建团队",
    "TEAM_JOIN": "加入团队",
    "TEAM_LEAVE": "离开团队",
    "TEAM_MEMBER_ADD": "添加成员",
    "TEAM_MEMBER_REMOVE": "移除成员",
    "TEAM_DELETE": "删除团队",
    "FEEDBACK_CREATE": "创建反馈",
    "FEEDBACK_REPLY": "回复反馈",
    "REPORT_SUBMIT": "提交报告",
    "REPORT_PROCESS": "处理报告",
    "ADMIN_USER_VIEW": "查看用户",
    "ADMIN_USER_CREATE": "创建用户",
    "ADMIN_USER_UPDATE": "更新用户",
    "ADMIN_USER_DELETE": "删除用户",
    "ADMIN_SETTING_CHANGE": "修改设置",
    "ADMIN_ANNOUNCEMENT_CREATE": "创建公告",
    "ADMIN_ANNOUNCEMENT_PUBLISH": "发布公告",
    "DATA_EXPORT": "数据导出",
    "DATA_IMPORT": "数据导入",
    "API_ACCESS": "API访问",
    "FILE_UPLOAD": "文件上传",
    "FILE_DOWNLOAD": "文件下载",
    "PRIVACY_CONSENT": "隐私同意",
}

RESOURCE_TYPE_LABELS = {
    "user": "用户",
    "task": "任务",
    "report": "报告",
    "team": "团队",
    "feedback": "反馈",
    "announcement": "公告",
    "setting": "设置",
    "file": "文件",
    "system": "系统",
}

SORTABLE_FIELDS = ["timestamp", "user_id", "action_type", "resource_type", "status", "ip_address"]


def get_action_label(action_type: str) -> str:
    return ACTION_TYPE_LABELS.get(action_type, action_type)


def get_resource_label(resource_type: str) -> str:
    return RESOURCE_TYPE_LABELS.get(resource_type, resource_type)


def parse_json_safe(value: Any) -> Optional[Dict]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return None
    return None


async def build_audit_query(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    action_types: Optional[List[str]] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: Optional[str] = None,
    ip_address: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> tuple[str, List[Any]]:
    """
    构建审计日志查询SQL
    
    Returns:
        (where_clause, params)
    """
    conditions = []
    params = []
    
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            conditions.append("DATE(timestamp) >= ?")
            params.append(start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            conditions.append("DATE(timestamp) <= ?")
            params.append(end_date)
        except ValueError:
            pass
    
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    
    if action_types and len(action_types) > 0:
        if len(action_types) == 1:
            conditions.append("action_type = ?")
            params.append(action_types[0])
        else:
            placeholders = ",".join("?" * len(action_types))
            conditions.append(f"action_type IN ({placeholders})")
            params.extend(action_types)
    
    if resource_type:
        conditions.append("resource_type = ?")
        params.append(resource_type)
    
    if resource_id:
        conditions.append("resource_id = ?")
        params.append(resource_id)
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if ip_address:
        if "%" in ip_address or "_" in ip_address:
            conditions.append("ip_address LIKE ?")
        else:
            conditions.append("ip_address LIKE ?")
            ip_address = f"%{ip_address}%"
        params.append(ip_address)
    
    if search:
        search_conditions = [
            "username LIKE ?",
            "user_id LIKE ?",
            "resource_id LIKE ?",
            "error_message LIKE ?",
        ]
        conditions.append(f"({' OR '.join(search_conditions)})")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    return where_clause, params


async def get_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    action_types: Optional[List[str]] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: Optional[str] = None,
    ip_address: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 50,
) -> tuple[List[Dict], int]:
    """
    获取审计日志列表
    """
    if sort_by not in SORTABLE_FIELDS:
        sort_by = "timestamp"
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"
    
    where_clause, params = await build_audit_query(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action_types=action_types,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        ip_address=ip_address,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    offset = (page - 1) * per_page
    
    conn = await get_db_connection()
    try:
        count_query = f"SELECT COUNT(*) as total FROM audit_logs {where_clause}"
        count_cursor = await conn.execute(count_query, params)
        total = (await count_cursor.fetchone())["total"]
        
        data_query = f"""
            SELECT 
                id, timestamp, user_id, username, user_role,
                ip_address, user_agent, action_type, resource_type,
                resource_id, old_value, new_value, status, error_message, created_at
            FROM audit_logs
            {where_clause}
            ORDER BY {sort_by} {sort_order.upper()}
            LIMIT ? OFFSET ?
        """
        data_cursor = await conn.execute(data_query, params + [per_page, offset])
        rows = await data_cursor.fetchall()
        
        return [dict(row) for row in rows], total
    finally:
        await conn.close()


def log_to_response(log: Dict) -> AuditLogResponse:
    return AuditLogResponse(
        id=log["id"],
        timestamp=log.get("timestamp"),
        user_id=log.get("user_id"),
        username=log.get("username"),
        user_role=log.get("user_role"),
        ip_address=log.get("ip_address"),
        user_agent=log.get("user_agent"),
        action_type=log.get("action_type", ""),
        resource_type=log.get("resource_type"),
        resource_id=log.get("resource_id"),
        old_value=parse_json_safe(log.get("old_value")),
        new_value=parse_json_safe(log.get("new_value")),
        status=log.get("status", "success"),
        error_message=log.get("error_message"),
        created_at=log.get("created_at"),
    )


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    request: Request,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    action_type: Optional[str] = Query(None, description="操作类型（多个用逗号分隔）"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    status: Optional[str] = Query(None, description="状态: success/failure"),
    ip_address: Optional[str] = Query(None, description="IP地址（支持模糊匹配）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("timestamp", description=f"排序字段: {', '.join(SORTABLE_FIELDS)}"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(50, ge=1, le=200, description="每页数量"),
    admin: dict = Depends(require_super_admin),
):
    """
    获取审计日志列表（仅超级管理员）
    
    支持多维筛选：
    - 时间范围：start_date, end_date
    - 用户筛选：user_id
    - 操作类型：action_type（支持多选，逗号分隔）
    - 资源筛选：resource_type, resource_id
    - 状态筛选：status
    - IP筛选：ip_address（支持模糊匹配）
    - 关键词搜索：search
    
    支持排序：
    - sort_by: timestamp, user_id, action_type, resource_type, status, ip_address
    - sort_order: asc, desc
    """
    log_audit_access(admin, "list_logs", request, {
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id,
            "action_type": action_type,
            "status": status,
        },
        "page": page,
        "per_page": per_page,
    })
    
    action_types = None
    if action_type:
        action_types = [t.strip() for t in action_type.split(",") if t.strip()]
    
    logs, total = await get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action_types=action_types,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        ip_address=ip_address,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    filters_applied = {
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id,
        "action_types": action_types,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "ip_address": ip_address,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    
    return AuditLogListResponse(
        logs=[log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        filters_applied={k: v for k, v in filters_applied.items() if v is not None},
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_log_detail(
    log_id: str,
    request: Request,
    admin: dict = Depends(require_super_admin),
):
    """获取单条审计日志详情（仅超级管理员）"""
    log_audit_access(admin, "view_log_detail", request, {"log_id": log_id})
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM audit_logs WHERE id = ?",
            (log_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise NotFoundException("日志不存在", ErrorCode.NOT_FOUND)
        
        return log_to_response(dict(row))
    finally:
        await conn.close()


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    admin: dict = Depends(require_admin),
):
    """获取审计日志统计"""
    conn = await get_db_connection()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        days_ago = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM audit_logs")
        total_logs = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM audit_logs WHERE DATE(timestamp) = ?",
            (today,)
        )
        logs_today = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM audit_logs WHERE DATE(timestamp) >= ?",
            (week_ago,)
        )
        logs_this_week = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM audit_logs WHERE DATE(timestamp) >= ?",
            (month_ago,)
        )
        logs_this_month = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM audit_logs WHERE status = 'success' AND DATE(timestamp) >= ?",
            (days_ago,)
        )
        success_count = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM audit_logs WHERE status = 'failure' AND DATE(timestamp) >= ?",
            (days_ago,)
        )
        failure_count = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(DISTINCT user_id) as count FROM audit_logs WHERE DATE(timestamp) >= ?",
            (days_ago,)
        )
        unique_users = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(DISTINCT ip_address) as count FROM audit_logs WHERE DATE(timestamp) >= ?",
            (days_ago,)
        )
        unique_ips = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT action_type, COUNT(*) as count
            FROM audit_logs
            WHERE DATE(timestamp) >= ?
            GROUP BY action_type
            ORDER BY count DESC
            LIMIT 10
            """,
            (days_ago,)
        )
        top_actions = [
            {
                "action_type": row["action_type"],
                "label": get_action_label(row["action_type"]),
                "count": row["count"]
            }
            for row in await cursor.fetchall()
        ]
        
        cursor = await conn.execute(
            """
            SELECT user_id, username, COUNT(*) as count
            FROM audit_logs
            WHERE DATE(timestamp) >= ?
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
            """,
            (days_ago,)
        )
        top_users = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(
            """
            SELECT DATE(timestamp) as date, COUNT(*) as count,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                   SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) as failure_count
            FROM audit_logs
            WHERE DATE(timestamp) >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            """,
            (days_ago,)
        )
        daily_trend = [dict(row) for row in await cursor.fetchall()]
        
        return AuditStatsResponse(
            total_logs=total_logs,
            logs_today=logs_today,
            logs_this_week=logs_this_week,
            logs_this_month=logs_this_month,
            success_count=success_count,
            failure_count=failure_count,
            unique_users=unique_users,
            unique_ips=unique_ips,
            top_actions=top_actions,
            top_users=top_users,
            daily_trend=daily_trend,
        )
    finally:
        await conn.close()


@router.get("/action-types")
async def get_action_types(admin: dict = Depends(require_admin)):
    """获取所有操作类型"""
    return {
        "types": [
            {"value": action, "label": label}
            for action, label in ACTION_TYPE_LABELS.items()
        ]
    }


@router.get("/resource-types")
async def get_resource_types(admin: dict = Depends(require_admin)):
    """获取所有资源类型"""
    return {
        "types": [
            {"value": resource, "label": label}
            for resource, label in RESOURCE_TYPE_LABELS.items()
        ]
    }


@router.get("/export")
async def export_audit_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    format: str = Query("csv", description="导出格式: csv/json"),
    admin: dict = Depends(require_admin),
):
    """
    导出审计日志
    
    支持CSV和JSON两种格式
    """
    action_types = None
    if action_type:
        action_types = [t.strip() for t in action_type.split(",") if t.strip()]
    
    logs, _ = await get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action_types=action_types,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        ip_address=ip_address,
        search=search,
        sort_by="timestamp",
        sort_order="desc",
        page=1,
        per_page=10000,
    )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format.lower() == "json":
        output = io.BytesIO(
            json.dumps(
                [log for log in logs],
                default=str,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")
        )
        filename = f"audit_logs_{timestamp}.json"
        media_type = "application/json"
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "ID", "时间", "用户ID", "用户名", "用户角色",
            "IP地址", "操作类型", "操作标签", "资源类型", "资源ID",
            "状态", "错误信息", "创建时间"
        ])
        
        for log in logs:
            writer.writerow([
                log.get("id", ""),
                log.get("timestamp", ""),
                log.get("user_id", ""),
                log.get("username", ""),
                log.get("user_role", ""),
                log.get("ip_address", ""),
                log.get("action_type", ""),
                get_action_label(log.get("action_type", "")),
                log.get("resource_type", ""),
                log.get("resource_id", ""),
                log.get("status", ""),
                log.get("error_message", ""),
                log.get("created_at", ""),
            ])
        
        output = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        filename = f"audit_logs_{timestamp}.csv"
        media_type = "text/csv"
    
    return StreamingResponse(
        output,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache",
        }
    )


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=30, le=365, description="保留天数"),
    admin: dict = Depends(require_super_admin),
):
    """
    清理旧审计日志（仅超级管理员）
    
    删除超过指定天数的日志
    """
    conn = await get_db_connection()
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor = await conn.execute(
            "DELETE FROM audit_logs WHERE DATE(timestamp) < ?",
            (cutoff_date,)
        )
        deleted_count = cursor.rowcount
        await conn.commit()
        
        return {
            "message": f"已删除 {deleted_count} 条超过 {days} 天的日志",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date,
            "retention_days": days,
        }
    finally:
        await conn.close()


@router.get("/user/{user_id}", response_model=AuditLogListResponse)
async def get_user_audit_logs(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    admin: dict = Depends(require_admin),
):
    """获取指定用户的审计日志"""
    action_types = None
    if action_type:
        action_types = [t.strip() for t in action_type.split(",") if t.strip()]
    
    logs, total = await get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action_types=action_types,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    return AuditLogListResponse(
        logs=[log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        filters_applied={"user_id": user_id},
    )


@router.get("/ip/{ip_address}", response_model=AuditLogListResponse)
async def get_ip_audit_logs(
    ip_address: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    admin: dict = Depends(require_admin),
):
    """获取指定IP的审计日志"""
    action_types = None
    if action_type:
        action_types = [t.strip() for t in action_type.split(",") if t.strip()]
    
    logs, total = await get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        action_types=action_types,
        status=status,
        ip_address=ip_address,
        page=page,
        per_page=per_page,
    )
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    return AuditLogListResponse(
        logs=[log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        filters_applied={"ip_address": ip_address},
    )


@router.get("/resource/{resource_type}/{resource_id}", response_model=AuditLogListResponse)
async def get_resource_audit_logs(
    resource_type: str,
    resource_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    admin: dict = Depends(require_admin),
):
    """获取指定资源的审计日志"""
    action_types = None
    if action_type:
        action_types = [t.strip() for t in action_type.split(",") if t.strip()]
    
    logs, total = await get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        action_types=action_types,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        per_page=per_page,
    )
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    return AuditLogListResponse(
        logs=[log_to_response(log) for log in logs],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        filters_applied={"resource_type": resource_type, "resource_id": resource_id},
    )
