"""
氛围估价API路由
Atmosphere Valuation API Routes

提供氛围估价相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional, List

from ..auth import get_current_user
from ..database import get_db_connection
from ..logger import get_logger
from ..app.services.atmosphere_engine import AtmosphereEngine

logger = get_logger("atmosphere")

router = APIRouter(prefix="/api/atmosphere", tags=["atmosphere"])
engine = AtmosphereEngine()


class EstimateRequest(BaseModel):
    address: str
    user_preferences: Optional[Dict] = None


class EstimateResponse(BaseModel):
    base_value: float
    atmosphere_score: float
    final_value: float
    factors: Dict[str, float]


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    estimate: Optional[EstimateResponse] = None


class AtmosphereFactors(BaseModel):
    community: float
    environment: float
    convenience: float
    safety: float
    culture: float
    potential: float


class HistoryItem(BaseModel):
    id: str
    address: str
    value: float
    timestamp: str


@router.post("/estimate", response_model=EstimateResponse)
async def estimate_atmosphere(
    request: EstimateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    氛围估价
    """
    try:
        result = await engine.calculate_value(
            request.address,
            request.user_preferences
        )
        
        # 保存估价记录到数据库
        user_id = current_user["id"]
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS atmosphere_estimates (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        address TEXT NOT NULL,
                        base_value REAL,
                        atmosphere_score REAL,
                        final_value REAL,
                        factors TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                import uuid
                estimate_id = str(uuid.uuid4())
                
                await conn.execute("""
                    INSERT INTO atmosphere_estimates (
                        id, user_id, address, base_value, atmosphere_score, final_value, factors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    estimate_id,
                    user_id,
                    request.address,
                    result["base_value"],
                    result["atmosphere_score"],
                    result["final_value"],
                    str(result["factors"])
                ))
            finally:
                await conn.close()
        
        return EstimateResponse(**result)
    except Exception as e:
        logger.error(f"氛围估价失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[HistoryItem])
async def get_estimate_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取历史估价记录
    """
    user_id = current_user["id"]
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT id, address, final_value, timestamp
                FROM atmosphere_estimates
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            rows = await cursor.fetchall()
            return [
                HistoryItem(
                    id=row[0],
                    address=row[1],
                    value=row[2],
                    timestamp=str(row[3])
                )
                for row in rows
            ]
        finally:
            await conn.close()


@router.get("/factors", response_model=AtmosphereFactors)
async def get_atmosphere_factors(
    address: str = Query(..., description="房产地址"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取氛围因素
    """
    try:
        factors = await engine.get_atmosphere_factors(address)
        return AtmosphereFactors(**factors)
    except Exception as e:
        logger.error(f"获取氛围因素失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_estimate(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    智能咨询估价
    """
    try:
        result = await engine.chat_estimate(
            request.message,
            request.session_id,
            current_user["id"]
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"智能咨询估价失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
