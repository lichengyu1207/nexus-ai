# -*- coding: utf-8 -*-
"""
Skill Market Router
API endpoints for skill marketplace
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from backend.services.skill.skill_registry import (
    SkillRegistry, Skill, SkillType, SkillCategory, SkillStatus,
    get_skill_registry, init_skill_registry
)
from backend.services.skill.point_service import (
    PointService, get_point_service, init_point_service
)
from backend.database_pg import get_db

router = APIRouter(prefix="/api/skills", tags=["Skill Market"])


class SkillCreateRequest(BaseModel):
    name: str
    description: str
    type: str = SkillType.BUILTIN
    category: str = SkillCategory.GENERAL
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    applicable_agents: List[str] = Field(default_factory=list)
    cost_points: int = 0
    version: str = "1.0.0"
    tags: List[str] = Field(default_factory=list)
    code_config: Dict[str, Any] = Field(default_factory=dict)
    icon_url: Optional[str] = None


class SkillUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    cost_points: Optional[int] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    icon_url: Optional[str] = None


class SkillPurchaseRequest(BaseModel):
    user_id: str


class SkillInvokeRequest(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = None


class SkillReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class SkillListResponse(BaseModel):
    skills: List[Dict[str, Any]]
    total: int
    page: int
    size: int


class WalletResponse(BaseModel):
    total_points: int
    available_points: int
    frozen_points: int
    withdrawable_points: int


async def get_skill_registry_dep():
    from backend.database_pg import PostgreSQLConnectionPool
    pool = await PostgreSQLConnectionPool.get_instance()
    if pool._pool is None:
        await pool._initialize()
    registry = get_skill_registry()
    if not registry:
        registry = await init_skill_registry(pool._pool)
    return registry


async def get_point_service_dep():
    from backend.database_pg import PostgreSQLConnectionPool
    pool = await PostgreSQLConnectionPool.get_instance()
    if pool._pool is None:
        await pool._initialize()
    service = get_point_service()
    if not service:
        service = await init_point_service(pool._pool)
    return service


@router.get("", response_model=SkillListResponse)
async def list_skills(
    category: Optional[str] = Query(None),
    type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("DESC"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    skills, total = await registry.list_skills(
        category=category,
        skill_type=type,
        status=status,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size
    )
    
    return SkillListResponse(
        skills=[s.to_dict() for s in skills],
        total=total,
        page=page,
        size=size
    )


@router.post("", response_model=Dict[str, Any])
async def create_skill(
    request: SkillCreateRequest,
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    skill = Skill(
        id="",
        name=request.name,
        description=request.description,
        type=request.type,
        category=request.category,
        input_schema=request.input_schema,
        output_schema=request.output_schema,
        dependencies=request.dependencies,
        applicable_agents=request.applicable_agents,
        cost_points=request.cost_points,
        version=request.version,
        tags=request.tags,
        code_config=request.code_config,
        icon_url=request.icon_url,
        status=SkillStatus.DRAFT
    )
    
    created_skill = await registry.create_skill(skill)
    return created_skill.to_dict()


@router.get("/wallet/balance", response_model=WalletResponse)
async def get_wallet_balance(
    user_id: str = "test-user",
    point_service: PointService = Depends(get_point_service_dep)
):
    balance = await point_service.get_balance(user_id)
    return WalletResponse(**balance)


@router.post("/wallet/checkin")
async def daily_checkin(
    user_id: str = "test-user",
    point_service: PointService = Depends(get_point_service_dep)
):
    try:
        result = await point_service.checkin(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallet/transactions")
async def get_transactions(
    user_id: str = "test-user",
    transaction_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    point_service: PointService = Depends(get_point_service_dep)
):
    transactions, total = await point_service.get_transactions(
        user_id=user_id,
        transaction_type=transaction_type,
        page=page,
        size=size
    )
    
    return {
        "transactions": [t.to_dict() for t in transactions],
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/{skill_id}", response_model=Dict[str, Any])
async def get_skill(
    skill_id: str,
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    skill = await registry.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.to_dict()


@router.put("/{skill_id}", response_model=Dict[str, Any])
async def update_skill(
    skill_id: str,
    request: SkillUpdateRequest,
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    updates = {k: v for k, v in request.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    skill = await registry.update_skill(skill_id, updates)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.to_dict()


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    success = await registry.delete_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"success": True, "message": "Skill deleted"}


@router.post("/{skill_id}/purchase")
async def purchase_skill(
    skill_id: str,
    request: SkillPurchaseRequest,
    background_tasks: BackgroundTasks,
    registry: SkillRegistry = Depends(get_skill_registry_dep),
    point_service: PointService = Depends(get_point_service_dep)
):
    skill = await registry.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    if skill.status != SkillStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Skill is not available for purchase")
    
    if skill.cost_points > 0:
        try:
            await point_service.deduct_points(
                request.user_id,
                skill.cost_points,
                "skill_purchase",
                f"购买技能: {skill.name}",
                skill_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    background_tasks.add_task(registry.increment_download_count, skill_id)
    
    return {
        "success": True,
        "skill_id": skill_id,
        "points_spent": skill.cost_points,
        "message": f"Successfully purchased skill: {skill.name}"
    }


@router.post("/{skill_id}/invoke")
async def invoke_skill(
    skill_id: str,
    request: SkillInvokeRequest,
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    skill = await registry.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    start_time = datetime.now()
    
    try:
        result = await _execute_skill(skill, request.input_data)
        status = "success"
        error_message = None
    except Exception as e:
        result = {}
        status = "error"
        error_message = str(e)
    
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    return {
        "skill_id": skill_id,
        "status": status,
        "output_data": result,
        "duration_ms": duration_ms,
        "error_message": error_message
    }


async def _execute_skill(skill: Skill, input_data: Dict[str, Any]) -> Dict[str, Any]:
    if skill.type == SkillType.BUILTIN:
        return await _execute_builtin_skill(skill, input_data)
    elif skill.type == SkillType.EXTERNAL:
        return await _execute_external_skill(skill, input_data)
    else:
        return {"message": f"Skill {skill.name} executed", "input": input_data}


async def _execute_builtin_skill(skill: Skill, input_data: Dict[str, Any]) -> Dict[str, Any]:
    skill_name = skill.name.lower()
    
    if "情感" in skill_name or "emotion" in skill_name:
        text = input_data.get("text", "")
        emotions = ["happy", "sad", "anxious", "excited", "neutral"]
        import random
        return {
            "emotion": random.choice(emotions),
            "score": round(random.uniform(0.5, 1.0), 2),
            "text_length": len(text)
        }
    
    elif "图表" in skill_name or "chart" in skill_name:
        return {
            "chart_url": f"https://charts.example.com/{skill.id}",
            "chart_type": input_data.get("chart_type", "bar"),
            "data_points": len(input_data.get("data", []))
        }
    
    elif "gis" in skill_name or "地图" in skill_name:
        return {
            "location": input_data.get("location", {}),
            "map_url": f"https://maps.example.com/{skill.id}",
            "analysis_type": input_data.get("analysis_type", "heatmap")
        }
    
    else:
        return {
            "skill_name": skill.name,
            "executed": True,
            "input_processed": input_data
        }


async def _execute_external_skill(skill: Skill, input_data: Dict[str, Any]) -> Dict[str, Any]:
    code_config = skill.code_config
    api_url = code_config.get("api_url")
    
    if not api_url:
        return {"error": "External skill not configured properly"}
    
    return {
        "external_call": True,
        "api_url": api_url,
        "input": input_data,
        "message": "External skill would be called here"
    }


@router.post("/{skill_id}/reviews")
async def create_review(
    skill_id: str,
    request: SkillReviewRequest,
    user_id: str = "test-user",
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    skill = await registry.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    import asyncpg
    from backend.database_pg import DATABASE_URL
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        review_id = str(__import__("uuid").uuid4())
        await conn.execute("""
            INSERT INTO skill_reviews (id, skill_id, user_id, rating, comment)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (skill_id, user_id) DO UPDATE SET rating = $4, comment = $5, updated_at = NOW()
        """, review_id, skill_id, user_id, request.rating, request.comment)
        
        await registry.update_rating(skill_id)
    finally:
        await conn.close()
    
    return {"success": True, "message": "Review submitted"}


@router.get("/{skill_id}/reviews")
async def get_reviews(
    skill_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50)
):
    import asyncpg
    from backend.database_pg import DATABASE_URL
    
    conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        offset = (page - 1) * size
        rows = await conn.fetch("""
            SELECT * FROM skill_reviews WHERE skill_id = $1
            ORDER BY created_at DESC LIMIT $2 OFFSET $3
        """, skill_id, size, offset)
        
        count_row = await conn.fetchrow(
            "SELECT COUNT(*) as total FROM skill_reviews WHERE skill_id = $1", skill_id
        )
        
        reviews = []
        for row in rows:
            reviews.append({
                "id": str(row["id"]),
                "user_id": str(row["user_id"]),
                "rating": row["rating"],
                "comment": row["comment"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })
        
        return {"reviews": reviews, "total": count_row["total"] if count_row else 0}
    finally:
        await conn.close()


@router.get("/{skill_id}/versions")
async def get_skill_versions(
    skill_id: str,
    registry: SkillRegistry = Depends(get_skill_registry_dep)
):
    versions = await registry.get_versions(skill_id)
    return {
        "skill_id": skill_id,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "changelog": v.changelog,
                "status": v.status,
                "created_at": v.created_at.isoformat()
            }
            for v in versions
        ]
    }
