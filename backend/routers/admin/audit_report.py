"""
管理员审计报告API
生成符合监管要求的PDF审计报告
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import io

from ...auth import require_admin
from ...services.report_generator import report_generator, REPORTLAB_AVAILABLE
from ...exceptions import BadRequestException, ErrorCode

router = APIRouter(prefix="/api/admin/audit/report", tags=["admin-audit-report"])


class ReportRequest(BaseModel):
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    user_id: Optional[str] = Field(None, description="用户ID筛选")
    action_types: Optional[List[str]] = Field(None, description="操作类型筛选")
    include_logs: bool = Field(True, description="是否包含日志明细")


@router.post("")
async def generate_audit_report(
    request: ReportRequest,
    admin: dict = Depends(require_admin),
):
    """
    生成审计报告PDF
    
    生成包含以下内容的PDF报告：
    - 封面：报告名称、生成时间、生成人、时间范围
    - 统计摘要：总日志数、按操作类型分布、按用户分布
    - 日志明细：最近100条日志（可选）
    - 完整性验证结果
    """
    if not REPORTLAB_AVAILABLE:
        raise BadRequestException(
            "PDF生成功能不可用，请安装 reportlab 库",
            ErrorCode.SERVICE_UNAVAILABLE
        )
    
    pdf_bytes = await report_generator.generate_report(
        start_date=request.start_date,
        end_date=request.end_date,
        user_id=request.user_id,
        action_types=request.action_types,
        include_logs=request.include_logs,
        generated_by=admin.get("email") or admin.get("username"),
    )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_report_{timestamp}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache",
        }
    )


@router.post("/preview")
async def preview_report_data(
    request: ReportRequest,
    admin: dict = Depends(require_admin),
):
    """
    预览报告数据
    
    返回报告将包含的数据，用于前端预览
    """
    from ...services.report_generator import AuditReportGenerator
    from ...database import get_db_connection
    
    conn = await get_db_connection()
    try:
        conditions = []
        params = []
        
        if request.start_date:
            conditions.append("DATE(timestamp) >= ?")
            params.append(request.start_date)
        if request.end_date:
            conditions.append("DATE(timestamp) <= ?")
            params.append(request.end_date)
        if request.user_id:
            conditions.append("user_id = ?")
            params.append(request.user_id)
        if request.action_types:
            placeholders = ",".join("?" * len(request.action_types))
            conditions.append(f"action_type IN ({placeholders})")
            params.extend(request.action_types)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as count FROM audit_logs {where_clause}
        """, params)
        total_logs = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(f"""
            SELECT action_type, COUNT(*) as count
            FROM audit_logs {where_clause}
            GROUP BY action_type
            ORDER BY count DESC
            LIMIT 10
        """, params)
        action_distribution = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(f"""
            SELECT user_id, username, COUNT(*) as count
            FROM audit_logs {where_clause}
            AND user_id IS NOT NULL
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        """, params)
        user_distribution = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(f"""
            SELECT status, COUNT(*) as count
            FROM audit_logs {where_clause}
            GROUP BY status
        """, params)
        status_distribution = {row["status"]: row["count"] for row in await cursor.fetchall()}
        
        return {
            "total_logs": total_logs,
            "action_distribution": action_distribution,
            "user_distribution": user_distribution,
            "status_distribution": status_distribution,
            "estimated_pages": max(5, (total_logs // 50) + 5) if request.include_logs else 5,
        }
    finally:
        await conn.close()


@router.get("/templates")
async def get_report_templates(
    admin: dict = Depends(require_admin),
):
    """
    获取报告模板列表
    
    返回可用的报告模板配置
    """
    return {
        "templates": [
            {
                "id": "standard",
                "name": "标准审计报告",
                "description": "包含完整的统计摘要和日志明细",
                "include_logs": True,
            },
            {
                "id": "summary",
                "name": "摘要报告",
                "description": "仅包含统计摘要，不含日志明细",
                "include_logs": False,
            },
            {
                "id": "security",
                "name": "安全审计报告",
                "description": "聚焦安全相关操作的审计报告",
                "action_types": ["LOGIN", "LOGIN_FAILED", "LOGOUT", "PASSWORD_CHANGE", "ADMIN_USER_CREATE", "ADMIN_USER_DELETE"],
                "include_logs": True,
            },
            {
                "id": "data_access",
                "name": "数据访问报告",
                "description": "聚焦数据访问和导出操作",
                "action_types": ["REPORT_VIEW", "REPORT_EXPORT", "DATA_EXPORT", "FILE_DOWNLOAD"],
                "include_logs": True,
            },
        ]
    }
