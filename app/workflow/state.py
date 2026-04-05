"""
LangGraph共享状态定义
用于在代理之间传递工作流状态
"""
from typing import TypedDict, List, Optional, Any
from dataclasses import dataclass, field


class AgentState(TypedDict):
    """
    代理状态类
    用于在工作流中传递状态和数据
    """
    query: str = ""
    requirement: dict = field(default_factory=dict)
    collected_data: dict = field(default_factory=dict)
    analysis_result: dict = field(default_factory=dict)
    final_report: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    current_step: str = "idle"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "query": self.query,
            "requirement": self.requirement,
            "collected_data": self.collected_data,
            "analysis_result": self.analysis_result,
            "final_report": self.final_report,
            "errors": self.errors,
            "current_step": self.current_step
        }
    
    def update(self, **kwargs) -> None:
        """更新状态"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
