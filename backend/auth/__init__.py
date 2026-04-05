"""
认证模块初始化
Authentication Module

统一导出：
1. 传统认证函数
2. 五端统一认证中心 (from unified_auth_center.py)
"""

from datetime import datetime, timedelta
from typing import Optional, List, Callable
import json
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import uuid

from ..models import TokenData, DEFAULT_ROLE_PERMISSIONS
from ..database import UserDB

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        if isinstance(hashed_password, bytes):
            hashed_bytes = hashed_password
        else:
            hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None


def decode_expired_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    user = await UserDB.get_user_by_id(token_data.user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active", 1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional)) -> Optional[dict]:
    if token is None:
        return None
    
    try:
        token_data = decode_access_token(token)
        
        if token_data is None or token_data.user_id is None:
            return None
        
        user = await UserDB.get_user_by_id(token_data.user_id)
        
        if user is None or not user.get("is_active", 1):
            return None
        
        return user
    except Exception:
        return None


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_active", 1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户未激活"
        )
    return current_user


async def get_optional_user(token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False))) -> Optional[dict]:
    if token is None:
        return None
    
    try:
        token_data = decode_access_token(token)
        if token_data and token_data.user_id:
            return await UserDB.get_user_by_id(token_data.user_id)
    except Exception:
        pass
    
    return None


def generate_user_id() -> str:
    return str(uuid.uuid4())


def get_user_permissions(user: dict) -> List[str]:
    role = user.get("role", "user")
    
    default_perms = DEFAULT_ROLE_PERMISSIONS.get(role, [])
    
    custom_perms_str = user.get("permissions", "{}")
    try:
        custom_perms = json.loads(custom_perms_str) if isinstance(custom_perms_str, str) else custom_perms_str
    except:
        custom_perms = {}
    
    all_perms = set(default_perms)
    for perm, enabled in custom_perms.items():
        if enabled:
            all_perms.add(perm)
        else:
            all_perms.discard(perm)
    
    return list(all_perms)


def has_permission(user: dict, permission: str) -> bool:
    permissions = get_user_permissions(user)
    return permission in permissions


def is_admin(user: dict) -> bool:
    role = user.get("role", "user")
    return role in ("admin", "super_admin") or bool(user.get("is_admin"))


def is_super_admin(user: dict) -> bool:
    role = user.get("role", "user")
    return role == "super_admin"


def require_role(*allowed_roles: str) -> Callable:
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


def require_permission(permission_name: str) -> Callable:
    async def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if not has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，缺少权限: {permission_name}"
            )
        return current_user
    
    return permission_checker


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


from .unified_auth_center import (
    UnifiedAuthCenter,
    UserIdentity,
    OAuthClient,
    Token,
    AuthSession,
    AuthorizationCode,
    TokenType,
    GrantType,
    AuthScope,
    EndType,
    TokenGenerator,
    AuthMonitor,
    END_PERMISSIONS,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_optional_user",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "decode_expired_token",
    "generate_user_id",
    "get_user_permissions",
    "has_permission",
    "is_admin",
    "is_super_admin",
    "require_role",
    "require_permission",
    "require_admin",
    "get_current_admin_user",
    "require_super_admin",
    "oauth2_scheme",
    "oauth2_scheme_optional",
    "UnifiedAuthCenter",
    "UserIdentity",
    "OAuthClient",
    "Token",
    "AuthSession",
    "AuthorizationCode",
    "TokenType",
    "GrantType",
    "AuthScope",
    "EndType",
    "TokenGenerator",
    "AuthMonitor",
    "END_PERMISSIONS",
]
