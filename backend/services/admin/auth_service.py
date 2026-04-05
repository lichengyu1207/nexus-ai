# -*- coding: utf-8 -*-
"""
管理员认证与RBAC权限服务
登录认证、Token管理、权限验证
"""
import asyncio
import hashlib
import secrets
import time
import logging
import os
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

from ..database.high_performance_db import get_db_service

logger = logging.getLogger(__name__)


class AdminRole(Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    AUDITOR = "auditor"
    AGENT_ADMIN = "agent_admin"


@dataclass
class AdminUser:
    id: str
    username: str
    email: str
    role: str
    permissions: Dict[str, Any]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    def has_permission(self, permission: str) -> bool:
        if self.is_superuser:
            return True
        
        if self.permissions.get("all"):
            return True
        
        return permission in self.permissions.get("permissions", [])


@dataclass
class TokenPayload:
    admin_id: str
    username: str
    role: str
    permissions: List[str]
    exp: datetime
    iat: datetime
    jti: str


class JWTManager:
    """JWT Token管理器"""
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire: int = 60,
        refresh_token_expire: int = 60 * 24 * 7
    ):
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", os.getenv("SECRET_KEY", "default-secret-key-change-me")
        )
        self.algorithm = algorithm
        self.access_token_expire = access_token_expire
        self.refresh_token_expire = refresh_token_expire
    
    def create_access_token(
        self,
        admin_id: str,
        username: str,
        role: str,
        permissions: List[str]
    ) -> str:
        """创建访问令牌"""
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.access_token_expire)
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": admin_id,
            "username": username,
            "role": role,
            "permissions": permissions[:50],
            "exp": exp,
            "iat": now,
            "jti": jti,
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, admin_id: str) -> str:
        """创建刷新令牌"""
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.refresh_token_expire)
        jti = secrets.token_urlsafe(32)
        
        payload = {
            "sub": admin_id,
            "exp": exp,
            "iat": now,
            "jti": jti,
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def get_token_hash(self, token: str) -> str:
        """获取令牌哈希"""
        return hashlib.sha256(token.encode()).hexdigest()


class AdminAuthService:
    """管理员认证服务"""
    
    def __init__(self):
        self.jwt_manager = JWTManager()
        self._token_blacklist: Set[str] = set()
        self._max_login_attempts = int(os.getenv("ADMIN_MAX_LOGIN_ATTEMPTS", "5"))
        self._lockout_minutes = int(os.getenv("ADMIN_LOCKOUT_MINUTES", "30"))
    
    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """管理员认证"""
        db = await get_db_service()
        
        admin = await db.fetchrow_read("""
            SELECT id, username, email, password_hash, role, permissions,
                   is_active, is_superuser, created_at, last_login,
                   failed_login_count, locked_until
            FROM admin_users
            WHERE username = $1 OR email = $1
        """, username)
        
        if not admin:
            await self._record_login_attempt(None, ip_address, False, "用户不存在")
            raise AuthenticationError("用户名或密码错误")
        
        if admin["locked_until"] and admin["locked_until"] > datetime.utcnow():
            await self._record_login_attempt(admin["id"], ip_address, False, "账户锁定")
            raise AuthenticationError(f"账户已锁定，请{self._lockout_minutes}分钟后再试")
        
        if not admin["is_active"]:
            await self._record_login_attempt(admin["id"], ip_address, False, "账户禁用")
            raise AuthenticationError("账户已被禁用")
        
        password_hash = self._hash_password(password)
        
        if admin["password_hash"] != password_hash:
            await self._handle_failed_login(admin["id"], ip_address)
            raise AuthenticationError("用户名或密码错误")
        
        await self._reset_failed_attempts(admin["id"])
        
        permissions = admin["permissions"].get("permissions", [])
        if admin["is_superuser"]:
            permissions = ["*"]
        
        access_token = self.jwt_manager.create_access_token(
            str(admin["id"]),
            admin["username"],
            admin["role"],
            permissions
        )
        
        refresh_token = self.jwt_manager.create_refresh_token(str(admin["id"]))
        
        await self._save_session(
            admin["id"],
            access_token,
            refresh_token,
            ip_address,
            user_agent
        )
        
        await self._update_last_login(admin["id"])
        
        await self._record_login_attempt(admin["id"], ip_address, True)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_manager.access_token_expire * 60,
            "admin": {
                "id": str(admin["id"]),
                "username": admin["username"],
                "email": admin["email"],
                "role": admin["role"],
                "permissions": permissions
            }
        }
    
    async def logout(self, token: str) -> bool:
        """登出"""
        payload = self.jwt_manager.decode_token(token)
        if not payload:
            return False
        
        jti = payload.get("jti")
        if jti:
            self._token_blacklist.add(jti)
        
        token_hash = self.jwt_manager.get_token_hash(token)
        
        db = await get_db_service()
        await db.execute_write("""
            UPDATE admin_sessions
            SET is_revoked = true
            WHERE token_hash = $1
        """, token_hash)
        
        return True
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新令牌"""
        payload = self.jwt_manager.decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("无效的刷新令牌")
        
        admin_id = payload.get("sub")
        jti = payload.get("jti")
        
        if jti in self._token_blacklist:
            raise AuthenticationError("令牌已被撤销")
        
        db = await get_db_service()
        
        admin = await db.fetchrow_read("""
            SELECT id, username, email, role, permissions, is_active, is_superuser
            FROM admin_users
            WHERE id = $1
        """, admin_id)
        
        if not admin or not admin["is_active"]:
            raise AuthenticationError("用户不存在或已禁用")
        
        permissions = admin["permissions"].get("permissions", [])
        if admin["is_superuser"]:
            permissions = ["*"]
        
        new_access_token = self.jwt_manager.create_access_token(
            str(admin["id"]),
            admin["username"],
            admin["role"],
            permissions
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": self.jwt_manager.access_token_expire * 60
        }
    
    async def validate_token(self, token: str) -> Optional[AdminUser]:
        """验证令牌"""
        payload = self.jwt_manager.decode_token(token)
        
        if not payload:
            return None
        
        jti = payload.get("jti")
        if jti in self._token_blacklist:
            return None
        
        admin_id = payload.get("sub")
        
        db = await get_db_service()
        
        session = await db.fetchrow_read("""
            SELECT is_revoked, expires_at
            FROM admin_sessions
            WHERE admin_id = $1 AND token_hash = $2
        """, admin_id, self.jwt_manager.get_token_hash(token))
        
        if session and (session["is_revoked"] or session["expires_at"] < datetime.utcnow()):
            return None
        
        admin = await db.fetchrow_read("""
            SELECT id, username, email, role, permissions, is_active, is_superuser,
                   created_at, last_login
            FROM admin_users
            WHERE id = $1
        """, admin_id)
        
        if not admin or not admin["is_active"]:
            return None
        
        return AdminUser(
            id=str(admin["id"]),
            username=admin["username"],
            email=admin["email"],
            role=admin["role"],
            permissions=admin["permissions"],
            is_active=admin["is_active"],
            is_superuser=admin["is_superuser"],
            created_at=admin["created_at"],
            last_login=admin["last_login"]
        )
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def _handle_failed_login(self, admin_id: str, ip_address: str):
        """处理登录失败"""
        db = await get_db_service()
        
        await db.execute_write("""
            UPDATE admin_users
            SET failed_login_count = failed_login_count + 1,
                locked_until = CASE 
                    WHEN failed_login_count + 1 >= $1 
                    THEN CURRENT_TIMESTAMP + INTERVAL '$2 minutes'
                    ELSE locked_until
                END
            WHERE id = $3
        """, self._max_login_attempts, self._lockout_minutes, admin_id)
    
    async def _reset_failed_attempts(self, admin_id: str):
        """重置失败次数"""
        db = await get_db_service()
        await db.execute_write("""
            UPDATE admin_users
            SET failed_login_count = 0, locked_until = NULL
            WHERE id = $1
        """, admin_id)
    
    async def _save_session(
        self,
        admin_id: str,
        access_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str
    ):
        """保存会话"""
        db = await get_db_service()
        
        await db.execute_write("""
            INSERT INTO admin_sessions (
                admin_id, token_hash, refresh_token_hash,
                ip_address, user_agent, expires_at, refresh_expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
            admin_id,
            self.jwt_manager.get_token_hash(access_token),
            self.jwt_manager.get_token_hash(refresh_token),
            ip_address,
            user_agent,
            datetime.utcnow() + timedelta(minutes=self.jwt_manager.access_token_expire),
            datetime.utcnow() + timedelta(minutes=self.jwt_manager.refresh_token_expire)
        )
    
    async def _update_last_login(self, admin_id: str):
        """更新最后登录时间"""
        db = await get_db_service()
        await db.execute_write("""
            UPDATE admin_users
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
            WHERE id = $1
        """, admin_id)
    
    async def _record_login_attempt(
        self,
        admin_id: Optional[str],
        ip_address: str,
        success: bool,
        message: str = None
    ):
        """记录登录尝试"""
        db = await get_db_service()
        
        await db.execute_write("""
            INSERT INTO admin_audit_logs (
                admin_id, action, resource_type, ip_address,
                new_value, created_at
            )
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """,
            admin_id,
            "login_success" if success else "login_failed",
            "auth",
            ip_address,
            {"success": success, "message": message}
        )


