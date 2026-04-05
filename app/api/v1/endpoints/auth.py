from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services.user_service import user_service, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User
from app.api.v1.dependencies.auth import get_current_user, get_current_active_user
from app.api.v1.schemas.auth import Token, TokenData, UserCreate, UserLogin, UserResponse, UserUpdate

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 创建用户
        created_user = user_service.create_user(
            db=db,
            username=user.username,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            phone_number=user.phone_number
        )
        
        # 转换为响应模型
        return UserResponse(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            full_name=created_user.full_name,
            phone_number=created_user.phone_number,
            role=created_user.role,
            status=created_user.status,
            created_at=created_user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    # 认证用户
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        role=current_user.role,
        status=current_user.status,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(user_update: UserUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """更新当前用户信息"""
    # 更新用户资料
    updated_user = user_service.update_user_profile(
        db=db,
        user_id=current_user.id,
        full_name=user_update.full_name,
        phone_number=user_update.phone_number
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        phone_number=updated_user.phone_number,
        role=updated_user.role,
        status=updated_user.status,
        created_at=updated_user.created_at
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """修改密码"""
    # 修改密码
    success = user_service.change_password(
        db=db,
        user_id=current_user.id,
        old_password=old_password,
        new_password=new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    return {"message": "Password changed successfully"}
