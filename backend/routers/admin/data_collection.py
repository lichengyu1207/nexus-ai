"""
数据采集任务管理API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import asyncio

from backend.database import get_db_connection
from backend.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/admin/data-collection", tags=["数据采集"])


class TaskCreate(BaseModel):
    city_name: str
    task_type: str
    province_name: Optional[str] = None
    total_items: Optional[int] = None


class TaskResponse(BaseModel):
    id: str
    city_name: str
    province_name: Optional[str]
    task_type: str
    status: str
    progress: int
    total_items: Optional[int]
    processed_items: int
    message: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class DashboardResponse(BaseModel):
    total_tasks: int
    pending_tasks: int
    processing_tasks: int
    completed_tasks: int
    failed_tasks: int
    cities: List[dict]


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    user = Depends(require_admin)
):
    """创建新的数据采集任务"""
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    now = datetime.now()
    
    conn = await get_db_connection()
    
    try:
        await conn.execute('''
            INSERT INTO data_collection_tasks 
            (id, city_name, province_name, task_type, status, total_items, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
        ''', (task_id, task.city_name, task.province_name, task.task_type, task.total_items, now, now))
        
        await conn.commit()
        
        cursor = await conn.execute(
            "SELECT * FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        row = await cursor.fetchone()
        
        from backend.services.data_collection_worker import run_task
        background_tasks.add_task(run_task, task_id)
        
        return dict(row)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    city: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user = Depends(require_admin)
):
    """获取任务列表"""
    conn = await get_db_connection()
    
    try:
        query = "SELECT * FROM data_collection_tasks WHERE 1=1"
        params = []
        
        if city:
            query += " AND city_name = ?"
            params.append(city)
        if status:
            query += " AND status = ?"
            params.append(status)
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
        
    finally:
        await conn.close()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user = Depends(require_admin)):
    """获取单个任务详情"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return dict(row)
        
    finally:
        await conn.close()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, user = Depends(require_admin)):
    """取消任务"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT status FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if row["status"] not in ["pending", "processing"]:
            raise HTTPException(status_code=400, detail="只能取消待处理或进行中的任务")
        
        await conn.execute('''
            UPDATE data_collection_tasks 
            SET status = 'cancelled', message = '用户取消', updated_at = ?
            WHERE id = ?
        ''', (datetime.now(), task_id))
        
        await conn.commit()
        
        return {"message": "任务已取消"}
        
    finally:
        await conn.close()


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    user = Depends(require_admin)
):
    """重试失败的任务"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute(
            "SELECT * FROM data_collection_tasks WHERE id = ?", (task_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if row["status"] not in ["failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="只能重试失败或取消的任务")
        
        new_task_id = f"task-{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        
        await conn.execute('''
            INSERT INTO data_collection_tasks 
            (id, city_name, province_name, task_type, status, total_items, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
        ''', (new_task_id, row["city_name"], row["province_name"], row["task_type"], row["total_items"], now, now))
        
        await conn.commit()
        
        from backend.services.data_collection_worker import run_task
        background_tasks.add_task(run_task, new_task_id)
        
        return {"message": "已创建重试任务", "new_task_id": new_task_id}
        
    finally:
        await conn.close()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(user = Depends(require_admin)):
    """获取数据采集仪表盘数据"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute("SELECT COUNT(*) FROM data_collection_tasks")
        total = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM data_collection_tasks WHERE status = 'pending'")
        pending = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM data_collection_tasks WHERE status = 'processing'")
        processing = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM data_collection_tasks WHERE status = 'completed'")
        completed = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM data_collection_tasks WHERE status = 'failed'")
        failed = (await cursor.fetchone())[0]
        
        cursor = await conn.execute('''
            SELECT 
                city_name,
                province_name,
                MAX(CASE WHEN task_type = 'community' THEN progress ELSE 0 END) as community_progress,
                MAX(CASE WHEN task_type = 'community' THEN status ELSE NULL END) as community_status,
                MAX(CASE WHEN task_type = 'price' THEN progress ELSE 0 END) as price_progress,
                MAX(CASE WHEN task_type = 'price' THEN status ELSE NULL END) as price_status,
                MAX(CASE WHEN task_type = 'poi' THEN progress ELSE 0 END) as poi_progress,
                MAX(CASE WHEN task_type = 'poi' THEN status ELSE NULL END) as poi_status
            FROM data_collection_tasks
            GROUP BY city_name
            ORDER BY city_name
        ''')
        cities = [dict(row) for row in await cursor.fetchall()]
        
        return {
            "total_tasks": total,
            "pending_tasks": pending,
            "processing_tasks": processing,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "cities": cities
        }
        
    finally:
        await conn.close()
