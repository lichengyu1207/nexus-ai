"""
认证API路由
实现用户注册、登录、获取当前用户等端点
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import json
import logging

from ..models import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    UserUpdate,
    PasswordChange,
    UserStats
)
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    generate_user_id,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    decode_expired_token
)
from ..database import UserDB
from ..tasks.geocode_tasks import geocode_and_save_location
from ..services.audit_service import log_audit, ActionType, ResourceType, AuditStatus
from ..rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_client_info(request: Request):
    """获取客户端信息"""
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, background_tasks: BackgroundTasks, request: Request):
    """
    用户注册
    
    Args:
        user_data: 用户注册数据
        background_tasks: 后台任务
        
    Returns:
        UserResponse: 注册成功的用户信息
        
    Raises:
        HTTPException: 邮箱已存在 (409)
    """
    ip, user_agent = get_client_info(request)
    
    existing_user = await UserDB.get_user_by_email(user_data.email)
    if existing_user:
        await log_audit(
            action_type=ActionType.REGISTER,
            username=user_data.email,
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            error_message="邮箱已被注册",
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册"
        )
    
    user_id = generate_user_id()
    hashed_password = get_password_hash(user_data.password)
    
    from ..services.user_source import get_initial_integral
    
    user_source = user_data.source
    initial_integral = await get_initial_integral(user_source)
    
    # 新用户注册赠送1000积分
    register_bonus = 1000
    total_integral = initial_integral + register_bonus
    
    await UserDB.create_user(
        user_id=user_id,
        username=user_data.email.split("@")[0],
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role="user",
        integral=total_integral,
        source=user_source,
        referred_by=user_data.referred_by,
        referred_by_other=user_data.referred_by_other
    )
    
    # 记录用户来源
    from ..services.user_source import record_user_source
    query_params = dict(request.query_params) if request else {}
    await record_user_source(
        user_id=user_id,
        source=user_source,
        url_params=query_params,
        ip_address=ip,
        user_agent=user_agent
    )
    
    # 记录注册赠送积分日志
    from ..services.integral import IntegralService
    await IntegralService.record_integral_change(
        user_id=user_id,
        change=register_bonus,
        reason="register_bonus",
        admin_note="新用户注册赠送"
    )
    
    # 如果是粉丝专属福利，记录额外积分日志
    if initial_integral > 3:
        bonus = initial_integral - 3
        await IntegralService.record_integral_change(
            user_id=user_id,
            change=bonus,
            reason="source_bonus",
            admin_note=f"来源奖励: {user_source}"
        )
    
    await log_audit(
        action_type=ActionType.REGISTER,
        user_id=user_id,
        username=user_data.email,
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.USER,
        resource_id=user_id,
        status=AuditStatus.SUCCESS,
    )
    
    if user_data.privacy_version_id:
        from ..database import get_db_connection
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT id, version FROM privacy_policy_versions WHERE id = ?",
                (user_data.privacy_version_id,)
            )
            privacy_row = await cursor.fetchone()
            
            if privacy_row:
                import uuid as uuid_module
                from datetime import datetime as dt
                agreed_at = dt.now().isoformat()
                agreement_id = str(uuid_module.uuid4())
                
                await conn.execute('''
                    INSERT INTO user_privacy_agreements 
                    (id, user_id, version_id, version, ip_address, user_agent, agreed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (agreement_id, user_id, user_data.privacy_version_id, privacy_row['version'], ip, user_agent, agreed_at))
                
                await conn.execute('''
                    UPDATE users SET agreed_privacy_version = ?, agreed_privacy_at = ?
                    WHERE id = ?
                ''', (privacy_row['version'], agreed_at, user_id))
                
                await conn.commit()
        finally:
            await conn.close()
    
    logger.info(f"User registered: {user_data.email}, source: {user_source}, integral: {total_integral}")
    
    if user_data.address:
        background_tasks.add_task(
            geocode_and_save_location,
            user_id=user_id,
            address=user_data.address,
            source="registration"
        )
    
    return {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": "user",
        "is_admin": False,
        "permissions": {},
        "integral": total_integral,
        "membership_level": "free",
        "membership_expires": None,
        "source": user_source,
        "referred_by": user_data.referred_by,
        "referred_by_other": user_data.referred_by_other,
        "created_at": None,
        "register_bonus": register_bonus,
        "message": f"注册成功！赠送{register_bonus}积分"
    }


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, request: Request):
    """
    用户登录
    
    Args:
        user_data: 用户登录数据
        request: 请求对象
        
    Returns:
        Token: 访问令牌
        
    Raises:
        HTTPException: 邮箱或密码错误 (401), 限流 (429)
    """
    ip, user_agent = get_client_info(request)
    
    # 检查限流
    rate_limiter = await get_rate_limiter()
    allowed, message = rate_limiter.check_rate_limit(ip, user_data.email)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
        )
    
    user = await UserDB.get_user_by_email(user_data.email)
    
    if not user:
        rate_limiter.record_attempt(ip, user_data.email, success=False)
        await log_audit(
            action_type=ActionType.LOGIN,
            username=user_data.email,
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            error_message="用户不存在",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_data.password, user["hashed_password"]):
        rate_limiter.record_attempt(ip, user_data.email, success=False)
        await log_audit(
            action_type=ActionType.LOGIN,
            user_id=user["id"],
            username=user_data.email,
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            error_message="密码错误",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", 1):
        await log_audit(
            action_type=ActionType.LOGIN,
            user_id=user["id"],
            username=user_data.email,
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            error_message="用户已被禁用",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "user")
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # 记录登录成功
    rate_limiter.record_attempt(ip, user_data.email, success=True)
    
    await log_audit(
        action_type=ActionType.LOGIN,
        user_id=user["id"],
        username=user_data.email,
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.USER,
        resource_id=user["id"],
        status=AuditStatus.SUCCESS,
    )
    
    logger.info(f"User logged in: {user_data.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request):
    """
    刷新访问令牌（允许使用过期Token）
    
    Args:
        request: 请求对象
        
    Returns:
        Token: 新的访问令牌
    """
    from ..auth import decode_expired_token
    from fastapi import Header
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.replace("Bearer ", "")
    token_data = decode_expired_token(token)
    
    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await UserDB.get_user_by_id(token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", 1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "user")
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info(f"Token refreshed for user: {user['email']}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login/form", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """
    表单登录 (OAuth2兼容)
    
    Args:
        form_data: 表单数据
        request: 请求对象
        
    Returns:
        Token: 访问令牌
    """
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    user = await UserDB.get_user_by_email(form_data.username)
    
    if not user:
        await log_audit(
            action_type=ActionType.LOGIN,
            username=form_data.username,
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            error_message="用户不存在",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user["hashed_password"]):
        await log_audit(
            action_type=ActionType.LOGIN,
            user_id=user["id"],
            username=form_data.username,
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.FAILURE,
            error_message="密码错误",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "user")
        }
    )
    
    await log_audit(
        action_type=ActionType.LOGIN,
        user_id=user["id"],
        username=form_data.username,
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.USER,
        resource_id=user["id"],
        status=AuditStatus.SUCCESS,
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        UserResponse: 用户信息
    """
    from ..services.user_source import get_source_config
    
    source = current_user.get("source")
    source_config = get_source_config(source) if source else None
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user.get("username"),
        full_name=current_user.get("full_name"),
        role=current_user.get("role", "user"),
        is_admin=bool(current_user.get("is_admin")),
        permissions=json.loads(current_user.get("permissions", "{}")) if current_user.get("permissions") else {},
        integral=current_user.get("integral", 3),
        membership_level=current_user.get("membership_level", "free"),
        membership_expires=current_user.get("membership_expires"),
        source=source,
        source_name=source_config.get("name") if source_config else None,
        bonus_label=source_config.get("bonus_label") if source_config else None,
        referred_by=current_user.get("referred_by"),
        referred_by_other=current_user.get("referred_by_other"),
        created_at=current_user.get("created_at")
    )


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """
    更新当前用户信息
    
    Args:
        update_data: 更新数据
        current_user: 当前用户
        request: 请求对象
        
    Returns:
        UserResponse: 更新后的用户信息
    """
    user_id = current_user["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    old_values = {}
    new_values = {}
    
    if update_data.full_name is not None:
        old_values["full_name"] = current_user.get("full_name")
        new_values["full_name"] = update_data.full_name
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE users SET full_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (update_data.full_name, user_id)
            )
            await conn.commit()
        finally:
            await conn.close()
    
    if update_data.password is not None:
        old_values["password"] = "***"
        new_values["password"] = "***"
        hashed_password = get_password_hash(update_data.password)
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (hashed_password, user_id)
            )
            await conn.commit()
        finally:
            await conn.close()
    
    if old_values:
        await log_audit(
            action_type=ActionType.PROFILE_UPDATE,
            user_id=user_id,
            username=current_user.get("email"),
            ip_address=ip,
            user_agent=user_agent,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            old_value=old_values,
            new_value=new_values,
            status=AuditStatus.SUCCESS,
        )
    
    updated_user = await UserDB.get_user_by_id(user_id)
    
    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        full_name=updated_user.get("full_name"),
        role=updated_user.get("role", "user"),
        is_admin=bool(updated_user.get("is_admin")),
        permissions=json.loads(updated_user.get("permissions", "{}")) if updated_user.get("permissions") else {},
        created_at=updated_user.get("created_at")
    )


