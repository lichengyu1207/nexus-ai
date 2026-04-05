from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.audit import AuditLogResponse
from app.models.audit import AuditLog

router = APIRouter()

@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(db: Session = Depends(get_db)):
    """列出所有审计日志"""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return logs

@router.get("/traces/{trace_id}", response_model=List[AuditLogResponse])
def get_audit_logs_by_trace(trace_id: str, db: Session = Depends(get_db)):
    """根据trace_id获取审计日志"""
    logs = db.query(AuditLog).filter(AuditLog.trace_id == trace_id).order_by(AuditLog.created_at).all()
    return logs
