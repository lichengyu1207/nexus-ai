from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetPolicyUpdate
from app.models.dataset import Dataset

router = APIRouter()

@router.post("/", response_model=DatasetResponse)
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    """注册数据集"""
    # 检查数据集是否已存在
    existing_dataset = db.query(Dataset).filter(Dataset.name == dataset.name).first()
    if existing_dataset:
        raise HTTPException(status_code=400, detail="数据集已存在")
    
    # 创建数据集
    db_dataset = Dataset(**dataset.model_dump())
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    return db_dataset

@router.get("/", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """列出所有数据集"""
    datasets = db.query(Dataset).all()
    return datasets

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """获取数据集详情"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return dataset

@router.put("/{dataset_id}/policy")
def update_dataset_policy(dataset_id: int, policy: DatasetPolicyUpdate, db: Session = Depends(get_db)):
    """更新数据集访问策略"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    dataset.policy = policy.policy
    db.commit()
    db.refresh(dataset)
    
    return dataset
