"""
智能体消息格式定义
定义代理间通信的标准消息格式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from enum import Enum
import uuid


class MessageType(str, Enum):
    """消息类型枚举"""
    REQUEST = "request"      # 请求消息
    RESPONSE = "response"    # 响应消息
    NOTIFY = "notify"        # 通知消息
    DEBATE = "debate"        # 辩论消息
    ERROR = "error"          # 错误消息


class AgentMessage(BaseModel):
    """
    智能体消息类
    定义代理间通信的标准消息格式
    
    Attributes:
        id: 消息唯一ID
        task_id: 所属任务ID
        sender: 发送代理名称
        recipient: 接收代理名称（None表示广播）
        type: 消息类型
        content: 消息内容
        in_reply_to: 回复的消息ID
        timestamp: 消息时间戳
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息唯一ID")
    task_id: str = Field(..., description="所属任务ID")
    sender: str = Field(..., description="发送代理名称")
    recipient: Optional[str] = Field(None, description="接收代理名称，None表示广播")
    type: MessageType = Field(MessageType.NOTIFY, description="消息类型")
    content: Dict[str, Any] = Field(default_factory=dict, description="消息内容")
    in_reply_to: Optional[str] = Field(None, description="回复的消息ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-123",
                "task_id": "task-456",
                "sender": "data_collector",
                "recipient": "market_analyst",
                "type": "request",
                "content": {"query": "需要更多南山区房价数据"},
                "in_reply_to": None,
                "timestamp": "2024-01-01T10:00:00"
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 消息字典
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.type.value if isinstance(self.type, MessageType) else self.type,
            "content": self.content,
            "in_reply_to": self.in_reply_to,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    def is_broadcast(self) -> bool:
        """
        判断是否为广播消息
        
        Returns:
            bool: 是否为广播
        """
        return self.recipient is None
    
    def is_reply(self) -> bool:
        """
        判断是否为回复消息
        
        Returns:
            bool: 是否为回复
        """
        return self.in_reply_to is not None
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 消息字符串
        """
        recipient_str = self.recipient if self.recipient else "ALL"
        return f"Message({self.sender} -> {recipient_str}: {self.type.value})"
