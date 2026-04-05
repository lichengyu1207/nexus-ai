"""
公告系统 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from ..database import get_db_connection
from ..auth import get_current_user

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


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
async def get_announcements():
    """获取公告列表"""
    return []


@router.post("/", response_model=AnnouncementResponse)
async def create_announcement(data: AnnouncementCreate, current_user: dict = Depends(get_current_user)):
    """创建公告"""
    announcement_id = str(uuid.uuid4())
    return AnnouncementResponse(
        id=announcement_id,
        title=data.title,
        content=data.content,
        type=data.type,
        is_published=data.is_published,
        created_at=datetime.now()
    )
