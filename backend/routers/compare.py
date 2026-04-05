"""
对比分析API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
import uuid

from ..auth import get_current_user
from ..database import get_db_connection

router = APIRouter(prefix="/api/compare", tags=["compare"])

@router.post("")
async def create_compare_analysis(
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    创建对比分析
    
    Args:
        data: 包含locations列表的请求数据
        current_user: 当前用户
        
    Returns:
        对比分析结果
    """
    locations = data.get("locations", [])
    
    if not locations or len(locations) < 2:
        raise HTTPException(
            status_code=400,
            detail="至少需要提供两个对比地点"
        )
    
    if len(locations) > 5:
        raise HTTPException(
            status_code=400,
            detail="最多支持5个地点对比"
        )
    
    compare_id = str(uuid.uuid4())
    
    # 创建对比任务
    conn = await get_db_connection()
    try:
        # 检查用户积分
        cursor = await conn.execute(
            "SELECT integral FROM users WHERE id = ?",
            (current_user["id"],)
        )
        user = await cursor.fetchone()
        
        if not user or user[0] < len(locations):
            raise HTTPException(
                status_code=403,
                detail=f"积分不足，需要{len(locations)}积分"
            )
        
        # 扣除积分
        await conn.execute(
            "UPDATE users SET integral = integral - ? WHERE id = ?",
            (len(locations), current_user["id"])
        )
        
        # 创建对比记录
        await conn.execute("""
            INSERT INTO compare_analyses (id, user_id, locations, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (
            compare_id,
            current_user["id"],
            str(locations),
            datetime.now().isoformat()
        ))
        
        await conn.commit()
    finally:
        await conn.close()
    
    return {
        "id": compare_id,
        "locations": locations,
        "status": "pending",
        "message": "对比分析任务已创建，正在处理中"
    }

@router.get("/{compare_id}")
async def get_compare_analysis(
    compare_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取对比分析结果
    
    Args:
        compare_id: 对比分析ID
        current_user: 当前用户
        
    Returns:
        对比分析结果
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT id, user_id, locations, status, result, created_at, updated_at
            FROM compare_analyses
            WHERE id = ? AND user_id = ?
        """, (compare_id, current_user["id"]))
        
        analysis = await cursor.fetchone()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="对比分析不存在")
        
        return {
            "id": analysis[0],
            "locations": eval(analysis[2]) if analysis[2] else [],
            "status": analysis[3],
            "result": analysis[4],
            "created_at": analysis[5],
            "updated_at": analysis[6]
        }
    finally:
        await conn.close()

@router.get("")
async def list_compare_analyses(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    获取对比分析列表
    
    Args:
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        
    Returns:
        对比分析列表
    """
    conn = await get_db_connection()
    try:
        # 获取总数
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM compare_analyses WHERE user_id = ?",
            (current_user["id"],)
        )
        total = (await cursor.fetchone())[0]
        
        # 获取列表
        cursor = await conn.execute("""
            SELECT id, locations, status, created_at
            FROM compare_analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (current_user["id"], limit, offset))
        
        analyses = []
        for row in await cursor.fetchall():
            analyses.append({
                "id": row[0],
                "locations": eval(row[1]) if row[1] else [],
                "status": row[2],
                "created_at": row[3]
            })
        
        return {
            "analyses": analyses,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        await conn.close()
