"""
事件定义模块
定义系统中使用的各种事件类型
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class BaseEvent:
    """事件基类"""
    event_type: str
    occurred_at: datetime
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['occurred_at'] = self.occurred_at.isoformat()
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class UserRegisteredEvent(BaseEvent):
    """用户注册事件"""
    event_type: str = "user_registered"
    user_id: str = ""
    email: str = ""
    source: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    referred_by: Optional[str] = None
    
    def __init__(
        self,
        user_id: str,
        email: str,
        source: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        referred_by: Optional[str] = None,
        occurred_at: datetime = None
    ):
        self.event_type = "user_registered"
        self.user_id = user_id
        self.email = email
        self.source = source
        self.city = city
        self.district = district
        self.referred_by = referred_by
        self.occurred_at = occurred_at or datetime.now()


@dataclass
class IntegralChangedEvent(BaseEvent):
    """积分变动事件"""
    event_type: str = "integral_changed"
    user_id: str = ""
    change: float = 0.0
    balance_after: float = 0.0
    reason: str = ""
    action_type: str = ""
    
    def __init__(
        self,
        user_id: str,
        change: float,
        balance_after: float,
        reason: str,
        action_type: str = "",
        occurred_at: datetime = None
    ):
        self.event_type = "integral_changed"
        self.user_id = user_id
        self.change = change
        self.balance_after = balance_after
        self.reason = reason
        self.action_type = action_type
        self.occurred_at = occurred_at or datetime.now()


@dataclass
class TaskCreatedEvent(BaseEvent):
    """任务创建事件"""
    event_type: str = "task_created"
    user_id: str = ""
    task_id: str = ""
    task_type: str = ""
    
    def __init__(
        self,
        user_id: str,
        task_id: str,
        task_type: str = "",
        occurred_at: datetime = None
    ):
        self.event_type = "task_created"
        self.user_id = user_id
        self.task_id = task_id
        self.task_type = task_type
        self.occurred_at = occurred_at or datetime.now()


@dataclass
class TaskCompletedEvent(BaseEvent):
    """任务完成事件"""
    event_type: str = "task_completed"
    user_id: str = ""
    task_id: str = ""
    task_type: str = ""
    
    def __init__(
        self,
        user_id: str,
        task_id: str,
        task_type: str = "",
        occurred_at: datetime = None
    ):
        self.event_type = "task_completed"
        self.user_id = user_id
        self.task_id = task_id
        self.task_type = task_type
        self.occurred_at = occurred_at or datetime.now()


@dataclass
class UserLocationUpdatedEvent(BaseEvent):
    """用户位置更新事件"""
    event_type: str = "user_location_updated"
    user_id: str = ""
    city: Optional[str] = None
    district: Optional[str] = None
    old_city: Optional[str] = None
    old_district: Optional[str] = None
    
    def __init__(
        self,
        user_id: str,
        city: Optional[str] = None,
        district: Optional[str] = None,
        old_city: Optional[str] = None,
        old_district: Optional[str] = None,
        occurred_at: datetime = None
    ):
        self.event_type = "user_location_updated"
        self.user_id = user_id
        self.city = city
        self.district = district
        self.old_city = old_city
        self.old_district = old_district
        self.occurred_at = occurred_at or datetime.now()


@dataclass
class SigninEvent(BaseEvent):
    """签到事件"""
    event_type: str = "user_signin"
    user_id: str = ""
    reward_integral: float = 0.0
    consecutive_days: int = 1
    
    def __init__(
        self,
        user_id: str,
        reward_integral: float = 0.0,
        consecutive_days: int = 1,
        occurred_at: datetime = None
    ):
        self.event_type = "user_signin"
        self.user_id = user_id
        self.reward_integral = reward_integral
        self.consecutive_days = consecutive_days
        self.occurred_at = occurred_at or datetime.now()
