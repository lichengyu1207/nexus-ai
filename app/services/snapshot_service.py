from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.api.v1.storage import task_store
from app.services.task_manager import task_manager
from app.models import TaskSnapshot
from app.core.database import SessionLocal


class SnapshotService:
    """Service for managing task snapshots"""
    
    def __init__(self):
        """Initialize snapshot service"""
        # 使用数据库存储
        pass
    
    def save(self, task_id: str) -> str:
        """Save task snapshot
        
        Args:
            task_id: Unique task ID
            
        Returns:
            Snapshot ID
        """
        try:
            # 获取任务信息
            task = task_store.get_task(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
            
            # 获取代理信息
            task_with_agents = task_manager.get_task_status(task_id)
            
            # 获取任务步骤
            steps_result = task_manager.get_task_steps(task_id, group_by_agent=True)
            
            # 构建快照数据
            snapshot_id = str(uuid.uuid4())
            snapshot_data = {
                "task_id": task_id,
                "snapshot_id": snapshot_id,
                "created_at": datetime.now().isoformat(),
                "task_info": task,
                "agents": task_with_agents.get("agents", {}) if task_with_agents else {},
                "steps": steps_result.get("steps_by_agent", {}) if steps_result else {},
                "total_duration": self._calculate_total_duration(task_with_agents)
            }
            
            # 存储到数据库
            db = SessionLocal()
            try:
                # 创建快照记录
                db_snapshot = TaskSnapshot(
                    id=snapshot_id,
                    task_id=task_id,
                    snapshot_data=snapshot_data,
                    total_duration=int(snapshot_data["total_duration"] * 1000)  # 转换为毫秒
                )
                db.add(db_snapshot)
                db.commit()
                db.refresh(db_snapshot)
            finally:
                db.close()
            
            # 也可以存储到任务的扩展信息中
            task_store.update_task_extra(task_id, "snapshot_id", snapshot_id)
            
            return snapshot_id
            
        except Exception as e:
            raise Exception(f"Failed to save snapshot: {str(e)}")
    
    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task snapshot
        
        Args:
            task_id: Unique task ID
            
        Returns:
            Snapshot data or None if not found
        """
        try:
            # 从数据库获取快照
            db = SessionLocal()
            try:
                snapshot = db.query(TaskSnapshot).filter(
                    TaskSnapshot.task_id == task_id
                ).order_by(TaskSnapshot.created_at.desc()).first()
                
                if snapshot:
                    return snapshot.snapshot_data
            finally:
                db.close()
            
            # 如果没有快照，实时生成一个
            snapshot_id = self.save(task_id)
            return self.get_by_id(snapshot_id)
            
        except Exception:
            return None
    
    def get_by_id(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get snapshot by ID
        
        Args:
            snapshot_id: Unique snapshot ID
            
        Returns:
            Snapshot data or None if not found
        """
        try:
            db = SessionLocal()
            try:
                snapshot = db.query(TaskSnapshot).filter(
                    TaskSnapshot.id == snapshot_id
                ).first()
                
                if snapshot:
                    return snapshot.snapshot_data
            finally:
                db.close()
            
            return None
        except Exception:
            return None
    
    def delete_old_snapshots(self, days: int = 7):
        """Delete old snapshots
        
        Args:
            days: Number of days to keep snapshots
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        db = SessionLocal()
        try:
            # 删除旧快照
            db.query(TaskSnapshot).filter(
                TaskSnapshot.created_at < cutoff_date
            ).delete()
            db.commit()
        finally:
            db.close()
    
    def _calculate_total_duration(self, task_with_agents: Optional[Dict[str, Any]]) -> float:
        """Calculate total workflow duration
        
        Args:
            task_with_agents: Task information with agent details
            
        Returns:
            Total duration in seconds
        """
        if not task_with_agents:
            return 0.0
        
        # 计算所有代理的总耗时
        total_duration = 0.0
        agents = task_with_agents.get("agents", {})
        
        for agent_info in agents.values():
            duration = agent_info.get("duration", 0.0)
            total_duration += duration
        
        return total_duration


# Create global snapshot service instance
snapshot_service = SnapshotService()
