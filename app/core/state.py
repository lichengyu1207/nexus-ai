"""
共享状态管理
实现代理间的状态共享和同步
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class SharedState:
    """
    共享状态类
    用于代理间共享任务状态和数据
    """
    task_id: str
    query: str = ""
    current_step: str = "initialized"
    progress: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update(self, **kwargs) -> None:
        """
        更新状态
        
        Args:
            **kwargs: 要更新的字段
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now()
    
    def set_data(self, key: str, value: Any) -> None:
        """
        设置数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value
        self.updated_at = datetime.now()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            Any: 数据值
        """
        return self.data.get(key, default)
    
    def set_result(self, agent_name: str, result: Any) -> None:
        """
        设置代理结果
        
        Args:
            agent_name: 代理名称
            result: 结果数据
        """
        self.results[agent_name] = result
        self.updated_at = datetime.now()
    
    def get_result(self, agent_name: str) -> Optional[Any]:
        """
        获取代理结果
        
        Args:
            agent_name: 代理名称
            
        Returns:
            Optional[Any]: 结果数据
        """
        return self.results.get(agent_name)
    
    def add_error(self, error: str) -> None:
        """
        添加错误
        
        Args:
            error: 错误信息
        """
        self.errors.append(error)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict: 状态字典
        """
        return {
            "task_id": self.task_id,
            "query": self.query,
            "current_step": self.current_step,
            "progress": self.progress,
            "data": self.data,
            "results": self.results,
            "errors": self.errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_json(self) -> str:
        """
        转换为JSON字符串
        
        Returns:
            str: JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)


class StateManager:
    """
    状态管理器
    管理所有任务的共享状态
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化状态管理器"""
        if self._initialized:
            return
        
        self._states: Dict[str, SharedState] = {}
        self._initialized = True
    
    def create_state(self, task_id: str, query: str = "") -> SharedState:
        """
        创建任务状态
        
        Args:
            task_id: 任务ID
            query: 查询内容
            
        Returns:
            SharedState: 状态实例
        """
        if task_id not in self._states:
            self._states[task_id] = SharedState(task_id=task_id, query=query)
        
        return self._states[task_id]
    
    def get_state(self, task_id: str) -> Optional[SharedState]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[SharedState]: 状态实例
        """
        return self._states.get(task_id)
    
    def update_state(self, task_id: str, **kwargs) -> None:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
        """
        state = self._states.get(task_id)
        if state:
            state.update(**kwargs)
    
    def remove_state(self, task_id: str) -> None:
        """
        移除任务状态
        
        Args:
            task_id: 任务ID
        """
        if task_id in self._states:
            del self._states[task_id]
    
    def get_all_tasks(self) -> List[str]:
        """
        获取所有任务ID
        
        Returns:
            List[str]: 任务ID列表
        """
        return list(self._states.keys())


# 全局状态管理器实例
state_manager = StateManager()
