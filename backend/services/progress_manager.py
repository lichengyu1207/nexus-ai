"""
进度管理器
提供实时进度显示、预计剩余时间、详细步骤追踪
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProgressStep:
    """进度步骤"""
    id: str
    name: str
    description: str
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0  # 0-100
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    estimated_duration: Optional[float] = None  # 预计耗时（秒）
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    total_steps: int = 5
    current_step: int = 0
    overall_progress: int = 0  # 0-100
    started_at: float = field(default_factory=time.time)
    steps: List[ProgressStep] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    
    def __post_init__(self):
        if not self.steps:
            self.steps = [
                ProgressStep(id="init", name="初始化", description="准备分析环境", estimated_duration=1.0),
                ProgressStep(id="parse", name="需求解析", description="解析用户查询", estimated_duration=2.0),
                ProgressStep(id="collect", name="数据采集", description="采集市场数据", estimated_duration=5.0),
                ProgressStep(id="analyze", name="智能分析", description="执行深度分析", estimated_duration=8.0),
                ProgressStep(id="report", name="报告生成", description="生成分析报告", estimated_duration=3.0),
            ]
            self.total_steps = len(self.steps)
    
    def get_estimated_remaining_time(self) -> float:
        """计算预计剩余时间"""
        elapsed = time.time() - self.started_at
        if self.overall_progress > 0:
            estimated_total = elapsed / (self.overall_progress / 100)
            return max(0, estimated_total - elapsed)
        return sum(s.estimated_duration or 0 for s in self.steps if s.status == "pending")
    
    def get_current_step(self) -> Optional[ProgressStep]:
        """获取当前步骤"""
        for step in self.steps:
            if step.status == "running":
                return step
        return None

class ProgressManager:
    """进度管理器"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._progress: Dict[str, TaskProgress] = {}
        self._sse_manager = None
    
    def set_sse_manager(self, sse_manager):
        """设置SSE管理器"""
        self._sse_manager = sse_manager
    
    async def create_progress(self, task_id: str) -> TaskProgress:
        """创建任务进度"""
        progress = TaskProgress(task_id=task_id)
        self._progress[task_id] = progress
        
        await self._broadcast_progress(task_id, "created")
        return progress
    
    async def start_step(self, task_id: str, step_id: str, description: str = None) -> bool:
        """开始步骤"""
        progress = self._progress.get(task_id)
        if not progress:
            return False
        
        for step in progress.steps:
            if step.id == step_id:
                step.status = "running"
                step.started_at = time.time()
                if description:
                    step.description = description
                
                progress.current_step = progress.steps.index(step) + 1
                progress.status = "running"
                
                await self._broadcast_progress(task_id, "step_started", step)
                return True
        
        return False
    
    async def update_step_progress(self, task_id: str, step_id: str, step_progress: int, details: Dict = None):
        """更新步骤进度"""
        progress = self._progress.get(task_id)
        if not progress:
            return
        
        for i, step in enumerate(progress.steps):
            if step.id == step_id:
                step.progress = min(100, max(0, step_progress))
                if details:
                    step.details.update(details)
                
                # 计算总体进度
                completed_weight = sum(s.progress for s in progress.steps[:i])
                current_weight = step.progress
                total_weight = 100 * len(progress.steps)
                progress.overall_progress = int((completed_weight + current_weight) / total_weight * 100)
                
                await self._broadcast_progress(task_id, "progress_update", step)
                return
    
    async def complete_step(self, task_id: str, step_id: str, result: Dict = None):
        """完成步骤"""
        progress = self._progress.get(task_id)
        if not progress:
            return
        
        for i, step in enumerate(progress.steps):
            if step.id == step_id:
                step.status = "completed"
                step.progress = 100
                step.completed_at = time.time()
                if result:
                    step.details.update(result)
                
                # 更新总体进度
                completed_steps = sum(1 for s in progress.steps if s.status == "completed")
                progress.overall_progress = int(completed_steps / progress.total_steps * 100)
                
                await self._broadcast_progress(task_id, "step_completed", step)
                return
    
    async def fail_step(self, task_id: str, step_id: str, error: str):
        """步骤失败"""
        progress = self._progress.get(task_id)
        if not progress:
            return
        
        for step in progress.steps:
            if step.id == step_id:
                step.status = "failed"
                step.details["error"] = error
                progress.status = "failed"
                
                await self._broadcast_progress(task_id, "step_failed", step)
                return
    
    async def complete_task(self, task_id: str, result: Dict = None):
        """完成任务"""
        progress = self._progress.get(task_id)
        if not progress:
            return
        
        progress.status = "completed"
        progress.overall_progress = 100
        
        for step in progress.steps:
            if step.status != "completed":
                step.status = "completed"
                step.progress = 100
        
        await self._broadcast_progress(task_id, "completed", result)
    
    async def fail_task(self, task_id: str, error: str):
        """任务失败"""
        progress = self._progress.get(task_id)
        if not progress:
            return
        
        progress.status = "failed"
        
        await self._broadcast_progress(task_id, "failed", {"error": error})
    
    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取进度信息"""
        progress = self._progress.get(task_id)
        if not progress:
            return None
        
        elapsed = time.time() - progress.started_at
        remaining = progress.get_estimated_remaining_time()
        current_step = progress.get_current_step()
        
        return {
            "task_id": task_id,
            "status": progress.status,
            "overall_progress": progress.overall_progress,
            "current_step": progress.current_step,
            "total_steps": progress.total_steps,
            "elapsed_time": round(elapsed, 1),
            "estimated_remaining": round(remaining, 1),
            "current_step_name": current_step.name if current_step else None,
            "current_step_description": current_step.description if current_step else None,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "status": step.status,
                    "progress": step.progress,
                }
                for step in progress.steps
            ],
        }
    
    async def _broadcast_progress(self, task_id: str, event_type: str, data: Any = None):
        """广播进度更新"""
        if not self._sse_manager:
            return
        
        progress_data = self.get_progress(task_id)
        if not progress_data:
            return
        
        event_data = {
            "type": event_type,
            "progress": progress_data,
            "timestamp": datetime.now().isoformat(),
        }
        
        if data:
            if isinstance(data, ProgressStep):
                event_data["step"] = {
                    "id": data.id,
                    "name": data.name,
                    "status": data.status,
                    "progress": data.progress,
                }
            elif isinstance(data, dict):
                event_data["data"] = data
        
        from ..sse_manager import SSEEvent
        event = SSEEvent(event="progress", data=event_data)
        await self._sse_manager.broadcast(task_id, event)

progress_manager = ProgressManager()
