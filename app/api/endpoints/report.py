from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.report import Report, ReportCreate, ReportUpdate

router = APIRouter()


@router.post("/", response_model=Report)
async def create_report(
    report: ReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new report"""
    # Implementation will be added later
    pass


@router.get("/", response_model=List[Report])
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get a list of reports"""
    # Implementation will be added later
    pass


@router.get("/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a report by ID"""
    # Implementation will be added later
    pass


@router.put("/{report_id}", response_model=Report)
async def update_report(
    report_id: str,
    report: ReportUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a report"""
    # Implementation will be added later
    pass


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a report"""
    # Implementation will be added later
    pass