@router.put("/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """
    修改密码
    
    Args:
        password_data: 密码修改数据
        current_user: 当前用户
        request: 请求对象
        
    Returns:
        dict: 修改结果
        
    Raises:
        HTTPException: 旧密码错误 (400)
    """
    user_id = current_user["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not verify_password(password_data.old_password, user["hashed_password"]):
        await log_audit(
            action_type=ActionType.PASSWORD_CHANGE,
            user_id=user_id,
            username=user.get("email"),
            ip_address=ip,
            user_agent=user_agent,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            status=AuditStatus.FAILURE,
            error_message="旧密码错误",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )
    
    hashed_password = get_password_hash(password_data.new_password)
    
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (hashed_password, user_id)
        )
        await conn.commit()
    finally:
        await conn.close()
    
    await log_audit(
        action_type=ActionType.PASSWORD_CHANGE,
        user_id=user_id,
        username=user.get("email"),
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.USER,
        resource_id=user_id,
        status=AuditStatus.SUCCESS,
    )
    
    logger.info(f"Password changed for user: {user['email']}")
    
    return {"message": "密码修改成功"}


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """
    获取用户统计信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        UserStats: 用户统计
    """
    user_id = current_user["id"]
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ?",
            (user_id,)
        )
        total = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ? AND status = 'completed'",
            (user_id,)
        )
        completed = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ? AND status = 'running'",
            (user_id,)
        )
        running = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM analysis_tasks WHERE user_id = ? AND status = 'failed'",
            (user_id,)
        )
        failed = (await cursor.fetchone())[0]
    finally:
        await conn.close()
    
    return UserStats(
        total_tasks=total,
        completed_tasks=completed,
        running_tasks=running,
        failed_tasks=failed
    )


from ..database import get_db_connection
