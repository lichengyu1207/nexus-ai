"""
智能体消息格式定义
定义代理间通信的标准消息格式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, Literal
from enum import Enum
import uuid


class MessageType(str, Enum):
    """消息类型枚举"""
    REQUEST = "request"      # 请求消息
    RESPONSE = "response"    # 响应消息
    NOTIFY = "notify"        # 通知消息
    DEBATE = "debate"        # 辩论消息
    ERROR = "error"          # 错误消息


class MessagePriority(str, Enum):
    """消息优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentMessage(BaseModel):
    """
    智能体消息类
    定义代理间通信的标准消息格式
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息唯一ID")
    task_id: str = Field(..., description="所属任务ID")
    sender: str = Field(..., description="发送代理名称")
    recipient: Optional[str] = Field(None, description="接收代理名称，None表示广播")
    type: MessageType = Field(MessageType.NOTIFY, description="消息类型")
    content: dict = Field(default_factory=dict, description="消息内容")
    in_reply_to: Optional[str] = Field(None, description="回复的消息ID")
    priority: MessagePriority = Field(MessagePriority.NORMAL, description="消息优先级")
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
                "priority": "normal",
                "timestamp": "2024-01-01T10:00:00"
            }
        }
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.type.value if isinstance(self.type, MessageType) else self.type,
            "content": self.content,
            "in_reply_to": self.in_reply_to,
            "priority": self.priority.value if isinstance(self.priority, MessagePriority) else self.priority,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    def is_broadcast(self) -> bool:
        """判断是否为广播消息"""
        return self.recipient is None
    
    def is_reply(self) -> bool:
        """判断是否为回复消息"""
        return self.in_reply_to is not None


class MessageHistory:
    """
    消息历史记录
    用于追踪和查询消息历史
    """
    
    def __init__(self):
        """初始化消息历史"""
        self._messages: list[AgentMessage] = []
    
    def add(self, message: AgentMessage) -> None:
        """添加消息到历史"""
        self._messages.append(message)
    
    def get_all(self) -> list[AgentMessage]:
        """获取所有消息"""
        return self._messages.copy()
    
    def get_by_task(self, task_id: str) -> list[AgentMessage]:
        """获取指定任务的所有消息"""
        return [msg for msg in self._messages if msg.task_id == task_id]
    
    def get_by_sender(self, sender: str) -> list[AgentMessage]:
        """获取指定发送者的所有消息"""
        return [msg for msg in self._messages if msg.sender == sender]
    
    def get_by_recipient(self, recipient: str) -> list[AgentMessage]:
        """获取指定接收者的所有消息"""
        return [msg for msg in self._messages if msg.recipient == recipient]
    
    def get_by_type(self, message_type: MessageType) -> list[AgentMessage]:
        """获取指定类型的所有消息"""
        return [msg for msg in self._messages if msg.type == message_type]
    
    def clear(self) -> None:
        """清空消息历史"""
        self._messages.clear()
