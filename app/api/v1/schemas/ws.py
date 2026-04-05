from pydantic import BaseModel
from enum import Enum


class NodeStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class WebSocketMessage(BaseModel):
    node: str
    status: NodeStatusEnum
    log: str
