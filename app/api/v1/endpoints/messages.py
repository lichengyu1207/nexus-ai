"""
消息API端点
提供代理间消息的查询和发送功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.ai_agents.bus import agent_bus, MessageType


router = APIRouter()


# ========== Pydantic模型 ==========

class MessageResponse(BaseModel):
    """消息响应模型"""
    id: str = Field(..., description="消息ID")
    task_id: str = Field(..., description="任务ID")
    from_agent: str = Field(..., description="发送方代理")
    to_agent: str = Field(..., description="接收方代理")
    type: str = Field(..., description="消息类型")
    content: dict = Field(..., description="消息内容")
    created_at: str = Field(..., description="创建时间")
    read_at: Optional[str] = Field(None, description="已读时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-123",
                "task_id": "task-456",
                "from_agent": "requirement_analyzer",
                "to_agent": "data_collector",
                "type": "REQUEST",
                "content": {"query": "需要采集深圳南山区房价数据"},
                "created_at": "2024-01-01T10:00:00",
                "read_at": None
            }
        }


class MessageCreate(BaseModel):
    """创建消息请求模型"""
    from_agent: str = Field(..., description="发送方代理")
    to_agent: str = Field(..., description="接收方代理")
    type: str = Field(..., description="消息类型")
    content: dict = Field(..., description="消息内容")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_agent": "admin",
                "to_agent": "requirement_analyzer",
                "type": "REQUEST",
                "content": {"query": "手动触发分析任务"}
            }
        }


class ConversationHistory(BaseModel):
    """对话历史响应模型"""
    task_id: str = Field(..., description="任务ID")
    messages: List[MessageResponse] = Field(..., description="消息列表")
    total_count: int = Field(..., description="消息总数")


# ========== API端点 ==========

@router.get("/tasks/{task_id}/messages", response_model=ConversationHistory)
async def get_task_messages(
    task_id: str,
    since: Optional[str] = Query(None, description="获取此时间之后的消息（ISO格式）"),
    agent_name: Optional[str] = Query(None, description="过滤特定代理的消息"),
    unread_only: bool = Query(False, description="只返回未读消息")
):
    """
    获取任务的所有代理消息
    
    Args:
        task_id: 任务ID
        since: 时间过滤（可选）
        agent_name: 代理名称过滤（可选）
        unread_only: 是否只返回未读消息
        
    Returns:
        ConversationHistory: 对话历史
    """
    try:
        # 解析时间参数
        since_time = None
        if since:
            try:
                since_time = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid time format for 'since' parameter")
        
        # 获取消息
        messages = agent_bus.get_messages(
            task_id=task_id,
            agent_name=agent_name,
            since=since_time,
            unread_only=unread_only
        )
        
        # 转换为响应格式
        message_responses = [
            MessageResponse(**msg.to_dict())
            for msg in messages
        ]
        
        return ConversationHistory(
            task_id=task_id,
            messages=message_responses,
            total_count=len(message_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/messages", response_model=MessageResponse)
async def send_message(task_id: str, message: MessageCreate):
    """
    手动发送消息（管理员调试用）
    
    Args:
        task_id: 任务ID
        message: 消息内容
        
    Returns:
        MessageResponse: 创建的消息
    """
    try:
        # 验证消息类型
        try:
            msg_type = MessageType(message.type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid message type. Must be one of: {[t.value for t in MessageType]}"
            )
        
        # 发送消息
        agent_message = await agent_bus.send(
            task_id=task_id,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            message_type=msg_type,
            content=message.content
        )
        
        return MessageResponse(**agent_message.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/messages/unread-count")
async def get_unread_count(task_id: str, agent_name: str = Query(..., description="代理名称")):
    """
    获取未读消息数量
    
    Args:
        task_id: 任务ID
        agent_name: 代理名称
        
    Returns:
        dict: 包含未读消息数量
    """
    try:
        count = agent_bus.get_unread_count(task_id, agent_name)
        return {
            "task_id": task_id,
            "agent_name": agent_name,
            "unread_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/messages/mark-read")
async def mark_messages_as_read(task_id: str, agent_name: str = Query(..., description="代理名称")):
    """
    标记代理的所有消息为已读
    
    Args:
        task_id: 任务ID
        agent_name: 代理名称
        
    Returns:
        dict: 操作结果
    """
    try:
        count = agent_bus.mark_messages_as_read(task_id, agent_name)
        return {
            "task_id": task_id,
            "agent_name": agent_name,
            "marked_count": count,
            "message": f"Successfully marked {count} messages as read"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
