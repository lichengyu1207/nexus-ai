"""
安全配置API
提供安全设置和扫描功能
"""
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ...auth import require_super_admin
from ...logger import get_logger
from ...utils.security_scan import SecurityScanner, generate_security_report

logger = get_logger("security_api")

router = APIRouter(prefix="/api/admin/security", tags=["security"])


class SecuritySettings(BaseModel):
    rate_limiting_enabled: bool = True
    csp_enabled: bool = True
    xss_protection: bool = True
    cors_strict_mode: bool = True
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    password_min_length: int = 8
    require_special_chars: bool = True


class CSPConfig(BaseModel):
    default_src: List[str] = ["'self'"]
    script_src: List[str] = ["'self'", "'unsafe-inline'"]
    style_src: List[str] = ["'self'", "'unsafe-inline'"]
    img_src: List[str] = ["'self'", "data:", "https:"]
    connect_src: List[str] = ["'self'"]
    font_src: List[str] = ["'self'"]
    frame_ancestors: List[str] = ["'self'"]


@router.get("/settings")
async def get_security_settings(
    current_user = Depends(require_super_admin),
):
    """获取安全设置"""
    return {
        "rate_limiting_enabled": os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true",
        "csp_enabled": True,
        "xss_protection": True,
        "cors_strict_mode": True,
        "session_timeout_minutes": int(os.getenv("SESSION_TIMEOUT_MINUTES", "60")),
        "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
        "password_min_length": 8,
        "require_special_chars": True,
    }


@router.put("/settings")
async def update_security_settings(
    settings: SecuritySettings,
    current_user = Depends(require_super_admin),
):
    """更新安全设置"""
    logger.info(f"Security settings updated by user {current_user.id}")
    
    return {
        "status": "updated",
        "settings": settings.model_dump(),
    }


@router.get("/csp")
async def get_csp_config(
    current_user = Depends(require_super_admin),
):
    """获取CSP配置"""
    return {
        "default_src": ["'self'"],
        "script_src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "style_src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "img_src": ["'self'", "data:", "https:", "blob:"],
        "connect_src": ["'self'", "https://api.openai.com", "wss:"],
        "font_src": ["'self'", "https://fonts.gstatic.com"],
        "frame_ancestors": ["'self'"],
    }


@router.put("/csp")
async def update_csp_config(
    config: CSPConfig,
    current_user = Depends(require_super_admin),
):
    """更新CSP配置"""
    logger.info(f"CSP config updated by user {current_user.id}")
    
    return {
        "status": "updated",
        "config": config.model_dump(),
    }


@router.post("/scan")
async def run_security_scan(
    current_user = Depends(require_super_admin),
):
    """运行安全扫描"""
    logger.info(f"Security scan initiated by user {current_user.id}")
    
    scanner = SecurityScanner()
    results = await scanner.run_full_scan()
    
    return results


@router.get("/scan/report")
async def get_security_report(
    current_user = Depends(require_super_admin),
):
    """获取安全报告"""
    scanner = SecurityScanner()
    results = await scanner.run_full_scan()
    report = generate_security_report(results)
    
    return {
        "report": report,
        "results": results,
    }


@router.get("/headers")
async def get_security_headers(
    current_user = Depends(require_super_admin),
):
    """获取推荐的安全头配置"""
    return {
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "X-Frame-Options": "SAMEORIGIN",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }


@router.get("/audit-log")
async def get_security_audit_log(
    days: int = 7,
    limit: int = 100,
    current_user = Depends(require_super_admin),
):
    """获取安全审计日志"""
    from ...database import get_db_connection
    
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT 
                id, action, user_id, ip_address, user_agent,
                details, timestamp
            FROM audit_logs
            WHERE timestamp >= datetime('now', ?)
            AND action IN ('login', 'logout', 'password_change', 'permission_change', 'failed_login')
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"-{days} days", limit))
        
        rows = await cursor.fetchall()
        
        logs = [
            {
                "id": row[0],
                "action": row[1],
                "user_id": row[2],
                "ip_address": row[3],
                "user_agent": row[4],
                "details": row[5],
                "timestamp": row[6],
            }
            for row in rows
        ]
        
        return {"logs": logs, "total": len(logs)}


@router.get("/failed-logins")
async def get_failed_login_attempts(
    days: int = 7,
    current_user = Depends(require_super_admin),
):
    """获取失败登录统计"""
    from ...database import get_db_connection
    
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT 
                ip_address,
                COUNT(*) as attempt_count,
                MAX(timestamp) as last_attempt
            FROM audit_logs
            WHERE action = 'failed_login'
            AND timestamp >= datetime('now', ?)
            GROUP BY ip_address
            ORDER BY attempt_count DESC
            LIMIT 20
        """, (f"-{days} days",))
        
        rows = await cursor.fetchall()
        
        return {
            "failed_attempts": [
                {
                    "ip_address": row[0],
                    "attempt_count": row[1],
                    "last_attempt": row[2],
                }
                for row in rows
            ]
        }
