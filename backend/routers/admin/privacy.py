"""
隐私政策管理员API
提供版本管理、统计等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import uuid

from backend.auth import require_admin
from backend.database import get_db_connection

router = APIRouter(prefix="/api/admin/privacy", tags=["admin-privacy"])


class CreateVersionRequest(BaseModel):
    title: str
    content: str
    effective_date: str
    version: str


class VersionResponse(BaseModel):
    id: str
    version: str
    title: str
    content: str
    effective_date: str
    is_current: int
    created_at: Optional[str] = None
    created_by: Optional[str] = None


class VersionSummary(BaseModel):
    id: str
    version: str
    title: str
    effective_date: str
    is_current: int
    created_at: Optional[str] = None
    agreement_count: int = 0


class StatsResponse(BaseModel):
    total_users: int
    agreed_users: int
    pending_users: int
    latest_version: Optional[str] = None
    version_distribution: List[dict]


@router.get("/versions", response_model=List[VersionSummary])
async def admin_list_versions(current_user: dict = Depends(require_admin)):
    """获取所有隐私政策版本（管理员）"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute('''
            SELECT 
                v.id, v.version, v.title, v.effective_date, v.is_current, v.created_at,
                (SELECT COUNT(*) FROM user_privacy_agreements WHERE version_id = v.id) as agreement_count
            FROM privacy_policy_versions v
            ORDER BY v.effective_date DESC
        ''')
        rows = await cursor.fetchall()
        
        return [
            VersionSummary(
                id=row['id'],
                version=row['version'],
                title=row['title'],
                effective_date=row['effective_date'],
                is_current=row['is_current'],
                created_at=row['created_at'],
                agreement_count=row['agreement_count']
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.post("/versions", response_model=VersionResponse)
async def create_version(
    request: CreateVersionRequest,
    http_request: Request,
    current_user: dict = Depends(require_admin)
):
    """创建新的隐私政策版本"""
    admin_id = current_user['id']
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM privacy_policy_versions WHERE version = ?",
            (request.version,)
        )
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="版本号已存在")
        
        version_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        await conn.execute('''
            INSERT INTO privacy_policy_versions 
            (id, version, title, content, effective_date, is_current, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        ''', (version_id, request.version, request.title, request.content, 
              request.effective_date, created_at, admin_id))
        
        await conn.commit()
        
        return VersionResponse(
            id=version_id,
            version=request.version,
            title=request.title,
            content=request.content,
            effective_date=request.effective_date,
            is_current=0,
            created_at=created_at,
            created_by=admin_id
        )
    finally:
        await conn.close()


@router.put("/versions/{version_id}/activate")
async def activate_version(
    version_id: str,
    current_user: dict = Depends(require_admin)
):
    """激活指定版本为当前版本"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM privacy_policy_versions WHERE id = ?",
            (version_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="版本不存在")
        
        await conn.execute("UPDATE privacy_policy_versions SET is_current = 0")
        await conn.execute("UPDATE privacy_policy_versions SET is_current = 1 WHERE id = ?", (version_id,))
        await conn.commit()
        
        return {"success": True, "message": "版本已激活"}
    finally:
        await conn.close()


@router.delete("/versions/{version_id}")
async def delete_version(
    version_id: str,
    current_user: dict = Depends(require_admin)
):
    """删除隐私政策版本"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id, is_current FROM privacy_policy_versions WHERE id = ?",
            (version_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        if row['is_current'] == 1:
            raise HTTPException(status_code=400, detail="不能删除当前生效的版本")
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM user_privacy_agreements WHERE version_id = ?",
            (version_id,)
        )
        if (await cursor.fetchone())[0] > 0:
            raise HTTPException(status_code=400, detail="该版本已有用户同意记录，无法删除")
        
        await conn.execute("DELETE FROM privacy_policy_versions WHERE id = ?", (version_id,))
        await conn.commit()
        
        return {"success": True, "message": "版本已删除"}
    finally:
        await conn.close()


@router.get("/stats", response_model=StatsResponse)
async def get_privacy_stats(current_user: dict = Depends(require_admin)):
    """获取隐私政策同意统计"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE agreed_privacy_version IS NOT NULL")
        agreed_users = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            "SELECT version FROM privacy_policy_versions WHERE is_current = 1 LIMIT 1"
        )
        latest_row = await cursor.fetchone()
        latest_version = latest_row['version'] if latest_row else None
        
        cursor = await conn.execute('''
            SELECT u.agreed_privacy_version as version, COUNT(*) as count
            FROM users u
            WHERE u.agreed_privacy_version IS NOT NULL
            GROUP BY u.agreed_privacy_version
        ''')
        version_rows = await cursor.fetchall()
        version_distribution = [
            {"version": row['version'], "count": row['count']}
            for row in version_rows
        ]
        
        pending_count = 0
        if latest_version:
            cursor = await conn.execute('''
                SELECT COUNT(*) FROM users 
                WHERE agreed_privacy_version IS NULL OR agreed_privacy_version != ?
            ''', (latest_version,))
            pending_count = (await cursor.fetchone())[0]
        
        return StatsResponse(
            total_users=total_users,
            agreed_users=agreed_users,
            pending_users=pending_count,
            latest_version=latest_version,
            version_distribution=version_distribution
        )
    finally:
        await conn.close()


@router.get("/versions/{version_id}/agreements")
async def get_version_agreements(
    version_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin)
):
    """获取指定版本的同意记录"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM privacy_policy_versions WHERE id = ?",
            (version_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="版本不存在")
        
        cursor = await conn.execute('''
            SELECT a.id, a.user_id, a.version, a.ip_address, a.user_agent, a.agreed_at,
                   u.email, u.username
            FROM user_privacy_agreements a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.version_id = ?
            ORDER BY a.agreed_at DESC
            LIMIT ? OFFSET ?
        ''', (version_id, limit, offset))
        rows = await cursor.fetchall()
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM user_privacy_agreements WHERE version_id = ?",
            (version_id,)
        )
        total = (await cursor.fetchone())[0]
        
        return {
            "agreements": [dict(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        await conn.close()
