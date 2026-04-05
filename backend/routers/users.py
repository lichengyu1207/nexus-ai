"""
用户设置API路由
"""
import os
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from ..auth import get_current_user, verify_password, get_password_hash
from ..database import UserDB
from ..tasks.geocode_tasks import geocode_and_save_location

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

UPLOAD_DIR = "uploads/avatars"


class ProfileUpdate(BaseModel):
    """资料更新模型"""
    full_name: Optional[str] = None
    username: Optional[str] = None
    address: Optional[str] = None


class PasswordUpdate(BaseModel):
    """密码更新模型"""
    current_password: str
    new_password: str


class PreferencesUpdate(BaseModel):
    """偏好更新模型"""
    theme: Optional[str] = None
    language: Optional[str] = None
    notification_preferences: Optional[dict] = None
    mascot: Optional[dict] = None


class MascotPreferencesResponse(BaseModel):
    """吉祥物偏好响应模型"""
    enabled: bool = True
    display_mode: str = "all"
    show_bubble: bool = True
    show_onboarding: bool = True


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    theme: str
    language: str
    notification_preferences: dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PreferencesResponse(BaseModel):
    """偏好响应模型"""
    theme: str
    language: str
    notification_preferences: dict


def ensure_upload_dir():
    """确保上传目录存在"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user = await UserDB.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    notification_prefs = {}
    if user.get("notification_preferences"):
        try:
            import json
            notification_prefs = json.loads(user["notification_preferences"])
        except:
            pass
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        avatar_url=user.get("avatar_url"),
        role=user.get("role", "user"),
        theme=user.get("theme", "system"),
        language=user.get("language", "zh"),
        notification_preferences=notification_prefs,
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at")
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """更新用户资料"""
    if profile_data.username:
        existing_user = await UserDB.get_user_by_username(profile_data.username)
        if existing_user and existing_user["id"] != current_user["id"]:
            raise HTTPException(status_code=400, detail="用户名已被使用")
    
    success = await UserDB.update_profile(
        user_id=current_user["id"],
        full_name=profile_data.full_name,
        username=profile_data.username
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    if profile_data.address:
        background_tasks.add_task(
            geocode_and_save_location,
            user_id=current_user["id"],
            address=profile_data.address,
            source="interest"
        )
    
    return await get_current_user_info(current_user)


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """上传头像"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    ensure_upload_dir()
    
    file_ext = os.path.splitext(file.filename or "image.jpg")[1]
    filename = f"{current_user['id']}_{uuid.uuid4().hex[:8]}{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    avatar_url = f"/uploads/avatars/{filename}"
    
    success = await UserDB.update_avatar(current_user["id"], avatar_url)
    if not success:
        raise HTTPException(status_code=500, detail="保存头像失败")
    
    return {"avatar_url": avatar_url}


@router.put("/me/password")
async def update_password(
    password_data: PasswordUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新密码"""
    user = await UserDB.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not verify_password(password_data.current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6位")
    
    hashed_password = get_password_hash(password_data.new_password)
    success = await UserDB.update_password(current_user["id"], hashed_password)
    
    if not success:
        raise HTTPException(status_code=500, detail="密码更新失败")
    
    return {"message": "密码已更新"}


@router.get("/me/preferences", response_model=PreferencesResponse)
async def get_preferences(current_user: dict = Depends(get_current_user)):
    """获取用户偏好设置"""
    prefs = await UserDB.get_preferences(current_user["id"])
    
    if not prefs:
        return PreferencesResponse(
            theme="system",
            language="zh",
            notification_preferences={}
        )
    
    notification_prefs = prefs.get("notification_preferences", {})
    if isinstance(notification_prefs, str):
        try:
            import json
            notification_prefs = json.loads(notification_prefs)
        except:
            notification_prefs = {}
    
    return PreferencesResponse(
        theme=prefs.get("theme", "system"),
        language=prefs.get("language", "zh"),
        notification_preferences=notification_prefs
    )


@router.put("/me/preferences")
async def update_preferences(
    prefs_data: PreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新用户偏好设置"""
    if prefs_data.theme and prefs_data.theme not in ["light", "dark", "system"]:
        raise HTTPException(status_code=400, detail="无效的主题设置")
    
    if prefs_data.language and prefs_data.language not in ["zh", "en"]:
        raise HTTPException(status_code=400, detail="无效的语言设置")
    
    success = await UserDB.update_preferences(
        user_id=current_user["id"],
        theme=prefs_data.theme,
        language=prefs_data.language,
        notification_preferences=prefs_data.notification_preferences
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新偏好设置失败")
    
    return {"message": "偏好设置已更新"}


@router.get("/me/preferences/mascot", response_model=MascotPreferencesResponse)
async def get_mascot_preferences(current_user: dict = Depends(get_current_user)):
    """获取吉祥物偏好设置"""
    prefs = await UserDB.get_preferences(current_user["id"])
    
    default_prefs = MascotPreferencesResponse()
    
    if not prefs:
        return default_prefs
    
    mascot_prefs = prefs.get("mascot", {})
    if isinstance(mascot_prefs, str):
        try:
            import json
            mascot_prefs = json.loads(mascot_prefs)
        except:
            mascot_prefs = {}
    
    return MascotPreferencesResponse(
        enabled=mascot_prefs.get("enabled", True),
        display_mode=mascot_prefs.get("display_mode", "all"),
        show_bubble=mascot_prefs.get("show_bubble", True),
        show_onboarding=mascot_prefs.get("show_onboarding", True)
    )


@router.put("/me/preferences/mascot")
async def update_mascot_preferences(
    mascot_data: MascotPreferencesResponse,
    current_user: dict = Depends(get_current_user)
):
    """更新吉祥物偏好设置"""
    if mascot_data.display_mode not in ["all", "empty"]:
        raise HTTPException(status_code=400, detail="无效的显示模式")
    
    mascot_prefs = {
        "enabled": mascot_data.enabled,
        "display_mode": mascot_data.display_mode,
        "show_bubble": mascot_data.show_bubble,
        "show_onboarding": mascot_data.show_onboarding
    }
    
    success = await UserDB.update_preferences(
        user_id=current_user["id"],
        mascot=mascot_prefs
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新吉祥物偏好设置失败")
    
    return {"message": "吉祥物偏好设置已更新", "preferences": mascot_prefs}


@router.get("/me/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """获取用户统计数据"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        # 获取任务统计
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ?",
            (current_user["id"],)
        )
        total_tasks = (await cursor.fetchone())[0]
        
        # 获取报告统计
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM analysis_reports WHERE user_id = ?",
            (current_user["id"],)
        )
        total_reports = (await cursor.fetchone())[0]
    finally:
        await conn.close()
    
    user = await UserDB.get_user_by_id(current_user["id"])
    
    return {
        "total_reports": total_reports,
        "total_tasks": total_tasks,
        "available_integral": user.get("integral", 0) if user else 0,
        "membership_level": user.get("membership_level", "免费用户") if user else "免费用户"
    }
