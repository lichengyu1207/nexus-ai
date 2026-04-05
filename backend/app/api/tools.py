from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.tool import ToolCreate, ToolResponse, ToolUpdate
from app.models.tool import Tool

router = APIRouter()

@router.post("/", response_model=ToolResponse)
def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    """注册工具"""
    # 检查工具是否已存在
    existing_tool = db.query(Tool).filter(Tool.name == tool.name).first()
    if existing_tool:
        raise HTTPException(status_code=400, detail="工具已存在")
    
    # 创建工具
    db_tool = Tool(**tool.model_dump())
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    
    return db_tool

@router.get("/", response_model=List[ToolResponse])
def list_tools(db: Session = Depends(get_db)):
    """列出所有工具"""
    tools = db.query(Tool).all()
    return tools

@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """获取工具详情"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    return tool

@router.put("/{tool_id}", response_model=ToolResponse)
def update_tool(tool_id: int, tool: ToolUpdate, db: Session = Depends(get_db)):
    """更新工具"""
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    
    # 更新工具信息
    update_data = tool.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tool, field, value)
    
    db.commit()
    db.refresh(db_tool)
    return db_tool

@router.delete("/{tool_id}")
def delete_tool(tool_id: int, db: Session = Depends(get_db)):
    """删除工具"""
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    
    db.delete(db_tool)
    db.commit()
    return {"message": "工具删除成功"}
