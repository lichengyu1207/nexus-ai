from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.agents.gongbu import GongbuAgent

router = APIRouter()

@router.get("/data")
def get_monitoring_data(db: Session = Depends(get_db)):
    """获取监控数据"""
    gongbu = GongbuAgent(db)
    return gongbu.get_monitoring_data()
