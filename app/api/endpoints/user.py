from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    # Implementation will be added later
    pass


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get a list of users"""
    # Implementation will be added later
    pass


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a user by ID"""
    # Implementation will be added later
    pass


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user"""
    # Implementation will be added later
    pass


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user"""
    # Implementation will be added later
    pass