"""
智能体记忆系统 - Pydantic 数据模型
定义记忆相关的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MemoryBase(BaseModel):
    agent_name: str = Field(..., description="智能体名称")
    input_text: str = Field(..., description="用户输入")
    output_text: str = Field(..., description="AI响应")
    session_id: Optional[str] = Field(None, description="会话ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    summary: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0, le=10)
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class MemoryResponse(BaseModel):
    id: str = Field(..., description="记忆ID")
    user_id: str = Field(..., description="用户ID")
    agent_name: str = Field(..., description="智能体名称")
    session_id: Optional[str] = Field(None, description="会话ID")
    input_text: str = Field(..., description="用户输入")
    output_text: str = Field(..., description="AI响应")
    summary: Optional[str] = Field(None, description="摘要")
    importance: float = Field(5.0, description="重要性")
    category: str = Field("fact", description="类别")
    tags: str = Field("[]", description="标签JSON")
    created_at: str = Field(..., description="创建时间")
    last_accessed: Optional[str] = Field(None, description="最后访问时间")
    access_count: int = Field(0, description="访问次数")
    embedding_id: Optional[str] = Field(None, description="向量ID")

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int
    limit: int
    offset: int


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    limit: int = Field(5, ge=1, le=20, description="返回数量限制")
    category: Optional[str] = Field(None, description="按类别过滤")
    threshold: float = Field(0.3, ge=0, le=1, description="相似度阈值")


class MemorySearchResponse(BaseModel):
    query: str
    results: List[MemoryResponse]
    count: int


class UserProfileBase(BaseModel):
    profile: Dict[str, Any] = Field(default_factory=dict, description="用户画像")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    user_id: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class MemoryGraph(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点列表")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边列表")


class MemoryStats(BaseModel):
    total_memories: int = Field(0, description="总记忆数")
    categories: Dict[str, int] = Field(default_factory=dict, description="类别分布")
    average_importance: float = Field(0, description="平均重要性")
    vector_store: Dict[str, Any] = Field(default_factory=dict, description="向量存储状态")


class ConsolidationResult(BaseModel):
    user_id: str
    memories_processed: int = Field(0, description="处理的记忆数")
    memories_merged: int = Field(0, description="合并的记忆数")
    memories_forgotten: int = Field(0, description="遗忘的记忆数")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="详细结果")


class MemoryContextResponse(BaseModel):
    context: str = Field(..., description="格式化的记忆上下文")
    query: Optional[str] = Field(None, description="查询文本")


class AdminMetricsResponse(BaseModel):
    total_memories: int
    total_users_with_memories: int
    daily_new_memories: int
    weekly_new_memories: int
    category_distribution: Dict[str, int]
    average_importance: float
    active_memories_7d: int
    vector_store: Dict[str, Any]
    collected_at: str
