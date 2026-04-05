"""
隐私政策API路由
提供隐私政策版本获取、用户同意记录、检查等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from backend.auth import get_current_user, require_admin
from ..database import get_db_connection

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


class PrivacyPolicyResponse(BaseModel):
    id: str
    version: str
    title: str
    content: str
    effective_date: str
    created_at: Optional[str] = None


class PrivacyVersionSummary(BaseModel):
    id: str
    version: str
    title: str
    effective_date: str
    is_current: int


class AgreeRequest(BaseModel):
    version_id: str


class AgreeResponse(BaseModel):
    success: bool
    message: str
    agreed_at: str


class CheckResponse(BaseModel):
    need_agree: bool
    current_version: Optional[str] = None
    latest_version: Optional[PrivacyPolicyResponse] = None


class UserAgreementRecord(BaseModel):
    id: str
    version: str
    version_id: str
    ip_address: Optional[str] = None
    agreed_at: str


@router.get("/current", response_model=PrivacyPolicyResponse)
async def get_current_privacy():
    """获取当前生效的隐私政策"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id, version, title, content, effective_date, created_at
            FROM privacy_policy_versions
            WHERE is_current = 1
            ORDER BY effective_date DESC
            LIMIT 1
        ''')
        row = await cursor.fetchone()
        
        if not row:
            cursor = await conn.execute('''
                SELECT id, version, title, content, effective_date, created_at
                FROM privacy_policy_versions
                ORDER BY effective_date DESC
                LIMIT 1
            ''')
            row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="未找到隐私政策")
        
        return PrivacyPolicyResponse(
            id=row['id'],
            version=row['version'],
            title=row['title'],
            content=row['content'],
            effective_date=row['effective_date'],
            created_at=row['created_at']
        )
    finally:
        await conn.close()


@router.get("/versions/{version}", response_model=PrivacyPolicyResponse)
async def get_privacy_by_version(version: str):
    """获取指定版本的隐私政策"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id, version, title, content, effective_date, created_at
            FROM privacy_policy_versions
            WHERE version = ?
        ''', (version,))
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        return PrivacyPolicyResponse(
            id=row['id'],
            version=row['version'],
            title=row['title'],
            content=row['content'],
            effective_date=row['effective_date'],
            created_at=row['created_at']
        )
    finally:
        await conn.close()


@router.get("/versions", response_model=List[PrivacyVersionSummary])
async def list_privacy_versions():
    """获取所有隐私政策版本列表"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id, version, title, effective_date, is_current
            FROM privacy_policy_versions
            ORDER BY effective_date DESC
        ''')
        rows = await cursor.fetchall()
        
        return [
            PrivacyVersionSummary(
                id=row['id'],
                version=row['version'],
                title=row['title'],
                effective_date=row['effective_date'],
                is_current=row['is_current']
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.post("/agree", response_model=AgreeResponse)
async def agree_privacy(
    request: AgreeRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """用户同意隐私政策"""
    user_id = current_user['id']
    
    ip = http_request.client.host if http_request.client else None
    forwarded = http_request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = http_request.headers.get('user-agent', '')
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id, version FROM privacy_policy_versions WHERE id = ?",
            (request.version_id,)
        )
        version_row = await cursor.fetchone()
        
        if not version_row:
            raise HTTPException(status_code=400, detail="无效的隐私政策版本")
        
        version = version_row['version']
        agreed_at = datetime.now().isoformat()
        
        agreement_id = str(uuid.uuid4())
        await conn.execute('''
            INSERT INTO user_privacy_agreements 
            (id, user_id, version_id, version, ip_address, user_agent, agreed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (agreement_id, user_id, request.version_id, version, ip, user_agent, agreed_at))
        
        await conn.execute('''
            UPDATE users SET agreed_privacy_version = ?, agreed_privacy_at = ?
            WHERE id = ?
        ''', (version, agreed_at, user_id))
        
        await conn.commit()
        
        return AgreeResponse(
            success=True,
            message="同意记录成功",
            agreed_at=agreed_at
        )
    finally:
        await conn.close()


@router.get("/check", response_model=CheckResponse)
async def check_privacy_agreement(current_user: dict = Depends(get_current_user)):
    """检查用户是否需要重新同意隐私政策"""
    user_id = current_user['id']
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT agreed_privacy_version FROM users WHERE id = ?",
            (user_id,)
        )
        user_row = await cursor.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user_version = user_row['agreed_privacy_version']
        
        cursor = await conn.execute('''
            SELECT id, version, title, content, effective_date, created_at
            FROM privacy_policy_versions
            WHERE is_current = 1
            ORDER BY effective_date DESC
            LIMIT 1
        ''')
        latest_row = await cursor.fetchone()
        
        if not latest_row:
            cursor = await conn.execute('''
                SELECT id, version, title, content, effective_date, created_at
                FROM privacy_policy_versions
                ORDER BY effective_date DESC
                LIMIT 1
            ''')
            latest_row = await cursor.fetchone()
        
        if not latest_row:
            return CheckResponse(need_agree=False)
        
        latest_version = latest_row['version']
        need_agree = (user_version != latest_version)
        
        return CheckResponse(
            need_agree=need_agree,
            current_version=user_version,
            latest_version=PrivacyPolicyResponse(
                id=latest_row['id'],
                version=latest_row['version'],
                title=latest_row['title'],
                content=latest_row['content'],
                effective_date=latest_row['effective_date'],
                created_at=latest_row['created_at']
            ) if need_agree else None
        )
    finally:
        await conn.close()


@router.get("/agreements", response_model=List[UserAgreementRecord])
async def get_user_agreements(current_user: dict = Depends(get_current_user)):
    """获取用户的同意记录历史"""
    user_id = current_user['id']
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT id, version, version_id, ip_address, agreed_at
            FROM user_privacy_agreements
            WHERE user_id = ?
            ORDER BY agreed_at DESC
        ''', (user_id,))
        rows = await cursor.fetchall()
        
        return [
            UserAgreementRecord(
                id=row['id'],
                version=row['version'],
                version_id=row['version_id'],
                ip_address=row['ip_address'],
                agreed_at=row['agreed_at']
            )
            for row in rows
        ]
    finally:
        await conn.close()
