"""
吉祥物管理API路由
提供表情管理、语录管理、统计等功能
需要 super_admin 权限
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
import os
import shutil
from pathlib import Path

from ...auth import get_current_user, require_admin, require_super_admin
from ...database import get_db_connection
from ...exceptions import ForbiddenException, NotFoundException, BadRequestException, ErrorCode
from ...services.audit_service import log_audit, ActionType, ResourceType, AuditStatus

router = APIRouter(prefix="/api/admin/mascot", tags=["admin-mascot"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "static" / "images" / "mascot" / "custom"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_client_info(request: Request):
    """获取客户端信息"""
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


class MascotEmotionCreate(BaseModel):
    """创建表情请求"""
    name: str = Field(..., min_length=1, max_length=50, description="表情名称")
    emotion_type: str = Field(..., description="表情类型: default, thinking, happy, confused, surprised, comforting")
    description: Optional[str] = Field(None, max_length=200, description="表情描述")
    is_active: bool = Field(default=True, description="是否启用")


class MascotEmotionUpdate(BaseModel):
    """更新表情请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="表情名称")
    description: Optional[str] = Field(None, max_length=200, description="表情描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class MascotEmotionResponse(BaseModel):
    """表情响应"""
    id: str
    name: str
    emotion_type: str
    file_path: str
    description: Optional[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class MascotEmotionListResponse(BaseModel):
    """表情列表响应"""
    emotions: List[MascotEmotionResponse]
    total: int


class MascotQuoteCreate(BaseModel):
    """创建语录请求"""
    category: str = Field(..., description="语录分类: default, thinking, happy, confused, surprised, comforting, random, easterEgg")
    content: str = Field(..., min_length=1, max_length=500, description="语录内容")
    is_active: bool = Field(default=True, description="是否启用")


class MascotQuoteUpdate(BaseModel):
    """更新语录请求"""
    category: Optional[str] = Field(None, description="语录分类")
    content: Optional[str] = Field(None, min_length=1, max_length=500, description="语录内容")
    is_active: Optional[bool] = Field(None, description="是否启用")


class MascotQuoteResponse(BaseModel):
    """语录响应"""
    id: str
    category: str
    content: str
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class MascotQuoteListResponse(BaseModel):
    """语录列表响应"""
    quotes: List[MascotQuoteResponse]
    total: int


class MascotStatsResponse(BaseModel):
    """吉祥物统计响应"""
    total_clicks: int
    total_interactions: int
    easter_egg_triggers: int
    by_emotion: Dict[str, int]
    by_scene: Dict[str, int]
    daily_stats: List[Dict[str, Any]]
    top_quotes: List[Dict[str, Any]]


class MascotInteractionLog(BaseModel):
    """互动日志"""
    interaction_type: str = Field(..., description="互动类型: click, drag, easter_egg, quote_shown")
    emotion: Optional[str] = Field(None, description="当前表情")
    scene: Optional[str] = Field(None, description="场景: dashboard, tasks, empty_state, etc.")
    quote_id: Optional[str] = Field(None, description="显示的语录ID")
    position: Optional[Dict[str, float]] = Field(None, description="位置坐标")


async def init_mascot_tables():
    """初始化吉祥物相关表"""
    conn = await get_db_connection()
    try:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS mascot_emotions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                emotion_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_mascot_emotions_type ON mascot_emotions(emotion_type);
            CREATE INDEX IF NOT EXISTS idx_mascot_emotions_active ON mascot_emotions(is_active);
            
            CREATE TABLE IF NOT EXISTS mascot_quotes (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_mascot_quotes_category ON mascot_quotes(category);
            CREATE INDEX IF NOT EXISTS idx_mascot_quotes_active ON mascot_quotes(is_active);
            
            CREATE TABLE IF NOT EXISTS mascot_interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                interaction_type TEXT NOT NULL,
                emotion TEXT,
                scene TEXT,
                quote_id TEXT,
                position_x REAL,
                position_y REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_mascot_interactions_user ON mascot_interactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_mascot_interactions_type ON mascot_interactions(interaction_type);
            CREATE INDEX IF NOT EXISTS idx_mascot_interactions_created ON mascot_interactions(created_at);
        """)
        await conn.commit()
    finally:
        await conn.close()


@router.on_event("startup")
async def startup():
    """启动时初始化表"""
    await init_mascot_tables()


@router.get("/emotions", response_model=MascotEmotionListResponse)
async def list_emotions(
    emotion_type: Optional[str] = Query(None, description="按表情类型筛选"),
    is_active: Optional[bool] = Query(None, description="按启用状态筛选"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_super_admin),
):
    """获取表情列表"""
    conn = await get_db_connection()
    try:
        conditions = ["1=1"]
        params = []
        
        if emotion_type:
            conditions.append("emotion_type = ?")
            params.append(emotion_type)
        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        where_clause = " AND ".join(conditions)
        
        cursor = await conn.execute(
            f"SELECT COUNT(*) FROM mascot_emotions WHERE {where_clause}",
            params
        )
        total = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            f"""
            SELECT id, name, emotion_type, file_path, description, is_active, created_at, updated_at
            FROM mascot_emotions
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        emotions = [
            MascotEmotionResponse(
                id=row["id"],
                name=row["name"],
                emotion_type=row["emotion_type"],
                file_path=row["file_path"],
                description=row["description"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
        
        return MascotEmotionListResponse(emotions=emotions, total=total)
    finally:
        await conn.close()


@router.post("/emotions", response_model=MascotEmotionResponse, status_code=status.HTTP_201_CREATED)
async def create_emotion(
    request: Request,
    file: UploadFile = File(..., description="SVG文件"),
    name: str = Form(..., description="表情名称"),
    emotion_type: str = Form(..., description="表情类型"),
    description: Optional[str] = Form(None, description="表情描述"),
    is_active: bool = Form(True, description="是否启用"),
    current_user: dict = Depends(require_super_admin),
):
    """上传新表情"""
    if not file.filename.endswith('.svg'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持SVG格式文件"
        )
    
    emotion_id = str(uuid.uuid4())
    file_name = f"{emotion_id}.svg"
    file_path = UPLOAD_DIR / file_name
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    db_path = f"/images/mascot/custom/{file_name}"
    
    conn = await get_db_connection()
    try:
        now = datetime.utcnow().isoformat()
        await conn.execute(
            """
            INSERT INTO mascot_emotions (id, name, emotion_type, file_path, description, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (emotion_id, name, emotion_type, db_path, description, 1 if is_active else 0, now, now)
        )
        await conn.commit()
        
        ip, user_agent = get_client_info(request)
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action=ActionType.CREATE,
            resource_type=ResourceType.SYSTEM_CONFIG,
            resource_id=emotion_id,
            details={"name": name, "emotion_type": emotion_type, "action": "create_mascot_emotion"},
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.SUCCESS,
        )
        
        return MascotEmotionResponse(
            id=emotion_id,
            name=name,
            emotion_type=emotion_type,
            file_path=db_path,
            description=description,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
    finally:
        await conn.close()


@router.put("/emotions/{emotion_id}", response_model=MascotEmotionResponse)
async def update_emotion(
    emotion_id: str,
    update_data: MascotEmotionUpdate,
    request: Request,
    current_user: dict = Depends(require_super_admin),
):
    """更新表情信息"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM mascot_emotions WHERE id = ?",
            (emotion_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise NotFoundException("表情不存在")
        
        updates = []
        params = []
        
        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)
        if update_data.description is not None:
            updates.append("description = ?")
            params.append(update_data.description)
        if update_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if update_data.is_active else 0)
        
        if updates:
            now = datetime.utcnow().isoformat()
            updates.append("updated_at = ?")
            params.extend([now, emotion_id])
            
            await conn.execute(
                f"UPDATE mascot_emotions SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
            
            ip, user_agent = get_client_info(request)
            await log_audit(
                user_id=current_user["id"],
                user_email=current_user["email"],
                action=ActionType.UPDATE,
                resource_type=ResourceType.SYSTEM_CONFIG,
                resource_id=emotion_id,
                details={"action": "update_mascot_emotion"},
                ip_address=ip,
                user_agent=user_agent,
                status=AuditStatus.SUCCESS,
            )
        
        cursor = await conn.execute(
            "SELECT * FROM mascot_emotions WHERE id = ?",
            (emotion_id,)
        )
        row = await cursor.fetchone()
        
        return MascotEmotionResponse(
            id=row["id"],
            name=row["name"],
            emotion_type=row["emotion_type"],
            file_path=row["file_path"],
            description=row["description"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    finally:
        await conn.close()


@router.delete("/emotions/{emotion_id}")
async def delete_emotion(
    emotion_id: str,
    request: Request,
    current_user: dict = Depends(require_super_admin),
):
    """删除表情"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM mascot_emotions WHERE id = ?",
            (emotion_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise NotFoundException("表情不存在")
        
        file_path = UPLOAD_DIR / f"{emotion_id}.svg"
        if file_path.exists():
            os.remove(file_path)
        
        await conn.execute(
            "DELETE FROM mascot_emotions WHERE id = ?",
            (emotion_id,)
        )
        await conn.commit()
        
        ip, user_agent = get_client_info(request)
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action=ActionType.DELETE,
            resource_type=ResourceType.SYSTEM_CONFIG,
            resource_id=emotion_id,
            details={"action": "delete_mascot_emotion", "name": row["name"]},
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.SUCCESS,
        )
        
        return {"message": "表情已删除"}
    finally:
        await conn.close()


@router.get("/quotes", response_model=MascotQuoteListResponse)
async def list_quotes(
    category: Optional[str] = Query(None, description="按分类筛选"),
    is_active: Optional[bool] = Query(None, description="按启用状态筛选"),
    search: Optional[str] = Query(None, description="搜索内容"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_super_admin),
):
    """获取语录列表"""
    conn = await get_db_connection()
    try:
        conditions = ["1=1"]
        params = []
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)
        if search:
            conditions.append("content LIKE ?")
            params.append(f"%{search}%")
        
        where_clause = " AND ".join(conditions)
        
        cursor = await conn.execute(
            f"SELECT COUNT(*) FROM mascot_quotes WHERE {where_clause}",
            params
        )
        total = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            f"""
            SELECT id, category, content, is_active, created_at, updated_at
            FROM mascot_quotes
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        quotes = [
            MascotQuoteResponse(
                id=row["id"],
                category=row["category"],
                content=row["content"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
        
        return MascotQuoteListResponse(quotes=quotes, total=total)
    finally:
        await conn.close()


@router.post("/quotes", response_model=MascotQuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: MascotQuoteCreate,
    request: Request,
    current_user: dict = Depends(require_super_admin),
):
    """创建语录"""
    quote_id = str(uuid.uuid4())
    
    conn = await get_db_connection()
    try:
        now = datetime.utcnow().isoformat()
        await conn.execute(
            """
            INSERT INTO mascot_quotes (id, category, content, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (quote_id, quote_data.category, quote_data.content, 1 if quote_data.is_active else 0, now, now)
        )
        await conn.commit()
        
        ip, user_agent = get_client_info(request)
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action=ActionType.CREATE,
            resource_type=ResourceType.SYSTEM_CONFIG,
            resource_id=quote_id,
            details={"category": quote_data.category, "action": "create_mascot_quote"},
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.SUCCESS,
        )
        
        return MascotQuoteResponse(
            id=quote_id,
            category=quote_data.category,
            content=quote_data.content,
            is_active=quote_data.is_active,
            created_at=now,
            updated_at=now,
        )
    finally:
        await conn.close()


@router.put("/quotes/{quote_id}", response_model=MascotQuoteResponse)
async def update_quote(
    quote_id: str,
    update_data: MascotQuoteUpdate,
    request: Request,
    current_user: dict = Depends(require_super_admin),
):
    """更新语录"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM mascot_quotes WHERE id = ?",
            (quote_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise NotFoundException("语录不存在")
        
        updates = []
        params = []
        
        if update_data.category is not None:
            updates.append("category = ?")
            params.append(update_data.category)
        if update_data.content is not None:
            updates.append("content = ?")
            params.append(update_data.content)
        if update_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if update_data.is_active else 0)
        
        if updates:
            now = datetime.utcnow().isoformat()
            updates.append("updated_at = ?")
            params.extend([now, quote_id])
            
            await conn.execute(
                f"UPDATE mascot_quotes SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
            
            ip, user_agent = get_client_info(request)
            await log_audit(
                user_id=current_user["id"],
                user_email=current_user["email"],
                action=ActionType.UPDATE,
                resource_type=ResourceType.SYSTEM_CONFIG,
                resource_id=quote_id,
                details={"action": "update_mascot_quote"},
                ip_address=ip,
                user_agent=user_agent,
                status=AuditStatus.SUCCESS,
            )
        
        cursor = await conn.execute(
            "SELECT * FROM mascot_quotes WHERE id = ?",
            (quote_id,)
        )
        row = await cursor.fetchone()
        
        return MascotQuoteResponse(
            id=row["id"],
            category=row["category"],
            content=row["content"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    finally:
        await conn.close()


@router.delete("/quotes/{quote_id}")
async def delete_quote(
    quote_id: str,
    request: Request,
    current_user: dict = Depends(require_super_admin),
):
    """删除语录"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM mascot_quotes WHERE id = ?",
            (quote_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise NotFoundException("语录不存在")
        
        await conn.execute(
            "DELETE FROM mascot_quotes WHERE id = ?",
            (quote_id,)
        )
        await conn.commit()
        
        ip, user_agent = get_client_info(request)
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action=ActionType.DELETE,
            resource_type=ResourceType.SYSTEM_CONFIG,
            resource_id=quote_id,
            details={"action": "delete_mascot_quote", "category": row["category"]},
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.SUCCESS,
        )
        
        return {"message": "语录已删除"}
    finally:
        await conn.close()


@router.post("/interactions")
async def log_interaction(
    interaction: MascotInteractionLog,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """记录吉祥物互动"""
    interaction_id = str(uuid.uuid4())
    
    conn = await get_db_connection()
    try:
        now = datetime.utcnow().isoformat()
        await conn.execute(
            """
            INSERT INTO mascot_interactions (id, user_id, interaction_type, emotion, scene, quote_id, position_x, position_y, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interaction_id,
                current_user.get("id"),
                interaction.interaction_type,
                interaction.emotion,
                interaction.scene,
                interaction.quote_id,
                interaction.position.get("x") if interaction.position else None,
                interaction.position.get("y") if interaction.position else None,
                now
            )
        )
        await conn.commit()
        
        return {"message": "互动已记录", "id": interaction_id}
    finally:
        await conn.close()


@router.get("/stats", response_model=MascotStatsResponse)
async def get_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: dict = Depends(require_super_admin),
):
    """获取吉祥物统计"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM mascot_interactions WHERE interaction_type = 'click'"
        )
        total_clicks = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM mascot_interactions"
        )
        total_interactions = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM mascot_interactions WHERE interaction_type = 'easter_egg'"
        )
        easter_egg_triggers = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            """
            SELECT emotion, COUNT(*) as count
            FROM mascot_interactions
            WHERE emotion IS NOT NULL
            GROUP BY emotion
            ORDER BY count DESC
            """
        )
        emotion_rows = await cursor.fetchall()
        by_emotion = {row["emotion"]: row["count"] for row in emotion_rows}
        
        cursor = await conn.execute(
            """
            SELECT scene, COUNT(*) as count
            FROM mascot_interactions
            WHERE scene IS NOT NULL
            GROUP BY scene
            ORDER BY count DESC
            """
        )
        scene_rows = await cursor.fetchall()
        by_scene = {row["scene"]: row["count"] for row in scene_rows}
        
        cursor = await conn.execute(
            f"""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM mascot_interactions
            WHERE created_at >= DATE('now', '-{days} days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
        )
        daily_rows = await cursor.fetchall()
        daily_stats = [{"date": row["date"], "count": row["count"]} for row in daily_rows]
        
        cursor = await conn.execute(
            """
            SELECT q.content, q.category, COUNT(*) as shown_count
            FROM mascot_interactions i
            JOIN mascot_quotes q ON i.quote_id = q.id
            WHERE i.quote_id IS NOT NULL
            GROUP BY q.id
            ORDER BY shown_count DESC
            LIMIT 10
            """
        )
        quote_rows = await cursor.fetchall()
        top_quotes = [
            {"content": row["content"], "category": row["category"], "shown_count": row["shown_count"]}
            for row in quote_rows
        ]
        
        return MascotStatsResponse(
            total_clicks=total_clicks,
            total_interactions=total_interactions,
            easter_egg_triggers=easter_egg_triggers,
            by_emotion=by_emotion,
            by_scene=by_scene,
            daily_stats=daily_stats,
            top_quotes=top_quotes,
        )
    finally:
        await conn.close()


@router.post("/quotes/batch")
async def batch_create_quotes(
    quotes: List[MascotQuoteCreate],
    request: Request,
    current_user: dict = Depends(require_super_admin),
):
    """批量创建语录"""
    conn = await get_db_connection()
    try:
        now = datetime.utcnow().isoformat()
        created_ids = []
        
        for quote in quotes:
            quote_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO mascot_quotes (id, category, content, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (quote_id, quote.category, quote.content, 1 if quote.is_active else 0, now, now)
            )
            created_ids.append(quote_id)
        
        await conn.commit()
        
        ip, user_agent = get_client_info(request)
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action=ActionType.CREATE,
            resource_type=ResourceType.SYSTEM_CONFIG,
            resource_id="batch",
            details={"action": "batch_create_mascot_quotes", "count": len(quotes)},
            ip_address=ip,
            user_agent=user_agent,
            status=AuditStatus.SUCCESS,
        )
        
        return {"message": f"成功创建 {len(quotes)} 条语录", "ids": created_ids}
    finally:
        await conn.close()