class RBACService:
    """RBAC权限服务"""
    
    def __init__(self):
        self._permission_cache: Dict[str, Set[str]] = {}
        self._cache_ttl = 300
        self._cache_time: Dict[str, float] = {}
    
    async def get_permissions_for_role(self, role_name: str) -> Set[str]:
        """获取角色的权限"""
        now = time.time()
        
        if role_name in self._permission_cache:
            if now - self._cache_time.get(role_name, 0) < self._cache_ttl:
                return self._permission_cache[role_name]
        
        db = await get_db_service()
        
        permissions = await db.execute_read("""
            SELECT p.code
            FROM admin_permissions p
            JOIN admin_role_permissions rp ON p.id = rp.permission_id
            JOIN admin_roles r ON r.id = rp.role_id
            WHERE r.name = $1
        """, role_name)
        
        perm_set = {p["code"] for p in permissions}
        
        self._permission_cache[role_name] = perm_set
        self._cache_time[role_name] = now
        
        return perm_set
    
    async def check_permission(
        self,
        admin: AdminUser,
        resource: str,
        action: str
    ) -> bool:
        """检查权限"""
        if admin.is_superuser:
            return True
        
        if admin.permissions.get("all"):
            return True
        
        permissions = admin.permissions.get("permissions", [])
        
        wildcard = f"{resource}:*"
        if wildcard in permissions:
            return True
        
        specific = f"{resource}:{action}"
        if specific in permissions:
            return True
        
        if "*" in permissions:
            return True
        
        role_perms = await self.get_permissions_for_role(admin.role)
        
        if wildcard in role_perms or specific in role_perms or "*" in role_perms:
            return True
        
        return False
    
    async def get_all_permissions(self) -> List[Dict[str, Any]]:
        """获取所有权限"""
        db = await get_db_service()
        
        permissions = await db.execute_read("""
            SELECT id, code, name, resource, action, description
            FROM admin_permissions
            ORDER BY resource, action
        """)
        
        return [dict(p) for p in permissions]
    
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """获取所有角色"""
        db = await get_db_service()
        
        roles = await db.execute_read("""
            SELECT r.id, r.name, r.description, r.level, r.is_system, r.permissions,
                   COUNT(rp.permission_id) as permission_count
            FROM admin_roles r
            LEFT JOIN admin_role_permissions rp ON r.id = rp.role_id
            GROUP BY r.id
            ORDER BY r.level DESC
        """)
        
        return [dict(r) for r in roles]
    
    async def create_role(
        self,
        name: str,
        description: str,
        permissions: List[str],
        level: int = 0
    ) -> str:
        """创建角色"""
        db = await get_db_service()
        
        role_id = await db.fetchval_read("""
            INSERT INTO admin_roles (name, description, level, permissions)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, name, description, level, {"permissions": permissions})
        
        for perm_code in permissions:
            await db.execute_write("""
                INSERT INTO admin_role_permissions (role_id, permission_id)
                SELECT $1, id FROM admin_permissions WHERE code = $2
            """, role_id, perm_code)
        
        return str(role_id)
    
    async def update_role_permissions(
        self,
        role_name: str,
        permissions: List[str]
    ) -> bool:
        """更新角色权限"""
        db = await get_db_service()
        
        role = await db.fetchrow_read("""
            SELECT id FROM admin_roles WHERE name = $1
        """, role_name)
        
        if not role:
            return False
        
        await db.execute_write("""
            DELETE FROM admin_role_permissions WHERE role_id = $1
        """, role["id"])
        
        for perm_code in permissions:
            await db.execute_write("""
                INSERT INTO admin_role_permissions (role_id, permission_id)
                SELECT $1, id FROM admin_permissions WHERE code = $2
            """, role["id"], perm_code)
        
        if role_name in self._permission_cache:
            del self._permission_cache[role_name]
        
        return True
    
    def invalidate_cache(self, role_name: str = None):
        """清除缓存"""
        if role_name:
            self._permission_cache.pop(role_name, None)
            self._cache_time.pop(role_name, None)
        else:
            self._permission_cache.clear()
            self._cache_time.clear()


class AuthenticationError(Exception):
    """认证错误"""
    pass


class PermissionDeniedError(Exception):
    """权限拒绝错误"""
    pass


admin_auth_service: Optional[AdminAuthService] = None
rbac_service: Optional[RBACService] = None


async def get_admin_auth_service() -> AdminAuthService:
    """获取管理员认证服务"""
    global admin_auth_service
    if admin_auth_service is None:
        admin_auth_service = AdminAuthService()
    return admin_auth_service


async def get_rbac_service() -> RBACService:
    """获取RBAC服务"""
    global rbac_service
    if rbac_service is None:
        rbac_service = RBACService()
    return rbac_service
