"""
管理员公告管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from ...database import get_db_connection
from ...auth import require_admin

router = APIRouter(prefix="/api/admin/announcements", tags=["admin-announcements"])


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    type: str = "info"
    is_published: bool = False


class AnnouncementResponse(BaseModel):
    id: str
    title: str
    content: str
    type: str
    is_published: bool
    created_at: datetime


@router.get("/", response_model=List[AnnouncementResponse])
async def get_announcements(current_user: dict = Depends(require_admin)):
    """获取公告列表"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@router.post("/", response_model=AnnouncementResponse)
async def create_announcement(data: AnnouncementCreate, current_user: dict = Depends(require_admin)):
    """创建公告"""
    announcement_id = str(uuid.uuid4())
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            INSERT INTO announcements (id, title, content, type, is_published, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (announcement_id, data.title, data.content, data.type, data.is_published, datetime.now().isoformat())
        )
        await conn.commit()
        
        return AnnouncementResponse(
            id=announcement_id,
            title=data.title,
            content=data.content,
            type=data.type,
            is_published=data.is_published,
            created_at=datetime.now()
        )
    finally:
        await conn.close()


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(announcement_id: str, data: AnnouncementCreate, current_user: dict = Depends(require_admin)):
    """更新公告"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            UPDATE announcements SET title = ?, content = ?, type = ?, is_published = ?
            WHERE id = ?
            """,
            (data.title, data.content, data.type, data.is_published, announcement_id)
        )
        await conn.commit()
        
        return AnnouncementResponse(
            id=announcement_id,
            title=data.title,
            content=data.content,
            type=data.type,
            is_published=data.is_published,
            created_at=datetime.now()
        )
    finally:
        await conn.close()


@router.delete("/{announcement_id}")
async def delete_announcement(announcement_id: str, current_user: dict = Depends(require_admin)):
    """删除公告"""
    conn = await get_db_connection()
    try:
        await conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        await conn.commit()
        return {"success": True, "message": "公告已删除"}
    finally:
        await conn.close()


@router.post("/{announcement_id}/publish")
async def publish_announcement(announcement_id: str, current_user: dict = Depends(require_admin)):
    """发布公告"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE announcements SET is_published = 1, updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), announcement_id)
        )
        await conn.commit()
        return {"success": True, "message": "公告已发布"}
    finally:
        await conn.close()
