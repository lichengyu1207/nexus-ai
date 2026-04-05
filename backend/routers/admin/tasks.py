"""
管理员任务管理API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime

from ...auth import get_current_user, require_admin
from ...database import get_db_connection

router = APIRouter(prefix="/admin", tags=["admin-tasks"])

@router.get("/tasks")
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """
    获取任务列表
    
    Args:
        page: 页码
        page_size: 每页数量
        status: 状态过滤
        admin: 管理员用户
        
    Returns:
        任务列表
    """
    conn = await get_db_connection()
    try:
        offset = (page - 1) * page_size
        
        # 构建查询条件
        conditions = []
        params = []
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM analysis_tasks WHERE {where_clause}"
        cursor = await conn.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        # 获取任务列表
        query = f"""
            SELECT id, user_id, query, status, progress, error_message, created_at, updated_at
            FROM analysis_tasks
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "user_id": row[1],
                "query": row[2],
                "status": row[3],
                "progress": row[4],
                "error_message": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            })
        
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    admin: dict = Depends(require_admin)
):
    """
    获取任务详情
    
    Args:
        task_id: 任务ID
        admin: 管理员用户
        
    Returns:
        任务详情
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT id, user_id, query, status, progress, error_message, created_at, updated_at
            FROM analysis_tasks
            WHERE id = ?
        """, (task_id,))
        
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "id": row[0],
            "user_id": row[1],
            "query": row[2],
            "status": row[3],
            "progress": row[4],
            "error_message": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }
    finally:
        await conn.close()
