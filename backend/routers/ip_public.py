"""
IP扶持计划 - 公共接口
包含IP申请、推广链接验证等公开接口
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import uuid
import json
import logging

from backend.database import get_db_connection
from backend.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ip", tags=["ip_public"])

class IPApplyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="姓名/昵称")
    contact: str = Field(..., min_length=1, max_length=100, description="联系方式")
    email: Optional[EmailStr] = None
    platform_type: str = Field(..., description="主要平台: zhihu/wechat/bilibili/douyin/redbook/other")
    platform_id: Optional[str] = Field(None, max_length=100, description="平台账号ID")
    platform_name: Optional[str] = Field(None, max_length=100, description="平台账号名称")
    followers: int = Field(default=0, ge=0, description="粉丝数")
    introduction: Optional[str] = Field(None, max_length=500, description="简介")

class IPApplyResponse(BaseModel):
    success: bool
    message: str
    application_id: Optional[str] = None

class IPInfoResponse(BaseModel):
    id: str
    name: str
    avatar: Optional[str]
    platform_type: str
    platform_name: Optional[str]
    level: str
    level_name: str

class LinkCheckResponse(BaseModel):
    valid: bool
    ip_info: Optional[IPInfoResponse] = None
    message: Optional[str] = None

@router.post("/apply", response_model=IPApplyResponse)
async def apply_ip(request: IPApplyRequest):
    """
    申请成为IP创作者
    - 提交申请信息
    - 状态设为pending等待审核
    """
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        existing = cursor.execute(
            "SELECT id, status FROM ip_partners WHERE email = ? OR contact = ?",
            (request.email, request.contact)
        ).fetchone()
        
        if existing:
            if existing['status'] == 'pending':
                return IPApplyResponse(
                    success=False,
                    message="您已有申请正在审核中，请耐心等待",
                    application_id=existing['id']
                )
            elif existing['status'] in ['trial', 'active']:
                return IPApplyResponse(
                    success=False,
                    message="您已经是IP创作者，无需重复申请"
                )
        
        ip_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_partners (
                id, name, contact, email, platform_type, platform_id, 
                platform_name, followers, introduction, status, level, 
                base_commission, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'bronze', 5.0, ?, ?)
        ''', (
            ip_id, request.name, request.contact, request.email,
            request.platform_type, request.platform_id, request.platform_name,
            request.followers, request.introduction,
            datetime.now(), datetime.now()
        ))
        
        cursor.execute('''
            INSERT INTO ip_operation_logs (id, ip_id, operation_type, notes, created_at)
            VALUES (?, ?, 'apply', '提交IP申请', ?)
        ''', (str(uuid.uuid4()), ip_id, datetime.now()))
        
        conn.commit()
        
        logger.info(f"New IP application: {ip_id} - {request.name}")
        
        return IPApplyResponse(
            success=True,
            message="申请已提交，我们将在1-3个工作日内审核",
            application_id=ip_id
        )
        
    except Exception as e:
        logger.error(f"IP apply error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="申请提交失败，请稍后重试")
    finally:
        conn.close()

@router.get("/check", response_model=LinkCheckResponse)
async def check_referral_link(code: str):
    """
    验证推广链接
    - 检查code是否有效
    - 返回IP信息用于展示欢迎信息
    """
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        link = cursor.execute('''
            SELECT l.*, p.name, p.avatar, p.platform_type, p.platform_name, p.level, p.status
            FROM ip_links l
            JOIN ip_partners p ON l.ip_id = p.id
            WHERE l.code = ? AND l.is_active = 1
        ''', (code,)).fetchone()
        
        if not link:
            return LinkCheckResponse(
                valid=False,
                message="推广链接无效或已失效"
            )
        
        if link['status'] not in ['trial', 'active']:
            return LinkCheckResponse(
                valid=False,
                message="该创作者暂未激活"
            )
        
        level_info = cursor.execute(
            "SELECT level_name FROM ip_levels WHERE level_code = ?",
            (link['level'],)
        ).fetchone()
        
        return LinkCheckResponse(
            valid=True,
            ip_info=IPInfoResponse(
                id=link['ip_id'],
                name=link['name'],
                avatar=link['avatar'],
                platform_type=link['platform_type'],
                platform_name=link['platform_name'],
                level=link['level'],
                level_name=level_info['level_name'] if level_info else '青铜创作者'
            )
        )
        
    except Exception as e:
        logger.error(f"Check referral link error: {e}")
        raise HTTPException(status_code=500, detail="验证失败")
    finally:
        conn.close()

@router.get("/levels")
async def get_ip_levels():
    """获取IP等级列表"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        levels = cursor.execute('''
            SELECT id, level_name, level_code, min_earnings, min_referrals, 
                   commission_bonus, benefits, icon, color
            FROM ip_levels
            ORDER BY min_earnings ASC
        ''').fetchall()
        
        return {"levels": levels}
    finally:
        conn.close()

@router.get("/commission-rules")
async def get_commission_rules():
    """获取公开的佣金规则信息"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        rules = cursor.execute('''
            SELECT id, name, rule_type, min_amount, commission_rate, bonus_rate
            FROM ip_commission_rules
            WHERE is_active = 1
            ORDER BY priority ASC
        ''').fetchall()
        
        return {"rules": rules}
    finally:
        conn.close()

@router.post("/click/{code}")
async def record_link_click(code: str, request: Request):
    """记录链接点击"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        result = cursor.execute(
            "UPDATE ip_links SET click_count = click_count + 1 WHERE code = ?",
            (code,)
        )
        
        if result.rowcount > 0:
            conn.commit()
            return {"success": True}
        else:
            return {"success": False, "message": "链接不存在"}
            
    except Exception as e:
        logger.error(f"Record click error: {e}")
        return {"success": False}
    finally:
        conn.close()

@router.get("/status/{application_id}")
async def check_application_status(application_id: str):
    """查询申请状态"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        application = cursor.execute('''
            SELECT id, name, status, level, base_commission, created_at, notes
            FROM ip_partners
            WHERE id = ?
        ''', (application_id,)).fetchone()
        
        if not application:
            raise HTTPException(status_code=404, detail="申请不存在")
        
        status_map = {
            'pending': '审核中',
            'trial': '试用期',
            'active': '已通过',
            'suspended': '已暂停',
            'rejected': '已拒绝',
            'terminated': '已终止'
        }
        
        return {
            "application_id": application['id'],
            "name": application['name'],
            "status": application['status'],
            "status_text": status_map.get(application['status'], '未知'),
            "level": application['level'],
            "base_commission": application['base_commission'],
            "created_at": application['created_at'],
            "notes": application['notes']
        }
        
    finally:
        conn.close()
