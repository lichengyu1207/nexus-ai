"""
团队协作相关Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class TeamRole(str, Enum):
    """团队角色枚举"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class TaskPermission(str, Enum):
    """任务权限枚举"""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


# ========== 团队模型 ==========

class TeamCreate(BaseModel):
    """创建团队请求"""
    name: str = Field(..., description="团队名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="团队描述", max_length=500)


class TeamUpdate(BaseModel):
    """更新团队请求"""
    name: Optional[str] = Field(None, description="团队名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="团队描述", max_length=500)


class TeamResponse(BaseModel):
    """团队响应"""
    id: str = Field(..., description="团队ID")
    name: str = Field(..., description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")
    owner_id: str = Field(..., description="所有者ID")
    member_count: int = Field(0, description="成员数量")
    created_at: str = Field(..., description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "team-123",
                "name": "房产分析团队",
                "description": "专业房产分析团队",
                "owner_id": "user-456",
                "member_count": 5,
                "created_at": "2024-01-01T10:00:00"
            }
        }


# ========== 成员模型 ==========

class TeamMemberAdd(BaseModel):
    """添加成员请求"""
    user_id: str = Field(..., description="用户ID")
    role: TeamRole = Field(TeamRole.MEMBER, description="角色")


class TeamMemberRoleUpdate(BaseModel):
    """更新成员角色请求"""
    role: TeamRole = Field(..., description="新角色")


class TeamMemberResponse(BaseModel):
    """成员响应"""
    team_id: str = Field(..., description="团队ID")
    user_id: str = Field(..., description="用户ID")
    role: TeamRole = Field(..., description="角色")
    joined_at: str = Field(..., description="加入时间")


# ========== 任务分享模型 ==========

class TaskShareCreate(BaseModel):
    """分享任务请求"""
    team_id: str = Field(..., description="团队ID")
    permission: TaskPermission = Field(TaskPermission.VIEW, description="权限")


class TaskShareResponse(BaseModel):
    """任务分享响应"""
    task_id: str = Field(..., description="任务ID")
    team_id: str = Field(..., description="团队ID")
    shared_by: str = Field(..., description="分享者ID")
    permission: TaskPermission = Field(..., description="权限")
    shared_at: str = Field(..., description="分享时间")


# ========== 评论模型 ==========

class CommentCreate(BaseModel):
    """创建评论请求"""
    content: str = Field(..., description="评论内容", min_length=1, max_length=2000)
    parent_id: Optional[str] = Field(None, description="父评论ID（回复时使用）")


class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: str = Field(..., description="评论内容", min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    """评论响应"""
    id: str = Field(..., description="评论ID")
    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[str] = Field(None, description="父评论ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    replies: List['CommentResponse'] = Field(default_factory=list, description="回复列表")


# ========== 通知模型 ==========

class NotificationType(str, Enum):
    """通知类型枚举"""
    MENTION = "mention"
    REPLY = "reply"
    SHARE = "share"
    COMMENT = "comment"


class NotificationResponse(BaseModel):
    """通知响应"""
    id: str = Field(..., description="通知ID")
    user_id: str = Field(..., description="接收者ID")
    type: NotificationType = Field(..., description="通知类型")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    is_read: bool = Field(False, description="是否已读")
    created_at: str = Field(..., description="创建时间")
