from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.agent import AgentCreate, AgentResponse, AgentToolsUpdate
from app.models.agent import Agent

router = APIRouter()

@router.post("/", response_model=AgentResponse)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """创建智能体"""
    # 检查智能体是否已存在
    existing_agent = db.query(Agent).filter(Agent.name == agent.name).first()
    if existing_agent:
        raise HTTPException(status_code=400, detail="智能体已存在")
    
    # 创建智能体
    db_agent = Agent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return db_agent

@router.get("/", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    """列出所有智能体"""
    agents = db.query(Agent).all()
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """获取智能体详情"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return agent

@router.put("/{agent_id}/tools")
def update_agent_tools(agent_id: int, tools: AgentToolsUpdate, db: Session = Depends(get_db)):
    """更新智能体工具白名单"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    agent.allowed_tools = tools.allowed_tools
    db.commit()
    db.refresh(agent)
    
    return agent
