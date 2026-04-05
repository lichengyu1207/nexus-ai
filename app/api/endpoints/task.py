from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.task import Task, TaskCreate, TaskUpdate

router = APIRouter()


@router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    # Implementation will be added later
    pass


@router.get("/", response_model=List[Task])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get a list of tasks"""
    # Implementation will be added later
    pass


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a task by ID"""
    # Implementation will be added later
    pass


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a task"""
    # Implementation will be added later
    pass


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a task"""
    # Implementation will be added later
    pass