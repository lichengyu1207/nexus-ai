from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.property import Property, PropertyCreate, PropertyUpdate

router = APIRouter()


@router.post("/", response_model=Property)
async def create_property(
    property: PropertyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new property"""
    # Implementation will be added later
    pass


@router.get("/", response_model=List[Property])
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get a list of properties"""
    # Implementation will be added later
    pass


@router.get("/{property_id}", response_model=Property)
async def get_property(
    property_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a property by ID"""
    # Implementation will be added later
    pass


@router.put("/{property_id}", response_model=Property)
async def update_property(
    property_id: str,
    property: PropertyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a property"""
    # Implementation will be added later
    pass


@router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a property"""
    # Implementation will be added later
    pass